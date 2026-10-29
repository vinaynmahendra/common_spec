---
id: "MT-prisma-implementation"
title: "Prisma implementation"
parent: "MT-isolation-strategy"
order: 4
type: "feature"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "`@nomology/db`: the only way application code gets a Prisma client — tenant-scoped transactions, workload-specific database roles, RLS SQL in migrations"
links: []
rev: 2
syncHash: "a076cf8079b3a1de"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 3.3.4 Prisma implementation

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> `@nomology/db`: the only way application code gets a Prisma client — tenant-scoped transactions, workload-specific database roles, RLS SQL in migrations

<!-- section:purpose -->
## Purpose and scope

`@nomology/db` (in `packages/db`) is the single entry point to Postgres for every app and worker. It exists because Prisma has no built-in notion of tenant or RLS: the package makes the safe path (a transaction with tenant context set) the only path. It owns the Prisma schema, the generated client, the Client extension that sets tenant context, the connection configuration per workload, and the migration files including RLS SQL.

It does **not** contain domain repositories (those live in each domain package and use this one), tenant resolution ([[MT-tenant-resolution]]) or retention logic ([[PKG-data-retention-legal-hold-and]]). It is the implementation of [[PKG-data-access]]'s tenant context propagation for Postgres.

Children (each a requirement):

- [[MT-prisma-client-extension-wraps]] — transaction-scoped tenant context
- [[MT-app-connects-as-a-non]] — runtime roles cannot bypass RLS
- [[MT-separate-privileged-role-used]] — privileged migration and platform-ops roles
- [[MT-prisma-migrations-include-rls]] — RLS policies are written in migration SQL

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Use case |
|---|---|
| `apps/web` (RSC, tRPC routers, Server Actions, public API handlers) | Read and write tenant data for the resolved tenant: list cases for the secretariat queue, file a Statement of Claim |
| Temporal workers (`apps/workers-temporal`, task queues `cases`, `hearings`, `documents`, `ai-pipelines`, `billing`) | Activities that write domain state, for example recording that a notice was served |
| BullMQ workers (`apps/workers-jobs`) | Short jobs such as indexing a document or recording a webhook delivery attempt |
| Platform admin console ([[APP-platform-admin-and-support]]) | Platform-level tables (tenants, plans) in platform context |
| Tenant lifecycle workflow ([[MT-tenant-lifecycle]]) | Seeding a new tenant; offboarding deletion through `nomo_platform_ops` |
| CI | Migrations (`prisma migrate deploy`), RLS catalogue tests |

<!-- section:api -->
## Public API

```ts
// packages/db/src/index.ts — everything not exported here is internal
import type { Prisma, PrismaClient } from './generated';

export type TenantTx = Omit<Prisma.TransactionClient, '$executeRawUnsafe' | '$queryRawUnsafe'>;

export interface TxOptions {
  isolationLevel?: Prisma.TransactionIsolationLevel;   // default ReadCommitted
  timeoutMs?: number;                                  // default 10_000 (web), 60_000 (workers)
  readOnly?: boolean;                                  // sets transaction_read_only
}

/** Runs fn in one transaction with app.tenant_id, app.user_id, app.request_id set locally. */
export function withTenant<T>(fn: (tx: TenantTx) => Promise<T>, opts?: TxOptions): Promise<T>;
/** Same, with an explicit context (workers, tests). */
export function withTenantContext<T>(ctx: { tenantId: string; userId?: string; requestId?: string },
                                     fn: (tx: TenantTx) => Promise<T>, opts?: TxOptions): Promise<T>;

/** Platform-level tables only (tenant, tenant_domain, plan, platform_setting). Tenant tables return zero rows. */
export function withPlatformContext<T>(actor: { staffUserId: string; reason: string },
                                       fn: (tx: PlatformTx) => Promise<T>): Promise<T>;

/** Lazily created clients per workload; each uses its own role and pool (see Configuration). */
export function getDbHealth(): Promise<{ ok: boolean; latencyMs: number; pool: { inUse: number; idle: number; waiting: number } }>;

export class TenantContextMissingError extends Error {}
export class TenantTransactionTimeoutError extends Error {}
export class RlsViolationError extends Error { table: string }       // mapped from 42501 / "violates row-level security policy"
export class UniqueViolationError extends Error { constraint: string }
export class SerializationRetryExhaustedError extends Error {}
```

