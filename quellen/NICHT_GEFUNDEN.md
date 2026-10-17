# Nicht gefunden

Dokumentation gemäß `aufgaben/PROMPT_ClaudeCode_Recherche_1.md`. Für jeden Punkt: was gesucht wurde, Datum des Versuchs, welche URLs probiert wurden, Ergebnis.

---

## 1. BSG-Urteil zu Webdesigner (2005) — Aktenzeichen B 3 KR 37/04 R

**Datum des Versuchs:** 08.10.2026

**Gesucht:** Volltext des Urteils vom 07.07.2005, Aktenzeichen B 3 KR 37/04 R (Leitentscheidung: Webdesigner als Künstler im Sinne des KSVG).

**Versuchte Quellen:**
- `bsg.bund.de`: Getestete URL `https://www.bsg.bund.de/SharedDocs/Entscheidungen/DE/2005/2005_07_07_B_03_KR_37_04_R.pdf?__blob=publicationFile` → **HTTP 404**. Das strukturierte Online-Archiv von bsg.bund.de deckt nachweislich nur Entscheidungen ab ca. 2018 ff. ab.
- `rechtsprechung-im-internet.de`: Über die Entscheidungssuche (Suchmaske, session-basiert) nach „B 3 KR 37/04 R" und „B 3 KR 37/04" gesucht → **0 Treffer**. Zur Kontrolle wurde ein noch älteres, ähnliches Aktenzeichen (B 3 KR 8/03 R, aus 2003, wird im Urteil B 3 KS 1/10 R als Referenz zitiert) ebenfalls gesucht → **ebenfalls 0 Treffer**. Das bestätigt: Diese Datenbank deckt Entscheidungen erst ab ca. 2010 ab; 2003–2005 liegt davor.
- `openjur.de`: Automatisierter Zugriff nicht möglich — die Seite stellt vor jedem Abruf ein Bild-Rotations-Captcha ("We have to check whether you are human"), das ohne Browser/Mensch nicht lösbar ist.
- `sozialgerichtsbarkeit.de`: Die Seite ist eine reine JavaScript-Single-Page-Application ohne serverseitig gerenderten Inhalt (schon in früheren Sitzungen festgestellt) — ohne Browser nicht abrufbar.
- `dejure.org`: Ist selbst kein Volltext-Hoster, sondern nur ein Verweis-/Zitierdienst auf andere Quellen; liefert daher keinen eigenen Volltext.

**Ergebnis: nicht gefunden.** Keine der im Auftrag erlaubten freien Quellen liefert den Volltext dieses Urteils.

---

## 2. BGBl. 2022 I S. 2759 (8. SGB IV-Änderungsgesetz) als natives PDF

**Datum des Versuchs:** 08.10.2026

**Gesucht:** Natives PDF der amtlichen Verkündung von recht.bund.de oder bgbl.de.

**Versuchte URLs:**
- `https://www.recht.bund.de/bgbl/1/2022/56/VO.html` → **HTTP 404**
- `https://www.recht.bund.de/bgbl/1/2022/56/regelungstext.pdf?__blob=publicationFile&v=1` → **HTTP 404**
- recht.bund.de übernahm die Verkündung erst ab 01.01.2023; dieses Gesetz (verkündet 28.12.2022) liegt davor.
- `bgbl.de` (altes Archiv): Der Java-basierte „Xaver"-Viewer liefert bei direktem URL-Aufruf kein natives PDF, sondern nur HTML-Viewer-Seiten.

**Ergebnis: Als natives PDF nicht gefunden.** Hinweis: Ein vollständiger **Textauszug** des amtlichen Inhalts (aus einer Wayback-Machine-Archivkopie einer bgbl.de-Viewerseite mit eingebettetem Volltext) liegt bereits als `quellen/ergaenzend/BGBl_2022_I_2759_8SGB-IV-AendG_Archivtext.txt` vor (aus einer früheren Sitzung) — das ist jedoch kein natives PDF, sondern ein HTML-Textauszug.

---

## 3. KSVG, Stand exakt zum 31.12.2025 / 01.01.2026

**Datum des Versuchs:** 08.10.2026

**Gesucht:** Eine Fassung des KSVG, die exakt den Rechtsstand zum Jahreswechsel 2025/2026 abbildet (ohne spätere Änderungen).

**Geprüft:** Die aktuelle Live-Fassung von `gesetze-im-internet.de/ksvg/KSVG.pdf` (heute abgerufen als `quellen/ergaenzend/KSVG_Momentaufnahme_2026-10-08.pdf`) weist als „Stand:" „Zuletzt geändert durch Art. 7c G v. 24.7.2026 I Nr. 228" aus — das ist **nach** dem 01.01.2026 und enthält somit mindestens eine spätere Änderung.

