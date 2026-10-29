---
id: "SEC-data-classification"
title: "Data classification"
parent: "SEC"
order: 3
type: "capability"
template: "control"
status: "draft"
owner: null
indicative: false
summary: "Data classification scheme and confidentiality tiers (public, tenant-internal, case participants, tribunal-only)"
links: []
rev: 3
syncHash: "a0e55b78504b1ea0"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 13.3 Data classification

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Data classification scheme and confidentiality tiers (public, tenant-internal, case participants, tribunal-only)

<!-- section:objective -->
## Control objective

Every piece of information the platform holds has a known classification and confidentiality tier, so that access rules, encryption, logging, retention and sharing are applied consistently and no case document, personal data or tribunal-only material is handled as if it were less sensitive than it is.

<!-- section:mapping -->
## Framework mapping

| Framework | Clause |
|---|---|
| ISO/IEC 27001:2022 [R1] | A.5.12 Classification of information; A.5.13 Labelling of information; A.5.10 Acceptable use of information and other associated assets; A.5.9 Inventory of information and other associated assets; A.8.11 Data masking; A.8.12 Data leakage prevention |
| SOC 2 TSC | C1.1 (identify and maintain confidential information), CC6.1 |
| DPDP Act | s.8(5) reasonable security safeguards (classification drives safeguards) |
| GDPR | Art. 32 (appropriate measures given the nature of data); Art. 9 / 10 special categories |
| PDPA | Protection obligation |

<!-- section:description -->
## Control description

**Two axes.** Every data element gets a **sensitivity class** (what kind of data it is) and, for case material, a **confidentiality tier** (who in the case may see it).

**Sensitivity classes**

| Class | Meaning | Examples | Minimum handling |
|---|---|---|---|
| Public | Approved for publication | Published rules, public awards a tenant chose to publish, marketing site | Integrity controls only |
| Internal | Nomology or tenant operational data with low harm if disclosed | Feature flags, non-personal configuration | Access by role; no public sharing |
| Confidential | Business-sensitive or case data | Pleadings metadata, invoices, tenant rules, audit trail | RLS + role; encrypted at rest; not in logs |
| Personal | Personal data under DPDP / GDPR / PDPA | Names, emails, phone numbers, addresses of parties and users | As Confidential, plus masking in support views, minimisation, rights handling |
| Sensitive personal | Data whose disclosure causes serious harm or is specially regulated | Identity documents and KYC results, bank details, health or criminal information in evidence, data of children, biometric liveness outputs | As Personal, plus field-level encryption ([[PKG-encryption-utilities-key]]), access logged on read, excluded from search snippets and AI prompts by default |
| Secret | Credentials and keys | API keys, signing keys, database passwords | Secrets manager only ([[INF-secrets-and-keys]]); never in database rows in clear, never in logs |

**Confidentiality tiers for case material** (enforced by [[PKG-rbac-abac-case-level-party]] and restrictive RLS policies on case tables)

| Tier | Who may see | Examples |
|---|---|---|
| Public | Anyone | Published award (if the tenant publishes) |
| Tenant-internal | Tenant staff (secretariat, tenant admin) | Internal notes, conflict check results, fee calculations |
| Case participants | Parties, counsel, tribunal and secretariat of that case | Pleadings, evidence, procedural orders, hearing recordings |
| Party-restricted | One party (and its counsel), tribunal and secretariat | Ex parte applications where permitted, a party's own payment details |
| Tribunal-only | Tribunal members and tribunal secretary (and secretariat if the rules allow) | Deliberation notes, draft awards, AI drafting workspace content |

**How classification is applied**

