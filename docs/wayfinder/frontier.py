#!/usr/bin/env python3
"""Frontier query for the local-markdown wayfinder tracker.

Frontier = open tickets, unclaimed, whose blockers are all closed. Everything else
is either takeable-but-claimed, blocked, or done. Run with no arguments:

    python3 docs/wayfinder/frontier.py
    python3 docs/wayfinder/frontier.py --all
"""

import re
import sys
from pathlib import Path

TICKETS = Path(__file__).parent / "tickets"
FIELD = re.compile(r"^(id|title|type|status|assignee|blocked_by):\s*(.*)$", re.M)


def load():
    tickets = {}
    for path in sorted(TICKETS.glob("*.md")):
        head = path.read_text(encoding="utf-8").split("---", 2)
        if len(head) < 3:
            continue
        fm = dict(FIELD.findall(head[1]))
        blockers = re.findall(r"\d{4}", fm.get("blocked_by", ""))
        tickets[fm.get("id", "").strip('"')] = {
            "title": fm.get("title", "").strip(),
            "type": fm.get("type", "").strip(),
            "status": fm.get("status", "").strip(),
            "assignee": fm.get("assignee", "").strip().strip('"'),
            "blocked_by": blockers,
            "path": path,
        }
    return tickets


def main():
    tickets = load()
    show_all = "--all" in sys.argv

    def closed(tid):
        return tickets.get(tid, {}).get("status") == "closed"

    frontier, blocked, claimed, done = [], [], [], []
    for tid, t in sorted(tickets.items()):
        if t["status"] == "closed":
            done.append((tid, t))
        elif not all(closed(b) for b in t["blocked_by"]):
            blocked.append((tid, t))
        elif t["assignee"]:
            claimed.append((tid, t))
        else:
            frontier.append((tid, t))

    def dump(label, rows, extra=lambda t: ""):
        if not rows:
            return
        print(f"\n{label} ({len(rows)})")
        for tid, t in rows:
            print(f"  [{t['type']:<9}] {t['title']}{extra(t)}")
            print(f"  {' ' * 12}{t['path'].as_posix()}")

    dump("FRONTIER — takeable now", frontier)
    dump("CLAIMED", claimed, lambda t: f"  → {t['assignee']}")
    dump("BLOCKED", blocked, lambda t: f"  ← chờ {', '.join(t['blocked_by'])}")
    if show_all:
        dump("CLOSED", done)
    else:
        print(f"\nCLOSED ({len(done)}) — dùng --all để xem")


if __name__ == "__main__":
    main()
