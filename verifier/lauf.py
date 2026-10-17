"""Einstieg der Gegenrechnung im eigenen Prozess (gestartet von app/sandbox.py mit `python -I`).

Ein- und Ausgabe nur JSON über stdin/stdout. Ablauf:
1. Anfrage lesen, Speicher- und CPU-Grenze setzen (Linux: `resource`; unter Windows gibt es das Modul nicht, dort gilt
   das Zeitlimit des Elternprozesses als Mindestschutz).
2. Regelregister laden (die einzige Datei, die gelesen wird).
3. Wächter einschalten (`sys.addaudithook`): ab jetzt kein Öffnen von Dateien, kein Netz, keine neuen Prozesse, kein
   Nachladen von Modulen, kein exec/compile. Jeder Versuch beendet die Gegenrechnung mit Fehler.
4. Jeden Aufruf nachrechnen, Ergebnis ausgeben.

Das ist ein Schutz vor Fehlern und ungewolltem Verhalten, kein vollständiger Sicherheitsrahmen wie ein Container
(siehe app/README.md, Abschnitt Gegenrechnung)."""
from __future__ import annotations

import json
import sys
import time
from decimal import Context, Decimal, Inexact
from fractions import Fraction
from pathlib import Path

# python -I setzt weder das Skript- noch das Arbeitsverzeichnis in den Suchpfad: nur der Projektstamm, damit das Paket
# `verifier` gefunden wird. `kern` und `app` sperrt der Wächter (und ein statischer Test).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import verifier  # noqa: E402
from verifier import rechnung, register_pruefung  # noqa: E402
from verifier.register import Register  # noqa: E402

_GESPERRT_PRAEFIX = ("socket.", "subprocess.", "os.system", "os.exec", "os.spawn", "os.posix_spawn", "os.fork",
                     "os.kill", "os.remove", "os.unlink", "os.rename", "os.rmdir", "os.mkdir", "os.chmod", "os.chdir",
                     "os.truncate", "shutil.", "ctypes.", "urllib.", "http.", "ftplib.", "smtplib.", "webbrowser.",
                     "winreg.", "msvcrt.")
_GESPERRT = {"open", "exec", "compile", "import", "builtins.input", "code.__new__", "marshal.loads", "pickle.find_class"}


class Gesperrt(RuntimeError):
    pass


def _waechter(ereignis: str, args) -> None:
    if ereignis in _GESPERRT or ereignis.startswith(_GESPERRT_PRAEFIX):
        raise Gesperrt(f"gesperrt in der Gegenrechnung: {ereignis}")


def _grenzen(speicher_bytes, cpu_s) -> None:
    try:
        import resource
    except ImportError:  # Windows
        return
    if speicher_bytes:
        resource.setrlimit(resource.RLIMIT_AS, (int(speicher_bytes), int(speicher_bytes)))
    if cpu_s:
        resource.setrlimit(resource.RLIMIT_CPU, (int(cpu_s), int(cpu_s)))


def _ein(x):
    """JSON -> Python: {'$d': '1.5'} wird ein exakter Bruch."""
    if isinstance(x, dict):
        if set(x) == {"$d"}:
            return Fraction(x["$d"])
        return {k: _ein(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_ein(v) for v in x]
    return x


def dezimaltext(x: Fraction) -> str | None:
    """Bruch als exakter Dezimaltext; None, wenn er nicht abbricht (dann gibt es keine exakte Dezimalzahl).
    Die Genauigkeit reicht immer für einen abbrechenden Bruch (Stellen des Zählers plus Bitlänge des Nenners)."""
    ctx = Context(prec=len(str(abs(x.numerator))) + x.denominator.bit_length() + 1, traps=[Inexact])
    try:
        return format(ctx.divide(Decimal(x.numerator), Decimal(x.denominator)), "f")
    except Inexact:
        return None


def _aus(x):
    if isinstance(x, Fraction):
        t = dezimaltext(x)
        return {"$d": t} if t is not None else {"$bruch": f"{x.numerator}/{x.denominator}"}
    if isinstance(x, dict):
        return {k: _aus(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_aus(v) for v in x]
    return x


def bearbeite(anfrage: dict, register: Register) -> dict:
    if anfrage.get("art") == "register":
        # Registerprüfung vor einer Freigabe (python -m verifier.pruefe_register); Spannen kommen mit der Anfrage.
        return {"ok": True, "name": verifier.NAME, "version": verifier.VERSION,
                "befunde": register_pruefung.pruefe(register.daten, anfrage["plausibilitaet"])}
    ergebnisse = []
    for aufruf in anfrage.get("aufrufe", []):
        name = aufruf["name"]
        if name not in rechnung.AUFRUFE:
            ergebnisse.append({"nicht_abgedeckt": name})
            continue
        ergebnisse.append(rechnung.rechne(register, name, _ein(aufruf.get("args", [])), _ein(aufruf.get("kwargs", {}))))
    return {"ok": True, "name": verifier.NAME, "version": verifier.VERSION, "ergebnisse": _aus(ergebnisse),
            "register": register.protokoll()}


def main() -> int:
    beginn = time.perf_counter_ns()
    try:
        anfrage = json.loads(sys.stdin.read())
        _grenzen(anfrage.get("speicher_bytes"), anfrage.get("cpu_s"))
        register = Register.lade()
        sys.addaudithook(_waechter)
        antwort = bearbeite(anfrage, register)
    except BaseException as fehler:  # noqa: BLE001 -- jeder Fehler ist "Prüfung fehlgeschlagen", nie "bestätigt"
        antwort = {"ok": False, "fehler": f"{type(fehler).__name__}: {fehler}"}
    antwort["dauer_ns"] = time.perf_counter_ns() - beginn
    sys.stdout.write(json.dumps(antwort, ensure_ascii=False))
    sys.stdout.flush()
    return 0 if antwort.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
