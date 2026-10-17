"""Regressionstests zu den Alltagsfällen F1–F4 (ksk-alltagsf_lle-4-testbelege-mit-soll-bewertung.pdf,
11.10.2026). Nur erfundene Daten; Soll-Werte aus der Testdatei, nicht vom Steuerberater geprüft.

OFFLINE: Die Modellantworten sind kontrolliert und den echten Antworten von mistral-large-latest
nachgebildet (aufgaben/audit/alltag4_ergebnis_large.md, dialog_nachgespielt_large.md). Geprüft
wird die Python-Logik:
- F1: Nutzungsrechte derselben Fotografin zählen mit (T-68), 'Image-Kampagne' ist Eigenwerbung.
- F2: Jahr aus den Rechnungsdaten, Recherche-Pauschale zählt (T-69), keine Reisekosten ohne Nachweis.
- F3: bezahlt wird der Rechnungsteller (GmbH), nicht das Film-Team (R-45, R-216).
- F4: Privatperson als Auftraggeber ist nicht abgabepflichtig (R-40, R-133), keine Schwelle."""
from __future__ import annotations

import json
import unittest
from decimal import Decimal as D
from pathlib import Path

from app import bestaetigung, pflichtangaben, router, zuordnung
from app.ergebnisklassen import FAKTEN_BESTAETIGUNG_NOETIG, RUECKFRAGE_NOETIG
from app.schema import Fakten, Position as P, Rechnung

KATALOG = json.loads((Path(__file__).resolve().parents[2] / "aufgaben" / "audit" / "testfall_alltag_4.json")
                     .read_text(encoding="utf-8"))
FRAGE = {f["id"]: f["frage"] for f in KATALOG["faelle"]}
NICHT = "Nicht abgabepflichtig (Vorschlag)"
ABGABEPFLICHTIG = "Abgabepflichtig (Vorschlag)"


class Modell:
    def __init__(self, *antworten: Fakten):
        self.antworten = list(antworten)

    def extrahiere_fakten(self, frage, verlauf=None, fallstand=None):
        return self.antworten.pop(0)

    def beschreibe_fall(self, kontext):  # pragma: no cover
        return ""


def _bestaetigt(antwort, llm):
    assert antwort.ergebnisklasse == FAKTEN_BESTAETIGUNG_NOETIG, (antwort.ergebnisklasse, antwort.rueckfragen)
    bestaetigung.SPEICHER.bestaetige(antwort.sitzungskennung, antwort.fakten_hash)
    return router.fuehre_nach_bestaetigung_aus(antwort.sitzungskennung, llm)


class TestF1Werbefotografie(unittest.TestCase):
    def _modell(self):
        return Modell(Fakten(
            anfrageart="bewertung", jahr=2026, leistungsart="Fotografie", taetigkeit_id="T-04", ein_auftragnehmer=True,
            positionen=[
                P(betrag=D("1800"), rolle="honorar", taetigkeit_id="T-04", auftragnehmer_nr=1,
                  bezeichnung="Produktfotografie Steinbruch, halbtägiges Shooting inkl. Konzeption"),
                P(betrag=D("220"), taetigkeit_id="T-04", auftragnehmer_nr=1, bezeichnung="Bildretusche und Farbkorrektur (12 Motive)"),
                P(betrag=D("450"), auftragnehmer_nr=1, bezeichnung="Nutzungsrechte Kampagne, 24 Monate, Web + Print"),
                P(betrag=D("469.30"), rolle="ust", auftragnehmer_nr=1, bezeichnung="Umsatzsteuer 19%"),
            ],
            rechnungen=[Rechnung(auftragnehmer_nr=1, gesamtbetrag=D("2939.30"))]))

    def test_ohne_rueckfrage_abgabepflichtig_121_03(self):
        llm = self._modell()
        erste = router.bearbeite_frage(FRAGE["F1"], llm, [])
        self.assertEqual(erste.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG, erste.rueckfragen)
        self.assertIn("Rechtliche Einordnung (Vorschlag des Systems, keine Angabe von Ihnen): Eigenwerbung", erste.fakten_zusammenfassung)
        ergebnis = _bestaetigt(erste, llm)
        self.assertEqual(ergebnis.ergebnisklasse, ABGABEPFLICHTIG)
        self.assertEqual(D(str(ergebnis.kern_protokoll["abgabe"])), D("121.03"))

    def test_nutzungsrechte_desselben_kuenstlers_zaehlen_mit(self):
        from app import taetigkeiten

        self.assertEqual(taetigkeiten.erkenne("Nutzungsrechte Kampagne, 24 Monate, Web + Print"), "T-68")
        self.assertEqual(taetigkeiten.beim_selben_kuenstler("T-68")[0], "zaehlt")

    def test_nutzungsrechte_allein_sind_kein_sicheres_kuenstlerisches_werk(self):
        from app import taetigkeiten

        self.assertEqual(taetigkeiten.gruppe("T-68"), "unsicher")

    def test_image_kampagne_ist_eigenwerbung(self):
        f = zuordnung.absichere_verwerterart("Sie hat für ihre Image-Kampagne diese Rechnung erhalten.", Fakten())
        self.assertEqual(f.verwerterart, "eigenwerber")


