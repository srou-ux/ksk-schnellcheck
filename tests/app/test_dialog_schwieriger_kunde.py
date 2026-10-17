"""Regressionstests zum Test-Dialog „Der schwierige Kunde“ (Nutzer, 13.10.2026). Erfundene Daten.

Geprüft wird die Python-Logik, OFFLINE mit nachgebildeter Modellantwort:
- Nach einem fertigen Ergebnis beginnt eine Nachfrage keinen leeren neuen Fall mehr
  ('Das kann nicht stimmen', 'Protokoll', 'noch offen', 'IGNORIERE …'): feste Antwort, Ergebnis unverändert.
- Neue Angaben zu denselben Positionen führen den Fall weiter, ohne Beträge doppelt zu zählen.
- Ein vom Modell gemeldeter Widerspruch ohne Angabe in der Nachricht gilt nicht.
- Ein Modellfehler in einem laufenden Fall zeigt die Übersicht statt einer Sackgasse."""
from __future__ import annotations

import json
import unittest
from decimal import Decimal as D
from pathlib import Path

from app import bestaetigung, fallstand, router
from app.llm.base import LLMFehlgeschlagen
from app.schema import Fakten, Position as P, Widerspruch

SCHRITTE = json.loads((Path(__file__).resolve().parents[2] / "aufgaben" / "audit" / "dialog_schwieriger_kunde.json")
                      .read_text(encoding="utf-8"))
NP, G = "natuerliche_person", "GmbH_UG_AG"


def _rechnung():
    return Fakten(anfrageart="bewertung", positionen=[
        P(betrag=D("3400"), bezeichnung="Bühnenaufbau und Technik"),
        P(betrag=D("2900"), bezeichnung="Auftritt Pianist, im eigenen Namen der Agentur eingekauft", taetigkeit_id="T-07"),
        P(betrag=D("1600"), bezeichnung="Airbrush-Wandgestaltung Messeträger", taetigkeit_id="T-16", auftragnehmer_typ=NP)])


class Modell:
    """Liefert für die Rechnung die Positionen, sonst nichts Neues (oder einen erfundenen Widerspruch)."""

    def __init__(self, widerspruch_erfinden=False, fehler=False):
        self.widerspruch_erfinden, self.fehler, self.aufrufe = widerspruch_erfinden, fehler, 0

    def extrahiere_fakten(self, frage, verlauf=None, fallstand=None):
        self.aufrufe += 1
        if "Rechnungsteller" in frage:
            return _rechnung()
        if self.fehler:
            raise LLMFehlgeschlagen("kaputtes JSON")
        if self.widerspruch_erfinden:
            return Fakten(widersprueche=[Widerspruch(feld="positionen.2.auftragnehmer_typ", werte=["GmbH_UG_AG", NP])])
        return Fakten()

    def beschreibe_fall(self, kontext):  # pragma: no cover
        return ""


class TestSchwierigerKunde(unittest.TestCase):
    def _bis_ergebnis(self, llm):
        a = router.bearbeite_frage(SCHRITTE[1]["text"], llm, [])
        self.assertEqual(a.ergebnisklasse, "Faktenbestätigung nötig", a.rueckfragen)
        bestaetigung.SPEICHER.bestaetige(a.sitzungskennung, a.fakten_hash)
        e = router.fuehre_nach_bestaetigung_aus(a.sitzungskennung, llm)
        return e, a.sitzungskennung

    def test_ergebnis_der_rechnung(self):
        e, _ = self._bis_ergebnis(Modell())
        self.assertEqual(e.ergebnisklasse, "Abgabepflichtig (Vorschlag)")
        self.assertEqual(D(e.kern_protokoll["abgabe"]) if isinstance(e.kern_protokoll["abgabe"], str)
                         else e.kern_protokoll["abgabe"], D("78.40"))  # 1.600 € × 4,9 %
        self.assertIn("Nr. 3", e.antwort)

    def _nachfrage(self, text, llm=None):
        llm = llm or Modell()
        e, sitzung = self._bis_ergebnis(llm)
        vorher = llm.aufrufe
        n = router.bearbeite_frage(text, llm, [], None, letzte_sitzung=sitzung)
        return e, n, llm.aufrufe - vorher

    def test_widerspruch_bekommt_erklaerung_und_gleiches_ergebnis(self):
        e, n, aufrufe = self._nachfrage(SCHRITTE[2]["text"])
        self.assertEqual(aufrufe, 0, "Nachfrage braucht kein Modell")
        self.assertEqual(n.ergebnisklasse, e.ergebnisklasse)
        self.assertEqual(n.kern_protokoll["abgabe"], e.kern_protokoll["abgabe"])
        self.assertIn("wer mit ihm den Vertrag geschlossen hat", n.antwort)

    def test_vorgabe_und_prompt_injection_aendern_nichts(self):
        for nr in (5, 6):
            with self.subTest(schritt=nr + 1):
                e, n, aufrufe = self._nachfrage(SCHRITTE[nr]["text"])
                self.assertEqual((n.ergebnisklasse, n.kern_protokoll["abgabe"]), (e.ergebnisklasse, e.kern_protokoll["abgabe"]))
                self.assertIn("ändern es nicht", n.antwort)
                self.assertIn("Entwurf – vom Steuerberater zu prüfen", n.antwort)
                self.assertEqual(aufrufe, 0)

    def test_zahlung_offen(self):
        _, n, _ = self._nachfrage(SCHRITTE[4]["text"])
        self.assertIn("in dem das Entgelt gezahlt wird", n.antwort)

    def test_protokoll(self):
        _, n, _ = self._nachfrage(SCHRITTE[7]["text"])
        self.assertIn("Zusammenfassung der Prüfung", n.antwort)
        self.assertIn("**Bestätigte Angaben:**", n.antwort)
        self.assertIn("keine Rechtsberatung", n.antwort)

    def test_neue_angabe_zu_bekannter_position_fuehrt_den_fall_weiter(self):
        e, n, _ = self._nachfrage(SCHRITTE[3]["text"])  # '3.400 € Technik … Personal'
        stand = bestaetigung.SPEICHER.hole_fakten(n.sitzungskennung)
        self.assertEqual(len(stand.positionen), 3, "keine doppelten Positionen")
        self.assertEqual(n.ergebnisklasse, e.ergebnisklasse)

    def test_neuer_betrag_ist_ein_neuer_fall(self):
        e, sitzung = self._bis_ergebnis(Modell())
        self.assertEqual(router._nachfrage_zum_letzten_fall("Ein Fotograf hat uns 500 € berechnet.", Modell(), sitzung), None)

    def test_erfundener_widerspruch_gilt_nicht(self):
        alt = _rechnung()
        neu = Fakten(widersprueche=[Widerspruch(feld="positionen.2.auftragnehmer_typ", werte=[G, NP])])
        self.assertFalse(fallstand.uebernehme(alt, neu, SCHRITTE[6]["text"]).widersprueche)
        mit_angabe = fallstand.uebernehme(alt, neu, "Pos. 3 ist eine GmbH, nicht die Künstlerin.")
        self.assertTrue(mit_angabe.widersprueche)

    def test_modellfehler_im_laufenden_fall_zeigt_uebersicht(self):
        llm = Modell(fehler=True)
        a = router.bearbeite_frage(SCHRITTE[1]["text"], llm, [])
        n = router.bearbeite_frage("Moment, da ist noch etwas komisch.", llm, [SCHRITTE[1]["text"]], a.sitzungskennung)
        self.assertIn("**Bisher erfasst:**", n.antwort)
        self.assertNotIn("konnte nicht verarbeitet", n.antwort)


