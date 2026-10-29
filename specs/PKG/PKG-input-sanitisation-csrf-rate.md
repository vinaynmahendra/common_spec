---
id: "PKG-input-sanitisation-csrf-rate"
title: "Input sanitisation, CSRF, rate limiting, bot protection"
parent: "PKG-security"
order: 2
type: "feature"
template: "security"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 3
syncHash: "a529595e82b365b2"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.4.2 Input sanitisation, CSRF, rate limiting, bot protection

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

`@nomology/http-guard` provides the request-level protections every entry point uses: schema validation conventions at trust boundaries, sanitisation of HTML, file names and spreadsheet exports, CSRF defence for routes that Next.js Server Actions do not cover, rate limiting and abuse controls, and the hooks for bot protection. Header-level defences (CSP, CORS, HSTS) are in [[APP-security-headers-csp-cors]]; API rate limits for external consumers and idempotency are in [[APP-api-versioning-rate-limiting]] and use this package's limiter.

Protects: integrity of case records against forged or injected input; users against stored XSS in messages and filings; service capacity and cost (SMS, OTP, AI) against automated abuse.

<!-- section:assets -->
## Protected assets

| Asset | Risk |
|---|---|
| State-changing endpoints (Server Actions, tRPC mutations, Route Handlers, webhooks in) | Forged requests, injection |
| Rich text in messages, procedural notes, form answers | Stored XSS |
| Uploaded file names and metadata | Path traversal, header injection |
| CSV / XLSX exports (case lists, reports) | Formula injection when opened in spreadsheets |
| OTP, magic link, sign-in, public filing entry | Abuse, enumeration, SMS cost |
| Search and list endpoints | Scraping |

<!-- section:actors -->
## Actors and roles

| Actor | Concern |
|---|---|
| Signed-in users (all personas) | Must not be throttled in normal use (secretariat bulk actions, transcriber autosave) |
| Unauthenticated visitors | Public filing entry, sign-in, status pages |
| API clients and aggregators | Separate quotas by credential ([[INT-public-api-and-webhooks]]) |
| Attackers and bots | Credential stuffing, scraping, SMS pumping, CSRF |
| Platform security | Adjust limits during incidents |

<!-- section:matrix -->
## Permission matrix

Control coverage by entry point (✓ = applied by default by the package; — = not applicable):

| Entry point | Schema validation | CSRF / origin | Rate limit bucket | HTML sanitise | Bot hook |
|---|---|---|---|---|---|
| Server Actions | ✓ zod (`defineAction`) | Next.js origin check [R3] **plus** package check rejecting missing `Origin` | `user` 60/min burst 120 | ✓ for rich-text fields | — |
| tRPC mutations | ✓ zod input | ✓ origin check + custom header `x-trpc-source` | `user` 120/min | ✓ | — |
| Route Handlers (browser, cookie-auth) | ✓ | ✓ origin check; double-submit token for form posts from other subdomains | `user` or `ip` | ✓ | — |
| Public API (API key / OAuth) | ✓ OpenAPI-derived zod | — (no cookies accepted) | `api_client` per plan | ✓ | — |
| Inbound webhooks (providers) | ✓ | — (signature verification instead) | `provider` | — | — |
| Sign-in, OTP, magic link, reset | ✓ | ✓ | `account` 5/15 min, `ip` 30/15 min, `ip_prefix` 300/15 min | — | ✓ |
| Public filing entry | ✓ | ✓ | `ip` 10/hour, `tenant` 500/hour | ✓ | ✓ |
| Search, list, export | ✓ | ✓ | `user` 30/min search, 5/hour exports | — | — |
| SMS sends (any cause) | — | — | `tenant` daily budget, `phone` 5/hour | — | — |

<!-- section:policy -->
## Policy model

