#!/usr/bin/env python3
"""Leaderboard, ranks and badges for the ROV experiments homework (docs/experiments/ROV_Experiments.md).

    gh issue list --state all --label experiment --limit 500 --json number,title,labels,author > experiments.json
    python3 docs/experiments/experiment_board.py experiments.json

The team leader verifies a result issue by adding `exp:E07` (worth that experiment's points) and any bonus labels:
bonus:prediction +5, bonus:replicated +10, bonus:bug +20, bonus:chart +10. The issue author collects the points.
Points and badges are read from the mission map in ROV_Experiments.md, so the doc is the only source.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

DOC = Path(__file__).with_name("ROV_Experiments.md")
BONUS = {"bonus:prediction": 5, "bonus:replicated": 10, "bonus:bug": 20, "bonus:chart": 10}
BADGES = {"⏱": "Latency Hunter", "📡": "Tether Whisperer", "💥": "Chaos Monkey", "🔥": "Heat and Power", "🎯": "Encoder Tuner", "👁": "Pilot's Eye"}
RANKS = [(450, "🧠 Chief Engineer"), (250, "⚙️ Engineer"), (100, "🔧 Technician"), (0, "🪸 Cadet")]


def mission_map(doc: Path = DOC) -> dict[str, tuple[int, str, str]]:
    """E-id → (points, badge emoji or '', name), parsed from the mission-map table."""
    rows = re.findall(r"^\| (E\d+) \| (.+?) \| (.+?) \| (?:🟢|🟡|🔴) \| (\d+) \|", doc.read_text(encoding="utf-8"), re.M)
    return {e: (int(p), b.strip() if b.strip() in BADGES else "", n.strip()) for e, n, b, p in rows}


def rank(points: int, badges: int) -> str:
    for need, name in RANKS:
        if points >= need and (need < 450 or badges >= 3):
            return name
    return RANKS[-1][1]


def board(issues: list[dict], exps: dict[str, tuple[int, str, str]]) -> tuple[list[tuple], set[str]]:
    pts, done = defaultdict(int), defaultdict(set)
    for it in issues:
        labels = {l["name"] for l in it.get("labels", [])}
        ids = {l.split(":", 1)[1] for l in labels if l.startswith("exp:") and l.split(":", 1)[1] in exps}
        if not ids:
            continue                                   # not verified yet
        who = it["author"]["login"]
        for e in ids:
            if e not in done[who]:                     # each experiment counts once per person
                pts[who] += exps[e][0]
            done[who].add(e)
        pts[who] += sum(v for l, v in BONUS.items() if l in labels)
    rows = []
    for who in pts:
        badges = [BADGES[b] for b in BADGES if all(e in done[who] for e, (_, bb, _) in exps.items() if bb == b)]
        rows.append((pts[who], who, len(done[who]), badges, rank(pts[who], len(badges))))
    rows.sort(key=lambda r: (-r[0], r[1]))
    nobody = set(exps) - set().union(*done.values()) if done else set(exps)
    return rows, nobody


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("issues_json")
    a = ap.parse_args()
    exps = mission_map()
    rows, nobody = board(json.load(open(a.issues_json, encoding="utf-8")), exps)
    print(f"{'#':>2}  {'who':18} {'pts':>4} {'exps':>4}  {'rank':20} badges")
    for i, (p, who, n, badges, rk) in enumerate(rows, 1):
        print(f"{i:>2}  {who:18} {p:>4} {n:>4}  {rk:20} {', '.join(badges) or '-'}")
    if nobody:
        print("\nNobody has done yet:", ", ".join(f"{e} {exps[e][2]}" for e in sorted(nobody, key=lambda x: int(x[1:]))))


if __name__ == "__main__":
    main()
