"""Zuordnung der Anfrageart absichern (Chatbot Teil 1f, Nachtrag, Abschnitt A).

Hintergrund (Mistral-Lauf nach Teil 1f, aufgaben/audit/ergebnisse_mistral.md): das echte
Sprachmodell hat Anfragearten falsch gesetzt -- eine Rechnungsfrage mit Betrag wurde zu
"auskunft" ohne Thema, ein Verein mit Konzerten und Betraegen wurde zu "hinweis". Das
Modell darf diese Einstufung nicht ungeprueft bestimmen (siehe aufgaben/
SYSTEMBESCHREIBUNG_fuer_KI.md, Abschnitt 2: "Regeln erfinden" ist dem Modell verboten).

Diese Pruefung ist DETERMINISTISCH und unabhaengig vom jeweiligen Modell: sie laeuft nach
jeder Fakten-Extraktion (app/router.py::bearbeite_frage), bevor irgendetwas mit der
Anfrageart geschieht.
"""
from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path

from app.rechtsform_erkennung import erkenne_rechtsform_auftragnehmer
from app.schema import Fakten, Position

_KONFIG_PFAD = Path(__file__).resolve().parent / "auskunft_begriffe.json"
_KONFIG: dict[str, list[str]] = json.loads(_KONFIG_PFAD.read_text(encoding="utf-8"))
AUSKUNFT_BEGRIFFE: dict[str, list[str]] = {k: v for k, v in _KONFIG.items() if not k.startswith("_")}

_VERWERTERART_KONFIG_PFAD = Path(__file__).resolve().parent / "verwerterart_begriffe.json"
_VERWERTERART_KONFIG: dict[str, list[str]] = json.loads(_VERWERTERART_KONFIG_PFAD.read_text(encoding="utf-8"))
VERWERTERART_BEGRIFFE: dict[str, list[str]] = {k: v for k, v in _VERWERTERART_KONFIG.items() if not k.startswith("_")}
# Pruefkatalog-Befund M3: 'typischer_verwerter' hat beim Erkennen immer Vorrang -- ein
# typischer Verwerter (KSVG § 24 Abs. 1) hat keine Schwelle, unabhaengig vom Zweck der
# einzelnen Zahlung (auch wenn diese Zahlung fuer die eigene Werbung war).
_VERWERTERART_REIHENFOLGE = ("typischer_verwerter", "eigenwerber", "generalklausel")

_FALLWECHSEL_KONFIG_PFAD = Path(__file__).resolve().parent / "fallwechsel_begriffe.json"
FALLWECHSEL_BEGRIFFE: list[str] = json.loads(_FALLWECHSEL_KONFIG_PFAD.read_text(encoding="utf-8"))["neuer_fall"]

_ZIFFER_MUSTER = re.compile(r"\d")
_UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def _vereinheitliche(text: str) -> str:
    """Kleinschreibung, Umlaute als ae/oe/ue/ss, Leerraum zusammengefasst."""
    return " ".join(text.lower().translate(_UMLAUTE).split())


def ist_neuer_fall(frage: str) -> bool:
    """Dialogtest Fallgrenzen (10.10.2026): Kündigt die Nachricht AUSDRÜCKLICH einen neuen,
    unabhängigen Fall an ('Neuer, unabhängiger Fall: ...'), darf nichts aus dem bisherigen
    Fall übernommen werden -- weder gespeicherte Sitzungsfakten noch Verlaufstext. Vorher
    übernahm app/router.py::_fakten_zusammenfuehren z. B. Jahr, Verwerterart und sogar die
    Rechnungspositionen des alten Falls, weil die neue Extraktion dafür (richtig) null
    lieferte. Deterministisch über eine Begriffsliste (app/fallwechsel_begriffe.json)."""
    text = _vereinheitliche(frage)
    return any(_vereinheitliche(b) in text for b in FALLWECHSEL_BEGRIFFE)


def _enthaelt_begriff(text: str, begriffe: list[str]) -> bool:
    text_klein = text.lower()
    return any(b.lower() in text_klein for b in begriffe)


def _enthaelt_begriff_als_wort(text: str, begriffe: list[str]) -> bool:
    """Wie `_enthaelt_begriff`, aber mit Wortgrenzen (`\\b`) -- fuer Begriffe, die sonst als
    Teil eines deutschen Kompositums faelschlich treffen wuerden (z. B. das einzelne Wort
    'orchester' in 'Hobbyorchester-Verein'; Pruefkatalog-Befund, Fall P-16)."""
    text_klein = text.lower()
    return any(re.search(r"\b" + re.escape(b.lower()) + r"\b", text_klein) for b in begriffe)


def _auskunft_thema_passt(frage: str, thema: str | None) -> bool:
    """`auskunft` gilt nur, wenn die Nutzerfrage SELBST einen Begriff zum vom Modell
    gelieferten Thema nennt -- sonst koennte das Modell aus einer ganz anderen Frage
    (z. B. einer Rechnungsfrage mit Betrag) frei ein Auskunftsthema erfinden."""
    if thema is None or thema not in AUSKUNFT_BEGRIFFE:
        return False
    return _enthaelt_begriff(frage, AUSKUNFT_BEGRIFFE[thema])


def _enthaelt_sachangabe(frage: str) -> bool:
    """`hinweis` (Begruessung/Smalltalk) gilt nur, wenn die Eingabe KEINE Sachangabe
    enthaelt: keine Ziffer (deckt Jahreszahl und Betrag ab) und keinen Fachbegriff aus
    der Auskunfts-Begriffsliste (Konfiguration, kein Festwert im Code)."""
    if _ZIFFER_MUSTER.search(frage):
        return True
    alle_begriffe = [b for liste in AUSKUNFT_BEGRIFFE.values() for b in liste]
    return _enthaelt_begriff(frage, alle_begriffe)


def absichere_anfrageart(frage: str, fakten: Fakten) -> Fakten:
    """Verwirft eine vom Modell gelieferte Anfrageart "auskunft"/"hinweis", wenn die
    deterministische Pruefung dagegen spricht -- die Anfrage faellt dann auf den
    Standardfall "bewertung" zurueck (Rueckfrage nach den fuer die Pruefung fehlenden
    Angaben, siehe app/pflichtangaben.py), statt eine falsche Auskunft/Begruessung
    auszugeben."""
    if fakten.anfrageart == "auskunft" and not _auskunft_thema_passt(frage, fakten.auskunft_thema):
        return fakten.model_copy(update={"anfrageart": None, "auskunft_thema": None})
    if fakten.anfrageart == "auskunft" and betraege_im_text(frage):
        # Korpus-Lauf 15.10.2026 (gestörte Fakten, 18 FALSCH): eine Zahlung mit Euro-Betrag wurde als Auskunft zum
        # Abgabesatz beantwortet. Nennt der Text einen Euro-Betrag, ist es keine reine Auskunft: bewerten bzw. nachfragen.
        return fakten.model_copy(update={"anfrageart": None, "auskunft_thema": None})
    if fakten.anfrageart == "hinweis" and _enthaelt_sachangabe(frage):
        return fakten.model_copy(update={"anfrageart": None})
    # Härtetest HT-2026-011 (14.10.2026, 1 von 6 Läufen): der Text verlangt ein bestimmtes BSG-Urteil als Beleg,
    # das Modell machte daraus eine reine Rechtsprechungsfrage -- die konkrete Zahlung (3.400 € an einen Autor)
    # wurde nicht bewertet ('Nicht abgedeckt'). Hat das Modell eine Zahlung als Position erkannt, deren Betrag so
    # im Text steht, wird die Zahlung bewertet; die verlangte Fundstelle prüft das System ohnehin selbst.
    # Alltagstest AT-2026-060: Auskunftsfrage ohne Betrag ('welche Grenze gilt 2026?'), vom Modell als Bewertung gelesen.
    if (fakten.anfrageart in (None, "bewertung") and "?" in frage and not fakten.positionen
            and fakten.gesamtbetrag_genannt is None and not fakten.leistungsart and not betraege_im_text(frage)):
        themen = [th for th, begriffe in AUSKUNFT_BEGRIFFE.items() if _enthaelt_begriff(frage, begriffe)]
        if len(themen) == 1:
            return fakten.model_copy(update={"anfrageart": "auskunft", "auskunft_thema": themen[0]})
    if (fakten.anfrageart == "rechtsprechungsfrage" and fakten.positionen
            and any(p.betrag in betraege_im_text(frage) for p in fakten.positionen)):
        return fakten.model_copy(update={"anfrageart": None})
    return fakten


def eigenwerbung_muster(text: str) -> str | None:
    """Siehe app/verwerterart_begriffe.json, '_eigenwerber_muster': die Wendung im Wortlaut des Textes, oder None."""
    regel = _VERWERTERART_KONFIG.get("_eigenwerber_muster") or {}
    for satz in _SATZGRENZE.split(text):
        klein = satz.lower()
        if not any(w in klein for w in regel.get("werbewort", [])):
            continue
        for muster in regel.get("muster", []):
            m = re.search(muster, klein)
            if m:
                return satz[m.start():m.end()]
    return None


def _erkenne_verwerterart(text: str) -> str | None:
    """Liefert die per Begriffsliste (app/verwerterart_begriffe.json) erkannte verwerterart
    aus Freitext, oder `None`. 'typischer_verwerter' wird zuerst geprueft (Vorrang)."""
    for wert in _VERWERTERART_REIHENFOLGE:
        if _enthaelt_begriff_als_wort(text, VERWERTERART_BEGRIFFE.get(wert, [])):
            return wert
        if wert == "eigenwerber" and eigenwerbung_muster(text):
            return wert
    return None


_PRIVAT_KONFIG = json.loads((Path(__file__).resolve().parent / "privat_begriffe.json").read_text(encoding="utf-8"))
_SATZGRENZE = re.compile(r"(?<=[.!?])\s+|[;\n]")


def privater_auftraggeber(text: str) -> bool:
    """Alltagsfälle 11.10.2026 (F4): nennt der Text ausdrücklich eine Privatperson als
    AUFTRAGGEBER? Je Satz: ein Begriff aus 'privat' und ein Auftraggeber-Hinweis, kein Begriff
    aus 'nicht_wenn' (app/privat_begriffe.json). 'Privatperson' allein beschreibt oft den
    Auftragnehmer und zählt deshalb nicht."""
    for satz in _SATZGRENZE.split(text.lower()):
        if (_enthaelt_begriff(satz, _PRIVAT_KONFIG["privat"])
                and _enthaelt_begriff(satz, _PRIVAT_KONFIG["auftraggeber"])
                and not _enthaelt_begriff(satz, _PRIVAT_KONFIG["nicht_wenn"])):
            return True
    return False


_NAME_IN_ZEICHEN = re.compile(r"(?<![\w])['\"„‚‘“]([^'\"„‚‘“”’\n]{1,60})['\"“”‘’](?![\w])")


def _ohne_namen(text: str) -> str:
    """Text ohne Namen in Anführungszeichen ('Galerie Hoffmann', „Verlag am See“): ein Wort darin beschreibt
    nicht die Art des Unternehmens (HT-2026-072)."""
    return _NAME_IN_ZEICHEN.sub(" ", text)


def absichere_verwerterart(text: str, fakten: Fakten) -> Fakten:
    """Pruefkatalog-Befunde M3/M4 (aufgaben/PROMPT_ClaudeCode_Chatbot_Pruefkatalog1_Befunde.md):
    `verwerterart` wird GEGENGEPRUEFT, nicht blind vom Modell uebernommen. `text` ist Verlauf
    und aktuelle Nachricht zusammen (siehe app/router.py::bearbeite_frage).

    M3: nennt der Text selbst einen Begriff fuer 'typischer_verwerter' (z. B. 'Verlag',
    'Werbeagentur'), gewinnt das immer -- auch gegen einen vom Modell gelieferten
    'eigenwerber'. Hintergrund: ein Verlag, der Flyer fuer die eigene Werbung gestalten
    laesst, bleibt ein typischer Verwerter (KSVG § 24 Abs. 1, keine Schwelle); die
    Eigenwerbungs-Schwelle (§ 24 Abs. 2 S. 1 Nr. 1) gilt nur fuer Unternehmen, die KEIN
    typischer Verwerter sind.
    M4: ein vom Modell gelieferter Wert wird nur dann verworfen, wenn der Text selbst einen
    ANDEREN, WIDERSPRECHENDEN Begriff nennt (z. B. Modell sagt 'typischer_verwerter', der
    Text belegt aber nur 'eigenwerber') -- fehlt im Text jeder Begriff (`erkannt is None`),
    bleibt ein bereits gesetzter Wert unangetastet. Eine reine Abwesenheit von Schluesselwoertern
    ist kein Widerspruch: viele Nachrichten (gerade kurze Rueckfrage-Antworten) nennen den
    Begriff nicht noch einmal, obwohl er an anderer Stelle im Dialog schon geklaert ist."""
    erkannt = _erkenne_verwerterart(_ohne_namen(text))
    # Fehlerquellen-Serie HT-2026-072 (live 15.10.2026): "Die 'Galerie Hoffmann' (Verein, … ein Schreinerverein)" --
    # das Wort steht nur im NAMEN. Belegt allein ein Name in Anführungszeichen den typischen Verwerter, ist ein
    # entsprechender Modellwert nicht belegt und wird verworfen (dann fragt das System).
    if (fakten.verwerterart == "typischer_verwerter" and erkannt != "typischer_verwerter"
            and _erkenne_verwerterart(text) == "typischer_verwerter"):
        fakten = fakten.model_copy(update={"verwerterart": None})
    # Alltagsfälle 11.10.2026 (F4): Privatperson als Auftraggeber nur mit Beleg im Text und nur,
    # wenn der Text keine andere Art nennt; einen unbelegten Modellwert 'privat' verwerfen.
    privat = privater_auftraggeber(text)
    if privat and erkannt is None:
        return fakten if fakten.verwerterart == "privat" else fakten.model_copy(update={"verwerterart": "privat"})
    if fakten.verwerterart == "privat" and not privat:
        return fakten.model_copy(update={"verwerterart": None})
    if erkannt == "typischer_verwerter" and fakten.verwerterart != "typischer_verwerter":
        return fakten.model_copy(update={"verwerterart": "typischer_verwerter"})
    # Testprotokoll 11.10.2026: 'ausschließlich für unsere eigene Werbung' / 'Wir betreiben
    # ausschließlich Eigenwerbung' -- das Modell setzte verwerterart nie, und das System fragte
    # immer wieder. Eine ausdrückliche Eigenwerbung im Text ergänzt den fehlenden Wert
    # (Generalklausel/Veranstalter bewusst nicht: 'Konzertveranstalter' ist ein typischer Verwerter).
    if erkannt == "eigenwerber" and fakten.verwerterart is None:
        return fakten.model_copy(update={"verwerterart": "eigenwerber"})
    if erkannt is not None and fakten.verwerterart is not None and fakten.verwerterart != erkannt:
        return fakten.model_copy(update={"verwerterart": None})
    return fakten


_BETRAG_NACH_ZAHL = re.compile(r"\s*(€|eur\b|euro)", re.IGNORECASE)


def jahr_nicht_aus_betrag(text: str, fakten: Fakten) -> Fakten:
    """Livetest 10.10.2026 (Dialog nachgespielt, mistral-small-latest): Auf die Antwort
    '2000 euro' setzte das Modell jahr = 2000 -- und die Sitzung überschrieb damit das per
    Knopf gewählte Jahr 2026. Eine Zahl, die im Text NUR als Geldbetrag vorkommt (direkt
    gefolgt von '€', 'EUR' oder 'Euro'), ist nie ein Jahr: dann wird `jahr` verworfen (die
    Sitzung behält ihren bisherigen Wert; fehlt einer, fragt das System nach)."""
    if fakten.jahr is None:
        return fakten
    vorkommen = list(re.finditer(rf"(?<![\d.,]){fakten.jahr}(?![\d.,]\d)", text))
    if vorkommen and all(_BETRAG_NACH_ZAHL.match(text, m.end()) for m in vorkommen):
        return fakten.model_copy(update={"jahr": None})
    return fakten


def gesamtbetrag_nicht_als_position(fakten: Fakten) -> Fakten:
    """Dialogtest Fallgrenzen (Live-Lauf 10.10.2026, mistral-small-latest): Bei 'insgesamt
    500 Euro, Aufteilung unbekannt' setzte das Modell neben gesamtbetrag_genannt = 500 in 4
    von 10 Extraktionen zusätzlich EINE Position über 500 € -- eine Rechnung, die nie genannt
    wurde. Eine einzige Position, deren Betrag genau dem genannten Gesamtbetrag entspricht und
    die nichts Eigenes trägt (keine Sonderrolle, kein Nachweis-/Künstlerisch-Merkmal), ist
    keine Aufteilung: sie wird entfernt, es bleibt beim Gesamtbetrag. Eine eigene Rechtsform
    der Position wird als allgemeine Rechtsform übernommen, wenn keine gesetzt ist. Rechnet
    nichts um: Summe und Kernergebnis bleiben gleich, nur die Darstellung ist ehrlich."""
    if fakten.gesamtbetrag_genannt is None or len(fakten.positionen) != 1:
        return fakten
    p = fakten.positionen[0]
    if p.betrag != fakten.gesamtbetrag_genannt or p.rolle not in (None, "honorar"):
        return fakten
    if p.nachgewiesen is not None or p.kuenstlerisch is not None or p.rechnungsrolle is not None:
        return fakten
    return fakten.model_copy(update={
        "positionen": [],
        "auftragnehmer_typ": fakten.auftragnehmer_typ or p.auftragnehmer_typ,
    })


def gesamtbetrag_mit_rolle(text: str, fakten: Fakten) -> Fakten:
    """Siehe app/rollen_belege.json, '_hinweis_gesamtbetrag'. Unabhängig vom Sprachmodell."""
    if fakten.positionen or fakten.gesamtbetrag_genannt is None:
        return fakten
    from app.textnorm import waehrung_nach_hinten

    t = waehrung_nach_hinten(text)
    betrag = fakten.gesamtbetrag_genannt
    if sorted(b for b in [*_alle_betraege(t)] if b == betrag) != [betrag]:
        return fakten
    passend = [r for r in _ROLLEN_KONFIG.get("_gesamtbetrag_als_rolle", [])
               if betrag in _betraege_am_begriff(t, _ROLLEN_BELEGE.get(r, []), wortende=True)]
    if len(passend) != 1:
        return fakten
    return fakten.model_copy(update={"gesamtbetrag_genannt": None, "positionen": [
        Position(betrag=betrag, rolle=passend[0], bezeichnung=fakten.leistungsart or "Zahlung laut Text",
                 auftragnehmer_typ=fakten.auftragnehmer_typ)]})


