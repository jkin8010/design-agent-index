#!/usr/bin/env python3
"""Turn metrics.json into a 0-100 score with published, fixed weights.

  python3 bench/score.py --date 2026-11-07

Every rule here is deterministic. A human review pass can override a cell, but the
override is recorded in `review.json` and shown next to the automatic score — never
silently folded in.
"""
import argparse
import json
import os
import re

BENCH = os.path.dirname(os.path.abspath(__file__))

BUZZ = ("elevate", "seamless", "unlock", "revolutioni", "supercharge", "game-chang",
        "cutting-edge", "effortless", "empower", "transform your")

PURPLE = re.compile(r"#(6d28d9|7c3aed|8b5cf6|a855f7|9333ea|6366f1|818cf8|4f46e5)", re.I)


def score(m):
    parts = {}

    # 1 render (10)
    renders = 10 if not m.get("console_errors") else max(0, 10 - 3 * len(m["console_errors"]))
    parts["render"] = min(10, renders)

    # 2 responsive (15)
    resp = 0
    resp += 10 if not m.get("overflow_375") else 0
    resp += 5 if m.get("tapViolations", 99) <= 2 else 2 if m.get("tapViolations", 99) <= 5 else 0
    parts["responsive"] = resp

    # 3 contrast (15)
    fail = m.get("contrast_fail_ratio")
    parts["contrast"] = 0 if fail is None else round(15 * (1 - fail))

    # 4 typography (10)
    fonts = len(m.get("fonts") or [])
    sizes = len(m.get("sizes") or [])
    parts["typography"] = (5 if fonts <= 3 else 2 if fonts <= 5 else 0) + \
                          (5 if 4 <= sizes <= 9 else 2 if sizes <= 12 else 0)

    # 5 colour discipline (10)
    bgs = len(m.get("bgColors") or [])
    fgs = len(m.get("colors") or [])
    parts["colour"] = (5 if bgs <= 8 else 2 if bgs <= 14 else 0) + \
                      (5 if fgs <= 5 else 2 if fgs <= 8 else 0)

    # 6 anti-slop (20)
    css = m.get("css") or ""
    text = (m.get("text") or "").lower()
    penalty = 0
    if PURPLE.search(css):
        penalty += 6
    if "backdrop-filter" in css or "-webkit-backdrop-filter" in css:
        penalty += 4
    if "background-clip: text" in css or "-webkit-background-clip: text" in css:
        penalty += 3
    if re.search(r"[\U0001F300-\U0001FAFF]", text):
        penalty += 3
    penalty += min(4, sum(1 for w in BUZZ if w in text))
    parts["anti_slop"] = max(0, 20 - penalty)

    # 7 structure (10)
    sem = m.get("semantic") or {}
    parts["structure"] = (5 if m.get("h1") == 1 else 0) + \
                         (5 if sum(1 for v in sem.values() if v) >= 4 else 2 if sum(1 for v in sem.values() if v) >= 2 else 0)

    # 8 weight (10)
    kb = (m.get("html_bytes") or 0) / 1024
    parts["weight"] = 10 if kb <= 300 else 6 if kb <= 600 else 2

    return {"total": sum(parts.values()), "parts": parts, "slop_penalty": penalty}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()

    base = os.path.join(BENCH, "runs", args.date)
    out = {}
    for skill in sorted(x for x in os.listdir(base) if os.path.isdir(os.path.join(base, x))):
        for brief in sorted(os.listdir(os.path.join(base, skill))):
            cell = os.path.join(base, skill, brief)
            mp = os.path.join(cell, "metrics.json")
            if not os.path.exists(mp):
                continue
            m = json.load(open(mp))
            meta = json.load(open(os.path.join(cell, "meta.json"))) if os.path.exists(os.path.join(cell, "meta.json")) else {}
            m["html_bytes"] = meta.get("html_bytes") or os.path.getsize(os.path.join(cell, "index.html"))
            s = score(m)
            s.update({"skill": skill, "brief": brief, "seconds": meta.get("seconds"),
                      "agent": meta.get("agent")})
            out[f"{skill}/{brief}"] = s
            json.dump(s, open(os.path.join(cell, "score.json"), "w"), indent=1)
            print(f"{s['total']:>3}  {skill}/{brief}  (slop -{s['slop_penalty']})")

    json.dump(out, open(os.path.join(base, "scores.json"), "w"), indent=1)
    print(f"\n{len(out)} cells scored")


if __name__ == "__main__":
    main()