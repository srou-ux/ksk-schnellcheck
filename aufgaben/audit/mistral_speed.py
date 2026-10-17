"""Unabhängige Geschwindigkeits- und Qualitätsmessung der Mistral-Modelle (nutzt NICHTS aus app/ oder kern/).
Direkte Verbindung per HTTP, Schlüssel nur aus der Umgebung (MISTRAL_API_KEY), wird nie ausgegeben.
Je Modell mehrere Aufrufe mit denselben erfundenen Fragen: Zeit bis zum ersten Zeichen, Gesamtdauer, Tokens,
Ist die Antwort gültiges JSON mit den erwarteten Feldern? Aufruf: python aufgaben/audit/mistral_speed.py [ausgabe.md]"""
import os, sys, json, time, pathlib, statistics, datetime
import httpx

OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
ZEILEN = []


def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); ZEILEN.append(s)


def speichern():
    if OUT: OUT.write_text("\n".join(ZEILEN) + "\n", encoding="utf-8")


KEY = os.environ.get("MISTRAL_API_KEY")
if not KEY:
    p("KEIN SCHLÜSSEL: MISTRAL_API_KEY nicht gesetzt."); speichern(); sys.exit(0)
H = {"Authorization": f"Bearer {KEY}"}
BASIS = "https://api.mistral.ai/v1"

SYSTEM = ("Du wandelst eine Nutzerfrage zur Künstlersozialabgabe in ein JSON-Objekt um mit den Feldern: "
          "jahr (Zahl oder null), anfrageart (bewertung|vorauszahlung|saeumniszuschlag|auskunft|hinweis|null), "
          "positionen (Liste mit betrag, bezeichnung, auftragnehmer_typ: natuerliche_person|GmbH_UG_AG|null). "
          "Du rechnest nicht und rätst nicht: Was nicht im Text steht, ist null. Antworte nur mit dem JSON-Objekt.")
FRAGEN = [
    ("einfach", "Im Jahr 2025 haben wir einem freiberuflichen Grafiker 2.400 Euro gezahlt. Ist das abgabepflichtig?", {"jahr": 2025}),
    ("gemischt", "2025 haben wir gezahlt: Grafiker 2.400 Euro, Texterin 1.100 Euro, das GmbH-Studio Nord 5.000 Euro und ein Fotograf 800 Euro. Alle außer dem GmbH-Studio sind Freiberufler.", {"jahr": 2025}),
    ("ohne_jahr", "Ist ein Auftrag an einen Texter abgabepflichtig?", {"jahr": None}),
]
N = int(os.environ.get("SPEED_N", "2"))
TIMEOUT = float(os.environ.get("SPEED_TIMEOUT", "90"))

r = httpx.get(f"{BASIS}/models", headers=H, timeout=30); r.raise_for_status()
daten = r.json().get("data", [])
ids = sorted({m["id"] for m in daten})
p(f"# Mistral-Geschwindigkeitsmessung {datetime.date.today()}\n")
p("Entwurf. Nur erfundene Fragen. Unabhängig von der App (direkte API-Aufrufe).\n")
p("Alle Modelle der Liste: " + ", ".join(ids) + "\n")
if os.environ.get("SPEED_MODELLE"):
    modelle = [m.strip() for m in os.environ["SPEED_MODELLE"].split(",") if m.strip()]
else:
    ok = lambda i: any(k in i for k in ("small", "medium", "large", "ministral", "magistral", "nemo")) and not any(k in i for k in ("embed", "ocr", "moderation", "vision", "pixtral"))
    modelle = [i for i in ids if ok(i)][:10]
p("Getestete Modelle: " + ", ".join(modelle) + f" (je {N} Durchläufe x {len(FRAGEN)} Fragen, Zeitgrenze {TIMEOUT:.0f} s)\n")


def lauf(modell, frage):
    body = {"model": modell, "stream": True, "temperature": 0.0, "top_p": 1,
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": frage}]}
    t0 = time.time(); erst = None; text = []; tokens = None
    try:
        with httpx.stream("POST", f"{BASIS}/chat/completions", headers=H, json=body, timeout=TIMEOUT) as a:
            if a.status_code >= 400:
                return {"fehler": f"HTTP {a.status_code}: {a.read().decode()[:160]}", "dauer": time.time() - t0}
            for zeile in a.iter_lines():
                if not zeile.startswith("data:") or zeile.strip() == "data: [DONE]":
                    continue
                d = json.loads(zeile[5:])
                if d.get("usage"): tokens = d["usage"].get("completion_tokens")
                for c in d.get("choices", []):
                    inh = (c.get("delta") or {}).get("content")
                    if isinstance(inh, list):
                        inh = "".join(b.get("text", "") for b in inh if isinstance(b, dict) and b.get("type") == "text")
                    if inh:
                        if erst is None: erst = time.time() - t0
                        text.append(inh)
    except httpx.HTTPError as e:
        return {"fehler": f"{type(e).__name__}", "dauer": time.time() - t0}
    return {"dauer": time.time() - t0, "erst": erst, "tokens": tokens, "text": "".join(text)}


def json_ok(text, soll):
    t = text.strip()
    if t.startswith("```"): t = t.strip("`").removeprefix("json").strip()
    try:
        d = json.loads(t)
    except Exception:
        return False
    return isinstance(d, dict) and all(d.get(k) == v for k, v in soll.items())


tab = []
for m in modelle:
    dauern, ersten, ok_n, fehler, ges = [], [], 0, 0, 0
    for name, frage, soll in FRAGEN:
        for _ in range(N):
            ges += 1
            e = lauf(m, frage)
            dauern.append(e["dauer"])
            if "fehler" in e:
                fehler += 1; p(f"  {m} / {name}: FEHLER {e['fehler']} nach {e['dauer']:.1f} s")
                continue
            if e["erst"] is not None: ersten.append(e["erst"])
            if json_ok(e["text"], soll): ok_n += 1
    med = statistics.median(dauern)
    tab.append((m, med, max(dauern), statistics.median(ersten) if ersten else None, ok_n, fehler, ges))
    p(f"{m}: Mittelwert-Median {med:.1f} s, längster {max(dauern):.1f} s, JSON richtig {ok_n}/{ges}, Fehler {fehler}")
    speichern()

p("\n| Modell | Dauer (Median) | längster | erstes Zeichen (Median) | JSON richtig | Fehler |\n|---|---|---|---|---|---|")
for m, med, mx, ers, okn, f, g in sorted(tab, key=lambda x: x[1]):
    p(f"| {m} | {med:.1f} s | {mx:.1f} s | {'-' if ers is None else f'{ers:.1f} s'} | {okn}/{g} | {f} |")
speichern()
