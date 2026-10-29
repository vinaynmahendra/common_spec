---
id: "MT-separate-privileged-role-used"
title: "Privileged migration role"
parent: "MT-prisma-implementation"
order: 3
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Separate privileged role, used only by migrations and controlled platform-admin jobs"
links: []
rev: 3
syncHash: "9371f2a9a27d3b44"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 3.3.4.3 Privileged migration role

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Separate privileged role, used only by migrations and controlled platform-admin jobs

<!-- section:statement -->
## Statement

The platform shall perform schema changes only as `nomo_migrator` (which assumes the owning role `nomo_owner`) from the deployment pipeline, and cross-tenant data operations only as `nomo_platform_ops` from listed jobs in the `platform-ops` worker or an approved break-glass session; neither role's credentials shall be available to web or ordinary worker containers.

<!-- section:rationale -->
## Rationale and source

Migrations need ownership to create tables and policies; some platform jobs (offboarding deletion, deletion verification, re-encryption) must span tenants. Concentrating these powers in two roles that the runtime cannot reach keeps [[MT-app-connects-as-a-non]] true and makes privileged use auditable (ISO/IEC 27001:2022 A.8.2 privileged access rights).

<!-- section:acceptance -->
## Acceptance criteria

- **Given** a release, **when** the pipeline runs `prisma migrate deploy` in a region, **then** it fetches `nomo_migrator` credentials from the regional secrets manager for that step only and the session is logged with the pipeline run id.
- **Given** a listed job (for example `tenant-offboarding-delete`), **when** it runs, **then** it uses short-lived `nomo_platform_ops` credentials, sets `app.job_id`, and every statement is logged.
- **Given** a job not in `packages/db/platform-ops-jobs.yaml`, **when** it requests `nomo_platform_ops` credentials, **then** the request is denied.
- **Negative**: **given** the web or worker task definition, **when** inspected, **then** it references no secret of `nomo_migrator` or `nomo_platform_ops`.

<!-- section:verification -->
## Verification method

Inspection: IaC policy check (task definitions / container app secrets) in CI. Test: platform-ops job registry test. Evidence: privileged session logs reviewed monthly and in quarterly access reviews ([[SEC-access-reviews]]).

<!-- section:priority -->
## Priority

Must. Phase 1.

<!-- section:questions -->
## Open questions

- [ ] Should `nomo_platform_ops` be split further (for example a delete-only role for offboarding)?
- [ ] Maximum credential lifetime for platform-ops jobs: 4 hours proposed.

<!-- section:notes -->
## Notes

`nomo_owner` is `NOLOGIN`. Because RLS is forced, even `nomo_owner` is subject to tenant policies for DML; data backfills in migrations therefore either iterate tenants with `set_config` or run as a listed platform-ops job, never as ad-hoc SQL. Adding a job to the platform-ops registry needs two approvers (platform lead and security).

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Yes. Without it either migrations would run as the app role (impossible) or the app role would need ownership (breaks RLS).

<!-- check:complete -->
### Complete and scoped

Covers both privileged uses (DDL and cross-tenant DML), where credentials live, how jobs are allowed, and the denial case. Break-glass procedure is referenced to [[SEC-access-reviews]].

<!-- check:verifiable -->
### Verifiable

IaC inspection and the job registry test are pass/fail; session logs give operating evidence.

<!-- check:consistent -->
### Consistent

Consistent with the role matrix in [[MT-isolation-strategy#matrix]].

<!-- end -->
