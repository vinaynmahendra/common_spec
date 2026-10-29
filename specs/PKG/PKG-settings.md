---
id: "PKG-settings"
title: "Settings"
parent: "PKG"
order: 7
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "`@nomology/settings`: typed setting definitions and the single resolver for the eight configuration scopes (platform → region → offering → tenant → unit → case type → case → user) with locks, bounds, entitlements, case pins, point-in-time reads and explanations; parent of the settings catalogue and data model"
links: []
rev: 4
syncHash: "9589acc1da7f704d"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.7 Settings

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> `@nomology/settings`: typed setting definitions and the single resolver for the eight configuration scopes (platform → region → offering → tenant → unit → case type → case → user) with locks, bounds, entitlements, case pins, point-in-time reads and explanations; parent of the settings catalogue and data model

<!-- section:purpose -->
## Purpose and scope

`@nomology/settings` is the only way code reads or writes a configurable value. It holds typed **setting definitions** (declared in each owning package with `defineSetting`) and resolves the **effective value** for any context along the eight scopes of [[PKG-configuration-scope-hierarchy]]: `platform → region → offering → tenant → unit → case_type → case → user`, applying locks, hard bounds, plan entitlements and case pins, and returning provenance ("set for the Mumbai office by A. Rao on 3 March, locked by the tenant").

Where the detail lives:
- Resolution rules, pinning, caching: [[PKG-configuration-scope-hierarchy]].
- Tables, RLS and migrations: [[PKG-settings-data-model]].
- How a value changes (change sets, maker-checker, preview, rollback): [[PKG-configuration-lifecycle]].
- Which settings exist: the domain catalogues indexed in [[PKG-settings-catalogue]].
- Tenant copy overrides: [[PKG-tenant-terminology-and-copy]] (stored as artefacts, selected by a setting).
- Personal preferences UI: [[PKG-personalisation]].

Boundaries kept from the earlier version of this node:
- **Branding**: settings hold only the pointer to the active theme version (`brand.theme.active_version`); the theme is an artefact ([[PKG-branding-and-theming]]).
- **Features**: availability comes from entitlements ([[BIL-plans-entitlements-and-usage]]), rollout from release flags ([[PKG-feature-flags]]); settings hold the tenant's choices about features it already has. A definition declares its gating entitlement, and the resolver applies it.
- **Limits**: hard ceilings come from entitlements (`limit.*`); a setting lets a tenant choose a lower operating limit, so the effective limit is `min(entitlement, setting)`, enforced by the resolver as a bound.

**Does not:** hold secrets ([[INF-secrets-and-keys]], [[PKG-encryption-utilities-key]]); hold deployment configuration ([[FND-environment-management]]); hold versioned artefacts such as forms, blueprints, templates or decision tables ([[PKG-configuration-and-customisation]]); decide access ([[PKG-authorization]]).

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Example keys (catalogue) |
|---|---|
| Authentication | `auth.mfa.required_personas`, `auth.session.idle_timeout_min` ([[PKG-settings-security-and-identity]]) |
| Authorisation | `access.change_control.review_all_changes`, `access.case.read_after_close_days` ([[PKG-settings-access-control]]) |
| Cases and filings | `case.intake.party_self_filing`, `case.filing.max_upload_mb` (≤ `limit.upload_mb`) ([[PKG-settings-cases-and-workflows]]) |
| Notifications | `notify.quiet_hours.start` (tenant default, user override), `notify.channel.sms.daily_budget` ([[PKG-settings-notifications]]) |
| Integrations | `integration.webhooks.max_endpoints` ([[PKG-settings-integrations]]) |
| Branding, content, locale | `brand.theme.active_version`, `content.terminology.override_set`, `locale.languages.enabled` ([[PKG-settings-branding-content]]) |
| AI | `ai.features.drafting_assist.enabled` ([[PKG-settings-ai]]) |
| Retention and privacy | `data.retention.case_record_years`, `data.files.allow_unscannable_with_review` ([[PKG-settings-data-and-privacy]]) |
| Billing | `billing.usage.alert_thresholds_pct`, `billing.case_fees.schedule` ([[PKG-settings-billing-and-plans]]) |
| Personal preferences | `personal.locale`, `personal.time_zone`, `personal.date_format` (feeds [[I18N-l10n]]) ([[PKG-settings-personal]]) |
| Platform operations | `platform.maintenance.window` ([[PKG-settings-platform-operations]]) |
| Temporal workflows | Receive `snapshot` or the case pin in workflow input |
| Admin console, admin API, admin copilot | `resolve`, `explain`, change-set writes |

