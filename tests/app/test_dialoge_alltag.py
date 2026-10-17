"""Alltags-Dialoge AT-2026-046 bis 050 (Nutzer, 14.10.2026; Status ENTWURF), offline wie die Oberfläche.

Dialoge: aufgaben/audit/dialoge_alltag/*.json (auch live im Gesamtlauf über tests/archiv/dialoge_soll.json).
Modell: Demo-Modus; bei AT-050 ist die erste Antwort nachgebildet, weil der Demo-Modus nur einfache Grüße
als Begrüßung erkennt (im Live-Betrieb setzt das Modell die Anfrageart 'hinweis')."""
from __future__ import annotations

import unittest
from decimal import Decimal as D

from app.llm.fake import FakeLLM
from app.schema import Fakten
from tests.app.test_dialoge_fehlerquellen import Oberflaeche, spiele  # noqa: F401

import json
from pathlib import Path

ORDNER = Path(__file__).resolve().parents[2] / "aufgaben" / "audit" / "dialoge_alltag"


def spiele_alltag(name: str, llm=None) -> list:
    ui = Oberflaeche(llm or FakeLLM())
    antworten = []
    for schritt in json.loads((ORDNER / f"{name}.json").read_text(encoding="utf-8")):
        if "text" in schritt:
            antworten.append(ui.tippe(schritt["text"]))
        elif "knopf" in schritt:
            antworten.append(ui.knopf(*schritt["knopf"]))
        else:
            antworten.append(ui.bestaetige())
    return antworten


class DialogeAlltag(unittest.TestCase):
    def test_at_046_warum_ergebnis_bleibt(self):
        a = spiele_alltag("at046")
        self.assertEqual(a[2].kern_protokoll.get("abgabe"), D("98.00"))
        self.assertEqual(a[2].ergebnisklasse, "Abgabepflichtig (Vorschlag)")

    def test_at_047_wo_steht_das(self):
        a = spiele_alltag("at047")
        self.assertEqual(a[2].kern_protokoll.get("abgabe"), D("98.00"))
        self.assertIn("KSVG § 24", a[2].antwort)  # Fundstelle aus dem System

    def test_at_048_korrektur_des_betrags(self):
        a = spiele_alltag("at048")
        self.assertIn("1.600,00 €", " ; ".join(a[1].fakten_zusammenfassung))
        self.assertNotIn("2.000,00 €", " ; ".join(a[1].fakten_zusammenfassung))
        self.assertEqual(a[2].kern_protokoll.get("abgabe"), D("78.40"))

    def test_at_049_neue_frage(self):
        a = spiele_alltag("at049")
        self.assertEqual(a[3].kern_protokoll.get("bemessungsgrundlage"), D("3000"))
        self.assertEqual(a[3].kern_protokoll.get("abgabe"), D("147.00"))

    def test_at_050_begruessung_dann_fall(self):
        frage = "Guten Tag! Wie funktioniert das hier?"
        llm = FakeLLM()
        llm.registriere(frage, Fakten(anfrageart="hinweis"))  # so wie das Modell live antwortet
        a = spiele_alltag("at050", llm)
        self.assertEqual(a[0].ergebnisklasse, "Hinweis")
        self.assertEqual(a[2].kern_protokoll.get("abgabe"), D("98.00"))
        self.assertNotIn("Guten Tag", " ; ".join(a[1].fakten_zusammenfassung))


class KorrekturErsetzt(unittest.TestCase):
    def test_nur_mit_korrekturwort_und_genau_passenden_betraegen(self):
        from app.fallstand import _ersetzter_betrag
        alt = [{"betrag": D("2000"), "bezeichnung": "Jingle"}]
        neu = [{"betrag": D("2000")}, {"betrag": D("1600")}]
        self.assertEqual(len(_ersetzter_betrag(alt, neu, "Sorry, es waren doch nur 1.600 EUR.")), 1)
        # ohne Korrekturwort: eine zweite Rechnung bleibt eine zweite Rechnung
        self.assertEqual(len(_ersetzter_betrag(alt, neu, "Dazu kommen 1.600 EUR.")), 2)


if __name__ == "__main__":
    unittest.main()
