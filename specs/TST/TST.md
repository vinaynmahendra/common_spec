---
id: "TST"
title: "Testing and Quality"
parent: null
order: 16
type: "area"
template: "area"
childTemplate: "standard"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 3
syncHash: "37006654ecbde54f"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 16 Testing and Quality

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

Testing and Quality defines how we show, before and after release, that the platform does what its specs say, keeps tenants apart, performs at the volumes our tenants generate, resists attack, is usable by disabled people and that its AI features are accurate enough for legal work. It sets the test layers, the shared test kit and fixture tenants, and which suites gate which pipeline stages.

**In scope**: unit, integration, contract and end-to-end testing ([[TST-unit-integration-contract-and]]); cross-tenant isolation testing ([[TST-multi-tenant-isolation-tests]]); performance and load ([[TST-performance-and-load-testing]]); security testing ([[TST-security-testing]]); accessibility testing ([[TST-accessibility-testing]]); AI evaluations and red-teaming ([[TST-evals-and-ai-testing]]).

**Out of scope**: the pipeline mechanics that run suites ([[DEP-ci-cd-pipelines-build-test]]); vulnerability management process and pen-test vendor management ([[SEC-vulnerability-management]]); production monitoring and synthetic checks ([[OBS-uptime-synthetic-monitoring]]); accessibility conformance reports and statements ([[APP-accessibility-conformance]]).

<!-- section:goals -->
## Goals and non-goals

Proposed targets:
1. Every tenant-owned table and every public API route is covered by an automated cross-tenant isolation test; zero isolation test failures are tolerated on `main`.
2. Every persona journey listed in [[APP-route-groups-per-persona]] has at least one Playwright end-to-end test with automated accessibility checks, run on each preview and in staging per region.
3. Load tests at 2 × the forecast peak for each region pass the latency targets in [[TST-performance-and-load-testing]] before the first production tenant in that region and before each phase boundary.
4. No critical or high security finding older than its SLA in [[SEC-vulnerability-management]] at release time.
5. Every AI feature has an eval set and pass thresholds, and no prompt, model or retrieval change ships without passing them.
6. Flaky tests: fewer than 1% of CI runs fail due to a quarantined or flaky test.

**Non-goals**: a line-coverage target as the main quality measure; manual regression test scripts for routine releases; testing third-party SaaS internals beyond their contracts.

<!-- section:principles -->
## Principles

1. **Test against the real thing where isolation or data integrity is at stake**: Postgres with forced RLS behind PgBouncer in transaction mode, real Redis, Temporal test server; no mocks for those in integration suites.
2. **Synthetic data only.** No production data, documents, recordings or transcripts in any test, fixture, eval set or screenshot, unless an AI eval set has been built under the anonymisation and consent rules in [[TST-evals-and-ai-testing]].
3. **Every bug fix ships with a test that would have caught it.**
4. **Every suite has an owner and a gate**: which pipeline stage it blocks, and who fixes it when it fails.
5. **Fixture tenants represent our real tenant types**: `arb-inst` (arbitral institution), `odr-inst` (SEBI ODR institution), `cord` (CORD tenant), `us-demo` (US region).
6. **Tests are code**: reviewed, linted and owned like production code.

<!-- section:context -->
## Context and boundaries

| Neighbour | What flows | Contract |
|---|---|---|
| [[DEP]] | Suites run as required checks and promotion gates | [[DEP-ci-cd-pipelines-build-test]], [[DEP-environment-promotion-and-multi]] |
| [[MT]] | Isolation requirements to prove | [[MT-automated-tests-that-prove-one]], [[MT-safeguards]] |
| [[SEC]] | Findings and evidence for ISMS | [[SEC-vulnerability-management]], [[SEC-isms-controls]] |
| [[APP]] | Accessibility conformance targets; performance budgets | [[APP-accessibility-wcag-2-1-aa]], [[APP-frontend-performance-budgets]] |
| [[AI]] | Features to evaluate | [[AI-ai-gateway]], [[AI-guardrails]], [[AI-human-in-the-loop]] |
| [[PKG]] | Each package's test contract | `testing` section of each package node |

<!-- section:decisions -->
## Key decisions

