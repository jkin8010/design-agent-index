# Methodology (v0.1)

## Scope

Included: repositories that give a **coding agent** design capability.

| Category | Definition |
|---|---|
| `skill` | A package installed into a coding agent (Claude Code, Codex, Cursor, Gemini CLI, …) that changes how it designs: layout, typography, colour, motion, brand, review. |
| `collection` | A corpus of `DESIGN.md` files or design-system descriptions meant to be read by an agent. |
| `extractor` | A tool that produces a `DESIGN.md` / design system from a live site, screenshot, Figma file or brand URL. |
| `spec` | The format definition itself. |

Excluded: component libraries, UI kits, boilerplates, human-facing design tools, prompt dumps with no artefact,
and anything that is a *product* rather than a capability you install.

## Inclusion rules

A repository enters the index when **all** of these hold:

1. Public, not archived, pushed within the last 180 days at snapshot time.
2. Description matches a design vocabulary (design, UI, UX, visual, brand, motion, typography, layout, slop, taste).
3. The default branch contains `SKILL.md`, `DESIGN.md`, or a plugin/marketplace manifest.
4. ≥50 stars at snapshot time (below that, noise dominates; the threshold drops as the index matures).

Rules are enforced by a human-reviewed registry (`registry.json`), not by a fully automatic crawler. Candidate
discovery is automatic (see `scripts/discover.py`); admission is not. This is deliberate — a keyword crawler
admits PCB-design and FPGA-design repos, which is exactly the failure mode that makes most "AI tool" lists useless.

## Scoring

| Signal | Weight | Rule | Why |
|---|---:|---|---|
| Activity | 25 | ≤7d 25 · ≤30d 20 · ≤90d 12 · ≤180d 5 · else 0 | A design skill that has not moved in six months has probably stopped tracking model changes. |
| Packaging | 20 | `SKILL.md` 8 · `DESIGN.md` 4 · plugin manifest 4 · ≥20 files 4 | The artefact is the product. A 3-file prompt dump scores low by construction. |
| Engineering | 15 | tests/evals 8 · CI 4 · OSI license 3 | Evals are the only public evidence of intent to measure output. |
| Adoption | 25 | `min(25, round(6 × log10(stars)))` | Log scale: 100★ = 12, 1k★ = 18, 10k★ = 24. Stars are a proxy for use, not for quality. |
| Docs surface | 15 | ≥200 files 15 · ≥50 10 · else 5 | Repo size correlates with a real system (rules, references, examples) rather than a single prompt. |

Weights sum to 100. All inputs are re-computed from the GitHub API at snapshot time and stored verbatim in
`data/snapshots/<date>.json`, so any row can be re-derived.

## Known biases

- **Stars are gameable and age-biased.** A 2026 repo can out-star a 2019 repo in a month.
- **File count rewards vendored assets.** A skill that bundles a 5,000-file fixture library scores like a real system.
- **English-language descriptions are over-represented** in the discovery queries; Chinese and Japanese repos surface
  only through specific queries (`design.md`, `设计`, explicit seeds).
- **No output quality signal exists yet.** The score cannot distinguish a skill that produces restrained, shippable UI
  from one that produces purple-gradient slop.

The last point is the point of v0.2: a fixed set of briefs, one harness, published renders and a published rubric.

## Roadmap

| Version | What changes |
|---|---|
| v0.1 (current) | Signal index, human-reviewed registry, weekly refresh of stars/dates/licence. |
| v0.2 | Hands-on benchmark: 12 briefs × top 20 skills, same model and harness, renders + scores published. |
| v0.3 | Category splits (web / mobile / slides / brand), per-category leaderboards, public harness for third-party runs. |

## Corrections

Open an issue with the repo URL and the claim that is wrong. Corrections to stars, dates and licence are
regenerated automatically; category and inclusion disputes are decided against the rules above, in public.
