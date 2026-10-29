---
id: "INT-e-signature"
title: "E-signature"
parent: "INT-common-integrations"
order: 2
type: "feature"
template: "integration"
status: "draft"
owner: null
indicative: false
summary: "Provider integration for signing settlement agreements, awards and declarations, including India Aadhaar e-sign and global e-sign options"
links: []
rev: 2
syncHash: "34af03eb8cb16dcd"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 9.2.2 E-signature

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Provider integration for signing settlement agreements, awards and declarations, including India Aadhaar e-sign and global e-sign options

<!-- section:purpose -->
## Purpose and use cases

Lets parties, counsel and neutrals sign documents with legal effect without printing: settlement agreements, consent awards, arbitral awards (signed by tribunal members), procedural declarations (independence and impartiality, confidentiality undertakings), and consent forms.

Two methods:
1. **Aadhaar eSign (India)**: online electronic signature through a CCA-licensed eSign Service Provider (ESP), where the signer authenticates with Aadhaar OTP or biometric and a short-lived signing certificate signs the document hash [R1].
2. **Global e-signature provider**: for signers outside India or tenants that choose it; electronic signature with a signing audit trail, optionally with certificate-based signatures.

A third option, a signer's own Class 3 digital signature certificate (USB token) applied in a desktop signer, is out of scope for Phase 4 (open question).

Which method is legally sufficient for which document type, seat and institution is a **legal decision recorded per tenant and document type**, not decided by this integration.

<!-- section:party -->
## External party and ownership

- ESP: to select from CCA-licensed ESPs (India); contract owner: legal with CTO office.
- Global provider: to select; must offer region-specific data storage for Singapore and US tenants (or accept our storage of the signed copy with deletion at provider).
- Environments: ESP staging (test Aadhaar numbers only) and production; global provider sandbox account per region.

<!-- section:flows -->
## Data flows

```
Secretariat / neutral marks document version ready for signature
  └─▶ Temporal documents workflow `{tenantId}-sign-{documentVersionId}`
        ├─ load immutable document version (SHA-256 h0) and signer list with order
        ├─ for Aadhaar eSign signer:
        │     ├─ signer opens "Sign" in platform ─▶ we compute PDF signing hash, send eSign request (hash only) to ESP
        │     ├─ signer authenticates at ESP page (redirect) ─▶ ESP returns signature (PKCS#7) to our callback
        │     └─ activity embeds signature into PDF ─▶ new version (h1), verify signature
        ├─ for global provider signer:
        │     ├─ activity createEnvelope(document h0, signers, order) idempotency `env:{documentVersionId}`
        │     ├─ signers receive provider email or embedded signing session launched from platform
        │     └─ webhook envelope.completed ─▶ download signed PDF + certificate of completion
        ├─ store signed PDF as new immutable version, hash, audit; verify embedded signatures
        └─ emit document.signed; for awards, hand to award publication step
```
Signing order is sequential for awards (tribunal members) and parallel for settlement agreements unless the tenant configures otherwise.

<!-- section:mapping -->
## Data mapping

| Our field | ESP (Aadhaar eSign) | Global provider | Personal data |
|---|---|---|---|
| document version | SHA-256 of the PDF byte range to sign (hash only) | full PDF | ESP: none; global: document content |
| signer name | returned in certificate from Aadhaar demographic data | `name` | yes |
| signer email / phone | — | `email`, optional SMS number | yes |
| signer role | — | custom field `role` | no |
| external reference | transaction ID `{tenantId}:{signRequestId}` | envelope `external_id` | no |
| signed output | PKCS#7 signature + signer certificate | signed PDF + completion certificate | yes |
| signing time | in signature | in audit trail | no |

Aadhaar numbers are never stored by us; we keep only what the ESP returns in the signature certificate (name, and other attributes as the ESP provides, to be confirmed).

<!-- section:auth -->
## Authentication and secrets

