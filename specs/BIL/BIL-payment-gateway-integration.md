---
id: "BIL-payment-gateway-integration"
title: "Payment gateway integration, dunning, refunds"
parent: "BIL"
order: 3
type: "capability"
template: "billing"
status: "draft"
owner: null
indicative: false
summary: "Payment collection through gateways per currency, inbound gateway events, dunning, refunds and daily settlement reconciliation; the same adapter serves tenants' case-fee collection"
links: []
rev: 2
syncHash: "7a0d6ad76bfd08dd"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 10.3 Payment gateway integration, dunning, refunds

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Payment collection through gateways per currency, inbound gateway events, dunning, refunds and daily settlement reconciliation; the same adapter serves tenants' case-fee collection

<!-- section:purpose -->
## Purpose and scope

Collects money for issued invoices and returns it when needed. Two uses share one adapter layer in `packages/payments`:
1. **Platform billing**: tenants pay Nomology's invoices from [[BIL-invoicing-taxes-gst-singapore]] (card, UPI / netbanking for INR, bank transfer, e-mandate or saved card for recurring).
2. **Case-fee collection**: parties pay a tenant's case fees, deposits or filing fees issued by [[DOM-invoices-and-vendor-bills]]. Here the **merchant of record is the tenant**: the payment goes into the tenant's own gateway merchant account, connected through the integration framework ([[INT-integration-framework]]). Nomology does not receive or hold those funds.

Out of scope: payouts to neutrals and transcribers (bank transfers from the tenant or Nomology, owned by [[DOM-invoices-and-vendor-bills]] with screening by [[INT-kyc-and-sanctions-screening]]); card data handling (we never see card numbers: hosted checkout or hosted fields only).

<!-- section:model -->
## Pricing model

No pricing of its own. Gateway fees are a cost to the merchant of record (Nomology for platform billing, the tenant for case fees) and are recorded from settlement reports as separate fee lines so that net settlement reconciles. Surcharging parties for card fees is off by default and is a tenant setting only where law allows (legal to confirm per region).

<!-- section:entitlements -->
## Entitlements

`feature.case_fee_collection` controls whether a tenant can connect its own merchant account. Payment collection for Nomology invoices is always available. The due-process rule applies: an unpaid Nomology invoice never blocks a party's payment of a case fee, nor a filing on an open case ([[BIL-plans-entitlements-and-usage#entitlements]], BIL-ENT-5).

<!-- section:metering -->
## Metering events

None billed. Operational counters only (payment attempts, success rate, refund count) to [[OBS-business-events]].

<!-- section:worked -->
## Worked examples

**1. Full payment with gateway fee (NTPL, INR)**: invoice INR 1,91,693.36 paid by netbanking. Settlement two days later: gross 1,91,693.36, gateway fee 2.00% = 3,833.87, GST on fee 18% = 690.10 (illustrative), net settled 1,87,169.39. Ledger: debit bank 1,87,169.39, debit gateway charges 3,833.87, debit input GST 690.10, credit receivable 1,91,693.36.

**2. Partial then full payment (TAPL, SGD)**: invoice S$2,953.90; customer pays S$2,000.00 by bank transfer (matched by virtual account reference) → `partially_paid`, balance S$953.90; second transfer S$953.90 → `paid`.

**3. Overpayment**: customer pays S$3,000.00 against S$2,953.90 → invoice `paid`, S$46.10 held as customer credit on the billing account and applied to the next invoice (or refunded on request).

**4. Refund after credit note**: credit note INR 14,160.00 (from invoicing example G) on a paid invoice; finance chooses refund. INR 14,160.00 is below the four-eyes threshold (proposed INR 50,000 / S$1,000 / US$1,000), so one approver suffices. Refund created with idempotency key `refund:{creditNoteId}`; gateway returns `pending`, then a `refund.processed` event marks it complete.

**5. Duplicate webhook**: the gateway sends `payment.captured` twice for the same payment. The second insert into `provider_event_inbox` hits the unique constraint on `(provider, connection_id, provider_event_id)` and is acknowledged with 200 without reprocessing.

**6. Chargeback (USD, card)**: US$2,067.00 invoice paid by card is disputed 40 days later. The dispute event moves the payment to `disputed`, re-opens the receivable, alerts finance with a deadline to submit evidence, and does not suspend the tenant automatically.

<!-- section:tax -->
## Tax and billing entity

