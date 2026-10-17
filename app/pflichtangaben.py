"""Pflichtangaben-Pruefung (Architektur Punkt 2).

Ohne Jahr gibt es kein Ergebnis, nur eine Rueckfrage. Fehlen weitere Angaben, die der
Kern voraussichtlich braucht, entsteht eine gezielte Rueckfrage -- kurz, hoechstens drei
Fragen auf einmal. Entwurf -- vom Steuerberater zu pruefen.

Teil 1f, Abschnitt F: jede Rechenart prueft ihre EIGENEN Pflichtangaben (z. B. Vorauszahlung:
nur Bemessungsgrundlage Vorjahr; Saeumniszuschlag: nur Rueckstand/Monate) -- VOR der
Faktenbestaetigung, damit der Nutzer nicht erst "Stimmt das?" bestaetigt und danach eine
Rueckfrage bekommt. Keine Fragen, die diese Rechenart nicht braucht (Rechtsform,
Leistungsart) -- vorher kamen die allgemeinen Bewertungsfragen faelschlich auch dort.
"""
from __future__ import annotations

from typing import Any

from app.schema import AUFTRAGSPARTNER_LESBAR, VERWERTERART_LESBAR, Fakten

# Livetest 10.10.2026: Zwei Fragen auf einmal (Zahl der Veranstaltungen UND ja/nein zur
# Einnahmeabsicht) verwirrten -- eine Frage nach der anderen. Reihenfolge = Reihenfolge der
# Prüfung unten; bekannte Angaben werden nie erneut gefragt.
MAX_FRAGEN = 1

FRAGE_JAHR = "In welchem Kalenderjahr ist der Sachverhalt zu bewerten?"
FRAGE_AUFTRAGNEHMER = (
    "Ist der Auftragnehmer eine natürliche Person, eine GbR, eine GmbH/UG/AG, "
    "eine KG/OHG, ein Verein oder im Ausland ansässig?"
)
# Livetest-Befund L1 (aufgaben/PROMPT_ClaudeCode_Chatbot_Livetest1_Befunde.md): vorher nahm
# app/router.py bei fehlender verwerterart stillschweigend "generalklausel"/Eigenwerbung an --
# eine Werbeagentur (typischer Verwerter, keine Schwelle) waere so faelschlich wie Eigenwerbung
# (mit Schwelle) geprueft worden. Jetzt eine gezielte Rueckfrage statt eines Defaults.
# Schritt 2 (17.10.2026, Auftrag „Rückfragen nach Tatsachen“): der Nutzer soll keine rechtliche Kategorie
# („typischer Verwerter“, „Generalklausel“) wählen. Gefragt wird nach der TATSACHE, wofür der Auftrag war; die
# Einordnung leitet das System ab (app/einordnung.py::leite_ab). Knöpfe: app/einordnung.py::ZWECK_KNOPF.
# Freie Beschreibung bleibt möglich (Eingabefeld); passt nichts, wird keine Kategorie erzwungen.
FRAGE_ZWECK = ("Wofür war dieser Auftrag gedacht? Sie können eine Antwort wählen oder den Zweck mit eigenen Worten "
               "beschreiben.")
FRAGE_VERWERTERART = FRAGE_ZWECK  # alter Name, gleiche Frage (Tests, Testläufer)
FRAGE_BETRAG = "Um welchen Betrag geht es, und wofür genau (z. B. Honorar, Nebenkosten, Reisekosten)?"
WEISS_NICHT = "Weiß ich nicht"
FRAGE_WIDERSPRUCH_GESAMTBETRAG = "Welche Angabe stimmt?"
# Testfall 20 Positionen (11.10.2026): ohne Angabe zur Leistung ist nicht zu prüfen, ob sie
# künstlerisch oder publizistisch ist (app/taetigkeiten.py) -- dann wird gefragt, nie geraten.
def frage_euro_betrag(label: str, fremd: str) -> str:
    """14.10.2026 (Testfall L-23): Betrag nur in fremder Währung -- nie umrechnen, nachfragen."""
    return (f"„{label}“ ist in fremder Währung angegeben ({fremd}). Welcher Betrag wurde dafür in Euro "
            "tatsächlich gezahlt (zum Beispiel laut Kontoauszug)?")


FRAGE_EURO_GESAMT_LABEL = "Der Gesamtbetrag"


