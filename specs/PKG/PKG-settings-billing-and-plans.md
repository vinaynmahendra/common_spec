---
id: "PKG-settings-billing-and-plans"
title: "Billing, plans and entitlement settings"
parent: "PKG-settings-catalogue"
order: 3
type: "feature"
template: "config"
status: "draft"
owner: null
indicative: false
summary: "Catalogue of `billing.*` settings: tenant billing profile and tax registration, payment preferences, usage alerts and over-limit behaviour, seat reclaiming, case fees collected from parties, and Nomology's platform billing operations (dunning, suspension, period boundary, discounts); plus the register of plan entitlement keys that gate settings in other catalogues"
links: []
rev: 1
syncHash: "037c3b75d377a376"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.7.3.3 Billing, plans and entitlement settings

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Catalogue of `billing.*` settings: tenant billing profile and tax registration, payment preferences, usage alerts and over-limit behaviour, seat reclaiming, case fees collected from parties, and Nomology's platform billing operations (dunning, suspension, period boundary, discounts); plus the register of plan entitlement keys that gate settings in other catalogues

<!-- section:purpose -->
## Purpose and scope

Registers the settings that tenants and Nomology use to run billing: how a tenant is invoiced by Nomology, how it is told about usage, what happens near plan limits, and how the tenant itself charges parties case fees. It also lists, for reference, the **entitlement keys** that other catalogues use in their Plan column.

Consumed by: [[BIL-plans-entitlements-and-usage]] (usage alerts, over-limit behaviour), [[BIL-invoicing-taxes-gst-singapore]] (billing profile, tax registration, e-invoicing), [[BIL-payment-gateway-integration]] (payment preferences, dunning, case-fee collection), [[DOM-invoices-and-vendor-bills]] (case fees charged to parties), [[AI-cost-controls]] (behaviour at the AI ceiling), [[APP-tenant-admin-console]] (plan and usage pages).

**Not here:** plans, prices, contract overrides and entitlements themselves. They are commercial records owned by [[BIL-plans-entitlements-and-usage]] (price-book versions, subscriptions, grants), changed by `platform_billing` under maker-checker, and read through `@nomology/entitlements`; they are not settings and do not use setting inheritance. Fee schedules for case fees are decision tables ([[PKG-rules-and-decision-engine]]); this catalogue selects which one applies. AI token budgets per unit or feature are in [[PKG-settings-ai]]; SMS budgets in [[PKG-settings-notifications]]. A tenant's billing entity (NTPL, TAPL, US entity) and invoice currency are set by the contract on the subscription, shown read-only.

<!-- section:scopes -->
## Scopes that apply

| Scope | Used for | Administered by |
|---|---|---|
| `platform` | Dunning, suspension mode, discount approval threshold, period boundary, defaults | `platform_billing` (checker `platform_owner` or a second `platform_billing`) |
| `region` | E-invoicing, accepted payment methods and currencies per region, dunning per region | `platform_billing` |
| `offering` | Trial length per product line | `platform_billing` |
| `tenant` | Billing profile, payment preference, usage alerts, seat reclaiming, case-fee policy | `billing_admin`, `tenant_owner`; payment terms set by `platform_billing` from the contract |
| `unit` | Invoice prefix and tax registration for units that issue their own case-fee invoices (for example a Singapore office) | `billing_admin` |
| `case_type` | Whether case fees apply, fee schedule, currency, due days, reminders | `workflow_designer` with `billing_admin` approval |
| `case` | Case-fee payment due days when the tribunal or secretariat extends time | `case_manager` (`case:configure`) |
| `user` | Not used | — |

<!-- section:catalogue -->
## Settings catalogue

**Billing profile** (`/admin/billing/profile`)

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `billing.profile.legal_name` | text≤200 | `brand.identity.legal_name` | tenant | no | all | `settings.billing:write` | next_billing_period (next invoice issued) | sensitive |
| `billing.profile.address` | object(postal address) | — (required before first invoice) | tenant | no | all | `settings.billing:write` | next_billing_period | sensitive |
| `billing.profile.tax_registration` | object{scheme enum{in_gstin, sg_gst, us_exemption_certificate, none}, number text≤20, verified bool} | none | tenant | no | all | `settings.billing:write` | next_billing_period | maker_checker |
| `billing.profile.place_of_supply` | enum{Indian state and union territory codes} | Derived from address | tenant | no | all | `settings.billing:write` | next_billing_period | maker_checker |
| `billing.profile.invoice_recipients` | set of up to 5 role mailbox addresses | Billing admin's address | tenant | no | all | `settings.billing:write` | immediate | standard |
| `billing.profile.purchase_order_ref` | text≤50 | — | tenant | no | all | `settings.billing:write` | next_billing_period | standard |
| `billing.profile.invoice_language` | ref(locale) | en | tenant | no | all | `settings.billing:write` | next_billing_period | standard |

