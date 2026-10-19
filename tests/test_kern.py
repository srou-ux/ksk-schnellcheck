"""Führt Testfälle gegen den Regelkern aus (kern/rechnen.py). Aufruf:  python tests/test_kern.py
Die Kennung (Q-01 …) verweist auf Regelwerk/Testfaelle_BSG_Urteile.xlsx. Entwurf – vom Steuerberater zu prüfen."""
import sys, pathlib, unittest, datetime
from decimal import Decimal as D
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from kern import rechnen as K


class Q(unittest.TestCase):
    def test_Q01_eigenwerbung_2025_900(self):
        e = K.pruefe_eigenwerbung(2025, 900)
        self.assertEqual(e.klasse, K.ABGABEPFLICHTIG); self.assertEqual(e.abgabe, D("45.00"))

    def test_Q02_eigenwerbung_2026_900(self):
        e = K.pruefe_eigenwerbung(2026, 900)
        self.assertEqual(e.klasse, K.NICHT); self.assertIsNone(e.abgabe)

    def test_Q03_werbeagentur_2026(self):
        e = K.pruefe_typischer_verwerter(2026, 900)
        self.assertEqual(e.klasse, K.ABGABEPFLICHTIG); self.assertEqual(e.abgabe, D("44.10"))

    def test_Q04_rechnung_dez_zahlung_jan(self):
        jahr, rueck = K.zahlungsjahr(datetime.date(2026, 1, 15))
        self.assertEqual(jahr, 2026); self.assertIsNone(rueck)
        e = K.pruefe_typischer_verwerter(jahr, 2000)
        self.assertEqual(e.abgabe, D("98.00"))
        _, rueck = K.zahlungsjahr(None); self.assertEqual(rueck.klasse, K.RUECKFRAGE)

    def test_Q05_vertreter_status_unbekannt(self):
        self.assertEqual(K.vertreter().klasse, K.RUECKFRAGE)
        self.assertEqual(K.vertreter(True, True).klasse, K.NICHT)
        self.assertEqual(K.vertreter(False, True).klasse, K.ABGABEPFLICHTIG)

    def test_Q06_musikverein_45_schueler_unbekannt(self):
        self.assertEqual(K.musikverein_schueler(2026, 45).klasse, K.RUECKFRAGE)

    def test_Q07_vervielfaeltigung(self):
        e = K.vervielfaeltigung(1200, 800); e.abgabe, _ = K.berechne_abgabe(e.bemessungsgrundlage, 2026)
        self.assertEqual(e.bemessungsgrundlage, D(1200)); self.assertEqual(e.abgabe, D("58.80"))

    def test_Q08_reisekosten_ohne_nachweis(self):
        e = K.reisekosten_ohne_nachweis(300)
        self.assertEqual(e.klasse, K.RUECKFRAGE); self.assertEqual(e.bemessungsgrundlage, D(300))

    def test_Q09_genau_8_stunden(self):
        n, e = K.verpflegung(2025, 8, erstattung=14)
        self.assertEqual(n, D(0)); self.assertEqual(e.klasse, K.GRENZFALL)
        self.assertEqual(D(1000) + D(14) - n, D(1014))

    def test_Q10_8_stunden_1_minute(self):
        n, e = K.verpflegung(2025, D("8.0167"), erstattung=14)
        self.assertEqual(n, D(14)); self.assertEqual(D(1000) + D(14) - n, D(1000))

    def test_Q11_bis_Q16_grenzwerte(self):
        for jahr, s, soll in ((2025, "699.99", K.NICHT), (2025, "700.00", K.NICHT), (2025, "700.01", K.ABGABEPFLICHTIG),
                              (2026, "999.99", K.NICHT), (2026, "1000.00", K.NICHT), (2026, "1000.01", K.ABGABEPFLICHTIG)):
            with self.subTest(jahr=jahr, summe=s):
                self.assertEqual(K.pruefe_eigenwerbung(jahr, s).klasse, soll)


