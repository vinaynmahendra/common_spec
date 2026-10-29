---
id: "PKG-authentication-policies"
title: "Tenant authentication policies"
parent: "PKG-authentication"
order: 6
type: "feature"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "Conditional-access style rules per tenant, persona, role and unit: required authentication strength, step-up per action class, session bounds, network zones, device trust and risk, with report-only mode, simulation, lock-out protection and strictest-wins evaluation under platform floors"
links: []
rev: 1
syncHash: "a67157b8d2139a9c"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.1.6 Tenant authentication policies

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Conditional-access style rules per tenant, persona, role and unit: required authentication strength, step-up per action class, session bounds, network zones, device trust and risk, with report-only mode, simulation, lock-out protection and strictest-wins evaluation under platform floors

<!-- section:purpose -->
## Purpose and scope

Tenant authentication policies decide, for every sign-in, session refresh and sensitive action, **which proof of identity is enough**, given who the person is, what they are trying to reach, and the circumstances (network, device, risk). They turn the method catalogue in [[PKG-authentication]] into rules a tenant's `security_admin` can author without code, within platform floors.

What it protects: every persona surface (route groups in [[APP-route-groups-per-persona]]), the tenant admin console, and consequential actions (filing, issuing an award, approving fees, payments, bank detail changes, exports, role and security changes).

Who relies on it: the session layer ([[PKG-mfa-session-management-device]]) asks the policy engine at sign-in, at each session refresh and at step-up; authorisation ([[PKG-authorization]]) trusts the resulting `acr` and session flags; the access explainer ([[PKG-access-explainer]]) and the admin copilot ([[APP-admin-copilot]]) use the same evaluation function in "what if" mode.

Boundary: authentication policies decide **how strongly someone must prove who they are**. What they may do once proven is authorisation ([[PKG-policy-engine-permission-matrix]]); the numeric defaults these rules refine live in [[PKG-settings-security-and-identity]].

Pattern borrowed from: Microsoft Entra Conditional Access (assignments, conditions, grant controls, report-only mode) [R4], its named authentication strengths [R5], and Okta Identity Engine global session and authentication policies with ordered rules [R6][R7]. Requirements below describe our behaviour only.

<!-- section:assets -->
## Protected assets

| Asset | Classification ([[SEC-data-classification]]) | Why it matters |
|---|---|---|
| Authentication policy definitions and versions (`auth_policy`, `auth_policy_rule`) | Internal, integrity-critical | A weakened rule silently lowers assurance for a whole persona |
| Authentication strengths (`auth_strength`) | Internal, integrity-critical | Redefining a strength changes every rule that references it |
| Network zones (`network_zone`: CIDR lists, countries) | Internal | Reveal tenant office networks; wrong zone locks out staff |
| Policy evaluation records (`auth_policy_decision`) | Personal (IP, device, location country) | Evidence of why access was allowed; DPDP and PDPA minimisation applies |
| Session flags set by policy (`acr`, `deviceTrust`, `networkZoneId`, `riskLevel`) | Confidential | Downstream authorisation trusts them |
| Exclusions and break-glass exemptions | Confidential, high privilege | The most common path to bypassing a policy |

<!-- section:actors -->
## Actors and roles

| Actor (role key) | Interaction with policies | How the role is acquired |
|---|---|---|
| `security_admin` | Authors, simulates and submits policies; approves another admin's policy | Assigned by `tenant_owner` (maker-checker) |
| `tenant_owner` | Approves policies when only one `security_admin` exists; holds a break-glass exemption by default | Set at tenant onboarding ([[APP-tenant-onboarding-wizard]]) |
| `tenant_admin`, `user_admin`, `auditor` | Read policies and decision logs; cannot edit | Tenant role assignment |
| `unit_admin` | May add unit-scoped rules that only tighten (for example a shorter session for the SEBI ODR desk) | Tenant role assignment, unit-scoped |
| `platform_security` | Owns the platform floor policy and region overlays; can apply an emergency tightening to a tenant | Nomology workforce IdP group |
| `platform_support` | Reads a tenant's policies and decision logs only under a support grant ([[PKG-support-access-and-impersonation]]) | Support grant |
| All signed-in principals | Are evaluated; see the outcome (prompt, block message) | — |
| `service_account`, `ai_agent`, `integration_connection` | Not evaluated by interactive policies; credential policies apply ([[PKG-api-clients-and-keys]], [[PKG-non-human-principals]]) | — |

