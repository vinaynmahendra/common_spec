---
id: "PKG-configuration-scope-hierarchy"
title: "Configuration scope hierarchy and inheritance"
parent: "PKG-configuration-and-customisation"
order: 9
type: "feature"
template: "design"
status: "draft"
owner: null
indicative: false
summary: "The eight configuration scopes (platform, region, offering, tenant, unit, case type, case, user) and the single resolution algorithm for every setting: inheritance, locks, hard bounds, plan entitlements, case pinning, point-in-time resolution, caching and invalidation"
links: []
rev: 1
syncHash: "a283b2c1bf7d91d0"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.8.9 Configuration scope hierarchy and inheritance

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> The eight configuration scopes (platform, region, offering, tenant, unit, case type, case, user) and the single resolution algorithm for every setting: inheritance, locks, hard bounds, plan entitlements, case pinning, point-in-time resolution, caching and invalidation

<!-- section:context -->
## Context and scope

The platform is configured at many levels. Nomology sets platform defaults and hard limits; a region adds local legal defaults (for example DPDP notice text in India); CORD and TERES differ as product lines; each tenant institution sets its own policies; parts of a tenant (an office, a SEBI ODR desk, a court programme) need local variations; a case-type blueprint fixes procedural values; a tribunal order can change one case; and every person has preferences.

What exists today:
- [[PKG-settings]] (`@nomology/settings`) resolves key-value settings over four levels (platform default, platform override, tenant, org unit, user) with locks and bounds.
- [[PKG-configuration-and-customisation]] (`@nomology/config-core`) versions larger artefacts (forms, case-type blueprints, templates, decision tables) and pins them to cases.
- [[BIL-plans-entitlements-and-usage]] (`@nomology/entitlements`) decides what a tenant has bought; [[PKG-feature-flags]] decides what code is rolled out; [[FND-environment-management]] carries deployment configuration.

Each of these had its own idea of "level". This note replaces them with one hierarchy and one resolution algorithm, used by every settings catalogue ([[PKG-settings-catalogue]]) and implemented once in `@nomology/settings`. It is the binding reference for the scope list in the shared model; the storage is in [[PKG-settings-data-model]] and the change process in [[PKG-configuration-lifecycle]].

<!-- section:goals -->
## Goals and non-goals

**Goals**
- One ordered list of scopes and one resolution algorithm for every setting in every domain, with no per-feature exceptions.
- For any setting, user, case and moment in time, the platform can say which value applied, where it came from, and why lower values were ignored (lock, bound, entitlement, pin).
- Procedural fairness: a value that affects a party's rights (deadlines, rules applied, service language) does not change under a running case unless the setting is declared "applies to running cases" or a recorded case-level decision changes it.
- Hot-path reads stay cheap: p95 ≤ 2 ms warm, ≤ 15 ms cold, and a change is visible everywhere in the region within 5 seconds.
- Higher scopes can protect lower ones: platform and region hard bounds, tenant locks, and plan entitlements cannot be bypassed by any API, console, bulk tool, package import or the admin copilot.

**Non-goals**
- Deployment configuration and secrets ([[FND-environment-management]], [[INF-secrets-and-keys]]) and release flags ([[PKG-feature-flags]]) are not settings and do not use this hierarchy.
- Access decisions are not settings. Settings may parameterise policy (for example "secretariat may see scrutiny comments"), but who holds which role is in [[PKG-roles-and-permission-sets]] and [[PKG-rbac-abac-case-level-party]].
- No free-form expression language for conditional values. Conditions belong in decision tables ([[PKG-rules-and-decision-engine]]) and automation rules ([[WF-automation-rules]]).
- No per-party scope. Parties and counsel get `user` preferences only; case-wide values are set by the case manager.

<!-- section:design -->
## Design

### 1. The scopes

