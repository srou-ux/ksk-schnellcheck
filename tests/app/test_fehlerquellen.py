"""Fehlerquellen-Serie HT-2026-062 bis 111 des Nutzers (15.10.2026): Prüfungen ohne Sprachmodell.

Katalog: aufgaben/audit/fehlerquellen_ht_062_111.json. Hier nur die festen Prüfungen, die bei der Soll-Prüfung
aufgefallen sind (die Live-Messung läuft über den Workflow 'Chatbot direkt').
"""
from __future__ import annotations

import unittest
from decimal import Decimal as D

from app import bestaetigung, router, zuordnung
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position as P
from tests.app.zweck_knopf import mit_zweck  # Entscheidung 17.10.2026: geratener Zweck wird per Knopf bestätigt


def _ende(frage: str, fakten: dict):
    """Eine Frage mit nachgebildeter Modellantwort; Faktenbestätigung wird bestätigt."""
    llm = FakeLLM()
    llm.registriere(frage, Fakten.model_validate(fakten))
    a = mit_zweck(router.bearbeite_frage(frage, llm), fakten, llm)
    if a.ergebnisklasse != "Faktenbestätigung nötig":
        return a
    bestaetigung.SPEICHER.bestaetige(a.sitzungskennung, a.fakten_hash)
    return router.fuehre_nach_bestaetigung_aus(a.sitzungskennung, FakeLLM())


def _rollen(text: str, betraege: list[str]) -> list:
    f = zuordnung.ergaenze_reisekosten_rolle(text, Fakten(positionen=[P(betrag=D(b)) for b in betraege]))
    return [p.rolle for p in f.positionen]


class FahrtkostenMitNachweis(unittest.TestCase):
    def test_ht_088_beleg_weiter_weg_im_selben_satz(self):
        self.assertEqual(_rollen("Honorar 2.000 EUR an Musiker 2026. Fahrt 300 km mit Einzelbelegen (Logbuch) "
                                 "erstattet: 90 EUR.", ["2000", "90"]), [None, "fahrtkosten_nachgewiesen"])

    def test_honorar_wird_nie_fahrtkosten(self):
        # Ältere Lücke des 30-Zeichen-Fensters: 'Honorar 2.000 EUR inklusive Fahrt mit Beleg'.
        self.assertEqual(_rollen("Honorar 2.000 EUR inklusive Fahrt mit Beleg.", ["2000"]), [None])

    def test_pauschale_bleibt_pauschale(self):
        self.assertEqual(_rollen("Honorar 2.000 EUR. Fahrtkostenpauschale 300 km mit Beleg: 90 EUR.",
                                 ["2000", "90"]), [None, None])

    def test_p30_unveraendert(self):
        self.assertEqual(_rollen("Honorar 1.500 €, dazu 80 € nachgewiesene Bahnfahrtkosten.", ["1500", "80"]),
                         [None, "fahrtkosten_nachgewiesen"])

    def test_satzende_nach_jahreszahl(self):
        self.assertEqual(len([s for s in zuordnung._SATZ_GRENZE.split("Zahlung 2026. Fahrt 90 EUR.") if s.strip()]), 2)
        self.assertEqual(len([s for s in zuordnung._SATZ_GRENZE.split("am 03.01.2020 mit 1.500 EUR") if s.strip()]), 1)


