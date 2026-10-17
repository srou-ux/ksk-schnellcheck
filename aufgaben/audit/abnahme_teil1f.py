"""Abnahmetest für Chatbot Teil 1f (vor dem Bau geschrieben: muss VORHER rot sein, NACHHER 0 Lücken).
Fakten von Hand wie ein gutes Modell (Claude als Sprachmodell), alles danach echt. Nur erfundene Daten.
Sollwerte kommen aus dem Kern/der Excel, nicht aus dem Kopf. Aufruf: python aufgaben/audit/abnahme_teil1f.py"""
import sys, pathlib, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from decimal import Decimal as D
from kern import rechnen as K
from tests.app.hilfen import lauf_bestaetigt
from app import router, bestaetigung
from app.llm.fake import FakeLLM
from app.schema import Fakten, Position as P

NP, GMBH = "natuerliche_person", "GmbH_UG_AG"
LUECKEN = []


def eur(x):
    return f"{D(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pruefe(name, bedingung, detail=""):
    print(f"{name:62} {'ok' if bedingung else 'LÜCKE'}" + ("" if bedingung else f"   <- {detail}"))
    if not bedingung:
        LUECKEN.append(name)


def erste_antwort(text, fakten):
    # 17.10.2026 (Entscheidung des Nutzers „Geratenen Zweck immer nachfragen“): die Etiketten hier nennen keinen Zweck;
    # wie ein Nutzer wird die Zweck-Rückfrage per Knopf beantwortet (tests/app/zweck_knopf.py), dann geprüft wie bisher.
    from tests.app.zweck_knopf import mit_zweck

    llm = FakeLLM(); llm.registriere(text, fakten)
    return mit_zweck(router.bearbeite_frage(text, llm), fakten, llm), llm


def voll(text, fakten):
    return lauf_bestaetigt(FakeLLM(), text, fakten)


def mit_feld(klasse, **kw):
    """Baut das Objekt; unbekanntes (noch nicht gebautes) Feld bleibt unbeachtet, der Test wird dann rot."""
    return klasse(**kw)


# ---- A: Rechtsform je Position ------------------------------------------------------------
t = "A Gemischte Positionen 2025 (je Position eigene Rechtsform)"
f = Fakten(anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter", leistungsart="Grafik/Design",
           positionen=[P(betrag=D("2400"), rolle="honorar", auftragnehmer_typ=NP),
                       P(betrag=D("1100"), rolle="honorar", auftragnehmer_typ=NP),
                       P(betrag=D("5000"), rolle="honorar", auftragnehmer_typ=GMBH, bezeichnung="GmbH-Studio"),
                       P(betrag=D("800"), rolle="honorar", auftragnehmer_typ=NP)])
soll_bg = D("2400") + D("1100") + D("800")
soll_abgabe = K.berechne_abgabe(soll_bg, 2025)[0]
a, _ = erste_antwort(t, f)
z = " ".join(a.fakten_zusammenfassung) or a.antwort
pruefe("A1 Bestätigungsfrage zeigt Rechtsform je Position",
       a.sitzungskennung and z.count("natürliche Person") >= 3 and re.search(r"GmbH|Gesellschaft|Kapital", z), z[:200])
b = voll(t, f)
pruefe("A2 BG und Abgabe nur aus den natürlichen Personen", eur(soll_bg) in b.antwort and eur(soll_abgabe) in b.antwort, b.antwort[:200])
pruefe("A3 falsche Summe (alle Posten) kommt nicht vor, es wurde gerechnet", eur(D("9300")) not in b.antwort and "Rückfrage" not in b.ergebnisklasse, b.ergebnisklasse)
pruefe("A4 Ausschluss GmbH-Position wird erklärt", "Nicht zur Bemessungsgrundlage" in b.antwort or "keine Bemessungsgrundlage" in b.antwort.lower(), b.antwort[:300])

