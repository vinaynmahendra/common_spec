---
id: "ADR-identity-platform"
title: "Identity platform"
parent: "ADR"
order: 12
type: "decision"
template: "adr"
status: "draft"
owner: null
indicative: false
summary: "Build on libraries, self-host an identity server per region, or use a managed IdP? Proposed: @nomology/auth in our regional stacks on vetted libraries (openid-client, SimpleWebAuthn), our own SCIM, and self-hosted Ory Polis per region for SAML; Keycloak broker-only as fallback; managed options fail India/Singapore residency except Auth0 Private Cloud."
links: []
rev: 1
syncHash: "38116ddac9e81804"
createdAt: "2026-10-28T09:00:00Z"
updatedAt: "2026-10-28T09:00:00Z"
updatedBy: null
---

# 19.10 Identity platform

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Build on libraries, self-host an identity server per region, or use a managed IdP? Proposed: @nomology/auth in our regional stacks on vetted libraries (openid-client, SimpleWebAuthn), our own SCIM, and self-hosted Ory Polis per region for SAML; Keycloak broker-only as fallback; managed options fail India/Singapore residency except Auth0 Private Cloud.

<!-- section:context -->
## Context and problem

**Question:** where does authentication run for CORD and TERES, and on what? Options are libraries inside our Next.js app (with our own SAML/OIDC handling), a self-hosted identity server in each region, or a managed identity provider that keeps data in each region.

**Hard constraint:** identity data, credentials, sessions and authentication events for a tenant are stored and processed only in that tenant's region: India, Singapore or US, and on Azure where a client requires it (AUTH-FR-7 in [[PKG-authentication]], [[MT-data-residency-2]]). A provider that cannot keep the data in the country fails, whatever its other merits.

**What the platform must do** (already specified in the overhauled nodes):

