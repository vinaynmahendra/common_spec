---
id: "SEC-privacy-controls"
title: "Privacy controls"
parent: "SEC"
order: 2
type: "capability"
template: "control"
status: "draft"
owner: null
indicative: false
summary: "consent management, data subject requests, retention and deletion, data minimisation"
links: []
rev: 2
syncHash: "b5f570bdb33449a9"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 13.2 Privacy controls

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> consent management, data subject requests, retention and deletion, data minimisation

<!-- section:objective -->
## Control objective

Personal data on the platform is processed only for stated purposes, on a valid legal basis, kept no longer than needed, and handled so that people can exercise their rights — while the legal record of a dispute stays complete. Each processing activity has a known role for Nomology (data fiduciary / controller, or data processor) and the matching obligations are met under India's DPDP Act and Rules [R1][R2], GDPR [R3] and Singapore's PDPA, and US state privacy laws where they apply.

This is the parent privacy control; specific controls sit in children: [[SEC-consent-and-notice-management]], [[SEC-data-principal-rights-requests]], [[SEC-privacy-notice-copy]].

<!-- section:mapping -->
## Framework mapping

| Obligation | DPDP Act 2023 / Rules 2025 | GDPR | PDPA (Singapore) | ISO/IEC 27001:2022 | SOC 2 |
|---|---|---|---|---|---|
| Notice | s.5; Rule 3 | Arts 13–14 | s.20 notification | A.5.34 | P1 |
| Consent and withdrawal | s.6; consent managers s.6(7)–(9), Rule 4 | Arts 6–7 | ss.13–17 | A.5.34 | P2 |
| Legitimate uses / other bases | s.7; exemptions s.17 | Art. 6(1)(b)–(f) | Schedules (exceptions, legitimate interests) | — | P2 |
| Purpose limitation and minimisation | s.4–s.6 (specified purpose) | Art. 5(1)(b)–(c) | purpose limitation s.18 | A.5.34 | P3 |
| Accuracy | s.8(3) | Art. 5(1)(d) | accuracy s.23 | — | P7 |
| Retention and erasure | s.8(7); Rule 8 (log retention one year) | Art. 5(1)(e), Art. 17 | retention limitation s.25 | A.8.10 | P4 |
| Rights | ss.11–14; Rule 14 | Arts 15–22 | ss.21–22 | A.5.34 | P5 |
| Security safeguards | s.8(5); Rule 6 | Art. 32 | protection s.24 | Annex A | CC6, CC7 |
| Breach | s.8(6); Rule 7 | Arts 33–34 | Part 6A | A.5.24–5.28 | CC7.3–7.5 |
| Processors | s.8(2) | Art. 28 | data intermediaries | A.5.19–5.20 | CC9.2 |
| Children and persons with disability | s.9; Rules on verifiable consent | Art. 8 | — | — | — |
| Records of processing | (implied by accountability) | Art. 30 | accountability s.11–12 | A.5.34 | P8 |
| Transfers | s.16 | Chapter V | s.26 transfer limitation | A.5.14 | — |
| Grievance officer / DPO | s.8(9)–(10) | Arts 37–39 | s.11(3) DPO | A.5.2 | — |

<!-- section:description -->
## Control description

1. **Roles register.** For each product and tenant type, record Nomology's role:

| Processing | Typical role of Nomology | Data fiduciary / controller |
|---|---|---|
| Case data for an arbitral institution tenant | Data processor / processor | The institution |
| Case data for a SEBI ODR institution tenant | Data processor | The ODR institution (assumption; legal to confirm) |
| Case data for the CORD tenant | Data fiduciary / controller (assumption) | NTPL |
| Tenant staff accounts | Processor for the tenant; fiduciary for platform security logs | Tenant / NTPL |
| Billing contacts, marketing, website visitors | Fiduciary / controller | NTPL, TAPL or US entity |

