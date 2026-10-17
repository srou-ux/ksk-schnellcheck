"""Tests fuer app/router.py gegen den echten Kern. Seit Chatbot Teil 1d braucht jede
Anfrage, die den Kern aufruft, zuerst eine Faktenbestaetigung (hilfen.lauf_bestaetigt
simuliert POST /frage + POST /bestaetigen); nur Rueckfragen wegen fehlendem Jahr und
Rechtsprechungsfragen kommen ohne Bestaetigung sofort final zurueck."""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from tests.app.hilfen import lauf_bestaetigt

from app import router
from app.ergebnisklassen import (
    ABGABEPFLICHTIG,
    FAKTEN_BESTAETIGUNG_NOETIG,
    NICHT_ABGEDECKT,
    RUECKFRAGE_NOETIG,
)
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position


class TestFaktenbestaetigungWirdVerlangt(unittest.TestCase):
    def test_bewertung_ohne_bestaetigung_liefert_zusammenfassung_statt_ergebnis(self):
        llm = FakeLLM()
        frage = "2024 Eigenwerbung Grafiker 1750 Euro."
        llm.registriere(
            frage,
            Fakten(jahr=2024, verwerterart="eigenwerber", auftragnehmer_typ="natuerliche_person",
                   leistungsart="Grafik/Design", positionen=[Position(betrag=Decimal("1750"))]),
        )
        erste = router.bearbeite_frage(frage, llm)
        self.assertEqual(erste.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG)
        self.assertTrue(erste.sitzungskennung)
        self.assertTrue(erste.fakten_hash)
        self.assertTrue(erste.fakten_zusammenfassung)


class TestEigenwerbung(unittest.TestCase):
    def test_fehlendes_jahr_fuehrt_zu_rueckfrage(self):
        llm = FakeLLM()
        llm.registriere("Frage ohne Jahr", Fakten())
        ergebnis = router.bearbeite_frage("Frage ohne Jahr", llm)
        self.assertEqual(ergebnis.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertTrue(ergebnis.rueckfragen)

    def test_eigenwerbung_2024_abgabepflichtig(self):
        # Entspricht Dialog 2 (regelwerk/Chatbot_Musterdialoge_Entwurf.md).
        llm = FakeLLM()
        frage = "Kanzlei, 2024 Website fuer 1750 Euro an einen freien Webdesigner."
        fakten = Fakten(
            jahr=2024, verwerterart="eigenwerber", auftragnehmer_typ="natuerliche_person",
            leistungsart="Grafik/Design", positionen=[Position(betrag=Decimal("1750"))],
        )
        ergebnis = lauf_bestaetigt(llm, frage, fakten)
        self.assertEqual(ergebnis.ergebnisklasse, ABGABEPFLICHTIG)
        self.assertEqual(ergebnis.kern_protokoll.get("abgabe"), Decimal("87.50"))
        self.assertTrue(ergebnis.fundstellen)

    def test_jahr_2017_ohne_schwellen_daten_ist_nicht_abgedeckt(self):
        """Dokumentiert denselben Fall, den PROMPT_ClaudeCode_Chatbot_1.md selbst als
        Beispiel nennt: Dialog 1/E-01 verlangt 2017, der Kern kennt Schwellen erst ab 2019.
        Weiter als Befund gemeldet (aufgaben/FUNDE_Chatbot.md, Befund 3), nicht angepasst."""
        llm = FakeLLM()
        frage = "Kanzlei, 2017 einmalig Website, 1750 Euro netto an einen freien Webdesigner."
        fakten = Fakten(
            jahr=2017, verwerterart="eigenwerber", auftragnehmer_typ="natuerliche_person",
            leistungsart="Grafik/Design", positionen=[Position(betrag=Decimal("1750"))],
        )
        ergebnis = lauf_bestaetigt(llm, frage, fakten)
        self.assertEqual(ergebnis.ergebnisklasse, NICHT_ABGEDECKT)


class TestVeranstaltungen(unittest.TestCase):
    def test_veranstaltung_ohne_einnahmeabsicht_fuehrt_zu_rueckfrage(self):
        llm = FakeLLM()
        frage = "2025, vier Konzerte, Summe 2000 Euro, Einnahmeabsicht unklar."
        fakten = Fakten(
            jahr=2025, verwerterart="generalklausel", auftragnehmer_typ="natuerliche_person", leistungsart="Musik",
            positionen=[Position(betrag=Decimal("2000"))], veranstaltungszahl=4,
        )
        ergebnis = lauf_bestaetigt(llm, frage, fakten)
        self.assertEqual(ergebnis.ergebnisklasse, RUECKFRAGE_NOETIG)

    def test_bis_drei_veranstaltungen_generalklausel_nicht_abgabepflichtig(self):
        from app.ergebnisklassen import NICHT_ABGABEPFLICHTIG

        llm = FakeLLM()
        frage = "2025, drei Lesungen, Summe 2000 Euro, mit Einnahmeabsicht."
        fakten = Fakten(
            jahr=2025, verwerterart="generalklausel", auftragnehmer_typ="natuerliche_person", leistungsart="Text/Redaktion",
            positionen=[Position(betrag=Decimal("2000"))], veranstaltungszahl=3, einnahmeabsicht=True,
        )
        ergebnis = lauf_bestaetigt(llm, frage, fakten)
        self.assertEqual(ergebnis.ergebnisklasse, NICHT_ABGABEPFLICHTIG)


class TestRechtsprechungsfrage(unittest.TestCase):
    """Befund 6 (behoben): eine reine Recherche darf ohne Jahr beantwortet werden, ohne
    Bestaetigung, aber nie mit einer berechneten Zahl."""

    def test_keine_jahr_pflicht_und_keine_bestaetigung(self):
        llm = FakeLLM()
        frage = "Gibt es eine Regel zur Künstlersozialabgabe bei Eigenwerbung?"
        llm.registriere(frage, Fakten(anfrageart="rechtsprechungsfrage", freitext_rest="eigenwerbung"))
        ergebnis = router.bearbeite_frage(frage, llm)
        self.assertNotEqual(ergebnis.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertNotEqual(ergebnis.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG)

    def test_nie_eine_zahl_in_der_antwort(self):
        llm = FakeLLM()
        frage = "Gibt es eine Regel zur Künstlersozialabgabe bei Eigenwerbung?"
        llm.registriere(frage, Fakten(anfrageart="rechtsprechungsfrage", freitext_rest="eigenwerbung"))
        ergebnis = router.bearbeite_frage(frage, llm)
        self.assertEqual(ergebnis.kern_protokoll, {})

    def test_ohne_treffer_nicht_abgedeckt_und_protokolliert(self):
        llm = FakeLLM()
        frage = "Gibt es ein LSG-Urteil zu Podcast-Produktionen?"
        llm.registriere(frage, Fakten(anfrageart="rechtsprechungsfrage", freitext_rest="podcast produktionen"))
        ergebnis = router.bearbeite_frage(frage, llm)
        self.assertEqual(ergebnis.ergebnisklasse, NICHT_ABGEDECKT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