def _neuer_fall_wort() -> str:
    """Das Stichwort für einen neuen Fall aus app/fallwechsel_begriffe.json (erster Eintrag), nicht im Code."""
    import json
    from pathlib import Path

    begriffe = json.loads((Path(__file__).resolve().parent / "fallwechsel_begriffe.json").read_text(encoding="utf-8"))
    return begriffe["neuer_fall"][0].title()


def frage_mehrere_zahlungsjahre(jahre: str) -> str:
    """Härtetest HT-2026-002 (14.10.2026): Zahlungen aus mehreren Kalenderjahren in einer Nachricht -- nicht
    zusammenzählen. Die Abgabe gilt je Kalenderjahr der Zahlung (KSVG § 25 Abs. 1, R-20)."""
    return (f"In Ihrer Nachricht stehen Zahlungen aus mehreren Kalenderjahren ({jahre}). Die Abgabe wird je "
            "Kalenderjahr der Zahlung berechnet, mit Satz und Grenze dieses Jahres. Bitte geben Sie die Zahlungen "
            f"eines Jahres allein ein und beginnen Sie jedes weitere Jahr mit „{_neuer_fall_wort()}: …“.")


# Härtetest HT-2026-008 (14.10.2026): Einzelunternehmen und spätere Gesellschaft nicht zusammenzählen.
FRAGE_RECHTSFORMWECHSEL = (
    "In Ihrer Nachricht steht ein Wechsel der Rechtsform (zum Beispiel vom Einzelunternehmen zur UG). Welcher "
    "Unternehmer hat welche Zahlung geleistet? Bitte geben Sie die Zahlungen je Unternehmer (vor und nach dem "
    "Wechsel) getrennt ein, jeweils als eigenen Fall.")
FRAGE_LEISTUNG = "Welche Leistung wurde genau erbracht (z. B. Logo-Gestaltung, Fotos, Texte, Programmierung)?"
# Mehrere Positionen desselben Künstlers (R-42, R-117, R-175): ob die Positionen von EINEM
# Auftragnehmer stammen, entscheidet, ob Nebenleistungen mitzählen -- dann wird gefragt.
FRAGE_GLEICHER_AUFTRAGNEHMER = "Stammen alle diese Positionen vom selben Auftragnehmer (einer Person)?"
GLEICHER_JA = "ja, alle vom selben Auftragnehmer"
GLEICHER_NEIN = "nein, von verschiedenen Auftragnehmern"
FRAGE_EINNAHMEABSICHT = "Wurden mit der/den Veranstaltung(en) Einnahmen erzielt oder beabsichtigt?"
FRAGE_VERANSTALTUNGSZAHL = "Wie viele einschlägige Veranstaltungen gab es in dem Jahr?"

# -- Teil 1f: je Rechenart eigene Pflichtangaben (Abschnitt F) --------------------------------
FRAGE_BEMESSUNGSGRUNDLAGE_VORJAHR = "Wie hoch war die Bemessungsgrundlage des Vorjahres?"
FRAGE_RUECKSTAND_UND_MONATE = "Wie hoch ist der Rückstand (ggf. je Zeitraum), und für wie viele Monate?"
FRAGE_REISE_STUNDEN = "Wie viele Stunden dauerte die Reise?"
FRAGE_UEBUNGSLEITER_BETRAG = "Um welchen Honorarbetrag geht es?"
FRAGE_VERTRAGSPARTNER_ABGABEPFLICHTIG = "Ist der Vertragspartner des Künstlers (z. B. der Veranstalter) selbst abgabepflichtig?"
FRAGE_KOMMISSION = "Wie hoch sind Verkaufspreis und Provision/Einbehalt?"
FRAGE_SCHAETZUNG_BRUTTO = "Wie hoch sind die Bruttoeinnahmen?"
FRAGE_RECHNUNGSPOSITIONEN = "Welche Rechnungspositionen gibt es (Betrag, Rolle)?"
FRAGE_AUSKUNFT_THEMA = (
    "Worüber möchten Sie Auskunft (Abgabesatz, Geringfügigkeitsgrenze/Schwelle, "
    "Meldefrist, Aufbewahrungsfrist oder Pauschale)?"
)

_RECHTSFORM_TYPEN = ("natuerliche_person", "GbR", "GmbH_UG_AG", "KG_OHG", "Verein", "Ausland")
RECHTSFORM_OPTIONEN = [AUFTRAGSPARTNER_LESBAR[t] for t in _RECHTSFORM_TYPEN]

