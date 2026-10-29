---
id: "WF-workflow-engine"
title: "Workflow engine"
parent: "WF"
order: 1
type: "capability"
template: "design"
status: "draft"
owner: null
indicative: false
summary: "Which mechanism runs what (Temporal, state machines, BullMQ), how tenant blueprints and automation rules map onto them, and the hand-offs between them"
links: [{"rel": "decided-by", "to": "ADR-workflow-engine"}]
rev: 4
syncHash: "7b29dba231c4c60f"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 7.1 Workflow engine

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Which mechanism runs what (Temporal, state machines, BullMQ), how tenant blueprints and automation rules map onto them, and the hand-offs between them

<!-- section:context -->
## Context and scope

[[ADR-workflow-engine]] decided that the platform uses a combination of three mechanisms rather than one engine. This note turns that decision into a rule an engineer can apply when building a new process, and states how the three mechanisms hand work to each other. The layer model inside Temporal is in [[WF-separation-of-concerns-temporal]]; this note sits one level above it.

What exists: Temporal self-hosted per region ([[ADR-temporal]], [[INF-temporal]]), BullMQ on regional Redis ([[ADR-queue-technology]], [[INF-redis]]), Postgres with forced RLS as the system of record ([[ADR-tenant-isolation]]).

<!-- section:goals -->
## Goals and non-goals

**Goals**

- Give a deterministic rule for choosing Temporal, a state machine or a BullMQ job, so two engineers make the same choice for the same scenario.
- Define the hand-offs (state machine to workflow, workflow to job, job back to workflow) so they are idempotent and tenant-safe.
- Keep the database the single source of truth for entity status; Temporal holds process position, not business state.

**Non-goals**

- Choosing a rules engine (open in [[WF-separation-of-concerns-temporal]]).
- Cluster sizing and operations ([[INF-temporal]]).

<!-- section:design -->
## Design

| Approach | Best suited for | Examples |
|---|---|---|
| Temporal | Long-running, multi-step, durable processes that must survive failures and wait days or weeks | Case lifecycle, hearing scheduling with reminders, transcription and AI pipelines, payment and dunning flows |
| Code-defined state machines | Entity status rules that must be enforced on every change | Case status, document approval states, invoice states |
| Queue-based jobs | Short, independent, fire-and-forget tasks | Sending notifications, virus scans, thumbnails, search indexing, webhooks |
| Tenant-authored blueprint, run by the generic interpreter (Temporal) | A tenant's procedure for a case type: stages, tasks, filings, deadlines | SEBI ODR conciliation, institutional arbitration, CORD mediation ([[WF-process-definition-model]]) |
| Tenant-authored automation rule (BullMQ) | "When X, if Y, do Z" with no procedural effect | Tag a case when a power of attorney arrives; notify the case manager; create a follow-up task ([[WF-automation-rules]]) |

#### Choosing a mechanism

Apply the questions in order; the first "yes" decides.

1. Is this a rule about which status an entity may move to, and who may move it? → **State machine** ([[WF-entity-state-machines]]). Always, even if a workflow also exists.
2. Does the process wait for a person, a timer longer than a few minutes, or an external callback, or have more than one step whose partial completion must be remembered? → **Temporal workflow**.
3. Is it a single side effect that completes in under about 5 minutes, can be retried on its own, and whose result no process waits on (or the waiting process gets a signal back)? → **BullMQ job** ([[WF-background-jobs-and-queues]]).
4. Otherwise (for example a synchronous computation inside a request) → plain code in the domain service.

For anything a **tenant** wants to configure, apply this second test after the first:

- Does it change what a party or neutral must do, by when, or what happens procedurally? → a step in the case-type **blueprint**, executed by the Temporal interpreter, versioned and pinned ([[WF-process-definition-model]], [[WF-workflow-versioning]]).
- Is it a reaction to an event that only informs, labels, assigns or creates follow-up work? → an **automation rule** on BullMQ ([[WF-automation-rules]]), not pinned, with loop protection.
- Is it a value (a period, fee, threshold, routing choice)? → a **decision table** row ([[PKG-rules-and-decision-engine]]) or a **setting** ([[PKG-settings-cases-and-workflows]]).

