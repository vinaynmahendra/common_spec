---
id: "OBS-ai-usage"
title: "AI usage"
parent: "OBS"
order: 6
type: "capability"
template: "observability"
status: "draft"
owner: null
indicative: false
summary: "Telemetry for every AI gateway call: model, provider, tokens, latency, cost, cache and fallback, guardrail outcomes and human review signals — never prompt or completion text"
links: []
rev: 2
syncHash: "c9b371f121cfefcf"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 11.6 AI usage

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Telemetry for every AI gateway call: model, provider, tokens, latency, cost, cache and fallback, guardrail outcomes and human review signals — never prompt or completion text

<!-- section:purpose -->
## Purpose

Answers: *What does AI cost per tenant and feature? Which models are slow or failing? How often do guardrails fire? Do neutrals and secretariat users accept, edit or reject AI drafts?* Users: AI platform team, finance, product, and [[RPT-platform-ai-usage-analytics]]; quality signals also feed ISO 42001 monitoring in [[AI-ai-governance-and-impact]].

All AI calls go through the AI gateway ([[AI-ai-gateway]]), which is the single emitter for call-level telemetry. Budget enforcement uses the authoritative token ledger in [[AI-cost-controls]]; telemetry is reconciled with it, not used instead of it.

<!-- section:catalogue -->
## Event catalogue

**Span per AI call** (`gen_ai` attributes follow the OpenTelemetry GenAI semantic conventions [R1])

| Attribute | Type | Example |
|---|---|---|
| `gen_ai.operation.name` | enum | `chat`, `embeddings` |
| `gen_ai.provider.name` | string | provider ID |
| `gen_ai.request.model` / `gen_ai.response.model` | string | |
| `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens` | int | |
| `nomo.ai.feature` | enum | `case_summary`, `draft_procedural_order`, `award_drafting_assist`, `transcript_cleanup`, `translation`, `rag_answer` |
| `nomo.ai.prompt.id` / `nomo.ai.prompt.version` | string / int | From [[AI-prompt-management]] |
| `nomo.ai.cost_usd_micros` | int | Computed from the versioned price table |
| `nomo.ai.cache_hit` | bool | |
| `nomo.ai.fallback_used` | bool | Model routing fallback |
| `nomo.ai.residency_region` | enum | Region where inference ran; must equal the tenant's region |
| `nomo.tenant.id`, `nomo.persona` | | Standard context |

**Events**

| Event | When | Emitter | Attributes | PII |
|---|---|---|---|---|
| `nomo.ai.guardrail_triggered` | A guardrail acts ([[AI-guardrails]]) | Gateway | `guardrail.type` (`pii_redacted`, `content_blocked`, `ungrounded_citation`, `injection_detected`), `action` (`redacted`, `blocked`, `flagged`), `nomo.ai.feature` | No (no matched text) |
| `nomo.ai.output_reviewed` | A human accepts, edits or rejects AI output ([[AI-human-in-the-loop]]) | Domain UI action | `decision` (`accepted`, `edited`, `rejected`), `edit_ratio` (0–1, character-level), `nomo.ai.feature`, `nomo.ai.prompt.version` | No |
| `nomo.ai.budget_threshold` | Tenant reaches 80% / 100% of its AI budget | [[AI-cost-controls]] | `threshold_pct`, `period` | No |

**Never captured**: prompts, completions, retrieved passages, document text, transcripts, embeddings. The GenAI conventions' optional content-capture attributes and events are disabled in SDK configuration and dropped in the collector.

<!-- section:metrics -->
## Metrics

| Metric | Instrument | Unit | Labels |
|---|---|---|---|
| `gen_ai.client.token.usage` [R1] | Histogram | `{token}` | `gen_ai.token.type` (`input`, `output`), `gen_ai.request.model`, `gen_ai.provider.name`, `nomo.ai.feature` |
| `gen_ai.client.operation.duration` [R1] | Histogram | `s` | `gen_ai.operation.name`, `gen_ai.request.model`, `error.type` |
| `nomo.ai.cost` | Counter | `USD` (micros) | `nomo.tenant.id`, `nomo.ai.feature`, `gen_ai.request.model` |
| `nomo.ai.requests` | Counter | `{request}` | `nomo.tenant.id`, `nomo.ai.feature`, `outcome` |
| `nomo.ai.guardrail_triggers` | Counter | `{trigger}` | `guardrail.type`, `nomo.ai.feature` |
| `nomo.ai.review_decisions` | Counter | `{decision}` | `decision`, `nomo.ai.feature` |