_VERWERTERART_TYPEN = ("eigenwerber", "typischer_verwerter", "generalklausel", "privat")
# Nur noch für die alte Schnittstelle (POST /knopf mit feld 'verwerterart'); die Rückfrage zeigt ZWECK_OPTIONEN.
VERWERTERART_OPTIONEN = [VERWERTERART_LESBAR[t] for t in _VERWERTERART_TYPEN]


def _zweck_knoepfe() -> dict[str, str]:
    from app.einordnung import ZWECK_KNOPF

    return dict(ZWECK_KNOPF)


ZWECK_OPTIONEN = list(_zweck_knoepfe())


def _rechtsform_frage(label: str) -> str:
    """Teil 1f, Abschnitt A2: nennt die betroffene Position (Bezeichnung oder 'Position N'),
    damit der Nutzer weiss, wofuer die Rechtsform noch fehlt -- nie raten."""
    return (
        f"Welche Rechtsform hat der Auftragnehmer bei {label} (natürliche Person, GbR, "
        "GmbH/UG/AG, KG/OHG, Verein oder im Ausland ansässig)?"
    )


def fehlende_pflichtangaben(fakten: Fakten, alle: bool = False) -> list[str]:
    """Liefert bis zu drei gezielte Rueckfragen. Leere Liste heisst: Pflichtangaben vorhanden
    (das sagt noch nichts darueber, ob der Kern den Fall rechnen kann).

    Befund 6 (aufgaben/FUNDE_Chatbot.md, behoben): Eine reine Rechtsprechungs-/Auslegungsfrage
    (`anfrageart == "rechtsprechungsfrage"`) braucht kein Jahr -- es wird ja nicht gerechnet,
    nur in der Quellenbasis gesucht (siehe app/router.py).

    Jede andere Anfrageart prueft NUR die Angaben, die ihr eigener Kernaufruf tatsaechlich
    braucht (Teil 1f, Abschnitt F) -- die allgemeinen Fragen nach Auftragnehmer-Typ/
    Leistungsart/Betrag (gedacht fuer den Standardfall "bewertung") passen dort nicht und
    wuerden faelschlich blockieren oder, schlimmer, der Nutzer bestaetigt unvollstaendige
    Fakten, bevor die eigentliche Rueckfrage kommt."""
    if fakten.anfrageart in ("rechtsprechungsfrage", "hinweis"):
        # "hinweis" (Teil 1f, J.3): Begruessung/Smalltalk braucht gar kein Jahr -- es wird
        # weder gerechnet noch recherchiert, nur eine feste Kurzbeschreibung gezeigt.
        return []
    if (fakten.anfrageart or "bewertung") == "bewertung":
        # Härtetest-Serie HT-2026-002 bis 011 (14.10.2026): mehrere Zahlungsjahre oder ein Rechtsformwechsel in
        # einer Nachricht -- erst trennen, dann rechnen (sonst würde alles zu einer Summe).
        if fakten.mehrere_zahlungsjahre:
            return [frage_mehrere_zahlungsjahre(fakten.mehrere_zahlungsjahre)]
        if fakten.rechtsformwechsel:
            return [FRAGE_RECHTSFORMWECHSEL]
    if fakten.jahr is None:
        from app import fallstand

        if not fallstand.ist_unbekannt(fakten, "jahr"):
            return [FRAGE_JAHR]
        # Jahr ausdrücklich unbekannt (Testprotokoll 11.10.2026): nicht erneut fragen; die
        # übrigen Angaben werden weiter erfasst, die Bewertung bleibt zurückgestellt.

    art = fakten.anfrageart or "bewertung"

    if art == "vorauszahlung":
        return [] if fakten.bemessungsgrundlage_vorjahr is not None else [FRAGE_BEMESSUNGSGRUNDLAGE_VORJAHR]

    if art == "saeumniszuschlag":
        hat_rueckstand = fakten.rueckstand is not None or bool(fakten.rueckstand_liste)
        if not hat_rueckstand or fakten.saeumnis_monate is None:
            return [FRAGE_RUECKSTAND_UND_MONATE]
        return []

    if art == "verpflegung":
        return [] if fakten.reise_stunden is not None else [FRAGE_REISE_STUNDEN]

    if art == "uebungsleiter_pauschale":
        # 14.10.2026 (P-20a, 16 von 16 Läufen Rückfrage): 'zahlt … insgesamt 2.500 €' legt das Modell als
        # Gesamtbetrag an, nicht als Position. Der Kern rechnet auch mit dem Gesamtbetrag (router).
        return [] if (fakten.positionen or fakten.gesamtbetrag_genannt is not None) else [FRAGE_UEBUNGSLEITER_BETRAG]

    if art == "kommission":
        if fakten.kommission_verkaufspreis is not None and fakten.kommission_einbehalt is not None:
            return []
        return [FRAGE_KOMMISSION]

    if art == "schaetzung_ausland":
        return [] if fakten.schaetzung_bruttoeinnahmen is not None else [FRAGE_SCHAETZUNG_BRUTTO]

    if art == "rechnungsanalyse":
        return euro_fragen(fakten) if fakten.positionen else [FRAGE_RECHNUNGSPOSITIONEN]

    if art == "auskunft":
        return [] if fakten.auskunft_thema is not None else [FRAGE_AUSKUNFT_THEMA]

    if art != "bewertung":
        return []  # unbekannte/zukuenftige Anfrageart: keine allgemeinen Fragen aufzwingen

    # Standardfall "bewertung": Eigenwerbung / typischer Verwerter / Positionen / Veranstaltungen.
    fragen: list[str] = euro_fragen(fakten)
    # Alltagsfälle 11.10.2026 (F4): Ist der Auftraggeber eine Privatperson (R-40, R-133), ist er
    # nicht abgabepflichtig -- unabhängig von Leistung, Rechtsform und Betrag. Keine weiteren Fragen.
    if fakten.verwerterart == "privat":
        return _abschliessen(fragen, fakten, alle)
    # 14.10.2026 (P-36, P-37): Grundsatzfragen ohne Betrag. Nachweismakler (R-35): keine Angabe nötig.
    # Vertretung (R-33): nur, ob der Vertragspartner selbst abgabepflichtig ist (der Betrag entscheidet nicht).
    if fakten.nachweismakler:
        return _abschliessen(fragen, fakten, alle)
    if fakten.vertretung_kuenstler and not (fakten.positionen or fakten.gesamtbetrag_genannt is not None):
        if fakten.empfaenger_abgabepflichtig is None:
            fragen.append(FRAGE_VERTRAGSPARTNER_ABGABEPFLICHTIG)
        return _abschliessen(fragen, fakten, alle)
    # Dialogtest Fallgrenzen: ein ausdrücklich genannter Gesamtbetrag ist eine bekannte
    # Zahlenbasis -- nicht erneut nach dem Betrag fragen und keine Aufteilung verlangen.
    hat_betrag = bool(fakten.positionen) or fakten.gesamtbetrag_genannt is not None
    # Livetest 10.10.2026: früher entfiel die Betragsfrage, sobald das Modell irgendetwas in
    # das freie Anzeigefeld `unternehmensart` schrieb -- dann kam eine Faktenbestätigung ohne
    # jeden Betrag und danach 'Nicht abgedeckt'. Ohne Betrag (und ohne Veranstaltungszahl, für
    # die der Kern die Entgeltsumme selbst erfragt) gibt es keine Bestätigung.
    if not hat_betrag and fakten.veranstaltungszahl is None:
        fragen.append(FRAGE_BETRAG)

    # Livetest-Befund L1: verwerterart entscheidet, welche Kernpruefung greift (Schwelle vs.
    # keine Schwelle) -- sobald es ueberhaupt eine Zahlenbasis gibt (Positionen oder
    # Veranstaltungszahl), ist sie Pflichtangabe, nie ein stillschweigender Default.
    if (hat_betrag or fakten.veranstaltungszahl is not None) and fakten.verwerterart is None:
        fragen.append(FRAGE_VERWERTERART)

    # Teil 1f, Abschnitt A2: Rechtsform gilt JE POSITION (Position.auftragnehmer_typ); fehlt
    # sie UND der globale Vorgabewert, ist sie fuer diese Position unbekannt -- nie raten,
    # die Rueckfrage nennt die Position. Nachtrag Abschnitt C1: nur fuer Honorar-/Entgelt-
    # positionen -- Rollen, die der Kern ohnehin gesondert (ohne Ruecksicht auf die
    # Rechtsform) behandelt, werden aus dem Kern gelesen, nicht im App-Code aufgezaehlt.
    from kern import rechnen as K

    sonderrollen = set(K._AUSSCHLUSSGRUENDE.keys())
    for i, p in enumerate(fakten.positionen, start=1):
        if p.rolle in sonderrollen:
            continue
        if p.zahlungsweg_unklar:
            # Härtetest HT-2026-001 (14.10.2026): ist der Zahlungsweg offen (Durchleitung, private Zahlung mit
            # offener Erstattung), entscheidet ohnehin der Steuerberater; der Betrag wird nur als „falls er
            # zählt“ ausgewiesen. Keine Rückfrage nach der Rechtsform dafür (keine Rückfrage-Schleife).
            continue
        if p.auftragnehmer_typ is None and fakten.auftragnehmer_typ is None:
            fragen.append(_rechtsform_frage(p.bezeichnung or f"Position {i}"))
    if not fakten.positionen and fakten.auftragnehmer_typ is None:
        fragen.append(FRAGE_AUFTRAGNEHMER)

    # Testfall 20 Positionen: Leistung fehlt ganz -> fragen. Nur, wo sie über die Abgabe
    # entscheidet (nicht bei Zahlungen an eine GmbH/KG und nicht bei Sonderrollen des Kerns).
    kapitalgesellschaft = ("GmbH_UG_AG", "KG_OHG")
    ohne_leistung = [
        p for p in fakten.positionen
        if p.rolle not in sonderrollen
        and (p.auftragnehmer_typ or fakten.auftragnehmer_typ) not in kapitalgesellschaft
        and (p.taetigkeit_id or fakten.taetigkeit_id) is None and not p.bezeichnung
    ]
    if not fakten.positionen and fakten.gesamtbetrag_genannt is not None:
        if fakten.auftragnehmer_typ not in kapitalgesellschaft and fakten.taetigkeit_id is None:
            ohne_leistung.append(None)

    # Nachtrag Abschnitt C2 (Fund, siehe aufgaben/FUNDE_Chatbot.md): leistungsart wird von
    # keiner Kernfunktion fuer die Bewertung gebraucht (weder summe_positionen/
    # pruefe_positionen noch veranstaltungen nehmen sie entgegen) -- deshalb keine
    # Pflichtangabe mehr. Das Modell darf sie weiterhin nennen (Anzeige in der
    # Faktenbestaetigung), sie blockiert nur nicht mehr.

    # Pruefkatalog-Befund M5 (aufgaben/PROMPT_ClaudeCode_Chatbot_Pruefkatalog1_Befunde.md):
    # bei "generalklausel" braucht kern.rechnen.veranstaltungen IMMER die Einnahmeabsicht,
    # und der Router muss klaeren, ob die Entgelte ueberhaupt aus Veranstaltungen stammen
    # (und wie vielen) -- VORHER wurde das nur gefragt, wenn veranstaltungszahl schon
    # zufaellig bekannt war; ohne diese Angabe landete der Fall faelschlich bei der
    # Eigenwerbungs-Pruefung fuer Positionen (app/router.py::_rufe_kern_auf).
    if fakten.verwerterart == "generalklausel":
        if fakten.veranstaltungszahl is None and not fakten.veranstaltungszahl_unbekannt:
            fragen.append(FRAGE_VERANSTALTUNGSZAHL)
        if fakten.einnahmeabsicht is None and not _hoechstens_ausnahme(fakten):
            fragen.append(FRAGE_EINNAHMEABSICHT)
    elif (fakten.veranstaltungszahl is not None and fakten.einnahmeabsicht is None
          and fakten.verwerterart not in ("typischer_verwerter", "eigenwerber")):
        # Härtetest RE-2026-777: für einen typischen Verwerter (§ 24 Abs. 1) und für Eigenwerbung
        # spielt die Einnahmeabsicht keine Rolle (kern.rechnen.veranstaltungen fragt sie dort nicht ab).
        fragen.append(FRAGE_EINNAHMEABSICHT)

    # Testfall 20 Positionen: die Frage nach der Leistung kommt zuletzt (eine Frage auf einmal).
    if not ohne_leistung and _gleicher_auftragnehmer_entscheidet(fakten):
        fragen.append(FRAGE_GLEICHER_AUFTRAGNEHMER)

    # Eine beschriebene Leistung (Bezeichnung oder leistungsart) ordnet
    # app/zuordnung.py::ergaenze_taetigkeit ein -- notfalls als 'unbekannt' (Grenzfall).
    if ohne_leistung and not fakten.leistungsart:
        fragen.append(FRAGE_LEISTUNG)

    return _abschliessen(fragen, fakten, alle)


