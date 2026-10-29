---
id: "WF-separation-of-concerns-temporal"
title: "Separation of Concerns (Temporal)"
parent: "WF"
order: 6
type: "design"
template: "design"
status: "draft"
owner: null
indicative: false
summary: "How process, decisions, work and runtime are split across Temporal building blocks."
links: [{"rel": "related", "to": "PKG-rules-and-decision-engine"}, {"rel": "related", "to": "PKG-configuration-and-customisation"}, {"rel": "related", "to": "WF-workflow-engine"}]
rev: 3
syncHash: "b162d40361a2a9c8"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 7.5 Separation of Concerns (Temporal)

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> How process, decisions, work and runtime are split across Temporal building blocks.

<!-- section:context -->
## Context and scope

Workflow logic, business decisions, the work itself and the runtime that executes it change at different speeds and are owned by different people. Keeping them in separate layers means:

- Legal or operations teams can change a deadline or a routing rule without a code release
- Tenants can have different procedures without forking the codebase
- Running cases are never disturbed by a change; new cases pick up the new version
- Each layer can be tested, versioned and scaled on its own

In Camunda this split comes built in (BPMN for process, DMN for decisions, Zeebe as the engine). Temporal provides only the engine, so the platform builds the process and decision layers itself, using the building blocks below.

Since the overhaul of administration and workflow authoring, layer 1 for tenant-configurable flows is the **case-type blueprint** ([[WF-process-definition-model]]), edited in the studio ([[WF-workflow-authoring-studio]]) and versioned as described in [[WF-workflow-versioning]]. Layer 2 remains the Rules and Decision Engine. Simple event reactions sit outside Temporal in automation rules on BullMQ ([[WF-automation-rules]]).

<!-- section:goals -->
## Goals and non-goals

**Goals**

- Legal and operations staff can change deadlines, reminder policies, fee scales and routing per tenant without a code release, and the change applies only to cases started (or stages entered) after publication.
- A tenant can run a different sequence of known steps (interpreter workflow) without forking code.
- Each layer can be tested on its own: decision tables from their rows, activities against real dependencies, workflows with time-skipping and replay tests.
- Every workflow carries tenant context, encrypted payloads and searchable attributes from its first version.

**Non-goals**

- A tenant-facing BPMN designer with arbitrary scripting. The interpreter only allows the reviewed step types.
- Running decision logic inside workflow code, even for simple rules.
- Per-tenant Temporal namespaces; tenant isolation is by context, IDs and RLS (see Cross-cutting concerns).

<!-- section:design -->
## Design

