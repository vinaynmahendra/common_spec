---
id: "WF-workflow-versioning"
title: "Workflow versioning, publishing and in-flight migration"
parent: "WF"
order: 14
type: "capability"
template: "design"
status: "draft"
owner: null
indicative: false
summary: "How blueprint versions are reviewed, published and pinned, how interpreter code is versioned in Temporal, and how running cases are migrated to a newer blueprint version with mapping, dry run, legal basis and approval"
links: []
rev: 3
syncHash: "70e56b6c05991af2"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T09:00:00Z"
updatedBy: null
---

# 7.13 Workflow versioning, publishing and in-flight migration

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> How blueprint versions are reviewed, published and pinned, how interpreter code is versioned in Temporal, and how running cases are migrated to a newer blueprint version with mapping, dry run, legal basis and approval

<!-- section:context -->
## Context and scope

Tenants author case-type blueprints as configuration ([[WF-process-definition-model]]); Nomology engineers write the generic Temporal interpreter that runs them ([[WF-separation-of-concerns-temporal]], [[PKG-workflow-templates]]). Two things therefore change independently and at different speeds:

| What changes | Who changes it | How often | Versioned by |
|---|---|---|---|
| Blueprint content (stages, steps, forms, decision tables, templates, SLA policies) | Tenant `workflow_designer`, approved by a second person | Weekly to yearly per case type | Immutable blueprint versions in `wf.blueprint_version`, lifecycle from [[PKG-configuration-lifecycle]] |
| Interpreter and activity code | Nomology platform engineering | Every release | Temporal Worker Versioning plus `patched()` [R1][R2] |

Facts that constrain the design:

- Cases run for months or years. A procedural rule that applied when a case started must keep applying unless there is a legal basis to change it (shared model rule 5: values that affect procedural fairness are pinned).
- Institutions do sometimes need to move running cases: a rules revision with transitional provisions, a fixed defect in a notification, a renamed stage, a regulator circular that applies to pending matters.
- The approved decision [[ADR-workflow-engine]] fixes the mechanism split (Temporal, state machines, BullMQ); this note does not revisit it.
- Temporal's Worker Versioning offers two behaviours: **Pinned** workflows complete on one worker deployment version, and **Auto-Upgrade** workflows move to the current version and must stay replay-safe through patching [R1]. Pinned behaviour is inherited across Continue-As-New only within the same worker deployment [R1].

This note covers: blueprint version states and publishing, change classification, what running cases see, interpreter code versioning, and in-flight migration of running cases to a newer blueprint version. Requirements use the prefix `WFV-FR-`.

<!-- section:goals -->
## Goals and non-goals

**Goals**

1. A published change never alters a running case unless someone with `workflow.migration:approve` approves a migration with a recorded legal basis (WFV-FR-1).
2. New cases pick up a newly published version from its `effective_from` instant, without a deploy (WFV-FR-2).
3. Interpreter code can be released every week without breaking any running case, proven by replay tests against recorded histories from every region (WFV-FR-3).
4. A migration of up to 10,000 running cases completes within 4 hours per region without breaching interactive Temporal SLOs in [[WF]] (WFV-FR-4).
5. Every version and every migration is reproducible and explainable: who, when, why, what diff, which simulation evidence (WFV-FR-5).
6. Rolling back a bad publication takes one approved action and affects new cases within one minute (WFV-FR-6).

**Non-goals**

- Arbitrary "edit the running case's process" by administrators. Ad hoc changes to one case go through case-level commands (extend deadline by order, reassign task, skip stage with reason) under [[PKG-settings-cases-and-workflows]] case-overridable settings, not through migration.
- Migrating between different case types (for example converting conciliation into arbitration). That is a domain command (`refer_to_arbitration`) that starts a new process on the target case type.
- Pinning interpreter code builds for the life of a case. Multi-year pinning to old worker builds is not operable; see Alternatives.

<!-- section:design -->
## Design

#### 1. Two version axes

```
Blueprint content (data)          Interpreter code (Nomology)
v1 ── v2 ── v3 (published)        build 2026.10.1 ── 2026.10.2 (current)
 │      │                          │
 └ cases pinned by data            └ case-process workflows are Auto-Upgrade:
   (wf.case_process.                 replay-safe through patched(); stage
    blueprint_version_id)            boundaries Continue-As-New
```

