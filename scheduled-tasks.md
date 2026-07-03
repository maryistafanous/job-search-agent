# Scheduled Task Prompts

Create these two daily tasks in Claude (Cowork: just ask Claude to "schedule a
task"; both must reference your folder). Sequence them with enough spacing that one finishes before the next starts (they share the database; the lock file makes overlap safe, but an overlapping run skips its write).

## Task 0 — The morning pipeline (recommended: this is the only scheduled task you need)

> Run my complete morning job-search pipeline as ONE sequential run. The phases
> below MUST run strictly in order, one at a time — never in parallel. All
> database writes follow the DB safety rules (lock file, copy-out/verify/
> copy-back). Wait 2-3 minutes between phases that write to the database. If a
> phase fails, note it in the summary and CONTINUE with the remaining phases
> (releasing the lock first if held).
> PHASE 1 — Data entry (Task 1 below). PHASE 2 — Career scan (Task 2 below).
> PHASE 3 — Screening + dashboard rebuild (Task 3 below). PHASE 4 — Inbox sweep
> (Task 4 below). Finish with ONE combined summary across all phases.
> If this run starts late because the computer was asleep, run all phases
> normally — order matters, start time does not.

Why one task instead of four: scheduled tasks only run while the computer is
awake. With four separate tasks, a laptop that slept through the morning fires
them all at once on wake — colliding on the database. One sequenced task fires
once, in order, whenever the machine wakes. Collisions become impossible by
construction. Keep the individual tasks below as manual spares.

## Task 1 — Data entry (daily, e.g. 7:05 AM)

> Read my unread job-alert emails from LinkedIn and Indeed. For each job in them,
> check whether its application URL already exists in Job_Tracker in job_search.db
> (folder: <your folder>). Insert only new rows with Source, App_URL, Title,
> Company, Location, and today's Date_Created — do NOT score anything. Follow the
> DB safety rules in skills/batch-job-screening.md. Finish with a summary:
> N alerts read, N new rows, N duplicates skipped.

## Task 2 — Career scan (daily or weekly, e.g. 7:15 AM)

> Run the company-career-scan (skills/company-career-scan.md) on
> target-companies.csv in <your folder>: check the least-recently-scanned
> companies for openings matching my role families and filters, insert new
> matches into Job_Tracker with Source "Career Scan", update the scan-state
> file, and summarize: companies checked, new roles found, best match.

## Task 3 — Screening (daily, e.g. 7:30 AM)

> Run the batch-job-screening workflow (skills/batch-job-screening.md) on
> job_search.db in <your folder>: score every row that has an App_URL but no
> Fitness_Score against fitness-rubric.md and my resume(s) per the rubric's track
> mapping. Follow the honesty and PROVISIONAL rules. Finish with a summary table:
> jobs scored, score distribution, and the highest-fit roles.

## Task 4 — Inbox sweep (daily, e.g. 7:45 AM, or on demand)

> Read my job-application-related emails since <date>. For each one that clearly
> matches a single Title+Company row in Job_Tracker, update Status
> (Applied / Interviewing / Rejected / Offer) and Date_Updated. Never downgrade
> or overwrite an existing Status without an unambiguous match. Summarize changes.
