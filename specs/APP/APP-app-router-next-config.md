---
id: "APP-app-router-next-config"
title: "App Router, next.config, middleware"
parent: "APP-app-configuration"
order: 1
type: "feature"
template: "frontend"
status: "draft"
owner: null
indicative: false
summary: "next.config.ts, proxy.ts, instrumentation and the root layout of apps/web: what each does, in what order, and what it must never do"
links: []
rev: 4
syncHash: "b90723a226d90b53"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 2.1.1 App Router, next.config, middleware

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> next.config.ts, proxy.ts, instrumentation and the root layout of apps/web: what each does, in what order, and what it must never do

<!-- section:scope -->
## Scope, audiences and surfaces

Covers the app-level plumbing of `apps/web` that runs before or around every route group:

- `next.config.ts` (build output, Cache Components, cache handlers, Server Actions limits, images, headers that are static)
- `proxy.ts` (formerly `middleware.ts`): tenant resolution, region check, CSP nonce, coarse session gate, request ID
- `instrumentation.ts` and `instrumentation-client.ts`: OpenTelemetry, start-up config validation, client error and Web Vitals hooks
- `app/layout.tsx` (root layout): `<html lang dir>`, theme CSS variables, skip link, providers
- `app/global-error.tsx` and `app/not-found.tsx`

Personas: all. Hosts: every tenant host (subdomain or custom domain) and the platform-admin host in each region.

Out of scope: per-group layouts and routes ([[APP-route-groups-per-persona]] and children), the header values themselves ([[APP-security-headers-csp-cors]]), cache design ([[APP-rendering-and-caching-strategy]]).

<!-- section:routing -->
## Routes, layouts and boundaries

```text
apps/web/
  next.config.ts
  proxy.ts                      # runs on every request except static assets
  instrumentation.ts            # server: OTel, loadConfig(), onRequestError
  instrumentation-client.ts     # browser: RUM init, error hooks (no PII)
  app/
    layout.tsx                  # root: <html lang dir>, theme vars, skip link, providers
    global-error.tsx            # last-resort boundary, renders its own <html>
    not-found.tsx               # generic not found (same copy as no-access)
    (public)/ (counsel)/ (neutral)/ (secretariat)/
    (transcriber)/ (tenant-admin)/ (platform-admin)/
    api/
      trpc/[trpc]/route.ts      # internal tRPC endpoint
      v1/[...path]/route.ts     # public REST (see APP-route-handlers-trpc-for-internal)
      csp-report/route.ts       # CSP violation reports -> regional collector
      health/route.ts           # liveness/readiness for ECS (no tenant)
```

**`proxy.ts` order of operations** (Node.js runtime):

1. Skip static paths (`/_next/static`, `/_next/image`, `/fonts`, `/favicon.ico`) via `config.matcher`.
2. Generate `x-request-id` (UUIDv7) unless a trusted upstream set one; strip any inbound `x-tenant-id`, `x-region`, `x-nonce` headers.
3. Resolve tenant from `host` through the tenant directory client ([[MT-tenant-resolution]]), cached in-process for 60 s. Unknown host: 404 with the generic page. Suspended tenant: 503 page with tenant-neutral copy.
4. Region check: if the tenant's home region is not this region, return `308` to the same path on the home-region host ([[MT-data-residency-2]]). Never proxy across regions.
5. Platform-admin isolation: any `/platform` or legacy `/ops` path on a tenant host returns 404; on the platform-admin host any path outside `/platform/*` returns 404, except legacy `/ops/*`, which permanently redirects to the same path under `/platform/*` for 12 months ([[APP-route-groups-per-persona]]).
6. Generate a per-request nonce (16 random bytes, base64) and set the CSP header for dynamic routes ([[APP-security-headers-csp-cors]]).
7. Coarse session gate: for persona prefixes, if no `__Host-session` cookie, redirect to `/sign-in?next=<relative path>`. Presence only; validation happens on the server in each page and action.
8. Forward `x-tenant-id`, `x-region`, `x-nonce`, `x-request-id` as request headers to the render.

`proxy.ts` makes **no authorisation decisions** and performs **no database reads**.

<!-- section:rendering -->
## Rendering and caching strategy

App-wide defaults (route groups override in their own nodes, decided in [[APP-rendering-and-caching-strategy]]):

