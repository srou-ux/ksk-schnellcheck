"""Schutz des Quellenbestands: `quellen/` darf nur ergänzt werden, nie geändert oder gelöscht.
Jedes Quelldokument (.pdf, .txt) unter quellen/ hat eine SHA-256-Prüfsumme in quellen/PRUEFSUMMEN.csv.
  python scripts/pruefsummen.py --pruefen    Fehler, wenn eine bekannte Datei geändert wurde oder fehlt.
                                             Neue Dateien ohne Eintrag werden gemeldet (Hinweis, kein Fehler).
  python scripts/pruefsummen.py --ergaenzen  trägt NUR neue Dateien ein; vorhandene Einträge bleiben unverändert.
Eine geänderte Quelle ist nie ein Update: neue Fassung = neue Datei mit neuem Namen (z. B. Datum im Namen) und
neue Zeile in quellen/index.csv; die alte Datei bleibt liegen."""
import csv, hashlib, pathlib, sys

W = pathlib.Path(__file__).resolve().parent.parent
Q = W / "quellen"
LISTE = Q / "PRUEFSUMMEN.csv"
GESCHUETZT = {".pdf", ".txt"}  # Quelldokumente. Nicht geschützt (laufend ergänzte Verzeichnisse): index.csv, archivnachweise.csv, DUPLIKATE.md, NICHT_GEFUNDEN.md, Listen

def summe(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def dateien():
    return {p.relative_to(Q).as_posix(): p for p in sorted(Q.rglob("*")) if p.is_file() and p.suffix.lower() in GESCHUETZT}

def lese():
    if not LISTE.exists():
        return {}
    with open(LISTE, encoding="utf-8", newline="") as f:
        return {r["datei"]: r["sha256"] for r in csv.DictReader(f)}

if __name__ == "__main__":
    alt, ist = lese(), dateien()
    if "--ergaenzen" in sys.argv:
        neu = {k: summe(p) for k, p in ist.items() if k not in alt}
        with open(LISTE, "a" if alt else "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            if not alt:
                w.writerow(["datei", "sha256"])
            for k in sorted(neu):
                w.writerow([k, neu[k]])
        print(f"{len(neu)} neue Datei(en) eingetragen; {len(alt)} vorhandene Einträge unverändert.")
        sys.exit(0)
    fehler = []
    for k, s in alt.items():
        if k not in ist:
            fehler.append(f"FEHLT (gelöscht oder umbenannt): {k}")
        elif summe(ist[k]) != s:
            fehler.append(f"GEÄNDERT (Quellen sind nur ergänzbar): {k}")
    neu = [k for k in ist if k not in alt]
    for n in neu:
        print(f"Hinweis: neue Datei ohne Prüfsumme: {n} (mit --ergaenzen eintragen)")
    if fehler:
        print("\n".join(fehler)); print("FEHLER im Quellenbestand."); sys.exit(1)
    print(f"Quellenbestand unverändert ({len(alt)} Dateien geprüft).")
    sys.exit(1 if neu else 0)
