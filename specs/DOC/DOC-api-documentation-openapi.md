---
id: "DOC-api-documentation-openapi"
title: "API documentation (OpenAPI, developer portal)"
parent: "DOC"
order: 2
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 2
syncHash: "c901696c7b8e8775"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 17.2 API documentation (OpenAPI, developer portal)

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

Defines how the external REST API ([[INT-public-api-and-webhooks]] and its children) and outbound webhooks ([[APP-webhooks-outbound]], [[INT-webhook-event-catalogue]]) are described, linted, published and versioned, and what the developer portal provides to integrators: reference, guides, sandbox access and changelog. Internal tRPC routers are typed end to end and are not published.

<!-- section:rules -->
## Rules

- **APIDOC-1** The OpenAPI 3.1 document for each public API family (cases and parties, documents and filings, hearings, tenant admin, aggregator intake) is generated from the Zod schemas and route definitions in `packages/api-contracts`; it is never hand-edited.
- **APIDOC-2** Webhook events are described in AsyncAPI 3, generated from the event schemas in the same package.
- **APIDOC-3** Every operation has `operationId`, summary, description, tags, security scheme, request and response examples (synthetic), all error responses as RFC 9457 problem types from [[APP-api-error-catalogue-problem]], rate-limit headers and idempotency-key behaviour ([[APP-api-versioning-rate-limiting]]).
- **APIDOC-4** Descriptions follow the copy rules in [[DOC-developer-facing-api-copy]] and use glossary terms.
- **APIDOC-5** Contracts are linted with Spectral using our ruleset (naming, pagination, problem types, examples present, no undocumented fields) as a required CI check.
- **APIDOC-6** `oasdiff` compares each PR's documents with the last released version; a breaking change fails unless the PR is labelled `api-breaking`, adds a new major version path, and adds a changelog entry ([[DEP-release-notes-and-change]] CHG-7).
- **APIDOC-7** The developer portal publishes: reference per version, getting-started guide (API client creation, authentication, first call), guides for common tasks (file a case, upload a document with a signed URL, receive and verify webhooks), regional base URLs, rate limits, changelog and deprecation schedule.
- **APIDOC-8** Each region has its own API base URL; docs state that tenants must call the base URL of their home region and that data is not served from other regions ([[MT-data-residency-2]]).
- **APIDOC-9** The "try it" console only calls sandbox tenants in non-production; production keys are never entered in the portal.
- **APIDOC-10** Aggregator-specific guides (for example the intake contract for NSE as an MII for SEBI ODR matters) are published only to that aggregator's authenticated portal space if the contract is not public.

<!-- section:rationale -->
## Rationale

- **APIDOC-1** Generated contracts cannot drift from the code that validates requests.
- **APIDOC-6** Integrators (institutions, aggregators) build long-lived integrations; an unannounced break can stop filings or regulatory status reporting.

<!-- section:tooling -->
## Tooling and configuration

`zod-openapi` (or equivalent) generator in `packages/api-contracts`; AsyncAPI generator; Spectral with `tooling/spectral/ruleset.yaml`; `oasdiff`; developer portal in `apps/developer-portal` rendering OpenAPI and AsyncAPI.

<!-- section:enforcement -->
## Enforcement

APIDOC-1 and APIDOC-2: CI regenerates documents and fails if committed output differs. APIDOC-3 and APIDOC-5: Spectral (required). APIDOC-6: `oasdiff` (required). APIDOC-9: portal configuration points the console at sandbox hosts only, checked by an e2e test.

<!-- section:examples -->
## Examples

Good: `POST /v1/cases` documents `Idempotency-Key` as required, returns `201` with `Location`, and lists `409 idempotency-key-reused` and `422 validation-failed` problem types with synthetic examples.

Bad: an operation with `description: "Creates a matter"` (non-glossary term) and no error responses.

<!-- section:exceptions -->
## Exceptions

Beta endpoints may be published under a `beta` tag with a stability notice; they are excluded from `oasdiff` gating until promoted.

<!-- section:questions -->
## Open questions

- [ ] Public or authenticated developer portal? Proposal: public reference, authenticated sandbox and aggregator-specific guides.
- [ ] API versioning style (path `/v1` vs header) to confirm with [[APP-api-versioning-rate-limiting]].
- [ ] Do we publish SDKs (TypeScript first) generated from OpenAPI?

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Generation drift, Spectral lint and breaking-change detection are required checks; portal sandbox restriction is e2e-tested.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

Synthetic examples only; sandbox-only consoles; regional base URLs documented so integrators keep data in-region.

<!-- check:onboarding -->
### Onboarding and usability

Engineers add an endpoint by adding a Zod schema and route definition; the document, examples and portal page follow. Spectral messages link to the rule in this node.

<!-- check:compliance -->
### Compliance evidence

Documented authentication, rate limits and webhook signing support client security reviews; the changelog supports contractual change notice.

<!-- check:ownership -->
### Ownership and change

Owner: API platform team; content review by content design for descriptions.

<!-- end -->
