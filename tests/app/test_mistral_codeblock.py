"""Prüfkatalog-Befund M2: Mistral Large liefert das Fakten-JSON in einem Markdown-Codeblock.
Offline: der Netzaufruf `_aufruf` wird durch eine feste Rohantwort ersetzt, es wird nie gesendet."""
from __future__ import annotations

import unittest

from app.llm.base import LLMFehlgeschlagen
from app.llm.mistral import MistralLLM, _json_aus_antwort


def _llm_mit_antwort(roh: str) -> MistralLLM:
    llm = MistralLLM(api_key="nur-test-ohne-netz")
    llm._aufruf = lambda system, user, max_tokens=None, json_objekt=False, schema=None: roh  # type: ignore[method-assign]
    return llm


class TestJsonAusAntwort(unittest.TestCase):
    def test_codeblock_mit_json_kennung(self):
        roh = '```json\n{\n  "jahr": 2025\n}\n```'
        self.assertEqual(_llm_mit_antwort(roh).extrahiere_fakten("2025").jahr, 2025)

    def test_codeblock_ohne_kennung(self):
        roh = '```\n{"jahr": 2026}\n```'
        self.assertEqual(_llm_mit_antwort(roh).extrahiere_fakten("2026").jahr, 2026)

    def test_satz_vor_und_nach_dem_json(self):
        roh = 'Hier die Fakten:\n{"jahr": 2024}\nIch hoffe, das hilft.'
        self.assertEqual(_llm_mit_antwort(roh).extrahiere_fakten("2024").jahr, 2024)

    def test_reines_json_unveraendert(self):
        self.assertEqual(_json_aus_antwort('{"jahr": 2025}'), '{"jahr": 2025}')

    def test_kein_json_bleibt_fehler(self):
        with self.assertRaises(LLMFehlgeschlagen):
            _llm_mit_antwort("Das kann ich nicht beantworten.").extrahiere_fakten("x")

    def test_codeblock_mit_falschem_typ_bleibt_fehler(self):
        """Die Verpackung wird entfernt, der Inhalt aber weiter gegen das Schema geprüft."""
        roh = '```json\n{"jahr": "zweitausendfuenfundzwanzig"}\n```'
        with self.assertRaises(LLMFehlgeschlagen):
            _llm_mit_antwort(roh).extrahiere_fakten("2025")

    def test_kaputtes_json_im_codeblock_bleibt_fehler(self):
        with self.assertRaises(LLMFehlgeschlagen):
            _llm_mit_antwort('```json\n{"jahr": 2025,\n```').extrahiere_fakten("2025")


if __name__ == "__main__":
    unittest.main()
