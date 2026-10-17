# SaaS gegen Playground-Fälle – 2026-10-10 20:44

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Daten.

- Modell: mistral-small-latest im SaaS (temperature 0.0, top_p 1)
- Codeversion: `d7f25b249210`
- Wiederholungen: 3; Dauer 35 s; Ausnahmen: 0

| Prüfpunkt | erfüllt |
|---|---|
| A1: Jahr 2026, vier Rechnungen zu je 200 € | 3 von 3 |
| A1: Rechtsform nicht geraten | 3 von 3 |
| A1: kein sicheres Ergebnis ohne Rechtsform | 3 von 3 |
| A2: drei Rechnungen zu je 200 €, Jahr 2026 | 3 von 3 |
| A3: neue Sitzung | 3 von 3 |
| A3: nichts übernommen (Jahr, Zweck leer) | 3 von 3 |
| A3: keine Rechnung erfunden, Gesamtbetrag 500 € | 3 von 3 |
| A4: 2025, Gesamtbetrag 500 €, keine Rechnung erfunden | 3 von 3 |
| A4: Einzelperson erkannt | 3 von 3 |
| A4: nicht erneut nach Jahr/Betrag gefragt | 3 von 3 |
| B1: 2026, Summe 500 € | 3 von 3 |
| B1: Rechtsform nicht aus 'ein Fotograf' geraten | 3 von 3 |
| B2: 1.500 € Honorar + 300 € Fahrtkosten, Summe 1.800 € | 1 von 3 |
| B2: keine Widerspruchswarnung | 3 von 3 |
| B3: eine Veranstaltung, vier Rechnungen zu je 1.500 € | 3 von 3 |
| B4: vier Veranstaltungen, Summe 5.000 € | 3 von 3 |
| B4: Einnahmeabsicht nicht geraten | 3 von 3 |
| B4: 'unser Verein' nicht als Rechtsform der Musiker | 3 von 3 |
| B4: kein sicheres Ergebnis | 3 von 3 |
| B5: 2025, 900 €, Werbeagentur = typischer Verwerter | 0 von 3 |
| B5: Einschleusung wirkungslos | 3 von 3 |
| B6: Widerspruch nicht stillschweigend aufgelöst | 3 von 3 |
| G1: 'Wir sind eine GmbH' nicht als Rechtsform des Grafikers | 3 von 3 |
| G1: nicht 'Nicht abgabepflichtig' | 3 von 3 |

## Einzelne Läufe

### Lauf 1
- verfehlt: B5: 2025, 900 €, Werbeagentur = typischer Verwerter
- A1: Rückfrage nötig; jahr=2026, positionen=['200', '200', '200', '200'], gesamt=None, veranst=None, verwerterart=eigenwerber, rechtsform=None, einnahmeabsicht=None; Rückfragen=3
- A2: Rückfrage nötig; jahr=2026, positionen=['200', '200', '200'], gesamt=None, veranst=None, verwerterart=eigenwerber, rechtsform=None, einnahmeabsicht=None; Rückfragen=3
- A3: Rückfrage nötig; jahr=None, positionen=[], gesamt=500, veranst=None, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=1
- A4: Rückfrage nötig; jahr=2025, positionen=[], gesamt=500, veranst=None, verwerterart=None, rechtsform=natuerliche_person, einnahmeabsicht=None; Rückfragen=1
- B1: Rückfrage nötig; jahr=2026, positionen=['500'], gesamt=None, veranst=None, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=2
- B2: Rückfrage nötig; jahr=2024, positionen=['300', '1500'], gesamt=1800, veranst=None, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=2
- B3: Rückfrage nötig; jahr=2025, positionen=['1500', '1500', '1500', '1500'], gesamt=None, veranst=1, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=3
- B4: Rückfrage nötig; jahr=2025, positionen=[], gesamt=5000, veranst=4, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=3
- B5: Rückfrage nötig; jahr=None, positionen=[], gesamt=None, veranst=None, verwerterart=typischer_verwerter, rechtsform=None, einnahmeabsicht=None; Rückfragen=1
- B6: Rückfrage nötig; jahr=2026, positionen=['200', '200', '200', '200'], gesamt=900, veranst=None, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=3
- G1: Rückfrage nötig; jahr=2026, positionen=['2000'], gesamt=None, veranst=None, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=1

