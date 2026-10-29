---
id: "MT-lint-review-check-that-every"
title: "RLS check for new tables"
parent: "MT-safeguards"
order: 2
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Lint / review check that every new tenant table has `tenant_id` + RLS policy"
links: []
rev: 3
syncHash: "6abdbd81e931dd0f"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 3.3.5.2 RLS check for new tables

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Lint / review check that every new tenant table has `tenant_id` + RLS policy

<!-- section:statement -->
## Statement

When a pull request adds or changes a table, view, function or trigger in the Prisma schema or migrations, CI shall fail unless the object is classified in `tenancy-classification.yaml`, every tenant-owned table carries `tenant_id` and the RLS block, every view on tenant tables uses `security_invoker = true`, and every `SECURITY DEFINER` function is listed in `security-definer-register.yaml`; and the pull request shall require approval from the `packages/db` code owners.

<!-- section:rationale -->
## Rationale and source

Catching a missing policy before merge is cheaper and safer than finding it in production. Views run with their owner's privileges unless `security_invoker` is set, which could silently bypass RLS [R1]. Source: [[MT-safeguards]] SG-2.

<!-- section:acceptance -->
## Acceptance criteria

- **Given** a migration creating table `x` not in the classification file, **when** CI runs, **then** it fails with "table x is not classified".
- **Given** a tenant-owned table without `FORCE ROW LEVEL SECURITY`, **then** CI fails naming the table.
- **Given** `CREATE VIEW v AS SELECT ... FROM cases` without `security_invoker`, **then** CI fails.
- **Given** a new `SECURITY DEFINER` function not in the register, **then** CI fails.
- **Given** all checks pass, **when** no code owner has approved, **then** merge is blocked by branch protection.

<!-- section:verification -->
## Verification method

Inspection: `pnpm db:lint` (SQL parser over migration files plus Prisma DMMF) in CI; code host branch protection with CODEOWNERS ([[FND-governance]]). Canary fixture proves the lint fails on a bad migration.

<!-- section:priority -->
## Priority

Must. Phase 0.

<!-- section:questions -->
## Open questions

- [ ] Build the SQL lint in-house (parser such as `pgsql-ast-parser`) or apply migrations to a scratch database and inspect the catalogue only? Proposed: both; the catalogue check is authoritative, the parser gives earlier, clearer messages.

<!-- section:notes -->
## Notes

Complements the behavioural tests in [[MT-automated-tests-that-prove-one]]; the lint checks intent, the tests check behaviour.

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Yes; it blocks the most common isolation regression (a new table without RLS) before it reaches any environment.

<!-- check:unambiguous -->
### Unambiguous

Lists exact conditions and files; each failure message names the object.

<!-- check:verifiable -->
### Verifiable

Each condition has a failing fixture; branch protection settings can be inspected.

<!-- check:consistent -->
### Consistent

Matches [[MT-prisma-migrations-include-rls]] and ISO-SR-7 in [[MT-isolation-strategy#requirements]].

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "With security_invoker, access to underlying relations (including row security policies) is checked against the user of the view rather than the view owner.",
    "id": "R1",
    "kind": "vendor",
    "title": "PostgreSQL documentation: CREATE VIEW",
    "url": "https://www.postgresql.org/docs/current/sql-createview.html",
    "vendor": "PostgreSQL Global Development Group"
  }
]
```

<!-- end -->
