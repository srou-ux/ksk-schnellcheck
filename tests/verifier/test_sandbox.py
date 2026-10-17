"""Teil 1e, D.3 und D.4: Verhalten der Sandbox und statische Prüfungen der Gegenrechnung.

Die Verbotsversuche laufen als kleines Prüfskript im eigenen Prozess (app/sandbox.py, wie die echte Gegenrechnung):
es schaltet denselben Wächter ein wie verifier/lauf.py und versucht dann etwas Verbotenes. Ehrlich: das zeigt, dass der
Wächter greift; es ist kein Beweis gegen jeden denkbaren Angriff (dafür Container ohne Netz, app/README.md)."""
from __future__ import annotations

import ast
import os
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from app import gegenrechnung as G
from app import sandbox

W = Path(__file__).resolve().parents[2]
VERIFIER = W / "verifier"


def _skript(rumpf: str, mit_waechter: bool = True) -> Path:
    ordner = Path(tempfile.mkdtemp(prefix="sandboxtest_"))
    kopf = f"""import json, sys
sys.path.insert(0, {str(W)!r})
from verifier import lauf
"""
    if mit_waechter:
        kopf += "sys.addaudithook(lauf._waechter)\n"
    pfad = ordner / "pruefskript.py"
    pfad.write_text(kopf + textwrap.dedent(rumpf), encoding="utf-8")
    return pfad


def _versuch(aktion: str) -> dict:
    """Führt `aktion` hinter dem Wächter aus; Antwort {'ok': True, 'gesperrt': bool, 'fehler': ...}."""
    rumpf = f"""
try:
{textwrap.indent(textwrap.dedent(aktion), '    ')}
    ergebnis = {{"ok": True, "gesperrt": False}}
except lauf.Gesperrt as f:
    ergebnis = {{"ok": True, "gesperrt": True, "fehler": str(f)}}
except Exception as f:
    ergebnis = {{"ok": True, "gesperrt": False, "fehler": type(f).__name__ + ": " + str(f)}}
sys.stdout.write(json.dumps(ergebnis))
"""
    return sandbox.fuehre_aus({}, lauf=_skript(rumpf))


class VerboteImKindprozess(unittest.TestCase):
    def test_netz_ist_gesperrt(self):
        for aktion in ("import socket\nsocket.create_connection(('example.org', 443), timeout=1)",
                       "import socket\nsocket.socket()",
                       "import urllib.request\nurllib.request.urlopen('https://example.org', timeout=1)"):
            with self.subTest(aktion=aktion.splitlines()[-1]):
                self.assertTrue(_versuch(aktion)["gesperrt"])

    def test_datei_schreiben_und_lesen_ist_gesperrt(self):
        ziel = Path(tempfile.gettempdir()) / "gegenrechnung_darf_das_nicht.txt"
        for aktion in (f"open({str(ziel)!r}, 'w').write('x')", f"open({str(W / 'README.md')!r}).read()",
                       f"import os\nos.remove({str(ziel)!r})"):
            with self.subTest(aktion=aktion):
                self.assertTrue(_versuch(aktion)["gesperrt"])
        self.assertFalse(ziel.exists())

    def test_neue_prozesse_sind_gesperrt(self):
        for aktion in ("import subprocess\nsubprocess.run(['echo', 'x'])", "import os\nos.system('echo x')"):
            with self.subTest(aktion=aktion):
                self.assertTrue(_versuch(aktion)["gesperrt"])

    def test_kern_und_app_lassen_sich_nicht_nachladen(self):
        for aktion in ("import kern.rechnen", "import app.router", "exec('1+1')"):
            with self.subTest(aktion=aktion):
                self.assertTrue(_versuch(aktion)["gesperrt"])

    def test_erlaubte_rechnung_laeuft_hinter_dem_waechter(self):
        self.assertFalse(_versuch("from fractions import Fraction\nFraction(1, 3) * 3")["gesperrt"])

    @unittest.skipUnless(sys.platform != "win32", "Speichergrenze gibt es nur mit dem Modul resource (Linux/macOS)")
    def test_speichergrenze_greift(self):
        rumpf = """
lauf._grenzen(200 * 1024 * 1024, None)
try:
    block = bytearray(800 * 1024 * 1024)
    ergebnis = {"ok": True, "begrenzt": False}
except MemoryError:
    ergebnis = {"ok": True, "begrenzt": True}
sys.stdout.write(json.dumps(ergebnis))
"""
        self.assertTrue(sandbox.fuehre_aus({}, lauf=_skript(rumpf, mit_waechter=False))["begrenzt"])

    def test_umgebung_ist_bereinigt(self):
        rumpf = """
import os
sys.stdout.write(json.dumps({"ok": True, "namen": sorted(os.environ)}))
"""
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "nur-ein-test", "HTTPS_PROXY": "http://x"}):
            namen = sandbox.fuehre_aus({}, lauf=_skript(rumpf, mit_waechter=False))["namen"]
        self.assertNotIn("MISTRAL_API_KEY", namen)
        self.assertNotIn("HTTPS_PROXY", namen)
        self.assertLessEqual(set(namen) - {"PYTHONIOENCODING", "SYSTEMROOT", "SystemRoot", "LC_CTYPE"}, set())


