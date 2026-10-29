---
id: "PKG-metadata-management-entity"
title: "Metadata management (entity definitions, custom fields)"
parent: "PKG-configuration-and-customisation"
order: 1
type: "feature"
template: "package"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 3
syncHash: "f079811521b01af5"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.8.1 Metadata management (entity definitions, custom fields)

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

`@nomology/metadata` lets a tenant extend the platform's core entities with its own fields (for example a SEBI ODR institution adding "Market participant type" and "Complaint category (SCORES)", or an arbitral institution adding "Applicable law" and "Language of arbitration") and describes every entity's fields, core and custom, in one machine-readable catalogue that forms, reports, search, exports, privacy tooling, the public API and the admin copilot read.

How custom fields fit the configuration backbone:
- **Scopes** ([[PKG-configuration-scope-hierarchy]]): field definitions exist at `tenant` scope (one definition per entity per tenant). A **case-type blueprint** selects which fields it uses and may make a field required at given stages, hide it, or set a default for that case type ([[WF-process-definition-model]]); it cannot change the field's type or classification. There are no unit-, case- or user-level definitions. Nomology can ship **platform-managed fields** in a blueprint (for example fields an aggregator report needs, [[RPT-aggregators]]), marked `managed`: the tenant can use and label them but not change or retire them.
- **Lifecycle** ([[PKG-configuration-lifecycle]]): an entity definition is an artefact of kind `entity_definition`; adding, changing or retiring fields is a change set. Adding a field with classification `personal` or `sensitive_personal`, or changing visibility, is `maker_checker`; other changes are `sensitive`.
- **Packages** ([[PKG-configuration-packages]]): definitions travel by field key; values never travel.
- **Entitlements**: the number of custom fields per entity is bounded by `limit.custom_fields_per_entity` ([[PKG-settings-billing-and-plans]]).

**Does not:** let tenants create new entity types at launch (core entities only: Case, Party, Representative, Hearing, Document, Invoice, Neutral profile); change core columns; store values outside the owning entity (custom values live on the entity row).

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Use |
|---|---|
| Form builder ([[PKG-forms-and-form-builder]]) | Fields available for placement, with types and validation |
| Case-type blueprints ([[WF-process-definition-model]], [[WF-workflow-authoring-studio]]) | Select fields per case type, stage-specific required rules, defaults |
| Domain write paths | Validate `custom_fields` on create and update |
| Search ([[PKG-search]]) | Index custom fields marked `searchable` |
| Reports and aggregator exports ([[RPT-configurable-report-templates]]) | Map custom fields into report columns |
| Public API ([[INT-public-api-cases-and-parties]]) | Expose custom fields in OpenAPI per tenant under `customFields` |
| Privacy tooling ([[SEC-data-principal-rights-requests]]) | Find personal data in custom fields by classification |
| Decision tables and automation rules ([[PKG-rules-and-decision-engine]], [[WF-automation-rules]]) | Use custom fields as inputs and conditions |
| Packages ([[PKG-configuration-packages]]) | Export and import definitions by key |
| Admin copilot ([[APP-admin-copilot]]) | Read the field catalogue; propose new fields as drafts with a classification suggestion that a human must confirm |

<!-- section:api -->
## Public API

