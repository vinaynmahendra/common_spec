---
id: "PKG-settings-cases-and-workflows"
title: "Case and workflow settings"
parent: "PKG-settings-catalogue"
order: 5
type: "feature"
template: "config"
status: "draft"
owner: null
indicative: false
summary: "Catalogue of every case and workflow setting (intake, references, procedure, deadlines, calendars, tasks, SLAs, authoring, publishing, migration, automation, simulation, runtime bounds) with scopes, locks, plans, permissions, timing and audit class"
links: []
rev: 1
syncHash: "deca6e16fe0d52dc"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.7.3.5 Case and workflow settings

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Catalogue of every case and workflow setting (intake, references, procedure, deadlines, calendars, tasks, SLAs, authoring, publishing, migration, automation, simulation, runtime bounds) with scopes, locks, plans, permissions, timing and audit class

<!-- section:purpose -->
## Purpose and scope

This catalogue registers every setting in the `case` and `workflow` domains: how cases are opened, referenced and run; deadlines and calendars; human tasks and queues; SLAs; workflow authoring, publishing, versioning and migration; automation rules; simulation; and the platform's runtime bounds for workflows.

Consumed by: [[DOM-cases]] (intake, references, case-level overrides), [[WF-process-definition-model]] and [[PKG-workflow-templates]] (blueprint interpretation), [[WF-human-tasks]], [[WF-sla-and-business-calendars]], [[PKG-calendars-and-deadline]], [[WF-workflow-versioning]], [[WF-automation-rules]], [[WF-workflow-simulation]], [[WF-workflow-authoring-studio]], [[PKG-rules-and-decision-engine]] and [[PKG-forms-and-form-builder]]. Values are resolved by `@nomology/settings` using the rules in [[PKG-configuration-scope-hierarchy]]; this node does not restate behaviour, it registers keys.

**Not settings here:**

| Item | Where it lives |
|---|---|
| Blueprint content (stages, steps, forms, decision tables, templates) | Configuration artefacts with their own lifecycle ([[WF-process-definition-model]]); a blueprint may carry `case_type`-scope overrides of the settings below |
| Notification channels, quiet hours, digest preferences | [[PKG-settings-notifications]], [[PKG-settings-personal]] |
| AI step enablement and models | [[PKG-settings-ai]], [[AI-tenant-ai-policy]] |
| Retention periods of case data | [[PKG-settings-data-and-privacy]] |
| Who may do what (roles, permission sets) | [[PKG-settings-access-control]], [[PKG-roles-and-permission-sets]] |
| Temporal namespaces, worker counts, queue concurrency | Deployment configuration ([[FND-environment-management]], [[INF-temporal]]) |
| Release flags for new step types | [[PKG-feature-flags]] |

<!-- section:scopes -->
## Scopes that apply

| Scope | Used | Administered by | Notes |
|---|---|---|---|
| `platform` | yes | `platform_owner`, `platform_admin` | Hard bounds (limits, chain depth, minimum intervals) and defaults |
| `region` | yes | `regional_ops` | Default business schedule and holiday calendars per region; legally driven defaults (for example India DLT-registered notice templates are handled in notification settings, not here) |
| `offering` | yes | `platform_admin` | CORD versus TERES defaults (for example party self-filing on for CORD); offering-locked regulator components |
| `tenant` | yes | `tenant_admin`, `workflow_designer` (workflow keys), `security_admin` not involved | Most keys |
| `unit` | yes | `unit_admin` | Calendars, queues, reference series, some task defaults |
| `case_type` | yes | `workflow_designer` through the blueprint's `settingsOverrides` | Pinned with the blueprint version |
| `case` | limited | `secretariat` with `case_manager` role on the case | Only keys marked case-overridable; changes need a reason and are audited |
| `user` | limited | The user | Only task delegation and inbox defaults listed in group J; other personal preferences are in [[PKG-settings-personal]] |

<!-- section:catalogue -->
## Settings catalogue

Column legend: **Scopes** lists where a value may be set (P platform, R region, O offering, T tenant, U unit, CT case type, C case, Usr user). **Lock**: whether a higher scope can force the value downward. **Plan**: entitlement from [[BIL-plans-entitlements-and-usage]] (`all` = every plan). **Takes effect**: `immediate`, `new cases`, `next stage`, `next evaluation`, `next publish`, `next sign-in`. **Audit**: `standard`, `sensitive` (notifies tenant owners), `maker-checker` (second approver required, [[PKG-separation-of-duties]]).

