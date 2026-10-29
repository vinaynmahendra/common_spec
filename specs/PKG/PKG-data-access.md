---
id: "PKG-data-access"
title: "Data access"
parent: "PKG"
order: 13
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "repositories, tenant context propagation, migrations, seed data"
links: []
rev: 3
syncHash: "9a630cc11ecebeed"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.13 Data access

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> repositories, tenant context propagation, migrations, seed data

<!-- section:purpose -->
## Purpose and scope

`@nomology/db` is the only way any app, Temporal worker or BullMQ worker talks to the regional Postgres database. It owns the single extended Prisma client, the tenant-scoped transaction wrapper, repository helpers, the transactional outbox, migrations (including raw SQL for RLS) and the loading of reference and seed data.

It exists so that the guarantees in [[MT-isolation-strategy]] are delivered by one piece of code instead of being re-implemented by each domain.

**Does not:**
- Decide who may see a row beyond tenant equality — case- and party-level filtering comes from [[PKG-authorization]] (`authz.where(...)`), which this package accepts as a Prisma `where` fragment.
- Run cross-tenant reports — those use the read-only reporting role or warehouse ([[MT-cross-tenant-reporting-via-a]], [[RPT-report-infrastructure]]).
- Own domain schemas — each domain owns its Prisma schema file and datamodel node (for example [[DOM-cases-schema]]); this package owns the mechanism, the shared conventions and the platform tables it needs (outbox, idempotency).

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Use case |
|---|---|
| Next.js Server Components and Server Actions (all route groups) | Read case lists and details inside `withTenant`, with `authz.where()` filters |
| tRPC routers ([[APP-internal-api-trpc-routers-per]]) | Mutations with optimistic concurrency (`version` column) and outbox events in one transaction |
| Temporal Activities (`cases`, `documents`, `billing` task queues) | Domain writes from long-running workflows, using tenant context from the Temporal interceptor |
| BullMQ workers (search indexing, notifications, webhooks) | Read the outbox and mark events dispatched |
| Platform admin jobs (tenant provisioning, retention sweeps) | Iterate tenants one at a time with `forEachTenant`, never with a bypass role |
| CI / deploy pipeline | `pnpm db:migrate` per region with the `nomo_migrator` role; reference data load ([[PKG-reference-and-seed-data]]) |

<!-- section:api -->
## Public API

