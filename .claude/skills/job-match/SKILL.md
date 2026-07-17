---
name: job-match
description: Score ONE job posting (URL supplied ad-hoc) against the fitness rubric and resume, producing the same JSON the screening skill emits — Fitness_Score + Recruiter_Match. Use when asked to "score this job/URL". For batch scoring of pending rows, use the screening skill instead.
---

# Job Match — score a single posting on demand

Same rules as `.claude/skills/screening/SKILL.md` (source ladder, honesty rules, PROVISIONAL convention, both scores) applied to one URL. Read that skill first; this file only covers what differs.

## Inputs
- The job post URL, supplied in the request.
- `config.json` → `rubric_path`, `resume_path`. Re-read the rubric and re-extract the resume from disk EVERY run — never reuse prior text.

## Steps
1. Read the posting via the screening skill's source ladder.
2. Score per the rubric: `fitness_score` 1–5 (targeting lens) AND `recruiter_match` 0–100% (recruiter lens). The two are independent.
3. Output ONE JSON object, nothing around it — identical shape to the screening skill's per-job output: `job_title, company, url, jd, salary_range, employment_type, date_posted, hiring_contact, track, fitness_score, recruiter_match, key_gaps[], anchor_story, notes`.
4. Only if asked to log/track it: write the object as one line to a `tmp/` JSONL file and run `python scripts/job_db.py apply-scores --file <that file>` (inserts if the URL is new, updates if it exists).
