"""Einstiegspunkt der Vollversion „Rechnungen prüfen“ (ohne KI).

Start: python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

17.10.2026: Der frühere KSK-Chat brauchte ein Sprachmodell (Mistral) und ist entfernt. Die App besteht jetzt aus dem
Dokumentenbereich: Upload (PDF, Foto, Excel, CSV) -> Lesen mit Python -> Angaben bestätigen -> Regelkern + Gegenrechnung.
"""
from app.dokument_app import app  # noqa: F401  (Startpunkt für uvicorn)
