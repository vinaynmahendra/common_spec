---
id: "APP-api-layer"
title: "API layer"
parent: "APP"
order: 3
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: "Parent standard for every API the app exposes: which style to use when, shared rules for versioning, limits, idempotency, mutations and errors"
links: []
rev: 3
syncHash: "0777b559db60a19c"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 2.3 API layer

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Parent standard for every API the app exposes: which style to use when, shared rules for versioning, limits, idempotency, mutations and errors

<!-- section:purpose -->
## Purpose and scope

Sets the rules shared by every API surface served from `apps/web` and points to the child nodes that hold the detail:

| Child | Covers |
|---|---|
| [[APP-route-handlers-trpc-for-internal]] | Which style to use: tRPC, Server Actions or Route Handlers (internal), REST + OpenAPI (external) |
| [[APP-internal-api-trpc-routers-per]] | Procedure contracts per persona |
| [[APP-api-versioning-rate-limiting]] | Versioning, rate limits, idempotency keys |
| [[APP-server-actions-and-mutation]] | Server Action and mutation conventions |
| [[APP-api-error-catalogue-problem]] | Shared RFC 9457 problem types |

Public resource contracts (cases, documents, hearings, tenant admin, aggregator intake, webhooks) live under [[INT-public-api-and-webhooks]] and follow these rules.

<!-- section:rules -->
## Rules

1. **API-1** Tenant comes from the session or credential, never from a path, query or body field ([[MT-tenant-resolution]]).
2. **API-2** Every input is validated with a Zod schema that rejects unknown keys (`.strict()`); the same schema generates OpenAPI for public routes.
3. **API-3** Every error is an RFC 9457 problem from the shared catalogue ([[APP-api-error-catalogue-problem]]).
4. **API-4** Every state-changing call with legal or financial effect is idempotent by key ([[APP-api-versioning-rate-limiting]]).
5. **API-5** Every call carries a request ID returned in `x-request-id` and recorded in logs, traces and audit events.
6. **API-6** Not-found and no-access are indistinguishable (same status, body and timing class).
7. **API-7** Every procedure, action and handler performs its own authorisation through [[PKG-authorization]].

<!-- section:tooling -->
## Tooling and configuration

Shared packages: `@nomology/api-core` (problem helpers, request ID, idempotency middleware, rate limiter), `@nomology/trpc` (procedure builders), `@nomology/rest` (public REST router and OpenAPI generation).

<!-- section:enforcement -->
## Enforcement

API-2 and API-7 by ESLint rules on procedure and action definitions (must use the builders that require a schema and an `authorize` step); API-3 by a tRPC error formatter and REST error middleware that reject unregistered problem types in tests; API-6 by contract tests; API-5 by middleware.

<!-- section:questions -->
## Open questions

- [ ] Confirm that the public REST router lives in `apps/web` rather than a separate API service per region (owner: platform architecture)

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Rules are enforced by the shared builders (a procedure cannot be defined without a schema and authorisation step) and by contract tests in CI.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

API-1 and API-7 put tenant isolation and authorisation in every entry point; API-6 prevents existence leaks; forced RLS remains the last layer.

<!-- check:exceptions -->
### Exceptions

Exceptions follow [[FND-governance]]; API-1 (tenant never from input), API-6 (identical not-found) and API-7 (self-authorising entry points) are non-waivable.

<!-- check:ownership -->
### Ownership and change

Owner: platform architecture lead; changes require review from security for API-1, API-6 and API-7.

<!-- end -->
