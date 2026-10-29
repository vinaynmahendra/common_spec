---
id: "RPT-documents"
title: "Documents"
parent: "RPT-platform-stats"
order: 4
type: "feature"
template: "report"
status: "draft"
owner: null
indicative: false
summary: "Document and filing counts, storage used against entitlement, documents pending approval or malware scan, and document lifecycle events"
links: []
rev: 2
syncHash: "c9175c173924f6fb"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.1.4 Documents

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Document and filing counts, storage used against entitlement, documents pending approval or malware scan, and document lifecycle events

<!-- section:audience -->
## Audience and questions

| Persona | Frequency | Questions |
|---|---|---|
| Secretariat lead | daily | Q1 Which filings are pending approval, and for how long? Q2 Which uploads are blocked (malware scan failed or pending)? |
| Tenant admin | monthly | Q3 How much storage do we use against our plan? Q4 How many documents and bundles were filed per case type? |
| Nomology operations | weekly | Q3, Q4 across tenants; Q5 Where is OCR / bundling backlog building? |
| Tenant compliance | on demand | Q6 What lifecycle events (version, approval, withdrawal, deletion under retention) happened on a case's documents? |

<!-- section:metrics -->
## Metric definitions

Owner of sources: Documents domain team; storage metering: Billing ([[BIL-plans-entitlements-and-usage]]). Table names are proposals pending [[DOM-documents-schema]].

| ID | Metric | Formula | Grain | Inclusions / exclusions | Source |
|---|---|---|---|---|---|
| DOC-M1 | Documents filed | count of `documents` with first version created in period | tenant × case type × period | excludes drafts never filed; excludes system-generated notices (shown separately) | `documents`, `document_versions` |
| DOC-M2 | Versions created | count of `document_versions` in period | tenant × period | | `document_versions` |
| DOC-M3 | Pending approval | documents with open `document_approvals` request, with age buckets in business hours | tenant × day | | `document_approvals` |
| DOC-M4 | Scan blocked | versions with `scan_status in ('pending','infected','error')` older than 15 min | tenant × now | | `document_versions` ([[PKG-encryption-at-rest-signed-urls]]) |
| DOC-M5 | Storage used (GB) | sum of object sizes of all live versions + bundles + recordings | tenant × day | excludes objects past deletion; counted once per object key | usage meter from [[BIL-plans-entitlements-and-usage]] |
| DOC-M6 | Storage vs entitlement | DOC-M5 ÷ plan storage entitlement | tenant × day | | same |
| DOC-M7 | Bundles issued | eBundles issued and re-issued | tenant × period | | `bundles` ([[DOM-ebundling]]) |
| DOC-M8 | Pipeline backlog | queued OCR / bundling jobs and oldest age | region × pipeline × now | | Temporal visibility, [[WF-long-running-pipelines]] |
| DOC-M9 | Lifecycle events | list of document events per case | document × event | | [[PKG-audit-trail]] |

<!-- section:dimensions -->
## Dimensions and filters

Case type, document type, filing party role (claimant, respondent, tribunal, secretariat), period, organisation unit. DOC-M5 also by storage class.

<!-- section:freshness -->
## Freshness and delivery

DOC-M3, DOC-M4, DOC-M8: 15 minutes. DOC-M5 / M6: daily from the usage meter, so it matches billing. Others nightly.

<!-- section:lineage -->
## Data sources and lineage

`documents`, `document_versions`, `document_approvals`, `bundles` → `rpt.fct_document_version`; storage from the billing usage meter rather than recomputed, so the report and the invoice agree; lifecycle events read from the audit trail export, not recomputed.

<!-- section:quality -->
## Data quality and reconciliation

DOC-M5 reconciles to the usage meter (it is the same number); every version has a content hash; versions without a scan result after 1 hour raise a data-quality warning and an operations alert.

<!-- section:access -->
## Access and privacy

Counts need no personal data. DOC-M9 lists document titles and actors, so it requires case-level access and honours tribunal-only classification ([[SEC-data-classification]]).

<!-- section:questions -->
## Open questions

- [ ] Do recordings and transcripts count toward storage entitlement (pricing decision)
- [ ] Should DOC-M9 be a tenant self-service export, or only on request through support

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

Storage is taken from the billing usage meter rather than recalculated, so the report and invoice always agree; a filed document is counted at its first version, not at upload of a draft.

<!-- check:security -->
### Access, privacy and export

Aggregates carry no personal data; the lifecycle list re-checks case access and document classification; exports audited.

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
