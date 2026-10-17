# app/ – Vollversion „Rechnungen prüfen“ (ohne KI)

Seit 17.10.2026 läuft die App **ohne Sprachmodell**: kein Mistral, kein Chat, kein Netz zur Laufzeit. Der frühere
KSK-Chat (Mistral, Quellenindex, Textbausteine, Antwort-Kontrolle) ist entfernt; sein letzter Stand steht im Git-Verlauf
(Commit vor „Ohne KI“). Bedienung, Grenzen und Tests: [DOKUMENTE.md](DOKUMENTE.md).

## Start

```text
python -m pip install -r app/requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Unter Windows: Doppelklick auf `scripts\start_windows.bat`. Für Fotos und Scans: Tesseract (Sprachpaket deu) und Poppler.

## Ablauf und Module

| Schritt | Modul |
|---|---|
| Webserver, Upload, Bestätigung (Ticket) | `dokument_app.py` (Start über `main.py`) |
| Dokument lesen: PDF-Text, OCR, Excel, CSV; Positionskandidaten | `dokument_lesen.py`, Grenzen in `dokument_config.json` |
| Leistung erkennen (Blatt „Tätigkeitsabgrenzung“) | `taetigkeiten.py`, `taetigkeit_erkennung.json` |
| Auftraggeber einordnen (Zweck, Katalog-Tätigkeit) | `einordnung.py` |
| Fehlende Angaben | `dokument_pruefung.py`, `pflichtangaben.py` |
| Regelkern aufrufen und gegenrechnen | `bewertung.py` → `kern/rechnen.py`, `gegenrechnung.py` → `verifier/` |
| Ergebnisklassen | `ergebnisklassen.py` |
| Quellen und Fundstellen aus dem Regelkatalog | `quellen.py` |

`zuordnung.py`, `fallstand.py`, `rechtsform_erkennung.py` und die `*_begriffe.json` sind feste Wortregeln aus der
Chat-Zeit, die die Einordnung und die Pflichtangaben weiter nutzen. Kommentare darin nennen frühere Testläufe mit Mistral
als Herkunft einer Regel; das ist Nachweis, kein Aufruf.

## Tests

```text
python -m pip install -r app/requirements-test.txt
python scripts/pruefe_alles.py
```

Der Wächter `tests/app/test_ohne_ki.py` stellt sicher, dass weder ein Sprachmodell noch ein Netzmodul (httpx, requests,
socket …) in `app/`, `kern/`, `verifier/` oder `schnellcheck/` zurückkommt.
