#!/usr/bin/env python3
"""Build the Design Agent Index snapshot and README.

Usage:
  python3 scripts/build_index.py            # use signals stored in registry.json
  python3 scripts/build_index.py --refresh  # re-fetch signals from the GitHub API

Signals are deliberately shallow: stars, recency, packaging artefacts, tests, license.
They measure *maintenance and packaging*, not design quality. A hands-on benchmark
(fixed briefs, same harness, published renders) is the v0.2 work.
"""
import json
import math
import os
import sys
import urllib.request
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "registry.json")
SNAPSHOT_DIR = os.path.join(ROOT, "data", "snapshots")
README = os.path.join(ROOT, "README.md")


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


def refresh(entry):
    name = entry["repo"]
    d = api(f"/repos/{name}")
    tree = api(f"/repos/{name}/git/trees/{d['default_branch']}?recursive=1").get("tree", [])
    paths = [t["path"] for t in tree]
    low = " ".join(paths).lower()
    entry["signals"] = {
        "stars": d["stargazers_count"],
        "forks": d["forks_count"],
        "pushed": d["pushed_at"][:10],
        "created": d["created_at"][:10],
        "files": len(paths),
        "skill_md": any(p.lower().endswith("skill.md") for p in paths),
        "design_md": any(p.lower().endswith("design.md") for p in paths),
        "plugin": any(p.lower().endswith(("plugin.json", "marketplace.json")) for p in paths),
        "tests": any(k in low for k in ("/test", "/eval", "/bench")),
        "ci": ".github/workflows" in low,
        "license": (d.get("license") or {}).get("spdx_id"),
        "topics": d.get("topics") or [],
        "archived": bool(d.get("archived")),
    }
    return entry


def days_since(date_str, today):
    return (today - datetime.date.fromisoformat(date_str)).days


def score(sig, today):
    """0-100. Weights are fixed and published; see METHODOLOGY.md."""
    age = days_since(sig["pushed"], today)
    activity = 25 if age <= 7 else 20 if age <= 30 else 12 if age <= 90 else 5 if age <= 180 else 0

    packaged = (8 if sig["skill_md"] else 0) + (4 if sig["design_md"] else 0) \
        + (4 if sig["plugin"] else 0) + (4 if sig["files"] >= 20 else 0)

    engineering = (8 if sig["tests"] else 0) + (4 if sig["ci"] else 0) \
        + (3 if sig.get("license") not in (None, "NONE", "NOASSERTION") else 0)

    adoption = min(25, round(6 * math.log10(max(sig["stars"], 1))))

    docs = 15 if sig["files"] >= 200 else 10 if sig["files"] >= 50 else 5

    return {
        "total": activity + packaged + engineering + adoption + docs,
        "activity": activity,
        "packaged": packaged,
        "engineering": engineering,
        "adoption": adoption,
        "docs": docs,
    }


def fmt(n):
    return f"{n:,}"


def short(text, n=84):
    text = " ".join((text or "").split()).replace("|", "\\|")
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def table(rows, today, desc=False):
    if desc:
        out = ["| # | Project | What it does | Score | Stars | Updated | License |",
               "|---|---|---|---:|---:|---|---|"]
    else:
        out = ["| # | Project | Score | Stars | Updated | License |",
               "|---|---|---:|---:|---|---|"]
    for i, e in enumerate(rows, 1):
        s = e["signals"]
        base = (f"[{e['repo']}](https://github.com/{e['repo']})")
        if desc:
            out.append(
                f"| {i} | {base} | {short(e.get('author_desc'))} | {e['score']} | {fmt(s['stars'])} | "
                f"{s['pushed']} | {s.get('license') or '—'} |"
            )
        else:
            out.append(
                f"| {i} | {base} | {e['score']} | {fmt(s['stars'])} | "
                f"{s['pushed']} | {s.get('license') or '—'} |"
            )
    return "\n".join(out)


