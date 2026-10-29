---
id: "INF-database-connection-handling"
title: "Database connection handling"
parent: "INF"
order: 7
type: "capability"
template: "infra"
status: "draft"
owner: null
indicative: false
summary: "The connection path from every workload to Postgres: PgBouncer in transaction mode, fixed Prisma pools, timeouts and retries, per-workload settings and pool monitoring"
links: []
rev: 3
syncHash: "b092ec852297de11"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 14.7 Database connection handling

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> The connection path from every workload to Postgres: PgBouncer in transaction mode, fixed Prisma pools, timeouts and retries, per-workload settings and pool monitoring

<!-- section:purpose -->
## Purpose and responsibilities

Owns the path between application code and Postgres. Forced RLS with transaction-scoped tenant context ([[MT-prisma-client-extension-wraps]]) and many small containers make this path a correctness concern, not only a performance one: nothing on the path may carry session state from one transaction to the next.

Children:

| Child | Owns |
|---|---|
| [[INF-pgbouncer]] | The pooler: deployment, transaction mode, pool sizes, Azure built-in variant, why not RDS Proxy |
| [[INF-small-fixed-prisma-pool-per]] | Client-side pool size per container and the connection budget formula |
| [[INF-timeouts-on-connect-query-and]] | Connect, acquire, statement and idle-in-transaction timeouts; retry rules |
| [[INF-separate-connection-settings-for]] | One connection profile per workload (web, workers, migrations, reporting, Temporal) |
| [[INF-monitor-pool-usage-wait-times]] | Pool usage and wait-time metrics and alerts |

<!-- section:topology -->
## Topology per region

```
web tasks (Prisma pool 5)  ─┐
worker-jobs (pool 3)       ─┼─► PgBouncer (2–3 tasks, transaction mode) ─► Postgres primary
temporal workers (pool 3)  ─┘           port 6432, internal NLB              (nomo_app / nomo_worker)

migrate task (1 conn)      ───────────────────────── direct 5432 ─────────► Postgres primary (nomo_migrator)
platform-ops jobs          ───────────────────────── direct 5432 ─────────► Postgres primary (nomo_platform_ops)
reporting service          ───────────────────────── direct 5432 ─────────► read replica (nomo_reporting)
Temporal server            ───────────────────────── direct 5432 ─────────► temporal-<region> (separate instance)
```

| Region | Pooler |
|---|---|
| AWS regions (prod-in, prod-sg, prod-us) | Self-run PgBouncer on ECS ([[INF-pgbouncer]]) |
| Azure regions | Built-in PgBouncer of Flexible Server, port 6432, transaction mode [R1] |

<!-- section:sizing -->
## Sizing and scaling

The connection budget per region is the binding constraint, worked out in [[INF-small-fixed-prisma-pool-per]]. Summary for prod-in (proposed): about 200 client connections from containers at maximum scale, multiplexed by PgBouncer into at most 120 server connections to the primary, inside `max_connections = 400` which also leaves room for migrations, admin, monitoring and RDS internal connections.

<!-- section:config -->
## Configuration baseline

Shared rules for every child:

1. Application traffic goes through the pooler; only migrations, platform admin jobs, reporting (replica) and the Temporal server connect directly.
2. Every connection sets `application_name` (`web`, `worker-jobs`, `worker-temporal-cases`, …) and connects as the workload's own role.
3. Tenant context only via `set_config('app.tenant_id', $1, true)` inside the transaction; `SET` without `LOCAL`, session advisory locks, `LISTEN/NOTIFY` and `WITH HOLD` cursors are forbidden on pooled connections (lint rule in the data-access package, [[PKG-data-access]]).
4. TLS `sslmode=verify-full` from client to PgBouncer and from PgBouncer to Postgres.

<!-- section:resilience -->
## High availability and DR

- PgBouncer task loss: clients reconnect through the NLB to the remaining tasks; in-flight transactions on the lost task fail and are retried by the application ([[INF-timeouts-on-connect-query-and]]).
- Postgres failover: PgBouncer server connections break; PgBouncer reconnects to the new primary via DNS; clients see a burst of retryable errors for 1–2 minutes.
- Pool exhaustion: requests wait up to the acquire timeout, then fail fast with a 503 problem type ([[APP-api-error-catalogue-problem]]) rather than piling up.

<!-- section:security -->
## Security

Credentials per workload role from Secrets Manager; PgBouncer authenticates clients with SCRAM through `auth_query` against a restricted lookup function, so passwords are not duplicated in PgBouncer configuration. TLS on both legs. Only listed security groups reach PgBouncer and the direct endpoint.

<!-- section:operations -->
## Runbook

Runbook entries: pool exhaustion (find the workload with most waiting clients, look for long transactions, scale or shed load), PgBouncer restart (one task at a time; `PAUSE` / `RESUME` for planned DB maintenance), changing pool sizes (IaC change, recalculated budget, rolling restart).

<!-- section:observability -->
## Monitoring and alerts

Pool metrics and alerts are specified in [[INF-monitor-pool-usage-wait-times]]: client waiting count and maximum wait in PgBouncer, Prisma / pg pool waiting requests and acquire time per container, server connections against budget, and connection errors by type.

<!-- section:readiness -->
## Production readiness

| Item | Status |
|---|---|
| Isolation tests run through PgBouncer in transaction mode in CI ([[TST-multi-tenant-isolation-tests]]) | Not started |
| Connection budget calculation reviewed per region | Proposed |
| Failover drill with retries verified | Not started |

<!-- section:questions -->
## Open questions

- [ ] Confirm the Prisma major version (v6 URL parameters vs v7 driver-adapter pool settings) in [[APP-framework-dependencies]].
- [ ] Do any workloads need session features (advisory locks for singleton jobs, LISTEN/NOTIFY)? If so, they need a separate direct, session-mode connection profile.

<!-- checks -->
## Template checks

<!-- check:dr -->
### Resilience and recovery

During a Postgres failover, PgBouncer reconnects to the new primary and the application retries whole transactions for retryable errors with backoff, so the user-visible effect is limited to a short latency spike within the database RTO. Drilled together with the database failover drill.

<!-- check:isolation -->
### Tenant isolation and noisy neighbours

The connection path is the place where tenant context could leak between requests, so it is designed so it cannot: transaction pooling plus `set_config(..., true)` means the setting dies with the transaction; session-level features are banned by lint; and the cross-tenant isolation tests run through the same PgBouncer configuration as production.

<!-- check:observability -->
### Monitoring and alerting

Waiting clients and wait time at both the application pool and PgBouncer are the leading indicators of exhaustion and are alerted before requests start failing ([[INF-monitor-pool-usage-wait-times]]).

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Built-in PgBouncer runs on port 6432, pool_mode defaults to transaction, it is not supported on the Burstable tier, and it is restarted on the new primary after HA failover so existing connections must be re-established. PgBouncer metrics are disabled by default.",
    "id": "R1",
    "kind": "vendor",
    "title": "PgBouncer in Azure Database for PostgreSQL",
    "url": "https://learn.microsoft.com/en-us/azure/postgresql/connectivity/concepts-pgbouncer",
    "vendor": "Microsoft"
  }
]
```

<!-- end -->
