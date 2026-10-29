---
id: "PKG-settings-integrations"
title: "Integration settings"
parent: "PKG-settings-catalogue"
order: 7
type: "feature"
template: "config"
status: "draft"
owner: null
indicative: false
summary: "Catalogue of 64 integration settings: connector availability, connection defaults per scope, ownership models, credential rotation, health, usage budgets, data policy switches, external apps and plugins, public API, webhooks and calendar"
links: []
rev: 1
syncHash: "303bc41b99108de8"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.7.3.7 Integration settings

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Catalogue of 64 integration settings: connector availability, connection defaults per scope, ownership models, credential rotation, health, usage budgets, data policy switches, external apps and plugins, public API, webhooks and calendar

<!-- section:purpose -->
## Purpose and scope

Settings for connections to outside providers, connector data policy switches, external apps and plugins, our public API and outbound webhooks, and calendar integration. Consumed by [[INT-integration-framework]], [[INT-connections-admin]], [[INT-connector-data-policies]], [[INT-plugin-model]], [[INT-public-api-and-webhooks]], [[APP-webhooks-outbound]] and [[INT-common-integrations]].

Not here: credentials and secrets (regional secrets manager, referenced from connections); API client and key policy such as key lifetime, IP restrictions and allowed authentication methods ([[PKG-settings-security-and-identity]], [[PKG-api-clients-and-keys]]); connector data policy **rules** (versioned artefacts in [[INT-connector-data-policies]]); AI provider choices ([[PKG-settings-ai]]); release flags for new connectors ([[PKG-feature-flags]]); connector code and catalogue entries (code plus platform tables). Keys with `<connector_key>` or `<category>` are templated: one row in the registry generates a key per connector or category.

<!-- section:scopes -->
## Scopes that apply

| Scope | Used | Administered by | Notes |
|---|---|---|---|
| `platform` | yes | `platform_admin` (maker), `platform_security` (checker) | Availability, hard bounds, locked behaviours |
| `region` | yes | `regional_ops` | Availability per region, in-region requirement, health intervals |
| `offering` | yes | `platform_admin` | Catalogue visibility for CORD vs TERES |
| `tenant` | yes | `integration_admin`, `tenant_admin`; `security_admin` for data policy switches | Most keys |
| `unit` | yes | `unit_admin` where `integration.connection.unit_admin_can_toggle` is true | Default connections, alert recipients, budgets |
| `case_type` | yes | `workflow_designer` | Default connection per category for the blueprint (pinned at case start) |
| `case` | no | — | Which connection a case uses is pinned from its blueprint; changing it is a migration, not a setting |
| `user` | no | — | Per-user connected accounts are records, not settings ([[PKG-personalisation]]) |

<!-- section:catalogue -->
## Settings catalogue

64 settings in nine groups. Columns as in [[PKG-settings-catalogue]]; audit classes standard, sensitive (reason required) and maker-checker.

**A. Catalogue and availability**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `integration.connector.<connector_key>.availability` | enum: available, beta, hidden, retired | from catalogue entry | platform, region, offering | yes | per entry | `settings.platform:write` | immediately (new connections); retired: no new calls after notice date | maker-checker |
| `integration.catalogue.visible_categories` | set of categories | all available | platform, offering, tenant | yes | all | `settings.integrations:write` | immediately | standard |
| `integration.catalogue.beta_opt_in` | bool | false | tenant | no | all | `settings.platform:write` (on tenant request) | immediately | sensitive |
| `integration.connection.ownership_models_allowed` | set: platform_managed, tenant_byo, user_connected | `[platform_managed]` | platform, region, tenant | yes | `tenant_byo`: `feature.byo_providers` | `settings.integrations:write` | new connections | maker-checker |
| `integration.connection.byo_categories` | set of categories | `[payments, calendar]` | platform, tenant | yes | `feature.byo_providers` | `settings.integrations:write` | new connections | maker-checker |
| `integration.connection.max_per_tenant` | int 1–200 | 50 | platform, tenant | yes | plan ceiling | `settings.integrations:write` | new connections | standard |

