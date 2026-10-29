---
id: "APP-webhooks-outbound"
title: "Outbound webhooks"
parent: "INT-public-api-and-webhooks"
order: 1
type: "feature"
template: "api"
status: "draft"
owner: null
indicative: false
summary: "Signed event delivery to tenant endpoints and its administration: event subscriptions with filters, per-endpoint secrets and rotation, configurable retries, pause and resume, delivery log, single and bulk replay with approval"
links: []
rev: 4
syncHash: "c5e139ebab9d2aac"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 9.4.1 Outbound webhooks

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Signed event delivery to tenant endpoints and its administration: event subscriptions with filters, per-endpoint secrets and rotation, configurable retries, pause and resume, delivery log, single and bulk replay with approval

<!-- section:purpose -->
## Purpose, audience and surface

Delivers platform events to HTTPS endpoints registered by a tenant, so institution systems, aggregators and partners learn about changes without polling. Callers: tenant systems (receivers). Endpoints are managed through [[INT-tenant-admin-api]] (`/admin/v1/webhook-endpoints`, scopes `admin.integrations:read` and `admin.integrations:write`) or the tenant admin console. This node covers registration rules, event subscriptions, the delivery pipeline, signing and secret rotation, retries, ordering, replay, the delivery log and the **administration** of all of these. Event types and payloads are in [[INT-webhook-event-catalogue]]; settings in [[PKG-settings-integrations]] group H.

Not exposed: events about other tenants, internal-only events (Temporal workflow internals, audit events), document content (events carry IDs and links to the API).

**Administration** (pattern borrowed from: event destination management with per-endpoint API version and event-type selection, a delivery list with attempts, manual retry and querying missed events, in Stripe [R4])

| Console page | What the admin does | Permission (role keys) |
|---|---|---|
| `/admin/integrations/webhooks` | List endpoints with status, failure rate, last success, subscribed event count; create endpoint | `webhook.endpoint:read` (`integration_admin`, `auditor`) |
| `/admin/integrations/webhooks/new` | URL, description, API version, event types (catalogue browser grouped by domain with payload examples), unit or case-type filter; secret shown once | `webhook.endpoint:create` (`integration_admin`) |
| `/admin/integrations/webhooks/[endpointId]` | Edit subscriptions, pause / resume, rotate secret, send test event, delete | `webhook.endpoint:update`, `webhook.endpoint:update`, `webhook.endpoint:delete` |
| `/admin/integrations/webhooks/[endpointId]/deliveries` | Filter by status, event type, date; open attempts with response code, latency and 1 KB response excerpt; replay one delivery | `webhook.delivery:read`, `webhook.delivery:update` |
| `/admin/integrations/webhooks/[endpointId]/replay` | Bulk replay by time range and event types; preview count; above `integration.webhooks.bulk_replay_approval_threshold` events needs a second approver | `webhook.delivery:update`, approval `webhook.delivery:approve` |
| `/admin/integrations/events` | Search the tenant's events (30 days) | `webhook.event:list` |
| `/platform/integrations/webhooks` | Per-region relay lag, deliveries by outcome, endpoints auto-disabled, abusive endpoints; no payloads | `platform_admin`, `platform_support` |

Alert recipients for failures and auto-disable come from `integration.webhooks.alert_recipients`; alerts are sent by [[PKG-notifications]] as `transactional` messages to admins.

<!-- section:resources -->
## Resources and identifiers

| Resource | ID | Notes |
|---|---|---|
| Webhook endpoint | `whe_` + UUIDv7 | URL, event type filter, API version, status |
| Endpoint secret | `whsec_` + 32 bytes base64 | Shown once at creation and rotation |
| Event | `evt_` + UUIDv7 | Same ID across all endpoints and retries |
| Delivery | `whd_` + UUIDv7 | One per (endpoint, event) |
| Delivery attempt | `wha_` + UUIDv7 | Each HTTP attempt |

URLs: `/v1/webhook-endpoints`, `/v1/webhook-endpoints/{endpoint_id}/deliveries`, `/v1/events`. Storage in [[INT-api-platform-tables]].

<!-- section:operations -->
## Operations

