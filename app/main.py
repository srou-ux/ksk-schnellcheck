"""FastAPI-Einstiegspunkt (Architektur Punkt 8).

Start: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
Ohne MISTRAL_API_KEY startet die App im Demo-Modus mit FakeLLM (siehe app/README.md).
"""
from __future__ import annotations

import json

import os
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app import bestaetigung, warteschlange
from app.ergebnisklassen import RUECKFRAGE_NOETIG
from app.llm.base import LLM
from app.llm.fake import FakeLLM
from app.router import Antwort, bearbeite_frage, fuehre_nach_bestaetigung_aus, wende_feldantwort_an

STATIC_VERZEICHNIS = Path(__file__).resolve().parent / "static"


def waehle_llm() -> LLM:
    """15.10.2026: jedes Sprachmodell über Umgebungsvariablen (app/llm/anbieter.py, LLM_ANBIETER). Ohne Angabe wie bisher:
    Mistral, wenn MISTRAL_API_KEY gesetzt ist, sonst Demo-Modus."""
    from app.llm.anbieter import waehle_llm as _waehle  # Import erst hier: httpx-Abhaengigkeit nur bei Bedarf

    return _waehle()


app = FastAPI(title="KSK-Chatbot (Prototyp, Entwurf)")


@app.on_event("startup")
def _quellenindex_aktualisieren() -> None:
    """RAG (Teil 2): Quellenindex beim Start aktualisieren (nur geänderte Quellen, lokale Dateien,
    kein Netz) -- VOR der ersten Anfrage, nicht parallel dazu (13.10.2026: ein Aufbau im
    Hintergrund lief gleichzeitig mit der ersten Faktenextraktion; siehe aufgaben/FUNDE_Chatbot.md).
    Der erste Aufbau dauert etwa eine Minute, danach wenige Sekunden."""
    import os

    if os.environ.get("RAG_AUS") == "1":
        return
    try:
        from app.rag import suche as rag_suche
        from app.rag.index import Basis, baue

        with rag_suche._SPERRE:
            baue(Basis())
    except Exception as fehler:  # noqa: BLE001 -- ohne Index läuft der Chatbot weiter (protokolliert)
        print(f"RAG-Index nicht gebaut: {fehler}")


_llm: LLM = waehle_llm()


def _ist_demo_modus() -> bool:
    return isinstance(_llm, FakeLLM)


class FrageEingabe(BaseModel):
    frage: str
    verlauf: Optional[list[str]] = None
    sitzungskennung: Optional[str] = None
    # Test-Dialog 'Der schwierige Kunde': die Sitzung des zuletzt FERTIG geprüften Falls, damit eine
    # Nachfrage dazu ('Das kann nicht stimmen', 'Protokoll') beantwortet werden kann.
    letzte_sitzung: Optional[str] = None


class BestaetigenEingabe(BaseModel):
    sitzungskennung: str
    fakten_hash: str


class KnopfEingabe(BaseModel):
    sitzungskennung: str
    feld: str
    wert: Any
    position: Optional[int] = None


class FrageAntwort(BaseModel):
    antwort: str
    ergebnisklasse: str
    rueckfragen: list[str] = []
    rueckfrage_optionen: list[dict] = []
    fundstellen: list[str] = []
    kern_protokoll: dict = {}
    sitzungskennung: Optional[str] = None
    fakten_hash: Optional[str] = None
    fakten_zusammenfassung: list[str] = []
    # Teil 1e: Prüfprotokoll der unabhängigen Gegenrechnung (Status, Prüfung, Version, Registerzeilen mit Gültigkeit)
    pruefprotokoll: dict = {}
    demo_modus: bool
    modell: str


def _zu_antwort(ergebnis: Antwort) -> FrageAntwort:
    return FrageAntwort(
        antwort=ergebnis.antwort,
        ergebnisklasse=ergebnis.ergebnisklasse,
        rueckfragen=ergebnis.rueckfragen,
        rueckfrage_optionen=ergebnis.rueckfrage_optionen,
        fundstellen=ergebnis.fundstellen,
        kern_protokoll={k: str(v) for k, v in ergebnis.kern_protokoll.items()},
        sitzungskennung=ergebnis.sitzungskennung,
        fakten_hash=ergebnis.fakten_hash,
        fakten_zusammenfassung=ergebnis.fakten_zusammenfassung,
        pruefprotokoll=json.loads(json.dumps(ergebnis.pruefprotokoll, default=str)),
        demo_modus=_ist_demo_modus(),
        modell=_llm.name,
    )


