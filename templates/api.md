# Template: API contract (`api`)

Generated from `api.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies an API surface (internal tRPC / Route Handlers, public REST, or webhooks and events) as a contract precise enough that a client could be built against it before the server exists, including errors, auth scopes, tenancy, limits and how it changes over time.

**Depth:** 3-10 pages plus a machine-readable spec. The OpenAPI 3.1 (or AsyncAPI 3.0 for events) document is the source of truth and must be linked and validated in CI; this node explains intent, rules and decisions the spec cannot carry. Operation, error and scope tables must be complete for the scope. Split into children when a family passes about 20 operations or 15 event types, or when internal and public surfaces diverge.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `purpose` Purpose, audience and surface (level 1)

What this API family is for, who calls it (our own UI, tenant systems, aggregators, partners), which surface it belongs to (internal, public REST, webhooks) and what it deliberately does not expose.

Illustrative example (not a requirement):

> **Case API (public, v1).** Lets an institution's case management system or an aggregator (for example an MII routing SEBI matters) create cases, add parties and read status without using our UI.
> 
> | Surface | Caller | Transport |
> |---|---|---|
> | Public REST | Tenant back-office systems, aggregators | `https://api.in.<platform-domain>/v1` (per region) |
> | Internal tRPC | Our Next.js app (party/counsel, secretariat route groups) | `/api/trpc/case.*` |
> | Webhooks | Tenant endpoints | `case.*` events |
> 
> Out of scope: award drafting, neutral deliberation notes, fee calculation internals (exposed only as computed results).

### `resources` Resources and identifiers (level 1)

The resources this API exposes, how they relate, URL structure, and the identifier format. State which IDs are public, which are internal-only, and whether tenants can supply their own external reference.

Illustrative example (not a requirement):

> | Resource | Path | ID format | Notes |
> |---|---|---|---|
> | Case | `/v1/cases/{case_id}` | `case_01J9Z...` (prefixed UUIDv7) | Public ID; Postgres PK not exposed if different |
> | Party | `/v1/cases/{case_id}/parties/{party_id}` | `pty_...` | Sub-resource; never addressable without its case |
> | Filing | `/v1/cases/{case_id}/filings/{filing_id}` | `fil_...` | Immutable once submitted |
> 
> `external_ref` (string, max 64, unique per tenant) lets an institution store its own case number, e.g. `HK-ARB-2026-0142`. IDs never encode tenant, region or sequence counts.

### `operations` Operations (level 1)

Every operation in a table: method and path (or tRPC procedure), summary, required scope, which personas can reach it, whether it is safe, idempotent or long-running. This is the checklist reviewers compare against the OpenAPI file.

Illustrative example (not a requirement):

> | Operation | Method / path | Scope | Idempotent | Notes |
> |---|---|---|---|---|
> | Create case | `POST /v1/cases` | `cases:write` | With `Idempotency-Key` (required) | Returns 201 + `Location` |
> | Get case | `GET /v1/cases/{id}` | `cases:read` | Yes | ETag returned |
> | List cases | `GET /v1/cases` | `cases:read` | Yes | Cursor pagination |
> | Update case metadata | `PATCH /v1/cases/{id}` | `cases:write` | With `If-Match` | JSON Merge Patch; status not patchable |
> | Withdraw case | `POST /v1/cases/{id}/withdraw` | `cases:transition` | With `Idempotency-Key` | Command, not a field update |
> | Internal: `case.fileResponse` | tRPC mutation | session: counsel of respondent | With client mutation ID | Used by the filing journey |

### `schemas` Request and response schemas (level 1)

Shapes of requests and responses: field names, types, required versus optional, nullability, formats and enums, written once (Zod or JSON Schema) and generated into OpenAPI. State conventions for dates, money, enums, expansion of related objects and unknown fields.

Illustrative example (not a requirement):

> ```yaml
> Case:
>   type: object
>   required: [id, status, created_at, rules]
>   properties:
>     id: { type: string, pattern: '^case_[0-9A-Za-z]{26}$', readOnly: true }
>     external_ref: { type: [string, 'null'], maxLength: 64 }
>     status: { type: string, enum: [draft, filed, served, constituted, hearing, award_issued, closed, withdrawn] }
>     rules: { type: string, examples: ['HKIAC-2024', 'SEBI-ODR-2023'] }
>     claim_amount: { $ref: '#/components/schemas/Money' }  # { amount: '1250000.00', currency: 'INR' }
>     created_at: { type: string, format: date-time, readOnly: true }  # RFC 3339, UTC
> ```
> Conventions: snake_case; money as decimal string plus ISO 4217 code; clients must ignore unknown fields; new enum values are allowed in minor changes, so clients must handle unknown values.

