# Prüfkatalog Stufe 1 – Lauf 2026-10-11 (Demo-Modus (FakeLLM))

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Soll-Werte: `aufgaben/audit/pruefkatalog.json`.

**Ergebnis: NICHT BESTANDEN**

- Fälle: 4, Dauer gesamt 0 s
- RICHTIG: 1, NACHGEFRAGT: 3, **FALSCH: 0**, FEHLER: 0
- Quote richtig bei Fällen mit sicherem Soll: 1 von 4 = 25 % (Ziel ≥ 90 %)
- Ziel Stufe 1: 0 FALSCH, 0 FEHLER, Quote ≥ 90 %.

| Fall | Fallgruppe | Soll | Ist | Bewertung | Dauer |
|---|---|---|---|---|---|
| F1 | Werbefotografie an Unternehmen (Eigenwerbung) | A | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0.1 s |
| F2 | Publizist an Verlag | A | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0.0 s |
| F3 | Agentur-Mischrechnung an Werbekunden (Vertragsstufen) | N | Nicht abgabepflichtig (Vorschlag) | **NACHGEFRAGT** | 0.0 s |
| F4 | Hochzeitsfotografie an Privatpersonen (Anti-Alarm) | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |

## Abweichungen im Einzelnen

### F1 – Werbefotografie an Unternehmen (Eigenwerbung) (NACHGEFRAGT)
- Frage: Mein Mandant ist die Steinbach Naturstein GmbH (B2B-Handel). Sie hat für ihre Image-Kampagne diese Rechnung erhalten:
Rechnungsteller: Jana Loots, Fotografin (freischaffend, Einzelunternehmerin), Rechnung F1-2026-88 vom 12.06.2026. Zahlung: „Mit Dank erhalten am 20.06.2026“ (laut Rechnung).
Pos. 01 Produktfotografie Steinbruch, halbtägiges Shooting inkl. Konzeption: 1.800,00 € netto
Pos. 02 Bildretusche und Farbkorrektur (12 Motive): 220,00 € netto
Pos. 03 Nutzungsrechte Kampagne, 24 Monate, Web + Print: 450,00 € netto
Nettosumme: 2.470,00 €, USt 19 %: 469,30 €, Rechnungsbetrag: 2.939,30 €.
Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '121.03'} (Referenz: Soll der Testdatei: alle 3 Positionen einbezogen (Retusche als Nebenleistung), 2.470 € × 4,9 % = 121,03 €, keine Rückfragen, Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Grenzfall → Steuerberater entscheidet; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Fotografie; Art des Auftraggebers: Eigenwerbung; Auftragnehmer: natürliche Person; Rechnungsteller (an ihn wird gezahlt): natürliche Person; Position 1: 1.800,00 € „Pos. 01 Produktfotografie Steinbruch, halbtägiges Shooting inkl. Konzeption“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Position 2: 220,00 € „Pos. 02 Bildretusche und Farbkorrektur (12 Motive)“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Position 3: 450,00 € „Pos. 03 Nutzungsrechte Kampagne, 24 Monate, Web + Print“, natürliche Person, Leistung: Nutzungsrechte, Lizenz, Buy-out, Urheberrechtsvergütung (Grenzfall); Position 4: 2.470,00 € „Nettosumme: , USt 19 %: , Rechnungsbetrag: .“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Position 5: 469,30 € „Nettosumme: , USt 19 %: , Rechnungsbetrag: .“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Position 6: 2.939,30 € „Nettosumme: , USt 19 %: , Rechnungsbetrag: .“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Alle Positionen vom selben Auftragnehmer: ja
- Verlauf: Antwort 1: Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['A'], Ist G

### F2 – Publizist an Verlag (NACHGEFRAGT)
- Frage: Mein Mandant ist die Rheinland Verlag GmbH & Co. KG (Fachmagazin „Stein & Bau“). Er hat diese Rechnung erhalten:
Rechnungsteller: Thomas Meyer, freier Journalist, Rechnung TM-2026-41 vom 03.09.2026. Zahlung: 30 Tage Ziel.
Pos. 01 Fachartikel „Naturstein im modernen Innenausbau“, 6 Seiten, einmalige Nutzung: 1.400,00 € netto
Pos. 02 Recherche-Pauschale (Fahrt, Literatur) lt. Vertrag: 350,00 € netto
Nettosumme: 1.750,00 €, USt 19 %: 332,50 €, Rechnungsbetrag: 2.082,50 €.
Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '85.75'} (Referenz: Soll der Testdatei: Verlag typischer Verwerter ohne Grenze; Artikel und Recherche-Pauschale einbezogen, 1.750 € × 4,9 % = 85,75 €, Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Grenzfall → Steuerberater entscheidet; Kern: Bemessungsgrundlage –, Abgabe –, ohne unsichere Leistungen 0.00
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Text/Redaktion; Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Rechnungsteller (an ihn wird gezahlt): natürliche Person; Position 1: 1.400,00 € „Pos. 01 Fachartikel „Naturstein im modernen Innenausbau“, 6 Seiten, einmalige Nutzung“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Position 2: 350,00 € „Pos. 02 Recherche-Pauschale (Fahrt, Literatur) lt. Vertrag“, natürliche Person, Leistung: Recherche und Vorarbeiten zu einer Leistung (Grenzfall); Position 3: 1.750,00 € „Nettosumme: , USt 19 %: , Rechnungsbetrag: .“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Position 4: 332,50 € „Nettosumme: , USt 19 %: , Rechnungsbetrag: .“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Position 5: 2.082,50 € „Nettosumme: , USt 19 %: , Rechnungsbetrag: .“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Alle Positionen vom selben Auftragnehmer: ja
- Verlauf: Antwort 1: Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['A'], Ist G

### F3 – Agentur-Mischrechnung an Werbekunden (Vertragsstufen) (NACHGEFRAGT)
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
- Ist: Nicht abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Grafik/Design; Art des Auftraggebers: Eigenwerbung; Auftragnehmer: GmbH/UG/AG; Rechnungsteller (an ihn wird gezahlt): GmbH/UG/AG; Position 1: 3.200,00 € „Pos. 01 Kampagnen-Konzeption durch Agentur-Team (GmbH, eigene Mitarbeiter)“, GmbH/UG/AG, Leistung: nicht im Regelwerk eingeordnet; Position 2: 1.900,00 € „Pos. 02 Illustrationen, beauftragt bei freischaffender Illustratorin Mara Vogt, im eigenen Namen der Agentur“, GmbH/UG/AG, Leistung: Illustration, Zeichnung, Icons, Comic, Karikatur (künstlerisch/publizistisch); Position 3: 24.500,00 € „Pos. 03 TV-Spot-Produktion (Regie, Kamera, Schnitt) durch freischaffendes Film-Team „Roter Hering GbR“ (3 Personen), im eigenen Namen der Agentur“, GmbH/UG/AG, Leistung: nicht im Regelwerk eingeordnet; Position 4: 750,00 € „Pos. 04 Synchronsprecher-Honorar, an Sprecher GmbH-Agentur gezahlt“, GmbH/UG/AG, Leistung: Sprecher (Werbung, Film, Hörbuch), Voiceover (künstlerisch/publizistisch); Position 5: 880,00 € „Pos. 05 Musik-Lizenz über Verwertungsgesellschaft (GEMA-Sammelabrechnung)“, GmbH/UG/AG, Leistung: Musik: Komposition, Jingle, Arrangement, Musiker, Sänger, Audio-Design, DJ (künstlerisch/publizistisch); Position 6: 400,00 € „Pos. 06 Fahrzeug- und Materialkosten der GbR (abgerechnet mit Hauptleistung, mit eigenem Beleg: Benzin )“, GmbH/UG/AG, Leistung: Material, Auslagen und Nebenkosten (Material, Fracht, Porto, Transport, Telefon) (Grenzfall); Position 7: 400,00 € „Pos. 06 Fahrzeug- und Materialkosten der GbR (abgerechnet mit Hauptleistung, mit eigenem Beleg: Benzin )“, GmbH/UG/AG, Leistung: Material, Auslagen und Nebenkosten (Material, Fracht, Porto, Transport, Telefon) (Grenzfall); Position 8: 3.150,00 € „Pos. 07 Laufende Kommunikationsdesign-Services (Retainer) durch die GmbH; Freelancer-Anteil darin nicht aufgeschlüsselt“, GmbH/UG/AG, Leistung: Grafikdesign, Layout, Logo, Corporate Design, Kommunikationsdesign (künstlerisch/publizistisch); Position 9: 34.780,00 € „Nettosumme: , USt 19 %: , Rechnungsbetrag: .“, GmbH/UG/AG, Leistung: nicht im Regelwerk eingeordnet; Position 10: 660,82 € „Nettosumme: , USt 19 %: , Rechnungsbetrag: .“, GmbH/UG/AG, Leistung: nicht im Regelwerk eingeordnet; Position 11: 35.440,82 € „Nettosumme: , USt 19 %: , Rechnungsbetrag: .“, GmbH/UG/AG, Leistung: nicht im Regelwerk eingeordnet; Alle Positionen vom selben Auftragnehmer: ja
- Verlauf: Antwort 1: Rückfrage nötig | Knopf verwerterart='Eigenwerbung' | -> Nicht abgabepflichtig (Vorschlag)
- Gründe: 1 Rückfrage(n), nötig laut Soll höchstens 0

### F4 – Hochzeitsfotografie an Privatpersonen (Anti-Alarm) (RICHTIG)
- Frage: Ein Brautpaar (Privatpersonen) hat für seine Hochzeit diese Rechnung erhalten:
Rechnungsteller: Pixel & Herz Fotografie GbR (2 freischaffende Fotografinnen), Rechnung PH-2026-19 vom 22.05.2026, Barzahlung bei Übergabe quittiert.
Pos. 01 Hochzeitsreportage, 10 Std., 2 Fotografinnen: 1.650,00 € netto
Pos. 02 Hochwertiges Fotobuch, 60 Seiten, Layout und Druck: 420,00 € netto
Nettosumme: 2.075,00 €, USt 19 %: 394,25 €, Rechnungsbetrag: 2.469,25 €.
Muss das Brautpaar Künstlersozialabgabe zahlen?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll der Testdatei: Privatpersonen sind kein abgabepflichtiges Unternehmen, keine Abgabe, keine Schwellenwarnung (Regelwerk: R-40, R-133), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Nicht abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Fotografie; Art des Auftraggebers: Privatperson (kein Unternehmen); Auftragnehmer: GbR; Rechnungsteller (an ihn wird gezahlt): GbR; Position 1: 1.650,00 € „Pos. 01 Hochzeitsreportage, 10 Std., 2 Fotografinnen“, GbR, Leistung: Fotografie (Werbe-, Foto-Design, künstlerische Fotografie) (künstlerisch/publizistisch); Position 2: 420,00 € „Pos. 02 Hochwertiges Fotobuch, 60 Seiten, Layout und Druck“, GbR, Leistung: Grafikdesign, Layout, Logo, Corporate Design, Kommunikationsdesign (künstlerisch/publizistisch); Position 3: 2.075,00 € „Nettosumme: , USt 19 %: , Rechnungsbetrag: .“, GbR, Leistung: nicht im Regelwerk eingeordnet; Position 4: 394,25 € „Nettosumme: , USt 19 %: , Rechnungsbetrag: .“, GbR, Leistung: nicht im Regelwerk eingeordnet; Position 5: 2.469,25 € „Nettosumme: , USt 19 %: , Rechnungsbetrag: .“, GbR, Leistung: nicht im Regelwerk eingeordnet; Alle Positionen vom selben Auftragnehmer: ja
- Verlauf: Antwort 1: Nicht abgabepflichtig (Vorschlag)
- Gründe: –

