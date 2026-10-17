"""Tests zu aufgaben/PROMPT_ClaudeCode_Chatbot_Livetest1_Befunde.md (Befunde aus dem ersten
Livetest im Codespace, Demo-Modus und Mistral, 10.10.2026): L1 (Verwerterart-Default),
L2 (Verlauf im Demo-Modus), L3 (Knopf-Erkennung), L5 (Umlaute/Darstellung), L6 (Fundstellen).
L4 ist laut Auftrag nur zu dokumentieren, nicht umzubauen -- hier kein Test dafuer."""
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from tests.app.hilfen import lauf_bestaetigt

from app import bestaetigung, pflichtangaben, router
from app.ergebnisklassen import (
    ABGABEPFLICHTIG,
    FAKTEN_BESTAETIGUNG_NOETIG,
    NICHT_ABGABEPFLICHTIG,
    PRUEFUNG_FEHLGESCHLAGEN,
    RUECKFRAGE_NOETIG,
)
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position as P

NP = "natuerliche_person"


# ==========================================================================================
# L1: verwerterart ist Pflichtangabe, kein stillschweigender Default mehr.
# ==========================================================================================
class TestL1VerwerterartKeinDefault(unittest.TestCase):
    def test_900_typischer_verwerter_ist_abgabepflichtig(self):
        frage = "Werbeagentur zahlt 2026 900 Euro an einen freien Grafiker."
        fakten = Fakten(
            jahr=2026, verwerterart="typischer_verwerter", auftragnehmer_typ=NP,
            positionen=[P(betrag=D("900"), rolle="honorar")],
        )
        ergebnis = lauf_bestaetigt(FakeLLM(), frage, fakten)
        self.assertEqual(ergebnis.ergebnisklasse, ABGABEPFLICHTIG)

    def test_900_eigenwerber_2026_ist_nicht_abgabepflichtig(self):
        frage = "Eigenwerbung: 2026 900 Euro an einen freien Grafiker."
        fakten = Fakten(
            jahr=2026, verwerterart="eigenwerber", auftragnehmer_typ=NP,
            positionen=[P(betrag=D("900"), rolle="honorar")],
        )
        ergebnis = lauf_bestaetigt(FakeLLM(), frage, fakten)
        self.assertEqual(ergebnis.ergebnisklasse, NICHT_ABGABEPFLICHTIG)

    def test_900_ohne_verwerterart_ist_rueckfrage(self):
        frage = "2026 900 Euro an einen freien Grafiker."
        fakten = Fakten(jahr=2026, auftragnehmer_typ=NP, positionen=[P(betrag=D("900"), rolle="honorar")])
        ergebnis = lauf_bestaetigt(FakeLLM(), frage, fakten)
        self.assertEqual(ergebnis.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertIn(pflichtangaben.FRAGE_VERWERTERART, ergebnis.rueckfragen)

    def test_werbeagentur_ohne_verwerterart_wird_nicht_als_nicht_abgabepflichtig_falsch_geraten(self):
        """Der konkrete Livetest-Fall: eine Werbeagentur zahlt 900 Euro -- OHNE Angabe der
        verwerterart darf daraus nie 'Nicht abgabepflichtig' (stillschweigende
        Eigenwerbungs-Annahme) werden. Seit dem Pruefkatalog-Befund M3 erkennt
        app/zuordnung.py::absichere_verwerterart 'Werbeagentur' selbst als Beleg fuer
        'typischer Verwerter' -- das Ergebnis ist deshalb jetzt direkt Abgabepflichtig
        (keine Schwelle), nicht mehr nur eine Rueckfrage."""
        frage = "Werbeagentur 2026, freie Grafikerin, 900 Euro."
        fakten = Fakten(jahr=2026, auftragnehmer_typ=NP, positionen=[P(betrag=D("900"), rolle="honorar")])
        ergebnis = lauf_bestaetigt(FakeLLM(), frage, fakten)
        self.assertNotEqual(ergebnis.ergebnisklasse, NICHT_ABGABEPFLICHTIG)
        self.assertEqual(ergebnis.ergebnisklasse, ABGABEPFLICHTIG)

    def test_unternehmen_ohne_erkennbare_verwerterart_fuehrt_weiterhin_zu_rueckfrage(self):
        """Nennt der Text KEINEN erkennbaren Begriff (weder Eigenwerbung noch ein typischer-
        Verwerter-Geschaeftstyp), bleibt es bei der Rueckfrage -- kein stillschweigender
        Default in keine Richtung."""
        frage = "Unsere Firma zahlt 2026 900 Euro an eine freie Grafikerin."
        fakten = Fakten(jahr=2026, auftragnehmer_typ=NP, positionen=[P(betrag=D("900"), rolle="honorar")])
        ergebnis = lauf_bestaetigt(FakeLLM(), frage, fakten)
        self.assertNotEqual(ergebnis.ergebnisklasse, NICHT_ABGABEPFLICHTIG)
        self.assertNotEqual(ergebnis.ergebnisklasse, ABGABEPFLICHTIG)
        self.assertEqual(ergebnis.ergebnisklasse, RUECKFRAGE_NOETIG)


class TestL1WaechterGegenDefaultImRouter(unittest.TestCase):
    """app/router.py::_rufe_kern_auf direkt aufgerufen (umgeht app/pflichtangaben.py) --
    auch hier darf ohne verwerterart nie ein Ergebnis 'Abgabepflichtig'/'Nicht abgabepflichtig'
    entstehen (Verteidigung in der Tiefe, Livetest-Befund L1, Punkt 3)."""

    def test_positionen_ohne_verwerterart_ist_rueckfrage(self):
        fakten = Fakten(jahr=2026, auftragnehmer_typ=NP, positionen=[P(betrag=D("900"), rolle="honorar")])
        kern_ergebnis = router._rufe_kern_auf(fakten)
        self.assertEqual(kern_ergebnis.klasse, RUECKFRAGE_NOETIG)

    def test_veranstaltungszahl_ohne_verwerterart_ist_rueckfrage(self):
        fakten = Fakten(
            jahr=2025, auftragnehmer_typ=NP, einnahmeabsicht=True,
            positionen=[P(betrag=D("2000"), rolle="honorar")], veranstaltungszahl=4,
        )
        kern_ergebnis = router._rufe_kern_auf(fakten)
        self.assertEqual(kern_ergebnis.klasse, RUECKFRAGE_NOETIG)

    def test_verwerterart_erscheint_in_der_faktenbestaetigung(self):
        fakten = Fakten(jahr=2026, verwerterart="typischer_verwerter", positionen=[P(betrag=D("900"))])
        liste = bestaetigung.als_liste(fakten)
        self.assertTrue(any("Typischer Verwerter" in z for z in liste))


# ==========================================================================================
# L2: Demo-Modus (FakeLLM) nutzt jetzt den Verlauf.
# ==========================================================================================
class TestL2VerlaufWirdGenutzt(unittest.TestCase):
    def test_dialog_rueckfrage_antwort_behaelt_jahr_und_betrag(self):
        llm = FakeLLM()
        erste_nachricht = "Eigenwerbung 2026, Grafikerin für Flyer, 1.200 €."
        erste = router.bearbeite_frage(erste_nachricht, llm)
        # Rechtsform fehlt noch -> Rueckfrage, kein Kernaufruf.
        self.assertEqual(erste.ergebnisklasse, RUECKFRAGE_NOETIG)

        zweite = router.bearbeite_frage("natürliche Person", llm, verlauf=[erste_nachricht])
        # Jahr und Betrag aus der ERSTEN Nachricht duerfen nicht verloren gehen: die zweite
        # Antwort muss jetzt zur Faktenbestaetigung (nicht zu einer neuen, inhaltsleeren
        # Rueckfrage nach Jahr/Betrag) fuehren.
        self.assertEqual(zweite.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG)
        zusammenfassung = " ".join(zweite.fakten_zusammenfassung)
        self.assertIn("1.200,00", zusammenfassung)
        self.assertIn("natürliche Person", zusammenfassung)


# ==========================================================================================
# L3: jede Rueckfrage-Schaltflaeche wird von der Heuristik erkannt.
# ==========================================================================================
class TestL3KnopfOptionenWerdenErkannt(unittest.TestCase):
    def test_alle_rechtsform_optionen_werden_erkannt(self):
        erwartet = dict(zip(pflichtangaben.RECHTSFORM_OPTIONEN, pflichtangaben._RECHTSFORM_TYPEN))
        for option_text, erwarteter_typ in erwartet.items():
            with self.subTest(option=option_text):
                fakten = FakeLLM().extrahiere_fakten(option_text)
                self.assertEqual(fakten.auftragnehmer_typ, erwarteter_typ)

    def test_einzelperson_einzelunternehmer_privatperson_werden_erkannt(self):
        for wort in ("Einzelperson", "Einzelunternehmer", "Privatperson"):
            with self.subTest(wort=wort):
                fakten = FakeLLM().extrahiere_fakten(wort)
                self.assertEqual(fakten.auftragnehmer_typ, "natuerliche_person")

    def test_alle_verwerterart_optionen_werden_erkannt(self):
        erwartet = dict(zip(pflichtangaben.VERWERTERART_OPTIONEN, pflichtangaben._VERWERTERART_TYPEN))
        for option_text, erwarteter_typ in erwartet.items():
            with self.subTest(option=option_text):
                fakten = FakeLLM().extrahiere_fakten(option_text)
                self.assertEqual(fakten.verwerterart, erwarteter_typ)

    def test_einnahmeabsicht_ja_nein_knoepfe_werden_erkannt(self):
        self.assertTrue(FakeLLM().extrahiere_fakten("ja").einnahmeabsicht)
        self.assertFalse(FakeLLM().extrahiere_fakten("nein").einnahmeabsicht)

    def test_jede_knopf_option_aus_echten_rueckfragen_wird_erkannt(self):
        """Baut echte Rueckfrage-Optionen (wie app/static/index.html sie anzeigt) aus
        app/pflichtangaben.py und prueft jede einzelne Schaltflaeche."""
        fehlend_rechtsform = pflichtangaben.fehlende_pflichtangaben(
            Fakten(jahr=2026, verwerterart="eigenwerber", positionen=[P(betrag=D("900"))])
        )
        optionen = pflichtangaben.rueckfrage_optionen(fehlend_rechtsform)
        self.assertTrue(optionen)
        for eintrag in optionen:
            for option_text in eintrag["optionen"]:
                with self.subTest(option=option_text):
                    fakten = FakeLLM().extrahiere_fakten(option_text)
                    self.assertIsNotNone(fakten.auftragnehmer_typ)


# ==========================================================================================
# L5: Darstellung -- Umlaute, keine doppelte Anzeige, keine internen Begriffe.
# ==========================================================================================
class TestL5Darstellung(unittest.TestCase):
    def test_ergebnisklassen_haben_echte_umlaute(self):
        self.assertEqual(FAKTEN_BESTAETIGUNG_NOETIG, "Faktenbestätigung nötig")
        self.assertEqual(PRUEFUNG_FEHLGESCHLAGEN, "Prüfung fehlgeschlagen")

    def test_rueckfragetexte_haben_echte_umlaute(self):
        self.assertIn("natürliche", pflichtangaben.FRAGE_AUFTRAGNEHMER)
        self.assertIn("ansässig", pflichtangaben.FRAGE_AUFTRAGNEHMER)
        self.assertNotIn("natuerliche", pflichtangaben.FRAGE_AUFTRAGNEHMER)
        self.assertNotIn("ansaessig", pflichtangaben.FRAGE_AUFTRAGNEHMER)
        rechtsform_frage = pflichtangaben._rechtsform_frage("Position 1")
        self.assertIn("natürliche", rechtsform_frage)
        self.assertIn("ansässig", rechtsform_frage)

    def test_faktenbestaetigung_zeigt_keine_interne_anfrageart(self):
        fakten = Fakten(anfrageart="bewertung", jahr=2025, positionen=[P(betrag=D("900"))])
        liste = bestaetigung.als_liste(fakten)
        self.assertFalse(any("Anfrageart" in z for z in liste))

    def test_faktenbestaetigung_uebersetzt_interne_rollen_codes(self):
        fakten = Fakten(
            jahr=2024,
            positionen=[
                P(betrag=D("1500"), rolle="honorar"),
                P(betrag=D("300"), rolle="fahrtkosten_nachgewiesen", nachgewiesen=True),
            ],
        )
        liste = bestaetigung.als_liste(fakten)
        text = " ".join(liste)
        self.assertNotIn("fahrtkosten_nachgewiesen", text)
        self.assertIn("nachgewiesene Fahrtkosten", text)
        self.assertIn("Honorar", text)


# ==========================================================================================
# L6: aehnlich geschriebene Fundstellen werden zusammengefasst (nicht nur textgleiche).
# ==========================================================================================
class TestL6FundstellenVereinheitlichung(unittest.TestCase):
    def test_satz_abkuerzung_und_aktuell_vermerk_gelten_als_dasselbe(self):
        fundstellen = [
            "KSVG § 24 Abs. 2 S. 2",
            "KSVG § 24 Abs. 2 Satz 2 (aktuell)",
            "KSVG § 27 Abs. 1",
        ]
        ergebnis = router._vereinheitliche_fundstellen(fundstellen)
        self.assertEqual(len(ergebnis), 2)
        self.assertIn("KSVG § 24 Abs. 2 S. 2", ergebnis)
        self.assertIn("KSVG § 27 Abs. 1", ergebnis)

    def test_echte_unterschiedliche_fundstellen_bleiben_getrennt(self):
        fundstellen = ["KSVG § 24 Abs. 1", "KSVG § 24 Abs. 2"]
        self.assertEqual(router._vereinheitliche_fundstellen(fundstellen), fundstellen)


if __name__ == "__main__":
    unittest.main(verbosity=2)
