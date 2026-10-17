# Prüfkatalog Stufe 1 – Lauf 2026-10-17 (Mistral (mistral-small-latest) – im KSK-Assistenten)

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Soll-Werte: `aufgaben/audit/testfall_20_positionen.json`.

**Ergebnis: NICHT BESTANDEN**

- Fälle: 21, Dauer gesamt 109 s
- RICHTIG: 10, NACHGEFRAGT: 11, **FALSCH: 0**, FEHLER: 0
- Quote richtig bei Fällen mit sicherem Soll: 9 von 20 = 45 % (Ziel ≥ 90 %)
- Ziel Stufe 1: 0 FALSCH, 0 FEHLER, Quote ≥ 90 %.

| Fall | Fallgruppe | Soll | Ist | Bewertung | Dauer |
|---|---|---|---|---|---|
| S-00 | Sammelrechnung mit allen 20 Positionen | A/G | Grenzfall → Steuerberater entscheidet | **RICHTIG** | 62.1 s |
| S-01 | Pos. 1: Webdesign & UI-Konzeption für Kundenportal | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 1.9 s |
| S-02 | Pos. 2: Programmierung des Backends (reines Coding) | N | Rückfrage nötig | **NACHGEFRAGT** | 2.4 s |
| S-03 | Pos. 3: Erstellung von Werbetexten für Social Media | A | Rückfrage nötig | **NACHGEFRAGT** | 2.6 s |
| S-04 | Pos. 4: Korrektorat und Rechtschreibprüfung der Texte | N | Rückfrage nötig | **NACHGEFRAGT** | 2.6 s |
| S-05 | Pos. 5: Fotografie von Vorstandsmitgliedern (inkl. Rechte) | A | Rückfrage nötig | **NACHGEFRAGT** | 3.9 s |
| S-06 | Pos. 6: Bereitstellung von Cloud-Hosting (AWS Gebühren) | N | Rückfrage nötig | **NACHGEFRAGT** | 1.9 s |
| S-07 | Pos. 7: Sprecherhonorar für Erklärvideo (Voiceover) | A | Rückfrage nötig | **NACHGEFRAGT** | 2.5 s |
| S-08 | Pos. 8: Einkauf von Stock-Bildern über Agentur-Lizenz | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 2.9 s |
| S-09 | Pos. 9: Konzeption einer Event-Choreografie | A | Rückfrage nötig | **NACHGEFRAGT** | 2.5 s |
| S-10 | Pos. 10: Miete für Kamera-Equipment (Leihgebühr) | N | Rückfrage nötig | **NACHGEFRAGT** | 2.3 s |
| S-11 | Pos. 11: Gestaltung eines Messe-Flyers (Layout) | A | Rückfrage nötig | **NACHGEFRAGT** | 2.6 s |
| S-12 | Pos. 12: Druckkosten für Messe-Flyer (Druckerei GmbH) | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 1.9 s |
| S-13 | Pos. 13: SEO-Analyse und technisches Audit | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 1.9 s |
| S-14 | Pos. 14: Komposition eines Marken-Audio-Jingles | A | Rückfrage nötig | **NACHGEFRAGT** | 2.9 s |
| S-15 | Pos. 15: Projektmanagement & Koordination (technisch) | G | Grenzfall → Steuerberater entscheidet | **RICHTIG** | 1.8 s |
| S-16 | Pos. 16: Moderation des Firmen-Workshops durch Einzelunternehmer | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 1.9 s |
| S-17 | Pos. 17: Übersetzung der Website ins Englische (Kreativtext) | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 2.4 s |
| S-18 | Pos. 18: Schaltung von Google-Ads Werbebudgets | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 1.9 s |
| S-19 | Pos. 19: Zeichnung von benutzerdefinierten Icons (Illustration) | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 2.0 s |
| S-20 | Pos. 20: Beratung zur Datenschutz-Grundverordnung (DSGVO) | N | Rückfrage nötig | **NACHGEFRAGT** | 1.9 s |

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
- Ist: Grenzfall → Steuerberater entscheidet; Kern: Bemessungsgrundlage –, Abgabe –, ohne unsichere Leistungen 433.65, mit ihnen 656.60
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 2.500,00 € „Webdesign & UI-Konzeption für Kundenportal“, natürliche Person, Leistung: Webdesign (Gestaltung von Internetseiten, auch mit Programmierung) (künstlerisch/publizistisch); Position 2: 4.100,00 € „Programmierung des Backends (reines Coding)“, natürliche Person, Leistung: Reine Programmierung oder technische Web-Betreuung ohne gestalterische Leistung (Webmaster, Administration) (nicht künstlerisch); Position 3: 600,00 € „Erstellung von Werbetexten für Social Media“, natürliche Person, Leistung: Werbetexte, Texter, Redaktion, Journalismus (künstlerisch/publizistisch); Position 4: 150,00 € „Korrektorat und Rechtschreibprüfung der Texte“, natürliche Person, Leistung: Reines Korrektorat (Rechtschreibung, Zeichensetzung) ohne Einfluss auf Stil und Inhalt (nicht künstlerisch); Position 5: 1.200,00 € „Fotografie von Vorstandsmitgliedern (inkl. Rechte)“, natürliche Person, Leistung: Fotografie (Werbe-, Foto-Design, künstlerische Fotografie) (künstlerisch/publizistisch); Position 6: 350,00 € „Bereitstellung von Cloud-Hosting (AWS Gebühren)“, natürliche Person, Leistung: Miete von Geräten oder Sachmitteln (Kamera, Licht, Ton, Equipment) (Grenzfall); Position 7: 450,00 € „Sprecherhonorar für Erklärvideo (Voiceover)“, natürliche Person, Leistung: Sprecher (Werbung, Film, Hörbuch), Voiceover (künstlerisch/publizistisch); Position 8: 120,00 € „Einkauf von Stock-Bildern über Agentur-Lizenz“, GmbH/UG/AG, Leistung: Nutzungsrechte, Lizenz, Buy-out, Urheberrechtsvergütung (Grenzfall); Position 9: 800,00 € „Konzeption einer Event-Choreografie“, natürliche Person, Leistung: Choreografie (künstlerisch/publizistisch); Position 10: 250,00 € „Miete für Kamera-Equipment (Leihgebühr)“, natürliche Person, Leistung: Miete von Geräten oder Sachmitteln (Kamera, Licht, Ton, Equipment) (Grenzfall); Position 11: 750,00 € „Gestaltung eines Messe-Flyers (Layout)“, natürliche Person, Leistung: Grafikdesign, Layout, Logo, Corporate Design, Kommunikationsdesign (künstlerisch/publizistisch); Position 12: 500,00 € „Druckkosten für Messe-Flyer“ (nachträgliche Vervielfältigung), GmbH/UG/AG, Leistung: Nachträgliche Vervielfältigung oder Druck nach Abschluss der künstlerischen Leistung (nicht künstlerisch); Position 13: 900,00 € „SEO-Analyse und technisches Audit“, natürliche Person, Leistung: Suchmaschinenoptimierung (SEO) (nicht künstlerisch); Position 14: 1.500,00 € „Komposition eines Marken-Audio-Jingles“, natürliche Person, Leistung: Musik: Komposition, Jingle, Arrangement, Musiker, Sänger, Audio-Design, DJ (künstlerisch/publizistisch); Position 15: 1.800,00 € „Projektmanagement & Koordination (technisch)“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Position 16: 1.200,00 € „Moderation des Firmen-Workshops durch Einzelunternehmer“, natürliche Person, Leistung: nicht eindeutig zuzuordnen; Position 17: 650,00 € „Übersetzung der Website ins Englische (Kreativtext)“, natürliche Person, Leistung: Übersetzung mit sprachlichem Gestaltungsspielraum und Öffentlichkeitsbezug (z. B. Werbe-, Website-, Literaturtext) (künstlerisch/publizistisch); Position 18: 3.000,00 € „Schaltung von Google-Ads Werbebudgets“, natürliche Person, Leistung: Anzeigenschaltung, Mediabudget, Branchen- und Telefonbucheinträge (nicht künstlerisch); Position 19: 400,00 € „Zeichnung von benutzerdefinierten Icons (Illustration)“, natürliche Person, Leistung: Illustration, Zeichnung, Icons, Comic, Karikatur (künstlerisch/publizistisch); Position 20: 950,00 € „Beratung zur Datenschutz-Grundverordnung (DSGVO)“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Rechnung von Auftragnehmer 1: 2.500,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 2: 4.100,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 3: 600,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 4: 150,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 5: 1.200,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 6: 350,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 7: 450,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 8: 120,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 9: 800,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 10: 250,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 11: 750,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 12: 500,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 13: 900,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 14: 1.500,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 15: 1.800,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 16: 1.200,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 17: 650,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 18: 3.000,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 19: 400,00 € gesamt (Rest vom System berechnet); Rechnung von Auftragnehmer 20: 950,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren); Alle Positionen vom selben Auftragnehmer: nein
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Knopf ein_auftragnehmer='nein, von verschiedenen Auftragnehmern' | -> Grenzfall → Steuerberater entscheidet
- Gründe: –

