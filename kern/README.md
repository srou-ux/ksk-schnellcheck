# Regelkern v0 (Entwurf)

Deterministischer Rechenkern ohne Sprachmodell. Er prüft und berechnet nur, was im Regelkatalog belegt ist, und sagt sonst „Rückfrage nötig“ oder „Nicht abgedeckt“. Das System macht Vorschläge, der Steuerberater entscheidet.

- `rechnen.py` – Funktionen: Eigenwerbung/Schwelle je Jahr, typische Verwerter, Abgabe (Decimal), Netto ohne Umsatzsteuer, Zahlungsjahr, Verpflegung (8-Stunden-Grenze), Reisekosten ohne Nachweis, vervielfältigte Druckkosten, Vertreter, Musikverein.
- `parameter.json` – Schwellen und Abgabesätze, **erzeugt** aus `regelwerk/Regelkatalog_24_KSVG_Entwurf.xlsx` (`python kern/erzeuge_parameter.py`). Nicht von Hand ändern; `--pruefen` erkennt Abweichungen.
- Tests: `python tests/test_kern.py` (18 Tests) und `python tests/lauf_testfaelle.py`: führt die maschinenlesbaren Fälle aus `regelwerk/testfaelle_maschinenlesbar.json` gegen den Kern aus und gleicht jedes Ergebnis mit dem erwarteten Ergebnis in der Excel-Datei ab (aktuell 94 von 329 Testfällen). Nicht ausgeführte Fälle werden mitgezählt.
- Funktionen zusätzlich: Positionssummen (GmbH/KG/OHG, Nicht-Künstlerisches, Fahrtkosten, Gewinnzuweisung), Veranstaltungen, Vorauszahlung, Säumniszuschlag, Meldefrist, Aufbewahrung, Übungsleiter-/Ehrenamtspauschale, Kommission, Schätzung Ausland.

Bekannte Grenzen: Die Rundung der Abgabe ist nicht belegt; bei mehr als 2 Nachkommastellen gibt der Kern keine gerundete Zahl aus. Fassung A (bis 2022) ist nur für Eigenwerbung bis 450 € umgesetzt. Auslandsreisen, Übungsleiterpauschalen und die meisten der 236 Regeln sind noch nicht im Kern. Alles bleibt Entwurf, bis der Steuerberater freigibt.

Rechnungsanalyse v0: `analysiere_rechnung()` bewertet jede Position einer Rechnung (Rolle wird vorgegeben: Zahlung an Kapitalgesellschaft, Vertretung des Künstlers, Eigengeschäft der Agentur, Reisekosten, nicht künstlerisch). Sicher zählende und offene Beträge werden getrennt; offene Punkte werden zu Rückfragen. Beispielbeleg: `tests/belege/AT-2026-204_Agentur_und_Vertretung_fiktiv.pdf` (Tests H-01 bis H-05).

## Regelregister (Werte ändern ohne Code)
Alle Zahlen, Vergleichsoperatoren und Listen (Pauschalen, 40-€-/50-€-/150-€-Grenzen, Säumniszuschlag, Fristen, Schätzsatz,
Rechtsformen ohne Entgelt) stehen im Blatt **Regelregister** der Datei `regelwerk/Regelkatalog_24_KSVG_Entwurf.xlsx`
(Spalten: Schlüssel, Wert, Einheit, Operator, Gültig von/bis, Regel-ID, Fundstelle, Prüfstatus).
Ändert sich etwas: neue Zeile mit neuem „Gültig von“ anlegen (alte Zeile bekommt „Gültig bis“), Fundstelle eintragen,
Status „Entwurf – vom Steuerberater zu prüfen“, dann `python kern/erzeuge_parameter.py` und die Tests laufen lassen.
Es ist kein Eingriff in `rechnen.py` nötig. Fehlt ein Eintrag für ein Jahr, antwortet der Kern „Nicht abgedeckt“.
Nicht im Register (bleibt Gesetzeslogik): Fassung A/B-Unterscheidung, die 450-€-Regel der Fassung A. Ein Wächter-Test (`Wächter`) lässt im Kern nur die technischen Zahlen 100, 0.01, 12, 31 zu.