| Capability | Specified in | Notable requirement |
|---|---|---|
| Method catalogue: password, magic link, email / SMS / WhatsApp OTP, passkeys (synced and device-bound), TOTP, recovery, social and government login | [[PKG-authentication]], [[PKG-email-password-magic-link-otp]], [[PKG-mfa-session-management-device]] | Passkey relying-party ID = the **tenant host**; SMS and WhatsApp OTP through regional providers in India |
| Assurance model and `Principal` contract (`acr` `aal1`–`aal3`, `amr`, `ivl`, policy version) | [[PKG-authentication#policy]] | Our own ordered assurance values |
| Per-tenant SAML 2.0 and OIDC connections, versioned with test-before-enable, assurance and group mapping, domain verification, home-realm discovery, single logout, break-glass admins | [[PKG-sso-saml-oidc-per-tenant]], [[PKG-domain-verification]] | Tenant-specific SP entity ID and ACS URL on the tenant host |
| Tenant authentication policies: strictest-wins rules, report-only mode, simulator, step-up by action class, network zones, device trust, platform floor | [[PKG-authentication-policies]] | Authored by tenant `security_admin` in our console |
| SCIM 2.0 Users and Groups, JIT, invitations, auto-join, durable deprovisioning (Temporal), reconciliation | [[PKG-user-provisioning-scim]] | `/scim/v2` per region; deactivation ends sessions within 60 s |
| External parties and counsel at volume: invitation bound to email, identity verification levels, representation | [[PKG-external-party-identity]] | SEBI ODR investor and MSME claimant volumes |
| API clients, keys, OAuth confidential clients (`private_key_jwt`, mTLS, DPoP), aggregator clients | [[PKG-api-clients-and-keys]] | Credentials bound to one tenant, region and environment |
| 82 `auth.*` settings within the scope hierarchy | [[PKG-settings-security-and-identity]] | Platform, region, offering, tenant, unit scopes |
| Sessions | [[PKG-mfa-session-management-device]] | Server-side, `__Host-` cookie per tenant host, revocation within 60 s |

**Affected parts:** `packages/auth`, the `(public)` sign-in surfaces ([[APP-public-and-sign-in-surfaces]]), the identity tables in [[MT-tenancy-and-identity-schema]], every route group, the admin console security pages ([[APP-tenant-admin-console]]), the API credential layer ([[INT-public-api-and-webhooks]]), workers that carry principals, and the regional infrastructure ([[INF-secrets-and-keys]], [[INF-redis]]).

**Out of scope:** Nomology's own workforce identity provider for staff (it is connected to the platform tenant as an ordinary enterprise connection), authorisation after sign-in ([[ADR-policy-engine]]), and KYC providers ([[INT-kyc-and-sanctions-screening]]).

<!-- section:drivers -->
## Decision drivers

| # | Driver | Weight | Why it matters here |
|---|---|---|---|
| D1 | **Country-level residency in India, Singapore and US (and Azure)** | Must | AUTH-FR-7; client contracts and DPDP / PDPA expectations; a region-level geography such as "Asia Pacific" is not enough |
| D2 | **Per-tenant enterprise federation (SAML 2.0 and OIDC)** | High | Institutions bring Entra ID, Okta, ADFS, Google Workspace; law firms bring their own IdP; versioned connections, assurance mapping and group mapping (SSO-1 to SSO-11) |
| D3 | **SCIM 2.0 with Users and Groups, and fast deprovisioning** | High | Group-to-role mapping, deactivation ends sessions within 60 s, reassignment through Temporal ([[PKG-user-provisioning-scim]]) |
| D4 | **Tenant-authored authentication policies with our assurance model** | High | Strictest-wins, report-only, simulator, step-up per action class, platform floor in code ([[PKG-authentication-policies]]) |
| D5 | **Phishing-resistant passkeys bound to the tenant host** | High | Relying-party ID per tenant host; synced vs device-bound distinction for `aal2-phr` / `aal3` (NIST SP 800-63B-4 forbids syncable authenticators at AAL3 [R29]) |
| D6 | **External parties at volume** | High | Magic links, OTP via regional SMS / WhatsApp providers, invitations bound to email; per-user pricing must stay viable at SEBI ODR volumes |
| D7 | **One identity model with our database** | High | Users per region, memberships tenant-owned under forced RLS ([[ADR-tenant-isolation]]), sessions revocable in 60 s; no second user store to reconcile |
| D8 | **Fit with the stack** | Medium | TypeScript, Next.js, Prisma ([[ADR-orm]]), Temporal, ECS per region and Azure Container Apps ([[ADR-container-orchestration]]) |
| D9 | **Operational burden and cost for a small team across 3+ regions** | Medium | Every component runs in India, Singapore, US and possibly Azure |
| D10 | **Security maturity, lock-in and licence** | Medium | Who finds and patches protocol vulnerabilities; exit cost; licence obligations for a commercial SaaS |

<!-- section:decision -->
## Decision

**Status: Proposed — awaiting CTO decision.**

**Recommended option: build authentication on libraries inside our regional stack, with one isolated open-source component for SAML.** This is option A in the options table.

1. **`@nomology/auth` in the Next.js app and workers owns the identity model**: users, memberships, credentials, sessions, the `Principal` contract, assurance values, tenant authentication policies, step-up, devices, invitations, SCIM and API credentials, all in the regional Postgres under forced RLS as specified in [[MT-tenancy-and-identity-schema]] and the `PKG-authentication` children.
2. **Protocol work uses vetted libraries, not hand-written crypto:**
   - OIDC relying party (tenant OIDC connections, social and Singpass login): `openid-client`, MIT licence, OpenID Certified for the Basic, FAPI 1.0 and FAPI 2.0 relying-party profiles, with PKCE, PAR and DPoP support [R27].
   - Passkeys and security keys: `@simplewebauthn/server` and `@simplewebauthn/browser`, MIT licence [R28], with the relying-party ID set to the tenant host.
   - Password hashing: Argon2id at OWASP parameters ([[PKG-email-password-magic-link-otp]]).
3. **SAML is handled by Ory Polis, self-hosted in each region.** Polis (formerly BoxyHQ Jackson, Apache-2.0) accepts SAML or OIDC from the tenant's IdP and presents it to our app as an OAuth 2.0 / OIDC flow [R9][R10]. It runs as a separate ECS service per region (and Azure Container Apps where needed), using its own database in the regional Postgres cluster. The app therefore never parses SAML XML, which keeps signature-wrapping risk [R31] in one hardened, separately patched component. This answers the open question in [[PKG-sso-saml-oidc-per-tenant#questions]] ("self-hosted SAML-to-OIDC bridge per region").
4. **SCIM 2.0 server is ours**, as already specified at `/scim/v2` in each region ([[PKG-user-provisioning-scim#flows]], RFC 7644 [R30]), because deprovisioning must drive our memberships, grant epochs and Temporal workflows in the same transaction. Polis's directory-sync feature is not used.
5. **Nothing identity-related leaves the region.** OTP and magic links go through regional providers ([[INT-messaging-providers]]); IdP metadata and JWKS are fetched through the regional egress proxy.

**Why, against the drivers**

- **D1 residency:** everything runs in our own regional stacks, so India, Singapore, US and Azure are covered equally. Among managed providers, only Auth0 Private Cloud on AWS states it is deployable in India and Singapore [R20]; Auth0 public cloud, Entra External ID, Zitadel Cloud, Ory Network and Clerk do not offer India or Singapore storage [R19][R23][R7][R11][R25], and WorkOS publishes no regional residency option [R17][R18] (assumption: US-hosted).
- **D2 federation:** Polis gives SAML and OIDC federation without us maintaining an XML security stack; OIDC uses a certified library.
- **D3 SCIM and D7 one identity model:** our SCIM endpoint writes directly into memberships and role assignments; a separate identity server would hold a second user store that must be kept in sync with our memberships and RLS-protected tables.
- **D4 tenant policies:** the policy engine, report-only mode and simulator are our product features; an identity server's own flow engine would either duplicate them or have to defer to us.
- **D5 passkeys:** RP ID per tenant host is natural when our app serves sign-in. Hosted providers serve login on their own domain; for example Auth0 Organizations do not support custom domains per organization [R21], which would move the RP ID away from the tenant host.
- **D6 volume:** no per-user fees; SMS and WhatsApp budgets stay under our control.
- **D8 stack fit:** TypeScript and Prisma throughout; Polis is a TypeScript / Next.js service with Postgres support [R9].
- **D9 operations:** one small stateless service per region (Polis) instead of a full identity server cluster.
- **D10:** permissive licences (MIT, Apache-2.0); exit cost is low because the data model is ours.

**Fallback (named now):** if the spike shows Polis is unsuitable (for example a needed feature requires the Ory Enterprise License, see questions), run **Keycloak per region in broker-only mode** for SAML (Apache-2.0, CNCF incubating [R1][R2]), keeping everything else in `@nomology/auth`.

**Scope:** sign-in, sessions, step-up, federation, provisioning, external participant identity and API credentials for all tenants, all regions and Azure deployments. It does not cover authorisation ([[ADR-policy-engine]]), KYC providers, or Nomology's workforce IdP.

**Better Auth and Auth.js:** Auth.js is now maintained by the Better Auth team for security patches and urgent issues, and new projects are advised to start with Better Auth [R12], so Auth.js is not a candidate. Better Auth (MIT [R16]) is considered as option B: its SSO plugin (SAML 2.0 and OIDC with domain verification) [R14] and SCIM plugin [R15] are close to our needs, but its own user, session and organisation tables and session model would have to be bent to our regional user, tenant-owned membership and RLS model. It is not recommended as the core, but individual pieces may be studied in the spike.

<!-- section:consequences -->
## Consequences

| Stakeholder | Easier | Harder |
|---|---|---|
| Developers | One identity model in Prisma; `Principal`, `acr` and policies in our code; no second user store | We own session, step-up, passkey, OTP, SCIM and OIDC integration code, with its bugs; protocol edge cases (IdP quirks) land on us |
| Security lead | Full control of assurance, logging and residency; SAML parsing isolated in Polis | Authentication code is a high-value target we maintain; every change to `packages/auth` needs security review; annual pen test per region must cover it ([[TST-security-testing]]) |
| Platform / DevOps | One small service (Polis) per region; same deployment in India, Singapore, US and Azure | Polis upgrades and its database per region; patch SLA for auth dependencies |
| Tenants' admins | SSO, SCIM, policies and simulator in our console, with our terminology | Their IdP integration guides are ours to write and maintain |
| Parties and counsel | Sign-in on the tenant host; passkeys work there | Passkeys do not carry across tenant hosts (intended, [[PKG-mfa-session-management-device#policy]]) |
| Compliance | No new identity sub-processor; residency argument is simple | We must evidence our own control operation (no vendor SOC 2 to lean on for identity) |

**New failure modes**
- Polis down in a region: SAML sign-ins for that region fail; OIDC, passkey and local methods still work; break-glass admins keep passkey sign-in ([[PKG-sso-saml-oidc-per-tenant#policy]]).
- A vulnerability in a protocol library: we must patch all regions quickly (target below).
- Drift between Polis connection configuration and our versioned connection records: our connection record is the source of truth and is pushed to Polis on publish; a reconciler compares them nightly.

**Follow-up work (ticket under [[PKG-authentication]]):** Polis deployment module per region; connection-sync from our versioned connections to Polis; SAML conformance and XSW test vectors in CI; dependency patch SLA in [[DEP-ci-cd-pipelines-build-test]]; the identity spike below.

<!-- section:confirmation -->
## Confirmation

**Automated checks (blocking in CI)**
- SAML negative conformance vectors (unsigned assertion, wrong audience, expired, signature-wrapping variants, duplicate assertions) and OIDC negatives (missing PKCE, wrong `nonce` or `iss`, unverified email) against containerised test IdPs, through Polis ([[PKG-sso-saml-oidc-per-tenant#verification]]).
- Cross-tenant assertion test: an assertion valid for tenant A is rejected at tenant B's endpoint.
- SCIM conformance suite against `/scim/v2`, and a deprovision end-to-end test: deactivate in a test IdP → sessions rejected within 60 s → reassignment tasks created ([[PKG-user-provisioning-scim]]).
- Restricted imports: SAML XML libraries may not be imported anywhere in the monorepo (SAML only via Polis); credential and session tables only through `packages/auth`.
- Residency test: identity-related egress from each regional stack is limited to an allow-list (tenant IdPs, regional messaging providers, Singpass in Singapore); a deliberately disallowed destination must be blocked in the test.

**Measurable production checks**

| Metric | Target |
|---|---|
| Identity data outside home region | 0 records (quarterly evidence from data inventory and egress logs) |
| Session revocation after SCIM deactivation or admin revoke | p99 ≤ 60 s |
| Session check latency | p95 ≤ 3 ms from Redis, ≤ 10 ms on Postgres fallback (A) |
| SSO success rate per connection | ≥ 80 % over 15 minutes (alert below, per [[PKG-sso-saml-oidc-per-tenant]]) |
| Critical CVE in an auth dependency or Polis | Patched in every region within 72 hours |
| Pen test | No open high or critical authentication finding before go-live per region |

**Spike / proof of concept (3–4 weeks, India staging)**

1. Polis in one region with two test tenants on separate hosts; SAML from Entra ID, Okta and an ADFS-style IdP; OIDC from Entra ID; Singpass sandbox if available.
2. Passkeys with RP ID per tenant host, recording backup flags; device-bound key for an admin role.
3. SCIM from Entra ID provisioning to our `/scim/v2`: create, update, groups, deactivate.
4. Session layer with revocation versions under load.

| Exit criterion | Pass if |
|---|---|
| SAML conformance and XSW vectors | 100 % rejected as expected through Polis |
| Licence | Every Polis feature we use is available under Apache-2.0 without the Ory Enterprise License, confirmed in writing |
| Deactivation to session end | p99 ≤ 60 s |
| Residency | No identity traffic outside the region except allow-listed IdPs and providers |
| Effort | Re-estimated build effort ≤ 9 engineer-months |

If the licence or SAML criterion fails, switch SAML to the Keycloak broker-only fallback. If the effort criterion fails, reopen this ADR with option C (Keycloak as the identity server) and option F (Auth0 Private Cloud) quotes.

<!-- section:options -->
## Options considered

Option A is recommended. Figures marked (A) are **assumptions** for comparison, not quotes.

**1. Fit to the decision drivers**

| Option | D1 residency IN / SG / US | D2 SAML + OIDC per tenant | D3 SCIM | D4 tenant auth policies | D5 passkeys on tenant host | D7 one identity model |
|---|---|---|---|---|---|---|
| **A. `@nomology/auth` on libraries + Ory Polis per region (recommended)** | ✓ all, plus Azure (our stacks) | ✓ SAML via Polis [R9]; OIDC via certified `openid-client` [R27] | ✓ ours, as specified | ✓ ours | ✓ RP ID = tenant host [R28] | ✓ |
| **B. `@nomology/auth` on Better Auth** (SSO, SCIM, organisation, passkey plugins) | ✓ (library in our stacks) | ✓ SAML 2.0 and OIDC plugin with DNS domain verification and replay protection [R14] | ✓ plugin, Users and Groups, per-connection tokens [R15] | Partly: we build policies on top | ✓ | Partly: framework tables and session model to adapt to RLS and regional users (A) |
| **C. Keycloak per region** | ✓ self-hosted | ✓ native broker; Organizations link IdPs and route by email domain [R4] | ✓ SCIM API supported from 26.8 [R3] | Partly: Keycloak authentication flows; our rules would sit on top or be re-expressed (A) | Only if login runs on each tenant host (realm or hostname per tenant) (A) | ✗ second user store to sync |
| **D. Zitadel self-hosted per region** | ✓ self-hosted (Zitadel Cloud offers US, EU, Switzerland, Australia only [R7]) | ✓ SAML and OIDC | Partly: SCIM Users only; groups not supported [R6] | Partly (A) | As C (A) | ✗ second store |
| **E. Ory self-hosted (Kratos + Polis)** | ✓ self-hosted (Ory Network regions: US East, US West, EU Central [R11]) | SAML and SCIM are not in open-source Kratos; Enterprise License needed, or Polis alongside [R8] | Via Enterprise License or Polis | Partly (A) | As C (A) | ✗ second store |
| **F. Auth0 Private Cloud on AWS** (one dedicated deployment each in India, Singapore, US) | ✓ India and Singapore listed as deployable [R20]; public cloud regions are AU, CA, EU, JP, UK, US only [R19] | ✓ enterprise connections and Organizations [R21] | ✓ inbound SCIM for SAML, OIDC, Okta and Entra connections, Users and Groups [R22] | Partly: Actions and policies in Auth0; our rules on top (A) | ✗ no custom domain per organization [R21] | ✗ second store |
| **G. Managed multi-tenant SaaS: WorkOS, Entra External ID, Clerk** | ✗ WorkOS: no published residency option [R17][R18]; Entra External ID: geography "Asia Pacific", country storage (Go-Local) only Australia and Japan, MFA logs may be in North America [R23]; Clerk: US only [R25] | ✓ (WorkOS SSO; Entra self-service SAML/WS-Fed and OIDC federation [R24]; Clerk SAML [R26]) | ✓ (WorkOS Directory Sync; Clerk Directory Sync [R26]) | Partly | ✗ hosted login domain (A) | ✗ |

**2. Cost, operations, residency, skills, lock-in, maturity and licence**

| Option | Cost (A) | Operational burden per region: India / Singapore / US (+ Azure) | Team skills (TypeScript, Next.js, Prisma, Temporal) | Lock-in | Maturity | Licence |
|---|---|---|---|---|---|---|
| **A** | Infra: Polis 2 small tasks per region, about US$50–150/month each. Build: about 5–7 engineer-months initial; 0.3–0.5 FTE ongoing security maintenance | One stateless service per region plus our app; same pipeline everywhere | Native; Polis is TypeScript / Next.js | Low: our schema; Polis replaceable by Keycloak broker | Libraries mature; our own code is new and must be pen tested | MIT (`openid-client`, SimpleWebAuthn), Apache-2.0 (Polis) [R9]; check which Polis features need the Ory Enterprise License |
| **B** | Infra nil; build about 3–5 engineer-months, plus adaptation of framework schema | As A without Polis | Native | Medium: framework schema and plugin APIs | Young and fast-moving framework; joined Vercel in July 2026 [R13]; SAML relies on an upstream SAML library (A) | MIT [R16] |
| **C** | Infra: 2–3 Keycloak nodes plus database per region, about US$400–900/month each; integration 2–4 engineer-months; 0.5 FTE operations across regions | Java service clusters, upgrades, themes and realm configuration in four places; zero-downtime patch releases supported since 26.6 [R3] | New: Java, FreeMarker themes, Keycloak admin model | Medium: realm configuration and user store | Very mature; CNCF incubating since April 2023 [R2] | Apache-2.0 [R1] |
| **D** | Infra about US$200–500/month per region | Go service plus database per region | New | Medium | Mature product; licence changed to AGPL-3.0 for core, console and login from v3 (March 2025) [R5] | AGPL-3.0 core; APIs and SDKs Apache-2.0 [R5]; legal review needed |
| **E** | Infra about US$300–700/month per region, plus Enterprise License for SAML / SCIM in Kratos (A) | Several Go services (Kratos, Hydra) plus Polis | New | Medium | Mature components | Apache-2.0 open source; Enterprise License for SAML, SCIM and organization login [R8] |
| **F** | Contracted per deployment; three dedicated deployments (A: well above all self-hosted options; quote required) | Vendor-run; we still integrate and run our session layer | Low learning curve for OIDC; Auth0 Actions | High: users, connections, Actions and pricing | Very mature | Proprietary |
| **G** | WorkOS SSO and Directory Sync US$125 per connection per month at 1–15 connections [R17]; Entra and Clerk per active user | Vendor-run | Low | High | Mature | Proprietary |

**Why not the others**

- **G** fails the residency constraint for India and Singapore and is excluded regardless of features.
- **F** is the only managed option that meets residency, but costs three dedicated deployments, moves passkeys and login to a vendor domain, creates a second user store and still leaves our policy engine and session layer to build. Keep as the option to re-quote if build risk becomes unacceptable.
- **C** is the strongest self-hosted alternative and the named SAML fallback. As the full identity platform it duplicates our identity model, adds Java operations in four regions and fits poorly with tenant-host passkeys and our tenant-authored policies.
- **D** adds an AGPL obligation and lacks SCIM groups. **E** needs a commercial licence for exactly the parts we need.
- **B** is close; it loses on D7 (framework-owned schema and sessions against our RLS and regional user model) and maturity.

<!-- section:revisit -->
## When to revisit

- **Managed residency appears:** a managed provider publishes country-level storage for both India and Singapore (for example Entra External ID Go-Local expanding beyond Australia and Japan [R23], or Auth0 public cloud adding those regions [R19]) at acceptable cost.
- **Build risk:** a critical authentication vulnerability in our own code reaches production, or auth maintenance exceeds 0.5 FTE for two consecutive quarters.
- **Polis changes:** licence change, the features we need move to the Ory Enterprise License, or the project stops receiving security releases for six months.
- **New protocol demands** we cannot meet with libraries, for example inbound Shared Signals / CAEP for an institution contract ([[PKG-authentication-policies#policy]]), or a certified identity service required by a government client.
- **Scale:** more than 500 enterprise connections in one region, or external participant sign-ins beyond what the session layer handles within budget.
- **Azure-only client** that requires Microsoft Entra as the identity platform.
- **Cross-region identity:** a decision to share counsel identities across regions ([[PKG-authentication#questions]]) would change the model.
- **Scheduled review:** 12 months after acceptance, with spike results, incident history and maintenance effort.

<!-- section:questions -->
## Open questions

- [ ] Risk appetite: accept owning authentication code (with pen tests and certified libraries) rather than running Keycloak as the identity server or paying for three Auth0 Private Cloud deployments. (CTO)
- [ ] Should we obtain an Auth0 Private Cloud quote for India, Singapore and US now, as a priced fallback? (CTO)
- [ ] Do any current or contracted clients require Azure-only hosting or Entra as the identity platform? (CTO, sales)
- [ ] Confirm with Ory in writing which Polis features, if any, need the Ory Enterprise License. (Security)
- [ ] Breached-password check: k-anonymity service or offline corpus per region ([[PKG-email-password-magic-link-otp#questions]]). (Security, DPO)
- [ ] Record the security reviewer and date for this ADR. (Security lead)

<!-- section:notes -->
## More information

- **Refines:** the open "build vs self-host" question in [[PKG-authentication#questions]] and the SAML library question in [[PKG-sso-saml-oidc-per-tenant#questions]].
- **Consistent with:** [[ADR-tenant-isolation]] (identity tables tenant-owned with forced RLS; user records region-level), [[ADR-orm]] (Prisma for all identity tables; Polis has its own database and is not accessed by app code), [[ADR-container-orchestration]] and [[ADR-next-js-hosting]] (Polis is one more regional service), [[ADR-temporal]] (deprovision workflow).
- **Related proposed decisions:** [[ADR-policy-engine]] consumes the `Principal`; [[ADR-expression-and-rules-language]] should also govern the attribute-mapping expressions on SSO connections ([[PKG-sso-saml-oidc-per-tenant#policy]]).
- Residency facts per provider were checked against official documentation in October 2026 and may change; re-check at each revisit.

<!-- checks -->
## Template checks

<!-- check:significance -->
### Significance

Significant: every persona and API depends on it, it holds the most sensitive personal data and credentials, it is the first thing institutions ask about in security questionnaires, and residency in India and Singapore is contractual. Reversing it after launch means migrating credentials (passkeys cannot be exported between relying parties) and re-federating every tenant IdP: estimated 2–3 engineer-months at 6 months and 4–6 at 18 months (assumption). One decision: where and on what authentication runs. Out of scope: authorisation, KYC providers and Nomology's workforce IdP. The context is phrased neutrally across build, self-host and managed.

<!-- check:options -->
### Options and evidence

Seven options are compared against ten drivers in two tables: libraries plus Polis, Better Auth, Keycloak, Zitadel, Ory, Auth0 Private Cloud, and managed SaaS (WorkOS, Entra External ID, Clerk, with Auth0 public cloud regions noted). The tables cover cost, operational burden per region, residency, team skills, lock-in, maturity and licence. Residency, licence and SAML / SCIM facts cite official documentation [R1]–[R31]; costs and effort are labelled assumptions. Auth.js is excluded because it is in maintenance [R12]. The spike tests the decisive assumptions (Polis licence and conformance, revocation timing, effort). The option fits Prisma, forced RLS, Temporal and ECS / Azure Container Apps with no conflict with approved ADRs.

<!-- check:compliance -->
### Regulatory, residency and tenancy fit

- **Residency:** all identity data, sessions, SSO configuration, SCIM data and authentication events stay in the tenant's regional stack; Polis runs per region with an in-region database; managed options without India and Singapore storage are excluded (D1).
- **Isolation:** identity tables follow [[ADR-tenant-isolation]]; Polis stores connection data per tenant in its own regional database, so tenant separation there relies on Polis tenant and product keys, not RLS; the connection record in our RLS-protected tables stays the source of truth and Polis is reachable only from the app's private network.
- **Sub-processors:** none added for identity (self-hosted); regional messaging providers and IdPs are unchanged ([[SEC-vendor-sub-processor-management]]).
- **Controls:** ISO/IEC 27001:2022 Annex A 5.16, 5.17, 5.18, 8.2 and 8.5; SOC 2 CC6.1–CC6.3; DPDP and PDPA security safeguards; NIST SP 800-63B-4 assurance levels as design reference [R29].
- **Audit:** authentication events recorded per [[PKG-authentication]] in the regional audit trail ([[PKG-audit-trail]]).
- **Review:** security reviewer, DPO and date to be recorded before acceptance.

<!-- check:consequences -->
### Consequences and costs

Downsides are stated per stakeholder: we own and must patch authentication code, Polis is a new regional service, IdP integration guides are ours, and there is no vendor SOC 2 report to rely on for identity. New failure modes (Polis outage, library vulnerability, configuration drift) have named mitigations. Costs are estimated as assumptions per region and in engineer-months, and follow-up work is listed for ticketing.

<!-- check:reversibility -->
### Reversibility and revisit triggers

Signals: the production metrics (revocation, SSO success, patch SLA, pen test findings) and the revisit triggers. Exit paths: replace Polis with Keycloak broker-only (weeks, configuration only, because connection records are ours); move to a managed provider with regional residency (months: re-federate tenant IdPs and re-enrol passkeys, since passkeys are bound to the tenant host). Kept reversible now by owning the data model and the versioned connection records, using standard protocols (OIDC, SAML, SCIM) at every boundary, and keeping SAML behind a bridge. Scheduled review 12 months after acceptance.

<!-- check:confirmation -->
### Confirmation

Blocking CI checks: SAML and OIDC negative conformance suites through Polis, cross-tenant assertion test, SCIM conformance and deprovision end-to-end test, restricted imports for SAML libraries, and an egress residency test with a deliberately blocked destination. Production targets for residency, revocation, session latency, SSO success, patch SLA and pen tests. A 3–4 week spike with exit criteria and a named fallback. Exceptions go through [[FND-governance]].

<!-- check:linked -->
### Linked and lifecycle

Governs [[PKG-authentication]], [[PKG-email-password-magic-link-otp]], [[PKG-sso-saml-oidc-per-tenant]], [[PKG-domain-verification]], [[PKG-mfa-session-management-device]], [[PKG-accessible-authentication-and]], [[PKG-authentication-policies]], [[PKG-user-provisioning-scim]], [[PKG-external-party-identity]], [[PKG-api-clients-and-keys]], [[PKG-settings-security-and-identity]], [[MT-tenancy-and-identity-schema]], [[APP-public-and-sign-in-surfaces]], [[APP-tenant-admin-console]], [[APP-user-and-access-admin]], [[INT-public-api-and-webhooks]], [[INT-api-platform-tables]]; infrastructure [[INF-secrets-and-keys]], [[INF-redis]], [[PKG-encryption-utilities-key]], [[INT-messaging-providers]]; controls [[OBS-security-events]], [[PKG-audit-trail]], [[TST-security-testing]], [[SEC-vendor-sub-processor-management]], [[MT-data-residency-2]]. Related: [[ADR-tenant-isolation]], [[ADR-orm]], [[ADR-container-orchestration]], [[ADR-next-js-hosting]], [[ADR-temporal]], [[ADR-policy-engine]], [[ADR-expression-and-rules-language]]. Governed nodes should add 'Decided by [[ADR-identity-platform]]' and close their build-vs-host question. Status: Proposed; deciders: CTO with security lead and DPO; consulted: platform engineering, product; informed: sales and tenant onboarding. No superseded records.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Apache License 2.0; Java.",
    "id": "R1",
    "kind": "vendor",
    "title": "keycloak/keycloak repository",
    "url": "https://github.com/keycloak/keycloak",
    "vendor": "Keycloak (CNCF)"
  },
  {
    "body": "Cloud Native Computing Foundation",
    "excerpt": "CNCF TOC accepted Keycloak as an incubating project (11 April 2023).",
    "id": "R2",
    "kind": "web",
    "title": "Keycloak joins CNCF as an incubating project",
    "url": "https://www.cncf.io/blog/2023/04/11/keycloak-joins-cncf-as-an-incubating-project/"
  },
  {
    "excerpt": "26.8.0: SCIM API moved from preview to supported; IdP can link to multiple organizations; multi-cluster v2 supported. 26.6.0: zero-downtime patch releases supported.",
    "id": "R3",
    "kind": "vendor",
    "title": "Keycloak release notes (26.x)",
    "url": "https://www.keycloak.org/docs/latest/release_notes/index",
    "vendor": "Keycloak"
  },
  {
    "excerpt": "Organizations within a realm; IdP linked to an organization; redirect when email domain matches.",
    "id": "R4",
    "kind": "vendor",
    "title": "Support for CIAM and multi-tenancy: Keycloak Organizations",
    "url": "https://www.keycloak.org/2024/06/announcement-keycloak-organizations",
    "vendor": "Keycloak"
  },
  {
    "excerpt": "From v3.0 (March 2025) core, console and hosted login are AGPL-3.0; APIs, SDKs and proto definitions stay Apache-2.0.",
    "id": "R5",
    "kind": "vendor",
    "title": "Strengthening Our Open Source Foundation: Moving to AGPL 3.0",
    "url": "https://zitadel.com/blog/apache-to-agpl",
    "vendor": "Zitadel"
  },
  {
    "excerpt": "Supports only the SCIM core User schema; group provisioning and extended schemas are not supported.",
    "id": "R6",
    "kind": "vendor",
    "title": "Zitadel docs: SCIM v2.0",
    "url": "https://zitadel.com/docs/guides/manage/user/scim2",
    "vendor": "Zitadel"
  },
  {
    "excerpt": "Data regions: United States, European Union, Switzerland, Australia.",
    "id": "R7",
    "kind": "vendor",
    "title": "Where is Zitadel Cloud data stored?",
    "url": "https://help.zitadel.com/where-is-zitadel-cloud-data-stored",
    "vendor": "Zitadel"
  },
  {
    "excerpt": "Apache-2.0, Go; SAML, SCIM and organization login are Ory Enterprise License features, not in the open-source version.",
    "id": "R8",
    "kind": "vendor",
    "title": "ory/kratos repository",
    "url": "https://github.com/ory/kratos",
    "vendor": "Ory"
  },
  {
    "excerpt": "Apache-2.0; SAML and OIDC SSO presented as OAuth 2.0; SCIM 2.0 directory sync; Postgres among supported databases; self-hosted Next.js service or NPM library; Enterprise License required for some features.",
    "id": "R9",
    "kind": "vendor",
    "title": "ory/polis repository (formerly BoxyHQ Jackson)",
    "url": "https://github.com/ory/polis",
    "vendor": "Ory"
  },
  {
    "excerpt": "Enterprise SSO service for SAML and OIDC IdPs exposed as an OAuth 2.0 flow; open source, self-hostable, bring your own database.",
    "id": "R10",
    "kind": "vendor",
    "title": "Introduction to Ory Polis",
    "url": "https://ory.com/docs/polis",
    "vendor": "Ory"
  },
  {
    "excerpt": "Regions US East, US West and EU Central (June 2024); multi-region on Enterprise plans.",
    "id": "R11",
    "kind": "vendor",
    "title": "Ory changelog: Self-service region selection and multi-region deployments",
    "url": "https://changelog.ory.com/announcements/self-service-region-selection-and-multi-region-deployments",
    "vendor": "Ory"
  },
  {
    "excerpt": "22 September 2025: Auth.js continues with security patches and urgent fixes; new projects advised to start with Better Auth.",
    "id": "R12",
    "kind": "vendor",
    "title": "Auth.js is now part of Better Auth",
    "url": "https://www.better-auth.com/blog/authjs-joins-better-auth",
    "vendor": "Better Auth"
  },
  {
    "excerpt": "7 July 2026 announcement; commitment to keep auth open source and framework agnostic.",
    "id": "R13",
    "kind": "vendor",
    "title": "Better Auth joins Vercel",
    "url": "https://better-auth.com/blog/better-auth-joins-vercel",
    "vendor": "Better Auth"
  },
  {
    "excerpt": "SAML 2.0 and OIDC providers; DNS TXT domain verification; organization linking; InResponseTo validation, assertion replay protection, clock skew and algorithm checks.",
    "id": "R14",
    "kind": "vendor",
    "title": "Better Auth docs: Single Sign-On (SSO) plugin",
    "url": "https://better-auth.com/docs/plugins/sso",
    "vendor": "Better Auth"
  },
  {
    "excerpt": "Inbound SCIM 2.0 (RFC 7643/7644) for Users and Groups with per-connection credentials; requires adapter with interactive transactions.",
    "id": "R15",
    "kind": "vendor",
    "title": "Better Auth docs: SCIM plugin",
    "url": "https://better-auth.com/docs/plugins/scim",
    "vendor": "Better Auth"
  },
  {
    "excerpt": "MIT licence.",
    "id": "R16",
    "kind": "vendor",
    "title": "better-auth/better-auth repository",
    "url": "https://github.com/better-auth/better-auth",
    "vendor": "Better Auth"
  },
  {
    "excerpt": "SSO and Directory Sync US$125 per connection per month for 1-15 connections, tiered down to US$65 at 51-100; AuthKit free up to 1 million MAU; no data residency or region options listed.",
    "id": "R17",
    "kind": "vendor",
    "title": "WorkOS Pricing",
    "url": "https://workos.com/pricing",
    "vendor": "WorkOS"
  },
  {
    "excerpt": "SOC 2 Type 2, GDPR and CCPA; no hosting regions or residency options stated.",
    "id": "R18",
    "kind": "vendor",
    "title": "WorkOS Security",
    "url": "https://workos.com/security",
    "vendor": "WorkOS"
  },
  {
    "excerpt": "Public cloud tenant regions: Australia, Canada, Europe, Japan, United Kingdom, United States.",
    "id": "R19",
    "kind": "vendor",
    "title": "Auth0 docs: Create Tenants",
    "url": "https://auth0.com/docs/get-started/auth0-overview/create-tenants.md",
    "vendor": "Auth0 (Okta)"
  },
  {
    "excerpt": "Lists countries where Private Cloud on AWS is fully deployable, including India and Singapore; single-tenant Basic and Performance tiers; contract and onboarding required.",
    "id": "R20",
    "kind": "vendor",
    "title": "Auth0 docs: Private Cloud on AWS",
    "url": "https://auth0.com/docs/deploy-monitor/deploy-private-cloud/private-cloud-on-aws.md",
    "vendor": "Auth0 (Okta)"
  },
  {
    "excerpt": "Per-organization connections, branding and roles; no custom domains per organization; organizations needing their own domains require separate tenants.",
    "id": "R21",
    "kind": "vendor",
    "title": "Auth0 docs: Understand how Auth0 Organizations work",
    "url": "https://auth0.com/docs/manage-users/organizations/organizations-overview",
    "vendor": "Auth0 (Okta)"
  },
  {
    "excerpt": "Inbound SCIM for SAML, OIDC, Okta Workforce and Entra ID connections; requires Enterprise Connections in plan; Groups supported with user members.",
    "id": "R22",
    "kind": "vendor",
    "title": "Auth0 docs: Configure Inbound SCIM",
    "url": "https://auth0.com/docs/authenticate/protocols/scim/configure-inbound-scim",
    "vendor": "Auth0 (Okta)"
  },
  {
    "excerpt": "Geo locations include Asia/Pacific; Go-Local country storage for external tenants only in Australia and Japan; MFA logs may be stored in North America; location cannot be changed after creation.",
    "id": "R23",
    "kind": "vendor",
    "title": "Microsoft Entra ID and data residency",
    "url": "https://learn.microsoft.com/en-us/entra/fundamentals/data-residency",
    "vendor": "Microsoft"
  },
  {
    "excerpt": "SAML/WS-Fed and OIDC federation for self-service sign-up; passkeys; custom URL domains; limited Conditional Access in external tenants.",
    "id": "R24",
    "kind": "vendor",
    "title": "Supported features in external tenants (Entra External ID)",
    "url": "https://learn.microsoft.com/en-us/entra/external-id/customers/concept-supported-features-customers",
    "vendor": "Microsoft"
  },
  {
    "excerpt": "US-hosted on Google Cloud and Cloudflare; no regional data residency; SOC 2 Type 2.",
    "id": "R25",
    "kind": "vendor",
    "title": "Clerk Security and Compliance at a Glance",
    "url": "https://clerk.com/security.md",
    "vendor": "Clerk"
  },
  {
    "excerpt": "SCIM 2.0 directory sync on top of SAML or OIDC enterprise connections; Pro or Business plan in production.",
    "id": "R26",
    "kind": "vendor",
    "title": "Clerk docs: Directory Sync (SCIM)",
    "url": "https://clerk.com/docs/guides/configure/auth-strategies/enterprise-connections/directory-sync",
    "vendor": "Clerk"
  },
  {
    "excerpt": "MIT; OpenID Certified for Basic, FAPI 1.0 and FAPI 2.0 relying-party profiles; PKCE, PAR and DPoP.",
    "id": "R27",
    "kind": "vendor",
    "title": "openid-client repository",
    "url": "https://github.com/panva/openid-client",
    "vendor": "panva"
  },
  {
    "excerpt": "MIT; @simplewebauthn/server and @simplewebauthn/browser packages for WebAuthn.",
    "id": "R28",
    "kind": "vendor",
    "title": "SimpleWebAuthn repository",
    "url": "https://github.com/MasterKale/SimpleWebAuthn",
    "vendor": "SimpleWebAuthn"
  },
  {
    "body": "NIST",
    "excerpt": "Syncable authenticators are not permitted at AAL3 because their keys are exportable.",
    "id": "R29",
    "kind": "standard",
    "title": "NIST SP 800-63B-4 Digital Identity Guidelines: Authentication and Authenticator Management",
    "url": "https://pages.nist.gov/800-63-4/sp800-63b.html"
  },
  {
    "body": "IETF",
    "excerpt": "SCIM 2.0 protocol.",
    "id": "R30",
    "kind": "standard",
    "title": "RFC 7644 System for Cross-domain Identity Management: Protocol",
    "url": "https://www.rfc-editor.org/rfc/rfc7644"
  },
  {
    "body": "OWASP",
    "excerpt": "XML signature wrapping attacks and defences for SAML implementations.",
    "id": "R31",
    "kind": "standard",
    "title": "OWASP SAML Security Cheat Sheet",
    "url": "https://cheatsheetseries.owasp.org/cheatsheets/SAML_Security_Cheat_Sheet.html"
  }
]
```

<!-- end -->
