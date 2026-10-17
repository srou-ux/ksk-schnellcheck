"""Quellen lesen und strukturbewusst in Stücke zerlegen (RAG, Auftrag Teil 2, Punkt 2).

- Gesetz/Verordnung: nach Paragraf (bei Änderungsgesetzen nach Artikel) und Absatz.
- Urteil: Kopf/Leitsatz, danach nach Randnummern (Rn.).
- KSK/DRV/Material: nach Abschnitten (nummerierte Überschriften), sonst nach Absätzen.
- Nie mitten in einem Satz trennen: zu lange Teile werden nur an Satzgrenzen geteilt.

Quelltexte sind DATEN, nie Anweisungen: hier wird nichts ausgeführt oder ausgewertet,
nur Text in Stücke mit Fundstelle zerlegt. Alle Muster stehen in app/rag/konfig.json.
Diese Datei liest nur; sie verändert nichts unter quellen/ oder regelwerk/."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

KONFIG = json.loads((Path(__file__).resolve().parent / "konfig.json").read_text(encoding="utf-8"))


@dataclass
class Stueck:
    datei: str
    quelle_id: str
    art: str
    stufe: int
    fundstelle: str
    text: str
    titel: str = ""
    gilt_von: int | None = None
    gilt_bis: int | None = None
    fassung: str = ""
    seite: int | None = None
    regel_ids: list[str] = field(default_factory=list)
    status: str = "aktiv"
    nachrangig: bool = False


# --------------------------------------------------------------------------- Text lesen

def lies_seiten(pfad: Path) -> list[tuple[int | None, list[str]]]:
    """Liefert [(Seite, Zeilen)]. PDF über pypdf (läuft auch unter Windows), Text direkt."""
    if pfad.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        leser = PdfReader(str(pfad))
        return [(i + 1, (s.extract_text() or "").splitlines()) for i, s in enumerate(leser.pages)]
    return [(None, pfad.read_text(encoding="utf-8", errors="replace").splitlines())]


_RAUSCHEN = [re.compile(m) for m in KONFIG["rauschen"]]


def saeubere_zeile(zeile: str) -> str | None:
    """Ersetzt geschützte Leerzeichen, entfernt Kopf-/Fußzeilen (Rauschen). None = weglassen,
    '' = Absatzende."""
    z = zeile.replace(" ", " ").replace("‑", "-").rstrip()
    s = z.strip()
    if not s:
        return ""
    if any(m.search(s) for m in _RAUSCHEN):
        return None
    return s


def verbinde(zeilen: Iterable[str]) -> str:
    """Zeilen zu Fließtext; Silbentrennung am Zeilenende ('heranzu -' + 'ziehen') aufheben."""
    text = ""
    for z in zeilen:
        if not z:
            continue
        if text.endswith("-") and z[:1].islower() and len(text) > 1 and text[-2].isalpha():
            text = text[:-1] + z
        elif text.endswith(" -") and z[:1].islower():
            text = text[:-2] + z
        else:
            text = f"{text} {z}" if text else z
    return re.sub(r"\s+", " ", text).strip()


_ABK = sorted(KONFIG["abkuerzungen_ohne_satzende"], key=len, reverse=True)
_SATZGRENZE = re.compile(r"[.!?][\"“”')]?\s+(?=[A-ZÄÖÜ„(§\d])")


def saetze(text: str) -> list[str]:
    """Teilt Fließtext an Satzenden. Kein Satzende nach Abkürzungen ('Abs.', 'z. B.'),
    einzelnen Buchstaben oder Zahlen ('Nr. 3', '1. Januar')."""
    teile, start = [], 0
    for m in _SATZGRENZE.finditer(text):
        davor = text[start:m.start() + 1]
        wort = re.search(r"(\S+)\.$", davor.rstrip("\"“”')"))
        if wort:
            w = wort.group(1)
            if (len(w) <= 1 or w.isdigit() or re.fullmatch(r"[\divxIVX]+", w)
                    or any(davor.endswith(a + ".") for a in _ABK)):
                continue
        teile.append(text[start:m.end()].strip())
        start = m.end()
    rest = text[start:].strip()
    if rest:
        teile.append(rest)
    return teile


def _ohne_riesensaetze(liste: list[str], grenze: int) -> list[str]:
    """Ein 'Satz' über dem Dreifachen der Stückgröße ist kein Satz, sondern eine Tabelle oder
    Liste ohne Satzzeichen (z. B. in Änderungsgesetzen, EStG, HGB). Nur dann wird an Wortgrenzen
    geteilt -- sonst würde ein Stück die Eingabegrenze der Embeddings sprengen."""
    erg: list[str] = []
    for satz in liste:
        if len(satz) <= 3 * grenze:
            erg.append(satz)
            continue
        aktuell = ""
        for wort in satz.split(" "):
            if aktuell and len(aktuell) + 1 + len(wort) > grenze:
                erg.append(aktuell)
                aktuell = wort
            else:
                aktuell = f"{aktuell} {wort}" if aktuell else wort
        if aktuell:
            erg.append(aktuell)
    return erg


def packe(text: str, max_zeichen: int | None = None) -> list[str]:
    """Teilt einen langen Text an Satzgrenzen in Teile <= max_zeichen (ein einzelner zu langer
    Satz bleibt ganz -- nie mitten im Satz trennen)."""
    grenze = max_zeichen or int(KONFIG["stueck_max_zeichen"])
    if len(text) <= grenze:
        return [text] if text else []
    teile, aktuell = [], ""
    for satz in _ohne_riesensaetze(saetze(text), grenze):
        if aktuell and len(aktuell) + 1 + len(satz) > grenze:
            teile.append(aktuell)
            aktuell = satz
        else:
            aktuell = f"{aktuell} {satz}" if aktuell else satz
    if aktuell:
        teile.append(aktuell)
    return teile


def _ist_menue(block: list[str]) -> bool:
    """Navigationsmenü einer Webseite: viele kurze Zeilen ohne Satzzeichen."""
    kurze = [z for z in block if len(z) <= 45 and not re.search(r"[.:;?!]$", z)]
    return len(block) >= 5 and len(kurze) >= 0.8 * len(block)


# --------------------------------------------------------------------------- Zerlegen

def _zeilen_mit_seite(seiten) -> list[tuple[int | None, str]]:
    erg = []
    for seite, zeilen in seiten:
        for roh in zeilen:
            z = saeubere_zeile(roh)
            if z is not None:
                erg.append((seite, z))
        erg.append((seite, ""))
    return erg


def zerlege_gesetz(seiten, kurz: str) -> list[tuple[str, str, int | None]]:
    """[(Fundstelle, Text, Seite)] nach Paragraf/Artikel und Absatz."""
    kopf = re.compile(KONFIG["paragraf_kopf"])
    artikel = re.compile(r"^Artikel\s+(\d+[a-z]?)\b")
    absatz = re.compile(KONFIG["absatz_kopf"])
    zeilen = _zeilen_mit_seite(seiten)
    hat_artikel = sum(1 for _, z in zeilen if artikel.match(z) and len(z) < 60) >= 2
    einheiten: list[dict] = []
    aktuell: dict | None = None
    art_nr = None
    for seite, z in zeilen:
        if hat_artikel:
            m = artikel.match(z)
            if m and len(z) < 60:
                art_nr = m.group(1)
                aktuell = {"name": f"Art. {art_nr}", "seite": seite, "absaetze": [[None, []]]}
                einheiten.append(aktuell)
                continue
        m = kopf.match(z)
        if m and len(z) <= int(KONFIG["abschnitt_kopf_max_zeichen"]) and not z.rstrip().endswith((",", ";")):
            zeichen = KONFIG["paragraf_zeichen"]  # Darstellung der Fundstelle, kein Rechtswert
            name = f"{zeichen} {m.group(1)}" if not art_nr else f"Art. {art_nr} {zeichen} {m.group(1)}"
            aktuell = {"name": name, "seite": seite, "absaetze": [[None, []]]}
            einheiten.append(aktuell)
            rest = z[m.end():].strip()
            if rest:
                aktuell["titel"] = rest
            continue
        if aktuell is None:
            continue
        ma = absatz.match(z)
        if ma:
            aktuell["absaetze"].append([ma.group(1), [z], seite])
        else:
            aktuell["absaetze"][-1][1].append(z)
            if len(aktuell["absaetze"][-1]) == 2:
                aktuell["absaetze"][-1].append(seite)
    # Inhaltsverzeichnis-Einträge (gleicher Paragraf ohne Text) gegen den vollen Text tauschen
    beste: dict[str, dict] = {}
    for e in einheiten:
        laenge = sum(len(" ".join(a[1])) for a in e["absaetze"])
        e["_laenge"] = laenge
        if e["name"] not in beste or laenge > beste[e["name"]]["_laenge"]:
            beste[e["name"]] = e
    erg = []
    for e in einheiten:
        if beste.get(e["name"]) is not e:
            continue
        for nr, teile, *s in e["absaetze"]:
            text = verbinde(teile)
            if not text or (nr is None and len(text) < 3):
                continue
            fund = f"{kurz} {e['name']}" + (f" Abs. {nr}" if nr else "")
            for stueck in packe(text):
                erg.append((fund, stueck, s[0] if s else e["seite"]))
    return erg


def zerlege_urteil(seiten, kurz: str) -> list[tuple[str, str, int | None]]:
    """Kopf/Leitsatz, dann Randnummern (einzelne Zahl in eigener Zeile oder '[ 7 ]'),
    nur wenn fortlaufend (1, 2, 3 ...). Ohne Randnummern: nach Absätzen mit Seite."""
    zeilen = _zeilen_mit_seite(seiten)
    rn_zeile = re.compile(KONFIG["randnummer_zeile"])
    rn_klammer = re.compile(KONFIG["randnummer_klammer"])
    # Fall 1: Randnummern als eigene Zeilen
    gruppen: list[tuple[int | None, int | None, list[str]]] = [(None, None, [])]
    erwartet = 1
    for seite, z in zeilen:
        m = rn_zeile.match(z)
        if m and int(m.group(1)) == erwartet:
            gruppen.append((erwartet, seite, []))
            erwartet += 1
            continue
        gruppen[-1][2].append(z)
    if erwartet <= 3:
        # Fall 2: '[ n ]' im Fließtext (lexetius)
        voll = verbinde(z for _, z in zeilen)
        stellen, erwartet = [], 1
        for m in rn_klammer.finditer(voll):
            if int(m.group(1)) == erwartet:
                stellen.append((erwartet, m.start(), m.end()))
                erwartet += 1
        if erwartet > 3:
            gruppen = [(None, None, [voll[: stellen[0][1]]])]
            for i, (nr, a, e) in enumerate(stellen):
                ende = stellen[i + 1][1] if i + 1 < len(stellen) else len(voll)
                gruppen.append((nr, None, [voll[e:ende]]))
        else:
            return zerlege_abschnitte(seiten, kurz)
    erg = []
    kopf_text = verbinde(_ohne_menue(gruppen[0][2]))
    if kopf_text:
        leitsatz = re.search(KONFIG["urteil_leitsatz"], kopf_text, re.MULTILINE) or ("Leitsatz" in kopf_text)
        for stueck in packe(kopf_text):
            erg.append((f"{kurz}, Leitsatz" if leitsatz else kurz, stueck, None))
    # Randnummern zu Teilen bis zur Höchstlänge bündeln
    grenze = int(KONFIG["stueck_max_zeichen"])
    puffer: list[tuple[int, str, int | None]] = []

    def leeren():
        if not puffer:
            return
        von, bis = puffer[0][0], puffer[-1][0]
        rn = f"Rn. {von}" if von == bis else f"Rn. {von}–{bis}"
        text = " ".join(t for _, t, _ in puffer)
        for stueck in packe(text):
            erg.append((f"{kurz}, {rn}", stueck, puffer[0][2]))
        puffer.clear()

    for nr, seite, teile in gruppen[1:]:
        text = verbinde(teile)
        if not text:
            continue
        if puffer and sum(len(t) for _, t, _ in puffer) + len(text) > grenze:
            leeren()
        puffer.append((nr, text, seite))
    leeren()
    return erg


def _ohne_menue(zeilen: list[str]) -> list[str]:
    bloecke, aktuell = [], []
    for z in zeilen:
        if not z:
            if aktuell:
                bloecke.append(aktuell)
            aktuell = []
        else:
            aktuell.append(z)
    if aktuell:
        bloecke.append(aktuell)
    erg: list[str] = []
    for b in bloecke:
        # in Blöcken ohne Leerzeilen das Menü zeilenweise abschneiden
        laeufe, lauf = [], []
        for z in b:
            if len(z) <= 45 and not re.search(r"[.:;?!]$", z):
                lauf.append(z)
            else:
                if len(lauf) >= 5:
                    laeufe.append(set(lauf))
                lauf = []
        if len(lauf) >= 5:
            laeufe.append(set(lauf))
        menue = set().union(*laeufe) if laeufe else set()
        if not _ist_menue(b):
            erg.extend(z for z in b if z not in menue)
        erg.append("")
    return erg


def zerlege_abschnitte(seiten, kurz: str) -> list[tuple[str, str, int | None]]:
    """Nach nummerierten Überschriften ('1.', '2.1', 'II.', 'a)'); Fundstelle mit Abschnitt und
    Seite. Ein Abschnittswechsel beendet immer ein Stück."""
    koepfe = [re.compile(m) for m in KONFIG["abschnitt_kopf"]]
    bezeichnung = KONFIG.get("abschnitt_bezeichnung", {}).get(kurz, "Abschn.")
    maxlen = int(KONFIG["abschnitt_kopf_max_zeichen"])
    zeilen = _zeilen_mit_seite(seiten)
    abschnitt: str | None = None
    haupt: str | None = None
    teile: list[tuple[str | None, int | None, list[str]]] = [(None, zeilen[0][0] if zeilen else None, [])]
    for seite, z in zeilen:
        neu = None
        # Überschrift: kurz und ohne Komma -- sonst ist es eine nummerierte Aufzählung im Text
        if z and len(z) <= maxlen and "," not in z:
            for k in koepfe:
                m = k.match(z)
                if m:
                    neu = m.group(1)
                    break
        if neu:
            if re.fullmatch(r"[a-z]", neu) and haupt:
                abschnitt = f"{haupt}{neu}"
            else:
                haupt = abschnitt = neu
            teile.append((abschnitt, seite, [z]))
        else:
            teile[-1][2].append(z)
    erg = []
    for abschn, seite, zz in teile:
        text = verbinde(_ohne_menue(zz))
        if not text:
            continue
        fund = kurz
        if abschn:
            fund += f", {bezeichnung} {abschn}"
        for stueck in packe(text):
            erg.append((fund + (f", S. {seite}" if seite else ""), stueck, seite))
    return erg


def zerlege_datei(pfad: Path, kurz: str, zerlegung: str) -> list[tuple[str, str, int | None]]:
    seiten = lies_seiten(pfad)
    if zerlegung == "paragraf":
        erg = zerlege_gesetz(seiten, kurz)
        return erg or zerlege_abschnitte(seiten, kurz)
    if zerlegung == "randnummer":
        return zerlege_urteil(seiten, kurz)
    return zerlege_abschnitte(seiten, kurz)
