---
id: "MT-safeguards"
title: "Safeguards"
parent: "MT-isolation-strategy"
order: 5
type: "feature"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "Controls that keep tenant isolation true over time: cross-tenant tests, schema lint and review, and a separate path for cross-tenant reporting"
links: []
rev: 2
syncHash: "141f62c7eb37a116"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 3.3.5 Safeguards

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Controls that keep tenant isolation true over time: cross-tenant tests, schema lint and review, and a separate path for cross-tenant reporting

<!-- section:purpose -->
## Purpose and scope

[[MT-isolation-strategy]] defines the isolation mechanism; this node defines the controls that stop it eroding as hundreds of tables, procedures and jobs are added. It protects the same assets from the same actors, but the threat here is **drift**: a new table without RLS, a new code path without context, a new report that reads across tenants from the wrong role.

Three safeguards, each a child requirement:

1. [[MT-automated-tests-that-prove-one]] — behavioural proof that tenant A cannot read or write tenant B's data on every path.
2. [[MT-lint-review-check-that-every]] — static and review checks that every new table and function is classified and protected before merge.
3. [[MT-cross-tenant-reporting-via-a]] — the only sanctioned way to read across tenants for reporting.

Relied on by: ISMS evidence for logical access controls ([[SEC-isms-controls]]), client security questionnaires, and the release gate in [[DEP-ci-cd-pipelines-build-test]]. The test standard is shared with [[TST-multi-tenant-isolation-tests]].

<!-- section:assets -->
## Protected assets

| Asset | Why drift threatens it | Classification |
|---|---|---|
| All tenant-owned tables | New tables may ship without `tenant_id` / RLS | Up to tribunal-only |
| tRPC routers, Server Actions, public API routes | New endpoints may accept a tenant id from input or skip membership checks | — |
| Background jobs and workflows | New jobs may forget the envelope | — |
| Derived stores (search, cache, vectors, object storage) | Outside Postgres RLS; each new index or cache key is a new chance to mix tenants | Same as source |
| Reporting outputs | Cross-tenant aggregates may expose one tenant's figures to another, or to the public in industry reports ([[RPT-industry-marketing]]) | Tenant-internal |

<!-- section:actors -->
## Actors and roles

| Actor | Role in the safeguards |
|---|---|
| Engineers (authors) | Classify new tables, use the generator, write isolation tests for new routers |
| Code owners (platform-core, security reviewer) | Required reviewers for `packages/db/**`, migrations, `security-definer-register.yaml` |
| CI | Runs lint, catalogue and isolation suites; blocks merge |
| Nightly verifier (`platform-ops` worker) | Runs catalogue checks against production per region |
| Reporting service | Only holder of `nomo_reporting` |
| ISMS lead | Reviews monthly evidence and exceptions ([[SEC-isms-controls]]) |

<!-- section:matrix -->
## Permission matrix

Who may change or waive a safeguard:

| Action | Engineer | Code owner (platform-core) | Security reviewer | ISMS lead | CI |
|---|---|---|---|---|---|
| Add a tenant-owned table | Propose | Approve | Approve if it holds sensitive personal data | — | Must pass |
| Add a platform-level table | Propose | Approve | Approve | — | Must pass |
| Add a `SECURITY DEFINER` function | Propose | Approve | Approve (required) | Informed | Must pass |
| Add an index exception to the leading-column rule | Propose | Approve | — | — | Must pass |
| Skip an isolation test (quarantine) | No | Request | Approve, max 7 days | Informed | Records quarantine |
| Grant a new view to `nomo_reporting` | Propose | Approve | Approve | — | Must pass |
| Disable a safeguard in CI | No | No | No | Approve with time limit | — |

<!-- section:policy -->
## Policy model

Safeguards are expressed as code in the repository and evaluated in this order on every pull request: (1) `tenancy-classification.yaml` covers every table in the Prisma schema and migrations; (2) migration lint checks for the RLS block; (3) the migration is applied to an empty database and a staging snapshot; (4) catalogue test; (5) isolation suite; (6) router coverage check (every tRPC router and API route has an isolation test entry). Any failure blocks merge. The nightly job repeats (4) against production.

<!-- section:threats -->
## Threats and abuse cases