**B. Connections: defaults, units and ownership**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `integration.default_connection.<category>` | connection ID | platform-managed regional connection | tenant, unit, case_type | yes | all | `settings.integrations:write`; case type: `workflow.definition:update` | new work (running work keeps its connection) | sensitive |
| `integration.default_connection.<category>.secondary` | connection ID or none | none | tenant, unit | yes | all | `settings.integrations:write` | new work | sensitive |
| `integration.connection.unit_enablement_mode` | enum: all_units, selected_units | all_units | tenant | no | all | `settings.integrations:write` | immediately | standard |
| `integration.connection.unit_admin_can_toggle` | bool | false | tenant | no | all | `settings.integrations:write` | immediately | standard |
| `integration.connection.require_owner_and_backup` | bool | true | platform, tenant | yes | all | `settings.integrations:write` | new connections; existing flagged | standard |
| `integration.connection.require_service_account_oauth` | set of categories | `[accounting, esign, payments]` | platform, tenant | yes | all | `settings.integrations:write` | next connect or reconnect | sensitive |
| `integration.connection.user_connected_categories` | set of categories | `[]` (calendar when enabled) | platform, tenant | yes | all | `settings.integrations:write` | immediately | sensitive |

**C. Credentials and health**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `integration.credential.rotation_days` | int 30–365 | 90 | platform, tenant | yes (platform ceiling) | all | `settings.integrations:write` | next rotation date calculation | sensitive |
| `integration.credential.expiry_warning_days` | int 3–60 | 14 | tenant | no | all | `settings.integrations:write` | next daily scan | standard |
| `integration.credential.reconnect_grace_days_after_grantor_leaves` | int 0–30 | 7 | platform, tenant | yes | all | `settings.integrations:write` | next deprovisioning event | sensitive |
| `integration.health.check_interval_min` | int 5–60 | 15 | platform, region | yes | all | `settings.platform:write` | next schedule | standard |
| `integration.health.failures_before_failing` | int 2–10 | 3 | platform, tenant | yes | all | `settings.integrations:write` | next probe | standard |
| `integration.health.degraded_error_rate_pct` | number 1–50 | 10 | platform, tenant | yes | all | `settings.integrations:write` | next evaluation (5 min) | standard |
| `integration.health.auto_suspend_after_hours_failing` | int 0 (never) – 168 | 0 | tenant | no | all | `settings.integrations:write` | next evaluation | sensitive |
| `integration.health.alert_recipients` | set: owner, backup_owner, role keys | `[owner, backup_owner, integration_admin]` | tenant, unit | no | all | `settings.integrations:write` | immediately | standard |

**D. Usage budgets**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `integration.usage.sms_segments.monthly_cap` | int ≥ 0 | plan entitlement | tenant, unit | no | entitlement ceiling | `settings.integrations:write` | immediately | standard |
| `integration.usage.esign_envelopes.monthly_cap` | int ≥ 0 | plan entitlement | tenant, unit | no | entitlement ceiling | `settings.integrations:write` | immediately | standard |
| `integration.usage.kyc_checks.monthly_cap` | int ≥ 0 | plan entitlement | tenant | no | entitlement ceiling | `settings.integrations:write` | immediately | standard |
| `integration.usage.video_minutes.monthly_cap` | int ≥ 0 | plan entitlement | tenant, unit | no | entitlement ceiling | `settings.integrations:write` | immediately | standard |
| `integration.usage.alert_thresholds_pct` | list of int | `[80, 100]` | tenant | no | all | `settings.integrations:write` | next roll-up | standard |

**E. Data policies (switches only; rules are artefacts in [[INT-connector-data-policies]])**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `integration.data_policy.default_group_new_connectors` | enum: blocked, metadata_only | blocked | platform, region, tenant | yes (tenant may only choose stricter) | all | `integration.data_policy:publish` | next connector publication | maker-checker |
| `integration.data_policy.exemptions_allowed` | bool | true | platform, tenant | yes | all | `integration.data_policy:publish` | immediately | maker-checker |
| `integration.data_policy.exemption_max_days` | int 1–90 | 30 | platform, tenant | yes | all | `integration.data_policy:publish` | new exemptions | maker-checker |
| `integration.data_policy.require_in_region` | bool | true | platform, region, tenant | yes | all | `integration.data_policy:publish` | new connections and next evaluation | maker-checker |
| `integration.data_policy.cross_border_requires_platform_approval` | bool | false (true for SEBI ODR blueprint) | platform, tenant | yes | all | `settings.platform:write` | new transfer records | maker-checker |
| `integration.data_policy.no_training_attestation_required` | bool | true | platform | yes (locked true) | all | `settings.platform:write` | immediately | maker-checker |
| `integration.generic_http.enabled` | bool | false | platform, tenant | yes | `feature.automation_http` | `integration.data_policy:publish` | immediately | maker-checker |
| `integration.generic_http.host_allowlist` | list of hostnames (no IPs, no wildcards above second level) | `[]` | tenant | no | `feature.automation_http` | `integration.data_policy:publish` | immediately | maker-checker |

