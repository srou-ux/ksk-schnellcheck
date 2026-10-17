"""Abruf-Güte messen (RAG, Auftrag Teil 2, Abschnitt 'Tests').

    python -m app.rag.guete            # schreibt aufgaben/RAG_Bericht.md

Für jeden Testfall aus regelwerk/Testfaelle_BSG_Urteile.xlsx (Blatt 'Testfälle', Spalte
Fundstelle) wird mit Beschreibung + Eingaben und dem Jahr gesucht (NICHT mit der Begründung oder
der Fundstelle -- sonst wäre die Antwort im Suchtext). Treffer, wenn eine Kernangabe der
erwarteten Fundstelle unter den ersten 5 Plätzen der Relevanzliste steht:
- Regel-ID (R-12) in den Regel-IDs des Stücks,
- Aktenzeichen (B 3 KS 3/21 R) in der Fundstelle des Stücks,
- Gesetz + Paragraf (+ Absatz, wenn genannt), z. B. KSVG § 24 Abs. 2,
- Dokument (KSK-Info 13, DRV K5006, KSK-FAQ ...) als Quelle des Stücks.
Abgleich auf Ebene Absatz bzw. Dokument, nicht Satz/Seite -- das steht so auch im Bericht.
Die JSON-Testfälle (regelwerk/testfaelle_maschinenlesbar.json) haben KEIN Feld Fundstelle und
fließen deshalb nicht ein (im Bericht vermerkt). Nichts wird schöngerechnet: Fälle mit einem Jahr
außerhalb des Registers zählen getrennt."""
from __future__ import annotations

import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from app.rag.index import WURZEL, Basis
from app.rag.suche import Treffer, suche

TESTFAELLE = WURZEL / "regelwerk" / "Testfaelle_BSG_Urteile.xlsx"
BERICHT = WURZEL / "aufgaben" / "RAG_Bericht.md"
PLAETZE = 5

_RID = re.compile(r"\bR-\d+\b")
_AZ = re.compile(r"\b([A-Z])\s?(\d+)\s?([A-Z]{1,3})\s?(\d+/\d+)(\s?R)?\b")
_GESETZ = r"(KSVG|KSAbg\d{4}V|SGB\s?[IVX]+|EStG|SGG|HGB|KSVEntgV|KSVGBeitrÜV|KSKSaV)"
_PARA_VOR = re.compile(_GESETZ + r"\s*§§?\s*(\d+[a-z]?)(?:\s*Abs\.?\s*(\d+))?")
_PARA_NACH = re.compile(r"§§?\s*(\d+[a-z]?)(?:\s*Abs\.?\s*(\d+))?(?:\s*(?:S\.|Satz)\s*\d+)?(?:\s*Nr\.?\s*\d+)?\s+" + _GESETZ)
_DOK = re.compile(r"(KSK-Info\s?\d+a?|Info\s\d+a?|DRV\s?K\d{4}|KSK-FAQ|(?:KSK-)?Checkliste\s(?:für\s)?\w+|Ausfüllhinweise|Meldebogen|Handlungshilfen|Merkblatt|Fragebogen)")


def _norm_az(t: str) -> str:
    return re.sub(r"\s+", "", t).upper()


