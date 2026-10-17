# Auftrag Chatbot Teil 1f: Rechtsform je Position, Säumniszuschlag, Auskunftsfragen, Fundstellen, Schaltflächen

**Entwurf – vom Steuerberater zu prüfen.** Gilt `CLAUDE.md` (11 Regeln) und `aufgaben/SYSTEMBESCHREIBUNG_fuer_KI.md`. Arbeitsbereich: **nur `app/` und `tests/app/`**. Fehler anderswo (Kern, Excel, Quellen) nicht beheben, sondern in `aufgaben/FUNDE_Chatbot.md` melden (Datei, Stelle, Problem, Vorschlag). Vorher: `git pull`, `aufgaben/Arbeitsstand.md` und `aufgaben/FUNDE_Chatbot.md` lesen.

## Hintergrund
Ein Test, bei dem Claude das Sprachmodell spielte (Fakten von Hand, Rest echt), hat Fehler in der App-Schicht gefunden. Excel und Kern sind in diesen Fällen richtig. Dieser Auftrag behebt nur die App-Schicht. Die Beschreibung steht in `aufgaben/PERSONA_Steuerberater_Test.md` (Abschnitt „Claude als Sprachmodell").

## Abnahme (muss zuerst gelesen werden)
`python aufgaben/audit/abnahme_teil1f.py` ist **vor** dem Bau geschrieben. Ausgangszustand: **18 Lücken**. Ziel: **0 Lücken**. Das Skript legt die Schnittstellen fest (Feldnamen unten). Es ist die Messlatte; ändere es nicht, um es grün zu machen. Wenn du eine Schnittstelle anders bauen willst, sag es im Bericht und bitte um Anpassung des Skripts. Zusätzlich: jede Zeile des Skripts als Unittest in `tests/app/test_teil1f.py` übernehmen (auch die Fälle, die schon „ok" sind).

## A. Rechtsform je Position (wichtigster Punkt)
Heute gilt `auftragnehmer_typ` global; bei gemischten Positionen wird eine GmbH-Position mitgezählt (BG 9.300 € statt 4.300 €).
1. `Position` bekommt `auftragnehmer_typ: Optional[AuftragspartnerTyp]`. Es gilt je Position; fehlt es, gilt der globale Wert von `Fakten.auftragnehmer_typ` als Vorgabe. Der Router (`_kern_positionen`) leitet den Empfänger pro Position ab, der Kern rechnet bereits pro Position (`empfaenger`).
2. Ist für eine Position weder ein eigener noch ein globaler Typ bekannt: Ergebnisklasse „Rückfrage nötig", die Rückfrage nennt die Position (Bezeichnung oder „Position 2"). Nie raten.
3. Die **Faktenbestätigung** zeigt die Rechtsform je Position („Position 3: 5.000,00 € (honorar), GmbH/UG/AG"). Der Hash der Fakten umfasst die Rechtsform je Position.
4. Die Antwort nennt die ausgeschlossene Position und den Grund. Der Kern liefert den Satz „Nicht zur Bemessungsgrundlage: … (Zahlung an Kapital-/Handelsgesellschaft, R-138, R-216)"; die App muss ihn durchreichen, nicht ersetzen.
5. Das Schema-Feld muss auch im Sprachmodell-Prompt (Mistral) und in `llm/fake.py` bekannt sein; das Modell setzt es nur, wenn der Nutzer es sagt, sonst `null`.

## B. Säumniszuschlag
Heute steht „Abgabepflichtig (Vorschlag) … Abgabe beim Abgabesatz 5 %". Das ist falsch benannt.
1. Der Baustein `ABGABESATZ` und der Satz „Abgabe beim Abgabesatz …" kommen nur bei Abgabe-Berechnungen (Bemessungsgrundlage mal Satz), nie beim Säumniszuschlag.
2. Der Säumniszuschlag erscheint als „Säumniszuschlag (Vorschlag): 80,00 €" mit Rückstand, Monaten und Fundstelle aus dem Kern. Die Zahl kommt aus `kern.rechnen.saeumniszuschlag`.
3. Das Wort „Abgabepflichtig" erscheint dort nicht. Die Ergebnisklasse darf eine zusätzliche Anzeigeklasse sein (Vorbild: `RECHTSPRECHUNG_GEFUNDEN` in `app/ergebnisklassen.py`), z. B. „Berechnung (Vorschlag)". Intern bleibt die Kernklasse im Protokoll. Dokumentiere die Wahl in `FUNDE_Chatbot.md`, damit der Nutzer sie freigeben kann (CLAUDE.md, Regel 5).

## C. Auskunftsfragen (neue Anfrageart `auskunft`)
Fragen wie „Wie hoch ist der Abgabesatz 2024?", „Ab wann gilt die Schwelle?", „Wann ist die Meldefrist?" hatten keinen Weg.
1. `Anfrageart` bekommt `"auskunft"`, `Fakten` das Feld `auskunft_thema: Optional[Literal["abgabesatz","schwelle","meldefrist","aufbewahrung","pauschale"]]`.
2. Router-Zweig: **die Antwort kommt aus dem Kern** (`kern.rechnen.abgabesatz`, `schwelle`, `meldefrist`, `aufbewahrung_bis`, bzw. die Register-Helfer `reg/wert/werte`), niemals aus dem Sprachmodell und niemals als Festwert im App-Code. Zahl, Datum und Fundstelle setzt das System über Platzhalter ein (Bausteinmechanismus aus 1d, keine Ausnahme).
3. Jahr fehlt → „Rückfrage nötig" (nur nach dem Jahr). Kein Wert im Register für das Jahr (`RegisterLuecke` oder `None`) → „Nicht abgedeckt (Quelle fehlt)", keine Zahl.
4. Für `pauschale`: nur beantworten, wenn der Kern einen Zugriff hat; sonst „Nicht abgedeckt" und in `FUNDE_Chatbot.md` melden, dass ein Kernzugriff für Pauschalen nötig ist.
5. Neue Ergebnisklasse für erteilte Auskunft nach dem Vorbild von Punkt B (z. B. „Auskunft aus dem Regelwerk"). Schlusssatz „Entwurf – vom Steuerberater zu prüfen" und die Antwort-Kontrolle gelten wie überall.

## D. Fundstellen mit richtigem Jahr
`app/quellen.py` zeigt bei Veranstaltungen 2025 „… (Kopie 2022-01-22)", und `fassung_fuer_jahr` hat `jahr <= 2022` fest im Code (Verstoß gegen Regel 2).
1. Die Fassung kommt aus Excel/Register über den Kern (`kern/parameter.json`), nicht aus dem App-Code. Kein Festwert wie 2022 in `app/`.
2. Bei der Auswahl der Quelle für eine Fundstelle: Das Jahr der Anfrage entscheidet. Eine Kopie mit älterem Stand wird nicht als Fundstelle für ein späteres Jahr genannt, ohne den Vorbehalt „Stand der Quelle: …" (Archivdatum ist nicht der Rechtsstand).
3. Wenn nur eine ältere Kopie vorhanden ist: nennen, aber mit Hinweis. Wenn keine passt: „Nicht abgedeckt (Quelle fehlt)". Details der echten Quellensuche macht Teil 2 (RAG); hier nur die Fehler beheben.

## E. Rückfragen als Schaltflächen
`Antwort` bekommt `rueckfrage_optionen: list[dict]`, je Eintrag `{"frage": str, "optionen": [str, ...]}`.
1. Geschlossene Fragen bekommen feste Optionen: Einnahmeabsicht → `["ja","nein"]`; Rechtsform → die Werte aus `AuftragspartnerTyp` mit lesbaren Namen (mindestens 3).
2. `static/index.html` zeigt die Optionen als Knöpfe; ein Klick schickt die Antwort wie getippt. Die Auswahl bleibt Nutzerinput (Daten), nicht Anweisung.
3. Offene Fragen (z. B. Jahr, Betrag) bleiben Texteingabe.

## F. Pflichtangaben je Rechenart
`Vorauszahlung` ohne Vorjahres-BG fragt heute zuerst „Stimmt das?" statt nach dem Fehlenden.
1. Vor der Faktenbestätigung prüft jede Rechenart ihre eigenen Pflichtangaben (Vorauszahlung: Jahr, BG Vorjahr; Säumnis: Rückstand, Monate; usw.). Fehlt etwas: nur danach fragen. Keine Fragen, die diese Rechenart nicht braucht (Rechtsform, Leistungsart).
2. Gleiches für `auskunft`: Jahr und Thema.

## G. Nicht ändern
Grenzen aus 1c/1d/Nachtrag 1+2 (Antwort-Kontrolle, Platzhalter, Faktenbestätigung, Wortlisten) bleiben. Alle bisherigen Tests und `python aufgaben/audit/gegenproben_teil1d_runde3.py` (0 Lücken) müssen grün bleiben. Keine Rundung der Abgabe, keine Zahl mit mehr als zwei Nachkommastellen (Regel 7). Kein Festwert im App-Code (Regel 2): Zahlen, Jahre, Fassungen, Sätze, Fristen kommen aus Kern/Excel.

## H. Abschluss
1. `python aufgaben/audit/abnahme_teil1f.py` → **Lücken: 0**; `python aufgaben/audit/gegenproben_teil1d_runde3.py` → 0; `python scripts/pruefe_alles.py` (mit installierten Paketen, inkl. `tests/app`) → ALLES GRÜN.
2. Neue Dateien prüfen: liegen sie wirklich im Repo (`.gitignore`)? `git push origin main`, danach in `origin/main` nachsehen.
3. `aufgaben/Arbeitsstand.md` aktualisieren; ins Projekt „ksk" schreiben (`claude/ksk-assistent-arbeitsstand.md`).
4. Kurzbericht: geänderte Dateien, Testzahl, Abnahme-Ergebnis, Befunde, was nicht geht. Nichts schönreden. Auch: Welche Ergebnisklassen wurden zusätzlich eingeführt (B, C)?

## I. Ergänzung aus dem Mistral-Test (Befunde M1–M3 in `aufgaben/PRUEFBERICHT_Mistral_Lauf1.md`)
Der Test mit dem echten Modell (`aufgaben/audit/ergebnisse_mistral.md`, Rohfakten je Frage) zeigt Fehler im Fakten-Ziehen. Zusätzlich zu A bis H:
1. **Keine Rechtseinstufung durch das Modell.** Der Extraktions-Prompt (`app/llm/mistral.py`) muss ausdrücklich verbieten, ohne ausdrückliche Aussage des Nutzers zu setzen: `auftraggeber_typ`, `auftragnehmer_typ` (auch je Position), `verwerterart`, `kuenstlerisch`, `agentur_abgabepflichtig`, `empfaenger_abgabepflichtig`, `einnahmeabsicht`. Dazu `leistungsart`: nur eine genannte Leistung, nie den Platzhalterwert „honorar". Beispiele aus dem Test: „Werbeagentur" ist nicht „GmbH"; „Verein mit vier Konzerten" ist keine Einstufung „typischer Verwerter"; „GmbH-Studio" bedeutet Rechtsform je Position, nicht `kuenstlerisch=False`. Alles Unbekannte bleibt `null` und wird zur Rückfrage.
2. **„Davon" nicht doppelt zählen.** Der Prompt erklärt: „X Euro, darin Y Euro …" ergibt Positionen (X minus Y) und Y, nicht X und Y. Zusätzlich eine deterministische Plausibilitätsprüfung in `app/` (keine Festwerte): Nennt die Frage einen Gesamtbetrag und weicht die Summe der Positionen davon ab, zeigt die Faktenbestätigung eine deutliche Warnung („Die Summe der Positionen (2.100,00 €) passt nicht zum genannten Gesamtbetrag (1.800,00 €)"). Das Feld dafür (`gesamtbetrag_genannt: Optional[Decimal]`) setzt das Modell nur, wenn der Nutzer einen Gesamtbetrag nennt.
3. **Kein Absturz bei unbrauchbarer Modellantwort.** Liefert das Modell kein gültiges JSON (z. B. weil Text der Frage als Anweisung gelesen wurde), fängt die App das ab und antwortet „Rückfrage nötig" mit fester Bitte, die Frage neu zu stellen. Kein `JSONDecodeError`, kein HTTP 500. Ein Unittest mit einem Modell, das Freitext statt JSON liefert; ein zweiter, bei dem das Modell JSON mit unbekannten Feldern oder falschen Typen liefert (Pydantic-Fehler).
4. Tests: die Prompt-Verbote als Offline-Test (der Prompt enthält die Verbote, ohne Netz); Plausibilitätswarnung; Absturzschutz. Das Ergebnis des Mistral-Workflows wird nach 1f von mir erneut geprüft (Ziel: keine Ausnahme, keine erfundene Einstufung).
5. **Mistral-Adapter robust machen** (Befunde M6 in `aufgaben/PRUEFBERICHT_Mistral_Lauf1.md`, Lauf 2 mit Large 4). In `app/llm/mistral.py`:
   a) `top_p: 1` mitschicken (Large 4 lehnt `temperature=0` sonst mit HTTP 400 ab).
   b) `content` kann ein Text oder eine Liste von Blöcken sein; bei einer Liste nur die Blöcke vom Typ `text` zusammensetzen.
   c) Wartezeit einstellbar über Umgebungsvariable (z. B. `MISTRAL_TIMEOUT`), Standard bleibt 30 s.
   d) Jede unbrauchbare Modellantwort (kein JSON, Pydantic-Fehler, Zeitüberschreitung, HTTP-Fehler) führt zu einer festen Rückfrage oder „Dienst gerade nicht verfügbar", nie zu einem Absturz oder einem HTTP 500.
   e) Offline-Unittests mit gefälschten Antworten für a bis d. Das Modell wird weiter über `MISTRAL_MODELL` gewählt; kein Modellname im Code festschreiben, außer dem bestehenden Standardwert.

