---
id: "MT-rls-enabled-and-forced-on"
title: "Forced RLS on tenant tables"
parent: "MT-isolation-strategy"
order: 3
type: "feature"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "RLS enabled and **forced** on all tenant tables; policy: `tenant_id = current_setting('app.tenant_id')::uuid`"
links: []
rev: 3
syncHash: "e7e8f320a0482600"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 3.3.3 Forced RLS on tenant tables

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> RLS enabled and **forced** on all tenant tables; policy: `tenant_id = current_setting('app.tenant_id')::uuid`

<!-- section:statement -->
## Statement

Every tenant-owned table shall have row-level security enabled and forced, and a permissive policy `tenant_isolation` for all commands for roles `nomo_app` and `nomo_worker` with `USING (tenant_id = app.current_tenant_id())` and `WITH CHECK (tenant_id = app.current_tenant_id())`, where `app.current_tenant_id()` returns `nullif(current_setting('app.tenant_id', true), '')::uuid`.

<!-- section:rationale -->
## Rationale and source

Enabling RLS without forcing it lets the table owner bypass policies; forcing it applies the policies to the owner too, while superusers and `BYPASSRLS` roles still bypass [R1]. `USING` filters rows read, updated and deleted; `WITH CHECK` stops inserts and updates that would place a row in another tenant [R2]. Using `nullif(..., '')` makes an unset or cleared setting compare as NULL, so the policy fails closed (no rows) instead of erroring or matching. Source: [[ADR-tenant-isolation]], ISO-SR-1 in [[MT-isolation-strategy#requirements]].

<!-- section:acceptance -->
## Acceptance criteria

- **Given** every table classified tenant-owned, **when** the catalogue test runs, **then** `pg_class.relrowsecurity` and `relforcerowsecurity` are true and `pg_policies` contains `tenant_isolation` with command `ALL`, roles `{nomo_app,nomo_worker}` and the exact expressions.
- **Given** context tenant A, **when** selecting from `cases`, **then** only tenant A rows are returned.
- **Given** context tenant A, **when** inserting a row with `tenant_id` = B, **then** Postgres raises `new row violates row-level security policy`.
- **Given** no context, **when** selecting, **then** zero rows are returned; **when** inserting, **then** the insert fails.
- **Given** a session as `nomo_owner` (via the migrator), **when** selecting without context, **then** zero rows are returned (forced).

<!-- section:verification -->
## Verification method

Test: `rls-coverage.spec.ts` (catalogue) and `isolation/*.spec.ts` (behaviour), every pull request; nightly catalogue check against each regional production database.

<!-- section:priority -->
## Priority

Must. Phase 0.

<!-- section:questions -->
## Open questions

- [ ] Should `app.current_tenant_id()` raise an error instead of returning NULL when context is missing, to make bugs louder? Proposed: no (fail closed quietly in SQL; the package raises the error before the query).

<!-- section:notes -->
## Notes

Tables with extra visibility rules (for example tribunal-only documents) add `AS RESTRICTIVE` policies on top; they may narrow but never replace `tenant_isolation`.

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Yes. This is the hard isolation boundary of the platform.

<!-- check:unambiguous -->
### Unambiguous

Gives exact SQL expressions, roles and commands; the catalogue test compares against them literally.

<!-- check:verifiable -->
### Verifiable

Catalogue test plus behaviour tests including the no-context and forced-owner negative cases.

<!-- check:consistent -->
### Consistent

Same helper and policy as [[MT-isolation-strategy#policy]] and [[MT-prisma-migrations-include-rls]].

<!-- check:traced -->
### Traced

From [[ADR-tenant-isolation]]; forward to migrations and the two test files.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Table owners normally bypass row security unless the table has FORCE ROW LEVEL SECURITY; superusers and roles with BYPASSRLS always bypass it. If no policy exists, a default-deny policy is used.",
    "id": "R1",
    "kind": "vendor",
    "title": "PostgreSQL documentation: Row Security Policies",
    "url": "https://www.postgresql.org/docs/current/ddl-rowsecurity.html",
    "vendor": "PostgreSQL Global Development Group"
  },
  {
    "excerpt": "USING expressions filter existing rows; WITH CHECK expressions are applied to rows being inserted or updated.",
    "id": "R2",
    "kind": "vendor",
    "title": "PostgreSQL documentation: CREATE POLICY",
    "url": "https://www.postgresql.org/docs/current/sql-createpolicy.html",
    "vendor": "PostgreSQL Global Development Group"
  }
]
```

<!-- end -->