#### A. Case types and intake

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `case.intake.enabled_case_types` | list of case-type keys | all published | T, U | yes | all | `settings.cases:write` | immediate (new filings) | standard |
| `case.intake.party_self_filing` | bool | CORD: true; TERES: false | O, T, CT | yes | all | `settings.cases:write` | immediate | sensitive |
| `case.filing.max_upload_mb` | int 1–2,048 (platform bound; region may lower; tenant value ≤ entitlement `limit.upload_mb`) | 200 | P, R, T, U, CT | yes | `limit.upload_mb` | `settings.cases:write`; platform and region: `settings.platform:write` | new uploads | standard |
| `case.intake.counsel_filing` | bool | true | O, T, CT | yes | all | `settings.cases:write` | immediate | standard |
| `case.intake.require_kyc_before_submit` | enum `none`, `claimant`, `all_parties` | `none` | R, T, CT | yes | `standard` and `enterprise` | `settings.cases:write` | new cases | sensitive |
| `case.intake.draft_expiry_days` | int 7–365 | 90 | P, T | yes | all | `settings.cases:write` | immediate | standard |
| `case.intake.aggregator_auto_register` | bool | false | O, T, CT | yes | `enterprise` | `settings.cases:write` | new cases | maker-checker |
| `case.intake.duplicate_check` | enum `off`, `warn`, `block` | `warn` | T, CT | no | all | `settings.cases:write` | immediate | standard |
| `case.intake.max_parties` | int 2–200 | 20 | P, T, CT | yes | all | `settings.cases:write` | new cases | standard |

#### B. Case references and identity

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `case.reference.format` | pattern string (tokens `{prefix}`, `{yyyy}`, `{seq:6}`, `{unit}`, `{type}`) | `{prefix}/{yyyy}/{seq:5}` | T, U, CT | yes | all | `settings.cases:write` | new cases | sensitive |
| `case.reference.prefix` | string 1–12 `[A-Z0-9-]` | tenant short code | T, U | no | all | `settings.cases:write` | new cases | standard |
| `case.reference.reset_period` | enum `never`, `yearly` | `yearly` | T | no | all | `settings.cases:write` | next period | sensitive |
| `case.reference.assign_on` | enum `submit`, `register` | `register` | T, CT | yes | all | `settings.cases:write` | new cases | standard |
| `case.reference.show_external_reference` | bool | true for SEBI ODR blueprint | T, CT | no | all | `settings.cases:write` | immediate | standard |

#### C. Procedure and lifecycle

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `case.procedure.default_language` | BCP 47 | tenant default locale | T, CT, C | no | all | `settings.cases:write`; case: `case:configure` | new cases; case: immediate | standard |
| `case.procedure.allowed_languages` | list BCP 47 | tenant locales | T, CT | yes | all | `settings.cases:write` | new cases | standard |
| `case.procedure.default_confidentiality` | enum `standard`, `confidential`, `sealed` | `standard` | T, CT, C | yes | all | `settings.cases:write`; case: `case:configure` | new cases; case: immediate | sensitive |
| `case.procedure.allow_stage_skip` | bool | false | T, CT | yes | all | `settings.cases:write` | next stage | maker-checker |
| `case.procedure.stage_skip_requires_reason` | bool | true (locked true at P) | P | yes | all | `settings.platform:write` | immediate | sensitive |
| `case.procedure.party_timeline_detail` | enum `stages`, `stages_and_deadlines`, `full` | `stages_and_deadlines` | T, CT | no | all | `settings.cases:write` | immediate | standard |
| `case.procedure.suspension_stays_deadlines` | bool | true | O, T, CT | yes | all | `settings.cases:write` | new cases | maker-checker |
| `case.procedure.withdrawal_before_constitution_by_claimant` | bool | true | T, CT | yes | all | `settings.cases:write` | new cases | sensitive |

