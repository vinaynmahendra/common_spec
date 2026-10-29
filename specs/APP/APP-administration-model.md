---
id: "APP-administration-model"
title: "Administration model and admin personas"
parent: "APP-route-groups-per-persona"
order: 8
type: "feature"
template: "design"
status: "draft"
owner: null
indicative: false
summary: "Admin planes (platform, tenant, unit, self), admin personas and delegated roles, scoped role assignment, the shared admin operation registry and the full admin capability catalogue (function × persona × scope × page × API × audit event)"
links: []
rev: 1
syncHash: "6c8df94963697f91"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 2.1.2.8 Administration model and admin personas

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Admin planes (platform, tenant, unit, self), admin personas and delegated roles, scoped role assignment, the shared admin operation registry and the full admin capability catalogue (function × persona × scope × page × API × audit event)

<!-- section:context -->
## Context and scope

The platform serves several kinds of administrator, at different levels, through different surfaces:

- **Nomology staff** run the platform per region: they create and provision tenants, set platform and regional bounds, operate workflows and queues, and help tenants under controlled support access. Today this is described in [[APP-platform-admin-and-support]] and [[MT-tenant-lifecycle]].
- **Tenant administrators** at an institution (an arbitral institution, a SEBI ODR institution, a CORD tenant, a court or government programme) manage their own users, access, security, configuration, content, integrations, AI use, data and billing contacts. Today this is described in [[APP-tenant-admin-console]] and the API in [[INT-tenant-admin-api]].
- **Unit administrators** run part of a tenant (an office, a panel, a programme or a desk such as "SEBI ODR desk") and need a subset of tenant powers limited to their unit.
- **Every user** manages their own preferences ([[PKG-personalisation]], [[PKG-settings-personal]]).

Before this note, each console and API listed its own operations, with different role names (for example `case_manager`, `finance_officer`, `support_engineer`) and no single list of what an administrator can do, at which scope, through which page and API, and with which audit event. The overhaul introduces shared vocabulary (scopes, role keys, permission naming, configuration lifecycle) in the shared model, and new owner nodes for permissions ([[PKG-permission-catalogue]]), roles ([[PKG-roles-and-permission-sets]]), separation of duties ([[PKG-separation-of-duties]]), elevation ([[PKG-jit-and-break-glass]]), configuration scopes ([[PKG-configuration-scope-hierarchy]]) and lifecycle ([[PKG-configuration-lifecycle]]).

This note is the **administration model**: the admin planes, the admin personas and what each may do, how admin scope is assigned, the admin operation registry that every console, bulk tool, API and the admin copilot share, and the **admin capability catalogue** (every admin function × persona × scope × console page × API × audit event). It is the parent reference for the admin nodes:

| Node | Owns |
|---|---|
| [[APP-tenant-admin-console]] | `/admin` route group: information architecture, shell, shared patterns |
| [[APP-user-and-access-admin]] | Users, invitations, groups, role assignment, access reviews and requests |
| [[APP-admin-change-history]] | Audit log search, change history, diffs and rollback |
| [[APP-bulk-admin-operations]] | Bulk import, update and export |
| [[APP-platform-admin-and-support]] | `/platform` route group for Nomology staff |
| [[APP-tenant-onboarding-wizard]] | Tenant provisioning wizard and tenant first-run setup |
| [[PKG-support-access-and-impersonation]] | Consent-based support access and "view as" |
| [[INT-tenant-admin-api]] | `/admin/v1` REST API |
| [[PKG-settings-platform-operations]] | Platform operations settings catalogue |
| [[APP-admin-copilot]] | AI assistant over the same operations (AI group) |

<!-- section:goals -->
## Goals and non-goals

**Goals**

