"""Abgleich Register ↔ Quelle (RAG, Auftrag Teil 2, 'Keine Festwerte').

    python -m app.rag.abgleich        # schreibt aufgaben/RAG_Abgleich.md

Für jede Zeile des Regelregisters und jede Zeile der Blätter 'Schwellen nach Jahr',
'Abgabesätze' und 'Pauschalen nach Jahr' wird geprüft, ob der eingetragene Wert im Text der
genannten Fundstelle vorkommt (für das Jahr der Zeile). Es wird NUR verglichen: kein Wert wird aus
einem Text gelesen oder übernommen, gerechnet wird weiter nur mit dem Register (kern/).

Ergebnis je Zeile:
- bestätigt            Wert steht in der genannten Stelle,
- nur im Dokument      Wert steht in der Quelle, aber nicht in der genannten Stelle,
- ABWEICHUNG           genannte Stelle gefunden, Wert steht dort nicht,
- Fundstelle fehlt     keine passende Stelle im Index (Quelle nicht in der Basis oder nicht zerlegbar),
- nicht prüfbar        kein Zahlenwert (z. B. Rechtsform, ja/nein, Operator)."""
from __future__ import annotations

import re
import sqlite3
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.rag.guete import kernangaben
from app.rag.index import Basis, _blatt, _int
from app.rag.suche import Treffer, _db, _zeile
from app.rag.zerlegen import KONFIG

STATUS_ORDNUNG = ["ABWEICHUNG", "Fundstelle fehlt", "nur im Dokument", "bestätigt", "nicht prüfbar"]


@dataclass
class Pruefzeile:
    blatt: str
    schluessel: str
    jahr: int | None
    wert: str
    fundstelle: str
    status: str = ""
    beleg: str = ""


def schreibweisen(wert: str) -> list[str]:
    """Deutsche Schreibweisen eines Zahlenwerts ('4.9' -> '4,9'; '1000' -> '1.000', '1000';
    '5' -> '5', '5,0'). Kein Rechnen: nur Darstellungen desselben Werts."""
    m = re.search(r"\d[\d.]*(?:,\d+)?", str(wert))
    if not m:
        return []
    roh = m.group(0)
    try:
        d = Decimal(roh.replace(".", "").replace(",", ".")) if "," in roh or re.fullmatch(r"\d{1,3}(\.\d{3})+", roh) \
            else Decimal(roh)
    except InvalidOperation:
        return []
    ganz = d == d.to_integral_value()
    if ganz:
        n = int(d)
        formen = {str(n), f"{n:,}".replace(",", "."), f"{n:,}".replace(",", " "), f"{n:,}".replace(",", "\u00a0"),
                  f"{n},0", f"{n},00"}
    else:
        t = format(d.normalize(), "f")
        formen = {t.replace(".", ","), t}
    return sorted(formen, key=len, reverse=True)


def _kommt_vor(formen: list[str], text: str) -> bool:
    for f in formen:
        # danach darf ',00' folgen (2.400,00 = 2400), aber keine weitere Ziffer ungleich null
        if re.search(r"(?<![\d,.])" + re.escape(f) + r"(?!\d)(?!,\d*[1-9])(?!\.\d)", text):
            return True
    return False


def _passt_jahr(t: Treffer, jahr: int | None) -> bool:
    return jahr is None or ((t.gilt_von is None or t.gilt_von <= jahr) and (t.gilt_bis is None or t.gilt_bis >= jahr))


def _stellen(db: sqlite3.Connection, fundstelle: str, beleg: str, jahr: int | None) -> tuple[list[Treffer], list[Treffer]]:
    """(genannte Stellen, ganzes Dokument) aus dem Index -- über Datei (Beleg) und Fundstelle."""
    from app.rag.guete import passt

    alle: list[Treffer] = []
    dateien = [b.strip().removeprefix("quellen/") for b in re.findall(r"quellen/[^\s,;]+", beleg or "")]
    for d in dateien:
        alle += [_zeile(r, 0, set()) for r in db.execute("SELECT * FROM stuecke WHERE datei=?", (d,))]
    angaben = [a for a in kernangaben(fundstelle) if a[0] in ("para", "dok", "az")]
    if angaben:
        kandidaten = [_zeile(r, 0, set()) for r in db.execute(
            "SELECT * FROM stuecke WHERE art NOT IN ('Regel','Register')")]
        for t in kandidaten:
            if any(passt(a, t) for a in angaben) and _passt_jahr(t, jahr):
                alle.append(t)
    alle = [t for t in alle if _passt_jahr(t, jahr)]
    genannt = alle
    if angaben:
        genannt = [t for t in alle if any(passt(a, t) for a in angaben)]
    dokument_dateien = {t.datei for t in alle}
    dokument = [_zeile(r, 0, set()) for d in dokument_dateien
                for r in db.execute("SELECT * FROM stuecke WHERE datei=?", (d,))]
    return genannt, [t for t in dokument if _passt_jahr(t, jahr)]


