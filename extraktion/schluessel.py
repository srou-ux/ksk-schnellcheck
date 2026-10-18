"""Schlüssel nur aus der Umgebung, sonst aus config/secrets.env.

Reihenfolge: Umgebungsvariable MISTRAL_API_KEY, und nur wenn sie fehlt die Datei.
Die Datei überschreibt eine gesetzte Variable nicht und wird nicht in die Umgebung kopiert.
Der Wert wird nie geloggt, nie gedruckt und nie committet.
"""
from __future__ import annotations

import os
from pathlib import Path

_DATEI = Path(__file__).resolve().parents[1] / "config" / "secrets.env"
_PLATZHALTER = ("hier-den", "einsetzen")


def schluessel() -> str | None:
    wert = _sauber(os.environ.get("MISTRAL_API_KEY", ""))
    if wert:
        return wert
    return _aus_datei()


def ablage() -> dict:
    """Form der Ablage, ohne den Schlüsselwert. Längen beider Quellen, nie die Werte."""
    roh = _DATEI.read_bytes() if _DATEI.exists() else b""
    datei_wert = _aus_datei()
    umgebung = _sauber(os.environ.get("MISTRAL_API_KEY", ""))
    wert = umgebung or datei_wert
    return {
        "quelle": "umgebung" if umgebung else ("datei" if datei_wert else "keine"),
        "pfad": str(_DATEI),
        "datei_vorhanden": _DATEI.exists(),
        "bom": roh.startswith(b"\xef\xbb\xbf"),
        "gleich_ohne_leerzeichen": _gleich_ohne_leerzeichen(),
        "innen_whitespace": bool(wert and any(zeichen.isspace() for zeichen in wert)),
        "platzhalter": False if wert else True,
        "laenge": len(wert or ""),
        "laenge_umgebung": len(umgebung or ""),
        "laenge_datei": len(datei_wert or ""),
    }


def _gleich_ohne_leerzeichen() -> bool:
    if not _DATEI.exists():
        return False
    for zeile in _DATEI.read_text(encoding="utf-8-sig").splitlines():
        text = zeile.strip()
        if text.startswith("MISTRAL_API_KEY"):
            return text.startswith("MISTRAL_API_KEY=")
    return False


def _aus_datei() -> str | None:
    if not _DATEI.exists():
        return None
    text = _DATEI.read_text(encoding="utf-8-sig")
    for zeile in text.splitlines():
        text_zeile = zeile.strip()
        if not text_zeile.startswith("MISTRAL_API_KEY="):
            continue
        return _sauber(text_zeile.split("=", 1)[1])
    return None


def _sauber(wert: str) -> str | None:
    wert = wert.strip().strip('"').strip("'")
    if not wert or any(teil in wert for teil in _PLATZHALTER):
        return None
    return wert
