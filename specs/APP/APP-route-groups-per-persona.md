---
id: "APP-route-groups-per-persona"
title: "Route groups per persona"
parent: "APP-app-configuration"
order: 2
type: "feature"
template: "frontend"
childTemplate: "frontend"
status: "draft"
owner: null
indicative: false
summary: "Map of the route groups of apps/web (public, six persona groups and the shared (account) group), their URL prefixes, hosts and session rules, a summary of the tenant admin, platform and personal settings route trees, and the defaults (layouts, boundaries, rendering, budgets, testing) every group inherits"
links: []
rev: 4
syncHash: "af3c551eada8a201"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 2.1.2 Route groups per persona

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Map of the route groups of apps/web (public, six persona groups and the shared (account) group), their URL prefixes, hosts and session rules, a summary of the tenant admin, platform and personal settings route trees, and the defaults (layouts, boundaries, rendering, budgets, testing) every group inherits

<!-- section:scope -->
## Scope, audiences and surfaces

This is the app-level frontend node. It defines the route groups of `apps/web`, the URL prefix each one owns (route groups do not change URLs, so prefixes keep them apart), the personas allowed in each, and the defaults every group inherits. Group nodes record only their differences.

| Route group | URL prefix | Host | Personas | Node |
|---|---|---|---|---|
| `(public)` | `/`, `/sign-in`, `/invite/[token]`, `/sso/[connection]`, `/file/*`, `/status`, `/accessibility`, `/legal/*` | tenant host | anyone, unauthenticated | [[APP-public-and-sign-in-surfaces]] |
| `(counsel)` | `/portal/*` | tenant host | party (claimant, respondent, investor, MSME claimant), counsel / authorised representative | [[APP-party-and-counsel-portal]] |
| `(neutral)` | `/tribunal/*` | tenant host | arbitrator, presiding arbitrator, mediator, conciliator | [[APP-neutral-workspace]] |
| `(secretariat)` | `/secretariat/*` | tenant host | `secretariat` (registry staff), acting on cases as `case_manager` or `tribunal_secretary` | [[APP-secretariat-console]] |
| `(transcriber)` | `/transcription/*` | tenant host | transcriber, transcript reviewer | [[APP-transcriber-workspace]] |
| `(tenant-admin)` | `/admin/*` | tenant host | tenant administrative roles (`tenant_owner`, `tenant_admin`, `security_admin`, `user_admin`, `workflow_designer`, `integration_admin`, `content_admin`, `billing_admin`, `ai_admin`, `auditor`, `unit_admin`) at tenant or unit scope; navigation shows only what the user's operations allow | [[APP-tenant-admin-console]] |
| `(platform-admin)` | `/platform/*` (old `/ops/*` redirects only) | platform-admin host per region, reachable only over the corporate zero-trust network | Nomology staff with platform roles (`platform_owner`, `platform_admin`, `platform_support`, `platform_security`, `platform_billing`, `regional_ops`) | [[APP-platform-admin-and-support]] |
| `(account)` | `/me/settings/*` | tenant host | every signed-in user, inside the shell of their active persona | [[PKG-personalisation]] |

A user can hold several personas in one tenant (for example a tribunal secretary who is also a tenant admin) and memberships in several tenants (counsel at an arbitral institution tenant and at a SEBI ODR institution tenant). The persona switcher ([[PKG-tenant-and-role-switcher]]) navigates between prefixes; the tenant switcher moves to another tenant host.

Administrative routes are summarised under Routing and owned by [[APP-tenant-admin-console]] and [[APP-platform-admin-and-support]]; the admin model is [[APP-administration-model]].

Out of scope: screen-level journeys (UI nodes), the permission matrix itself ([[PKG-policy-engine-permission-matrix]]).

<!-- section:routing -->
## Routes, layouts and boundaries

```text
app/
  (public)/
    layout.tsx                 # tenant-branded minimal shell, no session needed
    sign-in/  invite/[token]/  sso/[connection]/  file/  status/  accessibility/  legal/
  (counsel)/portal/
    layout.tsx                 # persona shell: header, tenant + role switcher, nav, skip link
    loading.tsx  error.tsx
    ...                        # see APP-party-and-counsel-portal
  (neutral)/tribunal/          layout.tsx  error.tsx ...
  (secretariat)/secretariat/   layout.tsx  error.tsx ...
  (transcriber)/transcription/ layout.tsx  error.tsx ...
  (tenant-admin)/admin/        layout.tsx  error.tsx ...    # tree summarised below; APP-tenant-admin-console
  (platform-admin)/platform/   layout.tsx  error.tsx ...    # tree summarised below; APP-platform-admin-and-support
  (account)/me/settings/       layout.tsx  error.tsx ...    # personal settings in the active persona's shell; PKG-personalisation
```

