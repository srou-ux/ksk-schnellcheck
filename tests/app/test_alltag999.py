"""Regressionstests zu ALLTAG-2026-999 „Viel-Künstler-Sammelrechnung“ (Testbeleg des Nutzers, 11.10.2026).
Erfundene Daten. Soll aus der Testdatei (Entwurf); Pos. 10 Provision ist ausdrücklich offen (R-38/R-39).

Befunde (aufgaben/audit/alltag999_auswertung.md), je ein Test:
- B1 Durchleitung/Direktvertrag zählt beim Mandanten (KSK-Info 27, KSK-Info 13, R-127) -- vorher Grenzfall.
- B2 gleicher Betrag in zwei Positionen (700 € Tanz 'eigener Name', 700 € Gesang 'durchgereicht').
- B3 Lichtkünstlerin blieb 'nicht eingeordnet' (neue Zeile T-19 aus KSK-Info 06).
- B4 Fundstelle Nr. 7 statt Nr. 3 beim Veranstalter (R-07 -> R-03/R-126).
- B5 Rückfrage nach der Art des Auftraggebers trotz 'Messe GmbH, Veranstalterin' (KSK-Info 13, R-126).
- B6 Provision: nicht mitgezählt, aber als offen gekennzeichnet, mit Betrag für den anderen Fall.
- B7 Umsatzsteuer bekam als Grund 'Zahlung an Kapitalgesellschaft'.
OFFLINE: Modellantwort nachgebildet."""
from __future__ import annotations

import json
import unittest
from decimal import Decimal as D
from pathlib import Path

from app import bestaetigung, router, taetigkeiten, zuordnung
from app.ergebnisklassen import FAKTEN_BESTAETIGUNG_NOETIG
from app.schema import Fakten, Position as P, Rechnung

FRAGE = json.loads((Path(__file__).resolve().parents[2] / "aufgaben" / "audit" / "testfall_alltag_999.json")
                   .read_text(encoding="utf-8"))["faelle"][0]["frage"]
NP, G = "natuerliche_person", "GmbH_UG_AG"


def _p(betrag, bez, tid=None, typ=NP, **kw):
    return P(betrag=D(betrag), bezeichnung=bez, taetigkeit_id=tid, auftragnehmer_typ=typ, **kw)


def _modellantwort():
    return Fakten(anfrageart="bewertung", positionen=[
        _p("1200", "Fotoshooting Messe-Eroeffnung", "T-04"), _p("1600", "Live-Konzert Messebuehne", "T-07", typ="GbR"),
        _p("800", "Buehnengrafik und Plakatmotive", "T-02"), _p("900", "Schauspieler-Auftritt", "T-15"),
        _p("700", "Tanzperformance", "T-64"), _p("950", "Autorenlesung", "T-03"), _p("620", "Pressetexte", "T-03"),
        _p("700", "Backing-Vocals Firmenvideo", "T-07"), _p("1100", "Lichtkunst-Installation"),
        _p("480", "Vermittlungsprovision Komposition", "T-07", typ=G), _p("2720", "Direktzahlung Komponist", "T-07"),
        _p("336", "Reisekosten Okafor, pauschal", rolle="fahrtkosten_nachgewiesen"),
        _p("1400", "Ton- und Lichttechnik-Anmietung", "T-65", typ="Ausland"), _p("900", "Uebersetzung lit.", "T-10"),
        _p("2220.34", "USt 19%", typ=None, rolle="ust")],
        rechnungen=[Rechnung(auftragnehmer_nr=1, gesamtbetrag=D("13906.34"))])


class Modell:
    def extrahiere_fakten(self, frage, verlauf=None, fallstand=None):
        return _modellantwort()

    def beschreibe_fall(self, kontext):  # pragma: no cover
        return ""