**Payment** (`/admin/billing/payment`)

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `billing.payment.method_preference` | enum{invoice_terms, card, bank_transfer, upi_autopay} | invoice_terms | tenant | no | all | `settings.billing:write` | next_billing_period | sensitive |
| `billing.payment.autopay_enabled` | bool | false | tenant | no | all | `settings.billing:write` | next_billing_period | sensitive |
| `billing.payment.terms_days` | int 0–60 | 15 | platform, region, tenant | platform | all | `settings.platform:write` (`platform_billing`) (tenant value from contract) | next_billing_period | maker_checker |

**Usage alerts and limits** (`/admin/billing/usage`)

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `billing.usage.alert_thresholds_pct` | set⊆int 50–100, at most 4 values | [80, 100] | platform, tenant | no | all | `settings.billing:write` | immediate | standard |
| `billing.usage.alert_recipients` | set⊆ref(role) | [billing_admin, tenant_owner] | tenant | no | all | `settings.billing:write` | immediate | standard |
| `billing.usage.overage_policy` | enum{allow_and_bill, admin_approval_for_new_cases} | allow_and_bill | platform, tenant | no | all | `settings.billing:write` | immediate | sensitive |
| `billing.usage.ai_ceiling_behaviour` | enum{block_ai_features, admin_approval} | block_ai_features | platform, tenant | no | all | `settings.billing:write` | immediate | sensitive |
| `billing.usage.statement_roles` | set⊆ref(role) | [billing_admin, tenant_owner, auditor] | tenant | no | all | `settings.billing:write` | immediate | standard |
| `billing.seats.reclaim_inactive_days` | int 0–365 (0 = off) | 0 | tenant | no | all | `settings.billing:write` | next_job_run | sensitive |
| `billing.seats.notify_before_reclaim_days` | int 1–30 | 7 | tenant | no | all | `settings.billing:write` | next_job_run | standard |

**Case fees charged to parties** (`/admin/billing/case-fees`)

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `billing.case_fees.enabled` | bool | false | tenant, case_type | yes | `feature.payments.case_fees` | `settings.billing:write` | new_cases_only | maker_checker |
| `billing.case_fees.schedule` | ref(decision_table, kind fee_schedule) | — | tenant, case_type | yes | `feature.payments.case_fees` | `settings.billing:write` | new_cases_only | maker_checker |
| `billing.case_fees.currency` | enum{INR, SGD, USD, HKD, EUR, GBP} | `in`: INR; `sg`: SGD; `us`: USD | region, tenant, case_type | yes | `feature.payments.case_fees` | `settings.billing:write` | new_cases_only | maker_checker |
| `billing.case_fees.payment_due_days` | int 1–90 | 14 | tenant, case_type, case | no | `feature.payments.case_fees` | `settings.billing:write`; case scope `case:configure` | new_cases_only (case value applies at once to that case) | sensitive |
| `billing.case_fees.reminder_days_before_due` | set⊆int 1–30, at most 4 | [7, 3, 1] | tenant, case_type | no | `feature.payments.case_fees` | `settings.billing:write` | running_cases | standard |
| `billing.case_fees.non_payment_action` | enum{reminders_only, reminders_then_secretariat_task} | reminders_then_secretariat_task | tenant, case_type | no | `feature.payments.case_fees` | `settings.billing:write` | new_cases_only | sensitive |
| `billing.case_fees.accepted_methods` | set⊆{card, netbanking, upi, bank_transfer, wallet} | Region list ([[BIL-payment-gateway-integration]]) | region, tenant | yes | `feature.payments.case_fees` | `settings.billing:write` | running_cases | standard |
| `billing.case_fees.invoice_prefix` | text 2–10, `^[A-Z0-9/-]+$` | Tenant short code | tenant, unit | no | `feature.payments.case_fees` | `settings.billing:write` | scheduled (start of next financial year) | maker_checker |
| `billing.case_fees.issuer_tax_registration` | object{scheme, number} | — | tenant, unit | no | `feature.payments.case_fees` | `settings.billing:write` | scheduled | maker_checker |
| `billing.case_fees.refund_approval` | enum{single_approver, maker_checker}, `stricter_only` | maker_checker | platform, tenant | platform | `feature.payments.case_fees` | `settings.billing:write` | immediate | maker_checker |

