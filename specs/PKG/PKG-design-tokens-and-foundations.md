---
id: "PKG-design-tokens-and-foundations"
title: "Design tokens and foundations"
parent: "PKG-ui-design-system"
order: 1
type: "feature"
template: "designsys"
status: "draft"
owner: null
indicative: false
summary: "DTCG token source, tiers and naming, build outputs (CSS, TS, email, PDF, Figma), governance and versioning"
links: []
rev: 2
syncHash: "df0d5ce2a0ead1df"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.14.1 Design tokens and foundations

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> DTCG token source, tiers and naming, build outputs (CSS, TS, email, PDF, Figma), governance and versioning

<!-- section:purpose -->
## Purpose and scope

This node specifies the token system behind every screen, email and generated document on the platform: the DTCG source in `packages/tokens`, the tier model and naming grammar, the build outputs, and how tokens are governed and versioned. It covers CORD, TERES and every tenant portal (arbitral institution tenants, SEBI ODR institution tenants, the CORD tenant), notification emails and generated PDFs.

Individual foundations are specified in children, and this node only summarises them:

| Foundation | Node |
|---|---|
| Colour palettes, semantic roles, case-status colours, contrast-pair manifest | [[PKG-colour-and-contrast]] |
| Type scale, legal and data typography, per-script fonts | [[PKG-typography-and-multi-script]] |
| Light, dark, high-contrast, forced colours, reduced motion, density | [[PKG-colour-modes-and-user]] |
| Charts and dashboards | [[PKG-data-visualisation-palette]] |
| Awards, procedural orders and eBundles in print | [[PKG-print-and-formal-document-theme]] |
| Tenant brand slots and validation | [[PKG-branding-and-theming]], [[PKG-tenant-theme-schema-and]] |

Out of scope: component-specific behaviour (component nodes under [[PKG-ui-design-system]]), tenant terminology ([[PKG-tenant-terminology-and-copy]]) and page layouts.

<!-- section:architecture -->
## Token architecture and naming

**Source format.** Tokens are written in the DTCG Format Module 2025.10 JSON (`$value`, `$type`, `$description`, `$extensions`) [R1]. Colours use the DTCG Color Module object form with `colorSpace: "srgb"` and a `hex` fallback [R2]. Modes, density and tenant brands are expressed with the DTCG Resolver Module (sets and modifiers) [R3].

**Tiers.**

| Tier | Example | Who may reference it |
|---|---|---|
| Primitive | `color.blue.600`, `dimension.space.4`, `font.family.sans-latin` | Only semantic tokens. Never apps, components or tenant themes |
| Semantic | `color.text.default`, `color.action.primary.bg`, `color.status.attention.fg`, `space.inset.md`, `typography.body.md` | Components and, rarely, app layout code |
| Component | `button.primary.bg.hover`, `datatable.row.bg.selected` | Only the owning component |

**Naming grammar.** `{category}.{role}.{variant?}.{property?}.{state?}` in lowercase kebab segments, for example `color.feedback.error.border`, `color.action.danger.bg.pressed`. CSS custom properties are prefixed `--nm-` and joined with hyphens (`--nm-color-action-primary-bg`). States use a closed list: `default`, `hover`, `pressed`, `selected`, `disabled`, `focus`.

**Repository layout.**

```
packages/tokens/
  src/primitive/{color,dimension,font,motion,shadow}.tokens.json
  src/semantic/{color,space,size,typography,radius,elevation,motion}.tokens.json
  src/component/{button,field,datatable,dialog,badge,...}.tokens.json
  src/modes/{light,dark,high-contrast}.tokens.json   # semantic colour overrides only
  src/density/{comfortable,compact}.tokens.json
  src/print/print.tokens.json                       # fixed print theme
  resolver.json                                     # DTCG resolver: sets + modifiers (mode, density)
  build.ts                                          # Style Dictionary configuration
```

