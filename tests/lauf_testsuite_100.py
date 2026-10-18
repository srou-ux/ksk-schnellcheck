"""100 Positionstests gegen den Regelkern. Der Kern wird nicht verändert.

Erwartete Suite-Status werden auf die Klassen in kern/rechnen.py abgebildet:
  ZAEHLT          -> Abgabepflichtig, oder die Position bleibt in der Summe
  AUSGENOMMEN     -> Nicht abgabepflichtig, weil eine Ausnahme-Art greift
  AUSGESCHLOSSEN  -> Nicht abgabepflichtig, weil die Rechtsform kein Entgelt ist
  OFFEN           -> Rückfrage, Grenzfall, Nicht abgedeckt oder RegisterLuecke
  SPERRE          -> keine Klasse im Kern

Aufruf:  python tests/lauf_testsuite_100.py
"""
from __future__ import annotations

import json
import re
import sys
import pathlib
from decimal import Decimal as D

WURZEL = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
from kern import rechnen as K  # noqa: E402

SUITE = pathlib.Path(__file__).with_name("testsuite_100_positionspruefung.json")
ERGEBNIS = pathlib.Path(__file__).with_name("ergebnis_testsuite_100.txt")

ERWARTET_AUF_KLASSE = {
    "ZAEHLT": "Position zählt (Abgabepflichtig oder in der Summe)",
    "AUSGENOMMEN": K.NICHT,
    "AUSGESCHLOSSEN": K.NICHT,
    "OFFEN": " / ".join((K.RUECKFRAGE, K.GRENZFALL, K.NICHT_ABGEDECKT, "RegisterLuecke")),
    "SPERRE": "keine Klasse im Kern",
}


def _jahr(txt: str) -> int:
    if "Bezugsjahr 2027" in txt:
        return 2027
    treffer = re.findall(r"20\d\d", txt)
    return int(treffer[0]) if treffer else 2026


def _betrag(test: dict) -> D:
    wert = test.get("betrag")
    return D(str(wert)) if wert is not None else D(0)


def _position(test: dict) -> dict:
    txt = test["txt"]
    low = txt.lower()
    pos = {"betrag": _betrag(test)}
    for form in ("ohg", "gmbh", "ug", "ag", "kg"):
        if re.search(rf"(?<![a-zäöü]){form}(?![a-zäöü])", low):
            pos["empfaenger"] = form
            break
    if re.search(r"\bgema\b", low) or "verwertungsgesellschaft" in low:
        pos["art"] = "verwertungsgesellschaft"
    if "angestellt" in low or "lohnsteuer" in low:
        pos["kuenstlerisch"] = False
    if any(wort in low for wort in ("reise", "fahrt", "hotel", "verpflegung", "zug")) and any(
        wort in low for wort in ("beigefügt", "nachweis liegt", "ticket beigefügt")
    ):
        pos["art"] = "fahrtkosten_nachgewiesen"
    if "bewirtung" in low and "beigefügt" in low:
        pos["art"] = "bewirtung"
    if "chorleit" in low and "nicht belegt" not in low and "fußnote" not in low and "fussnote" not in low and "regelmäßig" in low:
        pos["art"] = "vereinseigene_leitung"
    return pos


def _aus_klasse(klasse: str) -> str:
    if klasse in (K.RUECKFRAGE, K.GRENZFALL, K.NICHT_ABGEDECKT):
        return "OFFEN"
    if klasse in (K.ABGABEPFLICHTIG, K.NICHT):
        return "ZAEHLT"
    return "OFFEN"


