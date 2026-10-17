"""Chatbot Teil 1f, Nachtrag: uebernimmt jede Zeile aus
aufgaben/audit/abnahme_teil1f_nachtrag.py als Unittest (Abschnitt "Abnahme"). Zusaetzlich
direkte Unit-Tests fuer die neuen Module app/zuordnung.py (Abschnitt A) und fuer
app/router.py::_rueckfrage_antwort (Abschnitt B)."""
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from kern import rechnen as K

from app import bestaetigung, pflichtangaben, router, zuordnung
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position as P

NP = "natuerliche_person"


def voll(frage, fakten, llm=None):
    llm = llm or FakeLLM()
    llm.registriere(frage, fakten)
    a = router.bearbeite_frage(frage, llm)
    if a.sitzungskennung and a.fakten_hash:
        bestaetigung.SPEICHER.bestaetige(a.sitzungskennung, a.fakten_hash)
        a = router.fuehre_nach_bestaetigung_aus(a.sitzungskennung, llm)
    return a


class NurFesteTexte(FakeLLM):
    """Modell, das bei jedem Schreibversuch abstuerzt: Rueckfragen und Hinweise duerfen es
    nie aufrufen (identisch zum Abnahme-Skript)."""

    def formuliere_antwort(self, kontext):
        raise AssertionError("Das Modell darf fuer diese Antwort nicht aufgerufen werden")


# ======================================================================================
# Abschnitt A: Zuordnung der Anfrageart absichern
# ======================================================================================
class TestAbschnittAZuordnungAbsichern(unittest.TestCase):
    def test_a1_auskunft_ohne_thema_bei_einer_rechnungsfrage_keine_auskunfts_rueckfrage(self):
        f = "Wir sind eine Werbeagentur. Im Jahr 2025 haben wir einem freiberuflichen Grafiker 2.400 Euro gezahlt. Ist das abgabepflichtig?"
        a = voll(f, Fakten(anfrageart="auskunft", jahr=2025, positionen=[P(betrag=D("2400"), rolle="honorar")]))
        self.assertNotIn("Auskunft", a.antwort)
        self.assertNotIn("Worüber", a.antwort)

    def test_a2_erfundenes_auskunftsthema_frage_nennt_keinen_abgabesatz(self):
        f = "Ist ein Auftrag an einen Texter abgabepflichtig?"
        a = voll(f, Fakten(anfrageart="auskunft", jahr=2025, auskunft_thema="abgabesatz"))
        self.assertNotIn("Abgabesatz des Jahres", a.antwort)
        self.assertNotIn("Auskunft aus dem Regelwerk", a.ergebnisklasse)

    def test_a3_hinweis_bei_einer_frage_mit_jahr_und_betrag_keine_begruessung(self):
        f = "Unser Verein hat 2025 vier Konzerte veranstaltet und die Musiker mit zusammen 3.500 Euro bezahlt. Wir wollten Einnahmen erzielen."
        a = voll(f, Fakten(anfrageart="hinweis"))
        self.assertNotIn("Hallo", a.antwort)
        self.assertNotEqual(a.ergebnisklasse, "Hinweis")

    def test_a4_echte_begruessung_bleibt_eine_begruessung(self):
        a = voll("hallo", Fakten(anfrageart="hinweis"))
        self.assertTrue("Hallo" in a.antwort or a.ergebnisklasse == "Hinweis")

    def test_a5_echte_auskunftsfrage_bleibt_eine_auskunft_kontrolle(self):
        f = "Wie hoch ist der Abgabesatz im Jahr 2024?"
        a = voll(f, Fakten(anfrageart="auskunft", jahr=2024, auskunft_thema="abgabesatz"))
        self.assertIn("5", a.antwort)
        self.assertIn("Auskunft", a.ergebnisklasse)

    def test_zuordnung_absichere_anfrageart_direkt_auskunft_verworfen(self):
        fakten = Fakten(anfrageart="auskunft", jahr=2025, auskunft_thema="abgabesatz")
        ergebnis = zuordnung.absichere_anfrageart("Irgendeine Frage ohne Begriff.", fakten)
        self.assertIsNone(ergebnis.anfrageart)
        self.assertIsNone(ergebnis.auskunft_thema)

    def test_zuordnung_absichere_anfrageart_direkt_auskunft_bestaetigt(self):
        fakten = Fakten(anfrageart="auskunft", jahr=2025, auskunft_thema="schwelle")
        ergebnis = zuordnung.absichere_anfrageart("Ab wann gilt die Geringfügigkeitsgrenze?", fakten)
        self.assertEqual(ergebnis.anfrageart, "auskunft")
        self.assertEqual(ergebnis.auskunft_thema, "schwelle")

    def test_zuordnung_absichere_anfrageart_direkt_hinweis_verworfen(self):
        fakten = Fakten(anfrageart="hinweis")
        ergebnis = zuordnung.absichere_anfrageart("2025, 900 Euro Honorar.", fakten)
        self.assertIsNone(ergebnis.anfrageart)

    def test_zuordnung_absichere_anfrageart_direkt_hinweis_bestaetigt(self):
        fakten = Fakten(anfrageart="hinweis")
        ergebnis = zuordnung.absichere_anfrageart("Danke!", fakten)
        self.assertEqual(ergebnis.anfrageart, "hinweis")

    def test_zuordnung_andere_anfragearten_bleiben_unberuehrt(self):
        fakten = Fakten(anfrageart="vorauszahlung", jahr=2025, bemessungsgrundlage_vorjahr=D("24000"))
        ergebnis = zuordnung.absichere_anfrageart("Irgendein Text.", fakten)
        self.assertEqual(ergebnis.anfrageart, "vorauszahlung")


