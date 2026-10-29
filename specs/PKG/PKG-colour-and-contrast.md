---
id: "PKG-colour-and-contrast"
title: "Colour and contrast"
parent: "PKG-design-tokens-and-foundations"
order: 1
type: "requirement"
template: "designsys"
status: "draft"
owner: null
indicative: false
summary: "Primitive palettes, semantic colour roles, case-status colours and the contrast-pair manifest checked in CI"
links: []
rev: 2
syncHash: "0822e0e72d83ebb5"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.14.1.1 Colour and contrast

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Primitive palettes, semantic colour roles, case-status colours and the contrast-pair manifest checked in CI

<!-- section:purpose -->
## Purpose and scope

Defines the exact primitive palettes, the semantic colour roles every component uses, the case and document status tones, and the contrast-pair manifest that CI and the tenant theme validator check. Consumers: `@nomology/ui`, the email renderer, `@nomology/theme` (tenant validation) and the data-visualisation palette ([[PKG-data-visualisation-palette]]) which reuses the neutral and status ramps. Mode-specific overrides are listed here; how modes are selected is in [[PKG-colour-modes-and-user]].

<!-- section:architecture -->
## Token architecture and naming

Primitive ramps live in `packages/tokens/src/primitive/color.tokens.json`; semantic roles in `src/semantic/color.tokens.json` (light values) with overrides in `src/modes/dark.tokens.json` and `src/modes/high-contrast.tokens.json`. Components reference only `color.*` semantic tokens or their component tokens. Tenant brand colours enter only through `color.brand.primary` and `color.brand.accent`, which feed `color.action.primary.*`, `color.text.link`, `color.border.selected` and `color.focus.ring` after validation (see [[PKG-tenant-theme-schema-and]]). Feedback and status roles never take brand colour.

<!-- section:colour -->
## Colour

**Primitive palettes (sRGB hex).**

| Ramp | 0 | 50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900 | 950 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| neutral | #FFFFFF | #F7F8FA | #EEF0F3 | #DDE1E7 | #C3C9D2 | #8D96A5 | #6B7484 | #525B6B | #3C4452 | #272D38 | #181C24 | #0F1218 |
| blue | | #EEF4FF | #D9E6FF | | #8DB1F5 | #5F8FEA | #3A6FD8 | #2556B8 | #1D4494 | #173574 | | |
| red | | #FDF0EF | #FADBD8 | | #EE958C | #E26A5E | | #B4271B | #8F1F16 | | | |
| amber | | #FFF6E5 | #FDE7BF | | #F2C25C | #E3A21A | | #8A5A00 | #6E4700 | | | |
| green | | #ECF7EF | #D2EEDB | | #7FC99A | #4FAE72 | | #1E7041 | #175A34 | | | |
| violet | | #F3F0FD | #E4DDFA | | #B3A3EE | | | #5B3FB8 | #4A3396 | | | |

**Semantic roles.**

| Token | Light | Dark |
|---|---|---|
| `color.surface.default` | neutral.0 | neutral.950 |
| `color.surface.subtle` | neutral.50 | neutral.900 |
| `color.surface.sunken` | neutral.100 | neutral.950 |
| `color.surface.raised` | neutral.0 | neutral.900 |
| `color.surface.overlay` | neutral.0 | neutral.800 |
| `color.text.default` | neutral.900 | neutral.50 |
| `color.text.muted` | neutral.600 | neutral.300 |
| `color.text.disabled` | neutral.400 | neutral.500 |
| `color.text.link` | brand.primary (default blue.600) | blue.300 or validated brand dark variant |
| `color.text.on-action` | neutral.0 | neutral.950 |
| `color.border.default` | neutral.200 | neutral.800 |
| `color.border.control` | neutral.500 | neutral.400 |
| `color.border.selected` | brand.primary | brand dark variant |
| `color.action.primary.bg` / `.hover` / `.pressed` | blue.600 / blue.700 / blue.800 | blue.300 / blue.400 / blue.500 |
| `color.action.danger.bg` / `.hover` | red.600 / red.700 | red.300 / red.400 |
| `color.focus.ring` | blue.600 | blue.300 |
| `color.feedback.error.fg` / `.bg` / `.border` | red.700 / red.50 / red.600 | red.300 / neutral.900 / red.300 |
| `color.feedback.warning.fg` / `.bg` / `.border` | amber.700 / amber.50 / amber.600 | amber.300 / neutral.900 / amber.300 |
| `color.feedback.success.fg` / `.bg` / `.border` | green.700 / green.50 / green.600 | green.300 / neutral.900 / green.300 |
| `color.feedback.info.fg` / `.bg` / `.border` | blue.700 / blue.50 / blue.600 | blue.300 / neutral.900 / blue.300 |

