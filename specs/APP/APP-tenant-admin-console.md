---
id: "APP-tenant-admin-console"
title: "Tenant admin console"
parent: "APP-route-groups-per-persona"
order: 5
type: "requirement"
template: "frontend"
status: "draft"
owner: null
indicative: false
summary: "Frontend architecture for the (tenant-admin) route group: console shell, permission-driven navigation, unit scope switcher and the shared draft → review → publish → history pattern for every admin area"
links: []
rev: 3
syncHash: "e35f88c1b45b9605"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 2.1.2.5 Tenant admin console

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Frontend architecture for the (tenant-admin) route group: console shell, permission-driven navigation, unit scope switcher and the shared draft → review → publish → history pattern for every admin area

<!-- section:scope -->
## Scope, audiences and surfaces

Frontend architecture of the `(tenant-admin)` route group, prefix `/admin`, on tenant hosts. It is the single console where an institution administers its own tenant. The administration model, personas and the full capability catalogue are in [[APP-administration-model]]; this node covers the console shell, information architecture and the patterns every admin page shares.

**Personas** (shared-model role keys): `tenant_owner`, `tenant_admin`, `security_admin`, `user_admin`, `workflow_designer`, `integration_admin`, `content_admin`, `billing_admin`, `ai_admin`, `auditor` (read-only, includes audit log) and `unit_admin` (or any delegated role assigned at unit scope). Each person sees only the sections for which they hold at least one operation.

**Covers**: overview and setup checklist; organisation (profile, units, domains, owners); users, groups and access; security and identity; settings for every domain; workflow and case-type configuration (entry to the studio); content and branding; notifications; integrations; AI; data and privacy; billing; packages and sandboxes; review queue (change sets in review); change history and audit; bulk jobs; reports; the admin copilot side panel.

**Child nodes** (detail lives there):

| Area | Node |
|---|---|
| Users, invitations, groups, roles, access reviews, access requests, access explainer | [[APP-user-and-access-admin]] |
| Audit log, change history, diffs, rollback, support activity | [[APP-admin-change-history]] |
| Bulk import, update and export | [[APP-bulk-admin-operations]] |
| Admin copilot panel | [[APP-admin-copilot]] |
| Workflow authoring studio (`/admin/workflows/*`) | [[WF-workflow-authoring-studio]] |
| Tenant first-run setup (`/admin/setup`) | [[APP-tenant-onboarding-wizard]] |

