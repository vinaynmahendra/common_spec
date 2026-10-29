---
id: "RPT-platform-stats"
title: "Platform stats"
parent: "RPT"
order: 1
type: "capability"
template: "report"
status: "draft"
owner: null
indicative: false
summary: "Parent for operational platform reports (cases, neutrals, transcribers, documents): shared conventions for tenant and platform views, time, currency, and drill-down"
links: []
rev: 4
syncHash: "02e91fa2695db178"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.1 Platform stats

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Parent for operational platform reports (cases, neutrals, transcribers, documents): shared conventions for tenant and platform views, time, currency, and drill-down

<!-- section:audience -->
## Audience and questions

Parent node. Its children answer operational questions for three audiences:

| Audience | Where | Cadence | Children |
|---|---|---|---|
| Tenant admin, secretariat lead / registrar (arbitral institution tenant, SEBI ODR institution tenant, CORD tenant) | `/(tenant-admin)/reports/*` in [[APP-tenant-admin-console]] | daily / weekly | [[RPT-cases]], [[RPT-neutrals]], [[RPT-transcribers]], [[RPT-documents]] |
| Nomology operations and account managers | `/(platform-admin)/reports/*` | weekly | same reports in platform view (counts and amounts across tenants) |
| Tenant finance | tenant reports and scheduled email | monthly | unpaid invoice sections of each child |

Questions common to all children: What is open and how old is it? Where are we breaching targets? What money is owed, to whom and by whom? Which items need action now?

<!-- section:metrics -->
## Metric definitions

Children define their metrics. Shared conventions every child metric must follow (part of the metric contract):

| Convention | Rule |
|---|---|
| Time zone | Day and month boundaries use the **tenant's reporting time zone** (setting `reporting.timezone`, default from tenant seat: `Asia/Kolkata`, `Asia/Singapore`, `America/New_York`); stored timestamps are UTC |
| Day counting | Calendar days unless the metric says business days; business days use [[PKG-calendars-and-deadline]] with the case's calendar |
| Exclusions | Always exclude test / sandbox cases (`cases.is_test = true`), tenants flagged `tenant.kind = 'sandbox'`, and soft-deleted rows |
| Currency | Amounts shown per currency; no conversion in tenant views. Platform view converts to INR / SGD / USD only in [[RPT-internal-mis]] |
| Snapshots | "As at" metrics are taken at 00:00 tenant time for history; live tiles use latest replicated state |
| Rule versions | Targets from decision tables use the version in force on the day measured |

<!-- section:dimensions -->
## Dimensions and filters

Shared dimensions: tenant (platform view only), organisation unit, product (CORD / TERES), case type, rule set (for example SEBI ODR, institutional arbitration rules), region (platform view), period. Default filter: last 90 days, open items, current tenant.

<!-- section:freshness -->
## Freshness and delivery

Operational tiles: refreshed every 15 minutes from the reporting store; history models nightly. Delivery: dashboard, CSV export (async, BullMQ `rpt-export`), scheduled weekly email with summary and link (no attachments containing personal data). Each child may tighten this.

<!-- section:access -->
## Access and privacy

Permissions: `reports.view`, `reports.export`, `reports.schedule`, held by tenant admin and secretariat lead roles by default ([[PKG-policy-engine-permission-matrix]]). Drill-down to case lists re-checks case-level access ([[PKG-rbac-abac-case-level-party]]) and honours ethical walls ([[PKG-ethical-walls-conflict-based]]).

<!-- section:questions -->
## Open questions

- [ ] Default reporting time zone where a tenant has seats in several countries
- [ ] Is a platform-wide "your figures versus platform median" benchmark wanted for tenants; if so, minimum comparison group size
- [ ] Which reports are in the first release for the arbitral institution tenant versus the SEBI ODR institution tenant

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Tenant users query `rpt.*` as `rpt_tenant_reader` with `app.tenant_id` set per transaction through the same Prisma extension as the app ([[MT-prisma-client-extension-wraps]]); every table behind this report carries `tenant_id` with forced RLS [R1], so isolation does not depend on a WHERE clause. With no tenant set the query returns zero rows (tested). Nomology staff use the separate platform view under `rpt_platform_reader` ([[MT-cross-tenant-reporting-via-a]]). Export and email jobs carry `tenantId` in the BullMQ job payload and re-set the tenant before querying; cache keys are prefixed `rpt:{tenantId}:` ([[PKG-caching]]). The cross-tenant suite in [[TST-multi-tenant-isolation-tests]] logs in as tenant A and asserts no tenant B row in any metric, drill-down or export.

<!-- check:residency -->
### Residency and cross-region figures

Computed, stored, emailed and exported in the tenant's home region ([[MT-data-residency-2]]) from the regional reporting store in [[RPT-report-infrastructure]]; scheduled emails are sent through the regional messaging provider ([[INT-messaging-providers]]). The platform view across tenants reads per-region aggregates at tenant × day grain with no personal data; nothing tenant-grain is copied to another region.

<!-- check:definitions -->
### Metric semantics

Shared conventions (time zone, calendars, exclusions, currency, snapshots, rule versions) are fixed here and referenced by every child's metric table, so two analysts get the same number. Each child metric has an ID in the metric registry in [[RPT-report-infrastructure]].

<!-- check:performance -->
### Performance and cost

Queries run on the regional reporting store, never the primary; tiles read pre-aggregated `rpt.agg_*` tables refreshed by dbt; exports run as BullMQ `rpt-export` jobs with a per-tenant concurrency of 1 and a row cap (proposed 100k rows), so a large export cannot slow other tenants.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Table owners normally bypass row security; ALTER TABLE ... FORCE ROW LEVEL SECURITY makes policies apply to the owner as well.",
    "id": "R1",
    "kind": "vendor",
    "title": "PostgreSQL documentation: Row Security Policies",
    "url": "https://www.postgresql.org/docs/current/ddl-rowsecurity.html",
    "vendor": "PostgreSQL Global Development Group"
  }
]
```

<!-- end -->
