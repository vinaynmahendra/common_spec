---
id: "INF-redis"
title: "Redis"
parent: "INF"
order: 5
type: "capability"
template: "infra"
status: "draft"
owner: null
indicative: false
summary: "Two Redis deployments per region: a queue Redis for BullMQ (noeviction, Multi-AZ) and a cache Redis for Next.js and package caches (LRU), with ACL users per service"
links: [{"rel": "decided-by", "to": "ADR-queue-technology"}]
rev: 2
syncHash: "457451bdb178b087"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 14.5 Redis

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Two Redis deployments per region: a queue Redis for BullMQ (noeviction, Multi-AZ) and a cache Redis for Next.js and package caches (LRU), with ACL users per service

<!-- section:purpose -->
## Purpose and responsibilities

Provides Redis per region for two different jobs that need opposite settings:

| Instance | Used by | Must |
|---|---|---|
| `redis-queue-<region>` | BullMQ queues ([[WF-background-jobs-and-queues]], decided by [[ADR-queue-technology]]), rate limiting counters ([[PKG-input-sanitisation-csrf-rate]]) | Never evict keys: `maxmemory-policy noeviction` is the only setting that guarantees correct queue behaviour [R1] |
| `redis-cache-<region>` | Next.js shared cache handler and tag invalidation ([[APP-rendering-and-caching-strategy]]), [[PKG-caching]], session-adjacent short-lived data | Evict least-recently-used keys when full (`allkeys-lru`) |

Mixing both in one instance would either lose jobs (eviction) or make the cache fail writes when full (noeviction). Hence two instances.

<!-- section:topology -->
## Topology per region

| Region | Environment | Queue Redis | Cache Redis |
|---|---|---|---|
| India | prod | ElastiCache (Valkey or Redis OSS engine), cluster mode **disabled**, 1 primary + 2 replicas over 3 AZs, Multi-AZ automatic failover | Cluster mode disabled, 1 primary + 1 replica |
| Singapore | prod | 1 primary + 1 replica, Multi-AZ | 1 primary + 1 replica |
| US | prod | Same as Singapore | Same |
| India | staging / UAT | 1 primary + 1 replica | Single node |
| India | dev | Single node | Single node (may share with queue only in dev) |
| Azure region | prod | Azure Managed Redis with zone redundancy (assumption: Azure Cache for Redis is being retired in favour of Azure Managed Redis — to be confirmed) | Same, separate instance |

Cluster mode is disabled for the queue so BullMQ's multi-key Lua scripts work without hash-tag prefixes; one shard is expected to be enough (see sizing).

<!-- section:sizing -->
## Sizing and scaling

- Queue Redis: payloads hold **IDs only** (tenant ID, entity ID, job type), typically under 1 KB; completed jobs removed after 1 hour or 1,000 per queue (`removeOnComplete`), failed jobs kept 7 days. Estimated working set under 2 GB in India; start with `cache.r7g.large` (13 GB) for headroom.
- Cache Redis: start with `cache.r7g.large`; size by hit ratio, not by fitting everything.
- Scaling triggers: queue memory > 60% of `maxmemory` (ticket), > 75% (page — noeviction means writes fail when full); CPU of the main thread > 70%; cache hit ratio < 80% with evictions climbing.
- If a single queue shard ever becomes the bottleneck, split by workload into separate queue instances (for example `redis-queue-notify`) before moving to cluster mode.

<!-- section:config -->
## Configuration baseline

| Setting | Queue | Cache |
|---|---|---|
| `maxmemory-policy` | `noeviction` [R1] | `allkeys-lru` |
| Persistence | Engine persistence where offered; ElastiCache replication and daily snapshots (AOF is recommended by BullMQ but limited on ElastiCache [R1]; recovery relies on the outbox, below) | None (cache is disposable) |
| TLS (in transit) | Required | Required |
| Encryption at rest | Regional KMS key | Regional KMS key |
| Auth | Redis ACL users (RBAC user groups on ElastiCache), default user disabled | Same |
| Client settings | ioredis `maxRetriesPerRequest: null` for workers [R1], `enableReadyCheck: true`, reconnect with backoff | Short command timeout (200 ms); cache miss on timeout, never fail the request |
| Key namespaces | `bull:<queue>:*` | `t:<tenantId>:...` for tenant data, `p:...` for platform data, `next:<buildId>:...` for Next.js |

**ACL users (example)**

```
user web        on >*** ~bull:* ~rl:* &bull:* +@all -@dangerous     # enqueue + rate limits
user worker     on >*** ~bull:* &bull:* +@all -@dangerous
user cache-web  on >*** ~t:* ~p:* ~next:* +@read +@write +@keyspace -@dangerous
user default    off
```

Key and command restrictions per user follow Redis ACL rules [R2].

<!-- section:resilience -->
## High availability and DR

| Failure | Queue Redis | Cache Redis |
|---|---|---|
| Primary node failure | Automatic failover to replica (typically under a minute). Jobs written in the last moments before failover may be lost (asynchronous replication) | Failover; cold entries rebuilt |
| AZ loss | Failover to replica in another AZ | Same |
| Full data loss | Re-enqueue from the source of truth (below) | Rebuild on demand; no restore |