def kernangaben(fundstelle: str) -> list[tuple[str, tuple]]:
    """Zerlegt eine erwartete Fundstelle in prüfbare Kernangaben (in der Reihenfolge des Textes)."""
    erg: list[tuple[int, tuple[str, tuple]]] = []
    for m in _RID.finditer(fundstelle):
        erg.append((m.start(), ("regel", (m.group(0),))))
    for m in _AZ.finditer(fundstelle):
        erg.append((m.start(), ("az", (_norm_az(m.group(0)).removesuffix("R"),))))
    for m in _PARA_VOR.finditer(fundstelle):
        erg.append((m.start(), ("para", (re.sub(r"\s", "", m.group(1)), m.group(2), m.group(3)))))
    for m in _PARA_NACH.finditer(fundstelle):
        erg.append((m.start(), ("para", (re.sub(r"\s", "", m.group(3)), m.group(1), m.group(2)))))
    for m in _DOK.finditer(fundstelle):
        d = m.group(1)
        if d.startswith("Info "):
            d = "KSK-" + d
        cl = re.match(r"(?:KSK-)?Checkliste\s(?:für\s)?(\w+)", d)
        if cl:
            d = "checkliste" + cl.group(1)[:6]
        erg.append((m.start(), ("dok", (re.sub(r"\s", "", d).lower(),))))
    erg.sort(key=lambda x: x[0])
    gesehen, out = set(), []
    for _, k in erg:
        if k not in gesehen:
            gesehen.add(k)
            out.append(k)
    return out


_GESETZ_RE = re.compile(_GESETZ)
_PARA_RE = re.compile(r"§§?\s*(\d+[a-z]?)")
_ABS_RE = re.compile(r"Abs\.?\s*(\d+(?:\s*(?:,|und)\s*\d+(?!\s*(?:Satz|S\.\s)))*)")


def stellen_in(fundstelle: str) -> set[tuple[str, str, str | None]]:
    """Alle (Gesetz, Paragraf, Absatz) einer Fundstelle, auch Aufzählungen:
    'KSVG § 24 Abs. 1 Satz 2, Abs. 3' -> (KSVG,24,1), (KSVG,24,3);
    'SGG § 78 Abs. 1, § 84 Abs. 1 und 2' -> (SGG,78,1), (SGG,84,1), (SGG,84,2).
    Je durch ';' getrenntem Teil gilt das darin genannte Gesetz (davor oder danach)."""
    erg: set[tuple[str, str, str | None]] = set()
    for teil in fundstelle.split(";"):
        gesetz = _GESETZ_RE.search(teil)
        if not gesetz:
            continue
        name = re.sub(r"\s", "", gesetz.group(1))
        treffer = list(_PARA_RE.finditer(teil))
        for i, m in enumerate(treffer):
            ende = treffer[i + 1].start() if i + 1 < len(treffer) else len(teil)
            rest = teil[m.end():ende]
            absaetze = [n for a in _ABS_RE.finditer(rest) for n in re.findall(r"\d+", a.group(1))]
            if absaetze:
                erg.update((name, m.group(1), a) for a in absaetze)
            else:
                erg.add((name, m.group(1), None))
    return erg


def passt(angabe: tuple[str, tuple], t: Treffer) -> bool:
    art, werte = angabe
    fund = t.fundstelle or ""
    if art == "regel":
        return werte[0] in t.regel_ids
    if art == "az":
        return werte[0] in _norm_az(fund)
    if art == "para":
        gesetz, para, absatz = werte
        for g, p, a in stellen_in(fund):
            if g == gesetz and p == para and (absatz is None or a is None or a == absatz):
                return True
        return False
    if art == "dok":
        quelle = re.sub(r"\s|für", "", f"{t.quelle_id} {fund}").lower()
        return werte[0] in quelle
    return False


@dataclass
class Fall:
    id: str
    gruppe: str
    jahr: int | None
    suchtext: str
    fundstelle: str


_BEZUG = re.compile(r"^(?:Wie|Derselbe Fall wie|Gleicher Fall wie)\s+([A-Z]{1,2}-\d{2,3}[a-z]?)\b")


