---
id: "BIL-revenue-reporting-hooks-for"
title: "Revenue reporting hooks for finance"
parent: "BIL"
order: 4
type: "capability"
template: "billing"
status: "draft"
owner: null
indicative: false
summary: "Ledger posting events, revenue schedule data and finance exports per billing entity, plus MRR / ARR metrics for management reporting"
links: []
rev: 2
syncHash: "8bb6ffdf649e1393"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 10.4 Revenue reporting hooks for finance

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Ledger posting events, revenue schedule data and finance exports per billing entity, plus MRR / ARR metrics for management reporting

<!-- section:purpose -->
## Purpose and scope

Gives finance complete, timely and reconcilable data for each entity (NTPL, TAPL, US entity) without finance staff reading platform databases. It defines:
- the **finance events** emitted by billing and payments,
- the **posting rules** that turn them into journal data for the accounting system ([[INT-accounting-sync]] delivers them),
- the **revenue schedule data** on each invoice line so revenue can be recognised over time under IFRS 15 / Ind AS 115 in the ledger,
- **management metrics** (MRR, ARR, net revenue retention, overage share, unpaid invoices) for [[RPT-internal-mis]].

Revenue recognition itself happens in the ledger. The platform supplies facts, not accounting judgements.

<!-- section:model -->
## Pricing model

Not applicable; this node prices nothing. It classifies each priced line with `revenue_category`: `subscription` (base fee, add-ons), `usage` (metered overage), `services` (transcription hours, implementation), `contract_other` (manual contract lines).

<!-- section:entitlements -->
## Entitlements

Not applicable. Finance users access the outputs through the reporting warehouse with a finance role; they have no access to tenant case data.

<!-- section:metering -->
## Metering events

Consumes billing outbox events, never usage events directly. Event list and payload fields:

| Event | Key fields |
|---|---|
| `billing.invoice.issued` | entity, invoice number, date, currency, functional amounts and FX rate, lines (category, service period, amount, tax per component) |
| `billing.credit_note.issued` / `billing.debit_note.issued` | as above plus original invoice number |
| `billing.payment.received` | gateway, payment ID, amount, fees, invoice allocations |
| `billing.refund.processed` | refund ID, credit note reference, amount |
| `billing.invoice.written_off` | invoice, amount, approver |
| `billing.dispute.opened` / `.closed` | payment, amount, outcome |
| `billing.period.closed` | entity, period, counts and totals of each document type |

Each event has a UUIDv7 `id` used as the idempotency key on the accounting side.

<!-- section:worked -->
## Worked examples

**Annual prepaid subscription (NTPL)**: contract base fee INR 18,00,000 for 1 October 2026 to 30 September 2027, invoiced on 1 October with GST. The line carries `revenue_category=subscription`, `service_period_start=2026-10-01`, `service_period_end=2027-09-30`. Ledger: on issue, debit receivable, credit deferred revenue INR 18,00,000 and credit GST output; monthly, recognise INR 1,50,000 from deferred revenue to revenue (straight-line by month, to be confirmed by finance).

