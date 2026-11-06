# Brief 2: Analytics dashboard

**Deliverable:** a single self-contained `index.html` in the workspace root.

**Hard constraints (apply to every brief):**
- One HTML file. No build step. No CDN, no external fonts, no external images, no JS libraries.
- System font stack only. Any imagery must be CSS-only (gradients, shapes, SVG you write inline).
- Must be usable at 375px and 1440px wide. No horizontal scrolling at 375px.
- All copy below must appear verbatim. Do not invent testimonials, logos, statistics or prices.
- No lorem ipsum. No placeholder text.

---

**Goal:** an analytics dashboard screen for "Pulse", a product-analytics tool. This is an application screen, not a marketing page.

**Required elements:**
1. Top bar with product name, date-range control, and a user avatar.
2. Four KPI cards: "Active users 12,480 (+4.2%)", "Retention 38.1% (−0.8%)", "Events 4.2M (+11%)", "Error rate 0.42% (−0.05%)".
3. A chart area (draw it with inline SVG: a line chart with 12 points).
4. A table of five events: columns Event, Count, Users, Trend.
5. Left navigation with four items: Overview, Funnels, Retention, Settings.

**Fixed copy:** use the numbers above exactly. Table rows: "signup_completed 8,204 6,731 ↑", "checkout_started 3,918 3,102 ↑", "checkout_failed 412 388 ↓", "invite_sent 1,204 890 ↑", "export_created 268 201 ↑".

**Tone:** dense but calm; this is a tool someone stares at all day.

---

**When you are done:** write `index.html` and nothing else. Do not explain your choices in the file.


---

A design skill is installed at `.claude/skills/`: superdesign-skills-superdesign. Read it before you start and follow it. If it conflicts with the hard constraints above, the hard constraints win.
