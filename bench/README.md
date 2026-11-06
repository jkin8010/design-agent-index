# Design bench — methodology release (v0.2)

Same briefs. Same model. One design skill per cell. Renders published.

This is a **method-only release**. There is no leaderboard here, on purpose: a ranked table without a
named model, N≥3 repetitions and a control row is a rumour, not a measurement. The rules for when
results get published are written down in [`METHODOLOGY.md`](METHODOLOGY.md#10-what-would-make-a-ranking-publishable).

## What is here

| Path | What it is |
|---|---|
| [`METHODOLOGY.md`](METHODOLOGY.md) | the full method: briefs, isolation, stop rule, metrics, weights, biases, publication rules |
| `briefs/` | 12 fixed briefs, copy pinned verbatim |
| `runner.py` | runs one `(skill, brief)` cell, isolated, with a wall-clock budget |
| `measure.py` | Playwright measurements at 1440 and 375 |
| `score.py` | deterministic 0–100 from `metrics.json` alone |
| `check_content.py` | copy-fidelity gate, reported separately from the score |
| `aggregate.py` | median + spread across N repetitions |
| `report.py` | per-batch report and screenshot gallery |
| `example/` | one complete worked cell (control, brief 01) — prompt, HTML, metrics, score, both screenshots |

Raw cells for unpublished batches are not committed (`bench/runs/` is ignored). Published batches will
live under `bench/results/<batch>/`.

## Run one cell

```bash
python3 bench/runner.py --skill hallmark --brief 01-saas-landing
python3 bench/measure.py --date 2026-11-06
python3 bench/score.py   --date 2026-11-06
python3 bench/report.py  --date 2026-11-06
```

A full matrix with repetitions:

```bash
python3 bench/runner.py --skills control,hallmark,impeccable \
  --briefs 01-saas-landing,02-dashboard,03-pricing,08-admin-table \
  --repeat 3 --timeout 1200 --parallel 3 --post --date 2026-11-06-r2

python3 bench/check_content.py --date 2026-11-06-r2
python3 bench/score.py         --date 2026-11-06-r2
python3 bench/aggregate.py     --date 2026-11-06-r2   # medians + min/max
```

`--agent codex` swaps the CLI. The model comes from the operator's config and is recorded per cell in
`meta.json`; Claude Code runs against a **clean config directory** so personal plugins cannot
contaminate a cell.

## The worked example

`bench/example/01-saas-landing-control/` is the control cell for brief 01 with no skill installed. It
exists so the method can be inspected end to end — the exact prompt, the HTML, every metric, and the
score derived from those metrics — without publishing a comparison.

## Cost, measured

| Matrix | Cells | Sequential | At `--parallel 3` |
|---|---:|---:|---:|
| One cell | 1 | 10–14 min | — |
| Lean round, N=1 | 24 | ~4.5 h | ~1.7 h |
| Lean round, N=3 | 48 | ~9 h | ~3.5 h |
| Full 12×12, N=1 | 144 | ~26 h | ~9 h |

The full matrix is a weekend job, not a CI job.

## Status

Round 1 (24 cells, N=1) is done and is what the methodology was built from; its raw cells stay in git
history and are deliberately not published as a ranking. Round 2 (4 skills × 4 briefs × N=3, 1200s
budget) is the first batch that satisfies the publication conditions for repetition and control.

## Limits, stated up front

- scores measure hygiene (render, contrast, responsiveness, discipline), **not taste**
- one model only; comparisons are valid within a batch, never across models
- one generation per cell; N=3 medians replace single samples from round 2 on
- the anti-slop rules are heuristics — treat those 20 points as a warning light

Full bias list: [`METHODOLOGY.md` §11](METHODOLOGY.md#11-known-biases-and-threats-to-validity).
