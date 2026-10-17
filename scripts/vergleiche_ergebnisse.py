"""Zwei Testläufe vergleichen (z. B. altes und neues Sprachmodell), Fall für Fall.

  python scripts/vergleiche_ergebnisse.py tests/archiv/ergebnisse/ALT.csv tests/archiv/ergebnisse/NEU.csv

Zeigt, welche Fälle besser, schlechter oder gleich geworden sind. Rückgabewert 1, wenn der neue Lauf
einen Fall FALSCH oder FEHLER hat, der im alten Lauf nicht FALSCH oder FEHLER war -- dann ist das neue
Modell (noch) nicht einsetzbar. Rangfolge der Urteile: RICHTIG > NACHGEFRAGT > FEHLER > FALSCH.
FEHLER ist eine abgelehnte Antwort, FALSCH ein falsches Ergebnis. Läuft unter Windows ohne
Zusatzpakete."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

RANG = {"RICHTIG": 3, "NACHGEFRAGT": 2, "FEHLER": 1, "FALSCH": 0}
KURZ = {"aufgaben/audit/pruefkatalog.json": "pruefkatalog", "aufgaben/audit/testfall_20_positionen.json": "testfall20",
        "aufgaben/audit/testfall_alltag_4.json": "alltag4", "aufgaben/audit/testfall_alltag_999.json": "alltag999"}


def lies(pfad: str) -> tuple[dict[str, dict], str]:
    zeilen = {}
    modus = ""
    with open(pfad, encoding="utf-8", newline="") as datei:
        for z in csv.DictReader(datei):
            fall = z["fall"]
            if ":" not in fall:  # Lauf über einen Einzelkatalog: Archiv-ID bilden
                fall = f"{KURZ.get(z.get('katalog', ''), 'katalog')}:{fall}"
            zeilen[fall] = z
            modus = z.get("modus", modus)
    return zeilen, modus


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    alt, modus_alt = lies(argv[0])
    neu, modus_neu = lies(argv[1])
    gemeinsam = sorted(set(alt) & set(neu))
    besser, schlechter, gleich, neu_falsch = [], [], [], []
    for fall in gemeinsam:
        a, n = alt[fall]["urteil"], neu[fall]["urteil"]
        if RANG.get(n, -1) > RANG.get(a, -1):
            besser.append((fall, a, n))
        elif RANG.get(n, -1) < RANG.get(a, -1):
            schlechter.append((fall, a, n))
        else:
            gleich.append(fall)
        if n in ("FALSCH", "FEHLER") and a not in ("FALSCH", "FEHLER"):
            neu_falsch.append((fall, a, n))

    def zaehle(z: dict[str, dict]) -> str:
        werte = [z[f]["urteil"] for f in gemeinsam]
        return ", ".join(f"{u} {werte.count(u)}" for u in RANG)

    print(f"ALT: {Path(argv[0]).name} ({modus_alt})\n     {zaehle(alt)}")
    print(f"NEU: {Path(argv[1]).name} ({modus_neu})\n     {zaehle(neu)}")
    print(f"\nVerglichen: {len(gemeinsam)} Fälle; besser {len(besser)}, schlechter {len(schlechter)}, gleich {len(gleich)}")
    nur = sorted(set(alt) ^ set(neu))
    if nur:
        print(f"Nur in einem der Läufe (nicht verglichen): {len(nur)}")
    for titel, liste in (("Schlechter", schlechter), ("Besser", besser)):
        if liste:
            print(f"\n{titel}:")
            for fall, a, n in liste:
                print(f"  {fall:28} {a:12} -> {n}")
    if neu_falsch:
        print(f"\nNICHT EINSETZBAR: {len(neu_falsch)} Fall/Fälle neu FALSCH oder FEHLER.")
        return 1
    print("\nKein neuer FALSCH- oder FEHLER-Fall.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
