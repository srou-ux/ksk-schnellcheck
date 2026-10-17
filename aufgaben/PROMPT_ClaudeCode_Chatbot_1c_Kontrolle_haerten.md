# Auftrag an Claude Code – Chatbot Teil 1c: Antwort-Kontrolle härten

Grundlage: `aufgaben/PRUEFBERICHT_Chatbot_Teil1.md` (Befunde B1–B8) und `aufgaben/audit/gegenproben_teil1.py`. Vor Beginn `git pull`. Nur `app/` und `tests/app/` ändern; keine Festwerte (Jahre, Beträge, Prozentsätze, Paragrafen) im Code.

1. **Kontrolle in jedem Pfad** (B6–B8): `pruefe_antwort` läuft vor jeder Ausgabe – auch bei Rückfrage, „Nicht abgedeckt" und Rechtsprechungsfrage. In diesen Pfaden sind **keine Beträge** erlaubt, außer sie stehen wörtlich in den gelieferten Hinweisen/Fakten des Nutzers; Fundstellen und Aktenzeichen nur aus den gelieferten Quellenstücken. Bei Fehlschlag: Ersatztext wie im Hauptpfad + Lückenprotokoll.
2. **Beträge in allen Schreibweisen** (B1): „€", „Euro", „EUR", „999,-", „1.000", „1000,00", Tausenderpunkt/ohne. Jede Zahl mit Währungsbezug muss aus Kernergebnis oder Fakten stammen.
3. **Prozentwerte** (B3): Jeder Prozentwert in der Antwort muss aus dem Kernergebnis (Abgabesatz) oder den gelieferten Quellenstücken stammen.
4. **Paragrafen** (B2): Jeder „§ … Gesetz"-Verweis muss in den gelieferten Regeln/Fundstellen vorkommen (normalisiert: „§ 24 Abs. 2 S. 2" = „§ 24 Abs. 2 Satz 2").
5. **Jahre und Fassung** (B4, B5): Jede Jahreszahl in der Antwort muss das Prüfjahr oder in den gelieferten Quellenstücken genannt sein. Nennt die Antwort „Fassung A/B" oder eine Schwelle, muss sie zur Fassung des Prüfjahres laut Kern passen (Fassung aus den Daten, nicht aus dem Code).
6. **Aktenzeichen** (B7 aus dem Bericht, Fall 07): breite Erkennung aller Schreibweisen („Az. 12 R 77/22", „B 12 KR 1/20 R", „1 BvR …", „Urteil vom … – …").
7. **Tests**: Alle Fälle aus `aufgaben/audit/gegenproben_teil1.py` als Unittests übernehmen (`tests/app/test_gegenproben.py`), jeder Fall muss `Pruefung fehlgeschlagen` bzw. den Ersatztext liefern, außer Fall 00 (korrekt). Zusätzlich: Positivtests, dass korrekte Antworten mit Kernbeträgen, Schwelle und Abgabesatz weiter durchgehen (keine falschen Ablehnungen). Mutationsprobe: Jede Prüfregel kurz abschalten – mindestens ein Test muss dann scheitern.
8. `pip install -r app/requirements.txt`; `python -m unittest discover -s tests/app` komplett (auch `test_main`). `aufgaben/FUNDE_Chatbot.md` aktualisieren. Pushen (`git pull --rebase origin main && git push origin main`).

Antwort nur: geänderte Dateien, Testergebnis (Anzahl), welche Befunde B1–B8 behoben sind, was nicht geht.
