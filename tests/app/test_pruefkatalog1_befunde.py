"""Tests zu aufgaben/PROMPT_ClaudeCode_Chatbot_Pruefkatalog1_Befunde.md (Befunde aus dem
ersten Prüfkatalog-Lauf mit Mistral, 10.10.2026): M1 (geschlossene Rückfrage deterministisch
per Knopf beantworten, Sitzungswerte gehen nicht verloren), M3 (typischer Verwerter hat
Vorrang vor Eigenwerbung), M4 (verwerterart gegen den Nutzertext prüfen). M2 (Mistral-
Codeblock/response_format) ist in tests/app/test_mistral_rauchtest.py getestet."""
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app import bestaetigung, pflichtangaben, router, zuordnung
from app.ergebnisklassen import (
    ABGABEPFLICHTIG,
    FAKTEN_BESTAETIGUNG_NOETIG,
    NICHT_ABGABEPFLICHTIG,
    RUECKFRAGE_NOETIG,
)
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position as P
from tests.app.zweck_knopf import mit_zweck  # Entscheidung 17.10.2026: geratener Zweck wird per Knopf bestätigt

NP = "natuerliche_person"


class KeinVerwerterartModell(FakeLLM):
    """Testdoppel (Pruefkatalog-Befund M1, Soll Punkt 4): verhaelt sich wie FakeLLM, setzt
    aber NIE `verwerterart` -- wie ein Sprachmodell, das diese Einstufung laut Systemprompt
    nicht selbst vornehmen darf (app/llm/mistral.py, _SYSTEM_EXTRAKTION)."""

    def extrahiere_fakten(self, frage, verlauf=None):
        fakten = super().extrahiere_fakten(frage, verlauf)
        return fakten.model_copy(update={"verwerterart": None})


