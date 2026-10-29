---
id: "RPT"
title: "Reporting and Analytics (consumption layer)"
parent: null
order: 12
type: "area"
template: "area"
childTemplate: "report"
status: "draft"
owner: null
indicative: true
summary: "Consumption layer for operational reports, MIS, analytics and regulator / aggregator submissions, built on per-region reporting stores with tenant isolation, metric contracts and submission evidence"
links: [{"rel": "decided-by", "to": "ADR-aggregator-reporting"}]
rev: 3
syncHash: "3abd5e83d5d9252e"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12 Reporting and Analytics (consumption layer)

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Consumption layer for operational reports, MIS, analytics and regulator / aggregator submissions, built on per-region reporting stores with tenant isolation, metric contracts and submission evidence

<!-- section:purpose -->
## Purpose and scope

Reporting and Analytics is where platform data is turned into figures people act on: tenant dashboards (case ageing, unpaid invoices, neutral and transcriber performance), Nomology's internal MIS, AI usage and platform health views, and the regulator and aggregator submissions that some tenants owe (for example SEBI ODR matters reported via an MII). It is a **consumption layer**: it reads data that other areas produce and never changes case, billing or workflow state.

**In scope**
- Metric definitions treated as data contracts with producing teams (one definition per metric, reused everywhere)
- Tenant-facing dashboards and exports in the tenant admin console ([[APP-tenant-admin-console]])
- Nomology internal MIS and industry / marketing figures built from aggregated, non-personal data
- Regulator, aggregator and statutory submissions: obligation register, field mapping, maker-checker, evidence ([[RPT-compliance-reports]])
- Configurable report templates for new regulator / aggregator formats ([[RPT-configurable-report-templates]], [[ADR-aggregator-reporting]])
- The reporting runtime: regional reporting stores, transformation jobs, scheduled exports ([[RPT-report-infrastructure]])

**Out of scope** (and where it lives instead)
- Emitting metrics, traces and business events: Observability ([[OBS-foundations]], [[OBS-business-events]])
- Alert thresholds and paging: [[OBS-alerting]], [[PKG-thresholds-and-alert]]
- Finance ledgers, revenue recognition and tax returns: Billing ([[BIL-revenue-reporting-hooks-for]], [[BIL-invoicing-taxes-gst-singapore]])
- The incident process and its legal clocks: [[SEC-security-incident-response-and]] (this area only builds the filing content and keeps evidence)
- Aggregator case intake: [[INT-aggregator-intake-api]] (this area covers the onward reporting)
- Audit trail storage: [[PKG-audit-trail]]

<!-- section:goals -->
## Goals and non-goals

| # | Goal | Measure (proposed target) |
|---|---|---|
| G1 | Every published metric has exactly one definition with formula, grain, source and owner | 100% of metrics on a dashboard resolve to an entry in the metric registry; CI fails otherwise |
| G2 | No tenant ever sees another tenant's rows in any figure, drill-down, export or email | Cross-tenant leak tests in [[TST-multi-tenant-isolation-tests]] cover every report; zero findings |
| G3 | Regulatory and aggregator submissions are complete, accurate and on time | 100% submitted before deadline; control-total reconciliation stored with every submission |
| G4 | Every submitted figure can be reproduced later | Regeneration from the frozen snapshot matches the submitted file byte for byte (hash) |
| G5 | Reports never degrade case operations | Zero reporting queries on regional primaries; dashboard p95 under 3 s at year-3 volume (proposed) |
| G6 | Reporting data stays in the tenant's region | Only aggregated, suppressed, non-personal data leaves a region, and only for approved views |

**Non-goals**
- A general self-service BI tool for tenants (ad-hoc SQL or a full semantic layer exposed to tenant users)
- Real-time (sub-minute) analytics; operational screens show live state, reports may lag by minutes
- Acting as the legal reporter for a tenant: where a tenant (for example an ODR institution) owes a submission, the tenant remains the reporter; the platform prepares and evidences it
- Replacing the accounting system as the book of record for revenue

<!-- section:principles -->
## Principles

