# Chatbot direkt getestet – 2026-10-15 (Chatbot direkt (Browser) – Mistral (EU))

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Soll-Werte: `aufgaben/audit/taetigkeitskatalog_200.json`. Code-Stand `031309a`.
Jeder Fall wurde an der echten Weboberfläche gespielt: tippen, Knöpfe klicken, Fakten bestätigen.

- Fälle: 20, Dauer 134 s
- RICHTIG: 10, NACHGEFRAGT: 5, **FALSCH: 5**, FEHLER: 0

| Fall | Fallgruppe | Soll | Ist | Bewertung | Rückfragen | Dauer |
|---|---|---|---|---|---|---|
| TK-A-01 | Tätigkeit A | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 8.6 s |
| TK-A-11 | Tätigkeit A | N | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0 | 3.3 s |
| TK-B-21 | Tätigkeit B | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 3.3 s |
| TK-B-24 | Tätigkeit B | G/R | Abgabepflichtig (Vorschlag) | **FALSCH** | 0 | 8.7 s |
| TK-C-43 | Tätigkeit C | A | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0 | 7.4 s |
| TK-C-50 | Tätigkeit C | G/R | Abgabepflichtig (Vorschlag) | **FALSCH** | 0 | 3.6 s |
| TK-D-63 | Tätigkeit D | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 3.0 s |
| TK-D-66 | Tätigkeit D | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 3.5 s |
| TK-E-81 | Tätigkeit E | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 13.6 s |
| TK-F-101 | Tätigkeit F | A | Abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 7.0 s |
| TK-F-111 | Tätigkeit F | G/R | Nicht abgabepflichtig (Vorschlag) | **FALSCH** | 0 | 6.9 s |
| TK-F-113 | Tätigkeit F | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 10.6 s |
| TK-F-117 | Tätigkeit F | G/R | Abgabepflichtig (Vorschlag) | **FALSCH** | 0 | 3.3 s |
| TK-G-122 | Tätigkeit G | N | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0 | 5.7 s |
| TK-G-124 | Tätigkeit G | G/R | Grenzfall → Steuerberater entscheidet | **RICHTIG** | 0 | 13.8 s |
| TK-H-143 | Tätigkeit H | G/R | Grenzfall → Steuerberater entscheidet | **RICHTIG** | 0 | 4.8 s |
| TK-H-153 | Tätigkeit H | N | Nicht abgabepflichtig (Vorschlag) | **RICHTIG** | 0 | 7.6 s |
| TK-I-161 | Tätigkeit I | N | Abgabepflichtig (Vorschlag) | **FALSCH** | 0 | 8.1 s |
| TK-J-191 | Tätigkeit J | N | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0 | 7.5 s |
| TK-J-199 | Tätigkeit J | N | Grenzfall → Steuerberater entscheidet | **NACHGEFRAGT** | 0 | 3.6 s |

## Abweichungen

### TK-A-11 – Tätigkeit A (NACHGEFRAGT)
- Ist: Grenzfall → Steuerberater entscheidet; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | Bestätigt: Jahr: 2026; Leistung: technische Zeichnung (Bauzeichnung); Art des Auftraggebers: Typischer Verwerter; Position 1: 2.000,00 € „technische Zeichnung (Bauzeichnung)“, natürliche Person, Leistung: Technische Zeichnung (Bau-, CAD-, Konstruktionszeichnung) (Grenzfall) | 'Ja, das stimmt' -> Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['N'], Ist G

### TK-B-24 – Tätigkeit B (FALSCH)
- Ist: Abgabepflichtig (Vorschlag); Bemessungsgrundlage 2000, Abgabe 98.00
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | Bestätigt: Jahr: 2026; Leistung: Musik; Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Position 1: 2.000,00 € „DJ (Musik mixt live)“, natürliche Person, Leistung: Musik: Komposition, Jingle, Arrangement, Musiker, Sänger, Audio-Design, DJ (künstlerisch/publizistisch); Rechnung von Auftragnehmer 1: 2.000,00 € gesamt (Rest vom System berechnet) | 'Ja, das stimmt' -> Abgabepflichtig (Vorschlag)
- Gründe: Soll ['G', 'R'], Ist A (Abgabepflichtig (Vorschlag))

### TK-C-43 – Tätigkeit C (NACHGEFRAGT)
- Ist: Grenzfall → Steuerberater entscheidet; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | Bestätigt: Jahr: 2026; Leistung: Musikvideo; Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Position 1: 2.000,00 € „Tänzer (Musikvideo)“, natürliche Person, Leistung: nicht eindeutig zuzuordnen; Rechnung von Auftragnehmer 1: 2.000,00 € gesamt (Rest vom System berechnet) | 'Ja, das stimmt' -> Grenzfall → Steuerberater entscheidet
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
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | Bestätigt: Jahr: 2026; Leistung: Influencer (Werbefotos, Werbevideos, Werbetexte); Art des Auftraggebers: Typischer Verwerter; Position 1: 2.000,00 € „Influencer (Product-Placement)“, natürliche Person, Leistung: Influencer (Werbefotos, Werbevideos, Werbetexte) (künstlerisch/publizistisch) | 'Ja, das stimmt' -> Abgabepflichtig (Vorschlag)
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
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | Bestätigt: Jahr: 2026; Leistung: Musikauswahl, Playlist, Kuratierung ohne eigene Musik; Art des Auftraggebers: Typischer Verwerter; Auftragnehmer: natürliche Person; Position 1: 2.000,00 € „Musikdaten-Kurator (Playlist)“, natürliche Person, Leistung: Musikauswahl, Playlist, Kuratierung ohne eigene Musik (Grenzfall); Rechnung von Auftragnehmer 1: 2.000,00 € gesamt (Rest vom System berechnet) | 'Ja, das stimmt' -> Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['N'], Ist G

### TK-J-199 – Tätigkeit J (NACHGEFRAGT)
- Ist: Grenzfall → Steuerberater entscheidet; Bemessungsgrundlage –, Abgabe –
- Verlauf: Frage gesendet -> Faktenbestätigung nötig | Bestätigt: Jahr: 2026; Leistung: Fotogrammetrie (Vermessung); Art des Auftraggebers: Typischer Verwerter; Position 1: 2.000,00 € „Fotogrammetrie (Vermessung)“, natürliche Person, Leistung: Fotogrammetrie, Vermessung (technische Bildaufnahme) (Grenzfall) | 'Ja, das stimmt' -> Grenzfall → Steuerberater entscheidet
- Gründe: Soll ['N'], Ist G

