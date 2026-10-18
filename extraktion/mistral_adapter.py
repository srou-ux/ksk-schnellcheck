"""Stufe 1 OCR 4.1, Stufe 2 Small. Medium nur, wenn Small kein gültiges JSON liefert."""
from __future__ import annotations

import base64
import json
from pathlib import Path

from extraktion import http
from extraktion.felder import SCHEMA, aus_modell, konfig, leer
from extraktion.konfidenz import bloecke_filtern, einigung
from extraktion.schluessel import schluessel as lies_schluessel

_SYSTEM = (
    "Du füllst nur Felder, die im Dokument stehen. "
    "Du triffst keine Entscheidung zur Künstlersozialabgabe und nennst keine Ergebnisklasse. "
    "Was nicht dasteht, bleibt leer. "
    "Wenn du eine Angabe nicht sicher lesen kannst, setze unsicher auf true und lass den unsicheren Wert leer. "
    "Bilde keinen Mittelwert und ergänze nichts. "
    "Prozentzahlen der Umsatzsteuer stehen in ust_saetze. "
    "netto, ust und satz nur, wenn sie auf der Zeile stehen. "
    "summe_ohne_einheitlichen_satz nur, wenn das Dokument selbst sagt, dass die Summe zu keinem Satz passt."
)


def extrahiere(dokument, *, transport=None, schluessel: str | None = None) -> dict:
    """PDF oder Bild: OCR, dann Small. Reiner Text: nur Small, dreimal gelesen."""
    aufruf = transport or http.post_json
    key = schluessel if schluessel is not None else lies_schluessel()
    if not key:
        felder = leer()
        felder["unsicher"] = True
        felder["unklare_felder"] = ["schluessel"]
        return felder
    cfg = konfig()
    text, bloecke, kosten = _stufe_ocr(dokument, aufruf, key, cfg)
    if bloecke:
        sicher, verworfen = bloecke_filtern(bloecke, float(cfg["ocr_konfidenz_minimum"]))
        if verworfen:
            text = sicher
        if not text.strip():
            felder = leer()
            felder["unsicher"] = True
            felder["unklare_felder"] = ["ocr"]
            felder["ocr_bloecke"] = verworfen
            felder["kosten"] = kosten
            return felder
    else:
        verworfen = []
        text = _text(dokument) if not text else text
    ablesungen = []
    modell = cfg["MISTRAL_SMALL_MODEL"]
    for _ in range(int(cfg["ablesungen"])):
        roh, kosten_zeile, modell = _stufe_small(text, aufruf, key, cfg, modell)
        kosten.append(kosten_zeile)
        if roh is None:
            felder = leer()
            felder["unsicher"] = True
            felder["unklare_felder"] = ["small"]
            felder["kosten"] = kosten
            felder["ocr_bloecke"] = verworfen
            return felder
        ablesungen.append(aus_modell(roh))
    felder = einigung(ablesungen)
    felder["kosten"] = kosten
    felder["ocr_bloecke"] = verworfen
    felder["modelle"] = [cfg["MISTRAL_OCR_MODEL"], modell] if bloecke or _ist_datei(dokument) else [modell]
    return felder


def _stufe_ocr(dokument, aufruf, key: str, cfg: dict) -> tuple[str, list, list]:
    if not _ist_datei(dokument):
        return _text(dokument), [], []
    roh, mime = _bytes(dokument)
    art = "image_url" if mime.startswith("image/") else "document_url"
    data = "data:" + mime + ";base64," + base64.b64encode(roh).decode("ascii")
    koerper = {
        "model": cfg["MISTRAL_OCR_MODEL"],
        "document": {"type": art, art: data},
        "include_blocks": True,
        "confidence_scores_granularity": "block",
    }
    antwort = aufruf("/v1/ocr", koerper, key)
    seiten = antwort.get("pages") or []
    texte = []
    bloecke = []
    for seite in seiten:
        if seite.get("markdown"):
            texte.append(seite["markdown"])
        for block in seite.get("blocks") or []:
            wert = block.get("confidence_scores") or block.get("confidence")
            bloecke.append({
                "text": block.get("content") or block.get("markdown") or "",
                "konfidenz": wert,
            })
    nutzung = antwort.get("usage_info") or {}
    kosten = [{
        "stufe": "ocr",
        "modell": antwort.get("model") or cfg["MISTRAL_OCR_MODEL"],
        "seiten": nutzung.get("pages_processed") or len(seiten),
        "prompt_tokens": None,
        "completion_tokens": None,
    }]
    return "\n".join(texte), bloecke, kosten


def _stufe_small(text: str, aufruf, key: str, cfg: dict, modell: str):
    koerper = {
        "model": modell,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": text or ""},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "feldstruktur", "strict": True, "schema": SCHEMA},
        },
    }
    try:
        antwort = aufruf("/v1/chat/completions", koerper, key)
    except http.Schnittstellenfehler as fehler:
        if fehler.status in (401, 402, 403) or modell == cfg["MISTRAL_MEDIUM_MODEL"]:
            raise
        return _stufe_small(text, aufruf, key, cfg, cfg["MISTRAL_MEDIUM_MODEL"])
    inhalt = (((antwort.get("choices") or [{}])[0].get("message") or {}).get("content")) or ""
    try:
        roh = json_laden(inhalt)
    except ValueError:
        if modell != cfg["MISTRAL_MEDIUM_MODEL"]:
            return _stufe_small(text, aufruf, key, cfg, cfg["MISTRAL_MEDIUM_MODEL"])
        return None, _nutzung(antwort, "medium", modell), modell
    return roh, _nutzung(antwort, "small" if modell == cfg["MISTRAL_SMALL_MODEL"] else "medium", modell), modell


def json_laden(inhalt: str) -> dict:
    return json.loads(inhalt)


def _nutzung(antwort: dict, stufe: str, modell: str) -> dict:
    usage = antwort.get("usage") or {}
    return {
        "stufe": stufe,
        "modell": antwort.get("model") or modell,
        "seiten": 0,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
    }


def _text(dokument) -> str:
    if isinstance(dokument, str):
        return dokument
    if isinstance(dokument, dict):
        return str(dokument.get("text") or dokument.get("txt") or "")
    return ""


def _ist_datei(dokument) -> bool:
    if isinstance(dokument, dict) and (dokument.get("bytes") or dokument.get("pfad")):
        return True
    return False


def _bytes(dokument) -> tuple[bytes, str]:
    mime = str(dokument.get("mime") or "application/pdf")
    if dokument.get("bytes"):
        return dokument["bytes"], mime
    return Path(dokument["pfad"]).read_bytes(), mime
