# RAG – Bericht Abruf-Güte

Erzeugt von `python -m app.rag.guete` MIT Embeddings (RAG_EMBEDDINGS=1, Mistral EU), ohne Sprachmodell.

Testfälle mit Fundstelle: **329** (regelwerk/Testfaelle_BSG_Urteile.xlsx). Die JSON-Testfälle (regelwerk/testfaelle_maschinenlesbar.json) haben kein Feld Fundstelle und fehlen deshalb hier.

| Kennzahl | Wert |
|---|---|
| Gewertet (Jahr im Register, Kernangabe erkennbar) | 299 |
| **Treffer: eine Kernangabe der erwarteten Fundstelle unter den ersten 5** | **239 (79.9 %)** |
| Strenger: die ERSTE Kernangabe unter den ersten 5 | 216 (72.2 %) |
| Fehlschläge | 60 |
| Erwartete Fundstelle unter den GELIEFERTEN Stücken (höchstens 8, nach Mindestabdeckung) | 224 (74.9 %) |
| Geliefert leer („Nicht abgedeckt“), obwohl eine Fundstelle erwartet war | 34 |
| Jahr außerhalb des Registers → leer + „Nicht abgedeckt“ (so gewollt) | 28 |
| Erwartete Fundstelle ohne prüfbare Kernangabe | 2 |

Ziel des Auftrags: ≥ 90 %. Ergebnis: NICHT erreicht.

Abgleich auf Ebene Absatz (Gesetz) bzw. Dokument (KSK/DRV) bzw. Aktenzeichen (Urteil) bzw. Regel-ID – nicht auf Satz, Randnummer oder Seite.

## Nach Gruppe

| Gruppe | Treffer | Fehlschläge | Jahr nicht abgedeckt |
|---|---|---|---|
| Abgrenzung | 5 | 1 | 0 |
| Abwälzung | 1 | 0 | 0 |
| Altjahre | 3 | 0 | 0 |
| Altjahre Veranstalter | 0 | 0 | 3 |
| Ausfall | 2 | 0 | 0 |
| Ausgleichsvereinigung | 2 | 0 | 0 |
| Ausland | 6 | 0 | 0 |
| Band | 2 | 0 | 0 |
| Bemessungsgrundlage | 18 | 7 | 1 |
| Berechnung | 0 | 3 | 0 |
| Betriebsfeier | 3 | 0 | 0 |
| Branchen | 5 | 2 | 0 |
| Design | 5 | 0 | 0 |
| Designbüro | 0 | 0 | 1 |
| Dritte | 4 | 0 | 0 |
| Druck | 1 | 0 | 0 |
| Eigenwerber-Branchen | 2 | 0 | 0 |
| Eigenwerbung | 15 | 2 | 7 |
| Entgelt / Sachleistung | 0 | 1 | 0 |
| Entgelt / Währung | 0 | 1 | 0 |
| Erstattung | 0 | 1 | 0 |
| Fallgruppen | 4 | 2 | 0 |
| Fördermittel/Projekte | 1 | 0 | 0 |
| Galerie | 7 | 0 | 0 |
| Galerien | 3 | 0 | 0 |
| Gemeinnützigkeit | 1 | 0 | 0 |
| Generalklausel | 1 | 1 | 0 |
| Gesellschafter | 3 | 0 | 0 |
| Gestaltung | 0 | 0 | 1 |
| Gewinnzuweisung | 0 | 0 | 1 |
| GmbH-Gesellschafter | 1 | 0 | 0 |
| Grundsatz | 2 | 0 | 0 |
| Honorarformen | 3 | 0 | 0 |
| Influencer | 1 | 0 | 0 |
| Intake | 1 | 0 | 0 |
| KSK-Auslegung Eigenwerbung | 1 | 0 | 0 |
| Katalog | 1 | 7 | 0 |
| Kommission | 1 | 0 | 0 |
| Kommunen | 1 | 0 | 0 |
| Kulturförderung | 2 | 0 | 0 |
| Kunstverein | 2 | 0 | 0 |
| Körperschaft | 0 | 0 | 1 |
| Künstlerbegriff | 1 | 0 | 0 |
| Lizenzen | 3 | 0 | 0 |
| Mehrfachverwertung | 1 | 0 | 0 |
| Meldepflicht | 1 | 0 | 0 |
| Meldeverfahren | 3 | 3 | 0 |
| Meldung | 0 | 1 | 0 |
| Messe | 3 | 0 | 0 |
| Musikverein | 4 | 0 | 0 |
| Musikvereine | 3 | 0 | 0 |
| Nutzung mit Einnahmen | 0 | 1 | 0 |
| Orchester | 4 | 0 | 0 |
| Pauschalen | 4 | 1 | 0 |
| Pflichteingabe | 0 | 1 | 0 |
| Privat | 1 | 0 | 0 |
| Projekte | 4 | 0 | 0 |
| Prüfung | 1 | 0 | 0 |
| Rechnungsanalyse | 2 | 3 | 0 |
| Rechtsbehelfe | 5 | 0 | 0 |
| Rechtsform Künstler | 1 | 0 | 0 |
| Rechtsform des Empfängers | 1 | 0 | 2 |
| Rechtsformen | 0 | 2 | 0 |
| Rechtsprechung | 0 | 0 | 6 |
| Rechtsprechung / Verfahren | 1 | 0 | 0 |
| Rechtsprechung / Zwischenschaltung Ausland | 0 | 0 | 1 |
| Reisekosten | 7 | 0 | 0 |
| Rücknahme von Bescheiden | 1 | 0 | 0 |
| Schwelle | 13 | 2 | 0 |
| Systemverhalten | 1 | 1 | 0 |
| Säumniszuschlag | 3 | 0 | 0 |
| Theater | 2 | 0 | 0 |
| Träger | 1 | 0 | 0 |
| Typische Verwerter | 1 | 1 | 0 |
| Tätigkeitskatalog | 1 | 0 | 1 |
| Umsatzsteuer | 1 | 0 | 0 |
| Unternehmerbegriff | 1 | 0 | 0 |
| Veranstalter | 4 | 1 | 0 |
| Veranstaltungen | 2 | 0 | 0 |
| Veranstaltungen (Fassung A) | 1 | 0 | 0 |
| Verein | 1 | 0 | 0 |
| Verfahren | 19 | 5 | 0 |
| Verlage | 4 | 2 | 0 |
| Vermittlung | 2 | 3 | 1 |
| Vermittlung/Vertretung | 3 | 0 | 0 |
| Vertragsgestaltung | 0 | 1 | 0 |
| Vertreter | 3 | 0 | 0 |
| Vertretung | 4 | 0 | 0 |
| Webdesign | 2 | 0 | 0 |
| Werbeagentur | 3 | 1 | 0 |
| Werbung für Dritte | 4 | 1 | 0 |
| Zahlungen an Künstler | 1 | 0 | 0 |
| Zeitpunkt | 0 | 2 | 0 |
| Zwischenverwerter | 0 | 0 | 2 |
| Öffentliche Stelle | 1 | 0 | 0 |

