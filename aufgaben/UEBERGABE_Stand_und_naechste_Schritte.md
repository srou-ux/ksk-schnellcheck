# Übergabeprotokoll: Stand und nächste Schritte (Stand 09.10.2026)

Zweck: Wenn die Unterhaltung abbricht, das Kontingent endet oder eine andere KI weitermacht, steht hier alles, was man zum Weitermachen braucht. Zusätzlich lesen: `CLAUDE.md`, `aufgaben/Arbeitsstand.md`, `aufgaben/PFLEGE_Update_Anleitung.md`, `aufgaben/FUNDE_Chatbot.md`.

## 1. Was ist das Projekt
KSK-Assistent: SaaS für Steuerberater, Agenturen und andere Unternehmen zur Künstlersozialabgabe (KSVG § 24). Er prüft Zahlungen und Rechnungen, beantwortet Fachfragen mit Fundstellen, bereitet Meldungen vor und unterstützt bei DRV-Prüfungen. Leitsatz: **Das System macht Vorschläge, die verantwortliche Person entscheidet.** Alles ist „Entwurf – vom Steuerberater zu prüfen". Repo: privat, `srou-ux/ksk-assistent`, Zweig `main`. Alles bleibt auf GitHub, bis der Nutzer anderes sagt. Der Nutzer arbeitet unter Windows (`C:\ksk cloud`), spricht Deutsch, wünscht kurze, einfache Erklärungen und **eine Sache nach der anderen**.

Rollen: Claude (in der Unterhaltung) = Entwickler/Prüfer, schreibt Aufträge und prüft unabhängig. Claude Code (lokal beim Nutzer) = baut nach den Aufträgen `aufgaben/PROMPT_ClaudeCode_*.md` und macht die Recherche.

