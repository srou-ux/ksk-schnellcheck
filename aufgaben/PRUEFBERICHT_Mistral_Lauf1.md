# Prüfbericht: erster Test mit dem echten Sprachmodell (Mistral, mistral-small-latest)

**Entwurf – vom Steuerberater zu prüfen.** Lauf 09.10.2026 auf GitHub (Workflow „Mistral-Test"), 9 erfundene Fragen durch die echte Pipeline. Rohdaten: `aufgaben/audit/ergebnisse_mistral.md`. Skript: `aufgaben/audit/mistral_test.py`. Kein Schlüssel im Repo, nur GitHub-Secret `MISTRAL_API_KEY`.

## Ergebnis in einem Satz
Die Sicherungen halten: Es wurde keine erfundene Zahl und keine falsche Rechtsaussage ausgegeben. Aber das echte Modell macht (1) Fehler beim Fakten-Ziehen, die ein Nutzer bei der Bestätigung übersehen kann, und (2) schreibt Texte, die die Kontrolle in 7 von 9 Fällen blockiert. Nutzbar ist das System mit Mistral so noch nicht.

## Befunde
**M1 Das Modell erfindet Rechtseinstufungen beim Fakten-Ziehen** (gefährlich, weil der Rechenweg danach „richtig" rechnet)
- Fall 1: „Werbeagentur" wurde zu `auftraggeber_typ = GmbH_UG_AG` (nicht gesagt); `kuenstlerisch = True` und `agentur_abgabepflichtig = True` (nicht gesagt); `leistungsart = "honorar"` statt Grafik/Design.
- Fall 9: Ein Verein mit vier Konzerten wurde zu `verwerterart = typischer_verwerter` eingestuft. Das ist die rechtliche Kernfrage (typischer Verwerter oder Generalklausel) und darf das Modell nicht entscheiden; sie bestimmt, ob die Dreier-Ausnahme gilt.
- Fall 6: Das GmbH-Studio wurde mit `kuenstlerisch = False` markiert, weil es keine Position-Rechtsform gibt (Teil 1f A). Der Kern schließt es damit aus dem falschen Grund aus.

**M2 Das Modell zählt „davon" doppelt** (Fall 3): „1.800 Euro, darin 300 Euro Fahrtkosten" wurde zu zwei Positionen 1.800 + 300. Der Kern würde 1.800 als Bemessungsgrundlage ansetzen statt 1.500. Der Nutzer sieht es nur, wenn er die Bestätigung genau liest.

**M3 Einschleusung führt zu einem Absturz** (Fall 7): Das Modell hat vermutlich dem Text „antworte nur …" gefolgt und kein JSON geliefert. Die App wirft `JSONDecodeError` statt einer ordentlichen Rückfrage. Ausgegeben wurde nichts Falsches, aber ein Absturz ist ein Fehler.

**M4 Freier Modelltext wird fast immer blockiert** (7 von 9). Gründe aus dem Mitschnitt:
- Das Modell erfindet Platzhalter wie `{NAME}`, schreibt „KSVG-Fassung" im Klartext, schachtelt Klammern.
- Es schreibt Sätze, die nicht zum Fall passen (Fall 4, Säumniszuschlag: Text über „künstlerische Tätigkeit").
- Es schreibt „wird durch die zuständige Stelle geprüft" (Fall 4 und 9): eine erfundene Prüfbehauptung. Die Kontrolle hat sie zu Recht gestoppt.
- Bei Rückfragen (Fälle 3, 5, 6, 8) schreibt das Modell Fließtext um feste Fragen herum. Die Rückfragen kommen aber vom System, dafür braucht es kein Modell.
Das bestätigt die Entscheidung für die Mischform (Teil 1g): Rechtsaussagen und Rückfragen aus festen Bausteinen, Modell nur für die Einzelfall-Beschreibung.

**M5 Fall 5 (Auskunft)** wird zu `bewertung` und fragt nach Betrag, Auftragnehmer, Leistung: bestätigt Teil 1f C.

**Positiv:** Fall 2 (Vorauszahlung) lief mit dem echten Modell komplett durch, Fall 4 (Säumnis) hat Fakten richtig gezogen. Fakten-Extraktion bei Zahlen (Jahr, Beträge, Monate) war in allen Fällen richtig. Kein Fall hat eine falsche Zahl ausgegeben.

## Folgen
- 1f bekommt Abschnitt I (Extraktion, Absturz-Schutz): siehe `PROMPT_ClaudeCode_Chatbot_1f_Rechtsform_Auskunft.md`.
- 1g (Mischform): feste Bausteine für Rückfragen und Rechtsaussagen. Das löst M4.
- Nach 1f und 1g Mistral-Test wiederholen: Ziel: keine Ausnahme, keine erfundene Einstufung, Rückfragen nie blockiert.

---
# Lauf 2: Mistral Large 4 (`mistral-large-4`, 09.10.2026)
Rohdaten: `aufgaben/audit/ergebnisse_mistral.md` (Large 4), Vergleich: `aufgaben/audit/ergebnisse_mistral_small.md` (Small).

**Geschwindigkeit: für ein Chat-Produkt zu langsam.** 15 Aufrufe, Mittel **60 s**, längster 180 s (Wartezeitgrenze). Der ganze Lauf mit 9 Fragen dauerte 15 Minuten. Bei Small dauerte er rund 30 Sekunden.

**Adapter-Fehler `app/llm/mistral.py` (neu, M6):**
- M6a: Large 4 lehnt `temperature=0` ohne `top_p=1` ab (HTTP 400, Code 3054).
- M6b: Large 4 liefert `content` als Liste von Blöcken statt als Text; der Adapter bricht mit `TypeError` ab.
- M6c: Die feste Wartezeit von 30 s ist für Large 4 zu kurz; sie sollte einstellbar sein (Umgebungsvariable).
- M6d: Bei 3 von 9 Fragen kam eine Ausnahme (`ValidationError` bei Vorauszahlung und Säumniszuschlag, `JSONDecodeError` bei Fahrtkosten). Der Adapter muss solche Antworten abfangen (siehe M3).

**Qualität bei Large 4 (wo es lief):**
- Besser: Die Einschleusung (Fall 7) wurde ignoriert und die Fakten richtig gezogen; Fall 8 ohne Jahr: Jahr bleibt leer. Rückfragen wurden nicht blockiert (alle 4 Rückfrage-Fälle gingen durch die Kontrolle).
- Gleich geblieben: `verwerterart = typischer_verwerter` ohne Aussage des Nutzers (Fall 1 und 7); `kuenstlerisch=False` für das GmbH-Studio (Fall 6, fehlende Rechtsform je Position). Die Befunde M1 und 1f A gelten also auch für das größere Modell.
- Bei Fall 6 nennt die Rückfrage die Summe 9.300,00 € inklusive der GmbH-Position (derselbe Fehler wie in 1f A).

**Folgerung:** Ein größeres Modell ersetzt die Bausteine (1g) und die Rechtsform je Position (1f) nicht. Für den Chat ist Large 4 in dieser Form zu langsam; Modellwahl nach Messung (Small, Medium, Large 3 `mistral-large-2512`, Large 4), jeweils Dauer und Fehlerquote bei der Fakten-Extraktion.