class TestF2PublizistVerlag(unittest.TestCase):
    def _modell(self, reise_rolle=None):
        return Modell(Fakten(
            anfrageart="bewertung", unternehmensart="Fachmagazin", leistungsart="Text/Redaktion", ein_auftragnehmer=True,
            positionen=[
                P(betrag=D("1400"), rolle="honorar", taetigkeit_id="T-03", auftragnehmer_nr=1,
                  bezeichnung="Fachartikel „Naturstein im modernen Innenausbau“, 6 Seiten, einmalige Nutzung"),
                P(betrag=D("350"), rolle=reise_rolle, auftragnehmer_nr=1, bezeichnung="Recherche-Pauschale (Fahrt, Literatur) lt. Vertrag"),
                P(betrag=D("332.50"), rolle="ust", auftragnehmer_nr=1, bezeichnung="USt 19 %"),
            ],
            rechnungen=[Rechnung(auftragnehmer_nr=1, gesamtbetrag=D("2082.50"))]))

    def test_ohne_rueckfrage_abgabepflichtig_85_75(self):
        llm = self._modell()
        erste = router.bearbeite_frage(FRAGE["F2"], llm, [])
        self.assertEqual(erste.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG, erste.rueckfragen)
        self.assertTrue(any(z.startswith("Jahr: 2026 (aus den Daten auf der Rechnung abgeleitet")
                            for z in erste.fakten_zusammenfassung), erste.fakten_zusammenfassung)
        ergebnis = _bestaetigt(erste, llm)
        self.assertEqual(ergebnis.ergebnisklasse, ABGABEPFLICHTIG)
        self.assertEqual(D(str(ergebnis.kern_protokoll["abgabe"])), D("85.75"))

    def test_pauschale_ist_keine_nachgewiesene_reisekosten(self):
        llm = self._modell(reise_rolle="fahrtkosten_nachgewiesen")
        ergebnis = _bestaetigt(router.bearbeite_frage(FRAGE["F2"], llm, []), llm)
        self.assertEqual(D(str(ergebnis.kern_protokoll["abgabe"])), D("85.75"))

    def test_nachgewiesene_fahrtkosten_bleiben_ausgenommen(self):
        f = Fakten(positionen=[P(betrag=D("80"), rolle="fahrtkosten_nachgewiesen", bezeichnung="Bahnfahrt")])
        f = zuordnung.absichere_rollen("Bahnfahrt 80 €, Ticket liegt bei", f)
        self.assertEqual(f.positionen[0].rolle, "fahrtkosten_nachgewiesen")

    def test_zaehler_vor_positionen_kein_problem_mehr(self):
        # Der eigentliche Fall steht in test_taetigkeiten.TestMistralPositionOhneObjekt.
        self.assertIn(D("1400"), zuordnung.betraege_im_text(FRAGE["F2"]))
        self.assertNotIn(D("1"), zuordnung.betraege_im_text(FRAGE["F2"]))