def euro_fragen(fakten: Fakten) -> list[str]:
    """Rückfragen nach dem gezahlten Euro-Betrag für Beträge, die nur in fremder Währung vorliegen."""
    fragen = [frage_euro_betrag(p.bezeichnung or f"Position {i}", p.fremd_betrag or p.fremdwaehrung)
              for i, p in enumerate(fakten.positionen, start=1) if p.fremdwaehrung]
    if not fakten.positionen and fakten.gesamt_fremdwaehrung:
        fragen.append(frage_euro_betrag(FRAGE_EURO_GESAMT_LABEL, fakten.gesamt_fremdwaehrung))
    return fragen


def euro_frage_ziel(frage: str, fakten: Fakten) -> int | None:
    """Index der Position, nach deren Euro-Betrag `frage` fragt; -1 = Gesamtbetrag; None = keine Euro-Frage."""
    for i, p in enumerate(fakten.positionen):
        if p.fremdwaehrung and frage == frage_euro_betrag(p.bezeichnung or f"Position {i + 1}", p.fremd_betrag or p.fremdwaehrung):
            return i
    if fakten.gesamt_fremdwaehrung and frage == frage_euro_betrag(FRAGE_EURO_GESAMT_LABEL, fakten.gesamt_fremdwaehrung):
        return -1
    return None


