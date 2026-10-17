"""Teil 1e, D.1 und E: Kern und unabhängige Gegenrechnung liefern exakt dasselbe.

- alle rechnenden Testfälle aus regelwerk/testfaelle_maschinenlesbar.json,
- 5.000 Zufallsfälle (fester Startwert): 2.500 im eigenen Prozess (ein Aufruf der Sandbox), 2.500 im selben Prozess,
- große Zahlen bis 99.999.999.999,99 und eine Liste mit 100.000 Positionen im eigenen Prozess unter dem Zeitlimit,
- zu große Listen werden vorab abgelehnt,
- mehr als zwei Nachkommastellen: beide Seiten 'keine Zahl'.
Eine Abweichung ist ein Befund (aufgaben/FUNDE_Chatbot.md), nie ein Grund, eine Seite blind anzugleichen."""
from __future__ import annotations

import json
import random
import time
import unittest
from decimal import Decimal
from pathlib import Path

from app import gegenrechnung as G
from app import sandbox
from tests.verifier import zufall
from tests.verifier.hilfe import d, im_prozess, pruefe_aufrufe

W = Path(__file__).resolve().parents[2]


def _aufrufe_fuer_testfall(fn: str, a: dict) -> list[tuple[str, list, dict]]:
    j = a.get("jahr")
    if fn == "eigenwerbung":
        return [("pruefe_eigenwerbung", [j, d(a["summe"])], {})]
    if fn == "typisch":
        return [("pruefe_typischer_verwerter", [j, d(a["betrag"])], {})]
    if fn in ("positionen", "bemessung"):
        pos = [{**p, "betrag": d(p["betrag"])} for p in a["positionen"]]
        return [("pruefe_positionen" if fn == "positionen" else "bemessung_positionen", [j, pos], {})]
    if fn == "veranstaltungen":
        return [("veranstaltungen", [j, a["anzahl"], d(a["summe"]), a.get("einnahmeabsicht", True),
                                     a.get("art", "generalklausel")], {})]
    if fn == "abgabe":
        return [("berechne_abgabe", [d(a["bg"]), j], {})]
    if fn == "vorauszahlung":
        return [("vorauszahlung_monatlich", [j, d(a["bg"])], {})]
    if fn == "meldefrist":
        return [("meldefrist", [a["jahr"]], {})]
    if fn == "aufbewahrung":
        return [("aufbewahrung_bis", [a["jahr"]], {})]
    if fn == "saeumnis":
        return [("saeumniszuschlag", [[d(x) for x in a["rueckstand"]], a["monate"], j, a.get("gesondert", False)], {})]
    if fn == "pauschale":
        return [("uebungsleiter_bg", [j, d(a["betrag"]), a["art"], True, d(a.get("bereits", 0))], {})]
    if fn == "netto":
        return [("netto", [d(a["brutto"]), d(a["ust"])], {}),
                ("pruefe_typischer_verwerter", [j, d(a["brutto"]) - d(a["ust"])], {})]
    if fn == "kommission":
        return [("kommission_bg", [d(a["preis"]), d(a["einbehalt"])], {}),
                ("pruefe_typischer_verwerter", [j, d(a["preis"]) - d(a["einbehalt"])], {})]
    if fn == "schaetzung":
        return [("schaetzung_ausland", [d(a["brutto"]), j], {})]
    if fn == "rechnung":
        pos = [{**p, "betrag": d(p["betrag"])} for p in a["positionen"]]
        return [("analysiere_rechnung", [j, pos, a.get("empfaenger"), a.get("agentur")], {})]
    if fn == "verpflegung_bg":
        return [("verpflegung", [j, d(a["stunden"]), False, d(a["erstattung"])], {})]
    raise KeyError(fn)


class Testfaelle(unittest.TestCase):
    def test_alle_rechnenden_testfaelle_stimmen_ueberein(self):
        spec = json.loads((W / "regelwerk" / "testfaelle_maschinenlesbar.json").read_text(encoding="utf-8"))
        aufrufe = [x for c in spec for x in _aufrufe_fuer_testfall(c["fn"], c["args"])]
        self.assertGreaterEqual(len(spec), 90)
        p = pruefe_aufrufe(aufrufe)
        self.assertEqual(p.status, "bestaetigt", p.grund)


