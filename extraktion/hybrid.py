"""Regel ist die Autorität. Small füllt nur Felder, die die Regel leer gelassen hat.

Ein gefülltes Regelfeld wird nicht überschrieben und nicht zur Rückfrage gemacht.
"""
from __future__ import annotations

from extraktion.felder import SUMMEN, leer

_TEXTE = (
    "empfaenger", "empfaenger_name", "jahr", "betrag_in_worten", "betrag_in_ziffern",
    "leistungsart", "taetigkeit", "verwerter", "jahresaggregat", "veranlassung", "beschaeftigung",
)
_LISTEN = ("rechtsform_angaben", "ust_saetze", "erwahnungen")
_JANE = ("kleinunternehmer_genannt", "umsatzsteuer_genannt", "storno_genannt", "summe_ohne_einheitlichen_satz")
_ZEILE = ("nr", "betrag", "text", "betragswiderspruch", "unsicher", "netto", "ust", "satz")
_PROBE = {"betrag_in_worten", "ust_saetze", "rechtsform_angaben", "positionen"}


def kombiniere(regel: dict, mistral: dict) -> dict:
    """Herkunft regel, mistral oder beide. Ein Konflikt lässt den Regelwert stehen."""
    felder = leer()
    herkunft: dict[str, str] = {}
    mistral = dict(mistral)
    if _gesetzt(regel.get("rechtsform_angaben")):
        # Ein ergänzter Name setzt die Rechtsform nicht mehr in empfaenger.
        # V-092 bliebe dann offen, V-116 würde als Gesellschaft ausgeschlossen.
        if not _gesetzt(regel.get("empfaenger")):
            mistral["empfaenger"] = ""
        if not _gesetzt(regel.get("empfaenger_name")):
            mistral["empfaenger_name"] = ""
    gesperrt = set(mistral.get("abgeleitet") or [])
    for name in _TEXTE:
        _skalar(name, regel.get(name, ""), mistral.get(name, ""), felder, herkunft, gesperrt)
    for name in _LISTEN:
        _liste(name, regel.get(name) or [], mistral.get(name) or [], felder, herkunft, gesperrt)
    for name in _JANE:
        _janein(name, bool(regel.get(name)), bool(mistral.get(name)), felder, herkunft)
    for name in SUMMEN:
        _skalar(
            "summen." + name,
            (regel.get("summen") or {}).get(name, ""),
            (mistral.get("summen") or {}).get(name, ""),
            felder["summen"],
            herkunft,
            gesperrt,
        )
    _positionen(regel.get("positionen") or [], mistral.get("positionen") or [], felder, herkunft, gesperrt)
    felder["herkunft"] = herkunft
    felder["leser_widerspruch"] = []
    felder["abgeleitet"] = list(dict.fromkeys(list(regel.get("abgeleitet") or []) + list(gesperrt)))
    felder["kosten"] = list(mistral.get("kosten") or [])
    felder["modelle"] = list(dict.fromkeys(list(regel.get("modelle") or []) + list(mistral.get("modelle") or [])))
    return felder


def _gesetzt(wert) -> bool:
    if isinstance(wert, str):
        return bool(wert.strip())
    if isinstance(wert, bool):
        return wert is True
    if isinstance(wert, list):
        return any(str(teil).strip() for teil in wert)
    return wert not in (None, "")


def _schluessel(name: str) -> str:
    return name.split(".")[-1] if name.startswith("summen.") else name


def _ergaenzen(name: str, gesperrt: set) -> bool:
    if name in _PROBE or name.startswith("positionen"):
        return name not in gesperrt
    return True


def _skalar(name, links, rechts, ziel, herkunft, gesperrt):
    schluessel = _schluessel(name)
    if _gesetzt(links):
        ziel[schluessel] = links
        herkunft[name] = "regel"
        return
    if _gesetzt(rechts) and _ergaenzen(name, gesperrt):
        ziel[schluessel] = rechts
        herkunft[name] = "mistral"


def _liste(name, links, rechts, felder, herkunft, gesperrt):
    links_werte = [str(teil).strip() for teil in links if str(teil).strip()]
    rechts_werte = [str(teil).strip() for teil in rechts if str(teil).strip()]
    if links_werte:
        felder[name] = links_werte
        herkunft[name] = "regel"
        return
    if rechts_werte and _ergaenzen(name, gesperrt):
        felder[name] = rechts_werte
        herkunft[name] = "mistral"


def _janein(name, links, rechts, felder, herkunft):
    if links:
        felder[name] = True
        herkunft[name] = "regel"
    elif rechts:
        felder[name] = True
        herkunft[name] = "mistral"


def _positionen(links, rechts, felder, herkunft, gesperrt):
    if links:
        felder["positionen"] = [{name: zeile.get(name) for name in _ZEILE} for zeile in links]
        herkunft["positionen"] = "regel"
        return
    if not rechts or not _ergaenzen("positionen", gesperrt):
        return
    zeilen = []
    for index, zeile in enumerate(rechts):
        kopie = {name: zeile.get(name) for name in _ZEILE}
        if f"positionen[{index}].nr" in gesperrt:
            kopie["nr"] = ""
        kopie["betragswiderspruch"] = False
        if any(kopie.get(name) not in ("", False, None) for name in _ZEILE):
            zeilen.append(kopie)
    if zeilen:
        felder["positionen"] = zeilen
        herkunft["positionen"] = "mistral"
