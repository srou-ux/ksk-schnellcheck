"""Tests fuer app/quellen.py (RAG auf dem echten Regelkatalog/quellen-Index -- liest nur,
aendert nichts in regelwerk/ oder quellen/)."""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app import quellen as Q


class TestFassung(unittest.TestCase):
    def test_fassung_a_bis_2022(self):
        self.assertEqual(Q.fassung_fuer_jahr(2021), "A")
        self.assertEqual(Q.fassung_fuer_jahr(2022), "A")

    def test_fassung_b_ab_2023(self):
        self.assertEqual(Q.fassung_fuer_jahr(2023), "B")
        self.assertEqual(Q.fassung_fuer_jahr(2026), "B")

    def test_fassung_passt_erkennt_verneinung_nicht_als_zusage(self):
        # Regression: "B nicht geprueft" darf NICHT als Zusage fuer Fassung B gelten.
        self.assertTrue(Q._fassung_passt("Fassung A (bis 31.12.2022); B nicht geprüft", "A"))
        self.assertFalse(Q._fassung_passt("Fassung A (bis 31.12.2022); B nicht geprüft", "B"))

    def test_fassung_passt_alle_drei_token(self):
        self.assertTrue(Q._fassung_passt("A, B, aktuell (Text gleich)", "A"))
        self.assertTrue(Q._fassung_passt("A, B, aktuell (Text gleich)", "B"))


class TestBlattnameIstStabilGegenPositionsverschiebung(unittest.TestCase):
    """Regression: regelwerk/Regelkatalog_24_KSVG_Entwurf.xlsx bekam ein neues Blatt
    'Regelregister' an Position 1, wodurch alle folgenden Blatt-Indizes sich verschoben
    (siehe aufgaben/FUNDE_Chatbot.md). app/quellen.py muss Blaetter ueber den Namen finden,
    nicht ueber die Position."""

    def test_regeln_blatt_nicht_mit_regelregister_verwechselt(self):
        wb_namen = ["Regeln", "Regelregister", "Schwellen nach Jahr"]

        class FakeWB:
            sheetnames = wb_namen

        self.assertEqual(Q._blattname(FakeWB(), exakt="Regeln"), "Regeln")

    def test_alle_drei_tabellen_liefern_daten(self):
        self.assertGreater(len(Q.alle_regeln()), 0)
        self.assertGreater(len(Q.alle_schwellen()), 0)
        self.assertGreater(len(Q.alle_abgabesaetze()), 0)


class TestRegelnUndSchwellen(unittest.TestCase):
    def test_regel_existiert(self):
        self.assertTrue(Q.regel_existiert("R-01"))
        self.assertFalse(Q.regel_existiert("R-99999"))

    def test_regeln_suchen_respektiert_fassung(self):
        # R-62/R-63 gelten nur fuer Fassung A (BSG-Rechtsprechung zur alten Rechtslage) und
        # duerfen fuer 2024 (Fassung B) nicht auftauchen.
        treffer_2021 = {r["regel_id"] for r in Q.regeln_suchen(2021, ["eigenwerb"])}
        treffer_2024 = {r["regel_id"] for r in Q.regeln_suchen(2024, ["eigenwerb"])}
        self.assertIn("R-62", treffer_2021)
        self.assertNotIn("R-62", treffer_2024)

    def test_abgabesatz_bekannter_jahre(self):
        self.assertEqual(Q.abgabesatz_fuer_jahr(2025), Decimal("5"))
        self.assertEqual(Q.abgabesatz_fuer_jahr(2026), Decimal("4.9"))

    def test_abgabesatz_unbekanntes_jahr_ist_none(self):
        self.assertIsNone(Q.abgabesatz_fuer_jahr(1990))

    def test_schwelle_deckt_nur_2019_bis_2027_ab(self):
        self.assertIsNone(Q.schwelle_fuer_jahr(2017))
        self.assertIsNotNone(Q.schwelle_fuer_jahr(2019))
        self.assertIsNotNone(Q.schwelle_fuer_jahr(2027))


class TestFundstellenPruefung(unittest.TestCase):
    def test_bekannte_regel_id(self):
        self.assertTrue(Q.fundstelle_bekannt("R-01"))

    def test_bekanntes_aktenzeichen(self):
        self.assertTrue(Q.fundstelle_bekannt("B 3 KS 3/21 R"))

    def test_erfundenes_aktenzeichen_wird_abgelehnt(self):
        self.assertFalse(Q.fundstelle_bekannt("B 9 ZZ 99/99 R"))

    def test_leerer_text_ist_nicht_bekannt(self):
        self.assertFalse(Q.fundstelle_bekannt(""))

    def test_aktenzeichen_in_text_extrahiert_muster(self):
        treffer = Q.aktenzeichen_in_text("Siehe BSG 01.06.2022, B 3 KS 3/21 R, Rn. 14.")
        self.assertTrue(any("3/21" in t for t in treffer))


if __name__ == "__main__":
    unittest.main(verbosity=2)
