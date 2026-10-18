# Schnellcheck: Eingaben und Ergebniszustand abgesichert

Ausgangsstand: `5994db7f6a29a9c415e3e7430a0d61aeed5642d1` im Repository `srou-ux/ksk-schnellcheck`.
Der parallel entwickelte neue Schnellcheck wird beibehalten. Dieser Schritt ergänzt gezielte Fehlerbehebungen.
Es werden keine rechtlichen Regeln, Quellen, Excel-Werte oder Rechenfunktionen geändert.

## Behobene Fehler

1. **Stille Änderung des Betrags:** `12,345` wurde im Browser zu `12345`, `12.34,56` zu `1234.56`.
   Die Eingabe akzeptiert jetzt nur vollständige zulässige Schreibweisen. Deutsche Tausendergruppen und
   ein oder zwei Nachkommastellen bleiben erlaubt. Fehlerhafte Trennzeichen führen zur Korrekturaufforderung.
2. **Altes Ergebnis neben neuen Angaben:** Änderungen an Feldern, Auswahlwerten oder Positionen entfernen das Ergebnis.
   Antworten und Fehlermeldungen einer überholten Anfrage werden verworfen. Eine neuere Anfrage hat Vorrang.
3. **Formeln im CSV-Export:** Text aus Dokumenten konnte beim Öffnen in einer Tabellenkalkulation als Formel
   interpretiert werden. Formelpräfixe, auch hinter Leer- und Steuerzeichen, erhalten ein führendes Apostroph.
   Zeilenumbrüche einschließlich CR werden korrekt eingefasst. Bei Korrektur oder Zurücksetzen wird auch der
   gespeicherte Exportzustand gelöscht.

## Tatsächlich ausgeführte Prüfungen

- `python scripts/pruefe_alles.py`: vor und nach der Änderung **ALLES GRÜN**.
  33 Kern-Tests, 94 ausführbare Fachfälle, 21 Schnellcheck-Tests, 70 App-Tests und 31 Verifier-Tests;
  zusätzlich Regelwerk, Quellenbestand, 121 Quellenprüfsummen, Parameterabgleich, Testarchiv und Regelregister.
- `node --test tests/schnellcheck/frontend.test.cjs`: **8 von 8 bestanden**. Ausgeführt wird der tatsächliche
  JavaScript-Code aus beiden HTML-Dateien mit einem kleinen DOM-Ersatz, kein vollständiger Browser.
  Gegen den unveränderten Ausgangsstand schlagen alle acht Tests fehl.
- `python tests/app/livetest_dokumente.py`: **60 von 60** erfundene Dokumentfälle über echten HTTP-Server bestanden
  (PDF, XLSX, CSV; Upload, Bestätigung, Kern und Gegenrechnung).
- Der neue Playwright-Test wurde syntaktisch geprüft und in den GitHub-Workflow eingebunden.
  **Lokal kein bestandener Browsertest:** Chromium konnte in dieser Umgebung nicht installiert werden.
  Ein erfolgreiches CI-Browserergebnis ist gesondert zu kontrollieren.

## Grenzen

Diese Tests belegen technische Regressionen und die vorhandenen Testfälle, keine hundertprozentige fachliche
Richtigkeit. Die bekannten Lücken im Regelkatalog und die Freigabe durch einen Berufsträger bleiben offen.
Der manuelle Schnellcheck und der Dokumentenmodus bleiben zwei vorhandene Einstiege. Firmenkonten,
dauerhafte Fallablage, Veröffentlichung und Zusammenführung der Einstiege sind nicht Teil dieses Schritts.

Änderungen werden als separater Pull Request vorgelegt; `main` wird nicht überschrieben oder automatisch zusammengeführt.
