"""RAG-Korpus „Beispiele und Gegenbeispiele“ für den Quellenabruf (15.10.2026). Ohne Sprachmodell: der Abruf
(app/rag/suche.py) ist Stichwortsuche über die lokalen Quellen, also von Natur aus unabhängig vom Modell.

Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fragen. Prüft, was im Chat zählt:
- R1 Jahr: 'Abgabesatz' mit Jahr liefert die Verordnung DIESES Jahres und keine eines anderen Jahres.
- R2 Aktenzeichen: ein Urteil der Quellenbasis wird über sein Aktenzeichen gefunden; ein erfundenes Aktenzeichen ergibt
  'Nicht abgedeckt' statt anderer Urteile (Gegenbeispiel).
- R3 Fachfremd: Fragen ohne Bezug zur Künstlersozialabgabe ergeben 'Nicht abgedeckt'; eine fachliche Zwillingsfrage
  liefert Quellen (Gegenbeispiel).
- R4 Jahr ohne Register: 'Nicht abgedeckt', keine Annäherung mit einem anderen Jahr.
- R5 Regeln: jede Regel des Katalogs mit Fundstelle wird über ihre Voraussetzung gefunden (unter den gelieferten Stücken).
Dazu die bestehende Messung python -m app.rag.guete (329 Testfälle, Bericht aufgaben/RAG_Bericht.md).

Aufruf (Windows): python aufgaben/audit/korpus/rag_korpus.py   (Ergebnis: Konsole, CSV, Zeile in TESTPROTOKOLL.md)
"""
from __future__ import annotations

import csv
import datetime
import json
import pathlib
import re
import subprocess
import sys

WURZEL = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WURZEL))

from app.rag.suche import suche  # noqa: E402

PROTOKOLL = WURZEL / "aufgaben" / "audit" / "TESTPROTOKOLL.md"
ERGEBNISSE = WURZEL / "tests" / "archiv" / "ergebnisse"
METADATEN = WURZEL / "app" / "rag" / "quellen_metadaten.csv"
REGELKATALOG = WURZEL / "regelwerk" / "Regelkatalog_24_KSVG_Entwurf.xlsx"

FACHFREMD = [
    ("Wie hoch ist die Hundesteuer in Köln?", "Wie hoch ist die Künstlersozialabgabe für eine Werbeagentur?"),
    ("Muss ich für mein Elektroauto Kfz-Steuer zahlen?", "Muss ich für Honorare an freie Grafiker Künstlersozialabgabe zahlen?"),
    ("Welche Kündigungsfrist gilt für meinen Mietvertrag?", "Welche Frist gilt für die Meldung der Entgelte an die Künstlersozialkasse?"),
    ("Gibt es ein Urteil zu NFT-Kunstwerken auf der Blockchain?", "Gibt es ein Urteil zur Abgabepflicht von Werbeagenturen?"),
    ("Wie beantrage ich Kurzarbeitergeld für meine Bäckerei?", "Wie melde ich die Entgelte an selbständige Künstler bei der Künstlersozialkasse?"),
    ("Darf mein Nachbar seine Hecke drei Meter hoch wachsen lassen?", "Darf eine Agentur die Künstlersozialabgabe an den Kunden weiterberechnen?"),
    ("Gibt es BSG-Rechtsprechung zu KI-generierten Bildern?", "Gibt es BSG-Rechtsprechung zur Eigenwerbung mit Künstlern?"),
    ("Ist Pferdewetten in Bayern umsatzsteuerpflichtig?", "Gehört die Umsatzsteuer zur Bemessungsgrundlage der Künstlersozialabgabe?"),
    ("Wie hoch ist der Grundfreibetrag bei der Einkommensteuer?", "Wie hoch ist die Übungsleiterpauschale bei der Künstlersozialabgabe?"),
    ("Wann verjährt eine Forderung aus einem Kaufvertrag?", "Wann verjährt die Künstlersozialabgabe?"),
    ("Welche Strafe droht bei Schwarzarbeit auf dem Bau?", "Welcher Säumniszuschlag droht bei verspäteter Zahlung der Künstlersozialabgabe?"),
    ("Brauche ich eine Baugenehmigung für einen Carport?", "Brauche ich eine Abgabenummer der Künstlersozialkasse als Verlag?"),
    ("Wie hoch ist das Elterngeld für Selbständige?", "Wie hoch ist die Vorauszahlung zur Künstlersozialabgabe?"),
    ("Gibt es ein Urteil zur Maklerprovision beim Hauskauf?", "Gibt es ein Urteil zur Abgabepflicht bei Zahlungen an eine GmbH?"),
    ("Was kostet ein Reisepass in Deutschland?", "Was zählt bei einem Künstler zum Entgelt, wenn Reisekosten erstattet werden?"),
    ("Welche Impfungen brauche ich für Thailand?", "Welche Unternehmen sind typische Verwerter nach dem Künstlersozialversicherungsgesetz?"),
    ("Wie lange dauert die Probezeit im Arbeitsvertrag?", "Wie lange muss ich Aufzeichnungen zur Künstlersozialabgabe aufbewahren?"),
    ("Gilt die Gurtpflicht auch im Reisebus?", "Gilt die Künstlersozialabgabe auch für Zahlungen an ausländische Künstler?"),
    ("Wie hoch ist die Grunderwerbsteuer in Hessen?", "Wie hoch ist die Geringfügigkeitsgrenze für Eigenwerbung?"),
    ("Darf ich im Garten ein Feuer machen?", "Darf ein Musikverein die Künstlersozialabgabe vermeiden, wenn er wenige Konzerte gibt?"),
]


