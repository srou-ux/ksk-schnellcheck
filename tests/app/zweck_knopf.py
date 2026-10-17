"""Hilfe für Tests (kein eigener Test): beantwortet die Rückfrage nach dem Zweck per Knopf, wie ein Nutzer.

Entscheidung des Nutzers (17.10.2026, „Geratenen Zweck immer nachfragen“): einen Zweck, den nur das Modell gelesen hat
(kein Wort dafür im Text), übernimmt das System nicht, sondern fragt „Wofür war dieser Auftrag gedacht?“. Viele ältere
Tests bilden eine Modellantwort mit `verwerterart`/`auftragszweck` zu einem Text nach, der den Zweck nicht nennt
(oft nur ein Platzhalter wie „F“). Dort bestätigt der Test jetzt den Zweck per Knopf – das erwartete Ergebnis der Tests
bleibt unverändert (der Knopf führt zur selben Einordnung wie die Modellantwort)."""
from __future__ import annotations

from typing import Any

from app import pflichtangaben, router
from app.einordnung import KATEGORIE_ZU_ZWECK
from app.schema import Fakten


def zweck_aus(fakten: Any) -> str | None:
    """Der Zweck, den die nachgebildete Modellantwort meinte ('eigenwerber' -> 'eigene_werbung')."""
    if isinstance(fakten, dict):
        fakten = Fakten.model_validate(fakten)
    if isinstance(fakten, str):
        return KATEGORIE_ZU_ZWECK.get(fakten, fakten)
    if fakten is None:
        return None
    return fakten.auftragszweck or KATEGORIE_ZU_ZWECK.get(fakten.verwerterart or "")


def mit_zweck(antwort, fakten: Any, llm):
    """Ist die Antwort die Rückfrage nach dem Zweck, klickt der Test den passenden Knopf; sonst unverändert."""
    zweck = zweck_aus(fakten)
    if (zweck and antwort.sitzungskennung and antwort.rueckfragen
            and antwort.rueckfragen[0] == pflichtangaben.FRAGE_ZWECK):
        return router.wende_feldantwort_an(antwort.sitzungskennung, "auftragszweck", zweck, llm)
    return antwort
