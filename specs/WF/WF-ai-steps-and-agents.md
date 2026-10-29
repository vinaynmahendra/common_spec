---
id: "WF-ai-steps-and-agents"
title: "AI steps and agents in workflows"
parent: "WF"
order: 8
type: "capability"
template: "ai"
status: "draft"
owner: null
indicative: false
summary: "Summarise, classify, extract and draft steps and bounded agent tasks in case-type blueprints, with calibrated confidence thresholds, human review tasks, mandatory fallbacks, provenance rules that keep unreviewed AI out of anything with legal effect, and cost limits"
links: []
rev: 1
syncHash: "6e0b3c59567c00a7"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 7.7 AI steps and agents in workflows

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Summarise, classify, extract and draft steps and bounded agent tasks in case-type blueprints, with calibrated confidence thresholds, human review tasks, mandatory fallbacks, provenance rules that keep unreviewed AI out of anything with legal effect, and cost limits

<!-- section:purpose -->
## Intended use

This node specifies how a **workflow designer** adds AI to a case-type blueprint ([[WF-process-definition-model]]) without code: summarising a filing for the case manager, classifying incoming documents into the institution's filing categories, extracting dates and amounts into custom fields, drafting a routine acknowledgement for a person to send, or handing a bounded task to a published tenant agent. It also specifies how those steps run inside the generic Temporal interpreter workflow ([[WF-separation-of-concerns-temporal]]) and how they stay safe in legal processes.

**AI step definitions.** In the blueprint model ([[WF-process-definition-model]]) an AI step is a node of type `ai_step` that references an **AI step definition** by key and pinned version (component kind `ai_step` in `wf.blueprint_component`). The definition is a tenant configuration artefact owned by this node, versioned through [[PKG-configuration-lifecycle]] and reusable across blueprints and by automation rules (`request_ai_suggestion`, [[WF-automation-rules]]), where its output is always a suggestion for human review.

```ts
type AiStepKind = 'summarise' | 'classify' | 'extract' | 'draft' | 'agent_task';

type AiStepDefinition = {
  key: string; version: number; kind: AiStepKind;
  feature: 'case_summary' | 'bundle_summary' | 'document_classification' | 'metadata_extraction'
         | 'secretariat_drafting' | 'custom_agents';
  prompt?: { key: string };                                // platform step prompt, e.g. 'wf.classify.document'; version pinned on publish
  labelSet?: { key: string };                              // classify: tenant-defined label set with a declared purpose
  extract?: { customFieldGroup: string };                  // extract: target fields from PKG-metadata-management-entity
  draft?: { templateKey: string };                         // draft: document or notification template with AI fill slots
  agent?: { key: string; goal: string; tools?: string[] }; // agent_task: published tenant agent, goal templated over facts, subset of its read/propose tools
  confidence?: { autoAcceptAt: number };                   // classify and extract only; calibrated score 0..1
  review: { mode: 'always' | 'below_threshold'; reviewerRole: Role; samplePercent?: number; due?: DeadlineExpr };
  fallback: { onLowConfidence?: 'human_task'; onUnavailable: 'human_task' | 'skip' | 'default'; default?: Expr };
  limits: { maxCallsPerCase: number; maxTokensPerRun: number; timeout: Duration; maxSteps?: number; maxToolCalls?: number };
};

// Blueprint node (shape owned by WF-process-definition-model; shown for the bindings this node relies on)
type AiStepNode = {
  id: string; type: 'ai_step';
  ref: { key: string; version: number };                   // AI step definition, pinned at blueprint publish
  inputs: { documents?: Expr; facts?: Record<string, Expr> };
  output: string;                                          // fact name; usable downstream only after acceptance
  next?: string;
};
```

**Decisions these steps support:** where work goes next (routing a document to the right queue), what a person reviews first, and drafts a person finishes. **Not supported:** anything about the merits or the outcome of a dispute.

**Functional requirements**

