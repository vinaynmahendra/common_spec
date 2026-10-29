---
id: "INF-small-fixed-prisma-pool-per"
title: "Prisma pool sizing"
parent: "INF-database-connection-handling"
order: 2
type: "feature"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Small, fixed Prisma pool per container, sized so maximum container count × pool size stays within the pooler's client and server limits"
links: []
rev: 3
syncHash: "726a49a53514e762"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 14.7.2 Prisma pool sizing

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Small, fixed Prisma pool per container, sized so maximum container count × pool size stays within the pooler's client and server limits

<!-- section:statement -->
## Statement

The data-access package shall create each container's Prisma client with a fixed connection pool size taken from that workload's connection profile (`web` 5, `worker-jobs` 3, `worker-temporal-*` 3; minimum and maximum equal), such that the sum over all workloads of *maximum task count × pool size* in a region does not exceed 80% of PgBouncer's total `max_client_conn`, and the sum of PgBouncer server pools does not exceed 30% of the Postgres `max_connections`.

<!-- section:rationale -->
## Rationale and source

Containers scale out automatically ([[INF-compute#sizing]]); without a fixed pool, each new task opens more connections until PgBouncer or Postgres refuses them, which shows up as failures across all tenants at once. Because every request runs inside one transaction with transaction-local tenant context ([[MT-prisma-client-extension-wraps]]), a request holds exactly one pooled connection for its duration, so a small pool per container is enough.

Prisma's default pool is not small: in v6 it is derived from CPU count, and in v7 with the `pg` driver adapter the default `max` is 10 [R1]. The value must therefore be set explicitly.

How it is configured:

- Prisma v7 (driver adapter): `new PrismaPg({ connectionString, max: profile.poolSize, connectionTimeoutMillis: profile.acquireTimeoutMs })` — `max` replaces the v6 `connection_limit` [R1].
- Prisma v6: `?connection_limit=5&pool_timeout=5` on the PgBouncer URL.

**Budget for prod-in (proposed)**

| Workload | Max tasks | Pool | Client connections |
|---|---|---|---|
| `web` | 20 | 5 | 100 |
| `worker-jobs` | 10 | 3 | 30 |
| `worker-temporal-*` (all queues) | 24 | 3 | 72 |
| **Total** | | | **202** ≪ 0.8 × (3 × 1000) |
| PgBouncer server pools | 3 tasks × 40 | | **120** ≤ 0.3 × 400 = 120 |

Parent: [[INF-database-connection-handling]]. Related: [[INF-pgbouncer#sizing]], [[INF-separate-connection-settings-for]].

<!-- section:acceptance -->
## Acceptance criteria

- **Given** a `web` container started with the production profile, **when** 50 concurrent requests arrive, **then** at most 5 connections are open from that container to PgBouncer and the remaining requests wait in the client pool.
- **Given** the IaC parameters for a region, **when** CI runs the connection budget check, **then** it passes only if Σ(max tasks × pool size) ≤ 0.8 × total `max_client_conn` and Σ server pool sizes ≤ 0.3 × `max_connections`.
- **Negative**: **Given** a pull request that raises `web` max tasks from 20 to 40 without changing pools, **when** CI runs, **then** the budget check fails with a message naming the region and the overshoot.
- **Negative**: **Given** a workload whose profile does not define a pool size, **when** the container starts, **then** environment validation fails at start-up rather than falling back to the Prisma default.

<!-- section:verification -->
## Verification method

- **Test**: integration test in `packages/data-access` that starts a client with the profile and asserts pool size via the `pg` pool counters (`totalCount ≤ max`).
- **Analysis**: `scripts/connection-budget.ts` runs in CI on every change to `infra/live/**` and fails on overshoot.
- **Demonstration**: load test in staging ([[TST-performance-and-load-testing]]) shows no PgBouncer `max_client_conn` errors at maximum scale.

<!-- section:priority -->
## Priority

Must. Phase 1 (core platform), because the first load on the shared database arrives with tenant isolation.

<!-- section:notes -->
## Notes

**Open questions**

- [ ] Prisma major version (v6 or v7) — decides which configuration form is used ([[APP-framework-dependencies]]).
- [ ] Are the 80% / 30% headroom factors right? The 30% server-side factor leaves room for migrations, admin, monitoring and RDS internals; it may be raised once real usage is known.

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Without it, autoscaling can exhaust PgBouncer or Postgres connections, causing a region-wide outage for all tenants. No other requirement fixes the client-side pool.

<!-- check:unambiguous -->
### Unambiguous

Pool sizes per workload, the two inequalities and their headroom factors are stated numerically; "maximum task count" is the IaC autoscaling maximum.

<!-- check:feasible -->
### Feasible

Supported directly by Prisma (v6 `connection_limit`, v7 `pg` adapter `max` [R1]). One connection per request is enough because each request is one transaction.

<!-- check:verifiable -->
### Verifiable

Three methods: pool-size integration test, CI budget analysis on every infrastructure change (with a negative case), and a staging load test at maximum scale.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "With driver adapters, pool configuration comes from the driver; for pg the v6 connection_limit maps to max (default 10) and the acquire timeout maps to connectionTimeoutMillis, which defaults to 0 (no timeout).",
    "id": "R1",
    "kind": "vendor",
    "title": "Prisma ORM v7: Connection pool",
    "url": "https://www.prisma.io/docs/orm/v7/prisma-client/setup-and-configuration/databases-connections/connection-pool",
    "vendor": "Prisma"
  }
]
```

<!-- end -->
