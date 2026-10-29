---
id: "PKG-settings-ai"
title: "AI settings"
parent: "PKG-settings-catalogue"
order: 2
type: "feature"
template: "config"
status: "draft"
owner: null
indicative: false
summary: "Catalogue of every `ai.*` setting by scope: policy and notice, features, data use and retention, models, review and labelling, neutrals' use and disclosure, party opt-outs, budgets, agents, admin copilot, workflow AI steps and personal preferences, with blueprint defaults"
links: []
rev: 1
syncHash: "d8b4b58375470c96"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.7.3.2 AI settings

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Catalogue of every `ai.*` setting by scope: policy and notice, features, data use and retention, models, review and labelling, neutrals' use and disclosure, party opt-outs, budgets, agents, admin copilot, workflow AI steps and personal preferences, with blueprint defaults

<!-- section:purpose -->
## Purpose and scope

This catalogue registers every setting in the `ai` domain: what AI may do for a tenant, where, with which data, under which review, labelling, disclosure and spending rules. Behaviour lives in the owning nodes; this node is the single list of keys, defaults, scopes, locks, permissions and audit classes.

**Consumers**

| Consumer | Uses |
|---|---|
| [[AI-tenant-ai-policy]] | All `ai.policy.*`, `ai.features.*`, `ai.data.*`, `ai.models.*`, `ai.review.*`, `ai.labelling.*`, `ai.disclosure.*`, `ai.neutrals.*`, `ai.parties.*` keys, through `ai-policy.decide()` |
| [[AI-ai-gateway]], [[AI-guardrails]] | Resolved obligations (route set, redaction, retention) |
| [[AI-cost-controls]] | `ai.budget.*`, `ai.quota.*` |
| [[AI-agent-configuration]] | `ai.agents.*` |
| [[APP-admin-copilot]] | `ai.copilot.*` |
| [[WF-ai-steps-and-agents]] | `ai.workflow_steps.*` |
| [[AI-human-in-the-loop]], [[AI-ai-generated-text-labelling-and]] | `ai.review.*`, `ai.labelling.*`, `ai.disclosure.*` |
| Persona apps | `ai.personal.*` |

**Not settings here**

- Release availability of a feature in a region (`ai.feature.<key>` flags) and the regional kill switch `ai.killswitch`: [[PKG-feature-flags]].
- Model routes, provider credentials and prices: platform tables in [[AI-ai-gateway]] and [[AI-cost-controls]]; credentials in the secrets manager ([[INF-secrets-and-keys]]).
- Prompt versions and pins: [[AI-prompt-management]].
- Agent definitions themselves (they are configuration objects, not settings): [[AI-agent-configuration]].
- What a plan includes (AI features, token allowance): entitlements in [[BIL-plans-entitlements-and-usage]] and [[PKG-settings-billing-and-plans]].
- Retention of case records generally: [[PKG-settings-data-and-privacy]]; this catalogue only holds AI-specific retention.

<!-- section:scopes -->
## Scopes that apply

| Scope | Used | Administered by | Typical use |
|---|---|---|---|
| `platform` | yes | `platform_admin` with `platform_security` approval | Hard bounds (no training, zero retention, mandatory review), defaults |
| `region` | yes | `platform_admin` / `regional_ops` | Providers permitted in the region; features released in the region (flags, not here) |
| `offering` | yes | `platform_admin` | CORD vs TERES defaults (for example `live_captions` relevant to TERES hearings) |
| `tenant` | yes | `ai_admin`, `tenant_admin`, `tenant_owner` (notice and T3 widening), `security_admin` (data and model keys as checker) | The tenant AI policy |
| `unit` | yes | `unit_admin` (narrow only) | A desk with stricter rules, unit budget share |
| `case_type` | yes | `workflow_designer` within blueprint drafts | Feature on or off per case type, AI steps |
| `case` | limited | Case manager, presiding neutral | Only the case restriction (`ai.case.restriction`); party opt-outs are records, not settings |
| `user` | limited | The user | Personal display preferences (`ai.personal.*`) only; a user can never widen AI use |

<!-- section:catalogue -->
## Settings catalogue

Permissions: tenant-scope policy keys are edited as an AI policy draft with `ai.policy:configure` and published with `ai.policy:publish`; unit and case-type values use `settings.ai:write` at that scope. **MC** = maker-checker ([[PKG-separation-of-duties]]). "Narrow now / widen on publish" means a change that reduces AI use takes effect within 5 seconds after publish without a checker, while a widening change needs approval before publish.

