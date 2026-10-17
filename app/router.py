"""Router (Architektur Punkt 3): ruft den echten Kern auf und orchestriert die ganze Kette
Fakten-Extraktion -> Pflichtangaben -> Faktenbestaetigung -> Kern -> Quellen ->
Bausteinantwort -> Pruefung.

Seit Chatbot Teil 1b ist `kern/rechnen.py` Teil des Repos (aufgaben/FUNDE_Chatbot.md,
Befund 1, behoben) -- der Import ist nicht mehr defensiv.

Seit Chatbot Teil 1d schreibt das Sprachmodell nur noch Platzhalter-Text (app/baustein.py);
Zahlen, Fundstellen, Aktenzeichen, Regel-IDs, Paragrafen, Jahre, Fassung und die
Ergebnisaussage selbst setzt ausschliesslich dieser Router aus dem Kernergebnis und den
gelieferten Quellenstuecken ein. Und: der Kern wird erst aufgerufen, nachdem der Nutzer die
extrahierten Fakten bestaetigt hat (app/bestaetigung.py) -- ausser bei reinen
Rechtsprechungsfragen, die nichts berechnen.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional

from pydantic import ValidationError

from app import gegenrechnung, textnorm
# Teil 1e: der Kern wird über den Mitschnitt aufgerufen (app/gegenrechnung.py); jede Rechnung wird danach unabhängig
# gegengerechnet. Außerhalb eines Mitschnitts verhält sich `K` genau wie das Modul kern.rechnen.
from app.gegenrechnung import KERN as K

from app import bestaetigung, einordnung, fallstand, pflichtangaben, quellen, taetigkeiten, textbausteine, zuordnung
from app.baustein import erzeuge_platzhalter, formatiere_betrag, fuelle, pruefe_rohtext
from app.ergebnisklassen import (
    AUSKUNFT_ERTEILT,
    FAKTEN_BESTAETIGUNG_NOETIG,
    GRENZFALL,
    HINWEIS,
    NICHT_ABGEDECKT,
    PRUEFUNG_FEHLGESCHLAGEN,
    RECHTSPRECHUNG_GEFUNDEN,
    RUECKFRAGE_NOETIG,
    SAEUMNISZUSCHLAG_BERECHNET,
)
from app.llm.base import AntwortKontext, LLM, LLMFehlgeschlagen
from app.llm.fake import SCHLUSSSATZ
from app.log import protokolliere
from app.pruefung import pruefe_antwort
from app.schema import VERWERTERART_LESBAR, Fakten, Position

ERSATZTEXT_ALLGEMEIN = (
    "Die Antwort enthielt eine Angabe, die nicht aus dem Kernergebnis stammt. "
    "Sie wurde nicht ausgegeben."
)

# Teil 1f, Abschnitt I.3: liefert das Sprachmodell keine brauchbare Antwort (kein gueltiges
# JSON, Pydantic-Fehler, Zeitueberschreitung, HTTP-Fehler -- app.llm.base.LLMFehlgeschlagen),
# bekommt der Nutzer diese feste Rueckfrage statt eines Absturzes/HTTP 500.
MODELLFEHLER_RUECKFRAGE = "Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut."


# Test des Nutzers im Codespace (16.10.2026): Mistral antwortete „402 Payment Required“ (Guthaben aufgebraucht); der
# Chat sagte nur „Bitte stellen Sie Ihre Frage erneut“ – das hilft nicht, Wiederholen ändert nichts. Bei einem
# gesperrten Zugang (HTTP-Status unten) nennt der feste Text jetzt die Ursache. Überlastung (429/503) bleibt wie in M6:
# automatische Wiederholung, danach der allgemeine Text. Keine Einzelheiten des Kontos, kein Schlüssel im Text.
ZUGANG_GESPERRT_STATUS = frozenset({401, 402, 403})
ZUGANG_GESPERRT_RUECKFRAGE = ("Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder "
                              "Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des "
                              "Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.")


def _modellfehler_antwort(sitzungskennung: str | None = None, fehler: LLMFehlgeschlagen | None = None) -> Antwort:
    text = (ZUGANG_GESPERRT_RUECKFRAGE if getattr(fehler, "status", None) in ZUGANG_GESPERRT_STATUS
            else MODELLFEHLER_RUECKFRAGE)
    return Antwort(
        antwort=f"{text}\n*{SCHLUSSSATZ}*",
        ergebnisklasse=RUECKFRAGE_NOETIG,
        rueckfragen=[text],
        sitzungskennung=sitzungskennung,
    )


UNBEKANNTE_SITZUNG_RUECKFRAGE = "Diese Sitzung ist unbekannt oder abgelaufen. Bitte stellen Sie Ihre Frage erneut."


def _rueckfrage_antwort(
    rueckfragen: list[str], fakten: Fakten | None = None, sitzungskennung: str | None = None
) -> Antwort:
    """Nachtrag Abschnitt B: eine Rueckfrage (fehlende Pflichtangaben, Jahr fehlt,
    Rechtsform je Position fehlt, oder eine Rueckfrage des Kerns selbst) wird AUSSCHLIESSLICH
    aus festen Textbausteinen gebaut -- kein Aufruf von `llm.formuliere_antwort`. Keine
    Summe/Fassung im Einleitungssatz (Abschnitt B.2): dieser Text haengt nur von den
    Rueckfragen selbst ab, nie vom Kernergebnis.

    Pruefkatalog-Befund M1: `fakten`/`sitzungskennung` werden durchgereicht, damit
    `rueckfrage_optionen` die Feld-Zuordnung fuer eine knopfbasierte Antwort (POST /knopf,
    siehe wende_feldantwort_an) mitliefern kann und die Weboberflaeche weiss, an welche
    Sitzung sie die Antwort haengen muss."""
    einleitung = "Dafür fehlt noch folgende Angabe:" if len(rueckfragen) == 1 else "Dafür fehlen noch folgende Angaben:"
    zeilen = [f"**Ergebnis (Vorschlag):** {RUECKFRAGE_NOETIG}", einleitung]
    zeilen += [f"– {r}" for r in rueckfragen]
    zeilen.append(f"*{SCHLUSSSATZ}*")
    return Antwort(
        antwort="\n".join(zeilen),
        ergebnisklasse=RUECKFRAGE_NOETIG,
        rueckfragen=list(rueckfragen),
        rueckfrage_optionen=pflichtangaben.rueckfrage_optionen(list(rueckfragen), fakten),
        sitzungskennung=sitzungskennung,
    )


@dataclass
class KernErgebnis:
    klasse: str
    protokoll: dict[str, Any] = field(default_factory=dict)
    grund: str | None = None
    stichworte: list[str] = field(default_factory=list)
    rueckfragen: list[str] = field(default_factory=list)
    regel_ids: list[str] = field(default_factory=list)
    fundstellen_kern: list[str] = field(default_factory=list)


@dataclass
class Antwort:
    antwort: str
    ergebnisklasse: str
    rueckfragen: list[str] = field(default_factory=list)
    fundstellen: list[str] = field(default_factory=list)
    kern_protokoll: dict[str, Any] = field(default_factory=dict)
    sitzungskennung: Optional[str] = None
    fakten_hash: Optional[str] = None
    fakten_zusammenfassung: list[str] = field(default_factory=list)
    # Teil 1f, Abschnitt E: geschlossene Rueckfragen (z. B. Einnahmeabsicht, Rechtsform)
    # bekommen feste Antwortoptionen fuer Schaltflaechen in der Weboberflaeche
    # (app/pflichtangaben.py::rueckfrage_optionen); offene Fragen (Jahr, Betrag) bleiben
    # Texteingabe und tauchen hier nicht auf.
    rueckfrage_optionen: list[dict[str, Any]] = field(default_factory=list)
    # Teil 1e: Prüfprotokoll der unabhängigen Gegenrechnung (app/gegenrechnung.py), vom System erzeugt.
    pruefprotokoll: dict[str, Any] = field(default_factory=dict)


def _uebersetze(ergebnis: K.Ergebnis, stichworte: list[str], zusatz: dict[str, Any] | None = None) -> KernErgebnis:
    protokoll: dict[str, Any] = dict(zusatz or {})
    if ergebnis.bemessungsgrundlage is not None:
        protokoll["bemessungsgrundlage"] = ergebnis.bemessungsgrundlage
    if ergebnis.abgabe is not None:
        protokoll["abgabe"] = ergebnis.abgabe
    if ergebnis.begruendung:
        protokoll["subsumtion"] = " ".join(ergebnis.begruendung)
    return KernErgebnis(
        klasse=ergebnis.klasse,
        protokoll=protokoll,
        grund=" ".join(ergebnis.begruendung) if ergebnis.klasse == NICHT_ABGEDECKT else None,
        stichworte=stichworte,
        rueckfragen=list(ergebnis.rueckfragen),
        regel_ids=list(ergebnis.regeln),
        fundstellen_kern=list(ergebnis.fundstellen),
    )


def _empfaenger_fuer(auftragnehmer_typ: str | None) -> str | None:
    """Bildet AuftragspartnerTyp auf das von kern.rechnen.summe_positionen erwartete
    `empfaenger`-Vokabular ab (kern unterscheidet innerhalb von GmbH/UG/AG bzw. KG/OHG
    nicht -- alle Werte dieser Gruppen stehen gleichwertig im Regelregister
    'rechtsform.kein_entgelt')."""
    if auftragnehmer_typ == "GmbH_UG_AG":
        return "gmbh"
    if auftragnehmer_typ == "KG_OHG":
        return "kg"
    return None


def _einordnung(fakten: Fakten) -> list[dict[str, Any]]:
    """Einordnung jeder Position (bzw. des Gesamtbetrags) für die Tätigkeitsprüfung.

    Testfall 20 Positionen (11.10.2026): Gruppe aus dem Excel-Blatt 'Tätigkeitsabgrenzung'
    (app/taetigkeiten.py): 'kuenstlerisch', 'nicht_kuenstlerisch' oder 'unsicher' (Grenzfall,
    nicht im Regelwerk, Widerspruch, keine Angabe).

    Mehrere Positionen DESSELBEN Künstlers (R-42, R-117, R-175): Rechnet derselbe Auftragnehmer
    neben einer künstlerischen Leistung weitere Leistungen ab, gilt für diese die Spalte
    'Rechnet derselbe Künstler das mit ab' der Excel (zählt mit / zählt nicht / Steuerberater
    entscheidet). Derselbe Auftragnehmer heißt: gleiche `Position.auftragnehmer_nr` oder
    `Fakten.ein_auftragnehmer` ist True -- nie geraten.

    `zaehlend` ist False bei Zahlungen an eine GmbH/KG (R-138/R-216) und bei Sonderrollen des
    Kerns (Reisekosten, Umsatzsteuer, ...): dort entscheidet die Tätigkeit nicht."""
    eintraege: list[dict[str, Any]] = []
    for i, p in enumerate(fakten.positionen):
        tid = p.taetigkeit_id or fakten.taetigkeit_id
        e = taetigkeiten.nach_id(tid)
        gruppe = taetigkeiten.gruppe(tid) or "unsicher"
        if fakten.ein_auftragnehmer:
            schluessel: Any = "alle"
        elif p.auftragnehmer_nr is not None:
            schluessel = ("nr", p.auftragnehmer_nr)
        else:
            schluessel = ("einzeln", i)
        eintraege.append({
            "index": i, "bezeichnung": p.bezeichnung or f"Position {i + 1}", "tid": tid, "gruppe": gruppe,
            "nebenleistung": False, "schluessel": schluessel,
            "regel_ids": list(e["regel_ids"]) if e else [], "fundstellen": list(e["fundstellen"]) if e else [],
            "zaehlend": p.rolle not in K._AUSSCHLUSSGRUENDE and not _empfaenger_fuer(p.auftragnehmer_typ or fakten.auftragnehmer_typ),
        })
    if not fakten.positionen and fakten.gesamtbetrag_genannt is not None:
        e = taetigkeiten.nach_id(fakten.taetigkeit_id)
        eintraege.append({
            "index": None, "bezeichnung": fakten.leistungsart or "Gesamtbetrag", "tid": fakten.taetigkeit_id,
            "gruppe": taetigkeiten.gruppe(fakten.taetigkeit_id) or "unsicher", "nebenleistung": False,
            "schluessel": "gesamt", "regel_ids": list(e["regel_ids"]) if e else [],
            "fundstellen": list(e["fundstellen"]) if e else [], "zaehlend": not _empfaenger_fuer(fakten.auftragnehmer_typ),
        })

    # Derselbe Künstler: gibt es in der Gruppe eine sicher künstlerische, zählende Leistung?
    kuenstler = {x["schluessel"] for x in eintraege if x["zaehlend"] and x["gruppe"] == "kuenstlerisch"}
    gruppen_groesse: dict[Any, int] = {}
    for x in eintraege:
        gruppen_groesse[x["schluessel"]] = gruppen_groesse.get(x["schluessel"], 0) + 1
    for x in eintraege:
        if (x["zaehlend"] and x["gruppe"] != "kuenstlerisch" and x["schluessel"] in kuenstler
                and gruppen_groesse[x["schluessel"]] > 1):
            regel, e = taetigkeiten.beim_selben_kuenstler(x["tid"])
            regel_ids = e["selber_regel_ids"] if e else []
            x["regel_ids"] = list(dict.fromkeys([*x["regel_ids"], *regel_ids]))
            if regel == "zaehlt":
                x["gruppe"], x["nebenleistung"] = "kuenstlerisch", True
            elif regel == "zaehlt_nicht":
                x["gruppe"] = "nicht_kuenstlerisch"
            else:
                x["gruppe"] = "unsicher"
    # Härtetest RE-2026-777: Position, bei der die Rechnungstellerin nicht im eigenen Namen handelt
    # (Vertretung, Durchleitung, Direktzahlung): ob sie beim Mandanten zählt, entscheidet der
    # Vertrag mit dem Künstler (KSK-Info 27) -- das System entscheidet es nicht. Eine sicher nicht
    # künstlerische Leistung bleibt ausgeschlossen.
    for x in eintraege:
        p = fakten.positionen[x["index"]] if x["index"] is not None else None
        if p is not None and p.zahlungsweg_unklar and x["zaehlend"] and x["gruppe"] != "nicht_kuenstlerisch":
            x["gruppe"], x["nebenleistung"], x["zahlungsweg"] = "unsicher", False, True
            x["regel_ids"] = list(dict.fromkeys([*x["regel_ids"], "R-33", "R-36", "R-94", "R-38", "R-39"]))
    return eintraege


def _kern_positionen(fakten: Fakten, unsicher_zaehlt: bool = True) -> list[dict[str, Any]]:
    """Wandelt app/schema.py-Positionen in das von kern.rechnen.summe_positionen erwartete
    Dict-Format um. Teil 1f, Abschnitt A (Befund, behoben): die Rechtsform gilt JE POSITION
    (`Position.auftragnehmer_typ`); fehlt sie, gilt `Fakten.auftragnehmer_typ` als Vorgabe.
    Vorher wurde ausschliesslich der globale Wert verwendet -- bei gemischten Positionen
    (z. B. eine GmbH-Position neben mehreren natuerlichen Personen ohne globalen Typ) wurde
    die GmbH-Position faelschlich mitgezaehlt, weil ihr kein `empfaenger` zugeordnet war.

    Tätigkeitsprüfung: nicht künstlerische Leistungen bekommen `kuenstlerisch: False` (der Kern
    schließt sie aus); unsichere nur in der Rechnung 'ohne die unsicheren Leistungen'."""
    einordnung = {x["index"]: x for x in _einordnung(fakten)}
    ergebnis = []
    for i, p in enumerate(fakten.positionen):
        eintrag: dict[str, Any] = {"betrag": p.betrag}
        if p.rolle:
            eintrag["art"] = p.rolle
        empfaenger = _empfaenger_fuer(p.auftragnehmer_typ or fakten.auftragnehmer_typ)
        if empfaenger:
            eintrag["empfaenger"] = empfaenger
        if p.kuenstlerisch is not None:
            eintrag["kuenstlerisch"] = p.kuenstlerisch
        x = einordnung[i]
        if x["zaehlend"] and _ausschliessen(x, unsicher_zaehlt):
            eintrag["kuenstlerisch"] = False
        ergebnis.append(eintrag)
    return ergebnis


def _ausschliessen(x: dict[str, Any], unsicher_zaehlt: bool) -> bool:
    return x["gruppe"] == "nicht_kuenstlerisch" or (x["gruppe"] == "unsicher" and not unsicher_zaehlt)


def _liste(eintraege: list[dict[str, Any]], mit_bezeichnung: bool) -> str:
    teile = []
    for x in eintraege:
        lesbar = taetigkeiten.lesbar(x["tid"]) or "keine Angabe zur Leistung"
        teile.append(f"„{x['bezeichnung']}“ – {lesbar}" if mit_bezeichnung else lesbar)
    return "; ".join(dict.fromkeys(teile))


def _unsichere(fakten: Fakten) -> list[dict[str, Any]]:
    return [x for x in _einordnung(fakten) if x["zaehlend"] and x["gruppe"] == "unsicher"]


def _mit_taetigkeitspruefung(fakten: Fakten, rechne, stichworte: list[str], zusatz) -> KernErgebnis:
    """Testfall 20 Positionen (11.10.2026): nur künstlerische oder publizistische Leistungen
    zählen (Excel-Blatt 'Tätigkeitsabgrenzung', app/taetigkeiten.py). Nicht künstlerische
    Leistungen schließt der Kern aus. Ist eine Leistung unsicher (Grenzfall, nicht im
    Regelwerk, Widerspruch zwischen Modell und fester Erkennung), rechnet der KERN beide Fälle
    -- ohne und mit dieser Leistung. Hängt das Ergebnis davon ab, ist es ein Grenzfall; es
    gibt dann nie 'Abgabepflichtig'. `rechne(unsicher_zaehlt)` liefert ein K.Ergebnis,
    `zusatz(unsicher_zaehlt)` zusätzliche Protokollwerte."""
    eintraege = [x for x in _einordnung(fakten) if x["zaehlend"]]
    mehrere = len(eintraege) > 1
    sicher_k = [x for x in eintraege if x["gruppe"] == "kuenstlerisch" and not x["nebenleistung"]]
    neben = [x for x in eintraege if x["nebenleistung"]]
    sicher_n = [x for x in eintraege if x["gruppe"] == "nicht_kuenstlerisch"]
    unsicher = [x for x in eintraege if x["gruppe"] == "unsicher"]

    regel_t = list(dict.fromkeys(r for x in eintraege for r in x["regel_ids"]))
    fund_t = list(dict.fromkeys(f for x in eintraege for f in x["fundstellen"]))
    protokoll_t: dict[str, Any] = {}
    if sicher_k:
        protokoll_t["taetigkeit_kuenstlerisch"] = _liste(sicher_k, mit_bezeichnung=mehrere)
    if neben:
        protokoll_t["taetigkeit_nebenleistung"] = _liste(neben, mit_bezeichnung=True)
    if sicher_n:
        protokoll_t["taetigkeit_nicht"] = _liste(sicher_n, mit_bezeichnung=mehrere)

    def _fertig(ergebnis: K.Ergebnis, unsicher_zaehlt: bool) -> KernErgebnis:
        k = _uebersetze(ergebnis, stichworte, {**zusatz(unsicher_zaehlt), **protokoll_t})
        k.regel_ids += [r for r in regel_t if r not in k.regel_ids]
        k.fundstellen_kern += [f for f in fund_t if f not in k.fundstellen_kern]
        return k

    if not unsicher:
        return _fertig(rechne(True), True)
    mit = rechne(True)
    if mit.klasse not in (K.ABGABEPFLICHTIG, K.NICHT):
        return _fertig(mit, True)
    ohne = rechne(False)
    if ohne.klasse == mit.klasse and ohne.abgabe == mit.abgabe:
        return _fertig(mit, True)  # die unsicheren Leistungen ändern nichts am Ergebnis
    protokoll: dict[str, Any] = dict(protokoll_t)
    unsicher_taetigkeit = [x for x in unsicher if not x.get("zahlungsweg")]
    unsicher_zahlungsweg = [x for x in unsicher if x.get("zahlungsweg")]
    if unsicher_taetigkeit:
        protokoll["taetigkeit_unsicher"] = _liste(unsicher_taetigkeit, mit_bezeichnung=mehrere)
    if unsicher_zahlungsweg:
        # Härtetest-Serie HT-2026-002 bis 011: der Grund aus dem Text (Position.offen_grund) steht dabei.
        def _mit_grund(x: dict) -> str:
            p = fakten.positionen[x["index"]] if x.get("index") is not None else None
            return f"„{x['bezeichnung']}“" + (f" ({p.offen_grund})" if p is not None and p.offen_grund else "")
        protokoll["zahlungsweg_unklar"] = "; ".join(dict.fromkeys(_mit_grund(x) for x in unsicher_zahlungsweg))
    if mit.abgabe is not None:
        protokoll["abgabe_falls_kuenstlerisch"] = mit.abgabe
    if ohne.klasse == K.ABGABEPFLICHTIG and ohne.abgabe is not None:
        protokoll["abgabe_ohne_unsichere"] = ohne.abgabe
    return KernErgebnis(
        klasse=GRENZFALL,
        protokoll=protokoll,
        grund=("Mindestens eine Leistung ist nicht sicher als künstlerisch oder publizistisch eingeordnet, oder der "
               "Zahlungsweg ist unklar; sie entscheidet über das Ergebnis."),
        stichworte=stichworte,
        regel_ids=list(dict.fromkeys([*mit.regeln, *regel_t])),
        fundstellen_kern=list(dict.fromkeys([*mit.fundstellen, *fund_t])),
    )


def _mit_rechnungsteller_hinweis(fakten: Fakten, ergebnis: KernErgebnis, rechne=None) -> KernErgebnis:
    """Alltagsfälle 11.10.2026 (F3): Stellt eine KG/OHG oder juristische Person die Rechnung, wird
    an sie gezahlt (R-45, R-177, R-216). Ihre eigene Prüfung (Zahlungen an die von ihr beauftragten
    Künstler, R-219) gehört nicht zu dieser Bewertung: nur als Hinweis (Baustein aus dem
    Regelkatalog), keine Zahl."""
    if fakten.rechnungsteller_typ not in ("GmbH_UG_AG", "KG_OHG"):
        return ergebnis
    from app.schema import AUFTRAGSPARTNER_LESBAR

    ergebnis.protokoll["rechnungsteller_gesellschaft"] = AUFTRAGSPARTNER_LESBAR[fakten.rechnungsteller_typ]
    ergebnis.regel_ids += [r for r in ("R-45", "R-177", "R-216", "R-219") if r not in ergebnis.regel_ids]
    # ALLTAG-2026-999: Positionen mit direktem Vertrag zwischen Mandant und Künstler -- zählen mit, mit Begründung.
    direkt = [p.bezeichnung or f"Position {i + 1}" for i, p in enumerate(fakten.positionen) if p.vertrag_direkt]
    if direkt:
        ergebnis.protokoll["vertrag_direkt"] = "; ".join(f"„{b}“" for b in dict.fromkeys(direkt))
        ergebnis.regel_ids += [r for r in ("R-127", "R-36", "R-94") if r not in ergebnis.regel_ids]
    # Provision an die Rechnungstellerin (Gesellschaft): beim Mandanten nicht mitgezählt, aber offen (R-38/R-39).
    # Der KERN rechnet zusätzlich den Fall 'Provision zählt mit'; die Ergebnisklasse bleibt.
    provision = [i for i, p in enumerate(fakten.positionen)
                 if p.zahlungsweg_unklar and _empfaenger_fuer(p.auftragnehmer_typ or fakten.auftragnehmer_typ)]
    if provision and rechne is not None:
        mit = rechne([fakten.positionen[i].betrag for i in provision])
        ergebnis.protokoll["provision_offen"] = "; ".join(
            f"„{fakten.positionen[i].bezeichnung or f'Position {i + 1}'}“" for i in provision)
        if mit.abgabe is not None:
            ergebnis.protokoll["abgabe_mit_provision"] = mit.abgabe
        ergebnis.regel_ids += [r for r in ("R-38", "R-39") if r not in ergebnis.regel_ids]
    return ergebnis


def _nicht_zaehlend(fakten: Fakten, summe_kern: Decimal) -> dict[str, Any]:
    """Teil, den der Kern nicht zur Summe der Entgelte zählt (z. B. Zahlung an eine GmbH) --
    für Baustein TB-12 ('Davon nicht zur Bemessungsgrundlage gehörend'), damit die Antwort
    zeigt, WARUM die Summe kleiner ist als der genannte Betrag."""
    roh = fakten.summe_positionen() if fakten.positionen else fakten.gesamtbetrag_genannt
    if roh is None or Decimal(str(roh)) <= summe_kern:
        return {}
    differenz = Decimal(str(roh)) - summe_kern
    genannt = [p.betrag for p in fakten.positionen] if fakten.positionen else [fakten.gesamtbetrag_genannt]
    gegenrechnung.notiere("nicht_zur_bemessungsgrundlage", [genannt, summe_kern], {"zahl": differenz})
    return {"nicht_zur_bemessungsgrundlage": differenz}


def _veranstaltungszahl_unbekannt(fakten: Fakten, jahr: int) -> KernErgebnis:
    """Livetest 11.10.2026 (Projektplan Abschnitt 5: 'Fehlt die Historie ... zeigt beide
    Ausgänge und markiert Annahmen'). Generalklausel, Zahl der Veranstaltungen ausdrücklich
    unbekannt: der KERN rechnet beide Fälle -- innerhalb der Ausnahme (eine Veranstaltung) und
    knapp darüber (Grenze aus dem Regelregister + 1). Sind beide gleich, gilt dieses Ergebnis
    (z. B. Zahlung an eine GmbH, Summe unter der Schwelle). Unterscheiden sie sich, ist es ein
    Grenzfall: der Text (Gesetz, Abgabe für den Fall 'mehr', Empfehlung, Fundstellen) kommt aus
    den Textbausteinen der Excel (TB-17, TB-18), nicht aus dem Programm. Regeln R-15, R-16,
    R-21, R-83, R-212."""
    try:
        grenze = int(K.wert("veranstaltungen.ausnahme_max", jahr))
    except K.RegisterLuecke as fehler:
        return KernErgebnis(klasse=NICHT_ABGEDECKT, grund=str(fehler))
    # Testfall 20 Positionen: unsichere Leistungen zählen hier vorsorglich mit (beide Ausgänge
    # werden ohnehin gezeigt); ein sicheres 'Abgabepflichtig' verhindert der Wächter in
    # _rufe_kern_auf.
    summe = K.summe_positionen(_kern_positionen_oder_gesamtbetrag(fakten), jahr)
    innerhalb = K.veranstaltungen(jahr, 1, summe, fakten.einnahmeabsicht, "generalklausel")
    darueber = K.veranstaltungen(jahr, grenze + 1, summe, fakten.einnahmeabsicht, "generalklausel")
    if innerhalb.klasse == darueber.klasse:
        # Gleiches Ergebnis in beiden Fällen: NICHT die Begründung eines der beiden Fälle
        # übernehmen ('Mehr als drei Veranstaltungen ...' wäre bei unbekannter Zahl falsch).
        darueber.begruendung = ["Die Zahl der Veranstaltungen ist unbekannt; das Ergebnis ist bei "
                                "wenigen wie bei vielen Veranstaltungen dasselbe."]
        return _uebersetze(darueber, ["veranstalt"], _nicht_zaehlend(fakten, summe))
    protokoll: dict[str, Any] = {"veranstaltungsgrenze": grenze}
    if darueber.abgabe is not None:
        protokoll["abgabe_falls_mehr"] = darueber.abgabe
    return KernErgebnis(
        klasse=GRENZFALL,
        protokoll=protokoll,
        grund="Zahl der Veranstaltungen unbekannt; sie entscheidet über das Ergebnis.",
        stichworte=["veranstalt"],
        regel_ids=["R-15", "R-16", "R-21", "R-83", "R-212"],
        # Keine Paragrafen im Code (RAG-Auftrag, Wächter tests/app/test_keine_festwerte.py): die
        # Fundstellen kommen aus diesen Regeln im Regelkatalog (R-15, R-83, R-212).
        fundstellen_kern=[],
    )


def _kern_positionen_oder_gesamtbetrag(fakten: Fakten, unsicher_zaehlt: bool = True) -> list[dict[str, Any]]:
    """Dialogtest Fallgrenzen: Gibt es keine einzelnen Positionen, aber einen ausdrücklich
    genannten Gesamtbetrag, bekommt der Kern GENAU diesen Betrag als eine Summe (Rechtsform aus
    `Fakten.auftragnehmer_typ`, die app/pflichtangaben.py vorher abfragt). Für Schwelle und
    Bemessungsgrundlage zählt die Summe der Entgelte im Jahr, nicht die Aufteilung auf
    Rechnungen. `Fakten.positionen` bleibt dabei leer -- es entsteht keine Rechnungsposition,
    die der Nutzer nie genannt hat; die Faktenbestätigung zeigt 'Gesamtbetrag (Aufteilung
    unbekannt)'."""
    if fakten.positionen:
        return _kern_positionen(fakten, unsicher_zaehlt)
    eintrag: dict[str, Any] = {"betrag": fakten.gesamtbetrag_genannt}
    empfaenger = _empfaenger_fuer(fakten.auftragnehmer_typ)
    if empfaenger:
        eintrag["empfaenger"] = empfaenger
    gesamt = _einordnung(fakten)
    if gesamt and gesamt[0]["zaehlend"] and _ausschliessen(gesamt[0], unsicher_zaehlt):
        eintrag["kuenstlerisch"] = False
    return [eintrag]


