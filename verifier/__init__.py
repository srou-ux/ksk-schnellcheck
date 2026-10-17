"""Unabhängige Gegenrechnung (Chatbot Teil 1e, `aufgaben/PROMPT_ClaudeCode_Chatbot_1e_Pruefsandbox.md`).

Entwurf – vom Steuerberater zu prüfen. Dieses Paket rechnet jede Rechnung des Kerns ein zweites Mal nach, auf einem
eigenen Weg:
- Es importiert `kern` NIE (statischer Test: tests/verifier/test_sandbox.py). Wiederverwendung des Kern-Codes würde
  denselben Fehler zweimal bestätigen.
- Es liest nur Daten: das Regelregister (`kern/parameter.json`, erzeugt aus der Excel) und die Eingaben der
  Kern-Aufrufe. Das Ergebnis des Kerns sieht es nie.
- Es rechnet mit exakten Brüchen (`fractions.Fraction`) statt mit `Decimal`; Ausgabe als Dezimaltext.
- Es läuft im SaaS in einem eigenen Prozess (app/sandbox.py, Einstieg verifier/lauf.py).

Grenzen: Es bestätigt die RECHNUNG, nicht die Einordnung (Rechtsform, künstlerisch ja/nein) und nicht die fachliche
Richtigkeit einer Regel. Kern und Gegenrechnung lesen dieselbe Excel; ein falscher Wert dort fällt hier nicht auf."""

NAME = "Gegenrechnung verifier"
VERSION = "v1 (Stand 15.10.2026)"
