---
id: "AI-cost-controls"
title: "Cost controls"
parent: "AI"
order: 6
type: "capability"
template: "ai"
status: "draft"
owner: null
indicative: false
summary: "Token budgets per tenant with allocations to units, caps per feature, agent and workflow step, user quotas, alerts, limit behaviour and reconciliation"
links: []
rev: 3
syncHash: "88cd68766cd12b36"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 8.6 Cost controls

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Token budgets per tenant with allocations to units, caps per feature, agent and workflow step, user quotas, alerts, limit behaviour and reconciliation

<!-- section:purpose -->
## Intended use

Cost controls keep AI spend predictable and fair across tenants and inside each tenant: a monthly AI budget per tenant, optional allocations to units, caps per feature, agent and workflow step, quotas per user, rate limits, alerts before limits are reached, defined behaviour at the limit, and monthly reconciliation of metered usage against provider invoices.

Budgets come from the tenant's plan entitlement for AI ([[BIL-plans-entitlements-and-usage]]), optionally lowered or divided by the tenant's `ai_admin` or `billing_admin` through the `ai.budget.*` and `ai.quota.*` settings ([[PKG-settings-ai]]). Usage feeds billing as metered events.

**Budget hierarchy** (every call is charged to all the levels that apply; the first exhausted level stops the call):

| Level | Set by | Setting | Example |
|---|---|---|---|
| Tenant monthly budget | Plan entitlement; tenant may lower | `ai.budget.monthly_limit` | USD 2,000 equivalent |
| Unit allocation | Tenant AI admin; unit admin may lower their own | `ai.budget.unit_allocations` | SEBI ODR desk 40 percent |
| Feature cap | Tenant AI admin | `ai.budget.feature_caps` | `bundle_summary` at most 50 percent |
| Agent cap | Agent owner within tenant rules | `monthly_cap` field on the agent definition ([[AI-agent-configuration]]) | Rules assistant USD 100 |
| Workflow step limits | Workflow designer in the blueprint | `limits.maxCallsPerCase`, `limits.maxTokensPerRun` ([[WF-ai-steps-and-agents]]); tenant cap `ai.workflow_steps.max_calls_per_case` | 20 calls per case |
| User daily quota | Platform default; tenant may lower | `ai.quota.<feature>.user_daily_requests` | 30 drafting requests per day |
| Request caps | Platform | `maxOutputTokens`, max input per feature, `ai.budget.single_request_max_percent` | 5 percent of budget |

**Functional requirements**

| ID | Requirement |
|---|---|
| COST-FR-1 | Each tenant has a monthly AI budget in normalised units (USD micro-units of provider cost, plus token counts) in `ai_budgets`, with optional child rows per unit, feature and agent |
| COST-FR-2 | The gateway reserves an estimate against every applicable level before each call and settles actual usage after; reservations expire after 10 minutes if not settled |
| COST-FR-3 | Alerts at the thresholds in `ai.budget.alert_thresholds` (default 50, 80 and 100 percent) per level, to `ai.budget.alert_recipients` and the Nomology account owner (tenant level only) |
| COST-FR-4 | At a limit: behaviour per `ai.budget.on_limit`; by default interactive features show a clear message and stop, and Temporal pipelines pause and wait for a `budgetRaised` signal rather than failing; workflow AI steps take their fallback |
| COST-FR-5 | Per-user daily quotas per feature and per-tenant requests-per-minute limits |
| COST-FR-6 | Per-request caps: `maxOutputTokens` mandatory, maximum input tokens per feature, one retry per route |
| COST-FR-7 | Usage ledger `ai_usage_ledger` is append-only and reconciled monthly against provider invoices per region and account |
| COST-FR-8 | Usage is attributed to tenant, unit, feature, principal (user or agent), case type and workflow step, so admins can see where spend goes ([[RPT-platform-ai-usage-analytics]]) |
| COST-FR-9 | Evaluation and test usage (agent tests, calibration runs, sandbox simulations) is recorded under usage category `evaluation`, visible separately; the platform safety pack is not charged |
| COST-FR-10 | Lowering a budget or quota applies immediately; raising within entitlement needs `ai.budget:update`; enabling overage needs maker-checker with `billing_admin` |

<!-- section:outofscope -->
## Out-of-scope uses

- **Pricing AI to tenants** (plan prices, overage rates): [[BIL-plans-entitlements-and-usage]].
- **Throttling to protect providers' capacity** beyond our rate limits: provider-side quotas are an operational concern of [[AI-ai-gateway]].
- **Hard stop of a case process** because of AI budget: no case step depends on AI, so budgets never block legal steps.

<!-- section:models -->
## Models and providers

Prices are per route (model, region, provider) in a versioned table `ai_model_prices (route_id, input_per_1k, output_per_1k, currency, effective_from)`. Cost per request is computed at settle time from the price version in force.

<!-- section:context -->
## Inputs and context sources

**Planning model (proposed figures; to be replaced by measurements)**

| Feature | Typical input tokens | Typical output tokens | Calls per case |
|---|---|---|---|
| Case summary (secretariat) | 30,000 | 1,500 | 3 |
| Bundle summary (2,000 pages, map-reduce) | 1,000,000 | 20,000 | 1 per bundle issue |
| Drafting assistance (neutral) | 20,000 | 2,000 | 10 to 30 |
| RAG ingestion (embeddings) | about 500 per page | 0 | per document version |

