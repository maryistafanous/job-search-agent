# Publishing to GitHub + GitHub Pages

Goal: a public repo plus a live demo link for your resume, e.g.
`https://<username>.github.io/job-search-agent/`

## One-time (about 20 minutes, all in the browser)

1. Create a GitHub account if needed → github.com (pick a professional username).
2. New repository → name: `job-search-agent`, Public, no template.
3. Upload this folder's contents: "uploading an existing file" link on the empty
   repo page → drag the whole folder contents in → Commit.
   (Or with git:  git init; git add .; git commit -m "initial";
    git remote add origin <repo URL>; git push -u origin main)
4. Enable Pages: repo → Settings → Pages → Source: "Deploy from a branch" →
   Branch: main, folder: `/docs` → Save.
5. Wait ~2 minutes → your demo is live at
   `https://<username>.github.io/job-search-agent/`
6. Edit README.md line 5: replace YOUR-USERNAME with your username so the demo
   link works from the repo page too.

## Before you publish — checklist

- [ ] No database file, resumes, or personal application data in the repo
- [ ] Rubric in the repo is the TEMPLATE, not your filled-in version
- [ ] README results table is accurate to your real numbers
- [ ] Add the link to your resume header and LinkedIn Featured section

## Resume / LinkedIn wording

> Designed and operate an autonomous multi-agent AI pipeline (Claude Agent SDK,
> SQLite, scheduled agents) that screened 145 job postings in its first week,
> auto-triaging 68% and surfacing 24 high-fit roles — live demo: <link>

## Later upgrades (optional)

- Custom domain (e.g., marybuilds.dev) → Pages supports it, ~$12/yr
- Add the case-study PDF to /docs and link it from the demo page
- Record the demo video (script in your Showcase folder) and embed it in README
