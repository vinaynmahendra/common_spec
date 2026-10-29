---
id: "INT-public-api-cases-and-parties"
title: "Public API — Cases and parties"
parent: "INT-public-api-and-webhooks"
order: 2
type: "feature"
template: "api"
status: "draft"
owner: null
indicative: false
summary: "REST contract for creating cases, adding parties and representatives, lifecycle commands and status reads"
links: []
rev: 2
syncHash: "29fac60ddf1fe8b8"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 9.4.2 Public API — Cases and parties

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> REST contract for creating cases, adding parties and representatives, lifecycle commands and status reads

<!-- section:purpose -->
## Purpose, audience and surface

REST contract for institution systems and partners to create cases, add parties and their representatives, run lifecycle commands, and read status and history. Callers: institution case management systems (for example an arbitral institution importing filings from its own intake form), SEBI ODR institutions syncing status, partner law-firm tools. Our own UI uses tRPC ([[APP-internal-api-trpc-routers-per]]) over the same domain services and policies.

Not exposed: tribunal-only material, deliberations, conflict-check details ([[DOM-neutrals]]), internal workflow state, other parties' contact details beyond what the caller's role may see. Bulk aggregator filing has its own family ([[INT-aggregator-intake-api]]).

<!-- section:resources -->
## Resources and identifiers

```
/v1/cases/{case_id}
    /parties/{party_id}
        /representatives/{representative_id}
    /status-history
    /actions/{action}
```
| Resource | Public ID | Human reference | Tenant-supplied reference |
|---|---|---|---|
| Case | `case_` + UUIDv7 [R3] | `reference` (tenant numbering, e.g. `ARB-2026-0042`), read-only | `external_reference` (unique per tenant, ≤ 128 chars) |
| Party | `pty_` + UUIDv7 | — | `external_reference` (unique per case) |
| Representative | `rep_` + UUIDv7 | — | — |

Internal database IDs are the same UUIDs without the prefix; no sequential integer is ever exposed.

<!-- section:operations -->
## Operations

| Method and path | Summary | Scope | Personas reached (via service principal role) | Safe / idempotent / long-running |
|---|---|---|---|---|
| `POST /v1/cases` | Create case (draft or submitted) | `cases:write` | secretariat integration | Idempotency-Key required |
| `GET /v1/cases` | List cases visible to the client | `cases:read` | secretariat, counsel integration | safe |
| `POST /v1/cases/search` | Search by party email / phone / name (body, not URL) | `cases:read` | secretariat | safe (POST) |
| `GET /v1/cases/{case_id}` | Get case (optional `expand=parties`) | `cases:read` | all with case access | safe |
| `PATCH /v1/cases/{case_id}` | Update editable metadata (title, claim amount, language, seat) | `cases:write` | secretariat | If-Match required |
| `POST /v1/cases/{case_id}/actions/submit` | Submit draft (starts case workflow) | `cases:write` | secretariat, claimant counsel | Idempotency-Key; 202 if workflow start is slow |
| `POST /v1/cases/{case_id}/actions/withdraw` | Withdraw claim (reason) | `cases:write` | claimant counsel, secretariat | Idempotency-Key |
| `POST /v1/cases/{case_id}/actions/close` | Close (secretariat only) | `cases:write` | secretariat | Idempotency-Key |
| `GET /v1/cases/{case_id}/status-history` | Status events | `cases:read` | all with case access | safe |
| `POST /v1/cases/{case_id}/parties` | Add party | `parties:write` | secretariat | Idempotency-Key |
| `GET /v1/cases/{case_id}/parties` | List parties | `cases:read` | all with case access | safe |
| `GET /v1/cases/{case_id}/parties/{party_id}` | Get party | `cases:read` | all with case access (contact fields by role) | safe |
| `PATCH /v1/cases/{case_id}/parties/{party_id}` | Update party details | `parties:write` | secretariat | If-Match |
| `POST /v1/cases/{case_id}/parties/{party_id}/actions/remove` | Remove party (reason; not delete) | `parties:write` | secretariat | Idempotency-Key |
| `POST /v1/cases/{case_id}/parties/{party_id}/representatives` | Appoint representative (invites the user) | `parties:write` | secretariat, the party's counsel | Idempotency-Key |
| `GET /v1/cases/{case_id}/parties/{party_id}/representatives` | List representatives | `cases:read` | all with case access | safe |
| `POST .../representatives/{rep_id}/actions/end` | End representation | `parties:write` | secretariat, the representative | Idempotency-Key |

