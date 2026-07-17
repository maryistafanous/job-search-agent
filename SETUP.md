# Setup

Time: ~30–45 minutes. Prerequisites: a Claude subscription, [Claude Code](https://www.anthropic.com/claude-code) installed on the machine that will run the pipeline, Python 3, and an email account receiving job alerts.

## 1. Install Claude Code and log in with your plan

```
irm https://claude.ai/install.ps1 | iex     (Windows PowerShell)
```

Run `claude` once and log in with your **Claude account (subscription)** — not an API key. Confirm with `/status`. Make sure no `ANTHROPIC_API_KEY` environment variable is set, or it will silently take priority over your plan.

## 2. Clone this repo and trust it

```
git clone https://github.com/<you>/job-search-agent
cd job-search-agent
claude
```

Accept the **trust dialog** on that first interactive run, then exit. Without this, headless runs ignore `.claude/settings.json` and stall on permission prompts.

## 3. Create your data folder (outside the repo)

Personal data never goes in the repo. In a folder of your choice:

- Create the tracker: `sqlite3 job_search.db < db/schema.sql` (or ask Claude to do it)
- Copy `templates/fitness-rubric-template.md` → `fitness-rubric.md` and **fill it in completely** — this is 80% of result quality; be specific about red flags and anchor stories
- Copy `templates/search-profile-template.md` → `search-profile.md` — target roles, exclusions, location rules
- Copy `templates/target-companies-template.csv` → your target-companies CSV (for the career scan)
- Put your resume there (.docx or .pdf)

## 4. Point the engine at your data

```
copy config.example.json config.json
```

Edit `config.json`: db_path, resume_path, rubric_path, search_profile_path, target_companies_csv, scan_state_path, backup_dir, your name/email, and the Gmail label your job alerts land under. `config.json` is gitignored.

## 5. Connect Gmail and Chrome

- In Claude Code, `/mcp` should show the claude.ai **Gmail** connector connected (log in at claude.ai → Settings → Connectors if not). The pipeline reads alerts, applies labels, archives, and creates drafts — it never sends email.
- Set up daily job-alert emails on LinkedIn/Indeed, filtered to a Gmail label matching `config.json → gmail.alert_label`.
- Install the Claude Chrome extension if you want the career-scan phase; the pipeline skips it gracefully when no browser is connected.

## 6. First run — supervised

From the repo folder, in an interactive `claude` session:

1. "Follow .claude/skills/data-entry/SKILL.md" — check rows appear (`python scripts/job_db.py check`).
2. "Follow .claude/skills/screening/SKILL.md and score the pending jobs" — read the scores and gaps critically. If they feel wrong, fix the RUBRIC (not the scores) and re-run; the rubric is the dial.
3. Start the dashboard (`scripts\start-dashboard.bat`) and confirm http://127.0.0.1:8765/ shows your data.

## 7. Schedule it

```
schtasks /Create /TN "MorningJobPipeline" /TR "C:\path\to\job-search-agent\scripts\run-pipeline.bat" /SC DAILY /ST 07:10
```

In Task Scheduler → Properties → Settings, tick **"Run task as soon as possible after a scheduled start is missed"** (sleep tolerance). Logs land in `logs\pipeline-<timestamp>.log`, one per run. The model is pinned in `run-pipeline.bat` (`--model sonnet`); adjust to taste.

## 8. Daily use

Read the morning summary draft in Gmail; review roles scored 4–5 on the dashboard; set Status as you apply. Re-tune the rubric weekly — it should evolve with what you learn from interviews.

## Troubleshooting

- **"Ignoring N permissions.allow entries … workspace has not been trusted":** do step 2's interactive trust run.
- **Career scan skipped ("browser not connected"):** Chrome with the Claude extension wasn't open — expected and harmless; the same companies are retried next run.
- **LinkedIn descriptions won't load:** normal throttling; the screening skill flips to employer career sites for the rest of the batch. Don't retry repeatedly.
- **Scores feel off:** the rubric is underspecified. Add explicit red flags, non-red-flags, and baseline facts ("never list X as a gap").
- **DB integrity error:** `job_db.py` refuses to write and says so. Restore the newest backup from your backup folder; nothing is written to a suspect database.
