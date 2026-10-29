---
id: "APP-secretariat-console-and-neutral"
title: "Secretariat console and neutral workspace accessibility conformance"
parent: "APP-accessibility-wcag-2-1-aa"
order: 4
type: "requirement"
template: "accessibility"
status: "draft"
owner: null
indicative: false
summary: "Dense data tables, queues, award drafting; JAWS / NVDA on managed Windows machines"
links: []
rev: 2
syncHash: "ad4dbe4cded871da"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.4.1.4 Secretariat console and neutral workspace accessibility conformance

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Dense data tables, queues, award drafting; JAWS / NVDA on managed Windows machines

<!-- section:scope -->
## Scope and surfaces

Accessibility conformance for the `(secretariat)` console ([[APP-secretariat-console]]) and the `(neutral)` workspace ([[APP-neutral-workspace]]): dense data tables and queues, bulk actions, scheduling, award and order drafting editors, deliberation notes and the host side of the hearing room. Users work long sessions on managed Windows machines, many with JAWS or NVDA, and rely on keyboard efficiency.

<!-- section:obligations -->
## Standards and legal obligations by jurisdiction

As in [[APP-accessibility-legal-obligations]]. Institutions are also employers of secretariat staff; employment-related accessibility duties rest with the institution, but our console must not prevent reasonable accommodation.

<!-- section:target -->
## Conformance target and baseline

WCAG 2.2 AA; EN 301 549 clause 11 (software-like behaviour) applied to the editors as good practice; PDF/UA for orders and awards generated here.

<!-- section:criteria -->
## Success criteria mapping

