"""Auswertung der 'nachgefragten' Fälle (14.10.2026): vier Fälle, die in 16 von 16 Gesamtläufen
nachfragten, obwohl der Text die nötige Angabe enthielt. Spielt die ECHTEN Modellantworten der
Messung offline durch (tests/app/daten_nachgefragt_live_1410.json). Soll aus aufgaben/audit/pruefkatalog.json.
Fehlt die Art des Auftraggebers, setzt der Test sie wie der Knopf des Testlaufs. Erfundene Daten."""
from __future__ import annotations

import json
import unittest
from decimal import Decimal as D
from pathlib import Path

from app import bestaetigung, router, zuordnung
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position as P
from tests.app.zweck_knopf import mit_zweck  # Entscheidung 17.10.2026: geratener Zweck wird per Knopf bestätigt

W = Path(__file__).resolve().parents[2]
LIVE = {k: v for k, v in json.loads((W / "tests/app/daten_nachgefragt_live_1410.json").read_text(encoding="utf-8")).items()
        if not k.startswith("_")}
KATALOG = {f["id"]: f for f in json.loads((W / "aufgaben/audit/pruefkatalog.json").read_text(encoding="utf-8"))["faelle"]}
KNOPF = {"Eigenwerbung": "eigenwerber", "Typischer Verwerter": "typischer_verwerter", "natürliche Person": "natuerliche_person"}
KLASSE = {"A": "Abgabepflichtig (Vorschlag)", "N": "Nicht abgabepflichtig (Vorschlag)", "G": "Grenzfall → Steuerberater entscheidet"}


def _ergebnis(frage, roh, knoepfe):
    roh = dict(roh)
    if "verwerterart" in knoepfe:
        roh.setdefault("verwerterart", KNOPF[knoepfe["verwerterart"]])
    if "auftragnehmer_typ" in knoepfe:
        roh.setdefault("auftragnehmer_typ", KNOPF[knoepfe["auftragnehmer_typ"]])
    llm = FakeLLM()
    llm.registriere(frage, Fakten.model_validate(roh))
    a = mit_zweck(router.bearbeite_frage(frage, llm), roh, llm)
    if a.ergebnisklasse != "Faktenbestätigung nötig":
        return a, None
    bestaetigung.SPEICHER.bestaetige(a.sitzungskennung, a.fakten_hash)
    return a, router.fuehre_nach_bestaetigung_aus(a.sitzungskennung, FakeLLM())


class EchteModellantworten(unittest.TestCase):
    def test_jede_beobachtete_modellantwort_fuehrt_zum_soll(self):
        for fid, daten in LIVE.items():
            soll = KATALOG[fid]
            for nr, roh in enumerate(daten["modell"]):
                with self.subTest(fall=fid, antwort=nr):
                    a, c = _ergebnis(daten["frage"], roh, soll.get("knoepfe", {}))
                    self.assertIsNotNone(c, f"{fid}/{nr}: {a.ergebnisklasse}: {a.antwort[:200]}")
                    self.assertEqual(c.ergebnisklasse, KLASSE[soll["soll"][0]], c.antwort[:300])
                    for feld, wert in (soll.get("zahl") or {}).items():
                        self.assertEqual(c.kern_protokoll.get(feld), D(wert), f"{fid}/{nr} {feld}")

    def test_bandleader_nennt_die_fundstelle_von_r31_nicht_werbung_fuer_dritte(self):
        daten = LIVE["P-14"]
        _, c = _ergebnis(daten["frage"], daten["modell"][0], KATALOG["P-14"]["knoepfe"])
        self.assertIn("KSK-Info 04 (Stand 08.2025), Abschn. 2d", c.antwort)  # Fundstelle von R-31
        self.assertIn("Auslegung der KSK, kein Gesetz", c.antwort)
        self.assertNotIn("Nr. 7", c.antwort)


