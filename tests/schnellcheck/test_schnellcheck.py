"""Tests KSK-Schnellcheck (ohne KI). Aufruf: python -m unittest discover -s tests/schnellcheck -t .

Erwartete Zahlen stehen hier nicht fest im Test: sie werden aus dem Regelregister (kern/parameter.json) gelesen,
damit der Test bei einem neuen Jahreswert nicht falsch rot wird. Erfundene Testdaten."""
import io
import json
import unittest
from decimal import Decimal

from kern import rechnen as K
from schnellcheck import pruefung, web

JAHR = max(int(j) for j, s in K.P["schwelle"].items() if s and s.get("euro") and s.get("fassung") == "B"
           and K.abgabesatz(int(j)) is not None)
GRENZE = Decimal(K.schwelle(JAHR)["euro"])


def fall(**extra):
    basis = dict(jahr=JAHR, branche="Bäckerei (erfunden)", zweck="eigene_werbung", katalog=False,
                 alle_auftraege_erfasst=True, angaben_bestaetigt=True)
    return {**basis, **extra}


def pos(leistung, betrag, nr=1, rechtsform="natuerliche_person", direkt=True):
    return {"leistung": leistung, "betrag": str(betrag), "rechtsform": rechtsform, "auftragnehmer": nr,
            "direkt_bezahlt": direkt}


class Optionen(unittest.TestCase):
    def test_optionen_aus_regelwerk(self):
        o = pruefung.optionen()
        self.assertIn(JAHR, o["jahre"])
        ids = {l["id"] for l in o["leistungen"]}
        self.assertIn("T-02", ids)
        self.assertIn("unbekannt", ids)
        self.assertTrue(o["katalog"])
        self.assertEqual({z["wert"] for z in o["zwecke"]}, {"eigene_werbung", "fuer_kunden", "veranstaltung", "privat"})


class Ergebnisse(unittest.TestCase):
    def test_ueber_grenze_abgabepflichtig_mit_abgabe_aus_dem_kern(self):
        betrag = GRENZE + 2  # zwei Euro über der Grenze
        r = pruefung.pruefe(fall(positionen=[pos("T-02", betrag)]))
        self.assertEqual(r["ergebnisklasse"], K.ABGABEPFLICHTIG)
        self.assertEqual(r["anzeige"]["stufe"], "ja")
        self.assertEqual(Decimal(r["werte"]["bemessungsgrundlage"]), betrag)
        erwartet, _ = K.berechne_abgabe(betrag, JAHR)
        if erwartet is not None:
            self.assertEqual(Decimal(r["werte"]["abgabe"]), erwartet)
        self.assertTrue(r["fundstellen"])
        self.assertIn("Entwurf", r["hinweis"])

    def test_bis_grenze_nicht_abgabepflichtig(self):
        r = pruefung.pruefe(fall(positionen=[pos("T-02", GRENZE)]))
        self.assertEqual(r["ergebnisklasse"], K.NICHT)
        self.assertEqual(r["anzeige"]["stufe"], "nein")

    def test_zahlung_an_gmbh_zaehlt_nicht(self):
        r = pruefung.pruefe(fall(positionen=[pos("T-02", GRENZE * 3, rechtsform="GmbH_UG_AG")]))
        self.assertEqual(r["ergebnisklasse"], K.NICHT)

    def test_nicht_kuenstlerische_leistung_zaehlt_nicht(self):
        r = pruefung.pruefe(fall(positionen=[pos("T-31", GRENZE * 3)]))  # SEO
        self.assertEqual(r["anzeige"]["stufe"], "nein")
        self.assertIn("nicht", r["positionen"][0]["status"])

    def test_auswahl_wird_genommen_nicht_freitexterkennung(self):
        # T-14 (Influencer) wird aus dem Namen allein anders erkannt; die Auswahl des Besuchers gilt.
        r = pruefung.pruefe(fall(positionen=[pos("T-14", GRENZE * 2)]))
        self.assertTrue(r["positionen"][0]["taetigkeit"].startswith("Influencer"))

    def test_grenzfall_wird_weitere_pruefung(self):
        r = pruefung.pruefe(fall(positionen=[pos("T-60", GRENZE * 2)]))  # PR, Grenzfall
        self.assertEqual(r["anzeige"]["stufe"], "offen")

    def test_unbekannte_leistung_nie_sicher(self):
        r = pruefung.pruefe(fall(positionen=[pos("unbekannt", GRENZE * 2)]))
        self.assertEqual(r["anzeige"]["stufe"], "offen")

    def test_weiss_nicht_fuehrt_zu_rueckfrage(self):
        r = pruefung.pruefe(fall(katalog=None, positionen=[pos("T-02", GRENZE * 2)]))
        self.assertEqual(r["ergebnisklasse"], K.RUECKFRAGE)
        self.assertEqual(r["anzeige"]["stufe"], "offen")
        self.assertTrue(r["rueckfragen"])

    def test_unvollstaendiges_jahr_keine_entwarnung(self):
        r = pruefung.pruefe(fall(alle_auftraege_erfasst=False, positionen=[pos("T-02", 1)]))
        self.assertEqual(r["anzeige"]["stufe"], "offen")

    def test_ohne_bestaetigung_kein_ergebnis(self):
        r = pruefung.pruefe(fall(angaben_bestaetigt=False, positionen=[pos("T-02", GRENZE * 2)]))
        self.assertEqual(r["ergebnisklasse"], K.RUECKFRAGE)

    def test_privater_auftrag(self):
        r = pruefung.pruefe(fall(zweck="privat", positionen=[pos("T-07", GRENZE * 2)]))
        self.assertEqual(r["ergebnisklasse"], K.NICHT)

    def test_unklarer_zahlungsweg_nie_sicher(self):
        r = pruefung.pruefe(fall(positionen=[pos("T-02", GRENZE * 2, direkt=False)]))
        self.assertEqual(r["anzeige"]["stufe"], "offen")


