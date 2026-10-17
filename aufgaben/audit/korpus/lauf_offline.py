"""Korpus „Beispiele und Gegenbeispiele“ ohne Sprachmodell durch die echte Pipeline (Router -> Kern -> Gegenrechnung ->
Antwort), so wie die Weboberfläche: Frage -> Knöpfe -> Faktenbestätigung -> Ergebnis.

Drei Stufen, alle unabhängig vom Sprachmodell:
- orakel:   das „Modell“ liefert die perfekten Fakten des Falls. Prüft alles NACH dem Modell (Schutzregeln, Pflichtangaben,
            Kern, Gegenrechnung, Antwort). Soll: jeder Fall RICHTIG. Ein Fehler hier ist ein Fehler des Systems.
- gestoert: das „Modell“ macht einen typischen Fehler (aus echten Läufen beobachtet, siehe STOERUNGEN). Soll: nie FALSCH
            (Rückfrage oder Grenzfall sind sicher). So bleibt der Chat mit JEDEM Modell sicher.
- demo:     kein Modell, nur die einfache Notfall-Erkennung des Demo-Modus.

Bewertung wie überall (aufgaben/audit/pruefkatalog_lauf.py::bewerte): RICHTIG / NACHGEFRAGT / FALSCH / FEHLER.
Jeder Lauf wird protokolliert: CSV in tests/archiv/ergebnisse/, Bericht in aufgaben/audit/korpus/ergebnisse/, eine Zeile
in aufgaben/audit/TESTPROTOKOLL.md. Nichts wird überschrieben (Dateiname mit Datum, Stufe und Code-Stand).

Aufruf (Windows): python aufgaben/audit/korpus/lauf_offline.py --stufe orakel [--nur KB-0001,KB-0002] [--familie F03]
"""
from __future__ import annotations

import argparse
import collections
import copy
import csv
import datetime
import json
import pathlib
import subprocess
import sys
import time

WURZEL = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "aufgaben" / "audit"))

from pruefkatalog_lauf import bewerte, fuehre_fall_aus  # noqa: E402

from app.llm.fake import FakeLLM  # noqa: E402
from app.schema import Fakten  # noqa: E402

KORPUS = WURZEL / "aufgaben" / "audit" / "korpus_beispiele.json"
ERGEBNISSE = WURZEL / "tests" / "archiv" / "ergebnisse"
BERICHTE = WURZEL / "aufgaben" / "audit" / "korpus" / "ergebnisse"
PROTOKOLL = WURZEL / "aufgaben" / "audit" / "TESTPROTOKOLL.md"


# ---------------------------------------------------------------------------------------------------------------------
# Typische Modellfehler (beobachtet in echten Läufen mit Mistral; jedes andere Modell kann sie genauso machen)
# Jede Störung: (Name, Prüfung ob anwendbar, Änderung der Fakten)
# ---------------------------------------------------------------------------------------------------------------------
def _ohne(feld):
    return (lambda f: f.get(feld) is not None, lambda f: {**f, feld: None})


def _pos_aendern(fn):
    def anwenden(f):
        g = copy.deepcopy(f)
        g["positionen"] = [fn(dict(p)) for p in g["positionen"]]
        return g
    return anwenden


def _hat_pos(bed=lambda p: True):
    return lambda f: any(bed(p) for p in f.get("positionen") or [])