def _rechnungspositionen(fakten: Fakten) -> list[dict[str, Any]]:
    """Wie `_kern_positionen`, aber im Format von `kern.rechnen.analysiere_rechnung`
    (nr, text, betrag, rolle, belege)."""
    ergebnis = []
    for i, p in enumerate(fakten.positionen, start=1):
        ergebnis.append(
            {
                "nr": p.nr or i,
                "text": p.bezeichnung or "",
                "betrag": p.betrag,
                "rolle": p.rechnungsrolle,
                "belege": p.nachgewiesen,
            }
        )
    return ergebnis


def _auskunft(jahr: int | None, thema: str | None) -> KernErgebnis:
    """Teil 1f, Abschnitt C: Auskunftsfragen (Abgabesatz/Schwelle/Meldefrist/Aufbewahrung/
    Pauschale) direkt aus dem Register (`kern.rechnen`), nie als Festwert im App-Code und
    nie vom Sprachmodell. `thema` ist durch app/pflichtangaben.py bereits auf einen der 5
    bekannten Werte geprueft, bevor diese Funktion aufgerufen wird; `jahr` ist durch die
    globale Jahr-Pflicht bereits gesetzt."""
    try:
        if thema == "abgabesatz":
            satz = K.abgabesatz(jahr)
            if satz is None:
                return KernErgebnis(klasse=NICHT_ABGEDECKT, grund=f"Kein Abgabesatz im Regelwerk für das Jahr {jahr}.")
            zeile = K.P.get("abgabesatz", {}).get(str(jahr)) or {}
            return KernErgebnis(
                klasse=AUSKUNFT_ERTEILT, protokoll={"abgabesatz_prozent": satz},
                fundstellen_kern=[f for f in [zeile.get("fundstelle")] if f],
            )

        if thema == "schwelle":
            s = K.schwelle(jahr)
            if s is None or s.get("euro") is None:
                return KernErgebnis(klasse=NICHT_ABGEDECKT, grund=f"Keine Schwelle im Regelwerk für das Jahr {jahr}.")
            return KernErgebnis(
                klasse=AUSKUNFT_ERTEILT, protokoll={"schwelle": Decimal(str(s["euro"]))},
                fundstellen_kern=[f for f in [s.get("fundstelle")] if f],
            )

        if thema == "meldefrist":
            datum = K.meldefrist(jahr)
            zeile = K.reg("meldefrist.monat", jahr)
            return KernErgebnis(
                klasse=AUSKUNFT_ERTEILT, protokoll={"datum": datum.strftime("%d.%m.%Y")},
                regel_ids=[zeile["regel"]] if zeile.get("regel") else [],
                fundstellen_kern=[f for f in [zeile.get("fundstelle")] if f],
            )

        if thema == "aufbewahrung":
            datum = K.aufbewahrung_bis(jahr)
            zeile = K.reg("aufbewahrung.jahre", jahr)
            return KernErgebnis(
                klasse=AUSKUNFT_ERTEILT, protokoll={"datum": datum.strftime("%d.%m.%Y")},
                regel_ids=[zeile["regel"]] if zeile.get("regel") else [],
                fundstellen_kern=[f for f in [zeile.get("fundstelle")] if f],
            )

        if thema == "pauschale":
            # Fund (siehe aufgaben/FUNDE_Chatbot.md): fuer Pauschalen gibt es noch keine
            # eigene Kernfunktion/Register-Abfrage ohne Betrag -- nicht erfinden.
            return KernErgebnis(
                klasse=NICHT_ABGEDECKT,
                grund="Auskunft 'pauschale' braucht noch einen eigenen Kernzugriff (siehe aufgaben/FUNDE_Chatbot.md).",
            )
    except K.RegisterLuecke as fehler:
        return KernErgebnis(klasse=NICHT_ABGEDECKT, grund=str(fehler))

    return KernErgebnis(klasse=NICHT_ABGEDECKT, grund=f"Unbekanntes Auskunftsthema '{thema}'.")


