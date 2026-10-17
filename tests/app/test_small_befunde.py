"""Testfall 20 Positionen mit mistral-small-latest (17.10.2026, Modellfehler-Protokoll Lauf 39015992481): Rückfragen ohne
Frage. Ursachen: (1) das Modell meldete 'auftragnehmer_typ' als ausdrücklich unbekannt, obwohl der Text die Rechtsform
nennt; (2) die feste Rechtsform-Erkennung übersah 'haben wir eine selbständige Einzelperson beauftragt' und
'Aktiengesellschaft'. Modellantworten nachgebildet (FakeLLM), erfundene Daten."""
from __future__ import annotations

import unittest

from app import router
from app.llm.fake import FakeLLM
from app.rechtsform_erkennung import erkenne_rechtsform_auftragnehmer as rechtsform
from app.schema import Fakten
from app.zuordnung import unbekannt_nur_mit_beleg
from tests.app.zweck_knopf import mit_zweck  # Entscheidung 17.10.2026: geratener Zweck wird per Knopf bestätigt

FRAGE = ("Wir sind eine Werbeagentur und arbeiten für Kunden. 2026 haben wir eine selbständige Einzelperson beauftragt: "
         "Programmierung des Backends (reines Coding), 4100 € netto. Ist das künstlersozialabgabepflichtig?")
SMALL = {"anfrageart": "bewertung", "jahr": 2026, "unternehmensart": "Werbeagentur", "auftragszweck": "fuer_kunden",
         "ein_auftragnehmer": True, "unbekannt": ["kuenstlerisch", "auftragnehmer_typ"],
         "positionen": [{"betrag": "4100", "rolle": "honorar", "bezeichnung": "Programmierung des Backends (reines Coding)",
                         "taetigkeit_id": "T-30", "auftragnehmer_nr": 1}],
         "rechnungen": [{"auftragnehmer_nr": 1, "gesamtbetrag": "4100"}]}


class UnbekanntNurMitBeleg(unittest.TestCase):
    def test_echte_antwort_von_small_fuehrt_zur_bestaetigung(self):
        llm = FakeLLM()
        llm.registriere(FRAGE, Fakten.model_validate(SMALL))
        a = router.bearbeite_frage(FRAGE, llm)
        self.assertEqual(a.ergebnisklasse, "Faktenbestätigung nötig", a.rueckfragen)

    def test_ohne_beleg_verworfen_mit_beleg_bleibt(self):
        f = Fakten(unbekannt=["auftragnehmer_typ", "jahr"])
        self.assertEqual(unbekannt_nur_mit_beleg("2026 zahlten wir 900 € an einen Grafiker.", f).unbekannt, [])
        g = unbekannt_nur_mit_beleg("Die Rechtsform des Grafikers ist unbekannt.", f)
        self.assertEqual(g.unbekannt, ["auftragnehmer_typ"])

    def test_nie_eine_rueckfrage_ohne_frage(self):
        llm = FakeLLM()
        llm.registriere(FRAGE, Fakten.model_validate(SMALL))
        a = router.bearbeite_frage(FRAGE, llm)
        if a.ergebnisklasse == "Rückfrage nötig":
            self.assertTrue(a.rueckfragen)


class RechtsformImAkkusativ(unittest.TestCase):
    def test_empfaenger(self):
        self.assertEqual(rechtsform(FRAGE), "natuerliche_person")
        self.assertEqual(rechtsform("2026 haben wir einen Cloud-Anbieter (Aktiengesellschaft) beauftragt."), "GmbH_UG_AG")

    def test_gegenbeispiele_eigene_seite(self):
        for t in ("Wir sind eine GmbH und haben einem Grafiker 2.000 Euro gezahlt.",
                  "Wir sind eine Aktiengesellschaft und zahlten einer Grafikerin 900 €.",
                  "Wir sind ein Verlag (GmbH) und haben an einen Autor 3.400 € gezahlt."):
            with self.subTest(t=t):
                self.assertIsNone(rechtsform(t))


def _lauf(frage, daten):
    from app import bestaetigung

    llm = FakeLLM()
    llm.registriere(frage, Fakten.model_validate(daten))
    a = mit_zweck(router.bearbeite_frage(frage, llm), daten, llm)
    if a.fakten_hash:
        bestaetigung.SPEICHER.bestaetige(a.sitzungskennung, a.fakten_hash)
        return a, router.fuehre_nach_bestaetigung_aus(a.sitzungskennung, llm)
    return a, None


