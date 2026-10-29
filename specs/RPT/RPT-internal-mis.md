---
id: "RPT-internal-mis"
title: "Internal MIS"
parent: "RPT-mis-and-miscellaneous"
order: 1
type: "feature"
template: "report"
status: "draft"
owner: null
indicative: false
summary: "Nomology management information: tenants, case volumes, usage against plan, revenue and collections from Billing, operational health and AI cost, by region, entity and product"
links: []
rev: 2
syncHash: "a862fcc281467a87"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.3.1 Internal MIS

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Nomology management information: tenants, case volumes, usage against plan, revenue and collections from Billing, operational health and AI cost, by region, entity and product

<!-- section:audience -->
## Audience and questions

| Persona | Frequency | Questions |
|---|---|---|
| Founders / management | monthly, quarterly board pack | Q1 How many active tenants and cases do we have, by product, region and segment, and how is that trending? Q2 What is revenue billed and collected by entity (NTPL, TAPL, US entity)? |
| Account managers | weekly | Q3 Which tenants are near or over plan entitlements, or inactive? |
| CTO / engineering | monthly | Q4 Are we meeting platform SLOs, and what is the cost per region and per case? Q5 What is AI spend per tenant against budget? |
| COO / operations | weekly | Q6 Where are operational backlogs (transcription, bundling, approvals) across tenants? |

<!-- section:metrics -->
## Metric definitions

| ID | Metric | Formula | Grain | Source / owner |
|---|---|---|---|---|
| MIS-M1 | Active tenants | tenants with `status = active` and activity in last 30 days (see parent) | segment × region × month | tenant directory; Platform team |
| MIS-M2 | Cases registered / closed | sum of CASE-M6 / CASE-M7 | tenant × month (suppressed in external use) | [[RPT-cases]] aggregates |
| MIS-M3 | Open case backlog | CASE-M1 at month end | tenant × month | [[RPT-cases]] |
| MIS-M4 | Entitlement usage | usage ÷ entitlement for cases, seats, storage, AI tokens | tenant × month | [[BIL-plans-entitlements-and-usage]] |
| MIS-M5 | Revenue billed | invoice totals by billing entity and currency, as reported by Billing, not recomputed | entity × currency × month | [[BIL-revenue-reporting-hooks-for]] |
| MIS-M6 | Collections and receivables | cash received; receivables ageing | entity × currency × month | Billing / accounting sync |
| MIS-M7 | SLO attainment | from [[RPT-platform-performance]] | region × month | Platform |
| MIS-M8 | Infrastructure cost per region | cloud bill by `region` and `component` tags | region × month | FinOps export |
| MIS-M9 | Cost per active case | MIS-M8 ÷ open cases (MIS-M3) | region × month | derived |
| MIS-M10 | AI spend vs budget | from [[RPT-platform-ai-usage-analytics]] | tenant × month | AI platform |

Currency: platform totals converted to INR (NTPL view), SGD (TAPL) and USD (US entity) using month-end reference rates from a rate source to be chosen by finance; per-currency figures always shown alongside.

<!-- section:dimensions -->
## Dimensions and filters

Region, entity, product, tenant segment, tenant (internal only), month / quarter / financial year (April–March for NTPL; TAPL and US entity financial years to confirm).

<!-- section:layout -->
## Layout and views

Board pack: one page per question with headline numbers, 13-month trend and a table. Weekly flash: tiles for MIS-M1–M3, MIS-M6 receivables, MIS-M7 breaches.

<!-- section:freshness -->
## Freshness and delivery

Weekly flash every Monday; monthly figures frozen after finance close (business day 5, proposed) as a versioned snapshot so board numbers do not move afterwards. Restatements produce a new version with a change note.

<!-- section:lineage -->
## Data sources and lineage

MIS reads only `rpt_mis.*` models produced in each region and Billing's revenue hooks; it never recomputes revenue. Cost from the cloud billing export tagged per [[INF-cloud-and-iac]].

<!-- section:quality -->
## Data quality and reconciliation

Revenue MIS-M5 must equal the Billing figure for the month (tolerance 0); case totals equal the sum of regional aggregates; month snapshot frozen with hash. A failed check blocks the board pack.

<!-- section:access -->
## Access and privacy

`platform.mis.view` for management; tenant-level rows visible to account managers for their tenants. No personal data. MIS exports logged.

<!-- section:questions -->
## Open questions

- [ ] Exchange-rate source and date convention for converted totals (finance)
- [ ] Financial years for TAPL and the US entity
- [ ] Is MIS-M9 cost per case useful or misleading for pricing (HKIAC CMP-style bespoke work skews it)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Internal MIS is a Nomology-only, cross-tenant view; it never runs as a tenant user. It reads `rpt_mis.*` aggregates through `rpt_platform_reader` ([[MT-cross-tenant-reporting-via-a]]), which has no access to tenant-grain personal columns.

<!-- check:residency -->
### Residency and cross-region figures

Aggregates only, at tenant × month grain, with small-count suppression; no personal data crosses regions. Store location is open (see [[RPT-report-infrastructure]]).

<!-- check:definitions -->
### Metric semantics

Revenue and receivables are taken from Billing as reported, never recomputed; conversions use one stated rate source and month-end date; months are frozen after close and restatements are versioned.

<!-- check:quality -->
### Data quality and reconciliation

Revenue equals Billing (tolerance 0), case totals equal the sum of regional aggregates, snapshot hashed; failure blocks the pack.

<!-- end -->
