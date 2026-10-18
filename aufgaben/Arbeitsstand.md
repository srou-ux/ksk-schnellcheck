# KSK-Assistent – Arbeitsstand (09.10.2026)

Ergänzt `ksk-assistent-projektplan.md`. Abschnitte 9 (Rechtsquellen: Soll-Stand) und 14 (Nächste Schritte) des Plans sind damit überholt. Ideen und Vision: `ksk-assistent-ideen.md`.

## Arbeitsweise
- Alles liegt im privaten GitHub-Repo `srou-ux/ksk-assistent` (Branch main). Download: `git pull` in `C:\ksk cloud` oder „Code → Download ZIP“. Vor dem Pull nichts in `quellen\` lokal ändern.
- Internet-Recherche über Prompts für Claude Code (lokal): `aufgaben/PROMPT_ClaudeCode_Recherche_1.md`, `…_2.md`, `…_3.md` – alle erledigt und eingearbeitet.
- Nur öffentliche Quellen und erfundene Testdaten. Quellenpolitik mit Vertrauensstufen: `regelwerk/Quellenpolitik_Entwurf.md`. Eine Sache nach der anderen.

## Chatbot-Anforderung
Expertenebene für Steuerberater und Agenturen, nennt Urteile mit Fundstelle (nur aus der Quellenbasis, keine erfundenen Aktenzeichen), trennt Gesetz / Rechtsprechung / KSK-Praxis / Ableitung, nennt Gegenansicht und Risiko, macht Lösungsvorschläge mit Referenz, fragt fehlende Angaben aktiv ab, gleiche Standards bei der Rechnungsanalyse (ein gemeinsamer Regelkern). „Keine Lücke“ ist nicht garantierbar: Abdeckung messen, Lücken sichtbar machen, bei fehlender Quelle „nicht abgedeckt“. Dateien: `regelwerk/Chatbot_Systemanweisung_Entwurf.md`, `regelwerk/Chatbot_Musterdialoge_Entwurf.md`.

## Stand
- Quellen: über 100 öffentliche Dokumente, dazu 12 BSG-Urteile und 1 LSG-Urteil im Volltext, 1 BSG-Urteil nur als Sekundärquelle (2004, lexetius.com), SGG, SGB X, SGB I, HGB, Rundschreiben Statusfeststellung 2017, KSK-Fragebögen GmbH-Gesellschafter.
- Regelkatalog: 236 Regeln (R-01–R-236) mit Fundstelle; Blätter Abgabesätze 2015–2027 und Pauschalen nach Jahr. Testfälle: 329. Fragenkatalog: 191 Fragen (159 mit Regel, 23 teilweise, 9 sichtbare Lücken).
- Aus Recherche 2: Zahlungen an KG/OHG nicht abgabepflichtig, GbR ja (R-216–R-218); Zwischenverwerter nur im Einzelfall (R-219); Gewinnzuweisungen kein Entgelt (R-220); Rücknahme von Abgabebescheiden nach § 27 Abs. 1a S. 2 KSVG ohne Vertrauensschutz (R-223/R-224); Säumniszuschlag-Rundung bis 2022 mit Addition, ab 2023 gesonderte Abrundung zulässig (R-226); Rechtsbehelfe: Widerspruch 1 Monat, Klage 1 Monat, Wiedereinsetzung, aufschiebende Wirkung als Ableitung (R-227–R-232). Aus Recherche 3: KSK-Fragebögen für Gesellschafter (R-235).
- Unabhängiger Audit der Regeln R-205–R-234 und der Blätter durchgeführt; Korrekturen eingearbeitet.
- Rechtsstand: § 24 KSVG Fassung A (bis 31.12.2022) und B (ab 01.01.2023, Schwelle 450 € bis 2024, 700 € 2025, 1.000 € ab 2026). Abgabesätze: 2019–2022 4,2 %; 2023–2025 5,0 %; 2026 4,9 %; 2027 5,0 %.
- Archivdatum ≠ Stand der Quelle; KSK-/DRV-Hinweise sind „Auslegung, kein Gesetz“; alles „Entwurf – vom Steuerberater zu prüfen“.

## Ohne KI (17.10.2026, Repo `srou-ux/ksk-schnellcheck`)
- Entscheidung des Nutzers: Das SaaS läuft ohne KI, eigenständig, nur mit Regeln. Der Nutzer lädt PDF, Foto, Excel oder CSV hoch, Python liest.
- Entfernt: Mistral und die Sprachmodell-Schicht (`app/llm/`), der KSK-Chat (`app/router.py`, Bausteine, Antwort-Kontrolle, Bestätigung, Warteschlange, Lückenprotokoll), der Quellenindex (`app/rag/`), die KI beim Dokument-Lesen (`app/dokument_ki.py`), 13 Mistral-Workflows, 19 KI-Testläufer unter `aufgaben/audit/`, 58 Chat-Tests, `scripts/erzeuge_pruefliste_2.py` (brauchte den Quellenindex). Alles steht im Git-Verlauf.
- Neu: `app/bewertung.py` (18 Funktionen unverändert aus dem Router: Kernaufruf + Gegenrechnung), `app/main.py` startet nur „Rechnungen prüfen“ (`/`, alte Adresse `/rechnungen` bleibt), `tests/app/test_ohne_ki.py` (Wächter), `tests/app/test_regel_erkennung.py` (übernommene regelbasierte Tests), `app/requirements-test.txt` (httpx nur für Tests), `scripts/pruefliste_layout.py`.
- Geprüft: erfundene PDF, Excel, CSV und Foto (OCR) gelesen und bewertet, Gegenrechnung bestätigt.
- Ergebnisberichte der früheren KI-Läufe unter `aufgaben/audit/` bleiben als Nachweis; Kommentare in den Wortregeln nennen Mistral-Läufe als Herkunft einer Regel.

## KSK-Schnellcheck (17.10.2026, Repo `srou-ux/ksk-schnellcheck`)
- Kostenlose Ersteinschätzung ohne KI als Einstieg (Lead-Magnet) in das SaaS. Kopie von `ksk-assistent` (Stand 75ab51a) plus Ordner `schnellcheck/`.
- Besucher wählt Jahr, Zweck, Katalogfrage, Leistungen (feste Liste aus Blatt „Tätigkeitsabgrenzung“), Rechtsform, Betrag. Bewertung über `app.dokument_pruefung.auswerten` (Kern + Gegenrechnung), keine eigene Rechnung, keine Festwerte.
- Einzige Änderung am vorhandenen Code: `fakten_aus`/`auswerten` nehmen optional `taetigkeit_ids` (gewählte T-IDs statt Freitext-Erkennung; ungültige ID = „unbekannt“). Ohne Parameter unverändert.
- Grenzfall, Rückfrage, Nicht abgedeckt → Anzeige „Weitere Prüfung nötig“; die Kernklasse wird immer mit angezeigt.
- Tests: `tests/schnellcheck/` (21), Teil von `scripts/pruefe_alles.py`. Start: `scripts/start_schnellcheck_windows.bat`.

## Bekannte Lücken (Bot antwortet „nicht abgedeckt“)
- Keine neuen BSG-Urteile zur Abgabepflicht von Unternehmen nach 01.06.2022.
- Sechs LSG/SG-Entscheidungen nur als Sekundärquelle ohne Volltext (`quellen/ergaenzend/urteile/LISTE_LSG_SG.md`); zehn ältere BSG-Urteile (1998–2008) nicht frei abrufbar; „B 3 KS 1/08 R“ hat das Datum 18.09.2008.
- Kein BMF-/BFH-Material zur steuerlichen/buchhalterischen Behandlung der Abgabe.
- Keine Entscheidungen zu Insolvenz, Konzern, Geschäftsführerhaftung, Betriebsübergang; Umwandlung nur Sekundärquelle.
- Keine offizielle Veröffentlichung zu Podcasts, NFT/digitaler Kunst, KI-generierter Grafik/Texten.
- Infos 13–16 verwenden noch Fassung-A-Wortlaut („nicht nur gelegentlich“).
- Aus dem externen Prüfbericht umgesetzt: B1 (R-236, Tests L-18 bis L-21), B2/B3 (`quellen/DUPLIKATE.md`, `tests/pruefe_quellen.py`, Hinweis in `index.csv` korrigiert), B4 (R-10 bis R-15, R-24, R-150 „fachlich zu klären“), Statusmodell, Kontrollkatalog (48 Risiken; 5 umgesetzt (Daten), 25 teilweise, 18 erst im Prototyp prüfbar).

## Nächste Schritte
1. Inkrafttreten der Fassung B am amtlichen BGBl.-Original prüfen (B4).
2. Abnahme durch Steuerberater/Fachanwalt (aus „Entwurf“ heraus).
3. Lücken nur mit Quellen der Stufe 1/2 füllen (z. B. amtliche Volltexte der LSG/SG-Urteile über juris oder Landesportale).
4. Später: Interviewleitfaden, Fragebäume, Spezifikation Rollen/Protokoll, Prototyp (EU-Hosting, Mistral zuerst, RAG nur auf öffentlichen Quellen, Berechnung im Code).

## Nächster Schritt (09.10.2026)
- `aufgaben/PROMPT_ClaudeCode_Recherche_4.md`: B4 (BGBl.-Original), neue KSK-Infos, Rechtsprechung nach 2022. Erst nach Abschluss von Recherche 3 starten.

## Recherche 4 ausgewertet (09.10.2026)
- B4: Art. 34 Abs. 1 des 8. SGB IV-ÄndG nennt im Archivtext den 01.01.2023; Art. 17 (KSVG) steht nicht in den Ausnahmen der Abs. 2–10. Amtliches PDF weiterhin nicht frei abrufbar (bgbl.de nur per Viewer). R-10 bis R-15, R-24, R-150 bleiben „fachlich zu klären“, Vermerk präzisiert.
- Infos 13–16: live identisch mit den Repo-Kopien (Stand 09.2025); keine neuere Fassung. Infos 01, 01a, 06, 19, 26 lagen schon im Repo. Kein DRV-Rundschreiben zur KSA.
- Rechtsprechung ab 2023: keine Volltexte; LSG Berlin-Brandenburg 11.02.2026 (L 1 KR 367/23) nur Sekundärquelle.
- Fünf ältere BSG-Urteile (1998–2004) als Sekundärquelle (lexetius.com, Stufe 3) abgelegt, keine Regeln daraus; fünf weiterhin nicht gefunden.

## Prüfliste für den Steuerberater (09.10.2026)
- `regelwerk/Pruefliste_Steuerberater_Entwurf.xlsx`: 236 Regeln, Priorität 1 (9, offen/Grenzfall), 2 (162, KSK-Auslegung/Ableitung), 3 (65, Gesetz/Rechtsprechung). Alle 236 Regeln haben jetzt mindestens einen Test (N-01 bis N-70 neu, unabhängig geprüft, 10 Befunde eingearbeitet). Nichts ist freigegeben.

- Neue Testfälle N-01 bis N-70 für alle Regeln ohne Test; Prüfliste neu erzeugt (Spalte „Tests dazu“ überall gefüllt). Gesamt 298 Testfälle.
- Tests Q-01 bis Q-16: die acht Fälle T1–T8 des Prüfberichts plus Grenzwerte (8:00/8:01 Stunden, 699,99/700,00/700,01 € in 2025, 999,99/1.000,00/1.000,01 € in 2026). Gesamt 314 Testfälle.

## Regelkern v0 (09.10.2026)
- `kern/rechnen.py` + `kern/parameter.json` (aus dem Katalog erzeugt) + `tests/test_kern.py`: 18 Tests laufen grün, darunter Q-01 bis Q-16. Gegenprobe: bewusst eingebaute Fehler (>= statt >) lassen Tests scheitern. Noch nicht im Kern: die meisten der 236 Regeln, Rundung, Fassung A außer Eigenwerbung bis 450 €.

- Tranche 2 des Kerns: `tests/lauf_testfaelle.py` führt 84 von 318 Testfällen automatisch aus (alle bestanden); 234 sind noch nur Text (Einordnungsfragen wie Künstlerbegriff, Selbständigkeit, Branche; Verfahren). Vier neue Randtests T-01 bis T-04 (50-€-Stufe, 40 €, 150 €). Bewusst eingebaute Fehler wurden gefunden.

## Fallkatalog (40 Fallgruppen) geprüft (09.10.2026)
- `aufgaben/Fallgruppen_Abdeckung.md`: Zuordnung aller 40 Fallgruppen zu Regeln und Tests. 37 mit Regel und Test, 3 nur teilweise (11 Restaurant mit Livemusik, 13 Eventagentur, 39 Auszahlung an Dritten).
- Neue Tests F-01 bis F-06 (Konzertveranstalter, Jubiläum, viele kleine Rechnungen, Einnahmeabsicht). I-13, I-14 und C-22 präzisiert. Kern: Drei-Veranstaltungen-Ausnahme nur für die Generalklausel (`unternehmensart`). Jetzt 90 von 324 Testfällen im Kern.
- Offen: KSK-Webseite „Wer ist abgabepflichtig?“ (Q3 im Fallkatalog) als Quelle noch nicht im Repo (für Recherche 5 vormerken).

## Test mit fiktiver Agenturrechnung (09.10.2026)
- Beleg AT-2026-204 (Atelier Transit GmbH an Hafenforum Events KG, 12 Positionen, Netto 8.956 €) in `tests/belege/`. Tests H-01 bis H-05; Kern: `analysiere_rechnung()`. Ergebnis: sicher zählend 850 € (Gastbeitrag), offen 1.866 € (Eventdokumentation, Musik, Reisekosten ohne Belege); mit allen Angaben Abgabe 41,65 €. Rechnungssummen stimmen (USt 1.501 €).
- Befund: Würde man alle offenen Beträge mitzählen (2.716 €), ergäbe 4,9 % 133,084 € – die Rundung der Abgabe ist weiter nicht belegt (Kern liefert dann keine Zahl). Zu klären durch Steuerberater/KSK.
- Jetzt 94 von 329 Testfällen im Kern ausgeführt.

## Chatbot-Bau (09.10.2026)
- Auftrag an Claude Code: `aufgaben/PROMPT_ClaudeCode_Chatbot_1.md` (Prototyp in `app/`, Mistral EU + FakeLLM, Fakten-Extraktion → Kern → Quellenabruf → Antwort mit Kontrolle, Tests offline). Code bleibt auf GitHub; nichts lokal herunterladen, bis alles geprüft ist. Ich prüfe das Ergebnis danach unabhängig.

- Codespaces vorbereitet: `.devcontainer/devcontainer.json`, `scripts/start_codespace.sh`. Der Chatbot-Auftrag verlangt Demo-Modus ohne Schlüssel und eine einfache Weboberfläche. Anleitung für den Nutzer: GitHub → Repo → Code → Codespaces → Neu erstellen (Region Europa wählen); Tab 'Ports' öffnen.

## Regelregister (Kern flexibel)
- Neues Blatt „Regelregister“ (22 Zeilen) im Regelkatalog; `erzeuge_parameter.py` exportiert es nach `parameter.json` (Schlüssel `register`).
- `kern/rechnen.py` liest alle früheren Festwerte (8/24 Std., 12/14/24/28 €, 3 Veranstaltungen, 40 €, 12 Monate, 50 €, 1 %, 150 €, 25 %, 31.3., 5 Jahre, Rechtsformen, Schwellen-Operator) aus dem Register; `ev_juristische_person` entfernt (ohne Quelle). `schaetzung_ausland` hat jetzt ein Jahr.
- 4 neue Tests (23 gesamt), u. a. Gegenprobe: Wert/Operator im Register ändern ändert das Ergebnis; fehlender Eintrag → „Nicht abgedeckt“.
- Stand: 23 Kern-Tests bestanden; 94 von 329 Testfällen im Kern, 0 Abweichungen; Regelwerk-Prüfung ohne Fehler.
- Nachtrag: Zahlen und Schwellen stehen verbindlich in Excel (Regelkatalog: Blätter Schwellen, Abgabesätze, Pauschalen, Regelregister). Weitere Festwerte aus dem Code ins Register verschoben: Musikverein-Schülergrenze (60), Säumnis-Methode je Jahr (Addition bis 2022), Mindestjahr Verpflegung; Standardjahre 2026 entfernt (Jahr ist Pflicht). Neuer Wächter-Test: Zahlen im Kern nur 100, 0.01, 12/31. Stand: 24 Kern-Tests bestanden, 94/329 Testfälle im Kern, 0 Abweichungen.

## Offener Punkt: Rundung der Abgabe (dringend, wichtig für große Beträge)
Der Kern liefert keine Zahl, wenn die Abgabe mehr als zwei Nachkommastellen hat (z. B. 12.345.678,90 € × 5 % = 617.283,945 €), weil die Rundungsregel von KSK/DRV nicht belegt ist. Bei großen Beträgen tritt das oft auf. In die nächste Recherche (Recherche 5) aufnehmen: Rundung im Abgabebescheid der KSK (Quelle, Beispielrechnungen), SGB IV-Rundungsregeln, Rechtsprechung. Bis dahin: keine eigene Rundung, Antwort „Rundung ungeklärt".
Tests mit großen Zahlen: Kern rechnet exakt (Decimal) bis 99.999.999.999,99; 200.000 Positionen in 0,04 s. Auftrag 1d/1e um Formatierung, Schreibweisen, Sinnprüfung, Mengen und Zeitmessung ergänzt.

## Pflege für künftige Updates
- `aufgaben/PFLEGE_Update_Anleitung.md` (auch im Projekt als `claude/ksk-assistent-pflegeanleitung.md`) und `CLAUDE.md` im Projektstamm angelegt. Einstieg für ein Update: beide lesen, dann Ablauf A–F.
- `scripts/erzeuge_pruefliste.py` ins Repo übernommen (mit Schutz vor Überschreiben eingetragener Entscheidungen).
- Bekannte Lücke: Pauschalen für 2027 fehlen im Blatt „Pauschalen nach Jahr".

## Übergabeprotokoll
`aufgaben/UEBERGABE_Stand_und_naechste_Schritte.md` angelegt (Stand, Reihenfolge, Wiederaufnahme). Bei jedem größeren Schritt aktualisieren.

## Chatbot Teil 1b–1d (09.10.2026)
- Teil 1b: `kern/rechnen.py` echt angebunden (vorher nur Eigenwerbung/Positionen verdrahtet; jetzt alle 7 Fallgruppen: Vorauszahlung, Säumniszuschlag, Verpflegung, Übungsleiterpauschale, Kommission, Schätzung Ausland, Rechnungsanalyse).
- Teil 1c: Antwort-Kontrolle (`app/pruefung.py`) läuft jetzt in jedem Antwort-Pfad, nicht nur im Hauptpfad; Betrags-Erkennung gehärtet (Tausenderpunkt-Bug behoben).
- Teil 1d: Bausteinantwort mit Platzhaltern (`app/baustein.py`) – das Sprachmodell schreibt nur noch `{NAME}`-Platzhalter, nie Werte/Zahlen/Paragrafen/Gerichte selbst; Faktenbestätigung vor der Berechnung (`app/bestaetigung.py`, `POST /bestaetigen`), Sitzung nur im Arbeitsspeicher.
- Nachtrag 1 (6 Lücken aus Audit-Runde 2: Zahlwörter, Mengenangaben, Normbezüge im Wortlaut, Gerichtsworte ohne Aktenzeichen, ausgeschriebene Fassung, Schlussfolgerung ohne Zahl) behoben.
- Nachtrag 2 (17 Lücken aus Audit-Runde 3, `aufgaben/PRUEFBERICHT_Chatbot_Teil1d.md`): Schlussfolgerungen in anderen Worten, Gerichte/Behörden/Bestätigungen namentlich, verschleierte/falsch geschriebene Platzhalter (`{{ABGABE}}`, `{abgabe}`), Links/Mailadressen, gefälschter Schlusssatz – alle behoben; Zählung, wie viele Musterdialog-Sätze sich als feste Bausteine darstellen ließen (20 von 25) in `aufgaben/FUNDE_Chatbot.md`. Offen (wartet auf Nutzerentscheidung): feste, vom Berufsträger geprüfte Bausteine statt freier Sätze mit Wortlisten-Kontrolle – Wortlisten sind grundsätzlich nie vollständig.
- Property-based Test (`tests/app/test_eigenschaften.py`, ≥ 2000 Zufallsfälle) fand und behob 3 weitere Lücken (zwei in `app/pruefung.py`, eine fehlende Fehlerbehandlung in `app/router.py` für drei Kernfunktionen ohne `RegisterLuecke`-Schutz).
- Sandbox-Nachweis (frischer Klon, neue venv): 155 Tests grün, `scripts/pruefe_alles.py` ALLES GRÜN (`aufgaben/SANDBOX_Nachweis.md`). In der lokalen Arbeitskopie dieser Sitzung meldet der Prüfsummen-Schritt einen Fehler, der sich als lokale CRLF-Checkout-Eigenheit erwiesen hat (frischer Klon ist davon nicht betroffen, siehe `aufgaben/FUNDE_Chatbot.md`).

## Stand 09.10.2026 (Nachtrag 2 geprüft, Teil 1f vorbereitet)
- Nachtrag 2 abgenommen: `gegenproben_teil1d_runde3.py` 0 Lücken (vorher 17); `pruefe_alles --ohne-app` grün; 6 Fehler in `tests/app` nur wegen fehlender Pakete fastapi/httpx in der Prüfumgebung.
- Entscheidung: Bausteine als **Mischform** (siehe Übergabe). Fehlermelde-Programm als Konzept: `aufgaben/SYSTEMBESCHREIBUNG_fuer_KI.md` (Abschnitt 7), Umsetzung in Schritt 7.
- Auftrag Teil 1f: `aufgaben/PROMPT_ClaudeCode_Chatbot_1f_Rechtsform_Auskunft.md`. Abnahme: `python aufgaben/audit/abnahme_teil1f.py`, Ausgangszustand 18 Lücken, Ziel 0. Danach 1g (Mischform), 1e (Prüf-Sandbox), 2 (RAG).
- Kern: ausgeschlossene Positionen werden erklärt (`ausgeschlossene_positionen`, 27 Kern-Tests).

## Chatbot Teil 1f erledigt (09.10.2026) -- Rechtsform je Position, Säumniszuschlag, Auskunft, Fundstellen, Schaltflächen, Mistral-Robustheit, Oberfläche
- Abnahme `python aufgaben/audit/abnahme_teil1f.py`: **0 von 18 Lücken** (Ausgangszustand 18). `gegenproben_teil1d_runde3.py`: weiterhin 0. `scripts/pruefe_alles.py`: ALLES GRÜN bis auf den bereits bekannten, lokal-nur-hier auftretenden Prüfsummen-Befund (siehe `aufgaben/FUNDE_Chatbot.md`, im frischen Klon bestätigt unauffällig).
- A: `Position.auftragnehmer_typ` gilt je Position (vorher nur global -- gemischte Positionen zählten eine GmbH-Position fälschlich mit). B: Säumniszuschlag bekommt die neue Anzeigeklasse „Säumniszuschlag (Vorschlag)" statt der irreführenden Kernklasse „Abgabepflichtig". C: neue Anfrageart `auskunft` (Abgabesatz/Schwelle/Meldefrist/Aufbewahrung/Pauschale direkt aus dem Register; Pauschale bleibt „Nicht abgedeckt", Fund siehe FUNDE_Chatbot.md) mit Anzeigeklasse „Auskunft aus dem Regelwerk". D: `fassung_fuer_jahr` ohne Festwert, Archiv-Kopie-Datumsangaben in Fundstellen bereinigt. E: `rueckfrage_optionen` für geschlossene Fragen (Einnahmeabsicht, Rechtsform, seit J.1 auch Jahr aus dem Register). F: Pflichtangaben je Rechenart statt allgemeiner Bewertungsfragen.
- I (aus dem Mistral-Test, `aufgaben/PRUEFBERICHT_Mistral_Lauf1.md`): Extraktions-Prompt verbietet Rechtseinstufungen ohne ausdrückliche Nutzeraussage; Plausibilitätsprüfung gegen einen genannten Gesamtbetrag (`app/plausibilitaet.py`); `LLMFehlgeschlagen`-Ausnahme fängt jede unbrauchbare Modellantwort ab (kein Absturz/HTTP 500); Mistral-Adapter robust gegen Large 4 (`top_p`, Content-Blöcke, `MISTRAL_TIMEOUT`).
- J (Oberflächen-Befunde aus dem ersten Codespace-Test): Rückfrage-Knopf schickte bisher den Fragetext selbst und löste eine Schleife aus -- jetzt schickt er nur noch bei geschlossenen Fragen die Option; `**fett**`/`*kursiv*` werden jetzt sicher (ohne `innerHTML`) dargestellt statt mit Sternchen; neue Anfrageart `hinweis` für Begrüßung/Smalltalk ohne Modellaufruf; Kopfzeile kürzt lange Modusnamen mit Ellipse. Neuer CI-Job „oberflaeche" (Playwright, Chromium) in `.github/workflows/pruefen.yml`; Job „abnahme-1f" blockiert jetzt den Lauf (`continue-on-error` entfernt).
- Tests: `tests/app/test_teil1f.py` (jede Abnahme-Zeile als Unittest, plus I/J-Zusatztests) -- Gesamt 205 Tests in `tests/app`, 1 erwartet übersprungen (kein `MISTRAL_API_KEY`).
- Neue Ergebnisklassen zur Freigabe vorgelegt (`aufgaben/FUNDE_Chatbot.md`): „Säumniszuschlag (Vorschlag)", „Auskunft aus dem Regelwerk", „Hinweis".
- Nächster Schritt laut Übergabe: 1g (Mischform aus festen Bausteinen und freiem Text für Rechtsaussagen/Rückfragen), danach 1e (Prüf-Sandbox/Verifier), danach Teil 2 (RAG).

## Chatbot Teil 1f, Nachtrag erledigt (10.10.2026) -- Zuordnung absichern, Rückfragen ohne Modell, Rückfrage nur nach Kernbedarf
- Hintergrund: Mistral-Lauf nach 1f (`aufgaben/audit/ergebnisse_mistral.md`) zeigte, dass das echte Modell robust läuft (keine Ausnahme, 0,8 s/Aufruf, Rechtsform je Position und Fahrtkosten richtig gezogen), aber Anfragearten falsch zuordnet (Rechnungsfrage → `auskunft` ohne Thema; Verein mit Beträgen → `hinweis`) und Rückfragen frei schreibt (erfundene Zusatzfragen, kaputte Sätze, falsche Summe inkl. GmbH-Position).
- Abnahme `python aufgaben/audit/abnahme_teil1f_nachtrag.py`: **0 von 7 Lücken** (Ausgangszustand 7). `abnahme_teil1f.py`, `gegenproben_teil1d_runde3.py`: weiterhin je 0. `scripts/pruefe_alles.py`: ALLES GRÜN bis auf den bekannten, lokal-nur-hier auftretenden Prüfsummen-Befund.
- A: `app/zuordnung.py` + `app/auskunft_begriffe.json` (Konfiguration) prüfen deterministisch, ob die Nutzerfrage selbst einen Begriff zum vom Modell gelieferten `auskunft`-Thema nennt bzw. keine Sachangabe für `hinweis` enthält -- sonst wird die Anfrageart verworfen und wie `bewertung` behandelt. B: Rückfragen (Pflichtangaben- und Kern-Rückfragen) werden jetzt ausschließlich aus festen Textbausteinen gebaut (`app/router.py::_rueckfrage_antwort`), kein Modellaufruf mehr dafür. C: Rechtsform-Rückfrage nur noch für Honorar-/Entgeltpositionen (Sonderrollen aus `kern.rechnen._AUSSCHLUSSGRUENDE` gelesen); `leistungsart` ist keine Pflichtangabe mehr (Fund: keine Kernfunktion der Bewertung braucht sie). D: Säumniszuschlag heißt jetzt "Säumniszuschlag: …" statt "Abgabe: …"; `jahr_plausibel`-Grenzen (1980/2100) bewusst unverändert gelassen (Begründung in FUNDE_Chatbot.md); Kern-Formatierungsbug "5000.00 €" (Punkt statt Komma) gemeldet.
- Tests: `tests/app/test_teil1f_nachtrag.py` (jede Abnahme-Zeile plus Direkttests für `app/zuordnung.py`/`_rueckfrage_antwort`) -- Gesamt 227 Tests in `tests/app`, 1 erwartet übersprungen. Neuer blockierender CI-Job `abnahme-1f-nachtrag`.

## Chatbot Teil 1g erledigt (10.10.2026) -- Mischform: Antwort-Körper aus festen Textbausteinen, Modell nur noch Fallbeschreibung
- Hintergrund: Mistral-Lauf nach dem Nachtrag (`aufgaben/audit/ergebnisse_mistral_small_nachtrag.md`) zeigte 7 von 9 blockierten Antworten, weil das Modell weiterhin Zahlwörter/Paragrafen/Verwaltungspraxis in den Antworttext schrieb. Entscheidung (09.10.2026): Mischform -- Rechtsaussagen nur aus festen, im Regelkatalog gepflegten Textbausteinen; das Modell beschreibt höchstens den Einzelfall in einem Satz, ohne jede Rechtsaussage.
- Abnahme `python aufgaben/audit/abnahme_teil1g.py`: **0 von 15 Lücken** (Ausgangszustand 15). `abnahme_teil1f.py`, `abnahme_teil1f_nachtrag.py`, `gegenproben_teil1d_runde3.py`: weiterhin je 0. `scripts/pruefe_alles.py`: ALLES GRÜN bis auf den bekannten, lokal-nur-hier auftretenden Prüfsummen-Befund (im frischen Klon/venv bestätigt unauffällig, siehe `aufgaben/FUNDE_Chatbot.md`).
- A: neues Regelkatalog-Blatt "Textbausteine" (16 Bausteine TB-01..TB-16, vom Auftraggeber vorbereitet), gelesen und geprüft von `app/textbausteine.py` (ID eindeutig, Text/Prüfstatus gesetzt, Platzhalter bekannt; ein Fehler dort bricht beim Programmstart ab, nicht erst bei der ersten Frage). Auswahl pro Antwort nach benötigten/verbotenen Platzhaltern, Ergebnisklasse und Gültigkeitsjahr, sortiert nach Reihenfolge/ID; passt nichts, greift der strukturell erkannte (nicht über seine ID verdrahtete) Leerfall-Baustein, protokolliert als "Baustein fehlt".
- B/C: `LLM`-Schnittstelle, `FakeLLM`, `MistralLLM` bekommen `beschreibe_fall` (ein kurzer Satz, nur Platzhalter, nie Werte) statt `formuliere_antwort` (entfernt, nirgends mehr aufgerufen). `app/router.py::_ausgeben` baut den Körper aus den Textbausteinen; die Fallbeschreibung läuft durch dieselbe `pruefe_rohtext`-Kontrolle wie früher der ganze Körper -- verstößt sie oder fällt das Modell mit irgendeinem Fehler aus, entfällt NUR dieser eine Satz, nie mehr die ganze Antwort (kein "Prüfung fehlgeschlagen" mehr dafür). Das zweite Netz (`app/pruefung.py` auf dem fertigen Text) bleibt unverändert aktiv.
- Nebenbefund behoben: `app/baustein.py::PLATZHALTER_BESCHREIBUNG` fehlten `RUECKSTAND`/`MONATE`/`DATUM` (seit Teil 1f in `erzeuge_platzhalter`, aber nie dort ergänzt) -- fiel beim ersten Laden der Textbausteine sofort auf (TB-05).
- Bestehende Tests angepasst, keine Prüfung abgeschwächt (Begründung je Datei in `aufgaben/FUNDE_Chatbot.md`): `test_gegenproben.py/_2/_3.py`, `test_llm_fake.py`, `test_mistral_rauchtest.py`, `test_teil1f.py` -- alle griffen bisher über `formuliere_antwort` an bzw. riefen es direkt auf; jetzt über `beschreibe_fall`, mit der vom Auftrag selbst vorgegebenen neuen Erwartung (nur der Satz entfällt, nie die Antwort).
- Spannung mit `aufgaben/audit/gegenproben_teil1d_runde3.py` (zeigte nach dem Umbau 31 statt 0 Lücken, weil sein Angriff über das jetzt nie mehr aufgerufene `formuliere_antwort` lief) hat der Nutzer selbst gelöst (Commit `bb2ec59`, außerhalb dieses Auftrags): Angriff jetzt über `beschreibe_fall`, Prüfung "böser Text taucht in keiner Antwort auf" statt "ganze Antwort blockiert". Danach 0 von 31 Lücken.
- Tests: `tests/app/test_teil1g.py` (35 Tests, jede Abnahme-Zeile G1-G7 plus Jahresgrenze/fehlende-doppelte-ID/Auswahlregeln einzeln/verbotene Fallbeschreibung/Modellausfall/Mischfall 4 Positionen) -- Gesamt 262 Tests in `tests/app`, 1 erwartet übersprungen. Neuer blockierender CI-Job `abnahme-1g`.
- Offen (laut Auftrag Abschnitt A ausdrücklich erlaubt, Folgeauftrag): Rückfrage-Bausteintexte in `app/pflichtangaben.py`/`_rueckfrage_antwort` stehen weiterhin im App-Code, nicht im Regelkatalog.
- Nächster Schritt laut Übergabe: 1e (Prüf-Sandbox/Verifier), danach Teil 2 (RAG).

## Prüfkatalog Stufe 1 angelegt (10.10.2026)
- Anlass: erster Livetest im Codespace (Demo-Modus und Mistral small) fand eine kritische Lücke (Verwerterart wird still als Eigenwerbung angenommen, `aufgaben/PROMPT_ClaudeCode_Chatbot_Livetest1_Befunde.md`). Die bisherigen Mistral-Läufe prüften nur, ob geantwortet wird, nicht ob richtig.
- Neu: `aufgaben/audit/pruefkatalog.json` (51 erfundene Fälle: je einer zu den 40 Fallgruppen, einige doppelt, dazu 8 Kontrollfälle; Soll aus den vorhandenen Testfällen), `aufgaben/audit/pruefkatalog_lauf.py` (Soll gegen Ist: RICHTIG / NACHGEFRAGT / FALSCH / FEHLER), GitHub-Ablauf `.github/workflows/pruefkatalog.yml` (Demo + Mistral small/medium/large, Start von Hand).
- Ziel Stufe 1: 0 FALSCH, 0 FEHLER, ≥ 90 % richtig bei sicherem Soll. Danach Stufe 2 (Steuerberater testet 10–15 eigene Fälle), Stufe 3 (Pilot).
- Ausgangslage Demo-Modus: 15 RICHTIG, 30 NACHGEFRAGT, 6 FALSCH, 0 FEHLER (`aufgaben/audit/pruefkatalog_ergebnis_demo.md`). Die FALSCH-Fälle gehen auf L1 (Verlag/Verein still als Eigenwerbung, Einnahmeabsicht nicht abgefragt) und auf die Betragserkennung des Demo-Modus zurück (USt, Reise-, Druckkosten als eigene Honorarposition).
- `pruefe_alles.py --ohne-app`: ALLES GRÜN (App-Tests hier nicht ausführbar, Paket fastapi fehlt in der Prüfumgebung).
- Nachtrag (10.10.2026): Vergleichsmodus `--llm mistral-roh` – dieselben Fragen direkt an Mistral, ohne Kern, Regelwerk und Quellen, Antwort als JSON (Ergebnis, Zahl, Begründung, Fundstellen). Im GitHub-Ablauf als `roh-small` und `roh-large`. Zweck: messen, ob der KSK-Assistent besser ist als das rohe Modell, und erfundene Fundstellen des rohen Modells sichtbar machen.
- Hinweis zur Reihenfolge: Dieser Prüfkatalog lief gegen den Stand VOR der Code-Behebung von L1-L6 (siehe nächster Abschnitt) -- die oben genannten FALSCH-Fälle zu L1 sollten nach der Behebung erneut gelaufen werden (Folgeschritt, noch offen).

## Livetest-Befunde behoben (10.10.2026) -- `aufgaben/PROMPT_ClaudeCode_Chatbot_Livetest1_Befunde.md`
- Hintergrund: erster Livetest im Codespace (Demo-Modus und Mistral) fand 6 Befunde (L1-L6). Auftrag: nur in `app/` und `tests/app/` arbeiten.
- **L1 (kritisch, behoben):** `verwerterart` ist jetzt Pflichtangabe für jeden Kernaufruf, der davon abhängt (Positionen, Veranstaltungen) -- vorher nahm `app/router.py` bei fehlender Angabe stillschweigend „generalklausel"/Eigenwerbung an (eine Werbeagentur wäre so fälschlich mit Schwelle statt ohne geprüft worden). `app/pflichtangaben.py` fragt jetzt gezielt nach (neue Rückfrage mit Schaltflächen Eigenwerbung/Typischer Verwerter/Veranstalter); `app/router.py::_rufe_kern_auf` hat zusätzlich einen Wächter (kein Default mehr, auch bei direktem Aufruf). `verwerterart` erscheint jetzt in der Faktenbestätigung (`app/bestaetigung.py`, neues `VERWERTERART_LESBAR` in `app/schema.py`).
- **L2 (behoben):** `app/llm/fake.py` (Demo-Modus) wertet jetzt Verlauf UND neue Nachricht gemeinsam aus -- vorher gingen Jahr/Betrag nach einer Rückfrage-Antwort verloren.
- **L3 (behoben):** Umlaute werden vor dem Mustervergleich normalisiert (ü→ue usw.), sonst erkannte die Heuristik die eigene Schaltfläche „natürliche Person" nicht; zusätzlich „Einzelperson"/„Einzelunternehmer"/„Privatperson" als Synonyme. Eigener Test iteriert über alle echten `rueckfrage_optionen`.
- **L4:** laut Auftrag nur dokumentiert (`aufgaben/FUNDE_Chatbot.md`), nicht umgebaut (Demo-Modus-Grenze).
- **L5 (teilweise behoben):** echte Umlaute in `FAKTEN_BESTAETIGUNG_NOETIG`/`PRUEFUNG_FEHLGESCHLAGEN` (app/ergebnisklassen.py) und den Rückfragetexten (app/pflichtangaben.py); Faktenbestätigung zeigt die Fakten nicht mehr doppelt (app/static/index.html zeigt bei dieser Ergebnisklasse nur noch die Liste, nicht zusätzlich den vollen Fließtext); „Anfrageart: bewertung" weggelassen, interne Rollen-Codes (z. B. „fahrtkosten_nachgewiesen") jetzt lesbar übersetzt. Die unformatierte Subsumtionszeile hat ihre Ursache in `kern/rechnen.py` (außerhalb des erlaubten Bereichs) -- dokumentiert, nicht geändert.
- **L6 (teilweise behoben):** `app/router.py::_vereinheitliche_fundstellen` fasst unterschiedlich geschriebene, aber inhaltlich gleiche Fundstellen zusammen (z. B. „S. 2" und „Satz 2 (aktuell)"). Die falsche Fundstelle „§ 54" für Jahre, in denen sie nicht einschlägig ist, hat ihre Ursache in `kern/rechnen.py::pruefe_eigenwerbung` (fester Text, nicht jahresabhängig) -- dokumentiert, nicht geändert.
- Tests: neue Datei `tests/app/test_livetest1_befunde.py` (19 Tests), bestehende Tests angepasst, wo jetzt `verwerterart` explizit nötig ist (`test_pflichtangaben.py`, `test_router.py`, `test_teil1f_nachtrag.py`, `test_abnahme_musterdialoge.py`, `test_main.py`). Gesamt 284 Tests in `tests/app`, 1 erwartet übersprungen.
- Geprüft: `abnahme_teil1f.py`, `abnahme_teil1f_nachtrag.py`, `abnahme_teil1g.py`, `gegenproben_teil1d_runde3.py` weiterhin je 0 Lücken. `scripts/pruefe_alles.py`: ALLES GRÜN bis auf den bekannten, lokal-nur-hier auftretenden Prüfsummen-Befund (unverändert, nicht durch diese Sitzung verursacht).
- Folgeschritt (siehe Hinweis im Prüfkatalog-Abschnitt oben): `aufgaben/audit/pruefkatalog_lauf.py` im Demo-Modus erneut laufen lassen, jetzt mit behobenem L1 -- die 6 FALSCH-Fälle sollten sich verbessern.

## Unabhängige Prüfung der Livetest-Behebung (10.10.2026, Claude)
- `pruefe_alles.py --ohne-app`: ALLES GRÜN. Abnahmen 1f, 1f-Nachtrag, 1g, Gegenproben 1d Runde 3: je 0 Lücken.
- Prüfkatalog Demo-Modus nach der Behebung: 26 RICHTIG (vorher 15), 19 NACHGEFRAGT, 6 FALSCH, 0 FEHLER. L1 ist behoben: Werbeagentur (P-05), Verlag (P-06), Musikverein (P-16) und Verein ohne Angabe zur Einnahmeabsicht (K-07) sind nicht mehr falsch; das System fragt jetzt nach der Art des Auftraggebers.
- Die 6 verbleibenden FALSCH (P-04a, P-28, P-30, P-31, P-32, P-39) gehen alle auf L4 zurück: Der Demo-Modus macht jeden Eurobetrag zur Honorarposition (USt, Reise-, Bewirtungs-, Druckkosten, Zahlung an Manager; „fünf Rechnungen je 250 €" ergibt nur zwei Positionen). In der App sieht der Nutzer das in der Faktenbestätigung; der Prüflauf bestätigt automatisch. Aussagekräftig ist jetzt der Lauf mit Mistral (Ablauf „Prüfkatalog").

## Erster Prüfkatalog-Lauf mit Mistral (10.10.2026, Lauf 38056745573)
- Im Assistenten: small 22 RICHTIG / 26 NACHGEFRAGT / 3 FALSCH / 0 FEHLER; medium 4 / 46 / 1 / 0; large 0 / 0 / 0 / 51 FEHLER (JSON im Codeblock, Adapter liest es nicht).
- Roh, ohne Assistent: small 14 RICHTIG / 35 FALSCH / 2 FEHLER; large 13 RICHTIG / 2 NACHGEFRAGT / 29 FALSCH / 7 FEHLER. Typische Fehler: falscher Abgabesatz (Abgaben um den Faktor 2–3 daneben), Eigenwerbung unter der Schwelle als abgabepflichtig. Zitierte BSG-Aktenzeichen: 6 von 8 stehen nicht in der Quellenbasis (nicht prüfbar).
- Befunde M1–M4 als Auftrag: `aufgaben/PROMPT_ClaudeCode_Chatbot_Pruefkatalog1_Befunde.md` (Rückfrage-Schleife, large-Adapter, Verlag mit Eigenwerbung, Modell setzt Verwerterart gegen den Wortlaut).
- Katalog-Korrektur: K-03 prüfte auf „5,0", das System schreibt richtig „5 %"; jetzt sind beide Schreibweisen zulässig (Fehler im Katalog, nicht im System).
- M2 behoben (10.10.2026, Claude): `app/llm/mistral.py` entfernt vor `json.loads` einen umschließenden Markdown-Codeblock bzw. Text vor/nach dem JSON; die Prüfung gegen das Fakten-Schema bleibt unverändert. 7 neue Tests (`tests/app/test_mistral_codeblock.py`). Prüfkatalog-Ablauf um `mistral-large-4` ergänzt.

## Prüfkatalog-Befunde M1-M4 behoben (10.10.2026) -- `aufgaben/PROMPT_ClaudeCode_Chatbot_Pruefkatalog1_Befunde.md`
(M2 war zur selben Zeit parallel schon vom Nutzer/einer anderen Sitzung behoben worden, siehe Eintrag direkt darüber -- hier nur noch `response_format: json_object` ergänzt, siehe M2-Punkt unten.)
- **M1 (dringend, behoben):** geschlossene Rückfragen (Schaltflächen) werden jetzt DETERMINISTISCH beantwortet, ohne erneuten Modellaufruf. Neue Route `POST /knopf` (`app/main.py`) → `app/router.py::wende_feldantwort_an`: holt die fürs Sitzungskennung gespeicherten (noch nicht bestätigten) Fakten, wendet `feld`/`wert`(/`position`) an und validiert neu gegen das Schema. `app/pflichtangaben.py::rueckfrage_optionen` liefert dafür je Option jetzt `feld`/`werte`(/`position`) mit (vorher nur Anzeige-Text). Jede Pflichtangaben-Rückfrage bekommt jetzt selbst schon eine `sitzungskennung` (vorher nur die Faktenbestätigung) -- Voraussetzung dafür, dass ein Knopf später etwas wiederfindet. `app/static/index.html` schickt eine Schaltfläche mit Feld-Zuordnung über `/knopf`, sonst (offene Fragen, oder ohne Sitzung) wie bisher als Freitext über `/frage`.
  - Punkt 2 (Sitzungswerte gehen nicht verloren): neue `app/router.py::_fakten_zusammenfuehren` -- eine freie Folgenachricht über dieselbe Sitzung ERGÄNZT nur, was sie selbst liefert; fehlende Felder bleiben aus der Sitzung erhalten.
  - Punkt 3 (Rechtsform-Synonyme deterministisch, auch bei Mistral): neues `app/rechtsform_erkennung.py` (gemeinsame Muster für `app/llm/fake.py` und `app/zuordnung.py::ergaenze_rechtsform`, keine Code-Duplizierung mehr) -- ergänzt `auftragnehmer_typ` aus dem Nutzertext, wenn das Modell ihn nicht selbst setzt (global oder bei genau einer Position; bei mehreren Positionen wird nicht geraten).
- **M2 (Codeblock-Teil bereits parallel behoben, hier ergänzt):** `app/llm/mistral.py::_json_aus_antwort` entfernt einen umschließenden Markdown-Codeblock bzw. Text drumherum (siehe Eintrag oben); hier zusätzlich ergänzt: die Fakten-Extraktion schickt jetzt `response_format: {"type": "json_object"}` mit (Mistral-API-Doku).
- **M3 (fachlich, kritisch, behoben) + M4 (behoben):** neues `app/zuordnung.py::absichere_verwerterart` mit Begriffsliste `app/verwerterart_begriffe.json` (wie `auskunft_begriffe.json`). M3: nennt der Text selbst einen Begriff für „typischer Verwerter" (Verlag, Werbeagentur, Galerie, …), gewinnt das immer -- auch gegen einen vom Modell gelieferten „eigenwerber" (ein typischer Verwerter nach § 24 Abs. 1 hat keine Schwelle, unabhängig vom Zweck der einzelnen Zahlung). M4: ein vom Modell gelieferter Wert wird verworfen (→ erneute Rückfrage), wenn der Text einen ANDEREN, widersprechenden Begriff belegt; fehlt im Text jeder Begriff, bleibt ein bereits gesetzter Wert unangetastet (sonst hätten kurze Rückfrage-Antworten ohne erneute Begriffsnennung ständig den schon geklärten Wert verloren). Wortgrenzen-Vergleich (`\b`), damit z. B. „orchester" nicht fälschlich in „Hobbyorchester" matcht (beim ersten Testlauf gefunden, Fall P-16).
- **Nebenbefund beim Beheben von M3 gefunden und app-seitig korrigiert** (Ursache in `kern/rechnen.py::pruefe_typischer_verwerter`, siehe `FUNDE_Chatbot.md`): die Kernfunktion liefert „Abgabepflichtig" auch bei Bemessungsgrundlage 0 (z. B. Zahlung an eine ausgenommene GmbH/KG). `app/router.py::_nach_bestaetigung` korrigiert die ANZEIGE (Bemessungsgrundlage 0 bei Kernklasse Abgabepflichtig → „Nicht abgabepflichtig"), der Kern selbst bleibt unverändert.
- Tests: neue Datei `tests/app/test_pruefkatalog1_befunde.py` (15 Tests: Knopf-Dialog Ende-zu-Ende, Sitzungswerte bleiben erhalten, Rechtsform-Ergänzung, M3/M4-Gegenprobe inkl. Hobbyorchester-Regressionstest) und Ergänzungen in `tests/app/test_mistral_rauchtest.py` (1, `response_format`; der Codeblock-Teil ist in `tests/app/test_mistral_codeblock.py`, siehe Eintrag oben) und `tests/app/test_main.py` (2, `/knopf` Ende-zu-Ende). Gesamt 309 Tests in `tests/app`, 1 erwartet übersprungen.
- Geprüft: `abnahme_teil1f.py`, `abnahme_teil1f_nachtrag.py`, `abnahme_teil1g.py`, `gegenproben_teil1d_runde3.py` weiterhin je 0 Lücken. `scripts/pruefe_alles.py`: ALLES GRÜN bis auf den bekannten, lokal-nur-hier auftretenden Prüfsummen-Befund. `pruefkatalog_lauf.py --llm fake`: 28 RICHTIG (vorher 26), 17 NACHGEFRAGT, **dieselben 6 FALSCH wie vorher** (P-04a, P-28, P-30, P-31, P-32, P-39 -- alle laut Auftrag/L4 außerhalb dieses Auftrags), 0 FEHLER -- `aufgaben/audit/pruefkatalog_ergebnis_demo.md` erneuert.
- Offen: M1/M3/M4 sind mit Mistral noch nicht erneut gelaufen (kostet/braucht Schlüssel) -- nächster Prüfkatalog-Lauf mit Mistral sollte zeigen, ob die Rückfrage-Schleife jetzt aufhört und P-06/P-04b jetzt richtig sind (M2 mit large 4 bereits vom Nutzer/einer anderen Sitzung geprüft, siehe Eintrag oben).
- Zweiter Prüfkatalog-Lauf (10.10.2026, Lauf 38058189753, nach M2, VOR der Behebung von M1/M3/M4): small 22 RICHTIG / 29 NACHGEFRAGT / 0 FALSCH / 0 FEHLER; medium 5 / 46 / 0 / 0; large 19 / 22 / 0 / 10. Die 10 FEHLER bei large kamen in Serie nach je ca. 0,3 s (P-06 bis P-14, K-01) – vermutlich Ratenbegrenzung bei Mistral durch parallele Läufe, nicht das JSON-Format. `mistral-large-4` brauchte über 45 Minuten für den Katalog (Lauf abgebrochen) und ist für den Chat zu langsam; wieder aus dem Ablauf genommen. Hinweis: small antwortete bei P-04b und P-06 anders als im ersten Lauf, obwohl am Code dafür nichts geändert wurde – die Ergebnisse schwanken von Lauf zu Lauf.
- Prüfkatalog drückt jetzt bei Rückfragen die passenden Knöpfe wie ein Nutzer (`knoepfe` je Fall, Aufruf von `router.wende_feldantwort_an`, also derselbe Weg wie `POST /knopf`). Demo-Modus danach: 31 RICHTIG / 13 NACHGEFRAGT / 7 FALSCH. Neu sichtbar: Befund M5 (Generalklausel wird wie Eigenwerbung gerechnet), als Ergänzung in `aufgaben/PROMPT_ClaudeCode_Chatbot_Pruefkatalog1_Befunde.md`.
- Dritter Prüfkatalog-Lauf (10.10.2026, Lauf 38070498025, Stand mit M1–M4 und Knopf-Simulation): small 35 RICHTIG / 13 NACHGEFRAGT / 1 FALSCH / 2 FEHLER; medium 35 / 12 / 1 / 3; large 16 / 4 / 1 / 30 (vermutlich Ratenbegrenzung, Befund M6). Roh zum Vergleich: small 15 RICHTIG / 36 FALSCH; large 13 / 20 FALSCH / 16 FEHLER. Die FALSCH-Fälle im Assistenten sind P-08 und P-07 (beide Befund M5, Generalklausel) sowie bei medium P-18b („Nicht abgedeckt" statt Rückfrage); letzteres wertet der Katalog ab jetzt als NACHGEFRAGT, weil es keine gefährliche Antwort ist.

## Befunde M5 und M6 behoben (10.10.2026) -- `aufgaben/PROMPT_ClaudeCode_Chatbot_Pruefkatalog1_Befunde.md`
- **M5 (fachlich, kritisch, behoben):** `app/pflichtangaben.py` fragt jetzt bei `verwerterart == "generalklausel"` IMMER gezielt nach, ob/wie viele Veranstaltungen es gab (`FRAGE_VERANSTALTUNGSZAHL`, bisher ungenutzt) und nach der Einnahmeabsicht -- vorher fiel ein Generalklausel-Fall ohne bekannte Veranstaltungszahl stillschweigend in den `positionen`-Zweig und wurde mit der (falschen) Eigenwerbungs-Schwelle/-Fundstelle geprüft. `app/router.py::_rufe_kern_auf` hat dafür einen eigenen Wächter (wie beim verwerterart-Wächter) und ruft `K.veranstaltungen` nie mehr mit `generalklausel` auf, solange die Veranstaltungszahl unbekannt ist.
  - Zweites Beispiel (0 Veranstaltungen darf nicht "befreit" bedeuten): `kern.rechnen.veranstaltungen` prüft die Drei-Veranstaltungen-Ausnahme mit `anzahl <= 3`, was auch für `anzahl == 0` zutrifft -- obwohl die Ausnahme nur für Entgelte AUS Veranstaltungen gedacht ist. Da `kern/` außerhalb des erlaubten Bereichs liegt: `app/router.py` ruft die Kernfunktion bei `veranstaltungszahl == 0` mit einem Ersatzwert (`_KEINE_VERANSTALTUNGSAUSNAHME_ANZAHL = 1.000.000`) auf, der die Ausnahme sicher nicht auslöst und stattdessen die (korrekte) Schwellenprüfung der Generalklausel mit ihrer eigenen Fundstelle durchläuft (geprüft: P-07, 3.000 € → 150,00 € Abgabe, exakt wie gefordert). Details/Grenzen (kosmetisch ungenaue Kern-Begründung) in `FUNDE_Chatbot.md`.
  - Tests (neu `tests/app/test_pruefkatalog1_m5_m6_befunde.py`): P-08 (drei Veranstaltungen) → nicht abgabepflichtig; P-09 (vier) → abgabepflichtig 250,00 €; Generalklausel ohne Einnahmeabsicht/ohne Veranstaltungszahl → Rückfrage; P-07-Fall (0 Veranstaltungen) → abgabepflichtig 150,00 €, nie die Eigenwerbungs-Fundstelle (§ 54) für Generalklausel-Fälle.
- **M6 (behoben):** `app/llm/mistral.py::_aufruf` wiederholt HTTP 429/503 jetzt bis zu `MISTRAL_RETRY_VERSUCHE` Mal (Standard 3) mit wachsender Wartezeit `MISTRAL_RETRY_WARTEZEITEN` (Standard 1, 3, 9 s; beide als Umgebungsvariablen, nicht fest im Code) -- ein vom Server gesendeter `Retry-After`-Wert hat Vorrang. Die Fehlermeldung an den Nutzer bleibt dieselbe feste Rückfrage; das Python-Log nennt den HTTP-Status und die Wartezeit. Tests: Testdoppel mit zweimal HTTP 429 und dann einer gültigen Antwort (sowie 503, `Retry-After`-Vorrang, alle Versuche erschöpft, andere Statuscodes bleiben unverändert ohne Wiederholung).
- Geprüft: `abnahme_teil1f.py`, `abnahme_teil1f_nachtrag.py`, `abnahme_teil1g.py`, `gegenproben_teil1d_runde3.py` weiterhin je 0 Lücken. `scripts/pruefe_alles.py`: ALLES GRÜN bis auf den bekannten, lokal-nur-hier auftretenden Prüfsummen-Befund. Gesamt 323 Tests in `tests/app`, 1 erwartet übersprungen.
- `pruefkatalog_lauf.py --llm fake`: weiterhin 28 RICHTIG / 17 NACHGEFRAGT / dieselben 6 FALSCH wie vorher, 0 FEHLER -- P-07/P-08/P-09 wechseln von (vorher fachlich falsch berechnet) zu "Rückfrage nötig" (NACHGEFRAGT, keine Regression), weil die NEUE offene Frage "wie viele Veranstaltungen" keine Schaltfläche hat und der Prüfkatalog dafür nur ausgeschriebene Zahlwörter ("drei", "vier") als Freitext nachschickt, die `app/llm/fake.py` (nur Ziffern vor "Veranstaltung") nicht versteht -- Demo-Modus-Grenze wie L4, mit echtem Mistral sollte das funktionieren (siehe `FUNDE_Chatbot.md`). Die eigentliche Korrektheit von M5 ist durch die direkten Router-Tests (mit vorgegebener Veranstaltungszahl) bestätigt.
- Offen: M5/M6 sind mit Mistral noch nicht erneut gelaufen (kostet/braucht Schlüssel) -- nächster Lauf sollte zeigen, ob P-07/P-08/P-09 jetzt richtig sind und ob large/medium trotz Ratenbegrenzung ohne FEHLER durchlaufen.
- Prüfung M5/M6 (10.10.2026, Claude): Katalog von Claude Code nicht verändert (Soll-Werte unabhängig). Alle Prüfungen grün, Abnahmen je 0 Lücken, GitHub „Prüfen" grün. M5 im Ergebnis behoben (P-08 nicht mehr falsch), aber bei „0 Veranstaltungen" gibt der Router dem Kern die Ersatzzahl 1.000.000 – die Antwort begründet dann mit „mehr als drei Veranstaltungen". Neuer Befund M7 (Kernfunktion für die Generalklausel ohne Veranstaltungen); Katalog prüft die Begründung bei P-07 jetzt mit.
- Vierter Prüfkatalog-Lauf (10.10.2026, Lauf 38080541809, Stand mit M1–M6): **0 FALSCH bei allen drei Modellen.** small 34 RICHTIG / 14 NACHGEFRAGT / 0 FALSCH / 3 FEHLER; medium 34 / 16 / 0 / 1; large 26 / 12 / 0 / 13. Roh zum Vergleich: small 14 RICHTIG / 37 FALSCH; large 15 / 33 FALSCH. Quote richtig bei sicherem Soll: small und medium 34 von 47 (72 %, Ziel 90 %). Die FEHLER sind „Antwort konnte nicht verarbeitet werden" (keine falsche Antwort; small scheitert dabei jedes Mal an K-01 „Jahr fehlt"). Der Prüflauf schreibt ab jetzt den Grund aus dem Lückenprotokoll in den Bericht, damit der nächste Lauf die Ursache zeigt.
- Offen: M7 (falsche Begründung bei Generalklausel ohne Veranstaltungen), Ursache der FEHLER, Kern-Ausbau für die Fallgruppen, die heute nur nachfragen.

## Befund M7 behoben (10.10.2026) -- `aufgaben/PROMPT_ClaudeCode_Chatbot_Pruefkatalog1_Befunde.md`
- Für diesen Auftrag ausdrücklich erlaubt: Änderung an `kern/rechnen.py` und `tests/test_kern.py` (sonst außerhalb des Arbeitsbereichs). Ersatzzahl `_KEINE_VERANSTALTUNGSAUSNAHME_ANZAHL` (aus M5) wieder entfernt.
- `kern/rechnen.py::veranstaltungen` hat jetzt einen eigenen Zweig für `anzahl == 0` (Generalklausel ohne Veranstaltungen, z. B. Nutzung durch Lizenzierung): eigene Prüfung mit der bereits vorhandenen Regel **R-13** (§ 24 Abs. 2 Satz 1 Nr. 2, Satz 2 KSVG -- Nutzung für Unternehmenszwecke mit Einnahmeabsicht, Summe über Schwelle), nicht mehr R-14/R-132 (die sind an die Veranstaltungszahl gekoppelt). Eigene, zutreffende Begründung statt "Mehr als drei Veranstaltungen und Summe über der Schwelle". `app/router.py` ruft die Kernfunktion wieder direkt mit der echten `veranstaltungszahl` auf.
- Tests: `tests/test_kern.py::GeneralklauselOhneVeranstaltungen` (4, direkt am Kern, inkl. Gegenprobe dass `anzahl >= 1` unverändert bleibt); `tests/app/test_pruefkatalog1_m5_m6_befunde.py` erweitert um die exakte `verboten_text`-Prüfung aus `pruefkatalog.json` (P-07: "Mehr als drei Veranstaltungen"/"drei Veranstaltungen" dürfen nie vorkommen) und die Fundstellen-Prüfung.
- Geprüft: `tests/test_kern.py` (31 Tests inkl. Wächter gegen Festwerte) grün; alle vier Abnahmen weiterhin 0 Lücken; `scripts/pruefe_alles.py` ALLES GRÜN bis auf den bekannten lokalen Prüfsummen-Befund; `pruefkatalog_lauf.py --llm fake` unverändert 28 RICHTIG/17 NACHGEFRAGT/6 FALSCH (P-07/P-08/P-09 bleiben im Demo-Modus bei NACHGEFRAGT -- Grund ist die Demo-Heuristik-Grenze aus dem M5/M6-Eintrag oben, nicht M7; die eigentliche Korrektheit ist durch die direkten Kern-Tests mit vorgegebener Veranstaltungszahl bestätigt).
- Offen: erneuter Prüfkatalog-Lauf mit Mistral sollte zeigen, ob P-07 jetzt ohne die verbotene Begründung durchläuft.

## Dialogtest Fallgrenzen (10.10.2026, Claude) – Anlass: manueller Mistral-Playground-Test
- **Reproduziert offline mit kontrollierten (idealen) Modellantworten, Ursache im Python-Ablauf:** (1) „Neuer, unabhängiger Fall" lief unter derselben Sitzung weiter; `_fakten_zusammenfuehren` übernahm Jahr 2026, Eigenwerbung, Rechtsform und die drei alten Rechnungen zu je 200 € in den neuen Fall. (2) Ein genannter Gesamtbetrag ohne Aufteilung wurde ignoriert; nach der Ergänzung fragte das System erneut nach dem Betrag. (3) Die festen Textprüfungen (Rechtsform, Verwerterart) durchsuchten auch den Text des alten Falls. Korrektur („drei statt vier Rechnungen") funktionierte schon vorher richtig, die alte Bestätigung wurde ungültig.
- **Behoben:** ausdrücklich neuer Fall (Begriffsliste `app/fallwechsel_begriffe.json`) startet eine neue Sitzung; Verlauf ans Modell und Textprüfungen nur ab Fallbeginn (`Sitzung.verlauf_start`); Gesamtbetrag gilt als bekannte Summe (Pflichtangaben, Kern), Bestätigung zeigt „Gesamtbetrag (Aufteilung auf Rechnungen unbekannt)"; eine einzelne Modell-Position gleich dem Gesamtbetrag wird nicht als Rechnung gezeigt (`zuordnung.gesamtbetrag_nicht_als_position`); Prompt trennt Gesamtbetrag, Einzelbetrag, Rechnungs- und Veranstaltungszahl; Knopf „Neuer Fall" in der Oberfläche.
- **Tests:** `tests/app/test_dialog_fallgrenzen.py` (13 Tests offline; 7 der ersten 10 scheitern am alten Stand). Live: `aufgaben/audit/dialog_live.py` + Ablauf „Dialogtest live" (5 Wiederholungen je Modell, Codeversion/Modell/Einstellungen/Laufzeiten/Fehler im Bericht `aufgaben/audit/dialog_live_{small,large}.md`). Letzter Lauf (Code `e09e757`): small und large je 5 von 5 bei allen Kernpunkten, 0 technische Fehler.
- **Offen (Entscheidung nötig):** (a) Das Modell übernimmt „für unsere eigene Werbung" nicht als Art des Auftraggebers (0 von 10) → eine Rückfrage per Knopf; vertretbar, weil die Art des Unternehmens entscheidet. (b) mistral-large leitet aus „Ein Fotograf" „natürliche Person" ab (in den Läufen 3–5 von 5), entgegen dem Prompt; sichtbar in der Faktenbestätigung. Eine Gegenprobe wie bei M4 würde Rechtsformen verwerfen, die bestehende Tests/Musterdialoge erwarten – deshalb nicht eingebaut. (c) „hat uns 500 Euro berechnet" (ohne „insgesamt") wird von beiden Modellen als eine Rechnung über 500 € gelesen (10 von 10); plausibel, aber nicht ausdrücklich. (d) Widersprüche (Positionen ≠ Gesamtbetrag) werden in der Bestätigung gewarnt, nicht als Rückfrage erzwungen. (e) Nach einem fertigen Ergebnis ohne „Neuer Fall" schickt die Oberfläche weiter den ganzen Verlauf (ohne Sitzung, wie bisher).
- `pruefe_alles.py --ohne-app`: ALLES GRÜN; GitHub „Prüfen" (mit App- und Oberflächentests) grün; Abnahmen 1f/1f-Nachtrag/1g/1d-Runde-3 je 0 Lücken; Prüfkatalog Demo unverändert (28/17/6/0).

## SaaS gegen die Playground-Testfälle (10.10.2026, Claude)
- Anlass: manueller Test im Mistral-Playground (mistral-large-latest) mit 10 Testnachrichten A1–A4 (Dialog) und B1–B6; dieselben Nachrichten jetzt durch das echte SaaS: `aufgaben/audit/playground_vergleich.py`, Ablauf „SaaS gegen Playground", Berichte `aufgaben/audit/playground_vergleich_{small,large}.md`.
- **Neuer kritischer Befund, behoben:** Die feste Rechtsform-Ergänzung (M1.3) nahm jedes Rechtsform-Wort im Text, auch für den Auftraggeber. „Wir sind eine GmbH und haben … einem Grafiker 2.000 Euro gezahlt" → Grafiker als GmbH → **„Nicht abgabepflichtig"**; „Unser Verein hatte vier Konzerte" → Musiker als Verein. Jetzt `rechtsform_erkennung.erkenne_rechtsform_auftragnehmer`: Treffer mit „wir/uns/unser/ich/mein" kurz davor im selben Satz zählen nicht; bleiben mehrere Rechtsformen, wird nicht geraten. Auch im Demo-Modus. Tests in `tests/app/test_dialog_fallgrenzen.py`.
- Live (Code `d7f25b2`, je 3 Läufe): kein sicheres falsches Ergebnis. small: alle Punkte 3/3 außer B2 (Modell legt „darin 300 € Fahrtkosten" 2× falsch als 1.500 € ab; Gesamtbetrags-Warnung würde es in der Bestätigung zeigen) und B5 (nach der eingeschleusten Anweisung zieht small weder Jahr noch Betrag; wirkungslos, aber unvollständig → Rückfrage). large: alle Punkte 3/3 außer B1 (1× Rechtsform aus „ein Fotograf" an der Position abgeleitet) und B2 (1× Extraktion fehlgeschlagen).
- Vereinfachte Playground-Anweisung des Nutzers (Felder jahr, anzahl_rechnungen, betrag_je_rechnung_eur, werbezweck) direkt gegen mistral-large-latest getestet (`aufgaben/audit/playground_prompt_test.py`, Berichte `playground_prompt_t07.md`/`_t0.md`, je 3 Läufe): A3 und A4 0/3 (Gesamtbetrag 500 € landet als „Betrag je Rechnung"), B4 0/3 (vier Konzerte werden zu vier Rechnungen à 1.250 € – erfundene Aufteilung und Rechnung), B6 3/3 nur, weil das Schema den widersprüchlichen Gesamtbetrag 900 € gar nicht abbilden kann (er verschwindet still). Ursache: Schema ohne Feld für den Gesamtbetrag und ohne Rechenverbot. Das SaaS-Schema (`gesamtbetrag_genannt`, `veranstaltungszahl`) und die Prüfungen lösen genau diese Fälle richtig (Bericht `playground_vergleich_*.md`).
- Texte korrigiert (10.10.2026, Claude, nach Livetest im Codespace): Umlaute in den Rückfragen („wofür", „einschlägige", „für die Veranstaltung(en)"), in Meldungen bei fehlendem Regelwerk und Gedankenstrich statt „--" in Begrüßung und Sitzungsmeldung. Die 16 Textbausteine der Excel waren bereits in Ordnung. Keine Tests betroffen, alles grün.
- Vorgemerkt (Nutzer: „erst korrigieren, nachher denken"): Der Chatbot soll menschlicher reden. Vorschlag in drei Schritten: (1) Absichten verstehen („warum?", „mehr Details", „das ist kein Fall") mit festen Erklär-Bausteinen je Rückfrage; (2) Gesprächsführung frei vom Modell formuliert, Inhalt fest, Prüfnetz und Gesprächstests; (3) Erklären mit Quellen (Teil 2, RAG). Livetest-Beobachtung dazu: „bitte mehr details" wiederholt nur die Rückfrage; die eingegebene Playground-Anweisung wird nicht als „kein Fall" erkannt.
- Livetest „2000 euro wird nicht übernommen" (10.10.2026, Claude) mit echtem Mistral nachgespielt (`aufgaben/audit/dialog_nachspielen.py`, Ablauf „Dialog nachspielen", Bericht `dialog_nachgespielt_*.md`). Ursachen: (1) Die erste Nachricht war eine Formatvorgabe („Antworte nur als JSON mit: jahr, anzahl_rechnungen, …"); sie ging im Verlauf bei jeder Extraktion mit, Mistral befolgte sie, fremde Schlüssel wurden still verworfen. (2) Mistral las „2000 euro" als jahr = 2000, die Sitzung überschrieb das per Knopf gewählte Jahr 2026. (3) small lieferte `"positionen": null` → Schemafehler → keine Sitzung. Behoben: Nutzertext als Daten gekennzeichnet; fremde Schlüssel → ein zweiter Versuch, sonst sauberer Fehler; Zahl mit €/EUR/Euro nie als Jahr (`zuordnung.jahr_nicht_aus_betrag`); null = nicht angegeben; Demo-Modus erkennt „Euro" als Betrag. Tests `tests/app/test_livetest_nachgespielt.py` (6). Nachgespielt danach: large übernimmt Jahr 2026, GmbH und 2.000 € und fragt nach der Art des Auftraggebers; small stuft die Formatvorgabe als „kein Fall" ein (Begrüßung/Hinweis) und fragt bei „2000 euro" nach dem Jahr.
- Livetest Teil 2 (10.10.2026, Claude, Protokoll des Nutzers aus dem Codespace): (1) „2000" ohne Einheit → Bestätigung ohne Betrag → „Nicht abgedeckt" (Ursache: Betragsfrage entfiel, sobald das Modell das freie Feld `unternehmensart` füllte); (2) „2" auf die Veranstaltungsfrage erst beim zweiten Mal übernommen; (3) „ander fall" nach dem Ergebnis → alter Verlauf erneut ans Modell, 2.000 € doppelt; (4) Widerspruchs-Warnung in der Bestätigung, trotzdem „Ja" möglich. Behoben: Betrag immer Pflicht (außer bei Veranstaltungszahl); reine Zahl wird der einzigen offenen Zahlenfrage fest zugeordnet (`router._zahl_als_antwort`, offene Fragen je Sitzung); Widerspruch → Rückfrage mit Knöpfen „Gesamtbetrag stimmt"/„Einzelbeträge stimmen"; Oberfläche schließt den Fall nach einem Ergebnis ab; weitere Ankündigungen neuer Fälle („ander fall", „andere frage" …). 6 neue Tests. Nachgespielt mit small und large (`aufgaben/audit/dialog_livetest2.json`): Jahr 2026, GmbH, 2.000 €, Generalklausel, Einnahmeabsicht, 2 Veranstaltungen → Faktenbestätigung; „ander fall" → neuer Fall, fragt nach dem Jahr.
- Rückfragen einzeln (MAX_FRAGEN = 1), nach Livetest-Hinweis des Nutzers: Zahl und ja/nein gleichzeitig verwirrte (10.10.2026).

## „Weiß ich nicht" bei der Zahl der Veranstaltungen (11.10.2026, Claude, Wunsch des Nutzers)
- Frage „Wie viele einschlägige Veranstaltungen …?" hat jetzt zusätzlich den Knopf „Weiß ich nicht"; getippte Antworten wie „weiß ich nicht", „keine Ahnung" werden fest erkannt (`app/unbekannt_begriffe.json`). Neues Fakten-Feld `veranstaltungszahl_unbekannt` (nur per Knopf/Begriffsliste, nie vom Modell).
- Der Kern rechnet dann beide Fälle (eine Veranstaltung / Grenze aus dem Regelregister + 1). Gleiches Ergebnis → dieses Ergebnis mit ehrlicher Begründung („Zahl unbekannt, Ergebnis in beiden Fällen gleich"). Verschiedenes Ergebnis → „Grenzfall → Steuerberater entscheidet" mit neuen Textbausteinen TB-17 (Gesetz: § 24 Abs. 2 Satz 3 Nr. 1 KSVG, Wegfall der Ausnahme fürs ganze Jahr, Abgabe für den Fall „mehr") und TB-18 (Empfehlung: vorsorglich einplanen, Aufzeichnungspflicht § 28, Schätzung § 27 Abs. 1 Satz 4). Regeln R-15, R-16, R-21, R-83, R-212.
- **Vom Steuerberater zu prüfen:** Wortlaut von TB-17/TB-18 (Status Entwurf); R-21 sieht bei unbekannter Historie „Rückfrage nötig" vor – hier bewusst „Grenzfall", weil der Nutzer die Angabe ausdrücklich nicht machen kann.
- **Nebenbei gefundener Fehler, behoben:** Im Veranstaltungs-Zweig ging die rohe Summe an den Kern; Zahlungen an eine GmbH/KG, USt, nachgewiesene Fahrtkosten zählten mit (GmbH, 4 Veranstaltungen, 2.000 € ergab „abgabepflichtig 98,00 €"). Jetzt bildet der Kern die Summe der Entgelte (`K.summe_positionen`); der ausgenommene Teil wird ausgewiesen (TB-12).
- Tests: `tests/app/test_weiss_nicht.py` (5), `tests/app/test_livetest_nachgespielt.py` ergänzt. Alles grün.

## Konzept Prüfweg und Speicherung (11.10.2026)
- `aufgaben/KONZEPT_Pruefweg_und_Speicherung.md` neu (nur Konzept, kein Code): je Rechnung nur bestätigte Fakten ohne Namen, Prüfweg als Daten, Ergebnis, Regelversion und Entscheidung des Steuerberaters (etwa 1–3 KB); Erklärung wird bei Bedarf neu erzeugt; Aufbewahrung mindestens 5 Jahre nach § 28 KSVG (prüfen). Bau erst, wenn der Chatbot stabil läuft. Offene Fragen: Frist, Datenschutz, Ansicht zuerst für Steuerberater oder Mandant, Speicherort EU.
- Auch im Projektplan (claude.ai-Projekt „ksk“) als Abschnitt 15 eingetragen.

## Testfall „Sammelrechnung mit 20 Positionen“ (11.10.2026)
- Katalog `aufgaben/audit/testfall_20_positionen.json`, Workflow „Testfall 20 Positionen“, Auswertung `aufgaben/audit/testfall20_auswertung.md`. `pruefkatalog_lauf.py` kann jetzt `--katalog` und `--details`; die Höchstzahl der Knöpfe steht in `MAX_KNOEPFE`.
- Ergebnis im SaaS: 13 von 21 richtig (alle künstlerischen Positionen und alle Zahlungen an Kapitalgesellschaften). Sammelrechnung 891,80 € statt Soll 433,65 €.
- **Schwerer Befund:** keine Tätigkeitsprüfung. Nicht künstlerische Leistungen an Einzelpersonen (Programmierung, SEO, DSGVO-Beratung …) werden als sicher „Abgabepflichtig“ ausgegeben. Vorschlag: Blatt „Tätigkeiten“ in der Excel mit Fundstellen; unbekannt → Rückfrage oder Grenzfall. Noch nicht gebaut, Entscheidung des Nutzers offen.

## Standardmodell mistral-large-latest (11.10.2026)
- Auf Wunsch des Nutzers ist das Standardmodell jetzt `mistral-large-latest` (`app/llm/mistral.py`, `app/README.md`, `aufgaben/audit/mistral_modell.txt`, Standard in `pruefkatalog_lauf.py`). Im Codespace gilt das ohne weitere Einstellung nach `git pull` und einem Neustart der App. Eine eigene Variable `MISTRAL_MODELL` hat weiterhin Vorrang. Der Workflow „Testfall 20 Positionen“ läuft nur noch mit large (im SaaS und roh).

## Tätigkeitsprüfung gebaut (11.10.2026)
- Neues Excel-Blatt „Tätigkeitsabgrenzung“ (35 Tätigkeiten: künstlerisch / nicht künstlerisch / Grenzfall, jeweils mit Regel-ID oder Fundstelle, alles Entwurf) und Textbausteine TB-19 bis TB-23.
- Ablauf: Das Modell wählt nur eine T-ID aus der Liste. Die feste Erkennung über die Begriffe der Excel prüft gegen; widersprechen sich beide, ist es ein Grenzfall. Nicht künstlerische Leistungen schließt der Kern aus. Bei unsicheren oder unbekannten Leistungen rechnet der Kern beide Fälle (ohne und mit); hängt das Ergebnis davon ab, ist es ein Grenzfall mit beiden Beträgen. Ist die Leistung gar nicht beschrieben, fragt das System danach.
- Demo-Modus Testfall 20 Positionen: vorher 13 richtig / 8 falsch, jetzt 18 richtig / 3 nachgefragt / 0 falsch. Ganze Rechnung: Grenzfall, „ohne die unsicheren Leistungen 433,65 €“ (= Soll), „mit ihnen 603,68 €“. Prüfkatalog Demo: P-32 von FALSCH auf NACHGEFRAGT, sonst unverändert.
- Angepasste alte Tests (nur Testdaten um eine Leistungsangabe ergänzt, Absicht unverändert); `test_leistungsart_ist_keine_pflichtangabe_mehr` ersetzt durch `test_leistung_ist_wieder_pflichtangabe` (begründet im Test).
- Workflows laufen nur noch mit mistral-large-latest (plus Demo und roh).
- Offen: R-117/R-42/R-175 (mehrere Positionen desselben Künstlers), Prüfung aller Zeilen durch den Steuerberater.
- Live mit mistral-large-latest (11.10.2026): Testfall 20 Positionen 18 richtig / 3 nachgefragt / 0 falsch / 0 Fehler. Sammelrechnung: Grenzfall, ohne die unsicheren Leistungen 433,65 € (= Soll). Prüfkatalog large: 30 richtig / 19 nachgefragt / 0 falsch / 2 Fehler (HTTP 429 im Parallellauf). Mistral roh: 7 bzw. 13 richtig, viele falsch.

## Prüfliste für den Steuerberater und „derselbe Künstler“ (11.10.2026)
- `regelwerk/Pruefliste_Taetigkeiten_Entwurf.xlsx` (erzeugt mit `python scripts/erzeuge_pruefliste_taetigkeiten.py`, bricht ab, sobald Eintragungen vorhanden sind): Blätter Anleitung, Tätigkeiten (35, mit Regeltext, Fundstelle, Quellenart, Regel „derselbe Künstler“), Textbausteine TB-17 bis TB-24, Testfall 20 (Soll gegen SaaS), Offene Fragen F-01 bis F-12.
- Mehrere Positionen desselben Künstlers: Nebenkosten und technische Teile zählen mit, wenn die Excel es so vorsieht (z. B. Programmierung beim Webdesigner, Gerätemiete: R-117, R-42, R-175), nachträglicher Druck nicht (R-49), eigenständige Leistungen wie SEO entscheidet der Steuerberater. Ob die Positionen vom selben Auftragnehmer stammen, fragt das System, wenn es darauf ankommt (Knöpfe ja/nein). Neuer Prüfkatalog-Fall P-52 (Soll 3.200 € → 156,80 €, abgeleitet, vom Steuerberater zu prüfen).
- Live-Lauf danach (mistral-large-latest) brachte einen ernsten Fehler: eine bloße Zahl in `positionen` war zu einer erfundenen Position über 1,00 € geworden, dadurch K-04 fälschlich abgabepflichtig. Ursache war meine Umdeutung „Zahl = Betrag“. Sie ist zurückgenommen; jetzt gibt es einen zweiten Versuch, danach eine feste Rückfrage. Außerdem setzte das Modell Sonderrollen ohne Grundlage (P-29 „ust“ für Material, P-39 „gewinnzuweisung“ für den Manager). Eine Sonderrolle gilt jetzt nur mit einem Beleg im Text (`app/rollen_belege.json`). Neu ist auch T-67 Material/Auslagen (beim selben Künstler zählt es mit, R-42/R-165/R-175).
- Ergebnis danach: Prüfkatalog large 34 richtig / 18 nachgefragt / **0 falsch / 0 Fehler** (bisher bester Stand). Testfall 20 large: 17 / 3 / 0 / 1 Fehler (S-15: das Modell lieferte zweimal eine bloße Zahl, deshalb die Rückfrage „bitte erneut stellen“; nicht falsch, aber lästig). Demo-Prüfkatalog: 29 / 22 / 1 (P-04a, bekannte Demo-Grenze).

## Verbindlicher Fallstand (Testprotokoll 11.10.2026)
- Bericht: `aufgaben/PRUEFBERICHT_Testprotokoll_1110.md`. Ursachen gemessen (Fallstand vor/nach jedem Schritt, rohe Modellantwort) und behoben: Das Modell bekommt den gespeicherten Fallstand und nur die neue Nachricht (`app/fallstand.py`). Neue Zustände „ausdrücklich unbekannt“ und „widersprüchlich“, Übersicht, Knopf „Noch unbekannt / später klären“. Rechnungsbeträge mit enthaltenen Teilen: den Rest rechnet der Kern (`kern.rechnen.restbetrag`).
- Live (mistral-large-latest): alle 9 Schritte des Protokolls wie gewünscht; Prüfkatalog 33 / 19 / 0 falsch / 0 Fehler; Testfall 20: 17 / 4 / 0 / 0.
- Offen: Fallstand dauerhaft speichern (PostgreSQL), Einnahmeabsicht unbekannt mit beiden Ausgängen, Nachfrage bei unklarer Fallabgrenzung.

## Vertagt: dauerhafte Speicherung des Fallstands (Entscheidung des Nutzers, 11.10.2026)
- Der Fallstand bleibt vorerst im Arbeitsspeicher (geht beim Neustart der App verloren). Das reicht für die Testphase mit erfundenen Daten.
- **Später**, spätestens vor dem ersten Pilot mit einer echten Kanzlei: Schritt 1 SQLite-Datei hinter derselben Schnittstelle (Versionen statt Überschreiben, Umschalten über `DATENBANK_URL`); Schritt 2 PostgreSQL bei einem EU-Anbieter mit Sicherung; dann Fallliste, Anmeldung, Löschfristen, Auftragsverarbeitung.
- Jetzt: Regeln optimieren.

## Alltagsfälle F1–F4 (11.10.2026)
- Testbelege des Nutzers (Werbefotografie, Journalist/Verlag, Agentur-Mischrechnung, Brautpaar) als Katalog `aufgaben/audit/testfall_alltag_4.json`; neuer Workflow „Testkatalog“ (beliebiger Katalog, Kurzname); Rückfragen werden gezählt.
- Vorher live: 0 richtig, F3 **falsch** (1.220,10 € statt 0 €), F4 Sackgasse. Nachher live: **F1, F2, F4 richtig ohne Rückfrage; F3 richtig mit einer Rückfrage** (Art des Auftraggebers, nicht aus dem Beleg ableitbar). Prüfkatalog 33 / 19 / 0 / 0, Testfall 20: 18 / 3 / 0 / 0.
- Neu: Auftraggeber „Privatperson“ (R-40/R-133, TB-25), Rechnungsteller als Zahlungsempfänger (R-45/R-216, Hinweis TB-26/R-219), T-68 Nutzungsrechte, T-69 Recherche, Jahr aus Rechnungsdaten (gekennzeichnet), Reisekosten-Rolle nur mit Nachweis, Pauschale aus dem Text, KSK-Auslegung nicht mehr als „Norm“. Bericht: `aufgaben/audit/alltag4_auswertung.md`.
- Offen: fehlende Bestätigung der Übungsleiterpauschale gilt als erteilt (Fund, Entscheidung offen); Rechenfehler der Testdatei; alle neuen Zeilen Entwurf.

## Testarchiv für Modellwechsel (11.10.2026, Wunsch des Nutzers)
- `tests/archiv/`: alle 77 Chatbot-Testfälle (Prüfkatalog 52, Testfall 20 Positionen 21, Alltagsfälle 4) mit Soll in `alle_faelle.json`, 2 Dialoge mit Soll je Schritt (`dialoge.json`), jede Fassung jedes Falls in `versionen.jsonl` (nur ergänzen), Ergebnisse aller bisherigen Läufe je Fall als CSV in `ergebnisse/` (small, medium, large, roh, Demo). Erklärung: `tests/archiv/README.md`.
- Werkzeuge: `python scripts/erzeuge_testarchiv.py` (Archiv aktualisieren, `--berichte` übernimmt Berichte als CSV), `python scripts/vergleiche_ergebnisse.py ALT.csv NEU.csv` (meldet „NICHT EINSETZBAR“ bei neuem FALSCH/FEHLER), `pruefkatalog_lauf.py --csv`. Workflow „Testkatalog“ mit Eingabe **modell** (Standard: ganzes Archiv mit mistral-large-latest). `pruefe_alles.py` prüft jetzt, dass das Archiv aktuell ist.
- Training: Prüffälle nie zum Training verwenden; für ein späteres Feintuning bräuchte es geprüfte „richtige Fakten“ je Frage (gibt es noch nicht) und eine getrennte Prüfmenge.
- Ausgangswert (ganzes Archiv, live, Stand `acd85a8`): SaaS mit mistral-large-latest 52 richtig / 25 nachgefragt / **0 falsch / 0 Fehler**; Modell allein 21 / 5 / 49 / 2; Demo 52 / 24 / 1 / 0 (P-04a, bekannte Demo-Grenze).

## Härtetest RE-2026-777 (11.10.2026)
- Testbeleg des Nutzers (Agentur-Rechnung über den Jahreswechsel mit Vertretung, Durchleitung, Direktzahlung, Gutschrift). Vorher: Sackgasse, und die Regel aus F3 war für die ganze Rechnung abgeschaltet (4.800 € „im eigenen Namen der GmbH“ wären mitgezählt worden). Nachher live: **Grenzfall** (0,00 € oder 343,98 €), Positionen im eigenen Namen an die GmbH, Vertretung/Durchleitung/Direktzahlung „Steuerberater entscheidet“ (KSK-Info 27, R-33/R-36/R-94/R-38/R-39, TB-27). Ganzes Testarchiv live danach 55 / 22 / 0 / 0 (vorher 52 / 25 / 0 / 0).
- Die Soll-Bewertung der Testdatei ist ein ungeprüfter Entwurf und widerspricht an zwei Stellen den Quellen (Pos. 02 und das Abgabejahr nach Leistungsdatum statt Zahlung); Pos. 04 ist offen. Deshalb **nicht** mit festem Betrag im Testarchiv; Entscheidung des Nutzers/Steuerberaters offen. Bericht: `aufgaben/audit/haertetest777_auswertung.md`.

## Tests direkt im Chatbot, ALLTAG-2026-999, Dialog „Der schwierige Kunde“ (11.–13.10.2026)
- **Chatbot direkt:** Das ganze Testarchiv läuft an der echten Weboberfläche. Ein Browser (Playwright) tippt, klickt Knöpfe und bestätigt (`aufgaben/audit/chatbot_direkt.py`, Workflow „Chatbot direkt“). Dialoge werden Schritt für Schritt gespielt; Ergebnisse als CSV in `tests/archiv/ergebnisse/`.
- **ALLTAG-2026-999:** vorher FALSCH (Grenzfall, Nr. 7, 1 Rückfrage), nachher richtig: BG 4.520 €, Abgabe 221,48 €, Nr. 3, keine Rückfrage. Fixes:
  - Durchleitung/Direktvertrag zählt beim Mandanten (KSK-Info 27/13, R-127, TB-28).
  - Provision offen mit zweitem Betrag (R-38/R-39, TB-29/30).
  - Nummer des § 24 Abs. 1 nach Art des Unternehmens (`app/verwerter_nummer.json`).
  - Messe als typischer Verwerter (R-126).
  - T-19 aus KSK-Info 06.
  - Gleiche Beträge je Position; USt behält ihren Grund.
  - Reisekosten-Rolle bei Nachweis direkt am Betrag; „Honorar“ aus dem Text; P-28-Rest.
  - Bericht: `aufgaben/audit/alltag999_auswertung.md`. Fall im Testarchiv (78 Fälle).
- **Dialog „Der schwierige Kunde“:** Nachfragen nach dem Ergebnis (Widerspruch, Vorgabe/Prompt-Injection, Zahlung offen, Protokoll) mit TB-31 bis TB-34, Ergebnis unverändert, ohne Modell. Fall fortsetzen bei bekannten Positionen. Modellfehler im Fall → Übersicht. Modell-Widerspruch nur mit Angabe im Text. Bericht: `aufgaben/audit/dialog_schwieriger_kunde_auswertung.md`. Der Dialog ist im Testarchiv (3 Dialoge).
- **Gesamtsuite direkt im Chatbot (live):** vorher 56 / 21 / 0 / 0 (77 Fälle), Endstand 59 / 19 / **0 falsch / 0 Fehler** (78 Fälle).
- **Offen:**
  - ~~Erster Satz ohne Rechnung (fragt nach dem Jahr).~~ Erledigt 13.10.2026: TB-35 bittet um die Rechnung (Schritt 1 erfüllt das Soll, live geprüft).
  - Upload von Foto/PDF.
  - Prüfprotokoll als PDF.
  - Zustand „Zahlung offen“ je Position.
  - Härtetest 777: Soll-Entscheidung des Steuerberaters.

## Quellenabruf (RAG), Teil 2 gebaut (13.10.2026)
- Auftrag `aufgaben/PROMPT_ClaudeCode_Chatbot_2_RAG.md` umgesetzt in `app/rag/` (Beschreibung: `app/rag/README.md`).
  - Index: 117 Quellen + Regelkatalog → rund 8.800 Stücke, SQLite FTS5 in `app/_lokal/rag.sqlite` (nicht im Repo), Aufbau etwa 1 Minute, danach nur Geändertes. Befehl `python -m app.rag.index`.
  - Zerlegung: Gesetz nach § und Absatz, Urteil nach Leitsatz/Randnummern, KSK/DRV nach Abschnitt und Seite; nie mitten im Satz.
  - Gültigkeit je Quelle in `app/rag/quellen_metadaten.csv` (vorbelegt, **vom Steuerberater zu prüfen**); Fassung je Jahr aus dem Register.
  - Abruf: Regelfilter (Regeln des Kerns + ihre Quelltext-Stellen), Stichwortsuche mit Jahresfilter, Mindestabdeckung, höchstens 8 Stücke nach Stufe; Embeddings nur mit `RAG_EMBEDDINGS=1`.
  - Chatbot: Recherchefragen antworten aus dem Abruf (Regeln + Gesetz/Urteil/KSK-Stellen, sonst „Nicht abgedeckt“); Bewertungen zeigen zusätzlich „Belegstellen im Quelltext“; Hinweis „Quelle geändert, Regel in Prüfung“.
  - Prüfung: Regel-IDs und Aktenzeichen in der Antwort müssen unter dem Gelieferten stehen. Festwerte-Wächter `tests/app/test_keine_festwerte.py` (läuft unter Python 3.11–3.13 gleich).
- Messwerte: Abruf-Güte **85,6 %** (Ziel 90 % nicht erreicht; `aufgaben/RAG_Bericht.md`), Gegenproben 6 von 10 richtig leer; Abgleich Register ↔ Quelle: 49 bestätigt, 1 Abweichung, 2 Fundstelle fehlt, 3 nur im Dokument (`aufgaben/RAG_Abgleich.md`).
- Unabhängige Prüfung des RAG-Codes (eigener Prüfer): 11 Befunde, 10 behoben (u. a. Neuaufbau in Nebendatei, Status „prüfen“ bleibt erhalten und nur bei geändertem Inhalt, Metadaten-Änderungen erkannt, keine Nutzerwörter in der Begründung, Aktenzeichen als Wortgruppe, Hinweise nur für Kern-Regeln, CSV aus Excel). Bewusst nicht geändert: eine neue Quelle braucht eine Metadatenzeile (Gültigkeit wird nicht geraten).
- Modellfehler P-16 („Antwort konnte nicht verarbeitet werden“) untersucht: Ursache ist ein Tippfehler des Modells im Schlüssel (`veranstaltungzahl`), nicht der Quellenabruf (Vergleich mit `RAG_AUS=1`). Behoben in `app/llm/mistral.py` (eindeutiger Ein-Zeichen-Tippfehler wird umbenannt).
- Tests: `tests/app/test_rag.py` (44), `tests/app/test_keine_festwerte.py` (3), `tests/app/test_tippfehler_schluessel.py` (6); lokal 528 Chatbot-Tests (nur die bekannten 6 Umgebungsfehler). GitHub „Prüfen“ grün (b8c5089).
- **Alle Testaufgaben direkt im Chatbot (live, mistral-large-latest, Stand c010403): 60 richtig / 18 nachgefragt / 0 falsch / 0 Fehler** (vorher a7b1bc6: 58 / 20 / 0 / 0); besser P-04a, P-04b; nichts schlechter. Demo-Modus unverändert (53 / 23 / 0 / 2).
- Neuer Workflow „Prüfen mit Protokoll“: legt die Ausgabe der Gesamtprüfung als `aufgaben/audit/pruefen_protokoll.txt` ab (die Actions-Protokolle sind aus der Arbeitsumgebung nicht lesbar).
- Embeddings gemessen (13.10.2026): in allen Varianten schlechter (79,9–84,6 % gegen 85,6 %), Schalter bleibt aus; Kosten des Versuchs geschätzt 30–40 Cent (zwei vollständige Einbettungen à rund 1,5 Mio. Token). Neuer Workflow „RAG Embeddings messen“ (mit Cache).
- Offen: Güte unter 90 %, Metadaten und neue Textbausteine vom Steuerberater prüfen lassen, Spalten Gültigkeit/Stufe in `quellen/index.csv` übernehmen (Fund), lexetius-Zeilen in `quellen/index.csv` verschoben (Fund).

## Abruf: Ursachen der Fehlschläge und einfache Korrekturen (14.10.2026)
- 43 Fehlschläge einzeln untersucht (Funde, Abschnitt „Ursachen der Abruf-Fehlschläge“). Korrekturen: Messung (mehrere Absätze), Rechtsform-Abkürzungen, Gesetz/Urteil vor KSK-Auslegung (Antworten mit Gesetzes-/Urteilsstelle 133 → 228 von 266), Bezugsfälle in der Messung. Abruf-Güte 86,6 % (vorher 85,6 %), Gegenproben 6/10.
- Live alle Testaufgaben (Stand 30f1cf8): 58 richtig / 20 nachgefragt / 0 falsch / 0 Fehler (vorher 60/18/0/0). Die Verschiebung (P-04a, P-04b, P-30 schlechter, P-32 besser) ist Modell-Schwankung bei der Rechnungserkennung: diese vier Fälle wechseln seit dem 11.10. zwischen richtig und nachgefragt, unabhängig vom Code-Stand (P-04a/P-04b 3 von 10 Läufen richtig, P-30/P-32 6 von 10). GitHub „Prüfen“ grün.
- Offen für den Steuerberater: 12 Regeln ohne Fassung, zulässige Fundstellen je Testfall. Danach Entscheidung über den Umbau „Thema erkennen → Regeln → gezielt suchen“.

## Schritt 1 des Plans: fremde Währung (14.10.2026)
- **Vorher live (71f75e9):** 5 von 10 Währungsfällen FALSCH – z. B. 2.000 US-Dollar als 2.000,00 € gerechnet (Abgabe 98,00 €), ebenso $, GBP und eine gemischte Rechnung EUR + USD.
- **Gebaut:** Beträge in fremder Währung werden erkannt (`app/waehrung_begriffe.json`, ohne Code erweiterbar) und **nie umgerechnet**. Steht im selben Satz genau ein Euro-Betrag („abgebucht wurden 1.850,00 €“), zählt er. Sonst fragt das System nach dem tatsächlich gezahlten Euro-Betrag, und der Kern rechnet nicht, solange er fehlt. Die Antwort darauf („1.850,00 €“ oder nur „1850“) wird übernommen; die Faktenbestätigung zeigt „1.850,00 € (gezahlter Euro-Betrag; angegeben 2.000 USD)“. Modell-Ausgaben wie `"1500 $"` werden zur Zahl, nur wenn genau so im Text.
- Testkatalog `aufgaben/audit/testfall_waehrung.json` (W-01 bis W-10, Soll nach L-23) ist im Testarchiv (jetzt 88 Fälle + 3 Dialoge). Tests `tests/app/test_waehrung.py` (15).
- **Live nachher:** 10/10 richtig in vier Läufen hintereinander (6414d11, 563ab52 mit Textprüfung, zweimal im Gesamtlauf). Ein Zwischenstand (68451a5) hatte 4 Fehler „Antwort konnte nicht verarbeitet werden“ (Modell schrieb die Währung ins Zahlenfeld) – behoben.
- **Dabei gefunden und behoben: P-20b** einmal FALSCH (Abgabe ohne Übungsleiterpauschale, 3.500 € statt 1.100 €; Modell setzte die Pauschale, aber nicht die Anfrageart). Der Text geht jetzt vor; die Faktenbestätigung zeigt die Pauschale (`tests/app/test_pauschale_aus_text.py`).
- **Alle Testaufgaben live (ed2b47f): 68 richtig / 20 nachgefragt / 0 falsch / 0 Fehler** von 88. Ohne die 10 neuen Fälle: 58 / 20 / 0 / 0 (wie 30f1cf8). Besser P-20b, P-30; schlechter P-28, P-32 (nachgefragt statt richtig, Modell-Schwankung bei Teilbeträgen, Schritt 2). Demo-Modus unverändert 53 / 23 / 0 / 2. GitHub „Prüfen“ grün (ed2b47f).
- **Für den Steuerberater offen:** Welcher Euro-Wert zählt bei Zahlung in fremder Währung (abgebuchter Betrag, Kurs am Rechnungs-/Zahlungstag, amtlicher Kurs)? Keine Quelle in der Quellenbasis. Bis dahin nur ein vom Nutzer genannter Euro-Betrag.
- Nächster Schritt: Schritt 2 (Teilbeträge stabil lesen: P-04a, P-04b, P-28, P-30, P-32).

## Schritt 2 des Plans: Teilbeträge stabil lesen (14.10.2026)
- **Neues Werkzeug:** Fakten-Protokoll (`FAKTEN_PROTOKOLL_PFAD`, nur Testläufe mit erfundenen Daten) im Workflow „Modellfehler suchen“: rohe Modellfakten und fertige Fakten je Lauf in `aufgaben/audit/modellfehler_fakten_*_<Lauf>.jsonl`. Damit wird die Ursache gemessen statt geraten.
- **Messung (je Fall 6 Live-Läufe):** vorher P-04a 1/6, P-04b 0/6, P-28 2/6, P-30 6/6, P-32 1/6 → nachher alle 6/6; zusätzlich W-03, P-39, P-52 je 6/6. Ursache war nie ein Betrag, sondern was das Modell als „Rechnung“ anlegt. Regeln in `app/zuordnung.py` (Einzelrechnungen je Position, Positionen aus Rechnungen, enthaltener Betrag nie der Rest, Rolle beim enthaltenen Betrag nur mit Beleg, gleichartige Positionen); Einzelheiten in `aufgaben/FUNDE_Chatbot.md`.
- **Alle echten Modellantworten der Messungen sind Offline-Tests** (`tests/app/daten_teilbetraege_live_1410.json`, `tests/app/test_teilbetraege_live.py`, 21 Tests). Sie haben einen eigenen Fehler sofort gefunden (eine P-39-Erweiterung hätte P-28 falsch gerechnet).
- **Dabei gefunden und behoben (alte Lücken, vom Modell ausgelöst, alter Code rechnete mit denselben Fakten ebenso falsch):** P-39 (2.500 € statt 2.000 €, „davon an den Manager“), P-52 (3.000 € statt 3.200 €, Beleg-Wort der nächsten Position), W-03 (Modell füllte Systemfelder der Währung).
- **Gesamtlauf am Ende (3b58f6a): 71 richtig / 17 nachgefragt / 0 falsch / 0 Fehler** von 88 (vor Schritt 2: 68 / 20 / 0 / 0). Besser P-04a, P-04b, P-28, P-32; P-31 einmal nachgefragt (neues Modellmuster, alter Code gleich). Demo-Modus ohne neuen falschen Fall. Zwei Zwischen-Gesamtläufe hatten je einen FALSCH-Fall (P-39, P-52) – beide behoben und je 6/6 nachgemessen. GitHub „Prüfen“ grün.
- **Für den Steuerberater:** „Werbegrafik“ als Begriff bei T-02 (Excel)? F1 „Nutzungsrechte“: soll bei einem Grenzfall-Eintrag der Excel dieser gelten statt eines Widerspruchs mit dem Modell?
- Workflows sichern ihre Ergebnisse jetzt robust (ein Ergebnis war beim gleichzeitigen Push verloren gegangen).
- Nächster Schritt: Schritt 3 (Prüfliste für den Steuerberater als Excel).

## Schritt 3 des Plans: Prüfliste 2 für den Steuerberater (14.10.2026)
- **Neu:** `regelwerk/Pruefliste_2_Steuerberater_Entwurf.xlsx`, erzeugt mit `python scripts/erzeuge_pruefliste_2.py` (alles aus den Daten gelesen; bricht ab, sobald der Steuerberater etwas eingetragen hat – neue Fassung dann unter neuem Namen). Die erste Prüfliste (Tätigkeiten, 11.10.2026) bleibt unverändert.
- Blätter: Anleitung (mit Übersicht „noch offen“ je Blatt), **Regeln ohne Fassung** (12, vom Skript mit derselben Auswertung wie der Quellenabruf gefunden), **Fundstellen je Testfall** (40 Fehlschläge der Abruf-Güte mit den stattdessen gelieferten Stellen – der Steuerberater legt zulässige Fundstellen fest), **Quellen Gültigkeit** (alle 122 Quellen: Jahre, Stufe), **Textbausteine neu** (TB-27 bis TB-35), **Offene Fachfragen** (12, aus `aufgaben/pruefliste_2_fragen.json`: u. a. fremde Währung, Umsatzsteuer „gesondert ausgewiesen“, Übungsleiter-Bestätigung, „Werbegrafik“, Grenzfall-Eintrag gegen Modell, Rundung).
- Nur die gelben Spalten sind auszufüllen (Auswahllisten). Geprüft: jede Zelle gegen die Quelldaten (0 Abweichungen), Formeln ohne Fehler, Test `tests/app/test_pruefliste_2.py` (3).
- Offen: die Antworten nach Rückgabe als neue Version übernehmen (eigener Schritt; dafür ein Einlese-Skript, das nichts überschreibt).
- Nächster Schritt: Schritt 4 (`aufgaben/RAG_Strategie.md`).

## Schritt 4 des Plans: Strategie Quellenabruf (14.10.2026)
- `aufgaben/RAG_Strategie.md`: bereinigte Fassung des Strategiepapiers des Nutzers, nur gemessene Zahlen, mit Anhang „Was aus dem Strategiepapier wurde“. Nicht übernommen: Drei-Prüfer-Konsens (nicht belegt, Sprachmodell trifft keine Rechtsurteile), Stammdaten im Python-Code (Regel 2; ungeprüfte Werte), „real ~90–92 %“ (gemessen 86,6 %). Lemmatisierung nur mit Messung (Schritt 5).
- **Befund:** Die in `CLAUDE.md` (Regel 3) verlangte unabhängige Gegenrechnung `verifier/` (Auftrag Teil 1e) ist **nicht gebaut** (laut Systembeschreibung „geplant“). Empfehlung: vor dem Einsatz bei echten Kunden bauen.
- `app/rag/README.md`: Güte auf 86,6 % aktualisiert, Verweis auf die Strategie.
- Nächster Schritt: Schritt 5 (Wortstämme testen und messen).

## Nachgefragte Fälle einzeln untersucht (14.10.2026)
- Alle 17 nachgefragten Fälle mit je 6 Live-Läufen und rohen Modellfakten gemessen: 16 waren in allen 16 Gesamtläufen nachgefragt (festes Verhalten). Auswertung: `aufgaben/audit/nachgefragt_auswertung.md`.
- Behoben: P-02 (Webdesign mit Programmierung, R-142/R-184), P-14 (Bandleader, R-31), P-20a (Übungsleiterpauschale mit Gesamtbetrag), P-40 (Privatfeier, R-40/R-133). Live je 6 Läufe: 6/6, 6/6, 5/6, 5/6 (Rest vorsichtig, nie falsch). Tests mit den echten Modellantworten: `tests/app/test_nachgefragt_live.py`.
- **Gesamtlauf 5dd83af: 76 richtig / 12 nachgefragt / 0 falsch / 0 Fehler** (vorher 71 / 17 / 0 / 0); nichts schlechter, Demo-Modus ohne neuen falschen Fall.
- Offen als eigene Schritte: Musikvereine (R-57 in den Kern; P-16, P-17) und Grundsatzfragen ohne Betrag (Vertretung R-33/R-78, Nachweismakler R-35; P-36, P-37). Bewusst vorsichtig: P-11, P-13, S-10, S-16, S-20, F3.
- Neue Fragen an den Steuerberater Q-13 (Musikverein 15 Schüler) und Q-14 („Künstler“ ohne Leistung) in `aufgaben/pruefliste_2_fragen.json`; die Excel-Prüfliste 2 wurde nicht neu erzeugt (schon an den Nutzer gegeben).

## Musikvereine, Grundsatzfragen ohne Betrag, Härtetest HT-2026-001 (14.10.2026, abends)
- Musikvereine: R-57 im Kern (vereinseigene Chorleiter/Dirigenten außer Betracht), Hobby-/Laienvereine als Generalklausel, „mit Eintritt“ als Einnahme; bei höchstens drei Veranstaltungen keine Frage nach der Einnahmeabsicht (KSVG § 24 Abs. 2 S. 3 Nr. 1). Live P-16, P-17 je 6/6.
- Grundsatzfragen ohne Betrag: Vertretung (R-33, `kern.vertreter`) und Nachweismakler (R-35, neue Kern-Funktion). P-36, P-37 richtig.
- Härtetest HT-2026-001 des Nutzers (eigener Katalog, nicht im Archiv): vorher 1 von 6 FALSCH (Durchleitung und Privatzahlung still mitgezählt), nachher 6/6 (Grenzfall, sicherer Teil 108,29 €). Auswertung `aufgaben/audit/haertetest_ht_2026_001_auswertung.md`.
- W-05 (Modell liest „1.500 $“ nicht aus) behoben: gezielte Frage nach dem Euro-Betrag.
- **Gesamtlauf b4de425: 80 richtig / 8 nachgefragt / 0 falsch / 0 Fehler** (heute früh 71 / 17 / 0 / 0). Die 8 sind bewusst vorsichtig oder warten auf den Steuerberater.
- Neue Fragen an den Steuerberater Q-15 bis Q-17 (Durchleitung aus Sicht der Agentur, private Zahlung mit offener Erstattung, Wortlaut des Textbausteins „beim Mandanten“).
- Workflow „Modellfehler suchen“ nimmt jetzt einen eigenen Katalog an.
- Nächster Schritt: unabhängige Gegenrechnung `verifier/` (Teil 1e).

## Härtetests HT-2026-002 bis 011, Fehlerquellen-Serie HT-062 bis 111, Auftrag „Testfälle in Kern, Regeln und Anker“ (14./15.10.2026)
- **Eingang des Nutzers:** zehn Härtetests mit Soll, eine KI-Fachprüfung der Soll-Werte, korrigierte Soll-Lösungen und ein neuer Arbeitsauftrag (PDF, Arbeitsfassung 2), der ältere Auftrag A–C, 50 Fehlerquellen-Fälle, 60 Alltagstests, ein Tätigkeitskatalog mit 200 Fällen. Wo sich älterer Auftrag und PDF widersprechen, gilt die PDF (strenger, passt zu den Grundregeln).
- **HT-002 bis 011** (eigener Katalog, Fassung 2 nach den korrigierten Soll-Lösungen, Status ENTWURF; **nicht** im Archiv: keine Berater-Freigabe). Live je 6 Läufe: **FALSCH 18 → 0**. Bericht: `aufgaben/audit/haertetests_ht_2026_002_011_auswertung.md`. Neu:
  - mehrere Zahlungsjahre und Rechtsformwechsel in einer Nachricht → Rückfrage (R-20);
  - offene Beträge zeigen ihren Grund (Gutschrift, unbezahlt, Durchleitung, Provision);
  - Selbstbeschreibung „wir sind ein Verlag (GmbH)“;
  - Injection ändert die Bewertung nicht.
  - Sachleistung und Student zählen (R-41, R-174, R-26), bewusst nicht „offen“.
- **Fehlerquellen-Serie** (`aufgaben/audit/fehlerquellen_ht_062_111.json`): 37 Einzelfälle, jedes Soll vor der Aufnahme gegen das Register geprüft; Abweichungen je Fall begründet. Beispiele:
  - HT-082/083: mehrere Jahre → Rückfrage;
  - HT-106: 1.000 € übersteigt 1.000 € nicht → N;
  - HT-062: R-39 → kein festes Soll.
  - 13 Dialog- und Oberflächenfälle gesondert (`nicht_als_einzelfall`, Dialogtests folgen).
  - Live: erst 4 FALSCH (HT-069 GmbH auf alle Positionen, HT-072 „Galerie“ im Vereinsnamen, HT-087 Pauschale als Zahlung, HT-099 GmbH des Auftraggebers), behoben → 0 FALSCH. **Ins Testarchiv aufgenommen: 88 → 125 Fälle.**
  - HT-062 bis 070 je 6 Läufe: 0 FALSCH in 54.
- **Gesamtlauf b87a9bb (125 Fälle):** 108 richtig / 12 nachgefragt / 3 Fehler / 2 falsch. Die beiden FALSCH sind behoben:
  - P-16: ältere Lücke; R-57 griff nicht, wenn das Modell „honorar“ setzt.
  - HT-074: Ausschluss „nicht künstlerisch“ allein vom Modell, ohne Beleg im Text; jetzt Grenzfall.
- **Gesamtlauf f6fae68 (125 Fälle): 113 richtig / 12 nachgefragt / 0 Fehler / 0 falsch** – Abnahme A1 erfüllt (0 FALSCH, 0 FEHLER). Gegen b87a9bb: 7 besser, 1 schlechter (HT-085 einmal Grenzfall: „an Künstler“ ohne Leistung, offene Frage P-09). Die 12 nachgefragten sind bewusst vorsichtig oder warten auf den Steuerberater. Hinweis zum Auftrag: 138 Fälle wären 88 + 50; 13 der 50 sind Dialog- oder Oberflächenfälle und kommen als Dialogtests.
- **Modell-JSON-Fehler** („Antwort konnte nicht verarbeitet werden“):
  - Diagnose im Lückenprotokoll (Wörter maskiert).
  - Zweiter Versuch mit strukturiertem Format (json_schema, strict).
  - Feldname mit Satzzeichen am Rand wird erkannt.
  - Ergebnis: deutlich weniger FEHLER; der Rest war vor allem 429 (zwei Läufe gleichzeitig).
- **Weitere feste Prüfungen:** Zahlungsjahr vor Rechnungsjahr (HT-085); Fahrtkosten mit Beleg im selben Satz (HT-088); ein Betrag direkt nach „Honorar“ wird nie Fahrtkosten (ältere Lücke); freie Jahreszahl als Jahr (HT-094).
- **Register (Auftrag B1) schon vollständig:** Abgabesätze 2015–2027 (2027: 5 %, Quelle BGBl. 2026 I Nr. 262), Verpflegung 2019 24/12 €, Übungsleiterpauschale 2026 3.300 €, Schätzung Ausland. Nichts ergänzt.
- **Fachfragen Q-18 bis Q-31** in `aufgaben/pruefliste_2_fragen.json`. Zuordnung: Auftrag Q-15…Q-22 → Q-18…Q-25, weil Q-15 bis Q-17 schon vergeben waren. **Prüfliste 2 nicht überschrieben**, stattdessen `regelwerk/Pruefliste_2_Nachtrag_1_Entwurf.xlsx` (Q-13 bis Q-31) mit `python scripts/erzeuge_pruefliste_2_nachtrag.py`.
- **Offen, in dieser Reihenfolge:**
  1. Dialogtests für die 13 Dialogfälle;
  2. 60 Alltagstests;
  3. Tätigkeitskatalog (200, erst Demo gegen das Excel-Blatt);
  4. Auftrag B2 (Regelentwürfe mit Status „fachlich zu klären“);
  5. C1–C3 (Begriffe, Anker nur mit Messung);
  6. mehrere Jahre in einer Antwort rechnen;
  7. Verifier.

## Tests weiter ausgebaut, alles für die spätere Prüfung gesichert (15.10.2026)
- **Dialogtests Fehlerquellen-Serie:** 11 Dialoge (`aufgaben/audit/dialoge_fehlerquellen/`) und 2 Programmtests (HT-096 in `tests/app/test_gegenproben_3.py`, HT-104 Knopf). Live im Gesamtlauf über `tests/archiv/dialoge_soll.json`, offline in `tests/app/test_dialoge_fehlerquellen.py` (Oberfläche nachgebildet). Funde behoben:
  - HT-098: „Sind wir abgabepflichtig?“ nach dem Ergebnis bezieht sich auf den letzten Fall.
  - HT-075: „Einnahmen waren beabsichtigt“ wird erkannt.
  - HT-102: „es waren nur drei Rechnungen“ übernimmt die kürzere Liste.
- **Alltags-Serie AT-001 bis 060** (`aufgaben/audit/alltag_at_001_060.json`): 55 Einzelfälle, 5 Dialoge (`aufgaben/audit/dialoge_alltag/`, `tests/app/test_dialoge_alltag.py`). Soll gegen Register und Tätigkeitsblatt geprüft. Abweichungen je Fall begründet:
  - AT-005/018: Werbetexte laut Blatt publizistisch;
  - AT-022: Rundung ungeklärt;
  - AT-055: Rechnungsteller GmbH → nicht abgabepflichtig (Entwurf: 147 €).
  - Funde behoben: AT-047 „Wo steht das?“; AT-048 Betragskorrektur; AT-036 verneinter Begriff („Plakatierung, keine Gestaltung“).
- **Tätigkeitskatalog (200)** (`aufgaben/audit/taetigkeitskatalog_200.json`, Bericht `aufgaben/audit/taetigkeitskatalog_auswertung.md`):
  - Blatt: 64 Treffer, 96 Lücken, 40 Abweichungen.
  - Vorher 5× still abgabepflichtig (Entwurf „nicht künstlerisch“), 9× still nicht abgabepflichtig (Entwurf „Grenzfall“).
  - Für den Steuerberater: `regelwerk/Pruefliste_Taetigkeiten_Nachtrag_1_Entwurf.xlsx`, `regelwerk/Pruefliste_2_Nachtrag_2_Entwurf.xlsx` (Q-32 bis Q-35).
- **Änderungsprotokoll Excel** (`regelwerk/Regelkatalog_24_KSVG_Entwurf.xlsx`, Blatt „Tätigkeitsabgrenzung“, 15.10.2026, Art: Ergänzung, keine alte Zeile geändert – geprüft Zelle für Zelle gegen die Fassung davor):

  | Zeile | Tätigkeit | Gruppe | Vorrang | Fundstelle |
  |---|---|---|---|---|
  | T-70 | Textkorrektur | nicht künstlerisch | 1 | R-194 |
  | T-71 | Unterricht/Coaching in Musik, darstellender, bildender Kunst | Grenzfall | 0 | KSVG § 2 S. 1, R-137 gegen R-183 |
  | T-72 | technische Zeichnung | Grenzfall | 1 | R-137 |
  | T-73 | Playlist/Musikauswahl | Grenzfall | 1 | R-137 |
  | T-74 | Fotogrammetrie/Vermessung | Grenzfall | 1 | R-137 |
  | T-75 | Sync-Agent | Grenzfall | 1 | R-219 |

  Status aller sechs: Entwurf – vom Steuerberater zu prüfen. Prüfergebnis: 659 Tests ohne neue Fehler, Regelwerkprüfung ohne formale Fehler, keine Archivfrage betroffen.
- **Änderungsprotokoll Excel, Nachtrag (15.10.2026):** T-76 Fotomodell, Model, Mannequin — Grenzfall, Vorrang 1, Fundstelle R-137. Anlass: Alltagstest AT-024 live (Modellhonorar still als darstellende Kunst gezählt). Ergänzung; keine alte Zeile geändert. Status: Entwurf.
- **Alltags-Serie im Testarchiv** (seit 5932744): 180 Fälle, 19 Dialoge.
- **Gesamtlauf 5932744 (180 Fälle, Mistral EU):** 159 RICHTIG, 20 NACHGEFRAGT, 1 FEHLER (AT-032, kaputtes Modell-JSON), **0 FALSCH**. Ergebnis: `tests/archiv/ergebnisse/2026-10-15_chatbot_direkt-browser-mistral-large-latest_5932744.csv`.
- **Sechs Fälle von RICHTIG auf NACHGEFRAGT untersucht** (P-28, P-32, W-03, HT-092, A-999, HT-084). Faktenlauf 38696351534 (je 3× mit/ohne Quellenabruf). Dieselben Modellantworten mit dem alten Code-Stand f6fae68 nachgespielt: gleiche Ergebnisse. **Keine Folge der Änderungen vom 15.10.2026, sondern Schwankung des Modells.**
  - Das Modell erfindet in etwa einem von drei Läufen einen Rechnungsbetrag (z. B. W-03: Rechnung 2.000 – die US-Dollar – bei 1.850 € abgebucht). Das System fragt dann nach. Das ist sicher, nicht falsch.
  - HT-084 war schon bei 225f380 „Nicht abgedeckt“.
  - Gesichert in `tests/app/test_gesamtlauf_5932744.py`: Aus keiner dieser Antworten entsteht ein Ergebnis gegen das Soll.
  - Bewusst nicht gebaut: den erfundenen Rechnungsbetrag still verwerfen. Das wäre geraten. Möglicher späterer Schritt mit Messung: eine Rechnung, die im Text nicht als Gesamtbetrag steht, nicht übernehmen.
- Übersicht für die spätere Prüfung: `aufgaben/VALIDIERUNG_Uebersicht.md`.

## Unabhängige Gegenrechnung gebaut (15.10.2026) – Teil 1e
- **Was:** Jede Rechnung des Kerns wird vor der Ausgabe in einem eigenen Python-Prozess unabhängig nachgerechnet.
  - `verifier/`: eigener Rechenweg, exakte Brüche, importiert `kern` nie.
  - `app/sandbox.py`: `python -I -B -S`, bereinigte Umgebung, Zeitlimit 5 s; Wächter sperrt Netz, Dateien, Prozesse und Nachladen.
  - `app/gegenrechnung.py`: Mitschnitt jedes Kern-Aufrufs, Vergleich von Klasse und jeder Zahl, Zahlen-Herkunft.
  - Ausgang: Stimmt alles, steht in der Antwort die Zeile „**Gegenrechnung:** … stimmt überein“ und das Prüfprotokoll (Feld `pruefprotokoll`). Weicht etwas ab: keine Antwort, „Prüfung fehlgeschlagen“, Eintrag im Lückenprotokoll.
- **Messung:**
  - 94 Testfälle, 5.000 Zufallsfälle, 2.000 Anfragen über den ganzen Ablauf, Höchstbeträge, 100.000 Positionen: 0 Abweichungen.
  - 24 Mutationen (16 im Kern, 8 in der Gegenrechnung): alle gefangen.
  - Dauer im Mittel 32 ms je Anfrage.
  - Nachweis: `aufgaben/SANDBOX_Nachweis.md` (Abschnitt Teil 1e); GitHub „Prüfen“ 38702893512 grün.
- **Befunde:**
  - Kern-Fehler behoben: Rechnungsposition ohne Rolle zählte still mit 0, jetzt Rückfrage.
  - Säumniszuschlag mit mehreren Rückständen bis 2022: Die Gegenrechnung folgt dem Soll L-10/L-11 (Grenzfall).
  - Registerprüfung: 0 Fehler, 5 Hinweise (Pauschalen nur bis 2026).
- **Tests angepasst** (mit Begründung im Test):
  - `tests/app/test_rag.py`: Die im Speicher nachgebildete Excel-Änderung bekommt auch die Gegenrechnung.
  - `tests/app/test_eigenschaften.py`: Die Gegenrechnung läuft im selben Prozess, damit die 60-Sekunden-Grenze bleibt.
  - Kein Soll geändert.
- **Neue Befehle:**
  - `python -m verifier.pruefe_register`: Registerprüfung vor einer Freigabe.
  - `python scripts/messe_gegenrechnung.py`: Zeitmessung.
- **Offen:**
  - Zeitmessung für alle Schritte.
  - Windows-Speichergrenze.
  - Satz „Positionen ergeben …, Beleg nennt …“ in der Antwort.
  - Container ohne Netz beim Hosting.
- **Nächste Schritte:**
  - Auftrag B2/C: Regelentwürfe, Begriffe, Suchanker nur mit Messung.
  - Mehrere Zahlungsjahre in einer Antwort rechnen.
  - Lemmatisierung (Schritt 5).

## Korpus mit 1.822 Beispielen und Gegenbeispielen, jedes Sprachmodell, RAG getestet (15.10.2026, abends)
Auftrag des Nutzers: alle Fehler beheben, unabhängig vom Sprachmodell (vielleicht ChatGPT, lokales DeepSeek oder Anthropic), über 1.000 Beispiele und Gegenbeispiele, alles protokollieren, direkt im Chat testen, auch das RAG. Einzelheiten und Befunde: `aufgaben/FUNDE_Chatbot.md`, Abschnitt „Korpus …“. Protokoll aller Läufe: `aufgaben/audit/TESTPROTOKOLL.md`.
- **Was neu ist:**
  - Korpus `aufgaben/audit/korpus_beispiele.json`: 1.822 Fälle (911 Paare Beispiel/Gegenbeispiel, 19 Familien). Soll ist Entwurf, nicht vom Steuerberater geprüft → nicht im Testarchiv.
  - Offline-Lauf ohne Modell: `python aufgaben/audit/korpus/lauf_offline.py --stufe orakel` (fehlerfreie Fakten), `--stufe gestoert` (18 typische Modellfehler je Fall), `--stufe demo`.
  - RAG-Korpus: `python aufgaben/audit/korpus/rag_korpus.py` (327 Fragen).
  - Sprachmodell wählbar über Umgebungsvariablen (`app/README.md`, Abschnitt „Sprachmodell wechseln“): Mistral, OpenAI-kompatibel (ChatGPT, DeepSeek lokal über Ollama/vLLM), Anthropic. Außerhalb der EU nur mit `LLM_AUSSERHALB_EU_ERLAUBT=1`.
  - „Chatbot direkt“ kann Stichproben (`jeder`) und Teile (`teil`) spielen.
- **Ergebnisse:**
  - Orakel: 1.822 von 1.822 richtig.
  - Gestörte Fakten (Stichprobe jeder 5. Fall, 3.618 Läufe): FALSCH 428 → 0 (protokolliert, 56a909e); Rest richtig oder Rückfrage.
  - Demo-Modus (ohne Schlüssel, alle 1.822): 0 FALSCH (vorher 38), 310 Rückfragen.
  - RAG-Korpus: 271 → 307 von 327 richtig; Abruf-Güte unverändert 86,6 %; Gegenproben 6 → 9 von 10.
  - App-Tests: alle grün bis auf die 6 bekannten Umgebungsfehler (fastapi/httpx fehlen in dieser Umgebung).
  - **Live im Chat** (Browser, jeder 10. Korpusfall, 183 Fälle): Mistral 173 richtig / 0 falsch; allgemeiner Anschluss (wie für ChatGPT/DeepSeek) gegen Mistral: 170 → nach Korrektur 172 richtig / 0 falsch. Behoben dabei: strenges JSON-Schema im allgemeinen Anschluss, Telefonnummer ist keine Leistung, negatives Honorar im Korpus (Version 2).
  - **Ganzer Korpus live im Chat** (1.822 Fälle, Mistral, Browser, 16.10.2026): 1.740 richtig, 71 Rückfrage/Grenzfall, **0 falsch**, 11 nicht lesbare Modellantworten (System fragte nach). Danach behoben: „brutto, darin Umsatzsteuer“ (Rechnungsbetrag aus dem Text), „Unsere Agentur für …“ ist keine Leistung, Auskunft für ein Jahr ohne Registereintrag → „Nicht abgedeckt“ statt Rückfrage.
- **Offene Frage an den Steuerberater:** Fahrtkostenpauschale ohne Nachweis an denselben Künstler – Entgelt (abgabepflichtig) oder wie bisher Grenzfall (Tätigkeitskatalog T-67 „unsicher“)? Entscheidung in die Excel.
- **Nicht geprüft:** ChatGPT, DeepSeek und Claude live (kein Schlüssel); nur der allgemeine Anschluss gegen die Mistral-Schnittstelle.
- **Nächste Schritte:** Live-Stichproben im Chat (Mistral und allgemeiner Anschluss), Befunde beheben; Soll des Korpus vom Steuerberater prüfen lassen.

## RAG auf 90 %, seltene Modellfehler, Windows-Start (16.10.2026)
- **Quellenabruf (RAG):** Abruf-Güte 259 → **270 von 299 = 90,3 %** (Ziel erreicht; gemessen an denselben Testfällen, an denen eingestellt wurde). RAG-Korpus 310 von 327, Gegenproben 9 von 10. Dabei behoben: Regeln mit „Gilt für Fassung“ = „alle“/„Jahresabhängig“/„… nicht nur gelegentlich …“ wurden nie geliefert (R-20, R-21, R-89, R-115). Einzelheiten `aufgaben/FUNDE_Chatbot.md`.
- **Offene Frage an den Steuerberater:** R-18, R-19, R-27, R-36 stehen auf Fassung „aktuell“ und werden deshalb nie geliefert – soll dort „A und B“ stehen?
- **„Antwort nicht lesbar“:** Ursache gefunden (Schlüssel mit Hochkomma und Wert), behoben für jedes Modell.
- **Windows:** Doppelklick auf `scripts\start_windows.bat` startet den Chat (Umgebung, Pakete, Quellenindex, Browser).

## Umbau Schritt 1: Fakten statt einer Kategorie (16.10.2026)
- Der Chat speichert jetzt getrennt: **Tätigkeit des Unternehmens**, **Zweck dieses Auftrags** und ob die Tätigkeit zu den typischen Verwertern gehört – jeweils mit Herkunft (Zitat aus der Nachricht, Knopf, Modell oder System). Die alte „Art des Auftraggebers“ wird nur noch daraus abgeleitet.
- Widerspricht ein Knopf dem Text, fragt der Chat gezielt nach („Sie hatten geschrieben … Welche Angabe stimmt?“) statt still zu überschreiben.
- Die Bestätigung zeigt die Belege und die Annahme zur Umsatzsteuer; Auskünfte heißen „aus dem Register gelesen“, nicht „nachgerechnet“.
- Tests: 17 Abnahmetests (Bäckerei, Verlag, Agentur, privat – auch widersprüchlich/unvollständig). Korpus offline unverändert 0 falsch.
- **Offen für den Steuerberater:** vollständige Zuordnungsregeln mit Voraussetzungen und Ausnahmen (Entwurf in der Excel folgt in Schritt 2).
- **Nächste Schritte:** Live-Test im Chat; Schritt 2 (Rückfragen in Alltagssprache, Bestätigung als Satz).
- **F04 behoben:** Rückfrage „Teilbetrag so hoch wie die ganze Rechnung“ bei „… brutto, darin … Umsatzsteuer“ (Modell legte den ganzen Betrag als Steuer an); „Werbung für mein eigenes Unternehmen“ / „für unser eigenes Haus“ wird als Eigenwerbung erkannt. Offline unverändert 0 falsch (Orakel 1.822/1.822, Demo 1.594/228/0, gestört 3.445/173/0, RAG-Korpus 310/327).
- **Blockiert:** Mistral antwortet seit 16.10.2026 vormittags „402 Payment Required“ (Konto-Guthaben aufgebraucht). Live-Tests und der Chat mit Mistral gehen erst wieder nach Aufladen unter console.mistral.ai. Vor der Sperre: 107 Live-Fälle mit Schritt 1, 0 falsch.

## Für später notiert (16.10.2026, Gespräch mit dem Nutzer)
- **Haftung:** Grundsatz des Nutzers: die Software macht Vorschläge, der Steuerberater prüft, entscheidet und haftet. Später: AGB-Klausel (Haftungsbegrenzung, nur für Berufsträger; vom Anwalt für IT-Recht), einmalige Bestätigung beim ersten Anmelden im Chat.
- **SaaS-Grundlagen** (später): Verträge zur Auftragsverarbeitung (DSGVO), Berufsrecht (§ 62a StBerG, § 203 StGB) vom Anwalt prüfen lassen, Versicherung, Penetrationstest, Freigabe des Regelwerks durch einen Steuerberater.
- **Kosten Sprachmodell:** Mistral Small 4 mit dem Korpus gegen Large messen; Zwischenspeicher (Caching) für die feste Anleitung prüfen; Ausgabenlimit bei Mistral setzen. Mistral-Ticket #38339352 (Pay-as-you-go-Aktivierung) offen.
- **Eigener Server (DeepSeek, Frankfurt):** Workflow „Chatbot direkt“ kann ihn mit `anbieter=eigener-server` testen (Secrets `LLM_BASIS_URL`, `LLM_API_KEY`).

## Nur noch Mistral, Small als Standard (17.10.2026)
- **Entscheidung des Nutzers:** nur Mistral, Standardmodell Mistral Small (billig, schnell). Andere Anbieter entfernt; Demo-Modus bleibt (kein Sprachmodell, für Tests und Notbetrieb).
- **Messung:** Korpus jeder 10. Fall: Small 166/11/0 falsch (9 Min.), Large 168/9/0 falsch (27 Min.). Testfall 20 Positionen: Small 0 falsch, aber viele Rückfragen (behoben: „unbekannt“ nur mit Beleg, Rechtsform-Erkennung). Testarchiv mit Small: **5 falsch** – Ursachen behoben.
- **Stand der Einstellung:** Entscheidung des Nutzers: Small ist Standard, Large entfernt (`app/llm/anbieter.json`). Prüfstand bei der Entscheidung: Testarchiv 5 falsch, Korpus 30 falsch (Ursachen behoben, offline 0 falsch); Bestätigung live läuft.
- **Offen:** Mengenbegrenzung des Mistral-Kontos (Large: HTTP 429 im Vergleichslauf) – für viele Nutzer höhere Grenzen bei Mistral anfragen.

## Dokumentenprüfung ohne Sprachmodell (16.10.2026, Codex)
- Auftrag: Dokumente hochladen (PDF, Foto, Excel), Angaben prüfen, Abgabe je Position beurteilen; zunächst ohne Chat/LLM, mit vielen erfundenen Belegen testen.
- Neuer eigenständiger Einstieg `app.dokument_app:app`, Oberfläche `app/static/dokumente.html`. Codespace-/Windows-Startskripte öffnen diesen Modus. Der bestehende Chat bleibt unter `app.main:app` erhalten.
- Lokales Lesen mit pypdf, openpyxl/CSV und Tesseract/Poppler für Fotos/Scans. Originaldateien nur im temporären Arbeitsordner, danach gelöscht; keine Kundendaten im Repo/Quellenindex/Protokoll. Technische Grenzen in `app/dokument_config.json`.
- Automatische Positionen sind nur Kandidaten: Originaltext und Belegstelle sichtbar, Bearbeiten/Ergänzen/Entfernen möglich. Formeln werden nicht ausgeführt, Fremdwährungen nicht umgerechnet, Summenzeilen nicht als Entgelt übernommen. Keine Vollständigkeitszusage für beliebige Layouts.
- Getrennte Fakten: Auftraggeber-Tätigkeit, Zweck, Zahlungsjahr, Katalogtätigkeit mit Voraussetzungen aus der Excel; je Position Rechtsform, Auftragnehmer-Nummer und Zahlungsweg. Vollständige Jahresdaten sind vor Eigenwerbungs-/Generalklauselprüfung nötig. Keine stille Jahresbefreiung aus einer einzelnen Rechnung.
- Bestätigung zeigt jede Position sowie die Tätigkeitszuordnung und deren Abgrenzungen. Zeitlich begrenztes HMAC-Ticket bindet die Rechnung an exakt bestätigte Fakten. Änderungen verwerfen Bestätigung/Ergebnis.
- Bestehender Regelkern und unabhängige Gegenrechnung wiederverwendet. Keine Änderung an `kern/`, `verifier/`, Regel-Excel oder Quellen. Ergebnisse und Fundstellen kommen aus dem System; KSK-Auslegung gekennzeichnet. Unbekannte Leistungen/Vertragswege bleiben offen; keine eigene Rundung.
- **Ausgangsstand:** GitHub-Prüfung 38913032829 für Commit d6daab5 vollständig grün, einschließlich Browser-Prüfung. Lokale Kopie anhand Git-Blob-SHAs und Quellenprüfsummen geprüft.
- **Abschluss lokal:** `python scripts/pruefe_alles.py`: **ALLES GRÜN**, 784 App-Tests (1 übersprungen), 33 Kern-Tests, 31 Verifier-Tests; 94 ausführbare Kern-Testfälle bestanden, 235 weitere Testfälle weiterhin nur als Text. Kein Soll des bisherigen Regelwerks geändert.
- **Neue Tests:** 18 Tests in `tests/app/test_dokumente.py`, darunter 180 erzeugte PDF-/XLSX-/CSV-Belege durch Upload/Bestätigung/Kern/Gegenrechnung, echte Foto- und Scan-PDF-OCR, Grenz-/Mischfälle und fehlerhafte/manipulierte Angaben. `python tests/app/livetest_dokumente.py`: **60/60** über echten HTTP-Server richtig, Modellauswahl absichtlich ungültig gesetzt (Beweis: neuer Modus benötigt sie nicht).
- **Umgebungsbefunde:** Hier fehlte zunächst socksio für den vorhandenen Proxy; lokal ergänzt, keine Änderung der Produktionsanforderungen dafür. Poppler benötigte den lokalen Bibliothekspfad `LD_LIBRARY_PATH`; danach Scan-Test und vollständige Suite grün. Chromium startet in dieser Arbeitsumgebung nicht; der neue Browser-Test wird deshalb zusätzlich im GitHub-Workflow ausgeführt und dessen Ergebnis am Pull Request geprüft.
- Anleitung/Limitierungen: `app/DOKUMENTE.md`. Weiterhin Entwicklungsprototyp, nur erfundene Daten: keine Anmeldung/Mandantenverwaltung/dauerhafte Fallakte, keine Lastzusage und keine fachliche Freigabe. OCR benötigt Systemprogramme; Codespace-Konfiguration installiert sie beim Neuaufbau. Alle fachlichen Ergebnisse bleiben Entwurf.
- **Browser-Nachtest (GitHub 38969424670):** Der bisherige Chat-Browsertest und die drei fachlichen Abnahmen sind grün. Der neue Test verwendete `wait_for_function`, dessen internes `eval` an der CSP scheiterte. Test auf Locator-Prüfungen und Elementabmessungen umgestellt; `unsafe-eval` bleibt verboten. Keine Änderung an Fachlogik oder Seitenschutz. Erneuter vollständiger Prüflauf vor dem Nachtrag.

## Rechnungen prüfen – zweiter Bereich der Oberfläche (17.10.2026)
- **Wunsch des Nutzers:** Viele Nutzer wollen nicht chatten, sondern Rechnungen hochladen und prüfen. Oberfläche nach seiner Skizze: Menü links **„KSK-Chat“** und **„Rechnungen prüfen“**, eine gemeinsame App.
- **Grundlage:** Pull Request #1 (Dokumentenmodus von ChatGPT/Codex) übernommen und angepasst: PDF, Foto, Scan, Excel, CSV werden auf dem eigenen Server gelesen (Texterkennung Tesseract), Formular mit Belegstellen, Bestätigung, derselbe Kern und dieselbe Gegenrechnung wie im Chat.
- **Neu dazu:** KI-Unterstützung beim Lesen (Mistral Small ordnet nur den gelesenen Text, nie die Datei; jeder Betrag mit dem Dokument abgeglichen; grün = KI und Regeln einig, gelb = nur KI; abschaltbar); Jahresübersicht über mehrere Rechnungen mit Belegstelle je Position und CSV für den Steuerberater.
- **Geprüft:** GitHub-Prüfung grün einschließlich Browser-Tests (Menü, Upload, Bestätigung, Jahresübersicht, CSV, zwei Rechnungen in einem Jahresfall, Mobilansicht). Live mit KI: erster Lauf 2 von 4 – drei Systemfehler gefunden und behoben; zweiter Lauf 4 von 4.
- **Im Codespace:** `git pull`; für Fotos/Scans den Codespace einmal neu aufbauen (Tesseract wird dabei installiert).

## Korpus mit Small: 0 falsch (17.10.2026)
- Ganzer Korpus (1.822 Fälle) live mit `mistral-small-latest`: 1. Lauf 30 falsch, 2. Lauf 11, **3. Lauf 0 falsch** (1.692 richtig, 85 Rückfrage, 45 nicht auswertbar: ungültiges JSON vom Modell oder Zeitüberschreitung, das System fragte dann nach). Letzte Ursache: Small rechnete bei „brutto, darin Umsatzsteuer“ den Nettobetrag selbst aus, der Kern rechnete ihn auch – doppelt gezählt (`app/zuordnung.py::modellgerechneter_rest`).

## Schritt 2: Rückfragen nach Tatsachen, Bestätigung in Sätzen (17.10.2026)
- **Auftrag** (vom Nutzer, Text von ChatGPT/Codex; Codex prüft danach unabhängig): keine Rechtskategorie mehr wählen lassen, verständliche Faktenbestätigung, erst „Ja, das stimmt“ erlaubt die Berechnung.
- **Umgesetzt (792fb2c, 5b3b79c):** Rückfrage „Wofür war dieser Auftrag gedacht?“ mit Knöpfen in Alltagssprache (eigene Werbung / Werbung oder Öffentlichkeitsarbeit für Kunden / Veranstaltung mit Künstlern / privater Auftrag / noch unbekannt), freier Text möglich; Einordnung leitet das System ab, Tätigkeit des Auftraggebers bleibt (Verlag bleibt Verlag). Knopf und abgetippter Knopftext ohne Modellaufruf; Widerspruch Text/Auswahl → gezielte Frage; Modell kann die Auswahl nicht ändern; „noch unbekannt“ blockiert die Berechnung, spätere Angabe ergänzt. `POST /knopf` lehnt Systemfelder und ungültige Positionen ab (Rückfrage statt Serverfehler). Bestätigung: Sätze des Systems vor der Liste, Einordnung als „Vorschlag des Systems, keine Angabe von Ihnen“. Genaue Modellkennung aus der Mistral-Antwort in Oberfläche, `/gesundheit`, Testberichten. Details `app/README.md` („Rückfragen nach Tatsachen“).
- **Tests:** 22 neue (`tests/app/test_schritt2_rueckfragen.py`), ungültige Eingaben an `/knopf` (`test_main.py`), Browser-Dialog Frage → Rückfrage → Knopf → Bestätigung → Ergebnis (`playwright_oberflaeche.py`); 7 bestehende Tests nur an die neue Beschriftung angepasst (Ergebnis gleich). GitHub „Prüfen“ grün (alle Jobs). Offline-Korpus unverändert 0 falsch.
- **Live (Testarchiv, Small):** 1. Lauf 7 falsch. Gegenlauf auf dem alten Stand (2eaeb5d) 3 falsch; Nachbau der vom Modell gelieferten Angaben zeigte: alter und neuer Code entscheiden gleich – Small liest dieselben Texte von Lauf zu Lauf verschieden (auch bei Temperatur 0). Zwei solcher Lesarten jetzt fest abgefangen („fünfmal … jede Rechnung 250 €“, „1.500 EUR … an die GEMA“). 2. Lauf: **3 falsch** (A-999 Messe, AT-2026-004 Firmenfeier, AT-2026-007 „Agentur (GmbH)“) – Deutungsfälle, in denen Small den Zweck selbst rät.
- **Offen (Entscheidung nötig):** Soll ein Zweck, den nur das Modell vermutet (kein passendes Wort im Text), immer per Rückfrage bestätigt werden? Weniger falsch, mehr Rückfragen. Zum Upload-Vorschlag von ChatGPT fehlen noch: zweite Erkennung am Originalbild, Prüfung Positionen + Umsatzsteuer = Gesamt, Rechnungs- und Zahlungsdatum getrennt, Original und Angaben nebeneinander. Mistral-Dokumenterkennung würde die Datei an Mistral schicken (bisher: nur Text) – Entscheidung des Nutzers.

## Extraktion vor dem Kern (18.10.2026)
- Neues Paket `extraktion/`: `extrahiere_dokument` mit `rule` und `mistral`. Das Sprachmodell füllt Felder, der Kern entscheidet. App, Gegenrechnung und Schnellcheck bleiben ohne Sprachmodell.
- Mistral ist zweistufig und gepinnt: OCR `mistral-ocr-4-1`, dann `mistral-small-latest`. Drei Ablesungen, keine Mittelung. Block unter 0,85 Konfidenz fällt weg. Medium nur, wenn Small kein gültiges JSON liefert. Schlüssel nur aus `MISTRAL_API_KEY` oder `config/secrets.env`.
- Zwei Kernregeln, Sätze nur im Register: `ust.satz` 7 und 19 (UStG § 12). Passt die ausgewiesene Umsatzsteuer zu keinem Satz und die Summe zu keinem einheitlichen Satz, sperrt `sperre.ust_mischsatz` (§ 25 Abs. 1 KSVG, Rechenprobe). Eine öffentliche Stelle als Verwerter (`offen.oeffentliche_stelle`, KSK-Info 11 und Info 16) ist eine Rückfrage, bevor eine Kapitalgesellschaft ausgeschlossen wird.
- Regel-Leser auf der Suite 130, ohne die hinterlegten Strukturfelder: **93/130** (vorher 91/130). V-034 und V-116 sind damit grün. Bericht `tests/ergebnis_extraktion_vergleich.txt`, je Abweichung das konkrete Feld.
- Schlüssel: erst die Umgebungsvariable, nur wenn sie fehlt `config/secrets.env`. Die Datei überschreibt die Variable nicht und wird nicht in die Umgebung kopiert. Wert nie loggen, nie drucken, nie committen. Ablauf „Extraktion“ (von Hand) reicht das Actions-Secret an Modellliste und Suite 130 durch. Der Ablauf „Prüfen“ bleibt ohne Schlüssel.
- Verbindungstest lokal: Quelle Datei, Länge 45, Umgebung Länge 0, kein BOM, kein Leerzeichen. HTTP 401, der geladene Wert gilt bei der API nicht. Die Suite 130 über Mistral bleibt deshalb ohne Teilquote. Kostenlog 0 Aufrufe.
- Suite-100 100/100, Erfahrungs-Suite 120/120, Adversarial mit hinterlegter Struktur bleibt 95/130. Kern-Tests 45.

## Adversarial-Etappe 1 (18.10.2026)
- Strukturierte Dokumentfelder in der Adversarial-Suite. `kern/rechnen.py` prüft sie vor Szenario und Tätigkeit: Summenprobe, doppelte Positionsnummer, § 19, negative Summe, Cent-Toleranz. Eine fehlerhafte Zeile sperrt das Dokument.
- Neue Registerzeile `sperre.rechtsform` (Rechenprobe A2/A3): zwei Rechtsformen werden nicht still gewählt.
- K1 20/20, K3 15/15. Suite-100 100/100, Erfahrungs-Suite 120/120. Kern-Tests 43. Gesamt der Adversarial-Suite 95/130. Die übrigen ❌ stehen mit Quelle und Korrektur in `tests/ergebnis_adversarial_130.txt`.

## Adversarial-Suite (18.10.2026)
- `tests/testsuite_adversarial_130.json` und Lauf in `tests/lauf_testsuite_100.py`. Ergebnis: `tests/ergebnis_adversarial_130.txt`.
- 77/130. K1 12/20, K3 8/15, beide unter 100 %. K5 2/13. Suite-100 bleibt 100/100, Erfahrungs-Suite 120/120.
- Abnahme nicht bestanden. Die Abweichungen stehen im Ergebnisfile.

## Korpus ohne Sprachmodell (18.10.2026)
- `scripts/lauf_offline.py` ersetzt den gelöschten Chat-Lauf. 1.822 Fälle, perfekte Fakten, heutiger Kern: **1.782 richtig, 40 nachgefragt, 0 falsch**.
- Die 40 sind Fahrtkosten ohne Beleg (F09): Grenzfall, das Soll erlaubt abgabepflichtig oder Rückfrage. Keine falsche Abgabe.
- Bericht: `aufgaben/audit/alltag999_auswertung.md`.

## Zahlenquellen und Eigenwerbung (18.10.2026)
- `rules/saetze.json`: Jahre 2015–2026 aus `kern/parameter.json`. 2015–2018 ohne Schwelle. 2019–2022 sind 450 Euro Geringfügigkeit (Fassung A), 2023–2024 Fassung B. 2027 bleibt in dieser Datei leer (sichtbarer Konfigurationsfehler, Rücktest). Der Satz steht im Regelregister.
- `daten/zahlen-werte.json`: Ehrenamt auf KSK-Info 24/24a. 450-Euro-Grenze in Fassung A (bis 2022) und Fassung B (2023–2024) geteilt. Abgabesätze 2015–2027 jahrweise; 4,9 Prozent endet 2026.
- „eigenwerbung“ ist kein Tätigkeitssynonym mehr, sondern `szenarien.eigenwerbung`. `offen.waehrung` steht im Register, Fremdwährung ohne Nachweis bleibt Rückfrage.
- Suite-100 100/100, Erfahrungs-Suite 120/120, keine geänderte Erwartung. Kern-Tests 42, Wächter grün. `lauf_offline.py` fehlt, die 1.000er-Quote wurde nicht neu gezählt.

## Register aus den KSK-Infos (18.10.2026)
- 104 neue Registerzeilen, jede mit Fundstelle aus den PDFs unter `quellen/`. Liste und bewusste Lücken: `aufgaben/audit/register_luecken_2026-10-18.md`.
- Info 06: weitere Tätigkeitsbegriffe (unter anderem Web-Designer, Musiker, Kabarettist, Maskenbildner). Übersetzung, Kunstunterricht, Gesangsunterricht und Stimmcoaching bleiben Rückfrage.
- Info 12: Schülergrenze 20 und die Vermutung zwischen 20 und 60 ergänzt. Die 60 bleibt. Info 11: Stadt, Landkreis und Gemeinde sind nicht von der Abgabe ausgenommen.
- Suite-100 100/100, Erfahrungs-Suite 120/120. Geänderte Erwartungen nur T-093, E-017 (Webdesign) und E-024 (Maskenbildner am Theater). `lauf_offline.py` fehlt, die 1.000er-Kontrolle wurde nicht neu gezählt.

## Dokumentprüfungen Kategorie A, Cent-Toleranz, Konzert/Musik (18.10.2026)
- Fünf Prüfungen im Kern, jede mit eigener Registerzeile und Fundstelle: Rechenprobe brutto (Widerspruch = Sperre, keine Abgabe), doppelte Positionsnummer (Sperre), negative Gesamtsumme ohne Storno (Sperre; mit Storno im selben Jahr Rückfrage), Widerspruch § 19 UStG (Sperre), unklarer Skonto (Rückfrage, keine Sperre).
- Rundung: bis 1 Cent kein Sperrgrund, Hinweis „Rundungsdifferenz 1 ct, rechnerisch unbedeutend“; ab 2 Cent Sperre. Beide Grenzen stehen im Register (`sperre.toleranz`, `sperre.toleranz_ab`, `sperre.toleranz_hinweis`).
- Blatt Tätigkeitsabgrenzung, T-07: `konzert` und `musik` zählen nur als benannte Leistung. „des Konzerts“ / „eines Konzerts“ ist eine Erwähnung (`app/taetigkeit_erkennung.json`). „Konzert“ und „Konzerthonorar“ bleiben T-07.
- Messung: Suite-100 **100/100**, Erfahrungs-Suite **120/120**. Kern-Testfälle 94 ausgeführt, 0 Abweichung. `lauf_offline.py` liegt nicht im Repo; der Korpus (1.822 Fakten) über `bewertung._rufe_kern_auf` weicht in 80 Fällen der Familien F09, F11 und F15 von den Buchstaben im Soll ab – derselbe Codepfad wie vor diesem Auftrag, keine neue Sperre in diesen Familien.

