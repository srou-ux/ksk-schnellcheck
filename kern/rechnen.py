"""Regelkern v0 – deterministische Prüfung und Berechnung (ENTWURF, vom Steuerberater zu prüfen).
Kein Sprachmodell. Zahlen kommen aus parameter.json (erzeugt aus dem Regelkatalog). Geld nur als Decimal.
Das System macht Vorschläge, der Steuerberater entscheidet."""
from dataclasses import dataclass, field
from decimal import Decimal as D
import json, pathlib, datetime, re

P = json.loads((pathlib.Path(__file__).with_name("parameter.json")).read_text(encoding="utf-8"))
HINWEIS = "Entwurf – vom Steuerberater zu prüfen"

ABGABEPFLICHTIG = "Abgabepflichtig (Vorschlag)"
NICHT = "Nicht abgabepflichtig (Vorschlag)"
GRENZFALL = "Grenzfall → Steuerberater entscheidet"
RUECKFRAGE = "Rückfrage nötig"
NICHT_ABGEDECKT = "Nicht abgedeckt (Quelle fehlt)"
SPERRE = "Sperre — Rechnung prüfen"


@dataclass
class Ergebnis:
    klasse: str
    begruendung: list = field(default_factory=list)
    fundstellen: list = field(default_factory=list)
    regeln: list = field(default_factory=list)
    rueckfragen: list = field(default_factory=list)
    bemessungsgrundlage: D | None = None
    abgabe: D | None = None
    hinweis: str = HINWEIS


class RegisterLuecke(Exception):
    """Für Schlüssel/Jahr gibt es keinen Eintrag im Regelregister → Ergebnis 'Nicht abgedeckt'."""


def _zeilen(schluessel, jahr):
    z = [r for r in P.get("register", []) if r["schluessel"] == schluessel
         and (r["von"] is None or jahr >= r["von"]) and (r["bis"] is None or jahr <= r["bis"])]
    if not z:
        raise RegisterLuecke(f"Regelregister: kein Eintrag für '{schluessel}' im Jahr {jahr}.")
    return z


def reg(schluessel, jahr):
    z = _zeilen(schluessel, jahr)
    if len(z) > 1:
        raise RegisterLuecke(f"Regelregister: '{schluessel}' im Jahr {jahr} mehrdeutig.")
    return z[0]


def wert(schluessel, jahr):
    """Zahlenwert (Decimal) aus dem Regelregister, gültig im Jahr."""
    return D(reg(schluessel, jahr)["wert"])


def werte(schluessel, jahr):
    """Alle Textwerte eines Listen-Schlüssels, gültig im Jahr."""
    return {r["wert"] for r in _zeilen(schluessel, jahr)}


def vergleich(schluessel, jahr, a, b):
    """Wendet den im Register hinterlegten Operator an: a <op> b."""
    op = reg(schluessel, jahr)["operator"]
    return {">": a > b, ">=": a >= b, "<": a < b, "<=": a <= b, "=": a == b}[op]


def _luecke(f):
    """Fehlt ein Regelregister-Eintrag, liefert die Funktion 'Nicht abgedeckt' statt eines Fehlers."""
    import functools
    @functools.wraps(f)
    def g(*a, **k):
        try:
            return f(*a, **k)
        except RegisterLuecke as x:
            return Ergebnis(NICHT_ABGEDECKT, [str(x)])
    return g


def _d(x):
    return x if isinstance(x, D) else D(str(x))


def schwelle(jahr):
    s = P["schwelle"].get(str(jahr))
    if not s or not s["euro"]:
        return None
    return s


def abgabesatz(jahr):
    s = P["abgabesatz"].get(str(jahr))
    return None if not s else D(s["prozent"])


def berechne_abgabe(bemessung, jahr):
    """Abgabe = Bemessungsgrundlage × Abgabesatz des Jahres. Rundungsregel ist nicht belegt:
    ergibt sich mehr als 2 Nachkommastellen, wird keine gerundete Zahl behauptet."""
    r = abgabesatz(jahr)
    if r is None:
        return None, "Abgabesatz für dieses Jahr nicht im Regelwerk"
    roh = _d(bemessung) * r / 100
    if roh != roh.quantize(D("0.01")):
        return None, f"Rundung ungeklärt (ungerundet {roh})"
    return roh.quantize(D("0.01")), None


def _mit_abgabe(e, jahr):
    a, hinweis = berechne_abgabe(e.bemessungsgrundlage, jahr)
    e.abgabe = a
    e.fundstellen.append(P["abgabesatz"][str(jahr)]["fundstelle"] if str(jahr) in P["abgabesatz"] else "")
    if hinweis:
        e.rueckfragen.append(hinweis)
    return e


def netto(betrag, ust_gesondert_ausgewiesen=0):
    """KSVG § 25 Abs. 2 S. 1: abzüglich gesondert ausgewiesener Umsatzsteuer (R-18)."""
    return _d(betrag) - _d(ust_gesondert_ausgewiesen)


def jahr_fehlt(jahr):
    """Das Jahr ist Pflichteingabe (R-Querschnitt): ohne Jahr kein Ergebnis."""
    if jahr is None:
        return Ergebnis(RUECKFRAGE, ["Jahr fehlt."], rueckfragen=["Für welches Kalenderjahr?"])
    return None


