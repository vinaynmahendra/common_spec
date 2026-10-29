---
id: "ADR-policy-engine"
title: "Authorisation policy engine"
parent: "ADR"
order: 13
type: "decision"
template: "adr"
status: "draft"
owner: null
indicative: false
summary: "How are authorisation decisions evaluated? Proposed: in-process typed TypeScript policies in @nomology/authz over Postgres facts under forced RLS, with predicate and Prisma-filter forms, deny-overrides-permit, and an AuthZEN-shaped interface; Cedar is the fallback."
links: []
rev: 1
syncHash: "e514b2e1273a7f49"
createdAt: "2026-10-28T09:00:00Z"
updatedAt: "2026-10-28T09:00:00Z"
updatedBy: null
---

# 19.11 Authorisation policy engine

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> How are authorisation decisions evaluated? Proposed: in-process typed TypeScript policies in @nomology/authz over Postgres facts under forced RLS, with predicate and Prisma-filter forms, deny-overrides-permit, and an AuthZEN-shaped interface; Cedar is the fallback.

<!-- section:context -->
## Context and problem

**Question:** how should `@nomology/authz` evaluate authorisation decisions inside a tenant: who may do which action on which resource, and which rows a list or search query may return?

Tenant separation is already settled: forced Postgres Row-Level Security on `tenant_id` ([[ADR-tenant-isolation]]), reached only through the Prisma extension ([[ADR-orm]]). This record decides the layer **above** RLS, which the overhaul specified in detail but left as a proposed choice ([[PKG-policy-engine-permission-matrix#questions]], [[PKG-authorization#questions]]).

**What the engine must handle** (all already specified):

| Need | Where it is specified | Why it is hard |
|---|---|---|
| Scoped tenant roles (tenant, unit, case type, case) built from permission sets with muting | [[PKG-roles-and-permission-sets]], [[PKG-permission-catalogue]] | About 50 case permissions × 11 personas, plus admin domains |
| Case-level party roles derived from domain records (party, counsel, tribunal seat, case manager, hearing assignment) with side and time windows | [[PKG-rbac-abac-case-level-party]] | Relationship data that changes with every procedural step; must change in the same transaction as the domain record |
| Attribute conditions: stage, document tier, exchange, addressee, sealed / need-to-know | [[PKG-rbac-abac-case-level-party#matrix]] | Facts live in domain tables, not in an authorisation store |
| Ethical walls and need-to-know lists that override every allow, including JIT, break-glass and support grants | [[PKG-ethical-walls-conflict-based]], [[PKG-jit-and-break-glass]] | Deny-first semantics; exclusions are expensive in relationship engines |
| **List filtering** ("search with permissions") for case lists, documents, search, notification recipients and AI retrieval | AUTHZ-FR-3 in [[PKG-authorization]], [[PKG-search]], [[AI-rag]] | Filters must run inside the RLS-protected Postgres query, never post-filtering |
| Explanations and simulation, including "as of" a past date | [[PKG-access-explainer]] | Needs every allow path, deny rule and condition result, not only allow / deny |
| Non-human principals and AI on-behalf intersection | [[PKG-non-human-principals]] | Two evaluations per call, per tool call |
| Revocation on the next request; p95 ≤ 5 ms per decision | AUTHZ-FR-8, POL-FR-5 | Rules out stale caches and remote hops on hot paths |

**Affected parts:** every server entry point (Server Actions, tRPC, Route Handlers, public and admin API, Temporal Activities, BullMQ jobs, AI tools), search and derived copies, the admin console access pages ([[APP-user-and-access-admin]]), and the authz tables ([[PKG-authorization-data-model]]).

**Out of scope:** tenant isolation (decided), authentication strength and step-up rules ([[PKG-authentication-policies]], which have their own evaluator, and [[ADR-identity-platform]]), and the language tenants use for blueprint and automation conditions ([[ADR-expression-and-rules-language]]). Tenants never write authorisation policy; they configure roles, permission sets, scopes and settings ([[PKG-settings-access-control]]).

<!-- section:drivers -->
## Decision drivers

| # | Driver | Weight | Why it matters here |
|---|---|---|---|
| D1 | **List filtering inside the database query** | High | AUTHZ-FR-3: case lists, document lists, search and AI retrieval must apply permission filters in the Postgres query under RLS; a SEBI ODR tenant may have hundreds of thousands of cases ([[PKG-authorization-data-model#volume]]: `authz_case_role` 10M rows at 5 years) |
| D2 | **Consistency with domain writes and fast revocation** | High | Case roles are written in the same transaction as the domain record (ABAC-FR-6); revocation applies on the next request (AUTHZ-FR-8); walls apply on the subject's next request (WALL-FR-4) |
| D3 | **Latency** | High | p95 ≤ 5 ms warm and ≤ 15 ms on cache miss per decision (POL-FR-5); several decisions per page |
| D4 | **Explainability and auditability** | High | Explainer must return paths, deny rules and condition results and agree with `can()` (AEX-FR-1, agreement test); every decision carries policy and catalogue versions (AUTHZ-FR-7) |
| D5 | **Deny-first rules (walls, need-to-know, SoD, seals)** | High | Deny always overrides allow, including elevation and break-glass |
| D6 | **Residency and operations per region** | High | India, Singapore and US stacks (plus Azure where a client requires it); no cross-region call for a decision ([[PKG-authorization]]) |
| D7 | **Team skills and one codebase** | Medium | TypeScript, Next.js, Prisma, Temporal; fact loaders and Prisma filter compilation already exist in that language |
| D8 | **Correctness assurance** | Medium | Ability to prove or test that a change does not widen access (matrix-generated tests, mutation tests, or formal analysis) |
| D9 | **Reversibility and interoperability** | Medium | An external engine or a non-TypeScript caller must be possible later without rewriting callers |
| D10 | **Cost, licence and maturity** | Medium | Small platform team; open licences preferred; no new paid dependency on the hot path |

<!-- section:decision -->
## Decision

**Status: Proposed — awaiting CTO decision.**

**Recommended option: in-process, typed TypeScript policies in `@nomology/authz`, evaluated over facts loaded from the regional Postgres under forced RLS, with an AuthZEN-shaped decision interface.** This is option A in the options table. It confirms the candidate from the overhaul and adds three commitments that keep it reversible.

**What is decided**

1. **Engine.** Policies are TypeScript functions in a versioned policy bundle (`packages/authz/policies/*.ts`), one per catalogue permission, built from shared combinators (`when`, `or`, `and`, `hasCaseRole`, `inScope`, `tier`, `walled` …) as in [[PKG-policy-engine-permission-matrix#policy]]. No separate policy language, sidecar or authorisation service on the request path.
2. **Relationship data stays in Postgres.** Case-level roles are a Zanzibar-style projection (`authz_case_role`, one row per principal, case and role, with side and validity window) in the same regional database and the same transaction as the domain record [R16]. Scoped tenant roles live in `authz_role_assignment`. There is no second authorisation datastore.
3. **Two forms of every policy.** Each allow and deny rule has a predicate form (`can`, `assert`) and a filter form (`where`) that compiles to Prisma `where` fragments; the harness proves both agree on the generated corpus (ABAC-FR-5). This is how D1 is met: the database does the filtering, under RLS.
4. **Fixed combining rule.** Deny rules (walls, need-to-know, SoD runtime rules, seals, stage locks, legal hold) are evaluated before allow rules and override them; default deny. These are the same semantics as Cedar's forbid-overrides-permit [R3], so the bundle can be translated later if needed.
5. **AuthZEN-shaped interface.** The library signature takes subject, action, resource and context and returns a decision with reasons, matching the OpenID AuthZEN Authorization API 1.0 request and response shape (Access Evaluation, Access Evaluations and Resource Search) [R1][R2] (POL-FR-8). An HTTP endpoint that speaks AuthZEN 1.0 is **not** built now; it is built only when a caller outside the TypeScript monorepo needs decisions (see revisit triggers).
6. **Tracing evaluator for explanations.** `explain()` runs the same policy code with a tracer that records every path, deny rule and condition; it is not a second implementation (AEX-FR-5, agreement test).
7. **Caching** as specified: grant sets and wall sets cached in regional Redis keyed by the principal's grant epoch; decisions never cached across requests ([[PKG-policy-engine-permission-matrix#policy]]).

**Why, against the drivers**

- **D1 list filtering:** a policy compiled to a Prisma filter runs inside the RLS-protected query, with the indexes already designed in [[PKG-authorization-data-model#indexes]]. Relationship services answer "list objects" by returning ID lists or recommend building a local index from a change feed for large sets [R6], which would recreate this design with an extra copy. Cedar's partial evaluation, which would be the way to produce filters, is still experimental [R4].
- **D2 consistency:** facts are read in the same transaction as the write and the grant epoch is bumped in that transaction, so revocation and walls take effect on the next request without cross-store synchronisation. A separate relationship store needs consistency tokens or fully consistent reads to avoid the "new enemy" problem [R10].
- **D3 latency:** no network hop; budget is one fact query plus in-memory evaluation.
- **D4 explainability:** the tracer can report condition-level detail (for example `exchanged = false`) that the explainer requires; Cedar diagnostics report the determining policies and errors but not each condition's result [R3].
- **D5 deny-first:** fixed in the evaluator, tested on every matrix row.
- **D6 residency and operations:** nothing new to run in India, Singapore, US or Azure; policy bundle and catalogue deploy with the application in each region.
- **D7 skills:** one language and one review process for domain code and policies.
- **D8 assurance:** compensated by generated allow and deny tests (about 1,650), mutation testing of combinators, dual-form tests and the explainer agreement test ([[PKG-policy-engine-permission-matrix#verification]]). This is weaker than formal analysis; see consequences.
- **D9 reversibility:** the AuthZEN-shaped interface and Cedar-compatible combining rule keep a later move to Cedar or an external PDP a contained change.
- **D10 cost:** no licence, no new infrastructure.

**Scope of the decision:** all authorisation decisions inside a tenant for the web app, admin and public APIs, workers, Temporal Activities, automation actions and AI tools, in every region and on Azure deployments. It also covers the derived-copy rule: search, notification recipient resolution, people pickers, report drill-down and AI retrieval call the same policies. It does **not** decide authentication strength ([[ADR-identity-platform]]), the tenant-authored rules language ([[ADR-expression-and-rules-language]]) or whether a second RLS layer enforces `tribunal_only` (an open question kept in [[PKG-authorization#questions]]).

<!-- section:consequences -->
## Consequences

| Stakeholder | Easier | Harder |
|---|---|---|
| Developers | One language; policies use the same fact loaders and Prisma types; list filters come free from the filter form | Every policy needs both forms and must pass dual-form tests; combinators must stay pure (no I/O outside fact loaders) |
| Security lead | One package to review; decisions carry bundle and catalogue versions | No formal analysis: assurance rests on generated tests, mutation tests and review of `matrix.yaml` diffs; the security lead is a CODEOWNER bottleneck |
| Platform / DevOps | Nothing new to run per region; policy bundle ships with the app | Policy bundle and catalogue release must deploy together per region ([[DEP-environment-promotion-and-multi]]) |
| Tenant admins and auditors | Explainer and simulator use the real policy code, so answers match enforcement | Tenants cannot author policies; anything new needs a Nomology release (by design) |
| Future integrations | AuthZEN-shaped interface | A non-TypeScript service cannot call the engine until we build the AuthZEN HTTP endpoint |

**New failure modes**
- Predicate and filter forms disagree (list shows an item the detail page denies). Mitigated by the dual-form harness; residual risk sits in rare fact combinations not in the corpus.
- A policy with heavy fact loading slows pages. Mitigated by one-query fact loaders and the p95 budget in [[TST-performance-and-load-testing]].
- The case-list filter degrades as `authz_case_role` grows (10M rows at 5 years). Mitigated by partial indexes and the partition trigger in [[PKG-authorization-data-model#volume]].

**Follow-up work (to be ticketed under [[PKG-authorization]]):** the matrix-to-test generator; the tracing evaluator; the dual-form harness; the entry-point coverage CI check; the policy-engine spike below; an internal `AuthzDecisionRequest` type aligned field-by-field with AuthZEN 1.0.

**Cost:** no licence or infrastructure cost. Engineering cost is the policy bundle and test tooling already planned in the authz nodes (assumption: 2–3 engineer-months for engine, harness and tracer, excluding writing the 50+ policies).

<!-- section:confirmation -->
## Confirmation

**Automated checks (blocking in CI)**
- **Entry-point coverage:** CI enumerates Server Actions, tRPC procedures, Route Handlers, Temporal Activities, BullMQ handlers and AI tools and fails if any lacks a declared permission or `@public` ([[PKG-authorization#verification]]).
- **No other decision path:** ESLint `no-restricted-imports` blocks authz Prisma models outside `packages/authz` and `packages/db`; a rule forbids importing any policy engine SDK (`@cedar-policy/*`, `@openfga/*`, `@authzed/*`, OPA clients) outside `packages/authz`.
- **Matrix tests:** about 1,650 generated allow and deny tests from `matrix.yaml`, against real Postgres with RLS through PgBouncer ([[TST-multi-tenant-isolation-tests]]).
- **Dual-form agreement:** predicate and filter results equal on the generated corpus (ABAC-FR-5). Zero mismatches allowed.
- **Explainer agreement:** `explain().decision == can().allow` on the corpus (AEX verification).
- **Mutation testing:** at least 95 % of combinator mutants killed (assumption: threshold to be agreed with the security lead).
- **Deliberately failing case:** a fixture policy that widens access exists in the test suite and must make CI fail; if it ever passes, the harness is broken.

**Measurable production checks**

| Metric | Target | Source |
|---|---|---|
| Decision latency | p95 ≤ 5 ms warm, ≤ 15 ms cache miss | `authz.decision.duration` histogram per region |
| Case-list filter | p95 ≤ 20 ms at 5-year volume | Load test in [[TST-performance-and-load-testing]] |
| Revocation | Next request denied; realtime channels drop ≤ 60 s | Revocation timing test |
| Decisions for unknown permissions | 0 | `nomo.sec.authz_fail` with reason `unknown_permission` ([[OBS-security-events]]) |
| Access-control defects | No high-severity authorisation finding open past its SLA; every fixed bug gets a regression test | Pen test and bug tracker |

**Spike / proof of concept (2 weeks, before the authz package is built out)**

Implement three representative policies in **both** A (TypeScript) and B (Cedar via `cedar-wasm`): `case.document:read` with the four tiers and exchange; `case:list` with unit and case-type scopes; and an exclusion wall plus a sealed need-to-know case. Run them on a seeded India-sized dataset (10M `authz_case_role` rows, 2 tenants).

| Exit criterion | A must meet | Switch to B only if |
|---|---|---|
| Decision p95 (warm / miss) | ≤ 5 ms / ≤ 15 ms | B meets the same budget including fact serialisation |
| Case-list filter p95 | ≤ 20 ms | B's filter (via `tpe`) is generated without hand-written SQL per policy and meets 20 ms |
| Predicate–filter agreement | 100 % on corpus | B achieves 100 % |
| Explainer output | Paths, denies and condition results | B gives the same detail without a parallel implementation |
| Developer effort | Baseline | B is not more than 1.5× A's effort for the three policies |

If A meets all criteria, accept this ADR. If A misses a criterion and B meets all of them, reopen this ADR with B. If neither meets the list-filter criterion, reopen with option C (relationship service) as the candidate for case lists only.

**Exceptions:** any code path that decides access without `@nomology/authz` needs an ADR exception approved through [[FND-governance]] and is listed in an allow-list file under CODEOWNERS.

<!-- section:options -->
## Options considered

Option A is recommended. Claims are from official documentation where cited; other numbers are **assumptions** for comparison and are marked (A).

**1. Fit to the decision drivers**

| Option | D1 list filtering | D2 consistency and revocation | D3 latency | D4 explain and audit | D5 deny-first (walls) | D8 assurance |
|---|---|---|---|---|---|---|
| **A. In-process TypeScript policies + Postgres facts (recommended)** | Policy compiles to Prisma filter; runs under RLS in one query | Same transaction as domain write; epoch bump | In-process; target p95 ≤ 5 ms | Tracing evaluator: paths, denies, conditions, versions | Built into evaluator order | Generated tests, mutation tests; no formal proof |
| **B. Cedar embedded** (Rust core via `cedar-wasm` in Node [R5]) | Needs partial evaluation to make filters; `partial-eval` and type-aware `tpe` are experimental in cedar-policy 4.14.0 [R4]; we would still write SQL generation | Entities supplied per request from Postgres, so consistent if we load facts as in A | In-process WASM; fact loading cost same as A plus serialisation (A) | Decision plus determining policies and errors [R3]; condition-level trace would need extra work | Native: forbid overrides permit, default deny [R3] | Strong: schema validation and a symbolic compiler that checks policy properties [R5] |
| **C1. OpenFGA** (Zanzibar-style service per region) | ListObjects, or a local index built from the changes endpoint for large result sets [R6] | Second store; tuples written from Postgres via outbox, so not in the same transaction; staleness window unless consistency is forced | Network hop per check; batch check helps (A: 2–10 ms per hop in-region) | Check, Expand, ListObjects and ListUsers queries [R9]; condition detail limited to CEL conditions [R7] | Exclusions (`but not`) are supported but are the expensive relation type for list queries [R6] | Model tests; no formal analysis |
| **C2. SpiceDB** (Zanzibar-style service per region) | LookupResources returns IDs to feed into SQL (same pattern as C1) | ZedTokens give "at least as fresh" reads; without them the new-enemy window exists; fully consistent mode bypasses cache [R10] | Network hop; caching depends on consistency mode | Check plus debug traces (A) | Exclusion supported (A) | Schema validation and assertion tests (A) |
| **D. OPA / Rego** (sidecar or library) | Partial evaluation with compile API that produces SQL conditions [R13][R14]; Prisma would need our own translator (A) | Data pushed to OPA as bundles or loaded per request; bundles lag unless we pass facts per request (A) | Sidecar hop per decision or WASM in-process (A) | Decision logs and tracing (A) | Expressible; not the default combining rule | Rego unit tests; no formal analysis (A) |
| **E. External AuthZEN 1.0 PDP** (any engine behind the standard API [R1]) | AuthZEN Resource Search returns resource lists with paging [R1]; filters still built from IDs | Depends on engine behind it | Network hop | Depends on engine; the standard decision response carries only `decision` and optional `context` [R1] | Depends on engine | Depends on engine |

**2. Cost, operations, residency, skills, lock-in, maturity and licence**

| Option | Infra cost per region (A) | Operational burden: India / Singapore / US (and Azure) | Data residency | Team skills (TypeScript, Next.js, Prisma, Temporal) | Lock-in | Maturity | Licence |
|---|---|---|---|---|---|---|---|
| **A** | None beyond existing app, Postgres and cache Redis | None new; same deploy in every region | All grants, facts and decisions stay in the regional Postgres | Native | Low: our code; interface shaped to AuthZEN | Our code; patterns proven in the spec; maturity is what we build | Our code |
| **B** | None (library) | None new; WASM module per app and worker image | Same as A | New policy language and schema for reviewers; Rust/WASM toolchain for upgrades | Low to medium: Cedar is open source; policies would need rewriting to leave | cedar-policy 4.14.0; core stable, partial evaluation experimental [R4] | Apache-2.0 [R5] |
| **C1** | 2–3 service tasks plus a Postgres database per region (A: US$300–800/month per region); ×3 regions plus Azure | New stateful service, migrations, backups, upgrades and on-call in each region; outbox sync from Postgres | A second store of tenant relationship data per region; must keep it in-region and prove tenant isolation without RLS | New modelling language; Go service operated by us | Medium: model and tuples are engine-specific | CNCF incubating since October 2025 [R9]; Postgres 14+, MySQL 8, SQLite beta [R8] | Apache-2.0 [R8] |
| **C2** | Similar to C1; Postgres 15+ with `track_commit_timestamp` for Watch [R11] (A: US$300–900/month per region) | As C1; Postgres recommended only for single-region deployments, which matches one SpiceDB per region [R11] | As C1 | New schema language; Go service | Medium | Mature open-source project; commercial managed offering also exists [R12] | Apache-2.0 [R12] |
| **D** | Sidecar CPU per task, or bundle server (A: under US$100/month per region) | Bundle build and distribution per region; sidecar health | As A if facts passed per request; otherwise bundle data replicated per region | Rego is a new language for the team | Medium | CNCF graduated [R15] | Apache-2.0 [R15] |
| **E** | Depends on engine | Depends on engine; adds a network service | Depends on engine | Interface only | Low at the interface | AuthZEN 1.0 approved as a Final Specification in January 2026 [R2] | OpenID Foundation specification |

**Why not the others**

- **B (Cedar)** is the strongest alternative and the designated fallback. It loses today on D1 (filters need experimental partial evaluation plus our own SQL generation), D4 (condition-level explanations) and D7 (second language). It wins on D8. The spike below keeps it honest.
- **C1 / C2 (relationship services)** suit case roles well, but every tenant relationship would live in a second store per region that is not covered by RLS and is not written in the same transaction (fails D2 as specified), list filtering still ends with ID lists fed back into Postgres (D1), and they add a stateful service to run in four places (D6).
- **D (OPA)** shares Cedar's filter problem without Cedar's analysis tools and adds Rego.
- **E (AuthZEN)** is an interface, not an engine. We adopt its shape now (decision point 5) and keep the HTTP endpoint as a later step.

<!-- section:revisit -->
## When to revisit

Reopen this decision if any of the following happens:

- **Tenant-authored policy:** a product decision lets tenants write authorisation rules beyond roles, permission sets, scopes and settings. Then an analysable policy language (Cedar) becomes the default candidate.
- **Non-TypeScript caller:** a service outside the monorepo (for example a bespoke deployment such as the HKIAC case management platform, a partner system, or a document service in another language) needs decisions. First step: build the AuthZEN 1.0 HTTP endpoint over the same bundle; reopen only if that is not enough.
- **Performance:** decision p95 exceeds 5 ms warm or the case-list filter exceeds 20 ms at p95 for two consecutive releases after indexing and partitioning per [[PKG-authorization-data-model#volume]].
- **Correctness:** two or more high-severity access-control defects in 12 months that generated tests did not catch.
- **Cedar maturity:** Cedar's type-aware partial evaluation leaves experimental status [R4] and can emit filters we can translate to Prisma; re-run the spike.
- **Scale of relationships:** sharing patterns appear that need graph traversal (for example nested groups of firms across many cases, or cross-tenant sharing) that a SQL `EXISTS` cannot serve within budget.
- **Audit or contract demand:** a client or certification requires formal verification of access policies or a standard external PDP.
- **Scheduled review:** 12 months after acceptance, with the spike results and the year's access-control defect history.

<!-- section:questions -->
## Open questions

- [ ] Accept that assurance rests on generated and mutation tests rather than formal policy analysis (Cedar), at least until the revisit triggers fire. (CTO)
- [ ] Will tenants ever author authorisation rules themselves (beyond roles, sets, scopes and settings)? This is the main trigger for a policy language. (CTO, product)
- [ ] Does any bespoke or partner deployment (for example the HKIAC case management platform) need to call our decisions from outside the TypeScript monorepo in the next 18 months? If yes, schedule the AuthZEN endpoint. (CTO)
- [ ] Agree the mutation-testing threshold and the spike's effort criterion. (Security lead)
- [ ] Should a second RLS policy enforce the `tribunal_only` tier in the database? Kept open in [[PKG-authorization#questions]]; not decided here. (Security lead)
- [ ] Record the security reviewer and date for this ADR. (Security lead)

<!-- section:notes -->
## More information

- **Refines, does not change:** [[ADR-tenant-isolation]] (layer 1, forced RLS, stays the outer boundary; every policy runs inside the tenant transaction) and [[ADR-orm]] (filters are Prisma `where` fragments; raw SQL only through the tenant extension).
- **Related proposed decisions:** [[ADR-identity-platform]] (produces the `Principal` this engine trusts), [[ADR-expression-and-rules-language]] (tenant conditions in blueprints and automations are a different language for a different purpose; authorisation conditions stay in code).
- **Design references:** Zanzibar for relationship tuples [R16]; AuthZEN 1.0 for the interface shape [R1]; Cedar for combining semantics [R3]; OpenFGA guidance on search with permissions [R6], which shows why list filtering is the deciding factor.
- Implementation detail lives in [[PKG-policy-engine-permission-matrix]] and [[PKG-authorization-data-model]]; this record only fixes the choice.

<!-- checks -->
## Template checks

<!-- check:significance -->
### Significance

Significant: every request, job, workflow step, AI tool call, list and search query depends on it, and it is the main control behind case confidentiality (side, tier, walls). Reversing it after the 50+ policies and the test harness exist would take an estimated 1–2 engineer-months at 6 months and 3–5 at 18 months (assumption), mainly for filter generation and the explainer. It is one decision (how decisions are evaluated); it does not decide tenant isolation ([[ADR-tenant-isolation]]), authentication ([[ADR-identity-platform]]) or the tenant rules language ([[ADR-expression-and-rules-language]]). The context is phrased so that any option could answer it.

<!-- check:options -->
### Options and evidence

Five options (TypeScript in-process, Cedar embedded, OpenFGA, SpiceDB, OPA, plus AuthZEN as an interface) are compared against the same ten drivers in two tables, including infrastructure cost per region, operational burden in India, Singapore, US and Azure, residency, team skills, lock-in, maturity and licence. Engine facts are cited to official documentation [R1]–[R16]; costs and latencies are labelled assumptions. The decisive evidence (list filtering under RLS and consistency with domain writes) is tested in the two-week spike against Cedar before build-out. The choice fits Prisma, forced RLS, PgBouncer transaction pooling and Temporal Activities re-checking permissions; no conflict with existing ADRs.

<!-- check:compliance -->
### Regulatory, residency and tenancy fit

- **Residency:** unaffected; grants, facts and decisions stay in the regional Postgres and cache Redis; no decision needs a cross-region call. Options C1 and C2 would have added a second regional store of tenant relationship data.
- **Isolation:** strengthened, not changed: every policy runs inside the RLS-protected tenant transaction; filters only add conditions to RLS queries.
- **Sub-processors:** none added.
- **Controls:** ISO/IEC 27001:2022 Annex A 5.15 (access control), 5.18 (access rights), 8.2 (privileged access) and 8.3 (information access restriction); SOC 2 CC6.1–CC6.3; DPDP and GDPR security safeguards. Evidence: generated matrix and test report per release, explainer audit, policy bundle versions in decisions.
- **Audit:** decisions with `auditRead` obligations and denials of sensitive actions are audited with policy and catalogue versions ([[PKG-audit-trail]]).
- **Review:** security reviewer and date to be recorded before acceptance.

<!-- check:consequences -->
### Consequences and costs

Downsides are stated per stakeholder: no formal analysis, two forms per policy, security lead as reviewer bottleneck, no direct use by non-TypeScript callers, and tenants unable to author policies. New failure modes (filter and predicate disagreement, slow fact loaders, growth of `authz_case_role`) each have a named mitigation. Running cost is nil; build cost is estimated as an assumption. Follow-up work is listed for ticketing under [[PKG-authorization]].

<!-- check:reversibility -->
### Reversibility and revisit triggers

We would find out from the measurable checks (decision and filter latency, missed access-control defects) and the revisit triggers. The exit path is kept cheap by three choices made now: the AuthZEN-shaped interface (callers do not change), the Cedar-compatible deny-overrides-permit combining rule (policies translate one-to-one), and relationship data kept as tuple-like rows in `authz_case_role` (exportable to a relationship engine). Estimated exit effort: 1–2 months to Cedar, 2–4 months to a relationship service for case lists (assumptions). Scheduled review 12 months after acceptance.

<!-- check:confirmation -->
### Confirmation

Blocking CI checks: entry-point coverage, restricted imports, about 1,650 matrix tests on real Postgres with RLS through PgBouncer, dual-form agreement, explainer agreement and mutation testing, plus a deliberately widening fixture that must fail. Production metrics with targets for latency, revocation and unknown permissions. A two-week spike against Cedar with explicit exit criteria. Exceptions go through [[FND-governance]] with an allow-list under CODEOWNERS.

<!-- check:linked -->
### Linked and lifecycle

Governs [[PKG-authorization]], [[PKG-policy-engine-permission-matrix]], [[PKG-rbac-abac-case-level-party]], [[PKG-ethical-walls-conflict-based]], [[PKG-access-explainer]], [[PKG-permission-catalogue]], [[PKG-roles-and-permission-sets]], [[PKG-authorization-data-model]], [[PKG-jit-and-break-glass]], [[PKG-separation-of-duties]], [[PKG-non-human-principals]], [[PKG-support-access-and-impersonation]], [[PKG-settings-access-control]]; derived-copy consumers [[PKG-search]], [[AI-rag]], [[WF-ai-steps-and-agents]], [[WF-automation-rules]], [[PKG-notifications]], [[RPT-report-infrastructure]], [[PKG-encryption-at-rest-signed-urls]]; surfaces [[APP-user-and-access-admin]], [[INT-tenant-admin-api]], [[APP-admin-copilot]]; tests [[TST-multi-tenant-isolation-tests]], [[TST-performance-and-load-testing]]; operations [[PKG-caching]], [[INF-redis]], [[OBS-security-events]], [[SEC-access-reviews]]. Depends on [[ADR-tenant-isolation]] and [[ADR-orm]]; related to [[ADR-identity-platform]] and [[ADR-expression-and-rules-language]]. The governed nodes should add a 'Decided by [[ADR-policy-engine]]' link and replace their open ADR question. Status: Proposed; deciders: CTO with the security lead; consulted: platform engineering, domain team; informed: product and AI group. No superseded records.

<!-- citations -->
## Citations

```json
[
  {
    "body": "OpenID Foundation",
    "excerpt": "Defines Access Evaluation, Access Evaluations (batch), Subject, Resource and Action Search APIs; request of subject, action, resource and context; response with boolean decision and optional context; PDP metadata at /.well-known/authzen-configuration.",
    "id": "R1",
    "kind": "standard",
    "title": "Authorization API 1.0 (AuthZEN)",
    "url": "https://openid.net/specs/authorization-api-1_0.html"
  },
  {
    "body": "OpenID Foundation",
    "excerpt": "Announcement dated 12 January 2026 that AuthZEN Authorization API 1.0 is a Final Specification.",
    "id": "R2",
    "kind": "standard",
    "title": "Authorization API 1.0 Final Specification Approved",
    "url": "https://openid.net/authorization-api-1-0-final-specification-approved/"
  },
  {
    "excerpt": "Any satisfied forbid gives Deny even if a permit is satisfied; no satisfied policy gives Deny; the response lists the determining policies and errors.",
    "id": "R3",
    "kind": "vendor",
    "title": "Cedar documentation: How Cedar authorization works",
    "url": "https://docs.cedarpolicy.com/auth/authorization.html",
    "vendor": "Cedar (open source)"
  },
  {
    "excerpt": "Version 4.14.0; partial-eval, type-aware partial evaluation (tpe) and entity-manifest are listed under experimental features that may change in any release.",
    "id": "R4",
    "kind": "vendor",
    "title": "cedar-policy crate documentation (docs.rs)",
    "url": "https://docs.rs/cedar-policy",
    "vendor": "Cedar (open source)"
  },
  {
    "excerpt": "Apache-2.0; crates include cedar-policy, cedar-policy-symcc (symbolic compiler for verifying policy properties) and cedar-wasm for JavaScript and TypeScript.",
    "id": "R5",
    "kind": "vendor",
    "title": "cedar-policy/cedar repository",
    "url": "https://github.com/cedar-policy/cedar",
    "vendor": "Cedar (open source)"
  },
  {
    "excerpt": "Three approaches: search then check, local index from the changes endpoint, or ListObjects then search; recommends the local index for large result sets; 'and' and 'but not' relations are more expensive.",
    "id": "R6",
    "kind": "vendor",
    "title": "OpenFGA documentation: Search with permissions",
    "url": "https://openfga.dev/docs/interacting/search-with-permissions",
    "vendor": "OpenFGA (CNCF)"
  },
  {
    "excerpt": "Conditional relationship tuples evaluated with CEL; tuple context up to 32 KB; CEL evaluation cost capped by default.",
    "id": "R7",
    "kind": "vendor",
    "title": "OpenFGA documentation: Conditions",
    "url": "https://openfga.dev/docs/modeling/conditions",
    "vendor": "OpenFGA (CNCF)"
  },
  {
    "excerpt": "Apache-2.0; storage PostgreSQL 14+, MySQL 8, SQLite (beta); in-memory for development only.",
    "id": "R8",
    "kind": "vendor",
    "title": "openfga/openfga repository",
    "url": "https://github.com/openfga/openfga",
    "vendor": "OpenFGA (CNCF)"
  },
  {
    "excerpt": "CNCF Sandbox from 2022; Incubating maturity level since 28 October 2025.",
    "id": "R9",
    "kind": "vendor",
    "title": "OpenFGA Project",
    "url": "https://openfga.dev/project",
    "vendor": "OpenFGA (CNCF)"
  },
  {
    "excerpt": "Consistency modes minimize_latency, at_least_as_fresh, at_exact_snapshot and fully_consistent; ZedTokens address the New Enemy Problem caused by stale caches.",
    "id": "R10",
    "kind": "vendor",
    "title": "SpiceDB documentation: Consistency",
    "url": "https://authzed.com/docs/spicedb/concepts/consistency",
    "vendor": "AuthZed"
  },
  {
    "excerpt": "CockroachDB, Spanner, PostgreSQL, MySQL, memdb; PostgreSQL recommended for single-region self-hosted deployments; Postgres 15+ and track_commit_timestamp for Watch.",
    "id": "R11",
    "kind": "vendor",
    "title": "SpiceDB documentation: Datastores",
    "url": "https://authzed.com/docs/spicedb/concepts/datastores",
    "vendor": "AuthZed"
  },
  {
    "excerpt": "Apache-2.0; open-source Zanzibar-inspired database for fine-grained authorization data; AuthZed Cloud offered as a managed service.",
    "id": "R12",
    "kind": "vendor",
    "title": "authzed/spicedb repository",
    "url": "https://github.com/authzed/spicedb",
    "vendor": "AuthZed"
  },
  {
    "excerpt": "Partial evaluation over unknowns produces condition sets that are translated into SQL WHERE clauses.",
    "id": "R13",
    "kind": "vendor",
    "title": "OPA documentation: Evaluating a Data Filter Policy",
    "url": "https://www.openpolicyagent.org/docs/filtering/partial-evaluation",
    "vendor": "Open Policy Agent (CNCF)"
  },
  {
    "excerpt": "Compile endpoint returns SQL for a filter policy using standard OPA.",
    "id": "R14",
    "kind": "vendor",
    "title": "OPA documentation: Tutorial: SQL Data Filtering",
    "url": "https://openpolicyagent.org/docs/filtering/tutorial-sql-filtering",
    "vendor": "Open Policy Agent (CNCF)"
  },
  {
    "excerpt": "Apache-2.0; graduated CNCF project.",
    "id": "R15",
    "kind": "vendor",
    "title": "open-policy-agent/opa repository",
    "url": "https://github.com/open-policy-agent/opa",
    "vendor": "Open Policy Agent (CNCF)"
  },
  {
    "excerpt": "Relationship tuples and consistency tokens (zookies) for global authorization.",
    "id": "R16",
    "kind": "web",
    "title": "Zanzibar: Google's Consistent, Global Authorization System (USENIX ATC 2019)",
    "url": "https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/"
  }
]
```

<!-- end -->
