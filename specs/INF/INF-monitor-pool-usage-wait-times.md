---
id: "INF-monitor-pool-usage-wait-times"
title: "Connection pool monitoring"
parent: "INF-database-connection-handling"
order: 6
type: "feature"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Pool usage, waiting requests and acquire wait time are measured at both the application pool and PgBouncer, per workload and region, with alerts before exhaustion"
links: []
rev: 4
syncHash: "6f0b757c0513ef51"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 14.7.5 Connection pool monitoring

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Pool usage, waiting requests and acquire wait time are measured at both the application pool and PgBouncer, per workload and region, with alerts before exhaustion

<!-- section:statement -->
## Statement

The platform shall export, at least every 60 seconds per region and workload, the application connection pool's used, idle and pending counts and its acquire wait time, and PgBouncer's waiting clients, maximum wait and server connections per pool, and shall alert when waiting persists before requests start failing.

<!-- section:rationale -->
## Rationale and source

Pool exhaustion is the most likely database-path failure under autoscaling and long transactions, and it is invisible in CPU metrics. Measuring both sides tells on-call whether the limit is the container's own pool (raise or fix the workload) or the shared PgBouncer server pool (find the long transactions or rebalance budgets).

**Metrics**

| Metric | Type, unit | Source | Labels |
|---|---|---|---|
| `db.client.connection.count` | UpDownCounter, `{connection}`, `db.client.connection.state` = `used` / `idle` [R1] | `pg` pool counters in `packages/data-access` | `db.client.connection.pool.name` (= profile), `service.name`, `cloud.region` |
| `db.client.connection.pending_requests` | UpDownCounter, `{request}` [R1] | `pg` pool `waitingCount` | same |
| `db.client.connection.wait_time` | Histogram, `s` [R1] | timed around pool acquire | same |
| `db.client.connection.timeouts` | Counter, `{timeout}` [R1] | pool acquire timeouts | same |
| `pgbouncer_pools_client_waiting_connections` | Gauge | `pgbouncer_exporter` | `database`, `user`, task |
| `pgbouncer_pools_client_maxwait_seconds` | Gauge, `s` | `pgbouncer_exporter` | same |
| `pgbouncer_pools_server_active_connections` | Gauge | `pgbouncer_exporter` | same |

No tenant label on these metrics (bounded cardinality); tenant-level attribution comes from traces.

**Alerts (proposed)**

| Condition | Severity | Route |
|---|---|---|
| PgBouncer `maxwait` > 1 s for 5 min on `nomo_app` | Page | Platform on-call for the region |
| App pool `pending_requests` > 0 on > 50% of `web` tasks for 5 min | Page | Platform on-call |
| `db.client.connection.timeouts` rate > 1/min | Ticket | Platform team |
| Server connections > 90% of `max_db_connections` for 15 min | Ticket | Platform team |

Runbook: [[INF-database-connection-handling#operations]]. OTel database connection metrics are in Development status [R1]; names are pinned in the telemetry registry ([[OBS-foundations#catalogue]]).

<!-- section:acceptance -->
## Acceptance criteria

- **Given** staging under load, **when** the `web` pool is saturated, **then** `db.client.connection.pending_requests` > 0 appears on the regional dashboard within 2 minutes.
- **Given** a long transaction holding all `nomo_app` server connections in PgBouncer, **when** `maxwait` exceeds 1 s for 5 minutes, **then** the region's on-call is paged with the runbook link.
- **Negative**: **Given** normal load with no waiting, **when** 24 hours pass, **then** no pool alert fires.

<!-- section:verification -->
## Verification method

- **Demonstration**: in staging, hold connections with a test script and confirm metrics and the page.
- **Test**: unit test that the data-access package registers the four `db.client.connection.*` instruments with the profile name.

<!-- section:priority -->
## Priority

Must. Phase 1 for metrics; alerts by Phase 3 (first domain slice) and before any production tenant.

<!-- section:notes -->
## Notes

**Open questions**

- [ ] On Azure, built-in PgBouncer metrics are disabled by default and must be enabled with `metrics.pgbouncer_diagnostics` [R2]; confirm they reach our regional collector.
- [ ] Should pool alerts be per region on-call or a single follow-the-sun rotation ([[OBS-alerting]])?

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Pool exhaustion is not visible in CPU or error metrics until requests fail; this requirement gives the leading indicator that lets on-call act first.

<!-- check:unambiguous -->
### Unambiguous

Metric names, units, sources, thresholds and durations are listed; "persist" is defined as 5 minutes in the alert table.

<!-- check:verifiable -->
### Verifiable

Staging demonstration with a connection-holding script plus a unit test for instrument registration; the negative case checks for no false alerts over 24 hours.

<!-- check:traced -->
### Traced

Parent [[INF-database-connection-handling]]; metric names follow OpenTelemetry database client conventions [R1]; alert rules live in [[OBS-alerting]].

<!-- citations -->
## Citations

```json
[
  {
    "body": "OpenTelemetry (CNCF)",
    "excerpt": "db.client.connection.count (UpDownCounter, {connection}, state idle|used), db.client.connection.max, db.client.connection.pending_requests, db.client.connection.timeouts, db.client.connection.wait_time, db.client.connection.use_time; all in Development status.",
    "id": "R1",
    "ident": "Semantic conventions (Development status)",
    "kind": "standard",
    "title": "Semantic conventions for database client metrics",
    "url": "https://opentelemetry.io/docs/specs/semconv/db/database-metrics/"
  },
  {
    "excerpt": "Built-in PgBouncer runs on port 6432, pool_mode defaults to transaction, it is not supported on the Burstable tier, and it is restarted on the new primary after HA failover so existing connections must be re-established. PgBouncer metrics are disabled by default.",
    "id": "R2",
    "kind": "vendor",
    "title": "PgBouncer in Azure Database for PostgreSQL",
    "url": "https://learn.microsoft.com/en-us/azure/postgresql/connectivity/concepts-pgbouncer",
    "vendor": "Microsoft"
  }
]
```

<!-- end -->
