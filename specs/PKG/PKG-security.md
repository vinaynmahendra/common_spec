---
id: "PKG-security"
title: "Security"
parent: "PKG"
order: 4
type: "capability"
template: "security"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 3
syncHash: "3a0e792660385827"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.4 Security

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

Parent node for the application-level security utilities that every app and worker uses, as opposed to identity ([[PKG-authentication]]) and access decisions ([[PKG-authorization]]):
- [[PKG-encryption-utilities-key]] — `@nomology/crypto`: envelope and field-level encryption, keyed hashing (blind indexes), signing helpers, the secrets-manager client and the Temporal payload codec. Key stores themselves are in [[INF-secrets-and-keys]].
- [[PKG-input-sanitisation-csrf-rate]] — `@nomology/http-guard`: input validation conventions, HTML and file-name sanitisation, CSRF defence for non-Server-Action routes, rate limiting and bot protection.

Security headers and CSP are owned by [[APP-security-headers-csp-cors]]; vulnerability management by [[SEC-vulnerability-management]].

What is protected: confidentiality of the most sensitive fields (KYC data, bank details, TOTP secrets, identity numbers) even against database-level exposure; integrity of requests (no forged cross-site actions, no injection); availability against abuse (credential stuffing, scraping, SMS pumping).

<!-- section:assets -->
## Protected assets

| Asset | Classification | Protected by |
|---|---|---|
| Field-encrypted values (bank account numbers, PAN / national IDs, KYC results, TOTP secrets, OAuth refresh tokens for integrations) | Sensitive personal / secret | `@nomology/crypto` envelope encryption, per-tenant data keys |
| Data encryption keys (wrapped) | Secret | Regional KMS key-encryption keys |
| Application secrets (provider API keys, webhook signing secrets, DB credentials) | Secret | Secrets manager client |
| Request integrity of state-changing endpoints | — | CSRF defences, origin checks |
| Service capacity | — | Rate limits, bot protection |

<!-- section:actors -->
## Actors and roles

| Actor | Interaction |
|---|---|
| Application code (web, workers) | Calls encryption, sanitisation and rate-limit helpers |
| Workload identities (ECS task roles, Azure managed identities) per region | Only identities allowed to use KMS keys and read secrets |
| Platform security | Owns key policies and rotation schedule |
| External attacker | Forged requests, injection payloads, automated abuse |
| Insider with database access | Should see only ciphertext for encrypted fields |

<!-- section:matrix -->
## Permission matrix

| Capability | Web app | Temporal workers | BullMQ workers | Migration job | Platform security | Developers (non-prod) |
|---|---|---|---|---|---|---|
| Encrypt / decrypt field purpose `kyc`, `bank` | ✓ (decrypt only in finance and KYC Activities' code paths) | ✓ | ✗ | ✗ | ✗ (no data access) | test keys only |
| Encrypt / decrypt purpose `totp`, `integration_token` | ✓ | ✓ (`integration_token`) | ✓ (`integration_token`) | ✗ | ✗ | test keys only |
| Temporal payload codec | ✓ (client) | ✓ | ✗ | ✗ | Codec Server under grant | test keys only |
| Read secrets | own service's secrets | own | own | DB migrator only | manage | ✗ in production |
| Rotate keys / secrets | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| Configure rate-limit policies | ✗ (code defaults) | — | — | — | ✓ (overrides) | ✗ |

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat | Mitigation (child node) | Residual |
|---|---|---|---|---|
| T1 | I | Database snapshot or replica leak exposes bank details | Field encryption with KMS-wrapped per-tenant keys ([[PKG-encryption-utilities-key]]) | Low |
| T2 | T | Cross-site request forgery on Route Handlers | Origin check, SameSite cookies, CSRF tokens where needed ([[PKG-input-sanitisation-csrf-rate]]) | Low |
| T3 | T | Stored XSS through rich-text submissions | Server-side HTML sanitisation and CSP | Low |
| T4 | D | Credential stuffing, scraping, SMS pumping | Rate limits per account, IP, tenant; SMS budgets | Low |
| T5 | I | Secrets in env files or logs | Secrets client with regional manager; redaction | Low |

<!-- section:questions -->
## Open questions

- [ ] Bot protection approach without puzzle CAPTCHAs (see [[PKG-accessible-authentication-and]]): WAF bot rules only, or an invisible challenge service — which must not send personal data out of region.
- [ ] Do any clients require customer-managed keys (bring-your-own-key) per tenant? Affects [[PKG-encryption-utilities-key]] and [[INF-secrets-and-keys]].

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Data keys are per tenant and bound into ciphertext AAD; rate-limit keys include the tenant; no helper accepts a tenant ID that differs from the context.

<!-- check:resilience -->
### Failure modes and secrets

Encryption fails closed when KMS is unavailable for unwrap (cached unwrapped data keys bridge short outages for up to 5 minutes). Rate limiting fails open only for authenticated, low-risk read routes and fails closed for authentication and OTP routes when Redis is down.

<!-- check:residency -->
### Data residency

Keys, secrets and rate-limit counters are per region; there is no global key. Azure deployments use Key Vault and Azure Cache for Redis with the same interfaces.

<!-- check:audit -->
### Audit trail

Reveals of field-encrypted data, key rotations and DEK destruction, and security-relevant guard events are recorded, as specified in each child.

<!-- check:compliance -->
### Framework and legal mapping

ISO 27001:2022 Annex A 8.24 (use of cryptography), 8.28 (secure coding) and 8.26 (application security requirements) [R1]; SOC 2 CC6.1 and CC6.7; GDPR Article 32 encryption as an appropriate measure; DPDP reasonable security safeguards. Evidence: cryptographic inventory generated from `@nomology/crypto` purposes, key rotation logs, rate-limit configuration snapshots.

<!-- check:testing -->
### Verification and testing

Each child has a negative test suite (AAD tamper, missing reveal token, origin enforcement, XSS vectors, SSRF, rate limits) that runs in CI on every change.

<!-- citations -->
## Citations

```json
[
  {
    "body": "ISO/IEC",
    "id": "R1",
    "ident": "27001",
    "kind": "standard",
    "title": "ISO/IEC 27001:2022 Information security management systems",
    "url": "https://www.iso.org/standard/27001",
    "version": "2022"
  }
]
```

<!-- end -->
