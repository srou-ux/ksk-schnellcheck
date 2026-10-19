"""Feldstruktur, die der Kern liest. Keine Ergebnisklasse, keine Abgabe."""
from __future__ import annotations

import json
import pathlib
import re
from decimal import Decimal, InvalidOperation

WURZEL = pathlib.Path(__file__).resolve().parent
SUMMEN = ("positionssumme", "kopfsumme", "netto", "ust", "brutto", "gesamtsumme", "differenz")
ENTSCHEIDUNGSWORTE = ("abgabepflichtig", "status", "klasse", "zaehlt", "sperre", "entscheidung")

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "positionen": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "nr": {"type": "string"},
                    "betrag": {"type": "string"},
                    "text": {"type": "string"},
                    "betragswiderspruch": {"type": "boolean"},
                    "unsicher": {"type": "boolean"},
                    "netto": {"type": "string"},
                    "ust": {"type": "string"},
                    "satz": {"type": "string"},
                },
                "required": ["nr", "betrag", "text", "betragswiderspruch", "unsicher", "netto", "ust", "satz"],
            },
        },
        "summen": {
            "type": "object",
            "additionalProperties": False,
            "properties": {name: {"type": "string"} for name in SUMMEN},
            "required": list(SUMMEN),
        },
        "empfaenger": {"type": "string"},
        "empfaenger_name": {"type": "string"},
        "rechtsform_angaben": {"type": "array", "items": {"type": "string"}},
        "jahr": {"type": "string"},
        "betrag_in_worten": {"type": "string"},
        "betrag_in_ziffern": {"type": "string"},
        "unklare_felder": {"type": "array", "items": {"type": "string"}},
        "unsicher": {"type": "boolean"},
        "kleinunternehmer_genannt": {"type": "boolean"},
        "umsatzsteuer_genannt": {"type": "boolean"},
        "storno_genannt": {"type": "boolean"},
        "ust_saetze": {"type": "array", "items": {"type": "string"}},
        "summe_ohne_einheitlichen_satz": {"type": "boolean"},
    },
    "required": [
        "positionen", "summen", "empfaenger", "empfaenger_name", "rechtsform_angaben", "jahr",
        "betrag_in_worten", "betrag_in_ziffern", "unklare_felder", "unsicher",
        "kleinunternehmer_genannt", "umsatzsteuer_genannt", "storno_genannt",
        "ust_saetze", "summe_ohne_einheitlichen_satz",
    ],
}


def konfig() -> dict:
    daten = json.loads((WURZEL / "konfiguration.json").read_text(encoding="utf-8"))
    import os
    for name in ("MISTRAL_OCR_MODEL", "MISTRAL_SMALL_MODEL", "MISTRAL_MEDIUM_MODEL"):
        if os.environ.get(name, "").strip():
            daten[name] = os.environ[name].strip()
    return daten


def leer() -> dict:
    return {
        "positionen": [],
        "summen": {name: "" for name in SUMMEN},
        "empfaenger": "",
        "empfaenger_name": "",
        "rechtsform_angaben": [],
        "jahr": "",
        "betrag_in_worten": "",
        "betrag_in_ziffern": "",
        "unklare_felder": [],
        "unsicher": False,
        "kleinunternehmer_genannt": False,
        "umsatzsteuer_genannt": False,
        "storno_genannt": False,
        "ust_saetze": [],
        "summe_ohne_einheitlichen_satz": False,
        "ocr_bloecke": [],
        "kosten": [],
        "modelle": [],
    }


def dezimal(text: str) -> str | None:
    """Liest eine geschriebene Zahl. Kein Mittelwert, kein Ersatzwert."""
    roh = (text or "").strip().replace(" ", "")
    if not roh or not re.fullmatch(r"-?\d{1,3}(?:\.\d{3})+(?:,\d+)?|-?\d+,\d+|-?\d+(?:\.\d+)?", roh):
        return None
    if "," in roh:
        roh = roh.replace(".", "").replace(",", ".")
    try:
        return format(Decimal(roh), "f")
    except InvalidOperation:
        return None


def _kanon_wert(wert):
    if isinstance(wert, str):
        zahl = dezimal(wert)
        return zahl if zahl is not None else wert.strip()
    if isinstance(wert, bool) or wert is None:
        return wert
    if isinstance(wert, list):
        return [_kanon_wert(teil) for teil in wert]
    if isinstance(wert, dict):
        return {schluessel: _kanon_wert(inhalt) for schluessel, inhalt in wert.items()}
    return wert


def kanon(felder: dict) -> dict:
    """Vergleichsform ohne Kosten und ohne OCR-Rohdaten."""
    return {name: _kanon_wert(felder.get(name)) for name in SCHEMA["required"]}


def aus_modell(roh: dict) -> dict:
    """Übernimmt nur Schemafelder. Eine mitgelieferte Entscheidung wird verworfen."""
    felder = leer()
    if not isinstance(roh, dict):
        felder["unsicher"] = True
        felder["unklare_felder"] = ["antwort"]
        return felder
    if any(wort in roh for wort in ENTSCHEIDUNGSWORTE):
        felder["unsicher"] = True
        felder["unklare_felder"].append("entscheidung")
    for name in SCHEMA["required"]:
        if name not in roh:
            continue
        wert = roh[name]
        if name == "summen" and isinstance(wert, dict):
            felder["summen"] = {schluessel: str(wert.get(schluessel) or "") for schluessel in SUMMEN}
        elif name == "positionen" and isinstance(wert, list):
            felder["positionen"] = [_position(teil) for teil in wert if isinstance(teil, dict)]
        elif name == "rechtsform_angaben" and isinstance(wert, list):
            felder["rechtsform_angaben"] = [str(teil) for teil in wert if str(teil).strip()]
        elif name == "unklare_felder" and isinstance(wert, list):
            felder["unklare_felder"] = [str(teil) for teil in wert if str(teil).strip()]
        elif name == "ust_saetze" and isinstance(wert, list):
            felder["ust_saetze"] = [str(teil) for teil in wert if str(teil).strip()]
        elif name in ("unsicher", "kleinunternehmer_genannt", "umsatzsteuer_genannt", "storno_genannt", "summe_ohne_einheitlichen_satz"):
            felder[name] = bool(wert)
        elif isinstance(wert, str):
            felder[name] = wert.strip()
    return felder