Keys owned by other groups are listed as examples; the authoritative names are in each catalogue.

<!-- section:api -->
## Public API

```ts
// packages/settings/src/index.ts (server-only; types are client-safe in @nomology/settings-types)
import { z } from 'zod';
export type Scope = 'platform' | 'region' | 'offering' | 'tenant' | 'unit' | 'case_type' | 'case' | 'user';
export type AuditClass = 'standard' | 'sensitive' | 'maker_checker';
export type TakesEffect = 'immediate' | 'next_request' | 'next_sign_in' | 'new_cases_only' | 'running_cases'
  | 'next_billing_period' | 'next_job_run' | 'scheduled';

export interface SettingDef<S extends z.ZodTypeAny> {
  key: `${Domain}.${string}.${string}`;          // grammar in PKG-settings-catalogue
  schema: S;
  default: z.infer<S>;                           // platform default in code
  scopes: Scope[];                               // where a value may be set
  lockable?: boolean | 'platform_only';
  bounds?: Bound<z.infer<S>>;                    // range | enum_subset | subset_of | pattern | stricter_only
  entitlement?: `feature.${string}` | `limit.${string}`;
  pinning?: 'case_start' | 'live' | 'event';     // default 'live'
  caseOverridable?: boolean;
  migratable?: boolean;
  onOutOfBounds?: 'clamp' | 'fallback';
  auditClass: AuditClass;
  permission: `settings.${Catalogue}:write` | `case:configure` | 'self';
  takesEffect: TakesEffect;
  owner: string;                                 // owning package
  catalogueNode: string;                         // e.g. 'PKG-settings-data-and-privacy'
  label: LocalisedText; description: LocalisedText;
}
export function defineSetting<S extends z.ZodTypeAny>(def: SettingDef<S>): SettingHandle<z.infer<S>>;

export interface Resolved<T> {
  value: T;
  source: { scope: Scope | 'default'; ref?: string };
  locked: boolean; lockedAt?: Scope; managed: boolean;
  bound?: unknown; entitlement?: { key: string; granted: boolean };
  pinned: boolean; drift: boolean; valueVersion: number;
}

/** Reads (context from @nomology/tenant-context; options override parts of the chain) */
export function get<T>(h: SettingHandle<T>, opts?: ChainOverride): Promise<T>;
export function getMany(hs: SettingHandle<unknown>[], opts?: ChainOverride): Promise<Map<string, unknown>>;  // one round trip
export function resolve<T>(h: SettingHandle<T>, opts?: ChainOverride & { overlay?: string /* draft change set id */ }): Promise<Resolved<T>>;
export function resolveAt<T>(h: SettingHandle<T>, at: Date, opts?: ChainOverride): Promise<Resolved<T>>;    // point in time, no cache
export function explain(key: string, opts?: ChainOverride & { at?: Date }): Promise<Explanation>;          // every candidate and why
export interface ChainOverride { unitId?: string; caseTypeRef?: { key: string; version: number }; caseId?: string; membershipId?: string }

/** Case pinning */
export function pinForCase(tx: TenantTx, caseId: string, chain: ScopeChain): Promise<CasePinRef>;   // in the case-creation transaction
export function snapshot(hs: SettingHandle<unknown>[], opts?: ChainOverride): Promise<SettingsSnapshot>; // for Temporal input

/** Writes: always produce change-set items (PKG-configuration-lifecycle). */
export function draftSet<T>(tx: TenantTx, cs: ChangeSetRef, h: SettingHandle<T>, scope: Exclude<Scope, 'platform' | 'region' | 'offering' | 'case_type'>,
  value: T, opts?: { scopeId?: string; lock?: boolean; constraint?: Bound<T>; reason?: string }): Promise<ChangeItemRef>;
export function draftUnset(tx: TenantTx, cs: ChangeSetRef, h: SettingHandle<unknown>, scope: Scope, opts?: { scopeId?: string }): Promise<ChangeItemRef>;
export function setOneStep<T>(tx: TenantTx, h: SettingHandle<T>, scope: 'tenant' | 'unit', value: T, opts: { scopeId?: string; reason?: string }):
  Promise<{ published: true; resolved: Resolved<T> } | { published: false; changeSetId: string }>;   // console convenience; publishes only 'standard'
export function setCaseValue<T>(tx: TenantTx, h: SettingHandle<T>, caseId: string, value: T, opts: { reason: string; orderDocumentId?: string }): Promise<Resolved<T>>; // caseOverridable keys only
export function setPreference<T>(tx: TenantTx, h: SettingHandle<T>, value: T): Promise<Resolved<T>>;  // user scope, own membership only

/** Platform scopes (platform console server only) */
export function draftPlatformSet<T>(ptx: PlatformTx, cs: PlatformChangeSetRef, h: SettingHandle<T>,
  scope: 'platform' | 'region' | 'offering', ref: string, value: T | null, opts?: { bound?: Bound<T>; lock?: boolean; tenantTypes?: TenantType[] }): Promise<ChangeItemRef>;

/** Registry */
export function registry(): readonly SettingDefinitionSummary[];   // generated at build; used by consoles and CI

export class SettingUnknownError extends Error {}
export class SettingValidationError extends Error { readonly issues: z.ZodIssue[] }
export class SettingLockedError extends Error { readonly lockedAt: Scope; readonly managed: boolean }
export class SettingOutOfBoundsError extends Error { readonly bound: unknown; readonly source: Scope | 'entitlement' }
export class SettingNotEntitledError extends Error { readonly entitlement: string }
export class SettingScopeNotAllowedError extends Error {}
export class ConcurrencyConflictError extends Error {}
```

