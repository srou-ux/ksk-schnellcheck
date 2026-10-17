"""Optionale zweite Rangliste über Mistral-Embeddings (EU). Nur aktiv mit RAG_EMBEDDINGS=1
(Index-Aufbau UND Suche). Schlüssel nur aus der Umgebungsvariablen MISTRAL_API_KEY. Ohne Schalter
wird dieses Modul nie aufgerufen; Tests übergeben einen eigenen `einbetter` (kein Netz)."""
from __future__ import annotations

import json
import math
import os
import sqlite3
from typing import Any, Callable

from app.rag.zerlegen import KONFIG

Einbetter = Callable[[list[str]], list[list[float]]]


_STAPEL = 16          # Texte je Anfrage (Grenze der Anfrage-Länge bei Mistral)
_VERSUCHE = 6         # bei 429/5xx: warten und erneut versuchen
_MAX_ZEICHEN = 8000   # Sicherheitsgrenze je Text (Mistral: höchstens 8192 Token je Eingabe)


def mistral_einbetter(texte: list[str]) -> list[list[float]]:
    import time

    import httpx

    schluessel = os.environ.get("MISTRAL_API_KEY")
    if not schluessel:
        raise RuntimeError("RAG_EMBEDDINGS=1, aber MISTRAL_API_KEY fehlt (nur als Umgebungsvariable).")
    erg: list[list[float]] = []
    for i in range(0, len(texte), _STAPEL):
        for versuch in range(_VERSUCHE):
            antwort = httpx.post(KONFIG["embeddings_url"], timeout=60,
                                 headers={"Authorization": f"Bearer {schluessel}"},
                                 json={"model": KONFIG["embeddings_modell"], "input": texte[i:i + _STAPEL]})
            if antwort.status_code in (429, 500, 502, 503) and versuch < _VERSUCHE - 1:
                time.sleep(2 ** versuch)
                continue
            if antwort.status_code >= 400:
                raise RuntimeError(f"Mistral-Embeddings: HTTP {antwort.status_code}: {antwort.text[:300]}")
            break
        erg.extend(d["embedding"] for d in antwort.json()["data"])
    return erg


def ergaenze_vektoren(db: sqlite3.Connection, einbetter: Einbetter | None = None) -> int:
    """Vektoren für alle Stücke ohne Vektor (nur neue/geänderte Quellen kosten Aufrufe)."""
    einbetter = einbetter or mistral_einbetter
    offen = db.execute("SELECT id, fundstelle, text FROM stuecke WHERE id NOT IN (SELECT id FROM vektoren)").fetchall()
    for i in range(0, len(offen), 64):
        teil = offen[i:i + 64]
        vektoren = einbetter([f"{f}\n{t}"[:_MAX_ZEICHEN] for _, f, t in teil])
        db.executemany("INSERT OR REPLACE INTO vektoren VALUES (?, ?)",
                       [(sid, json.dumps(v)) for (sid, _, _), v in zip(teil, vektoren)])
        db.commit()  # Zwischenstand sichern: ein Abbruch kostet keine bereits bezahlten Aufrufe
    return len(offen)


_CACHE: dict[str, Any] = {}


def _alle_vektoren(db: sqlite3.Connection) -> dict[int, Any]:
    """Alle Vektoren einmal je Indexstand in den Speicher (mit numpy, wenn vorhanden)."""
    datei = db.execute("PRAGMA database_list").fetchone()[2]
    stand = f"{datei}:{db.execute('SELECT count(*), max(id) FROM vektoren').fetchone()}"
    if _CACHE.get("stand") != stand:
        try:
            import numpy as np
        except ImportError:
            np = None
        vektoren = {}
        for sid, v in db.execute("SELECT id, vektor FROM vektoren"):
            werte = json.loads(v)
            if np is not None:
                arr = np.asarray(werte, dtype="float32")
                vektoren[sid] = arr / (float(np.linalg.norm(arr)) or 1.0)
            else:
                vektoren[sid] = werte
        _CACHE.clear()
        _CACHE.update(stand=stand, vektoren=vektoren, np=np)
    return _CACHE


def _kosinus(a: list[float], b: list[float]) -> float:
    za = math.sqrt(sum(x * x for x in a)) or 1.0
    zb = math.sqrt(sum(x * x for x in b)) or 1.0
    return sum(x * y for x, y in zip(a, b)) / (za * zb)


def vektor_rangliste(db: sqlite3.Connection, frage: str, where: str, args: list[Any],
                     einbetter: Einbetter | None = None) -> list[sqlite3.Row]:
    """Stücke (mit demselben Jahres-/Statusfilter wie die Stichwortsuche) nach Ähnlichkeit."""
    ids = [r[0] for r in db.execute(f"SELECT s.id FROM stuecke s JOIN vektoren v ON v.id = s.id WHERE {where}", args)]
    if not ids:
        return []
    cache = _alle_vektoren(db)
    frage_vektor = (einbetter or mistral_einbetter)([frage])[0]
    np = cache["np"]
    if np is not None:
        q = np.asarray(frage_vektor, dtype="float32")
        q = q / (float(np.linalg.norm(q)) or 1.0)
        matrix = np.stack([cache["vektoren"][i] for i in ids])
        punkte = matrix @ q
        reihenfolge = [ids[i] for i in np.argsort(-punkte)[: int(KONFIG["fts_kandidaten"])]]
    else:
        reihenfolge = sorted(ids, key=lambda i: -_kosinus(frage_vektor, cache["vektoren"][i]))[: int(KONFIG["fts_kandidaten"])]
    zeilen = {r["id"]: r for r in db.execute(
        f"SELECT * FROM stuecke WHERE id IN ({','.join('?' * len(reihenfolge))})", reihenfolge)}
    return [zeilen[i] for i in reihenfolge if i in zeilen]
