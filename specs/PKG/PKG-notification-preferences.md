---
id: "PKG-notification-preferences"
title: "Notification preferences"
parent: "PKG-notifications"
order: 1
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Per-user channel opt-ins, per-event choices, language, digest and quiet hours applied within tenant notification policy; legal service, sign-in and policy-mandatory channels cannot be opted out of"
links: []
rev: 3
syncHash: "83d9e04e99a201dc"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.11.1 Notification preferences

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Per-user channel opt-ins, per-event choices, language, digest and quiet hours applied within tenant notification policy; legal service, sign-in and policy-mandatory channels cannot be opted out of

<!-- section:statement -->
## Statement

When the Notifications package resolves the channels for a recipient, it shall apply that recipient's stored channel opt-ins, per-event choices, language, digest and quiet-hours preferences within the limits of the published notification policy for the event type, except that notifications of class `legal_service` or `auth`, and channels the policy marks mandatory for the event type, shall be delivered regardless of the recipient's opt-outs (and, for `legal_service`, `auth` and policy-approved urgent events, regardless of quiet hours).

<!-- section:rationale -->
## Rationale and source

People must be able to control how often and where they are contacted (consent for SMS and WhatsApp, message fatigue, quiet hours), and privacy law expects messaging choices to be honoured; DPDP and GDPR make consent withdrawal as easy as giving it [R1][R2], and WhatsApp requires an opt-in that names the business [R4]. At the same time, a party cannot opt out of being served with a notice of arbitration or a procedural order, must receive sign-in codes when they ask for them, and may be required by their institution to receive hearing changes on a second channel. The layering (user choices applied inside tenant policy, with required messages overriding preferences) follows the common pattern of recipient preferences merged with tenant defaults and required workflows that override them [R3]. Source: parent capability [[PKG-notifications]]; tenant rules in [[PKG-notification-policies]]; service-of-notice obligations in [[DOM-service-of-notices-and-proof]]; consent handling in [[SEC-consent-and-notice-management]].

Preference model (for implementers): keys in [[PKG-settings-personal]] group E (`personal.notify.email.opt_in`, `.sms.opt_in`, `.whatsapp.opt_in` and `.push.opt_in` with consent records; `personal.notify.digest.frequency`; `personal.notify.event_overrides`) plus the user-scope rows of `notify.quiet_hours.*` and `notify.digest.*` in [[PKG-settings-notifications]]; language from `personal.locale.language`. Stored per tenant membership. Email default on, SMS and WhatsApp default off and require explicit opt-in with a verified number and a timestamped consent record. `legal_service` and `auth` have no opt-out controls in the UI; mandatory channels appear fixed with the explanation "Required by <organisation> for <event>".

<!-- section:acceptance -->
## Acceptance criteria

- **Given** a party has opted out of SMS, **when** a `reminder` notification is sent whose policy does not make SMS mandatory, **then** no SMS delivery is created and the result lists `skipped: opted_out` for SMS.
- **Given** the same party, **when** a `legal_service` notification whose service rules require email and SMS is sent, **then** both email and SMS deliveries are created.
- **Given** the same party and a tenant policy making SMS mandatory for `hearing.rescheduled`, **when** a hearing is rescheduled, **then** an SMS delivery is created and the party's settings page shows SMS as required for that event.
- **Given** a user whose quiet hours are 21:00–08:00 in `Asia/Kolkata`, **when** a `reminder` SMS is triggered at 22:30 IST, **then** the delivery is scheduled for 08:00 IST and recorded as `quiet_hours_deferred`.
- **Given** the same user, **when** an OTP is requested at 22:30 IST, **then** it is sent immediately.
- **Given** a user with locale `hi-IN` and a template available in Hindi, **when** any notification is sent, **then** the Hindi version is used; **given** no Hindi version, **then** the locale fallback chain (`notify.template.locale_fallback`) is used.
- **Given** a user chose weekly digests, **when** `transactional` events occur, **then** they are held for the digest unless the policy marks the event not digest-eligible.
- **Negative:** **given** a user has never opted in to WhatsApp, **when** a `transactional` notification lists WhatsApp in the policy's default channels, **then** no WhatsApp message is sent and the skip reason is `not_opted_in`.
- **Negative:** **given** a user tries to remove email from `notice.arbitration.served` through the API, **then** the request is rejected with `SettingValidationError` and nothing changes.

