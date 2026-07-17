#!/usr/bin/env python3
"""Salvage Job_Tracker records from a corrupt SQLite image by parsing
table-leaf b-tree pages directly (ignoring broken pointer structure)."""
import sys, json

DATA = open(sys.argv[1], "rb").read()
PAGE = int.from_bytes(DATA[16:18], "big")
if PAGE == 1: PAGE = 65536
RESERVED = DATA[20]
U = PAGE - RESERVED
NPAGES = len(DATA) // PAGE

def varint(b, i):
    v = 0
    for n in range(9):
        c = b[i]; i += 1
        if n == 8:
            v = (v << 8) | c
            return v, i
        v = (v << 7) | (c & 0x7F)
        if not (c & 0x80):
            return v, i
    return v, i

def serial_len(t):
    if t >= 12: return (t - 12) // 2 if t % 2 == 0 else (t - 13) // 2
    return [0,1,2,3,4,6,8,8,0,0][t] if t < 10 else None

def decode(t, raw):
    if t == 0: return None
    if 1 <= t <= 6:
        n = [1,2,3,4,6,8][t-1]
        return int.from_bytes(raw[:n], "big", signed=True)
    if t == 7:
        import struct; return struct.unpack(">d", raw[:8])[0]
    if t == 8: return 0
    if t == 9: return 1
    if t >= 13 and t % 2 == 1: return raw.decode("utf-8", "replace")
    if t >= 12: return raw  # blob
    return None

def overflow_chain(first_page, need):
    """Follow overflow pages, return up to `need` bytes."""
    out = b""; pg = first_page; seen = set()
    while pg and len(out) < need:
        if pg in seen or pg < 2 or pg > NPAGES: break
        seen.add(pg)
        off = (pg - 1) * PAGE
        nxt = int.from_bytes(DATA[off:off+4], "big")
        out += DATA[off+4 : off+PAGE]
        pg = nxt
    return out[:need]

def parse_leaf(pgno):
    """Yield (rowid, values, ok) for each cell on a table-leaf page."""
    base = (pgno - 1) * PAGE
    hoff = base + (100 if pgno == 1 else 0)
    if DATA[hoff] != 0x0D: return
    ncell = int.from_bytes(DATA[hoff+3:hoff+5], "big")
    if not (0 < ncell <= 200): return
    cparr = hoff + 8
    for c in range(ncell):
        try:
            cp = int.from_bytes(DATA[cparr+2*c:cparr+2*c+2], "big")
            if not (0 < cp < PAGE): continue
            i = base + cp
            P, i = varint(DATA, i)
            rowid, i = varint(DATA, i)
            if not (0 < P < 1_000_000 and 0 < rowid < 100_000): continue
            X = U - 35
            if P <= X:
                payload = DATA[i:i+P]
            else:
                M = ((U - 12) * 32 // 255) - 23
                K = M + ((P - M) % (U - 4))
                local = K if K <= X else M
                ovpg = int.from_bytes(DATA[i+local:i+local+4], "big")
                payload = DATA[i:i+local] + overflow_chain(ovpg, P - local)
            if len(payload) < P: continue
            # record decode
            hlen, j = varint(payload, 0)
            types = []
            while j < hlen:
                t, j = varint(payload, j)
                types.append(t)
            vals = []; k = hlen; ok = True
            for t in types:
                L = serial_len(t)
                if L is None or k + L > len(payload): ok = False; break
                vals.append(decode(t, payload[k:k+L])); k += L
            if ok:
                yield rowid, vals, pgno
        except Exception:
            continue

records = {}   # rowid -> list of (vals, page)
for pg in range(1, NPAGES + 1):
    for rowid, vals, pgno in parse_leaf(pg):
        if len(vals) == 21:   # Job_Tracker has 21 columns
            records.setdefault(rowid, []).append((vals, pgno))

COLS = ["Job_ID","Date_Created","Source","Agent","App_URL","Other_App_URL","Title",
        "Company","Location","JD","Salary_Range","Employment_Type","Date_Posted",
        "HM_or_TA","Job_Track","Fitness_Score","Key_Gaps","Anchor_Story","Notes",
        "Status","Date_Updated"]

out = []
dupes = 0
for rowid, versions in sorted(records.items()):
    if len(versions) > 1:
        dupes += 1
        # prefer latest Date_Updated (idx 20), then latest page order
        versions.sort(key=lambda v: ((v[0][20] or ""), v[1]))
    vals, pgno = versions[-1]
    rec = dict(zip(COLS, vals))
    rec["Job_ID"] = rowid          # col 0 is NULL (rowid alias)
    rec["_page"] = pgno
    rec["_versions"] = len(versions)
    # keep JD out of the dump (huge)
    rec["JD"] = (rec["JD"][:40] + "...") if isinstance(rec["JD"], str) and len(rec["JD"]) > 40 else rec["JD"]
    out.append(rec)

print(json.dumps({"page_size": PAGE, "pages": NPAGES,
                  "rows_salvaged": len(out), "rowids_with_multiple_versions": dupes}))
with open("/tmp/salvaged.json", "w") as f:
    json.dump(out, f, indent=1, default=str)
print("min/max rowid:", out[0]["Job_ID"] if out else None, out[-1]["Job_ID"] if out else None)