### `errors` Error model (level 1)

Every error is an RFC 9457 problem details object. List each problem type this API can return with its HTTP status, when it happens, whether it is retryable and what the client should do. Say how validation errors point at fields.

Illustrative example (not a requirement):

> | `type` (URI) | Status | When | Retry? |
> |---|---|---|---|
> | `/problems/validation` | 422 | Body fails schema; `errors[]` lists JSON Pointers | No |
> | `/problems/not-found` | 404 | Unknown ID **or** ID in another tenant or case the caller cannot see | No |
> | `/problems/state-conflict` | 409 | e.g. withdraw after award issued | No |
> | `/problems/precondition-failed` | 412 | `If-Match` ETag stale | After re-read |
> | `/problems/idempotency-key-reused` | 422 | Same key, different body | No |
> | `/problems/rate-limited` | 429 | Over quota; `Retry-After` set | Yes |
> 
> ```json
> {"type":"https://api.<platform-domain>/problems/state-conflict","title":"Case cannot be withdrawn in its current status","status":409,"detail":"Case case_01J9Z... is award_issued","instance":"/v1/cases/case_01J9Z.../withdraw","request_id":"req_7f3a..."}
> ```

### `auth` Authentication, scopes and permissions (level 1)

How each caller authenticates (session cookie for internal, OAuth 2.0 client credentials or API keys for public), the full scope list, and how scopes combine with the case-level permission matrix in the Security node. Scopes limit what a credential may attempt; the permission matrix still decides each object.

Illustrative example (not a requirement):

> | Caller | Mechanism | Token lifetime |
> |---|---|---|
> | Our web app | Session cookie, `SameSite=Lax`, CSRF token on mutations | Session policy (5.1.3) |
> | Tenant system | OAuth 2.0 client credentials, private_key_jwt | 15 min access token |
> | Simple integrations | API key `sk_live_in_...`, hashed at rest, shown once | Until rotated (max 1 year) |
> 
> | Scope | Grants |
> |---|---|
> | `cases:read` | Read cases and parties the client's service account can see |
> | `cases:write` | Create cases, edit metadata |
> | `cases:transition` | Lifecycle commands (withdraw, close) |
> | `documents:read` | Download filings (signed URL, 5 min) |
> | `webhooks:manage` | Register and rotate endpoints |

### `tenancy` Tenancy and region routing (level 1)

How the tenant is determined for every call (always from the credential or session, never from the path or body), how calls reach the tenant's region, and what happens if a credential is used against the wrong region or a tenant is suspended.

Illustrative example (not a requirement):

> - Each API client and key belongs to exactly one tenant and one region; the tenant ID is resolved from the credential and set with `set_config('app.tenant_id', ..., true)` by the Prisma extension.
> - Base URLs per region: `api.in.`, `api.sg.`, `api.us.`. A Singapore key used on `api.in.` gets `401 /problems/wrong-region` with the correct base URL in `detail`; no data is read.
> - Request bodies may not contain `tenant_id`; it is rejected by schema (`additionalProperties: false`).
> - Suspended tenant: reads allowed for 30 days for export, writes return `403 /problems/tenant-suspended`.

### `pagination` Pagination, filtering and sorting (level 2)

How list endpoints page (cursor or offset), page size limits, stable ordering, which fields can be filtered and sorted, and how filters map to indexes so they cannot become slow full scans.

Illustrative example (not a requirement):

> `GET /v1/cases?status=hearing&updated_after=2026-09-01T00:00:00Z&limit=50&cursor=eyJ...`
> 
> - Cursor pagination only; cursor is opaque, signed and bound to tenant and filter set.
> - `limit` default 25, max 100.
> - Default order `created_at desc, id desc` (stable tiebreak).
> - Filterable: `status`, `rules`, `updated_after`, `external_ref`. Each backed by an index listed in the Data model node.
> - Response: `{ "data": [...], "next_cursor": "..." | null }`. No total count by default (expensive under RLS); `include=total` allowed up to 10,000 rows.

