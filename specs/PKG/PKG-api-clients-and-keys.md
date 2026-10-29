---
id: "PKG-api-clients-and-keys"
title: "API clients, keys and OAuth apps"
parent: "PKG-authentication"
order: 5
type: "feature"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "Administration of machine and third-party credentials: API clients with human owners, restricted scopes, resource and IP restrictions, approval for admin scopes, expiring and rotatable keys, OAuth confidential clients and user-delegated OAuth apps, unused and owner-left suspension and leak response"
links: []
rev: 1
syncHash: "89907c8f5297b2b6"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.1.5 API clients, keys and OAuth apps

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Administration of machine and third-party credentials: API clients with human owners, restricted scopes, resource and IP restrictions, approval for admin scopes, expiring and rotatable keys, OAuth confidential clients and user-delegated OAuth apps, unused and owner-left suspension and leak response

<!-- section:purpose -->
## Purpose and scope

Administration of every credential a machine or third-party application uses to call the platform on a tenant's behalf: **API clients** (the registered integration), their **API keys**, **OAuth confidential clients** (client credentials with `private_key_jwt` or mTLS), **OAuth apps** that act for a signed-in user (authorisation code with PKCE and a consent screen), and the aggregator clients that Nomology operates for partners such as NSE. Credential verification at request time and the storage schema already exist in [[INT-public-api-and-webhooks#auth]] and [[INT-api-platform-tables]]; this node owns **who may create, scope, restrict, rotate, review and revoke** them, and the rules that keep them least-privilege.