| Scenario | Mechanism | Why |
|---|---|---|
| Case moves from `registered` to `awaiting_constitution` | State machine (+ case workflow observes) | Status guard must hold on every writer |
| Respondent's 30-day response window after service (value from rule set) | Temporal timer in the case workflow | Multi-week wait, must survive deploys |
| Send the notice email | BullMQ `notifications` job enqueued by an activity | Single side effect with provider retries |
| Track delivery receipts for that email until served or fallback | Temporal (`notice-service` workflow) | Waits on callbacks with deadlines |
| Malware scan of an upload | BullMQ `files.scan` | Short, independent |
| Bundle of 4,000 pages: merge, paginate, OCR, index | Temporal pipeline with heartbeating activities | Long, multi-step, resumable |
| Nightly SEBI status report to NSE | Temporal Schedule | Recurring, multi-step, auditable |
| Search re-index of one document | BullMQ `search.index` | Short, idempotent |
| Tenant adds a "scrutiny" stage with a 2-business-day target | Blueprint stage + SLA policy, run by `caseProcess` interpreter | Procedural position and timer, pinned per case |
| Tenant wants the case manager emailed when a respondent counsel is added | Automation rule on `automation.evaluate` / `automation.execute` | Informational reaction, no procedural effect |
| Move 400 running cases to the new rules version | Temporal `blueprintMigration` workflow sending Updates | Long, batched, auditable ([[WF-workflow-versioning]]) |

#### Hand-offs

- **State machine → workflow.** A transition writes the status change and an outbox event in one transaction. The outbox relay starts or signals the workflow using `workflowId = {tenantId}-{process}-{entityId}` with conflict policy "use existing", so a duplicate relay is harmless.
- **Workflow → state machine.** An activity calls the domain command (for example `registerCase`) with an idempotency key `{workflowId}:{activityId}`; the state machine validates the transition. If the guard fails, the activity throws a non-retryable `TransitionRejected` error and the workflow takes its failure branch.
- **Workflow → BullMQ.** An activity enqueues with BullMQ `jobId = {workflowId}:{activityId}` so a retried activity does not enqueue twice. If the workflow needs the result, the job's completion handler sends a signal back to the workflow.
- **BullMQ → workflow.** Only through the Temporal client (signal or signal-with-start), never by writing workflow state.
- **Automation rule → workflow.** Only through the `signal_case_process` action, and only for signals the blueprint declares automation-safe; the signal is authorised as the rule's automation principal.
- **Outbox → automation.** The outbox relay enqueues `automation.evaluate` for every registered event type, with the automation chain carried in the envelope for loop protection.

#### Ownership of state

| State | Source of truth |
|---|---|
| Entity status and history | Postgres (`*_status_events`) |
| Where a process is waiting, its timers | Temporal |
| Human task open / done | Postgres (`human_tasks`), mirrored to the workflow by update |
| Job attempts | BullMQ (transient); outcome recorded in Postgres if it matters |
| Which blueprint version a case runs and its current stage | Postgres (`wf.case_process`, `wf.case_stage_event`) |
| Automation executions | Postgres (`wf.automation_execution`) |

<!-- section:alternatives -->
## Alternatives considered

| Option | Why not chosen |
|---|---|
| Temporal for everything, including notifications and scans | Adds history and worker cost for millions of short jobs; BullMQ is cheaper and simpler for fire-and-forget work. |
| BullMQ for everything, with delayed jobs as timers | No durable multi-step state, no signals or queries, weak versioning for year-long cases; we would rebuild a workflow engine. |
| Status held only in Temporal workflow state | Status must be enforced on every writer (public API, admin console, migrations) and queried by SQL for reports; Temporal state is not queryable that way. |
| Camunda / Zeebe (BPMN + DMN) | Built-in process and decision layers, but adds a JVM stack, licensing for some features, and a second durable engine per region; the team's TypeScript stack fits Temporal. Recorded as background in [[ADR-workflow-engine]]. |

<!-- section:crosscutting -->
## Cross-cutting concerns

- **Tenancy**: every mechanism carries tenantId explicitly: workflow ID prefix and search attribute, BullMQ job data field validated by the worker wrapper, state-machine context. All database work runs through the Prisma tenant extension ([[MT-prisma-client-extension-wraps]]).
- **Residency**: all three mechanisms are per region; nothing crosses regions.
- **Security**: only the API layer and workers hold Temporal client credentials (mTLS per region); BullMQ job payloads carry IDs, not document content or personal data beyond what is needed.
- **Observability**: traces propagate from the request through outbox, workflow, activity and job (W3C trace context in job data and Temporal headers).
- **Cost**: Temporal actions are the main cost driver of self-hosting (history writes); short jobs stay on BullMQ.

