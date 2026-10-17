# Prüfkatalog Stufe 1 – Lauf 2026-10-11 (Mistral (mistral-large-latest) – ROH, ohne KSK-Assistent (Vergleich))

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Soll-Werte: `aufgaben/audit/pruefkatalog.json`.

**Ergebnis: NICHT BESTANDEN**

- Fälle: 4, Dauer gesamt 13 s
- RICHTIG: 1, NACHGEFRAGT: 0, **FALSCH: 2**, FEHLER: 1
- Quote richtig bei Fällen mit sicherem Soll: 1 von 4 = 25 % (Ziel ≥ 90 %)
- Ziel Stufe 1: 0 FALSCH, 0 FEHLER, Quote ≥ 90 %.

| Fall | Fallgruppe | Soll | Ist | Bewertung | Dauer |
|---|---|---|---|---|---|
| F1 | Werbefotografie an Unternehmen (Eigenwerbung) | A | Abgabepflichtig (Vorschlag) | **FALSCH** | 4.1 s |
| F2 | Publizist an Verlag | A | Ausnahme | **FEHLER** | 3.3 s |
| F3 | Agentur-Mischrechnung an Werbekunden (Vertragsstufen) | N | Abgabepflichtig (Vorschlag) | **FALSCH** | 3.5 s |
| F4 | Hochzeitsfotografie an Privatpersonen (Anti-Alarm) | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 2.1 s |

## Abweichungen im Einzelnen

