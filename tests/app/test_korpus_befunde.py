"""Befunde aus dem Korpus 'Beispiele und Gegenbeispiele' (15.10.2026), LLM-unabhängig.

Mit perfekten Fakten (so, wie ein fehlerfreies Sprachmodell den Text liest) muss das System jeden Fall richtig lösen.
Der erste Lauf zeigte 110 Abweichungen; Ursachen und Behebungen stehen in aufgaben/FUNDE_Chatbot.md. Hier:
- je Ursache ein kleiner Test,
- eine Stichprobe des Korpus (jeder 10. Fall) mit perfekten Fakten: alle RICHTIG.
Der ganze Korpus läuft mit aufgaben/audit/korpus/lauf_offline.py (Protokoll in aufgaben/audit/TESTPROTOKOLL.md)."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from app import taetigkeiten as T
from app import zuordnung
from app.textnorm import waehrung_nach_hinten

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "aufgaben" / "audit"))


class Betragsschreibweise(unittest.TestCase):
    def test_waehrung_vor_der_zahl_wird_erkannt(self):
        self.assertEqual(waehrung_nach_hinten("darin EUR 66,50 Umsatzsteuer"), "darin 66,50 EUR Umsatzsteuer")
        self.assertEqual(waehrung_nach_hinten("€300 Honorar"), "300 € Honorar")
        self.assertEqual(zuordnung.betraege_im_text("EUR 1.500,00 und € 300"),
                         {__import__("decimal").Decimal("1500.00"), __import__("decimal").Decimal("300")})

    def test_andere_texte_bleiben(self):
        for t in ("1.500 EUR", "Euro-Zone", "Code EUR2026-1", "Europa"):
            self.assertEqual(waehrung_nach_hinten(t), t)


class Taetigkeitserkennung(unittest.TestCase):
    def test_laengerer_treffer_gewinnt(self):
        self.assertEqual(T.erkenne("Telefonakquise"), "T-35")  # nicht 'telefon' (Nebenkosten) dazu

    def test_vorrang_bleibt_bei_eingeschlossenem_treffer(self):
        # Musiklehrer: T-71 (Vorrang 0) darf nicht hinter einem längeren Treffer schwächeren Vorrangs verschwinden.
        self.assertEqual(T.erkenne("Musiklehrer (Musikschule, bis 20 Schueler)"), "T-71")

    def test_zusammengesetzte_woerter_nur_freigegebene(self):
        self.assertEqual(T.erkenne("Werbejingle"), "T-07")
        self.assertEqual(T.erkenne("Hochzeitsfotografin"), "T-04")
        self.assertEqual(T.erkenne("Produktfotos"), "T-04")
        self.assertIsNone(T.erkenne("Pressesprecher"))  # nicht 'Sprecher' (T-05)

    def test_zweck_des_auftraggebers_ist_keine_leistung(self):
        text = "Unsere Steuerkanzlei macht Öffentlichkeitsarbeit für sich selbst. Ein Komponist schrieb einen Werbejingle."
        self.assertEqual(T.erkenne(text), "T-07")
        self.assertEqual(T.erkenne("PR-Agentur für Öffentlichkeitsarbeit"), "T-60")


class Auskunft(unittest.TestCase):
    def test_grenzbetrag_ist_eine_auskunft_zur_schwelle(self):
        from app.schema import Fakten

        f = zuordnung.absichere_anfrageart("Ab welchem Betrag ist Eigenwerbung 2019 abgabepflichtig (Grenzbetrag)?",
                                           Fakten(anfrageart="auskunft", jahr=2019, auskunft_thema="schwelle"))
        self.assertEqual((f.anfrageart, f.auskunft_thema), ("auskunft", "schwelle"))


class KorpusStichprobe(unittest.TestCase):
    def test_jeder_zehnte_fall_mit_perfekten_fakten_ist_richtig(self):
        from pruefkatalog_lauf import bewerte, fuehre_fall_aus

        from app.llm.fake import FakeLLM
        from app.schema import Fakten

        korpus = json.loads((W / "aufgaben" / "audit" / "korpus_beispiele.json").read_text(encoding="utf-8"))
        falsch = []
        for fall in korpus["faelle"][::10]:
            llm = FakeLLM()
            llm.registriere(fall["frage"], Fakten.model_validate(fall["fakten"]))
            ergebnis, _f, _s = fuehre_fall_aus(fall, llm)
            urteil, gruende = bewerte(fall, ergebnis, korpus["kuerzel"])
            if urteil != "RICHTIG":
                falsch.append(f"{fall['id']} {urteil}: {gruende}")
        self.assertEqual(falsch, [])


if __name__ == "__main__":
    unittest.main()
