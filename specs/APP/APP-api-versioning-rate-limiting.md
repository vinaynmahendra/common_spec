---
id: "APP-api-versioning-rate-limiting"
title: "API versioning, rate limiting, idempotency keys"
parent: "APP-api-layer"
order: 2
type: "feature"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 3
syncHash: "1325fa7d0f8f5299"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 2.3.2 API versioning, rate limiting, idempotency keys

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

Repo-wide rules for versioning the public REST API, limiting request rates and quotas, and making state-changing calls safe to retry with idempotency keys. Applies to `/api/v1/*` and, where stated, to internal tRPC and Server Actions. Resource-specific details stay in each public API node under [[INT-public-api-and-webhooks]].

<!-- section:rules -->
## Rules

**Versioning**
1. **VER-1** The public REST API has a major version in the path (`/api/v1/`). A new major version is created only for breaking changes.
2. **VER-2** Breaking changes are: removing or renaming a field, operation or enum value; changing a type, format or meaning; making an optional input required; changing default sort, pagination or status codes; tightening validation on existing inputs.
3. **VER-3** Non-breaking changes allowed within `v1`: new operations, new optional inputs, new response fields, new enum values in responses (clients must tolerate unknown values; documented), new problem types.
4. **VER-4** Deprecation is announced with the `Deprecation` header [R1] and a `Sunset` header [R2] on affected responses, in the changelog and by email to tenant admins and API client owners. Minimum notice before removal: 12 months for a major version, 6 months for a single operation or field (proposed; client contracts may require longer).

**Rate limits and quotas**
5. **RL-1** Limits are enforced per credential, per tenant and per operation class using token buckets in regional Redis:

   | Class | Examples | Per credential | Per tenant |
   |---|---|---|---|
   | read | GET cases, documents list | 20 req/s, burst 40 | 100 req/s |
   | write | create case, add party | 5 req/s, burst 10 | 30 req/s |
   | bulk | aggregator batch intake | 1 req/s, 2 concurrent | 4 concurrent |
   | expensive | exports, bundle generation, search | 10 per minute | 60 per minute |
   | auth-sensitive (internal) | OTP send, magic link, invitation | 5 per hour per address | 1,000 per hour |
   Values are proposed defaults; plan entitlements may raise them ([[BIL-plans-entitlements-and-usage]]).
6. **RL-2** Responses carry `RateLimit-Policy` and `RateLimit` headers following the IETF draft [R3]; a limited request returns `429` with `Retry-After` and problem type `rate-limited`.
7. **RL-3** Monthly quotas (cases created, storage, AI tokens) come from entitlements; exceeding returns `quota-exceeded` (not retried automatically).

**Idempotency**
8. **IDEM-1** `POST` operations that create records or have legal or financial effect require an `Idempotency-Key` header [R4] (public REST) or `idempotencyKey` input (internal); requests without one get `idempotency-key-missing`.
9. **IDEM-2** Keys are scoped to tenant and credential (or user), stored in `idempotency_keys` ([[INT-api-platform-tables]]) with a SHA-256 hash of the canonical request body, in the **same database transaction** as the business change, and kept for 24 hours.
10. **IDEM-3** Replay with the same key and same body returns the stored status and body; same key with a different body returns `422 idempotency-key-reused`; a replay while the first request is still running returns `409 idempotency-request-in-progress`.
11. **IDEM-4** Updates use optimistic concurrency: `ETag` / `If-Match` on public REST (`412 version-conflict` on mismatch, `428 precondition-required` if missing); version fields internally.

<!-- section:rationale -->
## Rationale

- Path major versions are the simplest for institution and aggregator developers to understand and route; date-based versions add little for our release cadence.
- Storing the idempotency record in the same transaction as the change (IDEM-2) prevents the crash window where a change commits but the key does not, which would let a retry file twice.
- Separate per-tenant buckets stop one aggregator's month-end bulk filing from starving other tenants' integrations.

<!-- section:tooling -->
## Tooling and configuration

`@nomology/api-core` middleware: `rateLimit(class)`, `idempotent()`, `requireIfMatch()`; Redis Lua scripts for atomic token buckets; OpenAPI diff in CI (classifies VER-2 vs VER-3 changes); changelog generated from OpenAPI diffs.