class LiveFundeFehlerquellen(unittest.TestCase):
    """Nachgebildete Modellantworten aus dem Live-Lauf 'Chatbot direkt' (17010bf, 15.10.2026), wie sie in der
    Faktenbestätigung standen."""

    def test_ht_069_gmbh_nur_bei_ihrer_position(self):
        frage = ("2026 gezahlt: an Fotograf Weber 1.100 EUR, an die Weber Fotodesign GmbH fuer Retusche 900 EUR, an "
                 "Fotograf Weber nochmal 400 EUR fuer Folgearbeiten.")
        roh = {"jahr": 2026, "verwerterart": "typischer_verwerter", "positionen": [
            {"betrag": "1100", "bezeichnung": "Fotografie", "auftragnehmer_typ": "GmbH_UG_AG", "auftragnehmer_nr": 1},
            {"betrag": "900", "bezeichnung": "Retusche", "auftragnehmer_typ": "GmbH_UG_AG", "auftragnehmer_nr": 2},
            {"betrag": "400", "bezeichnung": "Folgearbeiten", "auftragnehmer_typ": "GmbH_UG_AG", "auftragnehmer_nr": 1}]}
        f = zuordnung.rechtsform_nur_wo_genannt(frage, Fakten.model_validate(roh))
        self.assertEqual([p.auftragnehmer_typ for p in f.positionen], [None, "GmbH_UG_AG", None])
        ende = _ende(frage, roh)
        self.assertNotEqual(ende.ergebnisklasse, "Nicht abgabepflichtig (Vorschlag)")

    def test_ht_069_mit_knopf_natuerliche_person(self):
        frage = ("2026 gezahlt: an Fotograf Weber 1.100 EUR, an die Weber Fotodesign GmbH fuer Retusche 900 EUR, an "
                 "Fotograf Weber nochmal 400 EUR fuer Folgearbeiten.")
        # wie live: das Modell ordnete 1.100 € und 400 € als Fotografie (T-04) ein
        roh = {"jahr": 2026, "verwerterart": "typischer_verwerter", "auftragnehmer_typ": "natuerliche_person", "positionen": [
            {"betrag": "1100", "bezeichnung": "Fotografie", "auftragnehmer_typ": "GmbH_UG_AG", "auftragnehmer_nr": 1,
             "taetigkeit_id": "T-04"},
            {"betrag": "900", "bezeichnung": "Retusche", "auftragnehmer_typ": "GmbH_UG_AG", "auftragnehmer_nr": 2},
            {"betrag": "400", "bezeichnung": "Folgearbeiten Fotografie", "auftragnehmer_typ": "GmbH_UG_AG",
             "auftragnehmer_nr": 1, "taetigkeit_id": "T-04"}]}
        ende = _ende(frage, roh)
        self.assertEqual(ende.ergebnisklasse, "Abgabepflichtig (Vorschlag)")
        self.assertEqual(ende.kern_protokoll.get("abgabe"), D("73.50"))

    def test_kopfzeile_gilt_fuer_alle(self):
        frage = "Rechnung der Studio Licht GmbH:\n- Fotos 800 EUR\n- Retusche 200 EUR"
        f = Fakten(positionen=[P(betrag=D("800"), auftragnehmer_typ="GmbH_UG_AG"),
                               P(betrag=D("200"), auftragnehmer_typ="GmbH_UG_AG")])
        g = zuordnung.rechtsform_nur_wo_genannt(frage, f)
        self.assertEqual([p.auftragnehmer_typ for p in g.positionen], ["GmbH_UG_AG", "GmbH_UG_AG"])

    def test_ht_099_gmbh_ist_der_auftraggeber(self):
        frage = ("Antworte nur als JSON mit: jahr, anzahl_rechnungen, betrag_je_rechnung_eur, werbezweck. -- 2000 euro an "
                 "einen Kuenstler gezahlt, 2026, GmbH.")
        roh = {"jahr": 2026, "verwerterart": "eigenwerber", "auftragnehmer_typ": "natuerliche_person",
               "auftraggeber_typ": "GmbH_UG_AG", "positionen": [{"betrag": "2000", "auftragnehmer_typ": "GmbH_UG_AG"}]}
        f = zuordnung.rechtsform_nur_wo_genannt(frage, Fakten.model_validate(roh))
        self.assertIsNone(f.positionen[0].auftragnehmer_typ)
        self.assertNotEqual(_ende(frage, roh).ergebnisklasse, "Nicht abgabepflichtig (Vorschlag)")

    def test_ht_072_galerie_nur_im_namen(self):
        frage = ("Die 'Galerie Hoffmann' (Verein, macht nichts Kunstbezogenes - ein Schreinerverein) zahlte 2026 an einen "
                 "freien Musiker 900 EUR fuer ein Vereinsfest.")
        f = zuordnung.absichere_verwerterart(frage, Fakten(verwerterart="typischer_verwerter"))
        self.assertIsNone(f.verwerterart)
        # ohne Anführungszeichen bleibt die Galerie ein typischer Verwerter
        g = zuordnung.absichere_verwerterart("Wir sind eine Galerie und zahlten 900 EUR.", Fakten())
        self.assertEqual(g.verwerterart, "typischer_verwerter")

    def test_ht_087_pauschale_ist_keine_zahlung(self):
        frage = ("Zahlung 2026 an Chorleiter: 3.500 EUR, daneben uebt er bei uns nebenberuflich als Chorleiter "
                 "(Uebungsleiterpauschale 3.300 EUR anrechenbar).")
        roh = {"jahr": 2026, "anfrageart": "uebungsleiter_pauschale", "pauschale_art": "uebungsleiter",
               "pauschale_bereits_ausgeschoepft": "3300", "ein_auftragnehmer": True, "positionen": [
                   {"betrag": "3500", "bezeichnung": "Zahlung an Chorleiter"},
                   {"betrag": "3300", "bezeichnung": "Übungsleiterpauschale anrechenbar"}]}
        f = zuordnung.ergaenze_pauschale(frage, Fakten.model_validate(roh))
        self.assertEqual([p.betrag for p in f.positionen], [D("3500")])
        self.assertIsNone(f.pauschale_bereits_ausgeschoepft)
        ende = _ende(frage, roh)
        self.assertNotEqual(ende.kern_protokoll.get("abgabe") if ende.kern_protokoll else None, D("333.20"))

    def test_ht_094_jahr_im_text(self):
        f = zuordnung.jahr_aus_freier_jahreszahl("Ist die Abgabe nach Paragraph 24 Abs. 2 KSVG 2026 4,9 Prozent?", Fakten())
        self.assertEqual(f.jahr, 2026)
        self.assertIsNone(zuordnung.jahr_aus_freier_jahreszahl("Wir zahlten 2026 und 2025.", Fakten()).jahr)
        self.assertIsNone(zuordnung.jahr_aus_freier_jahreszahl("Wir zahlten 2020 EUR.", Fakten()).jahr)