```ts
// packages/metadata/src/index.ts
export type CoreEntity = 'case' | 'party' | 'representative' | 'hearing' | 'document' | 'invoice' | 'neutral_profile';
export type FieldType = 'text' | 'long_text' | 'number' | 'money' | 'date' | 'datetime' | 'boolean'
  | 'select' | 'multi_select' | 'country' | 'currency' | 'email' | 'phone' | 'party_ref' | 'user_ref';

export interface CustomFieldDef {
  key: string;                     // ^[a-z][a-z0-9_]{1,40}$, unique per entity per tenant, never reused
  entity: CoreEntity; type: FieldType;
  label: LocalisedText;            // per enabled locale (locale.languages.enabled); fallback to tenant default locale
  help?: LocalisedText;
  required?: boolean | { whenStage: string[] };
  validation?: { min?: number; max?: number; maxLength?: number; pattern?: string /* RE2-safe */; options?: { value: string; label: LocalisedText }[] };
  classification: 'internal' | 'case_participants' | 'personal' | 'sensitive_personal';
  visibility: 'case_participants' | 'side_restricted' | 'tribunal_only' | 'institution_internal'; // feeds authz field filtering
  searchable?: boolean; reportable?: boolean; apiExposed?: boolean;
  managed?: boolean;               // shipped by a Nomology blueprint; tenant may relabel only
  status: 'active' | 'retired';
}
export interface EntityDefinition { entity: CoreEntity; version: number; fields: CustomFieldDef[] }   // artefact kind 'entity_definition'

/** Case-type usage, declared inside the case-type blueprint (not here) and read through this helper */
export interface CaseTypeFieldUsage { key: string; requiredAtStages?: string[]; hidden?: boolean; default?: unknown }

export function getDefinition(tx: TenantTx, entity: CoreEntity, version?: number): Promise<EntityDefinition>;
export function effectiveFields(tx: TenantTx, entity: CoreEntity, caseType?: { key: string; version: number }): Promise<(CustomFieldDef & Partial<CaseTypeFieldUsage>)[]>;
export function validateValues(def: EntityDefinition, values: unknown, ctx: { stage?: string; caseType?: CaseTypeFieldUsage[] }):
  { ok: true; values: Record<string, unknown> } | { ok: false; issues: FieldIssue[] };
export function zodFor(def: EntityDefinition, ctx?: { stage?: string; caseType?: CaseTypeFieldUsage[] }): import('zod').ZodTypeAny;  // forms and API
export function jsonSchemaFor(def: EntityDefinition): object;                                       // OpenAPI generation
export function project(def: EntityDefinition, values: Record<string, unknown>, principalCanSee: (visibility: string) => boolean): Record<string, unknown>;
export function catalogue(tx: TenantTx): Promise<FieldCatalogue>;   // core + custom fields, with classification, for privacy, reports and the copilot

/** Admin operations (all create change-set items; see PKG-configuration-lifecycle) */
export function draftAddField(tx: TenantTx, cs: ChangeSetRef, field: Omit<CustomFieldDef, 'status'>): Promise<ChangeItemRef>;
export function draftUpdateField(tx: TenantTx, cs: ChangeSetRef, entity: CoreEntity, key: string, patch: FieldPatch): Promise<ChangeItemRef>;  // type and classification immutable
export function draftRetireField(tx: TenantTx, cs: ChangeSetRef, entity: CoreEntity, key: string): Promise<ChangeItemRef>;
export function usage(tx: TenantTx, entity: CoreEntity, key: string): Promise<{ caseTypes: string[]; forms: string[]; reports: string[]; automationRules: string[]; rowsWithValue: number }>;
```

Storage: each core entity table has `custom_fields jsonb not null default '{}'` and `custom_fields_def_version int`; values are validated by `validateValues` against the definition version recorded on the row. A `CHECK (jsonb_typeof(custom_fields) = 'object' AND pg_column_size(custom_fields) < 32768)` constraint caps size.

Admin surfaces: `/admin/workflows/fields` (all entities) and `/admin/workflows/fields/[entity]` (list, add, edit, retire, usage), with permissions `metadata.field:update` (default roles `workflow_designer`, `tenant_admin`) and `metadata.field:approve` (`tenant_admin`, `tenant_owner`). Tenant admin API: `GET /admin/v1/data-model/{entity}/fields`, and change-set items through `POST /admin/v1/change-sets/{id}/items` ([[INT-tenant-admin-api]]).

<!-- section:usage -->
## Usage examples

```ts
const def = await metadata.getDefinition(tx, 'case');
const parsed = metadata.validateValues(def, input.customFields, { stage: c.status });
if (!parsed.ok) return { errors: parsed.issues };
await tx.case.update({ where: { id }, data: { customFields: parsed.values, customFieldsDefVersion: def.version } });
```

<!-- section:tenant -->
## Tenant context

Entity definitions are tenant-owned configuration artefacts ([[PKG-configuration-and-customisation]]); values live on tenant-owned entity rows under forced RLS. `project()` removes fields whose `visibility` the viewer is not entitled to, using the same tiers as [[PKG-rbac-abac-case-level-party]], so custom fields cannot become a side channel for tribunal-only or institution-internal information. Case-type usage is read from the case's pinned blueprint version, so a later blueprint change does not alter which fields a running case requires.

