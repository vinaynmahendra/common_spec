---
id: "AI-guardrails"
title: "Guardrails"
parent: "AI"
order: 4
type: "capability"
template: "ai"
status: "draft"
owner: null
indicative: false
summary: "PII redaction, injection defences, content filtering, citation grounding and agent tool-call checks; tenants can tighten but never loosen"
links: []
rev: 3
syncHash: "62e720353e83f6f0"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 8.4 Guardrails

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> PII redaction, injection defences, content filtering, citation grounding and agent tool-call checks; tenants can tighten but never loosen

<!-- section:purpose -->
## Intended use

Guardrails are the input and output checks the gateway applies to every AI call, and the tool-call checks the agent runtime applies to every agent action, so that features cannot send more data than they need, cannot be steered by malicious content in documents, cannot use tools beyond their scope, and cannot return unsafe, ungrounded or badly formed text to users.

Four families:

1. **Data protection:** detection and redaction or pseudonymisation of personal identifiers.
2. **Safety and integrity:** prompt-injection defences, content filtering, output handling.
3. **Grounding:** citation checks that every factual statement in a RAG output points to a retrieved passage from the same case (or the same tenant knowledge collection).
4. **Tool use:** checks before and after each agent tool call ([[AI-agent-configuration]]).

Tenants can **tighten** guardrails through AI settings ([[PKG-settings-ai]]): redaction default, party-name pseudonymisation, content filter strictness, agent tool policies. They can never loosen a feature's platform minimum.

**Functional requirements**

| ID | Requirement |
|---|---|
| GRD-FR-1 | Each feature declares a guardrail policy (`redaction: none | pseudonymise | redact`, `grounding: required | optional`, `contentFilter: standard | strict`) in its manifest |
| GRD-FR-2 | Detect identifiers before sending: Aadhaar and PAN numbers, Singapore NRIC / FIN, US SSN, bank account and card numbers, email addresses, phone numbers, postal addresses |
| GRD-FR-3 | Pseudonymise reversibly within one request (`[PARTY_1]`, `[ACCOUNT_1]`); the mapping stays in gateway memory and is never sent or logged |
| GRD-FR-4 | Wrap untrusted text (documents, transcripts, tenant knowledge, user questions, pasted lists, tool results) in delimiters; strip or escape delimiter look-alikes |
| GRD-FR-5 | Reject outputs that fail the feature's schema, contain links or markup outside the allow-list, or trip the content filter |
| GRD-FR-6 | For grounding-required features, flag any sentence without a valid citation and compute a grounding score; block below threshold |
| GRD-FR-7 | Record which checks fired in `ai_requests.guardrail_flags`; never log the redacted values |
| GRD-FR-8 | Apply the stricter of the feature policy and the tenant's resolved settings (`ai.data.redaction_default`, `ai.data.pseudonymise_party_names`) as returned in the policy decision's obligations ([[AI-tenant-ai-policy]]) |
| GRD-FR-9 | Before each agent tool call: check the tool is bound to the agent version, arguments match the schema, `caseId` equals the conversation's case, the tenant tool policy does not block it, and the intersection rule allows it; after each call: validate output schema, trim to declared fields, redact, mark document text as untrusted |
| GRD-FR-10 | Filter out passages and tool results from submissions of a party who has opted out, and from restricted cases, before they reach a prompt |

<!-- section:outofscope -->
## Out-of-scope uses

- **Judging the legal merit or correctness of content.** Guardrails check form, grounding and safety; a person checks substance ([[AI-human-in-the-loop]]).
- **Moderating party filings.** Guardrails apply only to AI inputs and outputs, not to what parties upload.
- **Replacing access control.** Guardrails are a second layer; scope is enforced by RLS and permissions first.

<!-- section:models -->
## Models and providers

- Identifier detection: deterministic pattern and checksum rules first (Aadhaar Verhoeff checksum, PAN format, NRIC check letter), plus an in-region named-entity model for names and addresses where the feature needs it. No detector may send data out of region.
- Content filter: the in-region provider's safety filter where available, plus our own classifier prompt on `chat.small` for neutrality checks (outcome predictions, advice to a party).
- Grounding validator: deterministic citation parsing plus an entailment check on `chat.small` for a sample of sentences (proposed: all sentences for drafting assistance, sampled for summaries).