### `idempotency` Idempotency, concurrency and long-running operations (level 2)

Which operations need an Idempotency-Key, how long keys are kept and what replay returns; how concurrent edits are detected (ETag / If-Match or a version field); and how slow operations (bundling, transcription, bulk import) are exposed (202 plus an operation resource, or webhook on completion).

Illustrative example (not a requirement):

> - `Idempotency-Key` required on all public `POST` commands; stored per tenant + key for 24 h with a hash of the body. Replay returns the original status and body with `Idempotent-Replayed: true`.
> - `PATCH` requires `If-Match: "v7"`; stale returns 412.
> - `POST /v1/cases/{id}/bundles` starts a Temporal workflow and returns `202 Accepted` with `Location: /v1/operations/op_...`. The operation resource reports `pending | running | succeeded | failed` and links the bundle when done; a `bundle.completed` webhook is also sent.

### `events` Webhooks and events (level 2)

The event catalogue (name, trigger, payload, which scope or subscription receives it), the envelope, how deliveries are signed and verified, retry schedule, ordering and duplicate guarantees, and how endpoints are registered. Link the AsyncAPI document.

Illustrative example (not a requirement):

> | Event | Trigger | Payload (summary) |
> |---|---|---|
> | `case.filed` | Claimant submits request for arbitration | case id, rules, filed_at |
> | `case.status_changed` | Any lifecycle transition | case id, from, to, at |
> | `hearing.scheduled` | Secretariat confirms slot | hearing id, case id, starts_at (UTC), timezone |
> | `document.served` | Filing served on other party | filing id, served_at |
> 
> Envelope follows CloudEvents attributes (`id`, `type`, `source`, `time`, `specversion`) plus `tenant`. Payloads are thin: IDs and changed fields only, no document content or personal data beyond IDs; receivers fetch details via the API. Signed with HMAC-SHA256 over `id.timestamp.body`, per-endpoint secret, timestamps older than 5 minutes rejected. At-least-once delivery, retries over 72 h with exponential backoff, no ordering guarantee across events (use `time` and fetch current state).

### `limits` Rate limits and quotas (level 2)

Limits per credential, per tenant and per operation class, how they relate to plan entitlements, which headers tell clients where they stand, and what happens at the limit.

Illustrative example (not a requirement):

> | Class | Limit | Scope |
> |---|---|---|
> | Reads | 600 / min | per API client |
> | Writes | 120 / min | per API client |
> | Document downloads | 60 / min, 5 GB / day | per tenant |
> | Bulk case import | 2 concurrent operations | per tenant (plan: Institutional) |
> 
> Over limit: `429` with `Retry-After` and `RateLimit-Policy` / `RateLimit` headers. Limits are enforced in Redis in the tenant's region, keyed by tenant and client, so one tenant cannot exhaust another's budget.

### `versioning` Versioning, compatibility and deprecation (level 2)

How versions are named, what counts as a breaking change, what may change without a new version, how deprecation is announced (headers, changelog, email to tenant admins) and the minimum notice before removal.

Illustrative example (not a requirement):

> - Major version in path (`/v1`). Within v1 we may add optional fields, new endpoints, new enum values and new event types; we may not remove or rename fields, tighten validation, or change error types.
> - Breaking changes detected by an OpenAPI diff in CI; a breaking diff fails the build unless the PR targets a new major version.
> - Deprecation: `Deprecation` and `Sunset` headers on affected responses, changelog entry, email to each tenant's technical contact, minimum 12 months for public APIs (6 for internal tRPC, which we deploy together with the UI).
> - Usage of deprecated operations is tracked per tenant before sunset.

### `examples` Worked examples (level 3)

Two or three end-to-end sequences a client developer would follow, with real requests and responses, including one failure and recovery.

Illustrative example (not a requirement):

> **Aggregator files a SEBI ODR matter and waits for a conciliator.**
> 1. `POST /v1/cases` with `Idempotency-Key: 6f1c...` returns `201`, `case_01J9Z...`, status `filed`.
> 2. Network timeout on the client; it retries with the same key and gets the same `201` plus `Idempotent-Replayed: true`.
> 3. Webhook `case.status_changed` (`filed` to `constituted`) arrives twice; the receiver de-duplicates on event `id`.
> 4. `GET /v1/cases/case_01J9Z...` returns the appointed neutral's public profile ID.

