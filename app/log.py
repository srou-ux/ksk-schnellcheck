"""Lueckenprotokoll (Architektur Punkt 7): anonymisierte Fragen mit Ergebnis
'Nicht abgedeckt', Datum, Jahr, Grund -- in einer lokalen Datei, NICHT im Repo
(siehe .gitignore: /app/_lokal/ bleibt auch nach Freigabe von /app/ gesperrt).
Daraus entsteht laut regelwerk/Chatbot_Systemanweisung_Entwurf.md Abschnitt 6 die
naechste Recherche und der naechste Fragenkatalog-Eintrag. Entwurf -- vom Steuerberater
zu pruefen.
"""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path

from app.anonymisierung import anonymisiere

STANDARD_PFAD = Path(__file__).resolve().parent / "_lokal" / "lueckenprotokoll.jsonl"


def protokoll_pfad() -> Path:
    """Pfad der Protokolldatei; ueber LUECKENPROTOKOLL_PFAD ueberschreibbar (z. B. fuer Tests)."""
    override = os.environ.get("LUECKENPROTOKOLL_PFAD")
    return Path(override) if override else STANDARD_PFAD


def protokolliere(frage: str, jahr: int | None, grund: str, *, pfad: Path | None = None) -> None:
    ziel = pfad or protokoll_pfad()
    ziel.parent.mkdir(parents=True, exist_ok=True)
    eintrag = {
        "datum": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
        "jahr": jahr,
        "grund": grund,
        "frage_anonymisiert": anonymisiere(frage),
    }
    with open(ziel, "a", encoding="utf-8") as f:
        f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")


def lies_protokoll(*, pfad: Path | None = None) -> list[dict]:
    ziel = pfad or protokoll_pfad()
    if not ziel.exists():
        return []
    with open(ziel, encoding="utf-8") as f:
        return [json.loads(zeile) for zeile in f if zeile.strip()]


def protokolliere_fakten(frage: str, stufe: str, fakten) -> None:
    """Nur zur Fehlersuche in Testläufen mit ERFUNDENEN Daten (14.10.2026, Schritt 2 Teilbeträge):
    schreibt die Fakten des Modells ('roh', vor den Schutzregeln) und die fertigen Fakten
    ('fertig') in die Datei aus FAKTEN_PROTOKOLL_PFAD. Ohne diese Variable passiert nichts
    (Normalbetrieb: aus). Die Frage wird anonymisiert wie im Lückenprotokoll."""
    ziel = os.environ.get("FAKTEN_PROTOKOLL_PFAD")
    if not ziel:
        return
    Path(ziel).parent.mkdir(parents=True, exist_ok=True)
    eintrag = {"stufe": stufe, "frage_anonymisiert": anonymisiere(frage),
               "fakten": fakten.model_dump(mode="json", exclude_none=True, exclude_defaults=True)}
    with open(ziel, "a", encoding="utf-8") as f:
        f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")
