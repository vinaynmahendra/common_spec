---
id: "AI-tenant-ai-policy"
title: "Tenant AI policy and feature controls"
parent: "AI"
order: 10
type: "capability"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "One versioned AI policy per tenant (features on per scope, permitted models per region, data use and retention, review, labelling, disclosure, party opt-outs) and the fail-closed decision function every AI call, agent and workflow step must pass"
links: []
rev: 1
syncHash: "3fd4f8f1656ec6e2"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 8.10 Tenant AI policy and feature controls

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> One versioned AI policy per tenant (features on per scope, permitted models per region, data use and retention, review, labelling, disclosure, party opt-outs) and the fail-closed decision function every AI call, agent and workflow step must pass

<!-- section:purpose -->
## Purpose and scope

The tenant AI policy is the single, versioned decision about **whether, where and how AI may be used** for one tenant, and the runtime check that enforces that decision on every AI call. It turns the platform's AI principles ([[AI#principles]]) into choices a tenant can make and Nomology can audit.

It answers, for any AI request: *Is this feature allowed for this tenant, unit, case type and case? For this person or agent? On these documents? With which models, in which region? Under which review, labelling, retention and disclosure obligations?*

**Who relies on it**

| Consumer | How it uses the policy |
|---|---|
| [[AI-ai-gateway]] | Calls `ai-policy.decide()` as the first check on every request; refuses before any data leaves the service |
| [[AI-agent-configuration]] | Checks the policy at agent publish time and again on every tool call |
| [[WF-ai-steps-and-agents]] | Validates AI steps when a case-type blueprint is published; re-checks at run time |
| [[APP-admin-copilot]] | Is itself a feature governed by the policy; its drafts of AI settings are validated against platform bounds |
| [[AI-human-in-the-loop]] | Receives the review obligation (who must approve, review mode) from the decision |
| [[AI-ai-generated-text-labelling-and]] | Receives the label and disclosure obligations |
| Persona apps ([[APP-neutral-workspace]], [[APP-secretariat-console]], [[APP-transcriber-workspace]]) | Ask the same decision function to show, hide or explain AI controls |

**What the policy is made of**

1. **AI settings** in the `ai` domain ([[PKG-settings-ai]]), resolved through the scope hierarchy ([[PKG-configuration-scope-hierarchy]]): platform → region → offering → tenant → unit → case type → case → user.
2. **The tenant's AI decision record** (`tenant_ai_decisions`): which AI notice version the tenant accepted, who accepted it and when ([[AI-ai-governance-and-impact]]).
3. **Case-level restrictions and party opt-out records** set during a case.
4. **Platform hard bounds** that no tenant can cross (no training on tenant data, in-region processing only, mandatory human approval for anything that reaches a party or the record, no AI decisions on the merits).

**What changes with this node.** Before this overhaul, tenant AI enablement was modelled as feature flags (`ai.enabled`, `ai.feature.<name>`). From now on, flags only express **platform availability** (is the feature released in this region?) and the **operational kill switch** (`ai.killswitch`), as [[PKG-feature-flags]] intends. **Tenant choices are settings** (`ai.policy.enabled`, `ai.features.<feature>.enabled` and others), so they follow the configuration lifecycle ([[PKG-configuration-lifecycle]]), can be locked, previewed in a sandbox and moved in configuration packages ([[PKG-configuration-packages]]).

Pattern borrowed from: organisation-level AI controls that switch generative features on per product and audience in enterprise stacks, and trust-layer designs that apply masking, zero retention and audit to every call (trust-layer designs with masking, zero retention and audit; organisation-level controls over which audiences may use generative features [R7], [R8]).

<!-- section:assets -->
## Protected assets

| Asset | Classification ([[SEC-data-classification]]) | Why it matters |
|---|---|---|
| Published tenant AI policy (all `ai.*` setting values at tenant, unit and case-type scope) | Tenant-internal | Decides whether case data is sent to a model at all; a wrong value can expose parties' data or put AI into a forbidden use |
| Tenant AI decision record (`tenant_ai_decisions`: notice version, accepting person, date, conditions) | Tenant-internal, legal effect | Evidence that the tenant (the data fiduciary / controller) chose to use AI; needed for ISO/IEC 42001 and contract evidence [R1] |
| Case AI restrictions (`case_ai_restrictions`) | Case participants | A tribunal or case manager may have ordered that no AI be used on a case |
| Party AI opt-out records (`party_ai_preferences`) | Case participants, personal data | A party's request must be honoured on every path, including agents and workflow steps |
| AI feature catalogue and risk tiers (`ai_features`, platform-level) | Public within platform | Defines what each feature may touch; tenants pick from it |
| Region route allow-lists and provider terms (zero retention, no training) | Platform-internal | Determines where data goes |
| AI decisions log (`ai_policy_decisions`, sampled allows, all denies) | Tenant-internal | Lets auditors prove the policy was enforced |
| The action "send case content to a model" | Highest sensitivity action in the AI layer | Every other asset exists to control it |

