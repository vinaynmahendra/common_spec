---
id: "MT-platform-level-tables"
title: "Platform-level tables"
parent: "MT-isolation-strategy"
order: 2
type: "feature"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Platform-level tables (tenants registry, plans, platform settings) have no `tenant_id` and no tenant RLS"
links: []
rev: 3
syncHash: "6a15676dbb4c8477"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 3.3.2 Platform-level tables

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Platform-level tables (tenants registry, plans, platform settings) have no `tenant_id` and no tenant RLS

<!-- section:statement -->
## Statement

Tables classified as platform-level (tenant registry, tenant domains, plans, platform settings, shared reference data) shall have no tenant RLS policy and no `tenant_id` used as an isolation key, shall hold no case data, and shall be writable by `nomo_app` only inside `withPlatformContext` for tables listed as platform-writable.

<!-- section:rationale -->
## Rationale and source

Some data is genuinely global within a region: the list of tenants, plans, countries and currencies. Forcing a tenant key on them would be meaningless and would hide them from middleware and provisioning. Keeping them few, case-data-free and write-restricted limits what an error in platform context can expose. Source: [[ADR-tenant-isolation]].

<!-- section:acceptance -->
## Acceptance criteria

- **Given** `tenancy-classification.yaml`, **when** the catalogue test runs, **then** every platform-level table is listed with an owner and a reason, and none has a column classified as case data.
- **Given** a tenant context, **when** code tries to update `plan`, **then** Postgres rejects it (no UPDATE grant outside platform context; checked via `app.context_kind = 'platform'` in a policy or a separate grant).
- **Given** a proposal to store personal data in a platform-level table, **when** reviewed, **then** it requires an explicit policy (as for `user_account` in [[MT-tenancy-and-identity-schema#tenancy]]) and security approval.

<!-- section:verification -->
## Verification method

Test: catalogue test and grants test. Inspection: classification review in pull requests.

<!-- section:priority -->
## Priority

Must. Phase 1.

<!-- section:questions -->
## Open questions

- [ ] Do reference tables that tenants can extend (for example tenant-specific holiday calendars) need a split into a platform part and a tenant-owned part? Proposed: yes, `holiday_calendar` (platform) plus `tenant_holiday` (tenant-owned), see [[PKG-calendars-and-deadline]].

<!-- section:notes -->
## Notes

Initial platform-level list: `tenant`, `tenant_domain`, `plan`, `platform_setting`, `feature_flag_definition`, reference tables (`country`, `currency`, `language`, `holiday_calendar`). `user_account` and `user_identity` are platform-level but protected by membership policies, so they are a documented special case, not ordinary platform tables.

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Yes; without a rule, platform tables become a quiet place to store tenant data without RLS.

<!-- check:complete -->
### Complete and scoped

Covers classification, write restrictions, the personal-data exception and the review route.

<!-- check:verifiable -->
### Verifiable

Catalogue and grants tests are pass/fail.

<!-- check:consistent -->
### Consistent

Consistent with [[MT-tenancy-and-identity-schema]] and [[MT-isolation-strategy#matrix]].

<!-- end -->
