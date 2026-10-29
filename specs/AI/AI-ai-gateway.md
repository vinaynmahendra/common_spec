---
id: "AI-ai-gateway"
title: "AI gateway"
parent: "AI"
order: 1
type: "capability"
template: "ai"
status: "draft"
owner: null
indicative: false
summary: "provider abstraction, model routing, fallbacks"
links: []
rev: 3
syncHash: "4df60de1def01565"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 8.1 AI gateway

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> provider abstraction, model routing, fallbacks

<!-- section:purpose -->
## Intended use

The AI gateway is the single route from platform code to any model: chat / completion, embeddings and (later) speech-to-text. It is infrastructure, not a user feature. Every AI feature (case summary for the secretariat, bundle summary, drafting assistance in [[APP-neutral-workspace]], transcript support in [[APP-transcriber-workspace]]), every tenant agent turn ([[AI-agent-configuration]]), every workflow AI step ([[WF-ai-steps-and-agents]]) and the admin copilot ([[APP-admin-copilot]]) calls it.

It decides, for each call:

1. **Is AI allowed here?** It calls `ai-policy.decide()` ([[AI-tenant-ai-policy]]), which combines the regional kill switch and platform availability flags ([[PKG-feature-flags]]), plan entitlement, the tenant's published AI policy ([[PKG-settings-ai]]), case restrictions, party opt-outs, the caller's permissions and data scopes. The decision also returns the obligations the gateway must apply (allowed routes, redaction, retention, review mode).
2. **Which model, where?** A route from the regional route table, chosen by the tenant's home region ([[MT-data-residency-2]]) and the requested capability, limited to the `routeSet` in the decision (tenant-allowed providers with zero-retention terms).
3. **Within budget?** A reservation against the tenant, unit, user, agent or step budget ([[AI-cost-controls]]).
4. **Safe to send and safe to return?** Input and output guardrails ([[AI-guardrails]]).
5. **What is recorded?** An `ai_requests` row (with `policy_version`), usage event and OpenTelemetry span.

Proposed form (to be confirmed by an ADR, see [[ADR]]): a regional internal service `ai-gateway` running as its own ECS service / Container App per region, with a typed client package `@nomology/ai` used by the Next.js app, the agent runtime and Temporal `ai-pipelines` workers. A service (rather than a library only) lets us restrict network egress to provider endpoints to one set of tasks and hold provider credentials in one place.

**Functional requirements**

| ID | Requirement |
|---|---|
| AIGW-FR-1 | Expose `generate`, `stream` and `embed` operations through `@nomology/ai`; no other code may call providers |
| AIGW-FR-2 | Resolve the route from `ai_model_routes` by `(region, capability)`, restricted to the decision's `routeSet`; never select a route whose region differs from the tenant's home region |
| AIGW-FR-3 | Call `ai-policy.decide()` first and refuse the call with the decision's deny code (for example `AI_FEATURE_DISABLED`, `AI_CASE_RESTRICTED`, `AI_PARTY_OPTED_OUT`) before any data leaves the service; callers cannot pass a pre-computed decision |
| AIGW-FR-4 | Reserve estimated tokens against the applicable budgets before calling; settle actual usage after the call |
| AIGW-FR-5 | Apply input guardrails before sending and output guardrails before returning, using the stricter of the feature's and the decision's redaction obligation |
| AIGW-FR-6 | Fall back only to another route with the same region and capability inside the `routeSet`; otherwise fail closed with `AI_REGION_UNAVAILABLE` |
| AIGW-FR-7 | Write one `ai_requests` row per call with prompt key and version, model and version, policy version, principal (user or agent), token counts, cost and outcome |
| AIGW-FR-8 | Emit OpenTelemetry spans using the GenAI semantic conventions [R1] with tenant and feature attributes |
| AIGW-FR-9 | Support idempotency keys so Temporal activity retries do not double-bill or duplicate outputs |
| AIGW-FR-10 | Validate structured outputs against a Zod schema supplied by the feature; one repair attempt, then fail |
| AIGW-FR-11 | Accept agent and copilot calls only with an `ai_agent` principal in context, and record both the principal and the invoking human |
| AIGW-FR-12 | Store prompt and output bodies according to the decision's retention class (`case`, `short_30d`, `metadata_only`) |

