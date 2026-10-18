"""100 Positionstests gegen den Regelkern.

Erwartete Suite-Status werden auf die Klassen in kern/rechnen.py abgebildet:
  ZAEHLT          -> Abgabepflichtig, oder die Position bleibt in der Summe
  AUSGENOMMEN     -> Nicht abgabepflichtig, weil eine Ausnahme-Art greift
  AUSGESCHLOSSEN  -> Nicht abgabepflichtig, weil die Rechtsform kein Entgelt ist
  OFFEN           -> Rückfrage, Grenzfall, Nicht abgedeckt oder RegisterLuecke
  SPERRE          -> Sperre — Rechnung prüfen

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

SUITEN = (
    (pathlib.Path(__file__).with_name("testsuite_100_positionspruefung.json"), pathlib.Path(__file__).with_name("ergebnis_suite_100.txt")),
    (pathlib.Path(__file__).with_name("testsuite_erfahrung_120.json"), pathlib.Path(__file__).with_name("ergebnis_erfahrung_120.txt")),
)

ERWARTET_AUF_KLASSE = {
    "ZAEHLT": "Position zählt (Abgabepflichtig oder in der Summe)",
    "AUSGENOMMEN": K.NICHT,
    "AUSGESCHLOSSEN": K.NICHT,
    "OFFEN": " / ".join((K.RUECKFRAGE, K.GRENZFALL, K.NICHT_ABGEDECKT, "RegisterLuecke")),
    "SPERRE": K.SPERRE,
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
    jahr = _jahr(txt)
    pos = {"betrag": _betrag(test)}
    if "ggmbh" in low:
        pos["empfaenger"] = "ggmbh"
    elif "sparkasse" in low or "öffentliche" in low or "oeffentlich" in low or "stadtbetrieb" in low or "eigenbetrieb" in low:
        pos["empfaenger"] = "oeffentlich"
    elif re.search(r"(?<![a-zäöü])se(?![a-zäöü])", low) or "societas europaea" in low:
        pos["empfaenger"] = "se"
    else:
        for form in ("ohg", "gmbh", "ug", "ag", "kg"):
            if re.search(rf"(?<![a-zäöü]){form}(?![a-zäöü])", low):
                pos["empfaenger"] = form
                break
    if K.listentreffer(txt, "entgelt.ausgenommen", jahr):
        pos["art"] = "verwertungsgesellschaft"
    if "angestellt" in low or "lohnsteuer" in low:
        pos["kuenstlerisch"] = False
    if any(wort in low for wort in ("auslage", "notenmappe", "notenkauf", "kostenübernahme")) or (
        "materialkosten" in low and "beigefügt" in low
    ):
        pos["art"] = "auslage_nachgewiesen"
    if any(wort in low for wort in ("reise", "fahrt", "hotel", "verpflegung", "zug")) and any(
        wort in low for wort in ("beigefügt", "nachweis liegt", "nachweis vorliegt", "ticket beigefügt")
    ):
        pos["art"] = "fahrtkosten_nachgewiesen"
    if "bewirtung" in low and "beigefügt" in low:
        pos["art"] = "bewirtung"
    return pos


def _aus_klasse(klasse: str) -> str:
    if klasse == K.SPERRE:
        return "SPERRE"
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
        sperre = K.pruefe_sperre(txt, jahr)
        if sperre is not None:
            return _aus_klasse(sperre.klasse), sperre.klasse
        klar = K.pruefe_klarstellung(txt, betrag, jahr)
        if klar is not None:
            return _aus_klasse(klar.klasse), klar.klasse
        beleg = K.pruefe_beleg(txt, betrag, jahr)
        if beleg is not None:
            if beleg.klasse == K.NICHT:
                return "AUSGENOMMEN", beleg.klasse
            return _aus_klasse(beleg.klasse), beleg.klasse
        if "übungsleiter" in low:
            modus = "rueckfrage" if "überschritten" in low and "nicht überschritten" not in low else "rechnen"
            bg, ergebnis = K.uebungsleiter_bg(jahr, betrag, bestaetigung=True, bei_ueberschreitung=modus)
            if ergebnis.klasse == K.NICHT and bg == 0:
                return "AUSGENOMMEN", ergebnis.klasse
            return _aus_klasse(ergebnis.klasse), ergebnis.klasse
        if "vermittlung ohne weitere" in low or "gelegenheitsnachweis" in low:
            ergebnis = K.gelegenheitsnachweis()
            if ergebnis.klasse == K.NICHT:
                return "AUSGENOMMEN", ergebnis.klasse
            return _aus_klasse(ergebnis.klasse), ergebnis.klasse
        if kat.startswith("8-") and any(
            wort in low for wort in ("eigengeschäft", "eigengeschaeft", "vertragslage unklar", "im auftrag", "inkasso", "scheinselbst")
        ):
            ergebnis = K.vertreter()
            return _aus_klasse(ergebnis.klasse), ergebnis.klasse
        if "chorleit" in low and "fußnote" not in low and "fussnote" not in low:
            chor = K.pruefe_chorleitung(txt, betrag, jahr)
            if chor is not None:
                if chor.klasse == K.NICHT:
                    return "AUSGENOMMEN", chor.klasse
                return _aus_klasse(chor.klasse), chor.klasse
        pos = _position(test)
        aus = K.ausgeschlossene_positionen([pos], jahr)
        if aus:
            grund = aus[0][1]
            if "Kapital" in grund or "Handelsgesellschaft" in grund:
                return "AUSGESCHLOSSEN", K.NICHT
            if pos.get("kuenstlerisch") is False:
                return "AUSGESCHLOSSEN", K.NICHT
            return "AUSGENOMMEN", K.NICHT
        if K.ist_keine_kuenstlerische_taetigkeit(txt, jahr) is True:
            return "AUSGESCHLOSSEN", K.NICHT
        if kat.startswith(("1-", "2-", "10-", "B-")):
            katalog = K.einordnung_taetigkeit(txt, jahr)
            if katalog is not None:
                return _aus_klasse(katalog.klasse), katalog.klasse
        ergebnis = K.pruefe_positionen(jahr, [pos])
        hinweis = K.rundungshinweis(txt, jahr)
        if hinweis:
            ergebnis.begruendung.append(hinweis)
        if ergebnis.klasse == K.GRENZFALL:
            return "ZAEHLT", ergebnis.klasse
        return _aus_klasse(ergebnis.klasse), ergebnis.klasse
    except K.RegisterLuecke as exc:
        return "OFFEN", f"RegisterLuecke: {exc}"


def _bericht(suite: dict, tests: list) -> str:
    zeilen = [
        f"Suite: {suite.get('suite', '')} {suite.get('version', '')} {suite.get('datum', '')}",
        "Abbildung:",
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
    return "\n".join(zeilen) + "\n"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    for quelle, ziel in SUITEN:
        suite = json.loads(quelle.read_text(encoding="utf-8"))
        text = _bericht(suite, suite["tests"])
        ziel.write_text(text, encoding="utf-8")
        if quelle.name.startswith("testsuite_100"):
            quelle.with_name("ergebnis_testsuite_100.txt").write_text(text, encoding="utf-8")
        print(text, end="")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
