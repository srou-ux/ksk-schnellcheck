"""Umbau Schritt 1 (16.10.2026): Einordnung des Auftraggebers aus Fakten mit Herkunft (app/einordnung.py).

Abnahme laut Nutzer: Bäckerei mit Eigenwerbung, Verlag mit Eigenwerbung, Agentur mit Kundenauftrag, tatsächlich
privater Auftrag – jeweils auch mit fehlenden oder widersprüchlichen Angaben. Dazu die Regressionstests aus der
Diskussion mit dem Nutzer (keine allgemeine Rückfrage bei ausdrücklicher Eigenwerbung, gezielte Widerspruchsfrage,
73,50 € mit Eigenwerbungs-Begründung, genau 1.000 € nicht überschritten, Falljahr bleibt bei einer Zusatzfrage).
Die Modellantworten sind nachgebildet (FakeLLM) – geprüft wird das System, nicht das Modell. Erfundene Daten."""
from __future__ import annotations

import unittest

from app import bestaetigung, pflichtangaben, router, warteschlange
from app.einordnung import erfasse, leite_ab
from app.llm.fake import FakeLLM
from app.schema import Fakten
from tests.app.zweck_knopf import mit_zweck  # Entscheidung 17.10.2026: geratener Zweck wird per Knopf bestätigt

BAECKEREI = ("Wir sind eine Bäckerei und machen Werbung für unser eigenes Geschäft. 2026 haben wir einem freien "
             "Grafiker 1.500 € für Logo und Flyer gezahlt. Ist das abgabepflichtig?")
GRUND = {"anfrageart": "bewertung", "jahr": 2026, "auftragnehmer_typ": "natuerliche_person"}


def _start(text, **modell):
    llm = FakeLLM()
    daten = {**GRUND, "positionen": [{"betrag": 1500, "bezeichnung": "Logo und Flyer"}], **modell}
    llm.registriere(text, Fakten.model_validate(daten))
    return llm, router.bearbeite_frage(text, llm)


def _ergebnis(a, llm):
    assert a.ergebnisklasse == "Faktenbestätigung nötig", (a.ergebnisklasse, a.rueckfragen)
    bestaetigung.SPEICHER.bestaetige(a.sitzungskennung, a.fakten_hash)
    return router.fuehre_nach_bestaetigung_aus(a.sitzungskennung, llm)


class Baeckerei(unittest.TestCase):
    def test_ausdrueckliche_eigenwerbung_keine_allgemeine_rueckfrage(self):
        for modell in ({}, {"verwerterart": "eigenwerber"}, {"verwerterart": "typischer_verwerter"}):
            llm, a = _start(BAECKEREI, **modell)
            self.assertEqual(a.ergebnisklasse, "Faktenbestätigung nötig", (modell, a.rueckfragen))
            self.assertIn("Rechtliche Einordnung (Vorschlag des Systems, keine Angabe von Ihnen): Eigenwerbung", a.fakten_zusammenfassung)
            self.assertTrue(any("„für unser eigenes Geschäft“" in z for z in a.fakten_zusammenfassung),
                            "Herkunft mit Zitat sichtbar")

    def test_1500_euro_mit_eigenwerbungs_begruendung(self):
        llm, a = _start(BAECKEREI)
        e = _ergebnis(a, llm)
        self.assertEqual(str(e.kern_protokoll.get("abgabe")), "73.50")
        self.assertIn("Schwelle", e.antwort)
        self.assertNotIn("Typischer Verwerter: keine Schwelle", e.antwort)

    def test_genau_1000_euro_nicht_ueberschritten(self):
        llm = FakeLLM()
        text = BAECKEREI.replace("1.500", "1.000")
        llm.registriere(text, Fakten.model_validate({**GRUND, "positionen": [{"betrag": 1000, "bezeichnung": "Logo"}]}))
        e = _ergebnis(router.bearbeite_frage(text, llm), llm)
        self.assertEqual(e.ergebnisklasse, "Nicht abgabepflichtig (Vorschlag)")

    def test_widerspruechlicher_knopf_wird_gezielt_geklaert(self):
        llm, a = _start(BAECKEREI)
        b = router.wende_feldantwort_an(a.sitzungskennung, "verwerterart", "typischer_verwerter", llm)
        self.assertEqual(b.ergebnisklasse, "Rückfrage nötig")
        self.assertIn("Sie hatten geschrieben: „für unser eigenes Geschäft“", b.rueckfragen[0])
        self.assertIsNone(b.fakten_hash, "keine Bestätigung, solange der Widerspruch offen ist")
        stand = bestaetigung.SPEICHER.hole_fakten(b.sitzungskennung)
        self.assertIsNone(stand.verwerterart, "nichts still überschrieben")
        c = router.wende_feldantwort_an(b.sitzungskennung, "verwerterart", "eigenwerber", llm)
        self.assertEqual(c.ergebnisklasse, "Faktenbestätigung nötig")
        self.assertEqual(str(_ergebnis(c, llm).kern_protokoll.get("abgabe")), "73.50")

    def test_ohne_zweck_fragt_das_system(self):
        llm, a = _start("2026 haben wir einem freien Grafiker 1.500 € für Logo und Flyer gezahlt. Wir sind eine Bäckerei.")
        self.assertEqual(a.ergebnisklasse, "Rückfrage nötig")