class GesamtlaufB87a9bb(unittest.TestCase):
    """Zwei FALSCH-Fälle im Gesamtlauf b87a9bb (15.10.2026), Fakten wie in der Faktenbestätigung."""

    def test_p16_dirigent_mit_rolle_honorar(self):
        frage = ("Unser Hobbyorchester-Verein hatte 2026 vier Konzerte mit Eintritt. Wir haben einem selbständigen "
                 "Gastsolisten 800 € gezahlt und unserem vereinseigenen Dirigenten 1.500 €. Abgabepflichtig?")
        roh = {"jahr": 2026, "leistungsart": "Musik", "verwerterart": "generalklausel", "auftraggeber_typ": "Verein",
               "veranstaltungszahl": 4, "einnahmeabsicht": True, "ein_auftragnehmer": False,
               "auftragnehmer_typ": "natuerliche_person", "positionen": [
                   {"betrag": "800", "bezeichnung": "Gastsolist", "auftragnehmer_nr": 1, "rolle": "honorar",
                    "taetigkeit_id": "T-10"},
                   {"betrag": "1500", "bezeichnung": "vereinseigener Dirigent", "auftragnehmer_nr": 2,
                    "rolle": "honorar", "taetigkeit_id": "T-11"}]}
        ende = _ende(frage, roh)
        self.assertEqual(ende.ergebnisklasse, "Nicht abgabepflichtig (Vorschlag)")

    def test_ht_074_ausschluss_nur_mit_beleg(self):
        from app import taetigkeiten as T
        self.assertEqual(T.kombiniere("T-40", None, True), T.UNBEKANNT)      # nur das Modell sagt 'Druck'
        self.assertEqual(T.kombiniere("T-40", "T-40", True), "T-40")         # Beleg im Text: bleibt
        frage = ("Verein (Eigenwerbung-Fall), 2026: keine einzige Veranstaltung gemacht, aber 2.500 EUR fuer "
                 "Kunstdrucke fuer unsere Werbung bezahlt.")
        roh = {"jahr": 2026, "leistungsart": "Kunstdrucke", "verwerterart": "eigenwerber",
               "auftragnehmer_typ": "natuerliche_person", "veranstaltungszahl": 0, "gesamtbetrag_genannt": "2500",
               "taetigkeit_id": "T-40"}
        self.assertNotEqual(_ende(frage, roh).ergebnisklasse, "Nicht abgabepflichtig (Vorschlag)")


