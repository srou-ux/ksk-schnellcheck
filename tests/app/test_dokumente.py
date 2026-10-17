"""Erfundene Dokumente: echter Upload/Leser, Bestätigung, Regelkern, eigener Gegenrechnungsprozess.
Kein Sprachmodell und keine Kundendaten. Fachliches Soll ist Entwurf des vorhandenen Regelwerks.
"""
import copy
from decimal import Decimal
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
import openpyxl
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

from app import dokument_app, gegenrechnung
from app.dokument_lesen import geld, textpositionen
from app.dokument_pruefung import DokumentFall, auswerten


def fall(betrag="1500.00", **updates):
    d = {"jahr": 2026, "unternehmensart": "Bäckerei", "auftragszweck": "eigene_werbung",
         "katalog_taetigkeit": False, "jahresdaten_vollstaendig": True, "netto_und_bezahlt": True,
         "positionen_geprueft": True, "positionen": [{"bezeichnung": "Logo", "betrag": betrag,
         "auftragnehmer_typ": "natuerliche_person", "auftragnehmer_nr": 1, "zahlungsweg": "direkt"}]}
    d.update(updates)
    return d


def pdf(zeilen, bild=False):
    w = PdfWriter(); p = w.add_blank_page(width=600, height=800)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"),
                             NameObject("/BaseFont"): NameObject("/Helvetica")})
    p[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})})
    stream = DecodedStreamObject()
    lines = ["BT /F1 14 Tf 40 750 Td 22 TL"]
    for line in zeilen:
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        lines.append(f"({safe}) Tj T*")
    lines.append("ET"); stream.set_data("\n".join(lines).encode("latin-1"))
    p[NameObject("/Contents")] = w._add_object(stream)
    out = io.BytesIO(); w.write(out); return out.getvalue()


def xlsx(zeilen):
    w = openpyxl.Workbook(); s = w.active
    s.append(["Bezeichnung", "Betrag"])
    for z in zeilen: s.append(z)
    out = io.BytesIO(); w.save(out); w.close(); return out.getvalue()


