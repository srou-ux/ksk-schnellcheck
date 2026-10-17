"""Dialogtests der Fehlerquellen-Serie HT-2026-075 bis 111 (Nutzer, 14.10.2026; Status ENTWURF).

Die Dialoge stehen in aufgaben/audit/dialoge_fehlerquellen/*.json und laufen auch live im Gesamtlauf
(tests/archiv/dialoge_soll.json, Vergleich von Hand). Hier offline: die Oberfläche wird nachgebildet wie in
app/static/index.html (nach einem fertigen Ergebnis ist der Fall abgeschlossen; die nächste Nachricht kommt mit
'letzte_sitzung'). Modell: Demo-Modus (app/llm/fake.py), bei HT-102 kontrollierte Modellantworten, weil der
Demo-Modus 'vier Rechnungen je 250 EUR' nicht als vier Positionen liest. Nur erfundene Daten.
"""
from __future__ import annotations

import json
import unittest
from decimal import Decimal as D
from pathlib import Path

from app import bestaetigung, pflichtangaben, router
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position as P

W = Path(__file__).resolve().parents[2]
ORDNER = W / "aufgaben" / "audit" / "dialoge_fehlerquellen"
OFFEN = ("rückfrage", "faktenbestätigung", "hinweis")


class Oberflaeche:
    """Wie app/static/index.html: Verlauf je Fall, Sitzung, nach fertigem Ergebnis Fall abgeschlossen."""

    def __init__(self, llm):
        self.llm, self.verlauf, self.sitzung, self.letzte, self.a = llm, [], None, None, None

    def _nach(self, a):
        self.a = a
        self.sitzung = a.sitzungskennung or None
        if not str(a.ergebnisklasse).lower().startswith(OFFEN):
            self.verlauf, self.letzte, self.sitzung = [], a.sitzungskennung or self.letzte, None
        return a

    def tippe(self, text):
        a = router.bearbeite_frage(text, self.llm, list(self.verlauf), self.sitzung, letzte_sitzung=self.letzte)
        self.verlauf.append(text)
        return self._nach(a)

    def knopf(self, feld, wert):
        return self._nach(router.wende_feldantwort_an(self.sitzung, feld, wert, self.llm))

    def bestaetige(self):
        assert self.a is not None and self.a.fakten_hash, "nichts zu bestätigen"
        bestaetigung.SPEICHER.bestaetige(self.sitzung, self.a.fakten_hash)
        return self._nach(router.fuehre_nach_bestaetigung_aus(self.sitzung, self.llm))


def spiele(name: str, llm=None) -> list:
    ui = Oberflaeche(llm or FakeLLM())
    antworten = []
    for schritt in json.loads((ORDNER / f"{name}.json").read_text(encoding="utf-8")):
        if "text" in schritt:
            antworten.append(ui.tippe(schritt["text"]))
        elif "knopf" in schritt:
            antworten.append(ui.knopf(*schritt["knopf"]))
        else:
            antworten.append(ui.bestaetige())
    return antworten


def _bestaetigt(a) -> str:
    return " ; ".join(a.fakten_zusammenfassung or [])