<!-- section:outofscope -->
## Out-of-scope uses

- **Calling models directly from features**, tests or scripts against production data. Prevented by an ESLint `no-restricted-imports` rule on provider SDKs (`openai`, `@aws-sdk/client-bedrock-runtime`, `@azure/openai` and similar) outside `packages/ai-gateway`, and by egress rules that only allow provider endpoints from gateway tasks ([[INF-networking]]).
- **Deciding policy.** The gateway enforces the decision; the rules and their administration live in [[AI-tenant-ai-policy]] and [[PKG-settings-ai]].
- **Cross-region routing for availability.** Not allowed even during an outage, unless a tenant has an approved `ai.models.out_of_region_exception` (written agreement, security and legal approval, expiry).
- **Consumer AI tools** (public chat apps) for case data: covered by Nomology's AI policy, not by the gateway.
- **Model training or fine-tuning** on tenant data: no endpoint exists for it.
- **Executing agent tools.** The gateway returns tool-call requests from the model to the caller; the agent runtime ([[AI-agent-configuration]]) validates and executes them under the intersection rule. The gateway never calls platform operations itself.

<!-- section:models -->
## Models and providers

**Capabilities** (features ask for a capability, not a model):

| Capability | Used for | Notes |
|---|---|---|
| `chat.large` | Summaries of long documents, drafting assistance, agents with case knowledge, admin copilot | Long context window and tool calling needed |
| `chat.small` | Classification, extraction, short rewrites, request classification for copilot | Lower cost |
| `embed.default` | RAG embeddings | Must stay fixed per index; changing it means re-embedding ([[AI-rag]]) |
| `stt.default` | Speech-to-text for transcripts and captions (later) | Per-region availability to be confirmed |

**Route table** `ai_model_routes` (platform-level table, no `tenant_id`, per region):

```sql
create table ai_model_routes (
  id             uuid primary key,
  region         text not null check (region in ('in','sg','us')),
  cloud          text not null check (cloud in ('aws','azure','self')),
  capability     text not null,
  priority       int  not null,            -- 1 = primary, 2 = fallback
  provider       text not null,            -- e.g. 'bedrock', 'azure-openai', 'self-hosted'
  endpoint_ref   text not null,            -- secret / config reference, not a URL in code
  model_id       text not null,
  model_version  text not null,            -- pinned; no floating 'latest' aliases
  supports_tools boolean not null default false,
  zero_retention boolean not null,         -- provider terms confirm no storage of prompts/outputs (incl. abuse monitoring exemption)
  no_training    boolean not null,         -- provider terms exclude training on our data
  status         text not null check (status in ('active','draining','disabled')),
  terms_ref      text not null,            -- link to sub-processor record with retention / no-training terms
  eval_run_id    uuid,                     -- eval run that approved this model for this capability
  unique (region, capability, priority)
);
-- A route can become 'active' only if zero_retention and no_training are true and eval_run_id is set.
```

**Candidate providers (assumption, to be confirmed):** managed model services offered by our regional clouds (for example Amazon Bedrock on AWS and Azure OpenAI on Azure) in or near Mumbai / Hyderabad, Singapore and US regions. Which models are offered in which region, whether processing is guaranteed to stay in that region, and whether zero-retention terms are available, must be confirmed per provider and per model before a route is activated. A self-hosted open-weight model in-region is an option for the fallback route, for regions without a suitable managed model, and for tenants that set `ai.models.self_hosted_only`.

**Tenant filter:** the route set offered to a tenant is the region's active routes whose provider is in `ai.models.allowed_providers` ([[PKG-settings-ai]]).

