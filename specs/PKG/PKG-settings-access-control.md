---
id: "PKG-settings-access-control"
title: "Access control settings"
parent: "PKG-settings-catalogue"
order: 1
type: "feature"
template: "config"
status: "draft"
owner: null
indicative: false
summary: "Settings catalogue for authorisation: custom role bounds, assignment expiry, JIT, break-glass, access requests, separation of duties, case visibility, ethical walls, access reviews, non-human principals and the explainer, with defaults per tenant blueprint"
links: []
rev: 1
syncHash: "06654b3738a81c02"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.7.3.1 Access control settings

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Settings catalogue for authorisation: custom role bounds, assignment expiry, JIT, break-glass, access requests, separation of duties, case visibility, ethical walls, access reviews, non-human principals and the explainer, with defaults per tenant blueprint

<!-- section:purpose -->
## Purpose and scope

Settings that tune authorisation behaviour for a platform, region, tenant, unit, case type or case: custom role limits, assignment expiry, just-in-time elevation, break-glass, access requests, separation of duties, who sees what inside a case, ethical walls, access reviews, non-human principals, and the access explainer.

Consumed by: [[PKG-roles-and-permission-sets]], [[PKG-jit-and-break-glass]], [[PKG-separation-of-duties]], [[PKG-rbac-abac-case-level-party]], [[PKG-policy-engine-permission-matrix]], [[PKG-ethical-walls-conflict-based]], [[SEC-access-reviews]], [[PKG-non-human-principals]], [[PKG-access-explainer]] and the screens in [[APP-user-and-access-admin]].

Not here:
- The roles, permission sets and assignments themselves. They are configuration objects with their own lifecycle and travel in configuration packages, not settings.
- Authentication (MFA, session length, SSO, IP rules): [[PKG-settings-security-and-identity]].
- Support access consent and durations: [[PKG-support-access-and-impersonation]] and [[PKG-settings-platform-operations]].
- AI feature switches: [[PKG-settings-ai]] (this catalogue only bounds AI agent *permissions*).
- Case procedure (deadlines, stages): [[PKG-settings-cases-and-workflows]]. Keys under `access.case.*` here decide visibility and participation rights only.
- Release flags ([[PKG-feature-flags]]) and secrets ([[FND-environment-management]]).

Existing setting names in older nodes are replaced: `award.scrutinyVisibleToSecretariat` → `access.case.secretariat_sees_tribunal_drafts`; `case.readAfterCloseDays` → `access.case.read_after_close_days`; `recordingsToParties` → `access.case.recordings_to_parties`; `partiesPrepareBundles` → `access.case.parties_prepare_bundles`; `publicFiling` → `case.intake.party_self_filing` (owned by [[PKG-settings-cases-and-workflows]]).

<!-- section:scopes -->
## Scopes that apply

| Scope | Used | Administered by | Notes |
|---|---|---|---|
| `platform` | yes | platform_owner, platform_security | Hard bounds and locked minimums (for example maker-checker catalogue minimum) |
| `region` | yes | regional_ops (with platform_security) | Tightening only, for example India SEBI-programme tenants default to stricter JIT |
| `offering` | yes | platform_admin | CORD and TERES defaults differ (self-service explanations, party recordings) |
| `tenant` | yes | security_admin, tenant_owner (`settings.access:write`); tenant_admin reads only | Main level |
| `unit` | yes, selected keys | unit_admin may *tighten* only selected keys; loosening requires tenant scope | For example a unit with stricter review frequency |
| `case_type` | yes, `access.case.*` keys | workflow_designer with security_admin as checker | Visibility rules that belong to a procedure, pinned to cases at start |
| `case` | yes, a few `access.case.*` keys marked case-overridable | case_manager (`case:configure`) | For example a tribunal order to let parties see recordings |
| `user` | no | — | Access rules are never a personal preference |

<!-- section:catalogue -->
## Settings catalogue

Permission to change is `settings.access:write` unless stated; platform and region rows need `settings.platform:write`. Audit classes: `std` standard, `sens` sensitive, `mc` maker-checker ([[PKG-separation-of-duties]]). "Pinned" means the value is fixed on the case at start ([[PKG-configuration-scope-hierarchy]] rule 5).

