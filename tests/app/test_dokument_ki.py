"""KI-Unterstützung für „Rechnungen prüfen“ (app/dokument_ki.py, 17.10.2026). Nachgebildetes Modell, kein Netz, erfundene
Rechnungen. Geprüft: Abgleich mit der Regel-Erkennung, kein erfundener Betrag, Umsatzsteuer nur als Hinweis, Ausfall der
KI, Schalter ohne KI / Demo-Modus, zu langer Text."""
from __future__ import annotations

import unittest

from app import dokument_ki
from app.llm.base import LLMFehlgeschlagen
from app.llm.fake import FakeLLM
from app.schema import Fakten

TEXT = ("Grafikbüro Muster (Einzelunternehmen)\nRechnung Nr. 2026-17\nPos. 1  Logo-Gestaltung   1 x   1.200,00 EUR\n"
        "Logo-Varianten 300,00 EUR\nZwischensumme 1.500,00 EUR\nUmsatzsteuer 19 % 285,00 EUR\nGesamt 1.785,00 EUR")
REGEL = [{"bezeichnung": "Logo-Varianten", "betrag": "300.00", "beleg": "Seite 1, Zeile 4: Logo-Varianten 300,00 EUR"}]


class _Modell:
    """Liefert vorgegebene Fakten (wie ein echtes Modell, aber ohne Netz); kein FakeLLM (der gilt als 'ohne KI')."""

    def __init__(self, fakten=None, fehler=False):
        self.fakten, self.fehler, self.texte = fakten, fehler, []

    def extrahiere_fakten(self, frage, verlauf=None, fallstand=None):
        self.texte.append(frage)
        if self.fehler:
            raise LLMFehlgeschlagen("Testdoppel: HTTP-Fehler", status=503)
        return self.fakten


def _fakten(*positionen, typ=None):
    return Fakten.model_validate({"auftragnehmer_typ": typ, "positionen": list(positionen)})


class Abgleich(unittest.TestCase):
    def test_ki_und_regeln_einig_und_nur_ki(self):
        m = _Modell(_fakten({"betrag": "1200", "bezeichnung": "Logo-Gestaltung"},
                            {"betrag": "300", "bezeichnung": "Logo-Varianten"}, typ="natuerliche_person"))
        r = dokument_ki.ordne(TEXT, REGEL, m, 20000)
        self.assertEqual(r["ki"], "verwendet")
        self.assertEqual([p["betrag"] for p in r["positionen"]], ["1200", "300"])
        self.assertEqual(r["pruefung"], ["nur_ki", "bestaetigt"])
        from app.dokument_pruefung import DokumentPosition

        for p in r["positionen"]:
            DokumentPosition.model_validate(p)  # nur Felder des Formulars (extra='forbid')
        self.assertIn("Zeile 3", r["positionen"][0]["beleg"], "Belegstelle aus dem Dokument")
        self.assertEqual(r["positionen"][0]["auftragnehmer_typ"], "natuerliche_person")
        self.assertTrue(m.texte[0].endswith(TEXT), "nur der gelesene Text geht an das Modell")

    def test_erfundener_betrag_wird_verworfen(self):
        r = dokument_ki.ordne(TEXT, REGEL, _Modell(_fakten({"betrag": "999", "bezeichnung": "Erfunden"},
                                                           {"betrag": "300", "bezeichnung": "Logo-Varianten"})), 20000)
        self.assertEqual([p["betrag"] for p in r["positionen"]], ["300"])
        self.assertTrue(any("999" in h and "verworfen" in h for h in r["hinweise"]))

    def test_umsatzsteuer_nur_als_hinweis(self):
        r = dokument_ki.ordne(TEXT, REGEL, _Modell(_fakten({"betrag": "300", "bezeichnung": "Logo-Varianten"},
                                                           {"betrag": "285", "rolle": "ust", "bezeichnung": "Umsatzsteuer"})),
                              20000)
        self.assertEqual([p["betrag"] for p in r["positionen"]], ["300"])
        self.assertTrue(any("285" in h for h in r["hinweise"]))

    def test_nur_von_den_regeln_gefunden_ist_ein_hinweis(self):
        r = dokument_ki.ordne(TEXT, REGEL, _Modell(_fakten({"betrag": "1200", "bezeichnung": "Logo-Gestaltung"})), 20000)
        self.assertEqual([p["betrag"] for p in r["positionen"]], ["1200"])
        self.assertTrue(any("300.00" in h and "fehlt" in h for h in r["hinweise"]))

    def test_andere_kosten_bleiben_positionen(self):
        """Live-Test 17.10.2026: 'Fahrtkosten laut Beleg 60,00 EUR' – ob das zählt, entscheidet das Regelwerk."""
        text = "Auftritt Firmenfeier 800,00 EUR\nFahrtkosten laut Beleg 60,00 EUR\nSumme 860,00 EUR"
        m = _Modell(_fakten({"betrag": "800", "bezeichnung": "Auftritt"},
                            {"betrag": "60", "rolle": "fahrtkosten_nachgewiesen", "bezeichnung": "Fahrtkosten"}))
        r = dokument_ki.ordne(text, [], m, 20000)
        self.assertEqual([p["betrag"] for p in r["positionen"]], ["800", "60"])

    def test_tabelle_mit_mehreren_zeilen(self):
        """Live-Test 17.10.2026: '… 1.200,00 EUR' am Zeilenende vor '2  Illustrationen' ging verloren
        (app/textnorm.py::waehrung_nach_hinten über den Zeilenumbruch)."""
        text = "1  Logo-Gestaltung  1  1.200,00  1.200,00 EUR\n2  Illustrationen  3  150,00  450,00 EUR"
        m = _Modell(_fakten({"betrag": "1200", "bezeichnung": "Logo-Gestaltung"},
                            {"betrag": "450", "bezeichnung": "Illustrationen"}))
        r = dokument_ki.ordne(text, [], m, 20000)
        self.assertEqual([p["betrag"] for p in r["positionen"]], ["1200", "450"])


class OhneKI(unittest.TestCase):
    def test_ohne_modell_und_demo_modus(self):
        for llm in (None, FakeLLM()):
            r = dokument_ki.ordne(TEXT, REGEL, llm, 20000)
            self.assertEqual((r["ki"], r["pruefung"], r["positionen"]), ("nicht verwendet", ["regeln"], REGEL))

    def test_ausfall_der_ki(self):
        r = dokument_ki.ordne(TEXT, REGEL, _Modell(fehler=True), 20000)
        self.assertEqual((r["ki"], [p["betrag"] for p in r["positionen"]]), ("fehlgeschlagen", ["300.00"]))

    def test_zu_langer_text(self):
        m = _Modell(_fakten({"betrag": "300"}))
        r = dokument_ki.ordne(TEXT, REGEL, m, 50)
        self.assertEqual((r["ki"], m.texte), ("nicht verwendet", []))

    def test_keine_ki_positionen(self):
        r = dokument_ki.ordne(TEXT, REGEL, _Modell(_fakten()), 20000)
        self.assertEqual(r["pruefung"], ["regeln"])


if __name__ == "__main__":
    unittest.main()
