# Übersicht für die spätere Prüfung (Validierung) – Stand 15.10.2026

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Testdaten. Diese Datei sagt, **was** geprüft werden muss, **wo** es liegt und **in welcher Reihenfolge**. Nichts hier ist freigegeben.

## 1. Was der Steuerberater entscheiden muss (Excel, gelbe Spalten ausfüllen)

| Datei | Inhalt | Umfang |
|---|---|---|
| `regelwerk/Pruefliste_Steuerberater_Entwurf.xlsx` | Prüfliste 1: alle Regeln R-01 bis R-236 | 236 Regeln |
| `regelwerk/Pruefliste_Taetigkeiten_Entwurf.xlsx` | Tätigkeiten (11.10.2026) | erste Fassung |
| `regelwerk/Pruefliste_2_Steuerberater_Entwurf.xlsx` | Prüfliste 2: Regeln ohne Fassung, Fundstellen je Testfall, Quellen-Gültigkeit, Textbausteine, Fachfragen Q-01 bis Q-12 | übergeben |
| `regelwerk/Pruefliste_2_Nachtrag_1_Entwurf.xlsx` | Fachfragen Q-13 bis Q-31 | übergeben 14.10.2026 |
| `regelwerk/Pruefliste_2_Nachtrag_2_Entwurf.xlsx` | Fachfragen Q-32 bis Q-35 (Tätigkeiten) | neu |
| `regelwerk/Pruefliste_2_Nachtrag_3_Entwurf.xlsx` | Fachfrage Q-36 (Fotomodell) | neu |
| `regelwerk/Pruefliste_Taetigkeiten_Nachtrag_1_Entwurf.xlsx` | 200 Tätigkeiten: Entwurf, Blatt, System; Abweichungen und Lücken zuerst | 40 Abweichungen, 96 Lücken |

Alle Fachfragen stehen auch maschinenlesbar in `aufgaben/pruefliste_2_fragen.json` (Q-01 bis Q-36). Die Nummern Q-15 bis Q-22 aus dem Auftrag des Nutzers heißen dort Q-18 bis Q-25 (Zuordnung in der Datei).

**Reihenfolge (Vorschlag):**
1. Q-32 (Unterricht in Kunst).
2. Q-35 (Abweichungen Blatt ↔ Entwurf).
3. Q-34 (Lücken im Tätigkeitsblatt).
4. Q-13 (Musikverein).
5. Q-26 bis Q-31 (e. V., unbezahlt, Gutschrift, Rundung, Zusatzgeschenk, Provision).
6. Prüfliste 1.

Begründung: Die ersten drei verändern am meisten Ergebnisse.

## 2. Testkataloge (Soll mit Status, gegen Register geprüft)

| Katalog | Fälle | Im Testarchiv? | Letzter Live-Stand | Bericht |
|---|---|---|---|---|
| Prüfkatalog, Testfall 20, Alltag 4/999, Währung | 88 | ja | im Gesamtlauf | `aufgaben/audit/nachgefragt_auswertung.md` |
| Fehlerquellen HT-062 bis 111 (`aufgaben/audit/fehlerquellen_ht_062_111.json`) | 37 + 13 Dialog-/Programmtests | ja | 0 falsch | im Arbeitsstand |
| Alltags-Serie AT-001 bis 060 (`aufgaben/audit/alltag_at_001_060.json`) | 55 + 5 Dialoge | ja (seit 15.10.2026) | 49 richtig / 6 nachgefragt / 0 falsch | im Arbeitsstand |
| Härtetest HT-2026-001 (`aufgaben/audit/haertetest_ht_2026_001.json`) | 1 | **nein** (Berater-Punkte offen) | 6/6 | `aufgaben/audit/haertetest_ht_2026_001_auswertung.md` |
| Härtetests HT-002 bis 011 (`aufgaben/audit/haertetests_ht_2026_002_011.json`) | 10 | **nein** (Soll aus KI-Prüfung, nicht vom Berater) | 0 falsch | `aufgaben/audit/haertetests_ht_2026_002_011_auswertung.md` |
| Tätigkeitskatalog (`aufgaben/audit/taetigkeitskatalog_200.json`) | 200 | **nein** (erst Entscheidung Q-34/Q-35) | 20 Stichproben × 6 | `aufgaben/audit/taetigkeitskatalog_auswertung.md` |

