---
id: "PKG-notifications"
title: "Notifications"
parent: "PKG"
order: 11
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "email, SMS, WhatsApp, in-app, push: policy-driven channel, timing, sender and template resolution per event type and scope, preferences, escalation, digests and delivery evidence"
links: []
rev: 3
syncHash: "84af5edb4ab6e563"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.11 Notifications

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> email, SMS, WhatsApp, in-app, push: policy-driven channel, timing, sender and template resolution per event type and scope, preferences, escalation, digests and delivery evidence

<!-- section:purpose -->
## Purpose and scope

`@nomology/notifications` delivers messages to people across email, SMS, WhatsApp, in-app and push, on behalf of any app, workflow or job. Callers say **what** happened and **to whom** (by user or party ID); the package resolves recipients, applies the published **notification policy** for the event type and each recipient's preferences, picks channels, sender identity and the template per tenant and locale, sends through regional providers, escalates when configured, and records delivery evidence (provider message IDs, delivery receipts, bounces, opens where lawful).

Notices with legal effect (service of a notice of arbitration, procedural orders, awards) use class `legal_service`: they bypass opt-outs, quiet hours, suppression lists and budgets, are sent on every channel the case's service rules require, and their delivery evidence feeds [[DOM-service-of-notices-and-proof]].

Children and related nodes:

| Node | Owns |
|---|---|
| [[PKG-notification-policies]] | Tenant-administered policy per event type and scope: channels (default, allowed, mandatory), quiet hours, digests, escalation, sender, template, evidence level; admin console and API |
| [[PKG-notification-preferences]] | The rule for applying each recipient's own choices |
| [[PKG-notification-sender-identity]] | Email domains (SPF, DKIM, DMARC), SMS headers and registrations, WhatsApp numbers, verification and fallback |
| [[PKG-notification-copy]] | Wording standards per channel |
| [[PKG-settings-notifications]] | Settings catalogue for this package |

**Does not:** decide *when* to notify (workflows and automation rules do); write the wording ([[PKG-notification-copy]], templates in [[PKG-document-and-notification]]); manage provider accounts (connections in [[INT-connections-admin]], adapters in [[INT-messaging-providers]]); store message bodies beyond the evidence retention period.

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Notification | Class |
|---|---|---|
| Service-of-notices workflow | Notice of arbitration to respondent by email + SMS + WhatsApp (where allowed) with evidence | `legal_service` |
| Hearing reminder workflow | Reminder to neutral and parties; escalation to tribunal secretary | `reminder` |
| Filing Server Action (via outbox) | "Filing received" to the filer; "New filing" to the other side after exchange | `transactional` |
| Automation rules ([[WF-automation-rules]]) | "Send notification" actions configured by tenants | per event type |
| Authentication | OTP, magic link, new-device alert | `auth` |
| Thresholds ([[PKG-thresholds-and-alert]]) | Deadline approaching alerts to case managers | `transactional` |
| Billing | Invoice issued, payment received, overdue reminders | `transactional` / `reminder` |
| Integrations admin | Connection failing, credential expiring, webhook endpoint disabled | `transactional` to admins |
| Digest job (BullMQ `notify-digest:{region}`) | Daily or weekly activity digest per user | `digest` |
| Tenant admin console | Policy preview (`resolvePlan`), delivery search, evidence export | — |

<!-- section:api -->
## Public API