**Versuchte URL (Wayback CDX-API):** `http://web.archive.org/cdx/search/cdx?url=gesetze-im-internet.de/ksvg/KSVG.pdf&output=json` → Letzte je erfasste Archivkopie: 21.05.2024. Keine Erfassung in 2025 oder 2026.

**Ergebnis: nicht gefunden.** Es existiert keine Quelle, die den KSVG-Stand exakt und ausschließlich zum 31.12.2025/01.01.2026 abbildet. Die abgelegte Datei `KSVG_Momentaufnahme_2026-10-08.pdf` ist eine Momentaufnahme vom heutigen Abrufdatum und enthält nachweislich mindestens eine Änderung nach dem gesuchten Stichtag (siehe Hinweis in `index.csv`).

---

# Recherche 2 (08.10.2026) — gemäß `aufgaben/PROMPT_ClaudeCode_Recherche_2.md`

## Punkt A.1 — BSG-Entscheidungen zur Künstlersozialabgabe nach dem 01.06.2022 (Abgabepflicht von Unternehmen)

**Datum des Versuchs:** 08.10.2026

**Gesucht:** Neue BSG-Entscheidungen des 3. Senats (B 3 KS/B 3 KR) zur Abgabepflicht von Unternehmen nach dem 01.06.2022.

**Versuchte Quellen:** `bsg.bund.de`, Übersichtsseiten `verhandlungstermine_uebersicht_2022.html` bis `verhandlungstermine_uebersicht_2026.html` vollständig durchsucht.

**Ergebnis: Es existieren keine solchen Entscheidungen.** Die einzigen gefundenen B-3-KS-Verfahren 2022–2024 (B 3 KS 1/21 R, B 3 KS 2/21 R, B 3 KS 1/22 R, B 3 KS 1/23 R, B 3 KS 2/22 R) betreffen ausschließlich die Versicherungspflicht einzelner Künstler (Innenraumgestaltung, Tanzpädagogin, Flamencotanz, Tattookünstlerin, Hochzeitsrednerin), nicht die Abgabepflicht von Unternehmen. Das ist kein Rechercheversagen, sondern ein geprüftes Negativ-Ergebnis: Es gibt schlicht keine neue Abgabepflicht-Rechtsprechung des BSG seit B 3 KS 3/21 R (01.06.2022).

## Punkt A.2 — LSG/SG-Entscheidungen ohne freien Volltext

**Datum des Versuchs:** 08.10.2026

**Betroffen:** LSG Baden-Württemberg 27.04.2006 L 4 KR 2222/02; SG Stuttgart 24.03.2021 S 4 KR 2996/17; LSG Niedersachsen-Bremen (Celle) 22.12.2022 L 2 BA 49/22 B ER; LSG Berlin-Brandenburg 19.05.2019 L 1 KR 196/17; LSG Berlin-Brandenburg 11.02.2026 L 1 KR 367/23; LSG Baden-Württemberg 27.02.2026 (Aktenzeichen nicht ermittelbar).

**Versuchte Quellen:**
- `landesrecht-bw.de`: Direkter Abruf der Basisseite liefert nur eine leere React-SPA-Hülle (`<div id='container'>`, kein serverseitig gerenderter Inhalt) — die früher über Suchmaschinen gefundenen `jportal`-Links sind veraltet und führen zur selben leeren Hülle. Nicht automatisiert abrufbar.
- `sozialgerichtsbarkeit.de`: Sowohl die Startseite als auch einzelne Entscheidungs-URLs (`/entscheidungen/<id>`, `/legacy/<id>`, `/node/<id>`) liefern bei direktem Abruf nur eine 800-Byte-JavaScript-Hülle ("Sie müssen JavaScript aktivieren"). Mehrfach mit unterschiedlichen URL-Mustern getestet — immer dasselbe Ergebnis.
- `gerichtsentscheidungen.brandenburg.de`: Funktioniert grundsätzlich (siehe zwei andere Treffer), aber für L 1 KR 196/17 und L 1 KR 367/23 konnte über Websuche keine passende Dokument-ID auf dieser Domain ermittelt werden; die Suchfunktion der Domain selbst (`/search?q=...`) lieferte HTTP 404.

**Ergebnis: nicht gefunden (kein freier Volltext).** Alle sechs Treffer stehen mit Gericht, Datum, Aktenzeichen (soweit bekannt) und Thema in `quellen/ergaenzend/urteile/LISTE_LSG_SG.md`.

## Punkt A.3 — Ältere BSG-Entscheidungen (2003–2008), vor dem Abdeckungsbeginn der freien Volltext-Datenbanken

**Datum des Versuchs:** 08.10.2026

