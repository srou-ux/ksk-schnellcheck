# KSK-Chatbot -- Prototyp (Chatbot, Teil 1)

Status: **Entwurf -- vom Steuerberater zu prüfen. Nicht produktiv.** Kein Ersatz für
Rechtsberatung, keine Behauptung "KSK-geprüft" oder "offiziell".

Fach-Chatbot zur Künstlersozialabgabe für Steuerberater und Agenturen. Er spricht als
Kollege, nennt Gesetz, Rechtsprechung und KSK-Praxis mit Fundstelle, fragt fehlende Angaben
nach und gibt erst dann ein begründetes Ergebnis. **Das System macht Vorschläge, der
Steuerberater entscheidet.**

Diese Datei beschreibt NUR `app/` (und die zugehörigen Tests in `tests/app/`). Wichtige
Einschränkungen und Befunde zum Repo-Stand stehen in `aufgaben/FUNDE_Chatbot.md` -- bitte
vor dem Weiterbauen lesen. Seit Chatbot Teil 1b ist `kern/rechnen.py` Teil des Repos und
der Router ruft ihn echt auf (Befund 1 behoben). Seit Chatbot Teil 1d schreibt das
Sprachmodell nur noch Platzhalter-Text (`app/baustein.py`) und der Kern wird erst nach einer
ausdrücklichen Faktenbestätigung aufgerufen (`app/bestaetigung.py`) -- siehe die eigenen
Abschnitte unten.

## Start

**Windows (einfach):** Doppelklick auf `scripts\start_windows.bat` (oder in PowerShell
`powershell -ExecutionPolicy Bypass -File scripts\start_windows.ps1`). Das Skript legt beim ersten Start eine
Python-Umgebung an, installiert die Pakete, baut den Quellenindex und öffnet den Chat unter `http://localhost:8000/`.
Den Schlüssel des Sprachmodells vorher in derselben PowerShell setzen (`$env:MISTRAL_API_KEY = "…"`), nie in eine Datei.

```bash
pip install -r app/requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Dann `http://localhost:8000/` öffnen (in GitHub Codespaces: den von Codespaces
weitergeleiteten Port öffnen). Seit Chatbot Teil 1b liegen `.devcontainer/devcontainer.json`
und `scripts/start_codespace.sh` im Repo (Befund 2 behoben) -- ein neuer Codespace richtet
die Abhängigkeiten automatisch ein; der obige Befehl bleibt der verbindliche manuelle
Startbefehl aus `aufgaben/PROMPT_ClaudeCode_Chatbot_1.md`.

## Umgebungsvariablen

| Variable | Pflicht | Bedeutung |
|---|---|---|
| `MISTRAL_API_KEY` | nein | Ohne diese Variable läuft die App im **Demo-Modus** mit `FakeLLM` (siehe unten). Ist sie gesetzt, wird `app/llm/mistral.py` (Mistral, EU-Endpunkt) verwendet. |
| `MISTRAL_MODELL` | nein | anderes Mistral-Modell; Standard steht in `app/llm/anbieter.json` (seit 17.10.2026 `mistral-small-latest`, Entscheidung des Nutzers). |
| `LUECKENPROTOKOLL_PFAD` | nein | Pfad der lokalen Lückenprotokoll-Datei, Standard `app/_lokal/lueckenprotokoll.jsonl` (siehe `.gitignore` -- dieser Pfad wird nie hochgeladen). |

`MISTRAL_API_KEY` niemals im Repo speichern. Lokal z. B. per `export MISTRAL_API_KEY=...`
oder einer nicht versionierten `.env`-Datei setzen (`/app/.env` ist in `.gitignore`
ausdrücklich gesperrt).

## Sprachmodell (seit 17.10.2026 nur Mistral Small)

