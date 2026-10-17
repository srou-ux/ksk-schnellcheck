"""Gegenrechnung: jede Rechenart des Kerns, eigenständig aus den Regeltexten (Blatt 'Regeln') und dem Regelregister.

Entwurf – vom Steuerberater zu prüfen. Kein Import von `kern`. Exakte Brüche (Fraction), keine Gleitkommazahlen.

Rückgabe jeder Funktion: ein Wörterbuch mit festen Schlüsseln (die gleiche Form erzeugt app/gegenrechnung.py aus dem
Kernergebnis). Klassen als Kürzel: ABG (abgabepflichtig), NICHT, GRENZ (Grenzfall), RUECK (Rückfrage), LUECKE (nicht
abgedeckt). Beträge als Fraction oder None ('keine Zahl').

Die Aufrufnamen und Parameter entsprechen der Schnittstelle des Kerns (kern/rechnen.py), damit derselbe Aufruf zweimal
gerechnet werden kann. Der Rechenweg ist eigener Code."""
from __future__ import annotations

import datetime
import math
from fractions import Fraction

from verifier.register import Luecke, Register, bruch

ABG, NICHT, GRENZ, RUECK, LUECKE = "ABG", "NICHT", "GRENZ", "RUECK", "LUECKE"
HUNDERT = 100
CENT = Fraction(1, HUNDERT)


def _b(x) -> Fraction:
    """Eingabebetrag exakt als Bruch (Text, Zahl oder schon Bruch)."""
    return x if isinstance(x, Fraction) else bruch(x)


def _auf_cent(x: Fraction) -> bool:
    """Hat der Betrag höchstens zwei Nachkommastellen? (Grundregel 7: sonst keine Zahl, Rundung ungeklärt.)"""
    return (x * HUNDERT).denominator == 1


def _ergebnis(klasse: str, bg=None, abgabe=None) -> dict:
    return {"klasse": klasse, "bg": bg, "abgabe": abgabe}


def _abgabe(reg: Register, bg: Fraction, jahr):
    """Abgabe = Bemessungsgrundlage × Abgabesatz des Jahres / 100 (KSVG § 26, Blatt 'Abgabesätze').
    Kein Satz im Register oder mehr als zwei Nachkommastellen: keine Zahl (Rundung ist ungeklärt)."""
    satz = reg.abgabesatz(jahr)
    if satz is None:
        return None
    roh = bg * satz / HUNDERT
    return roh if _auf_cent(roh) else None


# ---------------------------------------------------------------------------------------------------------------------
# Entgelte: was zählt (R-41 alles; Ausnahmen R-18, R-44, R-46, R-47, R-48, R-49/R-176, R-57, R-138, R-216, R-217)
# ---------------------------------------------------------------------------------------------------------------------
# Arten (Vokabular der Fakten, app/schema.py), die nach dem Regeltext NICHT zur Bemessungsgrundlage gehören.
NICHT_ZAEHLENDE_ARTEN = {
    "ust": "R-18",                               # gesondert ausgewiesene Umsatzsteuer
    "verwertungsgesellschaft": "R-44",           # Zahlung an eine Verwertungsgesellschaft
    "gewinnzuweisung": "R-46",                   # Gewinnzuweisung an Gesellschafter
    "fahrtkosten_nachgewiesen": "R-47",          # erstattete, nachgewiesene Reisekosten
    "bewirtung": "R-48",                         # übliche Bewirtung
    "vervielfaeltigung_nachtraeglich": "R-49",   # nachträgliche Vervielfältigung, gesondert ausgewiesen
    "vereinseigene_leitung": "R-57",             # vereinseigener Chorleiter/Dirigent (Generalklausel)
}


def _zaehlt(p: dict, kein_entgelt: set[str]) -> bool:
    if p.get("empfaenger") in kein_entgelt:       # R-138, R-216, R-217: keine natürliche Person
        return False
    if p.get("kuenstlerisch") is False:           # keine künstlerische/publizistische Leistung
        return False
    return p.get("art") not in NICHT_ZAEHLENDE_ARTEN


