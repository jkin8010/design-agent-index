# Design bench (v0.2, work in progress)

Same briefs. Same model. One design skill per cell. Renders published.

The index in the repo root measures whether a skill is *maintained*. This bench measures what it
actually *produces*. They are separate on purpose: stars and file counts cannot tell you whether the
output looks like a human designed it.

## How a cell is defined

```
bench/runs/<date>/<skill>/<brief>/
  prompt.md      exactly what the agent was asked (brief + skill hint + hard constraints)
  index.html     the deliverable, one self-contained file
  meta.json      model, CLI version, skill commit, duration, exit code
  metrics.json   objective measurements (playwright)
  score.json     the 0–100 score with its component breakdown
  shot-1440.png  render at 1440px
  shot-375.png   render at 375px
```

A *cell* is one (skill, brief) pair. The control cell has no skill installed — it is the baseline
every skill is measured against.

## The 12 briefs

Landing page · dashboard · pricing · mobile onboarding · API docs · product detail · long-form article ·
admin table · auth + error states · 16:9 slide · status page · case study.

Every brief pins the copy verbatim: same words in every cell, so differences come from design, not content.
Hard constraints are identical everywhere: one HTML file, no CDN, no external fonts or images, system fonts
only, CSS-only imagery, usable at 375px and 1440px, no horizontal scroll.

## Run it

```bash
# one cell
python3 bench/runner.py --skill hallmark --brief 01-saas-landing

# a matrix, 3 at a time
python3 bench/runner.py --skill all --brief all --parallel 3

# measure → score → report for whatever ran
python3 bench/measure.py --date 2026-11-06
python3 bench/score.py   --date 2026-11-06
python3 bench/report.py  --date 2026-11-06     # REPORT.md + gallery.html
```

`--agent codex` swaps the CLI. The model is taken from the operator's config and recorded in
`meta.json`; the harness runs Claude Code against a **clean config dir** (`bench/.cache/claude-home`,
auth env only) so personal plugins and skills cannot contaminate a cell. That detail is the difference
between a benchmark and a demo.

## What is measured (deterministic)

| Dimension | Weight | Rule |
|---|---:|---|
| Render | 10 | no console errors |
| Responsive | 15 | no 375px overflow (10) · tap targets ≥44px (5) |
| Contrast | 15 | share of text runs meeting 4.5:1, computed from computed styles (oklch included) |
| Typography | 10 | ≤3 font families (5) · 4–9 distinct sizes (5) |
| Colour discipline | 10 | ≤8 background colours (5) · ≤5 text colours (5) |
| Anti-slop | 20 | −6 purple/violet gradient · −4 backdrop-filter glass · −3 gradient text · −3 emoji in copy · −1 per buzzword (max 4) |
| Structure | 10 | exactly one `h1` (5) · ≥4 semantic landmarks (5) |
| Weight | 10 | ≤300KB full (10) · ≤600KB (6) |

Deliberately **not** measured yet: whether the composition is good, whether the hierarchy matches the
brief's intent, whether it would survive a real design review. That is the human/LLM review layer, and
it is not in v0.2.

## Cost and time, measured

The first pilot cell (`hallmark` × `01-saas-landing`) took **11 minutes** wall clock and produced a
27.8KB HTML file that scored 89/100.

| Matrix | Cells | Sequential | At `--parallel 3` |
|---|---:|---:|---:|
| Pilot (1 skill × 1 brief) | 1 | 11 min | — |
| Lean publish (6 × 4) | 24 | ~4.4 h | ~1.5 h |
| Full (12 × 12) | 144 | ~26 h | ~9 h |

The full matrix is a weekend job, not a CI job. v0.2 publishes the lean matrix; the full one runs when
there is a reason to.

## Known limitations

- **One generation per cell.** No best-of-N, so a single unlucky run can misrepresent a skill. v0.2.1 runs 3
  and takes the median.
- **The model is a variable.** A skill that helps one model may not help another. The model id is recorded
  per cell, and comparisons are only valid within the same date + model.
- **Skill invocation is advisory.** The prompt tells the agent the skill is installed and to follow it; the
  agent decides how much to use. That is realistic, but it means results measure "skill + agent judgement",
  not the skill alone.
- **The anti-slop heuristics are crude.** A purple gradient is not automatically bad. Treat that 20 points
  as a warning light, not a verdict.
- **No human review yet.** Nothing in v0.2 says "this looks like a designer made it".
