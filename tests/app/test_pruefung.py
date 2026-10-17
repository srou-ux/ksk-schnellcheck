"""Tests fuer app/pruefung.py (Antwort-Kontrolle) -- inkl. Gegenproben mit absichtlich
eingebauten Fehlern, die gefangen werden muessen (Architektur Punkt 6).

Die Mutationsprobe (TestMutationsprobe) baut `text`/`kontext` direkt von Hand, OHNE den
Umweg ueber ein Sprachmodell oder app/baustein.py -- das macht sie unabhaengig von der seit
Teil 1d eingefuehrten Platzhalter-Architektur (frueher in tests/app/test_gegenproben.py)."""
import sys
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app import pruefung
from app.llm.base import AntwortKontext
from app.pruefung import pruefe_antwort
from app.schema import Fakten


def _kontext(**kwargs) -> AntwortKontext:
    basis = dict(
        frage="Testfrage",
        fakten=Fakten(jahr=2025),
        ergebnisklasse="Abgabepflichtig",
        kern_protokoll={"bemessungsgrundlage": Decimal("900"), "abgabe": Decimal("45.00")},
        regeln=[],
        fundstellen=[],
    )
    basis.update(kwargs)
    return AntwortKontext(**basis)


class TestGueltigeAntwort(unittest.TestCase):
    def test_korrekte_antwort_besteht_pruefung(self):
        text = (
            "Ergebnis: Abgabepflichtig. Bemessungsgrundlage 900,00 €, Abgabe 45,00 €.\n"
            "Entwurf – vom Steuerberater zu prüfen."
        )
        ergebnis = pruefe_antwort(text, _kontext())
        self.assertTrue(ergebnis.ok, ergebnis.gruende)


class TestRegressionBetragsErkennungOhneTausenderpunkt(unittest.TestCase):
    """Regression: kern.rechnen formatiert Betraege in Begruendungstexten nicht immer mit
    Tausenderpunkt (z. B. 'Summe 1750 € uebersteigt...'). Die alte Betrags-Regex haette hier
    faelschlich nur '750 €' erkannt und die Pruefung haette einen echten, aus dem
    Kernergebnis stammenden Betrag als 'erfunden' abgelehnt."""

    def test_vierstellige_zahl_ohne_tausenderpunkt_wird_vollstaendig_erkannt(self):
        text = (
            "Ergebnis: Abgabepflichtig. Summe 1750 € übersteigt die Schwelle 450 € nicht.\n"
            "Entwurf – vom Steuerberater zu prüfen."
        )
        # 1750 kommt aus dem Kernergebnis; 450 steht im selben (hier simulierten)
        # Begruendungssatz des Kerns und ist daher ebenfalls erlaubt -- siehe
        # app/pruefung.py, _erlaubte_betraege: Zahlen aus kern_protokoll/regeln/
        # fundstellen/hinweisen sind vertrauenswuerdig, nur der rohe Nutzertext
        # (`kontext.frage`) nicht.
        kontext = _kontext(
            kern_protokoll={
                "bemessungsgrundlage": Decimal("1750"),
                "abgabe": Decimal("87.50"),
                "subsumtion": "Summe 1750 € übersteigt die Schwelle 450 € nicht.",
            }
        )
        ergebnis = pruefe_antwort(text, kontext)
        self.assertTrue(ergebnis.ok, ergebnis.gruende)


class TestGegenprobeErfundenerBetrag(unittest.TestCase):
    def test_erfundener_betrag_wird_abgelehnt(self):
        text = (
            "Ergebnis: Abgabepflichtig. Abgabe 999.999,00 €.\n"
            "Entwurf – vom Steuerberater zu prüfen."
        )
        ergebnis = pruefe_antwort(text, _kontext())
        self.assertFalse(ergebnis.ok)
        self.assertTrue(any("999.999" in g for g in ergebnis.gruende))


class TestGegenprobeErfundenesAktenzeichen(unittest.TestCase):
    def test_nicht_existierendes_aktenzeichen_wird_abgelehnt(self):
        text = (
            "Ergebnis: Abgabepflichtig. Siehe BSG, B 9 ZZ 99/99 R.\n"
            "Entwurf – vom Steuerberater zu prüfen."
        )
        ergebnis = pruefe_antwort(text, _kontext())
        self.assertFalse(ergebnis.ok)
        self.assertTrue(any("B 9 ZZ 99/99 R" in g for g in ergebnis.gruende))


class TestGegenprobeFehlenderSchlusssatz(unittest.TestCase):
    def test_fehlender_schlusssatz_wird_abgelehnt(self):
        text = "Ergebnis: Abgabepflichtig. Abgabe 45,00 €."
        ergebnis = pruefe_antwort(text, _kontext())
        self.assertFalse(ergebnis.ok)
        self.assertTrue(any("Schlusssatz" in g for g in ergebnis.gruende))


