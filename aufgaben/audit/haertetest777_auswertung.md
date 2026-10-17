# Härtetest RE-2026-777 „Kultursommer GmbH“ (Testbeleg des Nutzers, 11.10.2026) – Auswertung

Grundlage: `ksk-haertetest-RE-2026-777.pdf`, erfundene Daten. Die PDF ist technisch fehlerhaft (Füllfarbe ohne Werte, die Seiten erscheinen weiß); den Text habe ich direkt aus dem Datenstrom gelesen. Katalog: `aufgaben/audit/testfall_haertetest_777.json`. Modell `mistral-large-latest`.

## 1. Messung

| Stand | Ergebnis im SaaS |
|---|---|
| Vorher (Stand vor `5d74e16`, mit der Regel aus F3) | **Sackgasse**: Rückfrage „Zu einem Restbetrag fehlt der Rechnungsbetrag“. Das Vertretungs-Wort in Pos. 02 schaltete die Rechnungsteller-Regel für die **ganze** Rechnung ab. Pos. 01 (4.800 €, „im eigenen Namen der GmbH eingekauft“) stand damit als natürliche Person im Fall und wäre mitgezählt worden. Außerdem bildete das System selbst einen „Rest der Rechnung“ von 9.886 €. |
| Nachher (`497a26c`) | **Grenzfall → Steuerberater entscheidet**: ohne die unklaren Positionen 0,00 €, mit ihnen 343,98 € (7.020 € × 4,9 %). Pos. 01, 05, 06, 07, 08 gehen an die GmbH. Pos. 02, 03, 04 sind als „nicht im eigenen Namen der Rechnungstellerin (Vertrag prüfen)“ gekennzeichnet. Eine Rückfrage bleibt: die Art des Auftraggebers. |
| Mistral allein, ohne SaaS | Abgabepflichtig, Bemessungsgrundlage 11.800 €. Zitiert ein „BFH-Urteil vom 27.02.2020 (XI R 13/18) zu Durchleitungsfällen“, das nicht in der Quellenbasis steht und nicht prüfbar ist. |

Gegenprobe auf dem ganzen Testarchiv (77 Fälle, live, Stand `a2c078b`): vorher 52 / 25 / 0 / 0, nachher **55 / 22 / 0 / 0** (P-10, P-12, P-21 besser, keiner schlechter).

## 2. Die Soll-Bewertung der Testdatei ist nicht verlässlich

Die Datei sagt selbst: „ENTWURF (LLM-generiert) … Vor Aufnahme in die Regressionssuite: fachliche Prüfung“. Gegen die Quellen im Repo geprüft:

| Punkt | Soll der Testdatei | Quellen | Einschätzung |
|---|---|---|---|
| Kultursommer als Veranstalterin | § 24 Abs. 1, keine Drei-Veranstaltungen-Ausnahme | § 24 Abs. 1 S. 1 Nr. 3 KSVG, R-29, R-160 („sonstige Unternehmen, deren wesentlicher Zweck … Aufführung“) | **plausibel**, wenn das Festival der Unternehmenszweck ist. „Veranstalterin“ allein belegt das nicht sicher (Generalklausel wäre auch möglich), deshalb fragt das System nach. |
| Pos. 01, 05, 06, 07 | bei Kultursommer ausgeschlossen | R-45, R-216 (Zahlung an GmbH im eigenen Namen) | **einverstanden** |
| Pos. 02 Pianist | abgabepflichtig ist die **Panorama GmbH**, „wer das Entgelt zahlt“ | KSK-Info 27: maßgeblich ist die unmittelbare Vertragsbeziehung zum Künstler, auch wenn ein Vertreter beteiligt ist; § 25 Abs. 1 S. 2 KSVG (R-36, R-94): zahlt ein nicht abgabepflichtiger Dritter, gehört das Entgelt zum abgabepflichtigen Unternehmen, **für das** die Leistung erbracht wurde | **widerspricht den Quellen.** § 25 Abs. 1 S. 2 sagt das Gegenteil der Begründung. Nach Info 27 spricht viel für Kultursommer (Vertrag in ihrem Namen). Entscheidung: Steuerberater. |
| Pos. 03 Durchleitung | 1.100 € bei Kultursommer | KSK-Info 27 (direkter Vertrag) | **im Grundsatz einverstanden**. Aber: „Lichtdesign-Workshop“ ordnet die Tätigkeitsliste als „Workshop-Moderation, nicht künstlerisch“ ein (T-34). Ob ein Workshop einer Lichtkünstlerin künstlerische Lehre ist, ist offen (Prüfliste, neue Frage). |
| Pos. 04 Komponist | nur 2.720 € (Direktanteil) | R-38: zahlt der Auftraggeber für Rechnung des Künstlers eine Provision an einen Vermittler, gehört sie in voller Höhe dazu; R-39: Ausnahme, wenn der Vertreter selbst abgabepflichtig ist | **offen**: 2.720 € oder 3.200 €, je nachdem, ob Panorama selbst abgabepflichtig ist. Die Testdatei nennt selbst diesen Punkt als „am wenigsten gesichert“. |
| Pos. 08 und Jahreswechsel | Gutschrift in die Meldung 2025; Abgabesatz „nach Leistungsdatum, nicht Rechnungsdatum“ | § 25 Abs. 1 S. 1 KSVG: Entgelte, die „im Laufe eines Kalenderjahres … gezahlt“ werden | **widerspricht dem Gesetzeswortlaut**: maßgeblich ist das Jahr der **Zahlung**, nicht der Leistung. Wie eine Gutschrift für eine Zahlung aus dem Vorjahr zu melden ist, steht in keiner Quelle des Repos → „Nicht abgedeckt“, Steuerberater. |
| Soll-Bemessungsgrundlage | 3.820 € | aus den Zeilen oben | **nicht gesichert.** Je nach Entscheidung zu Pos. 02/04: 3.820 €, 7.020 € oder 7.500 € (Pos. 03 zusätzlich abhängig von der Einordnung des Workshops). |

