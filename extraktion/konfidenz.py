"""Konfidenz: ein Block unter der Schwelle oder abweichende Ablesungen sperrt das Feld.

Es wird kein Mittelwert gebildet und keine der abweichenden Lesungen übernommen.
"""
from __future__ import annotations

from extraktion.felder import _kanon_wert, kanon, leer


def bloecke_filtern(bloecke: list, minimum: float) -> tuple[str, list]:
    """Liefert den sicheren Text und die verworfenen Blöcke."""
    sicher = []
    verworfen = []
    for block in bloecke or []:
        text = str(block.get("text") or block.get("content") or "").strip()
        wert = _konfidenz(block)
        if wert is None or wert < minimum:
            verworfen.append({"text": text, "konfidenz": wert})
            continue
        if text:
            sicher.append(text)
    return "\n".join(sicher), verworfen


def _konfidenz(block: dict):
    roh = block.get("konfidenz", block.get("confidence"))
    if isinstance(roh, dict):
        roh = roh.get("average_content_confidence_score")
    if roh is None:
        return None
    try:
        return float(roh)
    except (TypeError, ValueError):
        return None


def einigung(ablesungen: list[dict]) -> dict:
    """Drei gleiche Lesungen bleiben. Sonst ist das abweichende Feld leer und unsicher."""
    from extraktion.felder import SUMMEN, SCHEMA

    if len(ablesungen) < 3:
        felder = leer()
        felder["unsicher"] = True
        felder["unklare_felder"] = ["ablesung"]
        return felder
    felder = leer()
    for name in SCHEMA["required"]:
        if name in ("summen", "positionen"):
            continue
        werte = [kanon(lesung).get(name) for lesung in ablesungen]
        if all(andere == werte[0] for andere in werte):
            felder[name] = ablesungen[0].get(name)
        else:
            felder["unklare_felder"].append(name)
            felder["unsicher"] = True
    for name in SUMMEN:
        werte = [kanon(lesung).get("summen", {}).get(name, "") for lesung in ablesungen]
        if all(andere == werte[0] for andere in werte):
            felder["summen"][name] = (ablesungen[0].get("summen") or {}).get(name, "")
        else:
            felder["unklare_felder"].append("summen." + name)
            felder["unsicher"] = True
    felder["positionen"] = _positionen_einigen(ablesungen, felder)
    return felder


def _positionen_einigen(ablesungen: list[dict], felder: dict) -> list:
    """Gleiche Zeilenfelder bleiben. Ein abweichendes Feld leert nur sich selbst."""
    listen = [lesung.get("positionen") or [] for lesung in ablesungen]
    if len({len(liste) for liste in listen}) != 1:
        felder["unklare_felder"].append("positionen")
        felder["unsicher"] = True
        return []
    namen = ("nr", "betrag", "text", "betragswiderspruch", "unsicher", "netto", "ust", "satz")
    ergebnis = []
    for index in range(len(listen[0])):
        zeile = {}
        for name in namen:
            werte = [liste[index].get(name) for liste in listen]
            vergleich = [_kanon_wert(wert) for wert in werte]
            if all(andere == vergleich[0] for andere in vergleich):
                zeile[name] = listen[0][index].get(name)
            else:
                zeile[name] = False if name in ("betragswiderspruch", "unsicher") else ""
                felder["unklare_felder"].append(f"positionen[{index}].{name}")
                felder["unsicher"] = True
        ergebnis.append(zeile)
    return ergebnis
