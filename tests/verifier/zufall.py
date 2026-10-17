"""Zufallsfälle für die Gegenrechnung (Teil 1e, Abschnitte D.1 und E.1). Fester Startwert, also reproduzierbar.

Erzeugt Aufrufe (Name, args, kwargs) für jede Rechenart des Kerns: Jahre rund um 2019 bis 2027 (auch Jahre ohne
Registerzeile und 'kein Jahr'), Beträge von 0 bis 99.999.999.999,99, Werte genau an den Grenzen (Schwelle,
Untergrenze, Stunden), alle Anfragearten. Nur erfundene Testdaten."""
from __future__ import annotations

import random
from decimal import Decimal

from kern import rechnen as K

GROESSTER_BETRAG = Decimal("99999999999.99")
ARTEN = [None, "honorar", "ust", "verwertungsgesellschaft", "gewinnzuweisung", "fahrtkosten_nachgewiesen", "bewirtung",
         "vervielfaeltigung_nachtraeglich", "vereinseigene_leitung", "fahrtkosten", "unbekannte_art"]
EMPFAENGER = [None, None, None, "gmbh", "kg", "ohg", "ug", "ag", "gbr", "natuerliche_person"]
ROLLEN = [None, "vertretung_kuenstler", "reise_kuenstler", "eigengeschaeft_dritter", "klaeren", "an_kapitalgesellschaft",
          "nicht_kuenstlerisch", "unbekannte_rolle"]
SCHLUESSEL = sorted({z["schluessel"] for z in K.P["register"]})
ZAHL_SCHLUESSEL = sorted({z["schluessel"] for z in K.P["register"] if z["wert"].replace(".", "", 1).isdigit()})


def _grenzwerte() -> list[Decimal]:
    werte = {Decimal(s["euro"]) for s in K.P["schwelle"].values() if s.get("euro")}
    werte |= {Decimal(z["wert"]) for z in K.P["register"] if z["wert"].replace(".", "", 1).isdigit()}
    werte |= {Decimal(p["uebungsleiter"]) for p in K.P["pauschale"].values()}
    return sorted(werte)


GRENZEN = _grenzwerte()


def betrag(rng: random.Random) -> Decimal:
    art = rng.random()
    if art < 0.25:
        g = rng.choice(GRENZEN)
        return max(Decimal(0), g + rng.choice([Decimal("-0.01"), Decimal(0), Decimal("0.01"), Decimal(1)]))
    if art < 0.6:
        return Decimal(rng.randint(0, 300000)) / 100
    if art < 0.8:
        return Decimal(rng.randint(0, 5000))
    if art < 0.95:
        return Decimal(rng.randint(0, 10 ** 9)) / 100
    return rng.choice([GROESSTER_BETRAG, GROESSTER_BETRAG - Decimal("0.01"), Decimal(rng.randint(0, 10 ** 13)) / 100])


def jahr(rng: random.Random, ohne: bool = True):
    r = rng.random()
    if ohne and r < 0.03:
        return None
    if r < 0.1:
        return rng.choice([2013, 2014, 2015, 2016, 2017, 2018, 2028, 2030])
    return rng.randint(2019, 2027)


def positionen(rng: random.Random, n: int | None = None) -> list[dict]:
    liste = []
    for _ in range(rng.randint(0, 8) if n is None else n):
        p: dict = {"betrag": betrag(rng)}
        if rng.random() < 0.5:
            p["art"] = rng.choice(ARTEN)
        e = rng.choice(EMPFAENGER)
        if e:
            p["empfaenger"] = e
        if rng.random() < 0.3:
            p["kuenstlerisch"] = rng.choice([True, False])
        liste.append(p)
    return liste


def rechnungspositionen(rng: random.Random) -> list[dict]:
    return [{"nr": i + 1, "text": f"Position {i + 1}", "betrag": betrag(rng), "rolle": rng.choice(ROLLEN),
             "belege": rng.choice([True, False, None])} for i in range(rng.randint(0, 6))]


