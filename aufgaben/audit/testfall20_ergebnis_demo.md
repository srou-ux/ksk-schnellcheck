# Prüfkatalog Stufe 1 – Lauf 2026-10-17 (Demo-Modus (FakeLLM))

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Soll-Werte: `aufgaben/audit/testfall_20_positionen.json`.

**Ergebnis: BESTANDEN**

- Fälle: 21, Dauer gesamt 30 s
- RICHTIG: 19, NACHGEFRAGT: 2, **FALSCH: 0**, FEHLER: 0
- Quote richtig bei Fällen mit sicherem Soll: 18 von 20 = 90 % (Ziel ≥ 90 %)
- Ziel Stufe 1: 0 FALSCH, 0 FEHLER, Quote ≥ 90 %.

| Fall | Fallgruppe | Soll | Ist | Bewertung | Dauer |
|---|---|---|---|---|---|
| S-00 | Sammelrechnung mit allen 20 Positionen | A/G | Grenzfall → Steuerberater entscheidet | **RICHTIG** | 28.0 s |
| S-01 | Pos. 1: Webdesign & UI-Konzeption für Kundenportal | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.1 s |
| S-02 | Pos. 2: Programmierung des Backends (reines Coding) | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0.1 s |
| S-03 | Pos. 3: Erstellung von Werbetexten für Social Media | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.1 s |
| S-04 | Pos. 4: Korrektorat und Rechtschreibprüfung der Texte | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0.1 s |
| S-05 | Pos. 5: Fotografie von Vorstandsmitgliedern (inkl. Rechte) | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.1 s |
| S-06 | Pos. 6: Bereitstellung von Cloud-Hosting (AWS Gebühren) | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0.1 s |
| S-07 | Pos. 7: Sprecherhonorar für Erklärvideo (Voiceover) | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.1 s |
| S-08 | Pos. 8: Einkauf von Stock-Bildern über Agentur-Lizenz | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0.1 s |
| S-09 | Pos. 9: Konzeption einer Event-Choreografie | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.1 s |
| S-10 | Pos. 10: Miete für Kamera-Equipment (Leihgebühr) | N | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0.1 s |
| S-11 | Pos. 11: Gestaltung eines Messe-Flyers (Layout) | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.1 s |
| S-12 | Pos. 12: Druckkosten für Messe-Flyer (Druckerei GmbH) | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0.1 s |
| S-13 | Pos. 13: SEO-Analyse und technisches Audit | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0.1 s |
| S-14 | Pos. 14: Komposition eines Marken-Audio-Jingles | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.1 s |
| S-15 | Pos. 15: Projektmanagement & Koordination (technisch) | G | Grenzfall → Steuerberater entscheidet | **RICHTIG** | 0.1 s |
| S-16 | Pos. 16: Moderation des Firmen-Workshops durch Einzelunternehmer | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0.1 s |
| S-17 | Pos. 17: Übersetzung der Website ins Englische (Kreativtext) | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.1 s |
| S-18 | Pos. 18: Schaltung von Google-Ads Werbebudgets | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0.1 s |
| S-19 | Pos. 19: Zeichnung von benutzerdefinierten Icons (Illustration) | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.1 s |
| S-20 | Pos. 20: Beratung zur Datenschutz-Grundverordnung (DSGVO) | N | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0.1 s |

## Abweichungen im Einzelnen

