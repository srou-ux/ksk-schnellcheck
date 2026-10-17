# Chatbot direkt getestet – 2026-10-15 (Chatbot direkt (Browser) – Mistral (EU))

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Soll-Werte: `aufgaben/audit/taetigkeitskatalog_200.json`. Code-Stand `031309a`.
Jeder Fall wurde an der echten Weboberfläche gespielt: tippen, Knöpfe klicken, Fakten bestätigen.

- Fälle: 20, Dauer 138 s
- RICHTIG: 10, NACHGEFRAGT: 5, **FALSCH: 5**, FEHLER: 0

| Fall | Fallgruppe | Soll | Ist | Bewertung | Rückfragen | Dauer |
|---|---|---|---|---|---|---|
| TK-A-01 | Tätigkeit A | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 5.5 s |
| TK-A-11 | Tätigkeit A | N | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0 | 10.7 s |
| TK-B-21 | Tätigkeit B | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 7.3 s |
| TK-B-24 | Tätigkeit B | G/R | Abgabepflichtig (Vorschlag) | **FALSCH** | 0 | 3.9 s |
| TK-C-43 | Tätigkeit C | A | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0 | 3.6 s |
| TK-C-50 | Tätigkeit C | G/R | Abgabepflichtig (Vorschlag) | **FALSCH** | 0 | 5.4 s |
| TK-D-63 | Tätigkeit D | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 14.0 s |
| TK-D-66 | Tätigkeit D | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 9.4 s |
| TK-E-81 | Tätigkeit E | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 8.8 s |
| TK-F-101 | Tätigkeit F | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 5.0 s |
| TK-F-111 | Tätigkeit F | G/R | Nicht abgabepflichtig (Vorschlag) | **FALSCH** | 0 | 7.0 s |
| TK-F-113 | Tätigkeit F | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 14.3 s |
| TK-F-117 | Tätigkeit F | G/R | Abgabepflichtig (Vorschlag) | **FALSCH** | 0 | 4.1 s |
| TK-G-122 | Tätigkeit G | N | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0 | 5.1 s |
| TK-G-124 | Tätigkeit G | G/R | Grenzfall → Steuerberater entscheidet | **RICHTIG** | 0 | 4.1 s |
| TK-H-143 | Tätigkeit H | G/R | Grenzfall → Steuerberater entscheidet | **RICHTIG** | 0 | 5.0 s |
| TK-H-153 | Tätigkeit H | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 4.4 s |
| TK-I-161 | Tätigkeit I | N | Abgabepflichtig (Vorschlag) | **FALSCH** | 0 | 7.6 s |
| TK-J-191 | Tätigkeit J | N | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0 | 5.2 s |
| TK-J-199 | Tätigkeit J | N | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0 | 7.4 s |

## Abweichungen

### TK-A-11 – Tätigkeit A (NACHGEFRAGT)
- Ist: Grenzfall → Steuerberater entscheidet; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | Bestätigt: Jahr: 2026; Leistung: technische Zeichnung; Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Position 1: 2.000,00 € „technische Zeichnung (Bauzeichnung)“, natürliche Person, Leistung: Technische Zeichnung (Bau-, CAD-, Konstruktionszeichnung) (Grenzfall); Rechnung von Auftragnehmer 1: 2.000,00 € gesamt (Rest vom System berechnet) | 'Ja, das stimmt' -> Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['N'], Ist G

### TK-B-24 – Tätigkeit B (FALSCH)
- Ist: Abgabepflichtig (Vorschlag); Bemessungsgrundlage 2000, Abgabe 98.00
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | Bestätigt: Jahr: 2026; Leistung: Musik; Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Gesamtbetrag (Aufteilung auf Rechnungen unbekannt): 2.000,00 €, natürliche Person, Leistung: Musik: Komposition, Jingle, Arrangement, Musiker, Sänger, Audio-Design, DJ (künstlerisch/publizistisch) | 'Ja, das stimmt' -> Abgabepflichtig (Vorschlag)
- Gründe: Soll ['G', 'R'], Ist A (Abgabepflichtig (Vorschlag))

### TK-C-43 – Tätigkeit C (NACHGEFRAGT)
- Ist: Grenzfall → Steuerberater entscheidet; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | Bestätigt: Jahr: 2026; Leistung: Darstellende Kunst; Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Gesamtbetrag (Aufteilung auf Rechnungen unbekannt): 2.000,00 €, natürliche Person, Leistung: nicht eindeutig zuzuordnen | 'Ja, das stimmt' -> Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['A'], Ist G

