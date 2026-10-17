# Prüfkatalog Stufe 1 – Lauf 2026-10-11 (Mistral (mistral-large-latest) – im KSK-Assistenten)

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Soll-Werte: `aufgaben/audit/testfall_haertetest_777.json`.

**Ergebnis: NICHT BESTANDEN**

- Fälle: 1, Dauer gesamt 14 s
- RICHTIG: 0, NACHGEFRAGT: 1, **FALSCH: 0**, FEHLER: 0
- Quote richtig bei Fällen mit sicherem Soll: 0 von 1 = 0 % (Ziel ≥ 90 %)
- Ziel Stufe 1: 0 FALSCH, 0 FEHLER, Quote ≥ 90 %.

| Fall | Fallgruppe | Soll | Ist | Bewertung | Dauer |
|---|---|---|---|---|---|
| H-777 | Härtetest Multi-Jahr-Kette Kultursommer GmbH | A/G | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 14.5 s |

## Abweichungen im Einzelnen

### H-777 – Härtetest Multi-Jahr-Kette Kultursommer GmbH (NACHGEFRAGT)
- Frage: Mein Mandant ist die Kultursommer GmbH, Veranstalterin eines Festival-Zyklus. Sie hat diese Rechnung erhalten:
Rechnungsteller: Panorama Kulturproduktionen GmbH, Berlin. Rechnung an: Kultursommer GmbH.
Nr.: RE-2026-777 · Datum: 15.01.2026 · Leistungszeitraum: 20.12.2025 – 10.01.2026 (Jahreswechsel).
Projekt „Winternächte Festival 2025/26“ mit insgesamt 2 Veranstaltungen (22.12.2025 und 08.01.2026).
Pos. 01 Bühnenbild-Entwurf durch freischaffende Bühnenbildnerin Clara Winter, im eigenen Namen der GmbH eingekauft: 4.800,00 €
Pos. 02 Abschlusskonzert: Pianist Jonas Falk. GmbH trat als Beauftragte der Kultursommer GmbH im Namen und für Rechnung der Kultursommer GmbH auf; Zahlung erhielt aber die Panorama GmbH (vertragswidrig): 3.200,00 €
Pos. 03 Lichtdesign-Workshop, eigene Veranstaltung der Kultursommer GmbH – Vertrag direkt zwischen Kultursommer GmbH und Lichtkünstlerin Mira Ade; auf dieser Rechnung nur als „Weiterleitung erhaltener Rechnung, unverändert durchgereicht“ ausgewiesen: 1.100,00 €
Pos. 04 Komponist Adam Stern, Werkauftrag. GmbH erhält als Zwischenhändler 15 % Vermittlungsprovision (480,00 €) vom Honorar 3.200,00 €; Rest 2.720,00 € zahlt die Kultursommer GmbH direkt an den Komponisten: 480,00 € (Prov.)
Pos. 05 Reisekosten Clara Winter, pauschal lt. Vertrag; Belege liegen laut Anhang vor (Bahn 96 €, Hotel 240 € = 336 € belegt), abgerechnet: 336,00 €
Pos. 06 Agentur-Pauschale der Panorama GmbH (Projektleitung, eigene Mitarbeiter): 2.900,00 €
Pos. 07 Tontechnik-Vermietung (nur Equipment, kein Personal), Subunternehmer TonVermiet N.V., Rotterdam/NL: 1.400,00 €
Pos. 08 Storno/Gutschrift: Block 03 aus Vorausrechnung vom 28.11.2025 (Grafik-Performance, Künstlerin hat abgesagt), bereits 2025 gezahlt: −950,00 €
Nettosumme (ausgewiesen): 13.266,00 € · USt 19 % (Position 03 ohne USt, reine Durchleitung): ausgewiesen 2.257,17 € · Rechnungsbetrag: 15.523,17 €.
Belegvermerk: Position 05 Belege „im Anhang“ – der Anhang liegt dieser Rechnung NICHT bei.
Ist das für meinen Mandanten künstlersozialabgabepflichtig, und wie hoch ist die Bemessungsgrundlage?
- Soll: Abgabepflichtig (Vorschlag), Grenzfall → Steuerberater entscheidet (Referenz: Soll der Testdatei (Entwurf): abgabepflichtig, BG 3.820 € (Pos. 03 + Direktanteil Pos. 04); strittig, Sicherheit: Entwurf der Testdatei, nicht geprüft; nur Ergebnisklasse)
- Ist: Grenzfall → Steuerberater entscheidet; Kern: Bemessungsgrundlage –, Abgabe –, ohne unsichere Leistungen 0.00, mit ihnen 343.98
- Fakten (System) bzw. Fundstellen (roh): Jahr: 2026; Art des Auftraggebers: Typischer Verwerter; Auftraggeber: GmbH/UG/AG; Rechnungsteller (an ihn wird gezahlt): GmbH/UG/AG; Position 1: 4.800,00 € „Bühnenbild-Entwurf durch freischaffende Bühnenbildnerin Clara Winter, im eigenen Namen der GmbH eingekauft“, GmbH/UG/AG, Leistung: Grafikdesign, Layout, Logo, Corporate Design, Kommunikationsdesign (künstlerisch/publizistisch), Auftragnehmer 1; Position 2: 3.200,00 € „Abschlusskonzert: Pianist Jonas Falk. GmbH trat als Beauftragte der Kultursommer GmbH im Namen und für Rechnung der Kultursommer GmbH auf; Zahlung erhielt aber die Panorama GmbH (vertragswidrig)“, natürliche Person, Leistung: Musik: Komposition, Jingle, Arrangement, Musiker, Sänger, Audio-Design, DJ (künstlerisch/publizistisch), nicht im eigenen Namen der Rechnungstellerin (Vertrag prüfen), Auftragnehmer 3; Position 3: 1.100,00 € „Lichtdesign-Workshop, eigene Veranstaltung der Kultursommer GmbH – Vertrag direkt zwischen Kultursommer GmbH und Lichtkünstlerin Mira Ade; auf dieser Rechnung nur als „Weiterleitung erhaltener Rechnung, unverändert durchgereicht“ ausgewiesen“, natürliche Person, Leistung: nicht eindeutig zuzuordnen, nicht im eigenen Namen der Rechnungstellerin (Vertrag prüfen), Auftragnehmer 4; Position 4: 480,00 € „Komponist Adam Stern, Werkauftrag. GmbH erhält als Zwischenhändler 15 % Vermittlungsprovision (480,00 €) vom Honorar 3.200,00 €“, GmbH/UG/AG, Leistung: Musik: Komposition, Jingle, Arrangement, Musiker, Sänger, Audio-Design, DJ (künstlerisch/publizistisch), nicht im eigenen Namen der Rechnungstellerin (Vertrag prüfen), Auftragnehmer 1; Position 5: 2.720,00 € „Komponist Adam Stern, Werkauftrag. Rest 2.720,00 € zahlt die Kultursommer GmbH direkt an den Komponisten“, natürliche Person, Leistung: Musik: Komposition, Jingle, Arrangement, Musiker, Sänger, Audio-Design, DJ (künstlerisch/publizistisch), nicht im eigenen Namen der Rechnungstellerin (Vertrag prüfen), Auftragnehmer 5; Position 6: 336,00 € „Reisekosten Clara Winter, pauschal lt. Vertrag; Belege liegen laut Anhang vor (Bahn 96 €, Hotel 240 € = 336 € belegt), abgerechnet: 336,00 €“, GmbH/UG/AG, Leistung: nicht im Regelwerk eingeordnet, Auftragnehmer 1; Position 7: 2.900,00 € „Agentur-Pauschale der Panorama GmbH (Projektleitung, eigene Mitarbeiter)“, GmbH/UG/AG, Leistung: nicht im Regelwerk eingeordnet, Auftragnehmer 1; Position 8: 1.400,00 € „Tontechnik-Vermietung (nur Equipment, kein Personal), Subunternehmer TonVermiet N.V., Rotterdam/NL“, GmbH/UG/AG, Leistung: Miete von Geräten oder Sachmitteln (Kamera, Licht, Ton, Equipment) (Grenzfall), Auftragnehmer 1; Position 9: -950,00 € „Storno/Gutschrift: Block 03 aus Vorausrechnung vom 28.11.2025 (Grafik-Performance, Künstlerin hat abgesagt), bereits 2025 gezahlt“, GmbH/UG/AG, Leistung: Grafikdesign, Layout, Logo, Corporate Design, Kommunikationsdesign (künstlerisch/publizistisch), Auftragnehmer 1; Rechnung von Auftragnehmer 1: 15.523,17 € gesamt (Rest vom System berechnet); Alle Positionen vom selben Auftragnehmer: nein; Veranstaltungen: 2
- Verlauf: Antwort 1: Rückfrage nötig | Knopf verwerterart='Typischer Verwerter' | -> Grenzfall → Steuerberater entscheidet
- Gründe: 1 Rückfrage(n), nötig laut Soll höchstens 0

