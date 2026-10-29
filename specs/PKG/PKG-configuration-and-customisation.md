---
id: "PKG-configuration-and-customisation"
title: "Configuration and Customisation"
parent: "PKG"
order: 8
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "Parent of the configuration backbone: `@nomology/config-core` artefact versioning and pinning, with the scope hierarchy, the change lifecycle and configuration packages as child nodes; every tenant customisation is declarative, versioned, reviewed and reversible"
links: []
rev: 3
syncHash: "2c8814a385166d69"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.8 Configuration and Customisation

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Parent of the configuration backbone: `@nomology/config-core` artefact versioning and pinning, with the scope hierarchy, the change lifecycle and configuration packages as child nodes; every tenant customisation is declarative, versioned, reviewed and reversible

<!-- section:purpose -->
## Purpose and scope

Tenants (arbitral institutions, SEBI ODR institutions, the CORD tenant, court and government programmes) need different fields, forms, procedures, documents, branding, rules and alert thresholds without code changes. This node is the parent of the **configuration backbone** that makes that safe, and it specifies `@nomology/config-core`, the package that versions **configuration artefacts** and pins them to cases.

The backbone has four parts:

| Part | Node | Answers |
|---|---|---|
| Scope hierarchy and resolution | [[PKG-configuration-scope-hierarchy]] | Which value applies at platform, region, offering, tenant, unit, case type, case and user level, and why |
| Change lifecycle | [[PKG-configuration-lifecycle]] | How any change is drafted, validated, reviewed (maker-checker), previewed, published, scheduled and rolled back; sandboxes |
| Packages and blueprints | [[PKG-configuration-packages]] | How configuration moves between tenants and environments, and how tenants are created from blueprints |
| Settings | [[PKG-settings]], [[PKG-settings-catalogue]], [[PKG-settings-data-model]] | Key-value settings and their catalogues |

Artefact kinds and their owning child:

| Artefact kind | Child node | Package |
|---|---|---|
| `entity_definition` (custom fields) | [[PKG-metadata-management-entity]] | `@nomology/metadata` |
| `form` | [[PKG-forms-and-form-builder]] | `@nomology/forms` |
| `case_type_blueprint` (process definition, see [[WF-process-definition-model]]) | [[PKG-workflow-templates]] | `@nomology/workflow-templates` |
| `document_template`, `notification_template` | [[PKG-document-and-notification]] | `@nomology/templates` |
| `theme` | [[PKG-branding-and-theming]] | `@nomology/ui` theming |
| `terminology_overrides` | [[PKG-tenant-terminology-and-copy]] | `@nomology/i18n` |
| `threshold_set` | [[PKG-thresholds-and-alert]] | `@nomology/thresholds` |
| `decision_table` | [[PKG-rules-and-decision-engine]] | `@nomology/rules` |
| `automation_rule` | [[WF-automation-rules]] | `@nomology/automation` |
| `report_template` | [[RPT-configurable-report-templates]] | `@nomology/reports` |

Roles and permission sets ([[PKG-roles-and-permission-sets]]) and integration definitions ([[INT-connections-admin]]) are not artefacts of this package but use the same change lifecycle and travel in the same packages.

**Principles.** All customisation is declarative JSON validated against a schema; no tenant-supplied code, scripts or free expressions (expressions use closed vocabularies defined by each kind). Published versions are immutable. Running cases are pinned and never change because of a publish. Every change is a change set with a diff and a review proportional to its risk. AI may draft configuration but a human approves it ([[APP-admin-copilot]]).

**Does not:** hold key-value preferences ([[PKG-settings]]); run processes (the Temporal interpreter, [[WF-separation-of-concerns-temporal]]); hold release flags ([[PKG-feature-flags]]) or deployment configuration ([[FND-environment-management]]).

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Use case |
|---|---|
| Tenant admin console ([[APP-tenant-admin-console]]) and authoring studio ([[WF-workflow-authoring-studio]]) | Edit drafts, validate, preview, add to a change set, compare versions, view history |
| Change lifecycle ([[PKG-configuration-lifecycle]]) | Calls `stage`, `validate`, `publishVersions` and `inverse` for artefact items in a change set |
| Case creation ([[DOM-cases]]) | `pinForCase` resolves the published versions of every artefact a case type needs and stores them in `config.case_config_pin` together with the setting pin |
| Temporal workflows | Receive pinned version IDs in workflow input; load artefacts once at start through an Activity |
| Packages ([[PKG-configuration-packages]]) | Export and import artefacts as components by logical key |
| Workflow versioning ([[WF-workflow-versioning]]) | Move selected running cases to a new blueprint version through a reviewed migration item |
| Platform | Ship default artefacts in blueprints per tenant type |

