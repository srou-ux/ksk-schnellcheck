"""Rechnungen in fremder Währung (14.10.2026, Soll nach Testfall L-23: 'Rückfrage: Euro-Betrag
klären; keine erfundene Euro-Summe'). Offline mit nachgebildeter Modellantwort (FakeLLM)."""
from __future__ import annotations

import unittest
from decimal import Decimal as D

from app import bestaetigung, router, zuordnung
from app.ergebnisklassen import RUECKFRAGE_NOETIG
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position as P

EIGEN = dict(anfrageart="bewertung", jahr=2026, verwerterart="eigenwerber", auftragnehmer_typ="natuerliche_person")


def _fakten(*positionen, **extra):
    return Fakten(**{**EIGEN, **extra}, positionen=list(positionen))


def _bestaetige(antwort):
    bestaetigung.SPEICHER.bestaetige(antwort.sitzungskennung, antwort.fakten_hash)
    return router.fuehre_nach_bestaetigung_aus(antwort.sitzungskennung, FakeLLM())


class Erkennung(unittest.TestCase):
    def test_waehrungen_und_schreibweisen(self):
        for text, code, betrag in (("2.000 US-Dollar", "USD", "2000"), ("USD 2.000", "USD", "2000"), ("1.500 $", "USD", "1500"),
                                   ("3.000 CHF", "CHF", "3000"), ("1.200 Pfund", "GBP", "1200"), ("250.000 Yen", "JPY", "250000"),
                                   ("800 kanadische Dollar", "CAD", "800")):
            erg = zuordnung.fremdwaehrung_betraege(text)
            self.assertEqual([(b, c) for b, c, _ in erg], [(D(betrag), code)], text)

    def test_euro_rechnung_mit_dem_wort_dollar_ist_kein_fremdbetrag(self):
        self.assertEqual(zuordnung.fremdwaehrung_betraege("1.500 € gezahlt; die Rechnung lautet nicht auf kanadische Dollar."), [])


