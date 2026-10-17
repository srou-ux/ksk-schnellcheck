# Chatbot direkt getestet – 2026-10-16 (Chatbot direkt (Browser) – Mistral (EU))

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Soll-Werte: `aufgaben/audit/korpus_beispiele.json`. Code-Stand `76fc966`.
Jeder Fall wurde an der echten Weboberfläche gespielt: tippen, Knöpfe klicken, Fakten bestätigen.

- Fälle: 4 (Teil 1/1), Dauer 42 s
- RICHTIG: 1, NACHGEFRAGT: 3, **FALSCH: 0**, FEHLER: 0

| Fall | Fallgruppe | Soll | Ist | Bewertung | Rückfragen | Dauer |
|---|---|---|---|---|---|---|
| KB-0491 | F04 Umsatzsteuer gesondert ausgewiesen | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 14.5 s |
| KB-0521 | F04 Umsatzsteuer gesondert ausgewiesen | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 14.7 s |
| KB-0541 | F04 Umsatzsteuer gesondert ausgewiesen | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 9.0 s |
| KB-0551 | F04 Umsatzsteuer gesondert ausgewiesen | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 3.6 s |

## Abweichungen

### KB-0491 – F04 Umsatzsteuer gesondert ausgewiesen (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Aufteilung der Rechnung von Auftragnehmer 1 ist unklar: Ein Teilbetrag ist so hoch wie die ganze Rechnung. Bitte nennen Sie den Rechnungsbetrag und die darin enthaltenen Teilbeträge.']
- Gründe: Soll ['A'], Ist R

### KB-0521 – F04 Umsatzsteuer gesondert ausgewiesen (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Aufteilung der Rechnung von Auftragnehmer 1 ist unklar: Ein Teilbetrag ist so hoch wie die ganze Rechnung. Bitte nennen Sie den Rechnungsbetrag und die darin enthaltenen Teilbeträge.']
- Gründe: Soll ['A'], Ist R

### KB-0551 – F04 Umsatzsteuer gesondert ausgewiesen (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Aufteilung der Rechnung von Auftragnehmer 1 ist unklar: Ein Teilbetrag ist so hoch wie die ganze Rechnung. Bitte nennen Sie den Rechnungsbetrag und die darin enthaltenen Teilbeträge.']
- Gründe: Soll ['A'], Ist R

