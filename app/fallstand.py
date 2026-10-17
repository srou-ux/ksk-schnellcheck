"""Verbindlicher Fallstand (Testprotokoll 11.10.2026).

Der Chat ist nicht der Speicher. Der Fallstand eines Falls sind die in der Sitzung gespeicherten
Fakten (app/bestaetigung.py) mit zwei zusätzlichen Zuständen:
- 'ausdrücklich unbekannt' (`Fakten.unbekannt`): wird nicht erneut gefragt, blockiert aber eine
  davon abhängige Bewertung;
- 'widersprüchlich' (`Fakten.widersprueche`): keine bestätigte Änderung; der bisherige Wert
  bleibt, das System fragt gezielt nach, und es gibt keine Bewertung, solange der Widerspruch
  offen ist.
'Noch nicht erfragt' ist ein fehlender Wert ohne diese Zustände, 'bekannt' ein gesetzter Wert.

Das Sprachmodell bekommt den Fallstand und nur die neue Nachricht (app/llm/mistral.py) und
liefert den aktualisierten Stand; `uebernehme` prüft und übernimmt ihn in Python: was das Modell
nicht liefert, bleibt erhalten; ausdrücklich Unbekanntes wird geleert; ein Widerspruch ändert
den bisherigen Wert nicht. Schlüssel: Feldname oder 'positionen.<Nummer ab 1>.<Feld>'.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from decimal import Decimal

from app.schema import AUFTRAGSPARTNER_LESBAR, VERWERTERART_LESBAR, Fakten, Position, Widerspruch

_BEGRIFFE = json.loads((Path(__file__).resolve().parent / "fallstand_begriffe.json").read_text(encoding="utf-8"))
_UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})

UNBEKANNT_KNOPF = "Noch unbekannt / später klären"
UNBEKANNT_WERT = "__unbekannt__"

# Lesbare Namen für Übersicht und Rückfragen (Anzeige, keine fachlichen Werte).
FELD_LESBAR = {
    "jahr": "Jahr",
    "verwerterart": "Art des Auftraggebers",
    "auftragszweck": "Zweck des Auftrags",
    "auftragnehmer_typ": "Rechtsform des Auftragnehmers",
    "einnahmeabsicht": "Einnahmeabsicht",
    "veranstaltungszahl": "Zahl der Veranstaltungen",
    "gesamtbetrag_genannt": "Betrag",
    "leistungsart": "Leistung",
    "ein_auftragnehmer": "Alle Positionen vom selben Auftragnehmer",
    "betrag": "Betrag",
}
_NICHT_ALS_FELD = {"unbekannt", "widersprueche", "freitext_rest", "positionen", "rechnungen"}
# Angaben, die der Nutzer macht und die deshalb widersprüchlich sein können.
WIDERSPRUCHSFAEHIG = {"jahr", "verwerterart", "auftragszweck", "auftragnehmer_typ", "auftraggeber_typ", "einnahmeabsicht",
                      "veranstaltungszahl", "gesamtbetrag_genannt", "betrag", "ein_auftragnehmer", "leistungsart",
                      "bezeichnung", "anzahl_auftraege"}


def D_(zahl: str) -> Decimal:
    return Decimal(zahl.replace(".", ""))


def _norm(text: str) -> str:
    return " ".join(str(text or "").lower().translate(_UMLAUTE).split())


def _hat(text: str, begriffe: list[str]) -> bool:
    t = _norm(text)
    return any(re.search(r"(?<![0-9a-z])" + re.escape(_norm(b)), t) for b in begriffe)


def schluessel(feld: str, position: Optional[int] = None) -> str:
    """`position` ist der Listenindex (ab 0); im Schlüssel steht die Nummer ab 1."""
    return feld if position is None else f"positionen.{position + 1}.{feld}"


def zerlege(key: str) -> tuple[str, Optional[int]]:
    teile = key.split(".")
    if len(teile) == 3 and teile[0] == "positionen" and teile[1].isdigit():
        return teile[2], int(teile[1]) - 1
    return key, None


def gueltiger_schluessel(key: str, fakten: Fakten) -> bool:
    if key.startswith("rechnungen."):
        return True
    feld, index = zerlege(key)
    if index is None:
        return feld in Fakten.model_fields and feld not in _NICHT_ALS_FELD
    return 0 <= index < len(fakten.positionen) and feld in Position.model_fields


def lesbar(key: str, fakten: Fakten) -> str:
    if key.startswith("rechnungen."):
        return f"Rechnungsbetrag von Auftragnehmer {key.split('.', 1)[1]}"
    feld, index = zerlege(key)
    name = FELD_LESBAR.get(feld, feld.replace("_", " "))
    if index is None:
        return name
    p = fakten.positionen[index] if 0 <= index < len(fakten.positionen) else None
    bezeichnung = f" „{p.bezeichnung}“" if p is not None and p.bezeichnung else ""
    return f"{name} bei Position {index + 1}{bezeichnung}"


def wert_lesbar(feld: str, wert: Any) -> str:
    if feld in ("auftragnehmer_typ", "auftraggeber_typ"):
        return AUFTRAGSPARTNER_LESBAR.get(str(wert), str(wert))
    if feld == "verwerterart":
        return VERWERTERART_LESBAR.get(str(wert), str(wert))
    if feld == "auftragszweck":
        from app.einordnung import ZWECK_LESBAR

        return ZWECK_LESBAR.get(str(wert), str(wert))
    if isinstance(wert, bool):
        return "ja" if wert else "nein"
    return str(wert)


def normiere_wert(feld: str, wert: Any) -> Any:
    """Ein Widerspruchswert vom Modell ('Einzelunternehmerin', 'GmbH') auf den Schemawert
    abbilden, wo das eindeutig geht; sonst unverändert (dann gibt es dafür keinen Knopf)."""
    if feld in ("auftragnehmer_typ", "auftraggeber_typ") and wert not in AUFTRAGSPARTNER_LESBAR:
        from app.rechtsform_erkennung import erkenne_rechtsform

        return erkenne_rechtsform(str(wert)) or wert
    if feld == "verwerterart" and wert not in VERWERTERART_LESBAR:
        for schluessel_, text in VERWERTERART_LESBAR.items():
            if _norm(text) == _norm(str(wert)):
                return schluessel_
    return wert


def knopffaehig(feld: str, wert: Any) -> bool:
    if feld in ("auftragnehmer_typ", "auftraggeber_typ"):
        return wert in AUFTRAGSPARTNER_LESBAR
    if feld == "verwerterart":
        return wert in VERWERTERART_LESBAR
    if feld == "auftragszweck":
        from app.einordnung import ZWECK_LESBAR

        return wert in ZWECK_LESBAR
    return isinstance(wert, (bool, int)) or feld in ("jahr",)


def ist_unbekannt(fakten: Fakten, key: Optional[str]) -> bool:
    if not key:
        return False
    if key in fakten.unbekannt:
        return True
    feld, index = zerlege(key)
    # 'Die Rechtsformen der Auftragnehmer sind unbekannt' gilt für alle Positionen ohne eigene.
    return index is not None and feld in fakten.unbekannt


def _setze(daten: dict, key: str, wert: Any) -> None:
    feld, index = zerlege(key)
    if index is None:
        daten[feld] = wert
    elif 0 <= index < len(daten.get("positionen") or []):
        daten["positionen"][index][feld] = wert


def markiere_unbekannt(fakten: Fakten, key: str) -> Fakten:
    """Ausdrücklich unbekannt: Wert leeren, nicht mehr fragen, Widerspruch dazu schließen.
    Die Zahl der Veranstaltungen hat schon einen eigenen Zustand (beide Ausgänge, TB-17/18)."""
    daten = fakten.model_dump(mode="python")
    if key == "veranstaltungszahl":
        daten["veranstaltungszahl"] = None
        daten["veranstaltungszahl_unbekannt"] = True
        return Fakten.model_validate(daten)
    _setze(daten, key, None)
    daten["unbekannt"] = list(dict.fromkeys([*daten.get("unbekannt", []), key]))
    daten["widersprueche"] = [w for w in daten.get("widersprueche", []) if w["feld"] != key]
    return Fakten.model_validate(daten)


def setze_wert(fakten: Fakten, key: str, wert: Any) -> Fakten:
    """Bekannter Wert (Knopf oder klare Angabe): löst 'unbekannt' und 'widersprüchlich'."""
    daten = fakten.model_dump(mode="python")
    _setze(daten, key, wert)
    feld, index = zerlege(key)
    daten["unbekannt"] = [k for k in daten.get("unbekannt", []) if k != key]
    daten["widersprueche"] = [w for w in daten.get("widersprueche", []) if w["feld"] != key]
    return Fakten.model_validate(daten)


# ---------------------------------------------------------------------------------------------
# Erkennung in der neuen Nachricht (deterministisch, ohne Modell)
# ---------------------------------------------------------------------------------------------
_SATZ = re.compile(r"(?<=[.!?;\n])\s+")


def unbekannt_im_text(frage: str) -> list[str]:
    """'Das Jahr, die Rechtsformen der Auftragnehmer und die Einnahmeabsicht sind unbekannt.'
    -> ['jahr', 'auftragnehmer_typ', 'einnahmeabsicht']. Nur Sätze mit einem Unbekannt-Begriff
    UND einem Feld-Begriff; 'Alle anderen Angaben bleiben unbekannt' trifft kein Feld."""
    treffer: list[str] = []
    for satz in _SATZ.split(frage):
        if not _hat(satz, _BEGRIFFE["unbekannt"]):
            continue
        for feld, begriffe in _BEGRIFFE["feld_begriffe"].items():
            if _hat(satz, begriffe) and not _nennt_wert(satz, feld):
                treffer.append(feld)
    return list(dict.fromkeys(treffer))


def _nennt_wert(satz: str, feld: str) -> bool:
    """Nennt der Satz selbst einen Wert für das Feld, ist es nicht unbekannt."""
    t = _norm(satz)
    if feld == "jahr":
        return bool(re.search(r"\b(19|20)\d{2}\b", t))
    if feld == "gesamtbetrag_genannt":
        return bool(re.search(r"\d\s*(€|eur\b|euro)", t))
    if feld == "veranstaltungszahl":
        return bool(re.search(r"\b\d+\s+veranstaltung", t))
    if feld == "auftragnehmer_typ":
        from app.rechtsform_erkennung import RECHTSFORM_MUSTER

        return any(re.search(m, t) for m, _ in RECHTSFORM_MUSTER)
    return False


def antwort_ist_unbekannt(frage: str) -> bool:
    """Der erste Satz der Antwort sagt 'unbekannt/ungeklärt' (ohne ein bestimmtes Feld zu nennen)."""
    erster = _SATZ.split(frage.strip())[0] if frage.strip() else ""
    return len(erster) <= 120 and _hat(erster, _BEGRIFFE["unbekannt"])


def will_uebersicht(frage: str) -> bool:
    return _hat(frage, _BEGRIFFE["uebersicht"])


def meldet_widerspruch(frage: str) -> bool:
    return _hat(frage, _BEGRIFFE["widerspruch"])


def will_entfernen(frage: str) -> bool:
    return _hat(frage, _BEGRIFFE["entfernen"])


def widerspruch_rechtsform_im_text(frage: str, fakten: Fakten) -> Optional[Widerspruch]:
    """Deterministische Gegenprobe: die Nachricht meldet einen Widerspruch und nennt zwei
    verschiedene Rechtsformen ('Kollege sagt Einzelunternehmerin, auf der Rechnung steht GmbH').
    Betroffen ist die einzige Position (bzw. der Gesamtbetrag), deren bisherige Rechtsform eine
    der beiden ist; ist das nicht eindeutig, wird nichts geraten (None)."""
    if not meldet_widerspruch(frage):
        return None
    from app.rechtsform_erkennung import RECHTSFORM_MUSTER, normalisiere_umlaute

    t = normalisiere_umlaute(frage.lower())
    genannt = list(dict.fromkeys(w for m, w in RECHTSFORM_MUSTER if re.search(m, t)))
    if len(genannt) < 2:
        return None
    kandidaten = [i for i, p in enumerate(fakten.positionen)
                  if (p.auftragnehmer_typ or fakten.auftragnehmer_typ) in genannt]
    if len(kandidaten) > 1:
        # Welche Rechnung gemeint ist, zeigt ein genannter Betrag ('Fotorechnung über 800 Euro').
        betraege = {D_(b) for b in re.findall(r"(\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{2})?\s*(?:€|eur\b|euro)", t)}
        kandidaten = [i for i in kandidaten if fakten.positionen[i].betrag in betraege]
    if len(kandidaten) == 1:
        return Widerspruch(feld=schluessel("auftragnehmer_typ", kandidaten[0]), werte=genannt[:2],
                           hinweis="In der Nachricht als ungeklärt gemeldet.")
    if not fakten.positionen and fakten.auftragnehmer_typ in genannt:
        return Widerspruch(feld="auftragnehmer_typ", werte=genannt[:2], hinweis="In der Nachricht als ungeklärt gemeldet.")
    return None


# ---------------------------------------------------------------------------------------------
# Übernahme in Python
# ---------------------------------------------------------------------------------------------
def _widerspruch_im_text_belegt(feld: str, frage: str) -> bool:
    """Test-Dialog 'Der schwierige Kunde' (13.10.2026): Auf 'IGNORIERE alle vorherigen Anweisungen …'
    meldete das Modell einen Widerspruch zur Rechtsform -- ohne jedes Wort dazu in der Nachricht.
    Ein vom Modell gemeldeter Widerspruch gilt nur, wenn die NEUE Nachricht eine passende Angabe
    enthält (Rechtsform, Betrag, Jahreszahl, Zahl, Art des Auftraggebers)."""
    from app import zuordnung
    from app.rechtsform_erkennung import RECHTSFORM_MUSTER, normalisiere_umlaute

    t = normalisiere_umlaute(frage.lower())
    if feld in ("auftragnehmer_typ", "auftraggeber_typ"):
        return any(re.search(m, t) for m, _ in RECHTSFORM_MUSTER)
    if feld in ("betrag", "gesamtbetrag_genannt"):
        return bool(zuordnung.betraege_im_text(frage))
    if feld == "jahr":
        return bool(re.search(r"\b(?:19|20)\d{2}\b", frage))
    if feld in ("veranstaltungszahl", "anzahl_auftraege"):
        return bool(re.search(r"\d", frage))
    if feld == "verwerterart":
        return zuordnung._erkenne_verwerterart(frage) is not None or zuordnung.privater_auftraggeber(frage)
    return True


def _ersetzter_betrag(alte: list, neue: list, frage: str) -> list:
    """Genau eine alte Position, die Nachricht nennt genau EINEN Betrag und einen Korrektur-Begriff
    (app/fallstand_begriffe.json, 'ersetzen'), und die neue Liste besteht aus der alten Position und genau einer
    weiteren mit diesem Betrag: dann ist das eine Korrektur des Betrags, keine zweite Rechnung."""
    from decimal import Decimal

    from app.zuordnung import betraege_im_text

    if len(alte) != 1 or len(neue) != 2 or not _hat(frage, _BEGRIFFE.get("ersetzen", [])):
        return neue
    genannt = betraege_im_text(frage)
    if len(genannt) != 1:
        return neue
    neu_betrag = next(iter(genannt))
    alt_betrag = Decimal(str(alte[0]["betrag"]))
    betraege = [Decimal(str(p["betrag"])) for p in neue]
    if sorted(betraege) != sorted([alt_betrag, neu_betrag]) or alt_betrag == neu_betrag:
        return neue
    neu_pos = neue[betraege.index(neu_betrag)]
    return [{**alte[0], **{k: v for k, v in neu_pos.items() if v is not None}}]


def uebernehme(alt: Fakten, neu: Fakten, frage: str) -> Fakten:
    """Neuer Stand aus dem gespeicherten (`alt`) und der Modellantwort (`neu`):
    - ein gelieferter Wert ersetzt den alten (Korrektur, z. B. 900 statt 1.200 Euro);
    - ein fehlender Wert lässt den alten unverändert;
    - Positionen: eine gelieferte Liste ersetzt die alte -- WENIGER Positionen nur, wenn die
      Nachricht ausdrücklich etwas entfernt ('doppelt erfasst', 'streichen'); sonst bleiben die
      alten, damit das Modell keine Rechnung still verliert;
    - 'unbekannt' sammelt sich an; ein neu gelieferter Wert für ein Feld beendet 'unbekannt';
    - ein Widerspruch ändert den bisherigen Wert NICHT."""
    alt_daten = alt.model_dump(mode="python")
    neu_daten = neu.model_dump(mode="python")
    daten = dict(alt_daten)
    for feld, wert in neu_daten.items():
        if feld in ("unbekannt", "widersprueche", "positionen", "rechnungen"):
            continue
        if wert in (None, [], ""):
            continue
        daten[feld] = wert
    if neu_daten["positionen"]:
        weniger = len(neu_daten["positionen"]) < len(alt_daten["positionen"])
        if weniger and will_entfernen(frage):
            daten["positionen"] = neu_daten["positionen"]
        elif not weniger:
            # Gleiche oder mehr Positionen: je Position übernimmt ein fehlender Wert den alten
            # (das Modell ließ z. B. die Rechtsform der Fotorechnung einfach weg).
            zusammen = []
            for i, p_neu in enumerate(neu_daten["positionen"]):
                p_alt = alt_daten["positionen"][i] if i < len(alt_daten["positionen"]) else {}
                zusammen.append({**p_alt, **{k: v for k, v in p_neu.items() if v is not None}})
            daten["positionen"] = zusammen

    # Alltags-Dialog AT-2026-048: 'es waren doch nur 1.600 EUR' -- alte Position plus neue Position -> ersetzen.
    daten["positionen"] = _ersetzter_betrag(alt_daten["positionen"], daten["positionen"], frage)

    # Rechnungsbeträge je Auftragnehmer: ein neu genannter Betrag ersetzt den alten (Korrektur).
    rechnungen = {r["auftragnehmer_nr"]: r for r in alt_daten.get("rechnungen", [])}
    for r in neu_daten.get("rechnungen", []):
        rechnungen[r["auftragnehmer_nr"]] = r
    daten["rechnungen"] = list(rechnungen.values())

    # unbekannt: alte Einträge bleiben, außer die neue Antwort liefert dafür jetzt einen Wert.
    zwischen = Fakten.model_validate({**daten, "unbekannt": [], "widersprueche": []})
    bleibt = [k for k in alt.unbekannt if _wert(zwischen, k) is None or _wert(alt, k) == _wert(zwischen, k)]
    unbekannt = list(dict.fromkeys([*bleibt, *[k for k in neu.unbekannt if gueltiger_schluessel(k, zwischen)]]))

    widersprueche = {w.feld: w for w in alt.widersprueche}
    for w in neu.widersprueche:
        # Nur Angaben des Nutzers können widersprüchlich sein, keine vom System abgeleiteten
        # (Livetest 11.10.2026: das Modell meldete einen 'Widerspruch' bei taetigkeit_id).
        if (gueltiger_schluessel(w.feld, zwischen) and zerlege(w.feld)[0] in WIDERSPRUCHSFAEHIG
                and _widerspruch_im_text_belegt(zerlege(w.feld)[0], frage)):
            feld, _ = zerlege(w.feld)
            werte = list(dict.fromkeys(normiere_wert(feld, x) for x in w.werte))
            widersprueche[w.feld] = Widerspruch(feld=w.feld, werte=[str(x) for x in werte], hinweis=w.hinweis)
    # Ein Widerspruch lässt den bisherigen Wert stehen (keine stille Auflösung).
    for key in widersprueche:
        alter_wert = _wert(alt, key)
        if alter_wert is not None:
            _setze(daten, key, alter_wert)
    daten["unbekannt"] = [k for k in unbekannt if k not in widersprueche]
    daten["widersprueche"] = [w.model_dump() for w in widersprueche.values()]
    for key in daten["unbekannt"]:
        _setze(daten, key, None)  # ausdrücklich unbekannt heißt: kein Wert, auch kein Modellwert
    return Fakten.model_validate(daten)


def _wert(fakten: Fakten, key: str) -> Any:
    feld, index = zerlege(key)
    if index is None:
        return getattr(fakten, feld, None)
    if 0 <= index < len(fakten.positionen):
        return getattr(fakten.positionen[index], feld, None)
    return None


def ergaenze_aus_text(frage: str, fakten: Fakten) -> Fakten:
    """Deterministisch, ohne Modell: ausdrücklich Unbekanntes und gemeldete Rechtsform-Widersprüche
    aus der neuen Nachricht in den Stand übernehmen."""
    for feld in unbekannt_im_text(frage):
        fakten = markiere_unbekannt(fakten, feld)
    if not fakten.widersprueche:
        w = widerspruch_rechtsform_im_text(frage, fakten)
        if w is not None:
            d = fakten.model_dump(mode="python")
            d["widersprueche"] = [w.model_dump()]
            d["unbekannt"] = [k for k in d["unbekannt"] if k != w.feld]
            fakten = Fakten.model_validate(d)
    return fakten


# ---------------------------------------------------------------------------------------------
# Übersicht
# ---------------------------------------------------------------------------------------------
def offene_zeilen(fakten: Fakten) -> list[str]:
    zeilen = []
    for key in fakten.unbekannt:
        zeilen.append(f"{lesbar(key, fakten)}: ausdrücklich unbekannt")
    if fakten.veranstaltungszahl_unbekannt:
        zeilen.append(f"{FELD_LESBAR['veranstaltungszahl']}: ausdrücklich unbekannt")
    for w in fakten.widersprueche:
        feld, _ = zerlege(w.feld)
        werte = " oder ".join(wert_lesbar(feld, x) for x in w.werte) or (w.hinweis or "verschiedene Angaben")
        zeilen.append(f"{lesbar(w.feld, fakten)}: widersprüchlich ({werte})")
    return zeilen


def widerspruch_frage(w: Widerspruch, fakten: Fakten) -> str:
    if w.feld.startswith("rechnungen."):
        nr = w.feld.split(".", 1)[1]
        return (f"Die Aufteilung der Rechnung von Auftragnehmer {nr} ist unklar: {w.hinweis or ''} "
                "Bitte nennen Sie den Rechnungsbetrag und die darin enthaltenen Teilbeträge.").replace("  ", " ")
    feld, _ = zerlege(w.feld)
    if feld in ("verwerterart", "auftragszweck") and w.hinweis and w.hinweis.endswith("?"):
        return w.hinweis  # gezielte Frage aus app/einordnung.py::knopf ('Sie hatten geschrieben … Welche Angabe stimmt?')
    werte = " oder ".join(wert_lesbar(feld, x) for x in w.werte) or "verschiedene Angaben"
    return f"Widersprüchliche Angaben zu {lesbar(w.feld, fakten)}: {werte}. Welche Angabe stimmt?"