**A. Policy and notice**

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `ai.policy.enabled` | bool | false | platform, region, offering, tenant | yes | `feature.ai.summaries` | `ai.policy:configure` | Off: immediately, including running cases. On: after publish | maker-checker (on), sensitive (off) |
| `ai.policy.notice_version_required` | string (notice version) | current platform notice | platform | yes (platform only) | all | platform only | New enablements blocked until accepted | sensitive |
| `ai.policy.notice_grace_days` | int 0–60 | 30 | platform | yes | all | platform only | On next notice release | sensitive |
| `ai.policy.transparency_statement_published` | bool | true when `ai.policy.enabled` | tenant | no (platform floor true when AI on) | all | `ai.policy:configure` | On publish | standard |
| `ai.policy.transparency_statement_extra_text` | rich text, 2,000 chars, sanitised | empty | tenant | no | all | `ai.policy:configure` | On publish | standard |
| `ai.policy.contact_email` | email | tenant DPO contact | tenant | no | all | `ai.policy:configure` | On publish | standard |

**B. Features (one key per catalogue feature; scopes narrow only below tenant)**

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `ai.features.case_summary.enabled` | bool | false | platform, offering, tenant, unit, case_type | yes | `feature.ai.summaries` | `ai.policy:configure`; `settings.ai:write` (unit, case_type) | Narrow now / widen on publish | maker-checker (widen) |
| `ai.features.bundle_summary.enabled` | bool | false | platform, offering, tenant, unit, case_type | yes | `feature.ai.summaries` | as above | as above | maker-checker (widen) |
| `ai.features.document_classification.enabled` | bool | false | platform, offering, tenant, unit, case_type | yes | `feature.ai.summaries` | as above | as above | maker-checker (widen) |
| `ai.features.metadata_extraction.enabled` | bool | false | platform, offering, tenant, unit, case_type | yes | `feature.ai.summaries` | as above | as above | maker-checker (widen) |
| `ai.features.semantic_search.enabled` | bool | false | platform, offering, tenant, unit, case_type | yes | `feature.ai.summaries` | as above | as above | maker-checker (widen) |
| `ai.features.secretariat_drafting.enabled` | bool | false | platform, offering, tenant, unit, case_type | yes | `feature.ai.summaries` | as above | as above | maker-checker (widen) |
| `ai.features.drafting_assist.enabled` | bool | false | platform, offering, tenant, unit, case_type | yes | `feature.ai.advanced` | as above; first enablement needs `tenant_owner` | as above | maker-checker (widen, tenant owner) |
| `ai.features.transcript_assist.enabled` | bool | false | platform, offering, tenant, unit, case_type | yes | `feature.ai.summaries` | as above | as above | maker-checker (widen) |
| `ai.features.live_captions.enabled` | bool | false | platform, offering, tenant, unit, case_type | yes | `feature.ai.summaries` | as above | Next hearing session | maker-checker (widen) |
| `ai.features.translation_assist.enabled` | bool | false | platform, offering, tenant, unit, case_type | yes | `feature.ai.summaries` | as above | as above | maker-checker (widen) |
| `ai.features.custom_agents.enabled` | bool | false | platform, offering, tenant, unit | yes | `feature.ai.advanced` | as above | as above | maker-checker (widen) |
| `ai.features.workflow_ai_steps.enabled` | bool | false | platform, offering, tenant, case_type | yes | `feature.ai.advanced` | as above | Blueprints published after the change; running cases fall back at next AI step when turned off | maker-checker (widen) |
| `ai.features.admin_copilot.enabled` | bool | false | platform, tenant | yes | `feature.ai.summaries` | `ai.policy:configure` | Next conversation | sensitive |
| `ai.features.<key>.audience_roles` | list of tenant role keys | feature default (for example `secretariat` for `case_summary`) | tenant, unit | yes | all | `ai.policy:configure` | Next AI call | maker-checker (widen) |

