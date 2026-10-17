"""Tests fuer app/anonymisierung.py -- und Dokumentation ihrer bewussten Grenzen
(einfache Regex-Heuristik, siehe Docstring der Datei)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.anonymisierung import anonymisiere, gefundene_kategorien


class TestAnonymisierung(unittest.TestCase):
    def test_email_wird_maskiert(self):
        ergebnis = anonymisiere("Bitte antworten an max.mustermann@kanzlei-beispiel.de")
        self.assertNotIn("max.mustermann@kanzlei-beispiel.de", ergebnis)
        self.assertIn("[E-Mail]", ergebnis)

    def test_iban_wird_maskiert(self):
        ergebnis = anonymisiere("Zahlung auf DE89 3704 0044 0532 0130 00 bitte.")
        self.assertNotIn("3704 0044", ergebnis)
        self.assertIn("[IBAN]", ergebnis)

    def test_telefonnummer_wird_maskiert(self):
        ergebnis = anonymisiere("Rueckruf unter 0221 1234567 moeglich.")
        self.assertIn("[Telefonnummer]", ergebnis)

    def test_adresse_wird_maskiert(self):
        ergebnis = anonymisiere("Die Agentur sitzt in der Musterstraße 12.")
        self.assertIn("[Adresse]", ergebnis)
        self.assertNotIn("Musterstraße 12", ergebnis)

    def test_ort_wird_maskiert(self):
        ergebnis = anonymisiere("Sitz: 50667 Köln")
        self.assertIn("[Ort]", ergebnis)

    def test_name_nach_anrede_wird_maskiert(self):
        ergebnis = anonymisiere("Mandant Erika Musterfrau fragt nach der Abgabe.")
        self.assertIn("Mandant [Name]", ergebnis)
        self.assertNotIn("Erika Musterfrau", ergebnis)

    def test_grenze_name_ohne_anrede_wird_nicht_erkannt(self):
        # Bekannte, dokumentierte Grenze der einfachen Heuristik (siehe app/anonymisierung.py).
        ergebnis = anonymisiere("Erika Musterfrau hat 2025 eine Website bestellt.")
        self.assertIn("Erika Musterfrau", ergebnis)

    def test_fachtext_ohne_personenbezug_bleibt_unveraendert(self):
        text = "2025, Werbeagentur, 900 Euro Honorar fuer einen Flyer."
        self.assertEqual(anonymisiere(text), text)

    def test_gefundene_kategorien(self):
        kategorien = gefundene_kategorien("Kontakt: info@beispiel.de, Tel. 030 1234567")
        self.assertIn("E-Mail", kategorien)
        self.assertIn("Telefonnummer", kategorien)


if __name__ == "__main__":
    unittest.main(verbosity=2)
