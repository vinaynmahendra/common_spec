---
id: "RPT-regulators"
title: "Regulators"
parent: "RPT-regulatory-and-aggregator"
order: 1
type: "requirement"
template: "regulatory"
status: "draft"
owner: null
indicative: false
summary: "Direct submissions to regulators (RBI, SEBI, IRDAI) owed by tenants or by Nomology entities; currently no confirmed direct obligation, so this node holds the regulator registry and the intake process for confirming one"
links: []
rev: 3
syncHash: "cd4cb02165c4a79c"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.2.2.1 Regulators

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Direct submissions to regulators (RBI, SEBI, IRDAI) owed by tenants or by Nomology entities; currently no confirmed direct obligation, so this node holds the regulator registry and the intake process for confirming one

<!-- section:obligation -->
## Obligation and source

Status: **no direct regulator return is confirmed** for Nomology or for current tenants through the platform.

| Regulator | Known position | Status |
|---|---|---|
| SEBI | Under the SEBI ODR framework, ODR institutions are empanelled by and report through the MIIs, so tenant reporting goes to the MII as an aggregator ([[RPT-aggregators]], [[RPT-example]]) rather than directly to SEBI [R1]. Separate SEBI accessibility requirements for regulated entities are covered in [[RPT-accessibility-audit-evidence-for]] | to be confirmed by legal for each tenant |
| RBI | No known obligation on Nomology. Possible future case: an RBI-regulated tenant using the platform for customer disputes may want reports in a regulator-prescribed shape | none confirmed |
| IRDAI | No known obligation | none confirmed |

A regulator return is added here only after legal records the circular, clause and version in the register in [[RPT-compliance-reports]]; each confirmed return then gets its own child node with a full field mapping.

<!-- section:applicability -->
## Applicability

Would apply to the tenant (or Nomology entity) named in the confirmed rule; no current tenant.

<!-- section:recipient -->
## Recipient and channel

Registry entries (platform-level table `report_recipient`): `recipientKey`, `name`, `kind` (`regulator`), `jurisdiction`, `channels`, `templates`. Entries exist for SEBI, RBI and IRDAI with no active templates.

<!-- section:frequency -->
## Frequency and deadlines

None until confirmed.

<!-- section:fields -->
## Field mapping

None until a return is confirmed. A missing field mapping blocks Approved for any child created here.

<!-- section:validation -->
## Validation and reconciliation

Uses the shared validation in [[RPT-regulatory-and-aggregator#validation]].

<!-- section:changes -->
## Change management

Compliance owner reviews new circulars from SEBI, RBI and IRDAI that mention online dispute resolution, grievance redress or technology service providers at least quarterly and records conclusions in the register.

<!-- section:questions -->
## Open questions

- [ ] Legal: confirm that SEBI ODR reporting by our ODR institution tenants is only to MIIs, and whether any report goes directly to SEBI
- [ ] Are any prospective tenants RBI- or IRDAI-regulated entities that would need regulator-shaped reports from us
- [ ] Owner of the quarterly circular watch

<!-- checks -->
## Template checks

<!-- check:completeness -->
### Completeness

Completeness is handled by the register: each regulator has a row even with no obligation, and the quarterly watch updates it.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Establishes the common ODR portal operated by the MIIs and the empanelment of ODR institutions by MIIs, with timelines for conciliation and arbitration.",
    "id": "R1",
    "issued": "2023-07-31",
    "issuer": "Securities and Exchange Board of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Circular: Online Resolution of Disputes in the Indian Securities Market (31 July 2023)",
    "title": "Online Resolution of Disputes in the Indian Securities Market",
    "url": "https://www.sebi.gov.in/legal/circulars/jul-2023/online-resolution-of-disputes-in-the-indian-securities-market_74794.html"
  }
]
```

<!-- end -->
