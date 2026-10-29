---
id: "PKG-notification-sender-identity"
title: "Notification sender identity and domain authentication"
parent: "PKG-notifications"
order: 4
type: "feature"
template: "integration"
status: "draft"
owner: null
indicative: false
summary: "Sender identities per tenant and unit: email domains with SPF, DKIM and DMARC verification, India DLT headers and templates, Singapore and US SMS registrations, WhatsApp numbers; verification jobs, monitoring and recorded fallbacks"
links: []
rev: 1
syncHash: "7dff0d7b28dca74a"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.11.4 Notification sender identity and domain authentication

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Sender identities per tenant and unit: email domains with SPF, DKIM and DMARC verification, India DLT headers and templates, Singapore and US SMS registrations, WhatsApp numbers; verification jobs, monitoring and recorded fallbacks

<!-- section:purpose -->
## Purpose and use cases

Every message the platform sends on a tenant's behalf must come from a sender the recipient can trust and the provider will accept: an email domain authenticated with SPF, DKIM and DMARC, an SMS header or sender ID registered where the country requires it, and a WhatsApp business number with an approved display name. This node specifies how sender identities are set up, verified, monitored and assigned, per tenant and optionally per unit, and what happens when verification fails. It was split out of [[PKG-notification-policies]] because it is a multi-step, provider-facing process with its own failure modes.

Use cases:
1. An arbitral institution sends notices from `notices@arbitration.example.org` after publishing DNS records the console generates; DMARC alignment is checked daily.
2. A SEBI ODR institution sends SMS under its own DLT-registered header with registered content templates; the console blocks a template whose ID is missing.
3. A CORD tenant without its own domain sends from the platform domain (`<tenant-slug>@notify.<platform-domain>`) with its own display name.
4. A Singapore office (unit) uses its own Singapore sender ID while the rest of the tenant uses the India header.
5. A tenant moves its WhatsApp traffic from the shared regional platform number to its own number.

Out of scope: the notification policy that selects a sender ([[PKG-notification-policies]]), provider adapters ([[INT-messaging-providers]]), message wording ([[PKG-notification-copy]]), tenant custom web domains ([[INF-networking]], [[PKG-domain-verification]]).

<!-- section:party -->
## External party and ownership

| Item | Value |
|---|---|
| External parties | Email sending provider per region; SMS aggregator per region; WhatsApp Business Platform provider; the tenant's DNS host (the tenant publishes records); India DLT platforms operated by telecom access providers; US campaign registration through the SMS provider |
| Owner | Platform engineering (notifications) with Nomology ops for registrations Nomology makes as principal entity |
| Tenant roles | `integration_admin` or `tenant_admin` manage sender identities; `content_admin` sees registration status of templates; `unit_admin` may assign a verified unit sender where allowed |
| Environments | Sandbox senders use provider sandboxes and a platform test domain (`<tenant-slug>.sandbox-notify.<platform-domain>`); production senders are verified in production only |

**Sender identity types**

| Type | Verified by | Owner of registration |
|---|---|---|
| `email_domain` (tenant domain) | DNS: SPF include or CNAMEs, DKIM selector CNAMEs, custom return-path subdomain, DMARC record present [R1][R2][R3][R5] | Tenant (DNS); provider (keys) |
| `email_platform` | Pre-verified platform domain per region, tenant display name only | Nomology |
| `sms_header_in` | DLT principal entity, header and content templates registered; URLs, APKs and call-back numbers in templates whitelisted [R6] | Tenant or Nomology as principal entity (assumption, legal to confirm per tenant) |
| `sms_sender_sg` | Singapore SMS Sender ID Registry registration (assumption: required for alphanumeric sender IDs; to confirm with the provider and legal) | Tenant or Nomology |
| `sms_number_us` | 10DLC brand and campaign registration or toll-free verification through the provider | Nomology or tenant |
| `whatsapp_number` | Provider business verification, display name approval, message templates in utility or authentication categories | Nomology (shared regional number) or tenant |

<!-- section:flows -->
## Data flows