**AI feature catalogue (platform-defined; tenants cannot add features, only agents and workflow steps built from them)**

| Feature key | What it does | Risk tier ([[AI-ai-governance-and-impact]]) | Output destination |
|---|---|---|---|
| `case_summary` | Summary of a case for internal use | T1 | Internal case notes |
| `bundle_summary` | Summary of a bundle or document set for the tribunal | T2 | Tribunal workspace |
| `document_classification` | Suggests document type and filing category | T1 | Internal metadata |
| `metadata_extraction` | Extracts fields (dates, amounts, party details) into custom fields | T1 (internal) / T2 (if fields drive deadlines or fees) | Case fields after review |
| `semantic_search` | Question answering over one case's documents with citations | T1 | Shown to the asking user only |
| `secretariat_drafting` | Drafts notices, letters and messages | T2 | Sent message or document after approval |
| `drafting_assist` | Drafting help for procedural orders and awards | T3 | The neutral's own draft |
| `transcript_assist` | Spelling and correction suggestions in transcripts | T2 | Approved transcript |
| `live_captions` | Automatic captions in hearings | T2 | Shown live, labelled, never the record |
| `translation_assist` | Draft translations of documents for internal reading | T2 | Internal working copy, labelled |
| `custom_agents` | Tenant-configured assistants ([[AI-agent-configuration]]) | Tier of the most sensitive tool and destination it uses | As the agent's tools allow |
| `workflow_ai_steps` | AI steps inside case-type blueprints ([[WF-ai-steps-and-agents]]) | Per step kind | As the step allows |
| `admin_copilot` | Natural-language administration ([[APP-admin-copilot]]) | T1 | Configuration drafts only |

<!-- section:actors -->
## Actors and roles

| Actor | Role key | How they get it | What they do with the AI policy |
|---|---|---|---|
| Platform admin | `platform_admin` | Nomology staff, JIT elevation ([[PKG-jit-and-break-glass]]) | Sets platform bounds, region route allow-lists, feature availability; approves out-of-region exceptions with security |
| Platform security | `platform_security` | Nomology staff | Second approver for bound changes; owns the regional kill switch with the incident commander |
| Regional operations | `regional_ops` | Nomology staff | Operates routes and kill switch per region |
| Tenant owner | `tenant_owner` | Named in the tenant contract | Accepts the AI notice on behalf of the institution (the legal decision); approves policy changes that widen AI use |
| Tenant AI admin | `ai_admin` | Assigned by tenant owner or tenant admin ([[APP-user-and-access-admin]]) | Drafts and publishes the AI policy, feature toggles, budgets, agents |
| Tenant admin | `tenant_admin` | Assigned by tenant owner | Can do everything an `ai_admin` can, except accept the AI notice |
| Security admin | `security_admin` | Assigned | Checker for AI data and retention settings (maker-checker) |
| Unit admin | `unit_admin` | Assigned per unit | Can narrow (never widen) AI features for their unit |
| Workflow designer | `workflow_designer` | Assigned | Adds AI steps to blueprints within the policy |
| Auditor | `auditor` | Assigned | Reads policy history, decisions log and AI audit |
| Secretariat / case manager | `secretariat` + case role `case_manager` | Tenant role plus case assignment | Uses AI features; sets case AI restrictions; records party opt-out on a party's behalf |
| Neutral | `neutral` + `presiding_neutral` / `tribunal_member` | Appointment on the case | Uses neutral AI features if the institution allows; presiding neutral can restrict AI on the case |
| Party and counsel | `party`, `counsel` | Case participation | Cannot use internal AI features; can record an AI opt-out where the tenant offers it; see disclosures |
| AI agent principal | `ai_agent` | Created when an agent is published ([[PKG-non-human-principals]]) | Subject to the policy like a user; its effective rights are the intersection described in the policy model |
| Admin copilot | `ai_agent` (system agent `copilot.admin`) | Platform-defined | Can propose AI policy drafts; cannot publish |

<!-- section:matrix -->
## Permission matrix

Legend: **Y** allowed; **N** denied; **C** conditional (note); **—** not applicable. Every cell is decided. Permissions follow [[PKG-permission-catalogue]] naming.