Disabled text is exempt from contrast requirements under WCAG 1.4.3 [R1], but disabled controls are avoided where possible (see [[PKG-button-and-icon-button]]).

**Status tones.** Entity state machines ([[WF-entity-state-machines]]) map each case, document and invoice status to one of seven tones. The tone gives colour; the badge always shows the status label and an icon, so colour is never the only signal [R2].

| Tone | Light fg / bg | Dark fg / bg | Typical states (mapping owned by the state machine package) | Icon |
|---|---|---|---|---|
| `status.neutral` | neutral.700 / neutral.100 | neutral.200 / neutral.800 | Draft, not started | circle-dashed |
| `status.info` | violet.700 / violet.100 | violet.300 / neutral.800 | Submitted, under review by secretariat | inbox |
| `status.progress` | blue.700 / blue.100 | blue.300 / neutral.800 | Active, hearing scheduled, in transcription | progress |
| `status.attention` | amber.700 / amber.100 | amber.300 / neutral.800 | Awaiting your action, payment due, deadline within 7 days | alert-triangle |
| `status.critical` | red.700 / red.100 | red.300 / neutral.800 | Overdue, rejected, scan failed | alert-octagon |
| `status.success` | green.700 / green.100 | green.300 / neutral.800 | Award issued, paid, approved | check-circle |
| `status.closed` | neutral.600 / neutral.100 | neutral.300 / neutral.800 | Closed, withdrawn, archived | archive |

**Contrast-pair manifest** (`dist/contrast-manifest.json`, generated from `contrast-pairs.yaml`). Ratios below are computed with the WCAG 2.x relative luminance formula for the base theme [R1][R3]. CI recomputes them for every mode and fixture theme.

| Pair (fg on bg) | Required | Light | Dark |
|---|---|---|---|
| text.default on surface.default | 4.5 | 17.07 | 17.64 |
| text.default on surface.subtle / raised | 4.5 | 16.06 | 16.06 |
| text.muted on surface.default | 4.5 | 6.85 | 11.25 |
| text.muted on surface.subtle / raised | 4.5 | 6.44 | 10.25 |
| text.muted on surface.sunken | 4.5 | 6.00 | 11.25 |
| text.link on surface.default | 4.5 | 6.77 | 8.70 |
| text.link on surface.raised | 4.5 | 6.77 | 7.92 |
| text.on-action on action.primary.bg | 4.5 | 6.77 | 8.70 |
| text.on-action on action.primary.bg.hover | 4.5 | 9.10 | 5.90 |
| text.on-action on action.danger.bg | 4.5 | 6.47 | 8.32 |
| border.control on surface.default | 3.0 | 4.71 | 6.28 |
| border.control on surface.subtle / raised | 3.0 | 4.43 | 5.72 |
| focus.ring on surface.default | 3.0 | 6.77 | 8.70 |
| focus.ring on surface.subtle / raised | 3.0 | 6.37 | 7.92 |
| feedback.error.fg on surface.default | 4.5 | 8.84 | 8.32 |
| feedback.error.fg on feedback.error.bg | 4.5 | 7.95 | 7.57 |
| feedback.warning.fg on feedback.warning.bg | 4.5 | 7.63 | 10.28 |
| feedback.success.fg on feedback.success.bg | 4.5 | 7.50 | 8.72 |
| feedback.info.fg on feedback.info.bg | 4.5 | 8.25 | 7.92 |
| status.neutral fg on bg | 4.5 | 8.59 | 10.53 |
| status.info fg on bg | 4.5 | 7.27 | 6.18 |
| status.progress fg on bg | 4.5 | 7.25 | 6.41 |
| status.attention fg on bg | 4.5 | 6.77 | 8.33 |
| status.critical fg on bg | 4.5 | 6.81 | 6.13 |
| status.success fg on bg | 4.5 | 6.67 | 7.06 |
| status.closed fg on bg | 4.5 | 6.00 | 8.30 |

The focus ring is drawn on the outer side of a 2 px offset, so it sits on the surface rather than on the control; the ring-on-surface pairs above therefore cover filled buttons too. UI component boundaries (inputs, checkboxes) use `border.control`, which meets 3:1 [R4].

<!-- section:typography -->
## Typography

Not covered here. Type tokens are in [[PKG-typography-and-multi-script]]. The only colour rule for type: body and legal text use `text.default`; `text.muted` is allowed for hints, metadata and timestamps, never for required instructions or legal wording.

