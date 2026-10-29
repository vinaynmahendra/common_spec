---
id: "PKG-notification-policies"
title: "Notification policy administration"
parent: "PKG-notifications"
order: 3
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Tenant-administered notification policies per event type and scope: channels (default, allowed, mandatory), quiet hours, digests, escalation, sender identity, templates and evidence level, with legal-service and sign-in notices protected"
links: []
rev: 1
syncHash: "497f9a7bac0cd29e"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.11.3 Notification policy administration

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Tenant-administered notification policies per event type and scope: channels (default, allowed, mandatory), quiet hours, digests, escalation, sender identity, templates and evidence level, with legal-service and sign-in notices protected

<!-- section:statement -->
## Statement

When a notification is requested, the Notifications package shall determine its recipients' channels, timing (quiet hours, digest or immediate), escalation, sender identity, template and evidence level by resolving the **published notification policy** for that event type across the `platform`, `region`, `offering`, `tenant`, `unit` and `case_type` scopes and then applying each recipient's own preferences, and shall not let any lower scope or any user preference suppress a notification of class `legal_service` or `auth`, or a channel that a higher scope has marked mandatory for that event type.

<!-- section:rationale -->
## Rationale and source

Tenants differ sharply in how they must notify people. A SEBI ODR institution sends high volumes of SMS reminders to investors in several languages; an arbitral institution notifies counsel by email and expects formal records of every notice; a court programme may require that every hearing change reaches a party by two channels. These differences must be configuration, not code, and must be administered by the tenant within platform bounds. At the same time, the platform must protect three things no tenant setting may break: legal service of notices ([[DOM-service-of-notices-and-proof]]), sign-in codes ([[PKG-email-password-magic-link-otp]]), and people's lawful choices about optional messages, where privacy law expects consent to be as easy to withdraw as to give [R2][R3] and WhatsApp requires an opt-in that names the business [R4].

Pattern borrowed from: notification preference sets that merge recipient, tenant and environment defaults, with workflows that can be marked as overriding recipient preferences, in Knock [R1]; and separate sending streams for transactional and bulk mail so that digests cannot harm the delivery of notices, in Postmark [R6].

Source: CTO request for full notification administration (overhaul brief); parent [[PKG-notifications]]; preference rule [[PKG-notification-preferences]]; settings in [[PKG-settings-notifications]].

<!-- section:acceptance -->
## Acceptance criteria

- **Given** the tenant policy for `hearing.rescheduled` lists channels `email, sms` as mandatory, **when** a party who opted out of SMS is notified, **then** both email and SMS deliveries are created and the party's notification centre explains "Your organisation requires SMS for hearing changes".
- **Given** a unit policy for the SEBI ODR desk adds `whatsapp` as an optional channel for `deadline.approaching`, **when** an investor who opted in to WhatsApp is reminded, **then** a WhatsApp delivery is created; **and given** the investor did not opt in, **then** no WhatsApp delivery is created and the skip reason is `not_opted_in`.
- **Given** the platform baseline marks `notice.arbitration.served` as `legal_service`, **when** a tenant admin drafts a policy that removes email for it, **then** publish fails with problem type `notify-policy-mandatory-channel` naming the platform layer.
- **Given** quiet hours 21:00–08:00 for the recipient's time zone, **when** a `reminder` is triggered at 23:00, **then** it is deferred to 08:00; **when** an `auth` OTP is requested at 23:00, **then** it is sent immediately; **when** a tenant-mandated urgent event `hearing.changed_within_24h` with "bypass quiet hours" is triggered at 23:00, **then** it is sent immediately and the delivery is marked `quiet_hours_bypassed` with the policy version.
- **Given** a user chose a daily digest at 08:00, **when** five `transactional` notifications occur during the day, **then** in-app items appear immediately, one digest email is sent at 08:00 local time, and no individual emails are sent; `legal_service` items are never held for the digest.
- **Given** an escalation rule "if `order.issued` is unread in-app after 24 hours, send SMS and notify the case manager", **when** 24 hours pass without a read, **then** an SMS is sent and the case manager receives an in-app task, both linked to the original notification.
- **Given** a custom sending domain for the tenant fails DKIM verification, **when** an email is sent, **then** it is sent from the platform domain with the tenant's display name and the integration admin is alerted ([[PKG-notification-sender-identity]]).
- **Given** a `digest` or `reminder` email, **then** it carries one-click unsubscribe headers [R5]; **given** a `legal_service` or `auth` email, **then** it carries no unsubscribe header and the footer says why.
- **Negative:** **given** a unit admin without `notify.policy:update` on the tenant, **when** they try to edit the tenant-level policy, **then** the request is denied with `403` and the attempt is logged; **given** a policy version is published, **when** a running case later sends a notification, **then** the currently published version applies unless the event type is marked "pinned at case start" (for example statutory notice formats).