**F. External apps and plugins ([[INT-plugin-model]])**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `integration.apps.install_policy` | enum: disabled, admins_only, request_and_approve | admins_only | platform, tenant | yes | `feature.public_api` | `settings.integrations:write` | immediately | sensitive |
| `integration.apps.request_requires_justification` | bool | true | tenant | no | `feature.public_api` | `settings.integrations:write` | immediately | standard |
| `integration.apps.approvers` | set of role keys | `[integration_admin, security_admin]` | tenant | no | `feature.public_api` | `settings.integrations:write` | immediately | sensitive |
| `integration.apps.max_scopes` | set of public API scopes | all non-admin scopes | platform, tenant | yes | `feature.public_api` | `settings.integrations:write` | new installs and upgrades | maker-checker |
| `integration.apps.auto_upgrade` | enum: off, patch, minor | patch | tenant | no | all | `settings.integrations:write` | next published version | standard |
| `integration.apps.scope_change_requires_review` | bool | true | platform | yes (locked true) | all | `settings.platform:write` | immediately | maker-checker |
| `integration.plugins.allow_tenant_private` | bool | true (configuration kinds only) | platform, tenant | yes | all | `settings.integrations:write` | immediately | sensitive |
| `integration.plugins.private_publishers` | set: tenant_admin, nomology_implementation | `[nomology_implementation]` | platform, tenant | yes | all | `settings.integrations:write` | immediately | sensitive |

**G. Public API**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `integration.api.enabled` | bool | false | tenant | yes | `feature.public_api` | `settings.integrations:write` | immediately | sensitive |
| `integration.api.sandbox_enabled` | bool | true | tenant | no | `feature.public_api` | `settings.integrations:write` | immediately | standard |
| `integration.api.pinned_version` | date-named version | latest at enablement | tenant | no | `feature.public_api` | `settings.integrations:write` | immediately for new requests without a version header | sensitive |
| `integration.api.rate_limit.reads_per_min` | int ≤ entitlement | entitlement (`limit.api_rpm`) | tenant | no | entitlement ceiling | `settings.integrations:write` | within 60 s | standard |
| `integration.api.rate_limit.writes_per_min` | int ≤ entitlement | entitlement | tenant | no | entitlement ceiling | `settings.integrations:write` | within 60 s | standard |
| `integration.api.deprecation_contacts` | list of user IDs or emails | tenant admins with API clients | tenant | no | `feature.public_api` | `settings.integrations:write` | immediately | standard |

**H. Webhooks ([[APP-webhooks-outbound]])**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `integration.webhooks.enabled` | bool | false | tenant | yes | `feature.webhooks` | `settings.integrations:write` | immediately | sensitive |
| `integration.webhooks.max_endpoints` | int 1–50 | 10 | platform, tenant | yes | plan ceiling | `settings.integrations:write` | new endpoints | standard |
| `integration.webhooks.allowed_event_types` | set of event types or `*` | `*` | tenant | no | `feature.webhooks` | `settings.integrations:write` | next delivery fan-out | standard |
| `integration.webhooks.retry_window_hours` | int 24–168 | 72 | platform, tenant | yes | all | `settings.integrations:write` | deliveries created after the change | standard |
| `integration.webhooks.failure_alert_after_hours` | int 1–72 | 24 | tenant | no | all | `settings.integrations:write` | next evaluation | standard |
| `integration.webhooks.auto_disable_after_hours` | int 24–168 (≥ retry window) | 72 | tenant | no | all | `settings.integrations:write` | next evaluation | standard |
| `integration.webhooks.alert_recipients` | set of role keys or user IDs | `[integration_admin]` | tenant | no | all | `settings.integrations:write` | immediately | standard |
| `integration.webhooks.secret_rotation_overlap_hours` | int 1–168 | 24 | tenant | no | all | `settings.integrations:write` | next rotation | sensitive |
| `integration.webhooks.bulk_replay_approval_threshold` | int events | 1000 | platform, tenant | yes | all | `settings.integrations:write` | next replay request | sensitive |
| `integration.webhooks.replay_window_days` | int 1–30 | 30 | platform | yes | all | `settings.platform:write` | immediately | standard |
| `integration.webhooks.payload_mode` | enum: thin | thin | platform | yes (locked) | all | `settings.platform:write` | — | maker-checker |
| `integration.webhooks.allow_non_443_ports` | bool | false | platform, tenant | yes | all | `settings.platform:write` on tenant request | new endpoints | maker-checker |
| `integration.webhooks.delivery_log_retention_days` | int 7–90 | 30 | platform, tenant | yes | all | `settings.integrations:write` | next nightly clean-up | standard |