| Route | Rendering | Cache-Control |
|---|---|---|
| `(public)` marketing-free pages: `/sign-in`, `/status`, `/accessibility` | Static shell prerendered, tenant branding streamed in a dynamic hole | `public, max-age=0, s-maxage=300` on the shell only if the CDN key includes host; otherwise `private, no-cache` |
| All persona prefixes | Dynamic at request time (nonce CSP), streamed with `<Suspense>` | `private, no-store` |
| `/api/trpc/*`, `/api/v1/*` | Dynamic | `no-store` (public API may set `private, max-age` on specific GETs) |
| `/_next/static/*` | Immutable build assets | `public, max-age=31536000, immutable` |

`next.config.ts` sketch:

```ts
import type { NextConfig } from 'next';
const config: NextConfig = {
  output: 'standalone',
  deploymentId: process.env.BUILD_SHA,            // version-skew protection
  cacheComponents: true,
  cacheHandlers: { remote: require.resolve('./cache/redis-handler.mjs') },
  poweredByHeader: false,
  reactStrictMode: true,
  typedRoutes: true,
  serverExternalPackages: ['@prisma/client', '@temporalio/client'],
  images: { remotePatterns: [] },                   // no remote images; logos come via our own storage route
  experimental: { serverActions: { bodySizeLimit: '1mb', allowedOrigins: [] } }, // origins filled per region from config
};
export default config;
```

The exact location of `serverActions` options must be checked on each Next.js upgrade.

<!-- section:data -->
## Data fetching and mutations

The root layout may read only: the resolved tenant's theme version and tokens ([[PKG-branding-and-theming]]), the effective locale and direction, and the signed-in user's display name and active tenant list for the header ([[PKG-tenant-and-role-switcher]]). Each read goes through `@nomology/data-access` with `React.cache` per request. The theme read is cached with `'use cache: remote'` keyed by `tenantId` and `themeVersion`.

No case data is read in the root layout or any group layout. Mutations are never defined at this level.

<!-- section:errors -->
## Error, loading and empty handling

| Situation | Handled by |
|---|---|
| Unknown host | `proxy.ts` → 404 static page, no tenant branding |
| Tenant suspended | `proxy.ts` → 503 static page "This service is not available at the moment" |
| Wrong region | `proxy.ts` → 308 to home-region host |
| Unhandled render error in root layout | `app/global-error.tsx` (renders its own `<html>`, reports to collector with digest) |
| Route not found | `app/not-found.tsx`, same copy as no-access ([[APP-error-message-catalogue]]) |
| Server exception anywhere | `onRequestError` in `instrumentation.ts` records route template, digest, tenantId, request ID; never the error message to the browser |

Group-level boundaries are defined in [[APP-error-boundaries-loading-and]].

<!-- section:performance -->
## Performance budgets

App-level budgets (the group budgets in [[APP-frontend-performance-budgets]] add to these):
- `proxy.ts` p95 ≤ 5 ms per request in region (tenant directory hit from in-process cache); alarm if p95 > 20 ms
- Root layout server time p95 ≤ 30 ms (theme from remote cache)
- Shared client JavaScript (framework + providers + root layout) ≤ 95 KB gzip
- Fonts: at most two self-hosted WOFF2 files preloaded per script ([[PKG-typography-and-multi-script]])
Enforced by a CI bundle-size check (`size-limit` on `.next` output) and RUM.

<!-- section:security -->
## Security headers and browser session