**Administration and account route trees (summary).** The detail, including every page, belongs to the linked nodes; this table only fixes the prefixes so groups do not collide. The admin planes and personas are defined in [[APP-administration-model]].

Tenant admin console, `/admin/*` ([[APP-tenant-admin-console]]; admin copilot in the `@copilot` slot, [[APP-admin-copilot]]):

| Prefix | Holds | Detail |
|---|---|---|
| `/admin`, `/admin/setup` | Overview, setup checklist | [[APP-tenant-admin-console]], [[APP-tenant-onboarding-wizard]] |
| `/admin/organisation/*` | Profile, units, domains, owners | [[APP-administration-model]], [[PKG-domain-verification]] |
| `/admin/users/*`, `/admin/groups/*` | Members, invitations, member access and security, groups | [[APP-user-and-access-admin]], [[PKG-user-provisioning-scim]] |
| `/admin/access/*` | Roles, permission sets, access reviews, access requests, access explainer | [[PKG-roles-and-permission-sets]], [[SEC-access-reviews]], [[PKG-access-explainer]] |
| `/admin/security/*` | SSO connections, authentication policies, provisioning, sessions, support access | [[PKG-sso-saml-oidc-per-tenant]], [[PKG-authentication-policies]], [[PKG-support-access-and-impersonation]] |
| `/admin/settings/*` | Settings pages generated per catalogue (`/admin/settings/[domain]`) | [[PKG-settings-catalogue]] |
| `/admin/workflows/*` | Case types and blueprint versions (canvas, validation, simulation, diff, review), in-flight migrations, automation rules, SLA policies, business calendars, work queues, library | [[WF-workflow-authoring-studio]], [[WF-workflow-versioning]], [[WF-automation-rules]], [[WF-sla-and-business-calendars]], [[WF-workflow-simulation]] |
| `/admin/content/*` | Branding, terminology, document templates, legal text, accessibility statement | [[PKG-branding-and-theming]], [[PKG-tenant-terminology-and-copy]], [[PKG-settings-branding-content]] |
| `/admin/notifications/*` | Notification templates and notification policies | [[PKG-notification-policies]], [[PKG-settings-notifications]] |
| `/admin/integrations/*` | Connections, API clients, webhooks and delivery logs, connector data policies | [[INT-connections-admin]], [[PKG-api-clients-and-keys]], [[APP-webhooks-outbound]], [[INT-connector-data-policies]] |
| `/admin/ai/*` | Tenant AI policy, assistants and agents, AI usage | [[AI-tenant-ai-policy]], [[AI-agent-configuration]], [[PKG-settings-ai]] |
| `/admin/data/*` | Retention, legal holds, exports, data requests | [[PKG-settings-data-and-privacy]] |
| `/admin/billing/*` | Plan, usage, invoices, billing contacts | [[PKG-settings-billing-and-plans]] |
| `/admin/packages/*`, `/admin/sandboxes` | Configuration packages, sandboxes | [[PKG-configuration-packages]], [[PKG-configuration-lifecycle]] |
| `/admin/approvals/*`, `/admin/history/*`, `/admin/audit` | Maker-checker inbox, change sets and rollback, audit log | [[PKG-separation-of-duties]], [[APP-admin-change-history]] |
| `/admin/bulk/*`, `/admin/reports/*` | Bulk jobs, admin reports | [[APP-bulk-admin-operations]] |

Platform console, `/platform/*` on the platform-admin host ([[APP-platform-admin-and-support]]):

| Prefix | Holds | Detail |
|---|---|---|
| `/platform` | Region health, incidents, provisioning, pending support requests | [[APP-platform-admin-and-support]] |
| `/platform/tenants/*` (`/platform/tenants/new` is the wizard) | Tenant provisioning, lifecycle, plan, domains, per-tenant flags, region | [[APP-tenant-onboarding-wizard]], [[MT-tenant-lifecycle]] |
| `/platform/blueprints/*` | Tenant blueprints and their versions | [[PKG-configuration-packages]] |
| `/platform/settings/*`, `/platform/regions/[region]/settings`, `/platform/offerings/[offering]/settings` | Platform, region and offering scope settings | [[PKG-settings-platform-operations]], [[PKG-configuration-scope-hierarchy]] |
| `/platform/flags` | Release flags and kill switches | [[PKG-feature-flags]] |
| `/platform/operations/*` | Maintenance windows, banners, workflows, jobs, dead-letter queues | [[APP-platform-admin-and-support]] |
| `/platform/support/*`, `/platform/break-glass/*` | Support requests and sessions, break-glass grants | [[PKG-support-access-and-impersonation]], [[PKG-jit-and-break-glass]] |
| `/platform/approvals`, `/platform/staff`, `/platform/audit`, `/platform/reports/*` | Platform maker-checker inbox, staff roles (read-only mirror of the workforce IdP), audit, CSP and accessibility reports | [[APP-platform-admin-and-support]] |