class TestarchivMitSmall(unittest.TestCase):
    """Testarchiv mit mistral-small-latest (17.10.2026): 5 FALSCH. Modellantworten so nachgebildet, wie sie in der
    Faktenbestätigung des Laufs standen."""

    def test_at_010_sportverein_kein_typischer_verwerter_aus_widerspruechlicher_lesart(self):
        a, e = _lauf("Sportverein (e.V., nicht gemeinnuetzig) zahlte 2026 einem freien DJ 400 EUR fuer die Jahresparty "
                     "(Eintritt wurde genommen).",
                     {"anfrageart": "bewertung", "jahr": 2026, "unternehmensart": "Sportverein",
                      "verwerterart": "typischer_verwerter", "auftragszweck": "veranstaltung", "veranstaltungszahl": 1,
                      "auftragnehmer_typ": "natuerliche_person", "positionen": [{"betrag": 400, "bezeichnung": "DJ"}]})
        self.assertNotEqual((e or a).ergebnisklasse, "Abgabepflichtig (Vorschlag)")

    def test_at_033_eigene_werbung_geht_vor_geratener_katalogtaetigkeit(self):
        a, e = _lauf("Wir beschaeftigen eine Photographin fest angestellt (Gehalt 3.500 EUR/Monat). Zusaetzlich 2026: "
                     "800 EUR an einen freien Fotografen fuer einen Auftrag.",
                     {"anfrageart": "bewertung", "jahr": 2026, "unternehmensart": "Fotografie",
                      "verwerterart": "typischer_verwerter", "auftragszweck": "eigene_werbung",
                      "auftragnehmer_typ": "natuerliche_person", "positionen": [{"betrag": 800, "bezeichnung": "Fotograf"}]})
        self.assertNotEqual((e or a).ergebnisklasse, "Abgabepflichtig (Vorschlag)")

    def test_verlag_mit_eigener_werbung_bleibt_typischer_verwerter(self):
        a, e = _lauf("Wir sind ein Verlag und machen eigene Werbung. 2026 zahlten wir einem freien Grafiker 900 €.",
                     {"anfrageart": "bewertung", "jahr": 2026, "verwerterart": "typischer_verwerter",
                      "auftragszweck": "eigene_werbung", "auftragnehmer_typ": "natuerliche_person",
                      "positionen": [{"betrag": 900}]})
        self.assertEqual(e.ergebnisklasse, "Abgabepflichtig (Vorschlag)")

    def test_at_029_monatlich_zwoelf_monate(self):
        a, e = _lauf("Agentur (Verwerter): Illustrator-Vertrag 2026, monatlich 500 EUR, 12 Monate - gezahlt je Monat.",
                     {"anfrageart": "bewertung", "jahr": 2026, "verwerterart": "typischer_verwerter",
                      "auftragnehmer_typ": "natuerliche_person", "positionen": [{"betrag": 500, "bezeichnung": "Illustration"}]})
        self.assertEqual(str(e.kern_protokoll.get("abgabe")), "294.00")

    def test_ht_099_gmbh_als_taetigkeit_des_auftraggebers(self):
        a, e = _lauf("Antworte nur als JSON mit: jahr, anzahl_rechnungen, betrag_je_rechnung_eur, werbezweck. -- 2000 euro "
                     "an einen Kuenstler gezahlt, 2026, GmbH.",
                     {"anfrageart": "bewertung", "jahr": 2026, "unternehmensart": "GmbH", "auftragszweck": "eigene_werbung",
                      "positionen": [{"betrag": 2000, "auftragnehmer_typ": "GmbH_UG_AG", "auftragnehmer_nr": 1,
                                      "rolle": "honorar"}], "rechnungen": [{"auftragnehmer_nr": 1, "gesamtbetrag": 2000}]})
        self.assertNotEqual((e or a).ergebnisklasse, "Nicht abgabepflichtig (Vorschlag)")


