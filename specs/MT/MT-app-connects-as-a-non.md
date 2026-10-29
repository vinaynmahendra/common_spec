---
id: "MT-app-connects-as-a-non"
title: "Non-owner application role"
parent: "MT-prisma-implementation"
order: 2
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "App connects as a non-owner, non-superuser role so RLS cannot be bypassed"
links: []
rev: 3
syncHash: "37688da31351a8bb"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 3.3.4.2 Non-owner application role

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> App connects as a non-owner, non-superuser role so RLS cannot be bypassed

<!-- section:statement -->
## Statement

The application runtime (web containers, Temporal workers and BullMQ workers) shall connect to Postgres only as the roles `nomo_app` and `nomo_worker`, which shall not own any table, shall not be superusers, shall not have the `BYPASSRLS` attribute, and shall not be members of any role that has these properties.

<!-- section:rationale -->
## Rationale and source

In Postgres, superusers and roles with `BYPASSRLS` always bypass row security, and table owners bypass it unless the table is forced [R1]. If the app could connect as any of these, a single missing filter would expose every tenant. Least-privilege application accounts that do not own the schema are standard database practice [R2]. Source: [[ADR-tenant-isolation]], [[MT-isolation-strategy]].

<!-- section:acceptance -->
## Acceptance criteria

- **Given** the production database of each region, **when** the role inventory check runs, **then** `nomo_app` and `nomo_worker` have `rolsuper = false`, `rolbypassrls = false`, `rolcreaterole = false`, `rolcreatedb = false`, own zero relations, and `pg_has_role` returns false for `nomo_owner`, `nomo_migrator` and `nomo_platform_ops`.
- **Given** a session as `nomo_app`, **when** it runs `SET ROLE nomo_owner` or `ALTER TABLE cases DISABLE ROW LEVEL SECURITY`, **then** Postgres rejects it.
- **Negative**: **given** a container configured with the migrator's credentials, **when** it starts, **then** the start-up check (`SELECT current_user, rolbypassrls ...`) fails and the container exits before serving traffic.

<!-- section:verification -->
## Verification method

Test: `packages/db/test/roles.spec.ts` in CI; nightly role inventory job per region stores results as ISMS evidence ([[SEC-isms-controls]]). Demonstration: start-up guard in `@nomology/db`.

<!-- section:priority -->
## Priority

Must. Phase 0.

<!-- section:questions -->
## Open questions

- [ ] On Azure Database for PostgreSQL Flexible Server, confirm which built-in roles the administrator account grants and that `nomo_app` inherits none of them.

<!-- section:notes -->
## Notes

Roles are created by infrastructure code ([[INF-secrets-and-keys]], [[INF-database]]), not by Prisma migrations. Managed-database master users (for example the RDS master user) are never used by the application and are held under break-glass.

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Yes. It is what makes RLS a hard boundary rather than advice.

<!-- check:singular -->
### Singular

One constraint: the attributes of the runtime roles. The privileged roles are a separate requirement ([[MT-separate-privileged-role-used]]).

<!-- check:verifiable -->
### Verifiable

The role inventory query gives a pass/fail result per region, and the start-up guard demonstrates the negative case.

<!-- check:traced -->
### Traced

Traces to [[ADR-tenant-isolation]] and ISO-SR-2 in [[MT-isolation-strategy#requirements]]; forward to `roles.spec.ts` and the nightly inventory job.

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
    "excerpt": "Applications should connect with least-privilege accounts that do not own the schema.",
    "id": "R2",
    "kind": "web",
    "publisher": "OWASP",
    "title": "OWASP Database Security Cheat Sheet",
    "url": "https://cheatsheetseries.owasp.org/cheatsheets/Database_Security_Cheat_Sheet.html"
  }
]
```

<!-- end -->
