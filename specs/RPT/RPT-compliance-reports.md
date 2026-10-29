---
id: "RPT-compliance-reports"
title: "Compliance reports"
parent: "RPT"
order: 2
type: "capability"
template: "regulatory"
status: "draft"
owner: null
indicative: false
summary: "Register of every statutory, regulator and aggregator reporting obligation (confirmed or assumed), who owes it, and the shared rules all submissions follow"
links: []
rev: 4
syncHash: "22e621ff49c6a6ac"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.2 Compliance reports

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Register of every statutory, regulator and aggregator reporting obligation (confirmed or assumed), who owes it, and the shared rules all submissions follow

<!-- section:obligation -->
## Obligation and source

Parent node. It holds the **obligation register**: one row per reporting obligation, its legal source, status of legal confirmation, and the child node that specifies it. No row may be described as mandatory until its status is `confirmed` by legal with the exact clause recorded.

| # | Obligation | Source (to be verified clause by clause) | Owed by | Status | Node |
|---|---|---|---|---|---|
| 1 | Personal data breach notification (India) | DPDP Act 2023 s.8(6) and DPDP Rules 2025 breach rule [R1] [R2] | Data fiduciary: usually the tenant for case data; NTPL for its own account data (assumption) | confirmed as law; allocation of roles to confirm | [[RPT-privacy-and-confidentiality]] |
| 2 | Breach notification (EU, Singapore, US states) | GDPR Art. 33 [R3]; PDPA breach guide [R4]; US state laws (to be listed by counsel) | Controller / organisation; processor informs controller | applicability per tenant to confirm | [[RPT-privacy-and-confidentiality]] |
| 3 | SDF DPIA and audit | DPDP Act s.10 [R1] | NTPL only if notified as a Significant Data Fiduciary | not applicable unless notified | [[RPT-privacy-and-confidentiality]] |
| 4 | Sanctions / AML screening records and escalations | OFAC rules for US persons; India and Singapore counter-terrorist-financing laws; PMLA only if an entity is a reporting entity | US entity (OFAC); others to confirm | assumption, counsel to confirm | [[RPT-aml-kyc-sanctions-screening]] |
| 5 | FEMA filings for NTPL (for example overseas investment in TAPL, export of services) | FEMA 1999 and RBI regulations | NTPL | assumption, finance / CA to confirm | [[RPT-fema-violations]] |
| 6 | SEBI ODR status reporting to an MII | SEBI ODR circulars [R5] | Tenant (ODR institution) | clause and format to obtain | [[RPT-example]] |
| 7 | MSME aggregator reporting | to be identified | Tenant or aggregator contract | unknown | [[ADR-reporting-formats-for-msme-and]] |
| 8 | Accessibility evidence for SEBI-regulated tenants | SEBI digital accessibility circular and compliance guidelines [R6] | Regulated tenant (the platform supplies evidence) | clauses to extract | [[RPT-accessibility-audit-evidence-for]] |
| 9 | Direct returns to RBI, SEBI, IRDAI | none confirmed | — | none confirmed | [[RPT-regulators]] |
| 10 | CERT-In incident reporting | CERT-In directions [R7] | NTPL as service provider | confirmed as law; process owned by [[SEC-security-incident-response-and]] | (not a report here) |

<!-- section:applicability -->
## Applicability

Two groups:
- **Statutory** ([[RPT-statutory]]): obligations of Nomology's own entities (NTPL, TAPL, US entity), run in Nomology's internal compliance workspace.
- **Regulatory and aggregator** ([[RPT-regulatory-and-aggregator]]): obligations of tenants (or contractual reporting to an aggregator), run inside the tenant's context and region.

<!-- section:recipient -->
## Recipient and channel

Per child. All recipients and channels are listed in the aggregator / regulator registry in [[RPT-aggregators]] and [[RPT-regulators]].

<!-- section:frequency -->
## Frequency and deadlines

Per child. A compliance calendar view in `/(tenant-admin)/compliance` and `/(platform-admin)/compliance` lists every upcoming deadline from all children with status, built from `submission` rows and event-driven triggers.

<!-- section:fields -->
## Field mapping

Field mappings live in each child that specifies a prescribed format. This node defines only the register fields: `obligation_id`, `title`, `source_ref`, `source_clause`, `source_version`, `jurisdiction`, `owed_by_entity`, `tenant_scope`, `status` (`assumed`, `confirmed`, `not_applicable`, `retired`), `confirmed_by`, `confirmed_at`, `node_key`, `review_due`.

<!-- section:validation -->
## Validation and reconciliation

Register rules: every `confirmed` row has a clause and a named legal confirmer; every row is reviewed at least annually (`review_due`); a child node cannot reach Approved while its register row is `assumed`.

<!-- section:workflow -->
## Preparation, approval and submission