class Weitere(unittest.TestCase):
    def test_netto_ohne_ust(self):  # M-01 / B-01
        self.assertEqual(K.netto(11900, 1900), D(10000))
        e = K.pruefe_typischer_verwerter(2025, K.netto(11900, 1900)); self.assertEqual(e.abgabe, D("500.00"))

    def test_fassung_a_450(self):  # R-10
        self.assertEqual(K.pruefe_eigenwerbung(2021, 450).klasse, K.NICHT)
        self.assertEqual(K.pruefe_eigenwerbung(2021, 900).klasse, K.GRENZFALL)

    def test_jahr_ohne_regel(self):
        self.assertEqual(K.pruefe_eigenwerbung(2010, 900).klasse, K.NICHT_ABGEDECKT)
        self.assertEqual(K.pruefe_eigenwerbung(2030, 900).klasse, K.NICHT_ABGEDECKT)

    def test_alle_jahre_haben_satz(self):
        for j in range(2015, 2028): self.assertIsNotNone(K.abgabesatz(j))

    def test_rundung_nicht_geraten(self):
        a, h = K.berechne_abgabe("700.01", 2025)
        self.assertIsNone(a); self.assertIn("Rundung", h)

    def test_verpflegung_24h_und_uebernachtung(self):
        self.assertEqual(K.verpflegung(2025, 24, erstattung=40)[0], D(28))
        self.assertEqual(K.verpflegung(2025, 5, uebernachtung=True, erstattung=14)[0], D(14))
        self.assertEqual(K.verpflegung(2018, 9, erstattung=20)[0], D(12))

    def test_vorauszahlung_ohne_rundungsrest(self):
        """Korpus-Lauf 15.10.2026: 14.000 € / 12 × 4,2 % ist genau 49,00 € (vorher 48,999… -> 'Rundung ungeklärt')."""
        betrag, e = K.vorauszahlung_monatlich(2019, D(14000))
        self.assertEqual((betrag, e.klasse), (D("49.00"), K.ABGABEPFLICHTIG))

    def test_rechnungsposition_ohne_einordnung_wird_nachgefragt(self):
        """Teil 1e (15.10.2026), Befund der Gegenrechnung: eine Position ohne oder mit unbekannter Rolle zählte still
        mit 0. Jetzt: offen und Rückfrage ('nie geraten'), auch wenn der Empfänger abgabepflichtig ist."""
        pos = [{"nr": 1, "betrag": 900, "rolle": "vertretung_kuenstler"}, {"nr": 2, "betrag": 500, "rolle": None},
               {"nr": 3, "betrag": 200, "rolle": "unbekannt"}]
        e, z = K.analysiere_rechnung(2026, pos, True, True)
        self.assertEqual(e.klasse, K.RUECKFRAGE)
        self.assertEqual(e.bemessungsgrundlage, D(900))
        self.assertEqual(sum(x["offen"] for x in z), D(700))
        self.assertEqual(len([r for r in e.rueckfragen if r.startswith("Position ")]), 2)

    def test_H05_rechnungssummen(self):
        pos = [2400, 1180, 1360, 940, 850, 720, 125, 380, 145, 206, 310, 340]
        self.assertEqual(sum(D(x) for x in pos), D(8956))
        basis = D(8956) - 850 - 206
        self.assertEqual(basis, D(7900)); self.assertEqual(basis * D("0.19"), D("1501.00")); self.assertEqual(D(8956) + D(1501), D(10457))

    def test_parameter_passen_zum_katalog(self):
        import subprocess
        r = subprocess.run([sys.executable, "-I", str(pathlib.Path(__file__).resolve().parent.parent / "kern" / "erzeuge_parameter.py"), "--pruefen"])
        self.assertEqual(r.returncode, 0)

