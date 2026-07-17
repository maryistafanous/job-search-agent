@echo off
REM ==== job_search.db recovery — 2026-07-12 corruption ====
REM Run this in C:\JobSearch\job-search-agent AFTER killing the hung job-216 kit.
setlocal
cd /d C:\JobSearch\job-search-agent

echo [1/4] Preserving the corrupt DB (do not delete evidence)...
if exist db\job_search.db copy /Y db\job_search.db db\job_search.db.corrupt-20260712 >nul

echo [2/4] Clearing any stale sidecars...
del /q db\job_search.db-wal    2>nul
del /q db\job_search.db-journal 2>nul
del /q db\job_search.db-shm    2>nul

echo [3/4] Restoring clean backup (07:44, 261 rows)...
copy /Y backups\job_search-20260712_074410.bak db\job_search.db >nul

echo [4/4] Verifying integrity...
python scripts\job_db.py check
echo.
echo Done. If check passed, re-run the ATS kit for jobs 216 and 261 from the
echo dashboard to regenerate the "Kit generated" notes (docx already exist).
endlocal
