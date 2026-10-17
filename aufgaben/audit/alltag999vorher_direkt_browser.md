# Chatbot direkt getestet – 2026-10-11 (Chatbot direkt (Browser) – Mistral (EU))

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Soll-Werte: `aufgaben/audit/testfall_alltag_999.json`. Code-Stand `e6d09f6`.
Jeder Fall wurde an der echten Weboberfläche gespielt: tippen, Knöpfe klicken, Fakten bestätigen.

- Fälle: 1, Dauer 65 s
- RICHTIG: 0, NACHGEFRAGT: 0, **FALSCH: 1**, FEHLER: 0

| Fall | Fallgruppe | Soll | Ist | Bewertung | Rückfragen | Dauer |
|---|---|---|---|---|---|---|
| A-999 | Viel-Künstler-Sammelrechnung an Messe-Veranstalterin | A | Grenzfall → Steuerberater entscheidet | **FALSCH** | 1 | 16.2 s |

## Abweichungen

### A-999 – Viel-Künstler-Sammelrechnung an Messe-Veranstalterin (FALSCH)
- Ist: Grenzfall → Steuerberater entscheidet; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Rückfrage nötig | Knopf 'Typischer Verwerter' -> Faktenbestätigung nötig | 'Ja, das stimmt' -> Grenzfall → Steuerberater entscheidet
- Gründe: verbotener Text in der Antwort: 'Satz 1 Nr. 7'; 1 Rückfrage(n), nötig laut Soll höchstens 0


## Dialoge (Soll je Schritt von Hand vergleichen)

### dialog:testprotokoll_1110 (KSK_Testprotokoll_Claude_Code.pdf (Nutzer, 11.10.2026))

