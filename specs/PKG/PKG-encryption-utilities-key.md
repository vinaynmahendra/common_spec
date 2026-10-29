---
id: "PKG-encryption-utilities-key"
title: "Encryption and secrets client utilities"
parent: "PKG-security"
order: 1
type: "feature"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "Envelope and field-level encryption helpers and the secrets-manager client used by apps and workers; the key stores and secret managers themselves are specified in 14.9"
links: []
rev: 4
syncHash: "2b6512514f49ff49"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.4.1 Encryption and secrets client utilities

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Envelope and field-level encryption helpers and the secrets-manager client used by apps and workers; the key stores and secret managers themselves are specified in 14.9

<!-- section:purpose -->
## Purpose and scope

`@nomology/crypto` gives application code a small, hard-to-misuse set of cryptographic helpers: envelope encryption of sensitive fields with per-tenant data keys wrapped by a regional KMS key, keyed hashing for lookups (blind indexes) and pseudonymisation, HMAC signing and verification (webhooks, magic links), the Temporal payload codec, and the client used to read secrets from the regional secrets manager. It does not run key stores; AWS KMS, Azure Key Vault and the secrets managers are specified in [[INF-secrets-and-keys]].

Goal: a database dump, replica or backup reveals no sensitive field in clear, and destroying a tenant's keys makes its encrypted data unrecoverable (crypto-shredding on offboarding, [[MT-tenant-lifecycle]]).

<!-- section:assets -->
## Protected assets

| Purpose (key domain) | Data | Where used |
|---|---|---|
| `kyc` | KYC results, ID document numbers | [[INT-kyc-and-sanctions-screening]] |
| `bank` | Bank account and payout details | [[DOM-invoices-and-vendor-bills]] |
| `national_id` | PAN, Aadhaar reference (never full Aadhaar number unless law allows; to be confirmed), other ID numbers | Parties |
| `totp` | TOTP secrets | [[PKG-mfa-session-management-device]] |
| `integration_token` | OAuth refresh tokens and API keys for tenant integrations | [[INT-integration-framework]] |
| `temporal_payload` | Workflow and activity payloads | [[WF-separation-of-concerns-temporal]] |
| `audit_hash` | HMAC key for hashing personal values in audit | [[PKG-audit-log-schema]] |
| `blind_index` | HMAC key for searchable equality on encrypted fields (email lookups, PAN dedupe) | Parties, users |

<!-- section:actors -->
## Actors and roles

| Actor | Use |
|---|---|
| Web app task role (per region) | Encrypt and decrypt allowed purposes; `kms:Decrypt` and `kms:GenerateDataKey` on the regional KEK with encryption context condition `region` |
| Temporal worker roles | Same, for purposes their Activities need |
| BullMQ worker roles | `integration_token` and `temporal_payload` only |
| Codec Server (Temporal Web UI decryption) | `temporal_payload` decrypt, only for operators under a support grant |
| Platform security | Key policy administration, rotation, no decrypt permission |
| Migration job | No KMS access |

<!-- section:matrix -->
## Permission matrix

| Operation | Web | Temporal workers | BullMQ workers | Codec Server | Platform security | Tenant admin |
|---|---|---|---|---|---|---|
| `encryptField` / `decryptField` purpose `kyc`, `bank`, `national_id` | ✓ (decrypt only in code paths that pass an `authz` decision with `reveal` obligation) | ✓ | ✗ | ✗ | ✗ | ✗ |
| purpose `totp` | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| purpose `integration_token` | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| purpose `temporal_payload` | ✓ (client encode) | ✓ | ✗ | ✓ decrypt under grant | ✗ | ✗ |
| `blindIndex`, `hmacAudit` | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| `sign` / `verify` (webhooks, links) | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| `getSecret` | own service scope | own | own | own | manage | ✗ |
| Rotate KEK / re-wrap DEKs | ✗ | ✗ | ✗ | ✗ | ✓ (job) | ✗ |
| Destroy tenant DEKs (crypto-shred) | ✗ | offboarding workflow only, after two approvals | ✗ | ✗ | approve | request via offboarding |

