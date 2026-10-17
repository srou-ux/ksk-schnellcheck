# Auftrag an Claude Code (lokal, C:\ksk cloud) – Recherche 4

Erst starten, wenn Recherche 3 abgeschlossen und gepusht ist. Regeln wie bisher: nur öffentliche, frei abrufbare Quellen; keine Kundendaten; nichts außerhalb von `quellen/` und `aufgaben/` ändern; vor Beginn `git pull`. Jede Datei mit URL, Abrufdatum und SHA256 in `quellen/index.csv` eintragen (Dokumentart ehrlich angeben). Volltext speichern, nichts zusammenfassen oder umformulieren. Nicht Gefundenes mit Datum und versuchter URL in `quellen/NICHT_GEFUNDEN.md` ergänzen (nichts löschen). Keine Umgehung von Captchas, Paywalls oder Zugangsbeschränkungen. Vorher prüfen, ob die Datei schon im Repo liegt (Name und SHA256). Danach `python tests/pruefe_quellen.py` ausführen und Fehler beheben.

Ziel: Das System soll bei KSK-Fragen belastbar belegen können. Diese Recherche schließt die Lücken, die der Prüfbericht und die Audits gezeigt haben.

## A. Amtliches Original zum Inkrafttreten der Fassung B des § 24 KSVG (Befund B4)
1. Das 8. SGB IV-Änderungsgesetz (BGBl. 2022 I S. 2759) als amtliches PDF aus dem Bundesgesetzblatt (recht.bund.de / bgbl.de, frei abrufbar). Ziel: Art. 17 Nr. 8 (Änderung KSVG § 24) und Art. 34 (Inkrafttreten) im Original. Ablegen nach `quellen/ergaenzend/`.
2. In der Antwort wörtlich zitieren: Art. 34 Abs. 1 und etwaige weitere Absätze zum Inkrafttreten, mit Seitenzahl. Ausdrücklich sagen, ob „01.01.2023“ für Art. 17 Nr. 8 bestätigt ist, abweicht oder nicht lesbar ist. Nicht raten.
3. Falls das Original nicht frei abrufbar ist: Gesetzesbegründung (Bundestags-Drucksache) zum selben Gesetz suchen und nennen, welche Datei das Datum stützt.

## B. Aktuelle KSK-Veröffentlichungen
4. Prüfen, ob die KSK-Infos 13, 14, 15, 16 inzwischen in einer Fassung vorliegen, die die Gesetzesänderung ab 01.01.2023 berücksichtigt. Neue Fassungen mit Stand im Dateinamen ablegen; die alten nicht überschreiben.
5. KSK-Infos 01, 01a, 06, 19, 26 und die Merkblätter zur Ausgleichsvereinigung (§§ 32 ff. KSVG), soweit nicht im Repo.
6. Aktuelle Rundschreiben und Hinweise der KSK/DRV für 2025–2026 (Abgabesatz, Geringfügigkeitsgrenze 700 € / 1.000 €, Meldeverfahren). Nur Originalquellen.

## C. Rechtsprechung nach 2022
7. Entscheidungen von BSG, LSG und SG zu KSVG § 24 Abs. 2 in der Fassung ab 2023 (Geringfügigkeitsgrenze, Eigenwerbung, Fälle der Generalklausel). Volltext nach `quellen/ergaenzend/urteile/` (Dateiname `<Gericht>_<JJJJ-MM-TT>_<Aktenzeichen>.<pdf|txt>`); Treffer ohne Volltext in `LISTE_LSG_SG.md` ergänzen. Wenn es keine gibt: in `NICHT_GEFUNDEN.md` mit Suchbegriffen und Datum eintragen.
8. Die zehn älteren BSG-Urteile, die laut `NICHT_GEFUNDEN.md` nicht frei verfügbar waren, noch einmal auf bsg.bund.de, rechtsprechung-im-internet.de und den Landesportalen suchen.

## D. Abschluss
`git add quellen/ aufgaben/ && git commit -m "Recherche 4" && git pull --rebase origin main && git push origin main`. In der Antwort nur: Ergebnis zu A (bestätigt / abweichend / nicht lesbar, mit wörtlichem Zitat), Liste „heruntergeladen“ / „nicht gefunden“ mit Dateinamen.
