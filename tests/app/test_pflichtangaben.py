"""Tests fuer app/pflichtangaben.py: ohne Jahr nur die Jahr-Frage; sonst hoechstens drei."""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.pflichtangaben import FRAGE_JAHR, FRAGE_VERWERTERART, MAX_FRAGEN, fehlende_pflichtangaben, vollstaendig
from app.schema import Fakten, Position


class TestPflichtangaben(unittest.TestCase):
    def test_ohne_jahr_nur_jahr_frage(self):
        fragen = fehlende_pflichtangaben(Fakten())
        self.assertEqual(fragen, [FRAGE_JAHR])

    def test_ohne_jahr_ignoriert_andere_luecken(self):
        # Auch wenn sonst alles fehlt: mit fehlendem Jahr kommt NUR die Jahr-Frage.
        fragen = fehlende_pflichtangaben(Fakten(jahr=None))
        self.assertEqual(len(fragen), 1)

    def test_hoechstens_drei_fragen(self):
        fragen = fehlende_pflichtangaben(Fakten(jahr=2025))
        self.assertLessEqual(len(fragen), MAX_FRAGEN)

    def test_vollstaendige_angaben_keine_fragen(self):
        f = Fakten(
            jahr=2025,
            verwerterart="eigenwerber",
            auftragnehmer_typ="natuerliche_person",
            leistungsart="Grafik/Design",
            positionen=[Position(betrag=Decimal("900"))],
        )
        self.assertEqual(fehlende_pflichtangaben(f), [])
        self.assertTrue(vollstaendig(f))

    def test_veranstaltungszahl_ohne_einnahmeabsicht_fragt_nach(self):
        f = Fakten(
            jahr=2025,
            verwerterart="generalklausel",
            auftragnehmer_typ="natuerliche_person",
            leistungsart="Musik",
            positionen=[Position(betrag=Decimal("500"))],
            veranstaltungszahl=4,
        )
        fragen = fehlende_pflichtangaben(f)
        self.assertTrue(any("Einnahme" in s for s in fragen))

    def test_verwerterart_fehlt_bei_positionen_fuehrt_zu_rueckfrage(self):
        """Livetest-Befund L1: ohne verwerterart darf weder Eigenwerbung noch typischer
        Verwerter stillschweigend angenommen werden, sobald es ueberhaupt eine Zahlenbasis
        gibt (hier: Positionen)."""
        f = Fakten(
            jahr=2026,
            auftragnehmer_typ="natuerliche_person",
            positionen=[Position(betrag=Decimal("900"))],
        )
        fragen = fehlende_pflichtangaben(f)
        self.assertIn(FRAGE_VERWERTERART, fragen)

    def test_verwerterart_fehlt_bei_veranstaltungszahl_fuehrt_zu_rueckfrage(self):
        f = Fakten(
            jahr=2025,
            auftragnehmer_typ="natuerliche_person",
            positionen=[Position(betrag=Decimal("2000"))],
            veranstaltungszahl=4,
            einnahmeabsicht=True,
        )
        fragen = fehlende_pflichtangaben(f)
        self.assertIn(FRAGE_VERWERTERART, fragen)

    def test_verwerterart_vorhanden_keine_rueckfrage_danach(self):
        f = Fakten(
            jahr=2026,
            verwerterart="typischer_verwerter",
            auftragnehmer_typ="natuerliche_person",
            leistungsart="Grafik/Design",  # seit 11.10.2026 nötig (Tätigkeitsprüfung)
            positionen=[Position(betrag=Decimal("900"))],
        )
        self.assertEqual(fehlende_pflichtangaben(f), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
