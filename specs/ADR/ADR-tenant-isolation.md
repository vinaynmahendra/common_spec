---
id: "ADR-tenant-isolation"
title: "Tenant isolation"
parent: "ADR"
order: 1
type: "decision"
template: "adr"
status: "approved"
owner: null
indicative: false
summary: "Shared DB with `tenant_id` + Postgres Row-Level Security (see Section 3)"
links: []
rev: 2
syncHash: "fe77e62f369a5061"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 19.1 Tenant isolation

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Shared DB with `tenant_id` + Postgres Row-Level Security (see Section 3)

<!-- section:context -->
## Context and problem

**Question:** how do we keep each tenant's data (an arbitral institution, a SEBI ODR institution, a CORD tenant) separated inside one regional platform, so that a bug in one query cannot expose another tenant's cases, documents or invoices?

Affected parts: every tenant-owned table in the regional Postgres ([[INF-database]]), the data access layer ([[PKG-data-access]], [[MT-prisma-implementation]]), connection pooling ([[INF-pgbouncer]]), background workers (Temporal and BullMQ), search and vector indexes ([[PKG-search]], [[AI-rag]]) and reporting ([[RPT-report-infrastructure]]).

Starting point: each region (India, Singapore, US) runs its own full stack ([[MT-data-residency-2]]), so residency is solved by region, not by tenant database. Inside a region we expect tens of tenants at launch, with very uneven sizes (a large institution with thousands of active cases alongside small CORD tenants).

<!-- section:drivers -->
## Decision drivers

| # | Driver | Why it matters here |
|---|---|---|
| D1 | Isolation enforced below application code | Client security questionnaires and ISO 27001 A.8.3 (information access restriction) expect controls that do not rely on every developer remembering a `WHERE tenant_id = ...` |
| D2 | Operational cost per tenant | Onboarding a small CORD tenant must not mean a new database, migration run and backup policy |
| D3 | One migration path | Schema changes ship once per region, not once per tenant |
| D4 | Cross-tenant platform operations | Platform admin, support and aggregate reporting must still be possible through controlled routes |
| D5 | Fit with Prisma and PgBouncer transaction pooling | The mechanism must survive connection reuse between requests |
| D6 | Path to a dedicated deployment | Some clients may later require physical separation; the design must not block that |

<!-- section:decision -->
## Decision

**Shared database per region, every tenant-owned table carries a non-null `tenant_id`, and Postgres Row-Level Security is enabled and forced on those tables** (see [[MT-isolation-strategy]]).

How it works, in short:

- Every tenant-owned table has `tenant_id uuid not null`, usually the leading column of composite indexes ([[MT-every-tenant-owned-table-carries]]). Platform-level tables have no `tenant_id` and no tenant policy ([[MT-platform-level-tables]]).
- RLS is `ENABLE`d and `FORCE`d (table owners otherwise bypass policies; superusers and `BYPASSRLS` roles always do [R2]) with the policy `tenant_id = current_setting('app.tenant_id')::uuid` ([[MT-rls-enabled-and-forced-on]]).
- The Prisma Client extension opens a transaction per request and runs `set_config('app.tenant_id', <id>, true)` first, so the value lives only for that transaction and is safe with PgBouncer transaction pooling ([[MT-prisma-client-extension-wraps]]).
- The application connects as a non-owner, non-superuser role ([[MT-app-connects-as-a-non]]); a separate privileged role is used only by migrations and controlled platform-admin jobs ([[MT-separate-privileged-role-used]]).
- Cross-tenant reporting uses a read-only reporting role or the warehouse, never the app role ([[MT-cross-tenant-reporting-via-a]]).

Justification: forced RLS meets D1 because the database refuses rows from another tenant even when a query forgets the filter; one schema per region meets D2 and D3; the privileged and reporting roles meet D4; transaction-scoped settings meet D5. D6 is kept open because the same schema can be deployed as a single-tenant regional stack.

<!-- section:consequences -->
## Consequences

