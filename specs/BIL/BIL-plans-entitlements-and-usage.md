---
id: "BIL-plans-entitlements-and-usage"
title: "Plans, entitlements and usage metering"
parent: "BIL"
order: 1
type: "capability"
template: "billing"
status: "draft"
owner: null
indicative: false
summary: "Feature catalogue mapped to plans; entitlements shared by enforcement and billing; usage metering (cases, storage, AI tokens, seats)"
links: []
rev: 4
syncHash: "347462a0e91fbed7"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 10.1 Plans, entitlements and usage metering

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Feature catalogue mapped to plans; entitlements shared by enforcement and billing; usage metering (cases, storage, AI tokens, seats)

<!-- section:purpose -->
## Purpose and scope

Defines what a tenant has bought and how much of it they have used. It owns:
- the **feature catalogue** (every commercially controlled capability, with a stable key),
- **plans** and effective-dated **price-book versions** per currency,
- **contract overrides** for institutional tenants (custom limits, prices, pilots),
- the **entitlement store** and the `@nomology/entitlements` package that the app, workers, billing and the settings resolver all read,
- **usage events** and their aggregation into billable quantities.

Entitlements are commercial records, not settings: they are changed only by `platform_billing` (with maker-checker for overrides and grants), never inherited down the configuration scopes, and never carried in configuration packages. They **gate** settings: a setting definition names the `feature.*` key that must be granted, or the `limit.*` key that caps it, and the settings resolver applies it ([[PKG-configuration-scope-hierarchy]], step 4). Billing-related tenant choices (billing profile, usage alerts, case fees) are settings in [[PKG-settings-billing-and-plans]]. Rollout of code is separate again ([[PKG-feature-flags]]).

