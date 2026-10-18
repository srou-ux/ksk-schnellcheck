"""Suite 130 über den Regel-Leser und, wenn ein Schlüssel da ist, über Mistral.

Der Kern wird nicht verändert. Hinterlegte Strukturfelder der Suite werden nicht als Lesung verwendet.
"""
from __future__ import annotations

import json
import pathlib
import sys

WURZEL = pathlib.Path(__file__).resolve().parents[1]
if str(WURZEL) not in sys.path:
    sys.path.insert(0, str(WURZEL))

from extraktion.felder import an_kern  # noqa: E402
from extraktion.schnittstelle import extrahiere_dokument  # noqa: E402
from tests.lauf_testsuite_100 import PAARE, SPERRE_AUSBREITUNG, messe  # noqa: E402

SUITE = WURZEL / "tests" / "testsuite_adversarial_130.json"
BERICHT = WURZEL / "tests" / "ergebnis_extraktion_vergleich.txt"
KOSTEN = WURZEL / "tests" / "ergebnis_extraktion_kosten.txt"
_GOLD = ("positionssumme", "kopfsumme", "netto", "ust", "brutto", "gesamtsumme")


def entscheide(test: dict, felder: dict) -> tuple[str, str, str]:
    kopie = {schluessel: wert for schluessel, wert in test.items() if schluessel != "dokument"}
    kopie["dokument"] = an_kern(felder, 2026)
    return messe(kopie, grenzfall_zaehlt=False, taetigkeit=True)


def fehlerquelle(test: dict, felder: dict, erhalten: str) -> str:
    if erhalten == test["status"]:
        return ""
    if felder.get("unsicher") or felder.get("unklare_felder"):
        return "Extraktion"
    gold = test.get("dokument") or {}
    if gold and not _deckt_gold(felder, gold):
        return "Extraktion"
    if not _hat_inhalt(felder):
        return "Extraktion"
    return "Kern"


def _hat_inhalt(felder: dict) -> bool:
    summen = felder.get("summen") or {}
    return any(summen.get(name) for name in _GOLD) or bool(felder.get("rechtsform_angaben") or felder.get("positionen"))


def _deckt_gold(felder: dict, gold: dict) -> bool:
    gelesen = an_kern(felder, 2026)
    for name in _GOLD:
        if (gold.get("summen") or {}).get(name) and not (gelesen.get("summen") or {}).get(name):
            return False
    if gold.get("rechtsformen") and not gelesen.get("rechtsformen"):
        return False
    if gold.get("positionsnummern") and not gelesen.get("positionsnummern"):
        return False
    return True


def _korrektur(quelle: str) -> str:
    if quelle == "Extraktion":
        return "Feld leer oder unsicher gelesen. Nicht mitteln, nicht still übernehmen. Leser nachschärfen."
    if quelle == "Kern":
        return "Felder lagen vor, der Kern hat anders entschieden. Kernregel prüfen, Erwartung nicht verbiegen."
    return ""


def laufe(weg: str, tests: list, **kwargs) -> tuple[list[dict], list[dict]]:
    zeilen = []
    kosten = []
    for test in tests:
        try:
            felder = extrahiere_dokument({"text": test["txt"]}, weg, **kwargs)
        except Exception as fehler:
            zeilen.append({
                "id": test["id"],
                "kat": test.get("kat", ""),
                "erwartet": test["status"],
                "erhalten": "ABBRUCH",
                "ok": False,
                "quelle": "Extraktion",
                "korrektur": "Aufruf abgebrochen: " + str(fehler)[:180],
                "grund": "",
            })
            if getattr(fehler, "status", 0) in (401, 402, 403):
                break
            continue
        erhalten, klasse, grund = entscheide(test, felder)
        quelle = fehlerquelle(test, felder, erhalten)
        zeilen.append({
            "id": test["id"],
            "kat": test.get("kat", ""),
            "erwartet": test["status"],
            "erhalten": erhalten,
            "ok": erhalten == test["status"],
            "quelle": quelle,
            "korrektur": _korrektur(quelle),
            "grund": grund,
        })
        for aufruf in felder.get("kosten") or []:
            kosten.append({"id": test["id"], **aufruf})
    return zeilen, kosten


