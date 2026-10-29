---
id: "RPT-regulatory-and-aggregator"
title: "Regulatory and Aggregator Reporting"
parent: "RPT-compliance-reports"
order: 2
type: "feature"
template: "regulatory"
status: "draft"
owner: null
indicative: false
summary: "Shared pipeline for submissions owed by or for tenants to regulators and aggregators: frozen snapshots, template-driven files, validation and reconciliation, maker-checker, submission, acknowledgement and evidence"
links: []
rev: 2
syncHash: "5aad32690a114c67"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.2.2 Regulatory and Aggregator Reporting

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Shared pipeline for submissions owed by or for tenants to regulators and aggregators: frozen snapshots, template-driven files, validation and reconciliation, maker-checker, submission, acknowledgement and evidence

<!-- section:obligation -->
## Obligation and source

Parent node. Obligations are specified in the children: direct regulator returns ([[RPT-regulators]], none confirmed yet), aggregator reporting ([[RPT-aggregators]] with [[RPT-example]] for SEBI ODR matters via an MII and [[ADR-reporting-formats-for-msme-and]] for MSME), and accessibility evidence for SEBI-regulated tenants ([[RPT-accessibility-audit-evidence-for]]). This node defines the **shared pipeline and controls** every child uses, following the accuracy, completeness, timeliness and adaptability principles of BCBS 239 as a discipline [R1] (BCBS 239 is a banking standard and is not a legal obligation for us).

<!-- section:applicability -->
## Applicability

Submissions owed by a tenant (the ODR institution or arbitral institution is the reporter) or owed under a tenant's contract with an aggregator. The platform prepares, validates, evidences and, where the channel allows, transmits on the tenant's behalf; the tenant's compliance officer approves. Runs in the tenant's region under the tenant's context.

<!-- section:recipient -->
## Recipient and channel

Recipients and channels are configured in the aggregator / regulator registry ([[RPT-aggregators]]): `portal_upload` (platform produces the file, the tenant's officer uploads and records the reference), `api` (platform calls the recipient's API with credentials held in the regional secrets manager), `sftp`, `email`. Credentials for recipient portals belong to the tenant; the platform stores them only for `api` / `sftp` channels and only with the tenant's written authorisation.

<!-- section:frequency -->
## Frequency and deadlines

From the template's `schedule`: periodic (`monthly`, `quarterly`, `annual`) with cut-off time and time zone, due date in business days per [[PKG-calendars-and-deadline]]; or event-driven (`on_event`, for example `case.award_issued`) with a due period. A Temporal Schedule per tenant × template starts each run at cut-off + 1 hour (proposed) so late-arriving same-day data is included.

<!-- section:fields -->
## Field mapping

Field mappings are per child template. Every generated file carries this envelope in the evidence record (not necessarily in the file): `submissionId`, `tenantId`, `reportingEntity`, `recipientKey`, `templateKey`, `templateVersion`, `mappingCatalogueVersion`, `appRelease`, `periodStart`, `periodEnd`, `snapshotId`, `rowCount`, `fileSha256`, `preparedBy`, `approvedBy`, `submittedAt`, `ackRef`.

<!-- section:format -->
## Format and template

Layout per template: CSV, XLSX, JSON or XML; file naming pattern from the template; UTF-8; dates in the format the recipient prescribes.

<!-- section:validation -->
## Validation and reconciliation

Run in this order; any `error` blocks approval, `warning` needs a reason from the checker:
1. **Population control total**: row count equals an independent count (for example matters received from the aggregator through [[INT-aggregator-intake-api]] for the period, less exclusions), with every exclusion listed with reason.
2. **Field validity**: required fields, enums mapped to the recipient's code list, date formats, numeric precision.
3. **Cross-field rules** from the template (for example award date not before appointment date).
4. **Reconciliation** to related reports: outcome counts against [[RPT-cases]] for the same period and tenant (tolerance 0); amounts against Billing where relevant.
5. **Period integrity**: records changed after the previous submission are flagged as possible corrections to that submission.

<!-- section:workflow -->
## Preparation, approval and submission

Temporal workflow `RegulatorySubmissionWorkflow`, ID `{tenantId}-regsub-{templateKey}-{periodKey}` on task queue `rpt-submissions` in the tenant's region (naming per [[WF-separation-of-concerns-temporal]]).

```
Schedule fires → createSnapshot (Activity: point-in-time query into report_run_snapshot)
 → generateFile (Activity: template version + mapping catalogue)
 → runValidations → status PREPARED
 → wait Update `submitForApproval` (maker, needs regreports.prepare)
 → wait Update `approve` | `reject` (checker, needs regreports.approve, approver ≠ maker, enforced in the Update validator)
 → submit (Activity per channel) or wait Signal `manualSubmissionRecorded` (portal reference + uploaded receipt)
 → wait Signal `acknowledged` | `rejectedByRecipient` (or poll API)
 → archiveEvidence → COMPLETED
```
Deadline timers raise alerts at T-5 business days, T-2 and T-4 hours to the tenant compliance officer and a backup, and to Nomology support. Tables (tenant-owned, RLS): `report_run`, `report_run_snapshot`, `submission`, `submission_approval`, `submission_ack`, `submission_correction`. Screens: `/(tenant-admin)/compliance/submissions` and `/(tenant-admin)/compliance/submissions/[submissionId]`.

