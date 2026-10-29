---
id: "MT-automated-tests-that-prove-one"
title: "Cross-tenant isolation tests"
parent: "MT-safeguards"
order: 1
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Automated tests that prove one tenant cannot read or write another tenant's rows, including when `tenant_id` is missing from a query"
links: []
rev: 3
syncHash: "3eabd601abc15bb6"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 3.3.5.1 Cross-tenant isolation tests

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Automated tests that prove one tenant cannot read or write another tenant's rows, including when `tenant_id` is missing from a query

<!-- section:statement -->
## Statement

The platform shall have an automated isolation test suite, run on every pull request and nightly, that proves for every tenant-owned table, every tRPC router, every public API route family, every job and workflow family and every derived store (search, cache, vectors, object storage) that a caller in tenant A's context cannot read, list, update, delete or reference tenant B's data, including when the query omits any `tenant_id` filter and when no tenant context is set.

<!-- section:rationale -->
## Rationale and source

RLS and the Prisma wrapper are only as good as their coverage. Tests driven by a declared matrix of actors, resources and expected outcomes are the recommended way to keep authorization coverage complete [R1]. Source: [[MT-safeguards]] SG-1, [[PLAN]] (isolation tests are cross-cutting from Phase 0), [[TST-multi-tenant-isolation-tests]].

<!-- section:acceptance -->
## Acceptance criteria

- **Given** two seeded tenants (`acia` arbitral institution, `odr-alpha` SEBI ODR institution) with rows in every tenant table, **when** the database layer suite runs `findMany()` with no `where` clause in tenant A's context for every Prisma model, **then** every returned row has tenant A's id.
- **Given** a case id of tenant B, **when** a tenant A user calls `cases.get`, `documents.list` or `GET /api/v1/cases/{id}`, **then** the response is the same not-found response as for a random id.
- **Given** tenant A's context, **when** any model's `update`, `delete` or `create` targets tenant B's ids or `tenant_id`, **then** zero rows are affected or an RLS / FK error occurs.
- **Given** no tenant context, **when** any model is queried at the SQL level, **then** zero rows are returned.
- **Given** a search query, cache read or vector retrieval in tenant A, **when** the index holds tenant B documents with the same terms, **then** none are returned.
- **Given** a new model or router without an entry in the isolation test matrix, **when** CI runs, **then** the build fails.

<!-- section:verification -->
## Verification method

Tests in `packages/db/test/isolation/` (database layer, generated from the Prisma DMMF so every model is covered automatically), `apps/web/test/isolation/` (tRPC and route handlers), `apps/workers-*/test/isolation/` (envelopes), and per-package isolation tests for search, cache and storage. Real Postgres and PgBouncer in CI. Results stored as evidence.

<!-- section:priority -->
## Priority

Must. Phase 0 (database layer), extended every phase as routers are added.

<!-- section:questions -->
## Open questions

- [ ] Should the nightly run also execute against a production-like anonymised dataset in staging (larger, realistic volumes)? Proposed: yes, in Phase 3.

<!-- section:notes -->
## Notes

The test matrix lives in `test/isolation/matrix.ts` and is the input to [[TST-multi-tenant-isolation-tests]].

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Yes; it is the behavioural evidence that isolation works and the main defence against drift.

<!-- check:complete -->
### Complete and scoped

Covers read, write, reference and missing-context cases across database, API, jobs and derived stores, and the failure when coverage is missing.

<!-- check:feasible -->
### Feasible

Generating the database-layer cases from Prisma's DMMF keeps the cost low as tables grow; API-level cases are added per router.

<!-- check:verifiable -->
### Verifiable

Each scenario is a deterministic pass/fail test; coverage is enforced by the matrix check.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Drive authorization tests from a declared matrix of roles, resources and expected outcomes.",
    "id": "R1",
    "kind": "web",
    "publisher": "OWASP",
    "title": "OWASP Authorization Testing Automation Cheat Sheet",
    "url": "https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Testing_Automation_Cheat_Sheet.html"
  }
]
```

<!-- end -->
