#!/usr/bin/env bash
# Startet den KSK-Assistenten in GitHub Codespaces: zwei Bereiche in einer Oberfläche – „KSK-Chat“ und „Rechnungen prüfen“.
# Sprachmodell: Mistral Small (EU), Schlüssel als Codespaces-Secret MISTRAL_API_KEY. Ohne Schlüssel: Demo-Modus.
# Ohne Sprachmodell trotz Schlüssel:   LLM_ANBIETER=demo bash scripts/start_codespace.sh
# Nur erfundene Testdaten eingeben. Alles ist Entwurf – vom Steuerberater zu prüfen.
cd "$(dirname "$0")/.." || exit 1
if [ -z "${MISTRAL_API_KEY:-}" ]; then echo "Kein MISTRAL_API_KEY gesetzt: Demo-Modus mit Ersatzmodell."; fi
if [ "${LLM_ANBIETER:-}" = "demo" ]; then echo "LLM_ANBIETER=demo: Demo-Modus mit Ersatzmodell (kein Sprachmodell)."; fi
command -v tesseract >/dev/null || echo "Hinweis: Tesseract fehlt – Fotos und Scans in 'Rechnungen prüfen' gehen erst nach einem Neuaufbau des Codespace."
echo "Quellenindex (RAG) wird aktualisiert – beim ersten Mal etwa eine Minute ..."
python -m app.rag.index || echo "Quellenindex nicht gebaut – der Chat läuft ohne Quellenabruf weiter."
pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "uvicorn app.dokument_app:app" 2>/dev/null
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/ksk_chatbot.log 2>&1 &
sleep 2
echo "KSK-Assistent gestartet (Chat und Rechnungen prüfen). Port 8000 öffnet sich im Browser (Reiter 'Ports'). Log: /tmp/ksk_chatbot.log"