**Version pinning:** routes name an exact model version. Provider deprecation notices are tracked in the route table (`status = draining`) and a replacement must pass the feature evals, agent evaluation sets and workflow step suites ([[TST-evals-and-ai-testing]]) before it becomes `active`.

**Fallback:** priority 2 route in the same region and capability, inside the tenant's route set. If none is healthy, fail closed.

<!-- section:context -->
## Inputs and context sources

The gateway itself adds no case data; it carries what features send. It enforces minimisation rules on the way:

| Input | Source | Gateway handling |
|---|---|---|
| Rendered prompt | [[AI-prompt-management]] (template plus variables from the feature) | Must reference a published `prompt_key@version`; free-text prompts rejected outside dev |
| Retrieved passages | [[AI-rag]] | Accepted only as retrieval result objects carrying `tenantId`, `caseId` and chunk IDs; the gateway checks they match the request context |
| Context fields | Calling feature | Checked against the feature's declared field allow-list (feature manifest) |
| Identity | Request context | `tenantId`, `region`, `caseId`, `userId`, `feature`, `correlationId`; never sent to the provider |

**Request envelope (client sketch)**

```ts
export type AiContext = {
  tenantId: string; region: 'in' | 'sg' | 'us'; caseId?: string; userId?: string;
  feature: AiFeatureKey; correlationId: string; idempotencyKey: string;
};

export interface AiClient {
  generate<T>(ctx: AiContext, req: {
    capability: 'chat.large' | 'chat.small';
    prompt: { key: string; version?: number; vars: Record<string, unknown> };
    passages?: RetrievedPassage[];
    maxOutputTokens: number;
    schema?: z.ZodType<T>;
  }): Promise<{ requestId: string; output: T | string; citations: Citation[]; usage: Usage }>;
  stream(ctx: AiContext, req: GenerateRequest): AsyncIterable<GenerateChunk>;
  embed(ctx: AiContext, req: { texts: string[] }): Promise<{ vectors: number[][]; model: string; usage: Usage }>;
}
```

<!-- section:prompts -->
## Prompt design and versioning

The gateway resolves prompts; it does not own them. It loads `prompt_key@version` from the registry ([[AI-prompt-management]]), applies the tenant's slot values, and records the exact version used in `ai_requests`. If a feature does not name a version, the pinned version for that tenant and feature is used.

<!-- section:guardrails -->
## Guardrails

Order of checks inside the gateway (details in [[AI-guardrails]]):

1. Policy decision `ai-policy.decide()` ([[AI-tenant-ai-policy]]): kill switch, availability, entitlement, tenant policy, scope, case restriction, party opt-out, principal, data scopes, destination, route set
2. Region route check within the route set (`AI_REGION_UNAVAILABLE`)
3. Budget and rate limit reservation (`AI_BUDGET_EXCEEDED`, `AI_RATE_LIMITED`)
4. Input guardrails: redaction / pseudonymisation per obligation, injection markers on untrusted text, size limits
5. Provider call with timeout
6. Output guardrails: schema validation, content filter, citation and grounding check, de-pseudonymisation
7. Record and return

A blocked call returns an RFC 9457 problem type from the shared catalogue ([[APP-api-error-catalogue-problem]]) and never returns partial provider output.

<!-- section:oversight -->
## Human oversight

The gateway does not approve outputs; it marks every generated output as `generated` (unreviewed) and returns an `ai_outputs` ID so the feature can route it to review ([[AI-human-in-the-loop]]) with the review obligation from the policy decision.

Platform operators (platform admin console, `/platform/ai/routes` and `/platform/ai/killswitch`, [[APP-platform-admin-and-support]]) can:

- Disable a route (`status = disabled`) per region, immediately, with an audit event `platform.ai.route_changed`.
- Use the regional kill switch `ai.killswitch` (all AI off in a region), owned by the AI platform lead, platform security and the on-call incident commander; tenants are notified.

Tenant admins cannot change routes; they choose among permitted providers (`ai.models.allowed_providers`) and can switch AI off for their tenant at once (`ai.policy.enabled = false`).

