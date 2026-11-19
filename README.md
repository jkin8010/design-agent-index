# Design Agent Index

**What design capability actually ships inside your coding agent — measured, dated, and open.**

`2026-11-19` · 37 skills · 11 DESIGN.md collections · 6 extractors & specs

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

| # | Project | What it does | Score | Stars | Updated | License |
|---|---|---|---:|---:|---|---|
| 1 | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | An AI skill that provides design intelligence for building professional UI/UX acros… | 100 | 151,578 | 2026-11-19 | MIT |
| 2 | [kaankiziltug/logo-design-skill](https://github.com/kaankiziltug/logo-design-skill) | A comprehensive logo-design skill for Claude, Gemini CLI, Codex and other AI agents… | 98 | 7,329 | 2026-11-13 | MIT |
| 3 | [kwakseongjae/oh-my-design](https://github.com/kwakseongjae/oh-my-design) | Give your AI coding agent a design system. One command installs 500+ quality-graded… | 88 | 594 | 2026-11-16 | MIT |
| 4 | [Nutlope/hallmark](https://github.com/Nutlope/hallmark) | Anti-AI-slop design skill for Claude Code, Cursor, and Codex. | 87 | 57,808 | 2026-11-11 | MIT |
| 5 | [alchaincyf/huashu-design](https://github.com/alchaincyf/huashu-design) | Huashu Design 3.0 · 在 agent 里打一句话，拿回能交付的设计：网页 / App 原型 / 可编辑 PPTX / 动画 / 信息图 · 六个候选… | 83 | 29,861 | 2026-11-10 | MIT |
| 6 | [oil-oil/oil-ui](https://github.com/oil-oil/oil-ui) | UI design skill for Claude Code, Codex and other AI agents: explore distinct direct… | 83 | 3,539 | 2026-11-18 | MIT |
| 7 | [arla6ka/design.how](https://github.com/arla6ka/design.how) | Design systems, skills and visuals for coding agents | 76 | 575 | 2026-11-18 | MIT |
| 8 | [Vieeeeeee/wibi-style](https://github.com/Vieeeeeee/wibi-style) | 47 installable visual-design skills for Codex, with reusable Python tooling and ver… | 73 | 188 | 2026-11-07 | NOASSERTION |
| 9 | [oil-oil/beautify-github-readme](https://github.com/oil-oil/beautify-github-readme) | README design skill for Claude Code & Codex. 帮你把 GitHub README 做得好看又好懂。 | 70 | 1,993 | 2026-11-16 | MIT |
| 10 | [sunchaokun/PPT-Design-Skill](https://github.com/sunchaokun/PPT-Design-Skill) | Precision PPT design skill for OpenCode/Claude Code/Codex, with 40,000+ styles, pix… | 70 | 510 | 2026-09-16 | MIT |
| 11 | [murphytrueman/design-system-ops](https://github.com/murphytrueman/design-system-ops) | Claude Code skills for the work that keeps a design system alive | 67 | 221 | 2026-09-24 | MIT |
| 12 | [joeseesun/qiaomu-design](https://github.com/joeseesun/qiaomu-design) | 偏执型设计顾问：反 AI 味设计 + 风格试衣间 + 58 站设计系统库的 Claude Code Skill \| Opinionated design advis… | 66 | 691 | 2026-10-13 | MIT |
| 13 | [Owl-Listener/ai-design-skills](https://github.com/Owl-Listener/ai-design-skills) | AI Design Skills Collection: agentic skills, commands, and plugins for designing AI… | 65 | 207 | 2026-06-09 | MIT |
| 14 | [dominikmartn/hue](https://github.com/dominikmartn/hue) | open-source skill that learns any brand and turns it into a complete design system.… | 63 | 923 | 2026-11-10 | MIT |
| 15 | [touchine-ojo/OJO-Design-Skills](https://github.com/touchine-ojo/OJO-Design-Skills) | Reusable UI/UX design skills for AI coding agents — Codex, Claude Code, ZCode, and… | 63 | 193 | 2026-11-01 | MIT |
| 16 | [ehmo/slopkit](https://github.com/ehmo/slopkit) | Anti-slop skills for AI agents: slopbeth cleans the shipped writing, slopgent clean… | 63 | 115 | 2026-07-22 | MIT |
| 17 | [cuellarfr/design-skills](https://github.com/cuellarfr/design-skills) | UX and design skills for Claude Code — research, critique, accessibility, journey m… | 62 | 127 | 2026-09-30 | MIT |
| 18 | [agiwhitelist/auteur](https://github.com/agiwhitelist/auteur) | The Claude Code skill that directs a website like a film. Commit-sheet, generated a… | 60 | 1,056 | 2026-08-06 | MIT |
| 19 | [superdesigndev/superdesign-skill](https://github.com/superdesigndev/superdesign-skill) | The design skill for Claude Code, Cursor and any coding agent. Stop shipping AI-slo… | 58 | 1,027 | 2026-08-21 | MIT |
| 20 | [referodesign/refero_skill](https://github.com/referodesign/refero_skill) | Research-first design skill for AI agents. 150K+ real app screens and flows via Ref… | 55 | 356 | 2026-10-15 | MIT |
| 21 | [uxKero/anydesign](https://github.com/uxKero/anydesign) | Claude skill that analyzes images, websites, and Figma files and generates a struct… | 55 | 249 | 2026-09-15 | MIT |
| 22 | [SpaceZephyr/design-buddy](https://github.com/SpaceZephyr/design-buddy) | Design Buddy: visual production Agent Skills for brand design systems, GPT-image-2… | 54 | 189 | 2026-07-06 | — |
| 23 | [cth9191/motion-design](https://github.com/cth9191/motion-design) | Motion design skill for Codex and Claude Code. Adapt source examples into complete… | 53 | 283 | 2026-09-06 | — |
| 24 | [Nutlope/variate](https://github.com/Nutlope/variate) | A compact design skill that generates four design variations of a component to iter… | 52 | 222 | 2026-08-20 | MIT |
| 25 | [ceorkm/mobile-app-ui-design](https://github.com/ceorkm/mobile-app-ui-design) | Professional mobile app UI/UX design skill for Claude Code | 50 | 567 | 2026-10-28 | — |
| 26 | [zeke/swiss-design-skill](https://github.com/zeke/swiss-design-skill) | A Swiss International Style design system skill for AI agents | 50 | 164 | 2026-09-24 | MIT |
| 27 | [tasteskill/tasteskill](https://github.com/tasteskill/tasteskill) ⚠ unavailable since 2026-11-19 | The Anti-Slop Frontend Framework for AI Agents | 49 | 329 | 2026-05-24 | MIT |
| 28 | [MickeyAlton33/web-designer-plugin](https://github.com/MickeyAlton33/web-designer-plugin) | Award-winning web design skill for Claude Code. 48 patterns from 38 top websites. S… | 46 | 116 | 2026-06-10 | MIT |
| 29 | [kylezantos/design-motion-principles](https://github.com/kylezantos/design-motion-principles) | A motion design skill with two modes — build interactive components with purposeful… | 44 | 1,610 | 2026-05-30 | MIT |
| 30 | [content-designer/ux-writing-skill](https://github.com/content-designer/ux-writing-skill) | Agent Skill for systematic UX writing — scale content quality through AI-powered de… | 44 | 265 | 2026-05-26 | MIT |
| 31 | [Ilm-Alan/frontend-design](https://github.com/Ilm-Alan/frontend-design) | Frontend design skill for Claude Code, Codex, and Gemini CLI. Eight aesthetic ancho… | 42 | 179 | 2026-09-26 | MIT |
| 32 | [moguzbulbul/blueprint-animation](https://github.com/moguzbulbul/blueprint-animation) | Claude Design skill: animated before → after UX redesign, explained step by step th… | 41 | 441 | 2026-09-27 | NOASSERTION |
| 33 | [ziguishian/brand-design-skill](https://github.com/ziguishian/brand-design-skill) | Brand Design Skill 是一个 image-first 的 Codex 品牌设计 Skill。它通过对话式流程引导 Agent 完成苏格拉底式需求澄清、… | 41 | 200 | 2026-06-27 | — |
| 34 | [jiji262/claude-design-skill](https://github.com/jiji262/claude-design-skill) | A portable Claude Skill that turns Claude into an expert designer for HTML artifact… | 39 | 221 | 2026-07-15 | MIT |
| 35 | [senlindesign/claude2figma](https://github.com/senlindesign/claude2figma) | An enforcement layer for Claude Code + Figma — 4 skills that keep AI on your Design… | 38 | 208 | 2026-05-13 | MIT |
| 36 | [ponyodong2026/ponyo-cover-anchor-system](https://github.com/ponyodong2026/ponyo-cover-anchor-system) | Xiaohongshu cover design skill: information density × visual anchors | 36 | 232 | 2026-06-22 | — |
| 37 | [alima-max/prototype-to-figma-skill](https://github.com/alima-max/prototype-to-figma-skill) | Claude skill: Prototype → Figma. Analyzes a Claude Code prototype, maps components… | 34 | 142 | 2026-07-28 | MIT |

## DESIGN.md collections

Corpora of design systems you can drop into an agent. Ranked by stars — a collection's value is coverage, not commits.

| # | Project | Score | Stars | Updated | License |
|---|---|---:|---:|---|---|
| 1 | [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) | 71 | 128,220 | 2026-10-28 | MIT |
| 2 | [VoltAgent/awesome-claude-design](https://github.com/VoltAgent/awesome-claude-design) | 35 | 4,618 | 2026-06-20 | MIT |
| 3 | [bergside/awesome-design-skills](https://github.com/bergside/awesome-design-skills) | 60 | 3,729 | 2026-06-28 | MIT |
| 4 | [kzhrknt/awesome-design-md-jp](https://github.com/kzhrknt/awesome-design-md-jp) | 73 | 1,019 | 2026-11-18 | MIT |
| 5 | [Meliwat/awesome-ios-design-md](https://github.com/Meliwat/awesome-ios-design-md) | 43 | 649 | 2026-05-21 | MIT |
| 6 | [VoltAgent/official-design-md](https://github.com/VoltAgent/official-design-md) | 36 | 533 | 2026-09-21 | MIT |
| 7 | [Khalidabdi1/design-ai](https://github.com/Khalidabdi1/design-ai) | 52 | 253 | 2026-09-28 | MIT |
| 8 | [ricocc/brands-design-md](https://github.com/ricocc/brands-design-md) | 42 | 180 | 2026-08-05 | — |
| 9 | [fchangjun/awesome-design-md-cn](https://github.com/fchangjun/awesome-design-md-cn) | 45 | 152 | 2026-07-07 | — |
| 10 | [scroobius-pip/fudge-design-md](https://github.com/scroobius-pip/fudge-design-md) | 68 | 124 | 2026-11-16 | MIT |
| 11 | [ricocc/ricoui-design-md](https://github.com/ricocc/ricoui-design-md) | 43 | 116 | 2026-08-04 | Apache-2.0 |

## Extractors & specs

Tools that turn a live site (or a brand) into a `DESIGN.md`, plus the format spec itself.

| # | Project | What it does | Score | Stars | Updated | License |
|---|---|---|---:|---:|---|---|
| 1 | [google-labs-code/design.md](https://github.com/google-labs-code/design.md) | A format specification for describing a visual identity to coding agents. DESIGN.md… | 91 | 28,958 | 2026-11-18 | Apache-2.0 |
| 2 | [Railly/tinte](https://github.com/Railly/tinte) | Compile your design system into an Agent Plugin. Extract an identity from any refer… | 84 | 632 | 2026-11-17 | MIT |
| 3 | [fivetaku/insane-design](https://github.com/fivetaku/insane-design) | URL one-shot design system extractor — fetches real CSS, analyzes tokens, generates… | 67 | 135 | 2026-10-13 | MIT |
| 4 | [bergside/design-md-chrome](https://github.com/bergside/design-md-chrome) | Chrome extension to extract styles from any website and generate DESIGN.md files an… | 42 | 3,194 | 2026-05-25 | MIT |
| 5 | [shaom/brand-to-design-md-skill](https://github.com/shaom/brand-to-design-md-skill) | A portable local skill that turns a public brand URL into a source-aware DESIGN.md,… | 40 | 212 | 2026-08-08 | — |
| 6 | [bergside/design-md-figma](https://github.com/bergside/design-md-figma) | Figma plugin that extracts local style guidelines and generates DESIGN.md and SKILL… | 38 | 159 | 2026-05-25 | MIT |

## Get listed / correct a row

Open an issue with the repo URL. A row is added when it has a design-related description and a `SKILL.md`
or `DESIGN.md` in the default branch. Corrections to stars/licence/date are regenerated automatically.

## Disclosure

Maintained by [Jakin](https://github.com/jkin8010), who builds image-editing tools at [QiseTech](https://qise.tech).
Any project of his that appears here is marked in its row; it gets no scoring bonus and is excluded from the
top of the table by the same rules as everyone else.

## License

Data and text: CC BY 4.0. Scripts: MIT.
