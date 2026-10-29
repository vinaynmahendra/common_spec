---
id: "DEP-database-migration-strategy-zero"
title: "Database migration strategy (zero-downtime)"
parent: "DEP"
order: 3
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 2
syncHash: "06440a3e7cc2140c"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 15.3 Database migration strategy (zero-downtime)

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

Defines how Postgres schema and data changes are made so that every release can be deployed and rolled back without downtime, in each region independently, while the previous application version, Temporal workers and BullMQ workers are still running. It applies to every Prisma migration in `packages/db/prisma/migrations`. RLS policy requirements for new tables come from [[MT-prisma-migrations-include-rls]] and [[MT-rls-enabled-and-forced-on]]; connection settings for migrations from [[INF-separate-connection-settings-for]].

<!-- section:rules -->
## Rules

**Compatibility**
- **MIG-1** Every migration must work with both the currently deployed release (N-1) and the release being deployed (N). Breaking changes are split into **expand** (add), **migrate** (backfill and dual-write), and **contract** (remove) steps shipped in separate releases.
- **MIG-2** A contract step (drop column or table, add `NOT NULL`, tighten a constraint, rename) ships no earlier than the release after all regions run code that no longer depends on the old shape, and after any Temporal workflows or BullMQ jobs that carry the old shape have drained or been migrated.
- **MIG-3** Renames are never done in place: add the new column, dual-write, backfill, switch reads, then drop the old column.
- **MIG-4** Each migration folder name carries its phase: `<timestamp>_<expand|backfill|contract|safe>_<description>`.

**Tenant isolation**
- **MIG-5** A migration that creates a tenant-owned table in the same file adds the non-null `tenant_id`, the composite index led by `tenant_id`, `ENABLE ROW LEVEL SECURITY`, `FORCE ROW LEVEL SECURITY` and the tenant policy ([[MT-every-tenant-owned-table-carries]], [[MT-rls-enabled-and-forced-on]]). Platform-level tables are listed in `packages/db/platform-tables.txt` ([[MT-platform-level-tables]]).
- **MIG-6** Migrations never disable RLS, alter policies to be permissive, or grant `BYPASSRLS`; changes to policies need `security` approval.

**Locking and safety**
- **MIG-7** Each migration starts with `SET lock_timeout = '5s'` and `SET statement_timeout = '15min'` (proposed values). A migration that cannot get its lock fails and is retried by the pipeline, rather than queueing behind live traffic.
- **MIG-8** Indexes on existing tables are created with `CREATE INDEX CONCURRENTLY` in a migration file that contains only that statement (it cannot run inside a transaction block).
- **MIG-9** Adding `NOT NULL` to an existing column uses `ADD CONSTRAINT ... CHECK (col IS NOT NULL) NOT VALID`, then `VALIDATE CONSTRAINT` in a later migration. New foreign keys on existing tables use `NOT VALID` then `VALIDATE`.
- **MIG-10** No column type changes that rewrite the table, no volatile defaults on new columns of large tables, no `ALTER TYPE ... ADD VALUE` used in the same release that writes the new value.

**Data changes**
- **MIG-11** Migration files contain schema changes only. Backfills over tenant data run as a Temporal workflow (`schema-backfill`) that processes one tenant at a time in batches of at most 1,000 rows, under the app role with tenant context set per transaction, so RLS stays in force. Backfills are idempotent and resumable.
- **MIG-12** Reference and seed data changes follow [[PKG-reference-and-seed-data]].

**Running migrations**
- **MIG-13** Migrations run as a one-off `migrate` task (same image digest as the release) with the privileged migration role ([[MT-separate-privileged-role-used]]) on a direct connection, not through PgBouncer, before the new application version receives traffic.
- **MIG-14** Each region runs its migrations independently in the region wave order of [[DEP-environment-promotion-and-multi]]. A failure stops the rollout in that region and all later waves.
- **MIG-15** There is no down migration in production. Recovery from a bad migration is a forward fix; point-in-time restore is a disaster-recovery action under [[INF-backup-and-disaster-recovery]], not a release tool.
- **MIG-16** CI checks that `schema.prisma` and the migrations folder agree (`prisma migrate diff` against a shadow database) and that each region's `_prisma_migrations` history matches the release after deploy.

<!-- section:rationale -->
## Rationale

- **MIG-1, MIG-2** Blue-green and canary releases ([[DEP-blue-green-canary-releases]]) run N-1 and N side by side, and rollback means sending traffic back to N-1, so the schema must suit both. Long-running Temporal workflows can hold payloads with old field names for months.
- **MIG-7** Postgres lock queues are the usual cause of "zero-downtime" migrations taking a site down: an `ALTER TABLE` waiting for a lock blocks every query behind it.
- **MIG-11** Running backfills as the migration role would bypass RLS; running them per tenant under the app role keeps isolation and lets a single tenant's backfill be paused.
- **MIG-13** PgBouncer transaction pooling does not suit long DDL sessions and `CONCURRENTLY` operations; migrations need a direct connection [R1].

<!-- section:tooling -->
## Tooling and configuration