| Schritt | Eingabe | Ergebnis | Rückfrage / Antwort (gekürzt) | Soll |
|---|---|---|---|---|
| 1 | Wir sind ein Handwerksbetrieb und haben 2026 ausschließlich für unsere eigene We | Faktenbestätigung nötig | Bestätigung: Jahr: 2026; Leistung: Grafik/Design und Fotografie; Art des Auftraggebers: Eigenwerbung; Position 1: 300,00 € „Druckkosten“, natürliche Person, Leistung: Nachträgliche Vervielfältigung oder Druck nach Abschluss der künstlerischen Leistung (nicht künstlerisch), Auftragnehmer 1; Position 2: 900,00 € „Grafikdesign-Leistung (Restbetrag)“, natürliche Person, Leistung: Grafikdesign, Layout, Logo, Corporate Des | Faktenbestätigung ohne Rückfrage nach Eigenwerbung oder Rechtsform. Positionen 300 € Druckkosten + 900 € Grafik (natürliche Person, dieselbe Auftragnehmerin) + 800 € Foto-GmbH; Rechnung der Grafikerin 1.200 €. Keine doppelte Zählung der 300 €. |
| 2 | Wir betreiben ausschließlich Eigenwerbung. Die Grafikerin ist eine natürliche Pe | Faktenbestätigung nötig | Bestätigung: Jahr: 2026; Leistung: Grafik/Design und Fotografie; Art des Auftraggebers: Eigenwerbung; Position 1: 300,00 € „Druckkosten“, natürliche Person, Leistung: Nachträgliche Vervielfältigung oder Druck nach Abschluss der künstlerischen Leistung (nicht künstlerisch), Auftragnehmer 1; Position 2: 900,00 € „Grafikdesign-Leistung (Restbetrag)“, natürliche Person, Leistung: Grafikdesign, Layout, Logo, Corporate Des | Nichts geht verloren; Eigenwerbung und Rechtsform werden nicht erneut gefragt. |
| 3 | Die 300 Euro sind Druckkosten innerhalb der Rechnung der Grafikerin. Bitte als D | Faktenbestätigung nötig | Bestätigung: Jahr: 2026; Leistung: Grafik/Design und Fotografie; Art des Auftraggebers: Eigenwerbung; Position 1: 300,00 € „Druckkosten“, natürliche Person, Leistung: Nachträgliche Vervielfältigung oder Druck nach Abschluss der künstlerischen Leistung (nicht künstlerisch), Auftragnehmer 1; Position 2: 900,00 € „Grafikdesign-Leistung (Restbetrag)“, natürliche Person, Leistung: Grafikdesign, Layout, Logo, Corporate Des | Bezeichnung 'Druckkosten' wird angezeigt, keine erfundene Rolle; übrige Angaben unverändert. |
| 4 | Korrektur: Die gesamte Rechnung der Grafikerin beträgt 900 Euro netto statt 1.20 | Faktenbestätigung nötig | Bestätigung: Jahr: 2026; Leistung: Grafik/Design und Fotografie; Art des Auftraggebers: Eigenwerbung; Position 1: 300,00 € „Druckkosten“, natürliche Person, Leistung: Nachträgliche Vervielfältigung oder Druck nach Abschluss der künstlerischen Leistung (nicht künstlerisch), Auftragnehmer 1; Position 2: 600,00 € „Grafikdesign-Leistung (Restbetrag)“, natürliche Person, Leistung: Grafikdesign, Layout, Logo, Corporate Des | Korrektur: Rechnung der Grafikerin 900 €, darin 300 € Druckkosten, Rest 600 € (rechnet der Kern). Foto-GmbH 800 € unverändert. Alte Bestätigung ungültig. |
| 5 | Ich habe dieselbe korrigierte Rechnung der Grafikerin versehentlich zweimal erfa | Faktenbestätigung nötig | Bestätigung: Jahr: 2026; Leistung: Grafik/Design und Fotografie; Art des Auftraggebers: Eigenwerbung; Position 1: 300,00 € „Druckkosten“, natürliche Person, Leistung: Nachträgliche Vervielfältigung oder Druck nach Abschluss der künstlerischen Leistung (nicht künstlerisch), Auftragnehmer 1; Position 2: 600,00 € „Grafikdesign-Leistung (Restbetrag)“, natürliche Person, Leistung: Grafikdesign, Layout, Logo, Corporate Des | Keine doppelte Rechnung; weiterhin 900 € einschließlich 300 €. |
| 6 | Mein Kollege sagt, die Auftragnehmerin der Fotorechnung über 800 Euro sei Einzel | Rückfrage nötig | Widersprüchliche Angaben zu Rechtsform des Auftragnehmers bei Position 3 „Fotografie-Leistung“: natürliche Person oder GmbH/UG/AG. Welche Angabe stimmt? | Gezielte Widerspruchsfrage zur Rechtsform der Fotorechnung (Knöpfe für beide Werte und 'noch ungeklärt'); keine Bewertung, kein stilles Weiterrechnen mit 'Einzelunternehmerin'. |
| 7 | Neuer, unabhängiger Fall: Ein Verein hat für zwei Veranstaltungen insgesamt drei | Rückfrage nötig | Ist der Auftraggeber in diesem Fall eigenwerbend tätig (Werbung für das eigene Unternehmen), ein typischer Verwerter (z. B. Werbeagentur, Verlag, Galerie, die für andere verwertet) oder Veranstalter im Sinne der Generalklausel (z. B. nur gelegentliche Veranstaltungen)? Oder ist der Auftraggeber eine Privatperson (kein Unternehmen)? | Neuer, getrennter Fall ohne Daten des alten Falls. Jahr, Rechtsformen und Einnahmeabsicht 'ausdrücklich unbekannt'; keine geratenen Werte (z. B. nicht 'Verein' als Rechtsform der Musiker). |
| 8 | Der neue Vereinsfall betrifft 2026. Alle anderen bisher unbekannten Angaben blei | Rückfrage nötig | Ist der Auftraggeber in diesem Fall eigenwerbend tätig (Werbung für das eigene Unternehmen), ein typischer Verwerter (z. B. Werbeagentur, Verlag, Galerie, die für andere verwertet) oder Veranstalter im Sinne der Generalklausel (z. B. nur gelegentliche Veranstaltungen)? Oder ist der Auftraggeber eine Privatperson (kein Unternehmen)? | Jahr 2026 übernommen; unbekannte Angaben werden nicht erneut gefragt. |
| 9 | Das ist noch ungeklärt. Bitte weder Ja noch Nein annehmen. Welche Angaben sind f | Rückfrage nötig | **Ergebnis (Vorschlag):** Rückfrage nötig **Bisher erfasst:** – Jahr: 2026 – Leistung: Musik – Gesamtbetrag (Aufteilung auf Rechnungen unbekannt): 1.800,00 €, Leistung: Musik: Komposition, Jingle, Arrangement, Musiker, Sänger, Audio-Design, DJ (künstlerisch/publizistisch) – Veranstaltungen: 2 **Offen:** – Einnahmeabsicht: ausdrücklich unbekannt – Rechtsform des Auftragnehmers: ausdrücklich unbekannt – Art des Auftrag | Übersicht: was erfasst ist, was offen ist; Bewertung zurückgestellt; keine Sackgasse, kein Modellaufruf nötig. |

