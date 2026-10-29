---
id: "WF-automation-rules"
title: "Automation rules (trigger, condition, action)"
parent: "WF"
order: 9
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "@nomology/automation: tenant-authored 'when, if, do' rules on BullMQ with a closed, non-procedural action catalogue, ordering, limits, loop protection, dry runs and an execution log"
links: []
rev: 1
syncHash: "2848086d0c3cfcb3"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 7.8 Automation rules (trigger, condition, action)

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> @nomology/automation: tenant-authored 'when, if, do' rules on BullMQ with a closed, non-procedural action catalogue, ordering, limits, loop protection, dry runs and an execution log

<!-- section:purpose -->
## Purpose and scope

`@nomology/automation` lets tenant administrators define simple, event-driven **automation rules** of the form "**when** X happens, **if** Y is true, **do** Z", without code and without changing a case-type blueprint. Examples: "When a document of type Power of Attorney is uploaded and the case is in scrutiny, add the tag `poa-received` and notify the case manager"; "Every weekday at 09:00, for cases waiting on deposit for more than 10 business days, create a follow-up task in the Accounts queue".

Rules run on **BullMQ** ([[WF-background-jobs-and-queues]]), not Temporal, as the shared model's workflow authoring boundary requires: each execution is short, independent and retryable. Anything that waits on people or on legal time, or changes the procedure, belongs in the blueprint ([[WF-process-definition-model]]) and its Temporal interpreter.

**Does:** store and version rules; match triggers from the outbox event stream, schedules and manual runs; evaluate conditions with the shared expression grammar; execute a closed catalogue of actions as a constrained principal; enforce limits, ordering and loop protection; log every execution; support dry runs.

**Does not:** change case status or procedural deadlines, move documents between confidentiality tiers, add or remove parties or neutrals, or run arbitrary code or HTTP calls (outbound calls only through registered webhooks, [[APP-webhooks-outbound]]). It does not send messages itself (uses [[PKG-notifications]]) or create AI output directly (it may request a suggestion from an AI step owned by [[WF-ai-steps-and-agents]]).

Requirements use the prefix `AUT-FR-`.

- **AUT-FR-1** Every rule has exactly one trigger, zero or more conditions (AND / OR groups, depth at most 2) and 1 to 10 actions, executed in order.
- **AUT-FR-2** Actions are chosen only from the registered action catalogue; actions with procedural effect are not registrable.
- **AUT-FR-3** Rules apply to running cases from the moment they are published (they are not pinned), because their actions are non-procedural.
- **AUT-FR-4** Each execution runs as the rule's automation principal, whose permissions are the intersection of the rule's declared action permissions and the permissions of the publishing user at publish time; it is re-checked at each run.
- **AUT-FR-5** Loop protection stops any chain of rule-triggered events deeper than 3, any rule firing twice in one chain, and any rule exceeding 10 executions on the same subject within 10 minutes; the rule is then suspended and its owners alerted.
- **AUT-FR-6** Every execution, skipped or failed evaluation included, is logged with trigger, matched conditions, actions and outcome, for 90 days by default.

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Use case |
|---|---|
| Tenant admin console ([[WF-workflow-authoring-studio]], `/admin/workflows/automation`) | Author, test, publish, disable rules; view execution log |
| Secretariat console ([[APP-secretariat-console]]) | "Run automation" button on a case for rules with a `manual` trigger; banner when a rule acted on the case |
| Outbox relay and event bus ([[OBS-business-events]]) | Source of domain events that trigger rules |
| [[WF-human-tasks]] | `create_task`, `assign_task` actions; `task.overdue` and `task.escalated` events as triggers |
| [[PKG-notifications]] | `notify` action enqueues `notifications.send` |
| [[APP-webhooks-outbound]] | `send_webhook` action to a tenant-registered endpoint |
| Admin copilot ([[APP-admin-copilot]]) | Drafts rules from a description ("when a respondent counsel is added, notify the claimant counsel"); human reviews and publishes |
| Reports ([[RPT-cases]]) | Counts of automation actions per rule and tenant |

<!-- section:api -->
## Public API