1. One list of every administrative capability on the platform, each with a stable operation key, permission, allowed scopes, default personas, console page, API route and audit event. Reviewers, testers, auditors and the admin copilot all read the same list.
2. Delegated administration: a tenant can give a person exactly one area (users, security, workflow, content, integrations, billing, AI, audit) and, where useful, only one unit, without giving them full tenant admin.
3. No path to privilege escalation: nobody can grant a permission they do not hold, create platform roles, or give themselves case content through an admin role.
4. "Admins administer, they do not read case files": administrative roles carry no case content permissions by default ([[PKG-authorization#policy]]).
5. One operation, many surfaces: console pages, bulk jobs, the admin API, the platform console and the admin copilot call the same typed operation, so checks, validation and audit cannot drift (shared model AI principle 1).
6. Every administrative change is attributable (actor, on-behalf-of, surface, reason), visible to the tenant, and either reversible or explicitly marked irreversible with a stronger confirmation.
7. Nomology staff have no standing access to tenant data; support access needs tenant consent ([[PKG-support-access-and-impersonation]]).

**Non-goals**

- Defining the permission catalogue itself (owned by [[PKG-permission-catalogue]]) or the authorization data model ([[PKG-authorization-data-model]]). This note uses their names.
- Defining each settings catalogue. Settings are listed in the `PKG-settings-*` nodes; this note lists only the operations that change them.
- Case-level administration by the secretariat (assigning neutrals, extending deadlines). That is operational work in [[APP-secretariat-console]], governed by case-level roles in [[PKG-rbac-abac-case-level-party]].
- A global (cross-region) admin console. Each region has its own platform console ([[MT-data-residency-2]]).

<!-- section:design -->
## Design

### 1. Admin planes

| Plane | Who | Surface | Host | Identity | Data reach |
|---|---|---|---|---|---|
| Platform | Nomology staff (`platform_owner`, `platform_admin`, `platform_support`, `platform_security`, `platform_billing`, `regional_ops`) | `/platform/*` ([[APP-platform-admin-and-support]]), `/platform/v1` internal API | Platform-admin host per region, zero-trust network only | Workforce IdP, phishing-resistant MFA | Platform-level tables of that region; tenant data only through a support grant on the tenant host |
| Tenant | Tenant administrative roles | `/admin/*` ([[APP-tenant-admin-console]]), `/admin/v1` API ([[INT-tenant-admin-api]]) | Tenant host | Tenant sign-in policy ([[PKG-authentication-policies]]) | That tenant, under forced RLS |
| Unit | `unit_admin`, or any delegated admin role assigned at unit scope | Same `/admin/*` pages, filtered to the assigned units | Tenant host | As tenant | Memberships, queues and settings of the assigned unit subtree |
| Self | Every user | `/me/settings/*` personal pages ([[PKG-personalisation]]) | Tenant host | As tenant | Own preferences only |

The platform and tenant planes never share a session, a cookie, a host or a route group. A Nomology employee who is also, for testing, a member of a demo tenant uses a separate tenant identity.

### 2. Admin personas (role keys from the shared model)

| Role key | Plane | Purpose | Assignable scopes | May assign | Case content | Step-up | Holds by default (permission sets, see [[PKG-roles-and-permission-sets]]) |
|---|---|---|---|---|---|---|---|
| `platform_owner` | Platform | Accountable executive; approves platform bounds, region opening, tenant deletion | platform | Platform roles (through workforce IdP groups) | Never | Always | `ps.platform.owner` |
| `platform_admin` | Platform | Tenant lifecycle, blueprints, platform and offering settings, flags | platform, region, offering | — | Never (support grant only) | High-impact actions | `ps.platform.tenant_ops`, `ps.platform.settings` |
| `regional_ops` | Platform | One region's operations: maintenance, banners, workflow and queue operations, region settings | region | — | Never | High-impact actions | `ps.platform.region_ops` |
| `platform_support` (tier 1, tier 2) | Platform | Tickets; requests support grants; "view as" | platform (grants are per tenant) | — | Only under an approved grant | Every grant use | `ps.platform.support_t1` / `_t2` |
| `platform_security` | Platform | Break-glass approval, platform audit, security investigations | platform, region | — | Under break-glass only | Always | `ps.platform.security` |
| `platform_billing` | Platform | Plans, entitlements, billing accounts | platform | — | Never | Plan changes | `ps.platform.billing` |
| `tenant_owner` | Tenant | Accountable person at the institution; owns ownership transfer, tenant export, support consent, admin role grants | tenant | Every tenant role | No (unless also holding an operational role) | Always for owner actions | all `ps.admin.*` + `ps.admin.owner` |
| `tenant_admin` | Tenant | General administration across all areas except owner-only actions | tenant | Any tenant role except `tenant_owner` and `security_admin`; roles with a `priv` permission need a checker | No | Privileged actions | `ps.admin.users`, `ps.admin.roles`, `ps.admin.units`, `ps.admin.workflow`, `ps.admin.integrations`, `ps.admin.content`, `ps.admin.config_lifecycle`, `ps.admin.access_governance`, `ps.admin.ai`, `ps.admin.settings_read`, `settings.data:write` |
| `security_admin` | Tenant | SSO, authentication policies, sessions, support access, custom roles, access reviews, connector data policies | tenant | `security_admin` (checker: `tenant_owner`), `auditor`, `privacy_officer` | No | Always | `ps.admin.security`, `ps.admin.roles`, `ps.admin.access_governance`, `ps.admin.data`, `ps.admin.audit_read`, `ps.admin.settings_read` |
| `user_admin` | Tenant | Invite, suspend, end memberships; assign non-administrative roles; groups | tenant, unit | Non-privileged roles: operational roles (`secretariat`, `neutral`, `transcriber`, `counsel`, `party`, `observer`), `content_admin`, `user_admin`, `unit_admin`, managed templates without `priv` permissions, and custom roles whose permissions it holds | No | Bulk over threshold | `ps.admin.users`, `ps.admin.access_requests` |
| `workflow_designer` | Tenant | Case-type blueprints, decision tables, forms, custom fields, automations, business schedules and SLA policies | tenant, case_type; unit for business calendars and queues only | — | No (simulation uses synthetic data, [[WF-workflow-simulation]]) | Publish | `ps.admin.workflow`, `ps.admin.settings_read` |
| `integration_admin` | Tenant | Connections, API clients, webhooks | tenant | — | No | Key creation | `ps.admin.integrations`, `ps.admin.settings_read` |
| `content_admin` | Tenant | Branding, terminology, document and notification templates, legal texts (draft) | tenant, unit, case_type | — | No | Publish of legal texts | `ps.admin.content`, `ps.admin.settings_read` |
| `billing_admin` | Tenant | Plan and usage view, invoices, billing contacts, plan change requests | tenant | — | No | — | `ps.admin.billing` |
| `ai_admin` | Tenant | Tenant AI policy, assistants and agents, AI usage ([[AI-tenant-ai-policy]]) | tenant | — | No | Policy publish | `ps.admin.ai`, `ps.admin.settings_read` |
| `auditor` | Tenant | Read-only across admin configuration plus audit log and change history | tenant, unit | — | No | Export | `ps.admin.audit_read`, `ps.admin.settings_read` |
| `unit_admin` | Unit | User administration and unit settings for one unit subtree | unit | Non-privileged roles within the unit subtree | No | Bulk over threshold | `ps.admin.users`, `ps.admin.units`, `ps.admin.unit_settings`, `ps.admin.settings_read` |

Rules for personas:

- **ADM-R1** Administrative roles carry no case-content permission. A person who needs both (for example a registrar who is also tenant admin) holds `secretariat` as well, and both assignments are visible in access reviews.
- **ADM-R2** An admin may only grant permissions they hold (decision D6; rule ROLE-FR-3 in [[PKG-roles-and-permission-sets#requirements]]): custom roles and permission sets can contain, and be assigned by someone holding, only permissions the admin holds at that scope; system roles and managed templates can be assigned only by the roles in the "May assign" column. There is no `tenant_owner` exception. `tenant_owner` may be granted only by a `tenant_owner`. Platform roles are never assignable in a tenant.
- **ADM-R3** A tenant always has at least one active `tenant_owner` and at least one active `tenant_admin` or `tenant_owner` with MFA enrolled (extends TM-R6 in [[MT-tenant-model#rules]]). The console warns while there is only one owner.
- **ADM-R4** Assigning any role that contains a `priv` permission (`role.privileged:assign`; for example `tenant_owner`, `tenant_admin`, `security_admin`, `workflow_designer`, `integration_admin`, `ai_admin`) is maker-checker: a second admin who is not the requester and not the grantee approves the change set ([[PKG-separation-of-duties]], ROLE-FR-6).
- **ADM-R5** Nomology staff are never members of a customer tenant; they reach tenant data only through a support grant.
- **ADM-R6** Roles are additive. Where a tenant needs "everything in `tenant_admin` except billing", it creates a custom role from permission sets rather than using denials; muting (removing permissions from a set inside a custom role) is supported by [[PKG-roles-and-permission-sets]].
- **ADM-R7** Tenant admins never impersonate their own users. To check what someone can see or do, they use the permission simulator and access explainer ([[PKG-access-explainer]]); "view as" exists only for Nomology support under a tenant-approved grant ([[PKG-support-access-and-impersonation]]) (decision D6).
- **ADM-R8** Administrative roles can be held only by memberships with `membership.kind = staff`; `external` memberships (parties, counsel, external neutrals) hold only operational and case-level roles. Settings catalogues use the persona alias `staff_admin` for "any tenant administrative role" (decision D6).
- **ADM-R9** Roles may be assigned to groups as well as to individual memberships; the group's current members hold the role ([[PKG-roles-and-permission-sets]]). Managed role templates (`secretariat_lead`, `case_finance_officer`, `reporting_viewer`, `regulatory_reporter`, `regulatory_approver`, `privacy_officer`) are maintained by Nomology; tenants assign or clone them but cannot edit them in place.

### 3. Admin scope assignment

A role assignment is `(principal, role, scope)` where scope is `tenant` or a list of `unit` IDs (each covering its subtree). Pattern borrowed from: custom admin roles with resource sets in Okta [R1] and administrative units in Microsoft Entra ID [R2].

| Scope | What a unit-scoped admin can touch | What it cannot touch |
|---|---|---|
| `unit` (subtree) | Memberships whose primary unit is in the subtree; invitations into those units; unit settings marked unit-overridable (for example the unit business schedule, unit queue routing); unit reports | Tenant-wide settings, SSO, roles and permission sets, integrations, AI policy, billing, users outside the subtree, moving a membership out of the subtree |

- A membership with units in two subtrees can be changed by a unit admin only for the attributes inside that admin's subtree; changing tenant-level attributes (status, tenant roles) needs a tenant-scoped admin.
- Unit moves (reparenting) need a tenant-scoped admin, because they change who administers whom.
- Settings scopes follow [[PKG-configuration-scope-hierarchy]]; the admin scope determines **who** may set a value at `unit` scope.

### 4. Admin operation registry

Every administrative capability is declared once in `packages/admin-ops` (`@nomology/admin-ops`) and executed through one dispatcher:

```ts
// packages/admin-ops/src/define.ts (server-only)
export const inviteUser = defineAdminOp({
  key: 'admin.user.invite',                 // stable operation key
  plane: 'tenant',
  permission: 'user:create',                // from PKG-permission-catalogue
  scopes: ['tenant', 'unit'],               // where it may be granted and executed
  input: UserInviteInput,                   // Zod; generates OpenAPI and the bulk column map
  change: 'direct',                         // 'direct' | 'versioned' (config lifecycle) | 'workflow' (Temporal)
  reversible: { by: 'admin.user.invitation_revoke' },
  controls: { stepUp: false, makerChecker: 'when:privilegedRole', bulk: true, copilot: 'propose' },
  audit: 'admin.user.invited',
  surfaces: { console: '/admin/users/invite', api: 'POST /admin/v1/users', bulk: 'users.invite' },
  handler: async (ctx, input) => { /* domain service call inside withTenant() */ },
});
```

The dispatcher `runAdminOp(ctx, op, input, { via, reason, idempotencyKey, changeSetId })`:

1. Resolves the principal and its effective admin scope; checks `permission` at the target scope through `@nomology/authz` (with ADM-R2 for role grants).
2. Validates the input with the shared Zod schema and runs cross-object rules (last owner, seat limit, setting bounds).
3. Applies controls: step-up freshness, maker-checker (creates a change set in `in_review` instead of executing; [[PKG-configuration-lifecycle]]), plan entitlement ([[BIL-plans-entitlements-and-usage]]).
4. Executes inside `withTenant()` for tenant ops, or platform context for platform ops; writes `audit.record()` in the same transaction ([[PKG-audit-trail]]) and appends to the change set used by [[APP-admin-change-history]].
5. Emits the outbox event (`admin.*`) used by notifications to other admins, webhooks where subscribed, and the SIEM feed for security-category events ([[OBS-security-events]]).

`via` is one of `console`, `api`, `bulk`, `copilot`, `support` (Nomology staff, including platform-console changes to tenant values), `scim`, `system` (decision D3). The registry generates: the tRPC admin routers ([[APP-internal-api-trpc-routers-per]]), the `/admin/v1` OpenAPI operations, bulk column maps ([[APP-bulk-admin-operations]]), the copilot tool list ([[APP-admin-copilot]]), the console navigation (a page is shown only if the user holds at least one of its ops), and the catalogue table below (CI fails if they differ).

### 5. Change classes

| Class | Examples | How it changes | How it is undone |
|---|---|---|---|
| `versioned` | Settings, SSO connection, auth policy, theme, terminology, templates, blueprints, decision tables, automation rules, AI policy, connector data policies | [[PKG-configuration-lifecycle]]: draft → in_review → approved → published | Publish an earlier version (audited) |
| `direct` | Invite, suspend, assign role, add group member, rotate key, approve support grant | Immediate, single transaction | Inverse operation, re-checked as a new change (for example "remove role" for "assign role") |
| `workflow` | Provision tenant, suspend tenant, offboard, tenant data export, bulk job | Temporal workflow or BullMQ job with progress | Compensation defined per workflow; some steps irreversible (deletion, sent invitations) |
| `irreversible` | Tenant deletion approval, crypto-shred, legal-hold release, revealing a secret | Typed confirmation, step-up, usually maker-checker | Not undoable; the console says so before confirming |

### 6. Admin capability catalogue

Legend: **Ctl** = controls: `S` step-up, `MC` maker-checker, `V` versioned lifecycle, `W` workflow or job, `IR` irreversible, `B` available in bulk, `CP` admin copilot may propose a draft, `CX` copilot may execute after confirmation (read-only or low-risk direct ops only). Personas list the default holders; custom roles may also hold the permission. APIs prefixed `/platform/v1` are internal only.

#### 6.1 Platform plane: tenants and lifecycle

| Function | Op key | Permission | Default personas | Scopes | Console page | API | Audit event | Ctl |
|---|---|---|---|---|---|---|---|---|
| Create tenant draft | `platform.tenant.create` | `platform.tenant:create` | platform_admin, regional_ops | region | `/platform/tenants/new` | `POST /platform/v1/tenants` | `admin.tenant.created` | S |
| Provision tenant from blueprint | `platform.tenant.provision` | `platform.tenant:create` | platform_admin | region | `/platform/tenants/new` (wizard, [[APP-tenant-onboarding-wizard]]) | `POST /platform/v1/tenants/{id}/actions/provision` | `admin.tenant.provisioning_started`, `admin.tenant.provisioned` | S, W |
| Retry or abandon failed provisioning | `platform.tenant.provision_resolve` | `platform.tenant:update` | platform_admin | region | `/platform/tenants/{id}/lifecycle` | `POST /platform/v1/tenants/{id}/actions/{retry,abandon}` | `admin.tenant.provisioning_resolved` | S, W |
| Suspend / reinstate tenant | `platform.tenant.suspend`, `.reinstate` | `platform.tenant:update` | platform_admin, platform_billing (non-payment), platform_security (security) | region | `/platform/tenants/{id}/lifecycle` | `POST /platform/v1/tenants/{id}/actions/{suspend,reinstate}` | `admin.tenant.suspended`, `admin.tenant.reinstated` | S, W |
| Start offboarding | `platform.tenant.offboard` | `platform.tenant:delete` | platform_admin | region | `/platform/tenants/{id}/lifecycle` | `POST /platform/v1/tenants/{id}/actions/offboard` | `admin.tenant.offboarding_started` | S, MC, W |
| Approve deletion after export | `platform.tenant.approve_deletion` | `platform.tenant:approve` | platform_owner (with DPO sign-off) | region | `/platform/tenants/{id}/lifecycle` | `POST /platform/v1/tenants/{id}/actions/approve-deletion` | `admin.tenant.deletion_approved` | S, MC, IR |
| Request region move | `platform.tenant.region_move` | `platform.tenant:approve` | platform_owner | platform | `/platform/tenants/{id}/region` | `POST /platform/v1/tenants/{id}/actions/region-move` | `admin.tenant.region_move_requested` | S, MC, W |
| Change plan and entitlements | `platform.tenant.set_plan` | `platform.plan:update` | platform_billing | platform | `/platform/tenants/{id}/plan` | `PUT /platform/v1/tenants/{id}/plan` | `admin.billing.plan_changed` | S |
| Verify or override custom domain | `platform.tenant.domain_override` | `platform.tenant:update` | platform_admin | region | `/platform/tenants/{id}/domains` | `POST /platform/v1/tenants/{id}/domains/{d}/actions/verify` | `admin.domain.verified` | S |
| Publish tenant blueprint | `platform.blueprint.publish` | `platform.blueprint:publish` | platform_admin | platform, offering | `/platform/blueprints` | `POST /platform/v1/blueprints/{id}/versions/{v}/actions/publish` | `admin.blueprint.published` | V, MC |

#### 6.2 Platform plane: settings, operations and support

| Function | Op key | Permission | Default personas | Scopes | Console page | API | Audit event | Ctl |
|---|---|---|---|---|---|---|---|---|
| Set platform defaults and hard bounds | `platform.settings.publish` | `settings.platform:write` | platform_admin (author), platform_owner (approver) | platform | `/platform/settings/{domain}` | `PATCH /platform/v1/settings/{key}` | `admin.settings.published` | V, MC |
| Set region defaults and bounds | `platform.settings.publish` | `settings.platform:write` | regional_ops | region | `/platform/regions/{region}/settings` | same, `scope=region` | `admin.settings.published` | V, MC |
| Set offering defaults | `platform.settings.publish` | `settings.platform:write` | platform_admin | offering | `/platform/offerings/{offering}/settings` | same, `scope=offering` | `admin.settings.published` | V |
| Release flags per tenant | `platform.flag.set` | `platform.feature_flag:update` | platform_admin | platform, region, tenant | `/platform/flags` | `PUT /platform/v1/flags/{flag}/targets` | `admin.flag.changed` | S |
| Maintenance windows | `platform.maintenance.schedule` | `platform.operations:configure` | regional_ops | region | `/platform/operations/maintenance` | `POST /platform/v1/maintenance-windows` | `admin.maintenance.scheduled` | — |
| Platform and tenant banners | `platform.banner.publish` | `platform.operations:configure` | regional_ops, platform_admin | platform, region, tenant | `/platform/operations/banners` | `POST /platform/v1/banners` | `admin.banner.published` | — |
| Workflow and job operations (retry, cancel, terminate, replay DLQ) | `platform.workflow.operate` | `platform.workflow:update` | regional_ops | region | `/platform/operations/workflows`, `/platform/operations/jobs` | `POST /platform/v1/workflows/{id}/actions/{action}` | `admin.workflow.operator_action` | S |
| Request support access | `platform.support.request` | `platform.support_grant:create` | platform_support | per tenant | `/platform/support/requests/new` | `POST /platform/v1/support-requests` | `admin.support.requested` | — |
| Start "view as" or support session | `platform.support.start_session` | `user:impersonate` (under grant) | platform_support (requester only) | per tenant | `/platform/support/requests/{id}` → tenant host | `POST /platform/v1/support-grants/{id}/sessions` | `admin.support.session_started` | S |
| Break-glass into a tenant | `platform.break_glass.request`, `.approve` | `platform.support_grant:approve` | platform_security (approver), regional_ops (requester) | per tenant | `/platform/break-glass` | `POST /platform/v1/break-glass` | `admin.break_glass.granted` | S, MC ([[PKG-jit-and-break-glass]]) |
| Platform staff roles | `platform.staff.assign_role` | `platform.staff_role:assign` | platform_owner | platform | `/platform/staff` (read-only mirror of workforce IdP groups) | — (IdP) | `admin.staff_role.assigned` | MC |
| Platform audit search and export | `platform.audit.search`, `.export` | `platform.audit:read`, `platform.audit:export` | platform_security | platform, region | `/platform/audit` | `GET /platform/v1/audit-events` | `admin.audit.exported` | S on export |

#### 6.3 Tenant plane: organisation

| Function | Op key | Permission | Default personas | Scopes | Console page | API | Audit event | Ctl |
|---|---|---|---|---|---|---|---|---|
| Edit tenant profile (display name, contacts; default language and time zone are branding settings, [[PKG-settings-branding-content]]) | `admin.tenant_profile.update` | `tenant:update` | tenant_admin | tenant | `/admin/organisation/profile` | `PATCH /admin/v1/tenant` | `admin.tenant_profile.updated` | CP |
| Create, rename, archive unit | `admin.unit.create`, `.update`, `.archive` | `unit:create`/`update`/`delete` | tenant_admin; unit_admin for sub-units of own unit | tenant, unit | `/admin/organisation/units` | `POST/PATCH /admin/v1/units/{id}` | `admin.unit.created`, `.updated`, `.archived` | B, CP |
| Move unit (reparent) | `admin.unit.move` | `unit:update` | tenant_admin | tenant | `/admin/organisation/units/{id}` | `POST /admin/v1/units/{id}/actions/move` | `admin.unit.moved` | S |
| Add and verify custom domain | `admin.domain.add` | `auth.domain:create` | tenant_admin, security_admin | tenant | `/admin/organisation/domains` | `POST /admin/v1/domains` | `admin.domain.added`, `admin.domain.verified` | S ([[PKG-domain-verification]]) |
| Transfer or add tenant owner | `admin.owner.transfer` | `role.privileged:assign` | tenant_owner | tenant | `/admin/organisation/owners` | console only | `admin.owner.transferred` | S, MC (new owner accepts) |
| Configure sandbox (create, refresh, delete) | `admin.sandbox.manage` | `config.sandbox:create` | tenant_admin | tenant | `/admin/sandboxes` | `POST /admin/v1/sandboxes` | `admin.sandbox.created`, `.refreshed`, `.deleted` | W |
| Import, export or promote configuration package | `admin.package.import`, `.export`, `.promote` | `config.package:publish` | tenant_admin | tenant | `/admin/packages` | `POST /admin/v1/packages/{id}/actions/{import,promote}` | `admin.package.imported`, `admin.package.promoted` | MC, W ([[PKG-configuration-packages]]) |

#### 6.4 Tenant plane: users, groups and access ([[APP-user-and-access-admin]])

| Function | Op key | Permission | Default personas | Scopes | Console page | API | Audit event | Ctl |
|---|---|---|---|---|---|---|---|---|
| Invite user | `admin.user.invite` | `user:create` | user_admin, unit_admin, tenant_admin | tenant, unit | `/admin/users/invite` | `POST /admin/v1/users` | `admin.user.invited` | B, CP |
| Resend or revoke invitation | `admin.user.invitation_resend`, `_revoke` | `user:update` | user_admin, unit_admin | tenant, unit | `/admin/users/invitations` | `POST /admin/v1/invitations/{id}/actions/{resend,revoke}` | `admin.user.invitation_revoked` | B |
| Edit membership (name display, units, locale) | `admin.user.update` | `user:update` | user_admin, unit_admin | tenant, unit | `/admin/users/{id}` | `PATCH /admin/v1/users/{id}` | `admin.user.updated` | B |
| Suspend, reactivate, end membership | `admin.user.suspend`, `.reactivate`, `.end` | `user:update`, `user:delete` | user_admin, unit_admin | tenant, unit | `/admin/users/{id}` | `POST /admin/v1/users/{id}/actions/{suspend,reactivate,end}` | `admin.user.suspended`, `.reactivated`, `.ended` | B, S over threshold |
| Assign or remove operational role | `admin.role.assign`, `.unassign` | `role:assign` | user_admin, unit_admin | tenant, unit | `/admin/users/{id}/access` | `POST/DELETE /admin/v1/users/{id}/roles` | `admin.role.assigned`, `admin.role.unassigned` | B, CP |
| Assign administrative role | `admin.role.assign` (privileged) | `role.privileged:assign` | tenant_owner, tenant_admin | tenant, unit | `/admin/users/{id}/access` | same, `privileged=true` | `admin.role.assigned` | S, MC |
| Manage groups and members | `admin.group.create`, `.update`, `.add_member`, `.remove_member` | `group:create`, `group:update` | user_admin | tenant, unit | `/admin/groups` | `/admin/v1/groups/{id}/members` | `admin.group.created`, `admin.group.member_added` | B, CP |
| Assign roles to a group | `admin.group.assign_role` | `role:assign` | user_admin (operational), tenant_admin (admin roles) | tenant, unit | `/admin/groups/{id}` | `POST /admin/v1/groups/{id}/roles` | `admin.role.assigned` | MC for admin roles |
| Create or edit custom role or permission set | `admin.role.define` | `role:create`, `role:update` | security_admin | tenant | `/admin/access/roles` | `POST/PATCH /admin/v1/roles/{id}` | `admin.role.created`, `admin.role.updated` | V, MC, CP ([[PKG-roles-and-permission-sets]]) |
| Run access review campaign | `admin.access_review.run` | `access.review:create` | security_admin (owner), reviewers (managers, unit_admin) | tenant, unit | `/admin/access/reviews` | `POST /admin/v1/access-reviews` | `admin.access_review.started`, `.completed`, `admin.access_review.decision_recorded` | W ([[SEC-access-reviews]]) |
| Approve just-in-time elevation request | `admin.elevation.approve` | `access.elevation:approve` | security_admin, tenant_admin | tenant | `/admin/access/requests` | `POST /admin/v1/access-requests/{id}/actions/approve` | `admin.elevation.approved` | S ([[PKG-jit-and-break-glass]]) |
| Explain or simulate access | `admin.access.explain` | `access.explainer:read` | user_admin, security_admin, auditor | tenant, unit | `/admin/access/explain` | `POST /admin/v1/access/explain` | `admin.access.explained` | CX ([[PKG-access-explainer]]) |
| Reset MFA, revoke sessions, force password reset | `admin.user.reset_mfa`, `.revoke_sessions` | `user.mfa:update`, `user.session:delete` | security_admin | tenant | `/admin/users/{id}/security` | `POST /admin/v1/users/{id}/actions/{reset-mfa,revoke-sessions}` | `admin.user.mfa_reset`, `admin.user.sessions_revoked` | S |
| Configure SCIM / directory sync | `admin.provisioning.configure` | `settings.security:write` | security_admin | tenant | `/admin/security/provisioning` | console only | `admin.scim.configured` | V, S ([[PKG-user-provisioning-scim]]) |

#### 6.5 Tenant plane: security and identity

| Function | Op key | Permission | Default personas | Scopes | Console page | API | Audit event | Ctl |
|---|---|---|---|---|---|---|---|---|
| SSO connections | `admin.sso.publish` | `settings.security:write` | security_admin | tenant | `/admin/security/sso` | console only in v1 | `admin.sso.published` | V, S, MC ([[PKG-sso-saml-oidc-per-tenant]]) |
| Authentication and session policies | `admin.auth_policy.publish` | `settings.security:write` | security_admin | tenant, unit (tighten only) | `/admin/security/policies` | `PATCH /admin/v1/settings/auth.*` | `admin.auth_policy.published` | V, S, MC when weakening ([[PKG-authentication-policies]]) |
| Support access consent mode and approvals | `admin.support.approve`, `.revoke`, `.configure` | `support.grant:approve`, `settings.security:write` | security_admin, tenant_owner | tenant | `/admin/security/support-access` | console only | `admin.support.approved`, `.rejected`, `.revoked` | S |
| View support activity | `admin.support.activity` | `support.grant:read` | security_admin, auditor, tenant_owner | tenant | `/admin/security/support-access/activity` | `GET /admin/v1/support-activity` | — (read) | CX |
| Active sessions overview | `admin.session.list`, `.revoke` | `user.session:list`, `user.session:delete` | security_admin | tenant | `/admin/security/sessions` | `GET /admin/v1/sessions` | `admin.user.sessions_revoked` | S |

#### 6.6 Tenant plane: configuration and workflow

| Function | Op key | Permission | Default personas | Scopes | Console page | API | Audit event | Ctl |
|---|---|---|---|---|---|---|---|---|
| Change a setting (any domain) | `admin.settings.publish` | `settings.<catalogue>:write` | domain admin (see each `PKG-settings-*` catalogue) | tenant, unit, case_type | `/admin/settings/{domain}` | `PATCH /admin/v1/settings/{key}` | `admin.settings.published` | V, B, CP; MC per key |
| Case-type blueprint publish | `admin.workflow.publish` | `workflow.definition:publish` | workflow_designer (author), tenant_admin (approver) | tenant | `/admin/workflows/case-types/{id}` ([[WF-workflow-authoring-studio]]) | `POST /admin/v1/case-types/{id}/versions/{v}/actions/publish` | `admin.workflow.published` | V, MC, CP |
| Migrate running cases to a new blueprint version | `admin.workflow.migrate` | `workflow.definition:approve` | tenant_admin | tenant | `/admin/workflows/case-types/{id}/migrations` | `POST /admin/v1/case-types/{id}/migrations` | `admin.workflow.migration_started` | MC, W ([[WF-workflow-versioning]]) |
| Decision tables | `admin.decision_table.publish` | `rules.decision_table:publish` | workflow_designer | tenant, case_type | `/admin/workflows/rules` | `POST /admin/v1/decision-tables/{id}/versions/{v}/actions/publish` | `admin.decision_table.published` | V, CP |
| Forms and custom fields | `admin.form.publish`, `admin.custom_field.publish` | `form:publish`, `metadata.field:update` | workflow_designer | tenant, case_type | `/admin/workflows/forms`, `/admin/workflows/fields` | `/admin/v1/forms`, `/admin/v1/custom-fields` | `admin.form.published`, `admin.custom_field.published` | V, CP |
| Automation rules enable / disable | `admin.automation.publish`, `.disable` | `workflow.automation:publish` | workflow_designer | tenant, unit | `/admin/workflows/automation` | `/admin/v1/automation-rules/{id}` | `admin.automation.published`, `.disabled` | V, CP ([[WF-automation-rules]]) |
| Business schedules and SLA policies ([[WF-sla-and-business-calendars]]; seat calendars are computed by [[PKG-calendars-and-deadline]]) | `admin.calendar.publish` | `workflow.calendar:publish` | workflow_designer, unit_admin (unit calendar) | tenant, unit | `/admin/workflows/calendars` | `/admin/v1/calendars/{id}` | `admin.calendar.published` | V ([[WF-sla-and-business-calendars]]) |

#### 6.7 Tenant plane: content, notifications, integrations, AI, data, billing

| Function | Op key | Permission | Default personas | Scopes | Console page | API | Audit event | Ctl |
|---|---|---|---|---|---|---|---|---|
| Theme | `admin.theme.publish` | `brand.theme:publish` | content_admin | tenant | `/admin/content/branding` | `POST /admin/v1/branding/draft/actions/activate` | `admin.theme.published` | V, S ([[PKG-branding-and-theming]]) |
| Terminology and copy overrides | `admin.terminology.publish` | `content.terminology:publish` | content_admin | tenant | `/admin/content/terminology` | `/admin/v1/terminology` | `admin.terminology.published` | V, CP ([[PKG-tenant-terminology-and-copy]]) |
| Document templates | `admin.template.publish` | `template.document:publish` | content_admin | tenant, case_type | `/admin/content/document-templates` | `/admin/v1/document-templates` | `admin.template.published` | V, CP |
| Legal and consent texts, accessibility statement | `admin.legal_text.publish` | `settings.branding:write` | content_admin (author), tenant_owner (approver) | tenant | `/admin/content/legal` | console only | `admin.legal_text.published` | V, MC ([[I18N-legal-declaration-and-consent]]) |
| Notification templates and policies | `admin.notification_policy.publish` | `notify.policy:publish` | content_admin, tenant_admin | tenant, unit, case_type | `/admin/notifications` | `/admin/v1/notification-policies` | `admin.notification_policy.published` | V, CP ([[PKG-notification-policies]]) |
| Integration connections | `admin.connection.create`, `.update`, `.disable` | `integration.connection:update` | integration_admin | tenant | `/admin/integrations/connections` | `/admin/v1/connections` | `admin.connection.created` | S ([[INT-connections-admin]]) |
| API clients and keys | `admin.api_client.create`, `.rotate_key`, `.revoke_key` | `api_client:create`, `:update` | integration_admin | tenant | `/admin/integrations/api-clients` | create console only; rotate and revoke via API | `admin.api_client.created`, `admin.api_client.key_rotated`, `.key_revoked` | S ([[PKG-api-clients-and-keys]]) |
| Webhook endpoints | `admin.webhook_endpoint.manage` | `webhook.endpoint:create` | integration_admin | tenant | `/admin/integrations/webhooks` | `/admin/v1/webhook-endpoints` ([[APP-webhooks-outbound]]) | `admin.webhook_endpoint.created` | CP |
| Connector data policies | `admin.connector_policy.publish` | `integration.data_policy:publish` | security_admin | tenant | `/admin/integrations/data-policies` | console only | `admin.connector_policy.published` | V, MC ([[INT-connector-data-policies]]) |
| Tenant AI policy | `admin.ai_policy.publish` | `ai.policy:publish` | ai_admin (author), tenant_owner or tenant_admin (approver) | tenant, unit, case_type | `/admin/ai/policy` | `/admin/v1/ai-policy` | `admin.ai_policy.published` | V, MC ([[AI-tenant-ai-policy]]) |
| Assistants and agents | `admin.ai_agent.publish` | `ai.agent:publish` | ai_admin | tenant | `/admin/ai/agents` | `/admin/v1/ai-agents` | `admin.ai_agent.published` | V, MC ([[AI-agent-configuration]]) |
| Retention schedule overrides | `admin.retention.publish` | `settings.data:write` | tenant_admin (author), tenant_owner (approver) | tenant, case_type | `/admin/data/retention` | console only | `admin.retention.published` | V, MC ([[PKG-settings-data-and-privacy]]) |
| Legal holds | `admin.legal_hold.place`, `.release` | `data.legal_hold:create`, `:delete` | tenant_admin, secretariat lead via custom role | tenant | `/admin/data/legal-holds` | `/admin/v1/legal-holds` | `admin.legal_hold.placed`, `.released` | S; release is IR + MC |
| Full tenant data export | `admin.data_export.request` | `data.export:create` | tenant_owner | tenant | `/admin/data/exports` | `POST /admin/v1/data-exports` | `admin.data_export.requested`, `.downloaded` | S, MC, W |
| Billing view, contacts, plan change request | `admin.billing.update_contacts`, `.request_plan_change` | `billing.account:update` | billing_admin | tenant | `/admin/billing` | `/admin/v1/billing/*` | `admin.billing.contact_updated`, `.plan_change_requested` | — ([[PKG-settings-billing-and-plans]]) |

#### 6.8 Tenant plane: oversight

| Function | Op key | Permission | Default personas | Scopes | Console page | API | Audit event | Ctl |
|---|---|---|---|---|---|---|---|---|
| Approvals inbox (maker-checker) | `admin.approval.decide` | permission of the underlying op plus `:approve` | the approver role named on each op | tenant, unit | `/admin/changes?state=in_review` | `POST /admin/v1/change-sets/{id}/actions/{approve,reject}` | `admin.approval.approved`, `.rejected` | S |
| Audit log search | `admin.audit.search` | `audit.log:read` | auditor, security_admin, tenant_admin | tenant, unit (unit events only) | `/admin/audit` | `GET /admin/v1/audit-events` | — (read) | CX |
| Audit export | `admin.audit.export` | `audit.log:export` | auditor, security_admin | tenant | `/admin/audit` | `POST /admin/v1/audit-exports` | `admin.audit.exported` | S, W |
| Change history and rollback | `admin.change.rollback` | permission of the original op | the role that may make the original change | as original | `/admin/changes/{changeSetId}` | `POST /admin/v1/change-sets/{id}/actions/revert` | `admin.change.rolled_back` | as original op ([[APP-admin-change-history]]) |
| Bulk jobs | `admin.bulk.start`, `.cancel` | `bulk.job:create` plus each row's op permission | user_admin, tenant_admin, workflow_designer | tenant, unit | `/admin/bulk` | `POST /admin/v1/bulk-jobs` | `admin.bulk.job_started`, `.job_completed` | W, MC over threshold ([[APP-bulk-admin-operations]]) |
| Admin reports (seats, adoption, configuration health) | `admin.report.view` | `report.admin:read` | tenant_admin, auditor, billing_admin | tenant, unit | `/admin/reports` | `GET /admin/v1/reports/{id}` | — | CX |

<!-- section:examples -->
## Worked examples

**Example 1: delegated user admin for the SEBI ODR desk**

An ODR institution tenant has units "Head office" and "SEBI ODR desk". The tenant admin assigns Priya `unit_admin` at scope `unit:sebi-odr-desk`.

1. Priya opens `/admin/users`. The list is filtered server-side by `authz.where('user.list')` to memberships in the SEBI ODR desk subtree; the scope chip in the header reads "SEBI ODR desk".
2. She invites a conciliator with role `neutral`. `runAdminOp` checks `user:create` at `unit:sebi-odr-desk` (allowed) and ADM-R2 (`neutral` is in `unit_admin`'s "may assign" list) and records `admin.user.invited` with `via=console`.
3. She tries to give a colleague `user_admin`. The role picker does not offer it; a direct API call returns `403 role-escalation-forbidden`.

**Example 2: the same operation through four surfaces**

`admin.role.assign` with `role=secretariat` for 40 people arrives as: (a) a console multi-select action, (b) a bulk CSV row set, (c) `POST /admin/v1/users/{id}/roles` from the institution's HR system, (d) an admin copilot proposal "give the new Mumbai registry staff the secretariat role". All four call `runAdminOp`; (a) and (c) execute directly; (b) executes rows as a job; (d) produces a draft change set that a human confirms. The audit events differ only in `via` and, for (d), carry the copilot run reference ([[APP-admin-copilot]]).

**Example 3: privileged grant with maker-checker**

A tenant admin assigns `security_admin` to a new IT lead. The dispatcher sees `makerChecker: 'when:privilegedRole'` and creates change set `CS-…` in `in_review` instead of executing. The other tenant admin approves it in `/admin/changes` after step-up. Only then is `admin.role.assigned` recorded, with `approvedBy`, and all tenant owners get a notification.

<!-- section:alternatives -->
## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| One `tenant_admin` role with everything (current state) | No least privilege; an institution cannot give its IT team SSO without also giving templates, billing and AI policy; fails access-review expectations in [[SEC-access-reviews]] |
| Monolithic profiles per persona | Pattern rejected by modern stacks in favour of permission sets assembled into roles; we follow permission sets plus groups of sets ([[PKG-roles-and-permission-sets]]) |
| Separate admin apps per area (users app, workflow app) | Duplicates shell, auth and audit; navigation by permission inside one `/admin` group gives the same separation |
| Unit admins as separate "sub-tenants" | Breaks data ownership (a unit is not a tenant, TM glossary in [[MT-tenant-model#language]]); scoped role assignment gives delegation without new isolation boundaries |
| Admin operations implemented separately in console, API and bulk | Drift in validation and audit is the common cause of privilege bugs; a single registry is cheaper to test |
| Platform staff as hidden members of every tenant | Standing access to tenant data; rejected by ADM-R5 and by customer expectations of consent-based support |

Patterns borrowed from: organisation-level versus app-level admin roles in Atlassian [R3]; org owners, org admins and workspace admins in Slack Enterprise Grid [R4]; IAM administrator that cannot assign administrator roles and a single account owner in the Stripe dashboard [R5]; workspace-level permissions through groups in Relativity [R6]; environment-level administration in the Power Platform admin centre [R7].

<!-- section:crosscutting -->
## Cross-cutting concerns

| Concern | How the design addresses it |
|---|---|
| Security | Single dispatcher enforces permission, ADM-R2 no-escalation, step-up, maker-checker and entitlements; admin roles hold no case content; privileged grants alert other admins; admin API cannot create API clients ([[INT-tenant-admin-api#operations]]) |
| Tenancy | Tenant ops run in `withTenant()` with forced RLS; tenant ID only from session or credential; unit scope is an authz filter inside one tenant, never an isolation boundary |
| Privacy | Admin pages show only membership and configuration data; masking of contact fields for unit admins outside their subtree; audit events store IDs and hashes ([[PKG-audit-trail]]) |
| Residency | Every op runs in the tenant's home region; the platform console is per region; change sets, approvals and audit stay in region |
| Observability | Every op emits `admin.op.duration`, `admin.op.denied` and `admin.op.approval_pending` metrics with `op_key`, `via`, `tenant`, `region`; security-category events go to the SIEM ([[OBS-security-events]]) |
| AI | The copilot's tools are generated from the registry; it gets only ops flagged `CP`/`CX` and only within the invoking human's permissions (shared model §6) |
| Cost | Bulk and workflow-class ops run on bounded queues with per-tenant concurrency limits ([[PKG-settings-platform-operations]]) |
| Accessibility | All admin pages use design-system components; dense tables follow [[PKG-data-table]] and [[APP-secretariat-console-and-neutral]] conformance notes |

<!-- section:guardrails -->
## Guardrails

- **ADM-G1** No admin capability may be implemented outside `@nomology/admin-ops`. CI fails if a tRPC procedure, Route Handler or Server Action under `(tenant-admin)` or `(platform-admin)` mutates state without calling `runAdminOp`.
- **ADM-G2** Every op declares permission, scopes, change class, audit event, surfaces and controls; the registry build fails on missing fields or an unregistered audit action.
- **ADM-G3** Permissions must exist in [[PKG-permission-catalogue]]; role keys must exist in [[PKG-roles-and-permission-sets]]. New ones are added there first.
- **ADM-G4** Ops marked `irreversible` require typed confirmation and step-up, and the console must show the words "This cannot be undone".
- **ADM-G5** Tenant ID, unit ID scope and actor are never accepted from the request body; they come from context.
- **ADM-G6** Copilot exposure (`CP`, `CX`) defaults to none; adding it to an op needs review by the AI group owner.
- **ADM-G7** The catalogue tables in this node are generated from the registry (`pnpm admin-ops:catalogue`) and checked in CI; hand edits are overwritten.
- **ADM-G8** Admin ops never send content to a person outside the tenant except invitations and the notifications declared on the op.

<!-- section:ownership -->
## Ownership

| Part | Owner | Change process |
|---|---|---|
| Administration model (this node), persona table | Platform product lead with security lead | PR to this node plus ADR if a persona is added or removed |
| `@nomology/admin-ops` package | Platform core team (CODEOWNERS `@nomology/platform-core`) | Normal review plus security reviewer for new privileged ops |
| Each op's handler | Owning domain team (identity, workflow, content, integrations, AI) | Domain review |
| Permission and role names | Authorization owners ([[PKG-permission-catalogue]], [[PKG-roles-and-permission-sets]]) | Catalogue PR first |
| Platform plane ops | Platform operations lead per region | Change management in [[DEP-release-notes-and-change]] |

<!-- section:questions -->
## Open questions

- [ ] Should `tenant_owner` be held by a named individual at the institution (contractual signatory) or by any person the institution chooses? (owner: legal and account management)
- [ ] Minimum number of `tenant_owner`s: one (proposed, with a warning) or two (stricter, but hard for small CORD tenants)? (owner: product)
- [ ] Do unit admins need to administer unit-level settings for notification policies and AI policy, or only users and calendars in v1? (owner: product with SEBI ODR institution tenants)
- [ ] Should `auditor` be allowed to see support-session activity details, or only counts? Proposed: details. (owner: security)
- [ ] Shared model naming: the route group table in [[APP-route-groups-per-persona]] still shows the platform console at `/ops`; this node uses `/platform` per the shared model. The route-group owner should update its table. (owner: frontend lead)
- [ ] Is "may assign" for `user_admin` limited to roles with no admin permission at all, or to roles whose permissions are a subset of its own (proposed: both conditions)? (owner: security, with [[PKG-roles-and-permission-sets]])

<!-- checks -->
## Template checks

<!-- check:security -->
### Security and privacy

New attack surface: the admin dispatcher, delegated role assignment and four entry surfaces (console, API, bulk, copilot) over the same ops. Threats and answers: privilege escalation through role assignment (ADM-R2 subset rule, `tenant_owner` only by owner, maker-checker on privileged grants, alert to other admins); configuration access becoming case access (ADM-R1: admin roles carry no case permissions); drift between surfaces (ADM-G1/G2: one registry, CI-enforced); compromised admin credential (step-up on privileged ops, API cannot create API clients, privileged events forwarded to SIEM); copilot overreach (tools generated only for `CP`/`CX` ops, executed with the invoking human's permissions). Personal data processed: membership names and contact data, shown only to admins with `user:read` at the matching scope and masked otherwise.

<!-- check:tenancy -->
### Tenancy

Tenant identity comes from the host-resolved session or the API credential and is set per transaction by the Prisma extension under forced RLS; no op accepts `tenant_id` in its input (ADM-G5). Unit scope is an authz filter inside one tenant, not an isolation boundary. Platform ops read platform-level tables only and reach tenant data only through support grants on the tenant host (ADM-R5). Capacity: bulk and workflow ops use per-tenant concurrency limits so one tenant's large import cannot starve others ([[PKG-settings-platform-operations]] `platform.bulk.*`).

<!-- check:residency -->
### Data residency and lifecycle

All ops execute in the tenant's home region; approvals, change sets, bulk job files and audit events are stored in that region's Postgres and object storage. The platform console is per region with no global view; cross-region items (tenant directory entries) carry only slug, region and status. Retention of admin audit follows [[PKG-audit-trail#config]].

<!-- check:failure -->
### Failure handling and recovery

Direct ops are single transactions with the audit record inside, so they either fully happen or not at all. Versioned ops change only draft state until publish, which is atomic. Workflow-class ops (provisioning, offboarding, bulk) are idempotent per activity and resumable; the console shows partial progress and the compensation that will run. If the authz service or settings resolver is unavailable the dispatcher fails closed with a retryable `503`, never executing an unchecked op. Maker-checker requests expire (default 7 days) rather than executing late.

<!-- check:scale -->
### Capacity, performance and cost

Expected load is low for interactive admin traffic (tens of ops per minute per tenant) with peaks from bulk jobs (SEBI ODR tenants onboarding thousands of party or staff memberships). Targets: interactive op p95 under 500 ms server time; bulk throughput 50 rows per second per job with 2 concurrent jobs per tenant (proposed). The registry adds negligible cost; the main cost is audit volume, already sized in [[PKG-audit-trail#nfr]].

<!-- check:observability -->
### Observability

Metrics per `op_key`, `via`, tenant and region: count, error rate, denial rate, p95 duration, approvals pending and age. Alerts: spike in `admin.op.denied` for one principal (possible probing), any privileged grant outside business hours for the tenant's time zone (informational to tenant owners), maker-checker requests older than 5 days, bulk job failure rate over 5%. Dashboards in the platform console per region; tenants see their own admin activity in [[APP-admin-change-history]].

<!-- check:rollout -->
### Rollout and migration

1. Introduce `@nomology/admin-ops` and migrate existing ops in [[APP-tenant-admin-console]] and [[INT-tenant-admin-api]] behind it with no behaviour change.
2. Map existing role names to shared-model keys (`tenant_admin` stays; `case_manager` becomes `secretariat`; `support_engineer` becomes `platform_support`) in a data migration with aliases kept for one release.
3. Introduce delegated roles; existing tenant admins keep `tenant_admin`; the first tenant admin of each tenant is offered `tenant_owner` and must accept.
4. Rename `/ops` to `/platform` with redirects for one release; rename `/v1/admin` to `/admin/v1` with the old path kept for the deprecation period in [[INT-tenant-admin-api#versioning]].
Rollback: the registry can run in "shadow" mode (log differences, execute legacy path) during step 1.

<!-- check:reversibility -->
### Reversibility

Hard to change later: the role keys and their meaning (stored in assignments and audit), the op keys and audit event names (stored in history; never renamed, only deprecated), and the "admins do not read case content" principle (customer contracts will rely on it). These are recorded here and should be confirmed in an ADR before Phase 2. Easy to change: which permission sets each default role holds, console page layout, copilot exposure per op.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "A custom admin role is a set of permissions; a resource set scopes where it applies; an assignment links an admin to a role and resource set.",
    "id": "R1",
    "kind": "vendor",
    "title": "Okta Help: Use custom admin roles (roles, resource sets and assignments)",
    "url": "https://help.okta.com/en-us/Content/Topics/Security/custom-admin-role/about-creating-custom-admin-roles.htm",
    "vendor": "Okta"
  },
  {
    "excerpt": "Administrative units subdivide an organisation; a role assigned with an administrative unit as scope applies only to that unit's members.",
    "id": "R2",
    "kind": "vendor",
    "title": "Microsoft Entra ID: Create or delete administrative units",
    "url": "https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/admin-units-manage",
    "vendor": "Microsoft"
  },
  {
    "excerpt": "Organization admin, site admin, user access admin and app admin roles with different scopes; only organization admins manage other organization admins.",
    "id": "R3",
    "kind": "vendor",
    "title": "Atlassian Support: What are the different types of admin roles?",
    "url": "https://support.atlassian.com/user-management/docs/what-are-the-different-types-of-admin-roles/",
    "vendor": "Atlassian"
  },
  {
    "excerpt": "Permissions for org owners, org admins, workspace owners and workspace admins on an Enterprise Grid organisation.",
    "id": "R4",
    "kind": "vendor",
    "title": "Slack Help: Permissions by role in Slack",
    "url": "https://slack.com/help/articles/201314026",
    "vendor": "Slack"
  },
  {
    "excerpt": "IAM Administrator manages team members but cannot assign the Administrator or Super Administrator role; only one account owner.",
    "id": "R5",
    "kind": "vendor",
    "title": "Stripe Docs: User roles",
    "url": "https://docs.stripe.com/dashboard/teams/roles",
    "vendor": "Stripe"
  },
  {
    "excerpt": "Permissions are granted to groups at workspace level.",
    "id": "R6",
    "kind": "vendor",
    "title": "RelativityOne: Setting workspace permissions",
    "url": "https://help.relativity.com/RelativityOne/Content/Relativity/Security_permissions/Setting_workspace_permissions.htm",
    "vendor": "Relativity"
  },
  {
    "excerpt": "Administration of environments, security and governance in the Power Platform admin centre.",
    "id": "R7",
    "kind": "vendor",
    "title": "Power Platform admin documentation",
    "url": "https://learn.microsoft.com/en-us/power-platform/admin/admin-documentation",
    "vendor": "Microsoft"
  }
]
```

<!-- end -->