#### Layer model

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. PROCESS DEFINITION  (≈ BPMN)   What happens, in what order    │
│    Core flows: TypeScript workflows                              │
│    Tenant-configurable flows: JSON definitions + interpreter     │
├──────────────────────────────────────────────────────────────────┤
│ 2. DECISIONS           (≈ DMN)    Given facts, what's the answer │
│    Rules and Decision Engine package, called as an Activity      │
├──────────────────────────────────────────────────────────────────┤
│ 3. WORK EXECUTION      (≈ tasks)  Do the actual work             │
│    Activities, routed via Task Queues, hosted by Workers         │
├──────────────────────────────────────────────────────────────────┤
│ 4. RUNTIME / ENGINE    (≈ Zeebe)  Durable execution              │
│    Self-hosted Temporal cluster per region                       │
├──────────────────────────────────────────────────────────────────┤
│ 5. INTEGRATION & CONTROL          How the app talks to it        │
│    Client, Schedules, Search Attributes, Interceptors, Codec     │
└──────────────────────────────────────────────────────────────────┘
```

#### Temporal roles by layer

| Layer | Concern | Temporal role(s) | Our implementation |
|---|---|---|---|
| **1. Process definition** (≈ BPMN) | What happens, in what order | **Workflow Definition** | Core flows as TypeScript workflows (case lifecycle skeleton, payments, pipelines) |
| | | **Interpreter Workflow** (DSL pattern) | `caseProcess`: one generic workflow per case (`{tenantId}-process-{caseId}`) that runs the pinned case-type blueprint ([[WF-process-definition-model]]); pure interpreter core shared with the simulator |
| | Sub-processes | **Child Workflow** | Reusable sub-flows (e.g. hearing scheduling inside a case) |
| | Waiting on time | **Timer** (`sleep`, `condition` timeout) | Deadlines, reminders, SLA windows |
| | Waiting on people / external events | **Signal**, **Update** | Party / neutral actions (confirm, submit, approve); Update when the caller needs a validated response |
| | Process state visibility | **Query** | Current step, pending actions, deadlines for UI |
| | Very long-lived cases | **Continue-As-New** | Roll over history on multi-month / multi-year cases |
| | Process versioning | **Worker Versioning** (Auto-Upgrade for `caseProcess`, Pinned for short workflows) / `patched()` [R4] | Blueprint content pinned by data; code changes replay-safe; migration by validated Update ([[WF-workflow-versioning]]) |
| **2. Decisions** (≈ DMN) | Given these facts, what is the answer | **Activity** (`evaluateDecision`) | Calls the Rules and Decision Engine package; decision tables versioned per tenant |
| | Rule version pinning | **Workflow input** + **Memo** | Rule / definition version fixed at workflow start and recorded on the workflow |
| **3. Work execution** (≈ service tasks) | Do the actual work (I/O, side effects) | **Activity** | Notifications, document processing, AI calls, payments, DB writes |
| | Reliability of work | **Retry Policy**, **Timeouts**, **Heartbeats** | Per-activity retries; heartbeats for long AI / transcription jobs |
| | Routing work | **Task Queue** | Per domain / workload: `cases`, `hearings`, `documents`, `ai-pipelines`, `billing` |
| | Hosting work | **Worker** | Containers per task queue, scaled independently per region |
| **4. Runtime / engine** (≈ Zeebe) | Durable execution, timers, history | **Temporal Server** (Frontend, History, Matching, internal Worker services) | Self-hosted cluster per region |
| | State storage | **Persistence store**, **Visibility store** | Postgres per region (visibility via Postgres or OpenSearch) |
| | Isolation boundary | **Namespace** | Per environment and region (e.g. `prod-in`, `prod-sg`); tenant carried in context, not per-tenant namespaces |
| **5. Integration and control** | Start / signal / query from the app | **Temporal Client** | Used by Next.js API layer and domain services |
| | Recurring jobs | **Schedule** | Periodic reports, regulator / aggregator submissions, reminder sweeps |
| | Finding workflows | **Search Attributes** | `tenantId`, `caseId`, `caseType`, `status`, `stage`, `blueprintVersion`, `nextDeadline`, `assigneeRole` for admin search and reports |
| | Cross-cutting context | **Interceptors**, **Context Propagation** | Tenant ID, user ID, trace IDs passed into every workflow and activity |
| | Data confidentiality | **Data Converter** / **Payload Codec** + **Codec Server** | Encrypt workflow payloads at rest; decrypt only for authorised operators in the UI |
| | Operations | **Temporal Web UI**, **CLI** | Inspect, retry, terminate; access restricted by role |

<!-- section:examples -->
## Worked examples

#### Hearing reminder across the layers

Scenario: some days before a hearing, remind the neutral to confirm. If there is no confirmation within a window, escalate to the tribunal secretary. The number of days and the window differ by tenant and case type.

**Layer 2 — Decision table** (data, owned by the Rules and Decision Engine, editable per tenant)

```json
{
  "decision": "hearing-reminder-policy",
  "version": 4,
  "hitPolicy": "FIRST",
  "rules": [
    { "when": { "tenant": "HKIAC", "caseType": "Arbitration" }, "then": { "reminderDays": 7, "confirmWithinHours": 48 } },
    { "when": { "tenant": "SEBI-ODR", "claimValue": { "lt": 1000000 } }, "then": { "reminderDays": 3, "confirmWithinHours": 24 } },
    { "when": {}, "then": { "reminderDays": 5, "confirmWithinHours": 48 } }
  ]
}
```

**Layer 3 — Activities** (the actual work; retried automatically)

```ts
// activities.ts
export async function evaluateDecision(req: { decision: string; version: number; facts: object }) {
  return rulesEngine.evaluate(req.decision, req.version, req.facts); // Rules and Decision Engine package
}
export async function sendReminder(hearingId: string) { /* Notifications package */ }
export async function escalateToSecretary(hearingId: string) { /* Notifications + human task */ }
```

**Layer 1 — Workflow** (flow only: no I/O, no rule logic)

```ts
// workflows/hearing-reminder.ts
import { proxyActivities, defineSignal, setHandler, sleep, condition } from '@temporalio/workflow';
import type * as acts from '../activities';

