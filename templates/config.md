# Template: Settings catalogue (`config`)

Generated from `config.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Registers every configurable setting in one domain, at every level it can be set (platform, region, offering, tenant, unit, case type, case, user), so admins, engineers and auditors share one source of truth for defaults, inheritance, locks, permissions and audit.

**Depth:** 2–6 pages. The catalogue table is the heart: every setting has a stable key, type, default, allowed scopes, lock behaviour, permission to change, when the change takes effect and audit class. Group settings into sub-tables of 5–20 rows. Behaviour belongs in the owning package or feature node; link to it rather than re-specifying it here.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `purpose` Purpose and scope (level 1)

Which domain this catalogue covers, which features consume these settings (link their nodes), and what is deliberately not a setting here (deployment configuration, feature flags used for release, secrets).

Illustrative example (not a requirement):

> Covers how people prove who they are and how long they stay signed in. Consumed by [[PKG-authentication]] and the sign-in pages. Not here: provider client secrets (stored in the secrets manager), release flags.

### `scopes` Scopes that apply (level 1)

Which levels of the hierarchy in [[PKG-configuration-scope-hierarchy]] this domain uses, who administers each level, and any level that is skipped and why.

Illustrative example (not a requirement):

> | Scope | Used | Administered by |
> |---|---|---|
> | Platform | yes | Platform owner |
> | Tenant | yes | Tenant security admin |
> | Case | no | Sign-in happens before a case is chosen |

### `catalogue` Settings catalogue (level 1)

One row per setting. Columns: key (dot-separated, stable, lower_snake segments), type and allowed values, platform default, allowed scopes, lock (can a higher scope force the value for all lower scopes?), plan entitlement if any, permission needed to change it, when it takes effect (immediately, next sign-in, new cases only), audit class (standard, sensitive, maker-checker).

Illustrative example (not a requirement):

> | Key | Type | Default | Scopes | Lockable | Plan | Permission | Takes effect | Audit |
> |---|---|---|---|---|---|---|---|---|
> | `auth.session.idle_timeout_min` | int 5–480 | 30 | platform, tenant | yes | all | `settings.security:write` | next request | sensitive |

### `validation` Validation and dependencies (level 1)

Rules between settings (one setting requires or forbids another), bounds the platform enforces regardless of tenant choice, and what the admin sees when a change is invalid.

Illustrative example (not a requirement):

> - `auth.password.enabled = false` requires at least one of SSO or passkeys to be enabled for every active admin.
> - Bounds: idle timeout can never exceed the platform ceiling for the tenant's data classification.

### `defaults` Defaults by tenant type (level 2)

Starting values for each tenant blueprint (for example arbitral institution, SEBI ODR institution, CORD tenant, court or government programme), and why they differ.

Illustrative example (not a requirement):

> | Key | Arbitral institution | SEBI ODR institution | CORD tenant |
> |---|---|---|---|
> | `auth.mfa.required_roles` | admins | all staff | admins |

### `admin_ux` Where it is administered (level 2)

Console, page and section for each group of settings; API endpoint; whether the admin copilot may propose changes; how inherited and locked values are shown.

Illustrative example (not a requirement):

> Tenant admin console → Security → Sign-in. Shows the inherited value with its source ("Platform default") and a lock icon when a higher scope enforces it. API: `PATCH /admin/v1/settings/auth.*`.

### `change_control` Change control and audit (level 2)

Which changes need maker-checker approval, who is notified, how a change is rolled back, and what the audit record holds (old value, new value, scope, actor, reason).

Illustrative example (not a requirement):

> Turning off MFA for any role needs approval from a second security admin and notifies all tenant owners. Rollback restores the previous published version in one action.

### `migration` Versioning and migration (level 2)

How keys are added, renamed or retired without breaking tenants; how defaults change for existing tenants; how settings travel in configuration packages ([[PKG-configuration-packages]]).

Illustrative example (not a requirement):

> Keys are never reused. Renames keep an alias for two releases. A changed platform default applies only to tenants still inheriting it; tenants with an explicit value are listed in the release notes.

### `testing` Testing (level 2)

How resolution (inheritance, locks, entitlements) is tested for these keys, and how the catalogue is kept in sync with code (for example a generated registry checked in CI).

Illustrative example (not a requirement):

> The registry in `packages/settings/registry/auth.ts` is the source; CI fails if this catalogue and the registry disagree.

### `questions` Open questions (level 3)

Unresolved items as a checklist, each with an owner in brackets.

Illustrative example (not a requirement):

> - [ ] Should unit-level admins be allowed to shorten session timeouts? (Security)

### `notes` Notes (level 3)

Anything else worth keeping.

## Checks

### `inheritance` Inheritance and locks

**Question:** For every setting, is it unambiguous which value applies to a given user, case and tenant, and why?

- Is each key's allowed scope list explicit, and is the resolution order the one defined in [[PKG-configuration-scope-hierarchy]]?
- Can a higher scope lock a value, and is a locked value shown as locked (with its source) everywhere it appears?
- What happens to explicit lower-scope values when a higher scope later locks the setting?

**Good answer:** Every key lists its scopes and lockability; resolution follows the shared hierarchy with no per-feature exceptions; the console shows the effective value, its source scope and lock state; locking a value either clears or freezes lower overrides by a documented rule, and the admin is told how many overrides are affected before confirming.

**Red flags:**

- Features reading settings directly from tables instead of the resolver
- Locks that silently ignore lower values without telling anyone
- Different inheritance rules per domain

### `permissions` Who may change what

**Question:** Is the permission needed to change each setting defined, scoped and least-privilege?

- Which permission from [[PKG-permission-catalogue]] guards each group?
- Can a delegated admin (for example a branding admin) change only their domain?
- Are security-weakening changes subject to maker-checker ([[PKG-separation-of-duties]])?

**Good answer:** Each group maps to one named permission; delegated admin roles hold only their domain's permission; changes that weaken security, privacy or legal notices need a second approver; platform-only settings cannot be changed by any tenant role.

**Red flags:**

- One 'admin' permission for every setting
- Tenant admins able to change platform-only keys via the API
- No second approver for disabling MFA or audit

### `safety` Safe bounds

**Question:** Can any combination of tenant choices put the platform, the tenant's data or a party's legal rights at risk?

- Are there hard platform bounds (ceilings, floors) that tenant values cannot cross?
- Are legally mandatory behaviours (for example statutory notices, audit trail) non-configurable?
- Is every cross-setting dependency validated server-side?

**Good answer:** Hard bounds are listed and enforced in the resolver; legally mandatory behaviours are not settings at all, or are locked at platform scope; dependencies are validated on the server with clear messages; the catalogue names the legal or security reason for each bound.

**Red flags:**

- Audit logging or statutory notices that a tenant can switch off
- Validation only in the browser

### `timing` When changes take effect

**Question:** Is it clear when a change applies and to which in-flight work?

- Does a change affect running cases and workflows, or only new ones?
- Are caches invalidated within a stated time?
- Is the user told when a change will apply?

**Good answer:** Each key states its effect timing (immediate, next sign-in, new cases only, next billing period); running workflows read pinned values where fairness requires it; cache invalidation is event-driven with a stated maximum lag; the console shows the timing before the admin confirms.

**Red flags:**

- Procedural settings changing mid-case without a record
- Unbounded cache staleness

### `audit` Audit and rollback

**Question:** Can we reconstruct, for any date, which value applied and who changed it, and undo a bad change quickly?

- Is every change versioned with actor, reason, old and new value and scope?
- Can the effective configuration for a case on a past date be reproduced?
- Is rollback one action, and is it itself audited?

**Good answer:** Changes are written to the audit trail ([[PKG-audit-trail]]) and to versioned configuration history; a point-in-time resolver reproduces effective values for any case and date; rollback restores a previous version and is audited like any change.

**Red flags:**

- Settings stored as mutable rows with no history
- No way to show a party which procedural settings applied to their case

### `sync` Catalogue matches code

**Question:** Will this catalogue stay true as the code changes?

- Is there a typed registry in code that this catalogue is generated from or checked against?
- Do new keys need an owner node and a default before merge?

**Good answer:** A typed registry in `@platform/settings` is the single source; CI compares it with the catalogue; every key has an owner, default, scopes and audit class before it can merge.

**Red flags:**

- Hand-maintained list with no CI check
- Keys created ad hoc in feature code

