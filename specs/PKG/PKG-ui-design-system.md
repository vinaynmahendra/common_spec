---
id: "PKG-ui-design-system"
title: "UI / design system"
parent: "PKG"
order: 14
type: "capability"
template: "package"
childTemplate: "component"
status: "draft"
owner: null
indicative: false
summary: "Shared design-system packages: DTCG tokens, tenant theme compiler and validator, accessible React component library and Storybook with build-blocking accessibility and visual tests"
links: []
rev: 3
syncHash: "242141d6e36f9c8c"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.14 UI / design system

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Shared design-system packages: DTCG tokens, tenant theme compiler and validator, accessible React component library and Storybook with build-blocking accessibility and visual tests

<!-- section:purpose -->
## Purpose and scope

The UI / design system is the set of shared packages that every persona app in `apps/web` (and the email and PDF renderers) uses to look and behave the same way for every tenant. It exists so that accessibility (WCAG 2.2 AA, see [[APP-accessibility-wcag-2-1-aa]]), tenant branding and dense legal workflows are solved once, in components, rather than rebuilt per screen.

It is made of four workspace packages (Turborepo, pnpm workspaces, see [[FND-monorepo]]):

| Package | Contents | Imported by |
|---|---|---|
| `@nomology/tokens` (`packages/tokens`) | DTCG JSON token source and the Style Dictionary build that emits CSS, TypeScript, email, PDF and Figma outputs. Specified in [[PKG-design-tokens-and-foundations]] | `@nomology/ui`, `apps/web`, email renderer, PDF renderer |
| `@nomology/theme` (`packages/theme`) | Tenant theme schema (Zod), contrast and focus validation, theme compiler and the server helper that resolves `data-theme` / `data-mode` for a request. Specified in [[PKG-tenant-theme-schema-and]] and [[PKG-tenant-theme-accessibility]] | `apps/web` (server only), tenant admin API, BullMQ theme-compile job |
| `@nomology/ui` (`packages/ui`) | React components (5.14.2 to 5.14.14), hooks (`useToast`, `useAnnouncer`), layout primitives and icons | All route groups in `apps/web` |
| `@nomology/ui-storybook` (`apps/storybook`) | Storybook with every story, the token reference, accessibility and visual regression tests | CI only; published internally |

It deliberately does **not** contain: screens or journeys (owned by the route-group frontend nodes such as [[APP-party-and-counsel-portal]] and [[APP-secretariat-console]]), data fetching or tRPC calls (components receive data and callbacks from the caller, see [[APP-client-state-and-data-fetching]]), document rendering and the sandbox origin ([[APP-document-viewer-and-sandbox]]), the form builder ([[PKG-forms-and-form-builder]]) or translation storage ([[I18N-i18n]]).

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Uses | Example |
|---|---|---|
| Party and counsel portal `(counsel)` | Filing wizard, file upload, status and deadline badges, consequential confirmation | Counsel files a Statement of Claim with [[PKG-stepper-and-multi-step-form]], uploads exhibits with [[PKG-file-upload-dropzone]] and confirms with [[PKG-modal-dialog-and-consequential]] |
| Secretariat console `(secretariat)` | Data table with bulk actions, people picker, date-time picker | Tribunal secretary filters 400 open matters in [[PKG-data-table]], assigns a neutral with [[PKG-combobox-and-people-picker]], schedules a hearing across Singapore and New York time zones with [[PKG-date-and-time-picker-with]] |
| Neutral workspace `(neutral)` | Case timeline, document viewer controls, consequential confirmation | Arbitrator reviews the [[PKG-case-timeline]] and issues an award behind a typed confirmation |
| Transcriber workspace `(transcriber)` | Data table queue, alerts, toasts | Transcriber claims jobs from the turnaround queue |
| Tenant admin `(tenant-admin)` | Branding editor preview, form fields, alerts | SEBI ODR institution admin uploads a logo and sees contrast failures inline (see [[PKG-branding-and-theming]]) |
| Email and PDF renderers (`packages/notifications`, `packages/documents`) | Resolved token values (no CSS variables) and the print theme | Award PDF uses [[PKG-print-and-formal-document-theme]]; notification emails use `@nomology/tokens/email` |

