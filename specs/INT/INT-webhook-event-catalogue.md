---
id: "INT-webhook-event-catalogue"
title: "Webhook event catalogue"
parent: "APP-webhooks-outbound"
order: 1
type: "requirement"
template: "api"
status: "draft"
owner: null
indicative: false
summary: "Every outbound event type, envelope, payload, signing scheme, retry and ordering guarantees (AsyncAPI)"
links: []
rev: 2
syncHash: "bb30a6522485bae9"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 9.4.1.1 Webhook event catalogue

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Every outbound event type, envelope, payload, signing scheme, retry and ordering guarantees (AsyncAPI)

<!-- section:purpose -->
## Purpose, audience and surface

The list of every event type delivered by [[APP-webhooks-outbound]] and returned by `GET /v1/events`, with the common envelope, payload rules and per-event guarantees. The machine-readable source of truth is the AsyncAPI 3.0 document `packages/api-contracts/asyncapi/webhooks.v1.yaml` [R1], generated from Zod schemas in `packages/api-contracts/src/events/*`. This node explains intent and rules.

<!-- section:resources -->
## Resources and identifiers

**Envelope** (field names follow CloudEvents attribute ideas [R2], in our snake_case convention):

```json
{
  "id": "evt_01JBCX4M7Q2T8Z5V9K3N6P1R0S",
  "type": "case.status_changed",
  "api_version": "2026-10-01",
  "occurred_at": "2026-10-28T09:14:03.512Z",
  "tenant": "ten_01J9...",
  "region": "in",
  "subject": { "type": "case", "id": "case_01JB..." },
  "sequence": 14,
  "data": { "...": "type-specific, see table" },
  "links": { "subject": "https://api.in.<platform-domain>/v1/cases/case_01JB..." }
}
```
`id` equals the `webhook-id` header [R3]. `sequence` is monotonic per subject. `tenant` is the tenant's public ID (never its name).

<!-- section:operations -->
## Operations

Not an operation family; events are delivered by [[APP-webhooks-outbound]]. The catalogue:

| Event type | Trigger (committed change) | Subject | `data` fields | Scope needed to subscribe |
|---|---|---|---|---|
| `case.created` | Case registered (UI, API or aggregator) | case | `case_type`, `reference`, `external_reference`, `status` | `cases:read` |
| `case.status_changed` | Any status transition ([[WF-entity-state-machines]]) | case | `from`, `to`, `reason_code` | `cases:read` |
| `case.party_added` / `case.party_removed` | Party joined / removed | case | `party_id`, `role` (claimant, respondent, ...) | `cases:read` |
| `case.representative_added` / `case.representative_removed` | Counsel appointed / ended | case | `party_id`, `representative_id` | `cases:read` |
| `case.tribunal_constituted` | All tribunal members appointed | case | `member_count` | `cases:read` |
| `case.award_issued` | Award published to parties | case | `document_id`, `award_type` | `cases:read` + `documents:read` |
| `filing.received` | Filing accepted with receipt | case | `filing_id`, `filing_type`, `received_at`, `document_ids` | `documents:read` |
| `document.version_available` | New version passed malware scan | document | `document_id`, `version`, `sha256` | `documents:read` |
| `document.rejected` | Upload failed scan or validation | document | `upload_id`, `reason_code` | `documents:read` |
| `bundle.issued` | eBundle issued or re-issued | case | `bundle_id`, `version` | `documents:read` |
| `hearing.scheduled` / `hearing.rescheduled` / `hearing.cancelled` | Hearing changes | hearing | `case_id`, `starts_at`, `ends_at`, `time_zone` | `hearings:read` |
| `hearing.recording_available` | Recording copied and hashed | hearing | `document_id` | `hearings:read` + `documents:read` |
| `transcript.available` | Transcript version approved | hearing | `document_id`, `version` | `hearings:read` + `documents:read` |
| `notice.delivery_updated` | Service evidence changed ([[DOM-service-of-notices-and-proof]]) | notice | `notice_id`, `channel`, `status` | `cases:read` |
| `aggregator.batch.completed` | Bulk intake batch finished | batch | `batch_id`, counts | `aggregator:intake` |
| `webhook.test` | Test operation | endpoint | `{}` | `webhooks:manage` |

Subscriptions are filtered by both the endpoint's `event_types` and the scopes of the API client that registered it; an endpoint never receives an event its registering client could not read through the API. Events about cases are delivered only if the registering principal could see that case under the permission matrix.

