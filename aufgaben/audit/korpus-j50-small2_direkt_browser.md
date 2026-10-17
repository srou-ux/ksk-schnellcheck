# Chatbot direkt getestet – 2026-10-17 (Chatbot direkt (Browser) – Mistral (EU))

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Soll-Werte: `aufgaben/audit/korpus_beispiele.json`. Code-Stand `a3e41e2`.
Jeder Fall wurde an der echten Weboberfläche gespielt: tippen, Knöpfe klicken, Fakten bestätigen.

- Fälle: 37 (Teil 1/1, jeder 50. Fall), Dauer 112 s
- RICHTIG: 32, NACHGEFRAGT: 3, **FALSCH: 0**, FEHLER: 2

| Fall | Fallgruppe | Soll | Ist | Bewertung | Rückfragen | Dauer |
|---|---|---|---|---|---|---|
| KB-0001 | F01 Eigenwerbung: Schwelle (Fassung B) | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 3.2 s |
| KB-0051 | F01 Eigenwerbung: Schwelle (Fassung B) | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.4 s |
| KB-0101 | F01 Eigenwerbung: Schwelle (Fassung B) | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.0 s |
| KB-0151 | F01 Eigenwerbung: Schwelle (Fassung B) | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 3.2 s |
| KB-0201 | F01 Eigenwerbung: Schwelle (Fassung B) | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.9 s |
| KB-0251 | F02 Eigenwerbung: Grenze 450 € (Fassung A) | G | Grenzfall → Steuerberater entscheidet | **RICHTIG** | 0 | 2.6 s |
| KB-0301 | F02 Eigenwerbung: Grenze 450 € (Fassung A) | G | Grenzfall → Steuerberater entscheidet | **RICHTIG** | 0 | 2.9 s |
| KB-0351 | F03 Rechtsform des Empfängers | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 1 | 2.6 s |
| KB-0401 | F03 Rechtsform des Empfängers | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.6 s |
| KB-0451 | F03 Rechtsform des Empfängers | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 3.2 s |
| KB-0501 | F04 Umsatzsteuer gesondert ausgewiesen | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.4 s |
| KB-0551 | F04 Umsatzsteuer gesondert ausgewiesen | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 2.4 s |
| KB-0601 | F05 Typischer Verwerter oder Eigenwerbung | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.4 s |
| KB-0651 | F05 Typischer Verwerter oder Eigenwerbung | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.0 s |
| KB-0701 | F05 Typischer Verwerter oder Eigenwerbung | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.4 s |
| KB-0751 | F06 Künstlerisch oder nicht | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.2 s |
| KB-0801 | F06 Künstlerisch oder nicht | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.2 s |
| KB-0851 | F06 Künstlerisch oder nicht | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.1 s |
| KB-0901 | F07 Privatperson oder Unternehmen | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.5 s |
| KB-0951 | F08 Veranstaltungen (Generalklausel) | A | Rückfrage nötig | **FEHLER** | 0 | 21.2 s |
| KB-1001 | F08 Veranstaltungen (Generalklausel) | A | Rückfrage nötig | **NACHGEFRAGT** | 0 | 4.2 s |
| KB-1051 | F08 Veranstaltungen (Generalklausel) | A | Rückfrage nötig | **FEHLER** | 0 | 5.0 s |
| KB-1101 | F09 Reisekosten mit oder ohne Nachweis | A/R | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0 | 2.4 s |
| KB-1151 | F10 Jahr genannt oder nicht | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.3 s |
| KB-1201 | F11 Euro oder fremde Währung | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.1 s |
| KB-1251 | F12 Auskunft: Abgabesatz | AUSKUNFT | Auskunft aus dem Regelwerk | **RICHTIG** | 0 | 1.5 s |
| KB-1301 | F12 Auskunft: Abgabesatz | AUSKUNFT | Auskunft aus dem Regelwerk | **RICHTIG** | 0 | 2.0 s |
| KB-1351 | F13 Vorauszahlung | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 1.9 s |
| KB-1401 | F13 Vorauszahlung | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 1.6 s |
| KB-1451 | F14 Übungsleiterpauschale | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.6 s |
| KB-1501 | F15 Säumniszuschlag | S | Säumniszuschlag (Vorschlag) | **RICHTIG** | 0 | 1.9 s |
| KB-1551 | F16 Verwertungsgesellschaft | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.2 s |
| KB-1601 | F17 Eingeschmuggelte Anweisung | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.4 s |
| KB-1651 | F18 Störende Zahlen im Text | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.6 s |
| KB-1701 | F18 Störende Zahlen im Text | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.5 s |
| KB-1751 | F19 Mehrere Rechnungen im Jahr | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.7 s |
| KB-1801 | F19 Mehrere Rechnungen im Jahr | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 2.2 s |

## Abweichungen

### KB-0551 – F04 Umsatzsteuer gesondert ausgewiesen (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Aufteilung der Rechnung von Auftragnehmer 1 ist unklar: Die Teilbeträge sind größer als der Rechnungsbetrag. Bitte nennen Sie den Rechnungsbetrag und die darin enthaltenen Teilbeträge.']
- Gründe: Soll ['A'], Ist R

### KB-0951 – F08 Veranstaltungen (Generalklausel) (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1001 – F08 Veranstaltungen (Generalklausel) (NACHGEFRAGT)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Wie viele einschlägige Veranstaltungen gab es in dem Jahr?']
- Gründe: Soll ['A'], Ist R

### KB-1051 – F08 Veranstaltungen (Generalklausel) (FEHLER)
- Ist: Rückfrage nötig; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | offen: ['Die Antwort des Sprachmodells konnte nicht verarbeitet werden. Bitte stellen Sie Ihre Frage erneut.']
- Gründe: Ist: Rückfrage nötig

### KB-1101 – F09 Reisekosten mit oder ohne Nachweis (NACHGEFRAGT)
- Ist: Grenzfall → Steuerberater entscheidet; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | Bestätigt: Jahr: 2025; Ihr Unternehmen (Tätigkeit): Steuerkanzlei; Zweck dieses Auftrags: Werbung oder Öffentlichkeitsarbeit für das eigene Unternehmen (vom Sprachmodell gelesen – bitte prüfen); Art des Auftraggebers: Eigenwerbung; Position 1: 699,00 € „Fotos für die Webseite“, natürliche Person, Leistung: Fotografie (Werbe-, Foto-Design, künstlerische Fotografie) (künstlerisch/publizistisch); Position 2: 80,00 € „Fahrtkosten“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Rechnung von Auftragnehmer 1: 779,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren); Alle Positionen vom selben Auftragnehmer: ja; Belege vorhanden: nein | 'Ja, das stimmt' -> Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['A', 'R'], Ist G


## Gründe der Modellfehler (Lückenprotokoll des Servers)

- 1 × Fakten-Extraktion fehlgeschlagen: Modell-JSON enthaelt Schluessel ausserhalb des Schemas: positionen": [{"auftragnehmer_nr": 1, "betrag": 1800, "rolle": "honorar", "bezeichnung": "Zahlung an freie Mus
- 1 × Fakten-Extraktion fehlgeschlagen: Modell-JSON enthaelt Schluessel ausserhalb des Schemas: , , positionen": [{"auftragnehmer_nr": 1, "betrag": 1000.01, "rolle": "honorar", "bezeichnung": "Zahlung an fr
