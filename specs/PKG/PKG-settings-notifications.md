---
id: "PKG-settings-notifications"
title: "Notification settings"
parent: "PKG-settings-catalogue"
order: 8
type: "feature"
template: "config"
status: "draft"
owner: null
indicative: false
summary: "Catalogue of 61 notification settings (channels, mandatory and urgent notices, quiet hours, digests, escalation, sender identity, template locales, evidence, suppression, admin alerts) with scopes, locks, permissions and tenant blueprint defaults"
links: []
rev: 1
syncHash: "a65f1de572d8c480"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.7.3.8 Notification settings

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Catalogue of 61 notification settings (channels, mandatory and urgent notices, quiet hours, digests, escalation, sender identity, template locales, evidence, suppression, admin alerts) with scopes, locks, permissions and tenant blueprint defaults

<!-- section:purpose -->
## Purpose and scope

Settings that control how the platform notifies people on a tenant's behalf: which channels are on, channel order, mandatory and urgent notices, quiet hours, digests, escalation, sender identity, template locales, delivery evidence, suppression and admin alerts. Consumed by [[PKG-notifications]], [[PKG-notification-policies]] (which holds per-event-type rules as versioned policy artefacts, not settings), [[PKG-notification-sender-identity]], [[PKG-document-and-notification]] and [[DOM-service-of-notices-and-proof]] (evidence levels).

Not here: per-event-type policy rules (artefacts in [[PKG-notification-policies]]); a user's own channel opt-ins and digest choices, which are in [[PKG-settings-personal]] (the user-scope rows of `notify.quiet_hours.*` and `notify.digest.*` below are the only notification keys a user writes directly); provider credentials (secrets manager via [[INT-connections-admin]]); release flags for new channels ([[PKG-feature-flags]]); legal-service channel plans (decision tables in [[PKG-rules-and-decision-engine]]).

<!-- section:scopes -->
## Scopes that apply

| Scope | Used | Administered by | Notes |
|---|---|---|---|
| `platform` | yes | `platform_admin` (maker), `platform_security` (checker for locked rows) | Hard bounds, locked behaviours (email and in-app always on, legal service ignores suppression) |
| `region` | yes | `regional_ops` | For example SMS off by default in a region until a provider and registrations exist; WhatsApp region bounds |
| `offering` | no | — | Differences between CORD and TERES are expressed in tenant blueprints instead |
| `tenant` | yes | `tenant_admin`, `integration_admin` (channels, senders), `content_admin` (templates and locales) | Most keys |
| `unit` | yes | `unit_admin` | Channel enablement, order, quiet hours and senders where the tenant allowed unit overrides |
| `case_type` | yes | `workflow_designer` | Channel order, mandatory channels, escalation and evidence level for that blueprint; pinned at case start where marked |
| `case` | no | — | Notification behaviour is not changed per case; tribunal directions about service are data in the service workflow |
| `user` | yes (few keys) | the user | Quiet hours and digest timing only; opt-ins live in [[PKG-settings-personal]] |

<!-- section:catalogue -->
## Settings catalogue

61 settings in nine groups. Plan column: an entitlement key from [[BIL-plans-entitlements-and-usage]] or "all". "Lockable" means a higher scope may force the value for lower scopes. Audit classes: standard, sensitive (reason required), maker-checker (second approver, [[PKG-separation-of-duties]]).

