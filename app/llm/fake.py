"""FakeLLM: festes, im Test vorgegebenes Verhalten. Laeuft komplett offline, ohne Schlüssel.

Zwei Betriebsarten:
1. Registrierte Fakten (fuer Tests und Abnahmetests): `FakeLLM.registriere(frage, fakten)`
   legt exakt die Fakten fest, die "ein gutes Modell extrahieren wuerde".
2. Heuristische Notfall-Extraktion (fuer den Demo-Modus ohne Schluessel).

Seit Chatbot Teil 1g (Mischform) schreibt KEIN Modell mehr den Antwort-Koerper
(`formuliere_antwort` gibt es nicht mehr) -- der Koerper besteht ausschliesslich aus festen
Textbausteinen aus dem Regelkatalog (`app/textbausteine.py`, Blatt "Textbausteine").
`beschreibe_fall` liefert hoechstens einen harmlosen, platzhalterbasierten Satz zur
Einzelfall-Beschreibung, nie Zahlen/Normen/Ergebnisse (siehe app/router.py::_ausgeben)."""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from app.baustein import erzeuge_platzhalter
from app.llm.base import AntwortKontext
from app.rechtsform_erkennung import erkenne_rechtsform_auftragnehmer, normalisiere_umlaute
from app.schema import Fakten, Position

SCHLUSSSATZ = "Entwurf – vom Steuerberater zu prüfen."

# Livetest-Befund L1: dieselben drei Werte wie app.pflichtangaben.VERWERTERART_OPTIONEN --
# erkennt die eigene Rueckfrage-Schaltflaeche sowie eine explizite Nutzeraussage, rät aber
# nichts aus einer Branchenbeschreibung ("Werbeagentur") hinein.
_VERWERTERART_MUSTER: list[tuple[str, str]] = [
    (r"eigenwerbung|eigenwerber|eigenwerbend", "eigenwerber"),
    (r"typischer verwerter", "typischer_verwerter"),
    (r"generalklausel", "generalklausel"),
    (r"privatperson \(kein unternehmen\)", "privat"),
]

_LEISTUNGSART_MUSTER: list[tuple[str, str]] = [
    (r"website|webdesign|logo|grafik|design", "Grafik/Design"),
    (r"text|redakt|artikel|lektorat", "Text/Redaktion"),
    (r"musik|konzert|band|komponist", "Musik"),
    (r"foto", "Fotografie"),
    (r"illustr|zeichn", "Illustration"),
]

# Teil 1f, Abschnitt J.3: Begruessung/Smalltalk OHNE jede Sachfrage -- die GANZE
# (getrimmte) Eingabe muss dem Muster entsprechen, sonst bleibt es eine normale Frage
# (z. B. "Hallo, ich habe eine Frage zu 2025" matcht NICHT). Nur fuer den Demo-Modus; das
# echte Modell bekommt die gleichwertige Anweisung im Systemprompt (app/llm/mistral.py).
_HINWEIS_MUSTER = re.compile(
    r"^(hallo|hi|hey|guten\s+(tag|morgen|abend)|servus|moin|danke\w*|"
    r"was\s+kannst\s+du|wer\s+bist\s+du|wie\s+funktionierst\s+du)[\s!?.,]*$",
    re.IGNORECASE,
)


