"""Testarchiv DIREKT im Chatbot ausführen: wie ein Mensch an der Weboberfläche.

Startet die echte App (uvicorn app.main:app), öffnet die Seite in einem Browser (Playwright,
Chromium) und spielt jeden Fall so, wie ein Nutzer es tut:
  Frage ins Eingabefeld tippen -> Senden -> bei einer Rückfrage den passenden Knopf anklicken
  (aus 'knoepfe' im Fall) oder, wenn keiner passt, den 'nachtrag' tippen -> bei der
  Faktenbestätigung 'Ja, das stimmt' klicken -> Ergebnis ablesen.
Bewertet wird gegen das Soll wie in pruefkatalog_lauf.py (dieselbe Funktion `bewerte`), dazu
der SICHTBARE Text der Antwort (verbotener/erwarteter Text) und die Zahl der Rückfragen.
Die Antwort-Daten (Ergebnisklasse, Kern-Zahlen) liest das Skript aus den Antworten der App an
den Browser mit, nicht aus dem Programm-Inneren.

Dialoge aus tests/archiv/dialoge.json werden ebenso Schritt für Schritt gespielt; ihr Verlauf
steht im Bericht (das Soll je Schritt ist Text und wird von Hand verglichen).

Aufruf (Windows und Linux):
  python aufgaben/audit/chatbot_direkt.py --bericht bericht.md --csv ergebnis.csv
  python aufgaben/audit/chatbot_direkt.py --katalog aufgaben/audit/testfall_alltag_4.json --nur alltag4:F1
  python aufgaben/audit/chatbot_direkt.py --modus api      (ohne Browser, dieselben HTTP-Aufrufe wie die Seite)
Ohne MISTRAL_API_KEY läuft die App im Demo-Modus. Voraussetzung: pip install -r app/requirements.txt
playwright; python -m playwright install chromium. Nur erfundene Daten."""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import os
import pathlib
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from types import SimpleNamespace

WURZEL = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pruefkatalog_lauf import bewerte, kuerzel_von  # noqa: E402

ARCHIV = WURZEL / "tests" / "archiv" / "alle_faelle.json"
DIALOGE = WURZEL / "tests" / "archiv" / "dialoge.json"
OFFEN = ("Rückfrage nötig", "Faktenbestätigung nötig")
MAX_SCHRITTE = int(os.environ.get("MAX_KNOEPFE", "25"))
WARTEZEIT_S = float(os.environ.get("CHATBOT_WARTEZEIT_S", "180"))


# ---------------------------------------------------------------------------------------------
# App starten
# ---------------------------------------------------------------------------------------------
def _freier_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


LUECKEN_DATEI = pathlib.Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "chatbot_direkt_luecken.jsonl"


def modellfehler_gruende() -> list[str]:
    """Häufigkeit der Gründe für fehlgeschlagene Modellaufrufe (aus dem Lückenprotokoll des Servers). Nur der Grund
    (Fehlerart, HTTP-Status), gekürzt; keine Fragen, keine Schlüssel (die stehen nie im Protokoll)."""
    import re
    from collections import Counter

    if not LUECKEN_DATEI.exists():
        return []
    zaehler: Counter = Counter()
    for zeile in LUECKEN_DATEI.read_text(encoding="utf-8").splitlines():
        try:
            grund = json.loads(zeile).get("grund", "")
        except json.JSONDecodeError:
            continue
        if "fehlgeschlagen" in grund.lower():
            grund = re.sub(r"https?://\S+", "<adresse>", grund)
            grund = re.sub(r"\b[A-Za-z0-9]{24,}\b", "<…>", grund)  # zur Sicherheit: lange Kennungen nie in den Bericht
            zaehler[grund[:200]] += 1
    return [f"- {n} × {g}" for g, n in zaehler.most_common(15)]


