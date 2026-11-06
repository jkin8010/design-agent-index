# Brief 8: Admin data table

**Deliverable:** a single self-contained `index.html` in the workspace root.

**Hard constraints (apply to every brief):**
- One HTML file. No build step. No CDN, no external fonts, no external images, no JS libraries.
- System font stack only. Any imagery must be CSS-only (gradients, shapes, SVG you write inline).
- Must be usable at 375px and 1440px wide. No horizontal scrolling at 375px.
- All copy below must appear verbatim. Do not invent testimonials, logos, statistics or prices.
- No lorem ipsum. No placeholder text.

---

**Goal:** an operations table screen for support staff.

**Required:**
1. Toolbar: search field, status filter, "Export CSV" button.
2. Table with six rows and columns: Order, Customer, Status, Amount, Created.
3. Status chips with at least three distinct states (Paid, Pending, Refunded).
4. Pagination control at the bottom.
5. An empty state (shown as a separate block below the table, labelled "Empty state").

**Fixed copy:** six rows of plausible order data; amounts like "$128.00"; dates in "12 Mar 2026" form.

**Tone:** utilitarian. Density beats decoration; the row height should feel deliberate.

---

**When you are done:** write `index.html` and nothing else. Do not explain your choices in the file.


---

A design skill is installed at `.claude/skills/`: hallmark-skills-hallmark. Read it before you start and follow it. If it conflicts with the hard constraints above, the hard constraints win.
