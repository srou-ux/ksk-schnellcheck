# Auftrag: Befunde aus dem ersten Prüfkatalog-Lauf mit Mistral (10.10.2026)

Entwurf – vom Steuerberater zu prüfen. Grundlage: GitHub-Lauf „Prüfkatalog" Nr. 38056745573, Berichte `aufgaben/audit/pruefkatalog_ergebnis_{small,medium,large,roh-small,roh-large}.md`. Stand Code: `9552b19` (Livetest-Befunde behoben).

Arbeitsbereich: `app/` und `tests/app/`. Liegt eine Ursache im Kern oder im Regelkatalog: in `aufgaben/FUNDE_Chatbot.md` melden, nicht selbst ändern (Ausnahme: ausdrücklich unten genannt). Erfolgskriterium: `python scripts/pruefe_alles.py` „ALLES GRÜN", alle bisherigen Abnahmen 0 Lücken, und `python aufgaben/audit/pruefkatalog_lauf.py --llm fake` ohne neue FALSCH-Fälle gegenüber `aufgaben/audit/pruefkatalog_ergebnis_demo.md`.

## Ergebnis des Laufs (Kurzfassung)
| Lauf | RICHTIG | NACHGEFRAGT | FALSCH | FEHLER |
|---|---|---|---|---|
| Mistral small im Assistenten | 22 | 26 | 3 | 0 |
| Mistral medium im Assistenten | 4 | 46 | 1 | 0 |
| Mistral large im Assistenten | 0 | 0 | 0 | 51 |
| Mistral small roh (ohne Assistent) | 14 | 0 | 35 | 2 |
| Mistral large roh (ohne Assistent) | 13 | 2 | 29 | 7 |

