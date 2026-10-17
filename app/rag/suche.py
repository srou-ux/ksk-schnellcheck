"""Quellenabruf (RAG, Auftrag Teil 2, Punkt 3 und 4).

    suche(frage, jahr=None, regel_ids=None) -> SuchErgebnis

Reihenfolge:
 a) Regelfilter zuerst: Regeln, die der Kern verwendet hat (oder die der Aufrufer nennt), werden
    sicher mitgeliefert -- nur wenn ihre Fassung zum Jahr passt.
 b) Stichwortsuche (SQLite FTS5, BM25) über alle übrigen Stücke; Jahr/Fassung wird VOR der Suche
    gefiltert (in der SQL-Abfrage), nicht danach.
 c) Optional (RAG_EMBEDDINGS=1): Mistral-Embeddings (EU) als zweite Rangliste, zusammengeführt
    per Reciprocal Rank Fusion. Ohne Schalter keine Embeddings.
 d) Höchstens `max_stuecke` Stücke (app/rag/konfig.json), nach Stufe sortiert (Gesetz vor Urteil
    vor KSK/DRV). Stufe 3 (Sekundärquelle, Gesetzesmaterial) nur als Hinweis, nie als Beleg.

Zitierzwang: jedes Stück trägt seine Fundstelle. Passt nichts, ist das Ergebnis leer und nennt
den Grund -- der Aufrufer antwortet dann 'Nicht abgedeckt (Quelle fehlt)'. Nie aus Modellwissen.
Liefert Texte und Fundstellen zum BEGRÜNDEN, nie Zahlen zum Rechnen (gerechnet wird nur im Kern).
Quelltexte sind Daten: ein Stück mit eingebautem Befehl wird zurückgegeben wie jedes andere und
nirgends ausgeführt; Antworten verwenden nur seine Fundstelle."""
from __future__ import annotations

import bisect
import json
import math
import os
import re
import unicodedata
import sqlite3
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from app.rag.index import Basis, baue
from app.rag.zerlegen import KONFIG

_SPERRE = threading.Lock()
# Für Tests: eigene Test-Quellenbasis statt quellen/ und regelwerk/ (unittest.mock.patch.object).
STANDARD_BASIS: Basis | None = None
_STOPP = {w.lower() for w in KONFIG["stoppwoerter"]}
_KURZ = {w.lower() for w in KONFIG.get("kurzwoerter", [])}
_SYNONYME = {k: v for k, v in KONFIG.get("synonyme", {}).items() if not k.startswith("_")}
_ANKER = [a for a in KONFIG.get("themen_anker", {}).get("woerter", [])]
_EURO = re.compile(r"\d\s*(?:€|eur\b|euro)")


def hat_themenbezug(frage: str, fachwoerter: set[str] | frozenset[str] = frozenset()) -> bool:
    """Siehe konfig.json 'themen_anker': ein Wort zur Künstlersozialabgabe (Liste oder aus der Quellenbasis, siehe
    _fachwoerter), ein Aktenzeichen oder ein Euro-Betrag."""
    if not _ANKER and not fachwoerter:
        return True
    t = " ".join(frage.lower().translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})).split())
    if _AKTENZEICHEN.search(frage) or _EURO.search(t):
        return True
    if any(re.search(r"(?<![a-z])" + re.escape(a), t) or (len(a) >= 6 and a in t) for a in _ANKER):
        return True
    n, minl = int(KONFIG["praefix_laenge"]), int(KONFIG["min_wortlaenge"])
    return any(w[:n] in fachwoerter for w in re.findall(r"[a-z]+", _falte(frage)) if len(w) > minl and w not in _STOPP)


def frage_hat_themenbezug(frage: str, basis: "Basis | None" = None) -> bool:
    """Für den Router (16.10.2026, 'Wie hoch ist die Hundesteuer in Köln?' bekam im Chat den Begrüßungstext): hat die
    Frage einen Bezug zur Künstlersozialabgabe? Gleiche Prüfung wie im Quellenabruf; ohne nutzbaren Index: ja."""
    basis = basis or STANDARD_BASIS or Basis()
    try:
        db = _db(basis)
    except Exception:  # noqa: BLE001 -- ohne Index keine Aussage, nie eine Ablehnung deswegen
        return True
    try:
        fach = _fachwoerter(db, f"{basis.index}:{basis.index.stat().st_mtime_ns}")
    finally:
        db.close()
    return fach is None or hat_themenbezug(frage, fach)


_FACHWOERTER: dict[str, Any] = {}