Entscheidung des Nutzers am 17.10.2026: Der Chat arbeitet **nur mit Mistral (EU)**, Standardmodell **Mistral Small**
(`app/llm/anbieter.json`, Feld `mistral_modell`). Large wird nicht mehr verwendet (Entscheidung des Nutzers am 17.10.2026;
Prüfstand bei der Entscheidung in `_hinweis_umstellung`). Begründung: im Vergleich mit Large gleich genau (Korpus jeder 10. Fall:
Small 166 richtig / 11 Rückfrage / 0 falsch, Large 168 / 9 / 0), etwa dreimal schneller und etwa ein Drittel der Kosten
(`aufgaben/audit/TESTPROTOKOLL.md`). Die Anschlüsse für andere Anbieter (OpenAI-kompatibel, Anthropic) sind entfernt; sie
stehen in der Git-Geschichte (bis Commit 7777681).

Das Modell liest nur die Fakten aus dem Text; rechnen, prüfen, nachfragen und antworten tut das System.

| Einstellung | Bedeutung |
|---|---|
| `MISTRAL_API_KEY` | Schlüssel (GitHub-/Codespaces-Secret oder Umgebungsvariable, nie im Repo) |
| `MISTRAL_MODELL` | optional, anderes Mistral-Modell (vorher das ganze Testarchiv laufen lassen) |

**Genaue Modellkennung (17.10.2026):** eingestellt ist der Name `mistral-small-latest`. Das ist ein Verweis von Mistral
auf die jeweils neueste Small-Fassung, keine feste Fassung. Welche Fassung tatsächlich geantwortet hat, meldet die
Mistral-API in jeder Antwort (Feld `model`); das System zeigt beides in `/gesundheit` und in der Weboberfläche an
(„Mistral (EU) – mistral-small-latest (antwortet als …)“), und die Testberichte (`aufgaben/audit/*_direkt_browser.md`)
nennen die Kennung im Kopf. Wechselt Mistral die Fassung hinter dem Verweis, zeigt sich das dort; dann zuerst das ganze
Testarchiv und den Korpus laufen lassen. Ob ein Modell für die Rechnungen zuverlässig genug ist, entscheiden die
Testfälle, nicht die Geschwindigkeit. Für eine feste Fassung den genauen Namen in `app/llm/anbieter.json` eintragen.
| `LLM_ANBIETER=demo` | ohne Sprachmodell (Demo-Modus), auch wenn ein Schlüssel gesetzt ist |

Vor einem Modellwechsel: den Korpus und das Testarchiv live laufen lassen (Workflow „Chatbot direkt“, Feld `modell`) und mit
`python scripts/vergleiche_ergebnisse.py ALT.csv NEU.csv` vergleichen. Ohne Modell prüft
`python aufgaben/audit/korpus/lauf_offline.py --stufe orakel|gestoert|demo` das System.

## Demo-Modus (ohne Schlüssel)

Ohne `MISTRAL_API_KEY` verwendet die App `app/llm/fake.py` (`FakeLLM`). Das ist **kein**
echtes Sprachmodell: Es erkennt Jahr, Beträge (`... €`) und grobe Rechtsform-Schlagworte per
einfacher Regex-Heuristik; alles andere bleibt `None`. Für unklare Fragen entstehen deshalb
häufiger Rückfragen als mit einem echten Modell -- das ist beabsichtigt (lieber nachfragen
als raten). Die Weboberfläche zeigt den Demo-Modus deutlich als "Demo-Modus, Ersatzmodell"
an (`GET /gesundheit`, Feld `demo_modus`).

## Architektur

```
Nutzerfrage
  -> app/llm/{fake,mistral}.py   : extrahiere_fakten()         -> app/schema.py (Fakten, inkl. anfrageart)
  -> app/pflichtangaben.py       : fehlende_pflichtangaben()   -> ggf. Rückfrage, Ende
  -> app/bestaetigung.py          : Faktenzusammenfassung       -> ohne Bestätigung: Ende (Teil 1d)
  -> app/router.py                : _rufe_kern_auf()            -> kern/rechnen.py (echt, seit Teil 1b)
  -> app/quellen.py               : regel_by_id()/regeln_suchen() -> regelwerk/*.xlsx, quellen/index.csv (nur lesend)
  -> app/baustein.py              : erzeuge_platzhalter()        -> erlaubte {NAME}-Platzhalter fuer DIESE Antwort
  -> app/llm/{fake,mistral}.py   : formuliere_antwort()        -> NUR Platzhalter-Fließtext (nie Werte, Teil 1d)
  -> app/baustein.py              : pruefe_rohtext()/fuelle()    -> verwirft Erfindungen VOR dem Einsetzen; setzt Werte ein
  -> app/router.py                : Ergebnis-Zeile, Ebenen-Abschnitt, Schlusssatz (nie das Modell)
  -> app/pruefung.py              : pruefe_antwort()             -> zweites Netz NACH dem Einsetzen
  -> app/log.py                   : protokolliere() bei "Nicht abgedeckt" bzw. fehlgeschlagener Prüfung
```

