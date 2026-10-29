---
id: "INT-accounting-sync"
title: "Accounting sync"
parent: "INT-common-integrations"
order: 5
type: "feature"
template: "integration"
status: "draft"
owner: null
indicative: false
summary: "Invoice, payment and payout sync to the accounting system (e.g. Odoo) per billing entity"
links: []
rev: 2
syncHash: "d2e7e62ab009c958"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 9.2.5 Accounting sync

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Invoice, payment and payout sync to the accounting system (e.g. Odoo) per billing entity

<!-- section:purpose -->
## Purpose and use cases

Posts billing and payout facts to the accounting system (Odoo) for each billing entity (NTPL, TAPL, US entity) so finance closes the books from the ledger without re-keying. Use cases:
1. Customer invoices, credit notes and debit notes from [[BIL-invoicing-taxes-gst-singapore]].
2. Customer payments, refunds and gateway fees from [[BIL-payment-gateway-integration]].
3. Vendor bills and payouts for neutrals and transcribers where Nomology pays them ([[DOM-invoices-and-vendor-bills]]).
4. Daily reconciliation of counts and totals between platform and ledger.

Tenants' own accounting (an institution's ledger for case fees) is out of scope in Phase 5; a later connector could post to a tenant's accounting system through the same framework.

<!-- section:party -->
## External party and ownership

Odoo, owned by finance. Topology to decide: one Odoo database with one company per entity (multi-company) or separate databases. Hosting to decide (affects residency of billing contact data). Environments: Odoo staging database per entity linked to platform staging; production linked to production. Technical owner: billing team.

<!-- section:flows -->
## Data flows

```
billing outbox event (invoice.issued, credit_note.issued, payment.received, refund.processed, ...)
  └─▶ BullMQ queue `accounting:{region}` job (jobId = eventId)
        ├─ resolve entity → Odoo company + journal + account mapping (accounting_mapping table)
        ├─ upsert partner (customer) by our billing_account_id stored in Odoo `ref`
        ├─ search existing move by `ref` = our document number; if found, skip (idempotent)
        ├─ create move (customer invoice / credit note / payment / vendor bill) with lines and taxes
        ├─ post move; store odoo_move_id in accounting_sync_record
        └─ on failure: retry; after 10 attempts → dead-letter + finance task
Daily 06:00 entity local time: reconciliation job compares counts and totals per document type per day
```
Direction is one-way (platform → Odoo) except payment status for bank transfers matched in Odoo, which flows back by a scheduled pull (`odoo.reconciledPayments` sync, every 30 minutes) and is applied as `billing.payment.received` with source `bank_reconciliation`.

<!-- section:mapping -->
## Data mapping

| Platform | Odoo (model.field) | Notes |
|---|---|---|
| billing entity | `res.company` | Mapping table, platform-level |
| billing account ID, legal name, address, tax ID | `res.partner` (`ref`, `name`, address, `vat`) | Business contact only; no party or case data |
| invoice number, date, due date, currency | `account.move` (`name`/`ref`, `invoice_date`, `invoice_date_due`, `currency_id`) | Our number is authoritative; Odoo sequence not used for these journals (to configure) |
| invoice lines (description, quantity, unit price, revenue category, service period) | `account.move.line` (`name`, `quantity`, `price_unit`, `account_id`, analytic tags; deferral dates if used) | Account from category mapping |
| tax components (CGST, SGST, IGST, SG GST, US state) | `account.tax` by mapping | Amounts computed by us; Odoo taxes configured to match and differences flagged |
| IRN, QR payload (NTPL) | custom fields on move | |
| payment (gateway, reference, amount, fee) | `account.payment` + fee move | Reconciled to invoice |
| credit note | `account.move` type refund, reversed entry reference | |
| vendor bill (neutral fee), TDS withheld | `account.move` in_invoice, withholding tax line | Payee bank details are not sent |

<!-- section:auth -->
## Authentication and secrets

Odoo external API with a dedicated integration user per company holding only accounting rights needed (create and post moves, partners, payments), using an API key stored in the regional secrets manager. Network: private connectivity or IP allow-list from each region's egress to the Odoo host.

<!-- section:errors -->
## Errors, retries and idempotency

- Idempotency: `accounting_sync_record(entity_id, source_type, source_id)` unique; before create, search Odoo by `ref`; posting is skipped if a move exists.
- Retry transient errors (timeouts, 5xx, lock errors) with backoff; validation errors (missing account mapping, closed period in Odoo) go to a finance task with the error text.
- Ordering: payments wait for their invoice's sync record (job delay and retry), so a payment is never posted before its invoice.
- Tax mismatch: if Odoo's computed tax differs from ours by more than 0 minor units, the move is kept in draft and flagged.

<!-- section:limits -->
## Rate limits and SLAs

Expected volume is small (hundreds to low thousands of documents per month per entity). Concurrency 2 per Odoo company to avoid lock contention.

<!-- section:residency -->
## Data transfer and compliance

Only billing data about the tenant as a customer (business name, address, tax ID, billing contact email) leaves the region to Odoo. If Odoo is hosted in India while TAPL or US entity data is posted, that is a transfer of business contact data; record the basis, or host per entity.

<!-- section:testing -->
## Sandbox and testing

Odoo staging per entity with the same chart of accounts; contract tests on the move payloads; month-end rehearsal in staging: generate a month of invoices, payments and credit notes and check that the reconciliation report shows zero difference.

<!-- section:questions -->
## Open questions

- [ ] Odoo topology (multi-company versus separate databases) and hosting location.
- [ ] Should Odoo or the platform own numbering for these journals? Proposed: platform numbers, Odoo stores them.
- [ ] Deferred revenue schedules in Odoo: available in the edition we use, or handled by journal entries we generate?
- [ ] Bank statement import and matching: in Odoo (proposed).

<!-- checks -->
## Template checks

<!-- check:security -->
### Security

Dedicated least-privilege integration user per company, API key in the regional secrets manager, private connectivity or IP allow-list, no payee bank details or case data sent.

<!-- check:resilience -->
### Failure handling and degradation

Queue-based, retried, dead-lettered with a finance task; accounting outages never block invoicing or payment collection (alert at 4 hours lag).

<!-- check:consistency -->
### Consistency and reconciliation

The platform is authoritative for invoice content, numbers and tax amounts; Odoo is authoritative for the general ledger and bank matching. Idempotency by unique sync record and `ref` search; payments wait for their invoice. Daily reconciliation compares counts and totals per entity, document type and day, and any mismatch creates a finance task with the differing documents. Currencies and amounts are passed exactly (minor units converted to Odoo decimals at the currency's precision) and tax differences are flagged, never silently accepted.

<!-- check:audit -->
### Audit and evidence

Each posted move stores the Odoo ID against our document and the payload hash; the reconciliation report per period is the audit evidence for completeness.

<!-- end -->
