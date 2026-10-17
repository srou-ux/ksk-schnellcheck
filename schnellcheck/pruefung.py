"""KSK-Schnellcheck (kostenlos, ohne KI) – Eingabe aus festen Auswahlfeldern -> derselbe Regelkern wie im SaaS.

Hier wird NICHTS gerechnet und kein Rechtswert festgelegt. Die Angaben werden in den vorhandenen
`app.dokument_pruefung.DokumentFall` übersetzt und mit `auswerten()` geprüft (Kern + unabhängige Gegenrechnung).
Jahre, Leistungen, Rechtsformen, Katalog und Zwecke kommen aus dem Regelwerk bzw. der App-Schicht.
Entwurf – vom Steuerberater zu prüfen.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app import einordnung, quellen, taetigkeiten
from app.dokument_lesen import KONFIG
from app.dokument_pruefung import DokumentFall, auswerten
from app.schema import AUFTRAGSPARTNER_LESBAR, AuftragspartnerTyp, Auftragszweck
from kern import rechnen as K

HINWEIS = K.HINWEIS

# Anzeige für Besucher: die fünf Ergebnisklassen des Kerns bleiben unverändert sichtbar; der Schnellcheck fasst nur
# alles, was keine klare Einschätzung ist, unter „Weitere Prüfung nötig“ zusammen (keine Scheinsicherheit).
ANZEIGE = {
    K.ABGABEPFLICHTIG: ("ja", "Voraussichtlich abgabepflichtig"),
    K.NICHT: ("nein", "Voraussichtlich nicht abgabepflichtig"),
}
WEITERE_PRUEFUNG = ("offen", "Weitere Prüfung nötig")


class SchnellPosition(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    leistung: str = Field(min_length=1, max_length=20)  # T-ID aus der Liste oder 'unbekannt'
    betrag: Decimal = Field(gt=0, max_digits=14, decimal_places=2, allow_inf_nan=False)
    rechtsform: AuftragspartnerTyp | None = None
    auftragnehmer: int = Field(ge=1)  # gleiche Nummer = derselbe Auftragnehmer; Namen bleiben im Browser
    direkt_bezahlt: bool | None = None  # an den Leistungserbringer selbst gezahlt?


class SchnellFall(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    jahr: int | None = None
    branche: str = Field(default="", max_length=120)
    zweck: Auftragszweck | None = None
    katalog: bool | None = None
    alle_auftraege_erfasst: bool | None = None
    angaben_bestaetigt: bool = False
    veranstaltungen: int | None = Field(default=None, ge=0, le=100000)
    einnahmeabsicht: bool | None = None
    positionen: list[SchnellPosition] = Field(default_factory=list, max_length=KONFIG["max_positionen"])


def _jahre() -> list[int]:
    """Nur Jahre, für die das Register Schwelle und Abgabesatz enthält."""
    return [j for j in quellen.verfuegbare_jahre() if K.schwelle(j) and K.abgabesatz(j) is not None]


def optionen() -> dict:
    gruppen = {"kuenstlerisch": 0, "grenzfall": 1, "nicht_kuenstlerisch": 2}
    leistungen = sorted(taetigkeiten.alle(), key=lambda e: (gruppen.get(e["gruppe"], 9), e["name"].lower()))
    return {
        "jahre": _jahre(),
        "rechtsformen": AUFTRAGSPARTNER_LESBAR,
        "zwecke": [{"wert": w, "text": t} for t, w in einordnung.ZWECK_KNOPF.items()],
        "leistungen": [{"id": e["id"], "name": e["name"], "hinweis": e["bedingung"]} for e in leistungen]
                      + [{"id": taetigkeiten.UNBEKANNT, "name": "Andere Leistung (nicht in dieser Liste)", "hinweis": ""}],
        "katalog": [{"text": r["voraussetzung"], "quelle": r["fundstelle"]}
                    for r in quellen.alle_regeln() if r["gruppe"] == "Katalog"],
        "max_positionen": KONFIG["max_positionen"],
        "hinweis": HINWEIS,
    }


def _dokumentfall(fall: SchnellFall) -> DokumentFall:
    namen = {e["id"]: e["name"] for e in taetigkeiten.alle()}
    return DokumentFall(
        jahr=fall.jahr,
        unternehmensart=fall.branche,
        auftragszweck=fall.zweck,
        katalog_taetigkeit=fall.katalog,
        jahresdaten_vollstaendig=fall.alle_auftraege_erfasst,
        # Eine Bestätigung des Besuchers deckt beides ab: Beträge netto und tatsächlich gezahlt, Positionen vollständig
        # und mit den eigenen Rechnungen abgeglichen (Wortlaut der Checkbox in static/index.html).
        netto_und_bezahlt=fall.angaben_bestaetigt,
        positionen_geprueft=fall.angaben_bestaetigt,
        veranstaltungszahl=fall.veranstaltungen,
        einnahmeabsicht=fall.einnahmeabsicht,
        positionen=[{
            "bezeichnung": namen.get(p.leistung, "Andere Leistung"),
            "betrag": p.betrag,
            "auftragnehmer_typ": p.rechtsform,
            "auftragnehmer_nr": p.auftragnehmer,
            "beleg": "Schnellcheck: vom Besucher ausgewählt",
            "zahlungsweg": "direkt" if p.direkt_bezahlt else "unklar",
        } for p in fall.positionen],
    )


def pruefe(daten: dict) -> dict:
    """Prüft die Angaben. Wirft ValueError mit verständlichem Text bei ungültigen Eingaben."""
    try:
        fall = SchnellFall.model_validate(daten)
    except ValidationError:
        raise ValueError("Bitte Angaben prüfen: Beträge größer 0 mit höchstens zwei Nachkommastellen, "
                         "alle Auswahlfelder gültig.") from None
    if fall.jahr is not None and fall.jahr not in _jahre():
        raise ValueError("Für dieses Jahr enthält das Regelwerk keine Werte.")
    ids = [p.leistung for p in fall.positionen]
    if any(i != taetigkeiten.UNBEKANNT and not taetigkeiten.gueltige_id(i) for i in ids):
        raise ValueError("Bitte die Leistung aus der Liste auswählen.")
    erg = auswerten(_dokumentfall(fall), taetigkeit_ids=ids)
    erg.pop("pruefprotokoll", None)  # internes Rechenprotokoll, für Besucher ohne Nutzen
    stufe, titel = ANZEIGE.get(erg["ergebnisklasse"], WEITERE_PRUEFUNG)
    erg["anzeige"] = {"stufe": stufe, "titel": titel}
    erg.setdefault("hinweis", HINWEIS)
    return erg