**Roles and assignments**

| Key | Type | Default | Scopes | Lockable | Plan | Takes effect | Audit |
|---|---|---|---|---|---|---|---|
| `access.roles.custom_roles_enabled` | bool | true | platform, offering, tenant | yes | `feature.custom_roles` | immediately | sens |
| `access.roles.max_custom_roles` | int 0–200 | 50 | platform, tenant | yes (platform ceiling 200) | plan | immediately | std |
| `access.roles.max_custom_permission_sets` | int 0–300 | 100 | platform, tenant | yes | plan | immediately | std |
| `access.roles.allow_muting` | bool | true | platform, tenant | yes | `feature.custom_roles` | next publish of a role | sens |
| `access.roles.allow_system_role_variants` | bool | false | platform, tenant | yes | `feature.custom_roles` | immediately | mc |
| `access.admin.case_content_in_admin_roles` | enum `allow`, `warn`, `block` | `warn` | platform, region, tenant | yes | all | next role publish | mc |
| `access.assignment.max_duration_days_privileged` | int 1–730 | 365 | platform, region, tenant, unit (tighten) | yes | all | new assignments | mc |
| `access.assignment.default_expiry_days_external` | int 1–730 or null | 180 | tenant, unit, case_type | no | all | new assignments | std |
| `access.assignment.allow_direct_permission_sets` | bool | false | platform, tenant | yes | `feature.custom_roles` | immediately | sens |
| `access.assignment.unit_scope_default_descendants` | bool | true | tenant | no | all | new assignments | std |
| `access.assignment.allow_tenant_scope_secretariat` | bool | true | tenant | no | all | new assignments | sens |
| `access.assignment.require_reason_for` | enum `privileged`, `sensitive_and_privileged`, `all` | `privileged` | platform, tenant | yes (minimum `privileged`) | all | immediately | sens |
| `access.groups.scim_mappable_roles` | list of role keys | all non-privileged roles | tenant | no | `feature.sso` | next SCIM sync | mc |
| `access.groups.privileged_mapping_allowed` | bool | false | platform, tenant | yes | `feature.sso` | next SCIM sync | mc |
| `access.owners.minimum_count` | int 1–5 | 1 (2 recommended) | platform, tenant | yes (platform minimum 1) | all | immediately | mc |

**Just-in-time elevation and access requests**

| Key | Type | Default | Scopes | Lockable | Plan | Takes effect | Audit |
|---|---|---|---|---|---|---|---|
| `access.jit.enabled` | bool | true | platform, tenant | yes | all | immediately | mc |
| `access.jit.owner_standing_count` | int 1–5 | 2 | tenant | yes (platform floor 1) | all | immediately | mc |
| `access.jit.eligible_only_roles` | list of role keys | `security_admin`, `integration_admin`, `ai_admin` | platform (minimum), region, tenant | yes (platform minimum cannot be removed) | all | next assignment change; existing standing holders converted after 30 days' notice | mc |
| `access.jit.max_activation_minutes` | int 15–480 | 240 | platform (ceiling 480), tenant, unit (tighten) | yes | all | next activation | mc |
| `access.jit.require_approval_roles` | list of role keys | `security_admin` | platform, tenant | yes | all | next activation | mc |
| `access.jit.require_ticket_ref` | bool | false | tenant | no | all | next activation | std |
| `access.jit.approval_timeout_min` | int 10–1440 | 60 | tenant | no | all | next request | std |
| `access.jit.eligibility_valid_days` | int 30–730 | 365 | platform, tenant | yes | all | new eligibilities | sens |
| `access.requests.enabled` | bool | true | tenant | no | all | immediately | std |
| `access.requests.case_access_approver` | enum `case_manager`, `unit_secretariat_lead`, `either` | `either` | tenant, unit | no | all | next request | sens |
| `access.requests.max_duration_days` | int 1–365 or null | 90 | tenant, unit | no | all | next request | std |
| `access.denial.offer_request_link` | bool | true | tenant, offering | no | all | immediately | std |

**Break-glass**

