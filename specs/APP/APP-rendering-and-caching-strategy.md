---
id: "APP-rendering-and-caching-strategy"
title: "Rendering and caching strategy"
parent: "APP-app-configuration"
order: 4
type: "feature"
template: "design"
status: "draft"
owner: null
indicative: false
summary: "Design note: Cache Components / Partial Prerendering vs nonce-based CSP per route group, tenant-scoped cache keys, shared cache handler on regional Redis, version skew"
links: []
rev: 2
syncHash: "97318be378dcf867"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.1.4 Rendering and caching strategy

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Design note: Cache Components / Partial Prerendering vs nonce-based CSP per route group, tenant-scoped cache keys, shared cache handler on regional Redis, version skew

<!-- section:context -->
## Context and scope

`apps/web` is a Next.js 16 App Router app, self-hosted as `standalone` containers on ECS (or Azure Container Apps) in India, Singapore and US ([[ADR-next-js-hosting]]). Several tasks run per region behind a load balancer and CDN; deploys are rolling, so two versions serve traffic for some minutes.

Next.js now offers Cache Components: a prerendered static shell with dynamic holes streamed at request time (Partial Prerendering), plus `'use cache'` directives that cache function results [R1]. A strict Content Security Policy with nonces needs a fresh nonce in every HTML response, which means the page must be rendered dynamically; nonce-based CSP and a prerendered static shell do not mix [R2].

Our pages fall into two families:
- **Public, mostly anonymous** pages (sign-in, invitation landing, public filing entry, status, accessibility statement): the same for every visitor of a tenant host, apart from branding.
- **Authenticated persona** pages (portal, tribunal, secretariat, transcription, admin, ops): different per user, per case role and per tenant, full of confidential case data.

Data that is safe to cache and expensive to read: tenant theme and settings, rule-set summaries, reference data ([[PKG-reference-and-seed-data]]), message catalogues, holiday calendars.

<!-- section:goals -->
## Goals and non-goals

**Goals**
1. Strict CSP on every HTML response (no `unsafe-inline` for scripts) without giving up streaming.
2. No cache layer (CDN, Next.js server cache, router cache, TanStack Query, browser HTTP cache) can serve one tenant's or one user's content to another.
3. Cached data is shared across all tasks in a region and invalidated across all of them within 2 seconds.
4. A rolling deploy never breaks a user mid-task (no failed chunk loads, no "Failed to find Server Action").
5. Authenticated pages meet the TTFB budgets in [[APP-route-groups-per-persona]] without a static shell.

**Non-goals**
- Caching authenticated HTML at the CDN or in the Next.js full-route cache.
- Cross-region cache sharing or replication.
- Using ISR for tenant content.

<!-- section:design -->
## Design

#### 1. Rendering mode per route group

| Group | Mode | CSP | Why |
|---|---|---|---|
| `(public)` | Cache Components static shell + dynamic hole for tenant branding and any session-aware bits | **hash-based** (`'sha256-…'` + `'strict-dynamic'`, using build-time integrity hashes) | Same for every visitor; fast first paint on slow mobile networks; no nonce needed |
| `(counsel)`, `(neutral)`, `(secretariat)`, `(transcriber)`, `(tenant-admin)`, `(platform-admin)` | Fully dynamic per request, streamed with `<Suspense>` | **nonce-based** (`'nonce-…'` + `'strict-dynamic'`) | Content is per user anyway; a static shell would give little and would block nonces |

Inside dynamic pages, `'use cache'` is still used **for data**, not for HTML.

#### 2. Cache layers and their keys

| Layer | Used for | Key / scope | Lifetime | Invalidation |
|---|---|---|---|---|
| CDN | `/_next/static/*`, fonts, public shells | path + **host** (public shells only) | static: 1 year immutable; shells: 300 s | deploy (new hashes) |
| Next.js `'use cache: remote'` (Redis handler) | tenant theme, tenant settings, rule-set summaries, reference data, message catalogues | function ID + serialised args; **args must include `tenantId`** (and `locale`, `version` where relevant); prefix `{region}:{deploymentId}:` | `cacheLife('hours')` default; reference data `days` | `revalidateTag` / `updateTag` with tenant-scoped tags |
| Next.js `'use cache'` (in-memory, per task) | tiny, hot, non-tenant data (country list, problem type registry) | args | `minutes` | deploy |
| `React.cache` | per-request memoisation of session, user, case header | request | one request | n/a |
| Client router cache | RSC payloads of visited routes | per tab | Next.js defaults for dynamic routes (not reused across navigations to dynamic pages) | `router.refresh()` after writes |
| TanStack Query | interactive client views | `[tenantId, …]` | `staleTime` per query | `invalidateQueries` after mutation |
| Browser HTTP cache | none for authenticated HTML | `no-store` | — | — |