**Out of scope**: the backing operations and API ([[INT-tenant-admin-api]], `@nomology/admin-ops` in [[APP-administration-model#design]]); editor internals ([[PKG-forms-and-form-builder]], [[PKG-rules-and-decision-engine]], [[PKG-branding-and-theming]]); platform-level provisioning ([[APP-platform-admin-and-support]]); case operations ([[APP-secretariat-console]]); personal preferences (`/me/settings`, [[PKG-personalisation]]).

<!-- section:routing -->
## Routes, layouts and boundaries

```text
app/(tenant-admin)/admin/
  layout.tsx                 # shell: requireAdminAccess(); scope switcher (tenant | unit); nav built from permitted ops;
                             # global settings search; review-queue badge; @copilot slot
  @copilot/default.tsx       # parallel route: admin copilot side panel (APP-admin-copilot)
  page.tsx                   # overview: setup checklist, configuration health, pending approvals, expiring items
  loading.tsx  error.tsx  not-found.tsx
  setup/                     # first-run checklist (APP-tenant-onboarding-wizard)
  organisation/  profile/  units/  units/[unitId]/  domains/  owners/
  users/  users/invite/  users/invitations/  users/[membershipId]/(profile|access|security|activity)/
  groups/  groups/[groupId]/
  access/  roles/  roles/[roleId]/  permission-sets/  assignments/  reviews/  reviews/[campaignId]/  requests/  explain/
           simulate/  elevate/  break-glass/  walls/  permissions/  matrix/  settings/
  security/  sso/  sso/[connectionId]/  policies/  provisioning/  sessions/  sign-in/  mfa/  recovery/  api/  external-identity/
             support-access/  support-access/[grantId]/  support-access/activity/
  settings/  settings/[domain]/          # generic pages generated from the settings registry
  workflows/ ...                         # WF-workflow-authoring-studio (case-types, automation, sla-policies, calendars, queues);
                                         # rules/ (PKG-rules-and-decision-engine), forms/ (PKG-forms-and-form-builder), fields/ (PKG-metadata-management-entity)
  content/   branding/  branding/preview/  terminology/  document-templates/  legal/  accessibility-statement/
  notifications/  templates/  policies/
  integrations/  connections/  api-clients/  webhooks/  webhooks/[endpointId]/deliveries/  data-policies/
  ai/  policy/  agents/  usage/
  data/  retention/  legal-holds/  exports/  requests/
  billing/  plan/  usage/  invoices/  contacts/
  packages/  packages/[packageId]/  sandboxes/  config/effective/
  personalisation/                       # tenant defaults and shared views (PKG-personalisation)
  changes/  changes/[changeSetId]/  changes/point-in-time/   # change sets: review queue and history (PKG-configuration-lifecycle, APP-admin-change-history)
  audit/                                 # APP-admin-change-history
  bulk/  bulk/new/  bulk/[jobId]/        # APP-bulk-admin-operations
  reports/  reports/[reportId]/
```

- `requireAdminAccess()` replaces `requirePersona('tenant-admin')`: it passes if the membership holds any administrative role at tenant or unit scope, then each page calls `requireOp('<op key>')` for its own operations (layouts do not re-run per navigation, so pages repeat the check).
- **Navigation is generated** from the admin operation registry: a section appears only if the user holds at least one of its ops at the active scope. Hidden sections still return `notFound()` if requested directly.
- **Scope switcher**: a unit-scoped admin chooses the active unit subtree; the choice lives in the URL (`?scope=unit:<id>`) so links are shareable and the server re-checks it.
- **Common page pattern** for versioned configuration (settings, SSO, theme, templates, policies, blueprints): list → draft → validate → diff → preview or test → submit for approval (when maker-checker) → publish → history. The shared `ConfigEditorLayout` renders the draft banner, validation summary, diff tab, history tab and the "who must approve" note.
- `/admin/settings/[domain]` pages are generated from the settings registry ([[PKG-settings-catalogue]]): each field shows the effective value, its source scope ("Platform default", "Locked by Nomology", "Set for this tenant"), lock state, plan restriction and when a change takes effect.

<!-- section:rendering -->
## Rendering and caching strategy

Dynamic, `private, no-store`. Settings and configuration reads use the same tenant-keyed `'use cache: remote'` functions as other groups (keyed by tenant, scope and configuration version); a publish calls `updateTag('tenant:{tenantId}:{area}')` so every group in the region sees the change on the next request. Draft data, approvals, audit and history are never cached. The navigation model (permitted ops per membership) is computed per request from the authorization decision cache, which is invalidated on any `admin.role.*` or `admin.group.*` event for that membership.

<!-- section:data -->
## Data fetching and mutations

All writes go through `@nomology/admin-ops` (`runAdminOp`), whichever surface triggers them ([[APP-administration-model#design]]). Reads use the data access layer in Server Components; interactive tables use tRPC `admin.*` routers generated from the registry ([[APP-internal-api-trpc-routers-per]]).

| Operation group | Kind | Notes |
|---|---|---|
| `admin.user.*`, `admin.role.*`, `admin.group.*` | tRPC mutations | Detail in [[APP-user-and-access-admin]]; multi-select actions above 50 rows become a bulk job |
| `admin.settings.saveDraft` / `submit` / `publish` | Server Actions | Draft per domain and scope; validation through the settings resolver; maker-checker per key |
| `admin.theme.publish` | Server Action | Blocked unless contrast and focus checks pass ([[PKG-tenant-theme-accessibility]]); step-up |
| `admin.terminology.publish` | Server Action | Validates locked strings and locale completeness ([[PKG-tenant-terminology-and-copy]]) |
| `admin.decision_table.publish`, `admin.workflow.publish` | Server Actions | New version only; running cases keep their version ([[WF-workflow-versioning]]) |
| `admin.api_client.create` | Server Action | Console only; secret shown once; step-up ([[PKG-api-clients-and-keys]]) |
| `admin.webhook_endpoint.*` | tRPC | URL validation against SSRF rules ([[APP-webhooks-outbound]]) |
| `admin.support.approve` / `revoke` / `configure` | Server Actions | Step-up; detail in [[PKG-support-access-and-impersonation]] |
| `admin.approval.decide` | Server Action | Approver cannot be the author; shows the full diff being approved |
| `admin.change.rollback` | Server Action | Re-runs the original op's checks; see [[APP-admin-change-history]] |
| `admin.bulk.start` | tRPC mutation | Returns job ID; progress via polling query ([[APP-bulk-admin-operations]]) |
| Copilot proposals | tRPC | Arrive as draft change sets; the human publishes through the normal page ([[APP-admin-copilot]]) |

Every mutation carries an idempotency key generated when the form mounts and the expected version of the object (`If-Match` semantics), so double submits and concurrent edits are safe.

<!-- section:state -->
## Client state and URL state

- URL: list filters, sort, page cursor, selected version, active scope (`?scope=`), active tab, diff "compare with" version.
- Server: all configuration drafts are server-side draft versions, so two admins see the same draft and edits are protected by version numbers; a banner shows "Draft edited by A. Rao 4 minutes ago".
- TanStack Query: tables and polling (bulk job progress, provisioning checklist), keys prefixed with `tenantId` and `scope`.
- Local: unsaved field edits only; leaving a page with unsaved edits asks for confirmation.
- On tenant switch or sign-out all caches are discarded ([[APP-client-state-and-data-fetching]]); the copilot conversation is cleared on tenant switch.

<!-- section:forms -->
## Forms, validation and uploads

Large configuration forms (settings pages, theme, decision tables, policies) validate on the server and return a list of problems with JSON paths, shown as an error summary and inline. Settings forms show, per field, the bound ("Nomology allows 5–60 minutes"), the inherited value and a "Reset to inherited" action. Every publish asks for a reason (free text, 500 characters, required for security, legal-text and AI-policy changes) that is stored in the change set. Decision tables, notification policies and automation rules have a test panel where an admin enters facts and sees the result before publishing. File uploads (logo, CSV imports, configuration packages) use [[PKG-file-upload-dropzone]] and are malware-scanned before use.

<!-- section:errors -->
## Error, loading and empty handling

| Error | Handling |
|---|---|
| Validation failure | Publish blocked; error summary lists each failing rule (for example "Primary button text contrast 3.1:1, needs 4.5:1") with links to fields |
| `VERSION_CONFLICT` | "Someone else changed this draft"; offer reload with a diff of their change |
| `role-escalation-forbidden` | Inline on the role picker: "You can only give roles whose permissions you hold" |
| `approval-required` | Not an error: the change is saved as a request; page shows who can approve |
| `setting-key-locked` | Field shown read-only with the lock source; no edit control rendered |
| `entitlement-limit-reached` | Explains the plan limit and links to billing (for `billing_admin`) or says whom to contact |
| Missing operation permission | `notFound()` for direct URL access (same copy as missing resources) |
| Failed webhook test delivery | HTTP status and timing; response body capped at 1 KB |
| Step-up required | Step-up dialog; the pending action resumes after success |

<!-- section:performance -->
## Performance budgets

Desktop budgets from [[APP-route-groups-per-persona]] (≤ 250 KB gzip first-load JS, LCP ≤ 2.5 s, INP ≤ 200 ms). Editors (theme, decision table, form builder, workflow studio, diff viewer) and the copilot panel are separate chunks loaded on demand. User and audit tables are server-paginated (cursor) and virtualised above 200 rows ([[PKG-data-table]]); a tenant with 500,000 party memberships must list and search users with p95 under 1.5 s.

<!-- section:security -->
## Security headers and browser session

Inherits group defaults: 15 min idle, 8 h absolute (tenant policies may shorten, [[PKG-authentication-policies]]). Step-up (fresh MFA within 5 minutes) for: any administrative role grant, SSO and authentication policy publish, support-access approval or consent change, API client creation, theme and legal-text publish, data export, legal-hold release, rollback of a security change, and bulk jobs above the approval threshold. Admin roles do not carry case-content permissions; pages never render case content (counts only). The theme preview iframe is same-origin with `sandbox="allow-scripts allow-same-origin"`, limited to the preview route, and renders sample data only. Tenant-entered rich text (accessibility statement, notices, banners) is sanitised server-side to an allow-list schema. Contact fields of users outside a unit admin's subtree are masked.

<!-- section:i18n -->
## Localisation hookup

The admin console uses the `admin` message namespace plus `common`. The console UI is available in English at launch, with Hindi planned for Indian tenants; tenant-authored content (terminology, templates, legal texts) is edited per locale with a completeness indicator per locale. Setting labels and help text come from the settings registry and are translated with it. Dates in history and audit show the tenant time zone and UTC on hover.

<!-- section:theming -->
## Tenant theming hookup

The branding editor previews themes in light, dark and high-contrast modes and at 400% zoom before activation. The admin console itself uses the active tenant theme for brand slots only, with a platform fallback if the theme fails to load; destructive and maker-checker controls use locked semantic tokens so tenant colours cannot disguise them. During a support session the support banner uses a fixed platform colour that no tenant theme can override.

<!-- section:observability -->
## Frontend observability

Every server signal carries `route.group=tenant-admin`, `op_key`, `via=console`, `scope_type` and tenant and region attributes ([[OBS-foundations]]). Metrics: op success and error rate by `op_key`, denial rate, validation-failure rate per settings domain, time from draft to publish, approvals pending. Client RUM uses route templates only. No configuration values, names or emails in telemetry.

<!-- section:testing -->
## Testing strategy

- Playwright per persona: each delegated role sees only its sections; a direct URL to another section returns not-found.
- Unit-scope suite: a `unit_admin` sees and changes only memberships in its subtree; tenant-wide settings are absent.
- Lifecycle suite on each versioned area: draft, validate (failing case), diff, approve by a second admin, publish, visible in the portal after publish, rollback.
- Specific: publish a failing theme (blocked), publish a passing theme, publish a decision table version and test it, approve and revoke support access, privileged role grant requiring approval.
- Two-tenant diff test on every publish path and every list page.
- Registry contract test: every page's ops exist in the registry and in the generated catalogue in [[APP-administration-model]].
- axe on every visited state; keyboard-only runs for invite, role assignment, settings publish and approvals.

<!-- section:questions -->
## Open questions

- [ ] Which configuration areas need maker-checker by default per tenant type? Proposed defaults are in [[PKG-separation-of-duties]] and the `PKG-settings-*` catalogues; product to confirm with institution tenants. (owner: product)
- [ ] Should reports be embedded here or in a separate reporting surface ([[RPT-report-infrastructure]])? Proposed: admin reports (seats, adoption, configuration health) here; operational case reports in the reporting surface. (owner: reporting lead)
- [ ] Hindi console UI at launch or later? (owner: product, CORD)
- [ ] Should a `tenant_owner` be able to see a read-only "configuration health score" comparing their settings with blueprint recommendations? (owner: product)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation in rendering and caching

All publishes write tenant-scoped versions and invalidate tenant-scoped tags only. The navigation model and decision cache are keyed by tenant and membership. Theme preview renders synthetic data. Webhook endpoints, API clients, units and invitations are created under the session's tenant only; tenant and scope are never taken from the form (ADM-G5 in [[APP-administration-model#guardrails]]). Two-tenant diff tests run on every list and publish path.

<!-- check:data-exposure -->
### Server boundary and data exposure

Every page and action calls `requireOp` and every mutation goes through `runAdminOp`, which checks the permission at the active scope. Admin roles render no case content. Audit search is limited to the tenant and to roles holding `audit.log:read`; unit admins see only their unit's events. API client secrets are shown once and stored hashed. Contact data outside a unit admin's subtree is masked. Support-access grants show exactly which Nomology staff can see what and until when.

<!-- check:browser-security -->
### Browser security posture

Nonce CSP, `frame-ancestors 'none'`, no third-party scripts. Rich text entered by tenants is sanitised server-side to an allow-list; the preview iframe is restricted to the preview route with synthetic data; webhook URLs are validated against private ranges and metadata endpoints; uploaded CSV and package files are scanned and parsed server-side only, and CSV exports are neutralised against formula injection ([[APP-bulk-admin-operations]]).

<!-- check:session -->
### Sessions in the browser

15 min idle and 8 h absolute, shortened by tenant policy where set; step-up for the security-relevant changes listed in the Security section; Server Actions protected by same-origin checks; sign-out in one tab clears all admin tabs through `BroadcastChannel('session')`.

<!-- check:resilience -->
### Failure, deploys and version skew

Configuration drafts are saved server-side on every field blur, so a lost network or a new release does not lose work. Long operations (bulk jobs, exports, package imports, sandbox refresh) run as jobs and keep running if the admin closes the tab; the overview shows their progress. If the settings resolver or authz service is down, pages show a retry state and no write is attempted (fail closed).

<!-- check:capacity -->
### Rendering cost and capacity

Admin traffic is small relative to case traffic; the heavy parts are user lists for large SEBI ODR tenants and audit search, both server-paginated with indexed filters. Bulk jobs run on BullMQ with per-tenant concurrency limits, so console containers are not tied up.

<!-- check:accessibility -->
### App-level accessibility mechanics

Theme publishing is blocked when contrast or focus checks fail; editors use design-system components; the decision table editor is an accessible grid with row and column headers; diffs are available as a text list, not colour only; the copilot panel is a labelled complementary region that never steals focus.

<!-- check:residency -->
### Region, residency and telemetry privacy

The console, its drafts, approvals, history and bulk files live in the tenant's home region; the copilot calls the in-region AI gateway; telemetry goes to the regional collector.

<!-- end -->