Out of scope here: SCIM tokens (lifecycle in [[PKG-user-provisioning-scim#auth]], listed in the same console page), webhook signing secrets ([[APP-webhooks-outbound]]), outbound provider credentials ([[INT-connections-admin]]), the principal model for service accounts and AI agents ([[PKG-non-human-principals]]).

Pattern borrowed from: restricted API keys with per-resource permissions, test and live modes, and key roll with overlap as in payment-platform dashboards; described here as our behaviour.

<!-- section:assets -->
## Protected assets

| Asset | Classification | Storage |
|---|---|---|
| API key secret | Secret | SHA-256 hash and 12-character prefix only (`api_key.key_hash`), shown once |
| OAuth client secret (if `client_secret_basic` allowed) | Secret | Hash only; discouraged |
| Client public keys (JWKS) or `jwks_uri`; mTLS certificate thumbprints | Internal, integrity-critical | `oauth_client.jwks`, `oauth_client.mtls_thumbprints` |
| Access tokens (JWT, 10 min default) | Secret, bearer | Not stored; `jti` deny-list in Redis on revocation |
| Refresh tokens for OAuth apps | Secret | Hash, rotated on use, family revoked on reuse detection |
| Scope grants, resource restrictions, IP allow-lists | Internal, integrity-critical | `api_client` columns |
| User consents to OAuth apps | Personal | `oauth_consent` |
| Usage records (last used, source IP, counts) | Internal; IP is personal where a person's device | `api_client_usage_daily`, hashed IP |

<!-- section:actors -->
## Actors and roles

| Actor (role key) | Interaction | How acquired |
|---|---|---|
| `integration_admin` | Creates and manages API clients and OAuth confidential clients for the tenant; cannot grant admin scopes | Tenant role assignment |
| `security_admin` | Approves clients that request admin scopes (`admin.*`, `audit:read`), sets credential policy settings, reviews unused clients | Tenant role assignment |
| `tenant_owner` | As `security_admin`; approves OAuth app allow-list | Onboarding |
| Client owner (a named human member) | Accountable for one client; receives expiry and anomaly notices; must be an active member | Chosen at creation |
| `platform_admin` | Creates aggregator clients and links them to tenants after tenant approval ([[INT-aggregator-intake-api]]) | Workforce IdP |
| `service_account` | The principal an API client acts as, with a permission set | Created with the client ([[PKG-non-human-principals]]) |
| End user (any persona) | Grants or revokes consent for an allow-listed OAuth app | — |
| Third-party developer | Builds against the developer portal and sandbox; never gets live credentials without a tenant creating the client | [[DOC-api-documentation-openapi]] |

<!-- section:matrix -->
## Permission matrix

Permission keys proposed for [[PKG-permission-catalogue]]. "T" own tenant, "own" clients they own.

| Action | Permission | `integration_admin` | `security_admin` | `tenant_owner` | `tenant_admin` | `auditor` | Client owner | `platform_admin` | Admin API client |
|---|---|---|---|---|---|---|---|---|---|
| List clients and usage | `api_client:list` | T | T | T | T | T | own | ✓ | with `admin.integrations:write` |
| Create client (non-admin scopes) | `api_client:create` | T, step-up | T, step-up | T, step-up | ✗ | ✗ | ✗ | aggregator clients only | ✗ (never via API) |
| Request admin scopes on a client | `api_client:create` | T (goes to approval) | T | T | ✗ | ✗ | ✗ | ✗ | ✗ |
| Approve admin scopes | `api_client:approve` | ✗ | T (not own request) | T | ✗ | ✗ | ✗ | ✗ | ✗ |
| Narrow scopes or restrictions | `api_client:update` | T | T | T | ✗ | ✗ | own | ✓ | ✗ |
| Widen scopes | `api_client:update` + approval | T (approval) | T (approval if admin scope) | T | ✗ | ✗ | ✗ | ✗ | ✗ |
| Create key / rotate | `api_client.key:create` | T, step-up | T, step-up | T | ✗ | ✗ | own, step-up | ✓ | with `admin.integrations:write` (rotation only) |
| Revoke key or suspend client | `api_client.key:delete` | T | T | T | T (emergency) | ✗ | own | ✓ | with `admin.integrations:write` |
| Register JWKS / certificate | `api_client:update` | T | T | T | ✗ | ✗ | own | ✓ | ✗ |
| Manage OAuth app allow-list | `oauth_app:configure` | ✗ | T | T | ✗ | ✗ | ✗ | publishes catalogue | ✗ |
| Grant consent to an OAuth app | `oauth_app.consent:create` | own | own | own | own | own | — | ✗ | ✗ |
| Revoke a user's consent | `oauth_app.consent:delete` | ✗ | T | T | ✗ | ✗ | ✗ | ✗ | ✗ |

Escalation rule: no principal can create or widen a client beyond its own effective permissions, and admin scopes are never granted by an API call.

<!-- section:policy -->
## Policy model

**Client types**

| Type | Grant / auth | Typical use | Notes |
|---|---|---|---|
| Server API key client | `Authorization: Bearer ntk_live_{region}_…` (or `ntk_test_…`) | Small tenant scripts, e-filing bridges | Simplest; prefer OAuth for high privilege |
| OAuth confidential client | Client credentials with `private_key_jwt` [R4] (preferred) or mTLS [R5] | Institutions, aggregators, enterprise integrations | Short-lived JWT access tokens; optional sender-constrained tokens with DPoP [R6] or certificate binding [R5] |
| OAuth app (user-delegated) | Authorisation code + PKCE [R7], refresh token rotation | Counsel's practice-management tool reading their own cases | Phase 2; disabled by default (`auth.oauth_apps.user_consent = disabled`); acts with the narrower of the user's permissions and the granted scopes |
| Aggregator client | OAuth `private_key_jwt`, platform-created | NSE (SEBI ODR), MSME aggregator | Linked per tenant through `aggregator_tenant_link` with tenant approval |

**Restrictions on a client** (all optional, all tightening):
- Scopes from [[INT-public-api-and-webhooks#auth]]; admin scopes flagged high privilege.
- Resource restrictions: case types, units, and for read scopes a maximum confidentiality tier ([[SEC-data-classification]]).
- Network: IP allow-list (CIDRs, max 20); required for admin scopes when `auth.api_clients.admin_scope_requires_ip_allowlist`.
- Environment: `test` credentials work only against the tenant sandbox; `live` only against production.
- Expiry: each credential expires within `auth.api_clients.max_credential_days`; non-expiring keys are not allowed.

**Lifecycle**
1. Create (console only, step-up `strength.phishing_resistant`): name, owner, purpose, scopes, restrictions; the service account principal is created with permission set `ps.integration.<client>` limited to the scopes.
2. Admin scopes → `in_review` until approved by a different `security_admin` or `tenant_owner` ([[PKG-separation-of-duties]]).
3. Credential issue: key shown once with copy-to-clipboard and a download option; or JWKS registration.
4. Rotation: a second active key or key in the JWKS; the old one is retired after a chosen overlap (default 7 days, max 30); expiry reminders to the owner at 30, 7 and 1 days.
5. Review: clients unused for `auth.api_clients.unused_disable_days` are suspended (owner and security admins notified 14 days before); every admin-scope client appears in the quarterly review ([[SEC-access-reviews]]).
6. Owner leaves: when the owner's membership is suspended or ended ([[PKG-user-provisioning-scim]] F3), clients they own are flagged and, if no new owner is set within 7 days, suspended.
7. Revoke: immediate; access tokens of the client are rejected within 60 seconds via the `jti` deny-list and client status cache; OAuth token revocation endpoint per RFC 7009 [R8].

**Leak response.** Key prefixes are registered with secret-scanning programmes where available; a reported leak or a key seen in a public repository triggers automatic revocation, an alert to owner and security admins, and a security event `nomo.sec.api_key_leaked`.

**OAuth security baseline** follows the OAuth 2.0 Security BCP [R3]: no implicit or password grants, exact redirect URI matching, PKCE for every authorisation code flow, refresh token rotation, audience-restricted access tokens per regional API base URL.

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|---|
| T1 | S | Leaked API key used from the internet | IP allow-lists (required for admin scopes), short expiry, secret scanning, anomaly alert on new source network (`nomo.sec.api_key_used_new_origin`), instant revoke | Medium for keys without allow-lists |
| T2 | E | Compromised admin session mints a powerful client | Console-only creation with phishing-resistant step-up; admin scopes need a second approver; no creation via API | Low |
| T3 | E | Client acts beyond intended data | Scopes plus resource restrictions plus permission matrix on every object; service account has its own narrow permission set | Low |
| T4 | S | Stolen access token replayed | 10-minute tokens; optional DPoP or mTLS binding for admin scopes | Low with binding, Medium without |
| T5 | R | Nobody knows who owns an integration | Mandatory human owner; ownerless clients suspended | Low |
| T6 | I | Malicious OAuth app harvests case data via user consent | User consent disabled by default; allow-list only; consent screen shows tenant-approved scopes; admin can revoke all consents of an app | Low |
| T7 | T | Cross-region or cross-tenant token use | Tokens carry tenant and regional audience; verifier rejects other audiences | Very low |
| T8 | D | Runaway integration exhausts limits | Per-client rate limits ([[APP-api-versioning-rate-limiting]]); suspension by `tenant_admin` in an emergency | Low |

<!-- section:failure -->
## Denial behaviour

- Invalid, expired or revoked credential: `401` with problem type `auth/invalid-credentials` (no detail on which); suspended client: `401` with the same type to avoid confirming existence.
- Insufficient scope: `403` problem `auth/insufficient-scope` listing the missing scope (scopes are public documentation).
- IP not allowed: `403` problem `auth/network-not-allowed` without echoing the allow-list.
- Console: secret fields are write-only; after creation only prefix and last 4 characters are shown.
- Logged: `nomo.sec.api_key_created`, `_revoked`, `_used_new_origin`, `_leaked`, client approval and scope changes, with client ID and hashed IP.

<!-- section:requirements -->
## Security requirements

ASVS references are to OWASP ASVS **5.0** at section level [R1][R2]; requirement-level IDs are filled in when text is checked against the 5.0.0 release.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| APIC-FR-1 | API clients and their scopes shall be created only by a human tenant administrator in the console after phishing-resistant step-up, never through an API. | V8.2, V6.4 |
| APIC-FR-2 | A client requesting any admin scope shall stay inactive until approved by a second administrator who is not the requester. | V8.2 |
| APIC-FR-3 | Every credential shall have an expiry within the tenant's configured maximum and the platform maximum of 730 days. | V13.3 |
| APIC-FR-4 | Secrets shall be shown once and stored only as hashes; the console and API shall never return a stored secret. | V13.3 |
| APIC-FR-5 | Every client shall have an active human owner; a client whose owner leaves shall be suspended after 7 days without a new owner. | V8.2 |
| APIC-FR-6 | A client's effective access shall be the intersection of its scopes, resource restrictions, network restrictions and the permission matrix for its service account. | V8.2 |
| APIC-FR-7 | Revoking a key or suspending a client shall cause all its requests, including those with unexpired access tokens, to be rejected within 60 seconds. | V7.4 |
| APIC-FR-8 | Clients unused for the configured period shall be suspended with prior notice to the owner. | V8.2 |
| APIC-FR-9 | OAuth flows shall follow RFC 9700: authorisation code with PKCE only, exact redirect matching, refresh token rotation and audience-restricted tokens. | V10.1–V10.4 |
| APIC-FR-10 | Where `auth.api_clients.sender_constrained_for_admin_scopes` is on, tokens with admin scopes shall be bound to the client by DPoP or mTLS. | V10.3 |
| APIC-FR-11 | Credentials shall be valid for one tenant, one region and one environment (`live` or `test`). | V8.2 |

<!-- section:verification -->
## Verification

- Negative tests per matrix row (for example an admin API client calling `POST /admin/v1/api-clients` gets `405`; `integration_admin` cannot approve own admin-scope request).
- Revocation latency test (≤ 60 s) across web containers with a fake clock.
- Token tests: wrong audience, other region, expired, `test` key against production, DPoP proof missing or replayed.
- OAuth conformance: PKCE required, redirect URI exact match, refresh reuse detection revokes the family.
- Scheduled job tests: unused suspension, owner-left suspension, expiry reminders.
- Pen test: key leakage handling, scope escalation, consent phishing for OAuth apps.

<!-- section:questions -->
## Open questions

- [ ] Do we expose OAuth apps (user-delegated access) in phase 2 or later, and who reviews third-party apps for the catalogue? (Product, Security)
- [ ] mTLS for aggregators: do NSE or other MIIs require it? (Integrations)
- [ ] Should the `INT-api-platform-tables` schema gain `owner_membership_id`, `allowed_cidrs`, `resource_restrictions jsonb`, `service_account_id` and `oauth_client.mtls_thumbprints`? Proposed: yes; to be added by the API platform owner. (Engineering)
- [ ] Which secret-scanning programmes can we register our key prefixes with? (Security)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Clients, keys, OAuth clients and consents are tenant-owned rows under forced RLS; the credential verifier resolves the tenant from the credential and the regional audience, and the request's tenant context is set from that, never from a path or header. Aggregator clients are platform-created but act in a tenant only through an approved `aggregator_tenant_link`, separately per tenant.

<!-- check:enforcement -->
### Enforcement points and bypass paths

All public and admin API Route Handlers pass through one credential middleware (`packages/api-auth`) that checks status, expiry, environment, region, IP restriction, scope and then hands a service-account principal to the same permission matrix used for people. There is no route that accepts an API key without that middleware (route lint rule).

<!-- check:lifecycle -->
### Grant lifecycle and privileged access

Create with step-up, admin scopes with approval, expiry on every credential, rotation with overlap, unused and owner-left suspension, quarterly review of admin-scope clients, immediate revocation. Platform aggregator clients are reviewed by `platform_security` quarterly.

<!-- check:resilience -->
### Failure modes and secrets

If the client status cache (Redis) is unavailable, the verifier reads Postgres; if Postgres is unavailable, API requests fail closed with 503. Token signing keys are in the regional KMS and rotate every 90 days with JWKS overlap; if a signing key is suspected compromised, all tokens are invalidated by key removal and clients re-authenticate automatically.

<!-- check:residency -->
### Data residency

Clients and credentials exist only in the tenant's region; keys carry the region in their prefix and tokens carry a regional audience, so a credential cannot be used in another region.

<!-- check:audit -->
### Audit trail

Audited: client create, approve, update (scopes and restrictions with old and new values), owner change, key create, rotate, revoke, JWKS changes, consent grant and revoke, automatic suspensions. Per-request usage is aggregated daily; detailed request logs follow [[OBS-foundations]].

<!-- check:observability -->
### Detection and alerting

Dashboards per tenant: active clients, admin-scope clients, keys expiring in 30 days, unused clients, error rates per client. Alerts: use from a new network for an admin-scope client, leak report, spike of 401s for one client (rotation failure or attack).

<!-- check:compliance -->
### Framework and legal mapping

ISO 27001:2022 Annex A 5.17 (authentication information), 8.2 (privileged access rights), 5.18 (access rights) [R9]; SOC 2 CC6.1, CC6.2, CC6.3 [R10]. Evidence: client inventory with owners and scopes, approval records for admin scopes, review sign-offs, revocation logs.

<!-- check:testing -->
### Verification and testing

Matrix negative tests, revocation timing, token and OAuth conformance tests, scheduled job tests and pen testing as listed under verification.

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
    "body": "IETF",
    "id": "R3",
    "ident": "RFC 9700 (BCP 240)",
    "kind": "standard",
    "title": "Best Current Practice for OAuth 2.0 Security",
    "url": "https://www.rfc-editor.org/rfc/rfc9700"
  },
  {
    "body": "IETF",
    "id": "R4",
    "ident": "RFC 7523",
    "kind": "standard",
    "title": "JSON Web Token (JWT) Profile for OAuth 2.0 Client Authentication and Authorization Grants",
    "url": "https://www.rfc-editor.org/rfc/rfc7523"
  },
  {
    "body": "IETF",
    "id": "R5",
    "ident": "RFC 8705",
    "kind": "standard",
    "title": "OAuth 2.0 Mutual-TLS Client Authentication and Certificate-Bound Access Tokens",
    "url": "https://www.rfc-editor.org/rfc/rfc8705"
  },
  {
    "body": "IETF",
    "id": "R6",
    "ident": "RFC 9449",
    "kind": "standard",
    "title": "OAuth 2.0 Demonstrating Proof of Possession (DPoP)",
    "url": "https://www.rfc-editor.org/rfc/rfc9449"
  },
  {
    "body": "IETF",
    "id": "R7",
    "ident": "RFC 7636",
    "kind": "standard",
    "title": "Proof Key for Code Exchange by OAuth Public Clients",
    "url": "https://www.rfc-editor.org/rfc/rfc7636"
  },
  {
    "body": "IETF",
    "id": "R8",
    "ident": "RFC 7009",
    "kind": "standard",
    "title": "OAuth 2.0 Token Revocation",
    "url": "https://www.rfc-editor.org/rfc/rfc7009"
  },
  {
    "body": "ISO/IEC",
    "id": "R9",
    "ident": "27001",
    "kind": "standard",
    "title": "ISO/IEC 27001:2022 Information security management systems",
    "url": "https://www.iso.org/standard/27001",
    "version": "2022"
  },
  {
    "body": "AICPA",
    "id": "R10",
    "ident": "Trust Services Criteria",
    "kind": "standard",
    "title": "2017 Trust Services Criteria (with revised points of focus, 2022)",
    "url": "https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022",
    "version": "2017 (revised points of focus 2022)"
  }
]
```

<!-- end -->
