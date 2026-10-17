"""Vergleich Kern ↔ unabhängige Gegenrechnung (Chatbot Teil 1e, Abschnitt A.5/A.6).

Ablauf je Anfrage (app/router.py::_nach_bestaetigung):
1. Der Router ruft den Kern über `KERN` auf. Innerhalb von `mitschnitt()` wird jeder Aufruf einer Rechenfunktion des
   Kerns mitgeschrieben: Name, Eingaben (als JSON) und das Ergebnis in einheitlicher Form.
2. `pruefe()` schickt NUR die Eingaben an die Gegenrechnung (verifier/, eigener Prozess über app/sandbox.py). Das
   Kernergebnis bekommt sie nicht.
3. Ergebnisklasse und jede Zahl müssen exakt gleich sein. Zusätzlich muss jede Zahl im Kernprotokoll aus einem
   gegengerechneten Aufruf stammen (Zahlen-Herkunft).

Ausgang (`Pruefung.status`):
- 'bestaetigt': alles gleich -> die Antwort trägt eine kurze Prüfzeile und das Prüfprotokoll.
- 'abweichung' oder 'fehlgeschlagen' (Fehler, Zeitüberschreitung, zu große Eingabe): die Antwort wird NICHT
  ausgegeben ('Prüfung fehlgeschlagen'), Eintrag ins Lückenprotokoll.
- 'nicht_gegengerechnet': ein Aufruf oder eine Zahl ist von der Gegenrechnung nicht abgedeckt -> das wird offen
  gesagt, nie stillschweigend 'bestätigt'.
- 'ohne_rechnung': kein Kern-Aufruf (z. B. Rückfrage vor jeder Rechnung) -> keine Prüfzeile."""
from __future__ import annotations

import contextvars
import datetime
import hashlib
import inspect
import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Callable

from kern import rechnen as _K

from app import sandbox

_KLASSEN = {_K.ABGABEPFLICHTIG: "ABG", _K.NICHT: "NICHT", _K.GRENZFALL: "GRENZ", _K.RUECKFRAGE: "RUECK",
            _K.NICHT_ABGEDECKT: "LUECKE"}
LUECKE = "LUECKE"

# Alle öffentlichen Funktionen des Kerns gelten als Rechenfunktionen (Name aus dem echten Modul, damit auch ein in
# Tests ersetztes Attribut mitgeschrieben wird). Was die Gegenrechnung nicht kennt, wird 'nicht gegengerechnet'.
RECHENFUNKTIONEN = frozenset(n for n, f in vars(_K).items() if inspect.isfunction(f) and not n.startswith("_")
                             and f.__module__ == _K.__name__)


@dataclass
class Aufruf:
    name: str
    args: list
    kwargs: dict
    kern: dict


@dataclass
class Mitschnitt:
    aufrufe: list[Aufruf] = field(default_factory=list)


_AKTIV: contextvars.ContextVar[Mitschnitt | None] = contextvars.ContextVar("gegenrechnung_mitschnitt", default=None)


@contextmanager
def mitschnitt():
    m = Mitschnitt()
    marke = _AKTIV.set(m)
    try:
        yield m
    finally:
        _AKTIV.reset(marke)


