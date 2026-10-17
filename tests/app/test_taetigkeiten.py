"""Tätigkeitsprüfung (Testfall 20 Positionen, 11.10.2026).

Vorher galt jede Zahlung an eine Einzelperson als künstlerische Leistung: Programmierung, SEO
oder Datenschutzberatung kamen als sicher "Abgabepflichtig" heraus. Jetzt ordnet das System
jede Leistung einer Tätigkeit aus dem Excel-Blatt 'Tätigkeitsabgrenzung' zu. Unsichere oder
unbekannte Leistungen ergeben nie "Abgabepflichtig". Nur erfundene Testdaten."""
from __future__ import annotations

import unittest
from decimal import Decimal as D

from app import bestaetigung, pflichtangaben, router, taetigkeiten as T, zuordnung
from app.ergebnisklassen import GRENZFALL
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position as P
from tests.app.zweck_knopf import mit_zweck  # Entscheidung 17.10.2026: geratener Zweck wird per Knopf bestätigt

NP = "natuerliche_person"
A = "Abgabepflichtig (Vorschlag)"
N = "Nicht abgabepflichtig (Vorschlag)"


def _ergebnis(frage: str, fakten: Fakten):
    llm = FakeLLM()
    llm.registriere(frage, fakten)
    a = mit_zweck(router.bearbeite_frage(frage, llm), fakten, llm)
    if a.fakten_hash:
        bestaetigung.SPEICHER.bestaetige(a.sitzungskennung, a.fakten_hash)
        a = router.fuehre_nach_bestaetigung_aus(a.sitzungskennung, llm)
    return a


def _fall(bezeichnung: str, betrag: str = "1000", typ: str = NP, verwerter: str = "typischer_verwerter", **extra):
    return Fakten(anfrageart="bewertung", jahr=2026, verwerterart=verwerter,
                  positionen=[P(betrag=D(betrag), bezeichnung=bezeichnung, auftragnehmer_typ=typ, **extra)])


class TestErkennung(unittest.TestCase):
    def test_blatt_ist_geladen_und_jede_zeile_hat_eine_quelle(self):
        self.assertGreater(len(T.alle()), 20)
        for e in T.alle():
            self.assertTrue(e["regel_ids"] or e["fundstellen"], f"{e['id']} ohne Fundstelle")
            self.assertTrue(e["status"].startswith("Entwurf"), e["id"])

    def test_typische_leistungen(self):
        faelle = {
            "Programmierung des Backends (reines Coding)": "nicht_kuenstlerisch",
            "Webdesign & UI-Konzeption": "kuenstlerisch",
            "Webdesigner gestaltet und programmiert die Seiten": "kuenstlerisch",  # R-184
            "Korrektorat und Rechtschreibprüfung": "nicht_kuenstlerisch",
            "Lektorat mit Überarbeitung des Stils": "kuenstlerisch",
            "Moderation des Firmen-Workshops": "nicht_kuenstlerisch",  # R-183
            "Moderation der Jubiläumsgala": "kuenstlerisch",
            "SEO-Analyse": "nicht_kuenstlerisch",
            "Schaltung von Google-Ads": "nicht_kuenstlerisch",
            "Übersetzung der Website (Kreativtext)": "kuenstlerisch",
            "Übersetzung": "unsicher",
            "Miete für Kamera-Equipment": "unsicher",
            "Logo-Gestaltung": "kuenstlerisch",
        }
        for text, gruppe in faelle.items():
            self.assertEqual(T.gruppe(T.erkenne(text)), gruppe, text)

    def test_unbekannt_und_nichts(self):
        self.assertIsNone(T.erkenne("Beratung zur Datenschutz-Grundverordnung"))
        self.assertEqual(T.kombiniere(None, None, beschrieben=True), T.UNBEKANNT)
        self.assertIsNone(T.kombiniere(None, None, beschrieben=False))
        self.assertEqual(T.gruppe(T.UNBEKANNT), "unsicher")

    def test_modell_und_feste_erkennung_muessen_uebereinstimmen(self):
        self.assertEqual(T.kombiniere("T-02", "T-30", True), T.WIDERSPRUCH)
        self.assertEqual(T.kombiniere("T-02", "T-04", True), "T-04")  # gleiche Gruppe
        self.assertEqual(T.kombiniere("T-99-erfunden", None, True), T.UNBEKANNT)

    def test_modellanweisung_nennt_ids_aber_keine_gruppen(self):
        from app.llm.mistral import _taetigkeit_anweisung

        text = _taetigkeit_anweisung()
        self.assertIn("T-30:", text)
        self.assertNotIn("nicht künstlerisch", text)