<!-- section:config -->
## Configuration

| Limit or rule (proposed) | Value | Source |
|---|---|---|
| Custom fields per entity per tenant | Plan limit `limit.custom_fields_per_entity` (starter 20, standard 100, enterprise contract); hard platform maximum 200 | [[BIL-plans-entitlements-and-usage]] |
| Select options per field | 500 | Code |
| `custom_fields` size per row | < 32 KB | Database constraint |
| Field key reuse | Forbidden (retired keys stay reserved) | Code |
| Removing a field | Retire only; values kept until retention deletes the row | Code |
| Review class | Add or change a `personal` / `sensitive_personal` field, change visibility, retire a field used by a report: `maker_checker`; other changes: `sensitive` | Kind registration |
| Managed fields | Created only by blueprints; tenant may change label and help text only | Kind registration |

<!-- section:errors -->
## Error model

`FieldValidationError` (per field issues, localised), `DefinitionVersionMismatchError` (row written with a newer definition than the reader knows — reload), `FieldLimitExceededError` on publish.

<!-- section:nfr -->
## Performance and limits

Validation of a 100-field payload ≤ 2 ms; definitions cached by version ID (immutable).

<!-- section:versioning -->
## Versioning and compatibility

Definitions are versioned artefacts; changing a field's type or classification is not allowed (retire and add a new key). Adding options or relaxing validation is a new version that applies to new writes; existing values remain valid under the version they were written with. Tightening validation (for example making a field required) applies to new cases through the case-type blueprint, or to running cases only through a reviewed migration ([[WF-workflow-versioning]]). Managed fields change only through a blueprint upgrade.

<!-- section:testing -->
## Test contract

Property tests for every field type validator; `project()` tests across all visibility tiers and personas; size-limit constraint test; OpenAPI generation snapshot tests per definition.

<!-- section:questions -->
## Open questions

- [ ] Are tenant-defined entity types (for example "Settlement offer") needed in phase 4, or can they wait? Proposed: wait.
- [ ] Should `sensitive_personal` custom fields be field-encrypted automatically via [[PKG-encryption-utilities-key]]? Proposed: yes, which makes them non-searchable.
- [ ] Do aggregator report formats (NSE, MSME) require fixed custom field keys across tenants? Proposed: yes, shipped as managed fields in the SEBI ODR blueprint. (owner: product, reporting)
- [ ] Should unit-specific fields be allowed (an office that collects extra data)? Proposed: no; use case-type selection instead. (owner: product)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Definitions and values are tenant-owned under forced RLS; definitions of tenant A are never consulted for tenant B; `project()` applies visibility tiers per viewer.

<!-- check:security -->
### Security of the API surface

Patterns are RE2-safe (no catastrophic backtracking); values validated server-side with generated zod schemas; field keys restricted to a safe pattern; size capped by a database constraint.

<!-- check:data-protection -->
### Personal data handling

Every custom field must declare a classification at creation; adding a personal field is maker-checker and the builder shows a data-minimisation prompt; the field catalogue feeds rights requests, retention and log redaction; `sensitive_personal` fields are encrypted and excluded from search; AI-suggested classifications must be confirmed by a human.

<!-- check:residency -->
### Region awareness

Definitions and values live in the tenant's regional database only; OpenAPI documents generated per tenant are served from the regional stack.

<!-- check:audit -->
### Audit events

Definition changes are change-set items audited with diffs, author, approver and reason ([[PKG-configuration-lifecycle]]); changes to custom field values are audited by the owning domain operation with field keys and hashed values for personal fields, using the classification from the definition.

<!-- check:change-safety -->
### Change and release safety

Definition versions are recorded per row; field types and classifications cannot change; retired keys are reserved; case-type usage is pinned with the blueprint; new definitions affect new writes only; `usage()` shows what depends on a field before it is retired.

<!-- check:testing -->
### Testing

Property tests per field type, `project()` visibility tests across tiers and personas, database size-constraint tests and OpenAPI snapshot tests run on every change to `packages/metadata`.

<!-- end -->
