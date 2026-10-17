"""Spielt einen Dialog aus der Weboberfläche Schritt für Schritt durch die echte Pipeline nach
und zeigt je Schritt die ROHE Modellantwort, die übernommenen Fakten und die Systemantwort.
Nur erfundene Daten. Entwurf – vom Steuerberater zu prüfen.

Schritte als JSON-Liste: {"text": "..."} für eine Nachricht, {"knopf": ["feld", wert]} für eine
Schaltfläche. Aufruf: python aufgaben/audit/dialog_nachspielen.py --llm mistral --datei schritte.json
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

WURZEL = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL))

from app import bestaetigung, router  # noqa: E402

STANDARD = [
    {"text": "Extrahiere ausschließlich ausdrücklich genannte Fakten.\nAntworte nur als JSON mit: jahr, anzahl_rechnungen,\n"
             "betrag_je_rechnung_eur, werbezweck.\nFehlende Angaben bleiben null. Keine rechtliche Bewertung."},
    {"knopf": ["jahr", 2026]},
    {"knopf": ["auftragnehmer_typ", "GmbH_UG_AG"]},
    {"text": "bitte mehr details"},
    {"text": "2000 euro"},
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", choices=["fake", "mistral"], default="fake")
    ap.add_argument("--datei")
    ap.add_argument("--bericht")
    args = ap.parse_args()
    schritte = json.loads(pathlib.Path(args.datei).read_text(encoding="utf-8")) if args.datei else STANDARD
    if args.llm == "mistral":
        if not os.environ.get("MISTRAL_API_KEY"):
            print("KEIN SCHLÜSSEL")
            return 0
        from app.llm import mistral as M
        llm = M.MistralLLM()
        roh_aufruf = llm._aufruf
        rohe: list[str] = []

        def mitschneiden(system, user, max_tokens=None, **kw):
            antwort = roh_aufruf(system, user, max_tokens, **kw) if kw else roh_aufruf(system, user, max_tokens)
            if max_tokens is None:  # nur die Fakten-Extraktion, nicht die Fallbeschreibung
                rohe.append(f"EINGABE ANS MODELL: {user!r}\n- ROHE ANTWORT: {antwort[:3000]}")
            return antwort

        llm._aufruf = mitschneiden
        name = M.MISTRAL_MODELL
    else:
        from app.llm.fake import FakeLLM
        llm, rohe, name = FakeLLM(), [], "Demo-Modus"
    zeilen = [f"# Dialog nachgespielt – {name}", ""]
    verlauf, sitzung = [], None
    for i, s in enumerate(schritte, 1):
        rohe.clear()
        vorher = bestaetigung.SPEICHER.hole_fakten(sitzung) if sitzung else None
        offene_vorher = bestaetigung.SPEICHER.hole_offene_fragen(sitzung) if sitzung else []
        if "text" in s:
            a = router.bearbeite_frage(s["text"], llm, list(verlauf), sitzung)
            verlauf.append(s["text"])
            zeilen.append(f"## Schritt {i}: Nachricht {s['text'][:80]!r}")
        else:
            feld, wert = s["knopf"]
            a = router.wende_feldantwort_an(sitzung, feld, wert, llm)
            zeilen.append(f"## Schritt {i}: Knopf {feld} = {wert!r}")
        sitzung = a.sitzungskennung or sitzung
        f = bestaetigung.SPEICHER.hole_fakten(sitzung) if sitzung else None
        zeilen.append(f"- Sitzung: {sitzung}; Fallstand VORHER: {vorher.model_dump(exclude_none=True, mode='json') if vorher else None}")
        zeilen.append(f"- Offene Fragen vorher: {offene_vorher}")
        zeilen.append(f"- Mitgeschickter Verlauf (Einträge): {len(verlauf) - (1 if 'text' in s else 0)}")
        zeilen += [f"- {r}" for r in rohe]
        zeilen.append(f"- Fakten der Sitzung: {f.model_dump(exclude_none=True, mode='json') if f else None}")
        zeilen.append(f"- Systemantwort: {a.ergebnisklasse}; Rückfragen: {a.rueckfragen}; Knöpfe: "
                      f"{[o.get('optionen') for o in (a.rueckfrage_optionen or [])]}")
        if a.fakten_zusammenfassung:
            zeilen.append(f"- Angezeigte Faktenbestätigung: {a.fakten_zusammenfassung}")
        zeilen.append("")
    text = "\n".join(zeilen) + "\n"
    print(text)
    if args.bericht:
        pathlib.Path(args.bericht).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
