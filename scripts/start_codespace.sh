#!/usr/bin/env bash
# Startet „Rechnungen prüfen“ (ohne KI) in GitHub Codespaces. Kein Sprachmodell, kein Schlüssel.
# Nur erfundene Testdaten eingeben. Alles ist Entwurf – vom Steuerberater zu prüfen.
cd "$(dirname "$0")/.." || exit 1
command -v tesseract >/dev/null || echo "Hinweis: Tesseract fehlt – Fotos und Scans gehen erst nach einem Neuaufbau des Codespace."
pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "uvicorn app.dokument_app:app" 2>/dev/null
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/ksk_rechnungen.log 2>&1 &
sleep 2
echo "Rechnungen prüfen gestartet. Port 8000 öffnet sich im Browser (Reiter 'Ports'). Log: /tmp/ksk_rechnungen.log"