def _fachwoerter(db: sqlite3.Connection, schluessel: str) -> frozenset[str] | None:
    """Wörter (Präfixe), die in den Quellen zur Künstlersozialabgabe (KSVG, Verordnungen, Urteile, KSK, Regelkatalog)
    deutlich häufiger sind als in den allgemeinen Gesetzen (HGB, EStG, SGB, SGG; konfig.json 'themen_anker'):
    Fachwörter, die die Liste nicht nennt ('Ehrenamtspauschale', 'Ausgleichsvereinigung'). Einmal je Indexstand.
    None: die Quellenbasis enthält keine allgemeinen Gesetze -- dann gibt es keinen Themenfilter."""
    global _FACHWOERTER
    stand = _FACHWOERTER
    if stand.get("schluessel") == schluessel:
        return stand["woerter"]
    cfg = KONFIG.get("themen_anker", {})
    allgemein = tuple(cfg.get("allgemeine_quellen", []))
    ohne = tuple(cfg.get("nicht_zaehlen", []))
    faktor, mindest = float(cfg.get("fach_faktor", 0) or 0), int(cfg.get("fach_mindest", 0) or 0)
    n, minl = int(KONFIG["praefix_laenge"]), int(KONFIG["min_wortlaenge"])
    fach: dict[str, int] = {}
    allg: dict[str, int] = {}
    nf = na = 0
    if faktor and allgemein:
        for r in db.execute("SELECT datei, art, text FROM stuecke WHERE status = 'aktiv'"):
            if r["art"] == "Material" or r["datei"].startswith(ohne):
                continue
            ziel = allg if r["datei"].startswith(allgemein) else fach
            for w in {w[:n] for w in re.findall(r"[a-z]+", _falte(r["text"])) if len(w) > minl}:
                ziel[w] = ziel.get(w, 0) + 1
            if ziel is allg:
                na += 1
            else:
                nf += 1
    # Ohne allgemeine Gesetze in der Quellenbasis (z. B. eine Test-Quellenbasis) lässt sich nichts abgrenzen: kein Filter.
    woerter = None if not (nf and na) else frozenset(
        w for w, d in fach.items() if d >= mindest and (d / nf) >= faktor * ((allg.get(w, 0) + 0.5) / na))
    _FACHWOERTER = {"schluessel": schluessel, "woerter": woerter}
    return woerter


@dataclass
class Treffer:
    id: int
    datei: str
    quelle_id: str
    art: str
    stufe: int
    fundstelle: str
    text: str
    gilt_von: int | None
    gilt_bis: int | None
    fassung: str
    regel_ids: list[str]
    status: str
    rang: int = 0          # Platz in der Relevanzliste (1 = bester), 0 = über den Regelfilter
    quelle_geaendert: bool = False

    @property
    def nur_hinweis(self) -> bool:
        return self.stufe >= int(KONFIG["hinweis_ab_stufe"])

    @property
    def typ(self) -> str:
        """Ebene für die Antwort: gesetz / urteil / verwaltungspraxis / hinweis."""
        if self.nur_hinweis:
            return "hinweis"
        if self.art in ("Regel", "Register"):
            return "verwaltungspraxis" if self.stufe == 2 else "gesetz"
        return KONFIG["art_typ"].get(self.art, "hinweis")


@dataclass
class SuchErgebnis:
    stuecke: list[Treffer] = field(default_factory=list)   # geliefert, nach Stufe sortiert
    relevanz: list[Treffer] = field(default_factory=list)  # Stichwort-/Vektorliste (für die Abruf-Güte)
    grund: str | None = None                               # gesetzt, wenn leer
    hinweise: list[str] = field(default_factory=list)
    belegstellen: list[Treffer] = field(default_factory=list)  # Quelltext-Stellen der Regeln (Regelfilter)
    unbekannte_woerter: list[str] = field(default_factory=list)  # Wörter der Frage, die in keiner Quelle vorkommen

    @property
    def leer(self) -> bool:
        return not self.stuecke

    def fundstellen(self) -> list[str]:
        return [s.fundstelle for s in self.stuecke]

    def belege(self) -> list[Treffer]:
        return [s for s in self.stuecke if not s.nur_hinweis]


def _db(basis: Basis) -> sqlite3.Connection:
    """Öffnet den Index; fehlt er, wird er einmal gebaut (lokale Dateien, kein Netz)."""
    with _SPERRE:
        if not basis.index.exists():
            baue(basis, ausgabe=lambda *_: None)
    db = sqlite3.connect(str(basis.index))
    db.row_factory = sqlite3.Row
    return db


