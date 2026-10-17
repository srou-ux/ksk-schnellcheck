"""Teil 1e, D.2: Fehler müssen auffallen (Mutationsproben).

Je Probe wird absichtlich EIN Fehler eingebaut (per patch, nur im Test) und ein passender Fall gerechnet: die
Gegenrechnung muss jeweils eine Abweichung melden ('abweichung', Antwort wird nicht ausgegeben).
- KERN_MUTATIONEN: Fehler im Kern; die Gegenrechnung läuft im eigenen Prozess und liest das unveränderte Register.
- GEGEN_MUTATIONEN: Fehler in der Gegenrechnung (im selben Prozess, damit der Patch wirkt); der Kern ist richtig.
Die Liste steht auch in aufgaben/SANDBOX_Nachweis.md."""
from __future__ import annotations

import copy
import unittest
from contextlib import contextmanager
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from unittest.mock import patch

from app.ergebnisklassen import PRUEFUNG_FEHLGESCHLAGEN
from kern import rechnen as K
from tests.verifier.hilfe import im_prozess, pruefe_aufrufe
from verifier import rechnung as V

D = Decimal


@contextmanager
def _register_geaendert(schluessel: str, neuer_wert: str):
    zeilen = copy.deepcopy(K.P["register"])
    for z in zeilen:
        if z["schluessel"] == schluessel:
            z["wert"] = neuer_wert
    with patch.dict(K.P, {"register": zeilen}):
        yield


@contextmanager
def _operator_geaendert(schluessel: str, neuer_operator: str):
    zeilen = copy.deepcopy(K.P["register"])
    for z in zeilen:
        if z["schluessel"] == schluessel:
            z["operator"] = neuer_operator
    with patch.dict(K.P, {"register": zeilen}):
        yield


def _berechne_abgabe_mit_eigener_rundung(bemessung, jahr):
    r = K.abgabesatz(jahr)
    return (D(str(bemessung)) * r / 100).quantize(D("0.01"), rounding=ROUND_HALF_UP), None


_ORIG_SUMME = K.summe_positionen
_ORIG_SAEUMNIS = K.saeumniszuschlag
_ORIG_ANALYSE = K.analysiere_rechnung

