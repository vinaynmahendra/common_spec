---
id: "APP-responsive-mobile-first"
title: "Responsive / mobile-first"
parent: "APP-frontend-standards"
order: 2
type: "feature"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 2
syncHash: "b7f93af9718de609"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.4.2 Responsive / mobile-first

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

Rules for building screens that work from a 320 CSS pixel wide phone to a large desktop, mobile-first. Unrepresented parties at SEBI ODR and CORD tenants often use only a phone; secretariat staff use wide desktop screens with dense tables. Both must work, and reflow and zoom must satisfy WCAG 2.2 (1.4.4 Resize Text, 1.4.10 Reflow, 2.5.8 Target Size Minimum) [R1].

<!-- section:rules -->
## Rules

1. **RESP-1** Write base styles for the smallest viewport and add `min-width` media or container queries for larger ones.
2. **RESP-2** Breakpoints come from design tokens only: `sm 480`, `md 768`, `lg 1024`, `xl 1280`, `2xl 1536` (px). Component layouts prefer container queries over viewport queries.
3. **RESP-3** Every page works at 320 px width and at 400% zoom on a 1280 px screen without two-dimensional scrolling, except content that needs it (data tables, the document viewer, the transcript waveform), which scrolls inside its own region with a visible, keyboard-reachable scroll container.
4. **RESP-4** Pointer targets are at least 24 × 24 CSS px with spacing (WCAG 2.5.8); primary actions on touch layouts are at least 44 × 44 px.
5. **RESP-5** No functionality depends on hover; anything shown on hover is also available on focus and tap.
6. **RESP-6** Text uses `rem` units; no fixed heights on text containers; line length 45–80 characters for reading content.
7. **RESP-7** Orientation is never locked (WCAG 1.3.4).
8. **RESP-8** Persona priorities: `(public)` and `(counsel)` are designed phone-first; `(secretariat)`, `(neutral)` editors, `(transcriber)` and admin consoles are designed desktop-first but must still pass RESP-3 (on phones they may offer a reduced, read-mostly view, never a blank page).
9. **RESP-9** Data tables collapse to a stacked card list below `md` unless the user chooses table view; the stacked view keeps column labels.

<!-- section:rationale -->
## Rationale

Phone-first matters most where parties act without lawyers and deadlines have legal effect; a filing that cannot be completed on a phone is an access-to-justice problem, not a cosmetic one.

<!-- section:tooling -->
## Tooling and configuration

Tailwind CSS (or CSS modules with tokens) configured from DTCG tokens ([[PKG-design-tokens-and-foundations]]); Playwright projects for 320×640, 390×844, 768×1024, 1280×800 and 1280×800 at 400% zoom; Storybook viewport addon.

<!-- section:enforcement -->
## Enforcement

| Rule | Enforcement |
|---|---|
| RESP-2 | Stylelint: no raw pixel media queries outside tokens |
| RESP-3 | Playwright check: `document.scrollingElement.scrollWidth <= innerWidth` at 320 px and 400% zoom for every journey page (allow-listed scroll regions excluded) |
| RESP-4 | axe `target-size` rule in Storybook and Playwright |
| RESP-5 | Review checklist; Storybook interaction tests with keyboard |
| RESP-7 | Lint for `screen.orientation.lock` |

<!-- section:examples -->
## Examples

Good: the counsel case header stacks reference, stage badge and next deadline vertically below `md`, and shows them in one row from `md`. Bad: a secretariat queue that sets `min-width: 1200px` on the page so phones get horizontal page scrolling.

<!-- section:exceptions -->
## Exceptions

Content that requires two-dimensional layout (tables, viewer, waveform) is listed in `docs/responsive-exceptions.md` with its scroll-region design; no other exceptions.

<!-- section:questions -->
## Open questions

- [ ] Confirm the reduced phone view scope for `(secretariat)` and `(neutral)`: read-only or limited actions? (owner: UX)

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

RESP-2, 3, 4 and 7 are automated (Stylelint, Playwright overflow check, axe target-size, lint); RESP-5, 6, 8 and 9 are review items with Storybook interaction tests.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

Reflow and target-size rules implement WCAG 2.2 AA criteria 1.4.10 and 2.5.8 directly in CI.

<!-- check:measurement -->
### Adoption measurement

RUM reports share of sessions by viewport class per route group; Playwright reports pages failing reflow; target is zero failing journey pages.

<!-- check:ownership -->
### Ownership and change

Owner: design-system lead with the frontend lead; breakpoint tokens change only through [[PKG-design-tokens-and-foundations]]; reviewed yearly against RUM viewport data.

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C",
    "id": "R1",
    "ident": "WCAG 2.2",
    "kind": "standard",
    "title": "Web Content Accessibility Guidelines (WCAG) 2.2",
    "url": "https://www.w3.org/TR/WCAG22/",
    "version": "W3C Recommendation"
  }
]
```

<!-- end -->