<!-- section:verification -->
## Verification method

- **Test**: table-driven resolution tests in `packages/notifications/test/policy-resolution.spec.ts` over scope layers × class × mandatory flags × user opt-ins × quiet hours × digest × escalation, using the same fixtures as [[PKG-notification-preferences]].
- **Test**: publish validation tests for each problem type (`notify-policy-mandatory-channel`, `notify-policy-channel-not-enabled`, `notify-policy-template-missing-locale`, `notify-policy-bounds`).
- **Integration test** with BullMQ and real Postgres: escalation jobs fire, are idempotent per (notification, step), and cancel when the item is read.
- **Inspection**: console review of `/admin/notifications/policies` showing inherited and locked values with their source.
- **Demonstration**: evidence export for a served notice includes policy version, template version, channels, provider message IDs and timestamps.

<!-- section:priority -->
## Priority

Must. Phase 2 for classes, mandatory channels, quiet hours and the tenant policy table for email and in-app; Phase 3 for SMS policies, digests and escalation; Phase 4 for WhatsApp and push policies; Phase 5 for unit and case-type layers and the admin copilot proposing policy drafts ([[APP-admin-copilot]]).

<!-- section:questions -->
## Open questions

- [ ] Which event types besides `legal_service` and `auth` may a tenant mark "bypass quiet hours"? Proposed: only events flagged `urgent_eligible` in the event catalogue (hearing changes within 24 hours, hearing room link changes on the hearing day). (Legal + product)
- [ ] Should policy changes apply to running cases immediately (proposed, except event types pinned at case start) or only to new cases? (Legal)
- [ ] Is an in-app read receipt acceptable as acknowledgement for any rule set's service requirements? (Legal, per rule set)
- [ ] US recipients: confirm whether TCPA consent rules apply to our non-marketing case SMS; assumption: informational messages to numbers provided by the recipient need prior express consent, to be confirmed by legal. (Legal)
- [ ] Split sender identity into its own node: done, see [[PKG-notification-sender-identity]]. Decide whether unit-specific senders are needed in Phase 5. (Product)

<!-- section:notes -->
## Notes

**Policy model.** A notification policy is a versioned configuration artefact (`notification_policy`, `notification_policy_rule`; lifecycle per [[PKG-configuration-lifecycle]]; included in configuration packages per [[PKG-configuration-packages]]). One rule per event type (the template key family from [[INT-webhook-event-catalogue]] and [[OBS-business-events]]), per scope:

| Field | Meaning | Who may set it |
|---|---|---|
| `class` | `legal_service`, `auth`, `transactional`, `reminder`, `digest` | Platform only (fixed per event type) |
| `enabled` | Whether the event notifies at all | Tenant, unit; never false for `legal_service`, `auth` |
| `recipients` | Role keys or case sides to notify (for example `case_manager`, `claimant_counsel`) | Tenant, unit, case type; filtered by authorisation at send time |
| `channels.default` | Ordered channels used unless the user changes them | Tenant, unit, case type |
| `channels.allowed` | Channels the user may add | Tenant, unit |
| `channels.mandatory` | Channels the user cannot remove for this event | Tenant, unit, case type (for `legal_service` the service rules decide) |
| `user_adjustable` | Whether the event appears in the user's preference screen | Tenant |
| `quiet_hours` | `respect` or `bypass` (bypass only for `legal_service`, `auth` and `urgent_eligible` events) | Tenant |
| `digest_eligible` | Whether the event may be bundled into a digest | Tenant (never for `legal_service`, `auth`) |
| `escalation` | Ordered steps: `{after: 'PT24H', unless: 'read'|'acknowledged', action: 'send'|'notify_role', channel?, role?}` | Tenant, unit, case type |
| `sender` | Sender identity ID (email domain, SMS header, WhatsApp number) | Tenant, unit if allowed |
| `template` | Template key; locale coverage checked at publish | Tenant (content admin publishes templates) |
| `evidence_level` | `none`, `standard` (status and provider IDs) or `service_grade` (frozen rendered body, hashes, all receipts) | Platform floor; tenant may raise |
| `pinned_at_case_start` | Policy version captured on the case for this event | Platform or tenant |

**Resolution order.** Platform baseline → region overlay (for example India SMS template registration requirements) → offering → tenant → unit → case type → user preferences ([[PKG-notification-preferences]]) → send-time checks (authorisation, walls, address validity, budgets). Mandatory flags at a higher scope lock the field for lower scopes; the console shows the lock and its source.

**Mandatory notices.** Three levels: (1) `legal_service`: channels from the case's service rules decision table; no opt-out, no quiet hours, evidence `service_grade`; (2) `auth`: delivered on the channel of the chosen sign-in method; (3) tenant-mandated: tenant marks specific channels mandatory for an event; the user may add channels but not remove those. Users see mandatory items greyed in their settings with the reason.

**Digests.** A BullMQ repeatable job `notify-digest:{region}` runs every 15 minutes and builds digests for users whose local digest time has arrived; digests are sent from a separate sending stream and subdomain so complaints about digests cannot affect notice delivery [R6].

**Escalation.** Escalation steps are BullMQ delayed jobs on `notify-escalation:{region}` with `jobId = {notificationId}:{step}`; reading or acknowledging the item removes pending steps. Escalations that create work for staff create human tasks through [[WF-human-tasks]], not just messages. Fallback for `legal_service` is not configured here; it is the channel plan in [[DOM-service-of-notices-and-proof]].

**Administration.** Console: `/admin/notifications` (overview, health, volumes), `/admin/notifications/policies` (event × channel grid with inherited, locked and overridden cells; filter by class, unit, case type), `/admin/notifications/policies/[eventType]` (detail and history), `/admin/notifications/channels`, `/admin/notifications/quiet-hours-and-digests`, `/admin/notifications/escalations`, `/admin/notifications/senders` ([[PKG-notification-sender-identity]]), `/admin/notifications/templates` ([[PKG-document-and-notification]]), `/admin/notifications/deliveries` (search by case, recipient or provider message ID; evidence export), `/admin/notifications/suppressions` (bounced, complained, STOP). Platform: `/platform/notifications/baseline`, `/platform/notifications/providers`. Admin API: `/admin/v1/notifications/policies`, `/admin/v1/notifications/deliveries`, `/admin/v1/notifications/evidence/{noticeId}`. Permissions: `notify.policy:read|update|approve|publish`, `notify.delivery:read`, `notify.evidence:export`, `notify.suppression:update`, held by `tenant_admin`, `content_admin` (templates) through `ps.admin.content` ([[PKG-roles-and-permission-sets]]). Publishing a policy that removes a channel from any event or turns off an event is maker-checker. The admin copilot may draft policy changes as a diff for human approval ([[APP-admin-copilot]]).