<!-- section:policy -->
## Policy model

```ts
// packages/crypto/src/index.ts (server-only)
export type Purpose = 'kyc' | 'bank' | 'national_id' | 'totp' | 'integration_token' | 'temporal_payload';
export type Ciphertext = string & { __brand: 'Ciphertext' }; // 'v1.<keyId>.<iv>.<ct>.<tag>' base64url

export function encryptField(p: { purpose: Purpose; plaintext: string | Uint8Array; aad: Aad }): Promise<Ciphertext>;
export function decryptField(p: { purpose: Purpose; ciphertext: Ciphertext; aad: Aad; reveal: RevealToken }): Promise<string>;
export interface Aad { tenantId: string; table: string; column: string; rowId: string } // binds ciphertext to its place
export type RevealToken = { decisionId: string };   // produced by authz when the policy grants 'reveal'

export function blindIndex(p: { purpose: 'blind_index'; value: string; normalise?: 'email' | 'pan' | 'phone' }): Promise<string>;
export function hmacAudit(value: string): Promise<string>;
export function sign(p: { keyRef: string; payload: Uint8Array }): Promise<string>;
export function verify(p: { keyRef: string; payload: Uint8Array; signature: string; maxAgeSeconds?: number }): Promise<boolean>;
export function getSecret(name: SecretName, opts?: { maxAgeSeconds?: number }): Promise<string>;
export function createTemporalPayloadCodec(): PayloadCodec;    // for @temporalio/client and worker data converter
export class KeyUnavailableError extends Error {}              // KMS or secrets manager unreachable
export class DecryptionError extends Error {}                  // tampered, wrong AAD, wrong tenant
```

- **Algorithm**: AES-256-GCM with 96-bit random IVs; AAD includes tenant, table, column and row ID so a ciphertext cannot be moved to another row or tenant [R3].
- **Keys**: one data encryption key (DEK) per tenant per purpose, generated by KMS `GenerateDataKey`, stored wrapped in `crypto.tenant_dek (tenant_id, purpose, key_id, wrapped_key, kek_arn, created_at, retired_at)`; unwrapped DEKs cached in process memory for 5 minutes, never written to Redis or logs.
- **KEK**: one customer-managed KMS key per region per environment (Azure: Key Vault key), automatic annual rotation; DEKs rotated yearly by creating a new DEK and re-encrypting lazily on write plus a background re-encryption job.
- **Crypto-shredding**: on tenant offboarding, after the export is delivered and the retention period ends, the offboarding workflow deletes the tenant's wrapped DEKs (two-person approval). Backups still contain wrapped DEKs until backup expiry; documented in [[PKG-retention-and-deletion-schedule]].
- **Secrets**: AWS Secrets Manager or Azure Key Vault per region; `getSecret` caches for 5 minutes and refreshes on authentication failure, so rotation needs no redeploy [R4].

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|---|
| T1 | I | Database dump exposes sensitive fields | Envelope encryption; KMS access only to workload roles | Low |
| T2 | T | Ciphertext swapped between rows or tenants | AAD binds tenant, table, column, row | Very low |
| T3 | I | Developer decrypts in a code path without authorisation | `decryptField` requires a `RevealToken` from `authz` | Low |
| T4 | I | Keys leaked in logs or crash dumps | Branded types, redaction of `Uint8Array` keys, no DEK serialisation | Low |
| T5 | D | KMS outage blocks payments and sign-in with TOTP | 5-minute DEK cache, fail closed beyond it, alert | Medium |
| T6 | E | Cross-region key use | KMS key policy conditions on region and encryption context | Low |

<!-- section:failure -->
## Denial behaviour

