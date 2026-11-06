#!/usr/bin/env python3
"""Structural checks for the repository itself.

This is what CI runs on a PR. It does not compare generated text byte-for-byte (the README carries
today's date and decays with the clock); it asserts the things that must stay true for the repo to
mean anything.

  python3 scripts/check_repo.py
"""
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATEGORIES = {"skill", "collection", "extractor", "spec"}

checks = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))


def read(rel):
    p = os.path.join(REPO, rel)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def main():
    # --- registry shape
    try:
        reg = json.load(open(os.path.join(REPO, "registry.json"), encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL  registry.json does not parse: {exc}")
        return 1
    check("registry parses", isinstance(reg, list) and len(reg) > 0, f"{len(reg)} entries")

    missing = []
    for e in reg:
        sig = e.get("signals") or {}
        ok = all(k in e for k in ("repo", "category", "author_desc")) \
            and e.get("category") in CATEGORIES \
            and isinstance(sig.get("stars"), int) \
            and isinstance(sig.get("pushed"), str) \
            and len(sig.get("pushed", "")) == 10
        if not ok:
            missing.append(e.get("repo", "<no repo>"))
    check("registry entries well-formed", not missing, f"{len(missing)} bad" if missing else "all entries have repo/category/signals")

    # --- entry without signals must not be live
    bad_live = [e["repo"] for e in reg if not (e.get("signals") or {}).get("pushed")]
    check("no live entry without pushed date", not bad_live, f"{len(bad_live)} bad" if bad_live else "ok")

    # --- generated README must keep its guardrails
    readme = read("README.md")
    need = ["what this is **not**", "pay-to-play", "rules.md", "bench/methodology.md", "no leaderboard is published"]
    low = readme.lower()
    absent = [n for n in need if n not in low]
    check("README keeps its guardrails", not absent, f"missing: {absent}" if absent else "disclaimer + rules links present")

    # --- rulebook present
    rules = read("RULES.md")
    for cond in ["No paid placement", "check_publish_gate.py", "hygiene, not taste"]:
        check(f"RULES.md: {cond[:28]}", cond in rules, "" if cond in rules else "missing from RULES.md")

    method = read("bench/METHODOLOGY.md")
    check("METHODOLOGY: biases + publication conditions",
          "Known biases" in method and "would make a ranking publishable" in method,
          "" if method else "bench/METHODOLOGY.md missing")

    # --- unpublished batches must not be committed
    try:
        tracked = subprocess.run(["git", "ls-files", "bench/runs"], cwd=REPO,
                                 capture_output=True, text=True).stdout.strip()
    except Exception:  # noqa: BLE001
        tracked = ""
    check("bench/runs not committed", not tracked, f"{len(tracked.splitlines())} files tracked" if tracked else "clean")

    # --- no secrets in tracked files
    secret_pat = re.compile(
        r"(sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
        r"|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----"
        r"|ANTHROPIC_(AUTH_TOKEN|API_KEY)\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{12,}"
        r"|(api[_-]?key|secret|password)\s*[=:]\s*['\"][A-Za-z0-9_\-]{16,}['\"])", re.I)
    tracked = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True).stdout.split()
    leaks, env_files = [], []
    for rel in tracked:
        if re.search(r"(\.env$|\.env\.(?!example)|\.pem$|id_rsa)", rel):
            env_files.append(rel)
        full = os.path.join(REPO, rel)
        if os.path.getsize(full) > 2_000_000:
            continue
        try:
            body = open(full, encoding="utf-8", errors="ignore").read()
        except Exception:  # noqa: BLE001
            continue
        if secret_pat.search(body):
            leaks.append(rel)
    check("no committed secrets", not leaks and not env_files,
          f"{leaks + env_files}" if (leaks or env_files) else f"{len(tracked)} files scanned")

    # --- every published batch must pass the publication gate
    results = os.path.join(REPO, "bench", "results")
    batches = sorted(d for d in os.listdir(results) if os.path.isdir(os.path.join(results, d))) \
        if os.path.isdir(results) else []
    for b in batches:
        p = subprocess.run([sys.executable, os.path.join(REPO, "bench", "check_publish_gate.py"), "--batch", b],
                           cwd=REPO, capture_output=True, text=True)
        check(f"published batch {b}", p.returncode == 0,
              "gate PASS" if p.returncode == 0 else f"gate exit {p.returncode}")
    if not batches:
        check("published batches", True, "none yet (nothing to gate)")

    for name, ok, detail in checks:
        print(f"{'PASS ' if ok else 'FAIL '} {name:<44}{detail}")
    failed = [c for c in checks if not c[1]]
    print(f"\n{'FAIL' if failed else 'OK'}: {len(failed)} failed / {len(checks)} checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())