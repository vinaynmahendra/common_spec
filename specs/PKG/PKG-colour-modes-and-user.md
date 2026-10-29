---
id: "PKG-colour-modes-and-user"
title: "Colour modes and user preferences"
parent: "PKG-design-tokens-and-foundations"
order: 3
type: "requirement"
template: "designsys"
status: "draft"
owner: null
indicative: false
summary: "Light, dark, high-contrast and forced-colours support; reduced motion; density; server-rendered with no theme flash"
links: []
rev: 3
syncHash: "cc9f0597fea9e28b"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.14.1.3 Colour modes and user preferences

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Light, dark, high-contrast and forced-colours support; reduced motion; density; server-rendered with no theme flash

<!-- section:purpose -->
## Purpose and scope

Specifies the appearance modes (light, dark, high contrast), Windows forced-colours support, reduced motion and density, how each is chosen and stored, and how the server renders the right mode in the first HTML response. Applies to every route group in `apps/web`. The preference keys are defined in [[PKG-settings-personal]] (groups B and C) and edited on `/me/settings/appearance` and `/me/settings/accessibility` ([[PKG-personalisation]]); this node owns the visual and rendering behaviour. Email and PDF are out of scope: email ships light values only and PDFs use the fixed print theme ([[PKG-print-and-formal-document-theme]]).

<!-- section:architecture -->
## Token architecture and naming

Modes are DTCG resolver modifiers [R1]: `mode` (`light`, `dark`, `high-contrast`) and `density` (`comfortable`, `compact`). Mode files override semantic colour tokens only; density files override `size.control.*` and `space.inset.*` only. Output CSS:

```css
@layer nm.tokens {
  :root, [data-mode="light"] { /* light semantic values */ }
  [data-mode="dark"] { /* dark overrides */ }
  [data-mode="high-contrast"] { /* high contrast overrides */ }
  @media (prefers-color-scheme: dark) { [data-mode="system"] { /* dark overrides */ } }
  @media (prefers-contrast: more) { [data-mode="system"] { /* high contrast overrides */ } }
  [data-density="compact"] { /* compact sizing */ }
}
```

`data-mode="system"` lets the browser decide through media queries [R2], which needs no JavaScript and no cookie.

<!-- section:colour -->
## Colour

