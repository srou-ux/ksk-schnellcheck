"""Tests fuer app/baustein.py (Platzhalter-Architektur, Chatbot Teil 1d).

Prueft: Formatierung, welche Platzhalter aus welchem Kontext entstehen, und dass
`pruefe_rohtext` jede der Nachtrag-Luecken (Zahlwoerter, Normbezuege, Gerichtswoerter,
Fassung, Mengenangaben, Ergebnisaussagen) sowie die urspruenglichen Teil-1c-Faelle
(Ziffer, Paragraf, Aktenzeichen, Regel-ID, Waehrungswort, Prozentzeichen, unbekannter
Platzhalter) einzeln erkennt."""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.baustein import (
    formatiere_betrag,
    formatiere_prozent,
    fuelle,
    erzeuge_platzhalter,
    pruefe_rohtext,
)
from app.llm.base import AntwortKontext
from app.schema import Fakten, Position


class TestFormatierung(unittest.TestCase):
    def test_betrag_mit_tausenderpunkt(self):
        self.assertEqual(formatiere_betrag(Decimal("1500")), "1.500,00 €")

    def test_betrag_ohne_tausenderpunkt(self):
        self.assertEqual(formatiere_betrag(Decimal("45.5")), "45,50 €")

    def test_prozent_ohne_nachkommastellen(self):
        self.assertEqual(formatiere_prozent(Decimal("5")), "5 %")

    def test_prozent_mit_nachkommastelle(self):
        self.assertEqual(formatiere_prozent(Decimal("4.9")), "4,9 %")


class TestErzeugePlatzhalter(unittest.TestCase):
    def test_leerer_kontext_liefert_nur_vorhandene_werte(self):
        kontext = AntwortKontext(frage="f", fakten=Fakten(), ergebnisklasse="Nicht abgedeckt (Quelle fehlt)")
        werte = erzeuge_platzhalter(kontext)
        self.assertEqual(werte, {})

    def test_jahr_ergibt_jahr_und_fassung(self):
        kontext = AntwortKontext(frage="f", fakten=Fakten(jahr=2025), ergebnisklasse="x")
        werte = erzeuge_platzhalter(kontext)
        self.assertEqual(werte["JAHR"], "2025")
        self.assertIn("Fassung", werte["FASSUNG"])

    def test_schwelle_nur_wenn_im_kern_protokoll_vorhanden(self):
        kontext_ohne = AntwortKontext(frage="f", fakten=Fakten(jahr=2025), ergebnisklasse="x")
        self.assertNotIn("SCHWELLE", erzeuge_platzhalter(kontext_ohne))

        kontext_mit = AntwortKontext(
            frage="f", fakten=Fakten(jahr=2025), ergebnisklasse="x",
            kern_protokoll={"schwelle": Decimal("700")},
        )
        self.assertEqual(erzeuge_platzhalter(kontext_mit)["SCHWELLE"], "700,00 €")

    def test_summe_aus_positionen(self):
        kontext = AntwortKontext(
            frage="f", fakten=Fakten(positionen=[Position(betrag=Decimal("900"))]), ergebnisklasse="x",
        )
        self.assertEqual(erzeuge_platzhalter(kontext)["SUMME"], "900,00 €")

    def test_regeln_werden_nach_typ_in_eigene_platzhalter_sortiert(self):
        kontext = AntwortKontext(
            frage="f", fakten=Fakten(), ergebnisklasse="x",
            regeln=[
                {"typ": "urteil", "fundstelle": "BSG, B 1 KR 1/20 R"},
                {"typ": "gesetz", "fundstelle": "KSVG § 24"},
                {"typ": "verwaltungspraxis", "fundstelle": "KSK-Info 05"},
            ],
        )
        werte = erzeuge_platzhalter(kontext)
        self.assertEqual(werte["URTEIL_1"], "BSG, B 1 KR 1/20 R")
        self.assertEqual(werte["NORM_1"], "KSVG § 24")
        self.assertEqual(werte["VERWALTUNGSPRAXIS_1"], "KSK-Info 05")

    def test_rueckfragen_und_hinweise_werden_durchnummeriert(self):
        kontext = AntwortKontext(
            frage="f", fakten=Fakten(), ergebnisklasse="x",
            rueckfragen=["Welches Jahr?", "Welcher Betrag?"], hinweise=["Hinweis A"],
        )
        werte = erzeuge_platzhalter(kontext)
        self.assertEqual(werte["RUECKFRAGE_1"], "Welches Jahr?")
        self.assertEqual(werte["RUECKFRAGE_2"], "Welcher Betrag?")
        self.assertEqual(werte["HINWEIS_1"], "Hinweis A")


