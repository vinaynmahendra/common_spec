---
id: "PKG-rules-and-decision-engine"
title: "Rules and Decision Engine"
parent: "PKG"
order: 6
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "Shared engine for configurable decisions (deadlines, fees, eligibility, routing): versioned, per-tenant decision tables with tests, gap analysis, locks, explanations and maker-checker publishing, invoked from Temporal as an Activity (see [[WF-separation-of-concerns-temporal]]); each decision table is its own child node"
links: []
rev: 4
syncHash: "37369448cd450f82"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.6 Rules and Decision Engine

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Shared engine for configurable decisions (deadlines, fees, eligibility, routing): versioned, per-tenant decision tables with tests, gap analysis, locks, explanations and maker-checker publishing, invoked from Temporal as an Activity (see [[WF-separation-of-concerns-temporal]]); each decision table is its own child node

<!-- section:purpose -->
## Purpose and scope

`@nomology/rules` evaluates configurable business decisions — deadlines, fees, eligibility, routing, reminders — from versioned decision tables that legal and operations teams can change per tenant without a code release. It is the decisions layer (≈ DMN) in [[WF-separation-of-concerns-temporal]]: workflows call it as an Activity (`evaluateDecision`) with the decision version pinned at workflow start; request paths (for example a fee quote in the filing wizard) can call it synchronously.

Each decision table that matters to a domain gets its own child node (for example "Hearing reminder policy", "Filing fee schedule", "Neutral appointment routing"); none exist yet in the tree.