class Zufallsfaelle(unittest.TestCase):
    def test_2500_zufallsfaelle_im_eigenen_prozess(self):
        faelle = zufall.faelle(2500, 20261015)
        beginn = time.perf_counter()
        p = pruefe_aufrufe(faelle)
        self.assertEqual(p.status, "bestaetigt", p.grund[:2000])
        self.assertLess(time.perf_counter() - beginn, 60)

    def test_2500_weitere_zufallsfaelle_gleiche_logik_im_selben_prozess(self):
        p = pruefe_aufrufe(zufall.faelle(2500, 7), ausfuehren=im_prozess)
        self.assertEqual(p.status, "bestaetigt", p.grund[:2000])

    def test_alle_rechenarten_kommen_vor(self):
        namen = {n for n, _, _ in zufall.faelle(2500, 20261015)}
        self.assertEqual(namen, set(zufall.NAMEN))


class GrosseZahlenUndMengen(unittest.TestCase):
    def test_hoechstbetraege(self):
        g = zufall.GROESSTER_BETRAG
        aufrufe = [("pruefe_positionen", [jahr, [{"betrag": g}, {"betrag": g, "empfaenger": "gmbh"}, {"betrag": g}]],
                    {"typischer_verwerter": tv}) for jahr in range(2019, 2028) for tv in (True, False)]
        aufrufe += [("vorauszahlung_monatlich", [2026, g], {}), ("saeumniszuschlag", [[g, g], 24, 2021, False], {}),
                    ("uebungsleiter_bg", [2026, g, "ehrenamt", True, Decimal(0)], {})]
        self.assertEqual(pruefe_aufrufe(aufrufe).status, "bestaetigt")

    def test_100000_positionen_im_eigenen_prozess_unter_dem_zeitlimit(self):
        rng = random.Random(1)
        pos = [{"betrag": Decimal(rng.randint(0, 9999999999999)) / 100,
                **({"empfaenger": "gmbh"} if i % 7 == 0 else {}), **({"art": "ust"} if i % 11 == 0 else {})}
               for i in range(sandbox.konfiguration()["max_positionen"])]
        beginn = time.perf_counter()
        p = pruefe_aufrufe([("pruefe_positionen", [2026, pos], {"typischer_verwerter": True})])
        dauer = time.perf_counter() - beginn
        self.assertEqual(p.status, "bestaetigt", p.grund)
        self.assertLess(dauer, sandbox.konfiguration()["zeitlimit_s"] * 3)

    def test_zu_grosse_liste_wird_vorab_abgelehnt(self):
        pos = [{"betrag": Decimal(1)}] * (sandbox.konfiguration()["max_positionen"] + 1)

        def nie(*_a, **_k):
            raise AssertionError("die Sandbox darf gar nicht erst starten")

        p = pruefe_aufrufe([("summe_positionen", [pos, 2026], {})], ausfuehren=nie)
        self.assertEqual(p.status, "fehlgeschlagen")
        self.assertFalse(p.gibt_aus)
        self.assertIn("zu groß", p.grund)


class Rundung(unittest.TestCase):
    def test_mehr_als_zwei_nachkommastellen_beide_ohne_zahl(self):
        # 1.234,57 € x 4,9 % = 60,49393 €: keine eigene Rundung (Grundregel 7), auf beiden Seiten keine Zahl.
        with G.mitschnitt() as m:
            G.KERN.pruefe_typischer_verwerter(2026, Decimal("1234.57"))
        self.assertIsNone(m.aufrufe[0].kern["abgabe"])
        self.assertEqual(G.pruefe(m).status, "bestaetigt")

    def test_vorauszahlung_mit_bruchteil_beide_rueckfrage(self):
        with G.mitschnitt() as m:
            G.KERN.vorauszahlung_monatlich(2026, Decimal("10000"))
        self.assertEqual(m.aufrufe[0].kern, {"betrag": None, "klasse": "RUECK"})
        self.assertEqual(G.pruefe(m).status, "bestaetigt")


if __name__ == "__main__":
    unittest.main()