**Gesucht:** B 3 KR 29/04 R (07.07.2005); B 3 KR 8/03 R (12.11.2003); B 3 KR 10/03 R (12.11.2003); B 3 KR 15/03 R (04.03.2004); B 3 KR 27/99 R (31.08.2000); 3 KR 10/97 R (24.06.1998); B 3 KR 7/97 R (16.04.1998); B 3 KR 1/98 R (17.06.1999); B 3 KR 37/02 R (24.07.2003); B 3 KS 4/07 R (18.09.2008).

**Versuchte Quellen:**
- `bsg.bund.de`: Strukturiertes Archiv deckt nur ca. ab 2018 ff. ab (mehrfach bestätigt).
- `rechtsprechung-im-internet.de`: Über die Suchmaske (session-basiert) für jedes einzelne Aktenzeichen gesucht → **für alle zehn Fälle 0 Treffer.** Das deckt sich mit der bereits in einer früheren Sitzung festgestellten Abdeckungsgrenze dieser Datenbank (zuverlässig ab ca. 2008–2010, nicht davor — B 3 KS 4/07 R vom 18.09.2008 liegt bereits außerhalb, während spätere Fälle ab 12.08.2010 gefunden wurden).

**Ergebnis: nicht gefunden.** Keine der zehn Entscheidungen ist über die erlaubten freien Quellen abrufbar.

## Punkt A.3 (Fortsetzung) — BSG-Entscheidung „B 3 KS 1/08 R" — Datumskorrektur

**Datum des Versuchs:** 08.10.2026

**Aufgabe:** In `quellen/KSK-Checkliste_Eigenwerber.pdf` wird dieses Urteil mit dem Datum **18.09.2018** zitiert. Das ist ein Tippfehler im Original-Dokument der Künstlersozialkasse.

**Gefunden (per Websuche, Sekundärquellen judicialis.de und ksk-rechtshilfe.de):** Das korrekte Entscheidungsdatum ist **18.09.2008**, nicht 18.09.2018. Das Urteil betrifft die Abgabepflicht eines Luftverkehrsunternehmens für einen freien Mitarbeiter für Kommunikation/Gestaltung von Geschäftsberichten und Mitarbeiterzeitschriften.

**Versuchte Quellen für den Volltext:** `rechtsprechung-im-internet.de` (Suchmaske) → 0 Treffer, ebenso wie das am selben Tag entschiedene B 3 KS 4/07 R (siehe oben). `bsg.bund.de` → zu alt für das strukturierte Archiv.

**Ergebnis: Datum korrigiert und hier dokumentiert (18.09.2008 statt 18.09.2018), Volltext nicht gefunden.** Die fehlerhafte Originaldatei `KSK-Checkliste_Eigenwerber.pdf` wurde nicht verändert (ist eine amtliche Quellenkopie mit ihrem eigenen Fehler).

---

# Recherche 3 (09.10.2026) — gemäß `aufgaben/PROMPT_ClaudeCode_Recherche_3.md`

## Punkt A.1 — BMF-Schreiben/Verwaltungsanweisungen zur steuerlichen Behandlung der Künstlersozialabgabe (Betriebsausgabe, Umsatzsteuer, Rückstellung)

**Datum des Versuchs:** 09.10.2026

**Gesucht:** Ein BMF-Schreiben oder eine Verwaltungsanweisung, die speziell die steuerliche Behandlung der von Unternehmen gezahlten Künstlersozialabgabe (als Betriebsausgabe, bei der Umsatzsteuer, als Rückstellung/Passivierung) regelt.

**Versuchte Quellen:**
- Websuche nach "BMF Schreiben Künstlersozialabgabe Betriebsausgabe/Rückstellung/Umsatzsteuer" → nur Fachverlags-/Kanzlei-Blogartikel (NWB, Haufe, ecin.de, ksklar.de, experto.de), die übereinstimmend berichten, dass die Künstlersozialabgabe nach den **allgemeinen** Grundsätzen (§ 4 Abs. 4 EStG als Betriebsausgabe; Rückstellung für ungewisse Verbindlichkeit nach allgemeinen bilanzrechtlichen Regeln) behandelt wird, ohne ein spezifisches BMF-Schreiben zu zitieren.
- `esth.bundesfinanzministerium.de`, Amtliches Einkommensteuer-Handbuch, Anhang 1a II (per direktem Abruf geprüft, u. a. Ausgabe 2016): Dieser Anhang behandelt nicht die Unternehmens-Abgabe, sondern die **Datenübermittlung der Künstlersozialkasse zum Sonderausgabenabzug des Künstlers selbst** nach § 10 Abs. 1 Nr. 2/3 EStG (Rentenversicherungsbeitrag des Künstlers). Kein Bezug zur Betriebsausgaben-/Rückstellungsfrage der Unternehmen.
- Websuche nach "BMF" + "Künstlersozialabgabe" direkt auf `bundesfinanzministerium.de` → keine einschlägigen Treffer zu einem eigenständigen BMF-Schreiben.

