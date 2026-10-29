---
id: "APP-bulk-admin-operations"
title: "Bulk administration, import and export"
parent: "APP-tenant-admin-console"
order: 3
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Bulk import, update and export of users, roles, groups, units and settings through the same admin operations, with mandatory dry run, thresholds for step-up and approval, resumable jobs, per-row results and rollback"
links: []
rev: 1
syncHash: "564c4d05a6aed196"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 2.1.2.5.3 Bulk administration, import and export

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Bulk import, update and export of users, roles, groups, units and settings through the same admin operations, with mandatory dry run, thresholds for step-up and approval, resumable jobs, per-row results and rollback

<!-- section:statement -->
## Statement

When an authorised administrator submits a bulk file or a bulk selection, the platform shall validate every row against the same admin operation used for a single change, show a dry-run result, and, after confirmation, apply the rows as a resumable background job that records each row's outcome, so that the result is identical to making each change individually.

<!-- section:rationale -->
## Rationale and source

Institutions administer at volume: a SEBI ODR institution onboards hundreds of conciliators and case managers at once and may need to update thousands of memberships after an MII change; arbitral institutions refresh panels annually; court programmes load staff lists from government HR systems. Without a governed bulk path, admins either click through thousands of screens or ask Nomology to run scripts, which bypasses permission checks and the tenant's audit trail.

Source: CTO request for full administration requirements; the existing console offered only a 500-row CSV invite with no dry-run ([[APP-tenant-admin-console]] before this overhaul). Patterns borrowed from: the SCIM bulk operation model, where each operation in a bulk request has its own result [R1]; dry-run and per-row results in enterprise admin consoles. Security source: CSV and spreadsheet formula injection [R2]. File format: RFC 4180 CSV [R3].

**Detailed requirements** (one prefix, `BULK-FR`):

