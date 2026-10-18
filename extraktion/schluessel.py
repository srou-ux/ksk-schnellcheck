"""Schlüssel nur aus der Umgebung oder aus config/secrets.env. Nie ausgeben, nie ins Repo."""
from __future__ import annotations

import os
from pathlib import Path

_DATEI = Path(__file__).resolve().parents[1] / "config" / "secrets.env"
_PLATZHALTER = ("hier-den", "einsetzen")


def schluessel() -> str | None:
    wert = _sauber(os.environ.get("MISTRAL_API_KEY", ""))
    if wert:
        return wert
    if not _DATEI.exists():
        return None
    for zeile in _DATEI.read_text(encoding="utf-8").splitlines():
        text = zeile.strip()
        if not text.startswith("MISTRAL_API_KEY="):
            continue
        return _sauber(text.split("=", 1)[1])
    return None


def _sauber(wert: str) -> str | None:
    wert = wert.strip().strip('"').strip("'")
    if not wert or any(teil in wert for teil in _PLATZHALTER):
        return None
    return wert
