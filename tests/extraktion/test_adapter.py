import os
import pathlib
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from extraktion.belege import trenne
from extraktion.felder import an_kern, aus_modell, dezimal
from extraktion.konfidenz import bloecke_filtern, einigung
from extraktion.schluessel import ablage, schluessel
from extraktion.schnittstelle import extrahiere_dokument
from extraktion.verbatim import nur_woertlich, steht
from kern import rechnen as K


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

    def test_abweichende_zeilensteuer_loescht_nicht_den_namen(self):
        zeile = {
            "nr": "01", "betrag": "1800.00", "text": "Foto", "betragswiderspruch": False,
            "unsicher": False, "netto": "1800.00", "ust": "", "satz": "",
        }
        andere = dict(zeile)
        andere["ust"] = "342.00"
        a = _lesung(empfaenger_name="Steinbach Naturstein GmbH", positionen=[zeile], summen={"netto": "2470.00"})
        b = _lesung(empfaenger_name="Steinbach Naturstein GmbH", positionen=[andere], summen={"netto": "2470.00"})
        felder = einigung([a, a, b])
        self.assertEqual(felder["positionen"][0]["ust"], "")
        self.assertEqual(felder["positionen"][0]["netto"], "1800.00")
        dokument = an_kern(felder, 2026)
        self.assertEqual(dokument["empfaenger_name"], "Steinbach Naturstein GmbH")
        self.assertEqual(dokument["summen"]["netto"], "2470.00")
        self.assertNotIn("ust", dokument["positionen"][0])


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

    def test_abgeleitete_zeilen_ust_faellt_weg(self):
        text = "Pos 01 1.800,00 Euro. Nettosumme 2.470,00 Euro. USt 469,30 Euro. Rechnungsbetrag 2.939,30 Euro."
        felder = extrahiere_dokument("leer", "rule")
        felder["positionen"] = [{
            "nr": "01", "betrag": "1800.00", "text": "", "betragswiderspruch": False, "unsicher": False,
            "netto": "1800.00", "ust": "342.00", "satz": "19",
        }]
        felder["summen"]["netto"] = "2470.00"
        felder["summen"]["ust"] = "469.30"
        felder["summen"]["brutto"] = "2939.30"
        felder = nur_woertlich(felder, text)
        self.assertIn("positionen[0].ust", felder["abgeleitet"])
        self.assertEqual(felder["positionen"][0]["ust"], "")
        self.assertEqual(felder["summen"]["ust"], "469.30")
        dokument = an_kern(felder, 2026)
        self.assertNotIn("ust", dokument["positionen"][0])
        self.assertEqual(dokument["summen"]["ust"], "469.30")

    def test_rechtsform_ersetzt_den_namen_nicht(self):
        felder = extrahiere_dokument("Steinbach Naturstein GmbH", "rule")
        felder["empfaenger_name"] = "Steinbach Naturstein GmbH"
        felder["rechtsform_angaben"] = ["GmbH"]
        felder = nur_woertlich(felder, "Rechnung an Steinbach Naturstein GmbH")
        dokument = an_kern(felder, 2026)
        self.assertEqual(dokument["empfaenger_name"], "Steinbach Naturstein GmbH")
        self.assertEqual(dokument["rechtsform"], "gmbh")
        self.assertNotIn("empfaenger", dokument)

    def test_mehrere_faelle_werden_getrennt_und_ohne_soll(self):
        text = "Fall F1 Foto\nSoll-Bewertung\n121,03 Euro\nFall F2 Verlag\nSoll-Bewertung\n85,75 Euro"
        teile = trenne(text)
        self.assertEqual(len(teile), 2)
        self.assertNotIn("121,03", teile[0])
        self.assertIn("Verlag", teile[1])

    def test_tausenderzeichen_bleibt_woertlich(self):
        text = "Nettosumme 2\u00b7470,00 Euro. Pos 01 1\u202f800,00 Euro."
        self.assertTrue(steht("2470.00", text))
        self.assertTrue(steht("1800,00", text))
        self.assertFalse(steht("342.00", text))
        self.assertEqual(dezimal("1800,00"), "1800.00")
        self.assertEqual(dezimal("1.800,00"), "1800.00")

    def test_vier_belege_f1_rechnet_ohne_soll(self):
        text = "\n".join([
            "Fall F1 Werbefotografie Eigenwerbung",
            "Rechnungsempfänger: Steinbach Naturstein GmbH",
            "Pos 01 1\u202f800,00 Euro",
            "Pos 02 220,00 Euro",
            "Pos 03 450,00 Euro",
            "Nettosumme: 2\u00b7470,00 Euro · USt 469,30 Euro · Rechnungsbetrag: 2.939,30 Euro",
            "Soll-Bewertung",
            "Soll-Abgabe: 121,03 Euro",
            "Fall F2 Publizist",
            "Rechnungsempfänger: Rheinland Verlag GmbH & Co. KG",
            "Soll-Bewertung",
            "Fall F3 Agentur",
            "Rechnungsempfänger: VitaWelt Krankenversicherung a.G.",
            "Soll-Bewertung",
            "Fall F4 Hochzeit",
            "Rechnungsempfänger: Familie Brautpaar",
            "Soll-Bewertung",
        ])
        teile = trenne(text)
        self.assertEqual(len(teile), 4)
        self.assertNotIn("121,03", teile[0])
        self.assertIn("Eigenwerbung", teile[0])
        felder = extrahiere_dokument("leer", "rule")
        felder["empfaenger_name"] = "Steinbach Naturstein GmbH"
        felder["rechtsform_angaben"] = ["GmbH"]
        felder["jahr"] = "2026"
        felder["positionen"] = [{
            "nr": "01", "betrag": "1800.00", "text": "", "betragswiderspruch": False, "unsicher": False,
            "netto": "1800.00", "ust": "342.00", "satz": "19",
        }]
        felder["summen"]["positionssumme"] = "2470.00"
        felder["summen"]["netto"] = "2470.00"
        felder["summen"]["ust"] = "469.30"
        felder["summen"]["brutto"] = "2939.30"
        felder["summen"]["kopfsumme"] = "2939.30"
        felder = nur_woertlich(felder, teile[0])
        self.assertIn("positionen[0].ust", felder["abgeleitet"])
        dokument = an_kern(felder, 2026)
        self.assertEqual(dokument["empfaenger_name"], "Steinbach Naturstein GmbH")
        self.assertNotEqual(dokument.get("empfaenger"), "gmbh")
        self.assertIsNone(K.pruefe_dokument(dokument, 2026))
        entscheid = K.pruefe_eigenwerbung(2026, dokument["summen"]["netto"])
        self.assertEqual(entscheid.klasse, K.ABGABEPFLICHTIG)
        self.assertEqual(entscheid.abgabe, Decimal("121.03"))

    def test_kernmodul_importiert_die_extraktion_nicht(self):
        text = (__import__("pathlib").Path(__file__).resolve().parents[2] / "kern" / "rechnen.py").read_text(encoding="utf-8")
        self.assertNotIn("extraktion", text)
        self.assertNotIn("mistral", text.lower())


if __name__ == "__main__":
    unittest.main()