**A. Channels**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `notify.channel.email.enabled` | bool | true | platform | yes (locked true at platform) | all | `settings.platform:write` | immediately | maker-checker |
| `notify.channel.in_app.enabled` | bool | true | platform | yes (locked true) | all | `settings.platform:write` | immediately | maker-checker |
| `notify.channel.sms.enabled` | bool | false | region, tenant, unit | yes | `feature.notify.sms` | `settings.notifications:write` | immediately (new sends) | sensitive |
| `notify.channel.whatsapp.enabled` | bool | false | region, tenant, unit | yes | `feature.notify.whatsapp` | `settings.notifications:write` | immediately (new sends) | maker-checker |
| `notify.channel.push.enabled` | bool | true | tenant, unit | yes | all | `settings.notifications:write` | immediately | standard |
| `notify.channel.order.transactional` | ordered list of channels | `[in_app, email]` | tenant, unit, case_type | yes | all | `settings.notifications:write` | next send | standard |
| `notify.channel.order.reminder` | ordered list | `[in_app, email]` | tenant, unit, case_type | yes | all | `settings.notifications:write` | next send | standard |
| `notify.channel.secondary_connection_allowed_classes` | set of classes | `[legal_service, auth]` | tenant | yes | all | `settings.notifications:write` | immediately | sensitive |
| `notify.channel.whatsapp.allowed_classes` | set: transactional, reminder, digest | `[reminder]` | platform, tenant, unit | yes | `feature.notify.whatsapp` | `settings.notifications:write` | next send | sensitive |
| `notify.channel.sms.max_segments` | int 1–4 | 2 | platform, tenant | yes | all | `settings.notifications:write` | template publish | standard |
| `notify.channel.sms.daily_budget` | int ≥ 0 (messages) | plan entitlement | tenant, unit | no | entitlement ceiling | `settings.notifications:write` | immediately | standard |
| `notify.channel.push.lock_screen_content` | enum: generic, title_only | generic | platform, tenant | yes | all | `settings.notifications:write` | next send | standard |
| `notify.channel.email.track_opens` | bool | false | platform, tenant | yes | all | `settings.notifications:write` | next send | sensitive |
| `notify.channel.email.track_clicks` | bool | false | platform, tenant | yes | all | `settings.notifications:write` | next send | sensitive |

**B. Mandatory and urgent notices**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `notify.mandatory.events` | map event_type → mandatory channels | platform baseline (legal_service events: per service rules) | platform, tenant, unit, case_type | yes | all | `settings.notifications:write` | next send; pinned events at case start | maker-checker |
| `notify.mandatory.allow_user_extra_channels` | bool | true | tenant | yes | all | `settings.notifications:write` | immediately | standard |
| `notify.urgent.bypass_quiet_hours_events` | set of `urgent_eligible` event types | `[]` | tenant, unit, case_type | yes | all | `settings.notifications:write` | next send | maker-checker |
| `notify.urgent.window_hours` | int 1–72 | 24 | tenant | yes | all | `settings.notifications:write` | next send | standard |
| `notify.legal_service.copy_to_case_manager` | bool | true | tenant, unit, case_type | yes | all | `settings.notifications:write` | new notices | standard |

**C. Quiet hours and send windows**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `notify.quiet_hours.enabled` | bool | true | platform, tenant, unit, user | yes (not at user) | all | `settings.notifications:write`; user: `settings.personal:write` | next send | standard |
| `notify.quiet_hours.start` | time HH:MM | 21:00 | tenant, unit, user | yes | all | as above | next send | standard |
| `notify.quiet_hours.end` | time HH:MM | 08:00 | tenant, unit, user | yes | all | as above | next send | standard |
| `notify.quiet_hours.channels` | set: sms, whatsapp, push, email | `[sms, whatsapp, push]` | platform, tenant, unit | yes | all | `settings.notifications:write` | next send | standard |
| `notify.quiet_hours.respect_holidays` | bool (uses the unit business schedule, [[WF-sla-and-business-calendars]]) | false | tenant, unit, user | yes | all | as above | next send | standard |
| `notify.quiet_hours.time_zone_source` | enum: recipient, case_seat | recipient | tenant | yes | all | `settings.notifications:write` | next send | standard |
| `notify.quiet_hours.max_deferral_hours` | int 1–24 | 12 | platform, tenant | yes | all | `settings.notifications:write` | next send | standard |

