---
id: "PKG-authentication"
title: "Authentication"
parent: "PKG"
order: 1
type: "capability"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "Parent of `@nomology/auth`: identity model, method catalogue (password, magic link, OTP, passkeys, TOTP, SAML, OIDC, social and government IdPs), assurance levels and the Principal contract; children cover each mechanism, tenant policies, provisioning, external identity and API credentials"
links: []
rev: 3
syncHash: "37fb62bc120b9fd3"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.1 Authentication

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Parent of `@nomology/auth`: identity model, method catalogue (password, magic link, OTP, passkeys, TOTP, SAML, OIDC, social and government IdPs), assurance levels and the Principal contract; children cover each mechanism, tenant policies, provisioning, external identity and API credentials

<!-- section:purpose -->
## Purpose and scope

`@nomology/auth` (`packages/auth`) establishes who a person or system is, and keeps that knowledge trustworthy for the life of a session. It protects every persona surface (party and counsel portal, neutral workspace, secretariat console, transcriber workspace, tenant admin and platform admin consoles) and the public, admin and aggregator APIs.

This node is the parent: it sets the identity model, the **method catalogue** a tenant can configure, the assurance vocabulary (`acr`) and the `Principal` contract. Detail lives in the children:

| Child | Owns |
|---|---|
| [[PKG-email-password-magic-link-otp]] | Passwords, magic links, email / SMS / WhatsApp one-time codes |
| [[PKG-sso-saml-oidc-per-tenant]] | Tenant SAML and OIDC connections, social and government IdPs, attribute and group mapping; child [[PKG-domain-verification]] for domains and home-realm discovery |
| [[PKG-mfa-session-management-device]] | Passkeys and other WebAuthn authenticators, TOTP, recovery, sessions, devices |
| [[PKG-authentication-policies]] | Tenant rules: which strength per persona, role, unit, network, device and action class; step-up; session bounds |
| [[PKG-user-provisioning-scim]] | Invitations, bulk import, SCIM 2.0, JIT, auto-join, deprovisioning and lifecycle |
| [[PKG-external-party-identity]] | Parties, counsel and others outside the directory; identity verification levels; representation |
| [[PKG-api-clients-and-keys]] | API clients, keys, OAuth clients and apps |
| [[PKG-accessible-authentication-and]] | WCAG 3.3.8, no puzzle CAPTCHAs, accessible alternatives to liveness, guardians |

Every tunable value is a setting in [[PKG-settings-security-and-identity]] (`auth.*`). The tenant admin screens are under `/admin/security/...` in [[APP-tenant-admin-console]]; user and access administration screens are in [[APP-user-and-access-admin]].

**Relies on this control:** authorisation ([[PKG-authorization]]) trusts the `Principal`; audit trail actor attribution ([[PKG-audit-trail]]); support access and impersonation ([[PKG-support-access-and-impersonation]]); every Server Action, tRPC procedure and REST handler.

<!-- section:assets -->
## Protected assets

| Asset | Classification ([[SEC-data-classification]]) | Why it matters |
|---|---|---|
| User identity record (email, phone, name, locale) | Personal | Account takeover gives access to case files |
| Credentials: password hashes, OTP secrets, WebAuthn public keys, recovery codes | Confidential (secret) | Direct takeover |
| Session records and cookies | Confidential (secret) | Bearer of authority |
| SSO connection config (IdP metadata, client secrets, signing certificates) | Confidential (secret) | Forged assertions sign anyone in |
| Tenant membership and persona of a session | Internal | Wrong tenant or persona = wrong data |
| Sign-in and MFA event history | Internal | Evidence, anomaly detection |
| Actions behind authentication: filing, award issue, payment, export | Legal effect | Need step-up and non-repudiation |

<!-- section:actors -->
## Actors and roles