### S-01 – Pos. 1: Webdesign & UI-Konzeption für Kundenportal (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Webdesign & UI-Konzeption für Kundenportal, 2500 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '122.50'} (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-01 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 2500, Abgabe 122.50
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 2.500,00 € „Webdesign & UI-Konzeption für Kundenportal“, natürliche Person, Leistung: Webdesign (Gestaltung von Internetseiten, auch mit Programmierung) (künstlerisch/publizistisch); Rechnung von Auftragnehmer 1: 2.500,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Abgabepflichtig (Vorschlag)
- Gründe: –

### S-02 – Pos. 2: Programmierung des Backends (reines Coding) (NACHGEFRAGT)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Programmierung des Backends (reines Coding), 4100 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-02 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „typischer Verwerter“); Art des Auftraggebers: Typischer Verwerter; Position 1: 4.100,00 € „Programmierung des Backends (reines Coding)“, Leistung: Reine Programmierung oder technische Web-Betreuung ohne gestalterische Leistung (Webmaster, Administration) (nicht künstlerisch); Rechnung von Auftragnehmer 1: 4.100,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren); kuenstlerisch: ausdrücklich unbekannt; Rechtsform des Auftragnehmers: ausdrücklich unbekannt
- Verlauf: Antwort 1: Rückfrage nötig | Rückfragen: [] | Nachtrag gesendet: 'Wir sind typischer Verwerter (Werbung für Dritte).' -> Rückfrage nötig
- Gründe: Soll ['N'], Ist R

