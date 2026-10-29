---
id: "RPT-cases"
title: "Cases"
parent: "RPT-platform-stats"
order: 1
type: "feature"
template: "report"
status: "draft"
owner: null
indicative: false
summary: "Case ageing, stage-target breaches, intake and closure volumes, client-wise breakdowns and unpaid case-fee invoices, per tenant and platform-wide"
links: []
rev: 2
syncHash: "eeefab9269d5854d"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.1.1 Cases

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Case ageing, stage-target breaches, intake and closure volumes, client-wise breakdowns and unpaid case-fee invoices, per tenant and platform-wide

<!-- section:audience -->
## Audience and questions

| Persona | Frequency | Questions |
|---|---|---|
| Registrar / secretariat lead (arbitral institution tenant) | daily | Q1 How many cases are open and how old are they? Q2 Which cases are over their stage target? |
| ODR institution case manager (SEBI ODR tenant) | daily | Q2, plus Q3 Which matters are at risk of breaching the conciliation or arbitration timelines set by the tenant's rule set? |
| Tenant admin / management | weekly | Q4 How many cases came in and closed this period, by client and case type? Q5 How long does a case take to close? |
| Tenant finance | weekly / monthly | Q6 Which case-fee invoices are unpaid and for how long? |
| Nomology account manager | weekly | Q1, Q4 across tenants (counts only) |

