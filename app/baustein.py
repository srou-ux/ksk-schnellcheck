"""Bausteinantwort mit Platzhaltern (Architektur Teil 1d).

Das Sprachmodell schreibt NUR Fliesstext mit Platzhaltern der Form `{NAME}`. Welche
Platzhalter in einer Antwort erlaubt sind, bestimmt ausschliesslich das Kernergebnis der
jeweiligen Anfrage (`erzeuge_platzhalter`, von `app/router.py` aufgerufen) -- es gibt keine
feste Liste im Code. Der Prompt an das Modell nennt nur die Namen und ihre Bedeutung
(`PLATZHALTER_BESCHREIBUNG`), nie die Werte.

`pruefe_rohtext` verwirft den Modelltext VOR dem Einsetzen, wenn er irgendetwas ausserhalb
der Platzhalter enthaelt, das eine Tatsachenbehauptung waere: Ziffern, §-Zeichen,
Aktenzeichen-Muster, "Regel-ID", Waehrungswoerter, "%", Zahlwoerter, Mengenangaben
("T€"/"Mio"/"Mrd"/"Prozent"), Normwoerter ausserhalb von Fundstellen-Platzhaltern,
Gerichtswoerter ausserhalb von Urteils-Platzhaltern, ausgeschriebene Fassungs-/Jahres-
Bezuege und Ergebnisaussagen (das System setzt die Ergebnis-Formulierung, nie das Modell).
Das schliesst die 6 Luecken aus `aufgaben/PROMPT_ClaudeCode_Chatbot_1d_Nachtrag.md`
(gefunden durch `aufgaben/audit/gegenproben_teil1c_umgehung.py`) sowie die 17 weiteren
Luecken aus `aufgaben/PROMPT_ClaudeCode_Chatbot_1d_Nachtrag2.md` (gefunden durch
`aufgaben/audit/gegenproben_teil1d_runde3.py`, siehe `aufgaben/PRUEFBERICHT_Chatbot_Teil1d.md`):
Schlussfolgerungen in anderen Worten, eigene Gewissheits-/Verbindlichkeitsbehauptungen,
Gerichte/Behoerden/Bestaetigungen namentlich, Links/Kontaktadressen, HTML-Tags, Markdown-
Ueberschriften und nach dem Einsetzen uebrig gebliebene geschweifte Klammern (verschachtelt
oder klein geschrieben). Wortlisten sind nie vollstaendig (Nachtrag 2, Abschnitt B) -- das
ist ein grundsaetzliches Problem von Blocklisten, kein Fehler dieser Umsetzung.

`fuelle` ersetzt die Platzhalter durch die vom Kern gelieferten Werte -- Betrags-/Prozent-
Formatierung einheitlich und zentral in `formatiere_betrag`/`formatiere_prozent`.

Die Pruefung aus Teil 1c (`app/pruefung.py::pruefe_antwort`) laeuft NACH dem Einsetzen
zusaetzlich weiter (zweites Netz, siehe app/router.py).
"""
from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

_KONFIG_PFAD = Path(__file__).resolve().parent / "baustein_konfiguration.json"
_KONFIG: dict[str, list[str]] = json.loads(_KONFIG_PFAD.read_text(encoding="utf-8"))


def _baue_wortmuster(morpheme: list[str]) -> re.Pattern[str]:
    return re.compile("|".join(morpheme), re.IGNORECASE)


_ZAHLWORT_MUSTER = _baue_wortmuster(_KONFIG["zahlwort_morpheme"])
_MENGENANGABE_MUSTER = _baue_wortmuster(_KONFIG["mengenangaben"])
_NORMWORT_MUSTER = _baue_wortmuster(_KONFIG["normwoerter"])
_GERICHTSWORT_MUSTER = _baue_wortmuster(_KONFIG["gerichtswoerter"])
_FASSUNGSWORT_MUSTER = _baue_wortmuster(_KONFIG["fassungswoerter"])
_ERGEBNISAUSSAGE_MUSTER = _baue_wortmuster(_KONFIG["ergebnisaussagen"])
# Nachtrag 2 (aufgaben/PROMPT_ClaudeCode_Chatbot_1d_Nachtrag2.md):
_GEWISSHEITSWORT_MUSTER = _baue_wortmuster(_KONFIG["gewissheitswoerter"])
_BESTAETIGUNGSWORT_MUSTER = _baue_wortmuster(_KONFIG["bestaetigungswoerter"])
_LINK_KONTAKT_MUSTER = _baue_wortmuster(_KONFIG["links_und_kontakt"])