_AKTENZEICHEN = re.compile(r"\b[A-Z]\s?\d+\s?[A-Z]{1,3}\s?\d+/\d+(?:\s?R)?\b")
_PARAGRAF = re.compile(r"§\s?(\d+[a-z]?)(?:\s*Abs\.?\s*(\d+))?")


_VOKABULAR: dict[str, Any] = {}


def _vokabular(db: sqlite3.Connection, schluessel: str) -> dict[str, Any]:
    """Wörter des Index mit Dokumenthäufigkeit (FTS5-Vokabular), einmal je Indexstand geladen.
    Der Zwischenspeicher wird in EINEM Schritt ersetzt (gleichzeitige Abrufe sehen nie einen
    halb gefüllten Stand)."""
    global _VOKABULAR
    stand = _VOKABULAR
    if stand.get("schluessel") != schluessel:
        db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS temp.vokabel USING fts5vocab(main, 'fts', 'row')")
        df = {r[0]: r[1] for r in db.execute("SELECT term, doc FROM temp.vokabel")}
        stand = {"schluessel": schluessel, "df": df, "woerter": set(df), "sortiert": sorted(df),
                 "n": db.execute("SELECT count(*) FROM stuecke").fetchone()[0]}
        _VOKABULAR = stand
    return stand


def zerlege_kompositum(wort: str, vokabular: set[str]) -> list[str]:
    """Deutsche Zusammensetzungen: das längste bekannte Grundwort am Wortende
    ('sprechtheater' -> 'theater', 'gastschauspielern' -> 'schauspieler'). Nur Wörter, die im
    Index vorkommen; Endungen bis zu drei Buchstaben werden zugelassen."""
    minl = int(KONFIG.get("kompositum_min", 5))
    for ende_weg in range(0, 4):
        stamm = wort[: len(wort) - ende_weg] if ende_weg else wort
        for start in range(3, len(stamm) - minl + 1):
            if stamm[start:] in vokabular:
                return [stamm[start:]]
    return []


def _falte(t: str) -> str:
    """Wie der FTS5-Tokenizer (unicode61, remove_diacritics): klein, ohne Akzente/Umlautpunkte."""
    return "".join(c for c in unicodedata.normalize("NFKD", t.lower()) if not unicodedata.combining(c))


@dataclass
class Begriff:
    """Ein Begriff der Frage: eine oder mehrere FTS5-Formen (Wort, Grundwort, Wortgruppe)."""
    anzeige: str
    formen: list[tuple[str, str, bool]]  # (fts-Ausdruck, Text, Präfix?)
    gewicht: float = 1.0
    df: int = 0  # in wie vielen Stücken der Begriff (in einer seiner Formen) vorkommt

    def kommt_vor(self, text_gefaltet: str) -> bool:
        for _, t, praefix in self.formen:
            muster = r"(?<![a-z0-9])" + r"\W+".join(re.escape(_falte(w)) for w in t.split())
            if not praefix:
                muster += r"(?![a-z0-9])"
            if re.search(muster, text_gefaltet):
                return True
        return False


def _synonym_formen(w: str, gesehen: set[str], n: int) -> list[tuple[str, str, bool]]:
    """Zusätzliche Suchwörter aus konfig.json 'synonyme'. Ein Schlüssel gilt für das gleiche Wort und, ab fünf Buchstaben,
    für Wörter, die so beginnen ('radio' -> 'Radiosender'; 'satz' nur für 'Satz', nicht für 'Satzung')."""
    f = _falte(w)
    formen = []
    for schluessel, woerter in _SYNONYME.items():
        if f == schluessel or (len(schluessel) >= 5 and f.startswith(schluessel)):
            for s in woerter:
                rest = KONFIG.get("praefix_rest")
                lang = max(n, len(s) - int(rest)) if rest is not None and len(s) >= int(KONFIG.get("praefix_lang_ab", 0) or 0) else n
                if s[:lang] not in gesehen:
                    gesehen.add(s[:lang])
                    formen.append((f'"{s[:lang]}"*', s[:lang], True) if len(s) > n else (f'"{s}"', s, False))
    return formen