**Platform billing operations** (platform console, `/platform/settings?domain=billing`)

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `billing.dunning.reminder_days_after_due` | set⊆int 1–60 | [3, 7, 14, 30] | platform, region | platform | all | `settings.platform:write` (`platform_billing`) | next_job_run | maker_checker |
| `billing.dunning.suspend_after_days` | int 15–120 | 45 | platform, region, tenant (contract) | platform | all | `settings.platform:write` (`platform_billing`) | next_job_run | maker_checker |
| `billing.suspension.mode` | enum{restricted, read_only} | restricted | platform | platform | all | `settings.platform:write` (`platform_billing`) | immediate | maker_checker |
| `billing.period.boundary` | enum{utc_month, tenant_local_month} | utc_month | platform, tenant | platform | all | `settings.platform:write` (`platform_billing`) | next_billing_period | maker_checker |
| `billing.trial.default_days` | int 7–90 | 30 | platform, offering | platform | all | `settings.platform:write` (`platform_billing`) | new trials only | standard |
| `billing.discount.approval_threshold_pct` | int 0–100 | 20 | platform | platform | all | `settings.platform:write` (`platform_billing`) | immediate | maker_checker |
| `billing.invoice.e_invoicing_enabled` | bool | `region = in`: true; others false | platform, region | platform | all | `settings.platform:write` (`platform_billing`) | next_billing_period | maker_checker |

Total: 34 keys.

