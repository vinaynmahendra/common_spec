---
id: "PKG-thresholds-and-alert"
title: "Thresholds and alert configuration (consumed by Observability)"
parent: "PKG-configuration-and-customisation"
order: 6
type: "feature"
template: "observability"
status: "draft"
owner: null
indicative: false
summary: "Threshold sets that turn platform and business signals into alerts: platform-audience sets at platform and region scope, tenant-facing sets at tenant scope with unit overrides within platform and regulatory bounds, managed through the configuration change lifecycle; evaluation and routing in Observability"
links: []
rev: 3
syncHash: "730d3a58389ec2c9"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.8.6 Thresholds and alert configuration (consumed by Observability)

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Threshold sets that turn platform and business signals into alerts: platform-audience sets at platform and region scope, tenant-facing sets at tenant scope with unit overrides within platform and regulatory bounds, managed through the configuration change lifecycle; evaluation and routing in Observability

<!-- section:purpose -->
## Purpose

Lets platform operations and tenant admins configure the thresholds that turn signals into alerts, for example "alert the registry lead when more than 20 filings are awaiting review for over a day", "alert when transcription turnaround exceeds 48 hours", "alert when email bounces exceed 5% for a tenant in an hour", "warn the tenant at 80% of storage". Thresholds are configuration artefacts (kind `threshold_set`, [[PKG-configuration-and-customisation]]); the alerting machinery (evaluation, routing, on-call, incidents) is owned by [[OBS-alerting]], which consumes these definitions.

Two audiences:
- **Platform thresholds**: operational conditions per tenant or per region, delivered to Nomology on-call. Authored at `platform` and `region` scope by `platform_admin` in `/platform/thresholds`, published through platform change sets.
- **Tenant-facing thresholds**: aggregate business conditions inside one tenant (queues, turnaround, bounces, quota), delivered as in-app notifications and emails to tenant roles. Authored at `tenant` scope by `tenant_admin` (permission `monitoring.threshold:update`) in `/admin/settings/alerts`; a `unit_admin` may override values for their unit within bounds.

**Boundary with SLAs.** Case-level timers (a response deadline approaching, a hearing not confirmed 48 hours before, a stage target breached) are SLA policies of the case-type blueprint, owned by [[WF-sla-and-business-calendars]] and pinned to each case. This node keeps aggregate and operational thresholds only, so the same condition is never configured in two places. The previously listed defaults "response deadline approaching" and "hearing confirmation missing" move to SLA policies.

**Scopes** ([[PKG-configuration-scope-hierarchy]]): a threshold definition declares which scopes may change its value: `platform` (default and hard bounds), `region`, `tenant` (value and severity within bounds, routing to tenant roles), `unit` (value only). There are no case-type, case or user thresholds; personal alert delivery preferences are notification preferences ([[PKG-settings-personal]]). Bounds can be targeted by tenant type, so a regulator-driven limit (for example SEBI ODR turnaround expectations, assumption pending legal) cannot be loosened by a tenant.

**Lifecycle** ([[PKG-configuration-lifecycle]]): changing a tenant threshold set is `sensitive` (step-up, reason); lowering a severity, widening a value toward its bound or removing a route is `maker_checker`; platform threshold changes are reviewed by a second `platform_admin`.

<!-- section:catalogue -->
## Event catalogue

Events emitted by this package and by the evaluator in [[OBS-alerting]]:

| Event | When emitted | Emitter | Attributes (type) | PII |
|---|---|---|---|---|
| `threshold.definition.published` | A threshold set version is published by a change set | `@nomology/thresholds` | `tenant.id` (string, absent for platform sets), `threshold.set_key` (string), `threshold.set_version` (int), `config.change_set_id` (string), `scope` (enum) | No (pseudonymous IDs) |
| `threshold.breached` | Condition true for the configured duration | Alert evaluator | `tenant.id`, `region` (string), `threshold.key` (string), `threshold.severity` (enum), `observed.value` (double), `limit.value` (double), `limit.source_scope` (enum), `subject.type` (string), `subject.id` (string, e.g. unit ID) | No |
| `threshold.recovered` | Condition false again for the recovery window | Alert evaluator | as above + `breach.duration_s` (int) | No |
| `threshold.notification.sent` | A tenant-facing alert was delivered | Notifications | `tenant.id`, `threshold.key`, `channel` (enum), `recipient.count` (int) | No |
| `threshold.suppressed` | Breach suppressed (maintenance window, duplicate, quiet hours for non-urgent) | Alert evaluator | `tenant.id`, `threshold.key`, `suppression.reason` (enum) | No |
| `threshold.value.out_of_bounds` | A stored tenant or unit value violates a tightened bound | Drift scan ([[PKG-configuration-scope-hierarchy]]) | `tenant.id`, `threshold.key`, `scope` | No |