<!-- section:schemas -->
## Request and response schemas

Rules for every `data` payload:
- **Thin by default**: IDs, statuses, timestamps and codes. No names, emails, phone numbers, addresses, document content or free text. Receivers fetch details from the API with their own credentials.
- Fields are additive within an `api_version`; receivers must ignore unknown fields and tolerate unknown enum values.
- Timestamps RFC 3339 UTC; local times include `time_zone` (IANA).
- Confidential-tier and tribunal-only items ([[SEC-data-classification]]) never generate public events (for example tribunal deliberation notes, sealed documents).

<!-- section:errors -->
## Error model

Not applicable to delivery (receivers answer with HTTP status codes; see [[APP-webhooks-outbound#events]]). Schema errors are prevented in CI: every event emitted in integration tests is validated against the AsyncAPI schema.

<!-- section:auth -->
## Authentication, scopes and permissions

Signing as in [[APP-webhooks-outbound#auth]]. Subscription is limited by the registering client's scopes (table above).

<!-- section:tenancy -->
## Tenancy and region routing

Each event belongs to exactly one tenant (the `tenant_id` of the outbox row, set from transaction context); the envelope's `tenant` is informational for receivers serving several tenants. Cross-tenant events do not exist; a neutral appointed in two tenants generates separate events in each.

<!-- section:events -->
## Webhooks and events

**Guarantees per event**: at least once, same `id` on every retry and replay, `sequence` per subject, delivery within 60 seconds for healthy endpoints (proposed SLO). Events are emitted only after commit (transactional outbox) and never for rolled-back changes. Retention for `/v1/events`: 30 days.

<!-- section:versioning -->
## Versioning, compatibility and deprecation

Adding an event type is non-breaking (endpoints subscribed to `*` must ignore unknown types). Renaming or removing an event type, or changing a field's meaning, requires a new `api_version`. Each event's first version and deprecation date is recorded in the AsyncAPI document.

<!-- section:questions -->
## Open questions

- [ ] Are institution or aggregator receivers asking for any personal data in events (for example party names for routing)? If so, offer it only behind a separate scope.
- [ ] Should invoice and payment events for case fees ([[DOM-invoices-and-vendor-bills]]) be added in Phase 5?
- [ ] Event retention for `/v1/events`: 30 days proposed.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Object-level authorization and tenant isolation

Each event belongs to one tenant from transaction context, delivered only to that tenant's endpoints, and filtered by the registering client's scopes and case visibility.

<!-- check:compatibility -->
### Contract governance and breaking changes

AsyncAPI generated from Zod; CI validates every emitted event in integration tests; schema diff on PRs fails on removed or changed fields; additive changes only within an `api_version`.

<!-- check:reliability -->
### Retry safety and consistency

Outbox after commit, stable event IDs, per-subject sequences, 30-day events list for resync.

<!-- check:privacy -->
### Personal data and residency in the contract

Payloads are thin: no personal data, document content or free text; receivers fetch through the API, where object-level checks apply. Confidential-tier events are never emitted. This keeps webhooks safe to send to tenant endpoints outside the tenant's region.

<!-- citations -->
## Citations

```json
[
  {
    "body": "AsyncAPI Initiative",
    "excerpt": "Machine-readable description of message-driven and event APIs.",
    "id": "R1",
    "ident": "AsyncAPI",
    "kind": "standard",
    "title": "AsyncAPI Specification 3.0.0",
    "url": "https://www.asyncapi.com/docs/reference/specification/v3.0.0",
    "version": "3.0.0"
  },
  {
    "body": "CNCF",
    "excerpt": "Common envelope attributes for event data (id, source, type, time, subject).",
    "id": "R2",
    "ident": "CloudEvents",
    "kind": "standard",
    "title": "CloudEvents specification",
    "url": "https://cloudevents.io/"
  },
  {
    "excerpt": "Defines webhook-id, webhook-timestamp and webhook-signature headers with an HMAC-SHA256 signature over id.timestamp.payload, and secret rotation with multiple signatures.",
    "id": "R3",
    "kind": "web",
    "publisher": "Standard Webhooks (open specification)",
    "retrieved": "2026-10-28",
    "title": "Standard Webhooks specification",
    "url": "https://github.com/standard-webhooks/standard-webhooks"
  }
]
```

<!-- end -->