def _alle_betraege(text: str) -> list:
    """Alle Euro-Beträge im Text, mit Wiederholungen (betraege_im_text liefert eine Menge)."""
    return [Decimal(m.group(1).replace(".", "") + (f".{m.group(2)}" if m.group(2) else ""))
            for m in _BETRAG_IM_TEXT.finditer(text)]


def ergaenze_rechtsform(text: str, fakten: Fakten) -> Fakten:
    """Pruefkatalog-Befund M1.3: erkennt Rechtsform-Synonyme ('Einzelperson',
    'freiberuflich', ...) deterministisch aus dem Nutzertext, WENN das Modell
    `auftragnehmer_typ` (global oder bei genau einer Position) nicht selbst gesetzt hat --
    wie im Demo-Modus (app/llm/fake.py), hier aber fuer JEDES Modell (auch Mistral)
    nachgeschaltet. Bei mehreren Positionen ohne eigene Rechtsform wird NICHT geraten,
    welche Position gemeint ist -- dort bleibt es bei der gezielten Rueckfrage je Position
    (app/pflichtangaben.py).

    Seit der Prüfung gegen die Playground-Fälle (10.10.2026) nur noch Rechtsformen, die den
    AUFTRAGNEHMER beschreiben ('Wir sind eine GmbH', 'unser Verein' zählen nicht) und nur,
    wenn genau eine übrig bleibt (app/rechtsform_erkennung.py::erkenne_rechtsform_auftragnehmer)."""
    erkannt = erkenne_rechtsform_auftragnehmer(text)
    if erkannt is None:
        return fakten
    if fakten.auftragnehmer_typ is None and not fakten.positionen:
        return fakten.model_copy(update={"auftragnehmer_typ": erkannt})
    if (
        fakten.auftragnehmer_typ is None
        and len(fakten.positionen) == 1
        and fakten.positionen[0].auftragnehmer_typ is None
    ):
        neue_position = fakten.positionen[0].model_copy(update={"auftragnehmer_typ": erkannt})
        return fakten.model_copy(update={"positionen": [neue_position]})
    return fakten


_ALLGEMEINE_BEZEICHNUNGEN = {"honorar", "gage", "verguetung", "entgelt", "leistung", "honorarrechnung", "auftrag"}


def _allgemeine_bezeichnung(p) -> bool:
    if not p.bezeichnung:
        return p.rolle == "honorar"
    if p.rest and not p.rolle:
        # Schritt 2 (Live 14.10.2026, P-28): der Rest einer Rechnung ('Honorar inkl. Umsatzsteuer')
        # ist der Hauptteil der Leistung -- wie 'Honorar' (die feste Erkennung geht trotzdem vor).
        return True
    return _vereinheitliche(p.bezeichnung).strip(" .:") in _ALLGEMEINE_BEZEICHNUNGEN


def ergaenze_taetigkeit(text: str, fakten: Fakten) -> Fakten:
    """Testfall 20 Positionen (11.10.2026): ordnet jeder Position (bzw. dem Gesamtbetrag) eine
    Tätigkeit aus dem Excel-Blatt 'Tätigkeitsabgrenzung' zu (app/taetigkeiten.py).

    Grundlage je Position ist ihre eigene Bezeichnung. Den ganzen Nutzertext und die
    `leistungsart` nur, wenn es genau eine Position oder nur einen Gesamtbetrag gibt -- bei
    mehreren Positionen wäre sonst nicht klar, welche Position gemeint ist. Die Wahl des
    Modells (`taetigkeit_id`) und die feste Erkennung über die Begriffe der Excel müssen
    übereinstimmen; widersprechen sie sich, entscheidet der Steuerberater (Grenzfall)."""
    from app import taetigkeiten as T

    if (fakten.anfrageart or "bewertung") != "bewertung":
        return fakten
    if fakten.positionen:
        # Schritt 2 (Live-Messung 14.10.2026, P-04a): fünf Positionen 'kleine Werbegrafiken' sind EINE
        # Art von Leistung -- wie bei einer einzelnen Position gelten dann auch die genannte Leistung
        # des Auftragnehmers ('Grafik/Design') und die Wahl des Modells. Nur bei gleicher, nicht
        # leerer Bezeichnung aller Positionen.
        bezeichnungen = {(p.bezeichnung or "").strip().lower() for p in fakten.positionen}
        einzeln = len(fakten.positionen) == 1 or (len(bezeichnungen) == 1 and "" not in bezeichnungen)
        neue = []
        for p in fakten.positionen:
            erkannt = T.erkenne(p.bezeichnung)
            if erkannt is None and not einzeln and _allgemeine_bezeichnung(p):
                # 'Honorar' sagt nichts über die Leistung -- dann gilt die genannte Tätigkeit
                # des Auftragnehmers ('Ein Illustrator hat ... 3.000 € Honorar ... berechnet').
                erkannt = T.erkenne(fakten.leistungsart)
                if erkannt is None and T.gruppen_im_text(text) == {"kuenstlerisch"}:
                    # Prüfkatalog P-30 (live, schwankend): ohne leistungsart vom Modell blieb das
                    # 'Honorar' des 'freien Designers' uneingeordnet (Grenzfall). Nennt der ganze
                    # Text nur künstlerische Tätigkeiten, gilt diese Einordnung für das Honorar.
                    erkannt = T.erkenne(text)
            if erkannt is None and einzeln:
                # leistungsart und Text gemeinsam, damit der Vorrang der Excel gilt (ein
                # allgemeines 'Text/Redaktion' darf ein genanntes 'Korrektorat' nicht verdecken).
                erkannt = T.erkenne(f"{fakten.leistungsart or ''}\n{text}")
            elif erkannt is not None and einzeln and p.taetigkeit_id:
                # 14.10.2026 (P-02, 16 von 16 Läufen Grenzfall): die Bezeichnung 'Website Gestaltung und
                # Programmierung' allein ergibt T-30 (reine Programmierung); der Text ('Webdesigner') und
                # das Modell sagen T-01 (Webdesign, auch mit Programmierung; R-142, R-184). Bei EINER
                # Position gilt die Einordnung aus Bezeichnung + Leistung + Text, wenn sie laut Excel
                # VORRANG vor der Einordnung der Bezeichnung hat UND das Modell unabhängig dasselbe sagt.
                # Sonst bleibt es beim Widerspruch (Steuerberater entscheidet).
                gesamt = T.erkenne(f"{p.bezeichnung or ''}\n{fakten.leistungsart or ''}\n{text}")
                if (T.gueltige_id(gesamt) and gesamt == p.taetigkeit_id
                        and (erkannt == T.WIDERSPRUCH or T.nach_id(gesamt)["vorrang"] < T.nach_id(erkannt)["vorrang"])):
                    erkannt = gesamt
            beschrieben = bool(p.bezeichnung) or (einzeln and bool(fakten.leistungsart))
            modell = p.taetigkeit_id or (fakten.taetigkeit_id if einzeln else None)
            neue.append(p.model_copy(update={"taetigkeit_id": T.kombiniere(modell, erkannt, beschrieben)}))
        fakten = fakten.model_copy(update={"positionen": neue})
        if not einzeln:
            # Vorgabe für Positionen ohne eigene Angabe nur aus einer klaren Gesamtangabe; den
            # ganzen Text nur, wenn KEINE Position eine eigene Bezeichnung hat ('vier Rechnungen
            # von Musikern über je 1.500 €').
            erkannt = T.erkenne(fakten.leistungsart)
            if erkannt is None and not any(p.bezeichnung for p in fakten.positionen):
                # Nur eine künstlerische Einordnung des ganzen Textes gilt für alle Positionen.
                # Eine nicht künstlerische nicht: 'Gestaltung 1.200 € und Druck 800 €' würde
                # sonst beide Positionen als Druck ausschließen (Prüfkatalog P-32).
                aus_text = T.erkenne(text)
                erkannt = aus_text if T.gruppe(aus_text) == "kuenstlerisch" else None
            vorgabe = T.kombiniere(fakten.taetigkeit_id, erkannt, bool(fakten.leistungsart))
            if (not any(p.bezeichnung for p in fakten.positionen)
                    and len(T.gruppen_im_text(f"{fakten.leistungsart or ''}\n{text}")) > 1):
                # Mehrere Positionen ohne Bezeichnung, der Text nennt aber Leistungen
                # verschiedener Gruppen ('Webdesign ..., Druckkosten ...'): eine Vorgabe für
                # alle Positionen wäre geraten -- der Steuerberater entscheidet.
                vorgabe = T.WIDERSPRUCH
            return fakten.model_copy(update={"taetigkeit_id": vorgabe})
        return fakten.model_copy(update={"taetigkeit_id": None})
    erkannt = T.erkenne(f"{fakten.leistungsart or ''}\n{text}")
    return fakten.model_copy(update={
        "taetigkeit_id": T.kombiniere(fakten.taetigkeit_id, erkannt, bool(fakten.leistungsart))})


_ROLLEN_KONFIG: dict = json.loads((Path(__file__).resolve().parent / "rollen_belege.json").read_text(encoding="utf-8"))
_ROLLEN_BELEGE: dict = {k: v for k, v in _ROLLEN_KONFIG.items() if not k.startswith("_")}
_NACHWEIS_NOETIG: dict = {k: v for k, v in _ROLLEN_KONFIG.get("_nachweis_noetig", {}).items() if not k.startswith("_")}


def _nachweis_fehlt(text: str, p) -> bool:
    """Alltagsfälle 11.10.2026 (F2): eine Rolle, die einen NACHWEIS voraussetzt (nachgewiesene
    Reisekosten, R-47), gilt nicht für eine Pauschale und nicht ohne Nachweis-Begriff im Text."""
    regel = _NACHWEIS_NOETIG.get(p.rolle or "")
    if not regel:
        return False
    if p.bezeichnung and _enthaelt_begriff(_vereinheitliche(p.bezeichnung),
                                           [_vereinheitliche(b) for b in regel["nicht_wenn_bezeichnung"]]):
        return True
    t = _vereinheitliche(text)
    bejaht, verneint = _nachweis_im_text(t, regel)
    if verneint and not bejaht:
        return True  # nur verneint genannt ('keine Belege', 'ohne Nachweis'): kein Nachweis, egal was das Modell sagt
    if p.nachgewiesen:
        return False
    return not bejaht


def _nachweis_im_text(t: str, regel: dict) -> tuple[bool, bool]:
    """(bejaht, verneint): kommt ein Nachweis-Begriff ohne bzw. mit Verneinung vor? (app/rollen_belege.json)"""
    davor = [_vereinheitliche(w) for w in regel.get("verneinung_davor", [])]
    danach = [_vereinheitliche(w) for w in regel.get("verneinung_danach", [])]
    bejaht = verneint = False
    for b in regel["nachweis"]:
        for m in re.finditer(r"(?<![0-9a-z])" + re.escape(_vereinheitliche(b)), t):
            vorher, nachher = t[max(0, m.start() - 25):m.start()], t[m.end():m.end() + 25]
            if _enthaelt_begriff(vorher, davor) or any(nachher.lstrip().startswith(w) or f" {w}" in nachher[:len(w) + 12]
                                                        for w in danach):
                verneint = True
            else:
                bejaht = True
    return bejaht, verneint


def _gueltige_rollen() -> set[str]:
    from kern import rechnen as K

    return set(K._AUSSCHLUSSGRUENDE) | {"honorar"}


_GUELTIGE_ROLLEN = _gueltige_rollen()


def _betraege_am_begriff(text: str, begriffe: list[str], wortende: bool = False) -> set:
    """Beträge, die im Text höchstens 30 Zeichen vor oder nach einem der Begriffe stehen. Mit `wortende` zählt ein Begriff
    nur als ganzes Wort (mit Endung -n/-en/-s): 'gema' nicht in 'gemacht' (test_fehlerquellen HT-074)."""
    from decimal import Decimal

    t = _vereinheitliche(text)
    betraege = list(re.finditer(r"(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{1,2}))?\s*(?:€|eur\b|euro)", t))
    # Live 14.10.2026 (P-52 FALSCH): '… Kamera-Equipment 200 € netto, Druckkosten … 500 € netto' -- das
    # 'Druck' des NÄCHSTEN Listenteils galt als Beleg für die 200 €. Listenteile trennt ein Komma (nicht
    # zwischen Ziffern), Semikolon oder Zeilenumbruch. Ein Beleg-Wort in einem anderen Listenteil zählt
    # nicht, wenn dort ein eigener Betrag steht ('nachgewiesen durch Ticket' ohne Betrag zählt weiter).
    grenzen = [g.start() for g in re.finditer(r"(?<!\d),|,(?!\d)|[;\n]", t)]

    def teil(pos: int) -> int:
        return sum(1 for g in grenzen if g < pos)

    teil_mit_betrag = {teil(b.start()) for b in betraege}
    ende = r"(?:en|n|s)?(?![0-9a-zäöüß])" if wortende else ""
    muster = [re.compile(r"(?<![0-9a-z])" + re.escape(_vereinheitliche(b)) + ende) for b in begriffe]
    ergebnis = set()
    for m in betraege:
        betrag = Decimal(m.group(1).replace(".", "") + (f".{m.group(2)}" if m.group(2) else ""))
        von, bis = max(0, m.start() - 30), m.end() + 30
        eigener = teil(m.start())
        for mu in muster:
            if any(teil(von + w.start()) == eigener or teil(von + w.start()) not in teil_mit_betrag
                   for w in mu.finditer(t[von:bis])):
                ergebnis.add(betrag)
                break
    return ergebnis


def ergaenze_rolle_darin(text: str, fakten: Fakten) -> Fakten:
    """Schritt 2 (Live-Messung 14.10.2026, P-28): '1.190 € brutto, darin 190 € Umsatzsteuer' -- das
    Modell legte die 190 € ohne Rolle an; sie zählten als Honorar (Grenzfall statt Ergebnis). Eine
    Sonderrolle wird ERGÄNZT nur, wenn (1) der Betrag der Position im Text als enthaltener Teil steht
    ('darin/davon/einschließlich … 190 €'), (2) ein Beleg-Wort genau EINER Rolle direkt bei diesem
    Betrag steht (app/rollen_belege.json) und (3) dasselbe Wort in der Bezeichnung der Position
    steht. Danach prüft absichere_rollen wie immer (z. B. Nachweis bei Reisekosten)."""
    enthalten = {y for _x, y in _davon_paare(text)}
    if not enthalten or not any(p.rolle is None and p.betrag in enthalten for p in fakten.positionen):
        return fakten
    neue = []
    for p in fakten.positionen:
        if p.rolle is None and p.betrag in enthalten and p.bezeichnung:
            bez = _vereinheitliche(p.bezeichnung)
            passend = [rolle for rolle, begriffe in _ROLLEN_BELEGE.items()
                       if p.betrag in _betraege_am_begriff(text, begriffe)
                       and any(re.search(r"(?<![0-9a-z])" + re.escape(_vereinheitliche(b)), bez) for b in begriffe)]
            if len(passend) == 1:
                p = p.model_copy(update={"rolle": passend[0]})
        neue.append(p)
    return fakten.model_copy(update={"positionen": neue})


def fehlender_enthaltener_teil(text: str, fakten: Fakten) -> Fakten:
    """Live-Läufe 16.10.2026 (F04, KB-0491/0521, Modellfehler-Protokoll): '1.071,00 Euro brutto gezahlt, darin 171 EUR
    Umsatzsteuer' -- das Modell legte den GANZEN Betrag (1.071) als Umsatzsteuer an und ließ die 171 € weg (dazu oft ein
    leerer Rest). Ergebnis war die Rückfrage 'Teilbetrag so hoch wie die ganze Rechnung'. Nennt der Text genau EIN
    'X … darin Y', fehlt Y in den Fakten ganz, gibt es genau eine Position über X (ein Auftragnehmer) und steht bei Y das
    Beleg-Wort genau EINER Rolle (app/rollen_belege.json), wird Y als eigene Position mit dieser Rolle ergänzt; X verliert
    diese Rolle (der ganze Betrag kann nicht zugleich der enthaltene Teil sein). Beide Beträge stehen so im Text; den Rest
    rechnet wie immer der Kern (berechne_restpositionen). Nichts wird geschätzt."""
    from app.schema import Position
    from app.textnorm import waehrung_nach_hinten

    if (fakten.anfrageart or "bewertung") != "bewertung":
        return fakten
    t = waehrung_nach_hinten(text)
    paare = _davon_paare(t)
    # Korpus mit Small (17.10.2026, F04, z. B. KB-0498): nur ein Gesamtbetrag über X (brutto), keine Positionen -- die
    # enthaltene Umsatzsteuer fehlte, X zählte ganz. Dann wird X zur Position (wie es im Text steht); unten wird Y ergänzt.
    if (not fakten.positionen and fakten.gesamtbetrag_genannt is not None and len(paare) == 1
            and paare[0][0] == fakten.gesamtbetrag_genannt):
        fakten = fakten.model_copy(update={"gesamtbetrag_genannt": None, "positionen": [Position(
            betrag=fakten.gesamtbetrag_genannt, auftragnehmer_typ=fakten.auftragnehmer_typ,
            taetigkeit_id=fakten.taetigkeit_id)]})
    if not fakten.positionen:
        return fakten
    if len(paare) != 1:
        return fakten
    x, y = paare[0]
    betraege = [p.betrag for p in fakten.positionen]
    nrn = {p.auftragnehmer_nr for p in fakten.positionen} - {None}
    if y >= x or y in betraege or betraege.count(x) != 1 or len(nrn) > 1:
        return fakten
    passend = [rolle for rolle, begriffe in _ROLLEN_BELEGE.items() if y in _betraege_am_begriff(t, begriffe)]
    if len(passend) != 1:
        return fakten
    rolle = passend[0]
    neue = []
    for p in fakten.positionen:
        if p.betrag == x and p.rolle == rolle:
            p = p.model_copy(update={"rolle": None, "bezeichnung": None if p.bezeichnung and _enthaelt_begriff(
                _vereinheitliche(p.bezeichnung), [_vereinheitliche(b) for b in _ROLLEN_BELEGE[rolle]]) else p.bezeichnung})
        neue.append(p)
    voll = next(p for p in neue if p.betrag == x)
    neue.append(Position(betrag=y, rolle=rolle, bezeichnung=_ROLLEN_BELEGE[rolle][0].capitalize(),
                         auftragnehmer_nr=voll.auftragnehmer_nr, auftragnehmer_typ=voll.auftragnehmer_typ))
    return fakten.model_copy(update={"positionen": neue})


