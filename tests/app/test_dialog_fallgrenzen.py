"""Dialogtest Fallgrenzen (10.10.2026): ganzer Gesprächsverlauf offline mit KONTROLLIERTEN
Modellantworten -- Ausgangsfall, Korrektur, ausdrücklich neuer Fall, Ergänzung fehlender
Angaben. Das Testdoppel liefert wie ein ideales Modell nur, was in der jeweiligen Nachricht
ausdrücklich steht; so prüfen die Tests allein den Python-Ablauf (Sitzung, Zusammenführung,
Pflichtangaben, Kernaufruf). Erfundene Daten.

Reproduziert (vorher): Beim 'Neuen, unabhängigen Fall' übernahm die Sitzung Jahr 2026,
Eigenwerbung, Rechtsform und die drei alten Rechnungen zu je 200 € in den neuen Fall; ein
genannter Gesamtbetrag ohne Aufteilung wurde ignoriert und erneut nach dem Betrag gefragt.
"""
from __future__ import annotations

import unittest
from decimal import Decimal

from app import bestaetigung, router, zuordnung
from app import ergebnisklassen as EK
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position

M1 = "Wir haben 2026 für unsere eigene Werbung vier Grafiken beauftragt. Jede Rechnung beträgt 200 Euro netto."
M2 = "Korrektur: Es waren drei Rechnungen. Alle anderen Angaben bleiben gleich."
M3 = ("Neuer, unabhängiger Fall: Ein Fotograf hat insgesamt 500 Euro netto berechnet. Ob sich dieser "
      "Betrag auf eine oder mehrere Rechnungen verteilt, ist unbekannt. Auch Jahr und Verwendungszweck "
      "sind unbekannt.")
M4 = "Das war 2025, für unsere eigene Werbung, der Fotograf ist Einzelperson."


def _pos(betrag: str) -> Position:
    return Position(betrag=Decimal(betrag), rolle="honorar")


class _MitschnittLLM(FakeLLM):
    """FakeLLM mit festen Antworten je Nachricht, das zusätzlich mitschreibt, welchen Verlauf
    es bekommen hat (damit prüfbar ist, dass ein alter Fall nicht ans Modell geht)."""

    def __init__(self) -> None:
        super().__init__()
        self.verlaeufe: list[list[str]] = []

    def extrahiere_fakten(self, frage, verlauf=None):
        self.verlaeufe.append(list(verlauf or []))
        return super().extrahiere_fakten(frage, verlauf)


def _modell() -> _MitschnittLLM:
    llm = _MitschnittLLM()
    llm.registriere(M1, Fakten(anfrageart="bewertung", jahr=2026, verwerterart="eigenwerber",
                               leistungsart="Grafik/Design", positionen=[_pos("200")] * 4))
    llm.registriere(M2, Fakten(anfrageart="bewertung", jahr=2026, verwerterart="eigenwerber",
                               leistungsart="Grafik/Design", positionen=[_pos("200")] * 3))
    llm.registriere(M3, Fakten(anfrageart="bewertung", leistungsart="Fotografie",
                               gesamtbetrag_genannt=Decimal("500")))
    llm.registriere(M4, Fakten(anfrageart="bewertung", jahr=2025, verwerterart="eigenwerber",
                               auftragnehmer_typ="natuerliche_person"))
    return llm


class _Oberflaeche:
    """Verhält sich wie app/static/index.html: schickt den bisherigen Verlauf und die zuletzt
    erhaltene Sitzungskennung mit."""

    def __init__(self, llm) -> None:
        self.llm, self.verlauf, self.sitzung = llm, [], None

    def sende(self, text: str):
        antwort = router.bearbeite_frage(text, self.llm, list(self.verlauf), self.sitzung)
        self.verlauf.append(text)
        self.sitzung = antwort.sitzungskennung
        return antwort

    def knopf(self, feld: str, wert, position=None):
        antwort = router.wende_feldantwort_an(self.sitzung, feld, wert, self.llm, position)
        self.sitzung = antwort.sitzungskennung
        return antwort


