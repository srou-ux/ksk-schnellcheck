# Playground-Anweisung direkt gegen mistral-large-latest – Temperature 0.7
Stand 2026-10-10 20:51; 3 Läufe; Mittel 1.0 s je Aufruf. Ohne SaaS, nur das rohe Modell mit der vereinfachten Anweisung. Erfundene Daten.

| Fall | richtig |
|---|---|
| A1 | 3 von 3 |
| A2 | 3 von 3 |
| A3 | 0 von 3 |
| A4 | 0 von 3 |
| B1 | 3 von 3 |
| B2 | 2 von 3 |
| B3 | 3 von 3 |
| B4 | 0 von 3 |
| B5 | 3 von 3 |
| B6 | 3 von 3 |

## Antworten

### Lauf 1
- A1 ✅ ````json
{
  "jahr": 2026,
  "anzahl_rechnungen": 4,
  "betrag_je_rechnung_eur": 200,
  "werbezweck": "eigene Werbung"
}
````
- A2 ✅ ````json
{
  "jahr": 2026,
  "anzahl_rechnungen": 3,
  "betrag_je_rechnung_eur": 200,
  "werbezweck": "eigene Werbung"
}
````
- A3 ❌ ````json
{
  "jahr": null,
  "anzahl_rechnungen": null,
  "betrag_je_rechnung_eur": 500,
  "werbezweck": null
}
```` – betrag_je_rechnung_eur sollte null sein, ist 500
- A4 ❌ ````json
{
  "jahr": 2025,
  "anzahl_rechnungen": null,
  "betrag_je_rechnung_eur": 500,
  "werbezweck": "eigene Werbung"
}
```` – betrag_je_rechnung_eur sollte null sein, ist 500
- B1 ✅ ````json
{
  "jahr": 2026,
  "anzahl_rechnungen": null,
  "betrag_je_rechnung_eur": 500,
  "werbezweck": null
}
````
- B2 ❌ ````json
{
  "jahr": 2024,
  "anzahl_rechnungen": null,
  "betrag_je_rechnung_eur": 1800,
  "werbezweck": null
}
```` – betrag_je_rechnung_eur sollte null sein, ist 1800
- B3 ✅ ````json
{
  "jahr": 2025,
  "anzahl_rechnungen": 4,
  "betrag_je_rechnung_eur": 1500,
  "werbezweck": null
}
````
- B4 ❌ ````json
{
  "jahr": 2025,
  "anzahl_rechnungen": 4,
  "betrag_je_rechnung_eur": 1250,
  "werbezweck": null
}
```` – anzahl_rechnungen sollte null sein, ist 4; betrag_je_rechnung_eur sollte null sein, ist 1250
- B5 ✅ ````json
{
  "jahr": 2025,
  "anzahl_rechnungen": null,
  "betrag_je_rechnung_eur": 900,
  "werbezweck": null
}
````
- B6 ✅ ````json
{
  "jahr": 2026,
  "anzahl_rechnungen": 4,
  "betrag_je_rechnung_eur": 200,
  "werbezweck": null
}
````

### Lauf 2
- A1 ✅ ````json
{
  "jahr": 2026,
  "anzahl_rechnungen": 4,
  "betrag_je_rechnung_eur": 200,
  "werbezweck": true
}
````
- A2 ✅ ````json
{
  "jahr": 2026,
  "anzahl_rechnungen": 3,
  "betrag_je_rechnung_eur": 200,
  "werbezweck": true
}
````
- A3 ❌ ````json
{
  "jahr": null,
  "anzahl_rechnungen": null,
  "betrag_je_rechnung_eur": 500,
  "werbezweck": null
}
```` – betrag_je_rechnung_eur sollte null sein, ist 500
- A4 ❌ ````json
{
  "jahr": 2025,
  "anzahl_rechnungen": null,
  "betrag_je_rechnung_eur": 500,
  "werbezweck": true
}
```` – betrag_je_rechnung_eur sollte null sein, ist 500
- B1 ✅ ````json
{
  "jahr": 2026,
  "anzahl_rechnungen": null,
  "betrag_je_rechnung_eur": 500,
  "werbezweck": null
}
````
- B2 ✅ ````json
{
  "jahr": 2024,
  "anzahl_rechnungen": null,
  "betrag_je_rechnung_eur": null,
  "werbezweck": null
}
````
- B3 ✅ ````json
{
  "jahr": 2025,
  "anzahl_rechnungen": 4,
  "betrag_je_rechnung_eur": 1500,
  "werbezweck": null
}
````
- B4 ❌ ````json
{
  "jahr": 2025,
  "anzahl_rechnungen": 4,
  "betrag_je_rechnung_eur": 1250,
  "werbezweck": null
}
```` – anzahl_rechnungen sollte null sein, ist 4; betrag_je_rechnung_eur sollte null sein, ist 1250
- B5 ✅ ````json
{
  "jahr": 2025,
  "anzahl_rechnungen": null,
  "betrag_je_rechnung_eur": 900,
  "werbezweck": null
}
````
- B6 ✅ ````json
{
  "jahr": 2026,
  "anzahl_rechnungen": 4,
  "betrag_je_rechnung_eur": 200,
  "werbezweck": null
}
````

### Lauf 3
- A1 ✅ ````json
{
  "jahr": 2026,
  "anzahl_rechnungen": 4,
  "betrag_je_rechnung_eur": 200,
  "werbezweck": true
}
````
- A2 ✅ ````json
{
  "jahr": 2026,
  "anzahl_rechnungen": 3,
  "betrag_je_rechnung_eur": 200,
  "werbezweck": true
}
````
- A3 ❌ ````json
{
  "jahr": null,
  "anzahl_rechnungen": null,
  "betrag_je_rechnung_eur": 500,
  "werbezweck": null
}
```` – betrag_je_rechnung_eur sollte null sein, ist 500
- A4 ❌ ````json
{
  "jahr": 2025,
  "anzahl_rechnungen": null,
  "betrag_je_rechnung_eur": 500,
  "werbezweck": true
}
```` – betrag_je_rechnung_eur sollte null sein, ist 500
- B1 ✅ ````json
{
  "jahr": 2026,
  "anzahl_rechnungen": null,
  "betrag_je_rechnung_eur": 500,
  "werbezweck": null
}
````
- B2 ✅ ````json
{
  "jahr": 2024,
  "anzahl_rechnungen": null,
  "betrag_je_rechnung_eur": null,
  "werbezweck": null
}
````
- B3 ✅ ````json
{
  "jahr": 2025,
  "anzahl_rechnungen": 4,
  "betrag_je_rechnung_eur": 1500,
  "werbezweck": null
}
````
- B4 ❌ ````json
{
  "jahr": 2025,
  "anzahl_rechnungen": 4,
  "betrag_je_rechnung_eur": 1250,
  "werbezweck": null
}
```` – anzahl_rechnungen sollte null sein, ist 4; betrag_je_rechnung_eur sollte null sein, ist 1250
- B5 ✅ ````json
{
  "jahr": 2025,
  "anzahl_rechnungen": null,
  "betrag_je_rechnung_eur": 900,
  "werbezweck": null
}
````
- B6 ✅ ````json
{
  "jahr": 2026,
  "anzahl_rechnungen": 4,
  "betrag_je_rechnung_eur": 200,
  "werbezweck": null
}
````