2. **Records of processing (RoPA).** One entry per processing activity: purpose, data categories ([[SEC-data-classification]]), data principals, legal basis, retention ([[PKG-retention-and-deletion-schedule]]), recipients and sub-processors ([[SEC-vendor-sub-processor-management]]), region, transfers, security measures. Generated partly from the column classification file so it stays in step with the schema.
3. **Privacy by design review (DPIA-lite).** Every new feature that adds a personal data field, a new purpose, a new recipient or AI processing gets a privacy review in the spec (the `privacy` / `data-protection` checks in templates) and, if high risk (large-scale sensitive data, AI decisions affecting parties, new transfers), a full DPIA signed by the DPO.
4. **Minimisation rules.** Collect only fields required by the institution's rules or the procedure; optional fields are marked optional; KYC data is limited to what the screening provider needs; AI prompts are redacted by default ([[AI-guardrails]]).
5. **Retention.** Schedules per entity type and tenant in [[PKG-data-retention-legal-hold-and]]; deletion and anonymisation jobs; legal holds; offboarding deletion ([[MT-tenant-lifecycle]]).
6. **Legal-record conflict rule.** Where a rights request (erasure, correction) conflicts with a legal record (a pleading as filed, an award, a procedural order), the record is preserved unchanged, the request is answered with the legal basis for retention, and a correction note may be attached rather than altering the record. Assumption: DPDP s.17(1)(a) (enforcing legal rights or claims) and similar provisions support this; to be confirmed by legal.
7. **Processor duties to tenants.** Assist tenants with rights requests, breach notification, DPIAs; act only on documented instructions; delete or return data at the end of services.
8. **Training.** Privacy module for all staff; specific training for support staff on support access and rights requests.

<!-- section:owner -->
## Owner and frequency

Owner: DPO / Grievance Officer (named role; DPDP requires publishing contact details of a person who can answer questions, s.8(9)). Backup: legal counsel. Operators: product owners (privacy reviews), engineering (retention jobs), support (request intake). Frequency: RoPA reviewed quarterly and on change; DPIAs per feature; annual privacy programme review in the ISMS management review.

<!-- section:evidence -->
## Evidence

- Roles register and RoPA with version history (3 years after superseded).
- Privacy reviews and DPIAs per feature (life of the feature + 3 years).
- Retention job run logs and deletion verification reports (3 years).
- Training records.
- Processor assistance records (requests from tenants and our responses).

<!-- section:test -->
## Test procedure

Auditor reconciles a sample of 10 processing activities in the RoPA against the system (fields exist, retention configured, sub-processors match); samples 5 features launched in the period for a privacy review / DPIA; inspects retention job logs for 2 sampled months.

<!-- section:implementation -->
## Implementation in the platform

[[PKG-data-retention-legal-hold-and]], [[PKG-retention-and-deletion-schedule]], [[SEC-data-classification]], [[AI-guardrails]], [[SEC-consent-and-notice-management]], [[SEC-data-principal-rights-requests]], [[I18N-legal-declaration-and-consent]] (versioned legal text).

<!-- section:exceptions -->
## Exceptions

Processing that cannot meet a rule (for example a tenant instructs a longer retention) is recorded with the tenant's instruction and the DPO's review; for fiduciary processing, exceptions need DPO and legal approval and a documented basis.

<!-- section:metrics -->
## Monitoring and KPIs

- Processing activities without RoPA entries (target 0).
- Features launched without privacy review (target 0).
- Retention jobs failed or overdue (target 0 older than 7 days).
- Rights requests on time (from [[SEC-data-principal-rights-requests]]).

<!-- section:questions -->
## Open questions

- [ ] Confirm Nomology's role per product and tenant type (especially CORD and SEBI ODR tenants). Owner: legal.
- [ ] Confirm which DPDP exemptions (s.17(1)(a) legal claims; s.17(1)(b) judicial / quasi-judicial bodies) apply to arbitration and ODR processing. Owner: legal.
- [ ] Dates from which the DPDP Rules' substantive obligations apply (Rules 3 and 5–16 commence eighteen months after publication) [R2]; plan to be compliant before then.
- [ ] Is a GDPR Art. 27 EU representative needed (EU parties in arbitrations where Nomology is controller)?
- [ ] Which US state laws apply given thresholds (likely few, as Nomology is mainly a processor for US tenants)?

<!-- checks -->
## Template checks

<!-- check:scope -->
### Scope and population

All processing of personal data by NTPL, TAPL and the US entity on the platform and in supporting operations, in every region, for every tenant type. The population is the RoPA, reconciled with the classification file and the vendor register.

<!-- check:owner -->
### Ownership and accountability

DPO owns design and accountability for privacy operations; product and engineering operate controls; legal counsel covers; CTO is accountable at management level.

<!-- check:deficiency -->
### Failures and remediation

A processing activity found without basis or notice is paused or limited where possible, assessed by the DPO, and if personal data was processed unlawfully at scale, handled through the incident process for possible notification.

<!-- check:commitments -->
### Legal and client commitments

DPDP, GDPR and PDPA duties as mapped; client DPAs (processor duties, assistance, deletion at end of contract). Changes to retention or roles can break these and need DPO approval.

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
