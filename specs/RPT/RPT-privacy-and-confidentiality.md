---
id: "RPT-privacy-and-confidentiality"
title: "Privacy regulator notifications and filings"
parent: "RPT-statutory"
order: 1
type: "requirement"
template: "regulatory"
status: "draft"
owner: null
indicative: false
summary: "Content, approvals and evidence for event-driven privacy filings: personal data breach notifications (DPDP, GDPR, PDPA, US states) and SDF DPIA / audit filings if NTPL is notified as a Significant Data Fiduciary. No routine periodic report"
links: []
rev: 3
syncHash: "4dbb80e290697ff0"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.2.1.1 Privacy regulator notifications and filings

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Content, approvals and evidence for event-driven privacy filings: personal data breach notifications (DPDP, GDPR, PDPA, US states) and SDF DPIA / audit filings if NTPL is notified as a Significant Data Fiduciary. No routine periodic report

<!-- section:obligation -->
## Obligation and source

Event-driven obligations only; privacy laws in scope impose no routine periodic report on NTPL.

| Law | Key requirement | Reference |
|---|---|---|
| India DPDP Act 2023 | On a personal data breach, the Data Fiduciary gives the Data Protection Board and each affected Data Principal intimation of the breach (s.8(6)) | [R1] |
| India DPDP Rules 2025 | Intimation to the Board without delay, and a detailed report within 72 hours of becoming aware (or a longer period allowed by the Board); intimation to affected Data Principals without delay | [R2] |
| GDPR (EU) | "The controller shall without undue delay and, where feasible, not later than 72 hours after having become aware of it, notify the personal data breach to the supervisory authority"; the processor notifies the controller without undue delay (Art. 33) | [R3] |
| Singapore PDPA | Notify the PDPC no later than 3 calendar days after assessing that a breach is notifiable; notify affected individuals where required | [R4] |
| US state laws | Notification duties to residents and, in some states, to the state attorney general or regulator, with thresholds and content rules that differ by state | Assumption: counsel to provide a state matrix |
| DPDP Act s.10 (SDF) | Periodic Data Protection Impact Assessment and audit, if NTPL is notified as a Significant Data Fiduciary | [R1]; not applicable unless notified |

The clock management and incident decisions are owned by [[SEC-security-incident-response-and]]; this node specifies the **filing content, field mapping, approvals and evidence**.

<!-- section:applicability -->
## Applicability

Role matters more than entity:
- **Case data of a tenant** (parties, counsel, neutrals in an arbitral institution or SEBI ODR institution tenant): assumption: the tenant is the data fiduciary / controller and NTPL (or TAPL / US entity) is a processor under contract. The platform then owes the **tenant** a prompt notice with the facts the tenant needs to file; the tenant files.
- **Data where NTPL is fiduciary** (for example CORD direct users who sign up with NTPL, Nomology staff, marketing contacts): NTPL files with the Board / PDPC / authority itself.
- GDPR applies only where the tenant or NTPL falls within its territorial scope (for example EU-based parties in an institutional arbitration); to be confirmed per tenant.

Assumption to be confirmed by legal: the fiduciary / processor allocation per product and tenant type, recorded in each tenant's DPA.

<!-- section:recipient -->
## Recipient and channel

| Recipient | Channel | Who submits |
|---|---|---|
| Tenant (as fiduciary / controller) | Incident notice by email to the tenant's named security / DPO contact plus an in-app notice in `/(tenant-admin)/compliance/incidents/[incidentId]`; signed PDF and JSON facts pack | Nomology DPO / incident manager |
| Data Protection Board of India | Board's prescribed channel (to be confirmed: digital portal) | NTPL grievance officer / DPO |
| PDPC Singapore | PDPC online breach notification e-service | TAPL DPO |
| EU supervisory authority | Lead authority's online form | Controller (tenant or NTPL) |
| US state authorities | Per state | Counsel |

<!-- section:frequency -->
## Frequency and deadlines

Event-driven. Clock starts at the `aware_at` timestamp recorded on the incident in [[SEC-security-incident-response-and]]. Internal targets (proposed, stricter than law): tenant processor notice within 24 hours of `aware_at`; Board intimation draft within 12 hours; DPDP detailed report draft by `aware_at` + 48 h so review fits inside 72 h; PDPC notice within 1 calendar day after assessed notifiable. All times shown in IST, SGT and the authority's time zone.

<!-- section:fields -->
## Field mapping

Facts pack used for every recipient; each recipient template selects and words the fields. Field names below are the platform's, not any authority's form; each form's labels must be mapped when its current version is obtained.