STOERUNGEN = [
    ("Verwerterart fehlt", *_ohne("verwerterart")),
    ("Rechtsform fehlt", *_ohne("auftragnehmer_typ")),
    ("Jahr fehlt", *_ohne("jahr")),
    ("Jahr um eins daneben (aus Rechnungsnummer/Datum)", lambda f: f.get("jahr") is not None,
     lambda f: {**f, "jahr": f["jahr"] + 1}),
    ("Position doppelt", _hat_pos(), lambda f: {**f, "positionen": [*f["positionen"], f["positionen"][0]]}),
    ("Tätigkeit falsch zugeordnet (künstlerisch <-> nicht)", _hat_pos(lambda p: p.get("taetigkeit_id")),
     _pos_aendern(lambda p: {**p, "taetigkeit_id": ("T-30" if p.get("taetigkeit_id", "").startswith(("T-0", "T-1"))
                                                     else "T-02")} if p.get("taetigkeit_id") else p)),
    ("Tätigkeit fehlt", _hat_pos(lambda p: p.get("taetigkeit_id")),
     _pos_aendern(lambda p: {k: v for k, v in p.items() if k != "taetigkeit_id"})),
    ("Umsatzsteuer nicht als solche erkannt", _hat_pos(lambda p: p.get("rolle") == "ust"),
     _pos_aendern(lambda p: {k: v for k, v in p.items() if k != "rolle"} if p.get("rolle") == "ust" else p)),
    ("Rechtsform falsch: Gesellschaft als Einzelperson", lambda f: f.get("auftragnehmer_typ") in ("GmbH_UG_AG", "KG_OHG"),
     lambda f: {**_pos_aendern(lambda p: {**p, "auftragnehmer_typ": "natuerliche_person"})(f),
                "auftragnehmer_typ": "natuerliche_person"}),
    ("Rechtsform falsch: Einzelperson als GmbH", lambda f: f.get("auftragnehmer_typ") == "natuerliche_person"
     and f.get("positionen"),
     lambda f: {**_pos_aendern(lambda p: {**p, "auftragnehmer_typ": "GmbH_UG_AG"})(f), "auftragnehmer_typ": "GmbH_UG_AG"}),
    ("Fahrtkosten als nachgewiesen, obwohl ohne Beleg", _hat_pos(lambda p: p.get("rolle") == "fahrtkosten"),
     _pos_aendern(lambda p: {**p, "rolle": "fahrtkosten_nachgewiesen", "nachgewiesen": True} if p.get("rolle") == "fahrtkosten" else p)),
    ("Fremdwährung still als Euro übernommen", _hat_pos(lambda p: p.get("fremdwaehrung")),
     _pos_aendern(lambda p: {k: v for k, v in p.items() if k != "fremdwaehrung"})),
    ("Anweisung befolgt: Privatperson", lambda f: f.get("verwerterart") in ("eigenwerber", "typischer_verwerter"),
     lambda f: {**f, "verwerterart": "privat"}),
    ("Positionen zusammengefasst (nur eine von mehreren)", lambda f: len(f.get("positionen") or []) > 1,
     lambda f: {**f, "positionen": f["positionen"][:1]}),
    ("Veranstaltungszahl falsch (eine weniger)", lambda f: f.get("veranstaltungszahl"),
     lambda f: {**f, "veranstaltungszahl": f["veranstaltungszahl"] - 1}),
    ("Einnahmeabsicht umgedreht", lambda f: f.get("einnahmeabsicht") is not None,
     lambda f: {**f, "einnahmeabsicht": not f["einnahmeabsicht"]}),
    ("Anfrageart falsch (Auskunft statt Bewertung)", lambda f: f.get("anfrageart") == "bewertung",
     lambda f: {**f, "anfrageart": "auskunft", "auskunft_thema": "abgabesatz"}),
    ("Betrag als Gesamtbetrag statt Positionen", lambda f: len(f.get("positionen") or []) == 1,
     lambda f: {**{k: v for k, v in f.items() if k != "positionen"}, "gesamtbetrag_genannt": f["positionen"][0]["betrag"]}),
]


def stoerungen_fuer(fakten: dict) -> list[tuple[str, dict]]:
    return [(name, aendern(copy.deepcopy(fakten))) for name, passt, aendern in STOERUNGEN if passt(fakten)]