| Order | Scope key | Identified by | Value stored in | Administered by (role key) | Admin surface |
|---|---|---|---|---|---|
| 1 | `platform` | constant | `config.platform_setting_value` (platform-level) | `platform_owner`, `platform_admin` | `/platform/settings` |
| 2 | `region` | `in`, `sg`, `us` (and Azure variants such as `in-az`) | same table, `scope_ref = <region>` | `platform_admin`, `regional_ops` | `/platform/settings?scope=region` |
| 3 | `offering` | `cord`, `teres` | same table, `scope_ref = <offering>` | `platform_admin` | `/platform/settings?scope=offering` |
| 4 | `tenant` | `tenant.id` | `config.setting_value` (tenant-owned, forced RLS) | `tenant_owner`, `tenant_admin` and domain admins (`security_admin`, `content_admin`, `billing_admin`, `ai_admin`, `integration_admin`, `workflow_designer`) | `/admin/settings/...` |
| 5 | `unit` | `org_unit.id` (units nest up to 5 deep, [[MT-tenancy-and-identity-schema]]) | `config.setting_value`, `scope_type = 'unit'` | `unit_admin` for their unit and descendants, tenant admins | `/admin/organisation/units/[unitId]/settings` |
| 6 | `case_type` | blueprint key + version ([[WF-process-definition-model]]) | inside the published blueprint version (`settings` block), not in `setting_value` | `workflow_designer` | `/admin/workflows/[caseTypeKey]` (authoring studio, [[WF-workflow-authoring-studio]]) |
| 7 | `case` | `case.id` | `config.setting_value`, `scope_type = 'case'`, plus the case pin `config.case_config_pin` (its `settings` column) | `secretariat` holding the case-level role `case_manager` | Case settings panel in [[APP-secretariat-console]] |
| 8 | `user` | membership id (per tenant) | `config.setting_value`, `scope_type = 'user'` | the user themself | Personal settings ([[PKG-personalisation]], [[PKG-settings-personal]]) |

The shared model's names are binding. `org_unit` in older nodes is the `unit` scope.

### 2. Building the scope chain

Every resolution starts from a **scope chain** built from the active context ([[MT-tenant-resolution]], `@nomology/tenant-context`):

```ts
interface ScopeChain {
  region: 'in' | 'sg' | 'us' | 'in-az' | 'sg-az' | 'us-az';   // always the tenant's home region
  offering: 'cord' | 'teres';
  tenantId?: string;
  tenantType?: TenantType;          // arbitral_institution | odr_institution | cord | enterprise | court_programme | sandbox
  unitPath: string[];               // leaf first, root last; [] when none
  caseType?: { key: string; version: number };
  caseId?: string;
  membershipId?: string;            // user scope
  at?: Date;                        // point-in-time resolution; default now
}
```

- **SCOPE-FR-1** The region is always the tenant's home region from the tenant directory, never a request header.
- **SCOPE-FR-2** The offering in a case context is the offering of the case type; outside a case it is the tenant's primary offering (`tenant.primary_offering`). A tenant licensed for both CORD and TERES therefore gets CORD values on CORD case types.
- **SCOPE-FR-3** The unit path in a case context is the case's owning unit (`case.unit_id`) and its ancestors; outside a case it is the membership's primary unit. A user in several units resolves against the primary unit unless the screen is unit-specific.
- **SCOPE-FR-4** Background work (BullMQ jobs, Temporal activities) rebuilds the chain from IDs in the job payload; it never inherits a chain from another tenant's job.

### 3. What a setting definition declares