<!-- section:context -->
## Inputs and context sources

Guardrails see the same inputs as the gateway and the agent runtime. Policy per feature decides what happens to personal data; tenants may tighten it:

| Feature type (examples) | Platform redaction policy | Tenant may tighten to | Why |
|---|---|---|---|
| Case summary for secretariat | Pseudonymise identifiers; keep party names | Pseudonymise names too (`ai.data.pseudonymise_party_names`) | Names are useful; numbers are not |
| Drafting assistance for neutrals | Pseudonymise identifiers and account numbers | Pseudonymise names | Draft text is re-identified on return |
| Classification of filings (document type) | Redact all personal data | — (already strictest) | Task does not need it |
| Extraction into custom fields | Pseudonymise; target fields returned in clear only if the field is marked personal and the step reviewer may see it | Redact | Extraction must return values |
| Transcript spelling support | None for names; redact identifiers | Pseudonymise names | Names are the point of the task |
| Tenant agents | Pseudonymise identifiers | Pseudonymise names; block tools | Mixed sources |
| Admin copilot | Directory names and emails in clear (needed for user administration); no case content | — | Administration task |

<!-- section:guardrails -->
## Guardrails

**Input side**

1. Size and token limits per feature.
2. Identifier detection and pseudonymisation / redaction per the stricter of feature and tenant policy.
3. Opt-out and restriction filters on passages and tool results (GRD-FR-10).
4. Untrusted-content wrapping with unique per-request delimiters; instruction-like phrases inside documents are left as text but flagged (`possible_injection`) for monitoring.
5. Block if the feature's allow-list of variables is violated.

**Tool-call side (agents and agent tasks)**

1. Pre-call checks in GRD-FR-9; a block returns a tool error to the model ("not permitted") and is recorded, never retried with other arguments automatically.
2. Tenant tool policies (`ai.agents.tool_policies`) can block a tool or require user confirmation for roles or units; they can only restrict (pattern from agent access policies evaluated before and after each tool call [R3]).
3. Post-call trimming and redaction; results are untrusted content.
4. Step and tool-call limits per turn.

**Output side**

1. Schema validation (Zod) for structured outputs, including label sets and custom field types for workflow steps.
2. Output handling: render as plain text or a restricted markdown subset; no HTML, no remote images, links only to in-platform document anchors (OWASP LLM05 Improper Output Handling [R1]).
3. Content filter: harmful content, and neutrality rules (no prediction of outcome, no advice to one side, no assessment of credibility of a person); `strict` mode for tenants or features that choose it lowers the block threshold.
4. Grounding: every `[p:<chunkId>]` must be a passage retrieved in this request; sentences without citations are marked; grounding score = cited and supported sentences / factual sentences.
5. Re-identification of pseudonyms inside the gateway before return.

**Refusal behaviour:** a blocked output returns `AI_GUARDRAIL_BLOCKED` with a user-safe reason category ("could not ground the answer in the case documents") and no partial text.

<!-- section:oversight -->
## Human oversight

Guardrail flags are shown to the reviewer next to the output (for example "3 sentences without citations"). Reviewers can report a false positive or a missed issue, which feeds the eval sets. The AI platform lead owns thresholds; changes to thresholds are reviewed like prompt changes.

<!-- section:evaluation -->
## Evaluation

| Check | Test set | Threshold (proposed) |
|---|---|---|
| Identifier detection recall | Synthetic documents with Indian, Singapore and US identifiers in varied formats | At least 0.99 for numeric identifiers; at least 0.95 for names when policy requires |
| Injection resistance | Adversarial documents (hidden instructions, delimiter spoofing, multilingual instructions) | At least 0.98 of attacks fail to change task behaviour |
| Output handling | Outputs with HTML, scripts, external links | 100 percent neutralised |
| Neutrality filter | Labelled outputs with outcome predictions and one-sided advice | Recall at least 0.95, false positive rate under 5 percent |
| Grounding validator | Outputs with planted unsupported sentences | Detect at least 0.95 |

Run on every guardrail or prompt change and nightly ([[TST-evals-and-ai-testing]]); results stored with guardrail version.

<!-- section:failure -->
## Failure modes and fallback

