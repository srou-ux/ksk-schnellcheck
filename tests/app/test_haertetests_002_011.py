"""Härtetest-Serie HT-2026-002 bis 011 des Nutzers (14.10.2026) mit den echten Modellantworten.

Die Fragen stehen im eigenen Katalog aufgaben/audit/haertetests_ht_2026_002_011.json (nicht im Testarchiv:
die Soll-Werte sind Entwurf und noch nicht vom Steuerberater freigegeben). Die Modellantworten stammen aus dem
Lauf 38641137620 (tests/app/daten_haertetests_002_011.json) und sind unverändert.

Geprüft wird das SICHERE Verhalten, nicht ein bestimmter Wortlaut:
- mehrere Zahlungsjahre in einer Nachricht werden nie zusammengezählt (KSVG § 25 Abs. 1, R-20);
- ein Rechtsformwechsel wird nicht still zu einem Unternehmer zusammengefasst;
- offene Beträge (Gutschrift, unbezahlt, Durchleitung, Provision) zählen nie still mit und tragen ihren Grund;
- Sachleistungen und nebenberufliche Künstler zählen (R-41, R-174, R-26) -- HT-009;
- die Prompt-Injection in HT-011 ändert die Bewertung nicht.
"""
from __future__ import annotations

import json
import unittest
from decimal import Decimal as D
from pathlib import Path

from app import bestaetigung, router, zuordnung
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position as P

W = Path(__file__).resolve().parents[2]
KATALOG = {f["id"]: f for f in json.loads(
    (W / "aufgaben/audit/haertetests_ht_2026_002_011.json").read_text(encoding="utf-8"))["faelle"]}
DATEN = json.loads((W / "tests/app/daten_haertetests_002_011.json").read_text(encoding="utf-8"))["faelle"]
KNOPF = {"Typischer Verwerter": "typischer_verwerter", "Eigenwerbung": "eigenwerber",
         "natürliche Person": "natuerliche_person"}


def _lauf(fid: str, roh: dict):
    f = KATALOG[fid]
    roh = dict(roh)
    for feld, wert in f.get("knoepfe", {}).items():
        roh.setdefault(feld, KNOPF[wert])
    llm = FakeLLM()
    llm.registriere(f["frage"], Fakten.model_validate(roh))
    a = router.bearbeite_frage(f["frage"], llm)
    if a.ergebnisklasse != "Faktenbestätigung nötig":
        return a, None
    bestaetigung.SPEICHER.bestaetige(a.sitzungskennung, a.fakten_hash)
    return a, router.fuehre_nach_bestaetigung_aus(a.sitzungskennung, FakeLLM())


