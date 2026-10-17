# Chatbot für Steuerberater und Agenturen – Abdeckung der Quellen (Entwurf)

Ziel: Der Chatbot beantwortet Fragen so, als wäre er KSK-Experte/Rechtsanwalt – aber nur mit Belegen aus öffentlichen Quellen. Kein Raten: Fehlt die Quelle, sagt er „nicht abgedeckt" und nennt, was fehlt.

## Antwortklassen
Abgabepflichtig (Vorschlag) / Nicht abgabepflichtig (Vorschlag) / Grenzfall → Steuerberater entscheidet / Rückfrage nötig / Nicht abgedeckt (Quelle fehlt). Jede Antwort mit Fundstelle und Rechtsstand (Jahr, Fassung).

## Stand der Abdeckung (08.10.2026)
- Regelkatalog: 236 Regeln (R-01 bis R-236), Testfälle: 329, Fragenkatalog: 191 Fragen (159 mit Regel, 23 nur teilweise, 9 sichtbare Lücken).
- Prüfung: `python tests/pruefe_regelwerk.py` (formal). Inhaltliche Prüfung: zwei unabhängige Audits gegen die Quellen, Korrekturen eingearbeitet. Endabnahme durch Steuerberater/Fachanwalt steht aus.

## Themenfelder und Stand der Quellen
| Themenfeld | Quellen im Repo | Regeln | Status |
|---|---|---|---|
| Typische Verwerter (§ 24 Abs. 1) | KSVG, Infos 01, 01a, 02, 03, 07, 08, 11, 13–16, 21, Checklisten | R-01–R-09, R-119–R-130, R-152–R-160 | ausgewertet |
| Eigenwerbung / Generalklausel (§ 24 Abs. 2) | KSVG A/B, Infos 04, 05, 12, Checkliste Eigenwerber, BSG 2010–2022 | R-10–R-40, R-60–R-66, R-132, R-149, R-150, R-180–R-188 | ausgewertet |
| Künstler-/Publizistenbegriff | Infos 06, 09, FAQ | R-137, R-140, Tätigkeitskatalog | ausgewertet (Katalog), Einzelfälle teils offen |
| Bemessungsgrundlage (§ 25) | Info 10, 24, 24a, KSVEntgV, Checklisten, Merkblatt GmbH | R-41–R-59, R-68, R-69, R-172–R-177, R-199–R-203 | ausgewertet |
| Vermittlung/Vertretung | Info 27, Info 01, 26 | R-33–R-39, R-73–R-78, R-166, R-167 | ausgewertet |
| Ausland | KSVG § 25 Abs. 4, Info 22, Checklisten | R-27, R-37, R-70–R-72, R-178–R-179, R-189–R-190 | ausgewertet |
| Meldung, Vorauszahlung, Berechnung | KSVG §§ 26–30, Info 01, Abgabesätze | R-79–R-90, R-161–R-165 | ausgewertet |
| Prüfung, DRV | Infos 17, 18, DRV K5000/K5006, KSVGBeitrÜV | R-83–R-88, R-147, R-151, R-204 | ausgewertet |
| Verjährung, Säumnis, Bußgeld | KSVG, SGB IV | R-85–R-87, R-163 | ausgewertet; Fälligkeitsjahr nicht abschließend |
| Ausgleichsvereinigung, Erstattung | KSVG §§ 32, 33, Info 19 | R-168–R-171 | ausgewertet |
| Rechtsprechung | 12 BSG-Urteile (2010 ×2, 2014 ×3, 2015, 2017, 2019 ×2, 2020 ×2, 2022) und 1 LSG-Urteil (2010) im Volltext | R-60–R-66, R-216–R-226, R-233, R-234 | Rn.-Zitate geprüft; Rechtsform (KG/OHG/GbR), Zwischenverwerter, Gewinnzuweisung, Rücknahme, Säumniszuschlag ausgewertet; Webdesign-Urteile 2005 und weitere LSG/SG fehlen |
| Rechtsbehelfe | SGG, SGB X, KSVG § 39 (Momentaufnahme 08.10.2026) | R-227–R-232 | ausgewertet; aufschiebende Wirkung ist Ableitung, kein Urteil |

## Sichtbare Lücken (Chatbot antwortet „nicht abgedeckt“)
LSG-/SG-Rechtsprechung (sechs Entscheidungen nur als Sekundärquelle ohne Volltext, siehe `quellen/ergaenzend/urteile/LISTE_LSG_SG.md`), neuere BSG-Urteile nach 2022 (Recherche: keine zur Abgabepflicht von Unternehmen vorhanden), ältere BSG-Urteile 1998–2008 (nicht frei abrufbar), Betriebsausgabe und Buchung der Abgabe, Haftung der Geschäftsführer, Umwandlung/Insolvenz/Konzern, Plattformen, NFT/Games/Podcasts, KI-Grafik. Details: `regelwerk/Fragenkatalog_Chatbot_Entwurf.xlsx` (Zeilen mit „Quelle fehlt“).

## Nächste Schritte
1. Recherche 2 und 3 sind eingearbeitet. Recherche 3 fand kein BMF-/BFH-Material zur Abgabe, nichts zu Insolvenz/Konzern/Haftung/Podcasts/NFT/KI; Ergebnisse stehen in `quellen/NICHT_GEFUNDEN.md`. Offene Lücken nur mit Quellen aus Stufe 1/2 füllen (`regelwerk/Quellenpolitik_Entwurf.md`).
2. Abnahme der Regeln durch Steuerberater/Fachanwalt (Prüfstatus „Entwurf“ bleibt bis dahin).
3. Prototyp (EU-Hosting, Mistral, RAG nur auf öffentlichen Quellen, Berechnung im Code).

Ehrlich: „Keine Lücke“ kann man nicht garantieren. Machbar ist: Abdeckung messen (Fragenkatalog) und Lücken sichtbar machen.