**Ergebnis: nicht gefunden.** Es existiert nach dieser Recherche kein eigenständiges BMF-Schreiben zur steuerlichen Behandlung der Künstlersozialabgabe bei Unternehmen; die Abgabe wird unstreitig nach den allgemeinen ertrag- und bilanzsteuerlichen Vorschriften behandelt (keine Sondervorschrift gefunden).

## Punkt A.2 — BFH-Entscheidungen zur Künstlersozialabgabe (steuerliche Behandlung, Rückstellungen)

**Datum des Versuchs:** 09.10.2026

**Gesucht:** BFH-Entscheidungen, die sich mit der Künstlersozialabgabe (z. B. Rückstellungsbildung dafür) befassen.

**Versuchte Quellen:**
- Websuche nach "BFH Künstlersozialabgabe Rückstellung/Betriebsausgabe Urteil Aktenzeichen" → kein Treffer mit direktem Sachbezug zur Künstlersozialabgabe. Das einzige in den Trefferlisten auftauchende Rückstellungs-Grundsatzurteil (BFH v. 19.10.2005, XI R 64/04, BStBl 2006 II S. 371) betrifft eine Rückforderung von Honoraren durch eine Kassenärztliche Vereinigung (KVH) — kein KSA-Bezug, nur allgemein zur Rückstellungsbildung zitiert.
- `bundesfinanzhof.de`, Entscheidungssuche (`/de/entscheidungen/entscheidungen-online/`): Die Ergebnisliste wird clientseitig per JavaScript nachgeladen; ein direkter Abruf der Such-URL liefert nur die leere Seitenhülle ohne Trefferliste (automatisiert nicht auswertbar, analog zu den bereits in Recherche 2 festgestellten JS-Hüllen bei sozialgerichtsbarkeit.de und landesrecht-bw.de).
- `rechtsprechung-im-internet.de`: Die Entscheidungssuche ist session-basiert (bestätigt bereits in Recherche 2); ein direkter GET-Aufruf mit Suchparametern liefert HTTP 500 statt einer Trefferliste.

**Ergebnis: nicht gefunden.** Es konnte über die automatisiert zugänglichen, erlaubten Quellen keine BFH-Entscheidung mit unmittelbarem Künstlersozialabgabe-Bezug identifiziert werden.

## Punkt B.3 — Entscheidungen zu Insolvenz, Konzern/verbundene Unternehmen, Geschäftsführerhaftung, Betriebsübergang (Künstlersozialabgabe)

**Datum des Versuchs:** 09.10.2026

**Gesucht:** BSG/LSG/SG-Entscheidungen zur Künstlersozialabgabe im Zusammenhang mit: Insolvenz des Abgabepflichtigen, Konzern/verbundene Unternehmen, persönlicher Haftung von Geschäftsführern für KSA-Rückstände, Betriebsübergang nach § 613a BGB.

**Gefunden (anderes Teilthema, Rechtsnachfolge/Umwandlung):** BSG, Urteil vom 04.03.2004, B 3 KR 12/03 R (Volltext gespeichert, siehe `quellen/ergaenzend/urteile/BSG_2004-03-04_B3KR12-03R.txt`) — betrifft identitätswahrende Umwandlung (GbR → OHG → GmbH) und die Frage, dass ein Erfassungsbescheid auch gegenüber Rechtsnachfolgern wirkt. Darin referenziert: BSG, Urteil vom 10.10.2000, B 3 KR 31/99 R (SozR 3-5425 § 24 Nr 20) — selbe Rechtsfrage, Volltext bei dieser Recherche nicht gesondert gesucht/gefunden.

