---
id: "DEP-blue-green-canary-releases"
title: "Blue-green / canary releases, rollback"
parent: "DEP"
order: 4
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 2
syncHash: "a5bb8f0ac567e0d1"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 15.4 Blue-green / canary releases, rollback

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

Defines how a new release replaces the old one in a region without downtime, how much traffic it gets before it is trusted, what signals decide whether it continues or rolls back, and how Temporal and BullMQ workers are switched safely. It applies to the `web`, `doc-viewer`, `worker-temporal` and `worker-jobs` services on ECS, and to Azure Container Apps deployments. Region ordering is in [[DEP-environment-promotion-and-multi]]; database compatibility in [[DEP-database-migration-strategy-zero]].

<!-- section:rules -->
## Rules

**Web and doc-viewer (HTTP services)**
- **REL-1** Deploy as blue-green: the new version (green) starts in a separate target group (ECS) or revision (Container Apps), must pass health checks and a synthetic smoke suite on its private test listener, then receives traffic in steps: **5% for 15 minutes, 25% for 15 minutes, 100%** (proposed).
- **REL-2** At each step an automated analysis compares green against blue: HTTP 5xx rate, p95 latency per route group, error-boundary rate from RUM ([[OBS-frontend-real-user-monitoring]]) and failed sign-ins. If green is worse than the thresholds below, traffic returns to blue automatically.

| Signal | Rollback if green exceeds |
|---|---|
| 5xx rate | max(0.5%, 2 × blue) over 5 minutes |
| p95 latency (any route group) | 1.5 × blue over 10 minutes |
| Client error-boundary rate | 2 × blue over 10 minutes |
| Health check failures | any task failing 3 consecutive checks |

- **REL-3** Blue stays running, scaled to at least 50% of normal capacity, for 2 hours after 100% (proposed), and the previous task definition or revision is kept for 7 days so rollback is one command.
- **REL-4** Sessions are sticky to one version during a canary (cookie-based target group stickiness or revision affinity). Each build sets the Next.js `deploymentId`; a client that detects a version change reloads on its next navigation. Static assets from the last two releases stay on the CDN for at least 24 hours ([[APP-rendering-and-caching-strategy]]).

**Temporal workers**
- **REL-5** Workflow code changes that alter the command sequence of running workflows use Temporal worker versioning or `patched()` markers. Workers for the previous build keep running until no open workflow is pinned to it, or until the pinned workflows are migrated with Continue-As-New ([[WF-separation-of-concerns-temporal]]).
- **REL-6** Every workflow change runs a replay test in CI against recorded histories of each workflow type before it can merge.
- **REL-7** Activity input and output types are backwards-compatible for at least one release: new fields optional, no field removed while an older worker may still send or receive it.

**BullMQ workers**
- **REL-8** Job payloads carry a `v` field. New workers accept the previous version; producers emit the new version only after all workers in the region run the new code. Workers drain gracefully on SIGTERM (finish the current job up to 60 seconds, then return it to the queue).

**Rollback**
- **REL-9** Application rollback is a traffic switch back to blue or a redeploy of the previous digest; it never includes a database rollback (MIG-15). Target: traffic back on the previous version within 10 minutes of the decision.
- **REL-10** Any engineer on the release rota can trigger rollback without further approval; the change record is updated afterwards.

**Dark launches and tenant cohorts**
- **REL-11** Changes to legally significant behaviour (deadline computation, service of notices, award issue, payments) ship behind a feature flag and are enabled per tenant cohort: internal tenant, then one consenting tenant, then all tenants in the region ([[PKG-feature-flags]]).
- **REL-12** No production deploy starts in a region while any tenant there is in a protected window (live hearing scheduled, regulatory or aggregator submission due) unless it is an emergency change.

<!-- section:rationale -->
## Rationale

