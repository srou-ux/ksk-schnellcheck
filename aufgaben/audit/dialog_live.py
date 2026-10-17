"""Dialogtest Fallgrenzen – mit dem ECHTEN Modell, mehrfach wiederholt. Nur erfundene Daten.

Entwurf – vom Steuerberater zu prüfen. Ergänzt die Offline-Tests in
tests/app/test_dialog_fallgrenzen.py (kontrollierte Modellantworten): hier wird gemessen, was
ein echtes Modell im echten Ablauf (app/router.py, echter Prompt, echtes Schema) tut.

Aufruf (Windows und Linux gleich):
    python aufgaben/audit/dialog_live.py --llm fake --wiederholungen 1
    python aufgaben/audit/dialog_live.py --llm mistral --wiederholungen 5 --bericht aufgaben/audit/dialog_live_small.md
Modell über MISTRAL_MODELL, Schlüssel nur aus MISTRAL_API_KEY (wird nie ausgegeben).

Ein einzelner erfolgreicher Lauf ist kein Zuverlässigkeitsnachweis: der Bericht zählt je
Prüfpunkt, in wie vielen Wiederholungen er erfüllt war.
"""
from __future__ import annotations

import argparse
import datetime
import os
import pathlib
import subprocess
import sys
import time
from decimal import Decimal

WURZEL = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL))

from app import bestaetigung, router  # noqa: E402
from app import ergebnisklassen as EK  # noqa: E402

M1 = "Wir haben 2026 für unsere eigene Werbung vier Grafiken beauftragt. Jede Rechnung beträgt 200 Euro netto."
M2 = "Korrektur: Es waren drei Rechnungen. Alle anderen Angaben bleiben gleich."
M3 = ("Neuer, unabhängiger Fall: Ein Fotograf hat insgesamt 500 Euro netto berechnet. Ob sich dieser "
      "Betrag auf eine oder mehrere Rechnungen verteilt, ist unbekannt. Auch Jahr und Verwendungszweck "
      "sind unbekannt.")
M4 = "Das war 2025, für unsere eigene Werbung, der Fotograf ist Einzelperson."
# Beobachtung (Playground-Variante): Betrag ohne 'insgesamt', Rechnungszahl nicht genannt.
B1 = ("Neuer, unabhängiger Fall: Ein Fotograf hat uns 500 Euro netto berechnet. Jahr und "
      "Verwendungszweck sind noch unbekannt.")

ROH: list[dict] = []          # Rohfakten des Modells je Aufruf
ZEITEN: list[float] = []
PROTOKOLL: list[str] = []
_orig_protokolliere = router.protokolliere


def _protokolliere_mit(frage, jahr, grund, **kw):
    PROTOKOLL.append(str(grund)[:300])
    return _orig_protokolliere(frage, jahr, grund, **kw)


router.protokolliere = _protokolliere_mit


def _mitschnitt(llm):
    original = llm.extrahiere_fakten

    def extrahiere(frage, verlauf=None):
        t0 = time.time()
        try:
            fakten = original(frage, verlauf)
            ROH.append({"frage": frage[:40], "verlauf": len(verlauf or []),
                        "fakten": {k: v for k, v in fakten.model_dump(exclude_none=True, mode="json").items()
                                   if v not in ([], "", None) and k != "freitext_rest"}})
            return fakten
        finally:
            ZEITEN.append(time.time() - t0)

    llm.extrahiere_fakten = extrahiere
    return llm


class Oberflaeche:
    """Wie app/static/index.html: Verlauf und letzte Sitzungskennung werden mitgeschickt."""

    def __init__(self, llm):
        self.llm, self.verlauf, self.sitzung = llm, [], None

    def sende(self, text):
        a = router.bearbeite_frage(text, self.llm, list(self.verlauf), self.sitzung)
        self.verlauf.append(text)
        self.sitzung = a.sitzungskennung
        return a

    def knopf(self, feld, wert):
        a = router.wende_feldantwort_an(self.sitzung, feld, wert, self.llm)
        self.sitzung = a.sitzungskennung
        return a


