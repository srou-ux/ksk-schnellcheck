#!/usr/bin/env bash
# Startet „Rechnungen prüfen“ (ohne KI) in GitHub Codespaces. Kein Sprachmodell, kein Schlüssel.
# Nur erfundene Testdaten eingeben. Alles ist Entwurf – vom Steuerberater zu prüfen.
set -euo pipefail
cd "$(dirname "$0")/.." || exit 1
command -v tesseract >/dev/null || echo "Hinweis: Tesseract fehlt – Fotos und Scans gehen erst nach einem Neuaufbau des Codespace."

# Start und erneutes Verbinden dürfen keinen laufenden Upload abbrechen.
exec 9>"${TMPDIR:-/tmp}/ksk_rechnungen_start.lock"
flock -w 45 9
bereit() {
  python - <<'PY'
import json, sys, urllib.request
try:
    client = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with client.open('http://127.0.0.1:8000/gesundheit', timeout=1) as r:
        data = json.load(r)
    sys.exit(0 if data.get('modus') == 'dokumente' else 1)
except Exception:
    sys.exit(1)
PY
}

if ! bereit; then
  log="${TMPDIR:-/tmp}/ksk_rechnungen.log"
  nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$log" 2>&1 9>&- &
  server_pid=$!
  for versuch in {1..30}; do
    if ! kill -0 "$server_pid" 2>/dev/null; then
      echo "Dokumentenprüfung konnte nicht starten. Details: $log" >&2
      exit 1
    fi
    if bereit; then break; fi
    sleep 1
  done
  if ! bereit; then
    echo "Dokumentenprüfung noch nicht erreichbar. Details: $log" >&2
    exit 1
  fi
fi
echo "Dokument hochladen: http://localhost:8000/rechnungen"
echo "Codespaces öffnet Port 8000 im Browser. Falls der Browser den Tab blockiert: Ports → 8000 → Globus."