class TestRouter(unittest.TestCase):
    def test_programmierung_ist_nicht_abgabepflichtig(self):
        a = _ergebnis("Programmierung", _fall("Programmierung des Backends (reines Coding)", "4100"))
        self.assertEqual(a.ergebnisklasse, N)
        self.assertIn("nicht mitgezählt", a.antwort)

    def test_unbekannte_leistung_ist_nie_abgabepflichtig(self):
        a = _ergebnis("DSGVO", _fall("Beratung zur Datenschutz-Grundverordnung (DSGVO)", "950"))
        self.assertEqual(a.ergebnisklasse, GRENZFALL)
        self.assertIn("nicht im Regelwerk eingeordnet", a.antwort)
        self.assertIn("46,55 €", a.antwort)  # Abgabe, falls es mitzählt (vom Kern gerechnet)

    def test_widerspruch_modell_gegen_erkennung_ist_grenzfall(self):
        a = _ergebnis("W", _fall("Programmierung", taetigkeit_id="T-02"))
        self.assertEqual(a.ergebnisklasse, GRENZFALL)
        self.assertIn("nicht eindeutig", a.antwort)

    def test_gmbh_bleibt_unberuehrt(self):
        a = _ergebnis("G", _fall("Beratung zur Datenschutz-Grundverordnung", typ="GmbH_UG_AG"))
        self.assertEqual(a.ergebnisklasse, N)

    def test_sammelrechnung_rechnet_beide_ausgaenge(self):
        positionen = [P(betrag=D(b), bezeichnung=t, auftragnehmer_typ=NP) for t, b in (
            ("Webdesign", "2500"), ("Programmierung des Backends", "4100"),
            ("Werbetexte", "600"), ("Projektmanagement", "1800"))]
        a = _ergebnis("S", Fakten(anfrageart="bewertung", jahr=2026, verwerterart="typischer_verwerter",
                                  ein_auftragnehmer=False, positionen=positionen))
        self.assertEqual(a.ergebnisklasse, GRENZFALL)
        self.assertEqual(D(str(a.kern_protokoll["abgabe_ohne_unsichere"])), D("151.90"))  # 3.100 € × 4,9 %
        self.assertEqual(D(str(a.kern_protokoll["abgabe_falls_kuenstlerisch"])), D("240.10"))  # 4.900 € × 4,9 %
        self.assertIn("Programmierung", a.kern_protokoll["taetigkeit_nicht"])

    def test_unsichere_leistung_ohne_auswirkung_aendert_nichts(self):
        """Eigenwerbung 2026, alles zusammen unter der Schwelle: das Ergebnis ist in beiden
        Fällen gleich -- kein Grenzfall nötig."""
        a = _ergebnis("U", _fall("Beratung zur Datenschutz-Grundverordnung", "300", verwerter="eigenwerber"))
        self.assertEqual(a.ergebnisklasse, N)

    def test_veranstaltungszahl_unbekannt_mit_unsicherer_leistung_nie_abgabepflichtig(self):
        f = Fakten(anfrageart="bewertung", jahr=2026, verwerterart="generalklausel", einnahmeabsicht=True,
                   veranstaltungszahl_unbekannt=True, auftragnehmer_typ=NP, leistungsart="Eventberatung",
                   gesamtbetrag_genannt=D("5000"))
        k = router._rufe_kern_auf(zuordnung.ergaenze_taetigkeit("Eventberatung", f))
        self.assertNotEqual(k.klasse, A)


class TestPflichtangabe(unittest.TestCase):
    def test_ohne_beschreibung_wird_nach_der_leistung_gefragt(self):
        f = Fakten(anfrageart="bewertung", jahr=2026, verwerterart="eigenwerber", auftragnehmer_typ=NP,
                   gesamtbetrag_genannt=D("2000"))
        self.assertEqual(pflichtangaben.fehlende_pflichtangaben(f), [pflichtangaben.FRAGE_LEISTUNG])

    def test_antwort_auf_die_frage_wird_die_beschreibung(self):
        llm = FakeLLM()
        llm.registriere("Fall", Fakten(anfrageart="bewertung", jahr=2026, verwerterart="eigenwerber",
                                       auftragnehmer_typ=NP, gesamtbetrag_genannt=D("2000")))
        a = mit_zweck(router.bearbeite_frage("Fall", llm), "eigenwerber", llm)
        self.assertEqual(a.rueckfragen, [pflichtangaben.FRAGE_LEISTUNG])
        b = router.bearbeite_frage("ein neues Logo", llm, ["Fall"], a.sitzungskennung)
        self.assertTrue(any("Grafikdesign" in z for z in b.fakten_zusammenfassung), b.fakten_zusammenfassung)


