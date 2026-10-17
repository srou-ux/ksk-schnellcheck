"""Alltags-Serie AT-2026-001 bis 060 (Nutzer): Funde aus dem Live-Lauf 'Chatbot direkt' f6a5d1a (15.10.2026).

Die Modellantworten sind so nachgebildet, wie sie in der Faktenbestätigung standen. Katalog:
aufgaben/audit/alltag_at_001_060.json (Status ENTWURF)."""
from __future__ import annotations

import unittest
from decimal import Decimal as D

from app import taetigkeiten as T, zuordnung
from app.rechtsform_erkennung import erkenne_rechtsform_auftragnehmer
from app.schema import Fakten, Position as P
from tests.app.test_fehlerquellen import _ende


class AlltagLive(unittest.TestCase):
    def test_at_024_modellhonorar_nicht_still(self):
        self.assertEqual(T.gruppe(T.erkenne("Modellhonorar")), "unsicher")  # T-76

    def test_at_027_anzahlung_und_offener_rest(self):
        frage = ("Honorar 2026 3.000 EUR an freien Komponisten; wir haben am 15.12.2026 1.800 EUR angezahlt, Rest "
                 "1.200 EUR stehen noch aus.")
        roh = {"jahr": 2026, "leistungsart": "Musik", "verwerterart": "typischer_verwerter", "positionen": [
            {"betrag": "3000", "bezeichnung": "Honorar an freien Komponisten", "auftragnehmer_typ": "natuerliche_person"}],
            "rechnungen": [{"auftragnehmer_nr": 1, "gesamtbetrag": "3000"}]}
        ende = _ende(frage, roh)
        self.assertNotEqual(ende.kern_protokoll.get("abgabe"), D("147.00"))
        self.assertEqual(ende.kern_protokoll.get("abgabe_ohne_unsichere"), D("88.20"))

    def test_at_035_gmbh_zahlte_ist_der_zahler(self):
        self.assertIsNone(erkenne_rechtsform_auftragnehmer("GmbH zahlte 2026: 1.200 EUR an Videograf fuer Imagefilm"))
        self.assertEqual(erkenne_rechtsform_auftragnehmer("Die Foto GmbH hat uns 800 EUR berechnet"), "GmbH_UG_AG")
        text = ("GmbH zahlte 2026: 1.200 EUR an Videograf fuer Imagefilm (Firmenzweck). Der Inhaber liess privat von "
                "demselben Videografen seine Hochzeit filmen: 900 EUR - vom GmbH-Konto bezahlt (Versehen).")
        f = zuordnung.rechtsform_nur_wo_genannt(text, Fakten(positionen=[
            P(betrag=D("1200"), auftragnehmer_typ="GmbH_UG_AG"), P(betrag=D("900"), auftragnehmer_typ="GmbH_UG_AG")]))
        self.assertEqual([p.auftragnehmer_typ for p in f.positionen], [None, None])

    def test_at_054_gmbh_am_satzende_ohne_positionen(self):
        f = zuordnung.rechtsform_nur_wo_genannt("Wir haben 2026 viertausend Euro an eine freie Malerin gezahlt, GmbH.",
                                                Fakten(auftragnehmer_typ="GmbH_UG_AG", gesamtbetrag_genannt=D("4000")))
        self.assertIsNone(f.auftragnehmer_typ)

    def test_at_060_auskunft_ohne_betrag(self):
        frage = "Ab wann muss man 2026 KSK zahlen? Also welche Grenze?"
        ende = _ende(frage, {"jahr": 2026, "anfrageart": "bewertung"})
        self.assertEqual(ende.ergebnisklasse, "Auskunft aus dem Regelwerk")
        self.assertIn("1.000,00 €", ende.antwort)

    def test_eine_frage_mit_betrag_bleibt_bewertung(self):
        f = zuordnung.absichere_anfrageart("Welche Grenze gilt für 800 EUR an einen Grafiker?", Fakten(jahr=2026))
        self.assertNotEqual(f.anfrageart, "auskunft")


class AlltagLive0647320(unittest.TestCase):
    """Zweiter Live-Lauf (0647320): das Modell lieferte andere Fakten als im ersten Lauf."""

    def test_at_027_zwei_positionen_rest_offen(self):
        text = ("Honorar 2026 3.000 EUR an freien Komponisten; wir haben am 15.12.2026 1.800 EUR angezahlt, Rest "
                "1.200 EUR stehen noch aus.")
        f = zuordnung.zahlungsweg_im_freitext(text, Fakten(positionen=[P(betrag=D("1800")), P(betrag=D("1200"))]))
        self.assertEqual([p.zahlungsweg_unklar for p in f.positionen], [None, True])

    def test_at_035_private_hochzeit_nur_im_eigenen_satz(self):
        text = ("GmbH zahlte 2026: 1.200 EUR an Videograf fuer Imagefilm (Firmenzweck). Der Inhaber liess privat von "
                "demselben Videografen seine Hochzeit filmen: 900 EUR - vom GmbH-Konto bezahlt (Versehen).")
        f = zuordnung.zahlungsweg_im_freitext(text, Fakten(positionen=[P(betrag=D("1200")), P(betrag=D("900"))]))
        self.assertEqual([p.zahlungsweg_unklar for p in f.positionen], [None, True])
        self.assertIn("privater Zweck", f.positionen[1].offen_grund)

    def test_at_053_englisch(self):
        text = "We are a German GmbH and paid a freelance photographer EUR 2,500 in 2026 for our website photos."
        self.assertEqual(erkenne_rechtsform_auftragnehmer(text), "natuerliche_person")
        f = zuordnung.rechtsform_nur_wo_genannt(text, Fakten(auftraggeber_typ="GmbH_UG_AG", positionen=[
            P(betrag=D("2500"), auftragnehmer_typ="GmbH_UG_AG")]))
        self.assertIsNone(f.positionen[0].auftragnehmer_typ)
        # 'US-Dollar' macht eine Rechtsform nicht zur eigenen Seite
        self.assertEqual(erkenne_rechtsform_auftragnehmer("Zahlung 4.500 US-Dollar an die Foto GmbH"), "GmbH_UG_AG")


class AlltagLive1e97851(unittest.TestCase):
    def test_at_033_gehalt_zaehlt_nie_still(self):
        frage = ("Wir beschaeftigen eine Photographin fest angestellt (Gehalt 3.500 EUR/Monat). Zusaetzlich 2026: 800 EUR "
                 "an einen freien Fotografen fuer einen Auftrag.")
        roh = {"jahr": 2026, "leistungsart": "Fotografie", "verwerterart": "eigenwerber", "positionen": [
            {"betrag": "3500", "bezeichnung": "Gehalt fest angestellte Photographin", "auftragnehmer_typ": "natuerliche_person",
             "auftragnehmer_nr": 1},
            {"betrag": "800", "bezeichnung": "Auftrag an freien Fotografen", "auftragnehmer_typ": "natuerliche_person",
             "auftragnehmer_nr": 2}], "rechnungen": [{"auftragnehmer_nr": 2, "gesamtbetrag": "800"}]}
        ende = _ende(frage, roh)
        self.assertNotEqual(ende.ergebnisklasse, "Abgabepflichtig (Vorschlag)")
        self.assertIn("abhängiger Beschäftigung", ende.kern_protokoll.get("zahlungsweg_unklar", ""))


if __name__ == "__main__":
    unittest.main()
