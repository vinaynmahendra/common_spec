---
id: "INT-tenant-admin-api"
title: "Tenant admin API"
parent: "INT-public-api-and-webhooks"
order: 5
type: "feature"
template: "api"
status: "draft"
owner: null
indicative: false
summary: "REST admin API at /admin/v1 for one tenant: users, groups, roles, units, settings and drafts, branding, keys, bulk jobs, change history and rollback, approvals and audit, generated from the shared admin operation registry"
links: []
rev: 3
syncHash: "720be94fef5b2e4f"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 9.4.5 Tenant admin API

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> REST admin API at /admin/v1 for one tenant: users, groups, roles, units, settings and drafts, branding, keys, bulk jobs, change history and rollback, approvals and audit, generated from the shared admin operation registry

<!-- section:purpose -->
## Purpose, audience and surface

Lets a tenant's IT team automate administration of their own tenant: users, memberships, groups and role assignments; units; settings at tenant, unit and case-type scope; branding; API key rotation; webhook endpoints; configuration drafts and publication; bulk jobs; change history and rollback; approvals; and read their own audit events. Typical uses: an institution provisions secretariat staff from its HR system, rotates API keys on a schedule, promotes a configuration package from sandbox to production, or pulls audit events into its SIEM.

The API is generated from the same admin operation registry as the console, bulk tools and the admin copilot ([[APP-administration-model#design]]), so every operation here has the same permission, validation, maker-checker and audit behaviour as its console equivalent. The full list of admin capabilities, with which ones are exposed here, is the catalogue in [[APP-administration-model]].

Not exposed (console only, with step-up): creating API clients and granting scopes ([[PKG-api-clients-and-keys]]); SSO connection changes and SCIM configuration (lock-out risk); support-access approval and consent ([[PKG-support-access-and-impersonation]]); tenant owner transfer; full tenant data export; legal texts; retention overrides; connector data policies. Not exposed at all: platform-level settings, other tenants, plan changes (contract), break-glass. User provisioning from an identity provider uses SCIM 2.0 at `/scim/v2`, owned by [[PKG-user-provisioning-scim]]; these user endpoints are for systems that are not identity providers.

<!-- section:resources -->
## Resources and identifiers

Base URL: `https://api.{region}.<platform-domain>/admin/v1` (the regional API host of [[INT-public-api-and-webhooks]]). The earlier path `/v1/admin/*` remains as a deprecated alias until the removal date in Versioning.

| Resource | Path | ID prefix |
|---|---|---|
| Tenant profile | `/admin/v1/tenant` | — |
| Units | `/admin/v1/units`, `/admin/v1/units/{unit_id}` | `unt_` |
| Users (memberships) | `/admin/v1/users`, `/admin/v1/users/{user_id}` | `usr_` (membership-scoped) |
| Invitations | `/admin/v1/invitations/{invitation_id}` | `inv_` |
| Role assignments | `/admin/v1/users/{user_id}/roles`, `/admin/v1/groups/{group_id}/roles` | `ras_` |
| Groups | `/admin/v1/groups`, `/admin/v1/groups/{group_id}/members` | `grp_` |
| Roles and permission sets | `/admin/v1/roles`, `/admin/v1/permission-sets` (read) | `rol_`, `pst_` |
| Settings | `/admin/v1/settings`, `/admin/v1/settings/{key}` | key |
| Branding | `/admin/v1/branding` | — |
| API clients and keys | `/admin/v1/api-clients`, `/admin/v1/api-clients/{id}/keys` | `apc_`, `key_` |
| Webhook endpoints | `/admin/v1/webhook-endpoints` (contract in [[APP-webhooks-outbound]]) | `whe_` |
| Bulk jobs | `/admin/v1/bulk-jobs`, `/admin/v1/bulk-jobs/{job_id}`, `/admin/v1/bulk-jobs/{job_id}/results` | `blk_` |
| Change sets (drafts, reviews, history and rollback; [[PKG-configuration-lifecycle]]) | `/admin/v1/change-sets`, `/admin/v1/change-sets/{change_set_id}` | `chg_` (shown to admins as `CS-0042`) |
| Access explainer | `/admin/v1/access/explain` | — |
| Audit events and exports | `/admin/v1/audit-events`, `/admin/v1/audit-exports` | `aud_`, `aex_` |
| Packages and sandboxes | `/admin/v1/packages`, `/admin/v1/sandboxes` | `pkg_`, `sbx_` |

Users are identified within the tenant; the same person in two tenants has one platform identity in a region but separate memberships, and this API sees only the membership in its own tenant ([[MT-tenancy-and-identity-schema]]). Tenants may set `external_ref` (max 100 characters, unique per tenant) on users, groups and units to hold their HR or directory ID.

<!-- section:operations -->
## Operations

Scopes are listed in Authentication. "MC" means the call may return `202` with a change set in `in_review` instead of applying the change.

| Method and path | Summary | Scope | Safe / idempotent | Op key |
|---|---|---|---|---|
| `GET /admin/v1/tenant` | Tenant profile | `admin.org:read` | safe | — |
| `PATCH /admin/v1/tenant` | Update display name and contacts (default language and time zone are settings `locale.languages.default` and `locale.time.default_zone`, [[PKG-settings-branding-content]], changed through `/admin/v1/settings`) | `admin.org:write` | If-Match | `admin.tenant_profile.update` |
| `GET /admin/v1/units` | List units (tree, `parent_id` filter) | `admin.org:read` | safe | — |
| `POST /admin/v1/units` | Create unit | `admin.org:write` | Idempotency-Key | `admin.unit.create` |
| `PATCH /admin/v1/units/{id}` | Rename, archive | `admin.org:write` | If-Match | `admin.unit.update` |
| `POST /admin/v1/units/{id}/actions/move` | Reparent | `admin.org:write` | Idempotency-Key | `admin.unit.move` |
| `POST /admin/v1/users` | Invite user (email or phone, name, roles, units) | `admin.users:write` | Idempotency-Key | `admin.user.invite` |
| `GET /admin/v1/users` | List members (filters below) | `admin.users:read` | safe | — |
| `POST /admin/v1/users/search` | Search by exact email or phone (kept out of URLs) | `admin.users:read` | safe | — |
| `GET /admin/v1/users/{id}` | Get member with roles, groups, units | `admin.users:read` | safe | — |
| `PATCH /admin/v1/users/{id}` | Update units, locale, `external_ref` | `admin.users:write` | If-Match | `admin.user.update` |
| `POST /admin/v1/users/{id}/actions/{suspend,reactivate,end}` | Change membership status; `end` returns open case roles needing reassignment | `admin.users:write` | idempotent | `admin.user.suspend` / `.reactivate` / `.end` |
| `POST /admin/v1/users/{id}/actions/revoke-sessions` | End all sessions | `admin.security:write` | idempotent | `admin.user.revoke_sessions` |
| `POST /admin/v1/invitations/{id}/actions/{resend,revoke}` | Resend or revoke | `admin.users:write` | idempotent | `admin.user.invitation_resend` / `_revoke` |
| `POST /admin/v1/users/{id}/roles` | Assign role at tenant or unit scope | `admin.access:write` | Idempotency-Key; MC for admin roles | `admin.role.assign` |
| `DELETE /admin/v1/users/{id}/roles/{assignment_id}` | Remove role assignment | `admin.access:write` | idempotent | `admin.role.unassign` |
| `GET/POST /admin/v1/groups`, `PATCH /admin/v1/groups/{id}` | Manage groups | `admin.users:read` / `:write` | Idempotency-Key / If-Match | `admin.group.create` / `.update` |
| `POST/DELETE /admin/v1/groups/{id}/members` | Add or remove members (max 1,000 per call) | `admin.users:write` | idempotent | `admin.group.add_member` / `.remove_member` |
| `POST /admin/v1/groups/{id}/roles` | Assign role to group | `admin.access:write` | Idempotency-Key; MC for admin roles | `admin.group.assign_role` |
| `GET /admin/v1/roles`, `GET /admin/v1/permission-sets` | List roles and permission sets with permissions | `admin.access:read` | safe | — |
| `POST /admin/v1/roles`, `PATCH /admin/v1/roles/{id}` | Create or update custom role (creates a draft) | `admin.access:write` | Idempotency-Key / If-Match; MC | `admin.role.define` |
| `POST /admin/v1/access/explain` | Explain why a user can or cannot perform an action on a resource | `admin.access:read` | safe | `admin.access.explain` |
| `GET /admin/v1/settings?domain=&scope=` | Effective settings with source scope and lock state | `admin.settings:read` | safe | — |
| `PATCH /admin/v1/settings/{key}` | Set or clear a value at a scope (creates a draft, or publishes directly where the key allows) | `admin.settings:write` plus the key's own permission | If-Match; MC per key | `admin.settings.publish` |
| `GET/POST /admin/v1/change-sets`, `POST /admin/v1/change-sets/{id}/items`, `GET /admin/v1/change-sets/{id}/diff` | List change sets (filters: state, domain, op, actor, `via`, time), create a draft, add items, view diff | `admin.changes:read` / `:write` | Idempotency-Key | — |
| `POST /admin/v1/change-sets/{id}/actions/{submit,withdraw,rebase,publish}` | Lifecycle transitions ([[PKG-configuration-lifecycle]]) | `admin.changes:write` plus each item's own permission | Idempotency-Key; MC | `admin.settings.publish` |
| `GET /admin/v1/branding`, `PUT /admin/v1/branding/draft` | Read, save draft theme | `admin.branding:read` / `:write` | safe / idempotent | — |
| `POST /admin/v1/branding/draft/actions/activate` | Validate (contrast, focus) and activate | `admin.branding:write` | Idempotency-Key | `admin.theme.publish` |
| `GET /admin/v1/api-clients` | List API clients | `admin.integrations:read` | safe | — |
| `POST /admin/v1/api-clients/{id}/keys` | Create new key for an existing client (rotation); secret shown once | `admin.integrations:write` | Idempotency-Key | `admin.api_client.rotate_key` |
| `DELETE /admin/v1/api-clients/{id}/keys/{key_id}` | Revoke key immediately | `admin.integrations:write` | idempotent | `admin.api_client.revoke_key` |
| `POST /admin/v1/bulk-jobs` | Start bulk job from an uploaded file ID and an op (`users.invite`, `users.update`, `roles.assign`, `groups.members`, `units.create`, `settings.set`) | `admin.bulk:write` plus the row op's scope | Idempotency-Key; long-running (202) | `admin.bulk.start` |
| `GET /admin/v1/bulk-jobs/{id}`, `/results` | Status, counts, per-row results | `admin.bulk:read` | safe | — |
| `POST /admin/v1/bulk-jobs/{id}/actions/{confirm,cancel}` | Confirm after dry-run; cancel remaining rows | `admin.bulk:write` | idempotent | `admin.bulk.start` / `.cancel` |
| `POST /admin/v1/change-sets/{id}/actions/revert` | Roll back a published change set (reversible change sets only); creates a new change set with `origin = revert` | `admin.changes:write` plus original op's scope | Idempotency-Key; MC as original | `admin.change.rollback` |
| `GET /admin/v1/change-sets?state=in_review&awaiting=me`, `POST /admin/v1/change-sets/{id}/actions/{approve,reject}` | List and decide change sets awaiting review (human principals only, not API clients) | `admin.approvals:write` | idempotent | `admin.approval.decide` |
| `GET /admin/v1/audit-events` | Tenant's audit events | `audit:read` | safe | — |
| `POST /admin/v1/audit-exports` | Export audit events (JSONL, signed URL) | `audit:export` | Idempotency-Key; long-running | `admin.audit.export` |
| `GET /admin/v1/packages`, `POST /admin/v1/packages/{id}/actions/{import,promote}` | Configuration packages between sandbox and production | `admin.packages:write` | Idempotency-Key; MC; long-running | `admin.package.import` / `.promote` |

**Approvals cannot be decided by API clients.** A maker-checker change requested through the API becomes a change set in `in_review`; it is approved by a human in the console (or through the API by a human-held OAuth token with `admin.approvals:write`), so a single compromised credential cannot both make and approve a change.

<!-- section:schemas -->
## Request and response schemas

```ts
const ScopeRef = z.discriminatedUnion('type', [
  z.object({ type: z.literal('tenant') }),
  z.object({ type: z.literal('unit'), unit_id: z.string().startsWith('unt_') }),
]);

const UserInvite = z.object({
  email: z.string().email().max(254).optional(),
  phone: z.string().regex(/^\+[1-9]\d{6,14}$/).optional(),   // E.164
  name: z.string().min(1).max(200),
  roles: z.array(z.object({ role: z.string(), scope: ScopeRef })).min(1).max(10),
  unit_ids: z.array(z.string()).max(20).optional(),
  locale: z.string().optional(),
  external_ref: z.string().max(100).optional(),
}).strict().refine(v => !!v.email !== !!v.phone, 'exactly one of email or phone');

const RoleCreate = z.object({
  key: z.string().regex(/^[a-z][a-z0-9_]{2,40}$/), name: z.string().max(100),
  permission_sets: z.array(z.string().startsWith('ps.')).max(50),
  muted_permissions: z.array(z.string()).max(200).optional(),   // see PKG-roles-and-permission-sets
}).strict();

const SettingWrite = z.object({
  scope: z.union([ScopeRef, z.object({ type: z.literal('case_type'), case_type_id: z.string() })]),
  value: z.unknown(),                 // validated against the key's registry schema
  clear: z.boolean().optional(),      // true = revert to inherited
  reason: z.string().max(500).optional(),
}).strict();

const ChangeResult = z.object({
  status: z.enum(['applied', 'approval_required', 'draft_created']),
  change_set_id: z.string().startsWith('chg_'),   // config.change_set; state published, in_review or draft
});

const BulkJobCreate = z.object({
  op: z.enum(['users.invite', 'users.update', 'roles.assign', 'roles.unassign', 'groups.members', 'units.create', 'settings.set']),
  file_id: z.string(),                // uploaded through POST /admin/v1/uploads (signed URL)
  mode: z.enum(['dry_run', 'apply']).default('dry_run'),
  on_error: z.enum(['skip_row', 'stop']).default('skip_row'),
  notify: z.boolean().default(true),  // send invitations for users.invite
}).strict();
```
Write responses return `ChangeResult`. Theme activation runs the checks in [[PKG-tenant-theme-accessibility]]; failures return `422 theme-accessibility-failed` with each failing pair and its measured contrast ratio. Effective setting reads return `{ key, value, source_scope, locked_by?, editable, takes_effect }`.

<!-- section:errors -->
## Error model

RFC 9457 [R1] shared types from [[APP-api-error-catalogue-problem]] plus:

| Problem type | Status | When | Retry | Client action |
|---|---|---|---|---|
| `role-escalation-forbidden` | 403 | Granting a permission or role the caller does not hold, a platform role, or `tenant_owner` | No | Use a principal with sufficient rights |
| `last-owner` / `last-admin` | 409 | Ending, suspending or demoting the last `tenant_owner` or last MFA-enrolled admin | No | Add another owner or admin first |
| `entitlement-limit-reached` | 403 | Seat, custom-role or unit limit of the plan | No | Contact billing admin |
| `setting-key-locked` | 403 | Key locked at a higher scope | No | Show the lock source |
| `setting-out-of-bounds` | 422 | Value outside platform or region bound | No | `invalid_params` lists the bound |
| `setting-scope-not-allowed` | 422 | Key not settable at the requested scope | No | Use an allowed scope |
| `approval-required` | 202 (not an error) | Maker-checker; body is `ChangeResult` | — | Poll the approval |
| `approval-self-decision` | 403 | Approver is the author or the grantee | No | Another human must approve |
| `change-not-reversible` | 409 | Rollback of an irreversible change | No | Make a new forward change |
| `rollback-conflict` | 409 | Object changed since the change being rolled back | No | Review current state; roll back later changes first |
| `bulk-file-invalid` | 422 | Header or encoding errors; per-row errors are in results, not here | No | Fix the file |
| `theme-accessibility-failed` | 422 | Contrast or focus check failed | No | Adjust colours |
| `console-only-operation` | 403 | Operation exists only in the console | No | Use the console |

<!-- section:auth -->
## Authentication, scopes and permissions

Callers authenticate with OAuth 2.0 client credentials or API keys issued to a tenant `service_account` principal ([[PKG-api-clients-and-keys]], [[PKG-non-human-principals]]), or with a human user's OAuth token where an institution's tool acts for a signed-in admin.

| Scope | Grants operations on | Maps to permission sets |
|---|---|---|
| `admin.org:read` / `admin.org:write` | Tenant profile, units | `ps.admin.units`; tenant profile also `tenant:update` (`ps.admin.owner`) |
| `admin.users:read` / `admin.users:write` | Users, invitations, groups | `ps.admin.users` |
| `admin.access:read` / `admin.access:write` | Roles, assignments, explainer | `ps.admin.roles`, `ps.admin.users` (`role:assign`), `ps.admin.access_governance` |
| `admin.security:write` | Session revocation | `ps.admin.security` |
| `admin.settings:read` / `admin.settings:write` | Settings | the `ps.admin.*` set that holds each catalogue's `settings.<catalogue>:write` ([[PKG-settings-catalogue#design]]) |
| `admin.branding:read` / `admin.branding:write` | Branding | `ps.admin.content` |
| `admin.integrations:read` / `admin.integrations:write` | API keys, webhook endpoints | `ps.admin.integrations` |
| `admin.bulk:read` / `admin.bulk:write` | Bulk jobs | — (plus row-op scope) |
| `admin.changes:read` / `admin.changes:write` | Change sets: drafts, history, rollback | — (plus original op's scope) |
| `admin.approvals:write` | Approve or reject change sets in review (human tokens only) | — |
| `admin.packages:write` | Packages, sandboxes | `ps.admin.config_lifecycle` |
| `audit:read` / `audit:export` | Audit events | `ps.admin.audit_read` |

The effective right of a call is the **intersection** of the credential's scopes and the permissions held by its principal at the target scope; a service account may itself be limited to a unit scope. Admin scopes are requested by an `integration_admin` and approved in the console, with step-up, by a `security_admin` or `tenant_owner` who is not the requester (`api_client:approve`, [[PKG-api-clients-and-keys]]); they are flagged "high privilege". A client can never grant permissions it does not hold (no escalation). Admin API clients appear in the tenant's access reviews ([[SEC-access-reviews]]).

<!-- section:tenancy -->
## Tenancy and region routing

The tenant is taken only from the credential (API key or OAuth token), which is bound to one tenant and one region ([[INT-public-api-and-webhooks#auth]]). The auth middleware opens the request transaction and sets `app.tenant_id` through the Prisma extension ([[MT-prisma-client-extension-wraps]]); forced RLS ([[MT-rls-enabled-and-forced-on]]) is the final layer under the object-level policy checks. No path, query or body field can select a tenant; `tenant_id` is not accepted in any write schema (`additionalProperties: false`). Unit scope references are checked to belong to the credential's tenant. A credential used against another region's base URL gets `421` problem `wrong-region`. A suspended tenant gets read access and the protected due-process actions only; other writes return `403` problem `tenant-suspended-readonly`. Unknown and forbidden IDs both return the same `404 not-found`. Inviting an email that already has an identity creates a membership; the response never reveals whether the person exists in another tenant.

<!-- section:pagination -->
## Pagination, filtering and sorting

Cursor pagination (`limit` 1–200, default 50). Users filterable by `role`, `status`, `unit_id`, `group_id`, `external_ref`, `updated_after`; exact email or phone search only through `POST /admin/v1/users/search`, to keep personal data out of URLs. Audit events by `actor_id`, `action`, `target_type`, `via`, `occurred_after` with a 31-day maximum range per request. Change sets by `domain`, `op_key`, `actor_id`, `via`, `occurred_after`. Every filter maps to an index on `(tenant_id, …)`.

<!-- section:idempotency -->
## Idempotency, concurrency and long-running operations

Invitations, role assignments, role and group creation, key creation, theme activation, draft transitions, bulk jobs, rollbacks and exports require `Idempotency-Key` (kept 24 hours; replay returns the original response). Edits use ETag / `If-Match` [R3]; a stale ETag returns `412`. Bulk jobs, audit exports and package imports return `202` with a `Location` to the job resource; jobs are resumable and each row is applied exactly once using `job_id + row_number` as the row idempotency key.

<!-- section:events -->
## Webhooks and events

Tenants may subscribe their webhook endpoints ([[APP-webhooks-outbound]], catalogue in [[INT-webhook-event-catalogue]]) to admin events: `membership.created`, `membership.status_changed`, `role_assignment.created`, `role_assignment.removed`, `config.published`, `approval.requested`, `bulk_job.completed`, `support_grant.approved`, `support_grant.ended`. Payloads carry IDs, op key, `via`, actor ID and change ID; no names or emails. The full audit trail stays available through `GET /admin/v1/audit-events`.

<!-- section:limits -->
## Rate limits and quotas

Writes 60 per minute per client; reads 600 per minute per client; audit event reads count as expensive (10 per minute); one running audit export and two running bulk jobs per tenant (`platform.bulk.max_concurrent_jobs_per_tenant`). Plan entitlements can raise read limits but not the write limit. Responses carry `RateLimit` and `RateLimit-Policy` headers as in [[APP-api-versioning-rate-limiting]]; `429` includes `Retry-After`.

<!-- section:versioning -->
## Versioning, compatibility and deprecation

As for the other families ([[APP-api-versioning-rate-limiting]]). The path moves from `/v1/admin/*` to `/admin/v1/*` to match the shared naming; the old path is an alias that returns `Deprecation` and `Sunset` headers and is removed no earlier than 12 months after the new path ships, with email notice to tenant admins and integration admins. Settings keys are versioned by their registry schema ([[PKG-settings-catalogue]]); renamed keys keep an alias for two releases.

<!-- section:examples -->
## Worked examples

**1. HR system provisions a registry clerk at unit scope**

```http
POST /admin/v1/users
Authorization: Bearer <token for service account hr-sync (scopes admin.users:write admin.access:write)>
Idempotency-Key: 6f1c…
Content-Type: application/json

{ "email": "clerk@institution.example", "name": "R. Menon",
  "roles": [{ "role": "secretariat", "scope": { "type": "unit", "unit_id": "unt_01J…" } }],
  "external_ref": "HR-20441" }
```
`201` with `ChangeResult { status: "applied", change_set_id: "chg_…" }` and the user resource.

**2. Granting an admin role needs approval**

`POST /admin/v1/users/usr_…/roles` with `{ "role": "security_admin", "scope": { "type": "tenant" } }` returns `202` with `{ "status": "approval_required", "change_set_id": "chg_…" }`. A second human admin approves the change set in `/admin/changes?state=in_review`; the webhook `role_assignment.created` follows.

**3. Failure and recovery: rollback conflict**

`POST /admin/v1/change-sets/chg_A/actions/revert` returns `409 rollback-conflict` because `chg_B` later changed the same setting. The client lists `GET /admin/v1/change-sets?object=auth.session.idle_timeout_min`, rolls back `chg_B` first, then `chg_A`.

<!-- section:questions -->
## Open questions

- [ ] Should SSO configuration ever be manageable through the API? Proposed: console only in v1 (lock-out risk). (owner: identity group, [[PKG-sso-saml-oidc-per-tenant]])
- [x] SCIM 2.0 for user provisioning: yes, at `/scim/v2`, owned by [[PKG-user-provisioning-scim]]; these endpoints remain for non-IdP systems.
- [ ] Is creating API clients through the API ever needed (for example for an institution's automation platform)? Proposed: no. (owner: security)
- [ ] Should human-held OAuth tokens be allowed to decide approvals through the API, or only the console? (owner: security, with [[PKG-separation-of-duties]])

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Object-level authorization and tenant isolation

Memberships, roles, groups, units, settings, drafts, change sets and branding are tenant-owned with forced RLS; tenant comes only from the credential; unit references are checked to belong to the tenant; invitations never reveal other tenants' memberships; unknown and forbidden IDs return the same 404.

<!-- check:security -->
### Attack surface and abuse resistance

Highest-risk operations (creating clients, granting scopes, SSO, support access, owner transfer, data export) stay in the console with MFA step-up; effective rights are scope ∩ principal permissions; the API cannot escalate privileges (`role-escalation-forbidden`), cannot remove the last owner, and cannot both make and approve a maker-checker change. Mapped to OWASP API1 (object level) and API5 (function level authorisation) [R2]. Input limits: 1,000 group members per call, bulk files up to `platform.bulk.max_rows_per_file`.

<!-- check:compatibility -->
### Contract governance and breaking changes

Operations, schemas and scopes are generated from the admin operation registry, so the OpenAPI file and the running code share one source; contract tests compare the published OpenAPI with the registry in CI; the `/v1/admin` alias keeps old clients working for at least 12 months.

<!-- check:reliability -->
### Retry safety and consistency

Idempotency keys on every create and action, ETags on edits, row-level idempotency in bulk jobs, and change sets in review that publish exactly once on approval mean retries never double-invite, double-grant or double-publish.

<!-- check:privacy -->
### Personal data and residency in the contract

Emails and phone numbers are never in URLs (search by POST); responses include contact data only for scopes with `admin.users:read`; webhook payloads carry IDs only; audit and change records store hashes of personal values.

<!-- check:audit -->
### Attribution and legal evidence

Every write is an admin op recorded with op key, client ID, service-account principal or human principal, `via=api`, request ID, idempotency key and change set ID; tenants read their own events through `GET /admin/v1/audit-events` and change history through `GET /admin/v1/change-sets`.

<!-- check:operability -->
### Service levels, capacity and observability

Targets: p95 under 400 ms for reads and 800 ms for writes per region; bulk throughput 50 rows per second per job. Per-client and per-tenant dashboards show rate-limit hits, error types and latency.

<!-- check:consumability -->
### Developer experience and onboarding

The developer portal documents every operation with examples, the scopes table and the sandbox; a tenant sandbox ([[PKG-configuration-packages]]) lets institutions test provisioning scripts without touching production.

<!-- citations -->
## Citations

```json
[
  {
    "body": "IETF",
    "excerpt": "Defines the application/problem+json object with type, title, status, detail and instance members.",
    "id": "R1",
    "ident": "RFC 9457",
    "kind": "standard",
    "title": "Problem Details for HTTP APIs",
    "url": "https://datatracker.ietf.org/doc/html/rfc9457"
  },
  {
    "body": "OWASP",
    "excerpt": "Top API risks, led by Broken Object Level Authorization (API1) and Broken Authentication (API2).",
    "id": "R2",
    "ident": "OWASP API Security Top 10",
    "kind": "standard",
    "title": "OWASP API Security Top 10 (2023)",
    "url": "https://owasp.org/API-Security/editions/2023/en/0x11-t10/",
    "version": "2023"
  },
  {
    "body": "IETF",
    "excerpt": "Conditional requests with ETag and If-Match; 412 Precondition Failed.",
    "id": "R3",
    "ident": "RFC 9110",
    "kind": "standard",
    "title": "HTTP Semantics",
    "url": "https://www.rfc-editor.org/rfc/rfc9110"
  }
]
```

<!-- end -->