| Actor (shared-model key) | Region / tenant scope | How the identity is established | Default methods (tenant can tighten) |
|---|---|---|---|
| `party` (claimant, respondent, SEBI ODR investor, MSME claimant) | One region; one or more tenants | Case invitation, public filing entry or aggregator-created case, then control of email or mobile ([[PKG-external-party-identity]]) | Magic link, email OTP, passkey; SMS OTP in India; password optional |
| `counsel` | One identity per region; many tenants | Case invitation or nomination by a party, plus representation approval; firm SSO where configured | Password or passkey + MFA (tenant default), or firm SSO |
| `neutral` | Many tenants | Invitation after empanelment ([[DOM-neutrals]]) | Passkey or password + MFA (required), or institution SSO |
| `secretariat` (case manager / registry) | One tenant | Staff invitation, SCIM or JIT ([[PKG-user-provisioning-scim]]) | Tenant SSO; otherwise passkey or password + MFA (required) |
| `transcriber` | Many tenants | Invitation | Passkey or password + MFA (required) |
| `observer`, `expert`, `witness`, `interpreter` | Case-scoped | Case invitation | Magic link, email OTP, passkey |
| Tenant administrative roles (`tenant_owner`, `tenant_admin`, `security_admin`, `user_admin`, `workflow_designer`, `integration_admin`, `content_admin`, `billing_admin`, `ai_admin`, `auditor`, `unit_admin`) | One tenant | Owner at onboarding ([[APP-tenant-onboarding-wizard]]); others by invitation or SCIM group mapping with maker-checker | SSO or passkey / password + MFA (required); phishing-resistant per `auth.mfa.phishing_resistant_roles` |
| Nomology staff (`platform_owner`, `platform_admin`, `platform_support`, `platform_security`, `platform_billing`, `regional_ops`) | Platform | Nomology workforce IdP only | Workforce SSO with device-bound WebAuthn (`aal3`) |
| `service_account` behind an API client; aggregator client (e.g. NSE) | One tenant, one region | API key or OAuth client credentials ([[PKG-api-clients-and-keys]]) | Hashed API key or `private_key_jwt` |
| `integration_connection` (SCIM, inbound connectors) | One tenant | Connection token ([[PKG-user-provisioning-scim]], [[INT-connections-admin]]) | Hashed bearer token |
| `ai_agent` | One tenant | Never signs in; acts with a delegated or own principal ([[PKG-non-human-principals]]) | — |
| System workloads (Temporal workers, BullMQ workers) | Region | Workload identity (IAM role / managed identity), never user sessions | — |

Identity model: a **user** is one record per region keyed by verified email; a **membership** links a user to a tenant (`kind` = `staff` or `external`) with personas and roles ([[MT-tenancy-and-identity-schema]]). A person active in two regions has two user records; the global tenant directory stores only routing data, not the identity ([[MT-data-residency-2]]).

<!-- section:matrix -->
## Permission matrix

Who may perform authentication-administration actions. ✓ allowed, ✗ denied, "own" only for themselves, "T" within own tenant. Detailed matrices are in each child node; permission keys are proposed for [[PKG-permission-catalogue]].

| Action | Permission | Party / counsel / neutral / transcriber / secretariat | `user_admin` | `security_admin` | `tenant_owner` | `tenant_admin` | `auditor` | `platform_support` | `platform_security` / `platform_admin` | API client |
|---|---|---|---|---|---|---|---|---|---|---|
| Sign in with an enabled method | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | workforce SSO | workforce SSO | ✗ |
| Manage own factors, passkeys, sessions, devices | `user.self:update` | own | own | own | own | own | own | own | own | ✗ |
| Invite, suspend, end members | `user:create`, `user:update`, `user:delete` | ✗ | T | T | T | T | ✗ | ✗ | ✓ (tenant owner bootstrap) | with `admin.users:write` |
| Reset another member's MFA | `user.mfa:update` | ✗ | T (non-admin members, after identity re-proof) | T (admins: second approver) | T | ✗ | ✗ | under grant, read-only: ✗ | ✓ for tenant owners, two-person | ✗ |
| Force sign-out of a member | `user.session:delete` | ✗ | T | T | T | T | ✗ | ✗ | ✓ | with `admin.users:write` |
| Configure SSO connections, domains | `auth.connection:update`, `auth.domain:create` | ✗ | ✗ | T | T | ✗ | ✗ | ✗ | ✓ (domain overrides, two-person) | ✗ |
| Author / approve / publish authentication policies | `auth.policy:update` / `:approve` / `:publish` | ✗ | ✗ | T | T | ✗ | ✗ | ✗ | platform floor | ✗ |
| Change `auth.*` settings | `settings.security:write` | ✗ | ✗ | T | T | read | read | ✗ | platform and region scopes | ✗ (with `admin.settings:write`, drafts only) |
| Configure SCIM, JIT, invitations policy | `auth.provisioning:configure` | ✗ | read | T | T | ✗ | ✗ | ✗ | ✓ | ✗ |
| Create API clients | `api_client:create` | ✗ | ✗ | T | T | ✗ | ✗ | ✗ | aggregator clients | ✗ |