### S-03 – Pos. 3: Erstellung von Werbetexten für Social Media (NACHGEFRAGT)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Erstellung von Werbetexten für Social Media, 600 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '29.40'} (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-03 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „typischer Verwerter“); Art des Auftraggebers: Typischer Verwerter; Position 1: 600,00 € „Erstellung von Werbetexten für Social Media“, Leistung: Werbetexte, Texter, Redaktion, Journalismus (künstlerisch/publizistisch); Rechnung von Auftragnehmer 1: 600,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren); Rechtsform des Auftragnehmers: ausdrücklich unbekannt; kuenstlerisch: ausdrücklich unbekannt
- Verlauf: Antwort 1: Rückfrage nötig | Rückfragen: [] | Nachtrag gesendet: 'Wir sind typischer Verwerter (Werbung für Dritte).' -> Rückfrage nötig
- Gründe: Soll ['A'], Ist R

### S-04 – Pos. 4: Korrektorat und Rechtschreibprüfung der Texte (NACHGEFRAGT)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Korrektorat und Rechtschreibprüfung der Texte, 150 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-04 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „typischer Verwerter“); Art des Auftraggebers: Typischer Verwerter; Position 1: 150,00 € „Korrektorat und Rechtschreibprüfung der Texte“, Leistung: Reines Korrektorat (Rechtschreibung, Zeichensetzung) ohne Einfluss auf Stil und Inhalt (nicht künstlerisch); Rechnung von Auftragnehmer 1: 150,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren); kuenstlerisch: ausdrücklich unbekannt; Rechtsform des Auftragnehmers: ausdrücklich unbekannt
- Verlauf: Antwort 1: Rückfrage nötig | Rückfragen: [] | Nachtrag gesendet: 'Wir sind typischer Verwerter (Werbung für Dritte).' -> Rückfrage nötig
- Gründe: Soll ['N'], Ist R