class TestJahrAusRechnungsdaten(unittest.TestCase):
    def test_einheitliches_jahr(self):
        f = zuordnung.jahr_aus_rechnungsdaten("Rechnung vom 12.06.2026, bezahlt am 20.06.2026", Fakten())
        self.assertEqual((f.jahr, f.jahr_aus_rechnungsdaten), (2026, True))

    def test_verschiedene_jahre_nicht(self):
        self.assertIsNone(zuordnung.jahr_aus_rechnungsdaten("Rechnung vom 15.12.2025, bezahlt am 10.01.2026", Fakten()).jahr)

    def test_andere_jahreszahl_im_text_nicht(self):
        self.assertIsNone(zuordnung.jahr_aus_rechnungsdaten("Rechnung vom 15.12.2025, Zahlung 2026", Fakten()).jahr)

    def test_genanntes_jahr_bleibt(self):
        f = zuordnung.jahr_aus_rechnungsdaten("Rechnung vom 15.12.2025", Fakten(jahr=2026))
        self.assertEqual((f.jahr, f.jahr_aus_rechnungsdaten), (2026, None))

    def test_ausdruecklich_unbekannt_bleibt_unbekannt(self):
        self.assertIsNone(zuordnung.jahr_aus_rechnungsdaten("Rechnung vom 15.12.2025", Fakten(unbekannt=["jahr"])).jahr)


GMBH, GBR = "GmbH_UG_AG", "GbR"


