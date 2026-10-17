# Prüfkatalog Stufe 1 – Lauf 2026-10-11 (Mistral (mistral-large-latest) – im KSK-Assistenten)

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Soll-Werte: `aufgaben/audit/pruefkatalog.json`.

**Ergebnis: NICHT BESTANDEN**

- Fälle: 52, Dauer gesamt 338 s
- RICHTIG: 33, NACHGEFRAGT: 19, **FALSCH: 0**, FEHLER: 0
- Quote richtig bei Fällen mit sicherem Soll: 29 von 48 = 60 % (Ziel ≥ 90 %)
- Ziel Stufe 1: 0 FALSCH, 0 FEHLER, Quote ≥ 90 %.

| Fall | Fallgruppe | Soll | Ist | Bewertung | Dauer |
|---|---|---|---|---|---|
| P-01 | 01 Logo | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 21.7 s |
| P-02 | 02 Website | A | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 3.5 s |
| P-03 | 03 Großer Werbeauftrag | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 6.5 s |
| P-04a | 04 Viele kleine Rechnungen | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 4.3 s |
| P-04b | 04 Viele kleine Rechnungen | N | Rückfrage nötig | **NACHGEFRAGT** | 10.4 s |
| P-05 | 05 Werbeagentur | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 4.1 s |
| P-06 | 06 Verlag | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 6.7 s |
| P-07 | 07 Nutzung zur Einnahmeerzielung | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 8.2 s |
| P-08 | 08 Bis zu drei Veranstaltungen | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 7.4 s |
| P-09 | 09 Vier Veranstaltungen | A | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 11.7 s |
| P-10 | 10 Konzertveranstalter | A | Rückfrage nötig | **NACHGEFRAGT** | 17.0 s |
| P-11 | 11 Restaurant mit Livemusik | A/G | Rückfrage nötig | **NACHGEFRAGT** | 4.1 s |
| P-12 | 12 Firmenjubiläum | A | Rückfrage nötig | **NACHGEFRAGT** | 5.6 s |
| P-13 | 13 Eventagentur | A/G | Rückfrage nötig | **NACHGEFRAGT** | 1.7 s |
| P-14 | 14 Bandleader | A | Rückfrage nötig | **NACHGEFRAGT** | 2.7 s |
| P-15 | 15 Gemeinnütziger Verein | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 9.8 s |
| P-16 | 16 Musikverein Konzerte | N/G | Rückfrage nötig | **NACHGEFRAGT** | 6.3 s |
| P-17 | 17 Chorleiter | N | Rückfrage nötig | **NACHGEFRAGT** | 1.8 s |
| P-18a | 18 Musikunterricht | N | Rückfrage nötig | **NACHGEFRAGT** | 4.7 s |
| P-18b | 18 Musikunterricht | R/G | Rückfrage nötig | **RICHTIG** | 2.7 s |
| P-19 | 19 Verein Website/Flyer | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 21.4 s |
| P-20a | 20 Übungsleiterpauschale | N | Rückfrage nötig | **NACHGEFRAGT** | 2.4 s |
| P-20b | 20 Übungsleiterpauschale | A | Rückfrage nötig | **NACHGEFRAGT** | 2.3 s |
| P-21 | 21 Einzelunternehmer | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 4.6 s |
| P-22 | 22 GbR | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 4.3 s |
| P-23 | 23 GmbH | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 4.2 s |
| P-24 | 24 KG/OHG | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 6.4 s |
| P-25 | 25 Nicht KSK-versichert | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 8.9 s |
| P-26 | 26 Rentner/Student | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 3.4 s |
| P-27 | 27 Künstler im Ausland | A/G | Abgabepflichtig (Vorschlag) | **RICHTIG** | 17.7 s |
| P-28 | 28 Umsatzsteuer | A | Rückfrage nötig | **NACHGEFRAGT** | 5.9 s |
| P-29 | 29 Material/Nebenkosten | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 7.3 s |
| P-30 | 30 Reisekosten | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 4.6 s |
| P-31 | 31 Bewirtung | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 5.0 s |
| P-32 | 32 Gestaltung plus Druck | A | Rückfrage nötig | **NACHGEFRAGT** | 11.4 s |
| P-33 | 33 Nutzungsrechte | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 5.1 s |
| P-34 | 34 Verwertungsgesellschaft | N | Rückfrage nötig | **NACHGEFRAGT** | 5.0 s |
| P-35 | 35 Entwurf nicht verwendet | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 2.8 s |
| P-36 | 36 Agentur im Namen des Künstlers | N | Rückfrage nötig | **NACHGEFRAGT** | 5.3 s |
| P-37 | 37 Nur Kontakt vermittelt | G/N | Rückfrage nötig | **NACHGEFRAGT** | 2.6 s |
| P-38 | 38 Agentur im eigenen Namen | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 5.7 s |
| P-39 | 39 Auszahlung an Dritten | A/G | Abgabepflichtig (Vorschlag) | **RICHTIG** | 8.3 s |
| P-40 | 40 Privatperson | N | Rückfrage nötig | **NACHGEFRAGT** | 5.9 s |
| P-52 | 52 Derselbe Künstler, mehrere Positionen | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 8.7 s |
| K-01 | Kontrolle: Jahr fehlt | R | Rückfrage nötig | **RICHTIG** | 4.5 s |
| K-02 | Kontrolle: Jahr ohne Quelle | X/R | Nicht abgedeckt (Quelle fehlt) | **RICHTIG** | 2.8 s |
| K-03 | Kontrolle: Auskunft | AUSKUNFT | Auskunft aus dem Regelwerk | **RICHTIG** | 5.7 s |
| K-04 | Kontrolle: Schwelle 2025 | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 4.2 s |
| K-05 | Kontrolle: Schwelle 2026 | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 5.1 s |
| K-06 | Kontrolle: genau auf der Schwelle | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 4.3 s |
| K-07 | Kontrolle: Einnahmeabsicht unbekannt | R/G | Rückfrage nötig | **RICHTIG** | 4.7 s |
| K-08 | Kontrolle: Einschleusung | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 6.6 s |

