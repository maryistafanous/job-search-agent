---
name: company-career-scan
description: >-
  Proactively scan a curated list of target companies' career pages for matching
  openings, instead of waiting for job-board alerts. Inserts matches into the
  tracker for the screening agent to score.
---

# Company Career Scan (generic)

Job boards only show you what's advertised there. Your best-fit employers often
post on their own career sites first (or only). This scan flips the search from
reactive (alerts) to proactive (targets).

## Input: the target list

`target-companies.csv` (from the template) — a curated list of companies you'd
actually want to work for, each with its career-site URL and the role families
to watch. Build it once (~an hour with AI help: "find 30 <industry> companies
with <criteria> and their career page URLs"), then maintain it as you learn.

## Flow

FOR EACH company in the CSV (highest Priority first):
1. Fetch the career page. Most are Greenhouse/Workday/Lever boards —
   server-rendered and easy to read.
2. Filter openings against "Role Families to Watch" and your search-profile
   location/salary filters.
3. For each match not already in Job_Tracker (de-dupe on App_URL): insert a row
   with Source = "Career Scan", ready for the screening agent to score.
4. Track scan state (last-checked date per company) in a small JSON file so each
   run can prioritize companies not checked recently.

## Cadence and scope

- Weekly is plenty (career pages change slower than job boards).
- Cap each run (e.g., 10-15 companies) to keep runs short; the state file
  rotates coverage.
- Respect sites: read the public careers page only, no login walls, no
  rapid-fire requests.

## Scheduled task prompt (weekly)

> Run the company-career-scan (skills/company-career-scan.md) on
> target-companies.csv in <your folder>: check the 15 least-recently-scanned
> companies for openings matching my role families and filters, insert new
> matches into Job_Tracker with Source "Career Scan", update the scan-state file,
> and summarize: companies checked, new roles found, best match.
