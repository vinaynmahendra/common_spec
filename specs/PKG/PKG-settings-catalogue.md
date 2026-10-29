---
id: "PKG-settings-catalogue"
title: "Settings catalogue (all levels)"
parent: "PKG-settings"
order: 3
type: "feature"
template: "design"
childTemplate: "config"
status: "draft"
owner: null
indicative: false
summary: "Index of every domain settings catalogue and the conventions they share: key grammar, column vocabulary, permissions, audit classes, effect timing, the settings information architecture in the consoles, the generated registry that keeps catalogues true to code, and the rule for what is (and is not) a setting"
links: []
rev: 1
syncHash: "38c9ce07f65ccd0a"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.7.3 Settings catalogue (all levels)

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Index of every domain settings catalogue and the conventions they share: key grammar, column vocabulary, permissions, audit classes, effect timing, the settings information architecture in the consoles, the generated registry that keeps catalogues true to code, and the rule for what is (and is not) a setting

<!-- section:context -->
## Context and scope

Settings are spread across every package: sign-in policy, case filing, notifications, branding, AI, retention, billing and more. Before this overhaul each package listed its own settings in a `config` section with its own columns and names (for example `auth.mfa.requiredForParties`, `notifications.quietHours`, `filing.maxUploadMb` in [[PKG-settings#consumers]]). Admins, engineers and auditors had no single place to see what can be configured, at which level, by whom, and with what effect.

This node is the **index** of the domain settings catalogues (template "Settings catalogue") and the **conventions** they must all follow. Behaviour stays in the owning package or feature node; the catalogue rows only register the setting. Resolution rules are in [[PKG-configuration-scope-hierarchy]], storage in [[PKG-settings-data-model]], and the change process in [[PKG-configuration-lifecycle]].

<!-- section:goals -->
## Goals and non-goals

**Goals**
- Every configurable setting at every scope is registered in exactly one domain catalogue, with the same columns and vocabulary.
- The tenant and platform consoles present settings with one information architecture, generated from the same registry.
- The catalogues cannot drift from code unnoticed.
- A reader can decide in under a minute whether a new configurable thing is a setting, a feature flag, an entitlement, a configuration artefact, deployment configuration or a secret.

**Non-goals**
- Specifying feature behaviour (owned by each feature node).
- Listing the content of artefacts (forms, blueprints, templates, decision tables), which have their own models.

<!-- section:design -->
## Design

### 1. Index of domain catalogues

| Key prefix | Catalogue | Owner group | Main consumers | Tenant console section |
|---|---|---|---|---|
| `platform.*` | [[PKG-settings-platform-operations]] | admin | Platform consoles, tenant lifecycle, support access, maintenance windows | Platform only (`/platform/settings`), except `platform.preview.*` (tenant opt-in to early-access features, [[PKG-feature-flags]]) shown under Organisation → Early access |
| `auth.*` | [[PKG-settings-security-and-identity]] | identity | [[PKG-authentication]], [[PKG-authentication-policies]], [[PKG-sso-saml-oidc-per-tenant]], [[PKG-mfa-session-management-device]] | Security and sign-in |
| `access.*` | [[PKG-settings-access-control]] | authz | [[PKG-authorization]], [[PKG-separation-of-duties]], [[PKG-jit-and-break-glass]], [[PKG-ethical-walls-conflict-based]] | Access and roles |
| `case.*`, `workflow.*` | [[PKG-settings-cases-and-workflows]] | workflow | [[DOM-cases]], [[WF-process-definition-model]], [[WF-sla-and-business-calendars]], [[WF-automation-rules]] | Cases and workflows |
| `notify.*` | [[PKG-settings-notifications]] | integrations | [[PKG-notifications]], [[PKG-notification-policies]] | Notifications |
| `integration.*` | [[PKG-settings-integrations]] | integrations | [[INT-integration-framework]], [[INT-connections-admin]], [[INT-public-api-and-webhooks]] | Integrations and API |
| `brand.*`, `content.*`, `locale.*` | [[PKG-settings-branding-content]] | config | [[PKG-branding-and-theming]], [[PKG-tenant-terminology-and-copy]], [[I18N-content]], [[I18N-l10n]] | Branding; Content and terminology; Language and region |
| `ai.*` | [[PKG-settings-ai]] | ai | [[AI-tenant-ai-policy]], [[AI-ai-gateway]], [[AI-agent-configuration]] | AI |
| `data.*` | [[PKG-settings-data-and-privacy]] | config | [[PKG-data-retention-legal-hold-and]], [[SEC-privacy-controls]], [[SEC-consent-and-notice-management]], [[PKG-storage]] | Data and privacy |
| `billing.*` | [[PKG-settings-billing-and-plans]] | config | [[BIL-plans-entitlements-and-usage]], [[BIL-invoicing-taxes-gst-singapore]], [[DOM-invoices-and-vendor-bills]] | Plan and billing |
| `personal.*` | [[PKG-settings-personal]] | integrations | [[PKG-personalisation]], [[PKG-notification-preferences]], [[PKG-colour-modes-and-user]] | Personal settings (each persona) |

A key belongs to the catalogue of its first segment. A key may be read by many packages but is owned by one.

### 2. Key grammar

`<domain>.<area>.<name>` and optionally one more segment: `<domain>.<area>.<sub>.<name>`; all segments `lower_snake`; regex `^(platform|auth|access|case|workflow|notify|integration|brand|content|locale|ai|data|billing|personal)(\.[a-z][a-z0-9_]*){2,3}$`. Units in the name where they matter: `_min`, `_hours`, `_days`, `_years`, `_mb`, `_pct`. Booleans read as statements: `content.terminology.allow_case_type_terms`, not `content.terminology.case_type_terms_flag`. Keys are never reused for a different meaning; retired keys stay reserved ([[PKG-settings#versioning]]).

### 3. Column vocabulary (every catalogue table uses these columns)

| Column | Allowed content |
|---|---|
| Key | The key in backticks |
| Type | `bool`; `int a–b`; `decimal a–b`; `duration a–b` (ISO 8601 in storage, shown in units); `time` (HH:MM, tenant or user time zone); `enum{a,b,c}`; `set⊆{…}` or `set⊆ref(kind)`; `text≤n`; `ltext≤n` (localised text, one value per enabled locale); `ref(kind)` (reference to an artefact or record by key); `object(name)` (named schema in the owning package) |
| Default | The code default (platform). Values set by blueprints are in the catalogue's `defaults` section, not here |
| Scopes | Ordered list using the scope keys: `platform`, `region`, `offering`, `tenant`, `unit`, `case_type`, `case`, `user` |
| Lock | `yes` (any listed scope may lock), `platform` (only Nomology scopes may lock), `no`, or `managed` (Nomology sets it at tenant scope for some tenant types) |
| Plan | `all`, or the entitlement key that gates it (`feature.*`), or the limit that bounds it (`≤ limit.*`) |
| Permission | Permission key to change it at tenant-side scopes (section 4) |
| Takes effect | `immediate` (≤ 5 s), `next_request`, `next_sign_in`, `new_cases_only` (pinned at case start; running cases keep their value), `running_cases` (applies to open cases at their next step), `next_billing_period`, `next_job_run`, `scheduled` (always needs an `effective_from`) |
| Audit | `standard`, `sensitive` (step-up and reason, admins notified), `maker_checker` (second approver), as defined in [[PKG-configuration-lifecycle#design]] |

Catalogues group settings into sub-tables of 5–20 rows by console page.

### 4. Permissions and roles

- **Change permission**: `settings.<catalogue>:write`, one per catalogue (`security`, `access`, `cases`, `workflow`, `notifications`, `integrations`, `branding`, `data`, `billing`, `ai`, `personal`, `platform`). There are no area-level sub-permissions; high-risk keys are protected by `maker_checker` instead. Approval of `maker_checker` items needs `settings.<catalogue>:approve` plus `config.change_set:approve` ([[PKG-permission-catalogue]]).
- **Read permission**: `settings.<catalogue>:read`. Every tenant administrative role can read every domain's non-secret settings; `auditor` can read all settings and their history.
- **Case scope**: `case:configure`, held through the `case_manager` case role.
- **User scope**: no permission; the user changes only their own `personal.*` values.
- **Platform scopes** (platform, region and offering values of any catalogue, and hard bounds): `settings.platform:write`, held by `platform_admin`, and by `regional_ops` for region values in their own region; changes to `auth.*` and `access.*` bounds need `platform_security` as checker.

Default holders of each catalogue's write permission (the permission sets are defined in [[PKG-roles-and-permission-sets#matrix]], which is authoritative; the full list is in [[PKG-permission-catalogue#matrix]], group G):

| Catalogue permission | Default roles (through permission set) |
|---|---|
| `settings.security:write`, `settings.access:write` | `security_admin` (`ps.admin.security`), `tenant_owner` |
| `settings.data:write` | `security_admin` (`ps.admin.data`), `tenant_owner`, `tenant_admin`; `privacy_officer` template |
| `settings.cases:write`, `settings.workflow:write` | `workflow_designer` and `tenant_admin` (`ps.admin.workflow`); `unit_admin` at unit scope (`ps.admin.unit_settings`) |
| `settings.notifications:write` | `integration_admin` for channels and senders (`ps.admin.integrations`), `content_admin` (`ps.admin.content`), `tenant_admin`; `unit_admin` at unit scope |
| `settings.integrations:write` | `integration_admin` and `tenant_admin` (`ps.admin.integrations`) |
| `settings.branding:write` | `content_admin` and `tenant_admin` (`ps.admin.content`); `unit_admin` at unit scope |
| `settings.ai:write` | `ai_admin` and `tenant_admin` (`ps.admin.ai`), `tenant_owner` |
| `settings.billing:write` | `billing_admin` (`ps.admin.billing`), `tenant_owner` |
| `settings.personal:write` | every member for their own values (`ps.personal.self`); tenant and unit defaults: `content_admin` and `tenant_admin` (`ps.admin.content`) |
| `settings.*:read` | every tenant administrative role and `auditor` (`ps.admin.settings_read`) |

### 5. Settings information architecture

Inspired by the clear split in collaboration tools between organisation settings, workspace settings and personal preferences (Linear, Notion, Slack Enterprise Grid), adapted to our scopes:

**Tenant admin console** ([[APP-tenant-admin-console]])
- `/admin/settings`: settings home with one search box over every setting's label, description and key; recent changes; pending reviews; badges for settings that need attention (drift, dormant values after a plan change).
- One page per console section in the index table, for example `/admin/settings/branding`, `/admin/settings/content/terminology`, `/admin/settings/locale`, `/admin/settings/data/retention`, `/admin/settings/data/privacy`, `/admin/settings/billing`.
- `/admin/organisation/units/[unitId]/settings`: only keys that allow `unit`, grouped the same way, with "inherits from tenant" shown per row.
- `/admin/config/effective`: the effective configuration explorer (choose a unit, case type, case or user; see value, source, lock and explanation for every key; [[PKG-configuration-scope-hierarchy]]).
- `/admin/changes`: change sets and review queue ([[PKG-configuration-lifecycle]]).

**Every settings row shows**: label and help text; the effective value; a source badge ("Platform default", "Set for India region", "Set for this organisation", "Set for Mumbai office", "Managed by Nomology"); a lock icon with its source; a plan badge when not entitled ("Available on Standard"); takes-effect text ("Applies to new cases only"); audit class hint ("Needs approval"); and a History link.

**Platform console** ([[APP-platform-admin-and-support]]): `/platform/settings` with a scope switcher (platform, region, offering) and a tenant-type selector for targeted values; `/platform/settings/catalogue` (browse the generated registry with owners and usage counts); `/platform/tenants/[tenantId]/config/effective`.

**Personal settings**: under each persona's own route group, owned by [[PKG-personalisation]].

**APIs**: `GET /admin/v1/settings?domain=<domain>` (effective values with source and lock), `GET /admin/v1/settings/{key}?unit=&caseType=&case=&user=` (with `explain`), `PATCH /admin/v1/settings/{key}` (creates a one-item change set; returns `200` when published, `202` with the change set when review is needed), and the change-set endpoints of [[PKG-configuration-lifecycle]]. Platform: `/platform/v1/settings/...` with the same shapes.

**Admin copilot**: may read any setting the invoking human may read, explain values, and draft change sets; it cannot publish ([[APP-admin-copilot]]).

### 6. Generated registry and catalogue sync

- Every `defineSetting` call is collected at build time into `packages/settings-registry/dist/registry.json` (key, type, default, scopes, lock, entitlement, permission, takes effect, audit class, pinning, owner, catalogue node ID).
- CI job `settings:registry-check` fails when: a definition has no `catalogueNode`; a key violates the grammar; a key's prefix does not match its catalogue; a definition's schema narrows without a value migration; or a key's permission is not in the permission catalogue.
- CI also renders `docs/settings/catalogue.generated.md`; a weekly job compares it with the catalogue tables exported from the spec workspace and opens an issue listing keys in code but not in a catalogue, and catalogue rows with no code definition.
- At deploy, `config-registry-sync` loads the registry into `config.setting_definition` ([[PKG-settings-data-model]]), so the consoles and the platform catalogue browser always show the running release.

### 7. What is a setting (decision rule)

| If the thing… | It is a… | Lives in |
|---|---|---|
| is a tenant's (or unit's, case's, user's) choice about behaviour they already have | **Setting** | A domain catalogue, `@nomology/settings` |
| controls whether code that is being rolled out runs, for whom, temporarily | **Release, operational or migration flag** | [[PKG-feature-flags]] |
| decides whether a tenant has paid for a capability or how much of it | **Entitlement** (feature or limit) | [[BIL-plans-entitlements-and-usage]] |
| is a structured, versioned document with its own editor (form, blueprint, template, decision table, theme, role) | **Configuration artefact** | [[PKG-configuration-and-customisation]] and children |
| differs by environment or region of the deployment (endpoints, pool sizes, provider accounts) | **Deployment configuration** | [[FND-environment-management]] |
| is a credential | **Secret** | [[INF-secrets-and-keys]] |
| decides who may do what | **Role, permission set or policy** | [[PKG-roles-and-permission-sets]] |

A capability often needs several: "WhatsApp notices" is a release flag (`notify.whatsapp.enabled`, until rolled out), an entitlement (`feature.notify.whatsapp`), and settings (`notify.channel.whatsapp.enabled`, quiet hours). It is available only if all three allow it ([[BIL-plans-entitlements-and-usage#entitlements]], BIL-ENT-8).

<!-- section:examples -->
## Worked examples

**Reading a catalogue row**

| Key | Type | Default | Scopes | Lock | Plan | Permission | Takes effect | Audit |
|---|---|---|---|---|---|---|---|---|
| `data.retention.case_record_years` | int 1–30 | 8 | platform, region, tenant | managed | all | `settings.data:write` | `running_cases` | `maker_checker` |

Read as: Nomology sets a default of 8 years; a region may change it; the tenant may change it; Nomology may set a managed minimum for some tenant types; any plan; changing it needs the retention permission; it applies to open cases (their retention end date is recomputed); and a second person must approve.

**Adding a new setting (engineer)**
1. Decide it is a setting (section 7).
2. Choose the key in the right domain and add `defineSetting({ key, schema, default, scopes, lockable, entitlement, pinning, auditClass, permission, takesEffect, catalogueNode, ... })` in the owning package.
3. Add the row to the domain catalogue node, plus blueprint defaults if they differ.
4. CI checks grammar, catalogue node and permission; the deploy job syncs the definition; the setting appears in the console section automatically.

<!-- section:alternatives -->
## Alternatives considered

| Option | Why not chosen |
|---|---|
| One giant catalogue node | Too large to review and owned by nobody; domain owners would not maintain it. |
| Settings documented only in code (generated catalogue only) | Loses the review of defaults by tenant type, the validation rules between settings and the legal reasoning, which belong in the spec. We keep both and check them against each other. |
| Console pages hand-built per domain | Inconsistent presentation of inheritance and locks; every new setting needs UI work. Pages are generated from the registry, with custom editors only for complex types (`object`). |
| Configuration grouped by persona instead of domain | Admin personas overlap (a small tenant has one admin); grouping by domain with role-based visibility works for small and large tenants. |

<!-- section:crosscutting -->
## Cross-cutting concerns

| Concern | How the conventions address it |
|---|---|
| Security | Every key names its change permission and audit class; `sensitive` and `maker_checker` force step-up and review; secrets are never settings. |
| Privacy | Values must not contain personal data; `personal.*` keys are the only user-scope personal data and follow the membership's retention. |
| Tenancy | Platform scopes are administered only in the platform console; tenant pages never show other tenants' values. |
| Observability | Registry usage counts (`config.setting.reads` sampled per key) let owners find unused settings to retire. |
| Accessibility | Generated pages use the design-system form fields ([[PKG-form-fields]]); source and lock badges are text, not colour only. |

<!-- section:guardrails -->
## Guardrails

- **CAT-G-1** No setting without a catalogue row and a definition; CI enforces both directions weekly.
- **CAT-G-2** No key outside the fourteen domains.
- **CAT-G-3** A key that affects a party's procedural rights uses `new_cases_only` unless the catalogue explains why not ([[PKG-configuration-scope-hierarchy]], SCOPE-G-3).
- **CAT-G-4** A catalogue lists behaviour in one line and links the owning node; it does not re-specify behaviour.
- **CAT-G-5** Defaults that differ by tenant type are set by blueprints, never by code branches on tenant type.

<!-- section:ownership -->
## Ownership

This index and the conventions: configuration group (platform engineering). Each domain catalogue: the owner group in the index table. Changes to conventions need agreement of all catalogue owners and an update to the shared model.

<!-- section:questions -->
## Open questions

- [ ] Should a dedicated tenant role for privacy (for example `privacy_officer`) own `data.*` instead of `security_admin`? Many institutions name a grievance or data protection officer. (owner: authz group, DPO)
- [x] Settings permissions are `settings.<catalogue>:write` and `settings.<catalogue>:approve` (decision D2); see section 4.
- [ ] Should tenants see the settings of features they are not entitled to (with an "upgrade" badge) or should those be hidden? Proposed: shown, read-only, for discoverability; hidden for court programmes. (owner: product)

<!-- checks -->
## Template checks

<!-- check:security -->
### Security and privacy

The conventions make permission and audit class mandatory columns, so no setting exists without a defined change permission; CI rejects definitions whose permission is not in the permission catalogue. Secret-like keys fail the lint. Generated console pages call the same admin operations as the API, so there is no UI-only path that skips checks.

<!-- check:tenancy -->
### Tenancy

All tenant-side catalogue pages resolve values in the active tenant's context; platform scopes are only editable in the platform console. The registry itself contains no tenant data.

<!-- check:residency -->
### Data residency and lifecycle

The registry is code and is identical in every region; values are regional ([[PKG-settings-data-model]]). Region-scope values are the only place where regional legal defaults differ, and they are visible in the platform console per region.

<!-- check:failure -->
### Failure handling and recovery

If the registry sync fails at deploy, the release does not start serving (the deploy job gates on it), so code never reads a key the database does not know. If a catalogue node is out of date, the weekly comparison opens an issue; running behaviour follows code.

<!-- check:rollout -->
### Rollout and migration

Domain catalogues are introduced with this overhaul; existing keys are renamed to the grammar through the mapping in [[PKG-settings-data-model#migrations]]. The generated pages replace hand-built settings pages section by section behind release flag `admin.settings.generated_pages`.

<!-- check:reversibility -->
### Reversibility

Hard to change: the fourteen domains and the key grammar (keys are stored in data and referenced in packages and blueprints). Easy to change: console grouping, labels and the permission-set mapping.

<!-- end -->