def begriffe(frage: str, vok: dict[str, Any] | None = None,
             df_wortgruppe: Callable[[str], int] | None = None) -> list[Begriff]:
    """Begriffe der Frage: Wörter ohne Stoppwörter als Präfix (ersetzt das fehlende deutsche
    Stemming) samt Grundwort zusammengesetzter Wörter; Aktenzeichen, Paragrafen und Regel-IDs als
    Wortgruppe. Gewicht = Seltenheit im Index (IDF): seltene Begriffe zählen mehr."""
    vok = vok or {"df": {}, "woerter": set(), "sortiert": [], "n": 1}
    erg: list[Begriff] = []
    for az in _AKTENZEICHEN.findall(frage):
        t = " ".join(re.findall(r"\w+", az)).lower()
        erg.append(Begriff(az, [(f'"{t}"', t, False)]))
    for m in _PARAGRAF.finditer(frage):
        t = f"{m.group(1)} abs {m.group(2)}" if m.group(2) else m.group(1)
        erg.append(Begriff(m.group(0), [(f'"{t}"', t, False)]))
    for r in re.findall(r"\bR-\d+\b", frage):
        erg.append(Begriff(r, [(f'"{r.lower()}"', r.lower(), False)]))
    n, minl = int(KONFIG["praefix_laenge"]), int(KONFIG["min_wortlaenge"])
    gesehen: set[str] = set()
    for w in re.findall(r"[A-Za-zÄÖÜäöüß]+", frage):
        w = w.lower()
        # Kurze Fachabkürzungen (KG, GbR, OHG, UG, AG, USt …) entscheiden oft den Fall: trotz
        # Mindestlänge als ganzes Wort suchen (Liste: konfig.json 'kurzwoerter').
        if w in _KURZ and w not in gesehen:
            gesehen.add(w)
            erg.append(Begriff(w, [(f'"{w}"', w, False), *_synonym_formen(w, gesehen, n)]))
            continue
        if len(w) < minl or w in _STOPP or w[:n] in gesehen:
            continue
        gesehen.add(w[:n])
        # RAG-Güte 16.10.2026: das Präfix aus 7 Buchstaben machte 'Verwertungsgesellschaft' zu 'verwert*' (= auch der
        # häufige 'Verwerter'); ein seltenes Fachwort verlor so sein Gewicht. Mit 'praefix_rest' bleibt das Wort bis auf
        # höchstens so viele Endbuchstaben erhalten (mindestens 'praefix_laenge' Buchstaben).
        rest = KONFIG.get("praefix_rest")
        ab = int(KONFIG.get("praefix_lang_ab", 0) or 0)
        lang = max(n, len(w) - int(rest)) if rest is not None and len(w) >= ab else n
        formen = [(f'"{w[:lang]}"*', w[:lang], True) if len(w) > n else (f'"{w}"', w, False)]
        for grund in zerlege_kompositum(_falte(w), vok["woerter"]):
            if grund not in _STOPP and grund[:n] not in gesehen:
                gesehen.add(grund[:n])
                formen.append((f'"{grund[:n]}"*', grund[:n], True) if len(grund) > n else (f'"{grund}"', grund, False))
        formen += _synonym_formen(w, gesehen, n)
        erg.append(Begriff(w, formen))
    gesamt = max(int(vok["n"]), 1)
    for b in erg:
        werte = []
        for fts, t, p in b.formen:
            if " " in t:  # Wortgruppe (Aktenzeichen, Paragraf): über die Volltextsuche zählen
                werte.append(df_wortgruppe(fts) if df_wortgruppe else 1)
            else:
                werte.append(_df(vok, t, p))
        b.df = max(werte, default=0)
        b.gewicht = math.log((gesamt + 1) / (b.df + 0.5))
    return erg


def _df(vok: dict[str, Any], text: str, praefix: bool) -> int:
    t = _falte(text)
    if " " in t:
        return 0
    if not praefix:
        return int(vok["df"].get(t, 0))
    sortiert = vok["sortiert"]
    i = bisect.bisect_left(sortiert, t)
    summe = 0
    while i < len(sortiert) and sortiert[i].startswith(t):
        summe += vok["df"][sortiert[i]]
        i += 1
    return summe


def anfrage(frage: str, vok: dict[str, Any] | None = None) -> str:
    """FTS5-Abfrage aus den Begriffen der Frage (ODER-verknüpft). Alles in Anführungszeichen --
    Sonderzeichen der Frage können die Abfrage nicht verändern."""
    return " OR ".join(f for b in begriffe(frage, vok) for f, _, _ in b.formen)


def abdeckung(stueck_text: str, liste: list[Begriff]) -> float:
    """Anteil der (nach Seltenheit gewichteten) Begriffe der Frage, die ein Stück enthält."""
    gesamt = sum(b.gewicht for b in liste)
    if not gesamt:
        return 0.0
    t = _falte(stueck_text)
    return sum(b.gewicht for b in liste if b.kommt_vor(t)) / gesamt


def _jahr_filter(jahr: int | None) -> tuple[str, list[Any]]:
    if jahr is None:
        return "", []
    return " AND (s.gilt_von IS NULL OR s.gilt_von <= ?) AND (s.gilt_bis IS NULL OR s.gilt_bis >= ?)", [jahr, jahr]


