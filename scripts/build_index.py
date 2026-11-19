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
import urllib.error
import glob
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
    meta_path = f"/repos/{name}"
    d = request_stage(name, "meta", meta_path)
    tree_path = f"/repos/{name}/git/trees/{d['default_branch']}?recursive=1"
    tree = request_stage(name, "tree", tree_path)["tree"]
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
    entry.pop("unavailable_at", None)
    entry.pop("missing", None)
    return entry


class RefreshError(Exception):
    def __init__(self, record):
        self.record = record
        super().__init__(str(record))


def request_stage(repo, stage, path):
    try:
        result = api(path)
        if stage == "meta":
            for key in ("default_branch", "stargazers_count", "forks_count", "pushed_at", "created_at"):
                if key not in result or result[key] is None:
                    raise ValueError(f"missing {key}")
        elif not isinstance(result.get("tree"), list) or any("path" not in item for item in result["tree"]):
            raise ValueError("invalid tree")
        if stage == "tree" and result.get("truncated"):
            raise ValueError("truncated tree")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, TypeError, AttributeError) as exc:
        status = exc.code if isinstance(exc, urllib.error.HTTPError) else None
        if isinstance(exc, (ValueError, TypeError, AttributeError)):
            kind = "invalid_response"
        elif status in (404, 410):
            kind = "unavailable"
        elif status in (401, 403):
            kind = "authentication"
        elif status == 429 or (status is not None and status >= 500):
            kind = "rate_limit_or_server"
        else:
            kind = "network" if status is None else "http_error"
        record = {"repo": repo, "url": "https://api.github.com" + path,
                  "http_status": status, "stage": stage,
                  "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "kind": kind, "message": str(exc)}
        print(f"{repo} {stage} {kind} status={status}", file=sys.stderr, flush=True)
        raise RefreshError(record) from exc
    print(f"{repo} {stage} ok", flush=True)
    return result


def previous_entries():
    """Read the latest snapshot, including its retained signals for failed entries."""
    files = sorted((p for p in glob.glob(os.path.join(SNAPSHOT_DIR, "*.json"))
                    if not p.endswith(".errors.json")),
                   key=lambda p: (os.path.basename(p)[:10], os.path.basename(p)[10:-5]))
    if not files:
        return {}
    with open(files[-1]) as f:
        return {entry["repo"]: entry for entry in json.load(f)["entries"]}


def snapshot_path(today):
    """Never overwrite a snapshot, even when multiple runs occur on the same day."""
    base = os.path.join(SNAPSHOT_DIR, today.isoformat())
    path = base + ".json"
    number = 1
    while os.path.exists(path) or os.path.exists(path[:-5] + ".errors.json"):
        path = f"{base}-{number:04d}.json"
        number += 1
    return path


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
        base = (f"[{e['repo']}](https://github.com/{e['repo']})"
                + (f" ⚠ unavailable since {e['unavailable_at']}" if e.get("unavailable_at") else ""))
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

    errors = []
    if "--refresh" in sys.argv:
        previous = previous_entries()
        for entry in entries:
            old = previous.get(entry["repo"], entry)
            try:
                refresh(entry)
            except RefreshError as exc:
                entry["signals"] = old["signals"]
                entry["unavailable_at"] = old.get("unavailable_at") or today.isoformat()
                entry["missing"] = True
                errors.append(exc.record)

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
    path = snapshot_path(today)
    with open(path, "x") as f:
        json.dump(snap, f, ensure_ascii=False, indent=1)
    if errors:
        with open(path[:-5] + ".errors.json", "x") as f:
            json.dump(errors, f, ensure_ascii=False, indent=1)

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

⚠ Unavailable rows retain their last recorded signals; their scores are recalculated for this date and may be stale.

Full rules, inclusion criteria and known biases: [METHODOLOGY.md](METHODOLOGY.md).
### Benchmark (v0.2 — methodology published, results deliberately withheld)

Signal scores say whether a skill is *maintained*, not whether it *designs well*. The bench runs the same 12
briefs through each skill on one model, screenshots both 1440px and 375px, and scores the render on eight
deterministic dimensions (contrast, responsiveness, typography, colour discipline, anti-slop heuristics).

**No leaderboard is published here yet.** A ranked table without a named model, N≥3 repetitions, a control
row and published spread is a rumour, not a measurement — [the method and its publication rules](bench/METHODOLOGY.md)
ship first, and one complete worked cell is in [`bench/example/`](bench/example/). What may be published, and
under which conditions, is written down in [`RULES.md`](RULES.md) and enforced by `bench/check_publish_gate.py`.
Raw data and refresh errors: [`data/snapshots/`](data/snapshots/).

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
    return 1 if any(e["kind"] != "unavailable" for e in errors) else 0


if __name__ == "__main__":
    sys.exit(main())