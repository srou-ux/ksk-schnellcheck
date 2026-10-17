# ALLTAG-2026-999 „Viel-Künstler-Sammelrechnung“ – Test direkt im Chatbot und Optimierung

Grundlage: `claude-auftrag-alltag999.txt` und `alltag999-vielkuenstler-rechnung.txt` (Nutzer, 11.10.2026), erfundene Daten. Katalog: `aufgaben/audit/testfall_alltag_999.json`, jetzt auch im Testarchiv (`alltag999:A-999`).

**Ausführung wie ein echter Nutzer:** Die Rechnung wurde in das Eingabefeld der echten Weboberfläche getippt. Ein Browser (Playwright) klickte die Knöpfe und „Ja, das stimmt“ (`aufgaben/audit/chatbot_direkt.py`, Workflow „Chatbot direkt“). Modell: mistral-large-latest.

## Rechnung nachgerechnet

Von den beiden mitgelieferten Fassungen stimmt die mit **11.686,00 €**. Die Positionssumme ist 11.686,00 €, nicht 12.686,00 €. Daraus folgen USt 19 % = 2.220,34 € und brutto 13.906,34 €. Getestet wurde diese Fassung. Die Soll-Abgabe stimmt: 4.520,00 € × 4,9 % = 221,48 €.

## Ergebnis je Position (nachher)

| Pos. | Leistung | Chatbot | Soll | Match |
|---|---|---|---|---|
| 01 | Fotograf, eigener Name | an GmbH, ausgeschlossen | ausgeschlossen | Ja |
| 02 | Band, eigener Name | an GmbH, ausgeschlossen | ausgeschlossen | Ja |
| 03 | Grafikerin, eigener Name | an GmbH, ausgeschlossen | ausgeschlossen | Ja |
| 04 | Schauspieler, eigener Name | an GmbH, ausgeschlossen | ausgeschlossen | Ja |
| 05 | Tänzerin, eigener Name (700 €) | an GmbH, ausgeschlossen | ausgeschlossen | Ja (vorher Nein, Befund B2) |
| 06 | Autor, eigener Name | an GmbH, ausgeschlossen | ausgeschlossen | Ja |
| 07 | Journalist, eigener Name | an GmbH, ausgeschlossen | ausgeschlossen | Ja |
| 08 | Sängerin, Vertrag direkt, durchgereicht (700 €) | einbezogen 700,00 € | einbezogen 700,00 € | Ja (vorher Nein, B1) |
| 09 | Lichtkünstlerin, Vertrag direkt | einbezogen 1.100,00 € | einbezogen 1.100,00 € | Ja (vorher Nein, B1, B3) |
| 10 | Komponist: 480 € Provision / 2.720 € Direktzahlung | 2.720,00 € einbezogen; 480 € nicht, als **offen** gekennzeichnet (mit Provision 245,00 €) | 2.720,00 €; Provision offen | Ja (vorher Nein, B1, B6) |
| 11 | Reisekosten pauschal, Anhang fehlt | an GmbH, ausgeschlossen, keine Rückfrage | ausgeschlossen, keine Rückfrage | Ja |
| 12 | Equipment-Miete NL | an GmbH, ausgeschlossen, keine Auslandswarnung | ausgeschlossen, keine Warnung | Ja |
| 13 | lit. Übersetzung, eigener Name | an GmbH, ausgeschlossen | ausgeschlossen | Ja |
| Summe | | **abgabepflichtig, BG 4.520,00 €, Abgabe 221,48 €, keine Rückfrage, Fundstelle § 24 Abs. 1 Satz 1 Nr. 3** | dasselbe | Ja |

Vorher, live im Chatbot (Stand `e6d09f6`): **FALSCH**. Grenzfall, 1 Rückfrage (Art des Auftraggebers), und die Antwort nannte „§ 24 Abs. 1 Satz 1 Nr. 7“. Nachher (Stand `92c6002`): **RICHTIG**, 0 Rückfragen.

## Befunde und Fixes (je mit Test in `tests/app/test_alltag999.py`)

