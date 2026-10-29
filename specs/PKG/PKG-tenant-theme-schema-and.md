---
id: "PKG-tenant-theme-schema-and"
title: "Tenant theme schema and validation"
parent: "PKG-branding-and-theming"
order: 1
type: "requirement"
template: "designsys"
status: "draft"
owner: null
indicative: false
summary: "Allowed brand slots, limits, compile-on-activation, contrast validation and fallback for tenant themes"
links: []
rev: 2
syncHash: "fb58981ca77b3540"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.8.5.1 Tenant theme schema and validation

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Allowed brand slots, limits, compile-on-activation, contrast validation and fallback for tenant themes

<!-- section:purpose -->
## Purpose and scope

Exact schema, limits, storage, compile process and fallback for tenant themes. Implemented in `@nomology/theme` (server only) and used by the tenant admin UI, the tenant admin API ([[INT-tenant-admin-api]]) and the theme compile job. The accessibility rules applied during validation are specified as a requirement in [[PKG-tenant-theme-accessibility]].

<!-- section:architecture -->
## Token architecture and naming

A theme version is stored as validated input (JSON). The compiler turns it into a DTCG resolver `brand` context [R1], resolves it against the pinned base token version, and emits one CSS file that sets only `--nm-brand-*` and derived `--nm-color-action-primary-*`, `--nm-color-text-link`, `--nm-color-border-selected`, `--nm-color-focus-ring` custom properties inside `@layer nm.theme` for `[data-mode="light"]`, `[data-mode="dark"]` and `system` media queries.

<!-- section:colour -->
## Colour

