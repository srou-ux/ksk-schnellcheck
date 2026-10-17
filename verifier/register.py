"""Regelregister als Daten (Gegenrechnung). Liest `kern/parameter.json` als JSON; importiert `kern` nicht.

Jeder Zugriff wird gemerkt (Schlüssel und Gültigkeit), damit das Prüfprotokoll zeigen kann, welche Registerzeilen die
Gegenrechnung verwendet hat."""
from __future__ import annotations

import json
import operator
from fractions import Fraction
from pathlib import Path

PARAMETER_PFAD = Path(__file__).resolve().parents[1] / "kern" / "parameter.json"

_VERGLEICHE = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le, "=": operator.eq}


class Luecke(Exception):
    """Für Schlüssel und Jahr gibt es keine eindeutige Registerzeile: 'Nicht abgedeckt'."""


def bruch(text) -> Fraction:
    """Dezimaltext exakt als Bruch ('4.9' -> 49/10). Keine Gleitkommazahl."""
    return Fraction(str(text))


class Register:
    def __init__(self, daten: dict):
        self._d = daten
        self.verwendet: dict[tuple, dict] = {}

    @classmethod
    def lade(cls, pfad: Path = PARAMETER_PFAD) -> "Register":
        return cls(json.loads(Path(pfad).read_text(encoding="utf-8")))

    @property
    def daten(self) -> dict:
        return self._d

    def _merke(self, schluessel: str, von, bis, wert) -> None:
        self.verwendet[(schluessel, von, bis, str(wert))] ={"schluessel": schluessel, "von": von, "bis": bis, "wert": str(wert)}

    # --- Regelregister (Blatt 'Regelregister') ---
    def zeilen(self, schluessel: str, jahr) -> list[dict]:
        if jahr is None:
            raise Luecke(f"{schluessel}: ohne Jahr keine Registerzeile")
        treffer = [z for z in self._d.get("register", []) if z["schluessel"] == schluessel
                   and (z["von"] is None or z["von"] <= jahr) and (z["bis"] is None or jahr <= z["bis"])]
        if not treffer:
            raise Luecke(f"{schluessel}: keine Registerzeile für {jahr}")
        for z in treffer:
            self._merke(schluessel, z["von"], z["bis"], z["wert"])
        return treffer

    def zeile(self, schluessel: str, jahr) -> dict:
        treffer = self.zeilen(schluessel, jahr)
        if len(treffer) != 1:
            raise Luecke(f"{schluessel}: {jahr} mehrdeutig")
        return treffer[0]

    def zahl(self, schluessel: str, jahr) -> Fraction:
        return bruch(self.zeile(schluessel, jahr)["wert"])

    def text(self, schluessel: str, jahr) -> str:
        return str(self.zeile(schluessel, jahr)["wert"])

    def liste(self, schluessel: str, jahr) -> set[str]:
        return {str(z["wert"]) for z in self.zeilen(schluessel, jahr)}

    def gilt(self, schluessel: str, jahr, links: Fraction, rechts: Fraction) -> bool:
        """Vergleich mit dem Operator der Registerzeile ('übersteigt' = '>')."""
        op = self.zeile(schluessel, jahr)["operator"]
        if op not in _VERGLEICHE:
            raise Luecke(f"{schluessel}: unbekannter Vergleich {op!r}")
        return _VERGLEICHE[op](links, rechts)

    def operator(self, schluessel: str, jahr) -> str | None:
        return self.zeile(schluessel, jahr)["operator"]

    # --- Blätter 'Abgabesätze', 'Schwellen nach Jahr', 'Pauschalen nach Jahr' ---
    def abgabesatz(self, jahr) -> Fraction | None:
        z = self._d.get("abgabesatz", {}).get(str(jahr))
        if not z:
            return None
        self._merke("abgabesatz", jahr, jahr, z["prozent"])
        return bruch(z["prozent"])

    def schwelle(self, jahr) -> dict | None:
        z = self._d.get("schwelle", {}).get(str(jahr))
        if not z or not z.get("euro"):
            return None
        self._merke("schwelle", jahr, jahr, z["euro"])
        return {"euro": bruch(z["euro"]), "fassung": z["fassung"]}

    def pauschale(self, jahr) -> dict | None:
        z = self._d.get("pauschale", {}).get(str(jahr))
        if not z:
            return None
        self._merke("pauschale", jahr, jahr, z["uebungsleiter"])
        return z

    def protokoll(self) -> list[dict]:
        return sorted(self.verwendet.values(), key=lambda z: (z["schluessel"], str(z["von"])))
