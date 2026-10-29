---
id: "INF-pgbouncer"
title: "PgBouncer"
parent: "INF-database-connection-handling"
order: 1
type: "feature"
template: "infra"
status: "draft"
owner: null
indicative: false
summary: "PgBouncer in transaction pooling mode between app and Postgres (Azure: built-in PgBouncer of Flexible Server); RDS Proxy is not a drop-in equivalent because it pins sessions on set_config"
links: []
rev: 4
syncHash: "7bb45199c466ff15"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 14.7.1 PgBouncer

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> PgBouncer in transaction pooling mode between app and Postgres (Azure: built-in PgBouncer of Flexible Server); RDS Proxy is not a drop-in equivalent because it pins sessions on set_config

<!-- section:purpose -->
## Purpose and responsibilities

Multiplexes many short-lived client connections from containers onto a small number of Postgres server connections, so `web` and worker tasks can scale out without exhausting `max_connections`. Must run in **transaction pooling** mode: a server connection is assigned to a client only for the duration of one transaction [R1], which is exactly the scope of our tenant setting ([[MT-prisma-client-extension-wraps]]).

Why not RDS Proxy (by default): for PostgreSQL, RDS Proxy pins a client to a server connection when `SET` or `set_config` is used to set session variables [R2]. Every request runs `set_config('app.tenant_id', …, true)`, so it would likely pin on every transaction and lose the multiplexing benefit. It may only be chosen after a test proves that `set_config(..., true)` inside a transaction does not pin, with Prisma's real query pattern.

<!-- section:topology -->
## Topology per region

| Region | Environment | Deployment |
|---|---|---|
| prod-in | prod | ECS service `pgbouncer`, 3 tasks over 3 AZs behind an internal NLB (TCP 6432) |
| prod-sg, prod-us | prod | 2 tasks over 2 AZs (3rd AZ added if load requires) |
| staging / UAT / dev | non-prod | 1 task |
| Azure regions | prod | No separate service: Flexible Server built-in PgBouncer on port 6432, `pgbouncer.pool_mode = transaction` (the default) [R3] |

Each PgBouncer task has its **own pools**, so per-task pool sizes are the regional budget divided by task count.

<!-- section:sizing -->
## Sizing and scaling

PgBouncer is single-threaded; scale by adding tasks, not CPU. One task at 0.5 vCPU handles several thousand transactions per second for short queries (to be confirmed by load test).

Per-task pools for prod-in with 3 tasks (proposed):

| Pool (database / user) | `default_pool_size` | `reserve_pool_size` | Server connections × 3 tasks |
|---|---|---|---|
| `platform` / `nomo_app` | 25 | 5 | 75 (+15 reserve) |
| `platform` / `nomo_worker` | 15 | 0 | 45 |
| `max_db_connections` per task | 40 | | ≤ 120 total (+15 reserve) |
| `max_client_conn` per task | 1000 | | far above the ~200 client connections from containers |

Singapore and US with 2 tasks: `nomo_app` 20, `nomo_worker` 10, `max_db_connections` 30 per task (≤ 60 total). Budget check against Postgres in [[INF-small-fixed-prisma-pool-per]].

<!-- section:config -->
## Configuration baseline

```ini
[pgbouncer]
listen_port = 6432
pool_mode = transaction
auth_type = scram-sha-256
auth_user = pgbouncer_auth           ; can only execute the lookup function
auth_query = SELECT usename, passwd FROM pgbouncer.get_auth($1)
max_client_conn = 1000
default_pool_size = 25               ; overridden per user below
max_db_connections = 40
reserve_pool_size = 5
reserve_pool_timeout = 2
max_prepared_statements = 200        ; Prisma uses prepared statements; requires PgBouncer >= 1.21
server_reset_query_always = 0        ; reset query not run in transaction mode; we rely on transaction-local settings
server_idle_timeout = 300
server_lifetime = 1800
query_wait_timeout = 10              ; client gives up after 10 s waiting for a server connection
client_tls_sslmode = require
server_tls_sslmode = verify-full
ignore_startup_parameters = extra_float_digits,options
application_name_add_host = 0
stats_period = 60

[users]
nomo_app    = pool_size=25
nomo_worker = pool_size=15
```

Notes:

- With PgBouncer 1.21 or later, Prisma should **not** set `pgbouncer=true`; prepared statements are supported when `max_prepared_statements` is above zero [R4].
- `statement_timeout` and `idle_in_transaction_session_timeout` are set as **role defaults in Postgres** (`ALTER ROLE nomo_app SET …`), which apply when PgBouncer opens the server connection, instead of startup options that PgBouncer would drop ([[INF-timeouts-on-connect-query-and]]).
- Version: latest stable PgBouncer 1.2x, image pinned by digest, rebuilt monthly.
- Azure built-in PgBouncer parameters (`pgbouncer.default_pool_size`, `pgbouncer.max_prepared_statements`, etc.) are set through the Flexible Server parameter module with the same values; built-in PgBouncer is not available on the Burstable tier [R3].

<!-- section:resilience -->
## High availability and DR

- **Task failure**: NLB health check removes it within ~30 s; clients reconnect to other tasks; transactions in flight on that task fail and are retried by the application.
- **Postgres failover**: server connections drop; PgBouncer reconnects via the RDS DNS endpoint (DNS TTL is short; `dns_max_ttl = 15`). Expect 1–2 minutes of retryable errors.
- **Planned DB maintenance**: `PAUSE` on all tasks drains active transactions and holds new ones; `RESUME` after. Used for parameter changes needing a restart.
- **Azure**: built-in PgBouncer restarts with the server on failover and connections must be re-established [R3]; the same client retry rules apply.
- No state of its own; RPO not applicable, RTO under 5 minutes (redeploy).