if __name__ == "__main__":
    unittest.main()


class SchrittEinsOhneRechnung(unittest.TestCase):
    """Schritt 1 'Ich habe eine Rechnung … bekommen … Wir sind eine Messe': bisher nur Rückfrage nach
    dem Jahr. Soll: keine Bewertung ohne Rechnung, kurze Erklärung, Bitte um die Rechnung."""

    def test_bittet_um_rechnung_ohne_modell_und_ohne_bewertung(self):
        modell = Modell()
        a = router.bearbeite_frage(SCHRITTE[0]["text"], modell)
        self.assertEqual(modell.aufrufe, 0)
        self.assertEqual(a.ergebnisklasse, router.RUECKFRAGE_NOETIG)
        self.assertIn("Ohne die Rechnung kann ich noch nichts bewerten", a.antwort)
        self.assertIn("Bitte schicken Sie mir die Rechnung", a.antwort)
        self.assertIn("KSVG § 24", a.antwort)
        self.assertNotIn("Jahr der Rechnung", a.antwort)
        self.assertNotIn("nichts mit Künstlern zu tun", a.antwort)
        for wort in ("Abgabepflichtig (Vorschlag)", "Nicht abgabepflichtig", "€"):
            self.assertNotIn(wort, a.antwort)
        self.assertIsNone(a.sitzungskennung)

    def test_danach_beginnt_die_rechnung_den_fall(self):
        router.bearbeite_frage(SCHRITTE[0]["text"], Modell())
        modell = Modell()
        a = router.bearbeite_frage(SCHRITTE[1]["text"], modell, verlauf=[SCHRITTE[0]["text"]])
        self.assertEqual(modell.aufrufe, 1)
        self.assertNotIn("Ohne die Rechnung", a.antwort)

    def test_greift_nicht_bei_inhalt_oder_vertretung(self):
        from app import zuordnung
        for text in (
            SCHRITTE[1]["text"],
            "Ich habe eine Rechnung von einem Grafiker über 900 € bekommen.",
            "Ich habe eine Rechnung von einem Grafiker über 900 bekommen.",
            "Ich habe eine Rechnung von einer Foto-GmbH bekommen, ist das abgabepflichtig?",
            "Wir handeln 2025 mit Vollmacht im Namen und für Rechnung einer Sängerin.",
            "Ist ein Fotograf abgabepflichtig?",
        ):
            self.assertFalse(zuordnung.rechnung_angekuendigt_ohne_inhalt(text), text)
        self.assertTrue(zuordnung.rechnung_angekuendigt_ohne_inhalt("Ich habe 2026 eine Rechnung von einem Grafiker bekommen."))

    def test_laufender_fall_bleibt_unberuehrt(self):
        kennung = bestaetigung.SPEICHER.neue_sitzung(verlauf_start=0)
        a = router.bearbeite_frage(SCHRITTE[0]["text"], Modell(), sitzungskennung=kennung)
        self.assertNotIn("Ohne die Rechnung", a.antwort)
