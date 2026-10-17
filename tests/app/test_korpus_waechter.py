"""Wächter gegen typische Lesefehler eines Sprachmodells (Korpus-Lauf mit gestörten Fakten, 15.10.2026).

Jeder Wächter in app/zuordnung.py prüft die Angaben des Modells gegen den Nutzertext -- unabhängig davon, welches
Sprachmodell (Mistral, ChatGPT, lokales DeepSeek, Claude) die Fakten geliefert hat. Je Wächter: der Fehler, der behoben
wird, UND ein Gegenbeispiel, bei dem nichts geändert werden darf. Texte mit eigenen Formulierungen (nicht aus dem
Korpus), damit die Regeln nicht nur auf die Korpus-Sätze passen. Nur erfundene Daten."""
from __future__ import annotations

import unittest
from decimal import Decimal as D

from app import zuordnung
from app.rechtsform_erkennung import erkenne_rechtsform_auftragnehmer
from app.schema import Fakten, Position as P

NP, GMBH = "natuerliche_person", "GmbH_UG_AG"


class DoppeltePositionen(unittest.TestCase):
    def test_doppelt_angelegte_position_wird_gekuerzt(self):
        text = "2025 haben wir einer freien Illustratorin 700 Euro für ein Kinderbuch-Cover gezahlt."
        f = Fakten(positionen=[P(betrag=D("700"), bezeichnung="Cover"), P(betrag=D("700"), bezeichnung="Cover")])
        self.assertEqual(len(zuordnung.doppelte_positionen(text, f).positionen), 1)

    def test_gegenbeispiele_mengen_und_je(self):
        f = Fakten(positionen=[P(betrag=D("700"), bezeichnung="Cover"), P(betrag=D("700"), bezeichnung="Cover")])
        for text in ("Zwei Rechnungen der Illustratorin über 700 Euro.", "Für zwei Cover je 700 Euro.",
                     "Sie bekam zweimal 700 Euro.", "Ein Fall ohne jeden Betrag."):
            self.assertEqual(len(zuordnung.doppelte_positionen(text, f).positionen), 2, text)


class JahrNurAusText(unittest.TestCase):
    def test_jahr_des_modells_widerspricht_dem_text(self):
        f = zuordnung.jahr_nur_aus_text("Unser Chor hat 2024 einen Dirigenten bezahlt.", Fakten(jahr=2025))
        self.assertEqual(f.jahr, 2024)

    def test_gegenbeispiele(self):
        self.assertEqual(zuordnung.jahr_nur_aus_text("Ohne Jahreszahl.", Fakten(jahr=2025)).jahr, 2025)
        self.assertEqual(zuordnung.jahr_nur_aus_text("2024 und 2025 je eine Zahlung.", Fakten(jahr=2025)).jahr, 2025)
        # zwei Jahre im Text, keines vom Modell: offen lassen, nicht raten
        self.assertIsNone(zuordnung.jahr_nur_aus_text("2023 und 2024 je eine Zahlung.", Fakten(jahr=2025)).jahr)


class VeranstaltungszahlAusText(unittest.TestCase):
    def test_zahl_aus_dem_text_gilt(self):
        f = zuordnung.veranstaltungszahl_aus_text("Der Heimatverein hatte sechs Konzerte mit Bands.",
                                                  Fakten(veranstaltungszahl=5))
        self.assertEqual(f.veranstaltungszahl, 6)

    def test_gegenbeispiel_verschiedene_zahlen(self):
        f = zuordnung.veranstaltungszahl_aus_text("2 Konzerte im Frühjahr und 4 Konzerte im Herbst.",
                                                  Fakten(veranstaltungszahl=5))
        self.assertIsNone(f.veranstaltungszahl)


class EinnahmeabsichtUndNachweis(unittest.TestCase):
    def test_einnahmeabsicht_gegen_eindeutigen_text_wird_verworfen(self):
        f = zuordnung.ergaenze_einnahmeabsicht("Der Eintritt war frei, wir wollten keine Einnahmen erzielen.",
                                               Fakten(verwerterart="generalklausel", einnahmeabsicht=True))
        self.assertIsNot(f.einnahmeabsicht, True)

    def test_verneinter_nachweis_nimmt_die_rolle(self):
        text = "Honorar 900 Euro, dazu 120 Euro Fahrtkosten; Belege liegen nicht vor."
        f = Fakten(positionen=[P(betrag=D("900")), P(betrag=D("120"), rolle="fahrtkosten_nachgewiesen", nachgewiesen=True)])
        self.assertIsNone(zuordnung.absichere_rollen(text, f).positionen[1].rolle)

    def test_gegenbeispiel_nachweis_bejaht(self):
        text = "Honorar 900 Euro, dazu 120 Euro Fahrtkosten, die Bahntickets liegen vor."
        f = Fakten(positionen=[P(betrag=D("900")), P(betrag=D("120"), rolle="fahrtkosten_nachgewiesen", nachgewiesen=True)])
        self.assertEqual(zuordnung.absichere_rollen(text, f).positionen[1].rolle, "fahrtkosten_nachgewiesen")