"Client" means: for a tenant, the **referring organisation** of the case (for example the market participant / broker in SEBI ODR matters, or the claimant's organisation); for Nomology's platform view, the **tenant**.

<!-- section:metrics -->
## Metric definitions

Proposed metric registry entries (owner of every source: Cases domain team unless stated). Names of tables are proposals pending [[DOM-cases-schema]].

| ID | Metric | Formula | Grain | Inclusions / exclusions | Source |
|---|---|---|---|---|---|
| CASE-M1 | Open cases | count of cases where `status` not in terminal set (`closed`, `withdrawn`, `dismissed`, `settled_closed`) at snapshot time | tenant × day | excludes test cases; includes `on_hold` | `rpt.fct_case_daily` from `cases`, `case_stage_events` |
| CASE-M2 | Case age (days) | snapshot date − `registered_at` date (tenant tz), calendar days | case × day | starts at registration, not draft creation; drafts never counted | `rpt.fct_case_daily` |
| CASE-M3 | Ageing bucket | CASE-M2 into 0–30, 31–60, 61–90, 91–180, 181–365, >365 | case × day | open cases only | derived |
| CASE-M4 | Stage age (days) | snapshot − entry time of current stage; business or calendar days as the stage target says | case × day | time `on_hold` counted unless rule set says paused | `case_stage_events` |
| CASE-M5 | Cases over stage target | count where CASE-M4 > target from decision table `stage-target-days` (version in force on the snapshot date) | tenant × stage × day | stages without a target excluded | `rpt.fct_case_daily` + decision table versions from [[PKG-rules-and-decision-engine]] |
| CASE-M6 | New cases | count with `registered_at` in period | tenant × period | excludes test; includes later-withdrawn | `cases` |
| CASE-M7 | Closed cases | count entering a terminal status in period | tenant × outcome × period | reopened then re-closed counts once, at last close | `case_stage_events` |
| CASE-M8 | Time to close (median, p90) | median / p90 of (`closed_at` − `registered_at`) for cases closed in period | tenant × case type × period | withdrawn cases shown separately | `rpt.fct_case` |
| CASE-M9 | Unpaid case invoices (count, amount) | invoices with `kind = case_fee`, status `issued` or `part_paid`, outstanding = total − allocated payments − credit notes | tenant × currency × day | void and fully credited excluded; amounts per currency, never summed across currencies | `invoices`, `payments`, `credit_notes` (Billing team) |
| CASE-M10 | Invoice days overdue | snapshot − `due_date`, buckets 0, 1–30, 31–60, 61–90, >90 | invoice × day | not-yet-due shown as bucket "not due" | same |

Assumption: the timelines that apply to SEBI ODR matters are encoded as stage targets in the tenant's rule set; this report shows breaches of those configured targets and does not itself interpret the circular.

<!-- section:dimensions -->
## Dimensions and filters

Tenant (platform view), organisation unit, client (referring organisation), case type, rule set, product, current stage, assigned case manager, claim value band (configurable bands per currency), currency (invoices), period. Default: current tenant, open cases, all case types, ageing view.

<!-- section:layout -->
## Layout and views

1. **Overview**: tiles CASE-M1, CASE-M5, CASE-M6 / M7 for the period, CASE-M9 total per currency; each with "data as of".
2. **Ageing**: stacked bar of CASE-M3 by case type, with the same data as a table below; click a bucket → case list (filtered `/(secretariat)/cases?ageing=…`).
3. **Stage breaches**: table of stages × count over target, sortable; drill to cases.
4. **Flow**: monthly new vs closed line and CASE-M8 median / p90.
5. **Client-wise**: table by client: open, new, closed, median time to close, unpaid amount.
6. **Unpaid invoices**: CASE-M10 buckets by currency; drill to invoice list (finance role only).

<!-- section:freshness -->
## Freshness and delivery

Overview and breach tiles: 15-minute refresh. Daily snapshots (CASE-M1 to M5) built at 00:30 tenant time. Scheduled email: weekly Monday 08:00 tenant time with headline counts and a link; no case names in email. CSV export of drill-down lists is async.

<!-- section:lineage -->
## Data sources and lineage

`cases`, `case_stage_events` (written by the case state machine in [[WF-entity-state-machines]]) → logical replication → `rpt_stg.case`, `rpt_stg.case_stage_event` → `rpt.fct_case`, `rpt.fct_case_daily` (dbt). Stage targets: decision table versions exported from [[PKG-rules-and-decision-engine]] into `rpt.dim_stage_target` with valid-from / valid-to. Invoices from [[DOM-invoices-and-vendor-bills-schema]]. Business event `case.stage_changed` from [[OBS-business-events]] is used to cross-check stage history, not as primary source. Data contract (ODCS format [R2]) per source table, owned by the Cases and Billing teams.

<!-- section:quality -->
## Data quality and reconciliation

Before publish (dbt tests; failure marks views stale and holds emails):
- exactly one current stage per open case; no stage event before `registered_at`
- every case has a valid `tenant_id` and case type
- count of open cases equals the operational count from a nightly check query on the replica (tolerance 0)
- unpaid totals per currency reconcile to the billing ledger outstanding balance (tolerance 0.01 per currency)
- source freshness: `case_stage_events` no older than 30 min [R3]

<!-- section:access -->
## Access and privacy

`reports.view` for tiles and aggregates; drill-down lists show case reference and parties only if the user can open the case (same policy check as the case screen); unpaid invoice drill-down needs `billing.view`. Platform view shows counts and amounts per tenant, no party names. Exports logged to [[PKG-audit-trail]] (`report.exported`, filters, row count).

<!-- section:performance -->
## Performance and cost

Year-3 proposal: up to 500k cases and 10M stage events per region. Daily snapshot table partitioned by month; tiles served from `rpt.agg_case_daily`; dashboard p95 under 3 s target.

<!-- section:questions -->
## Open questions

- [ ] Confirm the terminal status list and whether `on_hold` pauses stage age per rule set
- [ ] Should claim value bands be tenant-configurable, and in which currencies
- [ ] Does a SEBI ODR institution tenant want breach tracking against the circular timelines specifically; if so, legal must confirm the timelines and the rule set must encode them
- [ ] Is "client" for CORD tenants the referring organisation or the claimant

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Tenant users query `rpt.*` as `rpt_tenant_reader` with `app.tenant_id` set per transaction through the same Prisma extension as the app ([[MT-prisma-client-extension-wraps]]); every table behind this report carries `tenant_id` with forced RLS [R1], so isolation does not depend on a WHERE clause. With no tenant set the query returns zero rows (tested). Nomology staff use the separate platform view under `rpt_platform_reader` ([[MT-cross-tenant-reporting-via-a]]). Export and email jobs carry `tenantId` in the BullMQ job payload and re-set the tenant before querying; cache keys are prefixed `rpt:{tenantId}:` ([[PKG-caching]]). The cross-tenant suite in [[TST-multi-tenant-isolation-tests]] logs in as tenant A and asserts no tenant B row in any metric, drill-down or export.

<!-- check:definitions -->
### Metric semantics

Each metric has a formula, grain, exclusions and source; shared conventions (tenant time zone, calendar vs business days via [[PKG-calendars-and-deadline]], per-currency amounts, snapshot at 00:00 tenant time) come from [[RPT-platform-stats]]. Stage targets use the decision-table version valid on the snapshot date, so history is not restated when a target changes. Late corrections to stage events restate past daily snapshots on the next full rebuild; the view shows a "restated" marker for affected days.

<!-- check:lineage -->
### Lineage and data contracts

Source tables, dbt models and owners are listed in the lineage section; data contracts per source table in ODCS [R2]. A new status in the case state machine fails a dbt `accepted_values` test until the report owner classifies it as open or terminal, so it cannot silently change CASE-M1.

<!-- check:quality -->
### Data quality and reconciliation

Not-null and uniqueness tests, one-current-stage test, operational count reconciliation (tolerance 0) and billing ledger reconciliation (0.01 per currency), with freshness thresholds [R3]. Failures mark views stale and hold the weekly email; the data owner is alerted.

<!-- check:security -->
### Access, privacy and export

Aggregates need no personal data; drill-down re-checks case access and ethical walls; invoice drill-down needs `billing.view`; emails carry counts only; exports are audited. Data erased or past retention leaves reporting tables on the next run because models are rebuilt from replicated sources that the retention jobs in [[PKG-data-retention-legal-hold-and]] already cleaned.

<!-- check:accessibility -->
### Accessible presentation

Every chart has the same data in a table below it; breach status uses text and an icon, not colour alone [R4]; colours from [[PKG-data-visualisation-palette]]; filters and drill-downs keyboard-operable; CSV is the accessible alternative for large lists; Indian digit grouping applied for INR in Indian locales.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Table owners normally bypass row security; ALTER TABLE ... FORCE ROW LEVEL SECURITY makes policies apply to the owner as well.",
    "id": "R1",
    "kind": "vendor",
    "title": "PostgreSQL documentation: Row Security Policies",
    "url": "https://www.postgresql.org/docs/current/ddl-rowsecurity.html",
    "vendor": "PostgreSQL Global Development Group"
  },
  {
    "body": "Bitol (Linux Foundation AI & Data)",
    "excerpt": "A YAML standard for describing a dataset's schema, semantics, quality rules, service levels and ownership.",
    "id": "R2",
    "ident": "Open Data Contract Standard",
    "kind": "standard",
    "title": "Open Data Contract Standard (ODCS)",
    "url": "https://github.com/bitol-io/open-data-contract-standard"
  },
  {
    "excerpt": "Freshness blocks define warn_after and error_after thresholds against a loaded_at field for each source.",
    "id": "R3",
    "kind": "vendor",
    "title": "dbt documentation: source freshness",
    "url": "https://docs.getdbt.com/reference/resource-configs/freshness",
    "vendor": "dbt Labs"
  },
  {
    "body": "W3C",
    "excerpt": "Success criteria 1.4.1 Use of Color, 1.4.3 Contrast (Minimum) 4.5:1 and 1.4.11 Non-text Contrast 3:1.",
    "id": "R4",
    "ident": "WCAG 2.2",
    "kind": "standard",
    "title": "Web Content Accessibility Guidelines (WCAG) 2.2",
    "url": "https://www.w3.org/TR/WCAG22/",
    "version": "W3C Recommendation"
  }
]
```

<!-- end -->
