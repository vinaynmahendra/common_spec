---
id: "PKG-email-password-magic-link-otp"
title: "Email/password, magic link, OTP"
parent: "PKG-authentication"
order: 1
type: "feature"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "First-factor methods for people without SSO: passwords (15+ characters, breach-checked, Argon2id), browser-bound magic links, email, SMS and WhatsApp OTP with regional rules, all tenant-configurable per persona within platform bounds"
links: []
rev: 3
syncHash: "247e8db2813705ac"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.1.1 Email/password, magic link, OTP

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> First-factor methods for people without SSO: passwords (15+ characters, breach-checked, Argon2id), browser-bound magic links, email, SMS and WhatsApp OTP with regional rules, all tenant-configurable per persona within platform bounds

<!-- section:purpose -->
## Purpose and scope

First-factor sign-in for people who do not use SSO: email + password, magic link, and one-time codes (OTP) by email or SMS. These methods matter most for parties (including unrepresented SEBI ODR investors and MSME claimants), counsel at firms without SSO, neutrals and transcribers. The control protects accounts from takeover while staying usable for people who sign in rarely, often on mobile, and sometimes with assistive technology ([[PKG-accessible-authentication-and]]).

Part of `@nomology/auth`. Session issue and MFA are in [[PKG-mfa-session-management-device]].

<!-- section:assets -->
## Protected assets

| Asset | Classification | Storage |
|---|---|---|
| Password hash (Argon2id, per-user salt) | Secret | `auth.credential_password` (tenant-independent, regional) |
| Magic link token | Secret, single use | Only SHA-256 hash stored in `auth.login_challenge` |
| OTP code | Secret, single use | Hash with per-challenge salt in `auth.login_challenge` |
| Email address and phone number | Personal | `auth.user`, `auth.user_phone` |
| Breached-password check result | Internal | Not stored, computed at set time |

<!-- section:actors -->
## Actors and roles

| Actor | Methods allowed by default (tenant can restrict through `auth.methods.*`) |
|---|---|
| `party` (incl. unrepresented) | Magic link, email OTP, passkey; SMS OTP in region `in` (DLT-registered template required, see [[PKG-notification-copy]]); WhatsApp OTP where enabled (assumption, India only); optional password |
| `counsel` | Password or passkey (+ MFA per tenant policy); magic link and email OTP as fallback |
| `neutral`, `transcriber` | Password or passkey + MFA (required) |
| `observer`, `expert`, `witness`, `interpreter` | Magic link, email OTP |
| `secretariat` and tenant administrative roles | Password + MFA or passkey, only where SSO is not enforced for their domain; break-glass admins keep a passkey |
| Nomology staff | Not allowed (workforce SSO only) |
| Attacker | Any public endpoint: sign-in, request OTP, request magic link, reset password |

Roles are acquired through invitation ([[PKG-user-provisioning-scim]]) or verified self-registration on the public filing entry ([[APP-public-and-sign-in-surfaces]]); external people are described in [[PKG-external-party-identity]].

<!-- section:matrix -->
## Permission matrix

| Operation | Unauthenticated | Signed-in user (own) | `user_admin` / `security_admin` | `platform_support` |
|---|---|---|---|---|
| Request magic link / email OTP for an email | ✓ (rate limited; same response if unknown) | — | ✗ | ✗ |
| Request SMS or WhatsApp OTP | ✓ only for a phone already verified on the account and in `auth.methods.sms_otp.allowed_countries` | ✓ | ✗ | ✗ |
| Verify OTP / consume magic link | ✓ (same browser that requested, see AUTH-PW-6) | — | ✗ | ✗ |
| Sign in with password | ✓ where the method is allowed for persona and tenant | — | ✗ | ✗ |
| Set or change password | ✗ | ✓ with current password or fresh step-up | ✗ (cannot see or set passwords) | ✗ |
| Start password reset | ✓ (same response if unknown) | ✓ | Can trigger a reset email to a member (`user:update`), never set the password | ✗ |
| Change email address | ✗ | ✓ with step-up, verification of new address, notice to old address | ✗ (only via assisted recovery with identity re-proof) | ✗ |
| Enable or disable a method for the tenant | ✗ | ✗ | `security_admin` only (`settings.security:write`) within platform floor | ✗ |

