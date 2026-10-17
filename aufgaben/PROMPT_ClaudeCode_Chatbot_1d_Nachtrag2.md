# Nachtrag 2 zu Chatbot Teil 1d (aus `aufgaben/PRUEFBERICHT_Chatbot_Teil1d.md`)

Vor Beginn `git pull`. Nur `app/` und `tests/app/`. Keine Festwerte im Code: Wortlisten stehen in `app/baustein_konfiguration.json` (oder einer gleichartigen Konfigurationsdatei), nicht im Python-Code.

## A. Technische Härtung (sicher umsetzbar)
1. Nach dem Einsetzen der Platzhalter darf im Text **keine geschweifte Klammer** mehr stehen. Platzhaltererkennung vor dem Einsetzen **ohne Beachtung der Groß-/Kleinschreibung** und auch für `{{…}}`: `{abgabe}` und `{{ABGABE}}` werden verworfen (Fälle d2, d3).
2. Im Modelltext verboten: Links (`http`, `https`, `www.`, `://`, Markdown-Link `[…](…)`), Mailadressen, jedes HTML-Tag (`<…>`), Markdown-Überschriften und Zeichen, mit denen der Schlusssatz nachgebaut werden könnte (Fälle d4, d6, d8). Der Schlusssatz und alle Überschriften/Kennzeichen kommen nur vom System; das Modell darf keinen Satz mit „geprüft", „freigegeben", „bestätigt", „offiziell", „verbindlich" schreiben.
3. Alle neuen Verbote als Konfigurationseinträge (Wörter, Muster) mit kurzer Begründung.

## B. Wortlisten erweitern (nützlich, aber nie vollständig – siehe Bericht)
Groß-/Kleinschreibung ignorieren; Wortstämme prüfen (z. B. „abgabe…", „zahl…", „pflicht…", „frei…", „befrei…").
1. **Schlussfolgerungen** (b1–b7): unterliegen/unterliegt, zahlungspflichtig, Zahlungspflicht, abgabefrei, abgabenfrei, Meldepflicht, entfällt/entfallen, fällig, schuldet, verpflichtet, befreit, Pflicht, müssen/muss zahlen, sollten/sollen/empfehle(n), ratsam, besser nicht, kein Anlass, unbedenklich.
2. **Gewissheit** (b7): sicher, eindeutig, zweifelsfrei, garantiert, definitiv, unstrittig, zwingend, ohne Zweifel, rechtssicher.
3. **Gerichte, Behörden, Bestätigungen** (c1–c5): Bundesgerichtshof, BGH, Bundesfinanzhof, BFH, Landessozialgericht, LSG, Sozialgericht, Finanzgericht, Verwaltungsgericht, Gericht, Behörde, Finanzamt, Rentenversicherung, DRV, Künstlersozialkasse, KSK (nur außerhalb von Platzhaltern), offiziell, amtlich, bestätigt, geprüft, genehmigt, freigegeben.
4. Die Mutationsprobe (jede Regel einzeln abschalten, ein Test muss scheitern) gilt auch für diese Listen: je Gruppe mindestens ein Fall.
5. Tests: alle Fälle b1–d8 aus `aufgaben/audit/gegenproben_teil1d_runde3.py` als Unittest (`tests/app/test_gegenproben_3.py`) übernehmen; die Kontrollfälle q1/q2 müssen durchgehen.

## C. Nicht umsetzen – wartet auf Entscheidung des Nutzers
Die grundsätzliche Lösung für „freier Text mit Rechtsbehauptungen" (Auswahl vorformulierter, vom Berufsträger geprüfter Bausteine statt freier Sätze) ist noch nicht entschieden. Keine Vorarbeiten daran, außer: im Bericht nennen, wie viele der Sätze in den Musterdialogen sich als feste Bausteine aus dem Regelkatalog (Spalten Voraussetzung, Rechtsfolge, Fundstelle) darstellen ließen und wie viele echten freien Text brauchen (Zählung in `aufgaben/FUNDE_Chatbot.md`, nur Zahlen).

## D. Abschluss
`python scripts/pruefe_alles.py` (mit installierten Paketen, auch `tests/app`) muss ALLES GRÜN melden. Sandbox-Nachweis (frischer Klon, neue Umgebung) nach 1d: Ergebnis in `aufgaben/SANDBOX_Nachweis.md`. Push, Arbeitsstand aktualisieren. Antwort nur: Dateien, Testzahl, welche der 17 Lücken geschlossen sind, was nicht geht.