**Versuchte Quellen für die übrigen Teilthemen:**
- Websuche nach "Künstlersozialabgabe Insolvenz/Insolvenzverwalter/Forderungsanmeldung Sozialgericht Urteil" → nur allgemeine Verwaltungsportal-Hinweise ("KSK ist Insolvenzgläubigerin, meldet Forderungen zur Tabelle an"), keine zitierfähige Gerichtsentscheidung mit KSA-Insolvenz-Bezug gefunden. Zwei zufällige Treffer mit Aktenzeichen (Hessisches LSG 06.03.2007 L 8 KR 214/06 ER; SG Dortmund 25.02.2011 S 34 R 321/08) betreffen bei Prüfung andere Themen (Gemeinnützigkeit/Öffentlichkeitsarbeit bzw. Verein/Webdesign), keine Insolvenz.
- Websuche nach "Künstlersozialabgabe Konzernunternehmen/verbundene Unternehmen Abgrenzung Urteil" → kein Treffer zu einer Entscheidung, die speziell Konzernstrukturen/verbundene Unternehmen zum Gegenstand hat (nur allgemeine Erfassungsbescheid-Rechtsprechung zu mehreren Tätigkeitsbereichen eines einzelnen Unternehmens, BSG v. 21.06.2012, B 3 KS 2/11 R — kein Konzern-Bezug).
- Websuche nach "Künstlersozialabgabe Geschäftsführer persönliche Haftung GmbH Rückstände Urteil" → nur Treffer zur (bereits in Recherche 2 dokumentierten) Frage, ob das Geschäftsführer-Gehalt selbst der KSA unterliegt; keine Entscheidung zur persönlichen Haftung für Abgabenrückstände nach § 823 BGB/§ 69 AO o. ä. gefunden.
- Websuche nach "Künstlersozialabgabe Betriebsübergang § 613a BGB Urteil Sozialgericht" → nur allgemeine arbeitsrechtliche Kommentierung zu § 613a BGB (Sozialversicherungsbeiträge gehen bei Betriebsübergang nicht automatisch auf den Erwerber über), keine KSA-spezifische Gerichtsentscheidung gefunden.

**Ergebnis: Für Insolvenz, Konzern/verbundene Unternehmen, Geschäftsführerhaftung und Betriebsübergang nicht gefunden.** Für Rechtsnachfolge/Umwandlung wurde eine einschlägige Entscheidung gefunden und gespeichert (s. o.).

## Punkt C.5 — Neue Leistungsarten und Plattformen (Künstlersozialabgabe)

**Datum des Versuchs:** 09.10.2026

**Gesucht:** Offizielle oder gerichtliche Veröffentlichungen zur Abgabepflicht bei: Plattformen/Marktplätzen (Vermittlung von Künstlern), Streaming, Podcasts, Games/Spieleentwicklung, NFT/digitale Kunst, KI-generierte Grafik/Texte, Influencer-Verträge, Voice-Over/Synchronisation.

**Bereits im Repo abgedeckt (kein erneuter Download, da keine Dubletten geladen werden sollen):**
- Plattformen/Marktplätze (Vermittlung von Künstlern): `quellen/KSK-Info_27_Vermittlung_und_Vertretung.pdf` (bereits vorhanden).
- Games/Spieleentwicklung: `quellen/KSK-Info_06_Kuenstlerische_publizistische_Taetigkeiten_und_Abgabesaetze.pdf` listet bereits "Spieleautor" und "Game-Designer" als Berufsgruppen (geprüft, 2 Treffer im Volltext).
- Influencer-Verträge: `quellen/ergaenzend/KSK-FAQ_Unternehmen_und_Verwerter.txt` behandelt Influencer-Marketing bereits ausführlich (3 Treffer, inkl. Abgrenzung Gestaltungsleistung vs. Reichweite, Affiliate-Marketing-Ausnahme).
- Voice-Over/Synchronisation: `quellen/KSK-Info_09_Abgrenzungskatalog.pdf` nennt "Synchronisation" bereits als Berufsgruppe.
- Streaming: LSG Berlin-Brandenburg 11.02.2026 (L 1 KR 367/23, Musikaggregatoren/Streaming-Plattformen) bereits in `quellen/ergaenzend/urteile/LISTE_LSG_SG.md` als Treffer ohne freien Volltext dokumentiert (Recherche 2).

**Versuchte Quellen für die verbleibenden Themen (Podcasts, NFT/digitale Kunst, KI-generierte Grafik/Texte):**
- Websuche nach "Künstlersozialkasse Abgabepflicht Podcast" und Volltextsuche in allen bereits vorhandenen KSK-Text-/Info-Dateien (`KSK-FAQ_Unternehmen_und_Verwerter.txt`, `KSK-Webseite_Bemessungsgrundlage.txt`, `KSK-Webseite_Entgeltmeldung.txt`, `Info_06`, `Info_09`) nach "Podcast" → kein Treffer in offiziellen Quellen.
- Websuche nach "Künstlersozialabgabe NFT digitale Kunst Marktplatz" → nur allgemeine NFT-Marktartikel ohne KSA-Bezug, keine offizielle oder gerichtliche Quelle.
- Websuche nach "Künstlersozialversicherungsgesetz künstliche Intelligenz KI-generierte Werke Abgabepflicht Gericht" → keine Entscheidung oder offizielle Veröffentlichung zur KSA-Abgabepflicht bei KI-generierten Inhalten gefunden; die gefundenen Treffer betreffen ausschließlich die urheberrechtliche Schutzfähigkeit von KI-Werken (z. B. AG München v. 13.02.2026 zu KI-Logos), nicht die Künstlersozialabgabe.
- `kuenstlersozialkasse.de`-Domainsuche nach "Podcast"/"NFT"/"Künstliche Intelligenz" → keine Treffer.