### TK-C-50 – Tätigkeit C (FALSCH)
- Ist: Abgabepflichtig (Vorschlag); Bemessungsgrundlage 2000, Abgabe 98.00
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | Bestätigt: Jahr: 2026; Leistung: Moderation; Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Position 1: 2.000,00 € „Moderator (nur durchs Interview leiten)“, natürliche Person, Leistung: Moderation (Veranstaltung, Show, Medien) (künstlerisch/publizistisch); Rechnung von Auftragnehmer 1: 2.000,00 € gesamt (Rest vom System berechnet) | 'Ja, das stimmt' -> Abgabepflichtig (Vorschlag)
- Gründe: Soll ['G', 'R'], Ist A (Abgabepflichtig (Vorschlag))

### TK-F-111 – Tätigkeit F (FALSCH)
- Ist: Nicht abgabepflichtig (Vorschlag); Bemessungsgrundlage 0, Abgabe 0.00
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | Bestätigt: Jahr: 2026; Leistung: SEO-Beratung; Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Position 1: 2.000,00 € „SEO-Beratung“, natürliche Person, Leistung: Suchmaschinenoptimierung (SEO) (nicht künstlerisch); Rechnung von Auftragnehmer 1: 2.000,00 € gesamt (Rest vom System berechnet) | 'Ja, das stimmt' -> Nicht abgabepflichtig (Vorschlag)
- Gründe: Soll ['G', 'R'], Ist N (Nicht abgabepflichtig (Vorschlag))

### TK-F-117 – Tätigkeit F (FALSCH)
- Ist: Abgabepflichtig (Vorschlag); Bemessungsgrundlage 2000, Abgabe 98.00
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | Bestätigt: Jahr: 2026; Leistung: Influencer (Product-Placement); Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Position 1: 2.000,00 €, natürliche Person, Leistung: Influencer (Werbefotos, Werbevideos, Werbetexte) (künstlerisch/publizistisch) | 'Ja, das stimmt' -> Abgabepflichtig (Vorschlag)
- Gründe: Soll ['G', 'R'], Ist A (Abgabepflichtig (Vorschlag))

### TK-G-122 – Tätigkeit G (NACHGEFRAGT)
- Ist: Grenzfall → Steuerberater entscheidet; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | Bestätigt: Jahr: 2026; Leistung: Gestecke; Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Position 1: 2.000,00 € „Gestecke“, natürliche Person, Leistung: nicht im Regelwerk eingeordnet; Rechnung von Auftragnehmer 1: 2.000,00 € gesamt (Rest vom System berechnet) | 'Ja, das stimmt' -> Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['N'], Ist G

### TK-I-161 – Tätigkeit I (FALSCH)
- Ist: Abgabepflichtig (Vorschlag); Bemessungsgrundlage 2000, Abgabe 98.00
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | Bestätigt: Jahr: 2026; Leistung: Text/Redaktion; Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Position 1: 2.000,00 € „Pressesprecher für die Firma“, natürliche Person, Leistung: Werbetexte, Texter, Redaktion, Journalismus (künstlerisch/publizistisch); Rechnung von Auftragnehmer 1: 2.000,00 € gesamt (Rest vom System berechnet) | 'Ja, das stimmt' -> Abgabepflichtig (Vorschlag)
- Gründe: Soll ['N'], Ist A (Abgabepflichtig (Vorschlag))

### TK-J-191 – Tätigkeit J (NACHGEFRAGT)
- Ist: Grenzfall → Steuerberater entscheidet; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | Bestätigt: Jahr: 2026; Leistung: Musikauswahl, Playlist, Kuratierung ohne eigene Musik; Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Gesamtbetrag (Aufteilung auf Rechnungen unbekannt): 2.000,00 €, natürliche Person, Leistung: Musikauswahl, Playlist, Kuratierung ohne eigene Musik (Grenzfall) | 'Ja, das stimmt' -> Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['N'], Ist G

### TK-J-199 – Tätigkeit J (NACHGEFRAGT)
- Ist: Grenzfall → Steuerberater entscheidet; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | Bestätigt: Jahr: 2026; Leistung: Fotogrammetrie, Vermessung; Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Position 1: 2.000,00 € „Fotogrammetrie (Vermessung)“, natürliche Person, Leistung: Fotogrammetrie, Vermessung (technische Bildaufnahme) (Grenzfall); Rechnung von Auftragnehmer 1: 2.000,00 € gesamt (Rest vom System berechnet) | 'Ja, das stimmt' -> Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['N'], Ist G

