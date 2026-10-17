"""Regressionstests zum manuellen Testprotokoll vom 11.10.2026 (KSK_Testprotokoll_Claude_Code.pdf).

OFFLINE: Die Modellantworten sind kontrolliert und den echten Antworten von mistral-large-latest
aus dem Nachspielen nachgebildet (aufgaben/audit/dialog_nachgespielt_large.md). Geprüft wird die
Python-Logik: verbindlicher Fallstand, Übernahme, Zustände 'unbekannt' und 'widersprüchlich',
Übersicht, Fallwechsel. Nur erfundene Daten."""
from __future__ import annotations

import unittest
from decimal import Decimal as D

from app import bestaetigung, fallstand, pflichtangaben, router
from app.ergebnisklassen import FAKTEN_BESTAETIGUNG_NOETIG, RUECKFRAGE_NOETIG
from app.schema import Fakten, Position as P, Widerspruch

NP, GMBH = "natuerliche_person", "GmbH_UG_AG"

S1 = ("Wir sind ein Handwerksbetrieb und haben 2026 ausschließlich für unsere eigene Werbung Leistungen eingekauft:\n"
      "– Eine selbstständige Grafikerin, Einzelunternehmerin, stellte uns 1.200 Euro netto in Rechnung. Darin sind "
      "300 Euro Druckkosten enthalten.\n– Eine Foto-GmbH stellte uns 800 Euro netto in Rechnung.\n"
      "Weitere Aufträge an Künstler oder Publizisten gab es 2026 nicht. Wie hoch ist unsere Künstlersozialabgabe?")
S3 = ("Die 300 Euro sind Druckkosten innerhalb der Rechnung der Grafikerin. Bitte als Druckkosten bezeichnen, nicht als "
      "„Vortrag und Reproduktion“.\nGesamtbetrag der Grafikerin weiterhin 1.200 Euro netto, einschließlich dieser 300 Euro. "
      "Alle anderen Angaben bleiben unverändert.")
S4 = ("Korrektur: Die gesamte Rechnung der Grafikerin beträgt 900 Euro netto statt 1.200 Euro. Darin sind weiterhin "
      "300 Euro Druckkosten enthalten.\nDie separate Rechnung der Foto-GmbH bleibt bei 800 Euro. Jahr 2026 und "
      "Eigenwerbung bleiben unverändert.")
S6 = ("Mein Kollege sagt, die Auftragnehmerin der Fotorechnung über 800 Euro sei Einzelunternehmerin. Auf der Rechnung "
      "steht aber „Foto-Beispiel GmbH“.\nWelche Angabe stimmt, ist noch ungeklärt. Kannst du einfach mit "
      "Einzelunternehmerin weiterrechnen? Alle anderen Angaben bleiben unverändert.")
S7 = ("Neuer, unabhängiger Fall: Ein Verein hat für zwei Veranstaltungen insgesamt drei Rechnungen von Musikern über "
      "zusammen 1.800 Euro erhalten.\nDas Jahr, die Rechtsformen der Auftragnehmer und die Frage, ob Einnahmen erzielt "
      "werden sollten, sind unbekannt. Muss der Verein Künstlersozialabgabe zahlen?")
S8 = "Der neue Vereinsfall betrifft 2026. Alle anderen bisher unbekannten Angaben bleiben unbekannt."
S9 = ("Das ist noch ungeklärt. Bitte weder Ja noch Nein annehmen. Welche Angaben sind für diesen Vereinsfall bisher "
      "erfasst, und welche bleiben offen?")


def _rechnungen(grafik="900", druck="300", rolle="material_auslagen", bez="Druckkosten", foto_typ=GMBH):
    return [P(betrag=D(grafik), bezeichnung="Grafikleistung (ohne Druckkosten)", auftragnehmer_typ=NP, auftragnehmer_nr=1),
            P(betrag=D(druck), rolle=rolle, bezeichnung=bez, auftragnehmer_typ=NP, auftragnehmer_nr=1),
            P(betrag=D("800"), bezeichnung="Fotografie", auftragnehmer_typ=foto_typ, auftragnehmer_nr=2)]