Personal settings, `/me/settings/*` (`(account)` group, [[PKG-personalisation]], settings defined in [[PKG-settings-personal]]): profile, language and region, appearance, accessibility, notifications, shortcuts, saved views, connected accounts. The group renders inside the shell of the user's active persona (a party sees the simplified party shell) and needs only a valid session, no administrative role.

**Legacy prefixes.** `/ops/*` is no longer a route: on the platform-admin host `proxy.ts` answers with a permanent redirect to the same path under `/platform/*`, and on tenant hosts it returns 404 like `/platform`. The redirect stays for 12 months ([[APP-app-router-next-config]]).


**Defaults every persona group inherits**
- `layout.tsx` per group renders the shell only: tenant name and logo, persona navigation, switchers, session-expiry warning, skip link, `<main id="main" tabIndex={-1}>`. It calls `requirePersona('<persona>')`, which redirects to `/sign-in` if the session is invalid and to a "you do not have access to this area" page if the persona is missing. Because layouts do not re-run on every navigation, **each page and action repeats its own check**.
- `error.tsx` at the group root and at each `[caseRef]` (or equivalent entity) segment, so a failure in one case leaves navigation usable.
- `not-found.tsx` at each entity segment, used for both missing and forbidden entities.
- `loading.tsx` only where a full-page skeleton is better than a streamed section; otherwise `<Suspense>` inside the page.
- Parallel `@modal` slots with intercepting routes are allowed for previews (document, party details) when the full route also exists for deep links.
- Entity URLs use the tenant-visible case reference (`caseRef`, for example `ARB-2026-00123`), never database UUIDs; the server maps the reference to the ID inside the tenant transaction.

<!-- section:rendering -->
## Rendering and caching strategy

Defaults (the trade-off is argued in [[APP-rendering-and-caching-strategy]]):

| Group | Default rendering | CSP | Cache-Control |
|---|---|---|---|
| `(public)` | Static shell plus dynamic tenant branding hole | hash-based | see [[APP-public-and-sign-in-surfaces]] |
| All authenticated groups | Dynamic per request, streamed; data-level caching only through tenant-keyed `'use cache: remote'` for reference data, rules and settings | nonce-based | `private, no-store` |

No authenticated page is prerendered at build time. `generateStaticParams` is not used in authenticated groups.

<!-- section:data -->
## Data fetching and mutations

Defaults:
- **Reads** in Server Components through `@nomology/data-access` (server-only; tenant transaction via [[MT-prisma-client-extension-wraps]]; permission checks via [[PKG-authorization]]).
- **Interactive client views** (filters, live queues, editors) read through tRPC with TanStack Query ([[APP-internal-api-trpc-routers-per]], [[APP-client-state-and-data-fetching]]).
- **Writes**: Server Actions for form submissions and single-entity commands; tRPC mutations for interactive or bulk operations. Rules in [[APP-server-actions-and-mutation]].
- After a write, the action calls `updateTag('tenant:{tenantId}:case:{caseId}')` (read-your-own-writes) and the client invalidates the matching TanStack Query keys.
- Long-running work (bundling, transcription, bulk import) starts a Temporal workflow and returns an operation ID; the UI polls a tRPC query or subscribes to status.

<!-- section:state -->
## Client state and URL state

Inherited defaults ([[APP-client-state-and-data-fetching]] holds the full rules): filters, sort, pagination and selected tab live in the URL; server data lives in TanStack Query with keys prefixed by `tenantId`; drafts live on the server (preferred) or in IndexedDB keyed `{userId}:{tenantId}:{draftKey}`. One `QueryClient` per tenant session: the provider is keyed by `tenantId`, so switching tenant discards the cache. Sign-out broadcasts on `BroadcastChannel('session')`; every tab clears caches and IndexedDB drafts that are not yet synced only after asking the user.

<!-- section:forms -->
## Forms, validation and uploads