```ts
// packages/automation/src/index.ts (server-only)

export type TriggerDef =
  | { kind: 'event'; event: RegisteredEventType; filter?: Record<string, unknown> }   // e.g. 'document.uploaded', 'case.stage_entered'
  | { kind: 'schedule'; cron: string; timeZone: string; scope: CaseFilter }          // at most hourly; evaluated per matching case
  | { kind: 'manual'; label: LocalisedText; allowedPermission: PermissionKey };       // run on one case by a user

export type Condition =
  | { all: Condition[] } | { any: Condition[] }
  | { expr: Expr };                    // shared closed grammar from @nomology/expr, same as decision tables and gateways

export type ActionDef =
  | { kind: 'notify'; template: TemplateRef; to: RecipientSpec }                     // roles or fact refs, never literal addresses
  | { kind: 'create_task'; taskTemplate: TaskTemplateRef; assignment: AssignmentSpec; dueIn?: DurationSpec }
  | { kind: 'assign_task'; taskSelector: TaskSelector; assignment: AssignmentSpec }
  | { kind: 'add_tag' | 'remove_tag'; tag: string }
  | { kind: 'set_field'; field: CustomFieldKey; value: Expr }                        // only fields flagged automation_writable (non-procedural)
  | { kind: 'add_note'; text: LocalisedText; visibility: 'tenant_internal' }
  | { kind: 'add_watcher'; who: RecipientSpec }
  | { kind: 'raise_priority'; to: 'high' | 'urgent' }
  | { kind: 'send_webhook'; endpointId: string; eventName: string }
  | { kind: 'signal_case_process'; signal: RegisteredSignal }                       // only signals the blueprint declares as automation-safe
  | { kind: 'request_ai_suggestion'; aiStep: AiStepRef };                            // creates a suggestion for human review

export interface AutomationRule {
  key: string; version: number;
  name: LocalisedText; description?: string;
  scope: { unitIds?: string[]; caseTypeKeys?: string[] };    // empty = whole tenant
  trigger: TriggerDef; conditions?: Condition; actions: ActionDef[];
  position: number;                    // evaluation order within the same trigger
  stopFurtherRules?: boolean;          // when matched, later rules for the same event are skipped
  enabled: boolean;
}

// Authoring (lifecycle from @nomology/config-core, kind 'automation_rule')
export function saveDraft(tx: TenantTx, rule: Omit<AutomationRule, 'version'>): Promise<{ id: string; issues: ValidationIssue[] }>;
export function dryRun(tx: TenantTx, draftId: string, input: { caseId: string } | { eventId: string }): Promise<DryRunReport>; // no side effects
export function publish(tx: TenantTx, draftId: string, opts: { reason: string }): Promise<{ version: number }>;     // maker-checker per setting
export function setEnabled(tx: TenantTx, key: string, enabled: boolean, reason: string): Promise<void>;
export function reorder(tx: TenantTx, trigger: string, keysInOrder: string[]): Promise<void>;

// Runtime
export function runManual(ctx: UserContext, ruleKey: string, caseId: string, idempotencyKey: string): Promise<{ executionId: string }>;
export function listExecutions(tx: TenantTx, filter: { ruleKey?: string; caseId?: string; outcome?: ExecutionOutcome[]; since?: Date }, page: Cursor): Promise<Page<ExecutionSummary>>;

// Registry (code; domain packages register their actions and events)
export function registerAction<A>(def: { kind: string; schema: ZodType<A>; permission: PermissionKey; procedural: false;
  execute: (ctx: ActionContext, args: A) => Promise<ActionResult> }): void;
export function registerEvent(def: { type: string; payloadSchema: ZodType; subject: 'case' | 'task' | 'document' | 'hearing' | 'invoice' }): void;

export type ExecutionOutcome = 'succeeded' | 'partially_failed' | 'failed' | 'skipped_conditions' | 'skipped_loop' | 'skipped_limit' | 'skipped_permission';
```

