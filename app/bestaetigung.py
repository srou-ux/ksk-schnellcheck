"""Faktenbestaetigung vor der Berechnung (Architektur Teil 1d, Abschnitt B).

Nach Fakten-Extraktion und Pflichtangaben-Pruefung zeigt das SYSTEM (nicht das Sprachmodell)
eine Zusammenfassung der erfassten Fakten. Erst nach ausdruecklicher Bestaetigung wird der
Kern aufgerufen. Die Bestaetigung gilt nur fuer GENAU diese Fakten (Hash); aendert sich ein
Wert -- auch durch eine Korrektur des Nutzers --, ist eine neue Bestaetigung noetig.

Sitzungsstaat liegt bewusst nur im Arbeitsspeicher (nicht in Dateien) -- er ist beim Neustart
der App weg. Reine Rechtsprechungsfragen (anfrageart == "rechtsprechungsfrage") brauchen
keine Bestaetigung, weil dort nichts berechnet wird (siehe app/router.py).
"""
from __future__ import annotations

import hashlib
import json
import threading
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from app.baustein import formatiere_betrag
from app.schema import AUFTRAGSPARTNER_LESBAR, VERWERTERART_LESBAR, Fakten


PAUSCHALE_LESBAR = {"uebungsleiter": "Übungsleiterpauschale", "ehrenamt": "Ehrenamtspauschale"}
# Schritt 2 (17.10.2026): die rechtliche Einordnung ist eine Ableitung des Systems, keine Angabe des Nutzers --
# so gekennzeichnet (vorher 'Art des Auftraggebers: …', das wie eine Angabe des Nutzers aussah).
EINORDNUNG_ZEILE = "Rechtliche Einordnung (Vorschlag des Systems, keine Angabe von Ihnen): "
ANNAHME_UST = ("Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten "
               "(falls doch, bitte die Angaben korrigieren)")