Charged party: the tenant (an arbitral institution, a SEBI ODR institution, a CORD organisation, or a court or government programme). The invoicing entity is decided in [[BIL-invoicing-taxes-gst-singapore#tax]]. Parties, counsel and neutrals are never charged by this node; case fees they pay are in [[DOM-invoices-and-vendor-bills]].

This node folds in the former "Core capabilities, features and functions" scope: the feature catalogue below is that list mapped to plans.

<!-- section:model -->
## Pricing model

**Structure**: plan (base fee per period, included allowances) + metered overage + optional add-ons + per-tenant contract overrides. All prices below are **illustrative placeholders for review by the commercial team**, not agreed prices.

| Plan key | For | Base fee / month | Included | Overage |
|---|---|---|---|---|
| `cord.starter` | Small CORD organisations | INR 25,000 / USD 300 / SGD 400 | 30 active cases, 5 staff seats, 50 GB, 1 M AI tokens | Per active case INR 600 / USD 8 / SGD 10 |
| `inst.standard` | Arbitral and ODR institutions | INR 1,50,000 / USD 1,800 / SGD 2,500 | 200 active cases, 20 staff seats, 500 GB, 5 M AI tokens | Case INR 400 / USD 5 / SGD 7; storage INR 8 / USD 0.10 / SGD 0.14 per GB-month; AI INR 60 / USD 0.75 / SGD 1.00 per 1 M tokens |
| `inst.enterprise` | Large institutions, contract-priced | Contract | Contract | Contract |

Add-ons (monthly): `addon.sso` (SAML/OIDC per tenant), `addon.custom_domain`, `addon.public_api`, `addon.ai_drafting`, `addon.transcription_hours` (priced per audio hour).

**Units and definitions**
- *Active case*: a case that was in a non-terminal status (any status other than `closed`, `withdrawn`, `archived` per [[WF-entity-state-machines]]) on at least one day of the billing period. Counted once per period however many days it was active.
- *Staff seat*: a user with a billable tenant role (tenant admin, secretariat, tribunal secretary, transcriber employed by the tenant) who was active on any day of the period. Parties, counsel and neutrals are never seats.
- *Storage GB-month*: mean of daily snapshots of stored bytes (all document versions, recordings, bundles) / 10^9, over the days in the period.
- *AI tokens*: input + output tokens reported by the AI gateway, summed per period; priced per 1 M.

**Currencies**: INR (NTPL), SGD (TAPL), USD (US entity and NTPL/TAPL exports where the contract says so). Prices are set per currency in the price book; no runtime FX conversion for pricing.

**Price-book data model (sketch)**
```prisma
model PriceBookVersion {   // platform-level, immutable once referenced
  id          String   @id @db.Uuid
  planKey     String
  currency    String   @db.Char(3)
  version     Int
  effectiveFrom DateTime @db.Timestamptz
  baseFeeMinor  BigInt
  components  Json     // validated: [{meter, includedQty, unitPriceMicros, unitSize}]
  @@unique([planKey, currency, version])
}
```
Unit prices are stored in **micros of the currency** (1/1,000,000) so per-token prices are exact; amounts are rounded to minor units only at line level.

<!-- section:entitlements -->
## Entitlements

**Feature catalogue (initial)**: keys are stable and referenced by code and by setting definitions; labels are tenant-facing.

| Key | Type | starter | standard | enterprise |
|---|---|---|---|---|
| `feature.cases.core` | boolean | yes | yes | yes |
| `feature.ebundling` | boolean | no | yes | yes |
| `feature.hearings.video` | boolean | yes | yes | yes |
| `feature.transcription` | boolean | add-on | add-on | contract |
| `feature.ai.summaries` | boolean | yes | yes | yes |
| `feature.ai.drafting` | boolean | no | add-on | contract |
| `feature.ai.advanced` (custom agents, workflow AI steps and their auto-accept option, [[PKG-settings-ai]]) | boolean | no | add-on | yes |
| `feature.public_api` | boolean | no | add-on | yes |
| `feature.webhooks` | boolean | no | with public API | yes |
| `feature.sso` | boolean | no | add-on | yes |
| `feature.custom_domain` | boolean | no | add-on | yes |
| `feature.branding.custom_theme` | boolean | yes | yes | yes |
| `feature.branding.unit_themes` | boolean | no | no | yes |
| `feature.branding.compact_attribution` | boolean | no | no | contract |
| `feature.config.packages` (tenant export and import of configuration packages) | boolean | no | yes | yes |
| `feature.data.bulk_export` | boolean | no | yes | yes |
| `feature.payments.case_fees` (collect case fees from parties) | boolean | yes | yes | yes |
| `feature.notify.whatsapp` | boolean | add-on | add-on | yes |
| `feature.notify.sms` | boolean | add-on | yes | yes |
| `feature.custom_email_domain` (send from the tenant's own domain, [[PKG-settings-notifications]]) | boolean | no | yes | yes |
| `feature.custom_roles` (custom roles and permission sets, [[PKG-roles-and-permission-sets]]) | boolean | no | yes | yes |
| `feature.automation_http` (outbound HTTP actions in automation rules, [[PKG-settings-integrations]]) | boolean | no | add-on | yes |
| `feature.calendar_sync` (personal calendar sync) | boolean | no | yes | yes |
| `feature.byo_providers` (tenant-supplied messaging, video or storage providers) | boolean | no | no | contract |
| `limit.active_cases` | soft limit | 30 | 200 | contract |
| `limit.staff_seats` | hard limit | 5 | 20 | contract |
| `limit.storage_gb` | soft limit | 50 | 500 | contract |
| `limit.ai_tokens_month` | soft limit with hard ceiling | 1 M (ceiling 3 M) | 5 M (ceiling 20 M) | contract |
| `limit.api_rpm` | rate limit | n/a | 600 req/min | contract |
| `limit.config_sandboxes` | hard limit | 0 | 1 | 3 (contract) |
| `limit.locales` (enabled languages) | hard limit | 2 | 4 | contract |
| `limit.custom_fields_per_entity` | hard limit | 20 | 100 | contract (platform maximum 200) |
| `limit.upload_mb` (ceiling for one uploaded file) | hard limit | 200 | 500 | contract (platform maximum 2,048) |

All values are illustrative placeholders for the commercial team, like the prices in the model section.

**Requirements**
- **BIL-ENT-1** Entitlements are resolved as: plan version → add-ons → contract override → time-boxed grant (trial / pilot), latest wins per key. The resolved set is stored in `tenant_entitlement_snapshot` and versioned on every change, with `valid_from` and `valid_to`, so the entitlement in force at any past moment can be read (used by point-in-time setting resolution, [[PKG-configuration-scope-hierarchy]]).
- **BIL-ENT-2** The app, workers, billing and the settings resolver read entitlements only through `@nomology/entitlements`: `can(featureKey)`, `limit(limitKey)`, `checkAndConsume(limitKey, qty, { action })`, `snapshotAt(at)`.
- **BIL-ENT-3** Soft limits warn at the thresholds in `billing.usage.alert_thresholds_pct` (default 80% and 100%; in-app banner to the roles in `billing.usage.alert_recipients` and an email), never block, and are billed as overage, unless the tenant chose `billing.usage.overage_policy = admin_approval_for_new_cases` ([[PKG-settings-billing-and-plans]]), which can hold back only new-case creation by tenant staff.
- **BIL-ENT-4** Hard limits block only the action that would exceed them (adding the 21st staff seat, enabling a fifth language), with an accessible message naming the limit and how to raise it.
- **BIL-ENT-5 (due process)** Actions in the **protected list** are never blocked by any limit, unpaid invoice, suspension or setting: filing a submission or response on an open case, uploading evidence before a deadline, joining a scheduled hearing, receiving service of a notice, downloading the record of one's own case. They are recorded with `overLimit=true` and billed normally.
- **BIL-ENT-6** Plan changes take effect in enforcement within 60 seconds (cache invalidation via tenant-scoped Redis key `ent:{region}:{tenantId}`, TTL 5 minutes as backstop; see [[PKG-caching]]); the change also bumps the tenant configuration epoch so entitlement-gated settings re-resolve.
- **BIL-ENT-7** If the entitlement store is unreachable, the package uses the last cached snapshot; if none exists it **fails open** for protected and existing features and **fails closed** for enabling a feature not previously enabled. AI features that require a signed data-processing addendum fail closed.
- **BIL-ENT-8** Entitlements, flags and settings are separate: a capability is available only if `can()` is true **and** its rollout flag is on ([[PKG-feature-flags]]) **and** the tenant's settings allow it.
- **BIL-ENT-9** When a tenant loses an entitlement (downgrade, end of trial or grant), its settings gated by that entitlement become **dormant**: kept, not applied, and listed in the plan-change notice to `billing_admin` and `tenant_owner`. If the entitlement returns, they apply again. Hard-limit downgrades are refused while usage exceeds the target limit (for example more enabled languages than `limit.locales`), and the admin is told what to remove.
- **BIL-ENT-10** Entitlement changes are made only in the platform console (`/platform/tenants/[tenantId]/entitlements`, `/platform/plans`) by `platform_billing` with permission `platform.plan:update`. Contract overrides and grants need a second approver (`platform.plan:approve`) when they exceed the discount threshold (`billing.discount.approval_threshold_pct`) or grant an AI feature; every change is audited as `admin.entitlement.changed`.
- **BIL-ENT-11** Tenants see their plan, entitlements, limits and usage read-only at `/admin/billing` and through `GET /admin/v1/billing/plan`; entitlement-gated settings in every console page show which plan includes them.

Acceptance: *Given* tenant T on `inst.standard` with 20 active staff seats, *when* a tenant admin invites a 21st staff user, *then* the invitation is refused with problem type `entitlement-limit-reached` and the admin sees "Your plan includes 20 staff seats. Remove a seat or contact us to add more." *Given* T is suspended for non-payment, *when* counsel files a response on an open case before its deadline, *then* the filing succeeds and a `usage.case.active` event is still recorded. *Given* T downgrades from enterprise to standard while one unit uses its own theme, *when* the downgrade takes effect, *then* the unit theme value becomes dormant, the unit shows the tenant theme, and the plan-change notice lists the dormant value.

<!-- section:metering -->
## Metering events

**Events** are written to the append-only, tenant-owned table `usage_event` (monthly partitions), either directly by the emitting service in the same transaction as the business change, or by a meter job reading source tables.

| Event type | Source | Emitted when | Quantity | Idempotency key |
|---|---|---|---|---|
| `usage.case.active` | Daily meter job (Temporal schedule `billing-meter-daily`, 00:30 UTC) reading `case` status | Case is in a non-terminal status on that UTC day | 1 per case per day | `case:{caseId}:{yyyy-mm-dd}` |
| `usage.seat.active` | Daily meter job reading memberships | Billable staff membership active that day | 1 per user per day | `seat:{userId}:{yyyy-mm-dd}` |
| `usage.storage.snapshot` | Daily meter job summing object sizes from `document_version`, recordings, bundles | Once per tenant per day | bytes | `storage:{tenantId}:{yyyy-mm-dd}` |
| `usage.ai.tokens` | AI gateway ([[AI-ai-gateway]]) after each completed call | Per model call | input + output tokens | `ai:{gatewayRequestId}` |
| `usage.transcription.seconds` | Transcription pipeline ([[WF-long-running-pipelines]]) on job completion | Per completed media file | audio seconds | `tx:{jobId}` |
| `usage.api.requests` | API gateway counters flushed hourly | Per client per hour | request count | `api:{clientId}:{yyyy-mm-ddThh}` |

```sql
CREATE TABLE usage_event (
  id               uuid        NOT NULL,           -- UUIDv7
  tenant_id        uuid        NOT NULL,
  event_type       text        NOT NULL,
  quantity         numeric(20,0) NOT NULL CHECK (quantity >= 0),
  occurred_at      timestamptz NOT NULL,
  period_key       char(7)     NOT NULL,           -- 'YYYY-MM' in UTC, set at insert
  idempotency_key  text        NOT NULL,
  source_ref       jsonb       NOT NULL DEFAULT '{}', -- ids only, never personal data
  recorded_at      timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, occurred_at, id),
  UNIQUE (tenant_id, event_type, idempotency_key, occurred_at)
) PARTITION BY RANGE (occurred_at);
```
Note: partitioned tables require the partition key in unique constraints, so the idempotency keys above embed the date, making `(tenant_id, event_type, idempotency_key)` unique in practice; `ai:` and `tx:` keys are globally unique IDs. Inserts use `ON CONFLICT DO NOTHING`.

**Aggregation**: at period close the invoice run computes, per tenant and meter: active cases = `count(distinct case id)` over `usage.case.active`; seats = `count(distinct user id)`; storage GB-month = `sum(bytes) / days_in_period / 10^9`, rounded half-up to 2 decimals; AI and transcription = sums. Results go to `usage_aggregate(tenant_id, period_key, meter, quantity, computed_at, input_hash)` where `input_hash` covers the event IDs used, so recomputation can be compared.

**Boundaries**: periods are calendar months in **UTC** for all tenants (proposed; see questions). Events arriving after period close (`recorded_at` > close time) for a closed period are billed on the next invoice as a separate "prior-period adjustment" line, never by changing the issued invoice.

**Independent checks** (nightly): distinct active cases from `case` status history versus `usage.case.active`; storage from object-store inventory versus snapshot; AI tokens from the AI gateway ledger ([[OBS-ai-usage]]). Difference over 0.5% or any missing day raises an alert to the billing on-call before the invoice run.

<!-- section:worked -->
## Worked examples

All examples use the illustrative prices in [[BIL-plans-entitlements-and-usage#model]]. Rounding: unit prices in micros; each line rounded half-up to minor units; tax computed per [[BIL-invoicing-taxes-gst-singapore#worked]].

**Example 1: institution on `inst.standard`, INR, October 2026 (31 days)**

| Meter | Measured | Included | Billable | Unit price | Line amount |
|---|---|---|---|---|---|
| Base fee | — | — | 1 | INR 1,50,000.00 | 1,50,000.00 |
| Active cases | 230 | 200 | 30 | INR 400.00 | 12,000.00 |
| Staff seats | 20 | 20 | 0 | — | 0.00 |
| Storage | 540.00 GB-month | 500 | 40.00 | INR 8.00 | 320.00 |
| AI tokens | 7,200,000 | 5,000,000 | 2.2 M | INR 60.00 per 1 M | 132.00 |
| **Subtotal (before tax)** | | | | | **1,62,452.00** |

Storage: daily snapshots summed to 16,740 GB-days; 16,740 / 31 = 540.00 GB-month.

**Example 2: AI tokens with a small unit price.** 2,345,678 billable tokens at INR 60 per 1 M: 2,345,678 × 60,000,000 micros / 1,000,000 = 140,740,680 micros = INR 140.74068, line rounded half-up to INR 140.74. Summing per-call amounts instead (each call rounded to paise) could drift by up to INR 0.005 per call; this is why pricing is applied once to the aggregate.

**Example 3: mid-period upgrade (proration).** Tenant moves from `cord.starter` (INR 25,000) to `inst.standard` (INR 1,50,000) effective 16 September 2026 00:00 UTC (30-day month, 15 days remaining).
- Credit for unused starter: 25,000 × 15/30 = INR 12,500.00 (credit line)
- Charge for standard: 1,50,000 × 15/30 = INR 75,000.00
- Net charge on the next invoice: INR 62,500.00 before tax. Included allowances are prorated the same way (standard cases 200 × 15/30 = 100 for the remainder of September); usage before 16 September is rated against starter allowances.

**Example 4: late event.** On 3 November a delayed `usage.transcription.seconds` event for 14,400 seconds (4 hours) on 30 October arrives after October was invoiced. It appears on the November invoice as "October adjustment: transcription 4.00 hours" at the October price-book version.

**Example 5: over hard limit during suspension (due process).** Tenant is suspended; counsel files a response. The filing is accepted, the case remains active and is counted in `usage.case.active`. No extra charge exists for the filing itself.

<!-- section:tax -->
## Tax and billing entity

This node does not determine tax. Each priced line carries a `tax_category` used by the tax engine in [[BIL-invoicing-taxes-gst-singapore#tax]]: `saas_subscription` for base fees, add-ons and metered platform use; `transcription_service` for transcription hours (may have a different classification; to be confirmed by the tax adviser).

<!-- section:lifecycle -->
## Invoice and payment lifecycle

Subscription states (code-defined state machine, [[WF-entity-state-machines]]): `trialing → active → past_due → suspended → cancelled`, plus `active → cancelled` at term end. Upgrades take effect immediately with proration (Example 3); downgrades take effect at the next period start and are refused if current usage exceeds the target plan's hard limits (the admin is told which seats to remove). Trials and pilots are time-boxed grants with an end date; on expiry the tenant drops to its contracted plan or to read-only, never deleting data. Invoice states and dunning are in [[BIL-invoicing-taxes-gst-singapore#lifecycle]] and [[BIL-payment-gateway-integration#lifecycle]].

<!-- section:reporting -->
## Revenue and finance reporting

Usage aggregates and entitlement snapshots feed [[BIL-revenue-reporting-hooks-for]] (MRR, overage revenue) and [[OBS-usage]] (feature adoption). Tenants see a **usage statement** in the tenant admin console ([[APP-tenant-admin-console]]) showing each meter by day, reconciling exactly to their invoice lines.

<!-- section:questions -->
## Open questions

- [ ] Commercial team to set real plans, prices and limits per currency; the tables are placeholders.
- [ ] Billing period boundary: UTC month for all tenants or the tenant's local month? Now a setting with default `utc_month` (`billing.period.boundary`, [[PKG-settings-billing-and-plans]]); the commercial decision sets the default per tenant type.
- [ ] Is "active case" the right billable unit for SEBI ODR tenants with high volumes of small claims, or should it be "cases registered in period"?
- [ ] Should neutrals empanelled with the tenant ever count as seats (for example if the tenant pays for their access)?
- [ ] Build or buy the rating engine (in-house versus Lago / Stripe Billing); this node assumes in-house on Postgres.
- [ ] AI hard ceiling behaviour: now a tenant setting (`billing.usage.ai_ceiling_behaviour`, default `block_ai_features`); confirm the default per tenant type.
- [ ] Is `limit.locales` a commercial limit at all? (owner: CCO)
- [x] ~~Merged from "Core capabilities, features and functions": feature catalogue mapped to plans / entitlements~~ — folded into the Entitlements section above.

<!-- checks -->
## Template checks

<!-- check:accuracy -->
### Metering accuracy and reconciliation

Each event type has a deterministic idempotency key (table above) enforced by a Postgres unique constraint with `ON CONFLICT DO NOTHING`, so BullMQ or Temporal retries cannot double count. Keys are kept as long as the partition (7 years for financial evidence; proposed). Usage is aggregated from the append-only `usage_event` table, and `usage_aggregate.input_hash` lets the nightly job recompute any period and compare. Independent counts (case status history, object-store inventory, AI gateway ledger) are compared nightly with a 0.5% alert threshold. Late events become prior-period adjustment lines. If the meter job misses days, it is re-run for those dates from source tables (the daily meters are reconstructable by design; AI and transcription events come from their own durable ledgers). Tenants see a day-by-day usage statement matching the invoice.

<!-- check:money -->
### Money, currency and rounding

Unit prices are stored in micros (`bigint`), amounts in minor units (`bigint`), each with an ISO 4217 code; the `Money` type in `packages/billing` refuses to add different currencies. Pricing is applied once per aggregated line and rounded half-up to minor units (Example 2 shows why). Prices are set per currency, so no FX is used in pricing. Tax rounding is defined in [[BIL-invoicing-taxes-gst-singapore]].

<!-- check:tenancy -->
### Tenant and client attribution

`usage_event.tenant_id` is filled from the transaction tenant context set by the Prisma extension ([[MT-prisma-client-extension-wraps]]); for meter jobs, the Temporal schedule fans out one activity per tenant and the interceptor sets context before any query. The table has forced RLS. The daily job skips tenants that are offboarded or belong to another region (the tenant directory is checked first) and asserts that no event is written for them. AI calls made by Nomology support staff under support access ([[PKG-support-access-and-impersonation]]) are tagged `actor=support` and excluded from billable AI totals.

<!-- check:entitlements -->
### Entitlement enforcement

One store, one package: `@nomology/entitlements` is read by tRPC procedures, public API handlers, workers, the settings resolver and the invoice run. Behaviour at limits is defined in BIL-ENT-3/4, the protected-action list in BIL-ENT-5, failure behaviour in BIL-ENT-7, dormant settings after a downgrade in BIL-ENT-9. Changes propagate within 60 seconds and re-resolve gated settings. Custom institutional terms are contract overrides and time-boxed grants stored as data, so no code change is needed for a pilot or a bespoke limit; versioned snapshots allow point-in-time answers.

<!-- check:audit -->
### Audit trail and adjustments

Price-book versions are immutable once referenced by any subscription; changes create a new version with an `effectiveFrom`. Every contract override and grant records actor, reason code, free-text justification, approver (required above the discount threshold, proposed 20% of list) and is written to the audit trail ([[PKG-audit-trail]]) in the same transaction.

<!-- end -->
