# KSK-Dokumentenprüfung unter Windows starten. Entwurf – vom Steuerberater zu prüfen.
#
# Aufruf in PowerShell im Ordner des Repos (z. B. C:\ksk cloud):
#     powershell -ExecutionPolicy Bypass -File scripts\start_windows.ps1
#
# Was das Skript tut:
#   1. legt beim ersten Start eine eigene Python-Umgebung im Ordner .venv an,
#   2. installiert die Pakete aus app\requirements.txt (nur beim ersten Start oder wenn sie sich ändern),
#   3. startet die Dokumentenprüfung und öffnet http://localhost:8000 im Browser.
#
# Ohne KI: kein Sprachmodell und kein API-Schlüssel. Für Fotos/Scans: Tesseract + Poppler im PATH.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python fehlt. Bitte Python 3.11 oder neuer von python.org installieren (Haken 'Add to PATH')." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Lege die Python-Umgebung .venv an ..."
    python -m venv .venv
}
$py = ".venv\Scripts\python.exe"
$merker = ".venv\requirements.installiert"
$stand = (Get-FileHash app\requirements.txt).Hash
if (-not (Test-Path $merker) -or (Get-Content $merker) -ne $stand) {
    Write-Host "Installiere die Pakete (einmalig) ..."
    & $py -m pip install --disable-pip-version-check -q -r app\requirements.txt
    Set-Content $merker $stand
}
Write-Host "Fotos und Scans in 'Rechnungen prüfen' brauchen zusätzlich Tesseract und Poppler im PATH (app\DOKUMENTE.md)."
Write-Host "Starte „Rechnungen prüfen“ (ohne KI) auf http://localhost:8000 (Beenden mit Strg+C) ..." -ForegroundColor Green
Start-Process "http://localhost:8000/"
& $py -m uvicorn app.main:app --host 127.0.0.1 --port 8000