#### D. Deadlines and calendars

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `case.deadline.default_counting` | object `{excludeStartDay, rollIfNonWorking, dueAt}` | `{true, next_working_day, end_of_day}` | R, T, CT | yes | all | `settings.cases:write` | new cases (pinned) | maker-checker |
| `case.deadline.seat_calendar_source` | enum `seat`, `tenant_default` | `seat` | O, T, CT | yes | all | `settings.cases:write` | new cases | maker-checker |
| `case.deadline.reminder_offsets` | list of durations | `[P7D, P2D, PT24H]` | T, CT, C | no | all | `settings.cases:write`; case: `case.deadline:update` | next timer start | standard |
| `case.hearing.reminder_offsets` | list of ISO 8601 durations | `[P1D, PT1H]` | T, U, CT | no | all | `settings.cases:write` | hearings scheduled after the change | standard |
| `case.deadline.extension_requires_order` | bool | true | O, T, CT | yes | all | `settings.cases:write` | immediate | maker-checker |
| `case.deadline.max_extension_without_order` | duration | `P0D` | T, CT | yes | all | `settings.cases:write` | immediate | maker-checker |
| `case.deadline.calendar_change_review` | enum `list_for_review`, `notify_case_manager` | `list_for_review` | T | no | all | `settings.cases:write` | immediate | standard |
| `workflow.calendar.region_default_schedule` | schedule key | IN: Mon–Fri 09:30–18:00 `Asia/Kolkata` `IN-NATIONAL`; SG: Mon–Fri 09:00–18:00 `Asia/Singapore` `SG`; US: Mon–Fri 09:00–17:00 `America/New_York` `US-FEDERAL` | P, R | yes | all | `settings.platform:write` | immediate (service-level clocks) | sensitive |
| `workflow.calendar.tenant_default_schedule` | schedule key | region default | T | no | all | `workflow.calendar:update` | immediate (service-level clocks) | standard |
| `workflow.calendar.unit_schedule` | schedule key | tenant default | U | no | all | `workflow.calendar:update` | immediate (service-level clocks) | standard |
| `workflow.calendar.public_calendar_horizon_months` | int 12–36 | 18 | P | yes | all | `settings.platform:write` | immediate | standard |

#### E. Human tasks and queues

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `workflow.task.default_assignment_strategy` | enum `pull`, `round_robin`, `least_loaded`, `skills` | `pull` | T, U | no | all | `workflow.queue:configure` | new tasks | standard |
| `workflow.task.max_open_per_assignee` | int 1–500 | 50 | T, U | no | all | `workflow.queue:configure` | new tasks | standard |
| `workflow.task.claim_timeout_hours` | int 0–168 (0 = never) | 0 | T, U | no | all | `workflow.queue:configure` | new claims | standard |
| `workflow.task.reassign_requires_reason` | bool | true | T | yes | all | `settings.workflow:write` | immediate | standard |
| `workflow.task.allow_self_assign_from_queue` | bool | true | T, U | no | all | `workflow.queue:configure` | immediate | standard |
| `workflow.task.respect_ethical_walls` | bool | true (locked true at P) | P | yes | all | `settings.platform:write` | immediate | sensitive |
| `workflow.task.out_of_office_auto_reassign` | enum `off`, `to_delegate`, `to_queue` | `to_queue` | T, U | no | all | `workflow.queue:configure` | immediate | standard |
| `workflow.task.party_tasks_enabled` | bool | CORD: true; TERES: false | O, T, CT | yes | all | `settings.workflow:write` | new cases | standard |
| `workflow.task.escalation_max_levels` | int 1–5 | 3 | P, T | yes | all | `settings.workflow:write` | new tasks | standard |
| `workflow.task.completion_requires_step_up` | list of task template keys | `[]` | T, CT | no | all | `settings.workflow:write` | immediate | sensitive |

#### F. SLAs

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `workflow.sla.enabled` | bool | true | O, T | yes | `standard` and `enterprise` | `settings.workflow:write` | new clocks | standard |
| `workflow.sla.warning_thresholds` | list of fractions 0.1–0.99 | `[0.5, 0.75, 0.9]` | T, CT | no | all | `workflow.sla_policy:update` | new clocks | standard |
| `workflow.sla.default_basis` | enum `business_hours`, `business_days`, `calendar_hours`, `calendar_days` | `business_days` | T | no | all | `workflow.sla_policy:update` | new clocks | standard |
| `workflow.sla.pause_on_waiting_for_party` | bool | true | T, CT | no | all | `workflow.sla_policy:update` | new clocks | standard |
| `workflow.sla.breach_notify_roles` | list of role keys | `[unit_admin]` | T, U | no | all | `workflow.sla_policy:update` | immediate | standard |
| `workflow.sla.show_targets_to_parties` | bool | false | T, CT | no | all | `workflow.sla_policy:update` | immediate | standard |
| `workflow.sla.policy_publish_requires_approval` | bool | true | T | yes | all | `settings.workflow:write` | next publish | sensitive |

