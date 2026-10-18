# KSK-Schnellcheck

Kostenlose Ersteinschätzung zur Künstlersozialabgabe für Unternehmen – **ohne KI, ohne Anmeldung**, mit Berechnung und Quelle.
Gedacht als Einstieg in die Vollversion (Rechnungen hochladen, gespeicherte Fälle, ausführlicher Prüfbericht).

**So funktioniert es:** Der Besucher wählt Zahlungsjahr, Zweck der Aufträge und seine Leistungen aus festen Listen und trägt die
gezahlten Beträge ein. Bewertet wird mit **demselben Regelkern wie im SaaS** (`kern/rechnen.py` + unabhängige Gegenrechnung,
Werte aus `regelwerk/Regelkatalog_24_KSVG_Entwurf.xlsx`). Fehlen Angaben oder ist der Fall nicht eindeutig, zeigt der Schnellcheck
„Weitere Prüfung nötig“ statt einer Scheinsicherheit.

| Kostenloser Schnellcheck | Vollversion (SaaS) |
|---|---|
| Angaben selbst eingeben | Rechnungen und Dokumente hochladen |
| Geführte Standardfälle | Individuelle Rückfragen und Erklärungen |
| Einzelne Prüfung | Mehrere Unterlagen und gespeicherte Fälle |
| Kurzes Ergebnis mit Quelle | Ausführlicher, nachvollziehbarer Prüfbericht |

**Starten (Windows):** Doppelklick auf `scripts\start_schnellcheck_windows.bat`, dann im Browser `http://127.0.0.1:8100`.
Details, Betrieb im Internet und Tests: [schnellcheck/README.md](schnellcheck/README.md).

Alles bleibt „Entwurf – vom Steuerberater zu prüfen“. Der Schnellcheck ist keine Rechts- oder Steuerberatung.

---

# KSK-Assistent

Prinzip: **Das System macht Vorschläge, der Steuerberater entscheidet.**

## Inhalt
- `quellen/` – öffentliche Quellen (KSVG, Verordnungen, KSK-Infos, Checklisten, Urteile) mit `index.csv` und `archivnachweise.csv`. Archivdatum ist nicht der Stand; Entwürfe sind als Entwurf gekennzeichnet.
- `regelwerk/`
  - `Regelkatalog_24_KSVG_Entwurf.xlsx` – 236 Regeln mit Fundstelle (Blätter: Regeln, Schwellen nach Jahr, Offene Punkte, Tätigkeitskatalog, Abgabesätze, Pauschalen nach Jahr)
  - `Testfaelle_BSG_Urteile.xlsx` – 329 erfundene Testfälle mit erwartetem Ergebnis
  - `Kontrollkatalog_Entwurf.xlsx` – 48 Risiken, Kontrollen und Soll-Tests aus dem externen Prüfbericht mit Stand im Repo
  - `Pruefliste_Steuerberater_Entwurf.xlsx` – alle 236 Regeln in drei Prioritäten mit Spalten für Entscheidung, Begründung, Name und Datum (zum Abarbeiten durch den Steuerberater)
  - `Statusmodell_Entwurf.md`, `Quellenpolitik_Entwurf.md`, `Chatbot_Systemanweisung_Entwurf.md`, `Chatbot_Musterdialoge_Entwurf.md`
  - `Fragenkatalog_Chatbot_Entwurf.xlsx` – 191 typische Fragen, jeweils mit Regel-IDs; Lücken sind markiert
- `aufgaben/` – Prompts für Claude Code (Recherche) und Abdeckungsübersicht (`Chatbot_Abdeckung.md`)
- `tests/pruefe_regelwerk.py` – formale Prüfung (IDs, Pflichtfelder, Quelldateien, Regelverweise). Aufruf: `python tests/pruefe_regelwerk.py`

## Pflege und Updates
- `aufgaben/PFLEGE_Update_Anleitung.md` – Schritt für Schritt: neues Jahr, geänderter Wert, ersetzte oder neue Regel, neue Quelle. `CLAUDE.md` – Grundregeln für Claude in jeder Sitzung.

## Regeln für dieses Repository
- Nur öffentliche Quellen und erfundene Testdaten. **Keine Kundendaten, Rechnungen oder Verträge.**
- Jede Aussage braucht eine Fundstelle; was nicht belegt ist, steht als "nicht belegt" da.
- Das Jahr ist Pflichtangabe (Rechtslage bis 31.12.2022 = Fassung A, ab 01.01.2023 = Fassung B).
- Alle Inhalte sind „Entwurf – vom Steuerberater zu prüfen“, bis ein Berufsträger sie bestätigt hat.
- Ergebnisklassen: Abgabepflichtig (Vorschlag) / Nicht abgabepflichtig (Vorschlag) / Grenzfall → Steuerberater entscheidet / Rückfrage nötig / Nicht abgedeckt (Quelle fehlt).
- Verwaltungspraxis der KSK/DRV (Infos, Checklisten) ist als „Auslegung der KSK, kein Gesetz“ gekennzeichnet.

## Regelkern (Entwurf)
- `kern/` – deterministischer Rechenkern v0 mit 18 Tests (`python tests/test_kern.py`); Details in `kern/README.md`.

## Vollversion: Rechnungen prüfen (ohne KI)

**Dokumente hochladen → Angaben prüfen → Ergebnis.** PDF, Foto, Excel und CSV werden auf dem eigenen Server mit Python
gelesen; bewertet wird mit demselben Regelkern und derselben Gegenrechnung wie im Schnellcheck. Kein Sprachmodell, kein
Chat (entfernt am 17.10.2026; der frühere Stand steht im Git-Verlauf). Anleitung, Grenzen und Testbefehle:
[app/DOKUMENTE.md](app/DOKUMENTE.md).


## Direkt in GitHub Codespaces testen

Codespaces startet automatisch die Dokumentenprüfung auf Port 8000. Dort können PDFs, Fotos, XLSX und CSV hochgeladen werden. Port 8100 ist nur das optionale manuelle Formular und wird nicht automatisch geöffnet.

Bei einem bestehenden Codespace auf dem PR-Zweig einmal `git pull --ff-only` ausführen und über die Befehlspalette (F1) **Codespaces: Rebuild Container** wählen. Neue Codespaces übernehmen die Konfiguration direkt. Beim erneuten Verbinden bleibt ein laufender Server bestehen. Falls der Browser den neuen Tab blockiert: unten **Ports**, bei **8000** auf das Globus-Symbol klicken.