def lies_register(basis: Basis) -> list[Pruefzeile]:
    import openpyxl

    wb = openpyxl.load_workbook(basis.regelkatalog, read_only=True, data_only=True)
    zeilen: list[Pruefzeile] = []
    ws = _blatt(wb, "Regelregister")
    if ws is not None:
        for z in ws.iter_rows(min_row=2, values_only=True):
            if not z or not z[0]:
                continue
            schl, wert, einheit, _op, von, _bis, _bed, _rid, fund = (list(z) + [None] * 10)[:9]
            zeilen.append(Pruefzeile("Regelregister", f"{schl} ({einheit})", _int(von), str(wert), str(fund or "")))
    ws = _blatt(wb, "Schwellen nach Jahr")
    if ws is not None:
        for z in ws.iter_rows(min_row=2, values_only=True):
            if z and _int(z[0]):
                zeilen.append(Pruefzeile("Schwellen nach Jahr", "Schwelle", _int(z[0]), str(z[2]), str(z[3] or ""),
                                         beleg=str(z[4] or "")))
    ws = _blatt(wb, "Abgabesätze")
    if ws is not None:
        for z in ws.iter_rows(min_row=2, values_only=True):
            if z and _int(z[0]):
                zeilen.append(Pruefzeile("Abgabesätze", "Abgabesatz", _int(z[0]), str(z[1]), str(z[2] or ""),
                                         beleg=str(z[3] or "")))
    ws = _blatt(wb, "Pauschalen nach Jahr")
    if ws is not None:
        for z in ws.iter_rows(min_row=2, values_only=True):
            if z and _int(z[0]):
                zeilen.append(Pruefzeile("Pauschalen nach Jahr", "Übungsleiterpauschale", _int(z[0]), str(z[1]), str(z[4] or "")))
                zeilen.append(Pruefzeile("Pauschalen nach Jahr", "Ehrenamtspauschale", _int(z[0]), str(z[2]), str(z[4] or "")))
    return zeilen


def gleiche_ab(basis: Basis | None = None) -> list[Pruefzeile]:
    basis = basis or Basis()
    zeilen = lies_register(basis)
    db = _db(basis)
    try:
        for z in zeilen:
            formen = schreibweisen(z.wert)
            if not formen:
                z.status = "nicht prüfbar"
                continue
            genannt, dokument = _stellen(db, z.fundstelle, z.beleg, z.jahr)
            if not genannt and not dokument:
                z.status = "Fundstelle fehlt"
            elif any(_kommt_vor(formen, t.text) for t in genannt):
                z.status = "bestätigt"
            elif any(_kommt_vor(formen, t.text) for t in dokument):
                z.status = "nur im Dokument"
            else:
                z.status = "ABWEICHUNG"
    finally:
        db.close()
    return zeilen


def schreibe_bericht(zeilen: list[Pruefzeile], pfad: Path | None = None) -> str:
    pfad = pfad or Basis().wurzel / KONFIG["abgleich_pfad"]
    zaehler = {s: sum(1 for z in zeilen if z.status == s) for s in STATUS_ORDNUNG}
    text = ["# RAG – Abgleich Register ↔ Quelle", "",
            "Erzeugt von `python -m app.rag.abgleich`. Geprüft wird nur, ob der eingetragene Wert im Text der "
            "genannten Fundstelle vorkommt; kein Wert wird aus Texten übernommen. Die Ergebnisse sind Hinweise "
            "für die menschliche Prüfung, keine Freigabe.", "",
            "| Ergebnis | Anzahl |", "|---|---|", *(f"| {s} | {n} |" for s, n in zaehler.items()), "",
            "| Ergebnis | Blatt | Schlüssel | Jahr | Wert | Fundstelle |", "|---|---|---|---|---|---|"]
    for z in sorted(zeilen, key=lambda z: (STATUS_ORDNUNG.index(z.status), z.blatt, z.jahr or 0)):
        text.append(f"| {z.status} | {z.blatt} | {z.schluessel} | {z.jahr or '–'} | {z.wert.replace('|', '/')[:60]} | "
                    f"{z.fundstelle.replace('|', '/')[:110]} |")
    pfad.write_text("\n".join(text) + "\n", encoding="utf-8")
    return ", ".join(f"{s}: {n}" for s, n in zaehler.items())


if __name__ == "__main__":
    print("Abgleich Register ↔ Quelle –", schreibe_bericht(gleiche_ab()))
    sys.exit(0)