**C. Data use, retention and redaction**

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `ai.data.allow_training` | bool, locked false | false | platform | locked at platform | — | none | — | — |
| `ai.data.require_zero_retention` | bool, locked true for case content | true | platform | locked at platform | — | none | — | — |
| `ai.data.redaction_default` | enum `pseudonymise`, `redact` | `pseudonymise` | platform, region, tenant, unit, case_type | yes | all | `ai.policy:configure` (security_admin checker) | Next AI call | maker-checker if loosened |
| `ai.data.pseudonymise_party_names` | bool | false (arbitral), true (SEBI ODR, court) via blueprint | tenant, unit, case_type | yes | all | as above | Next AI call | maker-checker if set false |
| `ai.data.allowed_scopes` | set of `case_documents`, `transcripts`, `tribunal_only`, `tenant_knowledge`, `admin_metadata` | `case_documents`, `transcripts`, `tenant_knowledge`, `admin_metadata` | tenant, unit, case_type | yes | all | as above | Next AI call | maker-checker (widen) |
| `ai.data.allow_deliberations_input` | enum `never`, `presiding_neutral_per_case` | `presiding_neutral_per_case` | platform, tenant | yes | all | as above | Next AI call | maker-checker (widen) |
| `ai.retention.prompt_output_bodies` | enum `case` (with case retention), `days_30`, `days_90`, `metadata_only` | `case` | platform, region, tenant | yes (platform sets allowed values) | all | as above | New requests only; existing bodies keep their class | sensitive |
| `ai.retention.blocked_outputs_days` | int 0–90 | 30 | platform, tenant | yes | all | as above | New blocked outputs | sensitive |
| `ai.retention.unreviewed_output_expiry_days` | int 7–90 | 30 | platform, tenant | yes | all | as above | New outputs | standard |
| `ai.retention.conversation_days` | int 0–365 | 30 | platform, tenant, unit | yes | all | as above | New conversations | sensitive |

**D. Models and providers**

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `ai.models.permitted_providers` | set of provider keys | per region (for example `bedrock` in `in` and `sg`) | platform, region | yes | — | platform only | Next AI call | maker-checker (platform) |
| `ai.models.allowed_providers` | subset of region's permitted providers | all permitted | tenant | yes | all | `ai.policy:configure` (security_admin checker) | Next AI call | maker-checker |
| `ai.models.self_hosted_only` | bool | false | region, tenant | yes | `enterprise` | as above | Next AI call; features without a self-hosted route become unavailable | maker-checker |
| `ai.models.out_of_region_exception` | object {region, provider, agreement ref, expires} or null | null | tenant (platform-written only) | yes, platform only | `enterprise` | `platform.ai.exception:approve` | On approval; ends at expiry | maker-checker (platform security + legal) |

**E. Review and labelling**

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `ai.review.approver_roles.<feature>` | list of case or tenant roles, narrower than feature default | feature default ([[AI-human-in-the-loop]]) | tenant, unit, case_type | yes | all | `ai.policy:configure` | New outputs | maker-checker (widen) |
| `ai.review.require_open_before_approve` | bool | true | platform, tenant | yes (platform floor true for T3) | all | as above | Next review | maker-checker if false |
| `ai.review.second_reviewer.<feature>` | bool | false (true not required by platform) | tenant, unit, case_type | yes | all | as above | New outputs | standard |
| `ai.review.sample_audit_percent` | int 2–100 | 2 | platform, tenant | yes (floor 2) | all | as above | Next monthly sample | standard |
| `ai.review.share_reviewer_metrics_with_tenant` | bool | false | tenant | no | all | `ai.policy:configure` (tenant_owner) | Next report | sensitive |
| `ai.labelling.show_in_issued_documents` | bool | false | tenant, case_type | yes | all | `ai.policy:configure` | Documents issued after publish | standard |
| `ai.labelling.label_ai_drafted_messages` | bool | false | tenant, case_type | yes | all | as above | Messages sent after publish | standard |
| `ai.labelling.labels_enabled` | bool, locked true | true | platform | locked | — | none | — | — |