t = "A5 Rechtsform einer Position fehlt -> Rückfrage"  # Etikett, keine Nutzeraussage (seit 11.10.2026 wird „unbekannt“ als Aussage gelesen)
f2 = Fakten(anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter", leistungsart="Grafik/Design",
            positionen=[P(betrag=D("2400"), rolle="honorar", auftragnehmer_typ=NP),
                        P(betrag=D("900"), rolle="honorar", bezeichnung="Studio Nord")])
a, _ = erste_antwort(t, f2)
pruefe(t, a.ergebnisklasse == K.RUECKFRAGE and any("Studio Nord" in r or "Position 2" in r for r in a.rueckfragen),
       f"{a.ergebnisklasse} {a.rueckfragen}")

t = "A6 globale Rechtsform gilt weiter als Vorgabe (Altverhalten)"
f3 = Fakten(anfrageart="bewertung", jahr=2025, verwerterart="typischer_verwerter", auftragnehmer_typ=NP, leistungsart="Grafik/Design",
            positionen=[P(betrag=D("2400"), rolle="honorar")])
b = voll(t, f3)
pruefe(t, eur(2400) in b.antwort and eur(K.berechne_abgabe(D("2400"), 2025)[0]) in b.antwort, b.antwort[:200])

# ---- B: Säumniszuschlag --------------------------------------------------------------------
t = "B Säumniszuschlag 2025, Rückstand 2.000 €, 4 Monate"
f = Fakten(anfrageart="saeumniszuschlag", jahr=2025, rueckstand=D("2000"), saeumnis_monate=4)
b = voll(t, f)
pruefe("B1 Antwort nennt 'Säumniszuschlag'", "äumniszuschlag" in b.antwort, b.antwort[:200])
pruefe("B2 kein 'Abgabesatz' und kein 'Abgabepflichtig' im Text", "Abgabesatz" not in b.antwort and "Abgabepflichtig" not in b.antwort, b.antwort[:300])
pruefe("B3 Zuschlag aus dem Kern genannt", eur(K.saeumniszuschlag([D("2000")], 4, 2025).abgabe) in b.antwort, b.antwort[:200])

# ---- C: Auskunftsfragen --------------------------------------------------------------------
class _Leer:
    antwort = "(Anfrageart 'auskunft' fehlt noch im Schema)"; ergebnisklasse = "-"; fundstellen = []; rueckfragen = []


def auskunft(thema, jahr):
    t = f"C Auskunft {thema} {jahr}"
    try:
        f = Fakten(anfrageart="auskunft", jahr=jahr, auskunft_thema=thema)  # Vorschlag: Literal abgabesatz|schwelle|meldefrist|aufbewahrung|pauschale
        return t, voll(t, f)
    except Exception as e:
        return t, _Leer()


t, b = auskunft("abgabesatz", 2024)
pruefe("C1 Abgabesatz 2024 aus der Excel", "5" in b.antwort and "Rückfrage" not in b.ergebnisklasse and b.fundstellen, f"{b.ergebnisklasse} {b.antwort[:200]}")
t, b = auskunft("schwelle", 2025)
pruefe("C2 Schwelle 2025 aus der Excel (700 €), mit Fundstelle", "700" in b.antwort and bool(b.fundstellen), b.antwort[:200])
t, b = auskunft("meldefrist", 2025)
pruefe("C3 Meldefrist 2025 = Kern-Datum", K.meldefrist(2025).strftime("%d.%m.%Y") in b.antwort and bool(b.fundstellen), b.antwort[:200])
t, b = auskunft("aufbewahrung", 2025)
pruefe("C4 Aufbewahrung = Kern-Datum", K.aufbewahrung_bis(2025).strftime("%d.%m.%Y") in b.antwort, b.antwort[:200])
t = "C5 Auskunft ohne Jahr -> Rückfrage"
try:
    a, _ = erste_antwort(t, Fakten(anfrageart="auskunft", auskunft_thema="abgabesatz"))
