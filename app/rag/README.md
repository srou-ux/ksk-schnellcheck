# Quellenabruf (RAG) – `app/rag/`

Auftrag: `aufgaben/PROMPT_ClaudeCode_Chatbot_2_RAG.md`. Stand 13.10.2026. Alles **Entwurf – vom Steuerberater zu prüfen**.

Der Quellenabruf liefert zu einer Frage die passenden Regeln, Gesetzesstellen, Urteile und KSK-/DRV-Texte, **jeweils mit Fundstelle** und passend zum Jahr. Er liefert Texte und Fundstellen zum **Begründen**, nie Zahlen zum Rechnen (gerechnet wird nur im Kern `kern/rechnen.py`). Das Sprachmodell bekommt keine Quelltexte. Antworten nennen nur Fundstellen aus dem, was der Abruf geliefert hat.

## Befehle (Windows wie Linux)

| Befehl | Wirkung |
|---|---|
| `python -m app.rag.index` | Index bauen/aktualisieren, nur geänderte Quellen; schreibt `aufgaben/RAG_Aenderungen.md` |
| `python -m app.rag.index --neu` | Index ganz neu bauen (etwa 1 Minute) |
| `python -m app.rag.index --pruefung-erledigt R-12` | Regel nach menschlicher Prüfung wieder freigeben (nach geänderter Quelle) |
| `python -m app.rag.guete` | Abruf-Güte gegen die Testfälle messen → `aufgaben/RAG_Bericht.md` |
| `python -m app.rag.abgleich` | Register ↔ Quelle abgleichen → `aufgaben/RAG_Abgleich.md` |
| `python -m app.rag.suche "Frage" 2025` | eine Suche von Hand ausprobieren |

Die Web-App aktualisiert den Index beim Start im Hintergrund. Der Index liegt in `app/_lokal/rag.sqlite` (nicht im Repo).

## Aufbau

| Datei | Aufgabe |
|---|---|
| `zerlegen.py` | PDF (pypdf) und TXT lesen, Kopf-/Fußzeilen entfernen, zerlegen: Gesetz nach § und Absatz (Änderungsgesetze nach Artikel), Urteil nach Leitsatz und Randnummern, KSK/DRV nach Abschnitten mit Seite. Nie mitten im Satz trennen. |
| `index.py` | Stücke aus dem Regelkatalog (Regeln, Regelregister, Schwellen, Abgabesätze, Tätigkeitskatalog) und aus den Quellen; SQLite **FTS5**; Prüfsumme je Quelle (nur Geändertes neu); Änderungsliste; geänderte/entfernte Quelle → verknüpfte Regeln auf „prüfen“. |
| `suche.py` | a) Regelfilter (Regeln des Kerns + die Quelltext-Stellen, die ihre Fundstelle nennt), b) Stichwortsuche BM25 mit Jahresfilter **in** der Abfrage, zwei Ranglisten (Regelkatalog / Quellen, nachrangige Gesetze schwächer) per Reciprocal Rank Fusion, Grundwörter deutscher Zusammensetzungen, c) optional Embeddings, d) höchstens 8 Stücke, nach Stufe sortiert, Mindestabdeckung der Begriffe, sonst leer mit Grund. |
| `embeddings.py` | nur mit `RAG_EMBEDDINGS=1`: Mistral-Embeddings (EU), Schlüssel nur aus `MISTRAL_API_KEY` |
| `abgleich.py` | prüft, ob jeder Registerwert im Text seiner Fundstelle steht (liest/übernimmt nie Werte) |
| `guete.py` | Abruf-Güte und Gegenproben |
| `konfig.json` | nur Technik: Muster, Rauschzeilen, Stoppwörter, Grenzen, Gewichte |
| `quellen_metadaten.csv` | je Quelle: Kurzname (für die Fundstelle), Art, Stufe (Quellenpolitik), **gilt_von / gilt_bis**, Zerlegung, aufnehmen, nachrangig. Automatisch vorbelegt, **vom Steuerberater zu prüfen**. |
| `gegenproben.json` | erfundene Fragen ohne Quelle (Soll: „Nicht abgedeckt“) |

Strategie und Reihenfolge der weiteren Arbeit: `aufgaben/RAG_Strategie.md`.

**Fassung und Gültigkeit kommen aus den Daten:** die Jahre einer Quelle aus `quellen_metadaten.csv`, die Fassung (A/B) je Jahr aus dem Register (`kern/parameter.json` ← Excel). Für ein Jahr ohne Registerdaten ist das Ergebnis leer: „Nicht abgedeckt“, keine Annäherung mit einem anderen Jahr.

## Neue Quelle oder neue Fassung – ohne Code

1. Datei nach `quellen/` (neuer Name, nie überschreiben), Prüfsumme: `python scripts/pruefsummen.py --ergaenzen`.
2. Zeile in `quellen/index.csv`.
3. Zeile in `app/rag/quellen_metadaten.csv` (Kurzname, Art, Stufe, gilt_von, gilt_bis, Zerlegung). **Ohne diese Zeile wird die Quelle nicht indexiert** und in der Änderungsliste gemeldet (die Gültigkeit wird nicht geraten).
4. `python -m app.rag.index`, dann `python -m app.rag.abgleich` und `python -m app.rag.guete`.

## Sicherheit

- Quelltexte sind Daten: ein Stück mit eingebautem Befehl wird geliefert wie jedes andere; Antworten verwenden nur seine Fundstelle (Test `test_injection_im_quelltext_ist_nur_daten`).
- Die Antwort-Prüfung (`app/pruefung.py`) verlangt: jede Regel-ID und jedes Aktenzeichen im Text steht unter dem, was dieser Antwort **geliefert** wurde (Kontext, Abruf, verwendete Textbausteine).
- Stufe 3 (Sekundärquelle, Gesetzesmaterial) nur als „Hinweis, kein Beleg“.

## Grenzen (offen gesagt)

- **Abruf-Güte 86,6 %** (Stand 14.10.2026, vorher 85,6 %; Ziel 90 % nicht erreicht), siehe `aufgaben/RAG_Bericht.md`. Ursachen: andere Wörter in Frage und Quelle (Bedeutungsabstand), lange Gesetzesabsätze, Zahlen in Wörtern („fünf Jahre“).
- **Embeddings gemessen (13.10.2026, mistral-embed, Workflow „RAG Embeddings messen“): in jeder Variante schlechter** (79,9 % bis 84,6 % gegen 85,6 % ohne), siehe `aufgaben/RAG_Embeddings_Varianten.md`. Der Schalter `RAG_EMBEDDINGS=1` bleibt deshalb aus. Ein vollständiges Einbetten kostet geschätzt 15–20 Cent (rund 1,5 Mio. Token); der Vektor-Index wird im Actions-Cache gehalten.
- **Mindestabdeckung ist ein Kompromiss:** 6 von 10 Gegenproben kommen richtig leer zurück; 34 von 299 echten Testfällen kämen leer zurück (in der Bewertung greift dagegen der Regelfilter, nicht die Abdeckung).
- Zerlegung ist heuristisch (Überschriften, Randnummern); Fundstellen sind auf Absatz-, Abschnitts- und Seitenebene, nicht auf Satzebene genau.
- Kein Anspruch auf Vollständigkeit.
