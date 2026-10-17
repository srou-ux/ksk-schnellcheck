"""Erzeugt regelwerk/Pruefliste_Taetigkeiten_Entwurf.xlsx für den Steuerberater (11.10.2026).

Inhalt (alles aus dem Regelkatalog gelesen, nichts doppelt gepflegt):
- Blatt 'Tätigkeiten': die Zeilen des Blatts 'Tätigkeitsabgrenzung' mit Regeltext und Fundstellen,
- Blatt 'Textbausteine': TB-17 bis TB-23 (neu, noch ungeprüft),
- Blatt 'Testfall 20': Soll der Testdatei gegen das Ergebnis des SaaS (mistral-large-latest),
- Blatt 'Offene Fragen': Fragen, die nur ein Berufsträger entscheiden kann.

Aufruf aus dem Projektstamm (Windows und Linux gleich):
    python scripts/erzeuge_pruefliste_taetigkeiten.py
SCHUTZ: Steht in der bestehenden Prüfliste schon eine Entscheidung, bricht das Skript ab --
Entscheidungen des Steuerberaters dürfen nicht verloren gehen.
"""
from __future__ import annotations

import pathlib
import re
import sys

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

WURZEL = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
ZIEL = WURZEL / "regelwerk" / "Pruefliste_Taetigkeiten_Entwurf.xlsx"
KATALOG = WURZEL / "regelwerk" / "Regelkatalog_24_KSVG_Entwurf.xlsx"
TESTFALL = WURZEL / "aufgaben" / "audit" / "testfall_20_positionen.json"
ERGEBNIS = WURZEL / "aufgaben" / "audit" / "testfall20_ergebnis_large.md"
ENTSCHEIDUNG = '"offen,freigeben,mit Änderung freigeben,ablehnen,Rückfrage an KSK/DRV"'
OFFEN = "offen"

# Spalten, in die der Steuerberater schreibt (je Blatt: Entscheidung + weitere Felder).
EINTRAGSSPALTEN = ("Entscheidung", "Richtige Gruppe", "Richtig beim selben Künstler", "Begründung / Änderung",
                   "Antwort", "Geprüft von", "Datum", "Soll richtig?", "Richtiges Soll")


def _schutz() -> None:
    if not ZIEL.exists():
        return
    wb = openpyxl.load_workbook(ZIEL)
    for ws in wb.worksheets:
        kopf = [c.value for c in ws[1]]
        spalten = [i for i, k in enumerate(kopf) if k in EINTRAGSSPALTEN]
        for zeile in ws.iter_rows(min_row=2, values_only=True):
            for i in spalten:
                wert = zeile[i] if i < len(zeile) else None
                if wert not in (None, "", OFFEN):
                    sys.exit(f"ABBRUCH: In '{ws.title}' stehen schon Eintragungen des Steuerberaters. Nicht überschreiben.")


def _regeln() -> dict[str, dict[str, str]]:
    ws = openpyxl.load_workbook(KATALOG, read_only=True)["Regeln"]
    zeilen = list(ws.iter_rows(values_only=True))
    ix = {k: i for i, k in enumerate(zeilen[0])}
    ergebnis = {}
    for r in zeilen[1:]:
        if r[0]:
            ergebnis[r[0]] = {k: str(r[ix[k]] or "") for k in ("Voraussetzung", "Rechtsfolge", "Fundstelle", "Vorbehalt / Hinweis")}
    return ergebnis


def _quellenart(texte: list[str]) -> str:
    t = " ".join(texte)
    arten = []
    if "BSG" in t or "Urteil" in t:
        arten.append("Rechtsprechung")
    if "KSK" in t or "Checkliste" in t or "Auslegung" in t:
        arten.append("Auslegung der KSK, kein Gesetz")
    if "KSVG §" in t:
        arten.append("Gesetz")
    return "; ".join(arten) or "–"


def _testfall_ergebnisse() -> dict[str, str]:
    if not ERGEBNIS.exists():
        return {}
    ergebnis = {}
    for zeile in ERGEBNIS.read_text(encoding="utf-8").splitlines():
        teile = [t.strip() for t in zeile.split("|")]
        if len(teile) > 5 and re.fullmatch(r"S-\d\d", teile[1]):
            ergebnis[teile[1]] = f"{teile[4]} ({teile[5].strip('*')})"
    return ergebnis


def _kopf(ws, spalten: list[tuple[str, int]]) -> None:
    ws.append([s for s, _ in spalten])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F3A5F")
        c.alignment = Alignment(wrap_text=True, vertical="top")
    for i, (_, breite) in enumerate(spalten, 1):
        ws.column_dimensions[get_column_letter(i)].width = breite