1. **Read-only consumer.** Reporting code never writes to operational tables; it reads replicas, CDC streams or business events.
2. **Never from the primary, never as the app role.** Queries run against the regional reporting store under reporting roles ([[MT-cross-tenant-reporting-via-a]]); the operational primary is not queried.
3. **Tenant isolation in the data layer.** Every tenant-grain reporting table carries `tenant_id` with forced RLS, and tenant-facing queries set `app.tenant_id` per transaction exactly as the app does ([[MT-isolation-strategy]], [[MT-prisma-client-extension-wraps]]). A missing tenant setting returns zero rows.
4. **One definition per metric.** Metrics are defined once in the metric registry (dbt model plus contract file) and referenced by ID; charts never re-implement formulas.
5. **Region first.** Reports for a tenant are computed, stored, emailed and exported in that tenant's home region ([[MT-data-residency-2]]). Cross-region views use aggregated, non-personal rows with small-count suppression (proposed threshold: suppress counts below 5).
6. **Minimum personal data.** Dashboards show counts and amounts; names appear only where the user could open the underlying case, and only in drill-down.
7. **Show freshness.** Every view, export and email shows "data as of" in the viewer's time zone; failed quality checks mark the view stale and hold scheduled sends.
8. **Submissions are reproducible.** Every regulator / aggregator submission is built from a frozen snapshot, records template, mapping and release versions, and passes maker-checker before it leaves the platform.
9. **Unconfirmed obligations are labelled.** No submission is built or described as mandatory until legal has confirmed the source clause; until then it is an assumption with an open question.

<!-- section:context -->
## Context and boundaries

```mermaid
flowchart LR
  subgraph Region[Each region: India / Singapore / US]
    OLTP[(Postgres primary\nforced RLS)] -->|logical replication / CDC| RS[(Reporting store\nrpt schemas)]
    OB[Business events\nOBS-business-events] --> RS
    TMP[Temporal visibility\nand workflow events] --> RS
    BIL[Billing ledger] --> RS
    RS --> DASH[Tenant dashboards\n(tenant-admin)/reports]
    RS --> SUB[Submission workflow\nmaker-checker]
    SUB --> RCPT[MII / aggregator /\nregulator channel]
    RS --> EXP[BullMQ export and\nscheduled-email jobs]
  end
  RS -->|aggregated, suppressed,\nnon-personal only| MIS[(Internal MIS store\nlocation to be decided)]
```

| Neighbour | Flows into Reporting | Flows out of Reporting | Contract |
|---|---|---|---|
| Domain modules ([[DOM-cases]], [[DOM-documents]], [[DOM-neutrals]], [[DOM-transcribers]], [[DOM-invoices-and-vendor-bills]]) | Tables via CDC, status events | none | Data contract per source table |
| [[OBS-business-events]] | `case.stage_changed`, `invoice.paid`, etc. | none | Event schema registry |
| [[OBS-performance]], [[OBS-security-events]], [[OBS-ai-usage]] | Metric and event streams | none | Metric names and labels |
| [[PKG-rules-and-decision-engine]] | Stage target tables, versioned | none | Decision table version per period |
| [[INT-aggregator-intake-api]] | Aggregator matter references | Status pulled by aggregator | API contract |
| [[PKG-audit-trail]] | none | Export, approval and submission events | Audit event schema |
| [[PKG-notifications]] | none | Scheduled report emails, deadline alerts | Template IDs |
| [[SEC-security-incident-response-and]] | Incident facts and clock start | Draft breach notification content | Incident record |

<!-- section:decisions -->
## Key decisions

- [[ADR-aggregator-reporting]]: aggregator reporting is configuration-driven; each new format is a versioned template, not new code. Shapes [[RPT-configurable-report-templates]] and every aggregator child.
- [[ADR-tenant-isolation]]: shared database with forced RLS; reporting stores inherit the same model rather than inventing their own filter logic.
- [[ADR-workflow-engine]] and [[ADR-temporal]]: periodic submissions with deadlines, approvals and retries run as Temporal workflows; exports and emails run as BullMQ jobs ([[ADR-queue-technology]]).
- **Open decision (to record as an ADR):** reporting store technology per region: Postgres reporting replica with dbt views versus a columnar store. The recommendation in [[RPT-report-infrastructure]] is Postgres first.
- **Open decision (to record as an ADR):** location and content of the cross-region internal MIS store.