class VerlagMitEigenwerbung(unittest.TestCase):
    TEXT = "Wir sind ein Buchverlag und lassen Flyer für die eigene Werbung gestalten. 2026 zahlten wir einer freien Illustratorin 300 €."

    def test_bleibt_typischer_verwerter(self):
        llm, a = _start(self.TEXT, unternehmensart="Buchverlag", positionen=[{"betrag": 300, "bezeichnung": "Flyer"}])
        self.assertIn("Rechtliche Einordnung (Vorschlag des Systems, keine Angabe von Ihnen): Typischer Verwerter", a.fakten_zusammenfassung)
        self.assertTrue(any("„Buchverlag“" in z for z in a.fakten_zusammenfassung))
        self.assertEqual(_ergebnis(a, llm).ergebnisklasse, "Abgabepflichtig (Vorschlag)")  # keine Schwelle

    def test_knopf_eigenwerbung_widerspricht_dem_verlag(self):
        llm, a = _start(self.TEXT, unternehmensart="Buchverlag", positionen=[{"betrag": 300, "bezeichnung": "Flyer"}])
        b = router.wende_feldantwort_an(a.sitzungskennung, "verwerterart", "eigenwerber", llm)
        self.assertEqual(b.ergebnisklasse, "Rückfrage nötig")
        self.assertIn("„Buchverlag“", b.rueckfragen[0])


class AgenturMitKundenauftrag(unittest.TestCase):
    TEXT = "Unsere Werbeagentur hat 2026 für einen Kunden einen freien Texter mit 800 € beauftragt."

    def test_typischer_verwerter(self):
        llm, a = _start(self.TEXT, unternehmensart="Werbeagentur", auftragszweck="fuer_kunden",
                        positionen=[{"betrag": 800, "bezeichnung": "Texte"}])
        self.assertIn("Rechtliche Einordnung (Vorschlag des Systems, keine Angabe von Ihnen): Typischer Verwerter", a.fakten_zusammenfassung)
        self.assertEqual(str(_ergebnis(a, llm).kern_protokoll.get("abgabe")), "39.20")

    def test_zweck_fuer_kunden_aber_katalog_verneint_bleibt_offen(self):
        f = leite_ab(Fakten(auftragszweck="fuer_kunden", katalog_taetigkeit=False))
        self.assertIsNone(f.verwerterart)