**D. Digests** (each user's own choice of frequency is `personal.notify.digest.frequency`; see [[PKG-settings-personal#catalogue]])

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `notify.digest.enabled` | bool | true | tenant, unit | yes | all | `settings.notifications:write` | next digest run | standard |
| `notify.digest.default_frequency` | enum: off, daily, weekly | daily | tenant, unit | yes | all | `settings.notifications:write` | next digest run | standard |
| `notify.digest.send_time` | time HH:MM (recipient zone) | 08:00 | tenant, unit, user | no | all | as above | next digest run | standard |
| `notify.digest.weekly_day` | enum mon–sun | mon | tenant, user | no | all | as above | next digest run | standard |
| `notify.digest.eligible_classes` | set: transactional, reminder | `[transactional]` | platform, tenant | yes | all | `settings.notifications:write` | next digest run | standard |
| `notify.digest.max_items` | int 10–200 | 50 | tenant | no | all | `settings.notifications:write` | next digest run | standard |
| `notify.digest.include_case_titles` | bool | false | tenant, unit | yes | all | `settings.notifications:write` | next digest run | sensitive |

**E. Escalation and reminder limits**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `notify.escalation.enabled` | bool | true | tenant, unit, case_type | yes | all | `settings.notifications:write` | new notifications | standard |
| `notify.escalation.unread_after_hours` | int 1–168 | 24 | tenant, unit, case_type | no | all | `settings.notifications:write` | new notifications | standard |
| `notify.escalation.next_channel` | enum: email, sms, whatsapp | email | tenant, unit, case_type | no | all | `settings.notifications:write` | new notifications | standard |
| `notify.escalation.notify_role` | role key or none | `case_manager` | tenant, unit, case_type | no | all | `settings.notifications:write` | new notifications | standard |
| `notify.reminder.max_per_recipient_per_day` | int 1–20 | 5 | platform, tenant | yes | all | `settings.notifications:write` | next send | standard |
| *Hearing reminder offsets* | see [[PKG-settings-cases-and-workflows#catalogue]] (`case.hearing.reminder_offsets`; reminder timing tied to procedure lives there, decision D9) | | | | | | | |

**F. Sender identity (see [[PKG-notification-sender-identity]])**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `notify.sender.email.default_identity` | sender identity ID | regional platform domain | tenant, unit | yes | custom domain: `feature.custom_email_domain` | `settings.notifications:write` | next send | maker-checker |
| `notify.sender.email.display_name` | text ≤ 64 | tenant display name | tenant, unit | yes | all | `settings.notifications:write` | next send | standard |
| `notify.sender.email.reply_to` | email on verified domain, or none | none (no-reply with footer link) | tenant, unit | no | all | `settings.notifications:write` | next send | standard |
| `notify.sender.email.fallback_to_platform_domain` | bool | true | tenant | yes | all | `settings.notifications:write` | immediately | sensitive |
| `notify.sender.email.min_dmarc_policy` | enum: none, quarantine, reject | none | platform, tenant | yes (platform floor) | all | `settings.notifications:write` | next verification run | sensitive |
| `notify.sender.sms.default_identity` | sender identity ID | regional platform header | tenant, unit | yes | `feature.notify.sms` | `settings.notifications:write` | next send | maker-checker |
| `notify.sender.sms.fallback_to_platform` | bool | true | tenant | yes | `feature.notify.sms` | `settings.notifications:write` | immediately | sensitive |
| `notify.sender.whatsapp.number_mode` | enum: shared_platform, tenant_number | shared_platform | tenant | yes | `feature.notify.whatsapp` | `settings.notifications:write` | next send | maker-checker |
| `notify.sender.unit_override_allowed` | bool | false | tenant | yes | all | `settings.notifications:write` | immediately | standard |

**G. Templates and locales**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `notify.template.required_locales` | list of BCP 47 tags | tenant enabled languages | tenant | yes | all | `settings.branding:write` | next template publish | standard |
| `notify.template.locale_fallback` | ordered list | `[user, unit_default, tenant_default, en]` | platform, tenant | yes | all | `settings.branding:write` | next send | standard |
| `notify.template.publish_requires_approval` | bool | true | platform, tenant | yes (locked true for `legal_service` templates) | all | `settings.branding:write` | immediately | maker-checker |
| `notify.template.allow_unit_variants` | bool | false | tenant | yes | all | `settings.branding:write` | immediately | standard |

**H. Evidence, suppression and retention**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `notify.evidence.default_level` | enum: none, standard, service_grade | standard (`service_grade` locked for `legal_service`) | platform, tenant, case_type | yes | all | `settings.notifications:write` | new notifications | maker-checker |
| `notify.evidence.email_open_counts_as_evidence` | bool | false | platform, tenant | yes (platform may lock false per region) | all | `settings.notifications:write` | new notices | maker-checker |
| `notify.evidence.whatsapp_read_counts_as_evidence` | bool | false | platform, tenant | yes | all | `settings.notifications:write` | new notices | maker-checker |
| `notify.suppression.auto_suppress_hard_bounce` | bool | true | platform, tenant | yes | all | `settings.notifications:write` | immediately | standard |
| `notify.suppression.legal_service_ignores_suppression` | bool | true | platform | yes (locked true) | all | `settings.platform:write` | immediately | maker-checker |
| `notify.in_app.retention_days` | int 30–730 | 180 | platform, tenant | yes | all | `settings.notifications:write` | next nightly clean-up | standard |

**I. Admin alerting**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `notify.admin_alerts.recipients` | set of role keys | `[tenant_admin, integration_admin]` | tenant, unit | no | all | `settings.notifications:write` | immediately | standard |
| `notify.admin_alerts.bounce_rate_threshold_pct` | number 1–20 | 5 | tenant | no | all | `settings.notifications:write` | next evaluation (5 min) | standard |
| `notify.admin_alerts.budget_alert_pct` | int 50–100 | 80 | tenant | no | all | `settings.notifications:write` | immediately | standard |

<!-- section:validation -->
## Validation and dependencies

- `notify.channel.email.enabled` and `notify.channel.in_app.enabled` are locked true at platform: email and in-app are needed for legal service and account security.
- `notify.mandatory.events` cannot remove a channel that the case's service rules require for a `legal_service` event, and cannot list a channel that is disabled at that scope (`notify-policy-channel-not-enabled`).
- `notify.urgent.bypass_quiet_hours_events` may contain only event types flagged `urgent_eligible` in the event catalogue.
- `notify.channel.whatsapp.enabled = true` requires an `active` WhatsApp connection with a policy group other than `blocked` ([[INT-connector-data-policies]]) and at least one approved WhatsApp template; `notify.channel.whatsapp.allowed_classes` can never include `legal_service` unless a platform-level rule for the region allows it (none today; legal to confirm per jurisdiction).
- `notify.channel.sms.enabled = true` in the India region requires a sender identity with DLT registration and all SMS templates in use carrying DLT template IDs, with URLs whitelisted [R3].
- `notify.quiet_hours.start` and `.end` must define a window of 4 to 12 hours; the platform bound protects reachability for reminders.
- `notify.sender.email.default_identity` must reference a `verified` identity; `min_dmarc_policy` at tenant may only be stricter than the platform floor.
- `notify.digest.eligible_classes` can never include `legal_service` or `auth` (schema-enforced).
- Digest and reminder emails always carry one-click unsubscribe [R1]; `legal_service` and `auth` emails never do. Not configurable.
- WhatsApp sends require a recorded opt-in naming the tenant [R2]; not configurable.
- Effective SMS budget = `min(entitlement, notify.channel.sms.daily_budget)`; `legal_service` and `auth` are never blocked by the budget.
- Invalid changes show the failing rule, the scope that imposes it, and the link to the owning node.

<!-- section:defaults -->
## Defaults by tenant type

| Key | Arbitral institution | SEBI ODR institution | CORD tenant | Court or government programme |
|---|---|---|---|---|
| `notify.channel.sms.enabled` | false | true | true | true |
| `notify.channel.whatsapp.enabled` | false | true (reminders only) | false | false |
| `notify.channel.order.reminder` | `[in_app, email]` | `[sms, email, in_app]` | `[email, sms, in_app]` | `[sms, email, in_app]` |
| `notify.mandatory.events` (beyond legal service) | hearing changes: email | hearing changes and deadline reminders: email + SMS | hearing changes: email | all hearing notices: email + SMS |
| `notify.quiet_hours.start` / `.end` | 21:00 / 08:00 | 21:00 / 09:00 | 21:00 / 08:00 | 20:00 / 08:00 |
| `notify.digest.default_frequency` | daily (counsel, neutrals) | off (parties get individual reminders) | daily | off |
| `notify.digest.include_case_titles` | true | false | false | false |
| `notify.escalation.unread_after_hours` | 48 | 24 | 24 | 24 |
| `notify.sender.email.default_identity` | tenant domain (required at go-live) | tenant domain | platform domain | tenant (government) domain |
| `notify.evidence.default_level` | service_grade | service_grade | standard | service_grade |
| `notify.template.required_locales` | `[en]` (plus `zh-Hant` for Hong Kong institutions, where chosen) | `[en, hi]` plus regional languages chosen by the institution | `[en]` | official languages of the programme |

Why they differ: SEBI ODR matters involve many unrepresented investors reached mainly by SMS, in several languages; arbitral institutions communicate with counsel by email and need formal evidence; court programmes need dual-channel hearing notices. Assumption: SEBI ODR circulars do not prescribe channels beyond electronic communication; to be confirmed by legal.

<!-- section:admin_ux -->
## Where it is administered

| Group | Console | API |
|---|---|---|
| A, B, C, D, E | Tenant admin console → Notifications → Channels / Quiet hours and digests / Escalations (`/admin/notifications/...`); unit admins at `/admin/organisation/units/[unitId]/notifications` | `PATCH /admin/v1/settings/notify.*` ([[INT-tenant-admin-api]]) |
| F | Notifications → Senders (`/admin/notifications/senders`) | `/admin/v1/notifications/senders` |
| G | Notifications → Templates → Locales | `/admin/v1/settings/notify.template.*` |
| H, I | Notifications → Evidence and alerts | `/admin/v1/settings/notify.*` |
| Platform and region rows | `/platform/notifications/baseline`, `/platform/regions/[region]/notifications` | `/platform/v1/settings/notify.*` |
| Case-type rows | Blueprint editor → Notifications panel ([[WF-workflow-authoring-studio]]) | part of the blueprint |
| User rows | `/me/settings/notifications` ([[PKG-personalisation]]) | tRPC `me.preferences.*` |

Every control shows the effective value, its source scope and a lock icon with the locking scope. The admin copilot ([[APP-admin-copilot]]) may propose changes (for example "add SMS to hearing reminders for the SEBI ODR desk") as a draft with a diff; it cannot publish maker-checker rows.

<!-- section:change_control -->
## Change control and audit

- Maker-checker: enabling WhatsApp, changing default senders, changing mandatory events or urgent bypass lists, lowering evidence levels, and changing whether email opens or WhatsApp reads count as evidence. Approver must hold `settings.notifications:approve` and differ from the author.
- Notified on publish: tenant owners (for maker-checker rows), integration admins (channels and senders), content admins (templates and locales).
- Rollback: publish the previous version from the change history ([[APP-admin-change-history]]); one action, audited as `admin.settings.published` with `rollback_of`.
- Audit record: key, scope and scope ID, old and new value, actor, approver, reason, policy and settings version, time ([[PKG-audit-trail]]).

<!-- section:migration -->
## Versioning and migration

Keys are never reused; renamed keys keep an alias for two releases. A changed platform default applies only to tenants that inherit it; tenants with an explicit value are listed in release notes. The digest and quiet-hours keys replace the free-form settings previously described in [[PKG-notifications#config]] (one-time migration, no tenant data yet). All tenant and unit rows travel in configuration packages ([[PKG-configuration-packages]]); sender identity IDs are remapped on import and imported senders start unverified.

<!-- section:testing -->
## Testing

Registry `packages/settings/registry/notify.ts` is the source; CI fails if this table and the registry differ (key, type, default, scopes, lock, permission, audit class). Resolution tests cover platform lock → tenant attempt; unit override where `notify.sender.unit_override_allowed` is false; user quiet hours within tenant bounds; case-type evidence level pinned at case start. Validation rules above each have a negative test.

<!-- section:questions -->
## Open questions

- [ ] Should a court programme be able to set `notify.channel.email.track_opens = true` for evidence? Default off; legal to advise per jurisdiction. (Legal)
- [x] Hearing reminder offsets moved to [[PKG-settings-cases-and-workflows]] as `case.hearing.reminder_offsets` (decision D9: reminder timing tied to procedure lives there); this catalogue keeps delivery mechanics.
- [ ] Confirm quiet-hours bounds (4–12 hours) against TRAI rules for transactional SMS in India; assumption: no time restriction for service and transactional messages, to be confirmed by legal. (Legal)

<!-- checks -->
## Template checks

<!-- check:inheritance -->
### Inheritance and locks

Each key lists its scopes; resolution is the shared order with locks and bounds from [[PKG-configuration-scope-hierarchy]]. The only user-writable notification keys are quiet hours and digest timing; per-event rules are policy artefacts resolved by [[PKG-notification-policies]], so there is one place for each decision. When a higher scope later locks a key, lower explicit values are kept but inactive and shown as "overridden by lock".

<!-- check:permissions -->
### Who may change what

`settings.notifications:write` for tenant and unit rows, `settings.branding:write` for templates and locales, `settings.platform:write` for platform rows, `settings.personal:write` for user rows; approvals need `settings.notifications:approve`. Unit admins act only on units in their resource set.

<!-- check:safety -->
### Safe bounds

Email and in-app cannot be turned off; legal-service notices ignore opt-outs, quiet hours, suppression and budgets; digests can never hold legal or sign-in messages; WhatsApp needs a non-blocked data policy group and recorded opt-in; quiet-hours windows have bounds.

<!-- check:timing -->
### When changes take effect

The "Takes effect" column states it per key; most apply to the next send; evidence levels and case-type rows marked pinned are captured when a case starts; caches are invalidated by settings version bump within 60 seconds.

<!-- check:audit -->
### Audit and rollback

Every change is versioned with actor, approver, reason, old and new values and scope; the effective value at any past time can be reproduced from versions; rollback is one audited action.

<!-- check:sync -->
### Catalogue matches code

Generated registry check in CI; new keys need an owner node, default, scopes and audit class before merge.

<!-- citations -->
## Citations

```json
[
  {
    "body": "IETF",
    "id": "R1",
    "ident": "RFC 8058",
    "kind": "standard",
    "title": "Signaling One-Click Functionality for List Email Headers",
    "url": "https://www.rfc-editor.org/rfc/rfc8058"
  },
  {
    "excerpt": "Opt-in must state that the person agrees to receive WhatsApp messages and name the business; opt-out requests for message categories must be honoured.",
    "id": "R2",
    "kind": "vendor",
    "publisher": "Meta",
    "retrieved": "2026-10-28",
    "title": "WhatsApp Business Platform: Get opt-in for WhatsApp",
    "url": "https://developers.facebook.com/docs/whatsapp/overview/getting-opt-in"
  },
  {
    "excerpt": "From 1 September 2024 messages containing URLs, APKs, OTT links or call-back numbers that are not whitelisted are not permitted; a content template may not be linked to more than one header.",
    "id": "R3",
    "issuer": "Telecom Regulatory Authority of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "title": "TRAI Direction of 20 August 2024 under the Telecom Commercial Communications Customer Preference Regulations, 2018",
    "url": "https://trai.gov.in/sites/default/files/Direction_20082024.pdf"
  }
]
```

<!-- end -->
