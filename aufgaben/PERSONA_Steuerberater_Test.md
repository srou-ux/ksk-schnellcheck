# Test aus Sicht des Steuerberaters (Entwurf), 09.10.2026

Methode: 12 typische Fragen in freier Sprache, wie sie in der Praxis kommen, durch den Chatbot im Demo-Modus (FakeLLM mit einfacher Mustererkennung). Skript: `aufgaben/audit/persona_steuerberater.py`.
**Einschränkung:** Der Demo-Modus erkennt nur grobe Muster. Ein Teil der Rückfragen entsteht dadurch, dass das Ersatzmodell die Frage nicht einordnet; mit Mistral wird das besser sein und ist **noch nicht getestet** (kein Schlüssel). Die Befunde 1 und 2 sind unabhängig vom Modell.

## Ergebnis
| Frage | Ergebnis |
|---|---|
| Verein, Webdesigner 900 €, 2026 | Antwort: nicht abgabepflichtig (Vorschlag), mit Norm und Verwaltungspraxis. **Funktioniert.** |
| Werbeagentur, Grafiker 2.400 €, 2025 | Rückfrage nach der Rechtsform des Grafikers (richtig, denn die Rechtsform entscheidet). |
| GmbH-Dienstleister 5.000 €, 2025 | Rückfrage nach der Leistungsart, obwohl Zahlungen an eine GmbH ohnehin nicht zählen. Unnötige Rückfrage. |
| Vorauszahlung 2026 bei Vorjahres-BG 31.500 € | Rückfrage nach Rechtsform und Leistungsart, die dafür nicht gebraucht werden. Unnötig. |
| Säumniszuschlag (Rückstand 2.000 €, 4 Monate, 2025) | Dieselben unnötigen Rückfragen. |
| Fotograf 1.800 € mit 300 € nachgewiesenen Fahrtkosten, 2024 | Rückfrage nach Rechtsform (richtig). |
| Vier Veranstaltungen, 3.500 € Honorare, 2025 | Rückfrage nach Rechtsform und Leistungsart statt nach der Einnahmeabsicht (der Kern braucht sie). Falsche Rückfragen. |
| **Bis wann Jahresmeldung 2025?** | Keine Antwort. Rückfragen zu Betrag, Rechtsform, Leistung. |
| **Wie lange Aufzeichnungen aufbewahren?** | Keine Antwort, Rückfrage nach dem Jahr. |
| **Wie hoch war der Abgabesatz 2024?** | Keine Antwort, Rückfragen zu Betrag, Rechtsform, Leistung. |
| **Welche Tätigkeiten gelten als künstlerisch/publizistisch?** | Keine Antwort, Rückfrage nach dem Jahr. |
| **Was sagt das BSG zur Abgrenzung bei Werbeagenturen?** | Rückfrage nach dem Jahr, obwohl Teil 1b reine Rechtsprechungsfragen ohne Jahr erlauben sollte. Das Ersatzmodell erkennt die Fragenart nicht. |

## Befunde
1. **Auskunftsfragen sind nicht angebunden (modellunabhängig).** Kern und Register kennen Abgabesatz, Schwelle, Meldefrist, Aufbewahrungsfrist, Pauschalen, Vorauszahlungsgrenze und die Tätigkeitsliste, aber der Chatbot hat dafür keinen Weg. Das sind die häufigsten einfachen Fragen eines Steuerberaters. Vorgeschlagen: Anfrageart `auskunft` mit den Unterarten Abgabesatz, Schwelle, Frist (Meldung, Aufbewahrung, Vorauszahlung), Pauschale, Tätigkeitskatalog. Antwort direkt aus Register/Katalog mit Fundstelle, ohne Rechtsform und Betrag zu verlangen; Jahr nur dort Pflicht, wo die Antwort vom Jahr abhängt.
2. **Pflichtangaben zu pauschal.** Rückfragen wie „Rechtsform des Auftragnehmers" kommen auch dort, wo der Kern sie nicht braucht (Vorauszahlung, Säumniszuschlag, GmbH-Zahlung, Veranstaltungen). Pflichtangaben müssen aus dem Bedarf des gewählten Kernaufrufs kommen (welche Eingaben braucht `vorauszahlung_monatlich`, `saeumniszuschlag`, `veranstaltungen`), nicht aus einer allgemeinen Liste.
3. **Mehrere Positionen in einer Frage** („Grafiker 2.400, Texter 1.100, GmbH-Studio 5.000, Fotograf 800 mit 150 Reisekosten") sind das übliche Mandantenbild. Muss mit einem echten Modell getestet werden; die Bestätigung zeigt die Liste.
4. **Rückfragen als Schnellauswahl.** Ein Profi will Antworten anklicken („natürliche Person / GbR / GmbH …", „Jahr: 2025"), nicht tippen. Weboberfläche: Rückfragen als Schaltflächen, Mehrfachfragen zusammen in einem Formular.

## Was ein Steuerberater im Alltag außerdem will (Anforderungen, noch nicht gebaut)
- Mehrere Mandanten und Jahre getrennt führen, Fälle speichern und wieder öffnen.
- Eine Liste von Zahlungen hochladen (Excel/CSV, Buchhaltungsexport) und eine Auswertung bekommen: je Zahlung abgabepflichtig/nicht/Grenzfall, Summe, Bemessungsgrundlage, Abgabe, Vorauszahlung.
- Ergebnis als druckbares Gutachten/Vermerk mit Fundstellen für die Handakte (PDF) und als Entwurf für die Jahresmeldung.
- Aufbereitung für eine DRV-Prüfung: alle Fälle eines Jahres mit Begründung und Regelversion.
- Hinweis bei Rechtsänderungen, die laufende Mandate betreffen.
- Fristenübersicht je Mandant (Meldung bis 31.03., Vorauszahlungen).

## Test mit Claude als Sprachmodell (Skript `aufgaben/audit/persona_claude_als_llm.py`, 12 Fälle)
Fakten von Hand geschrieben, durch die echte Pipeline geschickt. Entwurf – vom Steuerberater zu prüfen.

Funktioniert: Fälle 1b, 3, 4, 5, 9.

Befunde (für Auftrag Teil 1f):
- Fall 8: Gemischte Positionen. Die Rechtsform gilt nur global (`auftragnehmer_typ`), nicht je Position. Ergebnis BG 9.300 statt 4.300. Rechtsform muss je Position gelten und in der Faktenbestätigung angezeigt werden.
- Fall 7: Säumniszuschlag wird als „Abgabepflichtig … Abgabesatz 5 %" angezeigt. ABGABESATZ nur bei Bemessungsgrundlagen-Fällen, eigene Ergebnisformulierung.
- Fall 6: Typischer Verwerter mit BG 0 (GmbH-Empfänger) – im Kern jetzt erklärt („Nicht zur Bemessungsgrundlage … R-138, R-216"); Anzeige in der App prüfen.
- Fall 2: Vorauszahlung: Rundung ungeklärt (ungerundet 128.625) – Recherche 5.
- Fälle 10/11: Auskunftsfragen (Abgabesatz, Schwelle, Meldefrist, Aufbewahrung, Pauschalen) haben keine Route → neue Anfrageart `auskunft`.
- Weitere: Pflichtangaben je Kernaufruf statt allgemein; Rückfragen als Schaltflächen; Fundstelle „Kopie 2022-01-22" erscheint bei Veranstaltungen 2025.
