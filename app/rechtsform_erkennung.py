"""Gemeinsame, deterministische Rechtsform-Erkennung aus Freitext (Prüfkatalog-Befund M1.3,
aufgaben/PROMPT_ClaudeCode_Chatbot_Pruefkatalog1_Befunde.md).

Eine Stelle für die Muster, statt sie zweimal zu pflegen: `app/llm/fake.py` (Heuristik im
Demo-Modus) UND `app/zuordnung.py::ergaenze_rechtsform` (deterministische Ergänzung NACH
jedem Modellaufruf, auch Mistral) nutzen dieselben Regeln. Erkennt nur feste Muster -- rät
nie bei unklaren Wörtern.
"""
from __future__ import annotations

import re

_UMLAUT_TABELLE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def normalisiere_umlaute(text: str) -> str:
    """Die Muster unten sind ASCII geschrieben ('natuerliche person'); ohne diese
    Normalisierung erkennt die Heuristik z. B. die eigene Rückfrage-Schaltfläche
    'natürliche Person' (echte Umlaute) nicht."""
    return text.translate(_UMLAUT_TABELLE)


# Livetest-Befund L3: "Einzelperson"/"Einzelunternehmer"/"Privatperson" sind gängige
# Synonyme für eine natürliche Person (Alltagsfälle 11.10.2026: auch "freier Journalist").
RECHTSFORM_MUSTER: list[tuple[str, str]] = [
    # Testfall 20 Positionen, Small (17.10.2026): 'einen Cloud-Anbieter (Aktiengesellschaft)' -- ausgeschriebene Formen.
    (r"\bgmbh\b|\bug\b|\bag\b|aktiengesellschaft|gesellschaft mit beschraenkter haftung|unternehmergesellschaft",
     "GmbH_UG_AG"),
    (r"\bgbr\b", "GbR"),
    (r"\bkg\b|\bohg\b", "KG_OHG"),
    (r"\bverein\b|\be\.?\s?v\.?\b", "Verein"),
    (r"ausland|im ausland|auslaendisch", "Ausland"),
    (r"natuerliche person|einzelperson|einzelunternehmer|privatperson|\bfrei(?:e|en|er)?\s+\w+|freiberufl|\bfreelance", "natuerliche_person"),
]


# Prüfung SaaS gegen Playground-Fälle (10.10.2026): "Wir sind eine GmbH und haben einem
# Grafiker 2.000 Euro gezahlt" ergab Rechtsform GmbH für den GRAFIKER -> "nicht
# abgabepflichtig"; "Unser Verein hatte vier Konzerte" ergab Rechtsform Verein für die MUSIKER.
# Ein Rechtsform-Wort, vor dem im selben Satz kurz zuvor die eigene Seite genannt wird
# ("wir", "unser", "ich", "mein"), beschreibt den Auftraggeber, nicht den Auftragnehmer.
# Alltagstest AT-2026-053 (live 15.10.2026): 'We are a German GmbH and paid a freelance photographer' -- auch
# englische Selbstbezüge ('we', 'our'; nicht 'us' wegen 'US-Dollar').
_EIGENE_SEITE = re.compile(r"\b(wir|uns|unser\w*|ich|mein\w*|we|our)\b")
_FENSTER_WOERTER = 3
# Härtetest HT-2026-011 (14.10.2026): "wir sind ein Verlag (GmbH) und haben an einen Autor 3.400 € gezahlt"
# -- 'wir' steht vier Wörter vor 'GmbH'; die GmbH galt als Rechtsform des AUTORS (nicht abgabepflichtig,
# 5 von 6 Live-Läufen). Ein Selbstbild 'wir sind / ich bin / wir als' mit höchstens drei Wörtern ohne
# Präposition oder Artikel im Dativ bis zur Rechtsform beschreibt ebenfalls die eigene Seite. Ein größeres
# Fenster allein wäre falsch ('wir haben der Klangwerk GmbH gezahlt' nennt den Auftragnehmer).
_SELBSTBILD = re.compile(r"\b(?:wir sind|ich bin|wir als|ich als|we are|i am)\s+((?:[\w-]+\s+){0,3})\(?\s*$")
_NICHT_EIGENE_SEITE = {"an", "fuer", "von", "bei", "mit", "dem", "den", "einem", "einer", "zu", "zur", "zum"}
_SATZ_TRENNER = re.compile(r"[.!?;\n]")
# Alltagstest AT-2026-035 (live 15.10.2026): 'GmbH zahlte 2026: 1.200 EUR an Videograf' -- die GmbH ist der ZAHLER
# (Subjekt vor dem Zahlverb), nicht der Videograf. Folgt auf das Rechtsform-Wort binnen zwei Wörtern ein Zahlverb,
# beschreibt es die eigene Seite. 'hat' bewusst nicht ('die Foto GmbH hat uns 800 EUR berechnet').
_ZAHLER = re.compile(r"^\W*(?:[\w-]+\W+){0,2}?(?:zahlte|zahlt|zahlten|bezahlte|bezahlten|ueberwies|ueberwiesen)\b")


