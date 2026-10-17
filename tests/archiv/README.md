# Testarchiv des KSK-Assistenten

Hier liegen **alle Testfälle des Chatbots mit dem richtigen Ergebnis (Soll)** an einer Stelle, dazu die **Ergebnisse aller bisherigen Läufe**. Zweck: Wird das Sprachmodell gewechselt (z. B. ein neues Mistral-Modell), lässt sich mit einem Lauf prüfen, ob das SaaS damit genauso gut oder besser arbeitet.

Nur erfundene Daten. Kein Soll ist vom Steuerberater freigegeben. Die Spalte `sicherheit` je Fall sagt, woher das Soll stammt.

## Was liegt hier

| Datei | Inhalt |
|---|---|
| `alle_faelle.json` | Alle Einzelfälle (zurzeit 180): Frage, Soll-Ergebnis, Soll-Zahlen, Antworten auf Rückfragen (`knoepfe`, `nachtrag`), höchstens nötige Rückfragen. Erzeugt aus den Katalogen in `aufgaben/audit/`. |
| `dialoge.json` | Dialogtests (mehrere Nachrichten nacheinander) mit dem Soll je Schritt. |
| `dialoge_soll.json` | Soll der Dialoge, von Hand gepflegt. |
| `versionen.jsonl` | Jede Fassung jedes Falls mit Datum und Fingerabdruck. Hier wird nur ergänzt: Ändert sich ein Fall, kommt eine neue Version hinzu, die alte bleibt. |
| `ergebnisse/*.csv` | Ergebnis jedes Laufs je Fall: Datum, Modell, Code-Stand, Soll, Ist, Urteil (RICHTIG / NACHGEFRAGT / FALSCH / FEHLER). Dateiname: `Datum_Katalog_Lauf_Stand.csv`. |

Nicht hier, aber auch Tests:
- die Kern-Testfälle in `regelwerk/Testfaelle_BSG_Urteile.xlsx` und `regelwerk/testfaelle_maschinenlesbar.json`. Sie prüfen den Rechenkern ohne Sprachmodell und ändern sich bei einem Modellwechsel nicht.
- die Regressionstests in `tests/app/`. Sie laufen offline mit nachgebildeten Modellantworten.

Beide laufen in `python scripts/pruefe_alles.py`.

## Ein neues Modell prüfen

1. GitHub → Actions → **Testkatalog** → Run workflow.
2. Katalog `tests/archiv/alle_faelle.json` stehen lassen und bei **modell** den Namen eintragen, z. B. `mistral-medium-latest`.
3. Der Lauf rechnet alles dreimal: im Demo-Modus, im SaaS mit dem neuen Modell und mit dem Modell allein, ohne SaaS (zum Vergleich). Die Ergebnisse landen als CSV in `tests/archiv/ergebnisse/`.
4. Vergleichen, nach `git pull`, unter Windows im Projektordner:

   ```
   python scripts/vergleiche_ergebnisse.py tests/archiv/ergebnisse/ALT.csv tests/archiv/ergebnisse/NEU.csv
   ```

   Das zeigt, welche Fälle besser oder schlechter geworden sind. Gibt es einen **neuen FALSCH- oder FEHLER-Fall**, meldet das Programm „NICHT EINSETZBAR“.

Regel für einen Wechsel: **0 FALSCH**, und nicht weniger RICHTIG als mit dem bisherigen Modell. Die Antworten des Modells schwanken etwas von Lauf zu Lauf. Deshalb gilt: einen Fall, der sich ändert, einmal wiederholen, bevor man entscheidet.

## Was tun, wenn das neue Modell etwas falsch macht

