---
id: "TST-unit-integration-contract-and"
title: "Unit, integration, contract and end-to-end tests (Playwright)"
parent: "TST"
order: 1
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 2
syncHash: "fbb28bc7068324ae"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 16.1 Unit, integration, contract and end-to-end tests (Playwright)

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

Defines the functional test layers every package and app uses: what each layer tests, which tool runs it, where the files live, what data it uses, which pipeline stage it gates and what coverage is expected. Isolation, performance, security, accessibility and AI testing build on these layers and are specified in their own nodes.

<!-- section:rules -->
## Rules

**Layers**

| Layer | Scope | Tool | Location | Runs |
|---|---|---|---|---|
| Unit | Pure functions, state machines, rule evaluation, React components in isolation | Vitest; React Testing Library | `src/**/*.test.ts(x)` | Every PR (affected) |
| Integration | A package against real Postgres (forced RLS, PgBouncer transaction mode), Redis and Temporal test server | Vitest + `@nomology/testing` service harness | `src/**/*.int.test.ts` | Every PR (affected) |
| Workflow | Temporal workflows with time skipping; replay of recorded histories | `@temporalio/testing` | `packages/workflows/test/` | Every PR touching workflows |
| Contract | Public REST API against its OpenAPI document; webhooks against the AsyncAPI document; tRPC router input/output schemas | Schemathesis or equivalent property-based OpenAPI tester; schema snapshot tests | `packages/api-contracts/test/` | Every PR touching contracts; nightly full |
| End-to-end | Persona journeys through the browser | Playwright | `apps/web/e2e/<route-group>/` | Smoke on preview; full in staging per region |

**Rules**
- **TEST-1** Every package defines `test` and, if it touches a datastore or Temporal, `test:integration`. Mocking `@nomology/db`, Postgres, Redis or Temporal in integration tests is forbidden.
- **TEST-2** Integration tests use `@nomology/testing` fixtures: tenants `arb-inst`, `odr-inst`, `cord`, `us-demo`, with one user per persona per tenant, created through factories (`createCase`, `createParty`, `createHearing`). All values are synthetic; names come from a fixed synthetic list per locale.
- **TEST-3** Each test runs inside its own tenant-scoped transaction or a freshly seeded schema, so tests can run in parallel without order dependence.
- **TEST-4** Domain state machines ([[WF-entity-state-machines]]) have a table-driven unit test covering every allowed and every forbidden transition.
- **TEST-5** Every Rules and Decision Engine table ([[PKG-rules-and-decision-engine]]) has example-based tests per tenant variant, and deadline arithmetic ([[PKG-calendars-and-deadline]]) is tested across time zones, holidays and daylight-saving changes in the US.
- **TEST-6** Every public API operation has a contract test for success, validation failure, not-found and forbidden responses, checking RFC 9457 problem bodies ([[APP-api-error-catalogue-problem]]).
- **TEST-7** Each persona journey has at least one Playwright test, tagged `@smoke` or `@full`, signing in as a fixture user; journeys include: party files a statement of claim, counsel uploads documents, secretariat bulk-assigns cases, neutral issues a procedural order, transcriber submits a transcript, tenant admin changes branding, platform admin provisions a tenant.
- **TEST-8** Coverage is reported per package; the PR check fails if line coverage of changed lines is below 80% (proposed). There is no global percentage target.
- **TEST-9** Every `fix:` PR includes a test that fails without the fix.
- **TEST-10** Flaky tests follow CICD-13: quarantine within one working day, fix or delete within 10.
- **TEST-11** Screenshots, traces and videos from e2e runs contain only synthetic data and are kept for 14 days.

<!-- section:rationale -->
## Rationale

- **TEST-1** The most damaging bugs on this platform (tenant context not set, wrong transaction scope under PgBouncer) are invisible with mocks.
- **TEST-5** Missed deadlines are a legal harm; deadline logic is tested more heavily than ordinary code.
- **TEST-8** Changed-line coverage catches untested new code without encouraging tests written only to raise a global number.