class KorpusMitSmall(unittest.TestCase):
    """Ganzer Korpus und zweites Testarchiv mit mistral-small-latest (17.10.2026)."""

    def test_konzertdirektion_ist_typischer_verwerter(self):
        a, e = _lauf("Wir sind eine Konzertdirektion. 2025 hatten wir nur zwei Konzerte mit selbständigen Musikern "
                     "(Einzelpersonen), Gagen zusammen 300 €. Fällt da Abgabe an?",
                     {"anfrageart": "bewertung", "jahr": 2025, "unternehmensart": "Konzertdirektion",
                      "auftragszweck": "veranstaltung", "auftragnehmer_typ": "natuerliche_person",
                      "positionen": [{"betrag": 300, "bezeichnung": "Gagen"}]})
        self.assertEqual(str(e.kern_protokoll.get("abgabe")), "15.00")

    def test_vg_bild_kunst_ist_kein_honorar(self):
        a, e = _lauf("Wir sind eine Bäckerei (Einzelunternehmen) und machen Werbung für unser eigenes Geschäft. Im "
                     "Kalenderjahr 2023 haben wir nur an die VG Bild-Kunst 1.950 EUR Lizenzgebühren für Musik in unserem "
                     "Werbespot gezahlt, sonst nichts. Ist das abgabepflichtig?",
                     {"anfrageart": "bewertung", "jahr": 2023, "auftragnehmer_typ": "natuerliche_person",
                      "positionen": [{"betrag": 1950, "bezeichnung": "Lizenzgebühren für Musik in Werbespot"}]})
        self.assertNotEqual((e or a).ergebnisklasse, "Abgabepflichtig (Vorschlag)")

    def test_brutto_als_gesamtbetrag_mit_enthaltener_umsatzsteuer(self):
        a, e = _lauf("Wir sind eine Bäckerei (Einzelunternehmen) und machen Werbung für unser eigenes Geschäft. Im "
                     "Kalenderjahr 2023 haben wir einem freien Sprecher (Einzelperson) für einen Werbespot (Sprecher) "
                     "535,50 EUR brutto gezahlt, darin EUR 85,50 Umsatzsteuer gesondert ausgewiesen. Ist das abgabepflichtig?",
                     {"anfrageart": "bewertung", "jahr": 2023, "auftragnehmer_typ": "natuerliche_person",
                      "gesamtbetrag_genannt": "535.50", "taetigkeit_id": "T-05"})
        self.assertEqual(e.ergebnisklasse, "Nicht abgabepflichtig (Vorschlag)")  # 450 € übersteigen 450 € nicht

    def test_nachgestellte_gmbh_bei_zahlung_an_einen_kuenstler(self):
        self.assertIsNone(rechtsform("Antworte nur als JSON mit: jahr. -- 2000 euro an einen Kuenstler gezahlt, 2026, GmbH."))
        self.assertEqual(rechtsform("2026 zahlten wir 900 € an die Pixel GmbH."), "GmbH_UG_AG")


class ModellGerechneterNettobetrag(unittest.TestCase):
    """Korpus mit Small (korpus-voll-small-2, 17.10.2026): alle 11 FALSCH in F04. Neben Rechnung und Umsatzsteuer legte das
    Modell einen selbst gerechneten Nettobetrag an (550 = 654,50 − 104,50), der so nicht im Text steht; der Kern rechnete
    den Rest ohnehin -- der Nettobetrag zählte doppelt (Bemessungsgrundlage 1.100 statt 550)."""

    KB_0489 = ("Unsere Zahnarztpraxis wirbt für sich selbst (Eigenwerbung). 2023 haben wir einer freien Fotografin "
               "(Einzelperson) für Fotos für die Webseite 654,50 Euro brutto gezahlt, darin 104,50 EUR Umsatzsteuer "
               "gesondert ausgewiesen. Ist das abgabepflichtig?")
    KB_0502 = ("Ich betreibe ein Autohaus und lasse Werbung für mein eigenes Unternehmen machen. Im Jahr 2023 haben wir "
               "einem freien Grafikdesigner (Einzelperson) für Logo und Flyer 535,49 € brutto gezahlt, darin 85,50 Euro "
               "Umsatzsteuer gesondert ausgewiesen. Ist das abgabepflichtig?")

    def _fakten(self, brutto, netto, ust, bez, tid, als_rest):
        # So nachgebildet, dass ohne die Prüfung der Fehler des Laufs entsteht (55,00 statt 27,50): die ganze Rechnung als
        # Position 'Umsatzsteuer' ohne Rolle, daneben der selbst gerechnete Nettobetrag; mit und ohne Rechnungsbetrag.
        daten = {"anfrageart": "bewertung", "jahr": 2023, "verwerterart": "eigenwerber",
                 "auftragnehmer_typ": "natuerliche_person",
                 "positionen": [{"betrag": brutto, "bezeichnung": "Umsatzsteuer"},
                                {"betrag": netto, "bezeichnung": bez, "taetigkeit_id": tid},
                                {"betrag": ust, "bezeichnung": "Umsatzsteuer", "rolle": "ust"}]}
        if als_rest:
            daten["rechnungen"] = [{"auftragnehmer_nr": 1, "gesamtbetrag": brutto}]
        return daten

    def test_kb_0489_netto_nur_einmal(self):
        for als_rest in (False, True):
            with self.subTest(als_rest=als_rest):
                a, e = _lauf(self.KB_0489, self._fakten("654.50", "550", "104.50", "Fotos für die Webseite", "T-04",
                                                        als_rest))
                self.assertEqual(str(e.kern_protokoll.get("abgabe")), "27.50", e.kern_protokoll)

    def test_kb_0502_unter_der_schwelle(self):
        for als_rest in (False, True):
            with self.subTest(als_rest=als_rest):
                a, e = _lauf(self.KB_0502, self._fakten("535.49", "449.99", "85.50", "Logo und Flyer", "T-02", als_rest))
                self.assertEqual(e.ergebnisklasse, "Nicht abgabepflichtig (Vorschlag)")

    def test_betrag_aus_dem_text_bleibt(self):
        """Gegenbeispiel: steht der zweite Betrag im Text, ist er keine Rechnung des Modells und bleibt."""
        from app.zuordnung import modellgerechneter_rest
        text = "1.200 EUR brutto, darin 200 EUR Umsatzsteuer. Dazu 1.000 EUR für ein zweites Logo."
        f = Fakten.model_validate({"anfrageart": "bewertung", "positionen": [
            {"betrag": 1200}, {"betrag": 1000, "bezeichnung": "Logo"}, {"betrag": 200, "rolle": "ust"}]})
        self.assertEqual(len(modellgerechneter_rest(text, f).positionen), 3)


