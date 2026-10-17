"""Testarchiv: alle Testfälle des Chatbots mit ihrem richtigen Ergebnis (Soll) an EINER Stelle,
damit ein anderes Sprachmodell mit einem Befehl gegen alles geprüft werden kann.

  python scripts/erzeuge_testarchiv.py            Archiv aus den Katalogen aktualisieren (nur ergänzen)
  python scripts/erzeuge_testarchiv.py --pruefen  Fehler, wenn das Archiv nicht zu den Katalogen passt
  python scripts/erzeuge_testarchiv.py --berichte vorhandene Ergebnisberichte (aufgaben/audit/*_ergebnis_*.md)
                                                  als CSV ins Archiv übernehmen (nur neue)

Grundregel 6: nichts wird überschrieben. Ändert sich ein Fall (Frage, Soll, Zahl, ...), bekommt er
eine neue Version; die alte bleibt in tests/archiv/versionen.jsonl. Nur erfundene Daten.
Ausführliche Erklärung: tests/archiv/README.md."""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

W = Path(__file__).resolve().parent.parent
ARCHIV = W / "tests" / "archiv"
ALLE = ARCHIV / "alle_faelle.json"
DIALOGE = ARCHIV / "dialoge.json"
DIALOGE_SOLL = ARCHIV / "dialoge_soll.json"
VERSIONEN = ARCHIV / "versionen.jsonl"
ERGEBNISSE = ARCHIV / "ergebnisse"

# Kurzname -> Katalogdatei (Format von aufgaben/audit/pruefkatalog_lauf.py). Neue Kataloge hier ergänzen.
KATALOGE = {
    "pruefkatalog": "aufgaben/audit/pruefkatalog.json",
    "testfall20": "aufgaben/audit/testfall_20_positionen.json",
    "alltag4": "aufgaben/audit/testfall_alltag_4.json",
    "alltag999": "aufgaben/audit/testfall_alltag_999.json",
    "waehrung": "aufgaben/audit/testfall_waehrung.json",
    # 15.10.2026: Fehlerquellen-Serie des Nutzers (Auftrag A1), Soll vor der Aufnahme gegen das Register geprüft,
    # live 0 FALSCH (48d9897). Status je Fall: ENTWURF.
    "fehlerquellen": "aufgaben/audit/fehlerquellen_ht_062_111.json",
    # 15.10.2026: Alltags-Serie des Nutzers, Soll vor der Aufnahme gegen Register und Tätigkeitsblatt geprüft,
    # live 0 FALSCH, 0 FEHLER (2004cde). Status je Fall: ENTWURF. Die Dialoge AT-046 bis 050 stehen in dialoge_soll.json.
    "alltag": "aufgaben/audit/alltag_at_001_060.json",
}
# Präfix der Ergebnisberichte in aufgaben/audit/ -> Kurzname des Katalogs
BERICHTE = {"pruefkatalog_ergebnis_": "pruefkatalog", "testfall20_ergebnis_": "testfall20", "alltag4_ergebnis_": "alltag4"}
# Diese Felder bestimmen einen Fall; ändert sich eines, entsteht eine neue Version.
INHALT = ("frage", "soll", "zahl", "nachtrag", "knoepfe", "enthaelt", "verboten_text", "max_rueckfragen")
# Weitere Tests, die NICHT vom Sprachmodell abhängen (sie prüfen den Rechenkern) -- nur als Verweis.
WEITERE = [
    {"datei": "regelwerk/Testfaelle_BSG_Urteile.xlsx", "blatt": "Testfälle",
     "was": "Testfälle zu den Regeln (Kern, ohne Sprachmodell)", "ausfuehren": "python tests/lauf_testfaelle.py"},
    {"datei": "regelwerk/testfaelle_maschinenlesbar.json", "was": "maschinenlesbare Kern-Testfälle",
     "ausfuehren": "python tests/lauf_testfaelle.py"},
    {"datei": "regelwerk/Fragenkatalog_Chatbot_Entwurf.xlsx", "blatt": "Fragenkatalog",
     "was": "Fragenkatalog (Abdeckung: welche Frage hat welche Regel), kein automatischer Test"},
    {"datei": "tests/app/", "was": "Regressionstests des Chatbots (offline, nachgebildete Modellantworten)",
     "ausfuehren": "python -m unittest discover -s tests/app"},
]


def _lies(pfad: str | Path):
    return json.loads((W / pfad).read_text(encoding="utf-8"))