class TestAlltag999(unittest.TestCase):
    def setUp(self):
        self.llm = Modell()
        self.erste = router.bearbeite_frage(FRAGE, self.llm, [])
        self.stand = bestaetigung.SPEICHER.hole_fakten(self.erste.sitzungskennung)

    def _ergebnis(self):
        bestaetigung.SPEICHER.bestaetige(self.erste.sitzungskennung, self.erste.fakten_hash)
        return router.fuehre_nach_bestaetigung_aus(self.erste.sitzungskennung, self.llm)

    def test_b5_keine_rueckfrage(self):
        self.assertEqual(self.erste.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG, self.erste.rueckfragen)
        self.assertEqual(self.stand.verwerterart, "typischer_verwerter")

    def test_soll_4520_und_221_48(self):
        e = self._ergebnis()
        self.assertEqual(e.ergebnisklasse, "Abgabepflichtig (Vorschlag)")
        self.assertEqual(D(str(e.kern_protokoll["bemessungsgrundlage"])), D("4520"))
        self.assertEqual(D(str(e.kern_protokoll["abgabe"])), D("221.48"))

    def test_b1_b2_eigener_name_und_durchleitung_je_position(self):
        direkt = {p.bezeichnung for p in self.stand.positionen if p.vertrag_direkt}
        self.assertEqual(direkt, {"Backing-Vocals Firmenvideo", "Lichtkunst-Installation", "Direktzahlung Komponist"})
        typ = {p.bezeichnung: p.auftragnehmer_typ for p in self.stand.positionen}
        for bez in ("Fotoshooting Messe-Eroeffnung", "Live-Konzert Messebuehne", "Tanzperformance",
                    "Uebersetzung lit.", "Reisekosten Okafor, pauschal", "Ton- und Lichttechnik-Anmietung"):
            self.assertEqual(typ[bez], G, bez)

    def test_b3_lichtkunst_ist_eingeordnet(self):
        self.assertEqual(taetigkeiten.erkenne("Lichtkunst-Installation Messefoyer, Lichtkuenstlerin Mira Ade"), "T-19")
        self.assertEqual(taetigkeiten.gruppe("T-19"), "kuenstlerisch")
        # Ein 'Lichtdesign-Workshop' bleibt Workshop (T-34); offen für den Steuerberater.
        self.assertEqual(taetigkeiten.erkenne("Lichtdesign-Workshop"), "T-34")

    def test_b4_fundstelle_nr_3_nicht_nr_7(self):
        e = self._ergebnis()
        self.assertIn("Nr. 3", e.antwort)
        self.assertNotIn("Satz 1 Nr. 7", e.antwort)

    def test_b6_provision_offen_mit_anderem_betrag(self):
        e = self._ergebnis()
        self.assertIn("Offen: „Vermittlungsprovision Komposition“", e.antwort)
        self.assertEqual(D(str(e.kern_protokoll["abgabe_mit_provision"])), D("245.00"))  # 5.000 € × 4,9 %

    def test_b7_umsatzsteuer_behaelt_ihren_grund(self):
        ust = [p for p in self.stand.positionen if p.rolle == "ust"][0]
        self.assertIsNone(ust.auftragnehmer_typ)
        self.assertNotIn("2.220,34 € (Zahlung an Kapital", self._ergebnis().antwort)

    def test_keine_auslands_oder_belegwarnung(self):
        e = self._ergebnis()
        for wort in ("Ausland", "§ 25 Abs. 4", "Beleg"):
            self.assertNotIn(wort, e.antwort.split("**Rechtsprechung")[0])


class TestVerwerterNummer(unittest.TestCase):
    def test_werbeagentur_bleibt_nr_7(self):
        f = zuordnung.verwerter_aus_auftraggeber("Wir sind eine Werbeagentur.", Fakten(verwerterart="typischer_verwerter"))
        self.assertEqual(f.verwerter_regel, "R-07")

    def test_messestand_eines_handwerkers_ist_keine_messe(self):
        f = zuordnung.verwerter_aus_auftraggeber("Rechnung an: Tischlerei Holz GmbH, für unseren Messestand", Fakten())
        self.assertIsNone(f.verwerter_regel)
        self.assertIsNone(f.verwerterart)

    def test_eigenwerbung_im_text_setzt_keinen_typischen_verwerter(self):
        f = zuordnung.verwerter_aus_auftraggeber("Mein Mandant ist eine Messe GmbH. Es ist Eigenwerbung.", Fakten())
        self.assertIsNone(f.verwerterart)


