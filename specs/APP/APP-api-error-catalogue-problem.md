---
id: "APP-api-error-catalogue-problem"
title: "API error catalogue (problem types)"
parent: "APP-api-layer"
order: 4
type: "feature"
template: "api"
status: "draft"
owner: null
indicative: false
summary: "Shared RFC 9457 problem types, statuses, retryability and client guidance across all API families"
links: []
rev: 2
syncHash: "83a1d6226212bdd4"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.3.4 API error catalogue (problem types)

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Shared RFC 9457 problem types, statuses, retryability and client guidance across all API families

<!-- section:purpose -->
## Purpose, audience and surface

The shared catalogue of RFC 9457 problem types [R1] used by every API family: internal tRPC, Server Actions (as `problem` in `ActionResult`), public REST `/api/v1`, and inbound webhook responses. It fixes each type's URI, HTTP status, retryability and client guidance, so integrators and our own UI handle errors the same way everywhere. User-facing copy for each problem lives in [[APP-error-message-catalogue]].

<!-- section:resources -->
## Resources and identifiers

- Type URI: `https://developer.{platform-domain}/problems/{slug}` (placeholder until the developer portal domain is fixed); each URI resolves to a documentation page.
- `code`: a stable, upper-snake-case domain code for business-rule violations (for example `FILING_STAGE_CLOSED`), registered in [[APP-error-message-catalogue]].
- `instance`: `urn:request:{requestId}`, matching the `x-request-id` header.

<!-- section:operations -->
## Operations

| Slug | Status | Retryable | When | Client should |
|---|---|---|---|---|
| `invalid-request` | 400 | no | malformed JSON, wrong content type for body | fix the request |
| `validation-failed` | 422 | no | input fails schema; `errors[]` lists fields | show field errors |
| `idempotency-key-missing` | 400 | no | required key absent | add `Idempotency-Key` |
| `unauthenticated` | 401 | no | missing or invalid credential or session | sign in or refresh token |
| `session-expired` (internal) | 401 | no | session idle or absolute timeout | redirect to sign-in, keep draft |
| `step-up-required` | 403 | after step-up | action needs recent MFA | open `stepUpUrl`, then retry same request with same idempotency key |
| `insufficient-scope` | 403 | no | credential lacks scope for the operation | request scope from tenant admin |
| `action-not-permitted` | 403 | no | caller can see the resource but not do this action | hide or disable the action |
| `tenant-suspended` | 403 | no | tenant suspended | contact the institution |
| `not-found` | 404 | no | resource does not exist **or** caller may not see it | treat as absent |
| `method-not-allowed` | 405 | no | | |
| `version-conflict` | 412 | after reload | `If-Match` or version field stale | reload, reapply |
| `precondition-required` | 428 | no | update without `If-Match` | send `If-Match` |
| `idempotency-request-in-progress` | 409 | yes, after delay | same key still processing | retry after `Retry-After` |
| `idempotency-key-reused` | 422 | no | same key, different body | use a new key |
| `invalid-state-transition` | 409 | no | entity state does not allow the command ([[WF-entity-state-machines]]) | refresh state |
| `business-rule-violation` | 422 | no | domain rule failed; `code` says which | show message for `code` |
| `payload-too-large` | 413 | no | body or file over limit | reduce size |
| `unsupported-media-type` | 415 | no | | |
| `file-rejected` | 422 | no | malware found or file type not allowed | upload another file |
| `misdirected-region` | 421 | no | credential used against the wrong region's base URL; `region` extension | use the home-region base URL |
| `rate-limited` | 429 | yes | rate limit hit | wait `Retry-After` |
| `quota-exceeded` | 429 | no (until reset) | plan quota used up | contact tenant admin |
| `internal-error` | 500 | idempotent ops only | unexpected failure | retry with backoff if idempotent; quote `instance` |
| `dependency-unavailable` | 503 | yes | provider or downstream outage | retry after `Retry-After` |
| `timeout` | 504 | yes, with same idempotency key | outcome unknown | retry with same key |

<!-- section:schemas -->
## Request and response schemas

```ts
const Problem = z.object({
  type: z.string().url(),
  title: z.string(),                 // stable English summary per type
  status: z.number().int(),
  detail: z.string().optional(),     // safe, specific, never internal data
  instance: z.string(),              // urn:request:{requestId}
  code: z.string().regex(/^[A-Z][A-Z0-9_]+$/).optional(),
  errors: z.array(z.object({ pointer: z.string(), code: z.string(), detail: z.string().optional() })).optional(),
  region: z.enum(['in', 'sg', 'us']).optional(),
  stepUpUrl: z.string().optional(),
}).strict();
```
`Content-Type: application/problem+json` on REST. `errors[].pointer` is a JSON Pointer into the request body (RFC 6901 syntax); for query parameters, `#/query/{name}`.

<!-- section:errors -->
## Error model

This node is the error model. Rules: one type per distinct client action; `detail` never contains stack traces, SQL, hostnames, other parties' data or whether a hidden resource exists; `not-found` is used for both missing and forbidden resources with the same body and similar timing; new types are additive (non-breaking under [[APP-api-versioning-rate-limiting]] VER-3).

<!-- section:auth -->
## Authentication, scopes and permissions

Problems are returned before or after authentication checks as listed; authentication problems never reveal whether an account or tenant exists.

<!-- section:tenancy -->
## Tenancy and region routing

Problems never include tenant IDs other than the caller's. `misdirected-region` gives only the region code and base URL pattern, not whether a given tenant exists there.

<!-- section:versioning -->
## Versioning, compatibility and deprecation

The registry lives in `packages/api-core/src/problems.ts`; each type has a `since` release. Removing or changing a type's status is a breaking change.

<!-- section:examples -->
## Worked examples

```http
HTTP/1.1 422 Unprocessable Content
Content-Type: application/problem+json

{"type":"https://developer.{platform-domain}/problems/business-rule-violation",
 "title":"The request breaks a case rule",
 "status":422,
 "code":"FILING_STAGE_CLOSED",
 "detail":"Responses for this case could be filed until 5 March 2026, 17:00 Singapore time.",
 "instance":"urn:request:0192f6c4-8a1e-7c2b-9d3e-5f1a2b3c4d5e"}
```

<!-- section:questions -->
## Open questions

- [ ] Developer portal domain for type URIs (owner: product, [[DOC-api-documentation-openapi]])
- [ ] Should `detail` be localised for public API callers (via `Accept-Language`) or English only? (owner: content, [[DOC-developer-facing-api-copy]])

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Object-level authorization and tenant isolation

`not-found` covers both unknown and forbidden IDs with identical body; problems never echo other tenants' identifiers; `misdirected-region` does not confirm tenant existence.

<!-- check:security -->
### Attack surface and abuse resistance

`detail` strings are written from templates in the error catalogue, not from exception messages; a test fails if any problem body contains stack-trace patterns, SQL keywords or internal hostnames.

<!-- check:compatibility -->
### Contract governance and breaking changes

The registry is code; contract tests check every route's documented problem types against the registry; adding a type is non-breaking, changing a status or removing a type fails the OpenAPI diff.

<!-- check:consumability -->
### Developer experience and onboarding

Each type URI resolves to a documentation page with cause, example and recommended handling; SDKs expose problem types as typed errors.

<!-- citations -->
## Citations

```json
[
  {
    "body": "IETF",
    "id": "R1",
    "ident": "RFC 9457",
    "kind": "standard",
    "title": "Problem Details for HTTP APIs",
    "url": "https://datatracker.ietf.org/doc/html/rfc9457"
  }
]
```

<!-- end -->