| ID | Requirement |
|---|---|
| WFAI-FR-1 | AI steps are available in the authoring studio ([[WF-workflow-authoring-studio]]) only when `ai.features.workflow_ai_steps.enabled` is on for the tenant and case type and the designer holds `workflow.ai_step:configure` |
| WFAI-FR-2 | On blueprint publish, the validator calls the AI policy ([[AI-tenant-ai-policy]]) for every AI step for the tenant and case type, and rejects steps the policy does not allow |
| WFAI-FR-3 | Every AI step must declare a fallback; a step with no path when AI is unavailable cannot be published |
| WFAI-FR-4 | An AI step's output becomes a usable fact only in state `approved`, `approved_with_edits` or `accepted_by_policy` ([[AI-human-in-the-loop]]) |
| WFAI-FR-5 | Facts produced by an AI step carry provenance (`source = ai`, step ID, `ai_output` ID, acceptance state); the validator rejects any binding of an AI fact that was not human-approved into a decision table tagged `legal_effect`, a `transition` step, a deadline expression, a fee computation or a party-facing notice |
| WFAI-FR-6 | Auto-acceptance (`below_threshold`) is allowed only for `classify` and `extract`, only for internal destinations, only when a calibration run exists for the label set or field group, only at or above the platform floor `ai.workflow_steps.min_auto_accept_threshold`, only when the tenant has turned on `ai.workflow_steps.allow_auto_accept` (off by default), and never for outputs that affect the merits or parties' rights (decision D8, flagged for CTO decision) |
| WFAI-FR-7 | At run time, the interpreter re-checks the AI policy before each AI step; a policy deny takes the step's fallback, never fails the case workflow |
| WFAI-FR-8 | AI steps run as the Activity `ai.runStep` (and `ai.runAgentTask`) on task queue `ai-pipelines`, idempotent on `{workflowId}:{stepId}:{inputHash}` |
| WFAI-FR-9 | Prompt, model route policy, label set, field group, template and agent versions are pinned at blueprint publish and recorded on every `ai_outputs` row |
| WFAI-FR-10 | Label sets must declare a purpose from a closed list (`document_type`, `filing_category`, `language`, `routing_queue`, `completeness_hint`); labels that express merit, credibility or likely outcome are rejected by the validator and by a label-text classifier |

<!-- section:outofscope -->
## Out-of-scope uses

| Not allowed | Prevention |
|---|---|
| AI deciding anything with legal effect: admissibility, dismissal, deadlines, fees, appointment of neutrals, award content | WFAI-FR-5 provenance check at publish; decision tables tagged `legal_effect` refuse unreviewed AI facts at run time too |
| AI steps that assess merits, credibility or predict outcomes | No such step kind; label-set purpose list (WFAI-FR-10); neutrality filter on outputs ([[AI-guardrails]]) |
| Sending AI drafts to parties automatically | `draft` kind is always `review.mode = always`; sending is a separate human step |
| Auto-accepted completeness hints producing a deficiency notice to a party | `completeness_hint` outputs can route work to a person but cannot trigger party-facing notices without approval |
| Free-form prompts written by designers | Steps use platform step prompts; designers configure inputs, labels, fields and templates only |
| Autonomous agents running unsupervised loops in a case | `agent_task` has step and tool limits, read and propose tools only, and its output is always reviewed |
| Cross-case inputs | Inputs are expressions over the current case's facts and documents only |

<!-- section:models -->
## Models and providers

