---
id: "RPT-report-infrastructure"
title: "Report infrastructure"
parent: "RPT"
order: 8
type: "capability"
template: "infra"
status: "draft"
owner: null
indicative: false
summary: "Per-region reporting stores (Postgres reporting replica plus rpt schemas built by dbt), reporting roles under forced RLS, BullMQ export and scheduled-email jobs, Temporal submission workers and immutable evidence storage"
links: []
rev: 2
syncHash: "70a949ac55f1ae8a"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.7 Report infrastructure

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Per-region reporting stores (Postgres reporting replica plus rpt schemas built by dbt), reporting roles under forced RLS, BullMQ export and scheduled-email jobs, Temporal submission workers and immutable evidence storage

<!-- section:purpose -->
## Purpose and responsibilities

Runs every report and submission in [[RPT]] without touching the operational primary. Responsibilities:

- Hold a near-real-time copy of operational tables per region (logical replication into a separate reporting Postgres) plus business events from [[OBS-business-events]]
- Build modelled tables (`rpt_stg.*`, `rpt.fct_*`, `rpt.dim_*`, `rpt.agg_*`, `rpt.mis_*`) with dbt; host the metric registry
- Serve tenant dashboards under forced RLS and Nomology views under a separate read-only role ([[MT-cross-tenant-reporting-via-a]])
- Run exports and scheduled emails as BullMQ jobs, and regulator / aggregator submissions as Temporal workflows
- Store submission snapshots and evidence immutably in the region

Dependent services: tenant admin console reports pages, platform admin MIS, submission workflow workers, [[PKG-notifications]] for scheduled emails.

<!-- section:topology -->
## Topology per region

Per region (India `ap-south-1`, Singapore `ap-southeast-1`, US `us-east-1` proposed; Azure equivalents where a client requires Azure):

```
 App primary (Postgres, forced RLS)
     │  logical replication (publication rpt_pub, per-table)
     ▼
 Reporting Postgres (separate instance, Multi-AZ off in non-prod)
   ├─ schema raw      ← replicated tables (same tenant_id, same RLS policies)
   ├─ schema rpt_stg  ← dbt staging views
   ├─ schema rpt      ← facts / dims / aggregates (tenant_id + forced RLS)
   └─ schema rpt_mis  ← tenant-free aggregates for MIS (suppressed)
     │
     ├── PgBouncer (transaction mode) ── report API (Next.js route handlers / tRPC)
     ├── dbt runner (ECS scheduled task, every 15 min / nightly)
     ├── BullMQ workers: queues rpt-export, rpt-scheduled-email
     └── Temporal workers: task queue rpt-submissions
 Object storage bucket  rpt-evidence-<region>  (versioning + object lock)
 Object storage bucket  rpt-exports-<region>   (lifecycle: delete after 7 days)
```

| Environment | Reporting store | dbt schedule | Evidence bucket lock |
|---|---|---|---|
| dev | schemas in the dev primary (no replica) | on demand | none |
| staging | small replica instance | 15 min | governance mode |
| UAT | replica, masked tenant data | 15 min | governance mode |
| production (each region) | dedicated reporting instance | 15 min incremental, nightly full | compliance mode |

<!-- section:sizing -->
## Sizing and scaling

Assumptions (proposed, to be replaced by measured figures): year 1 per region up to 50k cases, 2M stage / document events, 500 GB documents metadata excluded from reporting (only metadata rows). Year 3: 10x.

| Item | Starting size (proposed) | Scale trigger |
|---|---|---|
| Reporting Postgres | 4 vCPU / 16 GB, 200 GB gp3 | CPU > 60% for 1 h at peak, replication lag > 5 min, storage > 70% |
| dbt incremental run | under 5 min | run time > 10 min → split models or move heavy aggregates nightly |
| BullMQ export workers | 2 tasks, concurrency 2 each | waiting jobs > 50 for 10 min |
| Temporal submission workers | 1 task (2 in prod) | schedule-to-start latency > 30 s |
| Exports | max 100k rows synchronous-free; all exports async | export p95 > 2 min |

If row counts at year 3 make dashboard p95 exceed 3 s after indexing and materialisation, revisit the columnar option in the open ADR.

<!-- section:config -->
## Configuration baseline

IaC module `infra/modules/reporting` (Terraform; Bicep variant for Azure) parameterised per region.

