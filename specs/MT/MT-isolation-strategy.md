---
id: "MT-isolation-strategy"
title: "Isolation strategy"
parent: "MT"
order: 3
type: "capability"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "**Shared DB with `tenant_id` + Postgres Row-Level Security** (record in ADR)"
links: [{"rel": "decided-by", "to": "ADR-tenant-isolation"}]
rev: 2
syncHash: "6f12339955f9cc6d"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 3.3 Isolation strategy

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> **Shared DB with `tenant_id` + Postgres Row-Level Security** (record in ADR)

<!-- section:purpose -->
## Purpose and scope

This control guarantees that data belonging to one tenant cannot be read, changed, referenced or inferred from another tenant's context, and that the guarantee holds even when application code has a bug. It implements [[ADR-tenant-isolation]]: one shared Postgres database per region, a `tenant_id` column on every tenant-owned table, and Postgres Row-Level Security that is enabled and forced on those tables [R1].

**Protected from:** users of other tenants (including legitimate users who hold memberships in two tenants), compromised user accounts, bugs in application code (missing filters, wrong IDs from the client), background jobs and workflows running for another tenant, and Nomology staff acting outside an approved support or break-glass grant.

**Relied on by:** every domain module ([[DOM-cases]], [[DOM-documents]], [[DOM-hearings]], [[DOM-neutrals]], [[DOM-transcribers]], [[DOM-invoices-and-vendor-bills]]), every shared package that stores data ([[PKG-audit-trail]], [[PKG-notifications]], [[PKG-settings]], [[PKG-search]]), the public API ([[INT-public-api-and-webhooks]]) and AI retrieval ([[AI-rag]]).

The control has three layers. Only the second is the hard boundary; the others reduce the chance of reaching it.

1. **Resolution and authorization**: the tenant is resolved from the request ([[MT-tenant-resolution]]) and the user must hold an active membership in it ([[PKG-authorization]]).
2. **Database enforcement**: forced RLS keyed on a transaction-local setting `app.tenant_id` ([[MT-rls-enabled-and-forced-on]], [[MT-prisma-client-extension-wraps]]), with the application connecting as a role that cannot bypass RLS ([[MT-app-connects-as-a-non]]).
3. **Derived stores**: the same tenant key scopes object-storage prefixes, cache keys, search indexes, vector stores and Temporal search attributes (owned by each package node).

<!-- section:assets -->
## Protected assets

| Asset | Examples | Classification ([[SEC-data-classification]]) |
|---|---|---|
| Case records | Cases, parties, representatives, pleadings metadata, status history | Case participants / tribunal-only |
| Documents and exhibits | Statements of claim, evidence, eBundles, awards, procedural orders (rows in Postgres, objects in storage) | Case participants / tribunal-only |
| Hearing data | Schedules, attendance, recordings and transcripts metadata | Case participants |
| Personal data of parties and users | Names, contact details, KYC results, identity documents, bank details for payouts | Personal / sensitive personal |
| Financial records | Invoices, fee schedules applied, payments, vendor bills | Tenant-internal (confidential) |
| Tenant configuration | Rules, decision tables, templates, branding, SSO configuration | Tenant-internal |
| Audit trail | Who did what, when, to which record | Tenant-internal; integrity-critical |
| Workflow state | Temporal payloads and search attributes; BullMQ job payloads | Same as the entity they carry |
| The tenant boundary itself | The `app.tenant_id` setting, database role credentials, the tenant directory | Platform-critical |

<!-- section:actors -->
## Actors and roles

