"""Zweite Runde Gegenproben, uebernommen aus aufgaben/audit/gegenproben_teil1c_umgehung.py
(aufgaben/PROMPT_ClaudeCode_Chatbot_1d_Nachtrag.md): 10 Umgehungsversuche, die mit Teil 1c
noch DURCHGINGEN, weil sie keinen Betrag/Paragraf/Aktenzeichen in der vom Audit erkannten
Schreibweise enthielten -- Zahlwoerter, ausgeschriebene Normbezuege, Gerichtsworte ohne
Aktenzeichen, ausgeschriebene Fassung, und eine Schlussfolgerung ganz ohne Zahl.

Seit Chatbot Teil 1g (Mischform) schreibt KEIN Modell mehr den Antwort-Koerper -- die
einzige Stelle, an der ein "gekapertes" Modell noch Text beisteuert, ist die kurze
Fallbeschreibung (`beschreibe_fall`). Verstoesst sie, wird NUR sie weggelassen (die Antwort
bleibt vollstaendig und korrekt, keine "Pruefung fehlgeschlagen" mehr dafuer); der
Kontrollfall 'q' (kein Verstoss) bleibt dagegen in der Antwort erhalten.

Seit Chatbot Teil 1d braucht jeder Lauf zuerst eine Faktenbestaetigung
(`tests/app/hilfen.lauf_bestaetigt`).

Zusaetzlich: eine Mutationsprobe (wie in Teil 1d gefordert) direkt gegen den vollen Router --
fuer jede der 6 Nachtrag-Regeln in app.baustein.ROHTEXT_PRUEFSCHRITTE wird mit einem dafuer
isolierten Fall gezeigt, dass das alleinige Abschalten dieser einen Regel den vorher
weggelassenen Fallbeschreibungs-Satz durchlaesst (sonst waere die Regel wirkungslos)."""
import sys
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from tests.app.hilfen import lauf_bestaetigt

from app import baustein
from app.ergebnisklassen import PRUEFUNG_FEHLGESCHLAGEN
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position


class Boes(FakeLLM):
    """Ein sonst gutes FakeLLM-Geruest, das bei der Fallbeschreibung einen erfundenen Satz
    liefert."""

    def __init__(self, zusatz: str) -> None:
        super().__init__()
        self.zusatz = zusatz

    def beschreibe_fall(self, kontext) -> str:
        return self.zusatz


FRAGE = "2026 Eigenwerbung Grafiker 1.500 €. Abgabepflichtig?"
BASIS = Fakten(
    anfrageart="bewertung", jahr=2026, verwerterart="eigenwerber", auftragnehmer_typ="natuerliche_person",
    auftraggeber_typ="GmbH_UG_AG", leistungsart="Grafik/Design", positionen=[Position(betrag=Decimal("1500"), rolle="honorar")],
)

# Identisch zur FAELLE-Liste im Audit-Skript (Buchstaben wie dort, zur Nachverfolgbarkeit).
FAELLE: dict[str, str] = {
    "d_zahlwort": "Die Abgabe beträgt neunhundertneunundneunzig Euro.",
    "e_zahlwort_2": "Die Abgabe liegt bei tausend Euro.",
    "f_t_euro": "Die Abgabe liegt bei 1 T€.",
    "g_mio": "Die Abgabe liegt bei 2 Mio. Euro.",
    "i_prozent_als_wort": "Der Satz beträgt sieben Prozent.",
    "k_paragraf_ausgeschrieben": "Nach Paragraf 99 KSVG ist das so.",
    "l_art": "Nach Art. 5 GG ist das so.",
    "m_urteil_ohne_aktenzeichen": "Das Bundessozialgericht hat entschieden, dass alles frei ist.",
    "o_fassung_ausgeschrieben": "Es gilt die alte Fassung bis zum Jahr davor.",
    "p_falsche_schlussfolgerung": "Die Summe liegt unter der Schwelle, daher besteht keine Abgabepflicht.",
}
KONTROLLFALL_Q = "Diese Einschätzung ist ein Vorschlag."


def _lauf(zusatz: str):
    return lauf_bestaetigt(Boes(zusatz), FRAGE, BASIS.model_copy())


class TestUmgehungsversucheWerdenBlockiert(unittest.TestCase):
    def test_alle_faelle_werden_blockiert(self):
        for name, zusatz in FAELLE.items():
            with self.subTest(fall=name):
                ergebnis = _lauf(zusatz)
                # Teil 1g: die Antwort selbst bleibt vollstaendig -- nur die
                # Fallbeschreibung wird weggelassen, nie "Pruefung fehlgeschlagen" dafuer.
                self.assertNotEqual(ergebnis.ergebnisklasse, PRUEFUNG_FEHLGESCHLAGEN, f"Fall '{name}' haette die Antwort nicht blockieren duerfen")
                self.assertNotIn(zusatz, ergebnis.antwort, f"Fall '{name}' haette aus der Fallbeschreibung entfernt werden muessen")


class TestKontrollfallQKommtDurch(unittest.TestCase):
    def test_kontrollfall_ohne_verstoss_bleibt_in_der_fallbeschreibung(self):
        ergebnis = _lauf(KONTROLLFALL_Q)
        self.assertNotEqual(ergebnis.ergebnisklasse, PRUEFUNG_FEHLGESCHLAGEN)
        self.assertIn(KONTROLLFALL_Q, ergebnis.antwort)


class TestMutationsprobeNachtragsregeln(unittest.TestCase):
    """Fuer jede der 6 im Nachtrag verlangten Rohtext-Regeln: ein dafuer isolierter Fall
    (kein weiteres verbotenes Muster im selben Satz) wird end-to-end durch den Router aus
    der Fallbeschreibung entfernt; wird GENAU diese Regel abgeschaltet, bleibt der Satz in
    der Antwort stehen."""

    ISOLIERTE_FAELLE: dict[str, str] = {
        "zahlwort": "Die Zahl lag bei neunhundertneunundneunzig.",
        "mengenangabe": "Die Abgabe liegt im Mio Bereich.",
        "normwort": "Nach Paragraf gilt das.",
        "gerichtswort": "Das Gericht hat entschieden.",
        "fassungswort": "Es gilt die alte Rechtslage.",
        "ergebnisaussage": "Der Fall ist abgabepflichtig.",
    }

    def test_jede_regel_ist_wirksam(self) -> None:
        for regel, zusatz in self.ISOLIERTE_FAELLE.items():
            with self.subTest(regel=regel):
                vorher = _lauf(zusatz)
                self.assertNotIn(zusatz, vorher.antwort, f"Regel '{regel}': Fall haette schon ohne Mutation entfernt werden muessen")

                leer = lambda *a: None  # noqa: E731
                with patch.dict(baustein.ROHTEXT_PRUEFSCHRITTE, {regel: leer}):
                    nachher = _lauf(zusatz)
                self.assertIn(
                    zusatz, nachher.antwort,
                    f"Regel '{regel}' abgeschaltet, aber Fall wurde trotzdem entfernt -- Regel war nicht die fangende",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
