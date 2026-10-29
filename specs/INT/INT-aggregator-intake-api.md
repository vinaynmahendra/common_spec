---
id: "INT-aggregator-intake-api"
title: "Aggregator intake API"
parent: "INT-public-api-and-webhooks"
order: 6
type: "feature"
template: "api"
status: "draft"
owner: null
indicative: false
summary: "Contract for aggregators (e.g. NSE for SEBI matters, MSME next) to bulk-file matters and pull status for onward reporting"
links: []
rev: 2
syncHash: "738652616fa4d2db"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 9.4.6 Aggregator intake API

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Contract for aggregators (e.g. NSE for SEBI matters, MSME next) to bulk-file matters and pull status for onward reporting

<!-- section:purpose -->
## Purpose, audience and surface

Contract for **aggregators**, bodies that route matters to ODR or arbitral institutions on the platform and report onward to a regulator or ministry ([[RPT-aggregators]], [[ADR-aggregator-reporting]]). Indicative: NSE as a market infrastructure institution routing SEBI ODR matters; MSME channels next. The aggregator bulk-files matters into a specific institution tenant and pulls status for onward reporting.

**Key assumption to confirm first**: this design assumes the aggregator calls our API. If an aggregator instead requires us to pull from or push to its own interface, the same internal model is used but the transport becomes a connector in [[INT-integration-framework]] (open question 1).

Not exposed: case documents other than intake attachments, tribunal material, party contact details after intake, any tenant the aggregator is not linked to.

<!-- section:resources -->
## Resources and identifiers

| Resource | ID | Notes |
|---|---|---|
| Aggregator partner | `agg_` (platform-level registry) | e.g. one per market infrastructure institution; credentials per region |
| Tenant link | `agl_` | Consent record: tenant ↔ aggregator, allowed case types, field mapping version, start / end date |
| Batch | `bat_` | Up to 500 matters per batch |
| Matter | identified by aggregator's `aggregator_reference` (unique per aggregator and tenant) and our `case_` ID once created | |
| Status change feed | cursor | Ordered status changes for linked tenants |

Routes are under `/v1/aggregator/...`. The target tenant is selected by `tenant_link_id` in the path, which must belong to the calling aggregator.

<!-- section:operations -->
## Operations

| Method and path | Summary | Scope | Safe / idempotent / long-running |
|---|---|---|---|
| `GET /v1/aggregator/links` | List tenant links for this aggregator in this region | `aggregator:status` | safe |
| `POST /v1/aggregator/links/{link_id}/batches` | Submit batch of matters (JSON array, max 500, max 10 MB) | `aggregator:intake` | Idempotency-Key; 202 + batch resource |
| `GET /v1/aggregator/batches/{batch_id}` | Batch status and per-item results (`created`, `duplicate`, `rejected` with problem) | `aggregator:intake` | safe |
| `GET /v1/aggregator/links/{link_id}/matters/{aggregator_reference}` | Matter status, case reference, stage, key dates | `aggregator:status` | safe |
| `GET /v1/aggregator/links/{link_id}/status-changes?after={cursor}` | Ordered feed of status changes since cursor | `aggregator:status` | safe |
| `POST /v1/aggregator/links/{link_id}/matters/{aggregator_reference}/attachments` | Create upload session for an intake attachment (same mechanics as documents API) | `aggregator:intake` | Idempotency-Key |

<!-- section:schemas -->
## Request and response schemas

```ts
const AggregatorMatter = z.object({
  aggregator_reference: z.string().min(1).max(64),       // the aggregator's complaint / matter ID
  case_type: z.string().max(64),                          // must be allowed by the tenant link
  received_at_aggregator: z.string().datetime(),
  claimant: AggregatorParty, respondent: AggregatorParty, // respondent may be a regulated entity identified by code
  claim_amount: Money.optional(),
  summary: z.string().max(4000),
  fields: z.record(z.string().max(64), z.unknown()),      // mapped by the link's field-mapping version
}).strict();

const BatchCreate = z.object({ items: z.array(AggregatorMatter).min(1).max(500) }).strict();

const StatusChange = z.object({
  cursor: z.string(), aggregator_reference: z.string(), case_id: z.string(), case_reference: z.string(),
  from: z.string().nullable(), to: z.string(), occurred_at: z.string().datetime(),
  reporting_stage: z.string(),   // stage name in the aggregator's vocabulary, via the link's mapping
});
```
Our status names are mapped to the aggregator's reporting stages by configuration held with the report template ([[RPT-configurable-report-templates]], [[RPT-example]]); the actual NSE field list and stage names must come from NSE's current format and are not invented here.

<!-- section:errors -->
## Error model