<!-- section:api -->
## Public API

The public API is the set of entry points listed in each package's `package.json` `exports`. Anything not exported is internal and blocked by Turborepo boundaries [R1].

```ts
// @nomology/ui  (client and server-safe entry points)
export { Button, IconButton } from './button';             // 5.14.2
export { TextField, Textarea, Select, Checkbox, RadioGroup, Field } from './form'; // 5.14.3
export { Combobox, PeoplePicker } from './combobox';        // 5.14.4
export { DatePicker, DateTimePicker, TimeZoneSelect } from './datetime'; // 5.14.5
export { FileDropzone } from './file-upload';               // 5.14.6
export { DataTable } from './data-table';                   // 5.14.7
export { Dialog, ConsequentialConfirmDialog } from './dialog'; // 5.14.8
export { Alert, ToastRegion, useToast, Announcer, useAnnouncer } from './feedback'; // 5.14.9
export { Stepper, MultiStepForm } from './stepper';         // 5.14.10
export { CaseTimeline } from './case-timeline';             // 5.14.11
export { StatusBadge, DeadlineBadge } from './badges';      // 5.14.12
export { TenantSwitcher, ActiveTenantIndicator } from './tenant-switcher'; // 5.14.13
export { DocumentViewerToolbar } from './document-viewer';  // 5.14.14
export { Icon, type IconName } from './icons';
export { VisuallyHidden, SkipLink, Stack, Inline, Grid } from './layout';
export type { UiMessages } from './i18n';                   // built-in strings, supplied by the app
export { UiProvider } from './provider';                    // locale, messages, time zone, announcer

// @nomology/tokens
export const tokens: ResolvedTokens;                        // TS object, semantic tier only
export type SemanticTokenName = /* union of all semantic token paths */;
// CSS: '@nomology/tokens/css/base.css', '@nomology/tokens/css/modes.css'
// '@nomology/tokens/email' (resolved hex JSON), '@nomology/tokens/pdf' (print theme JSON)

// @nomology/theme  (server-only; imports 'server-only')
export const TenantThemeInput: z.ZodType<TenantThemeInput>;
export function validateTheme(input: TenantThemeInput): ThemeValidationReport;
export function compileTheme(input: TenantThemeInput, base: TokenVersion): CompiledTheme;
export function resolveAppearance(req: { tenant: TenantContext; cookies: RequestCookies }): Appearance; // { themeHref, dataTheme, dataMode, dataDensity, reducedMotion }
```

Component props contracts live in each component node's `api` section; the shared conventions are: `size?: 'sm' | 'md' | 'lg'`, `variant`, `disabled`, `onXChange(value)`, `value` / `defaultValue` for controlled and uncontrolled use, `ref` forwarding to the main interactive element, and passthrough of `data-*`, `aria-*` and `id`. `className` and `style` are **not** accepted on components (only on layout primitives) to prevent visual drift.

<!-- section:usage -->
## Usage examples

```tsx
// app/(counsel)/layout.tsx  (server component)
import { resolveAppearance } from '@nomology/theme';
import { UiProvider } from '@nomology/ui';
import { getTenantContext } from '@nomology/tenancy';

export default async function Layout({ children }) {
  const tenant = await getTenantContext();            // from middleware, see MT-tenant-resolution
  const a = resolveAppearance({ tenant, cookies: await cookies() });
  return (
    <html lang={tenant.locale} dir={tenant.dir} data-theme={a.dataTheme} data-mode={a.dataMode} data-density={a.dataDensity}>
      <head><link rel="stylesheet" href={a.themeHref} /></head>
      <body>
        <UiProvider locale={tenant.locale} timeZone={a.timeZone} messages={await getUiMessages(tenant)}>
          {children}
        </UiProvider>
      </body>
    </html>
  );
}
```

```tsx
// a client component using the library
'use client';
const { show } = useToast();
<Button variant="primary" loading={isPending} onPress={() => save().then(
  () => show({ tone: 'success', message: t('draft.saved') }),
  (e) => show({ tone: 'critical', message: t('draft.saveFailed'), action: { label: t('retry'), onPress: save } })
)}>{t('draft.save')}</Button>
```