<!-- section:evaluation -->
## Evaluation

The gateway is tested for behaviour, not output quality (quality evals belong to each feature in [[TST-evals-and-ai-testing]]).

| Test | Pass threshold | When |
|---|---|---|
| Residency: for each region, requests for tenants of that region only hit routes of that region; a route in another region is never selected even when local routes are disabled | 100 percent, blocking | Every CI run and nightly synthetic in each region |
| Policy enforcement: for every deny code of `ai-policy.decide()` (feature off, case restricted, party opted out, not permitted, data scope, kill switch), the provider mock records zero calls | 100 percent, blocking | CI |
| Fail closed: policy snapshot missing or unreadable means deny | 100 percent, blocking | CI with fault injection |
| Route set: a route without `zero_retention` or outside the tenant's allowed providers is never selected | 100 percent, blocking | CI |
| Fallback: primary timeout leads to priority 2 in the same region within the latency budget | 100 percent | CI with fault injection |
| Idempotency: retried activity with same key returns the same `requestId` and no second ledger entry | 100 percent | CI |
| Overhead: gateway added latency excluding provider time (including policy decision) | p95 under 50 ms (proposed) | Load test ([[TST-performance-and-load-testing]]) |
| Model change gate: a new `model_version` in a route requires a linked passing eval run for every feature, agent and AI step definition using that capability | Blocking | Route activation |

<!-- section:failure -->
## Failure modes and fallback

| Failure | Detection | Behaviour |
|---|---|---|
| Provider timeout or 5xx | Timeout (proposed 60 s for `chat.large`, 15 s for `chat.small`), error rate | Retry once with jitter, then fallback route in-region, then `AI_PROVIDER_UNAVAILABLE`; Temporal activities retry later with backoff |
| Provider rate limit (429) | Response code | Back off per provider headers; queue in Temporal for pipeline calls; user sees "AI assistance is busy, try again shortly" |
| No in-region route | Route lookup | Fail closed; feature hides AI actions with an explanation |
| Model deprecated by provider | Route `draining` | Alert 30 days ahead (proposed); replacement must pass evals |
| Malformed structured output | Zod validation | One repair attempt, then error; never store invalid output |
| Gateway down | Health checks | Features degrade to non-AI paths; no case process depends on AI to proceed |

<!-- section:cost -->
## Cost and limits

The gateway enforces limits defined in [[AI-cost-controls]]: per-request `maxOutputTokens` caps, a pre-call token estimate reserved against the tenant budget, per-user and per-tenant rate limits, and a maximum of one retry per route. Costs are computed from a versioned price table and recorded on each `ai_requests` row.

<!-- section:logging -->
## Logging and audit

