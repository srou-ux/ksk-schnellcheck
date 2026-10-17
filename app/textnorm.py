"""Einheitliche Schreibweise von Beträgen für die festen Prüfungen (Korpus-Lauf 15.10.2026).

Nutzer und Rechnungen schreiben die Währung oft VOR die Zahl ('EUR 1.500,00', '€ 300'). Die festen Prüfungen in
app/zuordnung.py und app/fallstand.py suchen Beträge in der Form 'Zahl Währung' ('1.500,00 EUR'). Ohne Vereinheitlichung
blieben Beträge mit vorangestellter Währung unsichtbar (z. B. wurde 'darin EUR 66,50 Umsatzsteuer' nicht als Umsatzsteuer
erkannt). Diese Funktion stellt die Währung hinter die Zahl. Sie ändert nur den Text für die Prüfungen, nie die Frage an das
Sprachmodell. Unabhängig vom Sprachmodell."""
from __future__ import annotations

import re

# Live-Test „Rechnungen prüfen“ (17.10.2026): '… 1.200,00 EUR\n2  Illustrationen …' wurde zu '… 1.200,00 \n2 EUR …' – die
# Währung am Zeilenende galt als vorangestellt für die Zahl der NÄCHSTEN Zeile (1.200 € verschwand, 2 € entstand). Jetzt:
# nur innerhalb einer Zeile ([ \t]* statt \s*), und eine Währung direkt hinter einer Zahl gehört zu dieser Zahl.
_VORANGESTELLT = re.compile(r"(?<![0-9a-zA-ZäöüÄÖÜß])(€|EUR\b|Euro\b)[ \t]*(\d{1,3}(?:\.\d{3})+|\d+)(,\d{1,2})?(?![\d.,]\d)",
                            re.IGNORECASE)
_ZAHL_DAVOR = re.compile(r"(?:\d,\d{1,2}|\d\.\d{3})[ \t]*$")  # ein Geldbetrag ('1.200,00 EUR'), kein Jahr ('2026 EUR 900')


def waehrung_nach_hinten(text: str | None) -> str | None:
    """'EUR 1.500,00' -> '1.500,00 EUR'; '€300' -> '300 €'. Alles andere bleibt unverändert."""
    if not text:
        return text

    def ersetze(m: re.Match) -> str:
        if _ZAHL_DAVOR.search(text[max(0, m.start() - 20):m.start()]):
            return m.group(0)  # '1.200,00 EUR 2 Stück': die Währung gehört zur Zahl davor
        return f"{m.group(2)}{m.group(3) or ''} {m.group(1)}"

    return _VORANGESTELLT.sub(ersetze, text)