# ======================================================================================
# Abschnitt B: Rueckfragen und Hinweise ohne Modell
# ======================================================================================
class TestAbschnittBRueckfragenOhneModell(unittest.TestCase):
    def test_b1_rueckfrage_kommt_ohne_modellaufruf_zustande(self):
        f = "Wir haben 2025 Honorar gezahlt."
        a = voll(f, Fakten(anfrageart="bewertung", jahr=2025, positionen=[P(betrag=D("900"), rolle="honorar")]), NurFesteTexte())
        self.assertEqual(a.ergebnisklasse, K.RUECKFRAGE)
        self.assertTrue(a.rueckfragen)

    def test_b2_begruessung_ohne_modellaufruf(self):
        a = voll("hallo", Fakten(anfrageart="hinweis"), NurFesteTexte())
        self.assertIn("Hallo", a.antwort)

    def test_b3_rueckfrage_nach_dem_jahr_ohne_modellaufruf(self):
        a = voll("x", Fakten(anfrageart="bewertung"), NurFesteTexte())
        self.assertEqual(a.ergebnisklasse, K.RUECKFRAGE)
        self.assertIn("Kalenderjahr", a.antwort)

    def test_b4_rueckfrage_enthaelt_keinen_vom_modell_erfundenen_satz(self):
        f = "Wir haben 2025 Honorar gezahlt."
        a = voll(f, Fakten(anfrageart="bewertung", jahr=2025, positionen=[P(betrag=D("900"), rolle="honorar")]))
        for wort in ("einmalig", "wiederkehrend", "Fassung B des", "bereits in einem vorherigen"):
            self.assertNotIn(wort, a.antwort)

    def test_rueckfrage_antwort_ist_rein_system_formuliert(self):
        antwort = router._rueckfrage_antwort(["Frage A?", "Frage B?"])
        self.assertEqual(antwort.ergebnisklasse, K.RUECKFRAGE)
        self.assertIn("Frage A?", antwort.antwort)
        self.assertIn("Frage B?", antwort.antwort)
        self.assertIn("Entwurf", antwort.antwort)

    def test_rueckfrage_antwort_einzahl_vs_mehrzahl_einleitung(self):
        einzeln = router._rueckfrage_antwort(["Nur eine Frage?"])
        mehrere = router._rueckfrage_antwort(["Frage A?", "Frage B?"])
        self.assertIn("folgende Angabe:", einzeln.antwort)
        self.assertIn("folgende Angaben:", mehrere.antwort)

    def test_kern_rueckfrage_kommt_auch_ohne_modellaufruf_zustande(self):
        """Nicht nur Pflichtangaben-Rueckfragen, auch eine Rueckfrage aus dem KERN selbst
        (hier: kern.rechnen.uebungsleiter_bg verlangt eine schriftliche Bestaetigung;
        app/pflichtangaben.py prueft das nicht vorab, pruefe_fuellt_pflichtangaben also
        'vollstaendig', aber der Kern antwortet trotzdem mit einer Rueckfrage) darf das
        Modell nicht aufrufen."""
        f = "Übungsleiterhonorar 3.000 €, 2025, keine schriftliche Bestätigung."
        fakten = Fakten(
            anfrageart="uebungsleiter_pauschale", jahr=2025, pauschale_art="uebungsleiter",
            pauschale_bestaetigung=False, positionen=[P(betrag=D("3000"), rolle="honorar")],
        )
        self.assertEqual(pflichtangaben.fehlende_pflichtangaben(fakten), [])
        a = voll(f, fakten, NurFesteTexte())
        self.assertEqual(a.ergebnisklasse, K.RUECKFRAGE)
        self.assertTrue(a.rueckfragen)


