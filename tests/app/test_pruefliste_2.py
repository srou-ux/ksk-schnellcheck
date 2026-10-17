"""Prüfliste 2 für den Steuerberater (scripts/erzeuge_pruefliste_2.py, 14.10.2026): Inhalt aus den
Daten, und Eintragungen des Steuerberaters werden nie überschrieben. Ohne Quellenindex."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

W = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("pruefliste_2", W / "scripts" / "erzeuge_pruefliste_2.py")
P2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P2)
FASSUNGEN = {2019: "A", 2020: "A", 2021: "A", 2022: "A", 2023: "B", 2024: "B"}


class Pruefliste2(unittest.TestCase):
    def test_fassungen_lesbar(self):
        self.assertEqual(P2.fassungen_lesbar(FASSUNGEN), "A: 2019–2022; B: 2023–2024")

    def test_regeln_ohne_fassung_aus_dem_katalog(self):
        ids = {r["Regel-ID"] for r in P2.regeln_ohne_fassung(fassungen=FASSUNGEN)}
        self.assertIn("R-18", ids)       # „aktuell (…)“
        self.assertIn("R-233", ids)      # „Fassung vor 01.07.2001“
        self.assertNotIn("R-01", ids)

    def test_baue_und_schutz(self):
        wb = P2.baue([], [{"id": "X-01", "gruppe": "G", "jahr": None, "frage": "f", "erwartet": "e", "geliefert": []}],
                     [], [], [{"nr": "Q-01", "thema": "t", "frage": "f", "heute": "h", "bezug": "b", "herkunft": "x"}],
                     "A: 2019–2022", "14.10.2026")
        self.assertEqual(wb.sheetnames, ["Anleitung", "Regeln ohne Fassung", "Fundstellen je Testfall",
                                         "Quellen Gültigkeit", "Textbausteine neu", "Offene Fachfragen"])
        ws = wb["Fundstellen je Testfall"]
        self.assertIn("Nicht abgedeckt", ws["F2"].value)
        with tempfile.TemporaryDirectory() as d:
            ziel = Path(d) / "p.xlsx"
            wb.save(ziel)
            P2._schutz(ziel)  # nur 'offen': kein Abbruch
            ws["G2"] = "ja"
            wb.save(ziel)
            with self.assertRaises(SystemExit):
                P2._schutz(ziel)
