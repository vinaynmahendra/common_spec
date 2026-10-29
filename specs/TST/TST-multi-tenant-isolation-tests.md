---
id: "TST-multi-tenant-isolation-tests"
title: "Multi-tenant isolation tests (cross-tenant data leak checks)"
parent: "TST"
order: 2
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 2
syncHash: "6cc861a711eb97fd"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 16.2 Multi-tenant isolation tests (cross-tenant data leak checks)

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

Specifies the automated suite that proves one tenant cannot read, write, infer or receive another tenant's data, at every layer where tenant data lives: Postgres (forced RLS), the Prisma tenant extension under PgBouncer transaction pooling, caches, queues, workflows, object storage, search and vector indexes, and the HTTP surface. It implements [[MT-automated-tests-that-prove-one]] and the safeguards in [[MT-safeguards]]; the isolation design itself is in [[MT-isolation-strategy]].

<!-- section:rules -->
## Rules

**Database catalogue checks** (run on every PR touching `packages/db`, and after every migration in every environment)
- **ISO-1** Every table not listed in `platform-tables.txt` has a non-null `tenant_id` column, `relrowsecurity = true`, `relforcerowsecurity = true`, and at least one policy whose `USING` and `WITH CHECK` expressions reference `current_setting('app.tenant_id')` (queried from `pg_class` and `pg_policies`).
- **ISO-2** The application role is not the owner of any tenant table, is not a superuser and does not have `BYPASSRLS` (queried from `pg_roles` and `pg_tables`) ([[MT-app-connects-as-a-non]]). Owners and superusers bypass RLS unless it is forced, and `BYPASSRLS` always does [R1].
- **ISO-3** Every tenant table's indexes include one led by `tenant_id` ([[MT-every-tenant-owned-table-carries]]).

**Behavioural database tests** (generated per Prisma model)
- **ISO-4** For every tenant-owned model, with rows created for `arb-inst` and `odr-inst`: as `odr-inst`, `findMany`, `findFirst`, `findUnique` by an `arb-inst` ID, `count`, `aggregate`, `groupBy`, `update`, `updateMany`, `delete`, `deleteMany` and `upsert` return nothing or affect zero rows; `create` with `tenantId` of `arb-inst` is rejected by `WITH CHECK`.
- **ISO-5** Relation traversal (`include`, nested `connect`) from a tenant's own row to another tenant's row returns nothing or fails.
- **ISO-6** Queries run without tenant context (no `withTenant`) fail with an error; they never return rows. Queries with an empty or malformed tenant ID fail.
- **ISO-7** Tagged `$queryRaw` statements in `packages/db` are each covered by a cross-tenant test.

**Connection pooling**
- **ISO-8** With PgBouncer in transaction mode and a pool size of 1, 1,000 interleaved requests alternating between two tenants never see the other tenant's rows, and `current_setting('app.tenant_id', true)` is empty at the start of every new transaction ([[MT-prisma-client-extension-wraps]]) [R2].

**Beyond Postgres**
- **ISO-9** Cache: keys produced by `@nomology/cache` always include tenant and region; a test writes the same logical key for two tenants and reads back each tenant's own value ([[PKG-caching]]).
- **ISO-10** Queues and workflows: a BullMQ job or Temporal workflow started for tenant A runs its activities with tenant A context only; a job whose payload tenant differs from its envelope tenant is rejected; workflow IDs carry the tenant prefix ([[WF-separation-of-concerns-temporal]]).
- **ISO-11** Object storage: signed URLs for tenant A objects are refused when requested in tenant B's session; storage keys carry the tenant prefix ([[PKG-encryption-at-rest-signed-urls]]).
- **ISO-12** Search and vector retrieval: queries as tenant B never return tenant A documents or chunks, including through similarity search with tenant A's exact text ([[PKG-search]], [[AI-rag]]).
- **ISO-13** Notifications and webhooks: a template rendered for tenant A with a variable referencing a tenant B object renders nothing; webhook deliveries go only to the tenant's own endpoints.

**HTTP surface**
- **ISO-14** For every route handler, tRPC procedure, Server Action and public API operation, a generated test calls it as a tenant B user (and with a tenant B API key) using tenant A resource IDs, on tenant A's host and tenant B's host; the response is the identical not-found problem defined in [[APP-error-message-catalogue]], never 200 and never a different error that reveals existence.
- **ISO-15** Authenticated responses carry `Cache-Control: private, no-store` (or tenant-varied keys where caching is designed in [[APP-rendering-and-caching-strategy]]); a test fetches the same URL for two tenants through the CDN in staging and checks content differs.

**Running**
- **ISO-16** ISO-1 to ISO-8 run on every PR touching `packages/db`, `packages/domain-*` or `packages/testing`; the full suite runs nightly and as a production promotion gate in staging in every region ([[DEP-environment-promotion-and-multi]]). ISO-1 and ISO-2 also run against production after each migration, read-only.
- **ISO-17** Any isolation failure on `main` or in staging blocks all promotions until fixed, and is raised as a security incident if it reached production.

