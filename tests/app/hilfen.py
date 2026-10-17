"""Testhilfe (kein Testmodul selbst): fuehrt eine Anfrage durch die Faktenbestaetigung
(Architektur Teil 1d, Abschnitt B) hindurch, genau wie `POST /frage` gefolgt von
`POST /bestaetigen` in app/main.py das tun wuerden. Alle Tests, die ein fertiges Ergebnis
(nicht nur die Bestaetigungs-Rueckfrage) pruefen wollen, nutzen `lauf_bestaetigt` statt
`router.bearbeite_frage` direkt aufzurufen.
"""
from __future__ import annotations

from app import bestaetigung, router
from app.schema import Fakten


def lauf_bestaetigt(llm, frage: str, fakten: Fakten | None = None, verlauf=None) -> router.Antwort:
    if fakten is not None:
        llm.registriere(frage, fakten)
    erste = router.bearbeite_frage(frage, llm, verlauf)
    # Entscheidung 17.10.2026 („Geratenen Zweck immer nachfragen“): wie ein Nutzer den Zweck per Knopf bestätigen,
    # wenn der Text ihn nicht nennt (tests/app/zweck_knopf.py). Das erwartete Ergebnis bleibt gleich.
    from tests.app.zweck_knopf import mit_zweck

    erste = mit_zweck(erste, fakten, llm)
    if erste.sitzungskennung and erste.fakten_hash:
        bestaetigung.SPEICHER.bestaetige(erste.sitzungskennung, erste.fakten_hash)
        return router.fuehre_nach_bestaetigung_aus(erste.sitzungskennung, llm)
    # Kein Bestaetigungsschritt noetig (Rueckfrage/Rechtsprechungsfrage) -- erste Antwort ist final.
    return erste


def gegenrechnung_im_prozess(register_daten: dict | None = None):
    """Teil 1e: Gegenrechnung im SELBEN Prozess (statt app/sandbox.py), wahlweise mit einem geänderten Register.

    Nur für Tests, die das Regelregister des Kerns im Speicher ändern (z. B. `patch.dict(K.P, ...)`, um eine geänderte
    Excel nachzubilden): Im Betrieb lesen Kern und Gegenrechnung dieselbe Datei kern/parameter.json; im Test muss die
    Gegenrechnung dasselbe geänderte Register bekommen, sonst meldet sie zu Recht eine Abweichung."""
    import copy
    import json
    from contextlib import contextmanager
    from pathlib import Path
    from unittest.mock import patch

    from verifier import lauf
    from verifier.register import PARAMETER_PFAD, Register

    @contextmanager
    def _kontext():
        daten = copy.deepcopy(register_daten) if register_daten is not None else json.loads(
            Path(PARAMETER_PFAD).read_text(encoding="utf-8"))

        def ausfuehren(anfrage: dict, **_):
            return json.loads(json.dumps(lauf.bearbeite(anfrage, Register(daten))))

        with patch("app.sandbox.fuehre_aus", ausfuehren):
            yield

    return _kontext()
