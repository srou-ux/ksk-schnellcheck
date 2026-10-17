# Chatbot direkt getestet – 2026-10-16 (Chatbot direkt (Browser) – Mistral (EU))

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Soll-Werte: `aufgaben/audit/korpus_beispiele.json`. Code-Stand `5c85a93`.
Jeder Fall wurde an der echten Weboberfläche gespielt: tippen, Knöpfe klicken, Fakten bestätigen.

- Fälle: 37 (Teil 1/1, jeder 50. Fall), Dauer 17 s
- RICHTIG: 1, NACHGEFRAGT: 36, **FALSCH: 0**, FEHLER: 0

| Fall | Fallgruppe | Soll | Ist | Bewertung | Rückfragen | Dauer |
|---|---|---|---|---|---|---|
| KB-0001 | F01 Eigenwerbung: Schwelle (Fassung B) | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.6 s |
| KB-0051 | F01 Eigenwerbung: Schwelle (Fassung B) | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.5 s |
| KB-0101 | F01 Eigenwerbung: Schwelle (Fassung B) | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.6 s |
| KB-0151 | F01 Eigenwerbung: Schwelle (Fassung B) | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-0201 | F01 Eigenwerbung: Schwelle (Fassung B) | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-0251 | F02 Eigenwerbung: Grenze 450 € (Fassung A) | G | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-0301 | F02 Eigenwerbung: Grenze 450 € (Fassung A) | G | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-0351 | F03 Rechtsform des Empfängers | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-0401 | F03 Rechtsform des Empfängers | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-0451 | F03 Rechtsform des Empfängers | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-0501 | F04 Umsatzsteuer gesondert ausgewiesen | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-0551 | F04 Umsatzsteuer gesondert ausgewiesen | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-0601 | F05 Typischer Verwerter oder Eigenwerbung | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-0651 | F05 Typischer Verwerter oder Eigenwerbung | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-0701 | F05 Typischer Verwerter oder Eigenwerbung | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-0751 | F06 Künstlerisch oder nicht | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-0801 | F06 Künstlerisch oder nicht | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.5 s |
| KB-0851 | F06 Künstlerisch oder nicht | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-0901 | F07 Privatperson oder Unternehmen | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-0951 | F08 Veranstaltungen (Generalklausel) | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-1001 | F08 Veranstaltungen (Generalklausel) | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.5 s |
| KB-1051 | F08 Veranstaltungen (Generalklausel) | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-1101 | F09 Reisekosten mit oder ohne Nachweis | A/R | Rückfrage nötig | **RICHTIG** | 0 | 0.4 s |
| KB-1151 | F10 Jahr genannt oder nicht | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-1201 | F11 Euro oder fremde Währung | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-1251 | F12 Auskunft: Abgabesatz | AUSKUNFT | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-1301 | F12 Auskunft: Abgabesatz | AUSKUNFT | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-1351 | F13 Vorauszahlung | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-1401 | F13 Vorauszahlung | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-1451 | F14 Übungsleiterpauschale | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-1501 | F15 Säumniszuschlag | S | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-1551 | F16 Verwertungsgesellschaft | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-1601 | F17 Eingeschmuggelte Anweisung | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-1651 | F18 Störende Zahlen im Text | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-1701 | F18 Störende Zahlen im Text | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-1751 | F19 Mehrere Rechnungen im Jahr | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |
| KB-1801 | F19 Mehrere Rechnungen im Jahr | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 0.4 s |

## Abweichungen

### KB-0001 – F01 Eigenwerbung: Schwelle (Fassung B) (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-0051 – F01 Eigenwerbung: Schwelle (Fassung B) (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-0101 – F01 Eigenwerbung: Schwelle (Fassung B) (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-0151 – F01 Eigenwerbung: Schwelle (Fassung B) (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-0201 – F01 Eigenwerbung: Schwelle (Fassung B) (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-0251 – F02 Eigenwerbung: Grenze 450 € (Fassung A) (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['G'], Ist R

### KB-0301 – F02 Eigenwerbung: Grenze 450 € (Fassung A) (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['G'], Ist R

### KB-0351 – F03 Rechtsform des Empfängers (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-0401 – F03 Rechtsform des Empfängers (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-0451 – F03 Rechtsform des Empfängers (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-0501 – F04 Umsatzsteuer gesondert ausgewiesen (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-0551 – F04 Umsatzsteuer gesondert ausgewiesen (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-0601 – F05 Typischer Verwerter oder Eigenwerbung (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-0651 – F05 Typischer Verwerter oder Eigenwerbung (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-0701 – F05 Typischer Verwerter oder Eigenwerbung (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-0751 – F06 Künstlerisch oder nicht (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-0801 – F06 Künstlerisch oder nicht (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-0851 – F06 Künstlerisch oder nicht (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-0901 – F07 Privatperson oder Unternehmen (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-0951 – F08 Veranstaltungen (Generalklausel) (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-1001 – F08 Veranstaltungen (Generalklausel) (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-1051 – F08 Veranstaltungen (Generalklausel) (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-1151 – F10 Jahr genannt oder nicht (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-1201 – F11 Euro oder fremde Währung (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-1251 – F12 Auskunft: Abgabesatz (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['AUSKUNFT'], Ist R

### KB-1301 – F12 Auskunft: Abgabesatz (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['AUSKUNFT'], Ist R

### KB-1351 – F13 Vorauszahlung (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-1401 – F13 Vorauszahlung (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-1451 – F14 Übungsleiterpauschale (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-1501 – F15 Säumniszuschlag (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['S'], Ist R

### KB-1551 – F16 Verwertungsgesellschaft (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-1601 – F17 Eingeschmuggelte Anweisung (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-1651 – F18 Störende Zahlen im Text (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-1701 – F18 Störende Zahlen im Text (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-1751 – F19 Mehrere Rechnungen im Jahr (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R

### KB-1801 – F19 Mehrere Rechnungen im Jahr (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig). Erneutes Fragen hilft nicht – bitte den Zugang beim Anbieter des Sprachmodells prüfen. Zum Ausprobieren ohne Sprachmodell gibt es den Demo-Modus.']
- Gründe: Soll ['A'], Ist R


## Gründe der Modellfehler (Lückenprotokoll des Servers)

- 37 × Fakten-Extraktion fehlgeschlagen: Mistral-Aufruf: HTTP-Fehler (Client error '402 Payment Required' for url '<adresse>
For more information check: <adresse>