def starte_app() -> tuple[subprocess.Popen, str]:
    port = _freier_port()
    url = f"http://127.0.0.1:{port}"
    # 16.10.2026: Lückenprotokoll des Servers in eine eigene Datei, damit der Bericht die GRÜNDE der Modellfehler zeigt
    # (vorher stand nur „Antwort nicht verarbeitet“ im Bericht; Lauf korpus-j10-s1 brach ab Fall 107 ohne Grund ab).
    LUECKEN_DATEI.unlink(missing_ok=True)
    umgebung = {**os.environ, "LUECKENPROTOKOLL_PFAD": str(LUECKEN_DATEI)}
    server = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port)],
                              cwd=str(WURZEL), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, env=umgebung)
    for _ in range(100):
        try:
            with urllib.request.urlopen(f"{url}/gesundheit", timeout=1) as r:
                if json.loads(r.read()).get("status") == "ok":
                    return server, url
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.3)
    server.terminate()
    raise RuntimeError("Die App ist nicht gestartet (uvicorn app.main:app).")


def gesundheit(url: str) -> dict:
    with urllib.request.urlopen(f"{url}/gesundheit", timeout=5) as r:
        return json.loads(r.read())


# ---------------------------------------------------------------------------------------------
# Ein Nutzer im Browser
# ---------------------------------------------------------------------------------------------
class BrowserNutzer:
    """Bedient app/static/index.html wie ein Mensch. Merkt sich jede Antwort der App."""

    def __init__(self, url: str, playwright):
        self.url = url
        self.browser = playwright.chromium.launch()
        self.seite = None
        self.antworten: list[dict] = []

    def neuer_fall(self):
        if self.seite is not None:
            self.seite.close()
        self.seite = self.browser.new_page()
        self.antworten = []

        def mitlesen(antwort):
            if antwort.request.method == "POST" and antwort.url.rsplit("/", 1)[-1] in ("frage", "knopf", "bestaetigen"):
                try:
                    self.antworten.append(antwort.json())
                except Exception:  # noqa: BLE001 -- kaputte Antwort ist ein Befund, kein Abbruch
                    self.antworten.append({"ergebnisklasse": "FEHLER (keine JSON-Antwort)", "antwort": ""})

        self.seite.on("response", mitlesen)
        self.seite.goto(self.url)
        self.seite.wait_for_function("document.getElementById('modus').textContent !== 'lädt…'", timeout=15000)

    def _warte_auf_antwort(self, vorher: int) -> dict:
        ende = time.monotonic() + WARTEZEIT_S
        while len(self.antworten) <= vorher:
            if time.monotonic() > ende:
                raise TimeoutError("Keine Antwort der App innerhalb der Wartezeit.")
            self.seite.wait_for_timeout(100)
        # die Seite stellt die Antwort dar, sobald fetch fertig ist
        self.seite.wait_for_function("!document.getElementById('senden').disabled", timeout=15000)
        return self.antworten[-1]

    def tippe(self, text: str) -> dict:
        vorher = len(self.antworten)
        self.seite.fill("#eingabe", text)
        self.seite.click("#senden")
        return self._warte_auf_antwort(vorher)

    def klicke_option(self, beschriftung: str) -> dict:
        vorher = len(self.antworten)
        self.seite.locator(".nachricht.bot").last.locator(".vorschlag").get_by_text(beschriftung, exact=True).first.click()
        return self._warte_auf_antwort(vorher)

    def bestaetige(self) -> dict:
        vorher = len(self.antworten)
        self.seite.locator(".nachricht.bot").last.locator(".bestaetigung-knopf.ja").click()
        return self._warte_auf_antwort(vorher)

    def sichtbarer_text(self) -> str:
        return self.seite.locator(".nachricht.bot").last.inner_text()

    def schliessen(self):
        self.browser.close()


