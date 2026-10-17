# Chatbot direkt getestet – 2026-10-11 (Chatbot direkt (Browser) – FakeLLM (Demo-Modus, Ersatzmodell))

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Soll-Werte: `aufgaben/audit/testfall_alltag_4.json`. Code-Stand `bebfdff`.
Jeder Fall wurde an der echten Weboberfläche gespielt: tippen, Knöpfe klicken, Fakten bestätigen.

- Fälle: 4, Dauer 8 s
- RICHTIG: 1, NACHGEFRAGT: 3, **FALSCH: 0**, FEHLER: 0

| Fall | Fallgruppe | Soll | Ist | Bewertung | Rückfragen | Dauer |
|---|---|---|---|---|---|---|
| F1 | Werbefotografie an Unternehmen (Eigenwerbung) | A | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0 | 0.5 s |
| F2 | Publizist an Verlag | A | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0 | 0.6 s |
| F3 | Agentur-Mischrechnung an Werbekunden (Vertragsstufen) | N | Nicht abgabepflichtig (Vorschlag) | **NACHGEFRAGT** | 1 | 0.6 s |
| F4 | Hochzeitsfotografie an Privatpersonen (Anti-Alarm) | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 0.4 s |

## Abweichungen

### F1 – Werbefotografie an Unternehmen (Eigenwerbung) (NACHGEFRAGT)
- Ist: Grenzfall → Steuerberater entscheidet; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | 'Ja, das stimmt' -> Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['A'], Ist G

### F2 – Publizist an Verlag (NACHGEFRAGT)
- Ist: Grenzfall → Steuerberater entscheidet; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | 'Ja, das stimmt' -> Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['A'], Ist G

### F3 – Agentur-Mischrechnung an Werbekunden (Vertragsstufen) (NACHGEFRAGT)
- Ist: Nicht abgabepflichtig (Vorschlag); Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | Knopf 'Eigenwerbung' -> Faktenbestätigung nötig | 'Ja, das stimmt' -> Nicht abgabepflichtig (Vorschlag)
- Gründe: 1 Rückfrage(n), nötig laut Soll höchstens 0


## Dialoge (Soll je Schritt von Hand vergleichen)

### dialog:testprotokoll_1110 (KSK_Testprotokoll_Claude_Code.pdf (Nutzer, 11.10.2026))