class Ablauf(unittest.TestCase):
    FRAGE = "Unsere GmbH hat 2026 für eigene Werbung einem freien Fotografen (Einzelperson) in den USA 2.000 US-Dollar für Werbefotos gezahlt."

    def test_nur_dollar_rueckfrage_statt_euro_rechnung(self):
        llm = FakeLLM()
        llm.registriere(self.FRAGE, _fakten(P(betrag=D("2000"), bezeichnung="Werbefotos")))
        a = router.bearbeite_frage(self.FRAGE, llm)
        self.assertEqual(a.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertIn("in fremder Währung angegeben (2.000 USD)", a.antwort)
        self.assertNotIn("98,00", a.antwort)

    def test_euro_betrag_als_antwort_und_ergebnis(self):
        llm = FakeLLM()
        llm.registriere(self.FRAGE, _fakten(P(betrag=D("2000"), bezeichnung="Werbefotos")))
        a = router.bearbeite_frage(self.FRAGE, llm)
        b = router.bearbeite_frage("Laut Kontoauszug wurden dafür 1.850,00 € abgebucht.", llm, [self.FRAGE], a.sitzungskennung)
        self.assertEqual(b.ergebnisklasse, "Faktenbestätigung nötig")
        self.assertIn("1.850,00 € (gezahlter Euro-Betrag; angegeben 2.000 USD)", " ".join(b.fakten_zusammenfassung))
        c = _bestaetige(b)
        self.assertEqual(c.kern_protokoll.get("bemessungsgrundlage"), D("1850.00"))
        self.assertEqual(c.kern_protokoll.get("abgabe"), D("90.65"))

    def test_nur_zahl_als_antwort(self):
        llm = FakeLLM()
        llm.registriere(self.FRAGE, _fakten(P(betrag=D("2000"), bezeichnung="Werbefotos")))
        a = router.bearbeite_frage(self.FRAGE, llm)
        b = router.bearbeite_frage("1850", llm, [self.FRAGE], a.sitzungskennung)
        self.assertIn("1.850,00 €", " ".join(b.fakten_zusammenfassung))

    def test_euro_betrag_im_selben_satz_ohne_rueckfrage(self):
        frage = self.FRAGE + " Abgebucht wurden 1.850,00 €."
        frage = frage.replace("gezahlt. Abgebucht", "gezahlt, abgebucht")
        llm = FakeLLM()
        llm.registriere(frage, _fakten(P(betrag=D("2000"), bezeichnung="Werbefotos"), P(betrag=D("1850"))))
        a = router.bearbeite_frage(frage, llm)
        self.assertEqual(a.ergebnisklasse, "Faktenbestätigung nötig")
        zusammen = " ".join(a.fakten_zusammenfassung)
        self.assertIn("1.850,00 €", zusammen)
        self.assertNotIn("2.000,00 €", zusammen)  # nicht doppelt
        self.assertEqual(_bestaetige(a).kern_protokoll.get("bemessungsgrundlage"), D("1850"))

    def test_gemischte_rechnung_nur_die_fremde_position_offen(self):
        frage = "Rechnung 2026 eines freien Grafikers:\nPos. 1 Logo: 1.200,00 EUR\nPos. 2 Bildlizenz: 500 USD"
        llm = FakeLLM()
        llm.registriere(frage, _fakten(P(betrag=D("1200"), bezeichnung="Logo"), P(betrag=D("500"), bezeichnung="Bildlizenz")))
        a = router.bearbeite_frage(frage, llm)
        self.assertEqual(a.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertIn("„Bildlizenz“ ist in fremder Währung", a.antwort)
        self.assertNotIn("„Logo“ ist in fremder Währung", a.antwort)

    def test_kern_rechnet_nie_mit_fremdbetrag(self):
        f = _fakten(P(betrag=D("2000"), bezeichnung="Werbefotos", fremdwaehrung="USD", fremd_betrag="2.000 USD"))
        a = router._nach_bestaetigung("x", f, FakeLLM())
        self.assertEqual(a.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertNotIn("98,00", a.antwort)

    def test_gesamtbetrag_nur_in_fremder_waehrung(self):
        frage = "Wir haben 2026 einem freien Grafiker (Einzelperson) für eigene Werbung insgesamt 3.000 CHF gezahlt."
        llm = FakeLLM()
        llm.registriere(frage, Fakten(**EIGEN, gesamtbetrag_genannt=D("3000")))
        a = router.bearbeite_frage(frage, llm)
        self.assertEqual(a.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertIn("3.000 CHF", a.antwort)

    def test_euro_rechnung_unveraendert(self):
        frage = "Unsere GmbH hat 2026 für eigene Werbung einem freien Fotografen (Einzelperson) 2.000 € gezahlt."
        llm = FakeLLM()
        llm.registriere(frage, _fakten(P(betrag=D("2000"), bezeichnung="Werbefotos")))
        a = router.bearbeite_frage(frage, llm)
        self.assertEqual(a.ergebnisklasse, "Faktenbestätigung nötig")
        self.assertEqual(_bestaetige(a).kern_protokoll.get("abgabe"), D("98.00"))


if __name__ == "__main__":
    unittest.main(verbosity=2)


class ModellSchreibtWaehrungInsFeld(unittest.TestCase):
    """Live-Lauf 14.10.2026 (W-05, W-07, W-08): das Modell schrieb '"betrag": "1500 $"'; die
    Schemaprüfung verwarf die ganze Antwort. Jetzt: nur die Zahl, nur wenn sie so im Text steht."""

    def _llm(self, roh):
        from app.llm.mistral import MistralLLM
        import json
        llm = MistralLLM.__new__(MistralLLM)
        llm._aufruf = lambda system, text, json_objekt=False, schema=None: json.dumps(roh)
        return llm

    def test_betrag_mit_dollarzeichen_wird_zahl_und_bleibt_fremd(self):
        frage = "Wir sind eine Werbeagentur und haben 2026 einem Texter 1.500 $ gezahlt."
        f = self._llm({"anfrageart": "bewertung", "jahr": 2026,
                       "positionen": [{"betrag": "1500 $", "bezeichnung": "Werbetexte"}]}).extrahiere_fakten(frage)
        self.assertEqual(f.positionen[0].betrag, D("1500"))
        g = zuordnung.markiere_fremdwaehrung(frage, f)
        self.assertEqual(g.positionen[0].fremdwaehrung, "USD")

    def test_yen_mit_tausenderpunkt_und_rechnung(self):
        frage = "Wir haben 2026 einer Illustratorin aus Tokio 250.000 Yen gezahlt."
        f = self._llm({"anfrageart": "bewertung", "positionen": [{"betrag": "250.000 Yen"}],
                       "rechnungen": [{"auftragnehmer_nr": 1, "gesamtbetrag": "250.000 Yen"}]}).extrahiere_fakten(frage)
        self.assertEqual(f.positionen[0].betrag, D("250000"))

    def test_betrag_der_nicht_im_text_steht_bleibt_ein_fehler(self):
        from app.llm.base import LLMFehlgeschlagen
        frage = "Wir haben 2026 einem Fotografen 2.000 US-Dollar gezahlt."
        with self.assertRaises(LLMFehlgeschlagen):
            self._llm({"positionen": [{"betrag": "1850 USD"}]}).extrahiere_fakten(frage)

    def test_andere_waehrung_als_im_text_bleibt_ein_fehler(self):
        from app.llm.base import LLMFehlgeschlagen
        frage = "Wir haben 2026 einem Fotografen 2.000 US-Dollar gezahlt."
        with self.assertRaises(LLMFehlgeschlagen):
            self._llm({"positionen": [{"betrag": "2000 CHF"}]}).extrahiere_fakten(frage)

    def test_zusatztext_im_feld_bleibt_ein_fehler(self):
        self.assertIsNone(zuordnung.fremdbetrag_als_zahl("ca. 2000 USD netto", "2.000 USD"))


class ModellFuelltSystemfelder(unittest.TestCase):
    """Live 14.10.2026 (W-03, 7fdc4f9): das Modell setzte fremd_betrag '2000' selbst."""

    def test_modellwerte_in_waehrungsfeldern_werden_verworfen(self):
        frage = ("Unsere GmbH hat 2026 für eigene Werbung einem freien Fotografen (Einzelperson) in den USA "
                 "2.000 US-Dollar für Werbefotos gezahlt, abgebucht wurden 1.850,00 €. Ist das abgabepflichtig?")
        llm = FakeLLM()
        llm.registriere(frage, _fakten(P(betrag=D("1850"), bezeichnung="Werbefotos", fremdwaehrung="USD", fremd_betrag="2000")))
        a = router.bearbeite_frage(frage, llm)
        self.assertEqual(a.ergebnisklasse, "Faktenbestätigung nötig", a.antwort[:300])
        self.assertIn("1.850,00 € (gezahlter Euro-Betrag; angegeben 2.000 USD)", " ".join(a.fakten_zusammenfassung))


class ModellLaesstFremdbetragWeg(unittest.TestCase):
    """Live 14.10.2026 (W-05, 615dffa): das Modell las '1.500 $' nicht aus."""

    def test_frage_nach_dem_euro_betrag_statt_allgemein_nach_dem_betrag(self):
        frage = "Wir sind eine Werbeagentur und haben 2026 einem freien Texter (Einzelperson) aus Kanada 1.500 $ für Werbetexte gezahlt. Abgabepflichtig?"
        llm = FakeLLM()
        llm.registriere(frage, Fakten(anfrageart="bewertung", jahr=2026, verwerterart="typischer_verwerter",
                                      auftragnehmer_typ="natuerliche_person"))
        a = router.bearbeite_frage(frage, llm)
        self.assertEqual(a.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertIn("in fremder Währung angegeben (1.500 USD)", a.antwort)
        b = router.bearbeite_frage("1.400,00 €", llm, [frage], a.sitzungskennung)
        self.assertIn("1.400,00 €", " ".join(b.fakten_zusammenfassung))