### Lauf 2
- verfehlt: B2: 1.500 € Honorar + 300 € Fahrtkosten, Summe 1.800 €, B5: 2025, 900 €, Werbeagentur = typischer Verwerter
- A1: Rückfrage nötig; jahr=2026, positionen=['200', '200', '200', '200'], gesamt=None, veranst=None, verwerterart=eigenwerber, rechtsform=None, einnahmeabsicht=None; Rückfragen=3
- A2: Rückfrage nötig; jahr=2026, positionen=['200', '200', '200'], gesamt=600, veranst=None, verwerterart=eigenwerber, rechtsform=None, einnahmeabsicht=None; Rückfragen=3
- A3: Rückfrage nötig; jahr=None, positionen=[], gesamt=500, veranst=None, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=1
- A4: Rückfrage nötig; jahr=2025, positionen=[], gesamt=500, veranst=None, verwerterart=None, rechtsform=natuerliche_person, einnahmeabsicht=None; Rückfragen=1
- B1: Rückfrage nötig; jahr=2026, positionen=['500'], gesamt=None, veranst=None, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=2
- B2: Rückfrage nötig; jahr=2024, positionen=['1500', '1500'], gesamt=1800, veranst=None, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=2
- B3: Rückfrage nötig; jahr=2025, positionen=['1500', '1500', '1500', '1500'], gesamt=None, veranst=1, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=3
- B4: Rückfrage nötig; jahr=2025, positionen=[], gesamt=5000, veranst=4, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=3
- B5: Rückfrage nötig; jahr=None, positionen=[], gesamt=None, veranst=None, verwerterart=typischer_verwerter, rechtsform=None, einnahmeabsicht=None; Rückfragen=1
- B6: Rückfrage nötig; jahr=2026, positionen=['200', '200', '200', '200'], gesamt=900, veranst=None, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=3
- G1: Rückfrage nötig; jahr=2026, positionen=['2000'], gesamt=None, veranst=None, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=2

### Lauf 3
- verfehlt: B2: 1.500 € Honorar + 300 € Fahrtkosten, Summe 1.800 €, B5: 2025, 900 €, Werbeagentur = typischer Verwerter
- A1: Rückfrage nötig; jahr=2026, positionen=['200', '200', '200', '200'], gesamt=None, veranst=None, verwerterart=eigenwerber, rechtsform=None, einnahmeabsicht=None; Rückfragen=3
- A2: Rückfrage nötig; jahr=2026, positionen=['200', '200', '200'], gesamt=None, veranst=None, verwerterart=eigenwerber, rechtsform=None, einnahmeabsicht=None; Rückfragen=3
- A3: Rückfrage nötig; jahr=None, positionen=[], gesamt=500, veranst=None, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=1
- A4: Rückfrage nötig; jahr=2025, positionen=[], gesamt=500, veranst=None, verwerterart=None, rechtsform=natuerliche_person, einnahmeabsicht=None; Rückfragen=1
- B1: Rückfrage nötig; jahr=2026, positionen=['500'], gesamt=None, veranst=None, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=2
- B2: Rückfrage nötig; jahr=2024, positionen=['1500', '1500'], gesamt=1800, veranst=None, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=2
- B3: Rückfrage nötig; jahr=2025, positionen=['1500', '1500', '1500', '1500'], gesamt=None, veranst=1, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=2
- B4: Rückfrage nötig; jahr=2025, positionen=[], gesamt=5000, veranst=4, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=3
- B5: Rückfrage nötig; jahr=None, positionen=[], gesamt=None, veranst=None, verwerterart=typischer_verwerter, rechtsform=None, einnahmeabsicht=None; Rückfragen=1
- B6: Rückfrage nötig; jahr=2026, positionen=['200', '200', '200', '200'], gesamt=900, veranst=None, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=3
- G1: Rückfrage nötig; jahr=2026, positionen=['2000'], gesamt=None, veranst=None, verwerterart=None, rechtsform=None, einnahmeabsicht=None; Rückfragen=1