| # | Action (permission) | platform_admin | tenant_owner | tenant_admin | ai_admin | security_admin | unit_admin | workflow_designer | auditor | secretariat | neutral | party / counsel | ai_agent |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Read tenant AI policy (`ai.policy:read`) | C1 | Y | Y | Y | Y | C2 | Y | Y | C3 | C3 | C4 | N |
| 2 | Edit AI policy draft (`ai.policy:configure`) | N | Y | Y | Y | C5 | C2 | N | N | N | N | N | N |
| 3 | Approve AI policy change as checker (`ai.policy:approve` with `config.change_set:approve`) | N | Y | Y | Y | C5 | N | N | N | N | N | N | N |
| 4 | Publish approved AI policy (`ai.policy:publish`) | N | Y | Y | Y | N | N | N | N | N | N | N | N |
| 5 | Accept AI notice for the tenant (`ai.notice:approve`) | N | Y | N | N | N | N | N | N | N | N | N | N |
| 6 | Narrow AI features for a unit (`settings.ai:write` at unit) | N | Y | Y | Y | N | C2 | N | N | N | N | N | N |
| 7 | Set case-type AI options (`settings.ai:write` at case_type) | N | Y | Y | Y | N | N | C6 | N | N | N | N | N |
| 8 | Restrict AI on a case (`ai.case_restriction:update`) | N | N | N | N | N | N | N | N | C7 | C8 | N | N |
| 9 | Lift a case AI restriction | N | N | N | N | N | N | N | N | C9 | C8 | N | N |
| 10 | Record own AI opt-out (`ai.party_opt_out:create`) | — | — | — | — | — | — | — | — | — | — | C10 | N |
| 11 | Record opt-out on a party's behalf | N | N | N | N | N | N | N | N | C7 | N | N | N |
| 12 | Use an AI feature (`ai.generation:create`) | N | C11 | C11 | C11 | N | C11 | C11 | N | C11 | C11 | N | C12 |
| 13 | Approve AI output (`ai.output:approve`) | N | N | N | N | N | N | N | N | C13 | C13 | N | N |
| 14 | View AI usage and spend (`ai.usage:read`) | C1 | Y | Y | Y | N | C2 | N | Y | N | N | N | N |
| 15 | Change AI budgets (`ai.budget:update`) | C14 | Y | Y | Y | N | C2 | N | N | N | N | N | N |
| 16 | Read AI audit records (`ai.audit:read`) | C1 | Y | Y | Y | Y | N | N | Y | N | N | N | N |
| 17 | Export AI audit records (`ai.audit:export`) | N | Y | N | N | Y | N | N | Y | N | N | N | N |
| 18 | Change platform bounds, region routes, feature availability | C15 | N | N | N | N | N | N | N | N | N | N | N |
| 19 | Use the regional kill switch `ai.killswitch` | C16 | N | N | N | N | N | N | N | N | N | N | N |
| 20 | Approve an out-of-region processing exception | C17 | N | N | N | N | N | N | N | N | N | N | N |
| 21 | Turn the tenant's AI off immediately (tenant kill switch `ai.policy.enabled = false`) | N | Y | Y | Y | Y | N | N | N | N | N | N | N |

**Conditions**

- **C1** Only through support access approved by the tenant ([[PKG-support-access-and-impersonation]]); metadata only, no case content.
- **C2** Only for their own unit, and only to narrow: a unit admin can turn a feature off or lower a budget, never turn on something the tenant has off.
- **C3** Read-only summary page "How AI is used in this organisation" (which features are on for them, review duties, disclosure rules); not budgets or audit.
- **C4** Parties and counsel see the published AI transparency statement for the tenant and any case-level disclosure; not the internal policy.
- **C5** Security admin may edit and approve only the data, retention and model sub-sections (`ai.data.*`, `ai.models.*`, `ai.retention.*`), and is the required checker for any change there.
- **C6** Workflow designers set case-type AI options only as part of a blueprint draft; publication follows the blueprint's own lifecycle ([[WF-workflow-versioning]]), and the blueprint validator rejects AI steps the policy does not allow.
- **C7** Case manager on that case only.
- **C8** Presiding neutral (or sole neutral) on that case only, for example to give effect to a procedural order; recorded with the order reference.
- **C9** Case manager may lift only a restriction they set; a restriction set by the presiding neutral can be lifted only by the presiding neutral.
- **C10** Only if the tenant has set `ai.parties.opt_out_mode` to `on_request` or `ask_at_filing`; applies to the party's own submissions in that case.
- **C11** Only if the decision function allows the feature for that user, unit, case type and case, and the user holds the feature's use permission set (`ps.ai.<feature>_user`). Admin roles use only `admin_copilot` and agent test consoles unless they also hold an operational role.
- **C12** Only through a published agent or workflow AI step, with the intersection rule in the policy model.
- **C13** Only the approver role named for the feature in [[AI-human-in-the-loop]], on that case; never a service account or agent.
- **C14** Platform billing or account owner may raise the entitlement ceiling ([[BIL-plans-entitlements-and-usage]]); never lowers a tenant's own choices.
- **C15** Two-person change: platform admin proposes, platform security approves; release through [[PKG-configuration-lifecycle]] at platform scope.
- **C16** Any one of: AI platform lead, regional incident commander, platform security. Audited, tenants notified.
- **C17** Only with the tenant owner's signed written agreement naming the alternative region and provider, approved by platform security and Nomology legal; expiry required.

