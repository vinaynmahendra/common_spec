---
id: "PKG-sso-saml-oidc-per-tenant"
title: "SSO (SAML, OIDC) per tenant"
parent: "PKG-authentication"
order: 2
type: "feature"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "Tenant SAML 2.0 and OIDC connections plus platform social and government IdPs: versioned connections with test-before-enable, attribute, group and assurance mappings, SSO enforcement with break-glass, single logout; domains and home-realm discovery in the child node"
links: []
rev: 3
syncHash: "c6af2427826d5729"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.1.2 SSO (SAML, OIDC) per tenant

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Tenant SAML 2.0 and OIDC connections plus platform social and government IdPs: versioned connections with test-before-enable, attribute, group and assurance mappings, SSO enforcement with break-glass, single logout; domains and home-realm discovery in the child node

<!-- section:purpose -->
## Purpose and scope

Lets each tenant connect identity providers (IdPs) so its staff, and optionally the neutrals, law firms and parties it works with, sign in with accounts they already have. Three families of connection:

| Family | Examples | Configured by | Typical users |
|---|---|---|---|
| **Tenant enterprise connections** (SAML 2.0, OpenID Connect) | Institution's Microsoft Entra ID, Okta, Google Workspace, ADFS; a law firm's IdP | `security_admin` of the tenant | Secretariat, administrative roles, panel neutrals, counsel of a connected firm |
| **Platform social connections** (OIDC) | Google, Microsoft consumer accounts, Apple, LinkedIn | Nomology operates the client; tenant enables per persona (`auth.methods.social.*`) | Parties and, if the tenant allows, counsel and observers |
| **Government login** (OIDC) | Singpass (Singapore) [R6]; others reserved | Nomology operates the client after onboarding with the scheme; tenant enables (`auth.methods.government_login.providers`) | Parties in Singapore tenants. Assumption: requires Singpass onboarding of Nomology or the tenant as relying party; to be confirmed |

Protects tenants from forged or misrouted assertions and from one tenant's IdP signing users into another tenant. Domain proof and home-realm discovery are specified in [[PKG-domain-verification]]; JIT creation of memberships and SCIM in [[PKG-user-provisioning-scim]]; how strong an SSO sign-in counts is decided with [[PKG-authentication-policies]].

Typical scenarios: an arbitral institution federates its secretariat with Entra ID and enforces SSO for `@institution.example`; a large law firm that appears before several institutions connects its IdP once per tenant; a CORD tenant lets consumer claimants sign in with Google; Nomology staff use the workforce IdP connected to the platform tenant only.

<!-- section:assets -->
## Protected assets

