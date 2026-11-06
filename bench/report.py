#!/usr/bin/env python3
"""Render results: a markdown report and an HTML gallery (screenshots side by side).

  python3 bench/report.py --date 2026-11-07
"""
import argparse
import json
import os

BENCH = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()
    base = os.path.join(BENCH, "runs", args.date)
    scores = json.load(open(os.path.join(base, "scores.json")))

    skills = sorted({k.split("/")[0] for k in scores})
    briefs = sorted({k.split("/")[1] for k in scores})

    lines = [f"# Design bench — {args.date}", "",
             "Same briefs, same model, one skill per cell. Scores are deterministic (see `score.py`).", "",
             "| skill | " + " | ".join(b[:2] for b in briefs) + " | mean |",
             "|---|" + "---:|" * len(briefs) + "---:|"]
    for s in skills:
        row, vals = [], []
        for b in briefs:
            v = scores.get(f"{s}/{b}", {}).get("total")
            row.append(str(v) if v is not None else "·")
            if v is not None:
                vals.append(v)
        mean = round(sum(vals) / len(vals)) if vals else "·"
        lines.append(f"| {s} | " + " | ".join(row) + f" | **{mean}** |")
    lines += ["", "## Detail", "",
              "| cell | score | slop penalty | contrast fail | 375 overflow | seconds |",
              "|---|---:|---:|---:|:--:|---:|"]
    for k in sorted(scores):
        s = scores[k]
        cell_dir = os.path.join(base, *k.split("/"))
        m = json.load(open(os.path.join(cell_dir, "metrics.json")))
        lines.append(f"| {k} | {s['total']} | -{s['slop_penalty']} | {m.get('contrast_fail_ratio')} | "
                     f"{'yes' if m.get('overflow_375') else 'no'} | {s.get('seconds')} |")
    open(os.path.join(base, "REPORT.md"), "w").write("\n".join(lines) + "\n")

    cards = []
    for k in sorted(scores):
        s = scores[k]
        d = os.path.join(base, *k.split("/"))
        cards.append(
            f'<figure><img src="{k}/shot-1440.jpg"><figcaption>{k} — <b>{s["total"]}</b></figcaption></figure>'
            f'<figure><img class="m" src="{k}/shot-375.jpg"><figcaption>375px</figcaption></figure>'
        )
    html = ("<!doctype html><meta charset=utf-8><title>bench</title>"
            "<style>body{font:14px/1.5 system-ui;margin:24px;background:#111;color:#eee}"
            "figure{display:inline-block;vertical-align:top;margin:0 16px 24px 0;width:46%}"
            "img{width:100%;border:1px solid #333}img.m{width:180px}"
            "figcaption{padding-top:6px;color:#aaa}</style>"
            f"<h1>Design bench — {args.date}</h1>" + "".join(cards))
    open(os.path.join(base, "gallery.html"), "w").write(html)
    print(f"wrote {base}/REPORT.md and gallery.html ({len(scores)} cells)")


if __name__ == "__main__":
    main()