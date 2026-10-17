"""Chatbot Teil 1f: uebernimmt jede Zeile aus aufgaben/audit/abnahme_teil1f.py als
Unittest (Abnahme-Vorgabe, Abschnitt "Abnahme") -- auch die Faelle, die beim Schreiben
der Abnahme schon "ok" waren (A6, D2, G). Zusaetzlich: Tests fuer Abschnitt I (Mistral-
Adapter-Robustheit, Plausibilitaetspruefung, Absturzschutz) und Abschnitt J (Oberflaeche:
Rueckfrage-Optionen loesen die Rueckfrage auf, Begruessung/Hinweis, kein Modellaufruf
dafuer)."""
import json
import re
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from kern import rechnen as K

from app import bestaetigung, pflichtangaben, plausibilitaet, quellen, router
from app.ergebnisklassen import (
    AUSKUNFT_ERTEILT,
    HINWEIS,
    NICHT_ABGEDECKT,
    RUECKFRAGE_NOETIG,
    SAEUMNISZUSCHLAG_BERECHNET,
)
from app.llm.base import LLMFehlgeschlagen
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position as P
from tests.app.zweck_knopf import mit_zweck  # Entscheidung 17.10.2026: geratener Zweck wird per Knopf bestätigt
from tests.app.hilfen import lauf_bestaetigt

NP, GMBH = "natuerliche_person", "GmbH_UG_AG"


def eur(x) -> str:
    return f"{D(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def erste_antwort(text, fakten):
    llm = FakeLLM()
    llm.registriere(text, fakten)
    return mit_zweck(router.bearbeite_frage(text, llm), fakten, llm), llm


def voll(text, fakten):
    return lauf_bestaetigt(FakeLLM(), text, fakten)


# ======================================================================================
# Abschnitt A: Rechtsform je Position
# ======================================================================================
BASIS_A = Fakten(
    anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter", leistungsart="Grafik/Design",
    positionen=[
        P(betrag=D("2400"), rolle="honorar", auftragnehmer_typ=NP),
        P(betrag=D("1100"), rolle="honorar", auftragnehmer_typ=NP),
        P(betrag=D("5000"), rolle="honorar", auftragnehmer_typ=GMBH, bezeichnung="GmbH-Studio"),
        P(betrag=D("800"), rolle="honorar", auftragnehmer_typ=NP),
    ],
)
TEXT_A = "A Gemischte Positionen 2025 (je Position eigene Rechtsform)"
SOLL_BG_A = D("2400") + D("1100") + D("800")
SOLL_ABGABE_A = K.berechne_abgabe(SOLL_BG_A, 2025)[0]


class TestAbschnittARechtsformJePosition(unittest.TestCase):
    def test_a1_bestaetigungsfrage_zeigt_rechtsform_je_position(self):
        a, _ = erste_antwort(TEXT_A, BASIS_A)
        z = " ".join(a.fakten_zusammenfassung) or a.antwort
        self.assertTrue(a.sitzungskennung)
        self.assertGreaterEqual(z.count("natürliche Person"), 3)
        self.assertTrue(re.search(r"GmbH|Gesellschaft|Kapital", z))

    def test_a2_bg_und_abgabe_nur_aus_den_natuerlichen_personen(self):
        b = voll(TEXT_A, BASIS_A)
        self.assertIn(eur(SOLL_BG_A), b.antwort)
        self.assertIn(eur(SOLL_ABGABE_A), b.antwort)

    def test_a3_falsche_summe_alle_posten_kommt_nicht_vor(self):
        b = voll(TEXT_A, BASIS_A)
        self.assertNotIn(eur(D("9300")), b.antwort)
        self.assertNotEqual(b.ergebnisklasse, RUECKFRAGE_NOETIG)

    def test_a4_ausschluss_gmbh_position_wird_erklaert(self):
        b = voll(TEXT_A, BASIS_A)
        self.assertTrue(
            "Nicht zur Bemessungsgrundlage" in b.antwort or "keine Bemessungsgrundlage" in b.antwort.lower()
        )

    def test_a5_rechtsform_einer_position_unbekannt_fuehrt_zu_rueckfrage(self):
        text = "A5 Rechtsform einer Position fehlt -> Rückfrage"
        fakten = Fakten(
            anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter", leistungsart="Grafik/Design",
            positionen=[P(betrag=D("2400"), rolle="honorar", auftragnehmer_typ=NP), P(betrag=D("900"), rolle="honorar", bezeichnung="Studio Nord")],
        )
        a, _ = erste_antwort(text, fakten)
        self.assertEqual(a.ergebnisklasse, K.RUECKFRAGE)
        self.assertTrue(any("Studio Nord" in r or "Position 2" in r for r in a.rueckfragen))

    def test_a6_globale_rechtsform_gilt_weiter_als_vorgabe(self):
        text = "A6 globale Rechtsform gilt weiter als Vorgabe (Altverhalten)"
        fakten = Fakten(
            anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter", auftragnehmer_typ=NP, leistungsart="Grafik/Design",
            positionen=[P(betrag=D("2400"), rolle="honorar")],
        )
        b = voll(text, fakten)
        self.assertIn(eur(2400), b.antwort)
        self.assertIn(eur(K.berechne_abgabe(D("2400"), 2025)[0]), b.antwort)


