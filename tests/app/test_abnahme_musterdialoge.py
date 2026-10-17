"""Abnahmetests aus den 5 Musterdialogen (regelwerk/Chatbot_Musterdialoge_Entwurf.md) gegen
den ECHTEN Kern. FakeLLM gibt die Fakten vor, die ein gutes Modell extrahieren wuerde;
`hilfen.lauf_bestaetigt` fuehrt die seit Teil 1d noetige Faktenbestaetigung durch (simuliert
POST /frage + POST /bestaetigen).

Dialoge 1 und 3 weichen weiterhin vom im Musterdialog behaupteten Wortlaut ab, weil die
Schwellen-Tabelle im Regelregister nur 2019-2027 abdeckt -- genau das Beispiel, das
PROMPT_ClaudeCode_Chatbot_1.md selbst nennt. Wie dort vorgegeben: nicht angepasst, sondern
als Befund gemeldet (aufgaben/FUNDE_Chatbot.md, Befund 3). Dialog 4 ist seit Teil 1b
anbindbar (Befund 5 behoben) und liefert ein echtes Kernergebnis."""
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from tests.app.hilfen import lauf_bestaetigt

from app import log, router
from app.ergebnisklassen import ABGABEPFLICHTIG, NICHT_ABGEDECKT, RUECKFRAGE_NOETIG
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position


