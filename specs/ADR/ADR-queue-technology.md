---
id: "ADR-queue-technology"
title: "Queue technology"
parent: "ADR"
order: 7
type: "decision"
template: "adr"
status: "approved"
owner: null
indicative: false
summary: "BullMQ on Redis"
links: []
rev: 2
syncHash: "aff4b4b218b3b04f"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 19.7 Queue technology

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> BullMQ on Redis

<!-- section:context -->
## Context and problem

**Question:** what runs short, independent background jobs (notifications, virus scans, thumbnails, search indexing, webhook delivery) that do not need Temporal's durability ([[ADR-workflow-engine]])?

Affected parts: [[WF-background-jobs-and-queues]], [[INF-redis]], [[PKG-notifications]], [[PKG-search]], [[APP-webhooks-outbound]], [[PKG-encryption-at-rest-signed-urls]].

<!-- section:drivers -->
## Decision drivers

- **D1 Same technology on AWS and Azure** in every region.
- **D2 Retries with backoff, delays, rate limiting, dead-letter handling** built in.
- **D3 TypeScript-first** API for a Node.js monorepo.
- **D4 Low operating effort**; reuse infrastructure we already run.
- **D5 Tenant fairness:** one tenant's bulk job (for example 5,000 SEBI ODR notices) must not starve others.
- **D6 Observability:** queue depth, failure counts and traces per job.

<!-- section:decision -->
## Decision

**BullMQ on Redis.**

- One logical set of queues per region on the regional Redis ([[INF-redis]]); no cross-region queues.
- Every job payload carries `tenantId`, `region`, `correlationId` and an idempotency key; payloads hold identifiers, not case content.
- Workers use the same tenant-scoped data access as the app ([[ADR-tenant-isolation]]).
- Per-tenant fairness through BullMQ rate limiting or group keys, with bulk jobs on separate queues.

Chosen because it runs anywhere Redis runs (D1), provides retries, delays and rate limiting (D2), is TypeScript-native (D3) and reuses Redis that we need for caching anyway (D4).

<!-- section:consequences -->
## Consequences

**Easier:** simple API, quick to add a job type, good fit with Node workers.

**Harder:**

- BullMQ requires Redis `maxmemory-policy noeviction` and recommends AOF persistence [R1]. That conflicts with a cache, which wants eviction. Either queues and cache use separate Redis instances, or the cache must never fill memory. This is the main open point for [[INF-redis]].
- Redis becomes a durability dependency: losing it loses queued jobs. Producers that must not lose work use an outbox table in Postgres ([[INT-api-platform-tables]]) and re-enqueue.
- Workers using ioredis must set `maxRetriesPerRequest: null` [R1]; connection settings are standardised in the queue package.
- No built-in cross-region failover; a regional Redis outage pauses jobs in that region.

<!-- section:confirmation -->
## Confirmation

- Start-up check in every worker: reads `CONFIG GET maxmemory-policy` (or the managed-service parameter) and refuses to start if it is not `noeviction` on the queue instance.
- Lint rule: queue producers only through `packages/jobs`, which enforces the payload envelope (tenant, region, correlation, idempotency key) with a Zod schema.
- Dashboard and alerts on queue depth, failed and stalled jobs per queue and region ([[OBS-alerting]]).

<!-- section:options -->
## Options considered

| Option | D1 AWS + Azure | D2 features | Verdict |
|---|---|---|---|
| **BullMQ on Redis** | Yes | Full | **Chosen** |
| AWS SQS / Azure Service Bus | Different service per cloud | Good | Rejected: two code paths |
| RabbitMQ | Yes, but another stateful system to run | Good | Rejected on D4 |
| pg-boss (Postgres-backed) | Yes | Good | Credible; rejected to keep job load off the primary database |
| Temporal for all jobs | Yes | Full | Rejected: cost and overhead for very high volumes of tiny jobs |

<!-- section:revisit -->
## When to revisit

- Redis durability incidents cause job loss despite the outbox.
- Job volume or fairness needs exceed what BullMQ groups and rate limits can handle.
- Licensing or maintenance changes in BullMQ or the Redis distribution we use.

<!-- section:notes -->
## More information

**Open questions**

- [ ] Separate Redis instances for queues (`noeviction`, AOF) and cache (eviction allowed), or one instance with strict memory budgets? Recommendation: separate.
- [ ] Which job types need the Postgres outbox (for example legal service notices) and which can tolerate loss and re-run.
- [ ] Managed Redis choice per cloud (ElastiCache / Azure Cache for Redis or alternatives) and whether it allows `noeviction` and persistence settings we need.

<!-- checks -->
## Template checks

<!-- check:significance -->
### Significance

Significant because many packages depend on it and it fixes a stateful dependency in every region. It covers short jobs only; long processes are Temporal.

<!-- check:compliance -->
### Regulatory, residency and tenancy fit

Residency: queues are regional. Isolation: payloads carry `tenantId` and contain identifiers rather than case content, so Redis holds little personal data. Retention: completed and failed jobs are removed after a set period (proposed 7 days for completed, 30 days for failed) so Redis does not become an unmanaged data store ([[PKG-data-retention-legal-hold-and]]).

<!-- check:consequences -->
### Consequences and costs

Downsides stated: Redis eviction conflict with caching, Redis as a durability dependency, no cross-region failover. Follow-ups: outbox pattern, Redis split decision in [[INF-redis]].

<!-- check:confirmation -->
### Confirmation

Blocking worker start-up check on `noeviction`, producer envelope enforced by the jobs package and lint rule, and alerts on depth, stalled and failed jobs.

<!-- check:linked -->
### Linked and lifecycle

Governs [[WF-background-jobs-and-queues]], [[INF-redis]]. Related: [[ADR-workflow-engine]]. Status: Approved.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "It is very important to configure maxmemory-policy to noeviction, the only setting that guarantees correct queue behaviour; enabling AOF persistence is recommended; workers using ioredis should set maxRetriesPerRequest to null.",
    "id": "R1",
    "kind": "vendor",
    "title": "BullMQ: Going to production",
    "url": "https://docs.bullmq.io/guide/going-to-production",
    "vendor": "Taskforce.sh (BullMQ)"
  }
]
```

<!-- end -->