def lies_faelle(pfad: Path = TESTFAELLE) -> list[Fall]:
    import openpyxl

    ws = openpyxl.load_workbook(pfad, read_only=True, data_only=True)["Testfälle"]
    zeilen = [z for z in ws.iter_rows(min_row=2, values_only=True) if z and z[0]]
    text = {str(z[0]): f"{z[2] or ''} {z[4] or ''}".strip() for z in zeilen}

    def mit_bezug(fid: str, tiefe: int = 0) -> str:
        """'Wie I-01, aber …' beschreibt nur den Unterschied. Ein Nutzer würde den Grundfall
        mitschildern: dessen Text wird vorangestellt (auch über mehrere Stufen)."""
        eigen = text.get(fid, "")
        m = _BEZUG.match(eigen)
        if not m or tiefe > 5 or m.group(1) not in text:
            return eigen
        return f"{mit_bezug(m.group(1), tiefe + 1)} {eigen}"

    erg = []
    for z in zeilen:
        if not z[7]:
            continue
        try:
            jahr = int(str(z[3]).strip())
        except (TypeError, ValueError):
            jahr = None
        erg.append(Fall(str(z[0]), str(z[1] or ""), jahr, mit_bezug(str(z[0])), str(z[7])))
    return erg


def miss(basis: Basis | None = None, faelle: list[Fall] | None = None) -> dict:
    faelle = faelle if faelle is not None else lies_faelle()
    erg = {"faelle": [], "zaehler": Counter(), "gruppen": defaultdict(Counter)}
    for f in faelle:
        angaben = kernangaben(f.fundstelle)
        e = suche(f.suchtext, f.jahr, basis=basis)
        oben = e.relevanz[:PLAETZE]
        if e.grund and not e.relevanz and f.jahr is not None and "Jahr" in e.grund:
            status = "jahr_nicht_abgedeckt"
        elif not angaben:
            status = "keine_kernangabe"
        else:
            treffer_alle = any(passt(a, t) for a in angaben for t in oben)
            treffer_erste = any(passt(angaben[0], t) for t in oben)
            status = "treffer" if treffer_alle else "fehlschlag"
            if treffer_erste:
                erg["zaehler"]["erste_angabe"] += 1
            if any(passt(a, t) for a in angaben for t in e.stuecke):
                erg["zaehler"]["geliefert_treffer"] += 1
            if not e.stuecke:
                erg["zaehler"]["geliefert_leer"] += 1
        erg["zaehler"][status] += 1
        erg["gruppen"][f.gruppe][status] += 1
        erg["faelle"].append((f, status, angaben, [t.fundstelle for t in oben]))
    return erg


GEGENPROBEN = Path(__file__).resolve().parent / "gegenproben.json"


def gegenproben(basis: Basis | None = None) -> list[tuple[str, bool, list[str]]]:
    import json

    fragen = json.loads(GEGENPROBEN.read_text(encoding="utf-8"))["fragen"]
    erg = []
    for q in fragen:
        e = suche(q, basis=basis)
        erg.append((q, not e.stuecke, [t.fundstelle for t in e.stuecke[:3]]))
    return erg


