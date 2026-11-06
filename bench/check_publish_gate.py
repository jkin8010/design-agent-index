#!/usr/bin/env python3
"""Publication gate for benchmark results.

Rules that live only in someone's head get forgotten. This script is the memory: it refuses a
batch that cannot be published under bench/RULES.md, and says exactly which condition failed.

  python3 bench/check_publish_gate.py --batch 2026-11-06-r2
  python3 bench/check_publish_gate.py --batch 2026-11-06-r2 --backfill-model   # derive model for old runs

Exit codes: 0 = publishable, 1 = fails the gate, 2 = batch still incomplete.
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys

BENCH = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(BENCH)


def load(path, default=None):
    try:
        return json.load(open(path))
    except Exception:  # noqa: BLE001
        return default


def clean_config_model():
    cfg = os.path.join(BENCH, ".cache", "claude-home", "settings.json")
    env = load(cfg, {}).get("env", {})
    return env.get("ANTHROPIC_MODEL") or env.get("ANTHROPIC_DEFAULT_SONNET_MODEL")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True)
    ap.add_argument("--backfill-model", action="store_true",
                    help="write the agent-config model into metas that predate model recording")
    args = ap.parse_args()

    base = os.path.join(BENCH, "runs", args.batch)
    if not os.path.isdir(base):
        base = os.path.join(BENCH, "results", args.batch)
    if not os.path.isdir(base):
        print(f"FAIL  batch not found: {args.batch}")
        return 1

    batch = load(os.path.join(base, "BATCH.json"), {})
    metas = sorted(glob.glob(os.path.join(base, "*", "*", "meta.json")))
    if not metas:
        print("FAIL  no cells found")
        return 1

    cells = []
    for mp in metas:
        cell_dir = os.path.dirname(mp)
        m = load(mp, {})
        dirname = os.path.basename(cell_dir)
        brief, _, tag = dirname.partition("__")
        m.setdefault("brief", brief)
        m["_tag"] = tag or "r1"
        m["_dir"] = cell_dir
        m["_brief"] = brief
        cells.append(m)

    checks = []

    def check(name, ok, detail=""):
        checks.append((name, bool(ok), detail))

    # --- model provenance
    model = batch.get("model") or next((c.get("model") for c in cells if c.get("model")), None)
    if args.backfill_model and not model:
        model = clean_config_model()
    missing_model = [c["_dir"] for c in cells if not c.get("model")]
    if args.backfill_model:
        derived = clean_config_model()
        for c in cells:
            if not c.get("model") and derived:
                m = load(os.path.join(c["_dir"], "meta.json"), {})
                m["model"] = derived
                m["model_source"] = "derived from agent config after the fact (runner did not record it)"
                json.dump(m, open(os.path.join(c["_dir"], "meta.json"), "w"), ensure_ascii=False, indent=1)
        missing_model = []
        model = model or derived
    check("model recorded", model and not missing_model,
          f"{model}" if model else "no cell records a model id")

    # --- completeness
    expected = None
    if batch:
        expected = len(batch.get("skills", [])) * len(batch.get("briefs", [])) * batch.get("repeat", 1)
        check("batch manifest", True, f"{batch.get('started','?')} · budget {batch.get('timeout_s','?')}s")
    else:
        check("batch manifest", False, "BATCH.json missing (batch predates manifest writing)")

    # --- repetition
    from collections import defaultdict
    reps = defaultdict(set)
    for c in cells:
        reps[(c["skill"], c["_brief"])].add(c["_tag"])
    thin = {k: len(v) for k, v in reps.items() if len(v) < 3}
    check("N>=3 per cell", not thin, f"{len(thin)} cells below 3 runs" + (f" e.g. {list(thin)[0]}" if thin else ""))

    # --- control present
    skills = {c["skill"] for c in cells}
    briefs = {c["_brief"] for c in cells}
    control_ok = "control" in skills and all(
        any(c["skill"] == "control" and c["_brief"] == b for c in cells) for b in briefs)
    check("control row", control_ok, "control missing for some briefs" if not control_ok else "present")

    # --- completeness vs expected
    if expected is not None:
        check("all cells present", len(cells) >= expected, f"{len(cells)}/{expected}")

    # --- copy gate
    bad_content = []
    for c in cells:
        cj = load(os.path.join(c["_dir"], "content.json"))
        if not cj or not cj.get("ok"):
            bad_content.append(c["_dir"])
    check("copy gate green", not bad_content,
          f"{len(bad_content)} cells missing pinned copy" if bad_content else "all cells verified")

    # --- artifacts
    broken = []
    for c in cells:
        ok = (os.path.getsize(os.path.join(c["_dir"], "index.html")) > 1000
              if os.path.exists(os.path.join(c["_dir"], "index.html")) else False)
        ok = ok and os.path.exists(os.path.join(c["_dir"], "metrics.json"))
        ok = ok and os.path.exists(os.path.join(c["_dir"], "score.json"))
        ok = ok and os.path.exists(os.path.join(c["_dir"], "shot-1440.jpg"))
        ok = ok and os.path.exists(os.path.join(c["_dir"], "shot-375.jpg"))
        if not ok:
            broken.append(c["_dir"])
    check("artifacts complete", not broken, f"{len(broken)} cells broken" if broken else "html+metrics+score+2 shots")

    # --- budget + date stamped
    check("budget + date stamped", bool(batch.get("timeout_s")) and bool(batch.get("started")),
          f"budget {batch.get('timeout_s','?')}s, started {batch.get('started','?')}")

    # --- method docs present
    method = os.path.join(BENCH, "METHODOLOGY.md")
    mtext = open(method, encoding="utf-8").read() if os.path.exists(method) else ""
    check("method + biases published",
          "Known biases" in mtext and "would make a ranking publishable" in mtext,
          "METHODOLOGY.md sections found" if mtext else "METHODOLOGY.md missing")

    # --- report, if present, must name the model
    reports = glob.glob(os.path.join(base, "MEDIAN.md")) + glob.glob(os.path.join(base, "REPORT.md"))
    if reports:
        rt = "".join(open(r, encoding="utf-8").read() for r in reports)
        check("report names model + N", bool(model) and model in rt and re.search(r"\bN=3\b|median of 3", rt, re.I) is not None,
              "report must state the model id and the repetition count")

    print(f"batch: {args.batch}   cells: {len(cells)}   model: {model or 'UNKNOWN'}")
    for name, ok, detail in checks:
        print(f"{'PASS ' if ok else 'FAIL '} {name:<26}{detail}")

    failed = [c for c in checks if not c[1]]
    incomplete = (not batch.get("finished_at")) or any(
        n == "all cells present" and not ok for n, ok, _ in checks)
    if failed:
        print(f"\nGATE: {'INCOMPLETE' if incomplete else 'FAIL'} ({len(failed)} check(s) failed)")
        return 2 if incomplete else 1
    print("\nGATE: PASS — publishable under bench/RULES.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())