Threshold definition shape (artefact kind `threshold_set`):
```ts
interface ThresholdDef {
  key: string;                                  // 'case.filings.awaiting_review.count'
  audience: 'tenant' | 'platform';
  signal: RegisteredSignal;                     // metric or query-based signal, validated at publish
  subjectScope: 'tenant' | 'unit' | 'region';   // what one evaluation is about
  condition: { op: '<' | '<=' | '>' | '>='; value: number; forSeconds?: number };
  severity: 'info' | 'warning' | 'critical';
  route: { roles?: TenantRoleKey[] /* e.g. 'secretariat', 'tenant_admin', 'billing_admin' */; onCall?: 'platform-primary' | 'security' };
  editableScopes: ('region' | 'tenant' | 'unit')[];   // where the value may be overridden
  bounds?: { min: number; max: number; tenantTypes?: TenantType[] };   // platform-set limits; may be targeted by tenant type
  lockedFields?: ('severity' | 'route' | 'condition.op')[];             // fields tenants cannot change
}
```

Tenant-facing threshold values resolve like settings: unit override → tenant value → region → platform default, within the intersected bounds; the evaluator records the source scope of the limit used (`limit.source_scope`).

<!-- section:metrics -->
## Metrics

| Metric | Instrument | Unit | Labels | Source |
|---|---|---|---|---|
| `threshold.evaluations` | Counter | `{evaluation}` | `region`, `threshold.key`, `result` (breach/ok/error) | Evaluator |
| `threshold.breaches.active` | UpDownCounter | `{breach}` | `region`, `threshold.key`, `severity` | Evaluator |
| `threshold.evaluation.duration` | Histogram | `s` | `region`, `threshold.key` | Evaluator |
| `threshold.notification.latency` | Histogram | `s` | `region`, `audience` | From breach to delivery |
| `threshold.definitions.published` | Counter | `{version}` | `region`, `audience` | Package |

Tenant ID is an attribute on events and exemplars, not a metric label, to keep cardinality bounded (names follow OpenTelemetry conventions [R1]).

<!-- section:sli -->
## SLIs and SLOs

| SLI | Definition | SLO (proposed) | Window |
|---|---|---|---|
| Alert timeliness | Share of breaches whose notification is delivered within 5 minutes of the condition becoming true for its `forSeconds` | 99% | 28 days |
| Evaluation freshness | Share of evaluation cycles completed within their scheduled interval (1 minute for platform, 15 minutes for tenant business thresholds) | 99.5% | 28 days |

Error budget policy: if alert timeliness misses its SLO in a window, changes to the evaluator and threshold package are frozen except fixes until the budget recovers [R2].

<!-- section:alerts -->
## Alerts

| Alert | Condition | Severity | Routing | Runbook |
|---|---|---|---|---|
| Threshold evaluator stalled | No evaluation cycle completed for 5 minutes in a region | Critical | Platform on-call | `runbooks/obs/threshold-evaluator-stalled.md` |
| Tenant notifications delayed | `threshold.notification.latency` p95 > 10 min for 15 min | Warning | Platform on-call | `runbooks/obs/threshold-notify-latency.md` |
| Invalid threshold definition | Published definition references an unknown signal (should be blocked by validation) | Warning | Platform engineering channel | `runbooks/obs/threshold-invalid.md` |
| Alert storm | > 100 breaches per tenant per hour | Warning | Platform on-call; tenant notifications batched into a digest | `runbooks/obs/threshold-storm.md` |

