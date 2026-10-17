"""Bereich „Rechnungen prüfen“: Dokumente hochladen -> mit Python lesen -> Angaben prüfen -> Ergebnis aus dem Regelkern.
Ohne KI (17.10.2026): kein Sprachmodell, kein Netz zur Laufzeit. PDF-Text mit pypdf, Fotos/Scans mit lokalem
Tesseract, Excel/CSV mit openpyxl/csv; Positionen erkennt die Regel-Erkennung (app/dokument_lesen.py).

Start: python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Originale werden nur vorübergehend zur lokalen Extraktion gespeichert und anschließend gelöscht.
Keine fachlichen Ergebnisse oder Dokumenttexte im Serverlog/Quellenindex speichern.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from app.dokument_lesen import KONFIG
from app.dokument_pruefung import DokumentFall, auswerten, vorbereiten
from app import quellen
from app.schema import AUFTRAGSPARTNER_LESBAR

app = FastAPI(title="KSK-Dokumentenprüfung – Entwurf")
router = APIRouter()
WURZEL = Path(__file__).resolve().parent.parent
_SCHLUESSEL = (os.environ.get("DOKUMENT_TICKET_SCHLUESSEL") or secrets.token_hex()).encode()
_PLAETZE = asyncio.Semaphore(KONFIG["max_parallel"])


SICHERHEITS_KOEPFE = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' blob:; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'self'",
}


@app.middleware("http")
async def privat(request, call_next):
    antwort = await call_next(request)
    antwort.headers["Cache-Control"] = "no-store"
    antwort.headers["X-Content-Type-Options"] = "nosniff"
    antwort.headers["Referrer-Policy"] = "no-referrer"
    antwort.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' blob:; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'self'"
    return antwort


async def _inhalt(request: Request, grenze: int):
    daten = bytearray()
    async for teil in request.stream():
        if len(daten) + len(teil) > grenze:
            raise HTTPException(413, "Die Datei oder Anfrage ist zu groß. Bitte aufteilen.")
        daten.extend(teil)
    if not daten:
        raise HTTPException(400, "Die Datei oder Anfrage ist leer.")
    return bytes(daten)


async def _json(request):
    try:
        daten = json.loads(await _inhalt(request, KONFIG["max_json_bytes"]))
        if not isinstance(daten, dict):
            raise ValueError()
        return daten
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(422, "Die Angaben sind nicht lesbar. Bitte Formular und Beträge prüfen.") from None


def _fall(daten):
    try:
        return DokumentFall.model_validate(daten)
    except ValidationError:
        raise HTTPException(422, "Bitte Angaben prüfen: Beträge brauchen höchstens zwei Nachkommastellen, ohne negative Werte; alle Pflichtfelder müssen gültig sein.") from None


def _ticket(fall: DokumentFall, zeit=None):
    zeit = int(time.time()) if zeit is None else zeit
    roh = f"{zeit}:".encode() + fall.model_dump_json().encode()
    return f"{zeit}.{hmac.new(_SCHLUESSEL, roh, hashlib.sha256).hexdigest()}"


def _ticket_pruefen(fall, token):
    try:
        zeit = int(token.split(".", 1)[0])
        return 0 <= time.time() - zeit <= KONFIG["ticket_sekunden"] and hmac.compare_digest(token, _ticket(fall, zeit))
    except (ValueError, AttributeError, TypeError):
        return False


def _lese_prozess(daten, endung):
    with tempfile.TemporaryDirectory(prefix="ksk-dokument-") as ordner:
        pfad = Path(ordner) / ("eingabe" + endung)
        pfad.write_bytes(daten)
        try:
            r = subprocess.run([sys.executable, "-m", "app.dokument_lesen", str(pfad), endung],
                               cwd=WURZEL, capture_output=True, text=True, encoding="utf-8",
                               timeout=KONFIG["zeitlimit_s"], check=True)
            result = json.loads(r.stdout)
        except (subprocess.SubprocessError, ValueError, OSError):
            raise HTTPException(422, "Datei konnte nicht vollständig gelesen werden oder Zeitlimit erreicht. Bitte eine kleinere Datei versuchen.") from None
    if not result.pop("ok", False):
        raise HTTPException(422, result.get("fehler", "Datei nicht lesbar."))
    result["datei_hash"] = hashlib.sha256(daten).hexdigest()
    return result


@app.get("/")
@app.get("/rechnungen")  # frühere Adresse aus der Zeit mit Chat, bleibt gültig
def startseite():
    return FileResponse(WURZEL / "app/static/dokumente.html")


@app.get("/gesundheit")
def gesundheit():
    return {"modus": "dokumente", "llm": False}


@router.get("/dokumente/optionen")
def optionen():
    return {"rechtsformen": AUFTRAGSPARTNER_LESBAR, "jahre": quellen.verfuegbare_jahre(),
            "max_bytes": KONFIG["max_bytes"], "max_positionen": KONFIG["max_positionen"],
            "katalog": [{"text": r["voraussetzung"], "vorbehalt": r["vorbehalt"], "quelle": r["fundstelle"]}
                        for r in quellen.alle_regeln() if r["gruppe"] == "Katalog"]}


@router.post("/dokumente/lesen")
async def dokument_lesen(request: Request, endung: str):
    if endung not in KONFIG["endungen"]:
        raise HTTPException(415, "Bitte PDF, PNG, JPG, XLSX oder UTF-8-CSV hochladen. Ältere XLS-Dateien bitte zuerst als XLSX speichern.")
    if _PLAETZE.locked():
        raise HTTPException(429, "Gerade werden andere Dokumente gelesen. Bitte gleich erneut versuchen.")
    async with _PLAETZE:
        daten = await _inhalt(request, KONFIG["max_bytes"])
        result = await run_in_threadpool(_lese_prozess, daten, endung)
    result["pruefung"] = ["regeln"] * len(result["positionen"])
    return result


@router.post("/dokumente/vorbereiten")
async def dokument_vorbereiten(request: Request):
    fall = _fall(await _json(request))
    try:
        result = await run_in_threadpool(vorbereiten, fall)
    except ValidationError:
        raise HTTPException(422, "Bitte ein gültiges Zahlungsjahr und gültige Angaben eintragen.") from None
    if result["bereit"]:
        result["ticket"] = _ticket(fall)
    return result


@router.post("/dokumente/auswerten")
async def dokument_auswerten(request: Request):
    daten = await _json(request)
    fall = _fall(daten.get("fall"))
    if not _ticket_pruefen(fall, daten.get("ticket")):
        raise HTTPException(409, "Die Angaben wurden geändert oder die Bestätigung ist abgelaufen. Bitte erneut prüfen und bestätigen.")
    async with _PLAETZE:
        return await run_in_threadpool(auswerten, fall)


app.include_router(router)
