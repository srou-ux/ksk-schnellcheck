# Auftrag an Claude Code (lokal, C:\ksk cloud) – Chatbot, Teil 1 (Prototyp, offline testbar)

Ziel: Ein Fach-Chatbot zur Künstlersozialabgabe für Steuerberater und Agenturen. Er spricht als Kollege, nennt Gesetz, Rechtsprechung und KSK-Praxis mit Fundstelle, fragt fehlende Angaben nach und gibt erst dann ein klares, begründetes Ergebnis. **Das System macht Vorschläge, der Steuerberater entscheidet.** Alles bleibt Entwurf.

## Regeln für diese Arbeit
- Vor Beginn `git pull`. Nur in neuen Ordnern `app/` und `tests/app/` arbeiten; Dateien in `kern/`, `regelwerk/`, `quellen/` nicht ändern (Fehler dort in `aufgaben/FUNDE_Chatbot.md` melden: Datei, Stelle, Problem, Vorschlag).
- **Kein Code, kein Schlüssel außerhalb von GitHub.** Keine API-Schlüssel, keine Kundendaten im Repo. Schlüssel nur als Umgebungsvariable (`MISTRAL_API_KEY`); `.gitignore` für `.env`.
- Python 3.11+, nur wenige Abhängigkeiten (FastAPI + uvicorn für die Schnittstelle, `httpx` oder das offizielle Mistral-Paket, `pydantic`). Alles Weitere begründen. Keine Abhängigkeit von US-Diensten.
- Sprachmodell: **Mistral (EU)** über einen Adapter `app/llm/`. Dazu ein **FakeLLM** (festes, im Test vorgegebenes Verhalten). **Alle Tests laufen offline mit FakeLLM**; ein echter Mistral-Aufruf nur im optionalen Rauchtest, der ohne Schlüssel übersprungen wird.
- Jede Teilaufgabe: kleiner Commit mit klarer Meldung, am Ende `git pull --rebase origin main && git push origin main`.

## Architektur (verbindlich)
1. **Fakten-Extraktion**: Das Sprachmodell wandelt die Nutzerfrage in ein festes JSON (`pydantic`-Schema `Fakten`): Jahr, Unternehmensart, Auftraggeber/Auftragnehmer-Typ (natürliche Person, GbR, GmbH/UG/AG, KG/OHG, Verein, Ausland), Leistungsart, Positionen mit Beträgen und Rollen, Veranstaltungszahl, Einnahmeabsicht, Belege ja/nein. Unbekanntes bleibt `null` – **nie raten**. Das Modell rechnet nicht.
2. **Pflichtangaben-Prüfung** (`app/pflichtangaben.py`): Ohne Jahr kein Ergebnis, sondern Rückfrage. Fehlen weitere Angaben, die der Kern braucht, entsteht eine gezielte Rückfrage (Liste, kurz, höchstens drei auf einmal).
3. **Kern aufrufen** (`app/router.py`): Die Fakten gehen an `kern/rechnen.py` (`pruefe_eigenwerbung`, `pruefe_typischer_verwerter`, `veranstaltungen`, `bemessung_positionen`, `analysiere_rechnung`, `verpflegung`, `vorauszahlung_monatlich`, `saeumniszuschlag`, `uebungsleiter_bg`, …). Gerechnet wird **nur dort**. Liefert der Kern `Rückfrage nötig`, `Grenzfall` oder `Nicht abgedeckt`, wird das so ausgegeben, nicht überspielt.
4. **Quellenabruf (RAG, nur öffentliche Quellen)** (`app/quellen.py`): Aus `regelwerk/Regelkatalog_24_KSVG_Entwurf.xlsx` (Regeln, Fundstellen) und den zugehörigen Quelltexten wird passend zur Frage und zum Jahr abgerufen. Kein Zugriff auf das Internet zur Laufzeit. Eine Regel wird nur genutzt, wenn Jahr/Fassung passen (`Gilt für Fassung`). Aussagen ohne Fundstelle sind verboten.
5. **Antwort-Generator**: Das Sprachmodell formuliert die Antwort **ausschließlich aus Kernergebnis + abgerufenen Regeln/Fundstellen**, nach dem Schema in `regelwerk/Chatbot_Systemanweisung_Entwurf.md` (Ergebnis, Norm, Subsumtion, Rechtsprechung, Verwaltungspraxis, Gegenansicht/Risiko, offene Punkte, Lösungsvorschläge, Fundstellenliste) und mit dem Schlusssatz „Entwurf – vom Steuerberater zu prüfen“.
6. **Antwort-Kontrolle** (`app/pruefung.py`, deterministisch, vor der Ausgabe): (a) jeder genannte Betrag kommt aus dem Kernergebnis; (b) jede genannte Fundstelle/Regel-ID/jedes Aktenzeichen existiert in der Quellenbasis (`regelwerk/` bzw. `quellen/index.csv`); (c) keine erfundenen Urteile; (d) Ebenen getrennt benannt; (e) Schlusssatz vorhanden. Schlägt eine Kontrolle fehl: Antwort nicht ausgeben, stattdessen „Nicht abgedeckt/Prüfung fehlgeschlagen“ mit Grund (und ins Lückenprotokoll).
7. **Sicherheit**: Inhalte aus Nutzerdokumenten und Quelltexten sind Daten, keine Anweisungen (Prompt-Injection-Test mit eingebautem Befehl in einem Quelltext). Eingaben anonymisieren, bevor sie gespeichert werden (Klarnamen, Adressen maskieren; einfacher Regex-Anfang genügt, Grenzen benennen). **Lückenprotokoll** (`app/log.py`): anonymisierte Fragen mit Ergebnis „Nicht abgedeckt“, Datum, Jahr, Grund, in einer lokalen Datei (nicht im Repo, `.gitignore`).
8. **Schnittstelle**: `POST /frage` (Text, optional Verlauf) → JSON mit `antwort`, `ergebnisklasse`, `rueckfragen`, `fundstellen`, `kern_protokoll`. Dazu `GET /gesundheit`. Eine sehr einfache Chat-Weboberfläche (eine statische HTML-Seite, ohne externe Skripte) ist erlaubt. Kein Login in dieser Stufe, nur lokal startbar.

