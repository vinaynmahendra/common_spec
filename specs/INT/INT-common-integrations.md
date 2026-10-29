---
id: "INT-common-integrations"
title: "Common integrations"
parent: "INT"
order: 2
type: "capability"
template: "integration"
status: "draft"
owner: null
indicative: false
summary: "Catalogue of provider integrations (email, SMS, WhatsApp, calendar, video, e-signature, payment gateways, accounting, KYC) with the provider choice per region, ownership models, default data policy groups and core status; each provider has its own child node"
links: []
rev: 3
syncHash: "186c726feb5a1442"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 9.2 Common integrations

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Catalogue of provider integrations (email, SMS, WhatsApp, calendar, video, e-signature, payment gateways, accounting, KYC) with the provider choice per region, ownership models, default data policy groups and core status; each provider has its own child node

<!-- section:purpose -->
## Purpose and use cases

Lists every category of external provider the platform uses, the use cases it serves, the provider chosen (or shortlisted) per region, and the **catalogue defaults** each category carries into connection administration ([[INT-connections-admin]]) and connector data policies ([[INT-connector-data-policies]]). Each provider category has its own child node with the full data mapping and error handling; this node records the shared choices and covers the two small categories that do not yet have their own node: **email delivery** (mechanics in [[INT-messaging-providers]]) and **calendar**.

| Category | Use cases | Node | Ownership models offered | Default data policy group (platform baseline) | Core? |
|---|---|---|---|---|---|
| Video conferencing | Virtual hearings, recordings, transcript hand-off | [[INT-video-conferencing-for-hearings]] | platform_managed; tenant_byo later | case_data_approved for `recording_media` only where in-region | no |
| E-signature | Settlement agreements, awards, declarations, consent forms | [[INT-e-signature]] | platform_managed, tenant_byo | case_data_approved (`document_content`, `contact_pii`) | no |
| KYC and sanctions | Party identity where rules require it; payee screening before payouts | [[INT-kyc-and-sanctions-screening]] | platform_managed | case_data_approved (`identity_document`, `contact_pii`); nothing else | no |
| Messaging: email | Notices, reminders, OTPs | [[INT-messaging-providers]] | platform_managed, tenant_byo | metadata_only plus approved notice summaries | yes |
| Messaging: SMS | Reminders, OTPs, notice prompts | [[INT-messaging-providers]] | platform_managed, tenant_byo | metadata_only (`system_reference`, recipient `contact_pii`, case reference) | yes |
| Messaging: WhatsApp | Opt-in nudges | [[INT-messaging-providers]] | platform_managed (shared number), tenant number later | metadata_only, max tier `public` | no |
| Accounting | Ledger posting per billing entity | [[INT-accounting-sync]] | platform_managed (Nomology entities); tenant_byo for tenants' own books later | metadata_only plus `financial` | no |
| Payment gateways | Nomology invoices; tenants' case fees | [[BIL-payment-gateway-integration]] | platform_managed, tenant_byo | `financial`, payer `contact_pii` | no |
| Calendar | Hearing invites; neutral free / busy | This node | `.ics` (no connection); user_connected for free / busy | metadata_only | no |
| Embedded component accessibility | Register of vendor UI inside our journeys | [[INT-third-party-component]] | — | — | — |

