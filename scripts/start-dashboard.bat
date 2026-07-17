@echo off
rem Starts the local job dashboard (FastAPI). Page opens automatically.
setlocal
cd /d "%~dp0..\dashboard"
python dashboard_api.py
endlocal