def fingerabdruck(daten: dict) -> str:
    text = json.dumps(daten, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _versionen() -> list[dict]:
    if not VERSIONEN.exists():
        return []
    return [json.loads(z) for z in VERSIONEN.read_text(encoding="utf-8").splitlines() if z.strip()]


def _aktuelle_faelle() -> tuple[dict, list[dict]]:
    """Alle Fälle aller Kataloge, mit Archiv-ID '<katalog>:<id>'."""
    kuerzel = None
    faelle = []
    for kurz, pfad in KATALOGE.items():
        k = _lies(pfad)
        if kuerzel is None:
            kuerzel = k["kuerzel"]
        elif k["kuerzel"] != kuerzel:
            raise SystemExit(f"FEHLER: {pfad} hat andere Ergebnis-Kürzel als die übrigen Kataloge.")
        for f in k["faelle"]:
            inhalt = {feld: f[feld] for feld in INHALT if feld in f}
            faelle.append({**f, "id": f"{kurz}:{f['id']}", "quelle": pfad, "quelle_id": f["id"],
                           "fingerabdruck": fingerabdruck(inhalt), "_inhalt": inhalt})
    ids = [f["id"] for f in faelle]
    doppelt = sorted({i for i in ids if ids.count(i) > 1})
    if doppelt:
        raise SystemExit(f"FEHLER: doppelte Fall-IDs: {', '.join(doppelt)}")
    return kuerzel, faelle


def _aktuelle_dialoge() -> list[dict]:
    dialoge = []
    for d in _lies(DIALOGE_SOLL.relative_to(W))["dialoge"]:
        schritte = _lies(d["quelle"])
        inhalt = {"schritte": schritte, "soll_je_schritt": d["soll_je_schritt"]}
        dialoge.append({**d, "schritte": schritte, "fingerabdruck": fingerabdruck(inhalt), "_inhalt": inhalt})
    return dialoge


def _baue(versionen: list[dict]) -> tuple[dict, dict, list[dict]]:
    """Archivdateien im Speicher bauen; neue Versionen (noch nicht in versionen.jsonl) zurückgeben."""
    kuerzel, faelle = _aktuelle_faelle()
    dialoge = _aktuelle_dialoge()
    letzte: dict[str, dict] = {}
    for v in versionen:
        letzte[v["id"]] = v
    heute = datetime.date.today().isoformat()
    neu = []
    for eintrag in [*faelle, *dialoge]:
        alt = letzte.get(eintrag["id"])
        if alt is None or alt["fingerabdruck"] != eintrag["fingerabdruck"]:
            version = (alt["version"] + 1) if alt else 1
            v = {"id": eintrag["id"], "version": version, "fingerabdruck": eintrag["fingerabdruck"],
                 "aufgenommen": heute, "quelle": eintrag["quelle"], "inhalt": eintrag["_inhalt"]}
            neu.append(v)
            letzte[eintrag["id"]] = v
        eintrag["version"] = letzte[eintrag["id"]]["version"]
    entfernt = sorted(set(letzte) - {e["id"] for e in [*faelle, *dialoge]})
    for e in [*faelle, *dialoge]:
        e.pop("_inhalt")
    alle = {
        "hinweis": ("Testarchiv des KSK-Assistenten: alle Chatbot-Testfälle mit Soll (richtiges Ergebnis). Erzeugt mit "
                    "python scripts/erzeuge_testarchiv.py aus den Katalogen unten -- nicht von Hand ändern, sondern den "
                    "Katalog. Soll-Werte: siehe 'sicherheit' je Fall; nichts ist vom Steuerberater freigegeben. Nur "
                    "erfundene Daten. Ausführen gegen ein Modell: siehe tests/archiv/README.md."),
        "kuerzel": kuerzel,
        "quellen": KATALOGE,
        "anzahl": len(faelle),
        "nicht_mehr_im_katalog": entfernt,
        "weitere_tests": WEITERE,
        "faelle": faelle,
    }
    dialog_datei = {"hinweis": "Dialogtests mit Soll je Schritt; erzeugt aus tests/archiv/dialoge_soll.json.",
                    "dialoge": dialoge}
    return alle, dialog_datei, neu


def _json(daten) -> str:
    return json.dumps(daten, ensure_ascii=False, indent=1) + "\n"


def aktualisiere() -> int:
    ARCHIV.mkdir(parents=True, exist_ok=True)
    versionen = _versionen()
    alle, dialoge, neu = _baue(versionen)
    if neu:
        with VERSIONEN.open("a", encoding="utf-8", newline="\n") as datei:
            for v in neu:
                datei.write(json.dumps(v, ensure_ascii=False, sort_keys=True) + "\n")
    ALLE.write_text(_json(alle), encoding="utf-8", newline="\n")
    DIALOGE.write_text(_json(dialoge), encoding="utf-8", newline="\n")
    print(f"Testarchiv: {alle['anzahl']} Fälle, {len(dialoge['dialoge'])} Dialoge; {len(neu)} neue Version(en).")
    if alle["nicht_mehr_im_katalog"]:
        print("Hinweis: nicht mehr im Katalog (bleiben in versionen.jsonl):", ", ".join(alle["nicht_mehr_im_katalog"]))
    return 0


def pruefe() -> int:
    versionen = _versionen()
    alle, dialoge, neu = _baue(versionen)
    fehler = []
    if neu:
        fehler.append(f"{len(neu)} Fall/Fälle neu oder geändert, aber nicht archiviert: "
                      + ", ".join(v["id"] for v in neu[:10]))
    for pfad, soll in ((ALLE, alle), (DIALOGE, dialoge)):
        if not pfad.exists() or json.loads(pfad.read_text(encoding="utf-8")) != json.loads(_json(soll)):
            fehler.append(f"{pfad.relative_to(W).as_posix()} ist nicht aktuell")
    # Nur ergänzen: jede Version gibt es genau einmal, Versionen laufen ohne Lücke hoch.
    gesehen: dict[str, int] = {}
    for v in versionen:
        erwartet = gesehen.get(v["id"], 0) + 1
        if v["version"] != erwartet:
            fehler.append(f"versionen.jsonl: {v['id']} Version {v['version']} (erwartet {erwartet})")
        gesehen[v["id"]] = v["version"]
    if fehler:
        print("FEHLER im Testarchiv:\n- " + "\n- ".join(fehler)
              + "\nBehebung: python scripts/erzeuge_testarchiv.py (danach committen).")
        return 1
    print(f"Testarchiv aktuell: {alle['anzahl']} Fälle, {len(dialoge['dialoge'])} Dialoge, "
          f"{len(versionen)} Versionen.")
    return 0


_ZEILE = re.compile(r"^\| ([^|]+?) \| [^|]*? \| ([^|]+?) \| ([^|]+?) \| \*\*([A-Z]+)\*\* \| ([\d.]+) s \|$")


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=W, capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


def uebernehme_berichte() -> int:
    """Vorhandene Markdown-Berichte als CSV ablegen (Datum, Modus, Code-Stand aus git). Nur neue."""
    ERGEBNISSE.mkdir(parents=True, exist_ok=True)
    neu = 0
    for bericht in sorted((W / "aufgaben" / "audit").glob("*_ergebnis_*.md")):
        kurz = next((k for p, k in BERICHTE.items() if bericht.name.startswith(p)), None)
        if kurz is None:
            continue
        lauf = bericht.stem.split("_ergebnis_", 1)[1]
        text = bericht.read_text(encoding="utf-8")
        kopf = text.splitlines()[0] if text else ""
        datum = (re.search(r"Lauf (\d{4}-\d{2}-\d{2})", kopf) or [None, ""])[1]
        modus = (re.search(r"\((.*)\)\s*$", kopf) or [None, lauf])[1]
        stand = _git("log", "-1", "--format=%h", "--", bericht.relative_to(W).as_posix())
        ziel = ERGEBNISSE / f"{datum}_{kurz}_{lauf}_{stand or 'ohne-git'}.csv"
        if ziel.exists():
            continue
        zeilen = [m.groups() for m in (_ZEILE.match(z) for z in text.splitlines()) if m]
        if not zeilen:
            continue
        with ziel.open("w", encoding="utf-8", newline="") as datei:
            s = csv.writer(datei)
            s.writerow(["datum", "modus", "bericht_stand", "katalog", "fall", "soll", "ist", "urteil", "dauer_s"])
            for fall, soll, ist, urteil, dauer in zeilen:
                s.writerow([datum, modus, stand, KATALOGE[kurz], f"{kurz}:{fall.strip()}", soll.strip(),
                            ist.strip(), urteil, dauer])
        neu += 1
        print(f"übernommen: {ziel.relative_to(W).as_posix()} ({len(zeilen)} Fälle)")
    print(f"{neu} neue Ergebnisdatei(en).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pruefen", action="store_true")
    ap.add_argument("--berichte", action="store_true")
    a = ap.parse_args()
    if a.pruefen:
        return pruefe()
    if a.berichte:
        return uebernehme_berichte()
    return aktualisiere()


if __name__ == "__main__":
    sys.exit(main())
