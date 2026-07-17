#!/usr/bin/env python3
"""job_db.py — the ONLY write path to job_search.db for the agent pipeline.

All access is native SQLite (parameterized SQL, busy_timeout, integrity
checks). No copy-out/copy-back: this script is designed to run natively on
the machine that owns the DB file, where SQLite locking works.

Commands (all output one JSON object on stdout):
  python scripts/job_db.py list-pending [--limit N]
  python scripts/job_db.py insert --file rows.jsonl
  python scripts/job_db.py apply-scores --file scores.jsonl
  python scripts/job_db.py update-status --file updates.jsonl
  python scripts/job_db.py check
  python scripts/job_db.py migrate        # add any missing schema columns

JSONL record shapes:
  insert:        posting fields (title, company required; url recommended)
  apply-scores:  job-match JSON (url, job_title, company, jd, salary_range,
                 employment_type, date_posted, hiring_contact, track,
                 fitness_score, recruiter_match, key_gaps[], anchor_story, notes)
  update-status: {"job_id": 123, "status": "Applied", "date": "YYYY-MM-DD"}
                 or {"title": "...", "company": "...", "status": "...", ...}

Transition mode: if config.json transition.honor_lock_file is true, writes
acquire/release the legacy <db>.lock file so this runtime never collides
with a legacy writer still using the old lock-file protocol.
"""
import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import date, datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WRITER = "claude-code-job-db"

# Columns the pipeline may set on INSERT (Job_ID / Date_Created are automatic)
INSERT_COLS = ["Source", "Agent", "App_URL", "Other_App_URL", "Title", "Company",
               "Location", "JD", "Salary_Range", "Employment_Type", "Date_Posted",
               "HM_or_TA", "Job_Track", "Fitness_Score", "Recruiter_Match",
               "Key_Gaps", "Anchor_Story", "Notes", "Status", "Date_Updated"]
# Columns apply-scores may touch. NEVER: Status, Source, Agent, Location.
SCORE_COLS = ["Title", "Company", "JD", "Salary_Range", "Employment_Type",
              "Date_Posted", "Job_Track", "Fitness_Score", "Recruiter_Match",
              "Key_Gaps", "Anchor_Story", "Notes", "Date_Updated"]

# Schema migrations: column name -> ALTER statement (idempotent via `migrate`)
MIGRATIONS = {
    "Recruiter_Match":
        "ALTER TABLE Job_Tracker ADD COLUMN Recruiter_Match INTEGER",  # 0-100 recruiter-lens %
}


def die(msg, **extra):
    print(json.dumps({"ok": False, "error": msg, **extra}))
    sys.exit(1)


def load_config():
    path = os.path.join(REPO, "config.json")
    if not os.path.exists(path):
        die("config.json not found in repo root — copy config.example.json and edit it")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def connect(cfg, readonly=False):
    db = cfg["db_path"]
    if not os.path.exists(db):
        die(f"database not found: {db}")
    if readonly:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=15)
    else:
        con = sqlite3.connect(db, timeout=15)
        con.execute("PRAGMA busy_timeout=15000")
    return con


def integrity(con, quick=False):
    pragma = "quick_check" if quick else "integrity_check"
    return con.execute(f"PRAGMA {pragma}").fetchone()[0] == "ok"


# ---------- legacy lock-file protocol (transition only) ----------

def lock_path(cfg):
    return cfg["db_path"] + ".lock"


def acquire_lock(cfg):
    """Returns None on success, error string on failure. No-op unless enabled."""
    if not cfg.get("transition", {}).get("honor_lock_file"):
        return None
    lp = lock_path(cfg)
    try:
        if os.path.exists(lp) and os.path.getsize(lp) > 0:
            age = time.time() - os.path.getmtime(lp)
            if age < 1800:
                with open(lp, encoding="utf-8", errors="replace") as f:
                    return f"DB locked by: {f.read().strip() or '(unknown)'}"
            with open(lp, "w"):  # stale — clear
                pass
        with open(lp, "w", encoding="utf-8") as f:
            f.write(f"{WRITER} {datetime.now().isoformat(timespec='seconds')}")
        time.sleep(2)
        with open(lp, encoding="utf-8", errors="replace") as f:
            if WRITER not in f.read():
                return "lost lock race — another writer grabbed the lock"
    except OSError as e:
        return f"lock file error: {e}"
    return None


def release_lock(cfg):
    if not cfg.get("transition", {}).get("honor_lock_file"):
        return
    try:
        with open(lock_path(cfg), "w"):
            pass  # truncate, never delete (legacy convention)
    except OSError:
        pass


# ---------- helpers ----------

def read_jsonl(path):
    if not os.path.exists(path):
        die(f"input file not found: {path}")
    records = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                die(f"bad JSON on line {i} of {path}: {e}")
    return records


def norm(s):
    return (s or "").strip().lower()


def join_gaps(v):
    return "; ".join(v) if isinstance(v, list) else (v or "")