Payments carry no new tax, with two exceptions handled in the ledger: GST charged by Indian gateways on their fees (input tax credit for NTPL, Example 1), and withholding tax deducted by some customers (for example Indian TDS on payments to NTPL, if the customer deducts it). A short payment marked by finance as "withheld" is recorded as `tax_withheld` with the certificate reference, not as an unpaid balance.

<!-- section:lifecycle -->
## Invoice and payment lifecycle

**Payment flow** (Temporal workflow `{tenantId}-invoice-collect-{invoiceId}` on queue `billing`):
1. On `billing.invoice.issued`, create a payment intent at the gateway (activity, idempotency key `pi:{invoiceId}:{attempt}`) [R1] and include the hosted payment link in the invoice email.
2. If the billing account has an active mandate or saved method, attempt a charge on the due date.
3. Wait for signals from gateway events (`payment.succeeded`, `payment.failed`, `refund.*`, `dispute.*`), with a timer for the due date and each dunning step.

**Dunning schedule (proposed; per-tenant overrides allowed by contract)**

| Day vs due date | Action |
|---|---|
| −3 | Reminder email to billing contacts |
| 0 | Auto-charge if mandate; otherwise reminder |
| +3 | Retry charge; reminder with payment link |
| +7 | Retry charge; email to tenant admins and Nomology account manager |
| +14 | Final notice stating the suspension date |
| +30 | Subscription `suspended` if the contract allows and the account manager has not paused dunning |

**Suspension (BIL-PAY-1)**: a suspended tenant cannot create new cases or enable features, and its admins see a banner. Open cases continue: parties can file, pay case fees, join hearings and download their records (BIL-ENT-5). Suspension never deletes data. Lifting suspension on payment takes effect within 60 seconds.

**Refunds (BIL-PAY-2)**: only against a credit note or an overpayment; amount ≤ amount captured minus prior refunds; four-eyes approval above the threshold; refunded to the original method where the gateway supports it, otherwise by bank transfer with screening of the destination account.

<!-- section:payments -->
## Payments, payouts and reconciliation

**Gateways (to decide)**: one RBI-authorised payment aggregator for INR (UPI, netbanking, cards, e-mandates) and one gateway for SGD and USD cards and transfers. Each is an adapter implementing:
```ts
interface PaymentGatewayAdapter {
  createIntent(i: { amountMinor: bigint; currency: 'INR'|'SGD'|'USD'; reference: string;
                    customerRef: string; idempotencyKey: string }): Promise<GatewayIntent>;
  charge(i: { mandateRef: string; amountMinor: bigint; currency: string; idempotencyKey: string }): Promise<GatewayCharge>;
  refund(i: { paymentRef: string; amountMinor: bigint; idempotencyKey: string }): Promise<GatewayRefund>;
  verifyWebhook(rawBody: Buffer, headers: Headers, secret: SecretRef): VerifiedEvent; // throws on bad signature
  fetchSettlements(day: string): AsyncIterable<SettlementLine>;
}
```
**Inbound events**: `POST /api/integrations/webhooks/{provider}/{connectionId}`; the connection ID identifies tenant and region. Signature verified over the raw body before parsing, with timestamp tolerance of 5 minutes [R2]; event stored in `provider_event_inbox` (unique on provider event ID); then the matching collection workflow is signalled. Unknown or unverifiable events return 400 and are logged as security events ([[OBS-security-events]]).

**Funds collected for institutions (BIL-PAY-3)**: case fees settle directly into the tenant's own merchant account. Nomology is not in the funds flow, which avoids acting as a payment aggregator. Any model where Nomology receives funds for a tenant requires a legal review first.

**Payee checks**: not applicable to customer payments. Refund destinations that are not the original payment method are screened through [[INT-kyc-and-sanctions-screening]] before release.

**Daily reconciliation (BIL-PAY-4)**: Temporal schedule `billing-settlement-recon` at 07:00 entity local time imports the previous day's settlement report per gateway, matches each line to a payment (by gateway payment ID), records fees, refunds and chargebacks, and compares: sum of settled payments − fees − refunds = bank credit (from the bank statement import in Odoo). Unmatched lines or any difference above zero go to a finance work queue ([[WF-human-tasks]]) with a one-working-day target.

**FEMA**: foreign-currency receipts for NTPL record the purpose code and the bank's advice reference (FIRC or equivalent) against the export invoice, so realisation within the RBI time limit can be shown [R3].