def main():
    entries = json.load(open(REGISTRY))
    today = datetime.date.today()

    if "--refresh" in sys.argv:
        entries = [refresh(e) for e in entries]

    for e in entries:
        e["score_detail"] = score(e["signals"], today)
        e["score"] = e["score_detail"]["total"]
        e["stale"] = days_since(e["signals"]["pushed"], today) > 180

    live = [e for e in entries if not e["signals"].get("archived")]
    skills = sorted([e for e in live if e["category"] == "skill"], key=lambda x: (-x["score"], -x["signals"]["stars"]))
    colls = sorted([e for e in live if e["category"] == "collection"], key=lambda x: (-x["signals"]["stars"]))
    exts = sorted([e for e in live if e["category"] in ("extractor", "spec")], key=lambda x: (-x["score"], -x["signals"]["stars"]))

    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    snap = {
        "generated_at": today.isoformat(),
        "method": "v0.1-signals",
        "counts": {"skills": len(skills), "collections": len(colls), "extractors": len(exts)},
        "entries": entries,
    }
    with open(os.path.join(SNAPSHOT_DIR, f"{today.isoformat()}.json"), "w") as f:
        json.dump(snap, f, ensure_ascii=False, indent=1)

    doc = f"""# Design Agent Index

**What design capability actually ships inside your coding agent — measured, dated, and open.**

`{today.isoformat()}` · {len(skills)} skills · {len(colls)} DESIGN.md collections · {len(exts)} extractors & specs

---

## What this is

A reproducible index of the packages that give coding agents design ability: `SKILL.md` packs, `DESIGN.md`
corpora, and the tools that extract a design system from a live site.

## What this is **not**

- **Not a quality ranking.** These are *signal* scores: maintenance, packaging, tests, adoption. Whether a skill
  actually produces good UI is not measured here — a hands-on benchmark (same briefs, same harness, published
  renders) is the next version. Treat the score as "is this maintained and installable", not "is this good".
- **Not pay-to-play.** No sponsored rows, no affiliate links, no vendor submissions that skip the criteria.
- **Not exhaustive.** Inclusion requires a design-related description **and** a `SKILL.md` / `DESIGN.md`
  artefact in the repo. Plenty of good work is excluded by that rule; open an issue and it gets reviewed.

## Scoring (v0.1)

| Signal | Weight | Rule |
|---|---:|---|
| Activity | 25 | pushed ≤7d 25 · ≤30d 20 · ≤90d 12 · ≤180d 5 · else 0 |
| Packaging | 20 | `SKILL.md` 8 · `DESIGN.md` 4 · plugin/marketplace manifest 4 · ≥20 files 4 |
| Engineering | 15 | tests/evals 8 · CI 4 · OSI license 3 |
| Adoption | 25 | `min(25, round(6 × log10(stars)))` |
| Docs surface | 15 | ≥200 files 15 · ≥50 10 · else 5 |

Full rules, inclusion criteria and known biases: [METHODOLOGY.md](METHODOLOGY.md).
### Benchmark (v0.2, in progress)

Signal scores say whether a skill is maintained, not whether it designs well. The bench runs the **same 12
briefs** through each skill with one model and publishes the renders, screenshots and a deterministic score
(contrast, responsiveness, typography, colour discipline, anti-slop heuristics). Harness and rubric:
[`bench/`](bench/README.md). First pilot cell is committed under `bench/runs/`.
Raw data for this snapshot: [`data/snapshots/{today.isoformat()}.json`](data/snapshots/{today.isoformat()}.json).

## Skills

{table(skills, today, desc=True)}

## DESIGN.md collections

Corpora of design systems you can drop into an agent. Ranked by stars — a collection's value is coverage, not commits.

{table(colls, today)}

## Extractors & specs

Tools that turn a live site (or a brand) into a `DESIGN.md`, plus the format spec itself.

{table(exts, today, desc=True)}

## Get listed / correct a row

Open an issue with the repo URL. A row is added when it has a design-related description and a `SKILL.md`
or `DESIGN.md` in the default branch. Corrections to stars/licence/date are regenerated automatically.

## Disclosure

Maintained by [Jakin](https://github.com/jkin8010), who builds image-editing tools at [QiseTech](https://qise.tech).
Any project of his that appears here is marked in its row; it gets no scoring bonus and is excluded from the
top of the table by the same rules as everyone else.

## License

Data and text: CC BY 4.0. Scripts: MIT.
"""
    open(README, "w").write(doc)
    print(f"snapshot {today} — skills={len(skills)} collections={len(colls)} extractors={len(exts)}")
    print("top 5:", ", ".join(f"{e['repo']}({e['score']})" for e in skills[:5]))


if __name__ == "__main__":
    main()