<!-- section:api -->
## Public API

```ts
// packages/config-core/src/index.ts (server-only)
export type ArtefactKind = 'entity_definition' | 'form' | 'case_type_blueprint' | 'document_template' | 'notification_template'
  | 'theme' | 'terminology_overrides' | 'threshold_set' | 'decision_table' | 'automation_rule' | 'report_template';
export type VersionStatus = 'draft' | 'in_review' | 'approved' | 'published' | 'superseded' | 'retired';
export interface ArtefactRef { kind: ArtefactKind; key: string; version: number; id: string }

/** Each child registers its kind. */
export function registerKind<K extends ArtefactKind, B>(def: {
  kind: K; schema: import('zod').ZodType<B>; schemaVersion: number;
  validate: (tx: TenantTx, body: B, ctx: { changeSetId: string }) => Promise<ValidationIssue[]>;   // references, accessibility, policy
  dependencies: (body: B) => { kind: ArtefactKind; key: string; version?: number }[];
  auditClass: AuditClass | ((body: B) => AuditClass);   // e.g. decision tables: maker_checker
  updatePermission: string;                             // e.g. 'workflow.definition:update'
  approvePermission: string;                            // e.g. 'workflow.definition:approve'
  diff: (a: B, b: B) => JsonPatch;                      // RFC 6902, rendered by the change-set viewer
  migrate?: (body: unknown, fromSchema: number) => B;   // schema upgrades
  toPackageComponent?: (body: B) => unknown;            // logical keys only
}): void;

/** Draft and stage */
export function saveDraft(tx: TenantTx, kind: ArtefactKind, key: string, body: unknown): Promise<{ versionId: string; issues: ValidationIssue[] }>;
export function stage(tx: TenantTx, changeSetId: string, versionId: string): Promise<ChangeItemRef>;   // adds an 'artefact.version' item

/** Called by the change lifecycle only */
export function validateItem(tx: TenantTx, item: ChangeItemRef): Promise<ValidationIssue[]>;
export function publishVersions(tx: TenantTx, items: ChangeItemRef[], opts: { effectiveFrom?: Date }): Promise<ArtefactRef[]>;  // previous → superseded
export function inverse(tx: TenantTx, item: ChangeItemRef): Promise<ChangeItemDraft>;               // for revert

/** Reads */
export function getPublished(tx: TenantTx, kind: ArtefactKind, key: string, at?: Date): Promise<ArtefactRef | null>;
export function load<B>(tx: TenantTx, ref: ArtefactRef): Promise<B>;                                 // immutable body, cached by id
export function history(tx: TenantTx, kind: ArtefactKind, key: string): Promise<ArtefactVersionSummary[]>;
export function diff(tx: TenantTx, a: ArtefactRef, b: ArtefactRef): Promise<JsonPatch>;
export function retire(tx: TenantTx, cs: ChangeSetRef, ref: ArtefactRef): Promise<ChangeItemRef>;  // hidden from new pins, still loadable

/** Pinning */
export function pinForCase(tx: TenantTx, caseId: string, caseType: { key: string }): Promise<ConfigPin>;  // with settings.pinForCase, one row
export interface ConfigPin { caseId: string; blueprint: ArtefactRef; artefacts: ArtefactRef[] }
```

Version lifecycle (artefact versions follow their change set; states as in the shared model):
```
draft --(change set submitted)--> in_review --(approved)--> approved --(published)--> published --(newer version published)--> superseded
                                                                                         \--(retire item published)--> retired
```
Export and import of artefacts moved to [[PKG-configuration-packages]]; the previous `exportPack` / `importPack` functions are replaced by `exportPackage` / `planImport` / `applyImport` there.

<!-- section:tenant -->
## Tenant context