Defaults: React Hook Form with Zod schemas imported from the same package the server action or procedure validates with ([[PKG-form-fields]]); server errors return `fieldErrors` keyed by field path and are mapped to inputs with `setError`; the error summary component receives focus on submit failure. Forms built from tenant definitions use [[PKG-forms-and-form-builder]]. Uploads use [[PKG-file-upload-dropzone]] with direct-to-storage signed URLs ([[PKG-encryption-at-rest-signed-urls]]). Simple forms (sign-in, accept invitation, file a short reply) must work before JavaScript loads (progressive enhancement through Server Actions).

<!-- section:errors -->
## Error, loading and empty handling

| Error type | Default handling |
|---|---|
| Domain rule error (for example deadline passed, stage does not allow filing) | Returned as a typed result from the action or as a problem from tRPC; shown inline with the error summary pattern |
| Not found or no access | `notFound()` → entity-level `not-found.tsx`, identical copy |
| Session expired | `unauthorized()` → redirect to `/sign-in?next=`; drafts kept |
| Missing persona | "You do not have access to this area" page with links to the user's other personas |
| Server failure | Nearest `error.tsx` with retry and support reference (`digest` plus request ID) |
| Network failure (client) | Inline banner "You are offline. We will try again when you are back online."; mutations queued only where the group says so |
| Rolling deploy, stale bundle | Hard navigation forced by `deploymentId`; drafts saved first |

Copy is in [[APP-error-message-catalogue]]; boundary mechanics in [[APP-error-boundaries-loading-and]].

<!-- section:performance -->
## Performance budgets

Default budgets per group (p75 in RUM, per region; full set in [[APP-frontend-performance-budgets]]):

| Group | Device / network profile | LCP | INP | CLS | Route JS (gzip, first load) | TTFB |
|---|---|---|---|---|---|---|
| `(public)` | mid-range Android, slow 4G | ≤ 2.0 s | ≤ 200 ms | ≤ 0.1 | ≤ 130 KB | ≤ 200 ms |
| `(counsel)` | mid-range Android, slow 4G | ≤ 2.5 s | ≤ 200 ms | ≤ 0.1 | ≤ 180 KB | ≤ 600 ms |
| `(neutral)` | laptop, broadband | ≤ 2.5 s | ≤ 200 ms | ≤ 0.1 | ≤ 250 KB (excl. editor chunk) | ≤ 600 ms |
| `(secretariat)` | managed Windows desktop | ≤ 2.5 s | ≤ 200 ms | ≤ 0.1 | ≤ 260 KB | ≤ 800 ms |
| `(transcriber)` | laptop, broadband | ≤ 2.5 s | ≤ 200 ms | ≤ 0.1 | ≤ 300 KB incl. editor | ≤ 600 ms |
| `(tenant-admin)`, `(platform-admin)` | desktop | ≤ 2.5 s | ≤ 200 ms | ≤ 0.1 | ≤ 250 KB | ≤ 800 ms |

These are proposed targets; Core Web Vitals thresholds follow web.dev [R1].

<!-- section:security -->
## Security headers and browser session

Defaults for every authenticated group: nonce-based strict CSP, `frame-ancestors 'none'`, `Cache-Control: private, no-store`, session in a `__Host-` cookie ([[APP-security-headers-csp-cors]], [[PKG-mfa-session-management-device]]).

Proposed session timeouts per persona (to be confirmed with security and tenants):

| Persona group | Idle timeout | Absolute timeout | Step-up (re-enter MFA) for |
|---|---|---|---|
| `(counsel)` | 30 min (15 min if "shared device" chosen) | 12 h | changing bank details, adding a representative, withdrawing a claim |
| `(neutral)` | 60 min | 12 h | issuing an award or order, signing |
| `(secretariat)` | 30 min | 10 h | bulk actions over 50 cases, issuing on behalf of tribunal |
| `(transcriber)` | 60 min | 12 h | certifying a transcript |
| `(tenant-admin)` | 15 min | 8 h | role changes, SSO and theme activation, API key creation |
| `(platform-admin)` | 15 min | 8 h | every break-glass action |

`(account)` pages use the session rules of the user's active persona. In `(tenant-admin)` and `(platform-admin)`, step-up requirements per operation come from the authentication policies ([[PKG-authentication-policies]]) and the permission catalogue ([[PKG-permission-catalogue]]); the table above gives the defaults.

A warning dialog appears 2 minutes before idle expiry with "Stay signed in" (WCAG 2.2.1).

<!-- section:i18n -->
## Localisation hookup