**Ergebnis: Für Podcasts, NFT/digitale Kunst und KI-generierte Grafik/Texte nicht gefunden.** Es existiert nach dieser Recherche keine offizielle KSK-/DRV-Veröffentlichung oder Gerichtsentscheidung zu diesen drei Themen im KSA-Kontext; die übrigen fünf Teilthemen von Punkt C.5 sind bereits durch vorhandene Dateien abgedeckt (s. o.).

## Punkt D.6 — Antrag auf Befreiung von der Meldepflicht / Antrag auf Aufnahme in eine Ausgleichsvereinigung (eigenständiges Formular)

**Datum des Versuchs:** 09.10.2026

**Gesucht:** Ein eigenständiges PDF-Formular "Antrag auf Befreiung" (von der jährlichen Meldepflicht) sowie ein eigenständiges Antragsformular zur Aufnahme in eine Ausgleichsvereinigung.

**Versuchte Quellen:** Vollständige Link-Liste der Seiten `kuenstlersozialkasse.de/unternehmen-und-verwerter/entgeltmeldung`, `.../service-und-medien/mediencenter-unternehmen-und-verwerter` und `.../unternehmen-und-verwerter/ausgleichsvereinigung` nach PDF-Links durchsucht (alle dort verlinkten PDFs geprüft).

**Ergebnis: Es existiert kein eigenständiges Antragsformular.** Beide Vorgänge werden laut den geprüften Seiten nicht über ein separates PDF-Formular abgewickelt, sondern nur über die Informationsschrift `KSK-Info_19_Gruendung_von_Ausgleichsvereinigungen.pdf` (bereits im Repo vorhanden) bzw. durch formlose Mitteilung/Antrag an die KSK (Befreiung von der Meldepflicht). Kein Rechercheversagen, sondern geprüftes Negativ-Ergebnis. Stattdessen bei dieser Recherche gefunden und gespeichert: die zu `KSK-Merkblatt_Sozialversicherungsrechtliche_Beurteilung_von_Gesellschaftern_GmbH.pdf` gehörenden amtlichen Fragebögen Teil I und Teil II (s. `index.csv`).

---

# Recherche 4 (09.10.2026) — gemäß `aufgaben/PROMPT_ClaudeCode_Recherche_4.md`

## Punkt A.1 — Amtliches natives PDF zum 8. SGB IV-Änderungsgesetz (BGBl. 2022 I S. 2759)

**Datum des Versuchs:** 09.10.2026 (erneuter Versuch nach Recherche 1)

**Versuchte URLs:**
- `https://www.recht.bund.de/bgbl/1/2022/56/regelungstext.pdf?__blob=publicationFile&v=1` → HTTP 404
- `https://www.recht.bund.de/bgbl/1/2022/56/VO.html` → HTTP 404
- `https://www.recht.bund.de/bgbl/1/2022/56/inhaltsverzeichnis.html` → HTTP 404
- `https://www.bgbl.de/xaver/bgbl/start.xav?startbk=Bundesanzeiger_BGBl&jumpTo=bgbl122s2759.pdf` → HTTP 200, aber `Content-Type: text/html` — liefert nur die JavaScript-gesteuerte Xaver-Viewer-Hülle (Dojo-Framework, `banz.control.TextPrintClickable`), kein natives PDF im Response-Body. Der „PDF in neuem Fenster anzeigen"-Button ist rein clientseitig (JS) implementiert; keine statische Download-URL im HTML auffindbar.

**Ergebnis: Natives PDF weiterhin nicht frei abrufbar.** `recht.bund.de` übernahm die amtliche Verkündung erst ab 01.01.2023; dieses Gesetz (ausgefertigt 20.12.2022, verkündet 28.12.2022) liegt davor und ist dort nicht hinterlegt. `bgbl.de` liefert das Dokument nur über einen interaktiven JavaScript-Viewer aus, dessen tatsächlicher PDF-Abruf eine Browser-Sitzung voraussetzt — das wurde nicht umgangen (keine Bot-Umgehung von Zugangsbeschränkungen). Ersatzweise verwendet: der bereits vorhandene Webarchiv-Textauszug `quellen/ergaenzend/BGBl_2022_I_2759_8SGB-IV-AendG_Archivtext.txt` sowie zur Gegenprüfung `quellen/ergaenzend/BT-Drs_20-4706_Beschlussempfehlung_Materialien.pdf` (beide bereits im Repo). Ergebnis zum Inkrafttreten: siehe Antwort an den Nutzer (wörtliches Zitat von Art. 34).