def _abschliessen(fragen: list[str], fakten: Fakten, alle: bool) -> list[str]:
    # Testprotokoll 11.10.2026 (Fallstand): ausdrücklich Unbekanntes wird nicht erneut gefragt;
    # ein gemeldeter Widerspruch kommt zuerst, als gezielte Frage (app/fallstand.py).
    from app import fallstand

    fragen = [f for f in fragen if not _unbekannt(fakten, feld_der_frage(f, fakten))]
    fragen = [fallstand.widerspruch_frage(w, fakten) for w in fakten.widersprueche] + fragen
    return fragen if alle else fragen[:MAX_FRAGEN]


# Schritt 2: die Frage nach dem Zweck ersetzt die Frage nach der Art des Auftraggebers. Ein 'unbekannt' unter dem
# alten Namen (vom Modell oder aus einem früheren Fallstand) gilt weiter für dieselbe Frage.
GLEICHE_FRAGE = {"auftragszweck": "verwerterart"}


def _unbekannt(fakten: Fakten, key: str | None) -> bool:
    from app import fallstand

    return fallstand.ist_unbekannt(fakten, key) or (key in GLEICHE_FRAGE
                                                    and fallstand.ist_unbekannt(fakten, GLEICHE_FRAGE[key]))


def _gleicher_auftragnehmer_entscheidet(fakten: Fakten) -> bool:
    """Nur fragen, wenn es darauf ankommt: mehrere zählende Positionen an Einzelpersonen, darunter
    eine künstlerische und eine, die beim selben Künstler anders zählen würde, und weder
    `ein_auftragnehmer` noch `auftragnehmer_nr` ist bekannt."""
    if fakten.ein_auftragnehmer is not None or len(fakten.positionen) < 2:
        return False
    if any(p.auftragnehmer_nr is not None for p in fakten.positionen):
        return False
    from app import taetigkeiten
    from kern import rechnen as K

    zaehlend = [p for p in fakten.positionen
                if p.rolle not in K._AUSSCHLUSSGRUENDE
                and (p.auftragnehmer_typ or fakten.auftragnehmer_typ) not in ("GmbH_UG_AG", "KG_OHG")]
    gruppen = [taetigkeiten.gruppe(p.taetigkeit_id or fakten.taetigkeit_id) for p in zaehlend]
    if "kuenstlerisch" not in gruppen:
        return False
    return any(g != "kuenstlerisch" for g in gruppen)