class TestDialogVerlauf(unittest.TestCase):
    def setUp(self) -> None:
        self.llm = _modell()
        self.ui = _Oberflaeche(self.llm)

    def _bis_korrektur(self):
        erste = self.ui.sende(M1)
        self.assertEqual(erste.ergebnisklasse, EK.RUECKFRAGE_NOETIG)
        bestaetigung_1 = self.ui.knopf("auftragnehmer_typ", "natuerliche_person")
        self.assertEqual(bestaetigung_1.ergebnisklasse, EK.FAKTEN_BESTAETIGUNG_NOETIG)
        self.assertEqual(sum(z.startswith("Position ") for z in bestaetigung_1.fakten_zusammenfassung), 4)
        korrektur = self.ui.sende(M2)
        return bestaetigung_1, korrektur

    def test_korrektur_aendert_nur_die_rechnungszahl_und_macht_bestaetigung_ungueltig(self):
        vorher, korrektur = self._bis_korrektur()
        self.assertEqual(korrektur.ergebnisklasse, EK.FAKTEN_BESTAETIGUNG_NOETIG)
        liste = korrektur.fakten_zusammenfassung
        self.assertEqual(sum(z.startswith("Position ") for z in liste), 3)
        for bleibt in ("Jahr: 2026", "Rechtliche Einordnung (Vorschlag des Systems, keine Angabe von Ihnen): Eigenwerbung", "Auftragnehmer: natürliche Person"):
            self.assertIn(bleibt, liste)
        self.assertEqual(korrektur.sitzungskennung, vorher.sitzungskennung)
        self.assertNotEqual(korrektur.fakten_hash, vorher.fakten_hash)
        self.assertFalse(bestaetigung.SPEICHER.bestaetige(korrektur.sitzungskennung, vorher.fakten_hash))

    def test_neuer_fall_uebernimmt_nichts_aus_dem_alten_fall(self):
        _, korrektur = self._bis_korrektur()
        neu = self.ui.sende(M3)
        self.assertNotEqual(neu.sitzungskennung, korrektur.sitzungskennung)
        self.assertEqual(neu.ergebnisklasse, EK.RUECKFRAGE_NOETIG)
        self.assertIn(EK.RUECKFRAGE_NOETIG, neu.ergebnisklasse)
        gespeichert = bestaetigung.SPEICHER.hole_fakten(neu.sitzungskennung)
        self.assertIsNone(gespeichert.jahr)
        self.assertIsNone(gespeichert.verwerterart)
        self.assertIsNone(gespeichert.auftragnehmer_typ)
        self.assertEqual(gespeichert.positionen, [], "keine Rechnungsposition erfunden oder übernommen")
        self.assertEqual(gespeichert.gesamtbetrag_genannt, Decimal("500"))
        self.assertEqual(self.llm.verlaeufe[-1], [], "der alte Fall darf nicht ans Modell gehen")

    def test_ergaenzung_nutzt_gesamtbetrag_ohne_erfundene_position(self):
        self._bis_korrektur()
        self.ui.sende(M3)
        ergaenzt = self.ui.sende(M4)
        self.assertEqual(self.llm.verlaeufe[-1], [M3], "nur der Verlauf des neuen Falls")
        self.assertEqual(ergaenzt.ergebnisklasse, EK.FAKTEN_BESTAETIGUNG_NOETIG)
        liste = ergaenzt.fakten_zusammenfassung
        self.assertIn("Jahr: 2025", liste)
        self.assertFalse(any(z.startswith("Position ") for z in liste), liste)
        self.assertTrue(any(z.startswith("Gesamtbetrag (Aufteilung auf Rechnungen unbekannt): 500,00 €") for z in liste), liste)
        self.assertTrue(bestaetigung.SPEICHER.bestaetige(ergaenzt.sitzungskennung, ergaenzt.fakten_hash))
        ergebnis = router.fuehre_nach_bestaetigung_aus(ergaenzt.sitzungskennung, self.llm)
        # 2025: Eigenwerbung, 500 € übersteigen die Schwelle des Jahres nicht (Soll wie Q-01/K-04).
        self.assertEqual(ergebnis.ergebnisklasse, EK.NICHT_ABGABEPFLICHTIG)

    def test_knopf_nach_neuem_fall_wirkt_nur_im_neuen_fall(self):
        _, korrektur = self._bis_korrektur()
        neu = self.ui.sende(M3)
        router.wende_feldantwort_an(neu.sitzungskennung, "jahr", 2026, self.llm)
        alt = bestaetigung.SPEICHER.hole_fakten(korrektur.sitzungskennung)
        self.assertEqual(len(alt.positionen), 3)
        self.assertIsNone(alt.gesamtbetrag_genannt)


class TestTextpruefungenNurImEigenenFall(unittest.TestCase):
    def test_verlag_aus_altem_fall_bestimmt_nicht_den_neuen_fall(self):
        alt = "Wir sind ein Buchverlag und haben 2026 einer freien Grafikerin 300 € gezahlt."
        neu = "Neuer Fall: Unsere Firma hat 2026 für eigene Werbung einem Fotografen insgesamt 900 € gezahlt."
        llm = _MitschnittLLM()
        llm.registriere(alt, Fakten(anfrageart="bewertung", jahr=2026, positionen=[_pos("300")]))
        llm.registriere(neu, Fakten(anfrageart="bewertung", jahr=2026, verwerterart="eigenwerber",
                                    gesamtbetrag_genannt=Decimal("900")))
        ui = _Oberflaeche(llm)
        ui.sende(alt)
        antwort = ui.sende(neu)
        fakten = bestaetigung.SPEICHER.hole_fakten(antwort.sitzungskennung)
        self.assertEqual(fakten.verwerterart, "eigenwerber", "'Verlag' aus dem alten Fall darf nicht gewinnen")
        self.assertIsNone(fakten.auftragnehmer_typ, "'freie' aus dem alten Fall darf keine Rechtsform setzen")