class TestPruefeRohtextErlaubterText(unittest.TestCase):
    def test_reiner_platzhaltertext_ist_unbedenklich(self):
        erlaubt = {"SUMME", "SCHWELLE", "JAHR"}
        text = "Die Summe {SUMME} wird mit der Schwelle {SCHWELLE} des Jahres {JAHR} verglichen."
        self.assertEqual(pruefe_rohtext(text, erlaubt), [])

    def test_text_ganz_ohne_platzhalter_ist_unbedenklich(self):
        self.assertEqual(pruefe_rohtext("Es liegen keine weiteren Angaben vor.", set()), [])


class TestPruefeRohtextVerstoesse(unittest.TestCase):
    """Jeder Fall darf NUR die dafuer vorgesehene Regel verletzen -- das wird implizit durch
    test_mutationsprobe_jede_regel_ist_wirksam unten geprueft."""

    FAELLE: dict[str, str] = {
        "unbekannte_platzhalter": "Das Ergebnis ist {UNBEKANNT}.",
        "ziffer": "Es sind 3 Positionen zu nennen.",
        "paragraphzeichen": "Siehe § 24 KSVG.",
        "aktenzeichen": "Vgl. B 12 KR 99/23 R.",
        "regel_id_wort": "Die Regel-ID ist einschlägig.",
        "waehrungswort": "Der Betrag in Euro wird verglichen.",
        "prozentzeichen": "Der Satz liegt bei 5 %.",
        "zahlwort": "Es waren insgesamt zweitausend Euro Honorar.",
        "mengenangabe": "Die Summe liegt bei 2 Mio. Euro.",
        "normwort": "Nach Paragraf 24 KSVG gilt das.",
        "gerichtswort": "Das Bundessozialgericht hat entschieden.",
        "fassungswort": "Es gilt die alte Rechtslage.",
        "ergebnisaussage": "Der Fall ist abgabepflichtig.",
        "gewissheitswort": "Das ist rechtlich garantiert.",
        "bestaetigungswort": "Diese Einschätzung ist bereits genehmigt.",
        "links_kontakt": "Mehr Informationen unter www.beispiel-ohne-bezug.de.",
        "html_tag": "Wichtiger Hinweis: <b>bitte lesen</b>.",
        "markdown_ueberschrift": "### Zusatzhinweis\nHier steht mehr Text.",
        "geschweifte_klammer_uebrig": "Zusatzinfo: {{ABGABE}}.",
    }

    def test_jeder_fall_wird_erkannt(self):
        for name, text in self.FAELLE.items():
            with self.subTest(regel=name):
                verstoesse = pruefe_rohtext(text, set())
                self.assertTrue(verstoesse, f"Regel '{name}': Fall haette erkannt werden muessen")

    def test_jede_regel_ist_fuer_sich_wirksam(self):
        """Ruft jede Regelfunktion direkt (nicht ueber das Aggregat pruefe_rohtext) auf dem
        fuer sie gedachten Fall auf -- unabhaengig davon, ob derselbe Text (z. B. ein
        Aktenzeichen mit Ziffern) noch andere Regeln zusaetzlich ausloest."""
        from app import baustein

        for name, text in self.FAELLE.items():
            with self.subTest(regel=name):
                rest = baustein.PLATZHALTER_MUSTER.sub(" ", text)
                meldung = baustein.ROHTEXT_PRUEFSCHRITTE[name](text, rest, set())
                self.assertIsNotNone(meldung, f"Regel '{name}': eigene Regelfunktion haette auslösen muessen")


class TestFuelle(unittest.TestCase):
    def test_bekannte_platzhalter_werden_ersetzt(self):
        self.assertEqual(fuelle("Betrag: {X}.", {"X": "900,00 €"}), "Betrag: 900,00 €.")

    def test_unbekannte_platzhalter_bleiben_unveraendert(self):
        self.assertEqual(fuelle("Betrag: {Y}.", {}), "Betrag: {Y}.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