class TestDialog1EigenwerbungAlteRechtslage2017(unittest.TestCase):
    """Musterdialog behauptet 'Nicht abgabepflichtig' fuer 2017. Tatsaechlich: 'Nicht
    abgedeckt (Quelle fehlt)', da die Schwellen-Tabelle im Regelregister erst ab 2019
    beginnt (kern.rechnen.schwelle(2017) is None). Siehe aufgaben/FUNDE_Chatbot.md, Befund 3."""

    def test_dialog1_tatsaechliches_ergebnis_ist_nicht_abgedeckt(self):
        frage = "Mandant Kanzlei, 2017 einmalig Website, 1.750 € netto an einen freien Webdesigner. Abgabepflichtig?"
        llm = FakeLLM()
        fakten = Fakten(
            jahr=2017, verwerterart="eigenwerber", auftragnehmer_typ="natuerliche_person",
            leistungsart="Grafik/Design", positionen=[Position(betrag=Decimal("1750"))],
        )
        ergebnis = lauf_bestaetigt(llm, frage, fakten)
        self.assertEqual(ergebnis.ergebnisklasse, NICHT_ABGEDECKT)

    def test_dialog1_wird_anonymisiert_im_lueckenprotokoll_vermerkt(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = Path(tmp) / "lueckenprotokoll.jsonl"
            with patch.object(log, "STANDARD_PFAD", pfad):
                frage = "Mandant Kanzlei, 2017 einmalig Website, 1.750 € netto an einen freien Webdesigner."
                llm = FakeLLM()
                fakten = Fakten(
                    jahr=2017, verwerterart="eigenwerber", auftragnehmer_typ="natuerliche_person",
                    leistungsart="Grafik/Design", positionen=[Position(betrag=Decimal("1750"))],
                )
                lauf_bestaetigt(llm, frage, fakten)
                eintraege = log.lies_protokoll(pfad=pfad)
                self.assertEqual(len(eintraege), 1)
                self.assertEqual(eintraege[0]["jahr"], 2017)
                self.assertNotIn("Kanzlei", eintraege[0]["frage_anonymisiert"])


class TestDialog2EigenwerbungNeueRechtslage2024(unittest.TestCase):
    """Entspricht dem Musterdialog: 2024, Eigenwerbung, 1.750 € -> Abgabepflichtig, 87,50 €."""

    def test_dialog2_abgabepflichtig_mit_fundstellen(self):
        frage = "Derselbe Fall, aber 2024."
        llm = FakeLLM()
        fakten = Fakten(
            jahr=2024, verwerterart="eigenwerber", auftragnehmer_typ="natuerliche_person",
            leistungsart="Grafik/Design", positionen=[Position(betrag=Decimal("1750"))],
        )
        ergebnis = lauf_bestaetigt(llm, frage, fakten)
        self.assertEqual(ergebnis.ergebnisklasse, ABGABEPFLICHTIG)
        self.assertEqual(ergebnis.kern_protokoll.get("abgabe"), Decimal("87.50"))
        self.assertTrue(ergebnis.fundstellen, "Fundstellen muessen vorhanden sein")


class TestDialog3Grenzfall2017(unittest.TestCase):
    """Musterdialog behauptet 'Grenzfall' fuer 2017. Tatsaechlich (gleicher Grund wie
    Dialog 1): 'Nicht abgedeckt (Quelle fehlt)'. Siehe aufgaben/FUNDE_Chatbot.md, Befund 3."""

    def test_dialog3_tatsaechliches_ergebnis_ist_nicht_abgedeckt(self):
        frage = "Einmalige Kampagne, 5.000 €, Jahr 2017, Historie unbekannt."
        llm = FakeLLM()
        fakten = Fakten(
            jahr=2017, verwerterart="eigenwerber", auftragnehmer_typ="natuerliche_person",
            leistungsart="Grafik/Design", positionen=[Position(betrag=Decimal("5000"))],
        )
        ergebnis = lauf_bestaetigt(llm, frage, fakten)
        self.assertEqual(ergebnis.ergebnisklasse, NICHT_ABGEDECKT)


class TestDialog4BemessungsgrundlageReisekosten(unittest.TestCase):
    """Befund 5 (behoben): seit Chatbot Teil 1b verdrahtet, ueber Positionen mit
    `rolle='fahrtkosten_nachgewiesen'` (nachgewiesene Reisekosten zaehlen laut kern.rechnen
    nicht zur Bemessungsgrundlage, R-47). Tatsaechliches Ergebnis: Abgabepflichtig,
    Bemessungsgrundlage 3.000 € (ohne die 80 € Reisekosten), Abgabe 150,00 € (Satz 2025: 5 %)."""

    def test_dialog4_bemessungsgrundlage_ohne_nachgewiesene_reisekosten(self):
        frage = "2025, Designer 3.000 € Honorar, 80 € Bahnfahrt nachgewiesen erstattet. Bemessungsgrundlage?"
        llm = FakeLLM()
        fakten = Fakten(
            jahr=2025, verwerterart="eigenwerber", auftragnehmer_typ="natuerliche_person", leistungsart="Grafik/Design",
            positionen=[
                Position(betrag=Decimal("3000"), rolle="honorar"),
                Position(betrag=Decimal("80"), rolle="fahrtkosten_nachgewiesen", nachgewiesen=True),
            ],
        )
        ergebnis = lauf_bestaetigt(llm, frage, fakten)
        self.assertEqual(ergebnis.ergebnisklasse, ABGABEPFLICHTIG)
        self.assertEqual(ergebnis.kern_protokoll.get("bemessungsgrundlage"), Decimal("3000"))
        self.assertEqual(ergebnis.kern_protokoll.get("abgabe"), Decimal("150.00"))


class TestDialog5UrteilNichtInDerBasis(unittest.TestCase):
    """Befund 6 (behoben): `anfrageart='rechtsprechungsfrage'` braucht kein Jahr, keine
    Bestaetigung, und ruft den Kern nicht auf -- sofort 'Nicht abgedeckt (Quelle fehlt)'."""

    def test_dialog5_ohne_jahr_direkt_nicht_abgedeckt(self):
        frage = "Gibt es ein LSG-Urteil zu Podcast-Produktionen?"
        llm = FakeLLM()
        llm.registriere(frage, Fakten(anfrageart="rechtsprechungsfrage", freitext_rest="podcast produktionen"))
        ergebnis = router.bearbeite_frage(frage, llm)
        self.assertEqual(ergebnis.ergebnisklasse, NICHT_ABGEDECKT)
        self.assertNotEqual(ergebnis.ergebnisklasse, RUECKFRAGE_NOETIG)

    def test_dialog5_wird_protokolliert(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = Path(tmp) / "lueckenprotokoll.jsonl"
            with patch.object(log, "STANDARD_PFAD", pfad):
                frage = "Gibt es ein LSG-Urteil zu Podcast-Produktionen?"
                llm = FakeLLM()
                llm.registriere(frage, Fakten(anfrageart="rechtsprechungsfrage", freitext_rest="podcast produktionen"))
                router.bearbeite_frage(frage, llm)
                self.assertEqual(len(log.lies_protokoll(pfad=pfad)), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
