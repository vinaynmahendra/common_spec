# Shared model: platform vocabulary and agreed conventions

This is the binding vocabulary for every spec in this repo: configuration scopes, role keys, naming rules, the configuration change lifecycle, the workflow authoring boundary, AI-native administration principles, and the decisions agreed so far (section 8). Every spec must use these names. To change something here, raise it in a pull request and update every spec that uses it.

`[[ID]]` is a link to the spec with that ID (`specs/<AREA>/<ID>.md`).

## 1. Configuration scopes (the hierarchy)

Ordered from broadest to narrowest. Short keys are used in setting definitions, APIs and tables.

| Order | Scope key | Meaning | Who administers it | Example |
|---|---|---|---|---|
| 1 | `platform` | Nomology-wide defaults and hard bounds | Platform owner / platform admin | Maximum upload size 2 GB |
| 2 | `region` | Deployment region (India, Singapore, US); data residency, local legal defaults | Platform admin (regional ops) | India: DPDP notice text required |
| 3 | `offering` | Product line: CORD or TERES | Platform admin | CORD: party self-service filing on |
| 4 | `tenant` | One customer institution (arbitral institution, SEBI ODR institution, CORD tenant, court or government programme) | Tenant owner / tenant admins | Tenant brand, SSO, case types |
| 5 | `unit` | A part of a tenant: office, panel, programme or desk (for example "SEBI ODR desk", "Singapore office") | Unit admin | Unit-specific working calendar |
| 6 | `case_type` | A published case-type blueprint (process definition plus forms, rules and templates), for example "SEBI ODR conciliation", "Institutional arbitration (expedited)" | Workflow designer | Statement of claim due in 14 days |
| 7 | `case` | One matter | Case manager (secretariat), only for settings marked case-overridable | Extended deadline by tribunal order |
| 8 | `user` | One person's own preferences | The user | Dark mode, digest at 8 am |

Resolution rules (owned by [[PKG-configuration-scope-hierarchy]], implemented in `@nomology/settings`):
1. The most specific scope that the setting allows and that has an explicit value wins.
2. A higher scope may **lock** a value; then lower scopes cannot override it and the UI shows the lock and its source.
3. **Hard bounds** set at `platform` (and tightened at `region`) limit what any lower scope can choose.
4. **Plan entitlements** ([[BIL-plans-entitlements-and-usage]]) decide whether a tenant may change a setting at all; outside the entitlement the platform default applies.
5. Values that affect procedural fairness (deadlines, rules applied to a case) are **pinned** to a case when it starts, unless the setting is explicitly "applies to running cases".
6. Deployment configuration and secrets ([[FND-environment-management]]) and release feature flags ([[PKG-feature-flags]]) are **not** settings in this sense.

## 2. Personas and canonical role keys

Platform (Nomology staff) roles: `platform_owner`, `platform_admin`, `platform_support` (tiers 1 and 2 as attributes), `platform_security`, `platform_billing`, `regional_ops`.

Tenant administrative roles: `tenant_owner`, `tenant_admin`, `security_admin`, `user_admin`, `workflow_designer`, `integration_admin`, `content_admin` (branding, terminology, templates), `billing_admin`, `ai_admin`, `auditor` (read-only, includes audit log), `unit_admin`.

Tenant operational roles: `secretariat` (case manager / registry staff), `neutral` (arbitrator, mediator, conciliator), `transcriber`, `party`, `counsel`, `observer`.

Case-level roles (assigned per case, combined with tenant roles by [[PKG-rbac-abac-case-level-party]]): `case_manager`, `presiding_neutral`, `tribunal_member`, `claimant`, `respondent`, `claimant_counsel`, `respondent_counsel`, `expert`, `witness`, `interpreter`, `transcriber`, `observer`.

Non-human principals: `service_account`, `ai_agent`, `integration_connection` (owned by [[PKG-non-human-principals]]).

Custom roles: tenants may create custom roles by combining permission sets, but cannot grant a permission that their plan or the platform bounds do not allow, and cannot create platform roles.

## 3. Naming conventions