- **Validation**: every boundary uses zod schemas with explicit max lengths (default strings ≤ 2,000 chars, names ≤ 200, IDs as UUID), enums, and `strict()` objects (unknown keys rejected). Validation errors return the problem type `validation/failed` with field paths ([[APP-api-error-catalogue-problem]]).
- **Injection**: database access only through Prisma parameterisation or tagged `$queryRaw` (unsafe raw variants removed, [[PKG-data-access]]); no shell execution of user input; file paths built only by [[PKG-object-storage-abstraction-s3]] key builders; outbound URLs supplied by tenants (webhooks, SSO metadata) fetched only through the egress proxy with private-address blocking (SSRF).
- **HTML**: rich text is accepted as a restricted HTML subset (p, br, strong, em, ul, ol, li, a[href https/mailto], blockquote) and sanitised server-side on write with an allow-list sanitiser; rendering uses React escaping, never `dangerouslySetInnerHTML` except through the sanitised component.
- **File names**: Unicode NFC, strip control and path characters, max 200 bytes; original name kept only as metadata; `Content-Disposition` uses RFC 6266 `filename*` encoding.
- **Exports**: cells beginning with `=`, `+`, `-`, `@`, tab or carriage return are prefixed with `'` in CSV and written as text in XLSX.
- **CSRF**: cookies are `SameSite=Lax`; all state-changing browser requests must carry an `Origin` header matching the tenant host — Next.js lets requests without `Origin` through with a warning [R3], so the package rejects them for mutations; GET requests never change state [R4].
- **Rate limiting**: sliding-window counters in the regional cache Redis keyed `{region}:rl:{bucket}:{tenantId}:{subject}`; tenant admins cannot raise limits, platform security can per tenant. Responses use 429 with `Retry-After` and `RateLimit` headers.
- **Bot protection**: WAF managed bot rules at the edge ([[INF-networking]]); for sign-in and public filing, a progressive approach (throttle → proof-of-work challenge → block) without puzzle CAPTCHAs, consistent with [[PKG-accessible-authentication-and]].

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|---|
| T1 | T | CSRF on a Route Handler that changes state | Origin check, SameSite=Lax, no state change on GET | Low |
| T2 | T | Missing-Origin request to a Server Action (older clients, proxies stripping headers) | Package rejects mutations without Origin | Low |
| T3 | T/E | Stored XSS in a message read by the tribunal | Server-side sanitisation + CSP with nonces/hashes | Low |
| T4 | I | CSV formula injection in exported case lists | Prefixing dangerous cells | Low |
| T5 | D | Credential stuffing from rotating IPs | Account and IP-prefix buckets; anomaly alerts | Medium |
| T6 | D | SMS pumping | Per-tenant SMS budget, verified numbers only, country allow-list | Low |
| T7 | I | SSRF via tenant-supplied webhook or metadata URL | Egress proxy, deny private ranges, DNS rebinding protection | Low |
| T8 | D | Rate limits lock out a secretariat doing bulk work | Per-user limits sized for bulk actions; bulk endpoints accept batches | Low |

<!-- section:failure -->
## Denial behaviour

Validation errors: 422 with field-level messages from [[APP-error-message-catalogue]]. CSRF failures: 403 `security/origin-mismatch`, logged as a security event. Rate limits: 429 with `Retry-After`; UI shows "Too many attempts. Try again in N minutes." Sanitisation silently removes disallowed markup and records a counter (not the content).

<!-- section:requirements -->
## Security requirements

ASVS references are to OWASP ASVS **5.0** at section level [R1][R2]; requirement-level IDs to be added after checking against the 5.0.0 text.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| GRD-1 | All inputs at trust boundaries shall be validated with strict schemas including maximum lengths. | V2.2 |
| GRD-2 | State-changing browser requests without a matching `Origin` header shall be rejected. | V3.5 |
| GRD-3 | User-supplied rich text shall be sanitised server-side against an allow-list before storage. | V1.3 |
| GRD-4 | Spreadsheet exports shall neutralise formula-leading cells. | V1.2 |
| GRD-5 | Authentication and OTP endpoints shall be rate limited per account, per IP and per IP prefix. | V2.4 |
| GRD-6 | Tenant-supplied URLs shall be fetched only through the egress proxy, which blocks private and link-local addresses. | V1.3, V13.2 |
| GRD-7 | No GET request shall change state. | V3.5 |

