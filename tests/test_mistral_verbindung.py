"""Verbindungstest: nur die Modellliste, keine Rechnungsdaten.

Ein 401 bleibt ein Fehler. Die Meldung nennt die Form der Ablage, nie den Schlüsselwert.
"""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from extraktion.http import Schnittstellenfehler, get_json
from extraktion.schluessel import ablage, schluessel


class Verbindung(unittest.TestCase):
    def test_modelle_liste(self):
        info = ablage()
        self.assertEqual(info["pfad"].replace("\\", "/").endswith("config/secrets.env") or info["quelle"] == "umgebung", True)
        self.assertFalse(info["bom"], "config/secrets.env hat ein UTF-8-BOM")
        self.assertFalse(info["innen_whitespace"], "der Schlüsselwert enthält Whitespace")
        print(
            "Quelle",
            info["quelle"],
            "Laenge",
            info["laenge"],
            "Laenge Umgebung",
            info["laenge_umgebung"],
            "Laenge Datei",
            info["laenge_datei"],
        )
        key = schluessel()
        if key is None:
            self.fail(
                "Kein Schlüssel. Quelle "
                + info["quelle"]
                + ". Datei vorhanden: "
                + str(info["datei_vorhanden"])
                + ". Erwartet wird ein Key aus console.mistral.ai in config/secrets.env."
            )
        try:
            daten = get_json("/v1/models", key)
        except Schnittstellenfehler as fehler:
            self.fail(
                "HTTP "
                + str(fehler.status)
                + ". Quelle "
                + info["quelle"]
                + ", BOM "
                + str(info["bom"])
                + ", Whitespace "
                + str(info["innen_whitespace"])
                + ", Länge "
                + str(len(key))
                + ", Länge Umgebung "
                + str(info["laenge_umgebung"])
                + ", Länge Datei "
                + str(info["laenge_datei"])
                + ". Keys aus dem Chat-Produkt gelten nicht für die API. Kein Schlüsselwert in dieser Meldung."
            )
        modelle = daten.get("data") if isinstance(daten, dict) else None
        self.assertTrue(modelle, "die Modellliste ist leer")


if __name__ == "__main__":
    unittest.main(verbosity=2)