**Entitlement keys used by settings catalogues** (reference only; these are entitlements in [[BIL-plans-entitlements-and-usage#entitlements]], not settings)

| Entitlement | Gates | Catalogue |
|---|---|---|
| `feature.branding.custom_theme` | `brand.theme.active_version` at tenant scope | [[PKG-settings-branding-content]] |
| `feature.branding.unit_themes` | Unit-scope themes | [[PKG-settings-branding-content]] |
| `feature.branding.compact_attribution` | `brand.footer.platform_attribution = compact` | [[PKG-settings-branding-content]] |
| `feature.custom_domain` | `brand.domain.primary_host` | [[PKG-settings-branding-content]] |
| `limit.locales` | Size of `locale.languages.enabled` | [[PKG-settings-branding-content]] |
| `feature.data.bulk_export` | `data.export.bulk_case_export_enabled` | [[PKG-settings-data-and-privacy]] |
| `feature.payments.case_fees` | All `billing.case_fees.*` keys | this node |
| `feature.config.packages` | Tenant export and import of packages | [[PKG-configuration-packages]] |
| `limit.config_sandboxes` | Number of sandbox tenants | [[PKG-configuration-lifecycle]] |
| `limit.custom_fields_per_entity` | Custom field definitions | [[PKG-metadata-management-entity]] |
| `limit.upload_mb` | Ceiling for `case.filing.max_upload_mb` | [[PKG-settings-cases-and-workflows]] |

<!-- section:validation -->
## Validation and dependencies

| Rule | Enforced | Message |
|---|---|---|
| `billing.profile.address` and `billing.profile.legal_name` are required before the first invoice; for an Indian tenant invoiced by NTPL, `place_of_supply` is required and must match the GSTIN state code when a GSTIN is given | Save; invoice run blocks and alerts `platform_billing` | "Add your billing address before your first invoice on 1 Nov." |
| `tax_registration.number` format per scheme (GSTIN 15 characters with check digit; Singapore GST registration number pattern); `verified` is set only by the verification job, never by the tenant | Save | "This GSTIN is not valid." |
| Changing tax registration or legal name after invoices exist never changes issued invoices; it applies to invoices issued after publish ([[BIL-invoicing-taxes-gst-singapore]]) | Always | Shown before publish |
| `billing.usage.overage_policy = admin_approval_for_new_cases` may only hold back creating new cases by tenant staff; it never blocks any action on the protected list (BIL-ENT-5: filing, uploading before a deadline, joining hearings, service, downloading own record) | Platform bound | — |
| `billing.usage.ai_ceiling_behaviour = admin_approval` lets a tenant admin approve AI use above the hard ceiling for up to 7 days at a time; usage above the ceiling is billed as overage ([[AI-cost-controls]]) | Runtime | — |
| `billing.seats.reclaim_inactive_days` never reclaims seats from roles needed by open cases (secretariat assigned as case manager on an open case) | Job | — |
| `billing.case_fees.enabled = true` requires `billing.case_fees.schedule`, `currency`, an active payment connection ([[INT-connections-admin]]), and, where the tenant issues tax invoices, `issuer_tax_registration` | Publish | "Connect a payment provider before enabling case fees." |
| `billing.case_fees.non_payment_action` has no option to dismiss, suspend or block a party's filings automatically; any such step is a decision by the secretariat or tribunal recorded on the case | By design | — |
| `billing.case_fees.invoice_prefix` changes take effect only at the start of a financial year (1 April in India) so invoice number series stay continuous (assumption: tax adviser to confirm per entity) | Save sets `effective_from` | — |
| `billing.case_fees.currency` must be in the currencies supported by the connected gateway for the region | Publish | — |
| `billing.discount.approval_threshold_pct` applies to contract overrides recorded by `platform_billing` ([[BIL-plans-entitlements-and-usage]] audit check) | Platform | — |

<!-- section:defaults -->
## Defaults by tenant type

| Key | Arbitral institution | SEBI ODR institution | CORD tenant | Court or government programme |
|---|---|---|---|---|
| `billing.payment.method_preference` | invoice_terms | invoice_terms | upi_autopay or card | invoice_terms |
| `billing.usage.overage_policy` | allow_and_bill | allow_and_bill | allow_and_bill | admin_approval_for_new_cases (budget-capped public bodies) |
| `billing.usage.ai_ceiling_behaviour` | admin_approval | block_ai_features | block_ai_features | block_ai_features |
| `billing.case_fees.enabled` | true (institution fees and deposits) | Per SEBI ODR fee rules (assumption: fees are prescribed by the circular and may be payable by the market participant, not the investor; legal to confirm) [R1] | true (party pays platform case fee) | false |
| `billing.case_fees.currency` | By seat: SGD, INR, USD, HKD | INR | INR | INR |
| `billing.case_fees.payment_due_days` | 14 | 7 (assumption) | 7 | — |
| `billing.case_fees.non_payment_action` | reminders_then_secretariat_task | reminders_then_secretariat_task | reminders_then_secretariat_task | — |
| `billing.case_fees.refund_approval` | maker_checker | maker_checker | maker_checker | — |
| `billing.period.boundary` | utc_month | tenant_local_month (assumption, Indian institutions expect IST months) | utc_month | tenant_local_month |

Why they differ: arbitral institutions collect deposits in several currencies; SEBI ODR fee rules are set by the regulator; court programmes are usually free to parties and funded by budgets, so new-case overage needs approval.

<!-- section:admin_ux -->
## Where it is administered

| Settings group | Console page | API | Copilot may propose |
|---|---|---|---|
| Plan, entitlements and usage (read-only plan view, usage statement) | Plan and billing → Overview (`/admin/billing`), Usage (`/admin/billing/usage`) | `GET /admin/v1/billing/plan`, `GET /admin/v1/billing/usage?period=` | Explain only |
| Billing profile | Plan and billing → Profile (`/admin/billing/profile`) | `/admin/v1/settings/billing.profile.*` | No (tax and address data are entered by people) |
| Payment | Plan and billing → Payment (`/admin/billing/payment`) | `/admin/v1/settings/billing.payment.*` | No |
| Usage alerts and seats | Plan and billing → Usage → Alerts | `/admin/v1/settings/billing.usage.*`, `billing.seats.*` | Yes |
| Case fees | Plan and billing → Case fees (`/admin/billing/case-fees`), per case type in the workflow studio | `/admin/v1/settings/billing.case_fees.*` | Yes, drafts only |
| Platform billing operations, entitlements, contract overrides | `/platform/billing/settings`, `/platform/tenants/[tenantId]/entitlements`, `/platform/plans` | `/platform/v1/...` | No |

Entitlement-gated settings across the console show a plan badge and the plan that includes them; a tenant admin can open "Request upgrade", which creates a task for the account team, never a self-service change of entitlements at launch.

<!-- section:change_control -->
## Change control and audit

- `maker_checker`: tax registration, place of supply, payment terms, all case-fee keys that change money owed (enable, schedule, currency, prefix, issuer registration, refund approval) and all platform billing operations. The checker needs `settings.billing:approve` (tenant) or `settings.platform:approve` (platform).
- `sensitive`: legal name, address, payment method, autopay, overage and AI ceiling behaviour, seat reclaiming, case-fee due days and non-payment action.
- Notified on publish: `billing_admin` and `tenant_owner`; for case-fee changes also secretariat leads of affected units; for platform changes the finance owner of each billing entity.
- Rollback: revert the change set. Money already invoiced or collected is never changed by a rollback; corrections are credit notes and refunds ([[BIL-invoicing-taxes-gst-singapore#lifecycle]]).
- Audit record: `admin.settings.published` with old and new values; billing-profile changes are also attached to the next invoice's evidence record.

<!-- section:migration -->
## Versioning and migration

- New domain; no previous keys. The AI ceiling and billing period questions open in [[BIL-plans-entitlements-and-usage#questions]] are now settings with proposed defaults (`billing.usage.ai_ceiling_behaviour`, `billing.period.boundary`), so the commercial decision is a value, not code.
- `billing.period.boundary` changes only at a period start; switching a tenant mid-term produces one short period with prorated allowances (worked example to be added to the billing node when the decision is made).
- Case-fee keys travel in blueprints and case-type packages; tax registrations, addresses and payment preferences never travel in packages.

<!-- section:testing -->
## Testing

- Protected-action tests: with every combination of overage policy, suspension mode and unpaid invoices, the protected list in BIL-ENT-5 still succeeds.
- Tax registration format and verification tests per scheme; invoice evidence test that issued invoices keep the old profile after a change.
- Case-fee configuration tests: enabling without a payment connection fails; currency outside gateway support fails; prefix change scheduled at financial-year start.
- Resolution tests for case-scope due-day overrides and pinning of fee schedule per case.
- Registry sync check for all 34 keys.

<!-- section:questions -->
## Open questions

- [ ] Confirm SEBI ODR fee rules (who pays, amounts, timing) for the SEBI ODR blueprint defaults. (owner: legal)
- [ ] Billing period boundary: is the tenant's local month needed for Indian institutions? (owner: CCO, finance)
- [ ] Should tenants be able to self-upgrade plans or buy add-ons in the console? Proposed: not at launch. (owner: CCO)
- [ ] Invoice prefix changes only at financial-year start: confirm for India, Singapore and US entities. (owner: tax adviser)

<!-- checks -->
## Template checks

<!-- check:inheritance -->
### Inheritance and locks

Tenant billing profile keys exist only at tenant scope (unit scope only for units that issue their own case-fee invoices). Case-fee keys resolve tenant → case type → case, are pinned at case start except reminders and accepted methods, and a case value for due days applies only to that case. Entitlements are not inherited settings: they gate settings through the Plan column ([[PKG-configuration-scope-hierarchy]], step 4).

<!-- check:permissions -->
### Who may change what

`settings.billing:write` for profile and alerts (`billing_admin`, `tenant_owner`), the same `settings.billing:write` for money-moving areas (payment and case-fee keys), which are maker-checker so a second billing approver holding `settings.billing:approve` must agree, `case:configure` for case extensions, and `settings.platform:write` (held by `platform_billing` for billing keys) for platform operations and contract-derived values.

<!-- check:safety -->
### Safe bounds

Main risks: blocking a party's access to justice for non-payment (no setting can block protected actions; non-payment escalates to a human); charging the wrong amount or currency (fee schedule and currency pinned per case and maker-checker); invalid tax invoices (format checks, required fields before invoicing, changes never alter issued invoices); seat reclaiming removing a case manager mid-case (excluded).

<!-- check:timing -->
### When changes take effect

Profile and tax changes apply from the next invoice issued; payment terms from the next period; case-fee policy to new cases only; reminders and accepted methods to running cases; prefixes and issuer registrations at the next financial year start.

<!-- check:audit -->
### Audit and rollback

Change sets plus value history give the billing configuration on any date; invoices store a snapshot of the billing profile and fee schedule version they used, so a past invoice can be explained without re-resolving settings.

<!-- check:sync -->
### Catalogue matches code

Registry sync check in CI; the invoice run fails closed if a required billing key is undefined in the registry.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "issuer": "Securities and Exchange Board of India",
    "jurisdiction": "IN",
    "kind": "regulation",
    "ref": "Amendment (December 2023) to circular dated 31 July 2023 on Online Resolution of Disputes in the Indian Securities Market",
    "status": "in force (provisions consolidated in SEBI master circulars)",
    "title": "SEBI circular: Amendment to circular dated July 31, 2023 on Online Resolution of Disputes in the Indian Securities Market",
    "url": "https://www.sebi.gov.in/legal/circulars/dec-2023/amendment-to-circular-dated-july-31-2023-on-online-resolution-of-disputes-in-the-indian-securities-market_80110.html"
  }
]
```

<!-- end -->
