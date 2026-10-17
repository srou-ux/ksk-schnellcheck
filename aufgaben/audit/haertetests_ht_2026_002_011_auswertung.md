# Auswertung Härtetest-Serie HT-2026-002 bis 011 (14./15.10.2026)

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Testdaten. Katalog: `aufgaben/audit/haertetests_ht_2026_002_011.json` (eigener Katalog, **nicht** im Testarchiv: Die Soll-Werte sind Entwurf; die korrigierten Soll-Lösungen des Nutzers stammen aus einer KI-Fachprüfung, nicht vom Steuerberater).

Messung: Workflow „Modellfehler suchen“, je Fall 6 Läufe, Fakten-Protokoll an, Mistral EU (`mistral-large-latest`). „mit“ = SaaS mit Modell, „ohne“ = Vergleich ohne die festen Prüfungen.

## Ergebnis

| Fall | Thema | vorher (38641137620, Stand c361b56) | nachher (38644579629, Stand d4ff941) |
|---|---|---|---|
| HT-002 | zwei Zahlungsjahre, Reisekosten | 6 FALSCH | 3 RICHTIG, 3 FEHLER |
| HT-003 | Kulturverein, drei Konzerte | 6 RICHTIG | 6 RICHTIG |
| HT-004 | Direktzahlung, Gutschrift, Provision | 6 RICHTIG | 6 RICHTIG |
| HT-005 | GBP, USD in zwei Teilen, unbezahlt | 4 RICHTIG, 2 FEHLER | 3 RICHTIG, 3 FEHLER |
| HT-006 | drei Jahre, Grenzen | 6 RICHTIG | 6 RICHTIG |
| HT-007 | Musikverein, 15 Schüler | 6 RICHTIG | 6 RICHTIG |
| HT-008 | Einzelunternehmer → UG | 2 RICHTIG, 4 FEHLER | 1 RICHTIG, 5 FEHLER |
| HT-009 | Gutschein, PlayStation, Student | 6 FALSCH (altes Soll) | 5 RICHTIG, 1 FEHLER |
| HT-010 | 2019–2022, Verjährung | 6 RICHTIG | 6 RICHTIG |
| HT-011 | Prompt-Injection | 6 FALSCH | 6 RICHTIG |

**FALSCH: 18 → 0.** FEHLER: 6 → 12. FEHLER heißt hier immer: das Modell lieferte kaputtes JSON („Antwort konnte nicht verarbeitet werden“), auch nach dem zweiten Versuch. Das System hat dann nichts gerechnet. Das ist sicher, aber für den Nutzer schlecht. Ursache siehe unten.

„RICHTIG“ bei HT-002/006/008/010 heißt: Das System fragt nach, statt mehrere Jahre zusammenzuzählen. Bei HT-009 heißt es: Gutschein und Student zählen (R-41, R-174, R-26) → 2.050 € × 4,9 % = 100,45 €.

## Was geändert wurde (alles deterministisch, mit Fundstelle)

