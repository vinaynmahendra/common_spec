---
id: "PKG-roles-and-permission-sets"
title: "System roles, custom roles and permission sets"
parent: "PKG-authorization"
order: 10
type: "feature"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "System roles for every canonical role key, managed role templates, tenant custom roles and permission sets with muting, scoped assignments (tenant, unit, case type, case) and the bounds on tenant customisation"
links: []
rev: 1
syncHash: "353ba419b4f6bbdf"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.2.10 System roles, custom roles and permission sets

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> System roles for every canonical role key, managed role templates, tenant custom roles and permission sets with muting, scoped assignments (tenant, unit, case type, case) and the bounds on tenant customisation

<!-- section:purpose -->
## Purpose and scope

Defines how permissions from [[PKG-permission-catalogue]] are bundled and handed out: **permission sets** (small, named bundles), **roles** (what an administrator assigns), **assignments** (a role or permission set given to a principal at a scope, for a period) and the bounds within which tenants may customise all three.

Model in one line: *a principal holds a permission on a resource if an active assignment gives it a role or permission set containing that permission, the assignment's scope covers the resource, no muting removes it, and the policy's conditions and deny rules pass* ([[PKG-policy-engine-permission-matrix#policy]]).

Covers:
- system roles (Nomology-defined, one per canonical role key in the shared model), managed role templates, and tenant custom roles;
- system and custom permission sets, and muting;
- scoped assignments at `platform`, `region`, `tenant`, `unit`, `case_type` and `case`, to users, groups and non-human principals;
- how tenant-level roles combine with case-level roles (summary; conditions in [[PKG-rbac-abac-case-level-party]]);
- tenant customisation bounds and the role editor behaviour.

Not covered: table design ([[PKG-authorization-data-model]]); elevation and emergency access ([[PKG-jit-and-break-glass]]); maker-checker and toxic combinations ([[PKG-separation-of-duties]]); the user-and-access screens ([[APP-user-and-access-admin]]).

**Patterns adopted** (described as our behaviour, sources in *Policy model*): permission sets over monolithic profiles and muting inside a group of sets [R3][R4]; scope depth (record, unit, organisation) on the assignment rather than in the role [R5][R6]; custom admin roles that pair a role with a resource set [R7]; administrative units that limit an admin to part of the organisation [R8].

<!-- section:assets -->
## Protected assets

| Asset | Classification | Notes |
|---|---|---|
| System role and permission set definitions (`packages/authz/catalogue/roles.yaml`) | Internal | Shipped with each catalogue release; immutable for tenants |
| Tenant custom roles, custom permission sets, mutings | Confidential (reveal the institution's internal organisation) | Tenant-owned, forced RLS |
| Role assignments (who holds what, where, until when) | Confidential and Personal (links people to roles) | Tenant-owned; personal data under DPDP / GDPR / PDPA |
| Groups and IdP group mappings | Confidential | Synced by SCIM ([[PKG-user-provisioning-scim]]) |
| Assignment history | Confidential | Needed for access reviews and disputes; retained 7 years after the assignment ends (assumption, see Open questions) |

<!-- section:actors -->
## Actors and roles

**Memberships and personas.** Every membership has `membership.kind` = `staff` (the institution's own people) or `external` (parties, counsel, external neutrals, experts and observers) ([[PKG-external-party-identity]]). Administrative roles can be held only by `staff` memberships. In settings catalogues the persona alias `staff_admin` means "a membership holding any tenant administrative role" (for example in `auth.mfa.required_personas`, [[PKG-settings-security-and-identity]]).

**System roles.** One per canonical role key; definitions are fixed by Nomology. Tenants may rename the display label (via terminology, [[PKG-tenant-terminology-and-copy]]) but not the permissions.

| Role key | Level | Permission sets | Typical assignment scope | Assigned by | Privileged? |
|---|---|---|---|---|---|
| `tenant_owner` | Tenant admin | all `ps.admin.*` + `ps.admin.owner` | tenant | Platform at onboarding; another tenant_owner | Yes (min 1, recommended 2 per tenant) |
| `tenant_admin` | Tenant admin | `ps.admin.users`, `ps.admin.roles`, `ps.admin.units`, `ps.admin.workflow`, `ps.admin.integrations`, `ps.admin.content`, `ps.admin.config_lifecycle`, `ps.admin.access_governance`, `ps.admin.ai`, `ps.admin.settings_read`, plus `settings.data:write` (retention and privacy settings, maker-checker). Billing and security settings need the matching role or `tenant_owner`; `api_client:create` is muted for this role ([[PKG-api-clients-and-keys]]) | tenant | tenant_owner, tenant_admin (maker-checker) | Yes |
| `security_admin` | Tenant admin | `ps.admin.security`, `ps.admin.roles`, `ps.admin.access_governance`, `ps.admin.data`, `ps.admin.audit_read`, `ps.admin.settings_read` | tenant | tenant_owner (maker-checker) | Yes |
| `user_admin` | Tenant admin | `ps.admin.users`, `ps.admin.access_requests` | tenant, unit | tenant_admin | No (cannot assign privileged roles) |
| `unit_admin` | Tenant admin | `ps.admin.users`, `ps.admin.units`, `ps.admin.unit_settings`, `ps.admin.settings_read` | unit only | tenant_admin, user_admin | No |
| `workflow_designer` | Tenant admin | `ps.admin.workflow`, `ps.admin.settings_read` | tenant, case_type | tenant_admin | Yes (publishes blueprints) |
| `integration_admin` | Tenant admin | `ps.admin.integrations`, `ps.admin.settings_read` | tenant | tenant_admin (maker-checker) | Yes |
| `content_admin` | Tenant admin | `ps.admin.content`, `ps.admin.settings_read` | tenant, unit, case_type | tenant_admin | No |
| `billing_admin` | Tenant admin | `ps.admin.billing` | tenant | tenant_owner | No |
| `ai_admin` | Tenant admin | `ps.admin.ai`, `ps.admin.settings_read` | tenant | tenant_owner (maker-checker) | Yes |
| `auditor` | Tenant admin (read-only) | `ps.admin.audit_read`, `ps.admin.settings_read` | tenant, unit | tenant_owner, security_admin | No (read-only, but sensitive) |
| `secretariat` | Operational | `ps.case.secretariat_core`, `ps.report.viewer`, `ps.transcription.desk` | tenant, unit, case_type | tenant_admin, user_admin, unit_admin | No |
| `neutral` | Operational | `ps.neutral.self` | tenant | secretariat (supervisor set) on empanelment | No |
| `transcriber` | Operational | `ps.transcriber.self` | tenant | secretariat | No |
| `party`, `counsel`, `observer` | Operational base | `ps.personal.self` | tenant | Automatic on invitation acceptance ([[PKG-external-party-identity]]) | No |

Platform roles (`platform_owner`, `platform_admin`, `platform_support`, `platform_security`, `platform_billing`, `regional_ops`) use `ps.platform.*` sets, live only in the platform realm (workforce IdP, no tenant membership) and are assigned at `platform` or `region` scope by `platform_owner` with maker-checker. `platform_support` carries a `tier` attribute (1 or 2) that limits which support grant types the person may request ([[PKG-support-access-and-impersonation]]).

**Case-level roles.** Assigned per case and derived from domain records (party, representation, tribunal seat, case assignment, hearing assignment). They are system roles with scope `case` only:

| Case role | Permission sets | Derived from | Prerequisite tenant role |
|---|---|---|---|
| `case_manager` | `ps.case.secretariat_core` (case scope) | `case_assignment` | `secretariat` |
| `presiding_neutral` | `ps.case.participant_read`, `ps.case.tribunal_core`, `ps.case.tribunal_presiding` | tribunal seat `sole`, `presiding`, `emergency`, `mediator`, `conciliator` | `neutral` |
| `tribunal_member` | `ps.case.participant_read`, `ps.case.tribunal_core` | tribunal seat `co_neutral` | `neutral` |
| `tribunal_secretary` | `ps.case.participant_read`, `ps.case.tribunal_secretary` | tribunal seat `secretary` (appointed by the tribunal, with the parties' consent where the rules require it) | any membership (often `external`) |
| `claimant`, `respondent` | `ps.case.participant_read`, `ps.case.party_actions` | `case_parties.role` with a linked membership | `party` (or any membership) |
| `claimant_counsel`, `respondent_counsel` | `ps.case.participant_read`, `ps.case.counsel_actions` | active `case_representations` | `counsel` (or any membership) |
| `expert` | `ps.case.expert` | participant record | any membership |
| `witness` | `ps.case.witness` | hearing participant record | any membership |
| `interpreter`, `transcriber` | `ps.case.interpreter`, `ps.case.transcription` | `hearing_assignment` with `valid_from` / `valid_to` | `transcriber` for transcribers |
| `observer` | `ps.case.observer_read` | participant record with end date | any membership |

**Managed role templates.** Nomology-maintained roles shipped in tenant blueprints ([[PKG-configuration-packages]]), flagged `managed`. Tenants can assign them as they are, or clone them into a custom role; they cannot edit them in place. Updates arrive with catalogue releases.

Managed role templates are the accepted way to ship these personas (decision D6); they are not system roles.

| Template key | Built from | Purpose |
|---|---|---|
| `secretariat_lead` | `secretariat` sets + `ps.case.secretariat_supervisor` + `ps.neutral.panel_admin` | Registry head: registers cases, appoints neutrals, decides challenges, approves walls |
| `case_finance_officer` | `ps.finance.case_fees` | Case fees, invoices, refunds, vendor bills |
| `reporting_viewer` | `ps.report.viewer`, `ps.report.exporter` | Management reports |
| `regulatory_reporter` / `regulatory_approver` | `ps.report.regulatory_maker` / `ps.report.regulatory_checker` | SEBI / aggregator submissions with maker-checker |
| `privacy_officer` | `data.dsr:approve`, `audit.log:read`, `settings.data:write` | DPDP grievance and rights requests |

<!-- section:matrix -->
## Permission matrix

**System permission sets** (contents are lists of catalogue keys in `roles.yaml`; summarised here by purpose).

| Permission set | Main permissions | In roles |
|---|---|---|
| `ps.case.participant_read` | `case:list`, `case:read`, `case.deadline:read`, `case.document:list/read/export`, `case.hearing:read`, `case.hearing.room:read`, `case.message:list/create`, `case.transcript:read`, `case.recording:read` (setting-gated) | all participant case roles |
| `ps.case.party_actions` | `case.filing:create/delete`, `case.document:create`, `case.application:create`, `case.representative:create/delete`, `case.hearing.slot:create`, `case.payment:create`, `case.invoice:read`, `case.fee:read`, `neutral.challenge:create` | claimant, respondent |
| `ps.case.counsel_actions` | as party actions, with `case.representative:create` limited to co-counsel on own side | claimant_counsel, respondent_counsel |
| `ps.case.tribunal_core` | `case.order:create/read/approve`, `case.award:create/read/approve`, `case.message.tribunal:create`, `case.hearing:create/update`, `case.filing:approve`, `case.transcript:publish`, `case.document:create` (tribunal folder), `ai.generation:create` | presiding_neutral, tribunal_member |
| `ps.case.tribunal_secretary` | `case.order:create/read` (drafts for the tribunal; never approve or publish), `case.message.tribunal:create`, `case.hearing:create/update`, `case.document:create` (tribunal folder), `ai.generation:create` | tribunal_secretary |
| `ps.case.tribunal_presiding` | `case.order:publish`, `case.deadline:update`, `case.status:update` (tribunal commands), `case.participant:assign` (experts), `case.document:update` | presiding_neutral |
| `ps.case.secretariat_core` | `case:list/read/create/update/delete`, `case.status:update`, `case.party:*`, `case.representative:*`, `case.participant:assign`, `case.filing:create` (on behalf) and `:approve`, `case.document:*`, `case.bundle:create/publish`, `case.hearing:*`, `case.transcript:update/publish`, `case.notice:create`, `case.note.internal:*`, `case.deadline:update` (rule-gated), `case.audit:read`, `case.wall:read/create`, `case.fee:read`, `case.invoice:read`, `neutral.profile:list`, `ai.generation:create`, `user:create` (case participants) | secretariat, case_manager |
| `ps.case.secretariat_supervisor` | `case:approve`, `case:assign`, `case:configure`, `case:export`, `case.award:publish`, `case.recording:export`, `case.wall:approve/delete`, `neutral:assign`, `neutral.challenge:approve`, `case.vendor_bill:approve` | secretariat_lead template |
| `ps.case.transcription`, `ps.case.interpreter`, `ps.case.expert`, `ps.case.witness`, `ps.case.observer_read` | narrow sets for those case roles | case roles of the same name |
| `ps.neutral.self`, `ps.transcriber.self` | own profile, conflicts, own jobs, own vendor bills | neutral, transcriber |
| `ps.neutral.panel_admin` | `neutral.profile:list`, `neutral.empanelment:approve`, `neutral.conflict:read` | secretariat_lead template |
| `ps.transcription.desk` | `transcription.job:assign`, `transcription.review:approve` | secretariat |
| `ps.finance.case_fees` | `case.fee:read`, `case.invoice:create/read`, `case.payment:approve`, `case.vendor_bill:approve`, `report:read` (finance) | case_finance_officer template |
| `ps.report.viewer` / `ps.report.exporter` | `report:list/read` / `report:export`, `report.schedule:create` | secretariat, auditor, reporting_viewer |
| `ps.report.regulatory_maker` / `_checker` | `report.regulatory:create` / `:approve`, `:publish` | regulatory templates |
| `ps.admin.users` | `user:*` (not `impersonate`), `group:*`, `role:list/read`, `role:assign` | tenant_admin, user_admin, unit_admin |
| `ps.admin.access_requests` | `access.request:approve`, `access.explainer:read` | user_admin |
| `ps.admin.roles` | `role:create/update/delete`, `permission_set:*`, `role.privileged:assign`, `access.simulator:read` | tenant_admin, security_admin |
| `ps.admin.units` | `unit:*` | tenant_admin, unit_admin |
| `ps.admin.security` | `settings.security:write`, `settings.access:write`, `user.session:delete`, `user.mfa:update`, `user:delete`, `support.grant:read/approve`, `access.elevation:approve`, `access.break_glass:read`, `integration.data_policy:publish`, `role.privileged:assign` | security_admin |
| `ps.admin.unit_settings` | `settings.cases:write`, `settings.workflow:write`, `settings.notifications:write`, `settings.branding:write` (unit scope only, keys that allow `unit`); `settings.security:write`, `settings.access:write`, `settings.ai:write` for unit tighten-only keys; `workflow.queue:configure`, `workflow.calendar:update` (unit calendar), `workflow.sla_policy:update` (unit policies) | unit_admin |
| `ps.admin.access_governance` | `access.review:create/read`, `access.explainer:read`, `access.simulator:read` | tenant_admin, security_admin |
| `ps.admin.workflow` | `workflow.*`, `rules.decision_table:*`, `form:*`, `metadata.field:update`, `settings.cases:write`, `settings.workflow:write`, `config.sandbox:create` | workflow_designer, tenant_admin |
| `ps.admin.integrations` | `integration.connection:*`, `api_client:*`, `api_client.key:*`, `webhook.endpoint:*`, `service_account:*`, `settings.integrations:write`, `settings.notifications:write` (channels and senders) | integration_admin, tenant_admin |
| `ps.admin.content` | `brand.theme:*`, `content.terminology:*`, `template.*`, `form:*`, `notify.*`, `settings.branding:write`, `settings.notifications:write`, `settings.personal:write` (tenant and unit defaults) | content_admin, tenant_admin |
| `ps.admin.ai` | `ai.policy:configure`, `ai.agent:*`, `ai_agent.principal:assign`, `ai.usage:read`, `settings.ai:write` | ai_admin |
| `ps.admin.billing` | `billing.*`, `settings.billing:write`, `ai.usage:read` | billing_admin, tenant_owner |
| `ps.admin.data` | `settings.data:write`, `data.legal_hold:*`, `data.dsr:approve` | security_admin, tenant_owner |
| `ps.admin.audit_read` | `audit.log:read/export`, `access.review:read`, `access.break_glass:read`, `access.explainer:read`, `role:list/read`, `user:list/read`, `case.audit:read` (metadata), `report:list/read`, `billing.invoice:read`, `ai.usage:read` | auditor, security_admin |
| `ps.admin.config_lifecycle` | `config.change_set:approve`, `config.package:*`, `config.sandbox:create` | tenant_admin |
| `ps.admin.settings_read` | `settings.*:read` (all catalogues), `config.change_set:read` | every administrative role |
| `ps.admin.owner` | `tenant:update/delete`, `data.export:create`, `billing.subscription:update` | tenant_owner |
| `ps.integration.viewer` | `integration.connection:read`, `integration.usage:read`, `integration.connector:read` | auditor; custom roles |
| `ps.integration.case_intake` | `case:create`, `case.party:create`, `case.filing:create`, `case.document:create` (non-human, intake clients) | service accounts of aggregators and institutional systems ([[INT-public-api-and-webhooks]]) |
| `ps.identity.scim_provisioner` | `user:create`, `user:update`, `group:update` | SCIM `integration_connection` only ([[PKG-user-provisioning-scim]]) |
| `ps.ai.<feature>_user` | `ai.generation:create` for one AI feature | operational roles where [[PKG-settings-ai]] enables the feature |
| `ps.ai.agent_builder` | `ai.agent:create/update`, `ai.knowledge:read` (test console) | delegated agent builders; custom roles ([[AI-agent-configuration]]) |
| `ps.ai.copilot_admin` | ceiling for the admin copilot's `ai_agent` principal: read and draft admin operations only ([[APP-admin-copilot]]) | admin copilot principal |
| `ps.personal.self` | `settings.personal:write`, `access.request:create`, own sessions and devices | every member |

**Who may assign what** (enforced by `role:assign` vs `role.privileged:assign` and by the no-escalation rule):

| Assigner holds | May assign | Scope limit |
|---|---|---|
| `tenant_owner` | any tenant role, including tenant_owner | tenant |
| `tenant_admin` | any tenant role except tenant_owner and security_admin; privileged roles need a checker | tenant |
| `security_admin` | security_admin (checker: tenant_owner), auditor, privacy_officer | tenant |
| `user_admin` | non-privileged roles (secretariat, neutral, transcriber, content_admin, user_admin, unit_admin, managed templates without `priv` permissions) | tenant or unit |
| `unit_admin` | non-privileged roles | own unit and its descendants |
| `secretariat` with case scope | case-level roles on cases in scope, through the case screens (adding a party, counsel, observer) | the case |
| SCIM group mapping | roles mapped to the IdP group by a tenant_admin; never tenant_owner or security_admin | as mapped |

**Tenant customisation bounds.**

| Can tenants … | Answer | Bound |
|---|---|---|
| Create custom roles | Yes, where the plan includes `feature.custom_roles` (assumption: standard and enterprise plans) | Max `access.roles.max_custom_roles` (default 50) |
| Create custom permission sets | Yes | Only `customisable: y` permissions |
| Edit system roles or system permission sets | No | Clone instead |
| Mute permissions in a role | Yes, where `access.roles.allow_muting` | Muting can only remove; muting a permission in a system role creates a tenant variant `system_role_key@tenant`, shown with a badge |
| Grant a permission they do not hold | No | No-escalation rule (decision D6, "an admin may only grant permissions they hold"): custom roles and permission sets can be built only from permissions the author holds, and a custom role can be assigned only by someone who holds all of its permissions at a covering scope. System roles and managed templates, whose contents Nomology fixes, may be assigned by the roles in the "Who may assign what" table. There is no `tenant_owner` exception |
| Use platform permissions | No | Rejected by schema |
| Add case-content permissions to admin roles | Yes, but flagged | The role is marked "admin with case access" and appears in every access review; `access.admin.case_content_in_admin_roles` can forbid it |
| Assign roles beyond plan seats | No | `limit.staff_seats` counts members holding any non-base role ([[BIL-plans-entitlements-and-usage]]) |
| Create roles at unit level | Yes | A custom role may be marked `assignable_scopes: [unit]` so unit admins can use it |

<!-- section:policy -->
## Policy model

**Effective permissions.** For principal *p* in tenant *t*:

```text
effective(p, resource) =
  ⋃ over active assignments a of p (direct, via group, via case role, via elevation)
      where covers(a.scope, resource.scope_path)
        permissions(a.role or a.permission_set) − muted(a.role)
  ∩ entitlement_allowed(t)
  ∩ principal_ceiling(p)            -- non-human ceilings, support grant constraints, AI on-behalf intersection
```

- `covers`: `tenant` covers everything in the tenant; `unit` covers the unit (and descendants if `include_descendants`), cases whose `owning_unit_id` is in that set, and members of those units for admin permissions; `case_type` covers cases of that blueprint key (all versions); `case` covers one case and its child resources. This is the "depth" idea: the same `secretariat` role gives assigned-case, unit-wide or tenant-wide reach depending only on where it is assigned [R5][R6][R9].
- Case-level roles are always `case` scope. A tenant role gives no case access by itself, except where it is assigned at `tenant`, `unit` or `case_type` scope and contains case permissions (secretariat). Party and counsel tenant roles contain no case permissions; all their case access comes from case roles.
- A case role whose prerequisite tenant role is missing or suspended is inactive (for example a case_manager assignment for someone who is no longer secretariat).
- Muting applies within the role it is defined on only; a permission muted in role A but present in role B is still held through B. This is deliberate and shown in the explainer.

**Assignment attributes.** `principal` (membership, group, service account, AI agent), `role_id` or `permission_set_id`, `scope_type`, `scope_id`, `include_descendants`, `starts_at`, `ends_at`, `source` (`manual`, `scim`, `case_derived`, `jit`, `break_glass`, `blueprint`, `api`), `granted_by`, `approved_by`, `change_set_id`, `reason`.

**Rules**
1. **ROLE-R1 Last owner.** A tenant always has at least one active `tenant_owner` and one principal able to assign `security_admin`; removing the last one is refused.
2. **ROLE-R2 Expiry.** Assignments of privileged roles have an end date no later than `access.assignment.max_duration_days_privileged` (default 365) unless the role is held through JIT eligibility instead ([[PKG-jit-and-break-glass]]). External roles (`observer`, `expert`) default to an end date.
3. **ROLE-R3 Groups.** Group assignments apply to current members; group membership from SCIM is authoritative and cannot be edited locally for IdP-managed groups.
4. **ROLE-R4 Custom role versioning.** Changing a custom role creates a new version through the configuration lifecycle ([[PKG-configuration-lifecycle]]); the simulator shows who gains or loses which permissions before publish ([[PKG-access-explainer]]).
5. **ROLE-R5 Deletion.** A custom role with active assignments cannot be deleted; it can be retired (no new assignments) and its assignments migrated in one reviewed change.
6. **ROLE-R6 Labels.** Role display names are localised; keys never change.

**Admin surfaces.** Console `/admin/access/roles`, `/admin/access/roles/[roleId]`, `/admin/access/permission-sets`, `/admin/access/assignments`, `/admin/groups` (screens in [[APP-user-and-access-admin]]). API `/admin/v1/roles`, `/admin/v1/permission-sets`, `/admin/v1/role-assignments` ([[INT-tenant-admin-api]]). The admin copilot may draft a custom role or bulk assignment change; it arrives as a draft change set with a permission diff and needs a human publisher ([[APP-admin-copilot]]).

**Why not pure relationship tuples.** A Zanzibar-style store (relations such as `case#claimant_counsel@user`) is a good fit for case roles and is close to what `authz_case_role` already holds [R10][R11]. We keep RBAC with scoped assignments for tenant roles because institutions think in roles and units, access reviews are per role, and list filtering must compile to Postgres `where` clauses under RLS. The data model keeps case roles in tuple-like form so a later move to a relationship engine stays possible ([[PKG-policy-engine-permission-matrix#policy]]).

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat | Scenario | Mitigation | Residual |
|---|---|---|---|---|---|
| T1 | E | Privilege escalation through custom roles | user_admin creates a role with `role.privileged:assign` and assigns it to self | `role:create` is privileged; no-escalation rule; maker-checker; self-assignment of privileged roles refused | Low |
| T2 | E | Over-broad scope | secretariat for one desk assigned at tenant scope by mistake | Scope shown in plain words ("all cases in the tenant"); simulator count of newly visible cases; review flags tenant-scope secretariat assignments | Medium |
| T3 | E | Stale case role | Counsel replaced but `authz_case_role` row remains | Case roles written in the same transaction as the domain change; nightly drift reconciler compares with domain tables and alerts | Low |
| T4 | E | IdP group mapping grants admin | Attacker adds self to an IdP group mapped to tenant_admin | SCIM mappings cannot target tenant_owner or security_admin; privileged mappings need maker-checker and alert on each new member | Medium (depends on the tenant's IdP hygiene) |
| T5 | I | Admin reads case content | tenant_admin adds case permissions to own custom role | Flag "admin with case access"; optional block setting; access review highlights it | Low |
| T6 | R | Who granted this role | Dispute over a grant | Assignment history immutable with granter, approver, reason, change set | Low |
| T7 | E | Muting misunderstood | Admin mutes `case:export` in one role but the user also holds it through another role | Explainer shows all paths; simulator shows the effective result | Low |

<!-- section:failure -->
## Denial behaviour

- Assigning a role the assigner may not assign returns 403 `role_assignment_not_permitted` with the missing permissions listed (admins are trusted to see permission names).
- Custom role save with a non-customisable permission returns 422 `permission_not_customisable` naming the permission.
- Removing the last owner returns 409 `last_owner`.
- Every refused attempt to assign a privileged role is audited (`admin.role.assignment_refused`).

<!-- section:requirements -->
## Security requirements

ASVS references are to OWASP ASVS 5.0 at chapter level [R1][R2]; requirement-level IDs to be added after checking against the 5.0.0 text.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| ROLE-FR-1 | Each canonical role key in the shared model shall exist as a system role defined only by permission sets from the catalogue. | V8 |
| ROLE-FR-2 | Tenants shall be able to create custom roles and custom permission sets only from `customisable` permissions, within plan entitlements and `access.roles.*` bounds. | V8 |
| ROLE-FR-3 | An admin shall only grant permissions they hold (decision D6): a custom role or permission set may contain, and be assigned by someone holding, only permissions the admin holds at a covering scope; system roles and managed templates may be assigned only by the roles listed in "Who may assign what". No role, including `tenant_owner`, is exempt. | V8 |
| ROLE-FR-11 | Tenant administrators shall have the permission simulator ([[PKG-access-explainer]]) and no live impersonation of their own users; `user:impersonate` is held only by Nomology support under a tenant-approved grant ([[PKG-support-access-and-impersonation]]). | V8 |
| ROLE-FR-12 | Groups shall be valid assignees of roles and permission sets (and of human tasks, [[WF-human-tasks]]); a group assignment applies to current members only. | V8 |
| ROLE-FR-4 | Every assignment shall have a scope (`tenant`, `unit`, `case_type`, `case`; staff: `platform`, `region`) and the decision point shall apply the permission only to resources within that scope. | V8 |
| ROLE-FR-5 | Case-level roles shall be derived from domain records in the same database transaction as the change to those records. | V8 |
| ROLE-FR-6 | Assignment of a role containing a privileged permission shall require step-up and a second approver ([[PKG-separation-of-duties]]). | V8 |
| ROLE-FR-7 | Muting shall only remove permissions from the role in which it is defined. | V8 |
| ROLE-FR-8 | A tenant shall always have at least one active tenant_owner. | V8 |
| ROLE-FR-9 | Changes to custom roles shall follow the configuration lifecycle and show a permission and affected-user diff before publish. | — |
| ROLE-FR-10 | SCIM group mappings shall not grant `tenant_owner` or `security_admin`. | V8 |

Acceptance (selected):
- **Given** a user_admin, **when** they try to assign `integration_admin` to a member, **then** the request is refused with `role_assignment_not_permitted` and audited.
- **Given** a secretariat assignment at unit "SEBI ODR desk" with descendants, **when** a case owned by that unit is opened, **then** `case:read` is allowed; **and when** a case of the "Singapore office" unit is opened, **then** it is not found.
- **Given** a custom role that mutes `case:export`, **when** the user also holds secretariat_lead, **then** export is allowed and the explainer shows the path through secretariat_lead.

<!-- section:verification -->
## Verification

- Generated tests per system role from `roles.yaml` (each permission allowed, a sample of others denied), at each allowed scope, including scope edges (sibling unit, other case type) [R12].
- Property-based tests of the no-escalation rule: random custom roles and assigners; no assignment may increase the assigner's own reachable permission set.
- Drift reconciler test: change domain records without the authz helper in a test build and confirm the reconciler alerts.
- Pen test: escalation via custom roles, SCIM mappings and unit scope.

<!-- section:questions -->
## Open questions

- [ ] Which plans include custom roles? Assumed standard and enterprise. (Commercial, [[BIL-plans-entitlements-and-usage]])
- [ ] Assignment history retention: 7 years after end proposed; legal to confirm against institution record-keeping duties. (Legal)
- [ ] Do court or government programmes need a unit-scoped auditor that sees case content (inspection)? (Product)
- [ ] Under D6 a `user_admin` can assign `secretariat`, which carries case-content permissions the `user_admin` does not hold, because system role contents are fixed. Confirm this reading, or require the assigner to hold the role's permissions for system roles too. (CTO)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Roles, permission sets, mutings, groups and assignments are tenant-owned with forced RLS; system definitions are platform-level reference data that grant nothing by themselves. A person in two tenants has two memberships and unrelated assignments; no assignment can reference a principal or scope of another tenant because foreign keys include `tenant_id` ([[PKG-authorization-data-model#keys]]).

<!-- check:enforcement -->
### Enforcement points and bypass paths

Effective permissions are computed only inside `@nomology/authz`; domain code cannot read assignments directly (lint rule on imports of authz tables). Case-role writes go through `authz.caseRoles.grant/revoke` called by domain commands.

<!-- check:lifecycle -->
### Grant lifecycle and privileged access

Assignments carry start, end, source and approver; privileged roles expire within a year or are held as JIT eligibility; case roles end with the domain record; leavers are deprovisioned by SCIM within minutes ([[PKG-user-provisioning-scim]]); every assignment appears in access reviews ([[SEC-access-reviews]]).

<!-- check:audit -->
### Audit trail

`admin.role.created`, `admin.role.published`, `admin.role.assigned`, `admin.role.unassigned`, `admin.role.assignment_refused`, `admin.permission_set.published`, each with old and new values, scope, actor, approver, reason and catalogue release ([[PKG-audit-trail]]).

<!-- check:compliance -->
### Framework and legal mapping

ISO/IEC 27001:2022 Annex A 5.15, 5.18, 8.2 and 5.3 (segregation of duties) [R13]; SOC 2 CC6.1–CC6.3 [R14]; the generated role and assignment register is the evidence of least privilege; segregation rules are in [[PKG-separation-of-duties]].

<!-- check:testing -->
### Verification and testing

Generated per-role and per-scope tests, property tests of no-escalation, drift reconciler tests and pen-test scope as in *Verification*.

<!-- citations -->
## Citations

```json
[
  {
    "body": "OWASP",
    "id": "R1",
    "ident": "ASVS",
    "kind": "standard",
    "title": "OWASP Application Security Verification Standard",
    "url": "https://owasp.org/www-project-application-security-verification-standard",
    "version": "5.0"
  },
  {
    "body": "OWASP",
    "id": "R2",
    "ident": "ASVS",
    "kind": "standard",
    "title": "OWASP Cheat Sheet Series: ASVS 5.0 index (chapter and section titles)",
    "url": "https://cheatsheetseries.owasp.org/IndexASVS.html",
    "version": "5.0.x"
  },
  {
    "id": "R3",
    "kind": "vendor",
    "title": "Salesforce Help: Permission Set Groups",
    "url": "https://help.salesforce.com/s/articleView?language=en_US&id=platform.perm_set_groups.htm&type=5",
    "vendor": "Salesforce"
  },
  {
    "id": "R4",
    "kind": "vendor",
    "title": "Salesforce Help: Muting Permission Sets",
    "url": "https://help.salesforce.com/s/articleView?id=platform.perm_set_groups_muting.htm&language=en_US&type=5",
    "vendor": "Salesforce"
  },
  {
    "id": "R5",
    "kind": "vendor",
    "title": "Microsoft Learn: Security roles and privileges for Dataverse (access levels)",
    "url": "https://learn.microsoft.com/en-us/power-platform/admin/security-roles-privileges",
    "vendor": "Microsoft"
  },
  {
    "id": "R6",
    "kind": "vendor",
    "title": "Microsoft Learn: Create or edit business units (Power Platform)",
    "url": "https://learn.microsoft.com/en-us/power-platform/admin/create-edit-business-units",
    "vendor": "Microsoft"
  },
  {
    "id": "R7",
    "kind": "vendor",
    "title": "Okta Help: Custom admin roles",
    "url": "https://help.okta.com/oie/en-us/content/topics/security/custom-admin-role/custom-admin-roles.htm",
    "vendor": "Okta"
  },
  {
    "id": "R8",
    "kind": "vendor",
    "title": "Microsoft Learn: Administrative units in Microsoft Entra ID",
    "url": "https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/administrative-units",
    "vendor": "Microsoft"
  },
  {
    "id": "R9",
    "kind": "vendor",
    "title": "Workday Education: Segment-based security",
    "url": "https://doc.workday.com/workday-education/en-us/course-manuals/security-for-administrators/segment-based-security.html",
    "vendor": "Workday"
  },
  {
    "id": "R10",
    "kind": "web",
    "publisher": "USENIX ATC 2019 / Google Research",
    "title": "Zanzibar: Google's Consistent, Global Authorization System",
    "url": "https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/"
  },
  {
    "id": "R11",
    "kind": "vendor",
    "title": "OpenFGA documentation: Concepts",
    "url": "https://openfga.dev/docs/concepts",
    "vendor": "OpenFGA (CNCF)"
  },
  {
    "body": "OWASP",
    "id": "R12",
    "ident": "Cheat Sheet Series",
    "kind": "standard",
    "title": "OWASP Authorization Testing Automation Cheat Sheet",
    "url": "https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Testing_Automation_Cheat_Sheet.html"
  },
  {
    "body": "ISO/IEC",
    "id": "R13",
    "ident": "27001",
    "kind": "standard",
    "title": "ISO/IEC 27001:2022 Information security management systems",
    "url": "https://www.iso.org/standard/27001",
    "version": "2022"
  },
  {
    "body": "AICPA",
    "id": "R14",
    "ident": "Trust Services Criteria",
    "kind": "standard",
    "title": "2017 Trust Services Criteria (with revised points of focus, 2022)",
    "url": "https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022",
    "version": "2017 (revised points of focus 2022)"
  }
]
```

<!-- end -->
