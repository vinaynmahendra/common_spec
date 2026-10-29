---
id: "RPT-transcribers"
title: "Transcribers"
parent: "RPT-platform-stats"
order: 3
type: "feature"
template: "report"
status: "draft"
owner: null
indicative: false
summary: "Transcription turnaround against target, quality review outcomes, transcriber workload, pending vendor bills and unpaid transcription invoices"
links: []
rev: 2
syncHash: "928929de1a8ae453"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.1.3 Transcribers

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Transcription turnaround against target, quality review outcomes, transcriber workload, pending vendor bills and unpaid transcription invoices

<!-- section:audience -->
## Audience and questions

| Persona | Frequency | Questions |
|---|---|---|
| Transcription coordinator (TERES) | daily | Q1 Which assignments are at risk of missing the turnaround target? Q2 What is each transcriber's queue? |
| Quality lead | weekly | Q3 What share of transcripts pass first quality review, and what errors recur? |
| Tenant / Nomology finance | weekly | Q4 Which transcriber bills are pending, and which transcription invoices are unpaid? |
| Transcriber (own view) | on demand | Q5 My assignments, deadlines and payment status |

<!-- section:metrics -->
## Metric definitions

Owner of sources: Transcribers domain team. Table names are proposals pending [[DOM-transcribers-schema]].

| ID | Metric | Formula | Grain | Inclusions / exclusions | Source |
|---|---|---|---|---|---|
| TRN-M1 | Turnaround (hours) | `delivered_at − media_available_at` | assignment | excludes cancelled; re-assigned work measured from first availability | `transcriber_assignments` |
| TRN-M2 | On-time rate | delivered assignments with `delivered_at ≤ due_at` ÷ delivered assignments | tenant × service level (same-day, 24 h, 72 h) × period | `due_at` set from ordered service level | same |
| TRN-M3 | At-risk assignments | open assignments where `due_at − now` < 25% of the service-level window | transcriber × now | | same |
| TRN-M4 | Audio hours delivered | sum of media duration for delivered assignments | transcriber × period | | `transcriber_assignments`, `hearing_recordings` |
| TRN-M5 | First-pass quality rate | reviews with outcome `pass` on first review ÷ reviews | transcriber × period | only reviewed assignments | `transcript_quality_reviews` |
| TRN-M6 | Error rate per audio hour | review error count ÷ audio hours reviewed, by error category | tenant × category × period | | same |
| TRN-M7 | Pending transcriber bills | as NEU-M6 with `payee_type = transcriber` | tenant × currency | | `vendor_bills` |
| TRN-M8 | Unpaid transcription invoices | outstanding on invoices `kind = transcription` | tenant × currency × age bucket | | `invoices` |

Where AI draft transcription is used ([[WF-long-running-pipelines]]), TRN-M1 is split into machine and human stages so delays are visible by stage.

<!-- section:dimensions -->
## Dimensions and filters

Service level, hearing / case, transcriber (restricted), language, media type, period, currency.

<!-- section:freshness -->
## Freshness and delivery

TRN-M3 every 5 minutes (operational queue is in [[APP-transcriber-workspace]]; this report is the summary). Others nightly.

<!-- section:lineage -->
## Data sources and lineage

`transcriber_assignments`, `transcript_quality_reviews`, `hearing_recordings` metadata ([[DOM-hearings-schema]]), `vendor_bills`, `invoices` → `rpt.fct_transcription_assignment`, `rpt.fct_transcript_review`.

<!-- section:quality -->
## Data quality and reconciliation

`delivered_at ≥ media_available_at`; every delivered assignment has a service level; audio hours reconcile to recording metadata totals per day.

<!-- section:access -->
## Access and privacy

As [[RPT-neutrals]]: aggregates by default, individual rows behind `reports.transcriber_individual`, self-view for transcribers. Transcribers may be contractors in several countries; their individual data stays in the tenant's region.

<!-- section:questions -->
## Open questions

- [ ] Service-level catalogue (same-day, 24 h, 72 h) and whether targets are per tenant contract
- [ ] Are transcriber quality scores shared with the transcriber, and is there an appeal path
- [ ] Error category list for TRN-M6

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Tenant users query `rpt.*` as `rpt_tenant_reader` with `app.tenant_id` set per transaction through the same Prisma extension as the app ([[MT-prisma-client-extension-wraps]]); every table behind this report carries `tenant_id` with forced RLS [R1], so isolation does not depend on a WHERE clause. With no tenant set the query returns zero rows (tested). Nomology staff use the separate platform view under `rpt_platform_reader` ([[MT-cross-tenant-reporting-via-a]]). Export and email jobs carry `tenantId` in the BullMQ job payload and re-set the tenant before querying; cache keys are prefixed `rpt:{tenantId}:` ([[PKG-caching]]). The cross-tenant suite in [[TST-multi-tenant-isolation-tests]] logs in as tenant A and asserts no tenant B row in any metric, drill-down or export.

<!-- check:residency -->
### Residency and cross-region figures

Computed, stored, emailed and exported in the tenant's home region ([[MT-data-residency-2]]) from the regional reporting store in [[RPT-report-infrastructure]]; scheduled emails are sent through the regional messaging provider ([[INT-messaging-providers]]). The platform view across tenants reads per-region aggregates at tenant × day grain with no personal data; nothing tenant-grain is copied to another region. Transcribers working from other countries see their own rows through the tenant's region; no copy is made for them.

<!-- check:definitions -->
### Metric semantics

Turnaround starts at media availability, not at assignment, so re-assignment does not reset the clock; machine and human stages are split where AI drafting is used. On-time is measured against the ordered service level at the time of order.

<!-- check:security -->
### Access, privacy and export

Individual transcriber performance gated by a separate permission; self-view only for transcribers; exports audited.

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