- Prisma Migrate (`prisma migrate deploy`) inside the `migrate` image.
- `squawk` linter on every new migration SQL file, with rules for non-concurrent indexes, unsafe `NOT NULL`, table-rewriting type changes and missing `lock_timeout`.
- Custom `rls-migration-check` that parses new `CREATE TABLE` statements and fails unless the table is in the platform list or has `tenant_id`, `ENABLE`/`FORCE ROW LEVEL SECURITY` and a policy ([[MT-lint-review-check-that-every]]).
- Migration rehearsal job: applies pending migrations to a staging database loaded with production-sized synthetic data and records lock wait and duration.
- Temporal workflow `schema-backfill` in `packages/workflows` with progress exposed as a Query.

Example expand migration:

```sql
-- 20261101090000_expand_case_withdrawal_reason/migration.sql
SET lock_timeout = '5s';
ALTER TABLE cases ADD COLUMN withdrawal_reason_code text;
CREATE TABLE case_withdrawal_requests (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  case_id uuid NOT NULL,
  requested_at timestamptz NOT NULL,
  reason_code text NOT NULL
);
CREATE INDEX ON case_withdrawal_requests (tenant_id, case_id);
ALTER TABLE case_withdrawal_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE case_withdrawal_requests FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON case_withdrawal_requests
  USING (tenant_id = current_setting('app.tenant_id')::uuid)
  WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);
```

<!-- section:enforcement -->
## Enforcement

| Rule | Where | Fails |
|---|---|---|
| MIG-4 | CI `migration-lint` | Folder name without phase |
| MIG-5, MIG-6 | `rls-migration-check` (required); CODEOWNERS `platform-data` + `security` on migrations | New tenant table without RLS; policy change without security approval |
| MIG-7 to MIG-10 | `squawk` (required) | Unsafe statement |
| MIG-2 | `contract` migrations need a PR label linking the expand release and a checklist confirming all regions are on that release; release manager approval | Missing label |
| MIG-11 | Review; lint rule forbidding `UPDATE`/`INSERT` on tenant tables in migration files | Data statement in schema migration |
| MIG-13, MIG-14 | Promotion workflow runs `migrate` task per region before traffic shift | Rollout stops |
| MIG-16 | CI `prisma migrate diff`; post-deploy check | Drift |

<!-- section:examples -->
## Examples

Renaming `cases.claim_amount` to `claim_value_minor`:
1. Release 41 (expand): add `claim_value_minor`; code writes both and reads the old.
2. `schema-backfill` workflow copies values per tenant.
3. Release 42: code reads the new column, still writes both.
4. Release 43 (contract): stop writing the old column; drop it once all regions are on 43 and no workflow payload references it.

Bad: `ALTER TABLE cases RENAME COLUMN claim_amount TO claim_value_minor;` in one release; every N-1 container fails the moment the migration runs.

<!-- section:exceptions -->
## Exceptions

A migration that needs a maintenance window (for example a large table rewrite with no online alternative) needs an ADR, a high-risk change record ([[DEP-release-notes-and-change]]), tenant notice per contract, and is scheduled outside every affected tenant's protected windows. MIG-5 and MIG-6 are non-waivable.

<!-- section:questions -->
## Open questions

- [ ] Confirm the exact Prisma Migrate behaviour for `CREATE INDEX CONCURRENTLY` in a single-statement migration with the Prisma version chosen in [[APP-framework-dependencies]].
- [ ] Confirm `lock_timeout` and `statement_timeout` values after the first rehearsal on production-sized data.
- [ ] How long must a contract step wait for long-running Temporal workflows? Needs a payload versioning rule ([[DEP-blue-green-canary-releases]]).
- [ ] Should backfills that touch every tenant need tenant notice when they run for hours?

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Linting (`squawk`), RLS checking, phase naming and drift detection are required CI checks; contract timing is enforced by a required label plus release-manager approval because it depends on the state of all regions. Per-region execution order is enforced by the promotion workflow.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

Expand/contract is the core of this standard (MIG-1 to MIG-3). RLS: MIG-5 and MIG-6 require `tenant_id`, forced RLS and a policy on every new tenant table and forbid weakening policies. Backfills run under the app role with tenant context so RLS is never bypassed (MIG-11). The privileged role is used only in the `migrate` task.

<!-- check:onboarding -->
### Onboarding and usability

`pnpm db:migration:new --phase expand <name>` creates a correctly named folder with the `SET lock_timeout` header and, for new tables, an RLS block template. Linter messages cite MIG rule numbers.

<!-- check:exceptions -->
### Exceptions

Maintenance-window migrations require an ADR, a high-risk change record and tenant notice. RLS rules are non-waivable.

<!-- check:compliance -->
### Compliance evidence

Supports ISO/IEC 27001:2022 change management and secure development controls; migration PRs, approvals and per-region migration logs are change evidence. RLS checks support the tenant isolation commitments in client security questionnaires.

<!-- check:measurement -->
### Adoption measurement

Tracked: migrations per release by phase, longest lock wait in rehearsal, number of expand steps whose contract step is overdue (target 0 older than 3 releases), and migration-caused rollbacks.

<!-- check:ownership -->
### Ownership and change

Owner: platform-data lead; `security` co-approves anything touching RLS.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Lists which PostgreSQL features work in each pooling mode; session-level SET and RESET are not supported in transaction pooling mode.",
    "id": "R1",
    "kind": "vendor",
    "title": "PgBouncer features",
    "url": "https://www.pgbouncer.org/features.html",
    "vendor": "PgBouncer"
  }
]
```

<!-- end -->
