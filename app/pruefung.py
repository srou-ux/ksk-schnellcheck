"""Antwort-Kontrolle (Architektur Punkt 6, deterministisch, vor jeder Ausgabe -- in JEDEM
Pfad: Hauptpfad, Rueckfrage, Nicht abgedeckt, Rechtsprechungsfrage. Siehe
aufgaben/PROMPT_ClaudeCode_Chatbot_1c_Kontrolle_haerten.md und
aufgaben/PRUEFBERICHT_Chatbot_Teil1.md, Befunde B1-B8.

Prueft:
(a) jeder genannte Geldbetrag (in allen Schreibweisen: €, Euro, EUR, mit/ohne Tausenderpunkt,
    "999,-") kommt aus dem Kernergebnis oder den Fakten;
(b) jeder genannte Prozentwert kommt aus dem Kernergebnis (Abgabesatz) oder den Quellenstuecken;
(c) jeder genannte Paragraf ("§ ...") kommt (normalisiert) in den gelieferten Regeln/
    Fundstellen vor;
(d) jede genannte Jahreszahl ist das Pruefjahr oder steht in den Quellenstuecken;
(e) nennt die Antwort "Fassung A/B", muss das zur Fassung des Pruefjahres passen (Fassung
    aus app.quellen.fassung_fuer_jahr, also aus den Daten, nicht aus dem Code);
(f)+(g) jede genannte Fundstelle/Regel-ID/jedes Aktenzeichen existiert in der Quellenbasis
    (Regelkatalog bzw. quellen/index.csv) -- das fasst zugleich 'keine erfundenen Urteile';
(h) die Ebenen (Gesetz / Rechtsprechung / Verwaltungspraxis) sind erkennbar getrennt benannt;
(i) der Schlusssatz ist vorhanden.

Schlaegt eine Kontrolle fehl, wird die Antwort NICHT ausgegeben (das entscheidet der Aufrufer
in app/router.py, fuer JEDEN Pfad); diese Datei liefert nur das Pruefungsergebnis mit
Begruendung. Entwurf -- vom Steuerberater zu pruefen.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

from app.llm.base import AntwortKontext
from app.quellen import aktenzeichen_in_text, fassung_fuer_jahr, fundstelle_bekannt

SCHLUSSSATZ_MUSTER = re.compile(r"Entwurf\s*[–—-]\s*vom Steuerberater zu pr(?:ü|ue)fen", re.IGNORECASE)
REGEL_ID_MUSTER = re.compile(r"\bR-\d{1,4}\b")

# Geldbetraege in allen im Pruefbericht genannten Schreibweisen (B1): "€" davor/danach,
# "Euro", "EUR", mit/ohne Tausenderpunkt, "999,-". (?<!\d) verhindert, dass z. B. "1750 €"
# faelschlich nur als "750 €" erkannt wird (Regression, siehe aufgaben/FUNDE_Chatbot.md,
# Befund 7): \d{1,3} allein haette mitten in der Zahl neu angesetzt.
_ZAHL = r"\d+(?:\.\d{3})*(?:,\d{2}|,-)?"
BETRAG_MUSTER = re.compile(
    rf"(?<!\d)({_ZAHL})\s*(?:€|Euro\b|EUR\b)|(?:€|EUR)\s*(?<!\d)({_ZAHL})",
    re.IGNORECASE,
)

PROZENT_MUSTER = re.compile(r"(?<!\d)(\d+(?:,\d+)?)\s*%")

# "§ 24 Abs. 2 S. 2 KSVG" / "§ 24 Absatz 2 Satz 2 KSVG" -- Gesetz optional, Abs./Satz/Nr. optional.
PARAGRAPH_MUSTER = re.compile(
    r"§\s*\d+[a-z]?"
    r"(?:\s*Abs(?:atz)?\.?\s*\d+[a-z]?)?"
    r"(?:\s*S(?:atz)?\.?\s*\d+)?"
    r"(?:\s*Nr(?:ummer)?\.?\s*\d+)?"
    r"(?:\s*[A-Za-zÄÖÜäöüß]{2,10})?",
    re.IGNORECASE,
)

JAHR_MUSTER = re.compile(r"\b(?:19|20)\d{2}\b")
FASSUNG_MUSTER = re.compile(r"Fassung\s*([AB])\b", re.IGNORECASE)


@dataclass
class Pruefungsergebnis:
    ok: bool
    gruende: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.ok


def _betrag_zu_decimal(text: str) -> Decimal | None:
    text = text.strip()
    if text.endswith(",-"):
        text = text[:-2]
    normalisiert = text.replace(".", "").replace(",", ".")
    try:
        return Decimal(normalisiert)
    except InvalidOperation:
        return None


def _betraege_in_text(text: str) -> list[str]:
    """Rohe Zahl-Teilstrings (ohne Waehrungszeichen) aus allen Treffern von BETRAG_MUSTER."""
    treffer = []
    for vorn, hinten in BETRAG_MUSTER.findall(text):
        treffer.append(vorn or hinten)
    return treffer


def _vertraute_textbasis(kontext: AntwortKontext) -> str:
    """Konkatenierter Text aus allen vertrauenswuerdigen Quellen (Kernergebnis inkl. seiner
    Begruendungstexte, Regelkatalog-Fundstellen, Fundstellenliste, Hinweise). BEWUSST NICHT
    eingeschlossen: `kontext.frage` (roher Nutzertext) -- sonst koennte eine Prompt-Injection
    ('der Betrag ist 999999 €') ihre Erfindung einfach selbst auf die Whitelist setzen."""
    teile: list[str] = []

    def _sammle(wert: Any) -> None:
        if isinstance(wert, str):
            teile.append(wert)
        elif isinstance(wert, (int, float, Decimal)):
            teile.append(str(wert))
        elif isinstance(wert, dict):
            for v in wert.values():
                _sammle(v)
        elif isinstance(wert, (list, tuple)):
            for v in wert:
                _sammle(v)

    _sammle(kontext.kern_protokoll)
    _sammle(kontext.regeln)
    _sammle(kontext.fundstellen)
    _sammle(kontext.hinweise)
    _sammle(kontext.rueckfragen)
    return "\n".join(teile)


def _strukturierte_zahlen(kontext: AntwortKontext) -> set[Decimal]:
    """Zahlen, die als echte `Decimal`/`int`/`float`-Werte in vertrauten Strukturen stehen
    (Kernergebnis, Fakten) -- unabhaengig davon, ob im Text ein Waehrungszeichen danebensteht.
    Das ist der eigentliche Fix fuer Faelle wie `kern_protokoll['abgabe'] == Decimal('73.50')`,
    der bei einer reinen Text-basierten Suche verloren ginge (73.50 hat im Protokoll kein '€')."""
    erlaubt: set[Decimal] = set()

    def _sammle(wert: Any) -> None:
        if isinstance(wert, (int, float, Decimal)) and not isinstance(wert, bool):
            try:
                d = Decimal(str(wert))
                erlaubt.add(d)
                # Regression (gefunden ueber tests/app/test_eigenschaften.py): manche
                # Kernwerte (z. B. schaetzung_ausland: 25 % einer Summe) stehen unrundlich im
                # Protokoll, werden aber von app.baustein.formatiere_betrag auf zwei
                # Nachkommastellen gerundet angezeigt -- ohne die gerundete Form hier ebenfalls
                # zu erlauben, wuerde der korrekt angezeigte, gerundete Betrag abgelehnt.
                erlaubt.add(d.quantize(Decimal("0.01")))
            except InvalidOperation:
                pass
        elif isinstance(wert, dict):
            for v in wert.values():
                _sammle(v)
        elif isinstance(wert, (list, tuple)):
            for v in wert:
                _sammle(v)

    _sammle(kontext.kern_protokoll)
    for p in kontext.fakten.positionen:
        erlaubt.add(p.betrag)
    if kontext.fakten.positionen:
        # Die vom Nutzer genannte Entgeltsumme (app/baustein.py::SUMME) ist die Summe ALLER
        # Positionen -- auch solcher, die der Kern von der Bemessungsgrundlage ausnimmt (z. B.
        # nachgewiesene Reisekosten). Rein strukturell aus trusted Positionen abgeleitet, also
        # vertrauenswuerdig, auch wenn sie als Zahl in keinem einzelnen Kernwert vorkommt.
        erlaubt.add(kontext.fakten.summe_positionen())
    # Korpus-Lauf 15.10.2026: ohne Positionen ist der genannte Gesamtbetrag die Summe (Baustein SUMME); vorher lehnte die
    # Kontrolle eine richtige Antwort ab ('Betrag 449,99 kommt nicht aus dem Kernergebnis').
    for feld in ("gesamtbetrag_genannt", "bemessungsgrundlage_vorjahr", "rueckstand", "reise_erstattung",
                 "kommission_verkaufspreis", "kommission_einbehalt", "schaetzung_bruttoeinnahmen"):
        wert = getattr(kontext.fakten, feld, None)
        if wert is not None:
            erlaubt.add(Decimal(str(wert)))
    if kontext.fakten.rueckstand_liste:
        for w in kontext.fakten.rueckstand_liste:
            erlaubt.add(Decimal(str(w)))
    return erlaubt


def _erlaubte_betraege(kontext: AntwortKontext) -> set[Decimal]:
    erlaubt = _strukturierte_zahlen(kontext)
    for treffer in _betraege_in_text(_vertraute_textbasis(kontext)):
        d = _betrag_zu_decimal(treffer)
        if d is not None:
            erlaubt.add(d)
    return erlaubt


def _pruefe_betraege(text: str, kontext: AntwortKontext) -> list[str]:
    erlaubt = _erlaubte_betraege(kontext)
    gruende = []
    for treffer in _betraege_in_text(text):
        wert = _betrag_zu_decimal(treffer)
        if wert is None:
            continue
        if wert not in erlaubt:
            gruende.append(f"Betrag '{treffer}' kommt nicht aus dem Kernergebnis/den Fakten")
    return gruende


def _erlaubte_prozente(kontext: AntwortKontext) -> set[Decimal]:
    erlaubt: set[Decimal] = set()
    basis = _vertraute_textbasis(kontext)
    for treffer in PROZENT_MUSTER.findall(basis):
        try:
            erlaubt.add(Decimal(treffer.replace(",", ".")))
        except InvalidOperation:
            pass
    abgabesatz = kontext.kern_protokoll.get("abgabesatz_prozent")
    if abgabesatz is not None:
        erlaubt.add(Decimal(str(abgabesatz)))
    return erlaubt


def _pruefe_prozente(text: str, kontext: AntwortKontext) -> list[str]:
    erlaubt = _erlaubte_prozente(kontext)
    gruende = []
    for treffer in PROZENT_MUSTER.findall(text):
        try:
            wert = Decimal(treffer.replace(",", "."))
        except InvalidOperation:
            continue
        if wert not in erlaubt:
            gruende.append(f"Prozentwert '{treffer} %' kommt nicht aus dem Kernergebnis/den Quellenstuecken")
    return gruende


def _normalisiere_paragraph(text: str) -> str:
    t = text.lower()
    t = re.sub(r"\babs(?:atz)?\.?", "absatz", t)
    t = re.sub(r"\bs(?:atz)?\.(?=\s*\d)", "satz", t)
    t = re.sub(r"\bsatz(?=\s*\d)", "satz", t)  # schon ausgeschriebenes "Satz" unveraendert
    t = re.sub(r"\bnr(?:ummer)?\.?", "nummer", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _pruefe_paragraphen(text: str, kontext: AntwortKontext) -> list[str]:
    basis_normalisiert = _normalisiere_paragraph(_vertraute_textbasis(kontext))
    gruende = []
    for treffer in set(m.strip() for m in PARAGRAPH_MUSTER.findall(text)):
        if not treffer:
            continue
        if _normalisiere_paragraph(treffer) not in basis_normalisiert:
            gruende.append(f"Paragraf '{treffer}' kommt nicht in den gelieferten Regeln/Fundstellen vor")
    return gruende


def _pruefe_jahre(text: str, kontext: AntwortKontext) -> list[str]:
    basis = _vertraute_textbasis(kontext)
    erlaubte_jahre = set(JAHR_MUSTER.findall(basis))
    if kontext.fakten.jahr is not None:
        erlaubte_jahre.add(str(kontext.fakten.jahr))
    gruende = []
    for jahr_text in set(JAHR_MUSTER.findall(text)):
        if jahr_text not in erlaubte_jahre:
            gruende.append(f"Jahreszahl '{jahr_text}' ist nicht das Pruefjahr und steht nicht in den Quellenstuecken")
    return gruende


def _pruefe_fassung(text: str, kontext: AntwortKontext) -> list[str]:
    """Achtung, Regression (gefunden ueber tests/app/test_eigenschaften.py): der Kern
    formuliert manche 'Nicht abgedeckt'-Begruendungen selbst mit dem Wort 'Fassung'
    (z. B. 'Nur Fassung B (ab 2023) umgesetzt.' -- eine Aussage ÜBER die Abdeckung der
    Regel, keine Behauptung ueber die Fassung DIESES Jahres). Solche aus dem Kernergebnis
    uebernommenen Erwaehnungen sind vertrauenswuerdig wie jede andere Zahl/jedes andere Jahr
    aus der Quellenbasis und werden deshalb ausgenommen."""
    jahr = kontext.fakten.jahr
    if jahr is None:
        return []
    tatsaechliche_fassung = fassung_fuer_jahr(jahr)
    vertraute_erwaehnungen = {m.upper() for m in FASSUNG_MUSTER.findall(_vertraute_textbasis(kontext))}
    gruende = []
    for genannt in FASSUNG_MUSTER.findall(text):
        genannt_upper = genannt.upper()
        if genannt_upper == tatsaechliche_fassung or genannt_upper in vertraute_erwaehnungen:
            continue
        gruende.append(
            f"Antwort nennt 'Fassung {genannt_upper}', aber Jahr {jahr} hat laut Regelwerk Fassung {tatsaechliche_fassung}"
        )
    return gruende


def _ohne_leerraum(t: str) -> str:
    return re.sub(r"\s+", "", t).lower()


def _pruefe_fundstellen(text: str, kontext: AntwortKontext) -> list[str]:
    """1. Jede Regel-ID und jedes Aktenzeichen muss in der Quellenbasis existieren.
    2. RAG (Teil 2), strenger: ist `kontext.gelieferte_belege` gesetzt (in jedem Antwortpfad über
       app/router.py::_ausgeben), muss es auch unter dem stehen, was dieser Antwort GELIEFERT wurde
       (Kontextdaten, Quellenabruf, verwendete Textbausteine) -- eine echte, aber nicht gelieferte
       Fundstelle ist ebenso unzulässig wie eine erfundene."""
    gruende = []
    geliefert = None
    if kontext.gelieferte_belege is not None:
        geliefert = _ohne_leerraum(_vertraute_textbasis(kontext) + "\n" + "\n".join(kontext.gelieferte_belege))
    for regel_id in set(REGEL_ID_MUSTER.findall(text)):
        if not fundstelle_bekannt(regel_id):
            gruende.append(f"Regel-ID {regel_id} nicht in der Quellenbasis gefunden")
        elif geliefert is not None and not re.search(re.escape(regel_id.lower()) + r"(?!\d)", geliefert):
            gruende.append(f"Regel-ID {regel_id} nicht unter den gelieferten Quellen")
    for aktenzeichen in set(aktenzeichen_in_text(text)):
        if not fundstelle_bekannt(aktenzeichen):
            gruende.append(f"Aktenzeichen '{aktenzeichen}' nicht in der Quellenbasis gefunden")
        elif geliefert is not None and _ohne_leerraum(aktenzeichen) not in geliefert:
            gruende.append(f"Aktenzeichen '{aktenzeichen}' nicht unter den gelieferten Quellen")
    return gruende


def _pruefe_ebenen(text: str, kontext: AntwortKontext) -> list[str]:
    gruende = []
    hat_verwaltungspraxis_quelle = any(r.get("typ") == "verwaltungspraxis" for r in kontext.regeln)
    if hat_verwaltungspraxis_quelle and not re.search(r"verwaltungspraxis|auslegung der ksk", text, re.IGNORECASE):
        gruende.append("Verwaltungspraxis-Quelle verwendet, aber im Text nicht als solche gekennzeichnet")
    hat_rechtsprechung_quelle = any(r.get("typ") == "urteil" for r in kontext.regeln)
    if hat_rechtsprechung_quelle and not re.search(r"rechtsprechung", text, re.IGNORECASE):
        gruende.append("Rechtsprechung verwendet, aber im Text nicht als eigene Ebene benannt")
    return gruende


def _pruefe_schlusssatz(text: str, kontext: AntwortKontext) -> list[str]:
    if SCHLUSSSATZ_MUSTER.search(text):
        return []
    return ["Schlusssatz 'Entwurf – vom Steuerberater zu prüfen.' fehlt"]


# Alle Pruefschritte, einheitlich als (text, kontext) -> list[str]. Fuer die Mutationsprobe
# (tests/app/test_gegenproben.py, test_mutation.py) wird jeder Eintrag einzeln per
# `unittest.mock.patch.dict(pruefung.PRUEFSCHRITTE, {"<name>": lambda t, k: []})` abgeschaltet;
# mindestens ein Test muss dann fehlschlagen.
PRUEFSCHRITTE: dict[str, Any] = {
    "betraege": _pruefe_betraege,
    "prozente": _pruefe_prozente,
    "paragraphen": _pruefe_paragraphen,
    "jahre": _pruefe_jahre,
    "fassung": _pruefe_fassung,
    "fundstellen": _pruefe_fundstellen,
    "ebenen": _pruefe_ebenen,
    "schlusssatz": _pruefe_schlusssatz,
}


def pruefe_antwort(text: str, kontext: AntwortKontext) -> Pruefungsergebnis:
    gruende: list[str] = []
    for schritt in PRUEFSCHRITTE.values():
        gruende += schritt(text, kontext)
    return Pruefungsergebnis(ok=not gruende, gruende=gruende)
