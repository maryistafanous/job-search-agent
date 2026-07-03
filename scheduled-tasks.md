# Scheduled Task Prompts

Create these two daily tasks in Claude (Cowork: just ask Claude to "schedule a
task"; both must reference your folder). Space them 15+ minutes apart.

## Task 1 — Data entry (daily, e.g. 7:00 AM)

> Read my unread job-alert emails from LinkedIn and Indeed. For each job in them,
> check whether its application URL already exists in Job_Tracker in job_search.db
> (folder: <your folder>). Insert only new rows with Source, App_URL, Title,
> Company, Location, and today's Date_Created — do NOT score anything. Follow the
> DB safety rules in skills/batch-job-screening.md. Finish with a summary:
> N alerts read, N new rows, N duplicates skipped.

## Task 2 — Screening (daily, e.g. 8:30 AM)

> Run the batch-job-screening workflow (skills/batch-job-screening.md) on
> job_search.db in <your folder>: score every row that has an App_URL but no
> Fitness_Score against fitness-rubric.md and my resume(s) per the rubric's track
> mapping. Follow the honesty and PROVISIONAL rules. Finish with a summary table:
> jobs scored, score distribution, and the highest-fit roles.

## Optional Task 3 — Inbox sweep (on demand or weekly)

> Read my job-application-related emails since <date>. For each one that clearly
> matches a single Title+Company row in Job_Tracker, update Status
> (Applied / Interviewing / Rejected / Offer) and Date_Updated. Never downgrade
> or overwrite an existing Status without an unambiguous match. Summarize changes.
