# Dialogtest Fallgrenzen – 2026-10-10 20:30

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Daten.

- Codeversion: `e09e7579097d`
- Einstellungen: Modell mistral-large-latest; temperature 0.0, top_p 1 (fest in app/llm/mistral.py); Timeout 30.0 s; Wiederholungen bei 429/503: 3, Wartezeiten [1.0, 3.0, 9.0]
- Wiederholungen: 5; Dauer gesamt 149 s; Modellaufrufe (Extraktion): 30, Mittel 4.8 s, längster 9.0 s
- Technische Fehler: 0; Schutzmechanismus griff (Protokoll): 0

| Prüfpunkt | erfüllt |
|---|---|
| 1 Ausgangsfall: 2026, vier Rechnungen zu je 200 € | 5 von 5 |
| 2 Korrektur: drei Rechnungen, Jahr bleibt 2026 | 5 von 5 |
| 2 Korrektur: alte Bestätigung ungültig | 5 von 5 |
| 3 Neuer Fall: neue Sitzung | 5 von 5 |
| 3 Neuer Fall: nichts aus dem alten Fall übernommen (Jahr, Zweck leer) | 5 von 5 |
| 3 Neuer Fall: keine Rechnungsposition erfunden | 5 von 5 |
| 3 Neuer Fall: Gesamtbetrag 500 € erhalten | 5 von 5 |
| 3 Beobachtung: Modell setzt keine Rechtsform ohne Beleg | 0 von 5 |
| 4 Ergänzung: Jahr 2025 übernommen | 5 von 5 |
| 4 Ergänzung: nicht erneut nach Jahr oder Betrag gefragt | 5 von 5 |
| 4 Ergänzung: ohne Rückfrage (Modell übernimmt 'eigene Werbung'/'Einzelperson') | 0 von 5 |
| 4 Bestätigung ohne erfundene Position | 5 von 5 |
| 4 Ergebnis: nicht abgabepflichtig (500 € ≤ 700 €, 2025) | 5 von 5 |

## Technische Fehler

Keine.

## Schutzmechanismus griff (kein Fehler, nur zur Nachverfolgung)

Keine.

## Beobachtung: '500 Euro berechnet' ohne 'insgesamt' (Playground-Variante)

- Lauf 1: positionen=[Decimal('500')], gesamtbetrag=None, jahr=None, verwerterart=None
- Lauf 2: positionen=[Decimal('500')], gesamtbetrag=None, jahr=None, verwerterart=None
- Lauf 3: positionen=[Decimal('500')], gesamtbetrag=None, jahr=None, verwerterart=None
- Lauf 4: positionen=[Decimal('500')], gesamtbetrag=None, jahr=None, verwerterart=None
- Lauf 5: positionen=[Decimal('500')], gesamtbetrag=None, jahr=None, verwerterart=None

## Einzelne Läufe

### Lauf 1
- verfehlt: 3 Beobachtung: Modell setzt keine Rechtsform ohne Beleg, 4 Ergänzung: ohne Rückfrage (Modell übernimmt 'eigene Werbung'/'Einzelperson')
- nach 3: positionen=[], gesamtbetrag=500, jahr=None, rechtsform=natuerliche_person
- Rückfragen nach der Ergänzung: ['Ist der Auftraggeber in diesem Fall eigenwerbend tätig (Werbung für das eigene Unternehmen), ein typischer Verwerter (z. B. Werbeagentur, Verlag, Galerie, die für andere verwertet) oder Veranstalter im Sinne der Generalklausel (z. B. nur gelegentliche Veranstaltungen)?']
- Ergebnis: Nicht abgabepflichtig (Vorschlag); Fakten: Jahr: 2025; Leistung: Fotografie; Art des Auftraggebers: Eigenwerbung; Auftragnehmer: natürliche Person; Gesamtbetrag (Aufteilung auf Rechnungen unbekannt): 500,00 €, natürliche Person
- Modell-Rohfakten je Nachricht: [Wir haben 2026 für unsere eigene Werbung… Verlauf 0] {'anfrageart': 'bewertung', 'jahr': 2026, 'leistungsart': 'Grafik/Design', 'positionen': [{'betrag': '200', 'nr': 1}, {'betrag': '200', 'nr': 2}, {'betrag': '200', 'nr': 3}, {'betrag': '200', 'nr': 4}], 'anzahl_auftraege': 4} | [Korrektur: Es waren drei Rechnungen. All… Verlauf 1] {'anfrageart': 'bewertung', 'jahr': 2026, 'leistungsart': 'Grafik/Design', 'positionen': [{'betrag': '200'}, {'betrag': '200'}, {'betrag': '200'}], 'anzahl_auftraege': 4} | [Neuer, unabhängiger Fall: Ein Fotograf h… Verlauf 0] {'anfrageart': 'bewertung', 'auftragnehmer_typ': 'natuerliche_person', 'leistungsart': 'Fotografie', 'gesamtbetrag_genannt': '500'} | [Das war 2025, für unsere eigene Werbung,… Verlauf 1] {'anfrageart': 'bewertung', 'jahr': 2025, 'unternehmensart': 'eigene Werbung', 'auftragnehmer_typ': 'natuerliche_person', 'leistungsart': 'Fotografie', 'gesamtbetrag_genannt': '500'}