class Gegenproben(unittest.TestCase):
    def test_privatperson_als_auftragnehmer_ist_kein_privater_auftraggeber(self):
        for text in ("Wir haben 2026 einer Privatperson (Einzelperson) 900 € für Fotos gezahlt.",
                     "Für unsere Firma hat ein Fotograf (privat versichert) Bilder gemacht, 900 €.",
                     "Ein Ehepaar betreibt eine GmbH und hat privat einen Fotografen bezahlt."):
            with self.subTest(text=text):
                self.assertFalse(zuordnung.privater_auftraggeber(text))

    def test_private_feier_mit_auftraggeber(self):
        self.assertTrue(zuordnung.privater_auftraggeber("Ein Brautpaar hat für die Hochzeitsfeier eine Band gebucht."))

    def test_druckkosten_werden_nicht_zu_webdesign(self):
        text = "Eine Webdesign-Agentur hat uns 2026 nur Druckkosten für Flyer berechnet, 500 €."
        f = Fakten(anfrageart="bewertung", positionen=[P(betrag=D("500"), bezeichnung="Druckkosten", taetigkeit_id="T-30")])
        self.assertNotEqual(zuordnung.ergaenze_taetigkeit(text, f).positionen[0].taetigkeit_id, "T-01")

    def test_ohne_zustimmung_des_modells_bleibt_der_widerspruch(self):
        text = "Ein Webdesigner hat die Website gestaltet und programmiert, 3.000 €."
        f = Fakten(anfrageart="bewertung", positionen=[P(betrag=D("3000"), bezeichnung="Website Gestaltung und Programmierung",
                                                        taetigkeit_id="T-30")])
        self.assertNotEqual(zuordnung.ergaenze_taetigkeit(text, f).positionen[0].taetigkeit_id, "T-01")

    def test_uebungsleiter_ohne_jeden_betrag_fragt_weiter(self):
        from app import pflichtangaben
        f = Fakten(anfrageart="uebungsleiter_pauschale", jahr=2025)
        self.assertIn(pflichtangaben.FRAGE_UEBUNGSLEITER_BETRAG, pflichtangaben.fehlende_pflichtangaben(f))


class Musikverein(unittest.TestCase):
    """R-30, R-57 (KSK-Info 12, Abschn. 4): nicht kommerzielle Musikvereine nach der Generalklausel."""

    def test_vereinseigener_dirigent_bleibt_ausser_betracht(self):
        text = "Unser Hobbyorchester-Verein hatte 2026 vier Konzerte mit Eintritt. Gastsolist 800 €, vereinseigener Dirigent 1.500 €."
        f = Fakten(anfrageart="bewertung", jahr=2026, positionen=[P(betrag=D("800"), bezeichnung="Gastsolist"),
                                                                  P(betrag=D("1500"), bezeichnung="vereinseigener Dirigent")])
        g = zuordnung.musikverein_generalklausel(text, f)
        self.assertEqual(g.verwerterart, "generalklausel")
        self.assertEqual([p.rolle for p in g.positionen], [None, "vereinseigene_leitung"])
        self.assertTrue(zuordnung.ergaenze_einnahmeabsicht(text, g).einnahmeabsicht)

    def test_andere_vereinseigene_kuenstler_zaehlen_weiter(self):
        # KSK-Info 12: Zahlungen an alle anderen Künstler sind meldepflichtig, auch an Vereinsmitglieder.
        text = "Unser Laienchor (Verein) hatte 2026 fünf Auftritte. Die vereinseigene Sängerin bekam 900 €."
        f = Fakten(anfrageart="bewertung", jahr=2026, positionen=[P(betrag=D("900"), bezeichnung="vereinseigene Sängerin")])
        self.assertIsNone(zuordnung.musikverein_generalklausel(text, f).positionen[0].rolle)

    def test_ohne_freizeit_hinweis_keine_annahme(self):
        # Chor/Orchester mit überwiegendem Aufführungszweck ist typischer Verwerter (R-159): dann nicht raten.
        f = Fakten(anfrageart="bewertung", jahr=2025)
        self.assertIsNone(zuordnung.musikverein_generalklausel("Unser Musikverein unterrichtet 2025 15 Schüler.", f).verwerterart)

    def test_verband_und_berufsorchester_nicht(self):
        f = Fakten(anfrageart="bewertung", jahr=2026)
        for text in ("Unser Landesverband der Laienmusik veranstaltet 2026 sechs Konzerte.",
                     "Das Berufsorchester e. V. (kein Hobbyorchester) spielt 2026 zehn Konzerte."):
            with self.subTest(text=text):
                self.assertIsNone(zuordnung.musikverein_generalklausel(text, f).verwerterart)

    def test_eintritt_frei_setzt_keine_einnahmeabsicht(self):
        f = Fakten(verwerterart="generalklausel")
        self.assertIsNone(zuordnung.ergaenze_einnahmeabsicht("Vier Konzerte, Eintritt frei, mit Eintrittskarten zur Platzvergabe.", f).einnahmeabsicht)

    def test_rolle_nur_im_vereinsfall(self):
        f = Fakten(verwerterart="typischer_verwerter", positionen=[P(betrag=D("1500"), bezeichnung="Dirigent", rolle="vereinseigene_leitung")])
        self.assertIsNone(zuordnung.musikverein_generalklausel("Ein Theater zahlt dem Dirigenten 1.500 €.", f).positionen[0].rolle)


