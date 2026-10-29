---
id: "ADR-workflow-engine"
title: "Workflow engine"
parent: "ADR"
order: 4
type: "decision"
template: "adr"
status: "approved"
owner: null
indicative: false
summary: "Combination of Temporal, code-defined state machines and queue-based jobs, chosen per scenario (see Section 7)"
links: []
rev: 2
syncHash: "906816d4b911410a"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 19.4 Workflow engine

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Combination of Temporal, code-defined state machines and queue-based jobs, chosen per scenario (see Section 7)

<!-- section:context -->
## Context and problem

**Question:** what runs our processes: multi-week case lifecycles with deadlines and human steps, entity status changes, and short background jobs?

Affected parts: [[WF-workflow-engine]], [[WF-separation-of-concerns-temporal]], [[WF-entity-state-machines]], [[WF-background-jobs-and-queues]], [[WF-human-tasks]], [[WF-long-running-pipelines]], [[PKG-rules-and-decision-engine]], [[PKG-workflow-templates]].

Our processes differ in kind. A case can stay open for months and must survive restarts and deploys; a document status change must be validated on every write; a virus scan or a notification is a short job that just needs retries.

<!-- section:drivers -->
## Decision drivers

- **D1 Durability** of long processes with timers measured in days or weeks.
- **D2 Correctness of entity status** on every change, including changes outside a workflow (admin edits, API calls).
- **D3 Tenant-configurable procedures and decisions** without forking code ([[WF-separation-of-concerns-temporal]]).
- **D4 Per-region runtime** for residency ([[MT-data-residency-2]]) on AWS and Azure.
- **D5 Simplicity for short jobs**: no heavyweight engine for a thumbnail.
- **D6 Testability and versioning** so running cases are not disturbed by deploys.

<!-- section:decision -->
## Decision

**A combination of Temporal, code-defined state machines and queue-based jobs, chosen per scenario** (see Section 7, [[WF-workflow-engine]]).

| Scenario | Mechanism | Examples |
|---|---|---|
| Long-running, multi-step, waits on time or people | Temporal workflows ([[ADR-temporal]]) | Case lifecycle, hearing reminders, transcription and AI pipelines, dunning |
| Entity status rules enforced on every change | Code-defined state machines ([[WF-entity-state-machines]]) | Case status, document approval, invoice states |
| Short, independent, fire-and-forget | BullMQ jobs ([[ADR-queue-technology]]) | Notifications, virus scans, thumbnails, search indexing, webhook delivery |

Rules that keep them from overlapping: workflows hold flow only and call decisions and work as activities; state machines are the only code that changes an entity's `status` column, and workflows call them through activities; BullMQ jobs never wait on people or on timers longer than their retry window. This meets D1 and D6 (Temporal), D2 (state machines at the data layer), D5 (BullMQ), and D3 through the decision and interpreter layers described in [[WF-separation-of-concerns-temporal]].

<!-- section:consequences -->
## Consequences

**Easier:** each kind of work uses a tool that fits; status rules hold even for API and admin writes; tenants change rules and process definitions as data.

**Harder:**

- Three mechanisms to learn, monitor and operate in every region.
- Engineers must pick the right one; wrong picks (a BullMQ job that polls for a week, a workflow that writes `status` directly) need review-time detection.
- Tracing across the three needs common correlation IDs and tenant tags ([[OBS-foundations]]).
- Two runtimes (Temporal cluster and Redis) to back up, upgrade and fail over per region ([[INF-temporal]], [[INF-redis]]).

<!-- section:confirmation -->
## Confirmation

- Architecture review checklist item on every new process: which mechanism and why, using the table above.
- Lint rule: writes to `status` columns of state-machine entities only from `packages/state-machines` (checked by a restricted-import or code-owner rule on the repository functions).
- BullMQ job options are validated at registration: maximum delay and maximum total retry window (proposed 24 hours); longer needs a Temporal workflow.
- Temporal workflow code is checked by the Temporal SDK's determinism replay tests in CI.

<!-- section:options -->
## Options considered

| Option | Why not chosen |
|---|---|
| Temporal for everything | Overkill for millions of short jobs; status rules would still be bypassed by non-workflow writes |
| Camunda 8 (BPMN / DMN) | Process and decision layers built in, but adds a JVM platform and licensing considerations per region; team strength is TypeScript |
| AWS Step Functions | Not available on Azure; per-transition pricing for long cases; fails D4 |
| BullMQ plus database state only | No durable timers or history; long processes become hand-rolled schedulers |

<!-- section:revisit -->
## When to revisit

- Operating three mechanisms costs more than a proposed threshold of on-call time per quarter.
- The interpreter workflow plus rules engine proves too limited for tenant procedures and a BPMN engine becomes necessary (linked to the open rules-engine choice in [[WF-separation-of-concerns-temporal]]).
- Temporal licensing or project health changes ([[ADR-temporal]]).

<!-- section:notes -->
## More information

**Open questions**

- [ ] Rules engine choice for the decision layer (in-house JSON evaluator, GoRules Zen, or a FEEL / DMN interpreter), carried from [[WF-separation-of-concerns-temporal]]; it should become its own ADR.
- [ ] Which processes start as code workflows and which as interpreter workflows in Phase 3.
- [ ] Agree the maximum BullMQ delay and retry window (proposed 24 hours) above which Temporal is mandatory.

<!-- checks -->
## Template checks

<!-- check:significance -->
### Significance

Significant: it fixes how every process in the platform is built and operated, and it is hard to reverse once case workflows are running. It decides the choice of mechanism per scenario; Temporal hosting is a separate record ([[ADR-temporal]]), as is the queue technology ([[ADR-queue-technology]]).

<!-- check:options -->
### Options and evidence

Compared Temporal-only, Camunda 8, AWS Step Functions and BullMQ-with-state against the same drivers (durability, status correctness, configurability, per-region on AWS and Azure, simplicity). The decisive drivers were D4 (Azure and per-region) against Step Functions and D2 (status writes outside workflows) against Temporal-only. Cost comparisons are assumptions until [[INF-temporal]] sizing is done.

<!-- check:consequences -->
### Consequences and costs

Downsides: three mechanisms to operate per region, need for consistent tracing, and the risk of wrong mechanism choice. Mitigations are the review checklist, the status-write lint rule and BullMQ option validation.

<!-- check:confirmation -->
### Confirmation

Determinism replay tests for workflows in CI, a lint rule limiting `status` writes to the state-machine package, and registration-time validation of BullMQ delays and retry windows. The review checklist entry is part of the PR template ([[FND-governance]]).

<!-- check:linked -->
### Linked and lifecycle

Governs [[WF-workflow-engine]], [[WF-separation-of-concerns-temporal]], [[WF-entity-state-machines]], [[WF-background-jobs-and-queues]]. Related: [[ADR-temporal]], [[ADR-queue-technology]]. Status: Approved.

<!-- end -->
