"""Sprachmodell-Auswahl. Entscheidung des Nutzers am 17.10.2026: der KSK-Chat arbeitet NUR mit Mistral (EU), Standardmodell
Mistral Small (`app/llm/anbieter.json`, Feld `mistral_modell`; überschreibbar mit MISTRAL_MODELL). Die früheren Anschlüsse
für andere Anbieter (OpenAI-kompatibel, Anthropic) sind entfernt; sie stehen in der Git-Geschichte (bis Commit 7777681).

Ohne Sprachmodell läuft der Demo-Modus (`app/llm/fake.py`): feste Regelerkennung, kein KI-Anbieter. Er bleibt für alle
automatischen Tests und als Notbetrieb, wenn Mistral nicht erreichbar ist.

| Variable | Bedeutung |
|---|---|
| MISTRAL_API_KEY | Schlüssel (nur als Umgebungsvariable oder GitHub-/Codespaces-Secret, nie im Repo) |
| MISTRAL_MODELL | optional, anderes Mistral-Modell (Standard aus anbieter.json) |
| LLM_ANBIETER | optional: `mistral` (Standard, wenn ein Schlüssel gesetzt ist) oder `demo` (ohne Sprachmodell) |
"""
from __future__ import annotations

import os

from app.llm.base import LLM


class EinstellungFehlt(RuntimeError):
    """Die Einstellungen reichen nicht (ohne Raten: lieber nicht starten)."""


def _env(name: str) -> str | None:
    wert = os.environ.get(name)
    return wert if wert not in (None, "") else None


def waehle_llm() -> LLM:
    """Mistral, wenn MISTRAL_API_KEY gesetzt ist (oder LLM_ANBIETER=mistral), sonst der Demo-Modus."""
    from app.llm.fake import FakeLLM

    anbieter = (_env("LLM_ANBIETER") or ("mistral" if _env("MISTRAL_API_KEY") else "demo")).strip().lower()
    if anbieter == "demo":
        return FakeLLM()
    if anbieter == "mistral":
        from app.llm.mistral import MistralLLM

        if not _env("MISTRAL_API_KEY"):
            raise EinstellungFehlt("MISTRAL_API_KEY fehlt (für den Betrieb ohne Sprachmodell: LLM_ANBIETER=demo).")
        return MistralLLM()
    raise EinstellungFehlt(f"Unbekannter LLM_ANBIETER '{anbieter}' (nur mistral oder demo).")