# ======================================================================================
# Abschnitt B: Saeumniszuschlag
# ======================================================================================
class TestAbschnittBSaeumniszuschlag(unittest.TestCase):
    TEXT = "B Säumniszuschlag 2025, Rückstand 2.000 €, 4 Monate"
    FAKTEN = Fakten(anfrageart="saeumniszuschlag", jahr=2025, rueckstand=D("2000"), saeumnis_monate=4)

    def test_b1_antwort_nennt_saeumniszuschlag(self):
        b = voll(self.TEXT, self.FAKTEN)
        self.assertIn("äumniszuschlag", b.antwort)

    def test_b2_kein_abgabesatz_und_kein_abgabepflichtig_im_text(self):
        b = voll(self.TEXT, self.FAKTEN)
        self.assertNotIn("Abgabesatz", b.antwort)
        self.assertNotIn("Abgabepflichtig", b.antwort)

    def test_b3_zuschlag_aus_dem_kern_genannt(self):
        b = voll(self.TEXT, self.FAKTEN)
        self.assertIn(eur(K.saeumniszuschlag([D("2000")], 4, 2025).abgabe), b.antwort)

    def test_b_zusatz_ergebnisklasse_ist_die_neue_anzeigeklasse(self):
        b = voll(self.TEXT, self.FAKTEN)
        self.assertEqual(b.ergebnisklasse, SAEUMNISZUSCHLAG_BERECHNET)
        self.assertIn("kern_klasse", b.kern_protokoll)
        self.assertEqual(b.kern_protokoll["kern_klasse"], K.ABGABEPFLICHTIG)


# ======================================================================================
# Abschnitt C: Auskunftsfragen
# ======================================================================================
def auskunft(thema, jahr):
    text = f"C Auskunft {thema} {jahr}"
    fakten = Fakten(anfrageart="auskunft", jahr=jahr, auskunft_thema=thema)
    return text, voll(text, fakten)


