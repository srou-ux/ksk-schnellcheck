"""Tests zu M5 und M6 aus aufgaben/PROMPT_ClaudeCode_Chatbot_Pruefkatalog1_Befunde.md
(Befunde aus dem zweiten Prüfkatalog-Lauf mit Mistral, 10.10.2026):
M5 ("Veranstalter (Generalklausel)" wird wie Eigenwerbung gerechnet),
M6 (Mistral-Ratenbegrenzung -> Wiederholung mit wachsender Wartezeit)."""
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path
from unittest.mock import patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app import bestaetigung, pflichtangaben, router
from app.ergebnisklassen import ABGABEPFLICHTIG, NICHT_ABGABEPFLICHTIG, RUECKFRAGE_NOETIG
from app.llm.base import LLMFehlgeschlagen
from app.llm.fake import FakeLLM
from app.llm.mistral import MISTRAL_API_URL, MistralLLM
from app.schema import Fakten, Position as P
from tests.app.zweck_knopf import mit_zweck  # Entscheidung 17.10.2026: geratener Zweck wird per Knopf bestätigt

NP = "natuerliche_person"


def _lauf(frage, fakten, llm=None):
    llm = llm or FakeLLM()
    llm.registriere(frage, fakten)
    a = mit_zweck(router.bearbeite_frage(frage, llm), fakten, llm)
    if a.sitzungskennung and a.fakten_hash:
        bestaetigung.SPEICHER.bestaetige(a.sitzungskennung, a.fakten_hash)
        a = router.fuehre_nach_bestaetigung_aus(a.sitzungskennung, llm)
    return a