def _summe(reg: Register, positionen, jahr) -> Fraction:
    kein = reg.liste("rechtsform.kein_entgelt", jahr)
    return sum((_b(p["betrag"]) for p in positionen if _zaehlt(p, kein)), Fraction(0))


def summe_positionen(reg: Register, positionen, jahr):
    return {"zahl": _summe(reg, positionen, jahr)}


# ---------------------------------------------------------------------------------------------------------------------
# Abgabepflicht dem Grunde nach und Bemessungsgrundlage
# ---------------------------------------------------------------------------------------------------------------------
def _eigenwerbung(reg: Register, jahr, summe: Fraction) -> dict:
    """R-10 (Fassung A, bis 31.12.2022): Summe nicht über der Grenze: keine Pflicht; darüber Grenzfall (Regelmäßigkeit
    'nicht nur gelegentlich' muss der Steuerberater prüfen). R-11/R-24 (Fassung B): Summe übersteigt die Schwelle:
    abgabepflichtig, sonst nicht. 'Übersteigt' = Operator der Registerzeile 'schwelle.operator'."""
    if jahr is None:
        return _ergebnis(RUECK)
    s = reg.schwelle(jahr)
    if s is None:
        return _ergebnis(LUECKE)
    if s["fassung"] == "A":
        return _ergebnis(GRENZ if reg.gilt("schwelle.operator", jahr, summe, s["euro"]) else NICHT)
    if reg.gilt("schwelle.operator", jahr, summe, s["euro"]):
        return _ergebnis(ABG, summe, _abgabe(reg, summe, jahr))
    return _ergebnis(NICHT)


def _typischer_verwerter(reg: Register, jahr, entgelte: Fraction) -> dict:
    """R-07 ff. (KSVG § 24 Abs. 1): dem Grunde nach abgabepflichtig, keine Schwelle."""
    return _ergebnis(ABG, entgelte, _abgabe(reg, entgelte, jahr))


def pruefe_eigenwerbung(reg: Register, jahr, summe):
    return _eigenwerbung(reg, jahr, _b(summe))


def pruefe_typischer_verwerter(reg: Register, jahr, entgelte):
    return _typischer_verwerter(reg, jahr, _b(entgelte))


def pruefe_positionen(reg: Register, jahr, positionen, typischer_verwerter=False):
    if jahr is None:
        return _ergebnis(RUECK)
    try:
        summe = _summe(reg, positionen, jahr)
    except Luecke:
        return _ergebnis(LUECKE)
    return _typischer_verwerter(reg, jahr, summe) if typischer_verwerter else _eigenwerbung(reg, jahr, summe)


def bemessung_positionen(reg: Register, jahr, positionen):
    try:
        return _typischer_verwerter(reg, jahr, _summe(reg, positionen, jahr))
    except Luecke:
        return _ergebnis(LUECKE)


def veranstaltungen(reg: Register, jahr, anzahl, summe, einnahmeabsicht=True, unternehmensart="generalklausel"):
    """Generalklausel KSVG § 24 Abs. 2 S. 1 Nr. 2, S. 3 Nr. 1 (R-13, R-14, R-132), nur Fassung B:
    - typischer Verwerter: keine Drei-Veranstaltungen-Ausnahme, keine Schwelle;
    - Eigenwerber: nur die Schwelle;
    - 1 bis 'veranstaltungen.ausnahme_max' Veranstaltungen: nur gelegentlich, keine Pflicht (R-14);
    - Zahl oder Einnahmeabsicht unbekannt: Rückfrage;
    - ohne Einnahmeabsicht: keine Pflicht;
    - sonst (keine Veranstaltung = Nutzung nach R-13, oder mehr als die Ausnahme nach R-132): Summe übersteigt die
      Schwelle -> abgabepflichtig."""
    if jahr is None:
        return _ergebnis(RUECK)
    summe = _b(summe)
    if unternehmensart == "typischer_verwerter":
        return _typischer_verwerter(reg, jahr, summe)
    if unternehmensart == "eigenwerber":
        return _eigenwerbung(reg, jahr, summe)
    s = reg.schwelle(jahr)
    if s is None or s["fassung"] != "B":
        return _ergebnis(LUECKE)
    try:
        if anzahl is not None and anzahl > 0 and reg.gilt(
                "veranstaltungen.ausnahme_max", jahr, Fraction(anzahl), reg.zahl("veranstaltungen.ausnahme_max", jahr)):
            return _ergebnis(NICHT)
    except Luecke:
        return _ergebnis(LUECKE)
    if anzahl is None or einnahmeabsicht is None:
        return _ergebnis(RUECK)
    if not einnahmeabsicht:
        return _ergebnis(NICHT)
    if reg.gilt("schwelle.operator", jahr, summe, s["euro"]):
        return _ergebnis(ABG, summe, _abgabe(reg, summe, jahr))
    return _ergebnis(NICHT)