### dialog:livetest2 (Livetest des Nutzers im Codespace (10.10.2026))

| Schritt | Eingabe | Ergebnis | Rückfrage / Antwort (gekürzt) | Soll |
|---|---|---|---|---|
| 1 | Wir haben einen Grafiker für Werbung bezahlt. | Rückfrage nötig | In welchem Kalenderjahr ist der Sachverhalt zu bewerten? |  |
| 2 | Knopf „2026“ | Rückfrage nötig | Um welchen Betrag geht es, und wofür genau (z. B. Honorar, Nebenkosten, Reisekosten)? |  |
| 3 | Knopf auftragnehmer_typ='GmbH_UG_AG' | (noch nicht gefragt, wird später geklickt) | – | |
| 4 | 2000 | Rückfrage nötig | Ist der Auftraggeber in diesem Fall eigenwerbend tätig (Werbung für das eigene Unternehmen), ein typischer Verwerter (z. B. Werbeagentur, Verlag, Galerie, die für andere verwertet) oder Veranstalter im Sinne der Generalklausel (z. B. nur gelegentliche Veranstaltungen)? Oder ist der Auftraggeber eine Privatperson (kein Unternehmen)? | '2000' ohne Einheit wird der offenen Betragsfrage zugeordnet (2.000 €), nicht als Jahr gelesen. |
| 5 | Knopf „Veranstalter (Generalklausel)“ | Rückfrage nötig | Ist der Auftragnehmer eine natürliche Person, eine GbR, eine GmbH/UG/AG, eine KG/OHG, ein Verein oder im Ausland ansässig? |  |
| 3 (später) | Knopf „GmbH/UG/AG“ | Rückfrage nötig | Wie viele einschlägige Veranstaltungen gab es in dem Jahr? |  |
| 6 | Knopf einnahmeabsicht=True | (noch nicht gefragt, wird später geklickt) | – | |
| 7 | 2 | Rückfrage nötig | Wurden mit der/den Veranstaltung(en) Einnahmen erzielt oder beabsichtigt? | '2' wird als Zahl der Veranstaltungen übernommen; danach Faktenbestätigung mit Jahr 2026, GmbH, 2.000 €, Generalklausel, Einnahmeabsicht ja, 2 Veranstaltungen. |
| 6 (später) | Knopf „ja“ | Faktenbestätigung nötig | Bestätigung: Jahr: 2026; Leistung: Grafik/Design; Art des Auftraggebers: Veranstalter (Generalklausel); Auftragnehmer: GmbH/UG/AG; Gesamtbetrag (Aufteilung auf Rechnungen unbekannt): 2.000,00 €, GmbH/UG/AG, Leistung: Grafikdesign, Layout, Logo, Corporate Design, Kommunikationsdesign (künstlerisch/publizistisch); Veranstaltungen: 2; Einnahmeabsicht: ja |  |
| 8 | ander fall | Rückfrage nötig | In welchem Kalenderjahr ist der Sachverhalt zu bewerten? | 'ander fall' startet einen neuen Fall ohne alte Daten und fragt nach dem Jahr. |

