"""Abgeschlossene Ausführung der Gegenrechnung (Chatbot Teil 1e, Abschnitt B).

- Eigener Python-Prozess: `python -I -B -S verifier/lauf.py` (isoliert: keine Umgebungsvariablen von Python, kein
  Benutzer-Paketordner, kein `site`, Skript- und Arbeitsverzeichnis nicht im Suchpfad; keine .pyc-Dateien schreiben).
- Bereinigte Umgebung (nur das, was Python zum Start braucht), eigenes leeres Arbeitsverzeichnis (Temp-Ordner).
- Ein- und Ausgabe nur JSON über stdin/stdout. Es läuft ausschließlich fest hinterlegter Code aus `verifier/`; das
  Sprachmodell schreibt und startet dort nie Code.
- Zeitlimit (Wanduhr, app/konfiguration.json); im Kindprozess zusätzlich Speicher- und CPU-Grenze (nur Linux/macOS)
  und ein Wächter, der Netz, Dateizugriffe, neue Prozesse und Nachladen von Code sperrt (verifier/lauf.py).
- Fehler, Zeitüberschreitung, Absturz, unlesbare Ausgabe: `ok` ist False -- nie 'bestätigt'.

Ehrlich: das schützt vor Fehlern und ungewolltem Verhalten, ist aber kein vollständiger Sicherheitsrahmen wie ein
Container. Für das Hosting ist ein Container ohne Netz auf einem EU-Server vorgesehen (app/README.md)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
LAUF = WURZEL / "verifier" / "lauf.py"
KONFIGURATION = Path(__file__).resolve().parent / "konfiguration.json"
_MB = 1024 * 1024


@lru_cache(maxsize=1)
def konfiguration() -> dict:
    return json.loads(KONFIGURATION.read_text(encoding="utf-8"))["gegenrechnung"]


def _umgebung() -> dict[str, str]:
    """Nur was der Interpreter zum Start braucht (Windows: SYSTEMROOT). Keine Schlüssel, keine Proxys."""
    env = {"PYTHONIOENCODING": "utf-8"}
    for name in ("SYSTEMROOT", "SystemRoot"):
        if name in os.environ:
            env[name] = os.environ[name]
    return env


def fuehre_aus(anfrage: dict, *, zeitlimit_s: float | None = None, lauf: Path | None = None) -> dict:
    """Startet die Gegenrechnung und liefert ihre JSON-Antwort. Bei jedem Problem: {'ok': False, 'fehler': ...}."""
    k = konfiguration()
    daten = dict(anfrage)
    daten.setdefault("speicher_bytes", int(k["speicher_mb"]) * _MB)
    daten.setdefault("cpu_s", k["cpu_s"])
    with tempfile.TemporaryDirectory(prefix="gegenrechnung_") as arbeitsordner:
        try:
            r = subprocess.run(
                [sys.executable, "-I", "-B", "-S", str(lauf or LAUF)],
                input=json.dumps(daten, ensure_ascii=False), capture_output=True, text=True, encoding="utf-8",
                timeout=zeitlimit_s if zeitlimit_s is not None else k["zeitlimit_s"], cwd=arbeitsordner,
                env=_umgebung(),
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "fehler": "Zeitüberschreitung der Gegenrechnung"}
        except OSError as fehler:
            return {"ok": False, "fehler": f"Gegenrechnung nicht startbar: {fehler}"}
    try:
        antwort = json.loads(r.stdout)
    except ValueError:
        return {"ok": False, "fehler": f"Gegenrechnung ohne gültige Antwort (Rückgabewert {r.returncode})"}
    if not isinstance(antwort, dict) or antwort.get("ok") is not True:
        fehler = antwort.get("fehler") if isinstance(antwort, dict) else None
        return {"ok": False, "fehler": fehler or f"Gegenrechnung fehlgeschlagen (Rückgabewert {r.returncode})"}
    return antwort