| Asset | Classification |
|---|---|
| SSO connection record (`auth.sso_connection`): family, protocol, IdP entity ID / issuer, metadata URL, signing certificates, OIDC client ID, status, version | Internal |
| OIDC client secret or private key for `private_key_jwt` | Secret (regional secrets manager, referenced by ID) |
| SP signing / decryption key pairs per region | Secret (KMS) |
| Domain claims and domain-to-connection links (`auth_domain_claim`, `auth_domain_connection`, [[PKG-domain-verification#notes]]) | Internal |
| Attribute mappings (email, name, unit, groups) and assurance mappings (`acr`/`amr`/`AuthnContextClassRef` → our `acr`) | Internal, integrity-critical |
| Group-to-role mappings (`group_role_mapping`, shared with SCIM) | Internal, integrity-critical |
| Assertions in flight | Secret; never persisted beyond replay cache (assertion ID, 10 minutes) |

<!-- section:actors -->
## Actors and roles

| Actor (role key) | Role in SSO |
|---|---|
| `security_admin` | Creates, tests, enables, disables connections; maps attributes and groups; enforces SSO for verified domains |
| `tenant_owner` | As `security_admin`; approves mappings that grant administrative roles when no second `security_admin` exists |
| `tenant_admin`, `auditor` | Read connection status and sign-in logs; cannot see or change configuration secrets |
| `platform_security` | Approves manual domain verification; can disable a tenant connection in an incident; manages platform social and government connections |
| `platform_admin` | Configures the platform tenant's workforce connection |
| End user from the IdP | Signs in; linked to an existing membership by verified email on a verified domain, or JIT-provisioned if the tenant allows |
| Tenant's IdP / social or government IdP | External system; trusted only for the domains, tenant and connection it is bound to |
| Attacker | Controls a rogue IdP, tampers with assertions, replays responses, abuses metadata URLs |

<!-- section:matrix -->
## Permission matrix

Permission keys proposed for [[PKG-permission-catalogue]]. "T" own tenant.

| Action | Permission | `security_admin` | `tenant_owner` | `tenant_admin` | `auditor` | `platform_security` | `platform_support` | Others |
|---|---|---|---|---|---|---|---|---|
| View connections and status | `auth.connection:read` | T | T | T | T | ✓ | under grant | ✗ |
| Create connection (draft) | `auth.connection:create` | T | T | ✗ | ✗ | ✓ | ✗ | ✗ |
| Edit connection (draft version) | `auth.connection:update` | T | T | ✗ | ✗ | ✓ | ✗ | ✗ |
| Test connection (sign in as self) | `auth.connection:update` | T | T | ✗ | ✗ | ✓ | ✗ | ✗ |
| Enable connection | `auth.connection:publish` | T after a successful test sign-in in the last 24 h | T | ✗ | ✗ | ✓ | ✗ | ✗ |
| Claim and verify domain | `auth.domain:create` | T ([[PKG-domain-verification]]) | T | ✗ | ✗ | manual override, two-person | ✗ | ✗ |
| Enforce SSO for a domain | `settings.security:write` | T, maker-checker, break-glass admins kept | T | ✗ | ✗ | ✓ | ✗ | ✗ |
| Map groups to non-administrative roles | `auth.connection:update` | T | T | ✗ | ✗ | ✓ | ✗ | ✗ |
| Map groups to administrative roles | `auth.connection:update` + `:approve` by another | T, second approver | T | ✗ | ✗ | ✓ | ✗ | ✗ |
| Map IdP assurance to `acr` | `auth.connection:update` | T, maker-checker | T | ✗ | ✗ | ✓ | ✗ | ✗ |
| JIT on/off per connection | `auth.provisioning:configure` | T | T | ✗ | ✗ | ✓ | ✗ | ✗ |
| Enable a social or government provider for personas | `settings.security:write` | T | T | ✗ | ✗ | platform availability | ✗ | ✗ |
| View connection secrets | — | ✗ (write-only) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Disable connection | `auth.connection:update` | T | T | ✗ | ✗ | ✓ (incident, tenant notified) | ✗ | ✗ |
| Sign in through a connection | — | Users on a domain verified for the connection with a membership, JIT allowed, or (social / government) persona enabled | | | | | | |

<!-- section:policy -->
## Policy model

**Connection lifecycle**: `draft` → `testing` (test sign-in by the admin, diagnostics shown only to them) → `enabled` → `disabled`; configuration edits create a new version that goes through test again before it replaces the enabled one, so a bad certificate never breaks live sign-in. Versions follow [[PKG-configuration-lifecycle]].

**Routing (home-realm discovery)**: email-first routing on the tenant host to the primary connection of a verified domain; rules, statuses and acceptance criteria in [[PKG-domain-verification]]. Social and government buttons appear only for personas where they are enabled; they never appear for a verified domain where SSO is enforced.

**SAML**: SP-initiated only by default; signed assertions required (signed response alone is not enough); audience = tenant-specific SP entity ID `https://{tenantHost}/sso/saml/{connectionId}`; `Recipient` and `Destination` checked; `NotOnOrAfter` with ≤ 2 minutes clock skew; `InResponseTo` matched to the stored request; assertion ID replay cache 10 minutes; XML signature wrapping defences per the OWASP SAML cheat sheet [R3]. IdP-initiated SSO only if `auth.sso.idp_initiated_allowed`, and then with a one-time landing step. Optional encrypted assertions. Certificate rollover: up to two IdP signing certificates active per connection; metadata URL refresh every 24 hours with a diff shown to admins before a new certificate is trusted unless the metadata is fetched over HTTPS from the IdP's documented host.

**OIDC** [R4]: authorization code + PKCE (S256) [R7]; `state` and `nonce` checked; `iss` exact match; `aud` contains client ID; ID token signature verified with keys from the issuer's JWKS (cached 1 h, refetched on unknown `kid`); `email_verified` must be true or the tenant must declare the IdP authoritative for the domain. Client authentication to the IdP: `private_key_jwt` preferred, client secret allowed.

**Social connections**: Nomology-registered OIDC clients per region; only verified emails accepted; **never** used for account linking to a staff membership; `amr` from social IdPs is not trusted for MFA (sign-ins count `aal1`); Apple private-relay addresses are accepted as the account email and shown as such to the case manager.

**Government login**: treated as a federated sign-in for the persona and, where the scheme returns verified identity attributes (for example Myinfo), as an identity verification method for [[PKG-external-party-identity]] only when the person consents to that use. National ID numbers returned are not stored (see that node).

**Attribute mapping** (per connection, versioned): `email` (required), `given_name`/`family_name` or `displayName`, optional unit code, optional groups claim or SAML attribute, optional `employeeNumber`; unknown attributes are ignored. Mappings use a small expression language (`attr("department") == "Registry"`) validated at save, no code.

**Group mapping**: same table and rules as SCIM groups ([[PKG-user-provisioning-scim#flows]] F4); assertion groups apply only at sign-in; mapping to administrative roles needs a second approver.

**Account linking**: link to an existing user only when the email matches and the domain is verified for this connection; otherwise refuse and tell the user to contact the tenant admin. Never link on name. A social sign-in with the same email as an existing local account links only after the user proves control of the existing account (sign in with its current method).

**Assurance**: SSO sign-ins count as `aal1` unless `auth.sso.trust_idp_mfa` is on and the IdP returns `amr`/`acr` (OIDC) or `AuthnContextClassRef` (SAML) values the tenant mapped to `aal2` or `aal2-phr`; if the tenant policy requires a strength the IdP did not assert, the platform asks for its own second factor. Federation assurance considerations follow NIST SP 800-63C-4 [R5] (assumption: we do not claim a FAL).

**Session**: platform session lifetime is the shorter of the tenant policy and the assertion's `SessionNotOnOrAfter`; re-authentication at the IdP (`prompt=login` / `ForceAuthn`) for step-up only when `auth.sso.force_reauth_for_step_up`, otherwise step-up uses platform MFA. Single logout (SAML SLO, OIDC front-channel / back-channel) when `auth.sso.single_logout`; back-channel logout ends the platform session within 60 seconds.

**Break-glass**: when SSO is enforced, at least `auth.sso.break_glass_admins_min` administrators keep a local passkey sign-in; their use alerts all owners.

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|---|
| T1 | S | Rogue IdP claims another organisation's domain | DNS TXT domain verification per tenant ([[PKG-domain-verification]]); manual override needs two `platform_security` | Low |
| T2 | S | Assertion from tenant A's IdP used on tenant B | Per-tenant, per-connection audience and ACS URL; connection ID in path; tenant from host must match connection's tenant | Very low |
| T3 | T | XML signature wrapping / comment injection | Library hardened against XSW, schema validation, use only the signed element, reject multiple assertions | Low (library vulnerabilities) |
| T4 | S | Replay of SAML response or OIDC code | `InResponseTo` and replay cache; PKCE; single-use codes | Low |
| T5 | E | Group mapping grants an administrative role unexpectedly | Second-admin approval; mapping changes audited and notified to all tenant admins | Low |
| T6 | D | IdP outage locks out secretariat before a hearing | Break-glass admins on passkey; tenant can add a time-limited policy exclusion allowing email OTP + passkey for named users ([[PKG-authentication-policies]]) | Medium |
| T7 | I | Metadata URL used for SSRF | Metadata fetched only from HTTPS URLs on public IPs via the egress proxy with an allow-list per connection | Low |
| T8 | E | De-provisioned IdP user keeps platform session | Session lifetime bound to assertion; SCIM deactivation or back-channel logout ends sessions ≤ 60 s; stale-account report without SCIM | Low with SCIM, Medium without |
| T9 | S | Social account takeover used to reach a case | Social sign-in only for enabled personas, `aal1`, step-up for consequential actions; linking to existing accounts requires proof of the existing method | Medium for parties |
| T10 | E | Over-trusting IdP MFA claims | Explicit assurance mapping with maker-checker; tenant policy can require platform MFA regardless | Low |

<!-- section:failure -->
## Denial behaviour

SSO errors land on a tenant-branded error page with a correlation ID and a plain message ("Your organisation's sign-in did not complete. Try again or contact your administrator.") — never the raw SAML or OIDC error. Admin test sign-ins show detailed diagnostics (which check failed) only to the tenant admin who started the test. All failures are logged with connection ID and reason code (`saml_signature_invalid`, `audience_mismatch`, `assertion_expired`, `domain_not_verified`, `no_membership`).

<!-- section:requirements -->
## Security requirements

ASVS references are to OWASP ASVS **5.0** at section level [R1][R2]; requirement-level IDs are filled in when text is checked against the 5.0.0 release.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| SSO-1 | Each tenant SSO connection shall belong to exactly one tenant and accept assertions only at that tenant's host and connection-specific endpoint. | V6.8, V10.5 |
| SSO-2 | SAML assertions shall be signed and validated for audience, recipient, destination, validity window and replay. | V6.8 |
| SSO-3 | OIDC sign-in shall use authorization code with PKCE and validate `state`, `nonce`, `iss`, `aud` and signature. | V10.2, V10.5 |
| SSO-4 | Users shall be linked to existing accounts only by email on a domain verified for that connection ([[PKG-domain-verification]]). | V6.8 |
| SSO-5 | Enforcing SSO for a domain shall require at least one break-glass tenant admin with phishing-resistant MFA. | V6.4 |
| SSO-6 | Connection secrets shall be write-only in the UI and API and stored in the regional secrets manager. | V13.3 |
| SSO-7 | Role mappings that grant any administrative role shall require approval by a second administrator. | V8.2 |
| SSO-8 | A changed connection configuration shall not replace the enabled version until a test sign-in with the new version has succeeded. | — |
| SSO-9 | Social sign-ins shall count as `aal1`, shall never link to staff memberships, and shall be available only to personas the tenant enabled. | V6.8 |
| SSO-10 | IdP-asserted MFA shall raise `acr` only through an explicit, maker-checker-approved assurance mapping on the connection. | V6.8 |
| SSO-11 | Disabling a connection, or a back-channel logout from the IdP, shall end the affected platform sessions within 60 seconds. | V7.4 |

<!-- section:verification -->
## Verification

- Conformance suite: SAML test vectors (unsigned assertion, wrong audience, expired, XSW variants, duplicate assertions) and OIDC negative tests (missing PKCE, wrong `nonce`, wrong `iss`, unverified email) run in CI against a test IdP (Keycloak in docker-compose) for both protocols.
- Cross-tenant test: an assertion valid for tenant A posted to tenant B's endpoint is rejected.
- Pen test scope includes SSO abuse cases per region.

<!-- section:questions -->
## Open questions

- [ ] SAML library choice and whether to run a self-hosted SAML-to-OIDC bridge per region instead of parsing SAML in the app. Owner: security.
- [ ] Do neutrals sign in through an institution's IdP (institution-managed accounts) or their own? Affects linking across tenants. Owner: product.
- [ ] Should law-firm connections be shareable across tenants of the same region (configured once) or always per tenant? Proposed: per tenant for isolation; revisit with demand. Owner: product, security.
- [ ] Which social providers per offering and region at launch (LinkedIn for counsel?). Owner: product.
- [ ] Singpass relying-party onboarding: does Nomology (TAPL) onboard once for all Singapore tenants, or does each tenant onboard? Owner: legal, TAPL operations.
- [ ] Is there an Indian government sign-in scheme suitable for private-sector relying parties (for example via DigiLocker sign-in) that we should support? Assumption: not at launch. Owner: legal, product.
- Answered: SCIM 2.0 is specified in [[PKG-user-provisioning-scim]] (Enterprise plan).

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Connections, domain claims and mappings are tenant-owned rows with forced RLS. The connection ID is in the endpoint path and must belong to the tenant resolved from the host; audience values are unique per tenant and connection. A domain verified in tenant A grants nothing in tenant B. Group mappings apply only to memberships in the connection's tenant. Platform social clients are shared infrastructure, but the resulting identity is linked per tenant membership.

<!-- check:enforcement -->
### Enforcement points and bypass paths

The only endpoints that accept assertions or codes are `sso/[connection]/callback` Route Handlers in the `(public)` group ([[APP-public-and-sign-in-surfaces]]); they call one verifier per protocol and then the same session issuer and policy evaluator as every other method, so SSO cannot bypass tenant authentication policies.

<!-- check:lifecycle -->
### Grant lifecycle and privileged access

Sessions created through SSO never outlive the assertion's session limit or tenant policy (12 h max). Disabling a connection or a back-channel logout revokes affected sessions within 60 seconds. Administrative role mappings and assurance mappings need maker-checker. With SCIM, deactivation is immediate ([[PKG-user-provisioning-scim]]); without SCIM, a daily report lists users whose last IdP sign-in is older than 30 days.

<!-- check:resilience -->
### Failure modes and secrets

IdP metadata and JWKS are cached (1 h) so short IdP metadata outages do not break sign-in; unknown `kid` triggers one refetch, then denial. SP keys are in KMS and rotated yearly with overlapping publication in metadata for 30 days. Versioned connections mean a bad edit never replaces a working configuration until tested. An IdP outage affects only that connection's users; break-glass admins remain.

<!-- check:residency -->
### Data residency

Connection records, mappings and secrets are stored in the tenant's region; assertions are consumed by the regional stack. The external IdP is chosen and operated by the tenant (or, for social and government providers, by the provider); the authentication request contains no case data. Platform social and government clients are registered per region.

<!-- check:audit -->
### Audit trail

Audited: connection create, version, test result, enable, disable; domain claims and verification ([[PKG-domain-verification]]); attribute, group and assurance mapping changes (with approver); social and government provider enablement; SSO sign-in success and failure with reason code and connection version; JIT provisioning of a new membership; back-channel logouts.

<!-- check:observability -->
### Detection and alerting

Per connection: sign-in success rate, failure reason codes, assertion latency, certificate expiry date. Alerts to `auth.admin.alert_recipients` and Nomology support: success rate below 80 % for 15 minutes, IdP signing certificate expiring within 30 days, metadata refresh failing for 3 days, any break-glass sign-in, any `audience_mismatch` burst (possible cross-tenant replay, also to platform security).

<!-- check:compliance -->
### Framework and legal mapping

ISO 27001:2022 Annex A 5.16 (identity management), 5.17 and 8.5 (secure authentication) [R8]; SOC 2 CC6.1 and CC6.2 [R9]. Evidence: connection inventory and versions, approval records for mappings, domain verification records, SSO sign-in logs.

<!-- check:testing -->
### Verification and testing

CI runs the SAML and OIDC negative conformance suites and the cross-tenant assertion test against a containerised test IdP (Keycloak) on every change to `packages/auth/sso`; plus tests for versioned connection replacement, assurance mapping, social `aal1` and back-channel logout timing.

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
    "body": "OWASP",
    "id": "R3",
    "ident": "Cheat Sheet Series",
    "kind": "standard",
    "title": "OWASP SAML Security Cheat Sheet",
    "url": "https://cheatsheetseries.owasp.org/cheatsheets/SAML_Security_Cheat_Sheet.html"
  },
  {
    "body": "OpenID Foundation",
    "id": "R4",
    "ident": "OpenID Connect Core 1.0",
    "kind": "standard",
    "title": "OpenID Connect Core 1.0",
    "url": "https://openid.net/specs/openid-connect-core-1_0.html"
  },
  {
    "body": "NIST",
    "id": "R5",
    "ident": "SP 800-63C-4",
    "kind": "standard",
    "title": "NIST SP 800-63C-4 Digital Identity Guidelines: Federation and Assertions",
    "url": "https://pages.nist.gov/800-63-4/sp800-63c.html",
    "version": "800-63-4"
  },
  {
    "body": "Government Technology Agency of Singapore",
    "id": "R6",
    "kind": "vendor",
    "title": "Singpass Developer Docs (Singpass login and Myinfo)",
    "url": "https://docs.developer.singpass.gov.sg/docs"
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
    "body": "ISO/IEC",
    "id": "R8",
    "ident": "27001",
    "kind": "standard",
    "title": "ISO/IEC 27001:2022 Information security management systems",
    "url": "https://www.iso.org/standard/27001",
    "version": "2022"
  },
  {
    "body": "AICPA",
    "id": "R9",
    "ident": "Trust Services Criteria",
    "kind": "standard",
    "title": "2017 Trust Services Criteria (with revised points of focus, 2022)",
    "url": "https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022",
    "version": "2017 (revised points of focus 2022)"
  }
]
```

<!-- end -->
