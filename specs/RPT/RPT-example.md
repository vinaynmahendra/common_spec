---
id: "RPT-example"
title: "SEBI ODR status report to NSE"
parent: "RPT-aggregators"
order: 1
type: "requirement"
template: "regulatory"
status: "draft"
owner: null
indicative: false
summary: "Status submission for SEBI ODR matters handled by an ODR institution tenant and reported to NSE as MII; field list provisional until the current NSE format is obtained"
links: []
rev: 3
syncHash: "93193462e75b248d"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.2.2.2.1 SEBI ODR status report to NSE

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Status submission for SEBI ODR matters handled by an ODR institution tenant and reported to NSE as MII; field list provisional until the current NSE format is obtained

<!-- section:obligation -->
## Obligation and source

Source: SEBI circular "Online Resolution of Disputes in the Indian Securities Market" (31 July 2023) [R1] and the Master Circular (December 2023) [R2], under which MIIs operate the common ODR portal and empanel ODR institutions. The existing outline refers to an "Annexure X" status submission.

**Not yet confirmed:** the exact clause that requires ODR institutions to report status to the MII, the reporting frequency, and the current format prescribed by NSE. Legal / CORD product must obtain from NSE the current format (and its version or circular number) and the clause reference before this node can be Approved. Until then, the field mapping below is a **provisional working list**, and treating it as the prescribed format would be a compliance defect.

Also to confirm: whether status is reported through a periodic file at all, or by updating each matter on the MIIs' common ODR portal (in which case this node becomes a per-matter status sync via [[INT-aggregator-intake-api]] plus a periodic reconciliation).

<!-- section:applicability -->
## Applicability

Reporter: the SEBI ODR institution tenant (the ODR institution), not NTPL. Scope: matters allotted to the tenant through the common ODR portal, identified by rule set tag `SEBI-ODR` and aggregator `nse-mii` (or the MII that allotted the matter). From: the tenant's go-live on the platform.

<!-- section:recipient -->
## Recipient and channel

NSE as MII. Channel: to be confirmed (portal upload or email are the likely options; API only if NSE offers one). Credentials: held by the tenant's compliance officer; the platform does not store them for portal upload.

<!-- section:frequency -->
## Frequency and deadlines

Assumption: monthly, for matters active during the month, cut-off 23:59 IST on the last calendar day, due within a number of days to be taken from NSE's requirement. Event-driven updates (for example on award) may also be required. All times in IST (`Asia/Kolkata`); holidays from the India calendar in [[PKG-calendars-and-deadline]].

<!-- section:fields -->
## Field mapping

**Provisional working list (assumption).** Every row is to be replaced or confirmed against the NSE format; column names are placeholders.

| # | Placeholder field | Platform source | Transformation | Validation |
|---|---|---|---|---|
| 1 | ODR portal dispute reference | `cases.aggregator_ref` | as received | required, unique in file |
| 2 | ODR institution name / code | tenant registry `aggregator_codes['nse-mii']` | | required |
| 3 | Market participant name / code | `case_parties` with role `respondent_market_participant` | registered name | required |
| 4 | Complainant category | party type (investor, market participant) | map to NSE code list | enum |
| 5 | Date matter received | intake record `received_at` | IST date | required |
| 6 | Conciliator appointed on | stage event `conciliator_appointed` | IST date | ≥ #5 |
| 7 | Conciliation outcome and date | stage events | map outcome to NSE code list | required if concluded |
| 8 | Arbitration initiated on | stage event `arbitration_commenced` | IST date | ≥ conciliation end |
| 9 | Arbitrator(s) appointed on | `neutral_appointments.accepted_at` | IST date | ≥ #8 |
| 10 | Mode of hearing | hearing records | online / other | |
| 11 | Award date | stage event `award_issued` | IST date | ≥ #9 |
| 12 | Claim amount (INR) | `cases.claim_amount` | 2 decimals | ≥ 0, currency INR |
| 13 | Amount awarded / settled (INR) | award / settlement record | 2 decimals | ≤ claim unless reason |
| 14 | Current status | current stage | map to NSE status codes | enum |
| 15 | Reason for delay | `case_delay_reasons` | free text from list | required if beyond the rule-set timeline |
| 16 | Fees collected | invoices `kind = case_fee` | | per rule set |

Rule-set timelines for flagging delay are configured in the tenant's rule set and must be confirmed by legal against the circular.

<!-- section:format -->
## Format and template

Assumption: XLSX or CSV, one row per matter, file name `{institutionCode}_{yyyymm}_ODR_status.xlsx`. Replace with NSE's prescribed layout and attach a sample file when obtained.

<!-- section:validation -->
## Validation and reconciliation

- Control total: rows = matters allotted via the MII to the tenant and active in the period (intake records), less listed exclusions (for example transferred out)
- Every row has fields 1–5 and 14; date order rules 5 ≤ 6 ≤ 8 ≤ 9 ≤ 11
- Outcome counts reconcile to [[RPT-cases]] for rule set `SEBI-ODR`, same period (tolerance 0)
- Matters with a delay flag have a reason
- Shared checks in [[RPT-regulatory-and-aggregator#validation]]

<!-- section:workflow -->
## Preparation, approval and submission

Shared pipeline [[RPT-regulatory-and-aggregator#workflow]] with workflow ID `{tenantId}-regsub-nse-sebi-odr-status-{yyyymm}`. Maker: tenant case manager lead; checker: tenant compliance officer; submission by the compliance officer through NSE's channel, with the portal reference recorded.

<!-- section:evidence -->
## Evidence and retention

As in [[RPT-regulatory-and-aggregator#evidence]], India region, object lock.

<!-- section:changes -->
## Change management

NSE format or SEBI circular changes become a new template version of `nse-sebi-odr-status` with an effective month; compliance owner watches NSE investor-grievance / ODR notices and SEBI circulars.

<!-- section:risk -->
## Non-compliance risk

Late or wrong reporting may affect the tenant's standing with the MII as an empanelled ODR institution (consequences to be confirmed from the MII's terms). Escalation: tenant compliance officer → Nomology customer success → Nomology compliance.

<!-- section:questions -->
## Open questions

- [ ] Obtain NSE's current format, version and the clause requiring it; replace the provisional field list
- [ ] Is reporting by periodic file, by per-matter updates on the common ODR portal, or both
- [ ] Frequency and due date
- [ ] Do the other MIIs (BSE, CDSL, NSDL) require the same report for matters they allot
- [ ] Rule-set timelines to flag delay (legal to confirm against the circular)

<!-- checks -->
## Template checks

<!-- check:completeness -->
### Completeness

Control total is the set of intake records from the MII for the tenant, active in the period, less listed exclusions; reopened or transferred matters follow the template's rule (to be set once the NSE format is known).

<!-- check:accuracy -->
### Accuracy and reconciliation

Outcome counts reconcile to [[RPT-cases]] for rule set `SEBI-ODR`; dates are converted from UTC to IST at the matter level with tests around midnight; enum mappings to NSE code lists live in the template version.

<!-- check:segregation -->
### Tenant and entity segregation

Runs in the India region under the ODR institution tenant's context; the institution code comes from the tenant registry.

<!-- check:timeliness -->
### Timeliness

Run starts at 01:00 IST on the first day after cut-off; alerts T-5 business days, T-2 and T-4 hours before the NSE due date (to be confirmed) [R1].

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