class Modell:
    """Kontrollierte Modellantworten in fester Reihenfolge; merkt sich, was es bekommen hat."""

    def __init__(self, *antworten: Fakten):
        self.antworten = list(antworten)
        self.aufrufe: list[dict] = []

    def extrahiere_fakten(self, frage, verlauf=None, fallstand=None):
        self.aufrufe.append({"frage": frage, "verlauf": list(verlauf or []), "fallstand": fallstand})
        return self.antworten.pop(0)

    def beschreibe_fall(self, kontext):  # pragma: no cover - nicht gebraucht
        return ""


class Oberflaeche:
    def __init__(self, llm):
        self.llm, self.verlauf, self.sitzung = llm, [], None

    def sende(self, text):
        a = router.bearbeite_frage(text, self.llm, list(self.verlauf), self.sitzung)
        self.verlauf.append(text)
        self.sitzung = a.sitzungskennung or self.sitzung
        return a

    def knopf(self, feld, wert, position=None):
        a = router.wende_feldantwort_an(self.sitzung, feld, wert, self.llm, position)
        self.sitzung = a.sitzungskennung or self.sitzung
        return a

    def stand(self):
        return bestaetigung.SPEICHER.hole_fakten(self.sitzung)


class TestAusgangsfall(unittest.TestCase):
    def setUp(self):
        erste = Fakten(anfrageart="bewertung", jahr=2026, unternehmensart="Handwerksbetrieb", ein_auftragnehmer=False,
                       positionen=_rechnungen(), gesamtbetrag_genannt=D("2000"))
        self.llm = Modell(erste)
        self.ui = Oberflaeche(self.llm)
        self.a1 = self.ui.sende(S1)

    def test_eigenwerbung_wird_nicht_erneut_gefragt(self):
        """Schritt 1/2: 'ausschließlich für unsere eigene Werbung' -- das Modell setzt verwerterart nicht."""
        self.assertEqual(self.ui.stand().verwerterart, "eigenwerber")
        self.assertNotIn(pflichtangaben.FRAGE_VERWERTERART, self.a1.rueckfragen)
        self.assertFalse(any("Rechtsform" in r for r in self.a1.rueckfragen), self.a1.rueckfragen)

    def test_erfundene_rolle_wird_verworfen_und_bezeichnung_angezeigt(self):
        """'vortrag und reproduktion' / 'material_auslagen': keine gültige Rolle; angezeigt wird die Bezeichnung."""
        stand = self.ui.stand()
        self.assertIsNone(stand.positionen[1].rolle)
        liste = bestaetigung.als_liste(stand)
        self.assertTrue(any("„Druckkosten“" in z for z in liste), liste)
        self.assertFalse(any("material" in z.lower() for z in liste), liste)

    def test_druckkosten_bleiben_bei_der_grafikerin(self):
        """Gemeinsamer Auftragnehmer der Bestandteile (Rechnung der Grafikerin)."""
        stand = self.ui.stand()
        self.assertEqual(stand.positionen[0].auftragnehmer_nr, stand.positionen[1].auftragnehmer_nr)
        self.assertEqual(stand.summe_positionen(), D("2000"), "1.200 + 800, keine Doppelzählung")


