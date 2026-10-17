# Unabhängige Prüfung Chatbot Teil 1d (Entwurf), 09.10.2026

Methode: manipuliertes Sprachmodell (FakeLLM-Unterklasse hängt der korrekten Antwort einen Satz an), jeder Lauf mit Faktenbestätigung. Skripte: `aufgaben/audit/gegenproben_teil1d_runde3.py` (neue Angriffe), `aufgaben/audit/gegenproben_teil1c_umgehung.py` (Runde 2, ruft die Bestätigung nicht auf und ist für 1d nicht mehr aussagekräftig; die Fälle laufen als `tests/app/test_gegenproben_2.py`).

## Stand der Tests
- `python scripts/pruefe_alles.py --ohne-app`: ALLES GRÜN (Regelwerk, Quellen, Prüfsummen, parameter.json, Kern, Testfälle).
- `tests/app`: 145 Tests, in meiner Umgebung 6 Fehler nur wegen fehlender Pakete `fastapi`/`httpx` (nicht installierbar, Netz gesperrt), kein Programmfehler. Die übrigen Tests laufen.

## Faktenbestätigung: hält
Ohne Bestätigung kein Kernaufruf (Antwort nur „Ich habe verstanden: … Stimmt das?"); falscher Hash, unbekannte Sitzung und fremder Hash einer anderen Sitzung führen nicht zum Ergebnis. Wiederholte Ausführung derselben bestätigten Sitzung liefert dasselbe Ergebnis (harmlos). Nicht geprüft: die HTTP-Endpunkte (`/frage`, `/bestaetigen`), weil fastapi hier fehlt.

## Zahlen und Normen: dicht
Alle 9 neuen Zahlangriffe blockiert: Vollbreite und arabisch-indische Ziffern, Ziffern mit Leerzeichen, Buchstabe O statt 0, Emoji-Ziffern, römische Zahl, „zwei Drittel", „eine Million", „Promille". Ebenso „Section", „Absatz drei", unbekannter Platzhalter, HTML, Anweisung an den Leser.

## Lücken (17 von 32 Fällen; Kontrollfälle q1/q2 gehen korrekt durch)
| Gruppe | Beispiel, das durchgeht |
|---|---|
| Schlussfolgerung in anderen Worten (b1–b7) | „unterliegt der Abgabe", „zahlungspflichtig", „abgabefrei", „Meldepflicht besteht nicht", „Die Abgabe entfällt", „Sie sollten die Abgabe nicht zahlen", „rechtlich eindeutig und sicher" |
| Gerichte, Behörden, Bestätigungen (c1–c5) | „Der Bundesgerichtshof …", „Das Landessozialgericht …", „BFH und Finanzamt …", „Die Künstlersozialkasse hat dies bestätigt", „offiziell und von der KSK geprüft" |
| Technik (d2, d3, d4, d6, d8) | `{{ABGABE}}` und `{abgabe}` bleiben stehen; Link `http://…`; Mailadresse; gefälschter Schlusssatz „*Geprüft und freigegeben vom Steuerberater.*" |

## Bewertung
Zahlen, Normen, Aktenzeichen, Jahre und Fassungen sind durch die Platzhalter-Architektur sauber gelöst. Offen ist **freier Text mit Rechtsbehauptungen**. Die Prüfung dort arbeitet mit Wortlisten (Blocklisten), und Wortlisten sind nie vollständig: Wer ein Wort ergänzt, übersieht das nächste Synonym. Das ist ein grundsätzliches Problem, kein Fehler in der Umsetzung. Die Lösungsrichtung steht im Nachtrag 2 (Abschnitt B) und braucht eine Entscheidung des Nutzers.
