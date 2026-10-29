---
id: "INF-compute"
title: "Compute"
parent: "INF"
order: 2
type: "capability"
template: "infra"
status: "draft"
owner: null
indicative: false
summary: "Container images and runtime for the Next.js standalone server, BullMQ and Temporal workers, PgBouncer and the OTel collector, deployed per region"
links: [{"rel": "decided-by", "to": "ADR-next-js-hosting"}]
rev: 2
syncHash: "e593abbce3ce3547"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 14.2 Compute

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Container images and runtime for the Next.js standalone server, BullMQ and Temporal workers, PgBouncer and the OTel collector, deployed per region

<!-- section:purpose -->
## Purpose and responsibilities

Defines **what runs**: the container images, their runtime settings and how each workload scales. Orchestration mechanics (clusters, services, deployments) are in [[INF-orchestration]].

Workloads per region:

| Workload | Image | Serves |
|---|---|---|
| `web` | Next.js `output: 'standalone'` server ([[APP-app-router-next-config]]) | All persona route groups, tRPC and REST API, webhooks receive endpoints |
| `worker-jobs` | Node worker running BullMQ processors ([[WF-background-jobs-and-queues]]) | Notifications, virus scans, thumbnails, search indexing, webhook delivery |
| `worker-temporal-<queue>` | Node Temporal worker per task queue: `cases`, `hearings`, `documents`, `ai-pipelines`, `billing` ([[WF-separation-of-concerns-temporal]]) | Activities and workflow tasks |
| `pgbouncer` | Pinned PgBouncer image ([[INF-pgbouncer]]) | Connection pooling for AWS regions |
| `otel-collector` | OpenTelemetry Collector (contrib distribution, pinned) | Regional telemetry gateway ([[OBS-foundations#pipeline]]) |
| `migrate` | Same build as `web`, run as a one-off task | Prisma migrations before rollout ([[DEP-database-migration-strategy-zero]]) |
| Temporal server services | Official Temporal server image | See [[INF-temporal]] |

Decided by [[ADR-next-js-hosting]]: no Vercel or edge runtime holds tenant data; all rendering happens in-region.

<!-- section:topology -->
## Topology per region

| Region | Environment | web | worker-jobs | worker-temporal (per queue) | pgbouncer | otel-collector |
|---|---|---|---|---|---|---|
| India (ap-south-1) | prod | 3–20 tasks over 3 AZs | 2–10 | 2–8 | 2–3 | 2–4 |
| Singapore (ap-southeast-1) | prod | 3–12 | 2–6 | 2–6 | 2 | 2 |
| US (us-east-1) | prod | 3–12 | 2–6 | 2–6 | 2 | 2 |
| India | staging / UAT | 2 | 1 | 1 | 1 | 1 |
| India | dev | 1 | 1 | 1 | 1 | 1 |
| Azure region (when used) | prod | Container App replicas 3–12 | 2–6 | 2–6 | Not used (Flexible Server built-in PgBouncer) | 2 |

Minimum of 3 `web` tasks so that one per availability zone survives a zone loss. Counts are proposed starting points to be replaced by load test results ([[TST-performance-and-load-testing]]).

<!-- section:sizing -->
## Sizing and scaling

| Workload | Task size (proposed) | Scale-out trigger | Scale-in guard |
|---|---|---|---|
| `web` | 1 vCPU / 2 GB, Node heap `--max-old-space-size=1536` | Average CPU > 60% or ALB requests per target > 150/s for 3 minutes | 15-minute cooldown |
| `worker-jobs` | 0.5 vCPU / 1 GB | BullMQ waiting jobs per worker > 50 (custom metric from [[OBS-performance]]) | Never below 2 |
| `worker-temporal-ai-pipelines` | 2 vCPU / 4 GB | Temporal task queue backlog or activity schedule-to-start p95 > 30 s | Scale-in only when backlog = 0 for 10 minutes |
| other Temporal workers | 0.5 vCPU / 1 GB | Schedule-to-start p95 > 5 s | Never below 2 |
| `pgbouncer` | 0.5 vCPU / 1 GB | CPU > 50% (PgBouncer is single-threaded; add tasks, not size) | Fixed minimum 2 |

Growth assumption (to be confirmed by sales forecast): India carries ~60% of load (SEBI ODR volume through MIIs), Singapore ~25% (arbitral institutions), US ~15%. Every scale-out of `web` and workers must respect the database connection budget in [[INF-small-fixed-prisma-pool-per]]; the maximum task counts above are the numbers used in that calculation.

Architecture: ARM64 (Graviton / Ampere) by default for cost; images are built multi-arch so Azure can run amd64 if needed.

<!-- section:config -->
## Configuration baseline

**Image baseline**

- Base: Node.js 24 LTS on a minimal distroless or Alpine-based image, rebuilt weekly; runs as a non-root user (UID 10001), read-only root filesystem with a writable `/tmp` volume only.
- Built once per commit in CI, signed (cosign / Sigstore), SBOM attached, scanned ([[SEC-vulnerability-management]]); the **same digest** is promoted through dev → staging → UAT → prod ([[DEP-environment-promotion-and-multi]]).
- Next.js: `output: 'standalone'`, `NEXT_TELEMETRY_DISABLED=1`, a shared cache handler on regional Redis so all tasks share the data cache and tag invalidation ([[APP-rendering-and-caching-strategy]]), and a fixed `deploymentId` / build ID so version skew between tasks is handled.
- Configuration through environment variables validated by Zod at start-up ([[FND-environment-management]]); secrets injected from Secrets Manager / Key Vault references, never baked into images.
- `instrumentation.ts` initialises OpenTelemetry before the app starts ([[OBS-foundations]]).
- Graceful shutdown: on SIGTERM, `web` stops accepting new connections and drains for up to 30 s; BullMQ workers call `worker.close()` and finish the current job; Temporal workers call `Worker.shutdown()` with a 60 s grace period. ECS `stopTimeout` is set to match.
- Health: `/api/health/live` (process up) and `/api/health/ready` (can reach PgBouncer, Redis queue and Temporal frontend within 1 s). Readiness failures remove the task from the load balancer; liveness failures restart it.

<!-- section:resilience -->
## High availability and DR

- Stateless: any task can be killed at any time. Session state lives in the database / Redis, not memory.
- Spread across 3 AZs with ECS AZ rebalancing; minimum healthy percent 100% during deploys.
- Bad deploy: ECS deployment circuit breaker rolls back automatically; canary process in [[DEP-blue-green-canary-releases]].
- BullMQ jobs interrupted by a task stop are retried by BullMQ (stalled-job detection); handlers must be idempotent.
- Temporal activities interrupted by a task stop are retried by Temporal according to their retry policy; long activities heartbeat.
- RPO / RTO: not applicable (no state). Recovery = redeploy from the registry, under 15 minutes per region.

<!-- section:security -->
## Security

- Tasks run in private subnets with no public IP; inbound only from the load balancer security group (`web`) or from no one (workers).
- Each workload has its own task role with least privilege (for example only `worker-jobs` may call the malware scanning service; only `web` and `worker-temporal-documents` may sign S3 URLs).
- Containers drop all Linux capabilities, no privileged mode, no SSH; ECS Exec is disabled in production except through break-glass.
- Images are pulled only by digest from the regional registry; deploys reject unsigned images.
- No tenant data in images, environment variables or container logs written to disk.

<!-- section:operations -->
## Runbook

- **Scale manually**: change `desired_count` bounds in the `apps` stack; emergency scale through a pre-approved runbook command logged in the change channel.
- **Restart a workload**: force new deployment of the service; never stop all tasks at once.
- **Base image CVE**: rebuild and redeploy within 7 days for critical findings (target set in [[SEC-vulnerability-management]]).
- **Heap issues**: capture heap snapshot only in staging; in production use metrics and traces.
- Runbook location: `docs/runbooks/compute.md` ([[DOC-architecture-docs-adrs-runbooks]]).

<!-- section:observability -->
## Monitoring and alerts

- Per workload: CPU, memory, task count, restarts, OOM kills (ticket at >3 per hour, page if `web` tasks below minimum healthy for 5 minutes).
- Node runtime: event loop delay p99 (`nodejs.eventloop.delay`), heap used, GC pause.
- `web`: request rate, error rate and latency per `http.route` feed the SLOs in [[OBS-performance]].
- Worker backlog metrics (BullMQ waiting / failed, Temporal schedule-to-start) drive both autoscaling and alerts.

<!-- section:cost -->
## Cost

Compute is the largest item after the database. Proposed estimate (to be refined after load tests): India prod about 30–45 vCPU average, Singapore and US about 15–25 each. Levers: ARM64, Compute Savings Plans after three months of stable usage, Fargate Spot for staging and for retry-tolerant `worker-jobs` in non-production only.

<!-- section:readiness -->
## Production readiness

| Item | Status |
|---|---|
| Image hardening baseline and signing | Not started |
| Health endpoints and graceful shutdown in all workloads | Not started |
| Autoscaling on queue backlog metrics | Not started |
| Load test establishing per-task capacity | Not started |
| Connection budget check against max task counts | Not started |

<!-- section:questions -->
## Open questions

- [ ] Node.js 24 LTS for all workloads — any library (Temporal SDK, Prisma engines, sharp) not yet supported on it or on ARM64?
- [ ] Should the `ai-pipelines` worker run GPU or large-memory tasks (local OCR / transcription models), or are all heavy models called through the AI gateway?
- [ ] Do we need a separate `web-public` service for public filing and status pages so a spike there cannot starve signed-in users?
- [ ] Final task-size numbers after the first load test.

<!-- checks -->
## Template checks

<!-- check:security -->
### Security

Tasks are private, have no public IP, run as non-root with a read-only filesystem and no capabilities, and each workload has its own least-privilege task role. Images are signed and deployed by digest; unsigned images are rejected. Secrets come from Secrets Manager / Key Vault references at start-up. Critical base-image CVEs are fixed within 7 days by a rebuild.

<!-- check:isolation -->
### Tenant isolation and noisy neighbours

Compute is shared across tenants within a region; isolation is enforced in the data layer (forced RLS, [[MT-isolation-strategy]]). Starvation is prevented at the queue level: BullMQ per-tenant rate limits and group concurrency, and separate Temporal task queues for heavy work (`ai-pipelines`, `documents`) so a tenant's bulk eBundle or transcription run cannot consume `web` capacity. A tenant needing dedicated compute is handled by deploying an extra service from the same module with a tenant-pinned task queue, not a code fork.

<!-- check:observability -->
### Monitoring and alerting

Paging alerts are symptom-based (SLO burn rate on `web`, healthy task count below minimum); resource alerts (CPU, memory, OOM) create tickets. Worker backlogs alert when schedule-to-start exceeds its target for 10 minutes. Readiness probes exercise PgBouncer, Redis and Temporal, so a dependency failure shows up as an unhealthy target before users report it.

<!-- check:cost -->
### Cost

Cost driver is request volume (web) and pipeline minutes (AI and document workers). ARM64, Savings Plans and Spot for non-production are the main levers; Spot is rejected for production workers because long transcription activities would restart. All services are tagged by component and region.

<!-- end -->