| Method and path | Summary | Scope | Safe / idempotent |
|---|---|---|---|
| `POST /admin/v1/webhook-endpoints` | Register endpoint; returns secret once | `admin.integrations:write` | Idempotency-Key |
| `GET /admin/v1/webhook-endpoints` | List endpoints | `admin.integrations:read` | safe |
| `GET /admin/v1/webhook-endpoints/{id}` | Get endpoint | `admin.integrations:read` | safe |
| `PATCH /admin/v1/webhook-endpoints/{id}` | Change event types, filters, description, API version | `admin.integrations:write` | If-Match |
| `POST /admin/v1/webhook-endpoints/{id}/pause` | Pause deliveries; events are queued (not dropped) up to the retry window | `admin.integrations:write` | idempotent |
| `POST /admin/v1/webhook-endpoints/{id}/resume` | Resume; queued events delivered in order per subject | `admin.integrations:write` | idempotent |
| `DELETE /admin/v1/webhook-endpoints/{id}` | Delete endpoint; pending deliveries dropped | `admin.integrations:write` | idempotent |
| `POST /admin/v1/webhook-endpoints/{id}/rotate-secret` | New secret; old one valid for `integration.webhooks.secret_rotation_overlap_hours` (default 24 h) | `admin.integrations:write` | Idempotency-Key |
| `POST /admin/v1/webhook-endpoints/{id}/expire-old-secret` | End the overlap early (for example after a leak) | `admin.integrations:write` | idempotent |
| `POST /admin/v1/webhook-endpoints/{id}/test` | Send `webhook.test` event | `admin.integrations:write` | not idempotent |
| `GET /admin/v1/webhook-endpoints/{id}/deliveries` | Delivery log (status, attempts, last response code) | `admin.integrations:read` | safe |
| `GET /admin/v1/webhook-endpoints/{id}/deliveries/{delivery_id}/attempts` | Attempts with timing and response excerpt | `admin.integrations:read` | safe |
| `POST /admin/v1/webhook-endpoints/{id}/deliveries/{delivery_id}/replay` | Redeliver one event (same event ID) | `admin.integrations:write` | Idempotency-Key |
| `POST /admin/v1/webhook-endpoints/{id}/replay` | Redeliver events since a timestamp (≤ 30 days), optional event types; long-running | `admin.integrations:write` | 202 + operation; approval above threshold |
| `GET /admin/v1/operations/{operation_id}` | Status of a bulk replay | `admin.integrations:read` | safe |
| `GET /v1/event-types` | Event catalogue for the tenant's API version | `admin.integrations:read` | safe |
| `GET /v1/events` | List events for the tenant (30 days) for resync | `events:read` | safe |
| `GET /v1/events/{event_id}` | Get one event | `events:read` | safe |

Personas: tenant admins via console (same operations through [[INT-tenant-admin-api]]); API clients with `admin.integrations:write`. Bulk replay above the approval threshold returns `202` with `status: awaiting_approval`; an approver in the console releases it. The replay itself runs as Temporal workflow `WebhookReplayWorkflow` (ID `whreplay-{endpointId}-{operationId}`) on task queue `integrations-{region}`, which pages through events and enqueues `webhook-deliver` jobs at no more than 20% of the endpoint's concurrency so live traffic keeps flowing.

<!-- section:schemas -->
## Request and response schemas

```ts
const WebhookEndpointCreate = z.object({
  url: z.string().url().max(2048).refine(u => u.startsWith('https://')),
  description: z.string().max(200).optional(),
  event_types: z.array(z.string().regex(/^[a-z_]+(\.[a-z_]+)+$/)).min(1).max(50), // or ['*']
  filters: z.object({
    unit_ids: z.array(z.string()).max(50).optional(),
    case_type_keys: z.array(z.string()).max(50).optional(),
  }).strict().optional(),
  api_version: z.literal('2026-10-01').optional(),       // defaults to integration.api.pinned_version
}).strict();

const WebhookEndpoint = WebhookEndpointCreate.extend({
  id: z.string(),
  status: z.enum(['active', 'paused_by_tenant', 'disabled_by_tenant', 'disabled_failing']),
  disabled_reason: z.string().nullable(),
  failing_since: z.string().datetime().nullable(),
  secret_rotation: z.object({ old_secret_expires_at: z.string().datetime() }).nullable(),
  created_at: z.string().datetime(),
  secret: z.string().optional(),                          // only in create / rotate responses
});
```
Delivery request (what the receiver gets):
```
POST {endpoint url}
Content-Type: application/json
webhook-id: evt_01JBC...
webhook-timestamp: 1793180400
webhook-signature: v1,K5o0Q... [v1,old... during rotation]
User-Agent: NomologyWebhooks/1.0 (+https://<platform-domain>/docs/webhooks)

{ ...event envelope from INT-webhook-event-catalogue... }
```
Storage: `webhook_endpoint` gains `filters jsonb`, status value `paused_by_tenant` and `paused_at` ([[INT-api-platform-tables]]).

