"""Tests fuer app/bestaetigung.py (Faktenbestaetigung vor der Berechnung, Chatbot Teil 1d,
Abschnitt B): Hash-Stabilitaet, Zusammenfassung, und der Sitzungsspeicher -- insbesondere
'kein Kern ohne Bestaetigung' und 'eine Korrektur macht die alte Bestaetigung ungueltig'."""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.bestaetigung import Sitzungsspeicher, als_liste, fakten_hash, zusammenfassung
from app.schema import Fakten, Position


class TestFaktenHash(unittest.TestCase):
    def test_gleiche_fakten_ergeben_gleichen_hash(self):
        a = Fakten(jahr=2025, positionen=[Position(betrag=Decimal("900"))])
        b = Fakten(jahr=2025, positionen=[Position(betrag=Decimal("900"))])
        self.assertEqual(fakten_hash(a), fakten_hash(b))

    def test_geaenderter_wert_aendert_den_hash(self):
        a = Fakten(jahr=2025, positionen=[Position(betrag=Decimal("900"))])
        b = Fakten(jahr=2025, positionen=[Position(betrag=Decimal("901"))])
        self.assertNotEqual(fakten_hash(a), fakten_hash(b))


class TestZusammenfassung(unittest.TestCase):
    def test_als_liste_enthaelt_jahr_und_position(self):
        fakten = Fakten(jahr=2025, positionen=[Position(betrag=Decimal("900"), rolle="honorar")])
        liste = als_liste(fakten)
        self.assertIn("Jahr: 2025", liste)
        self.assertTrue(any("900,00 €" in z for z in liste))

    def test_zusammenfassung_endet_mit_rueckfrage(self):
        text = zusammenfassung(Fakten(jahr=2025))
        self.assertTrue(text.endswith("Stimmt das?"))
        self.assertIn("Jahr: 2025", text)


class TestSitzungsspeicher(unittest.TestCase):
    def test_ohne_bestaetigung_ist_ist_bestaetigt_falsch(self):
        speicher = Sitzungsspeicher()
        kennung = speicher.neue_sitzungskennung()
        fakten = Fakten(jahr=2025)
        speicher.setze_fakten(kennung, "Frage", fakten)
        self.assertFalse(speicher.ist_bestaetigt(kennung, fakten))

    def test_bestaetigung_mit_korrektem_hash_macht_ist_bestaetigt_wahr(self):
        speicher = Sitzungsspeicher()
        kennung = speicher.neue_sitzungskennung()
        fakten = Fakten(jahr=2025)
        speicher.setze_fakten(kennung, "Frage", fakten)
        self.assertTrue(speicher.bestaetige(kennung, fakten_hash(fakten)))
        self.assertTrue(speicher.ist_bestaetigt(kennung, fakten))

    def test_bestaetigung_mit_falschem_hash_schlaegt_fehl(self):
        speicher = Sitzungsspeicher()
        kennung = speicher.neue_sitzungskennung()
        fakten = Fakten(jahr=2025)
        speicher.setze_fakten(kennung, "Frage", fakten)
        self.assertFalse(speicher.bestaetige(kennung, "falscher-hash"))
        self.assertFalse(speicher.ist_bestaetigt(kennung, fakten))

    def test_bestaetigung_zu_unbekannter_sitzung_schlaegt_fehl(self):
        speicher = Sitzungsspeicher()
        self.assertFalse(speicher.bestaetige("unbekannt", "irgendein-hash"))

    def test_korrektur_macht_alte_bestaetigung_ungueltig(self):
        """Architektur Teil 1d, Abschnitt B.3: aendert sich ein Fakt (Korrektur), ist die
        alte Bestaetigung nicht mehr gueltig -- es braucht eine neue."""
        speicher = Sitzungsspeicher()
        kennung = speicher.neue_sitzungskennung()
        alt = Fakten(jahr=2025, positionen=[Position(betrag=Decimal("900"))])
        speicher.setze_fakten(kennung, "Frage", alt)
        self.assertTrue(speicher.bestaetige(kennung, fakten_hash(alt)))
        self.assertTrue(speicher.ist_bestaetigt(kennung, alt))

        neu = Fakten(jahr=2025, positionen=[Position(betrag=Decimal("950"))])
        speicher.setze_fakten(kennung, "Frage (korrigiert)", neu)
        self.assertFalse(speicher.ist_bestaetigt(kennung, neu))

        # Erst die erneute, ausdrueckliche Bestaetigung der NEUEN Fakten macht die Sitzung
        # wieder gueltig.
        self.assertTrue(speicher.bestaetige(kennung, fakten_hash(neu)))
        self.assertTrue(speicher.ist_bestaetigt(kennung, neu))

    def test_hole_fakten_und_hole_frage(self):
        speicher = Sitzungsspeicher()
        kennung = speicher.neue_sitzungskennung()
        fakten = Fakten(jahr=2025)
        speicher.setze_fakten(kennung, "Meine Frage", fakten)
        self.assertEqual(speicher.hole_fakten(kennung), fakten)
        self.assertEqual(speicher.hole_frage(kennung), "Meine Frage")

    def test_hole_fakten_fuer_unbekannte_sitzung_ist_none(self):
        speicher = Sitzungsspeicher()
        self.assertIsNone(speicher.hole_fakten("unbekannt"))
        self.assertIsNone(speicher.hole_frage("unbekannt"))

    def test_sitzungskennungen_sind_eindeutig(self):
        speicher = Sitzungsspeicher()
        kennungen = {speicher.neue_sitzungskennung() for _ in range(100)}
        self.assertEqual(len(kennungen), 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