**Tag convention**: `tenant:{tenantId}:{entity}[:{id}]`, for example `tenant:7f3c…:settings`, `tenant:7f3c…:case:ARB-2026-00123`, `tenant:7f3c…:ruleset:hkiac-2024:v3`. Platform-wide tags (`ref:countries`) carry no tenant data.

#### 3. Shared cache handler on regional Redis

```ts
// apps/web/cache/redis-handler.mjs  (registered under cacheHandlers.remote)
// get(cacheKey, softTags) / set(cacheKey, pendingEntry) / refreshTags() / getExpiration(tags) / updateTags(tags)
// - keys:   `${REGION}:${DEPLOYMENT_ID}:uc:${cacheKey}`
// - tags:   hash `${REGION}:tags` -> tag -> invalidatedAt (ms)
// - entry:  value stored as a stream buffer + { tags, stale, timestamp, expire, revalidate }
// - invalidation: updateTags() writes invalidatedAt and PUBLISHes on `${REGION}:tag-invalidations`;
//   every task SUBSCRIBEs and refreshes its local view of tag timestamps
```
Redis is the regional instance from [[INF-redis]], logical DB separate from BullMQ queues, with `maxmemory-policy allkeys-lru` for the cache DB only. If Redis is unavailable the handler returns a miss and the app reads from Postgres (fail open for the cache, never for authorisation).

#### 4. Version skew during rolling deploys
- `deploymentId = BUILD_SHA`: when a browser holding version N requests from a task on N+1, Next.js forces a hard navigation instead of failing.
- Before the hard navigation, form drafts are already on the server or in IndexedDB ([[APP-client-state-and-data-fetching]]), so nothing typed is lost.
- `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` is identical for N and N+1 within a region.
- Static assets of N stay on the CDN origin bucket for 24 hours after N+1 is live.
- Cache keys include `deploymentId`, so N+1 never reads entries whose shape N wrote.

<!-- section:examples -->
## Worked examples

**Tenant settings read in a secretariat page**

```ts
// packages/data-access/src/settings.ts
import 'server-only';
export async function getTenantSettings(tenantId: string, version: number) {
  'use cache: remote';
  cacheTag(`tenant:${tenantId}:settings`);
  cacheLife('hours');
  return withTenant(tenantId, (tx) => tx.tenantSetting.findMany({ where: { version } }));
}
```
A tenant admin changes the case-number format. The Server Action writes the new settings version and calls `updateTag(\`tenant:${tenantId}:settings\`)`. The handler marks the tag invalidated and publishes it; all tasks in the region see the change on their next read. Other tenants' entries are untouched because their tags differ.

**Wrong pattern (blocked by lint)**

```ts
export async function getSettings() { 'use cache: remote'; const t = headers().get('x-tenant-id'); … }
```
Reading the tenant inside a cached function means the cache key does not contain it; the lint rule `platform/cache-requires-tenant-arg` fails this.

**Rolling deploy**: a counsel user is on step 3 of a Statement of Claim. Tasks move to N+1. On "Save and continue" the action call hits N+1; Next.js sees the deployment mismatch and hard-reloads; the stepper restores step 3 from the server-side draft.

<!-- section:alternatives -->
## Alternatives considered

| Option | Why not chosen |
|---|---|
| Partial Prerendering for authenticated groups with hash-based CSP | Hashes only cover scripts known at build time; inline scripts emitted per request by streaming (RSC payload bootstrapping) cannot be hashed in advance, so we would need `unsafe-inline` or lose streaming. |
| Nonce CSP for public pages too | Makes every public page dynamic; loses the fast static shell for parties on slow mobile networks. Acceptable fallback if SRI hashing proves unreliable. |
| No CSP nonce, rely on `unsafe-inline` with other headers | Fails our strict-CSP goal and typical client security questionnaires. |
| Per-task in-memory cache only | Each task warms separately; invalidation cannot reach other tasks, so a settings change shows inconsistently for minutes. |
| Global cache shared across regions | Breaks data residency ([[MT-data-residency-2]]). |

<!-- section:crosscutting -->
## Cross-cutting concerns

