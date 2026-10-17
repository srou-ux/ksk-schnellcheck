# Chatbot direkt getestet – 2026-10-16 (Chatbot direkt (Browser) – Mistral (EU))

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Soll-Werte: `aufgaben/audit/korpus_beispiele.json`. Code-Stand `ed83086`.
Jeder Fall wurde an der echten Weboberfläche gespielt: tippen, Knöpfe klicken, Fakten bestätigen.

- Fälle: 37 (Teil 1/1, jeder 50. Fall), Dauer 21 s
- RICHTIG: 0, NACHGEFRAGT: 0, **FALSCH: 0**, FEHLER: 37

| Fall | Fallgruppe | Soll | Ist | Bewertung | Rückfragen | Dauer |
|---|---|---|---|---|---|---|
| KB-0001 | F01 Eigenwerbung: Schwelle (Fassung B) | A | Rückfrage nötig | **FEHLER** | 0 | 0.8 s |
| KB-0051 | F01 Eigenwerbung: Schwelle (Fassung B) | A | Rückfrage nötig | **FEHLER** | 0 | 0.6 s |
| KB-0101 | F01 Eigenwerbung: Schwelle (Fassung B) | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-0151 | F01 Eigenwerbung: Schwelle (Fassung B) | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-0201 | F01 Eigenwerbung: Schwelle (Fassung B) | A | Rückfrage nötig | **FEHLER** | 0 | 0.6 s |
| KB-0251 | F02 Eigenwerbung: Grenze 450 € (Fassung A) | G | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-0301 | F02 Eigenwerbung: Grenze 450 € (Fassung A) | G | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-0351 | F03 Rechtsform des Empfängers | A | Rückfrage nötig | **FEHLER** | 0 | 0.6 s |
| KB-0401 | F03 Rechtsform des Empfängers | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-0451 | F03 Rechtsform des Empfängers | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-0501 | F04 Umsatzsteuer gesondert ausgewiesen | A | Rückfrage nötig | **FEHLER** | 0 | 1.0 s |
| KB-0551 | F04 Umsatzsteuer gesondert ausgewiesen | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-0601 | F05 Typischer Verwerter oder Eigenwerbung | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-0651 | F05 Typischer Verwerter oder Eigenwerbung | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-0701 | F05 Typischer Verwerter oder Eigenwerbung | A | Rückfrage nötig | **FEHLER** | 0 | 1.0 s |
| KB-0751 | F06 Künstlerisch oder nicht | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-0801 | F06 Künstlerisch oder nicht | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-0851 | F06 Künstlerisch oder nicht | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-0901 | F07 Privatperson oder Unternehmen | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-0951 | F08 Veranstaltungen (Generalklausel) | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-1001 | F08 Veranstaltungen (Generalklausel) | A | Rückfrage nötig | **FEHLER** | 0 | 0.7 s |
| KB-1051 | F08 Veranstaltungen (Generalklausel) | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-1101 | F09 Reisekosten mit oder ohne Nachweis | A/R | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-1151 | F10 Jahr genannt oder nicht | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-1201 | F11 Euro oder fremde Währung | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-1251 | F12 Auskunft: Abgabesatz | AUSKUNFT | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-1301 | F12 Auskunft: Abgabesatz | AUSKUNFT | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-1351 | F13 Vorauszahlung | A | Rückfrage nötig | **FEHLER** | 0 | 0.6 s |
| KB-1401 | F13 Vorauszahlung | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-1451 | F14 Übungsleiterpauschale | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-1501 | F15 Säumniszuschlag | S | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-1551 | F16 Verwertungsgesellschaft | A | Rückfrage nötig | **FEHLER** | 0 | 0.6 s |
| KB-1601 | F17 Eingeschmuggelte Anweisung | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-1651 | F18 Störende Zahlen im Text | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-1701 | F18 Störende Zahlen im Text | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-1751 | F19 Mehrere Rechnungen im Jahr | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |
| KB-1801 | F19 Mehrere Rechnungen im Jahr | A | Rückfrage nötig | **FEHLER** | 0 | 0.5 s |

## Abweichungen

### KB-0001 – F01 Eigenwerbung: Schwelle (Fassung B) (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0051 – F01 Eigenwerbung: Schwelle (Fassung B) (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0101 – F01 Eigenwerbung: Schwelle (Fassung B) (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0151 – F01 Eigenwerbung: Schwelle (Fassung B) (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0201 – F01 Eigenwerbung: Schwelle (Fassung B) (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0251 – F02 Eigenwerbung: Grenze 450 € (Fassung A) (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0301 – F02 Eigenwerbung: Grenze 450 € (Fassung A) (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0351 – F03 Rechtsform des Empfängers (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0401 – F03 Rechtsform des Empfängers (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0451 – F03 Rechtsform des Empfängers (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0501 – F04 Umsatzsteuer gesondert ausgewiesen (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0551 – F04 Umsatzsteuer gesondert ausgewiesen (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0601 – F05 Typischer Verwerter oder Eigenwerbung (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0651 – F05 Typischer Verwerter oder Eigenwerbung (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0701 – F05 Typischer Verwerter oder Eigenwerbung (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0751 – F06 Künstlerisch oder nicht (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0801 – F06 Künstlerisch oder nicht (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0851 – F06 Künstlerisch oder nicht (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0901 – F07 Privatperson oder Unternehmen (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-0951 – F08 Veranstaltungen (Generalklausel) (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1001 – F08 Veranstaltungen (Generalklausel) (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1051 – F08 Veranstaltungen (Generalklausel) (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1101 – F09 Reisekosten mit oder ohne Nachweis (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1151 – F10 Jahr genannt oder nicht (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1201 – F11 Euro oder fremde Währung (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1251 – F12 Auskunft: Abgabesatz (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1301 – F12 Auskunft: Abgabesatz (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1351 – F13 Vorauszahlung (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1401 – F13 Vorauszahlung (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1451 – F14 Übungsleiterpauschale (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1501 – F15 Säumniszuschlag (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1551 – F16 Verwertungsgesellschaft (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1601 – F17 Eingeschmuggelte Anweisung (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1651 – F18 Störende Zahlen im Text (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1701 – F18 Störende Zahlen im Text (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1751 – F19 Mehrere Rechnungen im Jahr (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1801 – F19 Mehrere Rechnungen im Jahr (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig


## Gründe der Modellfehler (Lückenprotokoll des Servers)

- 37 × Fakten-Extraktion fehlgeschlagen: Mistral-Aufruf: HTTP-Fehler (Client error '402 Payment Required' for url '<adresse>
For more information check: <adresse>