### S-00 – Sammelrechnung mit allen 20 Positionen (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. Für ein Projekt 2026 haben wir folgende Leistungen eingekauft, wenn nicht anders angegeben jeweils von selbständigen Einzelpersonen:
1. Webdesign & UI-Konzeption für Kundenportal: 2500 € netto
2. Programmierung des Backends (reines Coding): 4100 € netto
3. Erstellung von Werbetexten für Social Media: 600 € netto
4. Korrektorat und Rechtschreibprüfung der Texte: 150 € netto
5. Fotografie von Vorstandsmitgliedern (inkl. Rechte): 1200 € netto
6. Bereitstellung von Cloud-Hosting (AWS Gebühren): 350 € netto (an einen Cloud-Anbieter (Aktiengesellschaft))
7. Sprecherhonorar für Erklärvideo (Voiceover): 450 € netto
8. Einkauf von Stock-Bildern über Agentur-Lizenz: 120 € netto (an eine Bildagentur (GmbH))
9. Konzeption einer Event-Choreografie: 800 € netto
10. Miete für Kamera-Equipment (Leihgebühr): 250 € netto
11. Gestaltung eines Messe-Flyers (Layout): 750 € netto
12. Druckkosten für Messe-Flyer (Druckerei GmbH): 500 € netto (an eine Druckerei (GmbH))
13. SEO-Analyse und technisches Audit: 900 € netto
14. Komposition eines Marken-Audio-Jingles: 1500 € netto
15. Projektmanagement & Koordination (technisch): 1800 € netto
16. Moderation des Firmen-Workshops durch Einzelunternehmer: 1200 € netto
17. Übersetzung der Website ins Englische (Kreativtext): 650 € netto
18. Schaltung von Google-Ads Werbebudgets: 3000 € netto (an Google (Kapitalgesellschaft))
19. Zeichnung von benutzerdefinierten Icons (Illustration): 400 € netto
20. Beratung zur Datenschutz-Grundverordnung (DSGVO): 950 € netto
Was davon ist künstlersozialabgabepflichtig und wie hoch ist die Abgabe?
- Soll: Abgabepflichtig (Vorschlag), Grenzfall → Steuerberater entscheidet; Zahl: {'abgabe': '433.65'} (Referenz: Soll aus der Testdatei: abgabepflichtig sind Pos. 1,3,5,7,9,11,14,17,19 = 8850 €, Pos. 15 Grenzfall, Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Grenzfall → Steuerberater entscheidet; Kern: Bemessungsgrundlage –, Abgabe –, ohne unsichere Leistungen 433.65, mit ihnen 597.80
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Grafik/Design; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 2.500,00 € „Webdesign & UI-Konzeption für Kundenportal“, natürliche Person, Leistung: Webdesign (Gestaltung von Internetseiten, auch mit Programmierung) (künstlerisch/publizistisch); Position 2: 4.100,00 € „Programmierung des Backends (reines Coding)“, natürliche Person, Leistung: Reine Programmierung oder technische Web-Betreuung ohne gestalterische Leistung (Webmaster, Administration) (nicht künstlerisch); Position 3: 600,00 € „Erstellung von Werbetexten für Social Media“, natürliche Person, Leistung: Werbetexte, Texter, Redaktion, Journalismus (künstlerisch/publizistisch); Position 4: 150,00 € „Korrektorat und Rechtschreibprüfung der Texte“, natürliche Person, Leistung: Reines Korrektorat (Rechtschreibung, Zeichensetzung) ohne Einfluss auf Stil und Inhalt (nicht künstlerisch); Position 5: 1.200,00 € „Fotografie von Vorstandsmitgliedern (inkl. Rechte)“, natürliche Person, Leistung: Fotografie (Werbe-, Foto-Design, künstlerische Fotografie) (künstlerisch/publizistisch); Position 6: 350,00 € „Bereitstellung von Cloud-Hosting (AWS Gebühren)“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Position 7: 450,00 € „Sprecherhonorar für Erklärvideo (Voiceover)“, natürliche Person, Leistung: Sprecher (Werbung, Film, Hörbuch), Voiceover (künstlerisch/publizistisch); Position 8: 120,00 € „Einkauf von Stock-Bildern über Agentur-Lizenz“, GmbH/UG/AG, Leistung: Nutzungsrechte, Lizenz, Buy-out, Urheberrechtsvergütung (Grenzfall); Position 9: 800,00 € „Konzeption einer Event-Choreografie“, natürliche Person, Leistung: Choreografie (künstlerisch/publizistisch); Position 10: 250,00 € „Miete für Kamera-Equipment (Leihgebühr)“, natürliche Person, Leistung: Miete von Geräten oder Sachmitteln (Kamera, Licht, Ton, Equipment) (Grenzfall); Position 11: 750,00 € „Gestaltung eines Messe-Flyers (Layout)“, natürliche Person, Leistung: Grafikdesign, Layout, Logo, Corporate Design, Kommunikationsdesign (künstlerisch/publizistisch); Position 12: 500,00 € „Druckkosten für Messe-Flyer (Druckerei GmbH)“, GmbH/UG/AG, Leistung: Nachträgliche Vervielfältigung oder Druck nach Abschluss der künstlerischen Leistung (nicht künstlerisch); Position 13: 900,00 € „SEO-Analyse und technisches Audit“, natürliche Person, Leistung: Suchmaschinenoptimierung (SEO) (nicht künstlerisch); Position 14: 1.500,00 € „Komposition eines Marken-Audio-Jingles“, natürliche Person, Leistung: Musik: Komposition, Jingle, Arrangement, Musiker, Sänger, Audio-Design, DJ (künstlerisch/publizistisch); Position 15: 1.800,00 € „Projektmanagement & Koordination (technisch)“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Position 16: 1.200,00 € „Moderation des Firmen-Workshops durch Einzelunternehmer“, natürliche Person, Leistung: Coaching, Team-Building, Workshop-Moderation (nicht künstlerisch); Position 17: 650,00 € „Übersetzung der Website ins Englische (Kreativtext)“, natürliche Person, Leistung: Übersetzung mit sprachlichem Gestaltungsspielraum und Öffentlichkeitsbezug (z. B. Werbe-, Website-, Literaturtext) (künstlerisch/publizistisch); Position 18: 3.000,00 € „Schaltung von Google-Ads Werbebudgets“, natürliche Person, Leistung: Anzeigenschaltung, Mediabudget, Branchen- und Telefonbucheinträge (nicht künstlerisch); Position 19: 400,00 € „Zeichnung von benutzerdefinierten Icons (Illustration)“, natürliche Person, Leistung: Illustration, Zeichnung, Icons, Comic, Karikatur (künstlerisch/publizistisch); Position 20: 950,00 € „Beratung zur Datenschutz-Grundverordnung (DSGVO)“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren); Alle Positionen vom selben Auftragnehmer: nein
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Grenzfall → Steuerberater entscheidet
- Gründe: –

