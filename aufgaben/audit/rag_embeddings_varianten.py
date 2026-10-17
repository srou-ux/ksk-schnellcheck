"""Vergleicht Varianten der Rangfolge MIT Embeddings auf denselben Testfällen (Abruf-Güte, erste 5).
Nur für den Workflow "RAG Embeddings messen" (braucht MISTRAL_API_KEY und einen Index mit Vektoren).
Achtung: Wer Varianten auf denselben Testfällen auswählt, passt sich an diese Testfälle an -- das Ergebnis
ist eine Messung, kein Beleg für neue Fragen. Schreibt aufgaben/RAG_Embeddings_Varianten.md."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.rag import embeddings, guete  # noqa: E402
from app.rag.zerlegen import KONFIG  # noqa: E402

_GEMERKT: dict[str, list[float]] = {}
_ORIGINAL = embeddings.mistral_einbetter


def _merkender_einbetter(texte: list[str]) -> list[list[float]]:
    """Suchfragen nur einmal einbetten (spart Aufrufe über alle Varianten)."""
    fehlend = [t for t in texte if t not in _GEMERKT]
    if fehlend:
        for t, v in zip(fehlend, _ORIGINAL(fehlend)):
            _GEMERKT[t] = v
    return [_GEMERKT[t] for t in texte]


embeddings.mistral_einbetter = _merkender_einbetter

VARIANTEN = [
    ("Nur Stichwortsuche (ohne Embeddings)", None),
    ("Embeddings als eine Liste, Gewicht 1,0", {"vektor_getrennt": False, "rrf_gewicht_vektor": 1.0}),
    ("Embeddings als eine Liste, Gewicht 0,5", {"vektor_getrennt": False, "rrf_gewicht_vektor": 0.5}),
    ("Embeddings getrennt (Regeln/Quellen/nachrangig), Gewicht 1,0", {"vektor_getrennt": True, "rrf_gewicht_vektor": 1.0}),
    ("Embeddings getrennt, Gewicht 0,5", {"vektor_getrennt": True, "rrf_gewicht_vektor": 0.5}),
    ("Embeddings getrennt, Gewicht 0,3", {"vektor_getrennt": True, "rrf_gewicht_vektor": 0.3}),
]


def main() -> int:
    faelle = guete.lies_faelle()
    zeilen = ["# RAG – Varianten mit Embeddings (Abruf-Güte)", "",
              "Gleiche 299 gewerteten Testfälle, erste 5 Plätze der Relevanzliste. Auswahl auf denselben Testfällen "
              "= Anpassung an diese Fälle; nur als Messung lesen.", "",
              "| Variante | Treffer | Quote | Erste Angabe | Gegenproben leer |", "|---|---|---|---|---|"]
    alt = dict(KONFIG)
    for name, aenderung in VARIANTEN:
        KONFIG.clear()
        KONFIG.update(alt)
        if aenderung is None:
            os.environ.pop("RAG_EMBEDDINGS", None)
        else:
            os.environ["RAG_EMBEDDINGS"] = "1"
            KONFIG.update(aenderung)
        e = guete.miss(faelle=faelle)
        z = e["zaehler"]
        g = z["treffer"] + z["fehlschlag"]
        leer = sum(1 for _, l, _ in guete.gegenproben() if l)
        zeile = f"| {name} | {z['treffer']}/{g} | {100 * z['treffer'] / g:.1f} % | {100 * z['erste_angabe'] / g:.1f} % | {leer}/10 |"
        print(zeile, flush=True)
        zeilen.append(zeile)
    KONFIG.clear()
    KONFIG.update(alt)
    Path("aufgaben/RAG_Embeddings_Varianten.md").write_text("\n".join(zeilen) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
