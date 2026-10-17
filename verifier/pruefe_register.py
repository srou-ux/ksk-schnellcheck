"""Registerprüfung vor einer Freigabe (Teil 1e, C.2). Aufruf (Windows und Linux, aus dem Projektstamm):

    python -m verifier.pruefe_register            Register prüfen, danach Kern-Tests, Testfälle und Gegenrechnung
    python -m verifier.pruefe_register --nur-register

Die Prüfung selbst läuft im eigenen Prozess (app/sandbox.py -> verifier/lauf.py, Art 'register'); die plausiblen
Spannen stehen in verifier/plausibilitaet.json. Danach laufen die Kern-Tests, die Testfälle gegen den Kern und die Tests
der Gegenrechnung mit den Werten der aktuellen kern/parameter.json. Ausgabe: Bericht für die Freigabe; Rückgabewert 1,
wenn ein FEHLER gefunden wurde oder ein Test scheitert.

Diese Datei ist nur der Startknopf (läuft nicht im Kindprozess); sie darf deshalb app/sandbox.py benutzen. Den Kern
importiert sie nicht."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
SPANNEN = Path(__file__).resolve().parent / "plausibilitaet.json"
TESTS = [
    ("Kern-Tests", [sys.executable, "tests/test_kern.py"]),
    ("Testfälle gegen den Kern", [sys.executable, "tests/lauf_testfaelle.py"]),
    ("Gegenrechnung (Übereinstimmung, Mutationen, Sandbox)",
     [sys.executable, "-m", "unittest", "discover", "-s", "tests/verifier", "-t", "."]),
]


def main(argv: list[str]) -> int:
    sys.path.insert(0, str(WURZEL))
    from app import sandbox

    antwort = sandbox.fuehre_aus({"art": "register", "plausibilitaet": json.loads(SPANNEN.read_text(encoding="utf-8"))})
    print("== Registerprüfung (Entwurf – vom Steuerberater zu prüfen) ==")
    if not antwort.get("ok"):
        print(f"FEHLER: Prüfung lief nicht durch: {antwort.get('fehler')}")
        return 1
    befunde = antwort["befunde"]
    for b in befunde:
        print(f"{b['art']}: {b['text']}")
    fehler = sum(1 for b in befunde if b["art"] == "FEHLER")
    print(f"-- {fehler} Fehler, {len(befunde) - fehler} Hinweise ({antwort['name']}, {antwort['version']})")
    ok = fehler == 0
    if "--nur-register" not in argv:
        for name, befehl in TESTS:
            r = subprocess.run(befehl, cwd=WURZEL, capture_output=True, text=True)
            letzte = (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
            print(f"{'[OK]    ' if r.returncode == 0 else '[FEHLER]'} {name}: {letzte[0]}")
            ok = ok and r.returncode == 0
    print("ERGEBNIS:", "keine Fehler – Freigabe durch den Steuerberater möglich" if ok else "FEHLER – nicht freigeben")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
