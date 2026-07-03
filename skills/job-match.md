---
name: job-match
description: >-
  Assess a single job posting against the user's resume and fitness rubric and
  return a structured JSON verdict. Use whenever the user shares a job post URL
  and wants it scored, or when the batch-screening workflow processes a job.
---

# Job Match (generic)

Score ONE job posting against the user's rubric and resume. Output one JSON object,
clean and consistent, ready for the tracker.

## Inputs

1. **Job post URL** — supplied per run.
2. **Fitness rubric** — `fitness-rubric.md` (from the template). Re-read EVERY run; it changes.
3. **Resume(s)** — per the rubric's track→resume mapping. Score against exactly one track.

If a file is missing, say so plainly; never guess its contents.

## Step 1 — Extract job facts (honesty rules)

Report only what the posting states. Never invent or infer from outside the page.

- **JD:** 1–2 sentence summary.
- **Salary:** verbatim if stated, else the string "Unlisted". Market estimates are NOT posting salary.
- **Employment type:** as stated, else null.
- **Date posted:** ISO date; estimating from "N days ago" is fine, no flag needed.
- **Hiring contact:** "Name, Title" if a named person is shown, else null.

When the page can't be fully read (login wall, throttling): extract what is visible,
set unknown fields to null/"Unlisted", and record the limitation — plus the URL
actually read — in notes. If scoring proceeded on partial information, START the
notes field with "PROVISIONAL:" and state what would change the score.

## Step 2 — Score against the rubric

1. Pick the track from the job title; read that track's resume only.
2. Fitness score 1–5 per the rubric's bands.
3. Red-flag cap: a rubric red flag caps the score ONLY when it is a core/required
   qualification. Under "preferred / nice to have" it is a key gap, not a cap.
4. Key gaps: short and concrete. Never list a minimum the user already exceeds.
5. Anchor story: the single best-matching story from the rubric; "N/A" if none fits,
   with a note describing what kind of story WOULD anchor this role.

## Output

One JSON object, nothing around it:

```json
{
  "job_title": "", "company": "", "url": "", "jd": "",
  "salary_range": "string or Unlisted", "employment_type": "string or null",
  "date_posted": "YYYY-MM-DD", "hiring_contact": "Name, Title or null",
  "track": "", "fitness_score": 0, "key_gaps": [], "anchor_story": "", "notes": ""
}
```
