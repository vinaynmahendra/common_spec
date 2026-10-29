---
id: "ADR-orm"
title: "ORM"
parent: "ADR"
order: 3
type: "decision"
template: "adr"
status: "approved"
owner: null
indicative: false
summary: "Prisma"
links: []
rev: 2
syncHash: "97e3a26ad9b6cba4"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 19.3 ORM

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Prisma

<!-- section:context -->
## Context and problem

**Question:** which data access library do the Next.js app, Temporal activities and BullMQ workers use to talk to the regional Postgres, given that tenant isolation depends on a per-transaction setting ([[ADR-tenant-isolation]])?

Affected parts: [[PKG-data-access]], [[MT-prisma-implementation]], [[DEP-database-migration-strategy-zero]], [[INF-database-connection-handling]], and every domain schema node (for example [[DOM-cases-schema]], [[DOM-documents-schema]]).

<!-- section:drivers -->
## Decision drivers

- **D1 Tenant context per transaction** must be injectable in one place, not in every query.
- **D2 Type safety** end to end in a TypeScript strict monorepo ([[FND-language-and-conventions]]).
- **D3 Migrations** that can carry raw SQL (RLS policies, partial indexes, exclusion constraints for hearing overlaps in [[DOM-hearings-schema]]).
- **D4 Works behind PgBouncer transaction pooling** ([[INF-pgbouncer]]).
- **D5 Team familiarity and hiring**, and existing CORD / TERES experience.
- **D6 Escape hatch** for reporting-style SQL without losing tenant context.

<!-- section:decision -->
## Decision

**Prisma.**

Prisma Client is the only way application code reads or writes the regional Postgres. A Prisma Client extension ([[MT-prisma-client-extension-wraps]]) wraps every operation in a transaction that first runs `set_config('app.tenant_id', <id>, true)`; Prisma Migrate owns schema changes and each migration may include raw SQL for RLS policies ([[MT-prisma-migrations-include-rls]]). Complex read queries use `$queryRaw` through the same extension, so they still run inside the tenant transaction.

Chosen because it gives the strongest generated types (D2), a single extension point for tenant context (D1), migrations that accept raw SQL (D3), and it is already known to the team (D5).

<!-- section:consequences -->
## Consequences

**Easier:** typed models shared across app and workers; one extension enforces tenant context; schema reviews happen on `schema.prisma` plus migration SQL.

**Harder:**

- Every request pays for an explicit transaction. Interactive transactions hold a pooled connection for their full duration, so long ones are banned in request paths ([[INF-timeouts-on-connect-query-and]]).
- Prisma's schema language does not express RLS, exclusion constraints or some index types; those live in raw SQL and must be kept in sync by review and by the CI schema check.
- Connection pool size per container must be small and fixed ([[INF-small-fixed-prisma-pool-per]]).
- Behaviour behind PgBouncer has to be pinned and tested per upgrade. Prisma's current guidance is transaction mode, and with PgBouncer 1.21.0 or later not to set `pgbouncer=true` but to enable `max_prepared_statements`; Prisma Migrate needs a direct (non-pooled) connection [R1]. Those settings go into [[INF-separate-connection-settings-for]].
- Generated client size and cold start add to container start-up time.

<!-- section:confirmation -->
## Confirmation

- ESLint rule blocks imports of `pg`, `postgres`, `knex` or other drivers outside `packages/data-access`.
- A test fails if a Prisma client is created without the tenant extension (the factory is the only export of `packages/data-access`).
- The CI schema check from [[ADR-tenant-isolation]] runs after `prisma migrate deploy` on a fresh database.
- A PgBouncer-in-the-loop integration test runs in CI with two concurrent tenants on one pooled connection and asserts no setting leaks.

<!-- section:options -->
## Options considered

| Option | D1 tenant context | D2 types | D3 raw SQL migrations | Verdict |
|---|---|---|---|---|
| **Prisma** | Client extension | Generated, strong | Yes | **Chosen** |
| Drizzle ORM | Possible via wrapper | Strong, SQL-like | Yes | Credible alternative; rejected for team familiarity and maturity of tooling at decision time |
| Kysely | Possible via plugin | Strong query builder | External migration tool | Rejected: more hand-written code, no schema-first model |
| TypeORM | Possible | Weaker | Yes | Rejected on type safety and maintenance history |

<!-- section:revisit -->
## When to revisit

- Prisma cannot run reliably behind our pooler with transaction-scoped settings after an upgrade.
- Measured per-request overhead of the transaction wrapper exceeds a proposed 20 ms at p95 in [[TST-performance-and-load-testing]].
- A major Prisma licensing or support change.

<!-- section:notes -->
## More information

**Open questions**

- [ ] Which Prisma major version and which driver adapter (`pg` via driver adapters or the default engine) do we standardise on, given pool settings move to the driver in newer versions?
- [ ] Is RDS Proxy ever used instead of PgBouncer? It pins sessions on `set_config`, so it would need its own validation ([[INF-pgbouncer]]).
- [ ] Agree the per-request overhead budget for the transaction wrapper.

<!-- checks -->
## Template checks

<!-- check:significance -->
### Significance

Significant because it is used by every service and the tenant isolation mechanism depends on it. It covers the relational store only; search, vector and object stores have their own clients.

<!-- check:consequences -->
### Consequences and costs

Downsides stated: explicit transaction per request, raw SQL kept in sync by review, small fixed pools, version-sensitive PgBouncer behaviour and client size. Follow-ups: PgBouncer spike, pool sizing in [[INF-small-fixed-prisma-pool-per]], timeouts in [[INF-timeouts-on-connect-query-and]].

<!-- check:reversibility -->
### Reversibility and revisit triggers

Medium cost. Keeping all data access inside `packages/data-access` repositories ([[PKG-data-access]]) means a later switch (for example to Drizzle) touches that package and the migration history, not domain code. Estimated one to three months depending on how much raw SQL has accumulated.

<!-- check:confirmation -->
### Confirmation

Blocking checks: restricted-imports lint rule, the client factory test, the post-migration RLS schema check, and the PgBouncer concurrency test in CI.

<!-- check:linked -->
### Linked and lifecycle

Governs [[PKG-data-access]], [[MT-prisma-implementation]], [[APP-framework-dependencies]] (which lists Prisma as an approved core library). Related: [[ADR-tenant-isolation]]. Status: Approved.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "PgBouncer must run in transaction mode; with PgBouncer 1.21.0 or later do not set pgbouncer=true and set max_prepared_statements above 0; Prisma CLI / Migrate needs a direct connection.",
    "id": "R1",
    "kind": "vendor",
    "title": "Prisma ORM v7: Configure Prisma Client with PgBouncer",
    "url": "https://www.prisma.io/docs/orm/v7/prisma-client/setup-and-configuration/databases-connections/pgbouncer",
    "vendor": "Prisma"
  }
]
```

<!-- end -->