| Key | Type | Default | Scopes | Lockable | Plan | Takes effect | Audit |
|---|---|---|---|---|---|---|---|
| `access.break_glass.enabled_profiles` | list (`emergency_case_access`, `emergency_tenant_admin`) | none | platform, tenant | yes | all | immediately | mc |
| `access.break_glass.case_access_holders` | enum `all_secretariat`, `listed_members` | `listed_members` | tenant | no | all | immediately | mc |
| `access.break_glass.listed_members` | list of membership ids | empty | tenant | no | all | immediately | mc |
| `access.break_glass.tenant_admin_holders` | list of membership ids (max 3) | empty | tenant | no | `feature.sso` | immediately | mc |
| `access.break_glass.duration_min` | int 15–120 | 120 (case), 60 (tenant admin) | platform (ceiling), tenant | yes | all | next invocation | mc |
| `access.break_glass.notify` | list of role keys | `tenant_owner`, `security_admin` (+ case manager) | platform (minimum), tenant | yes (minimum) | all | next invocation | sens |
| `access.break_glass.notify_sms` | bool | false | tenant | no | all | next invocation | std |
| `access.break_glass.review_days` | int 1–10 (working days) | 2 | platform (ceiling 10), tenant | yes | all | next invocation | sens |
| `access.break_glass.max_per_user_per_30d` | int 1–10 | 3 | platform, tenant | yes | all | immediately | sens |

**Separation of duties**

| Key | Type | Default | Scopes | Lockable | Plan | Takes effect | Audit |
|---|---|---|---|---|---|---|---|
| `access.sod.extra_maker_checker_operations` | list of catalogue operations | empty | tenant | no | all | new changes | mc |
| `access.sod.single_admin_fallback` | enum `block`, `owner_approves`, `delayed_self_approval` | per blueprint | platform, region, tenant | yes | all | new changes | mc |
| `access.sod.delayed_self_approval_hours` | int 24–168 | 24 | platform (minimum 24), tenant | yes | all | new changes | mc |
| `access.sod.toxic_combination_mode` | enum `warn`, `block` per system rule (map) | as rule defaults | platform (minimums), tenant | yes (per rule minimum) | all | next assignment | mc |
| `access.sod.custom_rules_enabled` | bool | true | tenant | no | `feature.custom_roles` | immediately | sens |
| `access.sod.finance_dual_approval_threshold` | money per currency | see Open questions | tenant | no | all | next approval | mc |
| `access.sod.exception_max_days` | int 1–90 | 90 | platform (ceiling 90), tenant | yes | all | new exceptions | mc |

**Case access and visibility** (`access.case.*`; case-type values are pinned at case start unless marked "running")

| Key | Type | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `access.case.secretariat_sees_tribunal_drafts` | bool | false | tenant, case_type | yes | all | `settings.access:write` | pinned | mc |
| `access.case.read_after_close_days` | int 0–3650 | 90 | tenant, case_type | no | all | `settings.access:write` | running | sens |
| `access.case.exchange_mode` | enum `on_filing`, `on_secretariat_release`, `per_rules` | `on_filing` | tenant, case_type | no | all | `settings.access:write` | pinned | mc |
| `access.case.recordings_to_parties` | bool | false | tenant, case_type, case | no | all | case: `case:configure` | running | sens |
| `access.case.transcripts_to_parties_on_release` | bool | true | tenant, case_type, case | no | `feature.transcription` | case: `case:configure` | running | sens |
| `access.case.parties_prepare_bundles` | bool | false | tenant, case_type, case | no | `feature.ebundling` | case: `case:configure` | running | std |
| `access.case.filing_on_behalf_enabled` | bool | true | tenant, case_type | no | all | `settings.access:write` | pinned | sens |
| `access.case.filing_on_behalf_notifies_party` | bool | true | platform (locked true for SEBI ODR blueprint), tenant | yes | all | `settings.access:write` | running | sens |
| `access.case.party_addressed_documents` | bool | false | case_type | no | all | `settings.access:write` | pinned | sens |
| `access.case.counsel_can_add_cocounsel` | bool | true | tenant, case_type | no | all | `settings.access:write` | running | std |
| `access.case.observer_default_expiry_days` | int 1–365 | 30 | tenant, case_type | no | all | `settings.access:write` | new assignments | std |
| `access.case.transcriber_access_window_hours` | int 1–720 | 72 after turnaround target | tenant, case_type | no | `feature.transcription` | `settings.access:write` | new assignments | std |
| `access.case.sealed_cases_need_to_know` | bool | true | platform, tenant | yes | all | `settings.access:write` | running | mc |
| `access.case.unit_owns_case_by` | enum `intake_unit`, `case_type_unit`, `manual` | `case_type_unit` | tenant | no | all | `settings.access:write` | new cases | sens |