## M1 (dringend): Antwort auf eine Rückfrage wird mit Mistral nicht übernommen – Schleife
- K-04: „…für eigene Werbung…" → Rückfrage „Art des Auftraggebers" → Nutzer antwortet „Es ist Eigenwerbung." → wieder dieselbe Rückfrage. Gleiches Muster in P-01, P-02, P-12, P-21, P-29 bis P-31, P-38, P-39 (small) und fast allen Fällen bei medium.
- Ursache (vermutlich): Die Antwort läuft wieder durch `extrahiere_fakten`; der Extraktions-Prompt verbietet `verwerterart` ohne ausdrückliche Aussage, und das Modell wertet auch „Es ist Eigenwerbung" nicht als solche. Zusätzlich wird „(Einzelperson)" in der Frage nicht als Rechtsform übernommen, sodass eine zweite Rückfrage offen bleibt.
- Soll:
  1. Antworten auf **geschlossene Rückfragen** (Schaltflächen) werden **deterministisch** dem Feld zugeordnet, ohne Modell: Die Oberfläche schickt Feld und Wert mit (z. B. `{"feld": "verwerterart", "wert": "eigenwerber"}`), der Router übernimmt sie in die Fakten der Sitzung. Freitext-Antworten dürfen weiter über das Modell laufen, dann aber zusammen mit den bereits bekannten Fakten der Sitzung (nicht neu von vorn).
  2. Bereits bestätigte oder per Knopf gesetzte Felder gehen bei der nächsten Extraktion nicht verloren.
  3. Rechtsform-Synonyme („Einzelperson", „Einzelunternehmer", „freiberuflich") deterministisch erkennen (wie im Demo-Modus), wenn das Modell sie nicht setzt.
  4. Tests: Dialog Frage → Rückfrage → Knopf → Faktenbestätigung, mit einem Testdoppel, das `verwerterart` nie setzt; höchstens eine Rückfrage je Feld.

## M2: Mistral large – jede Antwort scheitert (Codeblock um das JSON) – ERLEDIGT durch Claude (Prüfer) am 10.10.2026
- Umgesetzt: `app/llm/mistral.py::_json_aus_antwort` (entfernt nur die Verpackung, Schema-Prüfung bleibt), Tests `tests/app/test_mistral_codeblock.py`. Nichts mehr daran tun; nur nicht wieder entfernen.
- Alle 51 Fälle: „Die Antwort des Sprachmodells konnte nicht verarbeitet werden." Diagnose aus früheren Läufen (`ergebnisse_mistral_1g_large-2512.md`): Rohantwort beginnt mit drei Backticks und `json`.
- Soll: In `app/llm/mistral.py` vor `json.loads` einen umschließenden Markdown-Codeblock entfernen; zusätzlich `response_format: {"type": "json_object"}` für die Extraktion prüfen (Mistral-Doku), sofern das Modell es unterstützt. Test mit einer Rohantwort im Codeblock.

## M3 (fachlich, kritisch): Verlag mit „eigener Werbung" wird mit Schwelle geprüft
- P-06: Buchverlag lässt für 300 € Flyer für die eigene Werbung gestalten → System: Eigenwerbung → „Nicht abgabepflichtig" (300 € unter 1.000 €). Soll laut Testfall C-11 (Checkliste Verlage, R-180, R-131): **abgabepflichtig**, für typische Verwerter gilt keine Schwelle, auch nicht bei Eigenwerbung.
- Die Rückfrage fragt nach der Art des **Auftrags** (Eigenwerbung / Verwerter), entscheidend ist aber zuerst die Art des **Unternehmens**. Soll: Ist das Unternehmen typischer Verwerter, darf Eigenwerbung nicht zur Schwellenprüfung führen. Prüfen, ob die Weiche im Router (`_rufe_kern_auf`) oder im Kern liegt; liegt sie im Kern, in `FUNDE_Chatbot.md` melden. Test: Verlag + eigene Werbung + 300 € 2026 → abgabepflichtig, 14,70 €.

## M4: Modell setzt `verwerterart` gegen den Wortlaut
- P-04b: „…für unsere eigene Werbung…" → Mistral setzt „typischer Verwerter" → „Abgabepflichtig" (Soll: nicht abgabepflichtig, 800 € ≤ 1.000 €). Die Faktenbestätigung zeigt das zwar, aber das Modell darf diese Einstufung laut Prompt gar nicht setzen.
- Soll: Wie bei `auskunft_thema` (`app/zuordnung.py`) eine deterministische Gegenprobe: `verwerterart` vom Modell nur übernehmen, wenn die Nutzertexte einen passenden Begriff enthalten (Begriffsliste in einer Konfigurationsdatei, nicht im Code); sonst verwerfen und nachfragen.

## Nicht in diesem Auftrag (zur Kenntnis)
- Kern: Subsumtionszeile ohne deutsches Zahlenformat; § 54 erscheint auch für 2026 (aus dem Livetest, bereits in `FUNDE_Chatbot.md`).
- Viele Fallgruppen (Bandleader, Vermittler, Musikschule, Übungsleiter, GEMA, Privatperson) enden mit Rückfrage, weil der Kern dafür noch keine Rechenlogik hat. Das ist kein Fehler, sondern Ausbau (später).

## Nachher
Prüfkatalog im Demo-Modus laufen lassen und den Bericht `aufgaben/audit/pruefkatalog_ergebnis_demo.md` erneuern; Arbeitsstand ergänzen; Kurzbericht. Den Mistral-Lauf startet der Prüfer.

## M5 (fachlich, kritisch, neu nach M1 – 10.10.2026): „Veranstalter (Generalklausel)" wird wie Eigenwerbung gerechnet
- Gefunden mit dem Prüfkatalog, der jetzt wie ein Nutzer die Knöpfe drückt (`knoepfe` in `pruefkatalog.json`). P-08: Unternehmen, 2025, drei Veranstaltungen, 5.000 €, Einnahmeabsicht ja → Knopf „Veranstalter (Generalklausel)" → **„Abgabepflichtig"**. Soll laut D-03: **nicht abgabepflichtig** (bei der Generalklausel zählen Entgelte aus Veranstaltungen erst ab der vierten Veranstaltung, § 24 Abs. 2 Satz 3 Nr. 1 KSVG, R-149).
- Ursache: `app/router.py::_rufe_kern_auf`, Zweig `if fakten.positionen:` – bei `verwerterart == "generalklausel"` ruft er `K.pruefe_positionen(..., typischer_verwerter=False)` auf, also die Eigenwerbungs-Logik (Schwelle, Stichwort „eigenwerb"). Einnahmeabsicht und Zahl der Veranstaltungen werden nicht geprüft; die Fundstelle nennt die Eigenwerbung.
- Soll:
  1. Bei `generalklausel` ist `einnahmeabsicht` Pflicht (Rückfrage mit Knopf ja/nein; ohne Einnahmeabsicht keine Abgabepflicht nach der Generalklausel, vgl. F-05).
  2. Bei `generalklausel` muss geklärt sein, ob die Entgelte aus Veranstaltungen stammen und wie viele es im Jahr waren (Rückfrage). Mit Veranstaltungen → `K.veranstaltungen(...)`. Ohne Veranstaltungen (z. B. Fotos zur Lizenzierung, P-07) → passende Kernfunktion der Generalklausel; gibt es keine, „Nicht abgedeckt" statt Eigenwerbungs-Logik und in `FUNDE_Chatbot.md` melden.
  3. Nie die Eigenwerbungs-Logik oder -Fundstelle für `generalklausel` verwenden. Test: P-08 → nicht abgabepflichtig; P-09 (vier Veranstaltungen) → abgabepflichtig 250,00 €; Generalklausel ohne Einnahmeabsicht → Rückfrage.
- Zweites Beispiel zu M5 (Mistral large, Lauf 38070498025, P-07): Fotos zur Lizenzierung, „keine Veranstaltungen", Einnahmeabsicht ja → das Modell setzt `veranstaltungszahl = 0` → `K.veranstaltungen(..., 0, ...)` → **„Nicht abgabepflichtig"** (Soll: abgabepflichtig, 150,00 €). Die Ausnahme „bis zu drei Veranstaltungen" gilt nur für Entgelte **aus** Veranstaltungen; null Veranstaltungen heißt nicht „befreit". `veranstaltungszahl == 0` darf nie in die Veranstaltungs-Ausnahme führen.

## M6 (neu, 10.10.2026): Mistral-Ratenbegrenzung führt zu „Antwort konnte nicht verarbeitet werden"
- Lauf 38070498025: bei large 30 von 51 Fällen nach je 0,2–0,4 s „konnte nicht verarbeitet werden", vereinzelt auch bei small/medium (K-01, P-36, P-18a, P-37). Das Muster (sehr schnell, in Serie, wenn mehrere Läufe parallel laufen) spricht für HTTP 429 (zu viele Anfragen) von Mistral.
- Soll: In `app/llm/mistral.py::_aufruf` bei HTTP 429 und 503 bis zu drei Wiederholungen mit wachsender Wartezeit (z. B. 1, 3, 9 s; Wert `Retry-After` beachten, falls gesendet); Zahl und Wartezeiten als Umgebungsvariablen mit Standardwert, nicht fest im Code. Die Fehlermeldung an den Nutzer bleibt gleich, aber das Protokoll nennt den HTTP-Status. Test mit einem Testdoppel, das zweimal 429 und dann eine gültige Antwort liefert.

## M7 (neu, Prüfung von M5 am 10.10.2026): richtige Zahl, falsche Begründung bei Generalklausel ohne Veranstaltungen
- Die Behebung von M5 übergibt dem Kern bei `veranstaltungszahl == 0` die Ersatzzahl `_KEINE_VERANSTALTUNGSAUSNAHME_ANZAHL = 1_000_000` (`app/router.py`). Ergebnis und Abgabe stimmen (P-07: abgabepflichtig, 150,00 €), aber die Antwort begründet: **„Mehr als drei Veranstaltungen und Summe über der Schwelle."** – obwohl es keine Veranstaltung gab. Eine falsche Begründung ist für den Berufsträger ein Fehler, weil er das Ergebnis nachvollziehen und vertreten muss. Außerdem ist die Ersatzzahl ein Festwert mit erfundener Bedeutung.
- Soll: Ersatzzahl entfernen. Die Generalklausel ohne Veranstaltungen braucht im **Kern** eine eigene Prüfung (Einnahmeabsicht + Summe über der Schwelle des Jahres, Fundstelle § 24 Abs. 2 Satz 1 Nr. 2, Satz 2 KSVG) mit eigener, zutreffender Subsumtion. Das ist eine Kernänderung: Auftrag dafür ausdrücklich erlaubt für `kern/rechnen.py` und `tests/test_kern.py` (Schwelle aus dem Register, kein Festwert; Wächter-Test muss grün bleiben). Bis dahin lieber „Rückfrage/Grenzfall" als eine falsche Begründung.
- Der Prüfkatalog prüft das jetzt mit (`verboten_text` bei P-07).
