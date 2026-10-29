---
id: "ADR-workflow-interpreter-versioning"
title: "Workflow interpreter versioning"
parent: "ADR"
order: 14
type: "decision"
template: "adr"
status: "draft"
owner: null
indicative: false
summary: "How do we version the generic Temporal interpreter separately from blueprints? Proposed: Auto-Upgrade worker versioning plus patched(), short runs via Continue-As-New and a rollover sweep, a pure versioned core, and a data-selected interpreter contract with a 24-month previous-major window"
links: []
rev: 1
syncHash: "4c61227ade9a0d41"
createdAt: "2026-10-28T09:00:00Z"
updatedAt: "2026-10-28T09:00:00Z"
updatedBy: null
---

# 19.12 Workflow interpreter versioning

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> How do we version the generic Temporal interpreter separately from blueprints? Proposed: Auto-Upgrade worker versioning plus patched(), short runs via Continue-As-New and a rollover sweep, a pure versioned core, and a data-selected interpreter contract with a 24-month previous-major window

<!-- section:context -->
## Context and problem

**Question:** how do we version the Nomology-written generic Temporal interpreter (the `caseProcess` workflow and its pure core in `@nomology/workflow-templates`) so that weekly code releases never break cases that run for months or years, independently of the tenant-authored blueprint versions those cases are pinned to?

**Affected parts:** [[PKG-workflow-templates]] (interpreter core, shell, `INTERPRETER_CONTRACT`), [[WF-workflow-versioning]] (two version axes, migration), [[WF-separation-of-concerns-temporal]] (layer 1 and layer 4), [[WF-process-definition-model]] (`wf.blueprint_version.interpreter_contract`), [[WF-workflow-simulation]] (shared pure core), [[WF-human-tasks]], [[WF-sla-and-business-calendars]], [[WF-long-running-pipelines]] (short code workflows), [[INF-temporal]] (server version, worker services), [[PKG-settings-cases-and-workflows]] (`workflow.runtime.supported_interpreter_contracts`, `workflow.runtime.continue_as_new_events`).

**Facts that constrain the answer**