<!-- section:security -->
## Security

- Internal NLB only; security group allows 6432 from `web`, worker and `worker-temporal-*` security groups.
- SCRAM authentication through `auth_query`: PgBouncer holds only the `pgbouncer_auth` credential, which can call one `SECURITY DEFINER` function returning hashes for `nomo_app` and `nomo_worker` only (never for `nomo_migrator` or the master user).
- TLS on both client and server legs.
- Admin console (`pgbouncer` virtual database) is reachable only from the task itself (`admin_users` empty, `stats_users = pgbouncer_stats` used by the exporter sidecar).

<!-- section:operations -->
## Runbook

- **Change pool size**: update the IaC parameters, recalculate the budget, rolling restart one task at a time (`SHUTDOWN WAIT_FOR_CLIENTS` style graceful stop via SIGINT).
- **Diagnose waits**: `SHOW POOLS` (`cl_waiting`, `maxwait`), `SHOW CLIENTS`, then `pg_stat_activity` filtered by `application_name` to find long transactions.
- **Before choosing RDS Proxy** (if ever proposed): run the isolation test suite and a load test through RDS Proxy, and check the `DatabaseConnectionsCurrentlySessionPinned` metric; reject if pinning is near 100% of transactions.

<!-- section:observability -->
## Monitoring and alerts

Exported by `pgbouncer_exporter` sidecar to the regional collector; thresholds in [[INF-monitor-pool-usage-wait-times]]. Key series: client active / waiting, server active / idle per pool, `maxwait` seconds, total transactions and average transaction time per pool.

<!-- section:cost -->
## Cost

Small: 2–3 tasks of 0.5 vCPU per production region. Cheaper than RDS Proxy (billed per vCPU of the database) and keeps behaviour identical between AWS regions.

<!-- section:readiness -->
## Production readiness

| Item | Status |
|---|---|
| Image pinned and SCRAM `auth_query` set up | Not started |
| Prisma works with prepared statements through PgBouncer | Not started |
| Isolation tests pass through PgBouncer in CI | Not started |
| Failover drill: reconnect within RTO | Not started |
| Azure built-in PgBouncer parameter parity | Not started |

<!-- section:questions -->
## Open questions

- [ ] Accept self-run PgBouncer on ECS for AWS (proposed), or test RDS Proxy despite the pinning behaviour?
- [ ] Should PgBouncer run as a sidecar per `web` task instead of a central service? (Simpler networking, but multiplies server pools and weakens the budget.)
- [ ] Is a separate pooler needed in front of the reporting replica, or do reporting jobs connect directly with a small pool?

<!-- checks -->
## Template checks

<!-- check:security -->
### Security

Internal NLB only, SCRAM via a restricted `auth_query` function that cannot return privileged role hashes, TLS on both legs, no admin users, and a separate stats user for the exporter.

<!-- check:dr -->
### Resilience and recovery

Stateless; recovery is redeploy (under 5 minutes). Postgres failover is handled by reconnecting through DNS with a short `dns_max_ttl`; application retries cover the 1–2 minute window. Tested in the quarterly database failover drill.

<!-- check:isolation -->
### Tenant isolation and noisy neighbours

Transaction pooling assigns a server connection only for one transaction [R1]; the tenant setting is transaction-local, so it cannot carry to another client. The reset query is not relied on. Session features are banned on pooled connections. Per-user pools (`nomo_app`, `nomo_worker`) stop background work from consuming the connections reserved for interactive requests. The isolation test suite runs through PgBouncer in transaction mode in CI.

<!-- check:observability -->
### Monitoring and alerting

Waiting clients and `maxwait` per pool alert before exhaustion turns into errors; server connections against `max_db_connections` show when the budget is the limit.

<!-- check:lifecycle -->
### Operations and lifecycle

Pinned PgBouncer 1.2x image rebuilt monthly; upgrades tested in staging with the isolation and Prisma integration suites. Runbook covers pool resizing, PAUSE / RESUME for maintenance and wait diagnosis.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "In transaction pooling mode a server connection is assigned to a client only for the duration of a transaction; session-level features such as SET (without LOCAL), LISTEN and session advisory locks are not supported.",
    "id": "R1",
    "kind": "vendor",
    "title": "PgBouncer features (what works under transaction pooling)",
    "url": "https://www.pgbouncer.org/features.html",
    "vendor": "PgBouncer"
  },
  {
    "excerpt": "For PostgreSQL, using SET commands and set_config to assign values to session variables causes the proxy to pin the client to a database connection.",
    "id": "R2",
    "kind": "vendor",
    "title": "Avoiding pinning an RDS Proxy",
    "url": "https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/rds-proxy-pinning.html",
    "vendor": "AWS"
  },
  {
    "excerpt": "Built-in PgBouncer runs on port 6432, pool_mode defaults to transaction, it is not supported on the Burstable tier, and it is restarted on the new primary after HA failover so existing connections must be re-established. PgBouncer metrics are disabled by default.",
    "id": "R3",
    "kind": "vendor",
    "title": "PgBouncer in Azure Database for PostgreSQL",
    "url": "https://learn.microsoft.com/en-us/azure/postgresql/connectivity/concepts-pgbouncer",
    "vendor": "Microsoft"
  },
  {
    "excerpt": "PgBouncer must run in transaction mode; with PgBouncer 1.21.0 or later do not set pgbouncer=true and set max_prepared_statements above 0; Prisma CLI / Migrate needs a direct connection.",
    "id": "R4",
    "kind": "vendor",
    "title": "Prisma ORM v7: Configure Prisma Client with PgBouncer",
    "url": "https://www.prisma.io/docs/orm/v7/prisma-client/setup-and-configuration/databases-connections/pgbouncer",
    "vendor": "Prisma"
  }
]
```

<!-- end -->
