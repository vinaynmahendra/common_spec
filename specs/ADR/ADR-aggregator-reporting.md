---
id: "ADR-aggregator-reporting"
title: "Aggregator reporting"
parent: "ADR"
order: 8
type: "decision"
template: "adr"
status: "approved"
owner: null
indicative: false
summary: "Extensible, configuration-driven; indicative list: NSE, MSME (next)"
links: []
rev: 2
syncHash: "c5ce473ad838254d"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 19.8 Aggregator reporting

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Extensible, configuration-driven; indicative list: NSE, MSME (next)

<!-- section:context -->
## Context and problem

**Question:** how does the platform produce reports for aggregators, the bodies that route matters to a tenant and report onward to a regulator or ministry (indicatively NSE for SEBI ODR matters, MSME next), when each aggregator has its own format, schedule and delivery channel and these change over time?

Affected parts: [[RPT-aggregators]], [[RPT-configurable-report-templates]], [[RPT-example]], [[ADR-reporting-formats-for-msme-and]], [[INT-aggregator-intake-api]], [[RPT-report-infrastructure]], [[PKG-rules-and-decision-engine]].

Assumption: the exact NSE field list and MSME format are not yet captured; they must be taken from the current official formats ([[RPT-example]], [[ADR-reporting-formats-for-msme-and]]). This record decides the mechanism, not the formats.

<!-- section:drivers -->
## Decision drivers

- **D1 Add an aggregator or a format version without a code release.**
- **D2 Correctness and traceability:** every submitted figure can be traced to case records and the template version used.
- **D3 Tenant scope:** a SEBI ODR institution tenant reports only its own matters; aggregate cross-tenant reports use the reporting role ([[MT-cross-tenant-reporting-via-a]]).
- **D4 Schedules and deadlines** differ per aggregator (periodic and event-based).
- **D5 Delivery channels** vary (API, file upload, portal, email) and may need human approval before sending.

<!-- section:decision -->
## Decision

**Extensible, configuration-driven; indicative list: NSE, MSME (next).**

- An **aggregator registry** (platform-level table) holds each aggregator, the tenants linked to it, and the delivery channel.
- **Report templates** are versioned configuration ([[RPT-configurable-report-templates]]): field mapping from canonical case data, validation rules, output format (CSV, XLSX, JSON, XML), and file naming. A template version is fixed when a reporting period starts.
- **Schedules** run as Temporal Schedules in the tenant's region ([[ADR-temporal]]); event-based submissions are triggered by domain events.
- **Generation, validation, approval and delivery** form one workflow: generate from the read model, validate, require tenant approval where the template says so, deliver through a channel connector ([[INT-integration-framework]]), and store the submitted artefact and acknowledgement as evidence.
- Code changes are needed only for a new delivery channel type or a new canonical data field.

<!-- section:consequences -->
## Consequences

**Easier:** new aggregators and format revisions ship as reviewed configuration; evidence of each submission is uniform.

**Harder:**

- The canonical reporting model must cover all fields any aggregator needs; gaps mean a schema change.
- Template authoring becomes a controlled activity with its own review (wrong mapping means a wrong regulatory filing).
- Validation rules from aggregators may be complex enough to need the rules engine rather than simple field checks.
- Testing needs golden datasets per template version.

<!-- section:confirmation -->
## Confirmation

- Template schema validation in CI and in the admin UI; templates cannot be published without a passing golden-dataset test.
- Each submission record links template ID and version, data snapshot hash, approver, delivery receipt.
- Review check: a pull request that adds aggregator-specific `if` branches in reporting code is rejected unless it adds a channel type.

<!-- section:options -->
## Options considered

| Option | Verdict |
|---|---|
| **Configuration-driven templates and registry** | **Chosen**: meets D1 and D2 |
| Hard-coded report per aggregator | Rejected: every format change needs a release |
| Export raw data and let tenants build reports | Rejected: shifts regulatory correctness to tenants and loses traceability |
| External BI tool for regulatory outputs | Rejected for submissions (approval and evidence trail); acceptable for internal MIS ([[RPT-internal-mis]]) |

<!-- section:revisit -->
## When to revisit

- More than a proposed 20 percent of template changes require code changes.
- An aggregator mandates a real-time API integration that does not fit the batch workflow.
- A regulator prescribes its own reporting software or schema validator that must be embedded.

<!-- section:notes -->
## More information

**Open questions**

- [ ] Obtain the current NSE status report format and submission channel for SEBI ODR matters, and the MSME reporting format and source (owners: compliance and the relevant tenant).
- [ ] Who approves a template version before it is used for a real submission: the tenant, Nomology compliance, or both?
- [ ] Does any aggregator require reports across several tenants (platform-level), and on which legal basis?

<!-- checks -->
## Template checks

<!-- check:significance -->
### Significance

Significant because regulatory reporting correctness depends on it and it fixes how a whole family of outputs is built. It covers the mechanism, not the content of any specific report.

<!-- check:compliance -->
### Regulatory, residency and tenancy fit

Residency: generation runs in the tenant's region; submitted artefacts stay in-region. Isolation: tenant-scoped generation through the app role; cross-tenant only through the reporting role. Audit: every submission is logged with template version and approver ([[PKG-audit-trail]]). Formats themselves must be confirmed by compliance; none are assumed here.

<!-- check:consequences -->
### Consequences and costs

Downsides stated: the canonical model must anticipate fields, template authoring needs control, complex validation may need the rules engine, and per-version golden tests are required.

<!-- check:reversibility -->
### Reversibility and revisit triggers

Low risk: if configuration proves too limited for one aggregator, a coded report can be added behind the same registry and workflow, so the evidence and delivery parts are reused.

<!-- check:linked -->
### Linked and lifecycle

Governs [[RPT-aggregators]], [[RPT-configurable-report-templates]], [[RPT-example]], [[ADR-reporting-formats-for-msme-and]]. Related: [[ADR-temporal]]. Status: Approved.

<!-- end -->
