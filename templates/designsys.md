# Template: Design system foundations (`designsys`)

Generated from `designsys.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies the shared visual foundations (design tokens for colour, typography, spacing, radius, elevation, motion and icons), how tenants may brand them, and how they are versioned and governed, so every screen, email and document looks consistent and accessible for every tenant.

**Depth:** 3–10 pages. Token tables, contrast pairs and the tenant theme schema must be exact (names and values), because components and tenant admin validation code are built from them. Rationale stays short. Split into children per foundation (colour, typography, motion and so on) when one section exceeds about two pages, and put individual components in Component nodes, not here.

**Default child template:** `component`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `purpose` Purpose and scope (level 1)

What this foundation covers (all tokens, or one family such as colour), which products and surfaces consume it (CORD, TERES, tenant portals, emails, generated PDFs), and what it deliberately leaves to component specs or tenant settings.

Illustrative example (not a requirement):

> **Scope:** colour, typography, spacing, radius, elevation, motion and icon tokens for every web surface of CORD and TERES, plus the email and PDF renderers.
> 
> **Consumers:** `apps/web` (all persona route groups), `packages/ui` (components), `packages/notifications` (email templates), `packages/documents` (award, order and bundle PDFs), Storybook, the Figma library.
> 
> **Out of scope:** component behaviour (see Component nodes), tenant settings storage and admin screens (see *Tenant-level settings* and *Branding and theming*), marketing websites.

### `architecture` Token architecture and naming (level 1)

The token tiers (primitive, semantic, component), the naming grammar, the source format (DTCG JSON), file layout in the repo and which tier tenants and components may reference. State the rule for when a new token is allowed.

Illustrative example (not a requirement):

> | Tier | Example name | Who references it | Tenant may override? |
> |---|---|---|---|
> | Primitive | `color.blue.600` | Semantic tokens only | No (tenants supply brand primitives through the theme schema) |
> | Semantic | `color.action.primary.bg` | Components, page layouts | Only via the allowed brand slots |
> | Component | `button.primary.bg` | That component only | No |
> 
> Naming grammar: `<category>.<role>.<variant>.<property>.<state>`, e.g. `color.feedback.danger.text.hover`. CSS output: `--ds-color-feedback-danger-text-hover`.
> 
> Source: `packages/tokens/src/**/*.tokens.json` (DTCG 2025.10). Rule: components must never reference primitives; a new semantic token needs two or more real uses.

### `colour` Colour (level 1)

Primitive palettes, semantic colour roles (surface, text, border, action, feedback, focus, data-visualisation, case status) and the required contrast pairs. Give every pair that must pass, with the WCAG ratio it must meet.

Illustrative example (not a requirement):

> ```json
> {
>   "color": {
>     "$type": "color",
>     "blue": { "600": { "$value": { "colorSpace": "srgb", "components": [0.169, 0.373, 0.702], "hex": "#2b5fb3" } } },
>     "action": { "primary": { "bg": { "$value": "{color.blue.600}" } } }
>   }
> }
> ```
> 
> | Foreground | Background | Minimum ratio |
> |---|---|---|
> | `color.text.default` | `color.surface.default` | 4.5:1 |
> | `color.action.primary.text` | `color.action.primary.bg` | 4.5:1 |
> | `color.border.input` | `color.surface.default` | 3:1 (non-text) |
> | `color.focus.ring` | every surface token | 3:1 |
> 
> Case status colours (Filed, Under review, Hearing scheduled, Award issued) always pair with a text label and icon, never colour alone (illustrative values).

### `typography` Typography (level 1)

Font families and fallbacks per script, the type scale, line heights, weights, and the composite typography tokens used for headings, body, legal text and data. Say how fonts are loaded and what happens when a tenant font is missing.

Illustrative example (not a requirement):

> | Token | Size / line height | Use |
> |---|---|---|
> | `type.heading.lg` | 28 / 36 px | Case title on case overview |
> | `type.body.md` | 16 / 24 px | Default body, form fields |
> | `type.legal.md` | 16 / 26 px, serif | Award and order text, Terms of Reference |
> | `type.data.sm` | 14 / 20 px, tabular figures | Fee tables, bundle page numbers |
> 
> Families: Latin `Inter`, Devanagari `Noto Sans Devanagari`, Traditional Chinese `Noto Sans TC` (illustrative choices). Fonts self-hosted per region, `font-display: swap`, with metric-matched fallbacks to avoid layout shift. Minimum body size 16 px; no text below 12 px.

### `spacing` Spacing, sizing and layout (level 2)

The spacing scale, sizing tokens (including minimum target size), layout grid, breakpoints and density modes. Note which tokens use logical directions so layouts mirror in right-to-left languages.

Illustrative example (not a requirement):

> - Spacing scale (4 px base): `space.1`=4, `space.2`=8, `space.3`=12, `space.4`=16, `space.6`=24, `space.8`=32
> - `size.target.min` = 24 px (WCAG 2.5.8); `size.target.comfortable` = 44 px for touch-first persona views (party filing on mobile)
> - Breakpoints: `bp.sm` 480, `bp.md` 768, `bp.lg` 1024, `bp.xl` 1440
> - Density: `comfortable` (parties, counsel) and `compact` (secretariat case list, transcriber queue) switch `space.*` and `size.control.*`, never font size
> - Insets use logical names: `space.inset.inline-start`, not `left`

### `shape` Radius, borders and elevation (level 2)

Radius, border width and shadow / elevation tokens, the meaning of each elevation level, and how elevation is shown in dark mode and forced-colours mode where shadows disappear.

Illustrative example (not a requirement):

> | Token | Value | Meaning |
> |---|---|---|
> | `radius.sm` | 4 px | Inputs, chips |
> | `radius.md` | 8 px | Cards, document tiles |
> | `elevation.1` | `shadow` 0 1 2 / 8% | Cards on case overview |
> | `elevation.3` | `shadow` 0 8 24 / 16% | Dialogs, hearing-join panel |
> 
> Every elevated surface also has a 1 px `color.border.subtle` so it stays distinct in dark mode and Windows High Contrast, where shadows are removed. Tenants may choose a radius preset (`sharp`, `default`, `rounded`), not arbitrary values.

### `motion` Motion (level 2)

Duration and easing tokens, what motion is used for, and the reduced-motion behaviour. Name any motion that is essential and therefore kept when reduced motion is requested.

Illustrative example (not a requirement):

> ```json
> {
>   "motion": {
>     "duration": { "$type": "duration", "fast": { "$value": { "value": 120, "unit": "ms" } }, "moderate": { "$value": { "value": 240, "unit": "ms" } } },
>     "easing": { "$type": "cubicBezier", "standard": { "$value": [0.2, 0, 0, 1] } }
>   }
> }
> ```
> - Under `prefers-reduced-motion: reduce`, all `motion.duration.*` resolve to 0 ms except the upload progress bar (essential, shows progress)
> - No auto-playing motion longer than 5 seconds; no parallax; nothing flashes more than 3 times per second

### `iconography` Iconography and imagery (level 2)

Icon set, sizes, stroke, how icons get colour from tokens, accessible naming rules (decorative vs meaningful), and the domain icons the platform needs (document types, hearing, award, deadline).

Illustrative example (not a requirement):

> - One open-licence outline icon set, sizes `icon.sm` 16, `icon.md` 20, `icon.lg` 24; colour always `currentColor`
> - Domain icons owned by us: `doc-pleading`, `doc-exhibit`, `doc-award`, `hearing-virtual`, `deadline`, `seal` (tenant may not replace)
> - Decorative icons: `aria-hidden="true"`; icon-only buttons need an accessible name ("Download bundle")
> - Tenant logos: SVG or PNG uploaded through tenant admin, sanitised, served from the tenant's region; light and dark variants required

### `theming` Theming and tenant branding (level 1)

Exactly which brand slots a tenant may set, the schema and limits for each, how a tenant theme is resolved on top of the base (DTCG resolver sets and modifiers), how it is validated before activation, and how it reaches the page, emails and PDFs.

Illustrative example (not a requirement):

> Allowed tenant slots (theme schema v1):
> 
> | Slot | Type | Constraint |
> |---|---|---|
> | `brand.primary` | colour | Generated tonal ramp must give 4.5:1 for `action.primary.text` on `action.primary.bg` in light and dark |
> | `brand.accent` | colour | Decorative only, never text |
> | `brand.logo` | asset | SVG sanitised, max 200 KB, light + dark |
> | `brand.font.heading` | enum | From approved font list only |
> | `shape.preset` | enum | `sharp` / `default` / `rounded` |
> 
> Resolution order: `base` set → `tenant` modifier (e.g. context `hkiac`, `sebi-odr-inst-1`) → `mode` modifier (`light`, `dark`) → `density` modifier. A theme that fails any contrast pair cannot be activated; tenant admin sees which pair failed and a suggested nearest passing shade.

### `modes` Colour modes and user preferences (level 2)

Light, dark and high-contrast modes, how the mode is chosen (system preference, user setting, tenant default), forced-colours support, and how preferences are stored without causing a flash of the wrong theme.

Illustrative example (not a requirement):

> - Modes: `light` (default), `dark`, `high-contrast` (7:1 text pairs)
> - Precedence: user setting → tenant default → `prefers-color-scheme`
> - User choice stored in the user profile (server) and mirrored in a cookie so the server renders the right `data-theme` on first paint
> - `forced-colors: active`: components use system colour keywords (`CanvasText`, `Highlight`); focus rings and selected states remain visible
> - Awards and bundles always render in the light print theme regardless of the viewer's mode

### `distribution` Build, distribution and consumption (level 2)

How tokens are built (tool, outputs, platforms), published and consumed by apps, components, email and PDF renderers and Figma, including CSS layering and how runtime tenant themes are injected.

Illustrative example (not a requirement):

> Build: Style Dictionary reads DTCG source and emits
> - `@nomology/tokens/css` — `:root` custom properties in `@layer ds.tokens`
> - `@nomology/tokens/ts` — typed constants for charts and canvas
> - `@nomology/tokens/email` — inlined hex values for email templates
> - `@nomology/tokens/pdf` — values for the PDF renderer
> 
> Runtime tenant theme: the server resolves the tenant in middleware, loads the compiled theme CSS (generated at activation, stored per region, content-hashed) and links it in the root layout. No tenant values are interpolated into CSS at request time. Figma variables are synced from the same source; Figma is never the source of truth.

### `governance` Governance, versioning and deprecation (level 1)

Who owns the system, how changes are proposed and reviewed, the semver policy for tokens, deprecation windows, release notes, and how breaking changes are rolled out across apps and tenant themes.

Illustrative example (not a requirement):

> - Owners: design systems lead (design), `@nomology/ui-platform` (code) via CODEOWNERS on `packages/tokens`
> - Change request: issue with use cases → design review → token PR with Storybook and visual diff across all active tenant themes
> - Semver: rename or removal = major; new token = minor; value change within the same role = patch, but any value change that alters a contrast pair needs accessibility sign-off
> - Deprecation: `$deprecated: "Use color.feedback.danger.text"`; kept for two minor releases; lint warns, then errors
> - Releases via Changesets; changelog lists every token added, changed, deprecated

### `questions` Open questions (level 3)

Unresolved decisions as a checklist, each with an owner.

Illustrative example (not a requirement):

> - [ ] Do we allow tenants a second brand colour for navigation? (Design systems lead)
> - [ ] Approved font list for Traditional Chinese and Tamil (Design + Engineering)
> - [ ] Is high-contrast mode a user setting or only via OS forced colours? (Accessibility)
> - [ ] Do generated PDFs carry the tenant theme or a neutral institutional template? (Product + tenant contracts)

## Checks

### `accessibility` Accessibility by construction

**Question:** Do the tokens guarantee WCAG 2.2 AA (contrast, focus visibility, target size, text resizing, motion) for every combination of tenant theme, colour mode and density, so components cannot fail these criteria by using the system correctly?

- Is there a machine-readable list of every foreground / background pair that must pass, with its required ratio (4.5:1 text, 3:1 large text, UI components and focus indicators), and is it checked automatically in CI for every theme × mode?
- Which tokens define the focus indicator (width, offset, colour), and does it stay at least 3:1 against every surface token, including tenant brand surfaces and dark mode?
- Do size tokens enforce the 24 × 24 px minimum target (2.5.8), and which persona views use larger touch targets?
- Does the type scale still work at 200% zoom and with WCAG 1.4.12 text spacing overrides (line height 1.5, letter spacing 0.12em) without clipping in fixed-height tokens?
- Which semantic roles (status, errors, required fields, case stages) are guaranteed never to rely on colour alone, and how is that enforced in the component layer?
- What happens under forced-colours mode and prefers-contrast: more — which tokens map to system colours?
- Who signs off any token value change that alters a contrast pair, and what evidence (report artefact) is attached to the release?

**Good answer:** A contrast-pair manifest in the token package, checked by a CI job that fails the build if any pair in any theme × mode drops below its ratio, with the report stored as a release artefact. Focus, target size and text tokens are specified with exact values, and forced-colours behaviour is defined for every interactive role.

**Red flags:**

- Contrast is checked by eye in Figma only, or only for the default theme.
- Focus ring colour taken from the tenant brand colour without a contrast check.
- Status or error meaning carried by colour tokens with no paired icon or text rule.
- Fixed pixel heights on text containers that clip when text is resized.

### `tenancy` Tenant theme isolation and safety

**Question:** Can a tenant's theme ever appear for another tenant, or be used to inject code, break layouts or impersonate another institution, and what prevents each case?

- Are tenant theme values constrained to a typed schema (colour, enum, sanitised asset) and compiled at activation time, rather than free-text CSS interpolated into pages at request time?
- How are uploaded logos and SVGs sanitised (scripts, external references, `foreignObject`), size-limited and served, and from which region's storage?
- Is the compiled theme CSS cache key and URL tenant-specific and content-hashed, so a CDN or browser can never serve tenant A's theme on tenant B's domain? Are authenticated pages that embed theme data marked private?
- For a user who belongs to two tenants (counsel at HKIAC and at a SEBI ODR institution), does switching tenant change the theme, logo and product name everywhere, including open tabs, emails and downloads?
- Do tenant themes stay within the platform's Content Security Policy (no inline styles that need `unsafe-inline`, fonts and images only from our origins)?
- Which elements can a tenant never change (security indicators, platform consent text, the sign-in page trust cues) so a theme cannot imitate platform warnings or another institution?
- What happens to the live site if a theme fails to load: does it fall back to the neutral base theme rather than an unstyled or another tenant's page?

**Good answer:** A versioned theme schema with validation rules per slot, compile-on-activation into a content-hashed, tenant-scoped CSS file stored in the tenant's region, and a stated CSP that the theme fits within. The answer lists the non-themable elements and shows the fallback to the neutral base theme with an alert.

**Red flags:**

- Tenant admins can paste arbitrary CSS or hex values that are injected into a style tag.
- One shared theme URL keyed by hostname only, cached publicly.
- Uploaded SVG logos rendered inline without sanitisation.
- No list of elements a tenant cannot restyle.

### `single-source` Single source of truth and drift

**Question:** Is there exactly one source for every token, and how do we detect when Figma, code, emails, PDFs or hand-written CSS drift from it?

- Is the DTCG JSON in the repo the only source, with Figma variables and all platform outputs generated from it? Which direction does sync run, and who can change Figma variables?
- Which lint rules (for example stylelint and ESLint) block raw hex values, pixel spacing and ad-hoc shadows in apps and components, and what is the current count of violations?
- How are email templates and the PDF renderer (awards, procedural orders, eBundles) kept on the same tokens when they cannot use CSS custom properties?
- How do we find tokens that are defined but never used, or used but not documented?
- Are DTCG `$extensions` keys used (e.g. for Figma IDs), and do our tools preserve them on round-trip?
- How does a designer know which token to use: is there a searchable token reference with usage guidance in Storybook?

**Good answer:** The repo DTCG files are the only source; Figma, CSS, TypeScript, email and PDF outputs are generated in CI and any manual Figma variable edit is overwritten or flagged. Lint rules block hard-coded values with a tracked baseline that is trending to zero, and an unused-token report runs weekly.

**Red flags:**

- Figma and code both edited by hand and reconciled occasionally.
- Emails or PDFs with their own hard-coded brand colours.
- No lint rule against raw colour or spacing values.

### `change-safety` Change safety and blast radius

**Question:** Because one token change reaches every tenant and every screen, how is a change reviewed, tested across all tenant themes and modes, released and rolled back?

- Does every token PR run visual regression across a defined set of stories × active tenant themes × light/dark × LTR/RTL, and who approves the diffs?
- What is the semver rule for tokens (rename, removal, value change, new mode), and how are consuming apps in the monorepo upgraded?
- Can a token release be rolled back without redeploying every app, and can tenant themes be pinned to a known-good base version?
- How is a change that affects a tenant's contractual branding (for example a client's approved colours on an award cover page) communicated to that tenant before release?
- How are deprecated tokens flagged to developers (lint warning, then error) and how long is the deprecation window?
- Is there a changelog that a tenant admin or auditor can read, listing what visually changed and when?

**Good answer:** A written semver policy for tokens, automated visual regression over a fixed matrix including every active tenant theme, Changesets-driven releases with a human-readable changelog, and a rollback path (pin or revert the token package) tested at least once. Branding-affecting changes have a tenant notice period.

**Red flags:**

- Token changes merged without visual diff against tenant themes.
- Renaming tokens in a minor release.
- No way to roll back a token release short of a full redeploy.

### `i18n` Scripts, languages and direction

**Question:** Do the typography, spacing and layout tokens work for every script and direction our tenants need (Latin, Devanagari and other Indic scripts, Traditional and Simplified Chinese, Arabic or Hebrew if offered) without per-tenant fixes?

- Which font family and fallback stack applies per script, and are line-height tokens tall enough for Indic scripts with stacked marks?
- Are spacing, borders and radius expressed as logical (inline-start / inline-end) so layouts mirror correctly in right-to-left languages? Which icons must mirror (arrows) and which must not (play, check)?
- How do fixed-width tokens behave with 30–40% text expansion (German, Tamil) or with CJK where words do not break on spaces?
- Are tabular figures and locale-specific numerals (for example Devanagari digits) supported by the data typography tokens?
- Do fonts for each script load only when needed, from our regional origin, without layout shift?
- Is the legal typography (awards, orders) tested for each language a tenant issues documents in?

**Good answer:** A per-script font and line-height table, a rule that layout tokens are logical and lint-enforced, a list of mirrored and non-mirrored icons, and Storybook stories that render core components in each supported script and in RTL as part of visual regression.

**Red flags:**

- One Latin font with system fallback for everything else.
- Physical left/right spacing tokens used throughout.
- No RTL or non-Latin stories in visual tests.

### `performance` Runtime cost and first paint

**Question:** What does the design system cost the user in bytes, render time and layout shift, and does the right tenant theme and colour mode appear on first paint with no flash?

- What is the size budget for the base token CSS plus one compiled tenant theme (compressed), and how is it measured in CI?
- Is the theme and mode resolved on the server so the first HTML response carries the correct `data-theme`, avoiding a flash of the default theme or wrong mode?
- How many font files and weights load on a typical party page, and what is their combined size? Are fallbacks metric-matched to prevent layout shift (CLS ≤ 0.1)?
- Do theme assets get long-lived immutable caching via content hashes, and how are they invalidated when a tenant updates its theme?
- Does using tokens through CSS custom properties force any components to be client components in the App Router, or can server components render themed UI?
- What is the impact on Core Web Vitals on a low-end Android phone on 4G, the realistic device for many parties?

**Good answer:** Numeric budgets (for example base CSS ≤ 15 KB compressed, tenant theme ≤ 3 KB, ≤ 3 font files on first load) enforced in CI, server-rendered theme and mode, immutable hashed theme files, and field Core Web Vitals tracked per tenant to confirm no regression.

**Red flags:**

- Theme applied by client-side JavaScript after hydration.
- Every weight of every font loaded on every page.
- No measurement of layout shift caused by font or theme loading.

### `surfaces` Coverage across surfaces and formal outputs

**Question:** Does the system define how tokens apply to every surface the platform produces, including emails, generated PDFs (awards, orders, eBundles), print, embedded hearing rooms and data visualisations?

- Which surfaces have their own token output, and which tokens are not supported there (for example custom properties in email clients)?
- Do formal legal outputs use a fixed, sober print theme regardless of tenant marketing colours, and who approves that template per institution?
- Is there a categorical and sequential palette for charts in reporting dashboards that passes 3:1 between adjacent series and works for colour-blind users?
- How do embedded third-party surfaces (video hearing room, e-signature) receive branding, and what is the fallback when they cannot be themed?
- Are print styles defined (page size A4 and US Letter, margins, no dark backgrounds)?

**Good answer:** A surface-by-surface table stating which token outputs apply, known gaps and the fallback for each, a print theme for formal documents, and an accessible data-visualisation palette defined as tokens.

**Red flags:**

- Awards or bundles styled ad hoc inside the PDF generator.
- Chart colours picked per dashboard.
- Dark-mode colours leaking into generated documents.

### `adoption` Adoption, contribution and ownership

**Question:** How do teams adopt and contribute to the system, how do we measure how much of the product actually uses it, and who decides when a request is a new token versus a one-off?

- What share of styling in each app uses tokens today (measured by a script, not estimated), and what is the target by date?
- What is the contribution path for a new token or mode, and what is the response time for a request from a product team?
- Who are the named owners in design and engineering, and is there a regular review of usage and requests?
- How are exceptions recorded when a team must ship before a token exists, and when do they expire?
- Is the Storybook token reference published to all engineers and tenant implementation staff, and kept current automatically?

**Good answer:** Named owners, a documented contribution process with a target turnaround, a usage metric produced automatically from the codebase and reviewed monthly, and an exceptions register with expiry dates.

**Red flags:**

- No owner, or ownership split with no tie-break.
- Adoption reported as a guess.
- Teams forking token files into their app.