- `ai_requests` (tenant-owned, forced RLS, regional Postgres): `id, tenant_id, unit_id, case_id, feature, principal_kind, actor_user_id, agent_id, agent_version, workflow_id, step_id, prompt_key, prompt_version, policy_version, route_id, provider, model_id, model_version, region, input_tokens, output_tokens, cost_micros, latency_ms, outcome, deny_code, guardrail_flags, idempotency_key, correlation_id, created_at`.
- Prompt and output bodies are stored encrypted in regional object storage (`ai/{tenantId}/{caseId}/{requestId}/`) and referenced from the row; retention follows the decision's class: with the case retention schedule ([[PKG-retention-and-deletion-schedule]]), 30 days, or metadata only.
- OTel spans carry `gen_ai.operation.name`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens` [R1] plus `nomology.tenant_id`, `nomology.ai.feature` and `nomology.ai.principal_kind`; spans never contain prompt or output text ([[OBS-ai-usage]]).
- Audit events `ai.request.completed`, `ai.request.blocked` (with deny code and policy version), `platform.ai.route_changed` go to [[PKG-audit-trail]].

<!-- section:questions -->
## Open questions

- [ ] Gateway form: regional service (proposed) or in-process library; record as an ADR.
- [ ] Does the agent runtime run inside the gateway service or as a sibling service `ai-agents` (proposed sibling, so the gateway keeps no tool execution)? Record as an ADR.
- [ ] Providers and models per region (India, Singapore, US, and Azure deployments); confirm in-region processing, zero-retention and no-training terms for each.
- [ ] Is a self-hosted open-weight model needed for any region, and who operates GPU capacity?
- [ ] Out-of-region exceptions: allow per tenant with written agreement (now modelled) or forbid entirely?
- [ ] Timeouts and latency budgets per capability (proposed values above).
- [ ] Do we stream tokens to the browser for drafting assistance, and if so how are output guardrails applied to a stream (buffer by sentence or check at end before the draft can be saved)?

<!-- checks -->
## Template checks

<!-- check:risk -->
### Risk classification and impact

The gateway is infrastructure with no direct effect on a case; its risk is enabling every feature's risk (residency breach, data leakage, uncontrolled spend, a call that the tenant's policy forbids). It is recorded as AI system component `AIS-GW` in the inventory ([[AI-ai-governance-and-impact]]) and inherits the highest tier of the features that use it for its controls. Tenant-level control: AI is off until the tenant publishes an AI policy that turns it on, and the gateway enforces that policy on every call.

<!-- check:residency -->
### Residency

| Flow | Where | Control |
|---|---|---|
| Inference | Route in tenant's home region only, within the tenant's route set | Route lookup by `region`; CI and synthetic residency tests |
| Embeddings | Same | Same |
| Prompt / output storage | Regional object storage | Bucket per region ([[PKG-object-storage-abstraction-s3]]) |
| `ai_requests` log | Regional Postgres | RLS |
| Telemetry | Regional collectors, no content | [[OBS-ai-usage]] |

Fallback is fail-closed. Provider-side processing location and zero-retention terms must be confirmed per route before activation (enforced by the `zero_retention` and `no_training` columns).

<!-- check:security -->
### AI security and tenant isolation

Untrusted inputs are party-uploaded documents, transcripts, tenant knowledge and free-text fields; injection defences are applied in [[AI-guardrails]]. The gateway executes no tools: models return text, structured data or tool-call requests that the agent runtime authorises separately (mitigates OWASP LLM06 Excessive Agency [R2]). Provider credentials live only in the gateway task role / managed identity. Cross-tenant leakage is prevented by checking that retrieved passages carry the same `tenantId` and `caseId` as the request context, with an automated test. Policy decisions cannot be supplied by callers.

<!-- check:evals -->
### Evaluation

Behaviour tests with 100 percent pass thresholds (residency, policy enforcement for every deny code, fail closed, route set filtering, fallback, idempotency) run on every CI build; route activation requires a linked passing eval run for every dependent feature, agent and AI step definition. Feature-level quality evals live in [[TST-evals-and-ai-testing]].

<!-- check:cost -->
### Cost and limits

Every call reserves estimated tokens before calling and settles after; `maxOutputTokens` is mandatory; one retry per route maximum; rate limits per user and tenant. Budgets, thresholds and reconciliation are in [[AI-cost-controls]].

<!-- check:audit -->
### Audit and traceability

Each call writes an `ai_requests` row (prompt, model and policy versions, principal and invoking human, tokens, cost, outcome or deny code) with encrypted bodies in regional storage, retention per the policy's class, and audit events for blocked calls and route changes. Approval of outputs is recorded by [[AI-human-in-the-loop]] and linked by `request_id`.

<!-- citations -->
## Citations

```json
[
  {
    "body": "OpenTelemetry (CNCF)",
    "excerpt": "Standard span and metric attributes for model calls, such as requested model, operation name and input / output token usage.",
    "id": "R1",
    "ident": "Semantic conventions for generative AI",
    "kind": "standard",
    "title": "OpenTelemetry semantic conventions for generative AI systems",
    "url": "https://opentelemetry.io/docs/specs/semconv/gen-ai/"
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
  }
]
```

<!-- end -->