<!-- section:map -->
## Capability map

| Child | Owns |
|---|---|
| [[RPT-platform-stats]] | Tenant and platform operational reports (parent of cases, neutrals, transcribers, documents) |
| [[RPT-cases]] | Case ageing, stage breaches, client-wise volumes, unpaid case invoices |
| [[RPT-neutrals]] | Neutral workload, timeliness, pending vendor bills, unpaid fees |
| [[RPT-transcribers]] | Transcription turnaround, quality scores, pending vendor bills |
| [[RPT-documents]] | Document counts, storage, pending approvals, lifecycle events |
| [[RPT-compliance-reports]] | Register of statutory, regulator and aggregator obligations and the shared submission discipline |
| [[RPT-statutory]] | Nomology's own statutory filings (privacy, AML / sanctions, FEMA) |
| [[RPT-regulatory-and-aggregator]] | Submissions owed by or for tenants to regulators and aggregators, shared submission pipeline |
| [[RPT-configurable-report-templates]] | Requirement that new formats are configuration, not code |
| [[RPT-accessibility-audit-evidence-for]] | Accessibility evidence pack for SEBI-regulated tenants |
| [[RPT-mis-and-miscellaneous]] | Parent of internal MIS and industry / marketing reporting |
| [[RPT-internal-mis]] | Nomology management figures across tenants and regions |
| [[RPT-industry-marketing]] | Figures prepared for industry surveys and publications |
| [[RPT-platform-performance]] | API, UI and pipeline performance against SLOs |
| [[RPT-platform-security]] | Security events and incident reporting for management and tenants |
| [[RPT-platform-ai-usage-analytics]] | AI usage, cost and quality per tenant and platform-wide |
| [[RPT-report-infrastructure]] | Reporting stores, transformation jobs, exports, scheduling |

Gaps noted: no node yet for a **metric registry / semantic layer** as its own package (currently covered inside [[RPT-report-infrastructure]]); no node for **tenant-defined custom reports** (deliberately excluded for now).

<!-- section:phasing -->
## Phasing

| Phase ([[PLAN]]) | What lands | Entry condition for next step |
|---|---|---|
| 3–4 (domain slices) | Business events and CDC-friendly schemas emitted by domains; `tenant_id` and timestamps on every fact source | Data contracts drafted for cases, documents, invoices |
| 5 (commercial) | Unpaid invoice figures reconciled to the billing ledger | Billing ledger is the system of record |
| 7 (insight and compliance) | Reporting store per region, metric registry, tenant dashboards, internal MIS, SEBI ODR submission to the MII if confirmed | Isolation tests pass on reporting roles; first template approved by legal |
| 8 (hardening) | Submission evidence retention, DR for reporting store, accessibility audit of dashboards | Restore drill passed |

Must not be deferred to Phase 7: (a) business events and stage history captured from Phase 3, because history cannot be rebuilt later; (b) the reporting role separation in [[MT-cross-tenant-reporting-via-a]]; (c) if a SEBI ODR institution tenant goes live earlier than Phase 7, its MII submission must ship with it.

<!-- section:risks -->
## Risks and open questions

- [ ] Which submissions are actually owed, by whom (tenant institution, NTPL, TAPL, US entity) and under which clause: register in [[RPT-compliance-reports]] needs legal sign-off (owner: legal / compliance)
- [ ] Current MII format for SEBI ODR status reporting has not been obtained ([[RPT-example]]) (owner: CORD product)
- [ ] MSME aggregator identity and format unknown ([[ADR-reporting-formats-for-msme-and]])
- [ ] Location of the cross-region internal MIS store, and whether any client contract forbids even aggregated data leaving its region (owner: CTO with legal)
- [ ] Reporting store technology ADR (Postgres reporting replica vs columnar)
- [ ] Individual-level performance reporting on neutrals and transcribers needs a privacy and fairness review before release
- Risk: stage history not captured from day one makes ageing and timeliness figures impossible to restate; mitigated by principle 1 events in Phase 3.

