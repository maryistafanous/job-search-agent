---
name: screening
description: Score every pending Job_Tracker row (App_URL present, no Fitness_Score) against the fitness rubric and matching resume, then write scores back via job_db.py. Use when asked to "score pending jobs", "run screening", or as Phase 3 of the morning pipeline.
---

# Screening — score pending jobs against the rubric

Turn un-scored `Job_Tracker` rows into fully-scored entries: read each posting, score it against the rubric and the matching resume track, queue results locally, flush in small batches.

## Inputs (paths from `config.json`)
- `rubric_path` — the fitness rubric. THE single source of truth for scoring. Re-read every run; it changes.
- `resume_path` — THE resume. It may be .docx or .pdf; if the Read tool cannot parse it, extract the text with Python (a .docx is a zip — read `word/document.xml` and strip tags). **Freshness rule: re-extract from `resume_path` at the START of every run, directly from the file on disk — never reuse text from a previous run, a scratch file, or memory of its contents.** Log the resume file's modified timestamp in the run summary so a stale resume is visible. Extract once per run, reuse within the run only.

## Step 1 — Find pending jobs

    python scripts/job_db.py list-pending

Pending = has App_URL, no Fitness_Score, and no human-set Status. Never re-score rows that already have a Fitness_Score unless explicitly asked (e.g. after a rubric change).

## Step 2 — Read each posting (source ladder)

0. **Job-board MCP connector first (e.g. Indeed), if connected AND the row carries the connector's internal job id** (e.g. `indeed_job_id:<id>` in Notes). `get_job_details` needs that internal id — redirect shortlinks (to.indeed.com/...) will be rejected, and searching by title to recover an id is unreliable; don't attempt either, just drop to rung 1. When the id exists, verify the returned posting matches the row's Title+Company before trusting it.
1. **WebFetch the posting URL.** Company career pages and ATS boards (Greenhouse / Lever / Workday) are usually server-rendered and fetch cleanly, including salary.
2. **LinkedIn URLs:** LinkedIn aggressively limits automated access — the header (title, company, salary chip, posted date) may load while the description body does not. The FIRST time a LinkedIn body fails, treat LinkedIn as throttled for the REST of the batch: go company-site-first for every remaining job. Do not retry LinkedIn bodies job after job.
3. **Company-site fallback:** WebSearch `"<Company>" "<Title>" job description requirements` (bias with `greenhouse`, `careers`, or `salary`). Best sources in order: the company's ATS board, the company careers page, then aggregators. Record BOTH links in notes: the original App_URL and the source actually read.
4. **Browser MCP (claude-in-chrome or Playwright), if connected** — for pages that only render with JavaScript.
5. **No public JD** (confidential posting, staffing firm, tiny startup): score provisionally from the title + company context using whatever header facts are available.

## Step 3 — Score (rubric rules)

1. **Score against the single resume** (`resume_path`) and the rubric. For the output's `track` field, record the role family the rubric defines (e.g. Engineering Leadership / Product / Portfolio) — it fills the Job_Track column.
2. **Fitness score 1–5** per the rubric bands.
2b. **Recruiter_Match 0–100%** per the rubric's recruiter-lens section: re-score the same job as the posting's recruiter reading the resume cold — deductions for domain gaps, title mismatch, missing keywords, seniority direction. The two scores are independent; do NOT let one anchor the other.
3. **Red-flag cap:** a rubric red flag caps fitness at 2 ONLY when it is a core/required qualification. The same item under "preferred / nice to have" is a key gap, NOT a cap. Always check required vs preferred.
4. **Score 1 = clear non-fit:** wrong level/scope or a disqualifying core red flag. A red flag that is only "preferred" is a 2, not a 1.
5. **Key gaps:** short, concrete; never list a minimum the candidate already exceeds.
6. **Anchor story:** the single best-matching ownership story from the rubric; "N/A" if none fits (and say in notes what kind would).
7. **Honesty rules — never fabricate:** salary verbatim only if the posting states it, else "Unlisted" (market estimates are NOT posting salary); date_posted always ISO (estimating from "N days ago" is fine); hiring contact null unless named; company industry context is NOT a domain requirement unless the JD requires that domain depth.
8. **Provisional convention:** when the JD couldn't be fully read, START notes with `PROVISIONAL:` and state what's missing and what would change the score.

Output per job — one JSON object: `job_title, company, url, jd, salary_range, employment_type, date_posted, hiring_contact, track, fitness_score, recruiter_match, key_gaps[], anchor_story, notes`. `url` MUST be the row's App_URL exactly (it is the match key), even when the JD was read elsewhere.

## Step 4 — Queue and flush

- Append each result as one line to a local JSONL queue file the moment it exists.
- Every ~5 jobs and once at the end:

      python scripts/job_db.py apply-scores --file <queue>.jsonl

  On success, truncate the queue. On failure or `locked`, KEEP the queue file (it is the recovery record) and surface the error. The script matches rows by App_URL (1 match → update, 0 → insert, >1 → skip ambiguous) and never touches Status, Source, Agent, or Location.

## Step 5 — Verify

    python scripts/job_db.py check

Never end the run with a non-empty queue file unless a flush failed — then report the queue path. Summarize: jobs scored, score distribution, provisional count, best roles.