def pruefe_eigenwerbung(jahr, summe):
    """Eigenwerbung (KSVG § 24 Abs. 2 S. 1 Nr. 1): Schwelle je Jahr, 'übersteigt' (R-11, R-24, R-10)."""
    if jahr_fehlt(jahr):
        return jahr_fehlt(jahr)
    summe = _d(summe)
    s = schwelle(jahr)
    if s is None:
        return Ergebnis(NICHT_ABGEDECKT, [f"Für {jahr} ist keine Schwelle im Regelwerk."])
    grenze = D(s["euro"])
    e = Ergebnis(NICHT, regeln=["R-11", "R-24"], fundstellen=["KSVG § 24 Abs. 2 S. 2, § 54", s["fundstelle"]])
    if s["fassung"] == "A":
        e.regeln = ["R-10"]
        if summe <= grenze:
            e.klasse = NICHT
            e.begruendung.append(f"Fassung A: Summe {summe} € ≤ {grenze} € (Geringfügigkeitsgrenze).")
        else:
            e.klasse = GRENZFALL
            e.begruendung.append("Fassung A: über 450 €, zusätzlich muss die Auftragserteilung nicht nur gelegentlich sein.")
            e.rueckfragen.append("Wie oft und in welchem Abstand wurden Aufträge erteilt (Regelmäßigkeit)?")
        return e
    if vergleich("schwelle.operator", jahr, summe, grenze):
        e.klasse = ABGABEPFLICHTIG
        e.bemessungsgrundlage = summe
        e.begruendung.append(f"Summe {summe} € übersteigt die Schwelle {grenze} € des Jahres {jahr}.")
        _mit_abgabe(e, jahr)
    else:
        e.begruendung.append(f"Summe {summe} € übersteigt die Schwelle {grenze} € des Jahres {jahr} nicht.")
    return e


def privater_auftraggeber():
    """Auftraggeber ist eine Privatperson oder private Personengruppe (z. B. Hochzeit, Geburtstag):
    nicht abgabepflichtig, unabhängig von Betrag und Leistung (R-40, R-133; Fundstellen im
    Regelkatalog). Ein Vertreter des Künstlers kann meldepflichtig sein (R-40)."""
    return Ergebnis(NICHT, regeln=["R-40", "R-133"])


def pruefe_typischer_verwerter(jahr, entgelte):
    """Unternehmen nach § 24 Abs. 1 (z. B. Werbung für Dritte): dem Grunde nach abgabepflichtig, keine Schwelle (R-07)."""
    e = Ergebnis(ABGABEPFLICHTIG, regeln=["R-07"], fundstellen=["KSVG § 24 Abs. 1 S. 1"],
                 begruendung=["Typischer Verwerter: keine Schwelle."], bemessungsgrundlage=_d(entgelte))
    return _mit_abgabe(e, jahr)


def zahlungsjahr(zahlungsdatum):
    """KSVG § 25 Abs. 1 S. 1: Entgelte, die 'im Laufe eines Kalenderjahres' gezahlt werden (R-41, Ableitung).
    Rechnungsdatum ist nicht maßgeblich. Fehlt das Zahlungsdatum: Rückfrage."""
    if zahlungsdatum is None:
        return None, Ergebnis(RUECKFRAGE, ["Zahlungsdatum fehlt."], rueckfragen=["Wann wurde gezahlt?"], regeln=["R-41"])
    return zahlungsdatum.year, None


def verpflegung(jahr, stunden, uebernachtung=False, erstattung=0, inland=True):
    """Verpflegungsmehraufwand bei Inlandsreisen (R-236, EStG § 9 Abs. 4a S. 3, Info 10):
    mehr als 8 Stunden (ohne Übernachtung) 14 €; 24 Stunden 28 €; An-/Abreisetag mit Übernachtung 14 € (ab 2020).
    Rückgabe: (nicht zur Bemessungsgrundlage zählender Betrag, Ergebnis-Hinweis)."""
    erstattung = _d(erstattung)
    stunden = _d(stunden)
    if not inland:
        return D(0), Ergebnis(NICHT_ABGEDECKT, ["Auslandsreisen: länderweise Pauschbeträge nicht erfasst."], regeln=["R-236"])
    try:
        kl, gr = wert("verpflegung.pauschale_klein", jahr), wert("verpflegung.pauschale_gross", jahr)
    except RegisterLuecke as x:
        return D(0), Ergebnis(NICHT_ABGEDECKT, [str(x)], regeln=["R-236"])
    e = Ergebnis(ABGABEPFLICHTIG, regeln=["R-236", "R-47"], fundstellen=["EStG § 9 Abs. 4a S. 3 Nr. 1–3", "KSK-Info 10, Abschn. 3"])
    if vergleich("verpflegung.stunden_ganztag", jahr, stunden, wert("verpflegung.stunden_ganztag", jahr)):
        pausch = gr
    elif uebernachtung:
        pausch = kl
    elif vergleich("verpflegung.stunden_grenze", jahr, stunden, wert("verpflegung.stunden_grenze", jahr)):
        pausch = kl
    else:
        pausch = D(0)
        if stunden == wert("verpflegung.stunden_grenze", jahr):
            e.klasse = GRENZFALL
            e.begruendung.append("Genau 8 Stunden: Gesetz verlangt 'mehr als 8 Stunden', KSK-Info 10 schreibt '8 bis 24'. Vorschlag nach Gesetzeswortlaut: keine Pauschale.")
    nicht_zaehlend = min(erstattung, pausch)
    e.begruendung.append(f"Pauschale {pausch} €; davon nicht zur Bemessungsgrundlage: {nicht_zaehlend} €.")
    return nicht_zaehlend, e