def messe(test: dict) -> tuple[str, str]:
    """Liefert (Suite-Status aus dem Kern, Klassenname oder Ausnahme)."""
    txt = test["txt"]
    low = txt.lower()
    jahr = _jahr(txt)
    betrag = _betrag(test)
    kat = test.get("kat", "")
    try:
        if "belege nur angekündigt" in low or "nur angekündigt" in low:
            ergebnis = K.reisekosten_ohne_nachweis(betrag)
            return _aus_klasse(ergebnis.klasse), ergebnis.klasse
        if kat.startswith("7-") and "übungsleiter" in low:
            bg, ergebnis = K.uebungsleiter_bg(jahr, betrag, bestaetigung=True)
            if ergebnis.klasse == K.NICHT and bg == 0:
                return "AUSGENOMMEN", ergebnis.klasse
            return _aus_klasse(ergebnis.klasse), ergebnis.klasse
        if "vermittlung ohne weitere" in low or "gelegenheitsnachweis" in low:
            ergebnis = K.nachweismakler()
            return _aus_klasse(ergebnis.klasse), ergebnis.klasse
        if kat.startswith("8-") and any(
            wort in low for wort in ("eigengeschäft", "eigengeschaeft", "vertragslage unklar", "im auftrag", "inkasso", "scheinselbst")
        ):
            ergebnis = K.vertreter()
            return _aus_klasse(ergebnis.klasse), ergebnis.klasse
        if kat.startswith("5-") or "doppelt erfasst" in low:
            ergebnis = K.pruefe_positionen(jahr, [{"betrag": betrag if betrag else D(1)}])
            return _aus_klasse(ergebnis.klasse), ergebnis.klasse
        if "satz nicht belegt" in low:
            ergebnis = K.pruefe_typischer_verwerter(2027, betrag if betrag else D(1))
            return _aus_klasse(ergebnis.klasse), ergebnis.klasse
        pos = _position(test)
        aus = K.ausgeschlossene_positionen([pos], jahr)
        if aus:
            grund = aus[0][1]
            if "Kapital" in grund or "Handelsgesellschaft" in grund:
                return "AUSGESCHLOSSEN", K.NICHT
            if pos.get("kuenstlerisch") is False:
                return "AUSGESCHLOSSEN", K.NICHT
            return "AUSGENOMMEN", K.NICHT
        ergebnis = K.pruefe_positionen(jahr, [pos])
        return _aus_klasse(ergebnis.klasse), ergebnis.klasse
    except K.RegisterLuecke as exc:
        return "OFFEN", f"RegisterLuecke: {exc}"


def main() -> int:
    suite = json.loads(SUITE.read_text(encoding="utf-8"))
    tests = suite["tests"]
    zeilen = [
        f"Suite: {suite.get('suite', '')} {suite.get('version', '')} {suite.get('datum', '')}",
        "Kern unverändert. Abbildung:",
    ]
    for status, klasse in ERWARTET_AUF_KLASSE.items():
        zeilen.append(f"  {status} -> {klasse}")
    zeilen.append("")
    zeilen.append(f"{'ID':<8} {'erwartet':<16} {'erhalten':<16} {'Kern':<42} ")
    zeilen.append("-" * 90)
    je_kat: dict[str, list[bool]] = {}
    for test in tests:
        erhalten, kern = messe(test)
        erwartet = test["status"]
        ok = erhalten == erwartet
        je_kat.setdefault(test.get("kat", "?"), []).append(ok)
        zeilen.append(f"{test['id']:<8} {erwartet:<16} {erhalten:<16} {kern:<42} {'✅' if ok else '❌'}")
    zeilen.append("")
    zeilen.append("Kategorien")
    gesamt_ok = 0
    gesamt = 0
    for kat, werte in je_kat.items():
        treffer = sum(werte)
        gesamt_ok += treffer
        gesamt += len(werte)
        quote = 100 * treffer / len(werte)
        zeilen.append(f"  {kat:<22} {treffer:>3}/{len(werte):<3}  {quote:5.1f} %")
    quote = 100 * gesamt_ok / gesamt if gesamt else 0
    zeilen.append("")
    zeilen.append(f"Gesamt {gesamt_ok}/{gesamt}  {quote:.1f} %")
    text = "\n".join(zeilen) + "\n"
    ERGEBNIS.write_text(text, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
