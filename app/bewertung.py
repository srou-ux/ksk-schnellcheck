"""Bewertung eines bestätigten Falls: Regelkern aufrufen und unabhängig gegenrechnen. Ohne Sprachmodell.

Herkunft (17.10.2026, Umbau „ohne KI“): Die Funktionen stammen unverändert aus dem früheren Chat-Router
(app/router.py). Der Chat brauchte ein Sprachmodell und ist entfernt; „Rechnungen prüfen“ und der Schnellcheck nutzen
genau diese Kernaufrufe weiter (app/dokument_pruefung.py). Gerechnet wird nur in kern/rechnen.py, gegengerechnet im
verifier/. Entwurf – vom Steuerberater zu prüfen.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from app import einordnung, gegenrechnung, pflichtangaben, taetigkeiten
from app.gegenrechnung import KERN as K
from app.ergebnisklassen import AUSKUNFT_ERTEILT, GRENZFALL, NICHT_ABGEDECKT, RUECKFRAGE_NOETIG
from app.schema import VERWERTERART_LESBAR, Fakten, Position


@dataclass
class KernErgebnis:
    klasse: str
    protokoll: dict[str, Any] = field(default_factory=dict)
    grund: str | None = None
    stichworte: list[str] = field(default_factory=list)
    rueckfragen: list[str] = field(default_factory=list)
    regel_ids: list[str] = field(default_factory=list)
    fundstellen_kern: list[str] = field(default_factory=list)


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