class PrivaterAuftrag(unittest.TestCase):
    TEXT = "Ich habe 2026 privat für meine Hochzeitsfeier eine Band für 1.200 € gebucht."

    def test_nicht_abgabepflichtig(self):
        llm, a = _start(self.TEXT, positionen=[{"betrag": 1200, "bezeichnung": "Band"}])
        self.assertIn("Rechtliche Einordnung (Vorschlag des Systems, keine Angabe von Ihnen): Privatperson (kein Unternehmen)", a.fakten_zusammenfassung)
        self.assertEqual(_ergebnis(a, llm).ergebnisklasse, "Nicht abgabepflichtig (Vorschlag)")

    def test_knopf_typischer_verwerter_widerspricht(self):
        llm, a = _start(self.TEXT, positionen=[{"betrag": 1200, "bezeichnung": "Band"}])
        b = router.wende_feldantwort_an(a.sitzungskennung, "verwerterart", "typischer_verwerter", llm)
        self.assertEqual(b.ergebnisklasse, "Rückfrage nötig")
        self.assertIn("Welche Angabe stimmt?", b.rueckfragen[0])


class AlteKategorieNurAbgeleitet(unittest.TestCase):
    def test_kategorie_folgt_den_fakten(self):
        f = erfasse("Wir machen Werbung für unser eigenes Geschäft.", Fakten(verwerterart="typischer_verwerter"))
        self.assertEqual((f.auftragszweck, f.verwerterart), ("eigene_werbung", "eigenwerber"))
        self.assertEqual(f.herkunft["auftragszweck"].art, "text")

    def test_modell_lesart_ohne_beleg_gilt_nicht(self):
        """Bis 17.10.2026 galt eine Lesart des Modells ohne Beleg im Text (sichtbar als 'bitte prüfen'). Entscheidung des
        Nutzers (17.10.2026, „Geratenen Zweck immer nachfragen“): sie gilt nicht, das System fragt nach dem Zweck."""
        f = erfasse("2026 zahlten wir 900 Euro an einen Grafiker.", Fakten(verwerterart="eigenwerber"))
        self.assertIsNone(f.auftragszweck)
        self.assertNotIn("auftragszweck", f.herkunft)
        self.assertIsNone(f.verwerterart)
        self.assertIn(pflichtangaben.FRAGE_ZWECK, pflichtangaben.fehlende_pflichtangaben(
            f.model_copy(update={"jahr": 2026, "auftragnehmer_typ": "natuerliche_person",
                                 "gesamtbetrag_genannt": 900, "taetigkeit_id": "T-02"}), alle=True))

    def test_veranstaltung_mit_anzahl_im_text_bleibt(self):
        f = erfasse("2025, vier Konzerte, Summe 2000 Euro.", Fakten(verwerterart="generalklausel"))
        self.assertEqual((f.auftragszweck, f.verwerterart), ("veranstaltung", "generalklausel"))
        g = erfasse("GmbH, 30-Jahr-Feier 2026, Band 1.900 EUR, Firmenveranstaltung.", Fakten(auftragszweck="veranstaltung"))
        self.assertIsNone(g.verwerterart, "Zusammensetzung wie 'Firmenveranstaltung' nennt keine Anzahl")


class ZusatzfrageAendertDasFalljahrNicht(unittest.TestCase):
    def test_abgabesatz_2025_neben_dem_fall_2026(self):
        text = (BAECKEREI + "\n„Wie hoch ist der Abgabesatz 2025?“\n„Gibt es ein Urteil zu Werbeagenturen?“\n"
                "„Wie hoch ist die Hundesteuer in Köln?“")
        llm = FakeLLM()
        llm.registriere(BAECKEREI, Fakten.model_validate({**GRUND, "positionen": [{"betrag": 1500, "bezeichnung": "Logo"}]}))
        a = warteschlange.bearbeite_nachricht(text, llm)
        stand = bestaetigung.SPEICHER.hole_fakten(a.sitzungskennung)
        self.assertEqual(stand.jahr, 2026)
        self.assertEqual(stand.verwerterart, "eigenwerber")