# ---------------------------------------------------------------------------------------------------------------------
# JSON-Form der Eingaben und einheitliche Form der Ergebnisse
# ---------------------------------------------------------------------------------------------------------------------
def als_json(x: Any) -> Any:
    if isinstance(x, bool) or x is None or isinstance(x, (int, str)):
        return x
    if isinstance(x, (Decimal, float)):
        return {"$d": str(x)}
    if isinstance(x, (datetime.date, datetime.datetime)):
        return {"$datum": x.isoformat()}
    if isinstance(x, dict):
        return {str(k): als_json(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        return [als_json(v) for v in x]
    return {"$unbekannt": type(x).__name__}


def _klasse(e) -> str:
    return _KLASSEN.get(getattr(e, "klasse", None), f"? {getattr(e, 'klasse', None)}")


def _voll(e) -> dict:
    return {"klasse": _klasse(e), "bg": e.bemessungsgrundlage, "abgabe": e.abgabe}


_FORM: dict[str, Callable[[Any], dict]] = {
    "pruefe_eigenwerbung": _voll, "pruefe_typischer_verwerter": _voll, "pruefe_positionen": _voll,
    "bemessung_positionen": _voll, "veranstaltungen": _voll,
    "privater_auftraggeber": lambda e: {"klasse": _klasse(e)},
    "nachweismakler": lambda e: {"klasse": _klasse(e)},
    "vertreter": lambda e: {"klasse": _klasse(e)},
    "saeumniszuschlag": lambda e: {"klasse": _klasse(e), "abgabe": e.abgabe},
    "vorauszahlung_monatlich": lambda r: {"betrag": r[0], "klasse": _klasse(r[1])},
    "verpflegung": lambda r: {"nicht_zaehlend": r[0], "klasse": _klasse(r[1])},
    "uebungsleiter_bg": lambda r: {"bg_rueck": r[0], "klasse": _klasse(r[1]), "bg": r[1].bemessungsgrundlage,
                                   "abgabe": r[1].abgabe},
    "analysiere_rechnung": lambda r: {"klasse": _klasse(r[0]), "bg": r[0].bemessungsgrundlage, "abgabe": r[0].abgabe,
                                      "offen": sum((z["offen"] for z in r[1]), Decimal(0))},
    "berechne_abgabe": lambda r: {"abgabe": r[0]},
    "schwelle": lambda s: {"euro": Decimal(str(s["euro"])) if s else None, "fassung": s["fassung"] if s else None},
    "meldefrist": lambda d: {"datum": d.isoformat()},
    "aufbewahrung_bis": lambda d: {"datum": d.isoformat()},
    "reg": lambda z: {"wert": str(z["wert"]), "operator": z["operator"]},
}
for _name in ("summe_positionen", "netto", "restbetrag", "kommission_bg", "schaetzung_ausland", "wert", "abgabesatz"):
    _FORM[_name] = lambda x: {"zahl": x}


def einheitlich(name: str, ergebnis: Any) -> dict:
    form = _FORM.get(name)
    if form is None:
        return {"$ohne_form": True}
    return form(ergebnis)


class _KernMitMitschnitt:
    """Steht im Router an der Stelle des Kern-Moduls. Konstanten und Klassen werden durchgereicht; Aufrufe von
    Rechenfunktionen werden innerhalb von `mitschnitt()` mitgeschrieben (außerhalb: unverändert)."""

    def __getattr__(self, name: str):
        obj = getattr(_K, name)
        if name not in RECHENFUNKTIONEN or not callable(obj):
            return obj

        def aufruf(*args, **kwargs):
            m = _AKTIV.get()
            if m is None:
                return obj(*args, **kwargs)
            eingabe_args, eingabe_kwargs = als_json(list(args)), als_json(kwargs)
            try:
                ergebnis = obj(*args, **kwargs)
            except _K.RegisterLuecke:
                m.aufrufe.append(Aufruf(name, eingabe_args, eingabe_kwargs, {"klasse": LUECKE}))
                raise
            m.aufrufe.append(Aufruf(name, eingabe_args, eingabe_kwargs, einheitlich(name, ergebnis)))
            return ergebnis

        return aufruf


KERN = _KernMitMitschnitt()


def notiere(name: str, args: list, ergebnis: dict) -> None:
    """Eine Rechnung, die der Router selbst macht (nicht der Kern), zur Gegenrechnung anmelden."""
    m = _AKTIV.get()
    if m is not None:
        m.aufrufe.append(Aufruf(name, als_json(list(args)), {}, ergebnis))


# ---------------------------------------------------------------------------------------------------------------------
# Vergleich
# ---------------------------------------------------------------------------------------------------------------------
@dataclass
class Pruefung:
    status: str
    grund: str = ""
    abweichungen: list[str] = field(default_factory=list)
    protokoll: dict[str, Any] = field(default_factory=dict)
    nur_nachschlagen: bool = False  # alle Aufrufe lesen nur Werte aus dem Register (Auskunft), keine Rechnung

    @property
    def gibt_aus(self) -> bool:
        return self.status not in ("abweichung", "fehlgeschlagen")


def _wert_aus(x: Any) -> Any:
    """Antwort der Gegenrechnung -> Python (Dezimaltext als Decimal; nicht abbrechender Bruch bleibt Text)."""
    if isinstance(x, dict):
        if set(x) == {"$d"}:
            return Decimal(x["$d"])
        if set(x) == {"$bruch"}:
            return f"Bruch {x['$bruch']}"
        return {k: _wert_aus(v) for k, v in x.items()}
    return x


def _gleich(a: Any, b: Any) -> bool:
    if isinstance(a, Decimal) and isinstance(b, Decimal):
        return a == b
    if isinstance(a, (Decimal, int)) and isinstance(b, (Decimal, int)) and not isinstance(a, bool) \
            and not isinstance(b, bool):
        return Decimal(a) == Decimal(b)
    return a == b


def vergleiche(kern: dict, gegen: dict) -> list[str]:
    """Unterschiede zwischen beiden Ergebnissen (leer = gleich). Fehlt eine Registerzeile ('Nicht abgedeckt'), zählt
    nur die Klasse."""
    if "nicht_abgedeckt" in gegen or "$ohne_form" in kern:
        return ["nicht gegengerechnet"]
    if kern.get("klasse") == LUECKE or gegen.get("klasse") == LUECKE:
        return [] if kern.get("klasse") == gegen.get("klasse") else [f"klasse: Kern {kern.get('klasse')}, Gegenrechnung {gegen.get('klasse')}"]
    return [f"{k}: Kern {kern.get(k)}, Gegenrechnung {gegen.get(k)}"
            for k in sorted(set(kern) | set(gegen)) if not _gleich(kern.get(k), gegen.get(k))]


def _zahlen(x: Any) -> list[Decimal]:
    if isinstance(x, bool):
        return []
    if isinstance(x, (Decimal, int)):
        return [Decimal(x)]
    if isinstance(x, dict):
        return [z for v in x.values() for z in _zahlen(v)]
    if isinstance(x, (list, tuple)):
        return [z for v in x for z in _zahlen(v)]
    return []


def _positionen(args: Any) -> int:
    """Größte Liste in den Eingaben (Positionen, Rückstände)."""
    if isinstance(args, list):
        return max([len(args)] + [_positionen(v) for v in args])
    if isinstance(args, dict):
        return max([0] + [_positionen(v) for v in args.values()])
    return 0


def fall_hash(aufrufe: list[Aufruf]) -> str:
    roh = json.dumps([[a.name, a.args, a.kwargs] for a in aufrufe], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(roh.encode("utf-8")).hexdigest()[:16]


def pruefe(m: Mitschnitt, kern_protokoll: dict[str, Any] | None = None,
           ausfuehren: Callable[[dict], dict] | None = None) -> Pruefung:
    """`ausfuehren`: Standard ist der eigene Prozess (app/sandbox.py, erst beim Aufruf nachgeschlagen). Nur Tests
    geben hier etwas anderes an (z. B. die Gegenrechnung im selben Prozess mit einem geänderten Register)."""
    ausfuehren = ausfuehren or sandbox.fuehre_aus
    if not m.aufrufe:
        return Pruefung("ohne_rechnung")
    k = sandbox.konfiguration()
    kennung = fall_hash(m.aufrufe)
    if len(m.aufrufe) > k["max_aufrufe"] or any(_positionen([a.args, a.kwargs]) > k["max_positionen"] for a in m.aufrufe):
        return Pruefung("fehlgeschlagen", "Eingabe zu groß für die Gegenrechnung (Grenze in app/konfiguration.json)",
                        protokoll={"fall": kennung})
    antwort = ausfuehren({"aufrufe": [{"name": a.name, "args": a.args, "kwargs": a.kwargs} for a in m.aufrufe]})
    if not antwort.get("ok"):
        return Pruefung("fehlgeschlagen", str(antwort.get("fehler") or "unbekannter Fehler"), protokoll={"fall": kennung})
    ergebnisse = [_wert_aus(e) for e in antwort.get("ergebnisse", [])]
    if len(ergebnisse) != len(m.aufrufe):
        return Pruefung("fehlgeschlagen", "Gegenrechnung lieferte nicht zu jedem Aufruf ein Ergebnis",
                        protokoll={"fall": kennung})
    abweichungen, offen = [], []
    for a, g in zip(m.aufrufe, ergebnisse):
        unterschiede = vergleiche(a.kern, g)
        if unterschiede == ["nicht gegengerechnet"]:
            offen.append(a.name)
        elif unterschiede:
            abweichungen.append(f"{a.name}: " + "; ".join(unterschiede))
    protokoll = {"fall": kennung, "pruefung": antwort.get("name"), "version": antwort.get("version"),
                 "aufrufe": [a.name for a in m.aufrufe], "register": antwort.get("register", []),
                 "dauer_ms": round(antwort["dauer_ns"] / 1_000_000, 1) if antwort.get("dauer_ns") is not None else None}
    if abweichungen:
        return Pruefung("abweichung", "; ".join(abweichungen), abweichungen, protokoll)
    # Zahlen-Herkunft: jede Zahl im Kernprotokoll muss aus einem gegengerechneten Aufruf stammen.
    belegt = {z for a in m.aufrufe if a.name not in offen for z in _zahlen(a.kern)}
    ohne_beleg = sorted(schluessel for schluessel, wert in (kern_protokoll or {}).items()
                        if any(z not in belegt for z in _zahlen(wert)))
    if offen or ohne_beleg:
        teile = ([f"Rechenschritt ohne Gegenrechnung: {', '.join(dict.fromkeys(offen))}"] if offen else []) + \
                ([f"Zahl ohne Gegenrechnung: {', '.join(ohne_beleg)}"] if ohne_beleg else [])
        return Pruefung("nicht_gegengerechnet", "; ".join(teile), protokoll=protokoll)
    return Pruefung("bestaetigt", protokoll=protokoll,
                    nur_nachschlagen=all(a.name in NACHSCHLAGEN for a in m.aufrufe))


# Feste Texte (System, nie Modell).
ZEILE_BESTAETIGT = ("**Gegenrechnung:** Die Rechnung wurde unabhängig in einem eigenen Prozess nachgerechnet und stimmt "
                    "überein. Die Einordnung entscheidet der Steuerberater.")
# Diskussion mit dem Nutzer (16.10.2026, Punkt 5): bei einer reinen Auskunft wurde nichts „nachgerechnet“, sondern
# der Wert unabhängig ein zweites Mal aus dem Register gelesen. Namen der Kern-Funktionen, die nur nachschlagen.
NACHSCHLAGEN = frozenset({"abgabesatz", "schwelle", "wert", "werte", "reg"})
ZEILE_NACHGESCHLAGEN = ("**Gegenprüfung:** Der Wert wurde unabhängig in einem eigenen Prozess ein zweites Mal aus "
                        "dem Regelregister gelesen und stimmt überein.")
ZEILE_NICHT_GEGENGERECHNET = "**Gegenrechnung:** Ein Teil dieser Antwort ist nicht gegengerechnet. Bitte manuell prüfen."


def zeile(p: Pruefung) -> str | None:
    if p.status == "bestaetigt":
        return ZEILE_NACHGESCHLAGEN if p.nur_nachschlagen else ZEILE_BESTAETIGT
    if p.status == "nicht_gegengerechnet":
        return ZEILE_NICHT_GEGENGERECHNET
    return None


def text_fehlgeschlagen(p: Pruefung) -> str:
    if p.status == "abweichung":
        return f"Gegenrechnung weicht ab ({p.grund}). Bitte manuell prüfen."
    return f"Gegenrechnung fehlgeschlagen ({p.grund}). Bitte manuell prüfen."
