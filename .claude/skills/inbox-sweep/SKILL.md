---
name: inbox-sweep
description: Triage job-application emails in Gmail (labels = processing state), label/archive them, update Job_Tracker statuses, and draft a summary email. Use when asked to "sweep the inbox", "process application emails", or as Phase 4 of the morning pipeline.
---

# Inbox Sweep — application emails → Gmail labels + tracker statuses

Each run is fresh with no memory of prior runs. `config.json` supplies `owner_email` and `gmail.processed_labels` (application / update / interview label names).

## Core design principles
- **Gmail labels are the processing state.** An email is "processed" iff it carries one of the processed labels AND is archived. No timestamp window — every run is idempotent.
- **Classify from the BODY with quoted evidence.** Never from a subject line.
- **Batch all DB writes at the end** through `scripts/job_db.py`.

## 1. Find candidates
Union of Gmail searches, last 3 days, in inbox: from LinkedIn jobs-noreply; subject application/applying/interview/candidacy; body phrases ("your application", "we received", "thanks for applying", "not moving forward", "other candidates", "position has been filled", "schedule an interview"). Skip threads already carrying a processed label. Ignore newsletters, job alerts, recruiter cold-outreach, marketing.

## 2. Classify — body required, evidence required
Fetch the full body BEFORE deciding. Assign exactly one category with a short verbatim quote as justification; no quotable deciding phrase → UNCLEAR.

- A) APPLICATION RECEIVED — received/submitted confirmation, no rejection language.
- B) APP UPDATE (negative) — not moving forward / other candidates / filled / closed / on hold / "unfortunately".
- C) INTERVIEW REQUEST — invites scheduling or attending an interview/assessment.
- D) UNCLEAR — anything else, including mixed wording.

CRITICAL: LinkedIn uses the IDENTICAL subject "Your application to <role> at <company>" for BOTH confirmations (A) and rejections (B). Read every LinkedIn body: "Your update from <Company>" with tracking links containing `email_jobs_application_rejected_01` = rejection (B). "Your application was viewed by <Company>" = informational → D. ANY rejection phrase makes it B even if it also says thanks for applying.

For A/B/C extract JOB TITLE and COMPANY. For D: no label, no archive, leave unread; list in the summary.

## 3. Label and archive (A/B/C only)
Ensure the three processed labels exist (create missing). A → application label; B → update label; C → interview label. Apply label, mark read, archive. The label MUST succeed before archiving — if labeling fails, leave the email untouched so the next run retries.

## 4. Queue tracker updates
For each A/B/C email, queue: A → "Applied"; B → "Rejected"; C → "Interview Requested"; date = email received date (YYYY-MM-DD). Status is EXPECTED to advance (empty → Applied → Interview Requested / Rejected) — the email reflects the newer state, so overwrite. Only skip when the Title+Company match to the tracker is ambiguous or missing — never write on a fuzzy multi-row match.

## 5. Apply updates in ONE batch
Write the queue as JSONL ({"title","company","status","date"} per line), then:

    python scripts/job_db.py update-status --file <queue>.jsonl

The script requires exactly one row match per update (else it skips and reports), validates statuses, and honors the transition lock file. If it reports `locked`, list the unapplied updates in the summary email — the emails are already labeled, so a future run will NOT retry them; the summary is the record. Zero queued updates → skip this step entirely.

## 6. Draft a summary email
Create a DRAFT (never send) to `owner_email`, subject "Job application updates — <today>", body with counts (Interviews Requested / New Applications / Rejected / Needs manual review) and per-category "Title — Company" lists ("None" when empty). Under "Needs manual review": each UNCLEAR email (sender + subject + why). Under "Skipped tracker updates": labeled emails whose row couldn't be updated, including updates skipped because the DB was locked. Create the draft even when all counts are 0.
