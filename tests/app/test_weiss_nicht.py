"""Livetest 11.10.2026: Bei der Frage nach der Zahl der Veranstaltungen soll 'Weiß ich nicht'
möglich sein. Dann rechnet der Kern beide Fälle; unterscheiden sie sich, ist es ein Grenzfall
mit Erklärung (TB-17), Empfehlung (TB-18) und Fundstellen (R-15, R-16, R-21, R-83, R-212)."""
from __future__ import annotations

import unittest
from decimal import Decimal

from app import bestaetigung, pflichtangaben, router
from app.llm.fake import FakeLLM
from app.schema import Fakten
from tests.app.zweck_knopf import mit_zweck  # Entscheidung 17.10.2026: geratener Zweck wird per Knopf bestätigt


def _fall(typ="natuerliche_person", betrag="2000", einnahme=True):
    llm = FakeLLM()
    llm.registriere("F", Fakten(anfrageart="bewertung", jahr=2026, verwerterart="generalklausel",
                                einnahmeabsicht=einnahme, auftragnehmer_typ=typ, leistungsart="Musik",
                                gesamtbetrag_genannt=Decimal(betrag)))
    return llm, mit_zweck(router.bearbeite_frage("F", llm), "generalklausel", llm)


def _ergebnis(llm, antwort):
    bestaetigung.SPEICHER.bestaetige(antwort.sitzungskennung, antwort.fakten_hash)
    return router.fuehre_nach_bestaetigung_aus(antwort.sitzungskennung, llm)


class TestWeissNicht(unittest.TestCase):
    def test_knopf_wird_angeboten_und_zahl_bleibt_eingabe(self):
        _, a = _fall()
        self.assertEqual(a.rueckfragen, [pflichtangaben.FRAGE_VERANSTALTUNGSZAHL])
        self.assertEqual(a.rueckfrage_optionen[0]["optionen"], [pflichtangaben.WEISS_NICHT])

    def test_getippt_und_per_knopf_gleich(self):
        for weg in ("text", "knopf"):
            llm, a = _fall()
            if weg == "text":
                b = router.bearbeite_frage("weiß ich nicht", llm, ["F"], a.sitzungskennung)
            else:
                o = a.rueckfrage_optionen[0]
                b = router.wende_feldantwort_an(a.sitzungskennung, o["feld"], o["werte"][pflichtangaben.WEISS_NICHT], llm)
            self.assertIn("Veranstaltungen: Anzahl unbekannt", b.fakten_zusammenfassung, weg)

    def test_unterschiedliche_ausgaenge_ergeben_grenzfall_mit_erklaerung(self):
        llm, a = _fall()
        b = router.bearbeite_frage("keine Ahnung", llm, ["F"], a.sitzungskennung)
        r = _ergebnis(llm, b)
        self.assertEqual(r.ergebnisklasse, "Grenzfall → Steuerberater entscheidet")
        for teil in ("nicht mehr als 3", "98,00 €", "vorsorglich", "KSVG § 28", "geschätzt"):
            self.assertIn(teil, r.antwort)

    def test_gleiche_ausgaenge_ergeben_ergebnis_ohne_falsche_begruendung(self):
        llm, a = _fall(typ="GmbH_UG_AG")
        b = router.bearbeite_frage("weiß ich nicht", llm, ["F"], a.sitzungskennung)
        r = _ergebnis(llm, b)
        self.assertEqual(r.ergebnisklasse, "Nicht abgabepflichtig (Vorschlag)")
        self.assertNotIn("Mehr als drei", r.antwort)
        self.assertNotIn("Höchstens drei", r.antwort)
        self.assertIn("nicht zur Bemessungsgrundlage", r.antwort)

    def test_lange_nachricht_mit_weiss_nicht_geht_ans_modell(self):
        self.assertIsNone(router._unbekannt_als_antwort(
            "Ich weiß nicht genau, aber es waren wohl fünf Konzerte und ein Sommerfest im Park",
            [pflichtangaben.FRAGE_VERANSTALTUNGSZAHL]))
        self.assertIsNone(router._unbekannt_als_antwort("weiß ich nicht", [pflichtangaben.FRAGE_BETRAG]))


if __name__ == "__main__":
    unittest.main()
