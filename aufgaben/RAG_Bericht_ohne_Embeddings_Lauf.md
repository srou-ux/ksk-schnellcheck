# RAG – Bericht Abruf-Güte

Erzeugt von `python -m app.rag.guete` (offline, ohne Embeddings, ohne Sprachmodell).

Testfälle mit Fundstelle: **329** (regelwerk/Testfaelle_BSG_Urteile.xlsx). Die JSON-Testfälle (regelwerk/testfaelle_maschinenlesbar.json) haben kein Feld Fundstelle und fehlen deshalb hier.

| Kennzahl | Wert |
|---|---|
| Gewertet (Jahr im Register, Kernangabe erkennbar) | 299 |
| **Treffer: eine Kernangabe der erwarteten Fundstelle unter den ersten 5** | **256 (85.6 %)** |
| Strenger: die ERSTE Kernangabe unter den ersten 5 | 239 (79.9 %) |
| Fehlschläge | 43 |
| Erwartete Fundstelle unter den GELIEFERTEN Stücken (höchstens 8, nach Mindestabdeckung) | 227 (75.9 %) |
| Geliefert leer („Nicht abgedeckt“), obwohl eine Fundstelle erwartet war | 34 |
| Jahr außerhalb des Registers → leer + „Nicht abgedeckt“ (so gewollt) | 28 |
| Erwartete Fundstelle ohne prüfbare Kernangabe | 2 |

Ziel des Auftrags: ≥ 90 %. Ergebnis: NICHT erreicht.

Abgleich auf Ebene Absatz (Gesetz) bzw. Dokument (KSK/DRV) bzw. Aktenzeichen (Urteil) bzw. Regel-ID – nicht auf Satz, Randnummer oder Seite.

## Nach Gruppe

