---
id: "PKG-branding-and-theming"
title: "Branding and theming"
parent: "PKG-configuration-and-customisation"
order: 5
type: "feature"
template: "designsys"
status: "draft"
owner: null
indicative: false
summary: "Tenant branding model: limited brand slots, preview, validation and activation of themes across web, email, PDF cover and embedded vendors, with locked platform trust cues"
links: []
rev: 4
syncHash: "96817551bbd1aa79"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.8.5 Branding and theming

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Tenant branding model: limited brand slots, preview, validation and activation of themes across web, email, PDF cover and embedded vendors, with locked platform trust cues

<!-- section:purpose -->
## Purpose and scope

Branding and theming lets each tenant (an arbitral institution, a SEBI-recognised ODR institution, the CORD tenant, a court or government programme) present the platform with its own identity while the platform keeps its accessibility, security cues and legal neutrality. This node is the parent for tenant branding; it summarises the model and points to:

- [[PKG-tenant-theme-schema-and]]: the exact brand slots, schema, compile-on-activation and fallback.
- [[PKG-tenant-theme-accessibility]]: the save-time contrast and focus checks that block activation.
- [[PKG-settings-branding-content]]: every branding setting (active theme, unit themes, display names, footer, sign-in content, email and document branding) with scopes, permissions and blueprint defaults.

Branding covers the web app, notification emails, generated PDFs (cover and letterhead only, see [[PKG-print-and-formal-document-theme]]) and, where possible, embedded third-party surfaces. Tenant terminology (renaming "case" to "matter") is separate: [[PKG-tenant-terminology-and-copy]]. A person's own colour mode, contrast and density are personal preferences ([[PKG-colour-modes-and-user]], [[PKG-settings-personal]]).

Who does what: `content_admin` (and `tenant_admin`) edit and activate themes with permission `settings.branding:write`; `unit_admin` can choose one of the tenant's published theme versions for their unit when the tenant allows it; changing the primary host (custom domain) needs `settings.branding:write` and a second approver. Nomology sets the neutral base theme per offering and the locked trust cues.

<!-- section:architecture -->
## Token architecture and naming

A tenant theme is one context of the DTCG resolver modifier `brand` [R1]. It can only set brand slot tokens (`brand.*`); semantic tokens that depend on brand (`color.action.primary.*`, `color.text.link`, `color.border.selected`, `color.focus.ring`) are derived by the compiler. Tenants cannot reference primitives, add tokens or write CSS.

<!-- section:colour -->
## Colour