if __name__ == "__main__":
    unittest.main()


class TestReisekostenRolle(unittest.TestCase):
    """P-30 (live schwankend): nachgewiesene Bahnfahrtkosten ohne Rolle vom Modell."""

    def test_nachgewiesene_bahnfahrt_bekommt_rolle(self):
        text = "3.000 € Honorar gezahlt und zusätzlich 80 € nachgewiesene Bahnfahrtkosten erstattet."
        f = zuordnung.ergaenze_reisekosten_rolle(text, Fakten(positionen=[P(betrag=D("3000")), P(betrag=D("80"))]))
        self.assertEqual([p.rolle for p in f.positionen], [None, "fahrtkosten_nachgewiesen"])

    def test_pauschale_bekommt_keine_rolle(self):
        text = "Reisekosten Okafor, pauschal lt. Vertrag, Belege im Anhang | 336,00 EUR"
        f = zuordnung.ergaenze_reisekosten_rolle(text, Fakten(positionen=[P(betrag=D("336"))]))
        self.assertIsNone(f.positionen[0].rolle)

    def test_ohne_nachweis_keine_rolle(self):
        f = zuordnung.ergaenze_reisekosten_rolle("Fahrtkosten 120 €", Fakten(positionen=[P(betrag=D("120"))]))
        self.assertIsNone(f.positionen[0].rolle)


class TestRestBeiDarin(unittest.TestCase):
    """P-28 (live schwankend): '1.190 € brutto, darin 190 € Umsatzsteuer', Honorar vom Modell mit 1.190 €."""

    def test_ganzer_betrag_wird_zum_rest(self):
        f = Fakten(positionen=[P(betrag=D("1190"), auftragnehmer_nr=1), P(betrag=D("190"), rolle="ust", auftragnehmer_nr=1)],
                   rechnungen=[Rechnung(auftragnehmer_nr=1, gesamtbetrag=D("1190"))])
        text = "einem freien Fotografen 1.190 € brutto gezahlt, darin 190 € Umsatzsteuer gesondert ausgewiesen."
        f = zuordnung.berechne_restpositionen(f, text)
        self.assertEqual([p.betrag for p in f.positionen], [D("1000"), D("190")])
        self.assertFalse(f.widersprueche)

    def test_ohne_darin_bleibt_die_rueckfrage(self):
        f = Fakten(positionen=[P(betrag=D("1190"), auftragnehmer_nr=1), P(betrag=D("190"), auftragnehmer_nr=1)],
                   rechnungen=[Rechnung(auftragnehmer_nr=1, gesamtbetrag=D("1190"))])
        f = zuordnung.berechne_restpositionen(f, "1.190 € und 190 €")
        self.assertTrue(f.widersprueche)


class TestHonorarOhneLeistungsart(unittest.TestCase):
    def test_honorar_des_designers_wird_eingeordnet(self):
        t = ("Unsere Werbeagentur hat 2025 einem freien Designer (Einzelperson) 3.000 € Honorar gezahlt und "
             "zusätzlich 80 € nachgewiesene Bahnfahrtkosten erstattet.")
        f = Fakten(positionen=[P(betrag=D("3000"), bezeichnung="Honorar", rolle="honorar"),
                               P(betrag=D("80"), bezeichnung="nachgewiesene Bahnfahrtkosten", rolle="fahrtkosten_nachgewiesen")])
        self.assertEqual(zuordnung.ergaenze_taetigkeit(t, f).positionen[0].taetigkeit_id, "T-02")
