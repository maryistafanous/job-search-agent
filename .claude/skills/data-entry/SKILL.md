---
name: data-entry
description: Pull job-alert emails (LinkedIn) and optional job-board searches into the Job_Tracker table. Data entry only — no scoring. Use when asked to "pull new jobs", "run data entry", or as Phase 1 of the morning pipeline.
---

# Data Entry — job-alert emails → Job_Tracker

Pull new LinkedIn job-alert emails from Gmail and APPEND qualifying postings to `Job_Tracker`. DATA ENTRY ONLY — do NOT score anything; the screening skill does that separately.

## Inputs
- `config.json` (repo root): `gmail.alert_label`, `search_profile_path`, `db_path`.
- The search profile (markdown at `search_profile_path`): defines TARGET ROLES, ALERT-LEVEL EXCLUSIONS, CARD-LEVEL EXCLUSIONS, and location preferences. Re-read it every run — it changes.

## Steps

1. Search Gmail for alert emails newer than 1 day using the label from `config.json` (query form: `label:<alert_label> newer_than:1d` — use the hyphenated display-name form of the label, not a raw label ID).

2. For each matching message:
   a. The body's first line is "Your job alert for <name> ...". Extract <name>, title-case it — this is the Search Agent value for every posting in this email.
   b. Apply the search profile's ALERT-LEVEL EXCLUSIONS to <name>; on match, skip the whole email.
   c. Split the body into job cards on the divider line of dashes. Each real card: Title \ Company \ Location \ [optional badge lines] \ "View job: <tracking URL>". Ignore footer blocks.
   d. Canonical App_URL: take the URL after "View job:", extract the job ID digits from `/jobs/view/<jobID>`, normalize to `https://www.linkedin.com/jobs/view/<jobID>/` (strip query strings and the `/comm` segment).
   e. Apply CARD-LEVEL EXCLUSIONS. Collect survivors in memory — no DB writes yet.

3. OPTIONAL job-board search (time-boxed ~10 min; skip gracefully if blocked): prefer a job-board MCP connector (e.g. Indeed `search_jobs`) when connected; otherwise search the boards listed in the search profile for recent postings (< 1 week) matching the target roles and location preferences. Apply CARD-LEVEL EXCLUSIONS. Source = the board name. When a job comes from the connector, put its internal job id in `notes` as `indeed_job_id:<id>` and use the posting's canonical URL (not a to.indeed.com redirect shortlink) as `url` when the connector provides one — this lets the screening skill fetch the full JD through the connector later.

4. SINGLE DB WRITE PASS — write the collected jobs as JSONL (one object per line: `title, company, location, url, source, agent, notes`; set `agent` to "data-entry") to a temp file, then:

       python scripts/job_db.py insert --file <temp>.jsonl

   The script de-duplicates on App_URL and Title+Company, runs integrity checks, and honors the transition lock file if configured. Check its JSON output; if it reports `locked`, finish the run and list the collected-but-unwritten jobs in the summary so they can be re-added later.

5. Summarize: rows added per Search Agent and per source, skip counts by reason, and anything skipped (including a locked DB write).
