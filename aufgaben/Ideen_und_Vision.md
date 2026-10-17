# Ideen und Vision (gespeichert 08.10.2026)

Arbeitsweise: eine Sache nach der anderen. Dieses Dokument hält die Ideen fest, damit nichts verloren geht.

## Vision
- Das SaaS soll für Steuerberater und Agenturen die **Referenz** zur Künstlersozialabgabe sein: belegt, nachvollziehbar, mit sichtbaren Lücken.
- „Referenz“ heißt: Fundstelle zu jeder Aussage, Regeln mit Gültigkeit und Version, Testfälle gegen Urteile, fachliche Prüfung durch Steuerberater/Fachanwalt. Es heißt NICHT „von der KSK anerkannt“. Nicht mit „KSK-geprüft“ oder „offiziell“ werben, solange es keine Anerkennung gibt (Gespräche mit KSK/DRV bzw. Kammern wären ein eigener Schritt).
- Grundsatz: Das System macht Vorschläge, der Steuerberater entscheidet.

## Chatbot
- Spricht mit Steuerberatern auf Expertenebene (Kollegenton).
- Nennt Rechtsurteile und alles Einschlägige: Gesetz, BSG/LSG/SG, KSK-Infos, Verwaltungspraxis – getrennt nach Ebene, mit Fundstelle, Gegenansicht und Risiko.
- Nennt nur Urteile aus der Quellenbasis; keine erfundenen Aktenzeichen.
- Bei fehlender Quelle: „nicht abgedeckt“, Frage landet anonymisiert im Lückenprotokoll.
- **Lösungsvorschläge (Idee 08.10.2026):** Der Bot schlägt bei Problemen auch Lösungswege vor, jeweils mit Referenz. Beispiele: Betriebsprüfung der DRV (Unterlagen, Fristen, Rechtsbehelfe), Nachforderung, Korrektur einer Meldung, Abgrenzung Grenzfall, Umgang mit Auslandsleistungen. Jeder Vorschlag nennt: Handlungsoption, Fundstelle (Norm/Urteil/KSK-Info), Voraussetzungen, Risiko, Alternative. Nur Optionen aus der Quellenbasis; sonst „nicht abgedeckt“. Der Steuerberater entscheidet. Dazu ein Feld „Lösungsweg“ im Antwortschema und Testfälle dafür.
- Vollständigkeit ist nicht garantierbar; Ziel: Kern sehr gut abdecken, Lücken zeigen, laufend ergänzen.
- Dateien: `regelwerk/Chatbot_Systemanweisung_Entwurf.md`, `regelwerk/Chatbot_Musterdialoge_Entwurf.md`, `regelwerk/Fragenkatalog_Chatbot_Entwurf.xlsx`.

## Quellen vs. Code
- Quellenoriginale bleiben unverändert (Hash, Herkunft).
- Regeln und Zahlen als versionierte Daten (Regelkatalog, Tabellen) mit Fundstelle, Gültigkeit, Status – nicht im Code verstreut. Code liest und rechnet nur; Berechnung nicht im Sprachmodell.

## Aus dem externen Prüfbericht (PDF Fehlerkatalog) zu übernehmen
- B1: Verpflegungspauschale „mehr als 8 Stunden“ (§ 9 Abs. 4a EStG) in Regel R-47/R-176 ergänzen + Test für genau 8 Stunden.
- B2/B3: identische KSVG-Archivkopien per SHA-256 erkennen; unbelegte Index-Aussage einschränken.
- B4: aus dem Änderungsgesetz 2022 abgeleitete Daten als „unbestätigt“ markieren.
- Statusmodell: Entwurf | technisch geprüft | fachlich zu klären | fachlich freigegeben | aktiv | gesperrt.
- Kontroll-/Testliste R01–R48 aufnehmen.