class Regelregister(unittest.TestCase):
    SCHLUESSEL = ["schwelle.operator", "verpflegung.stunden_grenze", "verpflegung.stunden_ganztag", "verpflegung.pauschale_klein",
                  "verpflegung.pauschale_gross", "vorauszahlung.untergrenze", "vorauszahlung.monate", "saeumnis.stufe",
                  "saeumnis.satz_prozent", "saeumnis.bagatell_gesondert", "meldefrist.monat", "meldefrist.tag",
                  "aufbewahrung.jahre", "rechtsform.kein_entgelt", "musikverein.schueler_grenze", "saeumnis.addition_vor_abrundung"]

    def test_schluessel_fuer_2019_bis_2027_vorhanden(self):
        for j in range(2019, 2028):
            for k in self.SCHLUESSEL:
                K._zeilen(k, j)

    def test_jede_zeile_hat_fundstelle_und_status(self):
        for r in K.P["register"]:
            self.assertTrue(r["fundstelle"], r["schluessel"])
            self.assertIn("Steuerberater", r["status"], r["schluessel"])

    def _mit(self, schluessel, **neu):
        import copy
        alt = K.P["register"]
        K.P["register"] = [dict(r, **neu) if r["schluessel"] == schluessel else r for r in copy.deepcopy(alt)]
        return alt

    def test_aenderung_im_register_aendert_ergebnis(self):
        # Pauschale 14 -> 15: Erstattung 15 € wird dann voll nicht mitgezählt
        self.assertEqual(K.verpflegung(2026, 10, erstattung=15)[0], 14)
        alt = self._mit("verpflegung.pauschale_klein", wert="15")
        try:
            self.assertEqual(K.verpflegung(2026, 10, erstattung=15)[0], 15)
        finally:
            K.P["register"] = alt
        # Operator > -> >= bei der Schwelle: Summe genau auf der Schwelle wird abgabepflichtig
        self.assertEqual(K.pruefe_eigenwerbung(2026, 1000).klasse, K.NICHT)
        alt = self._mit("schwelle.operator", operator=">=")
        try:
            self.assertEqual(K.pruefe_eigenwerbung(2026, 1000).klasse, K.ABGABEPFLICHTIG)
        finally:
            K.P["register"] = alt
        # Meldefrist
        alt = self._mit("meldefrist.tag", wert="30")
        try:
            self.assertEqual(K.meldefrist(2025).day, 30)
        finally:
            K.P["register"] = alt
        self.assertEqual(K.meldefrist(2025).day, 31)

    def test_fehlender_eintrag_ist_nicht_abgedeckt(self):
        alt = K.P["register"]
        K.P["register"] = [r for r in alt if r["schluessel"] != "saeumnis.stufe"]
        try:
            self.assertEqual(K.saeumniszuschlag(1000, 1, 2026).klasse, K.NICHT_ABGEDECKT)
        finally:
            K.P["register"] = alt

class Ausschluesse(unittest.TestCase):
    def test_gmbh_zahlung_wird_erklaert_und_zaehlt_nicht(self):
        pos = [{"betrag": D("5000"), "empfaenger": "gmbh"}, {"betrag": D("2400")}, {"betrag": D("300"), "art": "fahrtkosten_nachgewiesen"}]
        e = K.pruefe_positionen(2025, pos, typischer_verwerter=True)
        self.assertEqual(e.bemessungsgrundlage, D("2400"))
        text = " ".join(e.begruendung)
        self.assertIn("5.000,00 € (Zahlung an Kapital-/Handelsgesellschaft, R-138, R-216)", text)
        self.assertIn("300,00 € (nachgewiesene Fahrtkosten, R-47)", text)
        self.assertIn("R-216", e.regeln)

    def test_nur_gmbh_zeigt_warum_bemessungsgrundlage_null(self):
        e = K.pruefe_positionen(2025, [{"betrag": D("5000"), "empfaenger": "gmbh"}], typischer_verwerter=True)
        self.assertEqual(e.bemessungsgrundlage, D("0"))
        self.assertTrue(any("Nicht zur Bemessungsgrundlage: 5.000,00 €" in b for b in e.begruendung))

    def test_ohne_ausschluesse_keine_zusatzzeile(self):
        e = K.pruefe_positionen(2025, [{"betrag": D("2400")}], typischer_verwerter=True)
        self.assertFalse(any("Nicht zur Bemessungsgrundlage" in b for b in e.begruendung))


