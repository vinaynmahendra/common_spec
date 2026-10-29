---
id: "PKG-settings-personal"
title: "Personal preference settings"
parent: "PKG-settings-catalogue"
order: 9
type: "feature"
template: "config"
status: "draft"
owner: null
indicative: false
summary: "Catalogue of 45 personal preference settings: language, time zone and formats, appearance and layout, accessibility (never lockable), shortcuts, personal notification choices, default views and dashboards, document, hearing and privacy preferences"
links: []
rev: 1
syncHash: "c692578bcdf6acf6"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.7.3.9 Personal preference settings

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Catalogue of 45 personal preference settings: language, time zone and formats, appearance and layout, accessibility (never lockable), shortcuts, personal notification choices, default views and dashboards, document, hearing and privacy preferences

<!-- section:purpose -->
## Purpose and scope

Each person's own preferences: language and region, appearance and layout, accessibility, shortcuts, personal notification choices, default views and dashboards, document and hearing defaults, privacy and presence. Consumed by [[PKG-personalisation]] (the personal settings area and its storage), [[PKG-colour-modes-and-user]] (mode, density, motion), [[PKG-notification-preferences]] (opt-ins), [[I18N-l10n]] (formats), [[APP-hearing-room-in-browser]] (captions, camera and microphone defaults) and [[APP-document-viewer-and-sandbox]].

Not here: the tenant's default language, terminology and branding ([[PKG-settings-branding-content]]); session timeout and MFA ([[PKG-settings-security-and-identity]]); AI assistant preferences ([[PKG-settings-ai]]); saved view and dashboard definitions, which are records, not settings ([[PKG-personalisation#data]]); notification rules per event type ([[PKG-notification-policies]]).

<!-- section:scopes -->
## Scopes that apply

| Scope | Used | Administered by | Notes |
|---|---|---|---|
| `platform` | yes | platform admin | Code defaults and bounds only |
| `region` | no | — | No regional differences in personal preferences |
| `offering` | no | — | — |
| `tenant` | yes | `tenant_admin`, `content_admin` | **Defaults** for members, never forcing accessibility, language or time zone |
| `unit` | yes | `unit_admin` | Defaults for unit members (for example compact density for a registry desk) |
| `case_type`, `case` | no | — | Personal preferences do not vary by case |
| `user` | yes | the user | Stored per tenant membership; optional "apply in all my organisations in this region" |

Values are stored per membership (user × tenant) as `setting_value` rows at level `user` ([[PKG-settings-data-model]]); a person with two memberships in different regions has independent values in each region.

<!-- section:catalogue -->
## Settings catalogue

45 settings in seven groups (the muted-cases row is listed to show where that state lives). "Lockable" here means a tenant or unit can force the value for its members; most personal settings are deliberately not lockable.

**A. Language and region**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `personal.locale.language` | BCP 47 tag from tenant enabled languages | inherit tenant default ([[PKG-settings-branding-content]]) | unit, user | no (never lockable) | all | self; defaults: `settings.personal:write` | next page load | standard |
| `personal.locale.time_zone` | IANA zone or `auto` | auto | unit, user | no | all | self; defaults: `settings.personal:write` | next page load | standard |
| `personal.locale.date_format` | enum: locale, iso, dmy, mdy | locale | tenant, unit, user | no | all | self; defaults: `settings.personal:write` | next page load | standard |
| `personal.locale.time_format` | enum: locale, h12, h24 | locale | tenant, unit, user | no | all | self; defaults: `settings.personal:write` | next page load | standard |
| `personal.locale.week_start` | enum: locale, mon, sat, sun | locale | tenant, unit, user | no | all | self; defaults: `settings.personal:write` | next page load | standard |
| `personal.locale.number_grouping` | enum: locale, indian, international | locale | tenant, unit, user | no | all | self; defaults: `settings.personal:write` | next page load | standard |
| `personal.locale.show_dual_time_zones` | bool | true | tenant, user | no | all | self; defaults: `settings.personal:write` | next page load | standard |
| `personal.locale.apply_to_all_memberships_in_region` | bool (action flag, stored for display) | false | user | no | all | `settings.personal:write` (self) | immediately | standard |

