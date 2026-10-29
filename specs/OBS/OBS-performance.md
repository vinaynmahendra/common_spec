---
id: "OBS-performance"
title: "Performance"
parent: "OBS"
order: 3
type: "capability"
template: "observability"
status: "draft"
owner: null
indicative: false
summary: "Latency, error and throughput signals and SLOs for the API, database, background jobs and Temporal pipelines (transcription, OCR, eBundling, AI), with UI Core Web Vitals delegated to RUM"
links: []
rev: 2
syncHash: "869beb2b4c3034d5"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 11.3 Performance

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Latency, error and throughput signals and SLOs for the API, database, background jobs and Temporal pipelines (transcription, OCR, eBundling, AI), with UI Core Web Vitals delegated to RUM

<!-- section:purpose -->
## Purpose

Answers: *Is the platform fast and reliable enough for each persona in each region, and where is time being spent?* Covers three layers:

1. **API and server rendering** (tRPC, REST public API, Server Actions, page renders).
2. **Background work**: BullMQ jobs and Temporal pipelines ([[WF-long-running-pipelines]]): transcription, OCR, eBundling, AI processing, notifications.
3. **UI**: Core Web Vitals and client errors, specified in [[OBS-frontend-real-user-monitoring]]; budgets in [[APP-frontend-performance-budgets]].

Users: engineering teams (tuning), platform on-call (SLO alerts), and [[RPT-platform-performance]] (management and client reporting).

<!-- section:catalogue -->
## Event catalogue

| Event | When | Emitter | Attributes | PII |
|---|---|---|---|---|
| `nomo.pipeline.completed` | A pipeline run finishes | Temporal workflow (via activity) | `pipeline.type` (`transcription`, `ocr`, `ebundle`, `ai_summary`, `translation`), `outcome` (`success`, `failed`, `cancelled`), `duration_s`, `size.pages` or `size.audio_min`, `nomo.tenant.id` | No |
| `nomo.pipeline.deadline_missed` | A pipeline exceeds its target time | Temporal timer in the workflow | `pipeline.type`, `target_s`, `nomo.tenant.id` | No |
| `nomo.slow_request` | Server request > 2 s | Web span processor (log record linked to trace) | `http.route`, `duration_s`, `db.call_count` | No |

<!-- section:metrics -->
## Metrics

| Metric | Instrument | Unit | Labels | Source |
|---|---|---|---|---|
| `http.server.request.duration` | Histogram | `s` | `http.route`, `http.request.method`, `http.response.status_code`, `nomo.persona`, `api.family` (`trpc`, `rest`, `action`, `page`) | OTel HTTP instrumentation |
| `rpc.server.duration` (tRPC procedures) | Histogram | `s` | `rpc.method` (procedure path), `nomo.persona`, `outcome` | tRPC middleware in [[APP-internal-api-trpc-routers-per]] |
| `db.client.operation.duration` | Histogram | `s` | `db.operation.name`, `db.collection.name` | Prisma instrumentation |
| `nomo.job.duration` / `nomo.job.wait_time` | Histogram | `s` | `queue`, `job.name`, `outcome` | BullMQ worker wrapper |
| `nomo.job.waiting` / `nomo.job.failed` | Gauge | `{job}` | `queue` | BullMQ queue metrics poller |
| Temporal SDK `temporal_activity_schedule_to_start_latency` | Histogram | `s` | `task_queue`, `activity_type` | Temporal SDK metrics |
| Temporal SDK `temporal_workflow_endtoend_latency` | Histogram | `s` | `workflow_type` | Temporal SDK metrics |
| `nomo.pipeline.duration` | Histogram | `s` | `pipeline.type`, `outcome`, `size.band` | From `nomo.pipeline.completed` |

Histogram buckets for request duration: 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10 s. Per-tenant latency is analysed from traces, not from metric labels.

<!-- section:sli -->
## SLIs and SLOs

All SLOs proposed, per region, 28-day window.

| Journey | SLI (good / valid) | Measured at | SLO |
|---|---|---|---|
| API availability | Requests not returning 5xx or our own 429 / all valid requests | `web` server span; ALB when no span | 99.9% |
| Interactive reads (tRPC queries, page renders) | Requests completing < 1 s / all | Server span | 99% |
| Interactive reads, fast path | Requests completing < 300 ms / all | Server span | 90% |
| Mutations (filing, uploads metadata, approvals) | Completing < 2 s / all | Server span | 99% |
| Public API (REST) | Completing < 1 s and not 5xx / all | Server span | 99.5% |
| Notification hand-off | Legal notices handed to provider < 5 min from creation / all | BullMQ job completion | 99% |
| eBundle generation | Bundles ≤ 2,000 pages issued < 15 min / all | `nomo.pipeline.completed` | 99% |
| OCR | Documents ≤ 200 pages OCR-complete < 10 min / all | `nomo.pipeline.completed` | 99% |
| Transcription | Machine draft available < 2 × audio length / all | `nomo.pipeline.completed` | 95% |

