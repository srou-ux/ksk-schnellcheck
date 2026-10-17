"""Abnahme für den Nachtrag zu Teil 1f (vor dem Bau geschrieben: muss VORHER rot sein, NACHHER 0 Lücken).
Hintergrund: Mistral-Lauf nach 1f (aufgaben/audit/ergebnisse_mistral.md): das echte Modell ordnet Anfragen falsch zu
(auskunft/hinweis) und schreibt Rückfragen selbst. Die Fälle bilden das Modellverhalten mit FakeLLM nach.
Nur erfundene Daten. Aufruf: python aufgaben/audit/abnahme_teil1f_nachtrag.py"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from decimal import Decimal as D
from kern import rechnen as K
from app import router, bestaetigung
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position as P

LUECKEN = []
NP = "natuerliche_person"


def pruefe(name, ok, detail=""):
    print(f"{name:78} {'ok' if ok else 'LÜCKE'}" + ("" if ok else f"   <- {str(detail)[:230]}"))
    if not ok:
        LUECKEN.append(name)


def voll(frage, fakten, llm=None):
    llm = llm or FakeLLM(); llm.registriere(frage, fakten)
    a = router.bearbeite_frage(frage, llm)
    if a.sitzungskennung and a.fakten_hash:
        bestaetigung.SPEICHER.bestaetige(a.sitzungskennung, a.fakten_hash)
        a = router.fuehre_nach_bestaetigung_aus(a.sitzungskennung, llm)
    return a


class NurFesteTexte(FakeLLM):
    """Modell, das bei jedem Schreibversuch abstürzt: Rückfragen und Hinweise dürfen es nie aufrufen."""
    def formuliere_antwort(self, kontext):
        raise AssertionError("Das Modell darf für diese Antwort nicht aufgerufen werden")


# A: Modell ordnet falsch zu --------------------------------------------------------------
f = "Wir sind eine Werbeagentur. Im Jahr 2025 haben wir einem freiberuflichen Grafiker 2.400 Euro gezahlt. Ist das abgabepflichtig?"
a = voll(f, Fakten(anfrageart="auskunft", jahr=2025, positionen=[P(betrag=D("2400"), rolle="honorar")]))
pruefe("A1 'auskunft' ohne Thema bei einer Rechnungsfrage -> keine Auskunfts-Rückfrage", "Auskunft" not in a.antwort and "Worüber" not in a.antwort, a.antwort)

f = "Ist ein Auftrag an einen Texter abgabepflichtig?"
a = voll(f, Fakten(anfrageart="auskunft", jahr=2025, auskunft_thema="abgabesatz"))
pruefe("A2 erfundenes Auskunftsthema (Frage nennt keinen Abgabesatz) -> keine Auskunft", "Abgabesatz des Jahres" not in a.antwort and "Auskunft aus dem Regelwerk" not in a.ergebnisklasse, a.antwort)

f = "Unser Verein hat 2025 vier Konzerte veranstaltet und die Musiker mit zusammen 3.500 Euro bezahlt. Wir wollten Einnahmen erzielen."
a = voll(f, Fakten(anfrageart="hinweis"))
pruefe("A3 'hinweis' bei einer Frage mit Jahr und Betrag -> keine Begrüßung", "Hallo" not in a.antwort and a.ergebnisklasse != "Hinweis", a.antwort)

a = voll("hallo", Fakten(anfrageart="hinweis"))
pruefe("A4 echte Begrüßung bleibt eine Begrüßung", "Hallo" in a.antwort or a.ergebnisklasse == "Hinweis", a.antwort)

f = "Wie hoch ist der Abgabesatz im Jahr 2024?"
a = voll(f, Fakten(anfrageart="auskunft", jahr=2024, auskunft_thema="abgabesatz"))
pruefe("A5 echte Auskunftsfrage bleibt eine Auskunft (Kontrolle)", "5" in a.antwort and "Auskunft" in a.ergebnisklasse, a.antwort)

# B: Rückfragen und Hinweise ohne Modell ------------------------------------------------------
f = "Wir haben 2025 Honorar gezahlt."
try:
    a = voll(f, Fakten(anfrageart="bewertung", jahr=2025, positionen=[P(betrag=D("900"), rolle="honorar")]), NurFesteTexte())
    pruefe("B1 Rückfrage kommt ohne Modellaufruf zustande", a.ergebnisklasse == K.RUECKFRAGE and a.rueckfragen, a.ergebnisklasse)
except AssertionError as e:
    pruefe("B1 Rückfrage kommt ohne Modellaufruf zustande", False, e)
try:
    a = voll("hallo", Fakten(anfrageart="hinweis"), NurFesteTexte())
    pruefe("B2 Begrüßung ohne Modellaufruf", "Hallo" in a.antwort)
except AssertionError as e:
    pruefe("B2 Begrüßung ohne Modellaufruf", False, e)
try:
    a = voll("x", Fakten(anfrageart="bewertung"), NurFesteTexte())
    pruefe("B3 Rückfrage nach dem Jahr ohne Modellaufruf", a.ergebnisklasse == K.RUECKFRAGE and "Kalenderjahr" in a.antwort, a.antwort)
except AssertionError as e:
    pruefe("B3 Rückfrage nach dem Jahr ohne Modellaufruf", False, e)
f = "Wir haben 2025 Honorar gezahlt."
a = voll(f, Fakten(anfrageart="bewertung", jahr=2025, positionen=[P(betrag=D("900"), rolle="honorar")]))
pruefe("B4 Rückfrage enthält keinen vom Modell erfundenen Satz ('einmalig', 'wiederkehrend', 'Fassung B des')",
       not any(w in a.antwort for w in ("einmalig", "wiederkehrend", "Fassung B des", "bereits in einem vorherigen")), a.antwort)

# C: Rückfrage nur nach dem, was der Kern braucht -------------------------------------------------
f = "Ein selbständiger Fotograf hat uns 2024 insgesamt 1.800 Euro berechnet, darin sind 300 Euro nachgewiesene Fahrtkosten."
a = voll(f, Fakten(anfrageart="bewertung", jahr=2024, positionen=[
    P(betrag=D("1500"), rolle="honorar", bezeichnung="Fotografie"),
    P(betrag=D("300"), rolle="fahrtkosten_nachgewiesen", bezeichnung="Fahrtkosten", nachgewiesen=True)]))
n = sum(1 for r in a.rueckfragen if "Rechtsform" in r)
pruefe("C1 Rechtsform-Rückfrage nur für die Honorar-Position, nicht für die Fahrtkosten", n <= 1 and not any("Fahrtkosten" in r for r in a.rueckfragen), a.rueckfragen)

f = "2025: Grafiker 2.400, Texterin 1.100, GmbH-Studio 5.000, Fotograf 800. Nur das Studio ist eine GmbH."
a = voll(f, Fakten(anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter", positionen=[
    P(betrag=D("2400"), rolle="honorar", auftragnehmer_typ=NP), P(betrag=D("1100"), rolle="honorar", auftragnehmer_typ=NP),
    P(betrag=D("5000"), rolle="honorar", auftragnehmer_typ="GmbH_UG_AG"), P(betrag=D("800"), rolle="honorar", auftragnehmer_typ=NP)]))
pruefe("C2 gemischte Positionen mit bekannter Rechtsform: keine Rückfrage nach Leistungsart, es wird gerechnet", a.ergebnisklasse != K.RUECKFRAGE and "4.300,00" in a.antwort, f"{a.ergebnisklasse} {a.antwort[:200]}")
pruefe("C3 in keiner Antwort steht die falsche Summe 9.300,00 €", "9.300,00" not in a.antwort)

print(f"\nLücken: {len(LUECKEN)}")
sys.exit(1 if LUECKEN else 0)