def _fakten(sitzung):
    return bestaetigung.SPEICHER.hole_fakten(sitzung) if sitzung else None


def _betraege(f):
    return [Decimal(str(p.betrag)) for p in (f.positionen if f else [])]


def lauf_dialog_a(llm) -> tuple[dict[str, bool], list[str]]:
    """Ausgangsfall -> (Rechtsform per Knopf) -> Korrektur -> neuer Fall -> Ergänzung -> Ergebnis."""
    ui, ok, notizen = Oberflaeche(llm), {}, []
    a = ui.sende(M1)
    if a.ergebnisklasse == EK.RUECKFRAGE_NOETIG and ui.sitzung:
        a = ui.knopf("auftragnehmer_typ", "natuerliche_person")  # Nutzer klickt 'natürliche Person'
    f = _fakten(ui.sitzung)
    ok["1 Ausgangsfall: 2026, vier Rechnungen zu je 200 €"] = bool(f) and f.jahr == 2026 and _betraege(f) == [Decimal(200)] * 4
    alte_sitzung, alter_hash = ui.sitzung, a.fakten_hash

    a = ui.sende(M2)
    f = _fakten(ui.sitzung)
    ok["2 Korrektur: drei Rechnungen, Jahr bleibt 2026"] = bool(f) and f.jahr == 2026 and _betraege(f) == [Decimal(200)] * 3
    ok["2 Korrektur: alte Bestätigung ungültig"] = not (alter_hash and bestaetigung.SPEICHER.bestaetige(ui.sitzung, alter_hash))

    a = ui.sende(M3)
    f = _fakten(ui.sitzung)
    ok["3 Neuer Fall: neue Sitzung"] = ui.sitzung is not None and ui.sitzung != alte_sitzung
    ok["3 Neuer Fall: nichts aus dem alten Fall übernommen (Jahr, Zweck leer)"] = bool(f) and f.jahr is None and f.verwerterart is None
    ok["3 Neuer Fall: keine Rechnungsposition erfunden"] = bool(f) and not f.positionen
    ok["3 Neuer Fall: Gesamtbetrag 500 € erhalten"] = bool(f) and f.gesamtbetrag_genannt == Decimal(500)
    # Beobachtung, kein Übernahmefehler: der Verlauf des alten Falls geht nicht ans Modell; setzt
    # es trotzdem eine Rechtsform, ist das eine Ableitung aus 'Ein Fotograf' (Prompt verbietet das).
    ok["3 Beobachtung: Modell setzt keine Rechtsform ohne Beleg"] = bool(f) and f.auftragnehmer_typ is None
    if f:
        notizen.append(f"nach 3: positionen={_betraege(f)}, gesamtbetrag={f.gesamtbetrag_genannt}, jahr={f.jahr}, rechtsform={f.auftragnehmer_typ}")

    a = ui.sende(M4)
    gefragt = list(a.rueckfragen or [])
    f = _fakten(ui.sitzung)
    ok["4 Ergänzung: Jahr 2025 übernommen"] = bool(f) and f.jahr == 2025
    ok["4 Ergänzung: nicht erneut nach Jahr oder Betrag gefragt"] = not any(
        ("Kalenderjahr" in r or "Betrag" in r) for r in gefragt)
    ok["4 Ergänzung: ohne Rückfrage (Modell übernimmt 'eigene Werbung'/'Einzelperson')"] = a.ergebnisklasse != EK.RUECKFRAGE_NOETIG
    # Wie ein Nutzer: nur die Knöpfe drücken, deren Antwort in der Nachricht stand.
    for _ in range(3):
        if a.ergebnisklasse != EK.RUECKFRAGE_NOETIG:
            break
        felder = [o.get("feld") for o in (a.rueckfrage_optionen or [])]
        if "verwerterart" in felder:
            a = ui.knopf("verwerterart", "eigenwerber")
        elif "auftragnehmer_typ" in felder:
            a = ui.knopf("auftragnehmer_typ", "natuerliche_person")
        else:
            break
    ok["4 Bestätigung ohne erfundene Position"] = a.ergebnisklasse == EK.FAKTEN_BESTAETIGUNG_NOETIG and not any(
        z.startswith("Position ") for z in a.fakten_zusammenfassung)
    ergebnis = None
    if a.ergebnisklasse == EK.FAKTEN_BESTAETIGUNG_NOETIG:
        bestaetigung.SPEICHER.bestaetige(a.sitzungskennung, a.fakten_hash)
        ergebnis = router.fuehre_nach_bestaetigung_aus(a.sitzungskennung, llm)
    ok["4 Ergebnis: nicht abgabepflichtig (500 € ≤ 700 €, 2025)"] = bool(ergebnis) and ergebnis.ergebnisklasse == EK.NICHT_ABGABEPFLICHTIG
    notizen.append(f"Rückfragen nach der Ergänzung: {gefragt or 'keine'}")
    notizen.append(f"Ergebnis: {ergebnis.ergebnisklasse if ergebnis else a.ergebnisklasse}; Fakten: {'; '.join(a.fakten_zusammenfassung)}")
    return ok, notizen