#### G. Authoring and publishing

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `workflow.authoring.enabled` | bool | true | O, T | yes | `standard` and `enterprise` (`starter` uses library blueprints only) | `settings.platform:write` | immediate | sensitive |
| `workflow.authoring.allowed_step_types` | list | all registered for the region's interpreter contract | P, O, T | yes | plan-dependent (`ai_step` needs `feature.ai.summaries`) | `settings.workflow:write` | next publish | standard |
| `workflow.authoring.max_steps` | int 10–500 | 200 | P, T | yes | all | `settings.platform:write` | next publish | standard |
| `workflow.authoring.max_parallel_branches` | int 1–10 | 5 | P | yes | all | `settings.platform:write` | next publish | standard |
| `workflow.authoring.max_subprocess_depth` | int 1–5 | 3 | P | yes | all | `settings.platform:write` | next publish | standard |
| `workflow.authoring.copilot_drafting` | bool | true where [[AI-tenant-ai-policy]] allows admin AI | T | yes | `feature.ai.summaries` | `settings.workflow:write` | immediate | sensitive |
| `workflow.publish.requires_approval` | bool | true (locked true for SEBI ODR and court blueprints) | O, T | yes | all | `settings.workflow:write` | next publish | maker-checker |
| `workflow.publish.procedural_change_approvers` | int 1–3 | 2 for SEBI ODR and court tenants; 1 otherwise | O, T | yes | all | `settings.workflow:write` | next publish | maker-checker |
| `workflow.publish.step_up_required` | bool | true (locked at P) | P | yes | all | `settings.platform:write` | immediate | sensitive |
| `workflow.publish.min_lead_time_hours` | int 0–720 | 0 | T, CT | no | all | `settings.workflow:write` | next publish | standard |
| `workflow.publish.notify_on_publish` | list of role keys | `[tenant_admin, unit_admin]` | T | no | all | `settings.workflow:write` | immediate | standard |

#### H. Versioning and migration

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `workflow.versioning.content_follows_latest` | map kind → bool (`notification_template`, `document_template`) | `{notification_template: false, document_template: false}` | O, T | yes | all | `settings.workflow:write` | next publish | maker-checker |
| `workflow.migration.enabled` | bool | false until tenant onboarding completes | O, T | yes | `enterprise` | `settings.workflow:write` | immediate | maker-checker |
| `workflow.migration.batch_size` | int 10–500 | 100 | P, T | yes | all | `settings.platform:write` | next plan run | standard |
| `workflow.migration.max_rate_per_min` | int 10–1,000 | 300 | P | yes | all | `settings.platform:write` | immediate | standard |
| `workflow.migration.max_cases_per_plan` | int 1–50,000 | 10,000 | P | yes | all | `settings.platform:write` | next plan | standard |
| `workflow.migration.require_legal_basis_from` | enum `structural`, `procedural` | `structural` | O, T | yes | all | `settings.workflow:write` | next plan | maker-checker |
| `workflow.migration.dry_run_max_age_hours` | int 1–72 | 24 | P | yes | all | `settings.platform:write` | immediate | standard |