### S-05 – Pos. 5: Fotografie von Vorstandsmitgliedern (inkl. Rechte) (NACHGEFRAGT)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Fotografie von Vorstandsmitgliedern (inkl. Rechte), 1200 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '58.80'} (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-05 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „typischer Verwerter“); Art des Auftraggebers: Typischer Verwerter; Position 1: 1.200,00 € „Fotografie von Vorstandsmitgliedern (inkl. Rechte)“, Leistung: Fotografie (Werbe-, Foto-Design, künstlerische Fotografie) (künstlerisch/publizistisch); Rechnung von Auftragnehmer 1: 1.200,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren); kuenstlerisch: ausdrücklich unbekannt; Rechtsform des Auftragnehmers: ausdrücklich unbekannt
- Verlauf: Antwort 1: Rückfrage nötig | Rückfragen: [] | Nachtrag gesendet: 'Wir sind typischer Verwerter (Werbung für Dritte).' -> Rückfrage nötig
- Gründe: Soll ['A'], Ist R

### S-06 – Pos. 6: Bereitstellung von Cloud-Hosting (AWS Gebühren) (NACHGEFRAGT)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir einen Cloud-Anbieter (Aktiengesellschaft) beauftragt: Bereitstellung von Cloud-Hosting (AWS Gebühren), 350 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-06 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „typischer Verwerter“); Art des Auftraggebers: Typischer Verwerter; Position 1: 350,00 € „Bereitstellung von Cloud-Hosting (AWS Gebühren)“, Leistung: nicht im Regelwerk eingeordnet; Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren); kuenstlerisch: ausdrücklich unbekannt; Rechtsform des Auftragnehmers: ausdrücklich unbekannt
- Verlauf: Antwort 1: Rückfrage nötig | Rückfragen: [] | Nachtrag gesendet: 'Wir sind typischer Verwerter (Werbung für Dritte).' -> Rückfrage nötig
- Gründe: Soll ['N'], Ist R

### S-07 – Pos. 7: Sprecherhonorar für Erklärvideo (Voiceover) (NACHGEFRAGT)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Sprecherhonorar für Erklärvideo (Voiceover), 450 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '22.05'} (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-07 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Sprecher (Werbung, Film, Hörbuch), Voiceover; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „typischer Verwerter“); Art des Auftraggebers: Typischer Verwerter; Position 1: 450,00 € „Sprecherhonorar für Erklärvideo (Voiceover)“, Leistung: Sprecher (Werbung, Film, Hörbuch), Voiceover (künstlerisch/publizistisch); Rechnung von Auftragnehmer 1: 450,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren); Rechtsform des Auftragnehmers: ausdrücklich unbekannt; kuenstlerisch: ausdrücklich unbekannt; Einnahmeabsicht: ausdrücklich unbekannt
- Verlauf: Antwort 1: Rückfrage nötig | Rückfragen: [] | Nachtrag gesendet: 'Wir sind typischer Verwerter (Werbung für Dritte).' -> Rückfrage nötig
- Gründe: Soll ['A'], Ist R

