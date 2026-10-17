"""Deterministische Plausibilitaetspruefungen auf den extrahierten Fakten (Chatbot Teil 1f,
Abschnitt I.2). Keine Festwerte, keine eigene Berechnung -- nur ein Vergleich zwischen zwei
bereits erfassten Zahlen. Ersetzt nichts automatisch: die Faktenbestaetigung zeigt die
Warnung, der Nutzer entscheidet (CLAUDE.md, Regel 1 -- Vorschlag, keine Korrektur).
"""
from __future__ import annotations

from app.baustein import formatiere_betrag
from app.schema import Fakten


def gesamtbetrag_warnung(fakten: Fakten) -> str | None:
    """Nennt der Nutzer einen Gesamtbetrag UND weicht die Summe der einzeln erfassten
    Positionen davon ab, liefert das eine deutliche Warnung fuer die Faktenbestaetigung.

    Hintergrund (Befund M2, aufgaben/PRUEFBERICHT_Mistral_Lauf1.md): bei "1.800 Euro, darin
    300 Euro Fahrtkosten" hat das Sprachmodell zwei Positionen 1.800 UND 300 (= 2.100)
    extrahiert, statt (1.800 - 300) und 300. `gesamtbetrag_genannt` haelt den vom Nutzer
    genannten GESAMTBETRAG fest (1.800), unabhaengig davon, wie das Modell die Positionen
    aufgeteilt hat -- weicht die Summe ab, sieht der Nutzer das bei der Bestaetigung, statt
    es nur zu uebersehen."""
    if fakten.gesamtbetrag_genannt is None or not fakten.positionen:
        return None
    summe = fakten.summe_positionen()
    if summe == fakten.gesamtbetrag_genannt:
        return None
    return (
        f"Die Summe der Positionen ({formatiere_betrag(summe)}) passt nicht zum "
        f"genannten Gesamtbetrag ({formatiere_betrag(fakten.gesamtbetrag_genannt)})."
    )