def _rufe_kern_auf(fakten: Fakten) -> KernErgebnis:
    jahr = fakten.jahr
    art = fakten.anfrageart or "bewertung"
    # Dialogtest Fallgrenzen: ein ausdrücklich genannter Gesamtbetrag ohne bekannte Aufteilung
    # auf Rechnungen ist eine bekannte Summe -- er wird nicht ignoriert und nicht in eine
    # erfundene Rechnungsposition verwandelt (siehe _kern_positionen_oder_gesamtbetrag).
    if fakten.positionen:
        summe = fakten.summe_positionen()
    else:
        summe = fakten.gesamtbetrag_genannt

    if art == "vorauszahlung":
        if fakten.bemessungsgrundlage_vorjahr is None:
            return KernErgebnis(RUECKFRAGE_NOETIG, rueckfragen=["Wie hoch war die Bemessungsgrundlage des Vorjahres?"])
        # K.vorauszahlung_monatlich prueft nur den Abgabesatz vorab selbst; fehlt im
        # Regelregister ein Eintrag fuer "vorauszahlung.monate"/"vorauszahlung.untergrenze"
        # in diesem Jahr, wirft sie (anders als die mit @_luecke dekorierten Funktionen) eine
        # RegisterLuecke (Fund, siehe aufgaben/FUNDE_Chatbot.md).
        try:
            betrag, ergebnis = K.vorauszahlung_monatlich(jahr, fakten.bemessungsgrundlage_vorjahr)
        except K.RegisterLuecke as fehler:
            return KernErgebnis(klasse=NICHT_ABGEDECKT, grund=str(fehler))
        zusatz = {"vorauszahlung_monatlich": betrag} if betrag is not None else {}
        return _uebersetze(ergebnis, ["vorauszahlung"], zusatz)

    if art == "saeumniszuschlag":
        rueckstaende = fakten.rueckstand_liste or fakten.rueckstand
        if rueckstaende is None or fakten.saeumnis_monate is None:
            return KernErgebnis(
                RUECKFRAGE_NOETIG,
                rueckfragen=["Wie hoch ist der Rückstand (ggf. je Zeitraum), und für wie viele Monate?"],
            )
        ergebnis = K.saeumniszuschlag(
            rueckstaende, fakten.saeumnis_monate, jahr, fakten.saeumnis_gesondert_angefordert or False
        )
        return _uebersetze(ergebnis, ["säumniszuschlag"])

    if art == "verpflegung":
        if fakten.reise_stunden is None:
            return KernErgebnis(RUECKFRAGE_NOETIG, rueckfragen=["Wie viele Stunden dauerte die Reise?"])
        # K.verpflegung ist (anders als die mit @_luecke dekorierten Funktionen) nicht gegen
        # einen fehlenden Regelregister-Eintrag fuer das Jahr abgesichert (Fund, siehe
        # aufgaben/FUNDE_Chatbot.md).
        try:
            nicht_zaehlend, ergebnis = K.verpflegung(
                jahr,
                fakten.reise_stunden,
                fakten.reise_uebernachtung or False,
                fakten.reise_erstattung or 0,
                fakten.reise_inland if fakten.reise_inland is not None else True,
            )
        except K.RegisterLuecke as fehler:
            return KernErgebnis(klasse=NICHT_ABGEDECKT, grund=str(fehler))
        return _uebersetze(ergebnis, ["verpflegung"], {"nicht_zur_bemessungsgrundlage": nicht_zaehlend})

    if art == "uebungsleiter_pauschale":
        if summe is None:
            return KernErgebnis(RUECKFRAGE_NOETIG, rueckfragen=["Um welchen Honorarbetrag geht es?"])
        bg, ergebnis = K.uebungsleiter_bg(
            jahr,
            summe,
            fakten.pauschale_art or "uebungsleiter",
            fakten.pauschale_bestaetigung if fakten.pauschale_bestaetigung is not None else True,
            fakten.pauschale_bereits_ausgeschoepft or 0,
        )
        zusatz = {"bemessungsgrundlage_nach_pauschale": bg} if bg is not None else {}
        return _uebersetze(ergebnis, ["übungsleiter", "pauschale"], zusatz)

    if art == "kommission":
        if fakten.kommission_verkaufspreis is None or fakten.kommission_einbehalt is None:
            return KernErgebnis(
                RUECKFRAGE_NOETIG, rueckfragen=["Wie hoch sind Verkaufspreis und Provision/Einbehalt?"]
            )
        bg = K.kommission_bg(fakten.kommission_verkaufspreis, fakten.kommission_einbehalt)
        ergebnis = K.pruefe_typischer_verwerter(jahr, bg)
        return _uebersetze(ergebnis, ["kommission"])

    if art == "schaetzung_ausland":
        if fakten.schaetzung_bruttoeinnahmen is None:
            return KernErgebnis(RUECKFRAGE_NOETIG, rueckfragen=["Wie hoch sind die Bruttoeinnahmen?"])
        # K.schaetzung_ausland ist (anders als die mit @_luecke dekorierten Funktionen) eine
        # reine Decimal-Funktion und wirft bei fehlendem Regelregister-Eintrag fuer das Jahr
        # eine RegisterLuecke, statt ein Ergebnis(NICHT_ABGEDECKT) zurueckzugeben -- hier
        # dieselbe Behandlung nachgebildet (Fund, siehe aufgaben/FUNDE_Chatbot.md).
        try:
            bg = K.schaetzung_ausland(fakten.schaetzung_bruttoeinnahmen, jahr)
        except K.RegisterLuecke as fehler:
            return KernErgebnis(klasse=NICHT_ABGEDECKT, grund=str(fehler))
        ergebnis = K.pruefe_typischer_verwerter(jahr, bg)
        return _uebersetze(ergebnis, ["schätzung", "ausland"])

    if art == "auskunft":
        return _auskunft(jahr, fakten.auskunft_thema)

    if art == "rechnungsanalyse":
        if not fakten.positionen:
            return KernErgebnis(RUECKFRAGE_NOETIG, rueckfragen=["Welche Rechnungspositionen gibt es (Betrag, Rolle)?"])
        ergebnis, _zeilen = K.analysiere_rechnung(
            jahr, _rechnungspositionen(fakten), fakten.empfaenger_abgabepflichtig, fakten.agentur_abgabepflichtig
        )
        return _uebersetze(ergebnis, ["rechnungsanalyse"])

    # Standardfall ("bewertung"): Eigenwerbung / typischer Verwerter / Positionen / Veranstaltungen.
    # Livetest-Befund L1 (aufgaben/PROMPT_ClaudeCode_Chatbot_Livetest1_Befunde.md): KEIN Default
    # mehr fuer verwerterart -- app/pflichtangaben.py fragt das vorher gezielt ab; dieser
    # Waechter greift auch, falls diese Funktion direkt mit unvollstaendigen Fakten aufgerufen
    # wird (z. B. aus app/router.py::fuehre_nach_bestaetigung_aus mit gespeicherten Fakten).

    # Pruefkatalog-Befund M5 (aufgaben/PROMPT_ClaudeCode_Chatbot_Pruefkatalog1_Befunde.md):
    # "generalklausel" braucht IMMER die Veranstaltungszahl (auch 0, fuer "keine
    # Veranstaltungen") -- sonst landete der Fall frueher unten im `positionen`-Zweig und
    # wurde faelschlich mit der Eigenwerbungs-Logik/-Fundstelle geprueft, OHNE die
    # Drei-Veranstaltungen-Ausnahme und OHNE die Einnahmeabsicht zu beruecksichtigen.
    # app/pflichtangaben.py fragt das vorher gezielt ab; dieser Waechter greift auch bei
    # direktem Aufruf (wie beim verwerterart-Waechter oben).
    # Alltagsfälle 11.10.2026 (F4): Privatperson als Auftraggeber (R-40, R-133) -- nicht
    # abgabepflichtig, ohne Schwellenvergleich und ohne Tätigkeitsprüfung.
    if fakten.verwerterart == "privat":
        return _uebersetze(K.privater_auftraggeber(), ["privat"],
                           {"auftraggeber_privat": VERWERTERART_LESBAR["privat"]})
    # 14.10.2026 (P-37): nur Benennung der Vertragsparteien (Nachweismakler, R-35) -- Grenzfall ohne Betrag.
    if fakten.nachweismakler:
        return _uebersetze(K.nachweismakler(), ["nachweis", "makler"])
    # 14.10.2026 (P-36): Vertretung im Namen und für Rechnung des Künstlers (R-33, KSVG § 25 Abs. 3). Ist der
    # Vertragspartner selbst abgabepflichtig, zahlt er -- unabhängig vom Betrag. Ohne Betrag entscheidet nur
    # die Kern-Prüfung der Vertretung (sonst wie bisher über die Beträge).
    if fakten.vertretung_kuenstler and (fakten.empfaenger_abgabepflichtig is True
                                        or not (fakten.positionen or fakten.gesamtbetrag_genannt is not None)):
        return _uebersetze(K.vertreter(fakten.empfaenger_abgabepflichtig, True), ["vertret"])

    if (fakten.verwerterart == "generalklausel" and fakten.veranstaltungszahl is None
            and fakten.veranstaltungszahl_unbekannt and summe is not None):
        ergebnis_unbekannt = _veranstaltungszahl_unbekannt(fakten, jahr)
        unsicher = _unsichere(fakten)
        if ergebnis_unbekannt.klasse == K.ABGABEPFLICHTIG and unsicher:
            ergebnis_unbekannt.klasse = GRENZFALL
            ergebnis_unbekannt.protokoll["taetigkeit_unsicher"] = _liste(unsicher, mit_bezeichnung=len(unsicher) > 1)
        return ergebnis_unbekannt
    if fakten.verwerterart == "generalklausel" and fakten.veranstaltungszahl is None:
        return KernErgebnis(RUECKFRAGE_NOETIG, rueckfragen=[pflichtangaben.FRAGE_VERANSTALTUNGSZAHL])

    if fakten.veranstaltungszahl is not None:
        if summe is None:
            return KernErgebnis(RUECKFRAGE_NOETIG, rueckfragen=["Welche Entgeltsumme wurde für die Veranstaltung(en) gezahlt?"])
        if fakten.verwerterart is None:
            return KernErgebnis(RUECKFRAGE_NOETIG, rueckfragen=[pflichtangaben.FRAGE_VERWERTERART])
        # Pruefkatalog-Befund M7: kein Ersatzwert mehr fuer veranstaltungszahl == 0 --
        # kern.rechnen.veranstaltungen prueft diesen Fall jetzt selbst eigenstaendig (R-13),
        # mit zutreffender Begruendung statt der (vorher uebernommenen) Drei-Veranstaltungen-
        # Subsumtion.
        # Livetest 10.10.2026 (GmbH + Generalklausel): hier ging früher die ROHE Summe an den
        # Kern -- Zahlungen an eine GmbH/KG, gesondert ausgewiesene USt, nachgewiesene
        # Fahrtkosten usw. zählten mit (4 Veranstaltungen, 2.000 € an eine GmbH ergab
        # 'abgabepflichtig 98,00 €'). Die Summe der Entgelte bildet der Kern selbst
        # (kern.rechnen.summe_positionen), genau wie im Positionen-Zweig.
        def rechne_veranstaltung(unsicher_zaehlt: bool) -> K.Ergebnis:
            s = K.summe_positionen(_kern_positionen_oder_gesamtbetrag(fakten, unsicher_zaehlt), jahr)
            return K.veranstaltungen(jahr, fakten.veranstaltungszahl, s, fakten.einnahmeabsicht, fakten.verwerterart)

        def zusatz_veranstaltung(unsicher_zaehlt: bool) -> dict[str, Any]:
            s = K.summe_positionen(_kern_positionen_oder_gesamtbetrag(fakten, unsicher_zaehlt), jahr)
            return _nicht_zaehlend(fakten, s)

        ergebnis = _mit_taetigkeitspruefung(fakten, rechne_veranstaltung, ["veranstalt"], zusatz_veranstaltung)
        return _mit_rechnungsteller_hinweis(fakten, ergebnis)

    if fakten.positionen or fakten.gesamtbetrag_genannt is not None:
        if fakten.verwerterart is None:
            return KernErgebnis(RUECKFRAGE_NOETIG, rueckfragen=[pflichtangaben.FRAGE_VERWERTERART])
        def rechne_positionen(unsicher_zaehlt: bool) -> K.Ergebnis:
            return K.pruefe_positionen(
                jahr, _kern_positionen_oder_gesamtbetrag(fakten, unsicher_zaehlt),
                typischer_verwerter=(fakten.verwerterart == "typischer_verwerter"),
            )

        def rechne_variante(zusaetzlich: list) -> K.Ergebnis:
            """Wie oben (ohne unsichere Leistungen), plus die offenen Provisionsbeträge."""
            return K.pruefe_positionen(
                jahr, _kern_positionen_oder_gesamtbetrag(fakten, False) + [{"betrag": b} for b in zusaetzlich],
                typischer_verwerter=(fakten.verwerterart == "typischer_verwerter"))

        stichworte = ["typischer verwerter"] if fakten.verwerterart == "typischer_verwerter" else ["eigenwerb"]
        ergebnis = _mit_taetigkeitspruefung(fakten, rechne_positionen, stichworte, lambda _u: {})
        return _mit_rechnungsteller_hinweis(fakten, ergebnis, rechne_variante)

    return KernErgebnis(
        klasse=NICHT_ABGEDECKT,
        grund="Weder Positionen/Betrag noch Veranstaltungszahl angegeben – ohne Zahlen kann nichts geprüft werden.",
    )