class FehlerHeisstNieBestaetigt(unittest.TestCase):
    def test_endlosschleife_wird_nach_dem_zeitlimit_beendet(self):
        beginn = time.perf_counter()
        antwort = sandbox.fuehre_aus({}, lauf=_skript("while True:\n    pass\n"), zeitlimit_s=1)
        self.assertFalse(antwort["ok"])
        self.assertIn("Zeitüberschreitung", antwort["fehler"])
        self.assertLess(time.perf_counter() - beginn, 10)

    def test_absturz_und_unsinn_ergeben_fehlgeschlagen(self):
        for rumpf in ("import os\nos._exit(3)\n", "raise SystemExit(2)\n", "sys.stdout.write('kein json')\n",
                      "sys.stdout.write(json.dumps({'ok': False, 'fehler': 'x'}))\n"):
            with self.subTest(rumpf=rumpf):
                self.assertFalse(sandbox.fuehre_aus({}, lauf=_skript(rumpf, mit_waechter=False))["ok"])

    def test_kaputte_anfrage_an_die_echte_gegenrechnung(self):
        self.assertFalse(sandbox.fuehre_aus({"aufrufe": [{"name": "pruefe_positionen", "args": "kaputt"}]})["ok"])

    def test_ausfall_der_sandbox_ist_pruefung_fehlgeschlagen(self):
        with G.mitschnitt() as m:
            G.KERN.abgabesatz(2026)
        p = G.pruefe(m, ausfuehren=lambda _a: {"ok": False, "fehler": "Zeitüberschreitung der Gegenrechnung"})
        self.assertEqual(p.status, "fehlgeschlagen")
        self.assertFalse(p.gibt_aus)
        self.assertIn("Gegenrechnung fehlgeschlagen", G.text_fehlgeschlagen(p))

    def test_unbekannte_rechnung_und_zahl_ohne_herkunft_sind_nicht_gegengerechnet(self):
        with G.mitschnitt() as m:
            G.KERN.abgabesatz(2026)
        m.aufrufe.append(G.Aufruf("neue_rechenart", [], {}, {"zahl": 1}))
        self.assertEqual(G.pruefe(m).status, "nicht_gegengerechnet")
        with G.mitschnitt() as m2:
            G.KERN.abgabesatz(2026)
        p = G.pruefe(m2, {"abgabesatz_prozent": G.Decimal("4.9"), "erfundene_zahl": G.Decimal("123")})
        self.assertEqual(p.status, "nicht_gegengerechnet")
        self.assertIn("erfundene_zahl", p.grund)

    def test_ohne_kernaufruf_keine_pruefzeile(self):
        with G.mitschnitt() as m:
            pass
        p = G.pruefe(m)
        self.assertEqual(p.status, "ohne_rechnung")
        self.assertIsNone(G.zeile(p))