**F. Neutrals, disclosure and parties**

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `ai.neutrals.drafting_assist_allowed` | enum `no`, `on_request_per_case`, `yes` | `no` | tenant, unit, case_type | yes | `feature.ai.advanced` | `ai.policy:configure` (tenant_owner for first change from `no`) | New sessions | maker-checker |
| `ai.neutrals.bundle_summary_allowed` | bool | false | tenant, unit, case_type | yes | `feature.ai.summaries` | as above | New outputs | maker-checker (widen) |
| `ai.disclosure.neutral_use` | enum `none`, `record_only`, `notify_parties`, `statement_in_document` | `record_only` | tenant, case_type | yes | all | as above | Documents and notices after publish; pinned per case at start | maker-checker |
| `ai.disclosure.statement_template_key` | template key ([[PKG-document-and-notification]]) | platform default statement | tenant, case_type | no | all | `ai.policy:configure`, `content_admin` edits template | On publish; pinned per case | standard |
| `ai.disclosure.secretariat_use` | enum `none`, `record_only`, `transparency_statement` | `transparency_statement` | tenant | yes | all | `ai.policy:configure` | On publish | standard |
| `ai.parties.opt_out_mode` | enum `not_offered`, `on_request`, `ask_at_filing` | `not_offered` | tenant, case_type | yes | all | `ai.policy:configure` | New cases (ask at filing); immediately (on request) | maker-checker |
| `ai.parties.opt_out_notice_text_key` | legal text key ([[I18N-legal-declaration-and-consent]]) | platform default | tenant | no | all | `content_admin` | On publish | sensitive |
| `ai.case.restriction` | enum `none`, `no_party_documents`, `off`, per feature list | `none` | case | no | all | `ai.case_restriction:update` (case manager, presiding neutral) | Immediately, including running steps | sensitive |

**G. Budgets and quotas** (behaviour in [[AI-cost-controls]])

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `ai.budget.monthly_limit` | money (tenant billing currency) or token units, at most the entitlement | entitlement | tenant | yes (entitlement ceiling) | per plan | `ai.budget:update` | Immediately | sensitive |
| `ai.budget.unit_allocations` | map unitId → percent or amount, total at most 100 percent | none (shared pool) | tenant, unit (own unit, lower only) | yes | `standard` and `enterprise` | `ai.budget:update` | Immediately | standard |
| `ai.budget.feature_caps` | map feature → percent of tenant budget | none | tenant, unit | yes | all | `ai.budget:update` | Immediately | standard |
| `ai.budget.alert_thresholds` | list of percents | 50, 80, 100 | platform, tenant | no | all | `ai.budget:update` | Next threshold crossing | standard |
| `ai.budget.alert_recipients` | roles and emails | `ai_admin`, `billing_admin` | tenant | no | all | `ai.budget:update` | Next alert | standard |
| `ai.budget.on_limit` | enum `stop_interactive_pause_pipelines`, `stop_all_ai` | `stop_interactive_pause_pipelines` | platform, tenant | yes | all | `ai.budget:update` | Immediately | standard |
| `ai.budget.allow_overage` | bool | false | tenant | yes (plan) | plans with overage | `ai.budget:update` (billing_admin checker) | Next billing period | maker-checker |
| `ai.quota.<feature>.user_daily_requests` | int 0–1,000 | feature default (for example 30 for `drafting_assist`) | platform, tenant, unit | yes (platform ceiling) | all | `ai.budget:update` | Next day | standard |
| `ai.quota.tenant_requests_per_minute` | int | plan default | platform, tenant | yes (platform ceiling) | per plan | platform only above plan | Immediately | standard |
| `ai.budget.single_request_max_percent` | int 1–20 | 5 | platform, tenant | yes | all | `ai.budget:update` | Next AI call | standard |

**H. Agents** (behaviour in [[AI-agent-configuration]])

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `ai.agents.builders` | list of roles or groups | `ai_admin` | tenant | yes | `feature.ai.advanced` | `ai.policy:configure` | Immediately | sensitive |
| `ai.agents.allowed_surfaces` | set of `secretariat`, `neutral`, `transcriber`, `admin`, `workflow_only` | `secretariat`, `admin`, `workflow_only` | platform, tenant | yes | `feature.ai.advanced` | as above | New publishes | maker-checker (widen) |
| `ai.agents.allowed_tools` | set of tool keys from the registry | all read tools; propose tools off | platform, tenant | yes | `feature.ai.advanced` | as above | New publishes; suspends agents using a removed tool | maker-checker (widen) |
| `ai.agents.tool_policies` | list of rules {tool, roles or units, action `block` or `confirm`} | none | tenant, unit | yes | `feature.ai.advanced` | as above | Next tool call | standard |
| `ai.agents.max_published` | int | plan default (for example 10) | platform, tenant | yes (plan) | per plan | platform only above plan | New publishes | standard |
| `ai.agents.min_test_cases` | int 10–200 | 10 | platform, tenant | yes (platform floor) | all | `ai.policy:configure` | New publishes | standard |
| `ai.agents.max_steps_per_turn` | int 1–8 | 8 | platform, tenant | yes (platform ceiling) | all | as above | New conversations | standard |
| `ai.agents.review_interval_months` | int 1–24 | 6 | tenant | no | all | as above | Next review date | standard |

