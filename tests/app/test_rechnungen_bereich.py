"""Gemeinsame Oberfläche (17.10.2026): „KSK-Chat“ (/) und „Rechnungen prüfen“ (/rechnungen) in einer App
(app/main.py hängt app/dokument_app.py ein). Demo-Modus, kein Netz, erfundene Daten."""
from __future__ import annotations

import os
import unittest

os.environ.pop("MISTRAL_API_KEY", None)
os.environ["LLM_ANBIETER"] = "demo"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


class GemeinsameOberflaeche(unittest.TestCase):
    def test_beide_bereiche_mit_menue(self):
        for pfad, aktiv in (("/", "KSK-Chat"), ("/rechnungen", "Rechnungen prüfen")):
            with self.subTest(pfad=pfad):
                r = client.get(pfad)
                self.assertEqual(r.status_code, 200)
                self.assertIn('id="bereiche"', r.text)
                self.assertIn(f'aria-current="page">{aktiv}</a>', r.text)

    def test_dokumentenbereich_mit_schutzkoepfen_und_ohne_ki_im_demo_modus(self):
        r = client.get("/dokumente/optionen")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["ki_verfuegbar"])
        self.assertEqual(r.headers.get("Cache-Control"), "no-store")
        self.assertIn("frame-ancestors 'none'", r.headers.get("Content-Security-Policy", ""))

    def test_lesen_liefert_pruefung_getrennt_von_den_positionen(self):
        r = client.post("/dokumente/lesen?endung=.csv", content="Bezeichnung;Betrag\nLogo;1500,00".encode())
        self.assertEqual(r.status_code, 200, r.text)
        d = r.json()
        self.assertEqual(d["pruefung"], ["regeln"])
        self.assertEqual(d["ki"], "nicht verwendet")
        self.assertNotIn("pruefung", d["positionen"][0])

    def test_chat_laeuft_weiter(self):
        self.assertEqual(client.get("/gesundheit").json()["status"], "ok")


if __name__ == "__main__":
    unittest.main()