## Punkt B.4 — Neuere Fassungen der KSK-Infos 13, 14, 15, 16 (Berücksichtigung der Gesetzesänderung ab 01.01.2023)

**Datum des Versuchs:** 09.10.2026

**Geprüft:** Live-Abruf aller vier PDFs von `kuenstlersozialkasse.de` und Byte-für-Byte-Vergleich (`cmp`) mit den bereits im Repo vorhandenen Kopien (Abrufdatum 2026-10-08, Stand jeweils 09.2025).

**Ergebnis: Keine neuere Fassung vorhanden — alle vier Dateien sind byte-identisch mit der bereits vorhandenen Kopie.** Die KSK hat Info 13, 14, 15 und 16 seit dem letzten Abruf nicht aktualisiert; „Stand: 09.2025“ ist weiterhin die aktuelle Fassung. Info 13 (Ausstellungs-/Messegesellschaften) und Info 16 (Sozialversicherungsträger) verwenden nach wie vor den alten Fassung-A-Wortlaut „nicht nur gelegentlich“ im Zusammenhang mit der Generalklausel/Eigenwerbung (§ 24 Abs. 2 KSVG); Info 14 (Banken) und Info 15 (Chemische Industrie) enthalten diese Formulierung gar nicht (daher insoweit keine Diskrepanz). Es wurde keine neue Datei abgelegt, da keine neue Fassung existiert (keine Dublette geladen).

## Punkt B.5/B.6 — Weitere KSK-Infos, Merkblatt Ausgleichsvereinigung, DRV-Rundschreiben 2025/2026

**Datum des Versuchs:** 09.10.2026

**Punkt 5 (KSK-Infos 01, 01a, 06, 19, 26; Merkblatt Ausgleichsvereinigung §§ 32 ff. KSVG):** Alle fünf Informationsschriften liegen bereits im Repo vor (`quellen/KSK-Info_01_...pdf`, `_01a_...pdf`, `_06_...pdf`, `_19_...pdf`, `_26_...pdf`). Ein eigenständiges „Merkblatt zur Ausgleichsvereinigung" existiert laut vollständiger Link-Liste der KSK-Mediencenter-Seite (geprüft bereits in Recherche 3, Punkt D.6/D.7, und erneut per Websuche geprüft) nicht separat — § 32 ff. KSVG werden ausschließlich in `KSK-Info_19_Gruendung_von_Ausgleichsvereinigungen.pdf` behandelt (bereits im Repo). Kein neuer Download nötig.

**Punkt 6 (Rundschreiben/Hinweise der KSK/DRV für 2025–2026: Abgabesatz, Geringfügigkeitsgrenze 700 €/1.000 €, Meldeverfahren):**
- Geprüft: `deutsche-rentenversicherung.de/.../summa-summarum/Rundschreiben/rundschreiben` (vollständige Liste der DRV-Rundschreiben) → **kein eigenständiges DRV-Rundschreiben zur Künstlersozialabgabe.** Die Seite verweist unter „Interessante Links" lediglich auf die Künstlersozialkasse selbst; die DRV gibt zur KSA kein eigenes Rundschreiben heraus.
- Geprüft: `bundestag.de/resource/blob/1102716/kuenstlersozialabgabe.pdf` (Infobrief WD 6 - 3010 - 025/25 der Wissenschaftlichen Dienste, 17.07.2025) → behandelt eine andere, engere Frage (Abgabepflicht von Bundestagsabgeordneten selbst), nicht Abgabesatz/Bagatellgrenze/Meldeverfahren allgemein. Nicht gespeichert, da nicht einschlägig für Punkt 6.
- Geprüft: `kuenstlersozialkasse.de/fileadmin/.../Mediencenter_Künstler_Publizisten/.../Aktuelle_Werte_in_der_SV_2026_bf.pdf` → betrifft die Beitragssätze der **versicherten Künstler** (Renten-/Kranken-/Pflegeversicherung), nicht den Abgabesatz oder die Bagatellgrenze der **abgabepflichtigen Unternehmen**. Nicht gespeichert, da falsche Zielgruppe/falsches Thema.
- Die tatsächlich einschlägigen Originalquellen (Abgabesatz 2025/2026, Bagatellgrenze 700 €/1.000 €, Meldeverfahren) liegen bereits im Repo vor: `KSK-Info_05_Abgabepflicht_fuer_Eigenwerber.pdf`, `KSK-Info_06_Kuenstlerische_publizistische_Taetigkeiten_und_Abgabesaetze.pdf`, `ergaenzend/KSK-Webseite_Entgeltmeldung.txt`, `BGBl_2026_I_262_KSA-Verordnung_2027.pdf`, `KSAbg2026V.pdf` u. a.