def modellgerechneter_rest(text: str, fakten: Fakten) -> Fakten:
    """Korpus mit Small (17.10.2026, korpus-voll-small-2, F04: KB-0489, KB-0502, … – alle 11 FALSCH): '654,50 Euro brutto
    gezahlt, darin 104,50 EUR Umsatzsteuer' -- das Modell legte die ganze Rechnung (654,50, Bezeichnung 'Umsatzsteuer'),
    die Umsatzsteuer (104,50) UND einen selbst gerechneten Nettobetrag (550, 'Fotos für die Webseite') an. Der Kern
    rechnete den Rest der Rechnung ohnehin (550) -- der Nettobetrag zählte doppelt (1.100 statt 550).

    Regel (Grundregel 3: das Modell rechnet nicht): Nennt der Text genau EIN 'X … darin Y', gibt es eine Position über Y
    und eine über X (oder eine Rest-Position), gehören alle Positionen zu einem Auftragnehmer, und gibt es eine weitere
    Position, deren Betrag NICHT im Text steht und genau X − Y ist, dann ist sie die Rechnung des Modells: sie wird
    entfernt, den Rest rechnet der Kern. Ihre Bezeichnung und Tätigkeit gehen auf die Position über X über, wenn diese nur
    ein Beleg-Wort einer Rolle trägt ('Umsatzsteuer'). Ein Betrag, der im Text steht, wird nie entfernt."""
    from kern import rechnen as K

    if (fakten.anfrageart or "bewertung") != "bewertung" or len(fakten.positionen) < 3:
        return fakten
    paare = _davon_paare(waehrung_nach_hinten_text(text))
    if len(paare) != 1:
        return fakten
    x, y = paare[0]
    positionen = list(fakten.positionen)
    nrn = {p.auftragnehmer_nr for p in positionen} - {None}
    if y >= x or len(nrn) > 1 or not any(p.betrag == y for p in positionen):
        return fakten
    ix = [i for i, p in enumerate(positionen) if p.rest or p.betrag == x]
    if len(ix) != 1:
        return fakten
    netto = K.restbetrag(x, [y])
    im_text = betraege_im_text(text)
    weg = [i for i, p in enumerate(positionen)
           if i != ix[0] and not p.rest and p.betrag == netto and p.betrag not in im_text and p.rolle in (None, "honorar")]
    if len(weg) != 1:
        return fakten
    doppelt, bleibt = positionen[weg[0]], positionen[ix[0]]
    rollenwoerter = [_vereinheitliche(b) for begriffe in _ROLLEN_BELEGE.values() for b in begriffe]
    if bleibt.rolle is None and (not bleibt.bezeichnung or _enthaelt_begriff(_vereinheitliche(bleibt.bezeichnung),
                                                                             rollenwoerter)):
        positionen[ix[0]] = bleibt.model_copy(update={
            "bezeichnung": doppelt.bezeichnung, "taetigkeit_id": bleibt.taetigkeit_id or doppelt.taetigkeit_id,
            "auftragnehmer_typ": bleibt.auftragnehmer_typ or doppelt.auftragnehmer_typ})
    del positionen[weg[0]]
    return fakten.model_copy(update={"positionen": positionen})


def waehrung_nach_hinten_text(text: str) -> str:
    from app.textnorm import waehrung_nach_hinten

    return waehrung_nach_hinten(text) or ""


def vg_als_empfaenger(text: str, fakten: Fakten) -> Fakten:
    """Siehe app/rollen_belege.json, '_vg_als_empfaenger' (Korpus mit Small, F16). Setzt nur eine Rolle, die der Text
    ausdrücklich belegt ('an die VG Bild-Kunst 1.950 EUR'); rechnet nichts."""
    regel = _ROLLEN_KONFIG.get("_vg_als_empfaenger")
    if not regel or not fakten.positionen:
        return fakten
    from app.textnorm import waehrung_nach_hinten

    t = _vereinheitliche(waehrung_nach_hinten(text))
    namen = "|".join(re.escape(_vereinheitliche(n)) for n in regel["empfaenger"])
    muster = re.compile(rf"\ban\s+(?:die|den|der)\s+(?:{namen})\b[^.;\n]{{0,{int(regel['abstand'])}}}?"
                        r"(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{1,2}))?\s*(?:€|eur\b|euro)")
    betraege = {Decimal(m.group(1).replace(".", "") + (f".{m.group(2)}" if m.group(2) else "")) for m in muster.finditer(t)}
    # Testarchiv mit Small (17.10.2026, AT-2026-039): '1.500 EUR GEMA-Pauschale an die GEMA' -- Betrag davor.
    davor = re.compile(r"(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{1,2}))?\s*(?:€|eur\b|euro)"
                       rf"[^.;\n\d]{{0,{int(regel['abstand'])}}}?\ban\s+(?:die|den|der)\s+(?:{namen})\b")  # keine Zahl dazwischen
    betraege |= {Decimal(m.group(1).replace(".", "") + (f".{m.group(2)}" if m.group(2) else "")) for m in davor.finditer(t)}
    if not betraege:
        return fakten
    neue = list(fakten.positionen)
    for b in betraege:
        idx = [i for i, p in enumerate(neue) if p.betrag == b]
        if len(idx) == 1 and neue[idx[0]].rolle in (None, "honorar") and _alle_betraege(t).count(b) == 1:
            neue[idx[0]] = neue[idx[0]].model_copy(update={"rolle": "verwertungsgesellschaft"})
    return fakten if neue == list(fakten.positionen) else fakten.model_copy(update={"positionen": neue})


def absichere_rollen(text: str, fakten: Fakten) -> Fakten:
    """Prüfkatalog 11.10.2026: eine Sonderrolle, die einen Betrag aus der Bemessungsgrundlage
    herausnimmt (Umsatzsteuer, Gewinnzuweisung, Reisekosten, ...), gilt nur mit einem Beleg im
    Nutzertext (app/rollen_belege.json). Sonst zählt der Betrag normal -- das Modell darf die
    Bemessungsgrundlage nicht ohne Grundlage verkleinern."""
    t = _vereinheitliche(text)
    neue = []
    geaendert = False
    for p in fakten.positionen:
        # Testprotokoll 11.10.2026: das Modell erfand Rollen ('material_auslagen', 'vortrag und
        # reproduktion'). Nur 'honorar' und die Sonderrollen des Kerns sind gültig; alles andere
        # ist keine Rolle (die Beschreibung steht in 'bezeichnung').
        if p.rolle is not None and p.rolle not in _GUELTIGE_ROLLEN:
            p = p.model_copy(update={"rolle": None})
            geaendert = True
        begriffe = _ROLLEN_BELEGE.get(p.rolle or "")
        if _nachweis_fehlt(text, p):
            p = p.model_copy(update={"rolle": None})
            geaendert = True
        elif begriffe and not any(re.search(r"(?<![0-9a-z])" + re.escape(_vereinheitliche(b)), t) for b in begriffe):
            p = p.model_copy(update={"rolle": None})
            geaendert = True
        elif begriffe and betraege_im_text(text) and p.betrag not in _betraege_am_begriff(text, begriffe):
            # Prüfkatalog P-28 (live 11.10.2026): '1.190 € brutto, darin 190 € Umsatzsteuer' --
            # das Modell gab den GANZEN Betrag als Umsatzsteuer aus. Ausgenommen wird nur der
            # Betrag, der im Text direkt bei dem Beleg-Wort steht.
            p = p.model_copy(update={"rolle": None})
            geaendert = True
        neue.append(p)
    return fakten.model_copy(update={"positionen": neue}) if geaendert else fakten


def berechne_restpositionen(fakten: Fakten, text: str | None = None) -> Fakten:
    """Testprotokoll 11.10.2026, Schritt 4: 'Die gesamte Rechnung der Grafikerin beträgt 900 statt
    1.200 Euro, darin weiterhin 300 Euro Druckkosten' -- das Modell müsste 900 - 300 rechnen und
    ließ den alten Restbetrag stehen. Jetzt: der Nutzer nennt den Rechnungsbetrag
    (`Fakten.rechnungen`), die enthaltenen Teile sind eigene Positionen, und den Rest (die
    Position mit `rest`) rechnet der Kern. Fehlt die Rest-Position, entsteht sie; wäre der Rest
    negativ, bleibt der Betrag unverändert und es wird ein Widerspruch vermerkt."""
    from kern import rechnen as K

    from app.schema import Position, Rechnung, Widerspruch
    from app.textnorm import waehrung_nach_hinten

    text = waehrung_nach_hinten(text) if text is not None else None  # 'darin EUR 104,50' wie '104,50 EUR'
    positionen = list(fakten.positionen)
    # Härtetest RE-2026-777: 'rest' setzt das Modell manchmal ohne jeden enthaltenen Teilbetrag im
    # Text (eine durchgereichte Position wurde zum 'Rest'). Ohne 'darin/davon/einschließlich' mit
    # Beträgen gibt es keinen Rest: der Betrag der Position bleibt, wie er im Text steht.
    if text is not None and not _DAVON.search(text) and any(p.rest for p in positionen):
        positionen = [p.model_copy(update={"rest": None}) if p.rest else p for p in positionen]
    # Aufteilungs-Widersprüche werden jedes Mal neu bestimmt (eine Korrektur kann sie lösen).
    widersprueche = [w for w in fakten.widersprueche if not w.feld.startswith("rechnungen.")]
    # Live-Lauf 16.10.2026 (Korpus, ganzer Lauf Teil 2, F04): '654,50 EUR brutto gezahlt, darin EUR 104,50 Umsatzsteuer'
    # -- das Modell legte den Rest (Netto) und die Umsatzsteuer an, aber keinen Rechnungsbetrag ('Zu einem Restbetrag fehlt
    # der Rechnungsbetrag'). Nennt der Text genau EIN 'X … darin Y', ist Y eine Position und gehören alle Positionen zu
    # demselben (oder keinem genannten) Auftragnehmer, ist X der Rechnungsbetrag: er steht so im Text, nichts wird gerechnet.
    if text is not None and not fakten.rechnungen and any(p.rest for p in positionen):
        paare = _davon_paare(text)
        nrn = {p.auftragnehmer_nr for p in positionen} - {None}
        if len(paare) == 1 and len(nrn) <= 1:
            gesamt, teil = paare[0]
            if teil in {p.betrag for p in positionen if not p.rest}:
                nr = next(iter(nrn)) if nrn else 1
                positionen = [p if p.auftragnehmer_nr == nr else p.model_copy(update={"auftragnehmer_nr": nr})
                              for p in positionen]
                fakten = fakten.model_copy(update={"rechnungen": [Rechnung(auftragnehmer_nr=nr, gesamtbetrag=gesamt)]})
    nummern = {r.auftragnehmer_nr for r in fakten.rechnungen}
    for p in positionen:
        if p.rest and p.auftragnehmer_nr not in nummern:
            # Prüfkatalog P-28 (live): Rest-Position ohne passenden Rechnungsbetrag -- ihr Betrag
            # wäre geraten (oft 0). Nicht still mit 0 rechnen: gezielt nachfragen.
            widersprueche.append(Widerspruch(feld=f"rechnungen.{p.auftragnehmer_nr or 0}", werte=[],
                                             hinweis="Zu einem Restbetrag fehlt der Rechnungsbetrag."))
    if not fakten.rechnungen:
        return fakten.model_copy(update={"widersprueche": widersprueche, "positionen": positionen})
    weg: set[int] = set()
    for r in fakten.rechnungen:
        gruppe = [i for i, p in enumerate(positionen) if p.auftragnehmer_nr == r.auftragnehmer_nr and i not in weg]
        reste = [i for i in gruppe if positionen[i].rest]
        teile = [positionen[i].betrag for i in gruppe if i not in reste]
        if text is not None and len(_DAVON.findall(text)) == 1:
            # Live-Messung 3 (14.10.2026, P-28): das Modell markierte die 190 € Umsatzsteuer als Rest,
            # die 1.190 € als normale Position. Ein Betrag, der im Text als enthaltener Teil steht
            # ('darin 190 €'), ist nie der Rest (den rechnet der Kern) -- die Markierung entfällt.
            # Live-Lauf 16.10.2026 (KB-0491): mit Nachkommastellen ('darin 104,50 EUR') -- vorher nur der ganze Teil (104).
            enthalten = {y for _x, y in _davon_paare(text)}
            for i in [i for i in reste if positionen[i].betrag and positionen[i].betrag in enthalten]:
                positionen[i] = positionen[i].model_copy(update={"rest": None})
            reste = [i for i in gruppe if positionen[i].rest]
            teile = [positionen[i].betrag for i in gruppe if i not in reste]
        rollen_andere = lambda i: {positionen[j].rolle for j in gruppe if j != i}  # noqa: E731
        # Rolle der Position in Höhe der ganzen Rechnung: keine, Honorar, oder eine Rolle, die eine
        # andere Position derselben Rechnung schon trägt (Schritt 2, 14.10.2026: das Modell nannte
        # 1.190 € UND 190 € 'ust' -- der ganze Betrag kann nicht zugleich der enthaltene Teil sein).
        gleich = [i for i in gruppe if i not in reste and positionen[i].betrag == r.gesamtbetrag
                  and (positionen[i].rolle not in _GUELTIGE_ROLLEN - {"honorar"}
                       or positionen[i].rolle in rollen_andere(i))]
        # Schritt 2 (Live-Messung 14.10.2026, P-28): das Modell legte zusätzlich eine leere
        # Rest-Position (0 €) an. Eine solche Rest-Position ohne Betrag ersetzt die Position in Höhe der
        # ganzen Rechnung nicht; sie fällt weg, wenn diese zum Rest wird.
        leere_reste = [i for i in reste if not positionen[i].betrag]
        # Live-Lauf 16.10.2026 (F04): das Modell legte zusätzlich den Rest MIT selbst gerechnetem Betrag an (Brutto, Umsatzsteuer
        # UND Netto). Den Betrag eines Rests rechnet ohnehin der Kern; eine Rest-Position mit Betrag zählt hier wie eine leere.
        if (len(gruppe) - len(reste) > 1 and len(gleich) == 1 and len(reste) <= 1
                and text is not None and _DAVON.search(text) and len(_DAVON.findall(text)) == 1):
            leere_reste = reste
            # Prüfkatalog P-28 (live, schwankend): '1.190 € brutto, darin 190 € Umsatzsteuer' -- das Modell
            # gab das Honorar mit dem ganzen Rechnungsbetrag an. Nennt der Text genau EINEN enthaltenen
            # Teilbetrag, ist diese Position der Rest der Rechnung; den Betrag rechnet der Kern.
            voll = positionen[gleich[0]]
            if len(leere_reste) == 1:
                # Das Modell hat den Rest schon angelegt (mit Beschreibung, ohne Betrag): er bleibt; die
                # Position in Höhe der ganzen Rechnung fällt weg und gibt nur fehlende Angaben ab.
                ziel = positionen[leere_reste[0]]
                fehlend = {k: v for k, v in voll.model_dump().items()
                           if v is not None and getattr(ziel, k) is None and k not in ("betrag", "rolle", "rest")}
                positionen[leere_reste[0]] = ziel.model_copy(update=fehlend)
                weg.add(gleich[0])
                reste = leere_reste
            else:
                positionen[gleich[0]] = voll.model_copy(
                    update={"rest": True, "rolle": voll.rolle if voll.rolle in (None, "honorar") else None})
                weg.update(leere_reste)
                reste = gleich
            gruppe = [i for i in gruppe if i not in weg]
            teile = [positionen[i].betrag for i in gruppe if i not in reste]
        if len(gruppe) > 1 and any(t == r.gesamtbetrag for t in teile):
            widersprueche.append(Widerspruch(feld=f"rechnungen.{r.auftragnehmer_nr}", werte=[],
                                             hinweis="Ein Teilbetrag ist so hoch wie die ganze Rechnung."))
            continue
        if len(reste) > 1:
            continue
        rest = K.restbetrag(r.gesamtbetrag, teile)
        if rest < 0:
            key = f"rechnungen.{r.auftragnehmer_nr}"
            if not any(w.feld == key for w in widersprueche):
                widersprueche.append(Widerspruch(feld=key, werte=[str(r.gesamtbetrag), str(sum(teile))],
                                                 hinweis="Die Teilbeträge sind größer als der Rechnungsbetrag."))
            continue
        if reste:
            positionen[reste[0]] = positionen[reste[0]].model_copy(update={"betrag": rest})
        elif rest > 0 and gruppe and (text is None or _DAVON.search(text)):
            # Härtetest RE-2026-777: eine FEHLENDE Rest-Position entsteht nur, wenn der Text einen
            # enthaltenen Teilbetrag nennt ('1.200 Euro … darin 300 Euro'). Sonst ist der
            # Unterschied zum Rechnungsbetrag kein 'Rest' (das Modell hatte den Bruttobetrag der
            # ganzen Rechnung einem Teil der Positionen zugeordnet: 9.886 € 'Rest der Rechnung').
            vorlage = positionen[gruppe[0]]
            positionen.append(Position(betrag=rest, bezeichnung="Rest der Rechnung", rest=True,
                                       auftragnehmer_nr=r.auftragnehmer_nr,
                                       auftragnehmer_typ=vorlage.auftragnehmer_typ))
    positionen = [p for i, p in enumerate(positionen) if i not in weg]
    return fakten.model_copy(update={"positionen": positionen, "widersprueche": widersprueche})


