"""Mehrere Fragen in einer Nachricht (Wunsch des Nutzers, Test im Codespace 16.10.2026: „der Chat soll alle Fragen
beantworten, auch wenn ich sie zusammen sende“).

Die Nachricht wird in einzelne Fragen zerlegt (app/zuordnung.py::zerlege_fragen). Jede Frage ist ein EIGENER Fall –
nichts wird vermischt. Die Fragen werden nacheinander beantwortet:
- Fragen ohne Rückfrage (Auskunft, Rechtsprechung, „Nicht abgedeckt“ …) erscheinen sofort untereinander;
- braucht eine Frage eine Rückfrage oder die Faktenbestätigung, wartet der Rest; sobald dieser Fall fertig ist
  (Knopf, Bestätigung oder getippte Antwort), geht es mit der nächsten Frage weiter.
Die Faktenbestätigung vor jeder Rechnung bleibt (Grundregel: das System rechnet erst nach der Bestätigung).
Nur im Speicher dieses Prozesses (wie die Sitzungen in app/bestaetigung.py), keine Daten auf der Platte."""
from __future__ import annotations

import sys
import threading

from app import bestaetigung, router, zuordnung
from app.ergebnisklassen import FAKTEN_BESTAETIGUNG_NOETIG, RUECKFRAGE_NOETIG
from app.llm.base import LLM
from app.router import Antwort

_SPERRE = threading.Lock()
_OFFEN: dict[str, list[str]] = {}  # Sitzung des laufenden Falls -> noch offene Fragen
_NUMMER: dict[str, tuple[int, int]] = {}  # Sitzung -> (Nummer der laufenden Frage, Zahl aller Fragen)


def _wartet(antwort: Antwort) -> bool:
    """Braucht der Fall noch eine Eingabe des Nutzers (Rückfrage, Faktenbestätigung)?"""
    return antwort.ergebnisklasse in (RUECKFRAGE_NOETIG, FAKTEN_BESTAETIGUNG_NOETIG) and bool(antwort.sitzungskennung)


def _kopf(nr: int, gesamt: int, frage: str) -> str:
    return f"**Frage {nr} von {gesamt}:** {frage}"


def _beantworte_ab(fragen: list[str], start_nr: int, gesamt: int, llm: LLM, davor: list[str]) -> Antwort:
    """Beantwortet die Fragen der Reihe nach, bis eine auf den Nutzer wartet. `davor`: schon fertige Antworttexte."""
    texte = list(davor)
    for i, frage in enumerate(fragen):
        nr = start_nr + i
        # Jede Frage ist ein eigener Fall. Der Verlauf der Oberfläche (mit der Sammelnachricht) gehört nicht dazu:
        # die Sitzung beginnt hinter jedem möglichen Verlaufseintrag, das Modell bekommt nur Fallstand + Frage.
        sitzung = bestaetigung.SPEICHER.neue_sitzung(verlauf_start=sys.maxsize)
        antwort = router.bearbeite_frage(frage, llm, [], sitzung)
        texte.append(f"{_kopf(nr, gesamt, frage)}\n{antwort.antwort}")
        if _wartet(antwort):
            rest = fragen[i + 1:]
            if rest:
                with _SPERRE:
                    _OFFEN[antwort.sitzungskennung] = rest
                    _NUMMER[antwort.sitzungskennung] = (nr, gesamt)
                texte[-1] += (f"\n\n*Danach folgen noch {len(rest)} weitere Frage(n) aus Ihrer Nachricht.*")
            antwort.antwort = "\n\n---\n\n".join(texte)
            return antwort
    antwort.antwort = "\n\n---\n\n".join(texte)
    return antwort


def bearbeite_nachricht(frage: str, llm: LLM, verlauf: list[str] | None = None, sitzungskennung: str | None = None,
                        letzte_sitzung: str | None = None) -> Antwort:
    """Wie router.bearbeite_frage; enthält die Nachricht mehrere Fragen, werden alle nacheinander beantwortet."""
    fragen = zuordnung.zerlege_fragen(frage) if zuordnung.mehrere_fragen(frage) else []
    if len(fragen) < 2:
        return weiter(router.bearbeite_frage(frage, llm, verlauf, sitzungskennung, letzte_sitzung=letzte_sitzung),
                      sitzungskennung, llm)
    if sitzungskennung:
        with _SPERRE:  # eine neue Sammelnachricht ersetzt, was aus einer früheren noch offen war
            _OFFEN.pop(sitzungskennung, None)
            _NUMMER.pop(sitzungskennung, None)
    einleitung = (f"Ihre Nachricht enthält {len(fragen)} Fragen. Ich beantworte sie nacheinander, jede als eigenen "
                  "Fall (nichts wird vermischt).")
    return _beantworte_ab(fragen, 1, len(fragen), llm, [einleitung])


def weiter(antwort: Antwort, sitzung_davor: str | None, llm: LLM) -> Antwort:
    """Nach jeder Antwort (Frage, Knopf, Bestätigung): ist der Fall fertig und warten aus derselben Nachricht noch
    Fragen, geht es mit der nächsten weiter. Wartet der Fall noch, wandern die offenen Fragen mit (falls die
    Sitzung wechselt)."""
    kennung = sitzung_davor or antwort.sitzungskennung
    if not kennung:
        return antwort
    with _SPERRE:
        offen = _OFFEN.get(kennung)
        nummer = _NUMMER.get(kennung)
    if not offen:
        return antwort
    if _wartet(antwort):
        if antwort.sitzungskennung and antwort.sitzungskennung != kennung:
            with _SPERRE:
                _OFFEN[antwort.sitzungskennung] = _OFFEN.pop(kennung)
                _NUMMER[antwort.sitzungskennung] = _NUMMER.pop(kennung)
        return antwort
    with _SPERRE:
        _OFFEN.pop(kennung, None)
        _NUMMER.pop(kennung, None)
    nr, gesamt = nummer or (0, len(offen))
    ergebnis = _beantworte_ab(offen, nr + 1, gesamt, llm, [antwort.antwort])
    return ergebnis