const { evaluateDecision, sendReminder, escalateToSecretary } = proxyActivities<typeof acts>({
  startToCloseTimeout: '1 minute',
  retry: { maximumAttempts: 5 },
});

export const neutralConfirmed = defineSignal('neutralConfirmed');

export async function hearingReminder(input: {
  hearingId: string; hearingAt: string; facts: object; policyVersion: number;
}) {
  let confirmed = false;
  setHandler(neutralConfirmed, () => { confirmed = true; });

  const policy = await evaluateDecision({
    decision: 'hearing-reminder-policy', version: input.policyVersion, facts: input.facts,
  });

  const remindAt = new Date(input.hearingAt).getTime() - policy.reminderDays * 86_400_000;
  await sleep(Math.max(0, remindAt - Date.now()));
  await sendReminder(input.hearingId);

  const ok = await condition(() => confirmed, `${policy.confirmWithinHours} hours`);
  if (!ok) await escalateToSecretary(input.hearingId);
  return ok ? 'CONFIRMED' : 'ESCALATED';
}
```

**Layer 4 — Runtime**: the self-hosted Temporal cluster in the tenant's region holds the timers, history and retries. If a worker restarts mid-wait, the workflow resumes exactly where it was.

**Layer 5 — Integration** (from the Next.js API layer)

```ts
await temporal.workflow.start(hearingReminder, {
  taskQueue: 'hearings',
  workflowId: `${tenantId}-hearing-reminder-${hearingId}`,
  searchAttributes: { tenantId: [tenantId], caseId: [caseId] },
  args: [{ hearingId, hearingAt, facts: { tenant, caseType, claimValue }, policyVersion: 4 }],
});