<!-- section:matrix -->
## Permission matrix

Permission keys are proposed for [[PKG-permission-catalogue]]. ✓ allowed, ✗ denied, "T" own tenant, "U" own unit, "G" under support grant.

| Action | Permission | `security_admin` | `tenant_owner` | `tenant_admin` | `unit_admin` | `auditor` | `platform_security` | `platform_support` | Others |
|---|---|---|---|---|---|---|---|---|---|
| View policies, strengths, zones | `auth.policy:read` | T | T | T | U | T | ✓ | G | ✗ |
| Create or edit draft policy / rule | `auth.policy:update` | T | T | ✗ | U (tighten-only rules) | ✗ | ✓ (platform and region policies) | ✗ | ✗ |
| Run what-if simulation | `auth.policy:read` | T | T | T | U | T | ✓ | G | ✗ |
| Approve a policy change (not own) | `auth.policy:approve` | T | T | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Publish approved policy (switch from report-only to enforced) | `auth.policy:publish` | T | T | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Manage network zones | `auth.network_zone:update` | T | T | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Define a custom authentication strength | `auth.strength:create` | T | T | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Add exclusion (user or group exempt from a rule) | `auth.policy:update` + approval | T, max 30 days, reason | T | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Emergency tightening of a tenant (force MFA, revoke sessions) | `platform.tenant.security:configure` | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ two-person, tenant notified within 1 h | ✗ | ✗ |
| Read decision log | `auth.policy_decision:list` | T | T | T | U | T | ✓ | G | own sign-ins only (via sign-in history) |
| Export decision log | `auth.policy_decision:export` | T (step-up) | T (step-up) | ✗ | ✗ | T (step-up) | ✓ | ✗ | ✗ |

No tenant role can edit the platform floor or region overlay; they are shown read-only with a lock.

<!-- section:policy -->
## Policy model

**Model.** A tenant has one ordered **authentication policy** per surface class, each made of rules; the platform has a floor policy and a region overlay that are evaluated first and cannot be overridden.

| Concept | Meaning |
|---|---|
| Surface class | `sign_in` (session creation and refresh), `step_up` (consequential action), `admin_console` (any `/admin/...` route), `api_admin` (reserved, non-interactive; see [[PKG-api-clients-and-keys]]) |
| Assignment | Who the rule applies to: persona keys, role keys, tenant groups, units, case roles (for `step_up` only), or "all"; plus exclusions |
| Conditions | Network zone in / not in; country; device trust (`unknown`, `remembered`, `managed`); sign-in risk (`low`, `medium`, `high`) from [[PKG-input-sanitisation-csrf-rate]] signals and impossible-travel; authentication method already used; client type (`browser`, `mobile_browser`); time since last sign-in |
| Grant controls | `allow`; `require_strength(<strength>)`; `require_managed_device`; `require_reauth_every(<minutes>)`; `set_session(idle, absolute)` within bounds; `deny` with a message key |
| Authentication strength | Named set of acceptable method combinations, e.g. `strength.any` (any allowed first factor, `aal1`), `strength.mfa` (`aal2`), `strength.phishing_resistant` (passkey or security key, `aal2-phr`), `strength.device_bound` (security key or platform authenticator with attestation from the AAGUID allow-list, `aal3`), `strength.sso_mfa` (IdP-asserted MFA mapped by [[PKG-sso-saml-oidc-per-tenant]]) |
| Action class (for `step_up`) | `consequential`, `financial`, `export`, `admin_security`; each consequential operation in [[PKG-permission-catalogue]] carries one class |
| Mode | `report_only` (evaluated, logged, not enforced) or `enforced`; new rules start in `report_only` for `auth.policy.new_rules_report_only_days` |

