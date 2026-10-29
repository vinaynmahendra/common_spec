---
id: "FND-environments"
title: "Environments"
parent: "FND"
order: 4
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: "local, dev, staging, UAT, production"
links: []
rev: 2
syncHash: "3bc6b0a1fd7725f8"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 1.4 Environments

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> local, dev, staging, UAT, production

<!-- section:purpose -->
## Purpose and scope

Defines the set of environments the platform runs in, what each one is for, which cloud account it lives in, what data it may hold and who can access it. Promotion between environments is specified in [[DEP-environment-promotion-and-multi]]; per-PR previews in [[DEP-preview-environments-per-pr]].

<!-- section:rules -->
## Rules

**Environment set**

| Env | Purpose | Regions | Account | Data allowed | Temporal namespace | Access |
|---|---|---|---|---|---|---|
| local | Developer laptop via Docker Compose: Postgres, PgBouncer (transaction mode), Redis, Temporal dev server, MinIO, Mailpit | n/a | none | Synthetic only | `local-in` | Developer |
| dev | Shared integration of `main`; auto-deployed | one non-prod region | non-prod | Synthetic only | `dev-in` | Engineering (SSO) |
| preview | One per pull request, short-lived | same as dev | non-prod | Synthetic only | shared `preview-in`, task queues suffixed by PR | Engineering, product (SSO) |
| staging | Release candidate in production-like topology | India, Singapore, US (+ one Azure staging) | staging per region | Synthetic only, production-like volumes | `staging-<region>` | Engineering, QA |
| UAT | Client acceptance of a release or tenant configuration | client's home region | UAT per region | Synthetic or client-supplied test data (see ENVS-5) | `uat-<region>` | Named client users, implementation team |
| prod | Live tenants | India, Singapore, US; Azure where a client requires it | prod per region | Real data | `prod-<region>` | Just-in-time, audited |

**Rules**
- **ENVS-1** Production in each region runs in its own cloud account (AWS) or subscription (Azure), separate from all non-production accounts. No network path exists from non-prod to prod.
- **ENVS-2** Real personal data and case content exist only in production. Production data is never copied to another environment, including for debugging; the debugging route is just-in-time access in production under [[PKG-support-access-and-impersonation]].
- **ENVS-3** Every environment uses the same container images (by digest), the same Prisma migrations and the same topology pattern (app role behind PgBouncer in transaction mode, forced RLS); environments differ only by configuration and size.
- **ENVS-4** Staging exists in every production region and on Azure, so region-specific configuration (endpoints, KMS keys, messaging providers) is exercised before production.
- **ENVS-5** UAT uses synthetic data by default. If a client wants to test with their own documents, the client confirms in writing that the data contains no real personal data; otherwise the UAT tenant is created in production as a sandbox tenant with production controls.
- **ENVS-6** Each environment has a fixed URL pattern: `*.dev.<nonprod-domain>`, `pr-<n>.preview.<nonprod-domain>`, `*.staging-<region>.<nonprod-domain>`, `*.uat-<region>.<domain>`, production tenant subdomains and custom domains per [[MT-tenant-resolution]]. Non-production pages send `X-Robots-Tag: noindex` and show an environment banner.
- **ENVS-7** Non-production messaging providers send only to allow-listed addresses and numbers (Mailpit locally; sandbox senders in dev, preview and staging).
- **ENVS-8** Seed data in every non-prod environment comes from `@nomology/testing` fixture tenants: `arb-inst` (arbitral institution, Singapore), `odr-inst` (SEBI ODR institution, India), `cord` (CORD tenant, India) and `us-demo` (US).
- **ENVS-9** Production access by engineers is just-in-time with approval, time-boxed and logged; there is no standing write access to production databases.

<!-- section:rationale -->
## Rationale

- **ENVS-1** Account separation is the strongest practical boundary on AWS and gives clean evidence for the ISO 27001 control on separating environments.
- **ENVS-2** Copying arbitration records to lower environments would breach confidentiality obligations in institutional rules and the purpose limits of DPDP, GDPR and PDPA, and would move data out of its region.
- **ENVS-3** If staging used direct connections instead of PgBouncer, tenant-context bugs that only appear under transaction pooling would first show up in production.
- **ENVS-7** A test notice sent to a real party could be mistaken for legal service.

<!-- section:tooling -->
## Tooling and configuration

- Docker Compose file `docker-compose.dev.yml` with pinned images; `pnpm dev:up`, `pnpm db:reset`, `pnpm seed`.
- Terraform workspaces per environment and region ([[INF-cloud-and-iac]]).
- GitHub Environments: `dev`, `preview`, `staging-in`, `staging-sg`, `staging-us`, `staging-az`, `uat-<region>`, `prod-in`, `prod-sg`, `prod-us`, `prod-az-<client>`.
- Access: AWS IAM Identity Center permission sets per environment class; production via just-in-time elevation.

<!-- section:enforcement -->
## Enforcement

| Rule | Enforcement |
|---|---|
| ENVS-1 | Terraform account structure; SCPs deny cross-account roles from non-prod into prod |
| ENVS-2 | No snapshot sharing permission outside prod accounts (SCP); quarterly access review checks restore targets |
| ENVS-3 | Deploy pipeline accepts only image digests from the `main` build; migrations run from the same artefact |
| ENVS-4 | Promotion gate requires a green staging deploy in the target region |
| ENVS-6 | Middleware adds the banner and `noindex` when `APP_ENV != prod` |
| ENVS-7 | Notifications package refuses non-allow-listed recipients when `APP_ENV != prod` (unit-tested) |
| ENVS-9 | Identity Center configuration; access logs reviewed under [[SEC-access-reviews]] |

<!-- section:examples -->
## Examples

Good: a bug reported by a SEBI ODR tenant is reproduced in staging-in with the `odr-inst` fixture and a synthetic case with the same shape.

Bad: restoring last night's prod-in snapshot into staging "just for an hour".

<!-- section:exceptions -->
## Exceptions

ENVS-1, ENVS-2 and ENVS-7 are non-waivable. Requests for extra environments (for example a dedicated performance environment) go through [[FND-governance]] with a cost estimate.

<!-- section:questions -->
## Open questions

- [ ] Which non-prod AWS region hosts dev and preview? (Synthetic data only, so cost and latency decide.)
- [ ] Do we need a separate performance-test environment or is staging sized up during load tests ([[TST-performance-and-load-testing]])?
- [ ] Confirm ENVS-5 with legal: is a client's written confirmation enough for UAT, or must client UAT always be a sandbox tenant in production?
- [ ] Is a UAT environment per region needed from Phase 3, or only when the first client acceptance starts?

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Account separation and snapshot restrictions are enforced by Terraform and service control policies; image and migration parity by the deploy pipeline; banner and messaging allow-lists by code with unit tests. Data rules (ENVS-2, ENVS-5) are also checked in quarterly access reviews.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

Personal data: ENVS-2, ENVS-5 and ENVS-8 keep real data in production only. Tenant isolation: ENVS-3 keeps forced RLS and PgBouncer transaction pooling identical in every environment. Secrets: each account has its own secrets manager, so a non-prod credential can never open a prod resource.

<!-- check:compliance -->
### Compliance evidence

Directly supports ISO/IEC 27001:2022 Annex A controls on separation of development, test and production environments and on protection of test information, and SOC 2 change-management criteria. Evidence: account structure in Terraform, SCPs, Identity Center assignments and access logs.

<!-- check:ownership -->
### Ownership and change

Owner: DevOps lead. Changes to the environment set need CTO approval because they change cost and audit scope.

<!-- end -->
