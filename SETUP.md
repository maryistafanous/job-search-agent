# Setup

Time: ~30–45 minutes. Prerequisites: a Claude subscription with Cowork (or
Claude Code), and an email account receiving job alerts.

## 1. Create your job-search folder

Make a folder Claude can access (in Cowork: connect it as your project folder).
Copy into it:

- `db/schema.sql` → then create the tracker:
  ask Claude to "create job_search.db from schema.sql", or run
  `sqlite3 job_search.db < schema.sql`
- `templates/fitness-rubric-template.md` → rename to `fitness-rubric.md` and
  **fill it in completely** (this is 80% of result quality — be specific about
  red flags and anchor stories)
- `templates/search-profile-template.md` → rename to `search-profile.md`, fill in
- `skills/` → keep both skill files in the folder (or install as Claude skills)
- Your resume PDF(s)

## 2. Set up job alerts

On LinkedIn and Indeed, create saved searches for your target titles/locations
and enable daily email alerts to the address Claude can read.

## 3. Connect Claude to your email

In Cowork, connect the Gmail connector (Settings → Connectors) so the data-entry
agent can read alert emails.

## 4. Create the scheduled tasks

Follow `scheduled-tasks.md` — two daily tasks, 15+ minutes apart.

## 5. First run — supervised

Before trusting the schedule, run each step manually once in a chat session:

1. "Run the data-entry task now" — check rows appear in the tracker.
2. "Score the 5 pending jobs" — read the scores and gaps critically. If they feel
   wrong, fix the RUBRIC (not the scores) and re-run; the rubric is the dial.
3. Check the summary output format works for you.

## 6. Daily use

Read the morning summary; review roles scored 4–5; set Status as you apply.
Re-tune the rubric weekly — it should evolve with what you learn from interviews.

## Troubleshooting

- **LinkedIn descriptions won't load:** normal throttling; the agent falls back to
  employer career sites. Don't reload repeatedly.
- **"disk I/O error" / DB oddities on synced folders:** see the DB safety rules in
  `skills/batch-job-screening.md` (copy-out / verify / copy-back, lock file).
- **Scores feel off:** the rubric is underspecified. Add explicit red flags,
  non-red-flags, and baseline facts ("never list X as a gap").
