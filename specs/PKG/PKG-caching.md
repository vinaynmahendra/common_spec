---
id: "PKG-caching"
title: "Caching"
parent: "PKG"
order: 5
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "Redis, request-level cache, tenant-scoped cache keys, invalidation strategy"
links: []
rev: 3
syncHash: "6558226c94336f07"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.5 Caching

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Redis, request-level cache, tenant-scoped cache keys, invalidation strategy

<!-- section:purpose -->
## Purpose and scope

`@nomology/cache` gives every server-side consumer one safe way to cache: a request-scoped memo, a bounded in-process LRU, and a regional Redis cache, all behind a key builder that always includes environment, region and tenant. It also provides the Next.js cache handler that stores rendered data on regional Redis ([[APP-rendering-and-caching-strategy]]) and tag-based invalidation.

**Does not:**
- Hold BullMQ queues — queues run on a separate Redis with `maxmemory-policy noeviction`, which BullMQ requires [R1]; the cache Redis uses `allkeys-lru` (or `volatile-lru`) and may lose any key at any time ([[INF-redis]]).
- Act as a source of truth or a session store — sessions belong to [[PKG-mfa-session-management-device]] and are persisted in Postgres.
- Cache authorisation decisions across requests for longer than the bounds stated in [[PKG-policy-engine-permission-matrix]].
- Cache document content, signed URLs or decrypted field values.

<!-- section:consumers -->
## Consumers and use cases

| Consumer | What it caches | Layer | TTL (proposed) |
|---|---|---|---|
| Settings ([[PKG-settings]]) | Effective settings per tenant and user | Redis + in-process | 5 min, versioned key |
| Feature flags ([[PKG-feature-flags]]) | Flag definitions per region | In-process, refreshed by pub/sub | 30 s |
| Authorisation ([[PKG-authorization]]) | Role grants and case-participant sets per user | Request memo + Redis | 60 s, invalidated on change |
| Secretariat console | Queue counts per tenant (dashboard tiles) | Redis | 30 s |
| Next.js data cache (`'use cache'`, `unstable_cache`) | Tenant-scoped reads in Server Components | Redis via cache handler | Per route, tag-invalidated |
| Reference data ([[PKG-reference-and-seed-data]]) | Countries, currencies, calendars | In-process | 10 min |

<!-- section:api -->
## Public API

```ts
// packages/cache/src/index.ts  (server-only)
export type Scope = 'tenant' | 'user' | 'platform';

export interface CacheKeySpec {
  namespace: string;          // registered namespace, e.g. 'settings', 'authz.grants', 'queue-counts'
  scope: Scope;               // 'tenant' and 'user' read tenantId/userId from context
  parts: readonly (string | number)[];
}

/** Builds `{env}:{region}:{scope-prefix}:{namespace}:v{nsVersion}:{parts...}`; the only way to make a key. */
export function cacheKey(spec: CacheKeySpec): CacheKey;          // branded string type

export interface GetOrSetOptions<T> {
  ttlSeconds: number;          // required; max 3600
  staleWhileRevalidateSeconds?: number;
  tags?: string[];             // e.g. ['case:123'] — tenant prefix added automatically
  schema: import('zod').ZodType<T>;   // values are validated on read; invalid = miss
  layer?: 'memo' | 'local' | 'redis' | 'local+redis'; // default 'redis'
  classification: 'public' | 'internal' | 'personal'; // 'personal' forces ttl <= 300 and no 'local'
}
export function getOrSet<T>(spec: CacheKeySpec, load: () => Promise<T>, opts: GetOrSetOptions<T>): Promise<T>;
export function get<T>(spec: CacheKeySpec, schema: import('zod').ZodType<T>): Promise<T | undefined>;
export function invalidate(spec: CacheKeySpec): Promise<void>;
export function invalidateTags(tags: string[]): Promise<void>;        // tenant-prefixed
export function bumpNamespace(namespace: string, scope: Scope): Promise<number>; // O(1) invalidation of a whole namespace for a tenant

/** Request-scoped memo (AsyncLocalStorage), cleared at the end of the request / activity. */
export function memo<T>(spec: CacheKeySpec, load: () => Promise<T>): Promise<T>;

/** Next.js incremental cache handler (cacheHandler / cacheHandlers in next.config). */
export { default as RedisCacheHandler } from './next-handler';

/** Namespace registry: every namespace is declared once with owner and max TTL. */
export function defineNamespace(def: { name: string; owner: string; maxTtlSeconds: number; scope: Scope; classification: 'public'|'internal'|'personal' }): void;

export class CacheUnavailableError extends Error {}   // never thrown from getOrSet; only from get() with { strict: true }
```

