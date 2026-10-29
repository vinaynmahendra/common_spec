---
id: "APP-internal-api-trpc-routers-per"
title: "Internal API — tRPC routers per persona"
parent: "APP-route-handlers-trpc-for-internal"
order: 1
type: "requirement"
template: "api"
status: "draft"
owner: null
indicative: false
summary: "Procedure contracts for party/counsel, neutral, secretariat, transcriber and admin route groups"
links: []
rev: 2
syncHash: "531b83b4b45445f5"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.3.1.1 Internal API — tRPC routers per persona

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Procedure contracts for party/counsel, neutral, secretariat, transcriber and admin route groups

<!-- section:purpose -->
## Purpose, audience and surface

Contract for the internal tRPC API used by our own client components in `apps/web`. One router per persona route group plus a `common` router. Callers: only our browser code on the same origin. Not for tenant systems or aggregators (they use the public REST API, [[INT-public-api-and-webhooks]]). No compatibility promise across releases beyond the version-skew rules in [[APP-rendering-and-caching-strategy]].

Deliberately not exposed: anything a Server Component can read directly; tribunal-only data outside the `tribunal` router; cross-tenant data.

<!-- section:resources -->
## Resources and identifiers

```text
appRouter
  common        session info, notifications, preferences, search (tenant-scoped)
  portal        cases, case timeline, documents, filings drafts, payments status, hearings
  tribunal      cases, record, drafts, deliberations, orders, appointments
  secretariat   queues, case commands, bulk operations, tasks, intake, scheduling
  transcription assignments, media URLs, segments, review
  admin         users, invitations, roles, settings, theme, terminology, rules, webhooks, api clients
  ops           tenants, flags, support access, break-glass (platform-admin host only)
```
Identifiers: entities are addressed by tenant-visible references where they exist (`caseRef`, for example `ARB-2026-00123`; `filingRef`), otherwise by UUIDv7. The tenant is never an input. Database UUIDs of cases are not exposed to the browser.

<!-- section:operations -->
## Operations

