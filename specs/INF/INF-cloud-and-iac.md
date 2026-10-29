---
id: "INF-cloud-and-iac"
title: "Cloud and IaC"
parent: "INF"
order: 1
type: "capability"
template: "infra"
status: "draft"
owner: null
indicative: false
summary: "Terraform modules and per-region stacks, account / subscription layout, landing-zone guardrails, policy-as-code and drift detection"
links: []
rev: 2
syncHash: "245429ca20c581f7"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 14.1 Cloud and IaC

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Terraform modules and per-region stacks, account / subscription layout, landing-zone guardrails, policy-as-code and drift detection

<!-- section:purpose -->
## Purpose and responsibilities

Defines **where** infrastructure lives (cloud accounts and Azure subscriptions) and **how** it is created and changed (Terraform modules, state, pipelines, policy checks). Every other Infrastructure node is a Terraform module that plugs into the layout here.

Depended on by: all [[INF]] children, [[DEP-ci-cd-pipelines-build-test]] (deploy roles), [[DEP-environment-promotion-and-multi]] (region ordering), [[SEC-isms-controls]] (change management and configuration evidence).

Working decision: **Terraform** (HashiCorp provider ecosystem, AWS and `azurerm` providers). Pulumi was listed in the original outline; it is not proposed because the team's existing experience and policy tooling (Checkov, OPA / conftest) are Terraform-based. Licence choice between Terraform and OpenTofu is an open question; modules are written to stay compatible with both.

<!-- section:topology -->
## Topology per region

**Account / subscription layout (AWS Organizations; Azure management groups mirror it)**

| Account | Purpose | Regions allowed |
|---|---|---|
| `nomo-management` | Organizations, SSO (IAM Identity Center), billing | Home region only |
| `nomo-security` | GuardDuty / Security Hub delegated admin, security tooling | All three |
| `nomo-log-archive` | CloudTrail, Config and VPC flow logs, one bucket **per region** | ap-south-1, ap-southeast-1, us-east-1 |
| `nomo-shared-services` | Image registry (ECR), CI OIDC roles, Terraform state buckets | All three |
| `nomo-nonprod` | dev, staging, UAT (separate VPCs) | ap-south-1 (assumption: non-production in India only, synthetic data) |
| `nomo-prod-in` | Production, India | ap-south-1 (+ ap-south-2 if in-country DR approved) |
| `nomo-prod-sg` | Production, Singapore | ap-southeast-1 |
| `nomo-prod-us` | Production, US | us-east-1 (+ us-west-2 for DR) |
| `nomo-backup-in` / `-sg` / `-us` | Immutable backup vaults (see [[INF-backup-and-disaster-recovery]]) | Same as matching prod account |

Azure variant: a subscription per environment and region under a `nomo-azure` management group, for example `nomo-az-prod-in` (Central India) and `nomo-az-prod-sg` (Southeast Asia), created only when a client contract requires Azure.

**Repository layout (in the Turborepo, folder `infra/`)**

```
infra/
  modules/
    aws/{network,ecs-service,ecs-cluster,rds-postgres,pgbouncer,elasticache,temporal,kms,secrets,backup,waf-cdn,otel-collector}
    azure/{network,container-app,aca-env,pg-flexible,redis,temporal,keyvault,backup,frontdoor}
  live/
    aws/<env>/<region>/<stack>/   # e.g. aws/prod/ap-south-1/database/
    azure/<env>/<region>/<stack>/
  policies/                       # OPA / Checkov custom rules
```

Stacks are split by blast radius: `network`, `security` (KMS, secrets), `data` (Postgres, Redis), `temporal`, `apps`, `edge` (CDN, WAF, DNS). A plan in `apps` can never destroy a database.

<!-- section:sizing -->
## Sizing and scaling

Not a runtime component; sizing here means scale of the code base and pipelines.