_SATZ_ABKUERZUNG_MUSTER = re.compile(r"\bS\.\s*(\d+)\b")
_AKTUELL_VERMERK_MUSTER = re.compile(r"\s*\(aktuell\)", re.IGNORECASE)


def _fundstelle_schluessel(fundstelle: str) -> str:
    """Normalisiert eine Fundstelle fuer den Vergleich (Livetest-Befund L6): 'S. 2' und
    'Satz 2' sowie ein zusaetzlicher '(aktuell)'-Vermerk gelten als dieselbe Fundstelle.
    Aendert nichts an der ANGEZEIGTEN Schreibweise -- nur am Vergleich, welche Fundstellen
    als Duplikat zusammengefasst werden."""
    text = _AKTUELL_VERMERK_MUSTER.sub("", fundstelle)
    text = _SATZ_ABKUERZUNG_MUSTER.sub(lambda m: f"Satz {m.group(1)}", text)
    return re.sub(r"\s+", " ", text.strip().lower())


def _vereinheitliche_fundstellen(fundstellen: list[str]) -> list[str]:
    """Entfernt nicht nur textgleiche (siehe dict.fromkeys), sondern auch nur anders
    geschriebene Duplikate (z. B. 'KSVG § 24 Abs. 2 Satz 2' und '... S. 2 (aktuell)')
    -- behaelt die erste gesehene Schreibweise."""
    gesehen: dict[str, str] = {}
    for f in fundstellen:
        schluessel = _fundstelle_schluessel(f)
        if schluessel not in gesehen:
            gesehen[schluessel] = f
    return list(gesehen.values())


def _ebenen_abschnitt(kontext: AntwortKontext) -> str:
    """System-komponierte Ebenen-Kennzeichnung (NICHT vom Modell -- das darf laut
    Nachtrag Punkt 3 keine Gerichtswoerter schreiben). Nutzt dieselbe Gruppierung wie
    app/baustein.py::erzeuge_platzhalter."""
    zeilen: list[str] = []
    urteile = [r.get("fundstelle") for r in kontext.regeln if r.get("typ") == "urteil" and r.get("fundstelle")]
    if urteile:
        zeilen.append("**Rechtsprechung:** " + "; ".join(urteile))
    normen = [r.get("fundstelle") or r.get("norm") for r in kontext.regeln if r.get("typ") == "gesetz"]
    normen = [n for n in normen if n]
    if normen:
        zeilen.append("**Norm:** " + "; ".join(normen))
    verwaltung = [r.get("fundstelle") for r in kontext.regeln if r.get("typ") == "verwaltungspraxis" and r.get("fundstelle")]
    if verwaltung:
        zeilen.append("**Verwaltungspraxis (Auslegung der KSK, kein Gesetz):** " + "; ".join(verwaltung))
    bereits = {r.get("fundstelle") for r in kontext.regeln}
    belege = [b for b in kontext.belegstellen if b not in bereits]
    if belege:
        zeilen.append("**Belegstellen im Quelltext:** " + "; ".join(belege))
    return "\n".join(zeilen)


def _ausgeben(frage: str, fakten: Fakten, kontext: AntwortKontext, llm: LLM,
              pruefung: gegenrechnung.Pruefung | None = None) -> Antwort:
    """Einziger Ausgabepunkt (seit Teil 1c: in jedem Pfad aktiv; seit Teil 1g: Mischform).
    Ablauf:
    1. app/baustein.py erzeugt die fuer DIESE Antwort erlaubten Platzhalter aus dem Kontext.
    2. Der Antwort-KOERPER kommt ausschliesslich aus festen Textbausteinen aus dem
       Regelkatalog (app/textbausteine.py) -- KEIN Modellaufruf dafuer mehr. Passt kein
       inhaltlicher Baustein, wird das als "Baustein fehlt" protokolliert (anonymisiert),
       die Ergebnisklasse und der Schlusssatz werden trotzdem ausgegeben.
    3. Das Modell darf hoechstens EINE kurze Fallbeschreibung liefern (`llm.beschreibe_fall`,
       nur Platzhalter, keine Werte). Sie laeuft durch dieselbe `pruefe_rohtext`-Kontrolle
       wie frueher der ganze Koerper (alle Nachtraege); verstoesst sie, oder faellt das
       Modell aus (`LLMFehlgeschlagen`/jeder andere Fehler), entfaellt NUR die
       Fallbeschreibung -- nie die ganze Antwort, nie 'Pruefung fehlgeschlagen' deswegen.
    4. Ergebnis-Zeile, Ebenen-Abschnitt und Schlusssatz setzt dieser Router, nie das Modell.
    5. app/pruefung.py (Teil 1c) laeuft als zweites Netz auf dem FERTIGEN Text. Schlaegt es
       an, ist das ein echter Befund (z. B. ein fehlerhafter Textbaustein) -- genereller
       Ersatztext ohne den erfundenen/beanstandeten Inhalt im Klartext (Nachtrag 6)."""
    werte = erzeuge_platzhalter(kontext)
    erlaubte_namen = set(werte.keys())

    auswahl = textbausteine.waehle_bausteine(werte, kontext.ergebnisklasse, fakten.jahr)
    if auswahl.leerfall:
        protokolliere(frage, fakten.jahr, "Baustein fehlt (kein passender Textbaustein fuer dieses Kernergebnis)")
    bausteintexte = list(auswahl.texte)
    for name in sorted(k for k in werte if k.startswith("RUECKFRAGE_")):
        bausteintexte.append("{" + name + "}")
    for name in sorted(k for k in werte if k.startswith("HINWEIS_")):
        bausteintexte.append("{" + name + "}")
    koerper = fuelle("\n".join(bausteintexte), werte)

    beschreibung: str | None = None
    try:
        beschreibung_roh = llm.beschreibe_fall(kontext)
    except Exception as fehler:  # noqa: BLE001 -- ein Modellfehler darf die Antwort nie zum Absturz bringen
        protokolliere(frage, fakten.jahr, f"Fallbeschreibung fehlgeschlagen: {fehler}")
        beschreibung_roh = None
    if beschreibung_roh is not None:
        verstoesse = pruefe_rohtext(beschreibung_roh, erlaubte_namen)
        if verstoesse:
            protokolliere(frage, fakten.jahr, f"Fallbeschreibung verworfen: {'; '.join(verstoesse)}")
        else:
            beschreibung = fuelle(beschreibung_roh, werte)

    ergebnis_zeile = f"**Ergebnis (Vorschlag):** {kontext.ergebnisklasse}"
    ebenen = _ebenen_abschnitt(kontext)
    teile = [ergebnis_zeile]
    if beschreibung:
        teile.append(beschreibung)
    teile.append(koerper)
    if ebenen:
        teile.append(ebenen)
    pruefzeile = gegenrechnung.zeile(pruefung) if pruefung is not None else None
    if pruefzeile:
        teile.append(pruefzeile)
    teile.append(f"*{SCHLUSSSATZ}*")
    text = "\n".join(teile)

    # Zitierzwang (Teil 2): geliefert sind die Daten des Kontexts und die verwendeten Textbausteine
    # (geprüfte Texte aus der Excel). Alles andere an Regel-IDs/Aktenzeichen lehnt die Prüfung ab.
    if kontext.gelieferte_belege is None:
        kontext.gelieferte_belege = [*auswahl.texte, *kontext.belegstellen]
    pruefungsergebnis = pruefe_antwort(text, kontext)
    if not pruefungsergebnis.ok:
        grund = "; ".join(pruefungsergebnis.gruende)
        protokolliere(frage, fakten.jahr, f"Pruefung fehlgeschlagen (nach Einsetzen): {grund}")
        return Antwort(
            antwort=f"{ERSATZTEXT_ALLGEMEIN}\n*{SCHLUSSSATZ}*",
            ergebnisklasse=PRUEFUNG_FEHLGESCHLAGEN,
            kern_protokoll=kontext.kern_protokoll,
        )

    return Antwort(
        antwort=text, ergebnisklasse=kontext.ergebnisklasse, rueckfragen=kontext.rueckfragen,
        fundstellen=kontext.fundstellen, kern_protokoll=kontext.kern_protokoll,
        rueckfrage_optionen=pflichtangaben.rueckfrage_optionen(kontext.rueckfragen, kontext.fakten),
        pruefprotokoll=_pruefprotokoll(pruefung),
    )


def _quellenabruf(frage: str, jahr: int | None, regel_ids: list[str] | None = None):
    """RAG (Teil 2): Quellenabruf über app/rag/suche.py. Fällt der Index aus (z. B. pypdf fehlt),
    läuft die Antwort ohne Quellenabruf weiter -- protokolliert, nie mit Modellwissen aufgefüllt.
    RAG_AUS=1 schaltet den Abruf ab (nur zum Vergleich in Testläufen)."""
    import os

    if os.environ.get("RAG_AUS") == "1":
        return None
    try:
        from app.rag.suche import suche

        return suche(frage, jahr, regel_ids)
    except Exception as fehler:  # noqa: BLE001 -- der Abruf darf eine Antwort nie zum Absturz bringen
        protokolliere(frage, jahr, f"Quellenabruf nicht verfügbar: {fehler}")
        return None


_BELEGSTELLEN_MAX = 3


def _als_quellen_eintrag(stueck) -> dict[str, Any] | None:
    """Ein geliefertes Stück als Eintrag für AntwortKontext.regeln: Regeln wie bisher über den
    Regelkatalog (Ebene aus dem Vorbehalt), Quelltext-Stellen mit ihrer Ebene aus dem Index."""
    if stueck.art == "Regel" and stueck.regel_ids:
        regel = _regel_eintrag_fuer(stueck.regel_ids[0])
        return _als_regel_eintrag(regel) if regel else None
    if stueck.nur_hinweis:
        return None
    return {"regel_id": None, "typ": stueck.typ, "fundstelle": stueck.fundstelle, "stufe": stueck.stufe}


