---
id: "APP-route-handlers-trpc-for-internal"
title: "API style (internal and external)"
parent: "APP-api-layer"
order: 1
type: "feature"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: "Route Handlers / tRPC for internal calls; REST + OpenAPI for external consumers"
links: []
rev: 4
syncHash: "fd5e54c496f990ee"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 2.3.1 API style (internal and external)

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Route Handlers / tRPC for internal calls; REST + OpenAPI for external consumers

<!-- section:purpose -->
## Purpose and scope

Decides which API style each kind of call uses, so that teams do not mix styles for the same job: tRPC for our own client components, Server Actions for form submissions, Route Handlers for HTTP endpoints that are not called by our React code, and REST with OpenAPI 3.1 for anything external consumers integrate with.

<!-- section:rules -->
## Rules

1. **STYLE-1** Use this table:

   | Caller and job | Style | Location |
   |---|---|---|
   | Our client components reading data interactively (filters, polling, infinite lists) | tRPC query via TanStack Query | `packages/api/src/routers/{persona}` mounted at `/api/trpc/[trpc]` |
   | Our client components performing interactive or bulk mutations (autosave, bulk actions, drag and drop) | tRPC mutation | same |
   | HTML forms and single-entity commands from Server or Client Components (file, accept, publish) | Server Action | `app/**/_actions/*.ts` or `packages/*/actions` ([[APP-server-actions-and-mutation]]) |
   | Server Components reading data | direct call to `@nomology/data-access` (no HTTP) | — |
   | External consumers: tenant systems, aggregators, partners | REST + OpenAPI 3.1, versioned | `/api/v1/*` via `@nomology/rest` |
   | Inbound webhooks from providers (payments, video, messaging receipts, e-sign) | Route Handler | `app/api/hooks/{provider}/route.ts` |
   | Streaming responses (AI drafting), file streaming, SSO callbacks, CSP reports, health | Route Handler | `app/api/...` |
2. **STYLE-2** tRPC is internal only: no external consumer may be given its URL, it has no compatibility guarantee across releases, and it is same-origin with cookies.
3. **STYLE-3** REST routes never use session cookies; they authenticate with OAuth 2.0 client credentials or API keys ([[INT-public-api-and-webhooks]]).
4. **STYLE-4** Domain logic lives in domain packages; tRPC procedures, Server Actions and REST handlers are thin adapters that validate, authorise, call the domain command or query, and map errors.
5. **STYLE-5** A capability exposed both internally and externally shares the domain command and Zod schemas, not the transport.
6. **STYLE-6** Inbound webhook handlers verify signatures before parsing, respond within 5 seconds, and hand work to BullMQ ([[WF-background-jobs-and-queues]]).

<!-- section:rationale -->
## Rationale

- tRPC gives end-to-end types for our own UI without publishing a contract; REST + OpenAPI gives external consumers a stable, documented contract [R1].
- Server Actions give progressive enhancement and simple forms, but they are public POST endpoints with framework-chosen IDs, so they are not suitable for external callers [R2].
- Thin adapters (STYLE-4) mean the same business rule applies whichever door a request came through.

<!-- section:tooling -->
## Tooling and configuration

- tRPC v11 with `@trpc/tanstack-react-query`; fetch adapter in `app/api/trpc/[trpc]/route.ts`
- `@nomology/rest`: a typed router (candidates: Hono mounted in `app/api/v1/[...path]/route.ts`, or ts-rest) with Zod-to-OpenAPI generation; OpenAPI files published per release
- Spectral lint and an OpenAPI diff tool in CI for public routes

<!-- section:enforcement -->
## Enforcement

| Rule | Enforcement |
|---|---|
| STYLE-1 | Code review checklist; ESLint rule forbids `fetch('/api/...')` from client components (must use tRPC client) |
| STYLE-2 | WAF and router: `/api/trpc` rejects requests without session cookie and same-origin headers |
| STYLE-3 | REST middleware rejects cookie-authenticated requests |
| STYLE-4 | Turborepo boundaries: routers and handlers may import domain packages, not Prisma |
| STYLE-6 | Template generator for webhook handlers includes signature verification; test asserts unsigned requests get 401 |

<!-- section:examples -->
## Examples

Good: the secretariat queue uses `secretariat.queue.page` (tRPC) with filters in the URL; the "Change status" dialog calls `secretariat.case.changeStatus`; the same `changeCaseStatus` domain command backs `POST /api/v1/cases/{caseId}/status-changes` for aggregators.

Bad: exposing `/api/trpc/secretariat.queue.page` to an aggregator because "it already returns what they need".

<!-- section:exceptions -->
## Exceptions

Exceptions (for example a Route Handler serving our own client for binary streaming) are recorded in the PR description with security review; STYLE-2 and STYLE-3 are non-waivable.

<!-- section:questions -->
## Open questions

- [ ] Public REST router: Hono or ts-rest (owner: platform architecture; Decision record)
- [ ] Should the public API be served from the same containers as the web app, or a separate service in each region for independent scaling? (owner: platform architecture)

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

STYLE-1 is partly review-based, with a lint rule for client `fetch` to internal paths; STYLE-2, 3 and 6 are enforced by middleware and tests; STYLE-4 by Turborepo boundaries.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

Every style funnels into the same domain commands, which run in tenant transactions; tRPC is closed to external callers; REST never uses cookies, so CSRF is limited to Server Actions and tRPC, both same-origin.

<!-- check:onboarding -->
### Onboarding and usability

The STYLE-1 table is the single decision aid; generators (`pnpm gen procedure`, `pnpm gen action`, `pnpm gen rest-route`, `pnpm gen webhook`) produce code that already follows the rules.

<!-- check:ownership -->
### Ownership and change

Owner: platform architecture lead; reviewed with each change to the public API strategy.

<!-- citations -->
## Citations

```json
[
  {
    "body": "OpenAPI Initiative",
    "id": "R1",
    "ident": "OpenAPI",
    "kind": "standard",
    "title": "OpenAPI Specification v3.1.1",
    "url": "https://spec.openapis.org/oas/v3.1.1",
    "version": "3.1.1"
  },
  {
    "id": "R2",
    "kind": "vendor",
    "title": "Next.js: Server Actions guide",
    "url": "https://nextjs.org/docs/app/guides/server-actions",
    "vendor": "Vercel (Next.js)"
  }
]
```

<!-- end -->