**I. Calendar**

| Key | Type and allowed values | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `integration.calendar.ics_attachments` | bool | true | tenant, unit | no | all | `settings.integrations:write` | next hearing notice | standard |
| `integration.calendar.user_sync_enabled` | bool | false | tenant | yes | `feature.calendar_sync` | `settings.integrations:write` | immediately | sensitive |
| `integration.calendar.sync_scope` | enum: free_busy_only | free_busy_only | platform | yes (locked) | all | `settings.platform:write` | — | maker-checker |

<!-- section:validation -->
## Validation and dependencies

- `integration.default_connection.<category>` must reference an `active` connection of that category, enabled for the unit (if unit scope), with a data policy group that allows the category's required data kinds; otherwise `integration-default-invalid`.
- `.secondary` must have the same category and a different ownership model or provider; it is used only for the classes listed in `notify.channel.secondary_connection_allowed_classes` ([[PKG-settings-notifications]]).
- `tenant_byo` in `integration.connection.ownership_models_allowed` requires entitlement `feature.byo_providers`; adding a category to `integration.connection.byo_categories` that has no BYO-capable connector in the region fails.
- `integration.webhooks.auto_disable_after_hours` ≥ `integration.webhooks.retry_window_hours`.
- `integration.generic_http.enabled = true` requires a non-empty `integration.generic_http.host_allowlist`; hosts must resolve to public addresses at save time and are re-checked before each call.
- `integration.data_policy.default_group_new_connectors` at tenant can only be equal to or stricter than the platform value.
- `integration.apps.max_scopes` can never include admin scopes unless the app is installed by `tenant_owner` with maker-checker.
- Effective API limits = `min(entitlement, setting)`.
- Platform bounds: webhook retry window 24–168 h, replay window ≤ 30 days, payload mode thin only, calendar sync free / busy only, no-training attestation always required.

<!-- section:defaults -->
## Defaults by tenant type

| Key | Arbitral institution | SEBI ODR institution | CORD tenant | Court or government programme |
|---|---|---|---|---|
| `integration.connection.ownership_models_allowed` | platform_managed, tenant_byo | platform_managed, tenant_byo | platform_managed | platform_managed, tenant_byo |
| `integration.connection.byo_categories` | payments, esign, calendar | payments, messaging | — | messaging, payments |
| `integration.data_policy.cross_border_requires_platform_approval` | false | true | false | true |
| `integration.api.enabled` | true | true (aggregator intake) | false | false |
| `integration.webhooks.enabled` | true | true | false | false |
| `integration.webhooks.retry_window_hours` | 72 | 72 | 72 | 168 (weekend maintenance windows) |
| `integration.apps.install_policy` | request_and_approve | admins_only | disabled | admins_only |
| `integration.calendar.user_sync_enabled` | true (neutrals) | false | false | false |
| `integration.health.auto_suspend_after_hours_failing` | 0 | 0 | 0 | 0 |

Arbitral institutions integrate their own case management systems and apps; SEBI ODR institutions connect to aggregators such as NSE and send high SMS volumes, and their cross-border transfers get Nomology security review; CORD tenants use platform-managed providers with no developer surface; court programmes often bring government messaging gateways and need longer webhook retries.

<!-- section:admin_ux -->
## Where it is administered

| Group | Console | API |
|---|---|---|
| A, B, C, D | `/admin/integrations` (catalogue), `/admin/integrations/connections/[connectionId]` (configuration, units, health, usage), `/admin/integrations/defaults` | `/admin/v1/integrations/...`, `PATCH /admin/v1/settings/integration.*` |
| E | `/admin/integrations/data-policies` (switches beside the policy editor) | `/admin/v1/integrations/data-policies` |
| F | `/admin/integrations/apps` (installed, requests, catalogue) | `/admin/v1/integrations/apps` |
| G | `/admin/integrations/api` (overview); API clients at `/admin/integrations/api-clients` ([[PKG-api-clients-and-keys]]) | `/admin/v1/settings/integration.api.*` |
| H | `/admin/integrations/webhooks`, `/admin/integrations/webhooks/[endpointId]` | `/admin/v1/webhook-endpoints` and settings |
| I | `/admin/integrations/calendar` | settings |
| Platform, region, offering | `/platform/integrations/connectors`, `/platform/integrations/regions/[region]` | `/platform/v1/settings/integration.*` |