class GesamtbetragMitRolle(unittest.TestCase):
    def test_zahlung_an_verwertungsgesellschaft(self):
        f = zuordnung.gesamtbetrag_mit_rolle("2025 zahlten wir 640 Euro an die GEMA für die Hintergrundmusik.",
                                             Fakten(gesamtbetrag_genannt=D("640")))
        self.assertEqual([(p.betrag, p.rolle) for p in f.positionen], [(D("640"), "verwertungsgesellschaft")])

    def test_gegenbeispiel_wortteil(self):
        # 'gema' steckt in 'gemacht' -- das ist keine Verwertungsgesellschaft (test_fehlerquellen HT-074)
        f = zuordnung.gesamtbetrag_mit_rolle("Wir haben 2025 Werbung gemacht und 640 Euro für Kunstdrucke gezahlt.",
                                             Fakten(gesamtbetrag_genannt=D("640")))
        self.assertEqual(f.positionen, [])


class RechtsformWiderlegt(unittest.TestCase):
    def test_rechtsform_des_modells_gegen_den_eigenen_satz(self):
        text = "2025 hat unser Café der Klangfabrik GmbH 1.300 Euro für einen Werbesong gezahlt."
        f = zuordnung.rechtsform_nur_wo_genannt(text, Fakten(positionen=[P(betrag=D("1300"), auftragnehmer_typ=NP)]))
        self.assertIsNone(f.positionen[0].auftragnehmer_typ)

    def test_gegenbeispiel_widerspruch_bleibt_fuer_die_rueckfrage(self):
        # Rechtsform OHNE Betrag an anderer Stelle: ein Widerspruch, den die Widerspruchsprüfung mit Knöpfen klärt.
        text = ("Die Rechnung über 1.300 Euro stammt laut Kollegin von einer Einzelunternehmerin. "
                "Auf dem Briefkopf steht aber Klangfabrik GmbH.")
        f = zuordnung.rechtsform_nur_wo_genannt(text, Fakten(positionen=[P(betrag=D("1300"), auftragnehmer_typ=GMBH)]))
        self.assertEqual(f.positionen[0].auftragnehmer_typ, GMBH)

    def test_empfaenger_nach_der_eigenen_seite(self):
        self.assertEqual(erkenne_rechtsform_auftragnehmer("2025 haben wir der Bildwerk GmbH 800 Euro gezahlt."), GMBH)
        self.assertIsNone(erkenne_rechtsform_auftragnehmer("Wir, die Bildwerk GmbH, zahlten 800 Euro an einen Maler."))


class FehlendeNebenkosten(unittest.TestCase):
    def test_vergessene_fahrtkosten_werden_eine_position(self):
        text = "Die Sängerin bekam 2025 eine Gage von 380 Euro, außerdem haben wir ihr 90 Euro Anfahrt pauschal bezahlt."
        f = zuordnung.fehlende_nebenkosten_position(
            text, Fakten(positionen=[P(betrag=D("380"), bezeichnung="Gage", auftragnehmer_typ=NP)]))
        self.assertEqual([p.betrag for p in f.positionen], [D("380"), D("90")])
        self.assertEqual(f.positionen[1].auftragnehmer_typ, NP)
        self.assertIsNone(f.positionen[1].rolle, "zählt normal; nachgewiesene Reisekosten erkennt ein anderer Wächter")

    def test_gegenbeispiele(self):
        start = Fakten(positionen=[P(betrag=D("380"), bezeichnung="Gage")])
        for text in ("Gage 380 Euro, darin 90 Euro Anfahrt.",             # enthalten, nicht zusätzlich
                     "Gage 380 Euro inklusive 90 Euro Fahrtkosten.",
                     "Gage 380 Euro. 90 Euro Fahrtkosten hat der Veranstalter getragen.",  # kein Zusatz-Wort
                     "Gage 380 Euro, zusätzlich 90 Euro für Blumen."):  # kein Nebenkosten-Begriff
            self.assertEqual(len(zuordnung.fehlende_nebenkosten_position(text, start).positionen), 1, text)
        # schon als Position vorhanden
        zwei = Fakten(positionen=[P(betrag=D("380")), P(betrag=D("90"), bezeichnung="Anfahrt")])
        self.assertEqual(len(zuordnung.fehlende_nebenkosten_position(
            "Gage 380 Euro, außerdem 90 Euro Anfahrt.", zwei).positionen), 2)