Not exported, by design: the base `PrismaClient`, `$executeRawUnsafe`, `$queryRawUnsafe`, and any client for `nomo_platform_ops` (available only from `@nomology/db/platform-ops`, importable only by `apps/workers-platform-ops`, enforced by Turborepo boundaries and ESLint).

<!-- section:usage -->
## Usage examples

```ts
// tRPC procedure: secretariat queue
import { withTenant } from '@nomology/db';

export const listQueue = secretariatProcedure.input(QueueInput).query(({ input }) =>
  withTenant((tx) => tx.case.findMany({
    where: { status: { in: input.statuses } },          // no tenantId needed; RLS applies
    orderBy: { nextDeadlineAt: 'asc' },
    take: 50,
  }), { readOnly: true }),
);
```

```ts
// Temporal activity: record service of a notice
export async function recordServiceEvent(input: { tenantId: string; noticeId: string; providerMessageId: string }) {
  return withTenantContext({ tenantId: input.tenantId, requestId: Context.current().info.activityId }, async (tx) => {
    const existing = await tx.serviceEvent.findUnique({ where: { tenantId_providerMessageId: { tenantId: input.tenantId, providerMessageId: input.providerMessageId } } });
    if (existing) return existing;                        // idempotent on retry
    return tx.serviceEvent.create({ data: { tenantId: input.tenantId, noticeId: input.noticeId, providerMessageId: input.providerMessageId } });
  });
}
```

```ts
// Error handling
try { await withTenant((tx) => tx.document.create({ data })); }
catch (e) {
  if (e instanceof RlsViolationError) throw new TRPCError({ code: 'FORBIDDEN' });     // never echo row values
  if (e instanceof UniqueViolationError) throw new TRPCError({ code: 'CONFLICT' });
  throw e;
}
```

<!-- section:tenant -->
## Tenant context

Tenant context enters through `@nomology/tenancy`'s AsyncLocalStorage (`getTenantContext()`), or explicitly through `withTenantContext` in workers. On every call the package opens an interactive Prisma transaction and runs, as its first statement:

```sql
SELECT set_config('app.tenant_id', $1, true),
       set_config('app.user_id',   $2, true),
       set_config('app.request_id', $3, true);
```

The third argument `true` makes each setting local to the transaction, so it disappears at COMMIT or ROLLBACK and cannot leak to the next client of a PgBouncer server connection [R1]. If no context is present, `withTenant` throws `TenantContextMissingError` before contacting the database. Even if a bug bypassed that check, RLS would return no rows ([[MT-rls-enabled-and-forced-on]]). Details and acceptance criteria: [[MT-prisma-client-extension-wraps]].

<!-- section:config -->
## Configuration

Connection settings per workload ([[INF-separate-connection-settings-for]]), all from the regional secrets manager:

| Workload | Role | Pool (`connection_limit`) | `statement_timeout` | `idle_in_transaction_session_timeout` | Through |
|---|---|---|---|---|---|
| Web (`apps/web`) | `nomo_app` | 5 per container (proposed) | 15 s | 20 s | PgBouncer (transaction mode) |
| Temporal / BullMQ workers | `nomo_worker` | 5 per container | 60 s | 60 s | PgBouncer |
| Platform ops worker | `nomo_platform_ops` | 2 | 300 s | 60 s | PgBouncer |
| Migrations | `nomo_migrator` | 1 | per file | — | Direct to primary (not PgBouncer) |
| Reporting | `nomo_reporting` | 3 | 120 s | 30 s | Read replica |

Timeouts are set as role defaults (`ALTER ROLE ... SET statement_timeout`) so they apply through the pooler [R2]; Prisma's `pgbouncer=true` is set on pooled URLs so Prisma does not rely on prepared statements across transactions. Pool sizes follow [[INF-small-fixed-prisma-pool-per]].

<!-- section:errors -->
## Error model

| Error | Cause | Retryable | Caller action |
|---|---|---|---|
| `TenantContextMissingError` | No tenant context | No | Bug; return 500 and alert |
| `RlsViolationError` | WITH CHECK failed (wrong `tenant_id` on insert / update) | No | 403; security event |
| `UniqueViolationError` | Constraint violation | No | 409 or idempotent return |
| `TenantTransactionTimeoutError` | Transaction exceeded `timeoutMs` | Yes, once | Retry in workers; surface 503 in web |
| `SerializationRetryExhaustedError` | Serializable transactions retried 3 times | No | Surface 409 / let Temporal retry the activity |
| Prisma `P1001` / connection errors | Pooler or database unavailable | Yes, with backoff | Workers rely on Temporal / BullMQ retries; web returns 503 |