def _aktenzeichen(datei: str) -> str | None:
    """'BSG_2022-06-01_B3KS3-21R.pdf' -> 'B 3 KS 3/21 R'; 'LSG-…_L9KR142-03.txt' -> 'L 9 KR 142/03'."""
    m = re.search(r"_([BL])(\d+)([A-Z]+)(\d+)-(\d+)(R?)\.", datei)
    if not m:
        return None
    return f"{m.group(1)} {m.group(2)} {m.group(3)} {m.group(4)}/{m.group(5)}" + (" R" if m.group(6) else "")


def _norm(t: str) -> str:
    return re.sub(r"\s+", "", t).upper()


def _enthaelt_az(erg, az: str) -> bool:
    return any(_norm(az) in _norm(f"{t.fundstelle} {t.datei}") or _norm(az).replace("/", "-") in _norm(t.datei)
               for t in erg.stuecke)


def faelle() -> list[dict]:
    erg: list[dict] = []
    # R1 Jahr
    for jahr in range(2019, 2028):
        erg.append({"id": f"R1-{jahr}", "gruppe": "R1 Jahr", "frage": "Wie hoch ist der Abgabesatz der Künstlersozialabgabe?",
                    "jahr": jahr, "pruefung": "jahr_verordnung", "soll": jahr})
    # R2 Aktenzeichen und erfundenes Aktenzeichen
    with open(METADATEN, encoding="utf-8") as f:
        urteile = [z["datei"] for z in csv.DictReader(f) if z["art"] == "Urteil"]
    for i, datei in enumerate(urteile):
        az = _aktenzeichen(datei)
        if not az:
            continue
        erg.append({"id": f"R2-{i + 1:02d}a", "gruppe": "R2 Aktenzeichen", "frage": f"Was hat das Gericht im Verfahren {az} entschieden?",
                    "jahr": None, "pruefung": "az_gefunden", "soll": az})
        teile = re.match(r"([BL]) (\d+) ([A-Z]+) (\d+)/(\d+)( R)?", az)
        falsch = f"{teile.group(1)} {teile.group(2)} {teile.group(3)} {int(teile.group(4)) + 40}/{teile.group(5)}{teile.group(6) or ''}"
        erg.append({"id": f"R2-{i + 1:02d}b", "gruppe": "R2 Aktenzeichen (erfunden)",
                    "frage": f"Was hat das Gericht im Verfahren {falsch} entschieden?", "jahr": None,
                    "pruefung": "leer", "soll": "Nicht abgedeckt"})
    # R3 fachfremd / fachlich
    for i, (fremd, fach) in enumerate(FACHFREMD, start=1):
        erg.append({"id": f"R3-{i:02d}a", "gruppe": "R3 Fachfremd", "frage": fremd, "jahr": None, "pruefung": "leer",
                    "soll": "Nicht abgedeckt"})
        erg.append({"id": f"R3-{i:02d}b", "gruppe": "R3 Fachlich (Zwilling)", "frage": fach, "jahr": None,
                    "pruefung": "nicht_leer", "soll": "Quellen"})
    # R4 Jahr ohne Register
    for jahr in (2010, 2014, 2031, 2040):
        erg.append({"id": f"R4-{jahr}", "gruppe": "R4 Jahr ohne Register", "frage": "Wie hoch ist der Abgabesatz der Künstlersozialabgabe?",
                    "jahr": jahr, "pruefung": "leer", "soll": "Nicht abgedeckt"})
    # R5 Regeln über ihre Voraussetzung
    import openpyxl

    wb = openpyxl.load_workbook(REGELKATALOG, read_only=True, data_only=True)
    zeilen = list(wb["Regeln"].iter_rows(values_only=True))
    kopf = {k: i for i, k in enumerate(zeilen[0])}
    for z in zeilen[1:]:
        rid, voraussetzung, fundstelle = z[0], z[kopf["Voraussetzung"]], z[kopf["Fundstelle"]]
        if not rid or not voraussetzung or not fundstelle:
            continue
        erg.append({"id": f"R5-{rid}", "gruppe": "R5 Regel", "frage": str(voraussetzung)[:300], "jahr": None,
                    "pruefung": "regel_geliefert", "soll": rid})
    return erg


