"""Schnittstelle fuer Sprachmodell-Adapter. Das Modell wandelt Nutzertext in Fakten um
und formuliert spaeter die Antwort ausschliesslich aus Kernergebnis + Regeln -- es rechnet
nie und erfindet keine Fundstellen. Entwurf -- vom Steuerberater zu pruefen.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.schema import Fakten


class LLMFehlgeschlagen(Exception):
    """Teil 1f, Abschnitt I.3/I.5d: das Sprachmodell hat keine brauchbare Antwort geliefert
    (kein gueltiges JSON, unbekannte Felder/falsche Typen, Zeitueberschreitung, HTTP-Fehler).
    app/router.py faengt das ab (nie ein unbehandelter Absturz/HTTP 500) und antwortet mit
    einer festen Rueckfrage, die Frage erneut zu stellen.

    `status`: HTTP-Status, falls es ein HTTP-Fehler war (sonst None) -- für die Wahl des festen Texts im Router."""

    def __init__(self, *args, status: int | None = None) -> None:
        super().__init__(*args)
        self.status = status


@dataclass
class AntwortKontext:
    """Alles, was der Antwort-Generator zur Verfuegung hat -- und zwar ausschliesslich das.
    Kein Feld hier darf vom Sprachmodell frei erfunden werden."""

    frage: str
    fakten: Fakten
    ergebnisklasse: str
    kern_protokoll: dict[str, Any] = field(default_factory=dict)
    regeln: list[dict[str, Any]] = field(default_factory=list)
    fundstellen: list[str] = field(default_factory=list)
    rueckfragen: list[str] = field(default_factory=list)
    hinweise: list[str] = field(default_factory=list)
    # RAG (Teil 2): Fundstellen der Quelltext-Stellen, auf die sich die verwendeten Regeln stützen
    # (vom Quellenabruf geliefert, nie vom Modell), und alles, was dieser Antwort als Beleg
    # GELIEFERT wurde (app/router.py::_ausgeben). Die Prüfung verlangt: jede Regel-ID und jedes
    # Aktenzeichen im Text steht darunter (strenger als 'existiert irgendwo im Repo').
    belegstellen: list[str] = field(default_factory=list)
    gelieferte_belege: list[str] | None = None


class LLM(Protocol):
    """Schnittstelle, die sowohl FakeLLM als auch der Mistral-Adapter erfuellen."""

    name: str

    def extrahiere_fakten(self, frage: str, verlauf: list[str] | None = None,
                          fallstand: Fakten | None = None) -> Fakten:
        """Wandelt die Nutzerfrage (und optional den Verlauf) in `Fakten` um. Unbekanntes
        bleibt `None` -- nie raten."""
        ...

    def beschreibe_fall(self, kontext: AntwortKontext) -> str:
        """Teil 1g (Mischform): EINE kurze Beschreibung des Einzelfalls in einem Satz --
        nur mit Platzhaltern aus `erzeuge_platzhalter(kontext)` (z. B. `{JAHR}`), ohne
        Zahlen, Normen, Ergebnisse, Wertungen, Links. Werte bekommt das Modell nie. Der
        eigentliche Antwort-Koerper kommt ausschliesslich aus festen Textbausteinen
        (app/textbausteine.py) -- das Modell schreibt ihn nicht mehr."""
        ...