- Two things change at different speeds. Blueprint content is data, pinned per case by `blueprintVersionId` and loaded once at start. Interpreter code is ours and ships every release. This record is about the second axis only.
- Temporal workflow code must replay deterministically against its recorded history. A code change that alters the sequence of commands for an existing history breaks that workflow unless it is gated by `patched()` [R4].
- Temporal Worker Versioning groups workers into a **Worker Deployment** with **Deployment Versions** (deployment name plus build ID). **Pinned** workflows complete on one version; **Auto-Upgrade** workflows move to the Current (or Ramping) version and "need to be kept replay-safe manually" with patching [R1].
- Pinned behaviour is inherited across Continue-As-New within the same deployment; Auto-Upgrade workflows do not inherit a version across Continue-As-New [R1].
- Worker Versioning became generally available in March 2026; **Upgrade on Continue-as-New** (moving a Pinned workflow to a new version at a Continue-As-New boundary) is still Public Preview, described as "an experimental SDK-level option" [R3][R9].
- Self-hosted requirements: Temporal Server 1.29.1 or later, CLI 1.4.1, UI 2.38.0, and TypeScript SDK 1.12 or later [R2]. The 2023 build-ID based draft ("version sets") is deprecated [R8].
- The overhaul already decided that case-process workflows Continue-As-New at every stage boundary, after every migration and after 2,000 history events ([[PKG-workflow-templates#config]]).

**Out of scope:** blueprint version lifecycle, change classes and in-flight migration between blueprint versions ([[WF-workflow-versioning]]); Temporal hosting ([[ADR-temporal]]); the choice of Temporal itself ([[ADR-workflow-engine]]); the expression language ([[ADR-expression-and-rules-language]]), except that an evaluator change is treated as an interpreter code change here.

<!-- section:drivers -->
## Decision drivers

| # | Driver | Why it matters here |
|---|---|---|
| D1 | **Running-case safety**: no release may cause a non-determinism error or change the behaviour of a running case | Cases carry legal deadlines; a stuck or mis-replayed case is a procedural failure |
| D2 | **Weekly release cadence**, per region, without coordinating with tenants | Platform engineering ships interpreter fixes and new step types continuously ([[WF-workflow-versioning]] goal 3) |
| D3 | **Reproducibility and explainability**: for any case we can say which blueprint version and which interpreter build produced each step | Institutions and regulators may ask why a deadline or step happened ([[PKG-audit-trail]]) |
| D4 | **Operating effort per region** (India, Singapore, US; Azure where a client requires it) for a small team on ECS or Azure Container Apps ([[ADR-container-orchestration]]) | Each live build is a worker service to run, patch, monitor and pay for in every region |
| D5 | **Security patching**: no old build with stale dependencies may run for years | ISO 27001 A.8.8 vulnerability management; worker images carry Node.js and SDK dependencies |
| D6 | **Simulator parity**: what the designer simulates is what runs ([[WF-workflow-simulation]] SIM-AC-3) | One pure core shared by simulator, migration dry run and live shell |
| D7 | **Maturity and support** of the Temporal features we depend on, on self-hosted clusters | Pre-release features add upgrade risk to a regulated system |
| D8 | **Reversibility**: we can move to another strategy without rewriting running cases | The strategy is otherwise locked in by years-long cases |
| D9 | **Team skills**: TypeScript, Temporal TypeScript SDK, no dedicated SRE team | Mechanisms must be teachable and testable in CI |

<!-- section:decision -->
## Decision

**Status: Proposed — awaiting CTO decision.**

**Recommended: Option A, Auto-Upgrade worker versioning plus `patched()`, with run lifetimes kept short by Continue-As-New and a rollover sweep, a pure and versioned interpreter core, and a separate, data-selected interpreter contract with a 24-month support window for the previous major.**

#### 1. Deployments and behaviours

| Workflow kind | Worker deployment | Versioning behaviour | Why |
|---|---|---|---|
| `caseProcess` (blueprint interpreter) | `wf-interpreter-{region}` (for example `wf-interpreter-in`), build ID = release tag (`2026.11.1`) | **Auto-Upgrade**, declared per workflow type with `setWorkflowOptions` [R5] | Cases outlive any build; Temporal's guide says a workflow type that may outlive its deployment versions should be Auto-Upgrade [R2] |
| Code subprocesses called by blueprints (notice service, eBundling) that can last weeks | Same deployment | Auto-Upgrade | Same reason as above |
| Short code workflows (pipelines, `blueprintMigration`, migration batches, sandbox test runs) | Same deployment | **Pinned** | They finish within days; no patching needed for them, and they drain on the old version [R2] |

Workers set `workerDeploymentOptions: { version: { deploymentName, buildId }, useWorkerVersioning: true, defaultVersioningBehavior: 'PINNED' }` [R5], so a workflow type that forgets to declare Auto-Upgrade gets the safe default.

#### 2. Three separate kinds of compatibility

| Layer | What changes | Mechanism | How long it lives |
|---|---|---|---|
| **Replay compatibility** (code) | The commands the shell emits for an existing history | `patched('<change-id>')`, then `deprecatePatch()`, then removal [R4] | Until no open run started before the patch. Section 3 keeps this to weeks |
| **State compatibility** | The shape of the interpreter state passed across Continue-As-New | `stateSchemaVersion` on the snapshot plus upcasters in the core; each build reads the current and previous two versions | About 3 releases |
| **Semantic compatibility** (contract) | What a blueprint construct means (`interp/<major>.<minor>`) | Chosen by **data**: the blueprint's declared contract selects the code path. Never by `patched()` | Current major plus previous major for at least 24 months (the CTO decides the window) |

This splits two things the overhaul notes merged ("previous major supported for 24 months using `patched()` branches"). `patched()` exists only for replay safety and should be removed quickly. Long-term support for old blueprint semantics is ordinary, tested code selected by the contract version.

#### 3. Short run lifetimes so patches can be removed

- Continue-As-New at every stage boundary, after every migration and when `workflowInfo().continueAsNewSuggested` is true [R6] (already specified in [[PKG-workflow-templates#config]]).
- **Rollover sweep (new):** a regional Temporal Schedule sends the Signal `requestRollover` to every `caseProcess` run older than `workflow.runtime.max_run_age_days` (proposed 30). The handler only sets a flag. The main workflow thread calls Continue-As-New at the next quiescent point (waiting on a timer, signal or human task), after it has drained pending signals into the new input [R6].
- Auto-Upgrade runs do not inherit a version across Continue-As-New [R1], so each new run starts on the version that is Current at that moment.
- The search attribute `interpreterBuild` is set at the start of each run. A patch may be deprecated once a visibility query shows no open run with an older build. Expected time: about 30 to 45 days after a full rollout, not the lifetime of a case.

#### 4. A pure, versioned core

- `reduce(state, event, ctx) → { state, commands }` has no I/O. The shell turns commands into activities, timers and child workflows.
- `ctx.features` is a set of patch IDs. The shell computes it by calling `patched()` at the point of use, so the core stays pure. The simulator passes the full current set, so simulation always shows current behaviour.
- The expression evaluator ([[ADR-expression-and-rules-language]]) is part of the core bundle. Any change to the evaluator that can change a result is treated as a replay-affecting interpreter change.

#### 5. Rollout and rollback

1. CI replay gate (see Confirmation).
2. Deploy the new version's workers in a region. Set it as **Ramping** at 10 percent for 24 hours (proposed). Then set it **Current** [R1][R2] if these gates hold: no non-determinism errors, no rise in `failed_config` cases, and workflow-task failure rate at or below baseline.
3. Regions roll one after another: Singapore, then US, then India (largest volume last; proposed order).
4. **Rollback is roll-forward by default.** Setting Current back to the previous build is allowed only if CI has shown that the previous build replays histories produced by the new build. Assumption: how the TypeScript SDK treats patch markers that the older code does not know must be confirmed in the spike.

#### 6. Major rewrites

When the change needed is too large for patches (for example a new state model), ship a new workflow type `caseProcessV{n}`. Running cases hand over to it by Continue-As-New at a quiescent point, reusing the migration machinery in [[WF-workflow-versioning]] (Option F used as a tool, not as the default).

#### 7. Platform prerequisites

Temporal Server 1.29.1 or later, CLI 1.4.1 or later and TypeScript SDK 1.12 or later in every region [R2] ([[INF-temporal]]). The deprecated build-ID based APIs are not used [R8].

#### Why

- **D1, D2:** patching plus replay tests is the documented way to keep Auto-Upgrade workflows safe [R1][R4]. Ramping limits how many cases a bad build can reach.
- **D4, D5:** at most two builds are live per region, and each only for hours to days. No build runs for years, which Option B would need.
- **D6:** one pure core serves the simulator, the dry run and live cases.
- **D7:** everything relies only on generally available features. Upgrade on Continue-as-New is still Public Preview [R3][R9].
- **D8:** the versioned state snapshot and the quiescent Continue-As-New points are also exactly what Option C needs. Switching later is a configuration change plus a spike, not a rewrite.

**Scope:** all Temporal workflows written by Nomology in every region and environment. This record refines, and does not change, [[ADR-workflow-engine]] (D6 testability and versioning) and [[ADR-temporal]].

<!-- section:consequences -->
## Consequences

**Easier**

- Engineers ship interpreter changes weekly. Old cases pick up fixes within weeks, because every new run starts on the current build.
- Operations runs one interpreter build per region in steady state, plus a second one during a ramp. The CVE patch window is the normal release cycle.
- Designers and auditors get one behaviour model. The simulator, dry runs and live cases share the core, and `interpreterBuild` plus `blueprintVersion` explain any step ([[WF-process-definition-model]]).

**Harder**

| Who | Cost or risk | Mitigation |
|---|---|---|
| Platform engineers | Every change that alters commands must be spotted and wrapped in `patched()`. A missed patch is a production non-determinism error | Replay gate on every PR touching `packages/workflow-templates/**`, and the patch-lint rule (Confirmation) |
| Platform engineers | Up to three state schema versions and two contract majors to support and test | Upcaster and contract conformance suites; contract support ends on a fixed date |
| Operations (per region) | The deploy pipeline must call `set-ramping-version` and `set-current-version` itself. On ECS and Azure Container Apps we cannot use Temporal's Kubernetes Worker Controller [R9] | Pipeline step written once in Turborepo CI, run per region; runbook in [[INF-temporal]] |
| Operations | Rollover sweep adds roughly one Continue-As-New per case each month. Assumption: at 2 million open workflows in India ([[INF-temporal]]) that is about 46 per minute, small against the 50 starts per second sizing | Rate limit on the sweep (`workflow.runtime.rollover_rate_per_min`, proposed 600) |
| Security | Replay CI needs real histories, which hold encrypted case payloads | Replay jobs run inside each region with the regional codec. Histories come from staging or anonymised exports ([[WF-workflow-versioning]] residency check) |
| Support | A case can show different builds on different runs | The Temporal Web UI shows the build per run; the secretariat console shows only stage and blueprint version |

**Follow-up work** (owner: workflow squad unless stated; tickets to be raised when the CTO accepts):

1. Add `interpreterBuild` as a registered search attribute in every namespace ([[INF-temporal]], DevOps).
2. Add settings `workflow.runtime.max_run_age_days` and `workflow.runtime.rollover_rate_per_min` to [[PKG-settings-cases-and-workflows]].
3. Correct the 24-month sentence in [[WF-workflow-versioning]] section 6 and in [[PKG-workflow-templates#versioning]] to "selected by contract version, not by `patched()`".
4. Upgrade every regional cluster to Temporal Server 1.29.1 or later before Phase 3 (DevOps).

**Cost (assumption, to be checked in the spike):** no licence cost, since Temporal Server is MIT [R10]. The extra cost is the second worker service during a ramp, about 1 to 2 days per release per region, plus one CI replay job per region per PR.

<!-- section:confirmation -->
## Confirmation

#### Automated checks (block merge or deploy)

| Check | Where | Blocks | Target |
|---|---|---|---|
| **Replay gate:** replay the newest 500 histories of `caseProcess` per region plus a pinned golden set (one per step type, interrupt and contract) with `Worker.runReplayHistories` [R7] | Regional CI runner, on PRs touching `packages/workflow-templates/**`, `packages/expr/**` or `packages/rules/**` | Merge | 0 `DeterminismViolationError` |
| **Backward replay:** the previous build replays histories produced by the new build in staging | Release pipeline | Setting Current back (rollback) | Pass or rollback is marked "roll-forward only" |
| **Patch lint:** a change to files under `interpreter/shell/**` or to the command output of the conformance suite without a new `patched()` ID fails | CI (golden command traces per conformance scenario) | Merge | — |
| **Simulator equivalence:** the conformance suite gives identical traces in the simulator and in the time-skipping test environment [R7] | CI | Merge | 100% identical |
| **Behaviour declaration:** every registered workflow type declares a versioning behaviour, and `caseProcess` is Auto-Upgrade | Unit test over the workflow registry | Merge | — |
| **Platform version:** each regional cluster runs Server 1.29.1 or later and workers run TypeScript SDK 1.12 or later [R2] | IaC policy check and worker start-up check | Deploy | — |

#### Measured in production (monthly review in [[OBS-performance]])

- Non-determinism errors on `caseProcess`: 0 per quarter.
- 95% of open `caseProcess` runs on the Current build within 45 days of a release (from `interpreterBuild`).
- Live `patched()` IDs older than 90 days: 0 (each one needs an approved exception).
- Builds polling per region outside a ramp: 1.

**Exceptions:** a patch kept beyond 90 days, or a rollback without backward replay, needs approval from the workflow squad lead, recorded in [[FND-governance]].

#### Spike (two weeks, before Phase 3, in the Singapore staging cluster)

1. Run `caseProcess` with 5,000 synthetic cases under Auto-Upgrade. Release three builds: one with a patched command change, one with a state schema change and one with a contract minor bump.
2. Run the rollover sweep and measure the time until 95% of runs are on Current.
3. Test rollback by setting the previous build Current after the new build has written patch markers.
4. Run the same scenario under Option C (Pinned plus Upgrade on Continue-as-New) [R3] for comparison.

**Exit criteria:** zero non-determinism errors in step 1. Step 2 within 72 hours at sweep rate 600 per minute. The rollback behaviour in step 3 is documented as safe or as "roll-forward only". Option C's result is recorded so that its revisit trigger can be judged. If step 1 fails, Option A is not accepted as is, and the CTO decides between Option C and Option E.

<!-- section:options -->
## Options considered

Scores: ✔ meets the driver, ◐ partly, ✘ fails. The cost figures are assumptions until the spike.

| Option | D1 safety | D2 weekly releases | D4 / D5 ops and patching per region (IN, SG, US) | D6 simulator parity | D7 maturity | Lock-in and licence | Residency | Skills | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **A. Auto-Upgrade + `patched()` + short runs + pure core** | ◐ Relies on patch discipline, enforced by replay and patch lint | ✔ | ✔ One build in steady state, two during a ramp; old builds gone within days | ✔ | ✔ Worker Versioning GA [R9] | Temporal (MIT [R10]); patching is portable to unversioned workers | ✔ No change | ✔ Standard TypeScript SDK patching [R4] | **Recommended** |
| B. Pinned for the life of the case (rainbow deployments) | ✔ No patching needed [R2] | ✔ | ✘ One live build per release per region for years (about 150 builds after 3 years of weekly releases), each needing CVE patching. Patching a pinned build changes its code, which defeats pinning | ◐ Simulator must emulate old builds | ✔ | Same | ✔ | ◐ | Rejected for case processes; used for short workflows |
| C. Pinned + Upgrade on Continue-as-New (+ rollover sweep) | ✔ No patching inside a run; upgrade only at Continue-As-New [R3] | ✔ | ◐ Old builds stay until every run has rolled over (the sweep bounds this to days). New version must accept the previous input [R3] | ✔ | ✘ Public Preview, "experimental SDK-level option" [R3][R9] | Same | ✔ | ◐ New API | **Strongest alternative**; reopen when GA (see Revisit) |
| D. Build-ID based versioning (2023 draft, version sets) | ◐ | ✔ | ◐ | ✔ | ✘ Deprecated [R8] | Deprecated API | ✔ | ◐ | Rejected |
| E. Unversioned workers + `patched()` only | ◐ Same patch discipline as A, but no ramp: a bad build reaches all cases at once | ✔ | ✔ One build | ✔ | ✔ Oldest, simplest path [R4] | Lowest | ✔ | ✔ | Fallback if Worker Versioning causes trouble in the spike |
| F. Continue-As-New migration to a new workflow type each release | ✔ Old type never changes | ✘ Every release needs a mass migration of running cases | ◐ Two types live per release; migration load each week | ✔ | ✔ | Low | ✔ | ◐ | Rejected as the default; kept as the tool for major rewrites (Decision 6) |
| G. Interpreter per blueprint version or contract (a separate deployment per contract, blueprint pins code) | ✔ | ◐ Fixes must be back-ported to every live contract build | ✘ Number of builds grows with the number of contracts, per region | ✘ Simulator must load many interpreters | ◐ | Low | ✔ | ✘ | Rejected |

**Notes on the evidence**

- Temporal's decision guide recommends Pinned plus upgrade on Continue-As-New for long-running workflows that use Continue-As-New, and Auto-Upgrade plus patching for those that do not [R2]. Our case processes do use Continue-As-New, so C is Temporal's own preferred pattern. It is not recommended now only because of D7 (Public Preview). Option A's state snapshot and quiescent rollover keep the move to C cheap.
- The cost per region is the same in India, Singapore and the US for every option, except that India, with the largest volume, takes the longest to drain Pinned builds (B, C).
- There is no conflict with the approved ADRs. The approved [[ADR-workflow-engine]] already requires determinism replay tests in CI, and [[WF-workflow-engine]] already has the guardrail "never pin a long-lived case process to a single worker build".

<!-- section:revisit -->
## When to revisit

- **Upgrade on Continue-as-New becomes GA** in the TypeScript SDK and self-hosted server [R3], and the spike shows it drains 95% of runs within 72 hours. Then reopen in favour of Option C.
- More than **one production non-determinism error** on `caseProcess` in a quarter, or more than **5 live patches older than 90 days**.
- Replay gate run time above **20 minutes** per PR, or false failures above 5% of runs.
- The rollover sweep cannot get 95% of runs onto the Current build within **45 days** in any region.
- A client contract requires that a case run on **certified, unchanging code** for its life (Option B or G for that tenant).
- We move off ECS or Azure Container Apps to Kubernetes, which makes Temporal's Worker Controller available [R9].
- A change in Temporal licence or project health ([[ADR-temporal]] revisit triggers).
- Scheduled review: 6 months after the first tenant blueprints go live in production.

<!-- section:questions -->
## Open questions

- [ ] Accept the previous-major support window of 24 months for interpreter contracts, or tie it to the longest expected case duration per tenant type (for example 36 months for institutional arbitration)? (CTO)
- [ ] Accept "roll-forward only" as the default rollback policy for interpreter builds? (CTO)
- [ ] Rollover age `workflow.runtime.max_run_age_days`: 30 days proposed. (Workflow squad)
- [ ] Region rollout order and the length of the ramp at 10% (24 hours proposed). (DevOps with product)
- [ ] Do production replay tests use anonymised production histories, or staging only? This affects coverage and the privacy review in [[SEC-privacy-controls]]. (Security)

<!-- section:notes -->
## More information

- Origin: the open questions in [[WF-separation-of-concerns-temporal#questions]], [[WF-workflow-versioning#questions]] and [[WF]], which asked for this strategy to be recorded as its own ADR, because [[ADR-workflow-engine]] is approved and must not be edited.
- Related proposed record: [[ADR-expression-and-rules-language]]. The evaluator is part of the interpreter core, so changes to it follow this record.
- Nodes to update when this is accepted: [[WF-workflow-versioning]] (section 6 wording), [[PKG-workflow-templates]] (versioning, new settings), [[INF-temporal]] (server version floor, search attribute, deploy pipeline steps), [[PKG-settings-cases-and-workflows]] (two new keys). Each should add a "Decided by" link to this record.

<!-- checks -->
## Template checks

<!-- check:significance -->
### Significance

Significant and hard to reverse. Every running case depends on the chosen behaviour. After 18 months there may be hundreds of thousands of open case workflows, and changing strategy then means a controlled rollover of all of them (estimate: 4 to 6 engineer-weeks plus a drain period). It affects every region, both offerings, and the reproducibility we owe institutions. It decides only interpreter code versioning. Blueprint content versioning and migration ([[WF-workflow-versioning]]), hosting ([[ADR-temporal]]) and the expression language ([[ADR-expression-and-rules-language]]) are separate.

<!-- check:options -->
### Options and evidence

Seven options were compared against the same nine drivers: A to C are the Worker Versioning variants, D is the deprecated build-ID API, E is unversioned patching, F is Continue-As-New to a new workflow type, and G is an interpreter per contract. The evidence is Temporal's official documentation for behaviours [R1], the production guide and version floors [R2], Upgrade on Continue-as-New status [R3][R9], patching [R4], worker configuration [R5], Continue-As-New [R6], replay testing [R7] and the legacy deprecation [R8]. Cost and drain-time figures are labelled assumptions and are measured in the spike. The record does not conflict with [[ADR-workflow-engine]] or [[ADR-temporal]].

<!-- check:compliance -->
### Regulatory, residency and tenancy fit

- **Residency:** unchanged. Each region runs its own `wf-interpreter-{region}` deployment. Replay tests run on regional CI runners, against regional staging histories or anonymised exports, with the regional codec. Histories never leave the region.
- **Tenant isolation:** unchanged. Workflow IDs stay tenant-prefixed, and interceptors still set tenant context per activity. The rollover sweep runs one Signal per workflow ID inside one namespace, with no cross-tenant data access.
- **Sub-processors:** none added.
- **Audit:** improved. `interpreterBuild` per run, plus blueprint version, explains which code applied. Release, ramp and rollback actions are logged by the deploy pipeline as `platform.workflow:update` operations ([[PKG-audit-trail]]).
- **Controls:** ISO 27001:2022 A.8.32 change management (ramp and gates), A.8.8 technical vulnerabilities (no long-lived old builds), A.8.29 testing in development (replay gate). SOC 2 CC8.1 change management.
- **Reviewer:** security and compliance review not yet recorded. To be added with name and date before acceptance.

<!-- check:consequences -->
### Consequences and costs

The downsides are listed per stakeholder in the Consequences section: patch discipline for engineers; up to three state versions and two contract majors to support; pipeline-driven version switching on ECS and Azure Container Apps without Temporal's Kubernetes controller; the rollover load; replay CI needing in-region histories; and builds varying per run for support. Four follow-up items are listed with owners. They become tickets when the CTO accepts. The cost is mostly CI time and one to two days of a second worker service per release per region (assumption).

<!-- check:reversibility -->
### Reversibility and revisit triggers

- **Failure signals:** non-determinism errors, patches older than 90 days, slow rollover, or a replay gate that is too slow (see When to revisit).
- **Exit to Option C:** switch `caseProcess` to Pinned with Upgrade on Continue-as-New once GA. The versioned state snapshot, quiescent Continue-As-New and rollover sweep stay the same. Estimate: 2 to 3 engineer-weeks plus one rollover cycle.
- **Exit to Option E:** stop using Worker Versioning and rely on patching alone. Low cost, because patching is already mandatory.
- **Exit to F or G:** costly. It needs new workflow types and a mass handover.
- **Kept cheap now:** state snapshot and contract versions are independent of the Temporal versioning behaviour.
- **Review:** 6 months after the first live tenant blueprints.

<!-- check:confirmation -->
### Confirmation

The blocking checks are: the replay gate (0 determinism errors on the newest 500 histories per region plus a golden set), backward replay before any rollback, a patch lint based on golden command traces, simulator and Temporal equivalence tests, a versioning-behaviour declaration test, and the server and SDK version floor in IaC and at worker start-up. Production measures are reviewed monthly. Exceptions are approved by the workflow squad lead and recorded in [[FND-governance]]. A two-week spike with exit criteria comes before Phase 3. The patch lint carries a deliberately failing fixture to prove that it still works.

<!-- check:linked -->
### Linked and lifecycle

Governs [[PKG-workflow-templates]], [[WF-workflow-versioning]], [[WF-separation-of-concerns-temporal]] (layer 1 versioning row), [[WF-process-definition-model]] (`interpreter_contract`), [[WF-workflow-simulation]], [[INF-temporal]] and [[PKG-settings-cases-and-workflows]]. Refines [[ADR-workflow-engine]] (D6) and works within [[ADR-temporal]]. Related: [[ADR-expression-and-rules-language]]. Status: Proposed on 2026-10-28; decider: CTO; consulted: workflow squad and DevOps; informed: product and legal (contract support window). The listed nodes need "Decided by" back-links on acceptance.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "A Pinned Workflow is guaranteed to complete on a single Worker Deployment Version. Auto-Upgrade Workflows need to be kept replay-safe manually, using patching. Pinned versions are inherited across Continue-as-New within the same deployment; Auto-Upgrade Workflows do not inherit a version.",
    "id": "R1",
    "kind": "vendor",
    "title": "Temporal docs: Worker Versioning (concepts)",
    "url": "https://docs.temporal.io/worker-versioning",
    "vendor": "Temporal Technologies"
  },
  {
    "excerpt": "Requires Temporal Server v1.29.1+, CLI v1.4.1, UI v2.38.0; TypeScript SDK v1.12. Decision guide: PINNED + upgrade on CaN for long-running workflows using Continue-as-New; AUTO_UPGRADE + patching otherwise; mark a Workflow Type Auto-Upgrade if it may outlive Worker Deployment Versions.",
    "id": "R2",
    "kind": "vendor",
    "title": "Temporal docs: Worker Versioning (production deployment guide)",
    "url": "https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning",
    "vendor": "Temporal Technologies"
  },
  {
    "excerpt": "This feature is in Public Preview as an experimental SDK-level option. Lazy moving only; the new version's Workflow must accept the previous input.",
    "id": "R3",
    "kind": "vendor",
    "title": "Temporal docs: Upgrade on Continue-as-New",
    "url": "https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning/upgrade-on-continue-as-new",
    "vendor": "Temporal Technologies"
  },
  {
    "excerpt": "patched() inserts a marker into history; deprecatePatch() keeps the marker but does not fail replay if missing; remove after no open executions use the previous code.",
    "id": "R4",
    "kind": "vendor",
    "title": "Temporal docs: Versioning (TypeScript SDK)",
    "url": "https://docs.temporal.io/develop/typescript/workflows/versioning",
    "vendor": "Temporal Technologies"
  },
  {
    "excerpt": "workerDeploymentOptions: { version: { deploymentName, buildId }, useWorkerVersioning: true, defaultVersioningBehavior }; per-Workflow versioningBehavior via setWorkflowOptions().",
    "id": "R5",
    "kind": "vendor",
    "title": "Temporal docs: Run a Worker (TypeScript SDK)",
    "url": "https://docs.temporal.io/develop/typescript/workers/run-worker-process",
    "vendor": "Temporal Technologies"
  },
  {
    "excerpt": "Use workflowInfo().continueAsNewSuggested; drain unprocessed Signals and pass them forward; do not call Continue-As-New from a Signal handler.",
    "id": "R6",
    "kind": "vendor",
    "title": "Temporal docs: Continue-As-New pattern",
    "url": "https://docs.temporal.io/design-patterns/continue-as-new",
    "vendor": "Temporal Technologies"
  },
  {
    "excerpt": "Worker.runReplayHistories() with client.workflow.list(); DeterminismViolationError on non-determinism; TestWorkflowEnvironment.createTimeSkipping().",
    "id": "R7",
    "kind": "vendor",
    "title": "Temporal docs: Testing suite (TypeScript SDK)",
    "url": "https://docs.temporal.io/develop/typescript/testing-suite",
    "vendor": "Temporal Technologies"
  },
  {
    "excerpt": "Refers to the 2023 draft of Worker Versioning, which was deprecated.",
    "id": "R8",
    "kind": "vendor",
    "title": "Temporal docs: Worker versioning (legacy)",
    "url": "https://docs.temporal.io/encyclopedia/worker-versioning-legacy",
    "vendor": "Temporal Technologies"
  },
  {
    "excerpt": "March 30, 2026: Worker Versioning GA, with Upgrade on Continue-as-New (Public Preview). May 4, 2026: Temporal Worker Controller GA for Kubernetes-based workers.",
    "id": "R9",
    "kind": "vendor",
    "title": "Temporal changelog: Server",
    "url": "https://temporal.io/changelog/product-area/server",
    "vendor": "Temporal Technologies"
  },
  {
    "excerpt": "MIT License.",
    "id": "R10",
    "kind": "vendor",
    "title": "temporalio/temporal repository (MIT licence)",
    "url": "https://github.com/temporalio/temporal",
    "vendor": "Temporal Technologies"
  }
]
```

<!-- end -->
