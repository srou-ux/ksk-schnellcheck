"""Extraktion vor dem Regelkern.

Der Kern entscheidet. Diese Schicht füllt nur Felder.
`rule` liest mit festen Mustern, `mistral` liest per OCR und Small.
Unsichere oder leere Felder werden nicht geraten.
"""
from extraktion.schnittstelle import extrahiere_dokument

__all__ = ["extrahiere_dokument"]