<!-- section:tenant -->
## Tenant context

Components never read tenant context themselves and never fetch data. Tenant context enters the design system in three places only:

1. **Theme and mode**: `resolveAppearance()` in `@nomology/theme` reads the tenant from the request context established by [[MT-tenant-resolution]] and returns the tenant's compiled, content-hashed theme stylesheet URL and `data-*` attributes for `<html>`. If there is no tenant (platform-admin or the public marketing shell), the neutral base theme is used. If the tenant's active theme cannot be loaded, the base theme is used and `ui.theme.fallback_used` is logged with tenant ID (see [[PKG-tenant-theme-schema-and#theming]]).
2. **Terminology and messages**: the app passes `messages` to `UiProvider`; tenant overrides are resolved upstream by [[PKG-tenant-terminology-and-copy]]. Components only render what they receive.
3. **Data-fetching components** (`PeoplePicker`, `Combobox` async mode, `DataTable` server mode) accept a caller-supplied loader (for example a tRPC query from [[APP-internal-api-trpc-routers-per]]). Tenant and permission scoping happens on the server inside the RLS transaction ([[MT-isolation-strategy]], [[MT-prisma-client-extension-wraps]]); any client cache key is built by the caller with `tenantId` and `userId` as required by [[APP-client-state-and-data-fetching]].

On tenant switch ([[PKG-tenant-and-role-switcher]]) the app performs a full navigation to the new tenant's host, so theme, messages and caches are rebuilt rather than mutated in place.

<!-- section:config -->
## Configuration

| Setting | Default | Where it lives | Who changes it |
|---|---|---|---|
| Base token version | Pinned in `apps/web/package.json` | Repo | Design system team via Changesets |
| Tenant brand slots (colour, logos, radius) | Base theme | `tenant_theme_version` table via Settings ([[PKG-settings]]) | Tenant admin, validated |
| Tenant default mode (`system`, `light`, `dark`) | `system` | Tenant settings | Tenant admin |
| User mode, density, reduced motion override | Follow system | `user_preferences` (Settings) mirrored in `nm_appearance` cookie | User |
| Visual regression theme matrix | 5 fixture themes | `apps/storybook/.matrix.json` | Design system team |
| Feature flag for new component versions | Off | [[PKG-feature-flags]] | Release owner, per tenant |

<!-- section:adapters -->
## Providers and extension points

- **Behaviour layer**: complex widgets (combobox, date picker, dialog, table, tabs) are built on a headless accessibility library so keyboard and ARIA behaviour follow the APG patterns [R2]. Proposed: React Aria Components, including `@internationalized/date` for calendar and time-zone arithmetic. This needs an ADR before Phase 2 of [[PLAN]].
- **Icon set**: one open-licence outline icon set wrapped by `Icon`; domain icons (award, procedural order, hearing, bundle, deadline) are drawn in-house on the same grid. Adding an icon is a PR to `packages/ui/icons` with a name in the `IconName` union.
- **Output platforms for tokens**: new Style Dictionary platforms (for example a native mobile target) are added in `packages/tokens/build.ts`; see [[PKG-design-tokens-and-foundations#distribution]].

<!-- section:errors -->
## Error model

UI components do not throw for user errors; they render error states from props (`error`, `status`). Developer errors are surfaced as:

| Error | When | Behaviour |
|---|---|---|
| Missing accessible name | `IconButton` without `label`, `TextField` without `label` | TypeScript compile error (required prop); dev-only console error if bypassed |
| Controlled / uncontrolled switch | `value` changes from `undefined` to defined | Dev-only warning, same rule as React inputs |
| `UiProvider` missing | Component rendered outside provider | Throws `UiProviderMissingError` in dev and test; in production falls back to `en` strings and logs once |
| Theme compile failure | `compileTheme` rejects | Returns `ThemeValidationReport` with error codes (`THEME_CONTRAST_TEXT_ON_PRIMARY`, `THEME_LOGO_SVG_UNSAFE`, ...); activation is blocked, never partially applied |

<!-- section:nfr -->
## Performance and limits

Proposed budgets, enforced in CI by `size-limit` and Lighthouse CI per [[APP-frontend-performance-budgets]]:

| Item | Budget (compressed) |
|---|---|
| Base token CSS (`base.css` + `modes.css`) | 12 KB |
| One compiled tenant theme stylesheet | 3 KB |
| `Button`, `TextField`, `Alert` client JS each | 3 KB |
| `DataTable` with virtualisation | 25 KB |
| `DateTimePicker` including date library | 30 KB |
| Fonts on a typical party page (Latin, 2 weights) | 70 KB |
| Interaction to Next Paint on mid-range Android for typing in `PeoplePicker` | 200 ms p75 |
| Cumulative Layout Shift from theme or font load | 0.0 target, 0.1 maximum |

<!-- section:versioning -->
## Versioning and compatibility

- All four packages are versioned together with Changesets [R3] and follow semver [R4]. Inside the monorepo apps consume `workspace:*`, so "release" means a tagged version that the visual baseline and the ACR ([[APP-accessibility-conformance]]) refer to.
- **Breaking** (major): removing or renaming a component, prop, token or `IconName`; changing a default; changing DOM structure that tests or ARIA depend on; changing a semantic token value so that a manifest contrast pair moves by more than 0.5 ratio.
- **Deprecation window**: one minor release with a lint warning (`@nomology/eslint-plugin/no-deprecated-ui`), then removal no sooner than 8 weeks later.
- Tenant themes store the base token version they were validated against; a major token release re-validates every active tenant theme before rollout (see [[PKG-tenant-theme-accessibility]]).

<!-- section:testing -->
## Test contract

The package guarantees, by tests run in CI on every PR that touches `packages/tokens`, `packages/theme` or `packages/ui` (Turborepo affected graph):

1. Every component has stories for each variant × state listed in its node ([[PKG-design-system-component]] defines the build-blocking checks).
2. Interaction tests (Storybook play functions) cover the keyboard-only path for every interactive component [R5].
3. axe-core runs on every story; serious and critical violations fail the build [R6].
4. Visual regression on Playwright screenshots of stories in a pinned Docker image (fonts and browser fixed) across the matrix: 5 fixture themes (base, synthetic arbitral institution, synthetic SEBI ODR institution, CORD, worst-case passing theme) × light / dark / high contrast × LTR / RTL for components that have direction-dependent layout [R7].
5. The contrast manifest check in [[PKG-colour-and-contrast]] passes for base and all fixture themes.
6. `@nomology/theme` has unit tests for every validation rule with known passing and failing inputs, including malicious SVG samples.

Fixture themes are synthetic. We never use a real client's logo or colours in public stories.

<!-- section:questions -->
## Open questions

- [ ] Confirm React Aria Components as the headless behaviour layer and record it as an ADR (owner: frontend lead).
- [ ] Visual regression: self-hosted Playwright snapshots (proposed) or a hosted service such as Chromatic; decide on cost and whether story data may leave our CI (owner: design system lead).
- [ ] Who is the named design owner for the system, and is there a budget for a part-time accessibility specialist reviewing component changes? (owner: CTO)
- [ ] Do we publish Storybook to tenant implementation staff (read-only, behind SSO) or keep it internal only? (owner: product)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

No component reads or caches tenant data. The only tenant-dependent inputs are: the compiled theme stylesheet (content-hashed URL under the tenant's own host, resolved server-side by `resolveAppearance`), the message bundle passed to `UiProvider`, and caller-supplied loaders for data-fetching components. Loaders run tRPC procedures inside the RLS transaction ([[MT-prisma-client-extension-wraps]]), and client cache keys are built by the caller including `tenantId` per [[APP-client-state-and-data-fetching]]. `@nomology/theme` reads and writes `tenant_theme_version`, a tenant-owned table with forced RLS ([[MT-rls-enabled-and-forced-on]]); its compile job runs in BullMQ with the tenant ID in the job payload and sets tenant context before any query. Tenant switching is a full navigation to another host, so nothing in memory survives a switch.

<!-- check:security -->
### Security of the API surface

- `@nomology/theme` is server-only (`import 'server-only'`) and blocked from client bundles by Turborepo boundaries [R1].
- Tenant theme input is a typed schema (hex colours, enums, asset IDs), never free CSS; compiled output is generated from a template, so no tenant string reaches a CSS context unescaped.
- SVG logos are sanitised (no scripts, event handlers, `foreignObject`, external `href`) and re-serialised; see [[PKG-tenant-theme-schema-and]].
- `dangerouslySetInnerHTML` is banned in `packages/ui` by lint; the only rich-text renderer accepts a sanitised AST.
- Dependencies are pinned through the pnpm lockfile and scanned per [[SEC-vulnerability-management]].

<!-- check:data-protection -->
### Personal data handling

Components hold personal data only in React state while rendered. Rules: no personal or case data in `data-*` attributes, URLs built by components, analytics events or `console` output; Storybook stories and visual baselines use synthetic data only; masked values (KYC numbers, bank account numbers) stay masked in the accessible name. The theme package stores tenant logos (not personal data) in the tenant's regional bucket.

<!-- check:residency -->
### Region awareness

Compiled theme stylesheets and logos are stored in the tenant's home-region bucket ([[PKG-object-storage-abstraction-s3]]) and served from the regional app origin, so a CDN edge only caches public, non-personal brand assets. Fonts are self-hosted per region ([[PKG-typography-and-multi-script]]). No design-system runtime call goes to a third-party origin.

<!-- check:audit -->
### Audit events

Design-system components emit no audit events themselves; consequential actions are audited by the caller's server mutation ([[PKG-audit-trail]]). `@nomology/theme` emits `branding.theme.submitted`, `branding.theme.validation_failed`, `branding.theme.activated` and `branding.theme.rolled_back` with actor, tenant, version ID and validation report hash.

<!-- check:change-safety -->
### Change and release safety

Every token or component change runs the affected-graph build, interaction, axe and visual regression tests across the fixture theme matrix. Changesets enforce a version bump type; major bumps need two CODEOWNERS approvals (design and engineering). Risky component rewrites ship behind a per-tenant flag ([[PKG-feature-flags]]) as `ComponentV2` until the old one is removed. Deprecated exports raise a lint warning for one minor release before removal.

<!-- check:testing -->
### Testing

See the Test contract section: stories per variant × state, keyboard interaction tests, axe-core on all stories with serious or critical violations failing the build, Playwright visual snapshots in a pinned image across 5 fixture themes × 3 modes × 2 directions, contrast-manifest check, and unit tests for every theme validation rule. Coverage threshold proposed at 85 percent lines for `packages/theme` and 70 percent for `packages/ui`.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "kind": "vendor",
    "retrieved": "2026-10-28",
    "title": "Turborepo reference: boundaries",
    "url": "https://turbo.build/repo/docs/reference/boundaries",
    "vendor": "Vercel"
  },
  {
    "body": "W3C",
    "id": "R2",
    "ident": "WAI-ARIA APG",
    "kind": "standard",
    "title": "ARIA Authoring Practices Guide: Patterns",
    "url": "https://www.w3.org/WAI/ARIA/apg/patterns/"
  },
  {
    "id": "R3",
    "kind": "vendor",
    "retrieved": "2026-10-28",
    "title": "Changesets: versioning and changelogs for monorepos",
    "url": "https://github.com/changesets/changesets",
    "vendor": "Changesets"
  },
  {
    "body": "semver.org",
    "id": "R4",
    "ident": "SemVer 2.0.0",
    "kind": "standard",
    "title": "Semantic Versioning 2.0.0",
    "url": "https://semver.org/",
    "version": "2.0.0"
  },
  {
    "id": "R5",
    "kind": "vendor",
    "retrieved": "2026-10-28",
    "title": "Interaction tests",
    "url": "https://storybook.js.org/docs/writing-tests/interaction-testing",
    "vendor": "Storybook"
  },
  {
    "id": "R6",
    "kind": "vendor",
    "retrieved": "2026-10-28",
    "title": "axe-core accessibility engine",
    "url": "https://github.com/dequelabs/axe-core",
    "vendor": "Deque"
  },
  {
    "id": "R7",
    "kind": "vendor",
    "retrieved": "2026-10-28",
    "title": "Visual comparisons",
    "url": "https://playwright.dev/docs/test-snapshots",
    "vendor": "Playwright"
  }
]
```

<!-- end -->