class TestGesamtbetrag(unittest.TestCase):
    def test_gesamtbetrag_typischer_verwerter_ohne_aufteilung(self):
        frage = "Unsere Werbeagentur hat 2026 einem freien Grafiker insgesamt 500 € gezahlt, Rechnungen unbekannt."
        llm = FakeLLM()
        llm.registriere(frage, Fakten(anfrageart="bewertung", jahr=2026, verwerterart="typischer_verwerter",
                                      auftragnehmer_typ="natuerliche_person", gesamtbetrag_genannt=Decimal("500")))
        erste = router.bearbeite_frage(frage, llm)
        self.assertEqual(erste.ergebnisklasse, EK.FAKTEN_BESTAETIGUNG_NOETIG)
        bestaetigung.SPEICHER.bestaetige(erste.sitzungskennung, erste.fakten_hash)
        ergebnis = router.fuehre_nach_bestaetigung_aus(erste.sitzungskennung, llm)
        self.assertEqual(ergebnis.ergebnisklasse, EK.ABGABEPFLICHTIG)
        self.assertEqual(Decimal(str(ergebnis.kern_protokoll["abgabe"])), Decimal("24.50"))

    def test_ohne_jeden_betrag_wird_weiter_nach_dem_betrag_gefragt(self):
        frage = "Ein Fotograf hat für uns 2026 gearbeitet."
        llm = FakeLLM()
        llm.registriere(frage, Fakten(anfrageart="bewertung", jahr=2026))
        antwort = router.bearbeite_frage(frage, llm)
        self.assertEqual(antwort.ergebnisklasse, EK.RUECKFRAGE_NOETIG)
        self.assertTrue(any("Betrag" in r for r in antwort.rueckfragen), antwort.rueckfragen)


class TestGesamtbetragNichtAlsErfundenePosition(unittest.TestCase):
    """Live-Befund (mistral-small-latest): Modell liefert zu 'insgesamt 500 Euro, Aufteilung
    unbekannt' zusätzlich eine Position über 500 € (kontrollierte Modellantwort nachgestellt)."""

    def _faktenliste(self, fakten: Fakten, frage: str) -> list[str]:
        llm = FakeLLM()
        llm.registriere(frage, fakten)
        return router.bearbeite_frage(frage, llm).fakten_zusammenfassung

    def test_eine_position_gleich_gesamtbetrag_wird_nicht_als_rechnung_gezeigt(self):
        liste = self._faktenliste(Fakten(
            anfrageart="bewertung", jahr=2025, verwerterart="eigenwerber",
            gesamtbetrag_genannt=Decimal("500"),
            positionen=[Position(betrag=Decimal("500"), rolle="honorar", auftragnehmer_typ="natuerliche_person")]),
            "Fotograf, insgesamt 500 Euro, 2025, eigene Werbung, Einzelperson")
        self.assertFalse(any(z.startswith("Position ") for z in liste), liste)
        # Seit der Tätigkeitsprüfung (11.10.2026) steht die Einordnung der Leistung mit in der Zeile.
        self.assertTrue(any(z.startswith("Gesamtbetrag (Aufteilung auf Rechnungen unbekannt): 500,00 €, natürliche Person")
                            for z in liste), liste)

    def test_darin_aufteilung_bleibt_unveraendert(self):
        """'1.800 Euro, darin 300 Euro Fahrtkosten' -- echte Aufteilung, nichts entfernen."""
        liste = self._faktenliste(Fakten(
            anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter", auftragnehmer_typ="natuerliche_person",
            gesamtbetrag_genannt=Decimal("1800"),
            positionen=[Position(betrag=Decimal("1500"), rolle="honorar"),
                        Position(betrag=Decimal("300"), rolle="fahrtkosten_nachgewiesen", nachgewiesen=True)]),
            "Grafikerin: 1.800 Euro, darin 300 Euro nachgewiesene Fahrtkosten, 2025, Werbeagentur, Einzelperson")
        self.assertEqual(sum(z.startswith("Position ") for z in liste), 2, liste)

    def test_abweichende_einzelposition_bleibt_und_warnt(self):
        liste = self._faktenliste(Fakten(
            anfrageart="bewertung", jahr=2025, verwerterart="eigenwerber", auftragnehmer_typ="natuerliche_person",
            gesamtbetrag_genannt=Decimal("500"), positionen=[Position(betrag=Decimal("400"), rolle="honorar")]),
            "Grafikerin: insgesamt 500 Euro, eine Rechnung über 400 Euro, 2025, eigene Werbung, Einzelperson")
        self.assertEqual(sum(z.startswith("Position ") for z in liste), 1, liste)
        self.assertTrue(any("passt nicht zum genannten Gesamtbetrag" in z for z in liste), liste)


