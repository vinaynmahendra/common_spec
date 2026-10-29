---
id: "WF-entity-state-machines"
title: "Entity state machines"
parent: "WF"
order: 7
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "Code-defined status lifecycles for cases, documents and invoices, enforced on every change, shared by domains"
links: []
rev: 3
syncHash: "b527f7be28c03e3e"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 7.6 Entity state machines

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Code-defined status lifecycles for cases, documents and invoices, enforced on every change, shared by domains

<!-- section:purpose -->
## Purpose and scope

`packages/state-machines` defines entity lifecycles as code and is the only path through which any status column changes. A machine declares states, commands, allowed source states, guards and permissions; `transition()` executes a command inside the caller's tenant transaction: locks the row, checks version and state, runs guards, updates status, appends a status event, writes an audit event and an outbox event. The same definition generates documentation diagrams, UI "allowed actions" and exhaustive tests.

Machines defined by domains: case ([[DOM-cases#lifecycle]]), document version ([[DOM-documents#lifecycle]]), invoice, deposit and vendor bill ([[DOM-invoices-and-vendor-bills#lifecycle]]), appointment and empanelment ([[DOM-neutrals#lifecycle]]), hearing and session ([[DOM-hearings#lifecycle]]), transcription job and assignment ([[DOM-transcribers#lifecycle]]), bundle version.

**Does not do**: wait for time or people (Temporal), or decide rule-set values (the Rules and Decision Engine). Guards may use values that a caller loaded from a decision table.

**Relationship to tenant blueprints.** Tenants cannot add, rename or remove statuses. A case-type blueprint maps each of its **stages** onto one status of the code-defined case machine ([[WF-process-definition-model#entities]]) and may only invoke registered commands through `transition` steps. Many stages can share one status (for example `awaiting_response`, `document_production` and `hearing_preparation` all sit in `in_proceedings`), so tenants get procedural detail while status stays a small, reportable, code-guarded set. Tenants may relabel statuses for display through terminology overrides ([[PKG-tenant-terminology-and-copy]]) without changing the key.

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Use |
|---|---|
| Domain services in `packages/domain-*` | Call `transition()` from every command that changes status |
| Temporal activities | Call domain commands, which call `transition()`; idempotency key from workflow and activity |
| tRPC routers and public API | `allowedCommands()` to show or hide actions; errors mapped to problem types |
| Documentation | `toMermaid()` output embedded in domain nodes |
| Tests | `generateTransitionTests()` for every machine |
| Blueprint validator and studio ([[WF-process-definition-model]], [[WF-workflow-authoring-studio]]) | `describeMachine()` catalogue: legal stage-to-status mappings and `transition` steps |
| Case-process interpreter | `transition` steps call domain commands, which call `transition()` with idempotency key `{workflowId}:{stepId}:{attempt}` |

<!-- section:api -->
## Public API

```ts
export interface MachineDef<S extends string, C extends string, E, G> {
  entity: string;                       // 'case'
  table: string;                        // 'cases'
  statusColumn: string;                 // 'status'
  eventsTable: string;                  // 'case_status_events'
  states: readonly S[];
  terminal: readonly S[];
  commands: Record<C, {
    from: readonly S[] | '*';
    to: S | ((entity: E, input: unknown) => S);   // e.g. resume -> entity.resume_to
    permission: string;                           // checked with PKG policy engine
    guards?: Array<Guard<E, G>>;                  // pure: (entity, guardContext, input) => GuardResult
    requiresReason?: boolean;
  }>;
  loadGuardContext?: (tx: TenantPrisma, entity: E) => Promise<G>;   // e.g. counts of parties, fee status
  emits?: { event: string; payload: (entity: E, from: S, to: S) => Record<string, unknown> };
}

export function defineMachine<S extends string, C extends string, E, G>(def: MachineDef<S, C, E, G>): Machine<S, C, E, G>;

export function transition<S extends string, C extends string, E, G>(
  tx: TenantPrisma, machine: Machine<S, C, E, G>, entityId: string, command: C,
  input: { actor: Actor; idempotencyKey: string; expectedVersion?: number; reason?: string; data?: unknown;
           ruleSetVersion?: number; workflowId?: string },
): Promise<{ entity: E; from: S; to: S; eventId: string; replayed: boolean }>;

export function allowedCommands<S, C, E, G>(machine: Machine<S, C, E, G>, entity: E, actor: Actor, guardContext?: G): Array<{ command: C; allowed: boolean; reasons: GuardFailure[] }>;
export function toMermaid(machine: Machine<any, any, any, any>): string;
export function generateTransitionTests(machine: Machine<any, any, any, any>, fixtures: MachineFixtures): TestCase[];

export class TransitionRejected extends Error { code: 'INVALID_FROM_STATE' | 'GUARD_FAILED' | 'PERMISSION_DENIED' | 'REASON_REQUIRED'; failures: GuardFailure[] }
export class ConcurrentModification extends Error {}
```

**Execution inside `transition()`** (one transaction, the caller's):

1. `SELECT ... FROM {table} WHERE id = $1 FOR UPDATE` (RLS applies).
2. If a status event with `idempotency_key` exists, return it with `replayed: true`.
3. Check `expectedVersion`, source state, permission, reason, guards (with `loadGuardContext`).
4. `UPDATE {table} SET status = $to, version = version + 1 WHERE id = $1`.
5. `INSERT INTO {eventsTable} (...)`, audit event ([[PKG-audit-trail]]), outbox row with the `emits` event.

**Catalogue export for authoring** (added for the studio and blueprint validator):

```ts
export interface MachineCatalogue {
  entity: string; machineVersion: string;
  states: { key: string; terminal: boolean; labelKey: string }[];
  commands: { key: string; from: string[] | '*'; to: string | 'dynamic'; permission: string; requiresReason: boolean;
              guardIds: string[]; blueprintInvocable: boolean }[];   // false for commands only humans or domains may run
}
export function describeMachine(machine: Machine<any, any, any, any>): MachineCatalogue;
// Published per release as ref.workflow_registry (see WF-process-definition-model#seed);
// the blueprint validator rejects stage→status mappings and transition steps that the catalogue does not allow.
```

<!-- section:usage -->
## Usage examples

```ts
export const caseMachine = defineMachine({
  entity: 'case', table: 'cases', statusColumn: 'status', eventsTable: 'case_status_events',
  states: CASE_STATES, terminal: ['closed'],
  commands: {
    submit:   { from: ['draft'], to: 'submitted', permission: 'case.submit',
                guards: [hasClaimantAndRespondent /* CASE-BR-1 */, hasValidRuleSet /* CASE-BR-2 */, partiesHaveContact /* CASE-BR-3 */] },
    register: { from: ['in_scrutiny'], to: 'registered', permission: 'case.register',
                guards: [filingFeeSettled /* CASE-BR-4 */] },
    suspend:  { from: ['registered', 'awaiting_constitution', 'constituted', 'in_proceedings'], to: 'suspended',
                permission: 'case.suspend', requiresReason: true },
    resume:   { from: ['suspended'], to: (c) => c.resumeTo, permission: 'case.suspend' },
    // ...
  },
  loadGuardContext: (tx, c) => loadCaseGuardFacts(tx, c.id),
  emits: { event: 'case.status_changed', payload: (c, from, to) => ({ caseId: c.id, from, to }) },
});

// in the cases service
try {
  await transition(tx, caseMachine, caseId, 'register', { actor, idempotencyKey, expectedVersion });
} catch (e) {
  if (e instanceof TransitionRejected) throw problem('case-transition-rejected', e.failures); // APP-api-error-catalogue-problem
  throw e;
}
```

<!-- section:tenant -->
## Tenant context

`transition()` accepts only a `TenantPrisma` transaction created by the Prisma tenant extension ([[MT-prisma-client-extension-wraps]]); it cannot be called with the base client (type-level and runtime check that `app.tenant_id` is set). Row lock, status update, event, audit and outbox all happen in that one transaction, so they share the same tenant and either all commit or none. Guards that read other tables do so through the same transaction and therefore under RLS ([[MT-isolation-strategy]]).

<!-- section:config -->
## Configuration

No runtime configuration: machines are code, reviewed and versioned. Values that guards compare against (fee settled thresholds, required party counts per procedure) come from decision tables loaded in `loadGuardContext` with the version pinned on the entity. Adding a state or command is a code change with a migration of the CHECK constraint on the status column (expand: add value; contract: remove after no rows use it).

Tenant influence is limited to: which commands a blueprint invokes (only those with `blueprintInvocable: true`), the decision tables guards read, display labels, and the case-level settings in [[PKG-settings-cases-and-workflows]] (for example `case.procedure.suspension_stays_deadlines`). There is no setting that disables a guard.

<!-- section:errors -->
## Error model

| Error | HTTP / problem type | Retryable |
|---|---|---|
| `TransitionRejected(INVALID_FROM_STATE)` | 409 `transition-not-allowed` | No |
| `TransitionRejected(GUARD_FAILED)` | 422 with guard failures (rule IDs) | No |
| `TransitionRejected(PERMISSION_DENIED)` | 403 | No |
| `ConcurrentModification` | 409 `concurrent-modification` | Yes, after reload (UI) or retry (activity) |
| Database serialisation / deadlock | 503 | Yes |

<!-- section:nfr -->
## Performance and limits

`transition()` adds at most 3 statements beyond the caller's work (lock, update, event insert; audit and outbox are inserts in the same transaction): proposed p95 under 15 ms excluding guard context loading. Guard context loaders must be single queries or small batches.

<!-- section:versioning -->
## Versioning and compatibility

Machines are versioned with the domain package. Removing a state or command is a breaking change and requires that no rows are in that state (a migration check query) and no running workflow sends that command (search attribute query on Temporal). Each machine exports `MACHINE_VERSION`, recorded in status events. Adding a status widens the generated CHECK on `wf.stage_definition.case_status` in the same release; removing one is blocked while any blueprint version in any region maps a stage to it ([[WF-process-definition-model#migrations]]).

<!-- section:testing -->
## Test contract

`generateTransitionTests()` produces, for each machine: every allowed (from, command) pair succeeds with satisfied guards; every disallowed pair is rejected with `INVALID_FROM_STATE`; each guard failing alone rejects with its rule ID; idempotent replay returns `replayed: true`; concurrent transitions on the same row produce one success and one `ConcurrentModification`. Tests run against real Postgres with RLS. A CI check fails if a domain package writes a status column outside this package (ESLint rule plus a grep on raw SQL).

<!-- section:questions -->
## Open questions

- [ ] Defence in depth: add a database trigger that rejects status changes unless the transaction set `app.sm_transition = 'on'` (set by `transition()` with `set_config(..., true)`)? Protects against writes from migrations, scripts or a missed code path. Proposed: yes for cases, documents and invoices.
- [ ] Use XState v5 for definitions (gains visual tooling) or keep the small in-house definition (current proposal: in-house, with `toMermaid()`)?
- [ ] Should `allowedCommands()` evaluate guards that need database reads for every list row, or only on detail views? Proposed: detail views only.
- [ ] Which case commands are `blueprintInvocable`? Proposed: `start_scrutiny`, `register` (when the rule set allows automatic registration), `start_conciliation`, `refer_to_arbitration`, `begin_constitution`, `close_case`; never `issue_award`, `terminate` or `withdraw`, which need a human actor. Owner: product with legal.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Only callable with a tenant-scoped Prisma transaction; the row lock and every insert run under forced RLS. No platform mode exists. Idempotency keys are unique per tenant in each events table.

<!-- check:security -->
### Security of the API surface

Every command declares a permission checked through the policy engine ([[PKG-policy-engine-permission-matrix]]) inside `transition()`, so a caller cannot skip it. Deny by default: commands without a permission fail to compile (required field).

<!-- check:audit -->
### Audit events

Each transition writes a status event and an audit event in the same transaction as the change (actor, on-behalf-of, reason, rule-set version, machine version, workflow ID, request ID), so a status change cannot exist without its record.

<!-- check:resilience -->
### Failure behaviour

Idempotent on `idempotencyKey`: a retried Temporal activity or API request returns the original result. Optimistic version plus row lock prevent lost updates. No internal retries; callers (Temporal, UI) decide.

<!-- check:change-safety -->
### Change and release safety

Breaking machine changes are gated by a check that no rows are in a removed state and no running workflow uses a removed command; generated tests run for every consumer through the Turborepo affected graph.

<!-- check:testing -->
### Testing

Exhaustive generated transition tests, guard-isolation tests, idempotent replay and concurrency tests, all against Postgres with RLS; plus a CI rule against direct status writes.

<!-- end -->