**Delivery evidence.** For `service_grade` items: frozen rendered body (or document version), SHA-256, template version, policy version, sender identity, destination (masked in UI, encrypted at rest), provider message ID, every provider event with timestamps, and read or acknowledgement events. Export as a signed PDF plus JSON bundle (`admin.notify.evidence_exported` audited). Retention follows the case record ([[PKG-retention-and-deletion-schedule]]).

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Yes. Without it, notification behaviour per tenant would be code, mandatory notices could be weakened by configuration, and admins could not control channels, quiet hours, digests, escalation or senders.

<!-- check:unambiguous -->
### Unambiguous

Resolution order, the three mandatory levels and the fields each scope may set are listed in Notes; acceptance criteria give exact outcomes, skip reasons and problem types.

<!-- check:singular -->
### Singular

It states one capability (policy-driven resolution of how a notification is delivered) with one protected exception. Sender identity detail is split into [[PKG-notification-sender-identity]] and preference handling stays in [[PKG-notification-preferences]].

<!-- check:complete -->
### Complete and scoped

Covers scopes, roles and permissions, mandatory channels, quiet hours, digests, escalation, sender, template, evidence, running-case timing and the error cases at publish and send time. Open items are listed with owners.

<!-- check:feasible -->
### Feasible

Uses existing pieces: [[PKG-settings]] resolution, configuration lifecycle, BullMQ delayed and repeatable jobs and the existing notification rows; no new infrastructure.

<!-- check:verifiable -->
### Verifiable

Table-driven resolution tests, publish validation tests, BullMQ integration tests for escalation and digests, and an evidence export demonstration.

<!-- check:consistent -->
### Consistent

Uses the classes and defaults of [[PKG-notifications]], the preference rule in [[PKG-notification-preferences]], the scope hierarchy and lifecycle from the shared model, and leaves legal-service fallback to [[DOM-service-of-notices-and-proof]].

<!-- check:traced -->
### Traced

Source: overhaul brief and [[PKG-notifications]]; forward to [[PKG-settings-notifications]] keys, `packages/notifications` resolution code and the named test files.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Preference sets combine categories, channel types, channels and workflows; tenants can have default preference sets merged before environment defaults; required workflows can override recipient preferences.",
    "id": "R1",
    "kind": "vendor",
    "publisher": "Knock",
    "retrieved": "2026-10-28",
    "title": "Preferences overview",
    "url": "https://docs.knock.app/preferences/overview"
  },
  {
    "id": "R2",
    "issuer": "Ministry of Electronics and Information Technology, India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 22 of 2023",
    "title": "Digital Personal Data Protection Act, 2023",
    "url": "https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf"
  },
  {
    "id": "R3",
    "issuer": "European Parliament and Council",
    "jurisdiction": "EU",
    "kind": "regulation",
    "ref": "Regulation (EU) 2016/679",
    "title": "General Data Protection Regulation (official text)",
    "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng"
  },
  {
    "excerpt": "Opt-in must state that the person agrees to receive WhatsApp messages and name the business; opt-out requests for message categories must be honoured.",
    "id": "R4",
    "kind": "vendor",
    "publisher": "Meta",
    "retrieved": "2026-10-28",
    "title": "WhatsApp Business Platform: Get opt-in for WhatsApp",
    "url": "https://developers.facebook.com/docs/whatsapp/overview/getting-opt-in"
  },
  {
    "body": "IETF",
    "id": "R5",
    "ident": "RFC 8058",
    "kind": "standard",
    "title": "Signaling One-Click Functionality for List Email Headers",
    "url": "https://www.rfc-editor.org/rfc/rfc8058"
  },
  {
    "excerpt": "Transactional and broadcast email are sent through separate message streams so that bulk mail cannot harm the delivery of transactional mail.",
    "id": "R6",
    "kind": "vendor",
    "publisher": "Postmark",
    "retrieved": "2026-10-28",
    "title": "Message Streams",
    "url": "https://postmarkapp.com/message-streams"
  }
]
```

<!-- end -->