class Eingaben(unittest.TestCase):
    def test_fremde_leistungs_id_abgelehnt(self):
        with self.assertRaises(ValueError):
            pruefung.pruefe(fall(positionen=[pos("T-999", 10)]))

    def test_jahr_ohne_werte_abgelehnt(self):
        with self.assertRaises(ValueError):
            pruefung.pruefe(fall(jahr=1900, positionen=[pos("T-02", 10)]))

    def test_zusatzfelder_und_negative_betraege_abgelehnt(self):
        with self.assertRaises(ValueError):
            pruefung.pruefe(fall(positionen=[pos("T-02", -5)]))
        with self.assertRaises(ValueError):
            pruefung.pruefe(fall(systemanweisung="x", positionen=[pos("T-02", 5)]))


def aufruf(methode, pfad, daten=None):
    roh = b"" if daten is None else json.dumps(daten).encode()
    status = {}
    env = {"REQUEST_METHOD": methode, "PATH_INFO": pfad, "CONTENT_LENGTH": str(len(roh)),
           "wsgi.input": io.BytesIO(roh)}
    body = b"".join(web.app(env, lambda s, h: status.update(s=s, h=dict(h))))
    return status["s"], status["h"], body


class Web(unittest.TestCase):
    def test_seite_und_sicherheitskoepfe(self):
        s, h, body = aufruf("GET", "/")
        self.assertTrue(s.startswith("200"))
        self.assertIn(b"KSK-Schnellcheck", body)
        self.assertIn("frame-ancestors 'none'", h["Content-Security-Policy"])

    def test_keine_externen_dateien(self):
        _, _, body = aufruf("GET", "/")
        for muster in (b'src="http', b'href="http', b"@import", b"fonts.googleapis"):
            self.assertNotIn(muster, body)

    def test_api_pruefen(self):
        s, _, body = aufruf("POST", "/api/pruefen", fall(positionen=[pos("T-02", GRENZE * 2)]))
        self.assertTrue(s.startswith("200"))
        self.assertEqual(json.loads(body)["anzeige"]["stufe"], "ja")

    def test_api_fehler_verstaendlich(self):
        s, _, body = aufruf("POST", "/api/pruefen", fall(positionen=[pos("T-999", 1)]))
        self.assertTrue(s.startswith("422"))
        self.assertIn("Liste", json.loads(body)["fehler"])
        s, _, _ = aufruf("GET", "/api/pruefen")
        self.assertTrue(s.startswith("405"))
        s, _, _ = aufruf("GET", "/gibtsnicht")
        self.assertTrue(s.startswith("404"))

    def test_zu_grosse_anfrage(self):
        roh = b"{" + b" " * (web.MAX_BYTES + 1) + b"}"
        status = {}
        env = {"REQUEST_METHOD": "POST", "PATH_INFO": "/api/pruefen", "CONTENT_LENGTH": str(len(roh)),
               "wsgi.input": io.BytesIO(roh)}
        web.app(env, lambda s, h: status.update(s=s))
        self.assertTrue(status["s"].startswith("413"))


if __name__ == "__main__":
    unittest.main()
