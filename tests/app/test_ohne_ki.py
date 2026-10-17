"""Wächter „ohne KI“ (17.10.2026): kein Sprachmodell, kein Netzzugriff, kein Mistral – in App, Kern, Gegenrechnung
und Schnellcheck. Läuft ohne fastapi."""
from __future__ import annotations

import ast
import json
import pathlib
import unittest

W = pathlib.Path(__file__).resolve().parents[2]
ORDNER = ("app", "kern", "verifier", "schnellcheck")
VERBOTENE_MODULE = {"httpx", "requests", "urllib", "http.client", "socket", "aiohttp", "openai", "anthropic", "mistralai"}
VERBOTENE_WOERTER = ("mistral", "api_key", "llm_anbieter")


def py_dateien():
    for o in ORDNER:
        yield from (W / o).rglob("*.py")


class OhneKi(unittest.TestCase):
    def test_keine_ki_und_keine_netzmodule(self):
        for p in py_dateien():
            for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
                namen = []
                if isinstance(n, ast.Import):
                    namen = [a.name for a in n.names]
                elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
                    namen = [n.module]
                for m in namen:
                    with self.subTest(datei=str(p.relative_to(W)), modul=m):
                        self.assertFalse(any(m == v or m.startswith(v + ".") for v in VERBOTENE_MODULE))
                        self.assertFalse(m.startswith(("app.llm", "app.rag", "app.router")))

    def test_kein_mistral_in_konfiguration_oberflaeche_und_start(self):
        # Nur ausführbare Teile: Konfiguration, Oberflächen, Workflows, Abhängigkeiten, Startskripte. Kommentare im
        # Code dürfen frühere Testläufe mit Mistral als Herkunft einer Regel nennen (Nachweis, nicht löschen).
        dateien = [W / "app/dokument_config.json", W / "app/konfiguration.json", *(W / "app").rglob("*.html"),
                   *(W / "schnellcheck").rglob("*.html"), *(W / ".github").rglob("*.yml"),
                   *W.glob("**/requirements*.txt"), *(W / "scripts").glob("start_*")]
        for p in dateien:
            text = p.read_text(encoding="utf-8").lower()
            for wort in VERBOTENE_WOERTER:
                with self.subTest(datei=str(p.relative_to(W)), wort=wort):
                    self.assertNotIn(wort, text)

    def test_sprachmodell_schicht_entfernt(self):
        for weg in ("app/llm", "app/rag", "app/router.py", "app/dokument_ki.py"):
            self.assertFalse((W / weg).exists(), weg)
        konfig = json.loads((W / "app/dokument_config.json").read_text(encoding="utf-8"))
        self.assertFalse(any(k.startswith("ki") or "ki_" in k for k in konfig))


if __name__ == "__main__":
    unittest.main()
