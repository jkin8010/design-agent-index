#!/usr/bin/env python3
"""Content fidelity check: does the page actually contain the copy the brief pinned?

The score rubric measures craft, not obedience. A page can be beautiful and still ignore
half the brief, so this runs separately and is reported as a gate, never folded into the score.

  python3 bench/check_content.py --date 2026-11-06
"""
import argparse
import glob
import json
import os
import re

BENCH = os.path.dirname(os.path.abspath(__file__))

REQUIRED = {
    "01-saas-landing": [
        "Every card swipe, explained.",
        "Auto-categorisation",
        "Duplicate detection",
        "Month-end close",
        "Connect your cards",
        "Export to your ledger",
        "Your books, before the deadline.",
    ],
    "02-dashboard": [
        "12,480", "38.1%", "4.2M", "0.42%",
        "signup_completed", "checkout_failed", "export_created",
        "Overview", "Funnels", "Retention", "Settings",
    ],
    "04-mobile-onboarding": [
        "Let's set up your view",
        "Daily spending", "Bills", "Savings goals", "Debt",
        "You can change this any time.",
        "Continue",
    ],
    "08-admin-table": [
        "Export CSV", "Paid", "Pending", "Refunded",
        "Empty state", "Order", "Customer", "Amount",
    ],
}


def page_text(path):
    html = open(path, encoding="utf-8", errors="ignore").read()
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    # Tag boundaries leave a space before punctuation ("explained ."), which would read as
    # missing copy. Normalise punctuation spacing and curly quotes before comparing.
    text = re.sub(r"\s+([,.;:!?…])", r"\1", text)
    return (text.replace("\u2019", "'").replace("\u2018", "'")
                .replace("\u201c", '"').replace("\u201d", '"'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()

    rows = []
    for f in sorted(glob.glob(os.path.join(BENCH, "runs", args.date, "*", "*", "index.html"))):
        skill = f.split(os.sep)[-3]
        brief = f.split(os.sep)[-2]
        need = REQUIRED.get(brief)
        if not need:
            continue
        text = page_text(f)
        missing = [n for n in need if n not in text]
        rec = {"skill": skill, "brief": brief, "required": len(need),
               "missing": missing, "ok": not missing}
        json.dump(rec, open(os.path.join(os.path.dirname(f), "content.json"), "w"), ensure_ascii=False, indent=1)
        rows.append(rec)

    for r in rows:
        mark = "ok  " if r["ok"] else f"MISS {len(r['missing'])}"
        print(f"{mark} {r['skill']:<16}{r['brief']:<22}" + ("" if r["ok"] else " → " + ", ".join(r["missing"][:4])))
    bad = sum(1 for r in rows if not r["ok"])
    print(f"\n{len(rows)} cells checked, {bad} with missing copy")


if __name__ == "__main__":
    main()