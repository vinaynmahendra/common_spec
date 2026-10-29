---
id: "PKG-domain-verification"
title: "Domain verification and home-realm discovery"
parent: "PKG-sso-saml-oidc-per-tenant"
order: 1
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Email domains drive SSO routing, enforcement, JIT, auto-join and SCIM acceptance only after per-tenant DNS TXT proof, re-checked daily; email-first home-realm discovery on the tenant host, with multi-tenant domains, subdomain rules and no cross-tenant leakage"
links: []
rev: 1
syncHash: "d2b28d2f5590e127"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.1.2.1 Domain verification and home-realm discovery

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Email domains drive SSO routing, enforcement, JIT, auto-join and SCIM acceptance only after per-tenant DNS TXT proof, re-checked daily; email-first home-realm discovery on the tenant host, with multi-tenant domains, subdomain rules and no cross-tenant leakage

<!-- section:statement -->
## Statement

When a tenant admin claims an email domain, the platform shall use that domain for SSO routing, SSO enforcement, just-in-time provisioning, auto-join or SCIM `userName` acceptance only after the tenant has proven control of it with a DNS TXT record, and shall stop using it within 24 hours of that proof disappearing.

<!-- section:rationale -->
## Rationale and source

Email domains decide who is routed to which identity provider and who can join a tenant automatically. Without proof of control, an attacker could register `bigfirm.com` in their own tenant (or a misconfigured tenant could claim it) and either intercept sign-ins of that firm's counsel or JIT-provision themselves into an institution. DNS proof is the industry norm for this: identity platforms verify organisation domains with a TXT record before using them for SSO and enrolment [R1][R2], and home-realm discovery that routes users to a federated IdP by domain depends on that verification [R3].

Our platform adds two specifics:
- A domain can legitimately belong to **several tenants** (a law firm whose counsel appear before many institutions), each with its own connection; verification is per tenant, not global.
- **Home-realm discovery (HRD)** must never let one tenant's verified domain affect sign-in on another tenant's host.