`DecryptionError` is never shown to users; the field renders as "unavailable" and an alert fires (possible tampering). `KeyUnavailableError` returns 503 on the affected action only.

<!-- section:requirements -->
## Security requirements

ASVS references are to OWASP ASVS **5.0** at section level [R1][R2]; requirement-level IDs to be added after checking against the 5.0.0 text.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| CRY-1 | Sensitive fields listed in the purpose table shall be stored only as AES-256-GCM ciphertext with AAD binding tenant, table, column and row. | V11.3, V14.2 |
| CRY-2 | Each tenant shall have its own data key per purpose, wrapped by a regional KMS key. | V11.1 |
| CRY-3 | Decryption of `kyc`, `bank` and `national_id` shall require an authorisation decision token. | V8.3 |
| CRY-4 | Secrets shall be read from the regional secrets manager at run time and never from committed files. | V13.3 |
| CRY-5 | A cryptographic inventory (purposes, algorithms, keys, owners) shall be generated from code. | V11.1 |
| CRY-6 | Temporal payloads shall be encrypted by the payload codec before leaving the process. | V11.3 |

<!-- section:verification -->
## Verification

Unit tests with KMS mocked by a local KEK; integration tests against LocalStack KMS and Azurite / Key Vault emulator; AAD tamper tests; decrypt-without-token type test; rotation test (old ciphertext still decrypts after rotation); crypto-shred test (ciphertext unrecoverable after DEK deletion).

<!-- section:questions -->
## Open questions

- [ ] Bring-your-own-key for institution tenants: required by any client? Owner: sales / legal.
- [ ] Which identity numbers may be stored at all (for example whether full Aadhaar numbers may be held) — legal to confirm; until then store only masked references.
- [ ] Use the AWS Encryption SDK instead of hand-built envelope code? Trade-off: proven format vs Azure parity.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Data keys are per tenant and AAD includes the tenant ID, so even a privileged process cannot decrypt tenant A's ciphertext as tenant B's. DEK rows are tenant-owned with forced RLS; key lookups run inside `withTenant`.

<!-- check:resilience -->
### Failure modes and secrets

Unwrapped DEKs are cached for 5 minutes to ride out short KMS blips; beyond that, operations needing decryption fail closed with 503. Secrets refresh on authentication errors, allowing rotation without redeploys. Compromised KEK: rotate key material in KMS and re-wrap all DEKs (job runs per region in under an hour at expected sizes); compromised DEK: create a new DEK and re-encrypt that tenant's purpose.

<!-- check:residency -->
### Data residency

Each region has its own KMS keys and secrets; key policies deny use outside the region and require encryption context `region=<in|sg|us>`. Azure deployments use Key Vault in the same Azure region as the tenant's data.

<!-- check:audit -->
### Audit trail

KMS calls are logged by the cloud provider (CloudTrail / Azure Monitor) in region; application audit records reveals of `kyc`, `bank` and `national_id` fields (who, which record, decision ID). Key rotation and DEK destruction are platform audit events.

<!-- check:compliance -->
### Framework and legal mapping

ISO 27001:2022 Annex A 8.24 (use of cryptography) and 5.17 for secrets; SOC 2 CC6.1 and CC6.7; GDPR Article 32 (encryption); supports DPDP reasonable security safeguards. Evidence: generated cryptographic inventory and KMS rotation reports.

<!-- check:testing -->
### Verification and testing

CI runs AAD tamper, wrong-tenant, missing reveal token and rotation tests on every change, plus integration tests against KMS emulators for AWS and Azure adapters.

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
    "title": "OWASP Cryptographic Storage Cheat Sheet",
    "url": "https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html"
  },
  {
    "body": "OWASP",
    "id": "R4",
    "ident": "Cheat Sheet Series",
    "kind": "standard",
    "title": "OWASP Secrets Management Cheat Sheet",
    "url": "https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html"
  }
]
```

<!-- end -->