"Core" connectors cannot be blocked by a tenant (only constrained) because legal service and sign-in depend on them; see [[INT-connector-data-policies#policy]].

<!-- section:party -->
## External party and ownership

Provider choices are **not yet made**; candidates below are for evaluation through [[SEC-vendor-sub-processor-management]] and are not commitments.

| Category | India | Singapore | US | Contract owner |
|---|---|---|---|---|
| Email | Cloud email service in an India region (for example Amazon SES in ap-south-1) | Same service in ap-southeast-1 | Same service in a US region | CTO office |
| SMS | DLT-registered Indian SMS aggregator | Provider supporting Singapore sender ID registration | US SMS provider with 10DLC registration | CTO office |
| Video | To select: provider with in-region media and recording storage, or self-hosted media servers in region | Same | Same | Product (TERES) |
| E-sign | CCA-licensed eSign Service Provider for Aadhaar eSign; global e-sign provider for others | Global e-sign provider | Global e-sign provider | Legal + CTO office |
| KYC / sanctions | Indian KYC provider (PAN, DigiLocker / offline Aadhaar where permitted); global screening list provider | Global provider | Global provider | Compliance |
| Accounting | Odoo (company per entity; hosting to decide) | Odoo | Odoo | Finance |
| Payments | RBI-authorised payment aggregator | Card / transfer gateway | Card / ACH gateway | Finance |

Each provider node records environments (sandbox per region, production per region), support contacts and escalation path once chosen. Each chosen provider becomes a **catalogue entry** with its regions, offerings, entitlement key, ownership models, auth kinds, operation data manifest, sub-processor ID and accessibility record ([[INT-connections-admin#mapping]]); BYO accounts are the tenant's own contracts.

**Calendar**: baseline is an iCalendar (`.ics`) attachment on hearing notices [R4] with stable `UID` = `hearing-{hearingId}@{tenant-domain}` and incrementing `SEQUENCE` on reschedule, so updates replace the entry in any calendar client (`integration.calendar.ics_attachments`). Optional later: neutrals who connect their own Microsoft 365 or Google calendar (a `user_connected` connection through [[INT-integration-framework]], OAuth authorisation code with PKCE) let the platform read free / busy only (`integration.calendar.sync_scope` locked to `free_busy_only`).

<!-- section:flows -->
## Data flows

| Flow | Direction | Trigger | Mode | Runs in |
|---|---|---|---|---|
| Send email / SMS / WhatsApp | Out | Notification dispatch | Async | BullMQ `notifications` |
| Delivery receipts, bounces, opt-outs | In | Provider webhook | Async | Inbox → BullMQ |
| Create hearing room, mint join token | Out | Hearing scheduled / participant joins | Async / sync (token) | Temporal `hearings` / Route Handler |
| Recording ready | In | Provider webhook | Async | Inbox → Temporal signal |
| Create signing envelope; signing completed | Out / In | Award or settlement ready to sign | Async | Temporal `documents` |
| KYC check; sanctions screen; list update | Out / In | Party onboarding, payee setup, list delta | Async | Temporal `cases` / schedule |
| Post invoice / payment to ledger | Out | Billing events | Async | BullMQ `accounting` |
| Payment intent; gateway events | Out / In | Invoice issued; gateway webhook | Async | Temporal `billing` |
| Calendar invite | Out | Hearing scheduled / changed | Async | With the notification |

<!-- section:mapping -->
## Data mapping

Field mappings are in each child node. Cross-cutting rules:
- Our identifiers sent to providers are opaque (`hearingId`, `envelope` external reference = `{tenantId}:{documentVersionId}`), never case titles or party names unless the use case needs them (for example the signer's name on an e-sign envelope).
- Personal data per category: email (address, name), SMS / WhatsApp (phone number, message text), video (display name, IP, audio / video), e-sign (name, email or Aadhaar-based identity at the ESP, document hash or content), KYC (identity document data), accounting (business billing contact only).
- Confidential case content is never sent in SMS or WhatsApp text; messages say a notice is available and link to the platform.

<!-- section:auth -->
## Authentication and secrets

All provider credentials are stored in the regional secrets manager through [[INT-integration-framework]]; inbound webhooks are signature-verified per connection. Method per provider is defined in each child node.

<!-- section:errors -->
## Errors, retries and idempotency

Shared policy from [[INT-integration-framework#errors]]: one retry layer (Temporal or BullMQ), idempotency keys on all mutating calls, provider event IDs de-duplicated in the inbox, forward-only state transitions. Category-specific degradation:

| Category | If the provider is down |
|---|---|
| Email | Queue and retry up to 24 h; switch to the secondary provider for the region if configured; legal notices also attempted by the next channel per [[DOM-service-of-notices-and-proof]] |
| SMS / WhatsApp | Retry 2 h; fall back to email |
| Video | Hearing room shows provider status; secretariat can issue a fallback dial-in or reschedule; no automatic switch mid-hearing |
| E-sign | Envelope creation retried; signer sees "signing temporarily unavailable"; deadline extension is a tribunal decision, not automatic |
| KYC / sanctions | Payout held (fail closed); party onboarding continues where KYC is not a precondition |
| Accounting | Queue indefinitely; alert at 4 h lag |
| Payments | Show "payment unavailable, try later" and an alternative (bank transfer details) |

<!-- section:limits -->
## Rate limits and SLAs

Provider limits and our expected volume are recorded per child node once providers are chosen. Planning volumes (proposed, end of Year 1 across regions): 1.5 M emails per month, 400 k SMS per month (mostly SEBI ODR reminders in India), 3,000 hearing hours per month, 2,000 signing envelopes per month, 5,000 KYC or screening checks per month.

<!-- section:residency -->
## Data transfer and compliance

Rule: each tenant's integrations use provider accounts or endpoints in its home region. Where a provider processes data outside the region, the transfer must have a recorded basis before the connector can be enabled for that region: for India, transfers are permitted unless to a country the Government restricts [R1]; for Singapore, the Transfer Limitation Obligation requires comparable protection, usually by contract [R2]; for EU parties in a case, Standard Contractual Clauses or adequacy apply [R3]. Each provider appears on the sub-processor list shown to tenants, and tenants are told before a new one is added. Institution contracts that restrict where case data may go override defaults: they are expressed as tenant connector data policy rules (`residency: in_region`) and the switch `integration.data_policy.require_in_region` ([[PKG-settings-integrations]]), checked at connection activation and on every call. For `tenant_byo` accounts the tenant declares the provider's processing location ([[INT-connections-admin#residency]]).

<!-- section:testing -->
## Sandbox and testing

Each provider has a sandbox connection per region in dev, staging and UAT; production credentials exist only in production secrets paths, and non-production environments cannot read them (IAM policy per environment). Contract tests with recorded fixtures per adapter; synthetic monitoring in staging runs one end-to-end flow per category daily.

<!-- section:questions -->
## Open questions

- [ ] Choose providers per category and region (table above); record each as an ADR.
- [ ] Video: managed provider with in-region recording versus self-hosted media servers per region (see [[INT-video-conferencing-for-hearings]]).
- [ ] Odoo hosting and topology: one database with a company per entity, or separate databases per entity and region?
- [ ] Is two-way calendar sync wanted for neutrals in Phase 7, or is `.ics` plus free / busy enough?
- [ ] Secondary email provider per region for failover: needed for SEBI ODR notice volumes? If yes, configure as `integration.default_connection.messaging.secondary`.
- [ ] Confirm which categories are "core" (proposed: email and SMS only).

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant separation at the provider

Platform-owned provider accounts are shared per region; every outbound object carries our tenant-scoped external reference and every inbound event is mapped by connection ID to one tenant, then re-checked against the stored record ([[INT-integration-framework#tenant]]). Tenants may bring their own accounts for the categories allowed in `integration.connection.byo_categories` ([[PKG-settings-integrations]]); per-user calendar connections hold user-scoped credentials. Provider-side resources (SMS templates, sender IDs, e-sign branding) are created per tenant and region through automation where the provider has an API, otherwise through a recorded runbook ([[PKG-notification-sender-identity]]).

<!-- check:residency -->
### Data transfer and residency

Per-region accounts and endpoints are the default; any out-of-region processing needs a recorded basis per jurisdiction [R1][R2][R3] before the connector is enabled, enforced by connector data policies on every call; tenant contract restrictions are tenant policy rules. Data minimisation in the mapping section and the platform baseline groups reduce what crosses (no case content in SMS / WhatsApp, opaque references).

<!-- check:vendor -->
### Vendor risk and exit

Every candidate goes through [[SEC-vendor-sub-processor-management]]: ISO 27001 or SOC 2 Type II evidence, breach notice terms compatible with CERT-In's 6-hour reporting, no use of our data for model training, exit plan (export format, deletion certificate). Adapter interfaces allow a second provider per category.

<!-- check:resilience -->
### Failure handling and degradation

Category-specific degradation is tabled in Errors; all outbound calls run in workers with one retry layer and idempotency keys; per-tenant rate limits stop one tenant exhausting a shared provider quota.

<!-- check:testing -->
### Testing

Sandbox per region and environment, production credentials unreadable outside production, contract tests from recorded fixtures, daily synthetic flow per category in staging.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "issuer": "Ministry of Electronics and Information Technology, India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 22 of 2023",
    "title": "Digital Personal Data Protection Act, 2023",
    "url": "https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf"
  },
  {
    "excerpt": "An organisation transferring personal data outside Singapore must ensure the recipient is bound to provide a comparable standard of protection, for example by contract.",
    "id": "R2",
    "kind": "web",
    "publisher": "Personal Data Protection Commission Singapore",
    "retrieved": "2026-10-28",
    "title": "Advisory Guidelines: The Transfer Limitation Obligation (Chapter 19)",
    "url": "https://www.pdpc.gov.sg/-/media/files/pdpc/pdf-files/advisory-guidelines/the-transfer-limitation-obligation---ch-19-(270717).pdf"
  },
  {
    "excerpt": "Model clauses for transfers of personal data from the EU to third countries.",
    "id": "R3",
    "kind": "web",
    "publisher": "European Commission",
    "retrieved": "2026-10-28",
    "title": "Standard Contractual Clauses (SCC)",
    "url": "https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/standard-contractual-clauses-scc_en"
  },
  {
    "body": "IETF",
    "id": "R4",
    "ident": "RFC 5545",
    "kind": "standard",
    "title": "Internet Calendaring and Scheduling Core Object Specification (iCalendar)",
    "url": "https://www.rfc-editor.org/rfc/rfc5545"
  }
]
```

<!-- end -->