Human transcription turnaround against tenant contracts is a business measure in [[RPT-transcribers]], not an engineering SLO.

**Error budget policy** (shared, in [[OBS-alerting#sli]]): when a region exhausts a 28-day budget, feature releases to that region pause except reliability fixes until the budget recovers, and a review is held within 5 business days [R1].

<!-- section:alerts -->
## Alerts

| Condition | Severity | Route | Runbook |
|---|---|---|---|
| API availability burn rate 14.4× over 1 h (and 5 min) | Page | Region platform on-call | `runbooks/api-availability.md` |
| API availability burn rate 6× over 6 h (and 30 min) | Page | Region platform on-call | same |
| Interactive read latency SLO burn 6× over 6 h | Page (business hours) / ticket | Owning team by route group | `runbooks/latency.md` |
| Any SLO burn 1× over 3 days | Ticket | Owning team | |
| Pipeline SLO burn 6× over 6 h | Page | Pipelines team | `runbooks/pipelines.md` |
| BullMQ `failed` growth on legal-notice queues | Page | Platform on-call | `runbooks/bullmq.md` |

Burn-rate windows follow the multiwindow, multi-burn-rate approach [R2].

<!-- section:dashboards -->
## Dashboards

- **SLO overview** (per region): every SLO, budget remaining, burn rate. Audience: engineering leads, on-call.
- **API by route group** (per persona): latency percentiles, error rate, top slow procedures, DB time share. Audience: domain teams.
- **Pipelines**: duration percentiles per pipeline type and size band, backlog, deadline misses. Audience: pipelines team, operations.
- **Database path**: query duration, pool waits ([[INF-monitor-pool-usage-wait-times]]).

<!-- section:pipeline -->
## Collection pipeline

Standard pipeline in [[OBS-foundations#pipeline]]. SLO calculations run as recording rules in the regional metrics store; the SLO definitions live as code in `observability/slo/*.yaml` (one file per journey, region list, target, window) and generate both recording rules and burn-rate alerts.

<!-- section:retention -->
## Retention and privacy

Metrics 13 months (needed for year-on-year SLO reporting to clients); traces 14 days; pipeline events 13 months in aggregated form. No personal data in any of these signals.

<!-- section:questions -->
## Open questions

- [ ] Confirm SLO targets with product leads and check against client SLAs (SLOs must be stricter than SLAs).
- [ ] Which client contracts include tenant-specific performance commitments that need separate tracking?
- [ ] eBundle and OCR size limits used in the SLIs — match product limits?
- [ ] Who signs the error budget policy (CTO and product lead proposed)?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant and region tagging

Metrics do not carry tenant labels; per-tenant latency is analysed from traces, which carry `nomo.tenant.id`. Pipeline events carry tenant ID for Reporting. Region comes from resource attributes, so dashboards are always per region.

<!-- check:naming -->
### Naming and schema

Standard OTel metrics are reused (`http.server.request.duration`, `db.client.operation.duration`, Temporal SDK metrics); custom ones use the `nomo.` prefix and are registered. Labels are bounded: route templates and procedure paths, never IDs.

<!-- check:slo -->
### SLIs, SLOs and error budgets

Each SLI is good / valid at a stated measurement point (server span, ALB, pipeline completion event), with exclusions (health checks, synthetic traffic, client-caused 4xx) defined in [[OBS-foundations#sli]]. Long-running journeys have their own SLIs (notification hand-off, eBundle, OCR, transcription). SLOs are per region, 28 days, with an error budget policy based on the SRE workbook example [R1]; signatories are an open question.

<!-- check:actionability -->
### Alerts and response

Paging is on multiwindow, multi-burn-rate SLO alerts [R2]; slow burns create tickets. Each alert names the owning team by route group or pipeline and links a runbook with first steps (check recent deploy, DB pool waits, pause the offending queue).

<!-- check:cost -->
### Volume and cost

Histogram series are bounded by route templates (about 200) × methods × status classes × personas; estimated under 50k active series per region at launch (to be measured).

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "An example policy stating what happens when a service exceeds its error budget.",
    "id": "R1",
    "kind": "web",
    "publisher": "Google",
    "title": "SRE Workbook: Example error budget policy",
    "url": "https://sre.google/workbook/error-budget-policy/"
  },
  {
    "excerpt": "Recommends multiwindow, multi-burn-rate alerts, e.g. page at 14.4x burn over 1 hour (with a 5-minute short window) and 6x over 6 hours (30-minute short window); ticket at 1x over 3 days.",
    "id": "R2",
    "kind": "web",
    "publisher": "Google",
    "title": "SRE Workbook: Alerting on SLOs",
    "url": "https://sre.google/workbook/alerting-on-slos/"
  }
]
```

<!-- end -->