def write_guarded(cfg, fn):
    """Run fn(con) inside lock + integrity gates. fn returns the result dict."""
    err = acquire_lock(cfg)
    if err:
        die(err, locked=True)
    try:
        con = connect(cfg)
        try:
            if not integrity(con):
                die("integrity_check failed BEFORE write — nothing written; restore from backup")
            n0 = con.execute("SELECT COUNT(*) FROM Job_Tracker").fetchone()[0]
            result = fn(con)
            con.commit()
            if not integrity(con):
                die("integrity_check failed AFTER commit — inspect the DB")
            n1 = con.execute("SELECT COUNT(*) FROM Job_Tracker").fetchone()[0]
            result.update(ok=True, rows_before=n0, rows_after=n1, integrity="ok")
            return result
        finally:
            con.close()
    finally:
        release_lock(cfg)


# ---------- commands ----------

def cmd_list_pending(cfg, args):
    con = connect(cfg, readonly=True)
    try:
        rows = con.execute(
            """SELECT Job_ID, Title, Company, App_URL, Job_Track, Date_Created
               FROM Job_Tracker
               WHERE Fitness_Score IS NULL
                 AND App_URL IS NOT NULL AND App_URL != ''
                 AND (Status IS NULL OR Status IN ('', 'To Apply'))
               ORDER BY Job_ID
               LIMIT ?""", (args.limit,)).fetchall()
    finally:
        con.close()
    print(json.dumps({"ok": True, "pending": [
        dict(job_id=r[0], title=r[1], company=r[2], url=r[3], track=r[4], created=r[5])
        for r in rows]}))


def cmd_insert(cfg, args):
    records = read_jsonl(args.file)
    today = date.today().isoformat()

    def fn(con):
        existing_urls = {norm(r[0]) for r in con.execute(
            "SELECT App_URL FROM Job_Tracker WHERE App_URL IS NOT NULL AND App_URL != ''")}
        existing_tc = {(norm(r[0]), norm(r[1])) for r in con.execute(
            "SELECT Title, Company FROM Job_Tracker")}
        inserted, skipped = [], []
        for rec in records:
            row = {k[0].upper() + k[1:]: v for k, v in rec.items()}  # tolerate lower-case keys
            row = {("App_URL" if k.lower() in ("url", "app_url") else k): v for k, v in row.items()}
            title, company = rec.get("title") or rec.get("Title"), rec.get("company") or rec.get("Company")
            url = rec.get("url") or rec.get("app_url") or rec.get("App_URL") or ""
            if not title or not company:
                skipped.append({"reason": "missing title/company", "record": rec})
                continue
            if url and norm(url) in existing_urls:
                skipped.append({"reason": "duplicate App_URL", "title": title, "company": company})
                continue
            if (norm(title), norm(company)) in existing_tc:
                skipped.append({"reason": "duplicate Title+Company", "title": title, "company": company})
                continue
            vals = {
                "Source": rec.get("source"), "Agent": rec.get("agent"),
                "App_URL": url or None, "Other_App_URL": rec.get("other_url"),
                "Title": title, "Company": company, "Location": rec.get("location"),
                "JD": rec.get("jd"), "Salary_Range": rec.get("salary_range"),
                "Employment_Type": rec.get("employment_type"),
                "Date_Posted": rec.get("date_posted"),
                "HM_or_TA": rec.get("hiring_contact"), "Job_Track": rec.get("track"),
                "Fitness_Score": rec.get("fitness_score"),
                "Recruiter_Match": rec.get("recruiter_match"),
                "Key_Gaps": join_gaps(rec.get("key_gaps")) or None,
                "Anchor_Story": rec.get("anchor_story"), "Notes": rec.get("notes"),
                "Status": rec.get("status"), "Date_Updated": today,
            }
            vals = {k: v for k, v in vals.items() if v is not None and k in INSERT_COLS}
            cols = ", ".join(vals)
            q = ", ".join("?" * len(vals))
            cur = con.execute(f"INSERT INTO Job_Tracker ({cols}) VALUES ({q})", list(vals.values()))
            inserted.append({"job_id": cur.lastrowid, "title": title, "company": company})
            existing_urls.add(norm(url))
            existing_tc.add((norm(title), norm(company)))
        return {"action": "insert", "inserted": inserted, "skipped": skipped}

    print(json.dumps(write_guarded(cfg, fn)))


