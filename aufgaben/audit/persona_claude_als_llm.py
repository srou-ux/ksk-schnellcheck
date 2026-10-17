"""Testphase: Claude spielt das Sprachmodell (Fakten-Extraktion von Hand, wie ein gutes Modell sie liefern würde).
Alles danach ist echt: Pflichtangaben, Bestätigung, Kern, Quellen, Platzhalter-Antwort, Kontrolle.
Nur erfundene Daten. Aufruf: python aufgaben/audit/persona_claude_als_llm.py"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from decimal import Decimal as D
from app import router, bestaetigung
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position as P

NP, GMBH = "natuerliche_person", "GmbH_UG_AG"
# (Frage, Fakten wie ein gutes Modell sie extrahiert; unbekannt = None)
FAELLE = [
 ("1 Werbeagentur, Grafiker 2.400 €, 2025 (Rechtsform des Grafikers unbekannt)",
  Fakten(anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter", auftraggeber_typ=GMBH, leistungsart="Grafik/Design",
         positionen=[P(betrag=D("2400"), rolle="honorar")])),
 ("1b dasselbe, Grafiker ist natürliche Person",
  Fakten(anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter", auftragnehmer_typ=NP, leistungsart="Grafik/Design",
         positionen=[P(betrag=D("2400"), rolle="honorar")])),
 ("2 Vorauszahlung 2026, BG Vorjahr 31.500 €",
  Fakten(anfrageart="vorauszahlung", jahr=2026, bemessungsgrundlage_vorjahr=D("31500"))),
 ("3 Fotograf 1.800 € davon 300 € nachgewiesene Fahrtkosten, 2024, natürliche Person",
  Fakten(anfrageart="bewertung", jahr=2024, verwerterart="typischer_verwerter", auftragnehmer_typ=NP, leistungsart="Fotografie",
         positionen=[P(betrag=D("1500"), rolle="honorar"), P(betrag=D("300"), rolle="fahrtkosten_nachgewiesen", nachgewiesen=True)])),
 ("4 Vier Veranstaltungen, Künstler 3.500 €, 2025, Einnahmeabsicht ja",
  Fakten(anfrageart="bewertung", jahr=2025, verwerterart="generalklausel", veranstaltungszahl=4, einnahmeabsicht=True,
         auftragnehmer_typ=NP, leistungsart="Musik", positionen=[P(betrag=D("3500"), rolle="honorar")])),
 ("5 Vier Veranstaltungen, Einnahmeabsicht unbekannt",
  Fakten(anfrageart="bewertung", jahr=2025, verwerterart="generalklausel", veranstaltungszahl=4,
         auftragnehmer_typ=NP, leistungsart="Musik", positionen=[P(betrag=D("3500"), rolle="honorar")])),
 ("6 GmbH-Dienstleister 5.000 €, 2025, Leistung Grafik",
  Fakten(anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter", auftragnehmer_typ=GMBH, leistungsart="Grafik/Design",
         positionen=[P(betrag=D("5000"), rolle="honorar")])),
 ("7 Säumniszuschlag: Rückstand 2.000 €, 4 Monate, 2025",
  Fakten(anfrageart="saeumniszuschlag", jahr=2025, rueckstand=D("2000"), saeumnis_monate=4)),
 ("8 Mehrere Positionen 2025: Grafiker 2.400, Texter 1.100, GmbH-Studio 5.000, Fotograf 800 (alle ausser GmbH natürliche Personen)",
  Fakten(anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter", auftragnehmer_typ=NP, leistungsart="Grafik/Design",
         positionen=[P(betrag=D("2400"), rolle="honorar"), P(betrag=D("1100"), rolle="honorar"),
                     P(betrag=D("5000"), rolle="honorar", bezeichnung="GmbH-Studio", kuenstlerisch=None),
                     P(betrag=D("800"), rolle="honorar")])),
 ("9 Reine Rechtsprechungsfrage ohne Jahr: BSG und Abgrenzung bei Werbeagenturen",
  Fakten(anfrageart="rechtsprechungsfrage", freitext_rest="Werbeagenturen Abgrenzung BSG")),
 ("10 Auskunft: Abgabesatz 2024 (kein passender Anfragetyp im Schema)",
  Fakten(anfrageart=None, jahr=2024, freitext_rest="Abgabesatz 2024")),
 ("11 Auskunft: Meldefrist Jahresmeldung 2025 (kein passender Anfragetyp)",
  Fakten(anfrageart=None, jahr=2025, freitext_rest="Meldefrist Jahresmeldung")),
]
if __name__ == "__main__":
    for text, fakten in FAELLE:
        llm = FakeLLM(); llm.registriere(text, fakten)
        try:
            a = router.bearbeite_frage(text, llm)
            stufe = "direkt"
            if a.sitzungskennung and a.fakten_hash:
                print("   [Bestätigungsfrage]", a.antwort.split("Stimmt das")[0].replace("\n", " ")[:260])
                bestaetigung.SPEICHER.bestaetige(a.sitzungskennung, a.fakten_hash)
                a = router.fuehre_nach_bestaetigung_aus(a.sitzungskennung, llm); stufe = "nach Bestätigung"
        except Exception as e:
            print(text, "\n   FEHLER", type(e).__name__, e); continue
        print(f"\n{text}\n   -> {stufe} | {a.ergebnisklasse}\n   {a.antwort.replace(chr(10), ' ')[:420]}")
