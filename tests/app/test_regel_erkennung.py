"""Regel-Erkennung der Leistung und Einordnung des Auftraggebers – ohne KI (17.10.2026).

Übernommen aus den früheren Chat-Tests (tests/app/test_taetigkeiten.py, test_einordnung.py): nur die Teile, die
ohne Sprachmodell gelten. Die Erkennung braucht „Rechnungen prüfen“ für die gelesenen Positionsbezeichnungen.
Erfundene Testdaten."""
from __future__ import annotations

import unittest
from decimal import Decimal as D

from app import bewertung, taetigkeiten as T
from app.einordnung import leite_ab
from app.ergebnisklassen import GRENZFALL
from app.schema import Fakten, Position as P


class TestErkennung(unittest.TestCase):
    def test_blatt_ist_geladen_und_jede_zeile_hat_eine_quelle(self):
        self.assertGreater(len(T.alle()), 20)
        for e in T.alle():
            self.assertTrue(e["regel_ids"] or e["fundstellen"], f"{e['id']} ohne Fundstelle")
            self.assertTrue(e["status"].startswith("Entwurf"), e["id"])

    def test_typische_leistungen(self):
        faelle = {
            "Programmierung des Backends (reines Coding)": "nicht_kuenstlerisch",
            "Webdesign & UI-Konzeption": "kuenstlerisch",
            "Webdesigner gestaltet und programmiert die Seiten": "kuenstlerisch",  # R-184
            "Korrektorat und Rechtschreibprüfung": "nicht_kuenstlerisch",
            "Lektorat mit Überarbeitung des Stils": "kuenstlerisch",
            "Moderation des Firmen-Workshops": "nicht_kuenstlerisch",  # R-183
            "Moderation der Jubiläumsgala": "kuenstlerisch",
            "SEO-Analyse": "nicht_kuenstlerisch",
            "Schaltung von Google-Ads": "nicht_kuenstlerisch",
            "Übersetzung der Website (Kreativtext)": "kuenstlerisch",
            "Übersetzung": "unsicher",
            "Miete für Kamera-Equipment": "unsicher",
            "Logo-Gestaltung": "kuenstlerisch",
        }
        for text, gruppe in faelle.items():
            self.assertEqual(T.gruppe(T.erkenne(text)), gruppe, text)

    def test_unbekannt_und_nichts(self):
        self.assertIsNone(T.erkenne("Beratung zur Datenschutz-Grundverordnung"))
        self.assertIsNone(T.erkenne("Evaluation des Konzerts durch eine Soziologin"))
        self.assertEqual(T.erkenne("Konzert"), "T-07")
        self.assertEqual(T.erkenne("Konzerthonorar"), "T-07")
        self.assertEqual(T.kombiniere(None, None, beschrieben=True), T.UNBEKANNT)
        self.assertIsNone(T.kombiniere(None, None, beschrieben=False))
        self.assertEqual(T.gruppe(T.UNBEKANNT), "unsicher")


class TestEinordnung(unittest.TestCase):
    """app/einordnung.py::leite_ab – Kategorie nur aus den getrennten Fakten (Tätigkeit des Auftraggebers, Zweck)."""

    def fall(self, **k):
        return leite_ab(Fakten(**k)).verwerterart

    def test_zweck_bestimmt_die_kategorie(self):
        self.assertEqual(self.fall(auftragszweck="eigene_werbung", katalog_taetigkeit=False), "eigenwerber")
        self.assertEqual(self.fall(auftragszweck="veranstaltung", katalog_taetigkeit=False), "generalklausel")
        self.assertEqual(self.fall(auftragszweck="privat", katalog_taetigkeit=False), "privat")
        self.assertEqual(self.fall(auftragszweck="fuer_kunden"), "typischer_verwerter")

    def test_katalog_taetigkeit_geht_vor(self):
        # Ein Verlag, der für sich selbst wirbt, bleibt typischer Verwerter.
        self.assertEqual(self.fall(auftragszweck="eigene_werbung", katalog_taetigkeit=True), "typischer_verwerter")

    def test_widerspruch_und_unbekannt_bleiben_offen(self):
        self.assertIsNone(self.fall(auftragszweck="fuer_kunden", katalog_taetigkeit=False))
        self.assertIsNone(self.fall())


class TestDerselbeKuenstler(unittest.TestCase):
    """Mehrere Positionen desselben Künstlers (R-42, R-117, R-175; R-49 Druck): früher über den Chat geprüft, jetzt direkt
    über app/bewertung.py (derselbe Kernaufruf wie „Rechnungen prüfen“). Gleiche Soll-Werte wie die alten Tests."""

    def lauf(self, paare, nr=None, **k):
        pos = [P(betrag=D(b), bezeichnung=t, auftragnehmer_typ="natuerliche_person", auftragnehmer_nr=nr,
                 taetigkeit_id=T.erkenne(t) or T.UNBEKANNT) for t, b in paare]
        ke, pr = bewertung._kern_mit_gegenrechnung(Fakten(anfrageart="bewertung", jahr=2026,
                                                          verwerterart="typischer_verwerter", positionen=pos, **k))
        self.assertEqual(pr.status, "bestaetigt")
        return ke

    def test_designer_rechnet_gestaltung_programmierung_miete_und_druck_ab(self):
        k = self.lauf([("Webdesign", "2000"), ("Programmierung des Backends", "1000"),
                       ("Miete für Kamera-Equipment", "200"), ("Druckkosten", "500")], ein_auftragnehmer=True)
        self.assertEqual(k.klasse, "Abgabepflichtig (Vorschlag)")
        self.assertEqual(D(str(k.protokoll["bemessungsgrundlage"])), D("3200"))  # ohne Druck (R-49)
        self.assertIn("Druckkosten", k.protokoll["taetigkeit_nicht"])

    def test_verschiedene_auftragnehmer_zaehlen_einzeln(self):
        k = self.lauf([("Webdesign", "2000"), ("Programmierung des Backends", "1000")], ein_auftragnehmer=False)
        self.assertEqual(D(str(k.protokoll["bemessungsgrundlage"])), D("2000"))

    def test_eigenstaendige_leistung_desselben_kuenstlers_entscheidet_der_steuerberater(self):
        k = self.lauf([("Fotografie", "1500"), ("SEO-Analyse", "500")], nr=1)
        self.assertEqual(k.klasse, GRENZFALL)
        self.assertEqual(D(str(k.protokoll["abgabe_ohne_unsichere"])), D("73.50"))
        self.assertEqual(D(str(k.protokoll["abgabe_falls_kuenstlerisch"])), D("98.00"))


if __name__ == "__main__":
    unittest.main()
