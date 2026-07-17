# CLAUDE.md — Job-Search Agent

An agentic job-search pipeline: data entry from job-alert emails, target-company career scans, rubric-based screening, inbox sweeps, and a live dashboard, all tracked in a local SQLite database.

## Configuration

`config.json` in the repo root (copy from `config.example.json`) supplies every personal/machine-specific value: owner name/email, database path, resume paths, rubric path, search profile, target-companies CSV, Gmail label names, allowed status values. Skills and scripts MUST read paths from it — never hard-code them.

## Database rules

- Database: SQLite at `config.json → db_path`, table `Job_Tracker` (schema: `db/schema.sql`).
- **ALL writes go through `scripts/job_db.py`** (`insert`, `apply-scores`, `update-status`). It uses parameterized SQL, busy_timeout, integrity checks before and after every write, and de-duplication. Never write SQL to the DB any other way; never edit the DB file with ad-hoc scripts.
- Reads may use `job_db.py` (`list-pending`, `check`) or read-only SQLite connections (`mode=ro`).
- Only update a row's Status on a confident, unambiguous single match (job_db.py enforces exactly-one-row matching). Status follows the application lifecycle and is EXPECTED to advance (empty → Applied → Interview Requested / Rejected); write the newest known state, never preserve a stale one.
- Honesty rules for job data: never fabricate salaries (verbatim or "Unlisted"), dates (ISO, estimates from relative dates OK), or contacts (null unless named). Flag partially-read postings with `PROVISIONAL:` in Notes.

### Transition mode (temporary)

While `config.json → transition.honor_lock_file` is `true`, a legacy pipeline may also write this database using a lock-file protocol. `job_db.py` automatically honors it: it aborts writes when `<db>.lock` is held fresh (<30 min), acquires it around its own writes, and releases by truncating to 0 (never deleting). If a write reports `locked`, report the unwritten changes in the run summary — do NOT retry by writing directly. After full cutover this flag goes to `false` and the lock file is retired.

## Components

- `pipeline/morning-pipeline.md` — the daily sequenced run (data entry → career scan → screening → inbox sweep → verify). Triggered by `scripts/run-pipeline.bat` (manually or via Windows Task Scheduler).
- `.claude/skills/` — the individual pipeline skills; each can also run standalone.
- `dashboard/dashboard_api.py` — local FastAPI dashboard (`scripts/start-dashboard.bat`, then http://127.0.0.1:<dashboard_port>/). Reads the DB directly; status changes made in the UI are written with the same safety rules.
- `db/schema.sql` — create a fresh database with `sqlite3 job_search.db < db/schema.sql`.
- `scripts/backup_db.py` — timestamped DB backup with retention (run-pipeline.bat calls it before each run). `scripts/salvage_sqlite.py` — last-resort recovery: parses table b-tree pages directly when SQLite can't open the file. Recovery order: stop writing, salvage, restore newest backup, re-apply diffs via job_db.py.
- `templates/` — starting points for the personal files (rubric, search profile, target companies) that live OUTSIDE the repo.

## Conventions

- The rubric file is the single source of truth for scoring — re-read it every run.
- Gmail labels are the processing state for the inbox sweep — never re-process a labeled email.
- Personal data (database, resumes, filled-in rubric/profile, config.json) never gets committed; `.gitignore` already covers it.