```ts
// packages/db/src/index.ts  (server-only)
import type { Prisma, PrismaClient } from '@prisma/client';
import type { RequestContext } from '@nomology/tenant-context';

/** Run fn inside one Postgres transaction with app.tenant_id (and actor) set via set_config(..., true). */
export function withTenant<T>(fn: (tx: TenantTx) => Promise<T>, opts?: TxOptions): Promise<T>;
export function withTenant<T>(ctx: RequestContext, fn: (tx: TenantTx) => Promise<T>, opts?: TxOptions): Promise<T>;

export interface TxOptions {
  isolation?: 'ReadCommitted' | 'RepeatableRead' | 'Serializable'; // default ReadCommitted
  timeoutMs?: number;            // default 5_000 interactive, max 30_000
  readOnly?: boolean;            // SET TRANSACTION READ ONLY; routed to replica when replicaOk
  replicaOk?: boolean;           // allow read replica (stale up to replica lag)
}

/** Prisma transaction client limited to tenant-owned and reference models. */
export type TenantTx = Omit<Prisma.TransactionClient, '$executeRawUnsafe' | '$queryRawUnsafe'>;

/** Platform-level tables only (tenant registry, plans, platform settings). Throws if a tenant-owned model is touched. */
export function withPlatform<T>(reason: PlatformReason, fn: (tx: PlatformTx) => Promise<T>): Promise<T>;
export type PlatformReason = 'tenant-provisioning' | 'tenant-directory' | 'platform-settings' | 'reference-data';

/** Iterate tenants in this region, each in its own withTenant transaction. Used by sweeps, never by request code. */
export function forEachTenant(job: string, fn: (tenantId: string, tx: TenantTx) => Promise<void>,
  opts?: { concurrency?: number; filter?: (t: TenantSummary) => boolean }): Promise<ForEachReport>;

/** Optimistic concurrency: update where version = expected, bump version; throws ConcurrencyConflictError. */
export function updateVersioned<M extends VersionedModel>(tx: TenantTx, model: M,
  id: string, expectedVersion: number, data: UpdateInput<M>): Promise<Row<M>>;

/** Transactional outbox: written in the caller's transaction; dispatched by the outbox relay (BullMQ). */
export function enqueueOutbox(tx: TenantTx, evt: OutboxEvent): Promise<void>;
export interface OutboxEvent {
  topic: OutboxTopic;            // 'search.index' | 'webhook.deliver' | 'notification.send' | 'retention.evaluate' | ...
  aggregate: { type: string; id: string };
  payload: unknown;              // validated by the topic's zod schema; identifiers only, no document content
  dedupeKey: string;             // unique per tenant + topic
}

/** Idempotency store for public API and Server Actions (see APP-api-versioning-rate-limiting). */
export function withIdempotency<T>(tx: TenantTx, key: string, scope: string,
  requestHash: string, fn: () => Promise<T>): Promise<IdempotentResult<T>>;

/** Typed errors */
export class TenantContextMissingError extends Error {}
export class TenantMismatchError extends Error {}
export class ConcurrencyConflictError extends Error { readonly currentVersion: number }
export class UniqueViolationError extends Error { readonly constraint: string }
export class ForeignKeyViolationError extends Error { readonly constraint: string }
export class SerializationRetryableError extends Error {}
export class DbUnavailableError extends Error {}
```

Repository convention (not an export, a pattern every domain follows): one `*.repo.ts` per aggregate root, functions take `TenantTx` as the first argument, return plain objects, and never call `withTenant` themselves so callers control transaction boundaries.

<!-- section:usage -->
## Usage examples

```ts
// Server Action: file a response document and notify, atomically
import { withTenant, updateVersioned, enqueueOutbox, ConcurrencyConflictError } from '@nomology/db';
import { authz } from '@nomology/authz';
import { audit } from '@nomology/audit';

export async function submitResponse(input: SubmitResponseInput) {
  return withTenant(async (tx) => {
    await authz.assert(tx, 'case.filing.submit', { type: 'case', id: input.caseId });
    try {
      const filing = await updateVersioned(tx, 'filing', input.filingId, input.version, { status: 'SUBMITTED' });
      await audit.record(tx, { action: 'filing.submitted', target: { type: 'filing', id: filing.id } });
      await enqueueOutbox(tx, {
        topic: 'notification.send', aggregate: { type: 'filing', id: filing.id },
        payload: { template: 'filing.submitted', filingId: filing.id },
        dedupeKey: `filing.submitted:${filing.id}:${filing.version}`,
      });
      return filing;
    } catch (e) {
      if (e instanceof ConcurrencyConflictError) return { conflict: true, currentVersion: e.currentVersion };
      throw e;
    }
  });
}
```

```ts
// Temporal Activity: context arrives from the interceptor, so the one-argument form is used
export async function markHearingScheduled(hearingId: string) {
  return withTenant((tx) => tx.hearing.update({ where: { id: hearingId }, data: { status: 'SCHEDULED' } }));
}
```

```ts
// Nightly sweep in a platform job (one transaction per tenant, never a bypass role)
await forEachTenant('retention-evaluate', async (tenantId, tx) => {
  await retention.evaluateDue(tx);
}, { concurrency: 4 });
```

<!-- section:tenant -->
## Tenant context

