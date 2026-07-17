# Scheduled tasks (deprecated)

This file described the original Cowork scheduled-task prompts. The pipeline now runs in **Claude Code**: the sequenced daily run lives in [`pipeline/morning-pipeline.md`](pipeline/morning-pipeline.md), triggered by `scripts/run-pipeline.bat` (manually or via Windows Task Scheduler — see [SETUP.md](SETUP.md) step 7).

The individual phases can still be run standalone by pointing Claude Code at the corresponding skill in `.claude/skills/` (data-entry, career-scan, screening, inbox-sweep).