class DialogeFehlerquellen(unittest.TestCase):
    def test_ht_075_weiss_nicht_bei_veranstaltungszahl(self):
        a = spiele("ht075")
        self.assertEqual(a[0].rueckfragen, [pflichtangaben.FRAGE_VERANSTALTUNGSZAHL])
        self.assertEqual(a[-1].ergebnisklasse, "Grenzfall → Steuerberater entscheidet")
        self.assertEqual(a[-1].kern_protokoll.get("abgabe_falls_mehr"), D("122.50"))  # 2.500 × 4,9 %

    def test_ht_091_euro_betrag_als_antwort(self):
        a = spiele("ht091")
        self.assertIn("fremder Währung", a[0].rueckfragen[0])
        self.assertIn("4.102,30 €", _bestaetigt(a[1]))
        self.assertEqual(a[2].kern_protokoll.get("bemessungsgrundlage"), D("4102.30"))
        self.assertIsNone(a[2].kern_protokoll.get("abgabe"))  # 201,0127 € – Rundung ungeklärt (Grundregel 7)

    def test_ht_098_folgefrage_nennt_die_zahl(self):
        a = spiele("ht098")
        self.assertEqual(a[2].ergebnisklasse, "Abgabepflichtig (Vorschlag)")
        self.assertEqual(a[2].kern_protokoll.get("abgabe"), D("98.00"))
        self.assertIn("98,00 €", a[2].antwort)

    def test_ht_101_ander_fall(self):
        a = spiele("ht101")
        self.assertEqual(a[3].kern_protokoll.get("bemessungsgrundlage"), D("1500"))
        self.assertNotIn("2.000,00", _bestaetigt(a[2]))

    def test_ht_103_knopf_verliert_keine_fakten(self):
        a = spiele("ht103")
        self.assertIn("Jahr: 2026", _bestaetigt(a[2]))
        self.assertIn("2.000,00 €", _bestaetigt(a[2]))
        self.assertEqual(a[3].kern_protokoll.get("abgabe"), D("98.00"))

    def test_ht_107_jahr_als_antwort_ist_kein_betrag(self):
        a = spiele("ht107")
        self.assertEqual(a[0].rueckfragen, [pflichtangaben.FRAGE_JAHR])
        self.assertIn("Jahr: 2026", _bestaetigt(a[1]))
        self.assertNotIn("2.026,00", _bestaetigt(a[1]))
        self.assertEqual(a[2].kern_protokoll.get("bemessungsgrundlage"), D("2000"))

    def test_ht_108_eine_frage_nach_der_anderen(self):
        a = spiele("ht108")
        self.assertEqual(len(a[1].rueckfragen), 1)
        self.assertEqual(a[1].rueckfragen, [pflichtangaben.FRAGE_BETRAG])

    def test_ht_109_keine_ahnung_nie_still(self):
        a = spiele("ht109")
        self.assertNotIn(a[-1].ergebnisklasse, ("Abgabepflichtig (Vorschlag)", "Nicht abgabepflichtig (Vorschlag)"))
        self.assertIn("Einnahmeabsicht: ausdrücklich unbekannt", a[-1].antwort)
        self.assertEqual(a[-1].rueckfragen, [])  # keine Schleife: dieselbe Frage kommt nicht wieder

    def test_ht_110_dieselbe_frage_nicht_doppelt(self):
        a = spiele("ht110")
        self.assertEqual(a[3].kern_protokoll.get("bemessungsgrundlage"), D("2000"))

    def test_ht_111_ganzer_weg(self):
        a = spiele("ht111")
        self.assertEqual(a[0].ergebnisklasse, "Hinweis")
        self.assertEqual(a[1].ergebnisklasse, "Rückfrage nötig")
        self.assertIn("2.205,00 € (gezahlter Euro-Betrag; angegeben 2.400 USD)", _bestaetigt(a[2]))
        self.assertIn("mehreren Kalenderjahren (2020, 2026)", a[3].rueckfragen[0])
        # Teil 6 'ander Fall': neuer, leerer Fall
        self.assertEqual(a[5].rueckfragen, [pflichtangaben.FRAGE_JAHR])
        self.assertEqual(_bestaetigt(a[5]), "")


class Modell:
    """Kontrollierte Modellantworten in fester Reihenfolge (wie tests/app/test_testprotokoll_1110.py)."""

    def __init__(self, *antworten):
        self.antworten = list(antworten)

    def extrahiere_fakten(self, frage, verlauf=None, fallstand=None):
        return self.antworten.pop(0)

    def beschreibe_fall(self, kontext):  # pragma: no cover
        return ""


class KorrekturNachBestaetigung(unittest.TestCase):
    def test_ht_102_drei_statt_vier_rechnungen(self):
        vier = Fakten(jahr=2026, verwerterart="typischer_verwerter", auftragnehmer_typ="natuerliche_person",
                      leistungsart="Illustration", ein_auftragnehmer=True,
                      positionen=[P(betrag=D("250"), bezeichnung="Illustration", taetigkeit_id="T-08") for _ in range(4)])
        drei = vier.model_copy(update={"positionen": vier.positionen[:3]})
        a = spiele("ht102", Modell(vier, drei))
        self.assertEqual(a[0].ergebnisklasse, "Faktenbestätigung nötig")
        self.assertNotEqual(a[0].fakten_hash, a[1].fakten_hash)          # alte Bestätigung ungültig
        self.assertFalse(bestaetigung.SPEICHER.bestaetige(a[1].sitzungskennung, a[0].fakten_hash))
        self.assertEqual(a[2].kern_protokoll.get("bemessungsgrundlage"), D("750"))
        self.assertEqual(a[2].kern_protokoll.get("abgabe"), D("36.75"))


class KnopfSchicktNurDasFeld(unittest.TestCase):
    """HT-2026-104: ein Knopf schickt Feld und Wert an /knopf, nie den Anzeigetext als neue Frage."""

    def test_oberflaeche(self):
        html = (W / "app" / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('fetch("/knopf"', html)
        self.assertIn("feld: feld, wert: wert, position: position", html)

    def test_optionen_haben_feld_und_werte(self):
        opt = pflichtangaben.rueckfrage_optionen([pflichtangaben.FRAGE_VERWERTERART])
        # Schritt 2 (17.10.2026): Feld ist der Zweck des Auftrags, keine rechtliche Kategorie mehr im Knopf.
        self.assertEqual(opt[0]["feld"], "auftragszweck")
        self.assertIn("Werbung oder Öffentlichkeitsarbeit für Kunden", opt[0]["werte"])
        self.assertNotIn("Typischer Verwerter", opt[0]["werte"])


if __name__ == "__main__":
    unittest.main()