def _fertig(ws, auswahl: dict[str, str]) -> None:
    for zeile in ws.iter_rows(min_row=2):
        for c in zeile:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    kopf = [c.value for c in ws[1]]
    for name, liste in auswahl.items():
        spalte = get_column_letter(kopf.index(name) + 1)
        dv = DataValidation(type="list", formula1=liste, allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{spalte}2:{spalte}{max(ws.max_row, 2)}")
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions


def baue() -> openpyxl.Workbook:
    import json

    from app import taetigkeiten as T

    regeln = _regeln()
    faelle = json.loads(TESTFALL.read_text(encoding="utf-8"))["faelle"] if TESTFALL.exists() else []
    beispiele: dict[str, list[str]] = {}
    for f in faelle[1:]:
        text = f["gruppe"].split(": ", 1)[-1]
        beispiele.setdefault(T.erkenne(text) or "", []).append(f"{f['id']} {text}")

    wb = openpyxl.Workbook()
    anleitung = wb.active
    anleitung.title = "Anleitung"

    # --- Tätigkeiten -------------------------------------------------------------------------
    ws = wb.create_sheet("Tätigkeiten")
    _kopf(ws, [("T-ID", 7), ("Tätigkeit", 40), ("Vorschlag Gruppe", 16), ("Bedingung / Hinweis", 45),
               ("Regel-ID(s)", 11), ("Regel: Voraussetzung → Rechtsfolge", 70), ("Fundstelle(n)", 40),
               ("Quellenart", 22), ("Rechnet derselbe Künstler das mit ab (Vorschlag)", 22), ("Regel / Hinweis dazu", 45),
               ("Erkennungsbegriffe (feste Prüfung)", 35), ("Beispiel aus Testfall 20", 35),
               ("Entscheidung", 18), ("Richtige Gruppe", 16), ("Richtig beim selben Künstler", 22),
               ("Begründung / Änderung", 40), ("Geprüft von", 14), ("Datum", 11)])
    lesbar = {"kuenstlerisch": "künstlerisch", "nicht_kuenstlerisch": "nicht künstlerisch", "grenzfall": "Grenzfall"}
    for e in T.alle():
        regeltext = "\n".join(f"{rid}: {regeln[rid]['Voraussetzung']} → {regeln[rid]['Rechtsfolge']}"
                              for rid in e["regel_ids"] if rid in regeln)
        fund = [regeln[rid]["Fundstelle"] for rid in e["regel_ids"] if rid in regeln] + e["fundstellen"]
        art = _quellenart(fund + [regeln[rid]["Vorbehalt / Hinweis"] for rid in e["regel_ids"] if rid in regeln])
        ws.append([e["id"], e["name"], lesbar[e["gruppe"]], e["bedingung"], "; ".join(e["regel_ids"]), regeltext,
                   "\n".join(dict.fromkeys(fund)), art,
                   {"zaehlt": "zählt mit", "zaehlt_nicht": "zählt nicht", "unsicher": "Steuerberater entscheidet"}[e["selber_kuenstler"]],
                   "; ".join(filter(None, ["; ".join(e["selber_regel_ids"]), e["selber_hinweis"]])),
                   "; ".join(e["begriffe"]), "\n".join(beispiele.get(e["id"], [])),
                   OFFEN, "", "", "", "", ""])
    _fertig(ws, {"Entscheidung": ENTSCHEIDUNG, "Richtige Gruppe": '"künstlerisch,nicht künstlerisch,Grenzfall"',
                 "Richtig beim selben Künstler": '"zählt mit,zählt nicht,Steuerberater entscheidet"'})

    # --- Textbausteine -----------------------------------------------------------------------
    ws = wb.create_sheet("Textbausteine")
    _kopf(ws, [("Baustein-ID", 10), ("Erscheint bei", 28), ("Text", 90), ("Bemerkung", 45),
               ("Entscheidung", 18), ("Begründung / Änderung", 40), ("Geprüft von", 14), ("Datum", 11)])
    tb = openpyxl.load_workbook(KATALOG, read_only=True)["Textbausteine"]
    for r in list(tb.iter_rows(values_only=True))[1:]:
        if r[0] and int(str(r[0]).split("-")[1]) >= 17:  # neu seit 11.10.2026, noch ungeprüft
            ws.append([r[0], r[4] or "jedem Ergebnis, wenn die Angabe vorliegt", r[5], r[9] or "", OFFEN, "", "", ""])
    _fertig(ws, {"Entscheidung": ENTSCHEIDUNG})

    # --- Testfall 20 -------------------------------------------------------------------------
    ws = wb.create_sheet("Testfall 20")
    _kopf(ws, [("Fall", 7), ("Leistung (erfunden)", 45), ("Netto", 10), ("Soll der Testdatei", 26),
               ("Einordnung durch das System", 45), ("Ergebnis SaaS (mistral-large-latest)", 36),
               ("Soll richtig?", 16), ("Richtiges Soll", 26), ("Begründung / Änderung", 40), ("Geprüft von", 14), ("Datum", 11)])
    kuerzel = {"A": "Abgabepflichtig", "N": "Nicht abgabepflichtig", "G": "Grenzfall"}
    ist = _testfall_ergebnisse()
    for f in faelle:
        text = f["gruppe"].split(": ", 1)[-1]
        betrag = re.search(r"(\d+) € netto", f["frage"])
        tid = T.erkenne(text) if f["id"] != "S-00" else None
        ws.append([f["id"], text, betrag.group(1) if betrag and f["id"] != "S-00" else "",
                   " oder ".join(kuerzel.get(s, s) for s in f["soll"]) + (f"; Abgabe {f['zahl']['abgabe'].replace('.', ',')} €" if f.get("zahl") else ""),
                   (T.lesbar(tid) or "nicht im Regelwerk eingeordnet") if f["id"] != "S-00" else "je Position",
                   ist.get(f["id"], "–"), OFFEN, "", "", "", ""])
    _fertig(ws, {"Soll richtig?": '"offen,ja,nein,unklar"'})

    # --- Offene Fragen -----------------------------------------------------------------------
    ws = wb.create_sheet("Offene Fragen")
    _kopf(ws, [("Nr.", 6), ("Frage", 70), ("Was das System heute tut", 55), ("Bezug", 30),
               ("Antwort", 50), ("Geprüft von", 14), ("Datum", 11)])
    fragen = [
        ("Mehrere Positionen desselben Künstlers: Zählen technische Teile und Nebenkosten (z. B. Druckvorstufe, Material, Gerätemiete) mit, wenn derselbe Künstler sie abrechnet? Gilt das nur für Designer (R-117) oder für alle Künstler (R-42, R-175)?",
         "Fragt nach, ob die Positionen vom selben Auftragnehmer stammen, wenn es darauf ankommt. Beim selben Künstler gilt die Spalte „Rechnet derselbe Künstler das mit ab“ im Blatt „Tätigkeiten“ (zählt mit / zählt nicht / Steuerberater entscheidet).", "R-117; R-42; R-175; R-49"),
        ("Gerätemiete (Kamera, Licht, Ton): Wie ist sie zu behandeln, wenn ein reiner Verleiher (Einzelperson, kein Künstler) sie abrechnet?",
         "Grenzfall, beide Beträge werden gezeigt.", "R-42; R-175; Testfall S-10"),
        ("Webdesign: Reicht es, dass dieselbe Person die Seiten gestaltet UND programmiert, damit das gesamte Entgelt zählt? Wie ist reine Backend-Programmierung im selben Projekt zu behandeln?",
         "„Webdesign“ geht der reinen Programmierung vor; reine Programmierung allein zählt nicht.", "R-142; R-184"),
        ("Korrektorat oder Lektorat: Ist die Grenze „Einfluss auf Stil und Inhalt“ (R-194) richtig umgesetzt?",
         "Korrektorat/Rechtschreibprüfung: nicht künstlerisch; Lektorat: künstlerisch.", "R-194; R-234; Testfall S-04"),
        ("Moderation: Ist Workshop-, Coaching- und Team-Building-Moderation nicht abgabepflichtig (R-183), Moderation einer Veranstaltung oder Show dagegen schon (KSK-Info 06)?",
         "Workshop/Coaching: nicht künstlerisch; sonst Moderation: künstlerisch; widersprechen sich Modell und feste Prüfung: Grenzfall.", "R-183; KSK-Info 06; Testfall S-16"),
        ("Tätigkeiten, die KSK-Info 06 mit * kennzeichnet (PR-Fachmann, Übersetzer/Bearbeiter, Tänzer, Tanzpädagoge, Tonmeister, Stuntman, Aktionskünstler): Ist „Grenzfall“ richtig, oder sollen sie grundsätzlich als künstlerisch gelten?",
         "Grenzfall.", "KSK-Info 06, Fußnote *"),
        ("Leistungen ohne Fundstelle in unseren Quellen (z. B. Projektmanagement, Datenschutzberatung, Hosting): Gibt es eine Quelle, mit der sie als „nicht künstlerisch“ eingetragen werden können?",
         "Grenzfall („nicht im Regelwerk eingeordnet“), nie „Abgabepflichtig“.", "Testfall S-15, S-20"),
        ("Lehrtätigkeit, Schulung, Seminar: Ist „Grenzfall“ richtig (Kunst lehren zählt, reine Wissensvermittlung nicht)?",
         "Grenzfall; Musik-, Ballett-, Theaterunterricht: künstlerisch.", "R-137; R-187"),
        ("Druckkosten: Reicht „Druckkosten/Druckerei“ als Hinweis auf nachträgliche Vervielfältigung (R-49), oder muss das System nach Druckvorstufe/Erstdruck fragen?",
         "Druckkosten: nicht künstlerisch (Hinweis auf Druckvorstufe in der Bedingung).", "R-49; R-176"),
        ("Zahl der Veranstaltungen unbekannt: Ist „Grenzfall mit Empfehlung, vorsorglich einzuplanen“ (TB-17, TB-18) richtig, oder soll nach R-21 nur zurückgefragt werden?",
         "Grenzfall mit beiden Beträgen und Empfehlung.", "R-15; R-16; R-21; R-83; R-212"),
        ("Aufbewahrung des Prüfwegs je Rechnung: Reichen 5 Jahre nach § 28 KSVG, oder gelten längere steuerliche oder berufsrechtliche Fristen?",
         "Noch nicht gebaut (Konzept im Projektplan, Abschnitt 15).", "KSVG § 28; R-83"),
        ("Sprecher, Kameraleute u. a. (KSK-Info 06, Fußnote **): Darf das System von Selbständigkeit ausgehen, wenn der Nutzer „selbständige Einzelperson“ angibt?",
         "Ja, die Angabe des Nutzers gilt; Hinweis in der Bedingung.", "KSK-Info 06, Fußnote **"),
    ]
    for i, (frage, heute, bezug) in enumerate(fragen, 1):
        ws.append([f"F-{i:02d}", frage, heute, bezug, "", "", ""])
    _fertig(ws, {})

    # --- Anleitung ---------------------------------------------------------------------------
    for t in [
        "Prüfliste Tätigkeitsprüfung für den Steuerberater – ENTWURF, Stand 11.10.2026. Alles sind Vorschläge; nichts ist freigegeben.",
        "Hintergrund: Das System prüft jetzt, ob eine Leistung künstlerisch oder publizistisch ist (Blatt „Tätigkeitsabgrenzung“ im Regelkatalog). "
        "Nicht künstlerische Leistungen zählen nicht mit; unsichere oder unbekannte Leistungen ergeben immer „Grenzfall → Steuerberater entscheidet“, nie „Abgabepflichtig“.",
        f"Blatt „Tätigkeiten“ ({len(T.alle())} Zeilen): Ist die Gruppe richtig? Stimmt die Bedingung? Sind Regel und Fundstelle passend? Spalte „Entscheidung“ wählen, bei Änderung „Richtige Gruppe“ und Begründung eintragen, Name und Datum setzen.",
        "Blatt „Textbausteine“: Diese Sätze erscheinen wörtlich in den Antworten. Bitte auf fachliche Richtigkeit und Verständlichkeit prüfen.",
        "Blatt „Testfall 20“: erfundene Sammelrechnung mit 20 Positionen. Das Soll stammt aus der Testdatei, nicht von einem Berufsträger. Bitte prüfen, ob das Soll stimmt.",
        "Blatt „Offene Fragen“: Fragen, die das System nicht selbst entscheiden darf. Bitte kurz beantworten (gern mit Fundstelle).",
        "Spalte „Quellenart“: „Auslegung der KSK, kein Gesetz“ heißt: Verwaltungspraxis der KSK, nicht der Gesetzestext. Rangfolge: Gesetz > Rechtsprechung > KSK/DRV-Auslegung.",
        "Nach der Prüfung bitte die Datei zurückgeben; die Entscheidungen werden als neue Version in den Regelkatalog übernommen (nichts wird überschrieben).",
    ]:
        anleitung.append([t])
    anleitung.column_dimensions["A"].width = 150
    for zeile in anleitung.iter_rows():
        for c in zeile:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    return wb


if __name__ == "__main__":
    _schutz()
    baue().save(ZIEL)
    print("geschrieben:", ZIEL.relative_to(WURZEL))