### `questions` Open questions (level 3)

Unresolved items as a checklist, each with an owner.

Illustrative example (not a requirement):

> - [ ] Do aggregators need a bulk status endpoint, or are webhooks enough? (Product)
> - [ ] OAuth client credentials only, or also API keys for smaller institutions? (Security)
> - [ ] Should `include=total` be removed entirely for performance? (Platform)
> - [ ] Event payloads: thin only, or optional full snapshot for tenants that cannot call back? (Architecture)

## Checks

### `tenancy` Object-level authorization and tenant isolation

**Question:** Can any operation, filter, cursor, expansion or webhook return or change an object belonging to another tenant, or to a case the caller is not a participant in, if the caller supplies or guesses its ID?

- For each operation that takes an ID (path, query, body, nested `include`), where is the object-level check that the caller may see that specific object, and is it the same policy function the UI uses?
- Do unknown IDs and forbidden IDs return the same 404 problem with the same timing, so the API cannot be used to learn whether a case exists in another tenant?
- Are cursors, ETags, operation IDs and signed download URLs bound to tenant and caller, so one leaked or copied from another tenant fails?
- Can a request body or query parameter set `tenant_id`, `owner_id`, `role` or `status` directly (mass assignment), and is `additionalProperties: false` enforced on every write schema?
- Is forced RLS still the final layer for every API path, including Route Handlers that use raw SQL, background export endpoints and tRPC procedures called from Server Components?
- For a webhook, can an event about tenant A ever be delivered to an endpoint registered by tenant B (shared endpoint URL, misrouted queue, retry after re-registration)?
- How is a user who is counsel in two tenants handled when they use a personal API token: one token per tenant, or a token that can switch tenants?

**Good answer:** Shows a per-operation table naming the object-level policy check (for example `canViewCase(principal, caseId)`), with tenant always taken from the credential and forced RLS underneath. Unknown and forbidden objects are indistinguishable. Write schemas reject unknown fields and server-owned fields. An automated suite runs every operation as a principal from another tenant and from a non-participant in the same tenant, and expects 404 for each.

**Red flags:**

- Tenant or case access decided only by the client sending the right path or header
- 403 for forbidden objects and 404 for missing ones, revealing existence
- Write endpoints that bind the request body straight into a Prisma `update` call
- No automated broken-object-level-authorization test across tenants

### `security` Attack surface and abuse resistance

**Question:** Has every operation been reviewed against the OWASP API Security Top 10 and the platform's abuse cases, with concrete limits on input size, cost and outbound calls?

- What are the maximum body size, array length, string length, nesting depth and upload size per operation, and where are they enforced (edge, Route Handler, Zod schema)?
- Which operations are expensive (search, exports, bundling, AI summaries) and what stops one client from running them in a loop: per-operation quotas, concurrency caps, cost-based limits?
- Webhook endpoint registration: are URLs validated against SSRF (no private IP ranges, no metadata endpoints, HTTPS only, re-resolved on each delivery), and are redirects refused?
- Do filters and sort parameters map to an allow-list, so no caller-controlled string reaches SQL, the search engine or a regex?
- How are credentials protected: API keys hashed at rest and shown once, OAuth tokens short-lived and audience-bound, keys revocable instantly, leaked-key scanning on public repositories?
- Which operations are sensitive business flows (bulk invitations, OTP or magic-link sends, party contact changes) and what extra controls stop automated misuse?
- Are error responses and `detail` strings checked so they never contain stack traces, SQL, internal hostnames or other parties' data?

**Good answer:** Includes a short table mapping each Top 10 risk to the operations it affects and the control in place, with numeric limits for size, rate and concurrency. Webhook delivery runs from an egress-controlled worker with SSRF protections. Credential handling is specified end to end, including revocation time and secret scanning. A security test plan covers fuzzing of schemas and limit enforcement.

**Red flags:**

- No body, page-size or upload limits stated
- Webhook URLs accepted and called without SSRF protection
- Free-text sort or filter parameters passed to the query layer
- API keys stored in plaintext or retrievable after creation

### `compatibility` Contract governance and breaking changes

