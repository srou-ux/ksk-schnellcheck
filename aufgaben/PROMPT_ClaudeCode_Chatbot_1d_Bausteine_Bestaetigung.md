# Auftrag an Claude Code – Chatbot Teil 1d: Bausteinantwort (Platzhalter) und Faktenbestätigung

**Reihenfolge:** erst Teil 1c (`PROMPT_ClaudeCode_Chatbot_1c_Kontrolle_haerten.md`) fertig und gepusht, dann dieser Auftrag. Vor Beginn `git pull`. Nur `app/`, `tests/app/` ändern. Keine Festwerte im Code (Jahre, Beträge, Prozentsätze, Paragrafen, Fassungen). Alles bleibt auf GitHub.

Ziel: Das Sprachmodell darf **keine Fakten schreiben**. Zahlen, Fundstellen, Aktenzeichen, Regel-IDs, Paragrafen, Jahre, Fassung und Ergebnisklasse setzt das System aus dem Kernergebnis und den gelieferten Quellenstücken ein. Zusätzlich bestätigt der Nutzer die erfassten Fakten, bevor gerechnet wird.

## A. Bausteinantwort mit Platzhaltern (`app/baustein.py`)
1. Das Modell schreibt nur Text mit Platzhaltern in der Form `{NAME}`. Die Platzhalter kommen aus einer **Liste, die der Router pro Anfrage aus dem Kernergebnis erzeugt** (z. B. `SUMME`, `SCHWELLE`, `ABGABESATZ`, `ABGABE`, `BEMESSUNGSGRUNDLAGE`, `JAHR`, `FASSUNG`, `FUNDSTELLE_1…n`, `REGEL_1…n`, `URTEIL_1…n`). Welche Platzhalter es gibt, bestimmt allein das Kernergebnis (keine feste Liste im Code).
2. Der Prompt an das Modell nennt nur die **Namen** der erlaubten Platzhalter und deren Bedeutung, **nicht die Werte**.
3. `fuelle(text, werte)` ersetzt die Platzhalter durch die Werte aus dem Kern. Format der Beträge einheitlich (Tausenderpunkt, Komma, zwei Nachkommastellen, „€"), zentral an einer Stelle.
4. **Verwerfen**, wenn der Modelltext vor dem Einsetzen enthält: (a) eine Ziffer außerhalb eines Platzhalters, (b) „§", (c) ein Aktenzeichen-Muster, (d) „Regel-ID"-Muster, (e) einen unbekannten Platzhalter, (f) Währungswörter mit Zahl („Euro", „EUR"), (g) das Zeichen „%". Dann: Ersatztext „Prüfung fehlgeschlagen" + Lückenprotokoll, nie Ausgabe des Modelltextes.
5. Der Schlusssatz „Entwurf – vom Steuerberater zu prüfen." wird vom System angehängt, nicht vom Modell geschrieben.
6. Die Prüfung aus Teil 1c läuft **zusätzlich nach dem Einsetzen** weiter (zweites Netz).
7. FakeLLM auf Platzhalterformat umstellen. Mistral-Adapter: Systemprompt und Beispielantwort mit Platzhaltern.

## B. Faktenbestätigung vor der Berechnung (`app/bestaetigung.py`)
1. Nach der Extraktion und der Pflichtangaben-Prüfung erzeugt das System aus den **extrahierten Fakten** (nicht vom Modell formuliert) eine Zusammenfassung: Jahr, Anfrageart, Beträge, Rollen, Rechtsform von Auftraggeber/Auftragnehmer, Leistungsart, Belege ja/nein. Beispiel: „Ich habe verstanden: Jahr 2026; Leistung: Grafik/Design; Auftragnehmer: natürliche Person; Auftraggeber: GmbH/UG/AG; Betrag 1.500,00 €. Stimmt das?"
2. Erst nach der Bestätigung („ja" / Button) wird der Kern aufgerufen. Antwortet der Nutzer mit einer Korrektur, wird neu extrahiert und erneut bestätigt. Die Bestätigung gehört zur Sitzung (`POST /frage` mit Sitzungskennung; `POST /bestaetigen`), im Speicher, nicht in Dateien.
3. Die Bestätigung gilt nur für genau die Fakten, die gezeigt wurden (Hash der Fakten); ändert sich ein Wert, ist eine neue nötig.
4. Weboberfläche: Bestätigungsfeld mit Ja/Korrigieren, Fakten als Liste.
5. Reine Rechtsprechungsfragen brauchen keine Bestätigung.

## C. Tests (offline, mit FakeLLM) und Nachweis in der Sandbox
1. Alle Fälle aus `aufgaben/audit/gegenproben_teil1.py` bleiben Tests und werden jetzt in der **Platzhalter-Architektur** geprüft: ein Modelltext mit eigener Zahl/Paragraf/Aktenzeichen wird verworfen.
2. **Eigenschaftstest** (`tests/app/test_eigenschaften.py`, nur Standardbibliothek, fester Zufallsstartwert): Erzeuge viele zufällige Fälle (Jahre 2019–2027, Beträge 0–100000, alle Rollen, alle Anfragearten). Für jede Antwort gilt: Jede Zahl in der Ausgabe stammt aus Kernergebnis oder Nutzerpositionen; jedes Jahr und jede Fassung passen zum Prüfjahr; jede Fundstelle stammt aus den gelieferten Stücken. Mindestens 2000 Fälle, Laufzeit unter 60 Sekunden.
3. **Mutationsproben** (`tests/app/test_mutation.py`): Jede einzelne Prüfregel in `baustein.py` und `pruefung.py` wird vorübergehend abgeschaltet (Monkeypatch); mindestens ein Test muss dann scheitern. Liste der Regeln und der fangenden Tests als Ausgabe.
4. Tests für B: ohne Bestätigung kein Kernaufruf; falsche Rechtsform korrigiert → neue Bestätigung; geänderte Fakten ungültig machen alte Bestätigung.
5. **Nachweis in einer sauberen Sandbox**: Frisch klonen in ein leeres temporäres Verzeichnis, virtuelle Umgebung anlegen, nur `app/requirements.txt` installieren, dann alle Tests laufen lassen (`python tests/test_kern.py`, `python tests/lauf_testfaelle.py`, `python -m unittest discover -s tests/app`). Skript `scripts/pruefe_sandbox.sh` (Linux/Mac) und `scripts/pruefe_sandbox.ps1` (Windows). Ergebnis (Anzahl bestanden/übersprungen/fehlgeschlagen) in `aufgaben/SANDBOX_Nachweis.md` mit Datum und Commit-Hash.
6. `app/README.md`, `aufgaben/FUNDE_Chatbot.md` aktualisieren; `git pull --rebase origin main && git push origin main`.

## D. Große Zahlen und Schreibweisen (Ergänzung)
1. **Einheitliche Ausgabe** der Beträge an genau einer Stelle: Tausenderpunkt, Komma, zwei Nachkommastellen, „€"; nie Exponentialschreibweise (aus „1E+12" wird „1.000.000.000.000,00 €"). Gilt für Antwort, Bestätigung und Prüfprotokoll.
2. **Eingabeformen** (Extraktion, mit FakeLLM-Tabelle und Mistral-Prompt-Beispielen): „1.234.567,89", „1 234 567,89", „1234567.89", „1,2 Mio.", „1,2 Millionen", „250 T€", „1.2M". Unklare Formen (z. B. „1.234" ohne Kontext) führen zu einer Rückfrage, nie zu einer Schätzung. Die Bestätigung zeigt den erfassten Betrag in der einheitlichen Form.
3. **Sinnprüfung**: Überschreitet ein Betrag oder eine Summe eine **konfigurierbare Grenze** (Datei `app/konfiguration.json`, nicht im Code; Voreinstellung großzügig), fragt das System vor der Berechnung nach („Der Betrag ist ungewöhnlich hoch. Stimmt 12.345.678,90 €?"). Dasselbe bei negativen Beträgen und Betrag 0.
4. Tests: Beträge von 0,01 bis 99.999.999.999,99; Schreibweisen aus Punkt 2; Rundungsfälle mit mehr als zwei Nachkommastellen (der Kern liefert dann keine Zahl: die Antwort sagt „Rundung ungeklärt" und nennt keine Abgabe, nie eine selbst gerundete).

## Grenzen (offen nennen)
- Die Platzhalter sichern, dass das Modell keine Fakten erfindet. Ob die Fakten richtig extrahiert wurden, sichert die Bestätigung durch den Nutzer. Ob der Kern fachlich richtig bewertet, bleibt Sache der Prüfung durch Steuerberater/Fachanwalt.
- Die Wirkung mit echtem Mistral ist erst mit Schlüssel prüfbar (Rauchtest).

Antwort nur: geänderte Dateien, Testergebnis (Anzahl) und Sandbox-Nachweis, welche Mutationen von welchen Tests gefangen werden, was nicht geht.
