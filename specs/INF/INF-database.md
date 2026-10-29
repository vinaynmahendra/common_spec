---
id: "INF-database"
title: "Database"
parent: "INF"
order: 6
type: "capability"
template: "infra"
status: "draft"
owner: null
indicative: false
summary: "Managed Postgres per region (RDS for PostgreSQL Multi-AZ; Azure Flexible Server where required): parameters, roles for forced RLS, extensions, read replicas and upgrades"
links: []
rev: 3
syncHash: "5cae03fedd702423"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 14.6 Database

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Managed Postgres per region (RDS for PostgreSQL Multi-AZ; Azure Flexible Server where required): parameters, roles for forced RLS, extensions, read replicas and upgrades

<!-- section:purpose -->
## Purpose and responsibilities

Hosts the single shared application database per region that holds all tenant data under forced Row-Level Security ([[ADR-tenant-isolation]], [[MT-isolation-strategy]]), plus in-region read replicas for reporting. The schema itself is owned by the domain and package data models (for example [[MT-tenancy-and-identity-schema]], [[DOM-cases-schema]], [[PKG-audit-log-schema]]); this node owns the **server**: engine, size, parameters, roles, extensions, replicas, backups and upgrades.

Depended on by: every workload through [[INF-database-connection-handling]]; [[RPT-report-infrastructure]] (replicas); [[DEP-database-migration-strategy-zero]] (migration role and direct endpoint). Temporal persistence uses a **separate** instance owned by [[INF-temporal]].

<!-- section:topology -->
## Topology per region

| Region | Environment | Primary | Replicas | Notes |
|---|---|---|---|---|
| India (ap-south-1) | prod | RDS for PostgreSQL, Multi-AZ (synchronous standby in a second AZ) | 1 in-region read replica for reporting | + cross-region replica in ap-south-2 only if in-country DR is approved |
| Singapore (ap-southeast-1) | prod | Multi-AZ | 1 read replica | No second AWS region in Singapore (see [[INF-backup-and-disaster-recovery]]) |
| US (us-east-1) | prod | Multi-AZ | 1 read replica | + us-west-2 replica if DR approved |
| India | staging / UAT | Single-AZ | None | Synthetic data only |
| India | dev | Single-AZ, smallest class | None | |
| Azure region | prod | Azure Database for PostgreSQL Flexible Server, zone-redundant HA, General Purpose or Memory Optimized tier (required for built-in PgBouncer [R1]) | 1 read replica | Built-in PgBouncer on port 6432 |

Endpoints per region: `pg-primary` (direct, used only by migrations and admin jobs), `pgbouncer` (all application traffic, [[INF-pgbouncer]]), `pg-reporting` (replica).

Working choice is RDS for PostgreSQL; Aurora PostgreSQL is an open decision (faster failover and storage auto-growth vs higher I/O cost and different behaviour for some extensions).

<!-- section:sizing -->
## Sizing and scaling

| Region | Starting class (proposed) | Storage | Basis |
|---|---|---|---|
| India | `db.r7g.xlarge` (4 vCPU, 32 GB) | gp3 500 GB, autoscaling to 2 TB, 12,000 IOPS | SEBI ODR volume via MIIs is high-count, small-document; audit log grows fastest |
| Singapore | `db.r7g.large` (2 vCPU, 16 GB) | gp3 200 GB, autoscaling to 1 TB | Arbitral institution tenants: fewer, larger cases |
| US | `db.r7g.large` | gp3 200 GB | |

Growth assumptions (to be replaced by forecasts): India 500k cases / year by year 3 with ~40 audit events per case; documents are in object storage, so Postgres holds metadata only. The audit log ([[PKG-audit-log-schema]]) is partitioned monthly to keep indexes small.

Scaling triggers: CPU > 60% sustained at peak for a week, buffer cache hit ratio < 99%, storage > 70% with 30-day forecast, active connections near the budget in [[INF-small-fixed-prisma-pool-per]]. Vertical scale-up happens in a maintenance window through Multi-AZ failover (about 1–2 minutes of disruption).

<!-- section:config -->
## Configuration baseline

**Engine**: PostgreSQL 17 (proposed; 18 once validated on both RDS and Azure Flexible Server). Same major version in every region.

**Parameter group (key settings)**

| Parameter | Value | Why |
|---|---|---|
| `rds.force_ssl` / `require_secure_transport` | `1` / `on` | TLS on every connection |
| `ssl_min_protocol_version` | `TLSv1.2` | |
| `password_encryption` | `scram-sha-256` | No md5 |
| `max_connections` | 400 (India), 250 (others), set explicitly | Matches the connection budget; avoids instance-size defaults changing on resize |
| `shared_preload_libraries` | `pg_stat_statements` | Normalised query stats without parameters |
| `log_min_duration_statement` | `500ms` | Slow query log |
| `log_parameter_max_length`, `log_parameter_max_length_on_error` | `0`, `0` | Bind parameters (which may hold personal data) never written to logs |
| `log_statement` | `ddl` | Schema changes logged for audit |
| `log_connections`, `log_disconnections` | `on` | Security evidence; feeds [[OBS-security-events]] |
| `idle_in_transaction_session_timeout` | `60s` server default (stricter per role) | See [[INF-timeouts-on-connect-query-and]] |
| `statement_timeout` | Not set globally; set per role | Different workloads, see [[INF-separate-connection-settings-for]] |
| `lock_timeout` | `5s` for the migration role | Migrations must not queue behind long locks |
| `track_io_timing` | `on` | Diagnose I/O-bound queries |