Tenant colours: `brand.primary` (required) and `brand.accent` (optional, used only for decorative header accents and never for text). Dark-mode variants are derived and approved during validation. See [[PKG-colour-and-contrast#theming]].

<!-- section:typography -->
## Typography

Tenants may pick a heading family from an allow-list of self-hosted fonts. Body, legal and data typography are fixed ([[PKG-typography-and-multi-script#theming]]).

<!-- section:theming -->
## Theming and tenant branding

| Slot | Type | Notes |
|---|---|---|
| `brand.primary` | Hex colour | Validated in light and dark |
| `brand.accent` | Hex colour, optional | Decorative only |
| `brand.logo.light`, `brand.logo.dark` | SVG or PNG asset | Header logo for each mode |
| `brand.logo.mark` | Square SVG or PNG | Tenant switcher, favicon fallback, small screens |
| `brand.favicon` | PNG / ICO | |
| `brand.radius` | `none`, `sm`, `md` | |
| `brand.heading-family` | Allow-list enum | |
| `brand.display-name` | String, max 60 characters | Shown next to the logo and in the tenant switcher; also the logo's accessible name. Sourced from the setting `brand.identity.display_name` |
| `email.header` | Derived from `brand.primary` and logo | No free HTML |

These are design-token slots inside a theme version (an artefact of kind `theme`); they are not settings. Which theme version is active is the setting `brand.theme.active_version` ([[PKG-settings-branding-content]]).

**Scopes.** A theme version belongs to the tenant. `brand.theme.active_version` resolves `offering` (neutral CORD or TERES base) → `tenant` → `unit` ([[PKG-configuration-scope-hierarchy]]). Unit values are allowed only when `brand.theme.allow_unit_themes = true` and the tenant holds `feature.branding.unit_themes`, and a unit may only select a validated version owned by the tenant. A case shows the theme of its owning unit. There is no case-type, case or user theme.

**Lifecycle** (the shared configuration lifecycle, [[PKG-configuration-lifecycle]]). The admin edits a draft theme version at `/admin/content/branding` → live preview (sample case list, filing step, dialog, email and PDF cover, in light and dark; served same-origin as `/admin/content/branding/preview`) → **Validate** runs schema and accessibility checks → the draft is added to a change set together with the `brand.theme.active_version` item (and any related settings such as footer text) → on publish, the BullMQ job `theme.compile` compiles the content-hashed stylesheet into the tenant's regional bucket, then the active version switches and the tenant configuration epoch is bumped. Theme changes are `standard` by default, so a `content_admin` can publish in one step; tenants that set `access.change_control.review_all_changes` get maker-checker. The previous version stays compiled for one-click revert. All steps are audited (`admin.config.published`, `branding.theme.activated`).

**Locked elements** (never tenant-controlled): sign-in trust cues (platform name and "Secured by" line on the sign-in page, URL host), security and consent text, error, warning and success colours, status colours, focus indicator style, the AI-content label, and the platform footer with privacy and accessibility statement links (`brand.footer.platform_attribution` can be `compact` but never removed). This prevents a theme from imitating platform warnings or another institution; display names are also checked against a protected-name list ([[PKG-settings-branding-content#validation]]).

<!-- section:distribution -->
## Build, distribution and consumption

Web: `<link>` to `/_theme/{hash}.css` on the tenant host. Email: resolved brand colour and hosted logo URL (regional, public, hash-named) passed to the email renderer. PDF: print logo and name block. Third-party surfaces: logo and primary colour pushed to vendor branding APIs where the integration supports it ([[INT-common-integrations]]); otherwise the vendor's neutral styling is used.

<!-- section:governance -->
## Governance, versioning and deprecation

Brand slot list changes are owned by the design system team and product; adding a slot is a minor release of `@nomology/theme` and requires a validation rule and a visual regression fixture. Tenant theme publication is self-service for `content_admin` and `tenant_admin` through change sets; platform support can revert a tenant's theme only under [[PKG-support-access-and-impersonation]] rules, and the revert appears in the tenant's change history. Blueprints ship a neutral starting theme per tenant type ([[PKG-configuration-packages]]); themes travel in packages with their assets referenced by hash, and are re-validated on import.

<!-- section:questions -->
## Open questions

- [ ] May a tenant use a custom domain for sign-in, and if so which trust cues show the platform behind it (owner: security lead, with [[MT-tenant-resolution]] and [[PKG-domain-verification]]).
- [ ] Do white-label tenants want the platform name hidden entirely from the footer? Decided for now: no; `compact` attribution is the most a plan can offer (owner: CEO / CCO to confirm).
- [ ] Should platform support be able to edit a tenant's theme on request, or only revert (owner: product).
- [ ] Unit themes: are different logos per unit needed (court programmes inside a larger tenant), or only different display labels? (owner: product)

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Accessibility by construction

Activation is blocked unless every derived pair passes in light and dark ([[PKG-tenant-theme-accessibility]]). High contrast and forced colours ignore tenant colours.

<!-- check:tenancy -->
### Tenant theme isolation and safety

Theme values are typed (colour, enum, asset ID), compiled at publish, stored per tenant in the tenant's region and served under the tenant host with a content-hashed URL, so another tenant's theme cannot be served by a cache. Units can only select their own tenant's validated versions. Locked elements and protected display names stop a theme from imitating platform warnings or another institution. Failure to load falls back to the neutral base theme.

<!-- check:change-safety -->
### Change safety and blast radius

Each activation is a new immutable theme version published through a change set, with one-click revert of the change set; base token majors re-validate every active tenant theme (including unit-selected versions) before deploy.

<!-- check:surfaces -->
### Coverage across surfaces and formal outputs

Web, email, PDF cover and third-party vendor branding all draw from the same compiled theme record; the formal document body never uses tenant colours.

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
  }
]
```

<!-- end -->