PLATZHALTER_MUSTER = re.compile(r"\{([A-Z0-9_]+)\}")
_AKTENZEICHEN_MUSTER = re.compile(r"(?:\d\s*)?[A-Z]+\s*\d+\s*[A-Z]{0,3}\s*\d+/\d+(?:\s*[A-Z])?", re.IGNORECASE)
_WAEHRUNGSWORT_MUSTER = re.compile(r"\beuro\b|\beur\b", re.IGNORECASE)
# Nachtrag 2 Punkt A: rein strukturelle/syntaktische Muster (kein Wortlisten-Inhalt, daher
# hier und nicht in der Konfigurationsdatei -- derselbe Grund wie bei PLATZHALTER_MUSTER/
# _AKTENZEICHEN_MUSTER oben).
_HTML_TAG_MUSTER = re.compile(r"<[^>]+>")
_MARKDOWN_UEBERSCHRIFT_MUSTER = re.compile(r"^\s{0,3}#{1,6}\s", re.MULTILINE)

PLATZHALTER_BESCHREIBUNG: dict[str, str] = {
    "JAHR": "das Kalenderjahr, fuer das geprueft wird",
    "FASSUNG": "die KSVG-Fassung (A oder B) fuer dieses Jahr",
    "SUMME": "die vom Nutzer genannte Entgeltsumme",
    "SCHWELLE": "die fuer dieses Jahr geltende Geringfuegigkeitsgrenze",
    "ABGABESATZ": "der Abgabesatz des Jahres in Prozent",
    "BEMESSUNGSGRUNDLAGE": "die vom Kern berechnete Bemessungsgrundlage",
    "ABGABE": "die vom Kern berechnete Kuenstlersozialabgabe",
    "NICHT_ZUR_BEMESSUNGSGRUNDLAGE": "ein vom Kern ausgenommener Teilbetrag (z. B. Verpflegungspauschale)",
    "VORAUSZAHLUNG": "die vom Kern berechnete monatliche Vorauszahlung",
    "SUBSUMTION": "die Begruendung des Kerns in eigenen Worten (vom Kern vorformuliert)",
    "RUECKSTAND": "der vom Nutzer genannte Rueckstand (Saeumniszuschlag)",
    "MONATE": "die vom Nutzer genannte Anzahl Monate (Saeumniszuschlag)",
    "DATUM": "ein vom Kern berechnetes Datum (z. B. Meldefrist, Aufbewahrung)",
    "VERANSTALTUNGSGRENZE": "die Zahl der Veranstaltungen im Jahr, bis zu der die Ausnahme gilt (aus dem Regelregister)",
    "ABGABE_FALLS_MEHR": "die vom Kern berechnete Abgabe fuer den Fall, dass es mehr Veranstaltungen waren",
    "TAETIGKEIT_KUENSTLERISCH": "die vom System als kuenstlerisch/publizistisch eingeordneten Leistungen",
    "TAETIGKEIT_NICHT": "die vom System als nicht kuenstlerisch eingeordneten Leistungen",
    "TAETIGKEIT_NEBENLEISTUNG": "Leistungen, die als Nebenleistung oder Nebenkosten desselben Kuenstlers mitzaehlen",
    "TAETIGKEIT_UNSICHER": "die Leistungen, deren Einordnung der Steuerberater entscheiden muss",
    "ABGABE_FALLS_KUENSTLERISCH": "die vom Kern berechnete Abgabe, falls die unsicheren Leistungen mitzaehlen",
    "ABGABE_OHNE_UNSICHERE": "die vom Kern berechnete Abgabe ohne die unsicheren Leistungen",
    "AUFTRAGGEBER_PRIVAT": "die Art des Auftraggebers, wenn er eine Privatperson ist",
    "ZAHLUNGSWEG_UNKLAR": "Positionen mit Provision an einen Vermittler oder vertragswidrigem Zahlungsweg",
    "NACHFRAGE_VORGABE": "Kennzeichen: Nachricht verlangt ein anderes Ergebnis oder andere Regeln",
    "NACHFRAGE_PROTOKOLL": "Kennzeichen: Nachricht verlangt eine Zusammenfassung der Prüfung",
    "NACHFRAGE_ZAHLUNG_OFFEN": "Kennzeichen: eine Zahlung ist laut Nachricht noch offen",
    "NACHFRAGE_WIDERSPRUCH": "Kennzeichen: Nachricht widerspricht dem Ergebnis oder fragt warum",
    "EINSTIEG_OHNE_RECHNUNG": "Kennzeichen: Nachricht kündigt eine Rechnung an, enthält sie aber nicht",
    "VERTRAG_DIREKT": "Positionen mit Vertrag unmittelbar zwischen Mandant und Künstler",
    "PROVISION_OFFEN": "Provisionen an die Rechnungstellerin, deren Einordnung offen ist",
    "ABGABE_MIT_PROVISION": "die vom Kern berechnete Abgabe, falls die Provision mitzählt",
    "RECHNUNGSTELLER_GESELLSCHAFT": "die Rechtsform des Rechnungstellers, wenn er eine KG/OHG oder juristische Person ist",
    "FUNDSTELLE_n": "eine Fundstelle aus der Quellenbasis (laufend durchnummeriert)",
    "REGEL_n": "eine Regel-ID aus dem Regelkatalog (laufend durchnummeriert)",
    "NORM_n": "ein Gesetzes-/Verordnungszitat aus den gelieferten Regeln (laufend durchnummeriert)",
    "URTEIL_n": "ein Gerichtszitat (Gericht, Datum, Aktenzeichen) aus den gelieferten Regeln (laufend durchnummeriert)",
    "VERWALTUNGSPRAXIS_n": "ein KSK-/DRV-Praxishinweis aus den gelieferten Regeln (laufend durchnummeriert)",
    "RUECKFRAGE_n": "eine vom System formulierte Rueckfrage (laufend durchnummeriert)",
    "HINWEIS_n": "ein vom System formulierter Hinweis (laufend durchnummeriert)",
}


