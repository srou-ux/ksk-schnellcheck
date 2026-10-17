# Prüfkatalog Stufe 1 – Lauf 2026-10-11 (Demo-Modus (FakeLLM))

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Soll-Werte: `aufgaben/audit/pruefkatalog.json`.

**Ergebnis: NICHT BESTANDEN**

- Fälle: 52, Dauer gesamt 0 s
- RICHTIG: 32, NACHGEFRAGT: 19, **FALSCH: 1**, FEHLER: 0
- Quote richtig bei Fällen mit sicherem Soll: 28 von 48 = 58 % (Ziel ≥ 90 %)
- Ziel Stufe 1: 0 FALSCH, 0 FEHLER, Quote ≥ 90 %.

| Fall | Fallgruppe | Soll | Ist | Bewertung | Dauer |
|---|---|---|---|---|---|
| P-01 | 01 Logo | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-02 | 02 Website | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-03 | 03 Großer Werbeauftrag | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-04a | 04 Viele kleine Rechnungen | A | Nicht abgabepflichtig (Vorschlag) | **FALSCH** | 0.0 s |
| P-04b | 04 Viele kleine Rechnungen | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-05 | 05 Werbeagentur | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-06 | 06 Verlag | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-07 | 07 Nutzung zur Einnahmeerzielung | A | Rückfrage nötig | **NACHGEFRAGT** | 0.0 s |
| P-08 | 08 Bis zu drei Veranstaltungen | N | Rückfrage nötig | **NACHGEFRAGT** | 0.0 s |
| P-09 | 09 Vier Veranstaltungen | A | Rückfrage nötig | **NACHGEFRAGT** | 0.0 s |
| P-10 | 10 Konzertveranstalter | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-11 | 11 Restaurant mit Livemusik | A/G | Rückfrage nötig | **NACHGEFRAGT** | 0.0 s |
| P-12 | 12 Firmenjubiläum | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-13 | 13 Eventagentur | A/G | Rückfrage nötig | **NACHGEFRAGT** | 0.0 s |
| P-14 | 14 Bandleader | A | Rückfrage nötig | **NACHGEFRAGT** | 0.0 s |
| P-15 | 15 Gemeinnütziger Verein | A | Rückfrage nötig | **NACHGEFRAGT** | 0.0 s |
| P-16 | 16 Musikverein Konzerte | N/G | Rückfrage nötig | **NACHGEFRAGT** | 0.0 s |
| P-17 | 17 Chorleiter | N | Rückfrage nötig | **NACHGEFRAGT** | 0.0 s |
| P-18a | 18 Musikunterricht | N | Rückfrage nötig | **NACHGEFRAGT** | 0.0 s |
| P-18b | 18 Musikunterricht | R/G | Rückfrage nötig | **RICHTIG** | 0.0 s |
| P-19 | 19 Verein Website/Flyer | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-20a | 20 Übungsleiterpauschale | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-20b | 20 Übungsleiterpauschale | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-21 | 21 Einzelunternehmer | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-22 | 22 GbR | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-23 | 23 GmbH | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-24 | 24 KG/OHG | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-25 | 25 Nicht KSK-versichert | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-26 | 26 Rentner/Student | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-27 | 27 Künstler im Ausland | A/G | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-28 | 28 Umsatzsteuer | A | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0.0 s |
| P-29 | 29 Material/Nebenkosten | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-30 | 30 Reisekosten | A | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0.0 s |
| P-31 | 31 Bewirtung | A | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0.0 s |
| P-32 | 32 Gestaltung plus Druck | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-33 | 33 Nutzungsrechte | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-34 | 34 Verwertungsgesellschaft | N | Rückfrage nötig | **NACHGEFRAGT** | 0.0 s |
| P-35 | 35 Entwurf nicht verwendet | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-36 | 36 Agentur im Namen des Künstlers | N | Rückfrage nötig | **NACHGEFRAGT** | 0.0 s |
| P-37 | 37 Nur Kontakt vermittelt | G/N | Rückfrage nötig | **NACHGEFRAGT** | 0.0 s |
| P-38 | 38 Agentur im eigenen Namen | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| P-39 | 39 Auszahlung an Dritten | A/G | Grenzfall → Steuerberater entscheidet | **RICHTIG** | 0.0 s |
| P-40 | 40 Privatperson | N | Rückfrage nötig | **NACHGEFRAGT** | 0.0 s |
| P-52 | 52 Derselbe Künstler, mehrere Positionen | A | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0.0 s |
| K-01 | Kontrolle: Jahr fehlt | R | Rückfrage nötig | **RICHTIG** | 0.0 s |
| K-02 | Kontrolle: Jahr ohne Quelle | X/R | Nicht abgedeckt (Quelle fehlt) | **RICHTIG** | 0.0 s |
| K-03 | Kontrolle: Auskunft | AUSKUNFT | Rückfrage nötig | **NACHGEFRAGT** | 0.0 s |
| K-04 | Kontrolle: Schwelle 2025 | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| K-05 | Kontrolle: Schwelle 2026 | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| K-06 | Kontrolle: genau auf der Schwelle | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |
| K-07 | Kontrolle: Einnahmeabsicht unbekannt | R/G | Rückfrage nötig | **RICHTIG** | 0.0 s |
| K-08 | Kontrolle: Einschleusung | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0.0 s |

