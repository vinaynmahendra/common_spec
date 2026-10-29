---
id: "PKG-external-party-identity"
title: "External party and counsel identity"
parent: "PKG-authentication"
order: 7
type: "feature"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "Identity for people outside a tenant's directory: external memberships with case-only access, identity verification levels ivl0–ivl3 per case role, counsel checks and approved representations, guardian flows, regional government ID options (flagged assumptions) and minimised verification data"
links: []
rev: 1
syncHash: "745b34ab3a08baa6"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.1.7 External party and counsel identity

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Identity for people outside a tenant's directory: external memberships with case-only access, identity verification levels ivl0–ivl3 per case role, counsel checks and approved representations, guardian flows, regional government ID options (flagged assumptions) and minimised verification data

<!-- section:purpose -->
## Purpose and scope

Most people on a case are **not** in the tenant's directory: claimants and respondents (including unrepresented SEBI ODR investors and MSME claimants), their counsel, guardians and authorised representatives, experts, witnesses, interpreters, observers, and neutrals who are empanelled but not staff. This control decides how such people get an identity on the platform, how strongly that identity is checked for a given case role, how counsel prove they may act for a party, and how all of this stays confined to the cases they belong to.

Protects: case confidentiality (a stranger must not join a case by guessing an email), procedural fairness (the respondent's counsel must really be authorised), and the personal data used for verification (identity documents and national ID numbers).

Relies on this control: case participant invitations ([[PKG-user-provisioning-scim]] F6), case-level authorisation ([[PKG-rbac-abac-case-level-party]]), the party and counsel portal ([[APP-party-and-counsel-portal]]), KYC and screening ([[INT-kyc-and-sanctions-screening]]), and the accessible alternatives in [[PKG-accessible-authentication-and]].

**Identity model.** An external person has one `user_account` per region (keyed by verified email), and per tenant an **external membership** (`membership.kind = 'external'`) that carries no tenant roles except `party`, `counsel`, `neutral` or `observer` personas; access comes from **case roles** only. External members cannot browse the tenant directory, other cases, or other tenants' data, and a tenant never sees which other tenants a person belongs to.

<!-- section:assets -->
## Protected assets

| Asset | Classification | Storage / rule |
|---|---|---|
| Identity verification record (`identity_verification`: subject, level, method, provider reference, result, verified name, date, expiry) | Personal | Tenant-owned, regional |
| Evidence documents (ID images, selfies, authority letters) | Personal, sensitive; may be government ID | Not retained after verification unless `auth.external.retain_evidence_documents` (default false); authority documents are case documents ([[DOM-documents]]) |
| National ID numbers (Aadhaar, NRIC/FIN, SSN) | Highly restricted | Never stored in full. Aadhaar: not stored; only the provider reference and masked last 4 digits where the provider returns them. NRIC: only where justified (see policy). SSN: never collected |
| Representation record (`representation`: counsel, party, case, authority document, status, verified by) | Legal effect | Case-scoped, tenant-owned |
| Bar or professional registration details | Personal (public register data) | Tenant-owned, re-checked per tenant setting |
| Case invitation tokens | Secret | SHA-256 hash only |

<!-- section:actors -->
## Actors and roles

| Actor | How the identity and access are acquired |
|---|---|
| `claimant`, `respondent` (person or organisation contact) | Public filing entry ([[APP-public-and-sign-in-surfaces]]) or case invitation from `case_manager`; email (or phone in India) control proven; higher levels per `auth.external.required_ivl` |
| `claimant_counsel`, `respondent_counsel` | Invitation by `case_manager` or by the party themselves (party nominates counsel; secretariat approves when `auth.external.counsel_check ≠ self_declared`), plus a representation record |
| Guardian / authorised representative | Invited as representative of a named party; consent and authority captured; banner "Acting for {party}" (see [[PKG-accessible-authentication-and#tenant]]) |
| `presiding_neutral`, `tribunal_member` who are not tenant staff | Tenant `neutral` persona after empanelment ([[DOM-neutrals]]); appointment creates the case role |
| `expert`, `witness`, `interpreter`, `observer` | Case invitation limited to specific hearings or document sets; expires with the case event |
| Aggregator-referred party (e.g. via NSE for SEBI matters) | Case created by the aggregator API ([[INT-aggregator-intake-api]]) with the party's contact details; the party claims the case by verifying control of that email or mobile |
| `case_manager` / `secretariat` | Invites, approves representations, performs manual verification |
| `security_admin` | Sets required levels and methods per case type |
| Verification provider | External; [[INT-kyc-and-sanctions-screening]] |

<!-- section:matrix -->
## Permission matrix

✓ allowed, ✗ denied, "C" only on cases where they hold `case_manager`, "own" only for themselves. Permission keys proposed for [[PKG-permission-catalogue]].

| Action | Permission | Party / counsel (own) | `case_manager` | `secretariat` (not on case) | `security_admin` | `tenant_admin` | `auditor` | `platform_support` |
|---|---|---|---|---|---|---|---|---|
| Invite a participant to a case | `case.participant:assign` | counsel may invite co-counsel of own firm if tenant allows | C | ✗ | ✗ | ✗ | ✗ | ✗ |
| Nominate own counsel | `case.representative:create` | own party only | C | ✗ | ✗ | ✗ | ✗ | ✗ |
| Approve a representation | `case.representative:approve` | ✗ | C | ✗ | ✗ | ✗ | ✗ | ✗ |
| Start own identity verification | `identity.verification:create` | own | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Perform manual verification (document review, video) | `identity.verification:approve` | ✗ | C (cannot verify themselves or a colleague) | ✗ | ✗ | ✗ | ✗ | ✗ |
| View verification outcome (level, method, date) | `identity.verification:read` | own | C | ✗ | T | T | T | under grant |
| View evidence documents | `identity.verification.evidence:read` | own | C, step-up, audited | ✗ | ✗ | ✗ | ✗ | ✗ |
| Set required levels per case type | `settings.security:write` | ✗ | ✗ | ✗ | T | ✗ | ✗ | ✗ |
| Revoke a participant's case access | `case.participant:assign` | ✗ (counsel may withdraw themselves) | C | ✗ | ✗ | ✗ | ✗ | ✗ |
| End an external membership in the tenant | `user:delete` | own (leave tenant) | ✗ | ✗ | ✗ | T | ✗ | ✗ |
| Merge duplicate external accounts | `user:update` (merge) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | `platform_support` with both users' confirmation |

"T" = within own tenant. No tenant role can see an external person's memberships in other tenants.

<!-- section:policy -->
## Policy model

**Identity verification levels (IVL).** Our own scale, chosen per case role by `auth.external.required_ivl` (case-type scope, pinned at case start). Rough alignment with NIST identity assurance levels [R3] is indicative only; we do not claim NIST conformance.

| Level | Meaning | Accepted evidence | Rough NIST alignment |
|---|---|---|---|
| `ivl0` | Asserted identity | Name typed by the person; access link sent by the tenant | none |
| `ivl1` | Control of contact | Verified email (link or OTP) or verified mobile (India) | below IAL1 |
| `ivl2` | Verified against an authoritative source | India: DigiLocker document fetch [R5], PAN verification, Aadhaar offline e-KYC through a licensed provider; Singapore: Myinfo via Singpass [R6]; US and elsewhere: document plus selfie through the KYC provider; any region: manual document review by `case_manager` | approx. IAL1–IAL2 depending on method |
| `ivl3` | Supervised verification | `ivl2` plus a live video or in-person check by a trained `case_manager`, or registry verification of a professional (bar enrolment) | approx. IAL2 supervised |

Rules:
1. Each case role has a required level; the participant can see case metadata (title, next step) at `ivl1` but cannot read documents or act until they reach the required level.
2. A verification is reusable within the same tenant for `auth.external.verification_reuse_days`; reuse across tenants is **off** (assumption: cross-tenant reuse needs the person's explicit consent and a legal basis under DPDP and PDPA; legal to confirm).
3. **Name matching**: the verified name is compared with the party name on the case using normalised, transliteration-aware matching; a mismatch follows `auth.external.name_mismatch_action` (default: task to `case_manager`).
4. **Counsel**: `auth.external.counsel_check` sets `self_declared` (counsel declares enrolment number and bar), `secretariat_verified` (case manager checks the register and records the result) or `registry_verified` (automated check where a register offers one; assumption: no stable public API exists for Indian state bar councils, the Singapore practising certificate register or US state bars, so this starts as manual).
5. **Authority to act**: with `auth.external.representation_proof_required`, counsel cannot file or see confidential documents until a representation record is `approved` with the authority document (vakalatnama, letter of authority, power of attorney or engagement letter). Change of counsel ends the outgoing counsel's case role when the incoming representation is approved, with a notice to both.
6. **Organisations as parties**: an organisation party has one or more authorised contacts; adding a contact needs approval by an existing contact or the case manager.
7. **Joining by invitation only**: no one can request access to a case they were not invited to or did not file; invitation tokens are single use and bound to the invited email (or phone).
8. **Authentication** of external people follows [[PKG-authentication-policies]] for personas `party`, `counsel`, `neutral`, `observer`; step-up for consequential actions (filing, settlement acceptance, signing) applies regardless of IVL.

**Government ID options (assumptions to be confirmed by legal before any is enabled):**

| Region | Option | Use | Constraints |
|---|---|---|---|
| India | DigiLocker (issued documents such as PAN, driving licence) [R5] | `ivl2` | Requires DigiLocker partner onboarding; only document fetch with the person's consent |
| India | Aadhaar authentication or offline e-KYC | `ivl2` | Authentication by non-government entities is permitted only where notified under the 2025 amendment to the Aadhaar authentication rules [R4]; we would use a licensed provider and never store the Aadhaar number. Assumption: Nomology or the tenant would need approval for the specific purpose |
| India | Aadhaar e-sign | Signing, not identity | Covered by [[INT-e-signature]] |
| Singapore | Singpass login and Myinfo [R6] | Sign-in (`auth.methods.government_login.providers`) and `ivl2` | Requires onboarding with the Singpass programme; NRIC numbers collected only where needed to verify identity to a high degree of fidelity, as the PDPC guidance allows [R7] |
| US | No national scheme for private services (Login.gov serves government agencies) | — | Document plus selfie via KYC provider; no SSN collection |

**Data minimisation.** We keep the outcome (level, method, provider reference, verified name, date) and discard images by default; under the DPDP Act the data fiduciary must limit processing to what is necessary for the stated purpose [R8].

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|---|
| T1 | S | Stranger joins a case with a forwarded invitation | Token bound to invited email, single use, expiry; acceptance requires sign-in with that email; case manager notified of every join | Low |
| T2 | S | Impersonated counsel (fake firm email, fake authority letter) | Representation approval with authority document; `secretariat_verified` check on register; respondent counsel join notified to the respondent party on their own contact | Medium for `self_declared` tenants |
| T3 | S | Synthetic identity passes document plus selfie | Provider liveness and document checks, name match to case, manual review on mismatch, sanctions screening where required | Medium |
| T4 | I | Leak of national ID numbers | Not stored; masked display; evidence images discarded by default; field-level encryption for any retained number ([[PKG-encryption-utilities-key]]) | Low |
| T5 | E | External member enumerates tenant directory or other cases | External memberships have no directory permissions; people pickers return only participants of the same case ([[PKG-combobox-and-people-picker]]) | Low |
| T6 | I | Tenant learns where else a person litigates | Memberships of other tenants never exposed; verification reuse across tenants off | Low |
| T7 | R | Party denies having appointed counsel | Representation record with authority document, approver and audit | Low |
| T8 | D | Person with a disability cannot complete liveness | Alternative routes required by [[PKG-accessible-authentication-and]]; manual verification at the same level | Low |
| T9 | T | Aggregator-sent contact details hijacked (wrong email in NSE feed) | Claiming a case needs control of the contact; secretariat can correct contacts with audit; investor notified via both channels where known | Medium |

<!-- section:failure -->
## Denial behaviour

- Below required level: the case page shows what is needed and why ("To read case documents you need to verify your identity. This takes about 5 minutes.") with the methods available in the region and an assisted route; no document titles are shown.
- Verification failed or name mismatch: neutral message; a review task is created; the person can retry or choose another method; the failure reason from the provider is shown only to the `case_manager`.
- Representation pending: counsel sees the case title and a pending banner, cannot file or read confidential documents.
- Invitation invalid, expired or for another email: the same generic message for each case ("This invitation can no longer be used. Ask the sender for a new one.").
- Logged: `identity.verification.completed` / `.failed` (reason code), `case.representation.approved` / `.rejected`, `case.participant.joined`, with case ID and hashed IP; no document images or ID numbers in logs.

<!-- section:requirements -->
## Security requirements

ASVS references are to OWASP ASVS **5.0** at section level [R1][R2]; requirement-level IDs are filled in when text is checked against the 5.0.0 release.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| XID-FR-1 | External members shall have no permissions outside the cases on which they hold a case role, apart from their own profile and sign-in settings. | V8.2 |
| XID-FR-2 | Case invitations shall be single use, bound to the invited email or phone, expire per `auth.invitations.case_participant_ttl_days`, and be stored only as hashes. | V6.6 |
| XID-FR-3 | The required identity verification level for each case role shall be taken from the case type and pinned when the case starts. | — |
| XID-FR-4 | A participant below the required level shall not read case documents or perform case actions. | V8.2 |
| XID-FR-5 | Counsel shall not file or read confidential documents for a party until a representation for that party is approved, where the tenant requires proof of authority. | V8.2 |
| XID-FR-6 | Verification evidence images shall be deleted once the outcome is recorded unless the tenant enabled retention, and full national ID numbers shall never be stored. | V14.2 |
| XID-FR-7 | A case manager shall not approve their own or a colleague-of-record's verification or representation where they are a participant in the case. | V8.2 |
| XID-FR-8 | The platform shall never reveal to a tenant the memberships, cases or verifications of a person in another tenant. | V8.2 |
| XID-FR-9 | Every verification route that relies on sight, facial movement or speech shall have an alternative at the same level. | — |
| XID-FR-10 | Change of counsel shall end the outgoing counsel's case role when the incoming representation is approved, and notify both counsel and the party. | — |

<!-- section:verification -->
## Verification

- Negative tests for every matrix row; external member calls to directory, other cases and tenant settings endpoints return the same not-found response as for a non-existent resource ([[APP-error-message-catalogue]]).
- Invitation tests: forwarded token used by a different signed-in email is refused; reuse refused; expiry enforced.
- Level gating tests per case type with pinned settings; changing the case type setting does not affect running cases.
- Provider sandbox tests per region (DigiLocker sandbox, Singpass staging, KYC provider test documents).
- Accessibility: alternative verification route walkthroughs with assistive technology users ([[PKG-accessible-authentication-and#testing]]).
- Pen test scope: invitation abuse, representation spoofing, people-picker enumeration.

<!-- section:questions -->
## Open questions

- [ ] Which Indian and Singapore government ID integrations are needed at launch, and is any approval needed for Aadhaar-based verification for our purpose? (Legal, Product)
- [ ] Does any SEBI ODR circular or MII agreement require investor identity verification by the ODR institution, and to which level? (Legal)
- [ ] Is cross-tenant reuse of a verification (with consent) wanted, and under which legal basis in India, Singapore and the US? (DPO, Legal)
- [ ] Are there machine-readable bar registers we can use for `registry_verified` in India, Singapore or US states? (Operations)
- [ ] Retention of the verification outcome after case closure — follow the case retention schedule or shorter? (DPO)
- [ ] Should a party be able to see and revoke counsel they appointed without the case manager? (Product, with tenants)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

External memberships, verification records and representations are tenant-owned rows under forced RLS; the region-level `user_account` holds only contact data and no tenant references visible to tenants. Case-level access comes from case roles evaluated by [[PKG-rbac-abac-case-level-party]]. Verification reuse is tenant-local by default, so one tenant's verification never grants anything in another.

<!-- check:enforcement -->
### Enforcement points and bypass paths

Level and representation gates are evaluated inside the case authorisation check (attribute `participant.ivl` and `representation.status`) used by every tRPC procedure, REST handler and signed-URL issuer for case documents ([[PKG-encryption-at-rest-signed-urls]]); documents are not reachable by URL without that check. Invitation acceptance is a single Route Handler; there is no other way to obtain a case role as an external person.

<!-- check:lifecycle -->
### Grant lifecycle and privileged access

Case roles end with case closure plus the tenant's post-closure access window, on counsel change, on revocation by the case manager, or when the invitation expires unaccepted. Verifications expire per reuse window. External memberships with no active case roles for 24 months are ended by a daily job (assumption, to be confirmed with DPO).

<!-- check:resilience -->
### Failure modes and secrets

If the verification provider is down, participants can use another configured method or the manual route; nothing is auto-approved. If the case document store is reachable but verification records are not, access fails closed.

<!-- check:residency -->
### Data residency

Verification records and any retained evidence are stored in the tenant's region; provider routing per region follows [[INT-kyc-and-sanctions-screening#residency]] (Indian subjects to an India-hosted provider; Singpass data stays in Singapore deployments).

<!-- check:audit -->
### Audit trail

Audited: invitation sent, accepted, expired, revoked; verification started, completed, failed, manually approved (with approver); representation created, approved, rejected, ended; evidence document viewed (by whom). These events also feed the case timeline where procedural ([[PKG-case-timeline]]).

<!-- check:observability -->
### Detection and alerting

Metrics per tenant and case type: verification completion rate, failure reasons, time to verify, pending representations older than 3 working days. Alerts: verification failure rate above 30 % in a day (provider issue), repeated invitation acceptance attempts with mismatched email (possible phishing).

<!-- check:compliance -->
### Framework and legal mapping

DPDP Act purpose limitation and security safeguards [R8]; PDPC NRIC guidance for Singapore [R7]; ISO 27001:2022 Annex A 5.16 (identity management), 5.34 (privacy and protection of PII) [R9]; SOC 2 CC6.1–CC6.3 [R10]. Evidence: per case-type level configuration, verification logs, deletion records for evidence images.

<!-- check:testing -->
### Verification and testing

Matrix negative tests, invitation abuse tests, level gating with pinned settings, provider sandbox tests per region, and accessibility walkthroughs of alternative routes run each release; pen test annually.

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
    "ident": "SP 800-63A-4",
    "kind": "standard",
    "title": "NIST SP 800-63A-4 Digital Identity Guidelines: Identity Proofing and Enrollment",
    "url": "https://pages.nist.gov/800-63-4/sp800-63a.html",
    "version": "800-63-4"
  },
  {
    "id": "R4",
    "issuer": "Unique Identification Authority of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "title": "UIDAI press release on Aadhaar authentication for good governance (amendment rules permitting authentication by entities other than government)",
    "url": "https://uidai.gov.in/images/Press_Release-Aadhaar_Authentication_Good_Governace.pdf"
  },
  {
    "body": "Ministry of Electronics and Information Technology (DigiLocker)",
    "id": "R5",
    "kind": "vendor",
    "title": "Digital Locker Authorized Partner API Specification v1.11",
    "url": "https://img1.digitallocker.gov.in/assets/img/Digital%20Locker%20Authorized%20Partner%20API%20Specification%20v1.11.pdf"
  },
  {
    "body": "Government Technology Agency of Singapore",
    "id": "R6",
    "kind": "vendor",
    "title": "Singpass Developer Docs (Singpass login and Myinfo)",
    "url": "https://docs.developer.singpass.gov.sg/docs"
  },
  {
    "id": "R7",
    "issuer": "Personal Data Protection Commission Singapore",
    "jurisdiction": "Singapore",
    "kind": "regulation",
    "title": "Advisory Guidelines on the PDPA for NRIC and other National Identification Numbers",
    "url": "https://www.pdpc.gov.sg/guidelines-and-consultation/2020/02/advisory-guidelines-on-the-personal-data-protection-act-for-nric-and-other-national-identification-numbers"
  },
  {
    "id": "R8",
    "issuer": "Ministry of Electronics and Information Technology, Government of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 22 of 2023",
    "title": "Digital Personal Data Protection Act, 2023",
    "url": "https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf"
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