**I. Admin copilot** (behaviour in [[APP-admin-copilot]])

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `ai.copilot.enabled` | bool | false | platform, tenant | yes | `feature.ai.summaries` | `ai.policy:configure` | Next conversation | sensitive |
| `ai.copilot.users` | list of admin roles | `tenant_admin`, `ai_admin`, `workflow_designer`, `user_admin` | tenant | yes | `feature.ai.summaries` | as above | Next conversation | sensitive |
| `ai.copilot.draft_domains` | set of setting domains and object kinds | all except `auth` and `access` | platform, tenant | yes | `feature.ai.summaries` | as above | Next conversation | maker-checker (widen) |
| `ai.copilot.read_audit_metadata` | bool | true (still requires the admin's `audit.log:read`) | tenant | no | `feature.ai.summaries` | as above | Next conversation | sensitive |
| `ai.copilot.conversation_retention_days` | int 0–365 | 90 | platform, tenant | yes | all | as above | New conversations | sensitive |

**J. Workflow AI steps** (behaviour in [[WF-ai-steps-and-agents]])

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `ai.workflow_steps.allowed_kinds` | set of `summarise`, `classify`, `extract`, `draft`, `agent_task` | `classify`, `extract`, `summarise` | platform, tenant, case_type | yes | `feature.ai.advanced` | `ai.policy:configure` | Blueprint publishes after change | maker-checker (widen) |
| `ai.workflow_steps.allow_auto_accept` | bool (enables the `accepted_by_policy` state, [[AI-human-in-the-loop]]; D8, CTO decision pending) | false | platform, tenant, case_type (case type may only turn it off) | yes | `feature.ai.advanced` | as above | Blueprint publishes after change; turning off downgrades running steps to `always` at once | maker-checker (on) |
| `ai.workflow_steps.min_auto_accept_threshold` | decimal 0.85–0.99 | 0.85 platform floor; tenant may raise | platform, tenant | yes (floor) | `feature.ai.advanced` | as above | Next AI step | standard |
| `ai.workflow_steps.min_sample_percent` | int 2–100 | 5 | platform, tenant | yes (floor 2) | `feature.ai.advanced` | as above | Next AI step | standard |
| `ai.workflow_steps.max_calls_per_case` | int 1–200 | 50 | platform, tenant, case_type | yes (ceiling 200) | all | as above | New cases; running cases at next step | standard |

**K. Personal preferences** (user scope; display only, see [[PKG-settings-personal]])

| Key | Type and allowed values | Platform default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `ai.personal.show_ai_panels` | bool | true | user | no | all | the user | Next page load | standard |
| `ai.personal.summary_length` | enum `short`, `standard`, `detailed` | `standard` | user | no | all | the user | Next request | standard |
| `ai.personal.output_language` | locale from tenant's allowed list | UI language | tenant (allowed list), user | yes (tenant allowed list) | all | the user | Next request | standard |

<!-- section:validation -->
## Validation and dependencies

**Dependencies**

- Any `ai.features.<key>.enabled = true` requires `ai.policy.enabled = true` and a current notice acceptance in `tenant_ai_decisions`.
- `ai.features.drafting_assist.enabled = true` requires `ai.neutrals.drafting_assist_allowed ≠ no` and `ai.disclosure.neutral_use` to be set explicitly (not inherited) at tenant scope.
- `ai.features.custom_agents.enabled = true` requires at least one role in `ai.agents.builders` and `ai.agents.allowed_surfaces` non-empty.
- `ai.workflow_steps.allow_auto_accept = true` requires `ai.features.workflow_ai_steps.enabled = true`; `allowed_kinds` including `agent_task` requires `custom_agents` enabled.
- `ai.data.allowed_scopes` including `tribunal_only` requires every feature that uses it to have an approver role that is a tribunal role.
- `ai.models.allowed_providers` must leave at least one active in-region route per enabled feature's capability, or the admin sees "These features would stop working: …" and must confirm.
- `ai.budget.unit_allocations` totals at most 100 percent; `ai.budget.monthly_limit` at most the entitlement.
- `ai.parties.opt_out_mode ≠ not_offered` requires an opt-out notice text in every enabled locale.

**Platform bounds enforced by the resolver regardless of tenant choice:** training never; zero retention for case content; in-region routes only (except an approved exception); labels always on; human approval for party-facing and record outputs; `require_open_before_approve` true for T3; auto-accept threshold floor 0.85 and sample floor 2 percent; agent step ceiling 8; workflow AI calls per case ceiling 200.

**Narrow-only rule:** at `unit`, `case_type` and `case` scope, a value may only be equal to or stricter than the inherited value (strictness order defined per key in the registry). A more permissive value fails with `SETTING_WIDENS_PARENT` and the message "This would allow more AI use than your organisation's AI policy. Ask an AI administrator."

**Invalid change display:** the console lists every failing rule with the key, the conflicting key and the fix; drafts from the copilot get the same list.

<!-- section:defaults -->
## Defaults by tenant type

Blueprint defaults applied at tenant creation ([[PKG-configuration-packages]]). AI is off at creation for every blueprint; these are the values that apply once the tenant turns AI on.

| Key | Arbitral institution | SEBI ODR institution | CORD tenant | Court or government programme |
|---|---|---|---|---|
| `ai.features.case_summary.enabled` | true | true | true | false |
| `ai.features.document_classification.enabled` | true | true | true | true |
| `ai.features.metadata_extraction.enabled` | true | true | true | false |
| `ai.features.bundle_summary.enabled` | true | false | false | false |
| `ai.features.secretariat_drafting.enabled` | true | true | true | false |
| `ai.features.drafting_assist.enabled` | false | false | false | false |
| `ai.features.transcript_assist.enabled` | true | false | false | true |
| `ai.features.live_captions.enabled` | true | false | false | true |
| `ai.features.custom_agents.enabled` | false | false | false | false |
| `ai.features.workflow_ai_steps.enabled` | true | true | true | false |
| `ai.neutrals.drafting_assist_allowed` | `on_request_per_case` | `no` | `no` | `no` |
| `ai.disclosure.neutral_use` | `record_only` | `notify_parties` | `record_only` | `statement_in_document` |
| `ai.data.pseudonymise_party_names` | false | true | true | true |
| `ai.parties.opt_out_mode` | `not_offered` | `on_request` | `not_offered` | `on_request` |
| `ai.workflow_steps.allow_auto_accept` | false | false | false | false |
| `ai.review.second_reviewer.bundle_summary` | false | — | — | — |
| `ai.retention.conversation_days` | 30 | 30 | 30 | 7 |

`ai.workflow_steps.allow_auto_accept` is false in every blueprint (decision D8: off by default, allowed only for calibrated internal classification and extraction steps with no effect on the merits or on parties' rights; flagged for CTO decision). A tenant turns it on explicitly, with maker-checker.

**Why they differ**

- **Arbitral institutions** (for example HKIAC-type administered arbitration) handle professional parties with counsel and long bundles, so summaries, captions and transcript help have the most value; neutral drafting help stays off unless requested per case, because institution rules on tribunal AI use vary (assumption: to be confirmed per institution).
- **SEBI ODR institutions** serve many unrepresented investors; defaults favour pseudonymisation, disclosure to parties and a party opt-out on request, and no auto-accept, because conciliation and arbitration timelines are prescribed by SEBI circulars and routing errors are costly. Assumption: no SEBI circular currently prescribes AI-specific rules for ODR institutions; to be confirmed by legal and with the MII.
- **CORD tenants** (B2B and consumer dispute programmes) favour volume features (classification, extraction, drafting of routine letters).
- **Court or government programmes** default to the most conservative choices: no summaries on the merits record, statements in documents, short conversation retention, no auto-accept.

<!-- section:admin_ux -->
## Where it is administered

| Group | Console location | API |
|---|---|---|
| Policy, notice, transparency (A, F) | Tenant admin console → AI → Policy (`/admin/ai/policy`); notice acceptance at `/admin/ai/policy/notice` | `GET/PATCH /admin/v1/settings/ai.policy.*` in a draft; `POST /admin/v1/ai/notice/accept` |
| Features (B) | AI → Features (`/admin/ai/features`), a matrix of features × units and case types with lock and source shown in each cell | `PATCH /admin/v1/settings/ai.features.*` |
| Data, retention, models (C, D) | AI → Data and models (`/admin/ai/data`) | `PATCH /admin/v1/settings/ai.data.*`, `ai.retention.*`, `ai.models.*` |
| Review, labelling, neutrals (E, F) | AI → Review and disclosure (`/admin/ai/review`) | `PATCH /admin/v1/settings/ai.review.*` etc. |
| Budgets and quotas (G) | AI → Usage and budgets (`/admin/ai/usage`) | `PATCH /admin/v1/settings/ai.budget.*`, `GET /admin/v1/ai/usage` |
| Agents (H) | AI → Agents (`/admin/ai/agents`) settings tab | `PATCH /admin/v1/settings/ai.agents.*` |
| Copilot (I) | AI → Admin copilot (`/admin/ai/copilot`) | `PATCH /admin/v1/settings/ai.copilot.*` |
| Workflow steps (J) | AI → Workflow steps (`/admin/ai/workflow-steps`); per case type inside the authoring studio | `PATCH /admin/v1/settings/ai.workflow_steps.*` |
| Case restriction | Case page → AI tab (secretariat console, neutral workspace) | tRPC `cases.ai.setRestriction` |
| Personal (K) | User menu → Preferences → AI ([[PKG-personalisation]]) | tRPC `me.preferences.update` |
| Platform bounds | Platform console → AI → Bounds and routes (`/platform/ai/bounds`, `/platform/ai/routes`) | `/platform/v1/settings/ai.*` |

Every value shows its effective value, its source scope ("Platform default", "Locked by platform", "Set by Singapore office") and a lock icon where a higher scope enforces it. The **admin copilot** may propose changes to any key in `ai.copilot.draft_domains` except `ai.copilot.*` itself, and its drafts are marked AI-proposed. A read-only page "How AI is used here" at `/admin/ai` summarises the effective policy in plain language for all staff.

<!-- section:change_control -->
## Change control and audit

| Change | Approval | Notified |
|---|---|---|
| Turning AI or any feature on; widening scopes, audiences, data scopes, providers, retention, auto-accept | Maker-checker (second `ai_admin` / `tenant_admin`); data and model keys need a `security_admin` checker | Tenant owner and AI admins |
| First enablement of a T3 feature (`drafting_assist`) or first change of `ai.neutrals.drafting_assist_allowed` from `no` | Tenant owner as checker | Tenant owner, Nomology account owner |
| Narrowing changes and the tenant kill switch | No checker; publish immediately | AI admins; affected unit admins |
| Budget changes within entitlement | Single `ai_admin` or `billing_admin` | Billing admin |
| Overage on | Maker-checker with `billing_admin` | Billing admin, Nomology account owner |
| Platform bounds, region providers | Platform admin plus platform security; legal for retention bounds | All tenant AI admins in the region when it affects them |
| Out-of-region exception | Platform security plus Nomology legal, with the tenant owner's signed agreement | Tenant owner |

Audit record per change: key, scope and scope ID, old value, new value, actor, approver, reason (required for widening), policy version, change set ID, origin (`console`, `api`, `copilot`, `package`). Events: `admin.settings.published` with domain `ai`, plus `admin.ai.policy_published`. Rollback publishes the previous policy version in one action and is itself audited.

<!-- section:migration -->
## Versioning and migration

- Keys are never reused; renamed keys keep an alias for two releases.
- **Migration from flags (this overhaul):** today tenant enablement is recorded as flag rules on `ai.enabled` and `ai.feature.<name>`. A one-off migration writes equivalent `ai.policy.enabled` and `ai.features.<key>.enabled` values at tenant scope, keeps the flags as platform availability only (decision D7; [[PKG-feature-flags]] FLAG-R-7), and removes tenant-targeted rules from them. Tenants are told in release notes; values are identical before and after.
- New features add a key `ai.features.<key>.enabled` with default false at platform; existing tenants never get a new feature on by default.
- Changed platform defaults apply only to tenants inheriting them; tenants with explicit values are listed in the release notes.
- AI settings travel in configuration packages ([[PKG-configuration-packages]]) except `ai.models.out_of_region_exception` and notice acceptances, which are tenant-specific legal records and are never copied.

<!-- section:testing -->
## Testing

- The registry `packages/settings/registry/ai.ts` is the source of truth; CI generates this catalogue's table and fails if they differ.
- Resolution tests per key: inheritance across all allowed scopes, locks, plan entitlement off, narrow-only rule at unit, case type and case.
- Dependency tests for every rule in Validation, including copilot-drafted invalid combinations.
- Policy integration tests: each key changes the `ai-policy.decide()` result as specified ([[AI-tenant-ai-policy#verification]]).
- Point-in-time test: the effective AI policy for a case on a past date is reproduced from history.

<!-- section:questions -->
## Open questions

- [ ] Budget unit shown to tenants: currency, credits or tokens (carried from [[AI-cost-controls]]). (owner: billing)
- [x] Plan names follow [[BIL-plans-entitlements-and-usage]] (decision D11): the Plan column uses the entitlement keys `feature.ai.summaries` (all plans), `feature.ai.advanced` (custom agents, workflow AI steps and auto-accept; added to the BIL feature catalogue) and the `enterprise` plan. Commercial to confirm whether basic AI stays included in every plan, as BIL states, rather than being an add-on. (owner: billing)
- [ ] Should `ai.retention.prompt_output_bodies = metadata_only` be offered, given it weakens our ability to explain past outputs? (owner: legal, AI governance lead)
- [ ] Defaults for court and government programmes to be validated with the first such tenant. (owner: product)

- [x] The AI permissions (`ai.policy:read`, `:configure`, `:approve`, `:publish`, `ai.budget:update`, `ai.case_restriction:update`, `ai.party_opt_out:create`, `ai.notice:approve`, `ai.audit:read`, `ai.audit:export`) are now in [[PKG-permission-catalogue]] (decision D10).

<!-- section:notes -->
## Notes

Pattern borrowed from: tenant-level controls to turn off publishing of generative agents and to govern agent knowledge and actions [R1]; workspace retention periods chosen by legal customers [R2]; zero data retention and masking applied to every call in a trust layer [R3].

<!-- checks -->
## Template checks

<!-- check:inheritance -->
### Inheritance and locks

Every key lists its scopes and lockability; resolution follows [[PKG-configuration-scope-hierarchy]], with the narrow-only rule below tenant and platform locks on the hard bounds. The console shows the effective value and its source for every key, including in the features matrix.

<!-- check:permissions -->
### Who may change what

Tenant policy keys need `ai.policy:configure` and `ai.policy:publish`; unit and case-type values need `settings.ai:write` at that scope; budgets need `ai.budget:update`; case restriction needs `ai.case_restriction:update`; data and model keys need a security admin checker; platform bounds are platform-only.

<!-- check:safety -->
### Safe bounds

Platform bounds (no training, zero retention, in-region, labels, human approval, thresholds) are locked at platform; widening changes need maker-checker; T3 needs the tenant owner; dependencies are validated server-side; the narrow-only rule prevents lower scopes from widening.

<!-- check:timing -->
### When changes take effect

Each key states when it applies. Narrowing applies within 5 seconds, including to running workflows at their next AI step; disclosure templates are pinned per case at start; feature and step widening applies to new calls and new blueprint publishes only.

<!-- check:audit -->
### Audit and rollback

Changes are versioned AI policy publishes with actor, approver, reason, old and new value and origin; `ai_requests.policy_version` reproduces the policy for any output; rollback is one audited action.

<!-- check:sync -->
### Catalogue matches code

The typed registry `packages/settings/registry/ai.ts` generates this table; CI fails on drift; new keys need an owner node, default, scopes, strictness order and audit class before merge.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Admins govern agent actions, connectors, knowledge sources, HTTP requests, channel publication and authentication through data policies; can turn off publishing of agents that use generative AI for a tenant; makers see a security warning and risk assessment before publishing; maker activity is audited.",
    "id": "R1",
    "kind": "vendor",
    "title": "Microsoft Copilot Studio: Security and governance",
    "url": "https://learn.microsoft.com/en-us/microsoft-copilot-studio/security-and-governance",
    "vendor": "Microsoft"
  },
  {
    "excerpt": "Customers set a workspace retention period for data such as assistant queries, from hours after processing up to 30 days after the agreement ends; some stores have their own retention setting.",
    "id": "R2",
    "kind": "vendor",
    "title": "Understanding Retention Policies",
    "url": "https://help.harvey.ai/articles/understanding-retention-policies",
    "vendor": "Harvey"
  },
  {
    "excerpt": "Trust layer features: grounding in customer data, data masking, toxicity detection, audit trail and feedback, and zero data retention agreements with third-party model providers.",
    "id": "R3",
    "kind": "vendor",
    "title": "Agentforce Developer Guide: Trust Layer",
    "url": "https://developer.salesforce.com/docs/ai/agentforce/guide/trust.html",
    "vendor": "Salesforce"
  }
]
```

<!-- end -->
