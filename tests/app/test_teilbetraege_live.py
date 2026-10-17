"""Schritt 2 (14.10.2026): Teilbeträge stabil lesen. Spielt die ECHTEN Modellantworten der
Live-Messung (Workflow 'Modellfehler suchen', Lauf 38559463415, mistral-large-latest, je Fall 6 Läufe)
offline durch: tests/app/daten_teilbetraege_live_1410.json. Vorher waren P-04a 1/6, P-04b 0/6,
P-28 2/6, P-30 6/6, P-32 1/6 richtig. Soll aus aufgaben/audit/pruefkatalog.json.
Die Knöpfe des Testlaufs (Art des Auftraggebers, Rechtsform) werden wie dort ergänzt, wenn das
Modell sie offen ließ. Erfundene Daten, ohne Netz."""
from __future__ import annotations

import json
import unittest
from decimal import Decimal as D
from pathlib import Path

from app import bestaetigung, router, zuordnung
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position as P, Rechnung as R

W = Path(__file__).resolve().parents[2]
LIVE = {k: v for k, v in json.loads((W / "tests/app/daten_teilbetraege_live_1410.json").read_text(encoding="utf-8")).items()
        if not k.startswith("_")}
KATALOG = {f["id"]: f for f in json.loads((W / "aufgaben/audit/pruefkatalog.json").read_text(encoding="utf-8"))["faelle"]}
KNOPF = {"Eigenwerbung": "eigenwerber", "Typischer Verwerter": "typischer_verwerter", "natürliche Person": "natuerliche_person"}
KLASSE = {"A": "Abgabepflichtig (Vorschlag)", "N": "Nicht abgabepflichtig (Vorschlag)"}


def _ergebnis(frage: str, roh: dict, knoepfe: dict):
    roh = dict(roh)
    roh.setdefault("verwerterart", KNOPF[knoepfe["verwerterart"]])
    roh.setdefault("auftragnehmer_typ", KNOPF[knoepfe["auftragnehmer_typ"]])
    llm = FakeLLM()
    llm.registriere(frage, Fakten.model_validate(roh))
    a = router.bearbeite_frage(frage, llm)
    if a.ergebnisklasse != "Faktenbestätigung nötig":
        return a, None
    bestaetigung.SPEICHER.bestaetige(a.sitzungskennung, a.fakten_hash)
    return a, router.fuehre_nach_bestaetigung_aus(a.sitzungskennung, FakeLLM())


class EchteModellantworten(unittest.TestCase):
    def test_jede_beobachtete_modellantwort_fuehrt_zum_soll(self):
        for fid, daten in LIVE.items():
            soll = KATALOG[fid]
            for nr, roh in enumerate(daten["modell"]):
                with self.subTest(fall=fid, antwort=nr):
                    a, c = _ergebnis(daten["frage"], roh, soll["knoepfe"])
                    self.assertIsNotNone(c, f"{fid}/{nr}: {a.ergebnisklasse}: {a.antwort[:300]}")
                    self.assertEqual(c.ergebnisklasse, KLASSE[soll["soll"][0]], c.antwort[:300])
                    for feld, wert in (soll.get("zahl") or {}).items():
                        self.assertEqual(c.kern_protokoll.get(feld), D(wert), f"{fid}/{nr} {feld}")


    def test_fehlt_der_enthaltene_betrag_wird_er_aus_dem_text_sichtbar_ergaenzt(self):
        """Soll geändert am 16.10.2026 (vorher: Rückfrage, 'nicht erfinden'). Begründung: das Modell machte denselben Fehler
        live wieder (F04, KB-0491/0521: ganzer Bruttobetrag als Umsatzsteuer, die enthaltene Umsatzsteuer fehlt), die
        Rückfrage 'Teilbetrag so hoch wie die ganze Rechnung' verstand der Nutzer nicht. Der fehlende Betrag wird nicht
        erfunden: er steht wörtlich im Text ('darin 190 € Umsatzsteuer'), genau ein 'X darin Y', mit dem Beleg-Wort genau
        einer Rolle (app/zuordnung.py::fehlender_enthaltener_teil). Er steht als eigene Zeile in der Faktenbestätigung –
        gerechnet wird erst nach der Bestätigung, also nicht still. Gleiche Linie wie fehlende_nebenkosten_position."""
        daten = LIVE["P-28"]
        soll = KATALOG["P-28"]
        for nr, roh in enumerate(daten.get("modell_ohne_enthaltenen_betrag", [])):
            with self.subTest(antwort=nr):
                a, c = _ergebnis(daten["frage"], roh, soll["knoepfe"])
                self.assertTrue(any("190,00 €" in z and "Umsatzsteuer" in z for z in a.fakten_zusammenfassung),
                                "der ergänzte Betrag steht sichtbar in der Bestätigung")
                self.assertIsNotNone(c, a.antwort[:300])
                self.assertEqual(c.ergebnisklasse, KLASSE[soll["soll"][0]])
                for feld, wert in (soll.get("zahl") or {}).items():
                    self.assertEqual(c.kern_protokoll.get(feld), D(wert), f"P-28/{nr} {feld}")

    def test_ohne_enthaltenen_betrag_im_text_bleibt_es_eine_rueckfrage(self):
        """Gegenprobe zur Änderung oben: steht der enthaltene Betrag NICHT im Text, wird nichts ergänzt."""
        daten = LIVE["P-28"]
        frage = "Unsere Werbeagentur hat 2025 einem freien Fotografen (Einzelperson) 1.190 € brutto gezahlt, Umsatzsteuer gesondert ausgewiesen."
        for nr, roh in enumerate(daten.get("modell_ohne_enthaltenen_betrag", [])):
            with self.subTest(antwort=nr):
                a, c = _ergebnis(frage, roh, KATALOG["P-28"]["knoepfe"])
                self.assertIsNone(c, "ohne Betrag im Text darf nicht gerechnet werden")


