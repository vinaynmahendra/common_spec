---
id: "PKG-configuration-packages"
title: "Configuration packages and tenant blueprints"
parent: "PKG-configuration-and-customisation"
order: 8
type: "feature"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "`@nomology/config-packages`: versioned, signed bundles of configuration (settings, roles and permission sets, custom fields, case-type blueprints, templates, rules, automation, integration definitions; never secrets or personal data) used for tenant blueprints, environment promotion, sandbox refresh and export, with three-way diff and import as a draft change set"
links: []
rev: 1
syncHash: "4b817c2290903d1e"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.8.8 Configuration packages and tenant blueprints

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> `@nomology/config-packages`: versioned, signed bundles of configuration (settings, roles and permission sets, custom fields, case-type blueprints, templates, rules, automation, integration definitions; never secrets or personal data) used for tenant blueprints, environment promotion, sandbox refresh and export, with three-way diff and import as a draft change set

<!-- section:purpose -->
## Purpose and scope

`@nomology/config-packages` moves configuration as a unit. A **configuration package** is a versioned, signed, self-describing bundle of configuration components, addressed by logical keys rather than database IDs. It is used to:

- create a tenant from a **tenant blueprint** (for example "SEBI ODR institution blueprint v1.2");
- upgrade a tenant to a newer blueprint version while keeping its own customisations;
- promote configuration from a sandbox tenant or a UAT tenant to the production tenant ([[PKG-configuration-lifecycle#design]]);
- refresh a sandbox from its parent, and export a tenant's configuration at offboarding ([[MT-tenant-lifecycle]]);
- ship optional add-on packs curated by Nomology (for example an MSME claims pack, a Hindi language pack).

Package kinds: `blueprint` (Nomology-published starting configuration for a tenant type), `extension` (Nomology-published add-on), `promotion` (selected change sets from one tenant to another tenant of the same customer), `snapshot` (all published configuration of one tenant at a moment).

**Does not:** carry secrets (integration credentials are declared as empty **secret slots** and filled through [[INT-connections-admin]]); carry personal data, users, memberships, cases, documents, audit events or usage; carry feature flags or deployment configuration ([[PKG-feature-flags]], [[FND-environment-management]]); publish anything by itself: every import becomes a draft change set that follows the target tenant's own review ([[PKG-configuration-lifecycle]]).

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Use case |
|---|---|
| Tenant onboarding wizard ([[APP-tenant-onboarding-wizard]]) and tenant lifecycle ([[MT-tenant-lifecycle]]) | Apply the chosen blueprint with parameters (name, locales, time zone, seat country) when a tenant is provisioned |
| Tenant admins (`tenant_owner`, `tenant_admin`) at `/admin/packages` | Export selected change sets from a sandbox and import them into production; export a snapshot for their records |
| Nomology implementation team at `/platform/tenants/[tenantId]/config/packages` | Build a customer's configuration in a UAT tenant, export a signed promotion package, import it into the production tenant as a draft |
| Platform product team at `/platform/config/blueprints` | Author, test, sign and publish blueprint and extension versions; offer upgrades to tenants |
| Sandbox refresh (`SandboxRefreshWorkflow`) | Snapshot the parent's configuration and apply it to the sandbox |
| Offboarding export | Include a snapshot package in the tenant's data export bundle |

<!-- section:api -->
## Public API

```ts
// packages/config-packages/src/index.ts (server-only)
export type PackageKind = 'blueprint' | 'extension' | 'promotion' | 'snapshot';

export interface PackageManifest {
  format: 'nomology.config-package/v1';
  id: string;                       // UUIDv7, unique per build
  key: string;                      // 'blueprint.sebi_odr_institution', 'promotion.<tenantSlug>.<n>'
  version: string;                  // semver for blueprints and extensions; build counter for others
  kind: PackageKind;
  offering: 'cord' | 'teres' | 'any';
  tenantTypes?: TenantType[];       // blueprints: which tenant types may use it
  platformCompat: { minSchema: number; maxSchema?: number };  // settings and artefact schema generation
  requires: { ref: string; version?: string }[];               // platform reference data, e.g. 'calendar.in-national', 'connector.msg91'
  parameters: PackageParameter[];   // values asked for at import, e.g. tenant.display_name
  components: ComponentEntry[];
  source: { environment: string; region: string; tenantRef?: string /* opaque hash, never the tenant id */; builtBy: string; builtAt: string };
  digest: string;                   // sha256 of the canonical manifest without signature
  signature?: { alg: 'ES256'; keyId: string; value: string };
}

export interface ComponentEntry {
  kind: ComponentKind;              // see table below
  key: string;                      // logical key, e.g. 'case_type.sebi_odr_conciliation'
  version?: number;                 // source version, informational
  managed: boolean;                 // blueprint components the tenant may not edit
  path: string;                     // file inside the archive, e.g. 'components/case_type/sebi_odr_conciliation.json'
  sha256: string;
  dependsOn: string[];              // other component keys in this package or `requires`
}

export type ComponentKind =
  | 'setting_values'      // values and constraints at tenant, unit (by unit code) and case_type scope
  | 'role' | 'permission_set'
  | 'custom_field_definition' | 'form' | 'case_type_blueprint' | 'decision_table'
  | 'document_template' | 'notification_template' | 'notification_policy'
  | 'automation_rule' | 'threshold_set' | 'terminology_overrides' | 'theme'
  | 'integration_definition' | 'report_template' | 'unit_structure' | 'fixture_set';

export interface PackageParameter { name: string; type: 'text' | 'locale' | 'locale_list' | 'time_zone' | 'country' | 'currency' | 'unit_list'; required: boolean; default?: unknown; label: LocalisedText }

// Build and export
export function exportPackage(tx: TenantTx, sel: { kind: 'promotion'; changeSetIds: string[] } | { kind: 'snapshot' }): Promise<{ exportId: string }>;    // BullMQ 'package-export'
export function getExport(tx: TenantTx, exportId: string): Promise<{ status: 'queued' | 'ready' | 'failed'; downloadUrl?: string; manifest?: PackageManifest }>;

// Import (tenant or platform context)
export function uploadPackage(tx: TenantTx, objectId: string): Promise<{ importId: string }>;                      // verify signature, scan, unpack
export function planImport(tx: TenantTx, importId: string, params: Record<string, unknown>): Promise<ImportPlan>;   // three-way diff
export function applyImport(tx: TenantTx, importId: string, decisions: ConflictDecision[]): Promise<{ changeSetId: string }>;  // creates a DRAFT change set

export interface ImportPlan {
  manifest: PackageManifest;
  verification: { signatureValid: boolean; keyId: string; trusted: boolean; digestsValid: boolean };
  components: { key: string; kind: ComponentKind; action: 'add' | 'update' | 'unchanged' | 'conflict' | 'remove_proposed'; patch?: JsonPatch; localChanged: boolean; incomingChanged: boolean }[];
  missingRequirements: string[];
  secretSlots: { component: string; slot: string; connector: string }[];
  blockers: ValidationIssue[];      // e.g. tenant not entitled to a component, schema too new
}
export type ConflictDecision = { key: string; take: 'incoming' | 'local' | 'manual'; manualPatch?: JsonPatch };

// Blueprints (platform context)
export function publishBlueprint(ptx: PlatformTx, buildId: string, opts: { reason: string }): Promise<PackageManifest>;   // signs; maker-checker
export function applyBlueprint(ptx: PlatformTx, tenantId: string, ref: { key: string; version: string }, params: Record<string, unknown>): Promise<{ workflowId: string }>; // Temporal ApplyBlueprintWorkflow
export function planBlueprintUpgrade(tx: TenantTx, toVersion: string): Promise<ImportPlan>;

// Events (outbox): config.package.exported, config.package.imported, config.package.verification_failed,
//                  config.blueprint.published, config.blueprint.applied, config.blueprint.upgrade_available
```

**Archive layout** (`.ncp`, a zip with a fixed layout):
```text
manifest.json                 # PackageManifest, canonicalised (RFC 8785) before hashing and signing
components/<kind>/<key>.json  # one file per component, canonical JSON
assets/<sha256>.<ext>         # theme logos, document template images, referenced by hash
fixtures/<key>.json           # fixture_set components only (synthetic data for sandboxes and simulation)
```

**Signing.** The manifest's `digest` is the SHA-256 of its canonical JSON form (RFC 8785 [R1]) excluding `signature`; each component's `sha256` covers its canonical file. The signature is ES256 over `digest`, created by an asymmetric KMS key per environment and region (`alias/nomology-<env>-<region>-config-package`, [[INF-secrets-and-keys]]); private key material never leaves KMS. Each environment holds a trust list of public keys it accepts (`config.trusted_package_key`): production trusts production keys and the UAT keys, for kind `promotion` only.

**Promotion across environments.** There is no network path from non-production to production ([[FND-environments]], ENVS-1). A UAT package is downloaded by the implementation engineer and uploaded in the production platform console; the production import verifies the UAT signature against the trust list. This keeps the pattern of moving a named, reviewed change bundle along a pipeline (as solutions do in Power Platform [R2] and work items in DevOps Center [R3]) without connecting the environments.

<!-- section:usage -->
## Usage examples

```ts
// Implementation engineer: import a UAT promotion package into the production tenant
const { importId } = await withTenant(tenantId, (tx) => packages.uploadPackage(tx, uploadedObjectId));
const plan = await withTenant(tenantId, (tx) => packages.planImport(tx, importId, {}));
if (!plan.verification.trusted || plan.blockers.length) throw new ImportBlockedError(plan);   // shown in the console
const decisions = plan.components.filter((c) => c.action === 'conflict').map((c) => ({ key: c.key, take: 'local' as const }));
const { changeSetId } = await withTenant(tenantId, (tx) => packages.applyImport(tx, importId, decisions));
// changeSetId is a draft: the tenant admin reviews and publishes it under the tenant's own policy
```

```ts
// Onboarding wizard: provision a SEBI ODR institution tenant in India
await packages.applyBlueprint(ptx, tenantId, { key: 'blueprint.sebi_odr_institution', version: '1.2.0' }, {
  'tenant.display_name': 'Example ODR Institution', 'tenant.locales': ['en-IN', 'hi-IN'], 'tenant.time_zone': 'Asia/Kolkata',
});
```

**Tenant blueprints shipped at launch** (contents are proposals; the defaults per catalogue are in each catalogue's `defaults` section, for example [[PKG-settings-branding-content#defaults]]):

| Blueprint key | Tenant type | Main contents | Managed (locked) components |
|---|---|---|---|
| `blueprint.arbitral_institution` | `arbitral_institution` | Case types: institutional arbitration (standard, expedited), emergency arbitrator; roles incl. tribunal secretary; fee decision tables (placeholder); award scrutiny stage; SSO-ready security defaults; English plus seat-specific holiday calendars | Platform footer, legal and consent texts, audit settings |
| `blueprint.sebi_odr_institution` | `odr_institution` | Case types: SEBI ODR conciliation and arbitration with timeline bounds from the SEBI ODR circulars [R4] (assumption: exact timelines and fee rules to be confirmed by legal); MII intake integration definition (NSE) with secret slots; aggregator report template ([[RPT-example]]); investor-facing plain-language terminology; English and Hindi | Regulator-defined timeline constraints, investor charter link, DPDP notice requirement, retention minimums |
| `blueprint.cord_tenant` | `cord` | Case types: online mediation, online arbitration, MSME claim (draft); self-registration for claimants; party payment of case fees | Platform footer, consent texts |
| `blueprint.court_programme` | `court_programme` | Case types: court-annexed mediation, Lok Adalat-style settlement (assumption: confirm with first court customer); review of all configuration changes; stricter retention and records rules; no AI drafting by default | Change-control review-all, records retention constraints, AI defaults off |

Each blueprint also includes a `fixture_set` of synthetic cases, parties and documents used by sandboxes ([[PKG-configuration-lifecycle]]) and by simulation ([[WF-workflow-simulation]]).

<!-- section:tenant -->
## Tenant context

- Exports and imports run inside `withTenant` for the source or target tenant ([[MT-prisma-client-extension-wraps]]); BullMQ jobs `package-export`, `package-verify` and `package-plan` carry the tenant ID in the payload and the worker sets context before any query. Missing context throws `TenantContextMissingError`.
- Packages never contain tenant IDs, user IDs, membership IDs or database IDs of any record. References are logical keys (case-type key, role key, unit code, template key). The exporter replaces IDs with keys and fails if it finds a UUID-shaped value in any component outside known version fields.
- Import records (`config.package_import`, `config.package_import_item`) and exports (`config.package_export`) are tenant-owned with forced RLS ([[PKG-settings-data-model#tables]]). Blueprints and extensions are platform-level (`config.package_release`) and readable by every tenant of the matching tenant type.
- A `promotion` package can be imported only into a tenant of the same customer: the source tenant's `customer_account_id` must match the target's (a new platform-level column on `tenant` proposed in [[PKG-settings-data-model#migrations]] for [[MT-tenant-model]]), or a `platform_admin` must record an approval.
- Each tenant records the blueprints and extensions applied (`config.tenant_package_lineage`: package key, version, applied change set), which is the base for three-way diffs on upgrade.

<!-- section:config -->
## Configuration

| Setting / limit | Default (proposed) | Where | Who changes |
|---|---|---|---|
| Maximum archive size | 50 MB including assets | Code | Engineering |
| Maximum components per package | 10,000 | Code | Engineering |
| Export retention in the regional bucket | 30 days, then deleted | Code | Engineering |
| Export download URL validity | 15 minutes, single tenant admin | Code | Engineering |
| Accept unsigned packages | Only in `local` and `dev` environments | Environment configuration ([[FND-environment-management]]) | DevOps |
| Trusted package keys | Per environment list | `config.trusted_package_key` (platform-level), maker-checker by `platform_security` | Platform security |
| Cross-region import of a promotion package | Off; allowed per import with `tenant_owner` approval on the target | Per import | Tenant owner |
| Entitlement for tenant export and import | `feature.config.packages` (see [[PKG-settings-billing-and-plans]]) | Plan | Billing |
| Number of sandbox tenants | `limit.config_sandboxes` | Plan | Billing |

<!-- section:adapters -->
## Providers and extension points

- **Component handlers.** Each component kind registers `{ kind, schemaVersion, export(tx, key), validate(component), diff(base, local, incoming): JsonPatch, toChangeItems(component, params): ChangeItem[] }`. Settings, roles and permission sets, custom fields, forms, case-type blueprints, templates, decision tables, automation rules, thresholds, terminology, themes, integration definitions and report templates each ship a handler from their owning package. A kind without a handler cannot be exported.
- **Signer.** `Signer` interface with `AwsKmsSigner` and `AzureKeyVaultSigner` (ES256), selected by `CLOUD` ([[FND-environment-management]]).
- **Storage.** Archives are stored through [[PKG-object-storage-abstraction-s3]] in the tenant's home-region bucket under `config-packages/{tenantId}/` (exports, uploads) or `config-packages/platform/` (blueprints), and scanned by the malware pipeline before unpacking ([[PKG-encryption-at-rest-signed-urls]]).
- **Personal-data scanner.** The same detector used by settings save-time checks (emails, phone numbers, Indian PAN and Aadhaar patterns, passport-like numbers) runs on every text field of every component except `fixture_set`, which must carry the synthetic marker on every record.

<!-- section:errors -->
## Error model

| Error | Retryable | Caller action |
|---|---|---|
| `PackageSignatureInvalidError` | No | Refuse import; security event `config.package.verification_failed` |
| `PackageKeyUntrustedError` | No | Ask platform security to review the trust list; never bypass |
| `PackageDigestMismatchError` | No | Re-download; refuse if it persists |
| `PackageSchemaUnsupportedError` (`platformCompat` outside range) | No | Upgrade the platform first or re-export from a compatible environment |
| `PackageContainsPersonalDataError` | No | Fix the source configuration; the error lists component and field |
| `PackageContainsIdentifiersError` | No | Exporter bug or tampering; refuse |
| `MissingRequirementError` | No | Install the required reference data or extension first |
| `NotEntitledError` | No | Component needs a feature the target tenant lacks; skip it or upgrade the plan |
| `CrossCustomerImportError` | No | Requires platform approval |
| Storage or KMS unavailable | Yes (backoff) | Job retries; plan shows "verification pending" |

<!-- section:nfr -->
## Performance and limits

- Export of a full snapshot (about 3,000 components) completes within 2 minutes p95; planning an import within 60 seconds p95.
- Applying a blueprint at provisioning completes within 5 minutes, including the change set publish and seeding fixture data for the sandbox.
- Verification (digests plus signature) for a 50 MB archive within 10 seconds.
- Package operations are rate limited to 10 exports and 10 imports per tenant per hour.

<!-- section:versioning -->
## Versioning and compatibility

- The archive format is `nomology.config-package/v1`. A new format version is introduced only with a reader for the previous one; the platform reads the current and previous format.
- Each component kind has its own `schemaVersion`; `platformCompat.minSchema` is the highest component schema generation used. Import upgrades older component schemas through the kind's migration functions; it never downgrades.
- Blueprints and extensions use semver: patch for content fixes, minor for new optional components, major when a managed component changes in a way tenants must review. Every published version is immutable and kept while any tenant's lineage references it.
- **Upgrade.** `planBlueprintUpgrade` computes a three-way diff between the version the tenant applied (base), the tenant's current published configuration (local) and the new version (incoming). Components the tenant never changed fast-forward; managed components always take incoming; edited components with incoming changes are conflicts for the admin to decide. The result is a draft change set. This is the layering idea of managed solutions in Power Platform [R2], with the tenant's own changes always visible as a layer.

<!-- section:testing -->
## Test contract

- Round trip: export a snapshot of each fixture tenant (`arb-inst`, `odr-inst`, `cord`, `us-demo`, [[FND-environments]] ENVS-8) and import into an empty tenant; the published configuration is identical by canonical digest.
- Tamper tests: changing one byte of a component, the manifest or an asset fails verification; an archive signed by an untrusted key is refused.
- Data protection: a component containing an email address, a phone number or a UUID of a real record is refused at export and at import.
- Three-way diff: table-driven tests for fast-forward, conflict, managed override and removal.
- Isolation: an import into tenant B cannot reference tenant A's components; exports run under forced RLS against real Postgres.
- Blueprint smoke: each published blueprint version provisions a tenant in staging per region and passes the journey tests of its case types.

<!-- section:questions -->
## Open questions

- [ ] Is tenant configuration (fee schedules, institution templates) "customer data" under our contracts, so that moving a promotion package across regions needs contractual cover? Proposed: treat as customer confidential and require tenant-owner approval. (owner: legal)
- [ ] Should tenants be able to share packages with each other (a template marketplace)? Proposed: not at launch; only Nomology-curated extensions. (owner: product)
- [ ] Confirm the SEBI ODR timelines and fee rules to encode as managed constraints in `blueprint.sebi_odr_institution`. (owner: legal)
- [ ] Court programme blueprint content depends on the first court customer. (owner: CEO)
- [ ] Should snapshot packages be signed with a tenant-specific key so a tenant can prove an export is theirs? Proposed: platform key plus a tenant reference hash is enough. (owner: security lead)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Exports read only the source tenant's published configuration under forced RLS; imports write only draft change-set items in the target tenant's context. Packages carry logical keys, never IDs, and the exporter fails if it finds record IDs. Promotion packages are limited to tenants of the same customer unless a platform admin approves. Blueprints are platform-level and read-only to tenants.

<!-- check:security -->
### Security of the API surface

Every non-local package is signed with a KMS-held ES256 key; imports verify the signature against a per-environment trust list (changes to it are maker-checker by `platform_security`), the manifest digest and every component digest. Archives are malware-scanned before unpacking, unpacked with path traversal protection (fixed layout, no symlinks, size limits), and parsed with strict schemas. Secrets are never exported; integration definitions carry empty secret slots. Imports cannot raise permissions beyond the target's entitlements and platform bounds, because they become normal change sets.

<!-- check:data-protection -->
### Personal data handling

Packages contain configuration only. A personal-data detector runs on every text field at export and import; `fixture_set` data must be synthetic and marked. Exports are stored for 30 days in the home-region bucket and downloadable only by tenant admins through 15-minute signed URLs. Snapshot packages in offboarding exports follow the export bundle's retention ([[PKG-data-retention-legal-hold-and]]).

<!-- check:residency -->
### Region awareness

Archives are stored in the tenant's home-region bucket; blueprint releases are published to each region's platform bucket separately. Cross-region import is off by default and needs tenant-owner approval per import; because packages contain no personal data, no personal data moves.

<!-- check:audit -->
### Audit events

Export, upload, verification failure, plan, apply, blueprint publish, blueprint apply and upgrade are audited (`admin.package.exported`, `admin.package.imported`, `admin.blueprint.published`, `admin.blueprint.applied`) with package key, version, digest, signer key ID and the resulting change set. The audit event is written in the same transaction as the state change, so it cannot be skipped.

<!-- check:observability -->
### Observability

Traces for each job (`package-export`, `package-verify`, `package-plan`) and for `ApplyBlueprintWorkflow`, with tenant ID as an attribute and no component content. Metrics: `config.package.export.duration`, `config.package.import.outcome` (counter by outcome), `config.package.verification_failures`. Verification failures also emit a security event ([[OBS-security-events]]).

<!-- check:resilience -->
### Failure behaviour

Export, verify and plan jobs are idempotent by export or import ID and retried with backoff on storage or KMS failure. `applyImport` is idempotent per import ID (a second call returns the same change set). `ApplyBlueprintWorkflow` uses Temporal activities with idempotency keys per step, so a retry after a crash does not create duplicate change sets.

<!-- check:change-safety -->
### Change and release safety

Imports never publish; they create drafts reviewed under the target tenant's policy. Blueprint upgrades are offered, not forced, and show a three-way diff. Managed components change only in a major or minor blueprint release published under platform maker-checker. The archive format and component schemas are versioned with readers for the previous version.

<!-- check:testing -->
### Testing

Round-trip, tamper, personal-data, identifier, three-way diff and isolation tests run in CI on every change to `packages/config-packages` and to any registered component handler; blueprint smoke tests run in staging in every region before a blueprint version can be published.

<!-- citations -->
## Citations

```json
[
  {
    "body": "IETF",
    "id": "R1",
    "ident": "RFC 8785",
    "kind": "standard",
    "title": "JSON Canonicalization Scheme (JCS)",
    "url": "https://www.rfc-editor.org/rfc/rfc8785.html"
  },
  {
    "id": "R2",
    "kind": "vendor",
    "title": "Microsoft Learn: Solution concepts (Power Platform ALM)",
    "url": "https://learn.microsoft.com/en-us/power-platform/alm/solution-concepts-alm",
    "vendor": "Microsoft"
  },
  {
    "id": "R3",
    "kind": "vendor",
    "title": "Salesforce Help: Promote Work Items Through Your Pipeline (DevOps Center)",
    "url": "https://help.salesforce.com/s/articleView?language=en_US&id=platform.devops_center_work_items_promote.htm&type=5",
    "vendor": "Salesforce"
  },
  {
    "id": "R4",
    "issuer": "Securities and Exchange Board of India",
    "jurisdiction": "IN",
    "kind": "regulation",
    "ref": "Amendment (December 2023) to circular dated 31 July 2023 on Online Resolution of Disputes in the Indian Securities Market",
    "status": "in force (provisions consolidated in SEBI master circulars)",
    "title": "SEBI circular: Amendment to circular dated July 31, 2023 on Online Resolution of Disputes in the Indian Securities Market",
    "url": "https://www.sebi.gov.in/legal/circulars/dec-2023/amendment-to-circular-dated-july-31-2023-on-online-resolution-of-disputes-in-the-indian-securities-market_80110.html"
  }
]
```

<!-- end -->