Mode colour values are in [[PKG-colour-and-contrast#colour]]. High contrast: text neutral.950 on neutral.0 (light) or neutral.0 on neutral.950 (dark base), every border `border.control`, status badges become outlined with a 2 px tone border and text, target 7:1 for text.

**Forced colours** (`@media (forced-colors: active)`) [R3]: we do not fight the user's palette. Rules:

| Element | System colour |
|---|---|
| Surfaces | `Canvas` |
| Text | `CanvasText` |
| Links | `LinkText` |
| Buttons | `ButtonFace` / `ButtonText` with 1 px `ButtonText` border |
| Focus ring | 2 px `Highlight` outline (outline survives forced colours; box-shadow rings do not) |
| Selected rows, checked states | `Highlight` / `HighlightText` |
| Disabled | `GrayText` |
| Status badges, deadline badges | Border in `CanvasText`; the icon and label carry meaning |
| Charts | `forced-color-adjust: none` only on the chart canvas, with patterns and direct labels so series stay distinguishable |

Focus rings are implemented with `outline` everywhere for this reason.

<!-- section:typography -->
## Typography

Not mode-dependent. Users who need larger text use browser zoom; layouts reflow to 400 percent (320 CSS px).

<!-- section:spacing -->
## Spacing, sizing and layout

Density modes:

| Token | Comfortable | Compact |
|---|---|---|
| `size.control.height` | 40 px | 32 px |
| `space.inset.md` | 12 px | 8 px |
| `datatable.row.height` | 48 px | 36 px |
| `size.target.min` | 24 px | 24 px (unchanged) |

Compact is offered only in `(secretariat)`, `(transcriber)` and `(platform-admin)`. Party, counsel and neutral pages are always comfortable; on coarse pointers party pages use 44 px targets.

<!-- section:motion -->
## Motion

Reduced motion is on when `prefers-reduced-motion: reduce` [R2] or the user's "Reduce motion" setting is on. Then durations become 0 ms except the indeterminate busy indicator (slowed to one pulse every 2 s) and determinate upload progress (no animation, the bar simply updates). Toasts appear without sliding. Smooth scrolling is disabled. Components read reduced motion through CSS only (`[data-motion="reduce"]` or the media query), so no client JavaScript is needed.

<!-- section:theming -->
## Theming and tenant branding

Tenant themes are compiled for light and dark (and validated in both, see [[PKG-tenant-theme-accessibility]]). High contrast and forced colours ignore tenant brand colours except the logo, so a tenant cannot reduce contrast in those modes. Tenants and units set a default mode (`system`, `light` or `dark`) through `personal.appearance.mode` at tenant or unit scope; users may always override it, and `high_contrast` is offered to every user as an explicit choice in addition to `prefers-contrast`. Density defaults can be restricted to `comfortable` per persona by the tenant.

<!-- section:modes -->
## Colour modes and user preferences

**Resolution order** (first match wins): user preference → unit default → tenant default → `system`, resolved by [[PKG-settings]] for the keys `personal.appearance.mode`, `personal.appearance.density` and `personal.a11y.reduce_motion` ([[PKG-settings-personal]]). A tenant or unit may set defaults but can never lock a user out of `high_contrast` or reduced motion.

| Source | Storage | Read by |
|---|---|---|
| User preference | `setting_value` rows at level `user` per tenant membership ([[PKG-settings-data-model]]), mirrored into an `nm_appearance` cookie (`Secure; SameSite=Lax; HttpOnly=false`, no personal data, values like `m=dark;d=compact;rm=1;hc=0`) | Server `resolveAppearance()` reads the cookie, so no database read is needed per request; the cookie is refreshed from settings at sign-in and tenant switch |
| Unit and tenant defaults | Settings rows at `unit` and `tenant` scope | `resolveAppearance()` from the cached tenant record |
| System | Browser media queries | CSS only |

**No flash of the wrong theme.** On dynamically rendered routes (most authenticated pages, which use nonce-based CSP per [[APP-rendering-and-caching-strategy]]) the server writes `data-mode`, `data-density` and `data-motion` on `<html>` in the first byte of HTML. On static shells in the `(public)` route group (hash-based CSP, no per-request rendering) the HTML always carries `data-mode="system"`; an explicit user override is applied after sign-in only. We do not use an inline script to read `localStorage`, because it would need a CSP exception.

Changing a preference updates the setting and the cookie through a Server Action, then sets the attribute on `<html>` client-side, with no reload. Preferences follow the user across devices because they are stored server-side (decided).

Setting `color-scheme: light dark` on `:root` (and `color-scheme: dark` under dark) makes native controls and scrollbars match.

<!-- section:distribution -->
## Build, distribution and consumption

`dist/css/modes.css` is part of the base stylesheet (one request). The compiled tenant theme includes both light and dark brand values. `resolveAppearance()` is exported from `@nomology/theme` and called in each route group's root layout.

<!-- section:governance -->
## Governance, versioning and deprecation

Adding a mode context is a minor release; it must ship with a full manifest pass for that mode and a visual regression baseline. Owners as in [[PKG-design-tokens-and-foundations#governance]].

<!-- section:questions -->
## Open questions

- [x] Sync the user's mode across devices or keep it per device? Decided: stored server-side and mirrored to the cookie on sign-in.
- [x] Per tenant membership or per identity across tenants? Decided: per membership, with an "apply in all my organisations in this region" option ([[PKG-personalisation#state]]).
- [x] Offer high contrast as an explicit user choice in addition to `prefers-contrast`? Decided: yes.
- [ ] Should forced-colours users get a hint about the platform's own high-contrast mode, or is that redundant? (Accessibility lead)

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Accessibility by construction

High contrast targets 7:1 for text; forced colours use system colours with `outline`-based focus rings that survive forced-colours mode; reduced motion removes all non-essential animation; compact density never drops targets below 24 px.

<!-- check:tenancy -->
### Tenant theme isolation and safety

Tenant brand colours do not apply in high contrast or forced colours. The appearance cookie stores only mode values, never tenant or user IDs, so it cannot leak tenant information between hosts (cookies are host-scoped to the tenant domain).

<!-- check:change-safety -->
### Change safety and blast radius

Each mode is a separate visual regression column; a token change that only affects dark mode still runs the full matrix.

<!-- check:i18n -->
### Scripts, languages and direction

Modes are independent of direction and script. RTL fixtures run in light and dark in visual regression.

<!-- check:performance -->
### Runtime cost and first paint

Mode and density are resolved server-side from a cookie, adding no database round-trip and no client script; static public shells use `system` via media queries. There is no theme flash on any route.

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C Design Tokens Community Group",
    "id": "R1",
    "ident": "DTCG Resolver",
    "kind": "standard",
    "title": "Design Tokens Resolver Module 2025.10",
    "url": "https://www.designtokens.org/tr/2025.10/resolver/",
    "version": "2025.10"
  },
  {
    "body": "W3C",
    "excerpt": "Defines prefers-color-scheme, prefers-reduced-motion, prefers-contrast and forced-colors.",
    "id": "R2",
    "ident": "Media Queries 5",
    "kind": "standard",
    "title": "Media Queries Level 5",
    "url": "https://www.w3.org/TR/mediaqueries-5/"
  },
  {
    "body": "W3C",
    "excerpt": "Defines forced colors mode and the forced-color-adjust property.",
    "id": "R3",
    "ident": "css-color-adjust-1",
    "kind": "standard",
    "title": "CSS Color Adjustment Module Level 1",
    "url": "https://www.w3.org/TR/css-color-adjust-1/"
  }
]
```

<!-- end -->