- Starting point: about 3 clouds-regions × 4 environments × 6 stacks ≈ 50–70 state files (AWS); Azure adds about 12 per Azure region when used.
- Plans run in parallel per stack in CI; target under 5 minutes for a full production plan across three regions.
- Scaling trigger: if any stack's plan exceeds 3 minutes or touches more than ~300 resources, split it.

<!-- section:config -->
## Configuration baseline

| Setting | Value | Why |
|---|---|---|
| State backend (AWS) | S3 bucket per region in `nomo-shared-services`, SSE-KMS with a dedicated key, versioning on, `use_lockfile = true` | State for a region stays in that region; native S3 locking avoids a separate lock table |
| State backend (Azure) | Storage account per region, blob lease locking, customer-managed key | Same rule as AWS |
| Provider pinning | Exact provider versions in `.terraform.lock.hcl`, Renovate opens upgrade PRs | Reproducible plans |
| Default tags | `nomo:env`, `nomo:region`, `nomo:component`, `nomo:owner`, `nomo:data-class` via provider `default_tags` | Cost allocation and ownership ([[INF]] principle INF-P10) |
| Region guard | Each `live/` folder sets `allowed_regions`; module asserts `var.region` is in it | Fails before reaching the cloud API |
| SCP | Deny all actions outside the account's allowed regions, except global services (IAM, Organizations, Route 53, CloudFront, WAF global scope) | Hard stop on residency errors |
| Azure Policy | `Allowed locations` and `Allowed resource types` assigned per subscription | Same as SCP |
| Policy-as-code | Checkov plus custom OPA rules in `infra/policies/`: no public data stores, encryption with CMK, TLS minimums, tags present, no cross-region replication unless in the exceptions list | Blocks a merge on failure |

<!-- section:resilience -->
## High availability and DR