| Gruppe | Treffer | Fehlschläge | Jahr nicht abgedeckt |
|---|---|---|---|
| Abgrenzung | 6 | 0 | 0 |
| Abwälzung | 1 | 0 | 0 |
| Altjahre | 2 | 1 | 0 |
| Altjahre Veranstalter | 0 | 0 | 3 |
| Ausfall | 2 | 0 | 0 |
| Ausgleichsvereinigung | 2 | 0 | 0 |
| Ausland | 6 | 0 | 0 |
| Band | 2 | 0 | 0 |
| Bemessungsgrundlage | 18 | 7 | 1 |
| Berechnung | 0 | 3 | 0 |
| Betriebsfeier | 3 | 0 | 0 |
| Branchen | 7 | 0 | 0 |
| Design | 5 | 0 | 0 |
| Designbüro | 0 | 0 | 1 |
| Dritte | 4 | 0 | 0 |
| Druck | 1 | 0 | 0 |
| Eigenwerber-Branchen | 2 | 0 | 0 |
| Eigenwerbung | 17 | 0 | 7 |
| Entgelt / Sachleistung | 0 | 1 | 0 |
| Entgelt / Währung | 0 | 1 | 0 |
| Erstattung | 1 | 0 | 0 |
| Fallgruppen | 5 | 1 | 0 |
| Fördermittel/Projekte | 1 | 0 | 0 |
| Galerie | 7 | 0 | 0 |
| Galerien | 3 | 0 | 0 |
| Gemeinnützigkeit | 1 | 0 | 0 |
| Generalklausel | 1 | 1 | 0 |
| Gesellschafter | 3 | 0 | 0 |
| Gestaltung | 0 | 0 | 1 |
| Gewinnzuweisung | 0 | 0 | 1 |
| GmbH-Gesellschafter | 1 | 0 | 0 |
| Grundsatz | 1 | 1 | 0 |
| Honorarformen | 3 | 0 | 0 |
| Influencer | 1 | 0 | 0 |
| Intake | 1 | 0 | 0 |
| KSK-Auslegung Eigenwerbung | 1 | 0 | 0 |
| Katalog | 3 | 5 | 0 |
| Kommission | 1 | 0 | 0 |
| Kommunen | 1 | 0 | 0 |
| Kulturförderung | 2 | 0 | 0 |
| Kunstverein | 2 | 0 | 0 |
| Körperschaft | 0 | 0 | 1 |
| Künstlerbegriff | 1 | 0 | 0 |
| Lizenzen | 3 | 0 | 0 |
| Mehrfachverwertung | 1 | 0 | 0 |
| Meldepflicht | 0 | 1 | 0 |
| Meldeverfahren | 4 | 2 | 0 |
| Meldung | 1 | 0 | 0 |
| Messe | 3 | 0 | 0 |
| Musikverein | 4 | 0 | 0 |
| Musikvereine | 3 | 0 | 0 |
| Nutzung mit Einnahmen | 1 | 0 | 0 |
| Orchester | 4 | 0 | 0 |
| Pauschalen | 4 | 1 | 0 |
| Pflichteingabe | 0 | 1 | 0 |
| Privat | 1 | 0 | 0 |
| Projekte | 4 | 0 | 0 |
| Prüfung | 1 | 0 | 0 |
| Rechnungsanalyse | 4 | 1 | 0 |
| Rechtsbehelfe | 4 | 1 | 0 |
| Rechtsform Künstler | 1 | 0 | 0 |
| Rechtsform des Empfängers | 0 | 1 | 2 |
| Rechtsformen | 0 | 2 | 0 |
| Rechtsprechung | 0 | 0 | 6 |
| Rechtsprechung / Verfahren | 1 | 0 | 0 |
| Rechtsprechung / Zwischenschaltung Ausland | 0 | 0 | 1 |
| Reisekosten | 7 | 0 | 0 |
| Rücknahme von Bescheiden | 1 | 0 | 0 |
| Schwelle | 14 | 1 | 0 |
| Systemverhalten | 1 | 1 | 0 |
| Säumniszuschlag | 3 | 0 | 0 |
| Theater | 2 | 0 | 0 |
| Träger | 1 | 0 | 0 |
| Typische Verwerter | 1 | 1 | 0 |
| Tätigkeitskatalog | 1 | 0 | 1 |
| Umsatzsteuer | 1 | 0 | 0 |
| Unternehmerbegriff | 0 | 1 | 0 |
| Veranstalter | 5 | 0 | 0 |
| Veranstaltungen | 2 | 0 | 0 |
| Veranstaltungen (Fassung A) | 1 | 0 | 0 |
| Verein | 1 | 0 | 0 |
| Verfahren | 21 | 3 | 0 |
| Verlage | 6 | 0 | 0 |
| Vermittlung | 3 | 2 | 1 |
| Vermittlung/Vertretung | 3 | 0 | 0 |
| Vertragsgestaltung | 0 | 1 | 0 |
| Vertreter | 3 | 0 | 0 |
| Vertretung | 4 | 0 | 0 |
| Webdesign | 2 | 0 | 0 |
| Werbeagentur | 4 | 0 | 0 |
| Werbung für Dritte | 5 | 0 | 0 |
| Zahlungen an Künstler | 1 | 0 | 0 |
| Zeitpunkt | 0 | 2 | 0 |
| Zwischenverwerter | 0 | 0 | 2 |
| Öffentliche Stelle | 1 | 0 | 0 |

## Fehlschläge