## Offene Reihenfolge
1. Recherche 2 (Claude Code) abwarten, Ergebnisse einarbeiten.
2. Übernahmen aus dem Prüfbericht.
3. Audit der Regeln ab R-205 nach jeder Erweiterung wiederholen (R-205–R-236 bereits geprüft).
4. Abnahme durch Steuerberater/Fachanwalt; erst dann aus „Entwurf“ heraus.
5. Später: Interviewleitfaden, Spezifikation Rollen/Protokoll, Prototyp (EU-Hosting, Mistral zuerst, RAG nur öffentliche Quellen).

## Qualitätsanspruch (Idee 08.10.2026)
Der Bot soll in der Sache besser arbeiten als ein einzelner Berater, weil er Entscheidungsvorschläge auf Referenzen stützt. Messbar gemacht über: 100 % der Aussagen mit Fundstelle, gleiche Frage = gleiche Antwort (Konsistenz), Prüfung gegen Testfälle/Urteile, vollständiges Abarbeiten aller Tatbestandsmerkmale, keine vergessenen Fristen, sichtbare Lücken. Grenze: Verantwortung und Würdigung des Einzelfalls bleiben beim Steuerberater; Nachweis der Qualität durch Vergleichstest (Bot vs. Steuerberater auf denselben Testfällen) und fachliche Abnahme.

## Gezielte Informationsabfrage und Entscheidung (Idee 08.10.2026)
Der Bot fordert fehlende Informationen aktiv an (strukturierte Fallaufnahme je Fallgruppe, inkl. Unterlagen/Belege) und kommt dann zu einem begründeten, eindeutigen Ergebnis statt „kommt darauf an“. Eindeutige Fälle: klare Entscheidung mit Fundstelle. Grenzfälle: Entscheidung mit Wahrscheinlichkeitseinschätzung, Gegenansicht und Risiko. Formal bleibt die Freigabe beim Steuerberater (Freigabe-Schritt, Protokoll). Umsetzung: Fragebäume pro Fallgruppe (Eigenwerber, Verwerter, Veranstalter, Auslandsleistung …), Pflichtfelder vor dem Ergebnis, Ergebnis nur bei vollständigen Angaben; Testfälle dazu.

## Gleiche Standards bei der Rechnungsanalyse (Idee 08.10.2026)
Alles, was für den Chatbot gilt, gilt auch für die Analyse von Rechnungen/Zahlungen: Fundstelle zu jeder Einstufung, Ebenentrennung (Gesetz / Rechtsprechung / KSK-Praxis / Ableitung), Gegenansicht und Risiko, Lösungsvorschläge mit Referenz, aktive Nachfrage fehlender Angaben (Jahr, Leistungsart, Auftragnehmer, Netto/Brutto, Reisekosten, Anzahl Aufträge), eindeutiges Ergebnis oder „Grenzfall / Rückfrage / nicht abgedeckt“, Freigabe durch den Steuerberater mit Protokoll, Rechnung im Code. Umsetzung: EIN gemeinsamer Regelkern (Regelkatalog + Zahlentabellen + Fragebäume) für Chatbot und Analyse, keine zwei getrennten Logiken. Jede Position einer Analyse zeigt Ergebnisklasse, Regel-ID, Fundstelle, Bemessungsgrundlage und offene Rückfragen; Summen und Jahresmeldung werden aus den freigegebenen Positionen berechnet. Testfälle (Regelwerk/Testfaelle) gelten für beides.

