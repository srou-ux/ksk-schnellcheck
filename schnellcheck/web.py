"""KSK-Schnellcheck – Webserver (WSGI, nur Python-Standardbibliothek).

Seiten:  GET /                Schnellcheck-Seite
         GET /api/optionen    Auswahlfelder aus dem Regelwerk
         POST /api/pruefen    Prüfung mit dem Regelkern
         GET /gesundheit      Lebenszeichen

Start lokal (Windows):   python -m schnellcheck            -> http://127.0.0.1:8100
Start Server:            waitress-serve --host 0.0.0.0 --port 8100 schnellcheck.web:app

Datenschutz: keine Anmeldung, keine Cookies, keine externen Dateien. Angaben werden nur für die Prüfung im
Speicher gehalten, nicht gespeichert und nicht ins Log geschrieben. Kein Sprachmodell, kein Netz zur Laufzeit.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from schnellcheck import pruefung

STATIC = Path(__file__).resolve().parent / "static"
MAX_BYTES = 64 * 1024
_PLAETZE = threading.BoundedSemaphore(int(os.environ.get("SCHNELLCHECK_PARALLEL", "4")))
# Link zum ausführlichen SaaS-Angebot (Rechnungen hochladen); leer = Hinweis ohne Link.
SAAS_URL = os.environ.get("SCHNELLCHECK_SAAS_URL", "")

KOEPFE = [
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "no-referrer"),
    ("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' "
     "'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; "
     "form-action 'self'"),
    ("Permissions-Policy", "camera=(), microphone=(), geolocation=()"),
]

_optionen_cache: bytes | None = None


def _antwort(start_response, status: str, body: bytes, typ: str, cache: str = "no-store"):
    start_response(status, [("Content-Type", typ), ("Content-Length", str(len(body))),
                            ("Cache-Control", cache), *KOEPFE])
    return [body]


def _json(start_response, status: str, daten) -> list[bytes]:
    body = json.dumps(daten, ensure_ascii=False, default=str).encode("utf-8")
    return _antwort(start_response, status, body, "application/json; charset=utf-8")


def _fehler(start_response, status: str, text: str):
    return _json(start_response, status, {"fehler": text})


def _lies_json(environ) -> dict:
    try:
        laenge = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        laenge = 0
    if laenge <= 0:
        raise ValueError("Die Anfrage ist leer.")
    if laenge > MAX_BYTES:
        raise OverflowError("Zu viele Angaben auf einmal. Bitte weniger Positionen eintragen.")
    roh = environ["wsgi.input"].read(laenge)
    daten = json.loads(roh.decode("utf-8"))
    if not isinstance(daten, dict):
        raise ValueError("Die Angaben sind nicht lesbar.")
    return daten


def app(environ, start_response):
    pfad = environ.get("PATH_INFO", "/") or "/"
    methode = environ.get("REQUEST_METHOD", "GET")

    if methode == "GET" and pfad in ("/", "/index.html"):
        return _antwort(start_response, "200 OK", (STATIC / "index.html").read_bytes(), "text/html; charset=utf-8")
    if methode == "GET" and pfad == "/gesundheit":
        return _json(start_response, "200 OK", {"modus": "schnellcheck", "llm": False})
    if methode == "GET" and pfad == "/api/optionen":
        global _optionen_cache
        if _optionen_cache is None:
            _optionen_cache = json.dumps({**pruefung.optionen(), "saas_url": SAAS_URL},
                                         ensure_ascii=False).encode("utf-8")
        return _antwort(start_response, "200 OK", _optionen_cache, "application/json; charset=utf-8")
    if pfad == "/api/pruefen":
        if methode != "POST":
            return _fehler(start_response, "405 Method Not Allowed", "Bitte über das Formular prüfen.")
        try:
            daten = _lies_json(environ)
        except OverflowError as x:
            return _fehler(start_response, "413 Payload Too Large", str(x))
        except (ValueError, UnicodeDecodeError):
            return _fehler(start_response, "422 Unprocessable Entity", "Die Angaben sind nicht lesbar.")
        if not _PLAETZE.acquire(timeout=10):
            return _fehler(start_response, "429 Too Many Requests", "Gerade sind viele Prüfungen gleichzeitig. Bitte gleich noch einmal.")
        try:
            return _json(start_response, "200 OK", pruefung.pruefe(daten))
        except ValueError as x:
            return _fehler(start_response, "422 Unprocessable Entity", str(x))
        except Exception:  # noqa: BLE001 – Besucher sieht nie einen Stacktrace; Inhalte werden nicht geloggt
            return _fehler(start_response, "500 Internal Server Error",
                           "Die Prüfung konnte nicht abgeschlossen werden. Bitte später erneut versuchen.")
        finally:
            _PLAETZE.release()
    return _fehler(start_response, "404 Not Found", "Seite nicht gefunden.")
