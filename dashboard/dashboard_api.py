#!/usr/bin/env python3
"""Job dashboard — local FastAPI server (backend only).

Reads all machine-specific values from ../config.json (see config.example.json).

Endpoints:
  GET  /            dashboard page (dashboard_ui/index.html)
  GET  /static/*    UI assets
  GET  /api/jobs    all Job_Tracker rows as JSON
  POST /api/updates apply status changes: {"updates":[{"id":182,"status":"Applied"}]}

Write safety:
  - In-process mutex + native SQLite locking (busy_timeout).
  - Integrity check before and after every write, plus read-back verification.
  - Transition mode: while config transition.honor_lock_file is true, the
    legacy <db>.lock protocol is honored so a legacy pipeline writer and this
    server never collide (423 returned when the lock is held).

Run:  python dashboard_api.py   (or scripts/start-dashboard.bat)
"""
import json
import os
import shutil
import sqlite3
import subprocess
import threading
import time
import webbrowser
from datetime import date, datetime

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
with open(os.path.join(REPO, "config.json"), encoding="utf-8") as f:
    CFG = json.load(f)

UI_DIR = os.path.join(HERE, "dashboard_ui")
DB = CFG["db_path"]
LOCK = DB + ".lock"
JOURNAL = DB + "-journal"
WAL = DB + "-wal"
PORT = CFG.get("dashboard_port", 8765)
WRITER = "dashboard-api"
ALLOWED = set(CFG.get("status_values", ["To Apply", "Applied", "Interviewing", "Offer",
                                        "Rejected", "Expired", "SKIP", "N/A"]))
HONOR_LOCK = CFG.get("transition", {}).get("honor_lock_file", False)

# ATS-kit runner: launch the resume-tailor skill headless from the repo root.
AGENT_REPO = REPO
KIT_LOG_DIR = os.path.join(REPO, "logs")
KIT_MODEL = "fable"
# Registry of in-flight kit runs: {job_id: {"proc": Popen, "log": path, "started": iso}}
kit_runs = {}
kit_lock = threading.Lock()

app = FastAPI(title="Job Dashboard API")
app.mount("/static", StaticFiles(directory=UI_DIR), name="static")
write_mutex = threading.Lock()  # serialize writes within this process


class Update(BaseModel):
    id: int
    status: str


class UpdateRequest(BaseModel):
    updates: list[Update]


class KitRequest(BaseModel):
    id: int


# ---------------- legacy lock-file protocol (transition only) ----------------

def lock_holder():
    """Return contents if the lock is held and fresh, else None."""
    try:
        if os.path.getsize(LOCK) > 0:
            age = time.time() - os.path.getmtime(LOCK)
            if age < 1800:
                with open(LOCK, "r", encoding="utf-8", errors="replace") as f:
                    return f.read().strip() or "(unknown writer)"
            with open(LOCK, "w"):  # stale (30+ min) — clear
                pass
    except FileNotFoundError:
        pass
    return None


def acquire_lock():
    """Acquire the write lock. Returns (ok, error_message)."""
    if not HONOR_LOCK:
        return True, ""
    holder = lock_holder()
    if holder:
        return False, f"DB locked by: {holder}. Try again in a few minutes."
    stamp = f"{WRITER} {datetime.now().isoformat(timespec='seconds')}"
    with open(LOCK, "w", encoding="utf-8") as f:
        f.write(stamp)
    time.sleep(1.0)
    try:
        with open(LOCK, "r", encoding="utf-8", errors="replace") as f:
            if WRITER not in f.read():
                return False, "Lost lock race — another writer grabbed the lock. Try again."
    except FileNotFoundError:
        return False, "Lock file vanished — another writer interfered. Try again."
    return True, ""


def release_lock():
    if not HONOR_LOCK:
        return
    try:
        with open(LOCK, "w"):
            pass  # truncate to 0 — never delete (legacy convention)
    except OSError:
        pass


def journal_check():
    """Refuse to write over another writer's mid-flight transaction."""
    if not HONOR_LOCK:
        return True, ""
    hot = any(os.path.exists(p) and os.path.getsize(p) > 0 for p in (JOURNAL, WAL))
    if hot:
        db_age = time.time() - os.path.getmtime(DB)
        if db_age < 600:
            return False, "A hot journal and fresh DB mtime indicate another writer is mid-transaction. Try again later."
        for p in (JOURNAL, WAL):
            if os.path.exists(p) and os.path.getsize(p) > 0:
                with open(p, "w"):
                    pass
    return True, ""


# ---------------- API ----------------

@app.get("/api/jobs")
def get_jobs():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=10)
    try:
        ok = con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        if not ok:
            return JSONResponse({"ok": False, "error": "integrity_check failed — do NOT write; restore from backup"}, status_code=500)
        have = {c[1] for c in con.execute("PRAGMA table_info(Job_Tracker)")}
        rm_expr = "Recruiter_Match" if "Recruiter_Match" in have else "NULL"
        rows = con.execute(
            f"""SELECT Job_ID, Title, Company, Location, Salary_Range, Fitness_Score,
                      Date_Posted, App_URL, Key_Gaps, Anchor_Story, Status, {rm_expr}, Source
               FROM Job_Tracker ORDER BY Job_ID DESC"""
        ).fetchall()
    finally:
        con.close()
    jobs = [
        dict(id=r[0], title=r[1] or "", co=r[2] or "", loc=r[3] or "", sal=r[4] or "",
             score=r[5] if r[5] is not None else 0, posted=r[6] or "", url=r[7] or "",
             gaps=r[8] or "", anchor=r[9] or "", status=r[10] or "",
             rm=r[11], src=r[12] or "")
        for r in rows
    ]
    return {"ok": True, "jobs": jobs, "generated": datetime.now().isoformat(timespec="seconds")}


