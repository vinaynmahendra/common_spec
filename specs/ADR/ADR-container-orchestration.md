---
id: "ADR-container-orchestration"
title: "Container orchestration"
parent: "ADR"
order: 5
type: "decision"
template: "adr"
status: "approved"
owner: null
indicative: false
summary: "AWS ECS, or Azure Container Apps as the Azure equivalent, per region"
links: []
rev: 2
syncHash: "9d4079dda5930338"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 19.5 Container orchestration

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> AWS ECS, or Azure Container Apps as the Azure equivalent, per region

<!-- section:context -->
## Context and problem

**Question:** what runs our containers (the Next.js app, Temporal workers, BullMQ workers, the AI gateway and, per [[ADR-temporal]], the Temporal services themselves) in each region, on AWS by default and on Azure where a client requires it?

Affected parts: [[INF-orchestration]], [[INF-compute]], [[INF-cloud-and-iac]], [[INF-networking]], [[DEP-blue-green-canary-releases]], [[DEP-environment-promotion-and-multi]], [[SEC-business-continuity]].

We run one full stack per region (India, Singapore, US) and expect a small number of additional Azure deployments. The platform team is small, so operating effort per region matters as much as features.

<!-- section:drivers -->
## Decision drivers

- **D1 Low operating effort** per region for a small platform team.
- **D2 Per-region deployment** with no shared control plane holding tenant data outside the region.
- **D3 An Azure equivalent** with the same container images and a similar deployment model.
- **D4 Independent scaling** per service (web, `cases`, `documents`, `ai-pipelines` task queues and BullMQ queues).
- **D5 Security baseline:** private networking, task-level IAM / managed identity, secrets from the regional secrets manager ([[INF-secrets-and-keys]]).
- **D6 Release patterns:** rolling and blue-green / canary with automatic rollback.

<!-- section:decision -->
## Decision

**AWS ECS, or Azure Container Apps as the Azure equivalent, per region.**

- Each region has its own ECS cluster (or Container Apps environment) per environment; there is no cross-region cluster.
- Every deployable (web, each worker pool, AI gateway, Temporal services) is a separate ECS service or Container App with its own scaling rule: CPU / request count for web, queue depth or Temporal task-queue backlog for workers.
- Images are identical across clouds; only infrastructure modules differ, and those differences are contained in [[INF-orchestration]] and [[INF-cloud-and-iac]].
- Launch type (Fargate or EC2 capacity providers) is an implementation choice recorded in [[INF-orchestration]], not part of this decision.

Justification: managed control planes meet D1 and D2; Container Apps gives a comparable service model on Azure (D3); per-service scaling meets D4; both support private networking and workload identity (D5) and revision-based or blue-green deploys (D6).

<!-- section:consequences -->
## Consequences

**Easier:** no Kubernetes control plane to run; per-service IAM roles; simple mental model of one service per deployable.

**Harder:**

- Two infrastructure module sets (ECS and Container Apps) must be kept functionally equivalent; feature drift between them is a risk.
- Fewer ecosystem tools than Kubernetes (no Helm charts for Temporal; we write our own task definitions).
- Autoscaling on Temporal backlog needs custom metrics published to CloudWatch / Azure Monitor.
- Long-lived Temporal services and stateful sidecars fit less naturally on serverless containers; resource limits and graceful shutdown need tuning.
- Portability to Kubernetes later is possible (containers are standard) but deployment definitions would be rewritten.

<!-- section:confirmation -->
## Confirmation

- IaC policy check (for example OPA / Conftest or the cloud's policy engine) in CI: every service runs in private subnets, uses a task role or managed identity, pulls secrets from the regional secrets manager, and has no public IP except load balancers.
- A parity test suite runs the same smoke tests ([[OBS-uptime-synthetic-monitoring]]) against an AWS staging region and an Azure staging environment before each release that touches infrastructure modules.
- Region tag check: every resource carries `region` and `environment` tags; untagged resources fail the pipeline.

<!-- section:options -->
## Options considered

| Option | D1 effort | D3 Azure equivalent | Verdict |
|---|---|---|---|
| **ECS / Azure Container Apps** | Low | Yes | **Chosen** |
| EKS / AKS (Kubernetes) | High: cluster upgrades, add-ons, node security | Yes, same tooling | Rejected for now on D1; revisit if we outgrow it |
| AWS App Runner | Lowest | Partial | Rejected: limited networking and worker support |
| Plain VMs with Docker | High | Yes | Rejected: patching and scaling burden |

<!-- section:revisit -->
## When to revisit

- More than a proposed three Azure deployments, or a client requiring Kubernetes, making a single Kubernetes toolchain cheaper than two module sets.
- Temporal self-hosting proves unreliable on ECS / Container Apps (see [[INF-temporal]]).
- Platform team grows enough to absorb Kubernetes operations, and a concrete need (service mesh, GPU scheduling for in-region models) appears.

<!-- section:notes -->
## More information

**Open questions**

- [ ] Fargate or EC2 capacity providers per region (cost versus control, and GPU needs if we ever host models in-region for [[AI-ai-gateway]]).
- [ ] Which clients currently require Azure, and in which regions, so we size the Azure module effort.
- [ ] Do Temporal server services run on the same cluster as app workloads or a dedicated one per region?

<!-- checks -->
## Template checks

<!-- check:significance -->
### Significance

Significant because it fixes the runtime for every service in every region, the IaC shape, and the release model. It does not decide the database, Redis or Temporal persistence services, which are managed services in [[INF-database]] and [[INF-redis]].

<!-- check:compliance -->
### Regulatory, residency and tenancy fit

Residency: positive, clusters are regional and no control plane holds tenant data outside the region. Isolation: task roles and private subnets per service. Sub-processors: the regional cloud provider only. The Azure variant must meet the same controls; parity tests confirm it. Reviewer and date to be recorded.

<!-- check:consequences -->
### Consequences and costs

Negative consequences are stated: two module sets to keep equivalent, custom autoscaling metrics for Temporal backlog, fewer ecosystem tools, and less natural fit for long-lived stateful services.

<!-- check:reversibility -->
### Reversibility and revisit triggers

Images are standard OCI containers, so a move to Kubernetes rewrites deployment definitions and pipelines, not application code; estimated one to two months per cloud. Keeping service configuration in a cloud-neutral description inside [[INF-cloud-and-iac]] lowers that cost.

<!-- check:linked -->
### Linked and lifecycle

Governs [[INF-orchestration]], [[INF-compute]], [[DEP-blue-green-canary-releases]]. Related: [[ADR-next-js-hosting]], [[ADR-temporal]]. Status: Approved.

<!-- end -->