class Dokumente(unittest.TestCase):
    def setUp(self):
        self.c = TestClient(dokument_app.app)

    def ergebnis(self, f):
        start = self.c.post("/dokumente/vorbereiten", json=f)
        self.assertEqual(start.status_code, 200, start.text)
        self.assertTrue(start.json()["bereit"], start.text)
        end = self.c.post("/dokumente/auswerten", json={"fall": f, "ticket": start.json()["ticket"]})
        self.assertEqual(end.status_code, 200, end.text)
        return end.json()

    def test_baeckerei_eigenwerbung_mit_quellen_und_gegenrechnung(self):
        d = self.ergebnis(fall())
        self.assertEqual(d["werte"]["abgabe"], "73.50")
        self.assertIn("Schwelle", d["begruendung"])
        self.assertTrue(d["fundstellen"])
        self.assertEqual(d["pruefprotokoll"]["status"], "bestaetigt")

    def test_kein_ergebnis_ohne_bestaetigung_oder_nach_aenderung(self):
        f = fall(); token = self.c.post("/dokumente/vorbereiten", json=f).json()["ticket"]
        f["positionen"][0]["betrag"] = "2500"
        for t in [None, "falsch", token]:
            self.assertEqual(self.c.post("/dokumente/auswerten", json={"fall": f, "ticket": t}).status_code, 409)

    def test_abgelaufene_bestaetigung(self):
        f = fall(); token = dokument_app._ticket(DokumentFall(**f), zeit=0)
        self.assertEqual(self.c.post("/dokumente/auswerten", json={"fall": f, "ticket": token}).status_code, 409)

    def test_fehlende_angaben_und_widersprueche_bleiben_offen(self):
        for changes in [{"jahr": None}, {"auftragszweck": None}, {"katalog_taetigkeit": None},
                        {"jahresdaten_vollstaendig": False}, {"netto_und_bezahlt": False},
                        {"positionen_geprueft": False}, {"auftragszweck": "fuer_kunden"},
                        {"auftragszweck": "privat", "katalog_taetigkeit": True}]:
            with self.subTest(changes=changes):
                d = self.c.post("/dokumente/vorbereiten", json=fall(**changes)).json()
                self.assertFalse(d["bereit"]); self.assertTrue(d["rueckfragen"]); self.assertNotIn("ticket", d)

    def test_bestaetigung_zeigt_jede_position_und_bedingungen(self):
        d = self.c.post("/dokumente/vorbereiten", json=fall()).json()
        self.assertTrue(any("Position 1" in s and "1500" in s for s in d["zusammenfassung"]))
        self.assertTrue(any("Voraussetzung" in s for s in d["zusammenfassung"]))

    def test_keine_vertrauten_systemfelder_vom_client(self):
        for key,value in [("verwerterart", "privat"), ("abgabe", 0), ("herkunft", {})]:
            self.assertEqual(self.c.post("/dokumente/vorbereiten", json=fall(**{key: value})).status_code, 422)
        f = fall(); f["positionen"][0]["kuenstlerisch"] = False
        self.assertEqual(self.c.post("/dokumente/vorbereiten", json=f).status_code, 422)

    def test_ungueltige_betraege(self):
        for b in ["NaN", "Infinity", "-1", "0.001", "1e1000"]:
            self.assertEqual(self.c.post("/dokumente/vorbereiten", json=fall(b)).status_code, 422)

    def test_grenzen_unbekannt_privater_auftrag_agentur_gmbh(self):
        self.assertTrue(self.ergebnis(fall("1000"))["ergebnisklasse"].startswith("Nicht"))
        self.assertEqual(self.ergebnis(fall("1000.01"))["werte"].get("abgabe"), None)  # Rundung offen
        self.assertTrue(self.ergebnis(fall(jahr=2031))["ergebnisklasse"].startswith("Nicht abgedeckt"))
        self.assertTrue(self.ergebnis(fall(auftragszweck="privat", jahresdaten_vollstaendig=False))["ergebnisklasse"].startswith("Nicht abgabepflichtig"))
        self.assertEqual(self.ergebnis(fall("100", unternehmensart="Werbeagentur", katalog_taetigkeit=True,
                                          auftragszweck="fuer_kunden"))["werte"]["abgabe"], "4.90")
        f = fall(); f["positionen"][0]["auftragnehmer_typ"] = "GmbH_UG_AG"
        self.assertTrue(self.ergebnis(f)["ergebnisklasse"].startswith("Nicht abgabepflichtig"))

    def test_gemischte_positionen_selber_und_anderer_auftragnehmer(self):
        f = fall(); p = copy.deepcopy(f["positionen"][0]); p.update(bezeichnung="Programmierung", betrag="500", auftragnehmer_nr=2)
        f["positionen"].append(p)
        d = self.ergebnis(f); self.assertEqual(d["werte"]["abgabe"], "73.50")
        self.assertIn("nicht", d["positionen"][1]["status"])
        p["auftragnehmer_nr"] = 1
        d = self.ergebnis(f); self.assertEqual(d["werte"]["abgabe"], "98.00"); self.assertTrue(d["positionen"][1]["nebenleistung"])

    def test_unbekannte_leistung_und_zahlungsweg(self):
        f = fall(); f["positionen"][0]["bezeichnung"] = "Zzz unbekannte Leistung"
        self.assertTrue(self.ergebnis(f)["ergebnisklasse"].startswith("Grenzfall"))
        f = fall(); f["positionen"][0]["zahlungsweg"] = "unklar"
        self.assertTrue(self.ergebnis(f)["ergebnisklasse"].startswith("Grenzfall"))

    def test_gegenrechnungsfehler_gibt_keine_zahlen_aus(self):
        with patch("app.dokument_pruefung.router._kern_mit_gegenrechnung", return_value=(None, gegenrechnung.Pruefung("abweichung", "Testabweichung"))):
            d = auswerten(DokumentFall(**fall()))
        self.assertEqual(d["werte"], {}); self.assertEqual(d["positionen"], [])

    def test_echter_pdf_xlsx_csv_upload_und_keine_summenzeile(self):
        for ext, data in [(".pdf", pdf(["Fiktive Rechnung", "Logo 1500,00 EUR", "Summe 1500,00 EUR"])),
                          (".xlsx", xlsx([["Logo", 1500], ["Summe", 1500]])),
                          (".csv", b"Bezeichnung;Betrag\nLogo;1500,00\nSumme;1500,00")]:
            with self.subTest(ext=ext):
                r = self.c.post("/dokumente/lesen?endung="+ext, content=data)
                self.assertEqual(r.status_code, 200, r.text)
                self.assertEqual(len(r.json()["positionen"]), 1)
                f = fall(); f["positionen"][0].update(r.json()["positionen"][0])
                self.assertEqual(self.ergebnis(f)["werte"]["abgabe"], "73.50")

    def test_formeln_fremdwaehrung_und_mehrdeutige_preise(self):
        r = self.c.post("/dokumente/lesen?endung=.xlsx", content=xlsx([["Logo", "=SUM(1,2)"]]))
        self.assertEqual(r.status_code, 200, r.text); self.assertEqual(r.json()["positionen"], [])
        self.assertTrue(any("Formel" in h for h in r.json()["hinweise"]))
        self.assertEqual(textpositionen("Logo USD 1500.00\nLogo 2 750,00 1500,00", "Probe"), [])
        self.assertIsNone(geld("1.500")); self.assertIsNone(geld("-100,00"))

    def test_leere_kaputte_grosse_und_falsche_dateien(self):
        for ext,data,code in [(".pdf", b"kaputt", 422), (".exe", b"x", 415), (".pdf", b"", 400)]:
            self.assertEqual(self.c.post("/dokumente/lesen?endung="+ext, content=data).status_code, code)
        with patch.dict(dokument_app.KONFIG, max_bytes=4):
            self.assertEqual(self.c.post("/dokumente/lesen?endung=.csv", content=b"12345").status_code, 413)

    def test_kein_llm_keine_chat_route_kein_cache(self):
        with patch("app.llm.anbieter.waehle_llm", side_effect=AssertionError("LLM darf nicht aufgerufen werden")):
            self.assertEqual(self.ergebnis(fall())["werte"]["abgabe"], "73.50")
        self.assertEqual(self.c.post("/frage", json={"frage":"Hallo"}).status_code, 404)
        self.assertFalse(self.c.get("/gesundheit").json()["llm"])
        self.assertEqual(self.c.get("/").headers["cache-control"], "no-store")

    def test_180_erfundene_dokumentfaelle_durch_den_ganzen_ablauf(self):
        # 60 Beträge, jeweils als echte PDF, XLSX und CSV; Soll unabhängig vorgegeben.
        # Alle Entgelte oberhalb der Jahresgrenze, Abgaben ohne Rundungsstreit.
        for n in range(60):
            betrag = 1500 + n * 100
            soll = str(Decimal('73.50') + n * Decimal('4.90'))
            docs = [(".pdf", pdf([f"Logo {betrag},00 EUR"])), (".xlsx", xlsx([["Logo", betrag]])),
                    (".csv", f"Bezeichnung;Betrag\nLogo;{betrag},00".encode())]
            for ext,data in docs:
                with self.subTest(n=n,ext=ext):
                    r = self.c.post("/dokumente/lesen?endung="+ext, content=data)
                    self.assertEqual(r.status_code, 200, r.text)
                    self.assertEqual(len(r.json()["positionen"]), 1)
                    f = fall(); f["positionen"][0].update(r.json()["positionen"][0])
                    self.assertEqual(self.ergebnis(f)["werte"]["abgabe"], soll)

    @unittest.skipUnless(shutil.which("tesseract"), "Lokales OCR benötigt Tesseract")
    def test_echtes_foto_ocr(self):
        bild = Image.new("RGB", (1400, 300), "white")
        ImageDraw.Draw(bild).text((40, 60), "Logo 1500,00 EUR", fill="black", font=ImageFont.load_default(size=48))
        out=io.BytesIO();bild.save(out,format="PNG")
        r=self.c.post("/dokumente/lesen?endung=.png",content=out.getvalue())
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()["methode"],"OCR")
        self.assertTrue(r.json()["positionen"],r.text)
        self.assertEqual(r.json()["positionen"][0]["betrag"],"1500.00")

    @unittest.skipUnless(shutil.which("tesseract") and shutil.which("pdftoppm"), "Scan-PDF benötigt Tesseract und Poppler")
    def test_echte_scan_pdf_ocr(self):
        bild = Image.new("RGB", (1400, 300), "white")
        ImageDraw.Draw(bild).text((40, 60), "Logo 1500,00 EUR", fill="black", font=ImageFont.load_default(size=48))
        out=io.BytesIO();bild.save(out,format="PDF",resolution=150)
        r=self.c.post("/dokumente/lesen?endung=.pdf",content=out.getvalue())
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()["methode"],"Text und OCR")
        self.assertTrue(r.json()["positionen"],r.text)
        self.assertEqual(r.json()["positionen"][0]["betrag"],"1500.00")


if __name__ == "__main__":
    unittest.main(verbosity=2)
