---
id: "INT-public-api-and-webhooks"
title: "Public API and webhooks"
parent: "INT"
order: 4
type: "capability"
template: "integration"
childTemplate: "api"
status: "draft"
owner: null
indicative: false
summary: "Our public REST API and outbound webhooks for institutions, aggregators and partners: regional base URLs, scopes, usage limits, sandbox, developer portal and the tenant administration of API access, clients, webhooks and usage"
links: []
rev: 4
syncHash: "412621805f48dada"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 9.4 Public API and webhooks

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Our public REST API and outbound webhooks for institutions, aggregators and partners: regional base URLs, scopes, usage limits, sandbox, developer portal and the tenant administration of API access, clients, webhooks and usage

<!-- section:purpose -->
## Purpose and use cases

Institutions, aggregators and partners integrate with the platform through a public REST API and outbound webhooks. This node owns the shared mechanics of that surface and its **tenant administration**; each API family has a child node:

| Child | Family |
|---|---|
| [[INT-public-api-cases-and-parties]] | Cases, parties, representatives, lifecycle commands |
| [[INT-public-api-documents-and-filings]] | Uploads, filings, documents, versions, bundles |
| [[INT-public-api-hearings-and]] | Hearings, slot proposals, room status, transcripts |
| [[INT-tenant-admin-api]] | Users, roles, API clients, webhook endpoints, settings, branding |
| [[INT-aggregator-intake-api]] | Bulk filing and status pull for aggregators |
| [[APP-webhooks-outbound]] and [[INT-webhook-event-catalogue]] | Webhook delivery, endpoint and event subscription admin, replay, event types |
| [[INT-api-platform-tables]] | Credentials, idempotency, endpoints, outbox, deliveries |

Use cases: an arbitral institution's case management system creates cases and files documents; a SEBI ODR institution receives status events for onward reporting; an aggregator bulk-files matters; a law firm's practice system reads hearing dates. Here, unlike other integration nodes, **we are the provider** and the tenant's system is the external party.

**Administration at a glance**

| Concern | Where | Who | Owning node |
|---|---|---|---|
| Turn the API and webhooks on, pin API version, sandbox, tenant rate limits below entitlement | `/admin/integrations/api` | `integration_admin`, `tenant_admin` | this node; keys in [[PKG-settings-integrations]] group G |
| API clients, keys, OAuth clients, scopes granted, IP restrictions, key expiry | `/admin/integrations/api-clients` | `integration_admin`, `security_admin` | [[PKG-api-clients-and-keys]] |
| Webhook endpoints, event subscriptions, signing secrets, retries, delivery log, replay | `/admin/integrations/webhooks` | `integration_admin` | [[APP-webhooks-outbound]] |
| External apps acting through the API | `/admin/integrations/apps` | `integration_admin`, approvers | [[INT-plugin-model]] |
| Usage, errors and limits per client | `/admin/integrations/api/usage` | `integration_admin`, `auditor` (read) | this node |
| Deprecation notices and changelog subscriptions | `/admin/integrations/api/changes` | `integration_admin` | this node |
| Platform view: per-region API health, clients per tenant, abuse controls | `/platform/integrations/api` | `platform_admin`, `platform_security` | this node |

All admin actions are operations in [[INT-tenant-admin-api]], so the console, bulk tools and the admin copilot use the same permission-checked calls.

<!-- section:party -->
## External party and ownership