These figures size default budgets per plan and are revisited after the first month of production data ([[OBS-ai-usage]]).

<!-- section:guardrails -->
## Guardrails

- Atomic reservation using Redis counters per `tenant:month`, `tenant:unit:month`, `tenant:feature:month`, `tenant:agent:month` and `tenant:user:feature:day`, updated in one Lua script on the regional Redis (cache instance), with the Postgres ledger as the source of truth; if Redis is unavailable the gateway falls back to a conservative per-request check against Postgres.
- Runaway protection: a single request may not exceed `ai.budget.single_request_max_percent` (default 5 percent) of the tenant's monthly budget without an explicit feature-level exception (bundle summaries).
- Loop protection: a Temporal workflow may not make more than a configured number of AI calls per run (default 200), enforced by an interceptor; agent turns are limited to 8 model steps and 15 tool calls.
- Unit allocations cannot total more than 100 percent; a unit admin can lower but not raise their unit's share.

<!-- section:oversight -->
## Human oversight

Tenant admins see usage, remaining budget per level and top features, agents and blueprint steps at `/admin/ai/usage` ([[APP-tenant-admin-console]]) and can lower budgets at once, raise them up to their entitlement, divide them between units, or request more. Unit admins see their unit only. The Nomology account owner approves increases beyond the entitlement. Platform finance reviews the monthly reconciliation. The admin copilot can draft budget changes but not publish them ([[APP-admin-copilot]]).

<!-- section:evaluation -->
## Evaluation

| Test | Threshold |
|---|---|
| Concurrent reservations do not overspend (100 parallel calls near the limit) | Overspend at most one request's estimate |
| Alerts fire once at each threshold | 100 percent |
| Pipeline pause and resume on `budgetRaised` | Pass |
| Monthly reconciliation difference between ledger and provider invoice | Under 2 percent per region and account (proposed), otherwise investigated |

<!-- section:failure -->
## Failure modes and fallback

| Failure | Handling |
|---|---|
| Estimate too low | Settle records actual cost; next reservation uses updated per-feature estimate |
| Redis counter lost | Rebuilt from ledger; conservative mode until rebuilt |
| Provider price change | New price version with `effective_from`; alert to finance |
| Tenant hits limit mid-bundle summary | Workflow pauses; secretariat sees "AI summary paused: monthly AI limit reached" |
| Unit allocation exhausted while the tenant pool has budget | Unit users see "Your team's AI allowance for this month is used up"; unit admin and AI admin alerted; no automatic borrowing from other units |
| Workflow AI step over its case limit | Step takes its fallback (usually a human task) |
| Agent cap reached | Agent replies "This assistant has reached its monthly limit"; owner alerted |

<!-- section:cost -->
## Cost and limits

This node is the cost model. Defaults per plan are set in [[BIL-plans-entitlements-and-usage]]; usage events `ai.usage.settled` feed metering. Platform-borne costs (evals, re-embedding, guardrail sampling) are tracked under a platform cost centre per region, not charged to tenants.

<!-- section:logging -->
## Logging and audit

`ai_usage_ledger (tenant_id, request_id, unit_id, feature, principal_kind, user_id, agent_id, case_type_key, workflow_step_id, usage_category, route_id, input_tokens, output_tokens, cost_micros, price_version, settled_at)` is append-only, tenant-owned with forced RLS, retained for the billing retention period (assumption: at least 8 years for tax records in India, to be confirmed by finance). Budget, allocation, quota and overage changes are audit events (`admin.ai.budget_changed`, `admin.ai.quota_changed`).

<!-- section:questions -->
## Open questions

- [ ] Budget unit shown to tenants: tokens, credits or currency?
- [ ] Do budgets reset on the calendar month or the billing period?
- [ ] Which features are allowed to exceed the single-request 5 percent cap (bundle summaries)?
- [ ] Should a unit be allowed to borrow unused budget from the tenant pool automatically? Proposed: no, to keep allocations meaningful.
- [ ] Retention period of the usage ledger per billing entity (NTPL, TAPL, US entity); confirm with finance.

<!-- checks -->
## Template checks

<!-- check:risk -->
### Risk classification and impact

Cost controls carry no direct risk to parties because no case step depends on AI; the main risk is commercial (overspend), owned by the AI platform lead and finance.

<!-- check:residency -->
### Residency

Counters and ledgers are in the tenant's region (regional Redis and Postgres); only aggregated, non-personal totals go to billing ([[BIL-plans-entitlements-and-usage]]).

<!-- check:monitoring -->
### Production monitoring and AI incidents

Spend per tenant, unit, feature, agent, step and region is shown in [[OBS-ai-usage]]; alerts on daily spend above three times the 7-day average (proposed) catch runaway use before budget thresholds.

<!-- check:cost -->
### Cost and limits

Per-feature planning model; budget hierarchy from tenant to unit, feature, agent, step and user; alerts at configurable thresholds; defined behaviour at each limit (interactive stops with a message, pipelines pause on a signal, workflow steps fall back); per-request caps; one retry per route; per-workflow and per-agent-turn call caps; evaluation usage reported separately; monthly reconciliation within a proposed 2 percent of provider invoices.

<!-- check:audit -->
### Audit and traceability

Append-only ledger linked to `request_id`, price version, unit, principal and step, so each charge can be recomputed and attributed; budget, allocation, quota and overage changes are audit events.

<!-- end -->