class Statisch(unittest.TestCase):
    def _importe(self, pfad: Path) -> set[str]:
        namen = set()
        for knoten in ast.walk(ast.parse(pfad.read_text(encoding="utf-8"))):
            if isinstance(knoten, ast.Import):
                namen |= {a.name.split(".")[0] for a in knoten.names}
            elif isinstance(knoten, ast.ImportFrom) and knoten.module:
                namen.add(knoten.module.split(".")[0])
        return namen

    def test_verifier_importiert_den_kern_nie(self):
        for pfad in sorted(VERIFIER.glob("*.py")):
            with self.subTest(datei=pfad.name):
                importe = self._importe(pfad)
                self.assertNotIn("kern", importe)
                if pfad.name != "pruefe_register.py":  # nur der Startknopf darf app/sandbox.py benutzen
                    self.assertNotIn("app", importe)

    def test_keine_fachlichen_festwerte_in_der_gegenrechnung(self):
        """Wie der Wächter in tests/test_kern.py: Zahlen nur technisch (100, 0.01, 12, 31, 0, 1)."""
        erlaubt = {0, 1, 100, 12, 31, "0.01"}
        fund = []
        for pfad in sorted(VERIFIER.glob("*.py")):
            baum = ast.parse(pfad.read_text(encoding="utf-8"))
            doc = {id(n.body[0].value) for n in ast.walk(baum)
                   if isinstance(n, (ast.FunctionDef, ast.Module, ast.ClassDef)) and n.body
                   and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant)}
            for n in ast.walk(baum):
                if isinstance(n, ast.Constant) and id(n) not in doc:
                    v = n.value
                    if isinstance(v, (int, float)) and not isinstance(v, bool) and v not in erlaubt:
                        fund.append((pfad.name, n.lineno, v))
                    elif isinstance(v, str) and v.replace(".", "", 1).isdigit() and v not in erlaubt:
                        fund.append((pfad.name, n.lineno, v))
        self.assertEqual(fund, [], "Festwerte in verifier/ – ins Regelregister oder in eine Konfigurationsdatei")

    def test_waechter_sperrliste_deckt_die_angriffswege_ab(self):
        from verifier import lauf

        for ereignis in ("open", "socket.connect", "subprocess.Popen", "os.system", "import", "exec", "compile",
                         "ctypes.dlopen", "os.remove"):
            with self.subTest(ereignis=ereignis), self.assertRaises(lauf.Gesperrt):
                lauf._waechter(ereignis, ())


class Router(unittest.TestCase):
    def test_antwort_traegt_pruefzeile_und_pruefprotokoll(self):
        from decimal import Decimal

        from app.llm.fake import FakeLLM
        from app.schema import Fakten
        from tests.app.hilfen import lauf_bestaetigt

        fakten = Fakten(anfrageart="kommission", jahr=2026, kommission_verkaufspreis=Decimal("1000"),
                        kommission_einbehalt=Decimal("500"))
        a = lauf_bestaetigt(FakeLLM(), "2026 Kommission 1.000 € Verkauf, 500 € Provision", fakten)
        self.assertIn(G.ZEILE_BESTAETIGT, a.antwort)
        pp = a.pruefprotokoll
        self.assertEqual(pp["status"], "bestaetigt")
        self.assertEqual(pp["version"], __import__("verifier").VERSION)
        self.assertIn({"schluessel": "abgabesatz", "von": 2026, "bis": 2026, "wert": "4.9"}, pp["register"])
        self.assertIn("dauer_kern_ms", pp)
        self.assertIn("dauer_gegenrechnung_gesamt_ms", pp)


if __name__ == "__main__":
    unittest.main()