class ApiNutzer:
    """Ohne Browser: dieselben HTTP-Aufrufe, die index.html schickt (Verlauf, Sitzung, Knopf)."""

    def __init__(self, url: str, _playwright=None):
        self.url = url

    def _post(self, pfad: str, daten: dict) -> dict:
        req = urllib.request.Request(f"{self.url}/{pfad}", data=json.dumps(daten).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=WARTEZEIT_S) as r:
            return json.loads(r.read())

    def neuer_fall(self):
        self.verlauf, self.sitzung, self.letzte, self.letzte_sitzung = [], None, {}, None

    def _nach(self, a: dict) -> dict:
        self.letzte = a
        self.sitzung = a.get("sitzungskennung")
        if a.get("ergebnisklasse") not in OFFEN and not str(a.get("ergebnisklasse", "")).startswith("Hinweis"):
            self.letzte_sitzung = a.get("sitzungskennung") or self.letzte_sitzung
            self.verlauf, self.sitzung = [], None
        return a

    def tippe(self, text: str) -> dict:
        a = self._post("frage", {"frage": text, "verlauf": list(self.verlauf), "sitzungskennung": self.sitzung,
                                 "letzte_sitzung": None if self.sitzung else self.letzte_sitzung})
        self.verlauf.append(text)
        return self._nach(a)

    def klicke_option(self, beschriftung: str) -> dict:
        for e in self.letzte.get("rueckfrage_optionen") or []:
            if beschriftung in (e.get("optionen") or []):
                wert = (e.get("werte") or {}).get(beschriftung)
                self.verlauf.append(beschriftung)
                if e.get("feld") and self.sitzung and wert is not None:
                    return self._nach(self._post("knopf", {"sitzungskennung": self.sitzung, "feld": e["feld"],
                                                           "wert": wert, "position": e.get("position")}))
                return self.tippe(beschriftung)
        raise ValueError(f"Knopf {beschriftung!r} nicht angeboten")

    def bestaetige(self) -> dict:
        return self._nach(self._post("bestaetigen", {"sitzungskennung": self.letzte["sitzungskennung"],
                                                     "fakten_hash": self.letzte["fakten_hash"]}))

    def sichtbarer_text(self) -> str:
        return self.letzte.get("antwort", "")

    def schliessen(self):
        pass


# ---------------------------------------------------------------------------------------------
# Fälle spielen
# ---------------------------------------------------------------------------------------------
def _alter_knopf(knoepfe: dict, feld: str | None):
    """Schritt 2 (17.10.2026): die Rückfrage nach dem Zweck ersetzt die nach der Art des Auftraggebers. Gespeicherte
    Fälle nennen noch die alte Kategorie ('Eigenwerbung'); geklickt wird der Zweck-Knopf mit derselben Einordnung."""
    if feld == "auftragszweck" and "verwerterart" in knoepfe and "auftragszweck" not in knoepfe:
        from app.einordnung import zweck_knopf_fuer_alten_knopf

        return zweck_knopf_fuer_alten_knopf(knoepfe["verwerterart"])
    return knoepfe.get(feld)


def _passender_knopf(antwort: dict, knoepfe: dict) -> str | None:
    for e in antwort.get("rueckfrage_optionen") or []:
        beschriftung = _alter_knopf(knoepfe, e.get("feld"))
        if beschriftung and beschriftung in (e.get("optionen") or []):
            return beschriftung
    return None


def spiele_fall(nutzer, fall: dict) -> tuple[dict, list[str], int]:
    nutzer.neuer_fall()
    schritte = []
    a = nutzer.tippe(fall["frage"])
    schritte.append(f"Frage gesendet -> {a.get('ergebnisklasse')}")
    rueckfragen = 0
    nachtrag_gesendet = False
    for _ in range(MAX_SCHRITTE):
        klasse = a.get("ergebnisklasse")
        if klasse == "Faktenbestätigung nötig" and a.get("fakten_hash"):
            schritte.append("Bestätigt: " + "; ".join(a.get("fakten_zusammenfassung") or []))
            a = nutzer.bestaetige()
            schritte.append(f"'Ja, das stimmt' -> {a.get('ergebnisklasse')}")
            continue
        if klasse != "Rückfrage nötig":
            break
        knopf = _passender_knopf(a, fall.get("knoepfe") or {})
        if knopf:
            rueckfragen += 1
            a = nutzer.klicke_option(knopf)
            schritte.append(f"Knopf {knopf!r} -> {a.get('ergebnisklasse')}")
            continue
        if fall.get("nachtrag") and not nachtrag_gesendet:
            rueckfragen += 1
            nachtrag_gesendet = True
            schritte.append(f"Rückfragen: {a.get('rueckfragen')}")
            a = nutzer.tippe(fall["nachtrag"])
            schritte.append(f"Nachtrag getippt -> {a.get('ergebnisklasse')}")
            continue
        schritte.append(f"offen: {a.get('rueckfragen')}")
        break
    return a, schritte, rueckfragen


