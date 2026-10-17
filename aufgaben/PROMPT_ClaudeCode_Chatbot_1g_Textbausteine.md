# Auftrag Chatbot Teil 1g: Mischform – feste Textbausteine statt freiem Modelltext (Entwurf – vom Steuerberater zu prüfen)

Lies zuerst `CLAUDE.md`, `aufgaben/PFLEGE_Update_Anleitung.md`, `aufgaben/Arbeitsstand.md`, `aufgaben/FUNDE_Chatbot.md`, `aufgaben/SYSTEMBESCHREIBUNG_fuer_KI.md`. Arbeite **nur in `app/` und `tests/app/`**. Fehler anderswo melde in `aufgaben/FUNDE_Chatbot.md`.

## Warum
Der Mistral-Lauf nach dem Nachtrag (`aufgaben/audit/ergebnisse_mistral_small_nachtrag.md`) zeigt: 7 von 9 Antworten wurden blockiert, weil das Modell im Antwort-Text Zahlwörter, Paragrafen oder Verwaltungspraxis „dazuschreibt". Die Kontrolle wirkt, aber so entsteht keine brauchbare Antwort. Entscheidung des Auftraggebers (09.10.2026): **Mischform**. Rechtsaussagen kommen nur aus festen Textbausteinen im Regelkatalog (später vom Berufsträger freigegeben). Das Modell darf höchstens den Einzelfall beschreiben, ohne Rechtsaussage. Fällt dieser Satz durch die Kontrolle, entfällt nur dieser Satz, nie die ganze Antwort.

## Bereits erledigt (nicht ändern)
- Regelkatalog hat ein neues Blatt **„Textbausteine"** (16 Zeilen TB-01 bis TB-16). Spalten: Baustein-ID | Reihenfolge | Benötigt (Platzhalter, mit `;`) | Nicht, wenn vorhanden (Platzhalter) | Nur bei Ergebnisklasse (leer = immer) | Text mit `{PLATZHALTERN}` | Gültig von (Jahr) | Gültig bis (Jahr) | Prüfstatus | Bemerkung. Die Texte entsprechen genau dem, was bisher fest in `FakeLLM.formuliere_antwort` stand.
- `aufgaben/audit/abnahme_teil1g.py` (Ausgangszustand **15 Lücken**, Ziel 0). Nicht verändern.

## A. Bausteine aus dem Regelkatalog lesen (kein Text im Programm)
1. Neuer kleiner Leser (z. B. `app/textbausteine.py`): liest das Blatt „Textbausteine" mit `openpyxl` aus `regelwerk/Regelkatalog_24_KSVG_Entwurf.xlsx` (nicht über `kern/parameter.json`, das ist Sache des Kerns; der Pfad wird wie beim Kern aufgelöst). Beim Programmstart einmal laden und prüfen: ID eindeutig, Text nicht leer, Platzhalternamen in „Benötigt"/„Nicht, wenn" bekannt (`app/baustein.py::PLATZHALTER_BESCHREIBUNG` bzw. die dynamischen `_n`-Namen). Fehler → klare Meldung beim Start, nicht erst bei der ersten Frage.
2. **Auswahl** je Antwort: Baustein gilt, wenn alle „Benötigt"-Platzhalter in `erzeuge_platzhalter(kontext)` vorhanden sind, kein „Nicht, wenn"-Platzhalter vorhanden ist, die Ergebnisklasse passt (falls gesetzt) und das Jahr der Anfrage in „Gültig von/bis" liegt (leer = unbegrenzt). Sortiert nach „Reihenfolge", bei Gleichstand nach ID. Danach `RUECKFRAGE_n` und `HINWEIS_n` wie bisher (feste Systemtexte) hinten anhängen.
3. Es gibt **keinen** Bausteintext mehr im Python-Code. Die bisherigen Texte in `FakeLLM.formuliere_antwort` fallen weg (siehe C). Texte der Rückfrage-Bausteine in `app/pflichtangaben.py`/`_rueckfrage_antwort` dürfen vorerst bleiben (Folgeauftrag), Befund dazu in `FUNDE_Chatbot.md`.
4. Passt kein einziger Baustein (außer TB-16), schreibe ins Lückenprotokoll „Baustein fehlt" (anonymisiert) und gib trotzdem Ergebnisklasse + Schlusssatz aus. Nie einen Text erfinden.

