"""Vollversion „Rechnungen prüfen“ ohne KI (17.10.2026): app/main.py startet nur noch den Dokumentenbereich.
Kein Netz, erfundene Daten."""
from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class OberflaecheOhneKi(unittest.TestCase):
    def test_startseite_ist_rechnungen_pruefen(self):
        r = client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn('id="bereiche"', r.text)
        self.assertIn('aria-current="page">Rechnungen prüfen</a>', r.text)
        for wort in ("KSK-Chat", "Mistral", "KI-Unterstützung"):
            self.assertNotIn(wort, r.text)

    def test_optionen_ohne_ki_mit_schutzkoepfen(self):
        r = client.get("/dokumente/optionen")
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("ki_verfuegbar", r.json())
        self.assertEqual(r.headers.get("Cache-Control"), "no-store")
        self.assertIn("frame-ancestors 'none'", r.headers.get("Content-Security-Policy", ""))

    def test_lesen_nur_mit_regel_erkennung(self):
        r = client.post("/dokumente/lesen?endung=.csv", content="Bezeichnung;Betrag\nLogo;1500,00".encode())
        self.assertEqual(r.status_code, 200, r.text)
        d = r.json()
        self.assertEqual(d["pruefung"], ["regeln"])
        self.assertNotIn("ki", d)
        self.assertNotIn("pruefung", d["positionen"][0])
        # Ein früherer KI-Schalter in der Adresse ändert nichts.
        self.assertEqual(client.post("/dokumente/lesen?endung=.csv&ki=1",
                                     content="Bezeichnung;Betrag\nLogo;1500,00".encode()).json()["pruefung"], ["regeln"])

    def test_kein_chat_mehr(self):
        self.assertEqual(client.post("/frage", json={"frage": "Hallo"}).status_code, 404)
        self.assertFalse(client.get("/gesundheit").json()["llm"])


if __name__ == "__main__":
    unittest.main()
