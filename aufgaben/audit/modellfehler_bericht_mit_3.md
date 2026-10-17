# Chatbot direkt getestet – 2026-10-15 (Chatbot direkt (Browser) – Mistral (EU))

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Soll-Werte: `tests/archiv/alle_faelle.json`. Code-Stand `fb10d17`.
Jeder Fall wurde an der echten Weboberfläche gespielt: tippen, Knöpfe klicken, Fakten bestätigen.

- Fälle: 6, Dauer 60 s
- RICHTIG: 4, NACHGEFRAGT: 2, **FALSCH: 0**, FEHLER: 0

| Fall | Fallgruppe | Soll | Ist | Bewertung | Rückfragen | Dauer |
|---|---|---|---|---|---|---|
| pruefkatalog:P-28 | 28 Umsatzsteuer | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 5.6 s |
| pruefkatalog:P-32 | 32 Gestaltung plus Druck | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 1 | 17.5 s |
| alltag999:A-999 | Viel-Künstler-Sammelrechnung an Messe-Veranstalterin | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 21.6 s |
| waehrung:W-03 | Währung: US-Dollar mit Euro-Betrag in derselben Angabe | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 3.5 s |
| fehlerquellen:HT-2026-084 | C Verpflegungspauschale je Jahr | AUSKUNFT/R | Nicht abgedeckt (Quelle fehlt) | **NACHGEFRAGT** | 0 | 6.2 s |
| fehlerquellen:HT-2026-092 | D Mischrechnung | G | Grenzfall → Steuerberater entscheidet | **RICHTIG** | 1 | 5.1 s |

## Abweichungen

### waehrung:W-03 – Währung: US-Dollar mit Euro-Betrag in derselben Angabe (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Aufteilung der Rechnung von Auftragnehmer 1 ist unklar: Die Teilbeträge sind größer als der Rechnungsbetrag. Bitte nennen Sie den Rechnungsbetrag und die darin enthaltenen Teilbeträge.']
- Gründe: Soll ['A'], Ist R

### fehlerquellen:HT-2026-084 – C Verpflegungspauschale je Jahr (NACHGEFRAGT)
- Ist: Nicht abgedeckt (Quelle fehlt); Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | Bestätigt: Jahr: 2019; Position 1: 24,00 € „Verpflegungspauschalen an Künstler“ | 'Ja, das stimmt' -> Nicht abgedeckt (Quelle fehlt)
- Gründe: Soll ['AUSKUNFT', 'R'], Ist X