**Ethical walls**

| Key | Type | Default | Scopes | Lockable | Plan | Takes effect | Audit |
|---|---|---|---|---|---|---|---|
| `access.walls.second_approver_rule` | enum `another_wall_approver`, `designated_officer` | `another_wall_approver` | tenant | no | all | next lift | mc |
| `access.walls.designated_officer` | membership id | null | tenant | no | all | next lift | mc |
| `access.walls.org_walls_enabled` | bool | true | tenant | no | all | immediately | sens |
| `access.walls.disclose_to_parties` | enum `never`, `after_challenge_decision`, `per_rules` | `per_rules` | tenant, case_type | no | all | pinned | sens |
| `access.walls.proposed_walls_deny` | bool | true | platform (locked true) | yes (locked) | all | — | — |
| `access.walls.require_acknowledgement` | bool | true | tenant | no | all | new walls | std |
| `access.walls.picker_hint_visible` | bool | true | tenant | no | all | immediately | std |

**Access reviews**

| Key | Type | Default | Scopes | Lockable | Plan | Takes effect | Audit |
|---|---|---|---|---|---|---|---|
| `access.review.enabled` | bool | true | tenant | no | all | next cycle | sens |
| `access.review.frequency` | enum `monthly`, `quarterly`, `half_yearly`, `annual` | `quarterly` | platform (maximum interval annual), tenant, unit (tighten) | yes | all | next cycle | sens |
| `access.review.population` | enum `privileged`, `all_staff`, `all_staff_and_external`, `all` | `all_staff` | tenant | no | all | next cycle | sens |
| `access.review.reviewer_rule` | enum `unit_admin`, `role_owner`, `manager_attribute`, `security_admin` | `unit_admin` | tenant | no | all | next cycle | sens |
| `access.review.duration_days` | int 5–30 | 10 | tenant | no | all | next cycle | std |
| `access.review.auto_remove_on_no_response` | bool | false | tenant | no | all | next cycle | mc |
| `access.review.include_non_human` | bool | true | platform (locked true for privileged) | yes | all | next cycle | sens |
| `access.review.inactive_days_flag` | int 30–365 | 90 | tenant | no | all | next cycle | std |

**Non-human principals and AI agents**

| Key | Type | Default | Scopes | Lockable | Plan | Takes effect | Audit |
|---|---|---|---|---|---|---|---|
| `access.nonhuman.max_lifetime_days` | int 30–730 | 365 | platform (ceiling), tenant | yes | `feature.public_api` | new principals | sens |
| `access.nonhuman.orphan_grace_days` | int 0–30 | 7 | tenant | no | all | immediately | sens |
| `access.nonhuman.disable_unused_days` | int 30–365 | 180 | tenant | no | all | nightly | sens |
| `access.ai_agent.allowed_permission_sets` | list of set keys | `ps.case.participant_read` subsets only | platform (allow-list), tenant | yes | `feature.ai.*` | next assignment | mc |
| `access.ai_agent.autonomous_max_scope` | enum `case`, `case_type`, `unit` | `case` | platform, tenant | yes | `feature.ai.*` | next assignment | mc |
| `access.ai_agent.on_behalf_max_hours` | int 1–8 | 8 | platform (ceiling 8), tenant | yes | `feature.ai.*` | next session | sens |

**Explainer and denial experience**

| Key | Type | Default | Scopes | Lockable | Plan | Takes effect | Audit |
|---|---|---|---|---|---|---|---|
| `access.explainer.self_service` | enum `off`, `staff`, `all_members` | `staff` | offering, tenant | no | all | immediately | std |
| `access.explainer.as_of_enabled` | bool | true | tenant | no | all | immediately | std |
| `access.explainer.auditor_sees_support_paths` | bool | true | tenant | no | all | immediately | std |
| `access.denial.show_reason_to_members` | bool | true | tenant | no | all | immediately | std |

