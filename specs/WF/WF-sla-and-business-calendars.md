---
id: "WF-sla-and-business-calendars"
title: "SLAs, timers and business calendars"
parent: "WF"
order: 11
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Procedural deadlines on seat calendars and service-level targets on tenant, unit, queue or region business schedules: SLA policies, pause, warnings, breach, stays and evidence"
links: []
rev: 1
syncHash: "15e4aaae09d76f6f"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 7.10 SLAs, timers and business calendars

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Procedural deadlines on seat calendars and service-level targets on tenant, unit, queue or region business schedules: SLA policies, pause, warnings, breach, stays and evidence

<!-- section:statement -->
## Statement

**Core statement (EARS, ubiquitous):** The platform shall measure every configured service-level target and every procedural deadline against the correct calendar for the tenant, unit, region and case seat, with pause, warning, breach and escalation behaviour defined as tenant configuration, and shall record every computed due time with the calendar versions and rule that produced it.

This node is a requirement cluster: it states the SLA, timer and business-calendar requirements for workflows. Calendar computation is owned by [[PKG-calendars-and-deadline]] and the configuration of business schedules and SLA policies by this node (decision D13); task assignment and escalation targets by [[WF-human-tasks]]; where they are used in a blueprint by [[WF-process-definition-model]].

#### Two kinds of clock (never mixed)

| | Procedural deadline | Service-level target (SLA) |
|---|---|---|
| Meaning | An obligation under the rules or an order (respondent files response within 30 days of service) | An internal or contractual performance target (secretariat scrutinises a filing within 2 business days) |
| Source of the period | Decision table pinned to the case, or an order | SLA policy (tenant configuration) |
| Calendar | Seat calendars and the case's seat time zone ([[PKG-calendars-and-deadline]]) | Business schedule of the unit or tenant (working hours, closures) |
| Stored in | `case_deadlines` ([[DOM-cases-schema]]) | `wf.sla_clock` |
| Changes | Only by order, extension or stay, recorded in `case_deadline_changes` | By policy version and pause rules |
| Missed | Domain event `deadline.missed`; procedural consequences decided by the blueprint | Breach event `sla.breached`; escalation; reporting |
| Engine | Temporal timer in the case process | Temporal timer in the case process or in the task's owner workflow; never a BullMQ delayed job |

#### Requirements