Source: threat T1 and T3 in [[PKG-sso-saml-oidc-per-tenant#threats]]; requirement SSO-4 in [[PKG-sso-saml-oidc-per-tenant#requirements]]; settings group E in [[PKG-settings-security-and-identity]].

<!-- section:acceptance -->
## Acceptance criteria

**Verification**

- **AC1 (happy path)** Given tenant T has added `lawfirm.example` with status `pending` and token `nomology-verify=6f1c…` / When the DNS TXT record at `_nomology-challenge.lawfirm.example` contains that value and the checker runs / Then the domain becomes `verified`, `verified_at` is set, audit event `admin.domain.verified` is written and the tenant's security admins are notified.
- **AC2 (not yet proven)** Given the domain is `pending` / When a user with `@lawfirm.example` signs in on T's host / Then HRD does not route them to any SSO connection and JIT, auto-join and SSO enforcement do not apply.
- **AC3 (proof removed)** Given the domain is `verified` / When two consecutive daily re-checks 12 hours apart fail to find the TXT value / Then the status becomes `lapsed`, SSO enforcement, JIT and auto-join stop for that domain, existing sessions continue, and security admins receive a warning with a 7-day window to restore the record before linked connections are disabled for that domain.
- **AC4 (public email domains)** Given a tenant admin adds `gmail.com` or another domain on the platform blocklist of consumer and disposable email domains / When they submit / Then the claim is refused with "This is a public email provider and cannot be claimed by an organisation."
- **AC5 (same domain, two tenants)** Given `lawfirm.example` is verified in tenants A and B with different SSO connections / When a user enters `jo@lawfirm.example` on A's host / Then they are routed only to A's connection; B's connection is never offered or used.
- **AC6 (subdomains)** Given `lawfirm.example` is verified / When a user has `@uk.lawfirm.example` / Then the subdomain is not covered unless the admin enabled "include subdomains" on that claim, which requires the TXT record on the parent domain at verification time.
- **AC7 (manual override)** Given a tenant cannot publish DNS records (for example a government domain managed centrally) / When `platform_security` approves a manual verification with documentary evidence and a second `platform_security` approves / Then status becomes `verified_manual` with a 12-month expiry and the evidence reference is stored.
- **AC8 (verification attempts)** Given a pending claim / When it is not verified within 14 days / Then it expires and the token is discarded; a new claim issues a new token.

**Home-realm discovery**

- **AC9 (email-first routing)** Given `auth.hrd.mode = email_first` and `institution.example` is verified for connection C (enabled) in tenant T / When a user enters `amy@institution.example` on T's sign-in page / Then the page redirects to C's IdP with `login_hint` (OIDC) or `Subject/NameID` hint (SAML) where the IdP supports it.
- **AC10 (enforced SSO)** Given `auth.sso.enforce_for_verified_domains = true` / When that user tries a password, magic link or OTP / Then the method is not offered, except for accounts on the break-glass list.
- **AC11 (no enumeration)** Given an email on a domain that is not verified in T / When it is entered / Then the page shows the same method choice as for any unknown address, and the response timing does not reveal whether the account exists.
- **AC12 (several connections)** Given a domain is mapped to two connections in T (allowed only during an IdP migration, with a primary flag) / When the user enters their email / Then they go to the primary connection, with a "Use another way to sign in" link to the second.
- **AC13 (other tenants' hosts)** Given a domain is verified only in tenant A / When the same email is entered on tenant B's host / Then B's own rules apply (local methods or B's connections), and nothing about A is shown.
- **AC14 (removal)** Given a verified domain is removed by a `security_admin` / When removal is approved (maker-checker if SSO is enforced for it) / Then routing, enforcement and JIT stop immediately, memberships are not ended, and users of that domain are asked to set up another method at next sign-in.

<!-- section:verification -->
## Verification method

- **Test**: integration tests in `packages/auth/domains/test` using a stub DNS resolver (record present, absent, wrong value, CNAME chains, multiple TXT strings, DNSSEC failure treated as absent); AC1–AC8.
- **Test**: Playwright HRD journeys on two tenant hosts with the same verified domain (AC5, AC9–AC13), including timing comparison for AC11 as in [[PKG-email-password-magic-link-otp#verification]].
- **Inspection**: the blocklist is reviewed quarterly; source and version recorded in [[PKG-reference-and-seed-data]].
- **Demonstration**: manual override (AC7) in staging with two `platform_security` approvers.

<!-- section:priority -->
## Priority

Must. Phase: with tenant SSO (same release as [[PKG-sso-saml-oidc-per-tenant]]); auto-join and subdomain inclusion are Should, one release later.

<!-- section:questions -->
## Open questions

- [ ] Which public and disposable email domain list do we use, and who maintains it per region? (Security)
- [ ] Should HTTP file verification (`/.well-known/nomology-verification.txt`) be offered as an alternative to DNS for tenants that cannot change DNS quickly? (Product, Security)
- [ ] Should the TXT record name be `_nomology-challenge` on the domain apex, or support delegated verification through a CNAME? (Engineering)
- [ ] Do Indian government `gov.in` / `nic.in` subdomains need a standard manual verification path agreed with NIC? (Legal, Operations)

<!-- section:notes -->
## Notes

**Data.** `auth_domain_claim(id, tenant_id, domain citext, include_subdomains bool, status enum('pending','verified','verified_manual','lapsed','expired','removed'), token_hash bytea, verified_at, last_checked_at, consecutive_failures int, evidence_ref text NULL, created_by)`; tenant-owned with forced RLS; `UNIQUE (tenant_id, domain)`; a domain may appear in many tenants. `auth_domain_connection(tenant_id, domain_claim_id, sso_connection_id, is_primary)` links domains to connections. This replaces `auth.sso_domain` in [[PKG-sso-saml-oidc-per-tenant#assets]]. Tenant **web hostnames** (custom domains for the tenant site, `tenant_domain` in [[MT-tenancy-and-identity-schema]]) are a separate concept, verified by [[MT-tenant-resolution]]; a tenant may reuse a verified email-domain proof to speed up a custom hostname claim, but the two records stay separate.

**Checker.** BullMQ repeatable job `identity-domains:check` every 15 minutes for `pending` claims (with backoff to hourly after 24 h) and daily for verified claims; DNS lookups go through the regional egress resolver, never a user-supplied server.

**HRD algorithm** (on the tenant host, in `packages/auth/hrd`):
1. Normalise the email (lowercase, IDNA to ASCII for the domain).
2. Look up verified claims for this tenant whose domain equals the email domain or, with `include_subdomains`, a parent domain; most specific wins.
3. If a claim has an enabled primary connection → redirect to the IdP; else → show local methods allowed for the persona (unknown persona: the union allowed for `party` and `counsel`).
4. Never consult other tenants' claims. Pattern borrowed from: email-first home-realm discovery in workforce identity platforms [R3]; enrolment modes (`off`, `suggest`, `automatic`) similar to verified domains in Clerk Organizations [R2].

**Auto-join.** With `auth.domains.auto_join = suggest`, a signed-in user whose verified email matches a claim sees "Join {tenant}" and the request goes to `user_admin` for approval; with `automatic`, they join with `auth.domains.auto_join_role`. Auto-join is never available for administrative roles and never on public email domains.

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Yes. Without it, SSO routing, enforcement, JIT and auto-join would trust a domain anyone can type, enabling interception of counsel sign-ins and self-provisioning into institutions (threats T1 and T3 in the SSO node).

<!-- check:unambiguous -->
### Unambiguous

The statement lists exactly which five behaviours depend on verification and the time limit for stopping. Acceptance criteria define the TXT location, re-check cadence (daily, two failures 12 hours apart) and the meaning of each status.

<!-- check:singular -->
### Singular

The statement is one constraint: domain-dependent behaviour only after DNS proof, stopping when proof disappears. HRD behaviour is expressed as acceptance criteria that follow from it; if reviewers prefer, AC9–AC13 can be split into a child requirement without changing the text.

<!-- check:complete -->
### Complete and scoped

Covers pending, verified, manual, lapsed, expired and removed states; multi-tenant domains; subdomains; public domains; enumeration; removal side effects; who can override (two `platform_security`).

<!-- check:feasible -->
### Feasible

DNS TXT checks through the regional resolver and a BullMQ repeatable job are standard; no new infrastructure.

<!-- check:verifiable -->
### Verifiable

Each AC is automated with a stub resolver or Playwright on two tenant hosts; AC7 is a staging demonstration.

<!-- check:consistent -->
### Consistent

Uses the shared-model roles, the `auth.domains.*` and `auth.hrd.mode` keys from [[PKG-settings-security-and-identity]], and replaces the inline domain rules previously in [[PKG-sso-saml-oidc-per-tenant#policy]]. Distinct from tenant custom hostnames in [[MT-tenant-resolution]].

<!-- check:traced -->
### Traced

Sources: SSO threats T1 and T3 and requirement SSO-4; forward to `packages/auth/domains`, `packages/auth/hrd`, tests in `packages/auth/domains/test` and Playwright suite `e2e/auth/hrd.spec.ts`.

<!-- citations -->
## Citations

```json
[
  {
    "body": "WorkOS",
    "id": "R1",
    "kind": "vendor",
    "title": "WorkOS Domain Verification",
    "url": "https://workos.com/docs/domain-verification"
  },
  {
    "body": "Clerk",
    "id": "R2",
    "kind": "vendor",
    "title": "Clerk Organizations: Verified domains",
    "url": "https://clerk.com/docs/guides/organizations/verified-domains"
  },
  {
    "body": "Microsoft",
    "id": "R3",
    "kind": "vendor",
    "title": "Microsoft Entra: Home realm discovery policy",
    "url": "https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/home-realm-discovery-policy"
  }
]
```

<!-- end -->