**Evaluation order** (function `evaluateAuthPolicy(ctx)` in `packages/auth/policy`, pure and deterministic):
1. Platform floor (code) — for example, administrative roles need `strength.mfa`; Nomology staff need `strength.device_bound` via workforce SSO.
2. Region overlay (platform-managed data) — for example blocked countries.
3. Tenant rules for the surface class, in priority order; **all matching rules apply and the strictest requirement wins** (deny > require device > strongest strength > shortest session). There is no "first match wins", so adding a rule can never weaken another.
4. Unit rules (tighten-only, validated at save).
5. Result: `{ decision: allow | challenge | deny, requiredStrength, sessionBounds, reasons[], policyVersion }`.

```ts
type AuthContext = {
  tenantId: string; region: 'in' | 'sg' | 'us'; surface: 'sign_in' | 'step_up' | 'admin_console';
  principal?: { userId: string; personas: Persona[]; roles: RoleKey[]; groups: string[]; units: string[]; caseRoles?: CaseRoleKey[] };
  session?: { acr: Acr; amr: Amr[]; authTime: Date; lastStepUpAt?: Date; deviceTrust: 'unknown' | 'remembered' | 'managed' };
  network: { ipHash: string; zoneIds: string[]; country: string };  // zone match done before hashing
  risk: 'low' | 'medium' | 'high'; actionClass?: ActionClass;
};
```

**Compilation and caching.** Publishing a policy compiles it to a JSON decision structure stored in `auth_policy_version.compiled` and cached in the regional cache Redis under `authpol:{tenantId}:{version}`; sessions record the policy version they were evaluated under. On publish, the tenant's `auth_policy_epoch` is bumped; on each request the session layer compares epochs and re-evaluates (a session that no longer satisfies the policy gets a `challenge`, or is ended if the decision is `deny`).

**Lock-out protection.** Publish is refused if the simulator shows that the publishing admin, or every holder of a break-glass exemption, would be denied; break-glass exemptions are limited to two accounts per tenant, need `strength.device_bound`, and every use alerts all tenant owners.