**Question:** How do we guarantee that the published contract and the running code never drift apart, and that no change breaks an existing client without the agreed notice?

- Is the OpenAPI / AsyncAPI document generated from the same Zod schemas the handlers validate with, or hand-written? If hand-written, what proves they match?
- Which tool diffs the spec on every pull request, which change classes fail the build, and who can approve an exception?
- Do response validators run in CI (and optionally in staging) so the server cannot return a shape the spec does not allow?
- Are there consumer-driven contract tests for our own UI, for the tenants' most-used operations and for aggregator integrations?
- How are behavioural changes caught that the schema diff cannot see (new validation rule, changed default sort, different status code, changed webhook timing)?
- When a field must change meaning for one jurisdiction or tenant, how is that done without forking the contract?
- How long are old major versions run in parallel, and what is the cost of keeping both (dual writes, translation layer)?

**Good answer:** The schema is single-sourced and the spec is generated and committed; CI fails on breaking diffs and on spec drift, and runs response validation against the spec in integration tests. A written list defines breaking versus non-breaking changes, including behavioural ones. Deprecation steps, notice periods and per-tenant usage tracking are named with owners.

**Red flags:**

- OpenAPI written by hand after the code, with no check that they match
- No automated breaking-change detection
- Version policy stated as 'we will be careful'
- Internal tRPC changes assumed safe even though mobile or cached clients may lag a deploy

### `reliability` Retry safety and consistency

**Question:** If any request or webhook delivery is retried, duplicated, reordered or interrupted half-way, does the system end up in the correct state with no duplicate legal or financial effects?

- Which operations create legally significant records (filing, service, payment, award publication), and is each protected by an idempotency key scoped to tenant and caller, with body hash comparison?
- Is the idempotency record written in the same database transaction as the business change, so a crash between them cannot leave a half-applied request?
- Are webhooks emitted from a transactional outbox (written with the state change, delivered by a worker), so an event is never sent for a change that rolled back and never lost for one that committed?
- What happens when a Temporal workflow started by `202 Accepted` fails or is retried: is the operation resource updated, and is a completion event sent exactly once from the client's point of view (same event ID)?
- How do clients recover after missing webhooks for days: is there an events list endpoint or `updated_after` filter to resynchronise?
- Under concurrent edits from the UI and the public API, what wins, and does the loser receive a clear 409 or 412 rather than a silent overwrite?
- What are the server-side timeouts per operation and what does the client see if the server times out after committing?

**Good answer:** Names the idempotency storage, key scope, retention and replay behaviour, and shows the key and the business write commit together. Webhooks use an outbox with stable event IDs and documented at-least-once semantics, plus a resynchronisation path. Concurrency control (ETag or version column) is specified for every mutable resource, and timeouts are listed with the client guidance for each.

**Red flags:**

- Payments or filings with no idempotency protection
- Webhooks sent directly from the request handler before or without the database commit
- No way for a client to recover missed events
- Last-write-wins on case data without telling the client

### `privacy` Personal data and residency in the contract

**Question:** Does each operation and event expose only the personal and case data the caller needs, keep it out of URLs and logs, and keep it within the tenant's region and lawful transfers?

- Which response fields contain personal data (names, emails, phone numbers, ID numbers, addresses), and is each one needed by every caller of that operation, or should it be behind a separate scope or field selection?
- Is any personal data or case content placed in a URL path or query string (where it lands in proxy, CDN and browser logs)? Searches by email or phone should use POST bodies.
- Do webhook payloads carry personal data or document content to tenant endpoints that may be outside the tenant's region, and is that covered by the tenant contract?
- Do regional base URLs guarantee processing stays in region, including the edge, WAF, API gateway logs and rate-limit counters?
- How do data subject requests (DPDP, GDPR, PDPA access or erasure) interact with the API: are erased parties redacted in responses and events, and is there an export endpoint?
- Are confidential-tier fields (for example tribunal-only notes, sealed documents) excluded from public schemas entirely rather than filtered at runtime?
- What is logged for each request (headers, bodies, query strings), and how are bodies with personal data masked before logs leave the service?

**Good answer:** A field-level table classifies personal and confidential fields per schema and states which scope reveals each. No personal data in URLs, logs mask bodies by default, and webhook payloads are thin. Regional endpoints and their supporting infrastructure are confirmed to process data in region, and the API's handling of erasure and export requests is specified.