# Testfall 20 Positionen, Small (17.10.2026): 'haben wir eine selbständige Einzelperson beauftragt' -- der Akkusativ
# ('eine', 'einen', 'ein') nach 'wir' nennt ebenfalls den Empfänger. 'wir sind eine GmbH' bleibt die eigene Seite
# (Selbstbild-Prüfung unten).
_EMPFAENGER_MARKE = _NICHT_EIGENE_SEITE | {"der", "die", "das", "eine", "einen", "ein"}

# Testarchiv mit mistral-small-latest (17.10.2026, HT-2026-099): '2000 euro an einen Kuenstler gezahlt, 2026, GmbH.' --
# eine nachgestellte Rechtsform in einem Satz, der den Empfänger als PERSON nennt ('an einen Künstler', 'an eine freie
# Grafikerin'), beschreibt den Absender. Personenwörter aus app/vertretung_begriffe.json ('kuenstler').
def _personen_empfaenger() -> re.Pattern:
    import json
    from pathlib import Path

    woerter = json.loads((Path(__file__).resolve().parent / "vertretung_begriffe.json").read_text(encoding="utf-8"))["kuenstler"]
    stamm = "|".join(sorted({re.escape(normalisiere_umlaute(w.lower())) for w in woerter}, key=len, reverse=True))
    return re.compile(rf"\ban\s+(?:einen|eine|einem|einer|den|die|der)\s+(?:\w+\s+)?(?:{stamm})(?:in|innen|en|n|s)?\b")


_PERSONEN_EMPFAENGER = _personen_empfaenger()


def _empfaenger_nach_eigener_seite(davor: list[str]) -> bool:
    """Korpus-Lauf 15.10.2026: 'haben wir der Pixelwerk GmbH 950 € gezahlt' -- 'wir' ist der Zahler, 'der Pixelwerk GmbH'
    der Empfänger. Steht NACH dem letzten Wort der eigenen Seite ein Artikel oder eine Präposition des Empfängers und kein
    Komma dazwischen (eine Beifügung 'wir, die Muster GmbH' bleibt die eigene Seite), ist die Rechtsform die des
    Auftragnehmers."""
    letzte = max((i for i, w in enumerate(davor) if _EIGENE_SEITE.fullmatch(w.strip(",.;:()"))), default=None)
    if letzte is None or any("," in w for w in davor[letzte:]):
        return False
    return bool({w.strip(",.;:()") for w in davor[letzte + 1:]} & _EMPFAENGER_MARKE)


def erkenne_rechtsform_auftragnehmer(text: str) -> str | None:
    """Wie `erkenne_rechtsform`, aber nur für den AUFTRAGNEHMER und ohne Raten:
    - Treffer, vor denen im selben Satz innerhalb der letzten drei Wörter die eigene Seite
      steht ('wir sind eine GmbH', 'unser Verein'), werden übergangen;
    - bleiben verschiedene Rechtsformen übrig, ist unklar, welche gemeint ist -> None
      (app/pflichtangaben.py fragt dann gezielt nach)."""
    gefunden: set[str] = set()
    for satz in _SATZ_TRENNER.split(normalisiere_umlaute(text.lower())):
        for muster, wert in RECHTSFORM_MUSTER:
            for treffer in re.finditer(muster, satz):
                davor = satz[: treffer.start()].split()[-_FENSTER_WOERTER:]
                if _EIGENE_SEITE.search(" ".join(davor)) and not _empfaenger_nach_eigener_seite(davor):
                    continue
                selbst = _SELBSTBILD.search(satz[: treffer.start()])
                if selbst and not (set(selbst.group(1).split()) & _NICHT_EIGENE_SEITE):
                    continue
                # AT-2026-054: 'Wir haben … an eine freie Malerin gezahlt, GmbH.' -- nachgestellte Rechtsform am Satzende
                # in einem Satz mit 'wir/uns': die Selbstbeschreibung des Absenders.
                if (satz[: treffer.start()].rstrip().endswith(",") and not satz[treffer.end():].strip(" )\t")
                        and (_EIGENE_SEITE.search(satz[: treffer.start()])
                             or _PERSONEN_EMPFAENGER.search(satz[: treffer.start()]))):
                    continue
                if _ZAHLER.match(satz[treffer.end():]) or re.match(r"-?konto\b", satz[treffer.end():]):
                    continue  # 'GmbH zahlte …', 'vom GmbH-Konto bezahlt': der Zahler (AT-2026-035)
                gefunden.add(wert)
    return gefunden.pop() if len(gefunden) == 1 else None


def erkenne_rechtsform(text: str) -> str | None:
    """Liefert die erste erkannte Rechtsform aus Freitext, oder `None`."""
    normalisiert = normalisiere_umlaute(text.lower())
    for muster, wert in RECHTSFORM_MUSTER:
        if re.search(muster, normalisiert):
            return wert
    return None
