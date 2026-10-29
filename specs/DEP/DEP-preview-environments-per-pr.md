---
id: "DEP-preview-environments-per-pr"
title: "Preview environments per PR"
parent: "DEP"
order: 2
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 2
syncHash: "362a2689aca41018"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 15.2 Preview environments per PR

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

Gives every pull request that changes a deployable app its own short-lived, production-shaped stack, so reviewers, product owners and automated end-to-end and accessibility suites can exercise the change before it merges. Previews run in the non-prod account, hold synthetic data only and are destroyed automatically. What a preview environment is allowed to hold is set in [[FND-environments]].

<!-- section:rules -->
## Rules

- **PREV-1** A preview is created when a PR changes `apps/web`, `apps/worker-*`, `apps/doc-viewer` or any package they depend on, and is updated on every push. PRs labelled `no-preview` and fork PRs get none.
- **PREV-2** Each preview runs the PR's images for `web`, `worker-temporal` and `worker-jobs` as ECS Fargate services in the shared preview cluster, at `pr-<n>.preview.<nonprod-domain>`, with tenant subdomains `<tenant>.pr-<n>.preview.<nonprod-domain>` covered by a wildcard certificate.
- **PREV-3** Each preview gets its own Postgres database (`pr_<n>`) on the shared non-prod instance, reached through PgBouncer in transaction mode as the non-owner app role. Migrations run with the migration role exactly as in production, then `pnpm seed --profile preview` loads the fixture tenants `arb-inst`, `odr-inst`, `cord` and `us-demo`.
- **PREV-4** Redis is shared with a key and BullMQ prefix of `pr<n>:`; Temporal uses the shared `preview-in` namespace with task queues suffixed `-pr<n>` (for example `cases-pr1234`) and workflow IDs prefixed accordingly.
- **PREV-5** Object storage uses a per-preview prefix in the preview bucket with a 7-day lifecycle rule. Malware scanning runs as in production.
- **PREV-6** Previews are reachable only after SSO sign-in to the engineering identity provider, in front of the app's own sign-in. They are never public and send `noindex`.
- **PREV-7** Outbound email, SMS and WhatsApp go only to Mailpit or sandbox providers; webhooks only to an internal request-capture endpoint.
- **PREV-8** A preview is destroyed when the PR is merged or closed, or after 5 days without a push; the database is dropped and the storage prefix deleted.
- **PREV-9** No more than 25 previews run at once (proposed); the oldest idle preview is reclaimed first. Each preview service runs at minimum size.
- **PREV-10** Previews use only non-prod secrets, scoped to the `preview` GitHub environment.

<!-- section:rationale -->
## Rationale

- **PREV-3** A per-PR database lets migrations be tested from scratch on every PR, and keeps the PgBouncer and forced-RLS behaviour identical to production.
- **PREV-4** Temporal namespaces per PR would be slow to create and clean up; suffixed task queues give the same isolation for a review stack.
- **PREV-6** Even synthetic data can expose unreleased features to the public; a second sign-in layer prevents previews from becoming a phishing surface that looks like a tenant portal.

<!-- section:tooling -->
## Tooling and configuration

- GitHub Actions workflow `preview.yml` (create/update on push, destroy on close) and a nightly `preview-reaper` job.
- Terraform module `infra/modules/preview-env` (ECS services, target group rules, DNS records) driven with per-PR variables, or a lightweight script against ECS APIs (see questions).
- ALB OIDC authentication with the engineering identity provider in front of preview listeners.
- PR comment bot posting the preview URLs, fixture user sign-in hints and test results.

<!-- section:enforcement -->
## Enforcement

| Rule | Enforcement |
|---|---|
| PREV-1, PREV-8 | Workflow triggers; reaper job; daily report of orphaned resources |
| PREV-3, PREV-4 | Preview env schema in `@nomology/env` requires `APP_ENV=preview`, a `pr_<n>` database and suffixed task queues |
| PREV-6 | ALB listener rule created by the module; synthetic check that an unauthenticated request gets redirected |
| PREV-7 | Notifications allow-list when `APP_ENV != prod` ([[FND-environments]] ENVS-7) |
| PREV-9 | Workflow refuses to create beyond the limit and reclaims the oldest idle preview |
| PREV-10 | OIDC role for `preview` can read only `/nomology/preview/*` secrets |

<!-- section:examples -->
## Examples

Good: a PR changing the secretariat bulk-assign action posts `https://odr-inst.pr-1234.preview.<nonprod-domain>`; the Playwright smoke suite signs in as the `odr-inst` secretariat fixture user and runs the bulk-assign journey and axe checks.

Bad: sharing a preview link with a client for acceptance; client acceptance belongs in UAT.

<!-- section:exceptions -->
## Exceptions

Longer-lived previews (for example for a design review spanning two weeks) need the `keep-preview` label, approved by the DevOps lead, with an end date in the PR description.

<!-- section:questions -->
## Open questions

- [ ] Terraform per preview or a scripted ECS approach? Terraform is consistent but slower to create.
- [ ] Is a shared Temporal namespace acceptable, or do we need per-PR namespaces for workflow-versioning tests?
- [ ] Budget ceiling for previews per month.
- [ ] Do previews need an Azure variant, or is staging-az enough for Azure-specific changes?

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Creation, teardown, size limits and secret scope are enforced by the workflow, the reaper and IAM; SSO gating is enforced by the ALB rule and verified by a synthetic check. Nothing relies on review alone except the `keep-preview` exception.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

Synthetic data only, non-prod secrets only, no public access, messaging allow-lists, and the same forced RLS and PgBouncer setup as production so isolation bugs show up before merge.

<!-- check:measurement -->
### Adoption measurement

Tracked: preview creation time (target under 8 minutes), number of orphaned resources (target 0), monthly preview cost, and share of web PRs whose e2e smoke ran on a preview.

<!-- check:ownership -->
### Ownership and change

Owner: DevOps lead.

<!-- end -->