<!-- section:enforcement -->
## Enforcement

| Rule | Enforcement |
|---|---|
| VER-1 to VER-3 | OpenAPI diff on every PR touching `/api/v1`; breaking change fails the build unless the PR targets a new major version |
| VER-4 | Release checklist; contract test that deprecated operations return both headers |
| RL-1, RL-2 | Middleware required by `@nomology/rest` route builder (cannot define a route without a class); load test verifies 429 behaviour |
| IDEM-1 to IDEM-3 | Route builder flag `effect: 'legal' | 'financial' | 'create'` makes the middleware mandatory; integration tests for replay, body mismatch and concurrency |
| IDEM-4 | Builder requires `If-Match` on PATCH/PUT for versioned resources |

<!-- section:examples -->
## Examples

```http
POST /api/v1/cases HTTP/1.1
Authorization: Bearer eyJ…
Idempotency-Key: 0192f6c4-8a1e-7c2b-9d3e-5f1a2b3c4d5e
Content-Type: application/json

{"caseType":"sebi-odr","claimant":{…},"respondent":{…}}
```
First call: `201 Created`, `Location: /api/v1/cases/c_01J…`. Network drops; the aggregator retries with the same key and body: `201 Created` with the same body and `Idempotent-Replayed: true` header. A retry with the same key but a different respondent: `422` with type `…/problems/idempotency-key-reused`.

<!-- section:exceptions -->
## Exceptions

A tenant may get higher limits through plan entitlements or a time-limited override set in the platform console (`/platform/tenants/[tenantId]/flags`, [[APP-platform-admin-and-support]]) with reason and expiry. IDEM-1 and IDEM-2 are non-waivable for legal and financial effects.

<!-- section:questions -->
## Open questions

- [ ] Confirm deprecation notice periods against client contracts (HKIAC CMP, MII integrations) (owner: legal and product)
- [ ] Should the `RateLimit` headers follow the current IETF draft names, given the draft may change? (owner: platform architecture)
- [ ] Rate-limit numbers per class need validation by load test and by aggregator expectations ([[INT-aggregator-intake-api]])

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Versioning is enforced by the OpenAPI diff in CI; rate limits and idempotency are enforced by middleware that the route builder makes mandatory based on the operation's declared class and effect.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

Per-tenant rate-limit buckets and idempotency key scoping by tenant and credential prevent one tenant's traffic or keys from affecting another; idempotency records live in the tenant's regional database under RLS.

<!-- check:compliance -->
### Compliance evidence

Idempotency with request hashes and stored outcomes provides evidence that each legal filing was received once, supporting audit and dispute about receipt times.

<!-- check:measurement -->
### Adoption measurement

Dashboards: 429 rate per tenant and class, idempotent replay rate, key-reuse conflicts, deprecated-operation calls per client (used to contact clients before sunset).

<!-- citations -->
## Citations

```json
[
  {
    "body": "IETF",
    "id": "R1",
    "ident": "RFC 9745",
    "kind": "standard",
    "title": "The Deprecation HTTP Response Header Field",
    "url": "https://www.rfc-editor.org/rfc/rfc9745.html"
  },
  {
    "body": "IETF",
    "id": "R2",
    "ident": "RFC 8594",
    "kind": "standard",
    "title": "The Sunset HTTP Header Field",
    "url": "https://datatracker.ietf.org/doc/html/rfc8594"
  },
  {
    "body": "IETF HTTPAPI WG",
    "id": "R3",
    "ident": "draft-ietf-httpapi-ratelimit-headers",
    "kind": "standard",
    "title": "RateLimit header fields for HTTP (Internet-Draft)",
    "url": "https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-ratelimit-headers"
  },
  {
    "body": "IETF HTTPAPI WG",
    "id": "R4",
    "ident": "draft-ietf-httpapi-idempotency-key-header-06",
    "kind": "standard",
    "title": "The Idempotency-Key HTTP Header Field (Internet-Draft)",
    "url": "https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header-06"
  }
]
```

<!-- end -->