Allowed actions per status come from the case state machine ([[WF-entity-state-machines]]); an action not allowed in the current status returns `409 invalid-state-transition`.

<!-- section:schemas -->
## Request and response schemas

```ts
const Money = z.object({ amount_minor: z.string().regex(/^\d{1,18}$/), currency: z.string().length(3) }).strict();

const CaseCreate = z.object({
  case_type: z.string().max(64),                       // tenant-configured, e.g. 'arbitration', 'sebi_odr_conciliation'
  rule_set: z.string().max(64).optional(),             // defaults by case_type
  title: z.string().min(1).max(300),
  external_reference: z.string().max(128).optional(),
  claim_amount: Money.optional(),
  language: z.string().regex(/^[a-z]{2,3}(-[A-Z]{2})?$/).default('en'),
  seat: z.string().max(100).optional(),
  submit: z.boolean().default(false),
  parties: z.array(PartyCreate).max(50).optional(),
  custom_fields: z.record(z.string().max(64), z.unknown()).optional(), // validated against tenant metadata (PKG-metadata-management-entity)
}).strict();

const PartyCreate = z.object({
  role: z.enum(['claimant', 'respondent', 'applicant', 'other']),
  kind: z.enum(['individual', 'organisation']),
  name: z.string().min(1).max(300),
  email: z.string().email().max(254).optional(),
  phone: z.string().regex(/^\+[1-9]\d{6,14}$/).optional(),   // E.164
  address: Address.optional(),
  external_reference: z.string().max(128).optional(),
}).strict();

const Case = z.object({
  id: z.string(), reference: z.string(), external_reference: z.string().nullable(),
  case_type: z.string(), status: z.string(),            // tolerate unknown values
  title: z.string(), claim_amount: Money.nullable(), language: z.string(), seat: z.string().nullable(),
  created_at: z.string().datetime(), updated_at: z.string().datetime(),
  version: z.number().int(),                            // also returned as ETag
  parties: z.array(Party).optional(),                   // with expand=parties
});
```
Party contact fields (`email`, `phone`, `address`) are returned only to principals whose role may see them (secretariat; a party's own representatives); others receive the party without them.

<!-- section:errors -->
## Error model

All errors are RFC 9457 problem details [R1].

| Problem type | Status | When | Retryable | Client action |
|---|---|---|---|---|
| `validation-failed` | 422 | Schema or custom-field validation; `errors[]` with JSON pointers (`/parties/0/email`) | No | Fix input |
| `duplicate-external-reference` | 409 | `external_reference` already used; `existing_id` included | No | Use existing case |
| `invalid-state-transition` | 409 | Action not allowed in current status; `allowed_actions` included | No | Re-read case |
| `precondition-failed` | 412 | ETag mismatch | Yes after re-read | Re-read and retry |
| `precondition-required` | 428 | PATCH without If-Match | No | Send If-Match |
| `idempotency-key-reused` | 422 | Same key, different body hash | No | New key |
| `idempotency-request-in-progress` | 409 | Same key still processing | Yes, after 1 s | Retry |
| `not-found` | 404 | Unknown or not visible | No | — |
| `insufficient-scope` | 403 | Scope missing | No | — |
| `entitlement-limit-reached` | 403 | Plan limit for a non-protected action | No | Contact admin |
| `tenant-suspended-readonly` | 403 | Tenant suspended, non-protected write | No | — |
| `rate-limited` | 429 | Limits | Yes, `Retry-After` | Back off |

<!-- section:auth -->
## Authentication, scopes and permissions

OAuth client credentials or API key ([[INT-public-api-and-webhooks#auth]]). Scopes `cases:read`, `cases:write`, `parties:write`. The service principal has a tenant role (for example `integration_secretariat`, or a counsel-firm integration limited to cases where the firm's users are representatives); every object is then checked by the same policy functions as the UI ([[PKG-rbac-abac-case-level-party]], [[PKG-ethical-walls-conflict-based]]).

<!-- section:tenancy -->
## Tenancy and region routing

The tenant is taken only from the credential (API key or OAuth token), which is bound to one tenant and one region ([[INT-public-api-and-webhooks#auth]]). The auth middleware opens the request transaction and sets `app.tenant_id` through the Prisma extension ([[MT-prisma-client-extension-wraps]]); forced RLS ([[MT-rls-enabled-and-forced-on]]) is the final layer under the object-level policy checks. No path, query or body field can select a tenant; `tenant_id` is not accepted in any write schema (`additionalProperties: false`). A credential used against another region's base URL gets `421` problem `wrong-region`. A suspended tenant gets read access and the protected due-process actions only; other writes return `403` problem `tenant-suspended-readonly`. Unknown and forbidden IDs both return the same `404 not-found`.

<!-- section:pagination -->
## Pagination, filtering and sorting

Cursor-based: `limit` (default 50, max 200), `starting_after` (opaque cursor encoding the last `(updated_at, id)`; bound to tenant and client, signed). Stable order `updated_at DESC, id DESC`. Filters (allow-listed): `status` (multi), `case_type`, `external_reference` (exact), `created_after`, `updated_after`. Indexes: `(tenant_id, updated_at DESC, id DESC)`, `(tenant_id, status, updated_at DESC)`, unique `(tenant_id, external_reference)`. No free-text filters in GET; search uses `POST /v1/cases/search` backed by the tenant-scoped search index ([[PKG-search]]).

<!-- section:idempotency -->
## Idempotency, concurrency and long-running operations

`Idempotency-Key` [R2] required on every POST that creates or acts; scope `(tenant, client, key)`; retained 72 hours; body SHA-256 compared; replay returns the original status and body. The key record is written in the same transaction as the business change ([[INT-api-platform-tables]]). Concurrency: `ETag: "v{version}"` on reads; PATCH requires `If-Match`. Submission that starts a Temporal workflow returns `200` when the workflow start is acknowledged within 2 s, else `202` with `Location: /v1/operations/{op_id}`.

<!-- section:events -->
## Webhooks and events

Emits `case.created`, `case.status_changed`, `case.party_added`, `case.party_removed`, `case.representative_added`, `case.representative_removed`, `case.tribunal_constituted`, `case.award_issued` ([[INT-webhook-event-catalogue]]).

<!-- section:limits -->
## Rate limits and quotas

Standard family limits ([[INT-public-api-and-webhooks#limits]]). `POST /v1/cases/search` counts as expensive (10 per minute). Maximum 50 parties per create request; body limit 256 KB.

<!-- section:versioning -->
## Versioning, compatibility and deprecation

Path major `/v1`; additive changes allowed (new optional fields, new statuses, new actions). Clients must tolerate unknown `status` values. Tenant-specific fields go in `custom_fields`, validated by tenant metadata, so the contract does not fork per jurisdiction.

<!-- section:examples -->
## Worked examples

**Create and submit a case**
```http
POST /v1/cases
Authorization: Bearer eyJ...
Idempotency-Key: 6f1c2d0e-1b8f-4b7e-9a51-7cde0a0e6b11
Content-Type: application/json

{ "case_type": "arbitration", "title": "Alpha Pte Ltd v Beta Ltd", "external_reference": "INTAKE-88213",
  "claim_amount": { "amount_minor": "250000000", "currency": "SGD" }, "submit": true,
  "parties": [ { "role": "claimant", "kind": "organisation", "name": "Alpha Pte Ltd", "email": "legal@alpha.example" },
               { "role": "respondent", "kind": "organisation", "name": "Beta Ltd" } ] }
```
```http
HTTP/1.1 201 Created
ETag: "v1"
{ "id": "case_01JBD3...", "reference": "ARB-2026-0042", "status": "submitted", "version": 1, ... }
```
**Retry after timeout**: the client times out and resends the same request with the same key; it receives the same `201` body. Sending a different body with that key returns `422 idempotency-key-reused`.

**Concurrent edit**: PATCH with `If-Match: "v1"` after the secretariat edited the case in the UI returns `412 precondition-failed`; client GETs (`ETag: "v2"`) and retries.

<!-- section:questions -->
## Open questions

- [ ] Which case types and actions are exposed to external clients per tenant (configurable allow-list proposed)?
- [ ] Do counsel-firm integrations exist in Phase 5, or only institution integrations?
- [ ] Should party contact searches be allowed at all through the API (privacy review)?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Object-level authorization and tenant isolation

Tenant from credential only; same policy functions as the UI for every ID in path, body and `expand`; RLS as the final layer; same 404 for unknown and forbidden; cursors signed and bound to tenant and client; `.strict()` schemas prevent setting `tenant_id`, `status` or `owner` directly (status changes only via actions) [R4].

<!-- check:security -->
### Attack surface and abuse resistance

Body limit 256 KB, arrays max 50, string limits in schemas; filters and sorts are allow-listed; search via POST body; contact fields only to roles allowed to see them; problem `detail` strings never include other parties' data or internals. Reviewed against OWASP API Top 10 [R4].

<!-- check:compatibility -->
### Contract governance and breaking changes

OpenAPI generated from these Zod schemas; diff on every PR; unknown enum tolerance documented; tenant variation through `custom_fields` validated by metadata, not by forking the contract.

<!-- check:reliability -->
### Retry safety and consistency

Idempotency keys in the same transaction as the change, body-hash comparison, ETag / If-Match for edits, forward-only actions through the state machine, outbox events after commit, 202 + operation for slow workflow starts.

<!-- check:privacy -->
### Personal data and residency in the contract

Contact fields are role-gated; searches by email or phone use POST bodies so they stay out of URLs and logs; request bodies are masked in logs. Erased parties (after a lawful erasure that does not conflict with the legal record) are returned with redacted fields.

<!-- check:audit -->
### Attribution and legal evidence

Every write records request ID, API client, service principal role, and payload hash in the audit trail; reads of party contact details are audited.

<!-- citations -->
## Citations

```json
[
  {
    "body": "IETF",
    "excerpt": "Defines the application/problem+json object with type, title, status, detail and instance members.",
    "id": "R1",
    "ident": "RFC 9457",
    "kind": "standard",
    "title": "Problem Details for HTTP APIs",
    "url": "https://datatracker.ietf.org/doc/html/rfc9457"
  },
  {
    "body": "IETF (Internet-Draft)",
    "excerpt": "Defines an Idempotency-Key request header so that clients can safely retry non-idempotent requests such as POST.",
    "id": "R2",
    "ident": "draft-ietf-httpapi-idempotency-key-header-06",
    "kind": "standard",
    "title": "The Idempotency-Key HTTP Header Field",
    "url": "https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header-06"
  },
  {
    "body": "IETF",
    "excerpt": "Defines UUID version 7, a time-ordered UUID suitable for database keys.",
    "id": "R3",
    "ident": "RFC 9562",
    "kind": "standard",
    "title": "Universally Unique IDentifiers (UUIDs)",
    "url": "https://datatracker.ietf.org/doc/rfc9562/"
  },
  {
    "body": "OWASP",
    "excerpt": "Top API risks, led by Broken Object Level Authorization (API1) and Broken Authentication (API2).",
    "id": "R4",
    "ident": "OWASP API Security Top 10",
    "kind": "standard",
    "title": "OWASP API Security Top 10 (2023)",
    "url": "https://owasp.org/API-Security/editions/2023/en/0x11-t10/",
    "version": "2023"
  }
]
```

<!-- end -->
