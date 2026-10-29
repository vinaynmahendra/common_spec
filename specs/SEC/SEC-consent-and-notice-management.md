---
id: "SEC-consent-and-notice-management"
title: "Consent and notice management"
parent: "SEC-privacy-controls"
order: 1
type: "feature"
template: "control"
status: "draft"
owner: null
indicative: false
summary: "DPDP / GDPR / PDPA notices, consent capture and withdrawal, legitimate-use records, consent manager integration if required"
links: []
rev: 2
syncHash: "50f84e7be50ab665"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 13.2.1 Consent and notice management

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> DPDP / GDPR / PDPA notices, consent capture and withdrawal, legitimate-use records, consent manager integration if required

<!-- section:objective -->
## Control objective

Every person whose personal data the platform collects receives the right notice at the right moment in a language they can read, consent is obtained where consent is the basis and can be withdrawn as easily as it was given, and for every processing we can show which basis applied and which notice version the person saw.

<!-- section:mapping -->
## Framework mapping

| Framework | Clause |
|---|---|
| DPDP Act 2023 | s.5 notice (itemised personal data and purpose, how to withdraw, how to exercise rights and complain); s.5(3) English or any Eighth Schedule language; s.6 consent (free, specific, informed, unconditional, unambiguous, clear affirmative action), s.6(4) withdrawal as easy as giving; s.6(7)–(9) consent managers; s.7 legitimate uses; s.9 children and persons with disability [R1] |
| DPDP Rules 2025 | Rule 3 notice contents and form; Rule 4 consent managers (in force one year after publication) [R2] |
| GDPR | Arts 6–7 (lawful basis, conditions for consent), Art. 8 (children), Arts 12–14 (transparent information) [R3] |
| PDPA | s.13–17 consent and withdrawal, s.20 notification of purposes |
| ISO/IEC 27001:2022 | A.5.34 |
| SOC 2 | P1 (notice), P2 (choice and consent) |

<!-- section:description -->
## Control description

**Basis per journey** (proposed, legal to confirm)

| Journey | Data principal | Basis (when Nomology or the tenant is fiduciary) | Consent needed? |
|---|---|---|---|
| Party filing a claim on CORD / SEBI ODR | Claimant (often an investor or MSME) | Consent for platform processing; legal-claim exemption for processing necessary to pursue the claim (assumption) | Yes, at registration, with notice |
| Respondent added by claimant or by aggregator intake | Respondent | Legal-claim processing / institution's rules; no consent possible before service | No; notice at first contact (service email / SMS) |
| Counsel invited to a case | Counsel | Contract / institutional rules | Notice at invitation acceptance |
| Neutral empanelment | Arbitrator / conciliator | Contract with the institution | Notice; consent for optional profile publication |
| Hearing recording and transcription | All participants | Institution's rules / tribunal direction | Notice before joining; consent where rules require |
| KYC and sanctions screening | Parties and payees | Legal obligation (AML) where applicable / contract | Notice |
| WhatsApp / SMS notifications | Any user | Consent (opt-in) for non-mandatory channels ([[PKG-notification-preferences]]) | Yes for WhatsApp / SMS marketing-free updates; legal service notices follow the institution's rules |
| AI features on case content | Parties (indirectly) | Tenant decision and disclosure ([[AI-ai-governance-and-impact]]) | Tenant-level opt-in; notice to parties |
| Analytics cookies on public pages | Visitors | Consent | Yes (banner); strictly necessary cookies only by default |
| Minor or person with disability as party | Parent / lawful guardian | Verifiable consent of parent or guardian (DPDP s.9) | Yes, via guardian flow ([[PKG-accessible-authentication-and]]) |

**Notice delivery**

1. Notices are versioned legal texts in the register ([[I18N-legal-declaration-and-consent]]) with copy in [[SEC-privacy-notice-copy]].
2. Shown as a standalone, layered notice before data is collected (a short notice with the itemised list, linking to the full notice), in the user's chosen language among those the tenant supports.
3. The notice identifies the fiduciary (the tenant institution, or NTPL for CORD) and, where Nomology is a processor, says so.
4. Notices sent by email or SMS at first contact include a short link to the full notice.

**Consent records**

Table `consent_record` (tenant-owned, append-only): `tenant_id`, `id`, `user_account_id` or `subject_ref` (for not-yet-registered parties), `purpose_key`, `notice_version_id`, `language`, `action` (`given`, `withdrawn`), `channel` (web, SMS link, consent manager), `evidence` (request id, IP hash, user agent hash, consent manager artefact id), `created_at`. Withdrawal is a new row, never an update. Current state is the latest row per purpose.

**Withdrawal.** A "Privacy and consent" page in every persona's settings lists purposes with toggles; withdrawal takes effect within 24 hours (target) across processing, including stopping WhatsApp / SMS and removing data from optional AI processing. The page explains what withdrawal will and will not stop (for example, the case record continues under the institution's rules).

