---
id: "APP-frontend-standards"
title: "Frontend standards"
parent: "APP"
order: 4
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: "Parent standard for repo-wide frontend rules: accessibility, responsive design, error and loading states, document viewing, performance, client state and content"
links: []
rev: 2
syncHash: "6f49a83a6bdb25c0"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.4 Frontend standards

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Parent standard for repo-wide frontend rules: accessibility, responsive design, error and loading states, document viewing, performance, client state and content

<!-- section:purpose -->
## Purpose and scope

Groups the frontend rules every screen in `apps/web` must follow, whatever its persona. Detail lives in the children:

| Child | Covers |
|---|---|
| [[APP-accessibility-wcag-2-1-aa]] (and its children) | WCAG 2.2 AA target, obligations, ACRs, per-surface conformance, feedback |
| [[APP-responsive-mobile-first]] | Breakpoints, layout, touch, zoom and reflow |
| [[APP-error-boundaries-loading-and]] · [[APP-error-message-catalogue]] | Boundaries, loading and empty states; error copy |
| [[APP-document-viewer-and-sandbox]] | Rendering uploaded documents on a sandbox origin |
| [[APP-frontend-performance-budgets]] | Web Vitals, JS and TTFB budgets |
| [[APP-client-state-and-data-fetching]] | Where state lives, query keys, clearing |
| [[APP-voice-tone-and-content-style]] | Voice, tone and microcopy |

Component-level rules are in [[PKG-ui-design-system]] and [[PKG-design-system-component]].

<!-- section:rules -->
## Rules

1. **FE-1** Screens are built from design-system components; a new interactive pattern needs a design-system proposal, not a local implementation.
2. **FE-2** No user-visible string in JSX; all copy from message catalogues.
3. **FE-3** Every screen has designed loading, empty, error and no-access states before it is marked done.
4. **FE-4** Every UI ticket's Definition of Done includes: axe clean, keyboard path tested, 320 px reflow checked, budgets met.
5. **FE-5** No personal data or case content in client-side logs, analytics events or error reports.

<!-- section:tooling -->
## Tooling and configuration

ESLint (`jsx-a11y`, literal-string rule, design-system import rules), Storybook with axe, Playwright with axe, `size-limit`, Lighthouse CI on preview deployments.

<!-- section:enforcement -->
## Enforcement

FE-1 by lint rules restricting raw interactive HTML elements outside `packages/ui` (for example `<div onClick>`), FE-2 by literal-string lint, FE-3 and FE-4 by PR template checklist and Playwright state coverage, FE-5 by a client-telemetry schema that only allows listed fields.

<!-- section:questions -->
## Open questions

- [ ] Who owns visual regression across tenant themes (proposed: design-system team with [[TST-accessibility-testing]])?

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Four of five rules are tool-enforced; FE-3 relies on the PR checklist plus Playwright tests that visit each state.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

FE-5 keeps personal data out of browser telemetry; FE-1 makes accessibility inherited from components; WCAG 2.2 AA checks run on every PR.

<!-- check:compliance -->
### Compliance evidence

The standards produce evidence for WCAG 2.2 AA conformance (axe and Playwright results per build, feeding the ACR) and for ISO 27001:2022 secure development (FE-5 telemetry schema, review records).

<!-- check:ownership -->
### Ownership and change

Owner: frontend lead, with the design-system lead for FE-1 and the content lead for FE-2.

<!-- end -->