# ======================================================================================
# Abschnitt C: Rueckfrage nur nach dem, was der Kern braucht
# ======================================================================================
class TestAbschnittCRueckfrageNurNachKernbedarf(unittest.TestCase):
    def test_c1_rechtsform_rueckfrage_nur_fuer_honorar_position(self):
        f = "Ein selbständiger Fotograf hat uns 2024 insgesamt 1.800 Euro berechnet, darin sind 300 Euro nachgewiesene Fahrtkosten."
        a = voll(f, Fakten(anfrageart="bewertung", jahr=2024, positionen=[
            P(betrag=D("1500"), rolle="honorar", bezeichnung="Fotografie"),
            P(betrag=D("300"), rolle="fahrtkosten_nachgewiesen", bezeichnung="Fahrtkosten", nachgewiesen=True),
        ]))
        n = sum(1 for r in a.rueckfragen if "Rechtsform" in r)
        self.assertLessEqual(n, 1)
        self.assertFalse(any("Fahrtkosten" in r for r in a.rueckfragen))

    def test_c2_gemischte_positionen_bekannte_rechtsform_rechnet_ohne_leistungsart_rueckfrage(self):
        f = "2025: Grafiker 2.400, Texterin 1.100, GmbH-Studio 5.000, Fotograf 800. Nur das Studio ist eine GmbH."
        a = voll(f, Fakten(anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter", positionen=[
            P(betrag=D("2400"), rolle="honorar", auftragnehmer_typ=NP),
            P(betrag=D("1100"), rolle="honorar", auftragnehmer_typ=NP),
            P(betrag=D("5000"), rolle="honorar", auftragnehmer_typ="GmbH_UG_AG"),
            P(betrag=D("800"), rolle="honorar", auftragnehmer_typ=NP),
        ]))
        self.assertNotEqual(a.ergebnisklasse, K.RUECKFRAGE)
        self.assertIn("4.300,00", a.antwort)

    def test_c3_falsche_summe_9300_kommt_nicht_vor(self):
        f = "2025: Grafiker 2.400, Texterin 1.100, GmbH-Studio 5.000, Fotograf 800. Nur das Studio ist eine GmbH."
        a = voll(f, Fakten(anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter", positionen=[
            P(betrag=D("2400"), rolle="honorar", auftragnehmer_typ=NP),
            P(betrag=D("1100"), rolle="honorar", auftragnehmer_typ=NP),
            P(betrag=D("5000"), rolle="honorar", auftragnehmer_typ="GmbH_UG_AG"),
            P(betrag=D("800"), rolle="honorar", auftragnehmer_typ=NP),
        ]))
        self.assertNotIn("9.300,00", a.antwort)

    def test_sonderrollen_kommen_aus_dem_kern_nicht_aus_dem_app_code(self):
        """Abschnitt C1: welche Rollen keine eigene Rechtsform brauchen, liest
        app/pflichtangaben.py direkt aus kern.rechnen._AUSSCHLUSSGRUENDE."""
        for rolle in ("fahrtkosten_nachgewiesen", "bewirtung", "ust", "verwertungsgesellschaft", "gewinnzuweisung"):
            fakten = Fakten(
                anfrageart="bewertung", jahr=2025,
                positionen=[P(betrag=D("100"), rolle=rolle)],
            )
            fragen = pflichtangaben.fehlende_pflichtangaben(fakten)
            self.assertFalse(
                any("Rechtsform" in f for f in fragen),
                f"Rolle '{rolle}' sollte keine Rechtsform-Rueckfrage ausloesen",
            )

    def test_leistung_ist_wieder_pflichtangabe(self):
        """Bis 11.10.2026 war die Leistung keine Pflichtangabe (Nachtrag C2), weil der Kern sie
        nicht brauchte. Der Testfall 20 Positionen zeigte: ohne Prüfung der Tätigkeit wird
        jede Zahlung an eine Einzelperson (auch Programmierung, SEO) als abgabepflichtig
        ausgegeben. Seitdem wird nach der Leistung gefragt, wenn sie gar nicht beschrieben ist."""
        fakten = Fakten(
            anfrageart="bewertung", jahr=2025, verwerterart="eigenwerber", auftragnehmer_typ=NP,
            positionen=[P(betrag=D("900"))],
        )
        self.assertEqual(pflichtangaben.fehlende_pflichtangaben(fakten), [pflichtangaben.FRAGE_LEISTUNG])
        mit_leistung = fakten.model_copy(update={"leistungsart": "Grafik/Design"})
        self.assertEqual(pflichtangaben.fehlende_pflichtangaben(mit_leistung), [])
        an_gmbh = fakten.model_copy(update={"auftragnehmer_typ": "GmbH_UG_AG"})
        self.assertEqual(pflichtangaben.fehlende_pflichtangaben(an_gmbh), [], "bei einer GmbH entscheidet die Leistung nicht")


if __name__ == "__main__":
    unittest.main(verbosity=2)