### Lauf 2
- verfehlt: 3 Beobachtung: Modell setzt keine Rechtsform ohne Beleg, 4 Ergänzung: ohne Rückfrage (Modell übernimmt 'eigene Werbung'/'Einzelperson')
- nach 3: positionen=[], gesamtbetrag=500, jahr=None, rechtsform=natuerliche_person
- Rückfragen nach der Ergänzung: ['Ist der Auftraggeber in diesem Fall eigenwerbend tätig (Werbung für das eigene Unternehmen), ein typischer Verwerter (z. B. Werbeagentur, Verlag, Galerie, die für andere verwertet) oder Veranstalter im Sinne der Generalklausel (z. B. nur gelegentliche Veranstaltungen)?']
- Ergebnis: Nicht abgabepflichtig (Vorschlag); Fakten: Jahr: 2025; Leistung: Fotografie; Art des Auftraggebers: Eigenwerbung; Auftragnehmer: natürliche Person; Gesamtbetrag (Aufteilung auf Rechnungen unbekannt): 500,00 €, natürliche Person
- Modell-Rohfakten je Nachricht: [Wir haben 2026 für unsere eigene Werbung… Verlauf 0] {'anfrageart': 'bewertung', 'jahr': 2026, 'leistungsart': 'Grafik/Design', 'positionen': [{'betrag': '200', 'nr': 1}, {'betrag': '200', 'nr': 2}, {'betrag': '200', 'nr': 3}, {'betrag': '200', 'nr': 4}], 'anzahl_auftraege': 4} | [Korrektur: Es waren drei Rechnungen. All… Verlauf 1] {'anfrageart': 'bewertung', 'jahr': 2026, 'leistungsart': 'Grafik/Design', 'positionen': [{'betrag': '200', 'nr': 1}, {'betrag': '200', 'nr': 2}, {'betrag': '200', 'nr': 3}], 'anzahl_auftraege': 4} | [Neuer, unabhängiger Fall: Ein Fotograf h… Verlauf 0] {'anfrageart': 'bewertung', 'auftragnehmer_typ': 'natuerliche_person', 'leistungsart': 'Fotografie', 'gesamtbetrag_genannt': '500'} | [Das war 2025, für unsere eigene Werbung,… Verlauf 1] {'anfrageart': 'bewertung', 'jahr': 2025, 'unternehmensart': 'eigene Werbung', 'auftragnehmer_typ': 'natuerliche_person', 'leistungsart': 'Fotografie', 'gesamtbetrag_genannt': '500'}

### Lauf 3
- verfehlt: 3 Beobachtung: Modell setzt keine Rechtsform ohne Beleg, 4 Ergänzung: ohne Rückfrage (Modell übernimmt 'eigene Werbung'/'Einzelperson')
- nach 3: positionen=[], gesamtbetrag=500, jahr=None, rechtsform=natuerliche_person
- Rückfragen nach der Ergänzung: ['Ist der Auftraggeber in diesem Fall eigenwerbend tätig (Werbung für das eigene Unternehmen), ein typischer Verwerter (z. B. Werbeagentur, Verlag, Galerie, die für andere verwertet) oder Veranstalter im Sinne der Generalklausel (z. B. nur gelegentliche Veranstaltungen)?']
- Ergebnis: Nicht abgabepflichtig (Vorschlag); Fakten: Jahr: 2025; Leistung: Fotografie; Art des Auftraggebers: Eigenwerbung; Auftragnehmer: natürliche Person; Gesamtbetrag (Aufteilung auf Rechnungen unbekannt): 500,00 €, natürliche Person
- Modell-Rohfakten je Nachricht: [Wir haben 2026 für unsere eigene Werbung… Verlauf 0] {'anfrageart': 'bewertung', 'jahr': 2026, 'leistungsart': 'Grafik/Design', 'positionen': [{'betrag': '200'}, {'betrag': '200'}, {'betrag': '200'}, {'betrag': '200'}], 'anzahl_auftraege': 4} | [Korrektur: Es waren drei Rechnungen. All… Verlauf 1] {'anfrageart': 'bewertung', 'jahr': 2026, 'leistungsart': 'Grafik/Design', 'positionen': [{'betrag': '200'}, {'betrag': '200'}, {'betrag': '200'}]} | [Neuer, unabhängiger Fall: Ein Fotograf h… Verlauf 0] {'anfrageart': 'bewertung', 'auftragnehmer_typ': 'natuerliche_person', 'leistungsart': 'Fotografie', 'gesamtbetrag_genannt': '500'} | [Das war 2025, für unsere eigene Werbung,… Verlauf 1] {'anfrageart': 'bewertung', 'jahr': 2025, 'auftragnehmer_typ': 'natuerliche_person', 'leistungsart': 'Fotografie', 'gesamtbetrag_genannt': '500'}