def _position(teil: dict) -> dict:
    return {
        "nr": str(teil.get("nr") or ""),
        "betrag": str(teil.get("betrag") or ""),
        "text": str(teil.get("text") or ""),
        "betragswiderspruch": bool(teil.get("betragswiderspruch")),
        "unsicher": bool(teil.get("unsicher")),
        "netto": str(teil.get("netto") or ""),
        "ust": str(teil.get("ust") or ""),
        "satz": str(teil.get("satz") or ""),
    }


def an_kern(felder: dict, jahr_fallback: int) -> dict:
    """Nur sichere, gefüllte Angaben. Unsichere Felder bleiben draußen."""
    unklar = set(felder.get("unklare_felder") or [])
    if felder.get("unsicher") and not unklar:
        unklar.update(SCHEMA["required"])
    dokument: dict = {}
    summen = {}
    abgeleitet_summen = set(felder.get("abgeleitet") or [])
    for name in SUMMEN:
        if name in unklar or ("summen." + name) in unklar or ("summen." + name) in abgeleitet_summen:
            continue
        zahl = dezimal((felder.get("summen") or {}).get(name, ""))
        if zahl is not None:
            summen[name] = zahl
    worte = None if "betrag_in_worten" in unklar else dezimal(felder.get("betrag_in_worten", ""))
    ziffern = None if "betrag_in_ziffern" in unklar else dezimal(felder.get("betrag_in_ziffern", ""))
    if worte is not None and ziffern is not None:
        summen["betrag_worte"] = worte
        summen["betrag_ziffern"] = ziffern
    if summen:
        dokument["summen"] = summen
    if "differenz" in summen:
        dokument["differenz"] = summen["differenz"]
    positionen = []
    nummern = []
    abgeleitet = set(felder.get("abgeleitet") or [])
    for index, position in enumerate(felder.get("positionen") or []):
        if position.get("unsicher"):
            continue
        zeile = {}
        if position.get("nr") and f"positionen[{index}].nr" not in abgeleitet:
            zeile["nr"] = position["nr"]
            nummern.append(position["nr"])
        if f"positionen[{index}].betrag" not in abgeleitet:
            zahl = dezimal(position.get("betrag", ""))
            if zahl is not None:
                zeile["betrag"] = zahl
        if position.get("betragswiderspruch"):
            zeile["betragswiderspruch"] = True
        for name in ("netto", "ust", "satz"):
            if f"positionen[{index}].{name}" in abgeleitet:
                continue
            zahl = dezimal(position.get(name, ""))
            if zahl is not None:
                zeile[name] = zahl
        if zeile:
            positionen.append(zeile)
    if positionen:
        dokument["positionen"] = positionen
    if len(nummern) != len(set(nummern)):
        dokument["positionsnummern"] = nummern
    formen = []
    if "rechtsform_angaben" not in unklar:
        formen = [str(form).lower() for form in felder.get("rechtsform_angaben") or [] if str(form).strip()]
    name = ""
    if "empfaenger_name" not in unklar and "empfaenger_name" not in abgeleitet_summen:
        name = str(felder.get("empfaenger_name") or "").strip()
    if not name and "empfaenger" not in unklar and "empfaenger" not in abgeleitet_summen:
        name = str(felder.get("empfaenger") or "").strip()
    name_ist_form = bool(name) and name.lower() in set(formen)
    if name and not name_ist_form:
        dokument["empfaenger_name"] = name
        if len(set(formen)) > 1:
            dokument["rechtsformen"] = list(dict.fromkeys(formen))
        elif len(formen) == 1:
            dokument["rechtsform"] = formen[0]
    elif len(set(formen)) > 1:
        dokument["rechtsformen"] = list(dict.fromkeys(formen))
    elif len(formen) == 1 and "empfaenger" not in unklar:
        dokument["empfaenger"] = formen[0]
    elif name and "empfaenger" not in unklar:
        dokument["empfaenger"] = name.lower()
    jahr = felder.get("jahr") or ""
    if "jahr" not in unklar and re.fullmatch(r"20\d\d", jahr):
        dokument["jahr"] = int(jahr)
    else:
        dokument["jahr"] = jahr_fallback
    if felder.get("kleinunternehmer_genannt") and "kleinunternehmer_genannt" not in unklar:
        dokument["kleinunternehmer"] = True
    if felder.get("umsatzsteuer_genannt") and "umsatzsteuer_genannt" not in unklar:
        dokument["ust_ausgewiesen"] = True
    if felder.get("storno_genannt") and "storno_genannt" not in unklar:
        dokument["storno"] = True
    if "ust_saetze" not in unklar:
        saetze = [str(satz).strip() for satz in felder.get("ust_saetze") or [] if str(satz).strip()]
        if saetze:
            dokument["ust_saetze"] = saetze
    if felder.get("summe_ohne_einheitlichen_satz") and "summe_ohne_einheitlichen_satz" not in unklar:
        dokument["summe_ohne_einheitlichen_satz"] = True
    return dokument