- **Security**: CSP choice per group as above, values in [[APP-security-headers-csp-cors]]. Cached values never include permission decisions; authorisation runs on every request.
- **Privacy**: only tenant configuration and reference data are cached in Redis; no case content, no party personal data. Entries live in the tenant's region only.
- **Tenancy**: tenant ID in every cache key and tag; lint rule; two-tenant diff test.
- **Observability**: handler emits `cache.hit`, `cache.miss`, `cache.error` counters labelled by function name and region (not tenant, to keep cardinality low), plus a per-tenant sample in traces.
- **Cost**: dynamic rendering of all authenticated pages raises CPU per request; sizing in the capacity check.

<!-- section:guardrails -->
## Guardrails

1. Never place `'use cache'` on a page or layout component in an authenticated group; only on data functions in `packages/data-access`.
2. Every `'use cache'`/`'use cache: remote'` function takes `tenantId` as its first argument unless it is in the allow-list of platform reference functions.
3. Never read `headers()`, `cookies()` or the session inside a cached function.
4. Tags must start with `tenant:{tenantId}:` or `ref:`.
5. After any write, call `updateTag` for the tags the write affects, in the same action.
6. Authenticated responses carry `Cache-Control: private, no-store`; a header test fails the build otherwise.

<!-- section:ownership -->
## Ownership

| Part | Owner |
|---|---|
| Rendering mode per group, CSP type | Frontend lead (with security review) |
| Redis cache handler | Platform engineering |
| Tag conventions and lint rule | Frontend lead |
| CDN rules | DevOps ([[INF-networking]]) |

<!-- section:questions -->
## Open questions

- [ ] Is Next.js build-time SRI (`experimental.sri`) available with our bundler for the hash-based CSP on `(public)`? If not, use nonce CSP for public pages too. (owner: frontend lead)
- [ ] Redis: separate logical DB on the shared regional Redis, or a dedicated cache cluster? (owner: platform engineering, [[INF-redis]])
- [ ] Should any authenticated list (for example the secretariat queue counts) use `'use cache: private'` to speed up back navigation? (owner: frontend lead)
- [ ] Record the rendering-mode decision as an ADR under [[ADR]] once reviewed.

<!-- checks -->
## Template checks

<!-- check:security -->
### Security and privacy

Trust boundaries: browser → CDN → Next.js task → Redis / Postgres. New attack surface is the shared Redis cache: a poisoned or mis-keyed entry could leak data across tenants. Mitigations: only configuration and reference data may be cached (guardrail 1), tenant ID in every key (guardrail 2, lint enforced), no request-scoped inputs inside cached functions (guardrail 3), Redis reachable only from app tasks in the region over TLS with AUTH, and the two-tenant diff test.

<!-- check:tenancy -->
### Tenancy

Tenant ID is carried as an explicit argument to every cached function and in every tag; invalidating `tenant:A:*` cannot touch tenant B. Authenticated HTML is never cached outside the browser tab. A missing tenant argument fails lint; a missing tenant at runtime makes `withTenant` throw (fail closed).

<!-- check:residency -->
### Data residency and lifecycle

Cache entries live in the regional Redis only; keys are prefixed with the region; there is no replication between regions. Entries contain no personal data. CDN caches only static assets and public shells, keyed by host.

<!-- check:failure -->
### Failure handling and recovery

Redis down: handler returns a miss and logs `cache.error`; pages fall back to Postgres (higher latency, same correctness). Pub/sub lost: tag timestamps are also read from the Redis hash on each `getExpiration`, so an invalidation is never missed for longer than one read. Deploy mid-task: handled by `deploymentId` and server-side drafts.

<!-- check:scale -->
### Capacity, performance and cost

Proposed basis to be validated by load test: per region at launch up to 200 concurrent authenticated users per task class, p95 server render ≤ 150 ms for list pages, cache hit rate ≥ 90% for settings and theme reads after warm-up. First bottleneck expected: CPU on render for secretariat queues (mitigated by server-side pagination at 50 rows), then Postgres connections behind PgBouncer ([[INF-small-fixed-prisma-pool-per]]).

<!-- check:reversibility -->
### Reversibility

The rendering mode per group can be changed later per route (switching `(public)` to nonce CSP is a config change). Harder to change: the tag naming convention and the rule that cache keys contain `deploymentId`, because the Redis handler and all data functions depend on them; both should be fixed in the ADR.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "kind": "vendor",
    "title": "Next.js: Caching (Cache Components)",
    "url": "https://nextjs.org/docs/app/getting-started/caching",
    "vendor": "Vercel (Next.js)"
  },
  {
    "id": "R2",
    "kind": "vendor",
    "title": "Next.js: How to set a Content Security Policy",
    "url": "https://nextjs.org/docs/app/guides/content-security-policy",
    "vendor": "Vercel (Next.js)"
  }
]
```

<!-- end -->