Events (outbox): `config.setting.published` (key, scope, scope ID, value version; values of `sensitive` keys omitted), `config.value.out_of_bounds`, `config.epoch.bumped`.

<!-- section:usage -->
## Usage examples

```ts
// packages/notifications/src/settings.ts
export const quietHours = defineSetting({
  key: 'notify.quiet_hours.start',
  schema: z.object({ start: z.string().regex(/^\d{2}:\d{2}$/), end: z.string().regex(/^\d{2}:\d{2}$/) }).nullable(),
  default: { start: '21:00', end: '08:00' },
  scopes: ['platform', 'region', 'tenant', 'unit', 'user'], lockable: true,
  auditClass: 'standard', permission: 'settings.notifications:write', takesEffect: 'immediate',
  owner: '@nomology/notifications', catalogueNode: 'PKG-settings-notifications',
  label: { en: 'Quiet hours' }, description: { en: 'Do not send non-urgent SMS or WhatsApp during these local hours' },
});

const qh = await settings.get(quietHours);   // user value if allowed, else unit, tenant, region, platform, default
```

```ts
// Console: a tenant admin changes a standard setting in one step
const r = await withTenant((tx) => settings.setOneStep(tx, footerNote, 'tenant', { en: 'Registry closed 25 Dec' }, { reason: 'Holiday notice' }));
if (!r.published) redirect(`/admin/changes/${r.changeSetId}`);   // the key needed review
```

```ts
// Case creation (same transaction as the case row)
await withTenant(async (tx) => {
  const c = await cases.create(tx, input);
  await settings.pinForCase(tx, c.id, chainFor(c));
});
```

```ts
// Errors
try { await withTenant((tx) => settings.setOneStep(tx, maxUpload, 'tenant', 800, {})); }
catch (e) { if (e instanceof SettingOutOfBoundsError) showFieldError(`Maximum ${(e.bound as Range).max} MB on your plan`); else throw e; }
```