<!-- section:errors -->
## Error model

| Problem type | Status | When | Retryable |
|---|---|---|---|
| `validation-failed` | 422 | Bad URL, non-HTTPS, unknown event type | No |
| `webhook-url-not-allowed` | 422 | URL resolves to private, loopback, link-local or metadata address, or uses a non-443 port without approval | No |
| `webhook-endpoint-limit` | 409 | More than 10 endpoints per tenant (default) | No |
| `insufficient-scope` | 403 | Missing `webhooks:manage` | No |
| `not-found` | 404 | Unknown or other tenant's endpoint / delivery | No |
| `precondition-failed` | 412 | ETag mismatch on PATCH | Re-read and retry |
| `replay-window-exceeded` | 422 | Replay older than 30 days | No |

<!-- section:auth -->
## Authentication, scopes and permissions

Management operations: `webhooks:manage`. Deliveries are authenticated to the receiver by signature using the Standard Webhooks scheme [R1]: `HMAC-SHA256(secret, "{webhook-id}.{webhook-timestamp}.{raw body}")`, base64, prefixed `v1,`. Receivers must verify the signature over the raw body, reject timestamps more than 5 minutes from their clock, and de-duplicate on `webhook-id` [R2]. Secrets are per endpoint, stored envelope-encrypted with the tenant's data key ([[PKG-encryption-utilities-key]]); rotation sends both signatures for 24 hours.

<!-- section:tenancy -->
## Tenancy and region routing