# (Name, Patch-Kontext, Aufrufe)
KERN_MUTATIONEN = [
    ("Vergleich '>' statt Registeroperator: 'übersteigt' wird zu 'mindestens'",
     lambda: _operator_geaendert("schwelle.operator", ">="),
     [("pruefe_eigenwerbung", [2026, D("1000")], {})]),
    ("falsche Übungsleiterpauschale 2026 (3.000 statt 3.300)",
     lambda: patch.dict(K.P, {"pauschale": {**K.P["pauschale"], "2026": {**K.P["pauschale"]["2026"], "uebungsleiter": "3000"}}}),
     [("uebungsleiter_bg", [2026, D("4000"), "uebungsleiter", True, D(0)], {})]),
    ("falscher Abgabesatz 2026 (5,0 statt 4,9)",
     lambda: patch.dict(K.P, {"abgabesatz": {**K.P["abgabesatz"], "2026": {**K.P["abgabesatz"]["2026"], "prozent": "5.0"}}}),
     [("pruefe_typischer_verwerter", [2026, D("2000")], {})]),
    ("falsche Schwelle 2025 (500 statt 700)",
     lambda: patch.dict(K.P, {"schwelle": {**K.P["schwelle"], "2025": {**K.P["schwelle"]["2025"], "euro": "500"}}}),
     [("pruefe_eigenwerbung", [2025, D("600")], {})]),
    ("vertauschte Summenregel: Umsatzsteuer zählt mit",
     lambda: patch.object(K, "_AUSSCHLUSSGRUENDE", {k: v for k, v in K._AUSSCHLUSSGRUENDE.items() if k != "ust"}),
     [("pruefe_positionen", [2026, [{"betrag": D("1000")}, {"betrag": D("190"), "art": "ust"}]], {"typischer_verwerter": True})]),
    ("GmbH zählt mit (Rechtsformliste leer)",
     lambda: patch.object(K, "werte", lambda s, j: set()),
     [("pruefe_positionen", [2026, [{"betrag": D("800")}, {"betrag": D("800"), "empfaenger": "gmbh"}]], {})]),
    ("ausgelassene Position (letzte Position fehlt in der Summe)",
     lambda: patch.object(K, "summe_positionen", lambda ps, j: _ORIG_SUMME(ps[:-1], j)),
     [("pruefe_positionen", [2026, [{"betrag": D("700")}, {"betrag": D("700")}]], {})]),
    ("eigene Rundung der Abgabe (statt 'keine Zahl')",
     lambda: patch.object(K, "berechne_abgabe", _berechne_abgabe_mit_eigener_rundung),
     [("pruefe_typischer_verwerter", [2026, D("1234.57")], {})]),
    ("Säumniszuschlag: ein Monat zu viel",
     lambda: patch.object(K, "saeumniszuschlag", lambda r, m, j, g=False: _ORIG_SAEUMNIS(r, m + 1, j, g)),
     [("saeumniszuschlag", [[D("1260")], 2, 2026, False], {})]),
    ("Säumniszuschlag: Abrundungsstufe 10 statt 50",
     lambda: _register_geaendert("saeumnis.stufe", "10"),
     [("saeumniszuschlag", [[D("1260")], 2, 2026, False], {})]),
    ("Drei-Veranstaltungen-Ausnahme: '<' statt '<=' (drei Veranstaltungen zählen schon)",
     lambda: _operator_geaendert("veranstaltungen.ausnahme_max", "<"),
     [("veranstaltungen", [2026, 3, D("5000"), True, "generalklausel"], {})]),
    ("Vorauszahlung: durch 11 statt 12 Monate",
     lambda: _register_geaendert("vorauszahlung.monate", "11"),
     [("vorauszahlung_monatlich", [2026, D("120000")], {})]),
    ("Verpflegung: genau 8 Stunden zählt schon ('>=' statt '>')",
     lambda: _operator_geaendert("verpflegung.stunden_grenze", ">="),
     [("verpflegung", [2026, D(8), False, D(14)], {})]),
    ("Rechnungsanalyse: Reisekosten ohne Belege zählen als sicher",
     lambda: patch.object(K, "analysiere_rechnung", lambda j, ps, e=None, a=None: _ORIG_ANALYSE(
         j, [{**p, "rolle": "vertretung_kuenstler"} if p.get("rolle") == "reise_kuenstler" else p for p in ps], e, a)),
     [("analysiere_rechnung", [2026, [{"nr": 1, "betrag": D("500"), "rolle": "reise_kuenstler", "belege": False},
                                      {"nr": 2, "betrag": D("900"), "rolle": "vertretung_kuenstler"}], True, True], {})]),
    ("Schätzung Ausland: 30 statt 25 Prozent",
     lambda: _register_geaendert("schaetzung.ausland_prozent", "30"),
     [("schaetzung_ausland", [D("10000"), 2026], {})]),
    ("Meldefrist: 30. statt 31. März",
     lambda: _register_geaendert("meldefrist.tag", "30"),
     [("meldefrist", [2026], {})]),
]


def _gilt_verdreht(self, schluessel, jahr, links, rechts):
    return not Register_gilt(self, schluessel, jahr, links, rechts)


from verifier.register import Register  # noqa: E402

Register_gilt = Register.gilt
_ORIG_V_SAEUMNIS = V.saeumniszuschlag
_ORIG_V_UEBUNG = V.uebungsleiter_bg
_ORIG_V_VORAUS = V.vorauszahlung_monatlich
_ORIG_V_ANALYSE = V.analysiere_rechnung