class Gegenproben(unittest.TestCase):
    """Echte Unstimmigkeiten bleiben eine Rückfrage."""

    def test_rechnung_mit_teil_in_voller_hoehe_und_weiterem_teil_bleibt_widerspruch(self):
        text = "Rechnung über 1.200 €: Gestaltung 1.200 €, Druck 300 €."
        f = Fakten(positionen=[P(betrag=D("1200"), auftragnehmer_nr=1), P(betrag=D("300"), auftragnehmer_nr=1)],
                   rechnungen=[R(auftragnehmer_nr=1, gesamtbetrag=D("1200"))])
        g = zuordnung.berechne_restpositionen(zuordnung.einzelrechnungen_je_position(text, f), text)
        self.assertTrue(any(w.feld == "rechnungen.1" for w in g.widersprueche))

    def test_ungleiche_anzahl_bleibt(self):
        text = "Zwei Rechnungen zu je 250 €, insgesamt drei Leistungen."
        f = Fakten(positionen=[P(betrag=D("250"), auftragnehmer_nr=1)] * 3,
                   rechnungen=[R(auftragnehmer_nr=1, gesamtbetrag=D("250"))] * 2)
        self.assertEqual(len(zuordnung.einzelrechnungen_je_position(text, f).rechnungen), 2)

    def test_mit_darin_bleiben_die_rechnungen(self):
        text = "Zwei Rechnungen: 1.000 €, darin 200 € Druck, und 200 €."
        f = Fakten(positionen=[P(betrag=D("1000"), auftragnehmer_nr=1), P(betrag=D("200"), auftragnehmer_nr=1)],
                   rechnungen=[R(auftragnehmer_nr=1, gesamtbetrag=D("1000")), R(auftragnehmer_nr=1, gesamtbetrag=D("200"))])
        self.assertEqual(len(zuordnung.einzelrechnungen_je_position(text, f).rechnungen), 2)

    def test_eigene_rolle_auf_vollem_betrag_bleibt_ohne_doppelte_rolle(self):
        # Reisekosten in voller Höhe der Rechnung, darin ein anderer Teil: nicht umdeuten.
        text = "Rechnung 500 €, darin 100 € Honorar."
        f = Fakten(positionen=[P(betrag=D("500"), auftragnehmer_nr=1, rolle="fahrtkosten_nachgewiesen"),
                               P(betrag=D("100"), auftragnehmer_nr=1, rolle="honorar")],
                   rechnungen=[R(auftragnehmer_nr=1, gesamtbetrag=D("500"))])
        g = zuordnung.berechne_restpositionen(f, text)
        self.assertTrue(any(w.feld == "rechnungen.1" for w in g.widersprueche))


