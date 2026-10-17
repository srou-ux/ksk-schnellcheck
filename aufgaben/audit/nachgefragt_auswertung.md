# Auswertung der „nachgefragten“ Fälle (14.10.2026)

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Testfälle.
Ausgangslage: Gesamtlauf 3b58f6a (88 Fälle): 71 richtig, **17 nachgefragt**, 0 falsch.
Messung: Workflow „Modellfehler suchen“, je Fall 6 Läufe mit Fakten-Protokoll (Lauf 38623132724, `aufgaben/audit/modellfehler_fakten_*_38623132724.jsonl`).

**Ergebnis der Messung:** 16 der 17 Fälle waren in **allen 16 bisherigen Gesamtläufen** und in **6 von 6** Messläufen nachgefragt. Das ist also kein Modell-Zufall, sondern festes Verhalten des Systems. P-31 war 6 von 6 richtig (der eine Ausreißer im Gesamtlauf war Zufall).

## Einordnung je Fall

| Fall | Soll | Was das System tat | Ursache | Einordnung | Stand |
|---|---|---|---|---|---|
| P-02 Webdesigner gestaltet und programmiert (Eigenwerbung) | A, 147,00 € | Grenzfall | Bezeichnung „Website Gestaltung und Programmierung“ allein → T-30 (reine Programmierung); Modell und Text → T-01 (Webdesign, auch mit Programmierung) → Widerspruch | **Schwäche** | **behoben** |
| P-14 Bandleader zahlt Bandmitglieder | A | fragte nach der Art des Auftraggebers | „Bandleader“ war keiner Art zugeordnet | **Schwäche** (R-31) | **behoben** |
| P-20a Übungsleiterpauschale, 2.500 € | N | „Um welchen Honorarbetrag geht es?“ | Modell legt 2.500 € als Gesamtbetrag an; die Pflichtangabe verlangte eine Position | **Schwäche** | **behoben** |
| P-40 Ehepaar, Silberhochzeit, privat | N | fragte nach der Art des Auftraggebers | Privat-Erkennung kannte „Ehepaar … privat“ nicht | **Schwäche** (R-40, R-133) | **behoben** |
| P-16 Hobbyorchester-Verein, Gastsolist 800 €, vereinseigener Dirigent 1.500 € | N | fragte nach der Art des Auftraggebers | Verein nicht als Veranstalter (Generalklausel) erkannt; **R-57** (vereinseigene Dirigenten bleiben außer Betracht) fehlt im Kern | Schwäche – **nicht** einfach zu beheben: nur „Veranstalter“ zu erkennen ergäbe 2.300 € > Schwelle → **falsch** | offen (eigener Schritt: R-57 in den Kern) |
| P-17 Gesangverein, 2 Auftritte, Chorleiter 2.400 € | N | wie P-16 | wie P-16 (R-17, R-30, R-159) | Schwäche | offen (mit P-16) |
| P-18a Musikverein, 15 Schüler | N | wie P-16 | zusätzlich: der Kern (`musikverein_schueler`, R-53/R-54) gibt bewusst „Rückfrage“ („Schülerzahl allein entscheidet nicht“), der Testfall B-06 erwartet „nicht abgabepflichtig“ | **Widerspruch Kern ↔ Testfall** | Frage an den Steuerberater |
| P-36 Agentur mit Vollmacht, Vertragspartner abgabepflichtig | N | „Um welchen Betrag geht es?“ | Grundsatzfrage ohne Betrag; `kern.vertreter` (R-33/R-78) gibt es, der Chatbot ruft ihn nie auf | Schwäche | offen (neuer Weg „Grundsatzfrage ohne Betrag“) |
| P-37 nur Kontakt vermittelt (Nachweismakler) | G oder N | „Um welchen Betrag geht es?“ | wie P-36; Regel R-35 fehlt im Kern | Schwäche | offen (mit P-36) |
| P-11 Restaurant, 50 Abende Livemusik | A oder G (unsicher) | fragte nach der Art des Auftraggebers | Eigenwerbung oder Veranstalter? (R-29, R-36, R-132 „teilweise abgedeckt“) | **Rückfrage vertretbar** | bleibt |
| P-13 Eventagentur bucht Band im eigenen Namen für Kunden | A oder G (unsicher) | wie P-11 | R-33, R-74, R-78 „teilweise abgedeckt“ | **Rückfrage vertretbar** | bleibt |
| P-09 Unternehmen, 4 Veranstaltungen, „bezahlte selbständige Künstler“ | A, 250,00 € | Grenzfall | „Künstler“ ohne Leistung ist in der Excel keiner Tätigkeit zugeordnet | **vorsichtig**; Frage an den Steuerberater: Gilt „Künstler“ bei Veranstaltungen als künstlerische Leistung? | Frage an den Steuerberater |
| S-10 Gerätemiete | N (Testdatei) | Grenzfall | Excel: Grenzfall | **bewusst vorsichtig** (Prüfliste 1, F-02) | wartet auf den Steuerberater |
| S-16 Moderation Firmen-Workshop | N (Testdatei) | Grenzfall | Modell und feste Erkennung uneinig | **bewusst vorsichtig** (Prüfliste 1, F-05) | wartet auf den Steuerberater |
| S-20 DSGVO-Beratung | N (Testdatei) | Grenzfall | Leistung ohne Fundstelle in der Quellenbasis | **bewusst vorsichtig** (Prüfliste 1, F-07) | wartet auf den Steuerberater |
| F3 Versicherung (Eigenwerbung), Rechnung einer GmbH | N | Ergebnis **richtig** (N), aber vorher eine Rückfrage nach der Art des Auftraggebers | „Versicherungsunternehmen mit Marketing“ ist kein ausdrücklicher Beleg für Eigenwerbung; der Testfall erlaubt 0 Rückfragen | **Rückfrage vertretbar** | bleibt |
| P-31 Bewirtung | A | in 6/6 Messläufen richtig | Ausreißer im Gesamtlauf | Modell-Zufall | – |

