"""13.10.2026, Live-Lauf P-16: das Modell schrieb 'veranstaltungzahl' statt 'veranstaltungszahl'.
Ein Tippfehler im SCHLÜSSEL (genau ein Zeichen, eindeutig) wird umbenannt; fremde Schlüssel bleiben
ein Fehler (Schutz gegen Formatvorgaben aus dem Nutzertext). Offline, ohne Netz."""
from __future__ import annotations

import json
import unittest

from app.llm.base import LLMFehlgeschlagen
from app.llm.mistral import MistralLLM, _tippfehler_schluessel
from app.schema import Fakten

ERLAUBT = set(Fakten.model_fields)


class Tippfehler(unittest.TestCase):
    def test_ein_fehlender_buchstabe_wird_umbenannt(self):
        erg = _tippfehler_schluessel({"veranstaltungzahl": 4, "jahr": 2026}, ERLAUBT)
        self.assertEqual(erg, {"veranstaltungszahl": 4, "jahr": 2026})

    def test_satzzeichen_am_rand_des_schluessels(self):
        # HT-2026-008 (live 15.10.2026): "freitext_rest': " -- nur Anführungszeichen/Doppelpunkt/Leerraum am Rand.
        erg = _tippfehler_schluessel({"freitext_rest': ": "x", "jahr": 2026}, ERLAUBT)
        self.assertEqual(erg, {"freitext_rest": "x", "jahr": 2026})
        # ein schon gesetztes Feld wird nie überschrieben
        erg = _tippfehler_schluessel({"jahr': ": 2000, "jahr": 2026}, ERLAUBT)
        self.assertEqual(erg["jahr"], 2026)

    def test_fremder_schluessel_bleibt_fremd(self):
        erg = _tippfehler_schluessel({"anzahl_rechnungen": 2, "summe_netto": 5}, ERLAUBT)
        self.assertIn("summe_netto", erg)
        self.assertNotIn("summe_netto", ERLAUBT)

    def test_kein_ueberschreiben_eines_vorhandenen_feldes(self):
        erg = _tippfehler_schluessel({"veranstaltungzahl": 4, "veranstaltungszahl": 2}, ERLAUBT)
        self.assertEqual(erg["veranstaltungszahl"], 2)
        self.assertIn("veranstaltungzahl", erg)  # bleibt fremd -> Fehler wie bisher

    def test_kurze_schluessel_werden_nie_geraten(self):
        self.assertEqual(_tippfehler_schluessel({"jahre": 2026}, ERLAUBT), {"jahre": 2026})

    def test_extraktion_mit_tippfehler_liefert_die_fakten(self):
        llm = MistralLLM.__new__(MistralLLM)
        antworten = [json.dumps({"anfrageart": "bewertung", "jahr": 2026, "veranstaltungzahl": 4})]
        llm._aufruf = lambda system, text, json_objekt=False, schema=None: antworten[0]
        f = llm.extrahiere_fakten("Unser Verein hatte 2026 vier Konzerte.")
        self.assertEqual(f.veranstaltungszahl, 4)

    def test_extraktion_mit_fremdem_schluessel_bleibt_fehler(self):
        llm = MistralLLM.__new__(MistralLLM)
        llm._aufruf = lambda system, text, json_objekt=False, schema=None: json.dumps({"jahr": 2026, "summe_netto": 5})
        with self.assertRaises(LLMFehlgeschlagen):
            llm.extrahiere_fakten("2026")


if __name__ == "__main__":
    unittest.main(verbosity=2)