def stunden(rng: random.Random) -> Decimal:
    return rng.choice([Decimal(8), Decimal("8.01"), Decimal("7.99"), Decimal(24), Decimal("23.99"), Decimal(0),
                       Decimal(rng.randint(0, 3000)) / 100])


def aufruf(rng: random.Random, name: str) -> tuple[list, dict]:
    j = jahr(rng)
    b = betrag
    if name == "pruefe_positionen":
        return [j, positionen(rng)], {"typischer_verwerter": rng.choice([True, False])}
    if name == "summe_positionen":
        return [positionen(rng), jahr(rng, ohne=False)], {}
    if name == "bemessung_positionen":
        return [jahr(rng, ohne=False), positionen(rng)], {}
    if name == "pruefe_eigenwerbung":
        return [j, b(rng)], {}
    if name == "pruefe_typischer_verwerter":
        return [j, b(rng)], {}
    if name == "veranstaltungen":
        return [j, rng.choice([None, 0, 1, 2, 3, 4, 5, 10]), b(rng), rng.choice([True, False, None]),
                rng.choice(["generalklausel", "typischer_verwerter", "eigenwerber", None])], {}
    if name == "vorauszahlung_monatlich":
        return [jahr(rng, ohne=False), b(rng)], {}
    if name == "saeumniszuschlag":
        rueck = b(rng) if rng.random() < 0.5 else [b(rng) for _ in range(rng.randint(1, 4))]
        return [rueck, rng.randint(1, 24), jahr(rng, ohne=False), rng.choice([True, False])], {}
    if name == "verpflegung":
        return [jahr(rng, ohne=False), stunden(rng), rng.choice([True, False]), b(rng), rng.random() < 0.9], {}
    if name == "uebungsleiter_bg":
        return [jahr(rng, ohne=False), b(rng), rng.choice(["uebungsleiter", "ehrenamt"]), rng.random() < 0.85,
                rng.choice([Decimal(0), b(rng)])], {}
    if name == "kommission_bg":
        return [b(rng), b(rng)], {}
    if name == "schaetzung_ausland":
        return [b(rng), jahr(rng, ohne=False)], {}
    if name == "netto":
        return [b(rng), b(rng)], {}
    if name == "restbetrag":
        return [b(rng), [b(rng) for _ in range(rng.randint(0, 4))]], {}
    if name == "berechne_abgabe":
        return [b(rng), jahr(rng, ohne=False)], {}
    if name == "analysiere_rechnung":
        return [j, rechnungspositionen(rng), rng.choice([True, False, None]), rng.choice([True, False, None])], {}
    if name in ("abgabesatz", "schwelle"):
        return [jahr(rng, ohne=False)], {}
    if name in ("meldefrist", "aufbewahrung_bis"):
        return [rng.randint(2013, 2030)], {}
    if name == "wert":
        return [rng.choice(ZAHL_SCHLUESSEL), jahr(rng, ohne=False)], {}
    if name == "reg":
        return [rng.choice(SCHLUESSEL), jahr(rng, ohne=False)], {}
    if name == "vertreter":
        return [rng.choice([True, False, None]), rng.choice([True, False, None])], {}
    if name in ("privater_auftraggeber", "nachweismakler"):
        return [], {}
    raise KeyError(name)


NAMEN = ["pruefe_positionen", "summe_positionen", "bemessung_positionen", "pruefe_eigenwerbung",
         "pruefe_typischer_verwerter", "veranstaltungen", "vorauszahlung_monatlich", "saeumniszuschlag", "verpflegung",
         "uebungsleiter_bg", "kommission_bg", "schaetzung_ausland", "netto", "restbetrag", "berechne_abgabe",
         "analysiere_rechnung", "abgabesatz", "schwelle", "meldefrist", "aufbewahrung_bis", "wert", "reg", "vertreter",
         "privater_auftraggeber", "nachweismakler"]


def faelle(anzahl: int, startwert: int) -> list[tuple[str, list, dict]]:
    rng = random.Random(startwert)
    return [(NAMEN[i % len(NAMEN)], *aufruf(rng, NAMEN[i % len(NAMEN)])) for i in range(anzahl)]
