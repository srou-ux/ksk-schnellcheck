"""Suite 130 über den Regel-Leser und, wenn ein Schlüssel da ist, über Mistral.

Der Kern wird nicht verändert. Hinterlegte Strukturfelder der Suite werden nicht als Lesung verwendet.
"""
from __future__ import annotations

import json
import pathlib
import re
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


def soll_feld(test: dict) -> str:
    """Das eine Feld, an dem dieser Fall hängt. Keine Ergebnisklasse."""
    text = test["txt"].lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    if "betrag in worten" in text:
        return "betrag_in_worten"
    if "zwei empfaenger" in text or "fotograf a" in text:
        return "empfaenger"
    if "umsatzsteuer separat" in text or "reine ust" in text or "ust-zeile" in text:
        return "ust_zeile"
    if "scanner-miete" in text or "anhang vorhanden" in text:
        return "beleg_vorhanden"
    if "reisekosten" in text or "eur/km" in text:
        return "fahrtkosten_beleg"
    if "in derselben rechnung" in text or "positionen" in text:
        return "positionen[]"
    if "gutschrift" in text:
        return "gutschrift"
    if "veranstaltungen" in text:
        return "veranstaltungszahl"
    if "schueler" in text:
        return "schuelerzahl"
    if "traegerschaft" in text or "fest angestellt" in text:
        return "beschaeftigung"
    if "personal" in text or "angestellte mitarbeiter" in text:
        return "personal"
    if "uebungsleiter" in text:
        return "uebungsleiter_anteil"
    if "jahr 2027" in text or "im jahr 2027" in text:
        return "jahr"
    if "verwerter" in text or "theaterunternehmen" in text:
        return "verwerter"
    if "jahresaggregat" in text or "aggregat" in text or "drei rechnungen" in text or "jahresentgelt" in text:
        return "jahresaggregat"
    if "veranlasst" in text or "auf anweisung" in text:
        return "veranlassung"
    if "bis 2028" in text or "loeschen" in text:
        return "vermerk"
    if "eigenwerbung" in text and "szenario" in text:
        return "szenario"
    gold = test.get("dokument") or {}
    if gold.get("rechtsformen"):
        return "rechtsform_angaben"
    if gold.get("positionsnummern") or any(p.get("nr") for p in gold.get("positionen") or []):
        return "positionen[].nr"
    for name in _GOLD:
        if (gold.get("summen") or {}).get(name):
            return "summen." + name
    if "prozent" in text and "ust" in text:
        return "ust_saetze"
    if any(wort in text for wort in ("konzert", "musik", "klavier", "chor", "kuenstler")) and any(
        wort in text for wort in ("evaluation", "versicherung", "transport", "reinigung", "sicherheit", "druck", "stimmung", "wartung", "nahrung")
    ):
        return "leistungsart"
    if any(wort in text for wort in ("pressetext", "social-media", "dj ", "dirigent", "stimmhilfe", "fotograf", "notenschreib", "gesang")):
        return "taetigkeit"
    return "leistungsart"


def feld_satz(name: str) -> str:
    saetze = {
        "empfaenger": "empfaenger nicht getrennt",
        "ust_zeile": "ust_zeile nicht erkannt",
        "positionen[]": "positionen[] nicht gesplittet",
        "positionen[].nr": "positionen[].nr nicht gelesen",
        "beleg_vorhanden": "beleg_vorhanden nicht gelesen",
        "fahrtkosten_beleg": "fahrtkosten_beleg nicht gelesen",
        "betrag_in_worten": "betrag_in_worten nicht als Zahl gelesen",
        "ust_saetze": "ust_saetze nicht gelesen",
        "rechtsform_angaben": "rechtsform_angaben nicht gelesen",
        "gutschrift": "gutschrift nicht gelesen",
        "veranstaltungszahl": "veranstaltungszahl nicht gelesen",
        "schuelerzahl": "schuelerzahl nicht gelesen",
        "beschaeftigung": "beschaeftigung nicht gelesen",
        "personal": "personal nicht gelesen",
        "uebungsleiter_anteil": "uebungsleiter_anteil nicht gelesen",
        "jahr": "jahr nicht als Fassung gelesen",
        "jahresaggregat": "jahresaggregat nicht gelesen",
        "veranlassung": "veranlassung nicht gelesen",
        "verwerter": "verwerter nicht gelesen",
        "vermerk": "vermerk nicht vom Zahlungsjahr getrennt",
        "szenario": "szenario nicht gelesen",
        "leistungsart": "leistungsart nicht von der Erwaehnung getrennt",
        "taetigkeit": "taetigkeit nicht gelesen",
    }
    if name in saetze:
        return saetze[name]
    if name.startswith("summen."):
        return name + " nicht gelesen"
    return name + " leer"


def feld_stand(felder: dict | None, name: str) -> str:
    if not felder:
        return "nicht gemessen"
    summen = felder.get("summen") or {}
    positionen = felder.get("positionen") or []
    if name == "empfaenger":
        gefuellt = bool(felder.get("empfaenger")) or len(felder.get("rechtsform_angaben") or []) > 1
    elif name == "ust_zeile":
        gefuellt = bool(summen.get("ust")) or any(p.get("ust") for p in positionen)
    elif name == "positionen[]":
        gefuellt = len(positionen) >= 2
    elif name == "positionen[].nr":
        gefuellt = sum(1 for p in positionen if p.get("nr")) >= 2
    elif name == "beleg_vorhanden":
        gefuellt = bool(felder.get("beleg_vorhanden"))
    elif name == "betrag_in_worten":
        from extraktion.felder import dezimal
        wort = str(felder.get("betrag_in_worten") or "").strip()
        gefuellt = bool(wort) and dezimal(wort) is not None
    elif name == "ust_saetze":
        gefuellt = len(felder.get("ust_saetze") or []) >= 2
    elif name == "rechtsform_angaben":
        gefuellt = bool(felder.get("rechtsform_angaben") or felder.get("empfaenger"))
    elif name.startswith("summen."):
        gefuellt = bool(summen.get(name.split(".", 1)[1]))
    else:
        wert = felder.get(name)
        gefuellt = wert not in ("", None, [], False)
    return "gefüllt" if gefuellt else "leer"