// Neutral clicks "Confirm"
await temporal.workflow.getHandle(`${tenantId}-hearing-reminder-${hearingId}`).signal(neutralConfirmed);
```

Changing HKIAC's reminder from 7 to 10 days means publishing version 5 of the decision table. Hearings already scheduled keep version 4; new ones use version 5. No code change, no deploy.

#### Tenant-configurable processes (interpreter workflow)

When the order of steps itself differs by tenant, the process is stored as data and run by one generic workflow.

```json
{
  "process": "hearing-reminder",
  "version": 3,
  "steps": [
    { "id": "decide",   "type": "decision", "decision": "hearing-reminder-policy", "output": "policy" },
    { "id": "wait",     "type": "waitUntil", "at": "hearingAt - policy.reminderDays days" },
    { "id": "remind",   "type": "activity",  "name": "sendReminder" },
    { "id": "confirm",  "type": "waitForSignal", "signal": "neutralConfirmed",
      "timeout": "policy.confirmWithinHours hours", "onTimeout": "escalate", "onSignal": "end" },
    { "id": "escalate", "type": "activity",  "name": "escalateToSecretary" }
  ]
}
```

| Use code workflows when | Use the interpreter when |
|---|---|
| The flow is core to the platform and rarely changes | The flow differs by tenant, institution or rule set |
| Logic is complex (loops, compensation, parallel branches) | Steps are a sequence of known building blocks |
| Only engineers change it | Admins configure it through the admin UI |

Rules for the interpreter:

- Only a fixed, reviewed set of element types is allowed; the full catalogue (stage, human task, form request, decision, timer, document, notification, AI step, service, transition, gateway, subprocess, wait for event, interrupts) is in [[WF-process-definition-model#entities]]
- Definitions are validated against a schema and must pass required simulation scenarios before publishing ([[WF-workflow-simulation]])
- The definition is loaded once at start (via an Activity) and passed in, so running cases keep their version; only an approved migration changes it ([[WF-workflow-versioning]])
- The visual studio ([[WF-workflow-authoring-studio]]) saves the same JSON; the outline view is its accessible equivalent

<!-- section:alternatives -->
## Alternatives considered

| Option | Trade-off | Outcome |
|---|---|---|
| Camunda 8 (BPMN, DMN, Zeebe) | Process and decision layers out of the box and a visual modeller; adds a second engine stack and a different operating model per region | Not chosen; see [[WF-workflow-engine]] |
| Code-only Temporal workflows with rules inline | Simplest to start; every rule change needs a deploy and versioning patch | Rejected: legal / operations need to change rules without deploys |
| Interpreter for all processes | Maximum configurability; complex flows (compensation, parallel branches) become hard to express and test | Rejected: core flows stay in TypeScript |
| Per-tenant namespaces | Strong operational isolation and per-tenant retention; namespace count grows with tenants and complicates workers and visibility | Rejected for now; revisit if a client contract demands it |

<!-- section:crosscutting -->
## Cross-cutting concerns

- **Tenancy**: tenant ID enters through the client wrapper, is placed in the workflow ID (`{tenantId}-{process}-{entityId}`), the `tenantId` search attribute and Temporal headers, and is restored by the activity interceptor, which opens every Prisma transaction with `set_config('app.tenant_id', ..., true)` ([[MT-prisma-client-extension-wraps]]). An activity without tenant context fails before doing any work.
- **Fairness**: shared task queues per domain; bulk imports (for example aggregator intake through [[INT-aggregator-intake-api]]) start workflows through a rate-limited starter so one tenant cannot flood a queue. Worker concurrency limits per task queue are set in [[INF-temporal]].
- **Security and privacy**: payloads hold IDs and minimal facts; document content never enters history. The payload codec encrypts with a regional KMS key; the codec server is reachable only from the operator network and checks the operator's role before decrypting.
- **Residency**: one cluster per region; persistence and visibility stores in-region; codec keys in the regional KMS.
- **Audit**: Temporal history is operational, not evidence. Legally significant steps write audit events through [[PKG-audit-trail]] inside the activity's transaction.
- **Observability**: SDK metrics plus business metrics per workflow type, traces through interceptors (OpenTelemetry), and search attributes `tenantId`, `caseId`, `caseType`, `status` (to be extended with `stage` and `nextDeadline`).

<!-- section:guardrails -->
## Guardrails

- Workflows contain **flow only**: no I/O, no DB reads, no rule logic. Anything non-deterministic goes in an Activity
- Decision tables and process definitions are **data**, owned by the Rules and Configuration packages, not by Temporal
- Definitions and rule versions are **loaded once at start** and passed in, so a change affects new cases only
- Every workflow and activity receives **tenant context** via interceptors; workflow IDs are prefixed with tenant (`{tenantId}-{process}-{entityId}`)
- Workflow payloads are **encrypted** through the Payload Codec; the Codec Server decrypts only for authorised operators
- Temporal handles **durable orchestration**; BullMQ handles **short fire-and-forget jobs**; state machines guard **entity status**, with no overlap
- Blueprints reference only registered activities, signals, events and AI steps; adding one is a code change with review
- The interpreter's pure core is the only place step semantics live; the Temporal shell and the simulator both call it
- Running cases change blueprint version only through the `migrateBlueprint` Update at a quiescent point

<!-- section:ownership -->
## Ownership

| Layer | Owned by | Changed through |
|---|---|---|
| Process definition (code: interpreter, core flows) | Platform engineering | Pull request, deploy, Worker Versioning and `patched()` |
| Process definition (case-type blueprints) | Tenant `workflow_designer`, approved by a second person; library blueprints by the Nomology implementation team with legal | Studio or `/admin/v1/workflows`, validation, simulation gate, publish new version |
| Decisions | Legal / operations, per tenant; offering-locked tables by Nomology with legal | Decision table editor, tests, review, publish new version |
| Automation rules (outside Temporal) | Tenant admins | Studio automation screens, approval per setting |
| Activities and Workers | Domain engineering teams | Pull request, deploy |
| Runtime | Platform / DevOps | Infrastructure as code |

<!-- section:questions -->
## Open questions

- [ ] Rules engine choice: in-house JSON evaluator vs GoRules Zen vs a FEEL / DMN interpreter
- [x] Visual editor: decided. The studio ships in Phase 4 with canvas and outline views ([[WF-workflow-authoring-studio]]).
- [ ] Visibility store: Postgres vs OpenSearch per region
- [ ] Which processes start as code workflows vs interpreter workflows. Proposed: case lifecycle runs as blueprints from Phase 3 using library blueprints; notice service, eBundling and pipelines stay code workflows called as registered subprocesses
- [x] Add `stage`, `blueprintVersion`, `nextDeadline` and `assigneeRole` as registered search attributes in every namespace: yes (see design table).
- [ ] Note: the summary of [[PKG-rules-and-decision-engine]] points to "7.6" for this design; the layer model lives here in 7.5. Correct the cross-reference.
- [ ] [[ADR-workflow-engine]] (approved, not edited) lists as a revisit trigger that the interpreter may prove too limited. Record the interpreter versioning strategy (Auto-Upgrade plus patching, pure core) as its own ADR. Owner: CTO.

<!-- checks -->
## Template checks

<!-- check:security -->
### Security and privacy

Payloads are encrypted through the payload codec with a regional KMS key [R1]; the codec server decrypts only for operators with the support role in that region, and every decrypt is logged. Workers authenticate to the cluster with mTLS. Updates have validators that reject out-of-state input before it is written to history [R2]. Workflow inputs hold IDs and minimal facts, not document content.

<!-- check:tenancy -->
### Tenancy

Tenant identity is carried in the workflow ID prefix, a `tenantId` search attribute, and Temporal headers set by a client interceptor and read by worker interceptors. Activities receive it explicitly and open each Prisma transaction with `set_config('app.tenant_id', $1, true)`, safe under PgBouncer transaction pooling. Missing context fails closed. Cross-tenant operations (platform Schedules for aggregator reports) run as one workflow per tenant, never one workflow iterating tenants with a privileged role. Isolation tests: a signal to tenant A's workflow sent with tenant B's session is rejected by the API wrapper.

<!-- check:residency -->
### Data residency and lifecycle

One cluster, namespace, persistence and visibility store per region; codec keys are regional. Closed workflow history is retained for a short operational window (proposed 30 days, open question in [[WF]]); anything needed later is written to the audit trail and domain tables in-region.

<!-- check:failure -->
### Failure handling and recovery

Activities have explicit timeouts and retry policies; long ones heartbeat. Decisions are evaluated through an activity, so a rules-engine outage retries rather than failing the case. Running cases pin decision and definition versions at start, so a bad publication only affects new cases and can be rolled back by publishing the previous version.

<!-- check:rollout -->
### Rollout and migration

New decision-table versions are published per tenant and apply to new cases or new stages only. New workflow code uses `patched()` for small changes or a new workflow type for larger ones, with replay tests against recorded histories in CI [R3]. Blueprint versions follow the lifecycle and simulation gate in [[WF-workflow-versioning]]; case-process workflows use Auto-Upgrade with patching [R4], short-lived workflows Pinned.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Payload codecs can encrypt workflow payloads; a codec server decrypts them for authorised users of the Web UI and CLI.",
    "id": "R1",
    "kind": "vendor",
    "title": "Temporal docs: Payload encryption (TypeScript SDK)",
    "url": "https://docs.temporal.io/develop/typescript/best-practices/data-handling/data-encryption",
    "vendor": "Temporal Technologies"
  },
  {
    "excerpt": "Update handlers can register a validator that rejects an update before it is written to workflow history.",
    "id": "R2",
    "kind": "vendor",
    "title": "Temporal docs: Workflow message passing (TypeScript)",
    "url": "https://docs.temporal.io/develop/typescript/message-passing",
    "vendor": "Temporal Technologies"
  },
  {
    "excerpt": "Patching (patched / deprecatePatch) lets new workflow code run alongside histories created by earlier code.",
    "id": "R3",
    "kind": "vendor",
    "title": "Temporal docs: Versioning (TypeScript)",
    "url": "https://docs.temporal.io/develop/typescript/versioning",
    "vendor": "Temporal Technologies"
  },
  {
    "excerpt": "Pinned workflows complete on one Worker Deployment Version; Auto-Upgrade workflows move to the current version and must be kept replay-safe.",
    "id": "R4",
    "kind": "vendor",
    "title": "Temporal docs: Worker Versioning",
    "url": "https://docs.temporal.io/worker-versioning",
    "vendor": "Temporal Technologies"
  }
]
```

<!-- end -->
