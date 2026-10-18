# Rechnungen prüfen (Dokumentenmodus)

Die Vollversion arbeitet **ohne KI** (Umbau 17.10.2026): kein Sprachmodell, kein Chat, kein Netz zur Laufzeit. Der Nutzer
lädt Rechnungen hoch (PDF, Foto, Excel, CSV), Python liest sie, der Nutzer prüft und ergänzt die Angaben, und der
Regelkern entscheidet mit unabhängiger Gegenrechnung. Gelesen wird mit pypdf (Text-PDF), Tesseract (Fotos und Scans),
openpyxl (Excel) und csv; Positionen erkennt die Regel-Erkennung in `app/dokument_lesen.py`, die Leistung die feste
Erkennung aus dem Blatt „Tätigkeitsabgrenzung“ (`app/taetigkeiten.py`).

## Start

Python 3.11 oder neuer:

```text
python -m pip install -r app/requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Danach im Browser `http://localhost:8000` öffnen (die alte Adresse `/rechnungen` funktioniert weiter). Unter Windows kann weiterhin `scripts\start_windows.bat` verwendet werden. Unter Codespaces: `bash scripts/start_codespace.sh`.

Text-PDFs, XLSX und UTF-8-CSV funktionieren mit den Python-Paketen. Für Fotos und gescannte PDF-Seiten müssen **Tesseract OCR** (deutsche und englische Sprachdaten) und **Poppler** (`pdftoppm`) im PATH vorhanden sein. Die Codespace-Konfiguration installiert sie bei der Erstellung. Bestehende Codespaces dafür neu bauen. Fehlt OCR, gibt die Oberfläche einen konkreten Hinweis; es wird kein Cloud-Dienst als Ersatz aufgerufen. Alte XLS-Dateien vorher als XLSX speichern.

## Ablauf

1. Eine oder mehrere Dateien eines Auftraggebers hochladen.
2. Gelesenen Text am Original kontrollieren. Automatische Positionen sind nur Kandidaten; sie können bearbeitet, entfernt und ergänzt werden.
3. Zahlungsjahr, Tätigkeit und Auftragszweck des Auftraggebers ergänzen. Die vollständige Liste der Katalogtätigkeiten samt Voraussetzungen wird aus der Regel-Excel angezeigt. Keine automatische Branchenentscheidung allein aus „Bäckerei“ oder „Agentur“.
4. Pro Position tatsächlich gezahlten Betrag **ohne gesondert ausgewiesene Umsatzsteuer**, Rechtsform, Auftragnehmer-Nummer und Vertrags-/Zahlungsweg bestätigen. Gleiche Auftragnehmer müssen auch über Dokumentgrenzen dieselbe Nummer erhalten. Das ist für Nebenleistungen wichtig.
5. Bei Eigenwerbung und Generalklausel vollständige relevante Jahresdaten bestätigen. Einzelrechnungen führen sonst zu Rückfragen, nicht zu einer abschließenden Jahresbefreiung.
6. Bestätigung zeigt jeden Betrag, die Tätigkeitszuordnung und die Voraussetzungen/Abgrenzungen aus der Excel. Treffen diese nicht zu, Angaben korrigieren bzw. fachlich klären. Erst „Ja, prüfen“ führt die Rechnung aus.
7. Ergebnis je Position, Gesamtergebnis, Quellen und unabhängige Gegenrechnung ansehen; bei Bedarf über den Browser drucken/als PDF speichern.

Ein positionsbezogenes „zählt“ ist keine isolierte Abgabepflicht. Die Jahresprüfung erfolgt gemeinsam. Unbekannte/mehrdeutige Tätigkeiten und unklare Zahlungswege bleiben offen. Keine neue Rundungsregel: liefert der Kern keinen gerundeten Betrag, zeigt die Oberfläche keinen erfundenen Betrag.

## Grenzen und Datenfluss