<!-- section:evidence -->
## Evidence and retention

Per submission, in `rpt-evidence-<region>` (object lock) plus rows above: frozen snapshot (or its hash and a reproducible query with snapshot timestamp), generated file and hash, validation and reconciliation results, approvals with timestamps, submission receipt or portal reference, acknowledgement, recipient queries, corrections. Retention: the longest of the applicable rule, the tenant contract and a proposed platform minimum of 8 years (to be confirmed).

<!-- section:changes -->
## Change management

Recipient format changes are detected by the compliance owner's watch of recipient circulars and notices and by recipient rejections; each change becomes a new template version ([[RPT-configurable-report-templates]]) with an effective date, tested against golden files and approved by legal before any tenant switches.

<!-- section:risk -->
## Non-compliance risk

Late, missing or wrong submissions can lead to recipient action against the tenant (for example under MII oversight of ODR institutions) and contractual liability for Nomology. Escalation: tenant compliance officer → Nomology customer success → Nomology compliance → CTO.

<!-- section:questions -->
## Open questions

- [ ] Retention minimum for submission evidence
- [ ] Should Nomology ever hold tenant credentials for recipient portals, or only for API / SFTP channels
- [ ] Who at Nomology is second-line reviewer for tenant submissions, if anyone (the tenant owns the obligation)

<!-- checks -->
## Template checks

<!-- check:completeness -->
### Completeness

The population is reconciled to an independent control total (aggregator intake records for the period, or cases tagged with the relevant rule set) and every exclusion is listed with a reason [R1]. Records created or corrected after a period's submission are flagged for correction. Nil returns are produced automatically when the template says the recipient expects them.

<!-- check:accuracy -->
### Accuracy and reconciliation

Outcome counts reconcile to [[RPT-cases]] for the same tenant and period with zero tolerance; enum mappings to recipient code lists are part of the template and tested; time conversion uses the template's time zone with tests around midnight cut-offs; results are stored with the submission.

<!-- check:lineage -->
### Traceability

Each submission records template version, mapping catalogue version, app release and snapshot ID; the snapshot can regenerate the file byte for byte (hash compared). For any cell, the evidence view lists contributing record IDs. Manual adjustments are not allowed in the file; corrections go to source data or a documented resubmission.

<!-- check:segregation -->
### Tenant and entity segregation

The workflow runs in the tenant's region with the tenant set on every query (`rpt_submission` role, forced RLS [R2]); the population filter cannot widen beyond the tenant. The reporting entity in the file comes from the tenant's registry entry, not free text.

<!-- check:timeliness -->
### Timeliness

Schedules start runs after cut-off with business-day due dates from the tenant calendar; alerts at T-5 business days, T-2 and T-4 hours to the officer and a backup; portal outages are recorded with attempts as evidence; on-time rate per tenant is shown in the compliance calendar.

<!-- check:security -->
### Access, approval and transmission

Maker-checker enforced in the Update validator; recipient credentials for API / SFTP held in the regional secrets manager with tenant authorisation; files encrypted at rest, transmitted over TLS or SFTP; all actions audited.

<!-- check:resubmission -->
### Corrections and resubmissions

Corrections create a new `submission` linked to the original with `submission_correction` recording reason and differences; the original stays unchanged. A source-data fix that touches a past period lists every affected submission.

<!-- check:retention -->
### Evidence retention

Full evidence set kept in object-locked storage in the tenant's region; retention is the longest of rule, contract and platform minimum. Snapshot personal data is limited to what the format requires; erasure requests against data in a submitted file are answered with the legal-retention exception recorded in [[SEC-data-principal-rights-requests]].

<!-- citations -->
## Citations

```json
[
  {
    "body": "Basel Committee on Banking Supervision",
    "excerpt": "Principles on accuracy and integrity, completeness, timeliness and adaptability of risk data aggregation, and on accuracy, comprehensiveness and clarity of reports. Used here as a discipline, not as a legal obligation.",
    "id": "R1",
    "ident": "BCBS 239",
    "kind": "standard",
    "title": "Principles for effective risk data aggregation and risk reporting",
    "url": "https://www.bis.org/publ/bcbs239.pdf",
    "version": "January 2013"
  },
  {
    "excerpt": "Table owners normally bypass row security; ALTER TABLE ... FORCE ROW LEVEL SECURITY makes policies apply to the owner as well.",
    "id": "R2",
    "kind": "vendor",
    "title": "PostgreSQL documentation: Row Security Policies",
    "url": "https://www.postgresql.org/docs/current/ddl-rowsecurity.html",
    "vendor": "PostgreSQL Global Development Group"
  }
]
```

<!-- end -->