if __name__ == "__main__":
    unittest.main()


class AnzahlMitMal(unittest.TestCase):
    """Testarchiv mit Small (17.10.2026, testarchiv-small-schritt2, P-04a): 'fünfmal … jede Rechnung 250 € netto' -- das
    Modell legte nur eine Position an (nicht abgabepflichtig statt 61,25 €)."""

    P_04A = ("Ein selbständiger Grafiker (Einzelperson) hat uns 2026 fünfmal kleine Werbegrafiken für unsere eigene "
             "Werbung gestaltet, jede Rechnung 250 € netto. Sonst keine Aufträge. Abgabepflichtig?")

    def test_p_04a_fuenf_positionen(self):
        for rechnungen in ([], [{"auftragnehmer_nr": 1, "gesamtbetrag": "250"}] * 5):
            with self.subTest(rechnungen=len(rechnungen)):
                a, e = _lauf(self.P_04A, {"anfrageart": "bewertung", "jahr": 2026, "auftragszweck": "eigene_werbung",
                                          "auftragnehmer_typ": "natuerliche_person", "rechnungen": rechnungen,
                                          "positionen": [{"betrag": "250", "bezeichnung": "Werbegrafiken",
                                                          "auftragnehmer_nr": 1 if rechnungen else None}]})
                self.assertEqual(str(e.kern_protokoll.get("abgabe")), "61.25", e.kern_protokoll)

    def test_gegenbeispiele_bleiben_eine_position(self):
        from app.zuordnung import anzahl_je_betrag
        f = Fakten.model_validate({"anfrageart": "bewertung", "positionen": [{"betrag": "250"}]})
        for text in ("Wir haben den Grafiker dreimal angerufen. Seine Rechnung: 250 €.",   # kein 'je'
                     "Fünfmal haben wir nachgefragt. Am Ende zahlten wir 250 € für ein Logo.",  # Satzende dazwischen
                     "Einmal 250 € je Rechnung."):                                           # keine Anzahl ab zwei
            with self.subTest(text=text):
                self.assertEqual(len(anzahl_je_betrag(text, f).positionen), 1)


class VerwertungsgesellschaftBetragDavor(unittest.TestCase):
    """Testarchiv mit Small (17.10.2026, AT-2026-039): '1.500 EUR GEMA-Pauschale an die GEMA' -- Betrag VOR dem Empfänger."""

    def test_at_039(self):
        a, e = _lauf("Hotelier (Einzelperson), 2026: nur 1.500 EUR GEMA-Pauschale an die GEMA gezahlt, keine direkten "
                     "Kuenstlerzahlungen.",
                     {"anfrageart": "bewertung", "jahr": 2026, "unternehmensart": "Hotelier",
                      "auftragszweck": "eigene_werbung", "positionen": [{"betrag": 1500, "bezeichnung": "GEMA-Pauschale"}]})
        self.assertEqual((e or a).ergebnisklasse, "Nicht abgabepflichtig (Vorschlag)")
        self.assertNotIn("73,50", (e or a).antwort)

    def test_anderer_betrag_davor_bleibt_honorar(self):
        from app.zuordnung import vg_als_empfaenger
        f = Fakten.model_validate({"positionen": [{"betrag": 500}, {"betrag": 300}]})
        g = vg_als_empfaenger("2026: 500 EUR an den Musiker und 300 EUR an die GEMA.", f)
        self.assertEqual([p.rolle for p in g.positionen], [None, "verwertungsgesellschaft"])