### Lauf 4
- verfehlt: 3 Beobachtung: Modell setzt keine Rechtsform ohne Beleg, 4 Ergänzung: ohne Rückfrage (Modell übernimmt 'eigene Werbung'/'Einzelperson')
- nach 3: positionen=[], gesamtbetrag=500, jahr=None, rechtsform=natuerliche_person
- Rückfragen nach der Ergänzung: ['Ist der Auftraggeber in diesem Fall eigenwerbend tätig (Werbung für das eigene Unternehmen), ein typischer Verwerter (z. B. Werbeagentur, Verlag, Galerie, die für andere verwertet) oder Veranstalter im Sinne der Generalklausel (z. B. nur gelegentliche Veranstaltungen)?']
- Ergebnis: Nicht abgabepflichtig (Vorschlag); Fakten: Jahr: 2025; Leistung: Fotografie; Art des Auftraggebers: Eigenwerbung; Auftragnehmer: natürliche Person; Gesamtbetrag (Aufteilung auf Rechnungen unbekannt): 500,00 €, natürliche Person
- Modell-Rohfakten je Nachricht: [Wir haben 2026 für unsere eigene Werbung… Verlauf 0] {'anfrageart': 'bewertung', 'jahr': 2026, 'leistungsart': 'Grafik/Design', 'positionen': [{'betrag': '200', 'nr': 1}, {'betrag': '200', 'nr': 2}, {'betrag': '200', 'nr': 3}, {'betrag': '200', 'nr': 4}], 'anzahl_auftraege': 4} | [Korrektur: Es waren drei Rechnungen. All… Verlauf 1] {'anfrageart': 'bewertung', 'jahr': 2026, 'leistungsart': 'Grafik/Design', 'positionen': [{'betrag': '200'}, {'betrag': '200'}, {'betrag': '200'}]} | [Neuer, unabhängiger Fall: Ein Fotograf h… Verlauf 0] {'anfrageart': 'bewertung', 'auftragnehmer_typ': 'natuerliche_person', 'leistungsart': 'Fotografie', 'gesamtbetrag_genannt': '500'} | [Das war 2025, für unsere eigene Werbung,… Verlauf 1] {'anfrageart': 'bewertung', 'jahr': 2025, 'unternehmensart': 'eigene Werbung', 'auftragnehmer_typ': 'natuerliche_person', 'leistungsart': 'Fotografie', 'gesamtbetrag_genannt': '500'}

### Lauf 5
- verfehlt: 3 Beobachtung: Modell setzt keine Rechtsform ohne Beleg, 4 Ergänzung: ohne Rückfrage (Modell übernimmt 'eigene Werbung'/'Einzelperson')
- nach 3: positionen=[], gesamtbetrag=500, jahr=None, rechtsform=natuerliche_person
- Rückfragen nach der Ergänzung: ['Ist der Auftraggeber in diesem Fall eigenwerbend tätig (Werbung für das eigene Unternehmen), ein typischer Verwerter (z. B. Werbeagentur, Verlag, Galerie, die für andere verwertet) oder Veranstalter im Sinne der Generalklausel (z. B. nur gelegentliche Veranstaltungen)?']
- Ergebnis: Nicht abgabepflichtig (Vorschlag); Fakten: Jahr: 2025; Leistung: Fotografie; Art des Auftraggebers: Eigenwerbung; Auftragnehmer: natürliche Person; Gesamtbetrag (Aufteilung auf Rechnungen unbekannt): 500,00 €, natürliche Person
- Modell-Rohfakten je Nachricht: [Wir haben 2026 für unsere eigene Werbung… Verlauf 0] {'anfrageart': 'bewertung', 'jahr': 2026, 'leistungsart': 'Grafik/Design', 'positionen': [{'betrag': '200', 'nr': 1}, {'betrag': '200', 'nr': 2}, {'betrag': '200', 'nr': 3}, {'betrag': '200', 'nr': 4}], 'anzahl_auftraege': 4} | [Korrektur: Es waren drei Rechnungen. All… Verlauf 1] {'anfrageart': 'bewertung', 'jahr': 2026, 'leistungsart': 'Grafik/Design', 'positionen': [{'betrag': '200'}, {'betrag': '200'}, {'betrag': '200'}]} | [Neuer, unabhängiger Fall: Ein Fotograf h… Verlauf 0] {'anfrageart': 'bewertung', 'auftragnehmer_typ': 'natuerliche_person', 'leistungsart': 'Fotografie', 'gesamtbetrag_genannt': '500'} | [Das war 2025, für unsere eigene Werbung,… Verlauf 1] {'anfrageart': 'bewertung', 'jahr': 2025, 'auftragnehmer_typ': 'natuerliche_person', 'leistungsart': 'Fotografie', 'gesamtbetrag_genannt': '500'}