except Exception:
    a = _Leer()
pruefe(t, a.ergebnisklasse == K.RUECKFRAGE, a.ergebnisklasse)
t, b = auskunft("abgabesatz", 2035)
pruefe("C6 Jahr ohne Excel-Wert -> Nicht abgedeckt, keine Zahl erfunden", b.ergebnisklasse == K.NICHT_ABGEDECKT, f"{b.ergebnisklasse} {b.antwort[:200]}")
pruefe("C7 Schlusssatz 'Entwurf – vom Steuerberater zu prüfen' vorhanden", "Entwurf" in b.antwort and "Steuerberater" in b.antwort)

# ---- D: Fundstellen mit richtigem Jahr -------------------------------------------------------
t = "D Vier Veranstaltungen 2025, Einnahmeabsicht ja"
f = Fakten(anfrageart="bewertung", jahr=2025, verwerterart="generalklausel", veranstaltungszahl=4, einnahmeabsicht=True,
           auftragnehmer_typ=NP, leistungsart="Musik", positionen=[P(betrag=D("3500"), rolle="honorar")])
b = voll(t, f)
alle = " ".join(b.fundstellen) + " " + b.antwort
pruefe("D1 keine Fundstelle 'Kopie 2022-01-22' bei Jahr 2025", "2022-01-22" not in alle, alle[:300])
pruefe("D2 Fassung B für 2025 genannt, nicht A", "Fassung A" not in alle)

# ---- E: Rückfragen als Schaltflächen ---------------------------------------------------------
t = "E Einnahmeabsicht fehlt -> Schaltflächen"  # Etikett, keine Nutzeraussage
f = Fakten(anfrageart="bewertung", jahr=2025, verwerterart="generalklausel", veranstaltungszahl=4,
           auftragnehmer_typ=NP, leistungsart="Musik", positionen=[P(betrag=D("3500"), rolle="honorar")])
a, _ = erste_antwort(t, f)
opt = getattr(a, "rueckfrage_optionen", None)
pruefe("E1 Antwort hat Feld rueckfrage_optionen mit ja/nein", bool(opt) and any({"ja", "nein"} <= {str(o).lower() for o in (x.get("optionen") if isinstance(x, dict) else [])} for x in opt), opt)
t = "E2 Rechtsform-Rückfrage bietet die Rechtsformen an"
a, _ = erste_antwort(t, f2)
opt = getattr(a, "rueckfrage_optionen", None)
pruefe(t, bool(opt) and any(len(x.get("optionen", [])) >= 3 for x in opt if isinstance(x, dict)), opt)

# ---- F: Pflichtangaben je Rechenart ------------------------------------------------------------
t = "F Vorauszahlung ohne Vorjahres-BG fragt nur danach"
a, _ = erste_antwort(t, Fakten(anfrageart="vorauszahlung", jahr=2026))
r = " ".join(a.rueckfragen).lower()
pruefe(t, a.ergebnisklasse == K.RUECKFRAGE and "vorjahr" in r and "rechtsform" not in r and "leistung" not in r, a.rueckfragen)

# ---- G: bisher Funktionierendes bleibt -------------------------------------------------------
t = "G Fotograf 1.800 € mit 300 € nachgewiesenen Fahrtkosten, 2024"
f = Fakten(anfrageart="bewertung", jahr=2024, verwerterart="typischer_verwerter", auftragnehmer_typ=NP, leistungsart="Fotografie",
           positionen=[P(betrag=D("1500"), rolle="honorar"), P(betrag=D("300"), rolle="fahrtkosten_nachgewiesen", nachgewiesen=True)])
b = voll(t, f)
pruefe(t, eur(1500) in b.antwort and eur(1800) not in b.antwort.replace("1.500,00", ""), b.antwort[:200])

print(f"\nLücken: {len(LUECKEN)}")
sys.exit(1 if LUECKEN else 0)
