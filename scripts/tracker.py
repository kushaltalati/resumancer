#!/usr/bin/env python3
"""Application tracker in ~/.resumancer/applications.json (+ a markdown view).
  tracker.py add --company C --role R --url U [--deadline YYYY-MM-DD] [--status filled|submitted|rejected|interview|offer] [--folder DIR] [--notes ...]
  tracker.py check <company>        # warn if applied to this company within --days (default 240 ≈ 8 months)
  tracker.py list [--days 30]       # table + deadlines within N days
  tracker.py set <id> --status submitted"""
import json, os, sys, argparse, datetime as dt

HOME = os.path.expanduser("~/.resumancer"); J = os.path.join(HOME, "applications.json"); M = os.path.join(HOME, "applications.md")

def load():
    if os.path.exists(J): return json.load(open(J))
    return []

def save(rows):
    os.makedirs(HOME, exist_ok=True)
    json.dump(rows, open(J, "w"), indent=2)
    with open(M, "w") as f:
        f.write("# Applications\n\n| # | Date | Company | Role | Status | Deadline | Folder | URL |\n|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['id']} | {r['date']} | {r['company']} | {r['role']} | {r['status']} | {r.get('deadline') or ''} | {r.get('folder') or ''} | {r.get('url') or ''} |\n")

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("--company", required=True); a.add_argument("--role", required=True); a.add_argument("--url", default="")
    a.add_argument("--deadline"); a.add_argument("--status", default="filled"); a.add_argument("--folder"); a.add_argument("--notes", default="")
    c = sub.add_parser("check"); c.add_argument("company"); c.add_argument("--days", type=int, default=240)
    l = sub.add_parser("list"); l.add_argument("--days", type=int, default=30)
    s = sub.add_parser("set"); s.add_argument("id", type=int); s.add_argument("--status", required=True); s.add_argument("--notes")
    x = ap.parse_args(); rows = load(); today = dt.date.today()
    if x.cmd == "add":
        rid = (max([r["id"] for r in rows]) + 1) if rows else 1
        rows.append({"id": rid, "date": today.isoformat(), "company": x.company, "role": x.role, "url": x.url, "deadline": x.deadline, "status": x.status, "folder": x.folder, "notes": x.notes})
        save(rows); print(f"added #{rid}: {x.company} — {x.role} [{x.status}]")
    elif x.cmd == "check":
        hits = [r for r in rows if r["company"].lower() == x.company.lower() and (today - dt.date.fromisoformat(r["date"])).days <= x.days]
        if hits:
            for r in hits: print(f"WARNING: applied to {r['company']} on {r['date']} ({r['role']}, {r['status']}) — {(today - dt.date.fromisoformat(r['date'])).days} days ago; check the firm's re-apply / cool-off policy")
            sys.exit(3)
        print(f"no application to {x.company} in the last {x.days} days")
    elif x.cmd == "list":
        if not rows: print("no applications yet"); return
        print(f"{'#':>3} {'date':10} {'status':10} {'deadline':10} company — role")
        for r in rows: print(f"{r['id']:>3} {r['date']:10} {r['status']:10} {(r.get('deadline') or '-'):10} {r['company']} — {r['role']}")
        soon = [r for r in rows if r.get("deadline") and 0 <= (dt.date.fromisoformat(r["deadline"]) - today).days <= x.days and r["status"] in ("filled", "draft")]
        if soon:
            print(f"\nDeadlines within {x.days} days, not yet submitted:")
            for r in soon: print(f"  {r['deadline']}  {r['company']} — {r['role']}  (#{r['id']})")
    elif x.cmd == "set":
        for r in rows:
            if r["id"] == x.id:
                r["status"] = x.status
                if x.notes: r["notes"] = x.notes
                save(rows); print(f"#{x.id} → {x.status}"); return
        print("no such id"); sys.exit(1)

if __name__ == "__main__":
    main()