| # | Flow | Direction | Trigger | Mode | Runs in |
|---|---|---|---|---|---|
| 1 | Add email domain | platform → provider | Admin enters domain at `/admin/notifications/senders/new` | sync create at provider, returns DNS records | Server Action → `notify.sender.createEmailDomain` |
| 2 | Verify DNS | platform → DNS, provider | Admin clicks "Verify", then every 6 h for 72 h, then daily | async | BullMQ `notify-sender-verify:{region}` |
| 3 | Monitor alignment | platform → DNS, provider | Daily; on DMARC aggregate report failures if the tenant routes reports to us (optional) | async | Same queue |
| 4 | Register SMS header and templates (India) | tenant / Nomology ↔ DLT platform | Onboarding; new template | manual registration with recorded IDs; status sync where the provider has an API | Human task + `notify-template-sync:{region}` |
| 5 | Register WhatsApp templates | platform → provider | Template publish ([[PKG-document-and-notification]]) | async, `pending_provider_approval` | `notify-template-sync:{region}` |
| 6 | Assign sender | internal | Admin sets default sender per channel at tenant or unit; policy may override per event type | sync | Settings keys `notify.sender.*` |
| 7 | Fallback on failure | internal | Verification fails or provider suspends a sender | async | Health job flips status; policy uses fallback |
| 8 | Retire sender | platform → provider | Admin removes, tenant offboarding | async | Provider deletion; DNS records reported as removable |

**States**: `pending_dns` → `verifying` → `verified` → (`degraded` when DMARC or alignment checks fail but DKIM still passes) → `failed` → `retired`. Messaging providers may also report `suspended` (for example spam complaints).

**Fallback rules**
- Email from a tenant domain that is `failed` or `suspended`: send from the regional platform domain with the tenant's display name and a reply-to the tenant chose; alert the owner; record `sender_fallback = true` on each delivery so evidence shows the actual sender.
- SMS header unusable: for `legal_service` and `auth`, send through the platform-managed header if the tenant allowed fallback (`notify.sender.sms.fallback_to_platform`); otherwise the delivery fails to the next channel in the service plan.
- WhatsApp number suspended: WhatsApp is skipped; the policy's next channel applies.

<!-- section:mapping -->
## Data mapping

**`notification_sender_identity`** (tenant-owned, forced RLS)

| Field | Type | Notes |
|---|---|---|
| `id` | uuid (`snd_…`) | |
| `tenant_id`, `unit_id` | uuid, uuid null | unit null means tenant-wide |
| `type` | enum above | |
| `channel` | `email` / `sms` / `whatsapp` | |
| `value` | text | domain, header, sender ID, E.164 number |
| `display_name` | text ≤ 64 | email From name or WhatsApp display name |
| `reply_to` | text null | must be a mailbox on a verified domain or the tenant's support address |
| `stream` | `notices` / `bulk` | email only; digests and reminders use `bulk` on a separate subdomain so complaints do not affect notices [R9] |
| `provider_connection_id` | uuid | the connection that sends ([[INT-connections-admin]]) |
| `provider_ref` | text | provider's domain, sender or number ID |
| `dns_records` | jsonb | expected records with host, type, value, status per record |
| `registration` | jsonb | DLT entity ID, header ID, template IDs and URL whitelist status; SSIR reference; 10DLC campaign ID; WhatsApp business account and number ID |
| `status`, `status_reason`, `last_checked_at` | | |
| `verified_at`, `verified_by` | | |

**Email headers set by the platform**: `From` (identity + display name), `Reply-To`, `Return-Path` on the custom bounce subdomain, `List-Unsubscribe` and `List-Unsubscribe-Post: List-Unsubscribe=One-Click` for `digest` and `reminder` only [R8], `X-Message-Ref: {tenantId}:{messageId}`. No personal data in custom headers.

<!-- section:auth -->
## Authentication and secrets

- DKIM keys are generated and held by the email provider (2048-bit where supported) and published through CNAMEs the tenant adds, so the tenant never handles private keys [R5]. If a provider requires a TXT key, the console shows it and key rotation is a runbook every 12 months.
- DMARC: the platform requires a DMARC record to exist on any custom sending domain (at least `p=none`), and recommends `quarantine` or `reject` once aggregate reports show alignment; large mailbox providers require SPF or DKIM for all senders and SPF, DKIM and DMARC with alignment for bulk senders [R4]. The console shows the tenant's current policy and alignment result.
- SPF: the domain's SPF record must include the provider and stay within the 10-DNS-lookup limit [R1]; the checker reports the lookup count.
- Registrations with telecom and messaging platforms are recorded with who registered, under which entity and when; credentials for those portals are not stored in the platform.
- WhatsApp opt-in records name the tenant as the business the recipient agreed to hear from [R7]; a move from the shared platform number to the tenant's own number requires fresh opt-in only if the provider's policy requires it (to be confirmed with the provider).
- Changing a tenant's default sender for notices is maker-checker and audited (`admin.notify.sender_changed`).

