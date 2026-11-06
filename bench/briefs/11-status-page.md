# Brief 11: Status page

**Deliverable:** a single self-contained `index.html` in the workspace root.

**Hard constraints (apply to every brief):**
- One HTML file. No build step. No CDN, no external fonts, no external images, no JS libraries.
- System font stack only. Any imagery must be CSS-only (gradients, shapes, SVG you write inline).
- Must be usable at 375px and 1440px wide. No horizontal scrolling at 375px.
- All copy below must appear verbatim. Do not invent testimonials, logos, statistics or prices.
- No lorem ipsum. No placeholder text.

---

**Goal:** a public status page during a partial outage.

**Required:**
1. Overall banner: "Partial outage" with a timestamp "Last updated 09:42 UTC".
2. Component list with four services and their states (Operational, Degraded, Outage).
3. An incident timeline with three entries, newest first.
4. A subscribe block: email input and "Notify me" button.

**Fixed copy:**
- Services: "API — Degraded", "Dashboard — Operational", "Webhooks — Outage", "File uploads — Operational".
- Timeline: "09:42 — Webhook delivery is retrying; no data loss expected." / "09:18 — We are investigating elevated webhook latency." / "09:05 — Investigating."

**Tone:** calm and factual. This page is read by people whose systems are broken.

---

**When you are done:** write `index.html` and nothing else. Do not explain your choices in the file.