_OFFENE_FRAGE_FELD = {
    FRAGE_JAHR: "jahr", FRAGE_BETRAG: "gesamtbetrag_genannt", FRAGE_ZWECK: "auftragszweck",
    FRAGE_AUFTRAGNEHMER: "auftragnehmer_typ", FRAGE_EINNAHMEABSICHT: "einnahmeabsicht",
    FRAGE_VERTRAGSPARTNER_ABGABEPFLICHTIG: "empfaenger_abgabepflichtig",
    FRAGE_VERANSTALTUNGSZAHL: "veranstaltungszahl", FRAGE_LEISTUNG: "leistungsart",
    FRAGE_GLEICHER_AUFTRAGNEHMER: "ein_auftragnehmer",
}


def feld_der_frage(frage: str, fakten: Fakten | None) -> str | None:
    """Fallstand-Schlüssel der Angabe, nach der eine Rückfrage fragt (für 'unbekannt' und den
    Knopf 'Noch unbekannt / später klären'), oder None."""
    from app import fallstand

    if frage in _OFFENE_FRAGE_FELD:
        return _OFFENE_FRAGE_FELD[frage]
    if fakten is not None:
        for w in fakten.widersprueche:
            if frage == fallstand.widerspruch_frage(w, fakten):
                return w.feld
        for i, p in enumerate(fakten.positionen):
            if frage == _rechtsform_frage(p.bezeichnung or f"Position {i + 1}"):
                return fallstand.schluessel("auftragnehmer_typ", i)
        ziel = euro_frage_ziel(frage, fakten)
        if ziel is not None:
            return "gesamtbetrag_genannt" if ziel < 0 else fallstand.schluessel("betrag", ziel)
    return None


