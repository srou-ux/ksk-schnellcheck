# KSK-Schnellcheck – Anleitung

Kostenlose Ersteinschätzung ohne KI. Der Ordner enthält nur die Oberfläche und eine dünne Übersetzung der Eingaben;
**gerechnet und entschieden wird ausschließlich im vorhandenen Regelkern** (`app/dokument_pruefung.py` → `kern/rechnen.py`,
Gegenrechnung im `verifier/`). Keine Zahl, kein Jahr, keine Schwelle steht hier im Code.

## Dateien
- `pruefung.py` – Eingabeschema (feste Auswahlfelder), Auswahllisten aus dem Regelwerk, Aufruf von `auswerten()`.
- `web.py` – Webserver (WSGI, nur Standardbibliothek): `/`, `/api/optionen`, `/api/pruefen`, `/gesundheit`.
- `static/index.html` – die Seite (eine Datei, keine externen Schriften oder Skripte).
- `requirements.txt` – pydantic, openpyxl, Pillow, pypdf, waitress (kein fastapi, kein Sprachmodell).

## Starten
Lokal (Windows, im Projektordner):

    python -m pip install -r schnellcheck\requirements.txt
    python -m schnellcheck

Dann `http://127.0.0.1:8100` öffnen. Oder einfach `scripts\start_schnellcheck_windows.bat`.

Im Internet (Server in der EU, hinter HTTPS-Proxy wie Caddy oder nginx):

    waitress-serve --host 127.0.0.1 --port 8100 schnellcheck.web:app

Einstellungen über Umgebungsvariablen:
- `SCHNELLCHECK_SAAS_URL` – Link für den Knopf „Vollversion ansehen“ (leer: „Bald verfügbar“).
- `SCHNELLCHECK_PARALLEL` – gleichzeitige Prüfungen (Standard 4).

## Was der Besucher angibt
1. Zahlungsjahr (nur Jahre mit Schwelle und Abgabesatz im Register) und was das Unternehmen macht.
2. Zweck der Aufträge (eigene Werbung, für Kunden, Veranstaltung, privat) und ob eine Katalog-Tätigkeit nach
   KSVG § 24 Abs. 1 vorliegt (Ja / Nein / Weiß nicht). Bei Veranstaltungen: Anzahl und Einnahmeabsicht.
3. Je Leistung: Leistung aus der Liste „Tätigkeitsabgrenzung“ (oder „Andere Leistung“), Auftragnehmer (Name bleibt im
   Browser, übertragen wird nur eine Nummer), Rechtsform, gezahlter Nettobetrag, direkt gezahlt ja/unklar.
4. Ob alle Aufträge des Jahres erfasst sind, und Bestätigung der Beträge.

## Ergebnis
- „Voraussichtlich abgabepflichtig“ / „Voraussichtlich nicht abgabepflichtig“ nur bei den Kernklassen
  Abgabepflichtig (Vorschlag) / Nicht abgabepflichtig (Vorschlag).
- Alles andere (Grenzfall, Rückfrage nötig, Nicht abgedeckt, Prüfung fehlgeschlagen) → „Weitere Prüfung nötig“.
- Die Kernklasse, Begründung, Werte (Bemessungsgrundlage, Satz, Abgabe, Jahresgrenze), Einordnung je Leistung,
  offene Punkte und Fundstellen werden immer angezeigt; KSK-Hinweise als „Auslegung der KSK (kein Gesetz)“.
- „Weiß nicht“, „nur ein Teil der Aufträge“, unklarer Zahlungsweg oder „Andere Leistung“ führen nie zu einer sicheren Aussage.

## Datenschutz
Keine Anmeldung, keine Cookies, keine externen Dienste, kein Zugriffsprotokoll beim lokalen Start. Angaben werden nur für
die Prüfung im Speicher gehalten und nicht gespeichert. Für den Betrieb im Internet: Impressum und Datenschutzerklärung
ergänzen und im Webserver/Proxy keine Anfrageinhalte protokollieren.

## Tests
    python -m unittest discover -s tests/schnellcheck -t .

Läuft auch in `python scripts/pruefe_alles.py` mit (muss „ALLES GRÜN“ melden).
