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
    (pathlib.Path(__file__).with_name("testsuite_adversarial_130.json"), pathlib.Path(__file__).with_name("ergebnis_adversarial_130.txt")),
)

PAARE = (
    ("V-119", "V-120"),
    ("V-123", "V-124"),
    ("V-092", "V-093"),
    ("V-082", "V-083"),
    ("V-061", "V-101"),
)
SPERRE_AUSBREITUNG = ("V-122", "V-125")

# Wenn das erwartete „warum“ einen dieser Anker nennt, muss der Kern denselben Grund benennen.
# Trifft kein Anker, wird der Grund nicht automatisch gewertet; der Text steht trotzdem im Bericht.
_GRUND_ANKER = (
    (("summenfehler", "rechenprobe", "positionssumme", "kopfsumme", "betragswiderspruch", "0,02"),
     ("summe", "rechenprobe", "brutto", "toleranz", "differenz")),
    (("doppelt", "pos-nr", "positionsnummer"), ("positionsnummer", "doppelt")),
    (("kleinunternehmer", "§19", "paragraf 19"), ("kleinunternehmer", "19")),
    (("skonto",), ("skonto",)),
    (("waehrung", "fremdwaehrung", "kurs"), ("waehrung", "umrechnung", "kurs")),
    (("storno", "saldierung"), ("storno", "saldier")),
    (("fussnote", "fußnote"), ("fussnote", "fusnote", "uebertraegt")),
    (("schwelle nicht", "keine schwelle", "nicht hinterlegt", "schwellenblatt"),
     ("schwelle", "nicht abgedeckt", "quelle fehlt")),
    (("rechtsform", "gmbh", "gesellschaftsform"), ("kapital", "gmbh", "gesellschaft", "handels")),
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


def _grundtext(ergebnis) -> str:
    teile = list(getattr(ergebnis, "begruendung", []) or [])
    teile += list(getattr(ergebnis, "rueckfragen", []) or [])
    teile += list(getattr(ergebnis, "regeln", []) or [])
    return " ".join(str(teil) for teil in teile if teil)


def _norm(text: str) -> str:
    return (text or "").lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")


def grund_passt(warum: str, kern_grund: str) -> bool | None:
    """True/False, wenn ein Anker im erwarteten Grund steht. None, wenn keiner zutrifft."""
    frage = _norm(warum)
    antwort = _norm(kern_grund)
    getroffen = False
    for ausloeser, erwartet in _GRUND_ANKER:
        if any(wort in frage for wort in ausloeser):
            getroffen = True
            if not any(wort in antwort for wort in erwartet):
                return False
    return True if getroffen else None


def messe(test: dict, *, grenzfall_zaehlt: bool = True, taetigkeit: bool = False) -> tuple[str, str, str]:
    """Liefert (Suite-Status aus dem Kern, Klassenname, Begründungstext)."""
    txt = test["txt"]
    low = txt.lower()
    jahr = _jahr(txt)
    betrag = _betrag(test)
    kat = test.get("kat", "")
    try:
        sperre = K.pruefe_sperre(txt, jahr)
        if sperre is not None:
            return _aus_klasse(sperre.klasse), sperre.klasse, _grundtext(sperre)
        klar = K.pruefe_klarstellung(txt, betrag, jahr)
        if klar is not None:
            return _aus_klasse(klar.klasse), klar.klasse, _grundtext(klar)
        beleg = K.pruefe_beleg(txt, betrag, jahr)
        if beleg is not None:
            if beleg.klasse == K.NICHT:
                return "AUSGENOMMEN", beleg.klasse, _grundtext(beleg)
            return _aus_klasse(beleg.klasse), beleg.klasse, _grundtext(beleg)
        if "übungsleiter" in low or "uebungsleiter" in low:
            modus = "rueckfrage" if ("überschritten" in low or "ueberschritten" in low) and "nicht überschritten" not in low and "nicht ueberschritten" not in low else "rechnen"
            bg, ergebnis = K.uebungsleiter_bg(jahr, betrag, bestaetigung=True, bei_ueberschreitung=modus)
            if ergebnis.klasse == K.NICHT and bg == 0:
                return "AUSGENOMMEN", ergebnis.klasse, _grundtext(ergebnis)
            return _aus_klasse(ergebnis.klasse), ergebnis.klasse, _grundtext(ergebnis)
        if "vermittlung ohne weitere" in low or "gelegenheitsnachweis" in low:
            ergebnis = K.gelegenheitsnachweis()
            if ergebnis.klasse == K.NICHT:
                return "AUSGENOMMEN", ergebnis.klasse, _grundtext(ergebnis)
            return _aus_klasse(ergebnis.klasse), ergebnis.klasse, _grundtext(ergebnis)
        if kat.startswith("8-") and any(
            wort in low for wort in ("eigengeschäft", "eigengeschaeft", "vertragslage unklar", "im auftrag", "inkasso", "scheinselbst")
        ):
            ergebnis = K.vertreter()
            return _aus_klasse(ergebnis.klasse), ergebnis.klasse, _grundtext(ergebnis)
        if "chorleit" in low and "fußnote" not in low and "fussnote" not in low:
            chor = K.pruefe_chorleitung(txt, betrag, jahr)
            if chor is not None:
                if chor.klasse == K.NICHT:
                    return "AUSGENOMMEN", chor.klasse, _grundtext(chor)
                return _aus_klasse(chor.klasse), chor.klasse, _grundtext(chor)
        pos = _position(test)
        aus = K.ausgeschlossene_positionen([pos], jahr)
        if aus:
            grund = aus[0][1]
            if "Kapital" in grund or "Handelsgesellschaft" in grund:
                return "AUSGESCHLOSSEN", K.NICHT, grund
            if pos.get("kuenstlerisch") is False:
                return "AUSGESCHLOSSEN", K.NICHT, grund
            return "AUSGENOMMEN", K.NICHT, grund
        if K.ist_keine_kuenstlerische_taetigkeit(txt, jahr) is True:
            return "AUSGESCHLOSSEN", K.NICHT, "Tätigkeit im Register ausgeschlossen"
        if taetigkeit or kat.startswith(("1-", "2-", "10-", "B-")):
            katalog = K.einordnung_taetigkeit(txt, jahr)
            if katalog is not None:
                return _aus_klasse(katalog.klasse), katalog.klasse, _grundtext(katalog)
        ergebnis = K.pruefe_positionen(jahr, [pos])
        hinweis = K.rundungshinweis(txt, jahr)
        if hinweis:
            ergebnis.begruendung.append(hinweis)
        if grenzfall_zaehlt and ergebnis.klasse == K.GRENZFALL:
            return "ZAEHLT", ergebnis.klasse, _grundtext(ergebnis)
        return _aus_klasse(ergebnis.klasse), ergebnis.klasse, _grundtext(ergebnis)
    except K.RegisterLuecke as exc:
        return "OFFEN", f"RegisterLuecke: {exc}", str(exc)


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
        erhalten, kern, _grund = messe(test)
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


def _kurz(text: str, laenge: int = 140) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= laenge else text[: laenge - 1] + "…"


def _bericht_adversarial(suite: dict, tests: list) -> str:
    zeilen = [
        f"Suite: {suite.get('suite', '')} {suite.get('version', '')} {suite.get('datum', '')}",
        "Gewertet wird der Status und, wo ein Anker im erwarteten Grund steht, die Begründung des Kerns.",
        "Ein Fall ist nur grün, wenn der Status stimmt und der getroffene Anker im Kerntext vorkommt.",
        "",
        f"{'ID':<8} {'erwartet':<14} {'erhalten':<14} {'Grund':<10} {'Kern':<28}",
        "-" * 110,
    ]
    je_kat: dict[str, list[bool]] = {}
    ergebnisse: dict[str, dict] = {}
    fehler: list[str] = []
    for test in tests:
        erhalten, kern, grund = messe(test, grenzfall_zaehlt=False, taetigkeit=True)
        erwartet = test["status"]
        anker = grund_passt(test.get("warum", ""), f"{grund} {kern}")
        status_ok = erhalten == erwartet
        grund_ok = anker is not False
        ok = status_ok and grund_ok
        je_kat.setdefault(test.get("kat", "?"), []).append(ok)
        ergebnisse[test["id"]] = {"ok": ok, "erhalten": erhalten, "grund": grund, "warum": test.get("warum", "")}
        zeilen.append(
            f"{test['id']:<8} {erwartet:<14} {erhalten:<14} "
            f"{('ok' if anker else 'ohne Anker' if anker is None else 'passt nicht'):<10} "
            f"{_kurz(kern, 28):<28} {'✅' if ok else '❌'}"
        )
        if not ok:
            fehler.append(
                f"{test['id']} | {test.get('kat', '')} | erwartet {erwartet} | erhalten {erhalten} | "
                f"Grund {'passt nicht' if anker is False else 'Status'}\n"
                f"  warum: {_kurz(test.get('warum', ''), 220)}\n"
                f"  kern:  {_kurz(grund or kern, 220)}"
            )
    zeilen.append("")
    zeilen.append("Kategorien")
    gesamt_ok = gesamt = 0
    abnahme_ok = True
    for kat, werte in je_kat.items():
        treffer = sum(werte)
        gesamt_ok += treffer
        gesamt += len(werte)
        quote = 100 * treffer / len(werte)
        mindest = 100 if kat.startswith(("K1", "K3")) else 90
        hält = quote + 1e-9 >= mindest
        abnahme_ok = abnahme_ok and hält
        zeilen.append(f"  {kat:<22} {treffer:>3}/{len(werte):<3}  {quote:5.1f} %  Ziel {mindest:>3} %  {'✅' if hält else '❌'}")
    quote = 100 * gesamt_ok / gesamt if gesamt else 0
    zeilen.append("")
    zeilen.append(f"Gesamt {gesamt_ok}/{gesamt}  {quote:.1f} %")
    zeilen.append("")
    zeilen.append("Paar-Check (beide müssen stimmen)")
    for links, rechts in PAARE:
        beide = ergebnisse.get(links, {}).get("ok") and ergebnisse.get(rechts, {}).get("ok")
        zeilen.append(f"  {links}/{rechts}: {'beide richtig' if beide else 'FEHLER'} {'✅' if beide else '❌'}")
        if not beide:
            abnahme_ok = False
    zeilen.append("")
    zeilen.append("Sperre-Ausbreitung")
    for fall_id in SPERRE_AUSBREITUNG:
        zeile = ergebnisse.get(fall_id, {})
        sperrt = zeile.get("erhalten") == "SPERRE" and zeile.get("ok")
        zeilen.append(f"  {fall_id}: {'sperrt das Dokument' if sperrt else 'sperrt nicht'} {'✅' if sperrt else '❌'}")
        if not sperrt:
            abnahme_ok = False
    zeilen.append("")
    zeilen.append(f"Abnahme: {'bestanden' if abnahme_ok else 'nicht bestanden'}")
    zeilen.append("")
    zeilen.append(f"Abweichungen ({len(fehler)})")
    zeilen.extend(fehler or ["Keine."])
    return "\n".join(zeilen) + "\n"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    for quelle, ziel in SUITEN:
        suite = json.loads(quelle.read_text(encoding="utf-8"))
        text = _bericht_adversarial(suite, suite["tests"]) if "adversarial" in quelle.name else _bericht(suite, suite["tests"])
        ziel.write_text(text, encoding="utf-8")
        if quelle.name.startswith("testsuite_100"):
            quelle.with_name("ergebnis_testsuite_100.txt").write_text(text, encoding="utf-8")
        print(text, end="")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
