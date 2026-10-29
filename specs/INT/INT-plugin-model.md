---
id: "INT-plugin-model"
title: "Plugin model"
parent: "INT"
order: 3
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "Defined extension points (first-party connectors, signed configuration plugins, out-of-process external apps via API and webhooks), a registry of installable plugins and the tenant administration model: request, approve with scope consent, install, upgrade, restrict, remove; no third-party code runs inside the platform runtime"
links: []
rev: 4
syncHash: "c7b38720da3f85c2"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 9.3 Plugin model

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Defined extension points (first-party connectors, signed configuration plugins, out-of-process external apps via API and webhooks), a registry of installable plugins and the tenant administration model: request, approve with scope consent, install, upgrade, restrict, remove; no third-party code runs inside the platform runtime

<!-- section:purpose -->
## Purpose and scope

Lets the platform be extended per tenant without forking code and without running untrusted code inside our runtime. A **plugin** is a registered, versioned package of one or more extensions that a tenant admin can install for their tenant. This package provides the registry, installation records, extension-point contracts, the **administration model** (who may publish, request, approve, install, upgrade, restrict and remove), and the checks that keep plugins inside their permissions.

Extension point classes:
1. **Connectors**: first-party adapters for providers ([[INT-integration-framework]]); code in our monorepo, reviewed and deployed by us; administered as connections ([[INT-connections-admin]]).
2. **Configuration plugins**: data-only bundles that tenants or our implementation team install: decision tables ([[PKG-rules-and-decision-engine]]), workflow templates and case-type blueprints ([[PKG-workflow-templates]], [[WF-process-definition-model]]), automation rule sets ([[WF-automation-rules]]), form definitions ([[PKG-forms-and-form-builder]]), document and notification templates ([[PKG-document-and-notification]]), report templates ([[RPT-configurable-report-templates]]), custom field definitions ([[PKG-metadata-management-entity]]). A configuration plugin is distributed as a signed configuration package ([[PKG-configuration-packages]]) and its contents follow the configuration lifecycle on install.
3. **External apps**: third-party or tenant-built services that act through the public API and receive webhooks, installed as an OAuth client with a scope grant ([[PKG-api-clients-and-keys]], [[INT-public-api-and-webhooks]]).

**Not supported**: third-party JavaScript or server code running in our Next.js app, workers or database; tenant-supplied scripts in the UI. A sandboxed in-process model may be considered later (see questions).

**Administration model** (pattern borrowed from: workspace app approval, where only pre-approved apps can be installed, members request others, app managers approve, and approving an app means approving its scopes [R1]; and app access rules that block installed apps from tenant content [R2]):

| Action | Who (role keys) | Permission | Controls |
|---|---|---|---|
| Publish first-party plugin version | `platform_admin` (maker), `platform_security` (checker) | `platform.plugin:publish` | Signed bundle, schema validation, region list |
| Publish tenant-private configuration plugin | Nomology implementation team, or `tenant_admin` where `integration.plugins.private_publishers` allows | `plugin:publish` | Configuration kinds only |
| Browse catalogue | `tenant_admin`, `integration_admin`, `workflow_designer`, `auditor` | `plugin:read` | Filtered by plan, region, offering |
| Request install | any staff role when `integration.apps.install_policy = request_and_approve` | `plugin.request:create` | Justification text, requested scopes shown |
| Approve request / install | `integration_admin`, `security_admin` (configurable approvers) | `plugin:create` | Scope consent screen; admin scopes need `tenant_owner` and maker-checker |
| Configure installation | `integration_admin` | `plugin:configure` | JSON Schema of the plugin |
| Upgrade | `integration_admin`; automatic for patch versions per `integration.apps.auto_upgrade` | `plugin:create` | Scope increases always need review (locked) |
| Restrict (block from case content without uninstalling) | `security_admin` | `plugin:configure` | Revokes data scopes, keeps configuration |
| Uninstall | `integration_admin` | `plugin:delete` | Option to keep data written by configuration plugins |
| Revoke version across tenants | `platform_admin` + `platform_security` | `platform.plugin:delete` | New installs and new cases stop using it |

Consoles: `/admin/integrations/apps` (installed, requests, catalogue), `/admin/integrations/apps/[installationId]` (overview, scopes granted, configuration, version history, activity); platform: `/platform/plugins`, `/platform/plugins/[key]/versions`. Admin API: `/admin/v1/plugins/...` ([[INT-tenant-admin-api]]).

<!-- section:consumers -->
## Consumers and use cases