def einzelrechnungen_je_position(text: str | None, fakten: Fakten) -> Fakten:
    """Schritt 2 (Live-Messung 14.10.2026, P-04a, P-04b, P-32: 15 von 18 Fehlversuchen): das Modell
    legte jede Position ZUSÄTZLICH als eigene Rechnung an ('fünfmal …, jede Rechnung 250 €' → 5
    Positionen à 250 € und 5 Rechnungen à 250 €, alle Auftragnehmer 1). berechne_restpositionen las
    das als EINE Rechnung über 250 € mit fünf Teilen ('Ein Teilbetrag ist so hoch wie die ganze
    Rechnung'). Passen die Rechnungen eines Auftragnehmers EINS ZU EINS zu seinen Positionen (gleich
    viele, dieselben Beträge, keine Rest-Position) und nennt der Text keinen enthaltenen Teilbetrag
    ('darin/davon'), ist jede Position eine eigene Rechnung: die Rechnungsangaben tragen nichts
    Zusätzliches und entfallen. Kein Betrag ändert sich. Eine echte Unstimmigkeit ('Rechnung
    1.200 €: Gestaltung 1.200 €, Druck 300 €') passt nicht eins zu eins und wird weiter gemeldet."""
    if not fakten.rechnungen or (text is not None and _DAVON.search(text)):
        return fakten
    if not fakten.positionen and text is not None:
        # Live-Messung 14.10.2026 (P-04a): nur Rechnungen, keine Position. Steht jeder Betrag so im
        # Text, ist jede Rechnung eine Position (Bestätigung durch den Nutzer folgt).
        im_text = betraege_im_text(text)
        if all(r.gesamtbetrag in im_text for r in fakten.rechnungen):
            from app.schema import Position

            return fakten.model_copy(update={"rechnungen": [], "positionen": [
                Position(betrag=r.gesamtbetrag, auftragnehmer_nr=r.auftragnehmer_nr) for r in fakten.rechnungen]})
        return fakten
    behalten = []
    nummern = {r.auftragnehmer_nr for r in fakten.rechnungen}
    for nr in nummern:
        rs = [r for r in fakten.rechnungen if r.auftragnehmer_nr == nr]
        ps = [p for p in fakten.positionen if p.auftragnehmer_nr == nr]
        eins_zu_eins = (len(rs) > 1 and len(rs) == len(ps) and not any(p.rest for p in ps)
                        and sorted(r.gesamtbetrag for r in rs) == sorted(p.betrag for p in ps))
        if not eins_zu_eins:
            behalten.extend(rs)
    if len(behalten) == len(fakten.rechnungen):
        return fakten
    return fakten.model_copy(update={"rechnungen": [r for r in fakten.rechnungen if r in behalten]})


_BETRAG_IM_TEXT = re.compile(r"(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{1,2}))?\s*(?:€|eur\b|euro)", re.IGNORECASE)


def betraege_im_text(text: str) -> set:
    from decimal import Decimal

    from app.textnorm import waehrung_nach_hinten

    return {Decimal(g.replace(".", "") + (f".{n}" if n else "")) for g, n in _BETRAG_IM_TEXT.findall(waehrung_nach_hinten(text))}


def absichere_gesamtbetrag(text: str, fakten: Fakten) -> Fakten:
    """Ein Gesamtbetrag, den der Nutzer nie genannt hat (das Modell hatte 1.200 + 800 = 2.000
    selbst addiert), ist keine Angabe des Nutzers: verwerfen. Das Modell rechnet nicht."""
    if fakten.gesamtbetrag_genannt is None or fakten.gesamtbetrag_genannt in betraege_im_text(text):
        return fakten
    if not fakten.positionen or fakten.gesamtbetrag_genannt != fakten.summe_positionen():
        return fakten  # nur die selbst gebildete Summe der Positionen wird verworfen
    return fakten.model_copy(update={"gesamtbetrag_genannt": None})


def rechtsform_je_auftragnehmer(fakten: Fakten) -> Fakten:
    """Live-Nachspielen 11.10.2026: die Druckkosten innerhalb der Rechnung der Grafikerin bekamen
    keine eigene Rechtsform, und das System fragte bei jeder Nachricht danach -- obwohl beide
    Positionen zu derselben Auftragnehmerin gehören (gleiche `auftragnehmer_nr`). Positionen
    desselben Auftragnehmers haben dieselbe Rechtsform: eine fehlende wird ergänzt, wenn in der
    Gruppe genau eine Rechtsform bekannt ist (bei verschiedenen wird nichts geraten)."""
    gruppen: dict[int, set] = {}
    for p in fakten.positionen:
        if p.auftragnehmer_nr is not None and p.auftragnehmer_typ:
            gruppen.setdefault(p.auftragnehmer_nr, set()).add(p.auftragnehmer_typ)
    if not gruppen:
        return fakten
    neue = []
    geaendert = False
    for p in fakten.positionen:
        werte = gruppen.get(p.auftragnehmer_nr) if p.auftragnehmer_nr is not None else None
        if p.auftragnehmer_typ is None and werte and len(werte) == 1:
            p = p.model_copy(update={"auftragnehmer_typ": next(iter(werte))})
            geaendert = True
        neue.append(p)
    return fakten.model_copy(update={"positionen": neue}) if geaendert else fakten


def ergaenze_rechtsform_je_zeile(frage: str, fakten: Fakten) -> Fakten:
    """Live-Nachspielen 11.10.2026, Schritt 1: '– Eine selbstständige Grafikerin, Einzelunternehmerin,
    stellte uns 1.200 Euro ... – Eine Foto-GmbH stellte uns 800 Euro ...' -- das Modell setzte gar
    keine Rechtsform, und bei mehreren Positionen rät ergaenze_rechtsform nicht. Hier wird je Zeile
    bzw. Satz der NEUEN Nachricht zugeordnet: nennt er genau eine Rechtsform des Auftragnehmers und
    Beträge, bekommen die Positionen mit genau diesem Betrag (oder deren Rechnung diesen Betrag hat)
    diese Rechtsform, wenn sie noch keine haben."""
    if not fakten.positionen:
        return fakten
    rechnung = {r.auftragnehmer_nr: r.gesamtbetrag for r in fakten.rechnungen}
    neue = list(fakten.positionen)
    geaendert = False
    teile = []
    for teil in re.split(r"\n+|(?<=[.!?])\s+", frage):
        teile.append(teil)
        # Fehlerquellen HT-2026-089 (Gesamtlauf 301eb97): 'an eine GmbH für Video-Produktion 1.500 EUR und an einen
        # freien Kameramann 1.000 EUR' -- zwei Rechtsformen in EINEM Satz. Der Satz wird an Komma, Semikolon, 'und',
        # 'sowie' zerlegt; nur Teile mit genau EINEM Betrag zählen (gleich, ob der Empfänger vor oder nach dem Betrag
        # steht: '4.000 EUR an freien Cartoonisten, 6.000 EUR an eine PR-GmbH').
        if len(_BETRAG_IM_TEXT.findall(teil)) > 1:
            teile.extend(t for t in _TEIL_MIT_UND.split(teil) if t and len(_BETRAG_IM_TEXT.findall(t)) == 1)
    for teil in teile:
        typ = erkenne_rechtsform_auftragnehmer(teil)
        betraege = betraege_im_text(teil)
        if typ is None or not betraege:
            continue
        for i, p in enumerate(neue):
            if p.auftragnehmer_typ is not None:
                continue
            if p.betrag in betraege or (p.auftragnehmer_nr is not None and rechnung.get(p.auftragnehmer_nr) in betraege):
                neue[i] = p.model_copy(update={"auftragnehmer_typ": typ})
                geaendert = True
    return fakten.model_copy(update={"positionen": neue}) if geaendert else fakten


_TEIL_MIT_UND = re.compile(r"(?<!\d),|,(?!\d)|;|\n|\s(?:und|sowie)\s")
_LISTENTEIL = re.compile(r"(?<!\d),|,(?!\d)|[;\n]|(?<=[.!?])\s+|\s--?\s")


def rechtsform_nur_wo_genannt(text: str, fakten: Fakten) -> Fakten:
    """Fehlerquellen-Serie (live 15.10.2026, 17010bf):
    - HT-2026-069 'an Fotograf Weber 1.100 EUR, an die Weber Fotodesign GmbH für Retusche 900 EUR, an Fotograf Weber
      nochmal 400 EUR' -- das Modell gab ALLEN drei Positionen 'GmbH' (0 € statt 1.500 €);
    - HT-2026-099 '2000 euro an einen Kuenstler gezahlt, 2026, GmbH.' -- die GmbH (der Auftraggeber) wurde zur
      Rechtsform der Position ('nicht abgabepflichtig').
    Steht der Betrag einer Position in einem Listenteil OHNE Rechtsform des Auftragnehmers, nennt aber ein ANDERER
    Listenteil genau diese Rechtsform, ist sie für diese Position nicht belegt: sie wird verworfen (dann fragt das
    System). Eine allgemeine Rechtsform (Fakten.auftragnehmer_typ) gleicher Art wird ebenso verworfen; Positionen,
    deren eigener Teil die Rechtsform nennt, behalten sie. Nie wird eine Rechtsform hinzugeraten.

    Alltags-Serie (live 15.10.2026, f6a5d1a): AT-2026-035 'GmbH zahlte … an Videograf' und AT-2026-054 '… an eine
    freie Malerin gezahlt, GmbH.' -- die Rechtsform des ZAHLERS wurde zur Rechtsform des Künstlers. Zusätzlich gilt:
    eine Gesellschafts-Rechtsform, die der Text an keiner Stelle für einen Auftragnehmer nennt, ist nicht belegt und
    wird verworfen; ohne Positionen auch dann, wenn sie nur in einem Teil ohne Betrag steht, ein anderer Teil aber
    eine natürliche Person nennt ('an eine freie Malerin')."""
    if rechnungsteller_typ(text) is not None:
        return fakten
    teile = [t for t in _LISTENTEIL.split(text) if t and t.strip()]
    saetze = [z for z in re.split(r"(?<=[.!?])\s+|\n", text) if z.strip()]

    def art(teil: str):
        # Ein Teil, der nur aus der Rechtsform besteht (', GmbH.'), wird im ganzen Satz beurteilt (AT-2026-054).
        if len(re.findall(r"\w+", teil)) <= 2:
            satz = next((z for z in saetze if teil.strip() in z), teil)
            return erkenne_rechtsform_auftragnehmer(satz) if erkenne_rechtsform_auftragnehmer(satz) else None
        return erkenne_rechtsform_auftragnehmer(teil)

    # Ein Teil mit mehreren Beträgen ('an eine GmbH … 1.500 EUR und an einen freien Kameramann 1.000 EUR'): zusätzlich
    # seine Teile mit genau einem Betrag, zerlegt an 'und'/'sowie' (wie ergaenze_rechtsform_je_zeile, HT-2026-089).
    abschnitte = []
    for t in teile:
        if len(_BETRAG_IM_TEXT.findall(t)) > 1:
            abschnitte.extend(x for x in _TEIL_MIT_UND.split(t) if x and len(_BETRAG_IM_TEXT.findall(x)) == 1)
        abschnitte.append(t)
    art_je_teil = [(art(t), betraege_im_text(t)) for t in abschnitte]
    alle_typen = {typ for typ, _ in art_je_teil if typ is not None}
    # Testarchiv mit mistral-small-latest (17.10.2026, HT-2026-099): Small schrieb die GmbH nicht als Rechtsform des
    # Auftraggebers, sondern als Tätigkeit des Unternehmens ('unternehmensart': 'GmbH'). Beides beschreibt den Auftraggeber.
    from app.rechtsform_erkennung import erkenne_rechtsform

    auftraggeber_form = fakten.auftraggeber_typ or (erkenne_rechtsform(fakten.unternehmensart)
                                                     if fakten.unternehmensart else None)
    # Ein Teil MIT Betrag belegt die Rechtsform für seine Position. Ein Teil OHNE Betrag ist meist eine Kopfzeile
    # ('Rechnung der Studio GmbH:') und gilt für alle -- außer er nennt die Rechtsform des AUFTRAGGEBERS (HT-099).
    genannt = {typ for typ, betraege in art_je_teil if typ is not None
               and (betraege or typ == auftraggeber_form)}
    natuerlich_genannt = "natuerliche_person" in alle_typen
    # Nur Rechtsformen, deren WORT im Text steht (egal für welche Seite). Steht es im Text, wird aber keinem
    # Auftragnehmer zugeordnet (nur Auftraggeber/Zahler), ist eine solche Rechtsform des Modells nicht belegt.
    from app.rechtsform_erkennung import RECHTSFORM_MUSTER, normalisiere_umlaute

    roh = normalisiere_umlaute(text.lower())
    im_text = {wert for muster, wert in RECHTSFORM_MUSTER if re.search(muster, roh)}

    def gesellschaft(typ) -> bool:
        return typ is not None and typ not in ("natuerliche_person", "Ausland")

    def nur_eigene_seite(typ) -> bool:
        return gesellschaft(typ) and typ in im_text and typ not in alle_typen

    if not fakten.positionen:
        g = fakten.auftragnehmer_typ
        nur_ohne_betrag = all(not b for typ, b in art_je_teil if typ == g)
        if nur_eigene_seite(g) or (gesellschaft(g) and g in alle_typen and nur_ohne_betrag and natuerlich_genannt
                                    and g == auftraggeber_form):
            return fakten.model_copy(update={"auftragnehmer_typ": None})
        return fakten

    def eigener_typ(betrag):
        # Korpus-Lauf 15.10.2026: ein Teilsatz ohne Rechtsform ('zusätzlich 150 EUR Fahrtkosten erstattet') verdeckte die
        # Rechtsform des ganzen Satzes ('einem freien Texter (Einzelperson) … 450 EUR … und zusätzlich 150 EUR'). Es gilt
        # die eine Rechtsform aller Abschnitte mit diesem Betrag; nennen sie verschiedene, keine.
        typen = [typ for typ, betraege in art_je_teil if betrag in betraege]
        if not typen:
            return None, False
        bekannt = {t for t in typen if t is not None}
        return (bekannt.pop() if len(bekannt) == 1 else None), True

    neue, geaendert = [], False
    global_typ = fakten.auftragnehmer_typ
    global_weg = nur_eigene_seite(global_typ)
    typen_mit_betrag = {typ for typ, betraege in art_je_teil if typ is not None and betraege}
    for p in fakten.positionen:
        typ_eff = p.auftragnehmer_typ or global_typ
        eigen, gefunden = eigener_typ(p.betrag)
        unbelegt = nur_eigene_seite(typ_eff)
        # Nennen die Abschnitte mit dem Betrag verschiedene Rechtsformen und darunter die des Modells (S1 'Eine Foto-GmbH
        # … 800 Euro', S6 '… über 800 Euro sei Einzelunternehmerin'), ist es ein Widerspruch, kein 'anderswo'.
        beim_betrag = {typ for typ, betraege in art_je_teil if p.betrag in betraege and typ is not None}
        anderswo = (gefunden and eigen is None and typ_eff is not None and typ_eff != "natuerliche_person"
                    and typ_eff in genannt and typ_eff not in beim_betrag)
        # Korpus-Lauf 15.10.2026 (gestörte Fakten, 167 FALSCH von 3.618): nennt der Teil mit dem Betrag selbst eine
        # ANDERE Rechtsform als das Modell ('einem freien Grafikdesigner (Einzelperson) 450,01 €', Modell: GmbH; 'der
        # Pixelwerk GmbH 950 €', Modell: Einzelperson), ist die Angabe des Modells widerlegt. Sie wird verworfen; das
        # System fragt nach (nie geraten, auch nicht zugunsten des Textes). Unabhängig vom Sprachmodell.
        # Nennt ein Teil OHNE Betrag gerade die Rechtsform des Modells ('Auf der Rechnung steht aber „Foto-Beispiel GmbH“'),
        # ist es ein Widerspruch, kein Fehler des Modells: dann bleibt sie, die Widerspruchsprüfung fragt mit zwei Knöpfen
        # (test_testprotokoll_1110.TestWiderspruch).
        ohne_betrag_genannt = any(typ == typ_eff and not betraege for typ, betraege in art_je_teil)
        widerlegt = (gefunden and eigen is not None and typ_eff is not None and eigen != typ_eff
                     and not ohne_betrag_genannt)
        # Steht der Betrag nicht im Text (z. B. Nettobetrag aus 'brutto … darin USt'), gilt die EINE Rechtsform, die der
        # Text für Auftragnehmer nennt (alle Teile mit Betrag): eine andere des Modells ist widerlegt. Nennt der Text an
        # anderer Stelle (auch ohne Betrag, 'Eine Grafikerin, Einzelunternehmerin, stellte uns 1.200 Euro') eine weitere
        # Rechtsform, ist nichts widerlegt (test_testprotokoll_1110, Bestandteil erbt die Rechtsform).
        if (not gefunden and typ_eff is not None and len(typen_mit_betrag) == 1 and alle_typen == typen_mit_betrag
                and typ_eff not in typen_mit_betrag):
            widerlegt = True
        unbelegt = unbelegt or widerlegt
        if p.auftragnehmer_typ is not None and (unbelegt or anderswo):
            p = p.model_copy(update={"auftragnehmer_typ": None})
            geaendert = True
        if (unbelegt or anderswo) and global_typ == typ_eff:
            global_weg = True
        neue.append(p)
    if not geaendert and not global_weg:
        return fakten
    if global_weg:
        neue = [p if p.auftragnehmer_typ is not None or eigener_typ(p.betrag)[0] is None
                else p.model_copy(update={"auftragnehmer_typ": eigener_typ(p.betrag)[0]}) for p in neue]
    update = {"positionen": neue}
    if global_weg:
        update["auftragnehmer_typ"] = None
    return fakten.model_copy(update=update)


def _davon_paare(text: str) -> list[tuple[Decimal, Decimal]]:
    """(Gesamtbetrag, enthaltener Betrag) je 'X … darin/davon Y' -- MIT Nachkommastellen. Live-Lauf 16.10.2026 (KB-0491):
    vorher wurden nur die ganzen Euro gelesen ('darin 104,50 EUR' -> 104), der Teilbetrag passte zu keiner Position."""
    erg = []
    for m in _DAVON.finditer(text):
        zahlen = _alle_betraege(m.group(0).lower())
        if len(zahlen) >= 2:
            erg.append((zahlen[0], zahlen[-1]))
    return erg


_DAVON = re.compile(
    r"(\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{1,2})?\s*(?:€|eur\b|euro)[^;\n]{0,120}?\b(?:davon|darin|darunter|einschlie(?:ß|ss)lich|inklusive|inkl\.?)\s+"
    r"(?:\w+\s+){0,3}?(\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{1,2})?\s*(?:€|eur\b|euro)", re.IGNORECASE)


