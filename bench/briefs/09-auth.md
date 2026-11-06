# Brief 9: Sign-in and error states

**Deliverable:** a single self-contained `index.html` in the workspace root.

**Hard constraints (apply to every brief):**
- One HTML file. No build step. No CDN, no external fonts, no external images, no JS libraries.
- System font stack only. Any imagery must be CSS-only (gradients, shapes, SVG you write inline).
- Must be usable at 375px and 1440px wide. No horizontal scrolling at 375px.
- All copy below must appear verbatim. Do not invent testimonials, logos, statistics or prices.
- No lorem ipsum. No placeholder text.

---

**Goal:** an authentication screen for a B2B product, including failure states.

**Required:**
1. Centred card: product mark, title "Sign in to Northwind", email field, password field, "Sign in" button, "Forgot password?" link.
2. An inline error state on the email field: "That email isn't registered."
3. A secondary block showing a rate-limit state: "Too many attempts. Try again in 4 minutes."
4. A footer line with SSO option.

**Fixed copy:** exactly the strings above.

**Tone:** plain and trustworthy. Error copy must be readable, not red-on-red.

---

**When you are done:** write `index.html` and nothing else. Do not explain your choices in the file.
