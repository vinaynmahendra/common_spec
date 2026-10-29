---
id: "WF-human-tasks"
title: "Human tasks"
parent: "WF"
order: 4
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "Human tasks: task templates, tenant-configured work queues and assignment rules, SLAs, escalation chains, reminders, delegation and bulk reassignment"
links: []
rev: 4
syncHash: "60a216df6bc47f6f"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 7.3 Human tasks

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Human tasks: task templates, tenant-configured work queues and assignment rules, SLAs, escalation chains, reminders, delegation and bulk reassignment

<!-- section:purpose -->
## Purpose and scope

`packages/human-tasks` manages work that a person must do: review a submitted case, approve a bundle, accept an appointment, direct alternative service, answer an accessibility accommodation request. It stores tasks in Postgres for inboxes and reports, resolves who should do each task through tenant-configured **work queues and assignment rules**, computes due times through SLA policies and business schedules, sends reminders, escalates through configured **escalation chains**, reassigns when people leave or are out of office, and returns the result to the Temporal workflow that is waiting.

Tasks come from three sources: steps in a case-type blueprint (`human_task` element, [[WF-process-definition-model]]), code workflows in domain packages, and automation rules (`create_task` action, [[WF-automation-rules]]).

**Tenant-configurable** (requirement prefix `HT-FR-`):