| ID | Jahr | Erwartet | Erste 5 Treffer |
|---|---|---|---|
| V-05 | 2024 | BSG 28.03.2019, B 3 KS 1/18 R, Rn. 20 | KSK-Info 21 (Stand 10.2025), Abschn. 5, S. 5 · KSK-Info 21, Abschn. 5, S. 4 · KSK-Info 21 (Stand 10.2025), Abschn. 5, S. 4 · KSK-FAQ Unternehmen und Verwerter, Frage 11 · KSK-Info 21 (Stand 10.2025), Abschn. 5, S. 4–5 |
| V-06 | 2024 | BSG 28.03.2019, B 3 KS 1/18 R, Rn. 20, 24; KSVG § 25 Abs. 3 Satz 1 | KSK-Info 20, S. 1 · KSK-Info 20, S. 1 · KSK-Info 20, S. 1 · KSK-Info 15, Abschn. 1, S. 1 · KSK-Info 21 (Stand 10.2025), Abschn. 5, S. 4 |
| S-01 | – | Vergleich E-01/E-02; BSG 01.06.2022, B 3 KS 3/21 R Rn. 15, 18 | KSK-Info 05 (Stand 08.2025), Abschn. 3, S. 1–2 · KSK-Info 01a, Abschn. 2.1, S. 4 · Checkliste Eigenwerber, S. 2; vgl. R-65, R-66 · KSK-Info 05, S. 1 · Checkliste Eigenwerber, S. 2–3 |
| I-26 | 2021 | KSVG § 24 Abs. 3 (Kopie 2022-01-22); Regel R-23 | KSVG § 24 Abs. 1 Satz 2, Abs. 3 (Kopie 2022-01-22); BSG 01.06.2022, B 3 KS 3/21 R, Rn. 14, 15, 18, 21, 24, 25 · BSG 25.11.2010, B 3 KS 1/10 R, Rn. 21 · KSK-Info 05 (Stand 08.2025), Abschn. 3, S. 1–2 · KSK-Info 05 (Archiv 2022-01-20), Abschn. 2, S. 1 · Checkliste Eigenwerber, S. 2; vgl. R-65, R-66 |
| I-27 | – | Regel R-20 | KSK-Info 27, S. 3 · KSK-FAQ Unternehmen und Verwerter, Frage 2 · Checkliste Werbeagenturen, S. 2 · BSG 16.07.2014, B 3 KS 3/13 R, Rn. 14 · KSK-Info 21 (Stand 10.2025), Abschn. 6, S. 5–6 |
| B-02 | 2025 | KSK-Info 10, Abschn. 1, S. 2; Regel R-45 | Ableitung; KSK-FAQ Frage 12 nennt nur die GmbH · KSK-Info 09, Abschn. 2.4, S. 3 · Ableitung; KSK-FAQ Frage 12 nennt nur die GmbH · KSK-Fragebogen Unternehmereigenschaft Projekte, Abschn. 2, S. 1 · KSK-FAQ Unternehmen und Verwerter, Frage 12 |
| P-01 | 2026 | KSAbg2026V § 1; KSVG § 26 Abs. 5; Regel R-89 | KSVEntgV § 1 Nr. 2; KSK-Info 10, Abschn. 2, S. 3 · KSK-Webseite Bemessungsgrundlage · Checkliste Allgemeines, S. 1 · BSG 25.02.2015, B 3 KS 5/13 R, Rn. 18 · KSK-Ausfüllhinweise Anmeldebogen, Ziffer 10, S. 4 |
| P-02 | 2025 | KSAbg2025V § 1; Regel R-89 | KSVEntgV § 1 Nr. 2; KSK-Info 10, Abschn. 2, S. 3 · KSK-Info 10 (Archiv 2025-01-14), Abschn. 1, S. 1 · Checkliste Allgemeines, S. 1 · KSK-Webseite Bemessungsgrundlage · KSK-Ausfüllhinweise Anmeldebogen, Ziffer 10, S. 4 |
| P-03 | 2021 | KSAbg2021V (Archiv 2021-09-26) § 1; Regel R-89 | KSVEntgV § 1 Nr. 2; KSK-Info 10, Abschn. 2, S. 3 · BSG 25.02.2015, B 3 KS 5/13 R, Rn. 18 · Checkliste Allgemeines, S. 1 · BSG 25.11.2010, B 3 KS 1/10 R, Rn. 30 · KSK-Ausfüllhinweise Anmeldebogen, Ziffer 10, S. 4 |
| P-10 | 2020 | SGB IV § 25 Abs. 1, 2; KSVG § 31; Regel R-87 | DRV K5006, Seite 1, 4 · BSG 04.03.2004, B 3 KR 15/03 R, Rn. 9 · KSVG § 36 Abs. 2, 3 · BSG 01.06.2022, B 3 KS 3/21 R, Rn. 4 · KSVG § 32 Abs. 1, 2; KSK-Info 19, Abschn. 1–3, S. 1–2 |
| P-11 | 2025 | KSVG § 36 Abs. 2, 3; § 27 Abs. 1; Regel R-85, R-79 | KSK-Info 04 (Stand 08.2025), Abschn. 2d, S. 2–3 · KSK-Info 17, S. 1 · KSK-FAQ Unternehmen und Verwerter, Frage 4; Handlungshilfen Kulturförderung · DRV K5001, S. 1 · KSVG § 32 Abs. 2; KSK-Info 19, Abschn. 4, S. 2 |
| K-01 | 2025 | KSK-FAQ Frage 1a; Regel R-131 | KSK-Info 01a, Abschn. 1.1 und 1.2, S. 2 · KSK-Info 02, Abschn. 4, S. 2 · Checkliste Veranstalter, S. 2; Galerien, S. 2; Verlage, S. 2; Werbeagenturen, S. 2 · KSK-Info 25, S. 1 · Checkliste Veranstalter, S. 2; Galerien, S. 2; Verlage, S. 2; Werbeagenturen, S. 2 |
| D-02 | 2025 | DRV K5006, S. 3, Hinweis; Regel R-148 | KSK-FAQ Unternehmen und Verwerter, Frage 12 · KSK-Info 02, Abschn. 3, S. 1 · Checkliste Eigenwerber, S. 2; vgl. R-142 · KSK-Info 02, Abschn. 2, S. 1 · Checkliste Eigenwerber, S. 2–3 |
| D-04 | 2025 | DRV K5006, S. 2; Regel R-149 | KSK-Info 04 (Stand 08.2025), Abschn. 2c, S. 2; KSVG § 24 Abs. 2 Satz 3 Nr. 1 · KSK-Fragebogen Unternehmereigenschaft Projekte, Abschn. 5, S. 1 · KSK-Info 12, Abschn. 4, S. 2–3 · KSK-Info 04, Abschn. 2, S. 1 · KSK-Info 01a, Abschn. 1.3–1.5, S. 2–3; Info 12 |
| A-09 | 2019 | KSK-Info 01, Abschn. 4, S. 7; Regel R-164 | KSK-Info 03, Abschn. 3, S. 2 · BSG 28.03.2019, B 3 KS 1/18 R, Rn. 28 · KSK-Info 27, S. 2–3 · KSK-Info 05 (Archiv 2022-01-20), Abschn. 3, S. 1 · KSK-Info 06, Abschn. 1, S. 1–4 (Katalog beispielhaft, nicht abschließend) |
| A-13 | 2026 | KSK-Info 26, S. 3–4; Regeln R-28, R-96, R-166 | KSK-Info 04 (Stand 08.2025), Abschn. 2d, S. 3 · KSK-Info 04, Abschn. 2d, S. 2 · KSK-Info 04 (Stand 08.2025), Abschn. 2d, S. 2–3 · KSK-Info 04, Abschn. 2d, S. 2 · KSK-Info 04 (Stand 08.2025), Abschn. 3, S. 3–5 |
| A-14 | 2026 | KSK-Info 01a, Abschn. 1, S. 2; Regeln R-152, R-24 | KSVG § 24 Abs. 2 Satz 1 Nr. 1, Satz 2 · BSG 25.11.2010, B 3 KS 1/10 R, Rn. 1–2 · Checkliste Eigenwerber, S. 2–3 · KSK-Info 12, Abschn. 3, S. 2 · KSK-FAQ Unternehmen und Verwerter, Frage 7 |
| C-06 | 2026 | Checkliste Allgemeines, S. 1; Regel R-177 | KSK-Info 27, S. 3 · KSK-Info 27, S. 1 · KSK-Info 13, Abschn. II.1a, S. 2 · KSK-Merkblatt Gesellschafter GmbH, S. 1 · Checkliste Eigenwerber, S. 3; Galerien, S. 2; Werbeagenturen, S. 2 |
| C-07 | 2026 | Checkliste Allgemeines, S. 1; Regel R-177 | KSK-Info 06, Abschn. 1, S. 1–4 (Katalog beispielhaft, nicht abschließend) · KSK-Merkblatt Gesellschafter GmbH, S. 1 · Checkliste Eigenwerber, S. 4; Galerien, S. 2; Werbeagenturen, S. 2; vgl. R-27, R-111 · KSK-FAQ Unternehmen und Verwerter, Frage 11 · KSK-Info 27, S. 3 |
| C-38 | 2025 | KSK-Info 24a, S. 1–3; Regel R-203, R-51 | KSK-Info 23 (Stand 01.2026), Abschn. 2, S. 1; KSK-Info 20 (Stand 01.2026), S. 1 · KSK-Info 23, Abschn. 2, S. 1 · KSK-Info 20, S. 1 · KSK-Info 20, S. 1 · KSK-Info 24, Abschn. 1–3, S. 1–2 und Muster-Bestätigung |
| M-03 | 2026 | KSK-Meldebogen rückwirkend, S. 1–2; Regeln R-209, R-87, R-163 | DRV K5006, Seite 2–3 · KSK-Webseite Entgeltmeldung · KSK-FAQ Unternehmen und Verwerter, Frage 5 · KSK-FAQ Unternehmen und Verwerter, Frage 5 · KSK-Info 01a, Abschn. 1.8, S. 3 |
| M-09 | 2026 | KSK-Meldebogen rückwirkend, S. 1; Regeln R-207, R-89 | KSK-Info 23 (Stand 01.2026), Abschn. 2, S. 1; KSK-Info 20 (Stand 01.2026), S. 1 · KSK-Info 20, S. 1 · KSK-Info 12, Abschn. 4, S. 2–3 · KSK-Info 20, S. 1 · KSK-Info 20, S. 2 |
| J-03 | 2026 | KSK-Info 24, S. 1; Regeln R-215, R-202 | EStG § 9 Abs. 4a S. 3 Nr. 1 (Momentaufnahme); KSK-Info 10 · KSK-Info 13, Abschn. III, S. 3 · EStG § 9 Abs. 4a S. 3 Nr. 2, 3 (Momentaufnahme); KSK-Info 10 · KSK-Info 14, Abschn. III, S. 2 · KSK-Info 03, Abschn. 8, S. 4 (Bezug auf BSG 16.04.1998, 3 KR 7/97; Urteil nicht im Repo) |
| L-03 | 2024 | BSG 12.08.2010, B 3 KS 2/09 R, Rn. 15; BSG 16.07.2014, B 3 KS 3/13 R, Rn. 18; R-218; KSK-Info 03 Abschn. 5 (R-93) | KSK-Info 07, Abschn. II.2a, S. 2 · KSK-FAQ Unternehmen und Verwerter, Frage 11 · KSK-FAQ Unternehmen und Verwerter, Frage 13 · BSG 08.10.2014, B 3 KS 1/13 R, Rn. 15 · KSK-FAQ Unternehmen und Verwerter, Frage 5 |
| L-22 | 2025 | KSVG § 25 Abs. 2 S. 1; KSK-Info 10, Abschn. 1; Checkliste Allgemeines (Sachleistungen); R-41; R-174 | KSK-Info 06, Abschn. 1, S. 1–4 (Katalog beispielhaft, nicht abschließend) · BSG 25.02.2015, B 3 KS 5/13 R, Rn. 14 · KSVG § 24 Abs. 1 Satz 1 Nr. 1 · BSG 02.04.2014, B 3 KS 3/12 R, Rn. 28 · KSK-Info 03, Abschn. 3, S. 2 |
| L-23 | 2025 | KSVG § 25 Abs. 1, 2, 4; R-41; R-70 | Checkliste Eigenwerber, S. 2; vgl. R-65, R-66 · BSG 04.03.2004, B 3 KR 15/03 R, Rn. 4 · KSK-Info 03, Abschn. 3, S. 2 · KSK-Info 05, Abschn. 4, S. 3 · KSK-FAQ Unternehmen und Verwerter, Frage 24 |
| L-24 | 2026 | KSVG § 25 Abs. 1 S. 1; KSVG § 24 Abs. 2 S. 2 („in einem Kalenderjahr erteilten Auftrag“); R-41 | KSK-Info 01, Abschn. 4, S. 7 · KSK-FAQ Unternehmen und Verwerter, Frage 11 · KSK-Info 06, Abschn. 1, S. 1–4 (Katalog beispielhaft, nicht abschließend) · KSK-Info 03, Abschn. 7, S. 3 · Checkliste Veranstalter, S. 2; vgl. R-37 |
| N-09 | 2024 | R-44; KSK-Info 10, Abschn. 1, S. 2; KSK-Info 12, S. 4 | KSK-FAQ Unternehmen und Verwerter, Frage 4; Handlungshilfen Kulturförderung · BSG 02.04.2014, B 3 KS 3/12 R, Rn. 7–8 · Checkliste Veranstalter, S. 2; Galerien, S. 2; Verlage, S. 2; Werbeagenturen, S. 2 · KSK-FAQ Unternehmen und Verwerter, Frage 23 · KSK-FAQ Unternehmen und Verwerter, Frage 5 |
| N-10 | 2024 | R-46; KSK-Info 10, Abschn. 1, S. 2 | Checkliste Werbeagenturen, S. 3; vgl. R-46, R-95 · KSK-Merkblatt Gesellschafter GmbH, S. 1 · KSK-Fragebogen Teil I, Ziff. 1–8; Teil II, Ziff. 1–12 (Stand 01.2025); vgl. R-200, R-220 · KSK-Merkblatt Gesellschafter GmbH, S. 1 · KSK-Merkblatt GmbH-Gesellschafter, S. 2–3; vgl. R-95 |
| N-37 | 2024 | R-161; KSK-Info 01, Abschn. 1 und 4, S. 1, 6; KSK-Info 26, S. 2 | KSK-Info 09, Abschn. 3.1–3.3, S. 3–4 · KSK-Info 20, S. 1 · KSK-Info 06, Abschn. 1, S. 1–4 (Katalog beispielhaft, nicht abschließend) · KSK-Info 25, Abschn. 9, S. 2 · KSK-FAQ Unternehmen und Verwerter, Frage 13 |
| N-45 | 2024 | R-02; KSVG § 24 Abs. 1 Satz 1 Nr. 2 | KSK-Info 07 (Stand 09.2025), Abschn. II.1, II.2, S. 1 · KSK-Info 07, Abschn. 1, S. 1 · KSK-FAQ Unternehmen und Verwerter, Frage 15, 16 · KSK-Info 01a, Abschn. 1, S. 2 · KSK-Info 01a, Abschn. 1.13, S. 4 |
| N-47 | 2024 | R-04; KSVG § 24 Abs. 1 Satz 1 Nr. 4 | KSK-Info 09, Abschn. 3.1–3.3, S. 3–4 · KSK-Info 01a, Abschn. 1.7, S. 3 · KSK-FAQ Unternehmen und Verwerter, Frage 15, 16 · KSK-FAQ Unternehmen und Verwerter, Frage 15 · KSK-Info 06, Abschn. 1, S. 1–4 (Katalog beispielhaft, nicht abschließend) |
| N-50 | 2024 | R-07; KSVG § 24 Abs. 1 Satz 1 Nr. 7 | KSK-Info 03 (Stand 08.2025), Abschn. 2, S. 1 · BSG 24.07.2003, B 3 KR 37/02 R, Rn. 26 · Checkliste Eigenwerber, S. 3; Galerien, S. 2; Werbeagenturen, S. 2 · BSG 12.11.2003, B 3 KR 10/03 R, Rn. 22 · Checkliste Werbeagenturen, S. 2 |
| N-51 | 2024 | R-08; KSVG § 24 Abs. 1 Satz 1 Nr. 8 | KSK-FAQ Unternehmen und Verwerter, Frage 4; Handlungshilfen Kulturförderung · KSK-Info 22, Abschn. 1, S. 1 · KSK-Info 01a, Abschn. 1.12, S. 4 · KSK-Info 13, Abschn. I, S. 1 · KSK-Info 20, S. 1 |
| N-52 | 2024 | R-09; KSVG § 24 Abs. 1 Satz 1 Nr. 9 | KSK-Info 06, Abschn. 1, S. 1–4 (Katalog beispielhaft, nicht abschließend) · KSK-Webseite Bemessungsgrundlage · KSK-Info 09, Abschn. 3.1–3.3, S. 3–4 · KSK-Info 23, Abschn. 2, S. 1 · KSK-FAQ Unternehmen und Verwerter, Frage 15, 16 |
| N-53 | 2024 | R-18; KSVG § 25 Abs. 1, 2 | KSK-Info 10, Abschn. 1, S. 2 · KSK-Checkliste für Eigenwerber, Abschn. 2, S. 1 · KSK-Meldebogen 2025, S. 1; Meldebogen rückwirkend, S. 1 · KSK-Checkliste für Verlage, Abschn. 2, S. 1 · KSK-FAQ Unternehmen und Verwerter, Frage 17 |
| N-54 | 2024 | R-19; KSVG § 25 Abs. 3; BSG B 3 KS 1/18 R Rn. 22–28 | KSK-Info 21 (Stand 10.2025), Abschn. 5, S. 4 · KSK-Info 21, Abschn. 1, S. 5 · KSK-Info 01, Abschn. 3, S. 5–6 · KSK-Info 21, Abschn. 5, S. 4 · KSK-Info 21 (Stand 10.2025), Abschn. 5, S. 5 |
| N-61 | 2024 | R-68; KSVG § 25 Abs. 2 Satz 2 Nr. 2 (Vergleich Kopie 2024-05-21 und Momentaufnahme 2026-10-08) | KSK-Info 12, Abschn. 4, S. 2–3 · KSK-Info 10, Abschn. 1, S. 1 · KSK-Info 24, Abschn. 1–3, S. 1–2 und Muster-Bestätigung · KSK-FAQ Unternehmen und Verwerter, Frage 10 · KSK-Info 12, Abschn. 2, S. 2 |
| N-69 | 2025 | R-231; SGG § 84 Abs. 2 S. 3, § 66, § 67 Abs. 1–3; SGB X § 27 Abs. 1–3 (nur sonstige Verwaltungsfristen) | SGG § 78 Abs. 1, § 84 Abs. 1 und 2; KSVG § 39 Abs. 1 · KSK-Info 18, Abschn. 6a, S. 4 · SGG § 87 Abs. 1 und 2 · BSG 12.11.2003, B 3 KR 10/03 R, Rn. 13 · KSK-Info 26, Abschn. „Wie funktioniert das Verfahren“, S. 2–3; KSVG § 31 |
| Q-03 | 2026 | KSVG § 24 Abs. 1 S. 1 Nr. 7; R-07; KSAbg2026V § 1 | KSK-Info 03 (Stand 08.2025), Abschn. 2, S. 1 · KSK-Checkliste für Werbeagenturen, S. 1 · KSK-Info 03, Abschn. 3, S. 2 · KSK-Info 02, Abschn. 3, S. 1 · Checkliste Werbeagenturen, S. 2 |
| Q-04 | 2026 | KSVG § 25 Abs. 1 S. 1; R-41; KSAbg2026V § 1; vgl. L-24 (Gegenindiz „fällig geworden“ offen) | KSK-Info 11 (Stand 09.2025), Abschn. 1–3, S. 1–2 · KSK-FAQ Unternehmen und Verwerter, Frage 11 · KSK-Info 03 (Stand 08.2025), Abschn. 2, S. 1 · KSK-Info 13, Abschn. 1a, S. 2 · KSK-Info 27, S. 3 |
| F-01 | 2025 | KSVG § 24 Abs. 1 S. 1 Nr. 3, Abs. 2 S. 3 Nr. 1; R-07; R-29; R-30; KSAbg2025V § 1 | KSK-Info 13 (Stand 09.2025), Abschn. II.1, S. 1–2 · LSG Berlin-Brandenburg 14.01.2010, L 9 KR 142/03 · KSK-Info 01a, Abschn. 1.6, S. 3 · KSK-FAQ Unternehmen und Verwerter, Frage 23 · KSK-Info 04 (Stand 08.2025), Abschn. 2d, S. 2–3 |
| H-05 | 2026 | KSVG § 25 Abs. 2 S. 1; R-18 | KSK-Info 10, Abschn. 1, S. 2 · KSK-Info 20, S. 1 · KSK-Meldebogen 2025, S. 1; Meldebogen rückwirkend, S. 1 · KSK-Info 10, Abschn. 1, S. 1 · KSK-FAQ Unternehmen und Verwerter, Frage 17 |