class AnnahmeUndGegenpruefung(unittest.TestCase):
    """Diskussion 16.10.2026, Punkte 3 und 5: die Umsatzsteuer-Annahme steht in der Bestätigung; bei einer reinen
    Auskunft heißt es nicht „nachgerechnet“, sondern „aus dem Regelregister gelesen“."""

    def test_umsatzsteuer_annahme_sichtbar(self):
        llm, a = _start(BAECKEREI)
        self.assertTrue(any(z.startswith("Annahme: In den Beträgen ist keine gesondert ausgewiesene Umsatzsteuer")
                            for z in a.fakten_zusammenfassung), a.fakten_zusammenfassung)

    def test_keine_annahme_wenn_umsatzsteuer_genannt(self):
        f = Fakten.model_validate({**GRUND, "positionen": [{"betrag": 1000}, {"betrag": 190, "rolle": "ust"}]})
        self.assertFalse(any(z.startswith("Annahme:") for z in bestaetigung.als_liste(f)))

    def test_auskunft_wird_nachgeschlagen_nicht_nachgerechnet(self):
        from app import gegenrechnung as G

        llm = FakeLLM()
        a = router.bearbeite_frage("Wie hoch ist der Abgabesatz 2025?", llm)
        e = _ergebnis(a, llm)
        self.assertIn(G.ZEILE_NACHGESCHLAGEN, e.antwort)
        self.assertNotIn("nachgerechnet", e.antwort)
        llm2, b = _start(BAECKEREI)
        self.assertIn(G.ZEILE_BESTAETIGT, _ergebnis(b, llm2).antwort, "eine echte Rechnung bleibt „nachgerechnet“")


class ModellfehlerF04(unittest.TestCase):
    """Modellfehler-Protokoll 16.10.2026 (KB-0491/0521, Antworten des Modells nachgebildet): der ganze Bruttobetrag als
    Umsatzsteuer, die enthaltene Umsatzsteuer fehlt; dazu 'Werbung für MEIN eigenes Unternehmen' / 'eigenes Haus'."""
    HOTEL = ("Wir sind ein Hotel und werben mit der Leistung für unser eigenes Haus. 2024 haben wir einer freien "
             "Illustratorin (Einzelperson) für Illustrationen für eine Broschüre 1.071,00 Euro brutto gezahlt, darin "
             "171 EUR Umsatzsteuer gesondert ausgewiesen. Ist das abgabepflichtig?")

    def _lauf(self, text, positionen, jahr):
        llm = FakeLLM()
        llm.registriere(text, Fakten.model_validate({"anfrageart": "bewertung", "jahr": jahr, "ein_auftragnehmer": True,
                                                     "positionen": positionen,
                                                     "rechnungen": [{"auftragnehmer_nr": 1,
                                                                     "gesamtbetrag": positionen[0]["betrag"]}]}))
        return _ergebnis(router.bearbeite_frage(text, llm), llm)

    def test_ganzer_betrag_als_umsatzsteuer(self):
        e = self._lauf(self.HOTEL, [{"betrag": "1071", "rolle": "ust", "auftragnehmer_nr": 1},
                                    {"betrag": "0", "rest": True, "auftragnehmer_nr": 1,
                                     "bezeichnung": "Illustrationen"}], 2024)
        self.assertEqual(str(e.kern_protokoll.get("abgabe")), "45.00")

    def test_umsatzsteuer_fehlt_ganz(self):
        e = self._lauf(self.HOTEL, [{"betrag": "1071", "bezeichnung": "Illustrationen", "auftragnehmer_nr": 1}], 2024)
        self.assertEqual(str(e.kern_protokoll.get("abgabe")), "45.00")

    def test_eigenwerbung_mit_anderen_worten(self):
        from app.zuordnung import eigenwerbung_muster

        self.assertEqual(eigenwerbung_muster("Ich lasse Werbung für mein eigenes Unternehmen machen."),
                         "für mein eigenes Unternehmen")
        self.assertEqual(eigenwerbung_muster(self.HOTEL), "für unser eigenes Haus")
        # Gegenbeispiele: Werbung für Kunden ist keine Eigenwerbung; ohne Werbewort zählt die Wendung nicht.
        self.assertIsNone(eigenwerbung_muster("Wir machen Werbung für unsere Kunden."))
        self.assertIsNone(eigenwerbung_muster("Ich habe für meine eigene Hochzeit eine Band gebucht."))


if __name__ == "__main__":
    unittest.main()