```ts
// packages/notifications/src/index.ts (server-only)
export type NotificationClass = 'legal_service' | 'auth' | 'transactional' | 'reminder' | 'digest';
export type Channel = 'email' | 'sms' | 'whatsapp' | 'in_app' | 'push';
export type RecipientRef = { userId: string } | { partyId: string } | { role: TenantRole; caseId: string } | { caseSide: 'claimant' | 'respondent' | 'tribunal'; caseId: string };

export interface NotifyRequest {
  event: EventTypeKey;                       // e.g. 'filing.received'; selects the policy rule and default template
  template?: TemplateKey;                    // override only where the policy allows
  class: NotificationClass;                  // must equal the class fixed for the event type (checked)
  recipients: RecipientRef[];                // max 500; never raw addresses, except legal_service to an unregistered respondent (see addresses)
  addresses?: { email?: string[]; phone?: string[] };   // only for legal_service to parties not yet registered; validated, stored encrypted
  vars: Record<string, unknown>;             // validated against the template's variable schema
  caseId?: string;                           // links evidence to the case timeline; required for legal_service
  unitId?: string;                           // selects unit policy layer; defaults from the case
  channels?: Channel[];                      // only for legal_service (from service rules); otherwise policy + preferences decide
  idempotencyKey: string;                    // required; same key within 7 days => no duplicate send
  notBefore?: Date;                          // scheduling (still respects quiet hours unless the policy bypasses them)
}
export interface NotifyResult {
  notificationId: string;
  policyVersion: string;                     // recorded with each delivery for evidence
  deliveries: { recipient: RecipientRef; channel: Channel; deliveryId: string; status: 'queued' | 'scheduled' | 'held_for_digest'; senderIdentityId?: string }[];
  skipped: { recipient: RecipientRef; channel?: Channel; reason: 'opted_out' | 'not_opted_in' | 'no_channel' | 'walled' | 'no_access' | 'invalid_address' | 'suppressed' | 'budget_reached' | 'event_disabled' }[];
}

export function notify(tx: TenantTx, req: NotifyRequest): Promise<NotifyResult>;        // writes rows + outbox in caller's transaction
export function resolvePlan(tx: TenantTx, req: NotifyRequest): Promise<ResolvedPlan>;  // dry run used by the admin preview and the policy simulator
export function getDeliveryEvidence(tx: TenantTx, notificationId: string): Promise<DeliveryEvidence[]>;   // for proof of service
export function exportEvidence(tx: TenantTx, p: { caseId: string; noticeId?: string }): Promise<{ pdfDocumentVersionId: string; jsonObjectKey: string }>;
export function markRead(tx: TenantTx, inAppId: string): Promise<void>;                // cancels pending escalation steps
export function acknowledge(tx: TenantTx, inAppId: string): Promise<void>;
export function listInApp(tx: TenantTx, q: { cursor?: string; unreadOnly?: boolean }): Promise<Page<InAppItem>>;

/** Provider webhooks (delivery receipts, bounces, replies/STOP) are received by INT-messaging-providers and passed here */
export function recordProviderEvent(evt: ProviderEvent): Promise<void>;

/** Temporal Activity wrapper */
export async function sendNotification(req: NotifyRequest): Promise<NotifyResult>;
```

**Resolution pipeline** (inside `notify`, in order): load the published policy rule for `event` across scopes ([[PKG-notification-policies]]) → resolve recipients by role or side and check authorisation and ethical walls at send time → per recipient, compute channels = policy default ∪ user additions − user removals (never removing mandatory) ∩ enabled channels ∩ opt-in requirements ([[PKG-notification-preferences]]) → apply suppression, budgets (never for `legal_service` / `auth`) → timing: immediate, quiet-hours deferral, or held for digest → pick sender identity ([[PKG-notification-sender-identity]]) and template version per locale → write `notification`, `notification_delivery` rows and outbox jobs → schedule escalation steps on `notify-escalation:{region}`.

Delivery state per channel: `queued → sent → delivered | bounced | failed | expired`, plus `read` for in-app and `opened` for email only where the tenant has enabled tracking (never for `auth` and `legal_service`).

<!-- section:usage -->
## Usage examples