| Actor | Database role | How it is obtained | Can span tenants? |
|---|---|---|---|
| Web request (any persona: tenant admin, secretariat / tribunal secretary, party / counsel, neutral, transcriber) | `nomo_app` | Session for a user with an active membership in the resolved tenant | No |
| Public API client of a tenant | `nomo_app` | API key or OAuth client bound to one tenant ([[INT-api-platform-tables]]) | No |
| Aggregator (for example an MII routing SEBI ODR matters) | `nomo_app` | Aggregator credential bound to a list of tenants; each call names one tenant and is checked against that list ([[INT-aggregator-intake-api]]) | No; one tenant per transaction |
| Temporal / BullMQ worker | `nomo_worker` | Tenant id from workflow input / job envelope, verified against the directory | No; one tenant per transaction |
| Platform admin (Nomology) | `nomo_app` with platform context, for platform-level tables only | Staff SSO + MFA, `platform_admin` role | Platform tables only |
| Support engineer under approved access | `nomo_app` with the target tenant's context | Time-limited, tenant-approved grant ([[PKG-support-access-and-impersonation]]) | One tenant per grant |
| Migration job | `nomo_migrator` (assumes `nomo_owner`) | CI/CD deploy step only ([[MT-separate-privileged-role-used]]) | Yes (DDL); no routine DML |
| Listed platform job (for example nightly deletion verification) | `nomo_platform_ops` (`BYPASSRLS`) | Defined job in the `platform-ops` task queue, short-lived credentials, two-person approval for new jobs | Yes, logged |
| Break-glass operator | `nomo_platform_ops` | Break-glass procedure ([[SEC-access-reviews]]) | Yes, logged, alerted |
| Reporting | `nomo_reporting` on replica / warehouse | Reporting service only ([[MT-cross-tenant-reporting-via-a]]) | Yes, read-only, curated views |

<!-- section:matrix -->
## Permission matrix

Permission matrix for **database roles** against table classes. Business permissions (who may file, who may see tribunal-only documents) are in [[PKG-rbac-abac-case-level-party]]; this matrix is the floor that those rules sit on.

| Role | Tenant-owned tables | Platform-level tables (tenant, plan, platform settings) | Shared reference tables (countries, currencies) | DDL | Bypass RLS |
|---|---|---|---|---|---|
| `nomo_app` | SELECT / INSERT / UPDATE / DELETE, rows where `tenant_id = app.current_tenant_id()` only | SELECT on listed tables; writes only on listed tables when in platform context | SELECT | No | No |
| `nomo_worker` | Same as `nomo_app` | Same as `nomo_app` | SELECT | No | No |
| `nomo_reporting` | No direct grant; SELECT on curated `reporting.*` views only | SELECT on `tenant`, `plan` | SELECT | No | Views are owned by a reporting owner role; see [[MT-cross-tenant-reporting-via-a]] |
| `nomo_platform_ops` | SELECT / UPDATE / DELETE, all tenants, for listed jobs | SELECT / UPDATE | SELECT | No | Yes |
| `nomo_migrator` → `nomo_owner` | Owner; FORCE RLS applies to it for DML | Owner | Owner | Yes | No (owner is subject to forced RLS) |
| Any role, no tenant context set | Zero rows; INSERT / UPDATE fail the WITH CHECK | As granted | As granted | — | — |

Conditions: DELETE on legally significant tables (case events, document versions, audit events) is revoked from `nomo_app` and `nomo_worker` regardless of RLS; deletion runs only through the retention package ([[PKG-data-retention-legal-hold-and]]) under `nomo_platform_ops`.

<!-- section:policy -->
## Policy model

**Policy pattern** (exact SQL in [[MT-rls-enabled-and-forced-on]]):

```sql
-- helper, owned by nomo_owner, created once per database
CREATE FUNCTION app.current_tenant_id() RETURNS uuid
  LANGUAGE sql STABLE PARALLEL SAFE
  AS $$ SELECT nullif(current_setting('app.tenant_id', true), '')::uuid $$;

ALTER TABLE cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE cases FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON cases
  AS PERMISSIVE FOR ALL TO nomo_app, nomo_worker
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());
```

`nullif(..., '')` matters: after a transaction that used `set_config(..., true)` ends, the setting reads as an empty string on that pooled connection, not as missing. Without `nullif` the cast fails noisily; with it the comparison is NULL and no rows match, which is the fail-closed behaviour we want. Missing context is surfaced separately by the Prisma extension raising `TenantContextMissingError` before any query is sent.

**Evaluation order**

1. Middleware resolves the tenant and checks the session's membership ([[MT-tenant-resolution]]).
2. Authorization evaluates role and case-level rules ([[PKG-policy-engine-permission-matrix]]).
3. The data-access call runs inside `withTenant(ctx, fn)`, which opens a transaction and sets `app.tenant_id`, `app.user_id` and `app.request_id` locally ([[MT-prisma-client-extension-wraps]]).
4. Postgres applies the tenant policy, then any restrictive policies on the table (for example case-participant visibility on tribunal-only documents, owned by [[DOM-documents-schema]]).