**Support access, bulk operations and admin governance** (moved from [[PKG-settings-platform-operations]], decision D9; platform bounds for these keys stay in `platform.support.*` and `platform.bulk.*` there)

| Key | Type | Default | Scopes | Lockable | Plan | Takes effect | Audit |
|---|---|---|---|---|---|---|---|
| `access.support.consent_mode` | enum `per_request`, `standing_config_read`, `deny_all_except_break_glass` | `per_request` | platform, region, tenant | yes (platform may forbid `standing_config_read`) | all | new requests | mc |
| `access.support.approvers` | role keys[] | `[tenant_owner, security_admin]` | tenant | no | all | new requests | sens |
| `access.support.case_content_approvers` | membership IDs[] (1–5) | `[]` (then `case_read` cannot be approved) | tenant | no | all | new requests | sens |
| `access.support.max_duration_min` | int, ≤ platform bound per type | platform bound | tenant | no | all | new grants | sens |
| `access.support.notify_impersonated_user` | bool | `true` | platform, tenant | yes | all | next session | sens |
| `access.support.weekly_report` | bool | `true` | tenant | no | all | next week | std |
| `access.support.show_full_names_under_config_read` | bool | `false` | tenant | no | all | new grants | sens |
| `access.support.break_glass_notify_contacts` | email[] (1–5) | tenant owners | tenant | no | all | immediately | sens |
| `access.bulk.step_up_threshold_rows` | int 1–1,000 | 50 | platform, tenant | yes (platform ceiling 1,000) | all | new jobs | sens |
| `access.bulk.approval_threshold_rows` | int 10–10,000 | 500 | platform, tenant | yes (platform ceiling 10,000) | all | new jobs | mc (when raised) |
| *Admin approval expiry* | see `access.change_control.approval_expiry_days` under *Configuration change control* below (maker-checker admin operations are change sets in review, decision D3) | | | | | | |
| `access.admin.reason_required` | enum `security_and_legal`, `all_publishes`, `all_changes` | `security_and_legal` | platform, tenant | yes (floor `security_and_legal`) | all | immediately | sens |
| `access.admin.notify_owners_on_privileged_grant` | bool | `true` | platform, tenant | yes (platform locks `true`) | all | immediately | std |
| `access.admin.single_owner_warning` | bool | `true` | tenant | no | all | immediately | std |

Permission: `settings.access:write`, except `access.support.consent_mode`, `access.support.approvers`, `access.support.case_content_approvers`, `access.support.show_full_names_under_config_read`, which need `support.consent:configure` (held only by `tenant_owner`, step-up) ([[PKG-support-access-and-impersonation]]).

**Configuration change control** (used by [[PKG-configuration-lifecycle]]; change sets per decision D3)

| Key | Type | Default | Scopes | Lockable | Plan | Takes effect | Audit |
|---|---|---|---|---|---|---|---|
| `access.change_control.review_all_changes` | bool: treat every `standard` and `sensitive` item as maker-checker | false | tenant | no | all | new change sets | mc |
| `access.change_control.maker_checker_kinds` | set of change item kinds that always need a checker | `[]` | tenant | no | all | new change sets | mc |
| `access.change_control.approval_expiry_days` | int 1–30: an approved change set lapses if not published in time | 14 | platform, tenant | yes | all | new approvals | sens |
| `access.change_control.emergency_rollback_roles` | set of role keys ⊆ {`tenant_owner`, `security_admin`, `tenant_admin`} | [`tenant_owner`, `security_admin`] | tenant | no | all | immediately | mc |

**Platform and region only** (permission `settings.platform:write`)

| Key | Type | Default | Scopes | Lockable | Takes effect | Audit |
|---|---|---|---|---|---|---|
| `access.platform.catalogue_release_pin` | release id or `latest` | `latest` | platform, region | yes | next deploy | mc |
| `access.platform.staff_jit_max_minutes` | int 30–480 | 480 | platform | yes | next activation | mc |
| `access.platform.decision_cache_ttl_s` | int 0–600 | 300 | platform, region | yes | next request | sens |
| `access.platform.decision_p95_budget_ms` | int | 5 | platform | yes | next deploy (alert threshold) | std |