<!-- section:tenant -->
## Tenant context

- The scope chain comes from `@nomology/tenant-context` (tenant, home region, offering, membership, primary unit) and from the case when one is in context ([[PKG-configuration-scope-hierarchy#design]]). Reads without a tenant context resolve only platform, region and offering values; reads of keys whose scopes include tenant-side scopes throw `TenantContextMissingError` unless the key also allows platform resolution.
- Storage: platform, region and offering values in platform-level tables; tenant, unit, case and user values in the tenant-owned `config.setting_value` under forced RLS ([[PKG-settings-data-model#tenancy]]); case-type values inside the pinned blueprint version; case pins in `config.case_config_pin`.
- Cache: L1 in process and L2 in the regional cache Redis via [[PKG-caching]], keys `{region}:{tenantId}:{epoch}:…`; a publish bumps the tenant epoch in the same transaction.
- A user who belongs to two tenants has separate user-scope values per membership; nothing personal resolves across tenants.

<!-- section:config -->
## Configuration

The package's own limits: L1 cache 10,000 entries and 30 s per entry; L2 TTL 5 minutes (epoch-bounded); maximum value size 16 KB; maximum 2,000 stored current values per tenant excluding user and case scopes; `resolveAt` and `explain` limited to 60 calls per minute per tenant. Who may write each scope is defined per key in the catalogues and enforced through change sets:

| Scope | Writer | Approval |
|---|---|---|
| Platform, region, offering | `platform_admin` (`regional_ops` for region values of their region), through platform change sets | By audit class; `platform_security` also approves `auth.*` and `access.*` bounds; legal approves regulated values |
| Tenant | Holders of the key's permission (for example `content_admin` for `brand.*`) | By audit class and tenant change-control settings ([[PKG-configuration-lifecycle]]) |
| Unit | `unit_admin` for their subtree, tenant admins | Same as tenant |
| Case type | `workflow_designer`, inside the blueprint version | Blueprint publish review |
| Case | `case_manager` on that case, `caseOverridable` keys only | Reason required; audited on the case timeline |
| User | The user, own preferences | None |

<!-- section:errors -->
## Error model

| Error | Retryable | Caller action |
|---|---|---|
| `SettingValidationError` | No | Show field errors |
| `SettingLockedError` | No | Show "Set by your organisation" or "Managed by Nomology" with the lock source |
| `SettingOutOfBoundsError` | No | Show the allowed range and its source (plan, region, platform) |
| `SettingNotEntitledError` | No | Show the plan badge and upgrade route |
| `SettingScopeNotAllowedError` | No | Programming error; the console only offers allowed scopes |
| `SettingUnknownError` | No | Programming error or retired key; fails CI when caught in tests |
| `ConcurrencyConflictError` | No | Reload and rebase the change set |
| `DbUnavailableError` on read with cache miss | Yes | Consumers of `stricter_only` and security keys fail closed; others may use the last L1 value for up to 60 s and must log that they did |

<!-- section:nfr -->
## Performance and limits

- `get` warm p95 ≤ 2 ms (L1/L2), cold ≤ 15 ms (one query for all tenant-side values of the chain).
- `getMany` resolves up to 100 keys in one round trip.
- A publish is visible to 99% of reads in the region within 5 s.
- `pinForCase` adds ≤ 10 ms to case creation (one insert of about 6 KB).
- `resolveAt` and `explain` ≤ 100 ms p95.

<!-- section:versioning -->
## Versioning and compatibility

Semver for the package API. Each setting's schema is part of the contract: widening (new optional field, larger range, new enum value appended) is a minor change; narrowing requires a migration of stored values first and is checked in CI (`settings:registry-check` compares schema hashes with the previous release). Keys are never reused for a new meaning; renamed keys keep a deprecated alias for one release with `replaced_by`; retired keys stay reserved. Secret-like names (`*secret*`, `*password*`, `*token*`, `*api_key*`) fail the definition lint. The old four-level API (`set(tx, h, level, ...)`) is kept for one release as a shim that creates one-step change sets.

<!-- section:testing -->
## Test contract

- Resolution matrix: for every combination of explicit, unset, locked, managed, out-of-bounds and not-entitled at each of the eight scopes, the effective value, source and explanation are correct (table-driven, generated from the algorithm in [[PKG-configuration-scope-hierarchy]]).
- Write-time checks reject exactly the values that read-time resolution would ignore.
- Pin stability: changing a `case_start` key never changes a pinned case; a case-scope value does.
- Point-in-time: `resolveAt` before and after a scheduled change returns the right values.
- Isolation: tenant A's values never resolve for tenant B; user values never resolve for another user (real Postgres with forced RLS, [[MT-automated-tests-that-prove-one]]).
- Cache: epoch bump invalidates L1 and L2 in a multi-container test; missed pub/sub is bounded by TTL.
- Temporal: snapshots and pins used in workflows are deterministic across replay.

<!-- section:questions -->
## Open questions

- [x] ~~Is the organisation-unit level needed at launch?~~ Yes: the `unit` scope is part of the shared hierarchy; unit pages ship with the tenant admin console.
- [x] ~~Which settings are surfaced to tenant admins?~~ All keys with a tenant-side scope, generated from the registry ([[PKG-settings-catalogue]]).
- [ ] Confirm with the billing owner the split between entitlements (records) and billing settings ([[PKG-settings-billing-and-plans]]). (owner: CCO)
- [ ] Should unit admins see values of sibling units (read-only) for consistency? Proposed: no. (owner: product)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Tenant-side values are in a tenant-owned table with forced RLS; platform values in a platform-level table that app roles can only read. The scope chain takes tenant and region from context, never from arguments; `ChainOverride` can narrow within the tenant (unit, case, membership) and every ID is checked to belong to the tenant. Cache keys include region, tenant and epoch. Users in two tenants have separate values per membership.

<!-- check:security -->
### Security of the API surface

Every key has a Zod schema, bounds and a named permission; writes go through change sets with step-up and review by audit class; `stricter_only` bounds stop lower scopes weakening security settings; locks and managed values cannot be bypassed by any write path (the same check runs at write and read). Secrets cannot be stored (lint and save-time scan).

<!-- check:data-protection -->
### Personal data handling

Only `personal.*` user-scope values are personal data (preferences); they are deleted with the membership and excluded from reporting copies. Other values must not contain personal data and are scanned on save. Telemetry carries key names and sources, never values.

<!-- check:residency -->
### Region awareness

All reads and writes go to the tenant's home-region database and regional Redis; platform values are authored per region. No cross-region calls at resolution time.

<!-- check:audit -->
### Audit events

Every non-preference write is a change item in a change set, audited as `admin.settings.published` with old value, new value, scope, actor, approver and reason in the publishing transaction. Value history (`valid_from`, `valid_to`) answers "which value applied on date X". Preference changes are counted, not individually audited.

<!-- check:observability -->
### Observability

Metrics `config.resolve.duration`, `config.cache.hit_ratio`, `config.invalidation.lag`, refused writes by error type, and drift counts; traces carry the key and source scope as attributes, never values; tenant ID is an event attribute, not a metric label.

<!-- check:resilience -->
### Failure behaviour

Reads fall back from L1 to L2 to the database; security keys fail closed if all fail. Writes are transactional with the epoch bump; invalidation is at-least-once through the outbox. Temporal workflows never call the package from workflow code; they get snapshots or pins in their input.

<!-- check:change-safety -->
### Change and release safety

Definitions live with their owning package; CI fails on schema narrowing without migration, on missing catalogue rows and on unknown permissions. Risky new behaviour that a setting enables is also gated by a release flag at first rollout. The eight-scope API ships with a shim for the old four-level API for one release.

<!-- check:testing -->
### Testing

Table-driven resolution matrix across scopes, locks, bounds, entitlements and pins; write/read consistency tests; isolation tests against real Postgres with RLS; cache invalidation tests with several containers; Temporal determinism tests; all run on every change to `packages/settings` and to any package that defines settings.

<!-- end -->