class TestGegenprobeVerwaltungspraxisNichtGekennzeichnet(unittest.TestCase):
    def test_verwaltungspraxis_ohne_kennzeichnung_wird_abgelehnt(self):
        kontext = _kontext(regeln=[{"typ": "verwaltungspraxis", "fundstelle": "KSK-Info 05"}])
        text = "Ergebnis: Abgabepflichtig. Quelle: KSK-Info 05.\nEntwurf – vom Steuerberater zu prüfen."
        ergebnis = pruefe_antwort(text, kontext)
        self.assertFalse(ergebnis.ok)
        self.assertTrue(any("Verwaltungspraxis" in g for g in ergebnis.gruende))

    def test_verwaltungspraxis_mit_kennzeichnung_besteht(self):
        kontext = _kontext(regeln=[{"typ": "verwaltungspraxis", "fundstelle": "KSK-Info 05"}])
        text = (
            "Ergebnis: Abgabepflichtig. Verwaltungspraxis KSK (Auslegung der KSK, kein Gesetz): KSK-Info 05.\n"
            "Entwurf – vom Steuerberater zu prüfen."
        )
        ergebnis = pruefe_antwort(text, kontext)
        self.assertTrue(ergebnis.ok, ergebnis.gruende)


class TestMutationsprobe(unittest.TestCase):
    """Jede Pruefregel in app.pruefung.PRUEFSCHRITTE wird einzeln abgeschaltet (per
    `unittest.mock.patch.dict`); dabei muss der dafuer gebaute Fall von 'fehlgeschlagen' zu
    'bestanden' wechseln -- sonst waere die Regel wirkungslos. `text`/`kontext` werden hier
    direkt gebaut (kein FakeLLM/Baustein-Umweg), damit die Probe unabhaengig von der
    Platzhalter-Architektur bleibt."""

    BASIS_TEXT = "Ergebnis: Abgabepflichtig. Bemessungsgrundlage 900,00 €, Abgabe 45,00 €.\nEntwurf – vom Steuerberater zu prüfen."

    FAELLE: dict[str, tuple[dict, str | None]] = {
        "betraege": ({}, "Die Abgabe beträgt 999 €."),
        "prozente": ({}, "Der Satz beträgt 7,5 %."),
        "paragraphen": ({}, "Nach § 99 KSVG ist das so."),
        "jahre": ({}, "Im Jahr 2031 sinkt die Schwelle."),
        # Fassung braucht eine im Kernergebnis verankerte Schwelle (450), sonst wuerde
        # schon die Betraege-Regel mitfangen und die Probe waere nicht isoliert.
        "fassung": (
            {"kern_protokoll": {"bemessungsgrundlage": Decimal("900"), "abgabe": Decimal("45.00"), "schwelle": Decimal("450")}},
            "Nach Fassung A gilt die Grenze 450 € und Regelmäßigkeit.",
        ),
        "fundstellen": ({}, "Nach R-9999 ist das so."),
        "schlusssatz": ({}, None),
    }

    def _text_und_kontext(self, zusatz_kwargs: dict, zusatz: str | None):
        kontext = _kontext(**zusatz_kwargs)
        text = self.BASIS_TEXT
        if zusatz is None:  # Fall "schlusssatz": Schlusssatz entfernen statt Betrag faelschen
            text = text.replace("Entwurf –", "Kein Schlusssatz hier –")
        else:
            text = text.replace("Entwurf –", zusatz + "\n\nEntwurf –", 1)
        return text, kontext

    def test_jede_regel_ist_wirksam(self) -> None:
        for name, (zusatz_kwargs, zusatz) in self.FAELLE.items():
            with self.subTest(regel=name):
                text, kontext = self._text_und_kontext(zusatz_kwargs, zusatz)
                vorher = pruefung.pruefe_antwort(text, kontext)
                self.assertFalse(vorher.ok, f"Regel '{name}': Fall haette schon ohne Mutation fehlschlagen muessen")

                leer = lambda t, k: []  # noqa: E731
                with patch.dict(pruefung.PRUEFSCHRITTE, {name: leer}):
                    nachher = pruefung.pruefe_antwort(text, kontext)
                self.assertTrue(
                    nachher.ok, f"Regel '{name}' abgeschaltet, aber Fall besteht trotzdem nicht -- Regel war nicht die fangende"
                )

    def test_regel_ebenen_ist_wirksam(self) -> None:
        kontext = _kontext(regeln=[{"typ": "verwaltungspraxis", "fundstelle": "KSK-Info 05"}])
        text = "Ergebnis: Abgabepflichtig. Quelle: KSK-Info 05.\nEntwurf – vom Steuerberater zu prüfen."
        vorher = pruefung.pruefe_antwort(text, kontext)
        self.assertFalse(vorher.ok)

        leer = lambda t, k: []  # noqa: E731
        with patch.dict(pruefung.PRUEFSCHRITTE, {"ebenen": leer}):
            nachher = pruefung.pruefe_antwort(text, kontext)
        self.assertTrue(nachher.ok)


if __name__ == "__main__":
    unittest.main(verbosity=2)
