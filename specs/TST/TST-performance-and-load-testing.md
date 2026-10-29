---
id: "TST-performance-and-load-testing"
title: "Performance and load testing"
parent: "TST"
order: 3
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 2
syncHash: "2af3e599b5068cef"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 16.3 Performance and load testing

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

Defines how we show that each regional stack meets its latency, throughput and capacity targets at realistic and peak volumes, and that one tenant's load cannot degrade others. It covers load models per tenant type, scenarios, targets, where tests run and when. Frontend budgets are in [[APP-frontend-performance-budgets]]; production monitoring in [[OBS-performance]].

<!-- section:rules -->
## Rules

**Load model** (proposed; to be replaced with forecasts from product and client success)

| Tenant type | Shape of load | Peak driver |
|---|---|---|
| SEBI ODR institution (`odr-inst`) | Many small matters, bulk intake from aggregators, many unrepresented parties on mobile | Aggregator batch intake; deadline-day filings |
| Arbitral institution (`arb-inst`) | Fewer, larger cases; large bundles; long hearings | Hearing days: bundle opening, transcript streaming, document search |
| CORD tenant (`cord`) | Mixed online dispute resolution volume | Notice campaigns (bulk service of notices) |

**Rules**
- **PERF-1** Each region is tested at 1 × and 2 × its forecast peak before its first production tenant, at every phase boundary from Phase 3, and before any release that changes database indexes on large tables, caching or Temporal task queue layout.
- **PERF-2** Scenarios (each a k6 script in `tests/load/`):
  1. Secretariat queue: 200 concurrent secretariat users filtering and bulk-acting on a queue of 20,000 cases.
  2. Aggregator intake: bulk filing of 10,000 matters through [[INT-aggregator-intake-api]] in one hour, with idempotency-key retries.
  3. Hearing day: 50 concurrent hearings, each with 10 participants opening a 5,000-page bundle and searching it.
  4. Notice campaign: 50,000 notices queued through BullMQ and delivered via provider sandboxes.
  5. Upload: 100 concurrent multi-gigabyte resumable uploads with malware scanning.
  6. Workflow throughput: 100,000 open case workflows with daily timers firing in the same minute.
  7. Noisy neighbour: one tenant at 5 × its normal rate while others run normal load.
- **PERF-3** Proposed targets at 1 × peak, per region:

| Measure | Target |
|---|---|
| API reads (tRPC and public API), p95 | under 300 ms |
| API writes, p95 | under 800 ms |
| Search, p95 | under 1.5 s |
| Error rate | under 0.1% |
| Temporal schedule-to-start latency, p95 | under 2 s |
| BullMQ queue wait, p95 (notifications) | under 30 s |
| PgBouncer client wait, p95 | under 50 ms |

At 2 × peak the system may slow down but must not fail: error rate under 1% and no data loss.
- **PERF-4** In the noisy-neighbour scenario, other tenants' p95 latency rises by no more than 20%, and per-tenant rate limits ([[APP-api-versioning-rate-limiting]]) engage.
- **PERF-5** Tests run in staging in the region under test, sized like production for the test window, with synthetic data at production-like volume per tenant type (seeded by `pnpm seed --profile load`). Never against production.
- **PERF-6** Results (k6 summary, database and pooler metrics, traces) are stored with the release ID and compared with the previous run; a regression of more than 20% at p95 on any scenario blocks the phase gate until explained.
- **PERF-7** A smaller "performance smoke" (scenarios 1 and 2 at 0.25 × peak) runs nightly in one staging region to catch regressions early.

<!-- section:rationale -->
## Rationale

- Scenarios mirror the moments tenants actually stress the platform; a generic requests-per-second test would miss Temporal timer storms and PgBouncer pool exhaustion.
- PERF-4 matters because all tenants in a region share one database and one PgBouncer pool under [[ADR-tenant-isolation]].

<!-- section:tooling -->
## Tooling and configuration

- k6 (scripts in TypeScript), run from k6 runners in the same region as the stack under test.
- Seed profile `load` in `@nomology/testing` generating synthetic cases, documents and hearings at volume.
- Observability: OpenTelemetry traces and metrics, PgBouncer `SHOW POOLS` metrics, Temporal server metrics ([[OBS-foundations]]).

<!-- section:enforcement -->
## Enforcement

PERF-1 and PERF-6 are phase-gate and promotion checks recorded on the change record for qualifying releases; PERF-7 is a nightly job that opens a ticket on regression. Scenario definitions are code-reviewed by the owning domain team.

<!-- section:examples -->
## Examples

Good: before Phase 4 exit, staging-in runs scenario 6 and finds timers firing at 00:00 IST cause a 40-second schedule-to-start delay; reminders are jittered across the hour and the rerun meets target.

Bad: a load test against dev with 10 tenants and 100 cases, reported as "load tested".

<!-- section:exceptions -->
## Exceptions

A phase gate may pass with a scenario below target only through a recorded risk acceptance by the CTO with a fix date.

<!-- section:questions -->
## Open questions

- [ ] Forecast peak volumes per region and tenant type (tenants, cases per month, concurrent hearings, aggregator batch sizes) from product and client success.
- [ ] Are the proposed latency targets consistent with client SLAs?
- [ ] Do we need a dedicated performance environment, or scale staging temporarily?
- [ ] Azure deployments: run the same scenarios before each Azure client goes live?

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Load tests are a phase-gate and qualifying-release gate with stored, comparable results; the nightly smoke job is automated. Targets live in the scripts as k6 thresholds so a breach fails the run.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

Synthetic data only; never against production; noisy-neighbour scenario tests the shared-database isolation model from a capacity angle.

<!-- check:measurement -->
### Adoption measurement

p95 per scenario over time per region, shown on the performance dashboard; regressions over 20% flagged.

<!-- check:ownership -->
### Ownership and change

Owner: platform engineering (performance champion to be named); domain teams own their scenarios.

<!-- end -->