## Gegenproben (Fragen ohne Quelle, Soll: leer → „Nicht abgedeckt“)

Richtig leer: **6 von 10** (app/rag/gegenproben.json).

| Frage | Ergebnis | geliefert (erste 3) |
|---|---|---|
| Gibt es ein LSG-Urteil zu Podcast-Produktionen? | leer (richtig) | – |
| podcast produktionen | leer (richtig) | – |
| Wie hoch ist die Hundesteuer in Köln? | **NICHT leer** | BSG 02.04.2014, B 3 KS 3/12 R, Rn. 18 · BSG 07.07.2020, B 12 R 28/18 R, Rn. 15 · BSG 28.03.2019, B 3 KS 1/18 R, Rn. 6 |
| Muss ich für mein Elektroauto Kfz-Steuer zahlen? | **NICHT leer** | BSG 07.07.2020, B 12 R 28/18 R, Rn. 15 · BSG 07.07.2020, B 12 R 28/18 R · SGG § 66 Abs. 1 und 2 |
| Welche Kündigungsfrist gilt für meinen Mietvertrag? | **NICHT leer** | KSVG § 8a Abs. 2 · KSVG § 6 Abs. 2 · SGG § 66 Abs. 1 und 2 |
| Gibt es ein Urteil zu NFT-Kunstwerken auf der Blockchain? | leer (richtig) | – |
| Wie beantrage ich Kurzarbeitergeld für meine Bäckerei? | leer (richtig) | – |
| Darf mein Nachbar seine Hecke drei Meter hoch wachsen lassen? | leer (richtig) | – |
| Gibt es BSG-Rechtsprechung zu KI-generierten Bildern? | **NICHT leer** | BSG 08.10.2014, B 3 KS 1/13 R, Rn. 21 · BSG 25.02.2015, B 3 KS 5/13 R, Rn. 14 · KSK-Info 11, Abschn. 3f, S. 5 |
| Ist Pferdewetten in Bayern umsatzsteuerpflichtig? | leer (richtig) | – |

## Ohne prüfbare Kernangabe

- S-03: –
- S-04: Alle Zeilen mit Urteil