def _rechtsprechungsfrage(frage: str, fakten: Fakten, llm: LLM) -> Antwort:
    """Reine Recherche ohne Berechnung (Befund 6, behoben): keine Faktenbestaetigung, kein
    Kern-Aufruf, nie eine Zahl in der Antwort. Seit Teil 2 (RAG): Quellen kommen aus dem
    Quellenabruf (app/rag/suche.py) -- Regeln des Katalogs UND Stellen aus Gesetz, Urteilen und
    KSK-/DRV-Texten, jeweils mit Fundstelle und passend zum Jahr, wenn eines genannt ist.
    Sekundärquellen/Gesetzesmaterial nur als Hinweis. Nichts gefunden -> 'Nicht abgedeckt'."""
    suchtext = fakten.freitext_rest or frage
    erg = _quellenabruf(suchtext, fakten.jahr)
    if erg is None:
        stichworte = [w.strip(".,;:?!()„\"") for w in suchtext.split() if len(w) >= 4]
        regeln = [_als_regel_eintrag(r) for r in quellen.regeln_suchen_ohne_jahr(stichworte)]
        hinweise: list[str] = []
    else:
        regeln = [e for e in (_als_quellen_eintrag(t) for t in erg.stuecke) if e]
        hinweise = [f"Hinweis (Sekundärquelle bzw. Gesetzesmaterial, kein Beleg): {t.fundstelle}"
                    for t in erg.stuecke if t.nur_hinweis] + list(erg.hinweise)
    fundstellen = _vereinheitliche_fundstellen([r["fundstelle"] for r in regeln if r.get("fundstelle")])

    if not regeln:
        grund = (erg.grund if erg is not None and erg.grund else "Keine passende Quelle (Urteil/Auslegung) in der Quellenbasis gefunden.")
        protokolliere(frage, fakten.jahr, f"Rechtsprechungsfrage ohne Treffer in der Quellenbasis: {grund}")
        kontext = AntwortKontext(
            frage=frage, fakten=fakten, ergebnisklasse=NICHT_ABGEDECKT,
            hinweise=[grund],
        )
        return _ausgeben(frage, fakten, kontext, llm)

    kontext = AntwortKontext(
        frage=frage, fakten=fakten, ergebnisklasse=RECHTSPRECHUNG_GEFUNDEN,
        regeln=regeln, fundstellen=fundstellen, hinweise=hinweise,
    )
    return _ausgeben(frage, fakten, kontext, llm)


HINWEIS_TEXT = (
    "Hallo! Ich bin ein Entwurf-Chatbot zur Künstlersozialabgabe (Künstlersozialversicherungsgesetz) – ich mache "
    "Vorschläge, kein Ersatz für Rechtsberatung; ein Steuerberater prüft das Ergebnis.\n"
    "Ich kann zum Beispiel: prüfen, ob eine Zahlung an einen Künstler oder Publizisten "
    "abgabepflichtig ist; den Abgabesatz oder die Geringfügigkeitsgrenze eines Jahres aus "
    "dem Regelwerk nennen; einen Säumniszuschlag berechnen.\n"
    "Beispiele:\n"
    "– „Ein Grafiker bekommt ein Honorar von einer GmbH, ist das abgabepflichtig?“\n"
    "– „Wie hoch ist der aktuelle Abgabesatz?“\n"
    "– „Ich habe einen Rückstand bei der Abgabe, wie hoch ist der Säumniszuschlag?“"
)


def _hinweis_antwort(fakten: Fakten) -> Antwort:
    """Teil 1f, Abschnitt J.3: Begruessung/Smalltalk ("hallo", "danke", "was kannst du?")
    ohne jede Sachfrage -- feste, vom SYSTEM formulierte Antwort, kein Modellaufruf, keine
    Pflichtangaben-Rueckfrage. Die Erkennung beruht auf dem festen Schema-Feld
    `anfrageart == "hinweis"` (vom Modell/der Heuristik gesetzt), nicht auf einer
    Wortliste im App-Code."""
    return Antwort(antwort=f"{HINWEIS_TEXT}\n*{SCHLUSSSATZ}*", ergebnisklasse=HINWEIS)


def _mit_sitzung(antwort: Antwort, sitzungskennung: str | None) -> Antwort:
    """Test-Dialog 'Der schwierige Kunde': auch ein fertiges Ergebnis trägt die Sitzung des Falls,
    damit die Oberfläche sie für Nachfragen als `letzte_sitzung` mitschicken kann."""
    if sitzungskennung and not antwort.sitzungskennung:
        antwort.sitzungskennung = sitzungskennung
    return antwort


def _pruefprotokoll(pruefung: gegenrechnung.Pruefung | None) -> dict[str, Any]:
    if pruefung is None or pruefung.status == "ohne_rechnung":
        return {}
    return {"status": pruefung.status, "grund": pruefung.grund, **pruefung.protokoll}


def _kern_mit_gegenrechnung(fakten: Fakten) -> tuple[KernErgebnis, gegenrechnung.Pruefung]:
    """Teil 1e: Kern aufrufen (mit Mitschnitt jeder Rechnung), die Werte aus dem Register ergänzen, die die Antwort
    zeigt (Abgabesatz, Schwelle), und alles unabhängig gegenrechnen (eigener Prozess, app/sandbox.py)."""
    beginn = time.perf_counter()
    with gegenrechnung.mitschnitt() as m:
        kern_ergebnis = _rufe_kern_auf(fakten)
        if fakten.jahr is not None:
            # Teil 1f, Abschnitt B: der Baustein ABGABESATZ (und der Satz "Abgabe beim
            # Abgabesatz ...") gehoert nur zu einer Bemessungsgrundlage-mal-Satz-Rechnung, nie
            # zum Saeumniszuschlag (eigene 1%-je-Monat-Regel, siehe kern.rechnen.saeumniszuschlag).
            # Fuer anfrageart=="auskunft" setzt _rufe_kern_auf abgabesatz_prozent bereits direkt
            # (siehe dort) -- dieses Auto-Setzen hier greift nur dort nicht ein (setdefault).
            hat_bemessungsgrundlage = (
                "bemessungsgrundlage" in kern_ergebnis.protokoll
                or "bemessungsgrundlage_nach_pauschale" in kern_ergebnis.protokoll
            )
            if hat_bemessungsgrundlage:
                abgabesatz = K.abgabesatz(fakten.jahr)
                if abgabesatz is not None:
                    kern_ergebnis.protokoll.setdefault("abgabesatz_prozent", abgabesatz)

            # Schwelle nur dann als Platzhalter anbieten, wenn der Kern sie in der eigenen
            # Begruendung tatsaechlich verwendet hat (z. B. Eigenwerbung/typischer Verwerter,
            # >3 Veranstaltungen) -- NICHT bei der Drei-Veranstaltungen-Ausnahme, wo die Schwelle
            # fuer die Entscheidung irrelevant ist (kern.rechnen.veranstaltungen). Sonst wuerde
            # app/baustein.py eine Zahl einsetzen, die app/pruefung.py zu Recht als nicht aus dem
            # Kernergebnis stammend ablehnt (Befund, dieses Phase).
            schwelle_info = K.schwelle(fakten.jahr)
            if schwelle_info and schwelle_info.get("euro") is not None:
                subsumtion = str(kern_ergebnis.protokoll.get("subsumtion", ""))
                if str(schwelle_info["euro"]) in subsumtion:
                    kern_ergebnis.protokoll.setdefault("schwelle", Decimal(str(schwelle_info["euro"])))
    kern_fertig = time.perf_counter()
    pruefung = gegenrechnung.pruefe(m, kern_ergebnis.protokoll)
    if pruefung.protokoll is not None and pruefung.status != "ohne_rechnung":
        # Teil 1e, E.3: Dauer je Schritt (Kern; Gegenrechnung samt Prozessstart) im Prüfprotokoll, ohne Inhalte.
        pruefung.protokoll["dauer_kern_ms"] = round((kern_fertig - beginn) * 1000, 1)
        pruefung.protokoll["dauer_gegenrechnung_gesamt_ms"] = round((time.perf_counter() - kern_fertig) * 1000, 1)
    return kern_ergebnis, pruefung


def _nach_bestaetigung(frage: str, fakten: Fakten, llm: LLM, sitzungskennung: str | None = None,
                       zusatz_protokoll: dict[str, Any] | None = None) -> Antwort:
    """Alles, was NACH der Faktenbestaetigung passiert: Kern aufrufen, Quellen anreichern,
    Bausteinantwort erzeugen und pruefen. `zusatz_protokoll`: feste Hinweise zu einer Nachfrage
    (Test-Dialog 'Der schwierige Kunde'), z. B. {'nachfrage_widerspruch': 'ja'} -> TB-32."""
    # 14.10.2026 (Testfall L-23): ein Betrag nur in fremder Währung wird nie gerechnet.
    euro_offen = pflichtangaben.euro_fragen(fakten)
    if euro_offen:
        return _rueckfrage_antwort(euro_offen, fakten, sitzungskennung)
    kern_ergebnis, pruefung = _kern_mit_gegenrechnung(fakten)
    if not pruefung.gibt_aus:
        # Teil 1e: Kern und Gegenrechnung stimmen nicht überein (oder die Gegenrechnung ist ausgefallen): die Antwort
        # wird nicht ausgegeben. Lückenprotokoll anonymisiert, mit Fall-Kennung (Hash der Eingaben).
        protokolliere(frage, fakten.jahr, f"Gegenrechnung {pruefung.status} (Fall {pruefung.protokoll.get('fall')}): "
                                          f"{pruefung.grund}")
        return _mit_sitzung(Antwort(
            antwort=f"{gegenrechnung.text_fehlgeschlagen(pruefung)}\n*{SCHLUSSSATZ}*",
            ergebnisklasse=PRUEFUNG_FEHLGESCHLAGEN, pruefprotokoll=_pruefprotokoll(pruefung),
        ), sitzungskennung)
    if pruefung.status == "nicht_gegengerechnet":
        protokolliere(frage, fakten.jahr, f"Nicht gegengerechnet: {pruefung.grund}")
    if zusatz_protokoll:
        kern_ergebnis.protokoll.update(zusatz_protokoll)

    # Pruefkatalog-Befund (entdeckt beim Beheben von M3, aufgaben/FUNDE_Chatbot.md): anders
    # als kern.rechnen.pruefe_eigenwerbung (das bei einer Bemessungsgrundlage von 0 unter
    # jeder Schwelle bleibt) liefert kern.rechnen.pruefe_typischer_verwerter "Abgabepflichtig"
    # UNABHAENGIG von der Bemessungsgrundlage -- z. B. wenn die einzige Position an eine nach
    # R-138/R-216 ausgenommene GmbH/KG ging und die Bemessungsgrundlage deshalb 0 ist. Bei 0
    # gibt es nichts zu erheben; die Anzeige wird hier korrigiert, der Kern bleibt unveraendert
    # (ausserhalb des erlaubten Bereichs dieses Auftrags).
    if kern_ergebnis.klasse == K.ABGABEPFLICHTIG and kern_ergebnis.protokoll.get("bemessungsgrundlage") == Decimal("0"):
        kern_ergebnis.klasse = K.NICHT

    if kern_ergebnis.klasse == RUECKFRAGE_NOETIG:
        # Nachtrag Abschnitt B: wie beim Pflichtangaben-Fall in bearbeite_frage -- feste
        # Textbausteine, kein Modellaufruf (auch die Rueckfragen des Kerns selbst, z. B.
        # "Rundung ungeklaert", duerfen nicht um erfundenen Modelltext ergaenzt werden).
        return _rueckfrage_antwort(kern_ergebnis.rueckfragen, fakten, sitzungskennung)

    if kern_ergebnis.klasse == NICHT_ABGEDECKT:
        protokolliere(frage, fakten.jahr, kern_ergebnis.grund or "unbekannt")
        kontext = AntwortKontext(
            frage=frage, fakten=fakten, ergebnisklasse=NICHT_ABGEDECKT,
            hinweise=[kern_ergebnis.grund or "Nicht abgedeckt"],
        )
        return _mit_sitzung(_ausgeben(frage, fakten, kontext, llm, pruefung), sitzungskennung)

    art = fakten.anfrageart or "bewertung"

    # ALLTAG-2026-999: Der Kern nennt für jeden typischen Verwerter R-07 (§ 24 Abs. 1 Nr. 7, Werbung
    # für Dritte). Die Nummer richtet sich nach der Art des Unternehmens (app/verwerter_nummer.json):
    # R-07 wird durch die erkannte Regel ersetzt; ist die Art unbekannt, entfällt die Nummer.
    if fakten.verwerterart == "typischer_verwerter" and "R-07" in kern_ergebnis.regel_ids:
        ersatz = fakten.verwerter_regel.split(";") if fakten.verwerter_regel else []
        kern_ergebnis.regel_ids = list(dict.fromkeys(
            x for r in kern_ergebnis.regel_ids for x in (ersatz if r == "R-07" else [r])))
    # 14.10.2026: Musikverein nach der Generalklausel -- die Vereinsregeln (R-30, R-57) gehören zur Begründung.
    if fakten.verwerterart == "generalklausel" and fakten.verwerter_regel:
        kern_ergebnis.regel_ids = list(dict.fromkeys(kern_ergebnis.regel_ids + fakten.verwerter_regel.split(";")))
    regeln = [_als_regel_eintrag(_regel_eintrag_fuer(regel_id)) for regel_id in kern_ergebnis.regel_ids]
    regeln = [r for r in regeln if r is not None]
    fundstellen_aus_kern = [quellen.bereinige_fundstelle(f) for f in kern_ergebnis.fundstellen_kern]
    fundstellen = fundstellen_aus_kern + [r["fundstelle"] for r in regeln if r.get("fundstelle")]
    fundstellen = _vereinheitliche_fundstellen([f for f in fundstellen if f])

    if kern_ergebnis.klasse == GRENZFALL:
        protokolliere(frage, fakten.jahr, "Grenzfall -- Steuerberater entscheidet")

    # Teil 1f, Abschnitt B: eine berechnete Saeumniszuschlag-Summe ist keine Abgabepflicht-
    # Entscheidung -- die generische Kernklasse ABGABEPFLICHTIG waere hier falsch benannt
    # (siehe app/ergebnisklassen.py::SAEUMNISZUSCHLAG_BERECHNET). Intern bleibt die
    # Kernklasse im Protokoll erhalten.
    angezeigte_klasse = kern_ergebnis.klasse
    if art == "saeumniszuschlag" and kern_ergebnis.klasse == K.ABGABEPFLICHTIG:
        kern_ergebnis.protokoll.setdefault("kern_klasse", kern_ergebnis.klasse)
        angezeigte_klasse = SAEUMNISZUSCHLAG_BERECHNET

    # RAG (Teil 2), Regelfilter: zu den Regeln des Kerns die Quelltext-Stellen, die ihre Fundstelle
    # nennt (Belegstellen zum Nachlesen), und der Hinweis, wenn eine Quelle geändert wurde.
    hinweise = list(kern_ergebnis.rueckfragen)
    belegstellen: list[str] = []
    abruf = _quellenabruf(frage, fakten.jahr, kern_ergebnis.regel_ids) if kern_ergebnis.regel_ids else None
    if abruf is not None:
        belegstellen = [t.fundstelle for t in abruf.belegstellen[:_BELEGSTELLEN_MAX]]
        hinweise += [h for h in abruf.hinweise if h not in hinweise]

    kontext = AntwortKontext(
        frage=frage, fakten=fakten, ergebnisklasse=angezeigte_klasse,
        kern_protokoll=kern_ergebnis.protokoll, regeln=regeln, fundstellen=fundstellen,
        hinweise=hinweise, belegstellen=belegstellen,
    )
    return _mit_sitzung(_ausgeben(frage, fakten, kontext, llm, pruefung), sitzungskennung)