### S-01 – Pos. 1: Webdesign & UI-Konzeption für Kundenportal (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Webdesign & UI-Konzeption für Kundenportal, 2500 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '122.50'} (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-01 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 2500, Abgabe 122.50
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Grafik/Design; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 2.500,00 €, natürliche Person, Leistung: Webdesign (Gestaltung von Internetseiten, auch mit Programmierung) (künstlerisch/publizistisch); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Abgabepflichtig (Vorschlag)
- Gründe: –

### S-02 – Pos. 2: Programmierung des Backends (reines Coding) (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Programmierung des Backends (reines Coding), 4100 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-02 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Nicht abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 0, Abgabe 0.00
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 4.100,00 €, natürliche Person, Leistung: Reine Programmierung oder technische Web-Betreuung ohne gestalterische Leistung (Webmaster, Administration) (nicht künstlerisch); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Nicht abgabepflichtig (Vorschlag)
- Gründe: –

### S-03 – Pos. 3: Erstellung von Werbetexten für Social Media (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Erstellung von Werbetexten für Social Media, 600 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '29.40'} (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-03 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 600, Abgabe 29.40
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Text/Redaktion; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 600,00 €, natürliche Person, Leistung: Werbetexte, Texter, Redaktion, Journalismus (künstlerisch/publizistisch); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Abgabepflichtig (Vorschlag)
- Gründe: –

### S-04 – Pos. 4: Korrektorat und Rechtschreibprüfung der Texte (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Korrektorat und Rechtschreibprüfung der Texte, 150 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-04 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Nicht abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 0, Abgabe 0.00
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Text/Redaktion; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 150,00 €, natürliche Person, Leistung: Reines Korrektorat (Rechtschreibung, Zeichensetzung) ohne Einfluss auf Stil und Inhalt (nicht künstlerisch); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Nicht abgabepflichtig (Vorschlag)
- Gründe: –

### S-05 – Pos. 5: Fotografie von Vorstandsmitgliedern (inkl. Rechte) (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Fotografie von Vorstandsmitgliedern (inkl. Rechte), 1200 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '58.80'} (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-05 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 1200, Abgabe 58.80
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Fotografie; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 1.200,00 €, natürliche Person, Leistung: Fotografie (Werbe-, Foto-Design, künstlerische Fotografie) (künstlerisch/publizistisch); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Abgabepflichtig (Vorschlag)
- Gründe: –

