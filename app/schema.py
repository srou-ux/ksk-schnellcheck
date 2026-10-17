"""Festes Fakten-Schema (pydantic). Das Sprachmodell wandelt die Nutzerfrage in dieses JSON um.
Unbekanntes bleibt `None` -- das Modell (und dieses Schema) raten nie. Entwurf -- vom Steuerberater zu pruefen.

`anfrageart` entscheidet, welche Kernfunktion app/router.py aufruft (siehe dort). Default
`None`/"bewertung" deckt den Standardfall ab (Eigenwerbung/typischer Verwerter/Positionen/
Veranstaltungen). "rechtsprechungsfrage" braucht kein Jahr (Befund 6 aus
aufgaben/FUNDE_Chatbot.md: eine reine Recherche ohne Bewertung darf ohne Jahr beantwortet
werden, aber nie mit einer Zahl).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

AuftragspartnerTyp = Literal[
    "natuerliche_person",
    "GbR",
    "GmbH_UG_AG",
    "KG_OHG",
    "Verein",
    "Ausland",
]

Anfrageart = Literal[
    "bewertung",               # Eigenwerbung / typischer Verwerter / Positionen / Veranstaltungen
    "vorauszahlung",
    "saeumniszuschlag",
    "verpflegung",
    "uebungsleiter_pauschale",
    "kommission",
    "schaetzung_ausland",
    "rechnungsanalyse",
    "rechtsprechungsfrage",     # reine Recherche/Auslegung, kein Rechenergebnis -- kein Jahr zwingend
    "auskunft",                 # Teil 1f: Abgabesatz/Schwelle/Meldefrist/Aufbewahrung/Pauschale aus dem Register
    "hinweis",                  # Teil 1f, Abschnitt J.3: Begruessung/Smalltalk ohne jede Sachfrage
]

AuskunftThema = Literal["abgabesatz", "schwelle", "meldefrist", "aufbewahrung", "pauschale"]

# Lesbare Namen fuer AuftragspartnerTyp (Teil 1f: einmal zentral, statt mehrfach in app/
# bestaetigung.py und app/pflichtangaben.py dupliziert).
AUFTRAGSPARTNER_LESBAR: dict[str, str] = {
    "natuerliche_person": "natürliche Person",
    "GbR": "GbR",
    "GmbH_UG_AG": "GmbH/UG/AG",
    "KG_OHG": "KG/OHG",
    "Verein": "Verein",
    "Ausland": "im Ausland ansässig",
}

# Alltagsfälle 11.10.2026 (F4): "privat" = Auftraggeber ist eine Privatperson oder private
# Personengruppe, kein Unternehmen (R-40, R-133). Nur mit Beleg im Text (app/zuordnung.py).
Verwerterart = Literal["eigenwerber", "typischer_verwerter", "generalklausel", "privat"]

# Lesbare Namen fuer Verwerterart (Livetest-Befund L1: fuer Rueckfrage-Schaltflaechen und die
# Faktenbestaetigung -- einmal zentral, wie AUFTRAGSPARTNER_LESBAR).
VERWERTERART_LESBAR: dict[str, str] = {
    "eigenwerber": "Eigenwerbung",
    "typischer_verwerter": "Typischer Verwerter",
    "generalklausel": "Veranstalter (Generalklausel)",
    "privat": "Privatperson (kein Unternehmen)",
}


class Position(BaseModel):
    """Eine einzelne Rechnungs- oder Zahlungsposition.

    `rolle` entspricht, wo zutreffend, direkt dem Vokabular von `kern.rechnen.summe_positionen`
    (z. B. 'vervielfaeltigung_nachtraeglich', 'fahrtkosten_nachgewiesen', 'gewinnzuweisung',
    'verwertungsgesellschaft', 'bewirtung', 'ust'); jeder andere Wert (z. B. 'honorar') zaehlt
    normal zur Bemessungsgrundlage. `rechnungsrolle` ist das davon unabhaengige Vokabular von
    `kern.rechnen.analysiere_rechnung` ('an_kapitalgesellschaft', 'nicht_kuenstlerisch',
    'vertretung_kuenstler', 'eigengeschaeft_dritter', 'reise_kuenstler', 'klaeren') -- nur fuer
    `anfrageart == 'rechnungsanalyse'` relevant.
    """

    betrag: Decimal
    rolle: Optional[str] = None
    rechnungsrolle: Optional[str] = None
    bezeichnung: Optional[str] = None
    nachgewiesen: Optional[bool] = None  # Reisekosten mit/ohne Einzelnachweis bzw. Belege
    kuenstlerisch: Optional[bool] = None  # nur explizit False schliesst aus (siehe kern.rechnen.summe_positionen)
    nr: Optional[int] = None  # Positionsnummer fuer analysiere_rechnung; sonst automatisch (Listenindex)
    # Teil 1f, Abschnitt A: Rechtsform GILT JE POSITION. Fehlt sie, gilt Fakten.auftragnehmer_typ
    # als Vorgabe (app/router.py::_kern_positionen); fehlen beide, ist die Rechtsform dieser
    # Position unbekannt -> Rueckfrage (nie raten, siehe app/pflichtangaben.py).
    auftragnehmer_typ: Optional[AuftragspartnerTyp] = None
    # Testfall 20 Positionen (11.10.2026): Tätigkeit aus dem Excel-Blatt 'Tätigkeitsabgrenzung'
    # (T-ID), 'unbekannt' oder 'widerspruch' -- gesetzt von app/zuordnung.py::ergaenze_taetigkeit
    # (Modellwahl + feste Erkennung), ausgewertet in app/router.py (app/taetigkeiten.py).
    taetigkeit_id: Optional[str] = None
    # Gleiche Nummer = derselbe Auftragnehmer (mehrere Positionen einer Person). Nur aus dem
    # Text oder per Rückfrage, nie geraten; wichtig für R-42/R-117/R-175 (app/router.py).
    auftragnehmer_nr: Optional[int] = None
    # Testprotokoll 11.10.2026: True = diese Position ist der REST einer Rechnung (Rechnungsbetrag
    # aus `Fakten.rechnungen` minus die übrigen Positionen derselben `auftragnehmer_nr`). Den
    # Betrag rechnet der Kern (kern.rechnen.restbetrag), nicht das Modell.
    rest: Optional[bool] = None
    # Härtetest RE-2026-777: True = die Rechnungstellerin handelt bei dieser Position nach der
    # Rechnung NICHT im eigenen Namen (Vertretung, Durchleitung, Direktzahlung). Vom SYSTEM gesetzt
    # (app/zuordnung.py::rechnungsteller_als_zahlungsempfaenger); die Position wird 'Steuerberater
    # entscheidet' (KSK-Info 27, R-33, R-36, R-94).
    zahlungsweg_unklar: Optional[bool] = Field(default=None, description="Wird vom System gesetzt. Immer null lassen.")
    # Härtetest-Serie HT-2026-002 bis 011 (14.10.2026): Grund, warum die Position offen ist (z. B. 'Gutschrift',
    # 'noch nicht bezahlt'), aus app/zahlungsweg_begriffe.json. Vom SYSTEM gesetzt, nie vom Modell.
    offen_grund: Optional[str] = Field(default=None, description="Wird vom System gesetzt. Immer null lassen.")
    # ALLTAG-2026-999: True = Vertrag unmittelbar zwischen Mandant und Künstler (Durchleitung, Vertretung,
    # Direktzahlung); zählt beim Mandanten (KSK-Info 27, KSK-Info 13, R-127). Vom SYSTEM gesetzt.
    vertrag_direkt: Optional[bool] = Field(default=None, description="Wird vom System gesetzt. Immer null lassen.")
    # 14.10.2026 (Testfall L-23): Betrag steht nur in fremder Währung (z. B. 'USD'); Euro-Betrag offen,
    # der Kern rechnet nicht. `fremd_betrag` zeigt die Angabe des Nutzers ('2.000 USD'). Vom SYSTEM gesetzt
    # (app/zuordnung.py::markiere_fremdwaehrung), nie umgerechnet.
    fremdwaehrung: Optional[str] = Field(default=None, description="Wird vom System gesetzt. Immer null lassen.")
    fremd_betrag: Optional[str] = Field(default=None, description="Wird vom System gesetzt. Immer null lassen.")


class Rechnung(BaseModel):
    """Rechnungsbetrag eines Auftragnehmers, so wie der Nutzer ihn nennt (inklusive enthaltener
    Teilbeträge). Eine Korrektur ('900 statt 1.200 Euro') ändert nur diesen Betrag."""

    auftragnehmer_nr: int
    gesamtbetrag: Decimal


Auftragszweck = Literal["eigene_werbung", "fuer_kunden", "veranstaltung", "privat"]


class Herkunft(BaseModel):
    """Woher eine Angabe stammt (Umbau Schritt 1, 16.10.2026; app/einordnung.py): 'text' (mit Zitat aus der Nachricht),
    'knopf' (vom Nutzer ausgewählt), 'modell' (vom Sprachmodell gelesen, im Text nicht wörtlich belegt), 'system'."""

    art: Literal["text", "knopf", "modell", "system"]
    beleg: Optional[str] = None


class Widerspruch(BaseModel):
    """Testprotokoll 11.10.2026: ausdrücklich widersprüchliche Angaben ('Kollege sagt
    Einzelunternehmerin, Rechnung sagt GmbH, ungeklärt') -- keine bestätigte Änderung. `feld`
    ist ein Feldname von Fakten oder 'positionen.<Nummer ab 1>.<Feld>'."""

    feld: str
    werte: list[str] = Field(default_factory=list)
    hinweis: Optional[str] = None


class Fakten(BaseModel):
    """Aus der Nutzerfrage extrahierte Fakten. Jedes Feld ist optional; fehlt eine Angabe,
    bleibt sie `None` und wird von app/pflichtangaben.py als Rueckfrage behandelt -- nie geraten."""

    anfrageart: Optional[Anfrageart] = None
    jahr: Optional[int] = None
    unternehmensart: Optional[str] = None  # frei beschreibend (z. B. "Werbeagentur"), fuer RAG/Anzeige
    # Alte Kategorie: seit dem Umbau (16.10.2026) NUR noch vom System abgeleitet (app/einordnung.py::leite_ab) aus den
    # getrennten Fakten unten. Eine Angabe des Modells hier gilt nur als Lesart (wird übernommen und neu abgeleitet).
    verwerterart: Optional[Verwerterart] = None
    # Wofür ist DIESER Auftrag? (getrennt von der Tätigkeit des Auftraggebers in `unternehmensart`)
    auftragszweck: Optional[Auftragszweck] = Field(default=None, description=(
        "Wofuer ist dieser Auftrag laut Text: eigene_werbung (Werbung/Oeffentlichkeitsarbeit fuer das eigene "
        "Unternehmen), fuer_kunden (fuer Kunden/Dritte), veranstaltung, privat. Nur bei ausdruecklicher Angabe, sonst null."))
    katalog_taetigkeit: Optional[bool] = Field(default=None, description="Wird vom System gesetzt. Immer null lassen.")
    herkunft: dict[str, Herkunft] = Field(default_factory=dict, description="Wird vom System gesetzt. Immer leer lassen.")
    auftraggeber_typ: Optional[AuftragspartnerTyp] = None
    auftragnehmer_typ: Optional[AuftragspartnerTyp] = None
    leistungsart: Optional[str] = None
    # Tätigkeit für einen Gesamtbetrag ohne Positionen bzw. Vorgabe für Positionen ohne eigene
    # (siehe Position.taetigkeit_id).
    taetigkeit_id: Optional[str] = None
    # True: alle Positionen stammen vom selben Auftragnehmer; False: von verschiedenen
    # (sofern nicht `Position.auftragnehmer_nr` etwas anderes sagt). Rückfrage in
    # app/pflichtangaben.py, wenn es über das Ergebnis entscheidet.
    ein_auftragnehmer: Optional[bool] = None
    positionen: list[Position] = Field(default_factory=list)
    rechnungen: list[Rechnung] = Field(default_factory=list)
    veranstaltungszahl: Optional[int] = None
    # Livetest 11.10.2026: Der Nutzer kann die Zahl der Veranstaltungen ausdrücklich NICHT
    # nennen ('Weiß ich nicht'). Nur per Knopf/fester Begriffsliste gesetzt, nie vom Modell
    # erraten; app/router.py rechnet dann beide Fälle und zeigt einen Grenzfall.
    veranstaltungszahl_unbekannt: Optional[bool] = None
    einnahmeabsicht: Optional[bool] = None
    belege_vorhanden: Optional[bool] = None
    anzahl_auftraege: Optional[int] = None

    # -- Vorauszahlung (kern.rechnen.vorauszahlung_monatlich) --
    bemessungsgrundlage_vorjahr: Optional[Decimal] = None

    # -- Saeumniszuschlag (kern.rechnen.saeumniszuschlag) --
    rueckstand: Optional[Decimal] = None
    rueckstand_liste: Optional[list[Decimal]] = None
    saeumnis_monate: Optional[int] = None
    saeumnis_gesondert_angefordert: Optional[bool] = None

    # -- Verpflegung (kern.rechnen.verpflegung) --
    reise_stunden: Optional[Decimal] = None
    reise_uebernachtung: Optional[bool] = None
    reise_erstattung: Optional[Decimal] = None
    reise_inland: Optional[bool] = None

    # -- Uebungsleiter-/Ehrenamtspauschale (kern.rechnen.uebungsleiter_bg) --
    pauschale_art: Optional[Literal["uebungsleiter", "ehrenamt"]] = None
    pauschale_bestaetigung: Optional[bool] = None
    pauschale_bereits_ausgeschoepft: Optional[Decimal] = None

    # -- Kommission (kern.rechnen.kommission_bg) --
    kommission_verkaufspreis: Optional[Decimal] = None
    kommission_einbehalt: Optional[Decimal] = None

    # -- Schaetzung Ausland (kern.rechnen.schaetzung_ausland) --
    schaetzung_bruttoeinnahmen: Optional[Decimal] = None

    # -- Rechnungsanalyse (kern.rechnen.analysiere_rechnung) --
    empfaenger_abgabepflichtig: Optional[bool] = None
    agentur_abgabepflichtig: Optional[bool] = None
    # 14.10.2026 (P-36, P-37): Grundsatzfragen ohne Betrag. Vom SYSTEM aus dem Text gesetzt
    # (app/zuordnung.py::ergaenze_vertretung, app/vertretung_begriffe.json), nie vom Modell.
    vertretung_kuenstler: Optional[bool] = Field(default=None, description="Wird vom System gesetzt. Immer null lassen.")
    nachweismakler: Optional[bool] = Field(default=None, description="Wird vom System gesetzt. Immer null lassen.")

    # -- Auskunft (Teil 1f, Abschnitt C): Abgabesatz/Schwelle/Meldefrist/Aufbewahrung/Pauschale
    # direkt aus dem Register (kern.rechnen), nie als Festwert im App-Code. --
    auskunft_thema: Optional[AuskunftThema] = None

    # Teil 1f, Abschnitt I.2: "X Euro, darin Y Euro ..." -- vom Nutzer genannter GESAMTBETRAG,
    # nur gesetzt, wenn er tatsaechlich genannt wurde (fuer die Plausibilitaetspruefung gegen
    # die Summe der Positionen, app/plausibilitaet.py).
    gesamtbetrag_genannt: Optional[Decimal] = None

    freitext_rest: Optional[str] = None  # alles, was das Modell nicht einordnen konnte

    # Alltagsfälle 11.10.2026 (F3): Rechtsform des ausdrücklich genannten Rechnungstellers.
    # Vom SYSTEM gesetzt (app/zuordnung.py::rechnungsteller_als_zahlungsempfaenger), nie vom Modell.
    rechnungsteller_typ: Optional[AuftragspartnerTyp] = Field(
        default=None, description="Wird vom System gesetzt. Immer null lassen.")
    # ALLTAG-2026-999: Regel zur Nummer des § 24 Abs. 1 (Art des typischen Verwerters, z. B. R-126
    # Messe, R-03 Veranstalter), aus der Beschreibung des Auftraggebers. Vom SYSTEM gesetzt.
    verwerter_regel: Optional[str] = Field(default=None, description="Wird vom System gesetzt. Immer null lassen.")
    # 14.10.2026: nur ein Gesamtbetrag, und der in fremder Währung ('2.000 USD'): Euro-Betrag offen.
    gesamt_fremdwaehrung: Optional[str] = Field(default=None, description="Wird vom System gesetzt. Immer null lassen.")
    # Härtetest-Serie HT-2026-002 bis 011 (14.10.2026): Zahlungen aus mehreren Kalenderjahren in einer Nachricht
    # ('2020, 2026') bzw. ein Rechtsformwechsel (Einzelunternehmer -> UG). Vom SYSTEM aus dem Text gesetzt
    # (app/zuordnung.py); app/pflichtangaben.py fragt dann, statt zu rechnen.
    mehrere_zahlungsjahre: Optional[str] = Field(default=None, description="Wird vom System gesetzt. Immer null lassen.")
    rechtsformwechsel: Optional[bool] = Field(default=None, description="Wird vom System gesetzt. Immer null lassen.")
    # Alltagsfälle 11.10.2026: Jahr aus den (einheitlichen) Daten der Rechnung abgeleitet --
    # vom SYSTEM gesetzt, in der Faktenbestätigung als 'bitte prüfen' gekennzeichnet.
    jahr_aus_rechnungsdaten: Optional[bool] = Field(
        default=None, description="Wird vom System gesetzt. Immer null lassen.")

    # -- Fallstand (Testprotokoll 11.10.2026, app/fallstand.py) --
    # Felder, die der Nutzer AUSDRÜCKLICH als unbekannt/ungeklärt bezeichnet hat: werden nicht
    # erneut gefragt, blockieren aber eine davon abhängige Bewertung. Schlüssel wie bei
    # Widerspruch.feld.
    unbekannt: list[str] = Field(default_factory=list)
    widersprueche: list[Widerspruch] = Field(default_factory=list)

    @field_validator("jahr")
    @classmethod
    def jahr_plausibel(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1980 <= v <= 2100):
            raise ValueError("Jahr ausserhalb des plausiblen Bereichs")
        return v

    def summe_positionen(self) -> Decimal:
        return sum((p.betrag for p in self.positionen), Decimal("0"))