def fehlende_nebenkosten_position(text: str, fakten: Fakten) -> Fakten:
    """Siehe app/rollen_belege.json, '_fehlende_nebenkosten'. Fügt nur einen Betrag hinzu, der im Text ausdrücklich als
    zusätzliche Nebenkosten steht und in den Fakten ganz fehlt; rechnet nichts."""
    regel = _ROLLEN_KONFIG.get("_fehlende_nebenkosten")
    if not regel or not fakten.positionen or (fakten.anfrageart or "bewertung") != "bewertung":
        return fakten
    from app.textnorm import waehrung_nach_hinten

    t = waehrung_nach_hinten(text)
    bekannt = {p.betrag for p in fakten.positionen} | {r.gesamtbetrag for r in fakten.rechnungen}
    bekannt |= {fakten.gesamtbetrag_genannt, fakten.summe_positionen()}
    if fakten.gesamtbetrag_genannt is not None and fakten.gesamtbetrag_genannt == fakten.summe_positionen():
        return fakten  # der genannte Gesamtbetrag ist schon vollständig verteilt
    alle = _alle_betraege(t)
    am_begriff = _betraege_am_begriff(t, regel["begriffe"])
    zusatz = [_vereinheitliche(w) for w in regel["zusatz"]]
    sperre = [_vereinheitliche(w) for w in regel["nicht_wenn"]]
    neue = list(fakten.positionen)
    nr = {p.auftragnehmer_nr for p in fakten.positionen}
    typ = {p.auftragnehmer_typ for p in fakten.positionen}
    for satz in re.split(r"(?<=[.!?;])\s+|\n", t):
        s = _vereinheitliche(satz)
        if _enthaelt_begriff(s, sperre):
            continue
        for m in _BETRAG_IM_TEXT.finditer(s):
            betrag = Decimal(m.group(1).replace(".", "") + (f".{m.group(2)}" if m.group(2) else ""))
            if betrag in bekannt or betrag not in am_begriff or alle.count(betrag) != 1:
                continue
            if not _enthaelt_begriff(s[:m.start()], zusatz):
                continue
            begriff = next((b for b in regel["begriffe"] if _vereinheitliche(b) in s), regel["begriffe"][0])
            neue.append(Position(betrag=betrag, bezeichnung=begriff.capitalize(),
                                 auftragnehmer_nr=next(iter(nr)) if len(nr) == 1 else None,
                                 auftragnehmer_typ=next(iter(typ)) if len(typ) == 1 else None))
            bekannt.add(betrag)
    if len(neue) == len(fakten.positionen):
        return fakten
    return fakten.model_copy(update={"positionen": neue})


def enthaltene_betraege_nicht_doppelt(text: str, fakten: Fakten) -> Fakten:
    """Prüfkatalog P-39 (live 11.10.2026): 'Gage von 2.000 €. ... zahlen wir davon 500 € direkt an
    ihren Manager' -- das Modell legte 2.000 UND 500 als Positionen an (2.500, doppelt). Nennt der
    Text 'X Euro ... davon/darin/einschließlich Y Euro' und gibt es Positionen über genau X und Y,
    wird X als Rechnungsbetrag geführt und der Rest vom Kern gerechnet (berechne_restpositionen) --
    kein Abzug durch das Modell, keine Doppelzählung. Nur, solange noch keine Rechnungsbeträge
    bekannt sind.

    Live 14.10.2026 (5584e86, P-39 FALSCH 2.500 €): das Modell legte selbst 'Rechnung von
    Auftragnehmer 1: 2.000 €' an und gab die 500 € einem Auftragnehmer 2. Gibt es schon eine
    Rechnung über GENAU X bei dem Auftragnehmer der X-Position, gilt dieselbe Zuordnung (Y gehört zu
    dieser Rechnung). Eine Rechnung mit einem anderen Betrag bleibt unberührt (dann prüft
    berechne_restpositionen)."""
    if len(fakten.positionen) < 2:
        return fakten
    from decimal import Decimal

    from app.schema import Rechnung

    positionen = list(fakten.positionen)
    rechnungen = list(fakten.rechnungen)
    geaendert = False
    for x, y in _davon_paare(text):
        ix = [i for i, p in enumerate(positionen) if p.betrag == x and not p.rest]
        iy = [i for i, p in enumerate(positionen) if p.betrag == y]
        if len(ix) != 1 or len(iy) != 1 or ix[0] == iy[0] or y >= x:
            continue
        nr = positionen[ix[0]].auftragnehmer_nr or max([p.auftragnehmer_nr or 0 for p in positionen] + [0]) + 1
        vorhanden = [r for r in rechnungen if r.auftragnehmer_nr == nr]
        if vorhanden and (len(vorhanden) != 1 or vorhanden[0].gesamtbetrag != x):
            continue
        if fakten.rechnungen and not vorhanden:
            continue  # Rechnungen bekannt, aber keine zu X: nicht raten
        if vorhanden and positionen[iy[0]].auftragnehmer_nr == nr:
            continue  # Y liegt schon bei dieser Rechnung: das regelt berechne_restpositionen (P-28)
        positionen[ix[0]] = positionen[ix[0]].model_copy(update={"rest": True, "auftragnehmer_nr": nr})
        positionen[iy[0]] = positionen[iy[0]].model_copy(update={"auftragnehmer_nr": nr})
        if not vorhanden:
            rechnungen.append(Rechnung(auftragnehmer_nr=nr, gesamtbetrag=x))
        geaendert = True
    if not geaendert:
        return fakten
    update: dict = {"positionen": positionen, "rechnungen": rechnungen}
    nummern = {p.auftragnehmer_nr for p in positionen}
    if fakten.ein_auftragnehmer is False and len(nummern) == 1:
        update["ein_auftragnehmer"] = None  # die zweite 'Person' war nur der Empfänger eines Teilbetrags
    return fakten.model_copy(update=update)


# ---------------------------------------------------------------------------------------------
# Alltagsfälle 11.10.2026 (F3): Rechnungsteller ist der Zahlungsempfänger
# ---------------------------------------------------------------------------------------------
_RT_KONFIG = json.loads((Path(__file__).resolve().parent / "rechnungsteller_begriffe.json").read_text(encoding="utf-8"))
_RT_ZEILE = re.compile(
    r"^[ \t]*(?:" + "|".join(re.escape(e) for e in _RT_KONFIG["etiketten"]) + r")[ \t]*:[ \t]*(.+)$",
    re.IGNORECASE | re.MULTILINE)
_RT_EIGENE_SEITE = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in _RT_KONFIG["eigene_seite"]) + r")\b",
                              re.IGNORECASE)
_KAPITAL_ODER_HANDELSGESELLSCHAFT = ("GmbH_UG_AG", "KG_OHG")


def rechnungsteller_typ(nachricht: str) -> str | None:
    """Rechtsform des Rechnungstellers aus einer ausdrücklich beschrifteten Zeile
    ('Rechnungsteller: Kreativwerk Agentur Licht GmbH, ...'). Nur bei genau EINER solchen Zeile
    und eindeutiger Rechtsform, sonst None (nie raten)."""
    zeilen = {m.group(1).strip() for m in _RT_ZEILE.finditer(nachricht)}
    if len(zeilen) != 1:
        return None
    zeile = zeilen.pop()
    if _RT_EIGENE_SEITE.search(zeile):
        return None  # 'Rechnungsteller: wir' -- die eigene Seite, nicht der Auftragnehmer
    return erkenne_rechtsform_auftragnehmer(zeile)


_POSITIONSBEGINN = re.compile(_RT_KONFIG["positionsbeginn"], re.IGNORECASE)


def _positionsabschnitte(nachricht: str) -> list[str]:
    """Teilt eine Rechnung in Abschnitte je Position: ab einer Zeile, die mit einer Positionsnummer
    beginnt ('Pos. 01 …', '02 | …'), bis zur nächsten oder bis zu einer Summen-/Vermerkzeile
    ('Nettosumme', 'Belegvermerk', …). Fortsetzungszeilen gehören zur Position davor. Ohne
    Positionsnummern gilt jede Zeile als eigener Abschnitt."""
    abschnitte: list[str] = []
    aktuell: list[str] | None = None
    for zeile in nachricht.splitlines():
        if zeile.strip().lower().startswith(tuple(_RT_KONFIG["abschnitt_ende"])):
            if aktuell:
                abschnitte.append("\n".join(aktuell))
            aktuell = None  # Summen- und Vermerkzeilen gehören zu keiner Position
            continue
        if _POSITIONSBEGINN.match(zeile):
            if aktuell:
                abschnitte.append("\n".join(aktuell))
            aktuell = [zeile]
        elif aktuell is not None:
            aktuell.append(zeile)
    if aktuell:
        abschnitte.append("\n".join(aktuell))
    return abschnitte or nachricht.splitlines()


_SATZTEIL = re.compile(_RT_KONFIG["satzteil_trenner"])


def _art_im_text(text: str) -> str | None:
    if _enthaelt_begriff(text, _RT_KONFIG["unklar"]):
        return "unklar"
    if _enthaelt_begriff(text, _RT_KONFIG["vertrag_direkt"]):
        return "vertrag_direkt"
    return None