**Does not:** sequence steps (process definitions belong to [[PKG-workflow-templates]]); do date arithmetic itself (it calls [[PKG-calendars-and-deadline]] through built-in functions); perform side effects (decisions are pure; acting on them is the caller's job).

**Administration** (requirement prefix `RUL-FR-`):

- **RUL-FR-1** Decision tables are authored in the tenant admin console at `/admin/workflows/rules` (table editor with typed columns, row annotations, test cases and a gap and overlap report) and through `/admin/v1/rules/decisions`; the studio links to them from blueprint steps ([[WF-workflow-authoring-studio]]).
- **RUL-FR-2** Lifecycle follows [[PKG-configuration-lifecycle]] (`draft` → `in_review` → `approved` → `published` → `superseded`); publishing needs `rules.decision_table:publish`, a different approver from the author ([[PKG-separation-of-duties]]) and step-up MFA.
- **RUL-FR-3** A table may be **locked** at `platform` or `offering` scope (for example SEBI ODR timelines); tenants can view and test a locked table but not change it, and the editor shows the lock source.
- **RUL-FR-4** A table may declare `unit` as an input fact so one table serves unit-specific values; there is no separate unit-scope copy.
- **RUL-FR-5** Every table declares a `classification`: `procedural` (deadlines, eligibility, tribunal size, fees owed by parties) or `operational` (routing, reminders, internal targets). Changes to procedural tables make the depending blueprint change class `procedural` ([[WF-workflow-versioning#design]]).
- **RUL-FR-6** `explain` returns, for any evaluation, the matched rule IDs with annotations and the fact values compared, in plain language for case managers.
- **RUL-FR-7** The admin copilot may propose table rows or test cases as a draft with a diff; it cannot submit or publish ([[APP-admin-copilot]]).

Vocabulary (decision table, hit policy, input and output columns) follows DMN [R1]; we do not import or export DMN XML at launch.

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Decision (example) | Called from |
|---|---|---|
| Hearing reminder workflow | `hearing-reminder-policy` → `{ reminderDays, confirmWithinHours }` | Temporal Activity |
| Filing wizard | `filing-fee` → `{ amountMinor, currency, taxCode }` from claim value, case type, party type | Server Action (synchronous) |
| Case intake (SEBI ODR tenant) | `odr-eligibility` → `{ eligible, reasonCode }` from complaint category, amount, time since grievance | Temporal Activity at intake |
| Neutral appointment | `appointment-routing` → `{ method: 'list' | 'direct' | 'rotation', panelSize }` | Temporal Activity |
| Deadline computation | `response-deadline` → `{ duration: { value: 30, unit: 'calendar_days' }, calendar: 'seat' }` then calendars computes the date | Temporal Activity |
| Escalation | `sla-escalation` → `{ escalateTo: 'secretariat_lead', afterHours }` | [[WF-human-tasks]] |

<!-- section:api -->
## Public API

```ts
// packages/rules/src/index.ts (server-only; pure evaluation, no I/O except loading the table)
export type HitPolicy = 'FIRST' | 'UNIQUE' | 'COLLECT' | 'PRIORITY';

export interface DecisionTable {
  decision: string;                    // e.g. 'hearing-reminder-policy'
  version: number;                     // immutable once published
  inputs: Record<string, FactType>;    // typed facts: 'string' | 'number' | 'money' | 'date' | 'enum:<...>' | 'boolean'
  outputs: Record<string, FactType>;
  hitPolicy: HitPolicy;
  classification: 'procedural' | 'operational';
  lockedBy?: 'platform' | 'offering';
  rules: { id: string; when: Record<string, Condition>; then: Record<string, OutputExpr>; annotation?: string }[];
}
export type Condition = { eq: unknown } | { in: unknown[] } | { lt: number } | { lte: number } | { gt: number }
  | { gte: number } | { between: [number, number] } | { any: true };
export type OutputExpr = unknown | { fn: BuiltinFn; args: unknown[] };   // built-ins only: add, multiply, min, max, round, percentOf, lookup

export interface EvaluateRequest { decision: string; version: number | 'published'; facts: Record<string, unknown> }
export interface EvaluateResult {
  outputs: Record<string, unknown> | Record<string, unknown>[];   // COLLECT returns a list
  matchedRuleIds: string[];
  decisionVersionId: string;           // uuid of the exact version evaluated
  inputHash: string;                   // sha256 of canonical facts, for audit and reproducibility
}

export function evaluate(tx: TenantTx, req: EvaluateRequest): Promise<EvaluateResult>;
export function resolvePublishedVersion(tx: TenantTx, decision: string): Promise<number>;  // call at workflow start, then pin

/** Temporal Activity wrapper (registered on regional workers) */
export async function evaluateDecision(req: EvaluateRequest & { version: number }): Promise<EvaluateResult>;

/** Authoring (tenant admin console /admin/workflows/rules; permissions rules.decision_table:update, rules.decision_table:approve, rules.decision_table:publish) */
export function saveDraft(tx: TenantTx, table: Omit<DecisionTable, 'version'>): Promise<{ draftId: string; validation: ValidationReport }>;
export function test(tx: TenantTx, draftId: string, cases: { facts: Record<string, unknown>; expect: Record<string, unknown> }[]): Promise<TestReport>;
export function submitForReview(tx: TenantTx, draftId: string): Promise<void>;
export function publish(tx: TenantTx, draftId: string, opts: { reason: string; effectiveFrom?: Date }): Promise<{ version: number }>;  // maker-checker: publisher ≠ author
export function retire(tx: TenantTx, decision: string, version: number): Promise<void>;
export function approve(tx: TenantTx, draftId: string, opts: { comment?: string }): Promise<void>;          // approver != author
export function explain(tx: TenantTx, result: EvaluateResult, facts: Record<string, unknown>, locale: string): Promise<Explanation>;
export function analyse(tx: TenantTx, draftId: string): Promise<{ gaps: FactRegion[]; overlaps: { ruleIds: string[] }[]; unreachableRules: string[] }>;
export function usages(tx: TenantTx, decision: string): Promise<{ blueprintVersionId: string; caseTypeKey: string; stepId: string }[]>;  // impact before change

export class DecisionNotFoundError extends Error {}
export class NoRuleMatchedError extends Error {}           // only for UNIQUE/FIRST without a default rule
export class AmbiguousMatchError extends Error {}          // UNIQUE with >1 match
export class FactValidationError extends Error {}
```

<!-- section:usage -->
## Usage examples

```ts
// Workflow start (layer 5): pin the version
const v = await withTenant((tx) => rules.resolvePublishedVersion(tx, 'hearing-reminder-policy'));
await temporal.workflow.start(hearingReminder, { args: [{ hearingId, hearingAt, facts, policyVersion: v }], ... });

// Inside the workflow (layer 1) the Activity is called with the pinned version; see WF-separation-of-concerns-temporal#examples
```

```ts
// Synchronous fee quote in a Server Action
const { outputs, decisionVersionId } = await withTenant((tx) => rules.evaluate(tx, {
  decision: 'filing-fee', version: 'published',
  facts: { caseType: 'ARB_INSTITUTIONAL', claimValueMinor: 25_000_000_00, currency: 'INR', claimantType: 'company' },
}));
// store decisionVersionId with the invoice line so the fee can be reproduced later
```

<!-- section:tenant -->
## Tenant context

- Decision tables are tenant-owned (`rules.decision_definition`, `rules.decision_version` with forced RLS). Platform templates (`ref.rule_set_template`, [[PKG-reference-and-seed-data]]) are cloned into a tenant when it enables a case type; after that, the tenant's copy evolves independently.
- `evaluate` loads the table inside `withTenant`; a tenant can only evaluate its own tables. The Temporal Activity gets tenant context from the interceptor; the decision version ID is checked to belong to that tenant.
- Facts are passed in by the caller and validated against the table's input types; the engine never reads other tenant data by itself.
- Evaluation results that drive legally significant outcomes (deadlines, fees, eligibility) are stored by the caller with `decisionVersionId` and `inputHash`, and audited, so the institution can show which rule produced an outcome.

<!-- section:config -->
## Configuration

| Setting | Default (proposed) |
|---|---|
| Max rules per table | 500 |
| Max inputs / outputs | 20 / 20 |
| Compiled table cache | In process, keyed by `decisionVersionId` (immutable, so no invalidation needed), LRU 1,000 entries |
| Publish approval | Maker-checker: author cannot approve; publisher needs `rules.decision_table:publish` (secretariat lead or tenant admin per tenant policy) and step-up; procedural tables follow `workflow.publish.procedural_change_approvers` ([[PKG-settings-cases-and-workflows]]) |
| Lock | `lockedBy` set only by Nomology for offering-level regulator tables |
| Effective-from scheduling | Optional; `published` resolves to the latest version whose `effective_from ≤ now()` |

<!-- section:adapters -->
## Providers and extension points

The evaluator is behind an `Evaluator` interface so the open question (in-house JSON evaluator vs GoRules Zen vs a FEEL / DMN interpreter, raised in [[WF-separation-of-concerns-temporal#questions]]) can be decided without changing consumers. The table JSON format above is ours; if a third-party engine is chosen, a compiler translates it. Built-in functions are a closed list; there is no user-defined code or general expression language at launch.

<!-- section:errors -->
## Error model

| Error | Retryable | Caller action |
|---|---|---|
| `FactValidationError` | No | Bug in caller or missing data; workflow should fail the step to a human task |
| `NoRuleMatchedError`, `AmbiguousMatchError` | No | Configuration error; human task to secretariat; alert tenant admin. Publishing validation tries to prevent these (gap and overlap analysis) |
| `DecisionNotFoundError` | No | Configuration missing for tenant |
| `DbUnavailableError` | Yes (Temporal retry) | — |

<!-- section:nfr -->
## Performance and limits

Evaluation of a compiled table with ≤ 500 rules: p99 ≤ 1 ms; load and compile on cache miss ≤ 20 ms. Publishing runs validation (types, gaps, overlaps for UNIQUE) in ≤ 2 s.

<!-- section:versioning -->
## Versioning and compatibility

Two kinds: package semver for the API; decision table versions per tenant, immutable once published, never deleted while any running workflow or stored outcome references them (retire hides them from `published` but keeps them evaluable).

<!-- section:testing -->
## Test contract

- Golden tests per decision table: authors attach test cases; publish is blocked unless all pass.
- Hit-policy semantics tests (FIRST, UNIQUE, COLLECT, PRIORITY) with property-based fact generation.
- Determinism: same version and facts → identical output and `inputHash` across runs and regions.
- Isolation: tenant B cannot evaluate tenant A's version ID.
- Replay: a workflow started on version 4 keeps using version 4 after version 5 is published.

<!-- section:questions -->
## Open questions

- [ ] Evaluator choice: in-house JSON evaluator vs GoRules Zen vs FEEL / DMN interpreter (carried from [[WF-separation-of-concerns-temporal#questions]]). Owner: platform engineering lead; record as an ADR.
- [ ] Who may publish decision tables in each tenant type? Proposed defaults via permission sets ([[PKG-roles-and-permission-sets]]): institution legal lead approves procedural tables, secretariat lead approves operational ones; Nomology implementation team only for offering-locked tables. Owner: product.
- [ ] Are there decisions where a regulator or institution rule fixes the outcome, so tenants must not edit them (locked tables)? Legal to identify per tenant type; assumption: SEBI ODR timelines are fixed by the applicable circulars and must be locked tables.
- [ ] Create child nodes for the first decision tables (hearing reminder policy, filing fee, response deadline, ODR eligibility).
- [ ] DMN import and export for institutions that already keep rules in DMN tools: needed? Owner: product.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Tables and versions are tenant-owned with forced RLS; evaluation runs inside `withTenant`; the Activity checks that the pinned version ID belongs to the context tenant. Platform templates are cloned, not shared, so a tenant change cannot affect another tenant.

<!-- check:audit -->
### Audit events

Publish, retire and review actions are audited (author, approver, reason, diff summary). Evaluations that drive deadlines, fees or eligibility are recorded by the caller with `decisionVersionId` and `inputHash` in the domain record and audit event, so outcomes are reproducible. Approval is a separate audited step (`admin.rules.approved`), and `usages` lets reviewers see which blueprints a change affects.

<!-- check:resilience -->
### Failure behaviour

Evaluation is pure and deterministic, so the Activity is safe to retry any number of times; versions are immutable, so retries always see the same table. The package never calls external services.

<!-- check:change-safety -->
### Change and release safety

Tenant rule changes are versioned and pinned per workflow, so publishing never disturbs running cases. Publishing requires passing golden tests and maker-checker. Engine changes are tested against every published table in a region using their attached test cases before release.

<!-- check:testing -->
### Testing

Golden tests per table block publish; hit-policy property tests; determinism and replay tests; isolation tests against real Postgres with RLS.

<!-- citations -->
## Citations

```json
[
  {
    "body": "Object Management Group",
    "excerpt": "Decision tables with hit policies; vocabulary reference only.",
    "id": "R1",
    "ident": "DMN",
    "kind": "standard",
    "title": "Decision Model and Notation (DMN)",
    "url": "https://www.omg.org/spec/DMN/"
  }
]
```

<!-- end -->