def privater_auftraggeber(reg: Register):
    """R-40, R-133: Privatperson als Auftraggeber -- nicht abgabepflichtig, ohne Betrag."""
    return {"klasse": NICHT}


def nachweismakler(reg: Register):
    """R-35: nur Benennung der Vertragsparteien -- dem Grunde nach pflichtig, aber keine Abgabe auf Entgelte:
    Grenzfall, weil jede weitere Mitwirkung das ändert."""
    return {"klasse": GRENZ}


def vertreter(reg: Register, abgabestatus_dritter=None, vertrag_im_namen_des_kuenstlers=None):
    """R-33, R-78, KSVG § 25 Abs. 3: unbekannt -> Rückfrage; Vertretung und Dritter pflichtig -> der Dritte zahlt
    (für den Vertreter: nicht abgabepflichtig); Vertretung, Dritter nicht pflichtig -> Vertreter; Eigengeschäft ->
    Agentur."""
    if abgabestatus_dritter is None or vertrag_im_namen_des_kuenstlers is None:
        return {"klasse": RUECK}
    if vertrag_im_namen_des_kuenstlers and abgabestatus_dritter:
        return {"klasse": NICHT}
    return {"klasse": ABG}


# ---------------------------------------------------------------------------------------------------------------------
# Einzelne Beträge
# ---------------------------------------------------------------------------------------------------------------------
def berechne_abgabe(reg: Register, bemessung, jahr):
    return {"abgabe": _abgabe(reg, _b(bemessung), jahr)}


def netto(reg: Register, betrag, ust_gesondert_ausgewiesen=0):
    """R-18: abzüglich gesondert ausgewiesener Umsatzsteuer."""
    return {"zahl": _b(betrag) - _b(ust_gesondert_ausgewiesen)}


def restbetrag(reg: Register, gesamt, teile):
    """Rechnungsbetrag minus die darin genannten Teilbeträge."""
    return {"zahl": _b(gesamt) - sum((_b(t) for t in teile), Fraction(0))}


def nicht_zur_bemessungsgrundlage(reg: Register, genannte_betraege, summe_entgelte):
    """Anzeige 'Davon nicht zur Bemessungsgrundlage' (Router): genannte Beträge minus Summe der Entgelte."""
    return {"zahl": sum((_b(x) for x in genannte_betraege), Fraction(0)) - _b(summe_entgelte)}


def kommission_bg(reg: Register, verkaufspreis, provision_oder_einbehalt):
    """R-109, R-110: Entgelt ist, was dem Künstler zusteht (Verkaufspreis abzüglich Provision)."""
    return {"zahl": _b(verkaufspreis) - _b(provision_oder_einbehalt)}


def schaetzung_ausland(reg: Register, bruttoeinnahmen, jahr):
    """R-37, R-179: Schätzgrundlage laut KSK-Praxis, Prozentsatz aus dem Register."""
    return {"zahl": _b(bruttoeinnahmen) * reg.zahl("schaetzung.ausland_prozent", jahr) / HUNDERT}


