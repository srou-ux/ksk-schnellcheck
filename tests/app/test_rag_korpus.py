"""Quellenabruf (RAG) gegen die echte Quellenbasis: Beispiele und Gegenbeispiele (RAG-Korpus, 15.10.2026).

Der Abruf ist Stichwortsuche über lokale Quellen und damit unabhängig vom Sprachmodell. Gemessen wird der ganze Korpus
mit aufgaben/audit/korpus/rag_korpus.py (Protokoll: aufgaben/audit/TESTPROTOKOLL.md); hier je Befund ein Beispiel und
ein Gegenbeispiel sowie eine Untergrenze für den ganzen Korpus. Nur erfundene Fragen."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

from app.rag.suche import hat_themenbezug, suche

W = Path(__file__).resolve().parents[2]


class AbgabesatzMitJahr(unittest.TestCase):
    def test_abgabesatz_findet_die_verordnung_des_jahres(self):
        # Die Verordnungen sagen 'Prozentsatz' (Synonym in app/rag/konfig.json).
        for jahr in (2020, 2024):
            e = suche("Wie hoch ist der Abgabesatz der Künstlersozialabgabe?", jahr)
            dateien = " ".join(t.datei + t.fundstelle for t in e.stuecke)
            self.assertIn(str(jahr), dateien, [t.fundstelle for t in e.stuecke])


class Aktenzeichen(unittest.TestCase):
    def test_vorhandenes_aktenzeichen_wird_gefunden(self):
        e = suche("Was hat das Gericht im Verfahren B 3 KS 3/21 R entschieden?")
        self.assertTrue(any("B 3 KS 3/21 R" in t.fundstelle for t in e.stuecke), [t.fundstelle for t in e.stuecke])

    def test_erfundenes_aktenzeichen_ergibt_nicht_abgedeckt(self):
        e = suche("Was hat das Gericht im Verfahren B 3 KS 47/21 R entschieden?")
        self.assertTrue(e.leer, [t.fundstelle for t in e.stuecke])
        self.assertIn("Nicht abgedeckt", e.grund)


class Fachfremd(unittest.TestCase):
    PAARE = [("Wie hoch ist die Hundesteuer in Köln?", "Wie hoch ist die Künstlersozialabgabe für eine Werbeagentur?"),
             ("Welche Kündigungsfrist gilt für meinen Mietvertrag?",
              "Welche Frist gilt für die Meldung der Entgelte an die Künstlersozialkasse?"),
             ("Brauche ich eine Baugenehmigung für einen Carport?",
              "Brauche ich eine Abgabenummer der Künstlersozialkasse als Verlag?")]

    def test_fachfremd_leer_fachlich_mit_quellen(self):
        for fremd, fach in self.PAARE:
            e = suche(fremd)
            self.assertTrue(e.leer, (fremd, [t.fundstelle for t in e.stuecke]))
            self.assertTrue(suche(fach).stuecke, fach)

    def test_themenbezug(self):
        self.assertTrue(hat_themenbezug("Zahlung 2025 an einen Steuerberater: 900 EUR."))  # Fallbeschreibung mit Betrag
        self.assertTrue(hat_themenbezug("Gibt es ein Urteil zu B 3 KS 1/10 R?"))
        self.assertTrue(hat_themenbezug("Muss der Musikverein melden?"))
        self.assertFalse(hat_themenbezug("Darf ich im Garten ein Feuer machen?"))

    def test_mit_regelfilter_kein_themenfilter(self):
        # Regeln, die der Kern verwendet hat, werden immer geliefert (der Themenfilter gilt nur für die freie Suche).
        e = suche("Feuer im Garten", regel_ids=["R-01"])
        self.assertTrue(any("R-01" in t.regel_ids for t in e.stuecke))


class GanzerKorpus(unittest.TestCase):
    def test_untergrenze(self):
        sys.path.insert(0, str(W / "aufgaben" / "audit" / "korpus"))
        import rag_korpus

        richtig = gesamt = 0
        for fall in rag_korpus.faelle():
            ok, _ = rag_korpus.bewerte(fall, suche(fall["frage"], fall["jahr"]))
            richtig += ok
            gesamt += 1
        # Gemessen 15.10.2026: 307 von 327 (vorher 271); 16.10.2026: 310. Untergrenze gegen Rückschritt.
        self.assertGreaterEqual(richtig, 300, f"{richtig}/{gesamt}")


class AbrufGueteZiel(unittest.TestCase):
    def test_ziel_90_prozent(self):
        """16.10.2026: Ziel des RAG-Auftrags (90 %) mit 270 von 299 erreicht (aufgaben/RAG_Bericht.md). Gemessen an
        denselben Testfällen, an denen die Einstellungen geprüft wurden -- kein unabhängiger Nachweis; Untergrenze
        gegen Rückschritt."""
        from app.rag import guete

        z = guete.miss()["zaehler"]
        self.assertGreaterEqual(z["treffer"] / (z["treffer"] + z["fehlschlag"]), 0.90)


if __name__ == "__main__":
    unittest.main()
