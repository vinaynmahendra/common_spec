---
id: "OBS-usage"
title: "Usage"
parent: "OBS"
order: 4
type: "capability"
template: "observability"
status: "draft"
owner: null
indicative: false
summary: "Feature adoption and usage signals for the UI, API, pipelines and workflows, using pseudonymous IDs and route templates; not the billing meter"
links: []
rev: 2
syncHash: "3f56c61468682992"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 11.4 Usage

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Feature adoption and usage signals for the UI, API, pipelines and workflows, using pseudonymous IDs and route templates; not the billing meter

<!-- section:purpose -->
## Purpose

Answers product and operations questions: *which features do secretariat users actually use? how many API calls does each tenant's integration make? how many eBundles and transcription minutes per tenant per month? which persona journeys are abandoned?* Used by product leads, customer success and [[RPT-mis-and-miscellaneous]] / [[RPT-internal-mis]].

Not the billing meter: plan usage counts that drive invoices (cases, seats, storage, AI tokens) are recorded by [[BIL-plans-entitlements-and-usage]] in its own ledger; usage telemetry is reconciled against it but never used to bill.

<!-- section:catalogue -->
## Event catalogue

| Event | When | Emitter | Attributes | PII |
|---|---|---|---|---|
| `nomo.ui.page_view` | Route rendered (server-side, App Router) | `web` | `url.template`, `nomo.persona`, `nomo.tenant.id`, `nomo.user.id` (pseudonymous) | Pseudonymous |
| `nomo.feature.used` | A registered feature is used (button, action, panel) | Server Action / tRPC middleware | `feature.key` (from the feature registry, [[PKG-feature-flags]]), `nomo.persona`, `nomo.tenant.id`, `nomo.user.id` | Pseudonymous |
| `nomo.journey.step` | Step reached in a multi-step journey (filing wizard, onboarding) ([[PKG-stepper-and-multi-step-form]]) | `web` | `journey.key`, `step.index`, `step.key`, `outcome` (`next`, `back`, `abandon`, `complete`) | Pseudonymous |
| `nomo.api.request` | Public API call completed | REST layer ([[INT-public-api-and-webhooks]]) | `api.client.id`, `http.route`, `http.response.status_code` class, `nomo.tenant.id` | No |
| `nomo.workflow.started` | Temporal workflow started | Temporal client wrapper | `workflow.type`, `nomo.tenant.id` | No |

<!-- section:metrics -->
## Metrics

| Metric | Instrument | Unit | Labels | Notes |
|---|---|---|---|---|
| `nomo.ui.page_views` | Counter | `{view}` | `url.template` group, `nomo.persona` | No tenant label |
| `nomo.feature.uses` | Counter | `{use}` | `feature.key`, `nomo.persona` | |
| `nomo.api.requests` | Counter | `{request}` | `nomo.tenant.id`, `api.family`, `status_class` | Tenant label allowed (registry budget: tenants × 3 × 5 series) |
| `nomo.workflow.starts` | Counter | `{workflow}` | `workflow.type`, `nomo.tenant.id` | Tenant label allowed |

Per-user metrics (daily active users per persona per tenant) are computed in Reporting from events, not as metric series.

<!-- section:sli -->
## SLIs and SLOs

No SLOs: usage is descriptive. Data completeness target (proposed): daily event counts within 1% of server request counts for the same routes.

<!-- section:alerts -->
## Alerts

| Condition | Severity | Route |
|---|---|---|
| A tenant's API requests drop > 80% vs same weekday last week | Ticket | Customer success (integration may be broken) |
| A tenant's API requests exceed 5× baseline | Ticket | Platform + security (possible runaway client or abuse) |
| Usage reconciliation with billing ledger differs > 2% | Ticket | Billing owner |

<!-- section:dashboards -->
## Dashboards

- **Feature adoption** per product and persona (platform-wide, internal only).
- **Tenant usage** (per tenant, internal; tenant admins see their own through [[APP-tenant-admin-console]] reports).
- **Journey funnels**: filing wizard completion and abandonment by step.

<!-- section:pipeline -->
## Collection pipeline

Server-side emission only (no browser analytics script): events go through the normal pipeline ([[OBS-foundations#pipeline]]) to the regional log store and are copied daily to Reporting. Feature keys are validated against the feature registry so free-text names cannot appear.

<!-- section:retention -->
## Retention and privacy

Raw usage events 13 months in-region, then aggregated (no user IDs) indefinitely. `nomo.user.id` is pseudonymous but linkable, so usage events are personal data in law: access through Reporting roles, deleted or de-identified when the user account is erased ([[SEC-data-principal-rights-requests]]). Assumption: product analytics on pseudonymous IDs is within the purposes stated in our privacy notices; to be confirmed by the DPO ([[SEC-privacy-notice-copy]]).

<!-- section:questions -->
## Open questions

- [ ] DPO: is pseudonymous product analytics covered by our notices in each region, or does it need consent?
- [ ] Do tenants want usage reports for their own users (for example secretariat productivity), and is that acceptable under employment and privacy rules in their jurisdiction?
- [ ] Which features are registered for `nomo.feature.used` at launch?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant and region tagging

Every event carries `nomo.tenant.id`; only `nomo.api.requests` and `nomo.workflow.starts` use tenant as a metric label, with a series budget. Tenant admins see only their tenant's usage through Reporting.

<!-- check:naming -->
### Naming and schema

`nomo.<area>.<event>` names in the registry; feature keys come from the feature-flag registry so they are bounded and consistent between flags and usage.

<!-- check:privacy -->
### Personal and confidential data

No browser analytics script; server-side events with route templates and registered feature keys only. User IDs are pseudonymous UUIDs; usage events are still treated as personal data, access-controlled, and erased with the user's account. Raw events age out after 13 months into aggregates with no user IDs.

<!-- check:retention -->
### Retention and residency

13 months raw, then user-free aggregates; deletion follows user erasure requests.

<!-- end -->