## J. Oberfläche (Befunde aus dem ersten Test im Codespace, Bild vom 09.10.2026)
Der Chatbot läuft im Codespace (Demo-Modus). Drei Fehler in `app/static/index.html` und im Router:
1. **Schaltfläche unter einer Rückfrage sendet den Fragetext als Antwort** und löst dieselbe Rückfrage erneut aus (Schleife). Nur geschlossene Fragen (`rueckfrage_optionen`, Abschnitt E) bekommen Knöpfe, und der Klick sendet die **Option** (z. B. „ja"), nicht den Fragetext. Offene Fragen (Jahr, Betrag) bekommen keinen Knopf; stattdessen bleibt das Eingabefeld, optional mit passendem Platzhaltertext. Für die Jahresfrage dürfen Auswahlknöpfe der **im Regelwerk vorhandenen Jahre** angeboten werden (aus Excel/Kern gelesen, keine Jahreszahlen im Code).
2. **Formatierung wird nicht dargestellt**: `**fett**` und `*kursiv*` erscheinen mit Sternchen. Die Oberfläche setzt diese beiden Auszeichnungen und Zeilenumbrüche sicher um, **ohne** HTML aus dem Text zu übernehmen (nur `textContent`/Escaping, keine `innerHTML`-Übernahme von Modell- oder Nutzertext; Schutz vor Einschleusung bleibt).
3. **Begrüßung/Smalltalk** („hallo", „danke", „was kannst du?"): feste Systemantwort ohne Modell und ohne Pflichtangaben-Frage, mit Kurzbeschreibung (was das System kann, Entwurf-Hinweis) und 2 bis 3 Beispielfragen. Keine Ergebnisklasse „Rückfrage nötig" dafür; eine eigene Anzeige „Hinweis". Die Erkennung darf nicht auf Wortlisten im Modelltext beruhen, sondern auf einem festen Anfragetyp `hinweis` im Schema (das Modell setzt ihn nur, wenn die Eingabe keinerlei Sachfrage enthält).
4. Kopfzeile: langer Modusname bricht um oder kürzt mit „…" statt über den Rand zu laufen.
5. Tests: Unittest für Knopf-Verhalten (Option statt Fragetext, soweit ohne Browser testbar: der Router bekommt die Option als Antwort und beantwortet die Rückfrage), Unittest für das Escaping (HTML im Text bleibt Text), Unittest für die Begrüßung. Zusätzlich ein Browser-Test mit Playwright im GitHub-Lauf (Chromium ist dort verfügbar): Seite öffnen, „hallo" senden, Begrüßung sichtbar, keine Sternchen im Text.