def vorauszahlung_monatlich(reg: Register, jahr, bg_vorjahr):
    """R-80, R-164 (KSVG § 27 Abs. 2, 3): Bemessungsgrundlage des Vorjahres / Monate × Abgabesatz. Bis zur
    Untergrenze (Register, Operator der Zeile) keine Vorauszahlung. Mehr als zwei Nachkommastellen: keine Zahl."""
    satz = reg.abgabesatz(jahr)
    if satz is None:
        return {"betrag": None, "klasse": LUECKE}
    monatlich = _b(bg_vorjahr) / reg.zahl("vorauszahlung.monate", jahr) * satz / HUNDERT
    if reg.gilt("vorauszahlung.untergrenze", jahr, monatlich, reg.zahl("vorauszahlung.untergrenze", jahr)):
        return {"betrag": None, "klasse": NICHT}
    if not _auf_cent(monatlich):
        return {"betrag": None, "klasse": RUECK}
    return {"betrag": monatlich, "klasse": ABG}


def saeumniszuschlag(reg: Register, rueckstaende, monate, jahr, gesondert_angefordert=False):
    """R-86, R-226 (SGB IV § 24 Abs. 1, KSVG § 30): Satz je angefangenen Monat auf den nach unten auf die Stufe
    abgerundeten Rückstand. Gesondert angefordert und Rückstand unter der Bagatellgrenze: nicht zu erheben.
    Mehrere Rückstände: immer Grenzfall (Testfälle L-10, L-11, L-16 der Testfall-Excel, Entwurf). Bis 2022 (Register
    'saeumnis.addition_vor_abrundung' = ja) wird vor der Abrundung addiert (BSG 07.07.2020, R-226); das Urteil betrifft
    Gesamtsozialversicherungsbeiträge, die Übertragung auf die Künstlersozialabgabe ist eine Ableitung -> Grenzfall
    mit dem Vorschlag nach der Additionsmethode. Ab 2023 ist auch die gesonderte Abrundung zulässig; welche Methode
    KSK/DRV anwenden, ist nicht belegt -> Grenzfall ohne Zahl."""
    liste = rueckstaende if isinstance(rueckstaende, (list, tuple)) else [rueckstaende]
    try:
        betraege = [_b(x) for x in liste]
        gesamt = sum(betraege, Fraction(0))
        if gesondert_angefordert and reg.gilt("saeumnis.bagatell_gesondert", jahr, gesamt,
                                              reg.zahl("saeumnis.bagatell_gesondert", jahr)):
            return {"klasse": NICHT, "abgabe": None}
        stufe = reg.zahl("saeumnis.stufe", jahr)
        satz = reg.zahl("saeumnis.satz_prozent", jahr)

        def zuschlag(basis: Fraction) -> Fraction:
            return math.floor(basis / stufe) * stufe * satz / HUNDERT * _b(monate)

        if len(betraege) > 1:
            vorschlag = zuschlag(gesamt) if reg.text("saeumnis.addition_vor_abrundung", jahr) == "ja" else None
            return {"klasse": GRENZ, "abgabe": vorschlag}
        return {"klasse": ABG, "abgabe": zuschlag(gesamt)}
    except Luecke:
        return {"klasse": LUECKE, "abgabe": None}


