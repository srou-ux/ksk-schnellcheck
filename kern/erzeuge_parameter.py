"""Erzeugt kern/parameter.json aus dem Regelkatalog (einzige Quelle der Zahlen).
Aufruf:  python kern/erzeuge_parameter.py   (prüft mit --pruefen, ob die JSON-Datei noch zum Katalog passt)"""
import json, re, sys, pathlib, openpyxl
W = pathlib.Path(__file__).resolve().parent.parent
XL = W / "regelwerk" / "Regelkatalog_24_KSVG_Entwurf.xlsx"
OUT = W / "kern" / "parameter.json"

def zahl(s):
    return str(s).replace(".", "").replace(",", ".").strip()

def bauen():
    wb = openpyxl.load_workbook(XL, data_only=True)
    satz = {}
    for r in wb["Abgabesätze"].iter_rows(min_row=2, values_only=True):
        if r[0]:
            satz[str(int(r[0]))] = {"prozent": str(r[1]), "fundstelle": r[2]}
    schwelle = {}
    for r in wb["Schwellen nach Jahr"].iter_rows(min_row=2, values_only=True):
        if not r[0]:
            continue
        m = re.match(r"^([\d.]+) €", str(r[2]))
        schwelle[str(int(r[0]))] = {"fassung": r[1], "euro": zahl(m.group(1)) if m else None,
                                    "text": r[2], "fundstelle": r[3]}
    pausch = {}
    for r in wb["Pauschalen nach Jahr"].iter_rows(min_row=2, values_only=True):
        if r[0]:
            ehr = str(r[2]).strip()
            pausch[str(int(r[0]))] = {"uebungsleiter": str(r[1]),
                                      "ehrenamt": ehr if ehr.isdigit() else None,
                                      "ehrenamt_ausgenommen": str(r[3]).strip().lower().startswith("ja"),
                                      "fundstelle": r[4]}
    reg = []
    for r in wb["Regelregister"].iter_rows(min_row=2, values_only=True):
        if r[0]:
            reg.append({"schluessel": r[0], "wert": str(r[1]), "einheit": r[2], "operator": r[3],
                        "von": int(r[4]) if r[4] else None, "bis": int(r[5]) if r[5] else None,
                        "regel": r[7], "fundstelle": r[8], "status": r[9]})
    return {"hinweis": "Erzeugt aus regelwerk/Regelkatalog_24_KSVG_Entwurf.xlsx – nicht von Hand ändern. Entwurf – vom Steuerberater zu prüfen.",
            "abgabesatz": satz, "schwelle": schwelle, "pauschale": pausch, "register": reg}

if __name__ == "__main__":
    neu = bauen()
    if "--pruefen" in sys.argv:
        alt = json.loads(OUT.read_text(encoding="utf-8"))
        if alt != neu:
            print("FEHLER: kern/parameter.json passt nicht mehr zum Regelkatalog. Neu erzeugen."); sys.exit(1)
        print("kern/parameter.json passt zum Regelkatalog.")
    else:
        OUT.write_text(json.dumps(neu, ensure_ascii=False, indent=1), encoding="utf-8"); print("geschrieben:", OUT)