class TestFallstandUndKorrekturen(unittest.TestCase):
    def _ui(self, *folgeantworten):
        erste = Fakten(anfrageart="bewertung", jahr=2026, verwerterart="eigenwerber", positionen=_rechnungen())
        llm = Modell(erste, *folgeantworten)
        ui = Oberflaeche(llm)
        a = ui.sende(S1)
        return llm, ui, a

    def test_modell_bekommt_fallstand_statt_chatverlauf(self):
        llm, ui, _ = self._ui(Fakten(positionen=_rechnungen(bez="Druckkosten")))
        ui.sende(S3)
        self.assertIsNotNone(llm.aufrufe[1]["fallstand"], "der gespeicherte Fallstand geht mit")
        self.assertEqual(llm.aufrufe[1]["fallstand"].jahr, 2026)

    def test_bezeichnung_laesst_sich_korrigieren(self):
        llm, ui, _ = self._ui(Fakten(positionen=_rechnungen(bez="Druckkosten (Rechnung der Grafikerin)")))
        a = ui.sende(S3)
        self.assertTrue(any("„Druckkosten (Rechnung der Grafikerin)“" in z for z in a.fakten_zusammenfassung or []),
                        a.fakten_zusammenfassung)

    def test_betragskorrektur_ersetzt_nur_den_betrag_und_macht_bestaetigung_ungueltig(self):
        llm, ui, a1 = self._ui(Fakten(positionen=_rechnungen(grafik="600")))
        alt_hash = a1.fakten_hash
        a = ui.sende(S4)
        stand = ui.stand()
        self.assertEqual([p.betrag for p in stand.positionen], [D("600"), D("300"), D("800")])
        self.assertEqual((stand.jahr, stand.verwerterart), (2026, "eigenwerber"))
        self.assertNotEqual(a.fakten_hash, alt_hash)
        self.assertFalse(bestaetigung.SPEICHER.bestaetige(ui.sitzung, alt_hash), "alter Bestätigungsknopf ist wirkungslos")

    def test_nicht_gelieferte_angaben_bleiben_erhalten(self):
        llm, ui, _ = self._ui(Fakten(jahr=None, verwerterart=None, positionen=_rechnungen()))
        ui.sende("Danke.")
        self.assertEqual((ui.stand().jahr, ui.stand().verwerterart), (2026, "eigenwerber"))

    def test_weniger_positionen_nur_bei_ausdruecklicher_entfernung(self):
        nur_zwei = Fakten(positionen=_rechnungen()[:2])
        llm, ui, _ = self._ui(nur_zwei, nur_zwei)
        ui.sende("Bitte nochmal prüfen.")
        self.assertEqual(len(ui.stand().positionen), 3, "das Modell darf keine Rechnung still verlieren")
        ui.sende("Die Fotorechnung bitte streichen.")
        self.assertEqual(len(ui.stand().positionen), 2)