def fakten_hash(fakten: Fakten) -> str:
    """Stabiler Hash ueber die erfassten Fakten. Aendert sich ein Wert, aendert sich der
    Hash -- eine Bestaetigung zu einem anderen Hash ist ungueltig (Architektur Teil 1d,
    Abschnitt B.3)."""
    daten = fakten.model_dump(mode="json")
    kanonisch = json.dumps(daten, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(kanonisch.encode("utf-8")).hexdigest()


def _rolle_lesbar(rolle: str) -> str:
    """Livetest-Befund L5: interne Rollen-Codes (z. B. 'fahrtkosten_nachgewiesen') sind in
    der Faktenbestaetigung fuer den Nutzer nicht verstaendlich -- feste, lesbare Bezeichnung
    statt des rohen Codes. Nutzt dieselbe Zuordnung wie kern.rechnen._AUSSCHLUSSGRUENDE (dort
    schon fuer die Begruendung verwendet), damit es nur eine Quelle fuer diese Texte gibt."""
    from kern import rechnen as K

    if rolle in K._AUSSCHLUSSGRUENDE:
        return K._AUSSCHLUSSGRUENDE[rolle][0]
    if rolle == "honorar":
        return "Honorar"
    return rolle.replace("_", " ")


def _taetigkeit_lesbar(tid: Optional[str]) -> Optional[str]:
    from app import taetigkeiten

    return taetigkeiten.lesbar(tid)


def als_liste(fakten: Fakten) -> list[str]:
    """Die Fakten als kurze, vom System formulierte Liste (fuer Weboberflaeche/API) --
    niemals vom Sprachmodell formuliert.

    Livetest-Befund L5: 'Anfrageart' ist ein interner Routing-Begriff (z. B. 'bewertung') --
    fuer die Bestaetigung der FAKTEN selbst nicht hilfreich, deshalb weggelassen (anders als
    AUFTRAGSPARTNER_LESBAR/VERWERTERART_LESBAR gibt es dafuer keine kurze, fuer alle elf Werte
    sinnvolle Nutzer-Bezeichnung)."""
    zeilen: list[str] = []
    if fakten.jahr is not None:
        zusatz = (" (aus den Daten auf der Rechnung abgeleitet – bitte prüfen, in welchem Jahr gezahlt wurde)"
                  if fakten.jahr_aus_rechnungsdaten else "")
        zeilen.append(f"Jahr: {fakten.jahr}{zusatz}")
    if fakten.leistungsart:
        zeilen.append(f"Leistung: {fakten.leistungsart}")
    # Umbau Schritt 1 (16.10.2026): erst die Fakten (Tätigkeit, Zweck, mit Herkunft), dann die daraus abgeleitete Art.
    from app import einordnung

    zeilen.extend(einordnung.zeilen_fuer_bestaetigung(fakten))
    if fakten.verwerterart:
        zeilen.append(f"{EINORDNUNG_ZEILE}{VERWERTERART_LESBAR.get(fakten.verwerterart, fakten.verwerterart)}")
    if fakten.auftragnehmer_typ:
        zeilen.append(f"Auftragnehmer: {AUFTRAGSPARTNER_LESBAR.get(fakten.auftragnehmer_typ, fakten.auftragnehmer_typ)}")
    if fakten.auftraggeber_typ:
        zeilen.append(f"Auftraggeber: {AUFTRAGSPARTNER_LESBAR.get(fakten.auftraggeber_typ, fakten.auftraggeber_typ)}")
    if fakten.rechnungsteller_typ:
        zeilen.append("Rechnungsteller (an ihn wird gezahlt): "
                      f"{AUFTRAGSPARTNER_LESBAR.get(fakten.rechnungsteller_typ, fakten.rechnungsteller_typ)}")
    for i, p in enumerate(fakten.positionen, start=1):
        # Testprotokoll 11.10.2026: angezeigt wird die Bezeichnung der Position (z. B.
        # „Druckkosten“), die Rolle nur, wenn sie etwas bewirkt (Sonderrolle des Kerns).
        from kern import rechnen as K

        bezeichnung = f" „{p.bezeichnung}“" if p.bezeichnung else ""
        rolle = f" ({_rolle_lesbar(p.rolle)})" if p.rolle in K._AUSSCHLUSSGRUENDE or (p.rolle and not p.bezeichnung) else ""
        if p.fremdwaehrung:
            betrag_text = f"{p.fremd_betrag or p.fremdwaehrung} (Euro-Betrag offen, wird nicht umgerechnet)"
        elif p.fremd_betrag:
            betrag_text = f"{formatiere_betrag(p.betrag)} (gezahlter Euro-Betrag; angegeben {p.fremd_betrag})"
        else:
            betrag_text = formatiere_betrag(p.betrag)
        zeile = f"Position {i}: {betrag_text}{bezeichnung}{rolle}"
        # Teil 1f, Abschnitt A3: Rechtsform je Position in der Bestaetigung anzeigen (eigene
        # Angabe oder der globale Vorgabewert), damit der Nutzer sieht, wonach gerechnet wird.
        effektiver_typ = p.auftragnehmer_typ or fakten.auftragnehmer_typ
        if effektiver_typ:
            zeile += f", {AUFTRAGSPARTNER_LESBAR.get(effektiver_typ, effektiver_typ)}"
        # Testfall 20 Positionen: die Einordnung der Leistung gehört zu den bestätigten Fakten.
        taetigkeit = _taetigkeit_lesbar(p.taetigkeit_id or fakten.taetigkeit_id)
        if taetigkeit:
            zeile += f", Leistung: {taetigkeit}"
        if p.zahlungsweg_unklar:
            # Härtetest-Serie HT-2026-002 bis 011: der Grund aus dem Text (app/zahlungsweg_begriffe.json), sonst allgemein.
            zeile += f", offen: {p.offen_grund}" if p.offen_grund else ", Provision/Zahlungsweg offen (Vertrag prüfen)"
        if p.vertrag_direkt:
            zeile += ", Vertrag direkt zwischen Mandant und Künstler (Durchleitung)"
        if p.auftragnehmer_nr is not None and not fakten.ein_auftragnehmer:
            zeile += f", Auftragnehmer {p.auftragnehmer_nr}"
        zeilen.append(zeile)
    if not fakten.positionen and fakten.gesamtbetrag_genannt is not None:
        # Dialogtest Fallgrenzen: nur ein Gesamtbetrag bekannt -- als solcher anzeigen, nicht
        # als 'Position 1', damit keine Rechnung bestätigt wird, die nie genannt wurde.
        zeile = f"Gesamtbetrag (Aufteilung auf Rechnungen unbekannt): {formatiere_betrag(fakten.gesamtbetrag_genannt)}"
        if fakten.auftragnehmer_typ:
            zeile += f", {AUFTRAGSPARTNER_LESBAR.get(fakten.auftragnehmer_typ, fakten.auftragnehmer_typ)}"
        taetigkeit = _taetigkeit_lesbar(fakten.taetigkeit_id)
        if taetigkeit:
            zeile += f", Leistung: {taetigkeit}"
        zeilen.append(zeile)
    for r in fakten.rechnungen:
        zeilen.append(f"Rechnung von Auftragnehmer {r.auftragnehmer_nr}: {formatiere_betrag(r.gesamtbetrag)} gesamt "
                      "(Rest vom System berechnet)")
    # Diskussion mit dem Nutzer (16.10.2026, Punkt 3): die stillschweigende Annahme zur Umsatzsteuer sichtbar machen.
    # Keine Rechtsaussage, nur die Annahme über die Fakten (gerechnet wird im Kern mit dem Betrag, wie er dasteht).
    if any(p.betrag is not None and p.rolle != "ust" for p in fakten.positionen) and not any(
            p.rolle == "ust" for p in fakten.positionen):
        zeilen.append(ANNAHME_UST)
    if fakten.ein_auftragnehmer is not None and len(fakten.positionen) > 1:
        zeilen.append("Alle Positionen vom selben Auftragnehmer: " + ("ja" if fakten.ein_auftragnehmer else "nein"))
    if fakten.veranstaltungszahl is not None:
        zeilen.append(f"Veranstaltungen: {fakten.veranstaltungszahl}")
    elif fakten.veranstaltungszahl_unbekannt:
        zeilen.append("Veranstaltungen: Anzahl unbekannt")
    # Testprotokoll 11.10.2026 (Fallstand): ausdrücklich Unbekanntes und Widersprüche sichtbar.
    from app import fallstand

    for zeile in fallstand.offene_zeilen(fakten):
        if zeile.endswith("ausdrücklich unbekannt") and not zeile.startswith(fallstand.FELD_LESBAR["veranstaltungszahl"]):
            zeilen.append(f"Ausdrücklich unbekannt: {zeile.rsplit(':', 1)[0]}")
        elif "widersprüchlich" in zeile:
            zeilen.append(f"Widersprüchlich: {zeile}")
    # Live-Lauf 14.10.2026 (P-20b): die Angaben zur Pauschale ändern die Zahl -- sichtbar machen.
    if fakten.pauschale_art is not None:
        zeile = f"Pauschale: {PAUSCHALE_LESBAR.get(fakten.pauschale_art, fakten.pauschale_art)}"
        if fakten.pauschale_bestaetigung is not None:
            zeile += ", schriftlich bestätigt: " + ("ja" if fakten.pauschale_bestaetigung else "nein")
        if fakten.pauschale_bereits_ausgeschoepft is not None:
            zeile += f", davon schon verbraucht: {formatiere_betrag(fakten.pauschale_bereits_ausgeschoepft)}"
        zeilen.append(zeile)
    # 14.10.2026: Grundsatzfragen ohne Betrag sichtbar machen (P-36, P-37).
    if fakten.vertretung_kuenstler:
        zeilen.append("Handelt im Namen und für Rechnung des Künstlers (Vertretung): ja")
    if fakten.empfaenger_abgabepflichtig is not None:
        zeilen.append("Vertragspartner selbst abgabepflichtig: " + ("ja" if fakten.empfaenger_abgabepflichtig else "nein"))
    if fakten.nachweismakler:
        zeilen.append("Nur Benennung der Vertragsparteien (kein Vertragsschluss, keine Organisation, kein Honorar, keine Haftung)")
    if fakten.einnahmeabsicht is not None:
        zeilen.append(f"Einnahmeabsicht: {'ja' if fakten.einnahmeabsicht else 'nein'}")
    if fakten.belege_vorhanden is not None:
        zeilen.append(f"Belege vorhanden: {'ja' if fakten.belege_vorhanden else 'nein'}")

    # Teil 1f, Abschnitt I.2: deutliche Warnung, wenn die Summe der Positionen nicht zu
    # einem vom Nutzer genannten Gesamtbetrag passt (Befund M2 -- "davon" doppelt gezaehlt).
    from app.plausibilitaet import gesamtbetrag_warnung

    warnung = gesamtbetrag_warnung(fakten)
    if warnung:
        zeilen.append(warnung)

    return zeilen


def saetze(fakten: Fakten, liste: Optional[list[str]] = None) -> str:
    """Schritt 2 (17.10.2026): kurze Zusammenfassung in Sätzen, vom SYSTEM formuliert (nie vom Sprachmodell). Sie
    wiederholt die Liste nicht, sondern sagt, worum es geht, was abgeleitet und was angenommen ist und dass erst nach
    der Bestätigung gerechnet wird. Keine Summe (gerechnet wird nur im Kern)."""
    liste = als_liste(fakten) if liste is None else liste
    teile = ["Bitte prüfen Sie, ob ich Ihre Angaben richtig verstanden habe."]
    anzahl = len(fakten.positionen)
    menge = (f"{anzahl} Position" + ("en" if anzahl != 1 else "")) if anzahl else (
        "einen Gesamtbetrag" if fakten.gesamtbetrag_genannt is not None else "")
    if fakten.jahr is not None:
        satz = f"Es geht um {menge} im Kalenderjahr {fakten.jahr}" if menge else f"Es geht um das Kalenderjahr {fakten.jahr}"
        if fakten.jahr_aus_rechnungsdaten:
            satz += " – das Jahr habe ich aus den Daten auf der Rechnung abgeleitet; maßgeblich ist das Jahr der Zahlung"
        teile.append(satz + ".")
    if fakten.verwerterart:
        teile.append(f"Aus Ihren Angaben leitet das System die Einordnung „{VERWERTERART_LESBAR.get(fakten.verwerterart)}“ "
                     "ab. Das ist ein Vorschlag des Systems, keine Angabe von Ihnen.")
    if ANNAHME_UST in liste:
        teile.append("Wichtig: Ich gehe davon aus, dass in den Beträgen keine gesondert ausgewiesene Umsatzsteuer "
                     "steckt.")
    if any(z.startswith(("Ausdrücklich unbekannt", "Widersprüchlich")) for z in liste):
        teile.append("Einige Angaben sind noch offen oder widersprüchlich; sie stehen in der Liste.")
    teile.append("Gerechnet wird erst, wenn Sie „Ja, das stimmt“ wählen. Sonst korrigieren Sie bitte die Angaben.")
    return " ".join(teile)


def zusammenfassung(fakten: Fakten) -> str:
    """Zusammenfassung (vom System formuliert): erst die Sätze, dann EINMAL die vollständige Liste, dann die Frage.
    Die Weboberfläche zeigt die Sätze und die Liste getrennt (die Liste nicht doppelt)."""
    liste = als_liste(fakten)
    return saetze(fakten, liste) + "\n\nErfasste Angaben: " + "; ".join(liste) + ". Stimmt das?"


@dataclass
class _Sitzung:
    frage: Optional[str] = None
    fakten: Optional[Fakten] = None
    bestaetigter_hash: Optional[str] = None
    # Dialogtest Fallgrenzen: ab welchem Eintrag des (von der Oberfläche mitgeschickten)
    # Verlaufs dieser Fall beginnt. Ältere Einträge gehören zu einem früheren Fall und gehen
    # weder an das Sprachmodell noch in die deterministischen Textprüfungen.
    verlauf_start: int = 0
    # Livetest 10.10.2026: die zuletzt gestellten Rückfragen, damit eine reine Zahl als
    # Antwort ('2000', '2') der offenen Frage fest zugeordnet werden kann (app/router.py).
    offene_fragen: list[str] = field(default_factory=list)


class Sitzungsspeicher:
    """Rein im Arbeitsspeicher. Fuer mehrere uvicorn-Worker/-Prozesse waere eine externe
    Ablage (Redis o. ae.) noetig -- fuer diesen Prototyp genuegt ein Lock in einem Prozess
    (siehe app/README.md, Grenzen)."""

    def __init__(self) -> None:
        self._sitzungen: dict[str, _Sitzung] = {}
        self._lock = threading.Lock()

    def neue_sitzungskennung(self) -> str:
        return uuid.uuid4().hex

    def neue_sitzung(self, verlauf_start: int = 0) -> str:
        """Legt eine Sitzung (= einen Fall) an und merkt sich, ab welchem Verlaufseintrag er
        beginnt (siehe _Sitzung.verlauf_start)."""
        kennung = self.neue_sitzungskennung()
        with self._lock:
            self._sitzungen[kennung] = _Sitzung(verlauf_start=max(0, int(verlauf_start)))
        return kennung

    def setze_offene_fragen(self, sitzungskennung: str, fragen: list[str]) -> None:
        with self._lock:
            sitzung = self._sitzungen.setdefault(sitzungskennung, _Sitzung())
            sitzung.offene_fragen = list(fragen)

    def hole_offene_fragen(self, sitzungskennung: str) -> list[str]:
        with self._lock:
            sitzung = self._sitzungen.get(sitzungskennung)
            return list(sitzung.offene_fragen) if sitzung else []

    def hole_verlauf_start(self, sitzungskennung: str) -> Optional[int]:
        with self._lock:
            sitzung = self._sitzungen.get(sitzungskennung)
            return sitzung.verlauf_start if sitzung else None

    def setze_fakten(self, sitzungskennung: str, frage: str, fakten: Fakten) -> None:
        with self._lock:
            sitzung = self._sitzungen.setdefault(sitzungskennung, _Sitzung())
            sitzung.frage = frage
            sitzung.fakten = fakten

    def hole_fakten(self, sitzungskennung: str) -> Optional[Fakten]:
        with self._lock:
            sitzung = self._sitzungen.get(sitzungskennung)
            return sitzung.fakten if sitzung else None

    def hole_frage(self, sitzungskennung: str) -> Optional[str]:
        with self._lock:
            sitzung = self._sitzungen.get(sitzungskennung)
            return sitzung.frage if sitzung else None

    def bestaetige(self, sitzungskennung: str, hash_wert: str) -> bool:
        """Bestaetigt GENAU den uebergebenen Hash. False, wenn die Sitzung unbekannt ist
        oder der Hash nicht zu den zuletzt gezeigten Fakten passt."""
        with self._lock:
            sitzung = self._sitzungen.get(sitzungskennung)
            if sitzung is None or sitzung.fakten is None:
                return False
            if fakten_hash(sitzung.fakten) != hash_wert:
                return False
            sitzung.bestaetigter_hash = hash_wert
            return True

    def ist_bestaetigt(self, sitzungskennung: str, fakten: Fakten) -> bool:
        with self._lock:
            sitzung = self._sitzungen.get(sitzungskennung)
            if sitzung is None or sitzung.bestaetigter_hash is None:
                return False
            return sitzung.bestaetigter_hash == fakten_hash(fakten)


SPEICHER = Sitzungsspeicher()