# ==========================================================================================
# M1: Dialog Frage -> Rueckfrage -> Knopf -> Faktenbestaetigung (-> Ergebnis).
# ==========================================================================================
class TestM1KnopfBeantwortetVerwerterart(unittest.TestCase):
    def test_dialog_frage_rueckfrage_knopf_faktenbestaetigung_ergebnis(self):
        llm = KeinVerwerterartModell()
        frage = "2026, freiberuflicher Grafiker, 900 €."

        erste = router.bearbeite_frage(frage, llm)
        self.assertEqual(erste.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertTrue(erste.sitzungskennung)
        self.assertEqual(erste.rueckfragen, [pflichtangaben.FRAGE_VERWERTERART])

        optionen = {o["frage"]: o for o in erste.rueckfrage_optionen}
        self.assertIn(pflichtangaben.FRAGE_VERWERTERART, optionen)
        eintrag = optionen[pflichtangaben.FRAGE_VERWERTERART]
        # Schritt 2 (17.10.2026): der Knopf nennt die Tatsache (Zweck), nicht mehr die Kategorie „Eigenwerbung“;
        # das Ergebnis des Dialogs bleibt dasselbe (Einordnung Eigenwerbung durch das System).
        self.assertEqual(eintrag["feld"], "auftragszweck")
        self.assertNotIn("position", eintrag)
        wert = eintrag["werte"]["Werbung für mein eigenes Unternehmen"]
        self.assertEqual(wert, "eigene_werbung")

        zweite = router.wende_feldantwort_an(erste.sitzungskennung, eintrag["feld"], wert, llm)
        self.assertEqual(zweite.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG)
        self.assertEqual(zweite.sitzungskennung, erste.sitzungskennung)
        self.assertTrue(any("Eigenwerbung" in z for z in zweite.fakten_zusammenfassung))

        bestaetigung.SPEICHER.bestaetige(zweite.sitzungskennung, zweite.fakten_hash)
        ergebnis = router.fuehre_nach_bestaetigung_aus(zweite.sitzungskennung, llm)
        self.assertEqual(ergebnis.ergebnisklasse, NICHT_ABGABEPFLICHTIG)  # 900 <= 1.000 (2026)

    def test_knopf_beantwortet_rechtsform_je_position(self):
        llm = FakeLLM()
        frage = "2026 Honorar 900 € für ein Logo."
        llm.registriere(
            frage,
            Fakten(jahr=2026, verwerterart="eigenwerber", positionen=[P(betrag=D("900"), rolle="honorar")]),
        )

        # Der Text nennt den Zweck nicht: erst bestätigt der Nutzer ihn (Entscheidung 17.10.2026), dann die Rechtsform.
        erste = mit_zweck(router.bearbeite_frage(frage, llm), "eigenwerber", llm)
        self.assertEqual(erste.ergebnisklasse, RUECKFRAGE_NOETIG)
        eintrag = erste.rueckfrage_optionen[0]
        self.assertEqual(eintrag["feld"], "auftragnehmer_typ")
        self.assertEqual(eintrag["position"], 0)
        wert = eintrag["werte"]["natürliche Person"]
        self.assertEqual(wert, "natuerliche_person")

        zweite = router.wende_feldantwort_an(erste.sitzungskennung, eintrag["feld"], wert, llm, eintrag["position"])
        self.assertEqual(zweite.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG)

    def test_knopf_beantwortet_einnahmeabsicht_ja_nein(self):
        llm = FakeLLM()
        frage = "2025, vier Konzerte, Summe 2000 €."
        llm.registriere(
            frage,
            Fakten(
                jahr=2025, verwerterart="generalklausel", auftragnehmer_typ=NP,
                positionen=[P(betrag=D("2000"))], veranstaltungszahl=4,
            ),
        )
        erste = router.bearbeite_frage(frage, llm)
        self.assertEqual(erste.ergebnisklasse, RUECKFRAGE_NOETIG)
        eintrag = erste.rueckfrage_optionen[0]
        self.assertEqual(eintrag["feld"], "einnahmeabsicht")
        self.assertEqual(eintrag["werte"]["ja"], True)
        self.assertEqual(eintrag["werte"]["nein"], False)

        zweite = router.wende_feldantwort_an(erste.sitzungskennung, "einnahmeabsicht", True, llm)
        self.assertEqual(zweite.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG)
        self.assertTrue(any("Einnahmeabsicht: ja" in z for z in zweite.fakten_zusammenfassung))

    def test_knopf_zu_unbekannter_sitzung_bricht_nicht_ab(self):
        ergebnis = router.wende_feldantwort_an("unbekannte-sitzung", "verwerterart", "eigenwerber", FakeLLM())
        self.assertEqual(ergebnis.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertIn(router.UNBEKANNTE_SITZUNG_RUECKFRAGE, ergebnis.rueckfragen)

    def test_knopf_mit_unpassendem_wert_bricht_nicht_ab(self):
        llm = FakeLLM()
        frage = "2026, 900 € Honorar."
        llm.registriere(frage, Fakten(jahr=2026, positionen=[P(betrag=D("900"))]))
        erste = router.bearbeite_frage(frage, llm)
        self.assertTrue(erste.sitzungskennung)
        # "jahr" ist kein Literal-Feld -- ein voellig unpassender Rohwert (Liste statt Zahl)
        # darf nicht zum Absturz (500) fuehren, sondern zu einer Rueckfrage.
        ergebnis = router.wende_feldantwort_an(erste.sitzungskennung, "jahr", ["nicht", "plausibel"], llm)
        self.assertEqual(ergebnis.ergebnisklasse, RUECKFRAGE_NOETIG)


class TestM1SitzungswerteGehenNichtVerloren(unittest.TestCase):
    def test_freie_folgenachricht_behaelt_bereits_bekannte_felder(self):
        """Pruefkatalog-Befund M1, Punkt 2: eine freie Folgenachricht (ueber dieselbe
        Sitzung) darf bereits bekannte Felder nicht verlieren, nur weil sie selbst nichts
        Neues dazu liefert."""
        llm = FakeLLM()
        erste_frage = "2026, freiberuflicher Grafiker, 1.200 €."
        erste = router.bearbeite_frage(erste_frage, llm)
        self.assertEqual(erste.ergebnisklasse, RUECKFRAGE_NOETIG)

        zweite = router.bearbeite_frage("Es ist Eigenwerbung.", llm, sitzungskennung=erste.sitzungskennung)
        self.assertEqual(zweite.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG)
        text = " ".join(zweite.fakten_zusammenfassung)
        self.assertIn("1.200,00", text)
        self.assertIn("natürliche Person", text)
        self.assertIn("Eigenwerbung", text)

    def test_fakten_zusammenfuehren_erhaelt_alten_wert_wenn_neu_nichts_liefert(self):
        alt = Fakten(jahr=2026, verwerterart="eigenwerber", auftragnehmer_typ=NP, positionen=[P(betrag=D("900"))])
        neu = Fakten()
        ergebnis = router._fakten_zusammenfuehren(alt, neu)
        self.assertEqual(ergebnis.jahr, 2026)
        self.assertEqual(ergebnis.verwerterart, "eigenwerber")
        self.assertEqual(len(ergebnis.positionen), 1)

    def test_fakten_zusammenfuehren_neu_ueberschreibt_wenn_vorhanden(self):
        alt = Fakten(jahr=2026, einnahmeabsicht=True)
        neu = Fakten(einnahmeabsicht=False)
        ergebnis = router._fakten_zusammenfuehren(alt, neu)
        self.assertEqual(ergebnis.jahr, 2026)
        self.assertFalse(ergebnis.einnahmeabsicht)


# ==========================================================================================
# M1.3: Rechtsform-Synonyme deterministisch ergaenzen (fuer JEDES Modell, nicht nur FakeLLM).
# ==========================================================================================
class TestM1_3ErgaenzeRechtsform(unittest.TestCase):
    def test_einzelperson_wird_global_ergaenzt_wenn_modell_nichts_setzt(self):
        fakten = Fakten(jahr=2026, positionen=[P(betrag=D("900"))])
        ergebnis = zuordnung.ergaenze_rechtsform("Ein Grafiker (Einzelperson) hat uns 900 € berechnet.", fakten)
        self.assertEqual(ergebnis.positionen[0].auftragnehmer_typ, "natuerliche_person")

    def test_bereits_gesetzte_rechtsform_wird_nicht_ueberschrieben(self):
        fakten = Fakten(jahr=2026, auftragnehmer_typ="GmbH_UG_AG", positionen=[P(betrag=D("900"))])
        ergebnis = zuordnung.ergaenze_rechtsform("Ein Grafiker (Einzelperson) hat uns 900 € berechnet.", fakten)
        self.assertEqual(ergebnis.auftragnehmer_typ, "GmbH_UG_AG")

    def test_bei_mehreren_positionen_wird_nicht_geraten(self):
        fakten = Fakten(jahr=2026, positionen=[P(betrag=D("900")), P(betrag=D("200"))])
        ergebnis = zuordnung.ergaenze_rechtsform("Einzelperson.", fakten)
        self.assertIsNone(ergebnis.positionen[0].auftragnehmer_typ)
        self.assertIsNone(ergebnis.positionen[1].auftragnehmer_typ)


# ==========================================================================================
# M3/M4: verwerterart gegen den Nutzertext pruefen.
# ==========================================================================================
class TestM3TypischerVerwerterHatVorrang(unittest.TestCase):
    def test_verlag_gewinnt_gegen_vom_modell_gelieferte_eigenwerbung(self):
        fakten = Fakten(jahr=2026, verwerterart="eigenwerber", positionen=[P(betrag=D("300"))])
        text = "Wir sind ein Buchverlag und lassen Flyer fuer die eigene Werbung gestalten."
        ergebnis = zuordnung.absichere_verwerterart(text, fakten)
        self.assertEqual(ergebnis.verwerterart, "typischer_verwerter")

    def test_hobbyorchester_ist_kein_typischer_verwerter_kompositum_faelschlich_erkannt(self):
        """Regressionstest (Pruefkatalog-Lauf, Fall P-16): 'orchester' darf nicht als Teil
        von 'Hobbyorchester' faelschlich als typischer Verwerter erkannt werden."""
        fakten = Fakten(jahr=2026, verwerterart="generalklausel", positionen=[P(betrag=D("800"))])
        text = "Unser Hobbyorchester-Verein hatte 2026 vier Konzerte."
        ergebnis = zuordnung.absichere_verwerterart(text, fakten)
        self.assertEqual(ergebnis.verwerterart, "generalklausel")


class TestM4ModellwertGegenTextGeprueft(unittest.TestCase):
    def test_widersprechender_modellwert_wird_verworfen(self):
        """P-04b: Text belegt nur 'eigene Werbung', das Modell sagt aber 'typischer
        Verwerter' -- der Widerspruch fuehrt zum Verwerfen (erneute Nachfrage), nicht zur
        kommentarlosen Uebernahme."""
        fakten = Fakten(jahr=2026, verwerterart="typischer_verwerter", positionen=[P(betrag=D("800"))])
        text = "Ein Grafiker hat uns viermal fuer unsere eigene Werbung Grafiken erstellt."
        ergebnis = zuordnung.absichere_verwerterart(text, fakten)
        self.assertIsNone(ergebnis.verwerterart)

    def test_ohne_jeden_begriff_bleibt_ein_bereits_gesetzter_wert_unangetastet(self):
        fakten = Fakten(jahr=2026, verwerterart="eigenwerber", positionen=[P(betrag=D("800"))])
        ergebnis = zuordnung.absichere_verwerterart("natürliche Person", fakten)
        self.assertEqual(ergebnis.verwerterart, "eigenwerber")


if __name__ == "__main__":
    unittest.main(verbosity=2)
