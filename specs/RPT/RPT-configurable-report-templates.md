---
id: "RPT-configurable-report-templates"
title: "Configurable report templates"
parent: "RPT-regulatory-and-aggregator"
order: 3
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "New regulator and aggregator report formats are added as versioned, schema-validated report templates (field list, mapping, validation rules, file layout), not as code changes"
links: []
rev: 3
syncHash: "8589e6c159faf657"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.2.2.3 Configurable report templates

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> New regulator and aggregator report formats are added as versioned, schema-validated report templates (field list, mapping, validation rules, file layout), not as code changes

<!-- section:statement -->
## Statement

When a new regulator or aggregator report format, or a new version of an existing format, is approved for use, the reporting service shall generate, validate and submit that report from a versioned report template definition (fields, source mappings drawn from the approved mapping catalogue, validation rules, file layout and schedule) without a code change or deployment.

<!-- section:rationale -->
## Rationale and source

[[ADR-aggregator-reporting]] decided that aggregator reporting is configuration-driven so that NSE (for SEBI ODR matters) and later aggregators such as MSME ([[ADR-reporting-formats-for-msme-and]]) can be added quickly. MIIs and regulators change formats by circular or notice, often with short lead times; a release cycle per format change risks late submissions. Templates are platform-level data (no `tenant_id`, per [[MT-platform-level-tables]]); tenants subscribe to a template version.

Boundary: a template may only reference **mapping functions and source fields already in the mapping catalogue** (for example `case.registered_at`, `case.outcome_code`, `fn.to_ist_date`). A field that needs new source data or a new transformation is a code change to the catalogue, reviewed once, and then reusable by every template. This keeps templates safe and testable.

Sketch of the template shape (stored in `report_template_version.definition`, JSON, validated by a Zod schema):

```json
{
  "templateKey": "nse-sebi-odr-status",
  "version": 3,
  "status": "approved",
  "effectiveFrom": "2027-04-01",
  "population": { "source": "rpt.fct_case", "filter": { "ruleSetTag": "SEBI-ODR" } },
  "schedule": { "kind": "monthly", "cutoffLocal": "23:59", "tz": "Asia/Kolkata", "dueBusinessDays": 7 },
  "fields": [
    { "col": "Dispute ID", "source": "case.aggregator_ref", "required": true },
    { "col": "Date of reference", "source": "case.registered_at", "fn": "fn.to_ist_date", "format": "DD-MM-YYYY" }
  ],
  "rules": [ { "id": "V1", "expr": "award_date >= appointment_date", "severity": "error" } ],
  "layout": { "type": "xlsx", "sheet": "Annexure", "fileName": "{institutionCode}_{yyyymm}.xlsx" }
}
```
(field names above are placeholders, not the NSE format).

<!-- section:acceptance -->
## Acceptance criteria

- **Given** an approved template version `nse-sebi-odr-status` v3 that adds one field mapped to an existing catalogue source, **when** a tenant admin with `regreports.configure` subscribes the tenant to v3 effective next period, **then** the next scheduled run produces the file with the new column, with no deployment.
- **Given** a draft template that references a source field not in the mapping catalogue, **when** it is submitted for approval, **then** validation rejects it naming the unknown field.
- **Given** a template version used by any completed submission, **when** someone tries to edit it, **then** the edit is refused and a new version must be created.
- **Given** two tenants subscribed to different versions of the same template, **when** both runs execute for the same period, **then** each output follows its own version and records the version number in `report_run`.
- **Given** a template whose population filter would match cases of more than one tenant, **when** it runs, **then** RLS limits the population to the running tenant (cross-tenant test asserts zero foreign rows).

<!-- section:verification -->
## Verification method

Test: unit tests for the Zod template schema and every catalogue function; integration test in `packages/reporting/test/templates` running golden templates against a seeded Postgres with forced RLS and asserting output byte-for-byte against golden files; cross-tenant test in [[TST-multi-tenant-isolation-tests]]. Demonstration to legal / compliance on the first real template before Phase 7 sign-off.

<!-- section:priority -->
## Priority

Must, Phase 7 ([[PLAN]]); earlier if a SEBI ODR tenant goes live before Phase 7.

<!-- section:notes -->
## Notes

Open questions:
- [ ] Who may approve a template version: Nomology compliance only, or also the tenant's compliance officer for tenant-specific variants?
- [ ] Do we allow tenant-specific template variants at all, or only platform templates per recipient?
- [ ] Expression language for validation rules: reuse the rules engine chosen in [[PKG-rules-and-decision-engine]] (decision pending in [[WF-separation-of-concerns-temporal]]) rather than a second evaluator
- [ ] Which output layouts are needed in the first release (CSV, XLSX, JSON for API submission, PDF)?

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Without it every format change from an MII or aggregator needs a release, which conflicts with [[ADR-aggregator-reporting]] and risks missed deadlines when a format changes at short notice.

<!-- check:unambiguous -->
### Unambiguous

"Without a code change" is bounded: new templates may only use sources and functions already in the mapping catalogue; extending the catalogue is code. Actor (reporting service), trigger (approved template version) and outputs (generate, validate, submit) are named.

<!-- check:feasible -->
### Feasible

Feasible on the stack: templates are JSON in a platform-level table, validated with Zod, executed by the submission workflow on the regional Temporal cluster against the reporting store under RLS. The main risk is template expressiveness creeping toward a programming language; the catalogue boundary contains it.

<!-- check:verifiable -->
### Verifiable

Golden-file integration tests per template, schema validation tests, an immutability test for used versions and a cross-tenant test; the negative cases are listed in the acceptance criteria.

<!-- check:consistent -->
### Consistent

Consistent with [[ADR-aggregator-reporting]], with templates being platform-level tables ([[MT-platform-level-tables]]) and with tenant isolation via forced RLS ([[MT-rls-enabled-and-forced-on]]). Validation rules should use the same evaluator as [[PKG-rules-and-decision-engine]], not a second one.

<!-- check:traced -->
### Traced

Source: [[ADR-aggregator-reporting]] and parent [[RPT-regulatory-and-aggregator]]. Forward trace: template table and executor in [[RPT-report-infrastructure]]; first users [[RPT-example]] and [[ADR-reporting-formats-for-msme-and]].

<!-- end -->