**Ergebnis: Keine neue Originalquelle gefunden, die nicht bereits im Repo vorhanden oder nicht zutreffend für diesen Punkt ist.**

## Punkt C.7 — Rechtsprechung zu § 24 Abs. 2 KSVG in der Fassung ab 2023 (Geringfügigkeitsgrenze, Eigenwerbung, Generalklausel)

**Datum des Versuchs:** 09.10.2026

**Gesucht:** BSG-, LSG- und SG-Entscheidungen, die § 24 Abs. 2 KSVG bereits in der seit 01.01.2023 geltenden Fassung (Wegfall „nicht nur gelegentlich", Geringfügigkeitsgrenze statt Regelmäßigkeitskriterium) anwenden.

**Versuchte Suchbegriffe:** „BSG LSG SG Urteil § 24 Abs. 2 KSVG 2023 2024 2025 Geringfügigkeitsgrenze Eigenwerbung"; „Künstlersozialabgabe Urteil 2024 2025 Bagatellgrenze 700 Euro Generalklausel Sozialgericht"; „Künstlersozialabgabe Urteil 2025 2026 Generalklausel LSG OR SG Aktenzeichen"; „Künstlersozialabgabe Eigenwerbung Urteil neue Rechtslage ab 2023 Sozialgericht Landessozialgericht".

**Ergebnis: nicht gefunden.** Es wurde keine Entscheidung identifiziert, die § 24 Abs. 2 KSVG n. F. (ab 2023) inhaltlich anwendet. Der einzige Treffer mit Bezug zur Generalklausel aus dem relevanten Zeitraum ist LSG Berlin-Brandenburg, 11.02.2026, L 1 KR 367/23 (Musikaggregatoren) — bereits in `LISTE_LSG_SG.md` als Treffer ohne freien Volltext dokumentiert (Recherche 2); dort wird zwar die Generalklausel erörtert, aber unter Bezug auf die ältere BSG-Rechtsprechung, nicht erkennbar unter der Schwellenwert-Neufassung. Plausible Erklärung: Die Gesetzesänderung trat erst am 01.01.2023 in Kraft; sozialgerichtliche Verfahren bis zur Revisionsinstanz dauern erfahrungsgemäß mehrere Jahre, sodass zum jetzigen Zeitpunkt noch keine einschlägige Rechtsprechung zur neuen Fassung vorliegen dürfte. Keine neue Datei abgelegt.

## Punkt C.8 — Zehn ältere BSG-Urteile (1998–2008): Ergebnis des Neuversuchs

**Datum des Versuchs:** 09.10.2026

**Versuchte Quellen:** `bsg.bund.de` (strukturiertes Archiv, erneut geprüft — deckt bestätigt weiterhin nur ca. ab 2018 ff. ab, Test-URL für B 3 KR 37/02 R liefert HTTP 404); `rechtsprechung-im-internet.de` (Suchmaske weiterhin session-basiert, kein Fortschritt gegenüber Recherche 2); zusätzlich zu den in Recherche 2 genutzten Quellen in diesem Durchgang neu herangezogen: `lexetius.com` (freie Volltext-Urteilsdatenbank, bereits in Recherche 3 für ein anderes Urteil verwendet) — dort gezielt nach Nachbar-IDs rund um bereits bekannte Fundstellen gesucht.

**Ergebnis: Fünf der zehn Urteile jetzt im Volltext gefunden** (siehe `index.csv` und `quellen/ergaenzend/urteile/`): B 3 KR 10/03 R (12.11.2003), B 3 KR 15/03 R (04.03.2004), B 3 KR 7/97 R (16.04.1998), B 3 KR 10/97 R (24.06.1998, in der ursprünglichen Liste als „3 KR 10/97 R" ohne „B" zitiert), B 3 KR 37/02 R (24.07.2003).

**Weiterhin nicht gefunden (5 von 10):** B 3 KR 29/04 R (07.07.2005); B 3 KR 8/03 R (12.11.2003); B 3 KR 27/99 R (31.08.2000); B 3 KR 1/98 R (17.06.1999); B 3 KS 4/07 R (18.09.2008). Für diese fünf wurde auf lexetius.com gezielt in der Nachbarschaft bekannter ID-Treffer gesucht (z. B. IDs 2003,3433–3450 um den gefundenen Nachbarfall B 3 KR 10/03 R für B 3 KR 8/03 R; IDs 1999,1450–1460 um den Nachbarfall vom 17.06.1999 für B 3 KR 1/98 R) — ohne Treffer. Eine Recherche über `dejure.org`'s Vernetzungsdienst wurde nach einer HTTP-402-Antwort („Payment Required") nicht fortgesetzt (keine Umgehung von Zugangsbeschränkungen).