## Fehlschläge

| ID | Jahr | Erwartet | Erste 5 Treffer |
|---|---|---|---|
| V-02 | 2024 | BSG 28.03.2019, B 3 KS 1/18 R, Rn. 22, 25, 26; KSVG § 25 Abs. 3 Satz 2 Nr. 2 | KSK-Info 27, S. 1 · KSK-Info 04, Abschn. 3b, S. 5 · KSK-Info 15, Abschn. 1, S. 1 · KSK-Info 04 (Stand 08.2025), Abschn. 3, S. 3–5 · KSK-Webseite Bemessungsgrundlage |
| V-05 | 2024 | BSG 28.03.2019, B 3 KS 1/18 R, Rn. 20 | KSK-Info 21, Abschn. 5, S. 4 · KSK-Info 21, Abschn. 1, S. 5 · Checkliste Eigenwerber, S. 3; Galerien, S. 2; Werbeagenturen, S. 2 · KSK-Info 21, Abschn. 2, S. 5 · KSK-Info 21, Abschn. 6, S. 5 |
| V-06 | 2024 | BSG 28.03.2019, B 3 KS 1/18 R, Rn. 20, 24; KSVG § 25 Abs. 3 Satz 1 | KSK-Info 20, S. 1 · KSK-Info 20, S. 1 · KSK-Info 20, S. 1 · KSK-Info 20, S. 1 · KSK-Info 11, Abschn. 3d, S. 5 |
| S-01 | – | Vergleich E-01/E-02; BSG 01.06.2022, B 3 KS 3/21 R Rn. 15, 18 | Checkliste Eigenwerber, S. 2–3 · KSK-Info 05, Abschn. 2, S. 1 · KSK-Info 01a, Abschn. 2.1, S. 4 · Checkliste Eigenwerber, S. 2; vgl. R-65, R-66 · KSK-Info 05 (Archiv 2023-04-03), Abschn. 2, S. 1 |
| I-01 | 2026 | KSVG § 24 Abs. 2 Satz 2 (aktuelle Fassung); Regel R-24 | KSK-Info 01a, Abschn. 2.1, S. 4 · KSK-Ausfüllhinweise Anmeldebogen, S. 1 · KSK-FAQ Unternehmen und Verwerter, Frage 1 · KSK-Info 11, Abschn. 3g, S. 5 · KSK-Info 12, Abschn. 3, S. 2 |
| I-08 | 2025 | KSK-Info 05 (Stand 08.2025), Abschn. 6, S. 4; Regel R-26 | KSK-Ausfüllhinweise Anmeldebogen, S. 1 · KSK-Info 12, Abschn. 3, S. 2 · KSK-Info 25, Abschn. 9, S. 2 · KSK-Info 03, Abschn. 3, S. 2 · KSK-Info 11, Abschn. 3g, S. 5 |
| I-15 | 2025 | KSVG § 24 Abs. 2 Satz 3 Nr. 1; Regel R-21 | KSK-Info 12, Abschn. 4, S. 2–3 · KSK-Info 01 (Archiv 2025-03-20), Abschn. 9, S. 1 · KSK-Info 04, Abschn. 2, S. 1 · wie R-14, R-15 · KSK-Fragebogen Unternehmereigenschaft Projekte, Abschn. 12, S. 3 |
| I-27 | – | Regel R-20 | BSG 12.11.2003, B 3 KR 10/03 R, Rn. 5 · BSG 04.03.2004, B 3 KR 15/03 R, Rn. 10 · BSG 12.11.2003, B 3 KR 10/03 R, Rn. 25–26 · BSG 12.11.2003, B 3 KR 10/03 R, Rn. 23–24 · BSG 08.10.2014, B 3 KS 1/13 R, Rn. 25–26 |
| B-01 | 2025 | KSK-Info 10, Abschn. 1, S. 2; Regel R-43 | KSK-Info 20, S. 1 · KSK-FAQ Unternehmen und Verwerter, Frage 9 · KSK-Webseite Bemessungsgrundlage · BSG 04.03.2004, B 3 KR 15/03 R, Rn. 10 · KSK-Info 01, Abschn. 3, S. 3 |
| B-05 | 2025 | KSK-Info 10, Abschn. 1, S. 2; Regel R-50 | KSK-Info 24, Abschn. 1–3, S. 1–2 und Muster-Bestätigung · KSK-Info 12, Abschn. 4, S. 2 · KSK-Info 24, Abschn. 1, S. 1 · KSK-Info 12 (Archiv 2025-11-14), Abschn. 4, S. 2 · KSK-FAQ Unternehmen und Verwerter, Frage 10 |
| P-01 | 2026 | KSAbg2026V § 1; KSVG § 26 Abs. 5; Regel R-89 | KSK-Info 24a, S. 1–3 · KSK-Webseite Bemessungsgrundlage · KSK-Info 01 (Archiv 2022-01-20 und 2025-03-20), Abschn. 3; Info 10 (Archiv); Info 12 (Archiv 2022-01-20); Info 24, 24a (Stand 01.2026) · KSK-Info 10, Abschn. 1, S. 2; KSK-Info 12, S. 4 · KSK-Info 10, Abschn. 1, S. 3 |
| P-02 | 2025 | KSAbg2025V § 1; Regel R-89 | KSK-Info 01 (Archiv 2022-01-20 und 2025-03-20), Abschn. 3; Info 10 (Archiv); Info 12 (Archiv 2022-01-20); Info 24, 24a (Stand 01.2026) · KSK-Webseite Bemessungsgrundlage · KSK-Info 24a, S. 1–3 · KSVG § 54: 'Abweichend von § 24 Absatz 2 Satz 2 beträgt die Entgeltsumme 700 Euro im Kalenderjahr 2025' · KSK-Info 10, Abschn. 1, S. 2; KSK-Info 12, S. 4 |
| P-03 | 2021 | KSAbg2021V (Archiv 2021-09-26) § 1; Regel R-89 | KSK-Info 01 (Archiv 2022-01-20 und 2025-03-20), Abschn. 3; Info 10 (Archiv); Info 12 (Archiv 2022-01-20); Info 24, 24a (Stand 01.2026) · KSK-Info 10, Abschn. 1, S. 2; KSK-Info 12, S. 4 · KSK-Info 24a, S. 1–3 · KSVG § 27 Abs. 2–4 · KSVG § 27 Abs. 3; KSK-Info 01 Abschn. 4 |
| P-10 | 2020 | SGB IV § 25 Abs. 1, 2; KSVG § 31; Regel R-87 | KSK-Meldebogen 2025, S. 1; Meldebogen rückwirkend, S. 1 · KSVG § 27 Abs. 1 · DRV K5006, Seite 1, 4 · BSG 04.03.2004, B 3 KR 15/03 R, Rn. 9 · EStG § 111 Abs. 5 |
| P-11 | 2025 | KSVG § 36 Abs. 2, 3; § 27 Abs. 1; Regel R-85, R-79 | KSK-Info 18, Abschn. 2a, S. 2 · DRV K5001, S. 1 · KSK-Info 26, S. 3; KSK-Info 01, Abschn. 3, S. 3–4 · KSK-Ausfüllhinweise Anmeldebogen, S. 1 · KSK-Info 28, S. 1 |
| W-02 | 2025 | KSK-Info 03, Abschn. 2, S. 1; Regel R-91 | KSK-FAQ Unternehmen und Verwerter, Frage 19 · KSK-Info 10 (Archiv 2025-01-14), Abschn. 1, S. 1 · KSK-Ausfüllhinweise Anmeldebogen, S. 1 · KSK-Info 28, S. 1 · KSK-Info 01, Abschn. 3, S. 3 |
| D-01 | 2025 | DRV K5006, S. 2–3; Regel R-146 | KSK-Info 01 (Archiv 2025-03-20), Abschn. 9, S. 1 · KSK-FAQ Unternehmen und Verwerter, Frage 1 · KSK-Info 01, Abschn. 2, S. 2 · KSK-Info 28, S. 1 · KSK-Info 05, Abschn. 2, S. 1 |
| D-02 | 2025 | DRV K5006, S. 3, Hinweis; Regel R-148 | KSK-Info 01a, Abschn. 2.1, S. 4 · KSK-Info 12, Abschn. 3, S. 2 · KSK-Ausfüllhinweise Anmeldebogen, S. 1 · KSK-Info 12 (Archiv 2025-11-14), Abschn. 3, S. 2 · KSK-FAQ Unternehmen und Verwerter, Frage 1 |
| D-04 | 2025 | DRV K5006, S. 2; Regel R-149 | KSK-Info 04 (Stand 08.2025), Abschn. 2c, S. 2; KSVG § 24 Abs. 2 Satz 3 Nr. 1 · KSK-Info 04, Abschn. 2, S. 1 · wie R-14, R-15 · KSK-Info 12, Abschn. 4, S. 2–3 · KSVG § 24 Abs. 2 S. 3 Nr. 1 |
| A-01 | 2026 | KSK-Info 01a, Abschn. 1.1, S. 2; Regeln R-01, R-131, R-153, R-154 | KSK-Info 06, Abschn. 1, S. 1–4 (Katalog beispielhaft, nicht abschließend) · KSK-Info 26, S. 3; KSK-Info 01, Abschn. 3, S. 3–4 · KSK-Info 12, Abschn. 4, S. 2 · KSK-Info 04 (Stand 08.2025), Abschn. 3a, S. 5 · KSK-Info 04, Abschn. 2, S. 1 |
| A-07 | 2026 | KSK-Info 01a, Abschn. 1.6, S. 3; Regel R-160 | KSK-Info 27, S. 1 · KSK-Info 27, S. 2 · KSK-Info 04 (Stand 08.2025), Abschn. 2a, 2b, S. 1–2; BSG B 3 KS 1/18 R Rn. 18 · KSK-Info 13, Abschn. II.1a, S. 2 · KSK-Info 04 (Stand 08.2025), Abschn. 3, S. 3–5 |
| A-12 | 2024 | KSVG § 33 Abs. 1; Regeln R-45, R-171 | Checkliste Allgemeines, S. 1; vgl. R-45, R-138 · KSK-FAQ Unternehmen und Verwerter, Frage 12 · KSK-FAQ Unternehmen und Verwerter, Frage 12 · Ableitung; KSK-FAQ Frage 12 nennt nur die GmbH · Ableitung; KSK-FAQ Frage 12 nennt nur die GmbH |
| A-13 | 2026 | KSK-Info 26, S. 3–4; Regeln R-28, R-96, R-166 | KSK-Info 04, Abschn. 2d, S. 2 · KSK-FAQ Unternehmen und Verwerter, Frage 23 · KSK-FAQ Unternehmen und Verwerter, Frage 23 · KSK-Info 04, Abschn. 2d, S. 2 · KSK-Info 13, Abschn. 1a, S. 2 |
| C-06 | 2026 | Checkliste Allgemeines, S. 1; Regel R-177 | KSK-Info 21, Abschn. 4, S. 2 · KSK-Info 12, Abschn. 3, S. 2 · KSK-Info 01a, Abschn. 2.2, S. 4 · KSK-Info 10, Abschn. 1, S. 1 · DRV K5000, Abschn. 5.2, S. 3 |
| C-07 | 2026 | Checkliste Allgemeines, S. 1; Regel R-177 | KSVG § 24 Abs. 2 · KSK-Info 01, Abschn. 2, S. 2 · KSK-Info 21, Abschn. 4, S. 2 · KSK-Ausfüllhinweise Anmeldebogen, S. 1 · BSG 01.06.2022, B 3 KS 3/21 R, Rn. 17 |
| C-17 | 2026 | Checkliste Eigenwerber, S. 3; Regeln R-187, R-24 | KSK-Info 04, Abschn. 4a, S. 6 · KSK-Info 16, Abschn. 2, S. 1 · KSK-FAQ Unternehmen und Verwerter, Frage 19 · KSK-Info 15, Abschn. 1, S. 1 · KSK-FAQ Unternehmen und Verwerter, Frage 19 |
| C-23 | 2026 | Checkliste Verlage, S. 2; Regel R-191 | DRV K5000, Abschn. 2.1, S. 1 · BSG 28.03.2019, B 3 KS 1/18 R, Rn. 6 · KSK-Info 21, Abschn. 4, S. 2 · KSK-Info 09, Abschn. 2.2, S. 1 · BSG 28.03.2019, B 3 KS 1/18 R, Rn. 4 |
| C-27 | 2026 | Checkliste Verlage, S. 2; Regel R-193 | BSG 04.06.2019, B 3 KS 2/18 R, Rn. 27 · BSG 04.06.2019, B 3 KS 2/18 R, Rn. 29 · BSG 04.06.2019, B 3 KS 2/18 R, Rn. 7 · BSG 28.03.2019, B 3 KS 1/18 R, Rn. 6 · BSG 04.06.2019, B 3 KS 2/18 R, Leitsatz 2, 3, Rn. 22, 24, 25, 28, 29 |
| C-31 | 2026 | Checkliste Werbeagenturen, S. 2; Regel R-197 | BSG 08.10.2014, B 3 KS 1/13 R, Rn. 23 · BSG 12.11.2003, B 3 KR 10/03 R, Rn. 5 · BSG 08.10.2014, B 3 KS 1/13 R, Rn. 22 · BSG 12.11.2003, B 3 KR 10/03 R, Rn. 27–28 · BSG 04.03.2004, B 3 KR 15/03 R, Rn. 10 |
| C-41 | 2026 | KSVGBeitrÜV § 3 Abs. 3, § 9; Regel R-204 | KSK-Info 18, Abschn. 2b, S. 2 · KSVGBeitrÜV § 9 Abs. 1 · KSK-Info 18 (Stand 09.2025), Einführung, Abschn. 1, 2b, 4a · KSK-Info 18, Abschn. 7, S. 8 · KSK-Info 18, Abschn. 1, S. 1 |
| M-01 | 2025 | KSK-Meldebogen 2025, S. 1; Regeln R-207, R-43, R-89 | KSK-Info 20, S. 1 · KSK-Info 01, Abschn. 3, S. 3 · DRV K5006, S. 1 · KSK-Info 28, S. 1 · KSK-Info 12, Abschn. 4, S. 2 |
| M-03 | 2026 | KSK-Meldebogen rückwirkend, S. 1–2; Regeln R-209, R-87, R-163 | KSK-Info 07, Abschn. 2b, S. 3 · KSVG § 27 Abs. 1 · KSK-Info 20, S. 1 · KSK-Anmelde- und Erhebungsbogen, Abschn. 7, S. 2 · KSK-Info 01a, Abschn. 1, S. 2 |
| M-09 | 2026 | KSK-Meldebogen rückwirkend, S. 1; Regeln R-207, R-89 | KSK-Info 20, S. 1 · KSK-Info 20, S. 1 · KSK-Info 20, S. 1 · KSK-Info 20, S. 1 · KSK-Info 26, S. 3; KSK-Info 01, Abschn. 3, S. 3–4 |
| M-10 | 2026 | KSVG § 29; Regel R-213 | KSK-Info 28, S. 1 · KSK-Info 03, Abschn. 8, S. 4 · KSK-Info 18, Abschn. 2a, S. 2 · KSK-Ausfüllhinweise Anmeldebogen, S. 1 · KSK-Ausfüllhinweise Anmeldebogen, S. 1 |
| J-03 | 2026 | KSK-Info 24, S. 1; Regeln R-215, R-202 | KSVG § 24 Abs. 2 Satz 2 (aktuell) · KSK-Info 01, Abschn. 4, S. 7 · BGBl. 2022 I S. 2759 Art. 34 Abs. 2 · BGBl. 2026 I Nr. 228 Art. 1 § 130e · BGBl. 2026 I Nr. 228 Art. 1 § 43a Abs. 4 |
| L-22 | 2025 | KSVG § 25 Abs. 2 S. 1; KSK-Info 10, Abschn. 1; Checkliste Allgemeines (Sachleistungen); R-41; R-174 | BSG 16.04.1998, B 3 KR 7/97 R, Rn. 15–16 · DRV K5000, Abschn. 2.1, S. 1 · BSG 02.04.2014, B 3 KS 3/12 R, Rn. 36 · KSK-Info 26, S. 3; KSK-Info 01, Abschn. 3, S. 3–4 · KSVG § 3 Abs. 1 |
| L-23 | 2025 | KSVG § 25 Abs. 1, 2, 4; R-41; R-70 | BSG 12.11.2003, B 3 KR 10/03 R, Rn. 27–28 · BSG 12.11.2003, B 3 KR 10/03 R, Rn. 33–34 · KSK-Info 03, Abschn. 7, S. 3 · BSG 12.11.2003, B 3 KR 10/03 R, Rn. 30–31 · BSG 04.03.2004, B 3 KR 15/03 R, Rn. 17 |
| L-24 | 2026 | KSVG § 25 Abs. 1 S. 1; KSVG § 24 Abs. 2 S. 2 („in einem Kalenderjahr erteilten Auftrag“); R-41 | KSVG § 27 Abs. 2–4 · KSK-Info 01, Abschn. 4, S. 7 · KSK-Info 01, Abschn. 4, S. 6 · KSVG § 17a · KSK-Ausfüllhinweise Anmeldebogen, S. 1 |
| N-03 | 2020 | R-12; KSVG § 24 Abs. 2 Satz 1, Abs. 3 (Kopie 2022-01-22); BSG B 3 KS 3/21 R Rn. 16, 17 | BSG 12.11.2003, B 3 KR 10/03 R, Rn. 27–28 · Checkliste Eigenwerber, S. 2; vgl. R-65, R-66 · BSG 04.03.2004, B 3 KR 15/03 R, Rn. 17 · KSK-Info 03, Abschn. 3, S. 2 · BSG 25.11.2010, B 3 KS 1/10 R, Rn. 23 |
| N-10 | 2024 | R-46; KSK-Info 10, Abschn. 1, S. 2 | Checkliste Werbeagenturen, S. 3; vgl. R-46, R-95 · KSK-Info 03, Abschn. 8, S. 4 · KSK-Merkblatt Gesellschafter GmbH, S. 1 · BSG 02.04.2014, B 3 KS 3/12 R, Rn. 27 · KSK-Merkblatt GmbH-Gesellschafter, S. 1–3 |
| N-14 | 2024 | R-59; KSK-Info 12, S. 3 | KSK-Info 03, Abschn. 5, S. 2–3 · KSK-Info 01 (Archiv 2024-03-05), Abschn. 3, S. 2 · KSK-Info 25 (Stand 11.2025), S. 2, Hinweis; KSVG § 24 Abs. 2 Satz 2, § 54 · KSK-Info 01, Abschn. 3, S. 3 · KSK-Webseite Bemessungsgrundlage |
| N-33 | 2024 | R-140; KSK-FAQ Unternehmen und Verwerter, Frage 15, 16 | KSK-Info 01a, Abschn. 2.1, S. 4 · BSG 24.07.2003, B 3 KR 37/02 R, Rn. 24 · BSG 07.05.2020, B 3 KS 3/18 R, Rn. 19 · BSG 24.07.2003, B 3 KR 37/02 R, Rn. 26 · SGB IV § 12 Abs. 1 |
| N-45 | 2024 | R-02; KSVG § 24 Abs. 1 Satz 1 Nr. 2 | KSK-Info 07, Abschn. 1, S. 1 · KSK-Info 09, Abschn. 2.2, S. 1 · KSK-Info 04, Abschn. 2, S. 1 · KSK-Info 07, Abschn. 2, S. 1 · KSK-Info 07, Abschn. II.2a, S. 2 |
| N-47 | 2024 | R-04; KSVG § 24 Abs. 1 Satz 1 Nr. 4 | KSK-Info 01a, Abschn. 1.7, S. 3 · KSK-Info 06, Abschn. 1, S. 1–4 (Katalog beispielhaft, nicht abschließend) · BSG 04.03.2004, B 3 KR 12/03 R, Rn. 5 · KSK-Info 09, Abschn. 3.1–3.3, S. 3–4 · KSK-Info 15, Abschn. 1, S. 1 |
| N-48 | 2024 | R-05; KSVG § 24 Abs. 1 Satz 1 Nr. 5 | KSK-Info 01a, Abschn. 1.8, S. 3 · KSK-Info 11, Abschn. 3c, S. 4 · KSK-FAQ Unternehmen und Verwerter, Frage 12 · DRV K5001, S. 1 · KSK-Info 25, S. 1 |
| N-49 | 2024 | R-06; KSVG § 24 Abs. 1 Satz 1 Nr. 6; BSG B 3 KS 1/18 R Rn. 20 | KSK-Info 20, S. 1 · KSK-Info 21, Abschn. 6, S. 5 · KSK-Info 21, Abschn. 2, S. 5 · KSK-Info 21, Abschn. 5, S. 4 · KSK-Info 21, Abschn. 1, S. 5 |
| N-50 | 2024 | R-07; KSVG § 24 Abs. 1 Satz 1 Nr. 7 | KSK-Info 03, Abschn. 6, S. 3 · BSG 25.02.2015, B 3 KS 5/13 R, Rn. 14 · KSK-Checkliste für Werbeagenturen, S. 1 · BSG 24.07.2003, B 3 KR 37/02 R, Rn. 26 · KSK-Info 03, Abschn. 3, S. 2 |
| N-51 | 2024 | R-08; KSVG § 24 Abs. 1 Satz 1 Nr. 8 | KSK-Info 01a, Abschn. 1.12, S. 4 · KSK-Info 21, Abschn. 4, S. 2 · KSK-Info 20, S. 1 · KSK-Info 13, Abschn. 1c, S. 2 · KSK-Info 11, Abschn. 3f, S. 5 |
| N-52 | 2024 | R-09; KSVG § 24 Abs. 1 Satz 1 Nr. 9 | KSK-Info 11, Abschn. 3b, S. 2 · KSK-Info 01a, Abschn. 1.13, S. 4 · KSK-Info 23, Abschn. 2, S. 1 · KSK-Info 24, Abschn. 1, S. 1 · KSK-Webseite Bemessungsgrundlage |
| N-53 | 2024 | R-18; KSVG § 25 Abs. 1, 2 | KSK-Info 20, S. 1 · KSK-Info 01, Abschn. 3, S. 3 · KSK-Webseite Bemessungsgrundlage · KSK-FAQ Unternehmen und Verwerter, Frage 9 · KSK-Info 12, Abschn. 4, S. 2 |
| N-54 | 2024 | R-19; KSVG § 25 Abs. 3; BSG B 3 KS 1/18 R Rn. 22–28 | KSK-Info 21, Abschn. 5, S. 4 · KSK-Info 21, Abschn. 1, S. 5 · KSK-Info 21 (Stand 10.2025), Abschn. 5, S. 4 · KSK-Info 21, Abschn. 2, S. 5 · KSK-Info 21, Abschn. 6, S. 5 |
| N-61 | 2024 | R-68; KSVG § 25 Abs. 2 Satz 2 Nr. 2 (Vergleich Kopie 2024-05-21 und Momentaufnahme 2026-10-08) | KSK-Info 24, Abschn. 1–3, S. 1–2 und Muster-Bestätigung · KSK-Info 12, Abschn. 4, S. 2 · KSK-Info 24, Abschn. 1, S. 1 · KSK-FAQ Unternehmen und Verwerter, Frage 10 · KSK-Info 01 (Archiv 2022-01-20 und 2025-03-20), Abschn. 3; Info 10 (Archiv); Info 12 (Archiv 2022-01-20); Info 24, 24a (Stand 01.2026) |
| N-64 | 2024 | R-84; KSVG § 29 | KSK-Info 17, Abschn. 4, S. 2 · KSK-Info 18, Abschn. 2a, S. 2 · KSK-Info 18, Abschn. 5, S. 4 · KSK-Info 18, Abschn. 4b, S. 3 · KSK-Info 18, Abschn. 4e, S. 4 |
| Q-03 | 2026 | KSVG § 24 Abs. 1 S. 1 Nr. 7; R-07; KSAbg2026V § 1 | KSK-Info 25, Abschn. 9, S. 2 · KSK-Webseite Bemessungsgrundlage · KSK-Info 12, Abschn. 3, S. 2 · DRV K5006, S. 1 · Checkliste Werbeagenturen, S. 3; vgl. R-46, R-95 |
| Q-04 | 2026 | KSVG § 25 Abs. 1 S. 1; R-41; KSAbg2026V § 1; vgl. L-24 (Gegenindiz „fällig geworden“ offen) | KSVG § 27 Abs. 2–4 · KSK-Info 01, Abschn. 4, S. 6 · Checkliste Veranstalter, S. 2; vgl. R-37 · Checkliste Werbeagenturen, S. 3; vgl. R-46, R-95 · KSK-FAQ Unternehmen und Verwerter, Frage 26 |
| F-01 | 2025 | KSVG § 24 Abs. 1 S. 1 Nr. 3, Abs. 2 S. 3 Nr. 1; R-07; R-29; R-30; KSAbg2025V § 1 | KSK-Info 01a, Abschn. 1.6, S. 3 · KSK-Info 13, Abschn. 1a, S. 2 · KSK-FAQ Unternehmen und Verwerter, Frage 5 · KSK-Info 04 (Stand 08.2025), Abschn. 2d, S. 2–3 · KSK-Info 27, S. 2 |
| F-05 | 2025 | KSVG § 24 Abs. 2 S. 1 Nr. 2; R-30; R-132 | KSK-FAQ Unternehmen und Verwerter, Frage 5 · KSK-Info 12, Abschn. 4, S. 2–3 · KSK-Info 12, Abschn. 4, S. 2 · KSK-Info 12 (Archiv 2025-11-14), Abschn. 4, S. 2 · KSK-Info 04, Abschn. 2, S. 1 |
| H-02 | 2026 | KSVG § 25 Abs. 1–3; R-138; R-33; R-36; R-47; R-78; R-176 | Checkliste Veranstalter, S. 2; vgl. R-37 · KSK-Info 27, S. 1 · KSK-Info 01, Abschn. 3, S. 3 · KSK-Info 04, Abschn. 3, S. 3 · KSK-Info 26, S. 1 |
| H-04 | 2026 | KSVEntgV § 1 Nr. 1; R-47; R-176; R-33; R-78 | KSK-Info 27, S. 1 · KSK-Info 26, S. 1 · Checkliste Veranstalter, S. 2; vgl. R-37 · BSG 16.07.2014, B 3 KS 3/13 R, Rn. 24 · KSK-Info 01, Abschn. 3, S. 3 |
| H-05 | 2026 | KSVG § 25 Abs. 2 S. 1; R-18 | KSK-Info 20, S. 1 · KSK-Webseite Bemessungsgrundlage · KSK-Info 01, Abschn. 3, S. 3 · EStG § 5 Abs. 5 · HGB § 87b Abs. 2 |