- **Content** is pinned by data: the interpreter receives `blueprintVersionId` and the locked component list as workflow input, loads the body once through an activity, and never re-reads "latest". This is the existing guardrail "definitions are loaded once at start" in [[WF-separation-of-concerns-temporal#guardrails]].
- **Code** uses Temporal Worker Versioning with the worker deployment `wf-interpreter-{region}`. Case-process workflows use the **Auto-Upgrade** behaviour, and every change to workflow code that alters the command sequence is wrapped in `patched('<change-id>')` with replay tests [R1][R2]. Short-lived code workflows (pipelines in [[WF-long-running-pipelines]], migration batches) use **Pinned** behaviour, because they finish within days and can drain on the old build.
- The interpreter exposes an **interpreter contract** (`interp/<major>.<minor>`). A blueprint declares the minimum contract it needs (`wf.blueprint_version.interpreter_contract`). A minor contract bump adds step types or options; a major bump means some blueprint construct changes meaning and requires a blueprint `schemaVersion` upgrade (see section 6).

#### 2. Blueprint version lifecycle

States come from the shared model ([[PKG-configuration-lifecycle]]): `draft` → `in_review` → `approved` → `published` → `superseded`, plus `retired`.

| Transition | Who (permission) | Gate |
|---|---|---|
| Save draft | `workflow.definition:update` | Schema validation (errors allowed in drafts) |
| Submit for review | Author with `workflow.definition:update` | Zero validation errors; required simulation scenarios pass ([[WF-workflow-simulation]]); change class computed |
| Approve | `workflow.definition:approve`, not the author ([[PKG-separation-of-duties]]) | Reviewer has opened the diff; for change class `procedural` a second approver with `legal` attribute is required when `workflow.publish.procedural_change_approvers = 2` |
| Publish | `workflow.definition:publish` with step-up MFA | Approved; `effective_from` in the future or now; no newer version scheduled; component lock written; `content_sha256` set |
| Supersede | System | When a later version becomes current |
| Retire | `workflow.definition:publish` | No new cases; existing pinned cases continue |
| Roll back | `workflow.definition:publish` with approval | Publishes a copy of an earlier version as a new version number with reason `rollback of vN` |

**WFV-FR-2** On publish with `effective_from = T`, `wf.case_type.current_version_id` switches at T (a Temporal Schedule per region fires `activateScheduledVersions` every minute); cases created before T pin the previous version, cases created at or after T pin the new one.

Audit events: `admin.workflow.draft_saved`, `admin.workflow.submitted`, `admin.workflow.approved`, `admin.workflow.rejected`, `admin.workflow.published`, `admin.workflow.retired`, `admin.workflow.rolled_back`.

#### 3. Change classification (computed by a semantic diff)

| Class | Examples | Running cases | New cases |
|---|---|---|---|
| `cosmetic` | Label or help text, stage display name, notification copy fix, document template typo | Unchanged by default; content components may follow latest if `workflow.versioning.content_follows_latest = true` for that component kind | New version |
| `additive` | New optional task, new notification at an existing step, new non-blocking AI suggestion step | Unchanged; may be migrated with a trivial mapping | New version |
| `structural` | New, removed or reordered stage; changed gateway conditions; new mandatory task | Unchanged; migration needs an explicit mapping | New version |
| `procedural` | Any change to a procedural timer, a decision table that yields deadlines, fees or eligibility, a locked component, the parties' filing obligations | Unchanged; migration requires `legal_basis` and two approvals | New version |

The diff runs over the canonical JSON and the component lock and shows, per element, `added`, `removed`, `changed` with before and after. The highest class wins.

**WFV-FR-7** If a change touches a component that is locked at `platform` or `offering` scope (for example SEBI ODR timelines), publish is refused with the lock source shown; only the scope owner can publish that component.

#### 4. What a running case sees

| Item | Running case behaviour |
|---|---|
| Stages, steps, gateways, timers, task templates | Pinned version |
| Decision tables | Version pinned in the component lock |
| Forms | Pinned; a party already mid-way through a draft keeps that form version |
| Notification and document templates | Pinned, unless the component row has `content_follows_latest = true` (only allowed for `cosmetic`-class changes to these kinds) |
| SLA policies | Pinned (service-level clocks keep their target); new clocks created after a migration use the target version's policy |
| Automation rules | Not pinned; rules are tenant-wide and apply to running cases ([[WF-automation-rules]]), because their action catalogue excludes procedural effects |
| Settings marked "applies to running cases" | Live, per [[PKG-configuration-scope-hierarchy]] |
| Business schedules and holiday calendars | Live for service-level timers; procedural deadlines already computed are not moved when a calendar changes ([[PKG-calendars-and-deadline#config]]) |

#### 5. In-flight migration

A **migration plan** moves a selected set of running cases from version A to version B of the same case type.

```mermaid
sequenceDiagram
  participant D as Workflow designer
  participant S as Studio / admin API
  participant M as Migration service
  participant T as Temporal (blueprintMigration)
  participant C as caseProcess workflow
  D->>S: create plan (A→B, mapping, policies, selection, legal basis)
  S->>M: validate mapping against both versions
  M->>M: dry run per case (pure simulator on current state)
  M-->>S: dry-run report (per case: migratable, changes, warnings)
  D->>S: submit for approval
  Note over S: approver ≠ author; procedural plans need 2 approvers
  S->>T: start blueprintMigration-{planId}
  loop batches of 100, rate-limited per tenant
    T->>C: Update migrateBlueprint(planId, mapping)
    C->>C: validator: quiescent? mapping covers active steps?
    C-->>T: accepted / rejected(reason)
    C->>C: apply at next safe point, write stage event 'migrated'
  end
  T-->>S: completion report
```

**Plan contents** (`wf.migration_plan`):

| Field | Meaning |
|---|---|
| `from_version_id`, `to_version_id` | Same case type; B must be `published` |
| `mapping` | For every step that can be active in A: target step in B of the same element type, or `cancel`; for every stage: target stage. Auto-proposed by matching `step_id`; author confirms |
| `timer_policy` | `keep_computed` (default: running procedural deadlines keep their due date), `recompute_not_started` (timers not yet started use B's rules), `recompute_all` (allowed only for `service_level` and `reminder` timers, never for procedural deadlines unless `legal_basis` cites an order or transitional provision) |
| `task_policy` | `keep_open` (default; open tasks continue, re-linked to B's task template if mapped), `cancel_and_recreate` |
| `selection` | Filter (stage, unit, created date range, explicit case list); max 10,000 cases per plan |
| `legal_basis` | Required for `structural` and `procedural`: text plus reference (for example "Rules 2027, Art. 45 transitional provision", "Procedural order PO-3 in case X") |
| `notify_participants` | Whether parties get a notice of the change (required true when any party-facing deadline or obligation changes) |

**WFV-FR-8 (quiescence)** The `migrateBlueprint` Update validator accepts only when the case process is waiting on a timer, a signal or a human task (never while an activity is executing) and every active step has a mapping. Rejected cases are recorded as `skipped` with the reason and can be retried.

**WFV-FR-9 (application)** On acceptance the interpreter: records the old and new version; re-keys active steps by the mapping; applies the timer and task policies (via activities that update `case_deadlines`, `human_tasks` and `wf.sla_clock` idempotently); writes a `migrated` stage event and audit event `workflow.case_migrated`; updates `wf.case_process.blueprint_version_id` and `migrated_from_version_id` under the migration trigger; and calls `continueAsNew` with the new input so the history starts clean on B.

**WFV-FR-10 (dry run)** The dry run uses the same pure interpreter core as simulation ([[WF-workflow-simulation]]) against each case's current state and reports: target stage, active steps after migration, deadlines that would change (with old and new dates), tasks cancelled or created, notifications that would be sent. Execution is refused if the report is older than 24 hours or if any case changed stage since the dry run (that case is re-dry-run in the batch).

**WFV-FR-11 (reversal)** A completed plan can be reversed by an auto-generated inverse plan only for cases where no step that exists only in B has completed since migration; others are listed for manual handling.

Approval and execution permissions: `workflow.migration:create` (designer), `workflow.migration:approve` (not the author; two approvers for `procedural`), `workflow.migration:publish` (may be the approver). Audit: `admin.workflow.migration_planned`, `admin.workflow.migration_approved`, `admin.workflow.migration_executed`, `admin.workflow.migration_reversed`.

#### 6. Schema and contract upgrades (Nomology-initiated)

When the interpreter contract has a major bump, Nomology ships an **upgrader** that converts blueprint bodies from `schemaVersion n` to `n+1`. Drafts are upgraded in place; published versions are upgraded into new drafts, which go through each tenant's own approval (AI-proposed changes and platform-proposed changes are drafts, never auto-published). Running cases on old contracts keep running because the interpreter supports the previous major contract for at least 24 months (proposed). Old contract behaviour is selected inside the pure core by the blueprint's declared contract version, not by `patched()`; `patched()` is used only for short-lived replay safety of in-flight histories, which roll over at each stage and monthly (proposed in [[ADR-workflow-interpreter-versioning]]).

#### 7. Interpreter core

The interpreter is split into a **pure core** (`reduce(state, event) → { state, commands }`, no I/O, deterministic) and a thin Temporal shell that turns commands into activities, timers and child workflows. The same core runs in the simulator and in migration dry runs, so what the designer tests is what runs. Replay tests run the shell against recorded histories (sampled from each region's staging and anonymised production exports) on every pull request touching `packages/workflow-templates/interpreter/**`.

<!-- section:examples -->
## Worked examples

#### A. Notification typo fix (cosmetic)

A tenant fixes a typo in the "Notice of arbitration served" email. The notification template's new version is published; the blueprint diff is `cosmetic`. Because `workflow.versioning.content_follows_latest.notification_template = true` for this tenant, the designer ticks "running cases use the corrected copy"; the component row is marked `content_follows_latest`, and running cases render the latest published version of that template from now on. No migration plan is needed. Audit records the choice.

#### B. Institutional rules revision (procedural, with transitional provision)

An arbitral institution's new rules take effect on 1 January. The designer creates v8 of "Institutional arbitration" with a new emergency-arbitrator stage and a changed response deadline (decision table `response-deadline` v4 → v5). The diff is `procedural`.

1. v8 is approved by two approvers and published with `effective_from = 2027-01-01T00:00+08:00`; cases filed from that instant pin v8.
2. The rules say pending cases continue under the old rules except Article 45, which applies to all cases where the tribunal is not yet constituted. The designer creates a migration plan v7 → v8, selection "stage in (`scrutiny`, `awaiting_constitution`)", `timer_policy = keep_computed`, legal basis "Rules 2027 Art. 45".
3. Dry run: 412 cases, 405 migratable, 7 skipped (an activity running); 0 procedural deadlines change because of `keep_computed`.
4. Execution in batches of 100; skipped cases retried automatically after 10 minutes; all 412 migrated within 25 minutes.

#### C. Interpreter code change

Engineers add support for `n_of_m` joins. The new code path is wrapped in `patched('join-n-of-m')`; replay tests pass against recorded histories; the new worker build is ramped to 10% of Auto-Upgrade workflows, then 100% [R1]. Blueprints can use `n_of_m` only once the region reports the new build as current; the studio reads the region's supported contract (`interp/2.4`) to enable the option.

#### D. Bad publication

v5 of "CORD consumer mediation" sends reminders to the wrong role. Ten minutes after publication the designer rolls back: v6 (a copy of v4) is published after approval. Cases created in those ten minutes stay on v5; the studio lists them, and the designer runs a migration v5 → v6 with the trivial auto-mapping.

<!-- section:alternatives -->
## Alternatives considered

| Option | Trade-off | Outcome |
|---|---|---|
| Always run the latest published blueprint for all cases | Simple; breaks procedural fairness and makes past behaviour irreproducible | Rejected |
| Pin case-process workflows to the worker build they started on (Temporal Pinned behaviour for the life of the case) | Strong code isolation; requires running old builds for years in every region, with old security patches | Rejected for case processes; used for short-lived workflows only |
| Per-case "edit the process" by administrators | Flexible; every case becomes its own process; unreportable and untestable | Rejected; case-level commands cover legitimate one-off needs |
| Migration that rewrites running Temporal history | Not supported by Temporal; would break determinism | Rejected; we apply migration as an Update then Continue-As-New |
| BPMN-engine style instance migration with element mapping | Proven pattern: map each active element to a target element of the same type, validate, migrate transactionally [R3] | Pattern borrowed for the mapping rules (same element type, every active element mapped, all-or-nothing per case) |
| Disable flow and let in-progress runs finish | Common in low-code tools, where turning a flow off lets running instances finish while no new ones start [R4] | Pattern borrowed for `retire` |

<!-- section:crosscutting -->
## Cross-cutting concerns

- **Tenancy**: plans, items and versions are tenant-owned under forced RLS ([[WF-process-definition-model#tenancy]]). The migration workflow ID is `{tenantId}-migration-{planId}`; it only sends Updates to workflow IDs with the same tenant prefix (client wrapper check).
- **Fairness and capacity**: migration batches run on the `cases-bulk` task queue with a per-tenant limit (setting `workflow.migration.batch_size`, default 100, and `workflow.migration.max_rate_per_min`, default 300 cases) so interactive `cases` queue latency stays within [[WF]] SLOs.
- **Security**: publish and migration approval require step-up MFA ([[PKG-mfa-session-management-device]]); the admin copilot may draft a version or a migration plan but cannot submit, approve, publish or execute ([[APP-admin-copilot]], shared model AI principle 3).
- **Privacy**: dry-run reports contain case IDs, references and dates, not party names; they are stored encrypted in-region and expire after 30 days.
- **Audit**: all lifecycle and migration events go to [[PKG-audit-trail]]; parties receive notices where `notify_participants` is true, generated by the notification template `case.procedure_changed`.
- **Observability**: metrics `wf_blueprint_publish_total{class}`, `wf_migration_cases_total{outcome}`, `wf_migration_duration_seconds`; search attribute `blueprintVersion` on case-process workflows so operators can count running cases per version.
- **Cost**: migration adds one Update and one Continue-As-New per case; negligible against case history volume.

<!-- section:guardrails -->
## Guardrails

- Never read "latest published" from inside a running case process; resolve versions only at case creation, at migration, and for components marked `content_follows_latest`.
- Every interpreter change that alters the command sequence goes behind `patched()`; removing a patch follows `deprecatePatch()` and only after the visibility query shows no open workflow started before the patch [R2].
- Never recompute a running procedural deadline in a migration without a recorded legal basis; never shorten one without a tribunal or institution order reference.
- Migrations apply only at quiescent points through the `migrateBlueprint` Update; never terminate and restart a case workflow to migrate it.
- A migration plan is all-or-nothing per case; partial application of a mapping inside one case is a bug.
- The simulator and the interpreter share one pure core; a feature that exists only in one of them must not ship.
- Locked components can only be changed by their lock scope owner.

<!-- section:ownership -->
## Ownership

| Part | Owner | Changed through |
|---|---|---|
| Blueprint lifecycle and diff | Workflow squad (platform engineering) | PR to `packages/workflow-templates`, `packages/config-core` |
| Interpreter core and shell, contract versions | Workflow squad | PR, replay tests, Worker Versioning ramp |
| Migration service and workflow | Workflow squad | PR |
| Blueprints and migration plans per tenant | Tenant `workflow_designer` with approvers | Studio or `/admin/v1/workflows/...` |
| Locked regulator-driven components | Nomology implementation team with legal (offering scope) | Platform admin console, `/platform/v1/blueprints/...` |
| Worker deployments per region | DevOps | IaC, [[INF-temporal]] |

<!-- section:questions -->
## Open questions

- [ ] Minimum support window for an old interpreter major contract: proposed 24 months, or tied to the longest case duration per tenant type. Owner: CTO (see [[ADR-workflow-interpreter-versioning]]).
- [ ] Should `content_follows_latest` be allowed for document templates that produce legal documents (procedural orders, awards)? Proposed: no, only for notification templates and non-legal documents. Owner: legal.
- [ ] Do parties need to consent to, or be able to object to, a migration that changes their obligations, or is notice enough? Assumption: notice is enough where the institution's rules allow; to be confirmed by legal per tenant type. Owner: legal.
- [ ] Two-approver rule for procedural changes: default on for SEBI ODR and court tenants, off for CORD tenants? Owner: product.
- [ ] ADR follow-up: [[ADR-workflow-engine]] is approved and is not edited here. Its revisit trigger "interpreter plus rules engine proves too limited" should be checked after the first three tenants' blueprints are live; this note adds the interpreter contract and Auto-Upgrade choice, which may merit a separate ADR ("Interpreter versioning strategy"). Owner: CTO.

<!-- checks -->
## Template checks

<!-- check:security -->
### Security and privacy

New surface: migration Updates to running workflows and bulk changes to many cases. Mitigations: Updates are sent only by the migration workflow with a tenant-prefix check; the Update validator re-checks plan approval and quiescence; publish and approval need step-up MFA and maker-checker ([[PKG-separation-of-duties]]); copilot can draft only. Personal data is not added: dry-run reports carry IDs and dates.

<!-- check:tenancy -->
### Tenancy

Versions, plans and items are tenant-owned with forced RLS; migration workflow IDs are tenant-prefixed and may only address same-tenant case workflows; per-tenant rate limits on `cases-bulk` stop one tenant's migration from delaying another's interactive work.

<!-- check:residency -->
### Data residency and lifecycle

Each region runs its own `wf-interpreter-{region}` deployment and migration workflows; plans and dry-run reports are stored in-region; replay-test histories are taken from the same region's staging or anonymised exports and are not moved across regions.

<!-- check:failure -->
### Failure handling and recovery

Migration is per case and all-or-nothing; a case not quiescent is skipped and retried; activity failures during application are retried idempotently (keys `{planId}:{caseId}:{step}`); a failed case stays on version A with a `failed` item and an alert. Interpreter code failures are caught by replay tests before release and by the ramp before full rollout [R1].

<!-- check:scale -->
### Capacity, performance and cost

Target 10,000 cases per plan per region within 4 hours at a default 300 cases per minute per tenant on the `cases-bulk` queue; cost is one Update plus one Continue-As-New per case.

<!-- check:observability -->
### Observability

Search attribute `blueprintVersion` counts running cases per version; migration metrics by outcome; alert when a plan has more than 5% failed items or runs longer than 6 hours; studio shows per-version running counts.

<!-- check:rollout -->
### Rollout and migration

Phase 4 ships lifecycle, pinning and diff; migration ships in Phase 5 behind a feature flag per tenant ([[PKG-feature-flags]]); first migrations run with Nomology implementation staff as second approver.

<!-- check:reversibility -->
### Reversibility

Hard to change later: the pure-core interpreter split, Auto-Upgrade for case processes, and the rule that content is pinned by data. Recorded here and proposed for its own ADR (see Open questions).

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "A Pinned Workflow is guaranteed to complete on a single Worker Deployment Version; Auto-Upgrade Workflows move to the current version and must be kept replay-safe, for example with patching.",
    "id": "R1",
    "kind": "vendor",
    "title": "Temporal docs: Worker Versioning",
    "url": "https://docs.temporal.io/worker-versioning",
    "vendor": "Temporal Technologies"
  },
  {
    "excerpt": "patched() lets new executions take a new code path while in-progress executions keep the old one; deprecatePatch() is the intermediate step before removal.",
    "id": "R2",
    "kind": "vendor",
    "title": "Temporal docs: Versioning (TypeScript SDK)",
    "url": "https://docs.temporal.io/develop/typescript/versioning",
    "vendor": "Temporal Technologies"
  },
  {
    "excerpt": "A migration plan maps each active element to a target element of the same type; migration is transactional per instance.",
    "id": "R3",
    "kind": "vendor",
    "title": "Camunda docs: Process instance migration",
    "url": "https://docs.camunda.io/docs/components/concepts/process-instance-migration",
    "vendor": "Camunda"
  },
  {
    "excerpt": "When you turn off a cloud flow, no new runs start. All in-progress and pending runs continue until they finish.",
    "id": "R4",
    "kind": "vendor",
    "title": "Microsoft Learn: Limits of automated, scheduled, and instant flows (Power Automate)",
    "url": "https://learn.microsoft.com/en-us/power-automate/limits-and-config",
    "vendor": "Microsoft"
  }
]
```

<!-- end -->