`Fakten.anfrageart` (`app/schema.py`) steuert, welcher Zweig in `app/router.py` den Kern
aufruft: `bewertung` (Standard: Eigenwerbung/typischer Verwerter/Positionen/Veranstaltungen),
`vorauszahlung`, `saeumniszuschlag`, `verpflegung`, `uebungsleiter_pauschale`, `kommission`,
`schaetzung_ausland`, `rechnungsanalyse` oder `rechtsprechungsfrage` (reine Recherche ohne
Kern-Aufruf, kein Jahr nötig, keine Faktenbestätigung nötig -- Befund 6, behoben).

`app/main.py` (FastAPI) verdrahtet das für `POST /frage`, `POST /bestaetigen`,
`GET /gesundheit` und liefert `app/static/index.html` (eine einzige statische Seite, kein
externes Skript/keine externe Schrift, responsiv per Flexbox/relativen Einheiten).

## Bausteinantwort mit Platzhaltern (Chatbot Teil 1d)

Seit Teil 1d schreibt das Sprachmodell (`app/llm/fake.py`, `app/llm/mistral.py`) in
`formuliere_antwort` **nur noch Fließtext mit Platzhaltern** der Form `{NAME}`
(`app/baustein.py`). Welche Platzhalter in einer Antwort erlaubt sind, bestimmt
ausschließlich `app/baustein.py::erzeuge_platzhalter` aus dem Kernergebnis der jeweiligen
Anfrage -- es gibt keine feste Liste im Code, und das Modell bekommt nie die tatsächlichen
Werte, nur die Namen und ihre Bedeutung (`PLATZHALTER_BESCHREIBUNG`).

