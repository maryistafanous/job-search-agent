---
name: batch-job-screening
description: >-
  Batch-screen pending rows in the Job_Tracker table: every row with an App_URL
  but no Fitness_Score gets read, scored via job-match, and written back.
  Handles LinkedIn throttling with employer-site fallback and provisional scores.
---

# Batch Job Screening (generic)

Work through all unscored tracker rows, one job at a time, saving after each.

## Flow

```
read rubric + resumes -> list pending rows -> FOR EACH job:
  read posting (LinkedIn -> employer site fallback) -> score (job-match)
  -> queue result -> flush queued scores to DB in small batches
-> verify DB integrity -> close browser tabs
```

Confirm scope first (how many jobs, what priority order) — a full backlog can be 70+ rows.

## Reading postings — the fallback ladder

1. **LinkedIn (user's own logged-in browser).** Wait ~5s, scroll down and back up
   (the description lazy-loads). The header (title/company/salary chip/date) always
   renders; after a few rapid loads LinkedIn soft-throttles the description BODY
   (grey skeleton bars). Don't fight it — pace loads, and switch to:
2. **Employer's own posting.** Web-search "<Company>" "<Title>" job description
   (bias with greenhouse/careers). Greenhouse/Workday/Lever boards are server-rendered,
   fetch cleanly, and usually state salary. Record BOTH URLs in Notes.
3. **No public JD** (confidential/recruiter posts): score PROVISIONALLY from the
   title + header facts, flag in Notes, or skip per user preference.

## Writing to the database — safety rules

- De-dupe on App_URL: update in place, never duplicate.
- Never overwrite a Status a human already set.
- Queue scores locally and flush in small batches. If the DB sits on a mount or
  synced folder (Dropbox/OneDrive/network share), NEVER update it in place:
  copy out, integrity-check (PRAGMA integrity_check = ok) BEFORE and AFTER applying
  changes, back up the original, copy back, then re-read to confirm the write stuck.
- If any other writer may touch the DB (a second scheduled agent, manual edits),
  use a lock file: check-acquire-release around the DB phase only.

## Scoring

Exactly per `job-match.md` — including the red-flag cap rule, honesty rules,
and the PROVISIONAL convention.