class FakeLLM:
    name = "FakeLLM (Demo-Modus, Ersatzmodell)"

    def __init__(self) -> None:
        self._registrierte_fakten: dict[str, Fakten] = {}

    # -- Teststeuerung -----------------------------------------------------
    def registriere(self, frage: str, fakten: Fakten) -> None:
        """Legt fest, welche Fakten fuer eine (normalisierte) Frage zurueckgegeben werden."""
        self._registrierte_fakten[self._norm(frage)] = fakten

    @staticmethod
    def _norm(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    # -- Schnittstelle -------------------------------------------------------
    def extrahiere_fakten(self, frage: str, verlauf: list[str] | None = None,
                          fallstand: Fakten | None = None) -> Fakten:
        """`fallstand` (gespeicherter Stand) braucht der Demo-Modus nicht: er wertet den Verlauf
        aus; die Übernahme in den Stand macht app/fallstand.py wie beim echten Modell."""
        hinterlegt = self._registrierte_fakten.get(self._norm(frage))
        if hinterlegt is not None:
            return hinterlegt
        # Korpus-Lauf Demo 15.10.2026 (38 FALSCH): 'EUR 536,69 brutto, darin 85,69 € Umsatzsteuer' -- die Heuristik las den
        # Betrag mit vorangestellter Währung nicht. Wie im Router wird die Schreibweise vorher vereinheitlicht.
        from app.textnorm import waehrung_nach_hinten

        return self._heuristische_extraktion(waehrung_nach_hinten(frage),
                                             [waehrung_nach_hinten(v) for v in verlauf] if verlauf else verlauf)

    def _heuristische_extraktion(self, frage: str, verlauf: list[str] | None = None) -> Fakten:
        """Sehr einfache Regex-Heuristik fuer den Demo-Modus ohne Schluessel. Erkennt nur
        grobe Muster; alles andere bleibt bewusst `None` (nie raten).

        Livetest-Befund L2: wertet VERLAUF und die neue Nachricht GEMEINSAM aus. Vorher
        wurde nur `frage` (die neueste Nachricht) betrachtet -- nach einer Rueckfrage-Antwort
        wie 'natürliche Person' gingen Jahr/Betrag der vorherigen Nachricht verloren und die
        naechste Rueckfrage kam, als waere nichts bekannt (anders als beim echten
        Mistral-Adapter, der Verlauf und Frage von Anfang an zusammen schickt, siehe
        app/llm/mistral.py::extrahiere_fakten)."""
        if not verlauf and _HINWEIS_MUSTER.match(frage.strip()):
            return Fakten(anfrageart="hinweis", freitext_rest=frage)

        text_gesamt = "\n".join([*(verlauf or []), frage])
        text = normalisiere_umlaute(text_gesamt.lower())

        # Test des Nutzers im Codespace (16.10.2026): 'Gibt es ein Urteil zur Abgabepflicht von Werbeagenturen?' lief im
        # Demo-Modus als Bewertung (Frage nach dem Jahr). Eine Frage nach Rechtsprechung ohne Betrag ist eine Recherche
        # (wie beim echten Modell); die Wörter stehen in app/rag/konfig.json ('urteile_voll_wenn').
        from app.rag.zerlegen import KONFIG as _RAG

        if not verlauf and not re.search(r"\d\s*(?:€|eur\b|euro)", text) and any(
                re.search(r"(?<![a-z])" + re.escape(normalisiere_umlaute(w)), text) for w in _RAG.get("urteile_voll_wenn", [])):
            return Fakten(anfrageart="rechtsprechungsfrage", freitext_rest=frage)

        # Livetest 10.10.2026: '2000 euro' ist ein Betrag, kein Jahr.
        jahr = None
        for jahr_treffer in re.finditer(r"\b(19|20)\d{2}\b", text_gesamt):
            if not re.match(r"\s*(€|eur\b|euro)", text_gesamt[jahr_treffer.end():], re.IGNORECASE):
                jahr = int(jahr_treffer.group(0))
                break

        auftragnehmer_typ = erkenne_rechtsform_auftragnehmer(text_gesamt)

        verwerterart = None
        for muster, wert in _VERWERTERART_MUSTER:
            if re.search(muster, text):
                verwerterart = wert
                break

        leistungsart = None
        for muster, wert in _LEISTUNGSART_MUSTER:
            if re.search(muster, text):
                leistungsart = wert
                break

        positionen: list[Position] = []
        betrag_muster = r"([\d\.]{1,10}(?:,\d{2})?)\s*(?:€|eur\b|euro\b)"
        # Testfall 20 Positionen: stehen Beträge auf mehreren Zeilen (Liste von Leistungen),
        # ist der Text der Zeile die Bezeichnung der Position (für die Tätigkeitsprüfung).
        # Nur die NEUE Nachricht: sonst entstehen die Positionen früherer Nachrichten erneut
        # (Testprotokoll 11.10.2026, Demo-Modus). Bisherige Positionen hält der Fallstand.
        zeilen = [z for z in frage.splitlines() if re.search(betrag_muster, z, re.IGNORECASE)]
        if len(zeilen) > 1:
            for zeile in zeilen:
                bezeichnung = re.sub(betrag_muster, "", zeile, flags=re.IGNORECASE)
                bezeichnung = re.sub(r"^\s*\d+[.)]\s*", "", bezeichnung)
                bezeichnung = re.sub(r"\((?:an|von)\b[^)]*\)+|\b(?:netto|brutto)\b", "", bezeichnung, flags=re.IGNORECASE)
                bezeichnung = " ".join(bezeichnung.split()).strip(" :-–,")
                for betrag_text in re.findall(betrag_muster, zeile, re.IGNORECASE):
                    try:
                        positionen.append(Position(betrag=Decimal(betrag_text.replace(".", "").replace(",", ".")),
                                                   bezeichnung=bezeichnung or None))
                    except InvalidOperation:
                        continue
        elif len(re.findall(betrag_muster, text_gesamt, re.IGNORECASE)) > 1:
            # Mehrere Beträge in einem Satz ('3.000 € Honorar, 200 € Material und 50 € Telefon'):
            # die Wörter direkt nach dem Betrag sind die Bezeichnung.
            for treffer in re.finditer(betrag_muster, text_gesamt, re.IGNORECASE):
                rest = re.match(r"\s*(?:netto|brutto)?\s*([^\W\d][^,;.€\d]*?)(?=,|;|\.|\bund\b|\bplus\b|\bnetto\b|$|\d)",
                                text_gesamt[treffer.end():])
                bezeichnung = " ".join(rest.group(1).split()) if rest else ""
                if bezeichnung.lower() in ("netto", "brutto", "") or len(bezeichnung) > 60:
                    bezeichnung = ""
                try:
                    positionen.append(Position(betrag=Decimal(treffer.group(1).replace(".", "").replace(",", ".")),
                                               bezeichnung=bezeichnung or None))
                except InvalidOperation:
                    continue
        else:
            # Demo-Modus: EIN Betrag und eine ausdrücklich genannte Verwertungsgesellschaft (GEMA, VG Wort …)
            # -> Rolle 'verwertungsgesellschaft' (Begriffe aus app/rollen_belege.json, wie beim echten Modell
            # gegengeprüft). Sonst wurde 'an die GEMA gezahlt' im Demo-Modus als Honorar gezählt (P-34).
            from app.zuordnung import _ROLLEN_BELEGE

            vg = any(re.search(r"(?<![a-z])" + re.escape(b), text) for b in _ROLLEN_BELEGE.get("verwertungsgesellschaft", []))
            for betrag_text in re.findall(betrag_muster, text):
                normalisiert = betrag_text.replace(".", "").replace(",", ".")
                try:
                    positionen.append(Position(betrag=Decimal(normalisiert), rolle="verwertungsgesellschaft" if vg else None))
                except InvalidOperation:
                    continue

        veranstaltungszahl = None
        anzahl_treffer = re.search(r"(\d+)\s+veranstaltung", text)
        if anzahl_treffer:
            veranstaltungszahl = int(anzahl_treffer.group(1))

        # Livetest-Befund L3: eine Rueckfrage-Schaltflaeche "ja"/"nein" (Einnahmeabsicht) ist
        # nur aus der NEUEN Nachricht allein sicher deutbar -- ein "ja" irgendwo im bisherigen
        # Verlauf soll nicht rueckwirkend als Antwort auf eine andere Frage gelten.
        einnahmeabsicht = None
        frage_getrimmt = normalisiere_umlaute(frage.strip().lower())
        if frage_getrimmt == "ja":
            einnahmeabsicht = True
        elif frage_getrimmt == "nein":
            einnahmeabsicht = False

        # Demo-Modus: 'eine Rechnung von einer Fotografin ...' mit mehreren Positionen heißt:
        # derselbe Auftragnehmer; 'jeweils von verschiedenen ...' heißt: verschiedene.
        ein_auftragnehmer = None
        if len(positionen) > 1:
            if re.search(r"\b(verschiedene[nr]?|jeweils von)\b", text):
                ein_auftragnehmer = False
            elif re.search(r"\beine[r]? (sammel)?rechnung (von|einer|eines)\b", text):
                ein_auftragnehmer = True

        return Fakten(
            ein_auftragnehmer=ein_auftragnehmer,
            jahr=jahr,
            auftragnehmer_typ=auftragnehmer_typ,
            verwerterart=verwerterart,
            leistungsart=leistungsart,
            positionen=positionen,
            veranstaltungszahl=veranstaltungszahl,
            einnahmeabsicht=einnahmeabsicht,
            freitext_rest=frage,
        )

    def beschreibe_fall(self, kontext: AntwortKontext) -> str:
        """Teil 1g, Abschnitt B/C: EINE kurze, harmlose Fallbeschreibung -- nur mit
        Platzhaltern aus `erzeuge_platzhalter`, nie Zahlen/Normen/Ergebnisse/Wertungen.
        Der Antwort-Koerper selbst kommt ausschliesslich aus app/textbausteine.py."""
        werte = erzeuge_platzhalter(kontext)
        if "JAHR" in werte:
            return "Es geht um eine Anfrage für das Jahr {JAHR}."
        return "Es geht um eine Anfrage ohne weitere Jahresangabe."