Jeder Fall trägt `status`: Erwartungstyp (FEST / BEDINGT / RÜCKFRAGE), Fachstatus (BELEGT / TATSACHEN_OFFEN / RECHTLICH_ZU_PRÜFEN / QUELLE_FEHLT), Freigabe (ENTWURF). Abweichungen vom Soll-Entwurf des Nutzers stehen je Fall unter `sicherheit`, mit Grund. Frühere Fassungen eines Falls: im Katalog unter `fassungen` und im Archiv in `tests/archiv/versionen.jsonl` (nur ergänzt, nie überschrieben).

## 3. Messergebnisse (nichts wird überschrieben)

- **Jeder Live-Lauf je Fall:** `tests/archiv/ergebnisse/*.csv` (Datum, Katalog, Modell, Code-Stand, Soll, Ist, Urteil, Gründe).
- **Vergleich zweier Läufe:** `python scripts/vergleiche_ergebnisse.py ALT.csv NEU.csv`.
- **Rohe Modellantworten** (Fakten, je Lauf): `aufgaben/audit/modellfehler_fakten_{mit,ohne}_<Lauf>.jsonl`.
- **Lückenprotokoll:** `aufgaben/audit/modellfehler_{mit,ohne}.jsonl`. Darin bei kaputtem Modell-JSON die Fehlerstelle; Wörter sind maskiert.

## 4. Programmtests mit echten oder nachgebildeten Modellantworten

| Test | Herkunft |
|---|---|
| `tests/app/test_haertetests_002_011.py` + `tests/app/daten_haertetests_002_011.json` | echte Modellantworten, Lauf 38641137620 |
| `tests/app/test_fehlerquellen.py` | Live-Funde der Fehlerquellen-Serie |
| `tests/app/test_dialoge_fehlerquellen.py` | 11 Dialoge |
| `tests/app/test_alltag_live.py` | Live-Funde der Alltags-Serie, drei Läufe |
| `tests/app/test_dialoge_alltag.py` | 5 Dialoge |
| `tests/app/test_taetigkeitskatalog.py` | neue Zeilen T-70 bis T-75 |

Ausführen (Windows): `python scripts/pruefe_alles.py` (muss „ALLES GRÜN“ melden).

## 5. Änderungen am Regelwerk, die der Steuerberater bestätigen muss

Blatt „Tätigkeitsabgrenzung“, neue Zeilen vom 15.10.2026, alle „Entwurf“; alte Zeilen unverändert:
- T-70 Textkorrektur
- T-71 Unterricht in Kunst
- T-72 technische Zeichnung
- T-73 Playlist
- T-74 Fotogrammetrie
- T-75 Sync-Agent
- T-76 Fotomodell

Einzelheiten stehen im Änderungsprotokoll in `aufgaben/Arbeitsstand.md`.

Änderung am Kern vom 15.10.2026 (zur Kenntnis): In der Rechnungsanalyse zählte eine Position ohne Einordnung still mit 0. Jetzt bleibt sie offen, und das System fragt nach (`aufgaben/FUNDE_Chatbot.md`, Abschnitt „Unabhängige Gegenrechnung gebaut“).

## 6. Bewusst offen (kein Fehler, sondern Entscheidung ausstehend)

- Mehrere Zahlungsjahre in **einer** Nachricht: Das System fragt nach, statt mehrere Jahre in einer Antwort zu rechnen (eigener Ausbauschritt).
- Rundung bei mehr als zwei Nachkommastellen: keine Zahl (Grundregel 7, Q-29).
- Unabhängige Gegenrechnung (`verifier/`): seit 15.10.2026 gebaut (Grundregel 3). Sie bestätigt Rechnungen, nicht die Einordnung und nicht die Werte der Excel (`aufgaben/SANDBOX_Nachweis.md`).
