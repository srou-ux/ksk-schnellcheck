# Auftrag an Claude Code (lokal, C:\ksk cloud) – Recherche 1

Regeln: nur öffentliche Quellen herunterladen; keine Kundendaten; nichts außerhalb von `quellen/` ändern. Vor Beginn `git pull`. Jede Datei: Quelle (URL), Abrufdatum, SHA256 in `quellen/index.csv` eintragen (Spalten wie bestehende Zeilen; Dokumentart ehrlich angeben: Urteil / Gesetz-Momentaufnahme / Archivkopie). Nichts erfinden: Was nicht gefunden wird, in `quellen/NICHT_GEFUNDEN.md` mit Datum und versuchter URL notieren.

## A. Fehlende BSG-Urteile (Volltext als PDF oder Text, nach `quellen/ergaenzend/urteile/`)
1. BSG, Urteil zu Veranstaltern, Aktenzeichen **B 3 KS 2/16 R** (2017)
2. BSG zur Werbefotografie (2010) – Aktenzeichen über Suche ermitteln (Stichwort Künstlersozialabgabe Werbefotografie BSG 2010)
3. BSG zu Berufskammer (2014) – Aktenzeichen ermitteln
4. BSG zu Designbüro (2015) – Aktenzeichen ermitteln
5. BSG zu Webdesigner (2005) – Aktenzeichen ermitteln
Quellen: bundessozialgericht.de, sozialgerichtsbarkeit.de, openjur.de, dejure/rechtsprechung-im-internet.de (nur freie Volltexte). Aktenzeichen und Datum im Dateinamen: `BSG_<JJJJ-MM-TT>_<Aktenzeichen>.pdf`.

## B. Gesetzestexte
6. KSVG, Stand Jahresende 2025 (Fassung vom/ab 01.01.2026 gekennzeichnet) von gesetze-im-internet.de als PDF; als „Momentaufnahme mit Abrufdatum" kennzeichnen.
7. BGBl. 2022 I S. 2759 (8. SGB IV-Änderungsgesetz) als natives PDF von recht.bund.de / bgbl.de, falls frei abrufbar.
8. SGB IV § 25 (Verjährung) und KSVG §§ 26–29, 31, 35, 36, 36a, 37 sind im KSVG-PDF enthalten; zusätzlich prüfen, ob die KSK-Webseite aktuelle Abgabesatz-Seite hat (Satz 2027 steht bereits in BGBl 2026 I 262).

## C. Danach
`git add quellen/ && git commit && git push origin main`. In der Antwort nur: Liste „heruntergeladen" / „nicht gefunden", mit Dateinamen.
