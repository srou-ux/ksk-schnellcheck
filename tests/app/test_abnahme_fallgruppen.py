"""Abnahmetests fuer die in Chatbot Teil 1b neu verdrahteten Kernfunktionen (Vorauszahlung,
Saeumniszuschlag, Verpflegung, Uebungsleiterpauschale, Kommission, Schaetzung Ausland,
Rechnungsanalyse), jeweils mit einem Fall aus `regelwerk/testfaelle_maschinenlesbar.json`
ueber die ganze Kette (FakeLLM -> Pflichtangaben -> Faktenbestaetigung (Teil 1d) -> Router ->
echter Kern -> Bausteinantwort -> Pruefung)."""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from tests.app.hilfen import lauf_bestaetigt

from app.ergebnisklassen import ABGABEPFLICHTIG, GRENZFALL
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position


class TestVorauszahlung(unittest.TestCase):
    def test_p04_vorauszahlung_2026_24000(self):
        # P-04: jahr=2026, bg=24000 -> wert 98.00
        frage = "2026, Bemessungsgrundlage Vorjahr 24.000 €. Monatliche Vorauszahlung?"
        fakten = Fakten(anfrageart="vorauszahlung", jahr=2026, bemessungsgrundlage_vorjahr=Decimal("24000"))
        ergebnis = lauf_bestaetigt(FakeLLM(), frage, fakten)
        self.assertEqual(ergebnis.kern_protokoll.get("vorauszahlung_monatlich"), Decimal("98.00"))


class TestSaeumniszuschlag(unittest.TestCase):
    def test_p07_saeumnis_2026(self):
        # P-07: rueckstand=[1234], monate=3, jahr=2026, gesondert=False -> abgabe 36.00
        frage = "Rückstand 1.234 €, 3 Monate, 2026. Säumniszuschlag?"
        fakten = Fakten(anfrageart="saeumniszuschlag", jahr=2026, rueckstand=Decimal("1234"), saeumnis_monate=3)
        ergebnis = lauf_bestaetigt(FakeLLM(), frage, fakten)
        self.assertEqual(ergebnis.kern_protokoll.get("abgabe"), Decimal("36.00"))


class TestVerpflegung(unittest.TestCase):
    def test_l18_genau_acht_stunden_ist_grenzfall(self):
        # L-18: jahr=2025, stunden=8, erstattung=14 -> Grenzfall
        frage = "2025, Reise genau 8 Stunden, 14 € Verpflegungserstattung. Bemessungsgrundlage?"
        fakten = Fakten(anfrageart="verpflegung", jahr=2025, reise_stunden=Decimal("8"), reise_erstattung=Decimal("14"))
        ergebnis = lauf_bestaetigt(FakeLLM(), frage, fakten)
        self.assertEqual(ergebnis.ergebnisklasse, GRENZFALL)


class TestUebungsleiterpauschale(unittest.TestCase):
    def test_j01_uebungsleiter_2020_3500(self):
        # J-01: jahr=2020, betrag=3500, art=uebungsleiter -> bg 1100, abgabe 46.20
        frage = "2020, Übungsleiterhonorar 3.500 €. Bemessungsgrundlage und Abgabe?"
        fakten = Fakten(
            anfrageart="uebungsleiter_pauschale", jahr=2020, pauschale_art="uebungsleiter",
            positionen=[Position(betrag=Decimal("3500"))],
        )
        ergebnis = lauf_bestaetigt(FakeLLM(), frage, fakten)
        self.assertEqual(ergebnis.kern_protokoll.get("bemessungsgrundlage_nach_pauschale"), Decimal("1100"))
        self.assertEqual(ergebnis.kern_protokoll.get("abgabe"), Decimal("46.20"))