<!-- section:policy -->
## Policy model

Tunable values are `auth.password.*`, `auth.otp.*`, `auth.magic_link.*`, `auth.methods.*` and `auth.sms.daily_budget` in [[PKG-settings-security-and-identity]]; the numbers below are platform defaults and bounds.

- **Passwords**: minimum 15 characters for every persona (`auth.password.min_length`, 15–64). NIST SP 800-63B-4 sets 15 for a password used as the only factor and 8 when it is part of MFA, and asks verifiers to permit at least 64 [R3]; we use one floor because parties and counsel may sign in without MFA. Maximum 128; all printable Unicode allowed, normalised with NFKC; no composition rules; checked against a breached-password corpus (locked `auth.password.breach_check = required`; k-anonymity service or offline corpus per region is an open question); no periodic expiry (NIST forbids periodic change requirements [R3]); change forced only on evidence of compromise. Tenants can switch passwords off per persona; for parties that is the SEBI ODR and court blueprint default.
- **Hashing**: Argon2id with at least m=19 MiB, t=2, p=1 per OWASP [R4]; parameters stored with each hash and upgraded on next sign-in.
- **Magic link**: 32 bytes random, valid `auth.magic_link.ttl_minutes` (default 15), single use, bound to the requesting browser via a `__Host-login_challenge` cookie; opening it on a different device shows a 6-digit code to type on the original device instead of signing in the other device.
- **OTP (email, SMS, WhatsApp)**: 6 digits, valid `auth.otp.ttl_seconds` (default 600), at most `auth.otp.max_attempts` per challenge (default 5), at most 5 challenges per hour per account; resending invalidates the previous code. Users may request a new code after `auth.otp.resend_cooldown_seconds` (default 30); no other time limit within the validity window (WCAG 2.2.1, see [[PKG-accessible-authentication-and]]).
- **Channel rules by region**: SMS OTP is restricted by NIST [R3] and allowed only for `party` by default in region `in` (DLT templates), off in `sg` and `us` unless enabled; never for administrative roles. WhatsApp OTP (assumption) is an India-only option behind `auth.methods.whatsapp_otp.enabled`, using an approved authentication template through the provider in [[INT-messaging-providers]]. A per-tenant daily budget (`auth.sms.daily_budget`) and per-country allow-list limit SMS pumping.
- **Throttling**: per account (exponential backoff after 5 failures: 1, 2, 4 ... minutes, max 30), per IP and per /24 or /48 (sliding window via [[PKG-input-sanitisation-csrf-rate]]); no permanent lockout. This stays well inside the NIST ceiling of 100 consecutive failures [R3].
- OTP and magic-link messages are sent through [[PKG-notifications]] with class `auth` (cannot be suppressed by preferences, never in digests, no tracking pixels or click tracking).

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|---|
| T1 | S | Credential stuffing | Breached-password check, throttling, MFA policy, anomaly alerts on failure spikes per tenant | Low |
| T2 | S | Magic link forwarded or intercepted (email scanners pre-fetch links) | Link opens a confirmation page (no sign-in on GET), browser binding, single use, 15 min | Low |
| T3 | S | OTP brute force | 5 attempts per challenge, 6 digits, challenge rate limit | Very low |
| T4 | S | SIM swap for SMS OTP | SMS OTP only as first factor for parties, never as the only factor for staff, neutrals or admins; NIST treats PSTN as restricted [R3] | Medium for parties |
| T5 | I | Enumeration via reset, OTP request or registration | Identical responses and timing; registration continues by email ("check your inbox") | Low |
| T6 | D | SMS pumping fraud (toll fraud) | SMS OTP only to verified numbers, per-tenant SMS budget and per-country allow-list | Low |
| T7 | T | Password reset token theft | Token single use, 30 min, invalidated on password change; all sessions revoked after reset | Low |
| T8 | E | Account pre-hijacking (attacker registers victim email first) | Email verification required before any case access; unverified accounts expire after 7 days | Low |