### S-08 – Pos. 8: Einkauf von Stock-Bildern über Agentur-Lizenz (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine Bildagentur (GmbH) beauftragt: Einkauf von Stock-Bildern über Agentur-Lizenz, 120 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-08 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Nicht abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 0, Abgabe 0.00
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 120,00 € „Einkauf von Stock-Bildern über Agentur-Lizenz“, GmbH/UG/AG, Leistung: Nutzungsrechte, Lizenz, Buy-out, Urheberrechtsvergütung (Grenzfall); Rechnung von Auftragnehmer 1: 120,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren); Ausdrücklich unbekannt: Rechtsform des Auftragnehmers; Ausdrücklich unbekannt: kuenstlerisch; Ausdrücklich unbekannt: Einnahmeabsicht
- Verlauf: Antwort 1: Nicht abgabepflichtig (Vorschlag)
- Gründe: –

### S-09 – Pos. 9: Konzeption einer Event-Choreografie (NACHGEFRAGT)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Konzeption einer Event-Choreografie, 800 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '39.20'} (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-09 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „typischer Verwerter“); Art des Auftraggebers: Typischer Verwerter; Position 1: 800,00 € „Konzeption einer Event-Choreografie“, Leistung: Choreografie (künstlerisch/publizistisch); Rechnung von Auftragnehmer 1: 800,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren); auftraggeber typ: ausdrücklich unbekannt; Rechtsform des Auftragnehmers: ausdrücklich unbekannt; kuenstlerisch: ausdrücklich unbekannt; Art des Auftraggebers: ausdrücklich unbekannt
- Verlauf: Antwort 1: Rückfrage nötig | Rückfragen: [] | Nachtrag gesendet: 'Wir sind typischer Verwerter (Werbung für Dritte).' -> Rückfrage nötig
- Gründe: Soll ['A'], Ist R

### S-10 – Pos. 10: Miete für Kamera-Equipment (Leihgebühr) (NACHGEFRAGT)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Miete für Kamera-Equipment (Leihgebühr), 250 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-10 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „typischer Verwerter“); Art des Auftraggebers: Typischer Verwerter; Position 1: 250,00 € „Miete für Kamera-Equipment (Leihgebühr)“, Leistung: Miete von Geräten oder Sachmitteln (Kamera, Licht, Ton, Equipment) (Grenzfall); Rechnung von Auftragnehmer 1: 250,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren); kuenstlerisch: ausdrücklich unbekannt; Rechtsform des Auftragnehmers: ausdrücklich unbekannt
- Verlauf: Antwort 1: Rückfrage nötig | Rückfragen: [] | Nachtrag gesendet: 'Wir sind typischer Verwerter (Werbung für Dritte).' -> Rückfrage nötig
- Gründe: Soll ['N'], Ist R

### S-11 – Pos. 11: Gestaltung eines Messe-Flyers (Layout) (NACHGEFRAGT)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Gestaltung eines Messe-Flyers (Layout), 750 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '36.75'} (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-11 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „typischer Verwerter“); Art des Auftraggebers: Typischer Verwerter; Position 1: 750,00 € „Gestaltung eines Messe-Flyers (Layout)“, Leistung: Grafikdesign, Layout, Logo, Corporate Design, Kommunikationsdesign (künstlerisch/publizistisch); Rechnung von Auftragnehmer 1: 750,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren); auftraggeber typ: ausdrücklich unbekannt; Rechtsform des Auftragnehmers: ausdrücklich unbekannt; kuenstlerisch: ausdrücklich unbekannt; Einnahmeabsicht: ausdrücklich unbekannt
- Verlauf: Antwort 1: Rückfrage nötig | Rückfragen: [] | Nachtrag gesendet: 'Wir sind typischer Verwerter (Werbung für Dritte).' -> Rückfrage nötig
- Gründe: Soll ['A'], Ist R

