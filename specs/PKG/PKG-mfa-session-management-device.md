---
id: "PKG-mfa-session-management-device"
title: "MFA, session management, device management"
parent: "PKG-authentication"
order: 3
type: "feature"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "Passkeys (synced and device-bound, passwordless or second factor), TOTP, recovery, step-up mechanics, server-side sessions with per-persona bounds, policy re-evaluation, trusted and managed devices, and fast revocation"
links: []
rev: 3
syncHash: "61b050afa31de191"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.1.3 MFA, session management, device management

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Passkeys (synced and device-bound, passwordless or second factor), TOTP, recovery, step-up mechanics, server-side sessions with per-persona bounds, policy re-evaluation, trusted and managed devices, and fast revocation

<!-- section:purpose -->
## Purpose and scope

Passkeys and other WebAuthn authenticators (as first factor or second factor), TOTP apps, recovery codes, email OTP as a second step for parties, step-up mechanics before consequential actions, server-side session management, trusted and managed devices, and the user's own view of their signed-in devices. Protects accounts after the first factor and makes revocation fast and visible.

Part of `@nomology/auth`. Session cookies and checks are used by every route group, Server Action and tRPC procedure. **Which** factor strength a persona, role or action needs is decided by [[PKG-authentication-policies]]; the tunable values (allowed factors, session lengths per persona, trusted-device period, step-up window) are `auth.mfa.*`, `auth.passkey.*`, `auth.session.*` and `auth.step_up.*` in [[PKG-settings-security-and-identity]]. This node owns how each mechanism works.

<!-- section:assets -->
## Protected assets

| Asset | Classification | Storage |
|---|---|---|
| WebAuthn credential (public key, credential ID, sign count, AAGUID) | Confidential | `auth.mfa_factor` |
| TOTP secret | Secret | `auth.mfa_factor.secret_ciphertext`, encrypted with [[PKG-encryption-utilities-key]] (`purpose: 'totp'`) |
| Recovery codes (10 × 10 characters) | Secret | Argon2id hashes only |
| Session record: hashed session ID, user, tenant, persona, `amr`, `acr`, created, last seen, expiry, device ID | Confidential | `auth.session` (regional Postgres), hot copy in Redis |
| Device record: label (browser + OS), first seen, last seen, approximate location (country) | Personal | `auth.device` |
| Trusted-device token (skip MFA for N days) | Secret | Hash in `auth.device` |

<!-- section:actors -->
## Actors and roles

| Actor | MFA requirement (platform floor) | Idle timeout default (tenant range) | Absolute lifetime default (range) |
|---|---|---|---|
| Nomology staff (`platform_*`, `regional_ops`) | Device-bound WebAuthn via workforce IdP (`aal3`) | 15 min (fixed) | 8 h (fixed) |
| Tenant administrative roles (`tenant_owner`, `security_admin`, `tenant_admin`, `user_admin`, `workflow_designer`, `integration_admin`, `content_admin`, `billing_admin`, `ai_admin`, `auditor`, `unit_admin`) | Required; phishing-resistant for roles in `auth.mfa.phishing_resistant_roles` | 15 min (5–30) | 8 h (1–8) |
| `secretariat` | Required (or IdP-asserted MFA) | 30 min (5–60) | 12 h (1–12) |
| `neutral` | Required | 30 min (5–60) | 12 h (1–12) |
| `transcriber` | Required | 60 min (5–120; long editing sessions — a documented deviation from the 1-hour AAL2 inactivity guidance, offset by step-up before delivery and certification) | 12 h (1–12) |
| `counsel` | Tenant setting (default required, 7-day enrolment grace) | 30 min (5–60) | 12 h (1–12) |
| `party`, `observer` | Optional unless tenant requires | 30 min (5–120) | 12 h (1–12) |

The 12-hour ceiling matches the NIST SP 800-63B-4 reauthentication limit for AAL3 and is stricter than its AAL2 guidance of 24 hours overall and 1 hour inactivity [R3]. Tenant contracts can raise requirements but not lower them.