**Roles** (created by a bootstrap migration run as the master user, then the master password is locked away)

| Role | Login | Purpose | RLS |
|---|---|---|---|
| `nomo_owner` | No | Owns all schemas and tables | Tables have `FORCE ROW LEVEL SECURITY`, so even the owner is subject to policies [R2] |
| `nomo_migrator` | Yes (direct endpoint only) | Assumes `nomo_owner`; used only by the `migrate` task ([[MT-separate-privileged-role-used]]) | Bypass only where a migration needs it, through an explicit, reviewed `SET ROLE` |
| `nomo_app` | Yes (via PgBouncer) | Web containers. DML grants on tenant tables as the classification file says; `NOBYPASSRLS`, owns nothing ([[MT-app-connects-as-a-non]]) | Subject to RLS |
| `nomo_worker` | Yes (via PgBouncer) | Temporal and BullMQ workers. Same grants as `nomo_app`; a separate login so `pg_stat_activity`, logs and timeouts differ per workload | Subject to RLS |
| `nomo_reporting` | Yes (replica only) | Read-only, cross-tenant platform reporting through curated `reporting.*` views only; no grant on base tables ([[MT-cross-tenant-reporting-via-a]]) | Read-only |
| `nomo_platform_ops` | Yes | Listed cross-tenant platform jobs (tenant provisioning and offboarding steps, deletion verification) and break-glass, with short-lived credentials and statement logging ([[MT-isolation-strategy#matrix]], [[APP-platform-admin-and-support]]) | `BYPASSRLS`; every session logged and alerted |

These are the canonical role names used by every node ([[MT-app-connects-as-a-non]]); the older names `app_owner`, `app_migrator`, `app_rls_user`, `app_web`, `app_worker`, `app_reporting` and `platform_admin_job` are retired.

The RLS policy reads `current_setting('app.tenant_id')`; if the setting is missing or empty the cast to `uuid` fails, so a query without tenant context errors instead of returning rows (fail closed).

**Extensions** (allow-list): `pgcrypto`, `pg_trgm` ([[PKG-search]]), `btree_gist` (no-overlap exclusion constraints in [[DOM-hearings-schema]]), `pg_stat_statements`, `pgvector` only if the RAG store stays in Postgres ([[AI-rag]]).

<!-- section:resilience -->
## High availability and DR

| Failure | Behaviour | RPO / RTO (proposed) |
|---|---|---|
| Primary instance or AZ failure | Multi-AZ automatic failover to synchronous standby; DNS endpoint moves; PgBouncer reconnects | 0 / 1–2 min (target under 5 min end to end) |
| Replica failure | Reporting degraded; recreated from IaC | n/a |
| Accidental delete / bad migration | Point-in-time restore to a new instance, then targeted data repair or cut-over | 5 min / 1–4 h depending on size |
| Logical corruption found late | Restore from daily snapshot in backup vault (up to 35 days PITR, monthly snapshots 12 months) | up to 24 h / 4–8 h |
| Region loss | See [[INF-backup-and-disaster-recovery]] | per region |

Failover must be tested with PgBouncer and Prisma in place: the drill checks that in-flight transactions fail with retryable errors and that new transactions succeed within the RTO ([[INF-timeouts-on-connect-query-and]]). Quarterly forced failover (`reboot --force-failover`) in staging and, in a maintenance window, production.

<!-- section:security -->
## Security

- Data subnets only; security group allows 5432 from `pgbouncer`, `migrate` and the platform-ops job task (`nomo_platform_ops`) security groups only; read replica allows the reporting service. No public accessibility.
- Storage, snapshots, replicas and Performance Insights encrypted with the regional CMK `rds-<region>`.
- Master credentials managed by RDS in Secrets Manager (never in Terraform state); application role passwords rotated by Secrets Manager every 30 days, or IAM database authentication for `nomo_migrator` and `nomo_platform_ops`.
- Human access: no standing logins. Break-glass role issues a 1-hour IAM auth token through SSO for a named engineer; every session is logged (`log_connections`) and reviewed ([[SEC-access-reviews]]).
- Hardening drift checked by a weekly job comparing the live parameter group and role grants against IaC and the expected grant list (`pg_roles`: `rolbypassrls` must be false for every login role except `nomo_platform_ops`).

<!-- section:operations -->
## Runbook

- **Minor version upgrades**: auto minor upgrade off; applied monthly in a regional maintenance window (India 01:00–03:00 IST Sunday; Singapore 01:00–03:00 SGT Sunday; US 02:00–04:00 ET Sunday — proposed, to be checked against hearing calendars).
- **Major version upgrades**: blue/green deployment (RDS Blue/Green) rehearsed in staging; tested with the Prisma migration history and RLS policies; scheduled with tenant notice.
- **Long-running query**: identify in `pg_stat_activity` by `application_name` (set per workload), cancel with `pg_cancel_backend`, then fix the query.
- **Bloat / vacuum**: monitor dead tuples on hot tables (cases, audit partitions, outbox); outbox rows deleted after delivery to keep it small.
- **Restore**: runbook in [[INF-backup-and-disaster-recovery#operations]].

<!-- section:observability -->
## Monitoring and alerts

| Signal | Alert (proposed) |
|---|---|
| CPU | > 80% for 15 min → ticket |
| Free storage | < 30% → ticket; < 15% → page |
| Connections vs `max_connections` | > 80% → page (see [[INF-monitor-pool-usage-wait-times]]) |
| Replica lag | > 60 s → ticket (reporting stale) |
| Transactions open > 60 s | Any → ticket; > 5 min → page |
| Deadlocks | > 5 / hour → ticket |
| Transaction ID age | > 500 million → page (wraparound risk) |
| Failover event | Event → chat + incident review |

Query-level: `pg_stat_statements` top queries by total time per region, exported hourly; Performance Insights for wait events.

<!-- section:cost -->
## Cost

Main drivers: instance class (Multi-AZ doubles instance cost), storage and IOPS, backup storage beyond the free allowance, replica. Reserved instances after sizing stabilises (6 months). Rejected saving: single-AZ in production (fails RTO).

<!-- section:readiness -->
## Production readiness

| Item | Status |
|---|---|
| Parameter group with no parameters in logs | Not started |
| Role model with FORCE RLS and no BYPASSRLS on app logins | Not started |
| Failover drill with PgBouncer and Prisma | Not started |
| PITR restore drill to a new instance | Not started |
| Maintenance windows agreed per region | Not started |

<!-- section:questions -->
## Open questions

- [ ] RDS for PostgreSQL or Aurora PostgreSQL? (Proposed ADR.)
- [ ] PostgreSQL 17 or 18 at launch?
- [ ] Does the RAG vector store live in this database (pgvector) or in a separate store ([[AI-rag]])?
- [ ] Reporting: is one in-region read replica enough, or is a warehouse needed from Phase 7 ([[RPT-report-infrastructure]])?
- [ ] Confirm maintenance windows per region against hearing schedules of the largest tenants.
- [ ] Is IAM database authentication acceptable for the migration and admin roles on both AWS and Azure (Entra ID auth)?

<!-- checks -->
## Template checks

<!-- check:security -->
### Security

Private data subnets, security groups listing exact callers, TLS 1.2+ forced, scram-sha-256, CMK encryption per region, managed master secret, 30-day rotation for application roles, no standing human logins (break-glass IAM token), and bind parameters kept out of logs.

<!-- check:residency -->
### Data residency

Primary, standby, replicas, automated backups and snapshots are all in the tenant's region. Cross-region replicas exist only where an in-country DR region is approved (ap-south-2 for India, us-west-2 for US). Slow-query and connection logs go to the regional log group and contain no bind parameters.

<!-- check:dr -->
### Resilience and recovery

Multi-AZ gives RPO 0 / RTO under 5 minutes for instance and AZ failure; PITR gives RPO 5 minutes for logical errors. Failover is drilled quarterly together with PgBouncer and Prisma, and a PITR restore to a new instance is drilled at least yearly with row counts and an application smoke test as completeness checks.

<!-- check:isolation -->
### Tenant isolation and noisy neighbours

All tenant tables have RLS enabled and forced, so even `nomo_owner` is subject to policies [R2]. Application logins (`nomo_app`, `nomo_worker`) are NOBYPASSRLS, non-owner roles; the weekly grant check fails if any login role other than `nomo_platform_ops` has `rolbypassrls`, or if any login role owns a table. Tenant context is set per transaction only ([[MT-prisma-client-extension-wraps]]); a missing setting errors rather than returning rows. Per-workload `statement_timeout` limits how long one tenant's heavy query can hold resources.

<!-- check:observability -->
### Monitoring and alerting

Connections against budget, free storage, long-open transactions, replica lag and transaction ID age are the key alerts; CPU only tickets. `application_name` per workload makes it possible to tell web, worker and reporting load apart.

<!-- check:lifecycle -->
### Operations and lifecycle

Minor versions monthly in regional maintenance windows, major versions through RDS Blue/Green after a staging rehearsal. Runbooks cover long queries, vacuum, failover and restore. PostgreSQL 17 community support runs to late 2029, giving time for a planned major upgrade.

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
  },
  {
    "body": "PostgreSQL Global Development Group",
    "excerpt": "Table owners normally bypass row security unless FORCE ROW LEVEL SECURITY is set; superusers and roles with BYPASSRLS always bypass it.",
    "id": "R2",
    "ident": "PostgreSQL documentation 5.9",
    "kind": "standard",
    "title": "Row Security Policies",
    "url": "https://www.postgresql.org/docs/current/ddl-rowsecurity.html"
  }
]
```

<!-- end -->