Procedure builders: `authedProcedure` (valid session, tenant membership), `personaProcedure(persona)` (adds persona check), `caseProcedure(relation)` (resolves `caseRef` inside the tenant transaction and checks the caller's relation: `participant`, `tribunal`, `secretariat`). Mutations use `idempotentMutation` where marked.

| Procedure | Type | Builder / relation | Idempotent | Notes |
|---|---|---|---|---|
| `common.me` | query | authed | safe | user, tenants, personas |
| `common.notifications.list` / `markRead` | query / mutation | authed | yes | |
| `common.search` | query | authed | safe | tenant-scoped search ([[PKG-search]]), results filtered by permission |
| `portal.cases.list` | query | persona(party, counsel) | safe | cursor |
| `portal.case.timeline` | query | case(participant) | safe | |
| `portal.documents.list` | query | case(participant) | safe | |
| `portal.documents.getViewUrl` | mutation | case(participant) | yes | sandbox signed URL, 5 min |
| `portal.filings.saveDraft` | mutation | case(participant) | yes (draftVersion) | |
| `portal.payments.status` | query | case(participant) | safe | server verifies with gateway |
| `tribunal.cases.list` | query | persona(neutral) | safe | |
| `tribunal.record.list` | query | case(tribunal) | safe | |
| `tribunal.drafts.get` / `save` / `lock` / `release` | query / mutation | case(tribunal) | yes (baseVersion, lease) | |
| `tribunal.deliberations.list` / `add` | query / mutation | case(tribunal) | yes | tribunal-only tier |
| `secretariat.queue.page` / `counts` | query | persona(secretariat) | safe | |
| `secretariat.case.changeStatus` | mutation | case(secretariat) | key | state machine check |
| `secretariat.bulk.start` / `status` | mutation / query | persona(secretariat) | key | long-running: returns `operationId` |
| `secretariat.tasks.claim` / `complete` / `reassign` | mutation | persona(secretariat) | key | |
| `secretariat.intake.acceptBatch` | mutation | persona(secretariat) | key | |
| `transcription.assignments.list` | query | persona(transcriber) | safe | |
| `transcription.media.getUrl` | mutation | assignment owner | yes | 15 min URL |
| `transcription.segments.save` | mutation | assignment owner | yes (segmentVersion) | |
| `admin.users.*`, `admin.invitations.*` | mixed | persona(tenant-admin) | key on create | |
| `admin.apiClients.create` | mutation | persona(tenant-admin) + step-up | key | secret returned once |
| `admin.webhooks.*` | mixed | persona(tenant-admin) | key on create | |
| `ops.*` | mixed | platform staff + host check | key | platform-admin host only |

The family exceeds 20 operations; it is kept as one node for now with the intent to split per persona router once each router's contract stabilises (Phase 4).

<!-- section:schemas -->
## Request and response schemas

- Inputs and outputs are Zod schemas in `packages/api/src/schemas/{persona}`; outputs are explicit view objects (no Prisma types cross the boundary), validated with `.output()` in development and CI [R1].
- Dates: ISO 8601 strings with offset (`2026-03-05T17:00:00+08:00`) plus the IANA zone where it matters (`seatTimeZone`).
- Money: `{ amountMinor: integer, currency: 'INR' | 'SGD' | 'USD' | … }`.
- Enums: string unions, closed; new values are additive and clients must handle unknown values with a generic label.
- Cursor pagination: `{ items, nextCursor | null }`, cursors opaque and signed.
- Unknown input keys rejected (`.strict()`).

<!-- section:errors -->
## Error model

Errors use the problem types in [[APP-api-error-catalogue-problem]]. The tRPC error formatter places the problem object in `error.data.problem` and sets the tRPC code from the problem's HTTP status. Validation errors carry `errors: [{ pointer: '/parties/0/email', code: 'invalid_email' }]` which forms map to fields. Not-found and no-access both return `not-found`.

<!-- section:auth -->
## Authentication, scopes and permissions

Session cookie (`__Host-session`) only, same origin, plus `x-trpc-source: web` header on mutations. Scopes are not used internally; the persona and case relation from the builder, then the permission matrix ([[PKG-policy-engine-permission-matrix]]) decide each call. Step-up procedures return `step-up-required` with a `stepUpUrl` when the session's authentication is older than 5 minutes for that action class.

<!-- section:tenancy -->
## Tenancy and region routing

Tenant is the one resolved from the host by `proxy.ts` and confirmed against the session membership in `authedProcedure`. Each procedure runs in a tenant transaction through [[MT-prisma-client-extension-wraps]]; forced RLS ([[MT-rls-enabled-and-forced-on]]) is the final layer. Requests to the wrong region never reach tRPC (redirected in `proxy.ts`). A suspended tenant gets `tenant-suspended` on every procedure.

<!-- section:pagination -->
## Pagination, filtering and sorting

Cursor pagination on all list procedures; default 25, maximum 100 (secretariat queue default 50). Sort and filter fields are allow-listed per procedure and mapped to indexes that lead with `tenant_id`.

<!-- section:idempotency -->
## Idempotency, concurrency and long-running operations

Mutations marked 'key' require an `idempotencyKey` (UUIDv7 generated by the client per user intent) stored in `idempotency_keys` for 24 hours; replay returns the stored result. Draft saves use version fields for concurrency (`DRAFT_VERSION_CONFLICT` on mismatch). Long-running operations return `{ operationId }` and are read via a status query.

<!-- section:limits -->
## Rate limits and quotas

Per-user limits in regional Redis: 20 requests per second burst, 300 per minute sustained per user across tRPC; stricter per-procedure limits on `getViewUrl` (60 per minute), `media.getUrl` (30 per minute), `bulk.start` (10 per hour), `apiClients.create` (5 per hour). Exceeding returns `rate-limited` with `Retry-After`.

<!-- section:versioning -->
## Versioning, compatibility and deprecation

No versioning. Clients and server ship together; during rolling deploys `deploymentId` forces stale clients to reload. Breaking changes to a procedure's input must accept the previous shape for one release (the old bundle may call the new server for a few minutes).

<!-- section:questions -->
## Open questions

- [ ] Split this node into one child per persona router at Phase 4 (owner: platform architecture)
- [ ] Should `common.search` be tRPC or a Route Handler with streaming results? (owner: search lead, [[PKG-search]])

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Object-level authorization and tenant isolation

No procedure accepts a tenant input; `caseProcedure` resolves `caseRef` inside the tenant transaction and checks the caller's relation, so a guessed reference from another tenant or case returns the same `not-found` as an unknown one. Cursors are signed and bound to tenant, user and procedure.

<!-- check:security -->
### Attack surface and abuse resistance

Inputs are `.strict()` Zod schemas with max lengths and array sizes; expensive procedures have their own rate limits; tRPC is same-origin only with a custom header; outputs are view objects validated against output schemas.

<!-- check:reliability -->
### Retry safety and consistency

Mutations with effects carry idempotency keys stored for 24 hours in the same transaction as the change; drafts use version fields; long-running work returns an operation ID backed by a Temporal workflow.

<!-- check:privacy -->
### Personal data and residency in the contract

View objects per persona omit fields the persona does not need (party contacts for transcribers, deliberations for parties); no personal data is placed in procedure inputs that end up in URLs (tRPC queries use GET with input in the query string, so search by email or phone uses mutations or POST batching).

<!-- check:audit -->
### Attribution and legal evidence

Each procedure call carries the request ID; mutations write audit events with actor, tenant, case and outcome through [[PKG-audit-trail]]; sensitive reads (document view URLs, media URLs) are audited too.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "kind": "vendor",
    "title": "tRPC documentation: Input and Output Validators",
    "url": "https://trpc.io/docs/server/validators",
    "vendor": "tRPC"
  }
]
```

<!-- end -->