def reisekosten_ohne_nachweis(betrag):
    """R-176: nicht nachgewiesene Reisekosten → Rückfrage; bis zur Klärung zählen sie mit."""
    e = Ergebnis(RUECKFRAGE, regeln=["R-47", "R-176"], fundstellen=["KSVEntgV § 1 Nr. 1", "KSK-Info 10, Abschn. 3"],
                 begruendung=["Nicht nachgewiesen oder nicht aufgeschlüsselt: kein Abzug anerkannt."],
                 rueckfragen=["Kostenart? Entstehung beim Künstler? Nachweise?"], bemessungsgrundlage=_d(betrag))
    return e


def vervielfaeltigung(gestaltung, vervielfaeltigung_nachtraeglich, gesondert_ausgewiesen=True):
    """R-49/R-176: nachträgliche, nicht künstlerische Vervielfältigung (gesondert ausgewiesen) zählt nicht mit."""
    g = _d(gestaltung); v = _d(vervielfaeltigung_nachtraeglich)
    e = Ergebnis(ABGABEPFLICHTIG, regeln=["R-49", "R-176"], fundstellen=["KSK-Info 10, Abschn. 1"])
    if gesondert_ausgewiesen:
        e.bemessungsgrundlage = g
        e.begruendung.append("Nachträgliche Vervielfältigung gesondert ausgewiesen: nicht Teil der Bemessungsgrundlage.")
    else:
        e.klasse = RUECKFRAGE; e.bemessungsgrundlage = g + v
        e.rueckfragen.append("Vervielfältigung nicht gesondert ausgewiesen: bitte aufschlüsseln.")
    return e


def vertreter(abgabestatus_dritter=None, vertrag_im_namen_des_kuenstlers=None):
    """R-33/R-78, KSVG § 25 Abs. 3: Wer zahlt, hängt vom Abgabestatus des Dritten ab; unbekannt → Rückfrage."""
    e = Ergebnis(RUECKFRAGE, regeln=["R-33", "R-78"], fundstellen=["KSVG § 25 Abs. 3", "KSK-Info 27"])
    if abgabestatus_dritter is None or vertrag_im_namen_des_kuenstlers is None:
        e.rueckfragen += ["Vertrag, Vollmacht, im Namen und für Rechnung wessen?", "Ist der Auftraggeber selbst abgabepflichtig?"]
        e.begruendung.append("Abgabeschuldner nicht allein aus der Rechnung bestimmbar.")
        return e
    if vertrag_im_namen_des_kuenstlers and abgabestatus_dritter:
        e.klasse = NICHT; e.begruendung.append("Dritter ist selbst abgabepflichtig: er zahlt, nicht die Agentur.")
    elif vertrag_im_namen_des_kuenstlers:
        e.klasse = ABGABEPFLICHTIG; e.begruendung.append("Dritter nicht abgabepflichtig: Agentur meldet die Entgelte.")
    else:
        e.klasse = ABGABEPFLICHTIG; e.begruendung.append("Eigengeschäft der Agentur.")
    return e


def gelegenheitsnachweis():
    """Nur die Vertragsparteien benennen, ohne weitere Mitwirkung: keine Abgabe auf diese Entgelte (R-35)."""
    return Ergebnis(
        NICHT,
        ["Nur Gelegenheitsnachweis, keine weitere Mitwirkung: keine Abgabe auf die Entgelte."],
        regeln=["R-35"],
        fundstellen=["KSK-Info 04, Abschn. 3b"],
    )


def nachweismakler():
    """R-35 (KSK-Info 04, Abschn. 3b; BSG B 3 KS 1/18 R Rn. 25): wer nur die Vertragsparteien benennt, ohne
    Vertragsschluss, Organisation, Honorareinzug oder Haftung, ist dem Grunde nach abgabepflichtig, schuldet aber
    keine Abgabe auf Entgelte. Grenzfall, weil jede weitergehende Mitwirkung das ändert."""
    e = Ergebnis(GRENZFALL, regeln=["R-35"])
    e.begruendung.append("Nur Benennung der Vertragsparteien (Nachweismakler): dem Grunde nach abgabepflichtig, "
                         "aber keine Abgabe auf Entgelte.")
    e.begruendung.append("Das ändert sich bei Unterschrift unter den Vertrag, Mitwirkung an Organisation, Kartenverkauf "
                         "oder Werbung, Einzug oder Weiterleitung des Honorars oder Haftung.")
    return e


def musikverein_schueler(jahr, schueler, struktur_bekannt=False, weitere_taetigkeiten_bekannt=False):
    """R-53/R-54: Schülerzahl allein entscheidet nicht (KSK-Verwaltungsvermutung)."""
    e = Ergebnis(RUECKFRAGE, regeln=["R-53", "R-54"], fundstellen=["KSK-Info 12, Abschn. 2"],
                 begruendung=["Schülerzahl ist nur ein Merkmal der KSK-Praxis, keine gesetzliche Grenze."])
    if not (struktur_bekannt and weitere_taetigkeiten_bekannt):
        e.rueckfragen += ["Strukturierter Unterricht gegen Gebühren?", "Vergütung je Ausbilder?", "Weitere Tätigkeiten des Vereins?"]
        return e
    e.klasse = GRENZFALL if vergleich("musikverein.schueler_grenze", jahr, _d(schueler), wert("musikverein.schueler_grenze", jahr)) else NICHT
    e.begruendung.append('Vermutung der KSK-Praxis (kein Gesetz); zahlt der Verein einem Ausbilder mehr als in Info 12 genannt, Grenzfall.')
    return e


# ---------------------------------------------------------------------------------------------
# Tranche 2 (Entwurf): Positionen, Veranstaltungen, Vorauszahlung, Säumnis, Fristen, Pauschalen
# ---------------------------------------------------------------------------------------------
# Zahlungen an Kapital-/Handelsgesellschaften: Liste im Regelregister (rechtsform.kein_entgelt); GbR zählt (R-59)