#### I. Automation rules

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `workflow.automation.enabled` | bool | true | P, O, T | yes | all | `settings.workflow:write` | immediate | sensitive |
| `workflow.automation.max_rules` | int 0–1,000 | `starter` 25, `standard` 200, `enterprise` 1,000 | P, T | yes | plan-dependent | `settings.platform:write` | next publish | standard |
| `workflow.automation.max_actions_per_rule` | int 1–10 | 10 | P | yes | all | `settings.platform:write` | next publish | standard |
| `workflow.automation.max_executions_per_hour` | int | `starter` 500, `standard` 5,000, `enterprise` 50,000 | P, T | yes | plan-dependent | `settings.platform:write` | immediate | standard |
| `workflow.automation.max_chain_depth` | int 1–3 | 3 | P (bound), T (may lower) | yes | all | `settings.workflow:write` | immediate | standard |
| `workflow.automation.loop_threshold` | object `{executions, windowMin}` | `{10, 10}` | P | yes | all | `settings.platform:write` | immediate | standard |
| `workflow.automation.schedule_min_interval_min` | int 15–1,440 | 60 | P | yes | all | `settings.platform:write` | next publish | standard |
| `workflow.automation.publish_requires_approval` | bool | true | T | yes | all | `settings.workflow:write` | next publish | maker-checker |
| `workflow.automation.allowed_actions` | list of action kinds | all registered | O, T | yes | all | `settings.workflow:write` | next publish | sensitive |
| `workflow.automation.execution_log_retention_days` | int 30–365 | 90 | P, T | yes | all | `settings.workflow:write` | next daily purge | standard |

#### J. Simulation and user-level task preferences

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `workflow.simulation.min_branch_coverage_pct` | int 0–100 | 80 overall; procedural gateways always 100 (locked at P) | P, O, T | yes | all | `settings.workflow:write` | next submit | sensitive |
| `workflow.simulation.required_scenarios_min` | int 0–50 | 3 | O, T | yes | all | `settings.workflow:write` | next submit | standard |
| `workflow.simulation.history_replay_max_cases` | int 0–2,000 | 500 | P, T | yes | `enterprise` | `settings.platform:write` | immediate | standard |
| `workflow.simulation.sandbox_time_scale` | int 60–1,440 (seconds of virtual time per real second) | 1,440 (1 day per minute) | P, T | yes | all | `settings.workflow:write` | next run | standard |
| `workflow.task.out_of_office_delegate` | membership ID or null | null | Usr | no | all | own user | immediate | standard |
| `workflow.task.inbox_default_view` | enum `mine`, `my_queues`, `team` | `mine` | T, Usr | no | all | own user | next sign-in | standard |

#### K. Platform runtime bounds (not tenant-editable)

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `workflow.runtime.continue_as_new_events` | int 500–10,000 | 2,000 | P | yes | — | `settings.platform:write` | next run segment | sensitive |
| `workflow.runtime.config_failure_task_queue` | queue key | `secretariat` | P, T | no | all | `settings.workflow:write` | immediate | standard |
| `workflow.runtime.bulk_start_rate_per_tenant` | int per minute | 600 | P, R | yes | — | `settings.platform:write` | immediate | sensitive |
| `workflow.runtime.supported_interpreter_contracts` | list | `["interp/2"]` | P, R | yes | — | `settings.platform:write` | immediate | sensitive |

Case-overridable keys (scope `C`): `case.procedure.default_language`, `case.procedure.default_confidentiality`, `case.deadline.reminder_offsets`. Every case-level change needs a reason and writes `admin.settings.case_override_set`.

<!-- section:validation -->
## Validation and dependencies

Rules between settings (checked by the resolver at save time and shown inline with the conflicting key):

- `case.intake.aggregator_auto_register = true` requires the case type's blueprint to have an automatic scrutiny path and `case.reference.assign_on = register`.
- `case.intake.party_self_filing = true` requires a published intake form that passes accessibility checks for the case type ([[PKG-forms-and-form-builder]]).
- `case.deadline.extension_requires_order = false` is refused while `workflow.publish.procedural_change_approvers ≥ 2` (court and SEBI ODR profiles), because those tenants must evidence orders.
- `workflow.migration.enabled = true` requires `workflow.publish.requires_approval = true`.
- `workflow.automation.max_chain_depth` at tenant cannot exceed the platform value (hard bound).
- `workflow.task.max_open_per_assignee` must be ≥ the largest `capacity` set on any queue member in that unit.
- `workflow.sla.warning_thresholds` must be strictly increasing and below 1.0.
- `workflow.authoring.allowed_step_types` cannot remove a step type used by a published blueprint version in the tenant; the admin sees the list of affected case types.
- `workflow.calendar.*` schedules must reference calendars loaded at least 12 months ahead (`CalendarNotLoadedError` otherwise).