@app.post("/api/updates")
def post_updates(req: UpdateRequest):
    if not req.updates:
        return {"ok": True, "applied": 0}
    for u in req.updates:
        if u.status not in ALLOWED:
            return JSONResponse({"ok": False, "error": f"Invalid status: {u.status!r}"}, status_code=400)

    with write_mutex:
        ok, err = acquire_lock()
        if not ok:
            return JSONResponse({"ok": False, "error": err}, status_code=423)
        try:
            ok, err = journal_check()
            if not ok:
                return JSONResponse({"ok": False, "error": err}, status_code=423)

            con = sqlite3.connect(DB, timeout=10)
            try:
                con.execute("PRAGMA busy_timeout=10000")
                if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    return JSONResponse({"ok": False, "error": "integrity_check failed BEFORE write — nothing written"}, status_code=500)
                n0 = con.execute("SELECT COUNT(*) FROM Job_Tracker").fetchone()[0]
                today = date.today().isoformat()
                missing = []
                for u in req.updates:
                    cur = con.execute(
                        "UPDATE Job_Tracker SET Status = ?, Date_Updated = ? WHERE Job_ID = ?",
                        (u.status, today, u.id),
                    )
                    if cur.rowcount == 0:
                        missing.append(u.id)
                if missing:
                    con.rollback()
                    return JSONResponse({"ok": False, "error": f"No row with Job_ID {missing} — nothing written"}, status_code=400)
                con.commit()
                if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    return JSONResponse({"ok": False, "error": "integrity_check failed AFTER commit — check the DB"}, status_code=500)
                if con.execute("SELECT COUNT(*) FROM Job_Tracker").fetchone()[0] != n0:
                    return JSONResponse({"ok": False, "error": "row count changed unexpectedly — check the DB"}, status_code=500)
                for u in req.updates:  # read-back verification
                    got = con.execute("SELECT Status FROM Job_Tracker WHERE Job_ID = ?", (u.id,)).fetchone()
                    if not got or got[0] != u.status:
                        return JSONResponse({"ok": False, "error": f"Read-back mismatch on Job_ID {u.id}"}, status_code=500)
            finally:
                con.close()
        finally:
            release_lock()

    return {"ok": True, "applied": len(req.updates)}


# ---------------- ATS kit runner ----------------

def _kit_command(prompt):
    """Build the headless-Claude argv. On Windows `claude` is a .cmd, so route
    through cmd.exe /c; args stay as a list so titles/company names (e.g. with
    '&') are quoted safely — no shell string interpolation."""
    if os.name == "nt":
        return ["cmd", "/c", "claude", "-p", "--model", KIT_MODEL, prompt]
    claude = shutil.which("claude") or "claude"
    return [claude, "-p", "--model", KIT_MODEL, prompt]


@app.post("/api/ats-kit")
def post_ats_kit(req: KitRequest):
    # Look up the job (read-only) so the prompt uses trusted DB values.
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=10)
    try:
        row = con.execute(
            "SELECT Title, Company, App_URL FROM Job_Tracker WHERE Job_ID = ?",
            (req.id,),
        ).fetchone()
    finally:
        con.close()
    if not row:
        return JSONResponse({"ok": False, "error": f"No job with Job_ID {req.id}"}, status_code=404)
    title, company, url = row[0] or "", row[1] or "", row[2] or ""
    if not url:
        return JSONResponse({"ok": False, "error": "Job has no App_URL — nothing to tailor against."}, status_code=400)

    with kit_lock:
        cur = kit_runs.get(req.id)
        if cur and cur["proc"].poll() is None:
            return JSONResponse({"ok": False, "error": "A kit run is already in progress for this job."}, status_code=409)

        if not os.path.isdir(AGENT_REPO):
            return JSONResponse({"ok": False, "error": f"Agent repo not found at {AGENT_REPO}"}, status_code=500)
        os.makedirs(KIT_LOG_DIR, exist_ok=True)

        prompt = (
            f"Prepare ATS kit for Job #{req.id} ({title} at {company}) "
            f"using the resume-tailor skill"
        )
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(KIT_LOG_DIR, f"ats-kit-{req.id}-{ts}.log")
        try:
            log_fh = open(log_path, "w", encoding="utf-8")
            proc = subprocess.Popen(
                _kit_command(prompt),
                cwd=AGENT_REPO,
                stdout=log_fh,
                stderr=subprocess.STDOUT,
            )
        except Exception as e:
            return JSONResponse({"ok": False, "error": f"Failed to launch Claude: {e}"}, status_code=500)
        kit_runs[req.id] = {"proc": proc, "log": log_path, "started": datetime.now().isoformat(timespec="seconds")}

    return {"ok": True, "started": True, "job_id": req.id, "log": os.path.basename(log_path)}


@app.get("/api/ats-kit/status")
def get_ats_kit_status(id: int):
    with kit_lock:
        run = kit_runs.get(id)
        if not run:
            return {"ok": True, "state": "idle", "job_id": id}
        rc = run["proc"].poll()
    if rc is None:
        return {"ok": True, "state": "running", "job_id": id, "started": run["started"]}
    return {"ok": True, "state": "done", "job_id": id, "returncode": rc,
            "log": os.path.basename(run["log"])}


# ---------------- dashboard page ----------------

@app.get("/")
def index():
    return FileResponse(os.path.join(UI_DIR, "index.html"), media_type="text/html")


if __name__ == "__main__":
    import uvicorn
    threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}/")).start()
    print(f"Job dashboard: http://127.0.0.1:{PORT}/  (Ctrl+C to stop)")
    uvicorn.run(app, host="127.0.0.1", port=PORT)
