"""Prüfung des Regelregisters vor einer Freigabe (Teil 1e, C.2). Läuft im eigenen Prozess (verifier/lauf.py, Art
'register'); gestartet von `python -m verifier.pruefe_register`.

Geprüft wird nur die FORM, nicht die fachliche Richtigkeit:
- Abgabesätze, Schwellen, Pauschalen: jedes Jahr vom ersten Prüfjahr bis zum höchsten Jahr der Tabelle lückenlos,
  jede Zeile mit Fundstelle.
- Regelregister: je Schlüssel jedes Jahr ab seiner ersten Zeile (frühestens ab dem ersten Prüfjahr; ein späterer
  Beginn ist ein Hinweis) bis zum höchsten genannten Jahr belegt (offenes Ende gilt), keine Überschneidung zweier Zeilen mit verschiedenem Wert (Ausnahme: Listen wie rechtsform.kein_entgelt, dort
  je Wert), jede Zeile mit Fundstelle und Status, Operator gültig.
- Jeder Zahlenwert in der Spanne aus verifier/plausibilitaet.json, jeder Textwert in der erlaubten Liste.
Rückgabe: Liste von Befunden (Art 'FEHLER' oder 'HINWEIS', Text)."""
from __future__ import annotations

from fractions import Fraction

LISTEN_SCHLUESSEL = {"rechtsform.kein_entgelt"}
OPERATOREN = {">", ">=", "<", "<=", "="}


def _zahl(x):
    try:
        return Fraction(str(x))
    except (ValueError, ZeroDivisionError):
        return None


def _in_spanne(wert, spanne) -> bool:
    z = _zahl(wert)
    return z is not None and Fraction(str(spanne[0])) <= z <= Fraction(str(spanne[-1]))


def pruefe(daten: dict, plausibel: dict) -> list[dict]:
    befunde: list[dict] = []

    def fehler(text: str) -> None:
        befunde.append({"art": "FEHLER", "text": text})

    def hinweis(text: str) -> None:
        befunde.append({"art": "HINWEIS", "text": text})

    erstes = int(plausibel["erstes_jahr"])

    for tabelle, feld, spanne_name in (("abgabesatz", "prozent", "abgabesatz_prozent"),
                                       ("schwelle", "euro", "schwelle_euro"),
                                       ("pauschale", "uebungsleiter", "pauschale_uebungsleiter")):
        jahre = sorted(int(j) for j in daten.get(tabelle, {}))
        if not jahre:
            fehler(f"{tabelle}: keine Einträge")
            continue
        fehlend = [j for j in range(erstes, jahre[-1] + 1) if str(j) not in daten[tabelle]]
        if fehlend:
            fehler(f"{tabelle}: Jahre fehlen: {fehlend}")
        hinweis(f"{tabelle}: belegt bis {jahre[-1]}; spätere Jahre ergeben 'Nicht abgedeckt'")
        for j, z in daten[tabelle].items():
            if not str(z.get("fundstelle") or "").strip():
                fehler(f"{tabelle} {j}: Fundstelle fehlt")
            if z.get(feld) not in (None, "") and not _in_spanne(z[feld], plausibel[spanne_name]):
                fehler(f"{tabelle} {j}: Wert {z[feld]} außerhalb der plausiblen Spanne {plausibel[spanne_name]}")
            if tabelle == "pauschale" and z.get("ehrenamt") not in (None, "") \
                    and not _in_spanne(z["ehrenamt"], plausibel["pauschale_ehrenamt"]):
                fehler(f"pauschale {j}: Ehrenamt {z['ehrenamt']} außerhalb der plausiblen Spanne")
    for j, z in daten.get("schwelle", {}).items():
        if z.get("fassung") not in ("A", "B"):
            fehler(f"schwelle {j}: Fassung {z.get('fassung')!r} unbekannt")

    zeilen = daten.get("register", [])
    for nr, z in enumerate(zeilen, start=1):
        name = f"Register Zeile {nr} ({z.get('schluessel')})"
        if not str(z.get("fundstelle") or "").strip():
            fehler(f"{name}: Fundstelle fehlt")
        if not str(z.get("status") or "").strip():
            fehler(f"{name}: Status fehlt")
        if z.get("operator") not in (None, "") and z["operator"] not in OPERATOREN:
            fehler(f"{name}: Operator {z['operator']!r} ungültig")
        if z.get("von") is not None and z.get("bis") is not None and z["von"] > z["bis"]:
            fehler(f"{name}: 'von' nach 'bis'")
        s = z.get("schluessel")
        if s in plausibel["register"] and not _in_spanne(z.get("wert"), plausibel["register"][s]):
            fehler(f"{name}: Wert {z.get('wert')} außerhalb der plausiblen Spanne {plausibel['register'][s]}")
        elif s in plausibel["texte"] and str(z.get("wert")) not in plausibel["texte"][s]:
            fehler(f"{name}: Wert {z.get('wert')!r} nicht in der erlaubten Liste")
        elif s not in plausibel["register"] and s not in plausibel["texte"]:
            hinweis(f"{name}: keine Plausibilitätsspanne hinterlegt")

    hoechstes = max([erstes] + [int(j) for t in ("abgabesatz", "schwelle") for j in daten.get(t, {})]
                    + [z[k] for z in zeilen for k in ("von", "bis") if z.get(k) is not None])
    for s in sorted({z["schluessel"] for z in zeilen}):
        eigene = [z for z in zeilen if z["schluessel"] == s]
        ende = max([erstes] + [z[k] for z in eigene for k in ("von", "bis") if z.get(k) is not None])
        offen = any(z.get("bis") is None for z in eigene)
        bis_jahr = hoechstes if offen else ende
        beginn = max([erstes] + [min(z["von"] for z in eigene if z.get("von") is not None)]
                     if all(z.get("von") is not None for z in eigene) else [erstes])
        if beginn > erstes:
            hinweis(f"{s}: gilt erst ab {beginn}; frühere Jahre ergeben 'Nicht abgedeckt'")
        for j in range(beginn, bis_jahr + 1):
            gueltig = [z for z in eigene if (z.get("von") is None or z["von"] <= j) and (z.get("bis") is None or j <= z["bis"])]
            if not gueltig:
                fehler(f"{s}: kein Wert für {j}")
            elif s in LISTEN_SCHLUESSEL:
                werte = [str(z["wert"]) for z in gueltig]
                if len(werte) != len(set(werte)):
                    fehler(f"{s}: Wert doppelt für {j}")
            elif len(gueltig) > 1:
                fehler(f"{s}: Überschneidung für {j} ({len(gueltig)} Zeilen)")
    return befunde
