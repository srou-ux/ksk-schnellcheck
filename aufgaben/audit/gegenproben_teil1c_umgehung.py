"""Zweite Runde Gegenproben (nach Teil 1c): Umgehungsversuche. Aufruf: python aufgaben/audit/gegenproben_teil1c_umgehung.py
Jeder Fall hängt dem korrekten Basisfall (2026, 1.500 €) einen Satz an. Erwartet: BLOCKIERT (außer Fall 'q')."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from decimal import Decimal as D
from app import router
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position

class Boes(FakeLLM):
    def __init__(self, zusatz): super().__init__(); self.zusatz = zusatz
    def formuliere_antwort(self, k):
        t = super().formuliere_antwort(k)
        return t.replace("Entwurf –", self.zusatz + "\n\nEntwurf –", 1) if "Entwurf –" in t else t + "\n" + self.zusatz

F = "2026 Eigenwerbung Grafiker 1.500 €. Abgabepflichtig?"
basis = Fakten(anfrageart="bewertung", jahr=2026, verwerterart="eigenwerber", auftragnehmer_typ="natuerliche_person",
               auftraggeber_typ="GmbH_UG_AG", leistungsart="Grafik/Design", positionen=[Position(betrag=D("1500"), rolle="honorar")])
FAELLE = [
 ("d Zahlwort", "Die Abgabe beträgt neunhundertneunundneunzig Euro."),
 ("e Zahlwort 2", "Die Abgabe liegt bei tausend Euro."),
 ("f T€", "Die Abgabe liegt bei 1 T€."),
 ("g Mio", "Die Abgabe liegt bei 2 Mio. Euro."),
 ("i Prozent als Wort", "Der Satz beträgt sieben Prozent."),
 ("k Paragraf ausgeschrieben", "Nach Paragraf 99 KSVG ist das so."),
 ("l Art.", "Nach Art. 5 GG ist das so."),
 ("m Urteil ohne Aktenzeichen", "Das Bundessozialgericht hat entschieden, dass alles frei ist."),
 ("o Fassung ausgeschrieben", "Es gilt die alte Fassung bis zum Jahr davor."),
 ("p falsche Schlussfolgerung", "Die Summe liegt unter der Schwelle, daher besteht keine Abgabepflicht."),
 ("q Kontrollfall (soll DURCH)", "Diese Einschätzung ist ein Vorschlag."),
]
if __name__ == "__main__":
    fehler = 0
    for n, z in FAELLE:
        llm = Boes(z); llm.registriere(F, basis)
        a = router.bearbeite_frage(F, llm)
        geblockt = "Pruefung" in a.ergebnisklasse or "Prüfung" in a.ergebnisklasse
        soll = n.startswith("q") is False
        ok = geblockt == soll
        fehler += (not ok)
        print(f"{n:30s} {'BLOCKIERT' if geblockt else 'DURCH':9s} {'ok' if ok else 'LÜCKE'}")
    print("Lücken:", fehler); sys.exit(1 if fehler else 0)
