"""Tests fuer app/llm/fake.py: registrierte Fakten (fuer Tests), die einfache
Heuristik-Extraktion (fuer den Demo-Modus) und das Platzhalter-Antwortschema (Teil 1d)."""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.baustein import PLATZHALTER_MUSTER, erzeuge_platzhalter, pruefe_rohtext
from app.llm.base import AntwortKontext
from app.llm.fake import FakeLLM
from app.schema import Fakten


class TestFakeLLMRegistrierung(unittest.TestCase):
    def test_registrierte_fakten_werden_exakt_zurueckgegeben(self):
        llm = FakeLLM()
        vorgabe = Fakten(jahr=2024, leistungsart="Grafik/Design")
        llm.registriere("Testfrage, 2024", vorgabe)
        self.assertEqual(llm.extrahiere_fakten("Testfrage, 2024"), vorgabe)

    def test_registrierung_ist_gross_klein_und_leerzeichen_tolerant(self):
        llm = FakeLLM()
        vorgabe = Fakten(jahr=2024)
        llm.registriere("  Testfrage   ", vorgabe)
        self.assertEqual(llm.extrahiere_fakten("testfrage"), vorgabe)


class TestFakeLLMHeuristik(unittest.TestCase):
    def test_jahr_wird_erkannt(self):
        f = FakeLLM().extrahiere_fakten("Wie ist das 2025 zu bewerten?")
        self.assertEqual(f.jahr, 2025)

    def test_unbekanntes_bleibt_none(self):
        f = FakeLLM().extrahiere_fakten("Irgendeine Frage ohne klare Angaben.")
        self.assertIsNone(f.jahr)
        self.assertIsNone(f.auftragnehmer_typ)

    def test_betrag_wird_erkannt(self):
        f = FakeLLM().extrahiere_fakten("2025, 900 € Honorar fuer ein Logo.")
        self.assertEqual(len(f.positionen), 1)
        self.assertEqual(f.positionen[0].betrag, Decimal("900"))

    def test_rechtsform_gmbh_wird_erkannt(self):
        f = FakeLLM().extrahiere_fakten("Die GmbH beauftragt 2025 einen Designer.")
        self.assertEqual(f.auftragnehmer_typ, "GmbH_UG_AG")


class TestFakeLLMBeschreibeFall(unittest.TestCase):
    """Seit Chatbot Teil 1g (Mischform) schreibt FakeLLM (wie ein echtes Modell) nur noch
    eine kurze Fallbeschreibung -- der Antwort-Koerper kommt ausschliesslich aus festen
    Textbausteinen (app/textbausteine.py). Die Beschreibung bleibt reiner Platzhalter-Text:
    keinen Schlusssatz, keine Ergebnisaussage, keine eigenen Werte."""

    def test_beschreibung_besteht_nur_aus_erlaubten_platzhaltern_und_fliesstext(self):
        kontext = AntwortKontext(
            frage="f", fakten=Fakten(jahr=2025), ergebnisklasse="Abgabepflichtig (Vorschlag)",
            kern_protokoll={"bemessungsgrundlage": Decimal("900"), "abgabe": Decimal("45.00"), "abgabesatz_prozent": Decimal("5")},
        )
        erlaubte_namen = set(erzeuge_platzhalter(kontext).keys())
        beschreibung = FakeLLM().beschreibe_fall(kontext)
        self.assertEqual(pruefe_rohtext(beschreibung, erlaubte_namen), [])

    def test_kein_schlusssatz_in_der_fallbeschreibung(self):
        kontext = AntwortKontext(frage="f", fakten=Fakten(), ergebnisklasse="Nicht abgedeckt (Quelle fehlt)")
        beschreibung = FakeLLM().beschreibe_fall(kontext)
        self.assertNotIn("Entwurf", beschreibung)

    def test_jahr_wird_als_platzhalter_referenziert(self):
        kontext = AntwortKontext(frage="f", fakten=Fakten(jahr=2025), ergebnisklasse="Rückfrage nötig")
        beschreibung = FakeLLM().beschreibe_fall(kontext)
        self.assertIn("{JAHR}", beschreibung)
        self.assertNotIn("2025", beschreibung)  # Wert erst nach dem Einsetzen sichtbar

    def test_ohne_jahr_ergibt_sich_ein_statischer_platzhalterfreier_text(self):
        kontext = AntwortKontext(frage="f", fakten=Fakten(), ergebnisklasse="Nicht abgedeckt (Quelle fehlt)")
        beschreibung = FakeLLM().beschreibe_fall(kontext)
        self.assertEqual(PLATZHALTER_MUSTER.findall(beschreibung), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