**Consent managers.** Rule 4 provides for registered consent managers. The platform will accept consent artefacts from a registered consent manager through an adapter if a tenant requires it; design deferred until registrations exist (assumption).

**Re-acceptance.** A material change to a notice creates a new version; users are shown the new notice at next sign-in and, where consent is the basis, asked again; processing under the old consent continues only within its original purpose.

<!-- section:owner -->
## Owner and frequency

Owner: DPO. Backup: legal counsel. Operators: product owners (journeys), tenant admins (tenant-specific notices where the tenant is fiduciary). Frequency: per journey change; quarterly review of notice versions and consent metrics; annual review of bases.

<!-- section:evidence -->
## Evidence

- Notice versions with approval records and publication dates ([[I18N-legal-declaration-and-consent]]).
- `consent_record` rows (kept for the life of the processing plus the limitation period; proposed 7 years after last action, to be confirmed by legal).
- Screenshots or rendered snapshots of each notice version per language, stored with the version.
- Withdrawal processing logs.

<!-- section:test -->
## Test procedure

Auditor samples 25 consent records and checks the notice version existed and was approved at that time, the language matches, and for withdrawn consents that processing stopped (for example no WhatsApp messages after withdrawal). Walks through one journey per persona to confirm notice placement.

<!-- section:implementation -->
## Implementation in the platform

[[I18N-legal-declaration-and-consent]] (text versioning), [[SEC-privacy-notice-copy]] (copy), [[PKG-notification-preferences]] (channel opt-in), [[PKG-settings]] (tenant notice configuration), [[PKG-audit-trail]] (record of acceptance), [[APP-public-and-sign-in-surfaces]] (registration and invitation flows).

<!-- section:exceptions -->
## Exceptions

A journey that cannot show a notice before collection (for example a respondent added by a claimant) must deliver it at first contact; any other exception needs DPO approval.

<!-- section:metrics -->
## Monitoring and KPIs

- Journeys collecting personal data without a linked notice version (target 0).
- Withdrawals processed within 24 hours (target 100%).
- Notice languages available versus tenant-supported languages.

<!-- section:questions -->
## Open questions

- [ ] Legal bases per journey (table above) to be confirmed by legal, especially reliance on the legal-claim exemption.
- [ ] Which Eighth Schedule languages must notices be available in at launch for SEBI ODR and CORD tenants? Proposed: English and Hindi first, then tenant-requested languages.
- [ ] Consent manager integration: required by any tenant? Revisit after Rule 4 commences.
- [ ] Retention period for consent records (7 years proposed).

<!-- checks -->
## Template checks

<!-- check:scope -->
### Scope and population

Every journey that collects personal data in every persona and channel (web, email, SMS, WhatsApp, API intake), for all tenants and regions. The population is the journey list in the APP and DOM nodes plus the API intake contracts.

<!-- check:evidence -->
### Evidence quality and retention

Append-only consent records linked to approved notice versions and stored snapshots let an auditor see exactly what each person saw and chose.

<!-- check:automation -->
### Automation and continuous monitoring

Consent capture, withdrawal propagation and journey-to-notice linkage checks are automated; choosing bases and approving notices are manual.

<!-- check:commitments -->
### Legal and client commitments

DPDP s.5–6 and Rule 3, GDPR Arts 7 and 12–14, PDPA ss.13–20, and tenant DPAs where the tenant is fiduciary and relies on our notice features. Changing a notice or basis requires DPO approval and, where the tenant is fiduciary, the tenant's agreement.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Sections 5–6 (notice and consent), 8 (obligations of data fiduciary, including breach intimation), 11–14 (rights of data principal), 17 (exemptions).",
    "id": "R1",
    "issuer": "Government of India (MeitY)",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 22 of 2023",
    "title": "Digital Personal Data Protection Act, 2023",
    "url": "https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf"
  },
  {
    "excerpt": "Rule 1: Rules 3 and 5–16 come into force eighteen months after publication, Rule 4 after one year. Rule 3 notice; Rule 6 security safeguards including keeping logs for one year; Rule 7 breach intimation to the Board with a detailed report within seventy-two hours; Rule 14(3) grievances answered within a period not exceeding ninety days.",
    "id": "R2",
    "issuer": "Government of India (MeitY)",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Digital Personal Data Protection Rules, 2025",
    "title": "Digital Personal Data Protection Rules, 2025 (Gazette notification)",
    "url": "https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf"
  },
  {
    "excerpt": "Art. 12(3) one month to respond to requests (extendable by two months); Arts 13–14 information; Arts 15–22 rights; Art. 28 processors; Art. 30 records; Art. 32 security; Art. 33 notify the supervisory authority within 72 hours; Art. 34 communicate to data subjects; Chapter V transfers.",
    "id": "R3",
    "issuer": "European Parliament and Council",
    "jurisdiction": "EU / EEA",
    "kind": "regulation",
    "ref": "Regulation (EU) 2016/679",
    "title": "General Data Protection Regulation",
    "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng"
  }
]
```

<!-- end -->
