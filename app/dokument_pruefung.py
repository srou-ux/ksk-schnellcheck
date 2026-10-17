"""Bestätigte Dokumentfakten -> vorhandener Regelkern + unabhängige Gegenrechnung, ohne LLM.

Keine eigene Rechtswerttabelle, keine Berechnung in der Oberfläche. Unvollständige Jahresdaten
führen zu Rückfragen, nicht zu einer vermeintlichen Jahresbefreiung aus einer Einzelrechnung.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app import einordnung, gegenrechnung, pflichtangaben, quellen, router, taetigkeiten
from app.dokument_lesen import KONFIG
from app.schema import AuftragspartnerTyp, Auftragszweck, Fakten, Herkunft, Position, VERWERTERART_LESBAR


class DokumentPosition(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    bezeichnung: str = Field(min_length=1, max_length=1000)
    betrag: Decimal = Field(ge=0, max_digits=14, decimal_places=2, allow_inf_nan=False)
    auftragnehmer_typ: AuftragspartnerTyp | None = None
    auftragnehmer_nr: int | None = Field(default=None, ge=1)
    beleg: str = Field(default="manuell erfasst", max_length=4000)
    # Kein frei beschreibbares Systemfeld/keine frei wählbare Tätigkeit-ID aus dem Client.
    zahlungsweg: Literal["direkt", "unklar"] = "unklar"


class DokumentFall(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    jahr: int | None = None
    unternehmensart: str = Field(default="", max_length=300)
    auftragszweck: Auftragszweck | None = None
    katalog_taetigkeit: bool | None = None
    jahresdaten_vollstaendig: bool | None = None
    netto_und_bezahlt: bool = False
    positionen_geprueft: bool = False
    veranstaltungszahl: int | None = Field(default=None, ge=0)
    einnahmeabsicht: bool | None = None
    positionen: list[DokumentPosition] = Field(default_factory=list, max_length=KONFIG["max_positionen"])


def fakten_aus(fall: DokumentFall, taetigkeit_ids: list[str] | None = None):
    """`taetigkeit_ids` (Schnellcheck, 17.10.2026): je Position eine vom Nutzer aus der festen Liste gewählte
    Tätigkeit (T-ID aus dem Blatt 'Tätigkeitsabgrenzung' oder 'unbekannt'). Ohne Angabe wie bisher: Erkennung
    aus der Bezeichnung. Eine ID, die nicht in der Liste steht, gilt als 'unbekannt' (nie geraten)."""
    if taetigkeit_ids is not None and len(taetigkeit_ids) != len(fall.positionen):
        raise ValueError("Für jede Position genau eine Tätigkeit angeben.")
    positionen = []
    for i, p in enumerate(fall.positionen):
        if taetigkeit_ids is not None:
            tid = taetigkeit_ids[i] if taetigkeiten.gueltige_id(taetigkeit_ids[i]) else taetigkeiten.UNBEKANNT
        else:
            tid = taetigkeiten.erkenne(p.bezeichnung) or taetigkeiten.UNBEKANNT
        positionen.append(Position(
            bezeichnung=p.bezeichnung, betrag=p.betrag, auftragnehmer_typ=p.auftragnehmer_typ,
            auftragnehmer_nr=p.auftragnehmer_nr, taetigkeit_id=tid,
            zahlungsweg_unklar=p.zahlungsweg != "direkt",
            offen_grund="Vertrag oder Zahlung an den Leistungserbringer ist noch unklar." if p.zahlungsweg != "direkt" else None))
    f = Fakten(jahr=fall.jahr, unternehmensart=fall.unternehmensart, auftragszweck=fall.auftragszweck,
               katalog_taetigkeit=fall.katalog_taetigkeit, positionen=positionen, anfrageart="bewertung",
               veranstaltungszahl=fall.veranstaltungszahl if fall.auftragszweck == "veranstaltung" else None,
               einnahmeabsicht=fall.einnahmeabsicht,
               herkunft={k: Herkunft(art="knopf", beleg="Dokumentenformular: vom Nutzer bestätigt")
                         for k in ("jahr", "unternehmensart", "auftragszweck", "katalog_taetigkeit")})
    return einordnung.leite_ab(f)


def offene_angaben(fall: DokumentFall, f: Fakten):
    fragen = []
    if not fall.positionen:
        fragen.append("Bitte mindestens eine tatsächlich gezahlte Position erfassen.")
    if fall.jahr is None:
        fragen.append("In welchem Jahr wurden diese Positionen bezahlt? Das Rechnungsdatum allein genügt nicht.")
    if not fall.unternehmensart:
        fragen.append("Was macht Ihr Unternehmen bzw. wer hat den Auftrag privat erteilt?")
    if not fall.auftragszweck:
        fragen.append("Wofür war der Auftrag?")
    if fall.katalog_taetigkeit is None:
        fragen.append("Bitte die weiteren Tätigkeiten des Auftraggebers anhand der angezeigten Liste klären.")
    if fall.katalog_taetigkeit is True and fall.auftragszweck == "privat":
        fragen.append("Privater Auftrag und Unternehmenstätigkeit widersprechen sich hier. Bitte den tatsächlichen Auftraggeber klären.")
    if fall.katalog_taetigkeit is False and fall.auftragszweck == "fuer_kunden":
        fragen.append("Sie nennen Werbung für Kunden, verneinen aber entsprechende Unternehmenstätigkeiten. Bitte diese Angaben klären.")
    if not fall.positionen_geprueft:
        fragen.append("Bitte alle erkannten und fehlenden Positionen mit den Originalen vergleichen und bestätigen.")
    if not fall.netto_und_bezahlt:
        fragen.append("Bitte bestätigen: Die Positionen enthalten die tatsächlich gezahlten Euro-Beträge ohne gesondert ausgewiesene Umsatzsteuer, keine Summenzeilen und keine Doppelzählungen.")
    if f.verwerterart in ("eigenwerber", "generalklausel") and fall.jahresdaten_vollstaendig is not True:
        fragen.append("Für die Jahresprüfung fehlen noch vollständige Jahresdaten. Eine einzelne Rechnung belegt keine Unterschreitung der Jahresgrenze.")
    for i, p in enumerate(fall.positionen, start=1):
        if p.auftragnehmer_typ is None:
            fragen.append(f"Position {i}: Welche Rechtsform hat der Leistungserbringer?")
        if p.auftragnehmer_nr is None:
            fragen.append(f"Position {i}: Bitte eine Auftragnehmer-Nummer vergeben. Dieselbe Person erhält immer dieselbe Nummer.")
    gruppen = {}
    for p in fall.positionen:
        if p.auftragnehmer_nr is not None and p.auftragnehmer_typ:
            gruppen.setdefault(p.auftragnehmer_nr, set()).add(p.auftragnehmer_typ)
    if any(len(g) > 1 for g in gruppen.values()):
        fragen.append("Für denselben Auftragnehmer wurden verschiedene Rechtsformen erfasst. Bitte getrennte Vertragspartner klären.")
    if not fragen:
        fragen.extend(pflichtangaben.fehlende_pflichtangaben(f, alle=True))
    return list(dict.fromkeys(fragen))


def vorbereiten(fall: DokumentFall):
    f = fakten_aus(fall)
    fragen = offene_angaben(fall, f)
    positionssaetze = []
    for i, p in enumerate(f.positionen, start=1):
        t = taetigkeiten.nach_id(p.taetigkeit_id)
        satz = f"Position {i}: {p.bezeichnung}, gezahlt {p.betrag} Euro, Auftragnehmer {p.auftragnehmer_nr}. Zuordnung: {taetigkeiten.lesbar(p.taetigkeit_id)}."
        if t and t.get("bedingung"):
            satz += f" Voraussetzung / Abgrenzung laut Regelkatalog: {t['bedingung']}"
        positionssaetze.append(satz)
    return {"rueckfragen": fragen, "bereit": not fragen,
            "zusammenfassung": [
                f"Auftraggeber: {fall.unternehmensart or 'noch offen'}.",
                f"Zweck: {einordnung.ZWECK_LESBAR.get(fall.auftragszweck, 'noch offen')}.",
                f"Zahlungsjahr: {fall.jahr if fall.jahr is not None else 'noch offen'}.",
                f"Sie prüfen {len(fall.positionen)} Positionen; gleiche Auftragnehmer-Nummern stehen für denselben Leistungserbringer.",
                f"Abgeleitete Einordnung: {VERWERTERART_LESBAR.get(f.verwerterart, 'noch offen')}.",
                "Vollständige Jahresdaten bestätigt." if fall.jahresdaten_vollstaendig else "Keine vollständigen Jahresdaten bestätigt.",
                *positionssaetze],
            "hinweis": "Entwurf – vom Steuerberater zu prüfen"}


def auswerten(fall: DokumentFall, taetigkeit_ids: list[str] | None = None):
    f = fakten_aus(fall, taetigkeit_ids)
    fragen = offene_angaben(fall, f)
    if fragen:
        return {"ergebnisklasse": "Rückfrage nötig", "rueckfragen": fragen, "positionen": [], "werte": {}}
    k, p = router._kern_mit_gegenrechnung(f)
    if p.status != "bestaetigt":
        return {"ergebnisklasse": "Prüfung fehlgeschlagen", "rueckfragen": [gegenrechnung.text_fehlgeschlagen(p)],
                "positionen": [], "werte": {}, "pruefprotokoll": router._pruefprotokoll(p)}
    zeilen = []
    for x, original in zip(router._einordnung(f), fall.positionen):
        if f.verwerterart == "privat":
            status = "Privater Auftrag – zählt hier nicht"
        elif not x["zaehlend"]:
            status = "Zählt nach Empfängerprüfung nicht"
        elif x["gruppe"] == "kuenstlerisch":
            status = "Zählt zur Entgeltprüfung"
        elif x["gruppe"] == "nicht_kuenstlerisch":
            status = "Zählt nach Tätigkeitsprüfung nicht"
        else:
            status = "Unklar – Steuerberater entscheidet"
        zeilen.append({"bezeichnung": original.bezeichnung, "betrag": str(original.betrag), "status": status,
                       "beleg": original.beleg, "taetigkeit": taetigkeiten.lesbar(x["tid"]),
                       "nebenleistung": x["nebenleistung"], "regel_ids": x["regel_ids"], "fundstellen": x["fundstellen"]})
    regeln = [quellen.regel_by_id(r) for r in k.regel_ids]
    fundstellen = list(dict.fromkeys([s for s in k.fundstellen_kern if s] +
                                     [r["fundstelle"] for r in regeln if r and r.get("fundstelle")]))
    fundstellen = [f"Auslegung der KSK (kein Gesetz): {s}" if "KSK" in s else s for s in fundstellen]
    return {"ergebnisklasse": k.klasse, "begruendung": k.grund or k.protokoll.get("subsumtion", ""),
            "rueckfragen": k.rueckfragen, "positionen": zeilen, "fundstellen": fundstellen,
            "regel_ids": k.regel_ids, "werte": {key: str(v) for key, v in k.protokoll.items() if isinstance(v, Decimal)},
            "pruefprotokoll": router._pruefprotokoll(p), "hinweis": "Entwurf – vom Steuerberater zu prüfen",
            "positionshinweis": "Die Positionsprüfung zeigt, welche Entgelte zählen. Die Abgabepflicht ergibt sich erst aus dem gesamten bestätigten Fall."}
