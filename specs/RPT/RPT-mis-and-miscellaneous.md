---
id: "RPT-mis-and-miscellaneous"
title: "MIS and miscellaneous"
parent: "RPT"
order: 3
type: "capability"
template: "report"
status: "draft"
owner: null
indicative: false
summary: "Parent for Nomology's internal MIS and externally published industry figures; both built only from aggregated, suppressed, non-personal data"
links: []
rev: 2
syncHash: "c946c266377c91ee"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.3 MIS and miscellaneous

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Parent for Nomology's internal MIS and externally published industry figures; both built only from aggregated, suppressed, non-personal data

<!-- section:audience -->
## Audience and questions

Parent node. Children:
- [[RPT-internal-mis]]: Nomology management (founders, CTO, COO, CCO, account managers): monthly and quarterly business and operations figures across all tenants and regions.
- [[RPT-industry-marketing]]: figures Nomology publishes or submits externally (industry surveys, our own ODR publications), always with tenant permission where a tenant could be identified.

Shared rule: both consume only `rpt_mis.*` aggregate models (no `tenant_id`-free personal data, small counts suppressed), never tenant-grain tables directly.

<!-- section:metrics -->
## Metric definitions

Defined in the children. Shared definitions both must reuse: active tenant (at least one non-test case registered or a user sign-in in the last 30 days), case volume (CASE-M6 / CASE-M7 from [[RPT-cases]]), and region (tenant home region from the tenant directory in [[MT-data-residency-2]]).

<!-- section:dimensions -->
## Dimensions and filters

Region, entity (NTPL, TAPL, US entity), product (CORD, TERES), tenant segment (arbitral institution, SEBI ODR institution, CORD tenant, court / government), period.

<!-- section:freshness -->
## Freshness and delivery

Monthly close plus a weekly flash; delivered as dashboard in `/(platform-admin)/mis` and a PDF pack.

<!-- section:access -->
## Access and privacy

Nomology staff with `platform.mis.view`. Tenant-identifiable figures leave Nomology only through [[RPT-industry-marketing]] with written tenant consent.

<!-- section:questions -->
## Open questions

- [ ] Where the MIS store lives (see [[RPT-report-infrastructure]]) and whether aggregated rows from India-region tenants may be read from Singapore or US
- [ ] Small-count suppression threshold (proposed: 5)

<!-- checks -->
## Template checks

<!-- check:residency -->
### Residency and cross-region figures

Only `rpt_mis` aggregate models leave a region; they carry no personal data, are at tenant × month grain or coarser, and suppress counts below the threshold. Whether any client contract restricts even this is an open question; until confirmed, the MIS store reads from each region rather than copying (federated query from platform admin), which keeps data in place.

<!-- end -->