- **State loss or corruption**: versioned state buckets; restore previous version. State buckets are backed up to the regional backup vault daily.
- **Lost CI system**: break-glass runbook allows a named engineer to run `terraform apply` from a hardened admin workstation using a time-bound role; every use is reviewed.
- **Region rebuild**: the yearly drill rebuilds a full staging region from an empty account using only `infra/live` and backups; target under 8 hours (goal 1 in [[INF#goals]]).
- **Provider outage** (cloud API down): no infrastructure changes; running workloads unaffected.

<!-- section:security -->
## Security

- CI runs `plan` with a read-only role and `apply` with a deploy role per account, both assumed through GitHub OIDC federation scoped to the `main` branch and protected environments (assumption: GitHub Actions is the CI system — see [[DEP-ci-cd-pipelines-build-test]]). No access keys exist.
- Production `apply` requires an approved pull request from a CODEOWNER in `infra/` and a second approval in the protected environment ([[FND-governance]]).
- Humans get read-only console access through SSO; write access is a time-bound elevation (maximum 4 hours) with ticket reference, logged in CloudTrail.
- State files can contain secrets (for example generated passwords). Rule: generate database and Redis passwords inside Secrets Manager (`manage_master_user_password` on RDS, random secrets created by the secret resource) so they never appear in state; state buckets are readable only by CI roles.
- Root user of each account has hardware MFA and no access keys; root use alerts the security channel.

<!-- section:operations -->
## Runbook

Routine:

1. **Change**: open PR → CI runs `fmt`, `validate`, Checkov / OPA, and `plan` per affected stack → plan posted as PR comment → approval → merge → apply to non-production → apply to production in region order India, Singapore, US (order set in [[DEP-environment-promotion-and-multi]]).
2. **Drift**: nightly `plan -detailed-exitcode` on every production stack; exit code 2 opens a ticket and posts to the infrastructure channel. AWS Config rules flag manual changes in near real time.
3. **Provider upgrades**: monthly Renovate batch, applied to dev and staging for one week before production.
4. **New region**: copy `live/aws/prod/<region>` parameters, add region to SCP allow-list and the tenant directory, run stacks in order network → security → data → temporal → apps → edge.

Incident: if an apply fails half-way, do not re-run blindly; read the plan, check state lock, and fix forward with a PR. Force-unlock only with a second engineer present.

<!-- section:observability -->
## Monitoring and alerts

- Drift job result per stack (ticket on drift, page never).
- CloudTrail metric filter: console write actions by human roles in production accounts → security alert ([[OBS-security-events]]).
- SCP denials logged and alerted (signals someone tried to create a resource in the wrong region).
- Policy-as-code failures counted per month as a process metric.

<!-- section:cost -->
## Cost

Low direct cost: state buckets, CI minutes, AWS Config rules (largest item, roughly proportional to resources recorded). Tag enforcement here enables cost allocation for every other component; budgets per account and region with anomaly alerts are created by this module and routed to the Infrastructure owner.

<!-- section:readiness -->
## Production readiness

| Item | Status |
|---|---|
| Account layout created with SCPs | Not started |
| State backends per region with locking and CMK | Not started |
| CI OIDC roles (plan read-only, apply per account) | Not started |
| Policy-as-code rules in CI | Not started |
| Nightly drift job | Not started |
| Break-glass apply runbook tested | Not started |

<!-- section:questions -->
## Open questions

- [ ] Terraform (BSL licence) or OpenTofu? Do any client contracts or our licence review constrain this?
- [ ] Confirm GitHub Actions as the CI system and GitHub OIDC as the identity for applies.
- [ ] Are non-production environments only in India, or does each region need its own staging for client UAT with regional data?
- [ ] Which IaC tool for Azure: Terraform `azurerm` (proposed, one toolchain) or Bicep if a client's team must maintain it?
- [ ] Who are the CODEOWNERS for `infra/` and who may approve production applies?

<!-- checks -->
## Template checks

<!-- check:security -->
### Security

No long-lived credentials: CI uses OIDC, services use task roles, humans use SSO with MFA and time-bound elevation. Production applies need two approvals. Secrets are generated inside Secrets Manager so they never enter Terraform state. Root accounts have hardware MFA and alerting on use.

<!-- check:residency -->
### Data residency

Residency is enforced in three layers: a module-level region assertion, SCPs / Azure Policy region allow-lists per account, and a policy-as-code rule rejecting cross-region replication or backup copy unless listed in the exceptions register. Terraform state itself is kept per region because state can contain resource attributes. The log archive account keeps one bucket per region so CloudTrail and VPC flow logs for India stay in India (supports the CERT-In 180-day in-India log retention in [[INF-backup-and-disaster-recovery]]).

<!-- check:iac -->
### Infrastructure as code and change control

All infrastructure is defined in `infra/modules` and instantiated from `infra/live/<cloud>/<env>/<region>/<stack>` with one parameter file each; allowed differences are size, counts, region and feature toggles (for example `enable_dr_region`). State is per region in S3 / Azure Storage with CMK encryption, versioning and native locking. Plans run in CI with a read-only OIDC role; applies run only from the pipeline after CODEOWNER approval. Drift is detected nightly and AWS Config / Azure Policy flag manual changes. Checkov and OPA rules block public data stores, missing encryption, missing tags and disallowed regions. Risky changes (engine upgrades, parameter changes needing reboot) go through [[DEP-release-notes-and-change]] with a maintenance window.

<!-- check:lifecycle -->
### Operations and lifecycle

Provider and module versions are pinned and upgraded monthly through Renovate. The runbook covers change, drift, new region and failed-apply recovery. A new on-call engineer needs only the repository and SSO access; no state lives on laptops.

<!-- check:cost -->
### Cost

Budgets and anomaly alerts per account and region are created by this module and routed to the Infrastructure owner. Tagging is enforced by the provider `default_tags` and an AWS Organizations tag policy, so every other component's cost can be allocated by region, environment and component.

<!-- end -->