def formatiere_betrag(wert: Any) -> str:
    """Einzige Stelle fuer die Geldbetrag-Formatierung: Tausenderpunkt, Komma, zwei
    Nachkommastellen, '€'."""
    d = Decimal(str(wert))
    s = f"{d:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"


def formatiere_prozent(wert: Any) -> str:
    d = Decimal(str(wert))
    s = f"{d:f}".rstrip("0").rstrip(".") if "." in f"{d:f}" else f"{d:f}"
    s = s.replace(".", ",")
    return f"{s} %"


def erzeuge_platzhalter(kontext: Any) -> dict[str, str]:
    """Baut aus dem AntwortKontext (siehe app/llm/base.py) die Liste der fuer DIESE Anfrage
    erlaubten Platzhalter samt ihrem Wert. Nur was hier zurueckkommt, darf im Modelltext
    vorkommen -- die Liste ist pro Anfrage verschieden, es gibt keine feste Liste im Code."""
    werte: dict[str, str] = {}
    protokoll = kontext.kern_protokoll
    fakten = kontext.fakten

    if fakten.jahr is not None:
        werte["JAHR"] = str(fakten.jahr)
        from app.quellen import fassung_fuer_jahr

        # Das Wort "Fassung" steckt bewusst schon im WERT (system-/kern-generiert), nicht im
        # Modell-Template: Nachtrag Punkt 4 verbietet das Wort "Fassung" im Modelltext
        # ausserhalb des Platzhalters selbst -- als Label daneben waere es trotzdem verboten.
        # Teil 1f, Befund D: fassung_fuer_jahr liefert jetzt `None`, wenn das Register das
        # Jahr nicht abdeckt (kein Festwert mehr im Code) -- dann gibt es auch keinen
        # FASSUNG-Platzhalter (statt "Fassung None").
        fassung = fassung_fuer_jahr(fakten.jahr)
        if fassung:
            werte["FASSUNG"] = f"Fassung {fassung}"

    if fakten.positionen:
        werte["SUMME"] = formatiere_betrag(fakten.summe_positionen())
    elif fakten.gesamtbetrag_genannt is not None:
        werte["SUMME"] = formatiere_betrag(fakten.gesamtbetrag_genannt)

    # Teil 1f, Abschnitt B: Rueckstand/Monate sind vom Nutzer genannte, strukturierte
    # Fakten (wie SUMME aus Positionen) -- fuer die Saeumniszuschlag-Formulierung, damit
    # ABGABESATZ/ABGABEPFLICHTIG dafuer nicht gebraucht werden.
    if fakten.rueckstand is not None:
        werte["RUECKSTAND"] = formatiere_betrag(fakten.rueckstand)
    elif fakten.rueckstand_liste and len(fakten.rueckstand_liste) == 1:
        werte["RUECKSTAND"] = formatiere_betrag(fakten.rueckstand_liste[0])
    if fakten.saeumnis_monate is not None:
        werte["MONATE"] = str(fakten.saeumnis_monate)

    # SCHWELLE kommt NICHT unabhaengig aus app/quellen.py, sondern nur aus dem Kernergebnis
    # (app/router.py setzt sie nur, wenn der Kern sie in der eigenen Begruendung tatsaechlich
    # verwendet hat) -- sonst koennte hier eine fuer die konkrete Entscheidung irrelevante
    # Zahl auftauchen (z. B. bei der Drei-Veranstaltungen-Ausnahme, wo keine Schwelle zaehlt).
    if "schwelle" in protokoll:
        werte["SCHWELLE"] = formatiere_betrag(protokoll["schwelle"])

    if "abgabesatz_prozent" in protokoll:
        werte["ABGABESATZ"] = formatiere_prozent(protokoll["abgabesatz_prozent"])
    if "bemessungsgrundlage" in protokoll:
        werte["BEMESSUNGSGRUNDLAGE"] = formatiere_betrag(protokoll["bemessungsgrundlage"])
    if "bemessungsgrundlage_nach_pauschale" in protokoll:
        werte["BEMESSUNGSGRUNDLAGE"] = formatiere_betrag(protokoll["bemessungsgrundlage_nach_pauschale"])
    if "abgabe" in protokoll:
        werte["ABGABE"] = formatiere_betrag(protokoll["abgabe"])
    if "nicht_zur_bemessungsgrundlage" in protokoll:
        werte["NICHT_ZUR_BEMESSUNGSGRUNDLAGE"] = formatiere_betrag(protokoll["nicht_zur_bemessungsgrundlage"])
    if "vorauszahlung_monatlich" in protokoll:
        werte["VORAUSZAHLUNG"] = formatiere_betrag(protokoll["vorauszahlung_monatlich"])
    if "subsumtion" in protokoll:
        werte["SUBSUMTION"] = str(protokoll["subsumtion"])
    # Teil 1f, Abschnitt C: Auskunftsfragen mit einem Datum als Ergebnis (Meldefrist,
    # Aufbewahrung) -- fertig formatiert vom Router (app/router.py), kein eigenes Parsen hier.
    if "datum" in protokoll:
        werte["DATUM"] = str(protokoll["datum"])
    if "veranstaltungsgrenze" in protokoll:
        werte["VERANSTALTUNGSGRENZE"] = str(protokoll["veranstaltungsgrenze"])
    if "abgabe_falls_mehr" in protokoll:
        werte["ABGABE_FALLS_MEHR"] = formatiere_betrag(protokoll["abgabe_falls_mehr"])
    # Testfall 20 Positionen: Einordnung der Leistungen (System-Text aus app/taetigkeiten.py
    # bzw. der Excel) und die beiden vom Kern gerechneten Ausgänge bei unsicherer Leistung.
    for schluessel, name in (("taetigkeit_kuenstlerisch", "TAETIGKEIT_KUENSTLERISCH"),
                             ("taetigkeit_nicht", "TAETIGKEIT_NICHT"),
                             ("taetigkeit_nebenleistung", "TAETIGKEIT_NEBENLEISTUNG"),
                             ("taetigkeit_unsicher", "TAETIGKEIT_UNSICHER")):
        if protokoll.get(schluessel):
            werte[name] = str(protokoll[schluessel])
    if "abgabe_falls_kuenstlerisch" in protokoll:
        werte["ABGABE_FALLS_KUENSTLERISCH"] = formatiere_betrag(protokoll["abgabe_falls_kuenstlerisch"])
    if "abgabe_ohne_unsichere" in protokoll:
        werte["ABGABE_OHNE_UNSICHERE"] = formatiere_betrag(protokoll["abgabe_ohne_unsichere"])
    if "abgabe_mit_provision" in protokoll:
        werte["ABGABE_MIT_PROVISION"] = formatiere_betrag(protokoll["abgabe_mit_provision"])
    # Alltagsfälle 11.10.2026: Privatperson als Auftraggeber (F4), Rechnung einer Gesellschaft (F3).
    for schluessel, name in (("auftraggeber_privat", "AUFTRAGGEBER_PRIVAT"),
                             ("rechnungsteller_gesellschaft", "RECHNUNGSTELLER_GESELLSCHAFT"),
                             ("zahlungsweg_unklar", "ZAHLUNGSWEG_UNKLAR"),
                             ("vertrag_direkt", "VERTRAG_DIREKT"),
                             ("provision_offen", "PROVISION_OFFEN"),
                             ("nachfrage_vorgabe", "NACHFRAGE_VORGABE"),
                             ("nachfrage_protokoll", "NACHFRAGE_PROTOKOLL"),
                             ("nachfrage_zahlung_offen", "NACHFRAGE_ZAHLUNG_OFFEN"),
                             ("nachfrage_widerspruch", "NACHFRAGE_WIDERSPRUCH"),
                             ("einstieg_ohne_rechnung", "EINSTIEG_OHNE_RECHNUNG")):
        if protokoll.get(schluessel):
            werte[name] = str(protokoll[schluessel])

    # Fundstellen kommen bereits bereinigt an (app/router.py::_als_regel_eintrag ruft
    # app.quellen.bereinige_fundstelle auf, bevor eine Regel hier ankommt -- Teil 1f,
    # Befund D: ein Archiv-Kopie-Datum ist kein fuer die Anfrage gueltiges Jahr).
    for i, f in enumerate(kontext.fundstellen, start=1):
        werte[f"FUNDSTELLE_{i}"] = str(f)
    regel_ids = [r.get("regel_id") for r in kontext.regeln if r.get("regel_id")]
    for i, rid in enumerate(regel_ids, start=1):
        werte[f"REGEL_{i}"] = str(rid)
    urteile = [r for r in kontext.regeln if r.get("typ") == "urteil"]
    for i, r in enumerate(urteile, start=1):
        werte[f"URTEIL_{i}"] = str(r.get("fundstelle") or "")
    normen = [r for r in kontext.regeln if r.get("typ") == "gesetz"]
    for i, r in enumerate(normen, start=1):
        werte[f"NORM_{i}"] = str(r.get("fundstelle") or r.get("norm") or "")
    verwaltung = [r for r in kontext.regeln if r.get("typ") == "verwaltungspraxis"]
    for i, r in enumerate(verwaltung, start=1):
        werte[f"VERWALTUNGSPRAXIS_{i}"] = str(r.get("fundstelle") or "")
    for i, rf in enumerate(kontext.rueckfragen, start=1):
        werte[f"RUECKFRAGE_{i}"] = str(rf)
    for i, h in enumerate(kontext.hinweise, start=1):
        werte[f"HINWEIS_{i}"] = str(h)

    return {k: v for k, v in werte.items() if v}