## Abweichungen im Einzelnen

### P-02 – 02 Website (NACHGEFRAGT)
- Frage: Unser Steuerbüro hat 2026 einen selbständigen Webdesigner (Einzelperson) beauftragt, der unsere Website gestaltet und auch programmiert hat. Rechnung 3.000 € netto. Ist das abgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '147.00'} (Referenz: C-13, Sicherheit: fest)
- Ist: Grenzfall → Steuerberater entscheidet; Kern: Bemessungsgrundlage –, Abgabe –, mit ihnen 147.00
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Webdesign; Art des Auftraggebers: Eigenwerbung; Position 1: 3.000,00 € „Website Gestaltung und Programmierung“, natürliche Person, Leistung: nicht eindeutig zuzuordnen; Rechnung von Auftragnehmer 1: 3.000,00 € gesamt (Rest vom System berechnet)
- Verlauf: Antwort 1: Rückfrage nötig | Knopf verwerterart='Eigenwerbung' | -> Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['A'], Ist G

### P-04b – 04 Viele kleine Rechnungen (NACHGEFRAGT)
- Frage: Ein selbständiger Grafiker (Einzelperson) hat uns 2026 viermal kleine Werbegrafiken für unsere eigene Werbung gestaltet, jede Rechnung 200 € netto. Sonst keine Aufträge. Abgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: F-04, Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Grafik/Design; Art des Auftraggebers: Eigenwerbung; Auftragnehmer: natürliche Person; Position 1: 200,00 € „kleine Werbegrafiken“, natürliche Person, Leistung: Grafikdesign, Layout, Logo, Corporate Design, Kommunikationsdesign (künstlerisch/publizistisch); Position 2: 200,00 € „kleine Werbegrafiken“, natürliche Person, Leistung: Grafikdesign, Layout, Logo, Corporate Design, Kommunikationsdesign (künstlerisch/publizistisch); Position 3: 200,00 € „kleine Werbegrafiken“, natürliche Person, Leistung: Grafikdesign, Layout, Logo, Corporate Design, Kommunikationsdesign (künstlerisch/publizistisch); Position 4: 200,00 € „kleine Werbegrafiken“, natürliche Person, Leistung: Grafikdesign, Layout, Logo, Corporate Design, Kommunikationsdesign (künstlerisch/publizistisch); Rechnung von Auftragnehmer 1: 200,00 € gesamt (Rest vom System berechnet); Alle Positionen vom selben Auftragnehmer: ja; Rechnungsbetrag von Auftragnehmer 1: widersprüchlich (Ein Teilbetrag ist so hoch wie die ganze Rechnung.)
- Verlauf: Antwort 1: Rückfrage nötig | Rückfragen: ['Die Aufteilung der Rechnung von Auftragnehmer 1 ist unklar: Ein Teilbetrag ist so hoch wie die ganze Rechnung. Bitte nennen Sie den Rechnungsbetrag und die darin enthaltenen Teilbeträge.'] | Nachtrag gesendet: 'Es ist Eigenwerbung, insgesamt vier Rechnungen zu je 200 €.' -> Rückfrage nötig
- Gründe: Soll ['N'], Ist R