class GeneralklauselOhneVeranstaltungen(unittest.TestCase):
    """Pruefkatalog-Befund M7: anzahl == 0 (keine Veranstaltungen, z. B. Nutzung durch
    Lizenzierung) bekommt eine eigene Pruefung (R-13), nicht die Drei-Veranstaltungen-
    Ausnahme (R-14/R-132, die nur fuer Entgelte AUS Veranstaltungen gilt)."""

    def test_p07_summe_ueber_schwelle_abgabepflichtig_150(self):
        e = K.veranstaltungen(2025, 0, D("3000"), True, "generalklausel")
        self.assertEqual(e.klasse, K.ABGABEPFLICHTIG)
        self.assertEqual(e.bemessungsgrundlage, D("3000"))
        self.assertEqual(e.abgabe, D("150.00"))
        self.assertEqual(e.regeln, ["R-13"])
        self.assertIn("KSVG § 24 Abs. 2 S. 1 Nr. 2, S. 2", e.fundstellen)
        text = " ".join(e.begruendung)
        self.assertNotIn("Veranstaltungen und Summe", text)
        self.assertNotIn("Höchstens drei", text)

    def test_summe_unter_schwelle_nicht_abgabepflichtig(self):
        e = K.veranstaltungen(2025, 0, D("500"), True, "generalklausel")
        self.assertEqual(e.klasse, K.NICHT)

    def test_ohne_einnahmeabsicht_nicht_abgabepflichtig(self):
        e = K.veranstaltungen(2025, 0, D("3000"), False, "generalklausel")
        self.assertEqual(e.klasse, K.NICHT)
        self.assertIn("Keine Einnahmeabsicht", e.begruendung[0])

    def test_echte_veranstaltungen_bleiben_unveraendert(self):
        """Gegenprobe: das Verhalten fuer anzahl >= 1 (Q-Faelle/abnahme) darf sich durch
        die neue anzahl==0-Verzweigung nicht aendern."""
        e3 = K.veranstaltungen(2025, 3, D("5000"), True, "generalklausel")
        self.assertEqual(e3.klasse, K.NICHT)
        e4 = K.veranstaltungen(2025, 4, D("5000"), True, "generalklausel")
        self.assertEqual(e4.klasse, K.ABGABEPFLICHTIG)
        self.assertEqual(e4.abgabe, D("250.00"))
        self.assertEqual(e4.regeln, ["R-14", "R-132"])