## Was geändert wurde (alles deterministisch, mit Fundstelle)

- `app/privat_begriffe.json`: Privatfeier-Begriffe aus R-40/R-133 (Hochzeits-, Geburtstags-, Familienfeier, Silberhochzeit, „privat“) und „Ehepaar“ als Hinweis auf den Auftraggeber; gesperrt, wenn im Satz Firma, Unternehmen, GmbH, Betrieb, Kanzlei, Agentur, Verein oder „privat versichert“ steht.
- `app/verwerter_nummer.json`: „Bandleader“ → typischer Verwerter mit R-31 (Fundstelle KSK-Info 04, Abschn. 2d; Auslegung der KSK, kein Gesetz). Auftraggeber-Zeile nur ausdrücklich „Ich bin Bandleader“.
- `app/pflichtangaben.py`: Übungsleiterpauschale auch mit genanntem Gesamtbetrag.
- `app/zuordnung.py::ergaenze_taetigkeit`: bei einer einzigen Position gilt die Einordnung aus Bezeichnung + Leistung + Text, wenn sie laut Excel Vorrang hat **und** das Modell unabhängig dasselbe sagt.
- Tests mit den echten Modellantworten: `tests/app/test_nachgefragt_live.py`, `tests/app/daten_nachgefragt_live_1410.json`.

## Live nachgemessen (je 6 Läufe, Stand 5dd83af)

| Fall | vorher | nachher | Rest |
|---|---|---|---|
| P-02 | 0/6 | 5/6 | 1× Grenzfall: das Modell ordnete die Leistung anders ein als der Text – dann bleibt es bewusst beim Grenzfall |
| P-14 | 0/6 | 5/6 | 1× Rückfrage nach der Leistung: das Modell nannte keine, und „Bandmitglieder“ allein erkennt die Excel nicht als Musik |
| P-20a | 0/6 | 6/6 | – |
| P-40 | 0/6 | 6/6 | – |

## Fragen an den Steuerberater (neu)

1. **P-18a / B-06:** Musikverein mit 15 Schülern: Der Kern fragt nach (R-53/R-54: Schülerzahl allein entscheidet nicht), der Testfall erwartet „nicht abgabepflichtig (bis 20 Schüler keine Musikschule anzunehmen)“. Was gilt?
2. **P-09:** Gilt „bezahlte selbständige Künstler“ bei Veranstaltungen ohne nähere Angabe der Leistung als künstlerische Leistung (Begriff „Künstler“ in der Excel)?

## Nächste Schritte (je ein eigener Schritt)

1. **Musikvereine:** R-57 (vereinseigene Chorleiter/Dirigenten bleiben außer Betracht) und R-17/R-30 in den Kern, dann Vereine mit Konzerten als Veranstalter erkennen (P-16, P-17).
2. **Grundsatzfrage ohne Betrag:** Vertretung (`kern.vertreter`, R-33/R-78) und Nachweismakler (R-35) ohne Betrag beantworten (P-36, P-37).

## Gesamtlauf danach (5dd83af)

**76 richtig / 12 nachgefragt / 0 falsch / 0 Fehler** von 88 (vorher 71 / 17 / 0 / 0). Besser: P-02, P-14, P-20a, P-31, P-40; nichts schlechter.

## Nachtrag 14.10.2026 abends: Musikvereine und Grundsatzfragen behoben

- P-16, P-17 (Musikvereine, R-30/R-57; KSK-Info 12 Abschn. 4): live je 6/6.
- P-36 (Vertretung, R-33) und P-37 (Nachweismakler, R-35): offline je 6/6 echte Modellantworten; im Gesamtlauf richtig.
- **Gesamtlauf b4de425: 80 richtig / 8 nachgefragt / 0 falsch / 0 Fehler.** Noch nachgefragt: P-09, P-11, P-13, P-18a, S-10, S-16, S-20, F3 – alle bewusst vorsichtig oder Frage an den Steuerberater (siehe Tabelle oben).
