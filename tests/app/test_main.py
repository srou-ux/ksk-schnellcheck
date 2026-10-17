"""Tests fuer app/main.py (FastAPI-Schnittstelle), offline mit FakeLLM/Demo-Modus.
Stellt sicher, dass MISTRAL_API_KEY nicht gesetzt ist, damit der Testlauf garantiert im
Demo-Modus bleibt (siehe PROMPT_ClaudeCode_Chatbot_1.md: 'Alle Tests laufen offline')."""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

os.environ.pop("MISTRAL_API_KEY", None)

from fastapi.testclient import TestClient

from app.ergebnisklassen import FAKTEN_BESTAETIGUNG_NOETIG, RUECKFRAGE_NOETIG
from app.main import app

client = TestClient(app)


class TestGesundheit(unittest.TestCase):
    def test_gesundheit_meldet_demo_modus(self):
        antwort = client.get("/gesundheit")
        self.assertEqual(antwort.status_code, 200)
        daten = antwort.json()
        self.assertTrue(daten["demo_modus"])
        self.assertIn("FakeLLM", daten["modell"])


class TestWeboberflaeche(unittest.TestCase):
    def test_startseite_liefert_html_ohne_externe_skripte(self):
        antwort = client.get("/")
        self.assertEqual(antwort.status_code, 200)
        self.assertIn("text/html", antwort.headers["content-type"])
        text = antwort.text
        self.assertNotIn("<script src=", text)
        self.assertNotIn("http://", text)
        self.assertNotIn("https://", text)
        self.assertIn("Entwurf", text)


class TestFrageEndpunkt(unittest.TestCase):
    def test_frage_ohne_jahr_liefert_rueckfrage(self):
        antwort = client.post("/frage", json={"frage": "Ist das abgabepflichtig?"})
        self.assertEqual(antwort.status_code, 200)
        daten = antwort.json()
        self.assertEqual(daten["ergebnisklasse"], RUECKFRAGE_NOETIG)
        self.assertTrue(daten["rueckfragen"])
        self.assertTrue(daten["demo_modus"])

    def test_frage_antwort_enthaelt_schlusssatz(self):
        antwort = client.post("/frage", json={"frage": "Eine völlig unklare Frage ohne Jahr."})
        daten = antwort.json()
        self.assertIn("Entwurf", daten["antwort"])


class TestBestaetigungsFluss(unittest.TestCase):
    """Seit Chatbot Teil 1d braucht jede berechnungsbeduerftige Anfrage zuerst eine
    Faktenbestaetigung (POST /bestaetigen) -- nur die Heuristik-Extraktion (Demo-Modus) kann
    hier offline alle Pflichtangaben liefern."""

    # Livetest-Befund L1: verwerterart ist jetzt Pflichtangabe -- "Eigenwerbung" muss die
    # Frage selbst nennen, sonst fragt die Heuristik (wie ein echtes Modell) gezielt danach.
    FRAGE = "Eigenwerbung: 2024, freiberuflicher Webdesigner erstellt ein Logo für 900 €."

    def test_frage_mit_vollstaendigen_angaben_verlangt_bestaetigung(self):
        antwort = client.post("/frage", json={"frage": self.FRAGE})
        daten = antwort.json()
        self.assertEqual(daten["ergebnisklasse"], FAKTEN_BESTAETIGUNG_NOETIG)
        self.assertTrue(daten["sitzungskennung"])
        self.assertTrue(daten["fakten_hash"])
        self.assertTrue(daten["fakten_zusammenfassung"])
        self.assertEqual(daten["kern_protokoll"], {})

    def test_bestaetigen_mit_korrektem_hash_liefert_endergebnis(self):
        erste = client.post("/frage", json={"frage": self.FRAGE}).json()
        zweite = client.post(
            "/bestaetigen",
            json={"sitzungskennung": erste["sitzungskennung"], "fakten_hash": erste["fakten_hash"]},
        )
        daten = zweite.json()
        self.assertNotEqual(daten["ergebnisklasse"], FAKTEN_BESTAETIGUNG_NOETIG)
        self.assertTrue(daten["kern_protokoll"])

    def test_bestaetigen_mit_falschem_hash_liefert_rueckfrage(self):
        erste = client.post("/frage", json={"frage": self.FRAGE}).json()
        zweite = client.post(
            "/bestaetigen",
            json={"sitzungskennung": erste["sitzungskennung"], "fakten_hash": "falscher-hash"},
        )
        daten = zweite.json()
        self.assertEqual(daten["ergebnisklasse"], RUECKFRAGE_NOETIG)

    def test_korrektur_per_erneutem_post_frage_macht_alte_bestaetigung_ungueltig(self):
        erste = client.post("/frage", json={"frage": self.FRAGE}).json()
        korrigiert = client.post(
            "/frage",
            json={"frage": "Eigenwerbung: 2024, freiberuflicher Webdesigner erstellt ein Logo für 950 €.", "sitzungskennung": erste["sitzungskennung"]},
        ).json()
        self.assertNotEqual(korrigiert["fakten_hash"], erste["fakten_hash"])
        # Die ALTE Bestaetigung (fuer 900 €) passt jetzt nicht mehr zu den neuen Fakten (950 €).
        zweite = client.post(
            "/bestaetigen",
            json={"sitzungskennung": erste["sitzungskennung"], "fakten_hash": erste["fakten_hash"]},
        ).json()
        self.assertEqual(zweite["ergebnisklasse"], RUECKFRAGE_NOETIG)


