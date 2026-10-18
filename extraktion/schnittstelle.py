"""Eine Funktion, zwei Leser. Der Kern wird hier nicht aufgerufen."""
from __future__ import annotations

from extraktion import mistral_adapter, regel


def extrahiere_dokument(dokument, weg: str = "rule", **kwargs) -> dict:
    if weg == "rule":
        return regel.extrahiere(dokument)
    if weg == "mistral":
        return mistral_adapter.extrahiere(dokument, **kwargs)
    raise ValueError("Unbekannter Extraktionsweg: " + weg)