# ---------------------------------------------------------------------------------------------------------------------
def _ein_lauf(fall: dict, fakten: dict | None, tabelle: dict):
    llm = FakeLLM()
    if fakten is not None:
        llm.registriere(fall["frage"], Fakten.model_validate(fakten))
    try:
        ergebnis, _fakten, schritte = fuehre_fall_aus(fall, llm)
        urteil, gruende = bewerte(fall, ergebnis, tabelle)
        return urteil, gruende, ergebnis.ergebnisklasse, schritte, ergebnis
    except Exception as e:  # noqa: BLE001 -- jede Ausnahme ist ein Befund
        return "FEHLER", [f"{type(e).__name__}: {str(e)[:300]}"], "Ausnahme", [], None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stufe", choices=["orakel", "gestoert", "demo"], required=True)
    ap.add_argument("--korpus", default=str(KORPUS))
    ap.add_argument("--nur")
    ap.add_argument("--familie", help="nur Fälle, deren Gruppe so beginnt (z. B. F03)")
    ap.add_argument("--jeder", type=int, default=1, help="nur jeden n-ten Fall (Stichprobe)")
    ap.add_argument("--ohne-protokoll", action="store_true", help="nichts ablegen (zum Ausprobieren)")
    ap.add_argument("--zeige", action="store_true", help="auch NACHGEFRAGT mit Grund ausgeben")
    args = ap.parse_args()

    korpus = json.loads(pathlib.Path(args.korpus).read_text(encoding="utf-8"))
    tabelle, faelle = korpus["kuerzel"], korpus["faelle"]
    if args.nur:
        wahl = {x.strip() for x in args.nur.split(",")}
        faelle = [f for f in faelle if f["id"] in wahl]
    if args.familie:
        faelle = [f for f in faelle if f["gruppe"].startswith(args.familie)]
    faelle = faelle[::args.jeder]

    zeilen, zaehler, je_gruppe = [], collections.Counter(), collections.defaultdict(collections.Counter)
    start = time.time()
    for fall in faelle:
        if args.stufe == "orakel":
            laeufe = [("perfekte Fakten", fall["fakten"])]
        elif args.stufe == "demo":
            laeufe = [("Demo-Modus", None)]
        else:
            laeufe = stoerungen_fuer(fall["fakten"])
        for art, fakten in laeufe:
            urteil, gruende, ist, schritte, _e = _ein_lauf(fall, fakten, tabelle)
            zaehler[urteil] += 1
            je_gruppe[fall["gruppe"][:3]][urteil] += 1
            zeilen.append({"fall": fall["id"], "paar": fall["paar"], "rolle": fall["rolle"], "gruppe": fall["gruppe"],
                           "variante": art, "soll": "/".join(fall["soll"]), "ist": ist, "urteil": urteil,
                           "gruende": "; ".join(gruende)[:400], "verlauf": " | ".join(schritte)[:400]})
    dauer = time.time() - start

    stand = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=WURZEL).stdout.strip()
    heute = datetime.date.today().isoformat()
    kurz = (f"Läufe {len(zeilen)} (Fälle {len(faelle)}): RICHTIG {zaehler['RICHTIG']}, NACHGEFRAGT {zaehler['NACHGEFRAGT']}, "
            f"FALSCH {zaehler['FALSCH']}, FEHLER {zaehler['FEHLER']} – {dauer:.0f} s")
    print(kurz)
    for g, z in sorted(je_gruppe.items()):
        print(f"  {g}: " + ", ".join(f"{k} {v}" for k, v in sorted(z.items())))
    if args.ohne_protokoll:
        for z in zeilen:
            if z["urteil"] in ("FALSCH", "FEHLER") or (args.zeige and z["urteil"] == "NACHGEFRAGT"):
                print(f"{z['fall']} {z['urteil']} {z['variante']}: {z['gruende'][:200]} || {z['verlauf'][:250]}")
        return 1 if zaehler["FALSCH"] or zaehler["FEHLER"] else 0

    name = f"{heute}_korpus_offline-{args.stufe}_{stand}"
    ERGEBNISSE.mkdir(parents=True, exist_ok=True)
    BERICHTE.mkdir(parents=True, exist_ok=True)
    nr = 1
    while (ERGEBNISSE / f"{name}{'' if nr == 1 else f'_{nr}'}.csv").exists():
        nr += 1
    name = f"{name}{'' if nr == 1 else f'_{nr}'}"
    with open(ERGEBNISSE / f"{name}.csv", "w", encoding="utf-8", newline="") as datei:
        s = csv.DictWriter(datei, fieldnames=["datum", "modus", "code_stand", "katalog", *zeilen[0].keys()])
        s.writeheader()
        for z in zeilen:
            s.writerow({"datum": heute, "modus": f"offline {args.stufe}", "code_stand": stand,
                        "katalog": "aufgaben/audit/korpus_beispiele.json", **z})
    schlecht = [z for z in zeilen if z["urteil"] in ("FALSCH", "FEHLER")]
    nachgefragt = collections.Counter((z["gruppe"][:3], z["variante"]) for z in zeilen if z["urteil"] == "NACHGEFRAGT")
    bericht = [f"# Korpus offline, Stufe {args.stufe} – {heute}, Code-Stand `{stand}`", "",
               "Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Ohne Sprachmodell.", "", f"- {kurz}", "",
               "| Familie | " + " | ".join(("RICHTIG", "NACHGEFRAGT", "FALSCH", "FEHLER")) + " |", "|---|---|---|---|---|",
               *[f"| {g} | " + " | ".join(str(z[k]) for k in ("RICHTIG", "NACHGEFRAGT", "FALSCH", "FEHLER")) + " |"
                 for g, z in sorted(je_gruppe.items())],
               "", "## FALSCH und FEHLER", ""]
    bericht += [f"- {z['fall']} ({z['rolle']}, {z['variante']}): Soll {z['soll']}, Ist {z['ist']}; {z['gruende']}"
                for z in schlecht] or ["Keine."]
    bericht += ["", "## NACHGEFRAGT je Familie und Variante (häufigste)", ""]
    bericht += [f"- {g} / {v}: {n}" for (g, v), n in nachgefragt.most_common(40)] or ["Keine."]
    (BERICHTE / f"{name}.md").write_text("\n".join(bericht) + "\n", encoding="utf-8")
    if not PROTOKOLL.exists():
        PROTOKOLL.write_text("# Testprotokoll (alle Läufe, nur ergänzen)\n\nEntwurf – vom Steuerberater zu prüfen. Nur erfundene "
                             "Fälle. Jede Zeile: Datum, Code-Stand, Lauf, Ergebnis, Datei.\n\n| Datum | Code | Lauf | Ergebnis | "
                             "Datei |\n|---|---|---|---|---|\n", encoding="utf-8")
    with open(PROTOKOLL, "a", encoding="utf-8") as p:
        p.write(f"| {heute} | {stand} | Korpus offline {args.stufe}{' (' + args.familie + ')' if args.familie else ''} | "
                f"{kurz} | `tests/archiv/ergebnisse/{name}.csv` |\n")
    print(f"abgelegt: tests/archiv/ergebnisse/{name}.csv, aufgaben/audit/korpus/ergebnisse/{name}.md")
    return 1 if zaehler["FALSCH"] or zaehler["FEHLER"] else 0


if __name__ == "__main__":
    sys.exit(main())
