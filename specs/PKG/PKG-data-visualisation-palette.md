---
id: "PKG-data-visualisation-palette"
title: "Data visualisation palette"
parent: "PKG-design-tokens-and-foundations"
order: 4
type: "requirement"
template: "designsys"
status: "draft"
owner: null
indicative: false
summary: "Categorical, sequential and status palettes for reporting dashboards, accessible to colour-blind users"
links: []
rev: 2
syncHash: "96fc5123b44308b3"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.14.1.4 Data visualisation palette

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Categorical, sequential and status palettes for reporting dashboards, accessible to colour-blind users

<!-- section:purpose -->
## Purpose and scope

Defines the colours, patterns and rules for charts in tenant dashboards and platform reports (case ageing, neutral performance, transcriber turnaround, unpaid invoices, AI usage), as consumed by [[RPT-report-infrastructure]] dashboards and the reports under [[RPT-platform-stats]]. Covers categorical, sequential, diverging and status palettes for light and dark modes. Chart components themselves (library choice, axes, tooltips) are out of scope and belong to the reporting UI.

<!-- section:architecture -->
## Token architecture and naming

Tokens in `src/semantic/dataviz.tokens.json`: `color.dataviz.categorical.{1..6}`, `color.dataviz.other`, `color.dataviz.sequential.{1..8}`, `color.dataviz.diverging.{neg3..pos3}`, `color.dataviz.status.*` (aliases of [[PKG-colour-and-contrast]] status tones), `color.dataviz.axis`, `color.dataviz.gridline`. Also exported in `dist/ts/tokens.ts` because chart libraries need values in JavaScript. Tenants cannot change dataviz tokens.

<!-- section:colour -->
## Colour

**Categorical** (order is fixed; series 1 always gets colour 1). Values were chosen so each colour has at least 3:1 against the chart surface, as WCAG 1.4.11 requires for graphical objects [R1], and to keep the pairwise distance as large as possible under simulated protanopia, deuteranopia and tritanopia (Machado 2009 simulation, distance measured in OKLab).

| Token | Light (on #FFFFFF) | Contrast | Dark (on #181C24) | Contrast |
|---|---|---|---|---|
| `categorical.1` | #2D3DAB | 8.87 | #5978E6 | 4.27 |
| `categorical.2` | #C1881B | 3.09 | #CE942B | 6.42 |
| `categorical.3` | #66354F | 9.60 | #50F5DB | 12.54 |
| `categorical.4` | #2C97F8 | 3.05 | #DE4181 | 4.21 |
| `categorical.5` | #AB4718 | 5.76 | #E6D666 | 11.52 |
| `categorical.6` | #7C6A94 | 4.83 | #96AEE8 | 7.73 |
| `other` | #6B7484 | 4.71 | #8D96A5 | 5.72 |

Minimum pairwise OKLab distance (×100) across normal vision and the three simulated deficiencies: 14.3 (light), 14.1 (dark). Proposed CI threshold: 12. The light and dark sets were optimised separately, so a series keeps its index but not necessarily its hue between modes; legends and direct labels make this acceptable. These values are a first proposal from an automated search and need review by product design for appearance; any replacement must pass the same check.

**Rules for categorical charts.**
- Maximum 6 categories; the rest go into "Other".
- Colour is never the only way to identify a series [R2]: lines get distinct markers and dash patterns, bars and pie segments get direct labels or a pattern fill option, and the legend order matches the visual order.
- Adjacent segments in stacked bars and pies have a 1 px `surface.default` separator so neighbouring colours need not contrast with each other.

**Sequential** (single hue, for heatmaps such as case ageing by month): #EEF4FF, #C9DBFB, #9DBDF3, #6F9BE6, #4479D2, #2556B8, #173F8C, #0E2A60. The first four steps are below 3:1 against white, so heatmap cells always show the value as text (using `text.default` or `text.on-action` chosen per cell for 4.5:1) and the legend has a bordered scale.

**Diverging** (for change versus previous period): red.700, red.400, red.100, neutral.100, blue.100, blue.400, blue.700. Direction is also shown with a sign and arrow in labels.

**Status series** reuse `status.*` tones (for example "overdue" in `status.critical`) and only for status meaning, never as general categorical colours.

<!-- section:typography -->
## Typography

Axis labels and tick values use `typography.data.cell` with tabular figures; chart titles use `typography.heading.sm`. Minimum text in charts is 12 px. Numbers are formatted by [[I18N-l10n]] utilities in the viewer's locale.

<!-- section:theming -->
## Theming and tenant branding

Not tenant-themable. Tenant brand colours would make charts inconsistent across tenants and could break the colour-vision checks.

<!-- section:modes -->
## Colour modes and user preferences

Light and dark values are separate tokens. In forced colours mode charts set `forced-color-adjust: none` on the plot area only and rely on patterns and direct labels; axes and text follow system colours. Every chart has a "View as table" toggle that renders the same data in [[PKG-data-table]], which is also the accessible alternative for screen reader users.

<!-- section:governance -->
## Governance, versioning and deprecation

Changes require the CVD distance check (`pnpm tokens:check-dataviz`) and contrast check to pass and are reviewed by the design system owners and the reporting product owner.

<!-- section:questions -->
## Open questions

- [ ] Product design review of the proposed categorical values for appearance and brand fit (owner: product design).
- [ ] Choose the chart library and confirm it supports patterns, markers and keyboard focus on data points (owner: reporting lead).
- [ ] Should the CVD distance threshold be 12 (proposed) or higher (owner: accessibility lead).

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Accessibility by construction

Each categorical colour has at least 3:1 against its chart surface; series are also distinguished by markers, dash patterns, direct labels and a data-table alternative; heatmap cells always print their value. A CI check simulates three colour-vision deficiencies and fails if any pair falls below the distance threshold.

<!-- check:tenancy -->
### Tenant theme isolation and safety

Dataviz tokens are not tenant-configurable, so a tenant theme cannot change chart colours or break the colour-vision check.

<!-- check:single-source -->
### Single source of truth and drift

Dataviz values are DTCG tokens exported to TypeScript for chart libraries; charts may not define their own colours (lint rule on the reporting package).

<!-- check:change-safety -->
### Change safety and blast radius

Any change reruns the contrast and colour-vision distance checks and the dashboard visual snapshots in light and dark; changing the categorical order is a major release because users learn series colours.

<!-- check:surfaces -->
### Coverage across surfaces and formal outputs

Dashboards in the web app use these tokens; exported report PDFs use the light values and print patterns; CSV exports have no colour.

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C",
    "excerpt": "User interface components and graphical objects need at least 3:1 against adjacent colours.",
    "id": "R1",
    "ident": "WCAG 2.2 SC 1.4.11",
    "kind": "standard",
    "title": "Understanding SC 1.4.11 Non-text Contrast",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast"
  },
  {
    "body": "W3C",
    "excerpt": "Colour is not used as the only visual means of conveying information.",
    "id": "R2",
    "ident": "WCAG 2.2 SC 1.4.1",
    "kind": "standard",
    "title": "Understanding SC 1.4.1 Use of Color",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/use-of-color"
  }
]
```

<!-- end -->
