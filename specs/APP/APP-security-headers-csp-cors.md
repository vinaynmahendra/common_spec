---
id: "APP-security-headers-csp-cors"
title: "Security headers, CSP, CORS"
parent: "APP-app-configuration"
order: 3
type: "feature"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 2
syncHash: "85ac08bb85a267c0"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.1.3 Security headers, CSP, CORS

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

Defines the HTTP response headers `apps/web` must send, the Content Security Policy for each route family, and the CORS policy for API routes. Applies to every response from the app in every region, including error pages and Route Handlers. The rendering trade-off (nonce versus hash) is decided in [[APP-rendering-and-caching-strategy]]; this node fixes the values.

<!-- section:rules -->
## Rules

1. **HDR-1** Every HTML response carries a strict CSP: script sources are only `'nonce-{n}'` (dynamic routes) or `'sha256-…'` hashes (static shells), plus `'strict-dynamic'`; never `'unsafe-inline'` or `'unsafe-eval'` for scripts in production.
2. **HDR-2** Baseline CSP for all HTML:
   ```text
   default-src 'self';
   script-src 'self' 'nonce-{n}' 'strict-dynamic';
   style-src 'self' 'nonce-{n}';
   img-src 'self' blob: data: https://{region-assets-host};
   font-src 'self';
   connect-src 'self' https://{region-rum-host};
   frame-src https://{region-docs-origin};
   media-src 'self' blob: https://{region-media-host};
   object-src 'none'; base-uri 'none'; form-action 'self';
   frame-ancestors 'none'; upgrade-insecure-requests;
   report-to csp; report-uri /api/csp-report
   ```
   Route-specific additions only: payment pages (gateway hosts), hearing room (video provider hosts). Each addition is declared in `packages/csp/routes.ts`.
3. **HDR-3** Static headers on every response:

   | Header | Value |
   |---|---|
   | `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` (custom domains: without `preload` unless the tenant requests it) |
   | `X-Content-Type-Options` | `nosniff` |
   | `Referrer-Policy` | `strict-origin-when-cross-origin` (persona routes: `same-origin`) |
   | `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), payment=(), usb=(), display-capture=()` except on hearing-room routes |
   | `Cross-Origin-Opener-Policy` | `same-origin` (sign-in with SSO pop-ups: `same-origin-allow-popups`) |
   | `Cross-Origin-Resource-Policy` | `same-origin` for HTML and API |
   | `X-Frame-Options` | `DENY` (legacy browsers; CSP `frame-ancestors` is authoritative) |
4. **HDR-4** Authenticated HTML and all `/api/trpc` responses carry `Cache-Control: private, no-store`.
5. **HDR-5** CORS: `/api/trpc/*` and Server Actions are same-origin only (no `Access-Control-Allow-Origin`). `/api/v1/*` (public REST) allows any origin **without credentials** (`Access-Control-Allow-Origin: *`, no `Access-Control-Allow-Credentials`), since it authenticates with bearer tokens, not cookies. No route reflects the request `Origin`.
6. **HDR-6** New CSP sources ship in `Content-Security-Policy-Report-Only` for at least 7 days in staging and 7 days in production before enforcement.
7. **HDR-7** Server Actions accept requests only from this region's tenant hosts (`serverActions.allowedOrigins`); tRPC mutations require a custom header (`x-trpc-source: web`) in addition to SameSite cookies.
8. **HDR-8** Uploaded content is never served from the app origin; it is served from the sandbox origin with its own policy ([[APP-document-viewer-and-sandbox]]).

<!-- section:rationale -->
## Rationale

- Nonces with `'strict-dynamic'` let Next.js load its chunks while blocking injected scripts; this is the approach Next.js documents for App Router [R1] and matches OWASP guidance [R2].
- `frame-ancestors 'none'` stops clickjacking of consequential actions (file, pay, issue award).
- Allowing `*` on the public REST API without credentials is safe because the browser sends no cookies; reflecting `Origin` with credentials is the common CORS mistake.
- Report-Only first (HDR-6) avoids breaking a hearing or payment when a vendor changes its hosts.