| Failure | Handling |
|---|---|
| Detector misses an identifier | Data reaches an in-region provider under no-training terms; detected in sampling audits, added to tests |
| False positive blocks useful output | User sees reason; reviewer can report; threshold tuned through eval |
| Injection partially succeeds (wrong task, odd text) | Output still needs human approval; flagged `possible_injection`; security review if repeated |
| Grounding validator unavailable | Grounding-required features fail closed |

<!-- section:cost -->
## Cost and limits

Deterministic checks are cheap. Entailment checks add `chat.small` calls; proposed cap of 20 percent extra tokens per request, charged to the tenant budget.

<!-- section:logging -->
## Logging and audit

`guardrail_flags` per request (check name, result, counts; never the matched value); guardrail version recorded; blocked outputs stored encrypted for 30 days (proposed) for investigation, then deleted unless under legal hold.

<!-- section:questions -->
## Open questions

- [ ] Which in-region detector for names and addresses (open-source NER self-hosted, or provider service) per region?
- [ ] Party-name pseudonymisation default per tenant type (now a setting, `ai.data.pseudonymise_party_names`; blueprint defaults in [[PKG-settings-ai#defaults]]): confirm with institutions.
- [ ] Retention of blocked outputs (proposed 30 days, setting `ai.retention.blocked_outputs_days`).
- [ ] Neutrality rules wording: agree with tenants and legal what counts as "advice" or "prediction" ([[APP-voice-tone-and-content-style]]).
- [ ] Should tenant tool policies support conditions on tool arguments (for example block `message.draft` to certain recipient types), or only on roles and units at launch?

<!-- checks -->
## Template checks

<!-- check:privacy -->
### Privacy and redaction

Per-feature redaction policy table that tenants can tighten, deterministic detection for Indian, Singapore and US identifiers, reversible in-request pseudonymisation with the mapping held only in gateway memory, opt-out and restriction filters before prompts, and flags without values in logs. Advisory guidance on data minimisation in AI systems from the PDPC informs the defaults [R2].

<!-- check:security -->
### AI security and tenant isolation

Untrusted content (including tool results, tenant knowledge and pasted lists) is delimited with per-request delimiters; output handling neutralises HTML, scripts and external links; agent tool calls are checked before and after execution against binding, schema, case scope, tenant tool policy and the intersection rule; injection resistance at least 0.98 on adversarial sets; mapped to OWASP LLM01, LLM02, LLM05 and LLM06 [R1].

<!-- check:oversight -->
### Human oversight

Reviewers see guardrail flags next to each output and can report false positives and misses; threshold changes are reviewed like prompt changes.

<!-- check:evals -->
### Evaluation

Recall, injection resistance, output handling, neutrality and grounding-detection thresholds are listed, run on every change and nightly, and stored with guardrail version.

<!-- check:monitoring -->
### Production monitoring and AI incidents

Live rates of `possible_injection`, blocked outputs and low grounding scores per feature and tenant, with alerts on sudden increases (proposed: three times the 7-day baseline); repeated injection flags open a security event ([[OBS-security-events]]).

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
  },
  {
    "excerpt": "Guidance on consent, notification, data minimisation and accountability when personal data is used to develop or deploy AI systems.",
    "id": "R2",
    "issuer": "Personal Data Protection Commission Singapore",
    "jurisdiction": "Singapore",
    "kind": "regulation",
    "ref": "Advisory Guidelines on Use of Personal Data in AI Recommendation and Decision Systems",
    "status": "advisory",
    "title": "Advisory Guidelines on Use of Personal Data in AI Recommendation and Decision Systems",
    "url": "https://pdpc.gov.sg/guidelines-and-consultation/2024/02/advisory-guidelines-on-use-of-personal-data-in-ai-recommendation-and-decision-systems"
  },
  {
    "excerpt": "Agent access policies are evaluated before a tool runs and after it returns, can block, filter or flag for review, apply to users, groups, agents and tools, and can only further restrict what an agent can do, never expand it.",
    "id": "R3",
    "kind": "vendor",
    "title": "About agent access policies",
    "url": "https://docs.glean.com/administration/protect/ai-security/agent-access-policies",
    "vendor": "Glean"
  }
]
```

<!-- end -->