<!-- section:verification -->
## Verification method

Test: table-driven unit tests over class × policy flags (default, allowed, mandatory, urgent) × channel × opt-in × quiet hours × digest × locale in `packages/notifications/test/preferences.spec.ts`, sharing fixtures with `policy-resolution.spec.ts` ([[PKG-notification-policies]]), plus an integration test with real Postgres verifying the consent record is required for SMS and WhatsApp opt-in. Inspection: UI review confirms no opt-out controls for `legal_service` and `auth`, and fixed mandatory channels with explanatory text, on `/me/settings/notifications` ([[PKG-personalisation]]).

<!-- section:priority -->
## Priority

Must. Phase 2 (Shared services) for email, SMS and in-app; WhatsApp preferences in phase 4 with the WhatsApp channel.

<!-- section:notes -->
## Notes

Open questions:
- [ ] Legal to confirm which events may be marked urgent and bypass quiet hours besides `legal_service` and `auth` (for example hearing-day changes within 24 hours); tracked in [[PKG-notification-policies]].
- [ ] Is a WhatsApp opt-in captured on the platform sufficient, or must it also be recorded with the provider? (Provider policy; to be confirmed with [[INT-messaging-providers]].)
- [x] Should tenant admins be able to force channels for `reminder` overriding user opt-outs? Decided: yes, but only per event type through a published, maker-checker policy marking the channel mandatory, and never for WhatsApp (which always needs the recipient's own opt-in).

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Yes: without it the platform would either ignore consent choices for SMS and WhatsApp (privacy and provider-policy breach) or let parties suppress legal notices (service failure).

<!-- check:singular -->
### Singular

It states one rule (apply preferences when resolving channels) with one exception class; the preference model in the rationale is context for implementers, not additional requirements.

<!-- check:complete -->
### Complete and scoped

States when it applies (every channel resolution), to whom (every recipient), the exceptions (legal service, auth, mandatory channels, urgent events) and the error case (attempts to remove mandatory channels are rejected; missing opt-in means skip with a reason).

<!-- check:verifiable -->
### Verifiable

Acceptance criteria cover the opt-out, the legal-service bypass, quiet hours, locale fallback and a negative WhatsApp case; all are automatable in the table-driven test.

<!-- check:consistent -->
### Consistent

Consistent with [[PKG-notifications]] classes, [[PKG-notification-policies]] layering, the keys in [[PKG-settings-notifications]] and [[PKG-settings-personal]], and settings inheritance in [[PKG-configuration-scope-hierarchy]].

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
    "id": "R2",
    "issuer": "European Parliament and Council",
    "jurisdiction": "EU",
    "kind": "regulation",
    "ref": "Regulation (EU) 2016/679",
    "title": "General Data Protection Regulation (official text)",
    "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng"
  },
  {
    "excerpt": "Preference sets combine categories, channel types, channels and workflows; tenants can have default preference sets merged before environment defaults; required workflows can override recipient preferences.",
    "id": "R3",
    "kind": "vendor",
    "publisher": "Knock",
    "retrieved": "2026-10-28",
    "title": "Preferences overview",
    "url": "https://docs.knock.app/preferences/overview"
  },
  {
    "excerpt": "Opt-in must state that the person agrees to receive WhatsApp messages and name the business; opt-out requests for message categories must be honoured.",
    "id": "R4",
    "kind": "vendor",
    "publisher": "Meta",
    "retrieved": "2026-10-28",
    "title": "WhatsApp Business Platform: Get opt-in for WhatsApp",
    "url": "https://developers.facebook.com/docs/whatsapp/overview/getting-opt-in"
  }
]
```

<!-- end -->
