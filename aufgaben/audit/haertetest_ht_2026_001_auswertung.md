# Härtetest HT-2026-001 „Die Agentur-Februar-Rechnung“ – Auswertung (14.10.2026)

Entwurf – vom Steuerberater zu prüfen. Erfundene Daten. Härtetest und Soll vom Nutzer; Katalog `aufgaben/audit/haertetest_ht_2026_001.json` (bewusst **nicht** im Testarchiv, bis Durchleitung und Erstattung fachlich bestätigt sind).
Messung: Workflow „Modellfehler suchen“ mit Katalog-Eingabe, je 6 Läufe (mistral-large-latest, mit und ohne Quellenabruf), Fakten-Protokoll.

## Ergebnis

| Stand | Läufe | Ergebnis |
|---|---|---|
| vorher (3e3b9a5) | 6 | 1× **FALSCH** (Bemessungsgrundlage 3.760 €, Abgabe 184,24 €: Band und Zauberer still mitgezählt), 5× Rückfrage nach der Rechtsform des Zauberers |
| nachher (b4de425) | 6 | **6× bestanden**: Grenzfall → Steuerberater entscheidet; sicherer Teil 2.210 € → **108,29 €**; Band (1.150 €) und Zauberer (400 €) als „Zahlungsweg offen“ ausgewiesen, Betrag mit ihnen ebenfalls genannt |

## Die 8 Fallen

| # | Falle | Verhalten |
|---|---|---|
| 1 | 2.400 USD, abgebucht 2.210 € | bestanden: nie umgerechnet; Bestätigung „2.210,00 € (gezahlter Euro-Betrag; angegeben 2.400 USD)“ |
| 2 | Rechnung 27.12.2025, Zahlung 09.01.2026 | bestanden: Jahr 2026 |
| 3 | Band: „nur vermittelt und das Geld durchgeleitet“ | **behoben**: Zahlungsweg offen, nie still mitgezählt (vorher mitgezählt) |
| 4 | GbR als Empfängerin | bestanden: zählt grundsätzlich mit (R-218), kein stilles „nicht abgabepflichtig“ |
| 5 | 1.200 € des Kunden an die Agentur | bestanden: legt das Modell sie als Position an, ist sie ebenfalls „Zahlungsweg offen“ |
| 6 | Zauberer, privat bezahlt, Erstattung offen | **behoben**: Zahlungsweg offen, keine Rückfrage-Schleife nach der Rechtsform |
| 7 | Werbeagentur = typischer Verwerter | bestanden: keine Schwelle, kein Eigenwerbungs-Vergleich |
| 8 | je Position prüfen | bestanden: Fotografie künstlerisch, Band und Zauberer getrennt ausgewiesen |

## Was geändert wurde

- `app/zuordnung.py::zahlungsweg_im_freitext` mit `app/zahlungsweg_begriffe.json`: Freitext **ohne** Rechnungsteller-Zeile (die Agentur fragt selbst). Zu jedem Euro-Betrag gehört der Text bis zum nächsten Euro-Betrag; nennt er Durchleitung oder eine offene Erstattung, wird die Position „Zahlungsweg unklar“. Nie „Vertrag direkt“: aus Sicht der durchleitenden Agentur zählt die Zahlung beim Kunden, aus Sicht des Kunden bei ihm selbst – das entscheidet der Mensch.
- `app/pflichtangaben.py`: keine Rechtsform-Frage für Positionen mit offenem Zahlungsweg (sie werden ohnehin nur als „falls zählend“ ausgewiesen).
- Tests mit allen 12 echten Modellantworten: `tests/app/test_nachgefragt_live.py` (Klassen ZahlungswegImFreitext, HaertetestHT2026001Echt), `tests/app/daten_haertetest_ht_2026_001.json`.

## Für den Steuerberater

1. **Durchleitung aus Sicht der Agentur** (Band, 1.150 €; Kunde hat 1.200 € überwiesen): Zählt das Entgelt beim Kunden (Vertrag Kunde–Band, KSK-Info 27, R-127)? Ist die Agentur hier nie abgabepflichtig?
2. **Private Zahlung des Managing Directors** (Zauberer, 400 €, Auftritt bei einer Firmenfeier des Kunden, Erstattung offen): Wann zählt das bei der Agentur?
3. **Textbaustein „Zahlungsweg offen“** sagt „ob und in welcher Höhe diese Beträge **beim Mandanten** zählen“. Fragt die Agentur selbst, passt „bei Ihnen“ besser. Wortlaut in der Excel (Blatt Textbausteine) prüfen.

## Grenzen

- Die Zuordnung „Text bis zum nächsten Euro-Betrag“ ist bewusst vorsichtig: steht ein Durchleitungs-Wort zwischen zwei Beträgen, werden im Zweifel beide offen – das ergibt einen Grenzfall, nie eine falsche Zahl.
- Dialog-Variante (Angaben verteilt über mehrere Nachrichten) noch nicht getestet – Ihr Angebot dazu nehme ich gern an.
