---
id: "INF-separate-connection-settings-for"
title: "Connection settings per workload"
parent: "INF-database-connection-handling"
order: 5
type: "feature"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "One connection profile per workload (web, BullMQ workers, Temporal workers, migrations, reporting, platform admin jobs, Temporal server) with its own role, endpoint, pool and timeouts"
links: []
rev: 4
syncHash: "af1d0e5d0eef2de7"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 14.7.4 Connection settings per workload

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> One connection profile per workload (web, BullMQ workers, Temporal workers, migrations, reporting, platform admin jobs, Temporal server) with its own role, endpoint, pool and timeouts

<!-- section:statement -->
## Statement

The platform shall define one named connection profile per workload — `web`, `worker-jobs`, `worker-temporal`, `migrate`, `reporting`, `platform-admin-job` and `temporal-server` — each with its own database role, endpoint, pool size, timeouts and `application_name`, and no workload shall connect with another workload's profile.

<!-- section:rationale -->
## Rationale and source

Workloads have opposite needs: web requests must fail fast; workers run longer statements; migrations need a direct, session-mode connection with a short lock timeout (Prisma Migrate cannot run reliably through PgBouncer [R1]); reporting must be read-only, cross-tenant and on the replica ([[MT-cross-tenant-reporting-via-a]]); the privileged role must be usable only by migrations and controlled admin jobs ([[MT-separate-privileged-role-used]]). Separate roles also make `pg_stat_activity`, logs and alerts attributable.

| Profile | Role | Endpoint | Pool | Statement timeout | Other |
|---|---|---|---|---|---|
| `web` | `nomo_app` | PgBouncer 6432 | 5 | 15 s | Idle-in-tx 10 s |
| `worker-jobs` | `nomo_worker` | PgBouncer 6432 | 3 | 120 s | Idle-in-tx 30 s |
| `worker-temporal` | `nomo_worker` | PgBouncer 6432 | 3 | 120 s | `application_name=worker-temporal-<queue>` |
| `migrate` | `nomo_migrator` | Direct primary 5432 | 1 | none | `lock_timeout 5s`; only the `migrate` task has the secret |
| `reporting` | `nomo_reporting` | Read replica 5432 | 5 | 300 s | `default_transaction_read_only = on` |
| `platform-admin-job` | `nomo_platform_ops` | Direct primary 5432 | 2 | 300 s | Break-glass approval, audited ([[APP-platform-admin-and-support]]) |
| `temporal-server` | `temporal` | Direct to `temporal-<region>` instance | Temporal `maxConns` | n/a | Separate instance ([[INF-temporal#config]]) |

Profiles are defined once in `packages/data-access/src/profiles.ts` and selected by the `DB_PROFILE` environment variable validated at start-up ([[FND-environment-management]]). Secrets are scoped per task role so a container can read only its own profile's credential ([[INF-secrets-and-keys]]).

<!-- section:acceptance -->
## Acceptance criteria

- **Given** the `web` service, **when** it starts, **then** it connects as `nomo_app` through PgBouncer with `application_name=web`, visible in `pg_stat_activity`.
- **Given** the `migrate` task, **when** it runs `prisma migrate deploy`, **then** it connects directly to the primary as `nomo_migrator` and a lock wait longer than 5 s aborts the migration.
- **Given** the reporting service, **when** it attempts an `UPDATE`, **then** the replica rejects it (read-only transaction).
- **Negative**: **Given** the `web` task role, **when** it tries to read the `nomo_migrator` secret, **then** Secrets Manager denies access.
- **Negative**: **Given** `DB_PROFILE` is missing or unknown, **when** a container starts, **then** start-up fails.

<!-- section:verification -->
## Verification method

- **Test**: integration test asserts role, endpoint and `application_name` per profile; IAM policy test (Access Analyzer / policy simulator) for secret access per task role.
- **Inspection**: weekly check that each login role's default settings match the profile table.

<!-- section:priority -->
## Priority

Must. Phase 1 (`web`, `migrate`), Phase 2–3 (workers, Temporal), Phase 7 (`reporting`).

<!-- section:notes -->
## Notes

**Open questions**

- [ ] Should BullMQ and Temporal workers use separate logins under the canonical `nomo_worker` role (both inherit its grants) for finer attribution and separate PgBouncer pools? This would extend the role inventory in [[MT-app-connects-as-a-non]].
- [ ] On Azure, can the migration role use Entra ID authentication with the same direct-endpoint rule?

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Without separate profiles, migrations would run through PgBouncer (which Prisma Migrate does not support reliably [R1]), reporting could run cross-tenant reads on the primary with the app role, and the privileged migrator credential would be available to web containers.

<!-- check:complete -->
### Complete and scoped

Covers all seven workload types that connect to Postgres in a region, including the Temporal server's own database; error cases (missing profile, wrong secret access, write on replica) are in the acceptance criteria.

<!-- check:verifiable -->
### Verifiable

Integration tests per profile plus IAM policy tests for secret scoping, both in CI.

<!-- check:consistent -->
### Consistent

Pool sizes match [[INF-small-fixed-prisma-pool-per]], timeouts match [[INF-timeouts-on-connect-query-and]], and roles match the role model in [[INF-database#config]] and the MT requirements on non-owner and privileged roles.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "PgBouncer must run in transaction mode; with PgBouncer 1.21.0 or later do not set pgbouncer=true and set max_prepared_statements above 0; Prisma CLI / Migrate needs a direct connection.",
    "id": "R1",
    "kind": "vendor",
    "title": "Prisma ORM v7: Configure Prisma Client with PgBouncer",
    "url": "https://www.prisma.io/docs/orm/v7/prisma-client/setup-and-configuration/databases-connections/pgbouncer",
    "vendor": "Prisma"
  }
]
```

<!-- end -->