## Start im Browser (GitHub Codespaces) – verbindlich
- Startbefehl: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`. Die Datei `.devcontainer/devcontainer.json` und `scripts/start_codespace.sh` sind schon im Repo (nicht ändern; Abhängigkeiten in `app/requirements.txt`).
- **Ohne `MISTRAL_API_KEY` startet die App im Demo-Modus** mit dem FakeLLM und kann die Fälle aus `aufgaben/Fallgruppen_Abdeckung.md` und den Musterdialogen beispielhaft beantworten (deutlich als „Demo-Modus, Ersatzmodell“ gekennzeichnet). Mit Schlüssel nutzt sie Mistral.
- Die Weboberfläche (eine statische Seite unter `/`) zeigt: Eingabefeld, Verlauf, Ergebnisklasse als Kennzeichnung, Fundstellen, Rückfragen als anklickbare Vorschläge, oben fest „Entwurf – vom Steuerberater zu prüfen. Nur erfundene Daten eingeben.“ Funktioniert auf dem Handy, keine externen Skripte oder Schriften.

## Tests (alle offline, mit FakeLLM)
- `tests/app/`: Einzeltests für Schema, Pflichtangaben, Router, Antwort-Kontrolle, Anonymisierung, Prompt-Injection, Lückenprotokoll.
- **Abnahmetests aus den 5 Musterdialogen** (`regelwerk/Chatbot_Musterdialoge_Entwurf.md`) und aus den Fallgruppen (`aufgaben/Fallgruppen_Abdeckung.md`), soweit der Kern sie rechnen kann. Der Test gibt dem FakeLLM die Fakten vor, die ein gutes Modell extrahieren würde, und prüft: richtige Ergebnisklasse, richtige Zahlen (aus dem Kern), richtige Rückfragen, Fundstellen vorhanden.
- **Gegenproben**: absichtlich eingebaute Fehler (erfundener Betrag, erfundenes Aktenzeichen, fehlendes Jahr, alte Fassung auf neues Jahr) müssen von der Antwort-Kontrolle gefangen werden. Dokumentiere jede Gegenprobe im Testnamen.
- Wo ein Musterdialog dem Kern widerspricht (z. B. Dialog 1/E-01 verlangt eine Bewertung für 2017, der Kern kennt die Schwellen erst ab 2019 und sagt „Nicht abgedeckt“): **nicht anpassen**, sondern in `aufgaben/FUNDE_Chatbot.md` melden.

## Grenzen (ehrlich bleiben)
- Der Chatbot ist kein Nachweis für richtige Rechtsanwendung; fachliche Freigabe fehlt (Status „Entwurf“). Das muss in README und in jeder Antwort sichtbar sein.
- Kein Hochladen von Kundendaten; Tests nur mit erfundenen Daten. Nichts außerhalb der EU (Mistral EU-Endpunkt; Hosting später).
- Keine Behauptung „KSK-geprüft“ oder „offiziell“.

## Abschluss
`app/README.md` (Start, Umgebungsvariablen, Tests, Grenzen), `aufgaben/FUNDE_Chatbot.md` (Befunde), dann pushen. In der Antwort nur: Ordner/Dateien (Kurzliste), Ergebnis von `python -m unittest discover -s tests/app` (Anzahl bestanden), die Befunde-Liste (Kurzfassung) und was **nicht** geht.