def restbetrag(gesamt, teile):
    """Rest einer Rechnung: Rechnungsbetrag minus die darin enthaltenen Teilbeträge
    ('1.200 Euro, darin 300 Euro Druckkosten' -> 900). Testprotokoll 11.10.2026: das
    Sprachmodell rechnet nicht; bei einer Korrektur des Rechnungsbetrags rechnet der Kern neu."""
    return _d(gesamt) - sum((_d(t) for t in teile), D(0))


def summe_positionen(positionen, jahr):
    """Summe der Entgelte aus Einzelpositionen.
    Position: {betrag, art, empfaenger?, kuenstlerisch?}. Nicht zählend: Zahlungen an GmbH/KG/OHG (R-138, R-216),
    nicht künstlerische Leistungen, nachgewiesene Fahrtkosten (R-47), Gewinnzuweisung (R-46), Verwertungsgesellschaft (R-44),
    übliche Bewirtung (R-48), gesondert ausgewiesene USt (R-18). Alles andere zählt (R-41)."""
    ausgenommen_arten = set(_AUSSCHLUSSGRUENDE)
    s = D(0)
    kein = werte("rechtsform.kein_entgelt", jahr)
    for p in positionen:
        if p.get("empfaenger") in kein:
            continue
        if p.get("kuenstlerisch") is False:
            continue
        if p.get("art") in ausgenommen_arten:
            continue
        s += _d(p["betrag"])
    return s


_AUSSCHLUSSGRUENDE = {
    "vervielfaeltigung_nachtraeglich": ("nachträgliche Vervielfältigung", None),
    "fahrtkosten_nachgewiesen": ("nachgewiesene Fahrtkosten", "R-47"),
    "gewinnzuweisung": ("Gewinnzuweisung", "R-46"),
    "verwertungsgesellschaft": ("Zahlung an Verwertungsgesellschaft", "R-44"),
    "bewirtung": ("übliche Bewirtung", "R-48"),
    "ust": ("gesondert ausgewiesene Umsatzsteuer", "R-18"),
    "auslage_nachgewiesen": ("nachgewiesene Auslage oder Weiterberechnung", "A1"),
    # 14.10.2026: nicht kommerzieller Musikverein (Hobby-/Laienmusik, Liebhaberorchester) nach der
    # Generalklausel: Zahlungen an vereinseigene Chorleiter und Dirigenten bleiben außer Betracht,
    # bei der Schwelle und bei der Bemessungsgrundlage (R-57; KSK-Info 12, Abschn. 4, S. 3-4).
    # Die Rolle setzt nur app/zuordnung.py::musikverein_generalklausel, mit Beleg im Text.
    "vereinseigene_leitung": ("Zahlung an vereinseigenen Chorleiter oder Dirigenten (Musikverein, Generalklausel)", "R-57"),
}


def ausgeschlossene_positionen(positionen, jahr):
    """Positionen, die nicht zur Bemessungsgrundlage zählen, mit Grund und Regel (gleiche Logik wie summe_positionen)."""
    kein = werte("rechtsform.kein_entgelt", jahr)
    liste = []
    for p in positionen:
        if p.get("empfaenger") in kein:
            liste.append((_d(p["betrag"]), "Zahlung an Kapital-/Handelsgesellschaft", "R-138, R-216"))
        elif p.get("kuenstlerisch") is False:
            liste.append((_d(p["betrag"]), "keine künstlerische oder publizistische Leistung", None))
        elif p.get("art") in _AUSSCHLUSSGRUENDE:
            grund, regel = _AUSSCHLUSSGRUENDE[p["art"]]
            liste.append((_d(p["betrag"]), grund, regel))
    return liste


def _eur_de(x):
    """Betrag deutsch formatiert: 5.000,00"""
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _erklaere_ausschluesse(e, positionen, jahr):
    for betrag, grund, regel in ausgeschlossene_positionen(positionen, jahr):
        zusatz = f", {regel}" if regel else ""
        e.begruendung.append(f"Nicht zur Bemessungsgrundlage: {_eur_de(betrag)} € ({grund}{zusatz}).")
        if regel:
            e.regeln += [r.strip() for r in regel.split(",") if r.strip() not in e.regeln]
    return e


@_luecke
def pruefe_positionen(jahr, positionen, typischer_verwerter=False):
    if jahr_fehlt(jahr):
        return jahr_fehlt(jahr)
    summe = summe_positionen(positionen, jahr)
    e = pruefe_typischer_verwerter(jahr, summe) if typischer_verwerter else pruefe_eigenwerbung(jahr, summe)
    return _erklaere_ausschluesse(e, positionen, jahr)


@_luecke
def bemessung_positionen(jahr, positionen):
    e = pruefe_typischer_verwerter(jahr, summe_positionen(positionen, jahr))
    return _erklaere_ausschluesse(e, positionen, jahr)


