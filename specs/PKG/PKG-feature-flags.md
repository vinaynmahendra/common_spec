---
id: "PKG-feature-flags"
title: "Feature flags"
parent: "PKG"
order: 9
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "`@nomology/flags`: release, operational (kill switch), migration and preview flags evaluated per region, tenant cohort, user or percentage without a deploy; engineering release control only, never tenant choices (settings) or commercial availability (entitlements)"
links: []
rev: 3
syncHash: "d2f266d8a34f307c"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.9 Feature flags

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> `@nomology/flags`: release, operational (kill switch), migration and preview flags evaluated per region, tenant cohort, user or percentage without a deploy; engineering release control only, never tenant choices (settings) or commercial availability (entitlements)

<!-- section:purpose -->
## Purpose and scope

`@nomology/flags` turns code paths on and off at run time, per region, tenant cohort, user cohort, persona or percentage, without a deploy. It is used for gradual rollout of new features, kill switches for risky integrations, short-lived data migrations (dual write, new read path) and early-access previews.

It follows the OpenFeature evaluation model (flag key, evaluation context, typed value, reason) [R1] [R2] so the in-house provider can be swapped for a hosted one later. At launch the provider is in-house: flag definitions in Postgres (platform-level, per region), cached in process and invalidated by Redis pub/sub.

