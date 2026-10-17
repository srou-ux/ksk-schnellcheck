"""Live-Lauf 14.10.2026 (P-20b, Stand 563ab52): Abgabe ohne Übungsleiterpauschale (3.500 € statt
1.100 €), weil die Modellangaben zur Pauschale dem Text widersprachen und die Faktenbestätigung sie
nicht zeigte. Der Text geht vor; die Bestätigung zeigt die Pauschale. Offline, erfundene Daten."""
from __future__ import annotations

import unittest
from decimal import Decimal as D

from app import bestaetigung, router
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position as P

FRAGE = ("Unser abgabepflichtiger gemeinnütziger Musikverein hat 2020 einer nebenberuflichen Chorleiterin "
         "3.500 € gezahlt. Sie hat die Übungsleiterpauschale schriftlich bestätigt. Wie hoch ist die Abgabe?")
BASIS = dict(jahr=2020, verwerterart="typischer_verwerter", auftragnehmer_typ="natuerliche_person",
             positionen=[P(betrag=D("3500"), bezeichnung="Zahlung an nebenberufliche Chorleiterin")])


def _lauf(frage: str, **extra):
    llm = FakeLLM()
    llm.registriere(frage, Fakten(**BASIS, **extra))
    a = router.bearbeite_frage(frage, llm)
    bestaetigung.SPEICHER.bestaetige(a.sitzungskennung, a.fakten_hash)
    return a, router.fuehre_nach_bestaetigung_aus(a.sitzungskennung, FakeLLM())


class PauschaleAusText(unittest.TestCase):
    def test_modell_setzt_art_laesst_aber_bewertung(self):
        a, c = _lauf(FRAGE, anfrageart="bewertung", pauschale_art="uebungsleiter", pauschale_bestaetigung=False)
        self.assertIn("Pauschale: Übungsleiterpauschale, schriftlich bestätigt: ja", " | ".join(a.fakten_zusammenfassung))
        self.assertEqual(c.kern_protokoll.get("bemessungsgrundlage"), D("1100"))

    def test_erfundener_verbrauch_zaehlt_nicht(self):
        _, c = _lauf(FRAGE, anfrageart="bewertung", pauschale_bereits_ausgeschoepft=D("2400"))
        self.assertEqual(c.kern_protokoll.get("bemessungsgrundlage"), D("1100"))

    def test_genannter_verbrauch_zaehlt(self):
        frage = FRAGE.replace("Wie hoch", "Davon hat sie bei einem anderen Verein schon 1.000 € genutzt. Wie hoch")
        a, c = _lauf(frage, anfrageart="bewertung", pauschale_bereits_ausgeschoepft=D("1000"))
        self.assertIn("davon schon verbraucht: 1.000,00 €", " | ".join(a.fakten_zusammenfassung))
        self.assertEqual(c.kern_protokoll.get("bemessungsgrundlage"), D("2100"))

    def test_verneinte_bestaetigung_bleibt_nein(self):
        frage = FRAGE.replace("Sie hat die Übungsleiterpauschale schriftlich bestätigt.",
                              "Für die Übungsleiterpauschale liegt keine Bestätigung vor.")
        a, c = _lauf(frage, anfrageart="bewertung", pauschale_art="uebungsleiter", pauschale_bestaetigung=False)
        self.assertIn("schriftlich bestätigt: nein", " | ".join(a.fakten_zusammenfassung))
        self.assertNotEqual(c.kern_protokoll.get("bemessungsgrundlage"), D("1100"))

    def test_andere_pauschale_im_text_wird_nicht_geraten(self):
        a, _ = _lauf(FRAGE, anfrageart="bewertung", pauschale_art="ehrenamt")
        self.assertIn("Pauschale: Ehrenamtspauschale", " | ".join(a.fakten_zusammenfassung))