### P-09 – 09 Vier Veranstaltungen (NACHGEFRAGT)
- Frage: Unser Unternehmen (kein Veranstalter von Beruf) hat 2025 vier Veranstaltungen mit bezahlten selbständigen Künstlern durchgeführt, Gagen zusammen 5.000 €. Wir wollten damit Einnahmen erzielen. Sonst keine Aufträge an Künstler. Abgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '250.00'} (Referenz: D-04, Sicherheit: fest)
- Ist: Grenzfall → Steuerberater entscheidet; Kern: Bemessungsgrundlage –, Abgabe –, mit ihnen 250.00
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2025; Leistung: Generalklausel, vier Veranstaltungen, Einnahmeabsicht ja.; Art des Auftraggebers: Veranstalter (Generalklausel); Auftragnehmer: natürliche Person; Gesamtbetrag (Aufteilung auf Rechnungen unbekannt): 5.000,00 €, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Veranstaltungen: 4; Einnahmeabsicht: ja
- Verlauf: Antwort 1: Rückfrage nötig | Knopf verwerterart='Veranstalter (Generalklausel)' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Rückfragen: ['Welche Leistung wurde genau erbracht (z. B. Logo-Gestaltung, Fotos, Texte, Programmierung)?'] | Nachtrag gesendet: 'Generalklausel, vier Veranstaltungen, Einnahmeabsicht ja.' -> Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['A'], Ist G

### P-10 – 10 Konzertveranstalter (NACHGEFRAGT)
- Frage: Wir sind eine Konzertdirektion. 2025 hatten wir nur zwei Konzerte mit selbständigen Musikern (Einzelpersonen), Gagen zusammen 300 €. Fällt da Abgabe an?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '15.00'} (Referenz: F-01, Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig | Knopf verwerterart='Typischer Verwerter' | -> Rückfrage nötig | Rückfragen: ['Wurden mit der/den Veranstaltung(en) Einnahmen erzielt oder beabsichtigt?'] | Nachtrag gesendet: 'Wir sind typischer Verwerter (Konzertdirektion).' -> Rückfrage nötig
- Gründe: Soll ['A'], Ist R

### P-11 – 11 Restaurant mit Livemusik (NACHGEFRAGT)
- Frage: Unser Restaurant hat 2025 jeden Freitag Livemusik, also rund 50 Abende, damit mehr Gäste kommen. Die selbständigen Musiker bekamen zusammen 6.000 €. Abgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag), Grenzfall → Steuerberater entscheidet (Referenz: R-29, R-36, R-132 (teilweise abgedeckt), Sicherheit: unsicher)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig
- Gründe: Soll ['A', 'G'], Ist R

### P-12 – 12 Firmenjubiläum (NACHGEFRAGT)
- Frage: Unsere Firma (kein Verwerter) hat 2025 ihr Jubiläum öffentlich mit Kunden gefeiert und dafür eine Band aus selbständigen Musikern für 900 € engagiert. Es war die einzige Veranstaltung, sonst keine Aufträge an Künstler. Abgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '45.00'} (Referenz: F-02, Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2025; Leistung: Musik; Position 1: 900,00 € „Band aus selbständigen Musikern“, natürliche Person, Leistung: Musik: Komposition, Jingle, Arrangement, Musiker, Sänger, Audio-Design, DJ (künstlerisch/publizistisch); Rechnung von Auftragnehmer 1: 900,00 € gesamt (Rest vom System berechnet); Veranstaltungen: 1; Art des Auftraggebers: ausdrücklich unbekannt
- Verlauf: Antwort 1: Rückfrage nötig | Knopf verwerterart='Eigenwerbung' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Rückfragen: ['Wurden mit der/den Veranstaltung(en) Einnahmen erzielt oder beabsichtigt?'] | Nachtrag gesendet: 'Es ist Eigenwerbung für unsere Firma.' -> Rückfrage nötig
- Gründe: Soll ['A'], Ist R

### P-13 – 13 Eventagentur (NACHGEFRAGT)
- Frage: Wir sind eine Eventagentur und organisieren 2026 für einen Kunden ein Sommerfest. Die Band (selbständige Musiker) buchen und bezahlen wir im eigenen Namen, 4.000 €. Sind wir abgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag), Grenzfall → Steuerberater entscheidet (Referenz: R-33, R-74, R-78 (teilweise abgedeckt), Sicherheit: unsicher)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig
- Gründe: Soll ['A', 'G'], Ist R

