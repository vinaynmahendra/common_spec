---
id: "INT-connections-admin"
title: "Integration connections administration"
parent: "INT-integration-framework"
order: 1
type: "feature"
template: "integration"
status: "draft"
owner: null
indicative: false
summary: "Connector catalogue, per-tenant and per-unit connections with credentials held as secret references, OAuth connections, health, usage, defaults per scope, rotation and revocation: how admins at every scope manage outside-provider connections"
links: []
rev: 1
syncHash: "d6e3f8d8d8cd444a"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 9.1.1 Integration connections administration

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Connector catalogue, per-tenant and per-unit connections with credentials held as secret references, OAuth connections, health, usage, defaults per scope, rotation and revocation: how admins at every scope manage outside-provider connections

<!-- section:purpose -->
## Purpose and use cases

How administrators at every scope find, connect, configure, monitor, enable and retire **connections** to outside providers. The mechanics (connector interface, vault, inbound receiver, call wrapper) are in [[INT-integration-framework]]; what data a connection may receive is decided by [[INT-connector-data-policies]]; the settings keys are in [[PKG-settings-integrations]]. This node owns the administration model on top of them.

**Concepts**

| Term | Meaning |
|---|---|
| Connector | A provider adapter written and certified by Nomology (for example a regional email service, an Aadhaar eSign ESP, a video provider, Odoo). Code, not configuration. |
| Catalogue entry | The platform record that describes a connector to admins: category, regions, offerings, plan entitlement, ownership models, auth kinds, data manifest, sub-processor ID, accessibility record, status (`certified`, `beta`, `deprecated`, `retired`). |
| Connection | A configured instance of a connector for one tenant (or for the platform in one region): endpoint and non-secret configuration, a credential reference, an owner, an enablement list and a health state. |
| Credential | The secret part of a connection, held only in the regional secrets manager and referenced by `secret_ref`. One connection has one **named** credential (shared by all its uses) and may allow **per-user** credentials (for example a neutral's own calendar). Pattern borrowed from: the split between named credentials (endpoint) and external credentials (authentication and principals) in Salesforce [R1]. |
| Ownership model | `platform_managed` (Nomology's regional account, tenant is a sub-account or tagged), `tenant_byo` (tenant's own provider contract and account), `user_connected` (one person's account, calendar only at first). |

**Use cases**
1. A tenant integration admin at a SEBI ODR institution switches SMS from the platform-managed Indian aggregator to the institution's own DLT-registered account, tests it, and enables it for the "SEBI ODR desk" unit only.
2. An arbitral institution connects its own e-signature account for awards, while the Singapore office (a unit) keeps the platform-managed account.
3. A workflow designer chooses which enabled e-sign connection the "Institutional arbitration (expedited)" case-type blueprint uses.
4. A platform admin marks a video connector `deprecated` in the US region and sees which tenants and case types still depend on it.
5. A neutral connects their own calendar for free / busy lookup; the tenant has allowed `user_connected` calendar connections.
6. An auditor exports the connection inventory with owners, last credential rotation and data policy group for an ISO 27001 supplier review.

**Where it is administered**

| Scope | Console route | Who (role keys) | Admin API |
|---|---|---|---|
| `platform` | `/platform/integrations/connectors` (catalogue, certification, status), `/platform/integrations/connections` (platform-managed accounts per region; cross-tenant health view with tenant names masked unless under break-glass) | `platform_admin`, `platform_security` (read), `platform_support` (health read only) | `/platform/v1/integrations/connectors`, `/platform/v1/integrations/connections` |
| `region` | `/platform/integrations/regions/[region]` (availability, regional platform accounts, egress allow-list status) | `regional_ops` | `/platform/v1/integrations/regions/{region}` |
| `offering` | Catalogue entry, "Offerings" tab | `platform_admin` | same as platform |
| `tenant` | `/admin/integrations` (catalogue), `/admin/integrations/connections`, `/admin/integrations/connections/[connectionId]` (overview, configuration, credential, units, usage, health, activity), `/admin/integrations/defaults` | `integration_admin`, `tenant_admin`, `tenant_owner`; `auditor` and `security_admin` read | `/admin/v1/integrations/...` ([[INT-tenant-admin-api]]) |
| `unit` | `/admin/organisation/units/[unitId]/integrations` | `unit_admin` (toggle only where the tenant allowed it) | `/admin/v1/units/{unitId}/integrations` |
| `case_type` | Blueprint editor, "Integrations" panel in [[WF-workflow-authoring-studio]] | `workflow_designer` | part of the blueprint ([[WF-process-definition-model]]) |
| `user` | `/me/settings/connected-accounts` ([[PKG-personalisation]]) | the user | tRPC `me.connectedAccounts.*` |

Not here: our own API clients and keys ([[PKG-api-clients-and-keys]]), webhook endpoints ([[APP-webhooks-outbound]]), installed external apps ([[INT-plugin-model]]), AI model providers ([[AI-ai-gateway]], [[AI-tenant-ai-policy]]), SSO identity providers ([[PKG-sso-saml-oidc-per-tenant]]).

<!-- section:party -->
## External party and ownership

| Item | Value |
|---|---|
| External parties | Every provider in [[INT-common-integrations]] (video, e-sign, KYC and sanctions, messaging, accounting, payments, calendar). For `tenant_byo` connections, the tenant's own provider contract is the external party; Nomology is not a party to it. |
| Owner of the administration model | Platform engineering (integrations team); product owners for CORD and TERES approve catalogue visibility per offering |
| Contract owner | `platform_managed`: NTPL, TAPL or the US entity per region (as recorded in [[SEC-vendor-sub-processor-management]]); `tenant_byo`: the tenant; `user_connected`: the user under the provider's own terms |
| Accountable at tenant | The connection's **owner** (a named person with `integration_admin`), plus a backup owner; both receive health and expiry alerts |
| Environments | Each connection belongs to one environment (`live` or `sandbox`). Sandbox connections exist in the tenant's sandbox configuration ([[PKG-configuration-lifecycle]]) and may only point at provider sandboxes; production credentials are unreadable from non-production stacks |
| Support path | Provider-side faults on `platform_managed` connections: Nomology support. On `tenant_byo` connections: tenant contacts its provider; Nomology support sees health and call logs only |

The catalogue entry records, per connector: provider legal name, sub-processor ID, regions with in-region processing, certification status, last security review date, accessibility record ([[INT-third-party-component]]) and the documentation link shown to tenant admins.

<!-- section:flows -->
## Data flows

| # | Flow | Direction | Trigger | Mode | Runs in |
|---|---|---|---|---|---|
| 1 | Browse catalogue | internal | Admin opens `/admin/integrations` | sync | Server Component reading catalogue + entitlements + data policy group |
| 2 | Create connection (API key, basic, mTLS) | platform → provider | Admin submits the form | sync validate, async probe | Server Action → `integrations.connection.create` → BullMQ `integration-probe:{region}` |
| 3 | Create connection (OAuth authorisation code) | platform ↔ provider | Admin clicks "Connect" | redirect flow | `beginOAuth` / `completeOAuth` in [[INT-integration-framework]] |
| 4 | Test connection | platform → provider | Admin clicks "Test", or after create, reconnect or rotation | async (≤ 30 s), result streamed to page | BullMQ `integration-probe:{region}` calling the connector's read-only `probe()` |
| 5 | Enable per unit | internal | Admin changes the unit list | sync | Settings write + `integration_connection_unit` rows |
| 6 | Set defaults per category | internal | Admin picks a default connection for a category at tenant, unit or case-type scope | sync | [[PKG-settings]] keys `integration.default_connection.<category>` |
| 7 | Health check | platform → provider | Every 15 minutes (setting), and on error-rate change | async | BullMQ repeatable `integration-health:{region}` |
| 8 | Credential rotation / reconnect | platform → provider | Scheduled (rotation days), expiry warning, or manual | async | Temporal `ConnectionCredentialRotationWorkflow` on task queue `integrations-{region}` |
| 9 | Disable / suspend | internal | Admin action, data policy change, failed checks, tenant suspension | sync | `integrations.connection.disable`; dependent work gets `IntegrationDisabledError` |
| 10 | Revoke and delete | platform → provider | Admin deletes, tenant offboarding ([[MT-tenant-lifecycle]]) | async | Temporal `ConnectionRevocationWorkflow`: revoke OAuth grant at provider, delete secret, request provider-side deletion where the API allows, record evidence |
| 11 | Per-user connect | user ↔ provider | User clicks "Connect calendar" | redirect flow | Same OAuth path; credential stored under the user path |
| 12 | Usage roll-up | internal | Hourly | async | BullMQ `integration-usage:{region}` aggregates `integration_call_log` into `integration_usage_daily` |

**Connection states** (code-defined state machine, [[WF-entity-state-machines]]):

```text
draft ──create──▶ pending_authorisation ──auth ok + probe ok──▶ active
active ──probe fails N times──▶ failing ──probe ok──▶ active
active ──error rate > threshold──▶ degraded ──recovers──▶ active
active ──credential expires within warning window──▶ credential_expiring (still usable)
any ──credential rejected by provider──▶ credential_invalid ──reconnect──▶ pending_authorisation
any ──admin / policy / tenant suspension──▶ suspended ──admin re-enables (policy allows)──▶ pending_authorisation
any ──delete──▶ revoking ──provider revoke done──▶ revoked (terminal; row kept for audit)
```

Only `active`, `degraded` and `credential_expiring` connections are returned by `withConnection`. A connection imported through a configuration package ([[PKG-configuration-packages]]) always starts in `pending_authorisation` because packages never carry secrets.

**Dependency view.** Before disable, delete or category default change, the console shows what depends on the connection: case-type blueprints that reference it, automation rules ([[WF-automation-rules]]) that call it, running cases with work pinned to it (for example an open e-sign envelope), and units using it. Running work keeps the connection it started with unless an admin explicitly migrates it (for example re-creates an envelope); disabling with in-flight work requires typing the connection name and a reason.

<!-- section:mapping -->
## Data mapping

This node maps administrative data, not case data; case-data mappings stay in each provider node.

**Connection record** (extends `integration_connection` in [[INT-integration-framework#api]]; tenant-owned, forced RLS)

| Field | Type | Source | Shown to admin | Notes |
|---|---|---|---|---|
| `id` | uuid | system | yes (`con_…`) | |
| `tenant_id` | uuid | context | no | null only for platform-managed regional accounts (platform table `platform_integration_connection`) |
| `connector_key`, `category` | text | catalogue | yes | |
| `display_name` | text ≤ 80 | admin | yes | |
| `environment` | `live` / `sandbox` | admin | yes | |
| `region` | `in` / `sg` / `us` | tenant home region | yes, read-only | cannot differ from tenant region |
| `ownership` | `platform_managed` / `tenant_byo` / `user_connected` | admin | yes | |
| `config` | jsonb | admin, validated by `configSchema` | yes | no secrets; max 16 KB |
| `secret_ref` | text | system | no; console shows "Set", last 4 characters where the provider shows them, and `credential_set_at` | path in the regional secrets manager |
| `auth_kind` | enum | catalogue | yes | |
| `oauth_grant` | jsonb (`scopes`, `granted_by_subject`, `grantor_type` `service_account`/`person`, `granted_at`, `expires_at`) | provider token response | yes | warns when `grantor_type = person` |
| `owner_user_id`, `backup_owner_user_id` | uuid | admin | yes | both must hold `integration_admin` |
| `status` | state enum above | system | yes | |
| `health` | jsonb (`last_probe_at`, `last_success_at`, `error_rate_1h`, `last_error_code`) | health job | yes | provider error text truncated to 500 chars, scrubbed of personal data |
| `data_policy_group` | `case_data_approved` / `metadata_only` / `blocked` | [[INT-connector-data-policies]] | yes | read-only here |
| `credential_rotate_by` | timestamptz | rotation policy | yes | |
| `config_version` | int | system | yes | optimistic concurrency (ETag) |

**Unit enablement**: `integration_connection_unit(tenant_id, connection_id, unit_id, enabled, set_by, set_at)`. Absence of rows means "all units" when `integration.connection.unit_enablement_mode = all_units`.

**Per-user credentials**: `integration_user_credential(tenant_id, connection_id, user_id, secret_ref, scopes, status, connected_at, last_used_at)`. A user sees and revokes only their own rows.

**Catalogue entry** (platform-level table `connector_catalogue_entry`, no tenant RLS per [[MT-platform-level-tables]]): `connector_key`, `version`, `category`, `status`, `regions[]`, `offerings[]`, `entitlement_key`, `ownership_models[]`, `auth_kinds[]`, `data_manifest` (per operation: data kinds and classification tiers sent, see [[INT-connector-data-policies#policy]]), `default_policy_group`, `subprocessor_id`, `acr_ref`, `docs_url`, `published_at`. Availability per region and offering is a separate row set `connector_availability(connector_key, region, offering, status)`.

**Admin API mapping** (`/admin/v1`, generated from the same Zod schemas):

| Operation | Permission |
|---|---|
| `GET /integrations/catalogue` | `integration.connector:read` |
| `GET /integrations/connections`, `GET /integrations/connections/{id}` | `integration.connection:read` |
| `POST /integrations/connections` | `integration.connection:create` |
| `PATCH /integrations/connections/{id}` (If-Match) | `integration.connection:update` |
| `PUT /integrations/connections/{id}/credential` (write-only body) | `integration.connection.credential:update` |
| `POST /integrations/connections/{id}/oauth/start` | `integration.connection.credential:update` |
| `POST /integrations/connections/{id}/test` | `integration.connection:read` |
| `PUT /integrations/connections/{id}/units` | `integration.connection:assign` (tenant) or unit-scoped `integration.connection:assign` for a unit admin where allowed |
| `POST /integrations/connections/{id}/disable` / `/enable` | `integration.connection:update` |
| `DELETE /integrations/connections/{id}` | `integration.connection:delete` |
| `GET /integrations/connections/{id}/usage`, `/health`, `/calls` | `integration.usage:read` |

Permissions are defined in [[PKG-permission-catalogue]] and bundled in `ps.admin.integrations` (all of the above) and `ps.integration.viewer` (read, usage) by [[PKG-roles-and-permission-sets]].

<!-- section:auth -->
## Authentication and secrets

- **Secrets are references.** The database holds only `secret_ref` (`/{env}/{region}/tenants/{tenantId}/integrations/{connectionId}` or, for per-user, `/…/users/{userId}/integrations/{connectionId}`). Credential fields in forms are write-only: they are posted once to a Server Action that writes to the secrets manager through `@nomology/secrets` ([[PKG-encryption-utilities-key]]) and are never returned, logged, cached in TanStack Query or included in configuration packages ([[INF-secrets-and-keys]]).
- **Who can read a secret.** Only the regional integration worker IAM role. The Next.js web role can create and overwrite secrets at tenant paths but cannot read them. No console, admin API or support tool displays a secret; support staff cannot read tenant secrets even under break-glass ([[PKG-jit-and-break-glass]]).
- **OAuth.** Authorisation code with PKCE; `state` bound to the session, tenant, connection and a 10-minute expiry; requested scopes are the minimum declared in the catalogue entry, and the consent screen lists them in plain English before redirect [R3]. Refresh tokens are stored in the vault and rotated when the provider rotates them.
- **Grants tied to people.** OAuth grants made with a person's provider account stop working when that person leaves the provider tenant, which is a common cause of silent integration failure in iPaaS tools that manage connections separately from the recipes using them [R2]. We therefore (a) prefer provider service accounts and record `grantor_type`, (b) show a warning on person-held grants, (c) block person-held grants for categories marked "service account required" in [[PKG-settings-integrations]] (`integration.connection.require_service_account_oauth`), and (d) when the granting user is deprovisioned on our side ([[PKG-user-provisioning-scim]]), raise a task for the connection owner to reconnect within 7 days.
- **Rotation.** API-key style credentials have a rotate-by date (default 90 days, bounds 30–365). Rotation: admin writes the new credential as a pending version, the probe runs against it, and on success the pending version becomes current and the old one is scheduled for deletion after 24 hours (so in-flight jobs can finish). On failure the old credential stays current.
- **Step-up.** Creating, changing or deleting a credential needs a recent strong authentication (within 10 minutes) per [[PKG-authentication-policies]]; deleting a `tenant_byo` payment or e-sign connection is maker-checker ([[PKG-separation-of-duties]]).
- **Principal.** A connection acts at the provider under its credential, and inside the platform it is an `integration_connection` principal ([[PKG-non-human-principals]]) whose actions (for example processing an inbound event that updates a case) are attributed in the audit trail to that principal, not to the admin who created it.
- **Inbound verification.** Per-connection signing secret, verified on the raw body before tenant resolution completes, as specified in [[INT-integration-framework#tenant]].

<!-- section:errors -->
## Errors, retries and idempotency

**Admin-facing errors** (RFC 9457 problem types in [[APP-api-error-catalogue-problem]]; the console shows the same message text)

| Problem type | When | Admin sees | Retryable |
|---|---|---|---|
| `integration-entitlement-required` | Plan does not include the connector or ownership model | "Your plan does not include …" with a contact link | No |
| `integration-region-unavailable` | Connector has no compliant endpoint in the tenant region and no transfer basis | Explains the region rule; link to data policy | No |
| `integration-data-policy-blocked` | Connector or operation is `blocked` by a policy layer | Which layer blocks it (platform, region, tenant, unit) | No |
| `integration-config-invalid` | `configSchema` validation fails | Field errors with JSON pointer | No |
| `integration-oauth-denied` / `integration-oauth-state-invalid` | User refused consent, or state expired or mismatched | "Connection was not authorised"; start again | Yes (restart flow) |
| `integration-probe-failed` | Probe returned auth or network error | Provider error code, our classification, next step | Yes |
| `integration-secret-store-unavailable` | Secrets manager write failed | "Could not save the credential; nothing was changed" | Yes |
| `integration-connection-in-use` | Delete or disable with dependants, without confirmation | Dependency list | No (confirm) |
| `precondition-failed` | ETag mismatch | "Someone else changed this connection" with a diff | Re-read |
| `integration-connection-limit` | `integration.connection.max_per_tenant` reached | Current count and limit | No |

**Runtime effects of connection problems**
- `credential_invalid` or `suspended`: callers get `IntegrationDisabledError` (non-retryable). Temporal activities fail to a human task "Integration needs attention" assigned to the connection owner, with the case reference; BullMQ jobs go to the dead-letter queue with reason `connection_unavailable` and are replayed automatically when the connection returns to `active` (only jobs younger than 72 hours; older jobs need an admin decision).
- `failing`: calls are attempted (the provider may recover) but the circuit breaker in the framework limits load; the tenant admin banner shows the failing connection.
- Fallback is never automatic across ownership models (for example from a tenant's own SMS account to the platform-managed one), because the sender identity and contract differ; a tenant may configure an explicit secondary connection per category (`integration.default_connection.<category>.secondary`), used only for classes the notification policy allows ([[PKG-notification-policies]]).

**Idempotency.** Create accepts `Idempotency-Key`; probe, rotate and revoke workflows use the connection ID and version as workflow ID (`conn-rotate-{connectionId}-{version}`), so retries cannot run two rotations at once. Duplicate OAuth callbacks are rejected after the first because `state` is single-use.

<!-- section:limits -->
## Rate limits and SLAs

| Limit | Default | Bound | Setting |
|---|---|---|---|
| Connections per tenant | 50 | plan | `integration.connection.max_per_tenant` |
| Connections per category per unit | 3 (one default, one secondary, one sandbox) | 5 | code |
| Health probe interval | 15 min | 5–60 min (platform) | `integration.health.check_interval_min` |
| Probe timeout | 30 s | fixed | code |
| Consecutive failed probes before `failing` | 3 | 2–10 | `integration.health.failures_before_failing` |
| Usage roll-up delay | ≤ 1 h | — | — |
| Usage budgets (SMS segments, e-sign envelopes, KYC checks, video minutes) | plan entitlement | tenant may set lower; alert at 80% and 100% | `integration.usage.<meter>.monthly_cap` |

At 100% of a tenant-set usage cap, non-mandatory sends stop with `integration-usage-cap-reached` while `legal_service` and `auth` notifications continue (they are never blocked by a tenant budget; billing records the overage per [[BIL-plans-entitlements-and-usage]]).

Provider SLAs for `platform_managed` accounts are recorded in each provider node; for `tenant_byo` accounts the tenant owns the provider SLA, and our health view shows observed availability only.

<!-- section:residency -->
## Data transfer and compliance

- A connection's region is always the tenant's home region ([[MT-data-residency-2]]); the field is read-only and the create call fails with `integration-region-unavailable` when the catalogue entry has no compliant endpoint in that region.
- For `tenant_byo` connections the tenant states where the provider processes data (a required field with options from the catalogue entry, for example "India region", "Singapore region", "Outside region under tenant's own contract"). Choosing "outside region" requires the transfer basis to be recorded and approved under [[INT-connector-data-policies]] before the connection can leave `pending_authorisation`. India permits transfers except to countries the Government restricts [R4]; Singapore requires a comparable standard of protection, usually by contract [R5]. The tenant remains responsible for its own provider contract.
- Connection metadata, health data, call logs and usage roll-ups stay in the regional database. The platform cross-tenant health view at `/platform/integrations/connections` is served from each region separately; there is no global copy.
- Offboarding: `ConnectionRevocationWorkflow` revokes grants and asks the provider for deletion where an API exists; where it does not, a task for Nomology ops records the manual request and the provider's confirmation as evidence in [[MT-tenant-lifecycle]].

<!-- section:testing -->
## Sandbox and testing

- Every connector ships a read-only `probe()` and a fake provider mode used by the sandbox environment, so tenant admins can rehearse a connection in their sandbox without touching real parties.
- Contract tests: create → probe → unit enablement → rotate → disable → revoke for each auth kind, against the `fake-provider` connector and against recorded fixtures of real connectors.
- Isolation tests (forced RLS through PgBouncer): tenant B cannot list, read, test or rotate tenant A's connection; a unit admin cannot toggle a connection outside their unit; a user cannot see another user's per-user credential.
- Secret handling tests: no response, log line, trace attribute or configuration package export contains a credential (property test over all admin API responses with a canary secret).
- Permission tests generated from the matrix in [[PKG-permission-catalogue]] for every operation in the mapping table.
- Dependency view test: disabling a connection referenced by a published blueprint shows the blueprint and requires confirmation.
- Playwright journeys: OAuth connect with consent denial, API-key connect with failed probe, rotation success and rollback.

<!-- section:questions -->
## Open questions

- [ ] Should `tenant_byo` be allowed for messaging (email and SMS) from Phase 3, given legal-notice evidence depends on provider receipts we do not contract for? Proposed: yes for email and SMS, with a mandatory receipt-capability check in the probe. (Product + legal)
- [ ] Do we expose provider-side deletion evidence to tenants in the offboarding pack, or keep it internal? (Privacy owner)
- [ ] Who may approve a `tenant_byo` connection whose provider processes data outside the tenant region: `security_admin` only, or also Nomology `platform_security` for regulated blueprints (SEBI ODR)? (Security)
- [ ] Unit-level BYO accounts (a unit's own e-sign contract): needed in Phase 5 or later? (Product, TERES)
- [ ] Per-user connections beyond calendar (for example a neutral's own e-sign identity)? (Product)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant separation at the provider

Platform-managed accounts are shared per region with our tenant-scoped external references; tenant-owned (`tenant_byo`) and per-user connections have their own credentials at tenant- and user-scoped secret paths. All connection, unit and per-user credential tables are tenant-owned with forced RLS; the only pre-tenant lookup is the inbound resolver in [[INT-integration-framework#tenant]]. Unit admins act only on units in their resource set. Offboarding runs `ConnectionRevocationWorkflow` with provider-side deletion evidence.

<!-- check:security -->
### Security

Credentials are write-only in every UI and API, stored only in the regional secrets manager and readable only by the integration worker role; OAuth uses PKCE, single-use state and minimum scopes [R3]; person-held grants are flagged and can be forbidden; credential changes need step-up and, for payment and e-sign BYO deletion, maker-checker. The connection acts as an `integration_connection` principal with its own audited identity.

<!-- check:residency -->
### Data transfer and residency

Connection region equals tenant region and is immutable; BYO connections must declare provider processing location, and out-of-region processing requires an approved transfer basis under [[INT-connector-data-policies]] [R4][R5]. Health, logs and usage stay regional; the platform health view is per region.

<!-- check:vendor -->
### Vendor risk and exit

Only connectors with a catalogue entry linked to a completed vendor assessment ([[SEC-vendor-sub-processor-management]]) can be `certified`; `beta` connectors are visible only to tenants a platform admin opts in. For BYO accounts the tenant is the contracting party; the catalogue records the minimum provider capabilities we rely on (receipts, deletion API), and the probe checks them.

<!-- check:resilience -->
### Failure handling and degradation

Connection problems change state (`degraded`, `failing`, `credential_invalid`) rather than failing silently; dependent Temporal work raises a human task to the owner and dead-lettered BullMQ jobs are replayed when the connection recovers. There is no silent fallback across ownership models; explicit secondary connections are policy-controlled. Rotation keeps the old credential for 24 hours.

<!-- check:consistency -->
### Consistency and reconciliation

The platform is the source of truth for connection configuration and enablement; the provider is the source of truth for whether a credential and grant are valid, checked by the probe every 15 minutes and on every call. Granted scopes are re-read from the provider token response on each refresh and differences raise `admin.integration.scope_drift` for review.

<!-- check:audit -->
### Audit and evidence

Every create, update, credential write (without value), rotation, unit change, default change, enable, disable and revoke writes `admin.integration.<verb>` events with actor, principal, reason, old and new non-secret values and config version ([[PKG-audit-trail]]). Revocation evidence from providers is stored with a SHA-256 hash. The inventory export lists owners, rotation dates and policy groups for auditors.

<!-- check:observability -->
### Observability

Per connection: probe results, error rate, 429 count, latency and usage against cap, shown on the connection page and rolled up to `/platform/integrations/connections` per region. Alerts go to the connection owner and backup owner (credential expiring in 14 days, `failing`, `credential_invalid`, 80% of a cap) and to Nomology on-call for platform-managed accounts ([[OBS-alerting]]).

<!-- check:testing -->
### Testing

Sandbox connections with fake-provider mode, contract tests per auth kind, RLS isolation tests through PgBouncer, a canary-secret leak test across all admin responses and exports, generated permission tests, and Playwright journeys for OAuth denial, failed probe and rotation rollback.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "A named credential defines the callout endpoint; an external credential defines how the caller authenticates, and principals map to user permissions.",
    "id": "R1",
    "kind": "vendor",
    "publisher": "Salesforce",
    "retrieved": "2026-10-28",
    "title": "Get Started with Named Credentials",
    "url": "https://developer.salesforce.com/docs/platform/named-credentials/guide/get-started.html"
  },
  {
    "excerpt": "Connections hold the credentials that recipes use to reach an application and are managed separately from the recipes that use them.",
    "id": "R2",
    "kind": "vendor",
    "publisher": "Workato",
    "retrieved": "2026-10-28",
    "title": "Workato documentation: Connections",
    "url": "https://docs.workato.com/connections.html"
  },
  {
    "body": "IETF",
    "excerpt": "Recommends sender-constrained or audience-restricted, short-lived access tokens and strong client authentication such as private_key_jwt.",
    "id": "R3",
    "ident": "RFC 9700",
    "kind": "standard",
    "title": "Best Current Practice for OAuth 2.0 Security",
    "url": "https://www.rfc-editor.org/rfc/rfc9700.html"
  },
  {
    "id": "R4",
    "issuer": "Ministry of Electronics and Information Technology, India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 22 of 2023",
    "title": "Digital Personal Data Protection Act, 2023",
    "url": "https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf"
  },
  {
    "excerpt": "An organisation transferring personal data outside Singapore must ensure the recipient is bound to provide a comparable standard of protection, for example by contract.",
    "id": "R5",
    "kind": "web",
    "publisher": "Personal Data Protection Commission Singapore",
    "retrieved": "2026-10-28",
    "title": "Advisory Guidelines: The Transfer Limitation Obligation (Chapter 19)",
    "url": "https://www.pdpc.gov.sg/-/media/files/pdpc/pdf-files/advisory-guidelines/the-transfer-limitation-obligation---ch-19-(270717).pdf"
  }
]
```

<!-- end -->
