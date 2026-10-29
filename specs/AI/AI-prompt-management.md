---
id: "AI-prompt-management"
title: "Prompt management"
parent: "AI"
order: 2
type: "capability"
template: "ai"
status: "draft"
owner: null
indicative: false
summary: "Versioned platform prompts (features, agent base prompts, workflow step prompts, copilot) with tenant slots, bounded agent instructions and structured step variables published as configuration"
links: []
rev: 3
syncHash: "707df8a2a5c111b1"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 8.2 Prompt management

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Versioned platform prompts (features, agent base prompts, workflow step prompts, copilot) with tenant slots, bounded agent instructions and structured step variables published as configuration

<!-- section:purpose -->
## Intended use

Prompt management stores, versions, tests and releases the prompts that AI features, agent base prompts, workflow step prompts and the admin copilot use, and lets tenants adjust a small set of safe, structured inputs without editing the platform's instructions: **slots** (terminology, institution rule references), **agent instructions** inside a bounded slot ([[AI-agent-configuration]]), and **step variables** such as label sets and field descriptions ([[WF-ai-steps-and-agents]]).

Who uses it: platform AI engineers (author prompts), the AI review group (approve releases), tenant admins (set slot values in the tenant admin console at `/admin/ai/prompts`, [[APP-tenant-admin-console]]), agent builders (write agent instructions), workflow designers (label sets and field descriptions), and the gateway (resolves `prompt_key@version` at call time, [[AI-ai-gateway]]).

**Prompt namespaces**

| Namespace | Examples | Tenant input |
|---|---|---|
| Feature prompts | `case-summary.secretariat`, `bundle-summary.tribunal`, `drafting-assist.order` | Slots only |
| Agent base prompts | `agent.base.secretariat`, `agent.base.neutral`, `agent.base.workflow`, `agent.base.admin` | Tenant instructions slot (max 4,000 characters) |
| Workflow step prompts | `wf.classify.document`, `wf.extract.fields`, `wf.summarise.filing`, `wf.draft.template_fill` | Structured variables (labels, field definitions, template slot descriptions) |
| Admin copilot | `copilot.admin`, `copilot.classify_request` | None at launch |
| Guardrail prompts | `guard.neutrality`, `guard.entailment` | None |

**Functional requirements**

| ID | Requirement |
|---|---|
| PROMPT-FR-1 | Prompts live in the repository under `packages/ai-prompts/prompts/<namespace>/<name>.md` with front matter (key, version, capability, output schema, owner, eval suite) |
| PROMPT-FR-2 | A published version is immutable; any change creates a new version |
| PROMPT-FR-3 | CI publishes merged prompts to the `ai_prompt_versions` table in every region; publishing requires a passing eval run for that version |
| PROMPT-FR-4 | Each feature has a platform default pin; a tenant may be pinned to an older approved version for a limited period (for example during their own acceptance testing) |
| PROMPT-FR-5 | Tenants can set values only for declared slots; slot values are validated (length, allowed characters, no instructions) and versioned |
| PROMPT-FR-6 | Every `ai_requests` row records `prompt_key`, `prompt_version` and the tenant slot version (or agent version, or AI step definition version) used |
| PROMPT-FR-7 | Rollout of a new version can be staged by feature flag percentage or tenant list ([[PKG-feature-flags]]) |
| PROMPT-FR-8 | Tenant slot values are configuration: they are edited as drafts, published through [[PKG-configuration-lifecycle]] and travel in configuration packages ([[PKG-configuration-packages]]) |
| PROMPT-FR-9 | Agent instructions and workflow step variables pass the same validator as slots; instructions are always placed in the lower-priority tenant block of the base prompt |
| PROMPT-FR-10 | A base prompt release re-runs the evaluation sets of every published agent and AI step definition that uses it before the pin moves |

<!-- section:outofscope -->
## Out-of-scope uses

- **Free-text prompts typed by end users that replace system instructions.** Users can type a question or instruction into a drafting panel or agent, but that text is a variable inside a fixed template and is treated as untrusted ([[AI-guardrails]]).
- **Tenant-authored full prompts.** Not supported. Tenants shape behaviour through slots, bounded agent instructions and structured step variables; the platform constraints section of every prompt (neutrality, no outcome prediction, citation rules) cannot be edited or removed by tenants. A tenant wanting different behaviour beyond that asks for a new slot or a new prompt version, reviewed by us.
- **Prompts stored only in the database without code review.** Prevented because the registry accepts platform prompt versions only from the CI publish job. Tenant inputs are stored as tenant configuration, never as prompt versions.

