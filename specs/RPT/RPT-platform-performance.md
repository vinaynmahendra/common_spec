---
id: "RPT-platform-performance"
title: "Platform performance"
parent: "RPT"
order: 4
type: "capability"
template: "report"
status: "draft"
owner: null
indicative: false
summary: "SLO attainment and trends for API, UI (Core Web Vitals) and pipelines / workflows per region and persona journey, for engineering, management and tenant SLA reporting"
links: []
rev: 2
syncHash: "1786119d45841b65"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.4 Platform performance

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> SLO attainment and trends for API, UI (Core Web Vitals) and pipelines / workflows per region and persona journey, for engineering, management and tenant SLA reporting

<!-- section:audience -->
## Audience and questions

| Persona | Frequency | Questions |
|---|---|---|
| Engineering leads / on-call review | weekly | Q1 Did each service meet its SLO, and how much error budget is left? Q2 Which routes or workflows got slower? |
| Management | monthly | Q3 Did we meet contractual availability per region and per client? |
| Tenant admin (own tenant) | monthly | Q4 What availability and performance did our users experience? |
| TERES / CORD operations | weekly | Q5 Are transcription, OCR, bundling and AI pipelines meeting their turnaround? |

<!-- section:metrics -->
## Metric definitions

Source signals come from [[OBS-performance]], [[OBS-frontend-real-user-monitoring]] and [[OBS-uptime-synthetic-monitoring]]; this report only aggregates them.

| ID | Metric | Formula | Grain | Notes |
|---|---|---|---|---|
| PERF-M1 | Availability | good minutes ÷ total minutes, where a minute is good if synthetic journey checks pass in that region | region × journey × month | excludes announced maintenance only if the client contract allows |
| PERF-M2 | API success rate | non-5xx responses ÷ all responses (4xx count as success) | region × route group × day | |
| PERF-M3 | API latency p95 / p99 | from request duration histograms | region × route template × day | route templates only, no IDs |
| PERF-M4 | Core Web Vitals p75 | LCP, INP, CLS from RUM | region × route group × day | per [[APP-frontend-performance-budgets]] |
| PERF-M5 | Error budget remaining | 1 − (bad events ÷ allowed bad events) | SLO × 28-day window | |
| PERF-M6 | Workflow / pipeline duration | p50 / p95 of workflow run time by workflow type | region × workflow type × day | from Temporal metrics and visibility |
| PERF-M7 | Queue latency | BullMQ wait time p95 by queue | region × queue × day | |
| PERF-M8 | Tenant-experienced availability | PERF-M1 restricted to the tenant's region, plus tenant-tagged API success | tenant × month | tenant view |

<!-- section:dimensions -->
## Dimensions and filters

Region, cloud (AWS / Azure), environment (production only by default), route group / persona, workflow type, tenant (tenant view and internal), period.

<!-- section:layout -->
## Layout and views

SLO overview table (target, actual, budget left); trends per SLO; pipeline panel; monthly SLA report per tenant (PDF) generated in the tenant's region.

<!-- section:freshness -->
## Freshness and delivery

Engineering dashboards: near real time in the observability tool. This report: daily aggregates, monthly frozen SLA report on business day 3.

<!-- section:lineage -->
## Data sources and lineage

OpenTelemetry metrics in the regional observability backend → daily export job → `rpt.agg_perf_daily` (no tenant data except tenant ID tag where applicable).

<!-- section:quality -->
## Data quality and reconciliation

Gaps in synthetic data larger than 15 minutes are flagged and not counted as good or bad; SLA report numbers reconcile to the underlying daily aggregates.

<!-- section:access -->
## Access and privacy

Engineering and management: all regions. Tenant admins: their own tenant's PERF-M8 and region-level PERF-M1 only.

<!-- section:questions -->
## Open questions

- [ ] Which SLOs are contractual per client, and does maintenance count as downtime
- [ ] Do tenants receive the SLA report automatically or on request
- [ ] Retention of daily performance aggregates (proposed 3 years)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Tenant views read only tenant-tagged aggregates and region-level figures; tenant tags are added by the instrumentation layer ([[OBS-foundations]]) and the tenant view filters by RLS on `rpt.agg_perf_daily.tenant_id`; region-level figures contain no tenant data.

<!-- check:residency -->
### Residency and cross-region figures

Performance aggregates are built in each region from the regional observability backend. Tenant-tagged rows stay in the region; cross-region engineering views use region-level aggregates that contain no tenant or personal data.

<!-- check:definitions -->
### Metric semantics

Availability is defined by synthetic journey checks per region, with an explicit rule for data gaps and maintenance; latency uses route templates; error budgets use a 28-day window.

<!-- check:quality -->
### Data quality and reconciliation

Synthetic-check gaps longer than 15 minutes are excluded and flagged rather than counted as good or bad, and the monthly SLA report must reconcile to the daily aggregates before it is released.

<!-- check:performance -->
### Performance and cost

Volumes are small (daily aggregates); heavy computation stays in the observability backend.

<!-- end -->
