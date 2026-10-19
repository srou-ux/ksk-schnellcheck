"""Ein Zahlenfeld gilt nur, wenn dieselbe Zahl im Text steht. Nichts wird nachgerechnet."""
from __future__ import annotations

import re
from decimal import Decimal

from extraktion.felder import SUMMEN, dezimal


def nur_woertlich(felder: dict, text: str) -> dict:
    """Streicht Werte, die der Text nicht enthält, und merkt sie als abgeleitet."""
    quelle = text or ""
    abgeleitet = list(felder.get("abgeleitet") or [])

    def pruefe(wert, pfad: str) -> str:
        roh = str(wert or "").strip()
        if not roh:
            return ""
        if steht(roh, quelle):
            return roh
        abgeleitet.append(pfad)
        return ""

    for name in SUMMEN:
        felder["summen"][name] = pruefe(felder["summen"].get(name, ""), "summen." + name)
    for index, position in enumerate(felder.get("positionen") or []):
        for name in ("nr", "betrag", "netto", "ust", "satz"):
            position[name] = pruefe(position.get(name, ""), f"positionen[{index}].{name}")
    for name in ("empfaenger", "empfaenger_name", "jahr", "betrag_in_worten", "betrag_in_ziffern"):
        felder[name] = pruefe(felder.get(name, ""), name)
    formen = []
    for form in felder.get("rechtsform_angaben") or []:
        if steht(str(form), quelle):
            formen.append(form)
        else:
            abgeleitet.append("rechtsform_angaben")
    felder["rechtsform_angaben"] = formen
    saetze = []
    for satz in felder.get("ust_saetze") or []:
        if steht(str(satz), quelle):
            saetze.append(satz)
        else:
            abgeleitet.append("ust_saetze")
    felder["ust_saetze"] = saetze
    felder["abgeleitet"] = abgeleitet
    return felder


def steht(wert: str, text: str) -> bool:
    """Format darf 1.800,00 oder 1800.00 sein. Eine andere Zahl gilt nicht."""
    kompakt = (text or "").replace("\u00a0", " ")
    zahl = dezimal(wert)
    if zahl is None:
        return wert.strip().lower() in (text or "").lower()
    betrag = Decimal(zahl)
    if betrag == 0:
        varianten = ("0,00", "0.00")
    else:
        varianten = _varianten(betrag)
    for variante in varianten:
        if re.search(rf"(?<!\d){re.escape(variante)}(?!\d)", kompakt):
            return True
    muster = _gruppiert(betrag)
    return bool(muster and re.search(muster, kompakt))


def _varianten(betrag: Decimal) -> tuple[str, ...]:
    plain = format(betrag, "f")
    ganz, _, bruch = plain.partition(".")
    vorzeichen = "-" if ganz.startswith("-") else ""
    ziffern = ganz[1:] if vorzeichen else ganz
    gruppen = []
    rest = ziffern
    while rest:
        gruppen.append(rest[-3:])
        rest = rest[:-3]
    gruppiert = vorzeichen + ".".join(reversed(gruppen))
    varianten = {plain, plain.replace(".", ","), ganz, gruppiert}
    if bruch and set(bruch) != {"0"}:
        varianten.add(ganz + "," + bruch)
        varianten.add(gruppiert + "," + bruch)
    else:
        varianten.add(ganz + ",00")
        varianten.add(gruppiert + ",00")
    return tuple(varianten)


def _gruppiert(betrag: Decimal) -> str:
    """Ein beliebiges Trennzeichen zwischen Tausendergruppen. 2·470,00 bleibt 2470."""
    plain = format(betrag, "f")
    vorzeichen = "-" if plain.startswith("-") else ""
    if vorzeichen:
        plain = plain[1:]
    ganz, _, bruch = plain.partition(".")
    gruppen = []
    rest = ganz
    while rest:
        gruppen.append(rest[-3:])
        rest = rest[:-3]
    teile = list(reversed(gruppen))
    if len(teile) < 2:
        return ""
    kern = r"[^\d]".join(re.escape(teil) for teil in teile)
    if bruch and set(bruch) != {"0"}:
        kern += r"[,.]" + re.escape(bruch)
    else:
        kern += r"(?:[,.]00)?"
    return rf"(?<!\d){vorzeichen}{kern}(?!\d)"
