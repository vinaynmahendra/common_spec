---
id: "MT-every-tenant-owned-table-carries"
title: "Tenant ID on every tenant table"
parent: "MT-isolation-strategy"
order: 1
type: "feature"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Every tenant-owned table carries a non-null `tenant_id`, indexed (usually as the leading column in composite indexes)"
links: []
rev: 3
syncHash: "9c01fd896b34f7f9"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 3.3.1 Tenant ID on every tenant table

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Every tenant-owned table carries a non-null `tenant_id`, indexed (usually as the leading column in composite indexes)

<!-- section:statement -->
## Statement

Every tenant-owned table shall have a column `tenant_id uuid NOT NULL REFERENCES tenant(id)`, shall use `(tenant_id, id)` as its primary key, shall include `tenant_id` in every foreign key to another tenant-owned table and in every unique constraint on business values, and shall have `tenant_id` as the leading column of its composite indexes unless an index review records a reason not to.

<!-- section:rationale -->
## Rationale and source

`tenant_id` is the key RLS compares against ([[MT-rls-enabled-and-forced-on]]). Composite keys and foreign keys make cross-tenant references impossible at the database level; tenant-scoped unique constraints avoid both false conflicts between tenants and side-channel disclosure through constraint errors. Leading-column indexes keep RLS-filtered queries efficient. Source: [[ADR-tenant-isolation]], ISO-SR-5 and ISO-SR-6 in [[MT-isolation-strategy#requirements]].

<!-- section:acceptance -->
## Acceptance criteria

- **Given** any table classified as tenant-owned, **when** the catalogue test runs, **then** `tenant_id` exists, is `uuid`, `NOT NULL`, references `tenant(id)`, and is the first column of the primary key.
- **Given** a foreign key from a tenant-owned table to another tenant-owned table, **when** inspected, **then** it includes `tenant_id` on both sides.
- **Given** tenant A and tenant B, **when** both create a case with reference `ARB-2026-001`, **then** both succeed (unique is per tenant).
- **Negative**: **given** a document row in tenant A, **when** an insert sets `case_id` to a case of tenant B, **then** the insert fails with a foreign key violation.

<!-- section:verification -->
## Verification method

Test: catalogue checks in `rls-coverage.spec.ts` (columns, PK, FK, unique constraints, index leading column with an allow-list for exceptions). Inspection: schema review.

<!-- section:priority -->
## Priority

Must. Phase 0 for the convention, every phase for each new table.

<!-- section:questions -->
## Open questions

- [ ] Should high-volume tables (audit events, notification deliveries) be list- or hash-partitioned by `tenant_id` to make tenant deletion cheap? Owner: [[PKG-audit-log-schema]] and [[INF-database]].

<!-- section:notes -->
## Notes

Exceptions to the leading-column rule (for example a global lookup by random token hash) are recorded in `tenancy-classification.yaml` with the reason. Partitioned tables (for example audit events) include `tenant_id` in the partition key or in every partition's primary key.

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Yes. RLS needs the column; composite keys prevent cross-tenant references that RLS alone does not stop on writes with forged ids.

<!-- check:singular -->
### Singular

It states the shape of the tenant key on tenant tables. Several facets (column, PK, FK, unique, index) are all aspects of that one convention and are checked by one test.

<!-- check:verifiable -->
### Verifiable

The catalogue test checks each facet; the forged-reference insert is the negative test.

<!-- check:consistent -->
### Consistent

Matches the schema conventions in [[MT-tenancy-and-identity-schema#keys]].

<!-- end -->