## Abweichungen im Einzelnen

### P-04a – 04 Viele kleine Rechnungen (FALSCH)
- Frage: Ein selbständiger Grafiker (Einzelperson) hat uns 2026 fünfmal kleine Werbegrafiken für unsere eigene Werbung gestaltet, jede Rechnung 250 € netto. Sonst keine Aufträge. Abgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '61.25'} (Referenz: F-03, Sicherheit: fest)
- Ist: Nicht abgabepflichtig (Vorschlag); Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Grafik/Design; Art des Auftraggebers: Eigenwerbung; Auftragnehmer: natürliche Person; Position 1: 250,00 €, natürliche Person, Leistung: Grafikdesign, Layout, Logo, Corporate Design, Kommunikationsdesign (künstlerisch/publizistisch)
- Verlauf: Antwort 1: Nicht abgabepflichtig (Vorschlag)
- Gründe: Soll ['A'], Ist N (Nicht abgabepflichtig (Vorschlag))

### P-07 – 07 Nutzung zur Einnahmeerzielung (NACHGEFRAGT)
- Frage: Wir sind ein Unternehmen ohne Kunstbezug. 2025 haben wir von einem freien Fotografen (Einzelperson) für 3.000 € netto Fotos erstellen lassen, die wir gegen Entgelt an Dritte lizenzieren, also um Einnahmen zu erzielen. Keine Veranstaltungen. Abgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '150.00'} (Referenz: R-12 (vgl. N-03, Fassung B), Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig | Knopf verwerterart='Veranstalter (Generalklausel)' | -> Rückfrage nötig | Rückfragen: ['Wie viele einschlägige Veranstaltungen gab es in dem Jahr?'] | Nachtrag gesendet: 'Generalklausel: Wir wollen mit den Fotos Einnahmen erzielen.' -> Rückfrage nötig
- Gründe: Soll ['A'], Ist R

### P-08 – 08 Bis zu drei Veranstaltungen (NACHGEFRAGT)
- Frage: Unser Unternehmen (kein Veranstalter von Beruf) hat 2025 drei Veranstaltungen mit bezahlten selbständigen Künstlern durchgeführt, Gagen zusammen 5.000 €. Wir wollten damit Einnahmen erzielen. Sonst keine Aufträge an Künstler. Abgabepflichtig?
- Soll: Nicht abgabepflichtig (Vorschlag) (Referenz: D-03, Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig | Knopf verwerterart='Veranstalter (Generalklausel)' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Rückfragen: ['Wie viele einschlägige Veranstaltungen gab es in dem Jahr?'] | Nachtrag gesendet: 'Generalklausel, drei Veranstaltungen, Einnahmeabsicht ja.' -> Rückfrage nötig
- Gründe: Soll ['N'], Ist R

### P-09 – 09 Vier Veranstaltungen (NACHGEFRAGT)
- Frage: Unser Unternehmen (kein Veranstalter von Beruf) hat 2025 vier Veranstaltungen mit bezahlten selbständigen Künstlern durchgeführt, Gagen zusammen 5.000 €. Wir wollten damit Einnahmen erzielen. Sonst keine Aufträge an Künstler. Abgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '250.00'} (Referenz: D-04, Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig | Knopf verwerterart='Veranstalter (Generalklausel)' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Rückfragen: ['Wie viele einschlägige Veranstaltungen gab es in dem Jahr?'] | Nachtrag gesendet: 'Generalklausel, vier Veranstaltungen, Einnahmeabsicht ja.' -> Rückfrage nötig
- Gründe: Soll ['A'], Ist R

### P-11 – 11 Restaurant mit Livemusik (NACHGEFRAGT)
- Frage: Unser Restaurant hat 2025 jeden Freitag Livemusik, also rund 50 Abende, damit mehr Gäste kommen. Die selbständigen Musiker bekamen zusammen 6.000 €. Abgabepflichtig?
- Soll: Abgabepflichtig (Vorschlag), Grenzfall → Steuerberater entscheidet (Referenz: R-29, R-36, R-132 (teilweise abgedeckt), Sicherheit: unsicher)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig
- Gründe: Soll ['A', 'G'], Ist R

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

### P-15 – 15 Gemeinnütziger Verein (NACHGEFRAGT)
- Frage: Unser gemeinnütziger Kulturverein hat 2025 fünf Konzerte mit Eintritt veranstaltet und den selbständigen Musikern zusammen 3.000 € gezahlt. Wir wollten Einnahmen erzielen. Sind wir als gemeinnütziger Verein befreit?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'abgabe': '150.00'} (Referenz: R-50 (KSK-Info 23), Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig | Knopf verwerterart='Veranstalter (Generalklausel)' | -> Rückfrage nötig | Knopf auftragnehmer_typ='natürliche Person' | -> Rückfrage nötig | Rückfragen: ['Wie viele einschlägige Veranstaltungen gab es in dem Jahr?'] | Nachtrag gesendet: 'Generalklausel, fünf Veranstaltungen, Einnahmeabsicht ja.' -> Rückfrage nötig
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

### P-28 – 28 Umsatzsteuer (NACHGEFRAGT)
- Frage: Unsere Werbeagentur hat 2025 einem freien Fotografen (Einzelperson) 1.190 € brutto gezahlt, darin 190 € Umsatzsteuer gesondert ausgewiesen. Wie hoch ist die Bemessungsgrundlage?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'bemessungsgrundlage': '1000', 'abgabe': '50.00'} (Referenz: B-01, Sicherheit: fest)
- Ist: Grenzfall → Steuerberater entscheidet; Kern: Bemessungsgrundlage –, Abgabe –, ohne unsichere Leistungen 0.00, mit ihnen 59.50
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2025; Leistung: Fotografie; Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Position 1: 1.000,00 € „gezahlt“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet, Auftragnehmer 1; Position 2: 190,00 € „Umsatzsteuer gesondert ausgewiesen“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet, Auftragnehmer 1; Rechnung von Auftragnehmer 1: 1.190,00 € gesamt (Rest vom System berechnet)
- Verlauf: Antwort 1: Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['A'], Ist G

### P-30 – 30 Reisekosten (NACHGEFRAGT)
- Frage: Unsere Werbeagentur hat 2025 einem freien Designer (Einzelperson) 3.000 € Honorar gezahlt und zusätzlich 80 € nachgewiesene Bahnfahrtkosten erstattet. Wie hoch ist die Bemessungsgrundlage?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'bemessungsgrundlage': '3000', 'abgabe': '150.00'} (Referenz: B-03, Sicherheit: fest)
- Ist: Grenzfall → Steuerberater entscheidet; Kern: Bemessungsgrundlage –, Abgabe –, ohne unsichere Leistungen 0.00, mit ihnen 154.00
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2025; Leistung: Grafik/Design; Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Position 1: 3.000,00 € „Honorar gezahlt“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Position 2: 80,00 € „nachgewiesene Bahnfahrtkosten erstattet“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet
- Verlauf: Antwort 1: Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['A'], Ist G

