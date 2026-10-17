"""Einfache Anonymisierung von Eingaben vor dem Speichern (Architektur Punkt 7).

Bewusst nur ein einfacher Regex-Anfang -- kein vollstaendiger Datenschutz-Schutz. Erkannt
werden: E-Mail-Adressen, IBAN, Telefonnummern, Strasse+Hausnummer, PLZ+Ort, sowie Namen nach
einer Anrede ("Herr/Frau/Mandant(in) <Name>"). NICHT erkannt werden u. a.: Namen ohne Anrede
oder Kontext, ungewoehnliche Schreibweisen, Adressen ohne Strassen-Suffix, Namen in
Fliesstext ohne erkennbares Muster. Das muss vor echtem Einsatz durch eine robustere Loesung
ersetzt werden (siehe app/README.md, Abschnitt Grenzen). Entwurf -- vom Steuerberater zu pruefen.
"""
from __future__ import annotations

import re

_MUSTER: list[tuple[str, re.Pattern[str]]] = [
    ("E-Mail", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("IBAN", re.compile(r"\bDE\d{2}\s?(?:\d{4}\s?){4}\d{2}\b")),
    ("Telefonnummer", re.compile(r"(?:\+49|0049|0)[\s/-]?\d{2,5}[\s/-]?\d{3,}(?:[\s/-]?\d+)*")),
    (
        "Adresse",
        re.compile(
            r"\b[A-ZÄÖÜ][a-zäöüß]+(?:straße|strasse|weg|allee|platz|gasse)\s+\d+\s?[a-zA-Z]?\b",
            re.IGNORECASE,
        ),
    ),
    ("Ort", re.compile(r"\b\d{5}\s+[A-ZÄÖÜ][a-zäöüß]+\b")),
    (
        "Name",
        re.compile(
            r"\b(Herr|Frau|Mandant(?:in)?)\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){0,2})"
        ),
    ),
]


def anonymisiere(text: str) -> str:
    """Ersetzt erkannte personenbezogene Muster durch Platzhalter wie '[E-Mail]'."""
    ergebnis = text
    for bezeichnung, muster in _MUSTER:
        if bezeichnung == "Name":
            ergebnis = muster.sub(lambda m: f"{m.group(1)} [Name]", ergebnis)
        else:
            ergebnis = muster.sub(f"[{bezeichnung}]", ergebnis)
    return ergebnis


def gefundene_kategorien(text: str) -> list[str]:
    """Nur fuer Tests/Diagnose: welche Kategorien wurden im Originaltext erkannt."""
    return [bezeichnung for bezeichnung, muster in _MUSTER if muster.search(text)]
