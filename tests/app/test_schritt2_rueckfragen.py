"""Schritt 2 (17.10.2026): Rückfragen nach Tatsachen und verständliche Faktenbestätigung.

Auftrag (vom Nutzer übermittelt, aufgaben/Arbeitsstand.md): der Nutzer wählt keine rechtliche Kategorie mehr
(„typischer Verwerter“, „Generalklausel“), sondern beantwortet „Wofür war dieser Auftrag gedacht?“. Die Einordnung
leitet das System ab (app/einordnung.py::leite_ab), der Kern rechnet erst nach „Ja, das stimmt“.
Modellantworten mit FakeLLM nachgebildet, erfundene Daten. Jahre und Beträge sind Testdaten, keine Regelwerte."""
from __future__ import annotations

import unittest
from decimal import Decimal as D

from app import bestaetigung, einordnung, pflichtangaben, router
from app.fallstand import UNBEKANNT_KNOPF, UNBEKANNT_WERT
from app.llm.fake import FakeLLM
from app.router import FAKTEN_BESTAETIGUNG_NOETIG, RUECKFRAGE_NOETIG
from app.schema import Fakten, Herkunft, Position

FRAGE = "2026 haben wir einer freien Grafikerin (Einzelperson) 1.500 € für ein Logo gezahlt."
OHNE_ZWECK = Fakten(anfrageart="bewertung", jahr=2026, auftragnehmer_typ="natuerliche_person",
                    positionen=[Position(betrag=D("1500"), bezeichnung="Logo", taetigkeit_id="T-02")])


class _Zaehler(FakeLLM):
    """Zählt die Modellaufrufe (ein Knopf und ein abgetippter Knopftext brauchen keinen)."""

    def __init__(self):
        super().__init__()
        self.aufrufe = 0

    def extrahiere_fakten(self, frage, verlauf=None, fallstand=None):
        self.aufrufe += 1
        return super().extrahiere_fakten(frage, verlauf, fallstand)


def _start(fakten=OHNE_ZWECK, frage=FRAGE):
    llm = _Zaehler()
    llm.registriere(frage, fakten)
    return llm, router.bearbeite_frage(frage, llm)


def _zweck_knopf(antwort, beschriftung):
    eintrag = next(o for o in antwort.rueckfrage_optionen if o["frage"] == pflichtangaben.FRAGE_ZWECK)
    return eintrag["feld"], eintrag["werte"][beschriftung]


def _ergebnis(antwort, llm):
    bestaetigung.SPEICHER.bestaetige(antwort.sitzungskennung, antwort.fakten_hash)
    return router.fuehre_nach_bestaetigung_aus(antwort.sitzungskennung, llm)


