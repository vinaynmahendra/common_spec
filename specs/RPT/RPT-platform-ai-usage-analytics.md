---
id: "RPT-platform-ai-usage-analytics"
title: "AI usage analytics"
parent: "RPT"
order: 6
type: "capability"
template: "report"
status: "draft"
owner: null
indicative: false
summary: "Platform-wide and per-tenant views of AI usage, cost against budget, latency and quality signals (acceptance, edits, flags); tenant users see only their own tenant"
links: []
rev: 3
syncHash: "c5ca88b6fb52ac9f"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.6 AI usage analytics

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Platform-wide and per-tenant views of AI usage, cost against budget, latency and quality signals (acceptance, edits, flags); tenant users see only their own tenant

<!-- section:audience -->
## Audience and questions

| Persona | Frequency | Questions |
|---|---|---|
| Tenant admin | monthly | Q1 How much AI did we use, on which features, and against our quota? |
| Nomology AI platform team | weekly | Q2 What does AI cost per tenant, feature and model, and is any tenant near its budget? Q3 Are latency and failure rates within target per provider? |
| AI governance (ISO 42001 owner) | monthly | Q4 How often are AI outputs accepted, edited or rejected by humans, and how often flagged by guardrails? |
| Account managers | monthly | Q1 for their tenants |

<!-- section:metrics -->
## Metric definitions

Source: [[OBS-ai-usage]] events written by the [[AI-ai-gateway]] (one event per model call), review outcomes from [[AI-human-in-the-loop]], budgets from [[AI-cost-controls]].

| ID | Metric | Formula | Grain |
|---|---|---|---|
| AIU-M1 | Model calls | count of `ai.request_completed` | tenant × feature × model × day |
| AIU-M2 | Tokens | input + output tokens | same |
| AIU-M3 | Cost | Σ tokens × price of the model version on the call date (price table versioned) | tenant × feature × currency × day |
| AIU-M4 | Budget used | month-to-date AIU-M3 ÷ tenant monthly AI budget | tenant × day |
| AIU-M5 | Latency p95 | from call duration | provider × model × region × day |
| AIU-M6 | Failure / fallback rate | failed or fallback calls ÷ calls | provider × model × day |
| AIU-M7 | Human acceptance rate | outputs approved without edit ÷ outputs reviewed | feature × tenant × month |
| AIU-M8 | Edit distance | median normalised edit distance between AI draft and approved text | feature × month |
| AIU-M9 | Guardrail flags | count of guardrail interventions by type (PII redaction, grounding failure) | feature × month |

<!-- section:dimensions -->
## Dimensions and filters

Tenant, feature (summarisation, drafting assistant, transcription, translation), model and version, provider, region, user persona, period.

<!-- section:freshness -->
## Freshness and delivery

AIU-M4 every 15 minutes (budget alerts are raised by [[AI-cost-controls]], not by this report); others daily.

<!-- section:lineage -->
## Data sources and lineage

AI gateway events (no prompt or completion text) → `rpt.fct_ai_call`; review outcomes → `rpt.fct_ai_review`; model price table versioned in the gateway config.

<!-- section:quality -->
## Data quality and reconciliation

AIU-M3 reconciles to provider invoices monthly within 2% (proposed) per provider and region; every call event has tenant, feature and model.

<!-- section:access -->
## Access and privacy

Tenant admins see their tenant only; no prompt, completion or case content in this report; per-user breakdown only for Nomology AI platform team with a stated purpose.

<!-- section:questions -->
## Open questions

- [ ] Is AI cost shown to tenants in money or only in tokens / credits (pricing decision with [[BIL-plans-entitlements-and-usage]])
- [ ] Which quality signals the AI governance owner needs for ISO 42001 monitoring evidence ([[AI-ai-governance-and-impact]])

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Tenant users query `rpt.*` as `rpt_tenant_reader` with `app.tenant_id` set per transaction through the same Prisma extension as the app ([[MT-prisma-client-extension-wraps]]); every table behind this report carries `tenant_id` with forced RLS [R1], so isolation does not depend on a WHERE clause. With no tenant set the query returns zero rows (tested). Nomology staff use the separate platform view under `rpt_platform_reader` ([[MT-cross-tenant-reporting-via-a]]). Export and email jobs carry `tenantId` in the BullMQ job payload and re-set the tenant before querying; cache keys are prefixed `rpt:{tenantId}:` ([[PKG-caching]]). The cross-tenant suite in [[TST-multi-tenant-isolation-tests]] logs in as tenant A and asserts no tenant B row in any metric, drill-down or export.

<!-- check:residency -->
### Residency and cross-region figures

AI call events are stored in the tenant's region (the gateway routes calls to in-region providers where available); platform-wide views read aggregates only.

<!-- check:definitions -->
### Metric semantics

Cost uses the model price in force on the call date from a versioned price table; acceptance and edit-distance are defined against the approved text in the human review step.

<!-- check:security -->
### Access, privacy and export

No prompt or output content reaches reporting tables; per-user views restricted to the AI platform team.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Table owners normally bypass row security; ALTER TABLE ... FORCE ROW LEVEL SECURITY makes policies apply to the owner as well.",
    "id": "R1",
    "kind": "vendor",
    "title": "PostgreSQL documentation: Row Security Policies",
    "url": "https://www.postgresql.org/docs/current/ddl-rowsecurity.html",
    "vendor": "PostgreSQL Global Development Group"
  }
]
```

<!-- end -->