<!-- section:failure -->
## Denial behaviour

All first-factor failures show the same message and return HTTP 200 with a generic body on request endpoints (OTP, magic link, reset) and 401 with `auth/invalid-credentials` on verify endpoints. Throttled users see when they can try again, without saying whether the account exists. Every failure is logged with reason code and hashed IP; codes, tokens and passwords are never logged.

<!-- section:requirements -->
## Security requirements

ASVS references are to OWASP ASVS **5.0** at section level [R1][R2]; requirement-level IDs are filled in when text is checked against the 5.0.0 release.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| AUTH-PW-1 | Passwords shall be at least 15 characters (or the tenant's higher minimum), allow at least 64, accept all printable Unicode and spaces, and impose no composition rules. | V6.2 |
| AUTH-PW-2 | New passwords shall be checked against a breached-password list and rejected if found. | V6.2 |
| AUTH-PW-3 | Passwords shall be stored with Argon2id at or above OWASP minimum parameters. | V11.4 |
| AUTH-PW-4 | OTPs shall be 6 digits, single use, valid for the configured time (maximum 10 minutes), with at most the configured number of verification attempts (maximum 5). | V6.6 |
| AUTH-PW-5 | Magic links shall be single use, valid for the configured time (maximum 15 minutes) and never sign in on an HTTP GET. | V6.6 |
| AUTH-PW-6 | Magic links and OTPs shall complete sign-in only in the browser that requested them. | V6.6 |
| AUTH-PW-7 | Sign-in, OTP, magic-link and reset endpoints shall return indistinguishable responses for existing and non-existing accounts. | V6.3 |
| AUTH-PW-8 | Repeated failures shall be throttled per account and per network without permanent lockout. | V6.3, V2.4 |
| AUTH-PW-9 | A password reset shall revoke all of the user's sessions in every tenant of the region. | V6.4, V7.4 |
| AUTH-PW-10 | Paste and password managers shall work in every credential field. | V6.2 |
| AUTH-PW-11 | SMS and WhatsApp OTP shall be sent only to verified numbers in allowed countries, within the tenant's daily budget, and never serve as the only second factor for a persona that requires MFA. | V6.6 |
| AUTH-PW-12 | Enabling or disabling a method for a persona shall take effect at the next sign-in without redeployment. | — |

<!-- section:verification -->
## Verification

- Unit: hashing parameters, OTP validation window, attempt counters, token single-use.
- Integration: response-equality test for known vs unknown emails (status, body, and timing within 50 ms median difference over 200 samples).
- E2E (Playwright): magic link flow including the cross-device code path; OTP resend invalidating previous code; password managers (autocomplete attributes present).
- Pen test: enumeration, rate-limit bypass via IP rotation, link pre-fetch behaviour.

<!-- section:questions -->
## Open questions

- [ ] Breached-password check: external k-anonymity service (data leaves region as a 5-character hash prefix) or offline corpus per region? Owner: security.
- [ ] Is SMS OTP needed outside India at launch? Affects SMS provider choice per region in [[INT-messaging-providers]]. Owner: product.
- [ ] WhatsApp OTP for parties in India — acceptable as first factor, and under which provider terms? Owner: product, security, legal.
- Answered in this overhaul: tenants can disable password per persona (including entirely for parties) through `auth.methods.password.personas`, provided another method without a cognitive function test remains ([[PKG-settings-security-and-identity#validation]]).

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Credentials (password hashes) are region-level and belong to the user, not a tenant, so a password reset affects the user's sign-in in every tenant of the region (and revokes all sessions there). Which methods are offered is decided per tenant host. OTP and link challenges record the tenant host they were requested on and complete only there.

<!-- check:enforcement -->
### Enforcement points and bypass paths

All first-factor endpoints are Route Handlers in the `(public)` route group behind the shared rate limiter and CSRF origin check; there is no other path that creates a session. Password set and change happen only through the auth package API; tenant admins have no endpoint that sets a password. After the first factor, the authentication policy evaluator decides whether MFA is needed ([[PKG-authentication-policies]]).

<!-- check:lifecycle -->
### Grant lifecycle and privileged access

Passwords never expire on a schedule; a forced change happens only on evidence of compromise (breach-corpus hit at sign-in, admin-triggered reset email after an incident). A reset revokes all sessions in the region. Phone numbers and emails are re-verified when changed. Accounts that never complete email verification expire after 7 days; dormant external accounts follow [[PKG-external-party-identity]].

<!-- check:resilience -->
### Failure modes and secrets

If the email, SMS or WhatsApp provider is down, OTP and magic-link requests return the same generic response and the failure is retried by the notification queue; users can switch to another allowed method (passkey works without any provider). Hashing runs in a worker thread pool; if the pool is saturated, sign-in returns 503 rather than weakening parameters.

<!-- check:residency -->
### Data residency

Password hashes, challenges and sign-in events are stored in the regional database. OTP and magic-link messages are sent through the region's providers ([[INT-messaging-providers]]); the message contains only the code or link and the tenant name.

<!-- check:audit -->
### Audit trail

Audited: password set, change and reset; OTP and magic-link issue (channel, not the code); successful and failed sign-in with method and reason code; email and phone changes (with notice to the old contact); method enablement changes by tenant admins (`admin.settings.published`). Events carry hashed IP and session ID.

<!-- check:observability -->
### Detection and alerting

Alerts: failed sign-ins per tenant above 5× the 7-day baseline in 15 minutes; OTP requests for more than 50 distinct accounts from one IP in 10 minutes; SMS spend per tenant above daily budget; SMS to a new country spike. Routed to the security on-call ([[OBS-security-events]], [[OBS-alerting]]).

<!-- check:compliance -->
### Framework and legal mapping

ISO 27001:2022 Annex A 5.17 (authentication information) and 8.5 (secure authentication) [R5]; SOC 2 CC6.1 [R6]; NIST SP 800-63B-4 password and OTP rules followed where stated [R3]. Evidence: password policy configuration, breach-check logs (counts only), throttling configuration, enumeration test results.

<!-- check:testing -->
### Verification and testing

Negative tests for each matrix row (tenant admin cannot set passwords; SMS OTP refused to unverified numbers and to countries outside the allow-list; magic link refused in another browser; reset revokes sessions; disabling a method hides it at next sign-in) run in CI against real Postgres and Redis.

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
    "body": "NIST",
    "id": "R3",
    "ident": "SP 800-63B-4",
    "kind": "standard",
    "title": "NIST SP 800-63B-4 Digital Identity Guidelines: Authentication and Authenticator Management",
    "url": "https://pages.nist.gov/800-63-4/sp800-63b.html",
    "version": "800-63-4 (final, July 2025)"
  },
  {
    "body": "OWASP",
    "excerpt": "Use Argon2id with a minimum configuration of 19 MiB of memory, an iteration count of 2, and 1 degree of parallelism.",
    "id": "R4",
    "ident": "Cheat Sheet Series",
    "kind": "standard",
    "title": "OWASP Password Storage Cheat Sheet",
    "url": "https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html"
  },
  {
    "body": "ISO/IEC",
    "id": "R5",
    "ident": "27001",
    "kind": "standard",
    "title": "ISO/IEC 27001:2022 Information security management systems",
    "url": "https://www.iso.org/standard/27001",
    "version": "2022"
  },
  {
    "body": "AICPA",
    "id": "R6",
    "ident": "Trust Services Criteria",
    "kind": "standard",
    "title": "2017 Trust Services Criteria (with revised points of focus, 2022)",
    "url": "https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022",
    "version": "2017 (revised points of focus 2022)"
  }
]
```

<!-- end -->