RFC 9457 [R2]. Batch-level: `validation-failed` (whole batch malformed), `link-inactive` (403), `batch-too-large` (413). Item-level results inside the batch: `duplicate-aggregator-reference` (returns existing `case_id`), `case-type-not-allowed`, `field-mapping-failed` (with field paths), `respondent-unknown`. A batch is accepted if well-formed even if some items are rejected; each item has its own outcome.

<!-- section:auth -->
## Authentication, scopes and permissions

OAuth client credentials with `private_key_jwt` only (no API keys) for aggregators; each aggregator has one client per region registered by a platform admin. Scopes `aggregator:intake`, `aggregator:status`. Access to a tenant requires an active tenant link that the **tenant admin has approved** in the console; the link limits case types and the date range of status visibility.

<!-- section:tenancy -->
## Tenancy and region routing

This is the one family where a credential is not bound to a single tenant: an aggregator client is bound to one aggregator and one region, and reaches tenants only through active links. For every request the middleware resolves `link_id` → (aggregator, tenant), checks the link belongs to the calling aggregator and is active, then sets `app.tenant_id` for the transaction to the link's tenant ([[MT-prisma-client-extension-wraps]]). Each batch is processed per item inside a tenant-scoped transaction. The status-change feed is per link, so it never mixes tenants. A link in another region returns `421 wrong-region`.

<!-- section:pagination -->
## Pagination, filtering and sorting

Status-change feed: opaque cursor (link ID + monotonic change sequence), `limit` up to 1,000, ordered by sequence; retained 400 days (proposed, to cover annual reporting). Batch item results paged 500 at a time.

<!-- section:idempotency -->
## Idempotency, concurrency and long-running operations

Batch submission requires `Idempotency-Key` [R1] (72 hours). Independently, each matter is idempotent on `(aggregator_id, tenant_id, aggregator_reference)` via a unique constraint, so resubmitting a matter in a later batch returns `duplicate` with the existing case. Processing runs in a Temporal workflow `{tenantId}-agg-batch-{batchId}` on the `cases` task queue; `aggregator.batch.completed` fires at the end.

<!-- section:events -->
## Webhooks and events

Aggregators may register webhook endpoints per link for `aggregator.batch.completed` and `case.status_changed` limited to their matters; the pull feed remains the source of truth for reporting.

<!-- section:limits -->
## Rate limits and quotas

5 concurrent batches per aggregator per region, 500 items each; feed reads 120 per minute. Month-end bursts (for example thousands of MSME matters) are absorbed by queueing batches, not by raising limits.

<!-- section:versioning -->
## Versioning, compatibility and deprecation

Field mappings are versioned per link; a new aggregator format is a new mapping version, not an API change ([[ADR-aggregator-reporting]]).

<!-- section:questions -->
## Open questions

- [ ] Does NSE (and each future aggregator) call a platform API, or require us to integrate with its own interface? This decides whether this node or a connector is built.
- [ ] Obtain the current NSE field list and stage names for SEBI ODR status reporting; do not infer them.
- [ ] Which party contact data does intake carry, and under what notice to the party (DPDP)?
- [ ] Status feed retention: 400 days proposed.
- [ ] Is aggregator access to a tenant approved by the tenant admin (proposed) or set by contract with Nomology?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Object-level authorization and tenant isolation

Aggregator credentials reach tenants only through active, tenant-approved links; the link determines the tenant for each transaction; feeds and batches are per link; item processing is tenant-scoped; unique matter key includes tenant.

<!-- check:reliability -->
### Retry safety and consistency

Batch idempotency key plus per-matter unique constraint; per-item outcomes; Temporal processing with a completion event; ordered, cursor-based status feed that the aggregator can replay from any point.

<!-- check:privacy -->
### Personal data and residency in the contract

Intake carries party data the aggregator already holds; after intake the aggregator sees only status and references, not documents or contact details. Field mappings are reviewed for minimisation.

<!-- check:operability -->
### Service levels, capacity and observability

Month-end peaks are queued; metrics per aggregator and link: batch latency, item rejection rate, feed lag. An alert fires if a link's feed has not been read for 7 days during a reporting period.

<!-- citations -->
## Citations

```json
[
  {
    "body": "IETF (Internet-Draft)",
    "excerpt": "Defines an Idempotency-Key request header so that clients can safely retry non-idempotent requests such as POST.",
    "id": "R1",
    "ident": "draft-ietf-httpapi-idempotency-key-header-06",
    "kind": "standard",
    "title": "The Idempotency-Key HTTP Header Field",
    "url": "https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header-06"
  },
  {
    "body": "IETF",
    "excerpt": "Defines the application/problem+json object with type, title, status, detail and instance members.",
    "id": "R2",
    "ident": "RFC 9457",
    "kind": "standard",
    "title": "Problem Details for HTTP APIs",
    "url": "https://datatracker.ietf.org/doc/html/rfc9457"
  }
]
```

<!-- end -->