<!-- section:policy -->
## Policy model

**Decision function.** One package, `@nomology/ai-policy`, exposes a pure, synchronous-after-load decision:

```ts
export type AiDecisionInput = {
  tenantId: string; region: 'in' | 'sg' | 'us';
  unitId?: string; caseTypeKey?: string; caseId?: string;
  principal: { kind: 'user'; userId: string } | { kind: 'ai_agent'; agentId: string; agentVersion: number; invokedBy?: string };
  feature: AiFeatureKey;                         // from the platform feature catalogue
  dataScopes: Array<'case_documents' | 'tribunal_only' | 'deliberations' | 'transcripts' | 'tenant_knowledge' | 'admin_metadata'>;
  partyIdsInInput?: string[];                    // whose submissions are in the input, for opt-out checks
  destination: 'user_only' | 'internal_record' | 'tribunal' | 'party_facing' | 'configuration_draft';
};
export type AiDecision =
  | { allow: true; obligations: AiObligations; policyVersion: string; reasons: string[] }
  | { allow: false; code: AiDenyCode; reason: string; policyVersion: string; source: SettingSource };

export type AiObligations = {
  routeSet: string[];                            // allowed route ids in the tenant's region (zero-retention only)
  redaction: 'none' | 'pseudonymise' | 'redact'; // stricter of feature default and tenant setting
  review: { mode: 'always' | 'below_threshold' | 'sampled'; approverRole: CaseRole | TenantRole; secondReviewer?: boolean };
  label: { required: true; inIssuedDocument: boolean; statementTemplateKey?: string };
  disclosure: 'none' | 'record_only' | 'notify_parties' | 'statement_in_document';
  retention: 'case' | 'short_30d' | 'metadata_only';
  budgetScope: { tenant: true; unitId?: string; userId?: string; agentId?: string };
};
```

**Evaluation order** (first failure wins; every deny has a stable code from [[APP-api-error-catalogue-problem]]):

| Step | Check | Source | Deny code |
|---|---|---|---|
| 1 | Regional kill switch off | Operational flag `ai.killswitch` ([[PKG-feature-flags]]) | `AI_DISABLED_PLATFORM` |
| 2 | Feature released in region and inventory entry approved | Release flag `ai.feature.<key>`; `ai_systems.status` ([[AI-ai-governance-and-impact]]) | `AI_FEATURE_UNAVAILABLE` |
| 3 | Plan includes the feature | Entitlement ([[BIL-plans-entitlements-and-usage]]) | `AI_NOT_ENTITLED` |
| 4 | Tenant AI on and current notice accepted | `ai.policy.enabled`; `tenant_ai_decisions` notice version equals current | `AI_FEATURE_DISABLED` |
| 5 | Feature on at the most specific scope (tenant, unit, case type) | `ai.features.<key>.enabled` resolved with locks | `AI_FEATURE_DISABLED` |
| 6 | Case not restricted for this feature | `case_ai_restrictions` | `AI_CASE_RESTRICTED` |
| 7 | No opted-out party's submissions in the input | `party_ai_preferences` | `AI_PARTY_OPTED_OUT` |
| 8 | Principal may use the feature | Permission check ([[PKG-policy-engine-permission-matrix]]); for agents, intersection rule below | `AI_NOT_PERMITTED` |
| 9 | Data scopes allowed for this feature and principal | Feature manifest; `ai.data.*` settings; document visibility ([[PKG-rbac-abac-case-level-party]]) | `AI_DATA_SCOPE_DENIED` |
| 10 | Destination allowed and review obligation computable | Feature manifest; `ai.review.*` | `AI_DESTINATION_DENIED` |
| 11 | At least one allowed route in region with zero-retention terms | `ai.models.allowed_providers` ∩ `ai_model_routes` where `zero_retention = true` | `AI_REGION_UNAVAILABLE` |

Budget reservation happens after the decision, inside the gateway ([[AI-cost-controls]]).

**Agents and the intersection rule.** An agent's effective right to do anything is the intersection of: (a) the permissions of the human who invoked it, (b) the permission sets granted to its `ai_agent` principal, (c) the tools bound to the published agent version, and (d) this policy. Scheduled or workflow-started agents with no invoking human use (b), (c) and (d) only, and may not use tools that need a human principal. This is the shared-model rule that AI never holds more rights than the narrower of its human and its own principal ([[PKG-non-human-principals]]).

**Platform hard bounds** (locked at `platform`; not settings a tenant can see as editable):

