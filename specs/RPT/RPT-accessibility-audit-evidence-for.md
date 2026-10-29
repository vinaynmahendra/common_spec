---
id: "RPT-accessibility-audit-evidence-for"
title: "Accessibility audit evidence for SEBI-regulated tenants"
parent: "RPT-regulatory-and-aggregator"
order: 4
type: "requirement"
template: "regulatory"
status: "draft"
owner: null
indicative: false
summary: "Accessibility evidence pack (IAAP-certified auditor report, conformance report, remediation tracker, platform and URL list) that the platform supplies to SEBI-regulated tenants and MIIs for their own accessibility compliance reporting"
links: []
rev: 2
syncHash: "2975c3f0dabdb008"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.2.2.4 Accessibility audit evidence for SEBI-regulated tenants

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Accessibility evidence pack (IAAP-certified auditor report, conformance report, remediation tracker, platform and URL list) that the platform supplies to SEBI-regulated tenants and MIIs for their own accessibility compliance reporting

<!-- section:obligation -->
## Obligation and source

SEBI issued a circular dated 31 July 2025 requiring regulated entities to comply with digital accessibility under the Rights of Persons with Disabilities Act, 2016 and its rules, followed by compliance guidelines in September 2025 [R1]. The obligation sits with the **regulated entity** (for example an MII, or a regulated tenant), not with Nomology; a regulated entity remains responsible when its platform is supplied by a vendor.

Assumption (from secondary summaries; legal to confirm against the circular text): the circular requires accessibility audits by IAAP-certified professionals, remediation of findings, an initial list of digital platforms, and annual audit and compliance reporting to the entity's reporting authority (SEBI or the relevant MII). The exact deadlines and report contents must be taken from the circular and guidelines before this node is Approved.

Related nodes: legal register [[APP-accessibility-legal-obligations]], conformance reports [[APP-accessibility-conformance]], conformance target [[APP-accessibility-wcag-2-1-aa]].

<!-- section:applicability -->
## Applicability

Tenants that are SEBI-regulated entities or that serve them (the SEBI ODR institution tenant and any MII using platform pages). Products: CORD pages used by investors and market participants; any tenant-branded public filing pages. Nomology supplies the pack; the tenant submits its own compliance report.

<!-- section:recipient -->
## Recipient and channel

The tenant's compliance or accessibility nodal officer, through `/(tenant-admin)/compliance/accessibility` (download of the pack) and on request by email. The tenant forwards to its reporting authority.

<!-- section:frequency -->
## Frequency and deadlines

Assumption: annually, ahead of the regulated entity's annual report deadline (to be confirmed), and on each major release that changes investor-facing journeys. Proposed internal target: pack available within 15 days after financial-year end (31 March), so tenants have time before their own deadline.

<!-- section:fields -->
## Field mapping

Evidence pack contents:

| Item | Source | Validation |
|---|---|---|
| List of digital platforms / URLs used by the tenant on our platform | tenant domains and route groups in use ([[MT-tenant-resolution]]) | matches tenant's live domains |
| Auditor report: scope, standard (WCAG 2.2 AA; also the standard the circular names, to confirm), method, findings | external audit by IAAP-certified auditor | auditor name, certification ID, date |
| Conformance report (ACR) for the release in use | [[APP-accessibility-conformance]] | release version matches tenant's deployed version |
| Remediation tracker: finding, severity, owner, target date, status, retest result | issue tracker export | every finding has a status; overdue items flagged |
| Accessibility statement for the tenant | per-tenant statement | dated, contact point present |
| Feedback and grievance summary: barriers reported, resolved, time to resolve | [[APP-accessibility-feedback]] | counts reconcile to the feedback log |
| Third-party components and their ACRs | [[INT-third-party-component]] | each embedded vendor listed |

<!-- section:format -->
## Format and template

PDF pack (tagged, accessible) plus a ZIP with the CSV remediation tracker and machine-readable ACR; naming `{tenantCode}_a11y_evidence_{FY}.zip`.

<!-- section:validation -->
## Validation and reconciliation

Auditor certification present and current; audit date within 12 months; every high-severity finding either fixed and retested or with a dated plan; platform list matches the tenant's live domains; pack PDF itself passes accessibility checks.

<!-- section:workflow -->
## Preparation, approval and submission

Prepared by Nomology accessibility lead, reviewed by QA lead, approved by CTO; published to the tenant view; download events audited.

<!-- section:evidence -->
## Evidence and retention

Each pack version kept with its source exports in the region of each tenant it was issued to; retention proposed 8 years.

<!-- section:questions -->
## Open questions

- [ ] Legal: extract exact obligations, deadlines and report contents from the July 2025 circular and the September 2025 guidelines, and any later extension circulars
- [ ] Does the circular reference WCAG 2.2, WCAG 2.1, GIGW or IS 17802, and which applies to our pages
- [ ] Is one platform-wide audit acceptable to tenants, or does each regulated tenant need an audit of its own configuration and branding
- [ ] Budget and appointment of an IAAP-certified external auditor

<!-- checks -->
## Template checks

<!-- check:completeness -->
### Completeness

The platform list is generated from the tenant's live domains and route groups, so no tenant-facing surface is missed; the remediation tracker includes every finding from the audit, not only open ones.

<!-- check:accuracy -->
### Accuracy and reconciliation

Release versions in the ACR and audit are matched against the tenant's deployed version; grievance counts reconcile to the feedback log.

<!-- check:timeliness -->
### Timeliness

Pack published within 15 days after financial-year end (proposed), with reminders to the accessibility lead at T-30 and T-7 days; actual regulatory deadlines to be confirmed from the circular [R1].

<!-- check:retention -->
### Evidence retention

Each issued pack version is kept unchanged with its sources, so a tenant can show its auditor what it received and when.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "SEBI guidelines on how regulated entities comply with the 31 July 2025 digital accessibility circular. Specific audit, reporting and timeline clauses to be extracted by legal before reliance.",
    "id": "R1",
    "issuer": "Securities and Exchange Board of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Compliance guidelines for the digital accessibility circular dated 31 July 2025 (September 2025)",
    "title": "Compliance guidelines for Digital Accessibility Circular – Rights of Persons with Disabilities Act, 2016 and Rules made thereunder – mandatory compliance by all Regulated Entities",
    "url": "https://www.sebi.gov.in/legal/circulars/sep-2025/compliance-guidelines-for-digital-accessibility-circular-rights-of-persons-with-disabilities-act-2016-and-rules-made-thereunder-mandatory-compliance-by-all-regulated-entities-dated-july-31-2025-_96862.html"
  }
]
```

<!-- end -->