class TestKommission(unittest.TestCase):
    def test_x01_kommission_2025(self):
        # X-01: jahr=2025, preis=1000, einbehalt=500 -> bg 500, abgabe 25.00
        frage = "2025, Verkaufspreis 1.000 €, Einbehalt 500 €. Abgabepflichtig?"
        fakten = Fakten(
            anfrageart="kommission", jahr=2025,
            kommission_verkaufspreis=Decimal("1000"), kommission_einbehalt=Decimal("500"),
        )
        ergebnis = lauf_bestaetigt(FakeLLM(), frage, fakten)
        self.assertEqual(ergebnis.ergebnisklasse, ABGABEPFLICHTIG)
        self.assertEqual(ergebnis.kern_protokoll.get("bemessungsgrundlage"), Decimal("500"))
        self.assertEqual(ergebnis.kern_protokoll.get("abgabe"), Decimal("25.00"))


class TestSchaetzungAusland(unittest.TestCase):
    def test_c10_schaetzung_2026(self):
        # C-10: jahr=2026, brutto=40000 -> bg 10000, abgabe 490.00
        frage = "2026, Bruttoeinnahmen Ausland 40.000 €, keine Kenntnis der echten Entgelte. Schätzung?"
        fakten = Fakten(anfrageart="schaetzung_ausland", jahr=2026, schaetzung_bruttoeinnahmen=Decimal("40000"))
        ergebnis = lauf_bestaetigt(FakeLLM(), frage, fakten)
        self.assertEqual(ergebnis.kern_protokoll.get("bemessungsgrundlage"), Decimal("10000"))
        self.assertEqual(ergebnis.kern_protokoll.get("abgabe"), Decimal("490.00"))


class TestRechnungsanalyse(unittest.TestCase):
    def test_h01_rechnung_2026(self):
        # H-01 (siehe tests/belege/AT-2026-204_Agentur_und_Vertretung_fiktiv.pdf):
        # 12 Positionen, nur Position 5 (850 €, vertretung_kuenstler) zaehlt sicher.
        frage = "Rechnung 2026 mit 12 Positionen (siehe Anlage). Bemessungsgrundlage?"
        positionen = [
            Position(betrag=Decimal("2400"), rechnungsrolle="an_kapitalgesellschaft", nr=1),
            Position(betrag=Decimal("1180"), rechnungsrolle="an_kapitalgesellschaft", nr=2),
            Position(betrag=Decimal("1360"), rechnungsrolle="an_kapitalgesellschaft", nr=3),
            Position(betrag=Decimal("940"), rechnungsrolle="an_kapitalgesellschaft", nr=4),
            Position(betrag=Decimal("850"), rechnungsrolle="vertretung_kuenstler", nr=5),
            Position(betrag=Decimal("720"), rechnungsrolle="eigengeschaeft_dritter", nr=6),
            Position(betrag=Decimal("125"), rechnungsrolle="an_kapitalgesellschaft", nr=7),
            Position(betrag=Decimal("380"), rechnungsrolle="an_kapitalgesellschaft", nr=8),
            Position(betrag=Decimal("145"), rechnungsrolle="nicht_kuenstlerisch", nr=9),
            Position(betrag=Decimal("206"), rechnungsrolle="reise_kuenstler", nr=10, nachgewiesen=True),
            Position(betrag=Decimal("310"), rechnungsrolle="an_kapitalgesellschaft", nr=11),
            Position(betrag=Decimal("340"), rechnungsrolle="an_kapitalgesellschaft", nr=12),
        ]
        fakten = Fakten(
            anfrageart="rechnungsanalyse", jahr=2026, positionen=positionen,
            empfaenger_abgabepflichtig=True, agentur_abgabepflichtig=True,
        )
        ergebnis = lauf_bestaetigt(FakeLLM(), frage, fakten)
        self.assertEqual(ergebnis.ergebnisklasse, ABGABEPFLICHTIG)
        self.assertEqual(ergebnis.kern_protokoll.get("bemessungsgrundlage"), Decimal("850"))
        self.assertEqual(ergebnis.kern_protokoll.get("abgabe"), Decimal("41.65"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