`proxy.ts` sets the nonce-based CSP for dynamic routes; static headers (HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy` default, `Cross-Origin-Opener-Policy`) are set in `next.config.ts` `headers()` so they also apply to static assets. Values in [[APP-security-headers-csp-cors]].

- `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` is loaded from the regional secrets manager and is identical across all tasks of a region and across the two versions running during a rolling deploy.
- `serverActions.allowedOrigins` is set to the tenant hosts of this region (custom domains included), refreshed at deploy; requests from other origins are rejected by Next.js.
- Session cookie handling is owned by [[PKG-mfa-session-management-device]]; the proxy only checks presence.

<!-- section:i18n -->
## Localisation hookup

The root layout computes the locale in this order: user preference → tenant default → `Accept-Language` matched against the tenant's enabled locales → `en`. It sets `<html lang={locale} dir={dir}>` and loads only the message namespaces used by the active route group ([[I18N-i18n]]). Locale is not in the URL.

<!-- section:theming -->
## Tenant theming hookup

The root layout injects the tenant's compiled theme as CSS custom properties in a nonce'd `<style>` tag inside `<head>`, before any content, so there is no flash of default branding. Theme tokens come from the active, validated theme version ([[PKG-tenant-theme-schema-and]]). Colour mode (light, dark, high contrast) is read from a cookie and rendered on the server ([[PKG-colour-modes-and-user]]).

<!-- section:observability -->
## Frontend observability

`instrumentation.ts` registers OpenTelemetry (`@vercel/otel` or the OTel Node SDK) exporting to the regional collector ([[OBS-foundations]]). Every span carries `tenant.id`, `region`, `route.group`, `route.template` (for example `/portal/cases/[caseRef]`), `release` and `request.id`; no URL with IDs, no query strings, no user names. `instrumentation-client.ts` initialises Web Vitals and error reporting to the regional RUM endpoint ([[OBS-frontend-real-user-monitoring]]).

<!-- section:testing -->
## Testing strategy

- Unit tests for `proxy.ts`: unknown host, suspended tenant, wrong region, `/platform` and `/ops` on tenant host, `/ops` redirect on the platform-admin host, header stripping, missing session cookie
- Contract test: `/api/health` returns no tenant data and needs no session
- Preview-deployment check: headers asserted on one route per group ([[APP-security-headers-csp-cors]])
- Version-skew test in staging: deploy N+1 while a Playwright session holds an N page, then submit a Server Action (expects hard reload, no data loss)

<!-- section:questions -->
## Open questions

- [ ] Tenant directory cache TTL in `proxy.ts` (60 s proposed): acceptable delay for suspension to take effect, or do we need push invalidation? (owner: platform engineering, [[MT-tenant-resolution]])
- [ ] Which OpenTelemetry package: `@vercel/otel` or the plain OTel Node SDK, given self-hosting? (owner: observability)
- [ ] Is `experimental.sri` (needed for hash-based CSP on static shells) supported with the bundler we build with? (owner: frontend lead, [[APP-rendering-and-caching-strategy]])

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation in rendering and caching

The tenant is resolved only from the host in `proxy.ts`; inbound `x-tenant-id` headers are stripped before resolution, so a client cannot inject one. The forwarded header is a hint used to pick the tenant transaction; every page and action then re-checks the session's membership in that tenant on the server ([[PKG-rbac-abac-case-level-party]]). The only cached read at this level (theme) is keyed by `tenantId` and `themeVersion`.

<!-- check:browser-security -->
### Browser security posture

Nonce-based CSP from `proxy.ts` for every dynamic route, static security headers from `next.config.ts` for all responses. `images.remotePatterns` is empty, so the image optimiser cannot be used to fetch arbitrary URLs (an SSRF vector). Redirects after sign-in accept only relative paths starting with a single `/`.

<!-- check:resilience -->
### Failure, deploys and version skew

`deploymentId` is the commit SHA, so a browser with an old bundle receives a hard navigation rather than broken chunk loads during an ECS rolling deploy; the Server Actions encryption key is shared across tasks and versions. The previous release's `/_next/static` assets remain on the CDN origin for at least 24 hours after a deploy.

<!-- check:residency -->
### Region, residency and telemetry privacy

The same image runs per region with region-specific collector, CDN and sandbox-origin hosts from config; the browser only contacts hosts in the tenant's region (enforced by the per-region CSP `connect-src`). Fonts are self-hosted. Source maps are uploaded privately to the regional error collector and not served by the app.

<!-- check:supply-chain -->
### Framework upgrades and supply chain

Next.js and React versions are pinned in the root `pnpm-workspace.yaml` catalog ([[APP-framework-dependencies]]). Security releases are applied within 72 hours for critical advisories (for example the December 2025 React Server Components vulnerability [R1]). The `middleware` to `proxy` rename in Next.js 16 [R2] is handled by the official codemod and covered by the proxy unit tests.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "kind": "vendor",
    "title": "Critical security vulnerability in React Server Components",
    "url": "https://react.dev/blog/2025/12/03/critical-security-vulnerability-in-react-server-components",
    "vendor": "Meta (React)"
  },
  {
    "id": "R2",
    "kind": "vendor",
    "title": "Next.js: How to upgrade to version 16",
    "url": "https://nextjs.org/docs/app/guides/upgrading/version-16",
    "vendor": "Vercel (Next.js)"
  }
]
```

<!-- end -->
