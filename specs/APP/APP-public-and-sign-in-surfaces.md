---
id: "APP-public-and-sign-in-surfaces"
title: "Public and sign-in surfaces"
parent: "APP-route-groups-per-persona"
order: 7
type: "requirement"
template: "frontend"
status: "draft"
owner: null
indicative: false
summary: "Frontend architecture for the (public) route group: sign-in, invitation acceptance, SSO hand-off, public filing entry, status pages; static-shell friendly with hash-based CSP"
links: []
rev: 2
syncHash: "33659a818d888526"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.1.2.7 Public and sign-in surfaces

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Frontend architecture for the (public) route group: sign-in, invitation acceptance, SSO hand-off, public filing entry, status pages; static-shell friendly with hash-based CSP

<!-- section:scope -->
## Scope, audiences and surfaces

Frontend architecture of the `(public)` route group on every tenant host: sign-in, invitation acceptance, SSO hand-off, public filing entry, the service status page and the tenant's accessibility statement and legal pages. Audiences: anyone who receives a notice, including first-time unrepresented parties on mobile phones with low digital confidence, and professionals signing in daily.

Out of scope: authentication mechanisms ([[PKG-email-password-magic-link-otp]], [[PKG-sso-saml-oidc-per-tenant]], [[PKG-mfa-session-management-device]]); accessible authentication requirements ([[PKG-accessible-authentication-and]]), which this node implements; the marketing website.

<!-- section:routing -->
## Routes, layouts and boundaries

```text
app/(public)/
  layout.tsx                    # minimal tenant-branded shell; no session required
  page.tsx                      # tenant landing: sign in, file a new matter, check status
  sign-in/page.tsx              # email -> method choice (password, magic link, passkey, SSO)
  sign-in/verify/page.tsx       # OTP / magic-link landing
  invite/[token]/page.tsx       # invitation acceptance (case participant or tenant staff)
  sso/[connection]/start/route.ts   # Route Handler: redirect to IdP
  sso/[connection]/callback/route.ts
  file/page.tsx                 # public filing entry: eligibility, then account creation
  file/[step]/page.tsx
  status/page.tsx               # regional service status
  accessibility/page.tsx        # tenant accessibility statement (APP-accessibility-conformance)
  legal/[doc]/page.tsx          # terms, privacy notice by version
```
`next` parameters on sign-in accept only relative paths that start with a single `/` and match a known persona prefix.

<!-- section:rendering -->
## Rendering and caching strategy

| Route | Rendering | CSP | Cache-Control |
|---|---|---|---|
| `/`, `/sign-in`, `/status`, `/accessibility`, `/legal/[doc]` | static shell + dynamic hole for tenant branding and content | hash-based | shell `public, s-maxage=300` with CDN key including host; dynamic parts `private, no-cache` |
| `/sign-in/verify`, `/invite/[token]`, `/file/[step]` | dynamic | nonce-based | `private, no-store` |
| `sso/*` Route Handlers | dynamic | n/a | `no-store` |

Tenant branding, statement text and legal documents are read through `'use cache: remote'` keyed by `(tenantId, locale, version)`. Decision and trade-off in [[APP-rendering-and-caching-strategy]].

<!-- section:data -->
## Data fetching and mutations

| Operation | Kind | Notes |
|---|---|---|
| `startSignIn` | Server Action | looks up method by email domain and tenant SSO settings; same response whether or not the account exists |
| `verifyOtp`, `consumeMagicLink` | Server Action | rate limited per email and per IP ([[PKG-input-sanitisation-csrf-rate]]) |
| `acceptInvitation` | Server Action | token single-use, 7-day expiry (proposed); binds the account to the case or tenant role |
| `publicFiling.saveStep` | Server Action | anonymous draft keyed by a signed cookie until account creation; then moved to the user |
| `getServiceStatus` | server read | from [[OBS-uptime-synthetic-monitoring]] for this region |

<!-- section:forms -->
## Forms, validation and uploads

Sign-in and OTP forms work without JavaScript. OTP inputs accept paste and autofill (`autocomplete="one-time-code"`), allow 10 minutes, and offer resend after 30 seconds. No puzzle CAPTCHA; bot protection is invisible risk scoring with an accessible fallback (email link). Public filing steps save on each step so a party can return from the emailed link.

<!-- section:errors -->
## Error, loading and empty handling

Sign-in errors never reveal whether an account exists ('If an account exists for this email, we have sent a sign-in link'). Expired invitation shows who to contact at the institution. SSO failures show the IdP name and a support reference without technical detail.

<!-- section:performance -->
## Performance budgets

`(public)` budgets: LCP ≤ 2.0 s, ≤ 130 KB gzip first-load JS on mid-range Android over slow 4G; TTFB ≤ 200 ms for static shells in region.

<!-- section:security -->
## Security headers and browser session

- Hash-based strict CSP on static shells, nonce-based on dynamic routes; no third-party scripts except the bot-protection provider on sign-in if chosen (assessed in [[INT-third-party-component]]).
- `frame-ancestors 'none'` everywhere (sign-in must never be framed).
- Open redirect protection on `next` and SSO `RelayState`.
- Anonymous filing drafts use a signed, HttpOnly cookie and expire after 7 days.

<!-- section:i18n -->
## Localisation hookup

Locale from `Accept-Language` matched against the tenant's enabled locales, with a visible language switcher on every public page; the choice is remembered in a cookie and copied to the user profile after sign-in.

<!-- section:theming -->
## Tenant theming hookup

Tenant logo and colours from the active theme; if the tenant has no theme yet, a neutral platform theme. The tenant name is shown as text, not only in the logo.

<!-- section:testing -->
## Testing strategy

Playwright: sign in by each method; accept invitation; public filing to account creation; keyboard-only sign-in; 3.3.8 checks (paste allowed, no cognitive test); open redirect tests; CSP header tests for static and dynamic routes.

<!-- section:questions -->
## Open questions

- [ ] Bot protection provider (if any) and its accessibility and residency (owner: security)
- [ ] Invitation expiry (7 days proposed) and whether institutions can change it (owner: product)
- [ ] Should public filing be available for all tenant types or only CORD and SEBI ODR tenants? (owner: CORD product)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation in rendering and caching

Static shells are tenant-neutral; branding and text are a dynamic hole keyed by tenant. The CDN cache key includes the host, so one tenant's shell cannot be served on another's host. Anonymous drafts are bound to the tenant host by the signed cookie.

<!-- check:browser-security -->
### Browser security posture

Hash-based strict CSP on shells and nonce CSP on dynamic routes; sign-in cannot be framed; redirects limited to known relative prefixes; no third-party scripts except a vetted bot-protection script if chosen.

<!-- check:session -->
### Sessions in the browser

Session cookie is issued only after successful verification, as `__Host-session`; a 'shared device' option shortens the session; magic links and OTPs are single-use with rate limits.

<!-- check:capacity -->
### Rendering cost and capacity

Static shells served from the CDN absorb notice-driven spikes (for example thousands of SEBI ODR notices sent at once); dynamic verification endpoints are rate limited and sized for 50 sign-ins per second per region (proposed).

<!-- check:accessibility -->
### App-level accessibility mechanics

Implements WCAG 2.2 3.3.8 Accessible Authentication: paste and password managers work, magic link and passkey alternatives, no puzzles; OTP time is 10 minutes with resend. See [[PKG-accessible-authentication-and]].

<!-- end -->