class NachtragUndBezeichnung(unittest.TestCase):
    def test_nachtrag_fuenf_rechnungen_im_laufenden_fall(self):
        d = LIVE["P-04a"]
        roh = dict(d["modell"][0], verwerterart="eigenwerber")
        nachtrag = "Es ist Eigenwerbung, insgesamt fünf Rechnungen zu je 250 €."
        llm = FakeLLM()
        llm.registriere(d["frage"], Fakten.model_validate(roh))
        llm.registriere(nachtrag, Fakten.model_validate(roh))
        a = router.bearbeite_frage(d["frage"], llm)
        b = router.bearbeite_frage(nachtrag, llm, [d["frage"]], a.sitzungskennung)
        self.assertEqual(b.ergebnisklasse, "Faktenbestätigung nötig", b.antwort[:300])
        bestaetigung.SPEICHER.bestaetige(b.sitzungskennung, b.fakten_hash)
        c = router.fuehre_nach_bestaetigung_aus(b.sitzungskennung, FakeLLM())
        self.assertEqual(c.kern_protokoll.get("abgabe"), D("61.25"))

    def test_eine_rechnung_mit_ungleichen_teilen_bleibt_widerspruch(self):
        text = "Eine Rechnung über 250 €: Logo 250 €, Plakat 100 €."
        f = Fakten(positionen=[P(betrag=D("250"), auftragnehmer_nr=1), P(betrag=D("100"), auftragnehmer_nr=1)],
                   rechnungen=[R(auftragnehmer_nr=1, gesamtbetrag=D("250"))])
        self.assertEqual(len(zuordnung.einzelrechnungen_je_position(text, f).rechnungen), 1)

    def test_gleiche_bezeichnung_nutzt_die_genannte_leistung(self):
        text = "Ein Grafiker hat dreimal Werbegrafiken gestaltet, je 400 €."
        f = Fakten(anfrageart="bewertung", leistungsart="Grafik/Design",
                   positionen=[P(betrag=D("400"), bezeichnung="Werbegrafiken")] * 3)
        g = zuordnung.ergaenze_taetigkeit(text, f)
        self.assertEqual({p.taetigkeit_id for p in g.positionen}, {"T-02"})

    def test_verschiedene_bezeichnungen_bekommen_die_leistung_nicht_vererbt(self):
        text = "Ein Grafiker: Werbegrafiken 400 €, Bürobedarf 50 €."
        f = Fakten(anfrageart="bewertung", leistungsart="Grafik/Design",
                   positionen=[P(betrag=D("400"), bezeichnung="Werbegrafiken"), P(betrag=D("50"), bezeichnung="Bürobedarf")])
        g = zuordnung.ergaenze_taetigkeit(text, f)
        self.assertNotEqual(g.positionen[1].taetigkeit_id, "T-02")


class RolleDarin(unittest.TestCase):
    def test_rolle_nur_mit_beleg_am_enthaltenen_betrag_und_in_der_bezeichnung(self):
        text = "1.190 € brutto, darin 190 € Umsatzsteuer gesondert ausgewiesen."
        f = Fakten(positionen=[P(betrag=D("1190"), bezeichnung="Honorar inkl. Umsatzsteuer"),
                               P(betrag=D("190"), bezeichnung="Umsatzsteuer gesondert ausgewiesen")])
        g = zuordnung.ergaenze_rolle_darin(text, f)
        self.assertEqual([p.rolle for p in g.positionen], [None, "ust"])

    def test_ohne_wort_in_der_bezeichnung_keine_rolle(self):
        text = "1.190 € brutto, darin 190 € Umsatzsteuer."
        f = Fakten(positionen=[P(betrag=D("190"), bezeichnung="Zusatzleistung")])
        self.assertIsNone(zuordnung.ergaenze_rolle_darin(text, f).positionen[0].rolle)

    def test_ohne_darin_keine_rolle(self):
        text = "Wir haben 190 € Umsatzsteuer und 1.000 € Honorar gezahlt."
        f = Fakten(positionen=[P(betrag=D("190"), bezeichnung="Umsatzsteuer")])
        self.assertIsNone(zuordnung.ergaenze_rolle_darin(text, f).positionen[0].rolle)

    def test_nur_rechnungen_ohne_positionen_werden_positionen(self):
        text = "fünfmal kleine Werbegrafiken, jede Rechnung 250 € netto"
        f = Fakten(rechnungen=[R(auftragnehmer_nr=1, gesamtbetrag=D("250"))] * 5)
        g = zuordnung.einzelrechnungen_je_position(text, f)
        self.assertEqual(([p.betrag for p in g.positionen], g.rechnungen), ([D("250")] * 5, []))

    def test_rechnungsbetrag_nicht_im_text_wird_keine_position(self):
        f = Fakten(rechnungen=[R(auftragnehmer_nr=1, gesamtbetrag=D("999"))])
        self.assertEqual(zuordnung.einzelrechnungen_je_position("Rechnung über 250 €", f).positionen, [])