def vollstaendig(fakten: Fakten) -> bool:
    return not fehlende_pflichtangaben(fakten)


_JA_NEIN_WERTE = {"ja": True, "nein": False}


def _geschlossene_frage_info(frage: str, fakten: Fakten | None) -> dict[str, Any] | None:
    """Erkennt, ob eine Rueckfrage eine geschlossene Frage mit fester Antwortmenge ist
    (Teil 1f, Abschnitt E) -- offene Fragen (Betrag, Rueckstand, ...) liefern `None` und
    bleiben reine Texteingabe (Abschnitt J.1: dafuer gibt es KEINEN Knopf mehr, nur noch
    das Eingabefeld, siehe app/static/index.html).

    Wird `fakten` mitgegeben, liefert der Treffer zusaetzlich die deterministische
    Feld-Zuordnung fuer die knopfbasierte Antwort ohne Modellaufruf (Pruefkatalog-Befund
    M1): `feld` (Fakten-Attribut), `werte` (Anzeigetext -> Rohwert) und bei einer
    Rechtsform-Frage je Position zusaetzlich `position` (0-basierter Index in
    `fakten.positionen`)."""
    f = frage.lower()
    if "einnahmeabsicht" in f or "einnahmen erziel" in f:
        return {"optionen": ["ja", "nein"], "feld": "einnahmeabsicht", "werte": dict(_JA_NEIN_WERTE)}
    if "vertragspartner des künstlers" in f:
        return {"optionen": ["ja", "nein"], "feld": "empfaenger_abgabepflichtig", "werte": dict(_JA_NEIN_WERTE)}
    if fakten is not None:
        for i, p in enumerate(fakten.positionen):
            if frage == _rechtsform_frage(p.bezeichnung or f"Position {i + 1}"):
                return {
                    "optionen": list(RECHTSFORM_OPTIONEN), "feld": "auftragnehmer_typ", "position": i,
                    "werte": dict(zip(RECHTSFORM_OPTIONEN, _RECHTSFORM_TYPEN)),
                }
    if "rechtsform" in f or "natuerliche person" in f or "natürliche person" in f:
        return {
            "optionen": list(RECHTSFORM_OPTIONEN), "feld": "auftragnehmer_typ",
            "werte": dict(zip(RECHTSFORM_OPTIONEN, _RECHTSFORM_TYPEN)),
        }
    if frage == FRAGE_ZWECK:
        return {"optionen": list(ZWECK_OPTIONEN), "feld": "auftragszweck", "werte": _zweck_knoepfe()}
    if frage == FRAGE_GLEICHER_AUFTRAGNEHMER:
        return {"optionen": [GLEICHER_JA, GLEICHER_NEIN], "feld": "ein_auftragnehmer",
                "werte": {GLEICHER_JA: True, GLEICHER_NEIN: False}}
    if frage == FRAGE_VERANSTALTUNGSZAHL:
        # Livetest 11.10.2026: die Zahl bleibt Texteingabe; zusätzlich ein Knopf für den
        # Fall, dass der Nutzer sie nicht kennt (app/router.py zeigt dann beide Ausgänge).
        return {"optionen": [WEISS_NICHT], "feld": "veranstaltungszahl_unbekannt", "werte": {WEISS_NICHT: True}}
    if "kalenderjahr" in f:
        # Teil 1f, Abschnitt J.1: Auswahlknoepfe der im Register VORHANDENEN Jahre -- aus
        # Excel/Kern gelesen (app.quellen.verfuegbare_jahre), kein Jahr im Code festgeschrieben.
        from app.quellen import verfuegbare_jahre

        jahre = [str(j) for j in verfuegbare_jahre()]
        if not jahre:
            return None
        return {"optionen": jahre, "feld": "jahr", "werte": {j: int(j) for j in jahre}}
    return None


