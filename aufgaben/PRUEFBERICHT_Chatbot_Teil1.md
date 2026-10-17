# Unabhängige Prüfung Chatbot Teil 1b (Entwurf)

Methode: Das Sprachmodell wurde durch eine manipulierte FakeLLM ersetzt, die an eine sonst korrekte Antwort einen Fehler anhängt. Skript: `aufgaben/audit/gegenproben_teil1.py` (`python aufgaben/audit/gegenproben_teil1.py`).
Basis: 2026, Eigenwerbung, 1.500 € → Kern sagt „Abgabepflichtig", Antwort korrekt (Fall 00).

## Gefangen (Antwort-Kontrolle greift)
- 01 erfundener Betrag „999 €"
- 06 erfundenes Aktenzeichen „B 12 KR 99/23 R"
- 07 Aktenzeichen in anderer Schreibweise („12 R 77/22" → erkannt als „R 77/22")
- 08 erfundene Regel-ID „R-9999"

## NICHT gefangen (Befunde)
| Nr. | Fall | Ergebnis |
|---|---|---|
| B1 | Betrag als „999 Euro", „EUR 999", „999 EUR", „999,- €" | durchgelassen (nur Muster `… €` wird erkannt) |
| B2 | erfundener Paragraf „§ 99 KSVG" | durchgelassen (keine Prüfung auf Paragrafen) |
| B3 | erfundener Prozentsatz „7,5 %" | durchgelassen (keine Prüfung auf Prozentwerte) |
| B4 | falsche Fassung „Fassung A … 450 €" bei Jahr 2026 | durchgelassen (Fassung/Schwelle nicht gegen den Kern geprüft) |
| B5 | erfundenes Jahr „2031" in der Antwort | durchgelassen (Jahreszahlen nicht geprüft) |
| B6 | Pfad **Rückfrage** | Antwort-Kontrolle läuft gar nicht: „Die Abgabe beträgt 4711 €" wird ausgegeben |
| B7 | Pfad **Nicht abgedeckt** | keine Kontrolle: erfundener Betrag wird ausgegeben |
| B8 | Pfad **Rechtsprechungsfrage** | keine Kontrolle: erfundener Betrag und erfundenes Aktenzeichen werden ausgegeben |

Nicht prüfbar mit FakeLLM: Prompt-Injection gegen ein echtes Modell (Frage mit eingebautem Befehl) – nur mit Mistral-Schlüssel testbar; der FakeLLM folgt ihm nicht (Fall 30 ohne Wirkung). Die Verteidigung hängt also an der Antwort-Kontrolle, die darum lückenlos sein muss.

## Bewertung
Der Kern und die Hauptkette sind sauber. Die Antwort-Kontrolle ist aber nur im Hauptpfad aktiv und erkennt nur einen Teil der Fehlerarten. Die Zusage „jede Zahl und jede Fundstelle in der Antwort ist belegt" gilt noch nicht.