def _beschriftung_fuer(antwort: dict, feld: str, wert) -> str | None:
    if feld == "verwerterart":  # Schritt 2: gespeicherter Dialog mit der alten Kategorie -> Zweck-Knopf
        from app.einordnung import KATEGORIE_ZU_ZWECK

        neu = next((b for e in antwort.get("rueckfrage_optionen") or [] if e.get("feld") == "auftragszweck"
                    for b, w in (e.get("werte") or {}).items() if w == KATEGORIE_ZU_ZWECK.get(wert)), None)
        if neu:
            return neu
    return next((b for e in antwort.get("rueckfrage_optionen") or [] if e.get("feld") == feld
                 for b, w in (e.get("werte") or {}).items() if w == wert), None)


def _kurz(a: dict) -> str:
    if a.get("ergebnisklasse") == "Faktenbestätigung nötig" and a.get("fakten_zusammenfassung"):
        text = "Bestätigung: " + "; ".join(a["fakten_zusammenfassung"])
    else:
        text = (a.get("rueckfragen") or [a.get("antwort", "")])[0]
    return " ".join(text.replace("|", "/").split())[:900]


def spiele_dialog(nutzer, dialog: dict) -> list[str]:
    """Spielt einen Dialog wie ein Mensch. Ein Knopf-Schritt wird geklickt, sobald der Chatbot
    die passende Frage stellt -- auch wenn er sie später oder in anderer Reihenfolge stellt als
    beim ursprünglichen Livetest (ein Mensch beantwortet die Frage, die gerade gestellt wird)."""
    nutzer.neuer_fall()
    zeilen: list[str] = []
    a: dict = {}
    offen: list[tuple[int, str, object]] = []  # Knöpfe, die der Chatbot noch nicht angeboten hat

    def offene_knoepfe_klicken():
        nonlocal a
        geklickt = True
        while geklickt:
            geklickt = False
            for eintrag in list(offen):
                nr, feld, wert = eintrag
                beschriftung = _beschriftung_fuer(a, feld, wert)
                if beschriftung:
                    a = nutzer.klicke_option(beschriftung)
                    offen.remove(eintrag)
                    zeilen.append(f"| {nr} (später) | Knopf „{beschriftung}“ | {a.get('ergebnisklasse')} | {_kurz(a)} | "
                                  f"{dialog['soll_je_schritt'].get(str(nr), '')} |")
                    geklickt = True

    for nr, schritt in enumerate(dialog["schritte"], start=1):
        try:
            if "text" in schritt:
                a = nutzer.tippe(schritt["text"])
                zeilen.append(f"| {nr} | {' '.join(schritt['text'].split())[:80]} | {a.get('ergebnisklasse')} | {_kurz(a)} | "
                              f"{dialog['soll_je_schritt'].get(str(nr), '')} |")
                if dialog.get("bestaetigen") and a.get("ergebnisklasse") == "Faktenbestätigung nötig" and a.get("fakten_hash"):
                    # Dialoge, in denen der Nutzer die Angaben bestätigt (wie ein Mensch: 'Ja, das stimmt').
                    a = nutzer.bestaetige()
                    zeilen.append(f"| {nr} (Ja) | 'Ja, das stimmt' | {a.get('ergebnisklasse')} | {_kurz(a)} | |")
            elif schritt.get("bestaetigen"):
                # 15.10.2026 (Dialoge der Fehlerquellen-Serie): ausdrücklicher Schritt 'Ja, das stimmt'.
                if a.get("ergebnisklasse") == "Faktenbestätigung nötig" and a.get("fakten_hash"):
                    a = nutzer.bestaetige()
                    zeilen.append(f"| {nr} | 'Ja, das stimmt' | {a.get('ergebnisklasse')} | {_kurz(a)} | "
                                  f"{dialog['soll_je_schritt'].get(str(nr), '')} |")
                else:
                    zeilen.append(f"| {nr} | 'Ja, das stimmt' | (keine Bestätigung angeboten) | – | "
                                  f"{dialog['soll_je_schritt'].get(str(nr), '')} |")
            else:
                feld, wert = schritt["knopf"]
                beschriftung = _beschriftung_fuer(a, feld, wert)
                if beschriftung is None:
                    offen.append((nr, feld, wert))
                    zeilen.append(f"| {nr} | Knopf {feld}={wert!r} | (noch nicht gefragt, wird später geklickt) | – | |")
                    continue
                a = nutzer.klicke_option(beschriftung)
                zeilen.append(f"| {nr} | Knopf „{beschriftung}“ | {a.get('ergebnisklasse')} | {_kurz(a)} | "
                              f"{dialog['soll_je_schritt'].get(str(nr), '')} |")
            offene_knoepfe_klicken()
        except Exception as e:  # noqa: BLE001
            zeilen.append(f"| {nr} | – | **FEHLER** {type(e).__name__}: {str(e)[:120]} | – | |")
            break
    for nr, feld, wert in offen:
        zeilen.append(f"| {nr} | Knopf {feld}={wert!r} | **nie gefragt** | – | |")
    return zeilen


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--katalog", default=str(ARCHIV))
    ap.add_argument("--modus", choices=["browser", "api"], default="browser")
    ap.add_argument("--nur", help="nur diese Fall-IDs, kommagetrennt")
    ap.add_argument("--ohne-dialoge", action="store_true")
    ap.add_argument("--teil", default="1/1", help="Teil i von n, z. B. 2/6 (große Kataloge in mehreren Läufen)")
    ap.add_argument("--jeder", type=int, default=1, help="nur jeden n-ten Fall (Stichprobe aus einem großen Katalog)")
    ap.add_argument("--bericht")
    ap.add_argument("--csv")
    args = ap.parse_args()

    katalog_datei = pathlib.Path(args.katalog)
    katalog = json.loads(katalog_datei.read_text(encoding="utf-8"))
    tabelle = katalog["kuerzel"]
    faelle = katalog["faelle"]
    if args.nur:
        wahl = {x.strip() for x in args.nur.split(",")}
        faelle = [f for f in faelle if f["id"] in wahl]
    if args.jeder > 1:
        faelle = faelle[::args.jeder]
    i, n = (int(x) for x in args.teil.split("/"))
    if n > 1:
        groesse = -(-len(faelle) // n)
        faelle = faelle[(i - 1) * groesse:i * groesse]
    try:
        katalog_anzeige = katalog_datei.resolve().relative_to(WURZEL).as_posix()
    except ValueError:
        katalog_anzeige = katalog_datei.as_posix()

    server, url = starte_app()
    zaehler = {"RICHTIG": 0, "NACHGEFRAGT": 0, "FALSCH": 0, "FEHLER": 0}
    zeilen, details, csv_zeilen, dialog_zeilen = [], [], [], []
    start = time.time()
    try:
        info = gesundheit(url)
        modus = f"Chatbot direkt ({'Browser' if args.modus == 'browser' else 'HTTP wie die Seite'}) – {info.get('modell')}"
        playwright_kontext = None
        if args.modus == "browser":
            from playwright.sync_api import sync_playwright
            playwright_kontext = sync_playwright().start()
        nutzer = (BrowserNutzer if args.modus == "browser" else ApiNutzer)(url, playwright_kontext)
        for fall in faelle:
            t0 = time.time()
            try:
                a, schritte, rueckfragen = spiele_fall(nutzer, fall)
                sichtbar = nutzer.sichtbarer_text()
                ergebnis = SimpleNamespace(ergebnisklasse=a.get("ergebnisklasse", ""), antwort=sichtbar,
                                           kern_protokoll=a.get("kern_protokoll") or {})
                urteil, gruende = bewerte(fall, ergebnis, tabelle)
                grenze = fall.get("max_rueckfragen")
                if grenze is not None and rueckfragen > grenze:
                    gruende.append(f"{rueckfragen} Rückfrage(n), nötig laut Soll höchstens {grenze}")
                    if urteil == "RICHTIG":
                        urteil = "NACHGEFRAGT"
                ist = a.get("ergebnisklasse", "")
            except Exception as e:  # noqa: BLE001 -- jede Ausnahme ist ein Befund
                urteil, gruende, ist, schritte, rueckfragen, a = "FEHLER", [f"{type(e).__name__}: {str(e)[:200]}"], "Ausnahme", [], 0, {}
            dauer = time.time() - t0
            zaehler[urteil] += 1
            kp = a.get("kern_protokoll") or {}
            zeilen.append(f"| {fall['id']} | {fall['gruppe']} | {'/'.join(fall['soll'])} | {ist} | **{urteil}** | {rueckfragen} | {dauer:.1f} s |")
            if urteil != "RICHTIG":
                details += [f"### {fall['id']} – {fall['gruppe']} ({urteil})",
                            f"- Ist: {ist}; Bemessungsgrundlage {kp.get('bemessungsgrundlage', '–')}, Abgabe {kp.get('abgabe', '–')}",
                            f"- Verlauf: {' | '.join(schritte) or '–'}", f"- Gründe: {'; '.join(gruende) or '–'}", ""]
            csv_zeilen.append({"fall": fall["id"], "soll": "/".join(fall["soll"]), "ist": ist, "urteil": urteil,
                               "bemessungsgrundlage": kp.get("bemessungsgrundlage", ""), "abgabe": kp.get("abgabe", ""),
                               "rueckfragen": rueckfragen, "gruende": "; ".join(gruende)[:500], "dauer_s": f"{dauer:.1f}"})
            print(f"{fall['id']:28} {urteil:11} {ist}", flush=True)
        if not args.ohne_dialoge and DIALOGE.exists():
            for d in json.loads(DIALOGE.read_text(encoding="utf-8"))["dialoge"]:
                dialog_zeilen += [f"### {d['id']} ({d.get('herkunft', '')})", "",
                                  "| Schritt | Eingabe | Ergebnis | Rückfrage / Antwort (gekürzt) | Soll |", "|---|---|---|---|---|",
                                  *spiele_dialog(nutzer, d), ""]
        nutzer.schliessen()
        if playwright_kontext is not None:
            playwright_kontext.stop()
        # 17.10.2026: am Ende noch einmal fragen -- jetzt kennt der Server die Kennung, mit der Mistral geantwortet hat.
        try:
            modell_ende = gesundheit(url).get("modell")
            if modell_ende and modell_ende not in modus:
                modus += f"; Modell laut Antwort: {modell_ende}"
        except OSError:
            pass
    finally:
        server.terminate()

    stand = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=WURZEL).stdout.strip()
    kopf = [f"# Chatbot direkt getestet – {datetime.date.today()} ({modus})", "",
            f"Entwurf – vom Steuerberater zu prüfen. Nur erfundene Fälle. Soll-Werte: `{katalog_anzeige}`. Code-Stand `{stand}`.",
            "Jeder Fall wurde an der echten Weboberfläche gespielt: tippen, Knöpfe klicken, Fakten bestätigen.", "",
            f"- Fälle: {len(faelle)} (Teil {args.teil}{f', jeder {args.jeder}. Fall' if args.jeder > 1 else ''}), Dauer {time.time() - start:.0f} s",
            f"- RICHTIG: {zaehler['RICHTIG']}, NACHGEFRAGT: {zaehler['NACHGEFRAGT']}, **FALSCH: {zaehler['FALSCH']}**, FEHLER: {zaehler['FEHLER']}",
            "", "| Fall | Fallgruppe | Soll | Ist | Bewertung | Rückfragen | Dauer |", "|---|---|---|---|---|---|---|"]
    gruende_modell = modellfehler_gruende()
    bericht = "\n".join(kopf + zeilen + ["", "## Abweichungen", ""] + (details or ["Keine."])
                        + (["", "## Gründe der Modellfehler (Lückenprotokoll des Servers)", ""] + gruende_modell
                           if gruende_modell else [])
                        + (["", "## Dialoge (Soll je Schritt von Hand vergleichen)", ""] + dialog_zeilen if dialog_zeilen else [])) + "\n"
    print("\n".join(kopf[5:7]))
    if args.bericht:
        pathlib.Path(args.bericht).write_text(bericht, encoding="utf-8")
    if args.csv:
        with open(args.csv, "w", encoding="utf-8", newline="") as datei:
            s = csv.DictWriter(datei, fieldnames=["datum", "modus", "code_stand", "katalog", *(csv_zeilen[0].keys() if csv_zeilen else [])])
            s.writeheader()
            for z in csv_zeilen:
                s.writerow({"datum": datetime.date.today().isoformat(), "modus": modus, "code_stand": stand,
                            "katalog": katalog_anzeige, **z})
    return 1 if (zaehler["FALSCH"] or zaehler["FEHLER"]) else 0


if __name__ == "__main__":
    sys.exit(main())