Inherited and locked values show their source and lock. The admin copilot may draft changes (for example "set the Singapore office default e-sign connection") for human approval; it may never write credentials or approve maker-checker rows.

<!-- section:change_control -->
## Change control and audit

Maker-checker rows need `settings.integrations:approve` (or `integration.data_policy:approve` for group E) held by someone other than the author. Changes that widen what leaves the platform (BYO models, generic HTTP, app scopes, data policy switches) notify the `tenant_owner` and `security_admin`. Rollback publishes the previous version; changes to defaults never move running work to a different connection. Audit records hold key, scope, old and new value, actor, approver, reason and version.

<!-- section:migration -->
## Versioning and migration

Templated keys are generated per connector and category; retiring a connector moves its availability to `retired` with a notice date and lists tenants and blueprints still using it. Settings travel in configuration packages; connection IDs are remapped on import and imported connections start `pending_authorisation`. Existing free-form framework settings in [[INT-integration-framework#config]] are replaced by these keys.

<!-- section:testing -->
## Testing

Registry `packages/settings/registry/integration.ts` generates the templated keys; CI compares it with this catalogue. Resolution tests: case-type default pinned at case start; unit default only when the connection is enabled for the unit; data policy switch at tenant cannot loosen platform. Each validation rule has a negative test, and webhook retry and auto-disable interplay is tested with fake time.

<!-- section:questions -->
## Open questions

- [ ] Webhook retry window: platform maximum 168 hours, or longer for court programmes? Stripe-style platforms retry for up to 3 days [R1]. (Product)
- [ ] App install requests by non-admins (for example counsel requesting a practice-management app): keep admins only, as in workspace app-approval models where members request and owners approve [R2]? (Product)
- [ ] Should calendar sync ever go beyond free / busy (for example writing hearing events), given `.ics` attachments [R3] already cover invites? (Product)

<!-- checks -->
## Template checks

<!-- check:inheritance -->
### Inheritance and locks

Scopes are explicit per key; templated keys inherit the row's scope rules; case-type defaults are pinned at case start; unit defaults apply only where the connection is enabled for that unit.

<!-- check:permissions -->
### Who may change what

`settings.integrations:write` (tenant and unit), `integration.data_policy:publish` for data policy switches, `workflow.definition:update` for case-type defaults, `settings.platform:write` for platform rows; approvals with matching `:approve` permissions; credentials are never settings.

<!-- check:safety -->
### Safe bounds

Hard bounds on retries, replay and payload mode; thin webhooks locked; generic HTTP off by default with allow-list; no-training attestation locked; data policy switches can only tighten below platform; BYO categories need entitlement and a capable connector.

<!-- check:timing -->
### When changes take effect

Stated per key; connection defaults affect new work only; rate limits apply within 60 seconds; webhook retry changes apply to new deliveries.

<!-- check:audit -->
### Audit and rollback

Versioned changes with actor, approver, reason and values; rollback one action; connection-level actions additionally audited in [[INT-connections-admin]].

<!-- check:sync -->
### Catalogue matches code

Generated registry including templated keys checked in CI; new connectors cannot publish without their availability rows.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Endpoints choose an API version and event types; deliveries are listed with attempts; live-mode retries continue for up to 3 days with exponential backoff; individual events can be retried manually; disabled destinations do not receive events generated while disabled.",
    "id": "R1",
    "kind": "vendor",
    "publisher": "Stripe",
    "retrieved": "2026-10-28",
    "title": "Manage event destinations",
    "url": "https://docs.stripe.com/workbench/event-destinations"
  },
  {
    "excerpt": "Owners can allow only pre-approved apps, route member requests to app managers, restrict apps, and approving an app means approving the scopes it will use.",
    "id": "R2",
    "kind": "vendor",
    "publisher": "Slack",
    "retrieved": "2026-10-28",
    "title": "Manage app approval for your workspace",
    "url": "https://slack.com/help/articles/222386767-Manage-app-approval-for-your-workspace"
  },
  {
    "body": "IETF",
    "id": "R3",
    "ident": "RFC 5545",
    "kind": "standard",
    "title": "Internet Calendaring and Scheduling Core Object Specification (iCalendar)",
    "url": "https://www.rfc-editor.org/rfc/rfc5545"
  }
]
```

<!-- end -->
