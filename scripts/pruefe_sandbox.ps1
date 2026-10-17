# Sandbox-Nachweis (Chatbot Teil 1d): klont das Repo FRISCH (vom aktuellen Remote/Commit)
# in ein temporaeres Verzeichnis, baut dort eine neue virtuelle Umgebung, installiert
# app/requirements.txt und laesst den vollen Testlauf (python -m unittest discover -s
# tests/app) komplett unabhaengig vom aktuellen Arbeitsordner laufen.
#
# Aufruf aus dem Projektstamm: powershell -File scripts/pruefe_sandbox.ps1
$ErrorActionPreference = "Stop"

$sandboxVerzeichnis = Join-Path ([System.IO.Path]::GetTempPath()) ("ksk-sandbox-" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $sandboxVerzeichnis | Out-Null

try {
    $repoUrl = (git config --get remote.origin.url).Trim()
    $commit = (git rev-parse HEAD).Trim()

    Write-Host "== Sandbox-Nachweis =="
    Write-Host "Repo:        $repoUrl"
    Write-Host "Commit:      $commit"
    Write-Host "Verzeichnis: $sandboxVerzeichnis"
    Write-Host ""

    Write-Host "-- Klone frisch ..."
    git clone --quiet $repoUrl "$sandboxVerzeichnis\repo"
    git -C "$sandboxVerzeichnis\repo" checkout --quiet $commit

    Write-Host "-- Baue virtuelle Umgebung ..."
    python -m venv "$sandboxVerzeichnis\venv"
    & "$sandboxVerzeichnis\venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
    & "$sandboxVerzeichnis\venv\Scripts\python.exe" -m pip install --quiet -r "$sandboxVerzeichnis\repo\app\requirements.txt"

    Write-Host "-- Fuehre vollen Testlauf aus ..."
    Push-Location "$sandboxVerzeichnis\repo"
    $env:PYTHONPATH = "."
    & "$sandboxVerzeichnis\venv\Scripts\python.exe" -m unittest discover -s tests/app -v
    Write-Host "-- Gegenrechnung (Teil 1e): Uebereinstimmung, Mutationen, Sandbox ..."
    & "$sandboxVerzeichnis\venv\Scripts\python.exe" -m unittest discover -s tests/verifier -t . -v
    & "$sandboxVerzeichnis\venv\Scripts\python.exe" -m verifier.pruefe_register --nur-register
    Pop-Location
}
finally {
    Remove-Item -Recurse -Force $sandboxVerzeichnis -ErrorAction SilentlyContinue
}