def _zeile(r: sqlite3.Row, rang: int, pruefen: set[str]) -> Treffer:
    ids = [i for i in (r["regel_ids"] or "").split(";") if i]
    return Treffer(id=r["id"], datei=r["datei"], quelle_id=r["quelle_id"], art=r["art"], stufe=r["stufe"],
                   fundstelle=r["fundstelle"], text=r["text"], gilt_von=r["gilt_von"], gilt_bis=r["gilt_bis"],
                   fassung=r["fassung"] or "", regel_ids=ids, status=r["status"], rang=rang,
                   quelle_geaendert=bool(set(ids) & pruefen))


def _fassung_fuer_jahr(jahr: int, basis: Basis) -> str | None:
    return basis.fassungen().get(jahr)


def suche(frage: str, jahr: int | None = None, regel_ids: list[str] | None = None, *,
          basis: Basis | None = None, max_stuecke: int | None = None,
          einbetter: Callable[[list[str]], list[list[float]]] | None = None) -> SuchErgebnis:
    basis = basis or STANDARD_BASIS or Basis()
    grenze = int(max_stuecke or KONFIG["max_stuecke"])
    if jahr is not None and _fassung_fuer_jahr(jahr, basis) is None:
        return SuchErgebnis(grund=f"Nicht abgedeckt: Für das Jahr {jahr} enthält das Regelwerk keine Daten (keine "
                                  f"Fassung im Register); keine Annäherung mit einem anderen Jahr.")
    db = _db(basis)
    try:
        status = {r["regel_id"]: r["grund"] for r in db.execute("SELECT regel_id, grund FROM regel_status")}
        entfernt = {rid for rid, g in status.items() if "entfernt" in (g or "")}
        pruefen = set(status)
        filt, args = _jahr_filter(jahr)
        basis_where = "s.status = 'aktiv'" + filt

        # a) Regelfilter: die Regel selbst und die Quelltext-Stellen, die ihre Fundstelle nennt
        fest: list[Treffer] = []
        belegstellen: list[Treffer] = []
        for rid in regel_ids or []:
            if rid in entfernt:
                continue
            for r in db.execute(f"SELECT s.* FROM stuecke s WHERE {basis_where} AND s.art='Regel' "
                                "AND (';'||s.regel_ids||';') LIKE ?", [*args, f"%;{rid};%"]):
                fest.append(_zeile(r, 0, pruefen))
            for r in db.execute(f"SELECT s.* FROM stuecke s WHERE {basis_where} AND s.art NOT IN ('Regel','Register') "
                                "AND (';'||s.regel_ids||';') LIKE ? ORDER BY s.stufe, s.id", [*args, f"%;{rid};%"]):
                t = _zeile(r, 0, pruefen)
                if not t.nur_hinweis:
                    belegstellen.append(t)

        # b) Stichwortsuche
        # Zwei Ranglisten: Regelkatalog (geprüfte Regeln mit Fundstelle) und Quelltexte. Sie werden
        # per Reciprocal Rank Fusion gemischt -- sonst verdrängen lange Gesetzestexte die kurzen Regeln.
        vok = _vokabular(db, f"{basis.index}:{basis.index.stat().st_mtime_ns}")
        def df_wortgruppe(fts: str) -> int:
            return db.execute("SELECT count(*) FROM fts WHERE fts MATCH ?", (fts,)).fetchone()[0]

        liste_begriffe = begriffe(frage, vok, df_wortgruppe)
        fachwoerter = _fachwoerter(db, f"{basis.index}:{basis.index.stat().st_mtime_ns}") if not regel_ids else None
        abfrage = " OR ".join(f for b in liste_begriffe for f, _, _ in b.formen)
        relevanz: list[Treffer] = []
        if abfrage:
            listen = []
            gewichte = KONFIG["rrf_gewichte"]
            # Fragt der Nutzer nach Rechtsprechung (Aktenzeichen, 'Urteil', 'BSG' …; konfig.json 'urteile_voll_wenn'),
            # zählen die Urteile voll -- sonst mit dem kleineren Gewicht 'rrf_gewichte.urteile'.
            if "urteile" in gewichte and (_AKTENZEICHEN.search(frage) or any(
                    re.search(r"(?<![a-zäöüß])" + re.escape(w), frage.lower()) for w in KONFIG.get("urteile_voll_wenn", []))):
                gewichte = {**gewichte, "urteile": gewichte.get("quellen", 1.0)}
            regel = ("Regel", "Register")
            if KONFIG.get("quellen_nach_stufe_trennen"):
                # Gesetz/Verordnung/Urteil (Stufe 1) und KSK/DRV-Auslegung (Stufe 2) als eigene Ranglisten:
                # die beste Gesetzesstelle steht oben, auch wenn eine KSK-Info mehr passende Wörter hat.
                teile = (("s.art IN ('Regel','Register')", gewichte["regeln"], lambda r: r["art"] in regel),
                         *((("s.art NOT IN ('Regel','Register','Urteil') AND s.nachrangig = 0 AND s.stufe = 1",
                             gewichte["quellen"],
                             lambda r: r["art"] not in (*regel, "Urteil") and not r["nachrangig"] and r["stufe"] == 1),
                            ("s.art = 'Urteil' AND s.nachrangig = 0", gewichte["urteile"],
                             lambda r: r["art"] == "Urteil" and not r["nachrangig"]))
                           if "urteile" in gewichte else
                           (("s.art NOT IN ('Regel','Register') AND s.nachrangig = 0 AND s.stufe = 1",
                             gewichte["quellen"],
                             lambda r: r["art"] not in regel and not r["nachrangig"] and r["stufe"] == 1),)),
                         ("s.art NOT IN ('Regel','Register'" + (",'Urteil'" if "urteile" in gewichte else "")
                          + ") AND s.nachrangig = 0 AND s.stufe > 1", gewichte["quellen"],
                          lambda r: r["art"] not in regel and not r["nachrangig"] and r["stufe"] > 1
                          and not ("urteile" in gewichte and r["art"] == "Urteil")),
                         ("s.art NOT IN ('Regel','Register') AND s.nachrangig = 1", gewichte["nachrangig"],
                          lambda r: r["art"] not in regel and r["nachrangig"]))
            else:
                teile = (("s.art IN ('Regel','Register')", gewichte["regeln"], lambda r: r["art"] in regel),
                         ("s.art NOT IN ('Regel','Register') AND s.nachrangig = 0", gewichte["quellen"],
                          lambda r: r["art"] not in regel and not r["nachrangig"]),
                         ("s.art NOT IN ('Regel','Register') AND s.nachrangig = 1", gewichte["nachrangig"],
                          lambda r: r["art"] not in regel and r["nachrangig"]))
            for teil, _, _ in teile:
                sql = (f"SELECT s.*, bm25(fts, 3.0, 1.0, 1.0, 2.0) AS score FROM fts JOIN stuecke s ON s.id = fts.rowid "
                       f"WHERE fts MATCH ? AND {basis_where} AND {teil} ORDER BY score LIMIT ?")
                liste = []
                for r in db.execute(sql, [abfrage, *args, int(KONFIG["fts_kandidaten"])]):
                    t = _zeile(r, 0, pruefen)
                    if not (set(t.regel_ids) & entfernt and t.art == "Regel"):
                        liste.append(t)
                listen.append(liste)
            gewichte_liste = [g for _, g, _ in teile]
            # RAG-Güte 16.10.2026 ('ohne_aussage', 'versichertenrecht' in konfig.json): Schlussvorschriften ('Diese Verordnung tritt mit Wirkung vom 1. Januar 1991 in Kraft',
            # 'Der Bund trägt die Verwaltungskosten') sind kurz und standen deshalb mit einem einzigen gemeinsamen Wort
            # ('auftritt' -> 'tritt') oben. Stücke, die nur aus so einer Vorschrift bestehen (konfig.json 'ohne_aussage'),
            # rücken ans Ende ihrer Liste -- außer die Frage nennt selbst einen Begriff daraus ('Inkrafttreten').
            for gruppe_name in ("ohne_aussage", "versichertenrecht"):
                gruppe_cfg = KONFIG.get(gruppe_name, {})
                muster = [re.compile(m, re.IGNORECASE) for m in gruppe_cfg.get("muster", [])]
                nicht = [re.compile(m, re.IGNORECASE) for m in gruppe_cfg.get("nicht_wenn", [])]
                ausnahme = [w.lower() for w in gruppe_cfg.get("ausser_frage_nennt", [])]
                if not muster or any(w in frage.lower() for w in ausnahme):
                    continue

                def hinten(t: Treffer) -> bool:
                    return any(m.search(t.text) for m in muster) and not any(m.search(t.text) for m in nicht)

                listen = [[t for t in l if not hinten(t)] + [t for t in l if hinten(t)] for l in listen]

            # c) optional: Embeddings als weitere Rangliste(n), Reciprocal Rank Fusion
            if os.environ.get("RAG_EMBEDDINGS") == "1" or einbetter is not None:
                from app.rag.embeddings import vektor_rangliste

                vektor = vektor_rangliste(db, frage, basis_where, args, einbetter=einbetter)
                w = float(KONFIG.get("rrf_gewicht_vektor", 1.0))
                if vektor and KONFIG.get("vektor_getrennt"):
                    # wie bei der Stichwortsuche: Regelkatalog / Quellen / nachrangige Quellen getrennt
                    for _, g, gehoert in teile:
                        listen.append([_zeile(r, 0, pruefen) for r in vektor if gehoert(r)])
                        gewichte_liste.append(g * w)
                elif vektor:
                    listen.append([_zeile(r, 0, pruefen) for r in vektor])
                    gewichte_liste.append(w)
            # Je Liste und danach: Wiederholungen derselben Stelle rücken nach hinten (_vielfalt).
            relevanz = _vielfalt(rrf([_vielfalt(l) for l in listen], gewichte=gewichte_liste))
        for i, t in enumerate(relevanz, start=1):
            t.rang = i
    finally:
        db.close()

    # d) Auswahl: Regelfilter zuerst, dann nach Relevanz; je Fundstelle nur einmal
    auswahl: list[Treffer] = []
    gesehen: set[str] = set()
    je_quelle: dict[str, int] = {}
    cap = int(KONFIG["max_je_quelle"])
    # Mindestabdeckung: ein Stück muss genug (seltene) Begriffe der Frage enthalten. Enthält die Frage
    # ein Wort, das in KEINER Quelle vorkommt (z. B. 'Podcast'), gilt die höhere Schwelle -- das
    # Thema ist dann wahrscheinlich nicht in der Quellenbasis.
    unbekannt = [b.anzeige for b in liste_begriffe if b.df == 0] if abfrage else []
    schwelle = float(KONFIG["min_abdeckung_bei_unbekanntem_wort" if unbekannt else "min_abdeckung"])
    # RAG-Korpus 15.10.2026 (R2, 0 von 19): ein Aktenzeichen, das in KEINER Quelle steht ('B 3 KS 43/12 R', erfunden oder
    # nicht in der Quellenbasis), lieferte andere Urteile und SGG-Stellen -- als wäre es dieses Verfahren. Dann liefert die
    # Stichwortsuche nichts (der Regelfilter bleibt); die Antwort lautet 'Nicht abgedeckt (Quelle fehlt)'.
    az_fehlt = any(b.df == 0 for b in liste_begriffe if _AKTENZEICHEN.fullmatch(b.anzeige)) if abfrage else False
    themenfremd = bool(abfrage) and not regel_ids and fachwoerter is not None and not hat_themenbezug(frage, fachwoerter)
    passend = [] if az_fehlt or themenfremd else [t for t in relevanz if abdeckung(f"{t.fundstelle} {t.text} {' '.join(t.regel_ids)}", liste_begriffe) >= schwelle] \
        if abfrage else []
    for t in fest + passend:
        schluessel = f"{t.art}|{t.fundstelle}|{';'.join(t.regel_ids) if t.art == 'Regel' else ''}"
        if schluessel in gesehen or (t.rang and je_quelle.get(t.datei, 0) >= cap and t.art != "Regel"):
            continue
        gesehen.add(schluessel)
        je_quelle[t.datei] = je_quelle.get(t.datei, 0) + 1
        auswahl.append(t)
        if len(auswahl) >= grenze:
            break
    rang_art = KONFIG["art_rang"]
    auswahl.sort(key=lambda t: (t.stufe, rang_art.get(t.art, 9), t.rang))
    erg = SuchErgebnis(stuecke=auswahl, relevanz=relevanz, belegstellen=_einmal(belegstellen),
                       unbekannte_woerter=unbekannt)
    if not auswahl:
        # bewusst ohne Wörter der Frage: die Antwort-Prüfung vertraut diesem Text
        erg.grund = ("Keine Quelle in der Quellenbasis deckt die Begriffe der Frage ausreichend ab "
                     "(Nicht abgedeckt, Quelle fehlt).") if abfrage or regel_ids else \
            "Die Frage enthält keine suchbaren Begriffe (Nicht abgedeckt)."
        if themenfremd:
            erg.grund = ("Die Frage betrifft kein Thema der Künstlersozialabgabe, zu dem die Quellenbasis etwas enthält "
                         "(Nicht abgedeckt, Quelle fehlt).")
        if az_fehlt:
            erg.grund = ("Das genannte Aktenzeichen steht in keiner Quelle der Quellenbasis "
                         "(Nicht abgedeckt, Quelle fehlt).")
        if regel_ids and set(regel_ids) <= entfernt:
            erg.grund = "Die Quelle der Regel wurde entfernt; die Regel ist in Prüfung."
    # Hinweis 'Quelle geändert': mit Regelfilter nur für die genannten Regeln (die der Kern verwendet
    # hat), sonst für die gelieferten Stücke
    if regel_ids:
        betroffen = sorted(set(regel_ids) & pruefen)
        erg.hinweise = [f"Quelle geändert, Regel in Prüfung: {', '.join(betroffen)}"] if betroffen else []
    else:
        for t in auswahl:
            if t.quelle_geaendert:
                erg.hinweise.append(f"Quelle geändert, Regel in Prüfung: {', '.join(sorted(set(t.regel_ids) & pruefen))}")
        erg.hinweise = list(dict.fromkeys(erg.hinweise))
    return erg


