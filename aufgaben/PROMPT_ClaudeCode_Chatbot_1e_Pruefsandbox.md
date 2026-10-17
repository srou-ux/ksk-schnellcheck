# Auftrag an Claude Code – Chatbot Teil 1e: Prüf-Sandbox mit unabhängiger Gegenrechnung

**Reihenfolge:** erst 1c, dann 1d fertig und gepusht, dann dieser Auftrag. Vor Beginn `git pull`. Alles bleibt auf GitHub. Keine Festwerte im Code (Zahlen nur aus dem Regelregister, siehe `kern/README.md`). Nutzer arbeitet unter Windows: alles muss auch dort laufen.

Ziel: Jede Rechnung des Kerns wird vor der Ausgabe in einer abgeschlossenen Python-Umgebung **unabhängig nachgerechnet**. Stimmt sie nicht exakt mit dem Kern überein, wird die Antwort nicht ausgegeben. Die Sandbox ist Teil des SaaS (läuft bei jeder Anfrage), nicht nur ein Testwerkzeug.

## A. Unabhängige Gegenrechnung (`verifier/`, neues Paket neben `kern/`)
1. **Eigener Rechenweg, kein Import von `kern/rechnen.py`.** Das Paket `verifier` darf `kern` nicht importieren (Test dafür: statische Prüfung der Importe). Es wird bewusst einfach und von Grund auf aus den Regeltexten (`regelwerk/Regelkatalog_24_KSVG_Entwurf.xlsx`, Blatt Regeln, Spalten Voraussetzung/Rechtsfolge/Fundstelle) und dem Regelregister gebaut. Wiederverwendung des Kern-Codes würde denselben Fehler zweimal bestätigen.
2. Eingabe nur: die strukturierten Fakten (JSON) und die Registerzeilen als Daten (`kern/parameter.json`, Abschnitt `register`, `abgabesatz`, `schwelle`, `pauschale`). **Nicht** das Ergebnis des Kerns.
3. Zu berechnen: Summe der Positionen (gleiche Ausschlussregeln wie im Regelkatalog: Kapitalgesellschaften, nicht künstlerisch, nachgewiesene Reisekosten, Gewinnzuweisung, Verwertungsgesellschaft, übliche Bewirtung, USt), Schwellenvergleich mit dem Operator aus dem Register, Bemessungsgrundlage, Abgabesatz des Jahres, Abgabe (nur wenn ohne Rundungsfrage; sonst „keine Zahl" wie im Kern), Vorauszahlung, Säumniszuschlag, Verpflegung, Übungsleiter-/Ehrenamtspauschale, Kommission, Schätzung Ausland, Rechnungssumme.
4. Rückgabe: Ergebnisklasse und alle Zahlen als Dezimalzahlen (`Decimal`).
5. **Vergleich** (`app/gegenrechnung.py`): Ergebnisklasse und jede Zahl müssen **exakt** gleich sein. Bei Abweichung: Antwort nicht ausgeben, Ergebnisklasse „Prüfung fehlgeschlagen", Text: „Gegenrechnung weicht ab (Kern: …, Gegenrechnung: …). Bitte manuell prüfen." + Eintrag ins Lückenprotokoll (anonymisiert, mit Fall-Hash). Ist die Fallart nicht von der Gegenrechnung abgedeckt, sagt das System das offen („nicht gegengerechnet"), nie stillschweigend „bestätigt".
6. Bei Bestätigung enthält die Antwort ein kurzes **Prüfprotokoll**: „Gegenrechnung bestätigt", Name der Prüfung, Version, die verwendeten Registerschlüssel mit Gültigkeit. Erzeugt vom System, nicht vom Modell (Platzhalter aus 1d).

## B. Abgeschlossene Ausführung (`app/sandbox.py`)
1. Die Gegenrechnung läuft in einem **eigenen Python-Prozess** (`subprocess`, `python -I`, bereinigte Umgebungsvariablen, eigenes leeres Arbeitsverzeichnis), Ein- und Ausgabe nur über JSON auf stdin/stdout. Es läuft **ausschließlich fest hinterlegter Code** aus `verifier/`. Das Sprachmodell darf dort nie Code schreiben oder ausführen.
2. Beschränkungen: Zeitlimit (aus einer Konfiguration, Voreinstellung wenige Sekunden), Speicherlimit wo das Betriebssystem es zulässt (Linux: `resource`; Windows: dokumentierte Alternative, z. B. Job-Objekt, oder Zeitlimit als Mindestschutz), **kein Netzwerk** (im Kindprozess `socket` sperren und per `sys.addaudithook` Netzwerk-, Datei-Schreib- und Prozessaufrufe außerhalb einer Positivliste verbieten), kein Schreibzugriff außerhalb des Temp-Ordners, keine Abhängigkeit von Dritt-Paketen.
3. Fehler, Zeitüberschreitung oder Absturz der Sandbox = Prüfung fehlgeschlagen (nie „bestätigt").
4. **Ehrlichkeit**: Das ist ein Schutz vor Fehlern und vor ungewolltem Verhalten, **kein vollständiger Sicherheitsrahmen** wie ein Container. In `app/README.md` offen schreiben, was die Sandbox kann und was nicht; Härtung (Container ohne Netzwerk, EU-Server) ist für das Hosting vorgesehen.

## C. Weitere Einsatzstellen
1. **Rechnungsanalyse**: Positionen unabhängig summieren; Abgleich „Summe der erfassten Positionen = Gesamtsumme laut Beleg"; Abweichung wird gemeldet („Positionen ergeben …, Beleg nennt …").
2. **Regeländerungen** (`python -m verifier.pruefe_register`): Prüft das Regelregister in der Sandbox: jedes Jahr 2019 bis zum höchsten Jahr lückenlos, keine Überschneidungen, jeder Wert plausibel (Spannen aus einer Konfigurationsdatei, nicht im Code), jede Zeile mit Fundstelle und Status; danach laufen alle Kern-Tests mit den neuen Werten. Ausgabe als Bericht für die Freigabe.
3. **Regressionstest** `scripts/pruefe_sandbox.sh` / `.ps1` (aus 1d) ruft die Sandbox-Tests mit auf.

## D. Tests (offline)
1. **Übereinstimmung**: Für alle Fälle aus `regelwerk/testfaelle_maschinenlesbar.json` und für mindestens 2000 zufällige Fälle (fester Startwert; Jahre 2019–2027, alle Anfragearten): Kern und Gegenrechnung liefern exakt dasselbe. Abweichungen sind Befunde und werden in `aufgaben/FUNDE_Chatbot.md` gemeldet (Kern oder Gegenrechnung ändern, nicht angleichen ohne Prüfung gegen den Regeltext).
2. **Fehler müssen auffallen (Mutation)**: Im Kern absichtlich Fehler einbauen (z. B. Vergleichsoperator `>` statt `>=`, falsche Pauschale, vertauschte Summenregel, ausgelassene Position) per Monkeypatch; die Gegenrechnung muss jeweils Abweichung melden. Dasselbe umgekehrt (Fehler in der Gegenrechnung). Liste der Mutationen und Ergebnis im Bericht.
3. **Sandbox-Verhalten**: Netzwerkzugriff im Kindprozess scheitert; Datei-Schreiben außerhalb scheitert; Endlosschleife wird nach dem Zeitlimit beendet; Absturz → „Prüfung fehlgeschlagen"; kein Import von `kern` im Paket `verifier` (statischer Test).
4. **Keine Festwerte**: Der Wächter-Test aus `tests/test_kern.py` wird für `verifier/` entsprechend angewandt (nur 100, 0.01, 12, 31 erlaubt).
5. Gesamtlauf in einer sauberen Sandbox-Umgebung (frischer Klon, neue virtuelle Umgebung) wie in 1d; Ergebnis in `aufgaben/SANDBOX_Nachweis.md` ergänzen (Anzahl Tests, Anzahl Zufallsfälle, Anzahl Mutationen, alle gefangen ja/nein).

## E. Große Zahlen, Menge und Zeitmessung (Ergänzung)
1. Zufallsfälle (D.1) umfassen Beträge bis 99.999.999.999,99 und Positionslisten mit bis zu 100.000 Positionen; Kern und Gegenrechnung müssen exakt übereinstimmen und die Gegenrechnung muss die Listen in einem Durchlauf unter dem Zeitlimit schaffen. Zu große Listen werden vorab abgelehnt statt abgebrochen (Grenze in `app/konfiguration.json`).
2. **Rundung**: Hat ein Ergebnis mehr als zwei Nachkommastellen, liefern Kern und Gegenrechnung beide „keine Zahl, Rundung ungeklärt"; stimmt das nicht überein, ist es ein Befund. Keine eigene Rundungsregel einführen.
3. **Zeitmessung**: Jede Anfrage protokolliert die Dauer je Schritt (Extraktion, Pflichtangaben, Kern, Gegenrechnung, Quellenabruf, Antwort, Kontrolle) in das anonymisierte Protokoll. `aufgaben/SANDBOX_Nachweis.md` nennt gemessene Mittel- und Höchstwerte über die Zufallsfälle (ohne Modellaufruf). Wird die Gegenrechnung im Mittel langsamer als 300 ms, einen dauerhaft laufenden Sandbox-Prozess vorschlagen (nicht ungefragt bauen).

## Grenzen (offen nennen)
- Die Gegenrechnung bestätigt die **Rechnung**, nicht die Einordnung (z. B. Rechtsform, künstlerisch ja/nein) und nicht die fachliche Richtigkeit der Regel. Beide Rechenwege lesen dieselbe Excel; ein falscher Wert in der Excel fällt hier nicht auf (dafür gibt es den Abgleich Register ↔ Quelltext in Teil 2 und die Fachprüfung).
- Fallarten ohne Gegenrechnung werden als „nicht gegengerechnet" gekennzeichnet.

Antwort nur: neue Dateien (Kurzliste), Testergebnis (Anzahl), Zahl Zufallsfälle und Abweichungen Kern ↔ Gegenrechnung, Mutationsbilanz, Sandbox-Nachweis, was nicht geht.
