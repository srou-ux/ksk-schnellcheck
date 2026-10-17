"""Kanonische Ergebnisklassen der App-Schicht, abgebildet auf die echten Klassen-Konstanten
von `kern.rechnen` (seit Chatbot Teil 1b: der Kern ist real, kein Testdoppel mehr -- siehe
aufgaben/FUNDE_Chatbot.md, Befund 1, behoben).
"""
from __future__ import annotations

from kern import rechnen as K

ABGABEPFLICHTIG = K.ABGABEPFLICHTIG
NICHT_ABGABEPFLICHTIG = K.NICHT
GRENZFALL = K.GRENZFALL
RUECKFRAGE_NOETIG = K.RUECKFRAGE
NICHT_ABGEDECKT = K.NICHT_ABGEDECKT
PRUEFUNG_FEHLGESCHLAGEN = "Prüfung fehlgeschlagen"
# Nur fuer anfrageart == "rechtsprechungsfrage" (reine Recherche ohne Berechnung, siehe
# app/pflichtangaben.py und app/router.py, Befund 6 aus aufgaben/FUNDE_Chatbot.md): kommt
# nicht aus kern.rechnen, weil der Kern dafuer gar nicht aufgerufen wird.
RECHTSPRECHUNG_GEFUNDEN = "Rechtsprechung/Auslegung in der Quellenbasis gefunden"
# Chatbot Teil 1d, Abschnitt B: Zwischenschritt, bevor der Kern aufgerufen wird. Kommt aus
# app/bestaetigung.py, nicht aus kern.rechnen.
FAKTEN_BESTAETIGUNG_NOETIG = "Faktenbestätigung nötig"

# Chatbot Teil 1f, Abschnitt B: kern.rechnen.saeumniszuschlag liefert intern die generische
# Kernklasse ABGABEPFLICHTIG (K.ABGABEPFLICHTIG) -- das waere hier aber falsch benannt,
# weil ein Saeumniszuschlag keine Abgabepflicht-Entscheidung ist, sondern ein Zuschlag auf
# einen bereits feststehenden Rueckstand. Die App zeigt deshalb eine eigene Anzeigeklasse
# (Vorbild RECHTSPRECHUNG_GEFUNDEN); die Kernklasse bleibt nur intern im Protokoll
# (app/router.py). Entscheidung dokumentiert in aufgaben/FUNDE_Chatbot.md.
SAEUMNISZUSCHLAG_BERECHNET = "Säumniszuschlag (Vorschlag)"

# Chatbot Teil 1f, Abschnitt C: Auskunftsfragen (Abgabesatz/Schwelle/Meldefrist/Aufbewahrung/
# Pauschale) sind keine Abgabepflicht-Entscheidung, sondern eine erteilte Auskunft aus dem
# Register -- eigene Anzeigeklasse, kommt nicht aus kern.rechnen. Entscheidung dokumentiert
# in aufgaben/FUNDE_Chatbot.md.
AUSKUNFT_ERTEILT = "Auskunft aus dem Regelwerk"

# Chatbot Teil 1f, Abschnitt J.3: Begruessung/Smalltalk ohne jede Sachfrage ("hallo",
# "danke", "was kannst du?") ist keine Rueckfrage und kein Ergebnis -- eine feste, vom
# System formulierte Kurzbeschreibung mit Beispielfragen.
HINWEIS = "Hinweis"

ALLE = (
    ABGABEPFLICHTIG,
    NICHT_ABGABEPFLICHTIG,
    GRENZFALL,
    RUECKFRAGE_NOETIG,
    NICHT_ABGEDECKT,
    PRUEFUNG_FEHLGESCHLAGEN,
    RECHTSPRECHUNG_GEFUNDEN,
    FAKTEN_BESTAETIGUNG_NOETIG,
    SAEUMNISZUSCHLAG_BERECHNET,
    AUSKUNFT_ERTEILT,
    HINWEIS,
)
