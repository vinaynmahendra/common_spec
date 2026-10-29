---
id: "RPT-fema-violations"
title: "FEMA reporting"
parent: "RPT-statutory"
order: 3
type: "requirement"
template: "regulatory"
status: "draft"
owner: null
indicative: false
summary: "Scope to be confirmed by finance / legal: NTPL's own FEMA filings (for example overseas direct investment in TAPL, export-of-services realisation). The platform supplies billing extracts; not a per-tenant platform report"
links: []
rev: 3
syncHash: "cbca4a38e9f1a3eb"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.2.1.3 FEMA reporting

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Scope to be confirmed by finance / legal: NTPL's own FEMA filings (for example overseas direct investment in TAPL, export-of-services realisation). The platform supplies billing extracts; not a per-tenant platform report

<!-- section:obligation -->
## Obligation and source

Status: **assumed, finance / chartered accountant to confirm.** The Foreign Exchange Management Act, 1999 and RBI regulations made under it place filing duties on NTPL as an Indian company with a Singapore subsidiary (TAPL) and foreign customers. Candidates (none confirmed here):
- Annual reporting on NTPL's overseas direct investment in TAPL
- Annual return on foreign liabilities and assets, if applicable
- Realisation and repatriation of export-of-services proceeds within the prescribed period, tracked through the authorised dealer bank

These are company filings made by NTPL's finance team, mostly through RBI or bank portals. The platform's role is to provide accurate **billing extracts** for foreign-currency invoices and receipts, not to file.

The node title says "violations"; no violation reporting is known to apply. Proposal: rename to "FEMA reporting support" once finance confirms scope.

<!-- section:applicability -->
## Applicability

NTPL only. Data: invoices issued by NTPL to customers outside India (including inter-company invoices to TAPL or the US entity), payments received, currency, dates. Not per tenant.

<!-- section:recipient -->
## Recipient and channel

NTPL finance controller (internal). External recipients (RBI / AD bank) handled by finance outside the platform.

<!-- section:frequency -->
## Frequency and deadlines

Monthly extract on business day 5 for finance; annual extract aligned to the financial year (April–March).

<!-- section:fields -->
## Field mapping

Billing extract (from [[DOM-invoices-and-vendor-bills-schema]] and the accounting sync):

| Field | Source | Validation |
|---|---|---|
| Invoice number and date | `invoices.number`, `issued_at` | billing entity = NTPL |
| Customer legal name and country | billing account | country ≠ IN |
| Currency and amount | `invoices.currency`, `total` | |
| Amount received, date, bank reference | `payments` | ≤ invoice amount |
| Outstanding and days since invoice | derived | |
| Inter-company flag | billing account type | |

<!-- section:validation -->
## Validation and reconciliation

Extract totals reconcile to the accounting system (Odoo) per currency for the period; every foreign invoice appears once.

<!-- section:questions -->
## Open questions

- [ ] Finance / CA: list the FEMA filings NTPL actually makes, their deadlines and which need platform data
- [ ] Rename the node to reflect that it supports filings rather than reports violations
- [ ] Should this extract live in the accounting system rather than the platform

<!-- checks -->
## Template checks

<!-- check:accuracy -->
### Accuracy and reconciliation

Totals reconcile to the accounting system per currency; the extract is generated from Billing tables, not re-keyed.

<!-- check:segregation -->
### Tenant and entity segregation

Only NTPL billing-entity data is included; runs in the internal compliance workspace in the India region.

<!-- end -->
