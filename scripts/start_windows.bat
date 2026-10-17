@echo off
rem „Rechnungen prüfen“ (ohne KI) unter Windows starten (Doppelklick). Ruft scripts\start_windows.ps1 auf.
powershell -ExecutionPolicy Bypass -File "%~dp0start_windows.ps1"
pause