<!-- section:guardrails -->
## Guardrails

- Do not start a Temporal workflow for a single side effect; enqueue a job.
- Do not use BullMQ delayed jobs for legal deadlines; legal timers live in Temporal so they are visible, versioned and auditable.
- Do not write a status column outside [[WF-entity-state-machines]].
- Every hand-off carries an idempotency key built from the workflow ID and activity, or a business key.
- A job never blocks a workflow without a timeout: if a workflow waits for a job's signal, it waits with a timer and a failure branch.
- Tenant configuration never becomes code: no tenant-supplied scripts, expressions outside the closed grammar, or HTTP calls outside registered integrations.
- Automation rules never change status, procedural deadlines, parties or confidentiality; anything procedural is a blueprint step.
- Never pin a long-lived case process to a single worker build; use Auto-Upgrade with `patched()` ([[WF-workflow-versioning]]).

<!-- section:questions -->
## Open questions

- [ ] Is a Temporal Schedule or a BullMQ repeatable job the default for low-stakes periodic sweeps (search re-index, thumbnail backfill)? Proposed: BullMQ for sweeps with no legal effect, Temporal Schedules for anything reported to a regulator or aggregator.
- [ ] Outbox relay: run as a BullMQ repeatable job per region or as a dedicated relay process? Owner: platform engineering.
- [ ] Do we allow signal-with-start from the outbox relay for every process, or only for case-level workflows?
- [ ] Should automation rules be allowed to start a library subprocess (for example "collect deposit") on a case, or only signal steps the blueprint declares? Proposed: signals only. Owner: product.

<!-- checks -->
## Template checks

<!-- check:security -->
### Security and privacy

Only the API layer and workers hold Temporal client credentials (mTLS per region) and Redis credentials; browsers never talk to Temporal or Redis. Hand-off payloads carry IDs only. Signals and updates from users pass the permission check in the API before reaching Temporal, and update validators re-check state.

<!-- check:tenancy -->
### Tenancy

The tenant is carried explicitly at every hand-off: in the workflow ID prefix and `tenantId` search attribute, in BullMQ job data (rejected by the worker wrapper when missing), and in the state-machine context. Every database write runs inside a Prisma transaction that sets `app.tenant_id`. The Temporal client wrapper refuses to start or signal a workflow whose ID prefix differs from the caller's active tenant. Automation rules and blueprints add no new path: rule lookup and interpreter activities run inside the case's tenant transaction.

<!-- check:residency -->
### Data residency and lifecycle

All three mechanisms are per region: Temporal cluster and namespace, Redis and BullMQ workers, and Postgres. The outbox relay runs per region and only starts workflows in its own region.

<!-- check:failure -->
### Failure handling and recovery

Each hand-off is idempotent: outbox relay starts use the business workflow ID with "use existing" conflict policy; activities pass `{workflowId}:{activityId}` as the idempotency key to domain commands and as the BullMQ `jobId`. Non-retryable errors (`TransitionRejected`, validation, permission) fail fast. A workflow waiting on a job's completion signal always has a timer and an escalation branch, so a lost job surfaces as a human task rather than a silent stall. In-flight workflows across deploys are protected by versioning ([[WF-separation-of-concerns-temporal]]).

<!-- check:scale -->
### Capacity, performance and cost

The split keeps Temporal history volume proportional to long-running processes (cases, notices, pipelines), while high-volume short work (notifications, scans, indexing) goes to BullMQ. The first bottleneck expected is Postgres connections from workers behind PgBouncer; worker pools have fixed small Prisma pools per [[INF-small-fixed-prisma-pool-per]].

<!-- check:observability -->
### Observability

Traces cross every hand-off (W3C trace context in BullMQ envelopes and Temporal headers). Each mechanism has its own health metrics (Temporal schedule-to-start, BullMQ wait time, state-machine rejection rates), and hand-off failures (outbox backlog age) have an alert.

<!-- check:reversibility -->
### Reversibility

Hard-to-change parts: the workflow ID convention (used for idempotency and lookup), the outbox event envelope, and the rule that status lives in Postgres. These are fixed in this note and in [[WF-separation-of-concerns-temporal]]. The mechanism for any one process can be changed later (for example moving a sweep from BullMQ to a Temporal Schedule) without data migration because both are fed by the same domain commands.

<!-- end -->