## B. Modell nur noch als „Fallbeschreibung"
1. `LLM`-Schnittstelle (`app/llm/base.py`): neue Methode `beschreibe_fall(kontext) -> str`. **Eine** kurze Beschreibung des Einzelfalls in einem Satz, nur mit Platzhaltern aus `erzeuge_platzhalter` (z. B. `{JAHR}`), ohne Zahlen, Normen, Ergebnisse, Wertungen, Links. Der Prompt sagt das ausdrücklich; Werte bekommt das Modell nie (wie bisher).
2. Router `_ausgeben`: Körper = Bausteine (A). Danach genau ein Aufruf `llm.beschreibe_fall`. Der Text geht durch **dieselbe** `pruefe_rohtext`-Kontrolle wie bisher (alle Nachträge). Verstößt er oder wirft das Modell `LLMFehlgeschlagen`/irgendeinen Fehler: **Fallbeschreibung weglassen**, Grund anonymisiert ins Lückenprotokoll, Antwort sonst unverändert. Nie `Pruefung fehlgeschlagen` wegen der Beschreibung.
3. Position der Beschreibung: direkt unter der Ergebniszeile, vor den Bausteinen. Danach Ebenen-Abschnitt, Schlusssatz wie bisher. `app/pruefung.py` (zweites Netz) prüft den **fertigen** Text weiter; schlägt es an, bleibt es bei `Pruefung fehlgeschlagen` (dann ist das ein echter Befund – melden, nicht abschalten).
4. `formuliere_antwort` wird nicht mehr aufgerufen. Entfernen oder als veraltet markieren (Tests, die es brauchen, anpassen; Begründung in `FUNDE_Chatbot.md`).

## C. Adapter
- `FakeLLM.beschreibe_fall`: liefert einen festen harmlosen Satz mit Platzhalter (z. B. „Es geht um eine Anfrage für das Jahr {JAHR}."), nie Zahlen.
- `app/llm/mistral.py`: `beschreibe_fall` mit eigenem knappen Prompt, `max_tokens` klein, `temperature 0`, `top_p 1`, dieselbe Robustheit wie bisher (Blockinhalt, Timeout, Fehler → `LLMFehlgeschlagen`). Das Modell soll **nicht** mehr den ganzen Antworttext schreiben; das spart auch Zeit.
- Mistral-Prompt für die Extraktion von Fakten bleibt unverändert, außer du findest einen echten Fehler (dann `FUNDE_Chatbot.md`).

## D. Tests (`tests/app/test_teil1g.py`) und CI
- Jede Zeile von `abnahme_teil1g.py` als Test, dazu: Baustein mit „Gültig bis" vor dem Jahr wird nicht verwendet (Test mit temporärer Kopie der Arbeitsmappe oder injizierter Tabelle); fehlende/doppelte ID beim Laden → Fehler; Bausteinauswahl-Regeln einzeln; Fallbeschreibung mit Link/Paragraf/Ziffer/Ergebnisaussage/HTML wird weggelassen, Antwort bleibt; Modellausfall bei der Beschreibung; Mischfall mit 4 Positionen (4.300,00 € / 215,00 €).
- Neuer blockierender CI-Job `abnahme-1g` in `.github/workflows/pruefen.yml` (wie `abnahme-1f-nachtrag`, `ubuntu-24.04`, Python 3.11). Die Workflow-Datei darfst du dafür ändern, sonst nichts außerhalb von `app/`/`tests/app/`.
- Bestehende Tests anpassen, die den alten Körpertext oder `formuliere_antwort` voraussetzen. Keine Prüfung abschwächen; was du ändern musst, in `FUNDE_Chatbot.md` begründen.

## E. Nicht ändern
Kern, Verifier, Excel-Inhalte außer dem Blatt „Textbausteine" (das hast du nur zu **lesen**), `aufgaben/audit/*`, Bestätigungsablauf, Ergebnisklassen, Rückfragen-Logik aus 1f, UI.

## F. Abschluss
`python scripts/pruefe_alles.py` → ALLES GRÜN; `python aufgaben/audit/abnahme_teil1g.py` → 0 Lücken; zusätzlich `abnahme_teil1f.py`, `abnahme_teil1f_nachtrag.py`, `gegenproben_teil1d_runde3.py` weiter 0. `git pull --rebase`, push, prüfen dass die neuen Dateien in `origin/main` liegen. `aufgaben/Arbeitsstand.md` aktualisieren, Projekt „ksk" (`claude/ksk-assistent-arbeitsstand.md`). Kurzbericht: geänderte Dateien, Testzahl, Abnahmeergebnis, Befunde, was nicht geht. Nichts schönreden.
