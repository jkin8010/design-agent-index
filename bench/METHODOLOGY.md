# Benchmark methodology (v0.2, method-only release)

This document describes **how** design skills for coding agents are measured. It contains no
leaderboard. The first ranked release will be published only after the conditions in
[§10](#10-what-would-make-a-ranking-publishable) are met, and it will carry its model id, date, N and
spread next to every number.

Why method first: a score table is cheap to produce and easy to fake. A method that others can
re-run is the only part that survives scrutiny. If the harness is wrong, every ranking built on it
is wrong — so the harness ships first.

---

## 1. What this measures, and what it does not

**Measures** — properties of a rendered page that a script can check without taste: does it render
without errors, does it hold together at 375px, is the text readable, is the type and colour set
disciplined, does it avoid a known set of AI-default tells, is the markup structured, is the file
sane in size.

**Does not measure** — whether the composition is good, whether the hierarchy matches the brief's
intent, whether a designer would sign it off. Evidence that this distinction is real: in round 1 the
`control` page (no skill) looked more distinctive to a human reviewer than the highest-scoring skill
page, and still scored 10 points lower because it overflowed at 375px. The score measured hygiene;
the eye measured taste. Both were correct.

**Consequence** — a high score means "nothing is broken", not "this is good design". Any published
ranking must say so in the same paragraph as the numbers, not in a footnote.

## 2. The briefs

Twelve briefs, each pinning a different kind of page:

| # | Brief | Why it is in the set |
|---|---|---|
| 01 | SaaS landing page | marketing composition, the most discriminative brief so far |
| 02 | Analytics dashboard | dense application UI, KPI cards, chart, table |
| 03 | Pricing page | three-plan comparison, highlight state, FAQ |
| 04 | Mobile onboarding | 375px-first, progress, option cards (saturated: see §9) |
| 05 | API documentation | sidebar + prose + code block readability |
| 06 | Product detail | gallery + purchase panel, variant selection |
| 07 | Long-form article | measure, rhythm, pull quote, footnotes |
| 08 | Admin data table | density, status chips, empty state, pagination |
| 09 | Auth + error states | trust, inline errors, rate-limit copy |
| 10 | 16:9 slide | a non-web medium, letterboxed at any viewport |
| 11 | Status page | calm factual tone under incident |
| 12 | Portfolio case study | evidence-led narrative layout |

A brief that every skill passes is dead weight. Round 1 showed brief 04 saturating (min 91/100) —
it will be rotated out of the working matrix and replaced by 03/06.

## 3. Fixed copy, fixed constraints

Every brief pins its copy **verbatim**: headline, body, numbers, button labels. The same words appear
in every cell, so a difference between two cells is a design difference, not a copywriting difference.

Hard constraints, identical everywhere:

- one self-contained `index.html`, no build step
- no CDN, no external fonts, no external images, no JS libraries
- system font stack only; imagery must be CSS/SVG the model writes itself
- usable at 375px and 1440px; no horizontal scrolling at 375px

These constraints exist to remove excuses: with no assets to download, a weak page is a design
failure rather than a sourcing failure.

## 4. A cell

```
runs/<batch>/<skill>/<brief>[__rN]/
  prompt.md      exactly what the agent was asked (brief + skill hint + constraints)
  index.html     the deliverable
  meta.json      model, CLI version, skill commit, installed skills, duration, exit code
  metrics.json   playwright measurements
  score.json     0–100 with the component breakdown
  content.json   copy-fidelity result (pass/fail + missing strings)
  shot-1440.jpg  full-page render at 1440px
  shot-375.jpg   full-page render at 375px
```

A cell is one `(skill, brief)` pair. `control` is the same cell with **no skill installed** — without
it, "89" is a number with no meaning.

## 5. Isolation

The most common way a benchmark like this becomes fiction is contamination by the operator's own
setup. Three defences:

1. **Clean config directory.** `CLAUDE_CONFIG_DIR` points at a generated directory holding only the
   auth/model `env` block. Personal plugins and global skills are stripped. Without this, every cell
   silently inherits whatever the operator happens to have installed.
2. **Generic skill installation.** Clone the skill repo shallow, walk it for every directory
   containing `SKILL.md`, and expose each under `.claude/skills/`. No assumption that the skill lives
   at the repo root; a 26-skill bundle is installed as 26 skills.
3. **Recorded provenance.** `meta.json` stores the skill's commit SHA, the CLI version and the model
   id. A run that cannot name its inputs cannot be compared to anything.

Installed skills are symlinked, not copied: one skill can be 100MB, and a matrix would otherwise
consume gigabytes. Installed copies are never committed.

## 6. The stop rule

Each cell gets a fixed wall-clock budget (900s in round 1, **1200s** from round 2). When the budget
expires the process group is killed and **whatever is on disk is scored**. `exit_code: "timeout"` is
recorded and reported alongside the score.

This rule matters more than it looks. Agents keep polishing after their first write — one round-1
cell grew from 14KB to 42KB after it was first measured, and an early version of this harness scored
the stale file. The current harness refuses to measure a cell until `meta.json` exists.

The budget is a shared, published condition, not a hidden advantage: reading a large skill costs
minutes, and 4 of 20 skill cells in round 1 hit the cap. A longer budget may change results; that is
stated, not hidden.

## 7. Measurement

Playwright, Chromium, two viewports (1440×900 and 375×812), full-page screenshots plus:

- console errors and page errors
- external network requests (should be zero by constraint)
- `scrollWidth > innerWidth` at 375px → overflow
- clickable elements smaller than 44×44
- computed font families, font sizes, text colours, background colours
- semantic landmarks and `h1` count
- body size in bytes

Text contrast is computed from computed styles, not from the screenshot: for every element holding a
text node, take its colour, walk ancestors to the first opaque background, and compute the WCAG
ratio. Modern CSS returns `oklch()` and `#hex` and `rgb()`; the parser handles all of them (a
colour-space bug in round 1 awarded full marks to an unmeasured cell — see §9).

## 8. Scoring

Fixed weights, deterministic, recomputable by a third party from `metrics.json` alone:

| Dimension | Weight | Rule |
|---|---:|---|
| Render | 10 | no console errors |
| Responsive | 15 | no 375px overflow (10) · tap targets ≥44px (5) |
| Contrast | 15 | share of text runs meeting 4.5:1; **unmeasurable scores 0, never full marks** |
| Typography | 10 | ≤3 font families (5) · 4–9 distinct sizes (5) |
| Colour discipline | 10 | ≤8 background colours (5) · ≤5 text colours (5) |
| Anti-slop | 20 | −6 purple/violet gradient · −4 backdrop-filter · −3 gradient text · −3 emoji in copy · −1 per buzzword (max 4) |
| Structure | 10 | exactly one `h1` (5) · ≥4 semantic landmarks (5) |
| Weight | 10 | ≤300KB (10) · ≤600KB (6) · else 2 |

`score.py` reads only `metrics.json`. No model judgement enters the score.

**The anti-slop rules are heuristics, not verdicts.** A purple gradient is not automatically bad; the
penalty is a warning light. This is stated here so a reader can discount those 20 points.

## 9. Content fidelity is a gate, not points

A page can be beautiful and ignore half the brief. `check_content.py` verifies that each brief's
pinned strings are present in the rendered text, and reports pass/fail **next to** the score.

It is deliberately not folded into the score: mixing "obeyed the brief" with "did not break" produces
a number that means neither. Round 1: 24/24 cells passed. The first version of the checker failed
three cells because it did not strip HTML tags and read `explained<span>.` as missing copy — a false
positive caught before publication, which is the reason this gate is reported raw (missing strings
listed) rather than as a silent boolean.

## 10. Repetition, aggregation, and what would make a ranking publishable

One generation per cell is noise. From round 2, every cell runs **N=3**, and the published number is
the **median**, with min and max shown. A skill whose three runs span 20 points has not been measured,
it has been sampled.

Before a ranked table is published, all of the following must hold:

1. **Model named in the title.** Scores compare skills *on one model*. A ranking without a model id is
   not a ranking, it is a rumour.
2. **N≥3 with spread shown** for every cell.
3. **Control in the same table.** A skill 2 points above control, with a 10-point spread, has
   demonstrated nothing.
4. **Copy gate green** for every cell, or the failures listed.
5. **Budget and date stated**, and all cells from one batch.
6. **Bias section included** (§11), not linked from a footnote.

If those conditions are not met, this repo publishes method, not results.

## 11. Known biases and threats to validity

- **One model.** Round 1–2 use a single model (`deepseek-v4.1-flash-1017` via a Qianwen-compatible
  endpoint). A skill that helps this model may not help another. Cross-model comparison is invalid
  unless both models are run on the same briefs.
- **One generation per cell in round 1.** Superseded by N=3, but round-1 numbers carry that caveat.
- **Skill invocation is advisory.** The prompt says a skill is installed and to follow it; the agent
  decides how much. Results measure "skill + agent judgement", not the skill alone.
- **Prompt adherence is compliance, not design.** A skill that produces a plain but obedient page can
  outscore a distinctive page that drops a required string.
- **Slop heuristics are crude** (§8). `backdrop-filter` is a legitimate technique.
- **Timing budget interacts with skill size.** Big skills spend minutes reading before writing; the
  cap is a confounder, reported per cell as `exit_code: "timeout"`.
- **Machine contention.** Cells run concurrently (2–3 at a time); a heavily loaded machine produces
  more timeouts, which is a runtime artifact, not a skill property.
- **Screenshots are JPEG q85.** Fine for review, not for pixel-level judgement.

## 12. Reproduce

```bash
# one cell
python3 bench/runner.py --skill hallmark --brief 01-saas-landing

# a matrix, three repetitions, three at a time
python3 bench/runner.py --skills control,hallmark --briefs 01-saas-landing,03-pricing \
  --repeat 3 --timeout 1200 --parallel 3 --post --date 2026-11-06-r2

python3 bench/check_content.py --date 2026-11-06-r2   # copy gate
python3 bench/score.py         --date 2026-11-06-r2   # deterministic scores
python3 bench/aggregate.py     --date 2026-11-06-r2   # medians + spread
python3 bench/report.py        --date 2026-11-06-r2   # gallery + report
```

Requirements: Python 3.12, Playwright with Chromium, and a coding-agent CLI that can run headless
(`claude -p` by default, `--agent codex` to switch).

## 13. Data and corrections policy

- Raw cells for a published batch live under `bench/results/<batch>/` with prompts, metrics and
  screenshots. Unpublished batches are not committed.
- **No paid placement, no sponsored inclusion, no ranking of our own products without marking them
  "our product" and separating them from the main table.**
- Corrections are made in the open: a wrong number is fixed in a commit that says what was wrong and
  why, not silently overwritten.
- If a skill's maintainer disputes a result, the reply links to the cell's `prompt.md`, `meta.json`,
  `metrics.json` and screenshots. The data is the argument.