- [[ADR-tenant-isolation]] — makes isolation testing a first-class suite rather than part of security testing.
- [[ADR-orm]] — Prisma means isolation tests must cover every model and also raw queries inside `packages/db`.
- [[ADR-workflow-engine]], [[ADR-temporal]] — workflow replay tests and Temporal test server in integration suites.
- Proposed ADR: test runner (Vitest), contract testing approach (OpenAPI-driven for public APIs; Pact only where an external consumer participates).

<!-- section:map -->
## Capability map

| Child | Owns |
|---|---|
| [[TST-unit-integration-contract-and]] | Test layers, tools, locations, coverage policy, fixture tenants, flaky-test policy, e2e journeys |
| [[TST-multi-tenant-isolation-tests]] | RLS catalogue checks, per-model cross-tenant tests, missing-context tests, PgBouncer leak tests, cache/queue/storage/search isolation, API IDOR tests |
| [[TST-performance-and-load-testing]] | Load models per tenant type, scenarios, targets, environments, noisy-neighbour tests |
| [[TST-security-testing]] | SAST, SCA, secrets, DAST, IaC and image scanning, authorisation matrix tests, pen tests, threat modelling |
| [[TST-accessibility-testing]] | Automated checks, manual AT passes, document accessibility checks, user testing |
| [[TST-evals-and-ai-testing]] | Golden datasets, metrics and thresholds, LLM judges, red-teaming, CI gates for AI changes |

<!-- section:phasing -->
## Phasing

| Phase ([[PLAN]]) | Lands |
|---|---|
| 0 | Unit and integration harness with Postgres + PgBouncer + Redis + Temporal; RLS catalogue check; secret scan and SAST; axe in Storybook |
| 1 | Full isolation suite; authorisation matrix tests; first Playwright journeys (sign-in, tenant switch) |
| 3 | E2E journeys for cases and documents; contract tests for public API drafts; first load test |
| 6 | AI eval harness and red-team suite |
| 8 | Full load tests per region, external pen test, manual accessibility audit, DR test linkage |

Isolation tests, security scanning and automated accessibility checks are cross-cutting from Phase 0 and must not be deferred.

<!-- section:risks -->
## Risks and open questions

- [ ] Owner for the area to be named (proposed: QA / engineering excellence lead).
- [ ] Load-test forecasts per region need inputs from product and client success (tenant counts, cases per month, hearing-day peaks).
- [ ] Whether SEBI-regulated tenants require a CERT-In empanelled auditor for security testing evidence is an assumption to be confirmed by legal and the tenant.
- [ ] Building AI eval sets without production case data is hard; see [[TST-evals-and-ai-testing#questions]].
- [ ] Risk: e2e suite run time grows; mitigated by journey-based sharding and preview smoke subsets.

<!-- checks -->
## Template checks

<!-- check:ownership -->
### Ownership and governance

Proposed owner: engineering excellence / QA lead. Reviewers: information security owner for security testing and isolation, accessibility lead for accessibility testing, AI platform lead for evals. Each child suite has a named owning team listed in its node.

<!-- check:boundaries -->
### Scope and boundaries

This area designs and owns suites; [[DEP]] runs them; [[SEC-vulnerability-management]] owns finding triage and SLAs; [[OBS]] owns production synthetic checks. Accessibility conformance reports belong to [[APP-accessibility-conformance]] and consume this area's results.

<!-- check:principles -->
### Principles and enforcement

Principle 1 is enforced by the shared test kit (`@nomology/testing` starts real services; an ESLint rule forbids mocking `@nomology/db` in `*.int.test.ts`). Principle 2 by fixture factories that generate synthetic data and a CI scan of fixtures and snapshots for real-looking personal data patterns. Principle 3 by the PR checklist for `fix:` commits. Principle 4 by a suite registry file listing owner and gate per suite, checked in CI.

<!-- check:compliance -->
### Regulatory and control mapping

Supports ISO/IEC 27001:2022 Annex A security testing in development and acceptance and protection of test information; WCAG 2.2 AA evidence for accessibility statements; ISO/IEC 42001 evaluation evidence for AI features. Test results are retained with the release's change record.

<!-- check:quality -->
### Quality targets

Quality targets inherited by children: isolation 100% table and route coverage; API latency targets from [[TST-performance-and-load-testing]]; WCAG 2.2 AA; OWASP ASVS Level 2 as the security verification target (proposed); AI pass thresholds per feature.

<!-- check:phase -->
### Phasing

Phasing table above; exit for Phase 1: isolation suite green in CI and in staging in all three regions.

<!-- end -->
