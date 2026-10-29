---
id: "PKG-workflow-templates"
title: "Workflow templates"
parent: "PKG-configuration-and-customisation"
order: 3
type: "feature"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "@nomology/workflow-templates: blueprint and process-definition schemas, validator, diff, projection, simulator and the generic caseProcess interpreter (pure core plus Temporal shell); see [[WF-separation-of-concerns-temporal]] and [[WF-process-definition-model]]"
links: []
rev: 4
syncHash: "4e484fb56d95c758"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.8.3 Workflow templates

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> @nomology/workflow-templates: blueprint and process-definition schemas, validator, diff, projection, simulator and the generic caseProcess interpreter (pure core plus Temporal shell); see [[WF-separation-of-concerns-temporal]] and [[WF-process-definition-model]]

<!-- section:purpose -->
## Purpose and scope

`@nomology/workflow-templates` is the code package behind tenant-configurable processes. It owns:

- the **blueprint and process-definition JSON Schemas** and their TypeScript types (the element catalogue is described in [[WF-process-definition-model#entities]]);
- the **validator** used by the studio, the admin API and the publish gate;
- the **interpreter**: a pure core (`reduce(state, event) → { state, commands }`) and the generic Temporal workflow `caseProcess` that wraps it, written and versioned by Nomology engineers ([[WF-separation-of-concerns-temporal]], [[WF-workflow-versioning]]);
- the **simulator** that runs the same pure core with a virtual clock ([[WF-workflow-simulation]]);
- the **registries** of activities, signals and subprocess fragments that blueprints may reference;
- **projection** of published bodies into the `wf` tables.

Core, complex flows (notice service, eBundling, pipelines) stay as TypeScript workflows and are exposed to blueprints as registered subprocesses.

**Does not:** store artefacts or run their lifecycle (`@nomology/config-core`, [[PKG-configuration-lifecycle]]); make decisions ([[PKG-rules-and-decision-engine]]); enforce entity status ([[WF-entity-state-machines]] remains the guard on every status change, so a blueprint cannot move a case into an invalid state); run automation rules ([[WF-automation-rules]]); own AI step behaviour ([[WF-ai-steps-and-agents]]).

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Use |
|---|---|
| Authoring studio ([[WF-workflow-authoring-studio]]) | Types for editors, `validate`, `diff`, `simulate` |
| Tenant admin API (`/admin/v1/workflows`, [[INT-tenant-admin-api]]) | Same operations for automation and configuration packages |
| Case creation ([[DOM-cases]]) | `pinForCase` (config-core) then start `caseProcess` with the pinned version |
| Temporal workers | Run `caseProcess`; load the body once by activity |
| Migration service ([[WF-workflow-versioning]]) | `diff`, mapping validation, `migrateBlueprint` Update |
| Secretariat console | `currentPosition` Query for current stage, pending actions and deadlines |
| Reports ([[RPT-cases]]) | Stage durations from projections and `wf.case_stage_event` |
| Admin copilot ([[APP-admin-copilot]]) | Generates draft bodies that must pass `validate` before they are shown as a draft |

<!-- section:api -->
## Public API

```ts
// packages/workflow-templates/src/index.ts
// schemaVersion 2 element types (see WF-process-definition-model#entities); schemaVersion 1 names in comments
export type StepType = 'decision' | 'service' /* v1 'activity' */ | 'timer' /* v1 'waitUntil' */
  | 'wait_for_event' /* v1 'waitForSignal' */ | 'human_task' /* v1 'humanTask' */ | 'form_request' /* v1 'form' */
  | 'subprocess' /* v1 'childProcess' */ | 'transition' | 'gateway' /* v1 'parallel' */
  | 'document' | 'notification' | 'ai_step' | 'end';

export interface CaseTypeBlueprint {
  meta: { key: string; offering: 'cord' | 'teres'; family: ProcedureFamily; ruleSetKey: string; locales: string[]; regions: Region[] };
  facts: Record<string, FactDef>;           // typed variables with sources
  caseRoles: CaseRoleKey[];
  process: { key: string; version: number }; // the ProcessDefinition below
  settingsOverrides?: Record<SettingKey, unknown>;   // only keys allowing scope case_type
  layout?: unknown;                          // studio positions, ignored by the interpreter
}

export interface ProcessDefinition {
  process: string; version: number; schemaVersion: 2;
  stages: { key: string; name: LocalisedText; caseStatus: CaseStatus; slaPolicy?: string; milestone?: boolean;
            visibleToParties?: boolean; entry?: string[]; exit?: { when: Expr }[] }[];
  interrupts?: { on: 'suspend' | 'stay_deadlines' | 'withdraw' | 'terminate'; mode: 'pause' | 'cancel' | 'goto'; target?: string }[];
  caseTypes: string[];                         // case types this applies to
  inputs: Record<string, FactType>;            // facts provided at start
  steps: Step[];
}
export type Step =
  | { id: string; type: 'decision'; decision: string; output: string }                     // decision version pinned at start
  | { id: string; type: 'activity'; name: RegisteredActivity; args?: Record<string, Expr>; next?: string }
  | { id: string; type: 'waitUntil'; at: DeadlineExpr; next?: string }                       // computed via calendars Activity
  | { id: string; type: 'waitForSignal'; signal: RegisteredSignal; timeout?: DeadlineExpr; onSignal: string; onTimeout: string }
  | { id: string; type: 'humanTask'; task: TaskSpec; onComplete: Record<string, string> }    // WF-human-tasks
  | { id: string; type: 'form'; form: { key: string }; assignee: Role; onSubmit: string }
  | { id: string; type: 'transition'; entity: 'case'; command: StateMachineCommand; next?: string }
  | { id: string; type: 'childProcess'; process: string; next?: string }
  | { id: string; type: 'parallel'; branches: string[][]; join: 'all' | 'any'; next?: string }
  | { id: string; type: 'end' }
  // added in schemaVersion 2
  | { id: string; type: 'timer'; kind: 'procedural' | 'service_level' | 'reminder'; deadlineRule?: string; at: DeadlineExpr; onDue: string }
  | { id: string; type: 'gateway'; mode: 'exclusive' | 'parallel' | 'join'; branches?: { when?: Expr; next: string }[]; join?: 'all' | 'any' | { n: number } ; next?: string }
  | { id: string; type: 'document'; template: { key: string }; outputFact: string; next?: string }
  | { id: string; type: 'notification'; template: { key: string }; to: RecipientSpec; next?: string }
  | { id: string; type: 'ai_step'; aiStep: { key: string }; reviewTask?: TaskSpec; outputFact: string; next?: string };  // semantics owned by WF-ai-steps-and-agents
// every step also carries: stage: string (owning stage key) and optional label: LocalisedText

/** Expressions: a closed, side-effect-free grammar over facts and step outputs */
export type Expr = string;        // e.g. "policy.reminderDays", "facts.claimValueMinor > 1000000"
export type DeadlineExpr = { from: Expr; duration: { value: Expr; unit: DurationUnit }; calendars?: 'seat' | string[] };

export function validate(tx: TenantTx, bp: CaseTypeBlueprint, def: ProcessDefinition): Promise<ValidationIssue[]>;  // schema + semantics + references + machine catalogue
export function diff(a: ResolvedBlueprint, b: ResolvedBlueprint): BlueprintDiff;          // element-level, with changeClass
export function project(tx: TenantTx, versionId: string): Promise<void>;                   // fill wf.stage_definition etc.
export function upgrade(body: unknown, fromSchema: number): { body: unknown; notes: string[] };   // schemaVersion upgraders
export const INTERPRETER_CONTRACT = 'interp/2.3';
export function simulate(def: ProcessDefinition, scenario: SimulationScenario): SimulationTrace;  // pure dry run with mocked activities and signals
export function registerActivity(name: string, def: { argsSchema: ZodTypeAny; resultSchema: ZodTypeAny; taskQueue: TaskQueue; idempotent: true }): void;
export function registerSignal(name: string, def: { payloadSchema: ZodTypeAny; allowedSenders: Action }): void;  // sender permission checked by authz
// Lifecycle (save, submit, approve, publish, pin) is provided by @nomology/config-core with kinds 'case_type_blueprint' and 'workflow_template'

// Temporal (registered on wf-interpreter-{region} workers, task queue 'cases'; migrations on 'cases-bulk')
export async function caseProcess(input: { caseId: string; blueprintVersionId: string; pinId: string; timeScale?: number }): Promise<CaseProcessResult>;
export const migrateBlueprint: UpdateDefinition<MigrationAck, [MigrationRequest]>;   // validator enforces quiescence (WF-workflow-versioning)
export const currentPosition: QueryDefinition<{ stage: string; activeSteps: string[]; nextDeadline?: string }>;
```

<!-- section:usage -->
## Usage examples

```json
{
  "process": "sebi-odr", "version": 3, "schemaVersion": 2,
  "stages": [
    { "key": "intake", "name": { "en": "Intake" }, "caseStatus": "in_scrutiny", "slaPolicy": "odr_scrutiny" },
    { "key": "conciliation", "name": { "en": "Conciliation" }, "caseStatus": "in_conciliation", "milestone": true, "visibleToParties": true },
    { "key": "arbitration", "name": { "en": "Arbitration" }, "caseStatus": "in_proceedings", "milestone": true, "visibleToParties": true },
    { "key": "closure", "name": { "en": "Closure" }, "caseStatus": "closed" }
  ],
  "interrupts": [ { "on": "suspend", "mode": "pause" }, { "on": "withdraw", "mode": "goto", "target": "close" } ],
  "steps": [
    { "id": "eligibility", "stage": "intake", "type": "decision", "decision": "odr-eligibility", "output": "elig" },
    { "id": "eligible_gw", "stage": "intake", "type": "gateway", "mode": "exclusive",
      "branches": [ { "when": "elig.eligible", "next": "register" }, { "next": "reject_notice" } ] },
    { "id": "register", "stage": "intake", "type": "transition", "entity": "case", "command": "register", "next": "start_conc" },
    { "id": "start_conc", "stage": "conciliation", "type": "transition", "entity": "case", "command": "start_conciliation", "next": "conc" },
    { "id": "conc", "stage": "conciliation", "type": "subprocess", "process": "odr-conciliation", "next": "conc_deadline" },
    { "id": "conc_deadline", "stage": "conciliation", "type": "timer", "kind": "procedural", "deadlineRule": "odr_conciliation_period",
      "at": { "from": "stage.enteredAt", "duration": { "value": "elig.conciliationDays", "unit": "calendar_days" }, "calendars": "seat" }, "onDue": "outcome" },
    { "id": "outcome", "stage": "conciliation", "type": "human_task", "task": { "template": "record_conciliation_outcome", "assignment": { "kind": "case_role", "role": "case_manager" } },
      "onComplete": { "settled": "close", "not_settled": "refer" } },
    { "id": "refer", "stage": "arbitration", "type": "transition", "entity": "case", "command": "refer_to_arbitration", "next": "arb" },
    { "id": "arb", "stage": "arbitration", "type": "subprocess", "process": "odr-arbitration", "next": "close" },
    { "id": "reject_notice", "stage": "intake", "type": "notification", "template": { "key": "odr.not_eligible" }, "to": { "caseRoles": ["claimant"] }, "next": "end" },
    { "id": "close", "stage": "closure", "type": "transition", "entity": "case", "command": "close_case", "next": "end" },
    { "id": "end", "stage": "closure", "type": "end" }
  ]
}
```
Assumption: the steps above illustrate shape only; the actual SEBI ODR stages and timelines (here `elig.conciliationDays`) must be taken from the applicable circulars by legal and encoded as offering-locked decision tables.

<!-- section:tenant -->
## Tenant context

Definitions are tenant-owned artefacts (forced RLS) through [[PKG-configuration-and-customisation]]. The interpreter workflow ID is `{tenantId}-process-{caseId}` and carries tenant context through interceptors; every Activity it calls re-establishes `withTenant` with that context. Signals are accepted only after `authz` confirms the sender may perform the mapped action on the case, so a template cannot open a path for an unauthorised user.

<!-- section:config -->
## Configuration

| Limit (proposed) | Value |
|---|---|
| Steps per definition | 200 |
| Nesting depth of child processes | 3 |
| Parallel branches | 5 |
| Expression length | 200 characters; grammar: literals, fact paths, comparison, boolean and arithmetic operators, `min`, `max`; no function calls beyond these |
| Continue-As-New | After 2,000 history events or each completed stage, whichever first |

The limits above are the platform defaults of the settings `workflow.authoring.max_steps`, `workflow.authoring.max_subprocess_depth`, `workflow.authoring.max_parallel_branches` and `workflow.runtime.continue_as_new_events` in [[PKG-settings-cases-and-workflows#catalogue]]; tenants may lower but not raise them. Continue-As-New also runs at every stage boundary and after every migration.

<!-- section:adapters -->
## Providers and extension points

Extension points are registries, not plugins: **activities** (`registerActivity`) and **signals** (`registerSignal`) are added by domain packages in code with schemas and task queues. A template can only reference registered names, so tenants compose reviewed building blocks and never inject code.

<!-- section:errors -->
## Error model

| Error | When | Handling |
|---|---|---|
| `ValidationIssue` (unreachable step, cycle without wait, unknown activity, missing decision, expression type error) | Save / publish | Blocks publish |
| Runtime expression error | Interpreter | Step fails to a `humanTask` "configuration problem" for the secretariat; alert tenant admin and platform on-call |
| Activity failure after retries | Interpreter | Per-activity policy: human task or compensation step if defined |
| Invalid state transition | Interpreter calls state machine | Rejected by [[WF-entity-state-machines]]; human task |
| `InterpreterContractUnsupported` | Publish: blueprint needs a contract newer than the region's workers | Blocks publish with the supported contract shown |
| `LockedComponentChanged` | Publish: offering- or platform-locked component modified | Blocks publish; lock source shown |
| `MigrationRejected` | `migrateBlueprint` Update while not quiescent or mapping incomplete | Item `skipped`, retried by the migration workflow |

<!-- section:nfr -->
## Performance and limits

Validation ≤ 2 s for 200 steps; simulation ≤ 1 s per scenario. The interpreter adds no more than one Activity call (definition load) per run start.

<!-- section:versioning -->
## Versioning and compatibility

- **Blueprint and template versions** are immutable and pinned per case; lifecycle, change classes and migration are in [[WF-workflow-versioning]].
- **Interpreter code** runs as Auto-Upgrade workflows under Temporal Worker Versioning; every change to the command sequence uses `patched()` with replay tests ([[WF-separation-of-concerns-temporal#design]]).
- **Interpreter contract** (`interp/<major>.<minor>`): minor bumps add elements or options; a major bump ships an upgrader from `schemaVersion n` to `n+1`. Drafts are upgraded in place; published versions are upgraded into new drafts for each tenant's own review. The previous major contract stays supported for at least 24 months (proposed).
- **schemaVersion 1 to 2**: v1 step names are accepted by the upgrader (see comments in the API); no v1 bodies exist in production yet.

<!-- section:testing -->
## Test contract

- Validator unit tests for every issue type.
- Simulation tests: authors attach scenarios (signals, timeouts, decision outputs); publish requires all to pass.
- Interpreter replay tests with Temporal's test environment for every step type, including Continue-As-New.
- Pinning: a case started on version 2 keeps version 2 after version 3 is published.
- Conformance suite shared by the pure core, the Temporal shell (time-skipping test environment) and the simulator; traces must be identical.
- Upgrader tests from every previous `schemaVersion` with golden inputs.

<!-- section:questions -->
## Open questions

- [x] Visual editor phase: decided, Phase 4 ([[WF-workflow-authoring-studio]]).
- [ ] Which processes start as code workflows vs blueprints. Proposed: case lifecycle as blueprints (from library blueprints), notice service, eBundling and pipelines as code workflows exposed as registered subprocesses.
- [ ] Expression grammar: in-house (proposed, small, shared as `@nomology/expr` by gateways, automation conditions and decision outputs) vs an existing safe language (for example CEL or JSONata).
- [x] Cross-reference fixed: the summary now points to [[WF-separation-of-concerns-temporal]] (7.5).

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Templates are tenant-owned; interpreter workflow IDs are tenant-prefixed and context is propagated by interceptors; every Activity re-enters `withTenant`; signals are authorised against the case.

<!-- check:security -->
### Security of the API surface

Only registered activities and signals can be referenced; expressions use a closed grammar without I/O; definitions are schema-validated; state changes still pass through the entity state machine guards.

<!-- check:resilience -->
### Failure behaviour

The definition is loaded once at start and passed in, so replay never depends on mutable data; registered activities must be declared idempotent; runtime configuration errors fall to a human task instead of failing the case silently.

<!-- check:change-safety -->
### Change and release safety

Published versions are pinned per case; interpreter changes use Temporal versioning; publish requires passing simulation scenarios and maker-checker approval. Interpreter code changes run under Auto-Upgrade with patching and a shared conformance suite; contract versions gate which elements a region can run.

<!-- check:testing -->
### Testing

Validator tests, author-supplied simulation scenarios as a publish gate, Temporal replay tests for each step type and pin-stability tests.

<!-- end -->