def _pruefe_unbekannte_platzhalter(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    unbekannt = set(PLATZHALTER_MUSTER.findall(text)) - erlaubte_namen
    return f"Unbekannte Platzhalter: {sorted(unbekannt)}" if unbekannt else None


def _pruefe_ziffer(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    return "Ziffer ausserhalb eines Platzhalters" if re.search(r"\d", rest) else None


def _pruefe_paragraphzeichen(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    return "§-Zeichen ausserhalb eines Platzhalters" if "§" in rest else None


def _pruefe_aktenzeichen_roh(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    return "Aktenzeichen-Muster ausserhalb eines Platzhalters" if _AKTENZEICHEN_MUSTER.search(rest) else None


def _pruefe_regel_id_wort(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    return "'Regel-ID' ausserhalb eines Platzhalters" if re.search(r"regel[\s-]?id", rest, re.IGNORECASE) else None


def _pruefe_waehrungswort(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    return "Waehrungswort (Euro/EUR) ausserhalb eines Platzhalters" if _WAEHRUNGSWORT_MUSTER.search(rest) else None


def _pruefe_prozentzeichen(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    return "%-Zeichen ausserhalb eines Platzhalters" if "%" in rest else None


def _pruefe_zahlwort(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    return "Zahlwort ausserhalb eines Platzhalters (Nachtrag 1)" if _ZAHLWORT_MUSTER.search(rest) else None


def _pruefe_mengenangabe(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    if _MENGENANGABE_MUSTER.search(rest):
        return "Mengenangabe (T€/Mio/Mrd/Prozent) ausserhalb eines Platzhalters (Nachtrag 1)"
    return None


def _pruefe_normwort(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    if _NORMWORT_MUSTER.search(rest):
        return "Normbezug im Wortlaut ausserhalb eines Platzhalters (Nachtrag 2)"
    return None


def _pruefe_gerichtswort(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    if _GERICHTSWORT_MUSTER.search(rest):
        return "Gerichts-/Urteilswort ausserhalb eines Platzhalters (Nachtrag 3)"
    return None


def _pruefe_fassungswort(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    if _FASSUNGSWORT_MUSTER.search(rest):
        return "Fassung/Rechtslage im Wortlaut ausserhalb eines Platzhalters (Nachtrag 4)"
    return None


def _pruefe_ergebnisaussage(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    if _ERGEBNISAUSSAGE_MUSTER.search(rest):
        return "Ergebnisaussage im Modelltext (Nachtrag 5/2 B.1) -- das System setzt das Ergebnis"
    return None


def _pruefe_gewissheitswort(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    if _GEWISSHEITSWORT_MUSTER.search(rest):
        return "Eigene Gewissheits-/Verbindlichkeitsbehauptung im Modelltext (Nachtrag 2 B.2)"
    return None


def _pruefe_bestaetigungswort(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    if _BESTAETIGUNGSWORT_MUSTER.search(rest):
        return "Behauptete Pruefung/Bestaetigung/Offizialitaet im Modelltext (Nachtrag 2 A.2/B.3)"
    return None


def _pruefe_links_kontakt(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    if _LINK_KONTAKT_MUSTER.search(rest):
        return "Link oder Kontaktadresse im Modelltext (Nachtrag 2 A.2)"
    return None


def _pruefe_html_tag(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    if _HTML_TAG_MUSTER.search(rest):
        return "HTML-Tag im Modelltext (Nachtrag 2 A.2)"
    return None


def _pruefe_markdown_ueberschrift(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    if _MARKDOWN_UEBERSCHRIFT_MUSTER.search(rest):
        return "Markdown-Ueberschrift im Modelltext (Nachtrag 2 A.2) -- Ueberschriften setzt nur das System"
    return None


def _pruefe_geschweifte_klammer_uebrig(text: str, rest: str, erlaubte_namen: set[str]) -> str | None:
    """Nachtrag 2 A.1: nach dem Entfernen aller wohlgeformten {NAME}-Platzhalter (exakt
    Grossbuchstaben, einfach geklammert) darf keine geschweifte Klammer mehr uebrig sein.
    Das faengt sowohl verschachtelte/doppelte Klammern ('{{ABGABE}}', Fall d2 -- die aeussere
    Klammer bleibt nach dem Entfernen des inneren Treffers uebrig) als auch Klein- oder
    Grossschreibungs-Variationen ('{abgabe}', Fall d3 -- PLATZHALTER_MUSTER verlangt
    Grossbuchstaben und entfernt solche Treffer gar nicht erst aus `rest`)."""
    if "{" in rest or "}" in rest:
        return "Geschweifte Klammer nach Platzhalter-Erkennung uebrig (Nachtrag 2 A.1) -- verschachtelt oder falsch geschrieben"
    return None


# Jeder Eintrag: (text, rest_ohne_platzhalter, erlaubte_namen) -> Verstoss-Text oder None.
# `rest` wird fuer jeden Schritt einmal vorab berechnet (PLATZHALTER_MUSTER.sub(" ", text)),
# damit die Pruefung unabhaengig vom Rest der Pipeline bleibt. Fuer die Mutationsprobe
# (tests/app/test_gegenproben_2.py) wird jeder Eintrag einzeln per
# `unittest.mock.patch.dict(baustein.ROHTEXT_PRUEFSCHRITTE, {"<name>": lambda *a: None})`
# abgeschaltet; mindestens ein vorher blockierter Fall muss dann durchgehen.
ROHTEXT_PRUEFSCHRITTE: dict[str, Any] = {
    "unbekannte_platzhalter": _pruefe_unbekannte_platzhalter,
    "ziffer": _pruefe_ziffer,
    "paragraphzeichen": _pruefe_paragraphzeichen,
    "aktenzeichen": _pruefe_aktenzeichen_roh,
    "regel_id_wort": _pruefe_regel_id_wort,
    "waehrungswort": _pruefe_waehrungswort,
    "prozentzeichen": _pruefe_prozentzeichen,
    "zahlwort": _pruefe_zahlwort,
    "mengenangabe": _pruefe_mengenangabe,
    "normwort": _pruefe_normwort,
    "gerichtswort": _pruefe_gerichtswort,
    "fassungswort": _pruefe_fassungswort,
    "ergebnisaussage": _pruefe_ergebnisaussage,
    "gewissheitswort": _pruefe_gewissheitswort,
    "bestaetigungswort": _pruefe_bestaetigungswort,
    "links_kontakt": _pruefe_links_kontakt,
    "html_tag": _pruefe_html_tag,
    "markdown_ueberschrift": _pruefe_markdown_ueberschrift,
    "geschweifte_klammer_uebrig": _pruefe_geschweifte_klammer_uebrig,
}


def pruefe_rohtext(text: str, erlaubte_namen: set[str]) -> list[str]:
    """Prueft den Modelltext VOR dem Einsetzen. Leere Liste heisst: unbedenklich."""
    rest = PLATZHALTER_MUSTER.sub(" ", text)
    verstoesse: list[str] = []
    for schritt in ROHTEXT_PRUEFSCHRITTE.values():
        ergebnis = schritt(text, rest, erlaubte_namen)
        if ergebnis:
            verstoesse.append(ergebnis)
    return verstoesse


def fuelle(text: str, werte: dict[str, str]) -> str:
    def _ersetze(m: re.Match[str]) -> str:
        return werte.get(m.group(1), m.group(0))

    return PLATZHALTER_MUSTER.sub(_ersetze, text)