<!-- section:rationale -->
## Rationale

- Catalogue checks (ISO-1 to ISO-3) catch the "forgot RLS on the new table" class of bug cheaply and on every environment, including production.
- Generated per-model tests (ISO-4) mean a new model is tested automatically without someone remembering to write the test.
- ISO-8 targets the specific risk of PgBouncer transaction pooling: a session-level `SET` would leak tenant context to the next client on the same server connection.
- Non-Postgres stores (ISO-9 to ISO-13) have no RLS; their isolation depends on key and filter conventions, which is exactly why they need tests.
- ISO-14 identical not-found prevents tenants inferring the existence of other tenants' cases by ID probing.

<!-- section:tooling -->
## Tooling and configuration

- `@nomology/testing/isolation`: `rlsCatalogueCheck(db)`, `generateModelIsolationTests(prismaDmmf)`, `poolLeakTest()`, `routeIsolationTests(routeRegistry)`.
- Route registry generated at build time from App Router route handlers, tRPC routers and the OpenAPI document.
- Testcontainers stack with PgBouncer configured `pool_mode = transaction` and `default_pool_size = 1` for ISO-8.
- Read-only production check job using the reporting role ([[MT-cross-tenant-reporting-via-a]]), which has catalogue access only.

<!-- section:enforcement -->
## Enforcement

Required PR check `isolation` (ISO-1 to ISO-8) and `rls-catalogue`; nightly full-suite workflow; promotion gate per region. A model or route that the generator cannot test (for example a custom raw query) fails the generator until a hand-written test is registered for it. The suite registry entry names `security` and `platform-data` as owners.

<!-- section:examples -->
## Examples

Generated test (sketch):

```ts
describe.each(tenantModels)('isolation: %s', (model) => {
  it('tenant B cannot read tenant A rows by id', async () => {
    const a = await factories[model].create(tenants.arbInst);
    const row = await withTenant(tenants.odrInst, (tx) => tx[model].findUnique({ where: { id: a.id } }));
    expect(row).toBeNull();
  });
});
```

<!-- section:exceptions -->
## Exceptions

None. Platform-level tables are not exceptions; they are declared in `platform-tables.txt`, and additions to that file need `security` approval.

<!-- section:questions -->
## Open questions

- [ ] Should missing tenant context raise an error (policy uses `current_setting('app.tenant_id')` without `missing_ok`) everywhere? Proposed yes; confirm against the policy text in [[MT-rls-enabled-and-forced-on]].
- [ ] Is a production read-only catalogue check after each migration acceptable to the information security owner (it uses the reporting role)?
- [ ] How are isolation tests run for Azure deployments where PgBouncer is the Flexible Server built-in ([[INF-pgbouncer]])?

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

All rules are automated: catalogue SQL checks, generated per-model and per-route tests, a pooling leak test and nightly plus promotion-gate runs. Coverage is complete by construction because tests are generated from the Prisma schema and the route registry.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

This node is the test side of the tenant isolation non-negotiable: forced RLS, non-owner app role, transaction-scoped tenant setting under PgBouncer, tenant-prefixed keys and identical not-found responses. Uses synthetic fixture tenants only.

<!-- check:exceptions -->
### Exceptions

Non-waivable. The only lever is the platform-tables list, which needs security approval.

<!-- check:compliance -->
### Compliance evidence

Evidence for tenant segregation claims in client security questionnaires, ISO/IEC 27001:2022 access-restriction and secure-development controls, and SOC 2 logical-access criteria: nightly and per-release isolation reports per region, retained with the change record.

<!-- check:measurement -->
### Adoption measurement

Coverage: share of tenant tables and routes with generated tests (target 100%); isolation failures on `main` (target 0); time to fix an isolation failure.

<!-- check:ownership -->
### Ownership and change

Owners: `security` and `platform-data` jointly.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Table owners normally bypass row security; ALTER TABLE ... FORCE ROW LEVEL SECURITY makes policies apply to the owner too. Superusers and roles with BYPASSRLS always bypass it.",
    "id": "R1",
    "kind": "vendor",
    "title": "Row Security Policies",
    "url": "https://www.postgresql.org/docs/current/ddl-rowsecurity.html",
    "vendor": "PostgreSQL Global Development Group"
  },
  {
    "excerpt": "Lists which PostgreSQL features work in each pooling mode; session-level SET and RESET are not supported in transaction pooling mode.",
    "id": "R2",
    "kind": "vendor",
    "title": "PgBouncer features",
    "url": "https://www.pgbouncer.org/features.html",
    "vendor": "PgBouncer"
  }
]
```

<!-- end -->
