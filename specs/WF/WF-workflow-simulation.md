---
id: "WF-workflow-simulation"
title: "Workflow simulation and test runs"
parent: "WF"
order: 13
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Static validation, scenario simulation on the shared pure interpreter core, historical what-if and sandbox test runs, with a publish gate on required scenarios and branch coverage"
links: []
rev: 1
syncHash: "5b744125c7222461"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 7.12 Workflow simulation and test runs

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Static validation, scenario simulation on the shared pure interpreter core, historical what-if and sandbox test runs, with a publish gate on required scenarios and branch coverage

<!-- section:statement -->
## Statement

**Core statement (EARS, event-driven):** When a workflow designer submits a case-type blueprint version for review, the platform shall run the version's required simulation scenarios and coverage checks with the same interpreter core that executes live cases, and shall block submission unless every required scenario passes and coverage meets the tenant's configured minimum.

Supporting requirements (prefix `SIM-FR-`):

- **SIM-FR-1 Three test modes.**

  | Mode | What runs | Side effects | Typical use |
  |---|---|---|---|
  | **Static validation** | Schema, references, reachability, dead ends, cycles without a wait, unmapped stage statuses, unreachable gateway branches, missing translations, accessibility of forms | None | Every save |
  | **Scenario simulation** | The pure interpreter core (`reduce(state, event)`, see [[WF-workflow-versioning#design]]) with a virtual clock, real decision-table evaluation and real calendar arithmetic, and mocked activities | None; runs in a BullMQ worker on queue `workflow.simulate` | Authoring, publish gate, migration dry runs |
  | **Sandbox test run** | The real Temporal interpreter on the tenant's sandbox ([[PKG-configuration-lifecycle]]) with synthetic cases marked `is_test`, compressed time (`timeScale`, for example 1 day = 1 minute) and real notifications delivered only to the designer's test inbox | Writes only `is_test` rows in the sandbox; external providers replaced by test doubles | Acceptance testing with real screens before go-live |

- **SIM-FR-2 Scenarios.** A scenario (`wf.simulation_scenario`) is data: initial facts (case fields, claim value, parties, representation), a timeline of events (`at: "P3D", event: "document.filed", payload: {...}`; `at: "P14D", event: "task.completed", task: "scrutinise_case", outcome: "defects"`), mocked activity results, and **assertions** (stage reached, deadline due date, task created for role, notification sent to role, decision output, end state, maximum duration).
- **SIM-FR-3 Required scenarios.** A designer marks scenarios as `required`; publishing (submit for review) is blocked unless all required scenarios pass on the exact version.
- **SIM-FR-4 Coverage.** Each simulation run reports coverage: stages entered, steps executed, gateway branches taken, timer timeouts fired, interrupts exercised. Submission is blocked if branch coverage across required scenarios is below `workflow.simulation.min_branch_coverage_pct` (default 100% for gateways that decide procedural paths, 80% overall).
- **SIM-FR-5 Trace.** Each run produces a step-by-step trace (virtual time, step, inputs as fact keys, decision rows matched, deadline explanations, tasks created, notifications that would be sent) viewable in the studio and downloadable as JSON.
- **SIM-FR-6 Historical what-if.** For a new version, the designer may replay the facts and event timelines of up to 500 closed cases of the same case type (taken from `case_stage_event`, `case_deadlines` and filings, with no personal data loaded into the simulator) and receive an impact report: change in stage durations, deadlines that would have differed, tasks per queue per week.
- **SIM-FR-7 AI-drafted scenarios.** The admin copilot ([[APP-admin-copilot]]) may propose scenarios that cover uncovered branches; proposed scenarios are drafts and become required only when a human marks them so.
- **SIM-FR-8 Evidence.** The passing gate run is linked to the version (`wf.blueprint_version.simulation_run_id`) and kept as long as the version, so reviewers and auditors can see what was tested.
- **SIM-FR-9 Determinism.** Running the same scenario on the same version twice shall produce an identical trace hash.
- **SIM-FR-10 Isolation.** Simulations never read or write live case data; sandbox test runs never send to real parties, providers or aggregators.

#### Tables (schema `wf`, tenant-owned, forced RLS)

**wf.simulation_scenario**: `id`, `tenant_id`, `case_type_id`, `key`, `name`, `body jsonb` (facts, timeline, mocks, assertions; no personal data, validator rejects contact details), `required boolean`, `source` (`human`, `ai_proposed`, `generated_from_history`), `created_by`, `version`.

**wf.simulation_run**: `id`, `tenant_id`, `blueprint_version_id`, `mode` (`scenario`, `history_replay`, `sandbox`), `scenario_ids uuid[]`, `status` (`queued`, `running`, `passed`, `failed`, `error`), `coverage jsonb`, `trace_ref uuid` (object store, encrypted), `trace_sha256 bytea`, `interpreter_build text`, `started_by`, `started_at`, `finished_at`.

<!-- section:rationale -->
## Rationale and source

- Tenants author procedures that decide legal deadlines and obligations; a wrong branch can deny a party a step or miss a statutory timeline. A publish gate with required scenarios and coverage makes "tested" a fact, not a hope.
- Low-code platforms let administrators define flow tests with initial conditions and assertions that run before activation [R1]; we borrow this, with stronger gating because our flows have legal effect.
- Temporal's own test tooling (time-skipping test environment) proves interpreter code [R2]; tenants need the same confidence for their data, which the shared pure core provides without spinning a Temporal test server per request.
- Historical what-if gives institutions the impact view they need before a rules revision, and supports the migration dry run in [[WF-workflow-versioning]].

<!-- section:acceptance -->
## Acceptance criteria

- **SIM-AC-1 Gate.** Given version v4 has two required scenarios and one fails its assertion "deadline `response_due` is 2027-03-15", when the designer submits for review, then submission is refused with the failing assertion, actual value and trace link.
- **SIM-AC-2 Coverage.** Given a gateway `eligible?` with branches `yes` and `no` and required scenarios that only take `yes`, when the designer submits, then submission is refused with "Branch `no` of gateway `eligible?` is not covered".
- **SIM-AC-3 Same core.** Given a scenario that passes in simulation, when the same facts and events are run as a sandbox test run with compressed time, then the sandbox case reaches the same stages in the same order with the same computed deadlines (checked by comparing the trace with the sandbox stage events).
- **SIM-AC-4 Determinism.** When a scenario is run twice on the same version and interpreter build, then the trace hashes are equal.
- **SIM-AC-5 Historical replay without personal data.** When a designer runs a what-if on 200 closed cases, then the simulator receives only fact keys, amounts bands, dates and event types; party names, addresses and document contents are not loaded (verified by a test asserting the loader's projection).
- **SIM-AC-6 Sandbox isolation.** Given a sandbox test run, when a notification step executes, then the message goes only to the designer's test inbox and no provider call is made with a real party address.
- **SIM-AC-7 Negative: AI scenarios are not auto-required.** When the copilot proposes three scenarios, then they are saved with `source = 'ai_proposed'`, `required = false`, and do not count toward the gate until a human marks them required.
- **SIM-AC-8 Negative: live data untouched.** When any simulation runs, then no row is written to `wf.case_process`, `human_tasks` or `case_deadlines` in the production tenant.

<!-- section:verification -->
## Verification method

| Method | Where |
|---|---|
| Unit tests of the pure core against a conformance suite shared with the Temporal shell (every step type, every interrupt) | `packages/workflow-templates/interpreter/conformance/*.spec.ts` |
| Equivalence test: each conformance scenario run in the simulator and in a Temporal time-skipping test environment yields identical traces [R2] | Same folder, CI |
| Gate tests through the admin API (`POST /admin/v1/workflows/case-types/{key}/versions/{v}:submit`) | `apps/web/test/admin/workflows-submit.spec.ts` |
| Sandbox isolation test with provider spies | `apps/web/e2e/admin/sandbox-test-run.spec.ts` |
| Analysis: projection used by history replay is reviewed by the privacy owner | Review record in [[SEC-privacy-controls]] |

<!-- section:priority -->
## Priority

**Must.** Static validation and scenario simulation with the publish gate land with the studio in Phase 4 (no tenant may publish a blueprint without them). Historical what-if and AI-proposed scenarios are **Should**, Phase 5. Sandbox test runs depend on tenant sandboxes from [[PKG-configuration-lifecycle]] and land when sandboxes do.

<!-- section:questions -->
## Open questions

- [ ] Coverage minimums per tenant type: is 100% of procedural gateways achievable for large institutional blueprints, or should the minimum be configurable down to 90% with a reviewer acknowledgement? (Product with legal)
- [ ] Should simulation traces be shareable outside the tenant (for example with Nomology implementation staff) without support access? Proposed: only through approved support access ([[PKG-support-access-and-impersonation]]). (Security)
- [ ] Load forecasting (tasks per queue per week from history replay) needs staff capacity data; is that in scope for Phase 5? (Product)
- [ ] Do court or government programme tenants require independent sign-off of test evidence before go-live? (Legal)

<!-- section:notes -->
## Notes

- Admin routes: `/admin/workflows/case-types/[caseTypeKey]/versions/[version]/simulate` and `/simulate/[runId]` ([[WF-workflow-authoring-studio#routing]]).
- Permissions: `workflow.simulation:create` (designers and reviewers), `workflow.definition:read` to view traces.
- Settings: `workflow.simulation.*` in [[PKG-settings-cases-and-workflows#catalogue]].
- Queue: `workflow.simulate` (BullMQ, concurrency 4 per worker, timeout 60 s per scenario, payload IDs only).

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Yes: without a gate, a tenant could publish a blueprint that skips a party's filing step or computes a wrong deadline, with no evidence of testing; migration dry runs also depend on the simulator.

<!-- check:unambiguous -->
### Unambiguous

Three modes are defined with what runs and what side effects are allowed; the gate condition (all required scenarios pass, coverage at or above the setting) is exact; acceptance criteria name expected outputs.

<!-- check:singular -->
### Singular

One capability (testing blueprints before and after publication) expressed as SIM-FR-1 to 10; the core EARS statement is the publish gate.

<!-- check:complete -->
### Complete and scoped

Covers scenario format, gate, coverage, trace, history replay, AI proposals, evidence retention, determinism and isolation, plus failure (simulator error yields status `error` and blocks submission with a retry, never a silent pass).

<!-- check:feasible -->
### Feasible

Depends on the pure interpreter core decided in [[WF-workflow-versioning]]; runs on BullMQ workers; no per-request Temporal test servers are needed.

<!-- check:verifiable -->
### Verifiable

Equivalence tests between simulator and Temporal test environment, gate API tests and sandbox isolation tests are specified with locations; negatives SIM-AC-7 and SIM-AC-8.

<!-- check:consistent -->
### Consistent

Consistent with the shared model (AI proposes, humans approve; sandboxes hold synthetic or masked data), with [[PKG-workflow-templates]] `simulate()` and with the publish gate referenced in [[WF-workflow-versioning]].

<!-- check:traced -->
### Traced

Sources: CTO request for workflow authoring; low-code flow tests [R1]; Temporal testing [R2]. Forward trace to the studio simulate screens and the tests listed above.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Flow tests define initial conditions and assertions that are evaluated when a flow test runs.",
    "id": "R1",
    "kind": "vendor",
    "title": "Salesforce Metadata API Developer Guide: FlowTest",
    "url": "https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_flowtest.htm",
    "vendor": "Salesforce"
  },
  {
    "excerpt": "The time-skipping test environment fast-forwards timers in workflow tests.",
    "id": "R2",
    "kind": "vendor",
    "title": "Temporal docs: Testing suite (TypeScript)",
    "url": "https://docs.temporal.io/develop/typescript/testing-suite",
    "vendor": "Temporal Technologies"
  }
]
```

<!-- end -->