class Dokumentpruefung(unittest.TestCase):
    def test_rechenprobe_widerspruch_sperrt_ohne_abgabe(self):
        e = K.rechenprobe_brutto(1000, 190, 1200, 2026)
        self.assertEqual(e.klasse, K.SPERRE)
        self.assertIn("Rechenprobe brutto", e.begruendung)
        self.assertIsNone(e.abgabe)
        self.assertIsNone(e.bemessungsgrundlage)
        self.assertIsNone(K.rechenprobe_brutto(1000, 190, 1190, 2026))

    def test_doppelte_positionsnummer_sperrt(self):
        e = K.positionsnummern_doppelt([7, 7], 2026)
        self.assertEqual(e.klasse, K.SPERRE)
        self.assertIn("doppelte Positionsnummer", e.begruendung[0])
        self.assertIsNone(e.abgabe)
        self.assertIsNone(K.positionsnummern_doppelt([1, 2], 2026))

    def test_struktur_sperrt_vor_der_entscheidung(self):
        summe = K.pruefe_dokument({"summen": {"positionssumme": "1200", "kopfsumme": "1350"}}, 2026)
        self.assertEqual(summe.klasse, K.SPERRE)
        self.assertIsNone(summe.abgabe)
        cent = K.pruefe_dokument({"differenz": "0.02"}, 2026)
        self.assertEqual(cent.klasse, K.SPERRE)
        self.assertIsNone(K.pruefe_dokument({"differenz": "0.01"}, 2026))
        netto_brutto = K.pruefe_dokument({
            "summen": {
                "positionssumme": "2470.00",
                "kopfsumme": "2939.30",
                "netto": "2470.00",
                "ust": "469.30",
                "brutto": "2939.30",
            }
        }, 2026)
        self.assertIsNone(netto_brutto)
        zeile = K.pruefe_dokument({"positionen": [{"nr": 2, "betragswiderspruch": True}]}, 2026)
        self.assertEqual(zeile.klasse, K.SPERRE)
        formen = K.pruefe_dokument({"rechtsformen": ["einzelunternehmen", "gmbh"]}, 2026)
        self.assertEqual(formen.klasse, K.SPERRE)
        self.assertIn("Gesellschaft", formen.begruendung[0])
        storno = K.pruefe_dokument({"storno": True, "summen": {"gesamtsumme": "-120"}}, 2026)
        self.assertEqual(storno.klasse, K.RUECKFRAGE)
        self.assertTrue(any("Storno" in teil or "Saldierung" in teil for teil in storno.begruendung))

    def test_ust_rechenprobe_mischsatz_sperrt_passende_zeile_nicht(self):
        falsch = K.pruefe_dokument({
            "positionen": [{"netto": "100.00", "ust": "20.00"}],
            "summen": {"netto": "100.00", "ust": "20.00"},
        }, 2026)
        self.assertEqual(falsch.klasse, K.SPERRE)
        self.assertIsNone(falsch.abgabe)
        self.assertTrue(any("Rechenprobe" in teil or "Misch" in teil for teil in falsch.begruendung))
        passt = K.ust_rechenprobe({
            "positionen": [{"netto": "100.00", "ust": "19.00", "satz": "19"}],
            "summen": {"netto": "100.00", "ust": "19.00"},
        }, 2026)
        self.assertIsNone(passt)
        text = K.pruefe_dokument({
            "ust_saetze": ["7", "19"],
            "summe_ohne_einheitlichen_satz": True,
        }, 2026)
        self.assertEqual(text.klasse, K.SPERRE)
        self.assertIsNone(text.abgabe)

    def test_oeffentliche_stelle_vor_kapitalgesellschaft(self):
        stelle = K.pruefe_dokument({"empfaenger": "oeffentlich", "jahr": 2026}, 2026)
        self.assertEqual(stelle.klasse, K.RUECKFRAGE)
        self.assertIn("Info 11", stelle.begruendung[0])
        self.assertIn("11/16", stelle.begruendung[0])
        auftrag = K.pruefe_dokument({"empfaenger": "natuerliche_person", "auftraggeber": "oeffentlich"}, 2026)
        self.assertEqual(auftrag.klasse, K.RUECKFRAGE)
        self.assertIsNone(K.pruefe_dokument({"empfaenger": "gmbh"}, 2026))
        sperre = K.pruefe_dokument({
            "empfaenger": "oeffentlich",
            "summen": {"positionssumme": "1200", "kopfsumme": "1350"},
        }, 2026)
        self.assertEqual(sperre.klasse, K.SPERRE)

    def test_negative_summe_ohne_storno_sperrt_mit_storno_offen(self):
        gesperrt = K.gesamtsumme_negativ(-350, False, 2026)
        self.assertEqual(gesperrt.klasse, K.SPERRE)
        self.assertIsNone(gesperrt.abgabe)
        offen = K.gesamtsumme_negativ(-350, True, 2026)
        self.assertEqual(offen.klasse, K.RUECKFRAGE)
        self.assertNotEqual(offen.klasse, K.SPERRE)

    def test_paragraph19_und_skonto(self):
        e = K.widerspruch_paragraph19(True, True, 2026)
        self.assertEqual(e.klasse, K.SPERRE)
        self.assertIn("§19", e.begruendung[0])
        self.assertIsNone(e.abgabe)
        self.assertIsNone(K.widerspruch_paragraph19(True, False, 2026))
        skonto = K.skonto_unklar(2026)
        self.assertEqual(skonto.klasse, K.RUECKFRAGE)
        self.assertNotEqual(skonto.klasse, K.SPERRE)

    def test_ein_cent_hinweis_zwei_cent_sperre(self):
        self.assertEqual(K.rundungshinweis("Rundungsdifferenz 1 Cent zwischen Positionssumme und Kopfsumme", 2026),
                         "Rundungsdifferenz 1 ct, rechnerisch unbedeutend")
        self.assertIsNone(K.pruefe_sperre("Rundungsdifferenz 1 Cent zwischen Positionssumme und Kopfsumme", 2026))
        zwei = K.pruefe_sperre("Rundungsdifferenz 2 Cent zwischen Positionssumme und Kopfsumme", 2026)
        self.assertEqual(zwei.klasse, K.SPERRE)
        self.assertIsNone(zwei.abgabe)