Restrictive policies (`AS RESTRICTIVE`) may narrow the tenant policy but never widen it; a permissive policy other than `tenant_isolation` on a tenant-owned table needs security review.

<!-- section:threats -->
## Threats and abuse cases

| STRIDE | Threat | Scenario | Mitigation | Residual risk |
|---|---|---|---|---|
| Information disclosure | Missing tenant filter | A new tRPC list procedure forgets `where: { tenantId }` | Forced RLS returns only the current tenant's rows | Low |
| Information disclosure | Context not set | Code uses a client outside `withTenant()` | Base client not exported; RLS returns zero rows; extension raises `TenantContextMissingError`; alert on count | Low |
| Information disclosure | Context leak across pooled connections | Session-level `SET app.tenant_id` survives on a PgBouncer server connection and the next request inherits it | Only `set_config(..., true)` allowed; lint bans `SET ` without `LOCAL`; PgBouncer validation test [R2] | Low |
| Spoofing | Tenant chosen by the client | Attacker sends `x-tenant-id` header or edits `tenantId` in a tRPC input | Middleware strips inbound tenant headers; tenant comes only from host / credential; inputs with `tenantId` ignored or rejected | Low |
| Elevation of privilege | RLS bypass through role | App credentials are those of the table owner or a `BYPASSRLS` role | [[MT-app-connects-as-a-non]]; role inventory test; FORCE RLS also binds the owner [R1] | Low |
| Tampering | Cross-tenant reference | Tenant A inserts a document row pointing at a case id of tenant B | Composite foreign keys `(tenant_id, case_id)` → `cases(tenant_id, id)` ([[MT-every-tenant-owned-table-carries]]) and WITH CHECK | Very low |
| Information disclosure | Views and functions bypass RLS | A `SECURITY DEFINER` function or a view owned by a privileged role reads across tenants | Views on tenant tables use `security_invoker = true` [R3]; SECURITY DEFINER functions need security review and are listed | Medium until lint covers functions |
| Information disclosure | Side channels | Unique constraint errors reveal another tenant's values (for example a global unique on case reference) | Unique constraints include `tenant_id`; identical not-found / no-access errors ([[APP-error-message-catalogue]]) | Low |
| Information disclosure | Derived stores | Search index, cache or vector store returns another tenant's hits | Tenant-scoped keys and indexes in [[PKG-caching]], [[PKG-search]], [[AI-rag]]; included in isolation tests | Medium (outside Postgres RLS) |
| Denial of service | Noisy neighbour | One SEBI ODR tenant bulk-files 50,000 matters and saturates the pool | Per-tenant rate limits and BullMQ group concurrency; small fixed Prisma pools ([[INF-small-fixed-prisma-pool-per]]) | Medium |
| Repudiation | Untraceable cross-tenant access | Operator uses privileged role without record | `nomo_platform_ops` sessions logged with `pgaudit`-style statement logging and alerted ([[OBS-security-events]]) | Low |
| Information disclosure | Backups and restores | Restoring one tenant restores rows of others into a shared environment | Point-in-time restore only into isolated recovery environment; tenant-level restore by filtered export ([[INF-backup-and-disaster-recovery]]) | Medium |

<!-- section:failure -->
## Denial behaviour

- **Not found and no access look the same.** A record of another tenant is indistinguishable from a record that does not exist: tRPC returns `NOT_FOUND`, the public API returns `404` with the shared problem type ([[APP-api-error-catalogue-problem]]), and the UI shows the identical "not found or no access" text ([[APP-error-message-catalogue]]).
- **Missing context** raises `TenantContextMissingError` in the package, returns a `500` problem with a correlation id (no tenant hints), and emits `security.tenant_context_missing` with route template, service and request id ([[OBS-security-events]]). More than zero events in production pages the on-call engineer.
- **Tenant mismatch** (session tenant differs from host tenant, or a job's tenant differs from the entity's tenant) is rejected with `403`, logged as `security.tenant_mismatch`, and counted per tenant.
- **WITH CHECK violations** (`new row violates row-level security policy`) are mapped to a generic `403` and logged with table name only, never with row values.

<!-- section:requirements -->
## Security requirements