- **HT-FR-1 Task templates.** A task template (artefact kind `task_template`) defines label and instructions per locale, the outcome form ([[PKG-forms-and-form-builder]]), allowed outcomes and their meaning for branching, the permission to complete (default `case.task:update`), default priority, SLA policy, escalation chain, whether step-up is required on completion, and whether parties can see it on their timeline.
- **HT-FR-2 Work queues.** A tenant or unit admin can define queues (`wf.work_queue`) with members (users or groups), per-member capacity and skills, a business schedule, and a strategy: `pull` (members claim), `round_robin`, `least_loaded` (fewest open tasks weighted by capacity) or `skills` (match required skills such as language or panel, then least loaded).
- **HT-FR-3 Assignment rules.** Assignment is resolved in this order: explicit membership; case role (`case_manager`, `presiding_neutral` …); queue with strategy; fallback queue (`workflow.runtime.config_failure_task_queue`). Resolution excludes anyone blocked by an ethical wall or conflict on the case ([[PKG-ethical-walls-conflict-based]]) and anyone without the completion permission.
- **HT-FR-4 Escalation chains.** An escalation chain is an ordered list of up to `workflow.task.escalation_max_levels` levels; each level has a trigger (SLA warning level or breach, or "unclaimed for N business hours"), a target (role, queue or the assignee's manager from the org unit), and actions (notify, reassign, raise priority). The final level's policy is `keep_open` or `expire`.
- **HT-FR-5 Out of office and delegation.** A user can set a delegate (`workflow.task.out_of_office_delegate`); while out of office, new tasks route per `workflow.task.out_of_office_auto_reassign`; delegates act with their own permissions, never the delegator's.
- **HT-FR-6 Bulk operations.** Supervisors with `case.task:assign` can bulk-reassign or bulk-claim up to 500 tasks per operation with a reason, through the bulk operations framework ([[APP-bulk-admin-operations]]).

**Does not do**: decide what the task's outcome means (the owning workflow does), send messages itself ([[PKG-notifications]]), compute calendars ([[PKG-calendars-and-deadline]], which it calls), or define SLA policy semantics ([[WF-sla-and-business-calendars]]).

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Example task types |
|---|---|
| Case workflow ([[DOM-cases]]) | `scrutinise-case`, `fix-defects` (claimant), `register-case` |
| [[DOM-service-of-notices-and-proof]] | `direct-alternative-service` |
| [[DOM-neutrals]] | `review-conflict-hits`, `accept-appointment` (neutral), `decide-challenge` |
| [[DOM-ebundling]] | `fix-bundle-manifest`, `review-bundle` |
| [[DOM-invoices-and-vendor-bills]] | `review-vendor-bill`, `screening-hold-review` |
| [[APP-accessibility-feedback]] | `accommodation-request` (standalone task, no workflow) |
| Persona apps | Inbox views in [[APP-secretariat-console]], [[APP-neutral-workspace]], [[APP-party-and-counsel-portal]], [[APP-transcriber-workspace]] |
| Blueprints ([[WF-process-definition-model]]) | Any `human_task` element, for example `scrutinise_case`, `record_conciliation_outcome`, `approve_settlement_terms` |
| [[WF-automation-rules]] | `create_task` and `assign_task` actions; `task.overdue`, `task.escalated` as triggers |
| [[WF-ai-steps-and-agents]] | Review tasks for AI suggestions (`review_ai_suggestion`), with the suggestion as task context |
| Admin studio ([[WF-workflow-authoring-studio]]) | Queue, task template and escalation chain configuration |

<!-- section:api -->
## Public API

**Server API** (`@nomology/human-tasks`)

```ts
export interface TaskSpec {
  taskType: string;                         // registered type with its form schema and permissions
  subject: { kind: 'case' | 'document' | 'bundle' | 'appointment' | 'invoice' | 'vendor_bill' | 'other'; id: string };
  caseId?: string;
  assignment:
    | { kind: 'membership'; membershipId: string }
    | { kind: 'case_role'; role: 'tribunal_secretary' | 'presiding_neutral' | 'case_manager' | 'claimant_counsel' | 'respondent_counsel'; partyId?: string }
    | { kind: 'pool'; poolKey: string }                     // e.g. 'secretariat', 'transcription-managers' (pull)
    | { kind: 'round_robin'; poolKey: string }
    | { kind: 'queue'; queueKey: string; strategyOverride?: QueueStrategy; skills?: string[] }   // tenant-configured wf.work_queue
    | { kind: 'template_default' };                         // use the task template's assignment rule
  sla: { policyKey: string; policyVersion: number };       // SLA policy (WF-sla-and-business-calendars), pinned
  template?: { key: string; version: number };             // task template from the blueprint component lock
  escalation?: { chainKey: string; chainVersion: number };
  priority?: 'normal' | 'high' | 'urgent';
  context: Record<string, unknown>;                         // shown to the assignee; IDs and short labels only
  owner: { kind: 'workflow'; workflowId: string } | { kind: 'none' };
  idempotencyKey: string;
}

export function createTask(ctx: TenantContext, spec: TaskSpec): Promise<HumanTask>;
export function claimTask(ctx: UserContext, taskId: string, expectedVersion: number): Promise<HumanTask>;
export function releaseTask(ctx: UserContext, taskId: string): Promise<HumanTask>;
export function completeTask(ctx: UserContext, taskId: string, outcome: unknown, expectedVersion: number): Promise<HumanTask>;
export function reassignTask(ctx: UserContext, taskId: string, to: TaskSpec['assignment'], reason: string): Promise<HumanTask>;
export function cancelTask(ctx: TenantContext, taskId: string, reason: string): Promise<void>;
export function listMyTasks(ctx: UserContext, filter: { status?: TaskStatus[]; caseId?: string; dueBefore?: Date }, page: Cursor): Promise<Page<HumanTaskSummary>>;
export function listPoolTasks(ctx: UserContext, poolKey: string, filter, page): Promise<Page<HumanTaskSummary>>;
export function registerTaskType(def: { taskType: string; outcomeSchema: z.ZodTypeAny; permission: string; labelKey: string }): void;   // code-defined types
export function bulkReassign(ctx: UserContext, taskIds: string[], to: TaskSpec['assignment'], reason: string, idempotencyKey: string): Promise<{ operationId: string }>;
export function setOutOfOffice(ctx: UserContext, input: { from: Date; until: Date; delegateMembershipId?: string }): Promise<void>;
export function explainAssignment(ctx: UserContext, taskId: string): Promise<AssignmentExplanation>;   // which rule, queue, strategy and exclusions chose the assignee

// Queue administration (tenant admin console, /admin/workflows/queues; permission workflow.queue:configure)
export type QueueStrategy = 'pull' | 'round_robin' | 'least_loaded' | 'skills';
export function upsertQueue(tx: TenantTx, q: { key: string; unitId?: string; name: LocalisedText; strategy: QueueStrategy;
  skillsRequired?: string[]; capacityDefault?: number; businessScheduleKey?: string }): Promise<void>;
export function setQueueMembers(tx: TenantTx, queueKey: string, members: { membershipId?: string; groupId?: string; capacity?: number; skills?: string[] }[]): Promise<void>;
```

**Workflow helper** (`@nomology/human-tasks/workflow`, safe for the Temporal sandbox: no I/O, only activities, timers and an update handler)

```ts
export async function awaitHumanTask<O>(spec: Omit<TaskSpec, 'owner'>): Promise<
  { kind: 'completed'; outcome: O; completedBy: string } | { kind: 'cancelled'; reason: string } | { kind: 'expired' }>;
// Registers update 'completeHumanTask' with a validator, creates the task via activity,
// waits with condition() until the next reminder / escalation instant, runs reminder and escalation activities,
// and returns when the update completes it or the final timeout policy says 'expire'.
```

Statuses: `open`, `claimed`, `waiting_on_external` (SLA paused), `completed`, `cancelled`, `expired`.

Audit events: `case.task.created`, `case.task.claimed`, `case.task.reassigned`, `case.task.escalated`, `case.task.completed`; admin events `admin.queue.updated`, `admin.queue.members_changed`, `admin.task_template.published`.

<!-- section:usage -->
## Usage examples

```ts
// In the notice-service recipient workflow
const result = await awaitHumanTask<{ channel: string; address?: string } | { manual: true; evidenceId: string }>({
  taskType: 'direct-alternative-service',
  subject: { kind: 'case', id: input.caseId }, caseId: input.caseId,
  assignment: { kind: 'case_role', role: 'tribunal_secretary' },
  sla: { policyKey: 'secretariat-task-sla', policyVersion: input.slaPolicyVersion },
  context: { recipientId, channelsTried },
  idempotencyKey: `${workflowInfo().workflowId}:alt-service:${round}`,
});
if (result.kind === 'expired') await escalateToCaseManager(...);

// In the API (tRPC procedure) when the secretary submits the form
await humanTasks.completeTask(userCtx, taskId, formValues, expectedVersion);
// -> checks permission and version, then sends Temporal update 'completeHumanTask' to the owning workflow,
//    which validates and persists the completion through an idempotent activity.
```

<!-- section:tenant -->
## Tenant context

Tasks are tenant-owned rows (`human_tasks`, `human_task_events`) under forced RLS. `createTask` takes a `TenantContext`; activities pass tenant ID explicitly. Pool keys and round-robin cursors are per tenant. Assignment resolution (`case_role`) reads the case's participants inside the tenant transaction. A user who belongs to several tenants sees only the active tenant's inbox ([[PKG-tenant-and-role-switcher]]).

Tables (owned by this package): `human_tasks` (id, tenant_id, task_type, subject_kind, subject_id, case_id, assignee_membership_id, pool_key, status, priority, due_at, next_reminder_at, escalation_level, sla_policy_key, sla_policy_version, context jsonb, outcome jsonb, owner_workflow_id, idempotency_key unique per tenant, created_at, completed_at, completed_by_membership_id, version) and `human_task_events` (append-only: created, claimed, released, reminded, escalated, reassigned, completed, cancelled, expired).

Queue tables `wf.work_queue` and `wf.work_queue_member` are tenant-owned under forced RLS; a unit-scoped queue is visible and editable only to holders of `workflow.queue:configure` scoped to that unit (ABAC scope check in [[PKG-rbac-abac-case-level-party]]). Assignment resolution reads ethical-wall exclusions inside the same tenant transaction. Tables gain `human_tasks.task_template_key`, `task_template_version`, `queue_key`, `escalation_chain_key` and `blueprint_step_id` (nullable for code task types).

<!-- section:config -->
## Configuration

| What | Where it is defined | Who changes it | Scope |
|---|---|---|---|
| Code task types (outcome schema, permission) | `registerTaskType` in domain packages | Platform engineering | Platform |
| Task templates (labels, outcome form, outcomes, SLA policy, escalation chain, step-up, party visibility) | Blueprint components, artefact kind `task_template` | `workflow_designer` | Tenant, pinned per case via the blueprint |
| Work queues, members, capacity, skills, strategy, schedule | `wf.work_queue`, `wf.work_queue_member` ([[WF-process-definition-model#tables]]) | `tenant_admin`, `unit_admin` for their units (`workflow.queue:configure`) | Tenant, unit; live (not pinned) |
| Escalation chains | Artefact kind `escalation_chain` | `workflow_designer` | Tenant, pinned with the blueprint |
| SLA policies and business schedules | [[WF-sla-and-business-calendars]] | `workflow_designer`, `unit_admin` | Tenant, unit, queue |
| Defaults (strategy, max open per assignee, claim timeout, reassign reason, out-of-office routing, party tasks) | `workflow.task.*` in [[PKG-settings-cases-and-workflows#catalogue]] | Per catalogue | Platform to user |

Example queue and escalation chain:

```json
{ "queue": { "key": "sg_registry", "unitKey": "singapore_office", "strategy": "skills",
             "skillsRequired": ["lang:zh"], "capacityDefault": 25, "businessScheduleKey": "sg_office" } }

{ "escalationChain": { "key": "secretariat_default", "levels": [
    { "on": { "slaWarning": 2 }, "actions": [ { "notify": { "to": "assignee" } } ] },
    { "on": { "slaBreach": true }, "target": { "queue": "sg_registry_leads" },
      "actions": [ { "reassign": true }, { "raisePriority": "high" } ] },
    { "on": { "afterBreach": "P1D", "basis": "business_days" }, "target": { "role": "unit_admin" },
      "actions": [ { "notify": { "to": "target" } } ], "final": "keep_open" } ] } }
```

Queue and membership changes apply to new assignments immediately; tasks already assigned stay with their assignee unless the change removes the member, in which case they return to the queue with a `reassigned` event (reason `member_removed`).

<!-- section:errors -->
## Error model

| Error | Meaning | Caller action |
|---|---|---|
| `TaskNotFound` | Not in this tenant or not visible | 404 with the shared not-found text ([[APP-error-message-catalogue]]) |
| `TaskVersionConflict` | Someone else changed it | Reload and show "already handled by …" |
| `TaskAlreadyCompleted` | Second completion | Show the existing outcome |
| `NotAssignee` / `PermissionDenied` | Not allowed | 403 |
| `OutcomeValidationError` | Outcome does not match schema | Show field errors |
| `OwnerWorkflowUnavailable` | Temporal update failed (retryable) | Retry with backoff; the task stays claimed |
| `NoEligibleAssignee` | Every candidate is excluded (walls, permissions, out of office) | Task goes to the fallback queue with a `configuration` flag; tenant admin alerted |
| `QueueNotFound` | Template or rule references a missing or retired queue | Validation error at publish; at runtime fallback queue and alert |
| `BulkLimitExceeded` | More than 500 tasks in one bulk operation | 422; split the selection |

<!-- section:nfr -->
## Performance and limits

Inbox query p95 under 200 ms for 5,000 open tasks per tenant pool. Completion round trip (API → update → activity persisted) p95 under 1.5 s. Reminder timing accuracy within 1 minute of policy time.

<!-- section:testing -->
## Test contract

Time-skipping workflow tests for reminders, escalation and expiry for each policy shape [R1]; race test where two users complete the same task (second gets `TaskAlreadyCompleted`); reassignment when the assignee's membership ends; isolation tests on both tables; contract tests for every registered task type's outcome schema. Assignment strategy tests (round robin fairness across 1,000 tasks, least-loaded with capacities, skills match with fallback), ethical-wall exclusion tests, out-of-office routing tests, escalation-chain tests for each level trigger with time-skipping, and `explainAssignment` output tests.

<!-- section:questions -->
## Open questions

- [ ] Should the inbox also show "waiting on others" tasks (for example the secretary sees that the respondent's response is due)? Proposed: yes, read-only, derived from case deadlines rather than tasks.
- [x] Out-of-office delegation: decided, HT-FR-5, Phase 4.
- [ ] Do parties (unrepresented) get tasks, or only deadlines and notifications? Proposed: controlled by `workflow.task.party_tasks_enabled` (on for CORD and SEBI ODR blueprints), with plain-language guidance from [[DOC-plain-language-guidance-for]]. Owner: product.
- [ ] Skills taxonomy: free tags per tenant or a platform list (languages, panels, specialisations)? Proposed: platform prefixes (`lang:`, `panel:`, `region:`) with tenant-defined values. Owner: product.
- [ ] Should capacity consider task weight (a scrutiny task counts more than an acknowledgement)? Owner: product.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Both tables are tenant-owned under forced RLS; `createTask` requires a tenant context; pools and round-robin cursors are per tenant; the update to the owning workflow is addressed by a workflow ID that starts with the tenant ID, and the API wrapper checks that prefix against the caller's tenant.

<!-- check:security -->
### Security of the API surface

Each task type declares the permission needed to complete it; completion checks both that permission and that the user is the assignee (or a pool member who has claimed it). The workflow update validator re-checks the task is open and the completer matches, so a forged update cannot complete someone else's task [R2]. Task `context` holds IDs and labels only. Assignment never selects someone excluded by an ethical wall or lacking the completion permission (HT-FR-3); delegates act with their own permissions.

<!-- check:audit -->
### Audit events

Every task event (created, claimed, reminded, escalated, reassigned with reason, completed with outcome hash, cancelled, expired) is appended to `human_task_events` and the audit log in the same transaction. Where the outcome has legal effect (for example a direction for alternative service), the owning domain also records it.

<!-- check:observability -->
### Observability

Metrics: open tasks by type, tenant and age bucket; share completed within SLA; escalations per day. Search attribute `assigneeRole` and `nextDeadline` on owning workflows. Alert: tasks past final escalation with `keep_open` policy for more than 2 business days.

<!-- check:resilience -->
### Failure behaviour

`createTask` is idempotent on `idempotencyKey`; the persistence activity behind the update is idempotent on task ID and version. If Temporal is unavailable at completion, the API returns a retryable error and the task stays claimed; nothing is completed in Postgres without the workflow accepting it.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "The time-skipping test environment fast-forwards timers in workflow tests.",
    "id": "R1",
    "kind": "vendor",
    "title": "Temporal docs: Testing suite (TypeScript)",
    "url": "https://docs.temporal.io/develop/typescript/testing-suite",
    "vendor": "Temporal Technologies"
  },
  {
    "excerpt": "Updates can be validated before they are accepted; a rejected update is not written to history.",
    "id": "R2",
    "kind": "vendor",
    "title": "Temporal docs: Workflow message passing (TypeScript)",
    "url": "https://docs.temporal.io/develop/typescript/message-passing",
    "vendor": "Temporal Technologies"
  }
]
```

<!-- end -->