| Bound | Value |
|---|---|
| Training or fine-tuning on tenant data | Never (`ai.data.allow_training` locked `false`) |
| Provider retention of prompts and outputs | Zero-retention routes only for case content (`ai.data.require_zero_retention` locked `true`) |
| Processing region | Tenant home region only; exceptions only per C17 |
| Human approval before output reaches a party, the case record or changes case state | Always ([[AI-human-in-the-loop]]) |
| AI deciding or predicting the outcome, damages or credibility | Prohibited; no feature, agent or step may be configured to do it |
| AI labels on AI output | Always shown; tenants may add statements, not remove labels |
| Deliberation notes as AI input | Only when the presiding neutral enables it for the case ([[APP-neutral-workspace]]) |

**Where policy lives.** Values are settings rows ([[PKG-settings-data-model]]) with kind `ai_policy`, edited as a draft and published through [[PKG-configuration-lifecycle]]. The decision function loads the published snapshot per tenant into process memory, keyed by `policyVersion`, invalidated by the `config.published` event (target: under 5 seconds in a region). Case restrictions and party opt-outs are tenant-owned rows read per request (cached for 30 seconds at most, invalidated on write). Temporal workflows receive the `policyVersion` at start but **re-check the decision at each AI step**, because a tighter policy must apply to running cases (AI settings are "applies to running cases" by design; loosening never reopens a case restriction).

**Neutrals' use of AI and disclosure (assumptions).** Whether neutrals may use AI drafting help, and what they must disclose, is decided by the institution's rules, not by Nomology. The policy offers `ai.neutrals.drafting_assist_allowed` and `ai.disclosure.neutral_use` (`none`, `record_only`, `notify_parties`, `statement_in_document`). Assumption: no statute in India, Singapore or the US currently prescribes a disclosure form for neutrals' AI use in arbitration or ODR; institutions may. To be confirmed by legal and collected per tenant.

**Party opt-out (assumption).** `ai.parties.opt_out_mode` = `not_offered` (default), `on_request`, `ask_at_filing`. When a party opts out, their submissions in that case are excluded from every AI input (retrieval filters chunks by submitting party; features that need the whole record are denied with `AI_PARTY_OPTED_OUT`, and the user is told why). Assumption: an opt-out is a service choice offered by the institution, not a statutory right under the DPDP Act 2023 [R4] or PDPA; whether a party can object to AI processing as a matter of law depends on the lawful basis the tenant relies on. To be confirmed by legal.

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat / abuse case | Mitigation | Residual risk |
|---|---|---|---|---|
| T1 | Elevation | A feature or agent calls the gateway without going through the policy (new code path, script, Temporal activity) | Gateway is the only route to models and calls `decide()` itself; features cannot pass a pre-made decision; lint bans provider SDKs outside the gateway ([[AI-ai-gateway]]) | Low |
| T2 | Elevation | Tenant admin widens AI use without the institution's agreement (for example turns on `drafting_assist` for all neutrals) | Widening changes need maker-checker with `tenant_owner` or a second admin; notice re-acceptance when risk tier T3 is first enabled; tenant owners notified | Low |
| T3 | Elevation | Unit admin turns on a feature the tenant has off | Unit scope may only narrow; resolver rejects a unit value more permissive than the tenant's | Low |
| T4 | Elevation | Agent uses its own principal's rights to act beyond the invoking user | Intersection rule; tool calls re-checked per call; tests with low-privilege invokers | Low |
| T5 | Information disclosure | Case content sent to a provider that keeps or trains on it | Zero-retention locked; route `terms_ref` and `zero_retention` required to activate; sub-processor review ([[SEC-vendor-sub-processor-management]]) | Medium until provider terms confirmed per region |
| T6 | Information disclosure | Opted-out party's documents reach a model through retrieval or an agent tool | Opt-out applied in retrieval filter and in step 7; isolation-style tests for opt-out | Low |
| T7 | Information disclosure | Tribunal-only documents or deliberations reach a secretariat summary | Data scope check plus document visibility at retrieval ([[AI-rag]]) | Low |
| T8 | Tampering | Policy changed directly in the database or through a stale draft | Only the lifecycle publish writes published rows; optimistic versions; audit hash chain ([[PKG-audit-log-schema]]) | Low |
| T9 | Repudiation | Tenant later denies having enabled AI | `tenant_ai_decisions` records notice version, person, step-up method and time; immutable audit | Low |
| T10 | Denial of service | Policy cache unavailable, so every AI call fails or (worse) allows | Fail closed: no loaded policy means deny with `AI_POLICY_UNAVAILABLE`; non-AI paths continue | Low |
| T11 | Spoofing | Copilot or agent drafts an AI policy change and a hurried admin publishes it | Drafts carry an "AI-proposed" marker, a readable diff and explanation; publish requires a human with step-up; maker-checker counts the invoking human as author ([[APP-admin-copilot]]) | Medium (human error) |
| T12 | Elevation | Out-of-region exception used as a general workaround during an outage | Exceptions are per tenant, written, expiring, approved by security and legal; never automatic | Low |
| T13 | Information disclosure | AI usage dashboards reveal case content | Usage records carry no prompt or output text ([[OBS-ai-usage]]) | Low |