# ==========================================================================================
# M5: Generalklausel -- nie die Eigenwerbungs-Logik/-Fundstelle, Drei-Veranstaltungen-
# Ausnahme nur fuer ECHTE Veranstaltungen (nie bei 0).
# ==========================================================================================
class TestM5GeneralklauselStattEigenwerbung(unittest.TestCase):
    def test_p08_drei_veranstaltungen_nicht_abgabepflichtig(self):
        fakten = Fakten(
            jahr=2025, verwerterart="generalklausel", auftragnehmer_typ=NP,
            veranstaltungszahl=3, einnahmeabsicht=True, positionen=[P(betrag=D("5000"), taetigkeit_id="T-07")],
        )
        ergebnis = _lauf("P-08", fakten)
        self.assertEqual(ergebnis.ergebnisklasse, NICHT_ABGABEPFLICHTIG)

    def test_p09_vier_veranstaltungen_abgabepflichtig_250(self):
        fakten = Fakten(
            jahr=2025, verwerterart="generalklausel", auftragnehmer_typ=NP,
            veranstaltungszahl=4, einnahmeabsicht=True, positionen=[P(betrag=D("5000"), taetigkeit_id="T-07")],
        )
        ergebnis = _lauf("P-09", fakten)
        self.assertEqual(ergebnis.ergebnisklasse, ABGABEPFLICHTIG)
        self.assertEqual(ergebnis.kern_protokoll.get("abgabe"), D("250.00"))

    def test_generalklausel_ohne_einnahmeabsicht_fuehrt_zu_rueckfrage(self):
        fakten = Fakten(
            jahr=2025, verwerterart="generalklausel", auftragnehmer_typ=NP,
            veranstaltungszahl=4, positionen=[P(betrag=D("5000"), taetigkeit_id="T-07")],
        )
        # 14.10.2026: bei höchstens drei Veranstaltungen fragt das System nicht mehr nach der Einnahmeabsicht
        # (KSVG § 24 Abs. 2 S. 3 Nr. 1: dann keine Abgabepflicht nach S. 1 Nr. 2, unabhängig davon); der
        # Zweck des Tests (bei der Generalklausel wird gefragt) gilt jetzt für mehr als drei Veranstaltungen.
        ergebnis = _lauf("RF-einnahmeabsicht", fakten)
        self.assertEqual(ergebnis.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertIn(pflichtangaben.FRAGE_EINNAHMEABSICHT, ergebnis.rueckfragen)

    def test_generalklausel_ohne_veranstaltungszahl_fuehrt_zu_rueckfrage(self):
        """Vorher (Befund): fiel ohne veranstaltungszahl in den `positionen`-Zweig und
        wurde faelschlich mit der Eigenwerbungs-Schwelle geprueft."""
        fakten = Fakten(jahr=2025, verwerterart="generalklausel", auftragnehmer_typ=NP, positionen=[P(betrag=D("5000"), taetigkeit_id="T-07")])
        ergebnis = _lauf("RF-veranstaltungszahl", fakten)
        self.assertEqual(ergebnis.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertIn(pflichtangaben.FRAGE_VERANSTALTUNGSZAHL, ergebnis.rueckfragen)

    def test_p07_null_veranstaltungen_wird_nicht_als_befreit_behandelt(self):
        """Zweites Beispiel zu M5/M7: Fotos zur Lizenzierung, 'keine Veranstaltungen'
        (veranstaltungszahl=0), Einnahmeabsicht ja -> abgabepflichtig 150,00 € (nicht
        'Nicht abgabepflichtig' ueber die Drei-Veranstaltungen-Ausnahme, die nur fuer
        Entgelte AUS Veranstaltungen gilt). M7: keine falsche Begruendung ('Mehr als drei
        Veranstaltungen'/'drei Veranstaltungen' -- genau die `verboten_text`-Liste von P-07
        in aufgaben/audit/pruefkatalog.json) und keine Ersatzzahl mehr; eigene Fundstelle
        R-13 (KSVG § 24 Abs. 2 S. 1 Nr. 2, S. 2), nicht die Veranstaltungs-Fundstelle
        (... S. 3 Nr. 1)."""
        fakten = Fakten(
            jahr=2025, verwerterart="generalklausel", auftragnehmer_typ=NP,
            veranstaltungszahl=0, einnahmeabsicht=True, positionen=[P(betrag=D("3000"), taetigkeit_id="T-07")],
        )
        ergebnis = _lauf("P-07", fakten)
        self.assertEqual(ergebnis.ergebnisklasse, ABGABEPFLICHTIG)
        self.assertEqual(ergebnis.kern_protokoll.get("abgabe"), D("150.00"))
        subsumtion = str(ergebnis.kern_protokoll.get("subsumtion", ""))
        self.assertNotIn("Mehr als drei Veranstaltungen", subsumtion)
        self.assertNotIn("drei Veranstaltungen", subsumtion)
        alle_fundstellen = " ".join(ergebnis.fundstellen)
        self.assertNotIn("S. 3 Nr. 1", alle_fundstellen)
        self.assertIn("S. 1 Nr. 2", alle_fundstellen)

    def test_generalklausel_nutzt_nie_die_eigenwerbungs_fundstelle(self):
        """M5, Punkt 3: fuer KEINEN Generalklausel-Fall darf die Eigenwerbungs-Fundstelle
        ('KSVG § 24 Abs. 2 S. 2, § 54') auftauchen -- weder bei der Veranstaltungs- noch
        bei der 0-Veranstaltungen-Schwellenpruefung."""
        for veranstaltungszahl in (3, 4, 0):
            with self.subTest(veranstaltungszahl=veranstaltungszahl):
                fakten = Fakten(
                    jahr=2025, verwerterart="generalklausel", auftragnehmer_typ=NP,
                    veranstaltungszahl=veranstaltungszahl, einnahmeabsicht=True,
                    positionen=[P(betrag=D("5000"), taetigkeit_id="T-07")],
                )
                ergebnis = _lauf(f"Fundstelle-{veranstaltungszahl}", fakten)
                alle_fundstellen = " ".join(ergebnis.fundstellen)
                self.assertNotIn("§ 54", alle_fundstellen)
                self.assertNotIn("Abs. 2 S. 2,", alle_fundstellen)

    def test_veranstaltungszahl_null_waechter_direkt_im_router(self):
        """Waechter-Test direkt auf app/router.py::_rufe_kern_auf (umgeht die
        Pflichtangaben-Pruefung) -- auch bei direktem Aufruf darf 0 Veranstaltungen nie
        in die Drei-Veranstaltungen-Ausnahme fuehren."""
        fakten = Fakten(
            jahr=2025, verwerterart="generalklausel", auftragnehmer_typ=NP,
            veranstaltungszahl=0, einnahmeabsicht=True, positionen=[P(betrag=D("3000"), taetigkeit_id="T-07")],
        )
        kern_ergebnis = router._rufe_kern_auf(fakten)
        self.assertEqual(kern_ergebnis.klasse, ABGABEPFLICHTIG)


def _antwort(status_code: int, inhalt: str | None = None, headers: dict | None = None) -> httpx.Response:
    anfrage = httpx.Request("POST", MISTRAL_API_URL)
    if status_code < 400:
        return httpx.Response(status_code, request=anfrage, json={"choices": [{"message": {"content": inhalt}}]})
    return httpx.Response(status_code, request=anfrage, headers=headers or {})


def _llm() -> MistralLLM:
    return MistralLLM(api_key="offline-test-schluessel")


# ==========================================================================================
# M6: HTTP 429/503 werden wiederholt (wachsende Wartezeit), statt sofort aufzugeben.
# Offline: `self._client.post` wird gefaked, `time.sleep` wird abgeschaltet.
# ==========================================================================================
class TestM6MistralRatenbegrenzung(unittest.TestCase):
    def test_429_zweimal_dann_erfolg_liefert_am_ende_die_fakten(self):
        llm = _llm()
        antworten = [_antwort(429), _antwort(429), _antwort(200, '{"jahr": 2025}')]
        with patch.object(llm._client, "post", side_effect=antworten) as post_mock, \
             patch("app.llm.mistral.time.sleep") as sleep_mock:
            fakten = llm.extrahiere_fakten("Frage")
        self.assertEqual(fakten.jahr, 2025)
        self.assertEqual(post_mock.call_count, 3)
        self.assertEqual(sleep_mock.call_count, 2)

    def test_wartezeiten_wachsen_gemaess_standardkonfiguration(self):
        llm = _llm()
        antworten = [_antwort(429), _antwort(429), _antwort(200, "{}")]
        with patch.object(llm._client, "post", side_effect=antworten), \
             patch("app.llm.mistral.time.sleep") as sleep_mock:
            llm.extrahiere_fakten("Frage")
        sleep_mock.assert_any_call(1.0)
        sleep_mock.assert_any_call(3.0)

    def test_retry_after_header_hat_vorrang_vor_der_konfiguration(self):
        llm = _llm()
        antworten = [_antwort(429, headers={"Retry-After": "5"}), _antwort(200, "{}")]
        with patch.object(llm._client, "post", side_effect=antworten), \
             patch("app.llm.mistral.time.sleep") as sleep_mock:
            llm.extrahiere_fakten("Frage")
        sleep_mock.assert_called_once_with(5.0)

    def test_503_wird_ebenfalls_wiederholt(self):
        llm = _llm()
        antworten = [_antwort(503), _antwort(200, "{}")]
        with patch.object(llm._client, "post", side_effect=antworten), \
             patch("app.llm.mistral.time.sleep") as sleep_mock:
            llm.extrahiere_fakten("Frage")
        self.assertEqual(sleep_mock.call_count, 1)

    def test_nach_allen_versuchen_bleibt_es_llmfehlgeschlagen(self):
        llm = _llm()
        antworten = [_antwort(429) for _ in range(10)]
        with patch.object(llm._client, "post", side_effect=antworten), \
             patch("app.llm.mistral.time.sleep"):
            with self.assertRaises(LLMFehlgeschlagen):
                llm.extrahiere_fakten("Frage")

    def test_andere_statuscodes_werden_nicht_wiederholt(self):
        llm = _llm()
        antworten = [_antwort(400)]
        with patch.object(llm._client, "post", side_effect=antworten) as post_mock, \
             patch("app.llm.mistral.time.sleep") as sleep_mock:
            with self.assertRaises(LLMFehlgeschlagen):
                llm.extrahiere_fakten("Frage")
        self.assertEqual(post_mock.call_count, 1)
        sleep_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