Mapped to OWASP ASVS 5.0 chapter V8 Authorization [R4]; exact requirement numbers to be confirmed against the published 5.0.0 text before approval.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| ISO-SR-1 | The platform shall enforce tenant isolation in the database with forced RLS on every tenant-owned table. | V8 (multi-tenant / cross-tenant controls) |
| ISO-SR-2 | The application shall connect to Postgres only as roles without ownership, superuser or `BYPASSRLS`. | V8, V13 configuration |
| ISO-SR-3 | Tenant context shall be set only with transaction-local settings. | V8 |
| ISO-SR-4 | The tenant shall be derived from the host, credential or verified envelope, never from request body or client-set headers. | V8 operation-level authorization |
| ISO-SR-5 | Every foreign key between tenant-owned tables shall include `tenant_id`. | V8 |
| ISO-SR-6 | Unique constraints on tenant-owned tables shall include `tenant_id` unless the value is a random identifier. | V8 |
| ISO-SR-7 | Views over tenant-owned tables shall be created with `security_invoker = true`; `SECURITY DEFINER` functions touching tenant tables require security review and an entry in the function register. | V8 |
| ISO-SR-8 | Cross-tenant reads shall use only `nomo_reporting` or `nomo_platform_ops`, each logged. | V8, V16 logging |
| ISO-SR-9 | Not-found and access-denied responses for tenant resources shall be indistinguishable. | V8 |
| ISO-SR-10 | Every derived store (cache, search, vector, object storage, Temporal visibility) shall partition or prefix by tenant id. | V8 |

<!-- section:verification -->
## Verification

- **Automated, every pull request**: catalogue test (`packages/db/test/rls-coverage.spec.ts`) asserting `relrowsecurity` and `relforcerowsecurity` on every tenant-classified table and a `tenant_isolation` policy per table; role inventory test; isolation suite with two seeded tenants ([[MT-automated-tests-that-prove-one]]).
- **Automated, nightly per region**: the same catalogue checks against production via a read-only catalogue role; results stored as ISMS evidence.
- **Review**: CODEOWNERS for `packages/db/**` and `**/migrations/**` include a security reviewer ([[MT-lint-review-check-that-every]]).
- **Independent**: annual external penetration test with explicit cross-tenant scope (two test tenants per region, users with memberships in both), plus a test of the public API and aggregator API with credentials for tenant A against resources of tenant B ([[SEC-vulnerability-management]]).

<!-- section:questions -->
## Open questions

- [ ] Confirm the exact ASVS 5.0.0 requirement IDs for the mapping table.
- [ ] Should `SECURITY DEFINER` functions be banned outright on tenant tables, or allowed via a register? Proposed: register with security sign-off.
- [ ] Is a tenant-level restore (one tenant to a point in time) a contractual promise for any institutional tenant? It changes the backup design.
- [ ] Do any clients require a dedicated (silo) database? If so, record as a separate ADR rather than a tenancy mode.
- [ ] Which statement-logging approach for `nomo_platform_ops` (pgaudit on managed Postgres in each region, or application-level logging only)?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Four independent layers would each have to fail: (1) the tenant comes only from host or credential, inbound tenant headers are stripped; (2) authorization requires an active membership in that tenant; (3) forced RLS with `tenant_id = app.current_tenant_id()` on every tenant table, set per transaction, with the app role unable to bypass it; (4) composite foreign keys including `tenant_id` so even a write with a forged id cannot reference another tenant's row. The only roles that can span tenants (`nomo_platform_ops`, `nomo_reporting`, `nomo_migrator`) are not available to the application runtime and every use is logged.

<!-- check:enforcement -->
### Enforcement points and bypass paths

Because enforcement sits in Postgres, every path that reaches a tenant table is covered: RSC data loads, tRPC procedures, Server Actions, route handlers for the public API, BullMQ jobs and Temporal activities all use `nomo_app` or `nomo_worker` through `@nomology/db`. Paths outside Postgres are covered by their own package contracts and are listed as residual risk: object storage (tenant prefix plus signed URL issued after a database check, [[PKG-encryption-at-rest-signed-urls]]), search and vector stores, caches and Temporal visibility.

<!-- check:lifecycle -->
### Grant lifecycle and privileged access