1. **Rechtsform aus der Selbstbeschreibung** (`app/rechtsform_erkennung.py`): „wir sind ein Verlag (GmbH)“ ist die eigene Seite, nicht der Autor (HT-011: vorher 5× „nicht abgabepflichtig“).
2. **Mehrere Zahlungsjahre** (`app/zahlungsjahr_begriffe.json`, `zuordnung.markiere_mehrere_zahlungsjahre`): Zahlungsdaten (Zahlwort davor/danach), Aufzählungen „2024: …“ und Sätze mit Jahr, Zahlverb und Betrag. Bei zwei oder mehr Jahren eine Rückfrage: Die Abgabe gilt je Kalenderjahr der Zahlung (KSVG § 25 Abs. 1, R-20). Ein Rechnungsdatum zählt nicht (HT-001 bleibt bei 2026).
3. **Rechtsformwechsel** (`app/rechtsformwechsel_begriffe.json`): Rückfrage, Zahlungen je Unternehmer getrennt eingeben.
4. **Offene Beträge mit Grund** (`app/zahlungsweg_begriffe.json`, Feld `Position.offen_grund`): Durchleitung, private Zahlung/Erstattung offen, noch nicht bezahlt, Gutschrift, keine Zahlung an den Künstler genannt, Vermittlungsprovision. Der nächste Begriff am Betrag gilt. Bestätigung und Ergebnis zeigen den Grund.
5. **Injection als „Rechtsprechungsfrage“** (`zuordnung.absichere_anfrageart`): Nennt der Text eine Zahlung, die das Modell als Position erkannt hat, wird bewertet (HT-011, 1 von 6).
6. **Zahlungsjahr vor Rechnungsjahr** (`zuordnung.jahr_aus_rechnungsdaten`, HT-085 aus der Fehlerquellen-Serie): Genau ein Zahlungsjahr im Text gilt, auch gegen ein Jahr, das nur im Rechnungsdatum steht. Es ist als „bitte prüfen“ gekennzeichnet.
7. **Bewusst NICHT gebaut:** Sachleistungen und Studenten als „offen“ markieren. Sie zählen nach R-41, R-174 und R-26 (Fachprüfung des Nutzers bestätigt das).

Tests mit den echten Modellantworten: `tests/app/test_haertetests_002_011.py`, `tests/app/daten_haertetests_002_011.json` (Lauf 38641137620, unverändert).

## FEHLER: kaputtes Modell-JSON

Lückenprotokoll (Lauf 38644579629):
- HT-008 (11×), HT-005 (5×), HT-004 (1×): „kein gültiges JSON: Expecting value: line 6–11 column 5“.
- HT-002 (5×), HT-007 (4×), HT-009 (1×): „positionen enthält Einträge, die keine Objekte sind“.
- 1× 429 (Ratenbegrenzung).

Die Fehlermeldung nannte bisher nicht die Stelle. Seit 48d9897 schreibt das System den Ausschnitt um die Fehlerstelle ins Protokoll. Darin werden alle Wörter außer Schema-Feldnamen zu „x“, es stehen also keine Inhalte darin. Bei Einträgen, die keine Objekte sind, stehen nur Typ und Länge im Protokoll. Mit dem nächsten Lauf lässt sich die Ursache gezielt beheben. Vorher repariere ich nichts blind: Das System soll das JSON des Modells nie raten.

## Abweichungen vom ersten Soll-Entwurf (Fassung 1), jetzt Fassung 2

| Fall | Fassung 1 | Fassung 2 (korrigierte Soll-Lösungen) | Grund |
|---|---|---|---|
| HT-002 | 2020 mit 5,0 % | 2020 4,2 %; Reisekosten nicht automatisch; 63,00 € oder 68,04 € | Register; R-47, KSK-Info 10 |
| HT-004 | auch N (0 €) zulässig | kein festes Null-Soll | § 25 Abs. 1, 3 KSVG (Drittzahlung, Vertretung) |
| HT-009 | nur G/R | A zulässig (100,45 € bei allen drei) | R-41, R-174, R-26 |
| HT-010 | – | Verjährung § 31 KSVG i. V. m. § 25 SGB IV (R-87); 3.990 € | R-87 |

## Fragen an den Steuerberater (Nachtrag 1 zur Prüfliste 2)

`regelwerk/Pruefliste_2_Nachtrag_1_Entwurf.xlsx`, darin Q-26 bis Q-31 aus dieser Serie: e. V. als Empfänger, unbezahlte Rechnung, Gutschrift, Rundung und Meldung in vollen Euro, Zusatzgeschenk, Provision an den Manager.

## Noch offen

- Mehrere Jahre in **einer** Antwort rechnen, statt nachzufragen (HT-082/083 erwarten das). Dafür müsste jede Position ihr Zahlungsjahr tragen. Das ist ein eigener Schritt.
- HT-005: Zwei USD-Teilzahlungen einer Rechnung zuordnen; heute fragt das System nach (sicher).
- Kaputtes Modell-JSON (siehe oben).