Platform hard bounds (never exceeded by any tenant): `workflow.authoring.max_steps ≤ 500`, `max_parallel_branches ≤ 10`, `max_subprocess_depth ≤ 5`, `automation.max_actions_per_rule ≤ 10`, `automation.max_chain_depth ≤ 3`, `automation.schedule_min_interval_min ≥ 15`, `migration.max_cases_per_plan ≤ 50,000`; `case.procedure.stage_skip_requires_reason`, `workflow.task.respect_ethical_walls` and `workflow.publish.step_up_required` are locked true.

An invalid change returns problem type `setting-validation-failed` with each failed rule; the console shows them next to the fields.

<!-- section:defaults -->
## Defaults by tenant type

| Key | Arbitral institution | SEBI ODR institution | CORD tenant | Court or government programme |
|---|---|---|---|---|
| `case.intake.party_self_filing` | false | true (investors file directly) | true | true |
| `case.intake.aggregator_auto_register` | false | true for MII-routed matters (assumption, confirm with NSE format) | false | false |
| `case.intake.require_kyc_before_submit` | `none` | `claimant` (assumption, to be confirmed by legal) | `none` | `all_parties` |
| `case.reference.show_external_reference` | false | true | false | true |
| `case.procedure.party_timeline_detail` | `stages_and_deadlines` | `full` | `full` | `stages_and_deadlines` |
| `case.deadline.extension_requires_order` | true | true (locked at offering by the SEBI ODR blueprint) | false | true |
| `workflow.task.party_tasks_enabled` | false | true | true | true |
| `workflow.sla.show_targets_to_parties` | false | true | true | false |
| `workflow.publish.procedural_change_approvers` | 1 | 2 | 1 | 2 |
| `workflow.versioning.content_follows_latest.notification_template` | false | false | true | false |
| `workflow.migration.enabled` | true (`enterprise`) | false until legal approves | false | false |
| `workflow.simulation.min_branch_coverage_pct` | 80 | 100 | 80 | 100 |
| `workflow.automation.publish_requires_approval` | true | true | false | true |

Why they differ: SEBI ODR and court programmes carry regulatory or public-law obligations and unrepresented parties, so they default to stricter approvals, full party timelines and locked deadline rules; CORD tenants are smaller teams with consumer parties, so faster publishing with content following latest copy; arbitral institutions are counsel-driven and rely on secretariat filing.

<!-- section:admin_ux -->
## Where it is administered