<!-- section:tooling -->
## Tooling and configuration

- Vitest (workspace mode per package), React Testing Library, MSW for third-party HTTP providers only.
- `@nomology/testing`: Testcontainers-based harness (`startStack({ postgres, pgbouncer, redis, temporal })`), factories, fixture tenants, persona sign-in helpers for Playwright.
- Playwright with projects per browser (Chromium, Firefox, WebKit) and per route group; `@axe-core/playwright` for accessibility checks ([[TST-accessibility-testing]]).
- Contract tooling: OpenAPI 3.1 documents generated from Zod schemas ([[DOC-api-documentation-openapi]]); `oasdiff` for breaking changes; Pact only if an external consumer such as an aggregator agrees to publish contracts [R1].

<!-- section:enforcement -->
## Enforcement

| Rule | Enforcement |
|---|---|
| TEST-1 | ESLint rule forbidding `vi.mock('@nomology/db')` in `*.int.test.ts`; MONO-9 script check |
| TEST-2, TEST-11 | Fixture scan job for real-looking emails, phone numbers and ID formats outside the synthetic list |
| TEST-4 | State machine definitions export their transition table; a generic test asserts every pair is covered |
| TEST-6 | Contract test generator fails if an operation lacks the four response cases |
| TEST-7 | Route-group registry check: every route group has at least one `@smoke` journey |
| TEST-8 | Changed-line coverage check (required) |
| TEST-9 | PR checklist for `fix:` titles; reviewer confirms |

<!-- section:examples -->
## Examples

Good:

```ts
it('odr-inst secretariat cannot see arb-inst cases', async () => {
  const { odr, arb } = await fixtures.tenants();
  await createCase(arb, { title: 'Synthetic v. Example' });
  const cases = await asUser(odr.secretariat, () => listOpenCases());
  expect(cases).toHaveLength(0);
});
```

Bad: a unit test that mocks `prisma.case.findMany` to return one case and asserts the UI shows it, presented as proof of access control.

<!-- section:exceptions -->
## Exceptions

Packages with no runtime code (for example `tooling/*`) are exempt from TEST-8. Other exceptions follow [[FND-governance#exceptions]].

<!-- section:questions -->
## Open questions

- [ ] Confirm changed-line coverage threshold (80% proposed) and whether domain packages need a higher one.
- [ ] Property-based OpenAPI testing tool choice (Schemathesis is Python; acceptable in CI?).
- [ ] Which aggregators (for example NSE for SEBI ODR matters) would participate in consumer-driven contract testing, if any?
- [ ] Browser matrix for e2e: all three engines on every staging run, or WebKit nightly only?

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Layer rules are enforced by lint (no mocks for datastores in integration tests), generators (contract cases), registry checks (journey per route group), and the changed-line coverage gate. Only TEST-9 depends on reviewer judgement.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

Tenant isolation is tested in integration with real RLS and PgBouncer; synthetic data only, scanned in CI; e2e artefacts expire after 14 days; journeys include axe checks for WCAG 2.2 AA.

<!-- check:onboarding -->
### Onboarding and usability

`pnpm test` runs unit tests for affected packages; `pnpm test:integration` starts the stack via Testcontainers. Factories and persona helpers make the right way the short way; examples live in each package's README.

<!-- check:compliance -->
### Compliance evidence

CI test history per release is retained with the change record, supporting ISO/IEC 27001:2022 security testing in development and acceptance; synthetic fixtures support the control on protection of test information.

<!-- check:measurement -->
### Adoption measurement

Tracked: changed-line coverage by package, flaky rate, e2e run time per region, defects found in production that had no test at the relevant layer (reviewed in post-incident reviews).

<!-- check:ownership -->
### Ownership and change

Owner: engineering excellence / QA lead. Package owners own their package's tests.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Consumer-driven contract testing: consumers record expectations that are verified against the provider.",
    "id": "R1",
    "kind": "vendor",
    "title": "Pact documentation",
    "url": "https://docs.pact.io/",
    "vendor": "Pact Foundation"
  }
]
```

<!-- end -->