Steps ask for a capability through the gateway ([[AI-ai-gateway]]): `chat.small` for `classify` and `extract`, `chat.large` for `summarise`, `draft` and `agent_task`. Routes are in-region, zero-retention and filtered by the tenant's allowed providers. Because the blueprint pins the step prompt version, a model route change triggers re-evaluation of every published blueprint's AI steps (platform suite plus the tenant's calibration set); if a step's measured precision at its threshold drops below the threshold, the step is switched to `review.mode = always` automatically and the workflow designer is notified (auto-accept is never kept on a degraded model).

**Confidence.** Model self-reported confidence is not trusted on its own. The step's score is a **calibrated** value: for routes that expose token probabilities, label probability is used; otherwise a self-consistency score over three samples (proposed) is used. A calibration run on labelled examples maps raw scores to observed precision, so `autoAcceptAt = 0.9` means "at this threshold, at least 90 percent of auto-accepted outputs were correct in calibration". The studio shows the precision and the share of items that would be auto-accepted at the chosen threshold.

<!-- section:context -->
## Inputs and context sources

| Step kind | Typical inputs | Minimisation |
|---|---|---|
| `summarise` | One filing or a document set chosen by expression (for example `facts.latestFiling.documents`) | Only the selected documents; pseudonymised identifiers |
| `classify` | First pages or OCR text of each new document, file name, filing form fields | Only the first N pages (proposed 5) unless configured; redaction per policy |
| `extract` | Selected document pages; the target field definitions | Only fields in the group; values validated against field types |
| `draft` | Case facts named in the template's AI slots, plus selected documents | Only slot inputs |
| `agent_task` | The goal text and what the agent's tools return | Tools trimmed to declared outputs |

Policy filters apply automatically: party opt-outs remove that party's submissions from inputs, a case AI restriction takes the fallback, and tribunal-only documents are never inputs for steps whose reviewer is not a tribunal member ([[AI-tenant-ai-policy#policy]]).

<!-- section:prompts -->
## Prompt design and versioning

Step prompts are platform prompts in [[AI-prompt-management]] under the `wf.` namespace: `wf.summarise.filing`, `wf.summarise.document_set`, `wf.classify.document`, `wf.extract.fields`, `wf.draft.template_fill`, `agent.base.workflow`. Tenant configuration enters as structured variables, not instructions: label names and descriptions (max 50 labels, 200 characters each), field names, types and descriptions, template slot descriptions. These variables pass the same slot validator as other tenant slots (no instruction-like text). The prompt version is pinned when the blueprint is published, so running cases keep consistent behaviour; a newer prompt reaches running cases only through a blueprint migration ([[WF-workflow-versioning]]).

<!-- section:guardrails -->
## Guardrails

- Input guardrails as for every AI call: size limits, redaction, untrusted-content delimiters ([[AI-guardrails]]).
- Output guardrails: schema validation against the label set or field types; values outside the label set are rejected; extracted dates and amounts must also appear in the cited source text (string and normalised-value match), otherwise the item is not auto-accepted.
- Provenance enforcement (WFAI-FR-5) at publish and again at run time.
- **Loop and spend limits:** `limits.maxCallsPerCase` per step (default 20), the tenant cap `ai.workflow_steps.max_calls_per_case` (default 50), and the existing interceptor cap of 200 AI calls per workflow run ([[AI-cost-controls]]).
- **Timeouts:** default 2 minutes for `classify` and `extract`, 10 minutes for `summarise` and `draft`, with heartbeats for long inputs ([[WF-long-running-pipelines]]).

<!-- section:oversight -->
## Human oversight

| Review mode | Allowed for | What happens |
|---|---|---|
| `always` | All kinds; mandatory for `summarise`, `draft`, `agent_task` | A human task of type `ai_review` is created for `reviewerRole` ([[WF-human-tasks]]) with the output, cited sources, flags and the effect of approval. The workflow waits on signal `aiOutputReviewed` or the task's due date |
| `below_threshold` | `classify`, `extract` with calibration and internal destination | Items at or above `autoAcceptAt` move to `accepted_by_policy` and are labelled "AI-classified" wherever shown; items below go to an `ai_review` task; a sample (`samplePercent`, default 5, minimum 2) of auto-accepted items is sent to after-the-fact review |

**After-the-fact review** finds errors in auto-accepted items. A reviewer who corrects one updates the fact; downstream routing that already happened is re-evaluated by the interpreter where the step is still open, and the error is counted against the step's measured precision. If measured precision over the last 200 sampled items falls below `autoAcceptAt`, the step switches to `always` automatically.

**Reviewer role** must be a role that may see the inputs (for example a case manager for secretariat steps; a tribunal secretary for tribunal-only inputs). Service accounts and agents cannot be reviewers.

**Due dates and escalation** for `ai_review` tasks follow the step's `due` expression and the tenant's business calendars ([[WF-sla-and-business-calendars]]); an overdue review escalates like any human task and never auto-approves.

<!-- section:evaluation -->
## Evaluation

| Gate | Content | Threshold (proposed) |
|---|---|---|
| Platform step suites ([[TST-evals-and-ai-testing]]) | Per step kind and language: classification on synthetic filings, extraction of dates and amounts in Indian, Singapore and US formats, summary faithfulness, draft template fill | Classification macro-F1 at least 0.85; extraction exact-match at least 0.90 for dates and amounts; summary grounding score at least 0.95 |
| Tenant calibration set (needed for `below_threshold`) | At least 30 labelled examples per label (or per field) from sandbox or approved historical items | Precision at threshold at least `autoAcceptAt` with a 95 percent lower confidence bound reported |
| Simulation ([[WF-workflow-simulation]]) | Blueprint run with AI steps using recorded outputs or live sandbox calls | Every AI step's fallback path exercised; cost estimate per case shown |
| Live production signals | Review overturn rate, sampled-error rate, fallback rate, time in review | Overturn above 10 percent over 100 reviews opens a designer review |

The studio shows the latest evaluation and calibration results next to each AI step; publishing is blocked if the platform suite for that step kind is failing in the tenant's region.

<!-- section:failure -->
## Failure modes and fallback

| Failure | Behaviour |
|---|---|
| AI turned off by policy after publish, case restricted, party opted out | Fallback (usually a human task "Classify these documents"); the case continues |
| Provider unavailable or timeout | Temporal retries with backoff up to the step timeout, then fallback |
| Budget exhausted | Fallback to human task for `classify` and `extract`; `summarise` and `draft` are skipped with a note; never blocks a legal step ([[AI-cost-controls]]) |
| Low confidence | Human task |
| Invalid output (label outside set, field type mismatch) | One repair attempt, then human task |
| Reviewer never acts | Task escalates; output expires after the HITL expiry; fact stays unset; fallback applies |
| Model change degrades accuracy | Automatic switch to `always`; designer notified |

<!-- section:cost -->
## Cost and limits

Each step declares `maxTokensPerRun`; simulation estimates cost per case from the blueprint (for example: classification of 40 documents at about 3,000 input tokens each, extraction for 5 documents, one filing summary). Usage is attributed to the tenant, the unit that owns the case, the case type and the step (`budgetScope` from the policy), so admins can see which blueprint steps spend most in [[RPT-platform-ai-usage-analytics]]. Calibration and live sandbox tests are charged as `evaluation` usage.

<!-- section:logging -->
## Logging and audit

- `ai_outputs` rows for steps carry `workflow_id`, `step_id`, `case_type_key`, `blueprint_version`, `prompt_version`, `label_set_version` or `field_group_version`, `confidence`, `acceptance` (`approved`, `approved_with_edits`, `accepted_by_policy`, `rejected`), and the reviewer for human-reviewed items.
- Audit events: `ai.step.completed`, `ai.step.auto_accepted`, `ai.step.fallback_taken` (with reason code), `ai.step.mode_downgraded`, plus HITL events for reviews.
- The case timeline shows AI-classified and AI-extracted items with their label, so case staff can see which facts came from AI.
- Temporal history keeps only references (output IDs), never document text; legal evidence lives in the audit trail ([[WF]] principle 6).

<!-- section:questions -->
## Open questions

- [ ] Workflow group: confirm the `ai_step` node binds to AI step definitions as sketched, add the `legal_effect` tag on decision tables, and confirm `accepted_by_policy` facts are allowed downstream. The process-definition model now states the D8 exception. (owner: workflow group)
- [ ] Platform floor for auto-accept threshold (proposed 0.85) and minimum calibration examples (proposed 30 per label). (owner: AI platform lead)
- [ ] Is `accepted_by_policy` acceptable to institutions at all, or do some (for example court programmes) require `always` for every AI step? Decided for the review pass (D8): tenant setting `ai.workflow_steps.allow_auto_accept`, off by default in every blueprint; final confirmation is a CTO decision. (owner: CTO, product with tenants)
- [ ] Should corrected auto-accepted facts re-run downstream routing automatically or create a task for the case manager? (owner: workflow group)

<!-- checks -->
## Template checks

<!-- check:risk -->
### Risk classification and impact

Steps are T1 when outputs stay internal (classification and extraction for routing) and T2 when outputs enter the record or a draft after review. No step kind can act on the merits; provenance rules stop unreviewed AI facts from reaching anything with legal effect. Each blueprint with AI steps is listed under inventory entry `AIS-WF-AI-STEPS`.

<!-- check:privacy -->
### Privacy and redaction

Inputs are limited to selected documents and pages; redaction applies; opted-out parties' submissions are excluded; tribunal-only inputs only for tribunal reviewers; Temporal history holds references only.

<!-- check:residency -->
### Residency

Steps run on the regional `ai-pipelines` task queue, call in-region zero-retention routes through the gateway and store outputs in regional Postgres and object storage.

<!-- check:security -->
### AI security and tenant isolation

Tenant configuration enters prompts only as validated structured variables; documents are untrusted content; agent tasks are limited to read and propose tools with step limits; validator rejects AI facts flowing into legal-effect logic (OWASP LLM05 improper output handling and LLM06 excessive agency [R2]).

<!-- check:oversight -->
### Human oversight

Draft, summary and agent outputs always need a named reviewer; auto-accept is limited to calibrated internal classification and extraction with sampling and automatic downgrade; overdue reviews escalate, never auto-approve (supports EU AI Act human-oversight expectations where applicable [R3]).

<!-- check:evals -->
### Evaluation

Platform suites per step kind with thresholds, tenant calibration sets for auto-accept, simulation of fallbacks and costs, and re-evaluation on model changes with automatic downgrade.

<!-- check:monitoring -->
### Production monitoring and AI incidents

Review overturn rate, sampled-error rate, fallback rate, auto-accept share and spend per step, per blueprint and tenant, with thresholds that notify the designer and downgrade auto-accept.

<!-- check:cost -->
### Cost and limits

Per-step token and call limits, per-case tenant cap, per-run interceptor cap, cost estimate in simulation and attribution to unit, case type and step.

<!-- check:audit -->
### Audit and traceability

Every output records blueprint, prompt, label-set or field-group, model and policy versions and its acceptance path, so each AI-sourced fact in a case can be traced to its origin and reviewer (ISO/IEC 42001 [R1]).

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
    "body": "OWASP Foundation",
    "excerpt": "Risk list including prompt injection, sensitive information disclosure, improper output handling, excessive agency, system prompt leakage, vector and embedding weaknesses, misinformation and unbounded consumption.",
    "id": "R2",
    "ident": "OWASP Top 10 for LLM Applications",
    "kind": "standard",
    "title": "OWASP Top 10 for Large Language Model Applications",
    "url": "https://genai.owasp.org/llm-top-10/",
    "version": "2025"
  },
  {
    "excerpt": "Annex III lists high-risk uses, including AI intended to assist a judicial authority in researching and interpreting facts and the law and applying the law to facts, or used in a similar way in alternative dispute resolution. Article 6(3) excludes Annex III systems that perform narrow procedural or preparatory tasks and do not materially influence the outcome of decision making; Article 26 sets deployer duties (human oversight, log keeping); Article 50 sets transparency duties.",
    "id": "R3",
    "issuer": "European Parliament and Council",
    "jurisdiction": "EU",
    "kind": "regulation",
    "ref": "Regulation (EU) 2024/1689",
    "status": "in force, phased application",
    "title": "Artificial Intelligence Act",
    "url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
  }
]
```

<!-- end -->