Default tenant-facing threshold set shipped in each blueprint (editable within bounds; [[PKG-configuration-packages]]): filings awaiting secretariat review > 20 for 24 hours; transcription turnaround breached for more than 3 jobs in a day; email bounce rate > 5% in an hour; invoice unpaid after due date (count > 0, daily digest); storage at 80% and 100% of entitlement; AI token budget at 80% ([[AI-cost-controls]]). Case-level deadline and hearing reminders are SLA policies ([[WF-sla-and-business-calendars]]).

<!-- section:dashboards -->
## Dashboards

- **Platform: threshold health** (on-call) — evaluations, errors, active breaches by region and key, notification latency.
- **Tenant: alerts and SLAs** (tenant admin console) — active and recent breaches for the tenant, by key and case; only the tenant's own data.

<!-- section:pipeline -->
## Collection pipeline

Signals come from the OpenTelemetry pipeline per region ([[OBS-foundations]]) for operational thresholds and from scheduled queries against the regional database (through `withTenant`) for business thresholds; the evaluator runs per region as a BullMQ repeatable job; tenant-facing alerts are sent through [[PKG-notifications]] as class `transactional`; platform alerts go to the on-call tool via [[OBS-alerting]].

<!-- section:retention -->
## Retention and privacy

Threshold definitions: kept as configuration artefacts. Breach and recovery events: 13 months in the regional observability store (proposed). Events contain IDs only (case ID, tenant ID), no names or content. Tenant users see only their tenant's breaches; platform on-call sees all in the region.

<!-- section:questions -->
## Open questions

- [ ] Which tenant-facing thresholds need tenant-type bounds (for example SEBI ODR turnaround) so that regulated timelines cannot be loosened? Legal and product to decide.
- [ ] Do tenants want alerts delivered to external tools (email distribution lists, Teams, Slack) via webhooks ([[APP-webhooks-outbound]]) or connections ([[INT-connections-admin]])?
- [ ] Evaluator implementation: inside our BullMQ workers versus the observability vendor's alerting with per-tenant rules.
- [ ] Confirm with the workflow group that all case-level timers live in SLA policies ([[WF-sla-and-business-calendars]]). (owner: workflow group)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant and region tagging

Every event carries `tenant.id` and `region`; tenant-facing threshold sets, unit overrides and breaches are tenant-owned rows under forced RLS and are shown only in that tenant's console; business-threshold queries run inside `withTenant`. Platform threshold sets are platform-level and invisible to tenants.

<!-- check:naming -->
### Naming and schema

Event and metric names use dotted lowercase namespaces and OpenTelemetry units and attribute naming [R1]; the catalogue above is the registry, and signal names referenced by definitions are validated against registered signals at publish time.

<!-- check:privacy -->
### Personal and confidential data

Breach events carry identifiers only (tenant, case, hearing IDs) and numeric values; notification bodies for tenant alerts are rendered from templates at delivery time and are not stored in telemetry.

<!-- check:slo -->
### SLIs, SLOs and error budgets

Alert timeliness (99% within 5 minutes, 28 days) and evaluation freshness (99.5%) are defined with an error budget policy that freezes non-fix changes when exhausted.

<!-- check:actionability -->
### Alerts and response

Every platform alert has severity, routing and a runbook path; tenant-facing alerts name the case and the action needed (for example "File response by 14 Nov") and link to the case; storms are batched into digests to avoid fatigue.

<!-- check:cost -->
### Volume and cost

Evaluations are bounded by the number of active thresholds (proposed cap 50 per tenant) and run every 1–15 minutes; metrics avoid tenant labels; events are low volume (breaches only). Expected volume is small relative to [[OBS-foundations]] totals.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "kind": "vendor",
    "title": "OpenTelemetry semantic conventions: attribute naming",
    "url": "https://opentelemetry.io/docs/specs/semconv/general/attribute-naming/",
    "vendor": "OpenTelemetry"
  },
  {
    "id": "R2",
    "kind": "web",
    "publisher": "Google",
    "title": "SRE Workbook: Example error budget policy",
    "url": "https://sre.google/workbook/error-budget-policy/"
  }
]
```

<!-- end -->