- **REL-1, REL-2** Percentage canaries catch platform-wide regressions (crashes, slow routes) cheaply. They do not catch problems that only one tenant's configuration triggers, which is why REL-11 adds tenant cohorts for risky behaviour.
- **REL-4** Self-hosted Next.js has no managed skew protection; without stickiness a user could load HTML from green and JavaScript chunks from blue mid-filing.
- **REL-5, REL-6** A case workflow can run for months. Deploying new workflow code that replays history differently causes non-determinism errors on every open case of that type.
- **REL-12** A failed deploy during a live hearing or on a SEBI reporting deadline harms parties directly; waiting a few hours costs nothing.

<!-- section:tooling -->
## Tooling and configuration

- ECS: built-in blue/green deployments with ALB weighted target groups, or CodeDeploy (to be settled by ADR); deployment circuit breaker on.
- Azure Container Apps: multiple revision mode with traffic weights, driven by the same pipeline step interface.
- Canary analysis: a pipeline step querying CloudWatch / Azure Monitor and the OpenTelemetry backend ([[OBS-foundations]]).
- Temporal: worker deployment versioning per task queue (`cases`, `hearings`, `documents`, `ai-pipelines`, `billing`), replay tests with `@temporalio/testing` `Worker.runReplayHistories`.
- `release` CLI in `tooling/release`: `release status`, `release rollback --region in`.

<!-- section:enforcement -->
## Enforcement

| Rule | Enforcement |
|---|---|
| REL-1 to REL-3 | Pipeline step definitions; ECS / Container Apps configuration in Terraform |
| REL-4 | `deploymentId` set from `RELEASE_ID` in `next.config`; CDN retention rule |
| REL-6 | `workflow-replay` CI job, required when `packages/workflows/**` changes |
| REL-7, REL-8 | Type-level compatibility test comparing payload schemas with the previous release tag |
| REL-11 | PR checklist plus CODEOWNERS on domain packages flagged as legally significant |
| REL-12 | Pipeline calls a protected-window check against tenant schedule data before starting a region |

<!-- section:examples -->
## Examples

Good: release 2026.11.04 reaches 25% in prod-in; p95 latency for the `(secretariat)` route group rises to 1.8 × blue; traffic returns to blue automatically, the pipeline stops later waves, and the change record shows "auto-rollback, latency".

Bad: changing the order of activities in the `case-lifecycle` workflow without a `patched()` marker; replay test fails in CI and the PR cannot merge.

<!-- section:exceptions -->
## Exceptions

Emergency changes may shorten canary steps (minimum 5 minutes at 5%) but may not skip health checks. Skipping REL-12 needs an emergency change approved under [[DEP-release-notes-and-change]].

<!-- section:questions -->
## Open questions

- [ ] ECS built-in blue/green or CodeDeploy? Settle by ADR before Phase 3.
- [ ] Retirement policy for old Temporal worker versions when cases stay open for years: force Continue-As-New onto the new version after N releases?
- [ ] Source of protected-window data: hearings schedule plus a tenant-maintained calendar in [[PKG-settings]]?
- [ ] Canary thresholds to be tuned after the first months of real traffic.

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Traffic shifting, analysis and rollback are pipeline-enforced; replay tests and payload-compatibility tests are required CI checks; protected-window checks are a pipeline step. Tenant-cohort rollout for legally significant changes relies on review plus CODEOWNERS.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

Backwards-compatible schemas (MIG-1) are the precondition for rollback. Canary analysis signals use route templates and counts only, no personal data. Tenant cohort rollout limits the blast radius of rule or deadline changes to consenting tenants first.

<!-- check:compliance -->
### Compliance evidence

Each deploy, canary result and rollback is written to the change record, which supports ISO/IEC 27001:2022 change management evidence and shows controlled release for client audits.

<!-- check:measurement -->
### Adoption measurement

Tracked: auto-rollback count and causes, time to rollback, deploys blocked by protected windows, Temporal non-determinism errors in production (target 0).

<!-- check:ownership -->
### Ownership and change

Owner: DevOps lead; workflow rules (REL-5 to REL-7) co-owned by the workflow platform owner.

<!-- end -->