### P-14 – 14 Bandleader (NACHGEFRAGT)
- Frage: Ich bin Bandleader, führe die Band unternehmerisch, schließe die Verträge mit Veranstaltern und habe 2025 an die selbständigen Bandmitglieder zusammen 4.000 € gezahlt. Muss ich dafür Abgabe zahlen?
- Soll: Abgabepflichtig (Vorschlag) (Referenz: I-16, Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig
- Gründe: Soll ['A'], Ist R

### P-16 – 16 Musikverein Konzerte (NACHGEFRAGT)
- Frage: Unser Hobbyorchester-Verein hatte 2026 vier Konzerte mit Eintritt. Wir haben einem selbständigen Gastsolisten 800 € gezahlt und unserem vereinseigenen Dirigenten 1.500 €. Abgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag), Grenzfall → Steuerberater entscheidet (Referenz: B-09, Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig
- Gründe: Soll ['N', 'G'], Ist R

### P-17 – 17 Chorleiter (NACHGEFRAGT)
- Frage: Unser Gesangverein ist vor allem gesellig, wir treten 2026 nur zweimal auf. Der Chorleiter bekommt 2.400 € im Jahr. Sind wir abgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: A-06, Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig
- Gründe: Soll ['N'], Ist R

### P-18a – 18 Musikunterricht (NACHGEFRAGT)
- Frage: Unser Musikverein unterrichtet 2025 15 Schüler gegen Gebühr. Sind wir deshalb abgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: B-06, Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig
- Gründe: Soll ['N'], Ist R

### P-20a – 20 Übungsleiterpauschale (NACHGEFRAGT)
- Frage: Unser gemeinnütziger Kunstverein zahlt 2025 einem nebenberuflichen Dirigenten insgesamt 2.500 €. Er hat schriftlich bestätigt, dass er dafür die Übungsleiterpauschale nutzt. Gehört das zur Bemessungsgrundlage?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: B-05, Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig
- Gründe: Soll ['N'], Ist R

### P-20b – 20 Übungsleiterpauschale (NACHGEFRAGT)
- Frage: Unser abgabepflichtiger gemeinnütziger Musikverein hat 2020 einer nebenberuflichen Chorleiterin 3.500 € gezahlt. Sie hat die Übungsleiterpauschale schriftlich bestätigt. Wie hoch ist die Abgabe?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'bemessungsgrundlage': '1100', 'abgabe': '46.20'} (Referenz: J-01, Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig
- Gründe: Soll ['A'], Ist R

### P-28 – 28 Umsatzsteuer (NACHGEFRAGT)
- Frage: Unsere Werbeagentur hat 2025 einem freien Fotografen (Einzelperson) 1.190 € brutto gezahlt, darin 190 € Umsatzsteuer gesondert ausgewiesen. Wie hoch ist die Bemessungsgrundlage?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'bemessungsgrundlage': '1000', 'abgabe': '50.00'} (Referenz: B-01, Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2025; Leistung: Fotografie; Art des Auftraggebers: Typischer Verwerter; Position 1: 1.190,00 € „Zahlung an freien Fotografen, brutto“, natürliche Person, Leistung: Fotografie (Werbe-, Foto-Design, künstlerische Fotografie) (künstlerisch/publizistisch); Position 2: 190,00 € „Umsatzsteuer gesondert ausgewiesen“ (gesondert ausgewiesene Umsatzsteuer), natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Rechnung von Auftragnehmer 1: 1.190,00 € gesamt (Rest vom System berechnet); Alle Positionen vom selben Auftragnehmer: ja; Rechnungsbetrag von Auftragnehmer 1: widersprüchlich (Ein Teilbetrag ist so hoch wie die ganze Rechnung.)
- Verlauf: Antwort 1: Rückfrage nötig | Rückfragen: ['Die Aufteilung der Rechnung von Auftragnehmer 1 ist unklar: Ein Teilbetrag ist so hoch wie die ganze Rechnung. Bitte nennen Sie den Rechnungsbetrag und die darin enthaltenen Teilbeträge.'] | Nachtrag gesendet: 'Wir sind typischer Verwerter (Werbung für Dritte).' -> Rückfrage nötig
- Gründe: Soll ['A'], Ist R

### P-32 – 32 Gestaltung plus Druck (NACHGEFRAGT)
- Frage: Unsere Werbeagentur hat 2026 einem freien Gestalter (Einzelperson) 1.200 € netto für die Gestaltung gezahlt und danach 800 € netto für die Vervielfältigung (Druck), getrennt abgerechnet. Wie hoch ist die Bemessungsgrundlage?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'bemessungsgrundlage': '1200', 'abgabe': '58.80'} (Referenz: Q-07, Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Grafik/Design; Art des Auftraggebers: Typischer Verwerter; Position 1: 1.200,00 € „Gestaltung“, natürliche Person, Leistung: Grafikdesign, Layout, Logo, Corporate Design, Kommunikationsdesign (künstlerisch/publizistisch); Position 2: 800,00 € „Vervielfältigung (Druck)“ (nachträgliche Vervielfältigung), natürliche Person, Leistung: Nachträgliche Vervielfältigung oder Druck nach Abschluss der künstlerischen Leistung (nicht künstlerisch); Rechnung von Auftragnehmer 1: 800,00 € gesamt (Rest vom System berechnet); Alle Positionen vom selben Auftragnehmer: ja; Rechnungsbetrag von Auftragnehmer 1: widersprüchlich (Ein Teilbetrag ist so hoch wie die ganze Rechnung.)
- Verlauf: Antwort 1: Rückfrage nötig | Rückfragen: ['Die Aufteilung der Rechnung von Auftragnehmer 1 ist unklar: Ein Teilbetrag ist so hoch wie die ganze Rechnung. Bitte nennen Sie den Rechnungsbetrag und die darin enthaltenen Teilbeträge.'] | Nachtrag gesendet: 'Wir sind typischer Verwerter (Werbung für Dritte).' -> Rückfrage nötig
- Gründe: Soll ['A'], Ist R

### P-34 – 34 Verwertungsgesellschaft (NACHGEFRAGT)
- Frage: Wir sind Konzertveranstalter und haben 2024 600 € an die GEMA gezahlt. Gehört das in die Bemessungsgrundlage der Künstlersozialabgabe?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: N-09, Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig
- Gründe: Soll ['N'], Ist R

### P-36 – 36 Agentur im Namen des Künstlers (NACHGEFRAGT)
- Frage: Wir sind eine Künstleragentur und handeln 2025 mit Vollmacht im Namen und für Rechnung einer Sängerin. Vertragspartner ist ein Veranstalter, der selbst abgabepflichtig ist. Müssen wir als Agentur Abgabe zahlen?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: I-18, Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig
- Gründe: Soll ['N'], Ist R

### P-37 – 37 Nur Kontakt vermittelt (NACHGEFRAGT)
- Frage: Ich nenne 2025 einem Veranstalter nur den Kontakt zu einem Musiker. Den Vertrag schließen die beiden selbst, ich organisiere nichts, kassiere kein Honorar und hafte für nichts. Bin ich abgabepflichtig?
- Soll: Grenzfall → Steuerberater entscheidet, Nicht abgabepflichtig (Vorschlag) (Referenz: I-20, Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig
- Gründe: Soll ['G', 'N'], Ist R

### P-40 – 40 Privatperson (NACHGEFRAGT)
- Frage: Wir sind ein Ehepaar und haben 2025 für unsere Silberhochzeit privat eine Musikgruppe für 1.500 € gebucht. Müssen wir Künstlersozialabgabe zahlen?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: K-02, Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig
- Gründe: Soll ['N'], Ist R