class MehrereZahlungsjahre(unittest.TestCase):
    def test_jahre_aus_dem_text(self):
        erwartet = {"HT-2026-002": {2020, 2026}, "HT-2026-005": {2026}, "HT-2026-006": {2024, 2025, 2026},
                    "HT-2026-008": {2025, 2026}, "HT-2026-010": {2019, 2020, 2021, 2022}, "HT-2026-011": {2026}}
        for fid, jahre in erwartet.items():
            with self.subTest(fall=fid):
                self.assertEqual(zuordnung.zahlungsjahre_im_text(KATALOG[fid]["frage"]), jahre)

    def test_rechnungsdatum_ist_kein_zahlungsjahr(self):
        # HT-2026-001: Rechnung vom 27.12.2025, abgebucht am 09.01.2026 -> nur 2026, keine Rückfrage.
        text = ("Rechnung AT-2026-0141 vom 27.12.2025 über 2.400 US-Dollar, Zahlung ist am 09.01.2026 abgebucht "
                "mit 2.210,00 €.")
        self.assertEqual(zuordnung.zahlungsjahre_im_text(text), {2026})

    def test_ht_085_zahlungsjahr_statt_rechnungsjahr(self):
        # Fehlerquellen-Serie HT-2026-085: Rechnung 2025, bezahlt 2026 -> 2026 (R-20), als abgeleitet gekennzeichnet.
        text = ("Wir sind eine Werbeagentur. Rechnung vom 15.12.2025 ueber 3.000 EUR an einen freien Kuenstler "
                "(Einzelperson, Illustration), bezahlt am 10.01.2026.")
        for modelljahr in (None, 2025):
            with self.subTest(modelljahr=modelljahr):
                f = zuordnung.jahr_aus_rechnungsdaten(text, Fakten(jahr=modelljahr))
                self.assertEqual(f.jahr, 2026)
                self.assertTrue(f.jahr_aus_rechnungsdaten)

    def test_ausdruecklich_genanntes_jahr_bleibt(self):
        # Steht das Jahr frei im Text ('2025 haben wir ...'), wird es nicht still ersetzt.
        f = zuordnung.jahr_aus_rechnungsdaten("2025 haben wir die Rechnung vom 15.12.2025 erhalten, bezahlt am 10.01.2026 "
                                              "mit 3.000 EUR.", Fakten(jahr=2025))
        self.assertEqual(f.jahr, 2025)

    def test_freies_jahr_neben_zahlungsdatum(self):
        self.assertEqual(zuordnung.zahlungsjahre_im_text(
            "Im Jahr 2025 Rechnung vom 15.12.2025 ueber 3.000 EUR, bezahlt am 10.01.2026."), {2026})

    def test_betrag_ist_kein_jahr(self):
        self.assertEqual(zuordnung.zahlungsjahre_im_text("Wir haben 2026 einmal 2020 € gezahlt."), {2026})

    def test_echte_modellantworten_werden_nicht_zusammengezaehlt(self):
        for fid in ("HT-2026-002", "HT-2026-006", "HT-2026-008", "HT-2026-010"):
            for nr, roh in enumerate(DATEN[fid]):
                with self.subTest(fall=fid, antwort=nr):
                    a, c = _lauf(fid, roh)
                    self.assertIsNone(c, "darf nicht bis zur Rechnung kommen")
                    self.assertEqual(a.ergebnisklasse, "Rückfrage nötig")
                    self.assertIn("mehreren Kalenderjahren", a.rueckfragen[0])


class Rechtsformwechsel(unittest.TestCase):
    def test_erkannt(self):
        f = zuordnung.markiere_rechtsformwechsel(KATALOG["HT-2026-008"]["frage"], Fakten())
        self.assertTrue(f.rechtsformwechsel)

    def test_nicht_ohne_wechsel(self):
        self.assertIsNone(zuordnung.markiere_rechtsformwechsel(KATALOG["HT-2026-011"]["frage"], Fakten()).rechtsformwechsel)

    def test_rueckfrage(self):
        from app import pflichtangaben
        f = Fakten(jahr=2026, rechtsformwechsel=True, positionen=[P(betrag=D("100"))])
        self.assertEqual(pflichtangaben.fehlende_pflichtangaben(f), [pflichtangaben.FRAGE_RECHTSFORMWECHSEL])

    def test_modell_darf_das_feld_nicht_setzen(self):
        f = zuordnung.ohne_systemfelder(Fakten(rechtsformwechsel=True, mehrere_zahlungsjahre="2025, 2026",
                                               positionen=[P(betrag=D("1"), offen_grund="x")]))
        self.assertIsNone(f.rechtsformwechsel)
        self.assertIsNone(f.mehrere_zahlungsjahre)
        self.assertIsNone(f.positionen[0].offen_grund)


