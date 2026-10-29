---
id: "RPT-statutory"
title: "Statutory"
parent: "RPT-compliance-reports"
order: 1
type: "feature"
template: "regulatory"
status: "draft"
owner: null
indicative: false
summary: "Parent for filings owed by Nomology's own entities (NTPL, TAPL, US entity): privacy notifications, sanctions / AML records and escalations, FEMA; run in an internal compliance workspace, not per tenant"
links: []
rev: 2
syncHash: "17edeeeb2ff3c75e"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.2.1 Statutory

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Parent for filings owed by Nomology's own entities (NTPL, TAPL, US entity): privacy notifications, sanctions / AML records and escalations, FEMA; run in an internal compliance workspace, not per tenant

<!-- section:obligation -->
## Obligation and source

Parent node for statutory obligations of Nomology's entities rather than of tenants. Children: [[RPT-privacy-and-confidentiality]], [[RPT-aml-kyc-sanctions-screening]], [[RPT-fema-violations]]. Their legal status is tracked in the register in [[RPT-compliance-reports]]; most are event-driven or assumptions awaiting confirmation. None is a routine periodic platform report except possibly FEMA returns (to be confirmed by finance).

<!-- section:applicability -->
## Applicability

| Entity | Jurisdiction | Children that may apply |
|---|---|---|
| NTPL | India | privacy (DPDP, CERT-In via incident process), FEMA, sanctions screening |
| TAPL | Singapore | privacy (PDPA), sanctions screening |
| US entity | United States | privacy (state laws), OFAC sanctions |

<!-- section:recipient -->
## Recipient and channel

Per child. Statutory filings are made by the entity's named officer (for example the DPO / grievance officer, the company secretary, finance controller) through the regulator's portal; the platform prepares content and stores evidence.

<!-- section:frequency -->
## Frequency and deadlines

Mostly event-driven (breach, sanctions match). Periodic only where a child confirms it.

<!-- section:fields -->
## Field mapping

Per child.

<!-- section:validation -->
## Validation and reconciliation

Per child, using the shared checks in [[RPT-regulatory-and-aggregator#validation]].

<!-- section:workflow -->
## Preparation, approval and submission

Runs in Nomology's internal compliance workspace: proposed as an internal tenant `nomology-compliance` in each region, so the same RLS, audit and maker-checker machinery applies and NTPL data stays in India, TAPL data in Singapore. Content that summarises tenant data (for example affected-tenant counts in a breach) is pulled from incident records, not from tenant tables.

<!-- section:questions -->
## Open questions

- [ ] Is an internal compliance tenant per region the right container, or should statutory work live outside the product entirely
- [ ] Named officer per entity for each filing

<!-- checks -->
## Template checks

<!-- check:segregation -->
### Tenant and entity segregation

Statutory work runs in a separate internal compliance tenant per region, so it never mixes with tenant submissions, and each entity's filings stay in that entity's region. Any cross-tenant content comes from the incident register, under the platform reader role.

<!-- end -->
