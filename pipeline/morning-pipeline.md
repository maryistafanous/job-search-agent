# Morning Job Pipeline

Run the complete morning job-search pipeline as ONE sequential run. Phases run strictly in order, never in parallel. All database access goes through `scripts/job_db.py` — never open the database any other way. If a phase fails, note it in the summary and CONTINUE with the remaining phases.

Before starting, read `config.json` (repo root) and `CLAUDE.md`.

Temporary working files: write ALL scratch files this run creates (extracted email text, resume text, score/status queues, helper .py scripts, etc.) into the `tmp/` subfolder (create it if missing) — never into the repo root, `applications/`, or `scripts/`.

Resume freshness: every scoring phase (2 and 3) must re-extract the resume text from `config.json → resume_path` directly from the file on disk at the start of that phase. Never reuse resume text from a previous run, a leftover scratch file, or memory. Log the resume file's modified timestamp in the summary.

## Phase 1 — Data entry
Follow `.claude/skills/data-entry/SKILL.md`: pull job-alert emails (and optional job-board search) into Job_Tracker. Inserts only, no scoring.

## Phase 2 — Target-company career scan
Follow `.claude/skills/career-scan/SKILL.md`: rotating subset of target companies' career sites; insert new matching roles (scored in-line). If the browser MCP is unavailable, skip gracefully exactly as the skill describes.

## Phase 3 — Screening
Follow `.claude/skills/screening/SKILL.md`: score all rows with an App_URL and no Fitness_Score. Every scored row gets BOTH Fitness_Score (1–5) and Recruiter_Match (0–100%).

## Phase 4 — Inbox sweep
Follow `.claude/skills/inbox-sweep/SKILL.md` and execute EVERY step. Phase 4 has THREE mandatory outputs and is NOT complete until all three are verified:
1. Gmail state: every A/B/C email is labeled, read, and archived (including ones with no tracker match — the label marks them processed). Only UNCLEAR emails stay unlabeled/unread in the inbox.
2. Tracker updates: confident single-match status changes applied via `job_db.py update-status`.
3. Summary draft: the Gmail draft exists.
VERIFY: re-run the sweep's searches and confirm zero unprocessed A/B/C candidates remain, and the draft was created.

## Phase 5 — Wrap up
Delete everything inside `tmp/` (keep the folder itself), plus any stray `tmp_*` or `_tmp_*` files accidentally created in the repo root — they are scratch, never needed after the run. Then run `python scripts/job_db.py check` and confirm integrity is ok. The live dashboard reads the database directly, so no rebuild step is needed — just note the current row count and high-fit "To Apply" count in the summary.

Finish with ONE combined summary: rows inserted (phases 1–2), jobs scored + score distribution + best roles (phase 3), status changes and emails labeled/archived (phase 4), integrity/row count (phase 5), and any phase skipped or failed and why.

Note: if this run starts late because the machine was asleep, run all phases normally.
