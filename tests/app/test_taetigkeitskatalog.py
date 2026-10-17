"""Tätigkeitskatalog des Nutzers (200 Fälle, 15.10.2026): Funde im Excel-Blatt 'Tätigkeitsabgrenzung'.

Neue Zeilen T-70 bis T-75 (Entwurf) und die Regel 'verneinter Begriff der gewählten Zeile'. Die Einordnung kommt
aus der Excel (app/taetigkeiten.py), nicht aus diesem Test; geprüft wird, dass zu breite Begriffe nicht mehr still
entscheiden. Katalog: aufgaben/audit/taetigkeitskatalog_200.json."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from app import taetigkeiten as T

W = Path(__file__).resolve().parents[2]


class NeueZeilen(unittest.TestCase):
    def test_vorher_still_falsch_jetzt_nicht_mehr(self):
        erwartet = {
            "Lektor (nur Textkorrektur)": "nicht_kuenstlerisch",          # T-70, R-194
            "Schauspiel-Coach (privat)": "unsicher",                       # T-71, KSVG § 2 'lehrt'
            "Dirigenten-Workshop": "unsicher",
            "Pantomimen-Lehrer (Workshop)": "unsicher",
            "Stimmtrainer (nur Coaching Gesang)": "unsicher",
            "technischer Zeichner (Bauzeichnung)": "unsicher",             # T-72
            "Musikdaten-Kurator (Playlist)": "unsicher",                   # T-73
            "Fotogrammetrie (Vermessung)": "unsicher",                     # T-74
            "Filmmusik-Sync-Agent (Vermittlung)": "unsicher",              # T-75
            "Festival-Plakatierung (aufkleben, keine Gestaltung)": "unsicher",  # verneinter Begriff
        }
        for text, gruppe in erwartet.items():
            with self.subTest(text=text):
                self.assertEqual(T.gruppe(T.erkenne(text)), gruppe)

    def test_unveraendert(self):
        # Publizistik: 'lehrt' steht in § 2 KSVG nur beim Künstler -> Schreib-Coach bleibt Coaching (R-183).
        self.assertEqual(T.erkenne("Schreib-Coach"), "T-34")
        self.assertEqual(T.erkenne("Persönlichkeits-Coach"), "T-34")
        self.assertEqual(T.erkenne("Lektorat"), "T-09")
        self.assertEqual(T.erkenne("Illustrator"), "T-08")
        self.assertEqual(T.erkenne("Grafikleistung (ohne Druckkosten)"), "T-02")

    def test_katalog_vollstaendig(self):
        k = json.loads((W / "aufgaben/audit/taetigkeitskatalog_200.json").read_text(encoding="utf-8"))
        self.assertEqual(len(k["faelle"]), 200)
        self.assertEqual(len({f["id"] for f in k["faelle"]}), 200)
        self.assertTrue(all(f["status"]["freigabe"] == "ENTWURF" for f in k["faelle"]))


if __name__ == "__main__":
    unittest.main()