def _korrektur(quelle: str, feld: str, stand: str = "") -> str:
    if quelle == "Kern" and feld == "jahr" and stand == "gefüllt":
        return (
            "Jahr gelesen. Der Kern rechnet 2027 aus parameter.json. "
            "saetze.json gibt das Jahr nicht frei. Erwartung nicht verbiegen."
        )
    satz = feld_satz(feld)
    if quelle == "Extraktion":
        return satz + ". Nicht mitteln, nicht still übernehmen."
    if quelle == "Kern":
        return satz + ". Feldbezug geprüft, der Kern hat anders entschieden. Erwartung nicht verbiegen."
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
        feld = soll_feld(test)
        quelle = fehlerquelle(test, felder, erhalten)
        if quelle == "Extraktion" and feld_stand(felder, feld) == "gefüllt":
            quelle = "Kern"
        zeilen.append({
            "id": test["id"],
            "kat": test.get("kat", ""),
            "erwartet": test["status"],
            "erhalten": erhalten,
            "ok": erhalten == test["status"],
            "quelle": quelle,
            "feld": feld,
            "stand": feld_stand(felder, feld),
            "korrektur": _korrektur(quelle, feld, feld_stand(felder, feld)),
            "grund": grund,
            "felder": felder,
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
    return "\n".join(teile)


def feld_bericht(regel: list[dict], mistral: list[dict] | None) -> str:
    """Je Abweichung das konkrete Feld und der Stand bei beiden Lesern."""
    andere = {zeile["id"]: zeile for zeile in mistral or []}
    vollstaendig = bool(mistral) and len(mistral) == len(regel) and all(zeile["erhalten"] != "ABBRUCH" for zeile in mistral)
    teile = ["Feld-Diagnose je Abweichung"]
    for zeile in regel:
        gegen = andere.get(zeile["id"]) if vollstaendig else None
        if zeile["ok"] and (gegen is None or gegen["ok"]):
            continue
        feld = zeile.get("feld") or soll_feld({"txt": "", "dokument": {}})
        links = zeile.get("stand") or feld_stand(zeile.get("felder"), feld)
        rechts = feld_stand(gegen.get("felder") if gegen else None, feld) if vollstaendig else "nicht gemessen"
        quelle = zeile["quelle"]
        if gegen and not gegen["ok"] and zeile["ok"]:
            quelle = gegen["quelle"]
        teile.append(
            f"{zeile['id']} | {zeile['kat']} | erwartet {zeile['erwartet']} | Regel {zeile['erhalten']} | "
            f"Mistral {gegen['erhalten'] if gegen else 'nicht gemessen'} | {quelle} | {feld_satz(feld)} | "
            f"Regel: {links} | Mistral: {rechts}"
        )
    if len(teile) == 1:
        teile.append("keine Abweichung")
    return "\n".join(teile)


def kosten_text(zeilen: list[dict]) -> str:
    seiten = sum(int(zeile.get("seiten") or 0) for zeile in zeilen)
    prompt = sum(int(zeile.get("prompt_tokens") or 0) for zeile in zeilen)
    completion = sum(int(zeile.get("completion_tokens") or 0) for zeile in zeilen)
    je_stufe: dict[str, list] = {}
    for zeile in zeilen:
        je_stufe.setdefault(str(zeile.get("stufe") or ""), []).append(zeile)
    stufen = ["Kosten je Stufe"]
    for name in ("ocr", "small", "medium"):
        gruppe = je_stufe.get(name, [])
        stufen.append(
            f"  {name}: Aufrufe {len(gruppe)} | Seiten {sum(int(zeile.get('seiten') or 0) for zeile in gruppe)} | "
            f"Prompt {sum(int(zeile.get('prompt_tokens') or 0) for zeile in gruppe)} | "
            f"Completion {sum(int(zeile.get('completion_tokens') or 0) for zeile in gruppe)}"
        )
    teile = [
        "Kostenlog Extraktion. Beträge in Token und Seiten, kein geschätzter Euro-Preis.",
        f"Aufrufe {len(zeilen)} | Seiten {seiten} | Prompt-Token {prompt} | Completion-Token {completion}",
        *stufen,
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
            grund = (abbruch["korrektur"] if abbruch else "Lauf unvollständig.").replace("\n", " ").strip()
            mistral_text = "Mistral nicht gemessen. " + grund + " Es gibt keine Teilquote."
        else:
            mistral_text = bericht("Mistral OCR 4.1 + Small", mistral_zeilen)
    text = [
        "Vergleich Extraktion, Suite 130. Strukturfelder der Suite werden nicht als Lesung benutzt.",
        "Fehlerquelle Extraktion: das benannte Feld war leer oder unsicher. Fehlerquelle Kern: das Feld lag vor, die Entscheidung weicht ab.",
        "",
        bericht("Regel-Leser", regel_zeilen),
        "",
        mistral_text,
        "",
        feld_bericht(regel_zeilen, mistral_zeilen if mistral_zeilen and not mistral_text.startswith("Mistral nicht gemessen") else None),
    ]
    BERICHT.write_text("\n".join(text) + "\n", encoding="utf-8")
    KOSTEN.write_text(kosten_text(kosten) + "\n", encoding="utf-8")
    print(BERICHT)
    print(mistral_text.splitlines()[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
