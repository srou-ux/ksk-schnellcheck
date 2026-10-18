"""Aufrufe an Mistral. Der Schlüssel steht nur im Header, nie im Bericht."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from extraktion.felder import konfig


class Schnittstellenfehler(RuntimeError):
    def __init__(self, status: int, hinweis: str):
        self.status = status
        super().__init__(f"Mistral-Aufruf {status}: {hinweis}")


def post_json(pfad: str, koerper: dict, schluessel: str, *, timeout: int = 90) -> dict:
    adresse = konfig()["endpunkt"].rstrip("/") + pfad
    anfrage = urllib.request.Request(
        adresse,
        data=json.dumps(koerper).encode("utf-8"),
        headers={"Authorization": "Bearer " + schluessel, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(anfrage, timeout=timeout) as antwort:
            return json.loads(antwort.read().decode("utf-8"))
    except urllib.error.HTTPError as fehler:
        if fehler.code == 429:
            time.sleep(2)
            try:
                with urllib.request.urlopen(anfrage, timeout=timeout) as antwort:
                    return json.loads(antwort.read().decode("utf-8"))
            except urllib.error.HTTPError as erneut:
                text = erneut.read().decode("utf-8", errors="replace")[:300]
                raise Schnittstellenfehler(erneut.code, text) from None
        text = fehler.read().decode("utf-8", errors="replace")[:300]
        raise Schnittstellenfehler(fehler.code, text) from None