**When a new token is allowed.** A new semantic token needs a role that at least two components or two apps need, and a description of when to use it. A new component token is allowed when a component state needs a value that differs from the semantic role. One-off values in apps are recorded as lint exceptions with an expiry date, not as tokens.

<!-- section:colour -->
## Colour

Summary only; exact palettes, semantic roles and the full contrast-pair manifest are in [[PKG-colour-and-contrast#colour]].

- Primitive ramps: `neutral` (0 to 950), `blue` (brand default), `red`, `amber`, `green`, `violet`.
- Semantic roles: `surface`, `text`, `border`, `action`, `feedback` (error, warning, success, info), `focus`, `status` (seven case and document status tones), `dataviz`.
- Every semantic text / background pair is listed in `contrast-manifest.json` with its required ratio (4.5:1 text, 3:1 large text, UI components and focus indicators) and checked in CI for every mode and fixture tenant theme [R4][R5].

<!-- section:typography -->
## Typography

Summary only; see [[PKG-typography-and-multi-script#typography]].

- Families: a sans serif for UI (Latin), a serif for legal text (awards, orders), a monospace for references and hashes, and per-script Noto fallbacks for Devanagari, Tamil, Kannada, Telugu, Bengali and Traditional / Simplified Chinese.
- Type scale in `rem` from 12 px to 36 px; body is 16 px with line height 1.5 (1.7 for Indic scripts).
- Composite tokens: `typography.heading.{xl,lg,md,sm}`, `typography.body.{lg,md,sm}`, `typography.legal.{body,heading,footnote}`, `typography.data.{cell,numeric}`.
- Fonts are self-hosted per region and loaded with `font-display: swap` and metric-matched fallbacks.

<!-- section:spacing -->
## Spacing, sizing and layout

**Spacing scale** (4 px base, in `rem` at 16 px root):

| Token | Value |
|---|---|
| `space.0` | 0 |
| `space.0-5` | 0.125rem (2 px) |
| `space.1` | 0.25rem (4 px) |
| `space.2` | 0.5rem (8 px) |
| `space.3` | 0.75rem (12 px) |
| `space.4` | 1rem (16 px) |
| `space.5` | 1.25rem (20 px) |
| `space.6` | 1.5rem (24 px) |
| `space.8` | 2rem (32 px) |
| `space.10` | 2.5rem (40 px) |
| `space.12` | 3rem (48 px) |
| `space.16` | 4rem (64 px) |

Semantic aliases: `space.inset.{sm,md,lg}` (padding inside controls and cards), `space.stack.{sm,md,lg}` (vertical rhythm), `space.inline.{sm,md}` (gaps between inline items).

**Sizing.**

| Token | Comfortable | Compact | Note |
|---|---|---|---|
| `size.control.height` | 2.5rem (40 px) | 2rem (32 px) | Buttons, inputs, selects |
| `size.target.min` | 1.5rem (24 px) | 1.5rem (24 px) | Never below WCAG 2.5.8 minimum [R6] |
| `size.target.touch` | 2.75rem (44 px) | n/a | Used by `(counsel)` party pages and the public filing entry on coarse pointers |
| `size.icon.{sm,md,lg}` | 16 / 20 / 24 px | 16 / 16 / 20 px | |

Compact density is available only in `(secretariat)`, `(transcriber)` and `(platform-admin)` route groups, where users work in dense queues on desktop.

**Layout.** Breakpoints `bp.sm` 40rem (640 px), `bp.md` 48rem, `bp.lg` 64rem, `bp.xl` 80rem, `bp.2xl` 96rem; 4-column grid below `md`, 12-column from `lg`; content max width `size.content.max` 80rem; reading width for legal text `size.measure.legal` 42rem. All layouts must reflow at 320 CSS px [R7].

**Direction.** All spacing, border and radius tokens are applied through CSS logical properties (`padding-inline-start`, `border-inline-end`, `inset-inline-start`) so layouts mirror in right-to-left locales [R8]. Physical properties are blocked by stylelint in `packages/ui`.

<!-- section:shape -->
## Radius, borders and elevation

| Token | Value | Use |
|---|---|---|
| `radius.none` | 0 | Tables, document viewer |
| `radius.sm` | 0.25rem | Inputs, badges |
| `radius.md` | 0.5rem | Buttons, cards (default) |
| `radius.lg` | 0.75rem | Dialogs, popovers |
| `radius.full` | 9999px | Avatars, pills |
| `border.width.default` | 1px | Containers, inputs |
| `border.width.strong` | 2px | Selected rows, active tab |
| `focus.ring.width` | 2px | Focus indicator |
| `focus.ring.offset` | 2px | Gap between control and ring |

Elevation levels: `elevation.0` flat; `elevation.1` cards and table headers when sticky; `elevation.2` popovers, menus, comboboxes; `elevation.3` dialogs and toasts. In dark mode shadows are weak, so each level also raises the surface colour (`surface.default` → `surface.raised` → `surface.overlay`). In forced-colours mode shadows are removed by the browser, so every elevated surface also has a `border.width.default` border in `CanvasText` [R9].

Tenants may choose `radius.brand` from `none | sm | md` only; it maps the `radius.md` alias.

<!-- section:motion -->
## Motion

| Token | Value | Use |
|---|---|---|
| `motion.duration.instant` | 0ms | Reduced motion substitute |
| `motion.duration.fast` | 100ms | Hover, pressed |
| `motion.duration.base` | 150ms | Popover open, toast in |
| `motion.duration.slow` | 250ms | Dialog, drawer |
| `motion.duration.progress` | 1200ms | Indeterminate progress loop |
| `motion.easing.standard` | cubic-bezier(0.2, 0, 0, 1) | Most transitions |
| `motion.easing.exit` | cubic-bezier(0.3, 0, 1, 1) | Elements leaving |

Motion is used only for state change feedback and spatial continuity (popovers, dialogs, toasts). No parallax, no auto-playing decorative animation. Under `prefers-reduced-motion: reduce` [R10] or the user's "reduce motion" setting, all durations except `progress` become `instant` and slide transitions become fades. Kept as essential: upload progress bars and the indeterminate busy indicator (slowed to a single pulse per 2 s). Details in [[PKG-colour-modes-and-user#motion]].

<!-- section:iconography -->
## Iconography and imagery

- One outline icon set on a 24 px grid with 1.5 px stroke, wrapped by `<Icon name>`; icons inherit `currentColor` so they take their colour from text tokens.
- Decorative icons (next to a visible label) get `aria-hidden="true"`; meaningful icons standing alone must have an accessible name, which `IconButton` makes a required prop.
- Domain icons required: statement of claim, response, exhibit, procedural order, award, hearing (virtual and in person), transcript, bundle, deadline, payment, neutral, party, counsel, secretariat, AI-generated content marker.
- Directional icons (`arrow-start`, `chevron-end`) mirror in RTL; play, check, upload, download and clock do not.
- No tenant-uploaded icons. Tenant imagery is limited to logos (see [[PKG-tenant-theme-schema-and]]).

<!-- section:theming -->
## Theming and tenant branding

Summary; the full schema is in [[PKG-tenant-theme-schema-and#theming]].

A tenant theme is a DTCG resolver modifier `brand` with one context per tenant. A tenant may set only: `brand.primary` colour, optional `brand.accent` colour, `radius.brand`, three logos (light, dark, square mark), favicon, and a heading font chosen from an allow-list. Everything else (text, surfaces, feedback, status, focus, typography scale, spacing) is locked. Tenant themes are validated and compiled when the tenant admin activates them, not at request time; the compiled stylesheet is content-hashed and stored in the tenant's region. Emails and PDFs get the tenant's logo and primary colour from the same compiled output (resolved hex values), but the formal document body uses the fixed print theme ([[PKG-print-and-formal-document-theme]]).

<!-- section:modes -->
## Colour modes and user preferences

Summary; see [[PKG-colour-modes-and-user]]. Modes are a resolver modifier `mode` with contexts `light`, `dark`, `high-contrast`; density is a modifier `density` with `comfortable` and `compact`. The server sets `data-mode` and `data-density` on `<html>` from the user's stored preference, otherwise the tenant default, otherwise `system` (CSS media queries decide), so there is no flash of the wrong mode.

<!-- section:distribution -->
## Build, distribution and consumption

Build with Style Dictionary (v4 or later, which supports DTCG) [R11], driven by `resolver.json`:

| Output | Path | Consumer | Notes |
|---|---|---|---|
| CSS custom properties | `dist/css/base.css`, `dist/css/modes.css` | `apps/web`, Storybook | Wrapped in `@layer nm.tokens`; modes scoped to `[data-mode=...]` and media queries |
| TypeScript | `dist/ts/tokens.ts` | Components needing values in JS (charts, canvas viewer) | Semantic tier only, values are `var(--nm-...)` references plus resolved fallbacks |
| Email JSON | `dist/email/light.json` | `packages/notifications` email renderer | Resolved hex and px; email clients do not reliably support custom properties |
| PDF / print JSON | `dist/pdf/print.json` | `packages/documents` PDF renderer | Fixed print theme, resolved values in pt and mm |
| Figma variables | `dist/figma/variables.json` | Figma via import plugin | One-way sync from repo to Figma |
| Contrast manifest | `dist/contrast-manifest.json` | CI check, `@nomology/theme` validator | Every required pair with its threshold |

**CSS layering.** `@layer nm.reset, nm.tokens, nm.theme, nm.components, nm.app;` [R12]. Tenant theme stylesheets populate `nm.theme` and can therefore only override the brand custom properties they define; component styles cannot be overridden by tenant CSS because tenants never supply CSS.

**Runtime tenant themes** are delivered as a `<link rel="stylesheet">` to the compiled, hashed file under the tenant host (`/_theme/{hash}.css`), which works with the nonce or hash-based CSP in [[APP-security-headers-csp-cors]] without `unsafe-inline` styles.

<!-- section:governance -->
## Governance, versioning and deprecation

- **Owners**: design system lead (engineering) and a named product designer; CODEOWNERS on `packages/tokens`, `packages/theme`, `packages/ui`.
- **Change process**: proposal as a GitHub issue using the "token request" template (role, where used, why an existing token does not fit) → PR with a Changeset → automated contrast, lint and visual regression results attached → approval by both owners. Target response time to a product team request: 3 working days.
- **Semver for tokens** [R13]: patch = value change that keeps every manifest pair passing and moves no pair by more than 0.5 ratio; minor = new token, new mode context; major = rename, removal, type change, or a value change that alters an approved tenant-facing appearance (for example print theme or status colours).
- **Deprecation**: deprecated tokens carry `$deprecated` with a replacement and stay for at least one minor release and 8 weeks; stylelint warns, then errors at removal.
- **Release notes**: Changesets generates a changelog per release; a short tenant-readable "visual changes" note is added to release notes ([[DEP-release-notes-and-change]]) whenever a change is visible in tenant themes, emails or PDFs.
- **Rollout of breaking changes**: all apps in the monorepo upgrade in the same PR; active tenant themes are re-validated against the new base before deploy, and tenants whose theme would fail are contacted before release.

<!-- section:questions -->
## Open questions

- [ ] Confirm Style Dictionary as the build tool and the minimum version that supports the DTCG 2025.10 resolver module, or whether we write a small resolver step ourselves (owner: design system lead).
- [ ] Figma: who may edit variables in the Figma library, and do we accept the one-way repo → Figma sync (owner: product design).
- [ ] Is compact density wanted in the neutral workspace for award drafting, or only in queues (owner: product).
- [ ] Do we need a native mobile token output in the next 12 months (owner: CTO).

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Accessibility by construction

Accessibility is enforced by data, not by review alone. `dist/contrast-manifest.json` lists every semantic foreground / background pair with its required ratio; CI computes WCAG relative-luminance contrast for each pair in light, dark and high-contrast modes and for all five fixture tenant themes, and fails the build below threshold (manifest in [[PKG-colour-and-contrast]]). Focus indicator tokens (`focus.ring.width` 2 px, offset 2 px, `color.focus.ring`) are in the manifest at 3:1 against every surface token. `size.target.min` is 24 px in both densities, with 44 px touch targets for party pages. Type sizes are in `rem` and no text container uses fixed heights, so 200 percent zoom and WCAG 1.4.12 spacing overrides do not clip; Storybook has a "text spacing" toolbar toggle tested in visual regression. Status, error and required states always include text or an icon (enforced by component APIs such as `StatusBadge` requiring a label). Forced colours map to system colours ([[PKG-colour-modes-and-user]]).

<!-- check:tenancy -->
### Tenant theme isolation and safety

Tenants set typed values only (hex colours, enums, asset IDs); there is no free CSS. Themes compile at activation into a content-hashed stylesheet stored in the tenant's home region and served from the tenant's own host, so the URL and CDN cache key are tenant-specific. Security indicators, feedback colours, status colours and focus colours are locked. If a theme fails to load, the base theme is used. Details in [[PKG-tenant-theme-schema-and]].

<!-- check:single-source -->
### Single source of truth and drift

The DTCG JSON in `packages/tokens/src` is the only source. Figma variables, CSS, TypeScript, email and PDF outputs are generated from it; sync to Figma is one-way. stylelint (`color-no-hex`, `declaration-property-unit-allowed-list`, a custom `nm/use-logical-properties` rule) and an ESLint rule on inline `style` block raw values in `packages/ui` and `apps/web`. A nightly script reports unused tokens and raw values per app; the baseline count is recorded in the first release and must go down each quarter.

<!-- check:change-safety -->
### Change safety and blast radius

Every token PR runs visual regression over all stories × 5 fixture themes × light / dark / high contrast, plus LTR / RTL for direction-sensitive components, and both owners approve diffs. Token semver rules are in the governance section. Rollback is a revert of the token package version in the same monorepo; tenant themes record the base token version they were validated against, so a failing re-validation blocks the deploy rather than the tenant.

<!-- check:i18n -->
### Scripts, languages and direction

Logical properties are mandatory for spacing, border and radius. Indic scripts get a taller line height (1.7) via `:lang()` selectors; CJK uses `word-break: auto-phrase` where supported and never relies on spaces. Fixed widths are not used for text containers. Directional icons mirror; non-directional icons do not. Details in [[PKG-typography-and-multi-script]].

<!-- check:performance -->
### Runtime cost and first paint

Proposed budgets: base token CSS ≤ 12 KB compressed, one tenant theme ≤ 3 KB. Theme and mode are resolved on the server and written to `<html>` attributes in the first response, so there is no flash. Theme files are immutable and content-hashed (`Cache-Control: public, max-age=31536000, immutable`); activation produces a new hash. Tokens are CSS custom properties, so server components render themed UI without `'use client'`.

<!-- check:surfaces -->
### Coverage across surfaces and formal outputs

Web uses CSS custom properties; email uses resolved hex values from `dist/email`; PDFs use `dist/pdf/print.json` and the fixed print theme ([[PKG-print-and-formal-document-theme]]); dashboards use [[PKG-data-visualisation-palette]]. Embedded third-party surfaces (video hearing room, e-signature) receive at most the tenant logo and primary colour through the vendor's own branding settings; where they cannot be themed they are shown with neutral platform framing (see [[INT-third-party-component]]).

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C Design Tokens Community Group",
    "id": "R1",
    "ident": "DTCG Format",
    "kind": "standard",
    "title": "Design Tokens Format Module 2025.10",
    "url": "https://www.designtokens.org/tr/2025.10/format/",
    "version": "2025.10"
  },
  {
    "body": "W3C Design Tokens Community Group",
    "id": "R2",
    "ident": "DTCG Color",
    "kind": "standard",
    "title": "Design Tokens Color Module 2025.10",
    "url": "https://www.designtokens.org/tr/2025.10/color/",
    "version": "2025.10"
  },
  {
    "body": "W3C Design Tokens Community Group",
    "id": "R3",
    "ident": "DTCG Resolver",
    "kind": "standard",
    "title": "Design Tokens Resolver Module 2025.10",
    "url": "https://www.designtokens.org/tr/2025.10/resolver/",
    "version": "2025.10"
  },
  {
    "body": "W3C",
    "excerpt": "Text and images of text have a contrast ratio of at least 4.5:1, large text at least 3:1.",
    "id": "R4",
    "ident": "WCAG 2.2 SC 1.4.3",
    "kind": "standard",
    "title": "Understanding SC 1.4.3 Contrast (Minimum)",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html"
  },
  {
    "body": "W3C",
    "excerpt": "User interface components and graphical objects need at least 3:1 against adjacent colours.",
    "id": "R5",
    "ident": "WCAG 2.2 SC 1.4.11",
    "kind": "standard",
    "title": "Understanding SC 1.4.11 Non-text Contrast",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast"
  },
  {
    "body": "W3C",
    "excerpt": "Targets are at least 24 by 24 CSS pixels, with listed exceptions such as spacing.",
    "id": "R6",
    "ident": "WCAG 2.2 SC 2.5.8",
    "kind": "standard",
    "title": "Understanding SC 2.5.8 Target Size (Minimum)",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum"
  },
  {
    "body": "W3C",
    "excerpt": "Content reflows without two-dimensional scrolling at 320 CSS px width.",
    "id": "R7",
    "ident": "WCAG 2.2 SC 1.4.10",
    "kind": "standard",
    "title": "Understanding SC 1.4.10 Reflow",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/reflow"
  },
  {
    "body": "W3C",
    "id": "R8",
    "ident": "css-logical-1",
    "kind": "standard",
    "title": "CSS Logical Properties and Values Level 1",
    "url": "https://www.w3.org/TR/css-logical-1/"
  },
  {
    "body": "W3C",
    "excerpt": "Defines forced colors mode and the forced-color-adjust property.",
    "id": "R9",
    "ident": "css-color-adjust-1",
    "kind": "standard",
    "title": "CSS Color Adjustment Module Level 1",
    "url": "https://www.w3.org/TR/css-color-adjust-1/"
  },
  {
    "body": "W3C",
    "excerpt": "Defines prefers-color-scheme, prefers-reduced-motion, prefers-contrast and forced-colors.",
    "id": "R10",
    "ident": "Media Queries 5",
    "kind": "standard",
    "title": "Media Queries Level 5",
    "url": "https://www.w3.org/TR/mediaqueries-5/"
  },
  {
    "id": "R11",
    "kind": "vendor",
    "retrieved": "2026-10-28",
    "title": "Design Tokens Community Group format support",
    "url": "https://styledictionary.com/info/dtcg/",
    "vendor": "Style Dictionary"
  },
  {
    "body": "W3C",
    "id": "R12",
    "ident": "css-cascade-5",
    "kind": "standard",
    "title": "CSS Cascading and Inheritance Level 5 (cascade layers)",
    "url": "https://www.w3.org/TR/css-cascade-5/"
  },
  {
    "body": "semver.org",
    "id": "R13",
    "ident": "SemVer 2.0.0",
    "kind": "standard",
    "title": "Semantic Versioning 2.0.0",
    "url": "https://semver.org/",
    "version": "2.0.0"
  }
]
```

<!-- end -->
