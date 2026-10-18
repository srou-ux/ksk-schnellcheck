"""Misst Suite 130 zweimal: Regel-Leser und Mistral-Leser, danach derselbe Kern.

Aufruf:  python -m extraktion.messe
Ohne Schlüssel läuft nur der Regel-Leser. Der Schlüssel wird nicht in die Ergebnisdatei geschrieben.
"""
from __future__ import annotations

import json
import sys
import pathlib

WURZEL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL))

from extraktion.felder import an_kern  # noqa: E402
from extraktion.schnittstelle import extrahiere_dokument  # noqa: E402
from extraktion.schluessel import schluessel  # noqa: E402
from tests.lauf_testsuite_100 import PAARE, SPERRE_AUSBREITUNG, _jahr, messe  # noqa: E402

SUITE = WURZEL / "tests" / "testsuite_adversarial_130.json"
BERICHT = WURZEL / "tests" / "ergebnis_extraktion_vergleich.txt"
KOSTEN = WURZEL / "tests" / "ergebnis_extraktion_kosten.txt"
LAUF = WURZEL / "extraktion" / "_lauf"
PAARE_IDS = PAARE
SPERRE_IDS = SPERRE_AUSBREITUNG


def bewerte(test: dict, felder: dict):
    kopie = {schluessel_: wert for schluessel_, wert in test.items() if schluessel_ != "dokument"}
    kopie["dokument"] = an_kern(felder, _jahr(test["txt"], {}))
    return messe(kopie, grenzfall_zaehlt=False, taetigkeit=True)


def fehlerquelle(test: dict, felder: dict, erhalten: str) -> str:
    if erhalten == test["status"]:
        return ""
    gold = test.get("dokument") or {}
    if felder.get("unsicher") or felder.get("unklare_felder"):
        return "Extraktion"
    if gold and not _deckt(felder, gold):
        return "Extraktion"
    if not _hat_inhalt(felder):
        return "Extraktion"
    return "Kern"


def _hat_inhalt(felder: dict) -> bool:
    summen = felder.get("summen") or {}
    return any(summen.values()) or bool(felder.get("positionen") or felder.get("rechtsform_angaben") or felder.get("jahr"))


def _deckt(felder: dict, gold: dict) -> bool:
    for name, wert in (gold.get("summen") or {}).items():
        if wert and not (felder.get("summen") or {}).get(name):
            return False
    if gold.get("rechtsformen") and len(felder.get("rechtsform_angaben") or []) < 2:
        return False
    if gold.get("positionsnummern") and len(felder.get("positionen") or []) < 2:
        return False
    return True


def _korrektur(quelle: str) -> str:
    if quelle == "Extraktion":
        return "Feld leer, unsicher oder abweichend gelesen. Nicht raten, die Angabe nicht an den Kern geben."
    if quelle == "Kern":
        return "Die Felder lagen vor. Die offene Entscheidung bleibt im Kern, nicht im Leser."
    return ""


def _sammle(tests: list, weg: str, leser) -> tuple[list, list]:
    zeilen = []
    kosten = []
    for test in tests:
        felder = leser(test)
        erhalten, klasse, grund = bewerte(test, felder)
        quelle = fehlerquelle(test, felder, erhalten)
        zeilen.append({
            "id": test["id"],
            "kat": test.get("kat", ""),
            "erwartet": test["status"],
            "erhalten": erhalten,
            "ok": erhalten == test["status"],
            "quelle": quelle,
            "korrektur": _korrektur(quelle),
            "klasse": klasse,
            "grund": grund,
        })
        kosten.extend(felder.get("kosten") or [])
    return zeilen, kosten


def _quote(zeilen: list) -> str:
    je: dict[str, list] = {}
    for zeile in zeilen:
        je.setdefault(zeile["kat"], []).append(zeile["ok"])
    texte = []
    treffer = sum(z["ok"] for z in zeilen)
    for kat, werte in je.items():
        texte.append(f"  {kat:<22} {sum(werte):>3}/{len(werte)}")
    texte.append(f"Gesamt {treffer}/{len(zeilen)}")
    return "\n".join(texte)


def _paare(zeilen: list) -> list[str]:
    stand = {zeile["id"]: zeile["ok"] for zeile in zeilen}
    ausgabe = []
    for links, rechts in PAARE_IDS:
        beide = stand.get(links) and stand.get(rechts)
        ausgabe.append(f"  {links}/{rechts}: {'beide richtig' if beide else 'FEHLER'}")
    return ausgabe


