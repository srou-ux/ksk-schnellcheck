"""Führt ALLE Prüfungen des Projekts nacheinander aus und meldet am Ende klar: ALLES GRÜN oder FEHLER.
Aufruf aus dem Projektstamm (Windows, Linux, Mac):  python scripts/pruefe_alles.py
Optional:  python scripts/pruefe_alles.py --ohne-app   (überspringt die Chatbot-Tests, falls fastapi nicht installiert ist)
Jede KI und jeder Mensch nutzt diesen einen Befehl als Erfolgskriterium nach einer Änderung."""
import subprocess, sys, pathlib

W = pathlib.Path(__file__).resolve().parent.parent
PY = sys.executable
SCHRITTE = [
    ("Regelwerk formal (IDs, Pflichtfelder, Quellen, Tests)", [PY, "tests/pruefe_regelwerk.py"]),
    ("Quellenbestand (Index, Dateien)", [PY, "tests/pruefe_quellen.py"]),
    ("Quellen unverändert (Prüfsummen, nur ergänzen)", [PY, "scripts/pruefsummen.py", "--pruefen"]),
    ("parameter.json passt zur Excel", [PY, "kern/erzeuge_parameter.py", "--pruefen"]),
    ("Kern-Tests (inkl. Regelregister, Wächter gegen Festwerte)", [PY, "tests/test_kern.py"]),
    ("Testfälle gegen den Kern", [PY, "tests/lauf_testfaelle.py"]),
    ("Testarchiv aktuell (alle Chatbot-Testfälle mit Soll, nur ergänzen)", [PY, "scripts/erzeuge_testarchiv.py", "--pruefen"]),
]
SCHNELLCHECK = ("Schnellcheck (ohne KI)", [PY, "-m", "unittest", "discover", "-s", "tests/schnellcheck", "-t", "."])
APP = ("Chatbot-Tests", [PY, "-m", "unittest", "discover", "-s", "tests/app"])
OPTIONAL = [  # nur wenn vorhanden (entstehen in späteren Teilen)
    ("Gegenrechnung (verifier)", "verifier", [PY, "-m", "unittest", "discover", "-s", "tests/verifier"]),
    ("Regelregister formal (Gegenrechnung, eigener Prozess)", "verifier", [PY, "-m", "verifier.pruefe_register", "--nur-register"]),
]

def lauf(name, cmd):
    print(f"\n=== {name}\n$ {' '.join(cmd[1:])}")
    r = subprocess.run(cmd, cwd=W, capture_output=True, text=True)
    ende = (r.stdout + r.stderr).strip().splitlines()[-6:]
    print("\n".join(ende))
    ok = r.returncode == 0
    print("-> OK" if ok else "-> FEHLER")
    return ok

if __name__ == "__main__":
    ergebnisse = [(n, lauf(n, c)) for n, c in SCHRITTE]
    ergebnisse.append((SCHNELLCHECK[0], lauf(*SCHNELLCHECK)))
    if "--ohne-app" not in sys.argv:
        ergebnisse.append((APP[0], lauf(*APP)))
    for n, pfad, c in OPTIONAL:
        if (W / pfad).exists():
            ergebnisse.append((n, lauf(n, c)))
    print("\n" + "=" * 60)
    for n, ok in ergebnisse:
        print(("[OK]     " if ok else "[FEHLER] ") + n)
    if all(ok for _, ok in ergebnisse):
        print("\nALLES GRÜN."); sys.exit(0)
    print("\nFEHLER – nicht pushen, zuerst beheben."); sys.exit(1)