def rueckfrage_optionen(rueckfragen: list[str], fakten: Fakten | None = None) -> list[dict[str, Any]]:
    """Teil 1f, Abschnitt E: geschlossene Fragen (Einnahmeabsicht, Rechtsform, Verwerterart,
    Kalenderjahr) bekommen feste Antwortoptionen fuer Schaltflaechen (`app/static/index.html`).

    Wird `fakten` mitgegeben (die Fakten, aus denen `rueckfragen` stammt -- Pruefkatalog-
    Befund M1), liefert jeder Eintrag zusaetzlich `feld`/`werte`(/`position`): ein Klick kann
    damit ueber `POST /knopf` (app/router.py::wende_feldantwort_an) DETERMINISTISCH beantwortet
    werden, ohne erneuten Modellaufruf. Ohne `fakten` (Rueckwaertskompatibilitaet, z. B. nach
    der Faktenbestaetigung) bleibt nur `optionen` -- ein Klick schickt dann wie bisher den
    Anzeigetext als Freitext."""
    from app import fallstand

    ergebnis = []
    for frage in rueckfragen:
        info = _geschlossene_frage_info(frage, fakten)
        key = feld_der_frage(frage, fakten) if fakten is not None else None
        widerspruch = next((w for w in (fakten.widersprueche if fakten is not None else []) if w.feld == key), None)
        if fakten is not None and key and (info is None or widerspruch is not None):
            # Offene Frage (Texteingabe) oder Widerspruch: Knöpfe nur für die Klärung.
            feld, index = fallstand.zerlege(key)
            info = {"optionen": [], "feld": feld, "werte": {}}
            if index is not None:
                info["position"] = index
            for wert in (widerspruch.werte if widerspruch else []):
                if not fallstand.knopffaehig(feld, wert):
                    continue
                info["optionen"].append(fallstand.wert_lesbar(feld, wert))
                info["werte"][fallstand.wert_lesbar(feld, wert)] = wert
        if (info is not None and fakten is not None and key and key != "veranstaltungszahl"
                and info.get("feld") and fallstand.UNBEKANNT_KNOPF not in info["optionen"]):
            # Testprotokoll 11.10.2026: jede Frage lässt sich als 'noch unbekannt' zurückstellen.
            info = {**info, "optionen": [*info["optionen"], fallstand.UNBEKANNT_KNOPF],
                    "werte": {**info["werte"], fallstand.UNBEKANNT_KNOPF: fallstand.UNBEKANNT_WERT}}
        if info and info.get("optionen"):
            ergebnis.append({"frage": frage, **info})
    return ergebnis


def _hoechstens_ausnahme(fakten: Fakten) -> bool:
    """14.10.2026 (P-17): bei höchstens so vielen Veranstaltungen, wie die Ausnahme der Generalklausel
    zulässt (Register 'veranstaltungen.ausnahme_max', KSVG § 24 Abs. 2 S. 3 Nr. 1), ist das Ergebnis
    unabhängig von der Einnahmeabsicht -- dann wird nicht nach ihr gefragt."""
    from decimal import Decimal

    from kern import rechnen as K

    if not fakten.veranstaltungszahl or fakten.jahr is None:
        return False
    try:
        return bool(K.vergleich("veranstaltungen.ausnahme_max", fakten.jahr, Decimal(fakten.veranstaltungszahl),
                                K.wert("veranstaltungen.ausnahme_max", fakten.jahr)))
    except (K.RegisterLuecke, KeyError, TypeError, ValueError):  # Jahr ohne Registerwert: wie bisher fragen
        return False