def verpflegung(reg: Register, jahr, stunden, uebernachtung=False, erstattung=0, inland=True):
    """R-236, R-47 (EStG § 9 Abs. 4a S. 3): nur Inlandsreisen. Mindestens 'stunden_ganztag' Stunden: große Pauschale;
    An-/Abreisetag mit Übernachtung oder mehr als 'stunden_grenze' Stunden: kleine Pauschale; sonst keine.
    Genau an der Grenze, die das Gesetz ausschließt ('mehr als'), schreibt die KSK-Info 10 '8 bis 24': Grenzfall.
    Nicht zur Bemessungsgrundlage zählt die Erstattung bis zur Pauschale."""
    erstattung, stunden = _b(erstattung), _b(stunden)
    if not inland:
        return {"nicht_zaehlend": Fraction(0), "klasse": LUECKE}
    try:
        klein = reg.zahl("verpflegung.pauschale_klein", jahr)
        gross = reg.zahl("verpflegung.pauschale_gross", jahr)
    except Luecke:
        return {"nicht_zaehlend": Fraction(0), "klasse": LUECKE}
    ganztag = reg.zahl("verpflegung.stunden_ganztag", jahr)
    grenze = reg.zahl("verpflegung.stunden_grenze", jahr)
    klasse = ABG
    if reg.gilt("verpflegung.stunden_ganztag", jahr, stunden, ganztag):
        pauschale = gross
    elif uebernachtung or reg.gilt("verpflegung.stunden_grenze", jahr, stunden, grenze):
        pauschale = klein
    else:
        pauschale = Fraction(0)
        if stunden == grenze and reg.operator("verpflegung.stunden_grenze", jahr) == ">":
            klasse = GRENZ
    return {"nicht_zaehlend": min(erstattung, pauschale), "klasse": klasse}


def uebungsleiter_bg(reg: Register, jahr, betrag, art="uebungsleiter", bestaetigung=True, bereits_ausgeschoepft=0):
    """R-50, R-51, R-202, R-203 (KSVG § 25 Abs. 2 S. 2 Nr. 2): nur der Betrag über der Pauschale zählt; die Pauschale
    gilt je Person einmal (bereits ausgeschöpfter Teil wird abgezogen). Ohne schriftliche Bestätigung: Rückfrage, der
    ganze Betrag zählt bis zur Klärung. Ehrenamtspauschale erst ab dem Jahr, für das die Excel 'ausgenommen' führt."""
    p = reg.pauschale(jahr)
    if not p:
        return {"bg_rueck": None, "klasse": LUECKE, "bg": None, "abgabe": None}
    betrag = _b(betrag)
    if not bestaetigung:
        return {"bg_rueck": betrag, "klasse": RUECK, "bg": betrag, "abgabe": None}
    if art == "ehrenamt":
        if not p["ehrenamt_ausgenommen"] or p["ehrenamt"] is None:
            return {"bg_rueck": betrag, "klasse": ABG, "bg": betrag, "abgabe": _abgabe(reg, betrag, jahr)}
        frei_gesamt = bruch(p["ehrenamt"])
    else:
        frei_gesamt = bruch(p["uebungsleiter"])
    frei = max(Fraction(0), frei_gesamt - _b(bereits_ausgeschoepft))
    bg = max(Fraction(0), betrag - frei)
    if bg == 0:
        return {"bg_rueck": bg, "klasse": NICHT, "bg": bg, "abgabe": None}
    return {"bg_rueck": bg, "klasse": ABG, "bg": bg, "abgabe": _abgabe(reg, bg, jahr)}


# ---------------------------------------------------------------------------------------------------------------------
# Rechnungsanalyse (Rolle je Position vorgegeben; R-33, R-36, R-47, R-78, R-138, R-176)
# ---------------------------------------------------------------------------------------------------------------------
SICHER_ZAEHLEND = {"vertretung_kuenstler"}                       # R-33, R-36
SICHER_NICHT = {"an_kapitalgesellschaft", "nicht_kuenstlerisch"}  # R-138; keine künstlerische Leistung


def analysiere_rechnung(reg: Register, jahr, positionen, empfaenger_abgabepflichtig=None, agentur_abgabepflichtig=None):
    """Je Position: sicher zählend, sicher nicht zählend oder offen (Rückfrage). Offen sind: Reisekosten ohne Belege
    (R-47, R-176), Eigengeschäft einer Agentur, deren Abgabepflicht nicht feststeht (R-78), und jede Position, deren
    Einordnung fehlt oder unbekannt ist ('nie geraten'). Abgabepflichtig nur, wenn der Empfänger es ist und nichts offen
    bleibt; die Abgabe wird gerechnet, sobald der Empfänger abgabepflichtig ist."""
    if jahr is None:
        return {"klasse": RUECK, "bg": None, "abgabe": None, "offen": Fraction(0)}
    sicher, offen, rueckfrage = Fraction(0), Fraction(0), False
    for p in positionen:
        b, rolle = _b(p["betrag"]), p.get("rolle")
        if rolle in SICHER_ZAEHLEND:
            sicher += b
        elif rolle in SICHER_NICHT:
            continue
        elif rolle == "reise_kuenstler" and p.get("belege"):
            continue
        elif rolle == "eigengeschaeft_dritter" and agentur_abgabepflichtig is True:
            continue
        else:
            offen += b
            rueckfrage = True
    klasse = ABG if (empfaenger_abgabepflichtig is True and not rueckfrage) else RUECK
    abgabe = _abgabe(reg, sicher, jahr) if empfaenger_abgabepflichtig is True else None
    return {"klasse": klasse, "bg": sicher, "abgabe": abgabe, "offen": offen}