@app.post("/frage", response_model=FrageAntwort)
def frage(eingabe: FrageEingabe) -> FrageAntwort:
    """Liefert bei berechnungsbeduerftigen Anfragen zunaechst nur die vom System
    formulierte Faktenzusammenfassung (ergebnisklasse 'Faktenbestätigung nötig') samt
    `sitzungskennung`/`fakten_hash` -- der Kern wird erst nach POST /bestaetigen
    aufgerufen. Eine Korrektur ist einfach ein erneuter POST /frage mit derselben
    `sitzungskennung` und dem korrigierten Text; das macht die alte Bestaetigung ungueltig
    (app/bestaetigung.py)."""
    # 16.10.2026: mehrere Fragen in einer Nachricht werden nacheinander beantwortet (app/warteschlange.py)
    ergebnis = warteschlange.bearbeite_nachricht(eingabe.frage, _llm, eingabe.verlauf, eingabe.sitzungskennung,
                                                 letzte_sitzung=eingabe.letzte_sitzung)
    return _zu_antwort(ergebnis)


@app.post("/knopf", response_model=FrageAntwort)
def knopf(eingabe: KnopfEingabe) -> FrageAntwort:
    """Pruefkatalog-Befund M1: beantwortet eine geschlossene Rueckfrage-Schaltflaeche
    (z. B. 'Eigenwerbung'/'Typischer Verwerter', eine Rechtsform, 'ja'/'nein') DETERMINISTISCH
    -- ohne erneuten Modellaufruf. `feld`/`wert`/`position` kommen unveraendert aus einem
    `rueckfrage_optionen`-Eintrag einer vorherigen Antwort zurueck (app/pflichtangaben.py,
    app/static/index.html); sie werden hier nicht neu interpretiert, nur angewendet."""
    ergebnis = warteschlange.weiter(
        wende_feldantwort_an(eingabe.sitzungskennung, eingabe.feld, eingabe.wert, _llm, eingabe.position),
        eingabe.sitzungskennung, _llm)
    return _zu_antwort(ergebnis)


@app.post("/bestaetigen", response_model=FrageAntwort)
def bestaetigen(eingabe: BestaetigenEingabe) -> FrageAntwort:
    """Bestaetigt GENAU die zuletzt unter dieser Sitzungskennung gezeigten Fakten (per
    Hash) und ruft erst dann den Kern auf (app/router.py::fuehre_nach_bestaetigung_aus)."""
    if not bestaetigung.SPEICHER.bestaetige(eingabe.sitzungskennung, eingabe.fakten_hash):
        return _zu_antwort(
            Antwort(
                antwort="Die Bestätigung passt nicht (mehr) zu den zuletzt gezeigten Fakten -- bitte Frage erneut stellen.",
                ergebnisklasse=RUECKFRAGE_NOETIG,
                sitzungskennung=eingabe.sitzungskennung,
            )
        )
    ergebnis = warteschlange.weiter(fuehre_nach_bestaetigung_aus(eingabe.sitzungskennung, _llm), eingabe.sitzungskennung, _llm)
    return _zu_antwort(ergebnis)


@app.get("/gesundheit")
def gesundheit() -> dict:
    return {"status": "ok", "demo_modus": _ist_demo_modus(), "modell": _llm.name}


@app.get("/")
def weboberflaeche() -> FileResponse:
    return FileResponse(STATIC_VERZEICHNIS / "index.html")


# 17.10.2026 (Wunsch des Nutzers): zwei Bereiche in einer Oberfläche – „KSK-Chat“ (/) und „Rechnungen prüfen“
# (/rechnungen, app/dokument_app.py). Viele Nutzer wollen nicht chatten, sondern Rechnungen hochladen und prüfen.
from app import dokument_app  # noqa: E402

app.include_router(dokument_app.router)
dokument_app.LLM_GEBER = lambda: _llm  # KI-Unterstützung beim Lesen der Rechnungen (app/dokument_ki.py)


@app.middleware("http")
async def _dokumente_privat(request, call_next):
    """Für den Dokumentenbereich dieselben Schutz-Köpfe wie in der eigenständigen Variante (keine Zwischenspeicherung)."""
    antwort = await call_next(request)
    if request.url.path.startswith(("/dokumente", "/rechnungen")):
        for name, wert in dokument_app.SICHERHEITS_KOEPFE.items():
            antwort.headers[name] = wert
    return antwort


@app.get("/rechnungen")
def rechnungen_pruefen() -> FileResponse:
    return FileResponse(STATIC_VERZEICHNIS / "dokumente.html")
