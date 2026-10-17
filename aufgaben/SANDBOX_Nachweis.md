# Sandbox-Nachweis (Chatbot Teil 1d, Nachtrag 2)

Datum: 2026-10-09 (UTC)
Commit: `494c639eefa4dbeb01a455fb40e955ce3e0bfbe0`
Repo: `https://github.com/srou-ux/ksk-assistent.git`, Branch `main`

## Vorgehen

Frischer Klon (nicht die Arbeitskopie dieser Sitzung) in ein temporäres Verzeichnis, neue
virtuelle Umgebung (Python 3.14.7), `pip install -r app/requirements.txt`, dann der volle
Testlauf -- genau der Ablauf aus `scripts/pruefe_sandbox.sh`/`.ps1`:

```bash
git clone https://github.com/srou-ux/ksk-assistent.git repo
cd repo && git checkout 494c639e...
python -m venv .venv && source .venv/Scripts/activate
pip install -r app/requirements.txt
PYTHONPATH=. python -m unittest discover -s tests/app -v
```

## Ergebnis

```
Ran 155 tests in 3.311s

OK (skipped=1)
```

155 Tests, 154 bestanden, 1 übersprungen (`test_mistral_rauchtest.py::TestMistralRauchtest`
-- erwartet, da `MISTRAL_API_KEY` nicht gesetzt ist; der Rest der Datei,
`TestMistralPromptOffline`, läuft ohne Netzwerk mit und bestand). Keine Fehler, keine
unerwarteten Überspringungen.

Zusätzlich im selben frischen Klon gegengeprüft:

- `python aufgaben/audit/gegenproben_teil1d_runde3.py`: **0 von 17 Lücken offen**, beide
  Kontrollfälle (q1, q2) gehen durch wie vorgesehen.