Each key is declared once in code with `defineSetting` (API in [[PKG-settings#api]]). The fields that drive resolution:

| Field | Meaning |
|---|---|
| `scopes` | Ordered subset of the eight scopes where a value may be set. Anything else is rejected at write time. |
| `lockable` | Whether a scope may lock the value for all narrower scopes. |
| `bounds` | Hard bounds per type: `range {min,max}`, `enum_subset`, `subset_of` (value must be a subset of an allowed set), `pattern`, `direction: 'stricter_only'` (lower scopes may only make it stricter, for example MFA required). |
| `entitlement` | A feature key (`feature.*`) that must be granted for tenant-and-below values to count, or a limit key (`limit.*`) that acts as a ceiling. |
| `pinning` | `case_start` (resolved when the case starts and frozen on the case), `live` (always current), or `event` (resolved when an event happens and recorded with that event, for example the notice language at the moment of service). |
| `caseOverridable` | Whether a case manager may set a case-scope value (only meaningful with `case` in `scopes`). |
| `migratable` | Whether running cases may be moved to a new value by a reviewed bulk migration. |
| `onOutOfBounds` | `clamp` (numeric ranges) or `fallback` (use the next broader valid value). |
| `auditClass` | `standard`, `sensitive` or `maker_checker` ([[PKG-configuration-lifecycle]]). |

### 4. The resolution algorithm

`resolve(key, chain)` returns the effective value and an explanation. Steps, in order:

1. **Definition.** Load the definition version valid at `chain.at`. Unknown or retired key: error `SettingUnknownError`.
2. **Candidates.** Collect explicit values for the key at every scope in the chain that the definition allows, valid at `chain.at` (`valid_from <= at < valid_to`). Case-type values come from the pinned blueprint version.
3. **Bounds.** Compute the effective bound as the intersection of the code bound, the `platform` bound, the `region` bound, the `offering` bound and any tenant **constraint** (a tenant may tighten bounds for its units and users, never loosen them). Bounds only tighten going down the chain.
4. **Entitlement.** If `entitlement` is a feature key the tenant does not hold at `chain.at` (from the entitlement snapshot, [[BIL-plans-entitlements-and-usage#entitlements]]), drop all candidates at `tenant` and narrower. If it is a limit key, intersect the bound with `max = limit`.
5. **Locks.** Find the broadest scope in the chain that locks the key. Drop all candidates narrower than that scope. A lock set by Nomology on a tenant row (`managed = true`) cannot be removed by tenant roles and is shown as "Managed by Nomology".
6. **Case pin.** If a case is in the chain and the key is `pinning = 'case_start'`, use the value recorded in the case pin unless there is a case-scope value set after the pin. If there is no pin yet (case not started), continue.
7. **Pick.** The narrowest remaining candidate wins. If none, the code default applies.
8. **Validate against bounds.** If the picked value violates the effective bound (because a bound was tightened after the value was saved), apply `onOutOfBounds` and mark the result `drift = true`.
9. **Return** `{ value, source: { scope, ref }, locked, lockedAt?, managed, bound, entitlementDecision, pinned, drift, valueVersion }`.

```text
platform ─┬─ bound ∩ ─ region ─ bound ∩ ─ offering ─ bound ∩ ─ tenant ─ constraint ∩ ─ unit … ─ case_type ─ case ─ user
          │             lock? ────────────────────────▶ drops everything narrower
          └─ entitlement gate applies from tenant downwards
narrowest surviving explicit value wins → validated against the intersected bound
```

- **SCOPE-FR-5** Every consumer reads settings only through `@nomology/settings` (`get`, `getMany`, `resolve`, `resolveAt`, `snapshot`). Direct reads of `config.*` tables outside the package fail an ESLint rule and a database grant check (only the settings role can select from them).
- **SCOPE-FR-6** Writes are checked against the same algorithm: a value that would be ignored (narrower than a lock, outside a bound, not entitled) is refused with `SettingLockedError`, `SettingOutOfBoundsError` or `SettingNotEntitledError`, never stored silently.
- **SCOPE-FR-7** When a scope locks a key, existing narrower values are **cleared** in the same change set and listed in its diff, with the count shown to the approver ("This lock removes 3 unit values and 41 user values"). Rolling back the change set restores them. No narrower value is ever silently shadowed.
- **SCOPE-FR-8** When a bound is tightened at `platform` or `region`, a BullMQ job `config-drift-scan` lists every stored value now out of bounds, notifies the owning tenant admins, and opens an admin task. Effective values follow `onOutOfBounds` until the tenant fixes them.
- **SCOPE-FR-9** When a tenant loses an entitlement (downgrade, expired trial), its values for gated keys are kept but **dormant**; the effective value falls back to the offering or platform value. The plan-change notice lists the dormant values, and they become active again if the entitlement returns.

### 5. Platform-managed values and tenant-type targeting

Some values must hold for a class of tenant without being a platform-wide default: for example SEBI ODR institutions must not shorten regulator-defined timelines, and must show the investor charter. Two mechanisms, both owned by Nomology:

- **Targeted platform values.** A `platform`, `region` or `offering` value may carry a selector `tenant_type in (...)`. Example: `data.retention.case_record_years` at `region = in` with selector `odr_institution`. Only `tenant_type` may be used as a selector; no other conditions.
- **Managed tenant values.** A blueprint ([[PKG-configuration-packages]]) may write tenant-scope values with `managed = true` and a lock. Tenant roles cannot change or unlock them; `platform_admin` can, through a maker-checker change set, with a reason that the tenant sees.

### 6. Case scope and pinning

- **SCOPE-FR-10** At case creation, the case service calls `settings.pinForCase(caseId, chain)`, which resolves every key with `pinning = 'case_start'` that the case type declares relevant and writes one immutable row to `config.case_config_pin` (its `settings` column) (key, value, source, value version). The pin is created in the same transaction as the case.
- **SCOPE-FR-11** A case-scope value may be set only for `caseOverridable` keys, only by a principal holding `case:configure` on that case (the `case_manager` case role), with a reason and, where it follows a tribunal decision, a reference to the procedural order document. It appears on the case timeline ([[PKG-case-timeline]]) and in the case audit log.
- **SCOPE-FR-12** Changing a `case_start` setting at a broader scope never changes running cases. To move running cases, a tenant runs a reviewed bulk migration (maker-checker) through [[WF-workflow-versioning]]; only `migratable` keys are eligible, and each moved case gets a timeline entry.
- Temporal workflows never call the package from workflow code: the pin (or a `snapshot`) is passed in workflow input and re-read through an Activity only on explicit migration ([[WF-separation-of-concerns-temporal]]).

### 7. Point-in-time resolution and explanation

- **SCOPE-FR-13** `resolveAt(key, chain, at)` returns the value that applied at time `at`, using value history (`valid_from`, `valid_to`), definition history, entitlement snapshots and case pins. It reads from the primary database and bypasses caches.
- **SCOPE-FR-14** `explain(key, chain, at?)` returns every candidate with its scope, whether it was used, and why not (locked above, out of bounds, not entitled, pinned, superseded). It powers the **effective configuration explorer** at `/admin/config/effective` and `/platform/tenants/[tenantId]/config/effective`, the admin copilot ([[APP-admin-copilot]]) and support investigations. It follows the same pattern as the access explainer ([[PKG-access-explainer]]).

### 8. Caching and invalidation

| Layer | Key | Contents | Invalidation |
|---|---|---|---|
| L1 in-process LRU (10,000 entries per container) | `{region}:{tenantId}:{epoch}:{key}:{chainHash}` | Resolved value + explanation summary | Epoch change |
| L2 regional cache Redis ([[INF-redis]], namespace `settings` via [[PKG-caching]]) | `cfg:{region}:{tenantId}:{epoch}:{unitPathHash}` | All tenant-and-unit values for the chain (one hash) | Epoch change; TTL 5 min backstop |
| Global epoch | `cfg:epoch:{region}:global` | Bumped on any `platform`, `region` or `offering` change and on definition sync | Pub/sub `cfg:invalidate:{region}` |
| Tenant epoch | `config.tenant_config_epoch` row, mirrored to `cfg:epoch:{region}:{tenantId}` | Bumped in the publishing transaction (outbox) | Pub/sub `cfg:invalidate:{region}` |

- **SCOPE-FR-15** A publish bumps the tenant epoch in the same transaction as the values; the outbox relay publishes the invalidation. Containers that miss the message pick up the change when L1 entries expire (30 s) or L2 TTL expires (5 min). Target: 99% of reads in the region return the new value within 5 s of commit.
- **SCOPE-FR-16** Scheduled changes (`effective_from` in the future) are stored with `valid_from` set to that time, so resolution is correct even before caches are told. A BullMQ delayed job on queue `config-activate` bumps the epoch at `effective_from`.
- User-scope values are cached per membership for 5 minutes and invalidated by a membership epoch.
- Point-in-time reads, `explain` and preview overlays never use or fill the caches.

### 9. Preview overlays

A draft change set can be laid over the chain for preview: `resolve(key, chain, { overlay: changeSetId })` applies the draft's items as if published, without writing or caching. Used by the preview panes described in [[PKG-configuration-lifecycle]].

<!-- section:examples -->
## Worked examples

**Example 1: upload limit with bound, entitlement and unit value** (`case.filing.max_upload_mb`, owned by [[PKG-settings-cases-and-workflows]]; used here only to show resolution)

| Scope | Stored | Note |
|---|---|---|
| code | default 200, bound 1–2048 | |
| platform | — | |
| region `in` | bound max 1024 | Regional bandwidth policy |
| tenant (on `inst.standard`, `limit.upload_mb = 500`) | 500 | |
| unit "Mumbai office" | 300 | |

A filing in a Mumbai-office case resolves to 300 (unit, narrowest). The tenant admin tries to set 800: refused with `SettingOutOfBoundsError` ("Your plan allows up to 500 MB"). Later the region bound drops to 250: `config-drift-scan` flags the tenant value (500) and the unit value (300); both clamp to 250 with `drift = true` until an admin fixes them.

**Example 2: region lock** (`data.notice.dpdp_notice_required`, [[PKG-settings-data-and-privacy]])

Region `in` sets `true` and locks it. An India tenant's admin page shows the toggle disabled with "Required in the India region (locked by Nomology)". A write attempt returns `SettingLockedError { lockedAt: 'region' }`.

**Example 3: managed tenant value from a blueprint**

The SEBI ODR institution blueprint needs a retention minimum the tenant may raise but never lower. It writes a tenant **constraint** `min 8` on `data.retention.case_record_years` (8 years is an assumption pending legal) with `managed = true`, and leaves the value itself unlocked. The tenant admin can set 10; an attempt to set 6 returns `SettingOutOfBoundsError` ("Minimum 8 years, managed by Nomology for SEBI ODR institutions"). For a value that must not change at all (for example showing the investor charter link), the blueprint instead writes a managed, locked value. Which pattern applies is chosen per key in the blueprint and is visible in its diff.

**Example 4: case pin and tribunal order**

Case 2026/ARB/0142 starts on 2 March under blueprint "Institutional arbitration (expedited) v3"; its pin records `case.response.default_days = 14` (case-type value). On 10 March the workflow designer publishes v4 with 21 days: case 0142 still resolves 14. On 20 March the tribunal extends the response time; the case manager sets a case-scope value 28 with reason "Procedural Order No. 2" and a link to the order document. `resolveAt(..., at = 15 March)` returns 14; `resolveAt(..., at = 21 March)` returns 28.

**Example 5: user preference within a tenant bound**

Tenant enables locales `en-IN` and `hi-IN` (`locale.enabled_locales`, a `subset_of` bound for `personal.locale`). A party sets `personal.locale = ta-IN`: refused, because the tenant has not enabled Tamil; the party sees the list of available languages.

**Example 6: explanation output**

```json
{
  "key": "brand.footer.show_unit_name",
  "value": false,
  "source": { "scope": "tenant", "ref": "t_01J..." },
  "candidates": [
    { "scope": "platform", "value": true, "used": false, "why": "superseded" },
    { "scope": "tenant", "value": false, "used": true, "lock": true },
    { "scope": "unit", "ref": "u_01J...", "value": true, "used": false, "why": "cleared_by_lock", "clearedIn": "cs_01J..." }
  ],
  "entitlement": null,
  "pinned": false, "drift": false, "valueVersion": 7
}
```

<!-- section:alternatives -->
## Alternatives considered

| Option | Why not chosen |
|---|---|
| Flat tenant settings plus user preferences (the previous four-level model) | No place for regional legal defaults, product-line differences, units, case-type values or case pins; each feature invented its own workaround. |
| Copy all defaults into each tenant at provisioning | Tenants then miss every later platform improvement and fix; "default" becomes meaningless. We store only explicit values and inherit the rest. Blueprints write explicit values only where the tenant type genuinely differs. |
| Per-feature configuration tables | Inconsistent locking, audit and history; no single "why does this value apply" answer; every catalogue would need its own change process. |
| Policy language (for example Rego) for conditional values | Powerful but opaque to tenant admins and hard to explain; conditions belong in decision tables and automation rules, which have their own authoring and testing. |
| Hosted configuration service (for example a cloud provider's app configuration product) | Good for deployment configuration (see [[FND-environment-management]]), but it has no notion of tenant, unit, case pin, entitlement or locks, and would put tenant configuration outside the regional database and RLS. |
| Most specific always wins, no locks | Cannot express "this institution requires MFA for all staff" or "India requires this notice"; locks are needed. |

Patterns borrowed (described in our own terms above):
- Hierarchical settings resolved organisation → profile → user, with the most specific value winning: pattern borrowed from hierarchy custom settings in Salesforce [R1].
- Values that a subscriber cannot change once a package installs them: borrowed from protected custom metadata in Salesforce [R2], here the "managed tenant value".
- Named, typed system properties with descriptions and read/write roles: borrowed from ServiceNow system properties [R3].
- A definition shipped once with a separate value per environment: borrowed from environment variables in Power Platform solutions [R4], here a definition in code with values per scope.
- Tenant-wide configuration with business-unit specific overrides: a common pattern in Workday tenant configuration and Dynamics 365 business units (no citation; general practice).

<!-- section:crosscutting -->
## Cross-cutting concerns

| Concern | How this design addresses it |
|---|---|
| Security | Bounds and locks are enforced at write and at read, so a bad stored value cannot take effect. `direction: 'stricter_only'` keys (MFA, session length, allowed file types) cannot be weakened below the broader scope. Writes require the domain permission ([[PKG-settings-catalogue]] conventions) and, for `sensitive` and `maker_checker` keys, step-up authentication and review ([[PKG-configuration-lifecycle]]). The copilot and AI agents can only propose drafts ([[APP-admin-copilot]]). |
| Privacy | Setting values must not contain personal data; definitions with free-text values are scanned on save for emails, phone numbers and ID numbers and refused ([[PKG-settings-data-model#protection]]). User-scope values (preferences) are personal data of low sensitivity, deleted with the membership ([[PKG-retention-and-deletion-schedule]]). |
| Tenancy | Tenant, unit, case and user values are tenant-owned rows under forced RLS ([[MT-rls-enabled-and-forced-on]]); platform, region and offering values are platform-level rows that no tenant role can write. Cache keys always include region, tenant and epoch. Targeted platform values select on tenant type only, never on tenant ID, so tenant-specific values always live in the tenant's own rows. |
| Residency | All values live in the regional database of the tenant's home region; platform, region and offering values are replicated to each region by the definition sync, not read across regions. |
| Observability | Metrics `config.resolve.duration` (histogram, s, labels `cache_layer`, `outcome`), `config.cache.hit_ratio`, `config.invalidation.lag` (histogram, s), `config.drift.values` (gauge per region). Events `config.value.out_of_bounds`, `config.lock.cleared_values`. No tenant ID as a metric label (it is an event attribute), per [[OBS-foundations]]. |
| Cost | One query resolves all tenant-and-unit values for a chain; L1 and L2 caches serve almost all reads. Point-in-time and explain reads are rare admin operations. |

<!-- section:guardrails -->
## Guardrails

- **SCOPE-G-1** Never read a setting from a table, environment variable or constant when a definition exists; always call `@nomology/settings`.
- **SCOPE-G-2** Never add a scope, or a selector other than `tenant_type`, without changing this node and the shared model.
- **SCOPE-G-3** A setting that changes what a party must do, by when, or under which rules is `pinning = 'case_start'` unless the owning catalogue states why it is `live`, and the reason is reviewed by legal for SEBI ODR and court tenants.
- **SCOPE-G-4** Locks clear narrower values in the same change set (SCOPE-FR-7); no code path may shadow values silently.
- **SCOPE-G-5** Entitlement gating is declared on the definition, not checked ad hoc in feature code.
- **SCOPE-G-6** Workflow code receives pins or snapshots as input; it never calls the settings package.
- **SCOPE-G-7** No secrets, credentials, tokens or personal data in setting values (lint plus save-time scan).
- **SCOPE-G-8** Resolution results used for a legally significant act (service of a notice, a deadline, a fee) are recorded with the act, with the value version, so the act can be explained later without re-resolving.

<!-- section:ownership -->
## Ownership

| Part | Owner | Change process |
|---|---|---|
| Scope list, resolution order, selectors | Platform architecture (CTO) | Change to this node and the shared model; ADR if a scope is added or removed |
| `@nomology/settings` resolver, caches | Platform engineering (configuration team) | PR with resolution matrix tests |
| Definitions per domain | Owning package, listed in each domain catalogue ([[PKG-settings-catalogue]]) | PR; catalogue regenerated in CI |
| Platform, region and offering values | `platform_admin`; `regional_ops` for region values | Platform change set with maker-checker for `sensitive` and `maker_checker` keys |
| Targeted and managed values for regulated tenant types | Product with legal sign-off | Platform change set, maker-checker, legal named as approver |

<!-- section:questions -->
## Open questions

- [ ] Is one primary offering per tenant enough, or do some tenants need the unit to choose the offering (for example a CORD programme run inside a TERES institution)? (owner: product)
- [ ] Confirm which keys need tenant-type targeting at launch; proposed list: retention minimums, SEBI ODR timeline bounds, investor charter display, DPDP notice requirements. (owner: legal)
- [ ] Should a unit admin be able to lock values for their sub-units, or only tenant admins? Proposed: unit admins may lock within their own subtree. (owner: product, authz group)
- [ ] Should `explain` be available to `auditor` for case-scope values on cases they cannot otherwise open? Proposed: no; explanation follows case access. (owner: security lead)
- [ ] Assumption: units nest at most 5 deep ([[MT-tenancy-and-identity-schema]]); resolution cost grows with depth, so deeper trees need a new design. (owner: platform engineering)

<!-- checks -->
## Template checks

<!-- check:security -->
### Security and privacy

New attack surface: the write API for values at five tenant-side scopes, the explain endpoint, and preview overlays. Threats and controls: (1) privilege escalation by writing a narrower value that defeats a security policy: blocked by locks, `stricter_only` bounds and write-time resolution (SCOPE-FR-6); (2) a tenant writing platform-scope values: platform rows are in a platform-level table with no tenant grant; (3) information leakage through `explain` (revealing another unit's or case's values): `explain` requires read permission on every scope it reveals, and case-scope candidates follow case access; (4) stored values that become dangerous when bounds change: drift scan and clamp or fallback (SCOPE-FR-8); (5) AI-proposed changes: drafts only, normal review. Personal data: only user-scope preferences (locale, time zone, density), which are low-sensitivity personal data deleted with the membership.

<!-- check:tenancy -->
### Tenancy

Tenant identity comes from `@nomology/tenant-context` and is set per transaction by the Prisma extension ([[MT-prisma-client-extension-wraps]]); all tenant, unit, case and user values are in tenant-owned tables with forced RLS. The chain builder takes the region from the tenant directory, not the request. Cache keys include region, tenant and epoch; L2 entries are per tenant and unit path, so one tenant's resolution can never be served to another. Targeted platform values select by tenant type only. Capacity: resolution is O(depth of chain) with one query per cold read; a noisy tenant cannot evict another tenant's L2 entries beyond the LRU policy, and admin-only `resolveAt` and `explain` calls are rate limited per tenant (proposed 60 per minute).

<!-- check:residency -->
### Data residency and lifecycle

Values, history, pins and caches for a tenant exist only in the tenant's home region. Platform, region and offering values are authored in the platform console of each region and synced from a reviewed source; there is no cross-region read at resolution time. History is retained per [[PKG-settings-data-model#retention]] and deleted with the tenant at offboarding ([[MT-tenant-lifecycle]]).

<!-- check:failure -->
### Failure handling and recovery

If Redis is down, reads fall back to the database (cold path, ≤ 15 ms p95). If the database is also unavailable, `get` throws `DbUnavailableError`; consumers of `stricter_only` and security keys fail closed, other consumers may use the last L1 value for up to 60 seconds and must record that they did. Missed invalidation messages are bounded by L1 (30 s) and L2 (5 min) expiry. Case pins are written in the case-creation transaction, so a case can never exist without its pin; Temporal workflows hold the pin in their input, so retries and replays see the same values. Scheduled activations are idempotent (epoch bump) and safe to re-run.

<!-- check:scale -->
### Capacity, performance and cost

Expected per region at five years: about 200 tenants, 5,000 units, 2 million cases, 300,000 memberships; about 600 setting keys. Warm reads p95 ≤ 2 ms from L1; cold reads ≤ 15 ms with one indexed query on `(tenant_id, key, scope_type, scope_id)`. Case pins add about 40 keys per case, roughly 80 million small rows over five years, partitioned by month (see [[PKG-settings-data-model#volume]]). Cost is dominated by Redis memory for L2 (estimated under 200 MB per region).

<!-- check:observability -->
### Observability

Resolution latency and cache hit ratio per layer, invalidation lag (commit to first read of the new epoch, sampled), drift counts per region, and refused writes by reason are emitted as OpenTelemetry metrics and shown on the "Configuration health" dashboard per region. Per-tenant questions ("why does this value apply") are answered by `explain`, not by telemetry. Alerts: invalidation lag p99 > 30 s for 10 minutes; drift values growing after a bound change for more than 7 days (task to tenant success team).

<!-- check:rollout -->
### Rollout and migration

Phase 1: extend `@nomology/settings` to the eight scopes with a compatibility shim that maps the old `org_unit` level to `unit` and the old platform override to `platform`. Migrate stored values with an expand-and-contract migration ([[PKG-settings-data-model#migrations]]). Phase 2: case pins for keys marked `case_start`, behind release flag `config.case_pins.enabled` per region ([[PKG-feature-flags]]). Phase 3: tenant-type targeting and managed values with the first SEBI ODR blueprint. Rollback: each phase is flag-gated; disabling pins falls back to live resolution for new cases only, and existing pins are kept.

<!-- check:reversibility -->
### Reversibility

Hard to change later, decided deliberately here: the scope list and order, the "broadest lock wins" rule, clearing narrower values on lock, case pinning at case start, and tenant type as the only selector. Adding a scope later means migrating every definition's `scopes` list and the chain builder, so it needs an ADR. Easy to change: cache sizes and TTLs, the drift-scan schedule and the explain format.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "kind": "vendor",
    "title": "Salesforce Help: Create Custom Settings",
    "url": "https://help.salesforce.com/s/articleView?id=sf.cs_about.htm&language=en_US&type=5",
    "vendor": "Salesforce"
  },
  {
    "id": "R2",
    "kind": "vendor",
    "title": "Salesforce Help: Protection and Privacy Options for Custom Metadata Types",
    "url": "https://help.salesforce.com/s/articleView?language=en_US&id=platform.custommetadatatypes_protection.htm&type=5",
    "vendor": "Salesforce"
  },
  {
    "id": "R3",
    "kind": "vendor",
    "title": "ServiceNow Docs: Add a system property",
    "url": "https://docs.servicenow.com/bundle/orlando-platform-administration/page/administer/reference-pages/task/t_AddAPropertyUsingSysPropsList.html",
    "vendor": "ServiceNow"
  },
  {
    "id": "R4",
    "kind": "vendor",
    "title": "Microsoft Learn: Use environment variables in Power Platform solutions",
    "url": "https://learn.microsoft.com/en-us/power-apps/maker/data-platform/environmentvariables",
    "vendor": "Microsoft"
  }
]
```

<!-- end -->
