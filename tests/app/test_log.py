"""Tests fuer app/log.py (Lueckenprotokoll). Schreibt nur in ein temporaeres Verzeichnis,
nie in app/_lokal/ selbst."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.log import lies_protokoll, protokolliere


class TestLueckenprotokoll(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.pfad = Path(self._tmp.name) / "lueckenprotokoll.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def test_eintrag_wird_geschrieben_und_gelesen(self):
        protokolliere("Frage von Erika Musterfrau", 2025, "Nicht abgedeckt", pfad=self.pfad)
        eintraege = lies_protokoll(pfad=self.pfad)
        self.assertEqual(len(eintraege), 1)
        self.assertEqual(eintraege[0]["jahr"], 2025)
        self.assertEqual(eintraege[0]["grund"], "Nicht abgedeckt")

    def test_frage_wird_anonymisiert_gespeichert(self):
        protokolliere("Mandant Erika Musterfrau fragt...", 2025, "Nicht abgedeckt", pfad=self.pfad)
        rohinhalt = self.pfad.read_text(encoding="utf-8")
        self.assertNotIn("Erika Musterfrau", rohinhalt)

    def test_mehrere_eintraege_werden_angehaengt(self):
        protokolliere("Frage 1", 2024, "Nicht abgedeckt", pfad=self.pfad)
        protokolliere("Frage 2", 2025, "Pruefung fehlgeschlagen", pfad=self.pfad)
        self.assertEqual(len(lies_protokoll(pfad=self.pfad)), 2)

    def test_leeres_protokoll_ohne_datei(self):
        self.assertEqual(lies_protokoll(pfad=self.pfad), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
