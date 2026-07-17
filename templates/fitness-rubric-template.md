# Job Fitness Rubric — <YOUR NAME>

> This file is the single source of truth for how the screening agent scores jobs.
> The agent re-reads it on every run, so edit freely as your search evolves.
> Replace every <angle-bracket> placeholder. Delete examples that don't apply.

## Target roles — tracks and resumes

List the role families you're pursuing and which resume file scores each.

- **Track A: <e.g., Engineering Leadership>** — titles: <Director of X, Head of Y, ...> → resume: `<ResumeA.pdf>`
- **Track B (optional): <e.g., Program Management>** — titles: <...> → resume: `<ResumeB.pdf>`

## Experience baseline

Facts the agent must assume so it never lists a gap you don't have:

- <e.g., "Treat my work from 2015 onward as management experience; I meet any '7+ years' minimum.">
- <e.g., "My current title undersells my scope — treat junior-looking titles as a compensation question, not a candidacy gap.">

## Scoring dimensions (rate each 1–5)

1. **Level fit:** <what seniority counts as right-level for you; what scores low>
2. **Scope match:** <the kind of work that is your core; more of it = higher>
3. **Reframing distance:** how much explaining the fit requires; less = higher

## Red flags (cap overall fitness at 2)

Only when they are core/required — under "preferred", they're gaps, not caps.

- <e.g., heavy hands-on production coding as the daily job>
- <e.g., a narrow domain you lack and don't want: ...>
- <e.g., 24/7 on-call as the core responsibility>

Explicit NON-red-flags (things that look scary but you're fine with):

- <e.g., "Industry X compliance is NOT a red flag — I'm learning it; list as a gap.">

## Overall fitness score

- **5 — apply now:** core-fit role, low reframing, no red flags
- **4 — strong, apply:** good match, minor reframing or one soft gap
- **3 — worth a tailored look:** real fit but needs a cover-letter-level reframe
- **2 — stretch, probably skip:** red flag or heavy reframing for thin payoff
- **1 — skip:** wrong level, wrong scope, or disqualifying red flag

## Recruiter_Match score (0–100%)

Scored AFTER the fitness score, from the opposite chair: the agent becomes the posting's recruiter reading your resume cold. Your experience-baseline reframings above do NOT apply — a screener only credits what the resume literally shows in the posting's vocabulary. Start at 100 and deduct:

- Domain/industry depth the JD asks for that the resume doesn't show: −15 preferred, −25 required
- Title-history mismatch (resume never carried a title close to the posting's): −15
- Missing JD hard-skill keywords: −5 each, max −20
- Seniority direction (resume reads a level below: −10; overqualified: −5)
- Experience minimums the resume doesn't explicitly evidence: −10
- Location / work-authorization / clearance friction: −10

Bands: 80–100 shortlisted as-is; 60–79 shortlisted with tailoring; 40–59 heavy tailoring or referral; <40 referral only. Fitness answers "do I want it?"; Recruiter_Match answers "will screening pass me?" — a role can score high on one and low on the other.

## Anchor stories (the agent picks one per job)

Your 5–10 proudest ownership stories, each with when to use it:

- **<Story name>:** <one-line what you did + measurable result>. Use for <role type>.
- **<Story name>:** <...>. Use for <...>.

If no anchor fits a role's core, the agent flags it — that absence is itself a fit signal.

## Key metrics bank

Numbers the agent may cite: <team size, budget, users, revenue impact, % improvements...>