if __name__ == "__main__":
    unittest.main()


class TestMistralPositionOhneObjekt(unittest.TestCase):
    """Prüfkatalog 11.10.2026 (large): eine bloße Zahl in 'positionen' wurde zur erfundenen
    Position über 1,00 € (K-04 dadurch fälschlich abgabepflichtig). Nie umdeuten."""

    def _llm(self, *antworten):
        import json
        from app.llm.mistral import MistralLLM

        llm = MistralLLM(api_key="nur-test-ohne-netz")
        folge = iter(antworten)
        aufrufe = []

        def aufruf(system, user, **kw):
            aufrufe.append(system)
            return json.dumps(next(folge))

        llm._aufruf = aufruf
        return llm, aufrufe

    def test_zweiter_versuch_und_dann_richtig(self):
        # Die bloße Zahl 1800 steht im Text als Betrag: nie umdeuten, zweiter Versuch.
        llm, aufrufe = self._llm({"jahr": 2025, "positionen": [1800, {"betrag": 900}]},
                                 {"jahr": 2025, "positionen": [{"betrag": 1800}, {"betrag": 900}]})
        f = llm.extrahiere_fakten("1.800 € und 900 €")
        self.assertEqual([p.betrag for p in f.positionen], [D("1800"), D("900")])
        self.assertIn("keine bloßen Zahlen", aufrufe[1])

    def test_zaehler_ohne_betrag_im_text_wird_verworfen(self):
        # Alltagsfälle 11.10.2026 (F2): eine '1' vor den Positionen ist kein Betrag des Nutzers.
        llm, aufrufe = self._llm({"jahr": 2025, "positionen": [1, {"betrag": 900}]})
        f = llm.extrahiere_fakten("900 €")
        self.assertEqual([p.betrag for p in f.positionen], [D("900")])
        self.assertEqual(len(aufrufe), 1)

    def test_zweimal_falsch_ist_ein_fehler(self):
        from app.llm.base import LLMFehlgeschlagen

        llm, _ = self._llm({"positionen": [1800]}, {"positionen": [1800]})
        with self.assertRaises(LLMFehlgeschlagen):
            llm.extrahiere_fakten("1.800 €")