| Field | Platform source | Transformation | Validation |
|---|---|---|---|
| Incident ID | `incidents.id` | — | required |
| Reporting entity | `incidents.entity` (NTPL / TAPL / US) | legal name and registration from entity registry | required |
| Fiduciary / controller | per affected tenant: `tenants.legal_name`; or NTPL | — | required per affected population |
| Date and time aware | `incidents.aware_at` | to IST / SGT / UTC | required |
| Date and time of breach (or estimate) | `incidents.occurred_from`, `occurred_to` | | `occurred_from ≤ aware_at` |
| Nature of breach | `incidents.category` (confidentiality, integrity, availability) + narrative | | required |
| Categories of personal data | from affected stores × [[SEC-data-classification]] tags | map to plain descriptions | required |
| Number of data principals affected (estimate) | count from affected-records query, per tenant | rounding stated | required; must equal sum per tenant |
| Number of records affected | same | | |
| Regions and systems affected | `incidents.regions`, components | | |
| Likely consequences | narrative | | required |
| Measures taken and proposed | narrative + linked actions | | required |
| Whether data principals are notified, how and when | `incident_notifications` | | required for DPDP |
| Contact point | DPO / grievance officer per entity | | required |
| Cross-border element | whether data left the home region | | required |

Affected-population queries run per tenant under that tenant's context, in the tenant's region, and only counts and categories leave the region.

<!-- section:format -->
## Format and template

Per recipient: PDF letter plus structured JSON for tenants; authority forms filled manually from the generated draft where the authority has a portal form. Naming: `{entity}_{incidentId}_{recipient}_{yyyymmddThhmm}.pdf`.

<!-- section:validation -->
## Validation and reconciliation

- Population counts per tenant sum to the total; categories are non-empty
- Every required field filled; times in order (`occurred_from ≤ aware_at ≤ submitted_at`)
- The draft names the right fiduciary for each affected population
- Legal review recorded before any submission to an authority

<!-- section:workflow -->
## Preparation, approval and submission

Temporal workflow `{tenantId|nomology-compliance}-privacy-notice-{incidentId}-{recipient}` started by the incident process when an incident is marked `personal_data_involved`. Prepared by the incident manager (maker), approved by DPO and legal (checker, different person), submitted by the named officer; each step is a Signal / Update with the actor recorded. Uses the shared pipeline in [[RPT-regulatory-and-aggregator#workflow]].

<!-- section:evidence -->
## Evidence and retention

Kept per submission: generated draft and final file, facts pack snapshot with affected-record query text and counts, approvals, submission time and acknowledgement or portal reference, follow-up correspondence. Stored in `rpt-evidence-<region>` with object lock; retention proposed 7 years from incident close (to be confirmed).

<!-- section:changes -->
## Change management

Authority forms and rules change by notification; the compliance owner reviews DPDP Board, PDPC and EU guidance quarterly and updates recipient templates as new versions ([[RPT-configurable-report-templates]]).

<!-- section:risk -->
## Non-compliance risk

Late or inaccurate breach notification can lead to penalties under DPDP (the Act's schedule sets maximum penalties for failure to notify) and under PDPA / GDPR, and to loss of client trust. Escalation: incident manager → DPO → CTO / CEO.

<!-- section:questions -->
## Open questions

- [ ] Confirm fiduciary / processor allocation per product and tenant type, and update DPAs
- [ ] Confirm the Board's notification channel and form under the DPDP Rules
- [ ] US state matrix (which states, thresholds, regulator notices) for the US entity's users
- [ ] Contractual notice windows promised to tenants (some institutional clients may require shorter windows than law)
- [ ] Evidence retention period

<!-- checks -->
## Template checks

<!-- check:completeness -->
### Completeness

Affected population is computed per tenant from the affected stores identified in the incident record, including search indexes, embeddings, backups and logs listed in [[PKG-data-retention-legal-hold-and]]; each tenant's count is shown, and the total must equal the sum. Every fiduciary involved gets a notice.

<!-- check:accuracy -->
### Accuracy and reconciliation

Counts come from a stored query run under each tenant's context with the query text kept as evidence; times are converted from UTC with the authority's time zone shown; legal reviews wording before submission.

<!-- check:segregation -->
### Tenant and entity segregation

Affected-record queries run in each tenant's region and context; only counts and categories are carried into the facts pack. Each tenant receives only its own population and facts.

<!-- check:timeliness -->
### Timeliness

Clocks start at `aware_at` recorded by the incident process; internal targets are set ahead of the legal limits (72 hours under DPDP Rules [R2] and GDPR [R3]; 3 calendar days after assessment under PDPA [R4]), with alerts at 50% and 80% of each window to the DPO and a backup.

<!-- check:security -->
### Access, approval and transmission

Maker-checker enforced by the workflow (approver ≠ preparer); drafts restricted to incident team, DPO and legal; files encrypted with the regional key; every action audited.

<!-- check:resubmission -->
### Corrections and resubmissions

DPDP Rules and PDPC guidance allow updates as more facts emerge; follow-up notices are new submissions linked to the original, with the differences recorded.

<!-- check:retention -->
### Evidence retention

Full evidence set kept in the region's object-locked bucket; retention period to be confirmed by legal (proposed 7 years). The facts pack holds counts, not personal data, so erasure requests do not conflict with it.

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
  }
]
```

<!-- end -->