class KernGeneralklausel(unittest.TestCase):
    def test_hoechstens_drei_veranstaltungen_ohne_einnahmeabsicht_nicht_abgabepflichtig(self):
        from kern import rechnen as K
        e = K.veranstaltungen(2026, 2, D("5000"), None, "generalklausel")
        self.assertEqual(e.klasse, K.NICHT)

    def test_vier_veranstaltungen_ohne_einnahmeabsicht_fragt(self):
        from kern import rechnen as K
        self.assertEqual(K.veranstaltungen(2026, 4, D("5000"), None, "generalklausel").klasse, K.RUECKFRAGE)


class GrundsatzfrageOhneBetrag(unittest.TestCase):
    """P-36 (Vertretung, R-33) und P-37 (Nachweismakler, R-35)."""

    def test_im_namen_des_kunden_ist_keine_vertretung_des_kuenstlers(self):
        f = Fakten(anfrageart="bewertung", jahr=2026)
        g = zuordnung.ergaenze_vertretung("Wir buchen als Eventagentur die Band im Namen und für Rechnung unseres Kunden.", f)
        self.assertIsNone(g.vertretung_kuenstler)

    def test_im_eigenen_namen_ist_keine_vertretung(self):
        f = Fakten(anfrageart="bewertung", jahr=2026)
        t = "Wir handeln im eigenen Namen, nicht im Namen und für Rechnung der Sängerin."
        self.assertIsNone(zuordnung.ergaenze_vertretung(t, f).vertretung_kuenstler)

    def test_kontakt_mit_honorareinzug_ist_kein_nachweismakler(self):
        f = Fakten(anfrageart="bewertung", jahr=2025)
        self.assertIsNone(zuordnung.ergaenze_vertretung("Wir vermitteln nur den Kontakt und kassieren das Honorar.", f).nachweismakler)

    def test_vertretung_ohne_angabe_fragt_nach_dem_vertragspartner(self):
        from app import pflichtangaben
        f = Fakten(anfrageart="bewertung", jahr=2025, vertretung_kuenstler=True)
        self.assertEqual(pflichtangaben.fehlende_pflichtangaben(f), [pflichtangaben.FRAGE_VERTRAGSPARTNER_ABGABEPFLICHTIG])

    def test_modellwerte_in_systemfeldern_werden_verworfen(self):
        f = Fakten(vertretung_kuenstler=True, nachweismakler=True)
        g = zuordnung.ohne_systemfelder(f)
        self.assertEqual((g.vertretung_kuenstler, g.nachweismakler), (None, None))