<!-- checks -->
## Template checks

<!-- check:ownership -->
### Ownership and governance

Proposed accountable owner: Head of Data / Reporting (until appointed, the CTO). Specialist reviewers: legal / compliance for every regulatory node; security lead for [[RPT-platform-security]] and export controls; platform engineering for [[RPT-report-infrastructure]]; product owners of CORD and TERES for tenant dashboards. Changes to principles go through an ADR under [[FND-governance]]; new regulatory nodes need legal sign-off on the obligation section before any other section is reviewed.

<!-- check:boundaries -->
### Scope and boundaries

The split is: Observability produces signals, Reporting consumes them; Billing owns ledgers, Reporting reads them; Incident response owns legal clocks, Reporting builds filing content and evidence. Each cross-boundary flow is listed with its contract in the context table. Two overlaps to watch: (1) [[OBS-uptime-synthetic-monitoring]] status page versus [[RPT-platform-performance]] (status page is live, the report is periodic and SLO-based); (2) [[BIL-revenue-reporting-hooks-for]] versus [[RPT-internal-mis]] (finance figures come from Billing; MIS shows them but does not recompute revenue).

<!-- check:principles -->
### Principles and enforcement

Enforcement per principle: (2) and (3) by database grants and the isolation test suite in [[TST-multi-tenant-isolation-tests]] run against the reporting store; (4) by a CI check that every chart's metric ID exists in the registry; (5) by IaC region allow-lists and a CI check that cross-region sync jobs only read `mis_*` aggregate models; (7) by the dashboard component refusing to render without an as-of timestamp; (8) by the submission workflow refusing to submit without a checker approval; (9) by review: regulatory nodes stay in draft until the obligation section is signed off.

<!-- check:compliance -->
### Regulatory and control mapping

| Obligation / standard | Control in this area | Evidence node |
|---|---|---|
| Tenant confidentiality (client contracts), DPDP / GDPR / PDPA data minimisation | RLS on reporting store, masking, small-count suppression | [[RPT-report-infrastructure]], each report's access section |
| SEBI ODR framework (obligations sit with ODR institutions and MIIs; exact reporting clauses to be confirmed) | Submission pipeline with maker-checker and evidence | [[RPT-example]], [[RPT-aggregators]] |
| Privacy breach notification (DPDP, GDPR, PDPA, US states) | Filing content and evidence | [[RPT-privacy-and-confidentiality]] |
| SEBI digital accessibility circular (for regulated tenants) | Evidence pack | [[RPT-accessibility-audit-evidence-for]] |
| ISO 27001:2022 / SOC 2 | Access control, logging of exports, retention | [[SEC-isms-controls]], [[PKG-audit-trail]] |
| WCAG 2.2 AA | Accessible dashboards, tables behind charts | Each report node's accessibility check |

<!-- check:regions -->
### Tenancy and residency

Everything that touches tenant-grain data is per region: reporting store, transformation jobs, export and email jobs, submission workflows (on the regional Temporal cluster) and evidence storage. Global pieces are limited to: report template definitions (platform-level, no tenant data, deployed to every region), the metric registry (code), and the internal MIS store fed only with aggregated non-personal rows. Azure-hosted tenants get the same components on Azure in the same region; no pipeline crosses clouds.

<!-- check:quality -->
### Quality targets

Inherited targets (proposed, to confirm): tenant dashboard p95 load under 3 s; reporting data no older than 15 minutes for operational views and 24 hours for MIS; reporting store RPO 24 h (it can be rebuilt from source) and RTO 8 h; submission evidence RPO 0 (stored in versioned object storage with object lock); 100% of submissions with stored reconciliation; WCAG 2.2 AA for dashboards and exported PDFs.

<!-- check:phase -->
### Phasing

See the phasing table. Business events and stage history (Phase 3) and reporting role separation (Phase 1, via [[MT-cross-tenant-reporting-via-a]]) must not be deferred. Any regulator or aggregator submission owed by a tenant that goes live earlier than Phase 7 moves forward with that tenant's go-live.

<!-- end -->