## 2. Was ist fertig (alles auf GitHub, geprüft)
- **Quellenbestand** `quellen/`: 121 Quelldokumente (PDF/TXT), `index.csv`, **Prüfsummen** (`quellen/PRUEFSUMMEN.csv`, nur ergänzen, nie ändern).
- **Regelwerk** `regelwerk/Regelkatalog_24_KSVG_Entwurf.xlsx`: 236 Regeln, Blätter Schwellen/Abgabesätze/Pauschalen nach Jahr, **Regelregister** (alle weiteren Zahlen/Operatoren mit Gültigkeit), Offene Punkte, Tätigkeitskatalog. 329 erfundene Testfälle, Prüfliste für den Berufsträger (9/162/65 nach Priorität), Kontrollkatalog (48 Risiken), Fragenkatalog (191).
- **Regelkern** `kern/`: rechnet mit `Decimal`, liest alle Werte aus dem Register (`parameter.json`, erzeugt aus der Excel), kein Festwert im Code (Wächter-Test). 24 Kern-Tests, 94 Testfälle automatisch mit 0 Abweichungen.
- **Chatbot Teil 1, 1b, 1c, 1d** (Claude Code, `app/`, `tests/app/`): Fakten-Extraktion, Pflichtangaben, **Faktenbestätigung vor der Rechnung**, Router zum echten Kern, **Platzhalter-Antworten** (das Modell schreibt keine Zahlen/Normen/Aktenzeichen), Antwort-Kontrolle in allen Pfaden, Anonymisierung, Lückenprotokoll, Weboberfläche, FakeLLM (Demo-Modus) und Mistral-Adapter (EU). Unabhängig geprüft: `aufgaben/PRUEFBERICHT_Chatbot_Teil1.md`, `…Teil1d.md`.
- **Pflege**: `aufgaben/PFLEGE_Update_Anleitung.md` (KI-neutral, nichts überschreiben, jede Änderung eine neue Version), `CLAUDE.md`, `AGENTS.md`, `scripts/pruefe_alles.py` (**ein Befehl, Erfolgskriterium: „ALLES GRÜN"**), `scripts/pruefsummen.py`, `scripts/erzeuge_pruefliste.py`.
- Merkliste `aufgaben/Ideen_und_Vision.md`: Admin-Seite, Optimierung, Import großer Datenmengen (CSV/Excel), acht weitere Ideen.

## 3. Wo stehen wir gerade
- Claude Code arbeitet an **Teil 1d, Nachtrag 2** (`aufgaben/PROMPT_ClaudeCode_Chatbot_1d_Nachtrag2.md`): 17 Lücken bei freiem Text (Schlussfolgerungen in anderen Worten, Gerichts-/Behördennamen, Links, nachgebaute Schlusssätze). Danach meldet der Nutzer „fertig", und es wird **unabhängig geprüft**: `python aufgaben/audit/gegenproben_teil1d_runde3.py` (Lücken sollen 0 sein) und `python scripts/pruefe_alles.py` mit installierten Paketen.
- **Entschieden (09.10.2026): Mischform.** Rechtsaussagen nur aus festen, vom Berufsträger geprüften Bausteinen (aus dem Regelkatalog); freier Text nur für die Beschreibung des Einzelfalls ohne Rechtsaussage; Einzelfall-Wertung bleibt „Grenzfall → Steuerberater entscheidet"; Wortliste bleibt als zweites Netz. Umsetzung als Auftrag „Teil 1g" nach 1f.

## 4. Nächste Schritte in fester Reihenfolge (eins nach dem anderen)
1. Nachtrag 2 zu 1d abschließen und prüfen. Entscheidung Bausteine ja/nein.
2. **Teil 1f – Auskunftsfragen und passende Rückfragen** (Auftrag noch zu schreiben, Grundlage `aufgaben/PERSONA_Steuerberater_Test.md`, Befunde 1, 2, 4): Fragen wie Abgabesatz, Schwelle, Fristen, Pauschalen, Tätigkeitskatalog direkt aus Register/Katalog beantworten; Pflichtangaben je Kernaufruf statt pauschal; Rückfragen als Schaltflächen.
3. **Teil 1e – Prüf-Sandbox** (`aufgaben/PROMPT_ClaudeCode_Chatbot_1e_Pruefsandbox.md`): unabhängige Gegenrechnung im Paket `verifier/` (importiert `kern` nie), Ausführung im getrennten Prozess, 2000+ Zufallsfälle, Mutationsproben, große Zahlen, Zeitmessung. Sandbox-Nachweis `aufgaben/SANDBOX_Nachweis.md`.
4. **Teil 2 – Quellenabruf (RAG)** (`aufgaben/PROMPT_ClaudeCode_Chatbot_2_RAG.md`): alles datengesteuert, Zahlen nie aus Texten gelesen, Abgleich Register ↔ Quelle, Prüfung beim Start (Excel neuer als `parameter.json`), Behebung des Festwerts `fassung_fuer_jahr` (Jahr 2022 im Code, siehe Nachtrag 1d), Trefferquote ≥ 90 % in `aufgaben/RAG_Bericht.md`.
5. **Recherche 5** (Claude Code): Rundung der Abgabe (Bescheide der KSK, SGB IV, Rechtsprechung), KSK-Seite „wer ist abgabepflichtig", fehlende BSG-Urteile, amtliches Original zum Datum 01.01.2023 (Offener Punkt B4), Pauschalen 2027.
6. **Belegmodul** (Konzept noch zu schreiben): erst direkt lesbare Belege (E-Rechnung, digitale PDF), dann Scans/Fotos (Doppelerkennung, Rechenkontrolle, Belegansicht), dann Handschrift; Excel mit mehreren Blättern **zuletzt**.
7. **Update-Agent und Admin-Seite**, **Datenbank** (PostgreSQL + pgvector auf EU-Server), Konten/Rollen, Versionsnummer je Berechnung, Hosting, **Optimierung**, Import großer Datenmengen.
8. **Fachliche Prüfung** der 236 Regeln durch Steuerberater/Fachanwalt (Prüfliste); erst danach Statuswechsel von „Entwurf". Ziel: Referenz für die KSK nutzbar (nie „KSK-geprüft" behaupten).
9. Erst wenn alles fertig und validiert ist: **lokal herunterladen**: im Ordner `C:\ksk cloud` `git pull` (ohne lokale Änderungen in `quellen\`).

## 5. Ehrlicher Stand der Qualität
- Der Kern ist technisch geprüft, aber **fachlich nicht freigegeben**. 235 der 329 Testfälle sind noch nur Text und laufen nicht im Kern. Drei Fallgruppen sind nur teilweise abgedeckt (Restaurant mit Livemusik, Eventagentur, Auszahlung an Dritte).
- **Rundung der Abgabe ungeklärt**: bei mehr als zwei Nachkommastellen nennt der Kern keine Zahl (Eintrag in „Offene Punkte").
- Jahre vor 2019 haben keine Schwellen (Musterdialog 2017 → „Nicht abgedeckt", bewusst).
- Die Chatbot-Tests konnte der Prüfer in seiner Umgebung nur teilweise ausführen (fehlende Pakete `fastapi`, `httpx`); Webschnittstelle und echter Mistral-Aufruf sind **nicht unabhängig getestet**.
- Die Wirkung gegen Prompt-Injection bei einem echten Modell ist erst mit Mistral-Schlüssel prüfbar.

## 6. So macht man weiter, wenn die Unterhaltung neu beginnt
**An Claude (in der Unterhaltung):**
> Lies im Repo srou-ux/ksk-assistent die Dateien `CLAUDE.md`, `aufgaben/UEBERGABE_Stand_und_naechste_Schritte.md`, `aufgaben/Arbeitsstand.md` und `aufgaben/PFLEGE_Update_Anleitung.md` (Kopien liegen im Projekt „ksk"). Mach dort weiter, wo das Protokoll aufhört. Eine Sache nach der anderen, alles bleibt auf GitHub.

**An Claude Code (lokal):**
```
git pull
Lies CLAUDE.md und aufgaben/UEBERGABE_Stand_und_naechste_Schritte.md.
Führe den nächsten offenen Auftrag aus aufgaben/PROMPT_ClaudeCode_*.md aus (Abschnitt 4, Reihenfolge einhalten).
Alles bleibt auf GitHub.
```

**Immer vor dem Weitermachen:** `git pull`, `python scripts/pruefe_alles.py` muss „ALLES GRÜN" melden. Immer nach dem Push prüfen, dass neue Dateien wirklich im Repo liegen (`.gitignore` ist eine Positivliste; ein Fehler hier hat schon einmal `kern/` stumm ausgeschlossen).

**Wenn Claude Code unterbrochen wurde:** `git status` und `git log -5` ansehen. Nichts verwerfen, was nicht gepusht ist; den letzten Auftrag erneut starten und Claude Code sagen, dass er den Stand im Repo und `aufgaben/FUNDE_Chatbot.md` zuerst lesen soll, um nichts doppelt zu bauen.

## 7. Eckpunkte der Entscheidungen des Nutzers (nicht neu verhandeln, wenn nicht nötig)
- Eine Sache nach der anderen, validieren, dann der nächste Schritt. Immer weitermachen und prüfen; erklären, was getan wird.
- Alles flexibel und datengesteuert: Änderungen (neues Jahr, Wert, Gesetz, Regel) ohne Codeänderung. **Nichts überschreiben, nur ergänzen** (neue Version); Quellen unveränderlich.
- Automatisch bis zum Schluss, **am Ende bestätigt ein Mensch** (Update-Agent, Admin-Seite kommen später).
- Das SaaS ist **allgemein**, nicht nur für Steuerberater: verantwortliche Person beim Kunden, gemeinsame Regeln zentral gepflegt.
- Nur öffentliche Quellen und erfundene Daten; keine Uploads außerhalb Europas.
- Jede Aussage mit Fundstelle; Jahr ist Pflicht; Zahlen nie vom Sprachmodell; unabhängige Gegenrechnung (Prüf-Sandbox) als Teil des SaaS.
- Belege aller Art (digital, Scan, Foto, Handschrift) sollen unterstützt werden, mit ehrlicher Vertrauensstufe pro Zahl; Excel mit mehreren Blättern ganz am Ende.