| Nr. | Kategorie | Befund | Ursache | Fix (Regelbasis mit Quelle) |
|---|---|---|---|---|
| B1 | a, c | Durchleitung und Direktzahlung (Pos. 08, 09, 10) wurden „Steuerberater entscheidet“ statt einbezogen | Die Härtetest-Regel 777 behandelte jede Abweichung vom eigenen Namen als unklar | Zwei Arten je Satzteil des Betrags (`app/rechnungsteller_begriffe.json`): **vertrag_direkt** (Vertrag unmittelbar mit dem Künstler, Vertretung, Direktzahlung) zählt beim Mandanten (KSK-Info 27 S. 1; KSK-Info 13 Abschn. II.1a; R-127, R-36, R-94; Baustein TB-28). **unklar** (Provision, Vermittler, vertragswidrig) entscheidet der Steuerberater (TB-27). |
| B2 | a | Pos. 05 (700 € Tanz, eigener Name) wurde wie Pos. 08 (700 € Gesang, durchgereicht) behandelt | Zuordnung von Position zu Rechnungszeile nur über den Betrag | Bei gleichem Betrag in mehreren Zeilen entscheidet die Übereinstimmung mit der Bezeichnung. |
| B3 | b | Lichtkünstlerin „nicht im Regelwerk eingeordnet“ | Tätigkeitsliste ohne Lichtkunst, Autor, Bühnenbild u. a. | Neue Zeile **T-19** aus der Liste der KSK-Info 06 (Light-Designer, Lichtkunst, Konzept-, Medien-, Video-, Performance-, Objektkunst, Plastik, Bühnen-/Szenen-/Kostümbild, Schriftsteller/Autor, Lesung, Regie, Dramaturgie). |
| B4 | d | Fundstelle „§ 24 Abs. 1 Satz 1 Nr. 7“ bei einer Veranstalterin | Der Kern nennt für jeden typischen Verwerter R-07 | Die Nummer ergibt sich aus der Beschreibung des Auftraggebers (`app/verwerter_nummer.json`): Messe → R-03 + R-126, Konzertdirektion/Festival → R-03, Verlag → R-01, Werbeagentur → R-07 usw. Unbekannt → keine Nummer. |
| B5 | e | Rückfrage „Art des Auftraggebers“ | „Mittelstands Messe Koblenz GmbH, Veranstalterin“ wurde nicht erkannt | In der Zeile, die den Auftraggeber beschreibt („Rechnung an“, „Mein Mandant“ …), belegt „Messe“ einen typischen Verwerter (KSK-Info 13, R-126). Nicht bei Eigenwerbung oder Privatperson im Text und nicht bei „Messestand“. |
| B6 | c | Provision 480 € | offen nach R-38/R-39 (Vorlage-Vorbehalt) | Nicht mitgezählt (Zahlung an die GmbH). Die Antwort kennzeichnet sie als offen; den Fall „zählt mit“ rechnet der Kern zusätzlich (245,00 €, TB-29/TB-30). |
| B7 | f | Umsatzsteuer erschien als „Zahlung an Kapitalgesellschaft“ | Die Rechnungsteller-Regel überschrieb auch Sonderrollen | Sonderrollen (USt, GEMA …) behalten ihren eigenen Grund. |
| B8 | (Gesamtsuite) | P-30 schwankte live zwischen richtig und Grenzfall | Das Modell setzte die Rolle „nachgewiesene Reisekosten“ nicht immer | Steht direkt beim Betrag ein Reise- und ein Nachweis-Begriff und keine Pauschale, gilt die Rolle (R-47). |
| B10 | (Gesamtsuite) | P-30: „Honorar“ des „freien Designers“ blieb uneingeordnet, wenn das Modell keine Leistungsart lieferte | Nur `leistungsart` wurde für allgemeine Bezeichnungen benutzt | Nennt der ganze Text nur künstlerische Tätigkeiten, gilt diese für das allgemeine „Honorar“. |
| B11 | (Gesamtsuite) | P-28: „1.190 € brutto, darin 190 € USt“ – Honorar mit dem ganzen Betrag, Rückfrage | Teil gleich Rechnungsbetrag | Nennt der Text genau einen enthaltenen Teilbetrag, ist diese Position der Rest (der Kern rechnet 1.000 €). |
| B9 | (Demo) | Demo-Modus zählte „an die GEMA gezahlt“ als Honorar (P-34) | Demo-Heuristik ohne Rollen | Ein Betrag und eine genannte Verwertungsgesellschaft → Rolle Verwertungsgesellschaft (R-44). |

Kein Fix steht im Prompt. Alles liegt in der Regelbasis (Excel und JSON-Begriffslisten) oder in der Engine, mit Fundstelle. Die Soll-Werte im Testarchiv wurden nicht geändert. Neu aufgenommen wurde nur A-999.

## Gesamtsuite, direkt im Chatbot (Browser, live)

| Stand | Fälle | richtig | nachgefragt | falsch | Fehler |
|---|---|---|---|---|---|
| vorher (`386dc28`) | 77 | 56 | 21 | 0 | 0 |
| nach B1–B7, B9 (`92c6002`) | 78 | 60 | 18 | 0 | 0 |
| Endstand (`87e78a7`, nach B8–B10 und dem Dialog „Der schwierige Kunde“) | 78 | 59 | 19 | **0** | 0 |

## Vorbehalte (nicht als endgültig festgeschrieben)

- **Pos. 10 Provision (R-38/R-39):** bleibt offen. Das System zählt sie nicht mit, nennt aber den anderen Betrag.
- **Tätigkeitsliste:** T-19 ist neu, aus KSK-Info 06, Entwurf. Pos. 03 „Bühnengrafik“ (T-02) und Pos. 09 Lichtkunst (T-19) sind vom Steuerberater zu prüfen.
- **Folge für den Härtetest 777:** Pos. 03 (Durchleitung) zählt jetzt beim Mandanten. Der „Lichtdesign-Workshop“ bleibt nach T-34 aber „nicht künstlerisch“ und zählt deshalb trotzdem nicht. Pos. 02 (vertragswidrige Zahlung) und die Provision bleiben offen.
- **Fundstellen:** Bei R-03 erscheint ein BSG-Urteil aus derselben Excel-Zeile unter „Norm“. Die Ebene richtet sich nach der Gruppe der Regel. Gemeldet in `FUNDE_Chatbot.md`, nicht geändert.
- **Burggraben:** Regelbasis, Schema und Soll-Werte liegen nur im privaten Repo `srou-ux/ksk-assistent`, nichts davon ist öffentlich.

Vergleich Endstand gegen vorher (77 gemeinsame Fälle, live im Browser): besser P-34, P-39; schlechter keiner; kein neuer FALSCH- oder FEHLER-Fall. Die Antworten des Modells schwanken von Lauf zu Lauf; P-28/P-30 waren in einzelnen Läufen nachgefragt. Die Fixes B8, B10 und B11 machen sie unabhängiger vom Modell.
