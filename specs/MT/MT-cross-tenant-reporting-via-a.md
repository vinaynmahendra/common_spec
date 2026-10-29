---
id: "MT-cross-tenant-reporting-via-a"
title: "Cross-tenant reporting role"
parent: "MT-safeguards"
order: 3
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Cross-tenant reporting via a read-only reporting role or warehouse, never from the app role"
links: []
rev: 3
syncHash: "19d963c4a271afe6"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 3.3.5.3 Cross-tenant reporting role

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Cross-tenant reporting via a read-only reporting role or warehouse, never from the app role

<!-- section:statement -->
## Statement

Cross-tenant reads for platform reporting shall be performed only by the reporting service using the read-only role `nomo_reporting` on the regional read replica or the regional warehouse, and only through curated `reporting.*` views that exclude free-text case content and apply a minimum cohort size of 5 tenants (proposed) to any aggregate shown outside Nomology; the application roles shall never be used for cross-tenant queries.

<!-- section:rationale -->
## Rationale and source

Platform statistics ([[RPT-platform-stats]]), internal MIS and industry reports ([[RPT-industry-marketing]]) need data from many tenants. Doing that from the app role would require bypassing RLS in the runtime; a separate read-only role on a replica keeps the runtime unable to span tenants and keeps reporting load off the primary. Source: [[MT-safeguards]] SG-3, [[RPT-report-infrastructure]].

<!-- section:acceptance -->
## Acceptance criteria

- **Given** `nomo_reporting`, **when** it selects from a base tenant table, **then** permission is denied; **when** it selects from `reporting.case_counts_by_tenant`, **then** rows for all tenants of that region are returned.
- **Given** `nomo_reporting`, **when** it attempts INSERT, UPDATE, DELETE or DDL, **then** it is denied (replica is read-only and the role has no write grants).
- **Given** an external-facing aggregate with fewer than 5 contributing tenants, **when** generated, **then** the value is suppressed.
- **Given** the app roles, **when** inspected, **then** they have no grant on `reporting.*`.
- **Given** a tenant-facing dashboard, **when** a tenant admin views it, **then** it is served through the app role with RLS (not through `nomo_reporting`).

<!-- section:verification -->
## Verification method

Test: grants test per region; cohort suppression unit tests in the reporting service; inspection of view definitions in review.

<!-- section:priority -->
## Priority

Must for Phase 7 (reporting); the grant restrictions from Phase 1.

<!-- section:questions -->
## Open questions

- [ ] Minimum cohort size for external aggregates (5 proposed); owner: CCO with legal.
- [ ] Warehouse technology per region (Postgres replica only in Phase 7, or a columnar store) — see [[RPT-report-infrastructure]].

<!-- section:notes -->
## Notes

Views in schema `reporting` are owned by `nomo_reporting_owner` (`NOLOGIN`, `BYPASSRLS`) and created without `security_invoker`, so they deliberately read across tenants; that makes their definitions security-sensitive and they are listed in the classification file with a security reviewer as code owner. Warehouse loads stay in-region; cross-region platform totals are combined from per-region aggregates only, never row-level data.

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Yes; without it the first cross-tenant report would push someone to use privileged or app credentials.

<!-- check:complete -->
### Complete and scoped

Covers role, location (replica / warehouse in region), allowed objects, prohibited writes, external aggregate suppression and the tenant-facing distinction.

<!-- check:verifiable -->
### Verifiable

Grants tests and cohort tests are pass/fail.

<!-- check:consistent -->
### Consistent

Consistent with the reporting row of [[MT-isolation-strategy#matrix]] and residency rules in [[MT-data-residency-2]].

<!-- end -->