**Red flags:**

- Email addresses or phone numbers used as path parameters or query filters
- Full request and response bodies logged in production
- Webhooks pushing documents or party contact details by default
- A single global API endpoint that routes to regions after terminating TLS and logging elsewhere

### `audit` Attribution and legal evidence

**Question:** For every call that changes state or reads sensitive material, can we later prove which principal did it, on whose behalf, with which credential and payload, and what the system answered?

- Does every request carry a request ID returned to the client and recorded in the audit trail, logs and traces, and can a tenant quote it to support?
- For machine clients, is the audit actor the API client, a named service account, and where relevant the human the integration acted for (for example a case manager at the institution)?
- Are filings and other legally significant submissions made through the API recorded with a content hash, received-at timestamp from our clock, and the exact version of the contract used?
- Are sensitive reads (document downloads, party contact details, exports) audited, not only writes?
- Can a tenant retrieve the audit history of actions made by its API clients (for example through an audit events endpoint), scoped to its own tenant?
- How long are audit records for API activity kept, and does that match retention required by the institution's rules and our ISO 27001 controls?

**Good answer:** States that every mutating operation and listed sensitive read writes an audit entry through the Audit trail package in the same transaction, including principal, acting-for user, client ID, request ID, operation, object IDs, content hash and outcome. Received-at times come from the server. Tenants can see their own API audit history, and retention is linked to the retention schedule.

**Red flags:**

- API actions attributed only to a shared integration user
- Audit written asynchronously with no guarantee it survives a crash
- No record of document downloads
- Client-supplied timestamps used as the legal filing time

### `operability` Service levels, capacity and observability

**Question:** What availability and latency does this API commit to per operation class, what load is it sized for, and can we see per tenant, client and region whether it is meeting those targets right now?

- What are the latency targets (p95, p99) and availability SLO for reads, writes and long-running starts, and are any committed in tenant contracts?
- What request volumes are expected per tenant at launch and in two years (for example an aggregator bulk-filing thousands of MSME matters at month end), and has that been load-tested through PgBouncer and RLS?
- Are metrics emitted per operation, status code, tenant, client and region with OpenTelemetry, without personal data in labels?
- Which alerts fire on error-rate or latency burn, on a single tenant's sudden spike, and on webhook delivery backlog or endpoint failure rates?
- When a tenant's webhook endpoint keeps failing, how and when are they told, and when is the endpoint automatically disabled?
- Is there a public status page per region that reflects API health, and are planned maintenance windows announced through the API (headers or changelog)?

**Good answer:** Lists numeric SLOs per operation class tied to error budgets, expected and tested peak volumes, and the dashboards and alerts that watch them per tenant and region. Webhook delivery health is visible to us and to each tenant, with documented auto-disable and notification rules.

**Red flags:**

- No latency or availability targets
- No load test with realistic aggregator bulk traffic
- Webhook failures only visible in worker logs
- Tenant or client IDs missing from API metrics, so a noisy client cannot be identified

### `consumability` Developer experience and onboarding

**Question:** Can a developer at an institution or aggregator go from zero to a working, safe integration using only the published documentation, sandbox and examples, without contacting our engineers?

- Is there a sandbox per region with synthetic data, separate credentials and the same contract, and are sandbox webhooks deliverable to test endpoints?
- Does every operation in the spec have a description, at least one request and response example and its possible problem types?
- Are SDKs or typed clients generated from the spec, and who maintains and versions them?
- Is there a getting-started guide for the two most common jobs (for example create a case and receive status events) with copy-paste code and signature-verification snippets in common languages?
- Are names, units and enums consistent with the other API families (same pagination, error, money and date conventions), so integrators learn them once?
- How does an integrator test failure handling: can the sandbox simulate 429s, 5xx, slow responses and duplicate webhooks?

**Good answer:** Names the developer portal location, sandbox per region, generated SDKs and the review that checks every operation has descriptions, examples and errors. Provides a getting-started path and a way to simulate failures. Conventions are shared with other API families through the API standard node rather than redefined.

**Red flags:**

- No sandbox, or a sandbox that uses production data
- Operations with no examples or no listed errors
- Different pagination or error shapes from other families of the same platform

