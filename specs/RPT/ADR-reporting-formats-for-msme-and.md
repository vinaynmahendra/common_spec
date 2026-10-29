---
id: "ADR-reporting-formats-for-msme-and"
title: "MSME reporting format"
parent: "RPT-aggregators"
order: 2
type: "decision"
template: "regulatory"
status: "draft"
owner: null
indicative: false
summary: "MSME aggregator reporting format: aggregator, legal source and format still to be identified; to be captured as a versioned report template once obtained"
links: []
rev: 3
syncHash: "a1e65f92c8bd8e6f"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.2.2.2.2 MSME reporting format

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> MSME aggregator reporting format: aggregator, legal source and format still to be identified; to be captured as a versioned report template once obtained

<!-- section:obligation -->
## Obligation and source

Status: **unknown.** The aggregator that will route MSME matters to the platform, the body it reports to (for example a ministry or a facilitation council) and the legal or contractual source of the reporting duty have not been identified. Nothing in this node should be read as an existing obligation.

What is known: [[ADR-aggregator-reporting]] lists MSME as the next aggregator and decides that its format will be a configuration-only template ([[RPT-configurable-report-templates]]).

<!-- section:applicability -->
## Applicability

To be confirmed: which tenant (for example a CORD tenant or an institution handling MSME delayed-payment disputes) receives MSME matters, and whether the reporter is the tenant or Nomology under an agreement with the aggregator.

<!-- section:recipient -->
## Recipient and channel

To be confirmed. Registry entry `msme-tbd` with status `planned` in the aggregator registry ([[RPT-aggregators]]).

<!-- section:frequency -->
## Frequency and deadlines

To be confirmed.

<!-- section:fields -->
## Field mapping

Not yet available. Capture steps when the format is obtained:
1. Record source document, version and clause in the obligation register ([[RPT-compliance-reports]]).
2. List every prescribed field, in order, with the recipient's label and code list.
3. Map each field to the mapping catalogue; any field without a catalogue source becomes an engineering ticket to extend the catalogue.
4. Create template `msme-<recipient>-<report>` v1 in draft; build golden files from a sample tenant dataset; legal review; approve.

Fields the catalogue already covers that MSME formats are likely to need (assumption): aggregator matter reference, claimant enterprise name and registration identifier, respondent name, amount claimed, date received, stage, outcome, settlement amount, dates of key events.

<!-- section:validation -->
## Validation and reconciliation

Shared validation in [[RPT-regulatory-and-aggregator#validation]], plus any MSME-specific rules from the format.

<!-- section:questions -->
## Open questions

- [ ] Identify the MSME aggregator and its reporting recipient (CORD product / founders)
- [ ] Obtain the format, version and legal or contractual source
- [ ] Confirm who reports: tenant or Nomology
- [ ] Rename this node (its ID starts with `ADR-` but it uses the regulatory template); propose title "MSME aggregator reporting format" under [[RPT-aggregators]]

<!-- end -->