```ts
// In a Temporal Activity (service of notice)
await sendNotification({
  event: 'notice.arbitration.served', class: 'legal_service', caseId,
  recipients: [{ caseSide: 'respondent', caseId }],
  channels: serviceRules.channels,                  // from rules engine decision, e.g. ['email','sms','whatsapp']
  vars: { caseRef, claimantName, responseDueLocal, portalLink },
  idempotencyKey: `${tenantId}:service:${caseId}:notice-of-arbitration`,
});

// Admin preview: what would happen for this event and recipient right now?
const plan = await resolvePlan(tx, { event: 'hearing.rescheduled', class: 'transactional', caseId,
  recipients: [{ role: 'claimant_counsel', caseId }], vars: sampleVars, idempotencyKey: 'preview' });
// plan.perRecipient[0] => { channels: ['email','sms'], mandatory: ['email','sms'], timing: 'immediate', sender: 'snd_…', policyVersion: 'np_…@7' }
```

<!-- section:tenant -->
## Tenant context

- `notify` runs inside the caller's `withTenant` transaction: policy, recipient resolution, preferences, templates, sender identities and delivery rows are all tenant-scoped under forced RLS; the outbox job carries the tenant context to the BullMQ send workers.
- Recipients are resolved at send time (not at enqueue time) and each is checked with `authz` for the notification's resource (for example a filing notification is only sent to people who can see that filing; walled users are skipped as `walled`).
- Unit policy layers apply when the case or request belongs to a unit; a unit can only tighten or add to tenant rules where the tenant allowed it.
- Sender identity is per tenant or unit ([[PKG-notification-sender-identity]]); provider credentials are per region and per connection, resolved through the secrets client.

<!-- section:config -->
## Configuration

All tunable behaviour is read through [[PKG-settings]] using the keys in [[PKG-settings-notifications]] (channels, mandatory and urgent events, quiet hours, digests, escalation, senders, template locales, evidence levels, suppression, admin alerts). Per-event-type rules are versioned policy artefacts in [[PKG-notification-policies]]. Users set their own channel opt-ins, digest frequency and quiet hours through [[PKG-settings-personal]]. Package constants: maximum 500 recipients per call; idempotency window 7 days; escalation steps at most 5 per rule.

<!-- section:adapters -->
## Providers and extension points

`ChannelAdapter { send(msg: OutboundMessage): Promise<{ providerMessageId: string }>; parseEvent(raw): ProviderEvent }` implemented per provider in [[INT-messaging-providers]] and reached through connections ([[INT-connections-admin]]), so a tenant can use the platform-managed provider or its own account. In-app uses our own table plus server-sent events; push uses Web Push [R1] (VAPID) for the PWA. Email is sent on two streams with separate subdomains: `notices` (legal_service, auth, transactional) and `bulk` (digests, reminders), so complaints about bulk mail cannot affect notice delivery [R2]. Adding a channel = new adapter + template kind + policy channel + settings keys; callers do not change.

<!-- section:errors -->
## Error model