def bericht(name: str, zeilen: list[dict]) -> str:
    je_kat: dict[str, list[bool]] = {}
    for zeile in zeilen:
        je_kat.setdefault(zeile["kat"], []).append(zeile["ok"])
    teile = [name, ""]
    gesamt_ok = 0
    for kat, werte in je_kat.items():
        treffer = sum(werte)
        gesamt_ok += treffer
        teile.append(f"  {kat:<22} {treffer}/{len(werte)}")
    teile.append(f"Gesamt {gesamt_ok}/{len(zeilen)}")
    teile.append("")
    by_id = {zeile["id"]: zeile for zeile in zeilen}
    teile.append("Paar-Check")
    for links, rechts in PAARE:
        beide = by_id.get(links, {}).get("ok") and by_id.get(rechts, {}).get("ok")
        teile.append(f"  {links}/{rechts}: {'beide richtig' if beide else 'FEHLER'}")
    teile.append("Sperre-Ausbreitung")
    for fall_id in SPERRE_AUSBREITUNG:
        sperrt = by_id.get(fall_id, {}).get("erhalten") == "SPERRE" and by_id.get(fall_id, {}).get("ok")
        teile.append(f"  {fall_id}: {'sperrt das Dokument' if sperrt else 'sperrt nicht'}")
    teile.append("")
    teile.append("Abweichungen")
    for zeile in zeilen:
        if zeile["ok"]:
            continue
        teile.append(
            f"{zeile['id']} | {zeile['kat']} | erwartet {zeile['erwartet']} | erhalten {zeile['erhalten']} "
            f"| {zeile['quelle']} | {zeile['korrektur']}"
        )
    return "\n".join(teile)


def kosten_text(zeilen: list[dict]) -> str:
    seiten = sum(int(zeile.get("seiten") or 0) for zeile in zeilen)
    prompt = sum(int(zeile.get("prompt_tokens") or 0) for zeile in zeilen)
    completion = sum(int(zeile.get("completion_tokens") or 0) for zeile in zeilen)
    teile = [
        "Kostenlog Extraktion. Beträge in Token und Seiten, kein geschätzter Euro-Preis.",
        f"Aufrufe {len(zeilen)} | Seiten {seiten} | Prompt-Token {prompt} | Completion-Token {completion}",
        "",
    ]
    for zeile in zeilen:
        teile.append(
            f"{zeile.get('id', '')} | {zeile.get('stufe', '')} | {zeile.get('modell', '')} | "
            f"Seiten {zeile.get('seiten') or 0} | Prompt {zeile.get('prompt_tokens')} | "
            f"Completion {zeile.get('completion_tokens')}"
        )
    return "\n".join(teile)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    tests = json.loads(SUITE.read_text(encoding="utf-8"))["tests"]
    regel_zeilen, _ = laufe("rule", tests)
    from extraktion.schluessel import schluessel
    mistral_zeilen: list[dict] = []
    kosten: list[dict] = []
    if not schluessel():
        mistral_text = "Mistral nicht gemessen: MISTRAL_API_KEY fehlt."
    else:
        mistral_zeilen, kosten = laufe("mistral", tests)
        abbruch = next((zeile for zeile in mistral_zeilen if zeile["erhalten"] == "ABBRUCH"), None)
        if abbruch or len(mistral_zeilen) != len(tests):
            grund = abbruch["korrektur"] if abbruch else "Lauf unvollständig."
            mistral_text = "Mistral nicht gemessen. " + grund + " Es gibt keine Teilquote."
        else:
            mistral_text = bericht("Mistral OCR 4.1 + Small", mistral_zeilen)
    text = [
        "Vergleich Extraktion, Suite 130. Kern unverändert. Strukturfelder der Suite werden nicht als Lesung benutzt.",
        "Fehlerquelle Extraktion: das Feld war leer oder unsicher. Fehlerquelle Kern: Felder lagen vor, die Entscheidung weicht ab.",
        "",
        bericht("Regel-Leser", regel_zeilen),
        "",
        mistral_text,
    ]
    BERICHT.write_text("\n".join(text) + "\n", encoding="utf-8")
    KOSTEN.write_text(kosten_text(kosten) + "\n", encoding="utf-8")
    print(BERICHT)
    print(mistral_text.splitlines()[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
