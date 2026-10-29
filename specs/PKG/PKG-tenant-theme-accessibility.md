---
id: "PKG-tenant-theme-accessibility"
title: "Tenant theme accessibility validation"
parent: "PKG-branding-and-theming"
order: 2
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Contrast and focus-indicator checks on tenant themes and logos at save time; activation blocked on failure"
links: []
rev: 2
syncHash: "6026463f9dacf8e7"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.8.5.2 Tenant theme accessibility validation

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Contrast and focus-indicator checks on tenant themes and logos at save time; activation blocked on failure

<!-- section:statement -->
## Statement

When a tenant admin validates or activates a tenant theme version, `@nomology/theme` shall compute every contrast pair in the contrast manifest that the theme's brand values affect, in light and dark modes, and shall reject the version (status `rejected`, activation blocked) if any pair is below its required ratio or a logo fails the legibility checks.

<!-- section:rationale -->
## Rationale and source

Tenant brand colours feed links, primary buttons, selected states and the focus ring on every page. One failing colour would break WCAG 2.2 AA (1.4.3 text contrast, 1.4.11 non-text contrast) for all of that tenant's users [R1][R2], and our conformance claim ([[APP-accessibility-conformance]]) covers tenant-branded pages. SEBI-regulated tenants must meet digital accessibility obligations under the SEBI circular of 31 July 2025 [R3], so a theme they choose must not be able to make the platform non-conformant. Parent: [[PKG-branding-and-theming]]; schema in [[PKG-tenant-theme-schema-and]].

Pairs checked (from `contrast-manifest.json`, filtered to brand-dependent pairs):

| Pair | Required |
|---|---|
| text.link on surface.default, surface.subtle, surface.raised | 4.5:1 |
| text.on-action on action.primary.bg, .hover, .pressed | 4.5:1 |
| focus.ring on surface.default, surface.subtle, surface.raised | 3:1 |
| border.selected on surface.default | 3:1 |
| logo (light) average contrast against header surface | 3:1 (logos are exempt as text under 1.4.3, but must be legible as the only tenant identifier; platform rule) |

<!-- section:acceptance -->
## Acceptance criteria

- **Given** a draft with `primary: #2556B8`, **when** the admin clicks Validate, **then** all pairs pass in light and dark, status becomes `validated`, and the report lists each pair with its ratio.
- **Given** a draft with `primary: #F2C25C` (light amber), **when** validated, **then** status becomes `rejected` with error `THEME_CONTRAST_TEXT_ON_PRIMARY` and `THEME_CONTRAST_LINK_ON_SURFACE`, the admin sees which pairs failed, the measured ratio and the minimum, and the Activate button is disabled.
- **Given** a primary colour that passes in light but fails in dark and no `primaryDark`, **when** validated, **then** the report proposes a derived dark variant that passes, and the version stays `draft` until the admin accepts or supplies a dark colour.
- **Given** a theme activated under base token version 3.x, **when** base tokens 4.0 change a surface colour, **then** the pre-release dry run re-validates the theme and lists it if it would now fail; the deploy is blocked until the tenant is contacted or the theme is fixed.
- **Given** an API call to `branding.activateTheme` for a `rejected` version, **then** it returns problem type `theme-not-validated` (HTTP 409) and nothing changes.

<!-- section:verification -->
## Verification method

Test: unit tests in `packages/theme/test/validate.spec.ts` with a table of passing and failing colours (including edge values within 0.01 of each threshold); integration test in the tenant admin API that activation of a rejected version is refused; Playwright test of the branding page error display. Evidence for audits: the stored `report` JSON on each `tenant_theme_version`.

<!-- section:priority -->
## Priority

Must. Phase 2 (shared services, design system) of [[PLAN]], before any tenant can self-serve branding.

<!-- section:notes -->
## Notes

Open questions:
- [ ] Is the logo legibility rule (3:1 average against the header) acceptable to institutions with low-contrast logos, or do we offer a neutral logo plate instead (owner: product design).
- [ ] Should platform support be able to override a rejection for a contractual brand colour (proposed: no; the tenant must supply a passing variant) (owner: CCO, accessibility lead).

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Without it, any tenant admin could choose a brand colour that breaks text and focus contrast for all of that tenant's users, and our WCAG 2.2 AA claim and SEBI-regulated tenants' accessibility obligations would fail.

<!-- check:unambiguous -->
### Unambiguous

The pairs and thresholds are listed exactly, the trigger (validate or activate) and the response (status `rejected`, activation blocked) are stated, and the contrast formula is the WCAG 2.x relative luminance ratio.

<!-- check:verifiable -->
### Verifiable

Table-driven unit tests with threshold edge cases, an API negative test (409 on activating a rejected version) and a stored validation report per version as audit evidence.

<!-- check:consistent -->
### Consistent

Thresholds and pair names match [[PKG-colour-and-contrast]]'s manifest; status names match [[PKG-tenant-theme-schema-and]].

<!-- check:traced -->
### Traced

Source: WCAG 2.2 SC 1.4.3 and 1.4.11, SEBI digital accessibility circular (31 July 2025) for regulated tenants, and the platform target in [[APP-accessibility-wcag-2-1-aa]]. Forward trace: `packages/theme/src/validate.ts` and its tests.

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
    "excerpt": "User interface components and graphical objects need at least 3:1 against adjacent colours.",
    "id": "R2",
    "ident": "WCAG 2.2 SC 1.4.11",
    "kind": "standard",
    "title": "Understanding SC 1.4.11 Non-text Contrast",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast"
  },
  {
    "id": "R3",
    "issuer": "Securities and Exchange Board of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "title": "Compliance guidelines for digital accessibility (circular dated 31 July 2025)",
    "url": "https://www.sebi.gov.in/legal/circulars/sep-2025/compliance-guidelines-for-digital-accessibility-circular-rights-of-persons-with-disabilities-act-2016-and-rules-made-thereunder-mandatory-compliance-by-all-regulated-entities-dated-july-31-2025-_96862.html"
  }
]
```

<!-- end -->