def _sperre(zeilen: list) -> list[str]:
    stand = {zeile["id"]: zeile for zeile in zeilen}
    ausgabe = []
    for fall_id in SPERRE_IDS:
        zeile = stand.get(fall_id, {})
        sperrt = zeile.get("erhalten") == "SPERRE" and zeile.get("ok")
        ausgabe.append(f"  {fall_id}: {'sperrt das Dokument' if sperrt else 'sperrt nicht'}")
    return ausgabe


def bericht(regel: list, mistral: list | None, hinweis: str) -> str:
    teile = [
        "Extraktion vor dem Kern. Der Kern ist unverändert.",
        "Regel = Muster im Text, ohne die in der Suite hinterlegten Strukturfelder.",
        "Mistral = OCR 4.1 nur bei Dateien, Small dreimal, Medium nur bei ungültigem JSON.",
        hinweis,
        "",
        "Regel",
        _quote(regel),
        "Paar-Check",
        *_paare(regel),
        "Sperre-Ausbreitung",
        *_sperre(regel),
        "",
    ]
    if mistral is None:
        teile.append("Mistral: nicht gemessen.")
    else:
        teile.extend(["Mistral", _quote(mistral), "Paar-Check", *_paare(mistral), "Sperre-Ausbreitung", *_sperre(mistral), ""])
        teile.append("Abweichungen Mistral (erwartet / erhalten / Fehlerquelle / Korrektur)")
        for zeile in mistral:
            if zeile["ok"]:
                continue
            teile.append(
                f"{zeile['id']} | {zeile['kat']} | {zeile['erwartet']} | {zeile['erhalten']} | "
                f"{zeile['quelle']} | {zeile['korrektur']}"
            )
    teile.append("")
    teile.append("Abweichungen Regel (erwartet / erhalten / Fehlerquelle / Korrektur)")
    for zeile in regel:
        if zeile["ok"]:
            continue
        teile.append(
            f"{zeile['id']} | {zeile['kat']} | {zeile['erwartet']} | {zeile['erhalten']} | "
            f"{zeile['quelle']} | {zeile['korrektur']}"
        )
    return "\n".join(teile) + "\n"


def kostenbericht(zeilen: list) -> str:
    prompt = sum(int(zeile.get("prompt_tokens") or 0) for zeile in zeilen)
    antwort = sum(int(zeile.get("completion_tokens") or 0) for zeile in zeilen)
    seiten = sum(int(zeile.get("seiten") or 0) for zeile in zeilen)
    teile = [
        "Kosten-Log. Beträge in Tokens und Seiten, kein umgerechneter Preis.",
        f"Aufrufe {len(zeilen)}",
        f"Prompt-Tokens {prompt}",
        f"Antwort-Tokens {antwort}",
        f"OCR-Seiten {seiten}",
        "",
    ]
    for zeile in zeilen:
        teile.append(
            f"{zeile.get('stufe', '')} | {zeile.get('modell', '')} | "
            f"seiten {zeile.get('seiten') or 0} | prompt {zeile.get('prompt_tokens')} | "
            f"antwort {zeile.get('completion_tokens')}"
        )
    return "\n".join(teile) + "\n"


def _sonde(key: str) -> str | None:
    from extraktion import http
    from extraktion.felder import konfig
    try:
        http.post_json(
            "/v1/chat/completions",
            {
                "model": konfig()["MISTRAL_SMALL_MODEL"],
                "temperature": 0,
                "messages": [{"role": "user", "content": "Antworte nur mit dem Wort ok."}],
                "max_tokens": 5,
            },
            key,
            timeout=30,
        )
    except Exception as fehler:
        return str(fehler)
    return None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    tests = json.loads(SUITE.read_text(encoding="utf-8"))["tests"]
    regel, _ = _sammle(tests, "rule", lambda test: extrahiere_dokument(test["txt"], weg="rule"))
    key = schluessel()
    mistral = None
    kosten = []
    hinweis = "Mistral nicht gemessen: kein Schlüssel."
    if key:
        problem = _sonde(key)
        if problem:
            hinweis = "Mistral nicht gemessen: Aufruf fehlgeschlagen (" + problem.split(":", 1)[-1].strip()[:180] + ")."
        else:
            mistral, kosten = _sammle(
                tests, "mistral", lambda test: extrahiere_dokument(test["txt"], weg="mistral", schluessel=key),
            )
            hinweis = "Mistral gemessen mit dem gepinnten Small-Modell, drei Ablesungen je Fall."
    BERICHT.write_text(bericht(regel, mistral, hinweis), encoding="utf-8")
    KOSTEN.write_text(kostenbericht(kosten), encoding="utf-8")
    print(BERICHT.read_text(encoding="utf-8")[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