<!-- section:validation -->
## Validation and dependencies

- `access.jit.eligible_only_roles` must include every role in `access.jit.require_approval_roles`.
- If `access.sod.single_admin_fallback = block`, the console shows how many maker-checker operations currently have fewer than two eligible checkers and refuses publish if any tenant_owner operation would be impossible (for example `tenant:delete` with one owner).
- `access.break_glass.enabled_profiles` containing `emergency_tenant_admin` requires at least 2 entries in `access.break_glass.tenant_admin_holders`, each with phishing-resistant MFA enrolled ([[PKG-settings-security-and-identity]]).
- `access.case.recordings_to_parties = true` at case scope requires a reason (tribunal order reference).
- `access.case.secretariat_sees_tribunal_drafts = true` requires `access.walls.proposed_walls_deny = true` (always) and is shown with a warning that it extends tribunal-only material to staff.
- `access.ai_agent.allowed_permission_sets` can never contain a set that includes a `privileged` permission or any `approve` or `publish` action (platform bound).
- Unit-scope values may only be stricter than tenant values for keys marked "tighten"; the editor shows the tenant value and refuses looser input with "Units can only make this stricter".
- Plan gating: if the plan lacks `feature.custom_roles`, the custom-role keys are read-only and show the platform default with an "Not in your plan" note.

<!-- section:defaults -->
## Defaults by tenant type

| Key | Arbitral institution | SEBI ODR institution | CORD tenant | Court or government programme |
|---|---|---|---|---|
| `access.jit.eligible_only_roles` | security_admin, integration_admin, ai_admin | + tenant_admin, secretariat_lead | security_admin, integration_admin, ai_admin | + tenant_admin, secretariat_lead |
| `access.jit.require_approval_roles` | security_admin | security_admin, tenant_admin | security_admin | security_admin, tenant_admin |
| `access.break_glass.enabled_profiles` | `emergency_case_access` | `emergency_case_access`, `emergency_tenant_admin` | none | `emergency_case_access` |
| `access.sod.single_admin_fallback` | `owner_approves` | `block` | `delayed_self_approval` | `block` |
| `access.case.secretariat_sees_tribunal_drafts` | false (institutions with award scrutiny set true per case type) | false | false | false |
| `access.case.exchange_mode` | `per_rules` | `on_filing` | `on_filing` | `on_secretariat_release` |
| `access.case.recordings_to_parties` | false | true | true | false |
| `access.case.read_after_close_days` | 365 | 90 | 90 | 3650 |
| `access.walls.disclose_to_parties` | `per_rules` | `after_challenge_decision` | `never` | `per_rules` |
| `access.review.frequency` | quarterly | quarterly | half_yearly | quarterly |
| `access.review.population` | `all_staff_and_external` | `all_staff_and_external` | `all_staff` | `all` |
| `access.explainer.self_service` | `staff` | `all_members` | `all_members` | `staff` |
| `access.admin.case_content_in_admin_roles` | `warn` | `block` | `warn` | `block` |

Why they differ: SEBI ODR institutions handle high volumes of retail investor disputes under MII oversight, so they get stricter admin elevation and no single-admin self-approval; CORD tenants are often small and need workable fallbacks; court and government programmes retain records longer and generally release documents only after registry review. The SEBI and court values are assumptions to be confirmed with those tenants and legal.

<!-- section:admin_ux -->
## Where it is administered

| Group | Console page | API |
|---|---|---|
| Roles and assignments, groups | `/admin/access/settings/roles` | `PATCH /admin/v1/settings/access.roles.*`, `access.assignment.*`, `access.groups.*` |
| JIT and requests | `/admin/access/settings/elevation` | `access.jit.*`, `access.requests.*` |
| Break-glass | `/admin/access/settings/break-glass` | `access.break_glass.*` |
| Separation of duties | `/admin/access/settings/separation-of-duties` | `access.sod.*` |
| Case visibility | `/admin/access/settings/case-visibility`; case-type values in the workflow studio's *Access* tab ([[WF-workflow-authoring-studio]]); case values on the case's *Access* panel for case managers | `access.case.*` |
| Ethical walls | `/admin/access/settings/walls` | `access.walls.*` |
| Access reviews | `/admin/access/settings/reviews` | `access.review.*` |
| Non-human and AI | `/admin/access/settings/non-human` | `access.nonhuman.*`, `access.ai_agent.*` |
| Platform | `/platform/settings/access` | `/platform/v1/settings/access.platform.*` |