`brand.primary` and `brand.accent` are hex strings `^#[0-9A-Fa-f]{6}$` (no alpha, no named colours, no `var()` or functions). Derived values: `action.primary.bg = brand.primary`; hover and pressed are the brand colour with OKLCH lightness reduced by 0.06 and 0.12 in light mode (raised in dark); `text.on-action` is white or neutral.950, whichever gives the higher ratio. Dark variant: computed as described in [[PKG-colour-and-contrast#theming]], or supplied explicitly as `brand.primaryDark`.

<!-- section:typography -->
## Typography

`brand.headingFamily` enum: `inter`, `source-serif-4`, `noto-sans`, `noto-serif`. Default `inter`.

<!-- section:theming -->
## Theming and tenant branding

**Schema (Zod, `packages/theme/src/schema.ts`).**

```ts
export const TenantThemeInput = z.object({
  schemaVersion: z.literal(1),
  primary: HexColour,                         // required
  primaryDark: HexColour.optional(),          // else derived
  accent: HexColour.optional(),
  radius: z.enum(['none', 'sm', 'md']).default('md'),
  headingFamily: z.enum(['inter', 'source-serif-4', 'noto-sans', 'noto-serif']).default('inter'),
  displayName: z.string().trim().min(2).max(60).regex(SAFE_TEXT),   // no control chars, no < >
  logos: z.object({
    light: AssetRef,                          // required
    dark: AssetRef.optional(),                // else light logo on a light plate
    mark: AssetRef,                           // square
    print: AssetRef.optional(),
  }),
  favicon: AssetRef.optional(),
  defaultMode: z.enum(['system', 'light', 'dark']).default('system'),
}).strict();                                  // unknown keys rejected
```

**Asset limits.**

| Asset | Formats | Max size | Dimensions |
|---|---|---|---|
| Logo light / dark | SVG, PNG | 200 KB | Rendered at 32 px height in header; source at least 64 px high (PNG); aspect ratio between 1:1 and 6:1 |
| Mark | SVG, PNG | 100 KB | Square, at least 128 × 128 (PNG) |
| Print logo | SVG, PNG (300 dpi) | 500 KB | Max 30 mm wide on cover |
| Favicon | PNG, ICO | 50 KB | 32 × 32 and 180 × 180 |

**SVG sanitisation.** Parse with a strict XML parser; allow-list elements (`svg`, `g`, `path`, `rect`, `circle`, `ellipse`, `line`, `polyline`, `polygon`, `defs`, `linearGradient`, `radialGradient`, `stop`, `clipPath`, `title`) and presentation attributes only; remove `script`, `style`, `foreignObject`, `image`, `use` with external `href`, event handler attributes, `javascript:` and external URLs; re-serialise; reject if anything was removed that changed rendering (compare a rasterised render before and after). PNGs are re-encoded to strip metadata. Assets are scanned by the malware pipeline ([[PKG-encryption-at-rest-signed-urls]]) before they can be used.

**Storage (tenant-owned, forced RLS, see [[MT-every-tenant-owned-table-carries]]).**

```prisma
model TenantTheme {
  tenantId        String   @id @db.Uuid
  activeVersionId String?  @db.Uuid
  updatedAt       DateTime @updatedAt
}
model TenantThemeVersion {
  id               String   @id @db.Uuid
  tenantId         String   @db.Uuid
  status           ThemeStatus  // draft | validated | active | retired | rejected
  input            Json         // TenantThemeInput
  baseTokenVersion String       // e.g. "3.4.0"
  report           Json?        // ThemeValidationReport
  cssObjectKey     String?      // themes/{tenantId}/{sha256}.css in the home-region bucket
  cssHash          String?
  createdBy        String   @db.Uuid
  activatedBy      String?  @db.Uuid
  createdAt        DateTime @default(now())
  activatedAt      DateTime?
  @@index([tenantId, status])
}
```

**Compile on activation.** `POST` via the tenant admin tRPC procedure `branding.activateTheme(versionId)` enqueues a BullMQ job `theme.compile` (tenant ID in payload; the worker sets tenant context before any query). The job: validates again against the current base token version → compiles CSS → writes to the regional bucket with `Content-Type: text/css` → sets `status = active`, retires the previous active version → invalidates the tenant record cache → emits `branding.theme.activated` audit event. Target: activation visible within 60 seconds.

**Serving.** `/_theme/{hash}.css` on the tenant's host, `Cache-Control: public, max-age=31536000, immutable`. The route checks that the hash belongs to the tenant resolved for that host; any other hash returns 404. Because the CSS is attached by `<link>` from our own origin, it fits `style-src 'self'` in our CSP [R2].

**Fallback.** If the active version's CSS cannot be fetched or the record is missing, `resolveAppearance()` returns the base theme (`data-theme="base"`) and logs `ui.theme.fallback_used` with tenant ID; an alert fires if more than 1 percent of a tenant's page views in 10 minutes use the fallback. Never another tenant's theme, never unstyled.

<!-- section:distribution -->
## Build, distribution and consumption

Emails read `primary` (light) and the hosted logo URL (`/_brand/{hash}.png` on the tenant host or a regional public asset host); PDFs read `logos.print` and `displayName`. Both read the active version at render time and record its ID.

<!-- section:governance -->
## Governance, versioning and deprecation

`schemaVersion` increases on any breaking schema change; the compiler supports the current and previous version and a migration script upgrades stored drafts. Validation rule changes that could reject currently active themes run a dry-run report across all tenants before release.

<!-- section:questions -->
## Open questions

- [ ] Is 60 seconds acceptable for activation to take effect, or do tenants expect instant preview-to-live (owner: product).
- [ ] Confirm the allowed logo aspect ratio range with real tenant logos from launch institutions (owner: design).
- [ ] Do we need a separate theme for the CORD consumer-facing public filing entry, or does the CORD tenant theme cover it (owner: CORD product lead).

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Accessibility by construction

Validation rules (contrast, focus ring, logo legibility) from [[PKG-tenant-theme-accessibility]] run before a version can become `validated`, and again at activation against the current base tokens.

<!-- check:tenancy -->
### Tenant theme isolation and safety

Input is a strict Zod schema with no free CSS; versions are stored in tenant-owned tables with forced RLS; the compile job sets tenant context from the job payload; CSS is stored under `themes/{tenantId}/` in the home-region bucket and served only on the tenant's own host after checking the hash belongs to that tenant. Fallback is always the base theme.

<!-- check:change-safety -->
### Change safety and blast radius

Each activation is a new immutable version with rollback to the previous one. Base token releases trigger a dry-run re-validation of all active themes.

<!-- check:performance -->
### Runtime cost and first paint

Compiled CSS per tenant is about 1 to 3 KB, immutable and long-cached; there is no per-request compilation.

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
    "id": "R2",
    "ident": "CSP3",
    "kind": "standard",
    "title": "Content Security Policy Level 3",
    "url": "https://www.w3.org/TR/CSP3/"
  }
]
```

<!-- end -->