class TestDerselbeKuenstler(unittest.TestCase):
    """Mehrere Positionen desselben Künstlers: Nebenkosten und nicht künstlerische Nebenleistungen
    gehören zum Entgelt (R-42, R-175), beim Designer keine Trennung kreativ/technisch (R-117);
    nachträgliche Vervielfältigung nicht (R-49). Regeln aus der Excel-Spalte 'Rechnet derselbe
    Künstler das mit ab'."""

    def _positionen(self, *paare, nr=None):
        return [P(betrag=D(b), bezeichnung=t, auftragnehmer_typ=NP, auftragnehmer_nr=nr) for t, b in paare]

    def test_designer_rechnet_gestaltung_programmierung_miete_und_druck_ab(self):
        positionen = self._positionen(("Webdesign", "2000"), ("Programmierung des Backends", "1000"),
                                      ("Miete für Kamera-Equipment", "200"), ("Druckkosten", "500"))
        a = _ergebnis("D", Fakten(anfrageart="bewertung", jahr=2026, verwerterart="typischer_verwerter",
                                  ein_auftragnehmer=True, positionen=positionen))
        self.assertEqual(a.ergebnisklasse, A)
        self.assertEqual(D(str(a.kern_protokoll["bemessungsgrundlage"])), D("3200"))  # ohne Druck (R-49)
        self.assertIn("Nebenleistung oder Nebenkosten desselben Künstlers", a.antwort)
        self.assertIn("Druckkosten", a.kern_protokoll["taetigkeit_nicht"])

    def test_verschiedene_auftragnehmer_zaehlen_einzeln(self):
        positionen = self._positionen(("Webdesign", "2000"), ("Programmierung des Backends", "1000"))
        a = _ergebnis("V", Fakten(anfrageart="bewertung", jahr=2026, verwerterart="typischer_verwerter",
                                  ein_auftragnehmer=False, positionen=positionen))
        self.assertEqual(D(str(a.kern_protokoll["bemessungsgrundlage"])), D("2000"))

    def test_eigenstaendige_leistung_desselben_kuenstlers_entscheidet_der_steuerberater(self):
        positionen = self._positionen(("Fotografie", "1500"), ("SEO-Analyse", "500"), nr=1)
        a = _ergebnis("E", Fakten(anfrageart="bewertung", jahr=2026, verwerterart="typischer_verwerter",
                                  positionen=positionen))
        self.assertEqual(a.ergebnisklasse, GRENZFALL)
        self.assertEqual(D(str(a.kern_protokoll["abgabe_ohne_unsichere"])), D("73.50"))
        self.assertEqual(D(str(a.kern_protokoll["abgabe_falls_kuenstlerisch"])), D("98.00"))

    def test_ohne_kuenstlerische_position_gilt_nichts_davon(self):
        positionen = self._positionen(("Programmierung", "1000"), ("Miete für Kamera-Equipment", "200"), nr=1)
        a = _ergebnis("O", Fakten(anfrageart="bewertung", jahr=2026, verwerterart="typischer_verwerter",
                                  positionen=positionen))
        self.assertNotEqual(a.ergebnisklasse, A)

    def test_rueckfrage_nur_wenn_es_darauf_ankommt(self):
        llm = FakeLLM()
        llm.registriere("R", Fakten(anfrageart="bewertung", jahr=2026, verwerterart="typischer_verwerter",
                                    positionen=self._positionen(("Webdesign", "2000"), ("Programmierung", "1000"))))
        a = router.bearbeite_frage("R", llm)
        self.assertEqual(a.rueckfragen, [pflichtangaben.FRAGE_GLEICHER_AUFTRAGNEHMER])
        o = a.rueckfrage_optionen[0]
        b = router.wende_feldantwort_an(a.sitzungskennung, o["feld"], o["werte"][pflichtangaben.GLEICHER_JA], llm)
        self.assertIn("Alle Positionen vom selben Auftragnehmer: ja", b.fakten_zusammenfassung)
        nur_kunst = Fakten(anfrageart="bewertung", jahr=2026, verwerterart="typischer_verwerter",
                           positionen=self._positionen(("Webdesign", "2000"), ("Fotografie", "1000")))
        self.assertEqual(pflichtangaben.fehlende_pflichtangaben(zuordnung.ergaenze_taetigkeit("", nur_kunst)), [])

    def test_demo_erkennt_eine_rechnung_einer_person(self):
        llm = FakeLLM()
        frage = ("2026 hat uns eine Rechnung von einer Webdesignerin (Einzelperson) erreicht, wir sind eine Werbeagentur:\n"
                 "1. Webdesign: 2000 €\n2. Programmierung: 1000 €")
        f = llm.extrahiere_fakten(frage)
        self.assertTrue(f.ein_auftragnehmer)


class TestSonderrolleBrauchtBeleg(unittest.TestCase):
    """Prüfkatalog 11.10.2026 (large): 'ust' für Materialkosten (P-29) und 'gewinnzuweisung'
    für eine Zahlung an den Manager (P-39) nahmen Beträge ohne Grundlage heraus."""

    def test_ohne_beleg_zaehlt_der_betrag(self):
        f = Fakten(positionen=[P(betrag=D("2000")), P(betrag=D("300"), rolle="ust")])
        self.assertIsNone(zuordnung.absichere_rollen("2.000 € Honorar plus 300 € Materialkosten", f).positionen[1].rolle)
        g = Fakten(positionen=[P(betrag=D("500"), rolle="gewinnzuweisung")])
        self.assertIsNone(zuordnung.absichere_rollen("500 € direkt an ihren Manager", g).positionen[0].rolle)

    def test_mit_beleg_bleibt_die_rolle(self):
        f = Fakten(positionen=[P(betrag=D("190"), rolle="ust")])
        self.assertEqual(zuordnung.absichere_rollen("1.000 € zzgl. 190 € Umsatzsteuer", f).positionen[0].rolle, "ust")

    def test_material_desselben_kuenstlers_zaehlt_mit(self):
        positionen = [P(betrag=D("2000"), bezeichnung="Illustration", auftragnehmer_typ=NP),
                      P(betrag=D("300"), bezeichnung="Materialkosten", auftragnehmer_typ=NP)]
        a = _ergebnis("M", Fakten(anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter",
                                  ein_auftragnehmer=True, positionen=positionen))
        self.assertEqual(D(str(a.kern_protokoll["bemessungsgrundlage"])), D("2300"))  # R-42