class OffeneBetraegeMitGrund(unittest.TestCase):
    def test_ht_004(self):
        f = Fakten(positionen=[P(betrag=D(b)) for b in ("3500", "3000", "500", "600")])
        f = zuordnung.zahlungsweg_im_freitext(KATALOG["HT-2026-004"]["frage"], f)
        gruende = {str(p.betrag): p.offen_grund for p in f.positionen}
        self.assertTrue(all(p.zahlungsweg_unklar for p in f.positionen))
        self.assertIn("Gutschrift", gruende["500"])
        self.assertIn("Vermittlungsprovision", gruende["600"])
        self.assertIn("keine Zahlung", gruende["3000"])

    def test_ht_005_unbezahlt(self):
        f = Fakten(positionen=[P(betrag=D("5287.50")), P(betrag=D("912.40")), P(betrag=D("915.80")), P(betrag=D("800"))])
        f = zuordnung.zahlungsweg_im_freitext(KATALOG["HT-2026-005"]["frage"], f)
        self.assertEqual([p.zahlungsweg_unklar for p in f.positionen], [None, None, None, True])
        self.assertIn("noch nicht bezahlt", f.positionen[3].offen_grund)

    def test_ht_001_bleibt(self):
        # Durchleitung und Erstattung (HT-2026-001) behalten ihre Markierung, jetzt mit Grund.
        text = ("an die Band 1.150 € direkt gezahlt – aber eigentlich hat unser Kunde die Band gebucht, wir haben nur "
                "vermittelt und das Geld durchgeleitet. Und unser Managing Director hat noch 400 € an einen Zauberer "
                "gezahlt, privat von seinem Konto, ob wir das erstatten müssen weiß ich noch nicht.")
        f = zuordnung.zahlungsweg_im_freitext(text, Fakten(positionen=[P(betrag=D("1150")), P(betrag=D("400"))]))
        self.assertIn("Durchleitung", f.positionen[0].offen_grund)
        self.assertIn("Erstattung offen", f.positionen[1].offen_grund)

    def test_ht_004_005_nie_still_abgabepflichtig(self):
        for fid in ("HT-2026-004", "HT-2026-005"):
            for nr, roh in enumerate(DATEN[fid]):
                with self.subTest(fall=fid, antwort=nr):
                    a, c = _lauf(fid, roh)
                    ende = c or a
                    self.assertNotEqual(ende.ergebnisklasse, "Abgabepflichtig (Vorschlag)")
                    self.assertNotEqual(ende.ergebnisklasse, "Nicht abgabepflichtig (Vorschlag)")


class SachleistungUndNebenberuf(unittest.TestCase):
    """HT-2026-009: Gutschein statt Honorar (Sachleistung, R-41/R-174) und Student nebenbei (R-26) zählen. Die
    Werte wie angegeben ergeben 2.050 € × 4,9 % = 100,45 € (Fachprüfung des Nutzers, Variante 'alle drei')."""

    def test_echte_modellantworten(self):
        for nr, roh in enumerate(DATEN["HT-2026-009"]):
            with self.subTest(antwort=nr):
                _, c = _lauf("HT-2026-009", roh)
                self.assertIsNotNone(c)
                self.assertEqual(c.ergebnisklasse, "Abgabepflichtig (Vorschlag)")
                self.assertEqual(c.kern_protokoll.get("abgabe"), D("100.45"))


class PromptInjection(unittest.TestCase):
    """HT-2026-011: die eingeschleuste Anweisung ändert nichts; 3.400 € × 4,9 % = 166,60 €."""

    def test_echte_modellantworten(self):
        for nr, roh in enumerate(DATEN["HT-2026-011"]):
            with self.subTest(antwort=nr):
                a, c = _lauf("HT-2026-011", roh)
                self.assertIsNotNone(c, a.rueckfragen)
                self.assertEqual(c.ergebnisklasse, "Abgabepflichtig (Vorschlag)")
                self.assertEqual(c.kern_protokoll.get("abgabe"), D("166.60"))
                for verboten in KATALOG["HT-2026-011"]["verboten_text"]:
                    self.assertNotIn(verboten, c.antwort)

    def test_selbstbeschreibung_ist_keine_rechtsform_des_autors(self):
        from app.rechtsform_erkennung import erkenne_rechtsform_auftragnehmer
        self.assertIsNone(erkenne_rechtsform_auftragnehmer(
            "Hallo, wir sind ein Verlag (GmbH) und haben 2026 an einen Autor 3.400 EUR gezahlt."))
        self.assertIsNotNone(erkenne_rechtsform_auftragnehmer("Wir haben der Klangwerk GmbH 1.200 EUR gezahlt."))


class NieStillEntschieden(unittest.TestCase):
    """HT-2026-003 und 007: Art des Auftraggebers (Verwerter oder Generalklausel) und Schülerzahl -- erst fragen."""

    def test_echte_modellantworten(self):
        for fid in ("HT-2026-003", "HT-2026-007"):
            for nr, roh in enumerate(DATEN[fid]):
                with self.subTest(fall=fid, antwort=nr):
                    a, c = _lauf(fid, roh)
                    ende = c or a
                    self.assertNotEqual(ende.ergebnisklasse, "Abgabepflichtig (Vorschlag)")


if __name__ == "__main__":
    unittest.main()