class TestMehrereRechnungenEineVeranstaltung(unittest.TestCase):
    def test_vier_rechnungen_zu_einer_veranstaltung_zaehlen_als_eine_veranstaltung(self):
        """Generalklausel, EINE Veranstaltung, aber vier Rechnungen (Band, Technik ...): die
        Zahl der Rechnungen darf nicht als Zahl der Veranstaltungen gelten (Soll wie D-03:
        bis zu drei Veranstaltungen -> nicht abgabepflichtig)."""
        frage = "Wir hatten 2025 eine Veranstaltung mit Einnahmeabsicht; dafür kamen vier Rechnungen von Musikern über je 1.500 €."
        llm = FakeLLM()
        llm.registriere(frage, Fakten(anfrageart="bewertung", jahr=2025, verwerterart="generalklausel",
                                      veranstaltungszahl=1, einnahmeabsicht=True,
                                      auftragnehmer_typ="natuerliche_person", positionen=[_pos("1500")] * 4))
        erste = router.bearbeite_frage(frage, llm)
        self.assertEqual(erste.ergebnisklasse, EK.FAKTEN_BESTAETIGUNG_NOETIG)
        self.assertIn("Veranstaltungen: 1", erste.fakten_zusammenfassung)
        bestaetigung.SPEICHER.bestaetige(erste.sitzungskennung, erste.fakten_hash)
        ergebnis = router.fuehre_nach_bestaetigung_aus(erste.sitzungskennung, llm)
        self.assertEqual(ergebnis.ergebnisklasse, EK.NICHT_ABGABEPFLICHTIG)


class TestFallwechselErkennung(unittest.TestCase):
    def test_ausdrueckliche_ankuendigungen(self):
        for text in (M3, "Neuer Fall: ...", "neuer, unabhaengiger Fall", "Ein anderer Fall: ...", "Neue Frage: ..."):
            self.assertTrue(zuordnung.ist_neuer_fall(text), text)

    def test_korrektur_und_ergaenzung_sind_kein_neuer_fall(self):
        for text in (M2, M4, "Das war 2025.", "Es waren fünf Rechnungen.", "Der Fall ist so wie oben."):
            self.assertFalse(zuordnung.ist_neuer_fall(text), text)


if __name__ == "__main__":
    unittest.main()


class TestRechtsformNurDesAuftragnehmers(unittest.TestCase):
    """Prüfung SaaS gegen Playground-Fälle (10.10.2026): Rechtsform-Wörter, die die eigene
    Seite beschreiben, dürfen nicht als Rechtsform des Auftragnehmers gelten."""

    def test_erkennung(self):
        from app.rechtsform_erkennung import erkenne_rechtsform_auftragnehmer as erk
        faelle = {
            "Wir sind eine GmbH und haben einem Grafiker 2.000 Euro gezahlt.": None,
            "Unser Verein hatte 2025 vier Konzerte, Gagen zusammen 5.000 Euro.": None,
            "Wir haben die Grafik-GmbH mit 5.000 Euro bezahlt.": "GmbH_UG_AG",
            "Das war 2025, der Fotograf ist Einzelperson.": "natuerliche_person",
            "Unsere Werbeagentur hat einem freien Grafiker 900 Euro gezahlt.": "natuerliche_person",
            "Ich bin Einzelunternehmer und zahle einer Agentur GmbH 3.000 Euro.": "GmbH_UG_AG",
            "Eine GbR und eine GmbH haben je 1.000 Euro bekommen.": None,
        }
        for text, soll in faelle.items():
            self.assertEqual(erk(text), soll, text)

    def test_wir_sind_eine_gmbh_fuehrt_nicht_zu_nicht_abgabepflichtig(self):
        """Vorher: Grafiker als GmbH eingestuft -> 'Nicht abgabepflichtig'. Soll: Rechtsform
        unbekannt -> Rückfrage, kein sicheres Ergebnis."""
        frage = "Wir sind eine GmbH und haben 2026 für unsere eigene Werbung einem Grafiker 2.000 Euro gezahlt."
        llm = FakeLLM()
        llm.registriere(frage, Fakten(anfrageart="bewertung", jahr=2026, verwerterart="eigenwerber",
                                      positionen=[_pos("2000")]))
        antwort = router.bearbeite_frage(frage, llm)
        self.assertEqual(antwort.ergebnisklasse, EK.RUECKFRAGE_NOETIG)
        self.assertTrue(any("Rechtsform" in r for r in antwort.rueckfragen), antwort.rueckfragen)
