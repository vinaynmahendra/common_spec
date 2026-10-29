---
id: "MT-tenant-resolution"
title: "Tenant resolution"
parent: "MT"
order: 2
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "subdomain, custom domain, or header; resolved in middleware"
links: []
rev: 2
syncHash: "472732ff779c1456"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 3.2 Tenant resolution

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> subdomain, custom domain, or header; resolved in middleware

<!-- section:purpose -->
## Purpose and scope

`@nomology/tenancy` (in `packages/tenancy`) turns an incoming request, job or workflow call into a verified `TenantContext` and makes it available to everything downstream. It resolves the tenant from, in order: the custom domain or subdomain of the request, the API credential (public API, aggregator API), or the internal envelope of a job or workflow. It runs in Next.js middleware ([[APP-app-router-next-config]]) and in worker bootstraps.

It deliberately does **not** authorize the user (that is [[PKG-authorization]]: membership and role checks), does not open database transactions (that is [[MT-prisma-implementation]]), and does not decide region placement (that is [[MT-data-residency-2]]); it only detects and handles a request that reached the wrong region.

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Use |
|---|---|
| Next.js middleware (`apps/web/middleware.ts`) | Resolve host to tenant, reject unknown / suspended / wrong-region tenants, place tenant in request headers for server code |
| Server Components, tRPC context, Server Actions | `getTenantContext()` to read the resolved tenant |
| Public API route handlers (`/api/v1/*`) | `resolveFromCredential()` for API keys and OAuth clients ([[INT-public-api-and-webhooks]]) |
| Aggregator intake (`/api/aggregator/v1/*`) | Resolve the target tenant named in the call and check it is in the credential's allowed list ([[INT-aggregator-intake-api]]) |
| BullMQ and Temporal workers | `runWithTenant(envelope, fn)` to restore context from a job envelope or workflow input |
| Sign-in surfaces | Resolve tenant branding and SSO settings before a session exists ([[APP-public-and-sign-in-surfaces]]) |

<!-- section:api -->
## Public API

```ts
export type RegionCode = 'in' | 'sg' | 'us' | (string & {}); // Azure deployments get their own code, e.g. 'in-az'

export interface TenantContext {
  readonly tenantId: string;          // uuid
  readonly slug: string;
  readonly region: RegionCode;        // home region
  readonly status: 'active' | 'suspended' | 'offboarding';
  readonly type: 'arbitral_institution' | 'odr_institution' | 'cord' | 'enterprise' | 'court_programme';
  readonly source: 'host' | 'api_credential' | 'aggregator' | 'job' | 'workflow';
  readonly resolvedAt: number;        // epoch ms, for cache diagnostics
}

/** Middleware entry point. Never throws; returns a decision. */
export function resolveFromRequest(req: NextRequest): Promise<
  | { kind: 'tenant'; ctx: TenantContext }
  | { kind: 'platform' }                                    // platform admin host, e.g. admin.<domain>
  | { kind: 'wrong_region'; redirectTo: URL; region: RegionCode }
  | { kind: 'not_found' }                                   // unknown host, deleted tenant
  | { kind: 'unavailable'; reason: 'suspended' | 'provisioning' | 'directory_down' }
>;

/** Writes the signed internal headers used by server code after middleware. */
export function attachTenantHeaders(res: NextResponse, ctx: TenantContext): void;

/** Server-side accessor (RSC, tRPC, Server Actions, route handlers). Throws if absent. */
export function getTenantContext(): TenantContext;            // throws TenantContextMissingError
export function tryGetTenantContext(): TenantContext | undefined;

/** Public API / aggregator credentials. */
export function resolveFromCredential(cred: { kind: 'api_key' | 'oauth_client' | 'aggregator'; id: string; requestedTenant?: string }): Promise<TenantContext>;

/** Workers: verify the envelope against the directory, then run fn inside AsyncLocalStorage context. */
export interface TenantEnvelope { tenantId: string; region: RegionCode; actor?: { userId?: string; kind: 'user' | 'system' | 'support' } }
export function runWithTenant<T>(env: TenantEnvelope, fn: () => Promise<T>): Promise<T>;
export function toEnvelope(ctx?: TenantContext): TenantEnvelope; // for enqueuing jobs / starting workflows

export class TenantContextMissingError extends Error {}
export class TenantNotFoundError extends Error {}
export class TenantUnavailableError extends Error { reason: 'suspended' | 'provisioning' | 'offboarding' }
export class TenantWrongRegionError extends Error { region: RegionCode }
export class TenantMismatchError extends Error {}           // e.g. job envelope tenant ≠ entity tenant

/** Events (emitted to OBS, no personal data) */
// tenancy.resolved, tenancy.not_found, tenancy.wrong_region, security.tenant_header_spoof, security.tenant_mismatch
```