### S-12 – Pos. 12: Druckkosten für Messe-Flyer (Druckerei GmbH) (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine Druckerei (GmbH) beauftragt: Druckkosten für Messe-Flyer (Druckerei GmbH), 500 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-12 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Nicht abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 0, Abgabe 0.00
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 500,00 € „Druckkosten für Messe-Flyer“ (nachträgliche Vervielfältigung), GmbH/UG/AG, Leistung: Nachträgliche Vervielfältigung oder Druck nach Abschluss der künstlerischen Leistung (nicht künstlerisch); Rechnung von Auftragnehmer 1: 500,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Nicht abgabepflichtig (Vorschlag)
- Gründe: –

### S-13 – Pos. 13: SEO-Analyse und technisches Audit (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: SEO-Analyse und technisches Audit, 900 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-13 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Nicht abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 0, Abgabe 0.00
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 900,00 € „SEO-Analyse und technisches Audit“, natürliche Person, Leistung: Suchmaschinenoptimierung (SEO) (nicht künstlerisch); Rechnung von Auftragnehmer 1: 900,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren); Ausdrücklich unbekannt: kuenstlerisch; Ausdrücklich unbekannt: Einnahmeabsicht
- Verlauf: Antwort 1: Nicht abgabepflichtig (Vorschlag)
- Gründe: –

### S-14 – Pos. 14: Komposition eines Marken-Audio-Jingles (NACHGEFRAGT)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Komposition eines Marken-Audio-Jingles, 1500 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '73.50'} (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-14 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „typischer Verwerter“); Art des Auftraggebers: Typischer Verwerter; Position 1: 1.500,00 € „Komposition eines Marken-Audio-Jingles“, Leistung: Musik: Komposition, Jingle, Arrangement, Musiker, Sänger, Audio-Design, DJ (künstlerisch/publizistisch); Rechnung von Auftragnehmer 1: 1.500,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren); auftraggeber typ: ausdrücklich unbekannt; Rechtsform des Auftragnehmers: ausdrücklich unbekannt; kuenstlerisch: ausdrücklich unbekannt; Art des Auftraggebers: ausdrücklich unbekannt; Einnahmeabsicht: ausdrücklich unbekannt
- Verlauf: Antwort 1: Rückfrage nötig | Rückfragen: [] | Nachtrag gesendet: 'Wir sind typischer Verwerter (Werbung für Dritte).' -> Rückfrage nötig
- Gründe: Soll ['A'], Ist R

### S-15 – Pos. 15: Projektmanagement & Koordination (technisch) (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Projektmanagement & Koordination (technisch), 1800 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Grenzfall → Steuerberater entscheidet (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-15 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Grenzfall → Steuerberater entscheidet; Kern: Bemessungsgrundlage –, Abgabe –, ohne unsichere Leistungen 0.00, mit ihnen 88.20
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 1.800,00 € „Projektmanagement & Koordination (technisch)“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Rechnung von Auftragnehmer 1: 1.800,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Grenzfall → Steuerberater entscheidet
- Gründe: –

### S-16 – Pos. 16: Moderation des Firmen-Workshops durch Einzelunternehmer (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Moderation des Firmen-Workshops durch Einzelunternehmer, 1200 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-16 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Nicht abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 0, Abgabe 0.00
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 1.200,00 € „Moderation des Firmen-Workshops“, natürliche Person, Leistung: Coaching, Team-Building, Workshop-Moderation (nicht künstlerisch); Rechnung von Auftragnehmer 1: 1.200,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Nicht abgabepflichtig (Vorschlag)
- Gründe: –