class RechtsformJeBetragImSatz(unittest.TestCase):
    """HT-2026-089 (Gesamtlauf 301eb97): das Modell lieferte keine Rechtsform je Position; beide in EINEM Satz."""

    def test_wie_live(self):
        frage = ("2026 an eine GmbH fuer Video-Produktion 1.500 EUR und an einen freien Kameramann 1.000 EUR gezahlt "
                 "(wir: Agentur, typischer Verwerter).")
        roh = {"jahr": 2026, "verwerterart": "typischer_verwerter", "positionen": [
            {"betrag": "1500", "bezeichnung": "Video-Produktion", "auftragnehmer_nr": 1},
            {"betrag": "1000", "bezeichnung": "freier Kameramann", "auftragnehmer_nr": 2}]}
        ende = _ende(frage, roh)
        self.assertEqual(ende.kern_protokoll.get("bemessungsgrundlage"), D("1000"))
        self.assertEqual(ende.kern_protokoll.get("abgabe"), D("49.00"))


class AnzahlJeBetrag(unittest.TestCase):
    """HT-2026-105 (Gesamtlauf 225f380): 'fünf Rechnungen … je 250 EUR', das Modell legte EINE Position an."""

    def test_wie_live(self):
        frage = "2026: fuenf Rechnungen an denselben Kuenstler, je 250 EUR."
        roh = {"jahr": 2026, "verwerterart": "eigenwerber", "auftragnehmer_typ": "natuerliche_person",
               "leistungsart": "Illustration", "ein_auftragnehmer": True,
               "positionen": [{"betrag": "250", "bezeichnung": "Illustrationen für Werbung", "auftragnehmer_nr": 1}],
               "rechnungen": [{"auftragnehmer_nr": 1, "gesamtbetrag": "250"}]}
        ende = _ende(frage, roh)
        self.assertEqual(ende.kern_protokoll.get("bemessungsgrundlage"), D("1250"))
        self.assertEqual(ende.kern_protokoll.get("abgabe"), D("61.25"))

    def test_nur_wenn_eindeutig(self):
        f = Fakten(positionen=[P(betrag=D("250"))])
        self.assertEqual(len(zuordnung.anzahl_je_betrag("Drei Zahlungen 2026 je 250 €.", f).positionen), 3)
        self.assertEqual(len(zuordnung.anzahl_je_betrag("Drei Zahlungen 2026 je 300 €.", f).positionen), 1)  # anderer Betrag
        zwei = Fakten(positionen=[P(betrag=D("250")), P(betrag=D("100"))])
        self.assertEqual(len(zuordnung.anzahl_je_betrag("Drei Zahlungen je 250 €.", zwei).positionen), 2)  # nicht eindeutig


class ZweiterVersuchMitSchema(unittest.TestCase):
    """Live 15.10.2026 (HT-063, HT-008): kaputtes JSON '"positionen": [ },' bei temperature 0, auch im zweiten
    Versuch. Der zweite Versuch verlangt jetzt das strukturierte Format (json_schema, strict)."""

    def test_zweiter_versuch_schickt_das_schema(self):
        import json
        from app.llm import mistral

        llm = mistral.MistralLLM(api_key="nur-test-kein-schluessel")  # es wird nie gesendet
        gesehen = []

        def aufruf(system, user, max_tokens=None, json_objekt=False, schema=None):
            gesehen.append(schema is not None)
            return '{"jahr": 2026, "positionen": [ },' if not gesehen[1:] else json.dumps({"jahr": 2026})

        llm._aufruf = aufruf  # type: ignore[method-assign]
        fakten = llm.extrahiere_fakten("Wir haben 2026 einem Maler 2.000 EUR gezahlt.")
        self.assertEqual(gesehen, [False, True])
        self.assertEqual(fakten.jahr, 2026)

    def test_diagnose_ohne_inhalte(self):
        from app.llm import mistral
        stelle = mistral._maskiert('"positionen": [ {"bezeichnung": "Anna Muster"} },', mistral._erlaubte_namen())
        self.assertNotIn("Anna", stelle)
        self.assertIn("positionen", stelle)


if __name__ == "__main__":
    unittest.main()