Folge: Der Fall kommt **nicht** mit einem festen Betrag ins Testarchiv. Im Katalog ist nur die Ergebnisklasse geprüft (abgabepflichtig oder Grenzfall). Ein fester Betrag folgt erst, wenn der Nutzer oder Steuerberater Pos. 02, 04, 08 entschieden hat.

## 3. Geändert (nur, was die Quellen tragen)

1. **Rechnungsteller-Regel je Position statt je Rechnung** (`app/zuordnung.py::rechnungsteller_als_zahlungsempfaenger`, `app/rechnungsteller_begriffe.json`):
   - Die Rechnung wird in Abschnitte je Position geteilt; Summen- und Vermerkzeilen gehören zu keiner Position.
   - Nennt der Abschnitt einer Position Vertretung, Durchleitung, einen direkten Vertrag oder eine Direktzahlung, wird diese Position **nicht** der GmbH zugeordnet, sondern als `zahlungsweg_unklar` markiert. Das Ergebnis ist dann ein Grenzfall mit beiden Beträgen (KSK-Info 27, R-33, R-36, R-94, R-38, R-39).
   - Neuer Textbaustein TB-27.
   - Nennt die Rechnungsteller-Zeile selbst eine Vertretung, bleibt es wie bisher: Es wird nichts gesetzt.
2. **Kein erfundener „Rest der Rechnung“**: Ein Rest entsteht nur, wenn der Text einen enthaltenen Teilbetrag nennt („1.200 € … darin 300 €“). Ein vom Modell gesetztes `rest` ohne solche Angabe wird nicht beachtet.
3. **Einnahmeabsicht nur bei der Generalklausel**: Ein typischer Verwerter und Eigenwerbung werden nicht mehr danach gefragt. Der Kern brauchte sie dort nie.
4. Der Hinweis auf die Agentur-Ebene (TB-26) erscheint auch bei Veranstaltungen.

Tests: `tests/app/test_haertetest_777.py` (10).

## 4. Offen

- Entscheidungen zum Soll: Pos. 02, Pos. 04, Pos. 08/Zahlungsjahr, Workshop in Pos. 03 (siehe Tabelle).
- Eine Rückfrage bleibt: Ob „Veranstalterin eines Festival-Zyklus“ ein typischer Verwerter ist, entscheidet der Unternehmenszweck. Der Begriff allein reicht nicht.
- Negative Beträge (Gutschriften) werden wie andere Positionen behandelt. Eine eigene Regel mit Quelle fehlt.
- Fund (nicht geändert): Bei einem typischen Verwerter nennt die Antwort immer „KSVG § 24 Abs. 1 Satz 1 Nr. 7“ (Werbung für Dritte, R-07), auch bei einem Veranstalter (dort Nr. 3, R-29/R-160). Siehe `aufgaben/FUNDE_Chatbot.md`.
