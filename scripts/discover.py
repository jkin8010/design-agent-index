#!/usr/bin/env python3
"""Discover candidate repositories and report ones not yet in the registry.

This does NOT admit entries. It prints candidates for human review, because keyword
search reliably returns PCB-design, FPGA-design and product repos that have nothing
to do with agent design capability.

Usage: python3 scripts/discover.py [--min-stars 50]
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

QUERIES = [
    "topic:design-skills",
    '"design skill" in:description',
    '"design.md" in:name,description',
    '"design intelligence" in:description',
    '"ui skill" in:description',
    '"frontend design" in:description',
    '"anti-slop" in:description',
    '"design system" skill in:description',
    '"design review" skill in:description',
]

WORDS = (
    "design", "ui", "ux", "visual", "brand", "motion", "typograph", "layout",
    "slop", "taste", "figma", "frontend",
)


def api(path):
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "design-agent-index",
            **({"Authorization": "Bearer " + token} if token else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    min_stars = 50
    if "--min-stars" in sys.argv:
        min_stars = int(sys.argv[sys.argv.index("--min-stars") + 1])

    known = {e["repo"] for e in json.load(open(os.path.join(ROOT, "registry.json")))}
    found = {}

    for q in QUERIES:
        enc = urllib.parse.quote(q)
        try:
            data = api(f"/search/repositories?q={enc}&sort=stars&order=desc&per_page=50")
        except Exception as exc:  # noqa: BLE001
            print(f"query failed: {q}: {exc}")
            continue
        for it in data.get("items", []):
            desc = (it.get("description") or "").lower()
            if it["stargazers_count"] < min_stars or it.get("archived"):
                continue
            if not any(w in desc for w in WORDS):
                continue
            found[it["full_name"]] = it["stargazers_count"]
        time.sleep(2)

    new = sorted(((n, s) for n, s in found.items() if n not in known), key=lambda x: -x[1])
    print(f"{len(new)} candidates not in registry\n")
    for name, stars in new:
        print(f"{stars:>7}  {name}")


if __name__ == "__main__":
    main()