- Logical replication: `wal_level=logical` on primary; publication `rpt_pub` lists tables explicitly (no `FOR ALL TABLES`) so new tables are opt-in and reviewed; subscription owned by role `rpt_replicator`.
- RLS on reporting copies: migrations that create a tenant table also create the same policy on the `raw` copy and on every `rpt.*` model that carries `tenant_id` (dbt post-hook `enable_forced_rls(tenant_id)`). Checked by the lint in [[MT-lint-review-check-that-every]].
- Roles: `rpt_tenant_reader` (no BYPASSRLS, not owner; used by tenant dashboards, sets `app.tenant_id` per transaction via the same Prisma extension as [[MT-prisma-client-extension-wraps]]); `rpt_platform_reader` (read-only, BYPASSRLS **only** on `rpt_mis` and on approved `rpt.*` platform views; no access to `raw` personal columns); `rpt_transformer` (dbt, owns models, not used by any reader); `rpt_submission` (tenant-scoped like `rpt_tenant_reader`, plus insert on `report_run*`).
- Timeouts: `statement_timeout=30s` for dashboard roles, `120s` for submission snapshot queries; `idle_in_transaction_session_timeout=60s` ([[INF-timeouts-on-connect-query-and]]).
- Connection settings per workload per [[INF-separate-connection-settings-for]].

<!-- section:resilience -->
## High availability and DR

| Failure | Behaviour | Recovery |
|---|---|---|
| Replication lag or stop | Dashboards show "data as of" the last applied LSN time and a stale banner if > 30 min; scheduled emails held | Alert; restart subscription; resync table if needed |
| Reporting instance lost | Dashboards unavailable; operations unaffected | Restore from snapshot (RPO 24 h) or rebuild from primary by re-creating subscription and running dbt full refresh (target RTO 8 h, proposed) |
| dbt model failure | Previous model state kept; affected views marked stale | Fix and rerun; failing tests block publish |
| Submission workflow worker down | Temporal retries; deadline alert escalates per [[RPT-regulatory-and-aggregator]] | Restart workers; workflow resumes |
| Evidence bucket | Versioned, object-locked; replicated to a second bucket **in the same region** only | Restore object version |

Reporting data is derived and can be rebuilt; submission evidence cannot, so it gets the stricter treatment. Restore drill for the reporting store yearly, evidence retrieval drill quarterly (proposed).

<!-- section:security -->
## Security

- Private subnets only; reachable from report API tasks, dbt runner, BullMQ and Temporal worker security groups on 5432 via PgBouncer.
- TLS `verify-full` everywhere; storage, snapshots and both buckets encrypted with the regional KMS key ([[INF-secrets-and-keys]]).
- Personal data: `raw` holds what replication brings; `rpt.*` models drop or hash personal columns unless a report needs them, and `rpt_mis` contains none. Column-level grants stop `rpt_platform_reader` reading personal columns.
- Exports are written to `rpt-exports-<region>` and served through short-lived signed URLs ([[PKG-encryption-at-rest-signed-urls]]); every export logs `report.exported` to [[PKG-audit-trail]] with user, filters and row count.
- Human access to the reporting store follows [[SEC-access-reviews]] with break-glass logging; no standing write access for humans.

<!-- section:operations -->
## Runbook

Routine: add a table to `rpt_pub` (migration PR plus contract file), dbt deploy via CI, resync a table, rotate role credentials, add a region (apply module with region parameters), restore evidence object. Incident steps: replication stopped; dbt failing tests; export queue stuck; suspected cross-tenant exposure (stop affected report, follow [[SEC-security-incident-response-and]]). Runbook to be written under [[DOC-architecture-docs-adrs-runbooks]].

<!-- section:observability -->
## Monitoring and alerts

| Signal | Alert (proposed) | Route |
|---|---|---|
| Replication lag per subscription | > 10 min warn, > 30 min page in business hours | Platform on-call |
| dbt run status and test failures | any `error` test failure | Data owner channel |
| Source freshness (dbt `freshness`) [R2] | warn 1 h, error 2 h for operational sources | Data owner |
| Export queue waiting / failed | waiting > 50 for 10 min; failed > 5 in 1 h | Platform on-call |
| Submission workflows nearing deadline without approval | T-5 d, T-2 d, T-4 h | Tenant compliance officer and backup |
| Rows returned to `rpt_tenant_reader` with no tenant set | must always be 0; any non-zero pages security | Security on-call |

<!-- section:cost -->
## Cost

Proposed estimate per production region: reporting Postgres instance and storage plus snapshots, a small always-on ECS footprint for workers, dbt runs as scheduled tasks, and object storage for evidence. Main drivers: number of replicated tables and event volume, dashboard concurrency, evidence retention years. Numbers to be produced from the AWS / Azure calculators once sizing is confirmed; budget alerts per region tagged `component=reporting` [R3].

<!-- section:readiness -->
## Production readiness

Go-live checklist (status: not started): isolation tests pass against `rpt_tenant_reader` and `rpt_submission`; replication publication reviewed; dbt tests and freshness configured for every source; restore drill done; evidence bucket object lock verified; alert routes tested per region; export audit events verified; runbook published.

<!-- section:questions -->
## Open questions