GEGEN_MUTATIONEN = [
    ("Gegenrechnung: Vergleich verdreht",
     lambda: patch.object(Register, "gilt", _gilt_verdreht),
     [("pruefe_eigenwerbung", [2026, D("1500")], {})]),
    ("Gegenrechnung: Umsatzsteuer zählt mit",
     lambda: patch.object(V, "NICHT_ZAEHLENDE_ARTEN", {k: v for k, v in V.NICHT_ZAEHLENDE_ARTEN.items() if k != "ust"}),
     [("pruefe_positionen", [2026, [{"betrag": D("1000")}, {"betrag": D("190"), "art": "ust"}]], {"typischer_verwerter": True})]),
    ("Gegenrechnung: Abgabe immer auf Cent gerundet",
     lambda: patch.object(V, "_auf_cent", lambda x: True),
     [("pruefe_typischer_verwerter", [2026, D("1234.57")], {})]),
    ("Gegenrechnung: bereits ausgeschöpfte Pauschale vergessen",
     lambda: patch.dict(V.AUFRUFE, {"uebungsleiter_bg": lambda reg, j, b, a="uebungsleiter", best=True, bereits=0:
                                    _ORIG_V_UEBUNG(reg, j, b, a, best, 0)}),
     [("uebungsleiter_bg", [2026, D("4000"), "uebungsleiter", True, D("1000")], {})]),
    ("Gegenrechnung: Säumniszuschlag aufgerundet statt abgerundet",
     lambda: patch.object(V.math, "floor", lambda x: -(-x.numerator // x.denominator)),
     [("saeumniszuschlag", [[D("1260")], 2, 2026, False], {})]),
    ("Gegenrechnung: Vorauszahlung ohne Untergrenze",
     lambda: patch.dict(V.AUFRUFE, {"vorauszahlung_monatlich": lambda reg, j, bg: {
         "betrag": Fraction(str(bg)) / 12 * reg.abgabesatz(j) / 100, "klasse": "ABG"}}),
     [("vorauszahlung_monatlich", [2026, D("6000")], {})]),
    ("Gegenrechnung: offene Positionen der Rechnung übersehen",
     lambda: patch.dict(V.AUFRUFE, {"analysiere_rechnung": lambda reg, j, ps, e=None, a=None: {
         **_ORIG_V_ANALYSE(reg, j, [p for p in ps if p.get("rolle") == "vertretung_kuenstler"], e, a)}}),
     [("analysiere_rechnung", [2026, [{"nr": 1, "betrag": D("500"), "rolle": None},
                                      {"nr": 2, "betrag": D("900"), "rolle": "vertretung_kuenstler"}], True, True], {})]),
    ("Gegenrechnung: Jahr der Schwelle verrutscht (Vorjahr)",
     lambda: patch.object(Register, "schwelle", lambda self, j, _o=Register.schwelle: _o(self, j - 1)),
     [("pruefe_eigenwerbung", [2026, D("900")], {})]),
]


class KernFehlerFallenAuf(unittest.TestCase):
    def test_ohne_mutation_ist_alles_gleich(self):
        for name, _patch, aufrufe in KERN_MUTATIONEN:
            with self.subTest(fall=name):
                self.assertEqual(pruefe_aufrufe(aufrufe).status, "bestaetigt")

    def test_jede_mutation_im_kern_wird_gefangen(self):
        for name, mutation, aufrufe in KERN_MUTATIONEN:
            with self.subTest(mutation=name), mutation():
                p = pruefe_aufrufe(aufrufe)
                self.assertEqual(p.status, "abweichung", f"nicht gefangen: {name}")
                self.assertFalse(p.gibt_aus)


class GegenrechnungsFehlerFallenAuf(unittest.TestCase):
    def test_ohne_mutation_ist_alles_gleich(self):
        for name, _patch, aufrufe in GEGEN_MUTATIONEN:
            with self.subTest(fall=name):
                self.assertEqual(pruefe_aufrufe(aufrufe, ausfuehren=im_prozess).status, "bestaetigt")

    def test_jede_mutation_der_gegenrechnung_wird_gefangen(self):
        for name, mutation, aufrufe in GEGEN_MUTATIONEN:
            with self.subTest(mutation=name), mutation():
                p = pruefe_aufrufe(aufrufe, ausfuehren=im_prozess)
                self.assertEqual(p.status, "abweichung", f"nicht gefangen: {name}")


class AntwortWirdNichtAusgegeben(unittest.TestCase):
    """Ende zu Ende über den Router: bei einer Abweichung keine Antwort, Eintrag ins Lückenprotokoll."""

    def test_falscher_abgabesatz_im_kern_ergibt_pruefung_fehlgeschlagen(self):
        import tempfile
        from pathlib import Path

        from app.llm.fake import FakeLLM
        from app.schema import Fakten
        from tests.app.hilfen import lauf_bestaetigt

        fakten = Fakten(anfrageart="kommission", jahr=2026, kommission_verkaufspreis=D("1000"),
                        kommission_einbehalt=D("500"))
        with tempfile.TemporaryDirectory() as ordner:
            pfad = Path(ordner) / "luecken.jsonl"
            with patch.dict("os.environ", {"LUECKENPROTOKOLL_PFAD": str(pfad)}), \
                    patch.dict(K.P, {"abgabesatz": {**K.P["abgabesatz"], "2026": {**K.P["abgabesatz"]["2026"], "prozent": "5.0"}}}):
                a = lauf_bestaetigt(FakeLLM(), "2026 Kommission 1.000 € Verkauf, 500 € Provision", fakten)
            eintraege = pfad.read_text(encoding="utf-8")
        self.assertEqual(a.ergebnisklasse, PRUEFUNG_FEHLGESCHLAGEN)
        self.assertIn("Gegenrechnung weicht ab", a.antwort)
        self.assertIn("Kern 25.0", a.antwort)
        self.assertIn("Gegenrechnung 24.5", a.antwort)
        self.assertNotIn("Abgabepflichtig", a.antwort)
        self.assertIn("Gegenrechnung abweichung (Fall ", eintraege)


if __name__ == "__main__":
    unittest.main()
