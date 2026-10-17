"""Eigenschaftsbasierter Test (property-based, nur Standardbibliothek, fester Seed):
generiert viele zufaellige, aber plausible Anfragen ueber alle Anfragearten und Jahre
2019-2027 und prueft die zentrale Eigenschaft der Architektur Teil 1c/1d:

    Jede Zahl, jedes Jahr, jede Fassung und jede Fundstelle in der ausgegebenen Antwort ist
    vertrauenswuerdig (kommt aus dem Kernergebnis/den Fakten/der Quellenbasis) -- sonst haette
    app/router.py::_ausgeben() 'Pruefung fehlgeschlagen' zurueckgegeben.

Da FakeLLM (ohne Boes-Manipulation) niemals absichtlich etwas erfindet, MUSS die ehrliche
Pipeline bei jedem der generierten Faelle durchkommen. Ein Fehlschlag hier zeigt denselben
Fehlertyp wie die beiden in dieser Phase gefundenen und behobenen Luecken (Schwelle/Summe,
siehe app/router.py bzw. app/pruefung.py): ein Platzhalter-/Protokollwert, der fuer einen
bestimmten Fall nicht zum Kernergebnis passt.

Fester Seed => reproduzierbar. Ziel: >= 2000 Faelle, < 60 Sekunden."""
import random
import sys
import time
import unittest
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from tests.app.hilfen import gegenrechnung_im_prozess, lauf_bestaetigt

from app.ergebnisklassen import PRUEFUNG_FEHLGESCHLAGEN
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position

SEED = 20251009
ANZAHL_FAELLE = 2000
JAHRE = range(2019, 2028)

ANFRAGEARTEN = [
    "bewertung", "veranstaltung", "vorauszahlung", "saeumniszuschlag", "verpflegung",
    "uebungsleiter_pauschale", "kommission", "schaetzung_ausland", "rechnungsanalyse",
]

_LEISTUNGSARTEN = ["Grafik/Design", "Text/Redaktion", "Musik", "Fotografie"]
_ROLLEN = [None, "honorar", "fahrtkosten_nachgewiesen"]
_RECHNUNGSROLLEN = [
    "an_kapitalgesellschaft", "vertretung_kuenstler", "eigengeschaeft_dritter",
    "nicht_kuenstlerisch", "reise_kuenstler",
]