def _einmal(stellen: list[Treffer]) -> list[Treffer]:
    """Je Fundstelle (ohne Seitenangabe) nur einmal, Reihenfolge bleibt."""
    gesehen, erg = set(), []
    for t in stellen:
        k = re.sub(r", S\. \d+(?:–\d+)?$", "", t.fundstelle)
        if k not in gesehen:
            gesehen.add(k)
            erg.append(t)
    return erg


_STAND = re.compile(r"\s*\((?:Stand|Archiv|Kopie)[^)]*\)|,?\s*S\.\s*\d+(?:\s*[–-]\s*\d+)?|,?\s*Seite\s*[\d–, -]+")


def _vielfalt(liste: list[Treffer]) -> list[Treffer]:
    """RAG-Güte 16.10.2026: unter den ersten Plätzen standen dieselbe Stelle mehrfach -- dieselbe KSK-Info in Stand- und
    Archivfassung ('KSK-Info 21 (Stand 10.2025), Abschn. 5, S. 5' und 'KSK-Info 21, Abschn. 5, S. 4') oder zwei Regeln mit
    derselben Fundstelle. Eine Wiederholung derselben Fundstelle (ohne Stand-/Archivvermerk und Seite) rückt hinter alle
    anderen Treffer; nichts fällt weg, die Reihenfolge sonst bleibt."""
    if not KONFIG.get("vielfalt", True):
        return liste
    erste, spaeter, gesehen = [], [], set()
    for t in liste:
        # Register-Zeilen derselben Regel (R-138 zweimal) zählen als Wiederholung; verschiedene Regeln nie.
        if t.art == "Regel":
            schluessel = "Regel:" + ";".join(t.regel_ids)
        elif t.art == "Register" and t.regel_ids:
            schluessel = "Register:" + ";".join(t.regel_ids)
        else:
            schluessel = _STAND.sub("", t.fundstelle).strip(" ,;")
        if t.art != "Regel" and schluessel in gesehen:
            spaeter.append(t)
        else:
            gesehen.add(schluessel)
            erste.append(t)
    return erste + spaeter


