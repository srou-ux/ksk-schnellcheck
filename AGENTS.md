# AGENTS.md – Einstieg für jede KI und jedes Werkzeug (Codex, Cursor, Claude Code, andere)

Die vollständigen Grundregeln stehen in `CLAUDE.md` (gelten für alle KI, nicht nur für Claude). Die Schritt-für-Schritt-Abläufe für Updates stehen in `aufgaben/PFLEGE_Update_Anleitung.md`.

Kurzfassung:
- Lies zuerst `CLAUDE.md`, `aufgaben/PFLEGE_Update_Anleitung.md`, `aufgaben/Arbeitsstand.md`.
- Das System macht Vorschläge, der Steuerberater entscheidet. Alles ist Entwurf.
- Ohne KI: kein Sprachmodell, kein Chat; Dokumente liest Python, entschieden wird nur mit Regeln (`CLAUDE.md`, Regel 12).
- Keine Festwerte im Code; Zahlen stehen in `regelwerk/Regelkatalog_24_KSVG_Entwurf.xlsx`.
- Nichts raten, keine Zahl ohne Fundstelle.
- Erfolgskriterium nach jeder Änderung: `python scripts/pruefe_alles.py` meldet „ALLES GRÜN".
- Alles bleibt auf GitHub; nach dem Push prüfen, dass neue Dateien wirklich im Repo liegen (`.gitignore` ist eine Positivliste).