## Gegenproben (Fragen ohne Quelle, Soll: leer → „Nicht abgedeckt“)

Richtig leer: **6 von 10** (app/rag/gegenproben.json).

| Frage | Ergebnis | geliefert (erste 3) |
|---|---|---|
| Gibt es ein LSG-Urteil zu Podcast-Produktionen? | leer (richtig) | – |
| podcast produktionen | leer (richtig) | – |
| Wie hoch ist die Hundesteuer in Köln? | **NICHT leer** | BSG 02.04.2014, B 3 KS 3/12 R, Rn. 18 · BSG 07.07.2020, B 12 R 28/18 R, Rn. 15 · BSG 28.03.2019, B 3 KS 1/18 R, Rn. 6 |
| Muss ich für mein Elektroauto Kfz-Steuer zahlen? | **NICHT leer** | EStG § 36a Abs. 4 · EStG § 6 Abs. 1 · BSG 07.07.2020, B 12 R 28/18 R, Rn. 15 |
| Welche Kündigungsfrist gilt für meinen Mietvertrag? | **NICHT leer** | HGB § 556 · HGB § 89 Abs. 1 · HGB § 490 Abs. 2 |
| Gibt es ein Urteil zu NFT-Kunstwerken auf der Blockchain? | leer (richtig) | – |
| Wie beantrage ich Kurzarbeitergeld für meine Bäckerei? | leer (richtig) | – |
| Darf mein Nachbar seine Hecke drei Meter hoch wachsen lassen? | leer (richtig) | – |
| Gibt es BSG-Rechtsprechung zu KI-generierten Bildern? | **NICHT leer** | BSG 08.10.2014, B 3 KS 1/13 R, Rn. 21 · BSG 25.02.2015, B 3 KS 5/13 R, Rn. 14 · KSK-Info 11, Abschn. 3f, S. 5 |
| Ist Pferdewetten in Bayern umsatzsteuerpflichtig? | leer (richtig) | – |

## Ohne prüfbare Kernangabe

- S-03: –
- S-04: Alle Zeilen mit Urteil