| Schritt | Eingabe | Ergebnis | Rückfrage / Antwort (gekürzt) | Soll |
|---|---|---|---|---|
| 1 | Wir sind ein Handwerksbetrieb und haben 2026 ausschließlich für unsere eigene We | Faktenbestätigung nötig | Ich habe verstanden: Jahr: 2026; Leistung: Grafik/Design; Art des Auftraggebers: Eigenwerbung; Position 1: 900,00 € „Eine selbstständige Grafikerin, Einzelunter | Faktenbestätigung ohne Rückfrage nach Eigenwerbung oder Rechtsform. Positionen 300 € Druckkosten + 900 € Grafik (natürliche Person, dieselbe Auftragnehmerin) + 800 € Foto-GmbH; Rechnung der Grafikerin 1.200 €. Keine doppelte Zählung der 300 €. |
| 2 | Wir betreiben ausschließlich Eigenwerbung. Die Grafikerin ist eine natürliche Pe | Faktenbestätigung nötig | Ich habe verstanden: Jahr: 2026; Leistung: Grafik/Design; Art des Auftraggebers: Eigenwerbung; Position 1: 900,00 € „Die Rechnung der Grafikerin beträgt insgesa | Nichts geht verloren; Eigenwerbung und Rechtsform werden nicht erneut gefragt. |
| 3 | Die 300 Euro sind Druckkosten innerhalb der Rechnung der Grafikerin. Bitte als D | Rückfrage nötig | Die Aufteilung der Rechnung von Auftragnehmer 1 ist unklar: Ein Teilbetrag ist so hoch wie die ganze Rechnung. Bitte nennen Sie den Rechnungsbetrag und die dari | Bezeichnung 'Druckkosten' wird angezeigt, keine erfundene Rolle; übrige Angaben unverändert. |
| 4 | Korrektur: Die gesamte Rechnung der Grafikerin beträgt 900 Euro netto statt 1.20 | Rückfrage nötig | Die Aufteilung der Rechnung von Auftragnehmer 1 ist unklar: Ein Teilbetrag ist so hoch wie die ganze Rechnung. Bitte nennen Sie den Rechnungsbetrag und die dari | Korrektur: Rechnung der Grafikerin 900 €, darin 300 € Druckkosten, Rest 600 € (rechnet der Kern). Foto-GmbH 800 € unverändert. Alte Bestätigung ungültig. |
| 5 | Ich habe dieselbe korrigierte Rechnung der Grafikerin versehentlich zweimal erfa | Rückfrage nötig | Welche Rechtsform hat der Auftragnehmer bei Ich habe dieselbe korrigierte Rechnung der Grafikerin versehentlich zweimal erfasst. Es gibt tatsächlich nur eine Re | Keine doppelte Rechnung; weiterhin 900 € einschließlich 300 €. |
| 6 | Mein Kollege sagt, die Auftragnehmerin der Fotorechnung über 800 Euro sei Einzel | Rückfrage nötig | Welche Rechtsform hat der Auftragnehmer bei in Rechnung (natürliche Person, GbR, GmbH/UG/AG, KG/OHG, Verein oder im Ausland ansässig)? | Gezielte Widerspruchsfrage zur Rechtsform der Fotorechnung (Knöpfe für beide Werte und 'noch ungeklärt'); keine Bewertung, kein stilles Weiterrechnen mit 'Einzelunternehmerin'. |
| 7 | Neuer, unabhängiger Fall: Ein Verein hat für zwei Veranstaltungen insgesamt drei | Rückfrage nötig | Ist der Auftraggeber in diesem Fall eigenwerbend tätig (Werbung für das eigene Unternehmen), ein typischer Verwerter (z. B. Werbeagentur, Verlag, Galerie, die f | Neuer, getrennter Fall ohne Daten des alten Falls. Jahr, Rechtsformen und Einnahmeabsicht 'ausdrücklich unbekannt'; keine geratenen Werte (z. B. nicht 'Verein' als Rechtsform der Musiker). |
| 8 | Der neue Vereinsfall betrifft 2026. Alle anderen bisher unbekannten Angaben blei | Rückfrage nötig | Ist der Auftraggeber in diesem Fall eigenwerbend tätig (Werbung für das eigene Unternehmen), ein typischer Verwerter (z. B. Werbeagentur, Verlag, Galerie, die f | Jahr 2026 übernommen; unbekannte Angaben werden nicht erneut gefragt. |
| 9 | Das ist noch ungeklärt. Bitte weder Ja noch Nein annehmen. Welche Angaben sind f | Rückfrage nötig | **Ergebnis (Vorschlag):** Rückfrage nötig **Bisher erfasst:** – Jahr: 2026 – Leistung: Musik – Auftragnehmer: Verein – Position 1: 1.800,00 €, Verein, Leistung: | Übersicht: was erfasst ist, was offen ist; Bewertung zurückgestellt; keine Sackgasse, kein Modellaufruf nötig. |

### dialog:livetest2 (Livetest des Nutzers im Codespace (10.10.2026))

| Schritt | Eingabe | Ergebnis | Rückfrage / Antwort (gekürzt) | Soll |
|---|---|---|---|---|
| 1 | Wir haben einen Grafiker für Werbung bezahlt. | Rückfrage nötig | In welchem Kalenderjahr ist der Sachverhalt zu bewerten? |  |
| 2 | Knopf „2026“ | Rückfrage nötig | Um welchen Betrag geht es, und wofür genau (z. B. Honorar, Nebenkosten, Reisekosten)? |  |
| 3 | Knopf auftragnehmer_typ='GmbH_UG_AG' | **nicht angeboten** | – |  |
| 4 | 2000 | Rückfrage nötig | Ist der Auftraggeber in diesem Fall eigenwerbend tätig (Werbung für das eigene Unternehmen), ein typischer Verwerter (z. B. Werbeagentur, Verlag, Galerie, die f | '2000' ohne Einheit wird der offenen Betragsfrage zugeordnet (2.000 €), nicht als Jahr gelesen. |
| 5 | Knopf „Veranstalter (Generalklausel)“ | Rückfrage nötig | Ist der Auftragnehmer eine natürliche Person, eine GbR, eine GmbH/UG/AG, eine KG/OHG, ein Verein oder im Ausland ansässig? |  |
| 6 | Knopf einnahmeabsicht=True | **nicht angeboten** | – |  |
| 7 | 2 | Rückfrage nötig | Ist der Auftragnehmer eine natürliche Person, eine GbR, eine GmbH/UG/AG, eine KG/OHG, ein Verein oder im Ausland ansässig? | '2' wird als Zahl der Veranstaltungen übernommen; danach Faktenbestätigung mit Jahr 2026, GmbH, 2.000 €, Generalklausel, Einnahmeabsicht ja, 2 Veranstaltungen. |
| 8 | ander fall | Rückfrage nötig | In welchem Kalenderjahr ist der Sachverhalt zu bewerten? | 'ander fall' startet einen neuen Fall ohne alte Daten und fragt nach dem Jahr. |