<!-- section:failure -->
## Denial behaviour

| Situation | What the user sees | What is logged |
|---|---|---|
| Feature off for tenant, unit or case type | AI controls hidden; where a user expects them, a short note "AI assistance is turned off for your organisation" with the admin contact ([[AI-ai-generated-text-labelling-and#errors]]) | Deny counted per code; no per-call audit for UI hiding |
| Case restricted | "AI is not used on this case." Plus who set it (role, not name, for non-staff) | `ai.policy.denied` with `AI_CASE_RESTRICTED` |
| Party opted out | "Some documents in this case cannot be used with AI because a party has asked for this." Never names the party to other parties | `ai.policy.denied` with `AI_PARTY_OPTED_OUT` and party ID (internal only) |
| Not permitted | Same text as feature off, so the response does not reveal which features exist for others | `ai.policy.denied` with `AI_NOT_PERMITTED` |
| Policy cannot be loaded | "AI assistance is not available right now. Nothing in your case has changed." | Error event and alert; deny |

Denies never return partial output and never reveal another tenant's, unit's or case's configuration. All denies from the gateway are written to `ai_policy_decisions`; allows are sampled (proposed 1 percent, plus all allows for T3 features) because the full request is already logged in `ai_requests`.

<!-- section:requirements -->
## Security requirements

ASVS mapping is at chapter level for version 5.0 [R3]; item IDs to be added during security review.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| AIPOL-FR-1 | Every AI call, agent tool call and workflow AI step is checked by `ai-policy.decide()` before any data leaves the platform | V8 Authorization |
| AIPOL-FR-2 | The decision follows the evaluation order in the policy model; the first failing step determines the deny code | V8 |
| AIPOL-FR-3 | No loaded policy, unreadable restriction table or unknown feature key results in deny (fail closed) | V8, V16 |
| AIPOL-FR-4 | Tenant AI choices are settings in the `ai` domain ([[PKG-settings-ai]]) and change only through the configuration lifecycle; there is no direct write API | V13 Configuration |
| AIPOL-FR-5 | Lower scopes (unit, case type, case) can only narrow AI use; the resolver rejects a more permissive value with `SETTING_WIDENS_PARENT` | V8 |
| AIPOL-FR-6 | Changes that widen AI use (enable a feature, add a data scope, relax review, lengthen retention, add a provider) need maker-checker ([[PKG-separation-of-duties]]); first enablement of a T3 feature needs the tenant owner | V8 |
| AIPOL-FR-7 | Narrowing changes and the tenant kill switch take effect without approval, within 5 seconds in the region, including for running workflows | V13 |
| AIPOL-FR-8 | The tenant must accept the current AI notice version before any feature can be enabled; a new notice version with material change suspends new enablements until re-accepted (existing features keep running for a proposed 30-day grace period) | — |
| AIPOL-FR-9 | Case restrictions and party opt-outs are applied in retrieval filters as well as in the decision, so that indirect paths (agents, workflow steps, search) honour them | V8 |
| AIPOL-FR-10 | Only zero-retention, no-training routes in the tenant's home region can appear in `routeSet` for case content | V14 Data Protection |
| AIPOL-FR-11 | Every policy publish, notice acceptance, restriction, opt-out and exception is an audit event (`admin.ai.policy_published`, `admin.ai.notice_accepted`, `ai.case.restricted`, `ai.party.opted_out`, `platform.ai.exception_approved`) with old and new values | V16 Logging |
| AIPOL-FR-12 | A published AI transparency statement, generated from the policy, is available to parties and counsel at `/ai-use` on the tenant's public host ([[APP-public-and-sign-in-surfaces]]) and in the case portal | — |
| AIPOL-FR-13 | The admin console shows, for any user and case, the effective AI decision and the setting that caused it (shared with [[PKG-access-explainer]]) | V8 |
| AIPOL-FR-14 | The admin copilot and agents may draft AI policy changes but cannot approve or publish them | V8 |
| AIPOL-FR-15 | Policy snapshots are versioned; every `ai_requests` row records `policy_version` so the policy that applied to any output can be reproduced | V16 |

<!-- section:verification -->
## Verification

| Test | Type | Threshold / when |
|---|---|---|
| Decision table tests: one test per row of the evaluation order, for each deny code, plus allow paths per feature tier | Unit, generated from the feature catalogue | 100 percent, every CI run |
| Matrix tests: each cell of the permission matrix as an allowed or denied API call against `/admin/v1/ai/*` and tRPC | Integration (two tenants) | 100 percent, blocking |
| Narrowing-only property test: random unit and case-type values never produce a decision more permissive than the tenant value | Property-based | 10,000 cases per run |
| Fail-closed tests: policy cache empty, restriction table unavailable, unknown feature key | Fault injection | 100 percent deny |
| Opt-out propagation: opted-out party's documents absent from retrieval, agents' tool results and workflow steps | Integration with [[AI-rag]] | 100 percent |
| Running-workflow tightening: switching a feature off stops the next AI step of a running case workflow | Temporal test environment | Pass |
| Gateway bypass: code search and egress test show no provider calls outside the gateway | CI lint and synthetic | Zero findings |
| Pen test scope: policy tampering through admin API, widening at unit scope, agent privilege escalation, copilot-assisted policy change | External pen test, annually and before first T3 enablement | No high findings open |

<!-- section:questions -->
## Open questions

- [x] Moving tenant AI enablement from flags to settings is accepted (decision D7); [[PKG-feature-flags]] (FLAG-R-7) keeps only platform availability and `ai.killswitch`.
- [ ] Legal: is offering a party AI opt-out advisable, and does any law in our regions give parties a right to object to AI processing of their submissions? (owner: Nomology legal)
- [ ] Legal: EU AI Act classification of `drafting_assist` and `bundle_summary` for tenants with EU parties; whether Article 6(3) applies to assistive, human-approved features [R2]. (owner: legal)
- [ ] Which institutions require disclosure of neutrals' AI use, and in what form? Collect per tenant at onboarding; do not assume. (owner: product with tenants)
- [ ] Grace period after a material AI notice change (proposed 30 days). (owner: legal)
- [ ] Should unit admins be allowed to hold `ai.budget:update` for their unit only? Proposed yes. (owner: product)
- [ ] Sampling rate for logged allows (proposed 1 percent plus all T3). (owner: security)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Policy rows, decision records, restrictions and opt-outs are tenant-owned tables under forced RLS; the decision function takes `tenantId` from the request context, never from the caller's payload. The route allow-list is filtered by the tenant's home region. Independent layers: RLS, the gateway's own context check, retrieval filters and the cross-tenant test suite ([[TST-multi-tenant-isolation-tests]]).

<!-- check:enforcement -->
### Enforcement points and bypass paths

One decision function is called by the gateway on every model call, by the agent runtime on every tool call, by the blueprint validator at publish and by workflow AI steps at run time. UI hiding is cosmetic only. Retrieval applies restrictions and opt-outs as filters, so indirect paths cannot bypass them. Provider SDKs are banned outside the gateway and egress is limited to gateway tasks.

<!-- check:lifecycle -->
### Grant lifecycle and privileged access

Settings change only through draft, review, approve, publish ([[PKG-configuration-lifecycle]]); widening changes need maker-checker and T3 first enablement needs the tenant owner; narrowing and the kill switch apply at once. Notice acceptance is re-required on material change. Out-of-region exceptions expire and need security and legal approval. Platform bound changes need two Nomology approvers.

<!-- check:resilience -->
### Failure modes and secrets

Fails closed when the policy snapshot, restriction table or feature catalogue cannot be read; non-AI paths continue, because no case step depends on AI. The regional kill switch stops all AI within 5 seconds. Compromise of an AI admin account is limited by maker-checker on widening changes and step-up on publish.

<!-- check:residency -->
### Data residency

Policy data, decision logs, restrictions and opt-outs are stored in the tenant's regional Postgres. The decision only ever returns routes in the tenant's home region. The global part is the platform feature catalogue, which holds no tenant data.

<!-- check:audit -->
### Audit trail

Every publish, notice acceptance, restriction, opt-out, exception and deny is recorded with actor, old and new value, policy version and reason in [[PKG-audit-trail]]; `ai_requests.policy_version` ties each output to the policy that allowed it; history can be replayed to reproduce the effective decision for any case and date.

<!-- check:observability -->
### Detection and alerting

Metrics: denies per code, tenant and feature; policy load latency and failures; time from publish to enforcement; opt-out counts. Alerts: any `AI_POLICY_UNAVAILABLE` burst (page regional on-call), deny rate for a tenant jumping above three times its 7-day baseline (AI platform lead), any route without zero-retention appearing in a route set (security, page). Feeds [[OBS-ai-usage]] and [[OBS-security-events]].

<!-- check:compliance -->
### Framework and legal mapping

ISO/IEC 42001 [R1]: AI policy (5.2), roles (5.3), information for interested parties (Annex A.8) through the transparency statement; EU AI Act deployer duties and transparency where tenants have EU parties [R2]; DPDP Act duties of a data fiduciary supported for tenants, with Nomology as processor [R4]; Singapore Model AI Governance Framework for Generative AI dimensions of accountability, data and content provenance [R5]; India AI Governance Guidelines (non-binding) [R6]. Evidence: published policy versions, notice acceptances, deny logs, test reports.

<!-- check:testing -->
### Verification and testing

Each matrix cell and each evaluation-order step has an automated test; property tests prove narrowing-only resolution; fault injection proves fail closed; opt-out propagation is tested end to end; annual pen test covers policy tampering and agent escalation.

<!-- citations -->
## Citations

```json
[
  {
    "body": "ISO/IEC",
    "excerpt": "Requirements for establishing, implementing, maintaining and continually improving an AI management system, including AI risk assessment, AI risk treatment and AI system impact assessment.",
    "id": "R1",
    "ident": "ISO/IEC 42001",
    "kind": "standard",
    "title": "Information technology - Artificial intelligence - Management system",
    "url": "https://www.iso.org/standard/42001",
    "version": "2023"
  },
  {
    "excerpt": "Annex III lists high-risk uses, including AI intended to assist a judicial authority in researching and interpreting facts and the law and applying the law to facts, or used in a similar way in alternative dispute resolution. Article 6(3) excludes Annex III systems that perform narrow procedural or preparatory tasks and do not materially influence the outcome of decision making; Article 26 sets deployer duties (human oversight, log keeping); Article 50 sets transparency duties.",
    "id": "R2",
    "issuer": "European Parliament and Council",
    "jurisdiction": "EU",
    "kind": "regulation",
    "ref": "Regulation (EU) 2024/1689",
    "status": "in force, phased application",
    "title": "Artificial Intelligence Act",
    "url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
  },
  {
    "body": "OWASP Foundation",
    "excerpt": "Application Security Verification Standard; version 5.0 chapters include V8 Authorization, V13 Configuration, V14 Data Protection and V16 Security Logging and Error Handling.",
    "id": "R3",
    "ident": "OWASP ASVS",
    "kind": "standard",
    "title": "OWASP Application Security Verification Standard",
    "url": "https://owasp.org/www-project-application-security-verification-standard",
    "version": "5.0"
  },
  {
    "excerpt": "Sections 5-6 (notice and consent), 7 (legitimate uses), 8 (obligations of data fiduciary, including reasonable security safeguards and engaging processors under contract), 11-14 (rights of data principal).",
    "id": "R4",
    "issuer": "Government of India (MeitY)",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 22 of 2023",
    "title": "Digital Personal Data Protection Act, 2023",
    "url": "https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf"
  },
  {
    "excerpt": "Nine dimensions for trusted generative AI: accountability, data, trusted development and deployment, incident reporting, testing and assurance, security, content provenance, safety and alignment R&D, and AI for public good. Released 30 May 2024.",
    "id": "R5",
    "issuer": "IMDA and AI Verify Foundation (Singapore)",
    "jurisdiction": "Singapore",
    "kind": "regulation",
    "ref": "Model AI Governance Framework for Generative AI",
    "status": "voluntary framework",
    "title": "Model AI Governance Framework for Generative AI",
    "url": "https://aiverifyfoundation.sg/resources/mgf-gen-ai/"
  },
  {
    "excerpt": "Non-binding national guidance issued by MeitY under the IndiaAI Mission (November 2025) setting out principles for safe and trusted AI, including accountability, understandability by design and safety, and recommending institutional and organisational measures.",
    "id": "R6",
    "issuer": "Ministry of Electronics and Information Technology, Government of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "India AI Governance Guidelines",
    "status": "guidance, non-binding",
    "title": "India AI Governance Guidelines: Enabling Safe and Trusted AI Innovation",
    "url": "https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc2025115685601.pdf"
  },
  {
    "excerpt": "Trust layer features: grounding in customer data, data masking, toxicity detection, audit trail and feedback, and zero data retention agreements with third-party model providers.",
    "id": "R7",
    "kind": "vendor",
    "title": "Agentforce Developer Guide: Trust Layer",
    "url": "https://developer.salesforce.com/docs/ai/agentforce/guide/trust.html",
    "vendor": "Salesforce"
  },
  {
    "excerpt": "Admins govern agent actions, connectors, knowledge sources, HTTP requests, channel publication and authentication through data policies; can turn off publishing of agents that use generative AI for a tenant; makers see a security warning and risk assessment before publishing; maker activity is audited.",
    "id": "R8",
    "kind": "vendor",
    "title": "Microsoft Copilot Studio: Security and governance",
    "url": "https://learn.microsoft.com/en-us/microsoft-copilot-studio/security-and-governance",
    "vendor": "Microsoft"
  }
]
```

<!-- end -->
