---
id: "TST-accessibility-testing"
title: "Accessibility testing"
parent: "TST"
order: 5
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 2
syncHash: "dc465fa428c31ba2"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 16.5 Accessibility testing

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

Defines how we test that persona apps, emails and generated documents meet WCAG 2.2 Level AA ([[APP-accessibility-wcag-2-1-aa]]): automated checks at component, page and journey level, manual keyboard and screen-reader passes, document checks, tenant theme checks and testing with disabled users. Results feed the conformance reports and accessibility statements in [[APP-accessibility-conformance]] and the audit evidence in [[RPT-accessibility-audit-evidence-for]].

<!-- section:rules -->
## Rules

**Automated**
- **A11YT-1** Every shared component story in Storybook runs axe checks in the Storybook test runner; any violation at WCAG 2.2 A or AA fails the build ([[PKG-design-system-component]]).
- **A11YT-2** Every Playwright journey ([[TST-unit-integration-contract-and]] TEST-7) runs `@axe-core/playwright` on each step's page state, including open dialogs and error states, with WCAG 2.0/2.1/2.2 A and AA tags.
- **A11YT-3** Keyboard journeys: for each journey, a Playwright test completes the task using only keyboard events and asserts focus is visible and not obscured (2.4.7, 2.4.11).
- **A11YT-4** Tenant themes are checked at save time for contrast (4.5:1 text, 3:1 UI components and focus indicators) by [[PKG-tenant-theme-accessibility]]; CI also runs the journey suite with each fixture tenant's theme.
- **A11YT-5** Generated PDFs (procedural orders, awards, receipts, eBundle indexes) are checked with veraPDF against PDF/UA-1 in CI on sample outputs ([[DOM-accessible-documents-and]]).
- **A11YT-6** Email templates are checked for language attribute, heading structure, alt text and link text in the notification template tests.
- **A11YT-7** ESLint `jsx-a11y` runs on every PR ([[FND-language-and-conventions]]).

**Manual**
- **A11YT-8** Before each release that changes a journey, the owning team runs a manual pass of that journey with the assistive technology matrix below. Before each major release and at least yearly, a full manual audit is done by a specialist (proposed: an IAAP-certified auditor where a tenant's regulator expects one).

| AT | Browser / platform | Primary for |
|---|---|---|
| NVDA | Firefox and Chrome on Windows | Parties, counsel |
| JAWS | Chrome on managed Windows | Secretariat, neutrals ([[APP-secretariat-console-and-neutral]]) |
| VoiceOver | Safari on macOS and iOS | Parties on mobile, counsel |
| TalkBack | Chrome on Android | Parties on mobile (SEBI ODR investors, MSME claimants) |
| Windows Voice Access / Dragon | Chrome on Windows | Voice control |
| Zoom at 400% and Windows High Contrast | Chrome, Edge | Low vision |

- **A11YT-9** Usability testing with disabled users (at least 5 participants per major journey per year, proposed) for the party filing and hearing-join journeys, recruited across screen-reader, low-vision, motor and cognitive needs.

**Recording**
- **A11YT-10** Manual results are recorded per WCAG success criterion in the conformance workbook used by [[APP-accessibility-conformance]], with tester, date, AT versions and evidence links. Automated results are stored per release.
- **A11YT-11** Accessibility defects use severity: blocker (a task cannot be completed with an AT), major, minor. Blockers block release of the affected journey.

<!-- section:rationale -->
## Rationale

- Automated tools find only part of WCAG failures; many criteria (meaningful alt text, logical reading order, understandable errors) need people. Hence both layers [R1].
- The AT matrix reflects who uses which surface: secretariat staff often use JAWS on managed machines, while many unrepresented parties use phones.
- Generated documents (awards, orders) are part of the record parties must read; inaccessible PDFs exclude them from their own case.

<!-- section:tooling -->
## Tooling and configuration

- Storybook test runner with `axe-playwright`; `@axe-core/playwright` in e2e; ESLint `jsx-a11y`.
- veraPDF in a CI container for PDF/UA checks.
- Conformance workbook (spreadsheet or structured file in `docs/accessibility/`) feeding the ACR.

<!-- section:enforcement -->
## Enforcement

| Rule | Enforcement |
|---|---|
| A11YT-1, A11YT-2, A11YT-3, A11YT-5, A11YT-6, A11YT-7 | Required CI checks (component, journey and document jobs) |
| A11YT-4 | Activation blocked on failure; CI journey run per fixture theme |
| A11YT-8, A11YT-9 | Release checklist item for journey-changing releases; yearly audit tracked by the accessibility lead |
| A11YT-11 | Blocker label prevents the release manager approving the release for that journey |

<!-- section:examples -->
## Examples

Good: the filing wizard step "Upload documents" fails A11YT-3 because the drag-and-drop zone has no keyboard alternative (2.5.7); fixed with an "Choose files" button before merge.

Bad: marking 1.1.1 Non-text Content as "supports" in the ACR based on axe passing, without checking that alt text is meaningful.

<!-- section:exceptions -->
## Exceptions

Known issues awaiting a fix are recorded in the accessibility statement with a date and an alternative route (for example secretariat-assisted filing). Exceptions for third-party components follow [[INT-third-party-component]].

<!-- section:questions -->
## Open questions

- [ ] Who is the accessibility lead and who performs the yearly specialist audit?
- [ ] Does any SEBI-regulated tenant require the audit to be by an IAAP-certified professional? (Assumption based on the node title of [[RPT-accessibility-audit-evidence-for]]; legal to confirm against the current SEBI circular.)
- [ ] Budget and recruitment route for testing with disabled users in India, Singapore and the US.
- [ ] Do we test Indic-language screen-reader output (for example Hindi with NVDA) before launching those locales?

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Component, journey, keyboard, document and email checks are required CI checks; theme checks block activation; manual passes and disabled-user testing are release checklist and yearly plan items tracked by the accessibility lead.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

This node is the WCAG 2.2 AA guardrail for frontend work. Test sessions and recordings with disabled participants follow consent and privacy rules, and fixtures are synthetic.

<!-- check:compliance -->
### Compliance evidence

Produces the evidence behind ACRs and accessibility statements ([[APP-accessibility-conformance]]) and the evidence pack for regulated tenants ([[RPT-accessibility-audit-evidence-for]]); obligations per region are listed in [[APP-accessibility-legal-obligations]].

<!-- check:measurement -->
### Adoption measurement

Automated violations per release (target 0 at A/AA), open blockers and majors by journey, share of journeys with a manual pass in the last release that changed them.

<!-- check:ownership -->
### Ownership and change

Owner: accessibility lead (to be named) with the frontend platform team.

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C",
    "excerpt": "Success criteria at levels A, AA and AAA, including 2.4.11 Focus Not Obscured, 2.5.8 Target Size (Minimum), 3.2.6 Consistent Help and 3.3.8 Accessible Authentication (new in 2.2).",
    "id": "R1",
    "ident": "WCAG",
    "kind": "standard",
    "title": "Web Content Accessibility Guidelines (WCAG) 2.2",
    "url": "https://www.w3.org/TR/WCAG22/",
    "version": "2.2"
  }
]
```

<!-- end -->
