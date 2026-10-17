# Auswertung: Testfall „Sammelrechnung mit 20 Positionen“ (11.10.2026)

Erfundene Testdaten des Nutzers (`KSK_Testfall_20_Positionen.xlsx`) als Katalog `aufgaben/audit/testfall_20_positionen.json`, Lauf über den Workflow „Testfall 20 Positionen“. Soll-Werte stammen aus der Testdatei und sind **nicht** vom Steuerberater geprüft.

Annahmen, damit jeder Fall eindeutig ist: Jahr 2026, Auftraggeber ist eine Werbeagentur (typischer Verwerter, also keine Geringfügigkeitsgrenze), Auftragnehmer eine selbständige Einzelperson. Ausnahmen sind Pos. 6, 8, 12 und 18 (Kapitalgesellschaft; Pos. 18 an Google habe ich ergänzt). S-00 ist die ganze Rechnung, S-01 bis S-20 sind die Positionen einzeln.

## Ergebnis

| Lauf | RICHTIG | FALSCH | FEHLER | Sammelrechnung (Soll 8.850 € → 433,65 €) |
|---|---|---|---|---|
| Demo | 13 | 8 | 0 | 22.170 € → 1.086,33 € |
| Mistral small im SaaS | 13 | 8 | 0 | 18.200 € → 891,80 € |
| Mistral large im SaaS | 12 | 7 | 2 | 18.200 € → 891,80 € |
| Mistral large roh (ohne SaaS) | 7 | 14 | 0 | 13.500 € → 243 € (rechnet falsch) |

Richtig sind im SaaS alle 9 künstlerischen Positionen (mit genauer Abgabe) und alle 4 Zahlungen an Kapitalgesellschaften.

## Befund 1 (schwer): keine Prüfung der Tätigkeit

Das System prüft nicht, **ob die Leistung künstlerisch oder publizistisch ist**. Jede Zahlung an eine Einzelperson gilt als Honorar und wird als „Abgabepflichtig“ ausgegeben, auch Programmierung (Pos. 2), Korrektorat (4), Gerätemiete (10), SEO-Audit (13), Projektmanagement (15), Workshop-Moderation (16) und DSGVO-Beratung (20). Das Schema hätte dafür `kuenstlerisch: false`, aber kein Modell hat es gesetzt. Nach unserer Regel soll das Modell das auch nicht entscheiden.

Gefährlich daran: Es kommt ein **sicheres** Ergebnis („Abgabepflichtig“) heraus, statt einer Rückfrage oder „Grenzfall“. Die 9.350 € dieser sieben Positionen sind der ganze Unterschied zwischen 18.200 € und 8.850 €.

Vorschlag (noch nicht gebaut): Tätigkeitsprüfung als eigener Schritt. In der Excel kommt ein neues Blatt „Tätigkeiten“ dazu (künstlerisch / nicht künstlerisch / Grenzfall, jeweils mit Fundstelle, zum Beispiel KSK-Info und Rechtsprechung). Das Modell ordnet die Beschreibung nur einer Tätigkeit aus dieser Liste zu. Ist die Tätigkeit unbekannt oder ein Grenzfall, gibt es nie „Abgabepflichtig“, sondern eine Rückfrage oder „Grenzfall → Steuerberater entscheidet“.

## Befund 2: Sammelrechnung ist mühsam

Mit dem kleinen Modell fragt das System die Rechtsform **für jede Position einzeln** ab (bei 20 Positionen bis zu 16 Klicks). Besser wäre eine Frage: „Gilt ‚Einzelperson‘ für alle Positionen ohne eigene Angabe?“

## Befund 3: zwei technische Fehler bei large

Bei Pos. 7 und Pos. 16 passte die Antwort von Mistral large nicht zum Fakten-Schema. Das System hat richtig reagiert und nachgefragt, statt zu raten. Der genaue Grund ist im Protokoll abgeschnitten; er muss noch ermittelt werden.

## Vergleich roh

Mistral ohne SaaS rechnet mit 5 % statt 4,9 %, kommt bei der Sammelrechnung auf eine unmögliche Summe (13.500 € → 243 €) und nennt Fundstellen, die nicht in unseren Quellen stehen (zum Beispiel „KSK-Info 10/2022 (Abgrenzung …)“, BSG-Aktenzeichen). Dafür erkennt es nicht künstlerische Tätigkeiten teilweise (Pos. 10, 20, Grenzfall bei 15). Das zeigt: Die Tätigkeitsprüfung fehlt bei uns, nicht beim Modell. Sie muss aber aus belegten Regeln kommen.

## Hinweise zur Testdatei (für den Steuerberater, prüfen)

- Die Regel-Referenzen R-01 bis R-20 der Testdatei sind Platzhalter. Sie passen nicht zu unserem Regelkatalog (dort ist zum Beispiel R-15 die Drei-Veranstaltungen-Regel).
- Pos. 10 (Gerätemiete): Stellt dieselbe Einzelperson sie in Rechnung, die auch die künstlerische Leistung erbringt, zählt sie nach § 25 KSVG vermutlich zum Entgelt. Das Soll „nicht abgabepflichtig“ gilt dann nur, wenn ein reiner Verleiher sie abrechnet. (prüfen)
- Pos. 4 (Korrektorat) und Pos. 16 (Moderation) sind Abgrenzungsfragen. Das Soll sollte der Steuerberater bestätigen. (prüfen)

## Nach dem Einbau der Tätigkeitsprüfung (11.10.2026, mistral-large-latest)

| Lauf | RICHTIG | NACHGEFRAGT | FALSCH | FEHLER | Sammelrechnung |
|---|---|---|---|---|---|
| Demo | 18 | 3 | 0 | 0 | Grenzfall: ohne unsichere Leistungen 433,65 €, mit ihnen 603,68 € |
| Mistral large im SaaS | 18 | 3 | 0 | 0 | Grenzfall: ohne unsichere Leistungen **433,65 € (= Soll)**, mit ihnen 639,45 € |
| Mistral large roh | 7 | 0 | 14 | 0 | – |

Die drei Fälle mit NACHGEFRAGT gehen bewusst an den Steuerberater:
- Pos. 10 Gerätemiete: Stellt der Künstler sie selbst in Rechnung, zählt sie als Nebenkosten mit (R-42, R-175). Eine reine Vermietung ist im Regelwerk nicht geregelt.
- Pos. 16 Workshop-Moderation: Das Modell wählte „Moderation“ (künstlerisch), die feste Erkennung „Workshop“ (nicht künstlerisch, R-183). Bei solchem Widerspruch entscheidet der Steuerberater.
- Pos. 20 DSGVO-Beratung: Dazu gibt es in unseren Quellen keine Fundstelle („nicht im Regelwerk eingeordnet“).

Im ersten Lauf traten zusätzlich HTTP 429 auf, weil zwei Workflows gleichzeitig liefen, und einmal `"positionen": [1800]`. Das System liest eine Zahl jetzt als Betrag.