- Tenant context enters through `@nomology/tenant-context` (AsyncLocalStorage), populated by Next.js middleware after tenant resolution ([[MT-tenant-resolution]]), by the Temporal client and worker interceptors ([[WF-separation-of-concerns-temporal#guardrails]]) and by the BullMQ job wrapper (job data carries a signed `ctx` envelope: `tenantId`, `region`, `actor`, `traceparent`).
- `withTenant` opens a Prisma interactive transaction and runs, as the first statements, `select set_config('app.tenant_id', $1, true), set_config('app.actor_id', $2, true), set_config('app.request_id', $3, true)`. The third argument `true` scopes the values to the transaction, which is what makes this safe on PgBouncer transaction pooling ([[MT-prisma-client-extension-wraps]], [[INF-pgbouncer]]).
- The application connects as `nomo_app` (web) or `nomo_worker` (Temporal and BullMQ workers), non-owner roles without `BYPASSRLS` ([[MT-app-connects-as-a-non]]). All tenant tables have RLS enabled and forced ([[MT-rls-enabled-and-forced-on]]); the policies use `current_setting('app.tenant_id', true)::uuid`, so an unset value yields NULL and matches no rows.
- Missing context: `withTenant` throws `TenantContextMissingError` before opening a connection; the error is logged with request ID and counted in `db.tenant_context.missing`. Passing a `ctx` whose tenant differs from the ambient context throws `TenantMismatchError` (also alerting).
- Prisma calls made outside `withTenant` on tenant models are blocked by a client extension that throws `TenantContextMissingError` — there is no "default" connection that runs queries without the setting.
- `withPlatform` connects with the same role, but its client extension allows only models tagged `@@platform` in the schema (tenant registry, plans, platform settings, reference data). It cannot read tenant tables at all; RLS would return nothing anyway.
- There is no BYPASSRLS path in this package for application code. `nomo_migrator` (which assumes the table owner `nomo_owner`) is used only by the migration runner ([[MT-separate-privileged-role-used]]); cross-tenant reporting uses `nomo_reporting` from the reporting stack, not this package.

<!-- section:config -->
## Configuration

| Setting | Default (proposed) | Where | Who changes |
|---|---|---|---|
| `DATABASE_URL_APP` | PgBouncer endpoint, role `nomo_app` (web) or `nomo_worker` (workers), chosen by `DB_PROFILE` ([[INF-separate-connection-settings-for]]) | Regional secrets manager ([[INF-secrets-and-keys]]) | DevOps |
| `DATABASE_URL_REPLICA` | Read replica via PgBouncer, same role as `DATABASE_URL_APP` (RLS applies on the replica) | Secrets manager | DevOps |
| `DATABASE_URL_MIGRATE` | Direct (not pooled) endpoint, role `nomo_migrator` | Secrets manager, CI only | DevOps |
| `connection_limit` | 5 per web container, 10 per worker container ([[INF-small-fixed-prisma-pool-per]]) | Env | DevOps |
| `pgbouncer=true` flag | Required | Env | Fixed |
| `statement_timeout` | 15 s app, 60 s workers, off for migrations (lock_timeout 5 s) ([[INF-timeouts-on-connect-query-and]]) | Role-level `ALTER ROLE ... SET` | DevOps via migration |
| `idle_in_transaction_session_timeout` | 10 s | Role-level | DevOps |
| Interactive transaction timeout | 5 s default, 30 s max | Code | Platform engineering |
| Outbox relay poll interval | 500 ms, batch 200 | Env | Platform engineering |

<!-- section:adapters -->
## Providers and extension points

- **Database targets**: AWS RDS / Aurora Postgres behind PgBouncer, or Azure Database for PostgreSQL Flexible Server with its built-in PgBouncer ([[INF-pgbouncer]]). The package has no provider-specific code; differences are in connection strings and tested in CI on both.
- **Outbox relay**: one BullMQ repeatable job per region reads `outbox_event` rows with `FOR UPDATE SKIP LOCKED` (inside `forEachTenant`-style per-tenant transactions) and hands each topic to its registered handler. New topics are added by registering a zod schema and handler in the owning package.
- **Read replica routing**: `replicaOk: true` routes read-only transactions to `DATABASE_URL_REPLICA`; RLS and the tenant setting apply identically on the replica.

<!-- section:errors -->
## Error model

| Error | Postgres cause | Retryable | Caller action |
|---|---|---|---|
| `TenantContextMissingError` | — | No | Bug: fix the entry point; never catch and continue |
| `TenantMismatchError` | — | No | Bug or attack: request is rejected, security event emitted |
| `ConcurrencyConflictError` | version mismatch | No (user decision) | Show "this record changed", reload |
| `UniqueViolationError` | `23505` | No | Map to a domain validation message |
| `ForeignKeyViolationError` | `23503` | No | Usually a cross-tenant or deleted reference; map to 404 |
| `SerializationRetryableError` | `40001`, `40P01` | Yes, by `withTenant` up to 3 times with jitter when `isolation: 'Serializable'` | None |
| `DbUnavailableError` | connection refused, PgBouncer `query_wait_timeout` | Yes, by Temporal / BullMQ retry policy, not inside the package | Return 503 with `Retry-After` from HTTP paths |
| `QueryTimeoutError` | `57014` | No in request path; yes for workers with backoff | Investigate query plan |

<!-- section:nfr -->
## Performance and limits

- `withTenant` overhead (BEGIN, `set_config`, COMMIT): p95 ≤ 2 ms within a region (proposed; measured in [[INF-monitor-pool-usage-wait-times]]).
- Interactive transactions: default 5 s, hard maximum 30 s; long work moves to Temporal Activities that use several short transactions.
- Outbox: end-to-end dispatch latency p95 ≤ 2 s; relay throughput ≥ 500 events/s per region.
- No unbounded list queries: repository list helpers require `take` ≤ 200 and cursor pagination.
- Connection budget: containers × `connection_limit` must stay below PgBouncer `default_pool_size` × pools; checked at deploy time.

<!-- section:versioning -->
## Versioning and compatibility

Semver for the TypeScript API [R1]. The database schema is versioned by Prisma migration history, applied forward-only per region in the order India → Singapore → US (aligned with [[DEP-environment-promotion-and-multi]]). Every schema change follows expand-and-contract across at least two releases ([[DEP-database-migration-strategy-zero]]) so version N-1 of the app keeps working. Changes to `withTenant` semantics are major versions and need sign-off from the security lead.

<!-- section:testing -->
## Test contract

- Integration suite runs against real Postgres with forced RLS **through PgBouncer in transaction mode** (docker-compose in CI); no mocks for the tenant mechanism.
- Isolation: for every tenant model, tenant A cannot read, update, delete or reference tenant B's rows, including when a query omits `tenantId` ([[MT-automated-tests-that-prove-one]]).
- Leakage across pooled connections: 1,000 interleaved transactions for two tenants over a pool of 2 server connections; `current_setting('app.tenant_id', true)` is never visible outside its transaction.
- Missing context: every exported function throws `TenantContextMissingError` with no context.
- Lint: every new tenant table has `tenant_id` and an RLS policy ([[MT-lint-review-check-that-every]]); `prisma migrate diff` shows no drift.
- An in-memory fake is not offered for `withTenant`; consumers use the Testcontainers fixture `createTestTenantDb()` so RLS is always exercised.

<!-- section:questions -->
## Open questions

- [ ] Should `withTenant` also set `app.case_ids` or similar for a second RLS layer on `tribunal_only` rows, or is case-level filtering application-only? (See [[PKG-rbac-abac-case-level-party]].)
- [ ] Is RDS Proxy ever acceptable instead of PgBouncer? [[INF-pgbouncer]] says it must be validated first; until then PgBouncer is mandatory.
- [ ] Outbox table per domain schema or one shared `platform.outbox_event`? Proposed: one shared table partitioned by day.
- [ ] Do we allow `Serializable` transactions in request paths, or only in workers?
- [ ] Owner for reference data per region (see [[PKG-reference-and-seed-data#questions]]).

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

All functions derive the tenant from `@nomology/tenant-context`; the two-argument `withTenant(ctx, fn)` form must match the ambient context or throws `TenantMismatchError` (logged, metric `db.tenant_context.mismatch`, security event). The tenant is set with `set_config('app.tenant_id', id, true)` as the first statement of every transaction, so nothing persists on the pooled server connection. The app roles `nomo_app` and `nomo_worker` have no `BYPASSRLS` and do not own tables; `withPlatform` is restricted to models tagged as platform-level and cannot query tenant tables. BullMQ jobs carry a signed context envelope and Temporal uses interceptors, so background work never runs without a tenant. Raw `$queryRawUnsafe` is removed from the transaction type.

<!-- check:security -->
### Security of the API surface

Credentials come from the regional secrets manager, never committed env files ([[FND-environment-management]]). Roles with minimum grants, as in [[MT-isolation-strategy#matrix]]: `nomo_app` (web) and `nomo_worker` (workers), each with DML on tenant tables and INSERT/SELECT only on audit tables; `nomo_migrator` (DDL, CI only). Replica reads use the same `nomo_app` / `nomo_worker` login against the replica endpoint, so RLS applies unchanged; `nomo_reporting` belongs to the reporting stack and is not used by this package. Unsafe raw query methods are removed from the exported transaction type; raw SQL lives only in reviewed migration files. The package imports `server-only` and is tagged `server` in Turborepo boundaries so it cannot enter a client bundle [R2].

<!-- check:residency -->
### Region awareness

Connection strings are per region and come from that region's secrets manager; the package refuses to start if the configured region (`APP_REGION`) does not match the region tag of the database it connects to (checked via a `platform.region_identity` row). `withTenant` compares the tenant's home region (from the tenant directory) with `APP_REGION` and throws `RegionMismatchError` rather than serving the request.

<!-- check:observability -->
### Observability

Spans per transaction (`db.transaction`, attributes `db.system=postgresql`, `app.tenant_id`, `app.region`, duration, retries) and Prisma query spans with statement templates only (no bound values). Metrics: transaction duration histogram, pool wait time, conflicts, `tenant_context.missing` counter. Logs carry tenant ID, request ID and trace ID; query parameters are never logged.

<!-- check:resilience -->
### Failure behaviour

`withTenant` retries only serialization failures (bounded, jittered) and leaves connection failures to Temporal or BullMQ so retries are not stacked. Timeouts: connect 5 s, statement 15 s (app) / 60 s (workers), idle-in-transaction 10 s; interactive transaction ≤ 30 s, shorter than Temporal start-to-close timeouts for DB activities (60 s). Connections are released on error by Prisma's transaction wrapper. Idempotency for external writes uses `withIdempotency` with keys stored per tenant for 24 h.

<!-- check:change-safety -->
### Change and release safety

Public API diff (API Extractor) blocks merges that change exports without a version bump. Migrations are expand-and-contract and are tested against a copy of the current production schema per region before release. CODEOWNERS: platform engineering plus security lead for anything touching `withTenant`, roles or RLS SQL.

<!-- check:testing -->
### Testing

Integration tests run against Postgres with forced RLS via PgBouncer in transaction mode in CI on every PR that touches `packages/db` or any Prisma schema; they include the cross-tenant read/write/reference suite, pooled-connection leakage test, missing-context test and `prisma migrate diff` drift check. Coverage threshold 90% lines for `packages/db/src`.

<!-- citations -->
## Citations

```json
[
  {
    "body": "semver.org",
    "id": "R1",
    "ident": "SemVer",
    "kind": "standard",
    "title": "Semantic Versioning 2.0.0",
    "url": "https://semver.org/",
    "version": "2.0.0"
  },
  {
    "id": "R2",
    "kind": "vendor",
    "title": "Turborepo reference: boundaries",
    "url": "https://turbo.build/repo/docs/reference/boundaries",
    "vendor": "Vercel (Turborepo)"
  }
]
```

<!-- end -->
