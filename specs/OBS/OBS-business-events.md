---
id: "OBS-business-events"
title: "Business events"
parent: "OBS"
order: 2
type: "capability"
template: "observability"
status: "draft"
owner: null
indicative: true
summary: "Indicative catalogue of domain events (cases, neutrals, transcribers, hearings, documents, invoices) written to the transactional outbox and consumed by Reporting, webhooks and business metrics"
links: []
rev: 2
syncHash: "46ee500413e068dc"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 11.2 Business events

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Indicative catalogue of domain events (cases, neutrals, transcribers, hearings, documents, invoices) written to the transactional outbox and consumed by Reporting, webhooks and business metrics

<!-- section:purpose -->
## Purpose

Business events record that something meaningful happened in a case's life (filed, served, neutral appointed, transcript delivered, bundle issued, invoice paid). They answer operational and management questions — *how many SEBI ODR matters moved to conciliation this week per tenant? how long from appointment to first hearing?* — and feed [[RPT-cases]], [[RPT-neutrals]], [[RPT-transcribers]], [[RPT-documents]], aggregator reporting ([[RPT-aggregators]]) and outbound webhooks ([[INT-webhook-event-catalogue]]).

They are **not** the audit trail ([[PKG-audit-trail]], the tamper-evident legal record of every action) and not debug telemetry. One event type can feed several consumers, so the schema is a data contract.

This catalogue is **indicative** (node marked indicative): event names and attributes will be finalised with each domain schema ([[DOM-cases-schema]], [[DOM-neutrals-schema]], [[DOM-transcribers-schema]], [[DOM-hearings-schema]], [[DOM-documents-schema]], [[DOM-invoices-and-vendor-bills-schema]]).

<!-- section:catalogue -->
## Event catalogue

**Envelope (every event)**

