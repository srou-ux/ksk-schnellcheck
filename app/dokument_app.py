"""Bereich „Rechnungen prüfen“ (Dokumentenmodus). Seit 17.10.2026 Teil der gemeinsamen App (app/main.py hängt `router`
ein, Seite /rechnungen); `app` bleibt als eigenständige Variante für Tests und den Betrieb ohne Chat.

Start (gemeinsam): python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Start (nur Dokumente): python -m uvicorn app.dokument_app:app --host 127.0.0.1 --port 8000
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
# 17.10.2026: KI-Unterstützung beim Lesen. app/main.py setzt hier das Sprachmodell der gemeinsamen App (Mistral oder
# Demo-Modus); die eigenständige Variante bleibt ohne KI (None).
LLM_GEBER = None
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
def startseite():
    return FileResponse(WURZEL / "app/static/dokumente.html")


@app.get("/gesundheit")
def gesundheit():
    return {"modus": "dokumente", "llm": False}


def _llm():
    return LLM_GEBER() if (LLM_GEBER is not None and KONFIG.get("ki_verwenden")) else None


@router.get("/dokumente/optionen")
def optionen():
    from app.llm.fake import FakeLLM

    llm = _llm()
    return {"rechtsformen": AUFTRAGSPARTNER_LESBAR, "jahre": quellen.verfuegbare_jahre(),
            "ki_verfuegbar": llm is not None and not isinstance(llm, FakeLLM),
            "max_bytes": KONFIG["max_bytes"], "max_positionen": KONFIG["max_positionen"],
            "katalog": [{"text": r["voraussetzung"], "vorbehalt": r["vorbehalt"], "quelle": r["fundstelle"]}
                        for r in quellen.alle_regeln() if r["gruppe"] == "Katalog"]}


@router.post("/dokumente/lesen")
async def dokument_lesen(request: Request, endung: str, ki: int = 1):
    if endung not in KONFIG["endungen"]:
        raise HTTPException(415, "Bitte PDF, PNG, JPG, XLSX oder UTF-8-CSV hochladen. Ältere XLS-Dateien bitte zuerst als XLSX speichern.")
    if _PLAETZE.locked():
        raise HTTPException(429, "Gerade werden andere Dokumente gelesen. Bitte gleich erneut versuchen.")
    async with _PLAETZE:
        daten = await _inhalt(request, KONFIG["max_bytes"])
        result = await run_in_threadpool(_lese_prozess, daten, endung)
    llm = _llm() if ki else None
    from app import dokument_ki

    ordnung = await run_in_threadpool(dokument_ki.ordne, result["text"], result["positionen"], llm, KONFIG["ki_max_text"])
    result["positionen"] = ordnung["positionen"]
    result["pruefung"] = ordnung["pruefung"]
    hinweise = result["hinweise"]
    if ordnung["positionen"]:
        # Live-Test 17.10.2026: „Keine eindeutigen Positionen erkannt“ stammt von der Regel-Erkennung und ist falsch, wenn
        # die KI Positionen gefunden hat.
        hinweise = [h for h in hinweise if not h.startswith("Keine eindeutigen Positionen erkannt")]
    result["hinweise"] = [*hinweise, *ordnung["hinweise"]]
    result["ki"] = ordnung["ki"]
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