def cmd_apply_scores(cfg, args):
    records = read_jsonl(args.file)
    today = date.today().isoformat()

    def fn(con):
        updated, inserted, skipped = [], [], []
        for rec in records:
            url = rec.get("url") or ""
            if not url:
                skipped.append({"reason": "no url", "title": rec.get("job_title")})
                continue
            matches = con.execute(
                "SELECT Job_ID FROM Job_Tracker WHERE LOWER(TRIM(App_URL)) = ?",
                (norm(url),)).fetchall()
            vals = {
                "Title": rec.get("job_title"), "Company": rec.get("company"),
                "JD": rec.get("jd"), "Salary_Range": rec.get("salary_range"),
                "Employment_Type": rec.get("employment_type"),
                "Date_Posted": rec.get("date_posted"), "Job_Track": rec.get("track"),
                "Fitness_Score": rec.get("fitness_score"),
                "Recruiter_Match": rec.get("recruiter_match"),
                "Key_Gaps": join_gaps(rec.get("key_gaps")),
                "Anchor_Story": rec.get("anchor_story"), "Notes": rec.get("notes"),
                "Date_Updated": today,
            }
            # HM_or_TA only when the key is present — never blank an existing contact
            if "hiring_contact" in rec:
                vals["HM_or_TA"] = rec["hiring_contact"] or "Not listed"
            vals = {k: v for k, v in vals.items() if v is not None}
            if len(matches) == 1:
                sets = ", ".join(f"{k} = ?" for k in vals)
                con.execute(f"UPDATE Job_Tracker SET {sets} WHERE Job_ID = ?",
                            list(vals.values()) + [matches[0][0]])
                updated.append({"job_id": matches[0][0], "title": rec.get("job_title"),
                                "score": rec.get("fitness_score")})
            elif len(matches) == 0:
                vals["App_URL"] = url
                cols = ", ".join(vals)
                q = ", ".join("?" * len(vals))
                cur = con.execute(f"INSERT INTO Job_Tracker ({cols}) VALUES ({q})",
                                  list(vals.values()))
                inserted.append({"job_id": cur.lastrowid, "title": rec.get("job_title"),
                                 "score": rec.get("fitness_score")})
            else:
                skipped.append({"reason": f"ambiguous: {len(matches)} rows match url", "url": url})
        return {"action": "apply-scores", "updated": updated, "inserted": inserted, "skipped": skipped}

    print(json.dumps(write_guarded(cfg, fn)))


def cmd_update_status(cfg, args):
    records = read_jsonl(args.file)
    allowed = set(cfg.get("status_values", []))
    today = date.today().isoformat()

    def fn(con):
        updated, skipped = [], []
        for rec in records:
            status = rec.get("status")
            if allowed and status not in allowed:
                skipped.append({"reason": f"invalid status {status!r}", "record": rec})
                continue
            when = rec.get("date") or today
            if rec.get("job_id"):
                matches = [r[0] for r in con.execute(
                    "SELECT Job_ID FROM Job_Tracker WHERE Job_ID = ?", (rec["job_id"],))]
            else:
                matches = [r[0] for r in con.execute(
                    "SELECT Job_ID FROM Job_Tracker WHERE LOWER(TRIM(Title)) = ? AND LOWER(TRIM(Company)) = ?",
                    (norm(rec.get("title")), norm(rec.get("company"))))]
            if len(matches) != 1:
                skipped.append({"reason": f"{len(matches)} rows match — need exactly 1",
                                "title": rec.get("title"), "company": rec.get("company"),
                                "job_id": rec.get("job_id")})
                continue
            con.execute("UPDATE Job_Tracker SET Status = ?, Date_Updated = ? WHERE Job_ID = ?",
                        (status, when, matches[0]))
            updated.append({"job_id": matches[0], "status": status})
        return {"action": "update-status", "updated": updated, "skipped": skipped}

    print(json.dumps(write_guarded(cfg, fn)))


def cmd_check(cfg, args):
    con = connect(cfg, readonly=True)
    try:
        ok = integrity(con)
        n = con.execute("SELECT COUNT(*) FROM Job_Tracker").fetchone()[0]
        scored = con.execute("SELECT COUNT(*) FROM Job_Tracker WHERE Fitness_Score IS NOT NULL").fetchone()[0]
    finally:
        con.close()
    print(json.dumps({"ok": ok, "integrity": "ok" if ok else "FAILED",
                      "rows": n, "scored": scored, "db": cfg["db_path"]}))


def cmd_migrate(cfg, args):
    def fn(con):
        have = {r[1] for r in con.execute("PRAGMA table_info(Job_Tracker)")}
        added, present = [], []
        for col, stmt in MIGRATIONS.items():
            if col in have:
                present.append(col)
            else:
                con.execute(stmt)
                added.append(col)
        return {"action": "migrate", "added": added, "already_present": present}

    print(json.dumps(write_guarded(cfg, fn)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("list-pending"); sp.add_argument("--limit", type=int, default=500)
    for name in ("insert", "apply-scores", "update-status"):
        sp = sub.add_parser(name); sp.add_argument("--file", required=True)
    sub.add_parser("check")
    sub.add_parser("migrate")
    args = p.parse_args()
    cfg = load_config()
    {"list-pending": cmd_list_pending, "insert": cmd_insert,
     "apply-scores": cmd_apply_scores, "update-status": cmd_update_status,
     "check": cmd_check, "migrate": cmd_migrate}[args.cmd](cfg, args)


if __name__ == "__main__":
    main()