def rrf(listen: list[list[Treffer]], k: int | None = None, gewichte: list[float] | None = None) -> list[Treffer]:
    """Reciprocal Rank Fusion: Punkte = Summe Gewicht/(k + Platz) über alle Ranglisten."""
    k = int(k or KONFIG["rrf_k"])
    gewichte = gewichte or [1.0] * len(listen)
    punkte: dict[int, float] = {}
    objekt: dict[int, Treffer] = {}
    for liste, g in zip(listen, gewichte):
        for platz, t in enumerate(liste, start=1):
            punkte[t.id] = punkte.get(t.id, 0.0) + float(g) / (k + platz)
            objekt.setdefault(t.id, t)
    return [objekt[i] for i in sorted(punkte, key=lambda i: -punkte[i])]


def regel_status(basis: Basis | None = None) -> dict[str, str]:
    basis = basis or Basis()
    db = _db(basis)
    try:
        return {r["regel_id"]: r["grund"] for r in db.execute("SELECT regel_id, grund FROM regel_status")}
    finally:
        db.close()


def als_json(erg: SuchErgebnis) -> str:
    return json.dumps({"grund": erg.grund, "hinweise": erg.hinweise,
                       "stuecke": [{"fundstelle": s.fundstelle, "art": s.art, "stufe": s.stufe, "rang": s.rang,
                                    "regel_ids": s.regel_ids, "text": s.text[:200]} for s in erg.stuecke]},
                      ensure_ascii=False, indent=1)


if __name__ == "__main__":
    import sys

    jahr = int(sys.argv[2]) if len(sys.argv) > 2 else None
    print(als_json(suche(sys.argv[1], jahr)))
