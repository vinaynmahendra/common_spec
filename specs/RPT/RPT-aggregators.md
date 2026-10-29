---
id: "RPT-aggregators"
title: "Aggregators"
parent: "RPT-regulatory-and-aggregator"
order: 2
type: "requirement"
template: "regulatory"
status: "draft"
owner: null
indicative: false
summary: "Aggregators (bodies that route matters to the platform and report onward, e.g. NSE as MII for SEBI ODR matters, MSME next) configured as registry entries with templates and channels, not code"
links: []
rev: 3
syncHash: "4ab871ea08734a1e"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.2.2.2 Aggregators

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Aggregators (bodies that route matters to the platform and report onward, e.g. NSE as MII for SEBI ODR matters, MSME next) configured as registry entries with templates and channels, not code

<!-- section:obligation -->
## Obligation and source

Aggregators are bodies that route matters to the platform and report onward to a regulator or ministry. The reporting obligation comes from the aggregator's own rules or circular (for SEBI ODR matters, the SEBI ODR circulars [R1] [R2] and the MII's operating requirements) and from the tenant's agreement with the aggregator. Each aggregator format is its own child node with its own obligation section: [[RPT-example]] (NSE, SEBI ODR), [[ADR-reporting-formats-for-msme-and]] (MSME). Decision: [[ADR-aggregator-reporting]].

<!-- section:applicability -->
## Applicability

Tenants that receive matters from an aggregator: today the SEBI ODR institution tenant (matters allotted through the MIIs' common ODR portal). The tenant's subscription to an aggregator is a tenant-level setting `aggregators.subscriptions[]` with effective dates.

<!-- section:recipient -->
## Recipient and channel

Aggregator registry (platform-level, no `tenant_id`):

| Column | Meaning |
|---|---|
| `aggregator_key` | for example `nse-mii`, `msme-tbd` |
| `name`, `jurisdiction`, `regulator` | for example NSE, India, SEBI |
| `intake_client_id` | API client for [[INT-aggregator-intake-api]] if the aggregator files matters by API |
| `channels` | portal upload / API / SFTP / email, with endpoint config per region |
| `templates` | report template keys and active versions |
| `case_reference_field` | which case field holds the aggregator's matter reference |
| `status` | `planned`, `active`, `retired` |

Adding an aggregator = adding a registry row, intake mapping and template versions; no code change if the mapping catalogue already covers the fields ([[RPT-configurable-report-templates]]).

<!-- section:frequency -->
## Frequency and deadlines

Per aggregator template schedule.

<!-- section:fields -->
## Field mapping

Per child. Common fields every aggregator template is expected to need, already in the mapping catalogue: aggregator matter reference, tenant institution code, date received, current stage mapped to the aggregator's status codes, outcome, key dates (appointment, hearing, award / settlement), amounts claimed and awarded per currency, reason for delay.

<!-- section:validation -->
## Validation and reconciliation

Shared validation in [[RPT-regulatory-and-aggregator#validation]]; population control total is the set of matters received from that aggregator (intake records), which gives a strong completeness check.

<!-- section:changes -->
## Change management

Aggregator format changes become new template versions with effective dates; the registry row lists active and next versions.

<!-- section:questions -->
## Open questions

- [ ] Which aggregators beyond NSE are expected in the next 12 months (other MIIs such as BSE, CDSL, NSDL for SEBI matters; MSME)
- [ ] Is reporting to all MIIs identical, or does each MII have its own format

<!-- checks -->
## Template checks

<!-- check:completeness -->
### Completeness

Because matters arrive through intake records tied to the aggregator, the control total for each report is the count of intake records for the tenant and period, less listed exclusions.

<!-- check:segregation -->
### Tenant and entity segregation

Registry and templates are platform-level; all runs are tenant-scoped under RLS in the tenant's region.

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
  },
  {
    "excerpt": "Consolidates the July 2023 ODR circular and its amendments. The exact reporting clauses relevant to ODR institutions and MIIs are to be extracted by legal before this citation is relied on for a specific field or deadline.",
    "id": "R2",
    "issuer": "Securities and Exchange Board of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Master Circular for Online Resolution of Disputes in the Indian Securities Market (December 2023)",
    "status": "in force (later amendments to be checked)",
    "title": "Master Circular for Online Resolution of Disputes in the Indian Securities Market",
    "url": "https://www.sebi.gov.in/legal/master-circulars/dec-2023/master-circular-for-online-resolution-of-disputes-in-the-indian-securities-market_80236.html"
  }
]
```

<!-- end -->