class ZahlungswegImFreitext(unittest.TestCase):
    """Härtetest HT-2026-001 (Nutzer, 14.10.2026): Durchleitung und offene Erstattung zählten still mit
    (Live 1 von 6: 3.760 € statt 2.210 €)."""

    FRAGE = json.loads((W / "aufgaben/audit/haertetest_ht_2026_001.json").read_text(encoding="utf-8"))["faelle"][0]["frage"]

    def _fakten(self):
        return Fakten(anfrageart="bewertung", jahr=2026, verwerterart="typischer_verwerter", ein_auftragnehmer=False, positionen=[
            P(betrag=D("2210"), bezeichnung="Werkleistung für einen Kundenauftrag (Fotografie)", auftragnehmer_typ="natuerliche_person"),
            P(betrag=D("1150"), bezeichnung="Zahlung an Band", auftragnehmer_typ="GbR"),
            P(betrag=D("400"), bezeichnung="Auftritt eines Zauberers", auftragnehmer_typ="natuerliche_person")])

    def test_band_und_zauberer_offen_fotograf_zaehlt(self):
        g = zuordnung.zahlungsweg_im_freitext(self.FRAGE, self._fakten())
        self.assertEqual([p.zahlungsweg_unklar for p in g.positionen], [None, True, True])

    def test_ergebnis_grenzfall_mit_sicherem_teil(self):
        llm = FakeLLM()
        llm.registriere(self.FRAGE, self._fakten())
        a = router.bearbeite_frage(self.FRAGE, llm)
        bestaetigung.SPEICHER.bestaetige(a.sitzungskennung, a.fakten_hash)
        c = router.fuehre_nach_bestaetigung_aus(a.sitzungskennung, FakeLLM())
        self.assertEqual(c.ergebnisklasse, "Grenzfall → Steuerberater entscheidet")
        self.assertEqual(c.kern_protokoll.get("abgabe_ohne_unsichere"), D("108.29"))
        self.assertNotIn("Bemessungsgrundlage: 3.760,00 €", c.antwort)

    def test_ohne_begriff_bleibt_alles(self):
        f = self._fakten()
        self.assertEqual(zuordnung.zahlungsweg_im_freitext("Fotograf 2.210 €, Band 1.150 €, Zauberer 400 €.", f), f)

    def test_mit_rechnungsteller_zeile_nicht_angewendet(self):
        f = self._fakten()
        text = "Rechnungsteller: Agentur Muster GmbH\nPos. 1 Band 1.150 € (durchgeleitet)"
        self.assertEqual(zuordnung.zahlungsweg_im_freitext(text, f), f)


class HaertetestHT2026001Echt(unittest.TestCase):
    """Alle echten Modellantworten des Härtetests: nie still mitgezählt, sicherer Teil 108,29 € (2.210 € × 4,9 %)."""

    def test_jede_modellantwort(self):
        frage = ZahlungswegImFreitext.FRAGE
        varianten = json.loads((W / "tests/app/daten_haertetest_ht_2026_001.json").read_text(encoding="utf-8"))["modell"]
        for nr, roh in enumerate(varianten):
            with self.subTest(antwort=nr):
                roh = dict(roh)
                roh.setdefault("verwerterart", "typischer_verwerter")
                llm = FakeLLM()
                llm.registriere(frage, Fakten.model_validate(roh))
                a = router.bearbeite_frage(frage, llm)
                self.assertEqual(a.ergebnisklasse, "Faktenbestätigung nötig", a.rueckfragen)
                self.assertIn("2.210,00 € (gezahlter Euro-Betrag; angegeben 2.400 USD)", " ".join(a.fakten_zusammenfassung))
                bestaetigung.SPEICHER.bestaetige(a.sitzungskennung, a.fakten_hash)
                c = router.fuehre_nach_bestaetigung_aus(a.sitzungskennung, FakeLLM())
                self.assertEqual(c.ergebnisklasse, "Grenzfall → Steuerberater entscheidet")
                self.assertEqual(c.kern_protokoll.get("abgabe_ohne_unsichere"), D("108.29"))