Artefact tables (`config.artefact`, `config.artefact_version`) and pins (`config.case_config_pin`) are tenant-owned with forced RLS ([[PKG-settings-data-model#tenancy]]). A tenant's artefacts can reference only that tenant's artefacts and platform reference data; dependencies are resolved inside `withTenant`. Blueprint-supplied artefacts may be `managed` (tenant cannot edit; Nomology updates them through blueprint upgrades). Platform default artefacts are not shared rows: they are copied into the tenant by applying a blueprint package, so a tenant's configuration never changes because Nomology edits a default.

<!-- section:config -->
## Configuration

| Setting / limit | Default (proposed) | Where |
|---|---|---|
| Review class per kind | `decision_table`, `case_type_blueprint`, `report_template`: maker_checker; `form`, `document_template`, `automation_rule`, `threshold_set`, `entity_definition`: sensitive; `theme`, `notification_template`, `terminology_overrides`: standard | Kind registration; tenants may tighten with `access.change_control.*` ([[PKG-configuration-lifecycle]]) |
| Maximum artefact body | 512 KB JSON | Code |
| Published versions kept loadable | Unlimited while pinned; unpinned superseded or retired versions kept 8 years ([[PKG-settings-data-model#retention]]) | Code |
| Effective-from scheduling | Allowed for all kinds through the change set | Lifecycle |
| Artefacts per tenant | Per kind limits in each child; custom fields bounded by `limit.custom_fields_per_entity` | Entitlements |

<!-- section:errors -->
## Error model

`ValidationFailedError` (with issues; blocks submit and publish), `DependencyMissingError` (references an unpublished or retired artefact not in the same change set), `ArtefactImmutableError` (edit of a version that left draft), `SchemaVersionUnsupportedError`, `ConcurrencyConflictError`. Maker-checker errors (`MakerCheckerError`) are raised by the change lifecycle. None are retryable.

<!-- section:versioning -->
## Versioning and compatibility

Artefact versions are immutable integers per key. Each kind has a `schemaVersion`; when it changes, `migrate` upgrades drafts on load, and published bodies are upgraded by a reviewed batch change set that creates new versions (old versions stay loadable by their reader code until no pin references them). The package API follows semver; adding a kind is a minor release.

<!-- section:testing -->
## Test contract

A shared suite runs for every registered kind: save draft, validate, stage, submit, maker-checker approve, publish, supersede, retire, revert through `inverse`, pin stability (a publish never changes an existing pin), schema migration of drafts, diff rendering, package round trip, and tenant isolation against real Postgres with forced RLS.

<!-- section:questions -->
## Open questions

- [ ] Do institution tenants want Nomology's implementation team to author changes in their production tenant with a tenant admin as checker, or always configure themselves? Carried to [[PKG-configuration-lifecycle#questions]]. (owner: CEO, COO)
- [x] ~~Should configuration packs be shareable between tenants as a marketplace?~~ Decided for launch: only Nomology-curated blueprints and extensions ([[PKG-configuration-packages]]).
- [ ] Should tenant-defined entity types (beyond custom fields on core entities) become an artefact kind in a later phase? See [[PKG-metadata-management-entity#questions]]. (owner: product)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

All artefacts, versions and pins are tenant-owned under forced RLS; dependency resolution runs inside the tenant context; blueprint defaults are copied in, not shared; packages carry logical keys only and import as drafts.

<!-- check:security -->
### Security of the API surface

Artefacts are declarative JSON validated by Zod and semantic validators; no tenant code, scripts or free expressions; template rendering and conditions use closed, sandboxed vocabularies defined per kind. Publishing requires the kind's approve permission under the change lifecycle's maker-checker rules.

<!-- check:data-protection -->
### Personal data handling

Artefacts are configuration and must not contain personal data; the save-time detector used for settings also scans artefact text fields. Custom field definitions declare a classification for the values they will hold ([[PKG-metadata-management-entity]]).

<!-- check:residency -->
### Region awareness

Artefacts live in the tenant's regional database. Packages moved between environments or regions contain configuration only and are imported as drafts ([[PKG-configuration-packages]]).

<!-- check:audit -->
### Audit events

Every version change is part of a change set, audited with author, approver, reason and diff ([[PKG-configuration-lifecycle]]). Pins record which versions governed each case, so the configuration behind any case can always be shown.

<!-- check:observability -->
### Observability

Metrics per kind: drafts, publishes, validation failures, load latency and cache hit ratio for published bodies; traces include kind, key and version as attributes.

<!-- check:resilience -->
### Failure behaviour

Published bodies are immutable and cached by version ID, so loading is safe to retry; workflows load pinned artefacts once at start through an Activity.

<!-- check:change-safety -->
### Change and release safety

Running cases are pinned at creation; publishing affects new cases only; effective-from dates coordinate changes; schema changes are migrated into new versions, never edited in place; reverts are one action.

<!-- check:testing -->
### Testing

The shared lifecycle suite runs for every registered kind on every change to `packages/config-core` or a kind's package, including isolation tests against real Postgres with RLS.

<!-- end -->
