---
id: "BIL-invoicing-taxes-gst-singapore"
title: "Invoicing, tax and multi-currency"
parent: "BIL"
order: 2
type: "capability"
template: "billing"
status: "draft"
owner: null
indicative: false
summary: "Invoices per billing entity (NTPL, TAPL, US entity): India GST and e-invoicing, Singapore GST, US state sales tax, credit notes, multi-currency"
links: []
rev: 3
syncHash: "2254e3d53b3c3c45"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 10.2 Invoicing, tax and multi-currency

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Invoices per billing entity (NTPL, TAPL, US entity): India GST and e-invoicing, Singapore GST, US state sales tax, credit notes, multi-currency

<!-- section:purpose -->
## Purpose and scope

Turns rated usage and subscription charges ([[BIL-plans-entitlements-and-usage]]) into legally valid tax documents issued by the correct Nomology entity:
- **NTPL** (India): tax invoices, credit and debit notes under India GST, with e-invoice registration (IRN and signed QR code) where applicable;
- **TAPL** (Singapore): tax invoices and credit notes under Singapore GST if TAPL is GST-registered;
- **US entity**: invoices with state sales tax where the entity has nexus and SaaS is taxable.

It owns billing entities, billing accounts (the tenant's legal and tax identity for invoicing), the invoice run, numbering, tax determination, currency handling, PDF rendering and delivery. Collection is in [[BIL-payment-gateway-integration]]; ledger posting in [[BIL-revenue-reporting-hooks-for]] and [[INT-accounting-sync]].

The tax engine and numbering service are also used by [[DOM-invoices-and-vendor-bills]] when a tenant issues case-fee invoices, but in that case the **tenant** is the supplier and its own registrations apply; this node only provides the mechanism.

<!-- section:model -->
## Pricing model

Invoices are produced monthly in arrears for usage and in advance for base fees and add-ons (proposed: one combined invoice per tenant per month, issued on the 1st working day after period close at 06:00 in the entity's time zone: IST for NTPL, SGT for TAPL, US Eastern for the US entity). Annual prepaid contracts produce one advance invoice for the base fee and monthly usage invoices. Invoice currency equals the billing account's contract currency (INR, SGD or USD); each entity also stores amounts in its functional currency (NTPL: INR, TAPL: SGD, US entity: USD) using the rate rule in the Tax section.

<!-- section:entitlements -->
## Entitlements

Not applicable to invoicing itself. One interaction: when a billing account has no valid tax identity where one is required (for example an Indian business customer without a verified GSTIN that wants to claim input tax credit), the invoice is issued as a B2C-style invoice and the tenant admin sees a banner asking for the GSTIN; this never blocks any platform feature.

<!-- section:metering -->
## Metering events

Consumes `usage_aggregate` rows from [[BIL-plans-entitlements-and-usage#metering]]. The invoice run (Temporal workflow `billing-invoice-run-{entity}-{period}` on task queue `billing`, one child workflow per tenant, workflow ID `{tenantId}-invoice-{period}`) records the `input_hash` of each aggregate on the draft invoice line, so a line can always be traced to the exact events that produced it.

<!-- section:worked -->
## Worked examples

Prices from [[BIL-plans-entitlements-and-usage#worked]] Example 1 (subtotal INR 1,62,452.00). Tax is computed **per line**, rounded half-up to the minor unit, and summed (proposed; to be confirmed by the tax adviser). Rates shown are assumptions for illustration, to be confirmed.

**A. NTPL → institution registered in Karnataka (intra-state, NTPL also in Karnataka)**

| Line | Taxable value | CGST 9% | SGST 9% |
|---|---|---|---|
| Base fee | 1,50,000.00 | 13,500.00 | 13,500.00 |
| Active cases overage | 12,000.00 | 1,080.00 | 1,080.00 |
| Storage overage | 320.00 | 28.80 | 28.80 |
| AI tokens | 132.00 | 11.88 | 11.88 |
| **Total** | **1,62,452.00** | **14,620.68** | **14,620.68** |

Invoice total INR 1,91,693.36. IRN and signed QR code obtained before the PDF is released (if e-invoicing applies).

**B. Same usage, customer registered in Maharashtra (inter-state)**: IGST 18% per line, total IGST INR 29,241.36; invoice total INR 1,91,693.36.

**C. NTPL → overseas institution, USD contract, export of services under a Letter of Undertaking (LUT)**: base USD 1,800.00 + 30 cases × USD 5.00 = USD 1,950.00; IGST 0 (zero-rated, assuming the export-of-services conditions are met, including receipt in convertible foreign exchange). Invoice carries the LUT reference and the required declaration text (wording from tax adviser). Functional amount recorded in INR at the rate rule below; realisation tracked under FEMA (see Payments section).

**D. TAPL → Singapore GST-registered customer, SGD**: S$2,500.00 + 30 × S$7.00 = S$2,710.00; GST 9% = S$243.90; total S$2,953.90 (assuming TAPL is GST-registered).

**E. TAPL → customer outside Singapore**: S$2,710.00, GST 0% if the supply qualifies as an international service (assumption, to be confirmed).

**F. US entity → customer in a state where it has nexus and SaaS is taxable**: USD 1,950.00 × rate returned by the tax service (illustrative 6.000%) = USD 117.00; total USD 2,067.00. Customer with a valid exemption certificate: tax 0, certificate ID printed.

**G. Credit note on A**: 30 overage cases turn out to be test cases created by the tenant's implementation team. Credit note referencing the original invoice: taxable 12,000.00, CGST 1,080.00, SGST 1,080.00, total INR 14,160.00. The original invoice is unchanged.

**H. Rounding stress**: AI tokens line INR 140.74 (from Example 2) × 9% = 12.6666 → CGST 12.67, SGST 12.67.

<!-- section:tax -->
## Tax and billing entity

**Billing entity selection (BIL-TAX-1)**: the entity is set on the `billing_account` when the contract is signed and is not derived at runtime from the hosting region. Default mapping proposed for sales:

| Customer location of belonging | Default entity | Hosting region (independent) |
|---|---|---|
| India | NTPL | India |
| Singapore | TAPL | Singapore |
| United States | US entity | US |
| Elsewhere | NTPL or TAPL by contract | Any (tenant choice) |

Changing a billing account's entity takes effect from the next period and requires finance approval (four-eyes).

**Tax treatment table (assumptions, to be reviewed by the named tax adviser before the first invoice from each entity)**

| Entity | Customer | Treatment | Invoice must show |
|---|---|---|---|
| NTPL | Indian business, same state | CGST + SGST (assumed 9% + 9% for SaaS) | NTPL GSTIN, customer GSTIN, place of supply, SAC code (to confirm), consecutive number unique per financial year (assumed max 16 characters), IRN + QR if e-invoicing applies |
| NTPL | Indian business, other state | IGST (assumed 18%) | As above |
| NTPL | Indian, unregistered | GST by place of supply = customer address state | As above without customer GSTIN |
| NTPL | Overseas business | Export of services, zero-rated under LUT, if conditions met | LUT reference, export declaration, currency |
| TAPL | Singapore business | Singapore GST at standard rate (assumed 9%) if TAPL is registered | TAPL GST registration number, tax invoice fields per IRAS |
| TAPL | Overseas business | Zero-rated international service (assumption) | As above, GST 0% |
| TAPL / NTPL | Singapore customer, supplier overseas | If NTPL invoices a Singapore customer directly, Singapore's overseas vendor and reverse-charge rules may apply [R2] | Adviser to confirm; default is to route Singapore customers to TAPL |
| US entity | US business | State sales tax only where nexus exists and SaaS is taxable; rate from a tax service | Tax per jurisdiction, exemption certificate ID if exempt |

**India e-invoicing (BIL-TAX-2)**: if NTPL's aggregate turnover is above the notified threshold, every B2B invoice and credit / debit note is reported to the Invoice Registration Portal and receives an IRN and signed QR code [R1]. The workflow requests the IRN (through a GST Suvidha Provider or the direct API; to decide) as an activity before the invoice is marked `issued`; if the portal is down, the invoice stays `pending_irn` and is retried with backoff, and the tenant is not sent an invoice without an IRN. Reporting deadlines after the invoice date (if any apply at NTPL's turnover) are tracked as an alert at 50% of the window.

**Tax identity capture (BIL-TAX-3)**: GSTIN (format check plus verification through the GST provider), Singapore UEN and GST registration number, US exemption certificates (stored as documents with expiry). Changes are audited and take effect on the next invoice.

**FX rule (BIL-TAX-4)**: when invoice currency differs from the entity's functional currency, the rate, its source and date are stored on the invoice. Source per entity is to be fixed by finance (assumption: for NTPL the rate prescribed for GST valuation, for TAPL the rate IRAS accepts, for the US entity a daily reference rate).

**Retention (BIL-TAX-5)**: issued invoices, notes and IRN responses are kept in the tenant's home region and exported to the entity's accounting system. Proposed retention: 8 years for NTPL and TAPL records, 7 years for the US entity, to be confirmed by finance against the Companies Act, CGST Act and Singapore record-keeping rules.

<!-- section:lifecycle -->
## Invoice and payment lifecycle

Invoice state machine ([[WF-entity-state-machines]]):

```
draft ──finalise──▶ pending_irn ──irn_ok──▶ issued ──payment──▶ paid
  │                     │ (NTPL e-invoice only)    │──partial──▶ partially_paid ──▶ paid
  └──discard            └──irn_rejected──▶ draft   │──due date──▶ overdue ──▶ paid / written_off
                                                    └──credit note covering 100%──▶ credited
```
- Drafts are visible to finance for 24 hours before finalisation (proposed review window) and may be edited only by regeneration from usage.
- `issued` invoices are immutable. Corrections: **credit note** (reduces) or **debit note** (increases), each with its own number series per entity, referencing the original invoice number and date, with reason code (`pricing_error`, `usage_dispute`, `goodwill`, `cancellation`, `tax_correction`).
- An e-invoice may be cancelled only within the portal's cancellation window (if any); after it, a credit note is required. This window is a configuration value, not code.
- Numbering: one gap-free sequence per entity, document type and financial year (India: April–March; Singapore and US: per entity's financial year, to confirm), allocated by a `SELECT ... FOR UPDATE` on `invoice_number_sequence(entity_id, doc_type, fiscal_year)` inside the finalise transaction, so a rolled-back finalisation never consumes a number.
- Write-off requires finance approval (four-eyes) and posts to the ledger.

<!-- section:payments -->
## Payments, payouts and reconciliation

Collection, dunning and refunds are in [[BIL-payment-gateway-integration]]. For NTPL export invoices, the invoice carries `export_realisation_due_at`, computed from the invoice date and the time limit in the RBI direction on export of goods and services [R3] (period to be confirmed by finance); receipts are matched against it and an alert is raised to finance 30 days before the due date for unrealised amounts.

<!-- section:reporting -->
## Revenue and finance reporting

Every invoice, note and write-off writes an outbox event (`billing.invoice.issued`, `billing.credit_note.issued`, `billing.debit_note.issued`, `billing.invoice.written_off`) consumed by [[BIL-revenue-reporting-hooks-for]]. Each invoice line carries `service_period_start`, `service_period_end` and `revenue_category` so the ledger can recognise revenue over time.

<!-- section:questions -->
## Open questions

- [ ] Tax adviser (name) to confirm the treatment table, rates, SAC code, invoice wording and rounding rule for each entity.
- [ ] Is NTPL above the e-invoicing turnover threshold now, and which reporting window applies? Use a GSP or the direct IRP API?
- [ ] Is TAPL GST-registered, or likely to cross the registration threshold, and which customers will it invoice?
- [ ] US entity: which states have economic nexus, and which sales tax service (for example a hosted tax API) to use?
- [ ] FX rate source per entity for functional-currency amounts.
- [ ] Invoice timing: combined monthly invoice in arrears plus advance base fee (proposed) or separate invoices?
- [ ] Do any institutional contracts require invoices in the client's own format or portal upload (vendor portals)?
- [ ] Retention periods per entity (proposed 8 / 8 / 7 years).

<!-- checks -->
## Template checks

<!-- check:money -->
### Money, currency and rounding

Amounts are `bigint` minor units with ISO 4217 currency on every row. Tax is computed per line and rounded half-up to the minor unit (Worked example H shows a fractional case). FX is never used to price; it is used only to record functional-currency values, with rate, source and date stored on the invoice (BIL-TAX-4).

<!-- check:tax -->
### Billing entity and tax

Entity is chosen by contract on the billing account (table BIL-TAX-1), independent of hosting region, so a Singapore-hosted tenant can still be invoiced by NTPL if the contract says so. Treatment per entity and customer type is in the tax table; India covers CGST + SGST versus IGST by place of supply, zero-rated export under LUT, and e-invoicing with IRN [R1]; Singapore covers TAPL registration and the overseas vendor question [R2]; the US entity uses a tax service and exemption certificates. Customer tax IDs are captured and verified (BIL-TAX-3). Export realisation is tracked per invoice against the RBI time limit [R3]. Payout withholding (TDS) belongs to [[DOM-invoices-and-vendor-bills]]. Every rate and rule in the table is flagged as an assumption until the tax adviser signs it off; re-review is proposed annually and on any rate change.

<!-- check:tenancy -->
### Tenant and client attribution

Invoices, lines and notes are tenant-owned tables with forced RLS. The invoice run fans out one child workflow per tenant and sets tenant context through the Temporal interceptor before reading usage. Finance staff read across tenants only through the reporting role and warehouse ([[MT-cross-tenant-reporting-via-a]]).

<!-- check:audit -->
### Audit trail and adjustments

Issued invoices are immutable; all corrections are credit or debit notes referencing the original. Numbers are gap-free per entity, document type and financial year, allocated inside the finalise transaction. Every finalisation, note, write-off and entity change is written to the audit trail with actor, reason and approver; write-offs and entity changes need four-eyes approval. Retention is proposed at 8 / 8 / 7 years by entity, in the tenant's home region, with a copy in the accounting system.

<!-- check:finance -->
### Ledger and revenue recognition

Each document emits an outbox event with lines carrying service period and revenue category; [[BIL-revenue-reporting-hooks-for]] maps these to ledger postings per entity and [[INT-accounting-sync]] delivers them idempotently to Odoo, with daily count-and-total reconciliation.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Explains e-invoice reporting to the Invoice Registration Portal, generation of the Invoice Reference Number (IRN) and signed QR code, and applicability by aggregate turnover.",
    "id": "R1",
    "kind": "web",
    "publisher": "Goods and Services Tax Network (GSTN)",
    "retrieved": "2026-10-28",
    "title": "e-Invoice System FAQs",
    "url": "https://einvoice1.gst.gov.in/Others/Faqs"
  },
  {
    "excerpt": "Explains when overseas suppliers of digital services to Singapore customers must register for GST under the Overseas Vendor Registration regime.",
    "id": "R2",
    "kind": "web",
    "publisher": "Inland Revenue Authority of Singapore (IRAS)",
    "retrieved": "2026-10-28",
    "title": "GST for overseas businesses and digital services",
    "url": "https://www.iras.gov.sg/taxes/goods-services-tax-(gst)/gst-and-digital-economy/overseas-businesses"
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