<!-- section:verification -->
## Verification

Unit tests for sanitiser (OWASP XSS vectors), file-name normaliser and CSV neutraliser; integration tests for Origin enforcement on each entry-point type; rate-limit tests with a fake clock; SSRF tests against the egress proxy (private IP, IPv6 link-local, DNS rebinding); DAST in CI against preview environments ([[TST-security-testing]]).

<!-- section:questions -->
## Open questions

- [ ] Proof-of-work challenge library or edge bot service — which keeps data in region? Owner: security.
- [ ] Do we need a Content Disarm and Reconstruction step for uploaded Office files, beyond malware scanning ([[PKG-encryption-at-rest-signed-urls]])?
- [ ] Rate-limit defaults per plan for the public API — owned by [[APP-api-versioning-rate-limiting]], confirm values.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Rate-limit keys include region and tenant so one tenant's traffic cannot exhaust another's budget; per-tenant overrides are set only by platform security. Validation and sanitisation are stateless.

<!-- check:enforcement -->
### Enforcement points and bypass paths

Guards are applied through wrappers (`defineAction`, tRPC middleware, `withRouteGuard` for Route Handlers) that every entry point must use; a CI check lists Route Handlers and fails if one is not wrapped. Rate limits for authentication routes are in the auth package itself so they cannot be skipped.

<!-- check:resilience -->
### Failure modes and secrets

If the cache Redis is unavailable, rate limiting fails closed for authentication, OTP, SMS and public filing routes (503 with retry) and fails open for authenticated reads, with an alert. Sanitisation and validation are local and have no dependencies.

<!-- check:residency -->
### Data residency

Rate-limit counters live in the regional cache Redis; the egress proxy and WAF rules are regional; no request content is sent to a global bot service without a residency review.

<!-- check:audit -->
### Audit trail

Origin rejections, repeated rate-limit blocks on authentication routes and sanitisation of dangerous markup are recorded as security events (not tenant audit events), with hashed IP and route template only.

<!-- check:observability -->
### Detection and alerting

Metrics: `http_guard.rate_limited` by bucket and route template, `http_guard.origin_rejected`, `http_guard.sanitised_fields`. Alerts: rate-limit hits on sign-in above baseline per tenant; any burst of origin rejections (possible CSRF attempt); SMS budget at 80%.

<!-- check:testing -->
### Verification and testing

CI runs the XSS vector suite, origin-enforcement tests for every entry-point type, SSRF tests and rate-limit tests; DAST scans each preview environment.

<!-- citations -->
## Citations

```json
[
  {
    "body": "OWASP",
    "id": "R1",
    "ident": "ASVS",
    "kind": "standard",
    "title": "OWASP Application Security Verification Standard",
    "url": "https://owasp.org/www-project-application-security-verification-standard",
    "version": "5.0"
  },
  {
    "body": "OWASP",
    "id": "R2",
    "ident": "ASVS",
    "kind": "standard",
    "title": "OWASP Cheat Sheet Series: ASVS 5.0 index (chapter and section titles)",
    "url": "https://cheatsheetseries.owasp.org/IndexASVS.html",
    "version": "5.0.x"
  },
  {
    "excerpt": "Next.js compares the host in the Origin header against the app host and rejects the action when they differ; a request with no Origin header is allowed through with a warning. Default body size limit is 1MB.",
    "id": "R3",
    "kind": "vendor",
    "title": "Next.js docs: serverActions (allowedOrigins, bodySizeLimit)",
    "url": "https://nextjs.org/docs/app/api-reference/config/next-config-js/serverActions",
    "vendor": "Vercel (Next.js)"
  },
  {
    "body": "OWASP",
    "id": "R4",
    "ident": "Cheat Sheet Series",
    "kind": "standard",
    "title": "OWASP Cross-Site Request Forgery Prevention Cheat Sheet",
    "url": "https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet"
  }
]
```

<!-- end -->