<!-- section:matrix -->
## Permission matrix

Permission keys proposed for [[PKG-permission-catalogue]].

| Action | Permission | Self | `user_admin` | `security_admin` | `tenant_owner` | `platform_security` | `platform_support` (under grant) |
|---|---|---|---|---|---|---|---|
| Enrol passkey / security key / TOTP | `user.self:update` | ✓ (fresh sign-in within 5 min) | ✗ | ✗ | ✗ | ✗ | ✗ |
| Remove own factor | `user.self:update` | ✓ with step-up by another factor; last factor cannot be removed if MFA is required | ✗ | ✗ | ✗ | ✗ | ✗ |
| Generate new recovery codes | `user.self:update` | ✓ with step-up | ✗ | ✗ | ✗ | ✗ | ✗ |
| Reset a member's factors (assisted recovery) | `user.mfa:update` | ✗ | ✓ non-administrative members, after re-proof, reason, member notified | ✓ incl. administrative members; second approver for `tenant_owner` and `security_admin` targets | ✓ | ✓ for tenant owners, two-person | ✗ |
| List own sessions and devices | `user.self:read` | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Revoke own session / device | `user.self:update` | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| List a member's sessions and devices | `user.session:list` | — | ✓ | ✓ | ✓ | ✓ | ✗ |
| Revoke all sessions of a member | `user.session:delete` | — | ✓ | ✓ | ✓ | ✓ | ✗ |
| Mark device trusted | `user.self:update` | ✓ if allowed (not for administrative roles) | ✗ | ✗ | ✗ | ✗ | ✗ |
| Configure MFA, passkey and session settings | `settings.security:write` | ✗ | ✗ | ✓ within platform floor | ✓ | platform floor | ✗ |
| View factor coverage report | `auth.policy:read` | ✗ | ✓ | ✓ | ✓ | ✓ | ✗ |

No administrator can enrol a factor for someone else, see a TOTP secret or a recovery code, or extend another person's session.

<!-- section:policy -->
## Policy model

**Passkeys (WebAuthn Level 3 [R4])**
- Registration: `residentKey: 'required'` for passwordless (`auth.methods.passkey.first_factor`), otherwise `preferred`; `userVerification` from `auth.passkey.user_verification` (default `required`; always `required` for administrative roles); attestation `none` by default, `direct` when `auth.passkey.aaguid_allow_list` is set or the role is in `auth.passkey.device_bound_roles`.
- **Synced vs device-bound**: the backup-eligible (`BE`) and backup-state (`BS`) flags are stored with each credential. Synced passkeys count as `aal2-phr`; device-bound credentials with an allowed AAGUID count as `aal3`. Roles in `auth.passkey.device_bound_roles` cannot register a credential with `BE = 1`. NIST SP 800-63B-4 permits syncable authenticators up to AAL2 and forbids them at AAL3 [R3]; enterprise passkey deployment guidance from the FIDO Alliance describes the same split [R5].
- Relying party ID: the tenant host (`tenantA.example`); passkeys therefore do not work across tenant hosts, which is intended. Assumption: WebAuthn related-origin requests are not used, to keep tenant isolation simple.
- Sign count and `BS` changes are recorded; a sign-count regression on a device-bound credential raises a security event and requires step-up with another factor.
- Passwordless sign-in: discoverable credential with conditional UI on the email field; if the user has no passkey, the normal method choice appears.

**TOTP (RFC 6238 [R6])**: 30-second step, ±1 step tolerance, replay of a used step rejected; secret encrypted with [[PKG-encryption-utilities-key]] (`purpose: 'totp'`).

**Email or SMS OTP as second step**: allowed only where `auth.mfa.allowed_factors` lists it and never for administrative roles; SMS never the only second factor for any persona that requires MFA.