### S-06 – Pos. 6: Bereitstellung von Cloud-Hosting (AWS Gebühren) (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir einen Cloud-Anbieter (Aktiengesellschaft) beauftragt: Bereitstellung von Cloud-Hosting (AWS Gebühren), 350 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-06 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Nicht abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 0, Abgabe 0.00
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 350,00 €, GmbH/UG/AG; Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='GmbH/UG/AG' | -> Nicht abgabepflichtig (Vorschlag)
- Gründe: –

### S-07 – Pos. 7: Sprecherhonorar für Erklärvideo (Voiceover) (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Sprecherhonorar für Erklärvideo (Voiceover), 450 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '22.05'} (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-07 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 450, Abgabe 22.05
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 450,00 €, natürliche Person, Leistung: Sprecher (Werbung, Film, Hörbuch), Voiceover (künstlerisch/publizistisch); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Abgabepflichtig (Vorschlag)
- Gründe: –

### S-08 – Pos. 8: Einkauf von Stock-Bildern über Agentur-Lizenz (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine Bildagentur (GmbH) beauftragt: Einkauf von Stock-Bildern über Agentur-Lizenz, 120 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-08 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Nicht abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 0, Abgabe 0.00
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: GmbH/UG/AG; Position 1: 120,00 €, GmbH/UG/AG, Leistung: Nutzungsrechte, Lizenz, Buy-out, Urheberrechtsvergütung (Grenzfall); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Nicht abgabepflichtig (Vorschlag)
- Gründe: –

### S-09 – Pos. 9: Konzeption einer Event-Choreografie (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Konzeption einer Event-Choreografie, 800 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '39.20'} (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-09 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 800, Abgabe 39.20
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 800,00 €, natürliche Person, Leistung: Choreografie (künstlerisch/publizistisch); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Abgabepflichtig (Vorschlag)
- Gründe: –

### S-10 – Pos. 10: Miete für Kamera-Equipment (Leihgebühr) (NACHGEFRAGT)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Miete für Kamera-Equipment (Leihgebühr), 250 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-10 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Grenzfall → Steuerberater entscheidet; Kern: Bemessungsgrundlage –, Abgabe –, ohne unsichere Leistungen 0.00, mit ihnen 12.25
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 250,00 €, natürliche Person, Leistung: Miete von Geräten oder Sachmitteln (Kamera, Licht, Ton, Equipment) (Grenzfall); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['N'], Ist G

### S-11 – Pos. 11: Gestaltung eines Messe-Flyers (Layout) (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Gestaltung eines Messe-Flyers (Layout), 750 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '36.75'} (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-11 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 750, Abgabe 36.75
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 750,00 €, natürliche Person, Leistung: Grafikdesign, Layout, Logo, Corporate Design, Kommunikationsdesign (künstlerisch/publizistisch); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Abgabepflichtig (Vorschlag)
- Gründe: –

### S-12 – Pos. 12: Druckkosten für Messe-Flyer (Druckerei GmbH) (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine Druckerei (GmbH) beauftragt: Druckkosten für Messe-Flyer (Druckerei GmbH), 500 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-12 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Nicht abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 0, Abgabe 0.00
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: GmbH/UG/AG; Position 1: 500,00 €, GmbH/UG/AG, Leistung: Nachträgliche Vervielfältigung oder Druck nach Abschluss der künstlerischen Leistung (nicht künstlerisch); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Nicht abgabepflichtig (Vorschlag)
- Gründe: –

### S-13 – Pos. 13: SEO-Analyse und technisches Audit (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: SEO-Analyse und technisches Audit, 900 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-13 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Nicht abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 0, Abgabe 0.00
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 900,00 €, natürliche Person, Leistung: Suchmaschinenoptimierung (SEO) (nicht künstlerisch); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Nicht abgabepflichtig (Vorschlag)
- Gründe: –