@_luecke
def veranstaltungen(jahr, anzahl, summe, einnahmeabsicht=True, unternehmensart="generalklausel"):
    """Generalklausel (KSVG § 24 Abs. 2 S. 1 Nr. 2, S. 3 Nr. 1; R-14, R-132, R-149), nur Fassung B (ab 2023):
    bis zu drei Veranstaltungen: keine Abgabepflicht; mehr als drei UND Summe über Schwelle UND Einnahmeabsicht: abgabepflichtig.
    Die Drei-Veranstaltungen-Ausnahme gilt NICHT für typische Verwerter (§ 24 Abs. 1, dort keine Schwelle) und nicht für Eigenwerbung
    (dort zählt nur die Schwelle). unternehmensart: 'generalklausel' | 'typischer_verwerter' | 'eigenwerber'.
    Pruefkatalog-Befund M7: anzahl == 0 (keine Veranstaltungen, z. B. Nutzung durch Lizenzierung) bekommt eine EIGENE Pruefung
    (R-13, KSVG § 24 Abs. 2 S. 1 Nr. 2, S. 2: Einnahmeabsicht + Summe über der Schwelle) -- die Drei-Veranstaltungen-Ausnahme
    (R-14/R-132/R-149) gilt nur für Entgelte AUS Veranstaltungen, 0 Veranstaltungen ist kein Anwendungsfall davon."""
    if jahr_fehlt(jahr):
        return jahr_fehlt(jahr)
    if unternehmensart == "typischer_verwerter":
        e = pruefe_typischer_verwerter(jahr, summe)
        e.begruendung.append("Typischer Verwerter: Drei-Veranstaltungen-Ausnahme gilt nicht.")
        return e
    if unternehmensart == "eigenwerber":
        e = pruefe_eigenwerbung(jahr, summe)
        e.begruendung.append("Eigenwerbung: nur die Schwelle zählt, nicht die Zahl der Veranstaltungen.")
        return e
    s = schwelle(jahr)
    if s is None or s["fassung"] != "B":
        return Ergebnis(NICHT_ABGEDECKT, ["Nur Fassung B (ab 2023) umgesetzt."], regeln=["R-14", "R-132"])
    if (anzahl is not None and anzahl > 0
            and vergleich("veranstaltungen.ausnahme_max", jahr, D(anzahl), wert("veranstaltungen.ausnahme_max", jahr))):
        # 14.10.2026 (P-17): bis zu drei Veranstaltungen gilt die Generalklausel nicht -- unabhängig von der
        # Einnahmeabsicht (KSVG § 24 Abs. 2 S. 3 Nr. 1); früher wurde trotzdem nach ihr gefragt.
        e = Ergebnis(NICHT, regeln=["R-14", "R-132"], fundstellen=["KSVG § 24 Abs. 2 S. 1 Nr. 2, S. 2, S. 3 Nr. 1"])
        e.begruendung.append("Höchstens drei Veranstaltungen: keine Abgabepflicht in den Fällen der Generalklausel.")
        return e
    if anzahl is None or einnahmeabsicht is None:
        return Ergebnis(RUECKFRAGE, ["Anzahl der Veranstaltungen oder Einnahmeabsicht unbekannt."],
                        rueckfragen=["Wie viele Veranstaltungen im Kalenderjahr?", "Sollen mit der Nutzung Einnahmen erzielt werden?"],
                        regeln=["R-14", "R-132"])
    if anzahl == 0:
        e0 = Ergebnis(NICHT, regeln=["R-13"], fundstellen=["KSVG § 24 Abs. 2 S. 1 Nr. 2, S. 2"])
        if not einnahmeabsicht:
            e0.begruendung.append("Keine Einnahmeabsicht: Generalklausel greift nicht.")
            return e0
        if vergleich("schwelle.operator", jahr, _d(summe), D(s["euro"])):
            e0.klasse = ABGABEPFLICHTIG
            e0.bemessungsgrundlage = _d(summe)
            e0.begruendung.append(f"Keine Veranstaltung, aber Nutzung mit Einnahmeabsicht: Summe {summe} € übersteigt die Schwelle {s['euro']} € des Jahres {jahr}.")
            return _mit_abgabe(e0, jahr)
        e0.begruendung.append(f"Keine Veranstaltung: Summe {summe} € übersteigt die Schwelle {s['euro']} € des Jahres {jahr} nicht.")
        return e0
    e = Ergebnis(NICHT, regeln=["R-14", "R-132"], fundstellen=["KSVG § 24 Abs. 2 S. 1 Nr. 2, S. 2, S. 3 Nr. 1"])
    if not einnahmeabsicht:
        e.begruendung.append("Keine Einnahmeabsicht: Generalklausel greift nicht.")
        return e
    if vergleich("veranstaltungen.ausnahme_max", jahr, D(anzahl), wert("veranstaltungen.ausnahme_max", jahr)):
        e.begruendung.append("Höchstens drei Veranstaltungen: keine Abgabepflicht in den Fällen der Generalklausel.")
        return e
    if vergleich("schwelle.operator", jahr, _d(summe), D(s["euro"])):
        e.klasse = ABGABEPFLICHTIG; e.bemessungsgrundlage = _d(summe)
        e.begruendung.append("Mehr als drei Veranstaltungen und Summe über der Schwelle.")
        return _mit_abgabe(e, jahr)
    e.begruendung.append("Mehr als drei Veranstaltungen, aber Summe nicht über der Schwelle.")
    return e


def vorauszahlung_monatlich(jahr, bg_vorjahr):
    """KSVG § 27 Abs. 2, 3 (R-80, R-164): BG des Vorjahres ÷ 12 × Abgabesatz; bis 40 € keine Vorauszahlungspflicht."""
    r = abgabesatz(jahr)
    if r is None:
        return None, Ergebnis(NICHT_ABGEDECKT, ["Abgabesatz fehlt."])
    # Korpus-Lauf 15.10.2026 (Befund der Gegenrechnung): vorher erst / Monate, dann × Satz -- 14.000 € / 12 × 4,2 %
    # ergab 48,99999… statt genau 49,00 € und damit fälschlich 'Rundung ungeklärt'. Jetzt eine einzige Division am Ende:
    # exakt, wenn das Ergebnis abbricht.
    roh = _d(bg_vorjahr) * r / (wert("vorauszahlung.monate", jahr) * 100)
    e = Ergebnis(NICHT, regeln=["R-80", "R-164"], fundstellen=["KSVG § 27 Abs. 2, 3"])
    grenze = wert("vorauszahlung.untergrenze", jahr)
    if vergleich("vorauszahlung.untergrenze", jahr, roh, grenze):
        e.begruendung.append(f"Monatlich {roh.quantize(D('0.01'))} € ≤ {grenze} €: keine Vorauszahlungspflicht.")
        return None, e
    if roh != roh.quantize(D("0.01")):
        e.klasse = RUECKFRAGE; e.rueckfragen.append(f"Rundung ungeklärt (ungerundet {roh}).")
        return None, e
    e.klasse = ABGABEPFLICHTIG
    return roh.quantize(D("0.01")), e