def _fakten_zusammenfuehren(alt: Fakten, neu: Fakten) -> Fakten:
    """Pruefkatalog-Befund M1, Punkt 2: Felder, die in dieser Sitzung bereits bekannt sind
    (aus einer vorherigen Nachricht), gehen bei einer neuen, freien Extraktion nicht verloren
    -- die neue Extraktion ERGAENZT nur, was sie selbst liefert (nicht `None`/leer); liefert
    sie fuer ein Feld nichts, bleibt der bisherige Sitzungswert erhalten. Eine nicht-leere
    `positionen`-Liste von `neu` ersetzt die von `alt` vollstaendig (keine Vermischung
    einzelner Positionen)."""
    alt_daten = alt.model_dump(mode="python")
    neu_daten = neu.model_dump(mode="python")
    zusammengefuehrt = dict(alt_daten)
    for feld, wert in neu_daten.items():
        if wert in (None, [], ""):
            continue
        zusammengefuehrt[feld] = wert
    return Fakten.model_validate(zusammengefuehrt)


_WIDERSPRUCH_FELD = "widerspruch_gesamtbetrag"


def _widerspruch_gesamtbetrag(frage: str, fakten: Fakten, sitzungskennung: str | None) -> Antwort | None:
    """Livetest 10.10.2026: Die Bestätigung zeigte 'Summe der Positionen 4.000 € passt nicht
    zum genannten Gesamtbetrag 2.000 €', liess aber 'Ja, das stimmt' zu -- gerechnet wurde mit
    der falschen Variante. Bei einem Widerspruch wählt das System keine Variante: es fragt mit
    zwei Schaltflächen nach (Gesamtbetrag stimmt / Einzelbeträge stimmen) oder der Nutzer
    beschreibt die Beträge neu."""
    from app.plausibilitaet import gesamtbetrag_warnung

    warnung = gesamtbetrag_warnung(fakten)
    if warnung is None:
        return None
    sitzungskennung = sitzungskennung or bestaetigung.SPEICHER.neue_sitzungskennung()
    bestaetigung.SPEICHER.setze_fakten(sitzungskennung, frage, fakten)
    bestaetigung.SPEICHER.setze_offene_fragen(sitzungskennung, [pflichtangaben.FRAGE_WIDERSPRUCH_GESAMTBETRAG])
    gesamt = formatiere_betrag(fakten.gesamtbetrag_genannt)
    summe = formatiere_betrag(fakten.summe_positionen())
    knopf_gesamt = f"Gesamtbetrag stimmt ({gesamt})"
    knopf_einzeln = f"Einzelbeträge stimmen ({summe})"
    zeilen = [
        f"**Ergebnis (Vorschlag):** {RUECKFRAGE_NOETIG}",
        f"Die Angaben widersprechen sich: {warnung}",
        f"– {pflichtangaben.FRAGE_WIDERSPRUCH_GESAMTBETRAG} Oder beschreiben Sie die Beträge bitte neu.",
        f"*{SCHLUSSSATZ}*",
    ]
    return Antwort(
        antwort="\n".join(zeilen),
        ergebnisklasse=RUECKFRAGE_NOETIG,
        rueckfragen=[pflichtangaben.FRAGE_WIDERSPRUCH_GESAMTBETRAG],
        rueckfrage_optionen=[{
            "frage": pflichtangaben.FRAGE_WIDERSPRUCH_GESAMTBETRAG,
            "optionen": [knopf_gesamt, knopf_einzeln],
            "feld": _WIDERSPRUCH_FELD,
            "werte": {knopf_gesamt: "gesamt", knopf_einzeln: "einzeln"},
        }],
        sitzungskennung=sitzungskennung,
        fakten_zusammenfassung=bestaetigung.als_liste(fakten),
    )


_ZAHL_ANTWORT = re.compile(r"^\s*(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{1,2}))?\s*(€|eur|euro)?\s*\.?\s*$", re.IGNORECASE)


_UNBEKANNT_BEGRIFFE: list[str] = json.loads(
    (Path(__file__).resolve().parent / "unbekannt_begriffe.json").read_text(encoding="utf-8"))["unbekannt"]


def _unbekannt_als_antwort(frage: str, offene_fragen: list[str]) -> tuple[str, Any] | None:
    """Livetest 11.10.2026: Auf die Frage nach der Zahl der Veranstaltungen soll 'weiß ich
    nicht' möglich sein. Nur wenn genau diese Frage offen ist und die Antwort kurz ist und einen
    Begriff aus app/unbekannt_begriffe.json enthält -- sonst entscheidet wie bisher das Modell."""
    if pflichtangaben.FRAGE_VERANSTALTUNGSZAHL not in offene_fragen or len(frage) > 60:
        return None
    text = zuordnung._vereinheitliche(frage)
    if any(zuordnung._vereinheitliche(b) in text for b in _UNBEKANNT_BEGRIFFE):
        return ("veranstaltungszahl_unbekannt", True)
    return None


def _zahl_als_antwort(frage: str, offene_fragen: list[str]) -> tuple[str, Any] | None:
    """Livetest 10.10.2026: Auf 'Wie viele einschlägige Veranstaltungen ...?' antwortete der
    Nutzer '2', auf die Betragsfrage '2000' -- das Modell sieht nur die Zahl, nicht die Frage,
    und übernahm sie nicht (oder als Jahr). Besteht die Nachricht NUR aus einer Zahl und passt
    sie zu GENAU EINER offenen Zahlenfrage, wird sie dieser Frage fest zugeordnet. Mit '€',
    'EUR' oder 'Euro' kommt nur der Betrag in Frage. Passen mehrere Fragen (z. B. Jahr und
    Betrag), wird nicht geraten -- dann entscheidet wie bisher das Modell."""
    treffer = _ZAHL_ANTWORT.match(frage)
    if not treffer:
        return None
    ganz, nachkomma, waehrung = treffer.groups()
    betrag = Decimal(ganz.replace(".", "") + (f".{nachkomma}" if nachkomma else ""))
    kandidaten: list[tuple[str, Any]] = []
    if pflichtangaben.FRAGE_BETRAG in offene_fragen:
        kandidaten.append(("gesamtbetrag_genannt", betrag))
    if not waehrung and not nachkomma:
        if pflichtangaben.FRAGE_VERANSTALTUNGSZAHL in offene_fragen:
            kandidaten.append(("veranstaltungszahl", int(betrag)))
        if pflichtangaben.FRAGE_JAHR in offene_fragen:
            kandidaten.append(("jahr", int(betrag)))
    return kandidaten[0] if len(kandidaten) == 1 else None


def _euro_betrag_als_antwort(frage: str, offene_fragen: list[str], fakten: Fakten | None) -> Fakten | None:
    """14.10.2026 (Testfall L-23): Antwort auf 'Welcher Betrag wurde in Euro tatsächlich gezahlt?'.
    Enthält die Nachricht GENAU EINEN Euro-Betrag (oder ist sie nur eine Zahl), wird er fest der
    ersten offenen Euro-Frage zugeordnet -- ohne Modell, ohne Umrechnung. Sonst None (wie bisher)."""
    if fakten is None:
        return None
    ziele = [(f, pflichtangaben.euro_frage_ziel(f, fakten)) for f in offene_fragen]
    ziele = [(f, z) for f, z in ziele if z is not None]
    if not ziele:
        return None
    euro = zuordnung.betraege_im_text(frage)
    if not euro:
        nur_zahl = _ZAHL_ANTWORT.match(frage)  # nur eine Zahl ('1850' / '1.850,00')
        if nur_zahl:
            ganz, nachkomma, _ = nur_zahl.groups()
            euro = {Decimal(ganz.replace(".", "") + (f".{nachkomma}" if nachkomma else ""))}
    if len(euro) != 1:
        return None
    betrag = next(iter(euro))
    _, ziel = ziele[0]
    if ziel < 0:
        return fakten.model_copy(update={"gesamtbetrag_genannt": betrag, "gesamt_fremdwaehrung": None})
    positionen = [p.model_copy() for p in fakten.positionen]
    positionen[ziel] = positionen[ziel].model_copy(update={"betrag": betrag, "fremdwaehrung": None})
    return fakten.model_copy(update={"positionen": positionen})


def _blockierende_offene(fakten: Fakten) -> list[str]:
    """Ausdrücklich unbekannte Angaben, von denen die Bewertung abhängt: die Fragen, die ohne
    'unbekannt' noch gestellt würden (Testprotokoll 11.10.2026)."""
    ohne = fakten.model_copy(update={"unbekannt": [], "widersprueche": []})
    gebraucht = {pflichtangaben.feld_der_frage(f, ohne) for f in pflichtangaben.fehlende_pflichtangaben(ohne, alle=True)}
    gebraucht |= {alt for neu, alt in pflichtangaben.GLEICHE_FRAGE.items() if neu in gebraucht}
    return [k for k in fakten.unbekannt
            if k in gebraucht or (fallstand.zerlege(k)[1] is None and any(g and fallstand.zerlege(g)[0] == k for g in gebraucht))]


def _uebersicht_antwort(fakten: Fakten, rueckfragen: list[str], sitzungskennung: str | None,
                        zurueckgestellt: list[str]) -> Antwort:
    """Testprotokoll 11.10.2026: Übersicht aus dem gespeicherten Fallstand -- was ist erfasst,
    was ist ausdrücklich unbekannt oder widersprüchlich, was fehlt noch. Nur System-Text."""
    erfasst = [z for z in bestaetigung.als_liste(fakten) if not z.startswith(("Ausdrücklich unbekannt", "Widersprüchlich"))]
    offen = fallstand.offene_zeilen(fakten)
    zeilen = [f"**Ergebnis (Vorschlag):** {RUECKFRAGE_NOETIG}", "**Bisher erfasst:**"]
    zeilen += [f"– {z}" for z in erfasst] or ["– noch nichts"]
    if offen:
        zeilen.append("**Offen:**")
        zeilen += [f"– {z}" for z in offen]
    if zurueckgestellt:
        namen = ", ".join(fallstand.lesbar(k, fakten) for k in zurueckgestellt)
        zeilen.append(f"Die Bewertung ist zurückgestellt, bis geklärt ist: {namen}. "
                      "Sie können die Angaben später in diesem Fall ergänzen.")
    if rueckfragen:
        zeilen.append("Als Nächstes fehlt:" if len(rueckfragen) == 1 else "Als Nächstes fehlen:")
        zeilen += [f"– {r}" for r in rueckfragen]
    zeilen.append(f"*{SCHLUSSSATZ}*")
    return Antwort(
        antwort="\n".join(zeilen), ergebnisklasse=RUECKFRAGE_NOETIG, rueckfragen=list(rueckfragen),
        rueckfrage_optionen=pflichtangaben.rueckfrage_optionen(list(rueckfragen), fakten),
        sitzungskennung=sitzungskennung, fakten_zusammenfassung=erfasst + offen,
    )


def _mit_pflichtangaben_weiter(frage: str, fakten: Fakten, llm: LLM, sitzungskennung: str | None,
                               uebersicht: bool = False) -> Antwort:
    """Gemeinsamer Ablauf NACH der Fakten-Extraktion -- ob durch ein Modell (bearbeite_frage)
    oder durch eine deterministische Knopf-Antwort (wende_feldantwort_an): Pflichtangaben
    pruefen, Rueckfrage/Faktenbestaetigung/Kernaufruf. Eine Pflichtangaben-Luecke bekommt
    jetzt IMMER eine sitzungskennung (Pruefkatalog-Befund M1): nur so kann eine spaetere
    Knopf-Antwort oder eine freie Folgenachricht die bisherigen Fakten wiederfinden und
    ergaenzen, statt bei jeder Teilantwort wieder bei null anzufangen."""
    # Positionen desselben Auftragnehmers teilen die Rechtsform (auch nach einem Knopf).
    fakten = zuordnung.rechtsform_je_auftragnehmer(fakten)
    fakten = einordnung.leite_ab(fakten)
    fehlend = pflichtangaben.fehlende_pflichtangaben(fakten)
    if fehlend:
        # Nachtrag Abschnitt B: eine Rueckfrage wird AUSSCHLIESSLICH aus festen System-
        # Textbausteinen gebaut -- kein Aufruf von llm.formuliere_antwort, damit ein
        # Modell keine erfundenen Zusatzsaetze oder kaputte Formulierungen einstreuen kann.
        sitzungskennung = sitzungskennung or bestaetigung.SPEICHER.neue_sitzungskennung()
        bestaetigung.SPEICHER.setze_fakten(sitzungskennung, frage, fakten)
        bestaetigung.SPEICHER.setze_offene_fragen(sitzungskennung, fehlend)
        if uebersicht or fakten.unbekannt or fakten.widersprueche:
            return _uebersicht_antwort(fakten, fehlend, sitzungskennung, _blockierende_offene(fakten))
        return _rueckfrage_antwort(fehlend, fakten, sitzungskennung)

    zurueck = _blockierende_offene(fakten)
    if zurueck:
        sitzungskennung = sitzungskennung or bestaetigung.SPEICHER.neue_sitzungskennung()
        bestaetigung.SPEICHER.setze_fakten(sitzungskennung, frage, fakten)
        bestaetigung.SPEICHER.setze_offene_fragen(sitzungskennung, [])
        return _uebersicht_antwort(fakten, [], sitzungskennung, zurueck)

    widerspruch = _widerspruch_gesamtbetrag(frage, fakten, sitzungskennung)
    if widerspruch is not None:
        return widerspruch

    if fakten.anfrageart == "rechtsprechungsfrage":
        return _rechtsprechungsfrage(frage, fakten, llm)

    sitzungskennung = sitzungskennung or bestaetigung.SPEICHER.neue_sitzungskennung()
    bestaetigung.SPEICHER.setze_fakten(sitzungskennung, frage, fakten)
    bestaetigung.SPEICHER.setze_offene_fragen(sitzungskennung, [])
    if not bestaetigung.SPEICHER.ist_bestaetigt(sitzungskennung, fakten):
        text = f"{bestaetigung.zusammenfassung(fakten)}\n*{SCHLUSSSATZ}*"
        return Antwort(
            antwort=text, ergebnisklasse=FAKTEN_BESTAETIGUNG_NOETIG,
            sitzungskennung=sitzungskennung, fakten_hash=bestaetigung.fakten_hash(fakten),
            fakten_zusammenfassung=bestaetigung.als_liste(fakten),
        )

    return _nach_bestaetigung(frage, fakten, llm, sitzungskennung)