Database roles are created by infrastructure code per region ([[INF-secrets-and-keys]]); credentials are rotated automatically every 90 days (proposed) and on staff departure. `nomo_platform_ops` credentials are short-lived (issued per job run or per break-glass session, maximum 4 hours) and never stored in application configuration. Human access to these roles is reviewed quarterly in [[SEC-access-reviews]].

<!-- check:resilience -->
### Failure modes and secrets

It fails closed: if the tenant setting is missing, empty or malformed, `app.current_tenant_id()` returns NULL and no rows match, and writes fail the WITH CHECK. If the tenant directory is unavailable, middleware serves from its regional cache for up to 10 minutes (proposed), then rejects requests rather than guessing. If application database credentials leak, the attacker still cannot bypass RLS, but can choose any tenant id; detection relies on connection-source alerts and rotation.

<!-- check:audit -->
### Audit trail

Tenant mismatches, missing-context errors and RLS WITH CHECK violations are security events ([[OBS-security-events]]). Every session of `nomo_platform_ops` and `nomo_migrator` is logged with job id, operator and statements. Business-level reads and changes are recorded by [[PKG-audit-trail]], which itself is tenant-owned and covered by RLS.

<!-- check:compliance -->
### Framework and legal mapping

ISO/IEC 27001:2022 A.8.3 (information access restriction), A.5.15 (access control), A.8.2 (privileged access rights), A.8.31 (separation of environments); SOC 2 CC6.1 and CC6.3 and C1.1 [R5]; DPDP Act s.8(5) reasonable security safeguards; GDPR Art. 32. Auditor evidence: CI and nightly catalogue reports, role inventory output, isolation suite results, pen-test report and access review records.

<!-- check:testing -->
### Verification and testing

Each row of the role matrix has an automated test: `nomo_app` and `nomo_worker` see zero rows of tenant B while in tenant A, and zero rows with no context; writes with a foreign `tenant_id` fail; `nomo_reporting` cannot read base tables; `nomo_app` cannot `SET ROLE` to privileged roles. These live in `packages/db/test/isolation/` and run on every pull request ([[MT-automated-tests-that-prove-one]]). The annual pen test covers what automation cannot: business-logic paths, derived stores and social-engineering of support access.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Table owners normally bypass row security unless the table has FORCE ROW LEVEL SECURITY; superusers and roles with BYPASSRLS always bypass it. If no policy exists, a default-deny policy is used.",
    "id": "R1",
    "kind": "vendor",
    "title": "PostgreSQL documentation: Row Security Policies",
    "url": "https://www.postgresql.org/docs/current/ddl-rowsecurity.html",
    "vendor": "PostgreSQL Global Development Group"
  },
  {
    "excerpt": "In transaction pooling mode, SET / RESET and other session-level state are not supported; SET LOCAL (transaction-scoped) is compatible.",
    "id": "R2",
    "kind": "vendor",
    "title": "PgBouncer features (SQL feature map for pooling modes)",
    "url": "https://www.pgbouncer.org/features.html",
    "vendor": "PgBouncer"
  },
  {
    "excerpt": "With security_invoker, access to underlying relations (including row security policies) is checked against the user of the view rather than the view owner.",
    "id": "R3",
    "kind": "vendor",
    "title": "PostgreSQL documentation: CREATE VIEW",
    "url": "https://www.postgresql.org/docs/current/sql-createview.html",
    "vendor": "PostgreSQL Global Development Group"
  },
  {
    "body": "OWASP",
    "excerpt": "Verification requirements for web application security, including the Authorization chapter.",
    "id": "R4",
    "ident": "ASVS",
    "kind": "standard",
    "title": "OWASP Application Security Verification Standard",
    "url": "https://owasp.org/www-project-application-security-verification-standard",
    "version": "5.0"
  },
  {
    "body": "AICPA",
    "excerpt": "Common criteria CC1–CC9 plus Availability (A), Confidentiality (C) and Privacy (P) criteria used in SOC 2 reports.",
    "id": "R5",
    "ident": "Trust Services Criteria",
    "kind": "standard",
    "title": "2017 Trust Services Criteria for Security, Availability, Processing Integrity, Confidentiality, and Privacy",
    "url": "https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022",
    "version": "2017 (revised points of focus 2022)"
  }
]
```

<!-- end -->