- Tenant admin console: browse, request, approve, install, configure, upgrade, restrict and remove plugins (`/admin/integrations/apps`).
- Implementation team: package an institution's rule set (for example a procedural timetable and fee schedule) as a configuration plugin and install it in the tenant sandbox, then production, through the configuration lifecycle.
- Platform admin: publish first-party plugins, revoke a plugin version across tenants, see installation counts per region.
- Workers and app code: query which plugins and versions are active for the tenant (`getActiveExtensions`).
- External app developers: register an app in the developer portal and request scopes; tenants see the requested scopes and data kinds before approving.

<!-- section:api -->
## Public API

```ts
// packages/plugins/src/index.ts (server-only)
export type ExtensionKind =
  | 'connector' | 'decision_table' | 'workflow_template' | 'case_type_blueprint' | 'automation_rules' | 'form'
  | 'document_template' | 'notification_template' | 'report_template' | 'custom_fields' | 'external_app';

export interface PluginManifest {
  key: string;                    // 'hkiac-style-timetable' (unique in registry)
  version: string;                // SemVer
  publisher: 'nomology' | { tenantId: string };   // tenant-private plugins
  extensions: Array<{ kind: ExtensionKind; ref: string; schemaVersion: number }>;
  permissions: string[];          // external_app: public API scopes; data plugins: target namespaces
  regions: Array<'in'|'sg'|'us'>;
  offerings: Array<'cord'|'teres'>;
  requiresEntitlements?: string[];  // e.g. ['feature.public_api']
  dataKinds?: DataKind[];         // external_app: data kinds it will read (shown on consent screen)
  support: { contact: string; docsUrl: string; privacyNoticeUrl?: string };
}

export async function publishPlugin(manifest: PluginManifest, bundle: Uint8Array, signature: Uint8Array): Promise<PluginVersion>;
export async function requestInstall(key: string, version: string, justification: string): Promise<InstallRequest>;      // tenant from context
export async function decideInstallRequest(requestId: string, decision: 'approve'|'reject', note?: string): Promise<InstallRequest>;
export async function installPlugin(key: string, version: string, config: unknown): Promise<Installation>;
export async function upgradeInstallation(id: string, toVersion: string): Promise<Installation>;  // fails with ScopeReviewRequired if scopes grow
export async function restrictInstallation(id: string, reason: string): Promise<Installation>;
export async function uninstallPlugin(id: string, opts: { keepData: boolean }): Promise<void>;
export async function getActiveExtensions(kind: ExtensionKind): Promise<ActiveExtension[]>;
// Events: plugin.install_requested | plugin.installed | plugin.upgraded | plugin.restricted | plugin.uninstalled | plugin.version_revoked
```

Tables: `plugin` and `plugin_version` (platform-level, no tenant RLS, per [[MT-platform-level-tables]]; tenant-private plugins carry `owner_tenant_id` and are filtered by policy), `plugin_installation(tenant_id, plugin_version_id, status 'active'|'restricted'|'uninstalled', config jsonb, granted_scopes text[], installed_by, approved_by, installed_at)` and `plugin_install_request(tenant_id, plugin_key, version, requested_by, justification, status, decided_by, decided_at)`, tenant-owned with forced RLS.

<!-- section:usage -->
## Usage examples

```ts
// Install an institution's fee schedule and timetable bundle in UAT
await installPlugin('institution-rules-2026', '1.2.0', { seat: 'Singapore', currency: 'SGD' });

// Workflow start loads the active decision tables once (then passes versions in)
const tables = await getActiveExtensions('decision_table'); // inside an Activity
```

<!-- section:tenant -->
## Tenant context

Installation is always for the tenant in context; a tenant-private plugin published by tenant A is invisible to tenant B (RLS policy on `owner_tenant_id`). Data written by configuration plugins is stored in the target package's tenant-owned tables under the installing tenant, as drafts that then follow the configuration lifecycle. External apps receive OAuth clients bound to the installing tenant and region only; a multi-tenant app vendor gets one client per tenant installation. Restricting an installation revokes its tokens within 30 seconds (revocation cache) while keeping its configuration.

<!-- section:config -->
## Configuration

Settings in [[PKG-settings-integrations]] group F: `integration.apps.install_policy` (`disabled`, `admins_only`, `request_and_approve`), `integration.apps.approvers`, `integration.apps.request_requires_justification`, `integration.apps.max_scopes`, `integration.apps.auto_upgrade` (`off`, `patch`, `minor`), `integration.apps.scope_change_requires_review` (locked true), `integration.plugins.allow_tenant_private`, `integration.plugins.private_publishers`. Allowed extension kinds per plan come from entitlements (`feature.public_api` for external apps). Installation config is validated against the plugin's JSON Schema.