_NACHFRAGE = json.loads((Path(__file__).resolve().parent / "nachfrage_begriffe.json").read_text(encoding="utf-8"))


def _nachfrage_art(frage: str) -> str | None:
    t = frage.lower()
    for eintrag in _NACHFRAGE["arten"]:
        if any(b in t for b in eintrag["begriffe"]):
            return eintrag["art"]
    return None


def _nachfrage_zum_letzten_fall(frage: str, llm: LLM, letzte_sitzung: str):
    """Test-Dialog 'Der schwierige Kunde' (13.10.2026). Nach einem fertigen Ergebnis begann bisher
    jede Nachricht einen neuen, leeren Fall -- 'Das kann nicht stimmen' oder 'schick mir das
    Protokoll' bekamen eine Rückfrage nach dem Jahr oder eine Fehlermeldung.
    - Nachfrage (Wunsch nach anderem Ergebnis/Anweisung, Protokoll, Zahlung offen, Widerspruch):
      feste Antwort (TB-31 bis TB-34) und das UNVERÄNDERTE Ergebnis des letzten Falls, ohne Modell.
    - Neue Angaben zu denselben Positionen (alle genannten Beträge stehen schon im Fall, oder ein
      Wort aus einer Positionsbezeichnung): 'fortsetzen' -- der letzte Fall wird weitergeführt.
    - Sonst None: neuer Fall wie bisher (keine doppelten Beträge)."""
    fakten = bestaetigung.SPEICHER.hole_fakten(letzte_sitzung)
    if fakten is None or not bestaetigung.SPEICHER.ist_bestaetigt(letzte_sitzung, fakten):
        return None
    art = _nachfrage_art(frage)
    betraege = zuordnung.betraege_im_text(frage)
    alte = {Decimal(str(p.betrag)) for p in fakten.positionen} | {Decimal(str(r.gesamtbetrag)) for r in fakten.rechnungen}
    if art is not None and (not betraege or betraege <= alte):
        antwort = _nach_bestaetigung(frage, fakten, llm, letzte_sitzung, zusatz_protokoll={f"nachfrage_{art}": "ja"})
        if art == "protokoll":
            liste = "\n".join(f"– {z}" for z in bestaetigung.als_liste(fakten))
            antwort.antwort = f"{antwort.antwort}\n**Bestätigte Angaben:**\n{liste}"
        return antwort
    if betraege and betraege <= alte:
        return "fortsetzen"
    laenge = int(_NACHFRAGE["fortsetzung_wortlaenge"])
    woerter = {w for p in fakten.positionen for w in re.findall(r"\w+", (p.bezeichnung or "").lower()) if len(w) >= laenge}
    if not betraege and woerter & set(re.findall(r"\w+", frage.lower())):
        return "fortsetzen"
    return None


EINSTIEG_RUECKFRAGE = "Bitte schicken Sie die Rechnung als Text."


def _knopftext_norm(text: str) -> str:
    return " ".join(re.sub(r"[\"'„“”‚‘’.!?:;,()]", " ", text or "").lower().split())


def _knopftext_als_antwort(frage: str, offene: list[str], fakten: Fakten | None) -> tuple[str, Any, int | None] | None:
    """(feld, wert, position), wenn die Nachricht genau einem Knopftext einer offenen Frage entspricht (Groß-/
    Kleinschreibung und Satzzeichen egal). Alles andere ist freier Text und geht wie immer an das Sprachmodell."""
    if fakten is None or not offene:
        return None
    eingabe = _knopftext_norm(frage)
    treffer = []
    for eintrag in pflichtangaben.rueckfrage_optionen(offene, fakten):
        for anzeige, wert in (eintrag.get("werte") or {}).items():
            if eingabe and _knopftext_norm(anzeige) == eingabe:
                treffer.append((eintrag["feld"], wert, eintrag.get("position")))
    return treffer[0] if len(treffer) == 1 else None


def _einstieg_ohne_rechnung_antwort() -> Antwort:
    """Test-Dialog 'Der schwierige Kunde' (13.10.2026), Schritt 1: 'Ich habe eine Rechnung von einer
    Agentur bekommen ... Wir sind eine Messe'. Bisher fragte der Chatbot nur nach dem Jahr. Jetzt:
    keine Bewertung ohne Rechnung, kurze Erklärung, worauf es ankommt, und die Bitte um die
    Rechnung -- fester Baustein aus der Excel (Platzhalter EINSTIEG_OHNE_RECHNUNG), kein Modell,
    keine Sitzung (die Rechnung beginnt den Fall)."""
    auswahl = textbausteine.waehle_bausteine({"EINSTIEG_OHNE_RECHNUNG": "ja"}, RUECKFRAGE_NOETIG, None)
    text = "\n".join(auswahl.texte)
    return Antwort(
        antwort=f"**Ergebnis (Vorschlag):** {RUECKFRAGE_NOETIG}\n{text}\n*{SCHLUSSSATZ}*",
        ergebnisklasse=RUECKFRAGE_NOETIG,
        rueckfragen=[EINSTIEG_RUECKFRAGE],
    )


def bearbeite_frage(
    frage: str, llm: LLM, verlauf: list[str] | None = None, sitzungskennung: str | None = None,
    letzte_sitzung: str | None = None,
) -> Antwort:
    # Dialogtest Fallgrenzen (10.10.2026): Verlauf und Sitzungszustand gehören zu EINEM Fall.
    # - Kündigt die Nachricht ausdrücklich einen neuen Fall an, beginnt eine neue Sitzung, und
    #   der bisherige Verlauf geht weder ans Modell noch in die Textprüfungen.
    # - Läuft die Nachricht unter einer bekannten Sitzung, zählt nur der Verlauf ab deren Beginn.
    # - Ohne Sitzung bleibt es beim bisherigen Verhalten (ganzer mitgeschickter Verlauf).
    verlauf = list(verlauf or [])
    # Test-Dialog 'Der schwierige Kunde' (13.10.2026): Nachricht nach einem FERTIGEN Ergebnis.
    if sitzungskennung is None and letzte_sitzung and not zuordnung.ist_neuer_fall(frage):
        nachfrage = _nachfrage_zum_letzten_fall(frage, llm, letzte_sitzung)
        if isinstance(nachfrage, Antwort):
            return nachfrage
        if nachfrage == "fortsetzen":
            sitzungskennung = letzte_sitzung
    # Test-Dialog 'Der schwierige Kunde', Schritt 1: Rechnung angekündigt, aber nicht mitgeschickt.
    if sitzungskennung is None and zuordnung.rechnung_angekuendigt_ohne_inhalt(frage):
        return _einstieg_ohne_rechnung_antwort()
    if zuordnung.ist_neuer_fall(frage):
        sitzungskennung = bestaetigung.SPEICHER.neue_sitzung(verlauf_start=len(verlauf))
        verlauf_fall: list[str] = []
    else:
        start = bestaetigung.SPEICHER.hole_verlauf_start(sitzungskennung) if sitzungskennung else None
        if start is None:
            verlauf_fall = verlauf  # keine (bekannte) Sitzung: Sitzung entsteht später mit Beginn 0
        else:
            verlauf_fall = verlauf[start:]
            offene = bestaetigung.SPEICHER.hole_offene_fragen(sitzungskennung)
            euro = _euro_betrag_als_antwort(frage, offene, bestaetigung.SPEICHER.hole_fakten(sitzungskennung))
            if euro is not None:
                return _mit_pflichtangaben_weiter(frage, euro, llm, sitzungskennung)
            zahl = _zahl_als_antwort(frage, offene) or _unbekannt_als_antwort(frage, offene)
            if zahl is not None:
                return wende_feldantwort_an(sitzungskennung, zahl[0], zahl[1], llm)
            # Schritt 2 (17.10.2026): ein exakt abgetippter Knopftext ('Ein privater Auftrag') gilt wie der Knopf --
            # ohne Modellaufruf, nur bei der passenden offenen Frage.
            knopf = _knopftext_als_antwort(frage, offene, bestaetigung.SPEICHER.hole_fakten(sitzungskennung))
            if knopf is not None:
                return wende_feldantwort_an(sitzungskennung, knopf[0], knopf[1], llm, knopf[2])
            # Testprotokoll 11.10.2026, Schritt 9: 'Das ist noch ungeklärt. Bitte weder Ja noch
            # Nein annehmen. Welche Angaben sind erfasst?' -- die offene Frage wird als
            # ausdrücklich unbekannt vermerkt (nicht erneut gefragt), ohne Modellaufruf.
            bisher = bestaetigung.SPEICHER.hole_fakten(sitzungskennung)
            if (bisher is not None and offene and fallstand.antwort_ist_unbekannt(frage)
                    and not fallstand.unbekannt_im_text(frage)):
                key = pflichtangaben.feld_der_frage(offene[0], bisher)
                if key:
                    return _mit_pflichtangaben_weiter(frage, fallstand.markiere_unbekannt(bisher, key), llm,
                                                      sitzungskennung, uebersicht=fallstand.will_uebersicht(frage))

    bisherige_fakten = bestaetigung.SPEICHER.hole_fakten(sitzungskennung) if sitzungskennung else None

    try:
        fakten = _extrahiere(llm, frage, verlauf_fall, bisherige_fakten)
    except LLMFehlgeschlagen as fehler:
        protokolliere(frage, None, f"Fakten-Extraktion fehlgeschlagen: {fehler}")
        if bisherige_fakten is not None and sitzungskennung:
            # Test-Dialog 'Der schwierige Kunde': in einem laufenden Fall keine Fehlermeldung,
            # die alles offen lässt -- der Fallstand bleibt, die Übersicht zeigt ihn.
            return _uebersicht_antwort(bisherige_fakten, pflichtangaben.fehlende_pflichtangaben(bisherige_fakten),
                                       sitzungskennung, _blockierende_offene(bisherige_fakten))
        return _modellfehler_antwort(sitzungskennung, fehler)
    from app.log import protokolliere_fakten

    protokolliere_fakten(frage, "roh", fakten)
    fakten = zuordnung.ohne_systemfelder(fakten)
    # Testfall 20 Positionen, Small (17.10.2026): 'unbekannt' nur mit Beleg im Nutzertext.
    fakten = zuordnung.unbekannt_nur_mit_beleg("\n".join([*verlauf_fall, frage]), fakten)
    modell_verwerterart = fakten.verwerterart  # Lesart des Modells (für die Herkunft, app/einordnung.py)
    # Korpus-Lauf 15.10.2026: Beträge mit vorangestellter Währung ('EUR 1.500,00') für alle festen Prüfungen einheitlich
    # schreiben (app/textnorm.py). Nur der Prüftext; die Frage an das Modell bleibt, wie der Nutzer sie geschrieben hat.
    frage = textnorm.waehrung_nach_hinten(frage)
    verlauf_fall = [textnorm.waehrung_nach_hinten(v) for v in verlauf_fall]

    # Nachtrag Abschnitt A: die Anfrageart "auskunft"/"hinweis" wird deterministisch
    # gegengeprueft (app/zuordnung.py) -- ein Modell darf nicht ungeprueft entscheiden,
    # dass eine Rechnungsfrage eine Auskunftsfrage oder eine Begruessung ist.
    fakten = zuordnung.absichere_anfrageart(frage, fakten)

    # Pruefkatalog-Befunde M1.3/M3/M4: Rechtsform-Synonyme deterministisch ergaenzen, wenn
    # das Modell sie nicht selbst gesetzt hat; verwerterart gegen den Nutzertext pruefen
    # (typischer Verwerter hat Vorrang, ein nicht textlich belegter Modellwert wird verworfen)
    # -- auf Verlauf UND aktuelle Nachricht zusammen, nicht nur auf die neueste Nachricht.
    text_gesamt = "\n".join([*verlauf_fall, frage])
    fakten = zuordnung.jahr_nicht_aus_betrag(text_gesamt, fakten)
    if bisherige_fakten is None:
        fakten = zuordnung.jahr_nur_aus_text(text_gesamt, fakten)
    fakten = zuordnung.veranstaltungszahl_aus_text(text_gesamt, fakten)
    fakten = zuordnung.gesamtbetrag_nicht_als_position(fakten)
    fakten = zuordnung.gesamtbetrag_mit_rolle(text_gesamt, fakten)
    fakten = zuordnung.ergaenze_rechtsform(text_gesamt, fakten)
    fakten = zuordnung.absichere_verwerterart(text_gesamt, fakten)
    fakten = zuordnung.ergaenze_pauschale(text_gesamt, fakten)
    fakten = zuordnung.verwerter_aus_auftraggeber(text_gesamt, fakten)

    # Test des Nutzers im Codespace (16.10.2026): 'Wie hoch ist die Hundesteuer in Köln?' bekam den Begrüßungstext
    # (das Modell nannte es 'hinweis'). Eine echte Frage OHNE Bezug zur Künstlersozialabgabe und ohne Betrag (erste
    # Nachricht eines Falls) geht wie eine Recherche an den Quellenabruf, der dann 'Nicht abgedeckt' meldet. Eine kurze
    # Begrüßung ('Hallo', 'Was kannst du?') bleibt ein Hinweis (app/einstieg_begriffe.json, 'hinweis_max_woerter').
    if (bisherige_fakten is None and "?" in frage and not zuordnung.betraege_im_text(frage)
            and len(frage.split()) > zuordnung.hinweis_max_woerter() and fakten.anfrageart in (None, "hinweis", "bewertung")):
        from app.rag.suche import frage_hat_themenbezug

        if not frage_hat_themenbezug(frage):
            return _rechtsprechungsfrage(frage, fakten.model_copy(update={"anfrageart": "rechtsprechungsfrage"}), llm)
    if fakten.anfrageart == "hinweis":
        return _hinweis_antwort(fakten)

    # Pruefkatalog-Befund M1, Punkt 2: laeuft diese Nachricht unter einer bereits bekannten
    # Sitzung (z. B. die Antwort auf eine Rueckfrage), gehen dort schon bekannte Felder nicht
    # verloren, nur weil die neue Extraktion sie nicht erneut liefert.
    if sitzungskennung:
        if bisherige_fakten is not None:
            # Testprotokoll 11.10.2026: der gespeicherte Fallstand ist verbindlich; die
            # Modellantwort wird in Python geprüft und übernommen (app/fallstand.py).
            # Schritt 2 (14.10.2026): Rechnungen, die eins zu eins den Positionen der Nachricht
            # entsprechen, VOR dem Zusammenführen auflösen -- der Fallstand führt eine Rechnung je
            # Auftragnehmer, aus fünf gleichen Rechnungen würde sonst eine.
            fakten = zuordnung.einzelrechnungen_je_position(text_gesamt, fakten)
            fakten = fallstand.uebernehme(bisherige_fakten, fakten, frage)
        # Testfall 20 Positionen: die Antwort auf 'Welche Leistung ...?' ist die Beschreibung
        # der Leistung, auch wenn das Modell sie nicht als leistungsart übernimmt.
        if (pflichtangaben.FRAGE_LEISTUNG in bestaetigung.SPEICHER.hole_offene_fragen(sitzungskennung)
                and not fakten.leistungsart):
            fakten = fakten.model_copy(update={"leistungsart": frage.strip()[:200]})

    # Testfall 20 Positionen: Tätigkeit je Position (Modellwahl + feste Erkennung), erst nach
    # dem Zusammenführen, damit die vollständigen Positionen des Falls zugrunde liegen.
    fakten = zuordnung.musikverein_generalklausel(text_gesamt, fakten)
    fakten = zuordnung.ergaenze_einnahmeabsicht(text_gesamt, fakten)
    fakten = zuordnung.ergaenze_vertretung(text_gesamt, fakten)
    fakten = zuordnung.ergaenze_rolle_darin(text_gesamt, fakten)
    fakten = zuordnung.absichere_rollen(text_gesamt, fakten)
    # F04 live (16.10.2026): ganzer Betrag als Umsatzsteuer, der enthaltene Betrag fehlt.
    fakten = zuordnung.fehlender_enthaltener_teil(text_gesamt, fakten)
    # Korpus mit Small (17.10.2026, F04): vom Modell gerechneter Nettobetrag zusätzlich zum Rest -> nicht doppelt zählen.
    fakten = zuordnung.modellgerechneter_rest(text_gesamt, fakten)
    # Korpus mit Small (17.10.2026, F16): Zahlung 'an die VG Bild-Kunst' ist kein Honorar.
    fakten = zuordnung.vg_als_empfaenger(text_gesamt, fakten)
    fakten = zuordnung.fehlende_nebenkosten_position(text_gesamt, fakten)
    fakten = zuordnung.ergaenze_reisekosten_rolle(text_gesamt, fakten)
    # HT-2026-105: 'fünf Rechnungen … je 250 EUR' -- fehlende gleiche Positionen ergänzen.
    fakten = zuordnung.anzahl_je_betrag(text_gesamt, fakten, frage)
    # AT-2026-027: angezahlt X, Rest Y offen -> Position X + Y teilen (gezahlt zählt, offen nie still).
    fakten = zuordnung.teilzahlung_aus_text(text_gesamt, fakten)
    fakten = zuordnung.doppelte_positionen(text_gesamt, fakten)
    fakten = zuordnung.enthaltene_betraege_nicht_doppelt(text_gesamt, fakten)
    fakten = zuordnung.einzelrechnungen_je_position(text_gesamt, fakten)
    fakten = zuordnung.berechne_restpositionen(fakten, text_gesamt)
    fakten = zuordnung.ergaenze_rechtsform_je_zeile(frage, fakten)
    # Fehlerquellen-Serie HT-2026-069/099: Rechtsform nur für die Position, bei der sie genannt ist.
    fakten = zuordnung.rechtsform_nur_wo_genannt(text_gesamt, fakten)
    # Alltagsfälle 11.10.2026 (F3): bezahlt wird der ausdrücklich genannte Rechnungsteller.
    fakten = zuordnung.rechnungsteller_als_zahlungsempfaenger([*verlauf_fall, frage], fakten)
    fakten = zuordnung.zahlungsweg_im_freitext(text_gesamt, fakten)
    # Härtetest-Serie HT-2026-002 bis 011 (14.10.2026): mehrere Zahlungsjahre, Rechtsformwechsel (Rückfrage).
    fakten = zuordnung.markiere_mehrere_zahlungsjahre(text_gesamt, fakten)
    fakten = zuordnung.markiere_rechtsformwechsel(text_gesamt, fakten)
    fakten = zuordnung.absichere_gesamtbetrag(text_gesamt, fakten)
    # 14.10.2026 (Testfall L-23): Beträge in fremder Währung nie als Euro rechnen. Vor der
    # Tätigkeitszuordnung, damit eine zusammengeführte Position ihre Bezeichnung schon trägt.
    fakten = zuordnung.markiere_fremdwaehrung(text_gesamt, fakten)
    fakten = zuordnung.ergaenze_taetigkeit(text_gesamt, fakten)
    fakten = zuordnung.jahr_aus_rechnungsdaten(text_gesamt, fakten)
    fakten = zuordnung.jahr_aus_freier_jahreszahl(text_gesamt, fakten)
    # Ausdrücklich Unbekanntes und gemeldete Widersprüche aus der NEUEN Nachricht (ohne Modell).
    fakten = fallstand.ergaenze_aus_text(frage, fakten)
    # Umbau Schritt 1 (16.10.2026): Tätigkeit und Zweck mit Herkunft; die alte Kategorie wird nur abgeleitet.
    fakten = einordnung.erfasse(text_gesamt, fakten, bisherige_fakten, modell_verwerterart)
    protokolliere_fakten(frage, "fertig", fakten)

    return _mit_pflichtangaben_weiter(frage, fakten, llm, sitzungskennung,
                                      uebersicht=fallstand.will_uebersicht(frage))