class Kontaktangabe(unittest.TestCase):
    """Live-Lauf 15.10.2026 (KB-1641): 'Telefon 030 1234567' galt als Leistung 'Telefon' (Nebenkosten) -> Grenzfall."""

    def test_telefonnummer_ist_keine_leistung(self):
        from app import taetigkeiten as T

        self.assertEqual(T.erkenne("Werbetexte für die Webseite. Unser Büro: Tel. 0221 987654."), "T-03")
        self.assertIsNone(T.erkenne("Kontakt: Telefon +49 89 1234567"))

    def test_gegenbeispiel_telefonkosten_mit_betrag(self):
        from app import taetigkeiten as T

        self.assertEqual(T.erkenne("Telefonkosten 1234567 EUR"), "T-67")
        self.assertEqual(T.erkenne("Telefonkosten 120 €"), "T-67")



class AuftraggeberBeschreibungIstKeineLeistung(unittest.TestCase):
    """Live-Lauf 16.10.2026 (KB-0587): 'Unsere Agentur für Öffentlichkeitsarbeit … einem freien Sprecher' -> Grenzfall."""

    def test_eigene_beschreibung(self):
        from app import taetigkeiten as T

        self.assertEqual(T.erkenne("Wir sind eine Agentur für Grafikdesign und haben einen Fotografen bezahlt."), "T-04")

    def test_gegenbeispiel_beauftragte_agentur(self):
        from app import taetigkeiten as T

        self.assertEqual(T.erkenne("Wir haben eine Agentur für Öffentlichkeitsarbeit beauftragt."), "T-60")


class AuskunftMitJahrOhneRegister(unittest.TestCase):
    """Live-Lauf 16.10.2026 (Teil 3, 9 Fälle): 'Abgabesatz Künstlersozialabgabe 2031?' -- Modell ohne Jahr, System fragte
    nach dem Jahr. Die genannte Jahreszahl gilt; das Ergebnis ist dann 'Nicht abgedeckt'."""

    def test_jahr_ausserhalb_des_registers_wird_uebernommen(self):
        f = zuordnung.jahr_aus_freier_jahreszahl("Abgabesatz Künstlersozialabgabe 2031?",
                                                 Fakten(anfrageart="auskunft", auskunft_thema="abgabesatz"))
        self.assertEqual(f.jahr, 2031)

    def test_gegenbeispiel_bewertung_bleibt_bei_der_rueckfrage(self):
        f = zuordnung.jahr_aus_freier_jahreszahl("2031 zahlten wir einem Grafiker 900 Euro.", Fakten(anfrageart="bewertung"))
        self.assertIsNone(f.jahr)
        f = zuordnung.jahr_aus_freier_jahreszahl("Abgabesatz 2031 oder 2032?", Fakten(anfrageart="auskunft"))
        self.assertIsNone(f.jahr)


