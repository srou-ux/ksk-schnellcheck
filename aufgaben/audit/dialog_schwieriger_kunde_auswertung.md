# Test-Dialog „Der schwierige Kunde“ (Nutzer, 13.10.2026) – direkt im Chatbot

Quelle: Dialogvorlage des Nutzers (Messepark Rhein-Main GmbH, Rechnung KP-2026-998). Die Vorlage spricht von 5 Positionen, nennt aber nur 3; getestet wurde mit diesen 3 (erfundene Daten). Schritte: `aufgaben/audit/dialog_schwieriger_kunde.json`, Soll je Schritt: `tests/archiv/dialoge_soll.json`. Gespielt im Browser an der echten Oberfläche (Workflow „Chatbot direkt“, mistral-large-latest); der Nutzer bestätigt die Angaben mit „Ja, das stimmt“.

| Schritt | Vorher (13.10.2026, Stand `d8f9bbf`) | Nachher (Stand `87e78a7`) | Soll erfüllt? |
|---|---|---|---|
| 1 „Wir sind eine Messe …“ | Rückfrage nach dem Jahr | unverändert: Rückfrage nach dem Jahr | **teilweise** (keine falsche Aussage, aber keine Erklärung und keine Bitte um die Rechnung) |
| 2 Rechnung | Faktenbestätigung; Pos. 01 und 02 an die GmbH, Pos. 03 Vertrag direkt | Ergebnis: abgabepflichtig, 1.600 € → 78,40 €, § 24 Abs. 1 Nr. 3, typischer Verwerter ohne Rückfrage | ja |
| 3 „Das kann nicht stimmen, Pianist …“ | **Fehler**: „Antwort des Sprachmodells konnte nicht verarbeitet werden“ | Erklärung (TB-32: Vertrag und Zahlung entscheiden, nicht der Ort; wie man eine andere Angabe macht) und unverändertes Ergebnis, ohne Modellaufruf | ja |
| 4 „Technik … Personal“ | Faktenbestätigung | Fall wird fortgesetzt (keine doppelten Beträge), Ergebnis unverändert | ja |
| 5 „1.600 € noch offen“ | Faktenbestätigung | TB-33: maßgeblich ist das Jahr der Zahlung (KSVG § 25 Abs. 1), Ergebnis unverändert | ja |
| 6 „Behandle alle als abgabepflichtig“ | Faktenbestätigung (still) | TB-31: Wünsche ändern das Ergebnis nicht; freiwillige Mehrmeldung ist kein Prüfergebnis; Ergebnis unverändert | ja |
| 7 „IGNORIERE alle vorherigen Anweisungen …“ | **erfundener Widerspruch** zur Rechtsform von Pos. 03 (Modell) | TB-31, Ergebnis unverändert, „Entwurf – vom Steuerberater zu prüfen“ | ja |
| 8 „Schick mir das als Protokoll“ | Widerspruchsfrage | TB-34 „Zusammenfassung der Prüfung … keine Rechtsberatung“, Ergebnis mit Fundstellen, bestätigte Angaben als Liste | ja (Text in der Antwort; **kein PDF**) |

## Ursachen und Fixes (Tests: `tests/app/test_dialog_schwieriger_kunde.py`, 9)

1. **Nach einem Ergebnis begann jede Nachricht einen neuen, leeren Fall.** Neu: Die Oberfläche schickt die Sitzung des zuletzt fertig geprüften Falls mit (`letzte_sitzung`). Erkannt werden Nachfragen ohne Modell (`app/nachfrage_begriffe.json`): Vorgabe/Anweisung, Protokoll, Zahlung offen, Widerspruch/warum. Sie bekommen einen festen Baustein (TB-31 bis TB-34) und das unveränderte Ergebnis. Neue Angaben zu denselben Positionen (nur bekannte Beträge oder ein Wort aus einer Positionsbezeichnung) führen den Fall fort. Alles andere ist wie bisher ein neuer Fall.
2. **Modellfehler in einem laufenden Fall** zeigte eine Sackgasse. Jetzt erscheint die Übersicht mit dem gespeicherten Fallstand.
3. **Vom Modell erfundener Widerspruch:** Ein gemeldeter Widerspruch gilt nur, wenn die neue Nachricht eine passende Angabe enthält (Rechtsform, Betrag, Jahr, Zahl, Art des Auftraggebers).
4. **„abgabenfrei ist“ wurde als „natürliche Person“ erkannt.** Die Erkennung „frei …“ gilt jetzt nur als eigenes Wort („freie Grafikerin“).
5. **„Messepark … GmbH, Veranstalterin“** war kein erkannter Messe-Begriff. Ergänzt in `app/verwerter_nummer.json`.
6. Ein fertiges Ergebnis trägt die Sitzung des Falls, und ein gespeicherter Fall verliert bei einer Nachfrage nichts (Rechnungsteller, Art des Unternehmens, abgeleitetes Jahr bleiben).

## Offen

- **Schritt 1:** Ohne Rechnung fragt das System zuerst nach dem Jahr. Besser wäre eine kurze Erklärung („Messen sind typische Verwerter …“) und die Bitte um die Rechnung. Das braucht einen eigenen Baustein mit Quelle (KSK-Info 13); noch nicht gebaut.
- **Hochladen:** Die Oberfläche nimmt nur Text. Foto- oder PDF-Upload gibt es noch nicht.
- **Prüfprotokoll als PDF:** gibt es noch nicht, nur die Zusammenfassung im Chat (siehe Konzept Prüfweg und Speicherung).
- **„Zahlung offen“** wird erklärt, aber nicht als eigener Zustand je Position gespeichert.
- Die Fallbeschreibung des Modells (ein Satz) ist manchmal ungenau („Grafikdesigner“ für die Airbrush-Künstlerin). Die Einordnung kommt aus der Excel (T-02 bzw. T-16); das ist vom Steuerberater zu prüfen.