ESP: per-region (India only) credentials and our request-signing certificate stored in the regional secrets manager / KMS; requests signed per the ESP's API specification; callbacks verified against the ESP's signature. Global provider: OAuth client credentials or JWT grant per region; webhooks verified by HMAC or provider signature; embedded signing URLs requested just-in-time and never stored.

<!-- section:errors -->
## Errors, retries and idempotency

| Situation | Handling |
|---|---|
| ESP authentication failed / cancelled by signer | Signer can retry; after 3 failures the secretariat is notified and may offer the global method if the tenant allows |
| ESP or provider unavailable | Retry with backoff; signer sees a clear message; deadline extensions are a tribunal decision |
| Signer declines (global) | Workflow ends `declined`; secretariat task |
| Document changed after request | Impossible by design: signing targets an immutable version; a new version restarts signing |
| Duplicate completion webhook | Inbox de-dupe; idempotent store on `signed:{envelopeId}` |
| Signature fails validation after embedding | Do not publish; alert; human task |

<!-- section:limits -->
## Rate limits and SLAs

Expected 2,000 envelopes per month in Year 1 (proposed). Aadhaar eSign volume depends on Indian tenants; per-transaction cost to be included in pricing ([[BIL-plans-entitlements-and-usage]]).

<!-- section:residency -->
## Data transfer and compliance

Aadhaar eSign sends only the document hash to the ESP, so document content stays in India. Global providers receive the full document; for Singapore and US tenants the provider's regional storage must match the tenant region, and the signed copy is stored by us. For Indian tenants, the global method sends content out of India only if the tenant enables it and a transfer basis is recorded.

<!-- section:testing -->
## Sandbox and testing

ESP staging with test identities; global provider sandbox per region; contract tests for callback parsing and signature embedding with recorded fixtures; PDF signature validation test suite (signatures remain valid after we add nothing further; any later stamp creates a new version).

<!-- section:questions -->
## Open questions

- [ ] Legal: for each tenant type and document (awards under the seat's arbitration law, settlement agreements, declarations), which signature methods are acceptable?
- [ ] Select the ESP and the global provider; confirm regional storage for Singapore and US.
- [ ] Support signers' own digital signature certificates (Class 3 DSC) for neutrals in a later phase?
- [ ] What attributes does the ESP's signer certificate expose, and which do we store?
- [ ] Accessibility of the ESP and provider signing pages (see [[INT-third-party-component]]).

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant separation at the provider

Signing requests carry `{tenantId}:{signRequestId}` as external reference; callbacks are resolved by connection then reference to one tenant and checked against the stored request under RLS. One platform account per provider per region; tenants may later bring their own global provider account.

<!-- check:security -->
### Security

ESP requests are signed with our certificate held in KMS; callback signatures verified; embedded signing URLs are just-in-time and not stored; Aadhaar numbers are never stored.

<!-- check:residency -->
### Data transfer and residency

Aadhaar eSign transfers only the hash [R1]; global providers receive the document, so regional storage at the provider must match the tenant's region, or the tenant must enable it with a recorded basis.

<!-- check:consistency -->
### Consistency and reconciliation

The platform owns the document versions and the signing workflow state; the provider is authoritative only for signer actions. A nightly reconciliation lists open envelopes older than their expiry and provider envelopes in `completed` with no stored signed version.

<!-- check:audit -->
### Audit and evidence

The signed PDF, the provider's completion certificate or the ESP response, and hashes before and after signing are stored as immutable versions in the tenant's region. Audit events: request created, each signer's action with time, completion, validation result. Retention follows the case record.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "eSign is an online electronic signature service offered by licensed eSign Service Providers, using Aadhaar-based authentication of the signer; the document itself is not sent, only its hash.",
    "id": "R1",
    "kind": "web",
    "publisher": "Controller of Certifying Authorities (CCA), Government of India",
    "retrieved": "2026-10-28",
    "title": "eSign - Online Electronic Signature Service (brochure)",
    "url": "https://cca.gov.in/sites/files/pdf/esign/esignbrochure1.5.pdf"
  }
]
```

<!-- end -->