<!-- section:nfr -->
## Performance and limits

- Overhead of the wrapper (transaction begin + `set_config` + commit) under 2 ms p95 within a region (proposed target, to be measured in [[TST-performance-and-load-testing]]).
- One transaction per tRPC procedure or activity; long-running work (bulk exports) uses batched transactions of at most 1,000 rows.
- Containers × pool size per region stays within PgBouncer `max_client_conn` and the database's `max_connections` budget ([[INF-pgbouncer]]).

<!-- section:versioning -->
## Versioning and compatibility

Prisma and `@prisma/client` versions are pinned in the root catalogue and upgraded together across the monorepo ([[APP-framework-dependencies]]). A Prisma upgrade must pass the full isolation suite and the PgBouncer compatibility test before merge, because extension and transaction behaviour can change between versions. Schema changes follow expand-and-contract ([[DEP-database-migration-strategy-zero]]).

<!-- section:testing -->
## Test contract

- Isolation suite ([[MT-automated-tests-that-prove-one]]) against a real Postgres with the same roles, through a real PgBouncer in transaction mode (Docker Compose in CI).
- Leak test: 1,000 alternating transactions for tenants A and B on a pool of 1 server connection; every transaction reads `current_setting('app.tenant_id', true)` first and must see only its own value, and a transaction without context must see an empty value.
- Catalogue test ([[MT-lint-review-check-that-every]]).
- Role test ([[MT-app-connects-as-a-non]]).

<!-- section:questions -->
## Open questions

- [ ] Interactive transactions for every call add round trips; is a batch-transaction mode (`$transaction([setConfig, query])`) worth offering for single-query reads? Proposed: no, keep one code path until measurements say otherwise.
- [ ] Confirm `pgbouncer=true` behaviour with the Prisma version chosen in [[APP-framework-dependencies]] (prepared statements support in PgBouncer 1.21+ may allow turning it off).
- [ ] Is RDS Proxy in scope for any region? If so it must pass the leak test above ([[INF-pgbouncer]]).

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

No exported function can run a tenant-table query without a tenant context: the base client is not exported, raw unsafe methods are removed from the transaction type, and `withTenant` throws before connecting if context is missing. The platform-ops client is in a separate entry point that only one app may import. RLS remains the backstop.

<!-- check:security -->
### Security of the API surface

Each workload connects with its own least-privilege role; credentials come from the regional secrets manager at start-up and are never logged. Raw SQL is allowed only through tagged-template `$queryRaw` (parameterised), and the ESLint rule bans `Prisma.raw` and `$queryRawUnsafe` outside `packages/db/src/internal`.

<!-- check:residency -->
### Region awareness

Each container connects only to its own region's database; the database URL is region-specific configuration, and `withTenantContext` checks the envelope region against `TENANCY_REGION` before connecting.

<!-- check:resilience -->
### Failure behaviour

Transient connection failures surface as typed retryable errors; workers rely on Temporal activity retries and BullMQ retries with backoff, and activities are written to be idempotent (natural keys or idempotency keys inside the same transaction). Timeouts at transaction, statement and idle-in-transaction level stop one stuck call from holding a pooled connection.

<!-- check:change-safety -->
### Change and release safety

CODEOWNERS on `packages/db/**` requires platform-core and security review; Prisma upgrades require the isolation suite and PgBouncer leak test to pass; migrations are applied region by region ([[DEP-environment-promotion-and-multi]]) with the previous application version still able to run.

<!-- check:testing -->
### Testing

Isolation suite, leak test, catalogue test and role test run on every pull request touching `packages/db/**`, any `schema.prisma` or any migration, and nightly on main.

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
    "excerpt": "statement_timeout, lock_timeout and idle_in_transaction_session_timeout settings.",
    "id": "R2",
    "kind": "vendor",
    "title": "PostgreSQL documentation: Client Connection Defaults",
    "url": "https://www.postgresql.org/docs/current/runtime-config-client.html",
    "vendor": "PostgreSQL Global Development Group"
  }
]
```

<!-- end -->