<!-- section:models -->
## Models and providers

Prompts declare a capability (`chat.large`, `chat.small`), not a model. The model is chosen by the gateway route table ([[AI-ai-gateway]]). A prompt version's eval run records which model versions it was tested against; a route change to a new model version triggers re-running evals for every active prompt on that capability.

<!-- section:context -->
## Inputs and context sources

Each prompt declares its variables and their sources in front matter, which doubles as the feature's field allow-list:

```yaml
---
key: case-summary.secretariat
version: 7
capability: chat.large
owner: ai-platform
evalSuite: case-summary-v3
output: schemas/case-summary.ts      # Zod schema
variables:
  caseRef:        { source: case.reference, pii: false }
  procedureType:  { source: case.procedureType, pii: false }
  passages:       { source: rag.retrieve, scope: case, maxTokens: 24000 }
  userQuestion:   { source: user, untrusted: true, maxChars: 2000 }
slots:
  terminology:    { maxChars: 1500, description: "Institution terms to prefer (glossary keys)" }
  rulesReference: { maxChars: 300,  description: "Name and version of the applicable institutional rules" }
---
```

No variable may pull data outside the case in context. Party names are included only when the feature's impact assessment allows it; otherwise pseudonymised by guardrails.

<!-- section:prompts -->
## Prompt design and versioning

**Structure.** Every prompt has fixed sections: role and task; constraints (neutral tone, no outcome predictions, no legal advice, answer only from supplied passages, cite passage IDs); the tenant block (slots, agent instructions or step variables, delimited and marked lower priority); the untrusted-content block with clear delimiters; output format (schema).

**Storage.**

| Table | Level | Purpose |
|---|---|---|
| `ai_prompt_versions` | Platform-level (no `tenant_id`) | `key, version, body, front_matter, sha256, eval_run_id, published_at, status (active/deprecated/withdrawn)` |
| `ai_prompt_pins` | Platform-level | Default version per feature and region |
| `tenant_ai_prompt_settings` | Tenant-owned, forced RLS | `tenant_id, prompt_key, slot values, version, pinned_prompt_version (optional, with expiry), change_set_id, updated_by` |
| `ai_agent_versions.instructions` | Tenant-owned ([[AI-agent-configuration]]) | Agent instructions with hash, validated by the same validator |
| AI step definitions | Tenant-owned ([[WF-ai-steps-and-agents]]) | Label sets, field descriptions and template slot descriptions |

**Release flow.** Pull request with prompt change and eval results, review by a second AI engineer and the feature owner, merge, CI runs the eval suite against the pinned route models (plus affected agents' and step definitions' evaluation sets for base and step prompts), CI publishes to every region, flag-based rollout, then default pin moves. Withdrawal sets `status = withdrawn` and moves pins back; running Temporal workflows keep the version captured at start, per [[WF-separation-of-concerns-temporal]].

<!-- section:guardrails -->
## Guardrails

- Slot values pass a validator: length limits, no markup, no phrases that look like instructions ("ignore", "system", "you are") and only glossary keys for the terminology slot ([[I18N-platform-glossary-and]]).
- Templates mark untrusted variables; the renderer wraps them in delimiters and escapes delimiter sequences.
- System prompts are not secret but are not shown to end users; prompts must not contain credentials or tenant data (OWASP LLM07 System Prompt Leakage [R1]).
- A CI lint checks each prompt for required sections (neutrality and no-advice constraints, citation instruction for RAG prompts).

<!-- section:oversight -->
## Human oversight

- Prompt releases are approved by a second AI engineer plus the feature owner; prompts for features in the highest risk tier, and agent base prompts, also need the AI governance lead ([[AI-ai-governance-and-impact]]).
- Tenant slot changes are made by `ai_admin` or `content_admin` (terminology slot) through the configuration lifecycle: draft, preview against sample cases in the sandbox, approval where the tenant requires it, publish, with rollback to a previous version. They are logged in the audit trail.
- Agent instructions are reviewed by the agent's approver as part of agent publishing ([[AI-agent-configuration]]); step variables by the blueprint's approver ([[WF-workflow-versioning]]).

