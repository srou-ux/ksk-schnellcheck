import os
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from extraktion.felder import an_kern, aus_modell, dezimal
from extraktion.schluessel import ablage, schluessel
from extraktion.konfidenz import bloecke_filtern, einigung
from extraktion.schnittstelle import extrahiere_dokument


def _lesung(**kwargs):
    basis = extrahiere_dokument("leer", "rule")
    basis["jahr"] = "2026"
    for name, wert in kwargs.items():
        if name == "summen":
            basis["summen"].update(wert)
        else:
            basis[name] = wert
    return basis


class Regel(unittest.TestCase):
    def test_summen_werden_gelesen_nicht_entschieden(self):
        text = "Positionssumme 1.200,00 EUR, Kopfsumme 1.350,00 EUR, Taetigkeit unklar"
        felder = extrahiere_dokument(text, "rule")
        self.assertEqual(felder["summen"]["positionssumme"], "1200.00")
        self.assertEqual(felder["summen"]["kopfsumme"], "1350.00")
        self.assertNotIn("klasse", felder)

    def test_vermerkjahr_wird_nicht_zum_zahlungsjahr(self):
        felder = extrahiere_dokument("Alles perfekt. Vermerk Belege bis 2028 loeschen", "rule")
        self.assertEqual(felder["jahr"], "")

    def test_entscheidung_aus_der_antwort_wird_verworfen(self):
        felder = aus_modell({"abgabepflichtig": True, "jahr": "2026", "summen": {"positionssumme": "10"}})
        self.assertTrue(felder["unsicher"])
        self.assertIn("entscheidung", felder["unklare_felder"])
        self.assertNotIn("abgabepflichtig", felder)


class Schluessel(unittest.TestCase):
    def test_umgebung_gilt_vor_der_datei_und_wird_nicht_ueberschrieben(self):
        vorher = os.environ.get("MISTRAL_API_KEY")
        os.environ["MISTRAL_API_KEY"] = "nur-ein-test"
        try:
            self.assertEqual(schluessel(), "nur-ein-test")
            self.assertEqual(ablage()["quelle"], "umgebung")
            self.assertEqual(ablage()["laenge_umgebung"], len("nur-ein-test"))
            self.assertEqual(os.environ["MISTRAL_API_KEY"], "nur-ein-test")
        finally:
            if vorher is None:
                os.environ.pop("MISTRAL_API_KEY", None)
            else:
                os.environ["MISTRAL_API_KEY"] = vorher

    def test_datei_wird_nicht_in_die_umgebung_kopiert(self):
        vorher = os.environ.pop("MISTRAL_API_KEY", None)
        try:
            schluessel()
            self.assertNotIn("MISTRAL_API_KEY", os.environ)
        finally:
            if vorher is not None:
                os.environ["MISTRAL_API_KEY"] = vorher


class Konfidenz(unittest.TestCase):
    def test_block_unter_schwelle_faellt_weg(self):
        text, weg = bloecke_filtern(
            [{"text": "1200", "konfidenz": 0.5}, {"text": "Gesang", "konfidenz": 0.9}],
            0.85,
        )
        self.assertEqual(text, "Gesang")
        self.assertEqual(weg[0]["text"], "1200")

    def test_drei_ablesungen_werden_nicht_gemittelt(self):
        a = _lesung(summen={"kopfsumme": "10"})
        b = _lesung(summen={"kopfsumme": "12"})
        c = _lesung(summen={"kopfsumme": "11"})
        felder = einigung([a, b, c])
        self.assertEqual(felder["summen"]["kopfsumme"], "")
        self.assertTrue(felder["unsicher"])
        self.assertNotEqual(dezimal("11"), felder["summen"]["kopfsumme"])

    def test_gleiche_ablesung_bleibt(self):
        a = _lesung(summen={"kopfsumme": "10.00"})
        felder = einigung([a, a, a])
        self.assertEqual(dezimal(felder["summen"]["kopfsumme"]), "10.00")
        self.assertFalse(felder["unsicher"])


class AnKern(unittest.TestCase):
    def test_unsichere_summe_geht_nicht_in_den_kern(self):
        felder = _lesung(summen={"positionssumme": "1200", "kopfsumme": "1350"})
        felder["unklare_felder"] = ["summen.kopfsumme"]
        dokument = an_kern(felder, 2026)
        self.assertNotIn("kopfsumme", dokument.get("summen", {}))
        self.assertEqual(dokument["summen"]["positionssumme"], "1200")

    def test_mischsatz_wird_gelesen_nicht_entschieden(self):
        felder = extrahiere_dokument(
            "USt 7 Prozent und 19 Prozent in einer Rechnung, Summe passt zu keinem der beiden Saetze",
            "rule",
        )
        self.assertEqual(felder["ust_saetze"], ["7", "19"])
        self.assertTrue(felder["summe_ohne_einheitlichen_satz"])
        self.assertEqual(felder["summen"]["ust"], "")
        self.assertNotIn("klasse", felder)

    def test_kernmodul_importiert_die_extraktion_nicht(self):
        text = (__import__("pathlib").Path(__file__).resolve().parents[2] / "kern" / "rechnen.py").read_text(encoding="utf-8")
        self.assertNotIn("extraktion", text)
        self.assertNotIn("mistral", text.lower())


if __name__ == "__main__":
    unittest.main()