<!-- section:errors -->
## Errors, retries and idempotency

| Error / condition | Detection | Effect | Admin action |
|---|---|---|---|
| DNS record missing or wrong | Verify job | `pending_dns` or `failed`; record-level status in console | Fix DNS, re-verify |
| DMARC record absent | Verify job | `degraded`; bulk stream blocked, notices fall back to platform domain | Publish DMARC |
| DKIM fails | Verify job, provider events | `failed`, fallback to platform domain | Fix CNAMEs |
| Provider suspends sender (complaints) | Provider webhook | `suspended`; alert; fallback per rules | Investigate complaint source |
| DLT template ID missing for India SMS | Template publish | Publish blocked (`notify-template-dlt-missing`) | Register template, enter ID |
| URL in SMS template not whitelisted | Template publish (whitelist list stored in `registration`) | Publish blocked [R6] | Whitelist the URL with the DLT platform |
| WhatsApp template rejected | Provider status sync | Template stays `provider_rejected`; policy skips WhatsApp | Edit and resubmit |
| Hard bounce rate > 5% per hour on a sender | Metrics | Bulk stream paused for the sender; notices continue | Review list quality |

Verification jobs are idempotent per (sender, day); status changes are forward-only within a check run and emitted as `notify.sender.status_changed`.

<!-- section:limits -->
## Rate limits and SLAs

