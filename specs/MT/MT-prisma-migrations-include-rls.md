---
id: "MT-prisma-migrations-include-rls"
title: "RLS policies in migrations"
parent: "MT-prisma-implementation"
order: 4
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Every Prisma migration that creates or changes a tenant-owned table includes the RLS SQL (ENABLE, FORCE, policies, grants) in the same migration file"
links: []
rev: 3
syncHash: "36f9d18ec8481fd2"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 3.3.4.4 RLS policies in migrations

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Every Prisma migration that creates or changes a tenant-owned table includes the RLS SQL (ENABLE, FORCE, policies, grants) in the same migration file

<!-- section:statement -->
## Statement

When a Prisma migration creates a tenant-owned table, or changes a table's tenancy classification, the same migration file shall contain the raw SQL that enables and forces RLS, creates the `tenant_isolation` policy for every command, and grants only the privileges listed for that table in `tenancy-classification.yaml`.

<!-- section:rationale -->
## Rationale and source

Prisma Migrate does not generate RLS, policies or grants, but migration files are SQL that can be edited before they are applied [R1]. Keeping policies in the same file as the table removes any window in which a tenant table exists without protection, and makes the migration history the single source of truth for the database's security state.

<!-- section:acceptance -->
## Acceptance criteria

- **Given** a pull request whose migration creates table `hearing_session` classified as tenant-owned, **when** CI runs, **then** the migration contains `ENABLE ROW LEVEL SECURITY`, `FORCE ROW LEVEL SECURITY` and `CREATE POLICY tenant_isolation` for that table, and the catalogue test passes after applying it.
- **Given** the same pull request with the RLS lines removed, **when** CI runs, **then** the build fails naming the table.
- **Given** a fresh database, **when** all migrations are applied, **then** the catalogue matches the classification file exactly.

<!-- section:verification -->
## Verification method

Test: `rls-coverage.spec.ts` after `prisma migrate deploy` on an empty database in CI. Inspection: migration lint ([[MT-lint-review-check-that-every]]). Template: `packages/db/templates/tenant-table.sql` is copied by `pnpm db:new-tenant-table <name>`.

<!-- section:priority -->
## Priority

Must. Phase 0.

<!-- section:questions -->
## Open questions

- [ ] Should policies be declared once in a YAML/TS manifest and rendered into migrations (less hand-written SQL), or stay hand-written with lint (proposed for Phase 1)?

<!-- section:notes -->
## Notes

Standard block appended by the generator:

```sql
ALTER TABLE "hearing_session" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "hearing_session" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "hearing_session" FOR ALL TO nomo_app, nomo_worker
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());
GRANT SELECT, INSERT, UPDATE ON "hearing_session" TO nomo_app, nomo_worker;
```

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Yes; otherwise new tables are created without RLS and rely on a later fix.

<!-- check:unambiguous -->
### Unambiguous

Names the exact statements, the same-file rule and the trigger (create or reclassify).

<!-- check:verifiable -->
### Verifiable

CI applies migrations and runs the catalogue test; the negative case (lines removed) fails the build.

<!-- check:traced -->
### Traced

Traces to [[ADR-tenant-isolation]] and [[MT-rls-enabled-and-forced-on]]; forward to the generator template and the catalogue test.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Migration files are SQL and can be edited before they are applied, to add SQL that Prisma does not generate.",
    "id": "R1",
    "kind": "vendor",
    "title": "Prisma documentation: Customizing migrations",
    "url": "https://www.prisma.io/docs/orm/prisma-migrate/workflows/customizing-migrations",
    "vendor": "Prisma"
  }
]
```

<!-- end -->