Tenant is a label on cost and request counts (registry-approved: tenants × features × outcomes series).

<!-- section:sli -->
## SLIs and SLOs

| SLI | SLO (proposed) | Window |
|---|---|---|
| AI calls returning a usable result (not error, not timeout) / all | 99% per feature | 28 days per region |
| Interactive AI calls (drafting panel) first token < 3 s / all | 95% | 28 days |
| Telemetry cost vs ledger cost difference | < 2% daily | Daily reconciliation |

<!-- section:alerts -->
## Alerts

| Condition | Severity | Route |
|---|---|---|
| AI error rate for a feature > 5% for 15 min | Page (business hours) | AI platform team |
| Inference residency mismatch (`nomo.ai.residency_region` ≠ tenant region) | Critical → page | AI platform + security; possible cross-border transfer |
| Cost per hour for a tenant > 3× its 7-day baseline | Ticket | AI platform + customer success |
| `ungrounded_citation` rate for a feature > 2× baseline after a prompt version change | Ticket | Prompt owner; consider rollback of prompt version |
| `rejected` share of AI drafts > 50% for a feature over 7 days | Ticket | Product + AI governance |

<!-- section:dashboards -->
## Dashboards

- **AI operations**: latency, errors, fallbacks by model and provider, per region.
- **AI cost**: cost by tenant, feature and model; budget usage.
- **AI quality**: guardrail triggers, review decisions and edit ratio by feature and prompt version; links to eval results from [[TST-evals-and-ai-testing]].

<!-- section:pipeline -->
## Collection pipeline

The gateway emits spans, events and metrics through `@nomology/telemetry` into the regional collector ([[OBS-foundations#pipeline]]). The price table (model → input / output price, effective date) is versioned configuration; cost is computed at emission time and recomputed in Reporting if prices are corrected.

<!-- section:retention -->
## Retention and privacy

Metrics 13 months; AI spans 14 days; review and guardrail events 13 months (needed for ISO 42001 monitoring evidence and model / prompt comparisons). No prompt or output content is stored in telemetry; where content must be kept for human review or evaluation, it is stored in the application database under case retention, not in telemetry.

<!-- section:questions -->
## Open questions

- [ ] Which AI features are in scope at Phase 6, and their final `nomo.ai.feature` keys?
- [ ] Is `edit_ratio` an acceptable quality signal for neutrals, or is it seen as monitoring judges' work? (Needs product and governance view.)
- [ ] Do tenants see their own AI quality signals, or only usage and cost?
- [ ] Price table owner and update process.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant and region tagging

Every AI span carries tenant, persona and the region where inference ran; a mismatch between inference region and tenant region is a critical alert because it could mean an unlawful transfer. Cost and request counts carry tenant labels within a registry budget.

<!-- check:naming -->
### Naming and schema

Standard `gen_ai.*` attributes and metrics from the OpenTelemetry GenAI conventions [R1]; platform-specific attributes use `nomo.ai.*` and are registered. The GenAI conventions are still evolving, so the registry pins the version we follow.

<!-- check:privacy -->
### Personal and confidential data

Prompts, completions, retrieved passages and embeddings never enter telemetry: GenAI content capture is disabled in the SDK and the attributes are dropped in the collector. Guardrail events record the type and action, never the matched text. Review events store only the decision and an edit ratio.

<!-- check:slo -->
### SLIs, SLOs and error budgets

Usable-result rate per feature and first-token latency for interactive drafting, per region over 28 days.

<!-- check:cost -->
### Volume and cost

Cost per call is computed from a versioned price table and reconciled daily with the [[AI-cost-controls]] ledger within 2%; spikes per tenant create tickets.

<!-- citations -->
## Citations

```json
[
  {
    "body": "OpenTelemetry (CNCF)",
    "excerpt": "GenAI semantic conventions (gen_ai.* attributes and metrics) are maintained in this repository.",
    "id": "R1",
    "ident": "GenAI semantic conventions",
    "kind": "standard",
    "title": "OpenTelemetry GenAI semantic conventions repository",
    "url": "https://github.com/open-telemetry/semantic-conventions-genai"
  }
]
```

<!-- end -->
