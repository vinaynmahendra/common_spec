---
id: "ADR-next-js-hosting"
title: "Next.js hosting"
parent: "ADR"
order: 2
type: "decision"
template: "adr"
status: "approved"
owner: null
indicative: false
summary: "Self-hosted containers, deployed per region for data residency"
links: []
rev: 2
syncHash: "be770da4fa6a0574"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 19.2 Next.js hosting

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Self-hosted containers, deployed per region for data residency

<!-- section:context -->
## Context and problem

**Question:** where and how does the Next.js App Router application run, given that tenant data must stay in the tenant's home region (India, Singapore, US) and some clients require Azure?

Affected parts: [[INF-compute]], [[INF-orchestration]], [[APP-rendering-and-caching-strategy]], [[APP-security-headers-csp-cors]], [[DEP-ci-cd-pipelines-build-test]], [[DEP-environment-promotion-and-multi]].

Server components, route handlers, server actions and the data cache all handle case data, so whatever runs the Next.js server is a data processor for that tenant.

<!-- section:drivers -->
## Decision drivers

- **D1 Residency:** server rendering, caches and logs must run in the tenant's home region; no edge or serverless function may execute in another country with case data.
- **D2 Same artefact on AWS and Azure:** one build must run on AWS ECS and on Azure Container Apps.
- **D3 Control of security headers:** nonce-based CSP per request on authenticated route groups ([[APP-security-headers-csp-cors]]).
- **D4 Shared cache across instances:** tenant-scoped cache keys on regional Redis ([[PKG-caching]]).
- **D5 Operability:** standard container logging, tracing ([[OBS-foundations]]) and blue-green / canary releases ([[DEP-blue-green-canary-releases]]).
- **D6 Cost predictability** at our expected traffic (mostly business-hours use by secretariats, neutrals and parties).

<!-- section:decision -->
## Decision

**Self-hosted containers, deployed per region for data residency.**

The app is built with `output: 'standalone'` into one Docker image per release, promoted unchanged through environments, and run as a service in each regional cluster ([[ADR-container-orchestration]]). Specifically:

- One image, region-specific configuration only through environment variables and the regional secrets manager ([[FND-environment-management]]).
- A custom cache handler stores the Next.js data and ISR cache in the regional Redis with tenant-scoped keys, so all instances in a region share it and nothing is cached across regions.
- Static assets are served from the regional load balancer or a CDN configured to cache only public, non-tenant assets ([[INF-networking]]).
- Middleware resolves the tenant ([[MT-tenant-resolution]]) and rejects requests whose tenant belongs to another region (routing to the home region is done by the global tenant directory, [[MT-data-residency-2]]).

This meets D1 and D2 directly, and D3 to D5 because we own the server process and its headers.

<!-- section:consequences -->
## Consequences

**Easier**

- Residency is simple to explain: case data is processed only by containers in the home region.
- Same image on ECS and Azure Container Apps; no vendor-specific build adapters.
- Full control over headers, nonces and logging.

**Harder**

- We own features a managed host gives for free: image optimisation (`sharp` in the image), ISR revalidation across instances (shared cache handler), and version skew between old and new deployments during rollout ([[APP-rendering-and-caching-strategy]]).
- Cold-start and scaling behaviour is ours to tune (minimum task counts per region).
- No global edge rendering; users far from their tenant's region see higher latency. Accepted, because residency outranks latency.
- Next.js upgrades must be tested against our cache handler and middleware before each upgrade ([[APP-framework-dependencies]]).

<!-- section:confirmation -->
## Confirmation

- CI builds only the `standalone` image; a pipeline check fails if any deployment target other than the regional container services is configured.
- Infrastructure-as-code review ([[INF-cloud-and-iac]]): CDN configuration may cache only paths under the public allow-list; a test fetches an authenticated route through the CDN and expects `Cache-Control: private, no-store`.
- Synthetic checks per region ([[OBS-uptime-synthetic-monitoring]]) confirm responses carry the region header and that a tenant from another region is redirected, not served.

<!-- section:options -->
## Options considered

| Option | D1 residency | D2 AWS + Azure | D3 headers | Verdict |
|---|---|---|---|---|
| **Self-hosted containers per region** | Full control | Yes | Full | **Chosen** |
| Vercel | Functions can be pinned to a region, but edge middleware and build pipeline are global; extra sub-processor | No Azure option | Good | Rejected on D1, D2 and sub-processor count |
| AWS Amplify Hosting | Regional | AWS only | Limited | Rejected on D2 |
| Static export + separate API | Full | Yes | Full | Rejected: loses server components and server actions that the persona apps rely on |

<!-- section:revisit -->
## When to revisit

- A managed Next.js host offers contractual, auditable in-region execution for every component in all three regions and on Azure.
- Operating cost of the self-hosted cache handler and image pipeline exceeds a proposed threshold (for example more than 10 percent of platform engineering time over a quarter).
- A Next.js release makes self-hosting materially harder (for example features that only work on a specific host).

<!-- section:notes -->
## More information

**Open questions**

- [ ] Do we use a CDN in front of the regional load balancers at all, and if so which one per region (and on Azure)? A global CDN is acceptable only for public, non-tenant assets.
- [ ] Skew protection approach during rolling deploys (pin a deployment ID per session or keep the previous build's assets available).
- [ ] Minimum task count per region and per environment, to bound cold-start latency for the first request of the day.

<!-- checks -->
## Template checks

<!-- check:significance -->
### Significance

Significant because it fixes where case data is processed for the web tier, the release pipeline shape, and which sub-processors appear in client contracts. It covers the Next.js server only; workers and Temporal are covered by [[ADR-container-orchestration]] and [[ADR-temporal]].

<!-- check:compliance -->
### Regulatory, residency and tenancy fit

Residency: positive, all server-side processing stays in the home region. Sub-processors: no additional hosting sub-processor beyond the regional cloud provider ([[SEC-vendor-sub-processor-management]]). Isolation: shared cache keys must include `tenant_id` ([[PKG-caching]]). Audit and logs stay in-region ([[OBS-foundations]]). Reviewer and date to be recorded.

<!-- check:consequences -->
### Consequences and costs

Downsides are listed explicitly: we own image optimisation, the shared cache handler, version-skew handling and scaling; users far from their region see higher latency. Follow-ups: cache handler package, skew protection design in [[APP-rendering-and-caching-strategy]], minimum task counts in [[INF-compute]].

<!-- check:reversibility -->
### Reversibility and revisit triggers

Fairly reversible: the app is standard Next.js with no host-specific APIs, so moving to a managed host is mostly a pipeline and configuration change (estimated a few weeks), provided we keep the cache handler behind an interface. The constraint is residency, not code.

<!-- check:linked -->
### Linked and lifecycle

Governs [[INF-compute]], [[APP-rendering-and-caching-strategy]], [[APP-security-headers-csp-cors]], [[DEP-environment-promotion-and-multi]]. Related: [[ADR-container-orchestration]], [[ADR-tenant-isolation]]. Status: Approved.

<!-- end -->