- Automatische Erkennung ist bewusst konservativ: einfache Textzeilen mit einem Betrag am Ende; Tabellen mit eindeutiger Beschreibungs- und Betragsspalte. Beliebige Rechnungslayouts, Handschrift, gemischte Bild-/Textseiten und schlecht lesbare Fotos werden nicht zuverlässig vollständig erkannt. Alle Positionen müssen am Original geprüft werden.
- Mengen, Einzelpreise und Gesamtpreise werden nicht geraten oder zusammenmultipliziert. Summenzeilen werden nicht als Position übernommen. Formeln werden nicht ausgeführt; solche Tabellenzeilen müssen ergänzt werden. Fremdwährungen werden nicht umgerechnet.
- Nur ein Zahlungsjahr und ein Auftraggeber je Prüfung. Mehrere Jahre, Rechtsformwechsel, Gutschriften/negative Beträge, noch offene Zahlungen und komplexe Vertragsketten müssen fachlich getrennt geklärt werden.
- Originaldateien werden im temporären Ordner eines Arbeitsprozesses gelesen und danach gelöscht. Keine Ablage in Git, Quellenindex oder Fallprotokoll. Die Oberfläche hält Angaben nur im geöffneten Tab, ohne Local Storage. Ein Neuladen verwirft sie.
- Zeit-, Größen-, Seiten-, ZIP-, Pixel- und Positionsgrenzen stehen in `app/dokument_config.json`. Linux begrenzt zusätzlich Arbeitsspeicher/CPU des Lesers; Windows hat hier nur das Wanduhrlimit und Formatgrenzen. Dies ist keine vollständige Betriebssystem-Isolation gegen bösartige Dateien.
- Bestätigungen sind zeitlich begrenzt und kryptografisch an den konkreten Fall gebunden. Eine Datenänderung verwirft sie. Bei mehreren Serverprozessen muss `DOKUMENT_TICKET_SCHLUESSEL` als gemeinsames starkes Geheimnis in der Umgebung gesetzt werden; niemals im Repo speichern.
- Die bestehende Anwendung ist weiterhin ein Entwicklungsprototyp: keine Benutzeranmeldung, Mandantenverwaltung oder dauerhafte Fallakte. Vor echtem SaaS-Betrieb sind diese Funktionen und die bereits dokumentierten fachlichen/rechtlichen Freigaben nötig. Bis dahin nur erfundene Belege verwenden.

## Prüfung

Für die Tests zusätzlich `python -m pip install -r app/requirements-test.txt`.

```text
python scripts/pruefe_alles.py
python tests/app/livetest_dokumente.py
python tests/app/playwright_dokumente.py
```

Die reguläre Suite enthält Dokumenttests mit 180 erzeugten PDF-/XLSX-/CSV-Fällen sowie Gegenbeispielen für Bestätigung, Manipulation, Mischpositionen, Jahresgrenzen, unbekannte Tätigkeiten, Dateifehler und OCR. Der Live-Test startet einen echten HTTP-Server und prüft weitere 60 erzeugte Belege. Der Browsertest benötigt Playwright und Chromium; er läuft zusätzlich im GitHub-Workflow. OCR-Tests melden ausdrücklich „übersprungen“, wenn die Systemprogramme fehlen.

Alle fachlichen Sollwerte folgen dem vorhandenen Entwurfsregelwerk. Erfolgreiche Tests ersetzen keine Freigabe durch einen Steuerberater und keinen Lasttest für viele gleichzeitige Nutzer.


### Automatische Vorbelegung (18.10.2026)

Text-PDFs werden unter Erhalt ihrer Zeilenanordnung gelesen. Eindeutige Positionen mit Beschreibung und Betrag erscheinen direkt in der Tabelle. Beschriftete Rechnungsempfänger bzw. Auftraggeber werden zusätzlich im Auftraggeberfeld vorgeschlagen, mit sichtbarem Textbeleg. Bereits korrigierte Felder werden nicht überschrieben. Bei verschiedenen Empfängern ist die gemeinsame Zuordnung zu klären.

Das ist keine allgemeine Erkennung sämtlicher Rechnungsformate: Mehrdeutige Tabellen, mehrere Preisspalten und fehlende Beschriftungen bleiben offen. Rechnungsdatum und Zahlungsziel ersetzen keinen Zahlungsnachweis. Zahlungsjahr, tatsächliche Zahlung, Jahresvollständigkeit und nicht belegte Rechtsform müssen weiterhin ergänzt bzw. bestätigt werden.
