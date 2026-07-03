# Job-Search Agent

An autonomous AI pipeline that reads, scores, and tracks job postings — so your mornings start with a prioritized shortlist, not a haystack.

**[▶ Live interactive demo](https://maryistafanous.github.io/job-search-agent/)** · [Case study (PDF)](docs/case-study.pdf) · Built with Claude (Anthropic Agent SDK / Cowork scheduled tasks)

![Architecture](docs/architecture.png)

## What it does

Every morning, unattended:

1. **Data-Entry Agent** (daily, 7:05 AM) parses overnight job-alert emails (LinkedIn, Indeed), de-duplicates against everything already tracked, and inserts new roles into a SQLite database.
2. **Career-Scan Agent** (daily, 7:15 AM) proactively checks a curated list of target companies' own career pages — catching roles that never hit the job boards — and feeds matches into the same pipeline.
3. **Screening Agent** (daily, 7:30 AM) opens each posting — automatically falling back to the employer's own careers site when LinkedIn won't render the description — and scores it 1–5 against *your* written fitness rubric and *your* resume. It records salary (only if actually stated), key gaps, and the strongest interview "anchor story" for each role. It finishes by rebuilding a personal dashboard of high-fit, not-yet-applied roles with one-click actions.
4. **Inbox-Sweep Agent** (daily, 7:45 AM) reads recruiter/application emails and keeps every application's status current.
5. **Resume Tailor** (on demand) turns any high-fit tracker row into an application kit: an ATS-optimized resume variant that honestly mirrors the posting's keywords, weaves in the pre-selected anchor story, plus a cover-letter draft. You pick the roles; it never fabricates experience.

The scheduled agents execute as a **single sequenced pipeline**: if the machine was asleep at 7 AM, the entire sequence runs once on wake — still in order, so schedule collisions are impossible by construction.

Your job shrinks to reviewing a prioritized shortlist over coffee — and saying "prepare a kit for #12" when one deserves an application.

## Results (author's first 7 days)

| Metric | Result |
|---|---|
| Roles ingested and fully scored | 145 |
| Auto-triaged out, with documented reasons | 68% |
| High-fit roles (4–5) surfaced | 24 |
| Human time required | ~20 min/day |

## Design principles

- **Rubric as single source of truth** — scoring policy is a markdown file you edit, re-read on every run. Works for any profession: define your own dimensions, red flags, and score bands.
- **Honesty rules** — the agent never fabricates salaries, dates, or contacts. Partially-read postings are flagged `PROVISIONAL` with what would change the score.
- **Idempotent writes** — de-duplication on application URL; re-runs update, never duplicate.
- **Reliability** — write-lock protocol, integrity checks before/after every write, timestamped backups. (Born from a real corruption incident; recovery tooling included the hard way.)

## What you need

- A Claude subscription with Cowork or Claude Code (the agents run as Claude skills + scheduled tasks)
- Gmail (or any mailbox Claude can read) receiving job-alert emails
- Your resume(s) and 30 minutes to fill in the rubric template

See **[SETUP.md](SETUP.md)** for step-by-step instructions.

## Repo layout

```
templates/   your-inputs: fitness rubric + search profile (fill these in)
skills/      the agent skill definitions incl. proactive company career scan
db/          SQLite schema for the tracker
docs/        interactive demo (GitHub Pages site)
SETUP.md     installation & first run
```

## Honest limitations

- Requires a Claude subscription; this is not a hosted service.
- LinkedIn postings are read through **your own logged-in browser session** (LinkedIn throttles and prohibits server-side scraping). The built-in fallback to employer career sites (Greenhouse/Workday/Lever) covers most gaps.
- Built and tested on one machine at a time; the tracker is a local SQLite file.

## License

MIT — see [LICENSE](LICENSE).