- **Permissions**: `<resource>:<action>`, resources dot-separated, for example `case.document:upload`, `settings.security:write`, `workflow.definition:publish`, `user:impersonate`. Actions: `read`, `list`, `create`, `update`, `delete`, `export`, `approve`, `publish`, `assign`, `impersonate`, `configure`. Catalogue owned by [[PKG-permission-catalogue]].
- **Permission sets**: named bundles, `ps.<domain>.<name>`, for example `ps.case.secretariat_core`.
- **Setting keys**: `<domain>.<area>.<name>` in lower_snake. Domains: `platform`, `auth`, `access`, `case`, `workflow`, `notify`, `integration`, `brand`, `content`, `locale`, `ai`, `data`, `billing`, `personal`.
- **Consoles**: platform admin console under `/platform/...`; tenant admin console under `/admin/...`. APIs: tenant admin API `/admin/v1/...` ([[INT-tenant-admin-api]]); platform internal API `/platform/v1/...`.
- **Audit events**: `admin.<domain>.<verb>`, for example `admin.settings.published`, `admin.role.assigned`.

## 4. Configuration change lifecycle

States: `draft` → `in_review` → `approved` → `published` → `superseded`. Rollback is publishing an earlier version (itself audited). Owned by [[PKG-configuration-lifecycle]].
- Changes marked **maker-checker** need a second approver who is not the author ([[PKG-separation-of-duties]]).
- Tenants may preview changes in a **sandbox** (a non-production copy of their configuration with synthetic or masked data).
- A **configuration package** is a versioned, signed bundle of settings, roles and permission sets, custom fields, case-type blueprints, document and notification templates, automation rules and integration definitions (no secrets). Used to promote between environments and to create tenants from a **tenant blueprint** (for example "SEBI ODR institution blueprint"). Owned by [[PKG-configuration-packages]].

## 5. Workflow authoring boundary

Tenants author **case-type blueprints** as configuration, never as code: stages, human tasks, forms, deadlines, rules (decision tables), document and notification templates, automation rules and AI steps. The model is [[WF-process-definition-model]]. Published blueprints are interpreted by generic Temporal workflows written by Nomology engineers (see [[WF-separation-of-concerns-temporal]] and [[PKG-workflow-templates]]); running cases stay on the blueprint version they started with unless migrated by [[WF-workflow-versioning]]. Simple event-driven automations ("when X, if Y, do Z") run through [[WF-automation-rules]] on BullMQ, not Temporal.

## 6. AI-native administration principles

1. Every admin action is a typed, permission-checked operation in the admin API; the consoles, bulk tools and the admin copilot all call the same operations.
2. The admin copilot ([[APP-admin-copilot]]) and any AI agent act with the permissions of the human who invoked them or of their own `ai_agent` principal, whichever is narrower; never more.
3. AI proposes, humans approve: AI-generated configuration changes arrive as a draft with a readable diff and an explanation, then follow the normal lifecycle.
4. Every AI action is audited with the prompt reference, model, tool calls and the approving human.
5. Tenants control AI use through [[AI-tenant-ai-policy]] and the AI settings catalogue [[PKG-settings-ai]].

## 7. Inspiration (patterns to learn from; never copy product names into requirements)

| Stack | Patterns worth learning from |
|---|---|
| Salesforce (Setup, profiles and permission sets, permission set groups, Flow, Agentforce and the Einstein Trust Layer, sandboxes, DevOps Center) | Permission sets over monolithic profiles; muting permissions; declarative flows; sandbox types; metadata deployment; AI agent topics and actions with guardrails |
| Microsoft Dynamics 365 and Power Platform (environments, security roles with business-unit depth, Dataverse, connector DLP policies, solutions, Copilot Studio) | Scoped privilege depth (user, unit, organisation); solutions as packages; data loss prevention policies per connector |
| Workday (business process framework, security groups, tenant configuration) | Configurable business processes with approvals and conditions; role-based and user-based security groups; segmented security |
| ServiceNow (system properties, scoped applications, update sets, Flow Designer, Now Assist) | Update sets for promotion; scoped apps; flow designer with subflows and actions; generative AI for authoring flows |
| Atlassian (organisation vs site admin, Jira automation, Rovo agents) | Org-level policies over many products; no-code automation rules (trigger, condition, action) with audit and limits |
| Zendesk (triggers, automations, SLA policies, business schedules) | SLA policies tied to business calendars; trigger ordering |
| Okta / Microsoft Entra ID | SCIM provisioning, conditional access, authentication policies, admin roles with resource sets |
| Slack Enterprise Grid, Linear, Notion | Organisation-wide policies vs workspace settings; clean settings information architecture; personal preferences |
| Stripe dashboard | Team roles, restricted API keys, test mode as sandbox, event and webhook admin |
| Vercel, Retool | Environment promotion, audit logs, access requests |
| Clio | Practice areas, custom fields, firm vs user settings, roles for legal staff |
| Relativity | Workspace permissions, item-level security, group-based access across matters |
| iManage, NetDocuments, Intapp Walls | Ethical walls and matter-centric security, need-to-know access |
| Harvey | Workspace admin, data controls and AI usage governance for legal teams |
| Court and arbitral case management systems | Case-type configuration, procedural deadlines, registry roles |