class TestF3Agenturrechnung(unittest.TestCase):
    def _modell(self, *weitere):
        f = Fakten(
            anfrageart="bewertung", jahr=2026, ein_auftragnehmer=True,
            positionen=[
                P(betrag=D("3200"), auftragnehmer_typ=GMBH, bezeichnung="Kampagnen-Konzeption durch Agentur-Team"),
                P(betrag=D("1900"), auftragnehmer_typ=GMBH, taetigkeit_id="T-08", bezeichnung="Illustrationen, im eigenen Namen der Agentur"),
                P(betrag=D("24500"), auftragnehmer_typ=GBR, taetigkeit_id="T-13", bezeichnung="TV-Spot-Produktion durch „Roter Hering GbR“"),
                P(betrag=D("750"), auftragnehmer_typ=GMBH, taetigkeit_id="T-05", bezeichnung="Synchronsprecher-Honorar"),
                P(betrag=D("880"), rolle="verwertungsgesellschaft", bezeichnung="Musik-Lizenz (GEMA)"),
                P(betrag=D("400"), auftragnehmer_typ=GBR, bezeichnung="Fahrzeug- und Materialkosten der GbR"),
                P(betrag=D("3150"), auftragnehmer_typ=GMBH, taetigkeit_id="T-02", bezeichnung="Kommunikationsdesign (Retainer)"),
                P(betrag=D("660.82"), rolle="ust", bezeichnung="USt 19 %"),
            ],
            rechnungen=[Rechnung(auftragnehmer_nr=1, gesamtbetrag=D("35440.82"))])
        return Modell(f, *weitere)

    def test_alle_positionen_an_die_agentur_gmbh_nicht_abgabepflichtig(self):
        llm = self._modell()
        erste = router.bearbeite_frage(FRAGE["F3"], llm, [])
        # Offen bleibt nur die Art des Auftraggebers (aus dem Beleg nicht sicher ableitbar).
        self.assertEqual(erste.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertEqual(erste.rueckfragen, [pflichtangaben.FRAGE_VERWERTERART])
        stand = bestaetigung.SPEICHER.hole_fakten(erste.sitzungskennung)
        # Sonderrollen (Umsatzsteuer, GEMA) behalten ihren eigenen Ausschlussgrund (ALLTAG-2026-999).
        self.assertEqual({p.auftragnehmer_typ for p in stand.positionen if p.rolle not in ("ust", "verwertungsgesellschaft")}, {GMBH})
        self.assertEqual(stand.rechnungsteller_typ, GMBH)
        zweite = router.wende_feldantwort_an(erste.sitzungskennung, "verwerterart", "eigenwerber", llm)
        self.assertIn("Rechnungsteller (an ihn wird gezahlt): GmbH/UG/AG", zweite.fakten_zusammenfassung)
        ergebnis = _bestaetigt(zweite, llm)
        self.assertEqual(ergebnis.ergebnisklasse, NICHT)
        self.assertNotIn("abgabe", ergebnis.kern_protokoll)
        self.assertIn("Die Rechnung stellt eine Gesellschaft (GmbH/UG/AG)", ergebnis.antwort)
        self.assertIn("eigene Prüfung bei ihr", ergebnis.antwort)

    def test_vertreter_wird_nicht_ueberschrieben(self):
        text = ("Rechnungsteller: Agentur Beispiel GmbH, handelt als Vertreter der Künstlerin\n"
                "Pos. 01 Illustration: 1.900,00 €")
        f = Fakten(positionen=[P(betrag=D("1900"), auftragnehmer_typ="natuerliche_person")])
        f = zuordnung.rechnungsteller_als_zahlungsempfaenger([text], f)
        self.assertEqual(f.positionen[0].auftragnehmer_typ, "natuerliche_person")
        self.assertIsNone(f.rechnungsteller_typ)

    def test_nur_positionen_dieser_rechnung(self):
        erste = "Rechnungsteller: Agentur Beispiel GmbH\nPos. 01 Konzept: 3.200,00 €"
        zweite = "Außerdem eine freie Grafikerin: 500 €"
        f = Fakten(positionen=[P(betrag=D("3200")), P(betrag=D("500"), auftragnehmer_typ="natuerliche_person")])
        f = zuordnung.rechnungsteller_als_zahlungsempfaenger([erste, zweite], f)
        self.assertEqual([p.auftragnehmer_typ for p in f.positionen], [GMBH, "natuerliche_person"])
        self.assertIsNone(f.ein_auftragnehmer)

    def test_zwei_rechnungsteller_in_einer_nachricht_nicht_raten(self):
        text = "Rechnungsteller: A GmbH\nRechnungsteller: B GbR\n1.000 €"
        self.assertIsNone(zuordnung.rechnungsteller_typ(text))

    def test_eigene_seite_ist_nicht_der_rechnungsteller(self):
        self.assertIsNone(zuordnung.rechnungsteller_typ("Rechnungsteller: wir selbst (Beispiel GmbH)"))

    def test_freier_journalist_ist_natuerliche_person(self):
        self.assertEqual(zuordnung.rechnungsteller_typ("Rechnungsteller: Thomas Meyer, freier Journalist"),
                         "natuerliche_person")


class TestF4Privatpersonen(unittest.TestCase):
    def _modell(self):
        return Modell(Fakten(
            anfrageart="bewertung", jahr=2026, leistungsart="Fotografie",
            positionen=[P(betrag=D("1650"), taetigkeit_id="T-04", bezeichnung="Hochzeitsreportage, 10 Std., 2 Fotografinnen"),
                        P(betrag=D("420"), taetigkeit_id="T-02", bezeichnung="Hochwertiges Fotobuch, 60 Seiten, Layout und Druck"),
                        P(betrag=D("394.25"), rolle="ust", bezeichnung="USt 19 %")]))

    def test_nicht_abgabepflichtig_ohne_rueckfrage_und_ohne_schwelle(self):
        llm = self._modell()
        erste = router.bearbeite_frage(FRAGE["F4"], llm, [])
        self.assertEqual(erste.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG, erste.rueckfragen)
        self.assertIn("Rechtliche Einordnung (Vorschlag des Systems, keine Angabe von Ihnen): Privatperson (kein Unternehmen)", erste.fakten_zusammenfassung)
        ergebnis = _bestaetigt(erste, llm)
        self.assertEqual(ergebnis.ergebnisklasse, NICHT)
        self.assertIn("Privatpersonen und private Personengruppen", ergebnis.antwort)
        self.assertNotIn("Schwelle des Jahres", ergebnis.antwort)
        self.assertNotIn("abgabe", ergebnis.kern_protokoll)
        # Grundregel 10: die Auslegung der KSK erscheint nicht als 'Norm'.
        self.assertIn("Verwaltungspraxis (Auslegung der KSK, kein Gesetz):** KSK-Info 04", ergebnis.antwort)

    def test_knopf_privatperson_vorhanden(self):
        optionen = pflichtangaben.rueckfrage_optionen([pflichtangaben.FRAGE_VERWERTERART], Fakten(jahr=2026))
        # Schritt 2 (17.10.2026): Knopf in Alltagssprache; er setzt den Zweck 'privat' (Einordnung wie bisher).
        self.assertEqual(optionen[0]["werte"]["Ein privater Auftrag"], "privat")

    def test_privatperson_als_auftragnehmer_ist_kein_privater_auftraggeber(self):
        for text in ("Wir haben eine Privatperson beauftragt, 500 €.",
                     "Der Auftragnehmer ist eine Privatperson.",
                     "Wir sind ein Verlag und verkaufen Bücher an Privatkunden.",
                     "Der Auftraggeber ist keine Privatperson, sondern eine GmbH."):
            with self.subTest(text=text):
                self.assertFalse(zuordnung.privater_auftraggeber(text))

    def test_unbelegter_modellwert_privat_wird_verworfen(self):
        f = zuordnung.absichere_verwerterart("Wir haben 2026 ein Logo für 900 € gekauft.", Fakten(verwerterart="privat"))
        self.assertIsNone(f.verwerterart)

    def test_andere_art_im_text_hat_vorrang(self):
        f = zuordnung.absichere_verwerterart(
            "Mein Mandant ist eine Werbeagentur; Rechnungsempfänger sind auch Privatkunden.", Fakten())
        self.assertEqual(f.verwerterart, "typischer_verwerter")


if __name__ == "__main__":
    unittest.main()


class TestPauschaleAusdruecklichGenannt(unittest.TestCase):
    """Prüfkatalog 11.10.2026 (P-20b, live): das Modell ordnete die bestätigte
    Übungsleiterpauschale als normale Bewertung ein -- Abgabe 147,00 € statt 46,20 €."""

    FRAGE = ("Unser abgabepflichtiger gemeinnütziger Musikverein hat 2020 einer nebenberuflichen Chorleiterin "
             "3.500 € gezahlt. Sie hat die Übungsleiterpauschale schriftlich bestätigt. Wie hoch ist die Abgabe?")

    def test_pauschale_wird_abgezogen(self):
        llm = Modell(Fakten(anfrageart="bewertung", jahr=2020, leistungsart="Musikalische Leitung",
                            verwerterart="typischer_verwerter", auftragnehmer_typ="natuerliche_person",
                            auftraggeber_typ="Verein",
                            positionen=[P(betrag=D("3500"), bezeichnung="Zahlung an Chorleiterin", taetigkeit_id="T-17")]))
        a = router.bearbeite_frage(self.FRAGE, llm, [])
        if a.ergebnisklasse == FAKTEN_BESTAETIGUNG_NOETIG:
            a = _bestaetigt(a, llm)
        self.assertEqual(a.ergebnisklasse, ABGABEPFLICHTIG)
        self.assertEqual(D(str(a.kern_protokoll["abgabe"])), D("46.20"))

    def test_verneint_oder_beide_nicht(self):
        self.assertEqual(zuordnung.ergaenze_pauschale("ohne Übungsleiterpauschale", Fakten()).anfrageart, None)
        beide = "Übungsleiterpauschale und Ehrenamtspauschale"
        self.assertIsNone(zuordnung.ergaenze_pauschale(beide, Fakten()).pauschale_art)

    def test_bestaetigung_nur_wenn_genannt(self):
        f = zuordnung.ergaenze_pauschale("Die Übungsleiterpauschale wird genutzt.", Fakten(anfrageart="bewertung"))
        self.assertEqual((f.anfrageart, f.pauschale_bestaetigung), ("uebungsleiter_pauschale", None))
