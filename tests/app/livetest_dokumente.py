"""Live-HTTP-Test mit eigenem Server und erfundenen Belegen; kein LLM und kein API-Schlüssel.
Aufruf: python tests/app/livetest_dokumente.py
"""
from decimal import Decimal
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from tests.app.test_dokumente import fall, pdf, xlsx


def main():
    url = "http://127.0.0.1:8733"
    # Gemeinsame App (17.10.2026), Demo-Modus: kein Sprachmodell, kein Schlüssel.
    server = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8733",
                               "--log-level", "error"], cwd=W,
                              env={**os.environ, "LLM_ANBIETER": "demo", "MISTRAL_API_KEY": "", "RAG_AUS": "1"})
    def post(path, data, raw=False):
        payload = data if raw else json.dumps(data).encode()
        r = urllib.request.Request(url+path, data=payload,
                                   headers={"Content-Type":"application/octet-stream" if raw else "application/json"})
        with urllib.request.urlopen(r, timeout=90) as response: return json.load(response)
    anzahl = 0
    try:
        for _ in range(100):
            try:
                urllib.request.urlopen(url+"/gesundheit", timeout=1);break
            except OSError:time.sleep(.2)
        else:raise RuntimeError("Server nicht erreichbar")
        for n in range(20):
            betrag=1500+n*100
            soll=str(Decimal("73.50")+n*Decimal("4.90"))
            for ext,beleg in [(".pdf",pdf([f"Logo {betrag},00 EUR"])),
                              (".xlsx",xlsx([["Logo",betrag]])),
                              (".csv",f"Bezeichnung;Betrag\nLogo;{betrag},00".encode())]:
                gelesen=post("/dokumente/lesen?endung="+ext,beleg,True)
                f=fall();f["positionen"][0].update(gelesen["positionen"][0])
                bereit=post("/dokumente/vorbereiten",f)
                assert bereit["bereit"],bereit
                result=post("/dokumente/auswerten",{"fall":f,"ticket":bereit["ticket"]})
                assert result["werte"].get("abgabe")==soll,result
                assert result["pruefprotokoll"]["status"]=="bestaetigt",result
                anzahl+=1
        print(f"LIVE-HTTP: {anzahl} von {anzahl} erfundenen Dokumentfällen richtig; Upload, Bestätigung, Regelkern und Gegenrechnung; kein LLM.")
    finally:
        server.terminate()
        try:server.wait(timeout=10)
        except subprocess.TimeoutExpired:server.kill()


if __name__ == "__main__": main()