def schreibe_bericht(erg: dict, pfad: Path = BERICHT) -> str:
    z = erg["zaehler"]
    gewertet = z["treffer"] + z["fehlschlag"]
    quote = 100.0 * z["treffer"] / gewertet if gewertet else 0.0
    quote_erste = 100.0 * z["erste_angabe"] / gewertet if gewertet else 0.0
    alle = gewertet + z["jahr_nicht_abgedeckt"] + z["keine_kernangabe"]
    from app.rag.zerlegen import KONFIG

    ziel, prozent = KONFIG["guete_ziel_prozent"], "%"
    zeilen = [
        "# RAG – Bericht Abruf-Güte", "",
        ("Erzeugt von `python -m app.rag.guete` MIT Embeddings (RAG_EMBEDDINGS=1, Mistral EU), ohne Sprachmodell."
         if os.environ.get("RAG_EMBEDDINGS") == "1" else
         "Erzeugt von `python -m app.rag.guete` (offline, ohne Embeddings, ohne Sprachmodell)."), "",
        f"Testfälle mit Fundstelle: **{alle}** (regelwerk/Testfaelle_BSG_Urteile.xlsx). "
        "Die JSON-Testfälle (regelwerk/testfaelle_maschinenlesbar.json) haben kein Feld Fundstelle und fehlen deshalb hier.", "",
        "| Kennzahl | Wert |", "|---|---|",
        f"| Gewertet (Jahr im Register, Kernangabe erkennbar) | {gewertet} |",
        f"| **Treffer: eine Kernangabe der erwarteten Fundstelle unter den ersten {PLAETZE}** | **{z['treffer']} ({quote:.1f} %)** |",
        f"| Strenger: die ERSTE Kernangabe unter den ersten {PLAETZE} | {z['erste_angabe']} ({quote_erste:.1f} %) |",
        f"| Fehlschläge | {z['fehlschlag']} |",
        f"| Erwartete Fundstelle unter den GELIEFERTEN Stücken (höchstens 8, nach Mindestabdeckung) | {z['geliefert_treffer']} ({(100.0 * z['geliefert_treffer'] / gewertet if gewertet else 0):.1f} %) |",
        f"| Geliefert leer („Nicht abgedeckt“), obwohl eine Fundstelle erwartet war | {z['geliefert_leer']} |",
        f"| Jahr außerhalb des Registers → leer + „Nicht abgedeckt“ (so gewollt) | {z['jahr_nicht_abgedeckt']} |",
        f"| Erwartete Fundstelle ohne prüfbare Kernangabe | {z['keine_kernangabe']} |", "",
        f"Ziel des Auftrags: ≥ {ziel} {prozent}. Ergebnis: {'erreicht' if quote >= ziel else 'NICHT erreicht'}.", "",
        "Abgleich auf Ebene Absatz (Gesetz) bzw. Dokument (KSK/DRV) bzw. Aktenzeichen (Urteil) bzw. Regel-ID – "
        "nicht auf Satz, Randnummer oder Seite.", "",
        "## Nach Gruppe", "", "| Gruppe | Treffer | Fehlschläge | Jahr nicht abgedeckt |", "|---|---|---|---|",
    ]
    for g, c in sorted(erg["gruppen"].items()):
        zeilen.append(f"| {g} | {c['treffer']} | {c['fehlschlag']} | {c['jahr_nicht_abgedeckt']} |")
    zeilen += ["", "## Fehlschläge", "", "| ID | Jahr | Erwartet | Erste 5 Treffer |", "|---|---|---|---|"]
    for f, status, angaben, oben in erg["faelle"]:
        if status == "fehlschlag":
            zeilen.append(f"| {f.id} | {f.jahr or '–'} | {f.fundstelle.replace('|', '/')} | "
                          f"{' · '.join(o.replace('|', '/') for o in oben) or '–'} |")
    proben = gegenproben()
    zeilen += ["", "## Gegenproben (Fragen ohne Quelle, Soll: leer → „Nicht abgedeckt“)", "",
               f"Richtig leer: **{sum(1 for _, leer, _ in proben if leer)} von {len(proben)}** (app/rag/gegenproben.json).", "",
               "| Frage | Ergebnis | geliefert (erste 3) |", "|---|---|---|"]
    zeilen += [f"| {q} | {'leer (richtig)' if leer else '**NICHT leer**'} | {' · '.join(f) or '–'} |" for q, leer, f in proben]
    zeilen += ["", "## Ohne prüfbare Kernangabe", ""]
    zeilen += [f"- {f.id}: {f.fundstelle}" for f, s, _, _ in erg["faelle"] if s == "keine_kernangabe"] or ["–"]
    text = "\n".join(zeilen) + "\n"
    pfad.write_text(text, encoding="utf-8")
    return f"Abruf-Güte: {z['treffer']}/{gewertet} = {quote:.1f} % (erste Angabe {quote_erste:.1f} %), " \
           f"Jahr nicht abgedeckt {z['jahr_nicht_abgedeckt']}, ohne Kernangabe {z['keine_kernangabe']}"


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Abruf-Güte messen")
    ap.add_argument("--bericht", default=str(BERICHT), help="Zieldatei des Berichts")
    a = ap.parse_args()
    print(schreibe_bericht(miss(), Path(a.bericht)))
    sys.exit(0)