### P-31 – 31 Bewirtung (NACHGEFRAGT)
- Frage: Wir sind eine Konzertdirektion. 2024 haben wir einer selbständigen Sängerin (Einzelperson) 1.000 € Gage gezahlt und sie zusätzlich üblich mit Essen und Getränken im Wert von 80 € bewirtet. Wie hoch ist die Bemessungsgrundlage?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'bemessungsgrundlage': '1000', 'abgabe': '50.00'} (Referenz: N-11, Sicherheit: fest)
- Ist: Grenzfall → Steuerberater entscheidet; Kern: Bemessungsgrundlage –, Abgabe –, ohne unsichere Leistungen 0.00, mit ihnen 54.00
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2024; Leistung: Musik; Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Position 1: 1.000,00 € „Gage gezahlt“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Position 2: 80,00 € „bewirtet“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet
- Verlauf: Antwort 1: Rückfrage nötig | Knopf verwerterart='Typischer Verwerter' | -> Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['A'], Ist G

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

### P-52 – 52 Derselbe Künstler, mehrere Positionen (NACHGEFRAGT)
- Frage: Unsere Werbeagentur hat 2026 eine Rechnung von einer freien Webdesignerin (Einzelperson) bekommen, alles von ihr: Webdesign 2.000 € netto, Programmierung des Backends 1.000 € netto, Miete für Kamera-Equipment 200 € netto, Druckkosten für den Nachdruck der fertigen Flyer 500 € netto. Wie hoch ist die Abgabe?
- Soll: Abgabepflichtig (Vorschlag); Zahl: {'bemessungsgrundlage': '3200', 'abgabe': '156.80'} (Referenz: R-117, R-42, R-175, R-49 (abgeleitet, 11.10.2026), Sicherheit: abgeleitet – vom Steuerberater zu prüfen)
- Ist: Grenzfall → Steuerberater entscheidet; Kern: Bemessungsgrundlage –, Abgabe –, ohne unsichere Leistungen 0.00, mit ihnen 181.30
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Leistung: Grafik/Design; Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Position 1: 2.000,00 €, natürliche Person, Leistung: nicht eindeutig zuzuordnen; Position 2: 1.000,00 €, natürliche Person, Leistung: nicht eindeutig zuzuordnen; Position 3: 200,00 €, natürliche Person, Leistung: nicht eindeutig zuzuordnen; Position 4: 500,00 €, natürliche Person, Leistung: nicht eindeutig zuzuordnen; Alle Positionen vom selben Auftragnehmer: ja
- Verlauf: Antwort 1: Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['A'], Ist G

### K-03 – Kontrolle: Auskunft (NACHGEFRAGT)
- Frage: Wie hoch ist der Abgabesatz der Künstlersozialabgabe im Jahr 2024?
- Soll: Auskunft aus dem Regelwerk (Referenz: Blatt Abgabesätze, Sicherheit: fest)
- Ist: Rückfrage nötig; Kern: Bemessungsgrundlage –, Abgabe –
- Fakten (System) bzw. Fundstellen (roh): –
- Verlauf: Antwort 1: Rückfrage nötig
- Gründe: Soll ['AUSKUNFT'], Ist R