- **Owner**: platform engineering (API platform team), with product owners for CORD and TERES per family.
- **External parties**: tenant IT teams and their vendors, aggregators, partners. Each is an API client registered by a tenant admin (or, for aggregators, by a platform admin with the tenant's consent).
- **Environments**: sandbox and production per region. Base URLs (placeholders): `https://api.in.<platform-domain>/v1`, `https://api.sg.<platform-domain>/v1`, `https://api.us.<platform-domain>/v1`; sandbox `https://sandbox-api.{region}.<platform-domain>/v1`. Azure-hosted tenants use the same hostnames routed to the Azure stack.
- **Developer portal**: static site generated from the OpenAPI 3.1 [R1] and AsyncAPI 3.0 [R2] documents, with getting-started guides, signature-verification snippets (TypeScript, Python, Java, C#), changelog and status links. Signed-in portal pages (key management) are part of the tenant admin console.

<!-- section:flows -->
## Data flows

1. **Enablement**: an integration admin turns on `integration.api.enabled` (entitlement `feature.public_api`), confirms the pinned API version and sandbox access.
2. **Client onboarding**: the admin creates an API client in the console (or via [[INT-tenant-admin-api]] with an admin session), chooses scopes and a principal role, and receives an API key once or registers a JWKS for OAuth `private_key_jwt` ([[PKG-api-clients-and-keys]]).
3. **Token**: OAuth clients call `POST /oauth/token` (client credentials) for a 10-minute access token bound to tenant, region and scopes; API-key clients send `Authorization: Bearer ntk_live_in_...` directly.
4. **Request**: edge (WAF, TLS) → regional API gateway Route Handlers in the Next.js app (`app/api/v1/...`) → auth middleware resolves credential → tenant context transaction → handler → RFC 9457 errors on failure [R4].
5. **Events**: state changes write to the outbox in the same transaction; the webhook relay delivers to registered endpoints ([[APP-webhooks-outbound]]).
6. **Resync**: clients that missed events use `GET /v1/events?after=` (30 days) or `updated_after` filters on list endpoints; admins can replay deliveries from the console.
7. **Monitoring**: the admin sees per-client request counts, error rates by problem type, rate-limit rejections and last use at `/admin/integrations/api/usage`; clients unused for 90 days are flagged for review ([[SEC-access-reviews]]).
8. **Change**: deprecations are announced with headers, changelog and email to `integration.api.deprecation_contacts`; the admin moves the pinned version when ready.

<!-- section:mapping -->
## Data mapping

Field-level mapping is in each API family node. Conventions shared by all families:
- IDs: type-prefixed UUIDv7 strings (`case_…`, `doc_…`, `hrg_…`); tenant-supplied `external_reference` (unique per tenant and resource type, max 128 chars).
- Timestamps RFC 3339 in UTC with `Z`; local times carried with an IANA `time_zone` field.
- Money: `{ "amount_minor": "191693", "currency": "INR" }` with amount as a string integer.
- Enums lowercase snake_case; unknown enum values must be tolerated by clients (documented).
- Personal data fields are documented per operation and kept out of URLs.

<!-- section:auth -->
## Authentication and secrets

**Credentials** are specified in [[PKG-api-clients-and-keys]] and stored per [[INT-api-platform-tables]]. Summary of what this surface relies on:
- *API keys*: format `ntk_{live|test}_{region}_{32 random base62}`; only a SHA-256 hash and a prefix are stored; shown once; optional expiry; revocable instantly.
- *OAuth 2.0 client credentials* with `private_key_jwt` client authentication (preferred for institutions and aggregators); access tokens are JWTs, 10-minute lifetime, audience = regional API base URL [R3].
- Credentials are bound to **one tenant and one region**. A person who is counsel in two tenants uses separate clients per tenant.

**Scopes**

| Scope | Grants |
|---|---|
| `cases:read` / `cases:write` | Read cases; create cases, edit metadata, lifecycle commands |
| `parties:write` | Add, update and remove parties and representatives |
| `documents:read` / `documents:write` | Download documents and bundles; upload and file |
| `hearings:read` / `hearings:write` | Read hearings; propose slots |
| `events:read` | Read the events list |
| `admin.org:*`, `admin.users:*`, `admin.access:*`, `admin.settings:*`, `admin.branding:*`, `admin.integrations:*`, `admin.bulk:*`, `admin.changes:*`, `admin.approvals:write`, `admin.packages:write` | Tenant administration; the scope list is owned by [[INT-tenant-admin-api#auth]] |
| `aggregator:intake`, `aggregator:status` | Aggregator operations |
| `audit:read` | Tenant's own audit events |

Scopes limit what a client may attempt; the permission matrix ([[PKG-policy-engine-permission-matrix]]) still decides each object. An API client acts as a `service_account` principal ([[PKG-non-human-principals]]) holding a tenant role or permission set (for example `ps.integration.case_intake`) and can optionally be restricted to units or case types. Admin scopes are requested by an `integration_admin` and approved by a `security_admin` or `tenant_owner` who is not the requester (`api_client:approve`, [[PKG-api-clients-and-keys]]).

<!-- section:errors -->
## Errors, retries and idempotency

All errors use RFC 9457 problem details [R4] with types from [[APP-api-error-catalogue-problem]] (for example `https://errors.<platform-domain>/validation-failed`, `/not-found`, `/insufficient-scope`, `/rate-limited`, `/idempotency-key-reused`, `/precondition-failed`, `/entitlement-limit-reached`, `/tenant-suspended-readonly`, `/wrong-region`). Each response carries `request_id` (also in header `X-Request-Id`). Retry guidance: 429 and 503 retryable with `Retry-After`; 409 `idempotency-request-in-progress` retry after a short delay; all 4xx validation errors non-retryable.

<!-- section:limits -->
## Rate limits and SLAs

Limits per client and per tenant, tied to entitlements ([[BIL-plans-entitlements-and-usage]] `limit.api_rpm`). Tenants may set lower operating limits (`integration.api.rate_limit.reads_per_min`, `.writes_per_min` in [[PKG-settings-integrations]]); the effective limit is `min(entitlement, setting)`.

| Class | Default (standard plan) | Notes |
|---|---|---|
| Reads | 600 req/min per client, 1,200 per tenant | Token bucket in regional Redis |
| Writes | 120 req/min per client | |
| Uploads | 20 concurrent upload sessions per client | |
| Expensive (search, exports, bulk) | 10 req/min, 2 concurrent per tenant | |
| Aggregator batches | 5 concurrent batches, 500 items each | |

Headers `RateLimit-Policy` and `RateLimit` per the IETF draft [R5], plus `Retry-After` on 429. Usage counts feed metering (`usage.api.requests`) and the admin usage page.

**SLO (proposed)**: 99.9% monthly availability per region for the API; p95 latency 300 ms for reads, 800 ms for writes (excluding uploads).

<!-- section:residency -->
## Data transfer and compliance

Each region's API processes only tenants homed there. Credentials encode the region, so the edge routes before credential lookup; a credential used against another region gets `421` with problem type `wrong-region` and the correct base URL. API gateway logs, rate-limit counters and WAF logs stay in the region. Webhook payloads leave our region by design (to tenant endpoints); they carry IDs and changed fields, not documents, and the tenant chooses the endpoint location under its own contract ([[APP-webhooks-outbound]]).

<!-- section:testing -->
## Sandbox and testing

Sandbox per region with synthetic seed data, separate `ntk_test_` credentials and the same contract. The sandbox can simulate failures via header `X-Sandbox-Simulate: rate_limit|server_error|slow|duplicate_webhook`. Contract governance: OpenAPI generated from Zod schemas (`zod-to-openapi`), diffed on every PR with breaking-change detection; response validation in CI integration tests; Pact consumer tests for the aggregator and the two largest institution integrations.

**Versioning**: major version in the path (`/v1`). Additive changes (new optional fields, new endpoints, new event types, new enum values) without a new version. Breaking changes need a new major version run in parallel for at least 12 months; deprecation announced with `Deprecation` [R6] and `Sunset` [R7] headers, changelog entry and email to tenant admins with API clients.

<!-- section:questions -->
## Open questions

- [ ] Domain and hostnames for the API per region and for Azure-hosted tenants.
- [ ] Do we also offer personal access tokens for counsel (user-bound, for practice-management tools), or only service principals in Phase 5 (proposed)? Decision belongs with [[PKG-api-clients-and-keys]].
- [ ] Should API clients be able to act on behalf of a named user (token exchange) for audit attribution?
- [ ] SDKs: generate TypeScript and Python clients from OpenAPI in Phase 5, or later?
- [ ] Minimum deprecation notice: 12 months proposed; check against institutional contracts.
- [ ] Should tenants see a per-client "explain this denial" view (scope versus object permission), reusing [[PKG-access-explainer]]? Proposed: yes in Phase 6.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant separation at the provider

Every credential is bound to one tenant and region; the tenant is set from the credential, never from path or body ([[MT-prisma-client-extension-wraps]]). Object access is decided by the same policy functions as the UI, and forced RLS is the final layer. Webhook endpoints are tenant-owned, and deliveries are fanned out only to endpoints of the event's tenant ([[APP-webhooks-outbound]]).

<!-- check:security -->
### Security

API keys are hashed (SHA-256 of a 190-bit random secret) and shown once; OAuth uses `private_key_jwt` with 10-minute audience-bound tokens [R3]; credentials are revocable instantly (revocation checked on every request, cached at most 30 s). Leaked-key scanning: the `ntk_` prefix is registered with secret-scanning programmes where available (to arrange). Webhooks are signed per endpoint and registered URLs are SSRF-checked. OWASP API Top 10 review is a release gate for each family.

<!-- check:residency -->
### Data transfer and residency

Regional base URLs, region-bound credentials, `421 wrong-region`, in-region logs and counters. Webhooks carry minimal data to tenant-chosen endpoints, under the tenant's contract.

<!-- check:resilience -->
### Failure handling and degradation

Write operations accept `Idempotency-Key`; webhooks are emitted from a transactional outbox; clients can resynchronise from the events list. Limits protect shared capacity per tenant.

<!-- check:observability -->
### Observability

Per region: request rate, error rate by problem type, latency p95 / p99 per operation, rate-limit rejections per client, webhook backlog and endpoint failure rate, all with OpenTelemetry and no personal data in labels. Tenant admins see the same per-client figures for their own tenant at `/admin/integrations/api/usage`. Alerts on SLO burn and on a single tenant's sudden spike. Public status page per region ([[OBS-uptime-synthetic-monitoring]]).

<!-- check:testing -->
### Testing

Sandbox with failure simulation, contract diff and response validation in CI, Pact consumer tests, synthetic API journey per region every 5 minutes.

<!-- citations -->
## Citations

```json
[
  {
    "body": "OpenAPI Initiative",
    "excerpt": "Machine-readable description of HTTP APIs, aligned with JSON Schema 2020-12.",
    "id": "R1",
    "ident": "OpenAPI Specification",
    "kind": "standard",
    "title": "OpenAPI Specification v3.1.1",
    "url": "https://spec.openapis.org/oas/v3.1.1",
    "version": "3.1.1"
  },
  {
    "body": "AsyncAPI Initiative",
    "excerpt": "Machine-readable description of message-driven and event APIs.",
    "id": "R2",
    "ident": "AsyncAPI",
    "kind": "standard",
    "title": "AsyncAPI Specification 3.0.0",
    "url": "https://www.asyncapi.com/docs/reference/specification/v3.0.0",
    "version": "3.0.0"
  },
  {
    "body": "IETF",
    "excerpt": "Recommends sender-constrained or audience-restricted, short-lived access tokens and strong client authentication such as private_key_jwt.",
    "id": "R3",
    "ident": "RFC 9700",
    "kind": "standard",
    "title": "Best Current Practice for OAuth 2.0 Security",
    "url": "https://www.rfc-editor.org/rfc/rfc9700.html"
  },
  {
    "body": "IETF",
    "excerpt": "Defines the application/problem+json object with type, title, status, detail and instance members.",
    "id": "R4",
    "ident": "RFC 9457",
    "kind": "standard",
    "title": "Problem Details for HTTP APIs",
    "url": "https://datatracker.ietf.org/doc/html/rfc9457"
  },
  {
    "body": "IETF (Internet-Draft)",
    "excerpt": "Defines RateLimit-Policy and RateLimit response header fields that tell clients their quota and remaining allowance.",
    "id": "R5",
    "ident": "draft-ietf-httpapi-ratelimit-headers",
    "kind": "standard",
    "title": "RateLimit header fields for HTTP",
    "url": "https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-ratelimit-headers"
  },
  {
    "body": "IETF",
    "excerpt": "Header that signals a resource is or will be deprecated.",
    "id": "R6",
    "ident": "RFC 9745",
    "kind": "standard",
    "title": "The Deprecation HTTP Response Header Field",
    "url": "https://www.rfc-editor.org/rfc/rfc9745.html"
  },
  {
    "body": "IETF",
    "excerpt": "Header that signals the date after which a resource is expected to become unresponsive.",
    "id": "R7",
    "ident": "RFC 8594",
    "kind": "standard",
    "title": "The Sunset HTTP Header Field",
    "url": "https://datatracker.ietf.org/doc/html/rfc8594"
  }
]
```

<!-- end -->