<!-- section:usage -->
## Usage examples

**Middleware**

```ts
// apps/web/middleware.ts
import { resolveFromRequest, attachTenantHeaders } from '@nomology/tenancy';

export async function middleware(req: NextRequest) {
  const r = await resolveFromRequest(req);           // strips inbound x-nomo-* headers first
  switch (r.kind) {
    case 'tenant': { const res = NextResponse.next(); attachTenantHeaders(res, r.ctx); return res; }
    case 'wrong_region': return NextResponse.redirect(r.redirectTo, 307);
    case 'not_found': return NextResponse.rewrite(new URL('/not-found', req.url), { status: 404 });
    case 'unavailable': return NextResponse.rewrite(new URL(`/unavailable?r=${r.reason}`, req.url), { status: 503 });
    case 'platform': return NextResponse.next();
  }
}
```

**tRPC context**

```ts
export async function createContext() {
  const tenant = getTenantContext();                 // throws if middleware did not run
  const session = await getSession();
  if (session && session.tenantId !== tenant.tenantId) throw new TenantMismatchError();
  return { tenant, session };
}
```

**Worker**

```ts
// BullMQ processor
worker.process(async (job) => runWithTenant(job.data.envelope, () => sendNotice(job.data.noticeId)));
```

<!-- section:tenant -->
## Tenant context

- **Entry**: host (subdomain `{slug}.{product domain}` or a verified custom domain from `tenant_domain`), API credential, or envelope. The tenant is never taken from the request body, query string, cookies or any client-supplied header.
- **Propagation in Next.js**: middleware writes `x-nomo-tenant-id`, `x-nomo-tenant-region` and `x-nomo-tenant-sig` (HMAC-SHA256 over id, region and request id with a per-region key) to the request; `getTenantContext()` verifies the signature before trusting the headers. Inbound headers with the `x-nomo-` prefix are removed before resolution and their presence is logged as `security.tenant_header_spoof`.
- **Propagation to work**: `toEnvelope()` is called when enqueuing a BullMQ job or starting a Temporal workflow; the envelope is part of the job data / workflow input, the workflow ID is prefixed with the tenant id (`{tenantId}-{process}-{entityId}`, [[WF-separation-of-concerns-temporal]]), and the Temporal interceptor restores it with `runWithTenant` for every activity.
- **Database**: `@nomology/db` reads `getTenantContext()` and sets `app.tenant_id` per transaction ([[MT-prisma-client-extension-wraps]]).
- **Missing**: `getTenantContext()` throws `TenantContextMissingError`; there is no default tenant. Platform pages use the explicit `platform` result and the platform context of `@nomology/db`.

<!-- section:config -->
## Configuration

| Setting | Default | Where | Who changes |
|---|---|---|---|
| `TENANCY_REGION` | — (required) | Env, validated by Zod at start-up ([[FND-environment-management]]) | DevOps via IaC |
| `TENANCY_PRODUCT_DOMAINS` | — | Env | DevOps |
| `TENANCY_PLATFORM_HOST` | `admin.<domain>` | Env | DevOps |
| Directory cache TTL | 60 s positive, 15 s negative | Package constant, overridable by env | Platform engineering |
| Directory outage grace | 10 min serving stale cache | Env | Platform engineering |
| Header signing key | — | Regional secrets manager ([[INF-secrets-and-keys]]), rotated 90 days | DevOps |
| Regional host map | `{ in: 'in.<domain>', sg: 'sg.<domain>', us: 'us.<domain>' }` | Env | DevOps |

<!-- section:adapters -->
## Providers and extension points

`DirectoryClient` interface with two implementations: `HttpDirectoryClient` (calls the global directory API) and `ReplicaDirectoryClient` (reads the regional read-only copy of the directory, the default in production). A test double `InMemoryDirectory` is exported from `@nomology/tenancy/testing`.