**B. Appearance and layout**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `personal.appearance.mode` | enum: system, light, dark, high_contrast | system (tenant may set light or dark default) | tenant, unit, user | no for high_contrast (users can always choose it) | all | self; defaults: `settings.personal:write` | immediately (no reload) | standard |
| `personal.appearance.density` | enum: comfortable, compact | comfortable | tenant, unit, user | tenant may restrict to comfortable | all | self; defaults: `settings.personal:write` | immediately | standard |
| `personal.appearance.sidebar_collapsed` | bool | false | user | no | all | `settings.personal:write` (self) | immediately | standard |
| `personal.appearance.start_page` | enum per persona (home, queue, cases, last_visited) | home | tenant, unit, user | no | all | self; defaults: `settings.personal:write` | next sign-in | standard |
| `personal.appearance.case_workspace_layout` | enum: timeline_left, documents_left, tabs | timeline_left | tenant, user | no | all | self; defaults: `settings.personal:write` | next case open | standard |
| `personal.table.page_size` | enum: 25, 50, 100 | 25 | tenant, user | no | all | self; defaults: `settings.personal:write` | next list load | standard |
| `personal.table.wrap_cell_text` | bool | false | user | no | all | `settings.personal:write` (self) | immediately | standard |

**C. Accessibility (never lockable by tenant or unit)**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `personal.a11y.reduce_motion` | enum: system, on, off | system | user | no | all | `settings.personal:write` (self) | immediately | standard |
| `personal.a11y.underline_links` | bool | false | user | no | all | `settings.personal:write` (self) | immediately | standard |
| `personal.a11y.larger_targets` | bool (44 px minimum) | false | user | no | all | `settings.personal:write` (self) | immediately | standard |
| `personal.a11y.enhanced_focus` | bool (thicker focus ring) | false | user | no | all | `settings.personal:write` (self) | immediately | standard |
| `personal.a11y.text_spacing` | enum: normal, wide | normal | user | no | all | `settings.personal:write` (self) | immediately | standard |
| `personal.a11y.live_announcements` | enum: all, important, off | important | user | no | all | `settings.personal:write` (self) | immediately | standard |
| `personal.a11y.captions_default_on` | bool | true | tenant, user | no | all | self; defaults: `settings.personal:write` | next hearing join | standard |
| `personal.a11y.timeout_warning_minutes` | int 2–10 | 2 | user | no | all | `settings.personal:write` (self) | next session warning | standard |
| `personal.a11y.prefer_accessible_document_copies` | bool | false | user | no | all | `settings.personal:write` (self) | next document open | standard |

**D. Keyboard shortcuts and command palette**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `personal.shortcuts.enabled` | bool | true (false in party portal, fixed) | tenant, user | no | all | self; defaults: `settings.personal:write` | immediately | standard |
| `personal.shortcuts.single_key_enabled` | bool | true | tenant, user | no (users can always turn off) | all | self; defaults: `settings.personal:write` | immediately | standard |
| `personal.shortcuts.overrides` | map action → key chord (validated against reserved list) | `{}` | user | no | all | `settings.personal:write` (self) | immediately | standard |
| `personal.command_palette.enabled` | bool | true | user | no | all | `settings.personal:write` (self) | immediately | standard |

