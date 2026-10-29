---
id: "PKG-design-system-component"
title: "Design system component accessibility contract"
parent: "PKG-ui-design-system"
order: 15
type: "feature"
template: "accessibility"
status: "draft"
owner: null
indicative: false
summary: "ARIA pattern, keyboard model, announcements and target size per shared component; build-blocking checks on Storybook stories"
links: []
rev: 2
syncHash: "cf8b498255425e04"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.14.15 Design system component accessibility contract

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> ARIA pattern, keyboard model, announcements and target size per shared component; build-blocking checks on Storybook stories

<!-- section:scope -->
## Scope and surfaces

This node is the accessibility contract for every shared component in `@nomology/ui` (5.14.2 to 5.14.14) and the build-blocking checks that enforce it on Storybook stories. It covers components as rendered in all route groups, all fixture tenant themes, light, dark and high-contrast modes, forced colours, comfortable and compact density, LTR and RTL. It does not cover full pages or journeys (surface nodes such as [[APP-party-and-counsel-portal-2]] and [[APP-secretariat-console-and-neutral]]), generated documents ([[DOM-accessible-documents-and]]) or third-party embeds ([[INT-third-party-component]]). Surface conformance nodes inherit from this contract and should not re-test component internals.

<!-- section:obligations -->
## Standards and legal obligations by jurisdiction

The design system carries no separate legal obligation; it is how the platform meets the obligations recorded in [[APP-accessibility-legal-obligations]] (for example the RPwD Act 2016 for Indian service providers [R1] and the SEBI digital accessibility circular of 31 July 2025 for SEBI-regulated tenants [R2]). The obligated party for component conformance is Nomology. Draft or unconfirmed instruments are tracked in the parent register, not here.

<!-- section:target -->
## Conformance target and baseline

WCAG 2.2 Level AA [R3] for every component in every supported configuration, plus these platform rules beyond AA: 2.4.13 Focus Appearance (AAA) for the focus ring geometry (2 px outline, 3:1) [R4]; no information by colour alone even where AA would allow it; 44 px touch targets on party pages. Applicable EN 301 549 clause 9 (web) maps to the same WCAG criteria. Baseline: no component exists yet; the baseline is set at the first release by the checks below.

<!-- section:criteria -->
## Success criteria mapping

Contract per component. "Test" column: A = automated in CI on stories, K = keyboard interaction test in CI, M = manual AT check per release.

| Component | APG pattern / native element | Keyboard model | Announcements | Target size | Key criteria | Test |
|---|---|---|---|---|---|---|
| [[PKG-button-and-icon-button]] | Native `<button>` | Enter, Space | `aria-busy` + loading text | 24 px min, 44 px touch on party pages | 2.5.3, 2.5.8, 4.1.2 | A, K, M |
| [[PKG-form-fields]] | Native inputs, `<fieldset>` / `<legend>` | Native | Error summary focus; errors via `aria-describedby` | 24 px (checkbox hit area padded) | 1.3.1, 1.3.5, 3.3.1, 3.3.2, 3.3.7 | A, K, M |
| [[PKG-combobox-and-people-picker]] | Combobox with listbox | Arrows, Enter, Escape, Backspace on chips | Result count, polite, once | 24 px options | 1.3.1, 2.1.1, 4.1.2, 4.1.3 | A, K, M |
| [[PKG-date-and-time-picker-with]] | Spinbutton segments + dialog grid | Arrows, Page Up / Down, Home / End | Grid heading; unavailable reason | 24 px day cells (40 px comfortable) | 1.3.1, 2.1.1, 3.3.1 | A, K, M |
| [[PKG-file-upload-dropzone]] | Native file input + list | Buttons only; no drag needed | Throttled per-file status | 24 px | 2.5.7, 4.1.3 | A, K, M |
| [[PKG-data-table]] | Native table; Grid only in opt-in mode | Tab (table) or arrows (grid) | Sort / filter / page summary | 24 px controls | 1.3.1, 2.4.11, 1.4.10, 4.1.3 | A, K, M |
| [[PKG-modal-dialog-and-consequential]] | Dialog (Modal) / alertdialog, native `<dialog>` | Tab cycle, Escape | Title and description on open | 24 px | 2.4.3, 3.3.4, 4.1.2 | A, K, M |
| [[PKG-alerts-toasts-and-status]] | Live regions, `role="alert"` | Toast region reachable | Polite / assertive policy | 24 px dismiss | 2.2.1, 4.1.3 | A, M |
| [[PKG-stepper-and-multi-step-form]] | `<nav><ol>` with `aria-current="step"` | Native | Focus to step heading | 24 px | 2.4.2, 2.4.6, 3.3.7 | A, K, M |
| [[PKG-case-timeline]] | Headings + `<ol>` of articles | Native | New-events banner | n/a | 1.3.1, 2.4.6 | A, M |
| [[PKG-status-and-deadline-badges]] | Text + icon | Not focusable | None (page announces deadline passing) | n/a | 1.4.1, 1.4.3 | A |
| [[PKG-tenant-and-role-switcher]] | Menu button (list of links) | Enter, arrows, Escape | `aria-current` | 24 px | 3.2.2, 4.1.2 | A, K, M |
| [[PKG-document-viewer-controls]] | Toolbar (roving tabindex) | Arrows in toolbar; modifier shortcuts | Explicit navigation | 24 px | 2.1.4, 4.1.2, 4.1.3 | A, K, M |