| Stakeholder | Easier | Harder |
|---|---|---|
| Developers | No tenant filter boilerplate; a missing filter returns zero rows instead of leaking | Every query must run inside the tenant transaction; raw SQL and `$queryRaw` must go through the extension; long interactive transactions hold a pooled connection |
| Platform / DevOps | One database, one migration, one backup policy per region | RLS policies live in raw SQL inside Prisma migrations ([[MT-prisma-migrations-include-rls]]) and must be reviewed like code |
| Security / audit | A single, testable enforcement point to show auditors | The privileged role becomes a high-value credential that needs break-glass handling ([[SEC-access-reviews]]) |
| Large tenants | Shared capacity absorbs spikes | Noisy-neighbour risk on CPU, I/O and locks; per-tenant restore is a filtered export, not a whole-database restore |
| Tenant offboarding | Deletion is a set of `DELETE ... WHERE tenant_id` jobs | Proving deletion from backups needs a documented backup-expiry argument ([[PKG-data-retention-legal-hold-and]]) |

New failure modes: the tenant setting missing (queries return nothing, so errors surface as "not found" rather than leaks); a table added without a policy (caught by the lint check below); the planner ignoring `tenant_id` indexes when policies use functions (watch query plans).

<!-- section:confirmation -->
## Confirmation

- **CI schema check** ([[MT-lint-review-check-that-every]]): after migrations run in CI, a query over `pg_class` / `pg_policies` fails the build if any table in the tenant schema lacks `relrowsecurity` and `relforcerowsecurity`, lacks a `tenant_id` column, or lacks a policy referencing `app.tenant_id`. Platform-level tables are listed in an allow-list file reviewed by CODEOWNERS.
- **Cross-tenant tests** ([[MT-automated-tests-that-prove-one]], [[TST-multi-tenant-isolation-tests]]): seed two tenants, then for every Prisma model attempt read, update and delete across tenants, including with the tenant setting unset. Blocking in CI.
- **Role check**: a start-up assertion in the app and workers that the connected role is not the table owner and has no `BYPASSRLS`.
- **Dependency rule**: ESLint `no-restricted-imports` blocks direct `pg` / `postgres` clients outside `packages/data-access`.
- Exceptions (a new platform-level table, a job needing the privileged role) are approved through the ADR process in [[FND-governance]].

<!-- section:options -->
## Options considered

| Option | D1 enforcement | D2 cost per tenant | D3 migrations | D6 dedicated path | Verdict |
|---|---|---|---|---|---|
| **Shared DB + `tenant_id` + forced RLS** | Database-enforced | Lowest | One per region | Same schema can run single-tenant | **Chosen** |
| Schema per tenant | Search-path based; a wrong `search_path` leaks | Medium | One per tenant schema; slow with many tenants | Easy | Rejected: migration fan-out and connection pool fragmentation with PgBouncer |
| Database per tenant | Strongest | Highest (backups, monitoring, connections per tenant) | One per tenant | Native | Rejected for the default; kept as a premium deployment option |
| Shared DB, application filter only | None below the app | Lowest | One | Same | Rejected: fails D1; one missed filter is a breach |

The AWS SaaS Lens describes the same silo / bridge / pool spectrum [R1].

<!-- section:revisit -->
## When to revisit

- A client contract or regulator requires physical database separation for that client: deploy a dedicated regional stack with the same schema, do not change this ADR.
- A single tenant exceeds an agreed share of regional database load (proposed trigger: more than 40 percent of CPU or I/O for a sustained week).
- RLS overhead on key queries exceeds a proposed 15 percent latency penalty versus the same query without the policy, measured in [[TST-performance-and-load-testing]].
- Prisma or PgBouncer changes break transaction-scoped settings (for example a pooler that pins or resets session state differently, see [[INF-pgbouncer]]).

<!-- section:notes -->
## More information

- Related decisions: [[ADR-orm]] (Prisma extension), [[ADR-next-js-hosting]] and [[ADR-container-orchestration]] (per-region stacks), [[ADR-queue-technology]] and [[ADR-temporal]] (workers must carry tenant context).
- Implementation detail lives in [[MT-isolation-strategy]] and its children; this record only fixes the choice.