<!-- section:reporting -->
## Revenue and finance reporting

Outbox events `billing.payment.received`, `billing.payment.failed`, `billing.refund.processed`, `billing.dispute.opened` and `billing.settlement.reconciled` feed [[BIL-revenue-reporting-hooks-for]] and the unpaid-invoice views in [[RPT-cases]] and [[RPT-internal-mis]].

<!-- section:questions -->
## Open questions

- [ ] Choose the INR gateway (RBI-authorised payment aggregator) and the SGD / USD gateway; is one provider acceptable for all three?
- [ ] Legal: confirm that case fees settling directly into the tenant's own merchant account keeps Nomology outside payment aggregator rules in India, and the equivalent position in Singapore and the US.
- [ ] Legal and commercial: confirm the suspension policy (day +30, open cases unaffected) against tenant contracts and institution rules.
- [ ] Four-eyes thresholds for refunds per currency (proposed INR 50,000 / S$1,000 / US$1,000).
- [ ] Is card surcharging of parties ever permitted per region?
- [ ] Bank statement import: in Odoo (proposed) or in the platform?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant and client attribution

Each inbound webhook URL contains a `connectionId` that maps to exactly one tenant and region; the stored connection is loaded and its tenant set in context before any write, and the invoice referenced by the event must belong to that tenant or the event is rejected and alerted. Platform-billing payments are written in the tenant's region under its tenant ID; case-fee payments additionally carry case ID and payer party ID.

<!-- check:entitlements -->
### Entitlement enforcement

Suspension stops only new cases and new features; protected actions on open cases continue (BIL-PAY-1, BIL-ENT-5). Lifting suspension after payment propagates within 60 seconds through the entitlement cache.

<!-- check:payments -->
### Payments, payouts and screening

Gateway calls carry idempotency keys derived from our IDs (`pi:{invoiceId}:{attempt}`, `refund:{creditNoteId}`) [R1]. Webhooks are verified over the raw body with timestamp tolerance [R2], de-duplicated by provider event ID through a unique constraint in `provider_event_inbox`, and processed by signalling a Temporal workflow, so retries and out-of-order events are safe (the invoice state machine accepts only valid forward transitions). Settlements are reconciled daily per gateway against payments and bank credits, including fees, partial and over-payments, refunds and chargebacks (BIL-PAY-4). No card data reaches our systems (hosted checkout), keeping PCI DSS scope to the self-assessment level for hosted pages (to confirm). Case fees settle into the tenant's own merchant account (BIL-PAY-3). Refunds above threshold need four-eyes approval; non-original refund destinations are screened. Foreign receipts for NTPL record purpose code and bank advice for FEMA [R3].

<!-- check:audit -->
### Audit trail and adjustments

Refunds, write-offs, dunning pauses and suspension overrides record actor, reason code, justification and approver in the audit trail. Gateway events are kept verbatim (signature-verified raw body, encrypted) in `provider_event_inbox` for 8 years as payment evidence (proposed; to align with invoice retention).

<!-- check:finance -->
### Ledger and revenue recognition

Ledger effects per event are listed in [[BIL-revenue-reporting-hooks-for]]; Worked example 1 shows the fee split. Settlement reconciliation output is the evidence for month-end cash.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Clients send an Idempotency-Key header on POST requests; the server returns the saved result for retries with the same key.",
    "id": "R1",
    "kind": "vendor",
    "retrieved": "2026-10-28",
    "title": "Stripe API reference: Idempotent requests",
    "url": "https://docs.stripe.com/api/idempotent_requests",
    "vendor": "Stripe"
  },
  {
    "body": "OWASP",
    "excerpt": "Guidance on signing webhook payloads, timestamp checks against replay, and SSRF protection when delivering to user-supplied URLs.",
    "id": "R2",
    "kind": "standard",
    "title": "OWASP Webhook Security Cheat Sheet",
    "url": "https://cheatsheetseries.owasp.org/cheatsheets/Webhook_Security_Cheat_Sheet.html"
  },
  {
    "excerpt": "Sets the time limits and procedures for realisation and repatriation of export proceeds, including for export of services.",
    "id": "R3",
    "issuer": "Reserve Bank of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "title": "Master Direction - Export of Goods and Services",
    "url": "https://www.rbi.org.in/scripts/BS_ViewMasDirections.aspx?id=10395"
  }
]
```

<!-- end -->
