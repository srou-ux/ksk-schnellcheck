"""Regressionstests zum Härtetest RE-2026-777 (ksk-haertetest-RE-2026-777.pdf, 11.10.2026). Erfundene Daten.

Die Soll-Bewertung der Testdatei ist laut Datei ein ungeprüfter Entwurf; mehrere Punkte widersprechen
den Quellen (aufgaben/audit/haertetest777_auswertung.md). Geprüft wird deshalb nur, was die Quellen
tragen:
- Positionen 'im eigenen Namen der GmbH eingekauft' gehen an die Rechnungstellerin (R-45, R-216).
- Positionen mit Vertretung, Durchleitung oder Direktzahlung entscheidet der Steuerberater
  (KSK-Info 27, R-33, R-36, R-94) -- nie still ausgeschlossen, nie still mitgezählt.
- Ohne 'darin/davon' gibt es keinen 'Rest der Rechnung'.
OFFLINE: die Modellantwort ist der echten Antwort von mistral-large-latest nachgebildet."""
from __future__ import annotations

import json
import unittest
from decimal import Decimal as D
from pathlib import Path

from app import bestaetigung, router, zuordnung
from app.ergebnisklassen import FAKTEN_BESTAETIGUNG_NOETIG
from app.schema import Fakten, Position as P, Rechnung

FRAGE = json.loads((Path(__file__).resolve().parents[2] / "aufgaben" / "audit" / "testfall_haertetest_777.json")
                   .read_text(encoding="utf-8"))["faelle"][0]["frage"]
NP, G = "natuerliche_person", "GmbH_UG_AG"


def _modellantwort():
    return Fakten(
        anfrageart="bewertung", jahr=2026, verwerterart="typischer_verwerter", auftraggeber_typ=G,
        positionen=[
            P(betrag=D("4800"), auftragnehmer_typ=NP, auftragnehmer_nr=2, taetigkeit_id="T-02", bezeichnung="Bühnenbild-Entwurf"),
            P(betrag=D("3200"), auftragnehmer_typ=NP, auftragnehmer_nr=3, taetigkeit_id="T-07", bezeichnung="Abschlusskonzert"),
            P(betrag=D("1100"), auftragnehmer_typ=NP, auftragnehmer_nr=4, taetigkeit_id="T-34", rest=True, bezeichnung="Lichtdesign-Workshop"),
            P(betrag=D("480"), auftragnehmer_typ=G, auftragnehmer_nr=1, bezeichnung="Vermittlungsprovision"),
            P(betrag=D("2720"), auftragnehmer_typ=NP, auftragnehmer_nr=5, taetigkeit_id="T-07", bezeichnung="Direktzahlung Komponist"),
            P(betrag=D("336"), auftragnehmer_typ=NP, auftragnehmer_nr=2, rolle="fahrtkosten_nachgewiesen", bezeichnung="Reisekosten, pauschal"),
            P(betrag=D("2900"), auftragnehmer_typ=G, auftragnehmer_nr=1, bezeichnung="Agentur-Pauschale"),
            P(betrag=D("1400"), auftragnehmer_typ="Ausland", auftragnehmer_nr=6, taetigkeit_id="T-65", bezeichnung="Tontechnik-Vermietung"),
            P(betrag=D("-950"), taetigkeit_id="T-02", bezeichnung="Storno/Gutschrift"),
            P(betrag=D("2257.17"), rolle="ust", auftragnehmer_typ=G, auftragnehmer_nr=1, bezeichnung="USt 19 %"),
        ],
        rechnungen=[Rechnung(auftragnehmer_nr=1, gesamtbetrag=D("15523.17"))])


class Modell:
    def extrahiere_fakten(self, frage, verlauf=None, fallstand=None):
        return _modellantwort()

    def beschreibe_fall(self, kontext):  # pragma: no cover
        return ""


class TestHaertetest777(unittest.TestCase):
    def setUp(self):
        self.llm = Modell()
        self.erste = router.bearbeite_frage(FRAGE, self.llm, [])
        self.stand = bestaetigung.SPEICHER.hole_fakten(self.erste.sitzungskennung)

    def test_keine_rueckfrage_und_kein_erfundener_rest(self):
        self.assertEqual(self.erste.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG, self.erste.rueckfragen)
        self.assertFalse(any(p.rest for p in self.stand.positionen))
        self.assertNotIn("Rest der Rechnung", [p.bezeichnung for p in self.stand.positionen])

    def test_eigener_name_geht_an_die_gmbh(self):
        typ = {p.bezeichnung: p.auftragnehmer_typ for p in self.stand.positionen}
        for bez in ("Bühnenbild-Entwurf", "Reisekosten, pauschal", "Agentur-Pauschale", "Tontechnik-Vermietung", "Storno/Gutschrift"):
            self.assertEqual(typ[bez], G, bez)

    def test_vertretung_durchleitung_direktzahlung_sind_markiert(self):
        # ALLTAG-2026-999: Durchleitung und Direktzahlung zählen beim Mandanten (KSK-Info 27, R-127);
        # offen bleiben nur Provision und vertragswidriger Zahlungsweg (R-38/R-39).
        unklar = {p.bezeichnung for p in self.stand.positionen if p.zahlungsweg_unklar}
        direkt = {p.bezeichnung for p in self.stand.positionen if p.vertrag_direkt}
        self.assertEqual(unklar, {"Abschlusskonzert", "Vermittlungsprovision"})
        self.assertEqual(direkt, {"Lichtdesign-Workshop", "Direktzahlung Komponist"})

    def test_ergebnis_grenzfall_mit_beiden_betraegen(self):
        bestaetigung.SPEICHER.bestaetige(self.erste.sitzungskennung, self.erste.fakten_hash)
        e = router.fuehre_nach_bestaetigung_aus(self.erste.sitzungskennung, self.llm)
        self.assertEqual(e.ergebnisklasse, "Grenzfall → Steuerberater entscheidet")
        # sicher: 2.720 € Direktzahlung (Workshop nach T-34 nicht künstlerisch); offen: 3.200 € Pianist
        self.assertEqual(e.kern_protokoll["abgabe_ohne_unsichere"], D("133.28"))
        self.assertEqual(e.kern_protokoll["abgabe_falls_kuenstlerisch"], D("290.08"))
        self.assertIn("entscheidet der Steuerberater anhand der Verträge", e.antwort)


