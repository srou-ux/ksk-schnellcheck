"""Optionaler Rauchtest fuer den echten Mistral-(EU)-Adapter. Wird OHNE MISTRAL_API_KEY
automatisch uebersprungen (siehe PROMPT_ClaudeCode_Chatbot_1.md: 'ein echter Mistral-Aufruf
nur im optionalen Rauchtest, der ohne Schluessel uebersprungen wird'). Macht einen echten
Netzwerkaufruf -- bewusst NICHT Teil des offline laufenden Standard-Testlaufs.

TestMistralPromptOffline (unten) laeuft dagegen immer mit: sie prueft nur den
Prompt-Aufbau (app/llm/mistral.py::beschreibe_fall/_platzhalter_beschreibung) ohne
Netzwerkaufruf (`_aufruf` wird durch einen Fake ersetzt) -- insbesondere, dass das Modell
NIE die tatsaechlichen Werte zu sehen bekommt (Teil 1d, Platzhalter-Architektur; seit Teil
1g gilt das fuer `beschreibe_fall`, den einzigen noch vom Modell geschriebenen Text)."""
import os
import sys
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.llm.base import AntwortKontext
from app.schema import Fakten


@unittest.skipUnless(os.environ.get("MISTRAL_API_KEY"), "MISTRAL_API_KEY nicht gesetzt -- Demo-Modus, Test übersprungen")
class TestMistralRauchtest(unittest.TestCase):
    def test_extrahiere_fakten_echter_aufruf(self):
        from app.llm.mistral import MistralLLM

        llm = MistralLLM()
        fakten = llm.extrahiere_fakten("Im Jahr 2025 hat eine GmbH einem Grafiker 900 Euro gezahlt.")
        self.assertIsInstance(fakten, Fakten)
        self.assertEqual(fakten.jahr, 2025)


class TestMistralPromptOffline(unittest.TestCase):
    """Laeuft immer (kein Netzwerk, kein Schluessel noetig): `_aufruf` wird gefaked, um nur
    den an das Modell gesendeten Prompt zu pruefen."""

    def _llm(self):
        from app.llm.mistral import MistralLLM

        return MistralLLM(api_key="offline-test-schluessel")

    def test_platzhalter_beschreibung_fuer_bekannten_namen(self):
        from app.llm.mistral import _platzhalter_beschreibung

        self.assertIn("Kalenderjahr", _platzhalter_beschreibung("JAHR"))

    def test_platzhalter_beschreibung_fuer_durchnummerierten_namen(self):
        from app.llm.mistral import _platzhalter_beschreibung

        self.assertEqual(_platzhalter_beschreibung("FUNDSTELLE_3"), _platzhalter_beschreibung("FUNDSTELLE_1"))
        self.assertIn("Fundstelle", _platzhalter_beschreibung("FUNDSTELLE_3"))

    def test_platzhalter_beschreibung_fuer_unbekannten_namen(self):
        from app.llm.mistral import _platzhalter_beschreibung

        self.assertEqual(_platzhalter_beschreibung("UNBEKANNT"), "(ohne Beschreibung)")

    def test_modell_bekommt_nie_die_tatsaechlichen_werte(self):
        llm = self._llm()
        kontext = AntwortKontext(
            frage="2025, 900 € Honorar.", fakten=Fakten(jahr=2025), ergebnisklasse="Abgabepflichtig (Vorschlag)",
            kern_protokoll={"bemessungsgrundlage": Decimal("900"), "abgabe": Decimal("45.00")},
        )
        gesendet = {}

        def fake_aufruf(system, user, max_tokens=None):
            gesendet["system"] = system
            gesendet["user"] = user
            return "{JAHR}"

        with patch.object(llm, "_aufruf", fake_aufruf):
            llm.beschreibe_fall(kontext)

        self.assertNotIn("900", gesendet["user"])
        self.assertNotIn("45,00", gesendet["user"])
        self.assertNotIn("45.00", gesendet["user"])
        self.assertIn("BEMESSUNGSGRUNDLAGE", gesendet["user"])
        self.assertIn("ABGABE", gesendet["user"])

    def test_systemprompt_verbietet_schlusssatz_und_ergebnisaussage(self):
        llm = self._llm()
        kontext = AntwortKontext(frage="f", fakten=Fakten(jahr=2025), ergebnisklasse="x")
        gesendet = {}

        def fake_aufruf(system, user, max_tokens=None):
            gesendet["system"] = system
            return "{JAHR}"

        with patch.object(llm, "_aufruf", fake_aufruf):
            llm.beschreibe_fall(kontext)

        self.assertIn("Schlusssatz", gesendet["system"])
        self.assertIn("abgabepflichtig", gesendet["system"])


class TestMistralResponseFormat(unittest.TestCase):
    """Pruefkatalog-Befund M2 (aufgaben/PROMPT_ClaudeCode_Chatbot_Pruefkatalog1_Befunde.md),
    zweiter Teil: `response_format: json_object` zusaetzlich zur Codeblock-Entfernung
    (Mistral-API-Doku) -- das Entfernen eines Markdown-Codeblocks selbst ist in
    tests/app/test_mistral_codeblock.py getestet (app/llm/mistral.py::_json_aus_antwort)."""

    def _llm(self):
        from app.llm.mistral import MistralLLM

        return MistralLLM(api_key="offline-test-schluessel")

    def test_extrahiere_fakten_verlangt_response_format_json_object(self):
        llm = self._llm()
        gesendet = {}

        def fake_aufruf(system, user, max_tokens=None, json_objekt=False):
            gesendet["json_objekt"] = json_objekt
            return "{}"

        with patch.object(llm, "_aufruf", fake_aufruf):
            llm.extrahiere_fakten("Frage")

        self.assertTrue(gesendet["json_objekt"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
