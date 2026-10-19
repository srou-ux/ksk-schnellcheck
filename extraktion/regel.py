"""Regel-Leser: nur Muster im Text, keine Abgabeentscheidung."""
from __future__ import annotations

import re

from extraktion.felder import SUMMEN, dezimal, leer
from extraktion.verbatim import nur_woertlich

_BETRAG = r"(-?\d{1,3}(?:\.\d{3})+(?:,\d{2})?|-?\d+,\d{2}|-?\d+\.\d{2}|-?\d+)"
_FORMEN = (
    ("ggmbh", "ggmbh"),
    ("gmbh", "gmbh"),
    ("einzelunternehmen", "einzelunternehmen"),
    ("freiberuflich", "freiberuflich"),
    ("ohg", "ohg"),
    ("ug", "ug"),
    ("ag", "ag"),
    ("kg", "kg"),
)


def extrahiere(dokument) -> dict:
    text = _text(dokument)
    felder = leer()
    felder["modelle"] = ["rule"]
    for name in SUMMEN:
        zahl = _nach_wort(text, name)
        if zahl is not None:
            felder["summen"][name] = zahl
    worte = re.search(r"betrag in worten\s+'([^']+)'", text.lower())
    ziffern = re.search(r"ziffern\s+" + _BETRAG, text.lower())
    if worte:
        felder["betrag_in_worten"] = worte.group(1)
    if ziffern and dezimal(ziffern.group(1)):
        felder["betrag_in_ziffern"] = dezimal(ziffern.group(1))
    doppelt = re.search(r"position\s+(\d+)\s+doppelt", text.lower())
    if doppelt:
        nr = doppelt.group(1)
        felder["positionen"] = [
            {"nr": nr, "betrag": "", "text": "", "betragswiderspruch": False, "unsicher": False, "netto": "", "ust": "", "satz": ""},
            {"nr": nr, "betrag": "", "text": "", "betragswiderspruch": False, "unsicher": False, "netto": "", "ust": "", "satz": ""},
        ]
    zeile = re.search(r"position\s+(\d+)[^\n]{0,80}betragswiderspruch", text.lower())
    if zeile:
        felder["positionen"].append({
            "nr": zeile.group(1), "betrag": "", "text": "", "betragswiderspruch": True, "unsicher": False,
            "netto": "", "ust": "", "satz": "",
        })
    low = text.lower()
    felder["kleinunternehmer_genannt"] = "kleinunternehmer" in low
    felder["umsatzsteuer_genannt"] = bool(re.search(r"(?<![a-zäöü])ust(?![a-zäöü])|umsatzsteuer", low))
    felder["storno_genannt"] = "storno" in low
    felder["ust_saetze"] = re.findall(r"(\d+)\s*prozent", low)
    felder["summe_ohne_einheitlichen_satz"] = "passt zu keinem" in low
    felder["rechtsform_angaben"] = _formen(low)
    if re.search(r"(oeffentliche|öffentliche)\s+(musikschule|stelle|sparkasse)", low):
        felder["rechtsform_angaben"].append("oeffentlich")
    jahre = []
    for treffer in re.finditer(r"20\d\d", text):
        davor = text[max(0, treffer.start() - 16):treffer.start()].lower()
        if "bis " in davor or "loesch" in davor or "lösch" in davor:
            continue
        jahre.append(treffer.group())
    if len(set(jahre)) == 1:
        felder["jahr"] = jahre[0]
    elif len(set(jahre)) > 1:
        felder["unklare_felder"].append("jahr")
        felder["unsicher"] = True
    return nur_woertlich(felder, text)


def _text(dokument) -> str:
    if isinstance(dokument, str):
        return dokument
    if isinstance(dokument, dict):
        return str(dokument.get("text") or dokument.get("txt") or "")
    return str(getattr(dokument, "text", "") or "")


def _nach_wort(text: str, wort: str) -> str | None:
    treffer = re.search(rf"{wort}(?:\s+\w+){{0,3}}\s+{_BETRAG}", text.lower())
    if not treffer:
        return None
    danach = text.lower()[treffer.end():treffer.end() + 16]
    if re.match(r"\s*prozent", danach):
        return None
    return dezimal(treffer.group(1))


def _formen(low: str) -> list[str]:
    gefunden = []
    for muster, name in _FORMEN:
        if re.search(rf"(?<![a-zäöü]){muster}(?![a-zäöü])", low) and name not in gefunden:
            gefunden.append(name)
    return gefunden
