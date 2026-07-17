---
name: resume-tailor
description: Generate an ATS-optimized resume variant (and optional cover-letter draft) for a specific high-fit job in the tracker. Use on demand — "prepare application kit for Job_ID N" or "kit N".
---

# Resume Tailor

Turn a scored tracker row into an application kit: an ATS-friendly resume tailored to that posting, plus an optional cover-letter draft.

## Why on-demand, not automatic
Screening scores dozens of roles; you apply to a few. Generating resumes only for chosen roles keeps quality high and gives a review step before anything represents you.

## Inputs
- The tracker row (read-only query on the DB from `config.json → db_path`): JD summary, Key_Gaps, Anchor_Story, Notes (incl. the URL actually read)
- The full job description — re-fetch it for exact wording
- The resume at `config.json → resume_path` (see the screening skill for .docx text extraction)
- The rubric's metrics bank and experience baseline (`rubric_path`)

## Steps
1. **Re-read the posting** and extract: exact title, top 8–12 requirement keywords/phrases (as literally written), and the required vs preferred split.
2. **Keyword alignment — honestly.** Mirror the posting's terminology wherever real experience matches. NEVER add skills or experience the base resume doesn't support. Tailoring is emphasis and vocabulary, not fiction.
3. **Reorder and reweight:** lead the professional summary with this role's emphasis; promote the 2–3 most relevant bullets in each job to the top; swap in the metrics that matter to this posting; address Key_Gaps by emphasizing the nearest real experience.
4. **Weave in the Anchor_Story** prominently — it was chosen for this role.
5. **ATS formatting rules:** single column; standard section headings (Professional Experience, Education, Skills); no tables, text boxes, images, or contact info in headers/footers; standard fonts; .docx output; file name "<Name> - <Title> - <Company>.docx"; spell out acronyms once.
6. **Cover letter (optional):** 3 short paragraphs — the hook (why this company), the proof (anchor story with metrics), the close. No restating the resume.
7. **Log it:** read the row's current Notes, then write back Notes + "; Kit generated <date>" through the single write path — a one-line JSONL `{"url": "<App_URL>", "notes": "<merged notes>"}` via `python scripts/job_db.py apply-scores --file <f>.jsonl` (it updates only the provided fields).

## Output
Both files saved to an `applications/<Company>/` folder in the data directory, plus a 5-line summary of what was emphasized and which keywords were mirrored — so the tailoring can be sanity-checked in 30 seconds.

Scratch files (helper .py generators, notes .jsonl, extracted JD text, etc.) go in the repo `tmp/` folder ONLY — never in `applications/` (final kit folders only) or `scripts/` or the repo root. The pipeline clears `tmp/` before and after every run.