- Email domains per tenant: 5 (default), sender identities per unit: 1 per channel.
- Verification polling: every 6 hours for the first 72 hours, then daily; manual verify limited to once per minute.
- Provider sending limits per sender and per region are respected by the BullMQ limiter on `notifications:{region}`; bulk stream sends are throttled first so notices keep their latency targets ([[PKG-notifications#nfr]]).

<!-- section:residency -->
## Data transfer and compliance

Sender identities and verification results are stored in the tenant's region. DNS lookups are public. Registrations at telecom platforms contain business details (entity name, header, template text), not case data. WhatsApp display names and template text are processed by the provider outside the region; they must not contain personal or case data, which the template checks enforce ([[INT-connector-data-policies#policy]]).

<!-- section:testing -->
## Sandbox and testing

- Unit tests for the DNS checker against recorded zone fixtures (missing record, wrong CNAME target, SPF over 10 lookups, DMARC absent, DMARC `p=none`, aligned and unaligned).
- Sandbox: every tenant sandbox gets a pre-verified sandbox domain so templates and policies can be tested end to end without DNS changes.
- Fallback tests: a failed tenant domain switches to the platform domain and `sender_fallback = true` appears in the delivery evidence.
- Template publish tests: India SMS without DLT ID, SMS with a non-whitelisted URL, WhatsApp template awaiting approval.

<!-- section:questions -->
## Open questions

- [ ] Who is the DLT principal entity for each India tenant type: the tenant, or NTPL on its behalf? Legal to confirm; affects who registers headers and templates. (Legal)
- [ ] Confirm Singapore sender ID registration requirements and the US registration path with the chosen providers. (CTO office)
- [ ] Should the platform receive DMARC aggregate reports for tenant domains (needs a reporting mailbox and parser), or only check DNS? Proposed: DNS checks only in Phase 3. (Platform engineering)
- [ ] BIMI (brand logos in inboxes) for institutions that ask for it: later phase? (Product)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant separation at the provider

Sender identities are tenant-owned rows under forced RLS, optionally narrowed to a unit; the provider-side domain or number ID is stored per tenant and every send carries `X-Message-Ref: {tenantId}:{messageId}`. The shared platform domain and WhatsApp number are used only with the tenant's display name, and replies to platform-domain mail route to the tenant's chosen reply-to address.

<!-- check:security -->
### Security

Tenants never handle DKIM private keys (CNAME delegation [R5]); DMARC, SPF and DKIM are checked daily [R1][R2][R3]; changes to the notice sender are maker-checker; portal credentials for DLT and messaging platforms are not stored in the platform.

<!-- check:resilience -->
### Failure handling and degradation

Failures change sender status and trigger explicit fallbacks that are recorded on each delivery; the bulk stream is paused before notices are affected; legal-service fallback continues through the service channel plan.

<!-- check:audit -->
### Audit and evidence

Every sender create, verify, status change, assignment and fallback is audited; delivery evidence records the actual sender used, so proof of service shows exactly who the notice came from.

<!-- check:observability -->
### Observability

Per sender: verification status, bounce and complaint rates, fallback count, template approval status; alerts at status change and bounce rate over 5% per hour, shown at `/admin/notifications/senders`.

<!-- check:testing -->
### Testing

DNS checker fixtures, sandbox pre-verified domains, fallback evidence tests and template registration checks run in CI.

<!-- citations -->
## Citations

```json
[
  {
    "body": "IETF",
    "id": "R1",
    "ident": "RFC 7208",
    "kind": "standard",
    "title": "Sender Policy Framework (SPF) for Authorizing Use of Domains in Email",
    "url": "https://www.rfc-editor.org/rfc/rfc7208"
  },
  {
    "body": "IETF",
    "id": "R2",
    "ident": "RFC 6376",
    "kind": "standard",
    "title": "DomainKeys Identified Mail (DKIM) Signatures",
    "url": "https://www.rfc-editor.org/rfc/rfc6376"
  },
  {
    "body": "IETF",
    "id": "R3",
    "ident": "RFC 7489",
    "kind": "standard",
    "title": "Domain-based Message Authentication, Reporting, and Conformance (DMARC)",
    "url": "https://www.rfc-editor.org/rfc/rfc7489"
  },
  {
    "excerpt": "Senders must authenticate with SPF or DKIM; bulk senders need SPF, DKIM and DMARC, alignment, and one-click unsubscribe for marketing messages.",
    "id": "R4",
    "kind": "vendor",
    "publisher": "Google",
    "retrieved": "2026-10-28",
    "title": "Email sender guidelines (Gmail)",
    "url": "https://support.google.com/mail/answer/81126"
  },
  {
    "excerpt": "DNS records (CNAMEs under automated security) authorise the sending service for SPF and DKIM, with a custom return-path subdomain and separate link branding.",
    "id": "R5",
    "kind": "vendor",
    "publisher": "Twilio SendGrid",
    "retrieved": "2026-10-28",
    "title": "Configure domain authentication",
    "url": "https://www.twilio.com/docs/sendgrid/ui/account-and-settings/how-to-set-up-domain-authentication"
  },
  {
    "excerpt": "From 1 September 2024 messages containing URLs, APKs, OTT links or call-back numbers that are not whitelisted are not permitted; a content template may not be linked to more than one header.",
    "id": "R6",
    "issuer": "Telecom Regulatory Authority of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "title": "TRAI Direction of 20 August 2024 under the Telecom Commercial Communications Customer Preference Regulations, 2018",
    "url": "https://trai.gov.in/sites/default/files/Direction_20082024.pdf"
  },
  {
    "excerpt": "Opt-in must state that the person agrees to receive WhatsApp messages and name the business; opt-out requests for message categories must be honoured.",
    "id": "R7",
    "kind": "vendor",
    "publisher": "Meta",
    "retrieved": "2026-10-28",
    "title": "WhatsApp Business Platform: Get opt-in for WhatsApp",
    "url": "https://developers.facebook.com/docs/whatsapp/overview/getting-opt-in"
  },
  {
    "body": "IETF",
    "id": "R8",
    "ident": "RFC 8058",
    "kind": "standard",
    "title": "Signaling One-Click Functionality for List Email Headers",
    "url": "https://www.rfc-editor.org/rfc/rfc8058"
  },
  {
    "excerpt": "Transactional and broadcast email are sent through separate message streams so that bulk mail cannot harm the delivery of transactional mail.",
    "id": "R9",
    "kind": "vendor",
    "publisher": "Postmark",
    "retrieved": "2026-10-28",
    "title": "Message Streams",
    "url": "https://postmarkapp.com/message-streams"
  }
]
```

<!-- end -->
