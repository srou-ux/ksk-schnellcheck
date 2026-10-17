"""Tests fuer app/schema.py: unbekannte Felder bleiben None, nie geraten."""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pydantic import ValidationError

from app.schema import Fakten, Position


class TestFakten(unittest.TestCase):
    def test_alle_felder_optional_und_default_none(self):
        f = Fakten()
        self.assertIsNone(f.jahr)
        self.assertIsNone(f.unternehmensart)
        self.assertIsNone(f.auftraggeber_typ)
        self.assertIsNone(f.leistungsart)
        self.assertEqual(f.positionen, [])
        self.assertIsNone(f.veranstaltungszahl)
        self.assertIsNone(f.einnahmeabsicht)

    def test_unbekanntes_bleibt_none_bei_teilbefuellung(self):
        f = Fakten(jahr=2025)
        self.assertEqual(f.jahr, 2025)
        self.assertIsNone(f.auftragnehmer_typ)
        self.assertIsNone(f.leistungsart)

    def test_jahr_ausserhalb_plausibler_grenzen_wirft_fehler(self):
        with self.assertRaises(ValidationError):
            Fakten(jahr=1066)
        with self.assertRaises(ValidationError):
            Fakten(jahr=3000)

    def test_summe_positionen(self):
        f = Fakten(positionen=[Position(betrag=Decimal("100")), Position(betrag=Decimal("50.50"))])
        self.assertEqual(f.summe_positionen(), Decimal("150.50"))

    def test_summe_positionen_leer_ist_null(self):
        self.assertEqual(Fakten().summe_positionen(), Decimal("0"))

    def test_auftragnehmer_typ_nur_erlaubte_werte(self):
        Fakten(auftragnehmer_typ="GmbH_UG_AG")  # darf nicht werfen
        with self.assertRaises(ValidationError):
            Fakten(auftragnehmer_typ="Einhorn_AG")


if __name__ == "__main__":
    unittest.main(verbosity=2)