class DavonAnDritte(unittest.TestCase):
    """Live 14.10.2026 (5584e86): P-39 FALSCH -- 2.500 € statt 2.000 €. Das Modell legte die Rechnung
    über 2.000 € selbst an und gab die 500 € 'davon an den Manager' einem zweiten Auftragnehmer.
    Der alte Code rechnete mit diesen Fakten ebenso falsch (Lücke älter als Schritt 2)."""

    FRAGE = ("Wir sind eine Konzertdirektion. Eine selbständige Sängerin (Einzelperson) bekommt 2025 eine Gage "
             "von 2.000 €. Auf ihren Wunsch zahlen wir davon 500 € direkt an ihren Manager. Wie hoch ist die Bemessungsgrundlage?")

    def _fakten(self, rechnungen):
        return Fakten(anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter",
                      auftragnehmer_typ="natuerliche_person", leistungsart="Musik", ein_auftragnehmer=False,
                      positionen=[P(betrag=D("2000"), bezeichnung="Gage für Sängerin", auftragnehmer_nr=1),
                                  P(betrag=D("500"), bezeichnung="Zahlung an Manager auf Wunsch der Sängerin", auftragnehmer_nr=2)],
                      rechnungen=rechnungen)

    def _bg(self, fakten):
        llm = FakeLLM()
        llm.registriere(self.FRAGE, fakten)
        a = router.bearbeite_frage(self.FRAGE, llm)
        bestaetigung.SPEICHER.bestaetige(a.sitzungskennung, a.fakten_hash)
        return router.fuehre_nach_bestaetigung_aus(a.sitzungskennung, FakeLLM()).kern_protokoll.get("bemessungsgrundlage")

    def test_mit_rechnung_des_modells(self):
        self.assertEqual(self._bg(self._fakten([R(auftragnehmer_nr=1, gesamtbetrag=D("2000"))])), D("2000"))

    def test_ohne_rechnung(self):
        self.assertEqual(self._bg(self._fakten([])), D("2000"))

    def test_rechnung_mit_anderem_betrag_wird_nicht_umgedeutet(self):
        f = self._fakten([R(auftragnehmer_nr=1, gesamtbetrag=D("2500"))])
        g = zuordnung.enthaltene_betraege_nicht_doppelt(self.FRAGE, f)
        self.assertEqual(g, f)


class BelegWortImNaechstenListenteil(unittest.TestCase):
    """Live 14.10.2026 (9d63759): P-52 FALSCH -- 'Miete für Kamera-Equipment 200 € netto, Druckkosten für
    den Nachdruck … 500 € netto': das Modell setzte für die 200 € die Rolle Vervielfältigung; das 'Druck'
    der nächsten Position galt als Beleg."""

    TEXT = ("Webdesign 2.000 € netto, Programmierung des Backends 1.000 € netto, Miete für Kamera-Equipment "
            "200 € netto, Druckkosten für den Nachdruck der fertigen Flyer 500 € netto.")

    def test_beleg_des_naechsten_listenteils_zaehlt_nicht(self):
        f = Fakten(positionen=[P(betrag=D("200"), bezeichnung="Miete für Kamera-Equipment", rolle="vervielfaeltigung_nachtraeglich"),
                               P(betrag=D("500"), bezeichnung="Druckkosten für den Nachdruck", rolle="vervielfaeltigung_nachtraeglich")])
        g = zuordnung.absichere_rollen(self.TEXT, f)
        self.assertEqual([p.rolle for p in g.positionen], [None, "vervielfaeltigung_nachtraeglich"])

    def test_nachweis_ohne_eigenen_betrag_zaehlt_weiter(self):
        text = "3.000 € Honorar und 80 € Fahrtkosten, nachgewiesen durch Ticket."
        self.assertIn(D("80"), zuordnung._betraege_am_begriff(text, ["nachgewiesen"]))

    def test_dezimalkomma_trennt_nicht(self):
        text = "Rechnung 1.190,00 € brutto, darin 190,00 € Umsatzsteuer"
        self.assertIn(D("190.00"), zuordnung._betraege_am_begriff(text, ["umsatzsteuer"]))
        self.assertNotIn(D("1190.00"), zuordnung._betraege_am_begriff(text, ["umsatzsteuer"]))