**E. Notifications (personal choices; tenant rules in [[PKG-settings-notifications]])**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `personal.notify.email.opt_in` | bool (non-mandatory classes only) | true | user | no | all | `settings.personal:write` (self) | next send | standard |
| `personal.notify.sms.opt_in` | bool + consent record | false | user | no | `feature.notify.sms` | `settings.personal:write` (self) after OTP verification | next send | sensitive |
| `personal.notify.whatsapp.opt_in` | bool + consent record naming the tenant | false | user | no | `feature.notify.whatsapp` | `settings.personal:write` (self) after OTP verification | next send | sensitive |
| `personal.notify.push.opt_in` | bool + browser permission | false | user | no | all | `settings.personal:write` (self) | next send | standard |
| `personal.notify.digest.frequency` | enum: immediate, daily, weekly | tenant `notify.digest.default_frequency` | user | no | all | `settings.personal:write` (self) | next digest run | standard |
| `personal.notify.event_overrides` | map event_type → channels (within allowed, never removing mandatory) | `{}` | user | no | all | `settings.personal:write` (self) | next send | standard |
| `personal.notify.in_app_sound` | bool | false | user | no | all | `settings.personal:write` (self) | immediately | standard |
| `personal.notify.muted_case_ids` | not a setting: case watch records ([[PKG-personalisation#data]]) | — | — | — | — | — | — | — |

**F. Views, dashboards and documents**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `personal.views.default.<surface>` | saved view ID visible to the user | tenant or unit default view | tenant, unit, user | tenant may lock a default view only for admin tables | all | self; defaults: `settings.personal:write` | next list load | standard |
| `personal.dashboard.home` | dashboard ID | tenant or unit published dashboard | tenant, unit, user | no | all | self; defaults: `settings.personal:write` | next home load | standard |
| `personal.documents.open_in` | enum: viewer, download | viewer | tenant, user | tenant may lock viewer (download controls) | all | self; defaults: `settings.personal:write` | next open | standard |
| `personal.documents.viewer_zoom` | enum: fit_width, fit_page, 100 | fit_width | user | no | all | `settings.personal:write` (self) | next open | standard |
| `personal.editor.spellcheck_language` | BCP 47 tag or `off` | same as `personal.locale.language` | user | no | all | `settings.personal:write` (self) | immediately | standard |
| `personal.hearing.join_with_camera_off` | bool | false | user | no | all | `settings.personal:write` (self) | next hearing join | standard |
| `personal.hearing.join_with_mic_muted` | bool | true | tenant, user | no | all | self; defaults: `settings.personal:write` | next hearing join | standard |

**G. Privacy and presence**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `personal.privacy.show_presence` | bool | true (staff), false (party, counsel) | tenant, user | no | all | self; defaults: `settings.personal:write` | immediately | standard |
| `personal.privacy.show_profile_photo_to_parties` | bool | false | user | no | all | `settings.personal:write` (self) | immediately | standard |
| `personal.privacy.usage_analytics` | enum: standard, essential_only | standard | user | no | all | `settings.personal:write` (self) | next page load | sensitive |


**User-writable keys from other catalogues**: `notify.quiet_hours.enabled`, `notify.quiet_hours.start`, `notify.quiet_hours.end`, `notify.quiet_hours.respect_holidays`, `notify.digest.send_time`, `notify.digest.weekly_day` ([[PKG-settings-notifications]]). They appear on `/me/settings/notifications` but are defined once, in that catalogue.

<!-- section:validation -->
## Validation and dependencies

- Accessibility (`personal.a11y.*`), language, time zone and colour mode `high_contrast` can never be locked by a tenant or unit; the registry marks them `lockable: false` and the settings API rejects a lock with `SettingNotLockableError`. Tenants may only set defaults. This keeps WCAG 2.2 user-adaptation needs in the user's control [R1].
- `personal.shortcuts.single_key_enabled` can always be turned off by the user (WCAG 2.2 SC 2.1.4 Character Key Shortcuts) [R1]; overrides cannot bind keys on the reserved list (browser, operating system and screen-reader keys).
- `personal.a11y.reduce_motion = system` follows `prefers-reduced-motion` [R2].
- `personal.locale.language` must be one of the tenant's enabled languages; if the tenant later disables it, resolution falls back to the unit or tenant default and the user is told once.
- `personal.notify.sms.opt_in` and `.whatsapp.opt_in` can be set to true only through the opt-in flow, which verifies the number and stores a consent record with the consent text version; WhatsApp opt-in names the tenant as the business [R3]. Setting them to false is always one action and takes effect for the next send; DPDP requires withdrawal to be as easy as giving consent [R4].
- `personal.notify.event_overrides` cannot remove mandatory channels for an event; the UI shows them as fixed with the reason.
- `personal.appearance.density = compact` is ignored on party, counsel and neutral surfaces ([[PKG-colour-modes-and-user#spacing]]).
- `personal.documents.open_in = download` is ignored where the tenant locks viewer-only access for confidential documents.

<!-- section:defaults -->
## Defaults by tenant type

| Key | Arbitral institution | SEBI ODR institution | CORD tenant | Court or government programme |
|---|---|---|---|---|
| `personal.locale.language` (tenant default via branding) | en | en (hi and regional languages offered) | en | official language of the programme |
| `personal.locale.show_dual_time_zones` | true | false (single zone, India) | true | false |
| `personal.locale.number_grouping` | locale | indian | locale | locale |
| `personal.appearance.density` (staff) | compact for secretariat unit | comfortable | comfortable | comfortable |
| `personal.a11y.captions_default_on` | true | true | true | true |
| `personal.shortcuts.single_key_enabled` | true (staff) | false (staff default; parties never) | true | false |
| `personal.notify.digest.frequency` | daily (counsel) | immediate | daily | immediate |
| `personal.privacy.show_presence` | true for staff | true for staff | true for staff | false |
| `personal.hearing.join_with_mic_muted` | true | true | true | true |

Why: institutional counsel and secretariat staff value dense views and digests; SEBI ODR investors and court programme users are often first-time, mobile users who need simple, immediate messages in their own language; dual time zones matter for international arbitration.

<!-- section:admin_ux -->
## Where it is administered

- Users: `/me/settings/<section>` ([[PKG-personalisation#routing]]); tRPC `me.preferences.get/set/reset`.
- Tenant and unit defaults: `/admin/personalisation/defaults` and `/admin/organisation/units/[unitId]/personalisation`; API `PATCH /admin/v1/settings/personal.*` (defaults only; the API refuses user-scope writes from admin credentials).
- Each personal control shows "Your choice" or "Default from <scope>"; reset returns to the inherited default.
- Admins cannot view an individual's personal values; support staff under impersonation ([[PKG-support-access-and-impersonation]]) see them read-only and cannot change opt-ins.
- The admin copilot may suggest tenant defaults; it never changes a user's own settings. A user's personal assistant may change that user's own non-consent preferences on request (for example "switch to dark mode"), audited as the user.

<!-- section:change_control -->
## Change control and audit

User changes are self-service, logged as `personal.preference_changed` (key and new value for non-sensitive keys). Opt-in and opt-out changes are audited with the consent record ID. Tenant default changes are standard audit class with a reason; they do not change values a user set explicitly. No maker-checker is needed in this catalogue, because no row weakens security or legal protections.

<!-- section:migration -->
## Versioning and migration

Keys never reused; renamed keys aliased for two releases. The `user_preferences` storage named in [[PKG-colour-modes-and-user]] becomes the `personal.appearance.*` and `personal.a11y.*` keys at level `user`. Personal values do not travel in configuration packages (they are personal data); tenant and unit defaults do. On membership deletion, user-scope rows are erased with the membership ([[PKG-retention-and-deletion-schedule]]).

<!-- section:testing -->
## Testing

Registry `packages/settings/registry/personal.ts`, CI comparison with this catalogue, and a test that every `personal.a11y.*`, language and time-zone key is `lockable: false`. Resolution tests for per-membership values and the "apply in region" action; opt-in tests requiring a consent record; reserved-key tests for shortcut overrides.

<!-- section:questions -->
## Open questions

- [ ] Should language and time zone follow the person across tenants in a region by default (proposed: per membership with the "apply in region" option)? (Product)
- [ ] Is `personal.privacy.usage_analytics = essential_only` enough to satisfy consent requirements for product analytics in each region, or is analytics opt-in needed in some? (Privacy owner)
- [ ] Should a dyslexia-friendly font option be offered? Depends on font licensing and the multi-script font stacks in [[PKG-typography-and-multi-script]]. (Accessibility lead)

<!-- checks -->
## Template checks

<!-- check:inheritance -->
### Inheritance and locks

Order is user → unit default → tenant default → platform default; accessibility, language and time zone are never lockable, so the user's choice always wins for them. Values are per membership and per region.

<!-- check:permissions -->
### Who may change what

Users change only their own values (`settings.personal:write` applied to self, user taken from the session); tenant and unit defaults need `settings.personal:write` held through an administrative role (`content_admin` or `tenant_admin`); admin credentials cannot write user-scope rows.

<!-- check:safety -->
### Safe bounds

No personal setting can bypass legal notices or security: mandatory notification channels cannot be removed, opt-ins require verified consent, and document download preference yields to tenant viewer-only locks.

<!-- check:timing -->
### When changes take effect

Stated per key; appearance and accessibility apply immediately without reload; language and formats on the next page load; notification choices on the next send.

<!-- check:audit -->
### Audit and rollback

Personal changes logged with key and time; consent changes with the consent record ID; tenant default changes audited with reason; values for a past date can be reproduced from versions.

<!-- check:sync -->
### Catalogue matches code

Generated registry checked in CI, including the non-lockable rule for accessibility, language and time-zone keys.

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C",
    "excerpt": "Includes SC 2.1.4 Character Key Shortcuts (single-key shortcuts can be turned off or remapped) and SC 2.2.1 Timing Adjustable.",
    "id": "R1",
    "ident": "WCAG 2.2",
    "kind": "standard",
    "title": "Web Content Accessibility Guidelines (WCAG) 2.2",
    "url": "https://www.w3.org/TR/WCAG22/",
    "version": "2.2"
  },
  {
    "body": "W3C",
    "excerpt": "Defines prefers-color-scheme, prefers-reduced-motion, prefers-contrast and forced-colors.",
    "id": "R2",
    "ident": "Media Queries 5",
    "kind": "standard",
    "title": "Media Queries Level 5",
    "url": "https://www.w3.org/TR/mediaqueries-5/"
  },
  {
    "excerpt": "Opt-in must state that the person agrees to receive WhatsApp messages and name the business; opt-out requests for message categories must be honoured.",
    "id": "R3",
    "kind": "vendor",
    "publisher": "Meta",
    "retrieved": "2026-10-28",
    "title": "WhatsApp Business Platform: Get opt-in for WhatsApp",
    "url": "https://developers.facebook.com/docs/whatsapp/overview/getting-opt-in"
  },
  {
    "id": "R4",
    "issuer": "Ministry of Electronics and Information Technology, India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 22 of 2023",
    "title": "Digital Personal Data Protection Act, 2023",
    "url": "https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf"
  }
]
```

<!-- end -->
