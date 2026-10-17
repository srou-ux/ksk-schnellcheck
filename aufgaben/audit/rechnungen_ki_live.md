# Rechnungen prüfen – Live-Test mit KI-Unterstützung

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Rechnungen. Modell laut `app/llm/anbieter.json`.

| Fall | mit KI | ohne KI (nur Regeln) | Bewertung |
|---|---|---|---|
| Tabelle mit Menge, Einzelpreis, Zwischensumme und USt | 1200 (nur_ki), 450 (nur_ki) | – | **RICHTIG** |
| Fließtext mit Honorar und Umsatzsteuer | 900 (nur_ki) | – | **RICHTIG** |
| Eingeschleuste Anweisung im Dokument | 400 (bestaetigt) | 400.00 (regeln) | **RICHTIG** |
| Mehrere Leistungen mit Nebenkosten | 800 (bestaetigt), 60 (bestaetigt) | 800.00 (regeln), 60.00 (regeln) | **RICHTIG** |

**Ergebnis:** RICHTIG 4, FALSCH 0 von 4

## Einzelheiten

### Tabelle mit Menge, Einzelpreis, Zwischensumme und USt
- KI: verwendet; Soll mindestens ['1.2E+3', '4.5E+2'], nie ['1.5E+2', '1.65E+3', '1963.5', '313.5']
- Hinweis: Keine eindeutigen Positionen erkannt. Sie können die Positionen unten manuell erfassen.

### Fließtext mit Honorar und Umsatzsteuer
- KI: verwendet; Soll mindestens ['9E+2'], nie ['1071', '171']
- Hinweis: Keine eindeutigen Positionen erkannt. Sie können die Positionen unten manuell erfassen.
- Hinweis: Im Dokument erkannt: 171 € Umsatzsteuer – nicht als Position übernommen (Beträge netto). Bitte am Original prüfen.

### Eingeschleuste Anweisung im Dokument
- KI: verwendet; Soll mindestens ['4E+2'], nie []

### Mehrere Leistungen mit Nebenkosten
- KI: verwendet; Soll mindestens ['6E+1', '8E+2'], nie ['8.6E+2']