- `python scripts/pruefe_alles.py`: **ALLES GRÜN** (alle 7 Prüfschritte, inkl. des
  Prüfsummen-Schritts "Quellen unverändert" -- der in der lokalen Arbeitskopie dieser
  Sitzung einen Fehler meldet, siehe `aufgaben/FUNDE_Chatbot.md`, Abschnitt dazu. Dass der
  frische Klon hier fehlerfrei durchläuft, bestätigt: der Fehler liegt an einer lokalen
  Eigenheit dieser Arbeitskopie, nicht am committeten Stand.

## Welche Mutationen von welchen Tests gefangen werden

Jede der folgenden Mutationsproben schaltet im Testlauf **eine einzelne Prüfregel** ab
(`unittest.mock.patch.dict`) und verlangt, dass ein vorher blockierter Fall danach
durchkommt -- bleibt der Fall weiterhin blockiert, war die Regel nicht die fangende und der
Test schlägt fehl:

| Mutationsprobe (Datei) | Geprüfte Regeln | Mechanismus |
|---|---|---|
| `test_pruefung.py::TestMutationsprobe` | `app.pruefung.PRUEFSCHRITTE`: betraege, prozente, paragraphen, jahre, fassung, fundstellen, ebenen, schlusssatz (8) | baut `text`/`kontext` direkt (kein LLM/Baustein-Umweg) |
| `test_baustein.py::TestPruefeRohtextVerstoesse` | `app.baustein.ROHTEXT_PRUEFSCHRITTE`: alle 19 Einzelregeln | ruft jede Regelfunktion direkt auf |
| `test_gegenproben_2.py::TestMutationsprobeNachtragsregeln` | zahlwort, mengenangabe, normwort, gerichtswort, fassungswort, ergebnisaussage (6, Nachtrag 1) | end-to-end durch den vollen Router |
| `test_gegenproben_3.py::TestMutationsprobeNachtrag2Regeln` | gewissheitswort, bestaetigungswort, links_kontakt, html_tag, markdown_ueberschrift, geschweifte_klammer_uebrig (6, Nachtrag 2) | end-to-end durch den vollen Router |

Zusammen deckt das **alle** Einträge in `app.pruefung.PRUEFSCHRITTE` (8) und
`app.baustein.ROHTEXT_PRUEFSCHRITTE` (19) einzeln ab.

## Was nicht geht

- Der Prüfsummen-Fehler in der LOKALEN Arbeitskopie dieser Sitzung (siehe oben) ist nicht
  behoben, weil `quellen/` außerhalb des erlaubten Arbeitsbereichs liegt und als
  unveränderlich gilt -- dieser Sandbox-Nachweis zeigt aber, dass er den committeten Stand
  nicht betrifft.
- Wortlisten/Blocklisten (Nachtrag 2, Abschnitt C) sind grundsätzlich nie vollständig --
  siehe `aufgaben/FUNDE_Chatbot.md`.

---

# Nachweis Teil 1e: unabhängige Gegenrechnung (15.10.2026)

Entwurf – vom Steuerberater zu prüfen. Auftrag: `aufgaben/PROMPT_ClaudeCode_Chatbot_1e_Pruefsandbox.md`. Code-Stand `7329b98`.

## Gesamtlauf in sauberer Umgebung
- **GitHub „Prüfen“, Lauf 38702893512** (frischer Checkout, neue Python-Umgebung 3.11, Pakete aus `app/requirements.txt`): alle fünf Jobs grün (`alles` = `python scripts/pruefe_alles.py` mit Regelwerk, Quellen, Prüfsummen, Kern, Testfällen, allen Chatbot-Tests (lokal gezählt 676; das GitHub-Protokoll selbst ist aus dieser Umgebung nicht abrufbar), 31 Gegenrechnungs-Tests, Registerprüfung; dazu Gegenproben 1d, Abnahmen 1f, 1f-Nachtrag, 1g, Oberfläche mit Playwright).
- **Frischer Klon in dieser Sitzung** (nicht die Arbeitskopie, Python 3.13): `tests/verifier` 31 Tests OK; `python -m verifier.pruefe_register`: 0 Fehler, 5 Hinweise, danach Kern-Tests OK, Testfälle 94/94, Gegenrechnung OK. Eine neue virtuelle Umgebung mit `pip install` ging hier nicht (PyPI aus dieser Umgebung gesperrt); den vollständigen Lauf mit frischen Paketen liefert der GitHub-Lauf oben.

## Übereinstimmung Kern ↔ Gegenrechnung (D.1, E.1, E.2)
| Prüfung | Umfang | Abweichungen |
|---|---|---|
| Rechnende Testfälle (`regelwerk/testfaelle_maschinenlesbar.json`) | 94 Fälle (alle Rechenarten der Liste) | 0 |
| Zufallsfälle im eigenen Prozess (`tests/verifier/test_uebereinstimmung.py`) | 2.500 Aufrufe, 25 Rechenarten, Startwert 20261015 | 0 |
| Zufallsfälle, gleiche Logik im selben Prozess | 2.500 Aufrufe, Startwert 7 | 0 |
| Erkundung beim Bau | 3 × 6.000 Aufrufe (Startwerte 1, 2, 3) | 0 (nach den Befunden unten) |
| Eigenschaftstest über den ganzen Ablauf (`tests/app/test_eigenschaften.py`) | 2.000 Anfragen, alle Anfragearten, Jahre 2019–2027 | 0 abgelehnt |
| Höchstbeträge | 99.999.999.999,99 € in allen Jahren 2019–2027 | 0 |
| Menge | 100.000 Positionen in EINEM Kern-Aufruf, eigener Prozess: 0,9 s (Kindprozess 0,5 s), Zeitlimit 5 s | 0 |
| Zu große Liste | 100.001 Positionen: vorab abgelehnt, Sandbox startet nicht, keine Antwort | – |
| Rundung | mehr als zwei Nachkommastellen: beide Seiten „keine Zahl“ | 0 |

Befunde beim Bau (Einzelheiten `aufgaben/FUNDE_Chatbot.md`): (1) Kern-Fehler in der Rechnungsanalyse behoben (Position ohne Rolle zählte still mit 0); (2) Säumniszuschlag mit mehreren Rückständen bis 2022: die Gegenrechnung folgt jetzt dem dokumentierten Soll L-10/L-11 (Grenzfall).

## Mutationen (D.2) – alle gefangen
Fehler im **Kern** (Gegenrechnung im eigenen Prozess, liest das unveränderte Register), `tests/verifier/test_mutation.py`:
1. „übersteigt“ wird zu „mindestens“ (Operator der Schwelle) – gefangen
2. falsche Übungsleiterpauschale 2026 – gefangen
3. falscher Abgabesatz 2026 – gefangen
4. falsche Schwelle 2025 – gefangen
5. vertauschte Summenregel (Umsatzsteuer zählt mit) – gefangen
6. GmbH zählt mit (Rechtsformliste leer) – gefangen
7. ausgelassene Position – gefangen
8. eigene Rundung der Abgabe statt „keine Zahl“ – gefangen
9. Säumniszuschlag ein Monat zu viel – gefangen
10. Säumniszuschlag Abrundungsstufe falsch – gefangen
11. Drei-Veranstaltungen-Ausnahme „<“ statt „<=“ – gefangen
12. Vorauszahlung durch 11 statt 12 Monate – gefangen
13. Verpflegung: genau 8 Stunden zählt schon – gefangen
14. Rechnungsanalyse: Reisekosten ohne Belege zählen als sicher – gefangen
15. Schätzung Ausland mit falschem Prozentsatz – gefangen
16. Meldefrist falscher Tag – gefangen

Fehler in der **Gegenrechnung** (Kern richtig):
1. Vergleich verdreht – gefangen
2. Umsatzsteuer zählt mit – gefangen
3. Abgabe immer auf Cent gerundet – gefangen
4. bereits ausgeschöpfte Pauschale vergessen – gefangen
5. Säumniszuschlag aufgerundet – gefangen
6. Vorauszahlung ohne Untergrenze – gefangen
7. offene Rechnungspositionen übersehen – gefangen
8. Schwelle des Vorjahres genommen – gefangen

Zusätzlich Ende zu Ende über den Router: falscher Abgabesatz im Kern → „Prüfung fehlgeschlagen“, Text „Gegenrechnung weicht ab (… Kern 25.0…, Gegenrechnung 24.5…)“, keine Ergebnisaussage, Eintrag im Lückenprotokoll mit Fall-Kennung.

**Bilanz: 24 Mutationen, 24 gefangen.** Ohne Mutation stimmen alle Proben überein.

## Sandbox-Verhalten (D.3, D.4) – `tests/verifier/test_sandbox.py`
- Netz (Socket, Verbindung, urllib): gesperrt.
- Datei schreiben, Datei lesen, Datei löschen: gesperrt (die Testdatei entsteht nicht).
- Neue Prozesse (subprocess, os.system): gesperrt.
- Nachladen von `kern`, `app`, `exec`: gesperrt.
- Endlosschleife: nach dem Zeitlimit beendet, Ergebnis „fehlgeschlagen“.
- Absturz, Abbruch, kaputte oder falsche Ausgabe: „fehlgeschlagen“, nie „bestätigt“.
- Speichergrenze (Linux): greift (Anforderung über der Grenze scheitert).
- Umgebung: Schlüssel und Proxy-Variablen des Elternprozesses kommen nicht im Kindprozess an.
- Statisch: kein Import von `kern` in `verifier/` (und kein `app` außer im Startknopf `pruefe_register.py`); keine fachlichen Festwerte in `verifier/` (nur 0, 1, 100, 12, 31, 0.01).

## Zeitmessung (E.3) – `python scripts/messe_gegenrechnung.py 500`
500 Zufallsfälle, je ein eigener Prozess, ohne Modellaufruf: Gegenrechnung gesamt im Mittel **32 ms** (Median 31 ms, Höchstwert 153 ms), davon Rechnen im Kindprozess im Mittel 0,5 ms (höchstens 1,6 ms). Der Rest ist der Start des Python-Prozesses. Unter der Grenze von 300 ms: ein dauerhaft laufender Sandbox-Prozess ist nicht nötig.

## Was nicht geht (ehrlich)
- Kein vollständiger Sicherheitsrahmen wie ein Container; ein Audit-Hook ist umgehbar für Code mit vollen Rechten im selben Prozess. Dort läuft nur fest hinterlegter Code aus `verifier/`.
- Windows: keine Speicher- und CPU-Grenze (nur Zeitlimit).
- Die Gegenrechnung bestätigt die Rechnung, nicht die Einordnung und nicht die Regel selbst; beide Seiten lesen dieselbe Excel.
- Zeitmessung nur für Kern und Gegenrechnung, nicht für alle Schritte.