def _betrag(rng: random.Random, min_eur: int = 0, max_eur: int = 50000) -> Decimal:
    cent = rng.randint(min_eur * 100, max_eur * 100)
    return (Decimal(cent) / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _erzeuge_fakten(rng: random.Random, art: str, jahr: int) -> tuple[str, Fakten]:
    """Liefert (frage, fakten) fuer eine zufaellige, aber in sich plausible Anfrage der
    gegebenen Anfrageart. 'bewertung'/'veranstaltung' bilden den Standardpfad ab (kein
    `anfrageart`-Feld in Fakten noetig -- siehe app/router.py::_rufe_kern_auf)."""
    frage = f"Zufallsfall ({art}, {jahr})."

    if art == "bewertung":
        positionen = [Position(betrag=_betrag(rng, 1, 20000), rolle=rng.choice(_ROLLEN))]
        fakten = Fakten(
            jahr=jahr, auftragnehmer_typ="natuerliche_person",
            leistungsart=rng.choice(_LEISTUNGSARTEN),
            verwerterart=rng.choice([None, "eigenwerber", "typischer_verwerter"]),
            positionen=positionen,
        )
        return frage, fakten

    if art == "veranstaltung":
        fakten = Fakten(
            jahr=jahr, auftragnehmer_typ="natuerliche_person", leistungsart=rng.choice(_LEISTUNGSARTEN),
            verwerterart=rng.choice([None, "eigenwerber", "typischer_verwerter", "generalklausel"]),
            positionen=[Position(betrag=_betrag(rng, 1, 10000))],
            veranstaltungszahl=rng.randint(0, 10), einnahmeabsicht=rng.choice([True, False]),
        )
        return frage, fakten

    if art == "vorauszahlung":
        fakten = Fakten(anfrageart="vorauszahlung", jahr=jahr, bemessungsgrundlage_vorjahr=_betrag(rng, 0, 100000))
        return frage, fakten

    if art == "saeumniszuschlag":
        fakten = Fakten(
            anfrageart="saeumniszuschlag", jahr=jahr, rueckstand=_betrag(rng, 1, 20000),
            saeumnis_monate=rng.randint(1, 24), saeumnis_gesondert_angefordert=rng.choice([True, False]),
        )
        return frage, fakten

    if art == "verpflegung":
        fakten = Fakten(
            anfrageart="verpflegung", jahr=jahr, reise_stunden=Decimal(rng.randint(0, 24)),
            reise_uebernachtung=rng.choice([True, False]), reise_erstattung=_betrag(rng, 0, 100),
            reise_inland=rng.choice([True, False]),
        )
        return frage, fakten

    if art == "uebungsleiter_pauschale":
        fakten = Fakten(
            anfrageart="uebungsleiter_pauschale", jahr=jahr, pauschale_art="uebungsleiter",
            pauschale_bestaetigung=rng.choice([True, False]),
            pauschale_bereits_ausgeschoepft=_betrag(rng, 0, 1000),
            positionen=[Position(betrag=_betrag(rng, 1, 5000))],
        )
        return frage, fakten

    if art == "kommission":
        preis = _betrag(rng, 1, 20000)
        einbehalt = _betrag(rng, 0, int(preis))
        fakten = Fakten(anfrageart="kommission", jahr=jahr, kommission_verkaufspreis=preis, kommission_einbehalt=einbehalt)
        return frage, fakten

    if art == "schaetzung_ausland":
        fakten = Fakten(anfrageart="schaetzung_ausland", jahr=jahr, schaetzung_bruttoeinnahmen=_betrag(rng, 1, 100000))
        return frage, fakten

    if art == "rechnungsanalyse":
        positionen = [
            Position(betrag=_betrag(rng, 1, 5000), rechnungsrolle=rng.choice(_RECHNUNGSROLLEN), nr=i, nachgewiesen=rng.choice([True, False]))
            for i in range(1, rng.randint(1, 6))
        ]
        fakten = Fakten(
            anfrageart="rechnungsanalyse", jahr=jahr, positionen=positionen,
            empfaenger_abgabepflichtig=rng.choice([True, False]), agentur_abgabepflichtig=rng.choice([True, False]),
        )
        return frage, fakten

    raise AssertionError(f"Unbekannte Testanfrageart: {art}")


class TestEigenschaftJedeZahlIstVertrauenswuerdig(unittest.TestCase):
    def test_ehrliche_pipeline_wird_nie_von_der_eigenen_kontrolle_abgelehnt(self):
        rng = random.Random(SEED)
        start = time.monotonic()
        fehlschlaege: list[str] = []

        # Teil 1e (15.10.2026): jede Antwort wird jetzt unabhängig gegengerechnet. Hier läuft die Gegenrechnung im
        # selben Prozess (gleiche Logik, verifier/), damit die 60-Sekunden-Grenze für 2000 Fälle gilt wie bisher; ein
        # eigener Prozess je Fall kostet etwa 50 ms (zusammen über 100 s). Den eigenen Prozess prüfen
        # tests/verifier/test_sandbox.py und die übrigen Tests in tests/app. Eine Abweichung Kern <-> Gegenrechnung
        # ergäbe auch hier 'Prüfung fehlgeschlagen' und damit einen Testfehler.
        with gegenrechnung_im_prozess():
            for i in range(ANZAHL_FAELLE):
                art = ANFRAGEARTEN[i % len(ANFRAGEARTEN)]
                jahr = rng.choice(list(JAHRE))
                frage, fakten = _erzeuge_fakten(rng, art, jahr)
                ergebnis = lauf_bestaetigt(FakeLLM(), frage, fakten)
                if ergebnis.ergebnisklasse == PRUEFUNG_FEHLGESCHLAGEN:
                    fehlschlaege.append(f"Fall {i} ({art}, {jahr}): {fakten!r} -> {ergebnis.antwort[:200]}")

        dauer = time.monotonic() - start
        self.assertLess(dauer, 60, f"Property-Test hat {dauer:.1f}s gebraucht (Grenze 60s)")
        self.assertEqual(
            fehlschlaege, [],
            f"{len(fehlschlaege)} von {ANZAHL_FAELLE} ehrlichen Faellen wurden von der eigenen "
            f"Kontrolle abgelehnt (Platzhalter-/Protokollwert passt nicht zum Kernergebnis):\n"
            + "\n".join(fehlschlaege[:5]),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