Shared submission pipeline: see [[RPT-regulatory-and-aggregator#workflow]]. Register changes are approved by the compliance owner and recorded in the audit trail.

<!-- section:evidence -->
## Evidence and retention

Each submission's evidence set is defined in [[RPT-regulatory-and-aggregator#evidence]]; the register itself is versioned so that the state of known obligations on any date can be shown to an auditor.

<!-- section:questions -->
## Open questions

- [ ] Legal to confirm or reject every `assumed` row, with clause references
- [ ] Who owns the register (proposed: Nomology compliance lead, with CTO as technical owner)
- [ ] Are tenants shown the register rows that concern them, as a service

<!-- checks -->
## Template checks

<!-- check:completeness -->
### Completeness

Completeness here means completeness of the register: every regulation in scope in the agent brief (DPDP, GDPR, PDPA, US state laws, SEBI ODR, MSME, AML / KYC / sanctions, FEMA, accessibility, CERT-In) has a row, even when the conclusion is "none confirmed". The annual review re-checks new circulars.

<!-- check:timeliness -->
### Timeliness

The compliance calendar aggregates every deadline across children so a missed obligation is visible in one place; each child owns its own alerts.

<!-- check:retention -->
### Evidence retention

The register is versioned (append-only history) so an auditor can see what was known and confirmed at any date.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Section 8(6): in the event of a personal data breach the Data Fiduciary shall give the Board and each affected Data Principal intimation of the breach. Section 10: additional obligations of a Significant Data Fiduciary, including periodic Data Protection Impact Assessment and audit.",
    "id": "R1",
    "issuer": "Government of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Digital Personal Data Protection Act, 2023 (No. 22 of 2023)",
    "title": "Digital Personal Data Protection Act, 2023",
    "url": "https://www.meity.gov.in/static/uploads/2024/02/Digital-Personal-Data-Protection-Act-2023.pdf"
  },
  {
    "excerpt": "Rule on intimation of personal data breach: the Data Fiduciary informs the Board without delay and gives a detailed report within seventy-two hours of becoming aware of the breach (or a longer period the Board allows).",
    "id": "R2",
    "issuer": "Ministry of Electronics and Information Technology, Government of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Digital Personal Data Protection Rules, 2025",
    "title": "Digital Personal Data Protection Rules, 2025 (gazette notification)",
    "url": "https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf"
  },
  {
    "clause": "Article 33",
    "excerpt": "The controller shall without undue delay and, where feasible, not later than 72 hours after having become aware of it, notify the personal data breach to the supervisory authority ... The processor shall notify the controller without undue delay after becoming aware of a personal data breach.",
    "id": "R3",
    "issuer": "European Parliament and Council",
    "jurisdiction": "EU",
    "kind": "regulation",
    "ref": "Regulation (EU) 2016/679",
    "title": "GDPR Article 33: Notification of a personal data breach to the supervisory authority (as adopted)",
    "url": "https://www.legislation.gov.uk/eur/2016/679/article/33/adopted"
  },
  {
    "excerpt": "Organisations must notify the PDPC as soon as practicable, and no later than 3 calendar days after assessing that a data breach is notifiable.",
    "id": "R4",
    "issuer": "Personal Data Protection Commission, Singapore",
    "jurisdiction": "Singapore",
    "kind": "regulation",
    "ref": "Guide on Managing and Notifying Data Breaches under the PDPA (15 March 2021)",
    "title": "Guide on Managing and Notifying Data Breaches under the PDPA",
    "url": "https://www.pdpc.gov.sg/-/media/files/pdpc/pdf-files/other-guides/guide-on-managing-and-notifying-data-breaches-under-the-pdpa-15-mar-2021.pdf"
  },
  {
    "excerpt": "Consolidates the July 2023 ODR circular and its amendments. The exact reporting clauses relevant to ODR institutions and MIIs are to be extracted by legal before this citation is relied on for a specific field or deadline.",
    "id": "R5",
    "issuer": "Securities and Exchange Board of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Master Circular for Online Resolution of Disputes in the Indian Securities Market (December 2023)",
    "status": "in force (later amendments to be checked)",
    "title": "Master Circular for Online Resolution of Disputes in the Indian Securities Market",
    "url": "https://www.sebi.gov.in/legal/master-circulars/dec-2023/master-circular-for-online-resolution-of-disputes-in-the-indian-securities-market_80236.html"
  },
  {
    "excerpt": "SEBI guidelines on how regulated entities comply with the 31 July 2025 digital accessibility circular. Specific audit, reporting and timeline clauses to be extracted by legal before reliance.",
    "id": "R6",
    "issuer": "Securities and Exchange Board of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Compliance guidelines for the digital accessibility circular dated 31 July 2025 (September 2025)",
    "title": "Compliance guidelines for Digital Accessibility Circular – Rights of Persons with Disabilities Act, 2016 and Rules made thereunder – mandatory compliance by all Regulated Entities",
    "url": "https://www.sebi.gov.in/legal/circulars/sep-2025/compliance-guidelines-for-digital-accessibility-circular-rights-of-persons-with-disabilities-act-2016-and-rules-made-thereunder-mandatory-compliance-by-all-regulated-entities-dated-july-31-2025-_96862.html"
  },
  {
    "excerpt": "Cyber incidents of the listed types must be reported to CERT-In within 6 hours of noticing; logs of ICT systems must be maintained for a rolling period of 180 days within Indian jurisdiction.",
    "id": "R7",
    "issued": "2022-04-28",
    "issuer": "CERT-In, Ministry of Electronics and Information Technology",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Directions under section 70B(6) of the IT Act, 2000 (No. 20(3)/2022-CERT-In)",
    "title": "CERT-In Directions relating to information security practices, procedure, prevention, response and reporting of cyber incidents",
    "url": "https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf"
  }
]
```

<!-- end -->
