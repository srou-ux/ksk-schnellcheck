#!/usr/bin/env bash
# Sandbox-Nachweis (Chatbot Teil 1d): klont das Repo FRISCH (vom aktuellen Remote/Commit)
# in ein temporaeres Verzeichnis, baut dort eine neue virtuelle Umgebung, installiert
# app/requirements.txt und laesst den vollen Testlauf (python -m unittest discover -s
# tests/app) komplett unabhaengig vom aktuellen Arbeitsordner laufen.
#
# Aufruf aus dem Projektstamm: bash scripts/pruefe_sandbox.sh
set -euo pipefail

sandbox_verzeichnis="$(mktemp -d)"
trap 'rm -rf "$sandbox_verzeichnis"' EXIT

repo_url="$(git config --get remote.origin.url)"
commit="$(git rev-parse HEAD)"

echo "== Sandbox-Nachweis =="
echo "Repo:      $repo_url"
echo "Commit:    $commit"
echo "Verzeichnis: $sandbox_verzeichnis"
echo

echo "-- Klone frisch ..."
git clone --quiet "$repo_url" "$sandbox_verzeichnis/repo"
git -C "$sandbox_verzeichnis/repo" checkout --quiet "$commit"

echo "-- Baue virtuelle Umgebung ..."
python3 -m venv "$sandbox_verzeichnis/venv" 2>/dev/null || python -m venv "$sandbox_verzeichnis/venv"
# shellcheck disable=SC1091
source "$sandbox_verzeichnis/venv/bin/activate" 2>/dev/null || source "$sandbox_verzeichnis/venv/Scripts/activate"
python -m pip install --quiet --upgrade pip
pip install --quiet -r "$sandbox_verzeichnis/repo/app/requirements.txt"

echo "-- Fuehre vollen Testlauf aus ..."
cd "$sandbox_verzeichnis/repo"
PYTHONPATH=. python -m unittest discover -s tests/app -v
echo "-- Gegenrechnung (Teil 1e): Uebereinstimmung, Mutationen, Sandbox ..."
PYTHONPATH=. python -m unittest discover -s tests/verifier -t . -v
python -m verifier.pruefe_register --nur-register