- **SLA-FR-1 Business schedules.** A tenant shall be able to define named business schedules (`wf.business_schedule`): IANA time zone, weekly working hours per weekday (up to 3 intervals per day), holiday calendars to apply (public `ref.calendar` codes plus `tenant:closures` and unit closures), and an effective-from date.
- **SLA-FR-2 Schedule binding.** Schedules shall be bound at `region` (platform default per region), `tenant`, `unit` and `work_queue` scopes (`wf.business_schedule_binding`); the schedule used for a clock is the most specific binding for the clock's subject: queue, then the case's unit, then tenant, then region.
- **SLA-FR-3 SLA policies.** A tenant shall be able to define SLA policies (`wf.sla_policy`, artefact kind `sla_policy`) with: ordered conditions (case type, unit, priority, claim-value band, party representation, procedure family), metrics with targets, measurement basis (`business_hours`, `business_days`, `calendar_hours`, `calendar_days`), pause conditions, warning thresholds and breach actions. Policies are evaluated in order and the first matching policy applies to the subject.
- **SLA-FR-4 Metrics.** Supported metrics: `task_completion` (human task created → completed), `first_response` (filing submitted → first staff action), `stage_duration` (stage entered → exited), `case_resolution` (registered → closed), `transcript_turnaround` (recording available → certified transcript, used by [[DOM-transcribers]]).
- **SLA-FR-5 Pause.** While a pause condition holds (case `suspended`; waiting on a party with a running procedural deadline; task in `waiting_on_external`), the clock shall stop and resume with its remaining time; each pause and resume is recorded on the clock.
- **SLA-FR-6 Warnings and breach.** When elapsed time reaches each warning threshold (default 50%, 75%, 90%) the platform shall emit `sla.warning` with the level; at 100% it shall emit `sla.breached`, mark the clock `breached`, and run the policy's breach actions (notify, raise priority, escalate to the next level of the task's escalation chain).
- **SLA-FR-7 Procedural timers.** When a blueprint timer of `kind: procedural` starts, the platform shall compute the due time through `computeDeadline` using the case seat calendars, seat time zone and the counting conventions from the pinned decision table, write a `case_deadlines` row with the explanation and `calendarVersions`, and set a Temporal timer for the due instant and for each configured reminder.
- **SLA-FR-8 Stays.** When a case is suspended or a deadline is stayed by order, running procedural deadlines shall move to `stayed` with `stayed_remaining`; on resume they shall be recomputed from the resume instant with the remaining duration and the same conventions.
- **SLA-FR-9 Calendar changes.** If a calendar or business schedule changes after a due time was computed, procedural deadlines shall not move automatically; affected deadlines shall be listed for case-manager review (existing rule in [[PKG-calendars-and-deadline#config]]). Service-level clocks shall be recomputed on the next tick from the new schedule.
- **SLA-FR-10 Case-level overrides.** A case manager with `case.deadline:update` may extend a procedural deadline only with an order reference or reason, as allowed by `case.deadline.extension_requires_order`; SLA targets cannot be edited per case.
- **SLA-FR-11 Evidence.** Every computed due time shall store `specHash`, calendar versions, the policy or decision version, and the human-readable explanation, so it can be reproduced.
- **SLA-FR-12 Reporting.** Clock states shall feed SLA attainment reports per tenant, unit, queue and case type ([[RPT-cases]]), and tenant-facing SLA reports where a contract requires them ([[RPT-platform-performance]] for platform SLAs, which are separate).

#### Tables (in schema `wf`, tenant-owned, forced RLS; see [[WF-process-definition-model#tenancy]])

**wf.business_schedule**: `id`, `tenant_id`, `key text`, `name jsonb`, `time_zone text` (IANA), `weekly_hours jsonb` (`{"mon":[["09:00","13:00"],["14:00","18:00"]], …}`), `calendars text[]` (e.g. `{'IN-NATIONAL','IN-KA','tenant:closures','unit:<id>:closures'}`), `effective_from date`, `version`.

**wf.business_schedule_binding**: `tenant_id`, `scope text` (`tenant`, `unit`, `work_queue`), `scope_ref uuid NULL`, `schedule_id`; unique `(tenant_id, scope, scope_ref)`. Region defaults are platform settings (`workflow.calendar.region_default_schedule`), not rows.

**wf.sla_policy** (projection of the `sla_policy` artefact): `id`, `tenant_id`, `key`, `version_no`, `position int`, `conditions jsonb`, `metrics jsonb` (per metric: `target`, `basis`, `warn_at` array, `breach_actions`), `pause_conditions jsonb`, `artefact_version_id`.

**wf.sla_clock**: `id`, `tenant_id`, `subject_kind` (`task`, `stage`, `case`, `filing`, `transcription_job`), `subject_id`, `case_id NULL`, `policy_id`, `metric`, `schedule_id NULL`, `started_at`, `target_at`, `paused_total interval`, `paused_since timestamptz NULL`, `warn_level smallint`, `status` (`running`, `paused`, `met`, `breached`, `cancelled`), `met_at NULL`, `breached_at NULL`, `explanation jsonb`, `version`. Index `(tenant_id, status, target_at)` for the breach radar.

#### Example SLA policy

```json
{
  "key": "secretariat_scrutiny", "position": 10,
  "conditions": { "all": [ { "expr": "case.procedureFamily == 'arbitration'" }, { "expr": "case.priority != 'urgent'" } ] },
  "metrics": {
    "task_completion": { "taskTemplates": ["scrutinise_case"], "target": "P2D", "basis": "business_days",
                         "warnAt": [0.5, 0.9],
                         "breachActions": [ { "kind": "escalate" }, { "kind": "notify", "to": { "roles": ["unit_admin"] } } ] }
  },
  "pause": [ "case.status == 'suspended'", "task.state == 'waiting_on_external'" ]
}
```

<!-- section:rationale -->
## Rationale and source

- Institutions report on and are judged by timeliness: SEBI-recognised ODR institutions follow timelines set in SEBI's ODR circulars (assumption: the specific timelines and whether they are calendar or business days must be confirmed by legal from the current master circular), arbitral institutions publish case-handling targets, and CORD tenants sign SLAs with their clients.
- Procedural deadlines and internal SLAs are often confused in case management tools; mixing them leads either to staff targets moving a party's legal deadline or to holidays of the wrong place being skipped. Keeping two clocks with different calendars avoids both.
- The pattern of SLA policies applied in list order, with targets measured in business or calendar hours against a business schedule with holidays, is well established in help-desk tools [R1][R2]; we adopt it for internal targets and keep procedural deadlines on seat calendars.
- Using Temporal timers for both clocks follows the guardrail in [[WF-workflow-engine#guardrails]] that legal timers never live in BullMQ delayed jobs.

<!-- section:acceptance -->
## Acceptance criteria

- **SLA-AC-1 Business-day target.** Given unit "Singapore office" has a schedule Mon–Fri 09:00–18:00 `Asia/Singapore` with calendar `SG`, and policy `secretariat_scrutiny` with target 2 business days, when a `scrutinise_case` task is created on Friday 16:00 before a Monday public holiday, then `target_at` is Wednesday 16:00 SGT and the explanation lists the skipped weekend and holiday.
- **SLA-AC-2 Most specific schedule.** Given a tenant schedule and a different unit schedule, when a task is created for a case in that unit and the task is in a queue without its own binding, then the unit schedule is used; when the queue has a binding, the queue schedule is used.
- **SLA-AC-3 Pause.** Given a running clock with 10 business hours remaining, when the case is suspended for 3 days and then resumed, then the clock shows `paused` during suspension and resumes with 10 business hours remaining; the pause is listed in the clock history.
- **SLA-AC-4 Warning and breach.** Given `warnAt [0.5, 0.9]`, when 50% and 90% of the target elapse, then `sla.warning` events with levels 1 and 2 are emitted once each; when the target passes, `sla.breached` is emitted, the clock is `breached` and the task escalates to the next level.
- **SLA-AC-5 Procedural deadline uses seat calendar.** Given a case seated in Mumbai with seat calendars `IN-NATIONAL, IN-MH` and a unit business schedule in Bengaluru, when the response window of 30 calendar days with roll-forward starts, then the due time is computed on the seat calendars and time zone, not on the unit schedule, and `case_deadlines` stores the calendar versions.
- **SLA-AC-6 Stay.** Given a running procedural deadline with 12 days remaining, when the tribunal stays proceedings, then the deadline is `stayed` with 12 days remaining; when proceedings resume on date R, the new due time is R plus 12 days under the same conventions and a `case_deadline_changes` row records both events.
- **SLA-AC-7 Calendar change does not move a procedural deadline.** Given a computed deadline, when a new public holiday is added to `IN-MH` that falls inside the window, then the deadline is not changed and the case appears on the "deadlines affected by calendar change" list for the case manager.
- **SLA-AC-8 Negative: SLA cannot be edited per case.** When a case manager tries to change an SLA target on one case, then the API returns 403 `setting-not-case-overridable` and nothing changes.
- **SLA-AC-9 Negative: BullMQ delay refused.** When code registers a BullMQ job with a delay used as a legal deadline, then registration validation fails in CI (maximum delay rule in [[ADR-workflow-engine#confirmation]]).
- **SLA-AC-10 First matching policy.** Given two policies whose conditions both match a task, when the task is created, then only the policy with the lower `position` applies.

<!-- section:verification -->
## Verification method

| Method | Where |
|---|---|
| Unit and property tests of business-hours arithmetic (DST changes for US schedules, multiple intervals per day, holidays on weekends, midnight boundaries) | `packages/calendars/test/business-hours.spec.ts` |
| Temporal time-skipping tests for warnings, breach, pause and resume, stays | `packages/workflow-templates/test/sla-clock.workflow.spec.ts` |
| Golden deadline tests per tenant blueprint with explanations compared to approved fixtures (legal sign-off on SEBI ODR fixtures) | `fixtures/deadlines/*.json` run in CI |
| End-to-end Playwright: create task, fast-forward in a sandbox test run with compressed time ([[WF-workflow-simulation]]), see warning badge and escalation | `apps/web/e2e/secretariat/sla.spec.ts` |
| Inspection: settings catalogue rows for `workflow.sla.*` and `workflow.calendar.*` match the registry | CI registry check ([[PKG-settings-cases-and-workflows#testing]]) |

<!-- section:priority -->
## Priority

**Must**, phased:

| Phase | Scope |
|---|---|
| 3 (first domain slice) | Procedural deadlines with seat calendars (SLA-FR-7, 8, 9, 11); one tenant business schedule; task due times |
| 4 (extended domain) | SLA policies, schedule bindings per unit and queue, pause, warnings, breach actions (SLA-FR-1 to 6, 10) |
| 5 | SLA reporting per tenant contract (SLA-FR-12), queue-level schedules, transcript turnaround metric |

<!-- section:questions -->
## Open questions

- [ ] Assumption: SEBI ODR timelines (for example conciliation and arbitration completion periods) are counted as calendar days and are fixed by the circular, so they are procedural deadlines in a locked decision table, not tenant SLAs. To be confirmed by legal. (Legal)
- [ ] Should partial-day closures (for example a half-day before a festival) be supported in business schedules? Proposed: yes, as closure intervals. (Product)
- [ ] Do parties see SLA targets (for example "the secretariat aims to review your filing within 2 business days")? Proposed: optional per policy with plain-language copy. (Product, content)
- [x] Business-schedule tables (`wf.business_schedule` and bindings) are owned here and consumed by key by the calendars package (decision D13: [[PKG-calendars-and-deadline]] owns calendar computation (seat calendars, business-day arithmetic); [[WF-sla-and-business-calendars]] owns the configuration of business schedules and SLA policies).
- [ ] Platform SLAs owed by Nomology to tenants (uptime, support response) are out of scope here and belong to [[RPT-platform-performance]]; confirm that no tenant contract expects them in the same report. (Commercial)

<!-- section:notes -->
## Notes

- Pattern borrowed from: SLA policies with ordered conditions, business-hours or calendar-hours targets and pausable metrics, and schedules with time zones and holidays [R1][R2]. Our difference: procedural deadlines are a separate clock on seat calendars.
- Settings that drive this node: `workflow.sla.*` and `workflow.calendar.*` in [[PKG-settings-cases-and-workflows#catalogue]].
- Admin routes: `/admin/workflows/sla-policies`, `/admin/workflows/calendars` ([[WF-workflow-authoring-studio#routing]]).
- Permissions: `workflow.sla_policy:update`, `workflow.sla_policy:publish`, `workflow.calendar:update`; audit events `admin.sla.published`, `admin.calendar.updated`, `admin.calendar.binding_changed`.

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Yes. Without it, internal targets and legal deadlines would be computed on the wrong calendars, SEBI ODR and institutional timeliness could not be reported, and escalation would have no trigger.

<!-- check:unambiguous -->
### Unambiguous

The two clock kinds are defined side by side with source, calendar, storage and change rules; schedule precedence (queue, unit, tenant, region) and policy precedence (first match by position) are explicit; acceptance criteria give exact expected instants.

<!-- check:singular -->
### Singular

This node deliberately groups one capability (time measurement for workflows) into numbered requirements SLA-FR-1 to 12; each acceptance criterion tests one of them. If reviewers prefer strict single-requirement nodes, SLA-FR-7/8/9 (procedural) can split into a child.

<!-- check:complete -->
### Complete and scoped

Covers definition (schedules, policies), binding, metrics, pause, warning, breach, procedural computation, stays, calendar changes, case-level overrides, evidence and reporting, plus the error case of a calendar not loaded far enough ahead (`CalendarNotLoadedError` from [[PKG-calendars-and-deadline]] fails the step to a configuration human task).

<!-- check:feasible -->
### Feasible

Uses existing pieces: `computeDeadline` and snapshots in the calendars package, Temporal timers in the interpreter, `case_deadlines` in the cases schema; the new tables are small.

<!-- check:verifiable -->
### Verifiable

Each requirement has a Given/When/Then criterion including negatives (SLA-AC-8, SLA-AC-9); tests are named with their locations; golden deadline fixtures are signed off by legal.

<!-- check:consistent -->
### Consistent

Agrees with [[ADR-workflow-engine]] (legal timers in Temporal), [[PKG-calendars-and-deadline]] (calendar changes do not move computed deadlines), [[DOM-cases-schema]] (`case_deadlines` statuses including `stayed`) and the shared-model scopes (region, tenant, unit; case only for overridable deadline extensions).

<!-- check:traced -->
### Traced

Sources: tenant contracts and institutional rules; SEBI ODR circulars (assumption pending legal confirmation); help-desk SLA patterns [R1][R2]. Forward trace: [[PKG-calendars-and-deadline]], [[WF-human-tasks]], [[WF-process-definition-model]], tests listed under Verification.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "SLA policies are applied in list order; targets can use calendar hours or business hours; pausable metrics stop while a ticket is pending.",
    "id": "R1",
    "kind": "vendor",
    "title": "Zendesk help: Defining SLA policies",
    "url": "https://support.zendesk.com/hc/en-us/articles/4408829459866-Defining-SLA-policies",
    "vendor": "Zendesk"
  },
  {
    "excerpt": "Schedules have a time zone and holidays; SLA policies based on business hours measure only scheduled hours.",
    "id": "R2",
    "kind": "vendor",
    "title": "Zendesk help: Setting your schedule with business hours and holidays",
    "url": "https://support.zendesk.com/hc/en-us/articles/4408842938522-Setting-your-schedule-with-business-hours-and-holidays",
    "vendor": "Zendesk"
  }
]
```

<!-- end -->