1. Every table column in a schema node is classified in its Tables section ([[MT-tenancy-and-identity-schema#tables]] is the pattern) and in `packages/db/data-classification.yaml`; CI fails if a new column has no class.
2. Documents carry a `confidentiality_tier` set at upload (default: case participants) and changeable only by the secretariat or tribunal with an audit record ([[DOM-documents-schema]]).
3. Labelling: generated PDFs carry a footer with the tier; the UI shows the tier badge on documents ([[PKG-status-and-deadline-badges]]).
4. Handling rules per class (logging, export, AI use, search indexing, backup, retention) are in the handling matrix below.
5. Owners: the data owner for case data is the tenant; for platform data, the owning team.

**Handling matrix (summary)**

| Rule | Confidential | Personal | Sensitive personal | Secret |
|---|---|---|---|---|
| In application logs / traces | Ids only | No | No | No |
| In Temporal payloads | Encrypted via codec | Encrypted, ids preferred | Ids only | No |
| In search index | Yes, tenant-scoped | Names yes; contact details no | No | No |
| Sent to AI providers | Per tenant opt-in ([[AI-ai-governance-and-impact]]) | Redacted by default ([[AI-guardrails]]) | No by default | No |
| In warehouse / reporting | Aggregated | Pseudonymised | Excluded | No |
| In support views | Yes under support access | Masked | Hidden | No |

<!-- section:owner -->
## Owner and frequency

Owner: ISMS lead (scheme). Backup: DPO. Operators: schema owners (column classification), secretariat and tribunal (document tiers). Frequency: scheme reviewed annually; classification checked on every schema change (CI); quarterly sample review of document tiers in two tenants (with tenant permission) or in staging data.

<!-- section:evidence -->
## Evidence

- Versioned classification scheme and handling matrix (document management system).
- `data-classification.yaml` history and CI results showing no unclassified columns (evidence repository, 3 years).
- Audit records of document tier changes ([[PKG-audit-trail]]).
- Log scanning reports showing no personal data patterns in logs (weekly job, results retained 1 year).

<!-- section:test -->
## Test procedure

Auditor selects 25 columns at random from the production schema and checks class and handling (masking, encryption, log exclusion) matches the matrix; selects 5 documents with tier changes and checks the audit record; reviews the latest 4 log-scan reports.

<!-- section:implementation -->
## Implementation in the platform

[[PKG-encryption-utilities-key]] (field-level encryption for sensitive personal), [[PKG-rbac-abac-case-level-party]] (tier enforcement), [[DOM-documents-schema]] (tier column), [[OBS-foundations]] (log redaction), [[AI-guardrails]] (redaction before AI calls), [[PKG-search]] (index exclusions).

<!-- section:exceptions -->
## Exceptions

A table or document type that cannot follow the handling matrix (for example a vendor that requires a personal field in a webhook payload) is raised as an exception with the DPO's approval and a compensating control, maximum 6 months.

<!-- section:metrics -->
## Monitoring and KPIs

- Unclassified columns in production: 0.
- Personal-data findings in log scans per week (target 0; any finding fixed within 5 working days).
- Documents with tier changed after sharing (monitored for misuse).

<!-- section:questions -->
## Open questions

- [ ] Do institutional rules (for example confidentiality provisions in an institution's arbitration rules) require additional tiers? To be checked per tenant during onboarding.
- [ ] Should the default tier for uploaded evidence be "case participants" for all tenant types, or tenant-configurable?
- [ ] Which data types are "sensitive personal" for DPDP purposes (the Act has no special-category list, unlike GDPR)? Proposed: use the GDPR list plus financial and identity data; DPO to confirm.

<!-- checks -->
## Template checks

<!-- check:scope -->
### Scope and population

All data in all regional databases, object storage, search, Temporal, logs and the warehouse; all generated documents; tenant configuration. The population is the Prisma schema plus document types, enforced by CI so new columns cannot appear unclassified.

<!-- check:automation -->
### Automation and continuous monitoring

Column classification check in CI and weekly log scanning are automated; document tier assignment is a user action with a default; the scheme and handling rules are manual and reviewed annually.

<!-- check:deficiency -->
### Failures and remediation

An unclassified column blocks merge; a log-scan finding is a minor nonconformity fixed within 5 working days, escalated to an incident if personal data reached a store outside the region or outside approved access.

<!-- check:commitments -->
### Legal and client commitments

Client contracts and institutional rules promise confidentiality of case material; classification and tiers are how that promise is implemented, so changing the scheme needs DPO and legal review.

<!-- citations -->
## Citations

```json
[
  {
    "body": "ISO/IEC",
    "excerpt": "Clauses 4–10 (ISMS requirements) and Annex A reference controls (93 controls in four themes).",
    "id": "R1",
    "ident": "ISO/IEC 27001",
    "kind": "standard",
    "title": "Information security, cybersecurity and privacy protection — Information security management systems — Requirements",
    "url": "https://www.iso.org/standard/27001",
    "version": "2022"
  }
]
```

<!-- end -->