| Group | Console location | API |
|---|---|---|
| A–D | Tenant admin console → Cases → Intake, References, Procedure, Deadlines (`/admin/settings/cases`) | `PATCH /admin/v1/settings/case.*` |
| D calendars, E, F | Workflows → Calendars, Queues, SLA policies (`/admin/workflows/calendars`, `/queues`, `/sla-policies`) | `PATCH /admin/v1/settings/workflow.calendar.*`, `workflow.task.*`, `workflow.sla.*` |
| G–J | Workflows → Settings (`/admin/workflows/settings`) | `PATCH /admin/v1/settings/workflow.*` |
| `case_type` overrides | Studio → version → Settings tab ([[WF-workflow-authoring-studio#routing]]) | Part of the blueprint body; changes follow the blueprint lifecycle |
| `case` overrides | Secretariat console → case → Settings drawer (only overridable keys) | `PATCH /admin/v1/cases/{caseId}/settings/{key}` |
| K | Platform console → Workflows runtime (`/platform/settings/workflow`) | `/platform/v1/settings/workflow.runtime.*` |

Every field shows the effective value, its source scope ("Inherited from: SEBI ODR offering") and a lock icon when a higher scope enforces it. The admin copilot ([[APP-admin-copilot]]) may propose changes to these keys as a draft change set with a diff and explanation; it cannot apply them.

<!-- section:change_control -->
## Change control and audit

- **Maker-checker** keys (marked above) need a second approver who is not the author, via [[PKG-configuration-lifecycle]]; the change set shows old value, new value, scope and affected case types.
- **Sensitive** keys notify tenant owners and the unit admins of affected units on publish.
- Rollback publishes the previous value set as a new change, in one action, audited as `admin.settings.rolled_back`.
- Audit record (`admin.settings.published`): key, scope, scope reference, old value, new value, actor (human or `ai_agent` proposer plus approving human), reason, change-set ID, request ID.
- Changes to keys with "new cases" timing are pinned at case start (shared-model rule 5); the change history view shows which cases started under which value.

<!-- section:migration -->
## Versioning and migration

- Keys are never reused; renames keep an alias for two releases, and the resolver logs alias reads.
- A changed platform default applies only to tenants still inheriting it; tenants with an explicit value are listed in release notes ([[DEP-release-notes-and-change]]).
- Settings with "new cases" timing are pinned in `config.case_config_pin` with the blueprint, so later changes cannot alter running cases; migration of a case to a new blueprint version ([[WF-workflow-versioning]]) re-pins `case_type` overrides from the target version but keeps tenant-level values pinned at case start unless the plan says otherwise.
- All non-platform keys travel in configuration packages ([[PKG-configuration-packages]]); tenant blueprints (for example "SEBI ODR institution blueprint") set the defaults in the table above.

<!-- section:testing -->
## Testing

- The registry `packages/settings/registry/case.ts` and `workflow.ts` is the source of truth; CI generates the catalogue table from it and fails if this node and the registry disagree (key, type, default, scopes, lock, permission, timing, audit class).
- Resolution tests per key: platform default, region override, offering lock, tenant value, unit value, case-type override, case override where allowed; lock blocks lower values; plan entitlement hides tenant control outside the plan.
- Validation rule tests for every rule listed under Validation, including the negative case.
- Pinning test: a case started under `case.deadline.default_counting` A keeps A after the tenant changes it to B.

<!-- section:questions -->
## Open questions

- [x] Plan tiers now use the names in [[BIL-plans-entitlements-and-usage]] (`starter`, `standard`, `enterprise`; decision D11); the numbers remain placeholders to align with [[BIL-plans-entitlements-and-usage]]. (Billing)
- [ ] Should unit admins be able to change `case.reference.format` for their unit, or only the prefix? (Product)
- [ ] KYC-before-submit for SEBI ODR claimants is an assumption; confirm with legal against current SEBI ODR circulars and the MII process. (Legal)
- [ ] Is `case.procedure.default_confidentiality = sealed` allowed at case scope without a tribunal order? (Legal)
- [ ] Region default schedules (working hours) need confirmation from regional operations. (Regional ops)

<!-- section:notes -->
## Notes

- Pattern borrowed from: tiered system properties with locks in enterprise platforms; per-plan automation limits similar to service limits in work-management tools.
- Keys in this catalogue use domains `case` and `workflow` only, as the shared naming convention requires.

<!-- checks -->
## Template checks

<!-- check:inheritance -->
### Inheritance and locks

Every key lists its scopes and lockability; resolution is the shared rule from [[PKG-configuration-scope-hierarchy]] with no exceptions; `case_type` values come only from the pinned blueprint version and `case` values only for the three overridable keys. The console shows effective value, source and lock. When a higher scope locks a key, existing lower values are frozen (kept for history, ignored by the resolver) and the admin sees how many tenants or units are affected before confirming.

<!-- check:permissions -->
### Who may change what

Each key names one permission: `settings.cases:write` and `settings.workflow:write` for tenant keys, narrower `workflow.calendar:update`, `workflow.queue:configure`, `workflow.sla_policy:update` for operational groups that unit admins hold within their units, `settings.platform:write` for platform bounds, and `case:configure` / `case.deadline:update` with the case-manager role for case overrides.

<!-- check:safety -->
### Safe bounds

Hard bounds and locked-true keys prevent unsafe combinations (stage skip without reason, ignoring ethical walls, publishing without step-up); validation rules stop combinations that would weaken procedural evidence; procedural values are pinned to cases; regulator-driven values are locked at offering scope for SEBI ODR blueprints.

<!-- check:timing -->
### When changes take effect

The "Takes effect" column states timing per key; "new cases" keys are pinned at case start; service-level calendar changes apply to running clocks on the next tick; procedural deadlines never move on a settings change.

<!-- check:audit -->
### Audit and rollback

Every change emits `admin.settings.published` with old and new value, scope, actor, approver and reason into the hash-chained audit log; point-in-time values are reconstructed from the settings version history ([[PKG-settings-data-model]]); rollback is one approved action.

<!-- check:sync -->
### Catalogue matches code

The catalogue is generated from the code registry and compared in CI; adding a key without a catalogue row fails the build.

<!-- end -->