<!-- section:adapters -->
## Providers and extension points

Each extension kind is handled by the owning package's loader, which validates the bundle against that package's schema (for example decision table schema version 3). Adding a new extension kind requires a loader, a schema and a review that the kind cannot execute code.

<!-- section:errors -->
## Error model

`PluginNotFound`, `PluginRegionUnavailable`, `EntitlementRequired`, `SchemaValidationFailed` (with JSON pointer paths), `InstallPolicyDisabled`, `InstallRequiresApproval` (request created instead), `ScopeReviewRequired` (upgrade adds scopes), `ScopeExceedsTenantMaximum`, `UpgradeBlocked` (running cases depend on the old version; decision and workflow versions are pinned per case, so upgrades apply to new cases only, per [[WF-workflow-versioning]]), `VersionRevoked`, `SignatureInvalid`.

<!-- section:nfr -->
## Performance and limits

Bundle size ≤ 5 MB; install and validate ≤ 10 s; `getActiveExtensions` served from the tenant-scoped cache (p99 < 5 ms warm).

<!-- section:versioning -->
## Versioning and compatibility

Plugins use SemVer. Revoking a version stops new installs and new cases using it; running cases keep their pinned version unless a platform admin forces migration with an audited reason.

<!-- section:testing -->
## Test contract

Each loader has schema tests and a test that a bundle containing executable content (scripts, `eval`-like expressions outside the decision language) is rejected. Isolation test: tenant-private plugin of A not listable or installable by B.

<!-- section:questions -->
## Open questions

- [ ] Is there a real need for third-party code running inside the platform (for example a tenant's custom validation)? If yes, choose a sandbox (separate container per tenant, or WebAssembly with no network) and record an ADR.
- [ ] Who may publish tenant-private plugins: tenant admins, or only Nomology's implementation team (current default)?
- [ ] Should there be a public marketplace listing of external apps, and what review would a listed app need (security questionnaire, pen-test summary, privacy notice)?
- [ ] Should counsel (non-staff) be able to request apps for their own use, for example a practice-management sync? Proposed: no in Phase 5.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Installations are tenant-owned with forced RLS; tenant-private plugins are filtered by `owner_tenant_id`; external apps get per-tenant OAuth clients; data written by configuration plugins lands in the installing tenant's rows only.

<!-- check:security -->
### Security of the API surface

No third-party code executes in our runtime; every extension kind is signed data validated against a schema, or an external service that holds only scoped, tenant- and region-bound OAuth credentials. Approving an app shows and grants its scopes and data kinds; scope increases always need review; admin scopes need the tenant owner and maker-checker; installations can be restricted without uninstalling. Loaders reject executable content.

<!-- check:residency -->
### Region awareness

Plugins declare the regions they support; installation is refused in a region not listed. Configuration bundles are copied into the tenant's regional tables; external apps call the tenant's regional API base URL with region-bound credentials, so no plugin path moves tenant data across regions through our platform.

<!-- check:audit -->
### Audit events

Publish, request, approve, reject, install, upgrade, restrict, uninstall and revoke are audited (`admin.plugin.*`) with actor, approver, tenant, plugin key and version, granted scopes and the configuration hash. Each case records the plugin versions (decision tables, workflow templates, blueprints) it was started with.

<!-- check:change-safety -->
### Change and release safety

Decision tables and workflow templates are pinned per case at start, so a plugin upgrade cannot change running cases. Upgrades are installed first in the tenant's UAT environment where they have one.

<!-- check:testing -->
### Testing

Loader schema tests, a rejection test for executable content, an isolation test for tenant-private plugins, and an upgrade test proving running cases keep their pinned versions.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Owners can allow only pre-approved apps, route member requests to app managers, restrict apps, and approving an app means approving the scopes it will use.",
    "id": "R1",
    "kind": "vendor",
    "publisher": "Slack",
    "retrieved": "2026-10-28",
    "title": "Manage app approval for your workspace",
    "url": "https://slack.com/help/articles/222386767-Manage-app-approval-for-your-workspace"
  },
  {
    "excerpt": "An app access rule blocks installed apps from reading, writing or deleting user-generated content in covered spaces, with exemptions for allowed apps.",
    "id": "R2",
    "kind": "vendor",
    "publisher": "Atlassian",
    "retrieved": "2026-10-28",
    "title": "Block app access (data security policies)",
    "url": "https://support.atlassian.com/security-and-access-policies/docs/block-app-access/"
  }
]
```

<!-- end -->
