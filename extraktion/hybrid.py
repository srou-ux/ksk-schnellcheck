"""Regel und Small nebeneinander. Ein leeres Feld übernimmt der andere Leser.

Widerspruch wird nicht gemittelt und nicht still aufgelöst.
"""
from __future__ import annotations

from extraktion.felder import SUMMEN, _kanon_wert, leer

_TEXTE = ("empfaenger", "empfaenger_name", "jahr", "betrag_in_worten", "betrag_in_ziffern", "leistungsart")
_LISTEN = ("rechtsform_angaben", "ust_saetze", "erwahnungen")
_JANE = ("kleinunternehmer_genannt", "umsatzsteuer_genannt", "storno_genannt", "summe_ohne_einheitlichen_satz")
_ZEILE = ("nr", "betrag", "text", "betragswiderspruch", "unsicher", "netto", "ust", "satz")


def kombiniere(regel: dict, mistral: dict) -> dict:
    """Herkunft je Feld: regel, mistral oder beide. Abweichung steht in leser_widerspruch."""
    felder = leer()
    herkunft: dict[str, str] = {}
    widerspruch: list[str] = []
    for name in _TEXTE:
        _skalar(name, regel.get(name, ""), mistral.get(name, ""), felder, herkunft, widerspruch)
    for name in _LISTEN:
        _liste(name, regel.get(name) or [], mistral.get(name) or [], felder, herkunft, widerspruch)
    for name in _JANE:
        _janein(name, bool(regel.get(name)), bool(mistral.get(name)), felder, herkunft, widerspruch)
    for name in SUMMEN:
        _skalar(
            "summen." + name,
            (regel.get("summen") or {}).get(name, ""),
            (mistral.get("summen") or {}).get(name, ""),
            felder["summen"],
            herkunft,
            widerspruch,
        )
    _positionen(regel.get("positionen") or [], mistral.get("positionen") or [], felder, herkunft, widerspruch)
    felder["herkunft"] = herkunft
    felder["leser_widerspruch"] = widerspruch
    felder["abgeleitet"] = list(dict.fromkeys(list(regel.get("abgeleitet") or []) + list(mistral.get("abgeleitet") or [])))
    felder["kosten"] = list(mistral.get("kosten") or [])
    felder["modelle"] = list(dict.fromkeys(list(regel.get("modelle") or []) + list(mistral.get("modelle") or [])))
    return felder


def _gleich(links, rechts) -> bool:
    if isinstance(links, list) and isinstance(rechts, list):
        return sorted(_kanon_wert(str(teil)).lower() for teil in links) == sorted(_kanon_wert(str(teil)).lower() for teil in rechts)
    a, b = _kanon_wert(links), _kanon_wert(rechts)
    if isinstance(a, str) and isinstance(b, str):
        return a.lower() == b.lower()
    return a == b


def _gesetzt(wert) -> bool:
    if isinstance(wert, str):
        return bool(wert.strip())
    if isinstance(wert, bool):
        return wert is True
    if isinstance(wert, list):
        return any(str(teil).strip() for teil in wert)
    return wert not in (None, "")


def _skalar(name, links, rechts, ziel, herkunft, widerspruch):
    links_da = _gesetzt(links)
    rechts_da = _gesetzt(rechts)
    if links_da and rechts_da and not _gleich(links, rechts):
        widerspruch.append(name)
        return
    if links_da and rechts_da:
        ziel[name.split(".")[-1] if name.startswith("summen.") else name] = links
        herkunft[name] = "beide"
    elif links_da:
        ziel[name.split(".")[-1] if name.startswith("summen.") else name] = links
        herkunft[name] = "regel"
    elif rechts_da:
        ziel[name.split(".")[-1] if name.startswith("summen.") else name] = rechts
        herkunft[name] = "mistral"


def _liste(name, links, rechts, felder, herkunft, widerspruch):
    links_werte = [str(teil).strip() for teil in links if str(teil).strip()]
    rechts_werte = [str(teil).strip() for teil in rechts if str(teil).strip()]
    if links_werte and rechts_werte and not _gleich(links_werte, rechts_werte):
        widerspruch.append(name)
        return
    if links_werte and rechts_werte:
        felder[name] = links_werte
        herkunft[name] = "beide"
    elif links_werte:
        felder[name] = links_werte
        herkunft[name] = "regel"
    elif rechts_werte:
        felder[name] = rechts_werte
        herkunft[name] = "mistral"


def _janein(name, links, rechts, felder, herkunft, widerspruch):
    if links and rechts and links != rechts:
        widerspruch.append(name)
        return
    if links and rechts:
        felder[name] = True
        herkunft[name] = "beide"
    elif links or rechts:
        felder[name] = True
        herkunft[name] = "regel" if links else "mistral"


def _positionen(links, rechts, felder, herkunft, widerspruch):
    if not links and not rechts:
        return
    if links and rechts and _pos_kern(links) != _pos_kern(rechts):
        widerspruch.append("positionen")
        return
    quelle = links or rechts
    beide = bool(links and rechts)
    zeilen = []
    for zeile in quelle:
        kopie = {name: zeile.get(name) for name in _ZEILE}
        if not beide:
            kopie["betragswiderspruch"] = False
        zeilen.append(kopie)
    felder["positionen"] = zeilen
    herkunft["positionen"] = "beide" if beide else ("regel" if links else "mistral")


def _pos_kern(liste) -> list:
    return [
        {name: _kanon_wert(zeile.get(name)) for name in ("nr", "betrag", "netto", "ust", "satz", "betragswiderspruch")}
        for zeile in liste
    ]