- [ ] ADR: Postgres reporting instance with dbt versus a columnar store (ClickHouse / Redshift / Synapse) per region; recommendation is Postgres first
- [ ] Logical replication from the primary versus CDC through Debezium; logical replication is simpler but couples schema changes
- [ ] Where the internal MIS store lives and which region hosts it; whether some tenants' contracts forbid even aggregated rows leaving the region
- [ ] Evidence retention period per obligation (drives object lock duration); needs legal input from [[RPT-compliance-reports]]
- [ ] Is a dashboard library (embedded BI) acceptable, or are dashboards built with our own components and [[PKG-data-visualisation-palette]]?

<!-- checks -->
## Template checks

<!-- check:security -->
### Security

Private subnets only, reached via PgBouncer from four named security groups; TLS verify-full; regional KMS keys for storage, snapshots and buckets. Reader roles are least-privilege: `rpt_tenant_reader` has no BYPASSRLS and owns nothing; `rpt_platform_reader` is limited to tenant-free `rpt_mis` and approved views with column grants excluding personal columns; dbt runs as `rpt_transformer`, which no reader uses. Credentials live in the regional secrets manager and rotate per [[INF-secrets-and-keys]].

<!-- check:residency -->
### Data residency

Reporting store, buckets, workers and dbt runs are created by the same module per region; nothing tenant-grain is replicated cross-region, and the evidence bucket's replica is in the same region. The only cross-region flow is the `rpt_mis` aggregate export to the MIS store, which carries no personal data and applies small-count suppression; its destination is an open question. India-region logs from these components stay in India, in line with CERT-In log retention directions [R1].

<!-- check:dr -->
### Resilience and recovery

Reporting store: RPO 24 h, RTO 8 h (proposed), because it can be rebuilt from the primary plus a dbt full refresh; yearly restore drill. Submission evidence: RPO 0 via versioned, object-locked bucket, same-region replica; quarterly retrieval drill. Temporal submission workflows resume after worker restart; deadline alerts cover prolonged outages.

<!-- check:isolation -->
### Tenant isolation and noisy neighbours

Forced RLS on every tenant-grain table in `raw` and `rpt`, applied by migration and dbt post-hook and checked by lint. Tenant set per transaction with `set_config('app.tenant_id', id, true)` through PgBouncer transaction pooling, so nothing carries across clients [R4]. A missing tenant returns zero rows, tested and monitored. Resource fairness: BullMQ `rpt-export` uses per-tenant concurrency limit 1 and a row cap; `statement_timeout` 30 s on dashboard roles.

<!-- check:iac -->
### Infrastructure as code and change control

Terraform module `infra/modules/reporting` with one parameter file per region and environment (Bicep variant for Azure); publication table lists live in migrations, dbt in `packages/reporting`. Plans run in CI, applied from the pipeline identity after code-owner approval; scheduled drift detection weekly.

<!-- check:observability -->
### Monitoring and alerting

Alerts on replication lag, dbt failures, source freshness, export queue health, submission deadlines and the zero-rows-without-tenant canary, each with an owner and runbook step (see Monitoring and alerts).

<!-- check:cost -->
### Cost

Driven by replicated table count, event volume, dashboard concurrency and evidence retention. Resources are tagged `component=reporting`, `region`, `env`; per-region budgets and anomaly alerts route to the reporting owner. Estimates still to be produced (open).

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Cyber incidents of the listed types must be reported to CERT-In within 6 hours of noticing; logs of ICT systems must be maintained for a rolling period of 180 days within Indian jurisdiction.",
    "id": "R1",
    "issued": "2022-04-28",
    "issuer": "CERT-In, Ministry of Electronics and Information Technology",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Directions under section 70B(6) of the IT Act, 2000 (No. 20(3)/2022-CERT-In)",
    "title": "CERT-In Directions relating to information security practices, procedure, prevention, response and reporting of cyber incidents",
    "url": "https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf"
  },
  {
    "excerpt": "Freshness blocks define warn_after and error_after thresholds against a loaded_at field for each source.",
    "id": "R2",
    "kind": "vendor",
    "title": "dbt documentation: source freshness",
    "url": "https://docs.getdbt.com/reference/resource-configs/freshness",
    "vendor": "dbt Labs"
  },
  {
    "excerpt": "Design principles for cost-aware architectures.",
    "id": "R3",
    "kind": "vendor",
    "title": "AWS Well-Architected Framework: Cost Optimization Pillar",
    "url": "https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html",
    "vendor": "Amazon Web Services"
  },
  {
    "excerpt": "Session-level features such as SET (non-LOCAL) and LISTEN are not compatible with transaction pooling.",
    "id": "R4",
    "kind": "vendor",
    "title": "PgBouncer features (what works under transaction pooling)",
    "url": "https://www.pgbouncer.org/features.html",
    "vendor": "PgBouncer"
  }
]
```

<!-- end -->