**Monthly usage (Example 1 in [[BIL-plans-entitlements-and-usage#worked]])**: overage lines totalling INR 12,452.00 carry service period 1–31 October 2026 and are recognised in October, the month of use.

**Month-end cut-off**: October closes on 1 November 06:00 IST; a late transcription event arriving on 3 November is billed in November as an October adjustment. Finance may accrue it in October from the `billing.period.closed` totals plus the late-adjustment report, or recognise in November (finance policy).

<!-- section:tax -->
## Tax and billing entity

Tax components are carried per line on every event (CGST, SGST, IGST, Singapore GST, US state tax by jurisdiction), mapped to the entity's tax accounts in the posting rules. No tax is computed here.

<!-- section:lifecycle -->
## Invoice and payment lifecycle

Not applicable beyond emitting events for each state change listed in [[BIL-invoicing-taxes-gst-singapore#lifecycle]] and [[BIL-payment-gateway-integration#lifecycle]].

<!-- section:payments -->
## Payments, payouts and reconciliation

Payment, fee, refund and dispute events carry the information needed for cash postings and bank reconciliation in the ledger (see the posting in [[BIL-payment-gateway-integration#worked]] Example 1).

<!-- section:reporting -->
## Revenue and finance reporting

**Posting rules (per entity; account codes are placeholders for finance)**

| Event | Debit | Credit |
|---|---|---|
| Invoice issued, `subscription` monthly | Trade receivable | Subscription revenue; output tax |
| Invoice issued, `subscription` with service period > 1 month | Trade receivable | Deferred revenue; output tax |
| Invoice issued, `usage` / `services` | Trade receivable | Usage / services revenue; output tax |
| Credit note | Revenue (or deferred revenue); output tax | Trade receivable |
| Payment received | Gateway clearing | Trade receivable |
| Settlement | Bank; gateway fees; input tax on fees | Gateway clearing |
| Refund | Trade receivable (or customer credit) | Gateway clearing / bank |
| Write-off | Bad debt expense | Trade receivable |

**Revenue recognition notes** [R1]: subscriptions are a stand-ready obligation recognised over the service period; metered usage is recognised as used; implementation or bespoke development under institutional contracts (for example a client-specific platform build) is a separate performance obligation assessed by finance and invoiced through the ledger, not this platform. Multi-element contracts need finance to allocate price; the platform records list price and discount per line to support that.

**Management metrics (to [[RPT-internal-mis]])**: MRR = sum of normalised monthly `subscription` amounts of active subscriptions at month end, in each entity's functional currency and in a reporting currency (USD, at month-end rates); ARR = 12 × MRR; overage share = `usage` revenue / total; unpaid invoices by age band (0–30, 31–60, 61–90, 90+ days) per entity.

**Delivery**: events go through the transactional outbox to (1) [[INT-accounting-sync]] and (2) the reporting warehouse ([[RPT-report-infrastructure]]) through the per-region export. Finance sees a period-close report per entity: counts and totals per document type in billing versus accounting.

<!-- section:questions -->
## Open questions

- [ ] Finance to supply the chart of accounts and posting rules per entity (placeholders above).
- [ ] Deferred revenue schedules: generated by the ledger (proposed) or by the platform?
- [ ] Reporting currency and FX source for group MRR / ARR.
- [ ] Month-end cut-off and accrual policy for late usage.
- [ ] Are intercompany charges between NTPL, TAPL and the US entity ever generated from platform data? Proposed: out of scope.

<!-- checks -->
## Template checks

<!-- check:accuracy -->
### Metering accuracy and reconciliation

Each period's `billing.period.closed` event carries counts and totals per document type; the accounting sync and the warehouse both reconcile to it, so a missing or duplicated posting shows up as a difference on the period-close report.

<!-- check:money -->
### Money, currency and rounding

Events carry amounts in minor units with currency, the functional-currency amount and the FX rate, source and date already fixed on the invoice, so the ledger never re-converts or re-rounds. MRR in a reporting currency uses month-end rates recorded with the metric.

<!-- check:tenancy -->
### Tenant and client attribution

Events are tenant-scoped in the outbox and carry the tenant's billing account ID; warehouse exports run under the reporting role per region. The accounting system receives the billing account (customer), not case data or party data.

<!-- check:audit -->
### Audit trail and adjustments

Every event is immutable and kept with the source document. Finance can export all events for a period and entity for auditors; manual adjustments made in the ledger are outside this node and must reference a platform document number when they relate to one.

<!-- check:finance -->
### Ledger and revenue recognition

Posting rules per event and entity are tabled above; the sync to the ledger is idempotent on event ID and reconciled per period by counts and totals (`billing.period.closed` versus Odoo). Subscriptions with service periods longer than a month post to deferred revenue; usage is recognised in the month of use; bespoke development is a separate performance obligation handled in the ledger [R1]. Cut-off is the period-close time per entity; post-close corrections are next-period adjustment lines or credit notes, never edits. Intercompany billing is proposed out of scope.

<!-- citations -->
## Citations

```json
[
  {
    "body": "IFRS Foundation",
    "excerpt": "Five-step model: identify the contract, identify performance obligations, determine and allocate the transaction price, recognise revenue when obligations are satisfied.",
    "id": "R1",
    "ident": "IFRS 15",
    "kind": "standard",
    "title": "IFRS 15 Revenue from Contracts with Customers",
    "url": "https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/"
  }
]
```

<!-- end -->