**The boundary with settings and entitlements** (binding; see the decision rule in [[PKG-settings-catalogue#design]]):

| Question | Answered by | Owner |
|---|---|---|
| Is this code ready and switched on for this cohort? | Flag | Engineering |
| Has this tenant paid for this capability, and how much? | Entitlement | [[BIL-plans-entitlements-and-usage]] |
| Has this tenant, unit or user chosen to use it, and how? | Setting | [[PKG-settings]] and the catalogues |
| Which deployment endpoints and sizes apply? | Deployment configuration | [[FND-environment-management]] |

Rules:
- **FLAG-R-1** A flag controls only whether code that is being rolled out, protected or migrated runs. A capability is available to a user only if its entitlement is granted, its flag (if any) is on, and the relevant settings allow it ([[BIL-plans-entitlements-and-usage#entitlements]], BIL-ENT-8).
- **FLAG-R-2** Flags never encode commercial availability or a tenant's choice. Targeting by plan or tenant type is therefore not supported; targeting by tenant ID is allowed only for rollout cohorts (pilot tenants, waves).
- **FLAG-R-3** Release, migration and preview flags are temporary: each has an owner and an `expiresOn` at most 90 days ahead; CI warns at expiry and fails 30 days later. Only `operational` flags (kill switches, load shedding) may be long-lived, and they are reviewed every 6 months.
- **FLAG-R-4** When a release flag reaches 100% in every region, the code path is made permanent and the flag removed within one release; if tenants need a choice, a setting is added at that point.
- **FLAG-R-5** Flags are not tenant configuration: they are not in configuration packages ([[PKG-configuration-packages]]), not shown in the tenant admin console, and not changed by tenants. The one exception is `preview` flags, whose availability is shown on the tenant's "Early access" page, where a tenant admin may opt in through a setting (proposed `platform.preview.opt_ins`, [[PKG-settings-platform-operations]]).
- **FLAG-R-6** A standing policy that happens to be on/off per region (for example "destructive retention runs enabled in India") is a region-scope setting, not a flag ([[PKG-settings-data-and-privacy]]).
- **FLAG-R-7** AI (decision D7). Flags express only whether an AI feature is **available** on the platform in a region (`ai.<feature>.available`, a release flag) and the regional **kill switch** `ai.killswitch` (an operational flag). Whether a tenant uses AI, and which features, is a setting: `ai.policy.enabled` and `ai.features.<key>.enabled` in [[PKG-settings-ai]], governed by [[AI-tenant-ai-policy]]. Pilot tenants may be a rollout cohort of an availability flag, but a tenant still sees nothing until its own setting is on. AI settings at `unit`, `case_type` and `case` scope can only narrow the tenant value.

Patterns borrowed: temporary release flags versus long-lived kill switches as distinct flag kinds with different lifecycles (LaunchDarkly release flags [R3] and kill switch flags [R4]).

**Does not:** decide what a tenant is entitled to; hold tenant choices; run experiments with analytics (out of scope at launch).

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Flag (example) | Kind | Also needs |
|---|---|---|---|
| eBundling pipeline | `case.ebundle.new_pagination_engine` | release, % of tenants | — |
| Notifications | `notify.whatsapp.enabled` | release, per region and pilot tenants | Entitlement `feature.notify.whatsapp`; settings in [[PKG-settings-notifications]] |
| AI drafting panel ([[APP-neutral-workspace]]) | `ai.drafting_assist.available` | release, per region (pilot tenants as a rollout cohort) | Entitlement `feature.ai.drafting`; tenant settings `ai.policy.enabled` and `ai.features.drafting_assist.enabled` ([[PKG-settings-ai]]) |
| All AI features ([[AI-ai-gateway]]) | `ai.killswitch` | operational, per region | Operated with `platform.feature_flag.killswitch:update`; tenants cannot override it. The tenant's own off switch is the setting `ai.policy.enabled = false` |
| Video provider integration | `integration.video_provider_x.kill_switch` | operational | — |
| Data migration | `case.documents.read_from_v2_table` | migration, per tenant | — |
| Frontend route groups | `platform.ui.secretariat_new_queue_view` | preview | Tenant opt-in setting `platform.preview.opt_ins` |
| Configuration backbone | `config.case_pins.enabled`, `config.change_sets.enabled` | release | — |

Old keys (`ebundle.newPaginationEngine`, `ai.awardDraftAssist`, and the former tenant-enablement flags `ai.enabled` and `ai.feature.<name>`, which become settings under FLAG-R-7) are renamed to the domain grammar when the flags are next touched; keys are code constants, so the rename is a code change with no data migration beyond the rule rows.

<!-- section:api -->
## Public API

```ts
// packages/flags/src/index.ts (server); client components receive evaluated values via props, never the SDK
export type FlagKind = 'release' | 'operational' | 'migration' | 'preview';

export interface FlagDef<T extends boolean | string | number> {
  key: string;                     // '<domain>.<area>.<name>' using the same domains as settings, e.g. 'notify.whatsapp.enabled'
  kind: FlagKind; type: 'boolean' | 'string' | 'number';
  default: T;                      // value when no rule matches or the provider fails (must be the safe value)
  owner: string;
  expiresOn?: string;              // required for release, migration and preview (≤ 90 days ahead); CI warns, then fails after 30 days
  reviewBy?: string;               // required for operational flags (≤ 6 months)
  requiresEntitlement?: `feature.${string}`;   // documentation and a runtime assertion: flag is only evaluated where the entitlement is granted
  description: string;
}
export function defineFlag<T extends boolean | string | number>(def: FlagDef<T>): FlagHandle<T>;

export interface EvalContext {          // built from @nomology/tenant-context; callers may add attributes
  region: 'in' | 'sg' | 'us' | 'in-az' | 'sg-az' | 'us-az';
  tenantId?: string; userId?: string; persona?: string; appVersion: string;
}
export interface Evaluation<T> { value: T; reason: 'STATIC' | 'TARGETING_MATCH' | 'SPLIT' | 'DEFAULT' | 'ERROR'; ruleId?: string; flagVersion: number }

export function isEnabled(h: FlagHandle<boolean>, extra?: Partial<EvalContext>): boolean;     // synchronous, in-memory
export function getValue<T>(h: FlagHandle<T>, extra?: Partial<EvalContext>): Evaluation<T>;
export function snapshotForWorkflow(handles: FlagHandle<any>[]): FlagSnapshot;               // pass into Temporal workflow input

/** Capability check combining the three sources (FLAG-R-1); lives in @nomology/capabilities, re-exported here */
export function isAvailable(cap: { flag?: FlagHandle<boolean>; entitlement?: string; setting?: SettingHandle<boolean> }): Promise<boolean>;

// Admin (platform admin console only)
export function upsertRules(tx: PlatformTx, key: string, rules: FlagRule[], opts: { reason: string; expectedVersion: number; changeRecord?: string }): Promise<void>;
export function killSwitch(tx: PlatformTx, key: string, opts: { reason: string; incidentRef?: string }): Promise<void>;   // operational flags only
export interface FlagRule {
  id: string;
  match: { regions?: string[]; tenantIds?: string[]; userIds?: string[]; personas?: string[] };   // no plan or tenant-type targeting (FLAG-R-2)
  serve: { value: unknown } | { split: { percent: number; value: unknown; by: 'tenantId' | 'userId' }[] };
}
```

Bucketing for percentage rollouts uses a stable hash `murmur3(flagKey + ':' + tenantId|userId) % 10000`, so the same tenant stays in the same bucket as the percentage grows.

Admin surface: `/platform/flags` (list with kind, owner, expiry, per-region state) and `/platform/flags/[key]` (rules per region, history, evaluation counts), API `/platform/v1/flags/...`. Permissions: `platform.feature_flag:update` (`platform_admin`, engineering owners through JIT, [[PKG-jit-and-break-glass]]), `platform.feature_flag.killswitch:update` (on-call `platform_admin` and `platform_support` tier 2).

<!-- section:usage -->
## Usage examples

```ts
export const whatsapp = defineFlag({ key: 'notify.whatsapp.enabled', kind: 'release', type: 'boolean',
  default: false, owner: 'notifications', expiresOn: '2027-01-31', description: 'Enable WhatsApp channel' });

if (flags.isEnabled(whatsapp)) channels.push('whatsapp');
```

```ts
// Temporal: evaluate once at start, pass in — never call flags from workflow code
const fs = flags.snapshotForWorkflow([newPagination]);
await temporal.workflow.start(buildBundle, { args: [{ bundleId, flags: fs }], taskQueue: 'documents', ... });
```

<!-- section:tenant -->
## Tenant context

Flag definitions and rules are platform-level data per region (`flags.flag_definition`, `flags.flag_rule`, `flags.flag_rule_history`; no tenant_id), because they describe code, not tenant data. Evaluation uses the tenant from context; rules can target tenant IDs for rollout cohorts only, and a tenant can never see or change flags (except the early-access list of `preview` flags, which shows names and descriptions, not rules). Without a tenant context (platform jobs), only region-level rules apply. Flag values are not personal data; evaluation never sends context outside the process.

<!-- section:config -->
## Configuration

| Setting | Default | Where |
|---|---|---|
| Refresh | Pub/sub invalidation; full reload every 30 s as safety net | Code |
| Max rules per flag | 50 | Code |
| Stale flag check | Release, migration and preview flags past `expiresOn`: CI warning, error after 30 days; operational flags past `reviewBy`: warning | CI |
| Change approval in production | Release, migration and preview flags: owner plus one reviewer (maker-checker), linked to the release change record ([[DEP-release-notes-and-change]]); operational kill switch: any on-call holder of `platform.feature_flag.killswitch:update`, alone, audited, with on-call channel notification | Platform console |
| Region order | Rollouts follow the release wave order of [[DEP-environment-promotion-and-multi]] unless the change record says otherwise | Process |

<!-- section:adapters -->
## Providers and extension points

Provider interface compatible with OpenFeature's provider contract (`resolveBooleanEvaluation` and the other typed resolvers returning value, reason and variant) [R1], so a hosted provider can be adopted if it offers in-region data handling. Shipped provider: `PostgresProvider` per region. Test provider: `StaticProvider` with in-memory rules. Evaluation context follows the OpenFeature context model with a targeting key of tenant or user ID [R2].

<!-- section:errors -->
## Error model

Evaluation never throws: on any provider failure the safe `default` is returned with reason `ERROR` and a counter increments. Admin writes throw `ConcurrencyConflictError` on version mismatch and `ValidationError` for malformed rules.

<!-- section:nfr -->
## Performance and limits

Evaluation is in-memory: p99 ≤ 0.1 ms. Rule changes reach all containers in a region within 5 s. Definition load at start-up ≤ 200 ms.

<!-- section:versioning -->
## Versioning and compatibility

Semver for the API. Flags themselves are versioned (`flagVersion` increments on every rule change) and the version is attached to traces for debugging.

<!-- section:testing -->
## Test contract

Unit tests for matching and stable bucketing (distribution within ±1% at 10,000 tenants); failure test (provider down → default); CI lint for expired and unreviewed flags; lint that rejects `plan` or `tenantType` in rule match objects; tests that client bundles never import the server SDK; contract test that `isAvailable` returns false when any of entitlement, flag or setting denies.

<!-- section:questions -->
## Open questions

- [ ] In-house provider versus a self-hosted open-source flag service per region? Proposed: in-house until experiments are needed.
- [x] ~~Should tenant admins see "preview" features they can opt into?~~ Yes: `preview` flags with a tenant opt-in setting (FLAG-R-5).
- [ ] Should flag changes in production for regulated tenants (SEBI ODR, court programmes) require notifying the tenant in advance? Proposed: release notes cover it; pilot cohorts are agreed with the tenant. (owner: product)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Flags are platform-level definitions that read tenant ID only as an evaluation attribute; they hold no tenant data and expose nothing to tenants beyond the early-access list. Percentage bucketing is per tenant by default, so a tenant does not see a mix of old and new behaviour across its users unless the rule says `by: 'userId'`.

<!-- check:security -->
### Security of the API surface

Only platform principals can change rules; release changes need maker-checker in production; kill switches are limited to on-call roles. Because flags cannot target plans or tenant types, they cannot be used to grant paid capabilities or bypass a tenant's settings.

<!-- check:residency -->
### Region awareness

Definitions are stored and evaluated per region; a flag can be on in Singapore and off in India. No evaluation data leaves the region.

<!-- check:audit -->
### Audit events

Every rule change is a platform audit event `admin.flag.updated` (actor, flag, region, old and new rules, reason, change record); kill-switch use emits `admin.flag.killswitch_used` and notifies the on-call channel; history is kept in `flags.flag_rule_history`.

<!-- check:resilience -->
### Failure behaviour

Evaluation is synchronous in memory with safe defaults on any failure. Temporal workflows receive a snapshot at start so replay is deterministic.

<!-- check:change-safety -->
### Change and release safety

This package is the change-safety tool for other packages: risky behaviour ships behind a flag, enabled per region and cohort, and can be turned off in seconds without a deploy. Flags have owners and expiry dates enforced by CI, and release flags are removed once at 100%, so flags do not turn into hidden configuration.

<!-- check:testing -->
### Testing

Bucketing, failure-default, expiry lint, targeting lint and capability-combination tests run on every change to `packages/flags`; each flag's both paths are covered by the owning package's tests until the flag is removed.

<!-- citations -->
## Citations

```json
[
  {
    "body": "OpenFeature (CNCF)",
    "id": "R1",
    "ident": "OpenFeature specification, section 1",
    "kind": "standard",
    "title": "OpenFeature specification: Flag evaluation API",
    "url": "https://openfeature.dev/specification/sections/flag-evaluation"
  },
  {
    "body": "OpenFeature (CNCF)",
    "id": "R2",
    "ident": "OpenFeature specification, section 3",
    "kind": "standard",
    "title": "OpenFeature specification: Evaluation context",
    "url": "https://openfeature.dev/specification/sections/evaluation-context"
  },
  {
    "id": "R3",
    "kind": "vendor",
    "title": "LaunchDarkly docs: Release flags",
    "url": "https://launchdarkly.com/docs/home/flags/release",
    "vendor": "LaunchDarkly"
  },
  {
    "id": "R4",
    "kind": "vendor",
    "title": "LaunchDarkly docs: Kill switch flags",
    "url": "https://launchdarkly.com/docs/home/flags/killswitch",
    "vendor": "LaunchDarkly"
  }
]
```

<!-- end -->
