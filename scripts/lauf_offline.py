# -*- coding: utf-8 -*-
"""Korpus ohne Sprachmodell gegen den heutigen Kern.

Die alte Datei aufgaben/audit/korpus/lauf_offline.py lief über den Chat
(Router, Knöpfe, Faktenbestätigung). Der Chat ist seit dem 17.10.2026 entfernt.
Dieser Lauf nimmt die perfekten Fakten jedes Falls und ruft denselben Kernweg
auf, den die Rechnungsprüfung heute benutzt (app.bewertung._rufe_kern_auf).

Bewertung wie im alten Prüfkatalog: Klasse im Soll und passende Zahl = RICHTIG.
Rückfrage, Grenzfall oder fehlende Quelle statt eines sicheren Solls = NACHGEFRAGT.
Eine andere sichere Klasse oder eine andere Zahl = FALSCH.

Der Säumniszuschlag heißt in der Anzeige „Säumniszuschlag (Vorschlag)“, intern
bleibt er abgabepflichtig. So hat es der frühere Router vor der Bewertung umbenannt.

Aufruf (Windows): python scripts/lauf_offline.py
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys
from decimal import Decimal, InvalidOperation

WURZEL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL))

from app.bewertung import _rufe_kern_auf  # noqa: E402
from app.ergebnisklassen import RUECKFRAGE_NOETIG, SAEUMNISZUSCHLAG_BERECHNET  # noqa: E402
from app.pflichtangaben import euro_fragen  # noqa: E402
from app.schema import Fakten  # noqa: E402
from kern import rechnen as K  # noqa: E402

KORPUS = WURZEL / "aufgaben" / "audit" / "korpus_beispiele.json"
OFFEN = {"R", "G", "X"}


def kuerzel(klasse: str, tabelle: dict) -> str:
    for k, v in tabelle.items():
        if v == klasse:
            return k
    return klasse


def dezimal(wert) -> Decimal | None:
    try:
        return Decimal(str(wert))
    except (InvalidOperation, ValueError):
        return None


def bewerte(fall: dict, klasse: str, protokoll: dict, tabelle: dict) -> tuple[str, list[str]]:
    ist = kuerzel(klasse, tabelle)
    soll = fall["soll"]
    gruende: list[str] = []
    if ist in soll:
        for schluessel, erwartet in (fall.get("zahl") or {}).items():
            wert = protokoll.get(schluessel)
            if wert is None:
                continue
            if dezimal(wert) != Decimal(str(erwartet)):
                gruende.append(f"{schluessel}: Soll {erwartet}, Ist {wert}")
        return ("FALSCH" if gruende else "RICHTIG"), gruende
    if ist in OFFEN:
        return "NACHGEFRAGT", [f"Soll {'/'.join(soll)}, Ist {ist}"]
    return "FALSCH", [f"Soll {'/'.join(soll)}, Ist {ist} ({klasse})"]


def anzeige(fakten: Fakten, ergebnis) -> str:
    if fakten.anfrageart == "saeumniszuschlag" and ergebnis.klasse == K.ABGABEPFLICHTIG:
        return SAEUMNISZUSCHLAG_BERECHNET
    return ergebnis.klasse


def main() -> int:
    korpus = json.loads(KORPUS.read_text(encoding="utf-8"))
    tabelle = korpus["kuerzel"]
    zaehler: collections.Counter = collections.Counter()
    je_gruppe: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    abweichungen: list[str] = []
    for fall in korpus["faelle"]:
        familie = fall["gruppe"][:3]
        try:
            fakten = Fakten.model_validate(fall["fakten"])
            # Betrag nur in fremder Währung: die Prüfung fragt nach dem Euro-Betrag
            # und ruft den Kern nicht auf (app/pflichtangaben.py, Testfall L-23).
            if euro_fragen(fakten):
                klasse, protokoll = RUECKFRAGE_NOETIG, {}
            else:
                ergebnis = _rufe_kern_auf(fakten)
                klasse, protokoll = anzeige(fakten, ergebnis), ergebnis.protokoll or {}
            urteil, gruende = bewerte(fall, klasse, protokoll, tabelle)
        except Exception as fehler:  # noqa: BLE001 -- jeder Abbruch ist ein Befund
            urteil, gruende = "FEHLER", [f"{type(fehler).__name__}: {str(fehler)[:240]}"]
        zaehler[urteil] += 1
        je_gruppe[familie][urteil] += 1
        if urteil != "RICHTIG":
            abweichungen.append(f"{fall['id']} {familie} {urteil}: {'; '.join(gruende)}")
    gesamt = sum(zaehler.values())
    print(f"Faelle {gesamt}: RICHTIG {zaehler['RICHTIG']}, NACHGEFRAGT {zaehler['NACHGEFRAGT']}, "
          f"FALSCH {zaehler['FALSCH']}, FEHLER {zaehler['FEHLER']}")
    for familie in sorted(je_gruppe):
        z = je_gruppe[familie]
        print(f"  {familie}: RICHTIG {z['RICHTIG']}, NACHGEFRAGT {z['NACHGEFRAGT']}, "
              f"FALSCH {z['FALSCH']}, FEHLER {z['FEHLER']}")
    for zeile in abweichungen[:80]:
        print(zeile)
    if len(abweichungen) > 80:
        print(f"... {len(abweichungen) - 80} weitere")
    return 1 if zaehler["FALSCH"] or zaehler["FEHLER"] else 0


if __name__ == "__main__":
    sys.exit(main())
