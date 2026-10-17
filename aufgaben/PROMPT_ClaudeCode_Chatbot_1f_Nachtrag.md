# Auftrag Chatbot Teil 1f, Nachtrag: falsche Zuordnung durch das Modell, Rückfragen ohne Modell

**Entwurf – vom Steuerberater zu prüfen.** Gilt `CLAUDE.md` und `aufgaben/SYSTEMBESCHREIBUNG_fuer_KI.md`. Arbeitsbereich: **nur `app/` und `tests/app/`** (und `.github/workflows/pruefen.yml`, um den neuen Abnahmetest aufzunehmen). Fehler anderswo nach `aufgaben/FUNDE_Chatbot.md`. Vorher `git pull`.

## Hintergrund
1f ist abgenommen (`abnahme_teil1f.py`: 0 Lücken). Der Mistral-Lauf danach (`aufgaben/audit/ergebnisse_mistral.md`, Modell Small, Adapter ohne Umgehung) zeigt: Der Adapter ist robust (keine Ausnahme, 0,8 s je Aufruf), die Rechtsform je Position und die Fahrtkosten werden richtig gezogen. Aber die neuen Anfragearten werden vom Modell **falsch zugeordnet** und Rückfragen werden vom Modell **frei geschrieben**:
- Fall 1 („… Ist das abgabepflichtig?") → `auskunft` ohne Thema → Rückfrage „Worüber möchten Sie Auskunft?" (falsch).
- Fall 8 („Ist ein Auftrag an einen Texter abgabepflichtig?") → `auskunft` mit erfundenem Thema `abgabesatz`.
- Fall 9 (Verein, vier Konzerte, 3.500 €) → `hinweis` → der Nutzer bekommt eine Begrüßung statt einer Antwort.
- Rückfrage-Texte vom Modell: erfundene Fragen („einmalige oder wiederkehrende Zahlung?"), kaputte Sätze („Fassung B des 2024"), falsche Summe 9.300,00 € inklusive GmbH-Position.
- Fall 3: Rechtsform wird auch für die Fahrtkosten-Position erfragt.
- Fall 6: trotz bekannter Rechtsform je Position wird nach der Leistungsart gefragt und nicht gerechnet.

## Abnahme
`python aufgaben/audit/abnahme_teil1f_nachtrag.py` (vor dem Bau geschrieben, Ausgangszustand **7 Lücken**, Ziel **0**). Nicht ändern, um es grün zu machen. Jede Zeile zusätzlich als Unittest in `tests/app/test_teil1f_nachtrag.py`. Der Workflow `pruefen.yml` bekommt einen Job dafür (blockierend).

## A. Zuordnung der Anfrageart absichern (deterministisch, nicht vom Modell abhängig)
1. `auskunft` gilt nur, wenn die Nutzerfrage **selbst** ein Auskunftsthema nennt. Prüfung im Router gegen eine Begriffsliste je Thema aus einer **Konfigurationsdatei** (z. B. `app/auskunft_begriffe.json`: Abgabesatz, Satz, Prozent; Schwelle, Geringfügigkeit, Bagatellgrenze; Meldefrist, melden, Frist; Aufbewahrung; Pauschale, Ehrenamt, Übungsleiter). Das vom Modell gelieferte Thema zählt nur, wenn ein Begriff dazu in der Frage steht. Sonst: `auskunft` verwerfen und wie `bewertung` behandeln (Rückfrage nach den fehlenden Angaben für die Prüfung).
2. `hinweis` gilt nur, wenn die Eingabe **keine Sachangabe** enthält: keine Ziffer, keine Jahreszahl, kein Betrag und kein Fachbegriff aus der Begriffsliste (Konfiguration, kein Festwert im Code). Sonst `hinweis` verwerfen und als Sachfrage behandeln.
3. Der Extraktions-Prompt (`app/llm/mistral.py`) beschreibt `auskunft` und `hinweis` enger: `auskunft` nur bei einer Frage nach einem festen Wert (Satz, Schwelle, Frist …) ohne Rechnung; `hinweis` nur bei Gruß, Dank oder „was kannst du?". Eine Frage „Ist … abgabepflichtig?" mit Beträgen ist immer `bewertung`. Das ist ein Zusatz zum Schutz in 1, 2, nicht der Ersatz dafür.

## B. Rückfragen und Hinweise ohne Modell
1. Wenn das Ergebnis eine Rückfrage ist (fehlende Pflichtangaben, Jahr fehlt, Rechtsform je Position fehlt), baut das **System** die Antwort aus festen Textbausteinen (die Fragetexte stehen schon in `app/pflichtangaben.py`). **Kein Aufruf von `llm.formuliere_antwort`.** Dasselbe für `hinweis` (ist schon so).
2. Die Antwort besteht aus: Ergebnisklasse „Rückfrage nötig", einem festen Einleitungssatz, den Rückfragen als Liste (mit `rueckfrage_optionen` wie in E), Schlusssatz. Keine Summe und keine Fassungsangabe im Einleitungssatz, es sei denn, sie wird als Platzhalter vom System gefüllt und stimmt (nie eine Summe, die ausgeschlossene Positionen enthält).
3. Das gilt unabhängig vom Modell: Auch ein Modell, das beim Schreiben abstürzt (`NurFesteTexte` im Abnahmetest), darf keine Rückfrage verhindern.

## C. Rückfragen nur nach dem, was der Kern braucht
1. Die Rechtsform wird je **Honorar-/Entgeltposition** erfragt, nicht für Positionen mit den Rollen, die der Kern ohnehin gesondert behandelt (nachgewiesene Fahrtkosten, Bewirtung, USt, Verwertungsgesellschaft u. a. laut `kern.rechnen`-Vokabular). Welche Rollen das sind, wird aus dem Kern gelesen, nicht im App-Code aufgezählt.
2. Ist die Rechtsform **jeder** Honorarposition bekannt (je Position oder global), wird nicht mehr nach der Leistungsart gefragt, wenn der Kern sie für diese Berechnung nicht braucht. Prüfe im Kern, wann `leistungsart` wirklich benötigt wird; dokumentiere das Ergebnis in `FUNDE_Chatbot.md`. Der Fall „2025: Grafiker 2.400, Texterin 1.100, GmbH-Studio 5.000, Fotograf 800" muss mit bekannter Rechtsform je Position **rechnen** und 4.300,00 € nennen.

## D. Kleinigkeiten
1. Bei Säumniszuschlag steht in der Antwort „Abgabe: 80,00 €". Das soll „Säumniszuschlag: 80,00 €" heißen.
2. `app/schema.py::jahr_plausibel` hat die Festwerte 1980 und 2100. Die Grenzen kommen aus dem Regelwerk (frühestes und letztes Jahr der Excel-Blätter), nicht aus dem Code. Ist das nicht sinnvoll, nenne es in `FUNDE_Chatbot.md` und lass es.
3. Der Kern-Satz „Nicht zur Bemessungsgrundlage: 5000.00 €" (Punkt statt deutscher Schreibweise) ist ein Befund im Kern. Melde ihn in `FUNDE_Chatbot.md`; ich korrigiere ihn dort.

## E. Abschluss
`python aufgaben/audit/abnahme_teil1f_nachtrag.py` → 0 Lücken; `abnahme_teil1f.py` → 0; `gegenproben_teil1d_runde3.py` → 0; `python scripts/pruefe_alles.py` → ALLES GRÜN. Push, in `origin/main` prüfen, `aufgaben/Arbeitsstand.md` aktualisieren. Kurzbericht: Dateien, Testzahl, Abnahme, Befunde, was nicht geht.