def lauf_beobachtung_b(llm) -> str:
    """Playground-Variante ohne 'insgesamt': nur beobachten, wie das Modell den Betrag ablegt."""
    ui = Oberflaeche(llm)
    ui.sende(M1)
    ui.sende(B1)
    f = _fakten(ui.sitzung)
    if not f:
        return "keine Fakten (Modellfehler?)"
    return (f"positionen={_betraege(f)}, gesamtbetrag={f.gesamtbetrag_genannt}, jahr={f.jahr}, "
            f"verwerterart={f.verwerterart}")


def _codeversion() -> str:
    sha = os.environ.get("GITHUB_SHA")
    if sha:
        return sha[:12]
    try:
        return subprocess.run(["git", "rev-parse", "--short=12", "HEAD"], cwd=WURZEL, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return "unbekannt"


def main() -> int:
    ap = argparse.ArgumentParser(description="Dialogtest Fallgrenzen")
    ap.add_argument("--llm", choices=["fake", "mistral"], default="fake")
    ap.add_argument("--wiederholungen", type=int, default=5)
    ap.add_argument("--bericht")
    args = ap.parse_args()

    if args.llm == "mistral":
        if not os.environ.get("MISTRAL_API_KEY"):
            print("KEIN SCHLÜSSEL: MISTRAL_API_KEY ist nicht gesetzt. Nichts getestet.")
            return 0
        from app.llm import mistral as M
        einstellungen = (f"Modell {M.MISTRAL_MODELL}; temperature 0.0, top_p 1 (fest in app/llm/mistral.py); "
                         f"Timeout {M.MISTRAL_TIMEOUT} s; Wiederholungen bei 429/503: {M.MISTRAL_RETRY_VERSUCHE}, "
                         f"Wartezeiten {M.MISTRAL_RETRY_WARTEZEITEN}")
        neues_llm = lambda: _mitschnitt(M.MistralLLM())  # noqa: E731
    else:
        from app.llm.fake import FakeLLM
        einstellungen = "Demo-Modus (FakeLLM, Regex-Heuristik, kein Sprachmodell)"
        neues_llm = lambda: _mitschnitt(FakeLLM())  # noqa: E731

    zaehler: dict[str, int] = {}
    zeilen, fehler, schutz, beobachtungen = [], [], [], []
    start = time.time()
    for n in range(1, args.wiederholungen + 1):
        PROTOKOLL.clear()
        ROH.clear()
        try:
            ok, notizen = lauf_dialog_a(neues_llm())
        except Exception as e:  # technischer Fehler ist ein Befund, kein Abbruch
            ok, notizen = {}, [f"AUSNAHME {type(e).__name__}: {str(e)[:200]}"]
            fehler.append(f"Lauf {n}: {type(e).__name__}: {str(e)[:200]}")
        for name, erfuellt in ok.items():
            zaehler[name] = zaehler.get(name, 0) + int(erfuellt)
        verfehlt = [name for name, erfuellt in ok.items() if not erfuellt]
        roh_dialog = list(ROH)
        for eintrag in dict.fromkeys(PROTOKOLL):
            # Technisch = das Modell/der Dienst hat versagt. Alles andere im Lückenprotokoll ist
            # ein Schutzmechanismus, der gegriffen hat (z. B. 'Fallbeschreibung verworfen':
            # nur der Modellsatz entfällt, die Antwort bleibt; Teil 1g).
            technisch = any(w in eintrag for w in ("Extraktion fehlgeschlagen", "HTTP", "Zeitueberschreitung",
                                                    "nicht verfuegbar", "kein gueltiges JSON", "Schema"))
            (fehler if technisch else schutz).append(f"Lauf {n}: {eintrag}")
        zeilen += [f"### Lauf {n}", f"- verfehlt: {', '.join(verfehlt) or 'nichts'}"]
        zeilen += [f"- {x}" for x in notizen]
        zeilen += [f"- Modell-Rohfakten je Nachricht: " + " | ".join(
            f"[{r['frage']}… Verlauf {r['verlauf']}] {r['fakten']}" for r in roh_dialog), ""]
        try:
            beobachtungen.append(f"Lauf {n}: {lauf_beobachtung_b(neues_llm())}")
        except Exception as e:
            beobachtungen.append(f"Lauf {n}: AUSNAHME {type(e).__name__}")

    kopf = [
        f"# Dialogtest Fallgrenzen – {datetime.datetime.now():%Y-%m-%d %H:%M}",
        "", "Entwurf – vom Steuerberater zu prüfen. Nur erfundene Daten.", "",
        f"- Codeversion: `{_codeversion()}`",
        f"- Einstellungen: {einstellungen}",
        f"- Wiederholungen: {args.wiederholungen}; Dauer gesamt {time.time() - start:.0f} s; "
        f"Modellaufrufe (Extraktion): {len(ZEITEN)}, Mittel {sum(ZEITEN)/len(ZEITEN) if ZEITEN else 0:.1f} s, "
        f"längster {max(ZEITEN) if ZEITEN else 0:.1f} s",
        f"- Technische Fehler: {len(fehler)}; Schutzmechanismus griff (Protokoll): {len(schutz)}", "",
        "| Prüfpunkt | erfüllt |", "|---|---|",
    ] + [f"| {k} | {v} von {args.wiederholungen} |" for k, v in zaehler.items()]
    teile = kopf + ["", "## Technische Fehler", ""] + ([f"- {x}" for x in fehler] or ["Keine."])
    teile += ["", "## Schutzmechanismus griff (kein Fehler, nur zur Nachverfolgung)", ""] + ([f"- {x}" for x in schutz] or ["Keine."])
    teile += ["", "## Beobachtung: '500 Euro berechnet' ohne 'insgesamt' (Playground-Variante)", ""]
    teile += [f"- {b}" for b in beobachtungen]
    teile += ["", "## Einzelne Läufe", ""] + zeilen
    bericht = "\n".join(teile) + "\n"
    print("\n".join(kopf))
    if args.bericht:
        pathlib.Path(args.bericht).write_text(bericht, encoding="utf-8")
        print(f"Bericht: {args.bericht}")
    alle_erfuellt = zaehler and all(v == args.wiederholungen for v in zaehler.values())
    return 0 if alle_erfuellt and not fehler else 1


if __name__ == "__main__":
    sys.exit(main())