**Recovery**: 10 single-use recovery codes (Argon2id hashes) when `auth.mfa.recovery_codes_enabled`; self-service recovery methods from `auth.recovery.self_service_methods`; assisted recovery by `user_admin` / `security_admin` only after identity re-proof (video check against the verified name or the tenant's documented process), with the user notified at all known contacts; a new factor added by assisted recovery cannot satisfy step-up for consequential actions for `auth.mfa.reset_cooldown_hours`.

**Sessions**
- Cookie `__Host-sid`: opaque 256-bit random, `HttpOnly; Secure; SameSite=Lax; Path=/`; server stores SHA-256 of the ID; one cookie per tenant host.
- Per-request check: Redis `sess:{region}:{hash}` (TTL = idle timeout), fallback Postgres; compares `tenantId` with the host tenant, `revocationVersion` of user, membership and tenant, and the tenant's `auth_policy_epoch` (re-evaluation on change, [[PKG-authentication-policies#policy]]).
- Rotation on sign-in, step-up, persona switch, tenant switch and privilege change.
- Concurrency: `auth.session.max_concurrent` per persona; the oldest session ends when exceeded, with a notice.
- Network change: `auth.session.network_change_action` (`none`, `step_up`, `revoke`) when the client IP leaves the network zone or country of session creation.

**Step-up**: `requireStepUp(actionClass)` checks `lastStepUpAt` within `auth.step_up.window_minutes` and that the factor used meets `auth.step_up.strength_by_action_class`; satisfied by a passkey (preferred), TOTP or, for parties, email OTP where the class allows.

**Devices**
- Device record per browser profile (label from user agent, first and last seen, country), shown to the user with "Sign out this device".
- **Trusted device** (skip MFA prompt at sign-in for `auth.session.trusted_device_days`; never for administrative roles or staff): hashed token in `__Host-tdev`, bound to the user and tenant host, revoked with the device.
- **Managed device** (for `auth.device.managed_required_roles`): asserted only by a signed claim from the tenant's verified SSO connection or by a client certificate chaining to a tenant-uploaded CA (`auth.device.managed_signal`); recorded as `deviceTrust = 'managed'` on the session. We do not install agents or inspect devices.
- New-device notice email when `auth.risk.new_device_notice`.

**Revocation**: user, membership and tenant each carry a `revocation_version`; bumping it invalidates matching sessions within 60 seconds (Redis pub/sub plus version check).

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|---|
| T1 | S | Real-time phishing proxy steals session after MFA | Passkeys are origin-bound; phishing-resistant required for listed roles and staff; impossible-travel step-up | Medium for TOTP users |
| T2 | S | MFA reset social engineering | Reset only by authorised admins after identity re-proof, notification to user at all contacts, cooldown before the new factor can approve consequential actions | Low |
| T3 | T | Session fixation | Rotation on sign-in and step-up; IDs never accepted from URL | Very low |
| T4 | I | Session ID leakage in logs | IDs hashed before logging; only session record ID (UUID) appears in audit | Low |
| T5 | E | Stale session after role removal | Revocation versions and policy epoch checked on every request | Low |
| T6 | R | "It wasn't me" for an award signature | Step-up with passkey or TOTP recorded in audit (`amr`, `acr`, device ID, policy version) | Low |
| T7 | D | Push/OTP fatigue attacks | No push approvals; OTP requests rate limited | Low |
| T8 | S | Synced passkey compromised through the user's cloud account | Synced passkeys capped at `aal2-phr`; device-bound required where the tenant lists roles; new-device notices | Medium |
| T9 | S | Forged managed-device claim | Accepted only from verified connections with signed assertions or tenant CA certificates | Medium (tenant IdP hygiene) |

<!-- section:failure -->
## Denial behaviour

- Expired or revoked session: 401 and redirect to sign-in with a same-origin return URL; drafts kept client-side.
- Step-up needed: problem type `auth/step-up-required` with `required_acr`; UI opens the MFA dialog and retries the action after success (idempotency key reused).
- MFA failures: generic "That code did not work" with remaining attempts not shown; 5 failures in 15 minutes trigger backoff and a notification to the user.

<!-- section:requirements -->
## Security requirements

ASVS references are to OWASP ASVS **5.0** at section level [R1][R2]; requirement-level IDs are filled in when text is checked against the 5.0.0 release.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| SESS-1 | Session IDs shall be 256-bit random values, sent only in `__Host-` cookies with HttpOnly, Secure and SameSite=Lax, and stored only as hashes. | V7.2, V3.3 |
| SESS-2 | Sessions shall expire after the persona's idle timeout and absolute lifetime as resolved from `auth.session.*`. | V7.3 |
| SESS-3 | Session IDs shall rotate on sign-in, step-up, tenant or persona switch and privilege change. | V7.2 |
| SESS-4 | When a user, membership or tenant is revoked or suspended, the platform shall reject that scope's sessions within 60 seconds. | V7.4 |
| SESS-5 | Users shall be able to list and revoke their own sessions and devices. | V7.4 |
| SESS-6 | When the tenant's authentication policy changes, each session shall be re-evaluated on its next request. | V7.4 |
| MFA-1 | Users in personas that require MFA shall not complete sign-in without a second factor (or a passkey with user verification). | V6.5 |
| MFA-2 | Consequential actions shall require a successful factor of the required strength within the step-up window. | V7.5 |
| MFA-3 | TOTP codes shall not be accepted twice within their validity window. | V6.5 |
| MFA-4 | Resetting another user's factors shall require identity re-proof, a reason, notification to the user and audit; resets of `tenant_owner` or `security_admin` shall need a second approver. | V6.4 |
| MFA-5 | A passkey registered with the backup-eligible flag shall not satisfy `aal3`, and roles requiring device-bound keys shall be unable to register one. | V6.5 |
| MFA-6 | Every persona that requires MFA shall be able to enrol at least one phishing-resistant authenticator. | V6.5 |
| MFA-7 | A factor added through assisted recovery shall not satisfy step-up for consequential actions until the configured cooldown has passed. | V6.4 |
| DEV-1 | Managed-device status shall be accepted only from a signed claim of a verified tenant SSO connection or a client certificate chaining to a tenant-registered CA. | V6.8 |
| DEV-2 | Trusted-device tokens shall never apply to administrative roles or Nomology staff, and shall expire within 30 days. | V7.3 |

<!-- section:verification -->
## Verification

- Integration tests for rotation, idle and absolute expiry (fake clock), revocation latency (assert rejection ≤ 60 s after bump), cookie attributes.
- WebAuthn tests with a virtual authenticator in Playwright; TOTP replay test.
- Route-catalogue test: every consequential action route rejects a session whose last step-up is older than 5 minutes.
- Pen test: session management and MFA bypass cases.

<!-- section:questions -->
## Open questions

- [ ] Is identity re-proof for assisted MFA reset a tenant process (secretariat verifies the neutral by video) or a Nomology support service for small tenants? Owner: operations.
- [ ] Should the platform offer WebAuthn related origins so one passkey works across a tenant's several custom hostnames? Proposed: no in phase 1. Owner: security.
- [ ] AAGUID metadata: use the FIDO Metadata Service to show authenticator names and certification levels? Owner: security.
- Answered in this overhaul: passkeys are offered as a first factor (passwordless) for all personas when `auth.methods.passkey.first_factor` is on; IP allow-listing and device restrictions are specified in [[PKG-authentication-policies]].

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Cookies are host-only per tenant host and passkeys are bound to the tenant host as relying party ID; each session record carries one tenant and is checked against the host tenant on every request. Tenant switch issues a new session and re-applies that tenant's policy. Session and factor tables are regional; membership revocation versions are per tenant.

<!-- check:enforcement -->
### Enforcement points and bypass paths

Every route group's middleware and every tRPC procedure, Server Action and REST handler runs the same session check; `requireStepUp(actionClass)` is the only way consequential operations proceed and is enforced by a lint rule and a generated coverage test. Hearing join tokens are issued only to sessions that pass the check ([[APP-hearing-room-in-browser]]).

<!-- check:lifecycle -->
### Grant lifecycle and privileged access

Revocation versions on user, membership and tenant take effect within 60 seconds; policy epoch changes re-evaluate sessions. Assisted resets need re-proof, a reason and (for owners and security admins) a second approver; a cooldown limits what a new factor can do. Trusted-device tokens expire within 30 days and are revoked with the device.

<!-- check:resilience -->
### Failure modes and secrets

If Redis is down, session checks fall back to Postgres; if Postgres is down, requests fail closed. TOTP secrets are decrypted through the crypto package with a regional KMS key; if KMS is unavailable, TOTP verification fails closed and passkeys still work (public keys need no decryption).

<!-- check:residency -->
### Data residency

Session, device, factor and step-up records are stored in the tenant's regional Postgres and Redis; TOTP secrets are encrypted with a regional KMS key; passkey public keys never leave the region. New-device notices go through the regional email provider.

<!-- check:audit -->
### Audit trail

Audited: factor enrol, remove, reset (with reason, re-proof reference and approver); passkey flags (`BE`, `BS`, AAGUID) at registration; recovery code generation and use; step-up success and failure with action class; session creation (method, `acr`, device, policy version), revocation (by whom, reason); trusted-device grant and revoke; managed-device assertion source.

<!-- check:observability -->
### Detection and alerting

Signals: step-up failure rate per tenant, recovery-code use (alert on any use by an administrative role), assisted resets per tenant per day (alert above 3), sessions from more than 3 countries per user per day (impossible-travel step-up and alert), sign-count regression on device-bound keys.

<!-- check:compliance -->
### Framework and legal mapping

ISO 27001:2022 Annex A 8.5 (secure authentication), 5.17 (authentication information) and 8.1 (user endpoint devices, for managed-device rules) [R7]; SOC 2 CC6.1 [R8]; supports DPDP reasonable security safeguards. Evidence: MFA and phishing-resistant coverage per persona per tenant, session policy snapshot, revocation latency test results, reset logs.

<!-- check:testing -->
### Verification and testing

CI covers each matrix row with a negative test (admin cannot enrol a factor for someone else; `user_admin` cannot reset a `security_admin`; support cannot reset), session rotation and revocation timing with a fake clock, passkey flag handling with a Playwright virtual authenticator (backup-eligible credential refused for device-bound roles), TOTP replay, and step-up enforcement generated from the consequential action catalogue.

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
    "body": "W3C",
    "id": "R4",
    "ident": "WebAuthn Level 3",
    "kind": "standard",
    "title": "Web Authentication: An API for accessing Public Key Credentials Level 3",
    "url": "https://www.w3.org/TR/webauthn-3/"
  },
  {
    "body": "FIDO Alliance",
    "id": "R5",
    "ident": "White paper",
    "kind": "standard",
    "title": "FIDO Alliance: Deploying passkeys in the enterprise (introduction)",
    "url": "https://fidoalliance.org/white-paper-fido-deploying-passkeys-in-the-enterprise-introduction/"
  },
  {
    "body": "IETF",
    "id": "R6",
    "ident": "RFC 6238",
    "kind": "standard",
    "title": "TOTP: Time-Based One-Time Password Algorithm",
    "url": "https://www.rfc-editor.org/rfc/rfc6238"
  },
  {
    "body": "ISO/IEC",
    "id": "R7",
    "ident": "27001",
    "kind": "standard",
    "title": "ISO/IEC 27001:2022 Information security management systems",
    "url": "https://www.iso.org/standard/27001",
    "version": "2022"
  },
  {
    "body": "AICPA",
    "id": "R8",
    "ident": "Trust Services Criteria",
    "kind": "standard",
    "title": "2017 Trust Services Criteria (with revised points of focus, 2022)",
    "url": "https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022",
    "version": "2017 (revised points of focus 2022)"
  }
]
```

<!-- end -->