class TestAbschnittCAuskunftsfragen(unittest.TestCase):
    def test_c1_abgabesatz_2024_aus_der_excel(self):
        _, b = auskunft("abgabesatz", 2024)
        self.assertIn("5", b.antwort)
        self.assertNotEqual(b.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertTrue(b.fundstellen)
        self.assertEqual(b.ergebnisklasse, AUSKUNFT_ERTEILT)

    def test_c2_schwelle_2025_aus_der_excel_mit_fundstelle(self):
        _, b = auskunft("schwelle", 2025)
        self.assertIn("700", b.antwort)
        self.assertTrue(b.fundstellen)

    def test_c3_meldefrist_2025_ist_kern_datum(self):
        _, b = auskunft("meldefrist", 2025)
        self.assertIn(K.meldefrist(2025).strftime("%d.%m.%Y"), b.antwort)
        self.assertTrue(b.fundstellen)

    def test_c4_aufbewahrung_ist_kern_datum(self):
        _, b = auskunft("aufbewahrung", 2025)
        self.assertIn(K.aufbewahrung_bis(2025).strftime("%d.%m.%Y"), b.antwort)

    def test_c5_auskunft_ohne_jahr_fuehrt_zu_rueckfrage(self):
        a, _ = erste_antwort("C5 Auskunft ohne Jahr -> Rückfrage", Fakten(anfrageart="auskunft", auskunft_thema="abgabesatz"))
        self.assertEqual(a.ergebnisklasse, K.RUECKFRAGE)

    def test_c6_jahr_ohne_excel_wert_ist_nicht_abgedeckt(self):
        _, b = auskunft("abgabesatz", 2035)
        self.assertEqual(b.ergebnisklasse, NICHT_ABGEDECKT)

    def test_c7_schlusssatz_vorhanden(self):
        _, b = auskunft("abgabesatz", 2024)
        self.assertIn("Entwurf", b.antwort)
        self.assertIn("Steuerberater", b.antwort)

    def test_c_zusatz_auskunft_ohne_thema_fuehrt_zu_rueckfrage(self):
        a, _ = erste_antwort("C ohne Thema", Fakten(anfrageart="auskunft", jahr=2025))
        self.assertEqual(a.ergebnisklasse, K.RUECKFRAGE)

    def test_c_zusatz_pauschale_ist_nicht_abgedeckt_kein_erfundener_wert(self):
        _, b = auskunft("pauschale", 2025)
        self.assertEqual(b.ergebnisklasse, NICHT_ABGEDECKT)


# ======================================================================================
# Abschnitt D: Fundstellen mit richtigem Jahr
# ======================================================================================
class TestAbschnittDFundstellenMitRichtigemJahr(unittest.TestCase):
    TEXT = "D Vier Veranstaltungen 2025, Einnahmeabsicht ja"
    FAKTEN = Fakten(
        anfrageart="bewertung", jahr=2025, verwerterart="generalklausel", veranstaltungszahl=4, einnahmeabsicht=True,
        auftragnehmer_typ=NP, leistungsart="Musik", positionen=[P(betrag=D("3500"), rolle="honorar")],
    )

    def test_d1_keine_fundstelle_kopie_2022_01_22_bei_jahr_2025(self):
        b = voll(self.TEXT, self.FAKTEN)
        alle = " ".join(b.fundstellen) + " " + b.antwort
        self.assertNotIn("2022-01-22", alle)

    def test_d2_fassung_b_fuer_2025_genannt_nicht_a(self):
        b = voll(self.TEXT, self.FAKTEN)
        alle = " ".join(b.fundstellen) + " " + b.antwort
        self.assertNotIn("Fassung A", alle)

    def test_d_zusatz_bereinigte_fundstelle_enthaelt_vorbehalt(self):
        text = quellen.bereinige_fundstelle("KSVG § 24 Abs. 2 Satz 2 (Kopie 2022-01-22)")
        self.assertNotIn("2022-01-22", text)
        self.assertIn("Stand der Quelle", text)

    def test_d_zusatz_fassung_fuer_jahr_ohne_festwert(self):
        self.assertEqual(quellen.fassung_fuer_jahr(2022), "A")
        self.assertEqual(quellen.fassung_fuer_jahr(2023), "B")
        self.assertIsNone(quellen.fassung_fuer_jahr(1990))


# ======================================================================================
# Abschnitt E: Rueckfragen als Schaltflaechen
# ======================================================================================
class TestAbschnittERueckfragenAlsSchaltflaechen(unittest.TestCase):
    FAKTEN_OHNE_EINNAHMEABSICHT = Fakten(
        anfrageart="bewertung", jahr=2025, verwerterart="generalklausel", veranstaltungszahl=4,
        auftragnehmer_typ=NP, leistungsart="Musik", positionen=[P(betrag=D("3500"), rolle="honorar")],
    )
    FAKTEN_RECHTSFORM_UNBEKANNT = Fakten(
        anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter", leistungsart="Grafik/Design",
        positionen=[P(betrag=D("2400"), rolle="honorar", auftragnehmer_typ=NP), P(betrag=D("900"), rolle="honorar", bezeichnung="Studio Nord")],
    )

    def test_e1_antwort_hat_feld_rueckfrage_optionen_mit_ja_nein(self):
        a, _ = erste_antwort("E Einnahmeabsicht fehlt -> Schaltflächen", self.FAKTEN_OHNE_EINNAHMEABSICHT)
        opt = a.rueckfrage_optionen
        self.assertTrue(opt)
        self.assertTrue(any({"ja", "nein"} <= {str(o).lower() for o in x.get("optionen", [])} for x in opt))

    def test_e2_rechtsform_rueckfrage_bietet_die_rechtsformen_an(self):
        a, _ = erste_antwort("E2 Rechtsform-Rückfrage bietet die Rechtsformen an", self.FAKTEN_RECHTSFORM_UNBEKANNT)
        opt = a.rueckfrage_optionen
        self.assertTrue(opt)
        self.assertTrue(any(len(x.get("optionen", [])) >= 3 for x in opt))

    def test_e_zusatz_jahresfrage_bietet_registerjahre_an(self):
        a, _ = erste_antwort("E3 Jahr fehlt", Fakten(anfrageart="bewertung"))
        opt = a.rueckfrage_optionen
        self.assertTrue(opt)
        jahre = next(x["optionen"] for x in opt if "Kalenderjahr" in x["frage"])
        self.assertIn("2025", jahre)
        # Seit 11.10.2026 zusätzlich der Knopf 'Noch unbekannt / später klären' (Fallstand).
        from app.fallstand import UNBEKANNT_KNOPF

        self.assertEqual([j for j in jahre if j != UNBEKANNT_KNOPF], [str(j) for j in quellen.verfuegbare_jahre()])
        self.assertIn(UNBEKANNT_KNOPF, jahre)

    def test_e_zusatz_offene_frage_hat_keine_optionen(self):
        a, _ = erste_antwort(
            "E4 Betrag unbekannt",
            Fakten(anfrageart="bewertung", jahr=2025, auftragnehmer_typ=NP, leistungsart="Musik"),
        )
        # Seit 11.10.2026 (Fallstand, Testprotokoll): auch eine offene Frage bietet genau einen
        # Knopf an -- 'Noch unbekannt / später klären'; die Antwort selbst bleibt Texteingabe.
        from app.fallstand import UNBEKANNT_KNOPF

        for eintrag in a.rueckfrage_optionen:
            if "Betrag" in eintrag["frage"]:
                self.assertEqual(eintrag["optionen"], [UNBEKANNT_KNOPF])

    def test_e_zusatz_klick_auf_option_beantwortet_die_rueckfrage(self):
        """Teil 1f, Abschnitt J.5: 'der Router bekommt die Option als Antwort und
        beantwortet die Rueckfrage' -- simuliert einen Klick auf den Options-Knopf
        'ja', der (wie im Browser) als naechste Nutzer-Nachricht gesendet wird."""
        erste, _ = erste_antwort("E5 Einnahmeabsicht fehlt", self.FAKTEN_OHNE_EINNAHMEABSICHT)
        self.assertEqual(erste.ergebnisklasse, K.RUECKFRAGE)
        self.assertTrue(any({"ja", "nein"} <= {o.lower() for o in x["optionen"]} for x in erste.rueckfrage_optionen))

        llm_antwort = FakeLLM()
        fakten_mit_antwort = self.FAKTEN_OHNE_EINNAHMEABSICHT.model_copy(update={"einnahmeabsicht": True})
        zweite = lauf_bestaetigt(llm_antwort, "ja", fakten_mit_antwort)
        self.assertNotEqual(zweite.ergebnisklasse, K.RUECKFRAGE)


# ======================================================================================
# Abschnitt F: Pflichtangaben je Rechenart
# ======================================================================================
class TestAbschnittFPflichtangabenJeRechenart(unittest.TestCase):
    def test_f_vorauszahlung_ohne_vorjahres_bg_fragt_nur_danach(self):
        a, _ = erste_antwort("F Vorauszahlung ohne Vorjahres-BG fragt nur danach", Fakten(anfrageart="vorauszahlung", jahr=2026))
        r = " ".join(a.rueckfragen).lower()
        self.assertEqual(a.ergebnisklasse, K.RUECKFRAGE)
        self.assertIn("vorjahr", r)
        self.assertNotIn("rechtsform", r)
        self.assertNotIn("leistung", r)

    def test_f_zusatz_saeumnis_ohne_rueckstand_fragt_nur_danach(self):
        a, _ = erste_antwort("F2 Saeumnis ohne Rueckstand", Fakten(anfrageart="saeumniszuschlag", jahr=2025))
        r = " ".join(a.rueckfragen).lower()
        self.assertEqual(a.ergebnisklasse, K.RUECKFRAGE)
        self.assertIn("rückstand", r)
        self.assertNotIn("rechtsform", r)

    def test_f_zusatz_auskunft_braucht_jahr_und_thema(self):
        self.assertEqual(pflichtangaben.fehlende_pflichtangaben(Fakten(anfrageart="auskunft")), [pflichtangaben.FRAGE_JAHR])
        self.assertEqual(
            pflichtangaben.fehlende_pflichtangaben(Fakten(anfrageart="auskunft", jahr=2025)),
            [pflichtangaben.FRAGE_AUSKUNFT_THEMA],
        )


# ======================================================================================
# Abschnitt G: bisher Funktionierendes bleibt
# ======================================================================================
class TestAbschnittGBestehendesBleibt(unittest.TestCase):
    def test_g_fotograf_mit_nachgewiesenen_fahrtkosten(self):
        text = "G Fotograf 1.800 € mit 300 € nachgewiesenen Fahrtkosten, 2024"
        fakten = Fakten(
            anfrageart="bewertung", jahr=2024, verwerterart="typischer_verwerter", auftragnehmer_typ=NP, leistungsart="Fotografie",
            positionen=[P(betrag=D("1500"), rolle="honorar"), P(betrag=D("300"), rolle="fahrtkosten_nachgewiesen", nachgewiesen=True)],
        )
        b = voll(text, fakten)
        self.assertIn(eur(1500), b.antwort)
        self.assertNotIn(eur(1800), b.antwort.replace("1.500,00", ""))


# ======================================================================================
# Abschnitt I: Mistral-Test-Befunde (Extraktion, Plausibilitaet, Absturzschutz, Adapter)
# ======================================================================================
class TestAbschnittIPlausibilitaetspruefung(unittest.TestCase):
    def test_i2_gesamtbetrag_passt_keine_warnung(self):
        fakten = Fakten(positionen=[P(betrag=D("1500")), P(betrag=D("300"))], gesamtbetrag_genannt=D("1800"))
        self.assertIsNone(plausibilitaet.gesamtbetrag_warnung(fakten))

    def test_i2_gesamtbetrag_passt_nicht_warnung_in_der_bestaetigung(self):
        fakten = Fakten(
            jahr=2024, auftragnehmer_typ=NP, leistungsart="Fotografie",
            positionen=[P(betrag=D("1800")), P(betrag=D("300"))], gesamtbetrag_genannt=D("1800"),
        )
        warnung = plausibilitaet.gesamtbetrag_warnung(fakten)
        self.assertIsNotNone(warnung)
        self.assertIn(eur(2100), warnung)
        self.assertIn(eur(1800), warnung)
        self.assertIn(warnung, bestaetigung.als_liste(fakten))

    def test_i2_ohne_gesamtbetrag_keine_warnung(self):
        fakten = Fakten(positionen=[P(betrag=D("1500"))])
        self.assertIsNone(plausibilitaet.gesamtbetrag_warnung(fakten))


class TestAbschnittIAbsturzschutz(unittest.TestCase):
    """I.3: 'kein JSONDecodeError, kein HTTP 500' -- hier simuliert durch ein LLM, das
    beim Extrahieren eine LLMFehlgeschlagen-Ausnahme wirft (wie der echte Mistral-Adapter
    das jetzt tut, siehe TestMistralAdapterRobustheit unten).

    Seit Teil 1g (Mischform) schreibt das Modell nicht mehr den Antwort-Koerper
    (`formuliere_antwort` gibt es nicht mehr) -- es liefert hoechstens eine kurze
    Fallbeschreibung (`beschreibe_fall`). Faellt GENAU DIE aus, wird nur sie weggelassen;
    die Antwort bleibt vollstaendig (keine feste Rueckfrage mehr dafuer, siehe
    aufgaben/audit/abnahme_teil1g.py::G6)."""

    class _AbsturzBeimExtrahieren(FakeLLM):
        def extrahiere_fakten(self, frage, verlauf=None):
            raise LLMFehlgeschlagen("Freitext statt JSON (simuliert)")

    class _AbsturzBeiDerFallbeschreibung(FakeLLM):
        def beschreibe_fall(self, kontext):
            raise LLMFehlgeschlagen("Netzwerkfehler bei der Fallbeschreibung (simuliert)")

    def test_keine_gueltige_json_antwort_fuehrt_zu_fester_rueckfrage(self):
        ergebnis = router.bearbeite_frage("Irgendeine Frage", self._AbsturzBeimExtrahieren())
        self.assertEqual(ergebnis.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertIn("erneut", ergebnis.antwort.lower())

    def test_fehler_bei_der_fallbeschreibung_fuehrt_zu_vollstaendiger_antwort_kein_absturz(self):
        llm = self._AbsturzBeiDerFallbeschreibung()
        fakten = Fakten(
            anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter",
            auftragnehmer_typ=NP, leistungsart="Musik", positionen=[P(betrag=D("900"))],
        )
        ergebnis = lauf_bestaetigt(llm, "F", fakten)
        abgabe = K.berechne_abgabe(D("900"), 2025)[0]
        self.assertNotEqual(ergebnis.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertNotIn("fehlgeschlagen", ergebnis.ergebnisklasse.lower())
        self.assertIn(eur(abgabe), ergebnis.antwort)


class TestAbschnittIMistralPromptVerbote(unittest.TestCase):
    """I.1/I.4: die Verbote stehen im Extraktions-Prompt -- Offline-Test (kein Netz)."""

    def test_prompt_verbietet_rechtseinstufung_ohne_ausdrueckliche_aussage(self):
        from app.llm.mistral import _SYSTEM_EXTRAKTION

        for feld in (
            "auftraggeber_typ", "auftragnehmer_typ", "verwerterart", "kuenstlerisch",
            "agentur_abgabepflichtig", "empfaenger_abgabepflichtig", "einnahmeabsicht",
        ):
            self.assertIn(feld, _SYSTEM_EXTRAKTION)
        self.assertIn("honorar", _SYSTEM_EXTRAKTION)
        self.assertIn("Davon", _SYSTEM_EXTRAKTION.replace("'Davon'", "Davon"))
        self.assertIn("gesamtbetrag_genannt", _SYSTEM_EXTRAKTION)

    def test_prompt_erlaubt_hinweis_fuer_begruessung_ohne_sachfrage(self):
        from app.llm.mistral import _SYSTEM_EXTRAKTION

        self.assertIn("hinweis", _SYSTEM_EXTRAKTION)


class TestAbschnittIMistralAdapterRobustheit(unittest.TestCase):
    """I.5 (M6a-d), offline mit gefaelschten httpx-Antworten -- kein echter Netzwerkaufruf."""

    def _llm(self):
        from app.llm.mistral import MistralLLM

        return MistralLLM(api_key="offline-test-schluessel")

    def _fake_response(self, status=200, json_daten=None, wirft=None):
        class _R:
            status_code = status

            def raise_for_status(self):
                if wirft:
                    raise wirft

            def json(self):
                return json_daten

        return _R()

    def test_m6a_top_p_wird_mitgeschickt(self):
        llm = self._llm()
        gesendet = {}

        def fake_post(url, headers, json):
            gesendet.update(json)
            return self._fake_response(json_daten={"choices": [{"message": {"content": "{}"}}]})

        with patch.object(llm._client, "post", fake_post):
            llm._aufruf("system", "user")
        self.assertEqual(gesendet.get("top_p"), 1)
        self.assertEqual(gesendet.get("temperature"), 0.0)

    def test_m6b_content_als_liste_von_bloecken_wird_zusammengesetzt(self):
        llm = self._llm()
        bloecke = [{"type": "text", "text": "Hallo "}, {"type": "text", "text": "Welt"}]
        with patch.object(
            llm._client, "post",
            lambda *a, **k: self._fake_response(json_daten={"choices": [{"message": {"content": bloecke}}]}),
        ):
            ergebnis = llm._aufruf("system", "user")
        self.assertEqual(ergebnis, "Hallo Welt")

    def test_m6c_timeout_ist_ueber_umgebungsvariable_einstellbar(self):
        import importlib

        with patch.dict("os.environ", {"MISTRAL_TIMEOUT": "99"}):
            import app.llm.mistral as mistral_modul

            importlib.reload(mistral_modul)
            try:
                self.assertEqual(mistral_modul.MISTRAL_TIMEOUT, 99.0)
            finally:
                importlib.reload(mistral_modul)  # Standardwert fuer nachfolgende Tests wiederherstellen

    def test_m6d_json_decode_fehler_wird_zu_llmfehlgeschlagen(self):
        llm = self._llm()
        with patch.object(
            llm._client, "post",
            lambda *a, **k: self._fake_response(json_daten={"choices": [{"message": {"content": "kein json {"}}]}),
        ):
            with self.assertRaises(LLMFehlgeschlagen):
                llm.extrahiere_fakten("Frage")

    def test_m6d_pydantic_fehler_wird_zu_llmfehlgeschlagen(self):
        llm = self._llm()
        unbekanntes_json = json.dumps({"jahr": "nicht_eine_zahl_sondern_text_ueber_1980_2100"})
        with patch.object(
            llm._client, "post",
            lambda *a, **k: self._fake_response(json_daten={"choices": [{"message": {"content": unbekanntes_json}}]}),
        ):
            with self.assertRaises(LLMFehlgeschlagen):
                llm.extrahiere_fakten("Frage")

    def test_m6d_timeout_wird_zu_llmfehlgeschlagen(self):
        import httpx

        llm = self._llm()
        with patch.object(llm._client, "post", side_effect=httpx.TimeoutException("zu lange gewartet")):
            with self.assertRaises(LLMFehlgeschlagen):
                llm._aufruf("system", "user")

    def test_m6d_http_fehler_wird_zu_llmfehlgeschlagen(self):
        import httpx

        llm = self._llm()
        with patch.object(
            llm._client, "post",
            lambda *a, **k: self._fake_response(status=400, wirft=httpx.HTTPStatusError("400", request=None, response=None)),
        ):
            with self.assertRaises(LLMFehlgeschlagen):
                llm._aufruf("system", "user")


# ======================================================================================
# Abschnitt J: Oberflaeche (Begruessung/Hinweis ohne Modellaufruf; kein Festwert im Code)
# ======================================================================================
class TestAbschnittJHinweisBegruessung(unittest.TestCase):
    def test_j3_begruessung_ohne_modellaufruf_und_ohne_rueckfrage(self):
        llm = FakeLLM()
        llm.registriere("hallo", Fakten(anfrageart="hinweis"))
        ergebnis = router.bearbeite_frage("hallo", llm)
        self.assertEqual(ergebnis.ergebnisklasse, HINWEIS)
        self.assertNotEqual(ergebnis.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertIn("Entwurf", ergebnis.antwort)

    def test_j3_demo_heuristik_erkennt_reine_begruessung(self):
        llm = FakeLLM()
        for text in ("hallo", "Hallo!", "Danke", "was kannst du?", "Guten Tag"):
            with self.subTest(text=text):
                fakten = llm.extrahiere_fakten(text)
                self.assertEqual(fakten.anfrageart, "hinweis", f"{text!r} haette als Hinweis erkannt werden muessen")

    def test_j3_demo_heuristik_erkennt_echte_frage_nicht_als_begruessung(self):
        llm = FakeLLM()
        fakten = llm.extrahiere_fakten("Hallo, ich habe eine Frage zu 2025 und einem Grafiker.")
        self.assertNotEqual(fakten.anfrageart, "hinweis")

    def test_j3_hinweis_braucht_kein_jahr(self):
        self.assertEqual(pflichtangaben.fehlende_pflichtangaben(Fakten(anfrageart="hinweis")), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