def _woerter(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", _vereinheitliche(text)) if len(w) > 3}


def _zahlungsweg(abschnitte: list[str], betrag: Decimal, bezeichnung: str | None = None) -> str | None:
    """Härtetest RE-2026-777 / ALLTAG-2026-999: Art des Zahlungswegs für EINEN Betrag. Zuerst die
    Satzteile, in denen der Betrag steht ('GmbH erhält 480 € Vermittlungsprovision' / 'Rest 2.720 €
    zahlt die Messe GmbH direkt an den Komponisten'), sonst der ganze Abschnitt der Position.
    'unklar' geht vor 'vertrag_direkt'; None heißt: im eigenen Namen der Rechnungstellerin."""
    def enthaelt(t: str) -> bool:
        b = betraege_im_text(t)
        return betrag in b or -betrag in b
    eigene = [a for a in abschnitte if enthaelt(a)]
    if len(eigene) > 1 and bezeichnung:
        # ALLTAG-2026-999: zwei Positionen mit demselben Betrag (700 € Tanz 'im eigenen Namen', 700 €
        # Gesang 'durchgereicht'). Dann gilt der Abschnitt, der am besten zur Bezeichnung passt.
        w = _woerter(bezeichnung)
        punkte = [len(w & _woerter(a)) for a in eigene]
        if max(punkte) > 0:
            eigene = [a for a, pkt in zip(eigene, punkte) if pkt == max(punkte)]
    teile = [t for a in eigene for t in _SATZTEIL.split(a) if enthaelt(t)]
    arten = {_art_im_text(t) for t in teile} - {None}
    if not arten:
        arten = {_art_im_text(a) for a in eigene} - {None}
    if "unklar" in arten:
        return "unklar"
    return "vertrag_direkt" if "vertrag_direkt" in arten else None


def rechnungsteller_als_zahlungsempfaenger(nachrichten: list[str], fakten: Fakten) -> Fakten:
    """Alltagsfälle 11.10.2026 (F3, Agentur-Mischrechnung): Der Kunde bezahlt den
    Rechnungsteller, nicht die Künstler, die dieser selbst beauftragt hat. Das Modell trug bei
    'TV-Spot durch Film-Team „Roter Hering GbR“, im eigenen Namen der Agentur' die GbR als
    Zahlungsempfänger ein -- 1.220,10 € statt 0 €.

    Nennt eine Nachricht ausdrücklich den Rechnungsteller (`rechnungsteller_typ`), gilt dessen
    Rechtsform für jede Position, deren Betrag in DIESER Nachricht steht (R-45, R-177, R-216;
    Agentur im eigenen Namen: R-189, R-219); diese Positionen stammen vom selben Auftragnehmer.

    Ausnahmen (Härtetest RE-2026-777):
    - Die Rechnungsteller-Zeile selbst nennt eine Vertretung: nichts setzen (R-33).
    - Der Abschnitt EINER Position nennt Vertretung, Durchleitung, einen direkten Vertrag mit dem
      Kunden oder eine Direktzahlung an den Künstler: für diese Position gilt die Rechtsform des
      Rechnungstellers nicht; sie wird `zahlungsweg_unklar` (Steuerberater entscheidet anhand der
      Verträge, KSK-Info 27, R-36, R-94). Vorher wurde bei einem solchen Wort die ganze Rechnung
      übergangen -- auch die Positionen 'im eigenen Namen der GmbH eingekauft'."""
    rt_typ = None
    gesetzt: set[int] = set()
    unklar: set[int] = set()
    positionen = list(fakten.positionen)
    for nachricht in nachrichten:
        typ = rechnungsteller_typ(nachricht)
        if typ is None:
            continue
        zeile = next((m.group(1) for m in _RT_ZEILE.finditer(nachricht)), "")
        if typ in _KAPITAL_ODER_HANDELSGESELLSCHAFT and _enthaelt_begriff(zeile, _RT_KONFIG["vertreter"]):
            continue
        betraege = set(betraege_im_text(nachricht))
        abschnitte = _positionsabschnitte(nachricht)
        for i, p in enumerate(positionen):
            betrag = Decimal(str(p.betrag))
            if betrag not in betraege and -betrag not in betraege:
                continue
            if p.rolle in _GUELTIGE_ROLLEN - {"honorar"}:
                continue  # Sonderrolle (z. B. Umsatzsteuer): ihr Ausschlussgrund bleibt der eigene
            art = _zahlungsweg(abschnitte, betrag, p.bezeichnung)
            if art == "unklar" or (art == "vertrag_direkt" and p.auftragnehmer_typ in _KAPITAL_ODER_HANDELSGESELLSCHAFT
                                   and p.rolle not in _GUELTIGE_ROLLEN - {"honorar"}):
                # Provision/Vermittler/vertragswidrig -- oder ein direkter Vertrag mit dem Künstler, bei dem
                # das Modell trotzdem eine Gesellschaft als Empfänger nennt: Steuerberater entscheidet.
                unklar.add(i)
                positionen[i] = p.model_copy(update={"zahlungsweg_unklar": True, "vertrag_direkt": None})
                continue
            if art == "vertrag_direkt":
                # Vertrag unmittelbar zwischen Mandant und Künstler: zählt beim Mandanten (KSK-Info 27 S. 1,
                # KSK-Info 13, R-127); die Rechtsform ist die des Künstlers, nicht die der Rechnungstellerin.
                positionen[i] = p.model_copy(update={"vertrag_direkt": True, "zahlungsweg_unklar": None})
                unklar.add(i)  # nicht 'gesetzt': die Position stammt nicht von der Rechnungstellerin
                continue
            positionen[i] = p.model_copy(update={"auftragnehmer_typ": typ, "auftragnehmer_nr": 1,
                                                 "zahlungsweg_unklar": None, "vertrag_direkt": None})
            gesetzt.add(i)
        rt_typ = typ
    if rt_typ is None or not (gesetzt or unklar):
        # Keine Rechnungsteller-Zeile in diesen Nachrichten (z. B. eine Nachfrage zum Fall): der
        # gespeicherte Stand bleibt, wie er ist.
        return fakten
    update: dict = {"positionen": positionen, "rechnungsteller_typ": rt_typ}
    if len(gesetzt) == len(positionen):
        update["ein_auftragnehmer"] = True
        update["auftragnehmer_typ"] = rt_typ
        if len(fakten.rechnungen) == 1:
            update["rechnungen"] = [fakten.rechnungen[0].model_copy(update={"auftragnehmer_nr": 1})]
    return fakten.model_copy(update=update)


# ---------------------------------------------------------------------------------------------
# Alltagsfälle 11.10.2026: Jahr aus einheitlichen Rechnungsdaten
# ---------------------------------------------------------------------------------------------
_DATUM_JAHR = re.compile(r"\b\d{1,2}\.\s?\d{1,2}\.\s?((?:19|20)\d{2})\b")
_FREIES_JAHR = re.compile(r"(?<![\d.,])((?:19|20)\d{2})(?![\d,]|\.\d)")


def jahr_aus_rechnungsdaten(text: str, fakten: Fakten) -> Fakten:
    """Eine Rechnung nennt Daten ('vom 12.06.2026', 'erhalten am 20.06.2026'), das Modell setzte
    das Jahr aber nicht, und das System fragte danach. Fehlt das Jahr (und ist es nicht
    ausdrücklich unbekannt), wird es übernommen, wenn ALLE Daten im Text dasselbe Jahr haben und
    keine andere Jahreszahl vorkommt. Die Faktenbestätigung kennzeichnet das als abgeleitet
    (bitte prüfen: maßgeblich ist, wann gezahlt wurde) -- der Nutzer bestätigt oder korrigiert."""
    jahr = _einheitliches_datumsjahr(text)
    if jahr is None:
        # Fehlerquellen-Serie HT-2026-085 (14.10.2026): 'Rechnung vom 15.12.2025, bezahlt am 10.01.2026' -- zwei
        # Jahre im Text, aber genau EIN Zahlungsjahr (app/zahlungsjahr_begriffe.json). Maßgeblich ist das Jahr der
        # Zahlung (KSVG § 25 Abs. 1, R-20); die Bestätigung kennzeichnet es als abgeleitet (bitte prüfen).
        zahlungsjahre = zahlungsjahre_im_text(text)
        jahr = next(iter(zahlungsjahre)) if len(zahlungsjahre) == 1 else None
    if fakten.jahr is None and "jahr" not in fakten.unbekannt and jahr is not None:
        return fakten.model_copy(update={"jahr": jahr, "jahr_aus_rechnungsdaten": True})
    zahlungsjahre = zahlungsjahre_im_text(text)
    if (fakten.jahr is not None and len(zahlungsjahre) == 1 and fakten.jahr not in zahlungsjahre
            and str(fakten.jahr) not in _FREIES_JAHR.findall(_DATUM_JAHR.sub(" ", text))):
        # HT-2026-085: das Jahr des Modells steht nur in einem anderen Datum (z. B. dem Rechnungsdatum), gezahlt
        # wurde laut Text in einem anderen Jahr -> das Zahlungsjahr gilt (R-20), gekennzeichnet als abgeleitet.
        return fakten.model_copy(update={"jahr": next(iter(zahlungsjahre)), "jahr_aus_rechnungsdaten": True})
    if fakten.jahr_aus_rechnungsdaten and jahr is not None and fakten.jahr != jahr:
        return fakten.model_copy(update={"jahr_aus_rechnungsdaten": None})  # Jahr inzwischen genannt
    return fakten


_TEILZAHLUNG = json.loads((Path(__file__).resolve().parent / "teilzahlung_begriffe.json").read_text(encoding="utf-8"))


def teilzahlung_aus_text(text: str, fakten: Fakten) -> Fakten:
    """AT-2026-027: 'Honorar 3.000 EUR …; 1.800 EUR angezahlt, Rest 1.200 EUR stehen noch aus' -- das Modell legte nur
    die 3.000 € an. Gibt es eine Position über genau X + Y, X ist im Text gezahlt und Y offen
    (app/teilzahlung_begriffe.json), wird die Position geteilt: X zählt, Y wird als 'noch nicht bezahlt' ausgewiesen."""
    if not fakten.positionen:
        return fakten
    gezahlt = _betraege_am_begriff(text, _TEILZAHLUNG["gezahlt"])
    offen = _betraege_am_begriff(text, _TEILZAHLUNG["offen"]) - gezahlt
    paare = [(x, y) for x in gezahlt for y in offen]
    neue, geaendert = [], False
    vorhanden = {p.betrag for p in fakten.positionen}
    for p in fakten.positionen:
        passend = [(x, y) for x, y in paare if x + y == p.betrag and x not in vorhanden and y not in vorhanden]
        if len(passend) == 1 and not p.zahlungsweg_unklar:
            x, y = passend[0]
            neue.append(p.model_copy(update={"betrag": x}))
            neue.append(p.model_copy(update={"betrag": y, "zahlungsweg_unklar": True,
                                             "offen_grund": "noch nicht bezahlt (maßgeblich ist die Zahlung; bitte prüfen)"}))
            geaendert = True
        else:
            neue.append(p)
    if not geaendert:
        return fakten
    # Ein Rechnungsbetrag über X + Y bleibt die Rechnung; die Teile sind ihre Positionen (Summe gleich).
    return fakten.model_copy(update={"positionen": neue})


_ANZAHL = json.loads((Path(__file__).resolve().parent / "anzahl_begriffe.json").read_text(encoding="utf-8"))


class _Treffer:
    """Gleiche Gruppen wie das Muster 'N Rechnungen … je X': 1 = Anzahl, 3 = Euro, 4 = Cent."""

    def __init__(self, anzahl: str, euro: str, cent: str | None) -> None:
        self._g = {1: anzahl, 3: euro, 4: cent}

    def group(self, i: int):
        return self._g[i]


def anzahl_je_betrag(text: str, fakten: Fakten, neueste: str | None = None) -> Fakten:
    """HT-2026-105 (Gesamtlauf 225f380): 'fünf Rechnungen an denselben Künstler, je 250 EUR' -- das Modell legte nur
    eine Position an. Nennt der Text 'N Rechnungen … je X' und gibt es genau EINE Position, und zwar über X, werden
    N gleiche Positionen daraus (app/anzahl_begriffe.json). Sonst bleibt alles, wie es ist (nichts geraten)."""
    if not fakten.positionen or fakten.gesamtbetrag_genannt is not None:
        return fakten
    # Korpus-Lauf 15.10.2026 (gestörte Fakten): auch wenn das Modell ZU VIELE oder zu wenige gleiche Positionen anlegt
    # (zwei oder vier statt drei), gilt die Zahl aus dem Text -- nur wenn alle Positionen gleich sind (sonst unklar).
    erste = fakten.positionen[0]
    if any(p.model_dump() != erste.model_dump() for p in fakten.positionen[1:]):
        return fakten
    from app.textnorm import waehrung_nach_hinten

    t = _vereinheitliche(waehrung_nach_hinten(text))
    worte = {w: i + 2 for i, w in enumerate(_ANZAHL["zahlwoerter"])}
    einheit = "|".join(re.escape(e) for e in _ANZAHL["einheiten"])
    muster = re.compile(rf"\b(\d+|{'|'.join(worte)})\s+(?:{einheit})\b([^.;\n]{{0,{int(_ANZAHL['abstand'])}}}?)\bje\s+"
                        r"(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{1,2}))?\s*(?:€|eur\b|euro)")
    treffer = [m for m in muster.finditer(t)]
    if not treffer:
        # Testarchiv, Small (17.10.2026, AT-2026-029): 'monatlich 500 EUR, 12 Monate' (siehe _hinweis_zeitraum).
        z_einheit = "|".join(re.escape(e) for e in _ANZAHL.get("zeit_einheiten", []))
        je_einheit = "|".join(re.escape(_vereinheitliche(e)) for e in _ANZAHL.get("je_einheit", []))
        if z_einheit and je_einheit:
            betrag_re = r"(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{1,2}))?\s*(?:€|eur\b|euro)"
            abstand = int(_ANZAHL["abstand"])
            vorwaerts = re.compile(rf"\b(?:{je_einheit})\s+{betrag_re}[^.;\n]{{0,{abstand}}}?\b(\d+|{'|'.join(worte)})\s+(?:{z_einheit})\b")
            rueckwaerts = re.compile(rf"\b(\d+|{'|'.join(worte)})\s+(?:{z_einheit})\b[^.;\n]{{0,{abstand}}}?\b(?:{je_einheit})\s+{betrag_re}")
            gefunden = [(m.group(3), m.group(1), m.group(2), m) for m in vorwaerts.finditer(t)] + \
                       [(m.group(1), m.group(2), m.group(3), m) for m in rueckwaerts.finditer(t)]
            if len(gefunden) == 1:
                treffer = [_Treffer(*gefunden[0][:3])]
    if not treffer and _ANZAHL.get("je_woerter"):
        # Testarchiv, Small (17.10.2026, P-04a): 'fünfmal … jede Rechnung 250 €' (siehe _hinweis_mal).
        je_wort = "|".join(re.escape(_vereinheitliche(w)) for w in _ANZAHL["je_woerter"])
        mal = re.compile(rf"\b(\d+|{'|'.join(worte)})\s*-?\s*mal\b[^.;\n]{{0,{int(_ANZAHL.get('abstand_mal', _ANZAHL['abstand']))}}}?"
                         rf"\b(?:{je_wort})\s+(\d{{1,3}}(?:\.\d{{3}})+|\d+)(?:,(\d{{1,2}}))?\s*(?:€|eur\b|euro)")
        gefunden = list(mal.finditer(t))
        if len(gefunden) == 1:
            treffer = [_Treffer(gefunden[0].group(1), gefunden[0].group(2), gefunden[0].group(3))]
    if len(treffer) != 1:
        return fakten
    m = treffer[0]
    if len(fakten.positionen) > 1 and (neueste is None or not muster.search(_vereinheitliche(waehrung_nach_hinten(neueste)))):
        # Mehrere Positionen nur korrigieren, wenn die Mengenangabe in der AKTUELLEN Nachricht steht -- eine spätere
        # Korrektur ('Es waren nur drei Rechnungen', HT-2026-102) darf nicht von der alten Angabe im Verlauf überstimmt werden.
        return fakten
    anzahl = int(m.group(1)) if m.group(1).isdigit() else worte[m.group(1)]
    betrag = Decimal(m.group(3).replace(".", "") + (f".{m.group(4)}" if m.group(4) else ""))
    p = fakten.positionen[0]
    if anzahl < 2 or p.betrag != betrag or len(fakten.positionen) == anzahl:
        return fakten
    # Jede Rechnung ist X ('je X'): eine vom Modell angelegte Rechnung über X für diesen Auftragnehmer ist eine der
    # N Rechnungen, keine Sammelrechnung -- sie wird nicht als Rechnungsbetrag für alle N Positionen geführt.
    rechnungen = [r for r in fakten.rechnungen
                  if not (r.gesamtbetrag == betrag and r.auftragnehmer_nr == p.auftragnehmer_nr)]
    return fakten.model_copy(update={"positionen": [p.model_copy() for _ in range(anzahl)], "rechnungen": rechnungen})


def doppelte_positionen(text: str, fakten: Fakten) -> Fakten:
    """Korpus-Lauf 15.10.2026 (gestörte Fakten): ein Modell legte dieselbe Position zweimal an (Summe doppelt, aus 'nicht
    abgabepflichtig' wurde 'abgabepflichtig'). Gleiche Positionen, deren Betrag im Text seltener steht, als es Positionen
    gibt, werden auf die Zahl der Nennungen im Text gekürzt -- außer der Text nennt eine Menge ('drei Rechnungen', 'je
    400 €', 'zweimal'; app/anzahl_begriffe.json). Unabhängig vom Sprachmodell; die Faktenbestätigung zeigt das Ergebnis."""
    if len(fakten.positionen) < 2:
        return fakten
    from collections import Counter

    from app.textnorm import waehrung_nach_hinten

    t = _vereinheitliche(waehrung_nach_hinten(text))
    nennungen: dict = {}
    for m in _BETRAG_IM_TEXT.finditer(t):
        nennungen.setdefault(Decimal(m.group(1).replace(".", "") + (f".{m.group(2)}" if m.group(2) else "")), []).append(m.start())
    if not nennungen:
        return fakten  # Text ohne jeden Betrag: nichts zum Vergleichen (test_livetest_nachgespielt, Widerspruch-Knöpfe)
    worte = "|".join(re.escape(w) for w in _ANZAHL["zahlwoerter"])
    einheit = "|".join(re.escape(e) for e in _ANZAHL["einheiten"])
    if re.search(rf"\b(?:\d+|{worte})\s+(?:{einheit})\b", t):
        return fakten
    # Mengen im Text: Zahlwörter (Wert = Stelle + 2) und Ziffern, die kein Betrag, kein Jahr und kein Datum sind.
    mengen = {i + 2 for i, w in enumerate(_ANZAHL["zahlwoerter"]) if re.search(rf"(?<![0-9a-z]){re.escape(w)}(?![0-9a-z])", t)}
    mengen |= {int(m.group(1)) for m in re.finditer(r"(?<![\d.,])(\d{1,2})(?![\d.,])(?!\s*(?:€|eur\b|euro|%|\.))", t)}
    davor = re.compile(r"(?<![0-9a-z])(?:" + "|".join(re.escape(w) for w in _ANZAHL["mehrfach_davor"]) + r")(?![0-9a-z])")
    abstand = int(_ANZAHL["mehrfach_abstand"])

    def schluessel(p):
        return (p.betrag, _vereinheitliche(p.bezeichnung or "").strip(), p.rolle, p.auftragnehmer_typ, p.auftragnehmer_nr, p.rest)

    gruppen = Counter(schluessel(p) for p in fakten.positionen)
    kuerzen = {}
    for sch, anzahl in gruppen.items():
        betrag = sch[0]
        stellen = nennungen.get(betrag, [])
        # Ein Betrag, der so nicht im Text steht (errechnet, z. B. netto aus 'brutto … darin USt'), gilt als einmal genannt.
        erlaubt = len(stellen) or 1
        if anzahl < 2 or sch[5] or anzahl <= erlaubt or anzahl in mengen:
            continue
        if any(davor.search(t[max(0, s - abstand):s]) for s in stellen):
            continue
        kuerzen[sch] = erlaubt
    if not kuerzen:
        return fakten
    behalten, neue = Counter(), []
    for p in fakten.positionen:
        sch = schluessel(p)
        if sch in kuerzen:
            if behalten[sch] >= kuerzen[sch]:
                continue
            behalten[sch] += 1
        neue.append(p)
    return fakten.model_copy(update={"positionen": neue})


_VERANSTALTUNG = json.loads((Path(__file__).resolve().parent / "veranstaltung_begriffe.json").read_text(encoding="utf-8"))


def veranstaltungszahl_aus_text(text: str, fakten: Fakten) -> Fakten:
    """Korpus-Lauf 15.10.2026 (gestörte Fakten): das Modell las '5 Veranstaltungen' als 4 (aus 'abgabepflichtig' wurde
    'nicht abgabepflichtig'; die Grenze liegt bei drei). Nennt der Text genau EINE Zahl von Veranstaltungen
    ('5 Veranstaltungen', 'vier Konzerte'; app/veranstaltung_begriffe.json), gilt sie; nennt er mehrere verschiedene und
    passt die Angabe des Modells zu keiner, bleibt die Zahl offen (Rückfrage)."""
    t = _vereinheitliche(text)
    worte = {_vereinheitliche(w): i + 1 for i, w in enumerate(_VERANSTALTUNG["zahlwoerter"])}
    einheit = "|".join(re.escape(_vereinheitliche(e)) for e in _VERANSTALTUNG["einheiten"])
    zahlen = {int(m.group(1)) if m.group(1).isdigit() else worte[m.group(1)]
              for m in re.finditer(rf"(?<![0-9a-z.,])(\d+|{'|'.join(map(re.escape, worte))})\s+(?:{einheit})\b", t)}
    if len(zahlen) == 1:
        zahl = next(iter(zahlen))
        if fakten.veranstaltungszahl != zahl and (fakten.veranstaltungszahl is not None or fakten.verwerterart == "generalklausel"):
            return fakten.model_copy(update={"veranstaltungszahl": zahl})
        return fakten
    if len(zahlen) > 1 and fakten.veranstaltungszahl is not None and fakten.veranstaltungszahl not in zahlen:
        return fakten.model_copy(update={"veranstaltungszahl": None})
    return fakten


_JAHRESZAHL = re.compile(r"(?<![\d.,])((?:19|20)\d\d)(?![\d])")


def jahr_nur_aus_text(text: str, fakten: Fakten) -> Fakten:
    """Korpus-Lauf 15.10.2026 (gestörte Fakten): das Modell nannte 2025, der Text sagt nur 2024 ('hat 2024 fünf
    Veranstaltungen durchgeführt'). Nennt der Text Jahreszahlen, aber nicht die des Modells, ist sie widerlegt.
    Steht im Text genau EINE Jahreszahl, die kein Geldbetrag ist und die das Register kennt, gilt sie; sonst bleibt das
    Jahr offen (Rückfrage). Nur für die ERSTE Nachricht eines Falls (später kann das Jahr aus einem Knopf stammen)."""
    if fakten.jahr is None:
        return fakten
    jahre = [int(m.group(1)) for m in _JAHRESZAHL.finditer(text) if not _BETRAG_NACH_ZAHL.match(text, m.end())]
    if not jahre or fakten.jahr in jahre:
        return fakten  # ohne Jahreszahl im Text (z. B. Jahr aus dem Verlauf) bleibt es beim Modell
    from app.quellen import verfuegbare_jahre

    bekannt = {j for j in jahre if j in set(verfuegbare_jahre())}
    return fakten.model_copy(update={"jahr": next(iter(bekannt)) if len(bekannt) == 1 else None})


def jahr_aus_freier_jahreszahl(text: str, fakten: Fakten) -> Fakten:
    """Fehlerquellen-Serie HT-2026-094 (live 15.10.2026): 'Ist die Abgabe nach Paragraph 24 Abs. 2 KSVG 2026 4,9 Prozent?'
    -- das Modell übernahm das Jahr nicht, das System fragte nach dem Kalenderjahr. Fehlt das Jahr (und ist es nicht
    ausdrücklich unbekannt), steht im Text kein Datum und genau EINE freie Jahreszahl, die kein Geldbetrag ist und die
    das Register kennt, gilt sie als genanntes Jahr."""
    if fakten.jahr is not None or "jahr" in fakten.unbekannt or _DATUM_JAHR.search(text):
        return fakten
    from app.quellen import verfuegbare_jahre

    jahre = {int(m.group(1)) for m in _FREIES_JAHR.finditer(text) if not _BETRAG_NACH_ZAHL.match(text, m.end())}
    if len(jahre) == 1 and next(iter(jahre)) in set(verfuegbare_jahre()):
        return fakten.model_copy(update={"jahr": next(iter(jahre))})
    # Live-Lauf 16.10.2026 (ganzer Korpus, Teil 3, 9 Fälle): 'Abgabesatz Künstlersozialabgabe 2031?' -- das Modell ließ das
    # Jahr weg (es kennt keinen Satz für 2031), das System fragte nach dem Jahr, das schon dastand. Bei einer AUSKUNFT gilt
    # die eine genannte Jahreszahl auch dann, wenn das Register sie nicht kennt: die Antwort ist dann 'Nicht abgedeckt'.
    if len(jahre) == 1 and fakten.anfrageart == "auskunft":
        return fakten.model_copy(update={"jahr": next(iter(jahre))})
    return fakten


def _einheitliches_datumsjahr(text: str) -> int | None:
    datum_jahre = set(_DATUM_JAHR.findall(text))
    if len(datum_jahre) != 1:
        return None
    jahr = datum_jahre.pop()
    if any(j != jahr for j in _FREIES_JAHR.findall(_DATUM_JAHR.sub(" ", text))):
        return None
    return int(jahr)


# ---------------------------------------------------------------------------------------------
# Prüfkatalog 11.10.2026 (P-20b): ausdrücklich genannte Übungsleiter-/Ehrenamtspauschale
# ---------------------------------------------------------------------------------------------
_PAUSCHALE = json.loads((Path(__file__).resolve().parent / "pauschale_begriffe.json").read_text(encoding="utf-8"))


def _genannt_und_nicht_verneint(text: str, begriffe: list[str]) -> bool:
    t = text.lower()
    for b in begriffe:
        for m in re.finditer(re.escape(b.lower()), t):
            davor = t[: m.start()].split()[-3:]
            if not any(w.strip(".,;:()") in _PAUSCHALE["verneinung"] for w in davor):
                return True
    return False


def _pauschale_angaben_aus_text(text: str, fakten: Fakten) -> Fakten:
    """Live-Lauf 14.10.2026 (P-20b, 563ab52): das Modell setzte zur Übungsleiterpauschale Werte,
    die dem Text widersprechen; die Pauschale fiel weg, die Abgabe war zu hoch (3.500 € statt
    1.100 €). Der Text geht vor:
    - Steht 'bestätigt' ausdrücklich (nicht verneint) im Text, gilt die Bestätigung als erteilt.
    - 'bereits ausgeschöpft' gilt nur mit einem Betrag, der so im Text steht (sonst offen = nichts
      verbraucht, wie bisher). Es wird nichts geschätzt."""
    update: dict = {}
    if (fakten.pauschale_bestaetigung is False
            and _genannt_und_nicht_verneint(text, _PAUSCHALE["bestaetigt"])):
        update["pauschale_bestaetigung"] = True
    verbraucht = fakten.pauschale_bereits_ausgeschoepft
    if verbraucht is not None and (verbraucht not in betraege_im_text(text)
                                   or verbraucht not in _betraege_am_begriff(text, _PAUSCHALE["verbraucht"])):
        update["pauschale_bereits_ausgeschoepft"] = None
    # HT-2026-087: der Betrag direkt beim Pauschalen-Begriff ist die Höhe der Pauschale, keine Zahlung.
    begriffe = _PAUSCHALE["uebungsleiter"] + _PAUSCHALE["ehrenamt"]
    hoehe = _betraege_am_begriff(text, begriffe) - _betraege_am_begriff(text, _PAUSCHALE["zahlung"])
    if hoehe and any(p.betrag in hoehe for p in fakten.positionen) and len(fakten.positionen) > 1:
        update["positionen"] = [p for p in fakten.positionen if p.betrag not in hoehe]
    return fakten.model_copy(update=update) if update else fakten


def ergaenze_pauschale(text: str, fakten: Fakten) -> Fakten:
    """Nennt der Text genau eine Pauschale ausdrücklich (z. B. 'Sie hat die Übungsleiterpauschale
    schriftlich bestätigt'), das Modell ordnete die Frage aber als normale Bewertung ein, gilt die
    Anfrageart 'uebungsleiter_pauschale' (der Kern rechnet die Pauschale ab, R-50/R-51). Die
    Bestätigung wird nur gesetzt, wenn sie im Text steht. Sonst bleibt alles, wie es ist."""
    fakten = _pauschale_angaben_aus_text(text, fakten)
    if fakten.anfrageart not in (None, "bewertung"):
        return fakten
    arten = [a for a in ("uebungsleiter", "ehrenamt") if _genannt_und_nicht_verneint(text, _PAUSCHALE[a])]
    if len(arten) != 1:
        return fakten
    if fakten.pauschale_art is not None and fakten.pauschale_art != arten[0]:
        return fakten  # Modell und Text nennen verschiedene Pauschalen: nichts raten
    # Live 14.10.2026 (P-20b): Modell setzte pauschale_art, ließ aber 'bewertung' -- der Kern
    # rechnete ohne Pauschale. Nennt der Text dieselbe Pauschale, gilt die Pauschalen-Rechnung.
    update: dict = {"anfrageart": "uebungsleiter_pauschale", "pauschale_art": arten[0]}
    if fakten.pauschale_bestaetigung is None and _genannt_und_nicht_verneint(text, _PAUSCHALE["bestaetigt"]):
        update["pauschale_bestaetigung"] = True
    return fakten.model_copy(update=update)


# ---------------------------------------------------------------------------------------------
# ALLTAG-2026-999: Art des typischen Verwerters aus der Beschreibung des Auftraggebers (§ 24 Abs. 1 Nr.)
# ---------------------------------------------------------------------------------------------
_VERWERTER_NR = json.loads((Path(__file__).resolve().parent / "verwerter_nummer.json").read_text(encoding="utf-8"))


def _auftraggeber_zeilen(text: str) -> list[str]:
    return [z for z in text.lower().splitlines() if _enthaelt_begriff(z, _VERWERTER_NR["auftraggeber_zeile"])
            and not _RT_ZEILE.match(z)]


def verwerter_aus_auftraggeber(text: str, fakten: Fakten) -> Fakten:
    """Sucht in den Zeilen, die den AUFTRAGGEBER beschreiben ('Rechnung an: Mittelstands Messe
    Koblenz GmbH, Veranstalterin …'), die Art des Unternehmens (app/verwerter_nummer.json):
    - `verwerter_regel` = die Regel mit der richtigen Nummer des § 24 Abs. 1 (z. B. R-126 Messe,
      R-03 Nr. 3), damit die Antwort nicht immer Nr. 7 nennt;
    - fehlt die Art des Auftraggebers noch, belegt ein Treffer einen typischen Verwerter
      (Messegesellschaft mit Eigenveranstaltungen: KSK-Info 13, R-126). Nennt der Text zugleich
      Eigenwerbung oder eine Privatperson, wird nichts gesetzt (dann fragt das System)."""
    zeilen = _auftraggeber_zeilen(text)
    if not zeilen:
        return fakten  # die Nachricht beschreibt den Auftraggeber nicht: gespeicherter Stand bleibt
    treffer = None
    for eintrag in _VERWERTER_NR["regeln"]:
        if any(_enthaelt_begriff_als_wort(z, eintrag["begriffe"]) for z in zeilen):
            treffer = eintrag
            break
    update: dict = {"verwerter_regel": ";".join(treffer["regeln"]) if treffer else None}
    if (treffer and treffer.get("typisch") and fakten.verwerterart is None
            and _erkenne_verwerterart(text) in (None, "typischer_verwerter") and not privater_auftraggeber(text)):
        update["verwerterart"] = "typischer_verwerter"
    if update == {"verwerter_regel": fakten.verwerter_regel}:
        return fakten
    return fakten.model_copy(update=update)


_VEREIN = json.loads((Path(__file__).resolve().parent / "verein_begriffe.json").read_text(encoding="utf-8"))


def musikverein_generalklausel(text: str, fakten: Fakten) -> Fakten:
    """14.10.2026 (P-16, P-17): nicht kommerzielle Musikvereine (Hobby-/Laienmusik, Liebhaberorchester) fallen
    nur unter die Generalklausel: mindestens vier Veranstaltungen und Entgelte über der Schwelle; Zahlungen an
    vereinseigene Chorleiter und Dirigenten bleiben außer Betracht (R-30, R-57; KSK-Info 12, Abschn. 4).
    - Art des Auftraggebers 'generalklausel' nur mit Verein UND Freizeit-Hinweis im Text, ohne andere Art
      (ein Chor/Orchester mit überwiegendem Aufführungszweck ist typischer Verwerter, R-159).
    - Rolle 'vereinseigene_leitung' nur für Positionen mit Leitungs-Begriff in der Bezeichnung und
      'vereinseigen' direkt beim Betrag; nur im Vereins-Fall der Generalklausel. Begriffe: app/verein_begriffe.json."""
    t = text.lower()
    verein = (_enthaelt_begriff(t, _VEREIN["verein"]) and _enthaelt_begriff(t, _VEREIN["freizeit"])
              and not _enthaelt_begriff(t, _VEREIN["nicht_wenn"]))
    update: dict = {}
    if (verein and fakten.verwerterart is None and _erkenne_verwerterart(text) is None
            and not privater_auftraggeber(text)):
        update["verwerterart"] = "generalklausel"
        update["verwerter_regel"] = ";".join(_VEREIN["regeln"])
    art = update.get("verwerterart", fakten.verwerterart)
    vereinseigen = _betraege_am_begriff(text, _VEREIN["vereinseigen"])
    positionen, geaendert = [], False
    for p in fakten.positionen:
        if p.rolle == "vereinseigene_leitung" and not (verein and art == "generalklausel"):
            p = p.model_copy(update={"rolle": None}); geaendert = True   # nur im Vereins-Fall
        # Gesamtlauf b87a9bb (P-16 FALSCH): das Modell setzte selbst 'honorar' -- die Standardrolle verhindert R-57 nicht.
        elif (verein and art == "generalklausel" and p.rolle in (None, "honorar") and p.betrag in vereinseigen
              and _enthaelt_begriff((p.bezeichnung or "").lower(), _VEREIN["leitung"])):
            p = p.model_copy(update={"rolle": "vereinseigene_leitung"}); geaendert = True
        positionen.append(p)
    if geaendert:
        update["positionen"] = positionen
    return fakten.model_copy(update=update) if update else fakten


_ZAHLUNGSWEG = json.loads((Path(__file__).resolve().parent / "zahlungsweg_begriffe.json").read_text(encoding="utf-8"))


def zahlungsweg_im_freitext(text: str, fakten: Fakten) -> Fakten:
    """Härtetest HT-2026-001 (14.10.2026): Durchleitung oder offene Erstattung im Freitext OHNE Rechnungsteller-
    Zeile (die Agentur fragt selbst). Zu jedem Euro-Betrag gehört der Text vom vorigen bis zum nächsten
    Euro-Betrag; nennt er einen Begriff aus app/zahlungsweg_begriffe.json ('durchgeleitet', 'privat von seinem
    Konto', 'ob wir das erstatten'), wird die Position 'zahlungsweg_unklar' (Steuerberater entscheidet, nie still
    mitgezählt). Im Zweifel eine Position zu viel: das ergibt einen Grenzfall, nie eine falsche Zahl.
    Mit Rechnungsteller-Zeile gilt rechnungsteller_als_zahlungsempfaenger (dort ist die Sicht die des Kunden).

    Härtetest-Serie HT-2026-002 bis 011 (14.10.2026): je Grund eine Begriffsliste ('gruende': Durchleitung,
    Erstattung offen, noch nicht bezahlt, Gutschrift, keine Zahlung an den Künstler, Vermittlungsprovision). Der
    Grund, dessen Begriff dem Betrag am nächsten steht, wird als `offen_grund` angezeigt."""
    if not fakten.positionen or rechnungsteller_typ(text) is not None:
        return fakten
    t = _vereinheitliche(text)
    treffer = list(_BETRAG_IM_TEXT.finditer(t))
    if not treffer:
        return fakten
    gruende = [(g["grund"], [_vereinheitliche(b) for b in g["begriffe"]], bool(g.get("nur_satz")))
               for g in _ZAHLUNGSWEG["gruende"]]
    offen: dict = {}
    for i, m in enumerate(treffer):
        von = treffer[i - 1].end() if i > 0 else 0
        bis = treffer[i + 1].start() if i + 1 < len(treffer) else len(t)
        bester = None  # (Abstand, Grund)
        # Satzgrenzen um den Betrag (für Gründe mit 'nur_satz')
        satz_von = max([g.end() for g in _SATZ_GRENZE.finditer(t[:m.start()])], default=0)
        naechste = _SATZ_GRENZE.search(t, m.end())
        satz_bis = naechste.start() if naechste else len(t)
        for grund, begriffe, nur_satz in gruende:
            v, b_ende = (max(von, satz_von), min(bis, satz_bis)) if nur_satz else (von, bis)
            for b in begriffe:
                for x in re.finditer(re.escape(b), t[v:m.start()]):
                    abstand = m.start() - (v + x.end())
                    if bester is None or abstand < bester[0]:
                        bester = (abstand, grund)
                for x in re.finditer(re.escape(b), t[m.end():b_ende]):
                    if bester is None or x.start() < bester[0]:
                        bester = (x.start(), grund)
        if bester is not None:
            betrag = Decimal(m.group(1).replace(".", "") + (f".{m.group(2)}" if m.group(2) else ""))
            offen.setdefault(betrag, bester[1])
    if not offen:
        return fakten
    neue, geaendert = [], False
    for p in fakten.positionen:
        if (p.betrag in offen and not p.zahlungsweg_unklar and not p.vertrag_direkt
                and p.rolle not in _GUELTIGE_ROLLEN - {"honorar"}):
            p = p.model_copy(update={"zahlungsweg_unklar": True, "offen_grund": offen[p.betrag]}); geaendert = True
        neue.append(p)
    return fakten.model_copy(update={"positionen": neue}) if geaendert else fakten


_ZAHLUNGSJAHR = json.loads((Path(__file__).resolve().parent / "zahlungsjahr_begriffe.json").read_text(encoding="utf-8"))
_JAHR_LISTE = re.compile(r"(?:^|[\s;,(])((?:19|20)\d{2})\s*:")
_SATZ_GRENZE = re.compile(r"[.!?;](?=\s|$)|(?<!\d)[.!?;](?!\d)|\n")


def zahlungsjahre_im_text(text: str) -> set:
    """Kalenderjahre, in denen laut Text GEZAHLT wurde (app/zahlungsjahr_begriffe.json): Datum mit Zahlwort
    davor oder danach, Jahreszahl als Aufzählung ('2024: …'), oder Satz mit freier Jahreszahl, Zahlverb und
    Euro-Betrag. Nur Jahre, die das Register kennt (app.quellen.verfuegbare_jahre) -- kein Jahr im Code."""
    from app.quellen import verfuegbare_jahre

    bekannt = set(verfuegbare_jahre())
    t = _vereinheitliche(text)
    davor = [_vereinheitliche(b) for b in _ZAHLUNGSJAHR["zahlwort_davor"]]
    danach = [_vereinheitliche(b) for b in _ZAHLUNGSJAHR["zahlwort_danach"]]
    verben = [_vereinheitliche(b) for b in _ZAHLUNGSJAHR["zahlverb"]]
    jahre: set = set()
    zahldaten: list = []  # Stellen der erkannten Zahlungsdaten
    for m in _DATUM_JAHR.finditer(t):
        vorher = t[max(0, m.start() - _ZAHLUNGSJAHR["abstand_davor"]): m.start()]
        nachher = t[m.end(): m.end() + _ZAHLUNGSJAHR["abstand_danach"]]
        if _enthaelt_begriff(vorher, davor) or _enthaelt_begriff(nachher, danach):
            jahre.add(int(m.group(1)))
            zahldaten.append(m.start())
    for m in _JAHR_LISTE.finditer(t):
        jahre.add(int(m.group(1)))
    pos = 0
    for satz in _SATZ_GRENZE.split(t):
        anfang = t.find(satz, pos) if satz else pos
        pos = anfang + len(satz or "")
        if not satz or not _enthaelt_begriff(satz, verben) or not _BETRAG_IM_TEXT.search(satz):
            continue
        if any(anfang <= z < pos for z in zahldaten):
            continue  # der Satz nennt sein Zahlungsdatum schon; eine freie Jahreszahl daneben ist kein zweites
        ohne_datum = _DATUM_JAHR.sub(" ", satz)
        for j in _FREIES_JAHR.findall(ohne_datum):
            if not _BETRAG_NACH_ZAHL.match(ohne_datum, ohne_datum.find(j) + len(j)):
                jahre.add(int(j))
    return {j for j in jahre if j in bekannt}


def markiere_mehrere_zahlungsjahre(text: str, fakten: Fakten) -> Fakten:
    """Härtetest HT-2026-002 (14.10.2026): 1.500 € (gezahlt 2020) und 900 € (gezahlt 2026) wurden zu 2.400 €
    zusammengezählt und mit dem Satz eines Jahres gerechnet. Die Abgabe gilt je Kalenderjahr der Zahlung
    (KSVG § 25 Abs. 1, R-20). Nennt der Text zwei oder mehr Zahlungsjahre, setzt das System
    `mehrere_zahlungsjahre` (z. B. '2020, 2026'); app/pflichtangaben.py fragt dann, statt zu rechnen."""
    if fakten.anfrageart not in (None, "bewertung"):
        wert = None
    else:
        jahre = zahlungsjahre_im_text(text)
        wert = ", ".join(str(j) for j in sorted(jahre)) if len(jahre) > 1 else None
    if wert == fakten.mehrere_zahlungsjahre:
        return fakten
    return fakten.model_copy(update={"mehrere_zahlungsjahre": wert})


_RECHTSFORMWECHSEL = json.loads((Path(__file__).resolve().parent / "rechtsformwechsel_begriffe.json").read_text(encoding="utf-8"))


def markiere_rechtsformwechsel(text: str, fakten: Fakten) -> Fakten:
    """Härtetest HT-2026-008 (14.10.2026): 'bis 31.05.2025 war ich Einzelunternehmer, seit 01.06.2025 eine UG' --
    die Zahlungen beider Unternehmer wurden zusammengezählt. Nennt der Text einen Rechtsformwechsel
    (app/rechtsformwechsel_begriffe.json), setzt das System `rechtsformwechsel`; app/pflichtangaben.py fragt."""
    wert = True if (fakten.anfrageart in (None, "bewertung") and _enthaelt_begriff(
        _vereinheitliche(text), [_vereinheitliche(b) for b in _RECHTSFORMWECHSEL["wechsel"]])) else None
    if wert == fakten.rechtsformwechsel:
        return fakten
    return fakten.model_copy(update={"rechtsformwechsel": wert})


_VERTRETUNG = json.loads((Path(__file__).resolve().parent / "vertretung_begriffe.json").read_text(encoding="utf-8"))


def ergaenze_vertretung(text: str, fakten: Fakten) -> Fakten:
    """14.10.2026 (P-36, P-37): Grundsatzfragen ohne Betrag (app/vertretung_begriffe.json).
    - Vertretung (R-33): 'im Namen und für Rechnung' eines KÜNSTLERS (das Wort danach ist ein Begriff aus
      'kuenstler'); nicht bei 'im eigenen Namen'. 'Im Namen unseres Kunden' ist keine Vertretung des Künstlers.
    - Nachweismakler (R-35): ein Begriff aus 'nachweis' UND mindestens so viele Begriffe aus 'ohne_mitwirkung',
      wie 'mindestens_ohne_mitwirkung' verlangt (kein Vertragsschluss, keine Organisation, kein Honorar, keine Haftung).
    Der Text entscheidet; was das Modell in diese Felder schreibt, wurde vorher verworfen (ohne_systemfelder)."""
    t = _vereinheitliche(text)
    update: dict = {}
    vertretung = False
    if not _enthaelt_begriff(t, [_vereinheitliche(b) for b in _VERTRETUNG["nicht_wenn"]]):
        for formel in _VERTRETUNG["formel"]:
            for m in re.finditer(re.escape(_vereinheitliche(formel)) + r"\s+(?:des|der|eines|einer|von|unseres|unserer|seines|seiner|ihres|ihrer)?\s*([\w-]+)", t):
                if _enthaelt_begriff(m.group(1), [_vereinheitliche(k) for k in _VERTRETUNG["kuenstler"]]):
                    vertretung = True
    if vertretung and fakten.vertretung_kuenstler is None:
        update["vertretung_kuenstler"] = True
    ohne = sum(1 for b in _VERTRETUNG["ohne_mitwirkung"] if _vereinheitliche(b) in t)
    if (_enthaelt_begriff(t, [_vereinheitliche(b) for b in _VERTRETUNG["nachweis"]])
            and ohne >= _VERTRETUNG["mindestens_ohne_mitwirkung"] and not vertretung and fakten.nachweismakler is None):
        update["nachweismakler"] = True
    return fakten.model_copy(update=update) if update else fakten


_EINNAHME = json.loads((Path(__file__).resolve().parent / "einnahme_begriffe.json").read_text(encoding="utf-8"))


def ergaenze_einnahmeabsicht(text: str, fakten: Fakten) -> Fakten:
    """14.10.2026 (P-16): 'Konzerte mit Eintritt' ist eine Einnahme (KSK-Info 12, Abschn. 4: Eintrittsgelder,
    Verkauf von Speisen und Getränken). Nur bei der Generalklausel, nur wenn die Angabe fehlt, nur mit Beleg
    und ohne Gegenbegriff ('Eintritt frei') -- sonst fragt das System wie bisher (app/einnahme_begriffe.json)."""
    if fakten.verwerterart != "generalklausel":
        return fakten
    t = text.lower()
    nein = _enthaelt_begriff(t, _EINNAHME["nicht_wenn"])
    ja = _enthaelt_begriff(t, _EINNAHME["einnahmen"]) or any(
        _enthaelt_begriff(satz, _EINNAHME.get("satz_einnahme", [])) and _enthaelt_begriff(satz, _EINNAHME.get("satz_absicht", []))
        for satz in _SATZ_GRENZE.split(t) if satz)
    # Korpus-Lauf 15.10.2026 (gestörte Fakten): das Modell drehte die Einnahmeabsicht um ('Wir verkaufen Eintrittskarten'
    # -> nein). Widerspricht die Angabe des Modells einer eindeutigen Aussage im Text, gilt sie nicht (Rückfrage oder,
    # bei eindeutigem 'ja', die Aussage des Textes wie bisher).
    if (fakten.einnahmeabsicht is True and nein and not ja) or (fakten.einnahmeabsicht is False and ja and not nein):
        fakten = fakten.model_copy(update={"einnahmeabsicht": None})
    if fakten.einnahmeabsicht is not None or nein:
        return fakten
    if ja:
        return fakten.model_copy(update={"einnahmeabsicht": True})
    return fakten


def _betraege_direkt_nach(text: str, begriffe: list[str], abstand: int) -> set:
    """Beträge, vor denen höchstens `abstand` Zeichen vorher einer der Begriffe steht ('Honorar 2.000 EUR')."""
    from decimal import Decimal

    t = _vereinheitliche(text)
    worte = [_vereinheitliche(b) for b in begriffe]
    ergebnis = set()
    for m in _BETRAG_IM_TEXT.finditer(t):
        if _enthaelt_begriff(t[max(0, m.start() - abstand): m.start()], worte):
            ergebnis.add(Decimal(m.group(1).replace(".", "") + (f".{m.group(2)}" if m.group(2) else "")))
    return ergebnis


def _einziger_betrag_im_satz_mit(text: str, begriffe: list[str], wortanfang: bool = True,
                                 nicht_im_satz: list[str] | None = None, nur_davor: bool = False) -> set:
    """Fehlerquellen-Serie HT-2026-088 (15.10.2026): 'Fahrt 300 km mit Einzelbelegen (Logbuch) erstattet: 90 EUR' --
    das Beleg-Wort steht mehr als 30 Zeichen vor dem Betrag. Steht in einem Satz genau EIN Euro-Betrag, gehört ein
    Begriff in diesem Satz zu ihm (`nur_davor`: nur vor dem Betrag). Enthält der Satz ein Wort aus `nicht_im_satz`,
    zählt er nicht. Satzgrenze: Punkt/Ausrufe-/Fragezeichen vor Leerraum oder nicht zwischen Ziffern, Semikolon,
    Zeilenumbruch."""
    from decimal import Decimal

    davor = r"(?<![0-9a-z])" if wortanfang else ""
    muster = [re.compile(davor + re.escape(_vereinheitliche(b))) for b in begriffe]
    sperre = [_vereinheitliche(b) for b in (nicht_im_satz or [])]
    ergebnis = set()
    for satz in _SATZ_GRENZE.split(_vereinheitliche(text)):
        betraege = list(_BETRAG_IM_TEXT.finditer(satz or ""))
        if len(betraege) != 1 or (sperre and _enthaelt_begriff(satz, sperre)):
            continue
        b = betraege[0]
        bereich = satz[: b.start()] if nur_davor else satz
        if any(m.search(bereich) for m in muster):
            ergebnis.add(Decimal(b.group(1).replace(".", "") + (f".{b.group(2)}" if b.group(2) else "")))
    return ergebnis


def ergaenze_reisekosten_rolle(text: str, fakten: Fakten) -> Fakten:
    """Prüfkatalog P-30 (live, schwankend): '80 € nachgewiesene Bahnfahrtkosten' -- das Modell setzte die
    Rolle mal, mal nicht; ohne Rolle wurde die Position 'unsicher' (Grenzfall). Steht direkt beim Betrag
    (30 Zeichen) ein Reise-Begriff UND ein Nachweis-Begriff und keine Pauschale, gilt die Rolle
    'fahrtkosten_nachgewiesen' (R-47; Begriffe aus app/rollen_belege.json). Nur für Positionen ohne Rolle."""
    regel = _NACHWEIS_NOETIG.get("fahrtkosten_nachgewiesen")
    begriffe = _ROLLEN_BELEGE.get("fahrtkosten_nachgewiesen")
    if not regel or not begriffe or not fakten.positionen:
        return fakten
    sperre = regel.get("nicht_im_satz", [])
    reise = _betraege_am_begriff(text, begriffe) | _einziger_betrag_im_satz_mit(
        text, begriffe, nicht_im_satz=sperre, nur_davor=True)
    nachweis = _betraege_am_begriff(text, regel["nachweis"]) | _einziger_betrag_im_satz_mit(
        text, regel["nachweis"], nicht_im_satz=sperre)
    honorar = _betraege_direkt_nach(text, regel.get("honorar_direkt_davor", []), regel.get("honorar_abstand", 0))
    reise -= honorar
    pauschal = (_betraege_am_begriff(text, regel["nicht_wenn_bezeichnung"])
                | _einziger_betrag_im_satz_mit(text, regel["nicht_wenn_bezeichnung"], wortanfang=False))
    neu, geaendert = [], False
    for p in fakten.positionen:
        if (p.rolle is None and p.betrag in reise and p.betrag in nachweis and p.betrag not in pauschal
                and not (p.bezeichnung and _enthaelt_begriff(_vereinheitliche(p.bezeichnung), regel["nicht_wenn_bezeichnung"]))):
            p = p.model_copy(update={"rolle": "fahrtkosten_nachgewiesen", "nachgewiesen": True})
            geaendert = True
        neu.append(p)
    return fakten.model_copy(update={"positionen": neu}) if geaendert else fakten


_EINSTIEG = json.loads((Path(__file__).resolve().parent / "einstieg_begriffe.json").read_text(encoding="utf-8"))


def mehrere_fragen(text: str) -> bool:
    """Siehe app/einstieg_begriffe.json, '_hinweis_mehrere_fragen'."""
    ab = int(_EINSTIEG.get("mehrere_fragen_ab", 0) or 0)
    if not ab:
        return False
    return len(zerlege_fragen(text)) >= ab


def hinweis_max_woerter() -> int:
    """Bis zu so vielen Wörtern bleibt eine Nachricht, die das Modell als Begrüßung einordnet, eine Begrüßung."""
    return int(_EINSTIEG.get("hinweis_max_woerter", 0) or 0)


def zerlege_fragen(text: str) -> list[str]:
    """Die einzelnen Fragen einer Sammelnachricht (app/warteschlange.py): je Zeile, die mit einem Fragezeichen endet,
    eine Frage. Zeilen ohne Fragezeichen davor gehören zur folgenden Frage (Sachverhalt), danach zur letzten
    (Nachsatz). Anführungszeichen am Rand und ein Klammerzusatz am Ende ('(Hier soll … kommen.)') fallen weg; der
    Wortlaut sonst bleibt."""
    fragen: list[str] = []
    sammel: list[str] = []
    # Nur Zeilen trennen: mehrere Fragen in EINER Zeile gehören meist zum selben Fall ('Ist das abgabepflichtig? Wie hoch
    # ist die Abgabe? Muss ich melden?') und bleiben zusammen.
    for zeile in text.splitlines():
        z = zeile.strip()
        if not z:
            continue
        ohne_zusatz = re.sub(r"\s*\([^()]*\)\s*$", "", z)
        sauber = ohne_zusatz.strip(" \t\"“”„'»«")
        if re.search(r"\?$", sauber):
            fragen.append(" ".join([*sammel, sauber]))
            sammel = []
        else:
            sammel.append(z.strip(" \t\"“”„'»«"))
    if sammel:
        if fragen:
            fragen[-1] = " ".join([fragen[-1], *sammel])
        else:
            return [text]
    return fragen


def rechnung_angekuendigt_ohne_inhalt(text: str) -> bool:
    """Test-Dialog 'Der schwierige Kunde' (13.10.2026), Schritt 1: Die Nachricht kündigt eine
    Rechnung an, enthält sie aber nicht. Ohne Rechnung gibt es nichts zu bewerten; statt einer
    Rückfrage nach dem Jahr bittet der Chatbot um die Rechnung (fester Baustein, kein Modell).
    Wahr nur, wenn ein Begriff aus app/einstieg_begriffe.json vorkommt und der Text KEINEN Betrag,
    keine andere Zahl als eine Jahreszahl, keine Positionszeile und keine Rechtsform des
    Auftragnehmers enthält (dann ist schon etwas zu prüfen, und der normale Weg gilt)."""
    t = text.lower()
    if not any(b in t for b in _EINSTIEG["angekuendigt"]):
        return False
    if betraege_im_text(text) or any(p in t for p in _EINSTIEG["positionszeile"]):
        return False
    stellen = int(_EINSTIEG["jahreszahl_stellen"])
    if any(len(z) != stellen for z in re.findall(r"\d+", text)):
        return False
    return erkenne_rechtsform_auftragnehmer(text) is None


_WAEHRUNG = json.loads((Path(__file__).resolve().parent / "waehrung_begriffe.json").read_text(encoding="utf-8"))
_ZAHL = r"(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{1,2}))?"


def _waehrung_muster() -> list[tuple[str, re.Pattern[str]]]:
    erg = []
    for code, namen in _WAEHRUNG["fremd"].items():
        for name in sorted(namen, key=len, reverse=True):
            n = re.escape(name)
            grenze = r"(?![\w])" if name[-1].isalnum() else ""
            # Zahl vor der Bezeichnung ('2.000 US-Dollar', '1.500 $') oder danach ('USD 2.000', '$1.500')
            erg.append((code, re.compile(_ZAHL + r"\s*" + n + grenze, re.IGNORECASE)))
            erg.append((code, re.compile(r"(?<![\w])" + n + r"\s*" + _ZAHL, re.IGNORECASE)))
    return erg


_WAEHRUNG_MUSTER = _waehrung_muster()


def _als_dezimal(ganz: str, nachkomma: str | None) -> Decimal:
    return Decimal(ganz.replace(".", "") + (f".{nachkomma}" if nachkomma else ""))


def fremdwaehrung_betraege(text: str) -> list[tuple[Decimal, str, int]]:
    """[(Betrag, Währungscode, Satznummer)] aller Beträge in fremder Währung. Nur Erkennung, keine
    Umrechnung. Überlappende Treffer zählen einmal (längste Bezeichnung zuerst)."""
    saetze = re.split(_WAEHRUNG["satzgrenze"], text)
    erg: list[tuple[Decimal, str, int]] = []
    for nr, satz in enumerate(saetze):
        belegt: list[tuple[int, int]] = []
        for code, muster in _WAEHRUNG_MUSTER:
            for m in muster.finditer(satz):
                if any(m.start() < e and s < m.end() for s, e in belegt):
                    continue
                belegt.append((m.start(), m.end()))
                erg.append((_als_dezimal(m.group(1), m.group(2)), code, nr))
    return erg


def fremdbetrag_als_zahl(wert, text: str) -> Decimal | None:
    """Modell-Ausgabe '1500 $' / '500 USD' statt einer Zahl (Live-Lauf 14.10.2026): nur die Zahl,
    und nur wenn GENAU dieser Betrag in DIESER Währung im Nutzertext steht. Sonst None (die
    Schemaprüfung verwirft die Antwort wie bisher). Keine Umrechnung; die Kennzeichnung als
    'Euro-Betrag offen' macht danach markiere_fremdwaehrung aus dem Text."""
    if not isinstance(wert, str):
        return None
    treffer = fremdwaehrung_betraege(wert)
    if len(treffer) != 1:
        return None
    betrag, code, _ = treffer[0]
    rest = wert
    for _, muster in _WAEHRUNG_MUSTER:
        rest = muster.sub("", rest)
    if rest.strip():
        return None  # außer Zahl und Währung steht noch etwas darin: nicht eindeutig
    if any(b == betrag and c == code for b, c, _ in fremdwaehrung_betraege(text)):
        return betrag
    return None


def _euro_je_satz(text: str) -> dict[int, list[Decimal]]:
    saetze = re.split(_WAEHRUNG["satzgrenze"], text)
    return {nr: sorted(betraege_im_text(s)) for nr, s in enumerate(saetze)}


def _anzeige_fremd(betrag: Decimal, code: str) -> str:
    ganz, _, rest = f"{betrag:,.2f}".partition(".")
    text = ganz.replace(",", ".") + ("," + rest if rest != "00" else "")
    return f"{text} {code}"


def unbekannt_nur_mit_beleg(text: str, fakten: Fakten) -> Fakten:
    """Testfall 20 Positionen mit mistral-small-latest (17.10.2026): das Modell schrieb
    'unbekannt': ['kuenstlerisch', 'auftragnehmer_typ'], obwohl der Text 'selbständige Einzelperson' sagt. 'Ausdrücklich
    unbekannt' heißt: nicht mehr fragen -- der Fall blieb eine Rückfrage OHNE Frage. Eine Angabe gilt nur dann als
    unbekannt, wenn der Nutzer das selbst schreibt (feste Erkennung app/fallstand.py::unbekannt_im_text); alles andere aus
    der Liste des Modells wird verworfen, dann fragt das System wie sonst nach."""
    if not fakten.unbekannt:
        return fakten
    from app import fallstand

    belegt = set(fallstand.unbekannt_im_text(text))
    behalten = [k for k in fakten.unbekannt if fallstand.zerlege(k)[0] in belegt]
    if behalten == list(fakten.unbekannt):
        return fakten
    return fakten.model_copy(update={"unbekannt": behalten})


def ohne_systemfelder(fakten: Fakten) -> Fakten:
    """Live-Lauf 14.10.2026 (W-03, 7fdc4f9): das Modell füllte die Währungsfelder selbst
    ('fremd_betrag': '2000') -- das System fragte dann nach einem Euro-Betrag, der schon im Text
    stand. Diese Felder setzt NUR das System (markiere_fremdwaehrung, aus dem Text); was das Modell
    dort einträgt, wird verworfen."""
    if fakten.herkunft or fakten.katalog_taetigkeit is not None:
        # Umbau Schritt 1 (16.10.2026): Herkunft und Katalog-Tätigkeit setzt nur das System (app/einordnung.py).
        fakten = fakten.model_copy(update={"herkunft": {}, "katalog_taetigkeit": None})
    if not (fakten.gesamt_fremdwaehrung or fakten.vertretung_kuenstler is not None or fakten.nachweismakler is not None
            or fakten.mehrere_zahlungsjahre or fakten.rechtsformwechsel is not None
            or any(p.fremdwaehrung or p.fremd_betrag or p.offen_grund for p in fakten.positionen)):
        return fakten
    return fakten.model_copy(update={
        "gesamt_fremdwaehrung": None, "vertretung_kuenstler": None, "nachweismakler": None,
        "mehrere_zahlungsjahre": None, "rechtsformwechsel": None,
        "positionen": [p.model_copy(update={"fremdwaehrung": None, "fremd_betrag": None, "offen_grund": None})
                       for p in fakten.positionen]})


def markiere_fremdwaehrung(text: str, fakten: Fakten) -> Fakten:
    """Rechnungen in fremder Währung (14.10.2026, Testfall L-23). Ein Betrag, der im Text nur in
    fremder Währung steht ('2.000 US-Dollar'), wird NICHT als Euro gerechnet:
    - Steht im selben Satz genau ein Euro-Betrag ('abgebucht wurden 1.850,00 €'), zählt dieser
      (eine Position mit dem Fremdbetrag wird darauf gesetzt bzw. als doppelt entfernt).
    - Sonst wird die Position als 'Euro-Betrag offen' markiert (Position.fremdwaehrung);
      app/pflichtangaben.py fragt nach dem tatsächlich gezahlten Euro-Betrag, der Kern rechnet nicht.
    Es wird nie umgerechnet. Ein Gesamtbetrag nur in fremder Währung wird ebenso behandelt."""
    fremd = fremdwaehrung_betraege(text)
    if not fremd:
        return fakten
    euro_im_text = betraege_im_text(text)
    if (not fakten.positionen and fakten.gesamtbetrag_genannt is None and not fakten.gesamt_fremdwaehrung
            and not euro_im_text and len({(b, c) for b, c, _ in fremd}) == 1):
        # Live 14.10.2026 (W-05, 615dffa): das Modell las '1.500 $' gar nicht aus; das System fragte allgemein
        # 'Um welchen Betrag geht es?'. Steht genau EIN Betrag in fremder Währung und kein Euro-Betrag im Text,
        # ist er der genannte Gesamtbetrag -- offen bleibt nur der gezahlte Euro-Betrag (nie umgerechnet).
        betrag, code, _ = fremd[0]
        return fakten.model_copy(update={"gesamt_fremdwaehrung": _anzeige_fremd(betrag, code)})
    euro_satz = _euro_je_satz(text)
    positionen = [p.model_copy() for p in fakten.positionen]
    entfernen: set[int] = set()
    for betrag, code, satz in fremd:
        if betrag in euro_im_text:
            continue  # dieselbe Zahl steht auch als Euro-Betrag im Text: nicht eindeutig fremd
        paar = euro_satz.get(satz, [])
        euro = paar[0] if len(paar) == 1 else None
        for i, p in enumerate(positionen):
            if i in entfernen or p.betrag != betrag:
                continue
            anzeige = _anzeige_fremd(betrag, code)
            if euro is not None:
                andere = [j for j, q in enumerate(positionen) if j != i and q.betrag == euro and j not in entfernen]
                if andere:  # Modell hat Fremd- und Euro-Betrag als zwei Positionen angelegt
                    entfernen.add(i)
                    ziel = positionen[andere[0]]
                    # Angaben der doppelten Position (z. B. Bezeichnung) übernehmen, wo die Euro-Position leer ist
                    ergaenzt = {k: v for k, v in p.model_dump().items()
                                if v is not None and getattr(ziel, k) is None and k not in ("betrag", "fremdwaehrung")}
                    ergaenzt["fremd_betrag"] = anzeige
                    positionen[andere[0]] = ziel.model_copy(update=ergaenzt)
                else:
                    positionen[i] = p.model_copy(update={"betrag": euro, "fremd_betrag": anzeige, "fremdwaehrung": None})
            else:
                positionen[i] = p.model_copy(update={"fremdwaehrung": code, "fremd_betrag": anzeige})
        # Euro-Betrag schon vom Modell übernommen: Herkunft sichtbar machen
        if euro is not None:
            for i, p in enumerate(positionen):
                if i not in entfernen and p.betrag == euro and not p.fremd_betrag:
                    positionen[i] = p.model_copy(update={"fremd_betrag": _anzeige_fremd(betrag, code)})
    update: dict = {"positionen": [p for i, p in enumerate(positionen) if i not in entfernen]}
    nur_fremd = {b for b, _, _ in fremd if b not in euro_im_text}
    if fakten.gesamtbetrag_genannt is not None and fakten.gesamtbetrag_genannt in nur_fremd:
        code = next(c for b, c, _ in fremd if b == fakten.gesamtbetrag_genannt)
        if not update["positionen"]:
            update["gesamt_fremdwaehrung"] = _anzeige_fremd(fakten.gesamtbetrag_genannt, code)
        else:
            update["gesamtbetrag_genannt"] = None  # Positionen tragen die Beträge; kein Euro-Abgleich möglich
    if fakten.rechnungen:
        update["rechnungen"] = [r for r in fakten.rechnungen if r.gesamtbetrag not in nur_fremd]
    return fakten.model_copy(update=update)