def _extrahiere(llm: LLM, frage: str, verlauf: list[str], fallstand_bisher: Fakten | None) -> Fakten:
    """Mit einem gespeicherten Fallstand bekommt das Modell diesen statt des Chatverlaufs
    (Testprotokoll 11.10.2026). Modelle ohne diese Möglichkeit (Testdoppel) wie bisher."""
    import inspect

    if fallstand_bisher is not None and "fallstand" in inspect.signature(llm.extrahiere_fakten).parameters:
        return llm.extrahiere_fakten(frage, verlauf, fallstand=fallstand_bisher)
    return llm.extrahiere_fakten(frage, verlauf)


# Felder, die nur das System setzt (app/schema.py: 'Wird vom System gesetzt'), und Listen, die kein Knopf ersetzt.
_NUR_SYSTEM_FELDER = {"katalog_taetigkeit", "herkunft", "widersprueche", "unbekannt", "positionen", "rechnungen",
                      "anfrageart", "rest"}


def _aktualisiere_feld(fakten: Fakten, feld: str, wert: Any, position: int | None) -> Fakten:
    """Wendet eine Knopf-Antwort (siehe wende_feldantwort_an) auf `fakten` an und validiert
    das Ergebnis erneut gegen das Schema (app/schema.py) -- `model_copy` allein wuerde einen
    unpassenden Wert ungeprueft durchlassen."""
    daten = fakten.model_dump(mode="python")
    if feld == _WIDERSPRUCH_FELD:
        if wert == "gesamt":
            daten["positionen"] = []
        elif wert == "einzeln":
            daten["gesamtbetrag_genannt"] = None
        else:
            raise ValueError(f"unbekannte Antwort {wert!r}")
        return Fakten.model_validate(daten)
    # Testprotokoll 11.10.2026 (Fallstand): 'Noch unbekannt / später klären' und Werte, die
    # einen Widerspruch oder ein 'unbekannt' auflösen, laufen über app/fallstand.py.
    # Schritt 2 (17.10.2026): Eingaben über die Schnittstelle prüfen, bevor etwas geändert wird -- nur Felder der
    # Fakten bzw. der Position, nie die Felder, die allein das System setzt, und nur eine vorhandene Position.
    if feld in _NUR_SYSTEM_FELDER or (position is None and feld not in Fakten.model_fields):
        raise ValueError(f"Feld {feld!r} ist über einen Knopf nicht änderbar")
    if position is not None and not (0 <= position < len(fakten.positionen) and feld in Position.model_fields):
        raise ValueError(f"Position {position!r} / Feld {feld!r} gibt es nicht")
    key = fallstand.schluessel(feld, position)
    if wert == fallstand.UNBEKANNT_WERT:
        return fallstand.markiere_unbekannt(fakten, key)
    if feld == "auftragszweck" and position is None:
        # Schritt 2: der Nutzer wählt den Zweck (Tatsache); die Einordnung leitet das System ab.
        return einordnung.zweck_knopf(fakten, wert)
    if feld == "verwerterart" and position is None:
        # Alte Schnittstelle (Umbau Schritt 1): der Knopf setzt die getrennten Fakten; widerspricht er dem Text, wird
        # gezielt gefragt.
        return einordnung.knopf(fakten, wert)
    if position is not None:
        daten["positionen"][position][feld] = wert
    else:
        daten[feld] = wert
    Fakten.model_validate(daten)  # Wert prüfen, bevor er übernommen wird
    return fallstand.setze_wert(fakten, key, wert)


def wende_feldantwort_an(
    sitzungskennung: str, feld: str, wert: Any, llm: LLM, position: int | None = None
) -> Antwort:
    """Fuer POST /knopf (app/main.py). Pruefkatalog-Befund M1: wendet eine geschlossene
    Rueckfrage-Antwort (Schaltflaeche) DETERMINISTISCH auf die fuer diese Sitzung
    gespeicherten (noch nicht bestaetigten) Fakten an -- OHNE erneuten Modellaufruf. Ein
    Sprachmodell hat solche Antworten ("Es ist Eigenwerbung.") bisher nicht verlaesslich
    uebernommen, was zu einer endlosen Wiederholung derselben Rueckfrage fuehrte.
    `feld`/`wert`/`position` kommen von app/pflichtangaben.py::rueckfrage_optionen (dort
    erzeugt, hier nur noch angewendet -- nie vom Nutzer frei erfunden, siehe
    app/static/index.html)."""
    fakten = bestaetigung.SPEICHER.hole_fakten(sitzungskennung)
    frage = bestaetigung.SPEICHER.hole_frage(sitzungskennung)
    if fakten is None or frage is None:
        return _rueckfrage_antwort([UNBEKANNTE_SITZUNG_RUECKFRAGE])
    try:
        aktualisiert = _aktualisiere_feld(fakten, feld, wert, position)
    except (ValidationError, IndexError, KeyError, TypeError, ValueError) as fehler:
        protokolliere(frage, fakten.jahr, f"Knopf-Antwort konnte nicht angewendet werden: {fehler}")
        return _rueckfrage_antwort([UNBEKANNTE_SITZUNG_RUECKFRAGE])
    return _mit_pflichtangaben_weiter(frage, aktualisiert, llm, sitzungskennung)


def fuehre_nach_bestaetigung_aus(sitzungskennung: str, llm: LLM) -> Antwort:
    """Fuer POST /bestaetigen (app/main.py): nutzt die in der Sitzung gespeicherten,
    jetzt bestaetigten Fakten."""
    fakten = bestaetigung.SPEICHER.hole_fakten(sitzungskennung)
    frage = bestaetigung.SPEICHER.hole_frage(sitzungskennung)
    if fakten is None or frage is None or not bestaetigung.SPEICHER.ist_bestaetigt(sitzungskennung, fakten):
        return Antwort(
            antwort=f"Keine bestätigten Fakten zu dieser Sitzung – bitte Frage erneut stellen.\n*{SCHLUSSSATZ}*",
            ergebnisklasse=RUECKFRAGE_NOETIG,
            sitzungskennung=sitzungskennung,
        )
    return _nach_bestaetigung(frage, fakten, llm, sitzungskennung)


def _regel_eintrag_fuer(regel_id: str) -> dict[str, Any] | None:
    return quellen.regel_by_id(regel_id)


def _als_regel_eintrag(regel: dict[str, Any]) -> dict[str, Any]:
    gruppe = str(regel.get("gruppe") or "").lower()
    # Alltagsfälle 11.10.2026: Die Ebene stand nur an der Gruppe. Eine KSK-Auslegung mit der
    # Gruppe 'Privat' oder 'Bemessungsgrundlage' (R-40, R-45) erschien deshalb als 'Norm'.
    # Grundregel 10: Auslegung der KSK ist kein Gesetz -- maßgeblich ist der Vorbehalt der Regel.
    vorbehalt = str(regel.get("vorbehalt") or "").lower()
    typ = "urteil" if "rechtsprechung" in gruppe or "bsg" in gruppe else (
        "verwaltungspraxis" if "ksk" in gruppe or "auslegung" in gruppe or "auslegung der ksk" in vorbehalt
        else "gesetz"
    )
    eintrag = {**regel, "typ": typ}
    # Teil 1f, Befund D: eine Archiv-Kopie-Markierung mit festem Datum ist kein fuer die
    # Anfrage gueltiges Jahr (app.quellen.bereinige_fundstelle); hier einmal zentral bereinigt,
    # statt an jeder Stelle, die "fundstelle" liest (app/baustein.py, _ebenen_abschnitt, ...).
    if eintrag.get("fundstelle"):
        eintrag["fundstelle"] = quellen.bereinige_fundstelle(eintrag["fundstelle"])
    return eintrag