| STRIDE | Drift scenario | Safeguard | Residual risk |
|---|---|---|---|
| Information disclosure | New table `transcript_segment` added without RLS | Lint + catalogue test fail the build | Low |
| Information disclosure | Policy changed by hand in production | Nightly catalogue check alerts | Low (detected within 24 h) |
| Information disclosure | New tRPC router reads by id passed from client without membership check | Router coverage check requires an isolation test; RLS still blocks other tenants | Low |
| Information disclosure | New search index without tenant filter | Isolation suite includes search queries per index | Medium (depends on test coverage) |
| Information disclosure | Analyst connects BI tool with app credentials | App credentials not issued to humans; reporting role separate; connection source alerts | Low |
| Elevation of privilege | `SECURITY DEFINER` function added quietly | Lint flags any `SECURITY DEFINER`; register required | Low |
| Tampering | Test quarantined and forgotten | Quarantine expires in 7 days and fails the build | Low |
| Information disclosure | Industry report reveals a small tenant's numbers | Minimum cohort size rule in reporting views ([[MT-cross-tenant-reporting-via-a]]) | Medium |

<!-- section:failure -->
## Denial behaviour

A safeguard failure in CI blocks the merge with a message naming the table, function or route and linking this node. A nightly production failure raises a P2 security alert to the platform on-call and the ISMS lead, opens an incident in [[SEC-security-incident-response-and]] if any table is found without forced RLS, and records the finding in the ISMS nonconformity log.

<!-- section:requirements -->
## Security requirements

| ID | Requirement | Child |
|---|---|---|
| SG-1 | Automated tests shall prove for every tenant-owned table, router and job family that tenant A cannot read or write tenant B's data, including with `tenant_id` omitted. | [[MT-automated-tests-that-prove-one]] |
| SG-2 | CI shall reject any change that adds a table, view or function touching tenant data without classification, RLS and review. | [[MT-lint-review-check-that-every]] |
| SG-3 | Cross-tenant reads shall happen only through the reporting role or the regional warehouse. | [[MT-cross-tenant-reporting-via-a]] |
| SG-4 | The production catalogue of each region shall be verified nightly against the classification file. | This node |
| SG-5 | Safeguard waivers shall be time-limited and approved by security. | This node |

<!-- section:verification -->
## Verification

Evidence produced: CI run artefacts for every merge (retained 13 months as ISMS evidence), nightly verifier reports per region, quarantine log, review approvals from the code host. External: annual pen test includes an attempt to find a table or route not covered.

<!-- section:questions -->
## Open questions

- [ ] Add a fourth safeguard for noisy-neighbour fairness (per-tenant rate limits and queue fairness)? Proposed: yes, as a requirement here.
- [ ] Retention period for CI evidence (13 months proposed, to cover a SOC 2 Type II period plus margin).

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

The safeguards do not grant access themselves; they detect and block drift in the layers defined in [[MT-isolation-strategy]]. The nightly verifier runs with a catalogue-only role that can read `pg_catalog` but no tenant data.

<!-- check:enforcement -->
### Enforcement points and bypass paths

Every change path into production goes through CI (branch protection, no direct pushes, no manual DDL in production outside break-glass), and the nightly check catches anything that bypassed it.

<!-- check:audit -->
### Audit trail

CI results, approvals, quarantine records and nightly verifier output are kept as evidence; break-glass DDL is logged and reviewed in [[SEC-access-reviews]].

<!-- check:compliance -->
### Framework and legal mapping

Supports ISO/IEC 27001:2022 A.8.25 (secure development life cycle), A.8.29 (security testing in development and acceptance), A.8.32 (change management) and A.8.3 (information access restriction); SOC 2 CC8.1 (change management) and CC7.1 (detection of configuration changes) [R1].

<!-- check:testing -->
### Verification and testing

The safeguards are themselves tested: a fixture migration without RLS must fail the lint and catalogue test (a "canary" test in CI), so a broken safeguard is noticed.

<!-- citations -->
## Citations

```json
[
  {
    "body": "AICPA",
    "excerpt": "Common criteria CC1–CC9 plus Availability (A), Confidentiality (C) and Privacy (P) criteria used in SOC 2 reports.",
    "id": "R1",
    "ident": "Trust Services Criteria",
    "kind": "standard",
    "title": "2017 Trust Services Criteria for Security, Availability, Processing Integrity, Confidentiality, and Privacy",
    "url": "https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022",
    "version": "2017 (revised points of focus 2022)"
  }
]
```

<!-- end -->
