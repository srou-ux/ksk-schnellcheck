"""Mehrere Belege in einem Text werden vor dem Lesen getrennt.

Eine Soll-Bewertung im selben Text ist keine Rechnung und wird nicht mitgelesen.
"""
from __future__ import annotations

import re

_FALL = re.compile(r"(?m)^#{0,3}\s*Fall\s+[A-Z]?\d+\b")
_STELLER = re.compile(r"(?m)^#{0,3}\s*Rechnungsteller\s*:")
_SOLL = re.compile(r"(?m)^#{0,3}\s*Soll-Bewertung\b")


def trenne(text: str) -> list[str]:
    """Ein Beleg bleibt ein Beleg. Mehrere Fall- oder Rechnungsköpfe werden getrennt."""
    grenzen = list(_FALL.finditer(text or ""))
    if len(grenzen) < 2:
        grenzen = list(_STELLER.finditer(text or ""))
    if len(grenzen) < 2:
        return [_ohne_soll(text or "")]
    teile = []
    for index, grenze in enumerate(grenzen):
        ende = grenzen[index + 1].start() if index + 1 < len(grenzen) else len(text)
        stueck = _ohne_soll(text[grenze.start():ende])
        if stueck:
            teile.append(stueck)
    return teile or [_ohne_soll(text or "")]


def _ohne_soll(text: str) -> str:
    treffer = _SOLL.search(text)
    if not treffer:
        return text.strip()
    return text[:treffer.start()].strip()