<!-- section:evaluation -->
## Evaluation

| Gate | Threshold | When |
|---|---|---|
| Feature eval suite for the new prompt version | At or above the feature's thresholds and no metric worse than the current pinned version by more than a proposed 2 percentage points | Every prompt change (blocking) |
| Prompt lint (required sections, variable declarations) | Pass | Every change |
| Slot injection test set (malicious slot values) | 100 percent rejected | CI |
| Re-run on model route change | All active prompts on that capability pass | Before route activation |

Suites and datasets are defined in [[TST-evals-and-ai-testing]].

<!-- section:failure -->
## Failure modes and fallback

| Failure | Handling |
|---|---|
| Prompt version missing in a region | Publish job is all-regions-or-nothing; gateway returns `AI_PROMPT_UNAVAILABLE` and alerts |
| Bad prompt released | Withdraw version; pins revert automatically; affected outputs found by `prompt_version` and flagged for re-review |
| Tenant slot causes poor output | Tenant can roll back; AI team can reset slots to defaults |

<!-- section:logging -->
## Logging and audit

Every request records `prompt_key`, `prompt_version`, `prompt_sha256` and tenant slot version. Publishing, pin changes and slot edits are audit events (`ai.prompt.published`, `ai.prompt.pin_changed`, `ai.prompt.slots_updated`). Prompt versions are kept indefinitely (they contain no personal data) so any past output can be explained.

<!-- section:questions -->
## Open questions

- [ ] Which slots do tenants actually need at launch (terminology, rules reference, tone)? Proposal: terminology and rules reference only.
- [ ] Should a tenant's acceptance testing be able to pin an older prompt version, and for how long at most (proposed 30 days)?
- [ ] Do institutions want to review and approve prompts used for their neutrals' drafting assistance before rollout?
- [ ] Language of prompts for non-English output (for example Hindi summaries): one prompt per language or a language variable?
- [ ] When a base prompt release makes a tenant agent fail its evaluation, how long does the tenant keep the old base version (proposed 14 days, aligned with [[AI-agent-configuration#models]])?

<!-- checks -->
## Template checks

<!-- check:risk -->
### Risk classification and impact

Prompt management inherits the risk of each feature; it is the main control for keeping feature behaviour stable and reviewable. Higher-tier features need the AI governance lead's approval of prompt releases.

<!-- check:security -->
### AI security and tenant isolation

User text, documents, tenant knowledge and tool results enter prompts only as delimited untrusted variables; tenant slots, agent instructions and step variables are validated against an injection test set (100 percent rejection required) and always sit in a lower-priority tenant block; system prompts carry no secrets or tenant data, addressing OWASP LLM01 and LLM07 [R1].

<!-- check:oversight -->
### Human oversight

Two-person review for prompt releases (AI engineer plus feature owner), AI governance lead for the highest tier and for agent base prompts; tenant slot edits go through the configuration lifecycle, are audited, previewable in the sandbox and reversible; agent instructions and step variables are approved with the agent or blueprint.

<!-- check:evals -->
### Evaluation

Every prompt change runs the feature's eval suite and is blocked if it falls below thresholds or regresses more than a proposed 2 points against the pinned version; results are stored with `prompt_key@version` and model version; model route changes re-run all active prompts.

<!-- check:audit -->
### Audit and traceability

Requests record prompt key, version, hash and the tenant slot, agent or step definition version; prompt versions are immutable and retained indefinitely; publishing, pinning and slot edits are audit events (`ai.prompt.published`, `ai.prompt.pin_changed`, `admin.ai.prompt_slots_published`).

<!-- citations -->
## Citations

```json
[
  {
    "body": "OWASP Foundation",
    "excerpt": "Risk list including prompt injection, sensitive information disclosure, improper output handling, excessive agency, system prompt leakage, vector and embedding weaknesses, misinformation and unbounded consumption.",
    "id": "R1",
    "ident": "OWASP Top 10 for LLM Applications",
    "kind": "standard",
    "title": "OWASP Top 10 for Large Language Model Applications",
    "url": "https://genai.owasp.org/llm-top-10/",
    "version": "2025"
  }
]
```

<!-- end -->