Criteria handled by foundations rather than components: 1.4.3, 1.4.11 (contrast manifest, [[PKG-colour-and-contrast]]), 1.4.4, 1.4.12 ([[PKG-typography-and-multi-script]]), 2.3.3 / reduced motion ([[PKG-colour-modes-and-user]]). Not applicable at component level with reason: 1.2.x (no time-based media in components; hearing room media is in [[DOM-hearing-room-accessibility]]), 2.4.1 bypass blocks (page level; `SkipLink` is provided but placement is the layout's job).

<!-- section:components -->
## Component and pattern requirements

Rules every component must honour (checked in review and, where marked, automatically):

1. Native HTML element where one exists; ARIA only to fill gaps (lint: `jsx-a11y`, custom rule against `role="button"` on `div`).
2. Accessible name required by the props type for every interactive part (`label`, `IconButton.label`, `rowLabel`).
3. Visible focus: 2 px outline in `color.focus.ring` with 2 px offset, never removed; survives forced colours.
4. Focus is never lost to `<body>` after open, close, delete, error or async completion; target documented in each component's keyboard section.
5. Status changes use the shared `Announcer`; components never create ad-hoc live regions.
6. No content on hover only; anything shown on hover or focus is dismissible, hoverable and persistent (1.4.13).
7. Minimum target 24 × 24 CSS px, including in compact density.
8. Built-in strings come from `UiMessages` and support ICU plurals.

<!-- section:at -->
## Assistive technology support matrix

| AT + browser | Platform | Who | Depth |
|---|---|---|---|
| NVDA + Chrome | Windows | Counsel, secretariat | Full: every component, every release |
| JAWS + Chrome | Managed Windows | Secretariat staff at institutions | Full for table, combobox, dialog, form fields, date picker |
| VoiceOver + Safari | macOS | Counsel, neutrals | Full |
| VoiceOver + Safari | iOS | Parties | Smoke: buttons, form fields, file upload, dialog, stepper |
| TalkBack + Chrome | Android | Parties (most common device for SEBI ODR investors and MSME claimants, assumption to be checked with usage data) | Smoke as iOS |
| Voice control (Dragon or Voice Control) | Windows / macOS | Motor-impaired users | Spot check: label-in-name on buttons and fields |
| Windows High Contrast / forced colours | Windows | Low-vision users | Automated snapshot + manual spot check |

<!-- section:tenant -->
## Tenant theming and configuration guardrails

Components use only semantic and component tokens, so tenant themes can change brand colours, logos, radius and heading font only. Brand colours are validated before activation ([[PKG-tenant-theme-accessibility]]). The visual regression matrix includes a "worst-case passing" fixture theme (brand colour just above every threshold, longest display name, widest logo) so components are proven at the limits tenants can reach.

<!-- section:testing -->
## Testing method

**Build-blocking checks on every PR that changes `packages/ui` or `packages/tokens`:**

| Check | Tool | Fails build when |
|---|---|---|
| Story coverage | Script comparing component node variant × state lists with story exports | A variant or state has no story |
| Automated rules | axe-core via the Storybook test runner on every story, in light, dark and high contrast [R5][R6] | Any `serious` or `critical` violation; `moderate` requires a recorded waiver |
| Keyboard interaction | Storybook play functions (`userEvent.keyboard`) [R7] | Keyboard path in the component's table fails, or focus ends on `<body>` |
| Contrast manifest | `pnpm tokens:check-contrast` | Any pair below threshold for any mode or fixture theme |
| Target size | Play-function assertion on bounding boxes | Any interactive element under 24 × 24 |
| Forced colours | Playwright snapshot with forced-colors emulation | Visual diff not approved |
| Lint | `eslint-plugin-jsx-a11y`, stylelint logical properties | Error |

Manual AT testing per the matrix each release, recorded in `docs/a11y/component-results/{version}.md` with tester, date, AT version and build hash. Following WCAG-EM [R8], the sample for the ACR is all component stories plus the states listed in each component node.

<!-- section:exceptions -->
## Known exceptions and remediation plan

None at the time of writing (no components shipped). Any exception is recorded in `docs/a11y/exceptions.yaml` with component, criterion, impact, workaround, owner and fix date, and flows into the ACR ([[APP-accessibility-conformance]]).

<!-- section:reporting -->
## Conformance reporting

Component results feed the platform ACR: each release's ACR references the design-system version and the stored test records. No separate public report for the design system.

<!-- section:questions -->
## Open questions

- [ ] Do we waive axe `moderate` findings or fail on them too (proposed: waiver needed) (owner: accessibility lead).
- [ ] Budget and schedule for testing components with disabled users (proposed: twice a year with recruited participants, paid) (owner: product).
- [ ] Confirm the device mix for parties from analytics once CORD traffic exists (owner: product analytics).

<!-- checks -->
## Template checks

<!-- check:evidence -->
### Integrity of the conformance claim

Each "Supports" claim for a component criterion is backed by a stored record: CI run ID and build hash for automated and keyboard tests, plus a manual result file per release naming tester, date, AT and browser versions. The ACR is re-issued when the design-system major version changes.

<!-- check:tenancy -->
### Tenant customisation and content

Tenants cannot inject CSS or scripts into components; brand colours are validated before activation in light and dark; the worst-case passing fixture theme proves components at the limits of what tenants can configure.

<!-- check:regression -->
### Preventing regression

axe-core on every story (serious and critical fail), keyboard play functions, contrast manifest, target-size assertions and forced-colours snapshots run on every PR that touches `packages/ui` or `packages/tokens`; jsx-a11y lint errors fail; manual AT matrix each release; accessibility acceptance criteria are part of the Definition of Done for component tickets.

<!-- check:third-party -->
### Third-party and embedded components

The design system does not embed third-party widgets. The headless behaviour library (proposed React Aria Components) is tested through our own stories and AT matrix, not accepted on the vendor's word.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "issuer": "Government of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 49 of 2016",
    "title": "Rights of Persons with Disabilities Act, 2016",
    "url": "https://indiacode.nic.in/bitstream/123456789/15939/1/the_rights_of_persons_with_disabilities_act%2C_2016.pdf"
  },
  {
    "id": "R2",
    "issuer": "Securities and Exchange Board of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "title": "Compliance guidelines for digital accessibility (circular dated 31 July 2025)",
    "url": "https://www.sebi.gov.in/legal/circulars/sep-2025/compliance-guidelines-for-digital-accessibility-circular-rights-of-persons-with-disabilities-act-2016-and-rules-made-thereunder-mandatory-compliance-by-all-regulated-entities-dated-july-31-2025-_96862.html"
  },
  {
    "body": "W3C",
    "id": "R3",
    "ident": "WCAG 2.2",
    "kind": "standard",
    "title": "Web Content Accessibility Guidelines (WCAG) 2.2",
    "url": "https://www.w3.org/TR/WCAG22/",
    "version": "2.2"
  },
  {
    "body": "W3C",
    "excerpt": "Focus indicator at least as large as a 2 CSS px perimeter and 3:1 change of contrast.",
    "id": "R4",
    "ident": "WCAG 2.2 SC 2.4.13 (AAA)",
    "kind": "standard",
    "title": "Understanding SC 2.4.13 Focus Appearance",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance"
  },
  {
    "id": "R5",
    "kind": "vendor",
    "retrieved": "2026-10-28",
    "title": "axe-core accessibility engine",
    "url": "https://github.com/dequelabs/axe-core",
    "vendor": "Deque"
  },
  {
    "id": "R6",
    "kind": "vendor",
    "retrieved": "2026-10-28",
    "title": "Accessibility tests",
    "url": "https://storybook.js.org/docs/writing-tests/accessibility-testing",
    "vendor": "Storybook"
  },
  {
    "id": "R7",
    "kind": "vendor",
    "retrieved": "2026-10-28",
    "title": "Interaction tests",
    "url": "https://storybook.js.org/docs/writing-tests/interaction-testing",
    "vendor": "Storybook"
  },
  {
    "body": "W3C",
    "id": "R8",
    "ident": "WCAG-EM",
    "kind": "standard",
    "title": "WCAG-EM Overview: Website Accessibility Conformance Evaluation Methodology",
    "url": "https://www.w3.org/WAI/test-evaluate/conformance/wcag-em/"
  }
]
```

<!-- end -->