| ID | Requirement |
|---|---|
| BULK-FR-1 | Supported bulk ops in v1: `users.invite`, `users.update`, `users.suspend`, `users.end`, `roles.assign`, `roles.unassign`, `groups.members`, `units.create`, `settings.set` (unit or case-type scope), `invitations.resend`. Each maps to one registry op ([[APP-administration-model#design]]). |
| BULK-FR-2 | Inputs: CSV (RFC 4180, UTF-8, header row required) or XLSX first sheet, up to `platform.bulk.max_rows_per_file` rows (default 10,000; platform ceiling 100,000) and 20 MB; or a console selection ("all users matching this filter"); or the API (`POST /admin/v1/bulk-jobs`, [[INT-tenant-admin-api]]). |
| BULK-FR-3 | Downloadable templates per op with column names generated from the op's Zod input schema, an example row and a description sheet; columns are matched by header name, case-insensitively. |
| BULK-FR-4 | Upload is malware-scanned and parsed server-side only; formulas are never evaluated; cells beginning with `=`, `+`, `-`, `@`, tab or carriage return are treated as text. |
| BULK-FR-5 | Dry run is mandatory for files: every row is validated with the op's schema, permission at the row's scope, cross-row rules (duplicates in file, last owner, seat limit across the whole file) and current state; the result lists per row `would_create`, `would_update`, `no_change`, `error` with field-level messages. No change is made during dry run. |
| BULK-FR-6 | Confirmation shows counts per outcome and requires step-up when rows exceed `access.bulk.step_up_threshold_rows` (default 50) and maker-checker approval when rows exceed `access.bulk.approval_threshold_rows` (default 500) or any row grants an administrative role. |
| BULK-FR-7 | Apply runs as BullMQ job on queue `admin-bulk` in the tenant's region (Temporal workflow `{tenantId}-admin-bulk-{jobId}` for jobs over 5,000 rows), at most `platform.bulk.max_concurrent_jobs_per_tenant` jobs per tenant (default 2), rows applied in file order, each row in its own transaction through `runAdminOp` with `via=bulk` and idempotency key `jobId:rowNumber`. |
| BULK-FR-8 | Error mode per job: `skip_row` (default) continues and reports, `stop` halts at the first failing row; state checked at apply time, so a row valid at dry run but invalid at apply is reported as `error` with the reason. |
| BULK-FR-9 | Progress (rows done, succeeded, failed, ETA) is visible in `/admin/bulk/{jobId}` and through the API; the job continues if the admin leaves. Cancel stops after the current row; completed rows stay applied. |
| BULK-FR-10 | Results file (CSV) has the original row plus `outcome`, `object_id`, `error_code`, `error_message`; retained `platform.bulk.result_retention_days` (default 30) in regional object storage, then deleted. Uploaded source files are deleted after the same period. |
| BULK-FR-11 | One change set per job ([[APP-admin-change-history]]) linking all row audit events; rollback of a job creates an inverse job for succeeded reversible rows. |
| BULK-FR-12 | `users.invite` respects `notify` (send invitations now or later) and per-tenant invitation send rate `platform.bulk.invitation_send_per_minute` (default 300) so messaging limits and DLT templates in India are respected ([[PKG-notification-copy]]). |
| BULK-FR-13 | Bulk export: users, groups, role assignments, units, settings (effective, with source scope), invitations and change history can be exported as CSV or JSONL by admins holding the matching read permission plus `bulk.job:create`; exports are jobs, require step-up above 1,000 rows, are audited (`admin.bulk.export_requested`) and neutralise formula-leading cells. |
| BULK-FR-14 | Unit admins may run bulk jobs only for rows inside their unit subtree; rows outside are reported as `error: out_of_scope` without revealing whether the target exists. |
| BULK-FR-15 | The admin copilot may prepare a bulk file or selection and run the dry run, but cannot confirm the apply step ([[APP-admin-copilot]]). |

<!-- section:acceptance -->
## Acceptance criteria

- **Happy path**: Given a `user_admin` uploads a 300-row `users.invite` CSV with 3 invalid emails, when the dry run completes, then it shows 297 `would_create` and 3 `error` with the field and message, and no invitation has been sent; when the admin confirms with step-up, then 297 invitations are created, the results file lists 3 errors, and one change set links 297 `admin.user.invited` events with `via=bulk`.
- **Approval threshold**: Given a file of 800 `roles.assign` rows, when the admin confirms, then the job waits in `awaiting_approval` until a second admin who is not the submitter approves; the job does not start if approval does not arrive within 7 days.
- **Escalation attempt (negative)**: Given a `user_admin` uploads `roles.assign` rows granting `tenant_admin`, when the dry run runs, then each such row is `error: role-escalation-forbidden` and the job cannot be confirmed with those rows.
- **Formula injection (negative)**: Given a cell `=HYPERLINK("http://evil.example","x")` in the name column, when the file is processed and later exported, then the value is stored as literal text and the export prefixes it so spreadsheet software does not execute it.
- **Resume**: Given a job of 20,000 rows when a worker restarts at row 12,000, then the job resumes and rows 1–12,000 are not applied twice (row idempotency keys).
- **Unit scope (negative)**: Given a `unit_admin` for "SEBI ODR desk" includes a row for a user in "Head office", then that row is `error: out_of_scope` and the message does not say whether the user exists.
- **State change between dry run and apply**: Given a row's user was ended by another admin after the dry run, when apply reaches that row, then it reports `error: user-not-active` and continues (`skip_row`).

<!-- section:verification -->
## Verification method

Test: integration tests per bulk op in `packages/admin-ops/test/bulk/*.test.ts` against Postgres with RLS through PgBouncer; property test that applying a file row by row through the single-op API and through bulk produces identical database state and audit events (except `via`); BullMQ worker crash test; Playwright journey for upload → dry run → confirm → results → rollback; security test cases for formula injection and oversized files in [[TST-security-testing]]; load test of 100,000-row job on staging within 1 hour.

<!-- section:priority -->
## Priority

Must, Phase 2 (tenant admin console general availability), for `users.invite`, `users.update`, `roles.assign`, `roles.unassign`, `groups.members` and exports; Should, Phase 3, for `settings.set` and `units.create`.

<!-- section:questions -->
## Open questions

- [ ] Is 10,000 rows per file the right default for SEBI ODR institutions, or should their blueprint default be 50,000? (product, CORD)
- [ ] Should bulk party creation (outside admin, for case intake) reuse this pipeline or stay in [[INT-aggregator-intake-api]]? Proposed: stay separate; share the parser and validation library. (platform core)
- [ ] Approval threshold defaults (50 step-up, 500 maker-checker): confirm with institution tenants. (security)
- [ ] XLSX support in v1 or CSV only? (product)

<!-- section:notes -->
## Notes

Settings used: `platform.bulk.max_rows_per_file`, `platform.bulk.max_file_mb`, `platform.bulk.max_concurrent_jobs_per_tenant`, `platform.bulk.result_retention_days`, `platform.bulk.invitation_send_per_minute`, `access.bulk.step_up_threshold_rows` and `access.bulk.approval_threshold_rows`; the `platform.bulk.*` keys are catalogued in [[PKG-settings-platform-operations]] and the `access.bulk.*` keys in [[PKG-settings-access-control]]. Console routes: `/admin/bulk`, `/admin/bulk/new`, `/admin/bulk/{jobId}` ([[APP-tenant-admin-console#routing]]). Audit events: `admin.bulk.job_started`, `admin.bulk.job_approved`, `admin.bulk.job_completed`, `admin.bulk.job_cancelled`, `admin.bulk.export_requested`, plus one event per row from the underlying op.

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Yes. Without it, high-volume tenants (SEBI ODR institutions, court programmes) depend on Nomology-run scripts that bypass tenant permission checks and audit, which conflicts with ADM-R5 (no standing staff access) and the single-operation principle.

<!-- check:unambiguous -->
### Unambiguous

Each behaviour is a numbered BULK-FR item with defaults given as setting keys and numbers; outcomes are a closed set (`would_create`, `would_update`, `no_change`, `error`).

<!-- check:singular -->
### Singular

The statement is one capability (governed bulk application of admin ops); the BULK-FR table details it. Bulk export (BULK-FR-13) could become its own requirement if it grows.

<!-- check:complete -->
### Complete and scoped

Covers who (permission plus scope), inputs and limits, validation, dry run, confirmation controls, execution, errors, resume, results retention, audit, rollback, unit scope, copilot limits and the negative cases.

<!-- check:feasible -->
### Feasible

Uses existing BullMQ queues and Temporal per region, the admin op registry and object storage; the throughput target (50 rows per second per job) is well inside Postgres and audit write capacity ([[PKG-audit-trail#nfr]]).

<!-- check:verifiable -->
### Verifiable

Acceptance scenarios include happy path and six negative or failure cases; the equivalence property test proves BULK-FR-7.

<!-- check:consistent -->
### Consistent

Uses shared-model role keys, `admin.*` audit naming, the change set model of [[APP-admin-change-history]] and the API in [[INT-tenant-admin-api]].

<!-- check:traced -->
### Traced

Source: CTO administration request and the earlier 500-row invite in the tenant console; forward to `packages/admin-ops/bulk`, queue `admin-bulk`, and tests listed under Verification.

<!-- citations -->
## Citations

```json
[
  {
    "body": "IETF",
    "id": "R1",
    "ident": "RFC 7644",
    "kind": "standard",
    "title": "System for Cross-domain Identity Management: Protocol (section 3.7, Bulk Operations)",
    "url": "https://www.rfc-editor.org/rfc/rfc7644"
  },
  {
    "body": "OWASP",
    "id": "R2",
    "ident": "CSV Injection",
    "kind": "standard",
    "title": "OWASP: CSV Injection",
    "url": "https://owasp.org/www-community/attacks/CSV_Injection"
  },
  {
    "body": "IETF",
    "id": "R3",
    "ident": "RFC 4180",
    "kind": "standard",
    "title": "Common Format and MIME Type for Comma-Separated Values (CSV) Files",
    "url": "https://www.rfc-editor.org/rfc/rfc4180"
  }
]
```

<!-- end -->