### S-17 – Pos. 17: Übersetzung der Website ins Englische (Kreativtext) (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Übersetzung der Website ins Englische (Kreativtext), 650 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '31.85'} (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-17 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 650, Abgabe 31.85
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 650,00 € „Übersetzung der Website ins Englische (Kreativtext)“, natürliche Person, Leistung: Übersetzung mit sprachlichem Gestaltungsspielraum und Öffentlichkeitsbezug (z. B. Werbe-, Website-, Literaturtext) (künstlerisch/publizistisch); Rechnung von Auftragnehmer 1: 650,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)
- Verlauf: Antwort 1: Abgabepflichtig (Vorschlag)
- Gründe: –

### S-18 – Pos. 18: Schaltung von Google-Ads Werbebudgets (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir Google (Kapitalgesellschaft) beauftragt: Schaltung von Google-Ads Werbebudgets, 3000 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-18 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Nicht abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 0, Abgabe 0.00
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 3.000,00 € „Schaltung von Google-Ads Werbebudgets“, GmbH/UG/AG, Leistung: Anzeigenschaltung, Mediabudget, Branchen- und Telefonbucheinträge (nicht künstlerisch); Rechnung von Auftragnehmer 1: 3.000,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren); Ausdrücklich unbekannt: auftraggeber typ; Ausdrücklich unbekannt: kuenstlerisch; Ausdrücklich unbekannt: agentur abgabepflichtig; Ausdrücklich unbekannt: empfaenger abgabepflichtig
- Verlauf: Antwort 1: Rückfrage nötig | Knopf auftragnehmer_typ='GmbH/UG/AG' | -> Nicht abgabepflichtig (Vorschlag)
- Gründe: –

### S-19 – Pos. 19: Zeichnung von benutzerdefinierten Icons (Illustration) (RICHTIG)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Zeichnung von benutzerdefinierten Icons (Illustration), 400 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '19.60'} (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-19 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage 400, Abgabe 19.60
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „Werbeagentur“); Art des Auftraggebers: Typischer Verwerter; Position 1: 400,00 € „Zeichnung von benutzerdefinierten Icons (Illustration)“, natürliche Person, Leistung: Illustration, Zeichnung, Icons, Comic, Karikatur (künstlerisch/publizistisch); Rechnung von Auftragnehmer 1: 400,00 € gesamt (Rest vom System berechnet); Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren); Ausdrücklich unbekannt: kuenstlerisch; Ausdrücklich unbekannt: Art des Auftraggebers
- Verlauf: Antwort 1: Abgabepflichtig (Vorschlag)
- Gründe: –

### S-20 – Pos. 20: Beratung zur Datenschutz-Grundverordnung (DSGVO) (NACHGEFRAGT)
- Frage: Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: Beratung zur Datenschutz-Grundverordnung (DSGVO), 950 € netto. Ist das künstlersozialabgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: Soll aus KSK_Testfall_20_Positionen.xlsx (Excel-Referenz R-20 ist nur ein Platzhalter der Testdatei), Sicherheit: Soll der Testdatei, nicht vom Steuerberater geprüft)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Wir sind typischer Verwerter (Werbung für Dritte).; Ihr Unternehmen (Tätigkeit): Werbeagentur; Zweck dieses Auftrags: Werbung, Öffentlichkeitsarbeit oder Verwertung für Kunden (Dritte) (vom Sprachmodell gelesen – bitte prüfen); Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater) (laut Ihrer Nachricht: „typischer Verwerter“); Art des Auftraggebers: Typischer Verwerter; Gesamtbetrag (Aufteilung auf Rechnungen unbekannt): 950,00 €, Leistung: nicht im Regelwerk eingeordnet; kuenstlerisch: ausdrücklich unbekannt; Rechtsform des Auftragnehmers: ausdrücklich unbekannt
- Verlauf: Antwort 1: Rückfrage nötig | Rückfragen: ['Welche Leistung wurde genau erbracht (z. B. Logo-Gestaltung, Fotos, Texte, Programmierung)?'] | Nachtrag gesendet: 'Wir sind typischer Verwerter (Werbung für Dritte).' -> Rückfrage nötig
- Gründe: Soll ['N'], Ist R

