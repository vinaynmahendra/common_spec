---
id: "MT-prisma-client-extension-wraps"
title: "Transaction-scoped tenant context"
parent: "MT-prisma-implementation"
order: 1
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Prisma Client extension wraps each request in a transaction and runs `set_config('app.tenant_id', <id>, true)` first, so the setting is scoped to that transaction only (safe with PgBouncer transaction pooling)"
links: []
rev: 3
syncHash: "2dbe73d02328d7f5"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 3.3.4.1 Transaction-scoped tenant context

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Prisma Client extension wraps each request in a transaction and runs `set_config('app.tenant_id', <id>, true)` first, so the setting is scoped to that transaction only (safe with PgBouncer transaction pooling)

<!-- section:statement -->
## Statement

When application code reads or writes tenant data, `@nomology/db` shall run the work inside a single database transaction whose first statement is `SELECT set_config('app.tenant_id', <tenantId>, true)` (together with `app.user_id` and `app.request_id`), and shall never set tenant context per session, so that the setting ends with the transaction and cannot carry over to another request on the same pooled connection.

<!-- section:rationale -->
## Rationale and source

RLS policies read `app.tenant_id` ([[MT-rls-enabled-and-forced-on]]). Behind PgBouncer in transaction pooling mode, consecutive transactions from different requests share server connections; session-level `SET` would leak one tenant's context into another's transaction, while transaction-local settings are compatible with transaction pooling [R1]. Prisma Client extensions provide the hook to wrap queries [R2]. Source: [[ADR-tenant-isolation]], [[INF-pgbouncer]].

<!-- section:acceptance -->
## Acceptance criteria

- **Given** a request for tenant A, **when** a tRPC procedure calls `withTenant(tx => tx.case.findMany())`, **then** the database log shows `BEGIN`, the `set_config` call with tenant A's id, the query and `COMMIT`, in that order, on one server connection.
- **Given** a pool limited to one server connection, **when** transactions for tenants A and B alternate 1,000 times, **then** each transaction reads only its own `app.tenant_id` and no rows of the other tenant.
- **Given** a transaction for tenant A has committed, **when** the next transaction on that connection runs without `withTenant`, **then** `current_setting('app.tenant_id', true)` returns an empty string and tenant tables return zero rows.
- **Given** no tenant context, **when** `withTenant` is called, **then** it throws `TenantContextMissingError` and sends no query.
- **Negative**: **given** any source file outside `packages/db/src/internal`, **when** it contains `SET app.` or `set_config(` with `false`, **then** lint fails the build.

<!-- section:verification -->
## Verification method

Test: `packages/db/test/tenant-context.spec.ts` and the PgBouncer leak test in CI (real PgBouncer in transaction mode, Docker Compose). Inspection: ESLint rule `nomology/no-session-config`. Both run on every pull request touching `packages/db/**`.

<!-- section:priority -->
## Priority

Must. Phase 0 (skeleton) and Phase 1 (complete).

<!-- section:questions -->
## Open questions

- [ ] Folded from the merged item "Tenant context set per transaction only": now part of the statement above. Remove the merged note once reviewed.
- [ ] Should nested `withTenant` calls join the outer transaction (proposed) or be rejected?

<!-- section:notes -->
## Notes

Settings use the `app.` prefix (a custom GUC namespace). Values are passed as bind parameters, never interpolated. `app.user_id` and `app.request_id` are consumed by audit triggers and the membership-based policies in [[MT-tenancy-and-identity-schema]].

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Yes. Without it, RLS has no tenant to compare against, or worse, inherits a stale tenant from a pooled connection, which is a cross-tenant disclosure.

<!-- check:unambiguous -->
### Unambiguous

The exact statement, the `true` (local) flag and the ordering are specified, and the negative lint rule makes the session-level variant detectable.

<!-- check:feasible -->
### Feasible

Yes. Interactive transactions and Client extensions are supported by Prisma; transaction-local settings are supported by PgBouncer transaction pooling [R1]. Overhead is one extra statement per transaction.

<!-- check:verifiable -->
### Verifiable

The leak test with a single server connection is a pass/fail test of the core guarantee, and includes the negative case of a context-free transaction.

<!-- check:consistent -->
### Consistent

Matches [[MT-isolation-strategy#policy]] (helper `app.current_tenant_id()` with `nullif`) and [[INF-pgbouncer]].

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "In transaction pooling mode, SET / RESET and other session-level state are not supported; SET LOCAL (transaction-scoped) is compatible.",
    "id": "R1",
    "kind": "vendor",
    "title": "PgBouncer features (SQL feature map for pooling modes)",
    "url": "https://www.pgbouncer.org/features.html",
    "vendor": "PgBouncer"
  },
  {
    "excerpt": "Client extensions add query-level hooks ($allModels / $allOperations) and custom client methods.",
    "id": "R2",
    "kind": "vendor",
    "title": "Prisma documentation: Prisma Client extensions",
    "url": "https://www.prisma.io/docs/orm/v7/prisma-client/client-extensions",
    "vendor": "Prisma"
  }
]
```

<!-- end -->