class RegisterAusbau(unittest.TestCase):
    def test_webdesign_ist_bekannt_uebersetzung_bleibt_offen(self):
        self.assertIsNone(K.einordnung_taetigkeit("Webdesign Vereinsseite", 2026))
        offen = K.einordnung_taetigkeit("Übersetzung Programmheft durch eine Übersetzerin", 2026)
        self.assertEqual(offen.klasse, K.RUECKFRAGE)
        self.assertEqual(K.einordnung_taetigkeit("Softwareentwicklung Voting-App", 2026).klasse, K.NICHT_ABGEDECKT)
        self.assertEqual(K.einordnung_taetigkeit("Evaluation des Konzerts durch eine Soziologin", 2026).klasse, K.NICHT_ABGEDECKT)
        self.assertFalse(K.ist_keine_kuenstlerische_taetigkeit("Softwareentwicklung Voting-App", 2026))

    def test_schuelerzahl_zwanzig_und_sechzig(self):
        self.assertEqual(K.musikverein_schueler(2026, 45).klasse, K.RUECKFRAGE)
        self.assertEqual(K.musikverein_schueler(2026, 10, True, True).klasse, K.NICHT)
        self.assertEqual(K.musikverein_schueler(2026, 40, True, True).klasse, K.NICHT)
        self.assertEqual(K.musikverein_schueler(2026, 80, True, True).klasse, K.GRENZFALL)

    def test_gemeinde_ist_kein_ausschluss_und_porto_zaehlt(self):
        self.assertNotIn("stadt", K.werte("rechtsform.kein_entgelt", 2026))
        self.assertIn("stadt", K.werte("auftraggeber.kommune", 2026))
        self.assertIsNone(K.pruefe_beleg("Porto für den Versand der Partitur", 12, 2026))
        self.assertIn("Befreiung", K.listentreffer("Der Verein ist gemeinnützig.", "gemeinnuetzig", 2026)["fundstelle"])

    def test_eigenwerbung_ist_szenario_und_waehrung_bleibt_offen(self):
        self.assertNotIn("eigenwerbung", K.werte("taetigkeit.synonym", 2026))
        self.assertIn("eigenwerbung", K.werte("szenarien.eigenwerbung", 2026))
        self.assertEqual(K.einordnung_taetigkeit("Eigenwerbung", 2026).klasse, K.NICHT_ABGEDECKT)
        self.assertEqual(K.pruefe_eigenwerbung(2026, 1500).klasse, K.ABGABEPFLICHTIG)
        waehrung = K.pruefe_klarstellung("Gage 2000 USD ohne Kurs", 2000, 2026)
        self.assertEqual(waehrung.klasse, K.RUECKFRAGE)
        self.assertIn("Umrechnungsnachweis", waehrung.begruendung[0])


class Wächter(unittest.TestCase):
    def test_keine_fachlichen_festwerte_im_kern(self):
        """Zahlen im Code nur technisch: 100 (Prozent), 0.01 (Cent), 12/31 (Kalenderjahresende). Alles andere gehört ins Regelregister."""
        import ast, pathlib
        quelle = pathlib.Path(K.__file__).read_text(encoding="utf-8")
        baum = ast.parse(quelle)
        doc = {id(n.body[0].value) for n in ast.walk(baum)
               if isinstance(n, (ast.FunctionDef, ast.Module, ast.ClassDef)) and n.body
               and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant)}
        erlaubt = {0, 1, 100, 12, 31, "0.01"}
        fund = []
        for n in ast.walk(baum):
            if isinstance(n, ast.Constant) and id(n) not in doc:
                v = n.value
                if isinstance(v, (int, float)) and not isinstance(v, bool) and v not in erlaubt:
                    fund.append((n.lineno, v))
                elif isinstance(v, str) and v.replace(".", "", 1).isdigit() and v not in erlaubt:
                    fund.append((n.lineno, v))
        self.assertEqual(fund, [], "Festwerte im Code gefunden – ins Regelregister verschieben")


if __name__ == "__main__":
    unittest.main(verbosity=2)