class TestAbschnitte(unittest.TestCase):
    def test_summenzeile_gehoert_zu_keiner_position(self):
        text = ("Rechnungsteller: Beispiel GmbH\nPos. 01 Logo im eigenen Namen eingekauft: 900,00 €\n"
                "Nettosumme 900,00 € (Pos. 02 reine Durchleitung)")
        f = zuordnung.rechnungsteller_als_zahlungsempfaenger([text], Fakten(positionen=[P(betrag=D("900"))]))
        self.assertEqual(f.positionen[0].auftragnehmer_typ, G)
        self.assertIsNone(f.positionen[0].zahlungsweg_unklar)

    def test_fortsetzungszeile_gehoert_zur_position(self):
        text = ("Rechnungsteller: Beispiel GmbH\n01 | Konzert | 3.200,00 €\n"
                "   im Namen und für Rechnung des Kunden\n02 | Konzept | 500,00 €")
        f = zuordnung.rechnungsteller_als_zahlungsempfaenger(
            [text], Fakten(positionen=[P(betrag=D("3200"), auftragnehmer_typ=NP), P(betrag=D("500"))]))
        self.assertEqual([p.vertrag_direkt for p in f.positionen], [True, None])
        self.assertEqual([p.auftragnehmer_typ for p in f.positionen], [NP, G])


class TestRestNurMitEinschluss(unittest.TestCase):
    def test_kein_rest_ohne_darin(self):
        f = Fakten(positionen=[P(betrag=D("800"), auftragnehmer_nr=1)], rechnungen=[Rechnung(auftragnehmer_nr=1, gesamtbetrag=D("1000"))])
        self.assertEqual(len(zuordnung.berechne_restpositionen(f, "Rechnung 1.000 €, Pos. 800 €").positionen), 1)

    def test_rest_mit_darin_wie_bisher(self):
        f = Fakten(positionen=[P(betrag=D("300"), auftragnehmer_nr=1)], rechnungen=[Rechnung(auftragnehmer_nr=1, gesamtbetrag=D("1200"))])
        f = zuordnung.berechne_restpositionen(f, "1.200 Euro netto in Rechnung. Darin sind 300 Euro Druckkosten enthalten.")
        self.assertEqual([p.betrag for p in f.positionen], [D("300"), D("900")])


if __name__ == "__main__":
    unittest.main()


class TestEinnahmeabsichtNurBeiGeneralklausel(unittest.TestCase):
    def test_typischer_verwerter_mit_veranstaltungen_ohne_einnahmefrage(self):
        from app import pflichtangaben

        f = Fakten(jahr=2026, verwerterart="typischer_verwerter", veranstaltungszahl=2,
                   positionen=[P(betrag=D("1000"), auftragnehmer_typ=NP, taetigkeit_id="T-07")])
        self.assertNotIn(pflichtangaben.FRAGE_EINNAHMEABSICHT, pflichtangaben.fehlende_pflichtangaben(f, alle=True))

    def test_generalklausel_fragt_weiter(self):
        from app import pflichtangaben

        # 14.10.2026: bei höchstens drei Veranstaltungen fragt das System nicht mehr nach der Einnahmeabsicht
        # (KSVG § 24 Abs. 2 S. 3 Nr. 1: dann keine Abgabepflicht nach S. 1 Nr. 2, unabhängig davon); der
        # Zweck des Tests (bei der Generalklausel wird gefragt) gilt jetzt für mehr als drei Veranstaltungen.
        f = Fakten(jahr=2026, verwerterart="generalklausel", veranstaltungszahl=4,
                   positionen=[P(betrag=D("1000"), auftragnehmer_typ=NP, taetigkeit_id="T-07")])
        self.assertIn(pflichtangaben.FRAGE_EINNAHMEABSICHT, pflichtangaben.fehlende_pflichtangaben(f, alle=True))
        f2 = f.model_copy(update={"veranstaltungszahl": 2})
        self.assertNotIn(pflichtangaben.FRAGE_EINNAHMEABSICHT, pflichtangaben.fehlende_pflichtangaben(f2, alle=True))
