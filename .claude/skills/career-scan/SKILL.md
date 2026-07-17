---
name: career-scan
description: Scan target companies' own career sites (rotating subset per run) for matching roles, score them in-line, and insert into Job_Tracker. Use when asked to "scan career sites" or as Phase 2 of the morning pipeline.
---

# Career Scan — target-company career sites → Job_Tracker

Proactively check a rotating subset of target companies' career pages — catching roles that never hit the job boards.

## Inputs (paths from `config.json`)
- `target_companies_csv` — columns include Company Name, Priority Level, Remote/Hybrid Signal, Career Site Link.
- `scan_state_path` — JSON mapping company name → last_scanned ISO date. Create if missing (treat all as never scanned).
- `rubric_path` + `resume_path` — for in-line scoring (single resume; see the screening skill for .docx extraction).
- The search profile (`search_profile_path`) — target roles and location rules.

## Steps

1. Pick 15 companies with the oldest (or missing) last_scanned. Ties: higher Priority first, then CSV order.

2. Read each company's career site with the **Playwright MCP** (headless Chrome — this is the browser the unattended pipeline uses). Do NOT use `claude-in-chrome` here: it drives a real Chrome through the extension and only works in an interactive session, so it will stall a headless run. If the Playwright MCP is not connected this run, DO NOT substitute LinkedIn/board searches: record "browser not connected — career scan skipped", leave the scan state UNCHANGED (so these companies are retried next run), and finish gracefully.
   - Navigate to the Career Site Link, let it render, extract the listings text.
   - Many pages embed an ATS (Greenhouse / Lever / Workday / iCIMS). If no inline listings, follow the "View openings"-type link to the ATS board. WebSearch may be used to DISCOVER the ATS board URL; read the listings through the browser (career/ATS pages are usually JS-rendered).
   - If a site can't be read, record "could not read site" and move on.

   **Timeout & budget (hard rules — a single slow site must never stall the run):**
   - The Playwright MCP is launched with `--timeout-navigation 45000 --timeout-action 15000`, so any single `browser_navigate`/click returns (with an error) within ~45s instead of hanging. Do NOT retry a page more than once. If a navigate errors or the snapshot is empty, record "could not read site (timeout)" and move to the next company.
   - iCIMS/Workday deep-links to an individual job page are the usual culprit: their iframes can keep the page from ever settling. Prefer reading the ATS **board/search** page (the listing index) and scoring from the summary text; only open an individual job page if you can't get title + enough JD from the board, and never open more than 2 such deep-links per company.
   - Whole-phase wall-clock budget: **20 minutes** from the start of career-scan. Note the start time. Before navigating to each new company, check elapsed time; once the budget is exceeded, STOP scanning, mark the remaining companies as NOT visited (leave their scan state unchanged so they're retried next run), and proceed to the DB write + summary with whatever was collected.

3. Keep a job only if ALL of: matches a target role (close variants OK); posted within 30 days (no date shown → keep, note "date not listed"); location matches the search profile's rules; full-time (assume if unspecified).
   Aim for 20–30 qualifying jobs per run; never pad with weak matches.

4. Score each qualifying job IN-LINE while its JD is loaded, following the screening skill's scoring rules (rubric bands, red-flag cap, recruiter-lens Recruiter_Match, honesty rules, and the resume-freshness rule — re-extract the resume from `resume_path` at run start; never reuse a prior run's text). Queue rows locally as JSONL: `title, company, location, url, jd, salary_range, employment_type, date_posted, hiring_contact, track, fitness_score, recruiter_match, key_gaps, anchor_story, notes`, plus `source: "Company Site"`, `agent: "career-scan"`. No DB writes during scanning.

5. Single DB write at the end:

       python scripts/job_db.py insert --file <temp>.jsonl

   Dedup (App_URL, Title+Company) is handled by the script; existing rows are never overwritten. If it reports `locked`, list the queued jobs in the summary instead.

6. Update the scan state: set last_scanned = today ONLY for companies actually visited (including "could not read site" ones); never advance companies skipped because the browser was unavailable. Summarize: companies scanned, unreadable sites, jobs found/inserted/deduped, score distribution.
