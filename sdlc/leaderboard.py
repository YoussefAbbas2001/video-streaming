#!/usr/bin/env python3
"""Bug Hunt League leaderboard from GitHub issues.

    gh issue list --state closed --label bug --limit 500 --json number,title,labels,author,closedAt > closed_bugs.json
    python3 leaderboard.py closed_bugs.json [--since 2026-12-01]

Points come from labels: sev:critical 10, sev:major 5, sev:minor 2, sev:ux 1; bonus labels
bonus:evidence +2, regression +3, bonus:fix +5. The issue author is the hunter.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict

SEVERITY = {"sev:critical": 10, "sev:major": 5, "sev:minor": 2, "sev:ux": 1}
BONUS = {"bonus:evidence": 2, "regression": 3, "bonus:fix": 5}


def points(labels: set[str]) -> int:
    sev = max((SEVERITY[l] for l in labels if l in SEVERITY), default=0)
    return sev + sum(v for l, v in BONUS.items() if l in labels) if sev else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("issues_json")
    ap.add_argument("--since", help="only issues closed on/after this date (YYYY-MM-DD)")
    a = ap.parse_args()
    issues = json.load(open(a.issues_json, encoding="utf-8"))
    score, bugs, best = defaultdict(int), defaultdict(int), {}
    for it in issues:
        if a.since and (it.get("closedAt") or "") < a.since:
            continue
        labels = {l["name"] for l in it.get("labels", [])}
        p = points(labels)
        if not p:
            continue   # unconfirmed or rejected: no severity label
        who = it["author"]["login"]
        score[who] += p; bugs[who] += 1
        if p > best.get(who, (0, ""))[0]:
            best[who] = (p, f"#{it['number']} {it['title']}")
    ranking = sorted(score.items(), key=lambda kv: (-kv[1], -bugs[kv[0]]))
    print(f"{'#':>2}  {'hunter':20} {'points':>6} {'bugs':>5}  best find")
    for i, (who, pts) in enumerate(ranking, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, "  ")
        print(f"{i:>2}{medal} {who:20} {pts:>6} {bugs[who]:>5}  {best[who][1][:60]}")
    if not ranking:
        print("No confirmed bugs yet: time for a Bug Bash!")


if __name__ == "__main__":
    main()
