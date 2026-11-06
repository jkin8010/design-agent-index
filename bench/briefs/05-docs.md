# Brief 5: API documentation page

**Deliverable:** a single self-contained `index.html` in the workspace root.

**Hard constraints (apply to every brief):**
- One HTML file. No build step. No CDN, no external fonts, no external images, no JS libraries.
- System font stack only. Any imagery must be CSS-only (gradients, shapes, SVG you write inline).
- Must be usable at 375px and 1440px wide. No horizontal scrolling at 375px.
- All copy below must appear verbatim. Do not invent testimonials, logos, statistics or prices.
- No lorem ipsum. No placeholder text.

---

**Goal:** a documentation page for a fictional API endpoint. Layout matters more than prose.

**Required:**
1. Left sidebar with grouped links: "Getting started" (Authentication, Rate limits), "Endpoints" (Create a charge, Retrieve a charge, Refund), "Webhooks".
2. Main column: page title "Create a charge", one-paragraph description, a code block with a curl example, a parameters table with five rows, and a "Response" section with a JSON block.
3. Right-hand "On this page" anchor list.

**Fixed copy:**
- Description: "Creates a charge against a payment method. Amounts are in the smallest currency unit."
- Code block: `curl https://api.example.com/v1/charges -u sk_test_51: -d amount=1200 -d currency=usd`
- Parameters: amount (integer, required), currency (string, required), customer (string, optional), description (string, optional), capture (boolean, optional).

**Tone:** technical, terse. Monospace must be genuinely readable.

---

**When you are done:** write `index.html` and nothing else. Do not explain your choices in the file.
