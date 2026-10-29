---
id: "RPT-industry-marketing"
title: "Industry / marketing"
parent: "RPT-mis-and-miscellaneous"
order: 2
type: "feature"
template: "report"
status: "draft"
owner: null
indicative: false
summary: "Figures Nomology publishes or submits externally (industry surveys such as GAR, Nomology ODR publications): aggregated, suppressed, approved, and with tenant consent where a tenant could be identified"
links: []
rev: 2
syncHash: "8683b04408592281"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.3.2 Industry / marketing

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Figures Nomology publishes or submits externally (industry surveys such as GAR, Nomology ODR publications): aggregated, suppressed, approved, and with tenant consent where a tenant could be identified

<!-- section:audience -->
## Audience and questions

| Audience | Frequency | Questions |
|---|---|---|
| Marketing / CCO preparing an external publication or survey response | annual or per campaign | Q1 How many disputes were handled on our platforms, by type, value band, region and outcome? Q2 How fast were they resolved? Q3 What share were resolved fully online? |
| Survey or publication recipients (for example Global Arbitration Review for GAR publications; Nomology's own "ODR Insights") | per edition | The same, in the recipient's questionnaire format |

Assumption: what is submitted for GAR 100 or similar surveys, and whether it relates to Nomology or to tenant institutions, is to be confirmed by the CCO. Tenant institutions may report their own caseload; Nomology must not publish a tenant's figures without that tenant's written consent.

<!-- section:metrics -->
## Metric definitions

| ID | Metric | Formula | Grain | Rule |
|---|---|---|---|---|
| IND-M1 | Disputes handled | count of cases registered in the period (CASE-M6) | product × dispute category × region × year | suppress any cell < 10 (proposed, stricter than internal) |
| IND-M2 | Disputes resolved | cases closed with outcome settled / award / resolved (CASE-M7) | same | |
| IND-M3 | Median days to resolution | median CASE-M8 | product × category × year | only cells with ≥ 30 cases |
| IND-M4 | Value band distribution | count by claim value band, per currency | product × year | |
| IND-M5 | Online share | cases with all hearings virtual and all filings electronic ÷ closed cases | product × year | |

Every figure carries its definition, period and "source: Nomology platform data" in the publication notes.

<!-- section:dimensions -->
## Dimensions and filters

Year, product, dispute category (mapped from tenant case types to a public category list), region (country-level only), outcome.

<!-- section:freshness -->
## Freshness and delivery

Built on request from frozen year-end MIS snapshots; never from live data.

<!-- section:lineage -->
## Data sources and lineage

From [[RPT-internal-mis]] frozen snapshots; mapping of case types to public categories is a versioned table owned by marketing with product review.

<!-- section:quality -->
## Data quality and reconciliation

Totals reconcile to the frozen MIS snapshot; suppression applied and tested; a second person checks every published number against the generated workbook (maker-checker).

<!-- section:access -->
## Access and privacy

Prepared by marketing with `platform.mis.view`; approved by CCO and a founder; tenant consent recorded for any tenant-identifiable figure; legal review where a publication describes regulated (SEBI ODR) matters.

<!-- section:questions -->
## Open questions

- [ ] Confirm what GAR or other surveys actually ask for and whether Nomology or the tenant is the respondent
- [ ] Public category list for disputes
- [ ] Do any tenant contracts forbid use of their aggregated data in Nomology marketing even when not identifiable

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

No tenant user ever sees this report. Figures are built from aggregate snapshots across tenants; any figure that could identify a tenant (for example one large institution in a country) requires that tenant's recorded consent.

<!-- check:residency -->
### Residency and cross-region figures

Country-level aggregates with suppression, built from `rpt_mis` snapshots; no personal data leaves any region.

<!-- check:definitions -->
### Metric semantics

Each public figure reuses an internal metric ID (CASE-M6, M7, M8) and is published with its definition and period, so readers can compare editions.

<!-- check:security -->
### Access, privacy and export

Maker-checker on every published number, CCO and founder approval, tenant consent records, legal review for regulated-matter statements.

<!-- end -->
