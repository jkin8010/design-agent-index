#!/usr/bin/env python3
"""Median across repeated runs (r1..rN) for one date.

One generation per skill is noise: a single unlucky run can sink a skill. This takes the
median per (skill, brief) so a published number survives a rerun.

  python3 bench/aggregate.py --date 2026-11-07
"""
import argparse
import glob
import json
import os
import statistics

BENCH = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()

    base = os.path.join(BENCH, "runs", args.date)
    cells = {}
    for f in glob.glob(os.path.join(base, "*", "*", "score.json")):
        skill = os.path.basename(os.path.dirname(os.path.dirname(f)))
        dirname = os.path.basename(os.path.dirname(f))
        brief, _, tag = dirname.partition("__")
        rec = json.load(open(f))
        rec["tag"] = tag or "r1"
        cells.setdefault((skill, brief), []).append(rec)

    if not cells:
        raise SystemExit("no scored cells")

    agg = {}
    for (skill, brief), recs in cells.items():
        totals = [r["total"] for r in recs]
        agg.setdefault(skill, {})[brief] = {
            "median": statistics.median(totals),
            "min": min(totals), "max": max(totals), "n": len(totals),
            "tags": sorted(r["tag"] for r in recs),
        }

    skills = sorted(agg, key=lambda s: -statistics.median(
        [v["median"] for v in agg[s].values()]))
    briefs = sorted({b for s in agg for b in agg[s]})

    lines = [f"# Design bench medians — {args.date}", "",
             f"Median of {max(v['n'] for s in agg for v in agg[s].values())} runs per cell. "
             "Same briefs, same model, one skill per cell.", "",
             "| skill | " + " | ".join(b[:2] for b in briefs) + " | median-of-medians | vs control |",
             "|---|" + "---:|" * len(briefs) + "---:|---:|"]
    control = agg.get("control", {})
    for s in skills:
        row, meds = [], []
        for b in briefs:
            v = agg[s].get(b)
            row.append(f"{v['median']:g}" if v else "·")
            if v:
                meds.append(v["median"])
        overall = statistics.median(meds) if meds else 0
        if s == "control" or not control:
            delta = "—"
        else:
            diffs = [agg[s][b]["median"] - control[b]["median"] for b in briefs
                     if b in agg[s] and b in control]
            delta = f"{statistics.median(diffs):+.1f}" if diffs else "—"
        lines.append(f"| {s} | " + " | ".join(row) + f" | **{overall:g}** | {delta} |")

    lines += ["", "## Spread across runs", "",
              "| cell | runs | min | median | max |", "|---|---:|---:|---:|---:|"]
    for s in skills:
        for b in briefs:
            v = agg[s].get(b)
            if v:
                lines.append(f"| {s}/{b} | {v['n']} | {v['min']} | {v['median']:g} | {v['max']} |")

    open(os.path.join(base, "MEDIAN.md"), "w").write("\n".join(lines) + "\n")
    json.dump(agg, open(os.path.join(base, "medians.json"), "w"), indent=1)
    print("\n".join(lines[:12]))
    print(f"\nwrote {base}/MEDIAN.md")


if __name__ == "__main__":
    main()