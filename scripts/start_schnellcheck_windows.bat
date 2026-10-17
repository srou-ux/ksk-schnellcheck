@echo off
REM KSK-Schnellcheck lokal starten (ohne KI). Danach im Browser: http://127.0.0.1:8100
cd /d "%~dp0\.."
python -m pip install -r schnellcheck\requirements.txt
python -m schnellcheck --port 8100
pause