```ts
interface DirectoryClient {
  byHost(host: string): Promise<DirectoryEntry | null>;
  byId(tenantId: string): Promise<DirectoryEntry | null>;
}
```

<!-- section:errors -->
## Error model

| Error | When | Retryable | Caller should |
|---|---|---|---|
| `TenantNotFoundError` | Unknown host or credential, deleted tenant | No | Return 404 with generic page |
| `TenantUnavailableError` | Suspended, provisioning, offboarding (write) | No | Show the unavailable page; offboarding allows read and export only |
| `TenantWrongRegionError` | Directory says another region | No | Redirect (web) or `421 Misdirected Request` (API) with problem type `wrong-region` |
| `TenantContextMissingError` | Accessor called without context | No (bug) | Fail the request with 500; alert |
| `TenantMismatchError` | Session or envelope tenant differs | No | 403; security event |
| `DirectoryUnavailableError` | Directory down beyond grace | Yes | 503 with `Retry-After` |

<!-- section:nfr -->
## Performance and limits

- Middleware resolution p99 under 5 ms on cache hit, under 40 ms on cache miss (proposed targets).
- Cache hit rate above 99% in steady state.
- No per-request database query on cache hit.
- Directory change (new domain, suspension) visible in every region within 60 s.

<!-- section:versioning -->
## Versioning and compatibility

Semver. `TenantContext` fields are additive only; removing or renaming a field is a major version and requires every app in the monorepo to update in the same pull request (the monorepo has a single version of this package). Header names and signature format are versioned (`v1:` prefix) so old and new containers can coexist during a rolling deploy.

<!-- section:testing -->
## Test contract

- Unit: host parsing (subdomain, custom domain, punycode, ports, uppercase), header stripping, signature verification, each decision branch.
- Integration: middleware with `InMemoryDirectory` for active, suspended, wrong-region and unknown tenants.
- Security: requests carrying spoofed `x-nomo-tenant-id` resolve to the host tenant and raise `security.tenant_header_spoof`; a session for tenant A on tenant B's host is rejected.
- Contract: the envelope round-trips through BullMQ and Temporal test environments with tenant intact.

<!-- section:questions -->
## Open questions

- [ ] Product domains and regional host naming (for example `{slug}.{product-domain}` with regional CNAMEs) to be confirmed by DevOps.
- [ ] Wrong-region requests: redirect at CDN by host (preferred) or in middleware only?
- [ ] Do custom domains need to be supported in Phase 1 for institutional tenants?
- [ ] Should the aggregator credential name the tenant per call (proposed) or be issued per tenant?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

The package returns exactly one tenant per request and has no API that accepts a tenant id from user input. The only cross-tenant risk is a stale cache entry after a domain moves between tenants; mitigated by a 60 s TTL, invalidation on `tenant.domain_*` events, and domain re-verification before a hostname can be attached to a different tenant.

<!-- check:security -->
### Security of the API surface

Inbound tenant headers are stripped and signed headers verified; custom domains require DNS TXT verification before use; the header signing key lives in the regional secrets manager. The package needs no database privileges beyond reading the directory replica.

<!-- check:residency -->
### Region awareness

If a request reaches the wrong region, the package redirects (web) or returns 421 (API) without reading or writing any tenant data in the wrong region. Envelopes carry the region and `runWithTenant` refuses to run a job whose envelope region differs from `TENANCY_REGION`.

<!-- check:observability -->
### Observability

Emits `tenancy.resolved` (sampled), `tenancy.not_found`, `tenancy.wrong_region`, `security.tenant_header_spoof`, `security.tenant_mismatch` with tenant id, route template and request id, never the full URL or user data ([[OBS-foundations]]). Alerts: any `tenant_mismatch` in production; wrong-region rate above 1% for 10 minutes.

<!-- check:resilience -->
### Failure behaviour

If the directory is unreachable, the regional cache serves stale entries for up to 10 minutes, then fails with 503. Suspension still applies within 60 s because the regional tenant row is checked on session creation as a second source.

<!-- check:testing -->
### Testing

Unit, integration and security tests above run on every change to `packages/tenancy/**`; the isolation suite ([[MT-automated-tests-that-prove-one]]) includes host-spoofing and envelope-mismatch cases.

<!-- end -->