Each value shows its source ("Platform default", "SEBI ODR blueprint", "Set by tenant on 3 Oct by Meera"), a lock icon with the locking scope, and the plan note where gated. The admin copilot may propose changes to any key; proposals arrive as drafts with a diff and, for access keys, a simulator result ([[APP-admin-copilot]], [[PKG-access-explainer]]).

<!-- section:change_control -->
## Change control and audit

- `mc` keys need a second approver ([[PKG-separation-of-duties]]); approval requires step-up.
- Notified on publish of any `mc` key: all tenant_owners and security_admins (in-app and email).
- Rollback: publish the previous version from `/admin/changes` ([[APP-admin-change-history]]); case-pinned values are not changed on running cases by rollback.
- Audit record (`admin.settings.published`): key, scope, old value, new value, actor, checker, reason, change set ID, catalogue release.

<!-- section:migration -->
## Versioning and migration

- Old ad-hoc keys listed under *Purpose and scope* are migrated with aliases kept for two releases; the settings registry logs reads of aliases so remaining callers are found.
- New keys arrive with a platform default; tenants inheriting it get it automatically; release notes list tenants with explicit values that differ from a changed default.
- `access.case.*` values are part of case-type blueprints and travel inside configuration packages ([[PKG-configuration-packages]]); tenant-level `access.*` values travel in the tenant settings part of the package; membership-id values (`listed_members`, `designated_officer`, `tenant_admin_holders`) are excluded from packages and must be set per environment.

<!-- section:testing -->
## Testing

- Registry `packages/settings/registry/access.ts` is generated from this catalogue's source YAML; CI fails on difference.
- Resolution tests per key for inheritance, locks, unit tightening and plan gating, using the shared settings test harness ([[PKG-settings-data-model]]).
- Behaviour tests: each key has at least one authz test showing the decision changes when the key changes (for example `recordings_to_parties` flips `case.recording:read` for claimant).

<!-- section:questions -->
## Open questions

- [ ] Finance dual-approval threshold default per currency. (Finance)
- [ ] Should `access.case.secretariat_sees_tribunal_drafts` be allowed only where the institution's rules provide for award scrutiny? (Legal, product)
- [ ] Court programme `read_after_close_days` of 3650 is an assumption pending each programme's record rules. (Legal)
- [ ] Is `access.review.auto_remove_on_no_response` safe for neutrals on long-running cases? Proposed: never auto-remove case roles, only tenant roles. (Product)

<!-- section:notes -->
## Notes

Settings change behaviour inside bounds; they never grant access on their own. Every `access.case.*` key is evaluated as a condition inside a policy, so its effect is visible in the explainer.

<!-- checks -->
## Template checks

<!-- check:inheritance -->
### Inheritance and locks

Each key lists allowed scopes; tighten-only keys at unit level are marked; case-type visibility keys are pinned at case start; the explainer shows which setting value and source applied in a decision.

<!-- check:permissions -->
### Who may change what

`settings.access:write` (security_admin, tenant_owner; tenant_admin reads only, [[PKG-roles-and-permission-sets#matrix]]), `case:configure` for case-overridable keys, `settings.platform:write` for platform and region keys; none grantable to AI agents.

<!-- check:safety -->
### Safe bounds

Platform bounds stop tenants from disabling proposed-wall denial, maker-checker minimums, break-glass review, AI agent ceilings and the minimum owner count; validation rules block unsafe combinations.

<!-- check:timing -->
### When changes take effect

Each row states when it applies; procedural visibility values are pinned to running cases unless marked running; JIT values apply to next activation.

<!-- check:audit -->
### Audit and rollback

`admin.settings.published` with old and new values, scope, actor, checker and reason; versions allow reconstruction for any date and rollback in one action.

<!-- check:sync -->
### Catalogue matches code

Generated registry checked against this catalogue in CI; alias read logging during renames.

<!-- end -->