Criteria met exactly as in the portal mapping through shared components and shells: 1.1.1, 1.3.2–1.3.5, 1.4.1–1.4.5, 1.4.11–1.4.13, 2.1.2, 2.2.1, 2.2.2, 2.3.1, 2.4.1, 2.4.2, 2.4.5–2.4.7, 2.5.1–2.5.4, 2.5.8, 3.1.1, 3.1.2, 3.2.1–3.2.4, 3.2.6, 3.3.1–3.3.3, 3.3.7, 3.3.8 (see [[APP-party-and-counsel-portal-2#criteria]]). Media criteria 1.2.x as for the hearing room and recordings.

Criteria with surface-specific risk:

| SC | Where | How met | Test |
|---|---|---|---|
| 1.3.1 Info and Relationships | queue grid, scheduler, decision panels | `role="grid"` only when cell navigation is needed, otherwise native `<table>` with `<th scope>`; sort state via `aria-sort`; selection checkboxes labelled with case reference | A, AT (JAWS, NVDA) |
| 1.4.10 Reflow | queue grid, scheduler | grid scrolls in its own region; stacked card view below `md` | automated + M |
| 2.1.1 Keyboard | grid, bulk dialog, scheduler drag, editor | grid arrow-key model per APG; scheduler offers form entry for every drag action; editor toolbar reachable with Alt+F10 style shortcut | K, AT |
| 2.1.4 Character Key Shortcuts | console shortcuts (`j`/`k` next/previous, `x` select) | off by default; enable and remap in user settings | M |
| 2.4.3 Focus Order | bulk action → operation page; dialogs; drawer | focus to operation heading; drawer traps and returns focus | K |
| 2.4.4 Link Purpose | queue rows | case reference link text plus row header | M |
| 2.4.11 Focus Not Obscured | sticky grid header, bulk action bar | `scroll-padding`; bar never covers focused row | K, M |
| 2.5.7 Dragging Movements | scheduler, order paragraph reorder | buttons and form alternatives | K |
| 3.3.4 Error Prevention | issue order, submit award, bulk status change | review step showing affected items, confirmation, step-up; orders can be corrected by a corrigendum route | K, M |
| 4.1.2 Name, Role, Value | editor (rich text), lock status, AI panel | editor exposes `role="textbox"` multiline with structure via headings and lists; lock status in a status element | AT |
| 4.1.3 Status Messages | filter results count, autosave, operation progress, lock changes | polite live region, rate-limited to one message per 2 s | AT |

<!-- section:components -->
## Component and pattern requirements

| Component | Contract essentials for this surface |
|---|---|
| [[PKG-data-table]] | APG grid or table; sortable headers; row selection; row count announced; virtualisation keeps `aria-rowcount` and `aria-rowindex` |
| [[PKG-combobox-and-people-picker]] | APG combobox; server results announced with count |
| [[PKG-date-and-time-picker-with]] | typed input; time zone stated |
| [[PKG-modal-dialog-and-consequential]] | affected count in heading |
| Rich-text editor (choice open) | toolbar pattern; headings and lists as structure; keyboard shortcuts announced in help |

<!-- section:at -->
## Assistive technology support matrix

| Combination | Who uses it | Depth per release |
|---|---|---|
| NVDA (current) + Chrome, Windows 11 | counsel, parties, secretariat | full critical journeys |
| JAWS (current and previous major) + Chrome / Edge, Windows 11 (managed) | secretariat, neutrals at institutions | full critical journeys for secretariat and neutral; smoke for others |
| VoiceOver + Safari, macOS | counsel, neutrals | critical journeys |
| VoiceOver + Safari, iOS (current and previous) | parties on phones | critical journeys for `(public)` and `(counsel)` |
| TalkBack + Chrome, Android (current) | parties on phones (largest group in India) | critical journeys for `(public)` and `(counsel)` |
| Windows forced colours (High Contrast) + Edge | low-vision users | smoke on every group |
| Browser zoom 200% and 400%, OS text scaling | low-vision users | every journey page (automated reflow check plus manual sample) |
| Dragon / Windows Voice Access + Chrome | users with motor disabilities | smoke on critical journeys each quarter |
| Keyboard only, Chrome / Firefox / Safari | everyone | every journey, automated in Playwright plus manual |

<!-- section:documents -->
## Documents, media and generated output

Orders and awards drafted here generate tagged PDF/UA from structured drafts, using the print theme ([[PKG-print-and-formal-document-theme]]); AI-assisted text is labelled in drafts and must be reviewed before issue ([[AI-ai-generated-text-labelling-and]]).

<!-- section:tenant -->
## Tenant theming and configuration guardrails

Tenant themes apply to the shell only; grid, editor and status colours use non-overridable semantic tokens.

<!-- section:testing -->
## Testing method

Sample: queue (filtered, empty, 10,000 rows), bulk action dialog and operation page, case overview, status change error, scheduler with conflict, task inbox, appointment acceptance, order editor (lock held, conflict), award submit for signature, deliberations, hearing host controls. JAWS + Chrome and NVDA + Firefox full runs each release; testing with at least one screen-reader user from an institution's secretariat twice a year.

<!-- section:exceptions -->
## Known exceptions and remediation plan

| Item | Impact | Workaround | Owner | Target |
|---|---|---|---|---|
| Rich-text editor not yet selected; screen-reader support unknown | possibly high for blind neutrals | draft in a word processor and upload; secretariat converts | frontend lead | editor decision before Phase 4 |
| Scheduler timeline view | medium | list view with forms is complete | UX | Phase 4 |

<!-- section:reporting -->
## Conformance reporting

Feeds the secretariat and neutral sections of the ACR.

<!-- section:questions -->
## Open questions

- [ ] Editor library decision with screen-reader evaluation (owner: frontend lead)
- [ ] Which JAWS versions do institution IT departments deploy (owner: account managers to survey)
- [ ] Console keyboard shortcut set (owner: UX)

<!-- checks -->
## Template checks

<!-- check:evidence -->
### Integrity of the conformance claim

Surface-specific criteria are mapped with tests; shared criteria are mapped by explicit reference to the portal mapping, so all 55 criteria are covered; known gaps are listed as exceptions with workarounds.

<!-- check:regression -->
### Preventing regression

JAWS and NVDA runs per release on the queue and editor; Playwright keyboard tests for bulk action and scheduling on every PR; data-table component changes trigger downstream story tests.

<!-- check:due-process -->
### Equal participation in proceedings

Neutrals with disabilities can draft through the editor or the upload workaround; accommodation requests from parties reach the secretariat task inbox with timers.

<!-- check:third-party -->
### Third-party and embedded components

The hearing provider's host controls and the e-sign provider used for awards are tested with JAWS and NVDA; failures recorded in [[INT-third-party-component]].

<!-- end -->