def meldefrist(entgeltjahr):
    """KSVG § 27 Abs. 1 (R-79): bis 31. März des Folgejahres."""
    return datetime.date(entgeltjahr + 1, int(wert("meldefrist.monat", entgeltjahr)), int(wert("meldefrist.tag", entgeltjahr)))


def aufbewahrung_bis(faelligkeitsjahr):
    """KSVG § 28 S. 3 (R-83): fünf Jahre nach Ablauf des Kalenderjahres der Fälligkeit."""
    return datetime.date(faelligkeitsjahr + int(wert("aufbewahrung.jahre", faelligkeitsjahr)), 12, 31)


@_luecke
def saeumniszuschlag(rueckstaende, monate, jahr, gesondert_angefordert=False):
    """SGB IV § 24, KSVG § 30 (R-86, R-226): 1 % je angefangenen Monat auf den auf 50 € abgerundeten Rückstand.
    Bis 2022 wird vor der Abrundung addiert (BSG 07.07.2020); ab 2023 ist gesonderte Abrundung zulässig – welche Methode
    KSK/DRV anwenden, ist nicht belegt → Grenzfall."""
    rs = [_d(x) for x in (rueckstaende if isinstance(rueckstaende, (list, tuple)) else [rueckstaende])]
    gesamt = sum(rs, D(0))
    e = Ergebnis(ABGABEPFLICHTIG, regeln=["R-86", "R-226"], fundstellen=["SGB IV § 24 Abs. 1", "KSVG § 30 Abs. 1"])
    if gesondert_angefordert and vergleich("saeumnis.bagatell_gesondert", jahr, gesamt, wert("saeumnis.bagatell_gesondert", jahr)):
        e.klasse = NICHT; e.begruendung.append("Bei gesonderter Anforderung und Rückstand unter 150 € nicht zu erheben.")
        return e
    def zuschlag(basis):
        stufe = wert("saeumnis.stufe", jahr)
        return (basis // stufe * stufe) * wert("saeumnis.satz_prozent", jahr) / 100 * monate
    if len(rs) > 1:
        e.klasse = GRENZFALL
        add = zuschlag(gesamt)
        sep = sum((zuschlag(x) for x in rs), D(0))
        e.begruendung.append(f"Additionsmethode: {add} € gesamt; gesonderte Abrundung (ab 2023 zulässig): {sep} € gesamt.")
        e.abgabe = add if reg("saeumnis.addition_vor_abrundung", jahr)["wert"] == "ja" else None
        return e
    e.abgabe = zuschlag(gesamt)
    return e


def uebungsleiter_bg(jahr, betrag, art="uebungsleiter", bestaetigung=True, bereits_ausgeschoepft=0, bei_ueberschreitung="rechnen"):
    """Übungsleiter-/Ehrenamtspauschale (KSVG § 25 Abs. 2 S. 2 Nr. 2; R-50, R-51, R-202, R-203): nur der übersteigende Betrag
    zählt. Voraussetzung: schriftliche Bestätigung; Pauschale ist je Person nur einmal abziehbar. Ehrenamtspauschale ist erst ab 2025
    ausgenommen."""
    p = P["pauschale"].get(str(jahr))
    if not p:
        return None, Ergebnis(NICHT_ABGEDECKT, [f"Pauschale für {jahr} nicht im Regelwerk."])
    e = Ergebnis(ABGABEPFLICHTIG, regeln=["R-50", "R-51", "R-202", "R-203"], fundstellen=[p["fundstelle"]])
    if not bestaetigung:
        e.klasse = RUECKFRAGE; e.rueckfragen.append("Schriftliche Bestätigung über die Geltendmachung der Pauschale fehlt.")
        e.bemessungsgrundlage = _d(betrag); return e.bemessungsgrundlage, e
    if art == "ehrenamt":
        if not p["ehrenamt_ausgenommen"] or p["ehrenamt"] is None:
            e.bemessungsgrundlage = _d(betrag)
            e.begruendung.append("Ehrenamtspauschale ist vor 2025 nicht von der Bemessungsgrundlage ausgenommen.")
            return e.bemessungsgrundlage, _mit_abgabe(e, jahr)
        grenze = D(p["ehrenamt"])
    else:
        grenze = D(p["uebungsleiter"])
    frei = max(D(0), grenze - _d(bereits_ausgeschoepft))
    bg = max(D(0), _d(betrag) - frei)
    e.bemessungsgrundlage = bg
    if bg == 0:
        e.klasse = NICHT
        e.begruendung.append("Betrag liegt innerhalb der Pauschale.")
        return bg, e
    if bei_ueberschreitung == "rueckfrage":
        e.klasse = RUECKFRAGE
        e.bemessungsgrundlage = None
        e.abgabe = None
        e.rueckfragen.append("Die Pauschale ist überschritten. Der übersteigende Betrag wird nicht still berechnet.")
        return bg, e
    return bg, _mit_abgabe(e, jahr)


def kommission_bg(verkaufspreis, provision_oder_einbehalt):
    """KSVG § 25 Abs. 3 (R-109, R-110, R-167): Entgelt ist, was dem Künstler zusteht (Preis abzüglich Provision)."""
    return _d(verkaufspreis) - _d(provision_oder_einbehalt)


def schaetzung_ausland(bruttoeinnahmen, jahr):
    """Schätzgrundlage laut KSK-Praxis: 25 % der Bruttoeinnahmen (R-37, R-179); Kenntnis der echten Entgelte hat Vorrang."""
    return _d(bruttoeinnahmen) * wert("schaetzung.ausland_prozent", jahr) / 100


# ---------------------------------------------------------------------------------------------
# Rechnungsanalyse v0 (Entwurf): Positionen einer Rechnung, Einordnung durch Mensch oder Sprachmodell vorgegeben
# ---------------------------------------------------------------------------------------------
ROLLEN = {
    "an_kapitalgesellschaft": "Zahlung an GmbH/UG/AG im eigenen Namen: keine Zahlung an selbständige Künstler (R-138)",
    "nicht_kuenstlerisch": "Nicht künstlerische/publizistische Leistung oder Kostenweitergabe (kein Entgelt für ein Werk oder eine Leistung)",
    "vertretung_kuenstler": "Honorar im Namen und für Rechnung des Künstlers (Vertretung): Entgelt des Auftraggebers an den Künstler (R-33, R-36)",
    "eigengeschaeft_dritter": "Agentur beauftragt den Künstler im eigenen Namen: Prüfung, wer abgabepflichtig ist (R-78, R-36)",
    "reise_kuenstler": "Reisekosten des Künstlers: nur nachgewiesene Kosten sind ausgenommen (R-47, R-176)",
}


def analysiere_rechnung(jahr, positionen, empfaenger_abgabepflichtig=None, agentur_abgabepflichtig=None):
    """Bewertet je Position, was zur Bemessungsgrundlage des Rechnungsempfängers (Zahlers) gehört. Rolle je Position wird vorgegeben
    (Einordnung ist Aufgabe von Steuerberater/Sprachmodell + Rückfrage). Fehlende Angaben → Rückfrage, nie geraten.
    Position: {nr, text, betrag, rolle, belege?}. Ist der Empfänger nicht abgabepflichtig oder unbekannt, bleibt das Gesamtergebnis offen."""
    if jahr_fehlt(jahr):
        return jahr_fehlt(jahr), []
    zeilen, summe_sicher, summe_offen = [], D(0), D(0)
    rueck = []
    for p in positionen:
        b = _d(p["betrag"]); rolle = p["rolle"]; z = {"nr": p["nr"], "betrag": b, "rolle": rolle, "zaehlt": D(0), "offen": D(0), "hinweis": ROLLEN.get(rolle, "?")}
        if rolle == "vertretung_kuenstler":
            z["zaehlt"] = b
        elif rolle == "reise_kuenstler":
            if p.get("belege"):
                z["hinweis"] += " – Belege liegen vor: ausgenommen"
            else:
                z["offen"] = b; z["hinweis"] += " – Belege fehlen: Rückfrage; bis zur Klärung zählt der Betrag mit"
                rueck.append(f"Position {p['nr']}: Belege zu den Reisekosten anfordern.")
        elif rolle == "eigengeschaeft_dritter":
            if agentur_abgabepflichtig is True:
                z["hinweis"] += " – Agentur ist abgabepflichtig: die Agentur meldet ihre Zahlung an den Künstler, nicht der Rechnungsempfänger"
            else:
                z["offen"] = b; z["hinweis"] += " – Abgabestatus der Agentur unbekannt/nein: Rückfrage"
                rueck.append(f"Position {p['nr']}: Ist die Agentur selbst abgabepflichtig? Wie viel zahlt sie an den Künstler?")
        elif rolle == "klaeren" or rolle not in ROLLEN:
            # Teil 1e (15.10.2026, Befund der Gegenrechnung): eine Position OHNE oder mit unbekannter Einordnung zählte
            # vorher still mit 0 (kein Zweig griff), ohne Rückfrage -- gegen 'nie geraten' oben. Jetzt wie 'klaeren'.
            z["offen"] = b; z["hinweis"] = "Einordnung unklar: Rückfrage"
            rueck.append(f"Position {p['nr']}: {p.get('frage', 'Wer erbringt die Leistung, in welcher Rolle?')}")
        summe_sicher += z["zaehlt"]; summe_offen += z["offen"]; zeilen.append(z)
    e = Ergebnis(RUECKFRAGE if (rueck or empfaenger_abgabepflichtig is not True) else ABGABEPFLICHTIG, regeln=["R-138", "R-33", "R-36", "R-47", "R-78", "R-176"])
    if empfaenger_abgabepflichtig is not True:
        rueck.insert(0, "Ist der Rechnungsempfänger abgabepflichtig (Abgabenummer, Unternehmensart)?")
    e.rueckfragen = rueck
    e.bemessungsgrundlage = summe_sicher
    e.begruendung.append(f"Sicher zählend: {summe_sicher} €; offen (zählt bei ungünstiger Klärung mit): {summe_offen} €.")
    if empfaenger_abgabepflichtig is True:
        a, h = berechne_abgabe(summe_sicher, jahr)
        e.abgabe = a
        if h: e.rueckfragen.append(h)
    return e, zeilen


# ---------------------------------------------------------------------------------------------
# Sperre, Tätigkeitskatalog, Klärfälle (Suite v1). Keine Berechnung, wenn die Rechnung gesperrt ist.
# ---------------------------------------------------------------------------------------------
_SPERR_MUSTER = (
    ("sperre.summenabweichung", ("positionen ergeben", "gedruckte")),
    ("sperre.ust_inkonsistent", ("nicht konsistent", "ust")),
    ("sperre.positionsnummer", ("doppelte positionsnummer",)),
    ("sperre.rechnungsbetrag", ("rechnungsbetrag", "netto")),
    ("sperre.negative_summe", ("negative gesamtsumme",)),
    ("sperre.ust_satz", ("ust-satz", "ohne hinweis")),
    ("sperre.netto_fehlt", ("keine nett", "nur brutto")),
    ("sperre.doppelzahlung", ("doppelt erfasst",)),
)


@_luecke
def pruefe_sperre(text, jahr):
    """Summen- oder USt-Widerspruch: keine Klasse der Abgabe und keine Berechnung."""
    low = text.lower()
    for schluessel, teile in _SPERR_MUSTER:
        if schluessel == "sperre.rechnungsbetrag" and "≠" not in text and "!=" not in text:
            continue
        if all(teil in low for teil in teile):
            eintrag = reg(schluessel, jahr)
            return Ergebnis(
                SPERRE,
                [f"Sperre: {eintrag['fundstelle']}"],
                fundstellen=[eintrag["fundstelle"]],
                regeln=[eintrag["regel"]],
            )
    return None


@_luecke
def einordnung_taetigkeit(text, jahr):
    """Ohne Synonym im Tätigkeitsregister keine automatische Entscheidung."""
    low = text.lower()
    buchstaben = "abcdefghijklmnopqrstuvwxyzäöü"
    begriffe = werte("taetigkeit.synonym", jahr)
    for begriff in begriffe:
        b = begriff.lower()
        start = 0
        while True:
            i = low.find(b, start)
            if i < 0:
                break
            davor = low[i - 1] if i else " "
            danach = low[i + len(b)] if i + len(b) < len(low) else " "
            if davor not in buchstaben or danach not in buchstaben:
                return None
            start = i + 1
    return Ergebnis(
        NICHT_ABGEDECKT,
        ["Kein Eintrag im Tätigkeitsregister trifft den Text. Es wird nicht geraten."],
        regeln=["C4"],
    )


def pruefe_chorleitung(text, betrag, jahr):
    """Chorleiter-Ausnahme nur bei belegter regelmäßiger Leitung. Sonst Rückfrage oder normal zählen."""
    low = text.lower()
    if "chorleit" not in low:
        return None
    if "keine regelmäßige" in low or "gesonderte" in low:
        return None
    if "nicht belegt" in low or "nur eine probe" in low:
        return Ergebnis(
            RUECKFRAGE,
            ["Regelmäßigkeit der Chorleitung ist nicht belegt."],
            rueckfragen=["Ist die Chorleitung regelmäßig?"],
            regeln=["R-57"],
        )
    if "regelmäßig" in low:
        return pruefe_positionen(jahr, [{"betrag": betrag, "art": "vereinseigene_leitung"}])
    return None


def pruefe_klarstellung(text, betrag, jahr):
    """Fälle, die der Kern nicht still zuordnet: Währung, Jahresgrenze, Datum, Vertrag."""
    low = text.lower()
    if "chf" in low and "umrechnung" in low:
        return Ergebnis(RUECKFRAGE, ["Fremdwährung ohne Umrechnungsnachweis."], rueckfragen=["Wie wurde umgerechnet?"], regeln=["A3"])
    if "ohne sie nicht" in low and "offen" in low:
        return Ergebnis(RUECKFRAGE, ["Die Schwelle steht nur, wenn offene Positionen mitzählen."], regeln=["S3a"])
    if "satz nicht belegt" in low:
        return Ergebnis(NICHT_ABGEDECKT, ["Der Abgabesatz ist für diesen Fall nicht belegt."], regeln=["D3"])
    if "gutschrift" in low and len(re.findall(r"20\d\d", text)) > 1:
        return Ergebnis(RUECKFRAGE, ["Gutschrift und Rechnung liegen in verschiedenen Jahren."], rueckfragen=["Welchem Zahlungsjahr gehört die Gutschrift?"], regeln=["A4"])
    if "auftrag erteilt" in low and "leistung" in low and "rechnung" in low and "zahlung" not in low:
        return jahr_fehlt(jahr) or Ergebnis(RUECKFRAGE, ["Zahlungsdatum fehlt."], rueckfragen=["Wann wurde gezahlt?"], regeln=["R-41"])
    if "rechnungsdatum" in low and "zahlung" in low and len(set(re.findall(r"20\d\d", text))) > 1:
        return Ergebnis(RUECKFRAGE, ["Rechnungsjahr und Zahlungsjahr fallen auseinander."], rueckfragen=["Welches Jahr ist das Zahlungsjahr?"], regeln=["D4"])
    if "privat" in low and ("hochzeit" in low or "kein vereinsbezug" in low):
        return Ergebnis(RUECKFRAGE, ["Privater Zweck ist nicht als Auftrag des Vereins belegt."], rueckfragen=["Wozu wurde beauftragt?"], regeln=["R-40"])
    if "eigenen namen" in low or "eigengeschäft" in low or "eigengeschaeft" in low:
        return vertreter()
    if "drittzahlung" in low and "abgabepflichtig" in low:
        return vertreter()
    if betrag < 0:
        return Ergebnis(RUECKFRAGE, ["Negativer Betrag ohne eindeutiges Zahlungsjahr."], regeln=["A4"])
    return None
