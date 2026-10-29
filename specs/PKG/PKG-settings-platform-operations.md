---
id: "PKG-settings-platform-operations"
title: "Platform operations settings"
parent: "PKG-settings-catalogue"
order: 10
type: "feature"
template: "config"
status: "draft"
owner: null
indicative: false
summary: "Settings for regions and offerings, tenant provisioning and lifecycle timers, sandboxes, support access bounds and tenant consent, bulk limits, admin governance, audit export limits, maintenance and the platform console"
links: []
rev: 1
syncHash: "a638426e8807fad9"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.7.3.10 Platform operations settings

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Settings for regions and offerings, tenant provisioning and lifecycle timers, sandboxes, support access bounds and tenant consent, bulk limits, admin governance, audit export limits, maintenance and the platform console

<!-- section:purpose -->
## Purpose and scope

Covers how Nomology runs the platform and how tenants govern administrative operations: which regions and offerings accept new tenants, tenant provisioning rules, lifecycle timers (invitation, domain verification, export window, deletion), sandboxes, support access bounds and tenant consent, bulk operation limits, admin approvals and change history, audit search and export limits, maintenance windows and banners, and platform console sessions.

Consumed by: [[MT-tenant-lifecycle]], [[APP-tenant-onboarding-wizard]], [[APP-platform-admin-and-support]], [[PKG-support-access-and-impersonation]], [[APP-bulk-admin-operations]], [[APP-admin-change-history]], [[APP-tenant-admin-console]], [[INT-tenant-admin-api]] and the admin dispatcher in [[APP-administration-model#design]].

Not here:
- Release flags per tenant ([[PKG-feature-flags]]) and deployment configuration and secrets ([[FND-environment-management]]).
- Authentication and session policies for tenant users ([[PKG-settings-security-and-identity]]); this catalogue only holds the **platform console** session bounds.
- Role, permission-set and separation-of-duties settings in general ([[PKG-settings-access-control]]); this catalogue holds only the `access.support.*` and `access.bulk.*` keys because they are specific to support access and bulk operations. The access-control catalogue should reference them rather than redefine them.
- Audit retention periods ([[PKG-settings-data-and-privacy]]); this catalogue holds only search and export limits.
- Plans and entitlement values ([[PKG-settings-billing-and-plans]]); entitlement names are referenced in the Plan column.

<!-- section:scopes -->
## Scopes that apply

| Scope | Used | Administered by |
|---|---|---|
| `platform` | Yes: hard bounds and defaults | `platform_admin` proposes, `platform_owner` approves (maker-checker) |
| `region` | Yes: region opening, allowed tenant types and billing entities, maintenance windows, region-specific bounds | `regional_ops` proposes, `platform_admin` approves |
| `offering` | Yes: blueprints and defaults that differ between CORD and TERES | `platform_admin` |
| `tenant` | Yes: two kinds. Contract values set **by platform staff** for one tenant (`platform.lifecycle.*`, `platform.sandbox.max_count`), and tenant governance values set **by the tenant** (`access.support.*`, `access.bulk.*`, `access.admin.*`) | Platform: `platform_admin`; tenant: `tenant_owner` or `security_admin` as listed per key |
| `unit` | No | Operations and support consent apply to the whole tenant |
| `case_type`, `case` | No | Not procedural settings |
| `user` | No | — |

<!-- section:catalogue -->
## Settings catalogue

Audit classes: `standard` (recorded), `sensitive` (recorded, other admins notified), `maker-checker` (second approver required, see [[PKG-separation-of-duties]]).

#### Regions and offerings

| Key | Type | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `platform.region.provisioning_open` | bool | `false` until legal sign-off | region | n/a | — | `settings.platform:write` | immediately (new provisioning only) | maker-checker |
| `platform.region.allowed_tenant_types` | enum[] (`arbitral_institution`, `odr_institution`, `cord`, `enterprise`, `court_programme`) | `[]` | region | n/a | — | `settings.platform:write` | new provisioning | maker-checker |
| `platform.region.allowed_billing_entities` | enum[] (`ntpl`, `tapl`, `us_entity`) | in: `[ntpl]`; sg: `[tapl]`; us: `[us_entity]` | region | n/a | — | `settings.platform:write` | new provisioning | maker-checker |
| `platform.region.legal_signoff_ref` | string (record ID) | — | region | n/a | — | `settings.platform:write` | informational | maker-checker |
| `platform.offering.enabled_regions` | region[] | CORD: `[in]`; TERES: `[in, sg, us]` | offering | n/a | — | `settings.platform:write` | new provisioning | maker-checker |
| `platform.offering.default_blueprints` | blueprint ID[] | per offering | offering | n/a | — | `settings.platform:write` | wizard | standard |

#### Tenant provisioning

| Key | Type | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `platform.tenant.reserved_slugs` | string[] | `[admin, api, platform, ops, status, www, mail, support, nomology, cord, teres]` | platform | n/a | — | `settings.platform:write` | immediately | standard |
| `platform.tenant.slug_min_length` | int 3–10 | 3 | platform | n/a | — | `settings.platform:write` | new tenants | standard |
| `platform.tenant.max_units` | int 1–5,000 | 500 | platform, tenant | yes | `units` entitlement | `settings.platform:write` | immediately | standard |
| `platform.tenant.max_unit_depth` | int 1–8 | 5 (TM-R8) | platform | n/a | — | `settings.platform:write` | immediately | maker-checker |
| *Maximum custom roles* | see [[PKG-settings-access-control#catalogue]] (`access.roles.max_custom_roles`, platform ceiling 200) | | | | | | | |
| `platform.tenant.min_owners` | int 1–3 | 1 | platform, tenant | yes | — | `settings.platform:write` | next owner change | maker-checker |
| `platform.tenant.owner_must_not_use_domains` | string[] | Nomology workforce domains | platform | n/a | — | `settings.platform:write` | immediately | maker-checker |
| `platform.tenant.provisioning_draft_retention_days` | int 1–90 | 30 | platform | n/a | — | `settings.platform:write` | nightly job | standard |
| `platform.tenant.smoke_check_required` | bool | `true` | platform | n/a | — | `settings.platform:write` | new provisioning | maker-checker |

#### Tenant lifecycle timers

| Key | Type | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `platform.lifecycle.owner_invitation_days` | int 1–30 | 7 | platform, tenant | no | — | `platform.tenant:update` | next invitation | standard |
| `platform.lifecycle.domain_verification_days` | int 1–30 | 7 | platform | n/a | — | `settings.platform:write` | new verifications | standard |
| `platform.lifecycle.export_window_days` | int 7–180 | 30 (proposed; contract value per tenant) | platform, tenant | no | — | `platform.tenant:update` | next offboarding | maker-checker |
| `platform.lifecycle.delete_after_days` | int 30–365 | 90 (proposed) | platform, tenant | no | — | `platform.tenant:update` | next offboarding | maker-checker |
| `platform.lifecycle.deletion_approval_escalation_days` | int 1–30 | 14 | platform | n/a | — | `settings.platform:write` | running offboardings | standard |
| `platform.lifecycle.nonpayment_grace_days` | int 0–90 | 15 (contract) | platform, tenant | no | — | `settings.platform:write` (`platform_billing`) | next dunning cycle | sensitive |
| `platform.lifecycle.suspension_legal_notices_continue` | bool | `true` (assumption, legal to confirm) | platform, offering, tenant | yes | — | `settings.platform:write` | next suspension | maker-checker |
| `platform.lifecycle.export_url_ttl_days` | int 1–14 | 7 | platform | n/a | — | `settings.platform:write` | new exports | standard |

#### Sandboxes

| Key | Type | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `platform.sandbox.enabled` | bool | `true` | platform, region, tenant | yes | `sandbox` entitlement | `settings.platform:write` | immediately | standard |
| `platform.sandbox.max_count` | int 0–5 | 1 | platform, tenant | yes | `sandbox` entitlement | `platform.tenant:update` | immediately | standard |
| `platform.sandbox.data_mode` | enum `synthetic`, `masked_copy` | `synthetic` | platform, region, tenant | yes | `masked_copy` needs `sandbox_masked` entitlement | `config.sandbox:create` | next refresh | maker-checker |
| `platform.sandbox.idle_expiry_days` | int 7–365 | 90 | platform, tenant | yes | — | `config.sandbox:create` | nightly job | standard |

#### Support access: platform bounds

| Key | Type | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `platform.support.max_duration_min.config_read` | int 15–480 | 480 | platform | n/a | — | `settings.platform:write` | new grants | maker-checker |
| `platform.support.max_duration_min.config_write` | int 15–240 | 240 | platform | n/a | — | `settings.platform:write` | new grants | maker-checker |
| `platform.support.max_duration_min.case_read` | int 15–480 | 480 | platform | n/a | — | `settings.platform:write` | new grants | maker-checker |
| `platform.support.max_duration_min.impersonate_readonly` | int 15–120 | 120 | platform | n/a | — | `settings.platform:write` | new grants | maker-checker |
| `platform.support.max_duration_min.break_glass` | int 15–120 | 120 | platform | n/a | — | `settings.platform:write` | new grants | maker-checker |
| `platform.support.request_expiry_hours` | int 1–72 | 12 [R1] | platform | n/a | — | `settings.platform:write` | new requests | maker-checker |
| `platform.support.session_idle_min` | int 5–60 | 30 | platform | n/a | — | `settings.platform:write` | new sessions | maker-checker |
| `platform.support.ip_allowlist` | CIDR[] | zero-trust proxy egress ranges | platform, region | yes | — | `settings.platform:write` | immediately | maker-checker |
| `platform.support.session_recording` | enum `off`, `case_grants`, `all` | `off` (open question) | platform, region | yes | — | `settings.platform:write` | new sessions | maker-checker |
| `platform.support.max_grants_per_engineer_per_day` | int 1–20 | 3 (alert threshold) | platform | n/a | — | `settings.platform:write` | immediately | standard |


#### Bulk operations

| Key | Type | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `platform.bulk.max_rows_per_file` | int 100–100,000 | 10,000 | platform, tenant | yes | `bulk_rows` entitlement | `settings.platform:write` | new jobs | standard |
| `platform.bulk.max_file_mb` | int 1–100 | 20 | platform | n/a | — | `settings.platform:write` | new uploads | standard |
| `platform.bulk.max_concurrent_jobs_per_tenant` | int 1–5 | 2 | platform, tenant | yes | — | `settings.platform:write` | next job start | standard |
| `platform.bulk.result_retention_days` | int 1–90 | 30 | platform | n/a | — | `settings.platform:write` | nightly job | standard |
| `platform.bulk.invitation_send_per_minute` | int 10–2,000 | 300 | platform, region, tenant | yes | — | `settings.platform:write` | running jobs | standard |

#### Admin governance

| Key | Type | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `platform.admin.rollback_window_days` | int 1–3,650 | 365 | platform | n/a | — | `settings.platform:write` | immediately | standard |
| `platform.admin.api_write_per_minute` | int 10–600 | 60 | platform, tenant | yes | `admin_api_rate` entitlement (reads only) | `settings.platform:write` | next minute | standard |

#### Audit search and export

| Key | Type | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `platform.audit.tenant_search_max_range_days` | int 1–93 | 31 | platform | n/a | — | `settings.platform:write` | next query | standard |
| `platform.audit.export_max_events` | int 10,000–10,000,000 | 5,000,000 | platform | n/a | — | `settings.platform:write` | new exports | standard |
| `platform.audit.export_url_ttl_hours` | int 1–72 | 24 | platform | n/a | — | `settings.platform:write` | new exports | standard |
| `platform.audit.max_running_exports_per_tenant` | int 1–3 | 1 | platform | n/a | — | `settings.platform:write` | next export | standard |

#### Maintenance, banners and platform console

| Key | Type | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `platform.maintenance.window` | weekly window (day, start, duration, time zone) | in: Sun 01:00–03:00 IST; sg: Sun 01:00–03:00 SGT; us: Sun 02:00–04:00 ET | region | n/a | — | `platform.operations:configure` | next window | standard |
| `platform.maintenance.notice_hours` | int 24–336 | 72 | platform, region | yes | contract may require more | `platform.operations:configure` | next window | standard |
| `platform.maintenance.tenant_blackout_dates` | date ranges | `[]` | tenant | no | — | `platform.tenant:update` (from contract, for example scheduled hearings) | immediately | standard |
| `platform.banner.max_active_per_scope` | int 1–5 | 2 | platform | n/a | — | `settings.platform:write` | immediately | standard |
| `platform.preview.opt_ins` | set of preview flag keys the tenant has opted into (only flags of kind `preview`, [[PKG-feature-flags]] FLAG-R-5) | `[]` | tenant | no | — | `settings.platform:write` on behalf of the tenant, or the tenant owner from the Early access page | next request | standard |
| `platform.console.idle_timeout_min` | int 5–30 | 15 | platform, region | yes | — | `settings.platform:write` | next request | maker-checker |
| `platform.console.absolute_timeout_hours` | int 1–12 | 8 | platform, region | yes | — | `settings.platform:write` | next sign-in | maker-checker |
| `platform.console.step_up_max_age_min` | int 1–15 | 5 | platform | n/a | — | `settings.platform:write` | next action | maker-checker |

**Moved to [[PKG-settings-access-control#catalogue]]** (decision D9: this catalogue keeps only `platform.*` keys): tenant support-access consent (`access.support.*`), bulk-operation controls (`access.bulk.*`) and admin governance (`access.admin.reason_required`, `access.admin.notify_owners_on_privileged_grant`, `access.admin.single_owner_warning`); the former admin approval expiry is now `access.change_control.approval_expiry_days`. See [[PKG-settings-access-control#catalogue]] for their definitions.

<!-- section:validation -->
## Validation and dependencies

- A tenant cannot be provisioned in a region unless `platform.region.provisioning_open = true`, its type is in `allowed_tenant_types`, its billing entity is in `allowed_billing_entities`, and the offering lists the region in `platform.offering.enabled_regions`.
- `access.support.consent_mode = standing_config_read` is rejected when the platform or region locks it off, and requires the tenant's plan contract flag `support_standing_consent`.
- `access.support.case_content_approvers` must contain only active memberships; if it becomes empty (people leave), `case_read` requests are rejected with "No case-content approver configured" and the owners are notified.
- `access.support.max_duration_min` must not exceed the matching `platform.support.max_duration_min.*` bound.
- `access.bulk.step_up_threshold_rows` must be ≤ `access.bulk.approval_threshold_rows`.
- `platform.lifecycle.delete_after_days` must be ≥ `platform.lifecycle.export_window_days` + 7.
- `platform.tenant.min_owners` cannot be raised for a tenant above its current owner count without a grace period; the console shows how many tenants would be affected.
- Lowering a platform bound below values explicitly set by tenants shows the affected tenants before confirmation; the default choice is to clamp those values at the new bound and notify their owners.
- Bounds are enforced server-side in the settings resolver; console validation is a convenience only.

<!-- section:defaults -->
## Defaults by tenant type

| Key | Arbitral institution | SEBI ODR institution | CORD tenant | Court or government programme | Why they differ |
|---|---|---|---|---|---|
| `access.support.consent_mode` | `per_request` | `per_request` | `standing_config_read` (CORD is operated by Nomology, assumption to confirm) | `deny_all_except_break_glass` | Government programmes often require no vendor access without formal approval |
| `access.support.notify_impersonated_user` | `true` | `true` | `true` | `true` | — |
| `access.support.show_full_names_under_config_read` | `false` | `false` | `true` | `false` | CORD support routinely resolves named-user sign-in issues |
| `access.bulk.step_up_threshold_rows` | 50 | 200 | 100 | 50 | ODR institutions onboard at higher volume |
| `access.bulk.approval_threshold_rows` | 500 | 2,000 | 1,000 | 200 | Same; government programmes are stricter |
| `platform.bulk.max_rows_per_file` | 10,000 | 50,000 (proposed) | 10,000 | 10,000 | MII-driven onboarding volumes |
| `platform.sandbox.max_count` | 1 | 1 | 0 | 1 | CORD tenant configuration is managed centrally |
| `platform.tenant.min_owners` | 2 | 2 | 1 | 2 | Institutions need continuity when staff change |
| `platform.lifecycle.export_window_days` | 60 | 30 | 30 | 90 | Contract norms (proposed; account management to confirm) |
| `platform.lifecycle.suspension_legal_notices_continue` | `true` | `true` | `true` | `true` | Due process on running cases; legal to confirm |
| `access.admin.reason_required` | `security_and_legal` | `all_publishes` | `security_and_legal` | `all_changes` | Regulated and government tenants need fuller change records |

<!-- section:admin_ux -->
## Where it is administered

| Group | Console and page | API | Copilot |
|---|---|---|---|
| Regions and offerings | Platform console → `/platform/regions/{region}/settings`, `/platform/offerings/{offering}/settings` | `PATCH /platform/v1/settings/{key}` | No |
| Provisioning, lifecycle, sandboxes (platform values) | `/platform/settings/operations`; per-tenant contract values on `/platform/tenants/{id}/lifecycle` | `/platform/v1/settings/{key}?scope=tenant:{id}` | No |
| Support bounds | `/platform/settings/support` | `/platform/v1/settings/platform.support.*` | No |
| Support consent | Tenant console → Security → Support access (`/admin/security/support-access`, "Consent" tab) | console only | May explain, never propose |
| Bulk and admin governance | Tenant console → Settings → Administration (`/admin/settings/administration`) | `PATCH /admin/v1/settings/access.bulk.*`, `access.admin.*` | May propose a draft |
| Maintenance, banners, console session | `/platform/operations/maintenance`, `/platform/operations/banners`, `/platform/settings/console` | `/platform/v1/...` | No |

Inherited and locked values show the effective value, its source ("Nomology platform default", "India region", "Set for this tenant") and a lock icon with the locking scope. Contract values set by Nomology for a tenant appear read-only in the tenant console under Settings → Administration → "Agreed with Nomology".

<!-- section:change_control -->
## Change control and audit

- Every `platform.*` change at platform or region scope is maker-checker (author `platform_admin` or `regional_ops`, approver `platform_owner` or `platform_admin` not the author) and is announced in the internal change log ([[DEP-release-notes-and-change]]).
- `access.support.consent_mode` changes need step-up by a `tenant_owner` and approval by a second owner or `security_admin`; all owners are notified, and Nomology support leads are notified so they know the new mode.
- Raising `access.bulk.approval_threshold_rows` (weakening) is maker-checker; lowering is a direct change.
- Rollback: publish the previous version through [[APP-admin-change-history]] (tenant keys) or the platform history page (platform keys).
- Audit record: key, scope, old and new value, actor, approver, reason, ticket reference, `via`, effective time ([[PKG-audit-trail]] event `admin.settings.published`).

<!-- section:migration -->
## Versioning and migration

Keys are registered in `packages/settings/registry/platform-ops.ts` and never reused. Renames keep an alias for two releases. Contract-derived tenant values (`platform.lifecycle.*`) are migrated from the existing `tenant.offboarding_export_until` / `delete_after` columns at the time offboarding starts; the tenant row keeps the concrete dates. Tenant blueprints carry the tenant-scope keys of this catalogue (`access.support.*`, `access.bulk.*`, `access.admin.*`) in their configuration package ([[PKG-configuration-packages]]); platform and region keys never travel in tenant packages.

<!-- section:testing -->
## Testing

Resolver tests for every key: default only; region override; tenant override within bound; tenant override outside bound (rejected); platform lock (lower values ignored and shown as locked); entitlement missing (platform default applies). Specific tests: provisioning blocked when the region is closed; standing consent rejected when locked off; support grant duration clamped to the tenant value; bulk thresholds trigger step-up and approval at the boundary values. CI compares this catalogue with the registry and fails on any difference ([[PKG-settings-catalogue]]).

<!-- section:questions -->
## Open questions

- [ ] Default `access.support.consent_mode` for the CORD tenant: is `standing_config_read` acceptable given Nomology operates CORD? (legal)
- [ ] `platform.support.session_recording`: required for `case_read` and break-glass sessions? (security)
- [ ] Should `access.support.*` and `access.bulk.*` move to [[PKG-settings-access-control]] for one place to find all `access.*` keys? Proposed: stay here, referenced there. (authz group)
- [ ] Maintenance windows per region: confirm with tenants that hold hearings on Sunday mornings in the US region. (regional ops)
- [ ] Export window and deletion defaults per tenant type (proposed values above) against standard contracts. (account management, legal)

<!-- checks -->
## Template checks

<!-- check:inheritance -->
### Inheritance and locks

Each key lists its scopes and lockability; resolution follows [[PKG-configuration-scope-hierarchy]] with no exceptions. Contract values at tenant scope are set by platform staff and shown read-only to tenants with their source. Locking a support or bulk bound clamps tenant values at the bound and notifies the tenant's owners.

<!-- check:permissions -->
### Who may change what

Platform and region keys need `settings.platform:write` (platform keys: `platform_admin`; region keys: `regional_ops` for their own region) and maker-checker; per-tenant contract values need `platform.tenant:update` or `settings.platform:write` (`platform_billing`); support consent, bulk and admin governance keys now live in [[PKG-settings-access-control]] (`settings.access:write`; support consent needs `support.consent:configure`, held only by `tenant_owner`). No tenant role can change any `platform.*` key.

<!-- check:safety -->
### Safe bounds

Hard bounds cap support durations, request expiry, bulk sizes and thresholds; owner notification on privileged grants is locked on; the reason requirement cannot drop below security and legal changes; provisioning cannot happen in a region without legal sign-off.

<!-- check:timing -->
### When changes take effect

Each key states when it applies; support and bulk keys apply to new grants and jobs, never to running ones; lifecycle keys apply at the next invitation or offboarding; console session keys apply on the next request or sign-in.

<!-- check:audit -->
### Audit and rollback

All changes are `admin.settings.published` events with old and new values, scope, actor, approver and reason, and are versioned so the value in force at any date can be reproduced; rollback publishes a previous version.

<!-- check:sync -->
### Catalogue matches code

Generated from `packages/settings/registry/platform-ops.ts`; CI fails if this table and the registry differ or a key lacks owner, default, scopes or audit class.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Requests expire if they are not approved within 12 hours.",
    "id": "R1",
    "kind": "vendor",
    "title": "Microsoft Purview Customer Lockbox",
    "url": "https://learn.microsoft.com/purview/customer-lockbox-requests",
    "vendor": "Microsoft"
  }
]
```

<!-- end -->