# 16.10.2026: Regel R-89 nennt den Bereich 'KSAbg2019V–2027V' (gilt für jedes Jahr; seit der Korrektur der Fassung
# 'Jahresabhängig' wird sie geliefert). Ein Bereich ist keine Verordnung eines anderen Jahres und zählt nicht.
_VO_JAHR = re.compile(r"KSAbg(\d{4})V(?!\s*[–-]\s*\d{4}V)(?<![–-]\d{4}V)|Verordnung_(\d{4})")


def bewerte(fall: dict, erg) -> tuple[bool, str]:
    p = fall["pruefung"]
    geliefert = [t.fundstelle for t in erg.stuecke][:5]
    if p == "leer":
        return (not erg.stuecke), ("leer" if not erg.stuecke else f"geliefert: {' · '.join(geliefert[:3])}")
    if p == "nicht_leer":
        return bool(erg.stuecke), (f"geliefert: {' · '.join(geliefert[:3])}" if erg.stuecke else f"leer: {erg.grund}")
    if p == "az_gefunden":
        return _enthaelt_az(erg, fall["soll"]), f"geliefert: {' · '.join(geliefert[:3])}"
    if p == "regel_geliefert":
        ok = any(fall["soll"] in t.regel_ids for t in erg.stuecke)
        return ok, f"geliefert: {' · '.join(geliefert[:3])}"
    if p == "jahr_verordnung":
        jahre = set()
        for t in erg.stuecke:
            for m in _VO_JAHR.finditer(f"{t.datei} {t.fundstelle}"):
                jahre.add(int(m.group(1) or m.group(2)))
        richtig = fall["soll"] in jahre
        fremd = jahre - {fall["soll"]}
        return (richtig and not fremd), f"Verordnungsjahre geliefert: {sorted(jahre) or '–'}"
    raise KeyError(p)


def main() -> int:
    alle = faelle()
    zeilen, je_gruppe = [], {}
    for fall in alle:
        erg = suche(fall["frage"], fall["jahr"])
        ok, grund = bewerte(fall, erg)
        g = je_gruppe.setdefault(fall["gruppe"], [0, 0])
        g[0 if ok else 1] += 1
        zeilen.append({**{k: fall[k] for k in ("id", "gruppe", "frage", "jahr", "soll")}, "urteil": "RICHTIG" if ok else "FALSCH",
                       "grund": grund[:300]})
    richtig = sum(1 for z in zeilen if z["urteil"] == "RICHTIG")
    kurz = f"RAG-Korpus: {richtig}/{len(zeilen)} richtig – " + "; ".join(f"{g}: {a}/{a + b}" for g, (a, b) in je_gruppe.items())
    print(kurz)
    for z in zeilen:
        if z["urteil"] != "RICHTIG":
            print(f"  {z['id']}: {z['frage'][:80]} -> {z['grund'][:160]}")
    if "--ohne-protokoll" in sys.argv:
        return 0
    stand = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=WURZEL).stdout.strip()
    heute = datetime.date.today().isoformat()
    name = f"{heute}_rag_korpus_{stand}"
    nr = 1
    while (ERGEBNISSE / f"{name}{'' if nr == 1 else f'_{nr}'}.csv").exists():
        nr += 1
    name = f"{name}{'' if nr == 1 else f'_{nr}'}"
    with open(ERGEBNISSE / f"{name}.csv", "w", encoding="utf-8", newline="") as datei:
        s = csv.DictWriter(datei, fieldnames=["datum", "code_stand", *zeilen[0].keys()])
        s.writeheader()
        for z in zeilen:
            s.writerow({"datum": heute, "code_stand": stand, **z})
    with open(PROTOKOLL, "a", encoding="utf-8") as p:
        p.write(f"| {heute} | {stand} | RAG-Korpus (ohne Modell) | {kurz} | `tests/archiv/ergebnisse/{name}.csv` |\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