| Error | Retryable | Caller action |
|---|---|---|
| `TemplateNotFoundError`, `TemplateVariableError` | No | Fix configuration; workflow fails the step to a human task |
| `NotificationPolicyMissingError` (no published rule for the event type at any scope) | No | Platform baseline always exists for platform event types; for tenant custom events, publish a policy |
| `NotificationClassMismatchError` | No | Bug: caller passed a class different from the event type's fixed class |
| Provider 5xx / timeout | Yes: BullMQ retries with exponential backoff (5 attempts over ~1 h), then `failed` and fallback channel if class allows | — |
| Hard bounce / invalid number | No | `bounced`; recipient's address suppressed; for `legal_service`, secretariat human task to use alternative service |
| `ConnectorPolicyViolationError` (template content not allowed for the channel's connector) | No | Fix the template; prevented at publish in normal operation |
| Idempotency key reuse with different payload | No | `IdempotencyConflictError`: bug |
| Quiet hours, digest hold | n/a | Deferred or held (not an error) |

<!-- section:nfr -->
## Performance and limits

- `notify()` p95 ≤ 50 ms (DB writes only; sending is asynchronous).
- Send latency (queued → handed to provider) p95 ≤ 30 s for `auth`, ≤ 2 min for others.
- Throughput ≥ 50 messages/s per region (bulk notices for high-volume ODR tenants), provider rate limits respected per sender.
- Max 500 recipients per call; bulk sends use multiple calls with distinct idempotency keys.

<!-- section:versioning -->
## Versioning and compatibility

Semver. Adding a class or channel is minor; changing how `legal_service` bypasses preferences is major and needs legal sign-off.

<!-- section:testing -->
## Test contract

- Contract tests per adapter against provider sandboxes.
- Idempotency: same key twice → one delivery per recipient and channel.
- Preference matrix tests per class (see [[PKG-notification-preferences]]).
- Authorisation at send time: removed counsel and walled users are skipped.
- Evidence: provider receipts attach to the right delivery; legal_service evidence query returns message IDs, timestamps and statuses.

<!-- section:questions -->
## Open questions

- [ ] Is email open tracking acceptable as supporting evidence of service for any tenant, given privacy concerns? Default off (`notify.evidence.email_open_counts_as_evidence`); legal to advise per jurisdiction.
- [ ] Which channels are valid for legal service per tenant type (email, SMS, WhatsApp)? Encoded per tenant in service rules; legal to confirm.
- [ ] Shared platform WhatsApp number per region vs per-tenant numbers (setting `notify.sender.whatsapp.number_mode`; default shared).
- [ ] Do we need a print-and-post channel for service on parties without electronic contact?
- [ ] Should a notification centre in each persona shell show mandatory-notice explanations inline? Proposed: yes ([[PKG-personalisation]]).

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

All rows are tenant-owned under forced RLS; policies, sender identities, templates and suppressions are per tenant (and unit); recipients are resolved and authorised at send time inside the tenant; worker jobs carry tenant context.

<!-- check:data-protection -->
### Personal data handling

Callers pass IDs, not addresses (except legal service to unregistered parties, where addresses are encrypted). Message bodies are stored only as long as the evidence retention for their class; telemetry records template keys and delivery IDs, never bodies or addresses. Providers receiving personal data are listed as sub-processors per region.

<!-- check:residency -->
### Region awareness

Providers and credentials are configured per region; a tenant pinned to India sends through India-region providers where available. Where a provider processes data outside the region (for example a global WhatsApp provider), it must be recorded in [[SEC-vendor-sub-processor-management]] and the transfer approved by legal.

<!-- check:audit -->
### Audit events

Every `legal_service` notification and its delivery evidence are audited and linked to the case with policy version, template version and sender identity; policy and settings changes are audited as configuration (`admin.notify.policy_published`, `admin.settings.published`); preference changes that affect legal notices are audited; sends to raw addresses are audited with the address hash; evidence exports are audited (`admin.notify.evidence_exported`).

<!-- check:observability -->
### Observability

Metrics by region, channel, class and provider: queued, sent, delivered, bounced, failed; send latency histograms. Alerts: bounce rate > 5% per tenant per hour, provider error rate > 10% for 10 minutes, `auth` send latency p95 > 60 s.

<!-- check:resilience -->
### Failure behaviour

`notify()` writes rows and outbox entries in the caller's transaction, so a send cannot happen without its record and vice versa; send workers are idempotent per delivery ID; retries are in BullMQ only; channel fallback is defined per class.

<!-- citations -->
## Citations

```json
[
  {
    "body": "IETF",
    "id": "R1",
    "ident": "RFC 8030",
    "kind": "standard",
    "title": "Generic Event Delivery Using HTTP Push",
    "url": "https://www.rfc-editor.org/rfc/rfc8030"
  },
  {
    "excerpt": "Transactional and broadcast email are sent through separate message streams so that bulk mail cannot harm the delivery of transactional mail.",
    "id": "R2",
    "kind": "vendor",
    "publisher": "Postmark",
    "retrieved": "2026-10-28",
    "title": "Message Streams",
    "url": "https://postmarkapp.com/message-streams"
  }
]
```

<!-- end -->
