@echo off
rem Runs the morning job pipeline headless via Claude Code.
rem Use manually or as a Windows Task Scheduler action.
setlocal
cd /d "%~dp0.."
if not exist logs mkdir logs
call :cleartmp
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set TS=%%i
echo Backing up database...
python scripts\backup_db.py
echo Running morning pipeline... log: logs\pipeline-%TS%.log
rem Keep the machine awake for the duration of the run (2026-07-14: PC slept 10 min
rem into the 06:08 run -> ERR_NETWORK_IO_SUSPENDED, pipeline suspended 2.5h).
rem keep_awake.ps1 watches this cmd process and releases when it exits.
start "" /b powershell -NoProfile -ExecutionPolicy Bypass -File scripts\keep_awake.ps1
rem --dangerously-skip-permissions: unattended run, no one to approve prompts (can't hang on a permission gate)
rem --verbose --output-format stream-json: emit one JSON event per step so the log fills LIVE instead of only at the end
claude -p --model sonnet --dangerously-skip-permissions --verbose --output-format stream-json "Read pipeline/morning-pipeline.md and execute it exactly, phase by phase." > "logs\pipeline-%TS%.log" 2>&1
call :cleartmp
echo Done. Log: logs\pipeline-%TS%.log
endlocal
goto :eof

:cleartmp
rem Clear scratch files from EVERY folder that can accumulate them:
rem tmp\, repo root (tmp_*/_tmp_*), applications\ (_kit* helper scripts from
rem ATS-kit runs -- files only, kit FOLDERS are kept), scripts\ (tmp_*.py),
rem __pycache__, and Playwright page snapshots.
if not exist tmp mkdir tmp
del /q tmp\* >nul 2>&1
for /d %%d in (tmp\*) do rmdir /s /q "%%d" >nul 2>&1
del /q tmp_* _tmp_* >nul 2>&1
del /q applications\_* applications\tmp_* >nul 2>&1
del /q scripts\tmp_* scripts\_tmp_* >nul 2>&1
if exist scripts\__pycache__ rmdir /s /q scripts\__pycache__ >nul 2>&1
if exist dashboard\__pycache__ rmdir /s /q dashboard\__pycache__ >nul 2>&1
if exist .playwright-mcp del /q .playwright-mcp\* >nul 2>&1
goto :eof
