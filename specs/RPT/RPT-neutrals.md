---
id: "RPT-neutrals"
title: "Neutrals"
parent: "RPT-platform-stats"
order: 2
type: "feature"
template: "report"
status: "draft"
owner: null
indicative: false
summary: "Neutral workload, appointment and award timeliness, pending vendor bills and unpaid neutral-fee invoices; individual-level views restricted"
links: []
rev: 2
syncHash: "ab825381e6f18a83"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.1.2 Neutrals

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Neutral workload, appointment and award timeliness, pending vendor bills and unpaid neutral-fee invoices; individual-level views restricted

<!-- section:audience -->
## Audience and questions

| Persona | Frequency | Questions |
|---|---|---|
| Registrar / appointments committee (arbitral institution tenant) | monthly | Q1 How many active cases does each empanelled neutral hold? Q2 How long do neutrals take from appointment to award or to each procedural milestone? |
| ODR institution case manager (SEBI ODR tenant) | weekly | Q3 Which neutrals have matters close to the rule-set award deadline? |
| Tenant finance | weekly | Q4 Which neutral vendor bills are pending approval or payment, and for how long? Q5 Which neutral-fee invoices to parties are unpaid (deposits not yet collected)? |
| Neutral (own view only) | on demand | Q6 What is my pending work and my payment status? |

<!-- section:metrics -->
## Metric definitions

Owner of sources: Neutrals domain team; billing figures: Billing team. Table names are proposals pending [[DOM-neutrals-schema]].

| ID | Metric | Formula | Grain | Inclusions / exclusions | Source |
|---|---|---|---|---|---|
| NEU-M1 | Active appointments | count of `neutral_appointments` with status `accepted` on cases not terminal | neutral × day | excludes declined, challenged-and-removed | `neutral_appointments`, `cases` |
| NEU-M2 | Acceptance time | median of `accepted_at − invited_at` (hours) | neutral × period | invitations without response by period end shown separately as "pending" | `neutral_appointments` |
| NEU-M3 | Appointment to award | median / p90 of `award_issued_at − accepted_at` in calendar days | neutral × case type × period | only cases with award in period; settled or withdrawn excluded and counted separately | `case_stage_events` |
| NEU-M4 | Matters near award deadline | open matters where award deadline (from rule set) − today ≤ N days (N configurable, default 7) | neutral × day | only rule sets with an award deadline | rule-set deadline from [[PKG-calendars-and-deadline]] |
| NEU-M5 | Conflict declarations pending | disclosures submitted and not reviewed | tenant × day | | `conflict_declarations` |
| NEU-M6 | Pending vendor bills | count and amount of `vendor_bills` with `payee_type = neutral`, status `submitted` or `approved_unpaid` | tenant × currency × age bucket | rejected bills excluded | `vendor_bills` |
| NEU-M7 | Unpaid neutral-fee invoices | outstanding on invoices with `kind = neutral_fee` or deposit requests | tenant × currency × age bucket | as CASE-M9 | `invoices`, `payments` |

<!-- section:dimensions -->
## Dimensions and filters

Neutral (restricted, see access), panel / empanelment list, case type, rule set, seat, currency, period, organisation unit. Default: tenant aggregate, last 12 months.

<!-- section:layout -->
## Layout and views

Aggregate view (tiles and table by panel and case type); individual neutral table only for roles with `reports.neutral_individual`; neutral self-view in the neutral workspace ([[APP-neutral-workspace]]) shows only the neutral's own rows.

<!-- section:freshness -->
## Freshness and delivery

Nightly for timeliness metrics; 15 minutes for NEU-M4 and NEU-M6. Monthly scheduled summary to the registrar.

<!-- section:lineage -->
## Data sources and lineage

`neutral_appointments`, `conflict_declarations` ([[DOM-neutrals-schema]]), `case_stage_events`, `vendor_bills` and `invoices` ([[DOM-invoices-and-vendor-bills-schema]]) → `rpt.fct_neutral_appointment`, `rpt.fct_vendor_bill`.

<!-- section:quality -->
## Data quality and reconciliation

Appointment rows reference an existing neutral profile in the same tenant; `accepted_at ≥ invited_at`; vendor bill totals reconcile to the accounting sync ledger ([[INT-accounting-sync]]) per currency.

<!-- section:access -->
## Access and privacy

Individual-level performance is personal data about neutrals and can affect their appointments. Proposal: aggregate views for `reports.view`; individual rows only with `reports.neutral_individual` (registrar / appointments committee); neutral sees self only. No ranking or scoring of neutrals in the first release. Requires a privacy impact review before release (open question).

<!-- section:questions -->
## Open questions

- [ ] Does any tenant want individual neutral timeliness used in appointment decisions? If yes, needs privacy and fairness review and a notice to neutrals
- [ ] Are neutral fees invoiced to parties by the tenant or by Nomology for any tenant (affects which billing entity's ledger is the source)
- [ ] Default N days for NEU-M4

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Tenant users query `rpt.*` as `rpt_tenant_reader` with `app.tenant_id` set per transaction through the same Prisma extension as the app ([[MT-prisma-client-extension-wraps]]); every table behind this report carries `tenant_id` with forced RLS [R1], so isolation does not depend on a WHERE clause. With no tenant set the query returns zero rows (tested). Nomology staff use the separate platform view under `rpt_platform_reader` ([[MT-cross-tenant-reporting-via-a]]). Export and email jobs carry `tenantId` in the BullMQ job payload and re-set the tenant before querying; cache keys are prefixed `rpt:{tenantId}:` ([[PKG-caching]]). The cross-tenant suite in [[TST-multi-tenant-isolation-tests]] logs in as tenant A and asserts no tenant B row in any metric, drill-down or export.

<!-- check:residency -->
### Residency and cross-region figures

Computed, stored, emailed and exported in the tenant's home region ([[MT-data-residency-2]]) from the regional reporting store in [[RPT-report-infrastructure]]; scheduled emails are sent through the regional messaging provider ([[INT-messaging-providers]]). The platform view across tenants reads per-region aggregates at tenant × day grain with no personal data; nothing tenant-grain is copied to another region.

<!-- check:definitions -->
### Metric semantics

Formulas are fixed per metric with clear exclusions (settled / withdrawn cases separated from award timeliness). A neutral empanelled with two tenants appears as two independent profiles; no metric joins them, so tenant figures never reflect another tenant's appointments.

<!-- check:quality -->
### Data quality and reconciliation

Appointment rows must reference a neutral profile in the same tenant, `accepted_at >= invited_at`, and vendor bill totals must reconcile per currency to the accounting sync ledger. A failed test marks the affected views stale and holds the monthly email.

<!-- check:security -->
### Access, privacy and export

Individual-level metrics are gated by a separate permission, neutrals see only themselves, no ranking in release 1, and a privacy impact review is required before release. Exports logged to [[PKG-audit-trail]].

<!-- check:performance -->
### Performance and cost

Queries run on the regional reporting store, never the primary; tiles read pre-aggregated `rpt.agg_*` tables refreshed by dbt; exports run as BullMQ `rpt-export` jobs with a per-tenant concurrency of 1 and a row cap (proposed 100k rows), so a large export cannot slow other tenants.

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
  }
]
```

<!-- end -->
