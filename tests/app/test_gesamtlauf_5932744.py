"""Gesamtlauf 5932744 (15.10.2026): sechs Fälle von RICHTIG auf NACHGEFRAGT (P-28, P-32, W-03, HT-2026-092,
A-999, HT-2026-084). Geprüft mit dem Faktenlauf 38696351534 (je 3 Läufe mit und ohne Quellenabruf; Protokolle
aufgaben/audit/modellfehler_fakten_{mit,ohne}_38696351534.jsonl, unverändert).

Befund: Mit dem Code-Stand f6fae68 (vor den Änderungen des 15.10.2026) ergeben dieselben Modellantworten genau
dieselben Ergebnisse. Ursache ist also die Schwankung des Modells, keine Folge der neuen Prüfungen. Das Modell
erfindet in etwa einem von drei Läufen einen Rechnungsbetrag (P-32: zwei Rechnungen 1.200 € und 800 €; W-03:
Rechnung über 2.000 -- die US-Dollar -- bei 1.850 € abgebucht; HT-092: Rechnung über 1.200 € = nur 'Design';
P-28: 1.190 € als Umsatzsteuer). Das System fragt dann nach ('Aufteilung der Rechnung … unklar').

Dieser Test sichert das SICHERE Verhalten: Aus keiner dieser Modellantworten entsteht ein Ergebnis, das dem
Soll widerspricht (P-28/P-32/W-03: nie 'Nicht abgabepflichtig'; HT-092: nie sicher 'Abgabepflichtig' oder
'Nicht abgabepflichtig', weil Programmierung/SEO/Hosting dabei sind). Er prüft kein bestimmtes Wording.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from app import bestaetigung, router
from app.llm.fake import FakeLLM
from app.schema import Fakten

W = Path(__file__).resolve().parents[2]
PROTOKOLLE = [W / f"aufgaben/audit/modellfehler_fakten_{v}_38696351534.jsonl" for v in ("mit", "ohne")]
KNOPF = {"Typischer Verwerter": "typischer_verwerter", "Eigenwerbung": "eigenwerber",
         "natürliche Person": "natuerliche_person"}
_ARCHIV = json.loads((W / "tests/archiv/alle_faelle.json").read_text(encoding="utf-8"))
FAELLE = {f["frage"]: f for f in (_ARCHIV["faelle"] if isinstance(_ARCHIV, dict) else _ARCHIV)}
VERBOTEN = {
    "pruefkatalog:P-28": {"Nicht abgabepflichtig (Vorschlag)"},
    "pruefkatalog:P-32": {"Nicht abgabepflichtig (Vorschlag)"},
    "waehrung:W-03": {"Nicht abgabepflichtig (Vorschlag)"},
    "fehlerquellen:HT-2026-092": {"Abgabepflichtig (Vorschlag)", "Nicht abgabepflichtig (Vorschlag)"},
}


def _ergebnis(frage: str, roh: dict, fall: dict) -> str:
    roh = dict(roh)
    for feld, wert in fall.get("knoepfe", {}).items():
        roh.setdefault(feld, KNOPF.get(wert, wert))
    llm = FakeLLM()
    llm.registriere(frage, Fakten.model_validate(roh))
    a = router.bearbeite_frage(frage, llm)
    if a.ergebnisklasse == "Faktenbestätigung nötig":
        bestaetigung.SPEICHER.bestaetige(a.sitzungskennung, a.fakten_hash)
        a = router.fuehre_nach_bestaetigung_aus(a.sitzungskennung, FakeLLM())
    return a.ergebnisklasse


class ModellschwankungBleibtSicher(unittest.TestCase):
    def test_kein_ergebnis_gegen_das_soll(self):
        gesehen = set()
        for pfad in PROTOKOLLE:
            for zeile in pfad.read_text(encoding="utf-8").splitlines():
                d = json.loads(zeile)
                fall = FAELLE.get(d["frage_anonymisiert"])
                if d.get("stufe") != "roh" or not fall or fall["id"] not in VERBOTEN:
                    continue
                gesehen.add(fall["id"])
                with self.subTest(fall=fall["id"], datei=pfad.name):
                    self.assertNotIn(_ergebnis(d["frage_anonymisiert"], d["fakten"], fall), VERBOTEN[fall["id"]])
        self.assertEqual(gesehen, set(VERBOTEN))


if __name__ == "__main__":
    unittest.main()