1. **Das Soll bleibt fest.** Es wird nie geändert, nur damit ein Test grün wird. Ist ein Soll selbst falsch, entscheiden das der Nutzer oder der Steuerberater, und es entsteht eine neue Version des Falls.
2. **Korrigiert wird das SaaS, nicht der Test:** Prüfregel, Erkennung oder Anweisung an das Modell. Dabei gilt: mit Fundstelle, mit einem neuen Regressionstest in `tests/app/` und mit `python scripts/pruefe_alles.py` grün.
3. **Danach das ganze Archiv neu laufen lassen.** Eine Korrektur darf keinen anderen Fall verschlechtern.
4. **Erst bei 0 FALSCH und nicht weniger RICHTIG als vorher** wird das neue Modell Standard (`app/llm/mistral.py`, `aufgaben/audit/mistral_modell.txt`).

Auftrag an Claude dafür, ein Satz genügt: „Teste das Modell X auf dem Testarchiv, vergleiche mit dem Ausgangswert und korrigiere die Fehler.“

## Neue Testfälle aufnehmen

1. Den Fall in einen Katalog in `aufgaben/audit/` eintragen. Für einen neuen Katalog: in `scripts/erzeuge_testarchiv.py` unter `KATALOGE` ergänzen.
2. `python scripts/erzeuge_testarchiv.py` ausführen und committen.

`python scripts/pruefe_alles.py` meldet einen Fehler, solange ein geänderter oder neuer Fall nicht im Archiv ist.

## Kann man ein Modell damit „trainieren“?

Ja, aber mit zwei Einschränkungen.

1. **Das SaaS braucht kein Training.** Das Modell zieht nur die Fakten aus dem Text (Beträge, Leistungen, Rechtsform). Rechnen und Entscheiden tun der Kern und die Regeln aus der Excel. Ein neues Modell wird deshalb zuerst **geprüft**, nicht trainiert. Meist reicht das.
2. **Prüffälle nie zum Training verwenden.** Ein Modell, das genau diese Fälle gelernt hat, besteht den Test auch dann, wenn es neue Fälle falsch macht. Der Test wäre dann wertlos. Soll später doch trainiert werden (Feintuning, falls der Anbieter es in Europa anbietet; vorher prüfen), dann:
   - die Fälle aufteilen, z. B. 80 % Training und 20 % Prüfung, die das Modell nie sieht;
   - als Trainingsziel die **richtigen Fakten** je Frage verwenden (Frage → richtiges Fakten-JSON), nicht das Endergebnis. Diese richtigen Fakten gibt es heute noch nicht für jeden Fall; sie müssten erst erstellt und geprüft werden;
   - nur erfundene Daten verwenden, nur bei einem Anbieter in Europa.

## Bestand

Stand 11.10.2026:
- Prüfkatalog: 52 Fälle (40 Fallgruppen und Kontrollfälle).
- Testfall 20 Positionen: 21 Fälle.
- Alltagsfälle F1–F4: 4 Fälle.
- 2 Dialoge (Testprotokoll 11.10.2026 mit 9 Schritten, Livetest 2 mit 8 Schritten).

Ergebnisse vorhanden für mistral-small, mistral-medium und mistral-large-latest (im SaaS und roh) sowie für den Demo-Modus.

**Ausgangswert für künftige Vergleiche** (ganzes Archiv, 77 Fälle, Code-Stand `acd85a8`, 11.10.2026):

| Lauf | richtig | nachgefragt | falsch | Fehler | Datei |
|---|---|---|---|---|---|
| SaaS mit mistral-large-latest | 52 | 25 | **0** | 0 | `ergebnisse/2026-10-11_archiv_saas-mistral-large-latest_acd85a8.csv` |
| mistral-large-latest allein (ohne SaaS) | 21 | 5 | 49 | 2 | `ergebnisse/2026-10-11_archiv_roh-mistral-large-latest_acd85a8.csv` |
| Demo-Modus (ohne Modell) | 52 | 24 | 1 | 0 | `ergebnisse/2026-10-11_archiv_demo_acd85a8.csv` |

Ein neues Modell wird gegen die erste Zeile verglichen.