<!-- section:theming -->
## Theming and tenant branding

Tenants may set `brand.primary` and optional `brand.accent`. The validator in [[PKG-tenant-theme-accessibility]] checks the brand colour in every manifest pair it feeds (text.link on all surfaces at 4.5:1, text.on-action on action.primary.bg at 4.5:1, focus.ring and border.selected at 3:1), in light and dark. If the brand colour fails in dark mode only, the compiler proposes a lighter variant in OKLCH (same hue and chroma, lightness raised in 0.02 steps until all dark pairs pass) and shows it to the tenant admin for approval. Feedback, status and surface colours are not tenant-configurable, so an institution cannot make an error look like a success.

<!-- section:modes -->
## Colour modes and user preferences

Light and dark values are in the semantic roles table. High-contrast mode (`data-mode="high-contrast"`, or `prefers-contrast: more` when the user is on `system`) sets text to neutral.950 or neutral.0, all borders to `border.control`, removes tinted status backgrounds in favour of 2 px tone-coloured borders, and requires 7:1 for text pairs. Forced colours map to system colours; see [[PKG-colour-modes-and-user]].

<!-- section:governance -->
## Governance, versioning and deprecation

Any change to a primitive or semantic colour value is at least a minor release and requires the regenerated manifest table above to be attached to the PR. Changes to status tones or feedback colours are major, because tenants and users learn them, and need product sign-off. The status-to-tone mapping lives with the state machines ([[WF-entity-state-machines]]) and is reviewed by the design system owners when a new status is added.

<!-- section:questions -->
## Open questions

- [ ] Should high-contrast mode target 7:1 for all text (proposed) or only body text (owner: accessibility lead).
- [ ] Approve the automatic dark-mode variant for tenant brand colours, or require tenants to supply a dark brand colour explicitly (owner: product).
- [ ] Confirm the seven status tones with the domain team before the case state machine is final (owner: domain lead, cases).

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Accessibility by construction

Every semantic pair is in the manifest with its required ratio and checked in CI per mode and fixture theme; the table above shows the base values all pass, with the lowest text pair at 6.00:1 and the lowest UI pair at 4.43:1. Focus ring passes 3:1 on all surfaces in both modes. Status tones always pair with a label and icon. High-contrast mode raises text pairs to 7:1.

<!-- check:tenancy -->
### Tenant theme isolation and safety

Only `brand.primary` and `brand.accent` are tenant-settable; they are hex values checked by the theme schema. Feedback, status, surface and text roles are locked so a tenant theme cannot imitate platform warnings.

<!-- check:single-source -->
### Single source of truth and drift

All values live in `packages/tokens/src`; the manifest is generated from `contrast-pairs.yaml`, and the table in this node is regenerated by `pnpm tokens:report` so it cannot drift from code.

<!-- check:change-safety -->
### Change safety and blast radius

A value change that moves any manifest pair by more than 0.5 ratio, or touches status or feedback colours, is a major release with product sign-off and a visual regression run across all fixture themes.

<!-- check:surfaces -->
### Coverage across surfaces and formal outputs

Email receives resolved light-mode hex values only (dark-mode email is left to the client). PDFs use the print theme, which reuses neutral and status ramps but prints status as text. Charts reuse status tones only for status series, never for categorical data.

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C",
    "excerpt": "Text and images of text have a contrast ratio of at least 4.5:1, large text at least 3:1.",
    "id": "R1",
    "ident": "WCAG 2.2 SC 1.4.3",
    "kind": "standard",
    "title": "Understanding SC 1.4.3 Contrast (Minimum)",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html"
  },
  {
    "body": "W3C",
    "excerpt": "Colour is not used as the only visual means of conveying information.",
    "id": "R2",
    "ident": "WCAG 2.2 SC 1.4.1",
    "kind": "standard",
    "title": "Understanding SC 1.4.1 Use of Color",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/use-of-color"
  },
  {
    "body": "W3C",
    "clause": "1.4.3, 1.4.11",
    "id": "R3",
    "ident": "WCAG 2.2",
    "kind": "standard",
    "title": "Web Content Accessibility Guidelines (WCAG) 2.2",
    "url": "https://www.w3.org/TR/WCAG22/",
    "version": "2.2"
  },
  {
    "body": "W3C",
    "excerpt": "User interface components and graphical objects need at least 3:1 against adjacent colours.",
    "id": "R4",
    "ident": "WCAG 2.2 SC 1.4.11",
    "kind": "standard",
    "title": "Understanding SC 1.4.11 Non-text Contrast",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast"
  }
]
```

<!-- end -->
