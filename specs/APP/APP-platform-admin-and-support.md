---
id: "APP-platform-admin-and-support"
title: "Platform admin and support console"
parent: "APP-route-groups-per-persona"
order: 6
type: "requirement"
template: "frontend"
status: "draft"
owner: null
indicative: false
summary: "Frontend architecture for the (platform-admin) route group at /platform: tenant provisioning and lifecycle, blueprints, platform/region/offering settings, operations, consent-based support access and break-glass, per region"
links: []
rev: 3
syncHash: "19d67eab9b59c297"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 2.1.2.6 Platform admin and support console

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Frontend architecture for the (platform-admin) route group at /platform: tenant provisioning and lifecycle, blueprints, platform/region/offering settings, operations, consent-based support access and break-glass, per region

<!-- section:scope -->
## Scope, audiences and surfaces

Frontend architecture of the `(platform-admin)` route group, prefix `/platform` (renamed from `/ops` to match the shared model; `/ops/*` redirects for one release), served only on the platform-admin host of each region (one per region; there is no global console). Personas (shared-model keys): `platform_owner`, `platform_admin`, `regional_ops`, `platform_support` (tiers 1 and 2), `platform_security`, `platform_billing`. Their capabilities are listed in [[APP-administration-model#design]] sections 6.1 and 6.2.

**Covers**: region overview; tenant directory for the region and tenant detail; tenant provisioning from blueprints ([[APP-tenant-onboarding-wizard]]) and lifecycle actions ([[MT-tenant-lifecycle]]); plans and entitlements per tenant ([[BIL-plans-entitlements-and-usage]]); tenant blueprints ([[PKG-configuration-packages]]); platform, region and offering settings ([[PKG-settings-catalogue]], [[PKG-settings-platform-operations]]); release flags per tenant ([[PKG-feature-flags]]); maintenance windows and banners; workflow and job operations (links into Temporal UI and BullMQ dashboards with codec restrictions); support requests, grants and "view as" sessions ([[PKG-support-access-and-impersonation]]); break-glass ([[PKG-jit-and-break-glass]]); platform staff role mirror; platform audit; accessibility and CSP report triage.

**Out of scope**: direct database access tools; cross-tenant analytics (served from the reporting role, [[MT-cross-tenant-reporting-via-a]]); deployment configuration and secrets ([[FND-environment-management]]); reading tenant data (only inside an approved support session on the tenant host).

<!-- section:routing -->
## Routes, layouts and boundaries

```text
app/(platform-admin)/platform/
  layout.tsx                    # fixed platform theme; "Platform operations — {region}" banner; requirePlatformRole()
  page.tsx                      # region health, open incidents, provisioning in progress, pending support requests, expiring grants
  tenants/  tenants/new/        # provisioning wizard (APP-tenant-onboarding-wizard)
  tenants/[tenantId]/           # overview: status, plan, blueprint version, region, domains, admins (names masked), usage
  tenants/[tenantId]/lifecycle/ # workflow status query, suspend / reinstate / offboard / approve deletion
  tenants/[tenantId]/plan/  tenants/[tenantId]/domains/  tenants/[tenantId]/flags/  tenants/[tenantId]/region/
  blueprints/  blueprints/[blueprintId]/versions/[version]/
  settings/  settings/[domain]/  regions/[region]/settings/  offerings/[offering]/settings/
  flags/
  operations/  maintenance/  banners/  workflows/  jobs/  dlq/
  support/  requests/  requests/new/  requests/[requestId]/  sessions/  sessions/[sessionId]/
  break-glass/  break-glass/[grantId]/
  approvals/                    # platform maker-checker inbox
  staff/                        # read-only mirror of workforce IdP groups → platform roles
  audit/
  reports/csp/  reports/accessibility/
```
`proxy.ts` returns 404 for `/platform` on tenant hosts and for anything except `/platform` (and `/ops` redirects) on the platform-admin host. Every page calls `requireOp()` with its platform op key; navigation is generated from the admin operation registry, as in the tenant console.

<!-- section:rendering -->
## Rendering and caching strategy

Dynamic, `private, no-store`. No `'use cache'` for any data in this group, so operators always see current state. Lifecycle pages poll the Temporal workflow `status` query every 5 seconds while a workflow step is running.

<!-- section:data -->
## Data fetching and mutations

All mutations call `runAdminOp` with `plane='platform'` and run in platform context against platform-level tables of this region ([[MT-platform-level-tables]]).

| Operation | Kind | Notes |
|---|---|---|
| `platform.tenant.create` / `.provision` | Server Actions | Draft row, then starts workflow `{tenantId}-tenant-lifecycle-{tenantId}` on queue `platform-ops` in this region |
| `platform.tenant.suspend` / `.reinstate` / `.offboard` | Server Actions | Reason code and ticket ID required; offboard is maker-checker; sends a Temporal Update and shows its result |
| `platform.tenant.approve_deletion` | Server Action | `platform_owner` with DPO sign-off reference; typed confirmation of tenant slug; irreversible |
| `platform.tenant.set_plan` | Server Action | Writes entitlements; tenant `billing_admin` notified |
| `platform.blueprint.publish` | Server Action | Versioned, signed configuration package; maker-checker |
| `platform.settings.publish` | Server Action | Platform, region or offering scope; bounds changes show how many tenants have values outside the new bound before confirming |
| `platform.flag.set` | tRPC | Release flags per tenant and region ([[PKG-feature-flags]]); not settings |
| `platform.maintenance.schedule`, `platform.banner.publish` | Server Actions | Banners can target platform, region, offering or one tenant; tenant banners show in that tenant's persona shells |
| `platform.workflow.operate` | Server Action | Retry, cancel, terminate, reset or replay dead-letter jobs; reason required; step-up |
| `platform.support.request` | tRPC mutation | Creates a request the tenant approves in `/admin/security/support-access`, unless the tenant's consent mode allows it |
| `platform.support.start_session` | Server Action | Only with an approved, unexpired grant; opens a tenant-host session in a new tab marked "Support session" |
| `platform.break_glass.request` / `.approve` | Server Actions | Second approver required; time-limited; paged to security; tenant notified ([[PKG-jit-and-break-glass]]) |

Tenant data is never read through this group directly; all tenant-scoped reads happen inside an approved support session on the tenant host, under the tenant's own audit trail.

<!-- section:state -->
## Client state and URL state

Filters and selected tenant tab in the URL. No drafts are kept in the browser: blueprint and settings drafts are server-side versions. On region switch (a different host) nothing is carried over.

<!-- section:forms -->
## Forms, validation and uploads

Every destructive or tenant-affecting form requires: reason code (from a fixed list per op), free-text note, ticket reference (validated against the ticket system's format), and a typed confirmation of the tenant slug for suspend, offboard and deletion approval. Settings and blueprint forms use the same `ConfigEditorLayout` as the tenant console.

<!-- section:errors -->
## Error, loading and empty handling

Missing or expired grant: 403 page with a "request access" link. Workflow start failures show the Temporal error class and a link to the runbook. Bounds change rejected because tenants have explicit values outside the new bound: the list of affected tenants is shown, with the option to lock (which freezes lower overrides by the rule in [[PKG-configuration-scope-hierarchy]]) or to cancel. Every destructive action shows a typed confirmation.

<!-- section:performance -->
## Performance budgets

Desktop budgets; no special targets beyond ≤ 250 KB gzip first-load JS. The tenant directory must list 1,000 tenants per region with filters in under 1 s.

<!-- section:security -->
## Security headers and browser session

- Reachable only through the corporate zero-trust network; the WAF allows only the identity-aware proxy's addresses ([[INF-networking]]).
- Sign-in with the workforce IdP plus phishing-resistant MFA (passkey or hardware key); 15 min idle, 8 h absolute (bounds in [[PKG-settings-platform-operations]] `platform.console.*`).
- Platform roles come only from workforce IdP groups; the `/platform/staff` page is a read-only mirror. Joiner, mover and leaver handling is in [[SEC-access-reviews]].
- Step-up on every break-glass, suspend, offboard, deletion approval, workflow operator action and support session start.
- Strict nonce CSP with no third-party scripts at all.
- Every action writes an audit event to the platform audit stream and, where it touches a tenant, to that tenant's audit trail ([[PKG-audit-trail]]), so the tenant sees provisioning, suspension, plan and support events in [[APP-admin-change-history]].

<!-- section:theming -->
## Tenant theming hookup

Fixed platform theme, visibly different from any tenant; a permanent banner with the region name and the operator's role.

<!-- section:observability -->
## Frontend observability

Dashboards of operator actions per region, by `op_key` and operator; alert when a break-glass grant is used; alert when any tenant stays in `provisioning_failed` over 1 hour; weekly report of support sessions per tenant sent to tenant security admins (setting `access.support.weekly_report`); monthly report of platform operator actions to the ISMS lead.

<!-- section:testing -->
## Testing strategy

Tests that `/platform` is unreachable on tenant hosts in each region; `/ops` redirects; view-as without grant fails; break-glass needs a second approver; offboarding needs a second approver; deletion approval requires `platform_owner`; audit events are written to both platform and tenant streams for tenant-affecting actions; navigation shows only the sections of each platform role.

<!-- section:questions -->
## Open questions

- [ ] Separate app and image for `(platform-admin)` so it can run only on private networking? (owner: security lead; Decision record needed)
- [ ] Is "view as" read-only always, or can support act with tenant approval (for example to fix a stuck filing)? Proposed in [[PKG-support-access-and-impersonation]]: read-only in v1; writes only through `config_write` grants. (owner: security with tenants)
- [ ] Should the route-group table in [[APP-route-groups-per-persona]] be updated from `/ops` to `/platform`? Proposed yes. (owner: frontend lead)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation in rendering and caching

The console reads only platform-level tables (tenant registry, plans, flags, grants, blueprints) with the platform role; tenant data is reached only through approved support sessions on the tenant host, under tenant RLS and the tenant's audit trail.

<!-- check:data-exposure -->
### Server boundary and data exposure

No tenant case data is rendered in `/platform`; tenant admin names and emails are masked in tenant detail. Support sessions happen on the tenant host under grant, are read-only by default and time-limited, and appear in the tenant's audit and in a weekly report to tenant security admins.

<!-- check:browser-security -->
### Browser security posture

No third-party scripts; strict nonce CSP; `frame-ancestors 'none'`; host-level separation enforced in `proxy.ts` and at the WAF; the console is reachable only through the zero-trust proxy.

<!-- check:session -->
### Sessions in the browser

Workforce IdP with phishing-resistant MFA; 15 min idle and 8 h absolute; step-up on every high-impact action.

<!-- check:resilience -->
### Failure, deploys and version skew

Lifecycle actions are Temporal Updates whose result is shown when it returns; if the console disconnects, the workflow continues and the lifecycle page shows its current step on reload. Operator actions are idempotent by op ID.

<!-- check:residency -->
### Region, residency and telemetry privacy

One console per region against that region's data; there is no global console that can see tenants of all regions, so operators switch region by host. Platform settings at `platform` scope are replicated as configuration packages to each region, not read cross-region.

<!-- end -->