### S-14 – Pos. 14: Komposition eines Marken-Audio-Jingles (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Komposition eines Marken-Audio-Jingles, 1500 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '73.50'} (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-14 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 1500, Abgabe 73.50
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 1.500,00 €, natürliche Person, Leistung: Musik: Komposition, Jingle, Arrangement, Musiker, Sänger, Audio-Design, DJ (künstlerisch/publizistisch); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Abgabepflichtig (Vorschlag)
- Gründe: –

### S-15 – Pos. 15: Projektmanagement & Koordination (technisch) (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Projektmanagement & Koordination (technisch), 1800 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Grenzfall → Steuerberater entscheidet (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-15 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Grenzfall → Steuerberater entscheidet; Kern: Bemessungsgrundlage –, Abgabe –, ohne unsichere Leistungen 0.00, mit ihnen 88.20
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Wir sind typischer Verwerter (Werbung für Dritte).; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „typischer Verwerter“); Art des Auftraggebers: Typischer Verwerter; Position 1: 1.800,00 €, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Rückfragen: ['Welche Leistung wurde genau erbracht (z. B. Logo-Gestaltung, Fotos, Texte, Programmierung)?'] | Nachtrag gesendet: 'Wir sind typischer Verwerter (Werbung für Dritte).' -> Grenzfall → Steuerberater entscheidet
- Gründe: –

### S-16 – Pos. 16: Moderation des Firmen-Workshops durch Einzelunternehmer (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Moderation des Firmen-Workshops durch Einzelunternehmer, 1200 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-16 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Nicht abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 0, Abgabe 0.00
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Position 1: 1.200,00 €, natürliche Person, Leistung: Coaching, Team-Building, Workshop-Moderation (nicht künstlerisch); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Nicht abgabepflichtig (Vorschlag)
- Gründe: –

### S-17 – Pos. 17: Übersetzung der Website ins Englische (Kreativtext) (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Übersetzung der Website ins Englische (Kreativtext), 650 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '31.85'} (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-17 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 650, Abgabe 31.85
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Grafik/Design; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 650,00 €, natürliche Person, Leistung: Übersetzung mit sprachlichem Gestaltungsspielraum und Öffentlichkeitsbezug (z. B. Werbe-, Website-, Literaturtext) (künstlerisch/publizistisch); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Abgabepflichtig (Vorschlag)
- Gründe: –

### S-18 – Pos. 18: Schaltung von Google-Ads Werbebudgets (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir Google (Kapitalgesellschaft) beauftragt: Schaltung von Google-Ads Werbebudgets, 3000 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-18 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Nicht abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 0, Abgabe 0.00
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 3.000,00 €, GmbH/UG/AG, Leistung: Anzeigenschaltung, Mediabudget, Branchen- und Telefonbucheinträge (nicht künstlerisch); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='GmbH/UG/AG' | -> Nicht abgabepflichtig (Vorschlag)
- Gründe: –

### S-19 – Pos. 19: Zeichnung von benutzerdefinierten Icons (Illustration) (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Zeichnung von benutzerdefinierten Icons (Illustration), 400 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '19.60'} (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-19 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 400, Abgabe 19.60
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Illustration; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 400,00 €, natürliche Person, Leistung: Illustration, Zeichnung, Icons, Comic, Karikatur (künstlerisch/publizistisch); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Abgabepflichtig (Vorschlag)
- Gründe: –

### S-20 – Pos. 20: Beratung zur Datenschutz-Grundverordnung (DSGVO) (NACHGEFRAGT)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Beratung zur Datenschutz-Grundverordnung (DSGVO), 950 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-20 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Grenzfall → Steuerberater entscheidet; Kern: Bemessungsgrundlage –, Abgabe –, ohne unsichere Leistungen 0.00, mit ihnen 46.55
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Wir sind typischer Verwerter (Werbung für Dritte).; Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „typischer Verwerter“); Art des Auftraggebers: Typischer Verwerter; Position 1: 950,00 €, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Rückfragen: ['Welche Leistung wurde genau erbracht (z. B. Logo-Gestaltung, Fotos, Texte, Programmierung)?'] | Nachtrag gesendet: 'Wir sind typischer Verwerter (Werbung für Dritte).' -> Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['N'], Ist G