**Recovering lost jobs**: jobs with business effect (notifications of legal service, webhooks, search indexing) are enqueued from a **transactional outbox** table in Postgres ([[INT-api-platform-tables]]) and marked done only when the job completes. After a Redis loss, a sweep re-enqueues outbox rows not marked done; job handlers are idempotent (job ID = outbox row ID). Anything that cannot be lost and must wait more than minutes belongs in Temporal, not BullMQ ([[WF-workflow-engine]]).

Proposed targets: queue RPO "no lost business jobs" (via outbox), RTO 15 minutes; cache RPO not applicable, RTO 15 minutes. Failover drill quarterly (ElastiCache "test failover" API).

<!-- section:security -->
## Security

- Private subnets; security groups allow 6379 only from `web`, worker and `migrate` security groups; no public endpoints.
- TLS required; ACL users per workload with key patterns; default user disabled; passwords in Secrets Manager with rotation.
- No personal data in Redis values on the queue: payloads carry IDs only; job handlers load data through Prisma with tenant context. Cache entries may contain tenant data (rendered fragments, query results) and are therefore always under a `t:<tenantId>:` key and expire (TTL ≤ 1 hour by default).
- `FLUSHALL`, `CONFIG`, `KEYS`, `DEBUG` blocked for application users (`-@dangerous`).

<!-- section:operations -->
## Runbook

- Inspect queues: Bull Board (or similar) behind SSO in the platform admin console, read-only by default; retry / remove actions require the `queue-operator` role and are audited.
- Pause a queue during an incident: `queue.pause()` from the admin tool; producers continue to enqueue.
- Memory pressure on queue: find the queue growing (`waiting` count), check for stuck workers, scale workers, or pause producers. Never switch the policy to eviction.
- Engine upgrade: minor versions in maintenance windows chosen outside hearing hours in the region's time zone.

<!-- section:observability -->
## Monitoring and alerts

| Signal | Alert (proposed) |
|---|---|
| Queue Redis memory used / maxmemory | > 75% → page |
| Evictions on queue Redis | Any > 0 → page (misconfiguration) |
| BullMQ waiting jobs per queue | Above queue-specific threshold for 10 min → owner |
| BullMQ failed jobs rate | Above baseline → ticket; DLQ size > 0 for legal-notice queues → page |
| Replication lag / failover events | Event → chat |
| Cache hit ratio | < 80% for 1 h → ticket |
| Client connections | > 80% of `maxclients` → ticket |

<!-- section:cost -->
## Cost

Two small-to-medium node groups per production region; Valkey engine on ElastiCache is cheaper than Redis OSS at the same size and is protocol-compatible with BullMQ (to be validated in staging). Reserved nodes after three months of stable size.

<!-- section:readiness -->
## Production readiness

| Item | Status |
|---|---|
| Separate queue and cache instances per region | Not started |
| ACL users and key patterns | Not started |
| Outbox re-enqueue sweep tested after a simulated Redis loss | Not started |
| Failover drill with BullMQ workers reconnecting | Not started |

<!-- section:questions -->
## Open questions

- [ ] ElastiCache engine: Valkey or Redis OSS? Confirm BullMQ compatibility of the chosen engine version in staging.
- [ ] Azure: confirm Azure Managed Redis as the target service and its availability in the Azure regions we need.
- [ ] Which BullMQ queues carry jobs that are not backed by an outbox row, and is that loss acceptable?
- [ ] Should rate-limit counters move to the cache Redis so queue memory is reserved for jobs?

<!-- checks -->
## Template checks

<!-- check:security -->
### Security

Private only, TLS required, at-rest encryption with the regional key, ACL users per workload with the default user disabled, passwords in Secrets Manager. Queue payloads contain IDs only, so Redis holds no personal data on the queue side.

<!-- check:residency -->
### Data residency

One queue and one cache instance per region; no global datastore or cross-region replication. Snapshots stay in the region. Queue payloads carry IDs only; cache entries containing tenant data live only in the tenant's region.

<!-- check:dr -->
### Resilience and recovery

Failover within the region is automatic; jobs that matter are recoverable because they are enqueued from a Postgres outbox and re-enqueued by a sweep after loss, with idempotent handlers keyed on the outbox row ID. Cache is disposable. Failover is drilled quarterly with workers connected, checking that ioredis reconnects and no job runs twice with visible effect.

<!-- check:isolation -->
### Tenant isolation and noisy neighbours

Cache keys always start with `t:<tenantId>:`, built only by the [[PKG-caching]] helper that takes tenant context; a lint rule forbids raw `redis.get` in application code. BullMQ uses per-tenant group rate limits and concurrency so one tenant's bulk job cannot starve others. ACL users stop the web service from reading worker-only keys and stop every application user from running dangerous commands [R2].

<!-- check:observability -->
### Monitoring and alerting

Queue memory against maxmemory and any eviction on the queue instance are paging alerts because `noeviction` turns a full Redis into failed writes. BullMQ waiting and failed counts per queue alert the owning team; dead-letter growth on legal-notice queues pages because it can affect service of notices ([[DOM-service-of-notices-and-proof]]).

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
  },
  {
    "excerpt": "ACLs restrict connections by user to specific commands and key patterns.",
    "id": "R2",
    "kind": "vendor",
    "title": "Redis documentation: ACL",
    "url": "https://redis.io/docs/latest/operate/oss_and_stack/management/security/acl/",
    "vendor": "Redis"
  }
]
```

<!-- end -->