class TestKnopfEndpunkt(unittest.TestCase):
    """Pruefkatalog-Befund M1: POST /knopf beantwortet eine geschlossene Rueckfrage-
    Schaltflaeche deterministisch, ohne erneuten Modellaufruf."""

    def test_frage_rueckfrage_knopf_faktenbestaetigung(self):
        erste = client.post(
            "/frage", json={"frage": "2024, freiberuflicher Webdesigner erstellt ein Logo für 900 €."}
        ).json()
        self.assertEqual(erste["ergebnisklasse"], RUECKFRAGE_NOETIG)
        self.assertTrue(erste["sitzungskennung"])
        # Schritt 2 (17.10.2026): der Knopf fragt nach dem Zweck (Tatsache), nicht nach der Rechtskategorie.
        eintrag = next(o for o in erste["rueckfrage_optionen"] if o["feld"] == "auftragszweck")
        wert = eintrag["werte"]["Werbung für mein eigenes Unternehmen"]

        zweite = client.post(
            "/knopf",
            json={"sitzungskennung": erste["sitzungskennung"], "feld": "auftragszweck", "wert": wert},
        )
        self.assertEqual(zweite.status_code, 200)
        daten = zweite.json()
        self.assertEqual(daten["ergebnisklasse"], FAKTEN_BESTAETIGUNG_NOETIG)
        self.assertEqual(daten["sitzungskennung"], erste["sitzungskennung"])
        self.assertTrue(any("Eigenwerbung" in z for z in daten["fakten_zusammenfassung"]))

    def test_ungueltige_eingaben_ohne_serverfehler(self):
        """Schritt 2: ungültige Eingaben an POST /knopf führen nie zu einem Serverfehler (500)."""
        erste = client.post(
            "/frage", json={"frage": "2024, freiberuflicher Webdesigner erstellt ein Logo für 900 €."}
        ).json()
        sk = erste["sitzungskennung"]
        for eingabe in ({"sitzungskennung": sk, "feld": "katalog_taetigkeit", "wert": True},
                        {"sitzungskennung": sk, "feld": "herkunft", "wert": {"x": 1}},
                        {"sitzungskennung": sk, "feld": "auftragszweck", "wert": {"a": [1, 2]}},
                        {"sitzungskennung": sk, "feld": "auftragnehmer_typ", "wert": "GbR", "position": -1},
                        {"sitzungskennung": sk, "feld": "auftragnehmer_typ", "wert": "GbR", "position": 10 ** 9},
                        {"sitzungskennung": sk, "feld": "jahr", "wert": "zweitausend"},
                        {"sitzungskennung": sk, "feld": "auftragszweck", "wert": None},
                        {"sitzungskennung": sk, "feld": "auftragszweck", "wert": "x", "position": "abc"},
                        {"sitzungskennung": sk},
                        {}):
            with self.subTest(eingabe=eingabe):
                antwort = client.post("/knopf", json=eingabe)
                self.assertIn(antwort.status_code, (200, 422), antwort.text)
                if antwort.status_code == 200:
                    self.assertEqual(antwort.json()["ergebnisklasse"], RUECKFRAGE_NOETIG)

    def test_knopf_zu_unbekannter_sitzung_liefert_rueckfrage_statt_fehler(self):
        antwort = client.post(
            "/knopf", json={"sitzungskennung": "unbekannt", "feld": "verwerterart", "wert": "eigenwerber"}
        )
        self.assertEqual(antwort.status_code, 200)
        self.assertEqual(antwort.json()["ergebnisklasse"], RUECKFRAGE_NOETIG)


if __name__ == "__main__":
    unittest.main(verbosity=2)
