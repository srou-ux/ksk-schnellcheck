# Auftrag an Claude Code (lokal, C:\ksk cloud) – Recherche 3

Erst starten, wenn Recherche 2 abgeschlossen und gepusht ist. Regeln wie bei Recherche 1 und 2: nur öffentliche, frei abrufbare Quellen; keine Kundendaten; nichts außerhalb von `quellen/` und `aufgaben/` ändern; vor Beginn `git pull`. Jede Datei mit URL, Abrufdatum und SHA256 in `quellen/index.csv` eintragen (Dokumentart ehrlich angeben). Volltext speichern, nichts zusammenfassen oder umformulieren. Nicht Gefundenes mit Datum und versuchter URL in `quellen/NICHT_GEFUNDEN.md` ergänzen (nichts löschen). Keine Umgehung von Captchas, Paywalls oder Zugangsbeschränkungen. Vorher prüfen, ob eine Datei schon im Repo liegt (Name und SHA256), nichts doppelt laden.

## A. Steuerliche und buchhalterische Behandlung der Künstlersozialabgabe
1. BMF-Schreiben oder Verwaltungsanweisungen zur Behandlung der Künstlersozialabgabe (Betriebsausgabe, Umsatzsteuer, Rückstellung/Passivierung) – soweit frei abrufbar (bundesfinanzministerium.de, Finanzverwaltungen der Länder).
2. BFH-Entscheidungen zur Künstlersozialabgabe (steuerliche Behandlung, Rückstellungen), Volltext von bundesfinanzhof.de oder rechtsprechung-im-internet.de.

## B. Haftung, Umstrukturierung, Sonderfälle (Rechtsprechung und Gesetz)
3. Entscheidungen (BSG, LSG, SG) zu: Rechtsnachfolge/Umwandlung/Verschmelzung, Insolvenz des Abgabepflichtigen, Konzern/verbundene Unternehmen, Haftung von Geschäftsführern, Betriebsübergang – jeweils im Zusammenhang mit der Künstlersozialabgabe. Volltext nach `quellen/ergaenzend/urteile/` (Dateiname `<Gericht>_<JJJJ-MM-TT>_<Aktenzeichen>.<pdf|txt>`); Treffer ohne Volltext in `quellen/ergaenzend/urteile/LISTE_LSG_SG.md` ergänzen.
4. Gesetzestexte als Momentaufnahme mit Abrufdatum nach `quellen/ergaenzend/`, nur falls nicht vorhanden: SGB IV §§ 28a ff. (Meldungen), § 28p (Prüfung), § 25 (Verjährung); InsO und HGB nur die Normen, die in Entscheidungen aus Punkt 3 zitiert werden.

## C. Neue Leistungsarten und Plattformen
5. Veröffentlichungen der KSK, der DRV, von Verbänden oder Gerichten zur Abgabepflicht bei: Plattformen/Marktplätzen (Vermittlung von Künstlern), Streaming, Podcasts, Games/Spieleentwicklung, NFT/digitale Kunst, KI-generierte Grafik und Texte, Influencer-Verträge, Voice-Over/Synchronisation. Nur Volltexte offizieller oder gerichtlicher Herkunft; Verbands- oder Kanzleiartikel nur, wenn sie ein Urteil im Volltext oder wörtlich mit Fundstelle wiedergeben, und dann als „Sekundärquelle“ kennzeichnen.

## D. KSK-Formulare und -Fragebögen
6. Aktuelle KSK-Formulare für Unternehmen: Anmeldebogen, Erhebungsbogen/Fragebogen zur Abgabepflicht, Meldebogen, Antrag auf Befreiung/Ausgleichsvereinigung, Formular zur Korrektur – als PDF mit Formularnummer und Stand im Dateinamen, falls nicht bereits in `quellen/` vorhanden.
7. Die KSK-Checkliste Veranstalter enthält auf Seite 3 eine Übersicht als Bild. Prüfen, ob dieselbe Übersicht als Text oder in einer anderen KSK-Veröffentlichung (z. B. Info 04, Webseite) vorliegt; wenn ja, Datei nennen.

## E. Abschluss
`git add quellen/ aufgaben/ && git commit -m "Recherche 3" && git pull --rebase origin main && git push origin main`. In der Antwort nur: Liste „heruntergeladen“ / „nicht gefunden“ mit Dateinamen und die Anzahl neuer Treffer in `LISTE_LSG_SG.md`.