**Queues** (added to the catalogue in [[WF-background-jobs-and-queues#api]]):

| Queue | Payload (IDs only) | Purpose |
|---|---|---|
| `automation.evaluate` | `{ eventId, eventType, subjectId, chain: string[] }` | Fan-out: find enabled rules for this trigger in order, evaluate conditions, enqueue executions |
| `automation.execute` | `{ executionId, ruleVersionId, subjectId, chain }` | Run actions in order for one matched rule |
| `automation.schedule` | `{ ruleVersionId, firedAt }` | Per-region repeatable tick (every minute) that enqueues due scheduled rules; one job per rule, then one execution per matching case (max 5,000 cases per run) |

**Events emitted:** `automation.executed`, `automation.rule_suspended` (to the outbox, so webhooks and reports can use them). **Audit events:** `admin.automation.draft_saved`, `admin.automation.published`, `admin.automation.enabled`, `admin.automation.disabled`, `admin.automation.auto_suspended`, `admin.automation.reordered`.

<!-- section:usage -->
## Usage examples

```json
{
  "key": "poa_received", "name": { "en": "Power of attorney received" },
  "scope": { "caseTypeKeys": ["inst_arbitration"] },
  "trigger": { "kind": "event", "event": "document.uploaded", "filter": { "documentType": "POWER_OF_ATTORNEY" } },
  "conditions": { "all": [ { "expr": "case.stage == 'scrutiny'" }, { "expr": "document.filedByRole in ['claimant_counsel','respondent_counsel']" } ] },
  "actions": [
    { "kind": "add_tag", "tag": "poa-received" },
    { "kind": "notify", "template": { "key": "staff.document_received" }, "to": { "caseRoles": ["case_manager"] } }
  ],
  "position": 10, "enabled": true
}
```

```ts
// Worker for automation.execute (inside packages/automation)
createWorker(automationExecuteQueue, async (job) => {
  await job.withTenantTx(async (tx) => {
    const exec = await loadExecution(tx, job.payload.executionId);           // idempotent: returns if already finished
    const principal = await automationPrincipal(tx, exec.ruleVersionId);     // AUT-FR-4
    for (const [i, action] of exec.actions.entries()) {
      const key = `${exec.id}:${i}`;
      try {
        await runAction(tx, principal, action, { idempotencyKey: key, chain: job.payload.chain });
      } catch (e) {
        if (e instanceof PermissionDenied) return markSkipped(tx, exec, 'skipped_permission', i);
        if (isRetryable(e)) throw e;                                          // BullMQ retries the job; done actions are skipped by key
        await markActionFailed(tx, exec, i, e);                               // continue or stop per rule.onActionError
      }
    }
    await markSucceeded(tx, exec);
  });
});
```

<!-- section:tenant -->
## Tenant context

- Rules, versions and executions are tenant-owned tables under forced RLS in the regional database:
  - `wf.automation_rule` (`id`, `tenant_id`, `key`, `scope_unit_ids uuid[]`, `scope_case_type_keys text[]`, `trigger_kind`, `trigger_event text NULL`, `position int`, `enabled boolean`, `current_version_id`, `suspended_reason text NULL`, `owner_membership_id`, `version`);
  - `wf.automation_rule_version` (`id`, `tenant_id`, `rule_id`, `version_no`, `artefact_version_id` → `config.artefact_version` kind `automation_rule`, `principal_permissions text[]` frozen at publish, `published_by`, `published_at`);
  - `wf.automation_execution` (`id`, `tenant_id`, `rule_version_id`, `trigger_event_id`, `subject_kind`, `subject_id`, `chain text[]`, `outcome`, `matched boolean`, `actions jsonb` (per action: kind, status, error code), `started_at`, `finished_at`), partitioned daily.
- Every job envelope carries `tenantId` and `region`; the worker wrapper opens every transaction with that tenant ([[WF-background-jobs-and-queues#tenant]]). Rule lookup for an event runs inside the event's tenant only; there is no cross-tenant rule.
- Per-tenant fairness: `automation.execute` uses `tenantFairness.maxActivePerTenant = 10` (proposed) so one tenant's bulk scheduled rule cannot starve others.
- The automation principal is a tenant-scoped `service_account` of type `automation` ([[PKG-non-human-principals]]), one per rule version; actions are attributed in audit as "Automation: <rule name> (published by <user>)".

<!-- section:config -->
## Configuration

Settings (catalogued in [[PKG-settings-cases-and-workflows#catalogue]]):

| Key | Default | Scopes |
|---|---|---|
| `workflow.automation.enabled` | true | platform, offering, tenant |
| `workflow.automation.max_rules` | 200 (plan-dependent) | platform, tenant (bounded by plan) |
| `workflow.automation.max_actions_per_rule` | 10 | platform |
| `workflow.automation.max_executions_per_hour` | 5,000 per tenant (plan-dependent) | platform, tenant |
| `workflow.automation.max_chain_depth` | 3 | platform (hard bound), tenant may lower |
| `workflow.automation.loop_threshold` | 10 executions per rule per subject per 10 minutes | platform |
| `workflow.automation.schedule_min_interval_min` | 60 | platform |
| `workflow.automation.publish_requires_approval` | true | tenant |
| `workflow.automation.execution_log_retention_days` | 90 | platform, tenant (30–365) |
| `workflow.automation.allowed_actions` | all registered | offering, tenant (subset) |

Limits follow the pattern of no-code automation products, which cap steps per rule, queued items, daily processing time and repeated self-triggering [R1]. Values above are proposals.

<!-- section:adapters -->
## Providers and extension points

Extension points are code registries, not tenant plugins:

- **Events** (`registerEvent`): each domain package registers the outbox events that may trigger rules, with a payload schema and subject kind. Initial set: `case.created`, `case.stage_entered`, `case.stage_exited`, `case.status_changed`, `case.party_added`, `case.representative_added`, `document.uploaded`, `document.approved`, `filing.submitted`, `deadline.approaching`, `deadline.missed`, `task.created`, `task.overdue`, `task.escalated`, `hearing.scheduled`, `hearing.rescheduled`, `invoice.issued`, `payment.settled`, `payment.overdue`, `notice.delivery_failed`.
- **Actions** (`registerAction`): each with a Zod schema, the permission it needs and `procedural: false` (a literal type, so a procedural action does not compile). Adding an action is a pull request with security review.
- **Condition functions**: the closed list in `@nomology/expr` (comparison, boolean, `in`, `contains`, `daysSince`, `businessDaysSince(schedule)`, `isEmpty`); no user-defined functions.

Pattern borrowed from: rule-based automation in work-management tools (trigger, condition, action with audit and service limits) [R1]; ordered triggers with "stop further processing" from help-desk tools.

<!-- section:errors -->
## Error model

| Error | When | Retryable | Handling |
|---|---|---|---|
| `RuleValidationError` | Save or publish: unknown event, action not allowed for tenant, expression type error, field not automation-writable, literal address in recipients | No | Blocks publish; shown in studio |
| `PermissionDenied` (runtime) | Principal lacks permission, for example publisher lost the role | No | Execution `skipped_permission`; rule suspended after 3 in a row; owners notified |
| `LoopDetected` | AUT-FR-5 thresholds | No | Execution `skipped_loop`; rule suspended; alert `automation_loop_suspended` to tenant admins and platform on-call |
| `TenantLimitExceeded` | Hourly execution cap | Yes (delayed) | Job re-delayed to next window without consuming attempts; banner in studio |
| `ActionFailed` (provider or downstream) | Action threw a retryable error | Yes | BullMQ retries with backoff (attempts 5); completed actions are skipped by idempotency key |
| `ActionRejected` (business) | Downstream refused (task already closed) | No | Recorded per action; continue or stop per `onActionError` (`continue` default, or `stop`) |

<!-- section:nfr -->
## Performance and limits

- Event to action latency p95 under 30 s for event triggers (same budget as `notifications.send` wait in [[WF]]).
- Rule matching: at most 200 enabled rules per tenant per trigger type; matching uses an in-memory index per tenant and trigger, refreshed on publish (cache key `automation:{tenantId}:{trigger}:{publishedSeq}`).
- Condition evaluation p99 under 2 ms per rule.
- Scheduled rules: at most 5,000 matching cases per run; larger selections are refused at publish with a suggestion to narrow the scope.
- Execution log write is one insert per execution plus per-action status in the same row.

<!-- section:versioning -->
## Versioning and compatibility

- Rules are configuration artefacts (`automation_rule` kind) with immutable versions; publishing a new version takes effect for events relayed after the publish commit. In-flight executions finish on the version they started with.
- Rules are deliberately **not** pinned to cases (AUT-FR-3). Because of that, the action catalogue may never contain an action with procedural effect; a request for one is a blueprint feature instead.
- Package semver: adding an action or event is minor; changing an action's schema needs a new action kind (`notify@2`) and an upgrader for drafts and published rules (published rules are upgraded into drafts for tenant review).
- Rules travel in configuration packages ([[PKG-configuration-packages]]) and import as disabled drafts.

<!-- section:testing -->
## Test contract

- Unit tests for every registered action against its schema and permission.
- Loop-protection tests: self-triggering rule (action `add_tag` triggers `case.tag_added` rule that removes it) stops at depth 3 and suspends; two-rule ping-pong stops and suspends both.
- Ordering tests: `stopFurtherRules` prevents later rules; reorder is atomic.
- Idempotency: a retried `automation.execute` job does not duplicate notifications or tasks.
- Permission tests: a rule whose publisher lost `case.task:assign` is skipped and suspended.
- Isolation: an event from tenant A never evaluates tenant B's rules (cross-tenant test suite, [[TST-multi-tenant-isolation-tests]]).
- Dry run has no side effects (asserted by a spy on every action executor).

<!-- section:questions -->
## Open questions

- [ ] Should tenants be able to trigger rules from inbound integration events (for example a payment gateway callback or an MII status update) directly, or only from our normalised domain events? Proposed: domain events only. Owner: integrations group ([[INT-integration-framework]]).
- [ ] Is `set_field` on custom fields enough, or do tenants need to set core case fields (priority, assigned secretary)? Proposed: `assign_secretary` as a separate action with its own permission. Owner: product.
- [ ] Maker-checker for automation publishing: default on for all tenant types, or off for CORD tenants with fewer staff? Owner: product with [[PKG-separation-of-duties]].
- [ ] BullMQ per-tenant fairness relies on the open question in [[WF]] (BullMQ Pro groups or our own token bucket) [R2]. Owner: platform engineering.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Rule lookup, condition evaluation and actions all run inside the event's tenant transaction; rules, versions and executions are tenant-owned with forced RLS; job envelopes carry `tenantId` and the worker wrapper rejects missing or foreign-region context; the automation principal is a tenant-scoped service account and cannot hold platform permissions.

<!-- check:security -->
### Security of the API surface

Closed action catalogue with `procedural: false`; actions run as a principal whose permissions are the intersection of declared action permissions and the publisher's permissions, re-checked each run; recipients are roles or fact references, never literal addresses; outbound calls only to verified tenant webhook endpoints; expressions use the closed grammar without I/O; publishing can require maker-checker.

<!-- check:data-protection -->
### Personal data handling

Payloads hold IDs only; the execution log stores outcome codes, not message content or fact values; notes added by automation are tenant-internal; logs are kept 90 days by default and deleted by partition drop; case erasure removes executions for that case.

<!-- check:residency -->
### Region awareness

Queues run on the regional Redis and workers; rules and logs live in the regional database; webhooks go only to endpoints registered for that tenant, whose data-transfer policy is governed by [[INT-connector-data-policies]].

<!-- check:audit -->
### Audit events

Lifecycle actions emit `admin.automation.*` audit events; every action performed by a rule is audited by the downstream package with actor "automation principal" and the rule version, so case audit trails show which rule did what.

<!-- check:observability -->
### Observability

Metrics per tenant and rule: executions by outcome, latency, suspended rules, loop detections; trace context from the triggering request flows through `automation.evaluate` and `automation.execute`; the execution log is visible to tenant admins in the studio.

<!-- check:resilience -->
### Failure behaviour

Actions are idempotent by `{executionId}:{index}`; retryable failures are retried by BullMQ with backoff and done actions are skipped; tenant limits re-delay rather than drop; a Redis outage delays automation without affecting case processes, which do not depend on it.

<!-- check:change-safety -->
### Change and release safety

New actions and events are minor releases behind registry entries; action schema changes create new action kinds with upgraders that produce drafts; per-tenant enablement through `workflow.automation.allowed_actions` lets a new action roll out gradually.

<!-- check:testing -->
### Testing

Loop, ordering, idempotency, permission, dry-run no-side-effect and cross-tenant tests run in CI against real Redis and Postgres with RLS.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Service limits include steps per rule, items queued globally, daily processing time and loop detection after repeated self- or cross-triggered runs.",
    "id": "R1",
    "kind": "vendor",
    "title": "Atlassian Support: Automation service limits",
    "url": "https://support.atlassian.com/cloud-automation/docs/automation-service-limits/",
    "vendor": "Atlassian"
  },
  {
    "excerpt": "Queue-level rate limiting of job processing.",
    "id": "R2",
    "kind": "vendor",
    "title": "BullMQ docs: Rate limiting",
    "url": "https://docs.bullmq.io/guide/rate-limiting",
    "vendor": "Taskforce.sh"
  }
]
```

<!-- end -->