### F1 – Werbefotografie an Unternehmen (Eigenwerbung) (FALSCH)
- Frage: Mein Mandant ist die Steinbach Naturstein GmbH (B2B-Handel). Sie hat für ihre Image-Kampagne diese Rechnung erhalten:
Rechnungsteller: Jana Loots, Fotografin (freischaffend, Einzelunternehmerin), Rechnung F1-2026-88 vom 12.06.2026. Zahlung: „Mit Dank erhalten am 20.06.2026“ (laut Rechnung).
Pos. 01 Produktfotografie Steinbruch, halbtägiges Shooting inkl. Konzeption: 1.800,00 € netto
Pos. 02 Bildretusche und Farbkorrektur (12 Motive): 220,00 € netto
Pos. 03 Nutzungsrechte Kampagne, 24 Monate, Web + Print: 450,00 € netto
Nettosumme: 2.470,00 €, USt 19 %: 469,30 €, Rechnungsbetrag: 2.939,30 €.
Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '121.03'} (Referenz: Soll der Testdatei: alle 3 Positionen einbezogen (Retusche als Nebenleistung), 2.470 € × 4,9 % = 121,03 €, keine Rückfragen, Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 2470.0, Abgabe 111.15
- Fakten (System) bzw. Fundstellen (roh): Fundstellen laut Modell: § 24 Abs. 1 KSVG; § 25 KSVG (Bemessungsgrundlage); KSK-Info 2021/1 (Abgrenzung künstlerischer Leistungen); BFH-Urteil vom 11.07.2018 (XI R 26/16)
- Verlauf: Antwort 1: Abgabepflichtig (Vorschlag)
- Gründe: abgabe: Soll 121.03, Ist 111.15

### F2 – Publizist an Verlag (FEHLER)
- Frage: Mein Mandant ist die Rheinland Verlag GmbH & Co. KG (Fachmagazin „Stein & Bau“). Er hat diese Rechnung erhalten:
Rechnungsteller: Thomas Meyer, freier Journalist, Rechnung TM-2026-41 vom 03.09.2026. Zahlung: 30 Tage Ziel.
Pos. 01 Fachartikel „Naturstein im modernen Innenausbau“, 6 Seiten, einmalige Nutzung: 1.400,00 € netto
Pos. 02 Recherche-Pauschale (Fahrt, Literatur) lt. Vertrag: 350,00 € netto
Nettosumme: 1.750,00 €, USt 19 %: 332,50 €, Rechnungsbetrag: 2.082,50 €.
Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '85.75'} (Referenz: Soll der Testdatei: Verlag typischer Verwerter ohne Grenze; Artikel und Recherche-Pauschale einbezogen, 1.750 € × 4,9 % = 85,75 €, Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Ausnahme; Kern: Bemessungsgrundlage 2470.0, Abgabe 111.15
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: –
- Gründe: JSONDecodeError: Expecting ',' delimiter: line 4 column 21 (char 89)

### F3 – Agentur-Mischrechnung an Werbekunden (Vertragsstufen) (FALSCH)
- Frage: Mein Mandant ist die VitaWelt Krankenversicherung a.G. (Versicherungsunternehmen mit Marketing). Sie hat diese Rechnung erhalten:
Rechnungsteller: Kreativwerk Agentur Licht GmbH, Rechnung KL-2026-112 vom 28.08.2026, Auftrag erteilt am 15.07.2026, Leistungszeitraum 07.–08.2026.
Pos. 01 Kampagnen-Konzeption durch Agentur-Team (GmbH, eigene Mitarbeiter): 3.200,00 € netto
Pos. 02 Illustrationen, beauftragt bei freischaffender Illustratorin Mara Vogt, im eigenen Namen der Agentur: 1.900,00 € netto
Pos. 03 TV-Spot-Produktion (Regie, Kamera, Schnitt) durch freischaffendes Film-Team „Roter Hering GbR“ (3 Personen), im eigenen Namen der Agentur: 24.500,00 € netto
Pos. 04 Synchronsprecher-Honorar, an Sprecher GmbH-Agentur gezahlt: 750,00 € netto
Pos. 05 Musik-Lizenz über Verwertungsgesellschaft (GEMA-Sammelabrechnung): 880,00 € netto
Pos. 06 Fahrzeug- und Materialkosten der GbR (abgerechnet mit Hauptleistung, mit eigenem Beleg: Benzin 400 €): 400,00 € netto
Pos. 07 Laufende Kommunikationsdesign-Services (Retainer) durch die GmbH; Freelancer-Anteil darin nicht aufgeschlüsselt: 3.150,00 € netto
Nettosumme: 34.780,00 €, USt 19 %: 660,82 €, Rechnungsbetrag: 35.440,82 €.
Ist das für meinen Mandanten künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag); Zahl: {'bemessungsgrundlage': '0'} (Referenz: Soll der Testdatei: auf Kundenebene alle Positionen ausgeschlossen (Zahlung an GmbH, Eigengeschäft der Agentur, GEMA), Bemessungsgrundlage 0 (bedingt), Agentur-Ebene nur als Hinweis, Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 29250, Abgabe 1287
- Fakten (System) bzw. Fundstellen (roh): Fundstellen laut Modell: § 25 KSVG (Abgabepflicht); KSK-Info 2023/1 (Abgrenzung künstlerische Leistungen); BFH-Urteil vom 25.11.2020 (V R 7/19) zu Retainer-Modellen; KSK-Merkblatt 'Werbung und Marketing'
- Verlauf: Antwort 1: Abgabepflichtig (Vorschlag)
- Gründe: Soll ['N'], Ist A (Abgabepflichtig (Vorschlag))

### F4 – Hochzeitsfotografie an Privatpersonen (Anti-Alarm) (RICHTIG)
- Frage: Ein Brautpaar (Privatpersonen) hat für seine Hochzeit diese Rechnung erhalten:
Rechnungsteller: Pixel & Herz Fotografie GbR (2 freischaffende Fotografinnen), Rechnung PH-2026-19 vom 22.05.2026, Barzahlung bei Übergabe quittiert.
Pos. 01 Hochzeitsreportage, 10 Std., 2 Fotografinnen: 1.650,00 € netto
Pos. 02 Hochwertiges Fotobuch, 60 Seiten, Layout und Druck: 420,00 € netto
Nettosumme: 2.075,00 €, USt 19 %: 394,25 €, Rechnungsbetrag: 2.469,25 €.
Muss das Brautpaar Künstlersozialabgabe zahlen?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll der Testdatei: Privatpersonen sind kein abgabepflichtiges Unternehmen, keine Abgabe, keine Schwellenwarnung (Regelwerk: R-40, R-133), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Nicht abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Fundstellen laut Modell: § 24 Abs. 1 KSVG; KSK-Info 1/2020, S. 5
- Verlauf: Antwort 1: Nicht abgabepflichtig (Vorschlag)
- Gründe: –