**Open questions**

- [ ] Do any current or contracted clients (for example an institution procuring a bespoke case management platform) require a dedicated database or dedicated regional stack? If so, record it as a deployment variant, not a change to this ADR.
- [ ] Agree the numeric revisit triggers (tenant load share, RLS latency penalty) with the database owner.
- [ ] Who holds and approves use of the privileged migration role in each region, and how is its use logged and reviewed?
- [ ] Deciders, consulted and informed lists and approval date to be added from the architecture review board minutes.

<!-- checks -->
## Template checks

<!-- check:significance -->
### Significance

Significant: it shapes every tenant-owned table, every query path and every worker, it is visible to clients in security questionnaires, and reversing it after data exists means a migration of every tenant. It decides isolation *inside* a regional database; it does not decide residency (that is [[MT-data-residency-2]]) or isolation in object storage, search and vector stores, which follow the same `tenant_id` rule in their own nodes.

<!-- check:compliance -->
### Regulatory, residency and tenancy fit

- **Residency:** unaffected; each region keeps its own database.
- **Isolation:** this is the primary control. Mapped to ISO 27001:2022 A.8.3 (information access restriction) and A.8.31 (separation of environments, for the privileged role) through [[SEC-isms-controls]].
- **Retention and deletion:** tenant offboarding deletes by `tenant_id`; backups expire on the regional schedule ([[PKG-data-retention-legal-hold-and]]).
- **Audit:** privileged-role sessions are logged to [[PKG-audit-trail]].
- Security reviewer and date: to be recorded at the next architecture review board.

<!-- check:consequences -->
### Consequences and costs

The downsides are stated per group in the Consequences table: noisy neighbours, filtered per-tenant restores, a high-value privileged role, and raw-SQL policies in migrations. Follow-up work: the CI schema check, the cross-tenant test suite and the role start-up assertion, each tracked under [[MT-safeguards]].

<!-- check:reversibility -->
### Reversibility and revisit triggers

We would find out through the revisit triggers (load share per tenant, RLS latency penalty from load tests, a contract demanding separation). The exit path is cheap for one tenant: because every row carries `tenant_id`, a tenant can be exported into a dedicated regional stack with the same schema (estimated at a few engineer-weeks for tooling, once). Moving the whole platform to database-per-tenant would be a multi-month project; we keep that option cheaper by never relying on cross-tenant joins in product code.

<!-- check:confirmation -->
### Confirmation

Three blocking checks: the CI schema check on `pg_class.relforcerowsecurity` and `pg_policies`, the cross-tenant test suite over every Prisma model, and the start-up assertion that the connected role has no `BYPASSRLS` and does not own tables. Exceptions go through the ADR process and the allow-list file under CODEOWNERS.

<!-- check:linked -->
### Linked and lifecycle

Governs [[MT-isolation-strategy]], [[MT-rls-enabled-and-forced-on]], [[MT-prisma-client-extension-wraps]], [[MT-safeguards]], [[TST-multi-tenant-isolation-tests]], [[AI-rag]] (vector rows carry `tenant_id`). Related: [[ADR-orm]], [[ADR-queue-technology]], [[ADR-temporal]]. Status: Approved; deciders and date to be added from the board minutes. No superseded records.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Describes silo, bridge and pool isolation models and the need to enforce isolation beyond application code.",
    "id": "R1",
    "kind": "vendor",
    "title": "AWS Well-Architected SaaS Lens: Tenant isolation",
    "url": "https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/tenant-isolation.html",
    "vendor": "Amazon Web Services"
  },
  {
    "body": "PostgreSQL Global Development Group",
    "excerpt": "Table owners normally bypass row security unless FORCE ROW LEVEL SECURITY is set; superusers and roles with BYPASSRLS always bypass it.",
    "id": "R2",
    "ident": "PostgreSQL documentation 5.9",
    "kind": "standard",
    "title": "Row Security Policies",
    "url": "https://www.postgresql.org/docs/current/ddl-rowsecurity.html"
  }
]
```

<!-- end -->