**Data model** (tenant-owned, forced RLS, details for [[PKG-authorization-data-model]] and [[PKG-settings-data-model]]): `auth_policy(id, tenant_id, surface, name, status)`, `auth_policy_version(id, tenant_id, policy_id, version, state, compiled jsonb, author_id, approver_id, published_at)` following [[PKG-configuration-lifecycle]] states; `auth_policy_rule(id, tenant_id, policy_version_id, priority, assignment jsonb, conditions jsonb, grant jsonb, mode, expires_at)`; `auth_strength(id, tenant_id NULL for platform strengths, key, combinations jsonb)`; `network_zone(id, tenant_id, name, cidrs cidr[], countries text[], kind)`; `auth_policy_decision` (partitioned daily, 90-day retention in the tenant's region) holding decision, reasons, rule IDs, policy version, session ID and hashed IP.

**Example rules (SEBI ODR institution blueprint)**

| # | Surface | Assignment | Conditions | Grant |
|---|---|---|---|---|
| 1 | `admin_console` | all administrative roles | any | `require_strength(strength.phishing_resistant)`, session idle 15 min |
| 2 | `sign_in` | `secretariat` | network not in zone "Mumbai office" | `require_strength(strength.mfa)`, `require_reauth_every(480)` |
| 3 | `sign_in` | `party` | risk `high` | `require_strength(strength.mfa)` (email OTP acceptable for parties as second step) |
| 4 | `step_up` | `neutral` with case role `presiding_neutral` | action class `consequential` | `require_strength(strength.phishing_resistant)` |
| 5 | `sign_in` | all | country in region blocked list | `deny` (`auth.deny.country`) |

**Continuous signals.** Assumption: inbound OpenID Shared Signals / CAEP events from tenant IdPs (session revoked, credential change) are a later phase; until then IdP-side changes are picked up at the next SSO session refresh or SCIM call ([[PKG-user-provisioning-scim]]).

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat | Scenario | Mitigation | Residual |
|---|---|---|---|---|---|
| T1 | E | Policy weakened by a compromised admin | Attacker with a `security_admin` session removes MFA for secretariat | Maker-checker on weakening changes, phishing-resistant step-up to author and approve, notification to all owners, strictest-wins evaluation, platform floor in code | Low |
| T2 | E | Exclusion used as permanent bypass | Admin exempts a group "temporarily" and forgets | Exclusions expire (≤ 30 days), need a reason, appear in [[SEC-access-reviews]] and the weekly security digest | Low |
| T3 | D | Self-inflicted lock-out | Zone rule excludes the office's new IP range | Simulator check against the publishing admin and break-glass accounts, report-only period, one-click rollback, platform support can restore the previous version under a grant | Low |
| T4 | S | IP spoofing to satisfy a zone | Attacker sets `X-Forwarded-For` to an office IP | Client IP taken only from the edge (CDN/WAF) header set by [[INF-networking]], never from the request; zones are a condition that can only add requirements for staff, never remove MFA for admins | Low |
| T5 | S | Forged managed-device signal | User sets a device claim in a self-hosted IdP | Device signal accepted only from a verified tenant connection with signed assertions; client-certificate option uses tenant-uploaded CA | Medium (depends on tenant IdP hygiene) |
| T6 | T | Policy cache poisoning or stale cache | Old compiled policy served after a tightening | Cache key includes version; epoch check on every request; Postgres fallback | Very low |
| T7 | I | Decision log reveals behaviour patterns | Admin profiles a neutral's locations | Logs store country and zone match, hashed IP; access needs `auth.policy_decision:list`; reads of another user's decisions are audited | Low |
| T8 | R | Dispute over whether policy was met | "I signed the award without MFA" | Session and step-up records carry policy version and rule IDs; audit hash chain | Low |

<!-- section:failure -->
## Denial behaviour

- **Challenge**: the UI shows what is needed in plain language ("Your organisation requires a security key for this action") with the method picker filtered to methods that satisfy the strength; the API returns `401` problem type `auth/step-up-required` with `required_acr` and `required_strength` ([[APP-api-error-catalogue-problem]]).
- **Deny**: a tenant-branded page with a message key chosen by the rule (copy from [[APP-error-message-catalogue]]), a correlation ID and the tenant's help contact; it never names the zone, the rule or the risk signal (avoids teaching the attacker), and never reveals whether the account exists.
- **Not enrolled**: if the required strength needs a factor the user lacks, and the rule allows enrolment-on-demand, the user is taken to enrolment after satisfying the strongest factor they have; otherwise deny with "Contact your administrator to set up a security key".
- **Logged**: every challenge and deny writes `auth_policy_decision` and the security event `nomo.sec.authn_policy_denied` ([[OBS-security-events]]) with rule IDs and policy version; report-only rules log `would_deny` / `would_challenge`.

<!-- section:requirements -->
## Security requirements

ASVS references are to OWASP ASVS **5.0** at section level [R1][R2]; requirement-level IDs are filled in when text is checked against the 5.0.0 release.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| APOL-FR-1 | The platform shall evaluate the platform floor, region overlay, tenant rules and unit rules on every session creation, session refresh, admin console request and consequential action, and shall apply the strictest result of all matching rules. | V6.1, V8.1 |
| APOL-FR-2 | A tenant rule shall never lower a requirement set by the platform floor or region overlay; the editor shall reject such a rule at save time. | V6.1 |
| APOL-FR-3 | Policy changes shall follow the configuration lifecycle, and any change that weakens a requirement shall need approval from a second holder of `auth.policy:approve`. | V8.2 |
| APOL-FR-4 | New or changed rules shall run in report-only mode for the configured period before enforcement, unless the change only tightens and the author chooses immediate enforcement. | — |
| APOL-FR-5 | Publishing shall be refused when simulation shows that the publishing admin or all break-glass accounts would be denied. | V6.4 |
| APOL-FR-6 | Exclusions shall have an expiry of at most 30 days, a reason and an approver, and shall be listed in access reviews. | V8.2 |
| APOL-FR-7 | When a policy is published, existing sessions shall be re-evaluated on their next request and challenged or ended if they no longer comply. | V7.4 |
| APOL-FR-8 | The client IP used for network conditions shall come only from the trusted edge header, and IPs shall be stored only as keyed hashes in decision records. | V16.2 |
| APOL-FR-9 | Authentication strengths shall map to assurance values `aal1`, `aal2`, `aal2-phr` and `aal3`, and `strength.phishing_resistant` shall always be available as an option at `aal2` [R3]. | V6.5 |
| APOL-FR-10 | Each consequential operation shall declare an action class, and a CI test shall fail if a consequential operation has no step-up policy coverage. | V7.5 |
| APOL-FR-11 | A what-if simulator shall return the decision, the matching rules and the reasons for any user, surface, network and device input, using the same evaluation code as enforcement. | — |
| APOL-FR-12 | Every challenge, deny and report-only would-deny shall be recorded with the rule IDs and policy version, and kept for 90 days in the tenant's region. | V16.3 |
| APOL-FR-13 | Deny responses shall not disclose the rule, zone or risk signal that caused them. | V16.5 |
| APOL-FR-14 | Session lengths set by rules shall stay within the bounds of `auth.session.*` in [[PKG-settings-security-and-identity]] and the reauthentication limits for the assurance level [R3]. | V7.3 |

<!-- section:verification -->
## Verification

- **Unit (property-based)**: `evaluateAuthPolicy` with generated rule sets proves strictest-wins, floor dominance and determinism; adding a rule never produces a weaker decision.
- **Integration**: publish a tightening and assert existing sessions are challenged on next request; epoch bump visible within 60 seconds across web containers; Redis outage falls back to Postgres.
- **Lock-out tests**: zone change that excludes the author is refused; break-glass accounts always pass.
- **Coverage test**: generated from [[PKG-permission-catalogue]] — every operation with an action class has a step-up rule in the platform floor.
- **E2E (Playwright)**: per blueprint, sign-in as each persona from inside and outside a zone, with and without passkey, and check prompts and denials; report-only rules log but do not block.
- **Pen test**: header spoofing for IP, device-claim forgery through a test IdP, race between policy publish and in-flight session refresh ([[TST-security-testing]]).

<!-- section:questions -->
## Open questions

- [ ] Which IdP device signals will we accept for `managed` (for example an Entra device compliance claim passed through OIDC, or only client certificates)? (Security)
- [ ] Do we need inbound Shared Signals / CAEP from tenant IdPs in phase 1 for any institution contract? (Security, Product)
- [ ] Sign-in risk scoring: in-house signals only, or a bot/risk provider in each region (data leaves the request path)? (Security, DPO)
- [ ] Should `unit_admin` be allowed to author tighten-only rules, or only request them? (Product)
- [ ] Retention of `auth_policy_decision` (90 days proposed) vs tenant contracts asking for 1 year. (DPO, Security)
- [ ] Do Indian government programme tenants require compliance with specific government security guidelines on admin network restrictions? Assumption: yes for some; legal to confirm per tenant.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Policies, rules, zones, strengths and decision records are tenant-owned rows under forced RLS; the evaluator receives `tenantId` from the resolved host and session only. Platform floor and region overlays are code and platform-level data with no tenant ID. Compiled policy cache keys include tenant and version. A user with memberships in two tenants is evaluated against the policy of the tenant whose host they are on; switching tenants re-evaluates against the other tenant's policy and issues a new session ([[PKG-mfa-session-management-device]]).

<!-- check:enforcement -->
### Enforcement points and bypass paths

One evaluator, called from: sign-in and session refresh in `packages/auth/session`; Next.js middleware for `/admin/...` routes (surface `admin_console`); the `requireStepUp(actionClass)` guard used by tRPC procedures, Server Actions and REST handlers for consequential operations (lint rule `auth/consequential-needs-step-up`); and the hearing room join token issuer. Temporal and BullMQ workers do not authenticate users; they carry the originating principal for audit only. No other code path can create a session.

<!-- check:lifecycle -->
### Grant lifecycle and privileged access

Policy versions follow draft → in_review → approved → published → superseded with maker-checker for weakening; exclusions expire within 30 days; break-glass exemptions (max two) are reviewed quarterly in [[SEC-access-reviews]] and every use alerts owners. Platform emergency tightening needs two `platform_security` approvers and is visible to the tenant.

<!-- check:resilience -->
### Failure modes and secrets

If the compiled policy cannot be loaded from Redis, the evaluator reads Postgres; if neither is available the request fails closed (503) for `admin_console` and `step_up`, and existing valid sessions continue only for read-only routes for up to 5 minutes (assumption, to be approved by security). Geo-IP database failure treats the country as unknown, which matches only rules written for unknown countries, and never removes a requirement.

<!-- check:residency -->
### Data residency

Policies, zones and decision records live in the tenant's regional Postgres; geo-IP lookup uses a database deployed in each region (no external call). Nothing in this control leaves the region.

<!-- check:audit -->
### Audit trail

Audit events `admin.auth_policy.drafted`, `.approved`, `.published`, `.rolled_back`, `admin.auth_policy.exclusion_added`, `admin.network_zone.updated` with old and new compiled versions, actor, approver and reason; per-request outcomes in `auth_policy_decision`; break-glass use as `nomo.sec.break_glass_used`.

<!-- check:observability -->
### Detection and alerting

Dashboards per tenant: challenge and deny rates by rule, report-only would-deny counts (shown to the admin before enforcement), break-glass use. Alerts: deny rate for a persona above 5 % for 15 minutes after a publish (likely misconfiguration, to `security_admin` and Nomology support), any break-glass use, any exclusion added to an administrative role.

<!-- check:compliance -->
### Framework and legal mapping

ISO 27001:2022 Annex A 8.5 (secure authentication), 5.15 (access control), 8.2 (privileged access rights) and 8.20 (network security) [R8]; SOC 2 CC6.1, CC6.2 and CC6.6 [R9]. Evidence: published policy versions with approvals, simulator output before publish, decision log extracts, MFA and phishing-resistant coverage report per persona.

<!-- check:testing -->
### Verification and testing

Every cell of the matrix has a negative test (for example `tenant_admin` cannot publish; `unit_admin` cannot add a loosening rule; support cannot read decisions without a grant). Property tests cover strictest-wins and floor dominance; a generated test covers step-up for every consequential operation; Playwright covers blueprint policies end to end.

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
    "body": "Microsoft",
    "id": "R4",
    "kind": "vendor",
    "title": "Microsoft Entra Conditional Access overview",
    "url": "https://learn.microsoft.com/en-us/entra/identity/conditional-access/overview"
  },
  {
    "body": "Microsoft",
    "id": "R5",
    "kind": "vendor",
    "title": "Microsoft Entra: Conditional Access authentication strengths",
    "url": "https://learn.microsoft.com/en-us/entra/identity/authentication/concept-authentication-strengths"
  },
  {
    "body": "Okta",
    "id": "R6",
    "kind": "vendor",
    "title": "Okta Identity Engine: Sign-on policies and rules",
    "url": "https://help.okta.com/oie/en-us/content/topics/identity-engine/policies/about-policies.htm"
  },
  {
    "body": "Okta",
    "id": "R7",
    "kind": "vendor",
    "title": "Okta Identity Engine: Add an app sign-in policy rule",
    "url": "https://help.okta.com/oie/en-us/content/topics/identity-engine/policies/add-app-sign-on-policy-rule.htm"
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