<!-- section:usage -->
## Usage examples

```ts
import { getOrSet, invalidateTags } from '@nomology/cache';
import { z } from 'zod';

const QueueCounts = z.object({ awaitingReview: z.number(), overdue: z.number() });

export function secretariatCounts(queueId: string) {
  return getOrSet(
    { namespace: 'queue-counts', scope: 'tenant', parts: [queueId] },
    () => withTenant((tx) => countQueue(tx, queueId)),
    { ttlSeconds: 30, schema: QueueCounts, tags: [`queue:${queueId}`], classification: 'internal' },
  );
}

// After a filing changes state, inside the same request (after commit):
await invalidateTags([`queue:${queueId}`, `case:${caseId}`]);
```

```ts
// next.config.ts
export default {
  cacheHandler: require.resolve('@nomology/cache/next-handler'),
  cacheMaxMemorySize: 0, // keep rendered data out of per-container memory; Redis is shared across containers
};
```

<!-- section:tenant -->
## Tenant context

- `cacheKey` reads `tenantId` (and `userId` for `scope: 'user'`) from `@nomology/tenant-context`; callers never put tenant IDs into `parts` themselves. Missing context for `tenant`/`user` scopes throws `TenantContextMissingError`.
- `platform` scope is allowed only for namespaces registered as `scope: 'platform'` with `classification: 'public' | 'internal'` (reference data, flag definitions). A lint rule rejects `scope: 'platform'` in route-group code.
- Tags are stored as `{env}:{region}:t:{tenantId}:tag:{tag}`; `invalidateTags` can only touch the current tenant's tags.
- The Next.js cache handler derives the tenant from the request context and prefixes every key; a cached entry produced without a tenant context is refused (`set` becomes a no-op and logs `cache.next.untagged_set`), which prevents a shared static render from leaking tenant data ([[APP-rendering-and-caching-strategy]]).
- Values are validated with the namespace schema on read, so a value written by another version or corrupted entry becomes a miss, not a wrong answer.
- The region is part of every key and the cache Redis is regional, so a tenant's cached data never leaves its region ([[MT-data-residency-2]]).

<!-- section:config -->
## Configuration

| Setting | Default (proposed) | Where |
|---|---|---|
| `CACHE_REDIS_URL` | Regional cache Redis (separate from queue Redis) | Secrets manager |
| Max TTL per namespace | declared in `defineNamespace`, hard cap 3600 s | Code |
| In-process LRU size | 5,000 entries / 50 MB per container | Env |
| Redis op timeout | 50 ms (reads), 100 ms (writes) | Env |
| Circuit breaker | open after 20 failures in 10 s; half-open after 30 s | Env |
| Redis eviction | `allkeys-lru`; TLS and AUTH required | Infrastructure ([[INF-redis]]) |

<!-- section:adapters -->
## Providers and extension points

`CacheStore` interface (`get`, `set`, `del`, `sadd`/`smembers` for tags, `incr` for namespace versions, `publish` for local-cache invalidation) with two implementations: `RedisStore` (ioredis, AWS ElastiCache or Azure Cache for Redis) and `MemoryStore` (tests and local dev). In-process caches subscribe to `{env}:{region}:cache:invalidate` so `bumpNamespace` reaches every container within about 1 s.

<!-- section:errors -->
## Error model

| Situation | Behaviour | Caller action |
|---|---|---|
| Redis timeout or down | `getOrSet` calls `load()` directly, records `cache.fallback` metric; breaker opens on repeated failures | None — degraded, not failed |
| Value fails schema | Treated as miss; entry deleted | None |
| Missing tenant context | `TenantContextMissingError` | Fix entry point |
| Unregistered namespace | `UnknownNamespaceError` at first use (and in tests) | Register namespace |
| Value too large (> 512 KB serialised) | Not cached; warning logged | Cache smaller projections |