Defaults from [[APP-app-router-next-config]]. Each group loads only its message namespace (`public`, `portal`, `tribunal`, `secretariat`, `transcription`, `admin`, `platform`, `account`) plus `common`. Dates and deadlines are shown with the absolute date, time and time zone of the seat, plus the viewer's local time when it differs (for example "5 March 2026, 17:00 Singapore time (14:30 your time)") using [[I18N-l10n]] and [[PKG-calendars-and-deadline]]. `(platform-admin)` is English only.

<!-- section:theming -->
## Tenant theming hookup

All tenant-facing groups use the tenant theme from the root layout. `(platform-admin)` uses a fixed, visibly different platform theme (distinct header colour and a permanent "Platform operations" banner) so staff never confuse it with a tenant surface. Focus indicators come from design-system tokens and cannot be overridden by tenant colours ([[PKG-tenant-theme-accessibility]]).

<!-- section:observability -->
## Frontend observability

Every signal carries `route.group` (one of the seven names above) and `persona`. Dashboards per group and region: Web Vitals, error-boundary hits by route template, Server Action failure rate, tRPC error rate by problem type. See [[OBS-frontend-real-user-monitoring]].

<!-- section:testing -->
## Testing strategy

Each group must have: Playwright journeys per persona with axe checks on every visited state, keyboard-only runs of the group's critical journeys, a negative-access suite (persona B cannot reach persona A's prefix; party of case X cannot open case Y), the two-tenant diff test on the group's main pages, visual regression in two tenant themes and dark mode, and bundle-size checks. Tooling in [[TST-unit-integration-contract-and]] and [[TST-accessibility-testing]].

<!-- section:questions -->
## Open questions

- [ ] Should `(platform-admin)` move to a separate Next.js app and image so it can be deployed only inside the private network? (owner: security lead; Decision record needed)
- [ ] Confirm URL prefixes with product, especially whether SEBI ODR investor journeys need a simpler prefix than `/portal` (owner: product, CORD)
- [ ] Confirm proposed session timeouts with security and with institution tenants that have their own policies (owner: security, [[PKG-mfa-session-management-device]])
- [ ] Do transcribers who work for several tenants need a cross-tenant work queue, which would conflict with tenant-per-host? (owner: TERES product, [[DOM-transcribers]])

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation in rendering and caching

Defense in layers: (1) tenant from host in `proxy.ts`; (2) `requirePersona()` checks membership of the session user in that tenant; (3) every data read in `@nomology/data-access` runs in a tenant transaction with forced RLS; (4) no authenticated page is prerendered or cached as HTML (`private, no-store`); (5) data-level caches take `tenantId` as an argument; (6) the TanStack Query provider is keyed by `tenantId`; (7) the two-tenant diff test runs per group. Counsel with memberships in two tenants switch by changing host, which gives a fresh document, query cache and cookie scope.

<!-- check:data-exposure -->
### Server boundary and data exposure

Pages and actions call `@nomology/data-access` (marked `import 'server-only'`), which applies [[PKG-policy-engine-permission-matrix]] and returns view objects shaped for the screen rather than Prisma records. Group layouts check persona only; pages and actions repeat full checks because layouts are not re-run on navigation. Not-found and forbidden entities both render `not-found.tsx` with the same copy.

<!-- check:session -->
### Sessions in the browser

Session cookie is `__Host-session` (HttpOnly, Secure, SameSite=Lax), validated server-side; idle and absolute timeouts per persona in the Security section, with a 2-minute warning and extend option. Sign-out in one tab is broadcast to all tabs, which clear their caches. Step-up actions per persona are listed in the Security section and implemented by [[PKG-mfa-session-management-device]].

<!-- check:capacity -->
### Rendering cost and capacity

All authenticated pages render per request, so capacity is set by server render cost. Proposed sizing basis: p95 render ≤ 150 ms CPU for list pages; peak in India at 09:00–11:00 IST on filing-deadline days. Each group's node states its own peak and page-size limits (for example the secretariat queue pages at 50 rows server-side). Load test per region before Approved, see [[TST-performance-and-load-testing]].

<!-- check:accessibility -->
### App-level accessibility mechanics

Each persona layout includes a skip link to `#main`, landmark structure (`header`, `nav`, `main`), and a route announcer: on client navigation, focus moves to the page `<h1>` and the new title is announced in a polite live region. Streaming sections announce completion only when the user triggered them. Session-expiry warning meets WCAG 2.2.1. Focus indicator tokens are not tenant-overridable.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "kind": "web",
    "publisher": "Google (web.dev)",
    "title": "Web Vitals",
    "url": "https://web.dev/articles/vitals"
  }
]
```

<!-- end -->
