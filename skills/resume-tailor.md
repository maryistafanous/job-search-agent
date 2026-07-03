---
name: resume-tailor
description: >-
  Generate an ATS-optimized resume variant (and optional cover-letter draft) for
  a specific high-fit job in the tracker. Runs on demand ("prepare application
  kit for Job_ID N"), or can be offered automatically for roles scoring 5.
---

# Resume Tailor (generic)

Turn a scored tracker row into an application kit: an ATS-friendly resume
tailored to that posting, plus an optional cover-letter draft.

## Why on-demand, not automatic

Screening scores dozens of roles; you apply to a few. Generating resumes only
for roles you choose keeps quality high and gives you a review step before
anything represents you. (Optional: have the screening summary end with
"say 'kit N' to prepare an application kit for any of these.")

## Inputs (all already in the system)

- The tracker row: JD summary, Key_Gaps, Anchor_Story, Notes (incl. the URL of
  the full posting actually read)
- The full job description — re-fetch it for exact wording
- The track's base resume
- The rubric's metrics bank and experience baseline

## Steps

1. **Re-read the posting** and extract: exact title, top 8-12 requirement
   keywords/phrases (as literally written), and required vs preferred split.
2. **Keyword alignment — honestly.** Mirror the posting's terminology wherever
   the user's real experience matches (e.g., their "release management" =
   posting's "delivery governance"). NEVER add skills or experience the base
   resume doesn't support. Tailoring is emphasis and vocabulary, not fiction.
3. **Reorder and reweight:** lead the professional summary with this role's
   emphasis; promote the 2-3 most relevant bullets in each job to the top;
   swap in the metrics that matter to this posting; address Key_Gaps by
   emphasizing the nearest real experience.
4. **Weave in the Anchor_Story** prominently — it was chosen for this role.
5. **ATS formatting rules:** single column; standard section headings
   (Professional Experience, Education, Skills); no tables, text boxes, images,
   headers/footers with contact info, or graphics; standard fonts; .docx output;
   file name "<Name> - <Title> - <Company>.docx"; spell out acronyms once.
6. **Cover letter (optional):** 3 short paragraphs — the hook (why this company),
   the proof (anchor story with metrics), the close. No restating the resume.
7. **Log it:** append "Kit generated <date>" to the row's Notes.

## Output

Both files saved to an `applications/<Company>/` folder, plus a 5-line summary
of what was emphasized and which keywords were mirrored — so the user can
sanity-check the tailoring in 30 seconds.