<!-- section:tooling -->
## Tooling and configuration

- `packages/csp`: builds the policy string from the baseline plus route additions; used by `proxy.ts` (nonce) and the build step (hashes).
- `next.config.ts` `headers()` for static headers.
- `/api/csp-report` Route Handler forwarding reports to the regional collector after stripping URLs to route templates ([[OBS-frontend-real-user-monitoring]]).
- `scripts/assert-headers.ts`: Playwright request-level test run against each preview deployment.

<!-- section:enforcement -->
## Enforcement

| Rule | Check | Stage |
|---|---|---|
| HDR-1, 2, 3, 4 | `assert-headers.ts` requests one route per group and per route family and compares to the expected set | PR preview deploy (required check) and post-deploy smoke per region |
| HDR-2 additions | ESLint rule: CSP sources only in `packages/csp/routes.ts`; CODEOWNERS: security | PR |
| HDR-5 | Contract test on `/api/trpc` and `/api/v1` preflight responses | CI |
| HDR-6 | Review checklist; enforcement flag per source in `routes.ts` with a date | PR review |
| HDR-7 | Integration test: Server Action from foreign origin returns error | CI |

<!-- section:examples -->
## Examples

Good: a payment page adds `connect-src https://checkout.{gateway}` in `routes.ts` under `/portal/cases/*/payments/*/pay` only.

Bad: adding the gateway host to the baseline `connect-src` so every page can reach it; adding `'unsafe-inline'` to make an inline analytics snippet work.

<!-- section:exceptions -->
## Exceptions

Exceptions are recorded in `packages/csp/exceptions.ts` with owner, reason, ticket and expiry date, and require security approval. HDR-1 (`unsafe-inline` / `unsafe-eval` in production) and HDR-5 credentialed wildcard CORS are non-waivable.

<!-- section:questions -->
## Open questions

- [ ] Is Trusted Types (`require-trusted-types-for 'script'`) feasible with our dependencies? Trial in Report-Only (owner: security)
- [ ] HSTS `preload` for tenant custom domains: offer as opt-in or never? (owner: DevOps)
- [ ] Do any IdPs used by tenants require pop-up SSO, needing `same-origin-allow-popups` on sign-in? (owner: identity, [[PKG-sso-saml-oidc-per-tenant]])

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Every header rule is checked by `assert-headers.ts` against the deployed preview (required check) and again after each regional deploy; CSP source additions are lint-restricted to one file owned by security in CODEOWNERS.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

The standard keeps uploaded content off the app origin (HDR-8), keeps authenticated pages out of caches (HDR-4) and keeps telemetry within region by listing only regional collector hosts in `connect-src`.

<!-- check:exceptions -->
### Exceptions

Exceptions live in `packages/csp/exceptions.ts` with owner, ticket and expiry; a CI job fails when an exception is past its expiry; two rules are non-waivable.

<!-- check:compliance -->
### Compliance evidence

Supports ISO 27001:2022 Annex A 8.26 (application security requirements) and 8.28 (secure coding) evidence through the stored header test results per release, and answers typical institution security questionnaires on CSP and clickjacking.

<!-- check:ownership -->
### Ownership and change

Owner: security lead with the frontend lead as deputy; changes need CODEOWNERS approval from security; the header set is reviewed at each Next.js major upgrade.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "kind": "vendor",
    "title": "Next.js: How to set a Content Security Policy",
    "url": "https://nextjs.org/docs/app/guides/content-security-policy",
    "vendor": "Vercel (Next.js)"
  },
  {
    "body": "OWASP",
    "id": "R2",
    "kind": "standard",
    "title": "Content Security Policy Cheat Sheet",
    "url": "https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html"
  }
]
```

<!-- end -->