class BruttoDarinUmsatzsteuer(unittest.TestCase):
    """Live-Lauf 16.10.2026 (ganzer Korpus, Teil 2): '… 654,50 EUR brutto gezahlt, darin EUR 104,50 Umsatzsteuer' --
    16 von 45 Fällen endeten in einer Rückfrage, weil das Modell den Rest ohne Rechnungsbetrag oder zusätzlich zum
    Bruttobetrag anlegte. Der Rechnungsbetrag steht im Text; den Rest rechnet der Kern."""

    TEXT = "2025 zahlten wir einer freien Grafikerin 714,00 EUR brutto, darin EUR 114,00 Umsatzsteuer."

    def test_rest_ohne_rechnungsbetrag(self):
        f = Fakten(positionen=[P(betrag=D("600"), rest=True, bezeichnung="Grafik"), P(betrag=D("114.00"), rolle="ust")])
        f = zuordnung.berechne_restpositionen(f, self.TEXT)
        self.assertEqual([(r.auftragnehmer_nr, r.gesamtbetrag) for r in f.rechnungen], [(1, D("714.00"))])
        self.assertEqual(f.widersprueche, [])
        self.assertEqual(sorted(p.betrag for p in f.positionen), [D("114.00"), D("600.00")])

    def test_brutto_ust_und_selbst_gerechneter_rest(self):
        f = Fakten(rechnungen=[{"auftragnehmer_nr": 1, "gesamtbetrag": D("714")}],
                   positionen=[P(betrag=D("714"), bezeichnung="Grafik", auftragnehmer_nr=1),
                               P(betrag=D("114"), rolle="ust", auftragnehmer_nr=1),
                               P(betrag=D("599"), rest=True, auftragnehmer_nr=1)])
        f = zuordnung.berechne_restpositionen(f, self.TEXT)
        self.assertEqual(f.widersprueche, [])
        self.assertEqual(sorted(p.betrag for p in f.positionen), [D("114"), D("600")], "Rest rechnet der Kern, nicht das Modell")

    def test_umsatzsteuer_mit_cent_als_rest_markiert(self):
        """Live 16.10.2026 (KB-0491): 'darin EUR 104,50 Umsatzsteuer' -- das Modell markierte die Umsatzsteuer als Rest; der
        enthaltene Betrag wurde nur in ganzen Euro gelesen (104) und passte nicht -> Rückfrage."""
        text = "Wir zahlten 654,50 EUR brutto, darin EUR 104,50 Umsatzsteuer."
        f = Fakten(rechnungen=[{"auftragnehmer_nr": 1, "gesamtbetrag": D("654.50")}],
                   positionen=[P(betrag=D("654.50"), auftragnehmer_nr=1),
                               P(betrag=D("104.50"), rolle="ust", rest=True, auftragnehmer_nr=1)])
        f = zuordnung.berechne_restpositionen(f, text)
        self.assertEqual(f.widersprueche, [])
        self.assertEqual(sorted(p.betrag for p in f.positionen), [D("104.50"), D("550.00")])

    def test_gegenbeispiel_zwei_darin_angaben(self):
        text = "Rechnung A 714 EUR, darin 114 EUR Umsatzsteuer; Rechnung B 500 EUR, darin 80 EUR Material."
        f = Fakten(positionen=[P(betrag=D("600"), rest=True), P(betrag=D("114"), rolle="ust")])
        f = zuordnung.berechne_restpositionen(f, text)
        self.assertEqual(f.rechnungen, [])
        self.assertTrue(f.widersprueche, "unklar -> Rückfrage")



class MehrereFragenInEinerNachricht(unittest.TestCase):
    """Test des Nutzers im Codespace (16.10.2026): vier Beispielfragen in einer Nachricht."""

    TEXT = ("Wir sind eine Bäckerei mit Eigenwerbung, 2026 zahlten wir einem freien Grafiker 1.500 €. Ist das abgabepflichtig?\n"
            "„Wie hoch ist der Abgabesatz 2025?“\n„Gibt es ein Urteil zu Werbeagenturen?“\n"
            "„Wie hoch ist die Hundesteuer in Köln?“ (Hier soll „Nicht abgedeckt“ kommen.)")

    def test_zerlegen(self):
        self.assertEqual(zuordnung.zerlege_fragen(self.TEXT)[1:], [
            "Wie hoch ist der Abgabesatz 2025?", "Gibt es ein Urteil zu Werbeagenturen?",
            "Wie hoch ist die Hundesteuer in Köln?"])

    def test_alle_fragen_werden_nacheinander_beantwortet(self):
        """Wunsch des Nutzers: der Chat beantwortet alle Fragen, auch wenn sie zusammen kommen -- jede als eigener Fall."""
        from app import bestaetigung, router, warteschlange as W
        from app.llm.fake import FakeLLM

        llm = FakeLLM()
        a = W.bearbeite_nachricht(self.TEXT, llm)
        self.assertIn("4 Fragen", a.antwort)
        texte = [a.antwort]
        for _ in range(10):
            if a.ergebnisklasse == "Faktenbestätigung nötig":
                sid = a.sitzungskennung
                bestaetigung.SPEICHER.bestaetige(sid, a.fakten_hash)
                a = W.weiter(router.fuehre_nach_bestaetigung_aus(sid, llm), sid, llm)
            elif a.ergebnisklasse == "Rückfrage nötig" and a.rueckfrage_optionen:
                o, sid = a.rueckfrage_optionen[0], a.sitzungskennung
                a = W.weiter(router.wende_feldantwort_an(sid, o["feld"], list(o["werte"].values())[0], llm,
                                                         o.get("position")), sid, llm)
            else:
                break
            texte.append(a.antwort)
        alles = "\n".join(texte)
        for nr in range(1, 5):
            self.assertIn(f"Frage {nr} von 4", alles)
        self.assertIn("Abgabepflichtig (Vorschlag)", alles)
        self.assertIn("Nicht abgedeckt", texte[-1])

    def test_gegenbeispiel_zwei_fragen_zum_selben_fall(self):
        self.assertFalse(zuordnung.mehrere_fragen("2026 zahlten wir 900 Euro. Ist das abgabepflichtig? Wie hoch ist die Abgabe?"))
        self.assertFalse(zuordnung.mehrere_fragen("Rechnung über 900 Euro.\nIst das abgabepflichtig?\nMuss ich melden?"))


if __name__ == "__main__":
    unittest.main()