The tenant is taken only from the credential (API key or OAuth token), which is bound to one tenant and one region ([[INT-public-api-and-webhooks#auth]]). The auth middleware opens the request transaction and sets `app.tenant_id` through the Prisma extension ([[MT-prisma-client-extension-wraps]]); forced RLS ([[MT-rls-enabled-and-forced-on]]) is the final layer under the object-level policy checks. No path, query or body field can select a tenant; `tenant_id` is not accepted in any write schema (`additionalProperties: false`). A credential used against another region's base URL gets `421` problem `wrong-region`. A suspended tenant gets read access and the protected due-process actions only; other writes return `403` problem `tenant-suspended-readonly`. Unknown and forbidden IDs both return the same `404 not-found`.

Delivery: the relay reads outbox rows per tenant (tenant context set per batch) and creates deliveries only for endpoints of the same tenant; `webhook_delivery` has a composite FK `(tenant_id, endpoint_id)` and `(tenant_id, event_id)`, so a delivery cannot join an event and an endpoint of different tenants. Re-registering an endpoint URL creates a new endpoint ID; old pending deliveries are not moved to it.

<!-- section:pagination -->
## Pagination, filtering and sorting

Cursor pagination on deliveries and events: `?limit=50` (max 200) `&starting_after={id}`; order by ID (UUIDv7, time-ordered). Filters: deliveries by `status`, `event_type`, `created_after`; events by `type`, `subject_id`, `after` (timestamp). Index `(tenant_id, endpoint_id, created_at DESC)` and `(tenant_id, occurred_at)`.

<!-- section:idempotency -->
## Idempotency, concurrency and long-running operations

Create, rotate and replay accept `Idempotency-Key` (72-hour retention, per [[APP-api-versioning-rate-limiting]]). Delivery pipeline: the outbox row is written in the same transaction as the state change; the relay (BullMQ repeatable job `webhook-relay:{region}` every second, plus a Postgres `LISTEN` wake-up) claims rows with `FOR UPDATE SKIP LOCKED`, inserts `webhook_delivery` rows with `UNIQUE(endpoint_id, event_id)` and enqueues `webhook-deliver` jobs with `jobId = delivery id`. Bulk replay is a long-running operation (`202` with `operation_id`).

<!-- section:events -->
## Webhooks and events

**Subscriptions**: an endpoint subscribes to explicit event types or `*` (all types allowed by `integration.webhooks.allowed_event_types`). Optional filters: `unit_ids`, `case_type_keys`. Filters narrow, never widen, what the tenant may receive; a filter on a unit the creator cannot administer is rejected.

**Delivery guarantees**
- At least once. Receivers must de-duplicate on `webhook-id` (the event ID).
- No global ordering. Per subject (for example one case), events carry `sequence` (monotonic per subject); the worker delivers one event at a time per (endpoint, subject) so in normal operation they arrive in order, but after retries a later event may arrive before an earlier one, and receivers should use `sequence` or re-fetch the resource.
- Success = any 2xx within 10 seconds. Redirects are not followed (treated as failure).

**Retry schedule** (from first attempt): 1 min, 5 min, 30 min, 2 h, 6 h, 12 h, 24 h, then every 24 h until the retry window ends (`integration.webhooks.retry_window_hours`, default 72, bounds 24–168); then delivery status `dead`. The schedule applies to deliveries created after a change.

**Endpoint health**: if every delivery to an endpoint has failed for `integration.webhooks.auto_disable_after_hours` (default 72, never less than the retry window), it moves to `disabled_failing`; alert recipients get a message after `integration.webhooks.failure_alert_after_hours` (default 24) of failure and at disablement. A paused endpoint (`paused_by_tenant`) keeps its queue; a disabled one does not receive events generated while disabled. Re-enabling does not resend dead deliveries automatically; the admin may run a bulk replay.

**Signing and rotation**: Standard Webhooks signature [R1]; during rotation both signatures are sent for the overlap period; `expire-old-secret` ends the overlap immediately.

**SSRF controls**: URL host is resolved at registration and **before every delivery**; private, loopback, link-local, CGNAT and cloud metadata ranges are refused; only port 443 unless `integration.webhooks.allow_non_443_ports` is approved; delivery runs from a dedicated egress with no route to internal networks [R2]. Per-region egress IP ranges are published for allow-listing.

AsyncAPI 3.0 document [R3]: `packages/api-contracts/asyncapi/webhooks.v1.yaml`, generated from the same Zod event schemas.

<!-- section:limits -->
## Rate limits and quotas

Max endpoints per tenant `integration.webhooks.max_endpoints` (default 10, plan ceiling 50); max 50 event types per endpoint (or `*`); max payload 256 KB per event (events are thin; `integration.webhooks.payload_mode` is locked to `thin`); per-endpoint concurrency 10 (across subjects); per-tenant delivery rate 50 per second, excess queued; bulk replay at most one running per endpoint and 100,000 events per operation; delivery log kept `integration.webhooks.delivery_log_retention_days` (default 30). Management API under normal write limits.

<!-- section:versioning -->
## Versioning, compatibility and deprecation

Each endpoint pins an `api_version` (date-named, for example `2026-10-01`); payload shape follows that version. New event types and new optional fields are additive. Removing or changing a field needs a new version; old versions are kept for at least 12 months after deprecation notice.

<!-- section:examples -->
## Worked examples

**Receiver verification (TypeScript)**
```ts
import { createHmac, timingSafeEqual } from 'node:crypto';
export function verify(raw: Buffer, h: Headers, secretB64: string) {
  const id = h.get('webhook-id')!, ts = h.get('webhook-timestamp')!;
  if (Math.abs(Date.now() / 1000 - Number(ts)) > 300) throw new Error('stale');
  const key = Buffer.from(secretB64.replace(/^whsec_/, ''), 'base64');
  const expected = createHmac('sha256', key).update(`${id}.${ts}.`).update(raw).digest('base64');
  const ok = (h.get('webhook-signature') ?? '').split(' ').some(s => {
    const [v, sig] = s.split(','); return v === 'v1' && sig.length === expected.length &&
      timingSafeEqual(Buffer.from(sig), Buffer.from(expected));
  });
  if (!ok) throw new Error('bad signature');
}
```
**Failure and recovery**: the receiver is down for 6 hours. Deliveries retry at 1 m, 5 m, 30 m, 2 h, 6 h; the 6-hour attempt succeeds. Two `case.status_changed` events for the same case arrive with `sequence` 14 then 13; the receiver ignores 13 because it already applied 14.

<!-- section:questions -->
## Open questions

- [ ] Retry window: 72 hours default with a 168-hour maximum for court programmes (proposed in [[PKG-settings-integrations]]); confirm with institutions that have weekend maintenance windows.
- [ ] Do any tenants need mTLS for deliveries? Egress IP ranges per region are published (decided).
- [ ] Should payload "fat" mode (including changed fields with personal data) ever be offered? Decided: never in v1 (setting locked to `thin`).
- [ ] Should paused endpoints have a maximum pause (for example 7 days) after which they become disabled? (Product)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Object-level authorization and tenant isolation

Deliveries are created only for endpoints of the event's tenant, enforced by composite foreign keys including `tenant_id` and by RLS on all webhook tables; the relay sets tenant context per batch. Endpoint and delivery IDs from another tenant return 404. Re-registration creates a new endpoint, so retries never move to a different tenant's URL.

<!-- check:security -->
### Attack surface and abuse resistance

HTTPS only, SSRF checks at registration and before each delivery with re-resolution, dedicated egress without internal routes, no redirects, port 443 by default [R2]. Per-endpoint HMAC secrets envelope-encrypted, shown once, rotated with configurable dual signing and early expiry after a leak [R1]. Payloads are thin (IDs and changed non-personal fields), locked at platform. Response bodies from receivers are stored only as a 1 KB excerpt for the log retention period. Bulk replays above a threshold need a second approver.

<!-- check:reliability -->
### Retry safety and consistency

Transactional outbox written with the state change; relay claims with `SKIP LOCKED`; `UNIQUE(endpoint_id, event_id)` prevents duplicate deliveries; event ID stays the same across retries and replays, so receivers can de-duplicate; per-subject sequence numbers handle reordering; `/v1/events` allows resync for 30 days.

<!-- check:operability -->
### Service levels, capacity and observability

SLO (proposed): 99.9% of events delivered to healthy endpoints within 60 seconds of commit. Metrics: outbox lag, deliveries by outcome, attempts per delivery, endpoint failure rate, paused and disabled endpoints, replay throughput; alerts on relay lag over 60 seconds. Tenant admins see per-endpoint health and are alerted per their settings; platform staff see per-region health without payloads.

<!-- check:consumability -->
### Developer experience and onboarding

Verification snippets in four languages, a test event operation, a delivery log with response codes, sandbox delivery to any HTTPS endpoint, and simulated duplicates through the sandbox header.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Defines webhook-id, webhook-timestamp and webhook-signature headers with an HMAC-SHA256 signature over id.timestamp.payload, and secret rotation with multiple signatures.",
    "id": "R1",
    "kind": "web",
    "publisher": "Standard Webhooks (open specification)",
    "retrieved": "2026-10-28",
    "title": "Standard Webhooks specification",
    "url": "https://github.com/standard-webhooks/standard-webhooks"
  },
  {
    "body": "OWASP",
    "excerpt": "Guidance on signing webhook payloads, timestamp checks against replay, and SSRF protection when delivering to user-supplied URLs.",
    "id": "R2",
    "kind": "standard",
    "title": "OWASP Webhook Security Cheat Sheet",
    "url": "https://cheatsheetseries.owasp.org/cheatsheets/Webhook_Security_Cheat_Sheet.html"
  },
  {
    "body": "AsyncAPI Initiative",
    "excerpt": "Machine-readable description of message-driven and event APIs.",
    "id": "R3",
    "ident": "AsyncAPI",
    "kind": "standard",
    "title": "AsyncAPI Specification 3.0.0",
    "url": "https://www.asyncapi.com/docs/reference/specification/v3.0.0",
    "version": "3.0.0"
  },
  {
    "excerpt": "Endpoints choose an API version and event types; deliveries are listed with attempts; live-mode retries continue for up to 3 days with exponential backoff; individual events can be retried manually; disabled destinations do not receive events generated while disabled.",
    "id": "R4",
    "kind": "vendor",
    "publisher": "Stripe",
    "retrieved": "2026-10-28",
    "title": "Manage event destinations",
    "url": "https://docs.stripe.com/workbench/event-destinations"
  }
]
```

<!-- end -->