API clients are also created by `integration_admin` (non-admin scopes; admin scopes go to approval), as specified in [[PKG-api-clients-and-keys#matrix]], which is authoritative.
| Read sign-in history | `auth.signin_event:list` | own | T | T | T | T | T | under grant | ✓ (`platform_security`) | with `audit:read` |

<!-- section:policy -->
## Policy model

**Method catalogue** (what a tenant can switch on; availability by region and plan in [[PKG-settings-security-and-identity]]):

| Method | Factor type | `amr` | Max assurance alone | Phishing-resistant | Owner node |
|---|---|---|---|---|---|
| Password | Knowledge | `pwd` | `aal1` | no | [[PKG-email-password-magic-link-otp]] |
| Magic link (email) | Possession of mailbox | `magic` | `aal1` | no | same |
| Email OTP | Possession of mailbox | `otp` (`email`) | `aal1` | no | same |
| SMS OTP (restricted per NIST [R5]) | Possession of phone number | `otp` (`sms`) | `aal1`; never the only second factor for staff | no | same |
| WhatsApp OTP (assumption, India only) | Possession of account | `otp` (`whatsapp`) | `aal1` | no | same |
| Passkey, synced (WebAuthn [R6]) | Possession + user verification | `webauthn` (`hwk`/`swk`, `user`) | `aal2-phr` | yes | [[PKG-mfa-session-management-device]] |
| Passkey or security key, device-bound, attested | Possession + user verification | `webauthn` | `aal3` | yes | same |
| TOTP app (RFC 6238) | Possession | `totp` | second factor → `aal2` | no | same |
| Recovery code | Knowledge (one time) | `recovery` | recovery only | no | same |
| Tenant SAML / OIDC SSO [R7] | Federated | `sso` (+ IdP `amr`) | as asserted and mapped by tenant | per IdP | [[PKG-sso-saml-oidc-per-tenant]] |
| Social IdP (Google, Microsoft consumer, Apple, LinkedIn) | Federated | `social` | `aal1` (IdP MFA not trusted) | no | same |
| Government login (Singpass, region `sg`; assumption) | Federated | `gov` | as mapped | per scheme | same |

**Assurance values** (`acr`): `aal1` (one factor), `aal2` (two factors, or IdP-asserted MFA), `aal2-phr` (two factors with a phishing-resistant one, or a passkey with user verification), `aal3` (device-bound, non-exportable key; Nomology staff and roles listed in `auth.passkey.device_bound_roles`). These follow the authenticator assurance levels of NIST SP 800-63B-4, which requires an AAL2 verifier to offer a phishing-resistant option and forbids syncable authenticators at AAL3 [R5].

**Evaluation order** (detail in [[PKG-authentication-policies#policy]]):
1. **Platform floor** (code): staff on workforce SSO with `aal3`; MFA for administrative roles, secretariat, neutrals and transcribers; session absolute lifetime ≤ 12 h (≤ 8 h for administrative roles); passwords per [[PKG-email-password-magic-link-otp]].
2. **Region overlay**: method availability (SMS, WhatsApp, government login), blocked countries.
3. **Tenant policy rules and `auth.*` settings**, strictest result wins; unit rules tighten only.
4. **Step-up** for consequential actions by action class (`consequential`, `financial`, `export`, `admin_security`), default window 5 minutes.

The result of authentication is a `Principal`:
```ts
interface Principal {
  kind: 'user' | 'service_account' | 'integration_connection' | 'ai_agent';
  userId?: string; principalId: string; tenantId: string; region: 'in' | 'sg' | 'us';
  membershipKind?: 'staff' | 'external';
  persona?: Persona; sessionId?: string;
  amr: ('pwd' | 'otp' | 'magic' | 'sso' | 'social' | 'gov' | 'totp' | 'webauthn' | 'recovery' | 'api_key' | 'pkjwt' | 'mtls')[];
  acr: 'aal1' | 'aal2' | 'aal2-phr' | 'aal3';
  authTime: Date; lastStepUpAt?: Date;
  deviceTrust?: 'unknown' | 'remembered' | 'managed';
  authPolicyVersion?: number;          // policy the session was last evaluated under
  ivl?: 'ivl0' | 'ivl1' | 'ivl2' | 'ivl3';   // external identity level in this tenant
  supportGrantId?: string; impersonatorId?: string; delegatedBy?: string; // ai_agent acting for a user
}
```
`acr` value `aal3` and fields `kind`, `membershipKind`, `deviceTrust`, `authPolicyVersion`, `ivl` and `delegatedBy` are additions in this overhaul; consumers that only check `acr >= 'aal2'` keep working because the comparison uses the ordered list above.

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat | Scenario | Mitigation | Residual risk |
|---|---|---|---|---|---|
| T1 | S | Credential stuffing | Leaked passwords tried against counsel accounts | Breached-password check, rate limits per account and IP, MFA for counsel by default, passkeys offered, alerts | Low |
| T2 | S | Phishing of OTP / magic link | Fake "hearing notice" email harvests OTP | Links only to verified tenant hosts, OTP bound to the requesting browser, phishing-resistant MFA required for admin roles | Medium for parties using magic links |
| T3 | S | Forged SSO assertion | Attacker with a self-hosted IdP claims a tenant domain | DNS domain verification per tenant ([[PKG-domain-verification]]), per-connection signing certs, assertion checks, no IdP-initiated SSO by default | Low |
| T4 | T | Session fixation / hijack | Stolen cookie reused | `__Host-` cookies, HttpOnly, Secure, SameSite=Lax, rotation on sign-in and step-up, network-change step-up per policy | Low |
| T5 | R | User denies filing | "I never submitted that" | Step-up before consequential actions, audit with `amr`, `acr`, policy version and session ID | Low |
| T6 | I | Account enumeration | Sign-in, reset or HRD reveals registered emails | Identical responses and timing; HRD only reveals tenant-verified domains, which are not secret | Low |
| T7 | D | Lockout as attack | Attacker locks the tribunal out before a hearing | Throttling with backoff rather than hard lockout; passkey and SSO paths stay available | Low |
| T8 | E | Wrong tenant on session | Counsel signed in to tenant A acts in tenant B | Session bound to one tenant host; tenant switch re-validates membership and policy; tenant ID from session, cross-checked with host | Low |
| T9 | E | Support staff impersonation abuse | Staff "view as" a neutral to read an award draft | Impersonation only via tenant-approved grant, read-only, audited in tenant's stream ([[PKG-support-access-and-impersonation]]) | Low |
| T10 | E | Admin weakens authentication to enable an attack | Compromised `security_admin` disables MFA for secretariat | Maker-checker for weakening, phishing-resistant step-up, owners notified, platform floor in code ([[PKG-authentication-policies]]) | Low |
| T11 | S | Stranger joins a case by forwarded invitation | Invitation link forwarded to opposing party | Invitation bound to invited email, single use ([[PKG-external-party-identity]]) | Low |
| T12 | E | Leaked API key or SCIM token | Key committed to a public repository | Hashed, expiring, IP-restricted credentials, secret scanning and instant revoke ([[PKG-api-clients-and-keys]]) | Medium without IP allow-list |

<!-- section:failure -->
## Denial behaviour

- Failed sign-in: one generic message ("The email or password is not correct, or the account cannot sign in with this method") with the same status and similar timing for unknown accounts. Copy comes from [[APP-error-message-catalogue]].
- Session expired: redirect to sign-in with return URL (same-origin only); unsaved form drafts are kept client-side by the form components.
- Step-up required: `401` with problem type `auth/step-up-required` ([[APP-api-error-catalogue-problem]]) and the required `acr`; UI shows the MFA prompt inline.
- Logged: every failure with reason code (`bad_credentials`, `mfa_failed`, `locked_throttled`, `method_not_allowed`, `sso_assertion_invalid`), hashed IP, user agent family; never the submitted password or OTP.

<!-- section:requirements -->
## Security requirements

ASVS references are to OWASP ASVS **5.0** at section level [R1][R2]; requirement-level IDs are filled in when text is checked against the 5.0.0 release.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| AUTH-FR-1 | The platform shall resolve the tenant from the request host before authentication, and a session shall be valid only for the tenant and region it was created in. | V7.2, V8.2 |
| AUTH-FR-2 | Sign-in responses shall not reveal whether an account exists. | V6.3 |
| AUTH-FR-3 | Nomology staff, tenant administrative roles, secretariat, neutrals and transcribers shall be required to complete MFA at sign-in. | V6.5 |
| AUTH-FR-4 | Consequential actions shall require authentication within the step-up window (default 5 minutes, maximum 15) at the strength required for their action class, and at least `aal2`. | V7.5 |
| AUTH-FR-5 | Session identifiers shall be at least 128 bits from a CSPRNG, stored only as hashes server-side, and rotated on sign-in, step-up and privilege change. | V7.2 |
| AUTH-FR-6 | All authentication events shall be recorded in the audit trail with `amr`, `acr`, policy version, session ID and outcome. | V16.3 |
| AUTH-FR-7 | Identity data, credentials and sessions of a tenant shall be stored only in that tenant's region. | V14.1 |
| AUTH-FR-8 | Revoking a user's membership shall end their sessions for that tenant within 60 seconds. | V7.4 |
| AUTH-FR-9 | Every tenant shall have at least one phishing-resistant method (passkey or security key) available to every persona that requires MFA. | V6.5 |
| AUTH-FR-10 | Tenant configuration shall never set an authentication requirement below the platform floor; the settings validator and policy editor shall reject such values. | V6.1 |
| AUTH-FR-11 | Changes that weaken authentication for any persona shall require approval by a second authorised administrator. | V8.2 |
| AUTH-FR-12 | Every principal, human or not, shall carry a `kind`, and non-human principals shall never be issued interactive sessions. | V8.2 |
| AUTH-FR-13 | A tenant shall be able to configure every method in the method catalogue that its region and plan allow, without code changes or redeployment. | — |

<!-- section:verification -->
## Verification

- Automated: Playwright journeys for each persona and method; negative tests for enumeration (response equality), session rotation, cross-tenant session reuse, step-up enforcement on every consequential action route (generated from the action catalogue).
- Review: security lead reviews any change to `packages/auth`.
- Pen test (annual and before go-live per region): authentication, session management and SSO abuse cases in scope, including tenant-boundary attacks ([[TST-security-testing]]).

<!-- section:questions -->
## Open questions

- [ ] Build vs self-host: in-house package on vetted libraries (for example `openid-client` for OIDC, a SAML library, `@simplewebauthn/server`) vs a self-hosted identity server per region. A hosted global IdP is ruled out unless it offers in-region data storage for India, Singapore and US. Owner: CTO; record as an ADR.
- [ ] Do SEBI ODR tenants require identity assurance for investors beyond email or mobile control? Assumption: email or mobile OTP is sufficient; to be confirmed by legal (tracked in [[PKG-external-party-identity#questions]]).
- [ ] Should counsel identities be shareable across regions with consent (one login, two regional records) or kept fully separate? Owner: product and DPO.
- [ ] Should `acr` values be exposed to tenants' own systems in webhook payloads or the admin API for their audits? Owner: product.
- [ ] Social IdPs for counsel (not only parties) — demand and risk? Owner: product and security.
- Answered in this overhaul: SCIM provisioning is specified in [[PKG-user-provisioning-scim]] (Enterprise entitlement, phase with tenant SSO).

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

The tenant is resolved from the host before sign-in; sessions carry one tenant and region and are rejected on any other host. Tenant switching for multi-tenant users (counsel, neutrals) re-checks membership and that tenant's authentication policy and issues a fresh session; permissions are never carried across. Identity tables are tenant-scoped through memberships with forced RLS; the user record is region-level and holds no tenant data. Support staff reach tenant data only through tenant-approved grants.

<!-- check:enforcement -->
### Enforcement points and bypass paths

Next.js middleware rejects unauthenticated requests to every route group except `(public)`; Server Actions and tRPC procedures call `requirePrincipal()` (lint rule fails a new action without it); consequential operations call `requireStepUp(actionClass)` (lint rule); REST handlers use the credential middleware in `packages/api-auth`; SCIM uses its own token middleware; Temporal and BullMQ workers use workload identity and carry the originating principal only as context for audit. The step-up coverage test is generated from the permission catalogue's action classes.

<!-- check:lifecycle -->
### Grant lifecycle and privileged access

Joiner, mover and leaver flows are in [[PKG-user-provisioning-scim]]: membership revocation ends tenant sessions within 60 seconds; SCIM deactivation suspends immediately and starts a durable deprovision workflow; without SCIM, stale accounts are reported daily. External participants lose case access with case closure or counsel change ([[PKG-external-party-identity]]). Staff access is via workforce SSO and break-glass only ([[PKG-jit-and-break-glass]], [[PKG-support-access-and-impersonation]]).

<!-- check:resilience -->
### Failure modes and secrets

If the session store (Postgres) is unavailable, requests fail closed (503). If Redis is down, session and policy checks read Postgres (slower, still correct). If a tenant IdP is down, only that connection's users are affected and break-glass admins keep phishing-resistant local sign-in. Signing keys and SSO secrets are in the regional KMS / secrets manager and rotated per [[PKG-encryption-utilities-key]].

<!-- check:residency -->
### Data residency

Users, credentials, sessions, SSO connections, domain claims, policies, SCIM data, verification records and authentication audit events are stored in the tenant's regional database. The sign-in page is served by the regional stack for the tenant host. Email and SMS providers for OTP and magic links, and KYC providers, are selected per region ([[INT-messaging-providers]], [[INT-kyc-and-sanctions-screening]]).

<!-- check:audit -->
### Audit trail

Sign-in success and failure, MFA and passkey enrolment, reset and removal, password change, session revocation, SSO connection and domain changes, authentication policy versions, SCIM and JIT provisioning, invitation lifecycle, identity verification outcomes, API credential issue and rotation and step-up events are all audited with `amr`, `acr`, policy version, session or principal ID, hashed IP and outcome. Credentials, OTPs and ID numbers never appear in events.

<!-- check:observability -->
### Detection and alerting

Security events in [[OBS-security-events]]: login success and failure, MFA changes, policy denies, session revocations, break-glass use, API key anomalies. Alerts per tenant: failed sign-ins above 5× the 7-day baseline in 15 minutes, any break-glass use, deny-rate spike after a policy publish, MFA resets above 3 per day, SCIM errors above 20 %; routed to platform security on-call and the tenant's alert recipients ([[OBS-alerting]]).

<!-- check:compliance -->
### Framework and legal mapping

ISO 27001:2022 Annex A 5.16 (identity management), 5.17 (authentication information), 5.18 (access rights), 8.2 (privileged access rights) and 8.5 (secure authentication) [R3]; SOC 2 CC6.1, CC6.2 and CC6.3 (logical access, registration and removal) [R4]; DPDP reasonable security safeguards. Evidence: published authentication policy versions with approvals, MFA and phishing-resistant coverage per persona, SCIM and deprovisioning logs, API client inventory, audit exports of sign-in events.

<!-- check:testing -->
### Verification and testing

Each child node carries negative tests for every matrix row; in addition the parent suite proves cross-tenant session rejection, step-up coverage for every consequential operation (generated), revocation within 60 seconds, and that no settings combination drops below the platform floor (property test over the settings registry). Annual pen test per region covers authentication, sessions, SSO, SCIM and API credentials ([[TST-security-testing]]).

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
    "body": "ISO/IEC",
    "id": "R3",
    "ident": "27001",
    "kind": "standard",
    "title": "ISO/IEC 27001:2022 Information security management systems",
    "url": "https://www.iso.org/standard/27001",
    "version": "2022"
  },
  {
    "body": "AICPA",
    "id": "R4",
    "ident": "Trust Services Criteria",
    "kind": "standard",
    "title": "2017 Trust Services Criteria (with revised points of focus, 2022)",
    "url": "https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022",
    "version": "2017 (revised points of focus 2022)"
  },
  {
    "body": "NIST",
    "id": "R5",
    "ident": "SP 800-63B-4",
    "kind": "standard",
    "title": "NIST SP 800-63B-4 Digital Identity Guidelines: Authentication and Authenticator Management",
    "url": "https://pages.nist.gov/800-63-4/sp800-63b.html",
    "version": "800-63-4 (final, July 2025)"
  },
  {
    "body": "W3C",
    "id": "R6",
    "ident": "WebAuthn Level 3",
    "kind": "standard",
    "title": "Web Authentication: An API for accessing Public Key Credentials Level 3",
    "url": "https://www.w3.org/TR/webauthn-3/"
  },
  {
    "body": "OpenID Foundation",
    "id": "R7",
    "ident": "OpenID Connect Core 1.0",
    "kind": "standard",
    "title": "OpenID Connect Core 1.0",
    "url": "https://openid.net/specs/openid-connect-core-1_0.html"
  }
]
```

<!-- end -->