<!-- section:nfr -->
## Performance and limits

- Redis read p95 ≤ 3 ms in-region; `getOrSet` hit overhead p95 ≤ 5 ms including schema validation.
- Max value 512 KB; keys ≤ 256 bytes.
- Stampede protection: single-flight per key per container plus optional `staleWhileRevalidateSeconds`.
- Invalidation reaches all containers in a region within 2 s (pub/sub); tag invalidation is best-effort, so TTLs remain the upper bound on staleness.

<!-- section:versioning -->
## Versioning and compatibility

Semver. Key format is part of the contract: changing it is a major version and is done by bumping every namespace version (old keys age out by TTL). Namespace schemas are versioned with the namespace (`v{n}` in the key), so deploying a new value shape never reads old shapes.

<!-- section:testing -->
## Test contract

- Key builder property test: no two contexts with different tenant, region or env ever produce the same key.
- Isolation test: tenant A `invalidateTags(['case:1'])` does not affect tenant B's `case:1`.
- Next.js handler: a render without tenant context is never stored; two tenants requesting the same route get different entries.
- Failure: Redis killed mid-test, `getOrSet` still returns loaded values; breaker opens and closes.
- `MemoryStore` passes the same contract suite as `RedisStore`.

<!-- section:questions -->
## Open questions

- [ ] Confirm two Redis deployments per region (queues with `noeviction`, cache with LRU) with DevOps — cost impact in [[INF-redis]].
- [ ] Which Next.js cache handler API (legacy `cacheHandler` vs `cacheHandlers` for `'use cache'`) do we target for the Next.js version pinned in [[APP-framework-dependencies]]?
- [ ] Should `personal` classification be allowed in Redis at all, or only in request memo? Proposed: allowed with TTL ≤ 300 s; DPO to confirm.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Keys are built only by `cacheKey`, which reads tenant and user from context and adds env and region; callers cannot supply the tenant. Tags are tenant-prefixed, so invalidation is tenant-local. Platform scope is limited to registered non-personal namespaces. The Next.js handler refuses to store entries without a tenant context. A property test proves key uniqueness across tenants, regions and environments.

<!-- check:data-protection -->
### Personal data handling

Namespaces declare a classification; `personal` forces TTL ≤ 300 s and disables the in-process layer. Document content, signed URLs and decrypted fields are never cacheable (lint rule on known types). Cached values carry no data that is not already readable by the same tenant; erasure is satisfied by TTL expiry plus `bumpNamespace` for user-scoped namespaces when a deletion run touches that user.

<!-- check:residency -->
### Region awareness

The cache Redis is per region and every key carries the region. There is no cross-region replication or global cache. If the regional cache is down, the package falls back to the regional database, never to another region.

<!-- check:observability -->
### Observability

Metrics: `cache.requests` (namespace, layer, result=hit|miss|fallback|invalid), `cache.latency` histogram, `cache.invalidations`, breaker state gauge. Tenant ID is a span attribute, not a metric label, to bound cardinality. Keys are logged as namespace plus hashed parts only.

<!-- check:resilience -->
### Failure behaviour

Cache failure never fails a request: `getOrSet` falls back to `load()` with 50 ms read timeouts and a circuit breaker. Single-flight prevents stampedes. Values are schema-validated so stale shapes become misses. The package never retries Redis calls itself beyond one immediate retry on connection reset.

<!-- check:change-safety -->
### Change and release safety

Namespace versions in keys mean a schema change never reads old values; key-format changes are major versions. CODEOWNERS: platform engineering; changes to the Next.js handler also need the frontend lead.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "It is very important to configure the maxmemory-policy setting to noeviction; this is the only setting that guarantees the correct behaviour of the queues.",
    "id": "R1",
    "kind": "vendor",
    "title": "BullMQ guide: Going to production",
    "url": "https://docs.bullmq.io/guide/going-to-production",
    "vendor": "Taskforce.sh (BullMQ)"
  }
]
```

<!-- end -->
