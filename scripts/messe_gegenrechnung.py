"""Zeitmessung der Gegenrechnung (Teil 1e, E.3) für aufgaben/SANDBOX_Nachweis.md. Ohne Modellaufruf, nur erfundene
Zufallsfälle (fester Startwert). Je Fall ein eigener Prozess, wie im Betrieb.

Aufruf (Windows): python scripts/messe_gegenrechnung.py [Anzahl]"""
from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.verifier import zufall  # noqa: E402
from tests.verifier.hilfe import pruefe_aufrufe  # noqa: E402


def main() -> None:
    anzahl = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    faelle = zufall.faelle(anzahl, 15102026)
    gesamt, intern, abweichungen = [], [], 0
    for fall in faelle:
        beginn = time.perf_counter()
        p = pruefe_aufrufe([fall])
        gesamt.append((time.perf_counter() - beginn) * 1000)
        if p.protokoll.get("dauer_ms") is not None:
            intern.append(p.protokoll["dauer_ms"])
        abweichungen += p.status != "bestaetigt"
    print(f"Fälle: {anzahl} (je ein eigener Prozess), nicht bestätigt: {abweichungen}")
    print(f"Gegenrechnung gesamt (mit Prozessstart): Mittel {statistics.mean(gesamt):.1f} ms, "
          f"Median {statistics.median(gesamt):.1f} ms, Höchstwert {max(gesamt):.1f} ms")
    print(f"davon Rechnen im Kindprozess: Mittel {statistics.mean(intern):.2f} ms, Höchstwert {max(intern):.2f} ms")


if __name__ == "__main__":
    main()