`pruefe_rohtext` verwirft den Modelltext **vor** dem Einsetzen, wenn er außerhalb eines
Platzhalters irgendetwas enthält, das eine Tatsachenbehauptung wäre: Ziffern, `%`-/`§`-
Zeichen, ein Aktenzeichen-Muster, das Wort „Regel-ID", Währungswörter, ausgeschriebene
Zahlwörter und Mengenangaben (T€/Mio./Mrd./Prozent), Normbezüge im Wortlaut (Paragraf,
Artikel, Absatz, Satz, Nr., SGB, KSVG, EStG, GG), Gerichts-/Urteilswörter ohne Aktenzeichen,
ausgeschriebene Fassungs-/Rechtslage-Bezüge und jede eigene Ergebnisaussage. Das schließt
die 6 Lücken aus `aufgaben/PROMPT_ClaudeCode_Chatbot_1d_Nachtrag.md` (gefunden durch
`aufgaben/audit/gegenproben_teil1c_umgehung.py`) sowie 17 weitere Lücken aus
`aufgaben/PROMPT_ClaudeCode_Chatbot_1d_Nachtrag2.md` (gefunden durch
`aufgaben/audit/gegenproben_teil1d_runde3.py`, siehe `aufgaben/PRUEFBERICHT_Chatbot_Teil1d.md`):
Schlussfolgerungen in anderen Worten ("zahlungspflichtig", "abgabefrei", "Meldepflicht",
Gewissheits-/Empfehlungswörter), Gerichte/Behörden/Bestätigungen namentlich
(Bundesgerichtshof, Finanzamt, „die KSK hat bestätigt"), Links/Mailadressen, HTML-Tags,
Markdown-Überschriften und nach dem Einsetzen fehlerhaft/verschleiert übrig gebliebene
Platzhalter (`{{ABGABE}}`, `{abgabe}`). Die Wortlisten dafür liegen in
`app/baustein_konfiguration.json` (Konfiguration, kein Code) -- solche Listen sind
grundsätzlich nie vollständig (siehe Grenzen unten).

Erst danach ersetzt `fuelle` die Platzhalter durch die vom Kern gelieferten Werte. Die
Ergebnis-Zeile, der Ebenen-Abschnitt (Rechtsprechung/Norm/Verwaltungspraxis) und der
Schlusssatz werden ausschließlich von `app/router.py` gesetzt, nie vom Modell. Danach läuft
`app/pruefung.py::pruefe_antwort` (Teil 1c) als **zweites Netz** über den fertigen Text.
Schlägt eine der beiden Kontrollen fehl, bekommt der Nutzer einen generellen Ersatztext ohne
den erfundenen Wert im Klartext (Nachtrag Punkt 6) -- der Grund mit Wert geht nur ins
Lückenprotokoll.

## Rückfragen nach Tatsachen (Schritt 2, 17.10.2026)

Der Nutzer wählt keine rechtliche Kategorie („typischer Verwerter“, „Generalklausel“) mehr. Fehlt der Zweck, fragt das
System: **„Wofür war dieser Auftrag gedacht?“** mit den Knöpfen „Werbung für mein eigenes Unternehmen“, „Werbung oder
Öffentlichkeitsarbeit für Kunden“, „Eine Veranstaltung mit Künstlern“, „Ein privater Auftrag“ und „Noch unbekannt /
später klären“ (`app/einordnung.py::ZWECK_KNOPF`). Freie Beschreibung bleibt möglich; passt nichts, wird keine Kategorie
erzwungen. Die Einordnung leitet das System ab (`app/einordnung.py::leite_ab`); die Tätigkeit des Auftraggebers bleibt
erhalten (ein Verlag mit eigener Werbung bleibt Verlag). Regeln:
- Knopf oder exakt abgetippter Knopftext: Wert direkt übernommen, ohne Modellaufruf, Herkunft „von Ihnen ausgewählt“.
- Widerspricht die Auswahl einer ausdrücklichen Angabe im Text (oder umgekehrt), wird nichts überschrieben: gezielte Frage
  „Welche Angabe stimmt?“ mit beiden Werten als Knöpfen.
- Das Modell kann eine Auswahl nicht ändern; nur eine neue ausdrückliche Angabe im Text führt zur Rückfrage.
- „Noch unbekannt“: keine Bestätigung, keine Berechnung („zurückgestellt“); eine spätere Angabe ergänzt den Fall.
- `POST /knopf` nimmt nur Felder der Fakten oder einer vorhandenen Position an, nie Felder, die nur das System setzt;
  ungültige Eingaben ergeben eine Rückfrage, keinen Serverfehler. Die alte Eingabe `feld: "verwerterart"` geht weiter.

Die Faktenbestätigung beginnt mit wenigen Sätzen des Systems (worum es geht, welche Einordnung das System ableitet –
gekennzeichnet als **Vorschlag des Systems, keine Angabe von Ihnen** –, welche Annahme zur Umsatzsteuer gilt, dass erst nach
„Ja, das stimmt“ gerechnet wird). Danach steht die vollständige Liste einmal (`app/bestaetigung.py::saetze`, `als_liste`).

## Faktenbestätigung vor der Berechnung (Chatbot Teil 1d)

Nach der Fakten-Extraktion und der Pflichtangaben-Prüfung zeigt das **System** (nicht das
Modell) eine Zusammenfassung der erfassten Fakten (`app/bestaetigung.py::zusammenfassung`)
und fragt, ob das stimmt. Der Kern wird erst aufgerufen, nachdem der Nutzer das bestätigt
hat -- außer bei reinen Rechtsprechungsfragen, die nichts berechnen.

Ablauf über die API: `POST /frage` liefert bei einer berechnungsbedürftigen Anfrage
`ergebnisklasse: "Faktenbestätigung nötig"` samt `sitzungskennung`, `fakten_hash` und
`fakten_zusammenfassung`. `POST /bestaetigen` (mit genau diesen beiden Feldern) bestätigt
die Fakten per Hash und ruft erst dann den Kern auf. Eine Korrektur ist ein erneuter
`POST /frage` mit derselben `sitzungskennung` und dem korrigierten Text -- das macht die
alte Bestätigung automatisch ungültig (der Hash ändert sich), eine neue Bestätigung ist
nötig. Der Sitzungsstand liegt bewusst **nur im Arbeitsspeicher** (`app/bestaetigung.py::
Sitzungsspeicher`), nie in einer Datei -- er ist beim Neustart der App weg (siehe Grenzen
unten).

## Antwort-Kontrolle (Chatbot Teil 1c)

`app/pruefung.py::pruefe_antwort` läuft seit Teil 1c in **jedem** Antwort-Pfad (Hauptpfad,
Rückfrage, Nicht abgedeckt, Rechtsprechungsfrage) über `app/router.py::_ausgeben` -- vorher
lief sie nur im Hauptpfad (siehe `aufgaben/PRUEFBERICHT_Chatbot_Teil1.md`, Befunde B6-B8).
Geprüft werden: Geldbeträge (€/Euro/EUR, mit/ohne Tausenderpunkt, „999,-"), Prozentwerte,
Paragrafen (normalisiert: „Abs." = „Absatz", „S." = „Satz"), Jahreszahlen, die genannte
Fassung (A/B, gegen `app/quellen.py::fassung_fuer_jahr`), Regel-IDs, Aktenzeichen (auch
untypische Schreibweisen wie „Az. 12 R 77/22" oder „1 BvR …") und die Ebenen-Kennzeichnung.
Jeder einzelne Prüfschritt steht als Eintrag in `app/pruefung.py::PRUEFSCHRITTE` und kann
in Tests gezielt abgeschaltet werden (Mutationsprobe, siehe `tests/app/test_gegenproben.py`).

## Grenzen (ehrlich, siehe auch aufgaben/FUNDE_Chatbot.md)

- `app/router.py` verdrahtet elf Kernfunktionen (siehe Architektur oben); nicht jede der
  236 Regeln/40 Fallgruppen hat eine eigene Kernfunktion -- der Kern selbst ist laut
  `kern/README.md` ein "v0" (94 von 329 maschinenlesbaren Testfällen ausgeführt).
- `app/anonymisierung.py` ist eine einfache Regex-Heuristik (siehe Docstring dort für die
  genauen Grenzen), kein vollständiger Datenschutz-Schutz.
- Der Chatbot ist kein Nachweis für richtige Rechtsanwendung; fachliche Freigabe fehlt.
  Keine Kundendaten eingeben, nur erfundene Daten (auch in Tests).
- Hosting/Datenfluss: nur Mistral EU-Endpunkt vorgesehen; dieses Repo enthält kein Hosting.
- Die Zuordnung "welche Anfrageart/welcher Verwerterart passt zur Frage" muss das
  Sprachmodell (bzw. im Demo-Modus: die einfache Heuristik in `app/llm/fake.py`) treffen --
  eine falsche Zuordnung führt zu einem falschen, aber durch `app/pruefung.py` weiterhin
  quellenecht belegten Ergebnis. Das ist kein Ersatz für fachliche Prüfung.
- Die Faktenbestätigung (`app/bestaetigung.py`) liegt **nur im Arbeitsspeicher eines
  Prozesses**. Bei mehreren uvicorn-Workern/-Prozessen (z. B. hinter einem Load Balancer)
  sieht nicht jeder Worker jede Sitzung; für einen Prototyp mit einem Worker reicht das.
  Ein Neustart der App verwirft alle offenen (noch nicht bestätigten) Sitzungen -- der
  Nutzer muss die Frage dann erneut stellen.
- Die Zahlwort-/Normwort-/Gerichtswort-Erkennung in `app/baustein.py` (Wortlisten in
  `app/baustein_konfiguration.json`) ist eine Substring-Heuristik ohne Wortbildungsanalyse:
  die meisten Morpheme haben bewusst **keine** Wortgrenze (`\b`), weil deutsche Zahlwörter
  zusammengeschrieben werden (z. B. "neunhundert"). Das erkennt zuverlässig die im Nachtrag
  genannten Fälle, kann aber in seltenen Fällen auch in unverwandten Wörtern anschlagen
  (z. B. "acht" in "beachten"/"Betracht") -- dann lieber eine unnötige Ablehnung
  ("Prüfung fehlgeschlagen") als eine durchgelassene Erfindung. Ein bereits gefundener und
  behobener Fall: "ein" als unbestimmter Artikel wurde zunächst fälschlich als Zahlwort
  erkannt (siehe Commit-Historie, Teil 1d Nachtrag).
- **Grundsätzlich (Teil 1d Nachtrag 2, Abschnitt C):** die gesamte Rohtext-Kontrolle in
  `app/baustein.py` arbeitet mit Wortlisten (Blocklisten). Blocklisten sind ihrer Natur
  nach nie vollständig -- wer ein verbotenes Wort ergänzt, übersieht das nächste Synonym
  für dieselbe Aussage; das ist kein Fehler dieser Umsetzung, sondern eine grundsätzliche
  Grenze des Ansatzes "freier Text mit nachträglicher Kontrolle" (siehe
  `aufgaben/PRUEFBERICHT_Chatbot_Teil1d.md`). Die im Bericht genannte Lösungsrichtung
  (feste, vom Berufsträger geprüfte Bausteine aus dem Regelkatalog statt freier Sätze)
  ist nicht umgesetzt -- das braucht eine Entscheidung des Nutzers. Zur Einordnung:
  `aufgaben/FUNDE_Chatbot.md` (Abschnitt "Nachtrag 2") zählt, wie viele Sätze der
  Musterdialoge sich schon jetzt als feste Bausteine darstellen ließen und wie viele
  echten freien Text brauchen.

## Tests

```bash
python -m unittest discover -s tests/app
```

Alle Tests laufen offline mit `FakeLLM`; ein echter Netzwerkaufruf passiert nur in
`tests/app/test_mistral_rauchtest.py`, und der wird ohne `MISTRAL_API_KEY` automatisch
übersprungen.

- `test_schema.py`, `test_pflichtangaben.py`, `test_quellen.py`, `test_pruefung.py`,
  `test_anonymisierung.py`, `test_log.py`, `test_llm_fake.py`, `test_main.py`: Einzeltests.
- `test_prompt_injection.py`: eingebettete Anweisungen in Nutzertext/Quelltext werden als
  Daten behandelt, nicht ausgeführt; die Antwort-Kontrolle fängt ein "gekapertes" Modell.
- `test_pruefung.py`: enthält die geforderten Gegenproben (erfundener Betrag, erfundenes
  Aktenzeichen, fehlender Schlusssatz, nicht gekennzeichnete Verwaltungspraxis) -- jede im
  Testnamen als solche benannt.
- `test_router.py`, `test_abnahme_musterdialoge.py`, `test_abnahme_fallgruppen.py`:
  Abnahmetests aus den 5 Musterdialogen und aus `regelwerk/testfaelle_maschinenlesbar.json`,
  gegen den ECHTEN Kern. Dialoge 1 und 3 weichen weiterhin vom im Musterdialog behaupteten
  Ergebnis ab, weil die Schwellen-Tabelle nur 2019-2027 abdeckt -- das ist bewusst **nicht**
  angepasst, sondern in `aufgaben/FUNDE_Chatbot.md` dokumentiert (genau wie in
  `aufgaben/PROMPT_ClaudeCode_Chatbot_1.md` vorgegeben). Dialog 4 ist seit Teil 1b
  anbindbar und liefert ein echtes Ergebnis.
- `test_gegenproben.py` (Teil 1c): alle Fälle aus `aufgaben/audit/gegenproben_teil1.py`
  (Befunde B1-B8 aus `aufgaben/PRUEFBERICHT_Chatbot_Teil1.md`) als Unittests sowie
  Positivfälle (keine falschen Ablehnungen). Die Mutationsprobe für
  `app/pruefung.py::PRUEFSCHRITTE` steht seit Teil 1d in `test_pruefung.py` (baut `text`/
  `kontext` direkt, unabhängig von der Platzhalter-Architektur).
- `test_gegenproben_2.py` (Teil 1d Nachtrag): die 10 Umgehungsversuche aus
  `aufgaben/audit/gegenproben_teil1c_umgehung.py` (Zahlwörter, T€/Mio., Prozent als Wort,
  ausgeschriebene Paragrafen/Artikel, Gericht ohne Aktenzeichen, ausgeschriebene Fassung,
  Schlussfolgerung ohne Zahl) -- alle müssen blockiert werden, der Kontrollfall bleibt frei.
  Dazu eine Mutationsprobe über `app.baustein.ROHTEXT_PRUEFSCHRITTE`, end-to-end durch den
  vollen Router.
- `test_gegenproben_3.py` (Teil 1d Nachtrag 2): die 30 Umgehungsversuche aus
  `aufgaben/audit/gegenproben_teil1d_runde3.py` (Schlussfolgerung in anderen Worten,
  Gerichte/Behörden/Bestätigungen namentlich, verschleierte/falsch geschriebene
  Platzhalter, Links/Mailadressen, gefälschter Schlusssatz) -- alle müssen blockiert
  werden, beide Kontrollfälle bleiben frei. Dazu eine Mutationsprobe über die 6 dafür neuen
  Regeln in `app.baustein.ROHTEXT_PRUEFSCHRITTE`.
- `test_baustein.py`, `test_bestaetigung.py` (Teil 1d): direkte Unit-Tests für
  `app/baustein.py` (Platzhalter-Erzeugung, Formatierung, jede Rohtext-Regel einzeln) und
  `app/bestaetigung.py` (Hash-Stabilität, Sitzungsspeicher, Korrektur macht alte
  Bestätigung ungültig).
- `test_eigenschaften.py` (Teil 1d, eigenschaftsbasiert, nur Standardbibliothek, fester
  Seed): generiert ≥ 2000 zufällige, aber plausible Anfragen über alle Anfragearten und
  Jahre 2019-2027 und prüft, dass die ehrliche Pipeline (ohne Manipulation) niemals von der
  eigenen Kontrolle abgelehnt wird -- das heißt: jede Zahl/jedes Jahr/jede Fassung/jede
  Fundstelle in der Antwort ist nachweislich vertrauenswürdig. Läuft in < 60 s.
- `test_main.py` (Teil 1d): deckt den vollen `POST /frage` → `POST /bestaetigen`-Fluss über
  die FastAPI-Schnittstelle ab, inkl. falschem Hash und Korrektur.

## Sandbox-Nachweis

`scripts/pruefe_sandbox.sh` (bash) / `scripts/pruefe_sandbox.ps1` (PowerShell) klonen das
Repo **frisch** vom aktuellen Remote/Commit in ein temporäres Verzeichnis, bauen dort eine
neue virtuelle Umgebung, installieren `app/requirements.txt` und lassen den vollen
Testlauf dort laufen -- unabhängig vom aktuellen Arbeitsordner. Ergebnis mit Datum und
Commit-Hash: `aufgaben/SANDBOX_Nachweis.md`.

## Unabhängige Gegenrechnung (Teil 1e, seit 15.10.2026)

Jede Rechnung des Kerns wird vor der Ausgabe ein zweites Mal gerechnet, auf eigenem Weg:

- `app/gegenrechnung.py`: Der Router ruft den Kern über einen Mitschnitt auf (`KERN`). Jeder Aufruf einer
  Rechenfunktion wird mit Eingaben und Ergebnis notiert. Danach gehen **nur die Eingaben** an die Gegenrechnung. Klasse
  und jede Zahl müssen exakt gleich sein. Zusätzlich muss jede Zahl im Kernprotokoll aus einem gegengerechneten Aufruf
  stammen.
- `verifier/` (eigenes Paket, importiert `kern` nie): rechnet mit exakten Brüchen nach Regeltext und Regelregister
  (`kern/parameter.json` als Daten). Einstieg `verifier/lauf.py`.
- `app/sandbox.py`: startet die Gegenrechnung als **eigenen Prozess** (`python -I -B -S`, bereinigte Umgebung, leerer
  Temp-Ordner, JSON über stdin/stdout, Zeitlimit aus `app/konfiguration.json`).

Ausgang:

| Status | Was der Nutzer sieht |
|---|---|
| bestätigt | Antwort wie bisher, dazu die Zeile **Gegenrechnung:** … stimmt überein; Prüfprotokoll im Feld `pruefprotokoll` (Prüfung, Version, Registerzeilen mit Gültigkeit, Dauer) |
| nicht gegengerechnet | Antwort mit dem Hinweis, dass ein Teil nicht gegengerechnet ist (nie stillschweigend „bestätigt“) |
| Abweichung / fehlgeschlagen | **keine** Antwort: „Prüfung fehlgeschlagen“ mit „Gegenrechnung weicht ab (… Kern …, Gegenrechnung …). Bitte manuell prüfen.“, Eintrag ins Lückenprotokoll (anonymisiert, Fall-Kennung) |

**Was die Sandbox kann:** eigener Prozess; Zeitlimit (auch unter Windows); unter Linux/macOS Speicher- und CPU-Grenze
(`resource`); ein Wächter (`sys.addaudithook`) sperrt nach dem Laden des Registers jedes Öffnen von Dateien, Netz,
neue Prozesse, das Nachladen von Modulen (auch `kern` und `app`) und `exec`/`compile`; keine Umgebungsvariablen und
Schlüssel des Elternprozesses; Fehler, Zeitüberschreitung oder Absturz heißen immer „fehlgeschlagen“.

**Was sie nicht kann (ehrlich):** Sie ist ein Schutz vor Fehlern und ungewolltem Verhalten, **kein vollständiger
Sicherheitsrahmen wie ein Container**. Ein Audit-Hook lässt sich von Code mit vollen Rechten im selben Prozess
grundsätzlich umgehen. Dort läuft aber nur fest hinterlegter Code aus `verifier/`; das Sprachmodell schreibt und
startet dort nie Code. Unter Windows gibt es keine eingebaute Speichergrenze (dort nur das Zeitlimit; möglich wäre
später ein Job-Objekt). Für das Hosting ist ein Container ohne Netz auf einem EU-Server vorgesehen.

**Was die Gegenrechnung nicht prüft:** die Einordnung (Rechtsform, künstlerisch ja/nein, Verwerterart) und die
fachliche Richtigkeit einer Regel. Kern und Gegenrechnung lesen dieselbe Excel; ein falscher Wert dort fällt hier
nicht auf (dafür: Abgleich Register ↔ Quelltext und die Prüfung durch den Steuerberater). Texte des Kerns
(Begründungssätze) werden nicht gegengerechnet, nur Klassen und Zahlen.

Registerprüfung vor einer Freigabe: `python -m verifier.pruefe_register` (Form des Registers im eigenen Prozess,
danach Kern-Tests, Testfälle und Gegenrechnungs-Tests). Zeitmessung: `python scripts/messe_gegenrechnung.py`.

## Sicherheit/Datenschutz

- Keine API-Schlüssel, keine Kundendaten im Repo (siehe `.gitignore`: `/app/_lokal/`,
  `/app/.env`).
- Eingaben werden vor dem Schreiben ins Lückenprotokoll anonymisiert (`app/anonymisierung.py`).
- Das Lückenprotokoll (`app/_lokal/lueckenprotokoll.jsonl`) ist rein lokal und nie im Repo.
- Die Faktenbestätigung (`app/bestaetigung.py`) liegt rein im Arbeitsspeicher, nie in einer
  Datei -- sie verschwindet beim Neustart der App.