## Weitere Ideen – für später (gespeichert 09.10.2026; Fokus bleibt auf den Ideen oben)
1. Rechtsänderungs-Überwachung: regelmäßige Prüfung neuer Sätze, Verordnungen, Urteile, KSK-Infos; zeigt betroffene Regeln und bereits geprüfte Fälle.
2. Prüfungsmappe für die DRV-Betriebsprüfung: pro Jahr alle Einstufungen mit Fundstelle, Belege, Freigaben, Rechenweg.
3. Risiko-Ampel pro Mandant: Grenzfälle, fehlende Belege, Nähe zur Schwelle, Ausland, Veranstaltungen; geschätzte Nachforderung inkl. Säumniszuschlag und 4-Jahres-Verjährung.
4. Erkennung aus der Buchhaltung (Kontenlisten, DATEV-Export): verdächtige Buchungen markieren.
5. Was-wäre-wenn-Rechner (Schwelle 2026, Ausgleichsvereinigung) mit Rechenweg.
6. Mandantenfertige Textentwürfe (Mandantenschreiben, Meldebogen-Erläuterung, Antwort an KSK), belegt, „Entwurf“.
7. Lerneffekt aus Freigaben: Korrekturen als anonymer Hinweis zur Regel, nur nach fachlicher Prüfung übernehmen.
8. Öffentliche Qualitätsseite: Quellenstand, Abdeckung, Testergebnisse, bekannte Lücken.
Favoriten für den Start: Nr. 1 und Nr. 2.

## Import großer Datenmengen (CSV/Excel) – für später
Tausende Buchungszeilen werden nicht vom Sprachmodell gelesen, sondern direkt per Python eingelesen. Der Nutzer ordnet die Spalten zu (Betrag, Datum, Empfänger, Text); die Zuordnung zu Rollen (künstlerisch, Rechtsform) erfolgt als Vorschlag mit Bestätigung. Gegenrechnung in der Prüf-Sandbox, Lauf in Stapeln, Fortschrittsanzeige. Anonymisierung vor jeder Speicherung. Erst nach Teil 1e und RAG.

## Admin-Seite für Pflege und Updates – für später (Entscheidung des Nutzers, 09.10.2026)
Ersetzt das Bearbeiten der Excel von Hand. Formulare für Werte, Regeln und Quellen mit Pflichtfeldern (Fundstelle, Gültigkeit, Status). Automatische Prüfungen mit Änderungsbericht auf der Seite (Lücken, Überschneidungen, Wert steht in der Quelle, Tests, Gegenrechnung in der Prüf-Sandbox). Freigabe mit Rolle und Protokoll (wer, wann, welche Version), Zurückrollen. Hinweise: fehlendes Jahr, Quelle älter als ein Jahr. Daten in PostgreSQL statt Excel; der Kern liest über dieselben Funktionen (`reg()`, `wert()`), `aufgaben/PFLEGE_Update_Anleitung.md` wird dann angepasst. Voraussetzung: Konten und Rollen, EU-Hosting. Bis dahin gilt die Pflegeanleitung mit der Excel.

## Optimierung – nach dem Fundament (Entscheidung des Nutzers, 09.10.2026)
Erst messen, dann optimieren. Reihenfolge: richtig, belegt, schnell. Mögliche Felder: Geschwindigkeit (Zeitmessung pro Schritt aus Teil 1e, dauerhaft laufende Sandbox, gebündelte Modellaufrufe, schnellere Suche), Qualität (Trefferquote des Quellenabrufs, weniger unnötige Rückfragen, bessere Eingabeerkennung), Pflege (Admin-Seite, Update-Agent), Code (Regeln in kleine, getestete Einheiten/Regeltypen zerlegen), Kosten (Zahl der Modellaufrufe, Modellwahl je Aufgabe). Jede Optimierung braucht vorher/nachher-Messwerte und darf keinen Test verschlechtern.

## Fehlermelde-Programm (Konzept, Schritt 7)
Nutzer melden Fehler per Formular (Fall anonym, Systemantwort, Erwartung, Fundstelle Pflicht). Eine KI sortiert vor (nur Triage, Zahlen rechnet Kern/Verifier), ein Mensch bestätigt, Korrektur als neue Version, erster Melder eines bestätigten Fehlers erhält 100 Credits. Details: `aufgaben/SYSTEMBESCHREIBUNG_fuer_KI.md` Abschnitt 7. Offen: Verarbeitung in Europa (Mistral EU zuerst).
