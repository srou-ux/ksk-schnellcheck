"""Hilfen für die Tests der Gegenrechnung (kein Testmodul)."""
from __future__ import annotations

import json
from decimal import Decimal

from app import gegenrechnung as G
from kern import rechnen as K
from verifier import lauf
from verifier.register import Register


def pruefe_aufrufe(aufrufe, ausfuehren=None, protokoll=None) -> G.Pruefung:
    """Ruft die Kernfunktionen über den Mitschnitt auf (wie der Router) und vergleicht mit der Gegenrechnung.
    Standard: eigener Prozess (app/sandbox.py)."""
    with G.mitschnitt() as m:
        for name, args, kwargs in aufrufe:
            try:
                getattr(G.KERN, name)(*args, **kwargs)
            except K.RegisterLuecke:
                pass
    return G.pruefe(m, protokoll, ausfuehren)


def im_prozess(anfrage: dict, **_) -> dict:
    """Gegenrechnung im selben Prozess (gleiche Logik, ohne Prozessstart) -- für Mutationen der Gegenrechnung."""
    return json.loads(json.dumps(lauf.bearbeite(anfrage, Register.lade())))


def d(x) -> Decimal:
    return Decimal(str(x))
