# Template: Commercial / billing (`billing`)

Generated from `billing.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies how something is priced, metered, invoiced, taxed and paid, so money-related behaviour is exact, auditable and consistent across entities.

**Depth:** 2–6 pages. Worked numeric examples are mandatory: every pricing rule needs at least one calculated example. Tax treatment per billing entity (NTPL, TAPL, US entity) must be explicit. Edge cases (proration, refunds, credit notes, currency) need their own rows.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `purpose` Purpose and scope (level 1)

What is being charged or paid, to whom, by which entity.

Illustrative example (not a requirement):

> Platform subscription billing for institutional tenants: a base plan plus usage (cases, storage, AI tokens), billed monthly by the entity serving the tenant's region.

### `model` Pricing model (level 1)

Plans, prices, tiers, units, currencies.

Illustrative example (not a requirement):

> | Plan | Base / month | Included | Overage |
> |---|---|---|---|
> | Institution Standard | USD 2,000 | 100 active cases, 200 GB, 5M AI tokens | USD 12 / case, USD 0.10 / GB, USD 8 / 1M tokens |
> INR pricing for India tenants set separately (not FX-converted).

### `entitlements` Entitlements (level 1)

What each plan unlocks or limits, and enforcement behaviour at the limit.

Illustrative example (not a requirement):

> | Entitlement | Standard | At limit |
> |---|---|---|
> | SSO | ✓ | — |
> | AI hearing summaries | ✓ | Soft limit: warn at 80%, bill overage |
> | Tenants' custom domains | 1 | Hard limit |

### `metering` Metering events (level 1)

Usage events, their source, idempotency key and aggregation.

Illustrative example (not a requirement):

> | Event | Source | Idempotency key | Aggregation |
> |---|---|---|---|
> | `usage.case.active` | Daily job | `{tenant}:{case}:{date}` | Max distinct cases in month |
> | `usage.ai.tokens` | AI gateway | request ID | Sum |

### `worked` Worked examples (level 1)

Calculated invoices for typical and edge cases.

Illustrative example (not a requirement):

> Tenant with 130 active cases, 180 GB, 7M tokens in October:
> - Base USD 2,000
> - Cases: 30 × 12 = 360
> - Storage: within allowance = 0
> - AI: 2M × 8 = 16
> - **Subtotal USD 2,376** + tax per entity rules

### `tax` Tax and billing entity (level 1)

Which entity invoices which customers, tax registrations, rates and invoice requirements.

Illustrative example (not a requirement):

> | Customer location | Billing entity | Tax |
> |---|---|---|
> | India | NTPL | GST 18% (CGST+SGST or IGST) |
> | Singapore | TAPL | Singapore GST if registered |
> | US | US entity | Sales tax per state rules for SaaS |
> (Confirm with tax advisors before go-live.)

### `lifecycle` Invoice and payment lifecycle (level 2)

Invoice states, dunning, credit notes, refunds, proration on plan change.

Illustrative example (not a requirement):

> Draft → issued (1st) → paid / overdue (net 30) → dunning reminders at +7, +14, +21 days → suspension review at +45. Mid-month upgrade prorated daily.

### `payments` Payments, payouts and reconciliation (level 2)

How money is collected and paid out, whose account receives funds collected on behalf of institutions, payee verification and screening, withholding tax, and the daily reconciliation between gateway, bank and ledger.

Illustrative example (not a requirement):

> | Flow | Channel | Checks | Reconciled against |
> |---|---|---|---|
> | Tenant subscription | Gateway (card, UPI) or bank transfer | Signed, deduplicated webhooks | Gateway settlement report and bank statement, daily |
> | Neutral fee payout | Bank transfer | KYC, bank-account verification, sanctions screening; TDS for India payees | Payout file and bank debit advice |
> | Refund | Original payment method | Credit note issued first; second approver above threshold | Gateway refund report |

### `reporting` Revenue and finance reporting (level 2)

Data handed to finance, ledger sync, revenue recognition notes.

Illustrative example (not a requirement):

> Invoices and payments synced to the accounting system nightly; revenue recognised monthly for subscriptions, on usage for overages.

### `questions` Open questions (level 3)

Checklist.

Illustrative example (not a requirement):

> - [ ] Do case fees collected on behalf of institutions flow through our accounts or directly to the institution?

## Checks

### `accuracy` Metering accuracy and reconciliation

**Question:** Is every billable unit counted exactly once, and can each invoice line be reconciled back to the usage events that produced it?

- What is the idempotency key for each usage event, where is uniqueness enforced (a unique constraint in Postgres, not only in application code), and how long are keys kept?
- What happens to events that arrive late (after the period closes) or are retried by BullMQ or Temporal: added to the next invoice, or a credit or debit note on the closed one?
- Is usage aggregated from an append-only event table, so the invoice can be recomputed and compared at any time?
- Which independent count is used to check the meter (for example distinct active cases from the cases table versus usage.case.active events), and what difference triggers an alert?
- How are clock and period boundaries defined (UTC or tenant local midnight), and is that the same in metering, invoicing and reporting?
- If metering is down for some hours, is usage reconstructed from source data, and is that reconstruction tested?
- Can a tenant see a usage statement that matches their invoice line by line?

**Good answer:** Names the idempotency key and the database constraint for every event, the late-event and retry policy, and the period boundary rule. Describes a daily automated reconciliation between metered usage and an independent source with a stated tolerance (exact for counts), an alert owner, and a tested backfill procedure. Invoices can be regenerated from stored events and match the tenant-facing usage statement.

**Red flags:**

- Usage counters stored as mutable totals with no event history
- Deduplication only in application memory or in a cache
- No independent check that the meter is correct
- Different period boundaries in metering and invoicing

### `money` Money, currency and rounding

**Question:** Are amounts stored, calculated, rounded and converted in a way that gives the same result every time and matches the invoice that the customer receives?

- Are amounts stored as integers in minor units or as fixed-precision decimals (Prisma Decimal), never as floating point?
- Is the currency stored with every amount (ISO 4217 code), and is mixing currencies in one sum prevented in code?
- At which step is rounding applied (per unit price, per line, per invoice, or on tax), with which rule (half-up, half-even), and do the worked examples show it?
- For prices set per currency (USD, INR, SGD), is any FX conversion used anywhere? If so, which rate source, which date, and is the rate stored on the invoice?
- How are very small unit prices (for example per 1,000 AI tokens) handled so that rounding does not lose or invent money at scale?
- Are tax amounts rounded as each tax authority requires (for example GST computed per line or per invoice)?

**Good answer:** States the storage type for money, the currency field on every amount, the rounding rule and the exact step where it applies, and the FX source and date where conversion is used, all demonstrated in worked examples including a sub-cent unit price. A test shows that summing lines equals the invoice total to the minor unit.

**Red flags:**

- Floating-point arithmetic for money
- Rounding rule not stated, or different between invoice and ledger
- FX conversion with no recorded rate

### `tax` Billing entity and tax

**Question:** For every customer location and product, is it clear which entity (NTPL, TAPL, US entity) invoices, which tax applies at what rate, and what the invoice must contain to be legally valid?

- How is the billing entity chosen: by tenant region, by customer's location of belonging, or by contract? What if a customer's registered office and usage region differ?
- India (NTPL): GST registration and place-of-supply rule, CGST plus SGST versus IGST, export of services to overseas customers (zero-rated under a Letter of Undertaking), and whether e-invoicing with an IRN applies at NTPL's turnover?
- Singapore (TAPL): is TAPL GST-registered, how are local and overseas customers treated, and does reverse charge apply on the customer side for business customers?
- US entity: in which states is there economic nexus, is SaaS taxable in each, and is a tax calculation service used?
- Is the customer's tax ID (GSTIN, Singapore UEN/GST number, US exemption certificate) captured, validated and printed on the invoice?
- For payouts to neutrals and transcribers, is tax withheld at source (for example Indian TDS) and are payees' tax documents collected?
- For export receipts into India, how is realisation of foreign currency within the RBI time limit tracked (FEMA)?
- Has a named tax adviser reviewed the table, and when is it re-reviewed?

**Good answer:** A table of customer location and customer type against billing entity, tax type, rate, registration number and mandatory invoice fields, with the rule used to decide the entity. It covers India GST (including export and e-invoicing applicability), Singapore GST, US state sales tax nexus, withholding on payouts and FEMA realisation tracking. It is signed off by a named tax adviser with a review date.

**Red flags:**

- One tax rate applied regardless of entity or customer location
- Customer tax IDs not captured or not validated
- Payouts with no withholding assessment
- 'Confirm with tax advisers' left open at go-live

### `tenancy` Tenant and client attribution

**Question:** Is every usage event, charge and payment attributed to the correct tenant and, where relevant, to the client or case it relates to, with no possibility of one tenant being billed for another's usage?

- Is tenant_id taken from the authenticated context (the RLS session setting) rather than from the request body, for every usage event?
- Are billing tables protected by forced RLS like operational tables, and which roles (finance staff, billing service) can read across tenants?
- Where a tenant passes costs to its own clients (for example case fees charged to parties), how are client and case recorded on each charge?
- For usage generated by system jobs (Temporal workflows, nightly storage counts), how is the tenant determined and verified?
- How is shared or platform usage (for example AI calls made by Nomology support on a tenant's behalf) attributed or excluded?
- Is there a check that no usage event exists for a tenant that is suspended, deleted or in another region?

**Good answer:** States that tenant_id is derived from the authenticated or workflow context and never from user input, that billing tables use forced RLS with a named cross-tenant finance role, and how client and case attribution works. Describes the rule for support-generated usage and an automated check for usage against invalid tenants.

**Red flags:**

- Tenant ID accepted from client-side input
- Billing data excluded from RLS
- Support or internal usage billed to tenants without a rule

### `entitlements` Entitlement enforcement

**Question:** Is what the customer is allowed to use enforced from the same source of truth that billing uses, with defined behaviour at each limit and when billing systems fail?

- Is there one entitlement store read by both the application (to allow or block features) and the billing engine (to price usage)?
- For each soft and hard limit: what does the user see at the warning threshold and at the limit, and is the message accessible and clear about cost?
- If the entitlement service is unavailable, does the platform fail open (allow and bill later) or fail closed (block)? Is that choice different for case-critical actions such as filing before a deadline?
- Are limits ever allowed to block a statutory or procedural deadline (for example filing within SEBI ODR timelines)? If not, how is the exception recorded and billed?
- How quickly does a plan change (upgrade, downgrade, add-on) take effect in enforcement, and how is it prorated?
- How are trial, pilot and custom contract terms (common with institutions such as HKIAC) represented without code changes?

**Good answer:** Names the single entitlement source shared by enforcement and billing, gives a table of limits with user-visible behaviour, and states the fail-open or fail-closed rule for each, with a documented exception for deadline-critical legal actions. Plan changes take effect within a stated time with a proration rule shown in a worked example, and custom contract terms are data, not code.

**Red flags:**

- Plan limits hard-coded in application code separately from billing
- A billing outage can stop a party filing before a legal deadline
- Custom institution terms handled by manual invoice edits

### `payments` Payments, payouts and screening

**Question:** Are incoming payments and outgoing payouts processed safely and exactly once, reconciled to the bank or gateway, and screened where law requires?

- Are payment gateway calls made with idempotency keys, and are webhook events verified by signature, deduplicated by event ID and processed in a Temporal workflow or queue that tolerates retries and out-of-order delivery?
- How are gateway settlements reconciled daily to invoices and bank statements, including fees, chargebacks, partial and over-payments?
- Does the platform ever store or see card data? If not, how is PCI DSS scope kept to the minimum (hosted fields or redirect)?
- Where money is collected on behalf of institutions (case fees, deposits), whose account receives it, and has that arrangement been checked against payment aggregator and trust-account rules?
- For payouts to neutrals and transcribers: which KYC, bank-account verification and sanctions screening (for example OFAC, UN, MHA lists) happen before the first payout and on list updates?
- Is there a four-eyes approval for payouts above a threshold and for refunds?
- Are cross-border payouts and receipts recorded with the purpose codes and documents required under FEMA?

**Good answer:** Describes idempotent gateway calls, signed and deduplicated webhooks handled by a retry-safe workflow, and a daily three-way reconciliation (gateway, bank, ledger) with exception handling. Confirms PCI scope, the legal arrangement for funds collected on behalf of institutions, KYC and sanctions screening for payees with re-screening on list changes, approval thresholds, and FEMA documentation for cross-border flows.

**Red flags:**

- Webhooks processed without signature verification or deduplication
- No daily reconciliation with the gateway and bank
- Payouts to unverified or unscreened payees
- Funds held for institutions with no legal review

### `audit` Audit trail and adjustments

**Question:** Can every price, discount, credit, refund and manual adjustment be traced to who made it, when, why, and under whose approval, with issued invoices never changed in place?

- Are price books and plan versions effective-dated and immutable once used, so an old invoice can be recomputed with the prices that applied then?
- Are issued invoices immutable, with every correction made by a credit note or debit note that references the original?
- Who may grant discounts or credits, up to what amount, and does anything above that need a second approver?
- Is a reason code and free-text justification required for every manual adjustment, and is it stored with the actor and timestamp in the audit log?
- Are invoice numbers sequential per entity without gaps, as tax authorities expect?
- How long are invoices and billing records retained per entity (for example India: books of account 8 years under the Companies Act, GST records at least 72 months from the due date of the annual return under the CGST Act; Singapore: 5 years), and in which region?
- Can an external auditor get a complete export of adjustments for a period?

**Good answer:** Confirms effective-dated, immutable price versions; immutable issued invoices corrected only by linked credit or debit notes; gap-free numbering per entity; and an approval matrix with amounts and second approver. Every adjustment carries actor, time, reason code and approval in an append-only audit log, retention periods are stated per entity and region, and an auditor export exists.

**Red flags:**

- Editing or deleting an issued invoice
- Discounts applied with no approver or reason
- Price changes overwrite the old price
- Gaps or reuse in invoice numbering

### `finance` Ledger and revenue recognition

**Question:** Does billing data flow into the accounting ledger completely and on time, in a form that supports correct revenue recognition and month-end close for each entity?

- Which events post to the ledger (invoice issued, payment received, credit note, refund, write-off), with which accounts, and per entity?
- Is the sync idempotent and reconciled (count and total of invoices in billing equals the accounting system for each period)?
- How are subscription revenue (recognised over the period), usage overage (recognised as used) and prepaid or annual plans (deferred revenue) handled under IFRS 15 / Ind AS 115?
- How are multi-year institutional contracts with bespoke development and platform fees (for example HKIAC CMP) split into performance obligations?
- What is the period-close cut-off: when is usage frozen, and how are post-close corrections booked?
- Is intercompany billing between NTPL, TAPL and the US entity (for example transfer pricing for shared development) covered or explicitly out of scope?

**Good answer:** Lists the posting events and accounts per entity, an idempotent sync with a monthly reconciliation of counts and totals, and recognition rules for subscription, usage, prepaid and bundled contracts agreed with finance. States the close cut-off and post-close correction method, and the treatment or exclusion of intercompany charges.

**Red flags:**

- Annual prepayments recognised as revenue on receipt
- No reconciliation between billing and the ledger
- No defined cut-off for usage at period end

