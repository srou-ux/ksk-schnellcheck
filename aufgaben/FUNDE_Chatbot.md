# Befunde aus dem Bau von Chatbot, Teil 1, 1b und 1c (09.10.2026)

Status: Entwurf. Gemäß den Prompts wurde in `kern/`, `regelwerk/` und `quellen/` nichts
geändert; alle Funde unten sind reine Beobachtungen. Format je Fund: Datei, Stelle, Problem,
Vorschlag.

## Befunde B1-B8 (PRUEFBERICHT_Chatbot_Teil1.md) -- ALLE BEHOBEN (Chatbot Teil 1c)

Grundlage: `aufgaben/PRUEFBERICHT_Chatbot_Teil1.md` (unabhängige Prüfung von Teil 1b) und
`aufgaben/audit/gegenproben_teil1.py`. Alle acht Befunde sind jetzt in
`tests/app/test_gegenproben.py` als Unittests nachgewiesen (22 Tests, alle bestehen).

- **B1** (Beträge in anderen Schreibweisen: „999 Euro", „EUR 999", „999,- €"): behoben --
  `app/pruefung.py::BETRAG_MUSTER` erkennt jetzt €-davor/danach, „Euro", „EUR" und „999,-".
- **B2** (erfundener Paragraf „§ 99 KSVG"): behoben -- neue Prüfung `_pruefe_paragraphen`,
  normalisiert „Abs." = „Absatz", „S." = „Satz", „Nr." = „Nummer" und vergleicht gegen die
  gelieferten Regeln/Fundstellen.
- **B3** (erfundener Prozentsatz „7,5 %"): behoben -- neue Prüfung `_pruefe_prozente` gegen
  Kernergebnis (`abgabesatz_prozent`, von `app/router.py` aus `kern.rechnen.abgabesatz(jahr)`
  ergänzt) und Quellenstücke.
- **B4** (falsche Fassung „Fassung A … 450 €" bei Jahr 2026): behoben -- neue Prüfung
  `_pruefe_fassung` vergleicht eine genannte „Fassung A/B" gegen
  `app/quellen.py::fassung_fuer_jahr(jahr)` (aus den Daten, nicht aus Code).
- **B5** (erfundenes Jahr „2031"): behoben -- neue Prüfung `_pruefe_jahre`.
- **B6** (Pfad Rückfrage ohne Kontrolle): behoben -- `app/router.py::_ausgeben` ist jetzt der
  einzige Ausgabepunkt und ruft `pruefe_antwort` in jedem Pfad auf, auch bei Rückfrage.
- **B7** (Pfad Nicht abgedeckt ohne Kontrolle): behoben, gleicher Mechanismus (`_ausgeben`).
- **B8** (Pfad Rechtsprechungsfrage ohne Kontrolle): behoben, `_rechtsprechungsfrage` nutzt
  jetzt ebenfalls `_ausgeben` statt direkt `llm.formuliere_antwort` auszugeben.
- Zusätzlich verbessert (Fall 07 aus dem Audit, „Aktenzeichen in anderer Schreibweise"): war
  bereits vorher erkannt (bestätigt durch `tests/app/test_gegenproben.py::test_aktenzeichen_andere_schreibweise_wird_trotzdem_erkannt`),
  `app/quellen.py::aktenzeichen_in_text` unverändert ausreichend.

**Beim Haerten gefundener Programmfehler (vor dem Commit behoben):** Die erste Fassung der
neuen `_erlaubte_betraege`-Logik scannte nur noch Text auf „<Zahl> €"-Muster und verlor dabei
die direkt aus `kern_protokoll` stammenden `Decimal`-Werte (z. B. `abgabe = Decimal('73.50')`
hat im Protokoll kein „€" danebenstehen) -- der korrekte Basis-Fall (00) wäre dadurch selbst
abgelehnt worden. Behoben durch `_strukturierte_zahlen` (laeuft die echten Python-Objekte ab,
nicht nur den daraus gebauten Text) zusaetzlich zur Text-Suche. Durch den Lauf von
`aufgaben/audit/gegenproben_teil1.py` sofort aufgefallen, bevor es in einen Commit kam.

## Befund 1 -- BEHOBEN (Chatbot Teil 1b) -- `kern/` existierte im Repo nicht

- **Datei:** `kern/` (gesamtes Verzeichnis)
- **Problem (Teil 1):** Das Verzeichnis `kern/` war in der Git-Historie nicht enthalten,
  obwohl ein früherer Commit (`489fa0b`) es fälschlich als hinzugefügt auswies (Ursache:
  fehlendes `!/kern/` in `.gitignore`).
- **Behoben:** Mit `git pull` (Chatbot Teil 1b) sind `kern/rechnen.py`, `kern/parameter.json`,
  `kern/erzeuge_parameter.py`, `kern/README.md` jetzt im Repo. `python tests/test_kern.py`
  (24 Tests) und `python tests/lauf_testfaelle.py` (94 von 329 Fällen, 0 Abweichungen)
  laufen fehlerfrei. `app/router.py` importiert `kern.rechnen` jetzt nicht mehr defensiv,
  sondern direkt (`from kern import rechnen as K`); `app/ergebnisklassen.py` übernimmt die
  Klassen-Konstanten jetzt direkt von dort (`K.ABGABEPFLICHTIG` usw.) statt eigene Werte zu
  definieren. `tests/app/kern_testdouble.py` wurde entfernt (nicht mehr gebraucht).

## Befund 2 -- BEHOBEN (Chatbot Teil 1b) -- `.devcontainer/` und `scripts/start_codespace.sh` fehlten

- **Problem (Teil 1):** Beide Pfade existierten nicht, obwohl der Prompt sie als "schon im
  Repo" voraussetzte.
- **Behoben:** Mit `git pull` (Chatbot Teil 1b) sind `.devcontainer/devcontainer.json` und
  `scripts/start_codespace.sh` jetzt im Repo (von dieser Aufgabe nicht verändert).
  `app/README.md` wurde entsprechend aktualisiert.

## Befund 3 (weiterhin offen) -- Schwellen-Tabelle deckt 2017 nicht ab, wie im Prompt selbst erwähnt

- **Datei:** `regelwerk/Regelkatalog_24_KSVG_Entwurf.xlsx`, Blatt "Schwellen nach Jahr"
- **Stelle:** Deckt nur die Kalenderjahre 2019-2027 ab (`kern.rechnen.schwelle(2017) is
  None`). `regelwerk/Chatbot_Musterdialoge_Entwurf.md`, Dialog 1 (Test E-01) und Dialog 3
  (Test E-05) verlangen beide eine Bewertung für 2017.
- **Problem:** `PROMPT_ClaudeCode_Chatbot_1.md` nennt dieses Auseinanderfallen selbst als
  Beispiel ("Dialog 1/E-01 verlangt eine Bewertung für 2017, der Kern kennt die Schwellen
  erst ab 2019 und sagt 'Nicht abgedeckt'"). Jetzt gegen den ECHTEN Kern bestätigt (nicht
  mehr nur gegen ein Test-Doppel, siehe `tests/app/test_abnahme_musterdialoge.py`):
  Dialog 1 UND Dialog 3 liefern tatsächlich `kern.rechnen.NICHT_ABGEDECKT`
  ("Nicht abgedeckt (Quelle fehlt)") statt der im Musterdialog behaupteten "Nicht
  abgabepflichtig" bzw. "Grenzfall". `PROMPT_ClaudeCode_Chatbot_1b_Kern_anbinden.md`
  bestätigt ausdrücklich: "2017 bleibt 'Nicht abgedeckt' (weiter als Befund melden, nicht
  anpassen)".
- **Vorschlag:** Unverändert. Falls 2017 abgedeckt werden soll, müsste die Schwellen-Tabelle
  im Regelregister um 2017/2018 ergänzt werden (mit Fundstelle/Beleg) -- das ist Aufgabe
  einer Regelwerk-Recherche, nicht dieses Chatbot-Bauabschnitts.

## Befund 4 (erledigt sich voraussichtlich, Hintergrund bleibt informativ) -- Fakten-Schema-Feld fuer Regelmaessigkeit

- **Datei:** `app/schema.py`
- **Hintergrund:** In Teil 1 wurde spekulativ ein Feld `anzahl_auftraege` ergaenzt, um
  Dialog 1 (einmaliger Auftrag) von Dialog 3 (Historie unbekannt) zu unterscheiden.
- **Klarstellung nach Anbindung des echten Kerns:** `kern.rechnen.pruefe_eigenwerbung(jahr,
  summe)` nimmt tatsaechlich nur zwei Parameter; die Fassung-A-Unterscheidung
  (`GRENZFALL` bei Summe über der Geringfügigkeitsgrenze) hängt nur von `summe` und `jahr`
  ab, nicht von einem dritten "Regelmäßigkeit"-Parameter. Da Dialog 1 und Dialog 3 ohnehin
  beide an Befund 3 (keine Schwelle für 2017) scheitern, konnte diese Unterscheidung mit dem
  echten Kern nicht weiter verifiziert werden. Das Feld `anzahl_auftraege` bleibt im Schema
  (harmlos, ungenutzt) für den Fall, dass eine künftige Kern-Funktion es braucht.

## Befund 5 -- BEHOBEN (Chatbot Teil 1b) -- Router verdrahtete nur drei Fallgruppen; Dialog 4 fehlte

- **Datei:** `app/router.py`
- **Problem (Teil 1):** Nur Eigenwerbung, "typischer Verwerter" und Veranstaltungen waren
  angebunden; Dialog 4 (Reisekosten-Position) lieferte `Nicht_abgedeckt`.
- **Behoben:** `app/router.py::_rufe_kern_auf` verdrahtet jetzt elf Fälle über
  `Fakten.anfrageart`: `bewertung` (Eigenwerbung/typischer Verwerter/Positionen/
  Veranstaltungen, inkl. `kern.rechnen.pruefe_positionen` für Positions-Rollen wie
  `fahrtkosten_nachgewiesen`), `vorauszahlung`, `saeumniszuschlag`, `verpflegung`,
  `uebungsleiter_pauschale`, `kommission`, `schaetzung_ausland`, `rechnungsanalyse`. Dialog 4
  liefert jetzt Abgabepflichtig/3.000 €/150,00 € (siehe
  `tests/app/test_abnahme_musterdialoge.py::TestDialog4BemessungsgrundlageReisekosten`).
  Weitere Abnahmetests gegen `regelwerk/testfaelle_maschinenlesbar.json` (P-04, P-07, J-01,
  X-01, C-10, L-18, H-01) in `tests/app/test_abnahme_fallgruppen.py`.
  Offen bleibt: Nicht jede der 236 Regeln/40 Fallgruppen hat eine eigene Kernfunktion (der
  Kern selbst ist laut `kern/README.md` ein "v0").

## Befund 6 -- BEHOBEN (Chatbot Teil 1b) -- Pflichtangaben-Prüfung unterschied nicht Bewertungsfrage von Rechtsprechungs-Recherche

- **Datei:** `app/pflichtangaben.py`, `app/schema.py` (`anfrageart`), `app/router.py`
  (`_rechtsprechungsfrage`)
- **Problem (Teil 1):** Dialog 5 ("Gibt es ein LSG-Urteil zu Podcast-Produktionen?") fragte
  zuerst nach dem Jahr statt sofort "Nicht abgedeckt (Quelle fehlt)" zu antworten.
- **Behoben:** Neues Feld `Fakten.anfrageart = "rechtsprechungsfrage"` überspringt die
  Jahr-Pflicht vollständig; `app/router.py::_rechtsprechungsfrage` ruft den Kern gar nicht
  auf (keine Berechnung, also auch nie eine Zahl in der Antwort -- `kern_protokoll` bleibt
  leer), sondern durchsucht `app/quellen.py::regeln_suchen_ohne_jahr` nach Stichworten aus
  der Frage. Ohne Treffer: `NICHT_ABGEDECKT` + Lückenprotokoll-Eintrag (wie im Musterdialog).
  Siehe `tests/app/test_abnahme_musterdialoge.py::TestDialog5UrteilNichtInDerBasis` und
  `tests/app/test_router.py::TestRechtsprechungsfrage`.

## Befund 7 (gefunden und behoben waehrend der Kern-Anbindung) -- Betrags-Erkennung in app/pruefung.py verschluckte die erste Ziffer

- **Datei:** `app/pruefung.py`, `BETRAG_MUSTER`
- **Problem:** Die ursprüngliche Regex `(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*€` ging von einer
  Tausenderpunkt-Formatierung aus. `kern.rechnen.pruefe_eigenwerbung` formatiert Beträge in
  seinen Begründungstexten aber nicht immer so (z. B. `f"Summe {summe} €"` ergibt bei
  `summe == 1750` den rohen String "1750 €" ohne Punkt). Die alte Regex erkannte darin
  fälschlich nur "750 €" (Regex-Suche setzt mitten in der Zahl neu an, wenn der Anfang nicht
  passt) -- die Antwort-Kontrolle hätte einen echten, aus dem Kernergebnis stammenden Betrag
  als "erfunden" abgelehnt und eine korrekte Antwort durch "Nicht abgedeckt/Prüfung
  fehlgeschlagen" ersetzt. Beim ersten Testlauf gegen den echten Kern sofort aufgefallen
  (Dialog 2, Dialog 4 schlugen fehl).
- **Behoben:** `BETRAG_MUSTER` hat jetzt ein `(?<!\d)`-Lookbehind und ein ungebundenes `\d+`
  am Anfang, erkennt also sowohl "1.750,00 €" als auch "1750 €" vollständig. Zusätzlich
  prüft `_erlaubte_betraege` jetzt auch Zahlen in Fließtext aus `kern_protokoll`, `regeln`,
  `fundstellen` und `hinweisen` (nicht nur strukturierte `Decimal`-Werte) -- bewusst NICHT
  aus `kontext.frage` (rohem Nutzertext), damit eine Prompt-Injection keinen erfundenen
  Betrag einfach selbst auf die Whitelist setzen kann. Regressionstest:
  `tests/app/test_pruefung.py::TestRegressionBetragsErkennungOhneTausenderpunkt`.

## Befund 8 (gefunden und behoben waehrend der Kern-Anbindung) -- generische Pflichtangaben blockierten die neuen Anfragearten

- **Datei:** `app/pflichtangaben.py`
- **Problem:** Beim ersten Verdrahten von `vorauszahlung`/`saeumniszuschlag`/`verpflegung`/
  `uebungsleiter_pauschale`/`kommission`/`schaetzung_ausland`/`rechnungsanalyse` prüfte
  `fehlende_pflichtangaben` weiterhin unterschiedslos die für die Standard-Bewertung
  gedachten Felder (Auftragnehmer-Typ, Leistungsart, Betrag) und erzeugte dadurch eine
  Rückfrage, bevor `app/router.py` die jeweils passende, spezialisierte Rückfrage stellen
  konnte -- alle sieben neuen Pfade blieben in `RUECKFRAGE_NOETIG` haengen.
- **Behoben:** `fehlende_pflichtangaben` prüft die generischen Felder jetzt nur noch für
  `anfrageart in (None, "bewertung")`; jede andere Anfrageart (ausser
  `"rechtsprechungsfrage"`, das auch die Jahr-Pflicht überspringt) behält nur die
  Jahr-Pflicht, der Rest liegt bei den spezialisierten Zweigen in `app/router.py`.

## Nachtrag (PROMPT_ClaudeCode_Chatbot_1d_Nachtrag.md) -- ALLE 6 LUECKEN BEHOBEN (Chatbot Teil 1d)

Die zweite Audit-Runde (`aufgaben/audit/gegenproben_teil1c_umgehung.py`) fand 6 Lücken, die
Teil 1c noch durchließ, weil sie keinen Betrag/Paragraf/Aktenzeichen in der dort geprüften
Schreibweise enthielten: Zahlwörter ("tausend Euro"), Mengenangaben ("T€"/"Mio."/"Prozent"
als Wort), ausgeschriebene Normbezüge ("Paragraf"/"Art."), Gerichtsworte ohne Aktenzeichen,
ausgeschriebene Fassung/Rechtslage, und eine Schlussfolgerung ganz ohne Zahl
("...daher besteht keine Abgabepflicht"). Alle 6 sind mit der Platzhalter-Architektur
(`app/baustein.py::pruefe_rohtext`, Teil 1d) geschlossen: das Modell darf außerhalb eines
Platzhalters keines dieser Muster schreiben, und die Ergebnisaussage selbst setzt
ausschließlich der Router. Tests: `tests/app/test_gegenproben_2.py` (alle 10 Fälle aus dem
Audit-Skript blockiert, Kontrollfall frei, Mutationsprobe je Regel).

## Befund 9 (gefunden und behoben waehrend Chatbot Teil 1d) -- drei Kernfunktionen werfen bei fehlendem Regelregister-Eintrag einen unbehandelten Fehler statt "Nicht abgedeckt"

- **Datei:** `kern/rechnen.py` (Fund; NICHT geändert -- nur in `app/router.py` abgefangen)
- **Problem:** `pruefe_positionen`, `veranstaltungen` und `saeumniszuschlag` sind mit
  `@_luecke` dekoriert und liefern bei einem fehlenden Regelregister-Eintrag für das
  gefragte Jahr `Ergebnis(NICHT_ABGEDECKT, ...)` statt eines Fehlers. `schaetzung_ausland`,
  `vorauszahlung_monatlich` und `verpflegung` sind **nicht** dekoriert, rufen aber intern
  direkt `wert(...)`/`vergleich(...)` auf, die in diesem Fall eine `RegisterLuecke`-Exception
  werfen -- gefunden über `tests/app/test_eigenschaften.py` (zufällige Jahre 2019-2027) am
  Beispiel `schaetzung.ausland_prozent` im Jahr 2021 (kein Eintrag im Regelregister). Ohne
  Behandlung hätte das die ganze Anfrage mit einem internen Serverfehler abgebrochen statt
  "Nicht abgedeckt (Quelle fehlt)" zu liefern.
- **Workaround (in `app/router.py::_rufe_kern_auf`, nicht in `kern/`):** alle drei Aufrufe
  sind jetzt in `try/except K.RegisterLuecke` eingefasst und liefern bei fehlendem Eintrag
  dieselbe `KernErgebnis(NICHT_ABGEDECKT, ...)` wie die dekorierten Funktionen.
- **Vorschlag für `kern/`:** `schaetzung_ausland`, `vorauszahlung_monatlich` und
  `verpflegung` ebenfalls mit `@_luecke` dekorieren (oder gleichwertig abfangen), damit sich
  Aufrufer nicht auf diese Inkonsistenz einstellen müssen.

## Befund 10 (gefunden und behoben waehrend Chatbot Teil 1d) -- Fassung-Prüfung verwechselte eine Kern-Begründung mit einer Behauptung über das Prüfjahr

- **Datei:** `app/pruefung.py::_pruefe_fassung`
- **Problem:** `kern.rechnen.veranstaltungen` formuliert für Jahre vor 2023 (außerhalb der
  Generalklausel-Ausnahme für ≤ 3 Veranstaltungen) selbst den Begründungstext "Nur Fassung B
  (ab 2023) umgesetzt." -- eine Aussage darüber, welche Fassung die Kernfunktion
  implementiert, keine Behauptung über die Fassung des geprüften Jahres. `_pruefe_fassung`
  erkannte diesen Unterschied nicht und lehnte die (korrekte) Antwort fälschlich ab, weil
  "Fassung B" im Text stand, das Prüfjahr aber Fassung A hatte. Gefunden über
  `tests/app/test_eigenschaften.py`.
- **Behoben:** `_pruefe_fassung` nimmt jetzt (wie `_pruefe_jahre` für Jahreszahlen) jede
  "Fassung X"-Erwähnung aus, die bereits wörtlich in der vertrauten Textbasis
  (Kernergebnis/Regeln/Fundstellen/Hinweise) steht.

## Befund 11 (gefunden und behoben waehrend Chatbot Teil 1d) -- gerundet angezeigte Kernbeträge wurden als erfunden abgelehnt

- **Datei:** `app/pruefung.py::_strukturierte_zahlen`
- **Problem:** Manche Kernwerte (z. B. die Bemessungsgrundlage bei `schaetzung_ausland`: 25 %
  einer Summe) stehen im Kernprotokoll mit voller Rechengenauigkeit (z. B. `5928.155`),
  werden von `app/baustein.py::formatiere_betrag` aber auf zwei Nachkommastellen gerundet
  angezeigt (`5.928,16 €`). Die gerundete Anzeige war nicht in der Vertrauensliste, die nur
  den exakten Rechenwert kannte -- die Antwort-Kontrolle lehnte den korrekt angezeigten
  Betrag fälschlich ab. Gefunden über `tests/app/test_eigenschaften.py`.
- **Behoben:** `_strukturierte_zahlen` nimmt jetzt zusätzlich die auf zwei Nachkommastellen
  gerundete Form jeder Kernzahl in die Vertrauensliste auf.

## Befund 12 (gefunden und behoben waehrend Chatbot Teil 1d) -- "ein" als unbestimmter Artikel wurde als Zahlwort erkannt

- **Datei:** `app/baustein_konfiguration.json`
- **Problem:** Die Zahlwort-Morphemliste enthielt `"\bein\b"` -- das ist im Deutschen auch
  der ganz gewöhnliche unbestimmte Artikel ("ein Vorschlag", "ein Betrag"). Das hätte
  praktisch jeden normalen Fließtext des Modells fälschlich als "Zahlwort außerhalb eines
  Platzhalters" abgelehnt. Gefunden über den Kontrollfall ("q") in
  `tests/app/test_gegenproben_2.py`, der gerade NICHT blockiert werden darf.
- **Behoben:** `"\bein\b"` entfernt; `"eins\b"` (das tatsächliche Zahlwort "eins") bleibt.

## Hinweis (kein Fund, zur Nachvollziehbarkeit) -- Blattreihenfolge in der xlsx ist nicht stabil

Während Chatbot Teil 1 wurde `regelwerk/Regelkatalog_24_KSVG_Entwurf.xlsx` von einer
anderen/parallelen Sitzung um ein neues Blatt `Regelregister` (an Position 1) ergänzt
(Commit `b10116d`, nach `git pull`). `app/quellen.py` hatte Blätter ursprünglich über ihre
Position (Index) angesprochen; dadurch griff `alle_schwellen()` plötzlich auf das falsche
Blatt zu und lieferte keine Daten mehr (von `tests/app/test_quellen.py` sofort erkannt).
Behoben, indem `app/quellen.py` Blätter über den Namen sucht (`_blattname`) -- keine
Änderung an der xlsx selbst. Regressionstest:
`tests/app/test_quellen.py::TestBlattnameIstStabilGegenPositionsverschiebung`.

## Hinweis (kein Fund, zur Nachvollziehbarkeit) -- Fassung-Erkennung im Regelkatalog uneinheitlich formatiert

Die Spalte "Gilt für Fassung" in `regelwerk/Regelkatalog_24_KSVG_Entwurf.xlsx`, Blatt
"Regeln", enthält u. a. den Wert `"Fassung A (bis 31.12.2022); B nicht geprüft"`. Eine naive
Tokenisierung hätte das `B` darin fälschlich als Zusage für Fassung B gewertet.
`app/quellen.py::_fassung_passt` prüft deshalb klauselweise und erkennt eine vorangestellte
Verneinung (`nicht`) im selben Teilsatz. Regressionstest:
`tests/app/test_quellen.py::test_fassung_passt_erkennt_verneinung_nicht_als_zusage`.

## Nachtrag 2 (PROMPT_ClaudeCode_Chatbot_1d_Nachtrag2.md, aus PRUEFBERICHT_Chatbot_Teil1d.md) -- ALLE 17 LUECKEN BEHOBEN (Chatbot Teil 1d)

Die dritte Audit-Runde (`aufgaben/audit/gegenproben_teil1d_runde3.py`, 32 Fälle, davon 2
Kontrollfälle) fand 17 Lücken, die auch die Platzhalter-Architektur aus dem ersten Nachtrag
noch durchließ, weil es Schlussfolgerungen in ANDEREN Worten als den dort schon gesperrten
waren, oder weil ein Platzhalter nach dem Einsetzen fehlerhaft/verschleiert stehen blieb:

- **b1-b7 (Schlussfolgerung in anderen Worten):** "unterliegt der Abgabe",
  "zahlungspflichtig", "abgabefrei", "Meldepflicht besteht nicht", "Die Abgabe entfällt",
  Empfehlungen ("Sie sollten ... nicht zahlen") und Gewissheitsbehauptungen ("rechtlich
  eindeutig und sicher").
- **c1-c5 (Gerichte/Behörden/Bestätigungen namentlich):** "Der Bundesgerichtshof …", "Das
  Landessozialgericht …", "BFH und Finanzamt …", "Die Künstlersozialkasse hat dies
  bestätigt", "offiziell und von der KSK geprüft".
- **d2, d3 (Platzhalter nach dem Einsetzen fehlerhaft/verschleiert):** `{{ABGABE}}` (doppelte
  Klammern) und `{abgabe}` (Kleinschreibung) blieben nach dem Einsetzen wörtlich im Text
  stehen, statt ersetzt oder abgelehnt zu werden.
- **d4, d6 (Link/Mailadresse):** `http://…`, `max@example.org`.
- **d8 (gefälschter Schlusssatz):** `*Geprüft und freigegeben vom Steuerberater.*` per
  Markdown nachgebaut.

Alle 17 sind geschlossen (siehe `app/baustein.py`, `app/baustein_konfiguration.json`;
Details im Commit). Gegengeprüft direkt mit dem Audit-Skript selbst: 0 von 17 Lücken offen,
beide Kontrollfälle (q1, q2) gehen weiterhin durch. Tests: `tests/app/test_gegenproben_3.py`.

**Offen (bewusst nicht umgesetzt, siehe Nachtrag 2 Abschnitt C -- wartet auf Entscheidung
des Nutzers):** Wortlisten/Blocklisten sind grundsätzlich nie vollständig -- wer ein Wort
ergänzt, übersieht das nächste Synonym für dieselbe Aussage. Das ist kein Fehler dieser
Umsetzung, sondern eine grundsätzliche Grenze des Ansatzes "freier Text mit nachträglicher
Wortlisten-Kontrolle". Die im Bericht vorgeschlagene Lösungsrichtung (feste, vom
Berufsträger geprüfte Bausteine aus dem Regelkatalog statt freier Sätze) ist nicht
umgesetzt. Zur Einschätzung, wie weit das träge: von den inhaltlichen Sätzen in den 5
Musterdialogen (`regelwerk/Chatbot_Musterdialoge_Entwurf.md`, Schlusssatz nicht mitgezählt,
da ohnehin immer wörtlich fest) ließen sich **20 von 25** unmittelbar als feste Bausteine
aus den Regelkatalog-Spalten Norm/Voraussetzung/Rechtsfolge/Fundstelle/Vorbehalt bzw. als
immer gleiche Standardsätze einer Ergebnisklasse darstellen; **5 von 25** brauchen echten
freien Text, weil sie die Regel auf die konkreten, erst zur Laufzeit bekannten Fakten des
Einzelfalls anwenden oder eine fallbezogene Risikoeinschätzung formulieren (Dialog 1:
"Bei einem einzelnen Auftrag … fehlt beides nach dem festgestellten Sachverhalt." und
"Gibt es weitere Aufträge … kann die Wertung kippen."; Dialog 2: die beiden Sätze, die das
Urteil von der neuen Rechtslage abgrenzen; Dialog 3: "Ein einmaliger Auftrag ist nicht
automatisch regelmäßig; ob das wirtschaftliche Ausmaß genügt, kann ich nicht entscheiden.").

## Hinweis (kein Fund in `app/`, ausserhalb des erlaubten Arbeitsbereichs) -- `scripts/pruefe_alles.py` meldet FEHLER bei "Quellen unverändert", Ursache lokal/ausserhalb `quellen/`

`python scripts/pruefe_alles.py` (Nachtrag 2, Abschnitt D) meldet FEHLER beim Prüfsummen-
Schritt für 20 Dateien unter `quellen/ergaenzend/` (u. a. mehrere BSG-Urteile,
`KSK-FAQ_Unternehmen_und_Verwerter.txt`, `BGBl_2022_I_2759_8SGB-IV-AendG_Archivtext.txt`).
Untersucht, NICHT behoben (ausserhalb `app/`/`tests/app/`, und `quellen/` ist laut CLAUDE.md
unveränderlich):

- `git status` zeigt diese Dateien durchgehend als unverändert (sauber); die in
  `quellen/PRUEFSUMMEN.csv` hinterlegte SHA-256-Prüfsumme stimmt exakt mit dem committeten
  Git-Blob überein (`git cat-file -p HEAD:<Pfad> | sha256sum` == Eintrag in
  `PRUEFSUMMEN.csv`). Die Abweichung liegt ausschließlich zwischen dem committeten Blob
  (nur LF) und den tatsächlichen Bytes auf der lokalen Festplatte dieser Sitzung (mit CRLF).
- `.gitattributes` setzt `quellen/** -text`, und `git check-attr text -- <Datei>` bestätigt
  "unset" (also korrekt erkannt) -- trotzdem checkt `git checkout -- <Datei>` lokal weiterhin
  eine CRLF-Version aus (mehrfach reproduziert, auch nach erneutem Checkout). Das deutet auf
  eine lokale Git-/`core.autocrlf=true`-Eigenheit dieser Arbeitskopie hin, die die
  `-text`-Regel beim Checkout nicht wie erwartet überstimmt (Ursache nicht abschließend
  geklärt -- nicht untersucht: ob `.git/info/attributes`, ein globales `core.attributesFile`
  oder eine Git-Version-spezifische Eigenheit dafür verantwortlich ist).
- **Nicht versucht:** die Bytes direkt zu überschreiben (`git cat-file -p HEAD:<Pfad> >
  <Pfad>`) -- das würde den Prüfsummen-Fehler lokal beheben, aber `git status` könnte danach
  (durch dieselbe fehlerhafte Smudge-Filterung) fälschlich "geändert" anzeigen, was neue
  Verwirrung stiften könnte, und `quellen/` liegt ausserhalb des für diese Aufgabe erlaubten
  Arbeitsbereichs.
- **Vorschlag:** auf einer anderen Maschine/einem frischen Klon prüfen, ob derselbe Fehler
  auftritt (würde eine echte Diskrepanz zwischen Commit und Prüfsumme nahelegen) oder nur
  hier (würde die lokale Git-Konfigurations-Theorie bestätigen). Die Chatbot-Tests selbst
  (`tests/app`) sind davon nicht betroffen und laufen durchgehend grün.
- **Bestätigt (09.10.2026, Chatbot Teil 1f):** ein frischer Klon in ein temporäres
  Verzeichnis (neue venv) meldet bei `python scripts/pruefe_alles.py` **ALLES GRÜN**,
  auch beim Prüfsummen-Schritt. Der Fehler tritt also ausschließlich in dieser einen,
  langlebigen lokalen Arbeitskopie auf -- bestätigt die lokale Git-Konfigurations-Theorie.
  Weiterhin nicht selbst behoben (außerhalb `app/`/`tests/app/`).

## Chatbot Teil 1f -- neue Ergebnisklassen (Abschnitte B/C, zur Freigabe durch den Nutzer, CLAUDE.md Regel 5)

`app/ergebnisklassen.py` bekam zwei zusätzliche Anzeigeklassen nach dem Vorbild von
`RECHTSPRECHUNG_GEFUNDEN` (kein Rechenergebnis im klassischen Sinn, kommt nicht aus
`kern.rechnen`, braucht also eine eigene Benennung statt der fünf Kern-Ergebnisklassen):

- **„Säumniszuschlag (Vorschlag)"** (`SAEUMNISZUSCHLAG_BERECHNET`): `kern.rechnen.
  saeumniszuschlag` liefert intern die generische Kernklasse `ABGABEPFLICHTIG`
  ("Abgabepflichtig (Vorschlag)") -- das wäre hier falsch benannt, weil ein
  Säumniszuschlag keine Abgabepflicht-Entscheidung ist, sondern ein Zuschlag auf einen
  bereits feststehenden Rückstand. Die Kernklasse bleibt zur Nachvollziehbarkeit intern im
  Protokoll (`kern_protokoll["kern_klasse"]`).
- **„Auskunft aus dem Regelwerk"** (`AUSKUNFT_ERTEILT`): für `anfrageart == "auskunft"`
  (Abgabesatz/Schwelle/Meldefrist/Aufbewahrung). Auch das ist keine Abgabepflicht-
  Entscheidung, sondern eine erteilte Auskunft aus dem Register.
- Zusätzlich (Abschnitt J.3, nicht in B/C verlangt, aber aus demselben Grund eine eigene
  Klasse): **„Hinweis"** (`HINWEIS`) für Begrüßung/Smalltalk ohne jede Sachfrage.

**Bitte prüfen und freigeben oder eine andere Benennung vorgeben** -- bis dahin gilt auch
das als "Entwurf".

## Chatbot Teil 1f, Abschnitt C.4 -- Auskunft "pauschale" hat noch keinen eigenen Kernzugriff

- **Datei:** `app/router.py::_auskunft` (Fund; kein Zugriffspfad in `kern/` vorhanden)
- **Problem:** `kern.rechnen.uebungsleiter_bg` braucht einen BETRAG, um die Pauschale
  anzuwenden -- es gibt keine Kernfunktion, die nur "die Pauschale des Jahres X" ohne
  einen Betrag zurückgibt. Für `auskunft_thema == "pauschale"` liefert die App deshalb
  "Nicht abgedeckt (Quelle fehlt)" statt eine Zahl zu erfinden oder zu raten, welcher Wert
  gemeint ist (Übungsleiter- oder Ehrenamtspauschale?).
- **Vorschlag:** eine Kernfunktion (oder ein Register-Zugriff ohne Betrag) ergänzen, die
  für ein Jahr beide Pauschalenwerte (Übungsleiter, Ehrenamt) direkt zurückgibt, inkl.
  Fundstelle -- dann kann `_auskunft` das ohne Festwert anbinden.

## Chatbot Teil 1f, Nachtrag -- Abschnitte A/B/C/D umgesetzt (18 Lücken auf 0 Lücken)

Behoben: deterministische Gegenprüfung der Anfrageart `auskunft`/`hinweis` gegen eine
Begriffsliste aus der Nutzerfrage selbst (`app/zuordnung.py`, `app/auskunft_begriffe.json`
-- Konfiguration, kein Festwert im Code); Rückfragen (Pflichtangaben UND Kern-Rückfragen)
werden jetzt ausschließlich aus festen Textbausteinen gebaut, ohne jeden Modellaufruf
(`app/router.py::_rueckfrage_antwort`); Rechtsform-Rückfrage nur noch für Honorar-/
Entgeltpositionen, nicht für Positionen mit vom Kern ohnehin gesondert behandelten Rollen
(`kern.rechnen._AUSSCHLUSSGRUENDE`, aus dem Kern gelesen statt im App-Code aufgezählt);
FakeLLM nennt den Säumniszuschlag jetzt "Säumniszuschlag: …" statt "Abgabe: …".

### Abschnitt C.2 -- Prüfungsergebnis: `leistungsart` wird vom Kern nirgends gebraucht

Geprüft (grep über `kern/rechnen.py`): **keine** Kernfunktion für die Bewertung
(`summe_positionen`, `pruefe_positionen`, `pruefe_eigenwerbung`, `pruefe_typischer_verwerter`,
`veranstaltungen`) nimmt `leistungsart` als Parameter entgegen oder liest sie aus den
Positionsdaten -- das Feld wurde bisher rein informativ erfasst und blockierte trotzdem als
Pflichtangabe. `app/pflichtangaben.py` verlangt `leistungsart` deshalb nicht mehr als
Pflichtangabe für `anfrageart == "bewertung"`; das Modell darf sie weiterhin nennen
(Anzeige in der Faktenbestätigung), sie wird nur nicht mehr erzwungen.

### Abschnitt D.2 -- `jahr_plausibel` (1980/2100) absichtlich NICHT auf das Regelwerk umgestellt

Geprüft und bewusst **nicht** umgesetzt (Erlaubnis aus dem Auftrag: "Ist das nicht
sinnvoll, nenne es und lass es"). Begründung: `jahr_plausibel` ist eine reine
Eingabe-Plausibilitätsprüfung (verhindert z. B. `jahr=99999` oder negative Jahre), keine
fachliche Schwelle/Frist/Satz im Sinne von CLAUDE.md Regel 2 -- vergleichbar mit den dort
ausdrücklich erlaubten technischen Zahlen (100, 0.01, 12/31). Würde man die Grenzen auf
die aktuelle Registerabdeckung (z. B. 2015–2027) verengen, würde die Konstruktion eines
`Fakten`-Objekts mit einem plausiblen, aber (noch) nicht im Register erfassten Jahr (z. B.
2017 oder 2035) schon bei der Pydantic-Validierung mit einem Fehler abbrechen -- genau die
Fälle, die heute korrekt als "Nicht abgedeckt (Quelle fehlt)" beantwortet werden
(`tests/app/test_router.py::test_jahr_2017_ohne_schwellen_daten_ist_nicht_abgedeckt`,
`tests/app/test_teil1f.py::test_c6_jahr_ohne_excel_wert_ist_nicht_abgedeckt`). Das wäre eine
Regression, keine Verbesserung.

### Abschnitt D.3 -- Kern-Satz "Nicht zur Bemessungsgrundlage: 5000.00 €" (Punkt statt Komma)

- **Datei:** `kern/rechnen.py::_erklaere_ausschluesse` (Fund; NICHT geändert)
- **Problem:** `f"{betrag:.2f}"` auf einem `Decimal` formatiert mit Punkt als
  Dezimaltrennzeichen ("5000.00"), nicht mit deutschem Tausenderpunkt/Komma ("5.000,00").
  Alle anderen Geldbeträge in der App laufen durch `app/baustein.py::formatiere_betrag`;
  dieser eine Satz kommt direkt aus dem Kern-Begründungstext und wird unverändert
  durchgereicht (Architektur-Vorgabe: der Kern-Satz wird durchgereicht, nicht ersetzt).
  Nebeneffekt: `app/pruefung.py`s Betrags-Regex erkennt "5000.00 €" dadurch nicht als
  gültigen Betrag (keine Sicherheitslücke, da kernseitig vertrauenswürdig -- der Betrag
  wird einfach nicht geprüft, statt zu Unrecht abgelehnt zu werden).
- **Vorschlag:** in `_erklaere_ausschluesse` die App-eigene Formatierung verwenden (Punkt
  als Tausendertrennzeichen ab 1000, Komma als Dezimaltrennzeichen, zwei Nachkommastellen).

## Chatbot Teil 1g -- Mischform (feste Textbausteine statt freiem Modelltext), 09./10.10.2026

Umsetzung von `aufgaben/PROMPT_ClaudeCode_Chatbot_1g_Textbausteine.md`: der Antwort-Körper
kommt jetzt ausschließlich aus festen, im Regelkatalog gepflegten Textbausteinen (neues
Blatt "Textbausteine", 16 Zeilen TB-01..TB-16, gelesen von `app/textbausteine.py`); das
Modell liefert höchstens eine kurze, nur-Platzhalter Fallbeschreibung
(`llm.beschreibe_fall`), die einzeln verworfen wird, wenn sie gegen `pruefe_rohtext`
verstößt -- nie mehr die ganze Antwort. `formuliere_antwort` gibt es nicht mehr (weder auf
`LLM`/`FakeLLM`/`MistralLLM`, noch wird es von `app/router.py` aufgerufen).
Abnahme: `aufgaben/audit/abnahme_teil1g.py` 0 von 15 Lücken. Neue Tests:
`tests/app/test_teil1g.py` (35 Tests).

### Bestehende Tests angepasst (keine Prüfung abgeschwächt, Begründung)

Mit dem Entfernen von `formuliere_antwort` wurde Body-Injektion über diesen Weg
**strukturell unmöglich** (die Methode existiert nicht mehr und wird nirgends aufgerufen);
das ist eine Verschärfung, keine Abschwächung. Mehrere bestehende Tests prüften genau
diesen jetzt geschlossenen Weg und mussten auf den neuen, tatsächlich noch erreichbaren
Angriffsweg (`beschreibe_fall`) umgestellt werden -- mit der vom Auftrag selbst
vorgegebenen, bewusst anderen Erwartung ("Fällt dieser Satz durch die Kontrolle, entfällt
nur dieser Satz, nie die ganze Antwort", Abschnitt B):

- **`tests/app/test_gegenproben.py`, `test_gegenproben_2.py`, `test_gegenproben_3.py`:**
  `Boes` überschreibt jetzt `beschreibe_fall` statt `formuliere_antwort`. Erwartung
  invertiert: vorher musste ein böser Zusatz die GANZE Antwort auf
  "Prüfung fehlgeschlagen" kippen; jetzt bleibt die Ergebnisklasse normal, nur der böse Satz
  darf nicht mehr im Text stehen (`assertNotIn`), die restliche Antwort (Betrag, Fundstelle,
  Schlusssatz) bleibt vollständig und korrekt. Kontrollfälle (kein Verstoß) müssen weiterhin
  im Text stehen -- bei `q2_gueltiger_platzhalter` nach dem Einsetzen ohne die rohe
  `{SUMME}`-Schreibweise, da `fuelle()` den Platzhalter unabhängig von der geprüften
  Nachtrag-Regel ersetzt.
- **`tests/app/test_llm_fake.py::TestFakeLLMAntwortIstReinerPlatzhalterText`** (umbenannt zu
  `TestFakeLLMBeschreibeFall`): testete direkt `FakeLLM().formuliere_antwort(...)`. Jetzt auf
  `beschreibe_fall` umgestellt; zwei Tests, die Rückfragen-Platzhalter in der (jetzt nicht
  mehr existierenden) Modell-Körperantwort prüften, sind durch einen Test ersetzt, der
  bestätigt, dass `beschreibe_fall` den `{JAHR}`-Platzhalter referenziert statt des Werts.
- **`tests/app/test_mistral_rauchtest.py::TestMistralPromptOffline`**: zwei Tests riefen
  `MistralLLM.formuliere_antwort` auf (existiert nicht mehr) -- umgestellt auf
  `beschreibe_fall`; `_aufruf`-Fake um den neuen optionalen `max_tokens`-Parameter ergänzt.
- **`tests/app/test_teil1f.py::TestAbschnittIAbsturzschutz::test_fehler_beim_formulieren_...`**
  (umbenannt): simulierte einen `LLMFehlgeschlagen`-Absturz bei `formuliere_antwort` und
  erwartete, dass die GANZE Antwort zu einer festen Rückfrage wird. Unter Teil 1g betrifft
  ein Fehler bei `beschreibe_fall` nur die (optionale) Fallbeschreibung -- die Antwort bleibt
  vollständig (siehe `abnahme_teil1g.py::G6`). Die Testklasse simuliert den Fehler jetzt bei
  `beschreibe_fall`; die Erwartung ist eine vollständige, korrekte Antwort (Abgabe-Betrag im
  Text), nicht mehr `RUECKFRAGE_NOETIG`.

### Spannung mit `aufgaben/audit/gegenproben_teil1d_runde3.py` -- vom Nutzer selbst behoben (bb2ec59)

Beim ersten Durchlauf nach dem Umbau zeigte dieses (laut Auftrag nicht zu ändernde) Skript
31 statt 0 Lücken: sein `Boes` überschrieb nur `formuliere_antwort` -- eine jetzt nie mehr
aufgerufene Methode, ihr Zusatztext erreichte die Antwort also gar nicht mehr, wodurch auch
die erwartete "Prüfung fehlgeschlagen"-Klassifizierung ausblieb. Der Nutzer hat das Skript
daraufhin selbst angepasst (Commit `bb2ec59`, außerhalb dieser Sitzung/dieses Auftrags):
`Boes` überschreibt jetzt zusätzlich `beschreibe_fall`, und die Prüfung lautet "der böse
Text taucht in keiner Antwort auf" statt "die Antwort wird als Ganzes blockiert" -- passend
zur Mischform-Architektur. Nach `git pull --rebase`: **0 von 31 Lücken**, beide
Kontrollfälle (q1, q2) gehen durch. Keine Änderung an diesem Skript durch Claude Code in
dieser Sitzung.

### Offen, bewusst nicht umgesetzt (laut Auftrag Abschnitt A, Folgeauftrag)

Die Rückfrage-Bausteintexte in `app/pflichtangaben.py`/`app/router.py::_rueckfrage_antwort`
stehen weiterhin als Python-Text im App-Code, nicht im Regelkatalog -- laut Auftrag
ausdrücklich erlaubt ("dürfen vorerst bleiben, Folgeauftrag"). `abnahme_teil1g.py::G2` prüft
nur den Haupt-Antwortkörper (Textbausteine-Blatt gegen Code-Scan), nicht diese Rückfragen;
keine Lücke, aber zur Nachvollziehbarkeit hier vermerkt.

## Befunde aus dem ersten Livetest im Codespace (10.10.2026) -- `aufgaben/PROMPT_ClaudeCode_Chatbot_Livetest1_Befunde.md`

Auftrag erlaubte nur Änderungen in `app/` und `tests/app/`. L1, L2, L3 und die app-seitig
behebbaren Teile von L5/L6 sind behoben (siehe Arbeitsstand, Commit dieser Sitzung). Drei
Punkte haben ihre Ursache in `kern/` bzw. `regelwerk/` und sind deshalb NICHT verändert,
sondern hier gemeldet:

- **L4** (jeder Eurobetrag im Fließtext wird im Demo-Modus zu einer eigenen Position):
  laut Auftrag ausdrücklich "im Demo-Modus hinnehmbar ... nur dokumentieren, nicht
  umbauen" -- keine Änderung. `app/llm/fake.py::_heuristische_extraktion` bleibt wie
  gehabt; betrifft nur FakeLLM (Demo-Modus ohne Schlüssel), nicht den Mistral-Adapter.
- **L5, Subsumtionszeile ohne deutsches Zahlenformat** ("Summe 1200 € übersteigt die
  Schwelle 1000 €" statt "1.200,00 €"/"1.000,00 €"): Ursache ist `kern/rechnen.py`
  (`pruefe_eigenwerbung`, `veranstaltungen`, u. a. bauen ihre `begruendung`-Sätze mit
  rohen `Decimal`-Werten per f-string, z. B. Zeile `f"Summe {summe} € übersteigt die
  Schwelle {grenze} € ..."` ohne `_eur_de`/`formatiere_betrag`). Dieser Text landet
  unverändert als `{SUBSUMTION}`-Platzhalter in der Antwort (`app/baustein.py`), während
  `{SCHWELLE}`/`{SUMME}` an anderer Stelle korrekt deutsch formatiert erscheinen -- daher
  die wahrgenommene Dopplung mit unterschiedlichem Format. `app/` kann das nicht beheben,
  ohne `kern/rechnen.py` zu ändern (außerhalb des erlaubten Bereichs dieses Auftrags) oder
  den `{SUBSUMTION}`-Platzhalter ganz zu entfernen (das wäre eine inhaltliche
  Textbaustein-Entscheidung im Regelkatalog, nicht im Code). Vorschlag für einen
  Folgeauftrag: `kern/rechnen.py` nutzt überall dieselbe deutsche Zahlenformatierung wie
  `_eur_de` (dort bereits für `_erklaere_ausschluesse` vorhanden) auch in den übrigen
  `begruendung`-Sätzen.
- **L6, Fundstelle passt nicht zum Jahr** ("KSVG § 24 Abs. 2 S. 2, § 54" erscheint auch für
  Jahre/Fälle, in denen § 54 nicht einschlägig ist): Ursache ist der feste Fundstellen-Satz
  in `kern/rechnen.py::pruefe_eigenwerbung`, Zeile `fundstellen=["KSVG § 24 Abs. 2 S. 2,
  § 54", s["fundstelle"]]` -- dieser String wird UNBEDINGT (für jedes Jahr/jede Fassung)
  angehängt, nicht nur wenn § 54 (Schwellenanhebung ab 2025) tatsächlich zur Begründung
  beiträgt. Liegt außerhalb von `app/`; nicht geändert. Der andere Teil von L6 ("doppelte
  Fundstellen zusammenfassen", z. B. "S. 2" vs. "Satz 2 (aktuell)") ist dagegen app-seitig
  behoben: `app/router.py::_vereinheitliche_fundstellen` fasst unterschiedlich
  geschriebene, aber inhaltlich gleiche Fundstellen zusammen (nicht nur textgleiche wie
  vorher `dict.fromkeys`).

## Befunde aus dem ersten Prüfkatalog-Lauf mit Mistral (10.10.2026) -- `aufgaben/PROMPT_ClaudeCode_Chatbot_Pruefkatalog1_Befunde.md`

M1, M2, M4 und der app-seitige Teil von M3 sind behoben (siehe Arbeitsstand). Beim Beheben
von M3 kam ein weiterer, bisher verdeckter Kern-Befund zum Vorschein (Ursache in `kern/`,
außerhalb des erlaubten Bereichs dieses Auftrags -- hier gemeldet, nicht geändert):

- **`kern/rechnen.py::pruefe_typischer_verwerter` liefert "Abgabepflichtig" unabhängig von
  der Bemessungsgrundlage.** Anders als `pruefe_eigenwerbung` (das bei Bemessungsgrundlage 0
  unter jeder Schwelle bleibt, also "Nicht abgabepflichtig" liefert) gibt
  `pruefe_typischer_verwerter(jahr, entgelte)` IMMER die Klasse `ABGABEPFLICHTIG` zurück,
  auch wenn `entgelte` 0 ist (z. B. weil `summe_positionen` die einzige Position wegen
  Zahlung an eine GmbH/KG nach R-138/R-216 bereits ausgenommen hat, siehe Testfälle P-23
  "Werbeagentur zahlt an Grafik-GmbH" und P-24 "Werbeagentur zahlt an Grafikbüro-KG" im
  Prüfkatalog). Das fiel erst auf, seit `app/zuordnung.py::absichere_verwerterart` (M3)
  "Werbeagentur" korrekt als typischen Verwerter erkennt -- vorher griff in diesen Fällen
  zufällig der (jetzt entfernte) Eigenwerbungs-Default, der bei Bemessungsgrundlage 0 schon
  immer richtig "Nicht abgabepflichtig" ergab. Da `kern/` außerhalb des erlaubten Bereichs
  liegt, wurde dies NICHT in `pruefe_typischer_verwerter` behoben, sondern als reine
  Anzeige-Korrektur in `app/router.py::_nach_bestaetigung` ergänzt (Bemessungsgrundlage 0
  bei Kernklasse `ABGABEPFLICHTIG` → Anzeige "Nicht abgabepflichtig"). Vorschlag für einen
  Folgeauftrag: `pruefe_typischer_verwerter` bekommt denselben "Bemessungsgrundlage 0 →
  Nicht abgabepflichtig"-Kurzschluss wie `pruefe_eigenwerbung`, dann kann die Anzeige-
  Korrektur in `app/router.py` wieder entfernt werden.

## Befunde M5/M6 behoben (10.10.2026) -- `aufgaben/PROMPT_ClaudeCode_Chatbot_Pruefkatalog1_Befunde.md`

- **M5-Workaround -- durch M7 ersetzt, siehe eigener Abschnitt unten:** der hier
  ursprünglich beschriebene Ersatzwert (`_KEINE_VERANSTALTUNGSAUSNAHME_ANZAHL`) samt der
  sachlich ungenauen Begründung ist mit Befund M7 (10.10.2026) entfernt worden;
  `kern/rechnen.py::veranstaltungen` prüft `anzahl == 0` jetzt selbst eigenständig.
- **Demo-Modus-Grenze (nicht behoben, wie L4):** `aufgaben/audit/pruefkatalog_lauf.py`
  simuliert für P-07/P-08/P-09 jetzt Knopf-Antworten (`knoepfe` in `pruefkatalog.json`),
  aber die neue Pflichtangabe "Wie viele Veranstaltungen" (`FRAGE_VERANSTALTUNGSZAHL`) ist
  eine offene Frage ohne Schaltfläche -- der Prüfkatalog schickt dafür ersatzweise den
  freien `nachtrag`-Text ("...drei Veranstaltungen..."), den `app/llm/fake.py` nicht
  parst, weil seine Heuristik nur Ziffern vor "Veranstaltung" erkennt
  (`(\d+)\s+veranstaltung`), keine ausgeschriebenen Zahlwörter. Die drei Fälle bleiben
  deshalb im Demo-Modus bei "Rückfrage nötig" (NACHGEFRAGT, keine falsche Zahl) statt
  RICHTIG; mit dem echten Mistral-Modell sollte "drei"/"vier" korrekt verstanden werden.
  Keine Regression (vorher waren diese Fälle fachlich falsch berechnet, nicht "richtig
  gelöst"); nicht behoben, weil außerhalb des Auftrags (Demo-Heuristik, wie L4).

## Befund M7 behoben (10.10.2026) -- `aufgaben/PROMPT_ClaudeCode_Chatbot_Pruefkatalog1_Befunde.md`

Richtige Zahl, aber falsche Begründung bei Generalklausel ohne Veranstaltungen (Folgeprüfung
von M5). Für diesen Auftrag ausdrücklich erlaubt: Änderung an `kern/rechnen.py` und
`tests/test_kern.py` (sonst wie immer außerhalb des Arbeitsbereichs).

- **Ursache behoben, nicht mehr umgangen:** `kern/rechnen.py::veranstaltungen` prüfte die
  "bis zu drei Veranstaltungen"-Ausnahme (R-14/R-132) mit `anzahl <= 3`, was auch für
  `anzahl == 0` zutraf. Neuer eigener Zweig für `anzahl == 0`: eigene Prüfung mit der
  Regel **R-13** (bereits im Regelkatalog vorhanden -- "Unternehmer beauftragt Künstler/
  Publizisten, um deren Werke oder Leistungen für Zwecke des Unternehmens zu nutzen, wenn
  im Zusammenhang mit dieser Nutzung Einnahmen erzielt werden sollen", Fassung B, Fundstelle
  "KSVG § 24 Abs. 2 Satz 1 Nr. 2, Satz 2"), nicht R-14/R-132 (die sind explizit an die
  Veranstaltungszahl gekoppelt). Prüft nur noch Einnahmeabsicht + Summe über der Schwelle
  des Jahres (Register, kein Festwert) und liefert eine eigene, zutreffende Begründung
  ("Keine Veranstaltung, aber Nutzung mit Einnahmeabsicht: Summe … übersteigt die Schwelle
  … nicht mehr/nicht"). `app/router.py` ruft `K.veranstaltungen` jetzt wieder direkt mit der
  echten `veranstaltungszahl` auf, ohne Ersatzwert -- `_KEINE_VERANSTALTUNGSAUSNAHME_ANZAHL`
  ist entfernt.
- Der Wächter-Test (`tests/test_kern.py::Wächter::test_keine_fachlichen_festwerte_im_kern`)
  bleibt grün: der neue Code verwendet nur den erlaubten Literal `0` und liest Schwelle/
  Vergleichsoperator weiterhin aus dem Register.
- Tests: `tests/test_kern.py::GeneralklauselOhneVeranstaltungen` (4, direkt am Kern: P-07
  exakt wie im Prüfkatalog gefordert inkl. Fundstelle/Regel-ID, Summe unter Schwelle, ohne
  Einnahmeabsicht, Gegenprobe dass `anzahl >= 1` unverändert bleibt);
  `tests/app/test_pruefkatalog1_m5_m6_befunde.py` erweitert um die exakte
  `verboten_text`-Prüfung aus `pruefkatalog.json` ("Mehr als drei Veranstaltungen"/"drei
  Veranstaltungen" dürfen in der P-07-Antwort nie vorkommen) und die Fundstellen-Prüfung
  (keine "S. 3 Nr. 1" bei 0 Veranstaltungen).
- Geprüft: alle vier Abnahmen weiterhin 0 Lücken, `scripts/pruefe_alles.py` ALLES GRÜN
  (bis auf den bekannten lokalen Prüfsummen-Befund), `pruefkatalog_lauf.py --llm fake`
  unverändert 28 RICHTIG/17 NACHGEFRAGT/6 FALSCH (dieselben wie vorher) -- P-07/P-08/P-09
  bleiben im Demo-Modus NACHGEFRAGT (Grund siehe Abschnitt direkt oberhalb, Demo-Heuristik-
  Grenze, nicht M7).

## Testfall 20 Positionen (11.10.2026) – fehlende Tätigkeitsprüfung
- Datei/Stelle: `app/router.py` (Bewertung), `kern/rechnen.py::summe_positionen` (zählt alles, was nicht `kuenstlerisch is False` ist).
- Problem: Nicht künstlerische Leistungen an Einzelpersonen werden als sicher „Abgabepflichtig (Vorschlag)“ ausgegeben. Belege in `aufgaben/audit/testfall20_auswertung.md`.
- Vorschlag: Tätigkeitsprüfung aus einem neuen Excel-Blatt „Tätigkeiten“ (mit Fundstellen); unbekannte Tätigkeit → Rückfrage/Grenzfall, nie „Abgabepflichtig“.
- **Behoben am 11.10.2026 (Tätigkeitsprüfung):** neues Excel-Blatt „Tätigkeitsabgrenzung“ (35 Zeilen, nur aus R-42, R-49, R-92, R-117, R-137, R-142, R-175, R-176, R-182–R-194, R-234 und KSK-Info 06/02); `app/taetigkeiten.py`; `app/zuordnung.py::ergaenze_taetigkeit` (Modellwahl + feste Erkennung, Widerspruch → Grenzfall); `app/router.py::_mit_taetigkeitspruefung` (der Kern rechnet ohne und mit den unsicheren Leistungen; hängt das Ergebnis davon ab → Grenzfall, nie „Abgabepflichtig“); Rückfrage `FRAGE_LEISTUNG`, wenn die Leistung gar nicht beschrieben ist; Textbausteine TB-19 bis TB-23. Tests: `tests/app/test_taetigkeiten.py`.
- Noch offen: (a) R-117 (Designer: keine Trennung kreativer und technischer Anteile) und R-42/R-175 (Nebenkosten des Künstlers zählen mit) gelten für Positionen DESSELBEN Künstlers; das System prüft je Position und weiß nicht, ob mehrere Positionen vom selben Auftragnehmer stammen. (b) Die Erkennungsbegriffe sind eine Liste und nie vollständig; deshalb wird bei keinem Treffer nie „Abgabepflichtig“ ausgegeben. (c) Alle 35 Zeilen sind „Entwurf – vom Steuerberater zu prüfen“.
- **Behoben am 11.10.2026 (derselbe Künstler, Punkt (a) oben):** Excel-Spalte „Rechnet derselbe Künstler das mit ab“ (zählt mit / zählt nicht / Steuerberater entscheidet, mit Regel-IDs R-42, R-117, R-175, R-184, R-49); Schema `Position.auftragnehmer_nr`, `Fakten.ein_auftragnehmer`; Rückfrage `FRAGE_GLEICHER_AUFTRAGNEHMER` (Knöpfe ja/nein) nur, wenn es über das Ergebnis entscheidet; `app/router.py::_einordnung`; Textbaustein TB-24; Prüfkatalog P-52. Vorsicht: Nennt der Text bei mehreren Positionen ohne Bezeichnung Leistungen verschiedener Gruppen, wird keine Vorgabe für alle geraten (Grenzfall).
- 11.10.2026, offen: mistral-large-latest liefert bei manchen Einzelpositionen `"positionen": [1800]` (bloße Zahl), auch im zweiten Versuch (Testfall S-15). Das System fragt dann fest nach („bitte erneut stellen“); es rät nicht. Vorschlag: Zahl nur übernehmen, wenn sie genau einem Betrag im Nutzertext entspricht und es nur diese eine Position gibt (bewusst noch nicht gebaut, erst nach Rücksprache).

## Testprotokoll 11.10.2026 – Fallstand (behoben, siehe aufgaben/PRUEFBERICHT_Testprotokoll_1110.md)
- Ursachen: Chatverlauf als Speicher, keine Zustände für „unbekannt“/„widersprüchlich“, Modell sollte Restbeträge rechnen, erfundene Rollen, Anzeige der Rolle statt der Bezeichnung, Eigenwerbung nur geprüft, nicht ergänzt.
- Noch offen: Fallstand dauerhaft (PostgreSQL); Wortlisten für „unbekannt“ nie vollständig; Druckkosten bei der Grafikerin als R-49 ohne Rückfrage nach Druckvorstufe (Prüfliste F-09).

## Alltagsfälle F1–F4 (11.10.2026)
- Behoben: Privatperson als Auftraggeber (R-40/R-133); Rechnungsteller als Zahlungsempfänger (R-45/R-216, Hinweis R-219); T-68 Nutzungsrechte, T-69 Recherche; Reisekosten-Rolle nur mit Nachweis; Jahr aus einheitlichen Rechnungsdaten (gekennzeichnet); KSK-Auslegung erschien als „Norm“ (Ebene jetzt auch nach dem Vorbehalt der Regel); ausdrücklich genannte Übungsleiterpauschale (P-20b). Bericht: `aufgaben/audit/alltag4_auswertung.md`.
- **Offen (Fund):** Datei `app/router.py`, Zweig `uebungsleiter_pauschale`: `fakten.pauschale_bestaetigung if … is not None else True`. Eine fehlende Bestätigung gilt als erteilt, obwohl R-50/R-202 eine schriftliche Bestätigung verlangen. Vorschlag: ohne Angabe zurückfragen („Liegt die schriftliche Bestätigung vor?“). Nicht geändert, weil es eine fachliche Änderung am bestehenden Verhalten ist; Entscheidung des Nutzers/Steuerberaters.
- Offen: Die Testdatei enthält Rechenfehler (F3 USt, F4 Nettosumme). Eine Plausibilitätswarnung „Nettosumme ≠ Summe der Positionen“ für Belege gibt es nicht.

## Härtetest RE-2026-777 (11.10.2026)
- Behoben: Rechnungsteller-Regel je Position (Vertretung/Durchleitung/Direktzahlung → `zahlungsweg_unklar`, Grenzfall, TB-27); kein selbst gebildeter „Rest der Rechnung“ ohne „darin/davon“; Einnahmeabsicht nur bei der Generalklausel. Bericht: `aufgaben/audit/haertetest777_auswertung.md`.
- **Offen (Fund):** Datei `kern/rechnen.py::pruefe_typischer_verwerter` (R-07, Fundstelle „KSVG § 24 Abs. 1 S. 1“) bzw. Regel R-07 („Nr. 7“): Jeder typische Verwerter bekommt die Fundstelle der Werbung für Dritte, auch ein Veranstalter (§ 24 Abs. 1 S. 1 Nr. 3, R-29/R-160) oder ein Verlag (Nr. 1). Vorschlag: die Nummer des § 24 Abs. 1 aus der Art des Unternehmens wählen (Excel: Zuordnung Unternehmensart → Regel).
- **Offen (fachlich):** „Lichtdesign-Workshop“ einer Lichtkünstlerin wird über T-34 („Workshop-Moderation“) als nicht künstlerisch eingeordnet. Ob das künstlerische Lehre (T-18) oder Wissensvermittlung (T-63) ist, entscheidet der Steuerberater.
- **Offen (fachlich):** Gutschriften/negative Beträge für Zahlungen aus dem Vorjahr: keine Regel mit Quelle. Die Soll-Aussage der Testdatei „Abgabesatz nach Leistungsdatum“ widerspricht § 25 Abs. 1 S. 1 KSVG („im Laufe eines Kalenderjahres … zahlt“).

## ALLTAG-2026-999 und Dialog „Der schwierige Kunde“ (11.–13.10.2026)
- Behoben: siehe `aufgaben/audit/alltag999_auswertung.md` (B1–B11) und `aufgaben/audit/dialog_schwieriger_kunde_auswertung.md`.
- Behoben (Fund): `app/rechtsform_erkennung.py`, Muster `frei(e|en|er)?\s+\w+` traf auch „abgabenfrei ist“ → jetzt nur als eigenes Wort.
- Offen (Fund, nicht geändert): Datei `app/router.py::_als_regel_eintrag`: Die Ebene einer Fundstelle richtet sich nach der Gruppe der Regel. Bei R-03 (Gruppe „Katalog“) erscheint deshalb ein BSG-Urteil aus der Spalte Fundstelle unter „Norm“. Vorschlag: Fundstellen mit „BSG“/„LSG“ als Rechtsprechung kennzeichnen oder in der Excel trennen.
- **Behoben am 13.10.2026:** Ohne Rechnung fragte das System zuerst nach dem Jahr. Jetzt fester Baustein TB-35 (Bitte um die Rechnung, Fundstellen KSVG § 24, § 25 Abs. 1, KSK-Info 27), Begriffe in `app/einstieg_begriffe.json`, Tests in `tests/app/test_dialog_schwieriger_kunde.py`.
- Offen (beobachtet 13.10.2026, Live-Lauf a7b1bc6): P-32 „1.200 € Gestaltung und danach 800 € Druck, getrennt abgerechnet“ wurde einmal als EINE Rechnung mit Teilbetrag gelesen (Modell) → Rückfrage statt Ergebnis. Vorher RICHTIG; schwankt mit dem Modell. Vorschlag: „getrennt abgerechnet“ als zwei Rechnungen fest erkennen.

## Quellenabruf RAG, Teil 2 (13.10.2026)
- Gebaut: `app/rag/` (Index FTS5, Suche, Abgleich, Güte), siehe `app/rag/README.md`, `aufgaben/RAG_Bericht.md`, `aufgaben/RAG_Abgleich.md`.
- **Fund `quellen/index.csv`:** Die Datei hat keine Spalten für Gültigkeit (von/bis), Stufe und Kurzname, die der Auftrag dort vorsieht. Sie stehen deshalb in `app/rag/quellen_metadaten.csv` (automatisch vorbelegt, vom Steuerberater zu prüfen). Vorschlag: nach Prüfung als neue Spalten in `quellen/index.csv` übernehmen (nur ergänzen).
- **Fund `quellen/index.csv`:** Bei den Zeilen der lexetius-Urteile (z. B. `BSG_2003-07-24_B3KR37-02R.txt`) sind die Spalten verschoben (Abrufdatum „1884“, Herkunft „2026-10-09“, überzählige Spalte). Der Index liest deshalb nur Spalte 1 und 2. Vorschlag: Zeilen korrigieren (Komma in der URL `lexetius.com/2003,1884` nicht in Anführungszeichen).
- **Fund Metadaten (behoben):** Der aktuelle KSVG-Text (mit § 54: 700 € im Jahr 2025) war zuerst nur ab 2026 eingetragen; das Register belegt 2025 mit genau diesem Text. Jetzt KSVG.pdf ab 2025, Archiv 2024-05-21 nur 2024. Fachlich zu prüfen: Gilt der Text vom Oktober 2026 auch für 2025 unverändert (Änderungen 2026 durch Art. 7c)?
- **Fund Regelregister `musikverein.schueler_grenze` (60, gültig ab 2015):** Belegt nur mit KSK-Info 12 (Stand 08.2025); in der Archivfassung 2022 der KSK-Info 12 steht der Wert nicht (Abgleich: ABWEICHUNG). Vorschlag: Gültig-von prüfen.
- **Fund Regelregister `verpflegung.pauschale_*` (2014–2019):** Fundstelle KSK-Info 10 Abschn. 3; für diese Jahre liegt keine Fassung der KSK-Info 10 in der Quellenbasis (ältestes Archiv 2023). Abgleich: „Fundstelle fehlt“.
- Offen: Abruf-Güte 85,6 % (Ziel 90 %). Ursachen und Liste der Fehlschläge in `aufgaben/RAG_Bericht.md`.
- **Gemessen 13.10.2026: Embeddings (mistral-embed) verschlechtern die Güte** in allen 5 Varianten (79,9–84,6 % gegen 85,6 %), `aufgaben/RAG_Embeddings_Varianten.md`. Schalter bleibt aus. Behoben dabei: 6 Tabellen-Stücke über der Eingabegrenze (8192 Token) werden jetzt an Wortgrenzen geteilt; Such-Einstellungen lösen keinen Neuaufbau (und keine neuen Embedding-Kosten) mehr aus. Mögliche nächste Wege: eine Rückfrage-gestützte Suche über die Fakten (Regelfilter) statt freier Ähnlichkeit, oder ein auf deutsche Rechtstexte trainiertes Modell (nur EU-Anbieter).
- Offen: Gegenproben (Fragen ohne Quelle) 6 von 10 richtig leer; die Stichwortsuche erkennt fachfremde Fragen mit gängigen Wörtern („Hundesteuer“, „Kündigungsfrist“) nicht sicher als „nicht abgedeckt“.
- **Fund, behoben 13.10.2026 (Live-Läufe f5106b4 und 7b4ebe1, je 2 FEHLER):** „Die Antwort des Sprachmodells konnte nicht verarbeitet werden“ bei P-16 (und einmal K-01, P-20a). Diagnose mit dem neuen Workflow „Modellfehler suchen“ (Protokolle `aufgaben/audit/modellfehler_*`): mistral-large-latest schreibt den Schlüssel `veranstaltungzahl` statt `veranstaltungszahl`; die strenge Schemaprüfung (`app/llm/mistral.py`) verwarf die ganze Antwort. **Nicht durch den Quellenabruf verursacht:** mit `RAG_AUS=1` derselbe Fehler (2 von 3 Läufen); der erste Vergleich (3:0) war Zufall. Behebung: `_tippfehler_schluessel` benennt einen unbekannten Schlüssel nur um, wenn er sich von genau einem Schema-Feld um ein Zeichen unterscheidet (mind. 8 Zeichen, Feld nicht schon gesetzt); fremde Schlüssel bleiben ein Fehler. Tests: `tests/app/test_tippfehler_schluessel.py`. Zusätzlich: Index-Aktualisierung beim App-Start läuft jetzt vor der ersten Anfrage statt parallel.

## Ursachen der Abruf-Fehlschläge (14.10.2026)
- Analyse der 43 Fehlschläge (85,6 %): ca. 18 „richtige, aber andere Quelle“ (z. B. KSK-Info 07 statt KSVG § 24 Abs. 1 Nr. 2) -- Urteil darüber beim Steuerberater; 2–3 Messfehler; 3 Rechtsform-Abkürzungen nicht gesucht; 4 Datenfälle; 3 reine Rechenfragen; 8–10 echte Lücken (Sachleistung, Fremdwährung, Verjährung, GEMA, Abwälzungsklausel, Meldebogen).
- Behoben: Messung liest alle Absätze/Paragrafen einer Fundstelle (`app/rag/guete.py::stellen_in`); Rechtsform-Abkürzungen KG, GbR, OHG, UG, AG, USt, GEMA, e. V. werden gesucht (`konfig.json` „kurzwoerter“); Gesetz/Urteil und KSK-Auslegung als getrennte Ranglisten (`quellen_nach_stufe_trennen`): Antworten mit Gesetzes-/Urteilsstelle 133 → 228 von 266, an erster Stelle 120 → 224; Testfälle „Wie X-01, aber …“ bekommen in der Messung den Text des Bezugsfalls. Quote 85,6 % → 86,6 %.
- Geprüft und verworfen: Stoppwörter („zahlt“, „Jahr“) entfernen -- keine Verbesserung.
- **Für den Steuerberater (Regelkatalog, Blatt Regeln, Spalte „Gilt für Fassung“):** 12 Regeln ohne auswertbare Fassung werden nie geliefert: R-18, R-19, R-27, R-36 („aktuell“), R-20, R-21 („alle“), R-68 („Wortlaut 2024 …“), R-89 („Jahresabhängig“), R-115 („A … / B …“), R-230, R-231 („Momentaufnahme …“), R-233 („Fassung vor 01.07.2001“). Vorschlag: je Regel „A, B“, „B“ oder „A“ eintragen (nur der Mensch entscheidet, ob „aktuell“ auch ältere Jahre deckt).
- **Für den Steuerberater (Testfälle):** je Testfall eine Liste der zulässigen Fundstellen statt einer einzigen (z. B. KSVG § 24 Abs. 1 Nr. 2 ODER KSK-Info 07), damit „richtig, aber anders“ nicht als Fehlschlag zählt.
- **Fund (Stabilität, 14.10.2026):** P-04a, P-04b, P-30, P-32 wechseln über 10 Live-Läufe zwischen RICHTIG und NACHGEFRAGT, unabhängig vom Code. Ursache jeweils bei der ersten Faktenerkennung: Mistral legt Teilbeträge einer Rechnung mal als Positionen, mal als Rechnung mit „darin“ an („Aufteilung unklar“, „Welche Angabe stimmt?“). Das System fragt dann richtig nach (nie falsch). Vorschlag für später: feste Erkennung „getrennt abgerechnet“ / „je … €“ / „davon“ vor dem Modell, damit das Ergebnis nicht vom Zufall abhängt.

## Fremde Währung (14.10.2026) – Schritt 1 des Plans
- **Fund (live, vorher, Stand 71f75e9):** Rechnungen in fremder Währung wurden als Euro gerechnet: 2.000 US-Dollar → Bemessungsgrundlage 2.000,00 €, Abgabe 98,00 €; ebenso 1.500 $, 1.200 GBP, gemischte Rechnung 1.200 EUR + 500 USD → 1.700,00 €. 5 von 10 Währungsfällen FALSCH, 1 FEHLER (`aufgaben/audit/testfall_waehrung.json`, Soll nach Testfall L-23).
- **Behoben:** `app/zuordnung.py::markiere_fremdwaehrung` erkennt Beträge in fremder Währung im Text (Begriffe in `app/waehrung_begriffe.json`, ohne Code erweiterbar). Es wird **nie umgerechnet**. Steht im selben Satz genau ein Euro-Betrag („abgebucht wurden 1.850,00 €“), zählt dieser; sonst fragt das System nach dem tatsächlich gezahlten Euro-Betrag (`app/pflichtangaben.py`), und der Kern rechnet nicht, solange er fehlt. Die Faktenbestätigung zeigt „1.850,00 € (gezahlter Euro-Betrag; angegeben 2.000 USD)“.
- **Fund (live, dabei):** Das Modell schrieb `"betrag": "1500 $"` / `"250.000 Yen"`; die Schemaprüfung verwarf die ganze Antwort („konnte nicht verarbeitet werden“). Behoben in `app/llm/mistral.py` mit `zuordnung.fremdbetrag_als_zahl`: nur die Zahl, und nur wenn genau dieser Betrag in dieser Währung im Nutzertext steht; sonst Fehler wie bisher.
- Live nachher (mistral-large-latest): 10/10 richtig (6414d11) und 10/10 richtig mit zusätzlicher Textprüfung „in fremder Währung angegeben“ (563ab52). Tests: `tests/app/test_waehrung.py` (15).
- **Für den Steuerberater (fachlich offen, keine Quelle in der Quellenbasis):** Welcher Euro-Wert zählt als Entgelt nach § 25 KSVG bei Zahlung in fremder Währung – der tatsächlich abgebuchte Betrag (so fragt das System jetzt), ein Kurs am Rechnungs- oder Zahlungstag, oder ein amtlicher Kurs (z. B. Umsatzsteuer-Umrechnungskurse des BMF)? Bis eine Quelle vorliegt, rechnet das System nur mit einem vom Nutzer genannten Euro-Betrag. Gebühren der Bank sind nicht berücksichtigt.
- Grenzen: Erkannt werden nur die Währungen in `app/waehrung_begriffe.json`. Ein Betrag, der als Zahl sowohl in Euro als auch in fremder Währung im Text steht, gilt als Euro (nicht eindeutig fremd). Mehrere Euro-Beträge im selben Satz werden keinem Fremdbetrag zugeordnet (dann Rückfrage).
- **Fund (live, 14.10.2026, Stand 563ab52, nicht durch die Währung verursacht): P-20b FALSCH** – Abgabe für 3.500 € ohne Übungsleiterpauschale (Soll Bemessungsgrundlage 1.100 €). In 11 Läufen davor ließ das Modell die Art des Auftraggebers offen (Rückfrage); diesmal setzte es sie, dazu `pauschale_art`, ließ aber die Anfrageart „bewertung“ – der Kern rechnete ohne Pauschale. Die Faktenbestätigung zeigte die Pauschale nicht, der Fehler war für den Nutzer nicht erkennbar. **Behoben** in `app/zuordnung.py` (`ergaenze_pauschale`, `_pauschale_angaben_aus_text`): Nennt der Text die Pauschale, gilt die Pauschalen-Rechnung; „bestätigt“ im Text geht vor einem „nein“ des Modells; „schon verbraucht“ zählt nur mit einem Betrag aus dem Text. `app/bestaetigung.py` zeigt jetzt „Pauschale: …, schriftlich bestätigt: ja/nein, davon schon verbraucht: …“. Tests `tests/app/test_pauschale_aus_text.py` (5).

## Teilbeträge stabil lesen (14.10.2026) – Schritt 2 des Plans
- **Messung vorher** (Workflow „Modellfehler suchen“, je Fall 6 Läufe, neu mit Fakten-Protokoll `FAKTEN_PROTOKOLL_PFAD`, Dateien `aufgaben/audit/modellfehler_fakten_*_<Lauf>.jsonl`): P-04a 1/6, P-04b 0/6, P-28 2/6, P-30 6/6, P-32 1/6 richtig. Die Beträge erkannte das Modell jedes Mal richtig; es schwankte nur bei der Frage, was eine „Rechnung“ ist.
- **Ursachen und Behebung** (`app/zuordnung.py`, alles deterministisch, nichts geschätzt):
  - Das Modell legte jede Position zusätzlich als eigene Rechnung an (5 × 250 € als Positionen UND als Rechnungen, alle Auftragnehmer 1) → „Ein Teilbetrag ist so hoch wie die ganze Rechnung“. `einzelrechnungen_je_position`: passen die Rechnungen eins zu eins zu den Positionen und nennt der Text kein „darin/davon“, ist jede Position eine eigene Rechnung. Auch vor dem Zusammenführen im Fallstand (der eine Rechnung je Auftragnehmer führt).
  - Nur Rechnungen, keine Position → jede Rechnung wird Position, wenn ihr Betrag so im Text steht.
  - „1.190 € brutto, darin 190 € Umsatzsteuer“: Position in Höhe der ganzen Rechnung (auch fälschlich als „ust“ bezeichnet), leere Rest-Position, oder die 190 € als „Rest“ markiert → jetzt: der im Text genannte enthaltene Betrag ist nie der Rest; die Position in Höhe der Rechnung wird zum Rest (bzw. fällt weg, wenn das Modell den Rest schon angelegt hat). `ergaenze_rolle_darin`: Rolle „ust“ für den enthaltenen Betrag nur mit Beleg-Wort direkt beim Betrag UND in der Bezeichnung.
  - Gleiche Bezeichnung aller Positionen („kleine Werbegrafiken“ × 5) = eine Art von Leistung; der Rest einer Rechnung gilt wie „Honorar“ als allgemeine Bezeichnung.
- **Messung nachher:** 36/36 richtig (P-04a, P-04b, P-28, P-30, P-32, W-03 je 6/6, Stand 7be4ac4). Die echten Modellantworten aller Messungen sind Offline-Testfälle: `tests/app/daten_teilbetraege_live_1410.json`, `tests/app/test_teilbetraege_live.py`.
- **Nicht gelöst (bewusst):** Lässt das Modell den enthaltenen Betrag ganz weg (nur 1.190 € und ein leerer Rest), fragt das System nach – den Betrag aus dem Text selbst zu bilden wäre geraten (1 von 18 P-28-Antworten).
- **Fund für die Excel (Blatt Tätigkeitsabgrenzung, nicht geändert):** Begriffe werden nur am Wortanfang erkannt; „Werbegrafik(en)“ wird deshalb nicht als T-02 erkannt (wohl „Grafik“, „Grafiker“). Vorschlag: „werbegrafik“ bei T-02 ergänzen (Mensch entscheidet; ähnlich evtl. „Werbefoto“ bei T-04).
- **Fund (live, 7fdc4f9): W-03** einmal nachgefragt: das Modell füllte die Systemfelder `fremd_betrag`/`fremdwaehrung` selbst („2000“). Behoben: `zuordnung.ohne_systemfelder` verwirft Modellwerte in diesen Feldern direkt nach dem Auslesen.
- **Fund (live, 5584e86, Lücke älter als Schritt 2): P-39 FALSCH** – 2.500 € statt 2.000 € („Gage 2.000 €, davon 500 € an den Manager“). Das Modell legte die Rechnung über 2.000 € selbst an und gab die 500 € einem zweiten Auftragnehmer; die Schutzregel `enthaltene_betraege_nicht_doppelt` griff nur ohne Rechnung. Mit denselben Fakten rechnete auch der Code von vor Schritt 2 (ed2b47f) 2.500 €. Behoben: gilt jetzt auch bei einer vorhandenen Rechnung über genau den äußeren Betrag, wenn der enthaltene Betrag bei einem anderen Auftragnehmer liegt. Tests in `tests/app/test_teilbetraege_live.py` (Klasse DavonAnDritte).
- **Fund (live, 9d63759, Lücke älter als Schritt 2): P-52 FALSCH** – Bemessungsgrundlage 3.000 € statt 3.200 €. Das Modell gab „Miete für Kamera-Equipment 200 €“ die Rolle „nachträgliche Vervielfältigung“; die Schutzregel ließ das zu, weil das Wort „Druck“ der NÄCHSTEN Position („200 € netto, Druckkosten …“) weniger als 30 Zeichen entfernt stand. Behoben in `zuordnung._betraege_am_begriff`: ein Beleg-Wort in einem anderen Listenteil (Komma nicht zwischen Ziffern, Semikolon, Zeilenumbruch) zählt nicht, wenn dort ein eigener Betrag steht. „80 € Fahrtkosten, nachgewiesen durch Ticket“ zählt weiter. Tests: Klasse BelegWortImNaechstenListenteil.
- **Für den Steuerberater (Vorschlag, nicht umgesetzt): F1 „Nutzungsrechte Kampagne“** – die feste Erkennung sagt T-68 (Grenzfall; zählt mit, wenn derselbe Künstler abrechnet: R-41, R-174, R-189), das Modell manchmal T-04 (Fotografie). Nach der Vorgabe „Modell und Erkennung uneinig → Steuerberater“ wird es ein Grenzfall (Messung 14.10.: 2 von 6 Läufen; in den 13 Gesamtläufen davor nie). Vorschlag: Ist das Ergebnis der festen Erkennung selbst ein Grenzfall-Eintrag, gilt dieser (die Excel-Regel entscheidet), statt eines Widerspruchs. Fachliche Entscheidung – bewusst nicht geändert.
- Beobachtet (nicht durch Schritt 2): A-999 einmal „Antwort konnte nicht verarbeitet werden“ (Modell lieferte in `positionen` Einträge, die keine Objekte sind; zweiter Versuch ebenso). Das System fragte richtig nach; nach dem Nachtrag ging es weiter.
- Beobachtet (Gesamtlauf 3b58f6a, nicht durch Schritt 2): **P-31** einmal nachgefragt (16 Läufe davor richtig). „1.000 € Gage … zusätzlich … Bewirtung 80 €“: legt das Modell eine Rechnung über 1.000 € an UND die Bewirtung als Teil davon, meldet das System „Teilbetrag so hoch wie die ganze Rechnung“ (alter Code gleich). Nie eine falsche Zahl. Vorschlag für später: „zusätzlich“ als eigene Leistung neben der Rechnung erkennen.
- Fund (Workflows, behoben): Ergebnisse eines Gesamtlaufs (0437282) gingen verloren, als zwei Workflows gleichzeitig pushten (`|| true` verschluckte den Fehler). „Chatbot direkt“ und „Modellfehler suchen“ sichern die Ergebnisse jetzt und pushen mit bis zu 3 Versuchen. Hinweis: Der Code-Stand im Dateinamen der Ergebnisse ist der Stand beim Start des Laufs (kann ein Ergebnis-Commit sein).

## Nachgefragte Fälle einzeln untersucht (14.10.2026)
- 16 von 17 nachgefragten Fällen waren in allen 16 Gesamtläufen nachgefragt (festes Verhalten, kein Zufall). Auswertung je Fall: `aufgaben/audit/nachgefragt_auswertung.md`.
- **Behoben** (deterministisch, mit Fundstelle): P-40 Privatfeier (R-40, R-133; `app/privat_begriffe.json`), P-14 Bandleader (R-31; `app/verwerter_nummer.json`), P-20a Übungsleiterpauschale mit Gesamtbetrag (`app/pflichtangaben.py`), P-02 Webdesign mit Programmierung (R-142, R-184; `zuordnung.ergaenze_taetigkeit`: Einordnung aus Bezeichnung + Text nur mit Vorrang laut Excel UND gleicher Wahl des Modells). Live je 6 Läufe: P-20a, P-40 6/6; P-02, P-14 5/6 (Rest vorsichtig). Gesamtlauf 5dd83af: 76 / 12 / 0 / 0.
- **Offen (eigene Schritte):** Musikvereine P-16, P-17 – R-57 (vereinseigene Dirigenten bleiben außer Betracht) fehlt im Kern; den Verein nur als Veranstalter zu erkennen, ergäbe bei P-16 eine FALSCHE Abgabepflicht, deshalb nicht geändert. Grundsatzfragen ohne Betrag P-36 (Vertretung; `kern.vertreter` wird vom Chatbot nie aufgerufen), P-37 (Nachweismakler; R-35 fehlt im Kern).
- **Für den Steuerberater:** P-18a/B-06 – Kern (R-53/R-54) fragt nach, Testfall erwartet „nicht abgabepflichtig bis 20 Schüler“: was gilt? P-09 – gilt „bezahlte selbständige Künstler“ bei Veranstaltungen ohne nähere Leistung als künstlerisch?
- Bewusst vorsichtig und unverändert: P-11, P-13 (Soll selbst „unsicher“), S-10, S-16, S-20 (Prüfliste 1, F-02/F-05/F-07), F3 (Rückfrage nach Eigenwerbung bei „Versicherungsunternehmen mit Marketing“).

## Musikvereine, Grundsatzfragen ohne Betrag, Härtetest HT-2026-001 (14.10.2026)
- **Musikvereine (P-16, P-17):** R-57 im Kern (`kern/rechnen.py`, Ausschlussgrund „vereinseigene_leitung“: vereinseigene Chorleiter/Dirigenten bleiben bei Schwelle und Bemessungsgrundlage außer Betracht; KSK-Info 12, Abschn. 4, S. 3–4). Hobby-/Laienmusikvereine werden als Generalklausel erkannt (nur mit Verein UND Freizeit-Hinweis; R-30, R-159; `app/verein_begriffe.json`), „mit Eintritt“ als Einnahme (`app/einnahme_begriffe.json`). Bei höchstens drei Veranstaltungen keine Frage mehr nach der Einnahmeabsicht (KSVG § 24 Abs. 2 S. 3 Nr. 1 – Wortlaut geprüft). Drei bestehende Tests, die das alte Fragen festhielten, auf mehr als drei Veranstaltungen umgestellt (Begründung im Test). Live P-16, P-17 je 6/6.
- **Grundsatzfragen ohne Betrag (P-36, P-37):** Vertretung „im Namen und für Rechnung“ eines Künstlers → `kern.vertreter` (R-33, KSVG § 25 Abs. 3); fehlt die Angabe, fragt das System, ob der Vertragspartner selbst abgabepflichtig ist. Nachweismakler (R-35) → neue Kern-Funktion `nachweismakler` (Grenzfall). Erkennung `app/vertretung_begriffe.json`; Systemfelder `vertretung_kuenstler`, `nachweismakler` setzt nur das System.
- **Härtetest HT-2026-001 (Nutzer):** vorher 1 von 6 FALSCH (Durchleitung und Privatzahlung still mitgezählt). Behoben mit `zuordnung.zahlungsweg_im_freitext` (`app/zahlungsweg_begriffe.json`) und ohne Rechtsform-Frage bei offenem Zahlungsweg; live 6/6. Auswertung `aufgaben/audit/haertetest_ht_2026_001_auswertung.md`; Fragen Q-15 bis Q-17 an den Steuerberater.
- **Fund (live, 615dffa): W-05** – das Modell las „1.500 $“ nicht aus; das System fragte allgemein nach dem Betrag statt nach dem Euro-Betrag (keine falsche Zahl). Behoben in `markiere_fremdwaehrung`.

## Unabhängige Gegenrechnung gebaut (15.10.2026) – Teil 1e
Auftrag: `aufgaben/PROMPT_ClaudeCode_Chatbot_1e_Pruefsandbox.md`. Gebaut: `verifier/` (eigener Rechenweg mit exakten Brüchen, kein Import von `kern`), `app/sandbox.py` (eigener Prozess), `app/gegenrechnung.py` (Mitschnitt und Vergleich), Einbau in `app/router.py::_nach_bestaetigung`. Abweichung = keine Antwort („Prüfung fehlgeschlagen“).

Befunde aus dem Abgleich Kern ↔ Gegenrechnung (Zufallsfälle, 3 × 6.000 Aufrufe):
1. **Kern-Fehler, behoben** (`kern/rechnen.py::analysiere_rechnung`): Eine Rechnungsposition **ohne** oder mit **unbekannter** Rolle zählte still mit 0, ohne Rückfrage – gegen den eigenen Grundsatz „Fehlende Angaben → Rückfrage, nie geraten“. Erreichbar war das, weil `app/pflichtangaben.py` bei der Rechnungsanalyse nur Positionen verlangt, keine Rolle je Position. Folge vorher: „Abgabepflichtig“ mit zu niedriger Bemessungsgrundlage möglich. Jetzt wie „klaeren“ (offen, Rückfrage). Test: `tests/test_kern.py::test_rechnungsposition_ohne_einordnung_wird_nachgefragt`. Keine Testfall-Soll betroffen (H-01 bis H-04 haben alle Rollen).
2. **Gegenrechnung korrigiert, nicht der Kern:** Säumniszuschlag mit mehreren Rückständen bis 2022. Meine erste Fassung nach R-226 ergab „abgabepflichtig“ mit der Additionsmethode. Die Testfälle L-10 und L-11 (Excel, Entwurf) verlangen aber „Grenzfall“, weil das BSG-Urteil Gesamtsozialversicherungsbeiträge betrifft und die Übertragung auf die Künstlersozialabgabe eine Ableitung ist. Die Gegenrechnung folgt jetzt diesem dokumentierten Soll (Begründung im Code). Der Betrag war auf beiden Seiten gleich.
3. **Hinweis:** Der Docstring von `kern.rechnen.saeumniszuschlag` sagt „Bis 2022 wird vor der Abrundung addiert“ ohne zu erwähnen, dass das Ergebnis trotzdem ein Grenzfall ist (L-10/L-11). Nur Text, keine Rechnung.
4. **Registerprüfung** (`python -m verifier.pruefe_register`): 0 Fehler, 5 Hinweise. Pauschalen (Übungsleiter/Ehrenamt) stehen nur bis 2026 im Register: Anfragen zur Pauschale für 2027 ergeben „Nicht abgedeckt“. `schaetzung.ausland_prozent` gilt erst ab 2025, `veranstaltungen.ausnahme_max` erst ab 2023 (beides gewollt, laut Excel).

Bewusst nicht gebaut / offen:
- Die Zeitmessung je Schritt steht im Prüfprotokoll jeder Antwort (Kern, Gegenrechnung). Eine Zeitmessung für ALLE Schritte (Extraktion, Pflichtangaben, Quellenabruf, Antwort, Kontrolle) im anonymisierten Protokoll fehlt noch (Auftrag E.3, Teil).
- Rechnungsanalyse C.1 („Positionen ergeben …, Beleg nennt …“): Der Abgleich Teilbeträge ↔ Rechnungsbetrag geschieht weiter vor der Faktenbestätigung in `app/zuordnung.py::berechne_restpositionen` (Widerspruch → Rückfrage). Die Gegenrechnung rechnet danach jede Summe nach, zeigt aber keinen eigenen Satz „Positionen ergeben …“.
- Windows: keine Speichergrenze im Kindprozess (nur Zeitlimit). Job-Objekt wäre möglich, nicht gebaut.

## Korpus „Beispiele und Gegenbeispiele“, Modellunabhängigkeit, RAG-Korpus (15.10.2026)
Auftrag des Nutzers: alle Fehler beheben, unabhängig vom Sprachmodell; über 1.000 Beispiele und Gegenbeispiele; alle Tests protokollieren; auch den Quellenabruf (RAG) testen. Protokoll aller Läufe: `aufgaben/audit/TESTPROTOKOLL.md` (nur ergänzen), Ergebnisse je Fall: `tests/archiv/ergebnisse/*korpus*`, `*rag_korpus*`.
- **Korpus** `aufgaben/audit/korpus_beispiele.json` (Erzeuger `aufgaben/audit/korpus/erzeuge_korpus.py`): 1.822 Fälle in 911 Paaren, 19 Familien. Soll aus Regelregister und Regeln abgeleitet – **Entwurf, nicht vom Steuerberater geprüft**, deshalb NICHT im Testarchiv.
- **Drei Stufen ohne Sprachmodell** (`aufgaben/audit/korpus/lauf_offline.py`): `orakel` (fehlerfreie Fakten) 1.822/1.822 richtig. `gestoert` (18 typische Lesefehler eines Modells je Fall: Jahr, Betrag, Rechtsform, doppelte oder weggelassene Position, Einnahmeabsicht umgedreht …): Stichprobe jeder 5. Fall, 3.618 Läufe – FALSCH vorher 428, jetzt 0 (protokolliert, Stand 56a909e: 3.413 richtig, 205 Rückfrage, 0 falsch). `demo` (Heuristik ohne Schlüssel): 1.512 richtig, 310 Rückfrage, 0 falsch (vorher 38 falsch).
- **Behoben (Kern):** Vorauszahlung mit Rundungsrest (`kern/rechnen.py`, Monatsrate aus einer Division).
- **Neue Wächter** (`app/zuordnung.py`, Begriffe in JSON, Tests `tests/app/test_korpus_waechter.py` mit eigenen Gegenbeispielen): doppelte Positionen, Jahr nur aus dem Text, Veranstaltungszahl aus dem Text, widersprochene Einnahmeabsicht, verneinter Nachweis, Gesamtbetrag mit Rolle (nur als ganzes Wort: „gema“ nicht in „gemacht“), widerlegte Rechtsform, vergessene Nebenkosten-Position („zusätzlich 150 € Fahrtkosten“). Jeder Wächter ändert nur, was der Text eindeutig sagt; sonst Rückfrage.
- **Fund beim Nachtest (behoben vor dem Commit):** Die ersten Fassungen der Rechtsform-Wächter löschten im Testprotokoll-Dialog (S6 „Kollege sagt Einzelunternehmerin, Rechnung sagt GmbH“) die Rechtsform, statt den Widerspruch mit zwei Knöpfen zu fragen; der Doppel-Wächter kürzte bei einem Text ohne Betrag. Eingegrenzt, Tests unverändert grün.
- **Sprachmodell wechseln** (`app/llm/anbieter.py`, `app/README.md`): Mistral, jedes OpenAI-kompatible Modell (ChatGPT, lokales DeepSeek über Ollama/vLLM, EU-Anbieter) und Anthropic. Anbieter außerhalb der EU nur mit Schalter `LLM_AUSSERHALB_EU_ERLAUBT=1` (Grundregel 8). Offline getestet: gleiche Modellantwort → gleiche Antwort des Chats über jeden Anschluss. **Live geprüft nur Mistral** (einziger Schlüssel); ChatGPT/DeepSeek/Claude live NICHT getestet.
- **RAG-Korpus** (`aufgaben/audit/korpus/rag_korpus.py`, 327 Fragen): vorher 271, jetzt 307 richtig. Behoben: „Abgabesatz“ fand die Verordnungen nicht (sie sagen „Prozentsatz“; Synonym in `app/rag/konfig.json`) 0/9 → 9/9; ein erfundenes Aktenzeichen lieferte andere Urteile 0/19 → 19/19 (jetzt „Nicht abgedeckt“); fachfremde Fragen („Hundesteuer in Köln“) bekamen Urteile 9/20 → 18/20 (Themenbezug: Fachwort-Liste plus Fachwörter, die in den KSK-Quellen deutlich häufiger sind als in HGB/EStG/SGB). Abruf-Güte unverändert 86,6 % (Ziel 90 % weiter nicht erreicht), Gegenproben 6/10 → 9/10.
- **Offen:** 18 Regeln werden über ihre Voraussetzung nicht geliefert (z. B. R-08 „Varieté- und Zirkusunternehmen, Museen“: Wörter zu kurz/zu allgemein); 2 fachfremde Fragen mit Fachwort („KI-generierte Bilder“, „Elterngeld für Selbständige“) bekommen weiter Quellen. Kurze Wörter (≤ 7 Buchstaben) werden ohne Endung gesucht („Verlag“ findet „Verlage“ nicht) – nicht geändert, weil es die Güte-Messung verschieben würde; Vorschlag für später.
- **Demo-Modus (ohne Schlüssel), Korpus-Lauf 15.10.2026:** 38 FALSCH – die Demo-Heuristik las Beträge mit vorangestellter Währung („EUR 536,69 brutto“) nicht. Behoben in `app/llm/fake.py` (Schreibweise wie im Router vereinheitlicht); F04, F09, F17 danach 0 FALSCH (F09 jetzt Grenzfall statt Ergebnis – vorsichtig).
- **Live im Chat (Browser, Mistral, jeder 10. Korpusfall, ef914a7):** 183 Fälle – 173 richtig, 9 Rückfrage/Grenzfall, **0 falsch**, 1 Fehler (KB-1421: Modellantwort nicht lesbar; das System bat um Wiederholung, keine Zahl). Befunde:
  - **Korpus-Fehler (behoben, Version 2):** KB-1081 u. a. hatten ein Honorar von „-50 €“ (Erzeuger: Schwelle minus 500 bei 450 €). 8 Fälle der Familie F09 neu erzeugt; F09 offline wieder 80/80 (orakel) und 0 FALSCH (gestört).
  - **Für den Steuerberater (offen, nicht geändert):** Fahrtkosten-Pauschale ohne Nachweis desselben Künstlers. Legt das Modell sie als eigene Position desselben Auftragnehmers an („Fahrtkostenpauschale ohne Nachweis“), ordnet das System sie als „nicht sicher einzuordnen“ ein (Tätigkeitskatalog: Nebenkosten/Auslagen T-67 „unsicher“) → Grenzfall. Mit perfekten Fakten (offline) zählt sie mit → abgabepflichtig. Frage: Zählt eine nicht nachgewiesene Fahrtkostenpauschale an den Künstler als Entgelt (KSVG § 25, R-47 nur für nachgewiesene Reisekosten) – dann sollte T-67 für Nebenkosten derselben Leistung nicht „unsicher“ sein? Die Entscheidung gehört in die Excel, nicht in den Code.
  - KB-0541 (Umsatzsteuer ausgewiesen): Rückfrage „Teilbetrag so hoch wie die ganze Rechnung“ – vorsichtig, keine falsche Zahl.
- **Live über den allgemeinen Anschluss** (OpenAI-kompatibel, wie für ChatGPT/DeepSeek; gegen die Mistral-Schnittstelle in der EU, 081cda9): 183 Fälle – 170 richtig, 10 Rückfrage/Grenzfall, **0 falsch**, 3 Fehler „Antwort nicht lesbar“ (eigener Mistral-Anschluss: 1). Ursache: Der eigene Anschluss verlangt im zweiten Versuch das strenge JSON-Schema, der allgemeine nur auf Wunsch. **Behoben:** strenges Schema jetzt Standard, mit automatischem Rückfall auf einfaches JSON, wenn ein Dienst es nicht kennt (HTTP 400/404/415/422; `app/llm/anbieter.json`); Test `tests/app/test_anbieter.py::test_strenges_schema_ist_standard_mit_rueckfall`. Ergebnis sonst gleich: dieselben Fälle Grenzfall (F09, s. o.), zusätzlich KB-1721 Grenzfall (Leistung „nicht eindeutig zuzuordnen“).
- **Nachtest allgemeiner Anschluss mit strengem Schema (0915ece):** 172 richtig, 10 Rückfrage/Grenzfall, 0 falsch, 1 Fehler (vorher 3; eigener Mistral-Anschluss: 1). Neuer Fund **KB-1641** (behoben): „Unsere Firma sitzt in 10115 Berlin, Telefon 030 1234567“ – das Wort „Telefon“ galt als Leistung (Nebenkosten, T-67 „unsicher“) → Grenzfall statt abgabepflichtig. Eine Telefonnummer direkt nach „Telefon/Tel./Fax/Mobil/Handy“ ist jetzt eine Kontaktangabe (`app/taetigkeit_erkennung.json`, `kontakt_woerter`); „Telefonkosten 120 €“ bleibt Nebenkosten. Tätigkeitskatalog-Vergleich (200 Tätigkeiten): keine Änderung.
- **Ganzer Korpus live (Mistral, Browser), Teile 1 und 2 (912 Fälle):** 885 richtig, 21 Rückfrage/Grenzfall, **0 falsch**, 6 Fehler „Antwort nicht lesbar“ (System fragte nach). Behoben:
  - **F04 „X brutto, darin Y Umsatzsteuer“** (16 unnötige Rückfragen): das Modell legte den Rest ohne Rechnungsbetrag an oder rechnete den Netto-Rest zusätzlich selbst aus. `zuordnung.berechne_restpositionen` übernimmt bei genau einer „darin“-Angabe den Rechnungsbetrag aus dem Text; einen selbst gerechneten Rest ersetzt der Kern. Tests `BruttoDarinUmsatzsteuer` (mit Gegenbeispiel: zwei „darin“-Angaben → Rückfrage).
  - **KB-0587 „Unsere Agentur für Öffentlichkeitsarbeit“** galt als Leistung (T-60) → Grenzfall. Muster `eigene_seite_davor` in `app/taetigkeit_erkennung.json`; „Wir haben eine Agentur für Öffentlichkeitsarbeit beauftragt“ bleibt T-60. Tätigkeitskatalog-Vergleich: keine Änderung.
  - Unverändert (vorsichtig): „Programmierung der Webseite“ → Grenzfall, wenn Modell und System verschieden einordnen. Offen: KB-0392 „Rückfrage nötig“ ohne angezeigte Frage (Ursache ohne Rohantwort nicht feststellbar).
- **Ganzer Korpus live, alle 4 Teile (1.822 Fälle):** 1.740 richtig, 71 Rückfrage/Grenzfall, **0 falsch**, 11 Fehler „Antwort nicht lesbar“. Teil 3 zusätzlich: 41 × F09 Fahrtkostenpauschale → Grenzfall (offene Frage an den Steuerberater, s. o.); **9 × F12** „Abgabesatz Künstlersozialabgabe 2031?“ → das Modell ließ das unbekannte Jahr weg, das System fragte nach dem Jahr. **Behoben** (`zuordnung.jahr_aus_freier_jahreszahl`): bei einer Auskunft gilt die eine genannte Jahreszahl auch ohne Registereintrag → „Nicht abgedeckt“. Bei einer Bewertung bleibt die Rückfrage (Gegenbeispiel im Test).

## Quellenabruf (RAG) auf 90 % gebracht (16.10.2026)
Auftrag des Nutzers: „besonders die RAG, es soll unser Ziel erreichen, 90 Prozent“. Abruf-Güte (`python -m app.rag.guete`, Treffer unter den ersten 5 Plätzen): **259 → 270 von 299 = 90,3 %** (erste Angabe 79,3 → 83,9 %). RAG-Korpus 307 → 310 von 327, Gegenproben 9 von 10. Je Schritt gemessen; was nicht half, ist wieder entfernt.
- **Fehler, behoben** (`app/quellen.py::_fassung_passt`, Index-Version 7): Regeln mit „Gilt für Fassung“ = „alle“ / „Jahresabhängig“ (R-20, R-21, R-89) und „A (bis 2022: nicht nur gelegentlich) / B (ab 2023)“ (R-115) wurden **nie geliefert** – das „nicht“ in „nicht nur gelegentlich“ galt als Verneinung. Verneint ist jetzt nur „nicht geprüft/verglichen/bestätigt/belegt“.
- **Für den Steuerberater (offen):** R-18 („Entgelt = alles, was … aufwendet“), R-19, R-27, R-36 stehen auf „aktuell“ (R-18: „andere Fassungen noch nicht verglichen“) und werden deshalb weiter **nie** geliefert. Soll dort „A und B“ (oder „B“) stehen? Entscheidung in der Excel.
- **Synonyme** (`app/rag/konfig.json`, `synonyme`): Alltagswörter zu den Wörtern der Quellen (Radiosender → Rundfunk, Museum → Museen, GEMA → Verwertungsgesellschaft, Gewinnanteil → Gewinnzuweisung, Gutschein → Sachleistung, Dollar → Umrechnung/Währung, Satz → Prozentsatz).
- **Ranglisten:** Urteile eigene Liste mit Gewicht 0,5 (voll, wenn die Frage nach Rechtsprechung fragt oder ein Aktenzeichen nennt); Wiederholungen derselben Stelle (Stand-/Archivfassung, Register-Zeilen derselben Regel) rücken nach hinten; Schlussvorschriften („tritt … in Kraft“) und reine Versicherten-Vorschriften rücken ans Ende, außer die Frage nennt sie; sehr lange Wörter werden nicht mehr auf 7 Buchstaben gekürzt („verwert*“ traf „Verwerter“).
- **Ehrlich:** Gemessen an denselben Testfällen, an denen die Einstellungen geprüft wurden – kein unabhängiger Nachweis. Die Gewichte sind empfindlich (kleine Änderungen verschieben die ersten fünf Plätze). Geprüft und verworfen: Nachsortieren nach Abdeckung, Verknüpfung Regel↔Quelle, Wortstämme für kurze Wörter, andere BM25-Gewichte, Mindestabdeckung je Liste.
- **Nicht lesbare Modellantworten (16.10.2026):** Die 12 Fälle mit „Antwort nicht lesbar“ aus den Live-Läufen je viermal nachgespielt (`Modellfehler suchen`, mit und ohne Quellenabruf): 46 von 48 richtig, 2 Fehler. Ursache beide Male: Schlüssel mit Hochkomma UND Wert im Namen („ein_auftragnehmer': true“). **Behoben** in `app/llm/mistral.py::_tippfehler_schluessel` (gilt für jeden Anbieter): steht dort ein einfacher JSON-Wert (true/false/null/Zahl/[]), gilt er für das Feld; alles andere bleibt ein Fehler (Test `test_schluessel_mit_hochkomma_und_wert`). Die übrigen 10 Fälle waren beim Nachspielen richtig – die Fehler sind selten und zufällig (Modell), keine Rechenfehler.
- **Live-Nachtest 16.10.2026 (f78c414, Mistral, 183 Fälle + 19 Dialoge):** 174 richtig, 9 Rückfrage/Grenzfall, **0 falsch, 0 Fehler** (vorher 1–3 nicht lesbare Antworten). Neuer Fund **KB-0491** (behoben): „darin EUR 104,50 Umsatzsteuer“ – die enthaltenen Beträge wurden an drei Stellen nur in ganzen Euro gelesen (104 statt 104,50), passten zu keiner Position → Rückfrage. Gemeinsame Funktion `zuordnung._davon_paare` mit Cent. F04 offline: gestört 996 → 1.035 von 1.080 richtig, 0 falsch.
- **Test des Nutzers im Codespace (16.10.2026):** Er schickte die vier Beispielfragen in EINER Nachricht. Der Chat behandelte alles als einen Fall und fragte nach der Art des Auftraggebers, obwohl „Werbung für unser eigenes Geschäft“ dastand (das Modell mischte die Fragen). **Behoben:** Ab drei Zeilen, die je mit einem Fragezeichen enden (`app/einstieg_begriffe.json`, `mehrere_fragen_ab`), bittet der Chat um eine Frage nach der anderen, ohne Modellaufruf. Zwei Fragen zum selben Fall bleiben erlaubt (Gegenbeispiel im Test).
- **Wunsch des Nutzers (16.10.2026): „der Chat soll alle Fragen beantworten, auch wenn ich sie zusammen sende“.** Umgesetzt in `app/warteschlange.py` (statt des Hinweises „eine Frage nach der anderen“): Eine Nachricht mit mindestens drei Fragezeilen wird zerlegt (`zuordnung.zerlege_fragen`), jede Frage ist ein eigener Fall (nichts wird vermischt). Fragen ohne Rückfrage erscheinen sofort untereinander („Frage 2 von 4: …“); braucht eine Frage eine Rückfrage oder die Faktenbestätigung, wartet der Rest und läuft nach Knopf/Bestätigung/getippter Antwort automatisch weiter. Die Faktenbestätigung vor jeder Rechnung bleibt.
- **Im selben Test gefunden, behoben:** (1) „Wie hoch ist die Hundesteuer in Köln?“ bekam den Begrüßungstext (das Modell nannte es „hinweis“). Eine echte Frage ohne Bezug zur Künstlersozialabgabe und ohne Betrag geht jetzt an den Quellenabruf → „Nicht abgedeckt“; kurze Begrüßungen (bis `hinweis_max_woerter` Wörter) bleiben ein Hinweis. (2) Demo-Modus: „Gibt es ein Urteil …?“ ohne Betrag ist eine Recherche, keine Bewertung. (3) Die irrelevanten Normen beim Urteil zu Werbeagenturen (KSVG § 27 Abs. 4, KSVGBeitrÜV § 2) kamen vom alten Stand im Codespace; mit dem neuen Quellenabruf nicht mehr.
- **Beobachtet, nicht geändert:** Auch die Auskunft „Abgabesatz 2025?“ zeigt erst „Jahr: 2025 – Stimmt das?“. Das ist die Faktenbestätigung vor jedem Zugriff auf das Register (Grundregel); bewusst nicht entfernt.
- **Zweiter Test des Nutzers (16.10.2026):** Ergebnis „Typischer Verwerter: keine Schwelle“ für „Wir sind eine Bäckerei und machen Werbung für unser eigenes Geschäft“ (Betrag zufällig gleich, Begründung falsch). Ursache: die Begriffsliste kannte „eigenes Unternehmen“, nicht „eigenes Geschäft“; den falschen Wert des Modells hielt nichts auf. **Behoben** in `app/verwerterart_begriffe.json` (gängige Wendungen für den eigenen Betrieb). Widerspricht das Modell (typischer Verwerter) dem Text (Eigenwerbung), fragt das System nach. Dass die übrigen Fragen nicht beantwortet wurden, lag sehr wahrscheinlich am alten Stand im Codespace (die Antwort zeigt keine Zeile „Frage 1 von 4“).

## Umbau Schritt 1: Fakten statt einer Kategorie (16.10.2026)
Anlass: Test des Nutzers („Bäckerei, Werbung für unser eigenes Geschäft“ → Begründung „Typischer Verwerter“) und seine Bedingungen für Schritt 1 (keine reine Branchenzuordnung, keine starre Entweder-oder-Kette, Textbelege schon jetzt, alte Kategorie nur ableiten, Tests fachlich prüfen).
- **Neue Faktenfelder** (`app/schema.py`): `unternehmensart` (Tätigkeit des Auftraggebers), `auftragszweck` (eigene Werbung / für Kunden / Veranstaltung / privat), `katalog_taetigkeit` (typischer Verwerter laut Tätigkeit) und `herkunft` je Feld (Text mit Zitat, Knopf, Modell, System). `katalog_taetigkeit` und `herkunft` setzt nur das System; Modellwerte dafür werden gelöscht (`zuordnung.ohne_systemfelder`).
- **Alte Kategorie nur noch abgeleitet** (`app/einordnung.py::leite_ab`): `verwerterart` folgt den Fakten, keine zweite Wahrheit. Ist ein Widerspruch offen oder fehlt der Zweck, bleibt sie leer → Rückfrage. Fehlende Fakten werden NICHT aus der alten Kategorie erfunden: eine Lesart des Modells ohne Textbeleg steht als „vom Sprachmodell gelesen – bitte prüfen“ in der Bestätigung.
- **Textbeleg mit Zitat** in der Faktenbestätigung, z. B. „Zweck dieses Auftrags: Werbung für das eigene Unternehmen (laut Ihrer Nachricht: „für unser eigenes Geschäft“)“. Ein Knopf oder eine bestätigte Antwort gilt als dokumentierte Quelle („von Ihnen gewählt“).
- **Widerspruch statt stiller Änderung:** Wählt der Nutzer einen Knopf, der seinem Text widerspricht (Bäckerei mit Eigenwerbung → „Typischer Verwerter“; Buchverlag → „Eigenwerbung“; Hochzeitsfeier → „Typischer Verwerter“), fragt das System gezielt: „Sie hatten geschrieben: „…“. Jetzt haben Sie „…“ gewählt. Welche Angabe stimmt?“ Bis dahin keine Bestätigung, keine Rechnung.
- **Mehrere Tatbestände nebeneinander:** `einordnung.tatbestaende` listet alle angezeigten (z. B. Verlag UND Eigenwerbung); entschieden wird nach der vorhandenen Regel (Katalog-Tätigkeit geht vor, R-07). Die vollständigen Zuordnungsregeln mit Voraussetzungen und Ausnahmen sind noch NICHT in der Excel – offen für den Steuerberater (Schritt 2).
- **Umsatzsteuer-Annahme sichtbar:** Die Bestätigung zeigt „Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer enthalten (falls doch, bitte die Angaben korrigieren)“, wenn keine Umsatzsteuer genannt ist.
- **Gegenprüfung bei Auskünften:** Bei einer reinen Auskunft (z. B. Abgabesatz 2025) heißt es nicht mehr „nachgerechnet“, sondern „ein zweites Mal aus dem Regelregister gelesen“ (`app/gegenrechnung.py`, `ZEILE_NACHGESCHLAGEN`).
- **Abnahme** (`tests/app/test_einordnung.py`, 17 Tests): Bäckerei mit Eigenwerbung (keine allgemeine Rückfrage, 73,50 €, genau 1.000 € nicht überschritten, widersprüchlicher Knopf, ohne Zweck → Rückfrage), Verlag mit Eigenwerbung, Agentur mit Kundenauftrag, privater Auftrag, alte Kategorie nur abgeleitet, Zusatzfrage ändert das Falljahr nicht.
- **Korpus erneut ausgewertet (offline):** Orakel 1.822/1.822, Demo 1.594 richtig / 228 Rückfrage / **0 falsch**, gestört 3.445 / 173 / **0 falsch** – unverändert gegenüber vorher, kein Soll geändert.
- **Noch offen (Schritt 2):** Rückfragen in Alltagssprache („Wofür war der Auftrag?“) statt der Kategorie-Knöpfe; Bestätigung als ganzer Satz; Zuordnungsregeln als Entwurf in die Excel (neue Zeilen).
- **Modellfehler F04 ausgewertet (KB-0491/0521/0541/0551, je 2 × mit/ohne Quellenabruf):** Zwei Ursachen. (1) Das Modell legte den ganzen Bruttobetrag als Umsatzsteuer an und ließ den enthaltenen Betrag weg → Rückfrage „Teilbetrag so hoch wie die ganze Rechnung“. **Behoben** (`zuordnung.fehlender_enthaltener_teil`): steht genau ein „X … darin Y“ im Text und fehlt Y, wird Y mit der Rolle seines Beleg-Worts als eigene Position ergänzt – sichtbar in der Faktenbestätigung, nichts geschätzt. Dafür das Soll von `test_teilbetraege_live` (P-28, 14.10.2026: „Rückfrage, nicht erfinden“) geändert, Begründung im Test; Gegenprobe ohne Betrag im Text bleibt Rückfrage. (2) „Werbung für **mein** eigenes Unternehmen“, „werben … für unser eigenes **Haus**“ wurden nicht als Eigenwerbung erkannt (feste Wendungen). **Behoben** mit einem Muster in `app/verwerterart_begriffe.json` (`_eigenwerber_muster`: Werbewort UND „für mein/unser … eigenes …“ im selben Satz; „für unsere Kunden“ und „für meine eigene Hochzeit“ treffen bewusst nicht). Nachgespielt: alle 16 aufgezeichneten Modellantworten jetzt richtig (vorher 6 Rückfragen).
- **Live-Test von Schritt 1 nicht abgeschlossen (16.10.2026):** Im ersten Lauf (a274351) waren die ersten 107 Fälle 104 richtig, 3 Rückfrage, 0 falsch; ab KB-1071 lehnte Mistral jede Anfrage ab. Grund (jetzt im Bericht sichtbar, `chatbot_direkt.py` schreibt die Gründe aus dem Lückenprotokoll des Servers): **„402 Payment Required“** – das Guthaben/Kontingent des Mistral-Kontos ist aufgebraucht. Kein Code-Fehler; der Schlüssel ist gültig (Modellliste abrufbar). **Der Nutzer muss das Konto unter console.mistral.ai prüfen.** Danach den Live-Lauf wiederholen.
- **Nebenbefund, behoben:** `aufgaben/audit/mistral_test.py` (Workflow „Mistral-Test“) brach seit Teil 1f bei jeder Frage mit TypeError ab (Messhilfe reichte die Argumente json_objekt/schema nicht durch).
- **Gesperrter Zugang verständlich gemeldet (16.10.2026, Test des Nutzers im Codespace):** Bei HTTP 401/402/403 vom Sprachmodell sagte der Chat „Bitte stellen Sie Ihre Frage erneut“ – das hilft nicht. Jetzt fester Text „Der Zugang zum Sprachmodell ist gerade gesperrt (zum Beispiel Guthaben aufgebraucht oder Schlüssel ungültig) …“ (`app/router.py`, `ZUGANG_GESPERRT_RUECKFRAGE`; `LLMFehlgeschlagen.status`). Überlastung (429/503) bleibt wie in Befund M6 (Wiederholung, danach allgemeiner Text). Test `tests/app/test_zugang_gesperrt.py`. Demo-Modus trotz gesetztem Schlüssel: `LLM_ANBIETER=demo bash scripts/start_codespace.sh`.
- **Mistral wieder frei (17.10.2026), Small-Stichprobe:** `mistral-small-latest`, jeder 50. Korpusfall: 32 richtig, 3 Rückfrage, **0 falsch**, 2 nicht lesbar. Ursache der 2: Small schrieb ein ganzes JSON-Stück in einen Schlüssel (`positionen": [{…}]`). **Behoben** in `app/llm/mistral.py::_tippfehler_schluessel` (gilt für jeden Anbieter): ergibt `{"` + Stück + `}` gültiges JSON aus noch nicht gesetzten Schema-Feldern, gilt es; sonst bleibt es ein Fehler. Die Reparatur läuft jetzt vor den Positionsprüfungen. Test `test_json_stueck_im_schluessel` (mit Gegenbeispiel).
- **Vergleich Small/Large (17.10.2026, Korpus jeder 10. + Dialoge, bc2641b):** Small 166/11/**0**/6 in 553 s, Large 168/9/**0**/6 in 1.639 s (Large-Fehler: 6 × HTTP 429, Ratenbegrenzung des Kontos). Testfall 20 Positionen: Small 10/11/**0**/0 (10.10.: 8 FALSCH), Large 18/3/0/0.
- **Rückfrage ohne Frage (Small, Testfall 20, auch Ursache des älteren KB-0392-Musters):** (1) Das Modell meldete `unbekannt: ["auftragnehmer_typ"]`, obwohl der Text die Rechtsform nennt → „ausdrücklich unbekannt“ → keine Frage, keine Rechnung. **Behoben:** `zuordnung.unbekannt_nur_mit_beleg` – „unbekannt“ gilt nur, wenn der Nutzertext es sagt (`fallstand.unbekannt_im_text`). (2) Feste Rechtsform-Erkennung: „haben wir **eine** selbständige Einzelperson beauftragt“ galt als eigene Seite; „Aktiengesellschaft“ fehlte. **Behoben** in `app/rechtsform_erkennung.py` (Akkusativ eine/einen/ein als Empfänger-Marke; ausgeschriebene Kapitalgesellschaften). Gegenbeispiele „Wir sind eine GmbH/Aktiengesellschaft …“ bleiben eigene Seite. Tests `tests/app/test_small_befunde.py`. Mit den echten Small-Antworten nachgespielt: Faktenbestätigung statt leerer Rückfrage.
- **Entscheidung des Nutzers (17.10.2026): nur noch Mistral, Standard Mistral Small.** Entfernt: Anschlüsse OpenAI-kompatibel und Anthropic (`app/llm/anbieter.py`, Tests, Workflow-Eingaben `anbieter`/`eigener-server`); in der Git-Geschichte bis 7777681. Geblieben: Demo-Modus (feste Regelerkennung, kein KI-Anbieter) für Tests und Notbetrieb. Standardmodell steht in `app/llm/anbieter.json` (`mistral_modell`), nicht mehr im Code; Workflows nutzen `mistral-small-latest`. **Die Einstellung bleibt auf Large, bis das ganze Testarchiv mit Small 0 FALSCH hat** (CLAUDE.md).
- **Testarchiv mit Small: 5 FALSCH, Ursachen behoben:** (1) AT-2026-010 Sportverein, AT-2026-033 Fotostudio, P-16 Hobbyorchester-Verein: Small las „typischer Verwerter“ ohne Begriff im Text UND zugleich einen anderen Zweck (Veranstaltung, eigene Werbung) – daraus wurde die Katalog-Tätigkeit (ohne Schwelle). `einordnung.erfasse`: widerspricht der vom Modell gelesene Zweck seiner unbelegten Kategorie, gilt der Zweck (Bedingung 4: keine Fakten aus der bloßen Kategorie). Ohne gelesenen Zweck bleibt Regel M4. (2) AT-2026-029 „monatlich 500 EUR, 12 Monate“: Small legte eine Position an; `anzahl_je_betrag` erkennt jetzt auch Zeiträume (`app/anzahl_begriffe.json`, `zeit_einheiten`/`je_einheit`). (3) HT-2026-099 „…an einen Kuenstler gezahlt, 2026, GmbH.“: Small schrieb die GmbH als Tätigkeit des Unternehmens statt als Rechtsform des Auftraggebers; `rechtsform_nur_wo_genannt` berücksichtigt jetzt beides. Tests in `tests/app/test_small_befunde.py`.
- **Ganzer Korpus mit Small (52ee640): 30 FALSCH, zweites Testarchiv (ebea088): 5 FALSCH.** Behoben (Tests `tests/app/test_small_befunde.py`, Klasse `KorpusMitSmall`): (1) F16 „an die VG Bild-Kunst 1.950 EUR“ – `zuordnung.vg_als_empfaenger` setzt die Rolle Verwertungsgesellschaft, wenn der Text die Zahlung ausdrücklich an sie richtet (`app/rollen_belege.json`, `_vg_als_empfaenger`); Gegenbeispiel „die GEMA-Gebühren übernimmt er“ bleibt unverändert. (2) F04 Brutto als Gesamtbetrag ohne die enthaltene Umsatzsteuer – `fehlender_enthaltener_teil` macht aus dem Gesamtbetrag X eine Position und ergänzt Y. (3) P-10 „Konzertdirektion“ fehlte in der Begriffsliste der typischen Verwerter (Quelle: KSK-FAQ „Konzert- und Gastspieldirektionen“, Auslegung der KSK); ergänzt. (4) HT-2026-099 nachgestellte „, GmbH.“ in einem Satz mit „an einen Künstler“: beschreibt den Absender (`rechtsform_erkennung`, Personenwörter aus `vertretung_begriffe.json`).
- **Nicht durch Wortregeln lösbar (Small deutet anders als das Soll):** P-12 Firmenjubiläum mit Kunden (Small: Veranstaltung; Soll: Eigenwerbung), AT-2026-007 „Agentur (GmbH) … Werbespot“ (Small: eigene Werbung; Soll: typischer Verwerter), W-07 Fremdwährung (sichere, aber falsche Rückfrage). Large liest diese Fälle richtig.
- **Entscheidung des Nutzers (17.10.2026): Mistral Small ist Standard, Large wird nicht mehr verwendet.** Der Nutzer kannte den Prüfstand (Testarchiv mit Small 5 FALSCH, Korpus 30 FALSCH; Ursachen behoben, offline 0 FALSCH, live noch nicht bestätigt). `app/llm/anbieter.json` steht auf `mistral-small-latest`; Workflows und Testskripte ebenso. Bestätigungsläufe mit Small (Testarchiv, ganzer Korpus) auf dem neuen Stand eingereicht.
- **Rechnungen prüfen (17.10.2026, Wunsch des Nutzers: „der Nutzer will vielleicht nicht chatten, nur Rechnungen hochladen und prüfen“).** Pull Request #1 (Dokumentenmodus von ChatGPT/Codex, ohne Sprachmodell) übernommen und eingebaut: **eine Oberfläche mit Menü links „KSK-Chat“ (/) und „Rechnungen prüfen“ (/rechnungen)**, gemeinsame App (`app/main.py` hängt `app/dokument_app.py` ein), Startskripte starten beides. Neu: **KI-Unterstützung beim Lesen** (`app/dokument_ki.py`): Python liest das Dokument, Mistral ordnet nur den gelesenen Text zu Positionen; jeder Betrag muss im Dokument stehen; Abgleich mit der Regel-Erkennung (grün „KI und Regeln einig“, gelb „nur KI – bitte prüfen“, nur Regeln = Hinweis); Umsatzsteuer nur als Hinweis; abschaltbar je Upload und in `app/dokument_config.json`. **Jahresübersicht:** mehrere Rechnungen in einem Jahresfall, Spalte „Rechnung / Belegstelle“, CSV für den Steuerberater; Summen rechnet nur der Kern. Befund beim Einbau: die Markierung je Position darf kein Feld der Position sein (das Formular lehnt unbekannte Felder ab) – getrennte Liste `pruefung`.
- **Live-Test „Rechnungen prüfen“ mit KI (17.10.2026, 2 von 4 richtig) – drei Fehler im System, behoben:** (1) `app/dokument_config.json` `summenzeile`: „Gesamtbetrag“, „Gesamtsumme“, „Rechnungssumme“, „Endsumme“ fehlten (`gesamt\b` trifft „Gesamtbetrag“ nicht) – die Regel-Erkennung schlug den Bruttobetrag als Position vor. (2) `app/textnorm.py::waehrung_nach_hinten`: eine Währung am Zeilenende galt als vorangestellt für die Zahl der nächsten Zeile („1.200,00 EUR\n2 Illustrationen“ → 1.200 € weg, 2 € neu); betraf auch mehrzeilige Chat-Nachrichten. Jetzt nur innerhalb einer Zeile, und eine Währung direkt hinter einem Geldbetrag gehört zu diesem („2026 EUR 900“ bleibt 900 €). (3) `app/dokument_ki.py`: nur die Umsatzsteuer wird nicht als Position übernommen; über andere Kosten (Fahrtkosten, Material) entscheidet das Regelwerk.
- **Korpus mit Small, 2. Lauf (17.10.2026, 56307c5): 11 FALSCH, alle F04.** Datei `app/zuordnung.py`. Problem: bei „654,50 € brutto, darin 104,50 € Umsatzsteuer“ legte Small die ganze Rechnung (Bezeichnung „Umsatzsteuer“), die Umsatzsteuer UND einen selbst gerechneten Nettobetrag (550 €, steht nicht im Text) an; der Kern rechnete den Rest der Rechnung ebenfalls – Bemessungsgrundlage 1.100 statt 550 €. **Behoben** (0232a1a): `modellgerechneter_rest` entfernt bei genau einem „X … darin Y“ eine Position, deren Betrag nicht im Text steht und genau X − Y ist; Bezeichnung und Tätigkeit gehen auf die Rechnungsposition über. Ein Betrag aus dem Text wird nie entfernt. Tests `ModellGerechneterNettobetrag` (KB-0489, KB-0502 nachgebildet, schlagen ohne die Prüfung fehl; Gegenbeispiel). Offline-Korpus unverändert 0 FALSCH; Live-Bestätigung: Lauf korpus-voll-small-3.
- **Korpus mit Small, 3. Lauf (17.10.2026, 0232a1a): 0 FALSCH** (1.692/85/0/45). Offene Befunde, alle „nicht auswertbar“ statt falsch: Small liefert öfter ungültiges JSON (unerlaubte Werte für `verwerterart`/`auskunft_thema`, verschachtelte oder abgebrochene Antworten, erfundene Schlüssel wie `veranstaltungszahl_unbekannt_aber_angegeben`). Vorschlag: unerlaubten Aufzählungswert verwerfen (Feld bleibt leer, dann Rückfrage) statt die ganze Antwort; nie raten. Zwei Antworttexte mit abgeschnittenem Paragrafen hielt die Antwortprüfung richtig an.
- **Schritt 2 (17.10.2026): Rückfragen nach Tatsachen.** Umgesetzt wie im Arbeitsstand beschrieben (792fb2c). Befunde dabei: (1) `app/router.py::_aktualisiere_feld` nahm über `POST /knopf` auch Felder an, die nur das System setzt (`katalog_taetigkeit`, `herkunft`), und eine Position −1 (= letzte); jetzt abgelehnt. (2) `app/einordnung.py::erfasse` übernahm einen vom Modell gelieferten anderen Zweck über eine Knopf-Auswahl hinweg; jetzt bleibt die Auswahl. (3) Die Testläufer klicken für gespeicherte Fälle mit der alten Kategorie den Zweck-Knopf derselben Einordnung (`einordnung.KATEGORIE_ZU_ZWECK`; „Typischer Verwerter“ → „Werbung oder Öffentlichkeitsarbeit für Kunden“) – Testfälle unverändert.
- **Testarchiv mit Small nach Schritt 2 (17.10.2026):** Lesart von Small schwankt zwischen Läufen (A-999: dreimal Rückfrage, dann falsch – auf dem alten Code). Fest abgefangen: `anzahl_je_betrag` ‚<N>mal … jede Rechnung <Betrag>‘ (P-04a), `vg_als_empfaenger` Betrag vor ‚an die GEMA‘ (AT-2026-039). **Offen, Vorschlag zur Entscheidung:** Zweck nur vom Modell vermutet (kein Wort im Text, z. B. ‚30-Jahr-Feier … Firmenveranstaltung‘ → Veranstaltung) immer per Rückfrage bestätigen lassen (AT-2026-004, A-999, P-12, AT-2026-007).
