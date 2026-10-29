---
id: "PKG-tenant-and-role-switcher"
title: "Tenant and role switcher"
parent: "PKG-ui-design-system"
order: 13
type: "feature"
template: "component"
status: "draft"
owner: null
indicative: false
summary: "Switch active tenant, persona or admin scope (organisation or unit); active tenant, persona, elevation and support sessions always visible"
links: []
rev: 3
syncHash: "493cd4051452d2c2"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.14.13 Tenant and role switcher

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Switch active tenant, persona or admin scope (organisation or unit); active tenant, persona, elevation and support sessions always visible

<!-- section:purpose -->
## Purpose and when to use

Three related header controls that tell a user **where they are acting and with what authority**, and let them change it:

1. `TenantSwitcher` lets a user who belongs to more than one tenant (for example counsel appearing before an arbitral institution tenant and a SEBI ODR institution tenant, or a neutral on several panels) switch the active tenant and, within a tenant, the active persona (counsel, neutral, secretariat, transcriber, administration).
2. `ActiveTenantIndicator` always shows which tenant and persona are active, on every page, so a user never files in the wrong forum.
3. `AdminScopeSwitcher` (new) is shown only in the tenant admin console ([[APP-tenant-admin-console]]) to admins who hold roles at unit scope ([[APP-administration-model#design]] section 3). It shows and changes the active administrative scope: "Whole organisation" or one assigned unit subtree (for example "SEBI ODR desk").

A fourth, non-interactive variant, `SupportSessionIndicator`, replaces the persona label during a Nomology support session ([[PKG-support-access-and-impersonation]]) and cannot be hidden or themed.

Tenant memberships come from [[MT-tenancy-and-identity-schema]]; admin scopes from role assignments in [[PKG-authorization-data-model]]. APG pattern: Menu Button [R1] (disclosure with a list of links).

<!-- section:anatomy -->
## Anatomy

| Part | Required | Element |
|---|---|---|
| Active indicator | Yes | In the header: tenant mark logo, tenant display name and persona label, as the trigger button text |
| Trigger | When more than one option | `<button aria-expanded aria-haspopup="true">` with name "Switch organisation or role. Current: {tenant}, {persona}" |
| Popup | On open | List grouped by tenant; each item is a link to the target host and persona route group |
| Current marker | Yes | `aria-current="true"` and a check icon with text "Current" |
| Search | When more than 8 tenants | Filter input |
| Admin scope chip | In `/admin` when the user has unit-scoped roles | Button "Scope: {scope name}" opening a list of "Whole organisation" (only if tenant-scoped) and assigned units, as links that set `?scope=` |
| Support banner | During a support session | Full-width `role="status"` region above the header: "Support session · {grant type} · read only · expires {time} · {grant ref}", fixed platform colours |

<!-- section:variants -->
## Variants and sizes

| Variant | Use |
|---|---|
| `header` (default) | Tenant and persona switcher in every persona shell |
| `menu-page` | Full page at `/switch` for mobile and for users with many memberships |
| `admin-scope` | Admin scope chip in the `/admin` shell only |
| `support-session` | Non-interactive indicator and banner during a support session; replaces `header` |

<!-- section:states -->
## States

Closed, open, switching (link navigates; the page shows a full-page loading state "Opening {tenant}…"), unavailable membership (suspended tenant or revoked membership, shown disabled with reason), scope restricted (admin scope chip shows only units the user administers; a unit archived since the last visit is removed with a toast "Your access to {unit} has changed"), support session (indicator locked, switcher disabled because the support principal has no memberships), elevated (during a just-in-time elevation from [[PKG-jit-and-break-glass]] the persona label shows "Administration · elevated until 15:10").

<!-- section:api -->
## Props API

```ts
type PersonaId = 'counsel' | 'neutral' | 'secretariat' | 'transcriber' | 'admin';
type Membership = {
  tenantId: string; tenantDisplayName: string; tenantMarkUrl: string; host: string;
  personas: Array<{ id: PersonaId; label: string; href: string }>;
  status: 'active' | 'suspended';
};
export type TenantSwitcherProps = { current: { tenantId: string; personaId: PersonaId }; memberships: Membership[] };
export type ActiveTenantIndicatorProps = {
  tenantDisplayName: string; tenantMarkUrl: string; personaLabel: string;
  elevatedUntil?: string;                       // ISO time, shows the elevated state
};
export type AdminScopeSwitcherProps = {
  current: { type: 'tenant' } | { type: 'unit'; unitId: string; name: string };
  options: Array<{ type: 'tenant' } | { type: 'unit'; unitId: string; name: string; path: string[] }>;  // path = ancestor names
  hrefFor: (scope: AdminScopeSwitcherProps['current']) => string;   // builds ?scope= URL
};
export type SupportSessionIndicatorProps = { grantRef: string; grantType: string; readOnly: boolean; expiresAt: string };
```
The `admin` persona appears in the list when the membership holds any administrative role at any scope; its label is "Administration" (tenant terminology may rename it).

<!-- section:behaviour -->
## Behaviour

Switching tenant or persona is a full navigation to the target tenant's host (`https://{tenant-host}/{persona-route}`), never an in-place state change. This rebuilds tenant context in middleware ([[MT-tenant-resolution]]), theme, messages and caches, and clears TanStack Query caches as required by [[APP-client-state-and-data-fetching]]. If the target tenant is in another region, the navigation goes to that region's stack ([[MT-data-residency-2]]); sign-in is handled by the platform identity flow ([[PKG-authentication]]). Other open tabs of the previous tenant keep working within their own tenant; because each tenant has its own host, a tab can never show mixed tenants. The membership list is loaded server-side for the signed-in user only. Switching emits `session.tenant_switched` to the audit trail.

Changing admin scope is a navigation within the same host that changes `?scope=`; the server re-checks the scope on every request, so editing the URL to a unit the user does not administer returns not-found. The admin console discards query caches keyed by the previous scope. Scope changes are not audited (they grant nothing), but every op records the scope it ran at.

During a support session the switchers are not rendered; the support banner cannot be dismissed, and its end time updates if the grant is revoked (session ends within 30 seconds).

<!-- section:keyboard -->
## Keyboard, focus and assistive technology

| Key | Action |
|---|---|
| Enter / Space on trigger | Open; focus first item (current item if present) |
| Down / Up | Move between items |
| Enter | Follow link (switch) |
| Escape | Close; focus returns to trigger |
| Tab | Close and move on |

WCAG: 2.1.1, 2.4.3, 2.4.4, 3.2.1, 3.2.2 (switching happens only on explicit activation), 4.1.2.

<!-- section:content -->
## Content guidelines

- Indicator: "{Tenant display name} · {Persona}" (for example "Institution name · Counsel"). The tenant name comes from the tenant's branding display name; persona labels from tenant terminology.
- Admin scope chip: "Scope: Whole organisation" or "Scope: {unit name}"; options show the unit path ("Head office › SEBI ODR desk").
- Elevated: "Administration · elevated until {time}".
- Support banner: "Support session · {grant type in words} · read only · ends at {time} · reference {grant ref}". Grant types in words: "configuration (view)", "configuration (change)", "case access (view)", "viewing as {user display name}", "emergency access".

<!-- section:tokens -->
## Tokens used

`header.bg`, `header.fg`, `elevation.2`, `listbox.option.*`, `radius.lg`, `size.icon.lg` for the tenant mark.

<!-- section:responsive -->
## Responsive behaviour and direction

Below `md` the indicator shows the tenant mark and persona in the header; selecting it opens the `/switch` page. The active tenant name is always available as text (visually or via the trigger's accessible name), never only as a logo.

<!-- section:examples -->
## Usage examples

```tsx
<ActiveTenantIndicator tenantDisplayName={tenant.displayName} tenantMarkUrl={tenant.markUrl} personaLabel={t(`persona.${persona}`)} />
<TenantSwitcher current={{ tenantId: tenant.id, personaId: persona }} memberships={memberships} />
```

<!-- section:testing -->
## Testing

Common to all components (see [[PKG-design-system-component]]): Storybook stories per variant × state, play-function interaction tests including the keyboard-only path, axe-core on every story (serious and critical fail the build), Playwright visual snapshots in a pinned Docker image across 5 fixture themes × light / dark / high contrast, plus RTL where layout is direction-dependent, and a forced-colours snapshot (Chromium `forcedColors: 'active'` emulation). Manual screen reader pass each release per the AT matrix in [[APP-accessibility-wcag-2-1-aa]] (NVDA + Chrome / Firefox, JAWS + Chrome on managed Windows, VoiceOver + Safari on macOS and iOS, TalkBack + Chrome on Android).

Specific: Playwright test that switching navigates to the other host and that the previous tenant's cached data is not visible; story with 30 memberships and search.

Additional: admin scope chip stories (tenant-scoped admin, unit-only admin with 1 and 12 units, archived unit); Playwright test that a hand-edited `?scope=` for an unassigned unit returns not-found; support-session story with the banner in all five fixture themes proving fixed colours; elevated state story.

<!-- section:questions -->
## Open questions

- [ ] Is persona switching within a tenant also a full navigation (proposed yes, since route groups differ) (owner: frontend lead).
- [ ] Do we show memberships in other regions in the list (requires a global directory lookup) (owner: architecture, with [[MT-data-residency-2]]).
- [ ] Should unit admins with several unassociated units be able to choose "All my units" as one scope? Proposed: yes, as a union scope, if [[PKG-authorization-data-model]] supports multi-unit assignments in one decision. (owner: authz group)

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Assistive technology conformance

Menu button with list of links, current item marked with `aria-current` and text, trigger name includes the current tenant and persona, switching only on explicit activation, focus returns on close.

<!-- check:theming -->
### Tenant themes and modes

The indicator uses the tenant's validated mark logo and display name; the switcher list shows each tenant's mark but not their colours, so one tenant's palette never appears inside another tenant's page; the support banner and elevated state use fixed platform semantic tokens.

<!-- check:security -->
### Data safety in the component

Switching tenant is a full navigation to another host so tenant context, theme and caches are rebuilt; the membership list comes from the server for the signed-in user only; the switch is audited. Admin scope is re-checked on every request; the support banner uses locked platform tokens so no tenant theme can hide a support session.

<!-- check:resilience -->
### Async, errors and edge cases

A suspended tenant or revoked membership is shown disabled with a reason; if the target region is unavailable the navigation shows the platform error page for that region rather than falling back to another region.

<!-- check:testing -->
### Test and documentation coverage

Stories for 1, 2 and 30 memberships, suspended membership and RTL; interaction tests for the menu-button keyboard model; Playwright test that switching lands on the other tenant's host with fresh caches.

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C",
    "id": "R1",
    "ident": "WAI-ARIA APG",
    "kind": "standard",
    "title": "ARIA Authoring Practices Guide: Patterns",
    "url": "https://www.w3.org/WAI/ARIA/apg/patterns/"
  }
]
```

<!-- end -->
