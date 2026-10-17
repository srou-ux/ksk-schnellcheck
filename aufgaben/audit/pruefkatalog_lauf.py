"""Prüfkatalog Stufe 1: Soll gegen Ist durch die echte Pipeline (Router -> Kern).

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle aus aufgaben/audit/pruefkatalog.json.

Aufruf (Windows und Linux gleich):
    python aufgaben/audit/pruefkatalog_lauf.py --llm fake
    python aufgaben/audit/pruefkatalog_lauf.py --llm mistral --bericht aufgaben/audit/pruefkatalog_ergebnis_small.md
Modell für Mistral über die Umgebungsvariable MISTRAL_MODELL (Standard seit 17.10.2026: mistral-small-latest),
Schlüssel nur aus MISTRAL_API_KEY (wird nie ausgegeben).

Bewertung je Fall:
    RICHTIG     Ergebnisklasse zulässig und (falls genannt) Zahl stimmt
    NACHGEFRAGT System fragt zurück / Grenzfall / nicht abgedeckt, Soll wäre ein sicheres Ergebnis
                (kein Fehler: lieber nachfragen als raten, aber nicht gelöst)
    FALSCH      sicheres Ergebnis, das nicht dem Soll entspricht, falsche Zahl oder verbotener Text
    FEHLER      Absturz, Modellantwort nicht verarbeitbar oder Prüfung fehlgeschlagen
Bestanden (Stufe 1) heißt: 0 FALSCH, 0 FEHLER und mindestens 90 % RICHTIG bei den Fällen mit
sicherem Soll. Rückgabewert 1, wenn es FALSCH oder FEHLER gibt.

Das Skript ändert nichts an app/ oder kern/; es ruft nur auf.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import sys
import time
from decimal import Decimal, InvalidOperation

WURZEL = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL))

from app import bestaetigung, router  # noqa: E402
from app import ergebnisklassen as EK  # noqa: E402

KATALOG = WURZEL / "aufgaben" / "audit" / "pruefkatalog.json"

# Gründe aus dem Lückenprotokoll mitschneiden (nur lesend weitergereicht), damit ein FEHLER im
# Bericht seinen Grund zeigt, z. B. HTTP 429 oder ungültiges JSON. Der Schlüssel erscheint nie darin.
_PROTOKOLL: list[str] = []
_orig_protokolliere = router.protokolliere


def _protokolliere_mit(frage, jahr, grund, **kw):
    _PROTOKOLL.append(" ".join(str(grund).split())[:600])  # Zeilenumbrüche weg, damit der Grund ganz im Bericht steht
    return _orig_protokolliere(frage, jahr, grund, **kw)


router.protokolliere = _protokolliere_mit
SICHER = {"A", "N", "AUSKUNFT"}
OFFEN = {"R", "G", "X"}


def kuerzel_von(ergebnisklasse: str, tabelle: dict) -> str:
    for k, v in tabelle.items():
        if v == ergebnisklasse:
            return k
    if ergebnisklasse == EK.PRUEFUNG_FEHLGESCHLAGEN:
        return "FEHLER"
    return ergebnisklasse  # unbekannte Klasse bleibt sichtbar


def _bestaetige_falls_noetig(antwort, llm):
    if antwort.sitzungskennung and antwort.fakten_hash and antwort.ergebnisklasse == EK.FAKTEN_BESTAETIGUNG_NOETIG:
        fakten = list(antwort.fakten_zusammenfassung or [])
        bestaetigung.SPEICHER.bestaetige(antwort.sitzungskennung, antwort.fakten_hash)
        return router.fuehre_nach_bestaetigung_aus(antwort.sitzungskennung, llm), fakten
    return antwort, list(antwort.fakten_zusammenfassung or [])


def _druecke_knopf(ergebnis, fall: dict, llm, schritte: list[str]):
    """Wie ein Nutzer in der Weboberfläche: bei einer Rückfrage die passende Schaltfläche
    drücken (POST /knopf -> router.wende_feldantwort_an). Liefert None, wenn kein Knopf passt."""
    knoepfe = fall.get("knoepfe") or {}
    if not ergebnis.sitzungskennung or not hasattr(router, "wende_feldantwort_an"):
        return None
    for option in getattr(ergebnis, "rueckfrage_optionen", None) or []:
        feld, beschriftung = option.get("feld"), knoepfe.get(option.get("feld"))
        if feld == "auftragszweck" and not beschriftung and "verwerterart" in knoepfe:
            # Schritt 2 (17.10.2026): gespeicherter Fall mit der alten Kategorie -> Zweck-Knopf derselben Einordnung.
            from app.einordnung import zweck_knopf_fuer_alten_knopf

            beschriftung = zweck_knopf_fuer_alten_knopf(knoepfe["verwerterart"])
        if beschriftung and beschriftung in (option.get("werte") or {}):
            schritte.append(f"Knopf {feld}={beschriftung!r}")
            return router.wende_feldantwort_an(
                ergebnis.sitzungskennung, feld, option["werte"][beschriftung], llm, option.get("position"))
    return None


def fuehre_fall_aus(fall: dict, llm):
    """Wie die Weboberfläche: Frage -> Rückfragen per Knopf (falls im Fall hinterlegt) ->
    Faktenbestätigung (automatisch 'Ja') -> Ergebnis. Passt kein Knopf und hat der Fall einen
    'nachtrag', wird dieser einmal als Freitext nachgeschickt."""
    verlauf: list[str] = []
    erste = router.bearbeite_frage(fall["frage"], llm, verlauf)
    ergebnis, fakten = _bestaetige_falls_noetig(erste, llm)
    schritte = [f"Antwort 1: {ergebnis.ergebnisklasse}"]
    for _ in range(int(os.environ.get("MAX_KNOEPFE", "6"))):  # höchstens so viele Knöpfe nacheinander
        if ergebnis.ergebnisklasse != EK.RUECKFRAGE_NOETIG:
            break
        naechste = _druecke_knopf(ergebnis, fall, llm, schritte)
        if naechste is None:
            break
        ergebnis, fakten = _bestaetige_falls_noetig(naechste, llm)
        schritte.append(f"-> {ergebnis.ergebnisklasse}")
    if ergebnis.ergebnisklasse == EK.RUECKFRAGE_NOETIG and fall.get("nachtrag"):
        schritte.append(f"Rückfragen: {ergebnis.rueckfragen}")
        verlauf = [fall["frage"]]
        zweite = router.bearbeite_frage(fall["nachtrag"], llm, verlauf, ergebnis.sitzungskennung)
        ergebnis, fakten = _bestaetige_falls_noetig(zweite, llm)
        schritte.append(f"Nachtrag gesendet: {fall['nachtrag']!r} -> {ergebnis.ergebnisklasse}")
    return ergebnis, fakten, schritte


def _dezimal(wert):
    try:
        return Decimal(str(wert))
    except (InvalidOperation, TypeError):
        return None


def bewerte(fall: dict, ergebnis, tabelle: dict) -> tuple[str, list[str]]:
    gruende: list[str] = []
    ist = kuerzel_von(ergebnis.ergebnisklasse, tabelle)
    text = ergebnis.antwort or ""
    # 16.10.2026: auch der feste Text bei gesperrtem Zugang (app/router.py, ZUGANG_GESPERRT_RUECKFRAGE) ist ein Modellfehler.
    if ist == "FEHLER" or "konnte nicht verarbeitet" in text or "Zugang zum Sprachmodell ist gerade gesperrt" in text:
        return "FEHLER", [f"Ist: {ergebnis.ergebnisklasse}"]
    for verboten in fall.get("verboten_text", []):
        if verboten.lower() in text.lower():
            gruende.append(f"verbotener Text in der Antwort: {verboten!r}")
    soll = fall["soll"]
    if ist in soll:
        for muss in fall.get("enthaelt", []):
            varianten = muss if isinstance(muss, list) else [muss]
            if not any(v in text for v in varianten):
                gruende.append(f"erwarteter Text fehlt: {' oder '.join(map(repr, varianten))}")
        protokoll = ergebnis.kern_protokoll or {}
        for schluessel, erwartet in (fall.get("zahl") or {}).items():
            wert = protokoll.get(schluessel)
            if wert is None:
                continue  # keine Zahl genannt (z. B. Rundung ungeklärt) -> nicht als falsch werten
            if _dezimal(wert) != Decimal(erwartet):
                gruende.append(f"{schluessel}: Soll {erwartet}, Ist {wert}")
        return ("FALSCH" if gruende else "RICHTIG"), gruende
    if gruende:
        return "FALSCH", gruende
    if ist in OFFEN:  # Rückfrage/Grenzfall/nicht abgedeckt statt Soll: nicht gelöst, aber nicht gefährlich
        return "NACHGEFRAGT", [f"Soll {soll}, Ist {ist}"]
    return "FALSCH", [f"Soll {soll}, Ist {ist} ({ergebnis.ergebnisklasse})"]


_SYSTEM_ROH = (
    "Du bist Fachberater für die Künstlersozialabgabe in Deutschland und antwortest einem Steuerberater. "
    "Beantworte die Frage nach deinem Wissen. Antworte NUR mit einem JSON-Objekt ohne weiteren Text:\n"
    '{"ergebnis": "abgabepflichtig" | "nicht_abgabepflichtig" | "grenzfall" | "rueckfrage" | "auskunft" | "nicht_bekannt", '
    '"bemessungsgrundlage": Zahl oder null, "abgabe": Zahl oder null, '
    '"begruendung": "kurz", "fundstellen": ["Norm, Urteil oder KSK-Info"]}\n'
    "'rueckfrage', wenn dir eine entscheidende Angabe fehlt; 'auskunft' bei reinen Wissensfragen (Satz, Frist)."
)
_ROH_KLASSEN = {
    "abgabepflichtig": "A", "nicht_abgabepflichtig": "N", "grenzfall": "G",
    "rueckfrage": "R", "auskunft": "AUSKUNFT", "nicht_bekannt": "X",
}


class RohErgebnis:
    """Antwort des Sprachmodells OHNE den KSK-Assistenten (kein Kern, kein Regelwerk, keine Quellen),
    in derselben Form wie router.Antwort, damit dieselbe Bewertung greift."""

    def __init__(self, roh: str, tabelle: dict):
        self.rueckfragen, self.sitzungskennung, self.fakten_hash = [], None, None
        text = roh.strip()
        if text.startswith("```"):
            text = text.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0]
        daten = json.loads(text[text.find("{"): text.rfind("}") + 1])
        kuerzel = _ROH_KLASSEN.get(str(daten.get("ergebnis", "")).strip().lower(), "FEHLER")
        self.ergebnisklasse = tabelle.get(kuerzel, EK.PRUEFUNG_FEHLGESCHLAGEN)
        self.kern_protokoll = {k: daten[k] for k in ("bemessungsgrundlage", "abgabe") if daten.get(k) is not None}
        fundstellen = daten.get("fundstellen") or []
        self.fakten_zusammenfassung = [f"Fundstellen laut Modell: {'; '.join(map(str, fundstellen)) or 'keine'}"]
        self.antwort = f"{daten.get('begruendung', '')} | Fundstellen: {fundstellen}"


def fuehre_fall_roh_aus(fall: dict, llm, tabelle: dict):
    """Vergleichsmodus: Frage direkt ans Modell. Fragt es zurück, wird der Nachtrag einmal angehängt."""
    ergebnis = RohErgebnis(llm._aufruf(_SYSTEM_ROH, fall["frage"]), tabelle)
    schritte = [f"Antwort 1: {ergebnis.ergebnisklasse}"]
    if ergebnis.ergebnisklasse == EK.RUECKFRAGE_NOETIG and fall.get("nachtrag"):
        ergebnis = RohErgebnis(llm._aufruf(_SYSTEM_ROH, f"{fall['frage']}\n{fall['nachtrag']}"), tabelle)
        schritte.append(f"Nachtrag gesendet: {fall['nachtrag']!r} -> {ergebnis.ergebnisklasse}")
    return ergebnis, ergebnis.fakten_zusammenfassung, schritte


def baue_llm(art: str):
    if art == "fake":
        from app.llm.fake import FakeLLM
        return FakeLLM(), "Demo-Modus (FakeLLM)"
    if not os.environ.get("MISTRAL_API_KEY"):
        print("KEIN SCHLÜSSEL: MISTRAL_API_KEY ist nicht gesetzt. Nichts getestet.")
        sys.exit(0)
    from app.llm.mistral import MistralLLM
    modell = os.environ.get("MISTRAL_MODELL", "mistral-small-latest")
    zusatz = " – ROH, ohne KSK-Assistent (Vergleich)" if art == "mistral-roh" else " – im KSK-Assistenten"
    return MistralLLM(timeout=float(os.environ.get("MISTRAL_TIMEOUT", "180"))), f"Mistral ({modell}){zusatz}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--llm", choices=["fake", "mistral", "mistral-roh"], default="fake",
                    help="mistral-roh: Frage direkt ans Modell, ohne Kern/Regelwerk/Quellen (Vergleich)")
    ap.add_argument("--bericht", help="Markdown-Bericht hierhin schreiben")
    ap.add_argument("--nur", help="nur diese Fall-IDs, kommagetrennt (z. B. P-05,K-08)")
    ap.add_argument("--katalog", help="anderer Fallkatalog im selben Format (Standard: pruefkatalog.json), "
                    "z. B. aufgaben/audit/testfall_20_positionen.json")
    ap.add_argument("--details", action="store_true", help="Details auch für RICHTIGE Fälle zeigen (Fakten, Zahl)")
    ap.add_argument("--csv", help="Ergebnis je Fall zusätzlich als CSV hierhin schreiben (Testarchiv, "
                    "Vergleich zweier Modelle mit scripts/vergleiche_ergebnisse.py)")
    args = ap.parse_args()

    katalog_datei = pathlib.Path(args.katalog) if args.katalog else KATALOG
    try:
        katalog_anzeige = katalog_datei.resolve().relative_to(WURZEL).as_posix()
    except ValueError:
        katalog_anzeige = katalog_datei.as_posix()
    katalog = json.loads(katalog_datei.read_text(encoding="utf-8"))
    tabelle = katalog["kuerzel"]
    faelle = katalog["faelle"]
    if args.nur:
        wahl = {x.strip() for x in args.nur.split(",")}
        faelle = [f for f in faelle if f["id"] in wahl]
    llm, name = baue_llm(args.llm)

    zeilen: list[str] = []
    zaehler = {"RICHTIG": 0, "NACHGEFRAGT": 0, "FALSCH": 0, "FEHLER": 0}
    csv_zeilen: list[dict] = []
    sicher_gesamt = sicher_richtig = 0
    details: list[str] = []
    start = time.time()
    for fall in faelle:
        t0 = time.time()
        _PROTOKOLL.clear()
        try:
            if args.llm == "mistral-roh":
                ergebnis, fakten, schritte = fuehre_fall_roh_aus(fall, llm, tabelle)
            else:
                ergebnis, fakten, schritte = fuehre_fall_aus(fall, llm)
            urteil, gruende = bewerte(fall, ergebnis, tabelle)
            ist = ergebnis.ergebnisklasse
            # Rückfrage-Kalibrierung (Alltagsfälle): mehr Rückfragen als nötig sind ein Befund,
            # aber kein falsches Ergebnis -> höchstens NACHGEFRAGT.
            rueckfragen = sum(1 for s in schritte if s.startswith(("Knopf ", "Nachtrag gesendet")))
            grenze = fall.get("max_rueckfragen")
            if grenze is not None and rueckfragen > grenze:
                gruende.append(f"{rueckfragen} Rückfrage(n), nötig laut Soll höchstens {grenze}")
                if urteil == "RICHTIG":
                    urteil = "NACHGEFRAGT"
        except Exception as e:  # jede Ausnahme ist ein Befund, kein Abbruch des Laufs
            urteil, gruende, ist, fakten, schritte = "FEHLER", [f"{type(e).__name__}: {str(e)[:200]}"], "Ausnahme", [], []
        dauer = time.time() - t0
        if urteil == "FEHLER" and _PROTOKOLL:
            gruende.append("Protokoll: " + " / ".join(dict.fromkeys(_PROTOKOLL)))
        zaehler[urteil] += 1
        if any(s in SICHER for s in fall["soll"]):
            sicher_gesamt += 1
            sicher_richtig += urteil == "RICHTIG"
        zeilen.append(f"| {fall['id']} | {fall['gruppe']} | {'/'.join(fall['soll'])} | {ist} | **{urteil}** | {dauer:.1f} s |")
        protokoll = getattr(ergebnis, "kern_protokoll", None) if urteil != "FEHLER" or ist != "Ausnahme" else None
        protokoll = protokoll if isinstance(protokoll, dict) else {}
        csv_zeilen.append({
            "fall": fall["id"], "soll": "/".join(fall["soll"]), "ist": ist, "urteil": urteil,
            "bemessungsgrundlage": protokoll.get("bemessungsgrundlage", ""), "abgabe": protokoll.get("abgabe", ""),
            "rueckfragen": sum(1 for x in schritte if x.startswith(("Knopf ", "Nachtrag gesendet"))),
            "gruende": "; ".join(gruende)[:500], "dauer_s": f"{dauer:.1f}"})
        if urteil != "RICHTIG" or args.llm == "mistral-roh" or args.details:  # roh: Fundstellen immer zeigen (erfunden?)
            details += [f"### {fall['id']} – {fall['gruppe']} ({urteil})",
                        f"- Frage: {fall['frage']}",
                        f"- Soll: {', '.join(tabelle.get(s, s) for s in fall['soll'])}"
                        + (f"; Zahl: {fall['zahl']}" if fall.get("zahl") else "")
                        + f" (Referenz: {fall['referenz']}, Sicherheit: {fall['sicherheit']})",
                        f"- Ist: {ist}" + (f"; Kern: Bemessungsgrundlage {ergebnis.kern_protokoll.get('summe', ergebnis.kern_protokoll.get('bemessungsgrundlage', '–'))}, Abgabe {ergebnis.kern_protokoll.get('abgabe', '–')}"
                                             + (f", ohne unsichere Leistungen {ergebnis.kern_protokoll['abgabe_ohne_unsichere']}" if 'abgabe_ohne_unsichere' in ergebnis.kern_protokoll else "")
                                             + (f", mit ihnen {ergebnis.kern_protokoll['abgabe_falls_kuenstlerisch']}" if 'abgabe_falls_kuenstlerisch' in ergebnis.kern_protokoll else "")
                                             if isinstance(getattr(ergebnis, 'kern_protokoll', None), dict) else ""),
                        f"- Fakten (System) bzw. Fundstellen (roh): {'; '.join(fakten) or '–'}",
                        f"- Verlauf: {' | '.join(schritte) or '–'}",
                        f"- Gründe: {'; '.join(gruende) or '–'}", ""]
        print(f"{fall['id']:6} {urteil:11} {ist}")

    quote = (100 * sicher_richtig / sicher_gesamt) if sicher_gesamt else 0.0
    bestanden = zaehler["FALSCH"] == 0 and zaehler["FEHLER"] == 0 and quote >= 90
    kopf = [
        f"# Prüfkatalog Stufe 1 – Lauf {datetime.date.today()} ({name})", "",
        f"Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Soll-Werte: `{katalog_anzeige}`.", "",
        f"**Ergebnis: {'BESTANDEN' if bestanden else 'NICHT BESTANDEN'}**", "",
        f"- Fälle: {len(faelle)}, Dauer gesamt {time.time() - start:.0f} s",
        f"- RICHTIG: {zaehler['RICHTIG']}, NACHGEFRAGT: {zaehler['NACHGEFRAGT']}, **FALSCH: {zaehler['FALSCH']}**, FEHLER: {zaehler['FEHLER']}",
        f"- Quote richtig bei Fällen mit sicherem Soll: {sicher_richtig} von {sicher_gesamt} = {quote:.0f} % (Ziel ≥ 90 %)",
        "- Ziel Stufe 1: 0 FALSCH, 0 FEHLER, Quote ≥ 90 %.", "",
        "| Fall | Fallgruppe | Soll | Ist | Bewertung | Dauer |", "|---|---|---|---|---|---|",
    ]
    bericht = "\n".join(kopf + zeilen + ["", "## Abweichungen im Einzelnen", ""] + (details or ["Keine."])) + "\n"
    print("\n".join(kopf[4:8]))
    if args.csv:
        import csv
        import subprocess

        try:
            stand = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                                   cwd=pathlib.Path(__file__).resolve().parent).stdout.strip()
        except OSError:
            stand = ""
        with open(args.csv, "w", encoding="utf-8", newline="") as datei:
            schreiber = csv.DictWriter(datei, fieldnames=["datum", "modus", "code_stand", "katalog", *csv_zeilen[0].keys()]
                                       if csv_zeilen else ["datum"])
            schreiber.writeheader()
            for z in csv_zeilen:
                schreiber.writerow({"datum": datetime.date.today().isoformat(), "modus": name, "code_stand": stand,
                                    "katalog": katalog_anzeige, **z})
        print(f"CSV: {args.csv}")
    if args.bericht:
        pathlib.Path(args.bericht).write_text(bericht, encoding="utf-8")
        print(f"Bericht: {args.bericht}")
    return 1 if (zaehler["FALSCH"] or zaehler["FEHLER"]) else 0


if __name__ == "__main__":
    sys.exit(main())