## 8. Agreed decisions

| # | Topic | Decision |
|---|---|---|
| D1 | Package scope | The monorepo scope is `@nomology/*` (as defined in [[FND-monorepo]]).  |
| D2 | Settings permissions | `write` is an allowed action, used only for settings: `settings.<catalogue>:write`, where `<catalogue>` is the catalogue name (`security`, `access`, `cases`, `workflow`, `notifications`, `integrations`, `branding`, `data`, `billing`, `ai`, `personal`, `platform`). Do not use `settings.x:update`. |
| D3 | Change sets | The single unit of configuration change, review, publish and rollback is the **change set**, table `config.change_set`, API `/admin/v1/change-sets`, owned by [[PKG-configuration-lifecycle]]. Admin-console history ([[APP-admin-change-history]]) reads change sets; there is no separate `admin_change_set` table. Every change records `via` (console, api, bulk, copilot, support, scim, system). |
| D4 | Paths | Tenant admin console `/admin/...`, platform console `/platform/...` (old `/ops` redirects only), tenant admin API `/admin/v1/...` (old `/v1/admin` is a 12-month alias only), personal settings `/me/settings`, SCIM `/scim/v2`. |
| D5 | Database roles | Canonical Postgres roles are those in the MT nodes: `nomo_owner`, `nomo_migrator`, `nomo_app`, `nomo_worker`, `nomo_reporting`, `nomo_platform_ops`. Older names (`app_rw`, `app_ro`, `app_reporting`, `app_rls_user`) are replaced. |
| D6 | Roles | Accepted: case-level role `tribunal_secretary`; groups as assignees; **managed role templates** (`secretariat_lead`, `case_finance_officer`, `reporting_viewer`, `regulatory_reporter`, `regulatory_approver`, `privacy_officer`) that Nomology maintains and tenants can clone; rule "an admin may only grant permissions they hold"; tenant admins get the permission simulator, not live impersonation of their own users; settings persona alias `staff_admin` = any tenant administrative role; `membership.kind` = `staff` or `external`. |
| D7 | AI enablement | Tenant AI enablement is a setting (`ai.policy.enabled`, `ai.features.<key>.enabled`); feature flags keep only platform availability and `ai.killswitch`. AI settings at unit, case-type and case scope can only narrow. |
| D8 | AI output acceptance | Default: AI output is a suggestion until a human accepts it. Exception: the HITL state `accepted_by_policy`, off by default, allowed only for calibrated internal classification and extraction steps with no effect on the merits or on parties' rights; flagged for CTO decision. |
| D9 | One home per setting key | Each setting key is defined in exactly one catalogue; other catalogues link to it. Procedural deadlines, reminder offsets tied to procedure and service windows → `PKG-settings-cases-and-workflows`; delivery mechanics (channels, quiet hours, digests) → `PKG-settings-notifications`; network zones and API key policy → `PKG-settings-security-and-identity`; `access.support.*` and `access.bulk.*` → `PKG-settings-access-control` (moved from platform operations; platform operations keeps only `platform.*`); tenant default language → `PKG-settings-branding-content`. |
| D10 | Permission catalogue is complete | Every permission key used anywhere must appear in [[PKG-permission-catalogue]]. Keys proposed by other groups are added there. |
| D11 | Plan names | Plan tiers everywhere use the names defined in [[BIL-plans-entitlements-and-usage]]. |
| D12 | Tenant type and offerings | Accepted: platform/region/offering values may target a `tenant_type`; Nomology-managed tenant values; tenant columns `primary_offering`, `offerings`, `parent_tenant_id`, `customer_account_id`; `sandbox` tenant type. |
| D13 | Calendars | [[PKG-calendars-and-deadline]] owns calendar computation; [[WF-sla-and-business-calendars]] owns configuration of business schedules and SLA policies. Seat calendars (procedural) vs business schedules (internal SLA) is the accepted split. |