class TestWiderspruch(unittest.TestCase):
    def _ui(self, antwort_s6):
        erste = Fakten(anfrageart="bewertung", jahr=2026, verwerterart="eigenwerber", positionen=_rechnungen(grafik="600"))
        ui = Oberflaeche(Modell(erste, antwort_s6))
        ui.sende(S1)
        return ui, ui.sende(S6)

    def _pruefe_widerspruch(self, ui, a):
        self.assertEqual(a.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertIsNone(a.fakten_hash, "keine Faktenbestätigung, solange der Widerspruch offen ist")
        self.assertIn("Widersprüchliche Angaben", a.rueckfragen[0])
        self.assertEqual(ui.stand().positionen[2].auftragnehmer_typ, GMBH, "keine stille Änderung")
        knoepfe = a.rueckfrage_optionen[0]
        self.assertIn("GmbH/UG/AG", knoepfe["optionen"])
        self.assertIn("natürliche Person", knoepfe["optionen"])
        self.assertIn(fallstand.UNBEKANNT_KNOPF, knoepfe["optionen"])
        return knoepfe

    def test_vom_modell_gemeldeter_widerspruch(self):
        meldung = Fakten(positionen=_rechnungen(grafik="600", foto_typ=NP), widersprueche=[
            Widerspruch(feld="positionen.3.auftragnehmer_typ", werte=["GmbH_UG_AG", "Einzelunternehmerin"])])
        ui, a = self._ui(meldung)
        knoepfe = self._pruefe_widerspruch(ui, a)
        b = ui.knopf(knoepfe["feld"], knoepfe["werte"]["GmbH/UG/AG"], knoepfe.get("position"))
        self.assertEqual(b.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG)
        self.assertEqual(ui.stand().widersprueche, [])

    def test_vom_modell_verschwiegener_widerspruch_wird_trotzdem_erkannt(self):
        """Echte Modellantwort: Rechtsform der Fotorechnung einfach null."""
        still = Fakten(positionen=_rechnungen(grafik="600", foto_typ=None))
        ui, a = self._ui(still)
        self._pruefe_widerspruch(ui, a)

    def test_ungeklaert_bleibt_offen(self):
        ui, a = self._ui(Fakten(positionen=_rechnungen(grafik="600", foto_typ=None)))
        k = a.rueckfrage_optionen[0]
        b = ui.knopf(k["feld"], fallstand.UNBEKANNT_WERT, k.get("position"))
        self.assertEqual(b.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertIn("zurückgestellt", b.antwort)
        self.assertIsNone(b.fakten_hash)


class TestFallwechselUndUnbekannt(unittest.TestCase):
    def setUp(self):
        alt = Fakten(anfrageart="bewertung", jahr=2026, verwerterart="eigenwerber", positionen=_rechnungen(grafik="600"))
        # Echte Modellantwort zu S7: 'Verein' als Rechtsform der MUSIKER, obwohl 'unbekannt' gesagt wurde.
        verein = Fakten(anfrageart="bewertung", unternehmensart="Verein", auftragnehmer_typ="Verein", leistungsart="Musik",
                        veranstaltungszahl=2, anzahl_auftraege=3, gesamtbetrag_genannt=D("1800"))
        s8 = Fakten(jahr=2026)
        self.llm = Modell(alt, verein, s8)
        self.ui = Oberflaeche(self.llm)
        self.ui.sende(S1)
        self.alte_sitzung = self.ui.sitzung
        self.a7 = self.ui.sende(S7)

    def test_neuer_fall_ist_getrennt_und_unbekanntes_bleibt_unbekannt(self):
        stand = self.ui.stand()
        self.assertNotEqual(self.ui.sitzung, self.alte_sitzung)
        self.assertIsNone(self.llm.aufrufe[1]["fallstand"], "der alte Fallstand geht nicht ans Modell")
        self.assertEqual(stand.positionen, [], "keine alten oder erfundenen Rechnungen")
        self.assertEqual((stand.veranstaltungszahl, stand.anzahl_auftraege, stand.gesamtbetrag_genannt), (2, 3, D("1800")))
        self.assertIsNone(stand.verwerterart, "keine Eigenwerbung aus dem alten Fall")
        self.assertIsNone(stand.auftragnehmer_typ, "'Verein' ist der Auftraggeber, die Rechtsformen sind unbekannt")
        for feld in ("jahr", "auftragnehmer_typ", "einnahmeabsicht"):
            self.assertIn(feld, stand.unbekannt)
        self.assertEqual(len(bestaetigung.SPEICHER.hole_fakten(self.alte_sitzung).positionen), 3, "alter Fall bleibt erhalten")

    def test_jahr_ergaenzen_und_unbekanntes_nicht_erneut_fragen(self):
        a8 = self.ui.sende(S8)
        stand = self.ui.stand()
        self.assertEqual(stand.jahr, 2026)
        self.assertNotIn("jahr", stand.unbekannt)
        self.assertNotIn(pflichtangaben.FRAGE_EINNAHMEABSICHT, a8.rueckfragen)

    def test_uebersicht_statt_sackgasse(self):
        self.ui.sende(S8)
        aufrufe_vorher = len(self.llm.aufrufe)
        a9 = self.ui.sende(S9)
        self.assertEqual(len(self.llm.aufrufe), aufrufe_vorher, "Schritt 9 braucht kein Modell")
        self.assertIn("Bisher erfasst", a9.antwort)
        self.assertIn("Jahr: 2026", a9.antwort)
        self.assertIn("Veranstaltungen: 2", a9.antwort)
        self.assertIn("Einnahmeabsicht: ausdrücklich unbekannt", a9.antwort)
        self.assertIn("zurückgestellt", a9.antwort)
        self.assertIsNone(a9.fakten_hash)
        self.assertNotIn(pflichtangaben.FRAGE_EINNAHMEABSICHT, a9.rueckfragen)

    def test_knopf_noch_unbekannt(self):
        a8 = self.ui.sende(S8)
        k = a8.rueckfrage_optionen[0]
        self.assertIn(fallstand.UNBEKANNT_KNOPF, k["optionen"])
        b = self.ui.knopf(k["feld"], fallstand.UNBEKANNT_WERT, k.get("position"))
        self.assertIn(k["feld"], self.ui.stand().unbekannt)
        self.assertNotIn(a8.rueckfragen[0], b.rueckfragen, "dieselbe Frage kommt nicht wieder")


class TestErkennung(unittest.TestCase):
    def test_unbekannt_im_text(self):
        self.assertEqual(fallstand.unbekannt_im_text(S7.split("\n")[1]), ["jahr", "auftragnehmer_typ", "einnahmeabsicht"])
        self.assertEqual(fallstand.unbekannt_im_text(S8), [])
        self.assertEqual(fallstand.unbekannt_im_text("Einmalige Kampagne, 5.000 €, Jahr 2017, Historie unbekannt."), [])

    def test_uebersicht_und_unbekannt_als_antwort(self):
        self.assertTrue(fallstand.will_uebersicht(S9))
        self.assertTrue(fallstand.antwort_ist_unbekannt(S9))
        self.assertFalse(fallstand.antwort_ist_unbekannt("Das war 2025, für unsere eigene Werbung."))


if __name__ == "__main__":
    unittest.main()


class TestBefundeAusDemLiveNachspielen(unittest.TestCase):
    """Zweites Nachspielen mit mistral-large-latest (11.10.2026)."""

    def test_verneinte_leistung_zaehlt_nicht(self):
        from app import taetigkeiten as T

        self.assertEqual(T.erkenne("Grafikleistung (ohne Druckkosten)"), "T-02")

    def test_widerspruch_nur_bei_angaben_des_nutzers(self):
        alt = Fakten(jahr=2026, positionen=[P(betrag=D("900"), taetigkeit_id="widerspruch")])
        neu = Fakten(widersprueche=[Widerspruch(feld="positionen.1.taetigkeit_id", werte=["widerspruch", "T-40"])])
        self.assertEqual(fallstand.uebernehme(alt, neu, "Bitte als Druckkosten bezeichnen.").widersprueche, [])

    def test_ausdruecklich_unbekanntes_jahr_wird_nicht_gefragt(self):
        f = Fakten(anfrageart="bewertung", unbekannt=["jahr"], gesamtbetrag_genannt=D("1800"), veranstaltungszahl=2)
        self.assertNotIn(pflichtangaben.FRAGE_JAHR, pflichtangaben.fehlende_pflichtangaben(f, alle=True))

    def test_fallstand_an_das_modell_ohne_abgeleitete_werte(self):
        import json
        from app.llm.mistral import MistralLLM

        llm = MistralLLM(api_key="nur-test-ohne-netz")
        gesendet = []
        llm._aufruf = lambda system, user, **kw: gesendet.append(user) or json.dumps({"jahr": 2026})
        llm.extrahiere_fakten("Danke.", ["alter Text"], fallstand=Fakten(
            jahr=2026, taetigkeit_id="T-02", positionen=[P(betrag=D("900"), taetigkeit_id="widerspruch")]))
        self.assertIn("BISHERIGER FALLSTAND", gesendet[0])
        self.assertNotIn("taetigkeit_id", gesendet[0])
        self.assertNotIn("alter Text", gesendet[0], "der Chatverlauf geht nicht mit")


class TestRechnungMitEnthaltenenTeilen(unittest.TestCase):
    """Schritt 4 live: '900 statt 1.200 Euro, darin weiterhin 300 Euro Druckkosten' -- das Modell
    hätte 900 - 300 rechnen müssen und ließ den alten Rest stehen. Jetzt rechnet der Kern den Rest."""

    def _stand(self, gesamt):
        from app.schema import Rechnung

        return Fakten(anfrageart="bewertung", jahr=2026, verwerterart="eigenwerber",
                      rechnungen=[Rechnung(auftragnehmer_nr=1, gesamtbetrag=D(gesamt))],
                      positionen=[P(betrag=D("0"), bezeichnung="Grafikleistung", rest=True, auftragnehmer_typ=NP, auftragnehmer_nr=1),
                                  P(betrag=D("300"), bezeichnung="Druckkosten", auftragnehmer_typ=NP, auftragnehmer_nr=1),
                                  P(betrag=D("800"), bezeichnung="Fotografie", auftragnehmer_typ=GMBH, auftragnehmer_nr=2)])

    def test_rest_und_korrektur_des_rechnungsbetrags(self):
        from app.schema import Rechnung

        ui = Oberflaeche(Modell(self._stand("1200"), Fakten(rechnungen=[Rechnung(auftragnehmer_nr=1, gesamtbetrag=D("900"))])))
        ui.sende(S1)
        self.assertEqual([p.betrag for p in ui.stand().positionen], [D("900"), D("300"), D("800")])
        ui.sende(S4)
        self.assertEqual([p.betrag for p in ui.stand().positionen], [D("600"), D("300"), D("800")])

    def test_teile_groesser_als_rechnung_ist_ein_widerspruch(self):
        from app import zuordnung

        f = zuordnung.berechne_restpositionen(self._stand("200"))
        self.assertTrue(any(w.feld == "rechnungen.1" for w in f.widersprueche))

    def test_vom_modell_addierter_gesamtbetrag_wird_verworfen(self):
        from app import zuordnung

        f = Fakten(gesamtbetrag_genannt=D("2000"), positionen=_rechnungen(grafik="1200", druck="0"))
        f = f.model_copy(update={"positionen": f.positionen[:1] + f.positionen[2:]})
        self.assertIsNone(zuordnung.absichere_gesamtbetrag(S1, f).gesamtbetrag_genannt)
        g = Fakten(gesamtbetrag_genannt=D("1800"))
        self.assertEqual(zuordnung.absichere_gesamtbetrag("zusammen 1.800 Euro", g).gesamtbetrag_genannt, D("1800"))


class TestGemeinsamerAuftragnehmer(unittest.TestCase):
    def test_bestandteil_erbt_die_rechtsform_derselben_auftragnehmerin(self):
        positionen = [P(betrag=D("900"), bezeichnung="Grafikdesign", auftragnehmer_typ=NP, auftragnehmer_nr=1),
                      P(betrag=D("300"), bezeichnung="Druckkosten", auftragnehmer_nr=1),
                      P(betrag=D("800"), bezeichnung="Fotografie", auftragnehmer_typ=GMBH, auftragnehmer_nr=2)]
        ui = Oberflaeche(Modell(Fakten(anfrageart="bewertung", jahr=2026, positionen=positionen)))
        a = ui.sende(S1)
        self.assertEqual(ui.stand().positionen[1].auftragnehmer_typ, NP)
        self.assertFalse(any("Rechtsform" in r for r in a.rueckfragen), a.rueckfragen)


class TestRechtsformJeZeile(unittest.TestCase):
    def test_schritt1_ohne_rechtsform_vom_modell(self):
        """Live: das Modell lieferte zu S1 keine einzige Rechtsform."""
        from app.schema import Rechnung

        modell = Fakten(anfrageart="bewertung", jahr=2026,
                        rechnungen=[Rechnung(auftragnehmer_nr=1, gesamtbetrag=D("1200")), Rechnung(auftragnehmer_nr=2, gesamtbetrag=D("800"))],
                        positionen=[P(betrag=D("300"), bezeichnung="Druckkosten", auftragnehmer_nr=1),
                                    P(betrag=D("0"), bezeichnung="Grafikdesign", rest=True, auftragnehmer_nr=1),
                                    P(betrag=D("800"), bezeichnung="Fotografie", auftragnehmer_nr=2)])
        ui = Oberflaeche(Modell(modell))
        a = ui.sende(S1)
        stand = ui.stand()
        self.assertEqual([p.auftragnehmer_typ for p in stand.positionen], [NP, NP, GMBH])
        self.assertEqual([p.betrag for p in stand.positionen], [D("300"), D("900"), D("800")])
        self.assertEqual(a.ergebnisklasse, FAKTEN_BESTAETIGUNG_NOETIG, a.rueckfragen)


class TestDavonNichtDoppelt(unittest.TestCase):
    def test_p39_gage_davon_an_den_manager(self):
        from app import zuordnung

        text = ("Eine selbständige Sängerin (Einzelperson) bekommt 2025 eine Gage von 2.000 €. Auf ihren Wunsch "
                "zahlen wir davon 500 € direkt an ihren Manager.")
        f = Fakten(positionen=[P(betrag=D("2000"), bezeichnung="Gage", auftragnehmer_typ=NP),
                               P(betrag=D("500"), bezeichnung="Zahlung an Manager", auftragnehmer_typ=NP)])
        f = zuordnung.berechne_restpositionen(zuordnung.enthaltene_betraege_nicht_doppelt(text, f))
        self.assertEqual(f.summe_positionen(), D("2000"))
        self.assertEqual([p.betrag for p in f.positionen], [D("1500"), D("500")])

    def test_plus_ist_kein_davon(self):
        from app import zuordnung

        f = Fakten(positionen=[P(betrag=D("2000")), P(betrag=D("300"))])
        self.assertEqual(zuordnung.enthaltene_betraege_nicht_doppelt("2.000 € Honorar plus 300 € Material", f), f)

    def test_rechnungen_als_zahl_zweiter_versuch(self):
        import json
        from app.llm.mistral import MistralLLM

        llm = MistralLLM(api_key="nur-test-ohne-netz")
        # Ohne Rest-Position hängt an den Rechnungsbeträgen nichts: sie werden verworfen, der Rest gilt.
        folge = iter([{"jahr": 2026, "rechnungen": [1]}])
        llm._aufruf = lambda *a, **k: json.dumps(next(folge))
        f = llm.extrahiere_fakten("2026")
        self.assertEqual((f.jahr, f.rechnungen), (2026, []))


class TestP28Umsatzsteuer(unittest.TestCase):
    """Live 11.10.2026: das Modell gab 1.190 € als 'Umsatzsteuer' und eine Rest-Position 0 € aus
    -- Ergebnis 'nicht abgabepflichtig'. Jetzt: keine stille Null, gezielte Rückfrage."""

    TEXT = ("Unsere Werbeagentur hat 2025 einem freien Fotografen (Einzelperson) 1.190 € brutto gezahlt, darin "
            "190 € Umsatzsteuer gesondert ausgewiesen. Wie hoch ist die Bemessungsgrundlage?")

    def test_ganzer_betrag_ist_keine_umsatzsteuer(self):
        from app import zuordnung

        f = Fakten(positionen=[P(betrag=D("1190"), rolle="ust"), P(betrag=D("190"), rolle="ust")])
        f = zuordnung.absichere_rollen(self.TEXT, f)
        self.assertEqual([p.rolle for p in f.positionen], [None, "ust"])

    def test_rest_ohne_rechnung_und_teil_gleich_rechnung_fuehren_zur_rueckfrage(self):
        from app.schema import Rechnung

        modell = Fakten(anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter",
                        rechnungen=[Rechnung(auftragnehmer_nr=1, gesamtbetrag=D("1190"))],
                        positionen=[P(betrag=D("1190"), rolle="ust", auftragnehmer_typ=NP, auftragnehmer_nr=1),
                                    P(betrag=D("0"), bezeichnung="Honorar für Fotografie", rest=True, auftragnehmer_typ=NP)])
        a = Oberflaeche(Modell(modell)).sende(self.TEXT)
        self.assertEqual(a.ergebnisklasse, RUECKFRAGE_NOETIG)
        self.assertIsNone(a.fakten_hash, "keine Bestätigung einer unklaren Aufteilung")
        self.assertTrue(any("Aufteilung der Rechnung" in r for r in a.rueckfragen), a.rueckfragen)


class TestRobusteModellantwort(unittest.TestCase):
    def _llm(self, antwort):
        import json
        from app.llm.mistral import MistralLLM

        llm = MistralLLM(api_key="nur-test-ohne-netz")
        llm._aufruf = lambda *a, **k: json.dumps(antwort)
        return llm

    def test_harmlose_formfehler_werden_ohne_raten_bereinigt(self):
        f = self._llm({"jahr": 2026, "kuenstlerisch": True, "rechnungen": [1],
                       "positionen": [{"bezeichnung": "Auftrag ohne Betrag"}, {"betrag": 900}]}).extrahiere_fakten("x")
        self.assertEqual([p.betrag for p in f.positionen], [D("900")])
        self.assertEqual(f.rechnungen, [])

    def test_rechnungen_als_zahl_bei_restposition_bleibt_ein_fehler(self):
        from app.llm.base import LLMFehlgeschlagen

        llm = self._llm({"rechnungen": [1200], "positionen": [{"betrag": 0, "rest": True}]})
        with self.assertRaises(LLMFehlgeschlagen):
            llm.extrahiere_fakten("x")