class ZweckStattKategorie(unittest.TestCase):
    def test_frage_und_knoepfe_in_alltagssprache(self):
        _, a = _start()
        self.assertEqual(a.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertEqual(a.rueckfragen, [pflichtangaben.FRAGE_ZWECK])
        self.assertTrue(a.rueckfragen[0].startswith("Wofür war dieser Auftrag gedacht?"))
        eintrag = a.rueckfrage_optionen[0]
        self.assertEqual(eintrag["feld"], "auftragszweck")
        self.assertEqual(eintrag["optionen"], ["Werbung für mein eigenes Unternehmen",
                                               "Werbung oder Öffentlichkeitsarbeit für Kunden",
                                               "Eine Veranstaltung mit Künstlern", "Ein privater Auftrag",
                                               UNBEKANNT_KNOPF])
        for verboten in ("Typischer Verwerter", "Generalklausel", "Eigenwerbung", "eigenwerbend"):
            self.assertNotIn(verboten, " ".join([a.rueckfragen[0], *eintrag["optionen"]]))

    def test_eigener_werbeauftrag(self):
        llm, a = _start()
        b = router.wende_feldantwort_an(a.sitzungskennung, *_zweck_knopf(a, "Werbung für mein eigenes Unternehmen"), llm)
        self.assertEqual(b.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG)
        f = bestaetigung.SPEICHER.hole_fakten(b.sitzungskennung)
        self.assertEqual((f.auftragszweck, f.verwerterart, f.herkunft["auftragszweck"].art),
                         ("eigene_werbung", "eigenwerber", "knopf"))
        self.assertIn(bestaetigung.EINORDNUNG_ZEILE + "Eigenwerbung", b.fakten_zusammenfassung)
        self.assertEqual(_ergebnis(b, llm).ergebnisklasse, "Abgabepflichtig (Vorschlag)")
        self.assertEqual(llm.aufrufe, 1, "der Knopf braucht keinen Modellaufruf")

    def test_werbung_fuer_kunden(self):
        llm, a = _start()
        b = router.wende_feldantwort_an(a.sitzungskennung,
                                        *_zweck_knopf(a, "Werbung oder Öffentlichkeitsarbeit für Kunden"), llm)
        f = bestaetigung.SPEICHER.hole_fakten(b.sitzungskennung)
        self.assertEqual((f.auftragszweck, f.verwerterart), ("fuer_kunden", "typischer_verwerter"))
        self.assertIsNone(f.katalog_taetigkeit, "die Tätigkeit des Auftraggebers wird nicht erfunden")

    def test_privater_auftrag(self):
        llm, a = _start()
        b = router.wende_feldantwort_an(a.sitzungskennung, *_zweck_knopf(a, "Ein privater Auftrag"), llm)
        self.assertEqual(_ergebnis(b, llm).ergebnisklasse, "Nicht abgabepflichtig (Vorschlag)")

    def test_veranstaltung_fragt_weiter_nach_tatsachen(self):
        llm, a = _start()
        b = router.wende_feldantwort_an(a.sitzungskennung, *_zweck_knopf(a, "Eine Veranstaltung mit Künstlern"), llm)
        self.assertEqual(b.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertEqual(b.rueckfragen, [pflichtangaben.FRAGE_VERANSTALTUNGSZAHL])

    def test_abgetippter_knopftext_ohne_modell(self):
        llm, a = _start()
        b = router.bearbeite_frage("ein privater Auftrag.", llm, [FRAGE], a.sitzungskennung)
        self.assertEqual(llm.aufrufe, 1, "kein zweiter Modellaufruf")
        self.assertEqual(bestaetigung.SPEICHER.hole_fakten(b.sitzungskennung).auftragszweck, "privat")
        self.assertEqual(b.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG)

    def test_freie_beschreibung_ohne_passenden_zweck_erzwingt_nichts(self):
        llm, a = _start()
        frei = "Das Logo war für eine interne Schulung."
        llm.registriere(frei, Fakten(anfrageart="bewertung"))
        b = router.bearbeite_frage(frei, llm, [FRAGE], a.sitzungskennung)
        self.assertEqual(b.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertEqual(b.rueckfragen, [pflichtangaben.FRAGE_ZWECK])
        self.assertIsNone(b.fakten_hash)
        f = bestaetigung.SPEICHER.hole_fakten(b.sitzungskennung)
        self.assertIsNone(f.verwerterart)


class TaetigkeitBleibt(unittest.TestCase):
    def test_verlag_mit_eigener_werbung_bleibt_verlag(self):
        f = Fakten(anfrageart="bewertung", jahr=2026, unternehmensart="Buchverlag", katalog_taetigkeit=True,
                   herkunft={"katalog_taetigkeit": Herkunft(art="text", beleg="Verlag")},
                   positionen=[Position(betrag=D("900"))])
        g = einordnung.zweck_knopf(f, "eigene_werbung")
        self.assertEqual((g.unternehmensart, g.katalog_taetigkeit, g.auftragszweck, g.verwerterart),
                         ("Buchverlag", True, "eigene_werbung", "typischer_verwerter"))

    def test_verlag_im_text_ohne_rueckfrage(self):
        frage = "Wir sind ein Verlag und machen eigene Werbung. 2026 zahlten wir einer freien Grafikerin 900 €."
        _, a = _start(Fakten(anfrageart="bewertung", jahr=2026, auftragnehmer_typ="natuerliche_person",
                             positionen=[Position(betrag=D("900"), bezeichnung="Grafik", taetigkeit_id="T-02")]),
                      frage)
        self.assertEqual(a.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG)
        self.assertIn(bestaetigung.EINORDNUNG_ZEILE + "Typischer Verwerter", a.fakten_zusammenfassung)
        self.assertTrue(any(z.startswith("Zweck dieses Auftrags: Werbung oder Öffentlichkeitsarbeit für das eigene")
                            for z in a.fakten_zusammenfassung))

    def test_nur_vermutete_katalogtaetigkeit_weicht_der_auswahl(self):
        f = Fakten(katalog_taetigkeit=True, herkunft={"katalog_taetigkeit": Herkunft(art="modell")})
        self.assertEqual(einordnung.zweck_knopf(f, "eigene_werbung").verwerterart, "eigenwerber")


class Widersprueche(unittest.TestCase):
    TEXT = "Wir machen Werbung für unser eigenes Geschäft. " + FRAGE

    def test_auswahl_ueberschreibt_den_text_nicht(self):
        llm, a = _start(OHNE_ZWECK, self.TEXT)
        self.assertEqual(a.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG)
        b = router.wende_feldantwort_an(a.sitzungskennung, "auftragszweck", "privat", llm)
        self.assertEqual(b.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertTrue(b.rueckfragen[0].endswith("Welche Angabe stimmt?"), b.rueckfragen)
        f = bestaetigung.SPEICHER.hole_fakten(b.sitzungskennung)
        self.assertEqual((f.auftragszweck, f.verwerterart), ("eigene_werbung", None), "nichts still überschrieben")
        knoepfe = next(o for o in b.rueckfrage_optionen if o["frage"] == b.rueckfragen[0])
        self.assertEqual(set(knoepfe["werte"].values()) - {UNBEKANNT_WERT}, {"eigene_werbung", "privat"})
        c = router.wende_feldantwort_an(b.sitzungskennung, knoepfe["feld"], "privat", llm)
        g = bestaetigung.SPEICHER.hole_fakten(c.sitzungskennung)
        self.assertEqual((g.auftragszweck, g.verwerterart, g.widersprueche), ("privat", "privat", []))

    def test_spaetere_textangabe_gegen_die_auswahl(self):
        llm, a = _start()
        b = router.wende_feldantwort_an(a.sitzungskennung, *_zweck_knopf(a, "Ein privater Auftrag"), llm)
        nachtrag = "Es war Werbung für unser eigenes Geschäft."
        llm.registriere(nachtrag, Fakten(anfrageart="bewertung"))
        c = router.bearbeite_frage(nachtrag, llm, [FRAGE, "Ein privater Auftrag"], b.sitzungskennung)
        self.assertEqual(c.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertIn("Welche Angabe stimmt?", c.rueckfragen[0])

    def test_modell_aendert_die_auswahl_nicht(self):
        llm, a = _start()
        b = router.wende_feldantwort_an(a.sitzungskennung, *_zweck_knopf(a, "Werbung für mein eigenes Unternehmen"), llm)
        nachtrag = "Die Grafikerin hat auch die Visitenkarten gestaltet, im Preis enthalten."
        llm.registriere(nachtrag, Fakten(anfrageart="bewertung", auftragszweck="fuer_kunden",
                                         verwerterart="typischer_verwerter"))
        # Verlauf ohne den Knopftext: geprüft wird nur, ob das MODELL die Auswahl ändern kann (der Knopftext im Verlauf
        # wäre selbst ein Beleg im Text).
        c = router.bearbeite_frage(nachtrag, llm, [FRAGE], b.sitzungskennung)
        f = bestaetigung.SPEICHER.hole_fakten(c.sitzungskennung)
        self.assertEqual((f.auftragszweck, f.verwerterart), ("eigene_werbung", "eigenwerber"))


class UnbekanntUndSpaeter(unittest.TestCase):
    def test_unbekannt_blockiert_und_spaeter_ergaenzen(self):
        llm, a = _start()
        b = router.wende_feldantwort_an(a.sitzungskennung, "auftragszweck", UNBEKANNT_WERT, llm)
        self.assertEqual(b.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertIsNone(b.fakten_hash, "ohne Zweck keine Bestätigung und keine Berechnung")
        self.assertIn("zurückgestellt", b.antwort)
        self.assertNotIn(pflichtangaben.FRAGE_ZWECK, b.rueckfragen, "die Frage kommt nicht sofort wieder")
        nachtrag = "Jetzt weiß ich es: es war Werbung für unser eigenes Geschäft."
        llm.registriere(nachtrag, Fakten(anfrageart="bewertung"))
        c = router.bearbeite_frage(nachtrag, llm, [FRAGE], b.sitzungskennung)
        self.assertEqual(c.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG, c.antwort)
        self.assertFalse(any("unbekannt" in z.lower() for z in c.fakten_zusammenfassung), c.fakten_zusammenfassung)


class Bestaetigung(unittest.TestCase):
    def _bestaetigung(self):
        llm, a = _start()
        return llm, router.wende_feldantwort_an(a.sitzungskennung,
                                                *_zweck_knopf(a, "Werbung für mein eigenes Unternehmen"), llm)

    def test_saetze_vom_system_und_liste_einmal(self):
        _, b = self._bestaetigung()
        saetze, rest = b.antwort.split("\n\n", 1)
        self.assertIn("Vorschlag des Systems, keine Angabe von Ihnen", saetze)
        self.assertIn("Gerechnet wird erst, wenn Sie „Ja, das stimmt“ wählen", saetze)
        self.assertIn("Kalenderjahr 2026", saetze)
        self.assertIn("keine gesondert ausgewiesene Umsatzsteuer", saetze)
        for zeile in b.fakten_zusammenfassung:
            self.assertNotIn(zeile, saetze, "die Liste steht nicht doppelt in den Sätzen")
            self.assertEqual(rest.count(zeile), 1)

    def test_betraege_annahmen_herkunft_sichtbar(self):
        _, b = self._bestaetigung()
        liste = b.fakten_zusammenfassung
        self.assertTrue(any(z.startswith("Position 1: 1.500,00 €") for z in liste), liste)
        self.assertIn(bestaetigung.ANNAHME_UST, liste)
        self.assertTrue(any("von Ihnen ausgewählt" in z for z in liste), liste)
        self.assertIn("Jahr: 2026", liste)

    def test_keine_berechnung_vor_bestaetigung(self):
        llm, b = self._bestaetigung()
        e = router.fuehre_nach_bestaetigung_aus(b.sitzungskennung, llm)
        self.assertEqual(e.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertEqual(e.kern_protokoll, {})

    def test_korrektur_macht_alte_bestaetigung_ungueltig(self):
        llm, b = self._bestaetigung()
        alter_hash = b.fakten_hash
        korrektur = "Korrektur: es waren 900 € statt 1.500 €."
        llm.registriere(korrektur, Fakten(anfrageart="bewertung", positionen=[
            Position(betrag=D("900"), bezeichnung="Logo", taetigkeit_id="T-02")]))
        c = router.bearbeite_frage(korrektur, llm, [FRAGE], b.sitzungskennung)
        self.assertNotEqual(c.fakten_hash, alter_hash)
        self.assertFalse(bestaetigung.SPEICHER.bestaetige(b.sitzungskennung, alter_hash))
        self.assertEqual(router.fuehre_nach_bestaetigung_aus(b.sitzungskennung, llm).ergebnisklasse,
                         RUECKFRAGE_NOETIG)

    def test_alte_bestaetigung_gilt_nicht_nach_neuer_auswahl(self):
        llm, b = self._bestaetigung()
        self.assertTrue(bestaetigung.SPEICHER.bestaetige(b.sitzungskennung, b.fakten_hash))
        c = router.wende_feldantwort_an(b.sitzungskennung, "auftragszweck", "privat", llm)
        self.assertNotEqual(c.fakten_hash, b.fakten_hash)
        self.assertFalse(bestaetigung.SPEICHER.ist_bestaetigt(c.sitzungskennung,
                                                              bestaetigung.SPEICHER.hole_fakten(c.sitzungskennung)))


class UngueltigeEingaben(unittest.TestCase):
    def test_kein_absturz_und_nichts_geaendert(self):
        llm, a = _start()
        vorher = bestaetigung.SPEICHER.hole_fakten(a.sitzungskennung)
        for feld, wert, position in (("katalog_taetigkeit", True, None), ("herkunft", {}, None),
                                     ("gibt_es_nicht", 1, None), ("auftragszweck", "quatsch", None),
                                     ("auftragnehmer_typ", "natuerliche_person", -1),
                                     ("auftragnehmer_typ", "natuerliche_person", 99), ("rest", True, 0),
                                     ("verwerterart", "unsinn", None), ("jahr", "zweitausend", None),
                                     ("auftragszweck", None, None), ("widersprueche", [], None)):
            with self.subTest(feld=feld, wert=wert, position=position):
                b = router.wende_feldantwort_an(a.sitzungskennung, feld, wert, llm, position)
                self.assertEqual(b.ergebnisklasse, RUECKFRAGE_NOETIG)
                self.assertEqual(bestaetigung.SPEICHER.hole_fakten(a.sitzungskennung), vorher)

    def test_unbekannte_sitzung(self):
        b = router.wende_feldantwort_an("gibt-es-nicht", "auftragszweck", "privat", FakeLLM())
        self.assertEqual(b.ergebnisklasse, RUECKFRAGE_NOETIG)


class AlteTestfaelle(unittest.TestCase):
    def test_alter_knopf_fuehrt_zur_selben_einordnung(self):
        for alt, kategorie in (("Eigenwerbung", "eigenwerber"), ("Typischer Verwerter", "typischer_verwerter"),
                               ("Veranstalter (Generalklausel)", "generalklausel"),
                               ("Privatperson (kein Unternehmen)", "privat")):
            with self.subTest(alt=alt):
                knopf = einordnung.zweck_knopf_fuer_alten_knopf(alt)
                f = einordnung.zweck_knopf(Fakten(), einordnung.ZWECK_KNOPF[knopf])
                self.assertEqual(f.verwerterart, kategorie)


if __name__ == "__main__":
    unittest.main()