| Field | Type | Notes |
|---|---|---|
| `event.name` | string | Registry name, e.g. `nomo.case.stage_changed` |
| `event.version` | int | Schema version; breaking change = new version, dual emission for one release |
| `event.id` | UUID | Idempotency key for consumers (= outbox row ID) |
| `occurred_at` | timestamp (UTC) | Time of the domain change, in the same transaction |
| `nomo.tenant.id` | UUID | |
| `nomo.product` | enum | `cord`, `teres`, `hkiac-cmp` |
| `actor.type` | enum | `user`, `system`, `api_client` |
| `actor.persona` | enum | As in [[OBS-foundations#catalogue]] |
| `trace_id` | string | Links back to the request that caused it |

**Events (indicative)**

| Event | When emitted | Emitter | Attributes (type) | PII |
|---|---|---|---|---|
| `nomo.case.created` | Case record created (draft or intake) | Cases domain | `case.id` (UUID), `case.type` (enum), `intake.channel` (`portal`, `public_api`, `aggregator`), `aggregator.id` (string, optional) | No |
| `nomo.case.filed` | Statement of claim submitted | Cases | `case.id`, `case.type`, `rule_set.id` + `rule_set.version`, `claim.value_band` (enum band, not amount) | No |
| `nomo.case.stage_changed` | State machine transition ([[WF-entity-state-machines]]) | Cases | `case.id`, `stage.from`, `stage.to` (enums), `transition.reason` (enum) | No |
| `nomo.case.closed` | Final status reached | Cases | `case.id`, `outcome` (enum: `award`, `settled`, `withdrawn`, `dismissed`) | No |
| `nomo.notice.served` | Delivery evidence recorded ([[DOM-service-of-notices-and-proof]]) | Cases / Notifications | `case.id`, `notice.type`, `channel`, `delivery.status` | No |
| `nomo.party.added` | Party or representative joined | Cases | `case.id`, `party.role` (enum) | No (no names) |
| `nomo.neutral.empanelled` | Neutral added to a tenant panel | Neutrals | `neutral.id` (UUID), `panel.id` | No |
| `nomo.neutral.appointed` | Appointment confirmed | Neutrals | `case.id`, `neutral.id`, `appointment.method` (enum) | No |
| `nomo.neutral.conflict_declared` | Conflict declaration recorded | Neutrals | `case.id`, `neutral.id`, `declaration.result` (enum) | No |
| `nomo.hearing.scheduled` / `nomo.hearing.held` | Hearing booked / ended | Hearings | `case.id`, `hearing.id`, `hearing.mode` (enum), `duration_min` (int, held only) | No |
| `nomo.transcript.assigned` / `nomo.transcript.delivered` | Assignment / delivery | Transcribers | `hearing.id`, `transcriber.id`, `turnaround.target_h` (int), `turnaround.actual_h` (float, delivered only) | No |
| `nomo.document.uploaded` | Upload passed malware scan | Documents | `case.id`, `document.id`, `document.kind` (enum), `size_bytes` (int), `pages` (int) | No (no file names) |
| `nomo.bundle.issued` | eBundle version issued ([[DOM-ebundling]]) | Documents | `case.id`, `bundle.id`, `bundle.version`, `pages` | No |
| `nomo.invoice.issued` / `nomo.invoice.paid` | Invoice issued / payment confirmed | Invoices | `invoice.id`, `billing_entity` (`ntpl`, `tapl`, `us`), `currency`, `amount_minor` (int) | No |
| `nomo.vendor_bill.submitted` / `nomo.vendor_bill.paid` | Neutral / transcriber bill | Invoices | `bill.id`, `payee.type` (`neutral`, `transcriber`), `currency`, `amount_minor` | No |

Attributes never allowed: names, emails, phone numbers, addresses, document titles or file names, free-text reasons, claim descriptions.

<!-- section:metrics -->
## Metrics

Derived counters for operational dashboards (bounded labels only; per-tenant analysis happens in Reporting from the events themselves):

| Metric | Instrument | Unit | Labels | Source |
|---|---|---|---|---|
| `nomo.business.events` | Counter | `{event}` | `event.name`, `nomo.product` | Outbox relay on publish |
| `nomo.outbox.lag` | Histogram | `s` | `consumer` (`webhooks`, `reporting`) | Time from `occurred_at` to delivery |
| `nomo.outbox.pending` | Gauge | `{event}` | `consumer` | Outbox relay |

<!-- section:sli -->
## SLIs and SLOs

| SLI | SLO (proposed) | Window |
|---|---|---|
| Events delivered to Reporting within 5 minutes of `occurred_at` / all events | 99% | 28 days per region |
| Events lost (outbox rows never delivered) | 0 | Continuous; reconciled daily by row count |

<!-- section:alerts -->
## Alerts

| Condition | Severity | Route | Runbook |
|---|---|---|---|
| `nomo.outbox.pending` growing for 15 min, or oldest pending > 10 min | Page | Platform on-call | `runbooks/outbox-relay.md` |
| Daily reconciliation: outbox count ≠ Reporting count for a tenant | Ticket | Data / Reporting team | `runbooks/business-event-reconcile.md` |
| Schema validation failures at the relay | Ticket | Emitting domain team | |

<!-- section:dashboards -->
## Dashboards

- **Case flow** (per region, per product): events per hour by type; stage transitions as a flow. Audience: product and operations.
- **Outbox health**: pending, lag, failures per consumer. Audience: platform on-call.

<!-- section:pipeline -->
## Collection pipeline

1. Domain code calls `emitBusinessEvent(name, attrs)` from `@nomology/telemetry`, which validates against the registry and inserts a row into the outbox table ([[INT-api-platform-tables]]) **in the same database transaction** as the change, with tenant ID from the transaction context (row is under RLS).
2. The outbox relay (BullMQ worker) reads committed rows, publishes to consumers (Reporting ingestion in-region, webhook delivery [[APP-webhooks-outbound]]) and increments `nomo.business.events`.
3. Reporting stores events in the regional warehouse / replica schema ([[RPT-report-infrastructure]]).

Because events are written in the business transaction, there are no events for rolled-back changes and no missing events for committed ones.

<!-- section:retention -->
## Retention and privacy

- Outbox rows deleted 7 days after all consumers acknowledge.
- In Reporting, business events follow the **case retention schedule** ([[PKG-retention-and-deletion-schedule]]): when a case is deleted or anonymised, its events are deleted or have `case.id` replaced by a hash.
- Events hold no direct personal data, but `case.id`, `neutral.id` and `transcriber.id` can be linked to people in the app database, so they are treated as pseudonymous personal data with access through Reporting roles only.

<!-- section:questions -->
## Open questions

- [ ] Final event list per domain (this catalogue is indicative).
- [ ] Should `claim.value_band` bands be defined per tenant / currency, and who owns the band table?
- [ ] Is a separate event stream (for example Kafka-compatible) needed later, or is outbox → Reporting enough?
- [ ] Which events feed aggregator reports (for example SEBI ODR status to NSE, [[RPT-example]]) and need stricter delivery guarantees?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant and region tagging

Every event carries `nomo.tenant.id` from the transaction context, and the outbox row is itself tenant-owned under RLS. Reporting views for tenant users filter by tenant in the reporting layer ([[RPT-platform-stats]]).

<!-- check:naming -->
### Naming and schema

Event names are `nomo.<entity>.<past-tense verb>`, declared in the registry with a version; breaking changes create a new version with dual emission for one release. Reporting is a named consumer of each schema, so schema changes are reviewed by the Reporting owner as a data contract. Bounded attributes (stage, channel, outcome) are enums; IDs are never metric labels.

<!-- check:privacy -->
### Personal and confidential data

No names, contact details, file names, titles or free text in any event; amounts only for invoices and bills. IDs are pseudonymous and linkable only through the app database; access to events is through Reporting roles. Events follow case retention, so deletion of a case removes or anonymises its events.

<!-- check:slo -->
### SLIs, SLOs and error budgets

Delivery freshness (99% within 5 minutes) and zero loss, reconciled daily per tenant by row counts, are the SLIs; they matter most for aggregator reports with fixed submission deadlines.

<!-- check:propagation -->
### End-to-end correlation

Each event stores the `trace_id` of the request that caused it, so an anomaly in a report can be traced to the original request in the trace store (within trace retention).

<!-- end -->
