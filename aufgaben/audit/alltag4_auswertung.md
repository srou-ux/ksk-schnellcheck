# Alltagsfälle F1–F4 (Testbelege des Nutzers, 11.10.2026) – Auswertung

Grundlage: `ksk-alltagsf_lle-4-testbelege-mit-soll-bewertung.pdf` (erfundene Belege). Katalog: `aufgaben/audit/testfall_alltag_4.json`. Die Fragen geben die Belege wörtlich wieder, auch die Rechenfehler der Testdatei. Soll-Werte aus der Testdatei, **nicht vom Steuerberater geprüft**. Neu im Lauf: Rückfragen werden gezählt (`max_rueckfragen`). Mehr Rückfragen als nötig ergeben „NACHGEFRAGT“, nicht „FALSCH“.

Modell `mistral-large-latest`, temperature 0. Workflow „Testkatalog“ (Eingaben: Katalog, Kurzname).

## Ergebnis

| Fall | Soll | Vorher (Stand `7487b18`) | Nachher (Stand `5588d4b`) |
|---|---|---|---|
| F1 Werbefotografie | A, 121,03 €, keine Rückfrage | Grenzfall (98,98 € / 121,03 €), 1 Rückfrage | **A, 121,03 €, keine Rückfrage** |
| F2 Journalist/Verlag | A, 85,75 €, keine Rückfrage | Formfehler des Modells (feste Rückfrage) | **A, 85,75 €, keine Rückfrage** |
| F3 Agentur-Mischrechnung | N, BG 0 (bedingt), Agentur-Ebene nur Hinweis | **FALSCH: A, 1.220,10 €** (GbR als Zahlungsempfänger) | N, Hinweis auf die Agentur-Ebene; **1 Rückfrage** (Art des Auftraggebers) |
| F4 Brautpaar | N, keine Schwellenwarnung | Sackgasse (kein Knopf „Privatperson“) | **N, keine Rückfrage, keine Schwelle** |

Zum Vergleich hat Mistral allein (ohne SaaS) im ersten Lauf 1 richtig / 2 falsch / 1 Fehler. F3 war auch dort falsch.

Kontrollläufe nach den Änderungen (live):
- Prüfkatalog (52 Fälle): 33 richtig / 19 nachgefragt / **0 falsch / 0 Fehler**. Ein Zwischenlauf hatte 1 FALSCH (P-20b, Übungsleiterpauschale übergangen); das ist behoben (`94cba66`).
- Testfall 20 Positionen: 18 / 3 / 0 / 0 (vorher 17 / 4 / 0 / 0).

## Ursachen und Änderungen

1. **F4: kein Auftraggeber „Privatperson“.** Neue Art des Auftraggebers `privat` (R-40, R-133), Knopf „Privatperson (kein Unternehmen)“, Textbaustein TB-25. Erkannt wird sie nur, wenn ein Satz eine Privatperson als Auftraggeber nennt (`app/privat_begriffe.json`). „Privatperson“ allein reicht nicht, weil so auch Auftragnehmer beschrieben werden. Ein unbelegter Modellwert wird verworfen.
2. **F3: Zahlungsempfänger falsch.** Eine ausdrücklich beschriftete Zeile „Rechnungsteller: …“ bestimmt die Rechtsform aller Positionen, deren Betrag in dieser Nachricht steht (R-45, R-177, R-216). Nennt der Text eine Vertretung des Künstlers, wird bei einer Gesellschaft nichts gesetzt (R-33). Die Antwort weist auf die eigene Prüfung bei der Agentur hin (TB-26, R-219), ohne Zahl. Die Faktenbestätigung zeigt „Rechnungsteller (an ihn wird gezahlt)“.
3. **F1: „Nutzungsrechte“ ohne Einordnung.** Neue Zeile T-68 „Nutzungsrechte, Lizenz, Buy-out“ (Grenzfall; derselbe Künstler: zählt mit, R-41, R-174, R-189). Vorrang 3: Eine konkrete Tätigkeit im selben Text (z. B. Fotos) geht vor. „Für ihre Image-Kampagne“ gilt als Eigenwerbung.
4. **F2:**
   - Neue Zeile T-69 „Recherche und Vorarbeiten“ (R-41, R-42).
   - „Freier Journalist“ wird als natürliche Person erkannt.
   - Die Reisekosten-Rolle gilt nur mit Nachweis und nie für eine Pauschale (R-47).
   - Eine bloße Zählzahl in `positionen`, die im Text nicht als Betrag steht, wird verworfen. Steht sie dort als Betrag, gibt es wie bisher einen zweiten Versuch.
5. **Jahr aus den Rechnungsdaten.** Haben alle Daten im Text dasselbe Jahr und kommt keine andere Jahreszahl vor, wird dieses Jahr übernommen. Die Faktenbestätigung kennzeichnet es: „aus den Daten auf der Rechnung abgeleitet – bitte prüfen, in welchem Jahr gezahlt wurde“.
6. **Nebenbefund (Grundregel 10):** KSK-Auslegungen mit einer Gruppe wie „Privat“ oder „Bemessungsgrundlage“ erschienen in der Antwort als „**Norm:**“. Die Ebene richtet sich jetzt zusätzlich nach dem Vorbehalt der Regel („Auslegung der KSK … kein Gesetz“).
7. **P-20b (Zwischenlauf):** Das Modell ordnete eine ausdrücklich bestätigte Übungsleiterpauschale als normale Bewertung ein. Eine genau einmal genannte, nicht verneinte Pauschale setzt jetzt die Anfrageart (`app/pauschale_begriffe.json`).

Tests: `tests/app/test_alltagsfaelle_f1_f4.py` (27 Tests, offline mit nachgebildeten Modellantworten). Excel: T-68, T-69, TB-25, TB-26 (alles Entwurf). Die Prüfliste für den Steuerberater ist neu erzeugt.

## Offen / nicht gelöst

- **F3, eine Rückfrage bleibt:** Ob die VitaWelt Eigenwerbung betreibt, steht nicht ausdrücklich im Beleg („Versicherungsunternehmen mit Marketing“). Das System rät die Art des Auftraggebers nicht. Das Ergebnis hängt davon ab: Ein typischer Verwerter wäre auch mit 0 € dem Grunde nach abgabepflichtig.
- **Zahlungsjahr:** Das abgeleitete Jahr ist das Jahr der Rechnungsdaten, nicht sicher das Jahr der Zahlung. Deshalb steht es gekennzeichnet in der Faktenbestätigung.
- **Fehler in der Testdatei:**
  - F3: USt 19 % von 34.780 € sind 6.608,20 €, nicht 660,82 €; der Rechnungsbetrag stimmt dann auch nicht.
  - F4: 1.650 + 420 = 2.070 €, nicht 2.075 €.
  - Das System rechnet mit den Positionen. Eine Plausibilitätswarnung zur Nettosumme gibt es hier nicht.
- **Fund, nicht geändert:** Bei der Übungsleiterpauschale nimmt `app/router.py` eine fehlende Bestätigung als „bestätigt“ an (`pauschale_bestaetigung … else True`). Siehe `aufgaben/FUNDE_Chatbot.md`.
- Alle neuen Zeilen und Bausteine sind „Entwurf – vom Steuerberater zu prüfen“.
