---
id: "INT-messaging-providers"
title: "Messaging providers"
parent: "INT-common-integrations"
order: 4
type: "feature"
template: "integration"
status: "draft"
owner: null
indicative: false
summary: "Email, SMS and WhatsApp provider integrations per region (sender identity, delivery receipts, opt-out handling)"
links: []
rev: 2
syncHash: "64d7f7069dcbd34c"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 9.2.4 Messaging providers

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Email, SMS and WhatsApp provider integrations per region (sender identity, delivery receipts, opt-out handling)

<!-- section:purpose -->
## Purpose and use cases

Sends email, SMS and WhatsApp messages produced by [[PKG-notifications]] and brings back delivery receipts, bounces, complaints and opt-outs. Delivery evidence feeds electronic service of notices ([[DOM-service-of-notices-and-proof]]). Use cases: notices and orders (legal service), deadline reminders, hearing invitations with `.ics`, OTPs and magic links ([[PKG-email-password-magic-link-otp]]), payment links, and short WhatsApp nudges where a party has opted in.

<!-- section:party -->
## External party and ownership

| Channel | India | Singapore | US |
|---|---|---|---|
| Email | Cloud email service in an India region | Same service in a Singapore region | Same service in a US region |
| SMS | DLT-registered SMS aggregator (to select) | Provider supporting Singapore sender ID registration (to select) | Provider with 10DLC / toll-free registration (to select) |
| WhatsApp | WhatsApp Business Platform via Meta or a business solution provider (to select) | Same | Same |

Sender identity per tenant: email from the tenant's verified domain (SPF, DKIM, DMARC set up during onboarding, [[MT-tenant-lifecycle]]) or from a platform domain with the tenant's name; SMS sender IDs and templates registered per tenant where the tenant is the principal entity (assumption: for Indian DLT, the tenant or Nomology registers as principal entity; legal to confirm).

<!-- section:flows -->
## Data flows

```
PKG-notifications renders message (template version, locale)
  └─▶ BullMQ queue `notifications:{region}` job (jobId = messageId)
        └─ MessagingProvider.send(channel, to, content, idempotencyKey=messageId)
             └─ provider message ID stored on `notification_delivery`
Provider webhooks (delivered, bounced, complained, read, failed, STOP)
  └─▶ /api/integrations/webhooks/{provider}/{connectionId} ─▶ inbox ─▶ update delivery status (forward-only)
        └─ for legal service: emit notice.delivery_updated to DOM-service-of-notices workflow
```
Fallback order for legal service notices is set by the service workflow (for example email, then SMS, then WhatsApp, then a secretariat task for physical service).

<!-- section:mapping -->
## Data mapping

| Our field | Email | SMS | WhatsApp | Personal data |
|---|---|---|---|---|
| recipient | address | E.164 number | E.164 number | yes |
| sender | tenant domain address | sender ID / number | business number | no |
| content | subject + HTML + text | DLT-registered template with variables (India) | pre-approved template with variables | may be |
| message ID | `X-Message-Ref: {tenantId}:{messageId}` header | client reference | client reference | no |
| receipt | delivery / bounce / complaint events | DLR status | sent / delivered / read / failed | metadata |

Content rules: SMS and WhatsApp never contain case content, party names of the other side, amounts or document text; they say a notice is available and link to the platform (lock-screen safe, [[PKG-notification-copy]]). Email may contain a summary only where the template is approved for it.

<!-- section:auth -->
## Authentication and secrets

Provider credentials per region in the regional secrets manager; email sending via API with IAM role (no static SMTP passwords) where the provider supports it; webhooks verified by signature (or by signed notification messages for cloud email); WhatsApp app secret verifies payload signatures.

<!-- section:errors -->
## Errors, retries and idempotency

- Retry transient errors with backoff up to 24 h for email, 2 h for SMS / WhatsApp; then mark `failed` and trigger fallback.
- Hard bounce: mark the address undeliverable for that tenant, notify the secretariat if it is a party's service address.
- Complaint / STOP / opt-out: record per recipient and channel; non-essential messages stop; legal service notices continue by email or another channel per [[PKG-notification-preferences]].
- Duplicate receipts: inbox de-dupe; status transitions forward-only (`queued → sent → delivered → read`; `failed`/`bounced` terminal).

<!-- section:limits -->
## Rate limits and SLAs

Planned volumes (Year 1, proposed): 1.5 M emails per month, 400 k SMS per month, WhatsApp 100 k per month. Per-tenant send rate limits to protect sender reputation (default 20 emails per second per tenant domain). SEBI ODR bulk reminder bursts are spread by BullMQ rate limiter.

<!-- section:residency -->
## Data transfer and compliance

Email and SMS use providers in the tenant's region. WhatsApp messages are processed by Meta outside our region; therefore WhatsApp is opt-in per recipient, content is limited to non-confidential prompts, and it is off by default per tenant. Message content stored by us stays in region.

<!-- section:testing -->
## Sandbox and testing

Sandbox / test mode per provider; non-production environments route all messages to a capture inbox (no real recipients) enforced in the adapter; seed recipient allow-list for UAT. Contract tests on receipt webhook parsing.

<!-- section:questions -->
## Open questions

- [ ] Confirm India DLT requirements and who registers as principal entity (Nomology or each tenant) for SMS.
- [ ] Is WhatsApp acceptable as a service channel under any institution's rules, or only as a reminder?
- [ ] Select SMS and WhatsApp providers per region.
- [ ] Do we need a secondary email provider per region for failover?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant separation at the provider

Each message carries `{tenantId}:{messageId}`; receipts are resolved by connection and reference to one tenant. Sender domains and SMS templates are per tenant. Opt-outs are stored per tenant and recipient.

<!-- check:residency -->
### Data transfer and residency

Email and SMS in region; WhatsApp is opt-in, off by default, and carries no confidential content because Meta processes it outside the region.

<!-- check:audit -->
### Audit and evidence

For legal service, the delivery record (provider message ID, timestamps of sent / delivered / bounced, provider raw receipt) is stored with the notice as proof of delivery ([[DOM-service-of-notices-and-proof]]).

<!-- check:testing -->
### Testing

Non-production delivery goes only to a capture inbox, enforced in the adapter; production credentials are unreadable outside production.

<!-- end -->
