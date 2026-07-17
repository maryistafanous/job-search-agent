#!/usr/bin/env python3
"""backup_db.py — timestamped copy of the tracker DB, with retention.

Reads db_path and backup_dir from config.json (repo root). Keeps the newest
KEEP backups it created (job_search-*.bak) and deletes older ones.

Run: python scripts/backup_db.py   (run-pipeline.bat calls this before the run)
"""
import json
import os
import shutil
import sys
from datetime import datetime

KEEP = 14

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(REPO, "config.json"), encoding="utf-8") as f:
    cfg = json.load(f)

db = cfg["db_path"]
bdir = cfg.get("backup_dir") or os.path.join(os.path.dirname(db), "backups")
if not os.path.exists(db):
    print(json.dumps({"ok": False, "error": f"database not found: {db}"}))
    sys.exit(1)
os.makedirs(bdir, exist_ok=True)

name = f"job_search-{datetime.now():%Y%m%d_%H%M%S}.bak"
dest = os.path.join(bdir, name)
shutil.copyfile(db, dest)

mine = sorted(f for f in os.listdir(bdir)
              if f.startswith("job_search-") and f.endswith(".bak"))
pruned = []
for old in mine[:-KEEP]:
    os.remove(os.path.join(bdir, old))
    pruned.append(old)

print(json.dumps({"ok": True, "backup": dest,
                  "kept": min(len(mine), KEEP), "pruned": len(pruned)}))