# ---------------------------------------------------------------------------------------------------------------------
# Auskünfte aus dem Register
# ---------------------------------------------------------------------------------------------------------------------
def abgabesatz(reg: Register, jahr):
    return {"zahl": reg.abgabesatz(jahr)}


def schwelle(reg: Register, jahr):
    s = reg.schwelle(jahr)
    return {"euro": s["euro"] if s else None, "fassung": s["fassung"] if s else None}


def meldefrist(reg: Register, entgeltjahr):
    """R-79 (KSVG § 27 Abs. 1): Tag und Monat aus dem Register, im Folgejahr."""
    monat = int(reg.zahl("meldefrist.monat", entgeltjahr))
    tag = int(reg.zahl("meldefrist.tag", entgeltjahr))
    return {"datum": datetime.date(entgeltjahr + 1, monat, tag).isoformat()}


def aufbewahrung_bis(reg: Register, faelligkeitsjahr):
    """R-83 (KSVG § 28 S. 3): Jahre nach Ablauf des Kalenderjahres der Fälligkeit, Ende des Jahres."""
    jahre = int(reg.zahl("aufbewahrung.jahre", faelligkeitsjahr))
    return {"datum": datetime.date(faelligkeitsjahr + jahre, 12, 31).isoformat()}


def wert(reg: Register, schluessel, jahr):
    return {"zahl": reg.zahl(schluessel, jahr)}


def reg_zeile(reg: Register, schluessel, jahr):
    z = reg.zeile(schluessel, jahr)
    return {"wert": str(z["wert"]), "operator": z["operator"]}


AUFRUFE = {
    "summe_positionen": summe_positionen,
    "pruefe_eigenwerbung": pruefe_eigenwerbung,
    "pruefe_typischer_verwerter": pruefe_typischer_verwerter,
    "pruefe_positionen": pruefe_positionen,
    "bemessung_positionen": bemessung_positionen,
    "veranstaltungen": veranstaltungen,
    "privater_auftraggeber": privater_auftraggeber,
    "nachweismakler": nachweismakler,
    "vertreter": vertreter,
    "berechne_abgabe": berechne_abgabe,
    "netto": netto,
    "restbetrag": restbetrag,
    "kommission_bg": kommission_bg,
    "nicht_zur_bemessungsgrundlage": nicht_zur_bemessungsgrundlage,
    "schaetzung_ausland": schaetzung_ausland,
    "vorauszahlung_monatlich": vorauszahlung_monatlich,
    "saeumniszuschlag": saeumniszuschlag,
    "verpflegung": verpflegung,
    "uebungsleiter_bg": uebungsleiter_bg,
    "analysiere_rechnung": analysiere_rechnung,
    "abgabesatz": abgabesatz,
    "schwelle": schwelle,
    "meldefrist": meldefrist,
    "aufbewahrung_bis": aufbewahrung_bis,
    "wert": wert,
    "reg": reg_zeile,
}


def rechne(reg: Register, name: str, args: list, kwargs: dict) -> dict:
    """Ein Aufruf. Fehlende Registerzeile -> LUECKE (wie 'Nicht abgedeckt')."""
    try:
        return AUFRUFE[name](reg, *args, **kwargs)
    except Luecke:
        return {"klasse": LUECKE}
