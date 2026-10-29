---
id: "PKG-configuration-lifecycle"
title: "Configuration change lifecycle"
parent: "PKG-configuration-and-customisation"
order: 7
type: "feature"
template: "design"
status: "draft"
owner: null
indicative: false
summary: "One change process for every configuration change (settings, case-type blueprints, forms, templates, rules, roles, themes, integrations): change sets moving draft → in review → approved → published → superseded, maker-checker by audit class, validation and impact analysis, scheduled publish, rollback, preview overlays and sandbox tenants"
links: []
rev: 1
syncHash: "eb4dafe8bab4a957"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.8.7 Configuration change lifecycle

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> One change process for every configuration change (settings, case-type blueprints, forms, templates, rules, roles, themes, integrations): change sets moving draft → in review → approved → published → superseded, maker-checker by audit class, validation and impact analysis, scheduled publish, rollback, preview overlays and sandbox tenants

<!-- section:context -->
## Context and scope

Before this overhaul, configuration changed in two different ways: settings were written directly with step-up and an audit event ([[PKG-settings]]), while artefacts (forms, workflow templates, document templates, decision tables) went through draft, review and publish in `@nomology/config-core` ([[PKG-configuration-and-customisation]]). Themes and terminology had their own activation flows ([[PKG-branding-and-theming]], [[PKG-tenant-terminology-and-copy]]). Admins therefore could not group related changes ("new fee schedule plus the notice template that announces it"), reviewers saw different screens for each, and rollback meant something different everywhere.

This note defines one lifecycle, built on a **change set**, that every configuration change follows, whoever or whatever makes it: a tenant admin in the console, the tenant admin API ([[INT-tenant-admin-api]]), a bulk import ([[APP-bulk-admin-operations]]), a package import ([[PKG-configuration-packages]]), a Nomology implementation engineer, or the admin copilot ([[APP-admin-copilot]]). States are those of the shared model: `draft` → `in_review` → `approved` → `published` → `superseded`.

<!-- section:goals -->
## Goals and non-goals

**Goals**
- Every configuration change, of any kind, is a change set with an author, a reason, a readable diff, a review decision proportionate to risk, and an audit trail.
- Maker-checker where the risk needs it, and no friction where it does not: a `standard` change can be published by its author in one step.
- Changes can be grouped, previewed against the live configuration, tested in a sandbox, scheduled for a date, and rolled back in one action.
- Running cases are never changed by a publish (pinning, [[PKG-configuration-scope-hierarchy#design]]) unless a reviewed migration says so.
- AI proposes, humans approve: AI-authored change sets are drafts with an explanation, and the human who asked for them cannot also be the checker.

**Non-goals**
- Release of platform code and flags ([[DEP-release-notes-and-change]], [[PKG-feature-flags]]).
- Migration of running cases between blueprint versions (owned by [[WF-workflow-versioning]]; it uses a change set as its approval vehicle).
- Access requests and role grants to people, which use the same maker-checker primitives but are owned by [[PKG-separation-of-duties]] and [[PKG-jit-and-break-glass]].

<!-- section:design -->
## Design

### 1. Change sets and items

A **change set** is a named, tenant-owned (or platform-level) bundle of **items**. Each item is one of:

| Item kind | Example | Registered by |
|---|---|---|
| `setting.set`, `setting.unset`, `setting.lock`, `setting.unlock`, `setting.constrain` | `brand.footer.show_unit_name = false` at tenant scope, locked | [[PKG-settings]] |
| `artefact.version` | New version of a form, case-type blueprint, document or notification template, decision table, threshold set, theme, terminology override set, custom field definition, automation rule | [[PKG-configuration-and-customisation]] and its children |
| `role.version`, `permission_set.version` | Custom role "Senior case manager" v3 | [[PKG-roles-and-permission-sets]] |
| `integration.definition` | Connection definition without secrets | [[INT-connections-admin]] |
| `case.migration` | Move 37 running cases to blueprint v4 | [[WF-workflow-versioning]] |
| `admin.op` | A direct admin operation that is not versioned, such as assigning a role or deactivating a user, with its before and after state and declared inverse | [[APP-administration-model]] |

Every item records its **base version** (the version of the target when the item was drafted) so that conflicts are detected at publish.

The change set is the **only** record of configuration and administrative change (decision D3): table `config.change_set` with `config.change_item` and `config.change_review` ([[PKG-settings-data-model#tables]]), API `/admin/v1/change-sets`. Direct admin operations that need no review (for example a standard-tier role assignment) are still written as a change set with one `admin.op` item, created and published in the same transaction. The admin console's history and rollback screens ([[APP-admin-change-history]]) read these tables; there is no separate admin change table.

Every change set records:

| Field | Meaning |
|---|---|
| `number` | Per-tenant reference shown to admins, for example `CS-0042` |
| `op_key`, `domains` | The admin op and the catalogues or areas touched |
| `via` | `console`, `api`, `bulk`, `copilot`, `support`, `scim` or `system` |
| `origin`, `origin_ref` | `package_import`, `blueprint`, `case_migration` or `revert`, with the source ID |
| `author_membership_id`, `author_principal_id`, `on_behalf_of_membership_id`, `author_platform_user_id` | Human author, non-human principal, the human an agent acted for, and Nomology staff under a support grant |
| `reason`, `ticket_ref` | Required reason and optional external reference |
| `bulk_job_id`, `copilot_run_id`, `support_grant_id` | Source links |
| `reversible`, `reverted_by_change_set_id` | Rollback chain (a revert's own `origin_ref` points back) |
| Reviews | Rows in `config.change_review` (reviewer, decision, step-up time) |

Audit events carry `change_set_id`, so related audit events are found by that ID rather than stored on the change set.

### 2. States and transitions

```text
           submit                 approve (checker)          publish / activate at effective_from
draft ───────────────▶ in_review ───────────────▶ approved ───────────────────────────────▶ published ──▶ superseded
  ▲  │                    │  │                                                                 (when a later change
  │  │ withdraw           │  └── reject ──▶ rejected                                              set replaces all its
  │  ▼                    │                                                                       items)
  │ withdrawn             └── edit by author ──▶ draft (approvals cleared)
  └──── rebase ◀── stale (base version changed)          failed ◀── activation re-validation fails
```

| Transition | Who | Guard |
|---|---|---|
| create, edit | Anyone holding the update permission for every item's domain (for example `settings.branding:write`, `workflow.definition:update`) | Item scopes allowed for the author ([[PKG-settings-catalogue]] conventions) |
| submit | Author | All validations pass (section 4); reason given |
| approve | Checker | Holds `config.change_set:approve` and the domain approve permission (`settings.<catalogue>:approve` or `<resource>:approve`); is not the author; is not the human on whose behalf an AI agent authored it; fresh step-up within `auth.step_up.window_minutes` (default 5 minutes, maximum 15, [[PKG-settings-security-and-identity]]) |
| reject | Checker | Comment required |
| publish | Author or checker, or the `config-activate` job at `effective_from` | Re-validation passes; no stale items; approval not expired (default 14 days) |
| rollback | See section 7 | |

- **CLC-FR-1** Every write to configuration goes through a change set, including single-setting edits in the console. For a `standard` change, the console creates, submits and publishes the change set in one click; the record still exists.
- **CLC-FR-2** Editing a change set after any approval clears all approvals and returns it to `draft`.
- **CLC-FR-3** A change set is published atomically in one database transaction per region: all items take effect together or none do.

### 3. Review policy

The review a change set needs is the strictest required by any of its items:

| Audit class (per setting key or artefact kind) | Review | Step-up | Who is notified on publish |
|---|---|---|---|
| `standard` | None; author may publish | No | Nobody (visible in change history) |
| `sensitive` | None by default; reason required | Yes | Tenant owner and the domain admins (in-app; daily email digest) |
| `maker_checker` | One checker who is not the author | Yes, author and checker | Tenant owner, domain admins, `auditor` role holders (in-app plus email) |

Tenants can tighten, never loosen, the policy with change-control settings (proposed for [[PKG-settings-access-control]], which owns separation-of-duties settings):

| Key | Type | Default | Meaning |
|---|---|---|---|
| `access.change_control.review_all_changes` | boolean | false | Treat every `standard` and `sensitive` item as `maker_checker` |
| `access.change_control.maker_checker_kinds` | set of item kinds | `[]` | Extra kinds that always need a checker (for example `artefact.version:document_template`) |
| `access.change_control.approval_expiry_days` | int 1–30 | 14 | Approval lapses if not published in time (defined in [[PKG-settings-access-control#catalogue]], like the other keys in this table) |
| `access.change_control.emergency_rollback_roles` | set of role keys ⊆ {`tenant_owner`, `security_admin`, `tenant_admin`} | [`tenant_owner`, `security_admin`] | Who may use the emergency rollback path |

Platform-scope change sets (platform, region, offering values; blueprints; platform packages) use the same model in `/platform/changes`, with `platform_admin` as checker and `platform_security` additionally required for security bounds (`auth.*`, `access.*` keys).

- **CLC-FR-4** The checker must differ from the author by person, not by role or session: the platform compares the `user_account.id` behind both memberships, and for AI-authored change sets the invoking human counts as the author ([[PKG-separation-of-duties]]).
- **CLC-FR-5** An `ai_agent` or `service_account` principal can create and submit change sets within its own permissions but can never approve or publish a `sensitive` or `maker_checker` change set ([[PKG-non-human-principals]]).

### 4. Validation and impact analysis

Run on save (fast checks), on submit (all checks) and again at publish or activation:

1. **Schema**: Zod schema per setting key and artefact kind.
2. **Scope rules**: locks, bounds, entitlements and allowed scopes, using the resolution algorithm in write mode ([[PKG-configuration-scope-hierarchy]], SCOPE-FR-6).
3. **Dependencies**: every reference (a form used by a blueprint, a template used by an automation rule, a role used by a task) resolves to a published version or to an item in the same change set.
4. **Cross-setting rules**: rules declared in each catalogue's `validation` section, for example "public filing on requires a privacy notice version for every enabled locale".
5. **Policy checks**: locked content cannot be overridden ([[PKG-tenant-terminology-and-copy]]); themes pass accessibility checks ([[PKG-tenant-theme-accessibility]]); no personal data or secrets in values.
6. **Impact analysis** (BullMQ queue `config-impact-analysis`, result cached on the change set): how many units, users, open cases and scheduled jobs the change affects; which running cases are unaffected because of pins; which narrower values a lock will clear; which dormant values will wake.
7. **Simulation** (optional for blueprints and decision tables): results of the test runs in [[WF-workflow-simulation]] attached to the item.

Errors block submit; warnings are shown to the checker and must be acknowledged.

### 5. Publish and scheduled activation

- **CLC-FR-6** Publishing writes setting values with `valid_from = now` (or `effective_from`), marks artefact versions `published` and the previous versions `superseded`, bumps the tenant configuration epoch, writes outbox events (`config.change_set.published`) and the audit event `admin.config.published`, all in one transaction.
- **CLC-FR-7** A change set with `effective_from` in the future stays `approved` with `scheduled_for` set. A BullMQ delayed job on queue `config-activate` publishes it at that time after re-validation. If re-validation fails, the change set moves to `failed` and the author and checker are notified; nothing is applied.
- **CLC-FR-8** A change set whose items' targets changed since drafting is `stale`. If no item overlaps a changed target, the platform rebases it automatically and records that; otherwise the author must rebase, which clears approvals.

### 6. Preview

Every editor offers **Preview** before submit, using a read-only overlay of the draft on the live configuration (`resolve(..., { overlay: changeSetId })`):

| What is previewed | How |
|---|---|
| Effective values | `/admin/config/effective?overlay=<changeSetId>`: per key, current versus proposed effective value for a chosen unit, case type and user |
| Forms and portal pages | Render as a chosen persona (party, counsel, secretariat) with a synthetic sample case, in a same-origin iframe |
| Notifications and documents | Rendered with sample data; sending is disabled except "send test to me" |
| Theme and terminology | Sample case list, filing step, dialog, email and PDF cover in light and dark mode |
| Case-type blueprints | Simulation runs ([[WF-workflow-simulation]]) |

Preview never writes to production data, never sends to parties and never fills caches.

### 7. Rollback

- **Revert a change set**: creates a new change set containing the inverse of every item (previous values; previous artefact versions republished; cleared narrower values restored). It follows the normal review policy.
- **Restore a version**: for one setting or artefact, from its history page.
- **Emergency rollback**: a holder of a role in `access.change_control.emergency_rollback_roles` may publish a revert of the most recent change set alone, with step-up and a reason, if every restored value was itself previously approved and is still within current bounds and entitlements. The platform opens a mandatory post-hoc review task for another approver, due within 2 business days, and notifies the tenant owner.
- **CLC-FR-9** Rollback never changes pinned values of running cases; a revert of a case migration is itself a migration.
- **CLC-FR-10** Rollback is audited as `admin.config.rolled_back` with a link to the reverted change set.

### 8. Sandbox tenants

Production data never leaves production ([[FND-environments]], ENVS-2). A sandbox is therefore a **separate tenant in the same production region**, linked to its parent, with production controls:

| Aspect | Rule |
|---|---|
| Creation | `tenant_owner` or `tenant_admin` at `/admin/sandboxes` (permission `config.sandbox:create`); count limited by entitlement `limit.config_sandboxes` |
| Identity | `tenant.type = 'sandbox'`, `parent_tenant_id` set; host `<slug>-sbx<n>.<domain>`; environment banner on every page and "SANDBOX" in every email subject |
| Data | Synthetic only at launch: generated from the blueprint's fixture set ([[PKG-configuration-packages]]). A masked copy of production case data is not offered (open question) |
| Configuration | Created from, and refreshable from, a snapshot package of the parent's published configuration (Temporal workflow `SandboxRefreshWorkflow` on task queue `config-<region>`) |
| Outbound effects | Email, SMS and WhatsApp only to allow-listed addresses of the parent's staff; integrations only with sandbox credentials; webhooks only to endpoints flagged as test; payments in provider test mode |
| Billing | Excluded from usage meters; included in the plan's sandbox allowance |
| Access | Members copied from the parent's admin roles on request; parties are synthetic accounts |
| Lifetime | Expires after 90 days without sign-in (warning at 75 days); deletion through the normal tenant deletion path |
| Promotion | Export selected change sets as a package and import them into the parent as a draft change set ([[PKG-configuration-packages]]); the parent's own review applies |

Nomology implementation teams also use UAT tenants in the UAT environment ([[FND-environments]]) with the same promotion path, which works like moving a change through a staged pipeline (pattern borrowed from DevOps Center [R2] and update sets [R3]).

### 9. Surfaces and API

| Surface | Route or endpoint |
|---|---|
| Change history and review queue | `/admin/changes` (filters: state, domain, author, awaiting my review) and `/admin/changes/[changeSetId]` (diff, validation, impact, comments, approve, publish, revert) |
| Per-object history | "History" tab on every settings page and artefact editor, linking to change sets ([[APP-admin-change-history]]) |
| Platform | `/platform/changes`, `/platform/tenants/[tenantId]/changes` |
| Tenant admin API ([[INT-tenant-admin-api]]) | `POST /admin/v1/change-sets`, `POST /admin/v1/change-sets/{id}/items`, `POST /admin/v1/change-sets/{id}/actions/{submit|approve|reject|publish|withdraw|rebase}`, `GET /admin/v1/change-sets/{id}/diff` (JSON Patch per item [R4]), `POST /admin/v1/change-sets/{id}/actions/revert` |
| Internal tRPC | `admin.config.changeSets.*` in the admin router ([[APP-internal-api-trpc-routers-per]]) |

Approve and publish over the API require a user token with recent step-up; API clients with client credentials can create and submit only.

### 10. Audit events

`admin.config.drafted`, `admin.config.submitted`, `admin.config.approved`, `admin.config.rejected`, `admin.config.withdrawn`, `admin.config.published`, `admin.config.failed`, `admin.config.rolled_back`, `admin.settings.published` (one per setting item, with old value, new value, scope and source), `admin.settings.locked`, `admin.settings.unlocked`, `admin.sandbox.created`, `admin.sandbox.refreshed`, `admin.sandbox.deleted`. Each records actor, on-behalf-of (for AI agents), approver, reason, change set ID and item diff summary, written to [[PKG-audit-trail]] in the publishing transaction.

<!-- section:examples -->
## Worked examples

**Example 1: a standard change in one click.** A `content_admin` changes `brand.email.footer_note`. The console creates change set CS-0911 with one item, validates it, and publishes it on Save. The History tab shows "Published by A. Rao, 28 Oct 2026 10:14, reason: new office address". No reviewer is involved because the key's audit class is `standard`.

**Example 2: grouped, scheduled, maker-checker change.** From 1 April 2027 an institution changes its fee schedule (decision table, `maker_checker`) and the notice template announcing fees (`standard`). The `workflow_designer` drafts both in CS-1002 with `effective_from = 2027-04-01T00:00+05:30`, attaches simulation results, and submits. The checker (`tenant_admin`, a different person) reviews the diff and impact ("applies to new cases from 1 April; 212 open cases keep the current schedule") and approves with step-up. On 1 April at 00:00 IST the `config-activate` job re-validates and publishes both items in one transaction.

**Example 3: emergency rollback.** A newly published notification template renders the hearing link wrongly. The `tenant_owner` opens CS-1040, selects **Emergency rollback**, gives the reason "broken hearing link" and completes step-up. The previous template version is republished within seconds; a post-hoc review task is assigned to another tenant admin; the audit log shows both events.

**Example 4: AI-drafted change.** A tenant admin asks the copilot "require MFA for all neutrals". The copilot creates draft CS-1101 authored by its `ai_agent` principal on behalf of that admin, containing `auth.mfa.required_personas` with `neutral` added, plus an explanation and impact ("affects 48 neutrals; 12 have no MFA factor enrolled"). The key is `maker_checker`, so the requesting admin cannot approve it; the security admin does.

**Example 5: stale change set.** Two admins draft changes to the same theme. The first publishes; the second change set becomes `stale`. Because both touched the theme item, automatic rebase is not possible; the second admin rebases, sees the merged diff, and resubmits.

<!-- section:alternatives -->
## Alternatives considered

| Option | Why not chosen |
|---|---|
| Direct writes with an audit log only | No grouping, no preview, no maker-checker where needed, and rollback is a manual reconstruction. |
| Capture changes implicitly as the admin works (a "current update set" collecting every edit) | Familiar from ServiceNow update sets [R3], but implicit capture surprises admins and mixes unrelated edits. We make the change set explicit and default it per editor. |
| Git-based configuration for tenants (pull requests on a configuration repository) | Strong review tooling, but tenant admins are not engineers, data residency for configuration would move to a code host, and the platform would have to reconcile drift. Used internally by Nomology for platform defaults in code only. |
| Separate lifecycle per kind (settings, artefacts, roles) | The previous state; inconsistent review and rollback, and no grouped changes. |
| Full sandbox copies of production data | Common in CRM platforms (full and partial copy sandboxes [R1]), but conflicts with ENVS-2 and with data minimisation for case data. Synthetic data plus configuration snapshots meets the testing need. |

<!-- section:crosscutting -->
## Cross-cutting concerns

| Concern | How this design addresses it |
|---|---|
| Security | Step-up for approve and publish of `sensitive` and `maker_checker` items; person-level separation of author and checker; non-human principals cannot approve; API approval only with user tokens. Change sets are tenant-owned and visible only to holders of `config.change_set:read`. |
| Privacy | Change sets carry configuration only. Free-text fields (reason, comments) are short and must not contain personal data; the console warns when it detects emails or phone numbers. Sandbox tenants hold synthetic data only. |
| Tenancy | `config.change_set`, `config.change_item` and `config.change_review` are tenant-owned with forced RLS; platform change sets are in separate platform-level tables. A tenant change set can only contain items that target its own tenant and its units, case types, cases and users. |
| Observability | Metrics: `config.change_set.publish.duration`, `config.change_set.state` (gauge by state), `config.activation.failures`, `config.review.wait_time` (histogram). Dashboard "Configuration changes" per region and per tenant (tenant view in the admin console). |
| Cost | Impact analysis runs asynchronously and is bounded (counts only, capped at 50,000 cases per query, then estimated). |

<!-- section:guardrails -->
## Guardrails

- **CLC-G-1** No code path writes configuration tables except the publish path of this lifecycle; migrations that seed defaults write platform values through a platform change set in the deploy job.
- **CLC-G-2** Every new item kind registers a schema, validators, a diff renderer, an inverse (for revert) and its audit class before it can be used.
- **CLC-G-3** The console never offers "publish" on a `maker_checker` change set to its author.
- **CLC-G-4** Package imports always create a draft change set; nothing imported is published without the target tenant's own review.
- **CLC-G-5** Sandbox tenants can never be promoted to production tenants, and production tenants can never be converted to sandboxes.
- **CLC-G-6** Scheduled activations re-validate; an approval is never applied to a configuration it was not checked against.

<!-- section:ownership -->
## Ownership

| Part | Owner |
|---|---|
| Change set engine, validation pipeline, activation jobs | Platform engineering (configuration team) |
| Maker-checker rules and change-control settings | Authz group with [[PKG-separation-of-duties]] |
| Item kinds | Each registering package |
| Change history UI | Admin group ([[APP-admin-change-history]]) |
| Sandbox tenants | Platform engineering with [[MT-tenant-lifecycle]] |

<!-- section:questions -->
## Open questions

- [ ] Should a masked copy of production configuration plus anonymised case data ever be offered in sandboxes (useful for testing reports)? Proposed: no at launch; DPO to decide. (owner: DPO)
- [ ] Is 14 days the right default approval expiry? (owner: product)
- [ ] Should SEBI ODR and court tenants have `access.change_control.review_all_changes = true` by default in their blueprints? Proposed: yes for court programmes, no for SEBI ODR. (owner: product, legal)
- [ ] May a Nomology implementation engineer act as author and a tenant admin as checker in the tenant's production tenant, with a recorded approval, so that institutions do not have to build their own configuration? Carried over from [[PKG-configuration-and-customisation]]. (owner: CEO, COO)
- [ ] Emergency rollback post-hoc review window: 2 business days proposed. (owner: security lead)

<!-- checks -->
## Template checks

<!-- check:security -->
### Security and privacy

New surface: change-set APIs, the review queue and emergency rollback. Threats: (1) self-approval through a second account or an AI agent: blocked by person-level comparison and the on-behalf-of rule (CLC-FR-4, CLC-FR-5); (2) approving one thing and publishing another: edits clear approvals and publish re-validates (CLC-FR-2, CLC-G-6); (3) abuse of emergency rollback to push unreviewed values: only restores previously approved values within current bounds, single most recent change set, step-up, post-hoc review; (4) compromised API client publishing configuration: client credentials can only create and submit. Personal data: none by design; free-text reasons are short and scanned.

<!-- check:tenancy -->
### Tenancy

Change sets, items, reviews and comments are tenant-owned under forced RLS; the item validator rejects any target outside the tenant. Platform change sets are platform-level and target platform, region or offering scopes only. Impact analysis runs per tenant in the tenant's context through `withTenant`. Sandbox tenants are separate tenants with their own RLS boundary; the parent link is a platform-level column used only for refresh and promotion.

<!-- check:residency -->
### Data residency and lifecycle

All change sets for a tenant live in its home region and are published there. Platform change sets are authored per region; a change that must apply in all regions is published once per region, in the release-wave order of [[DEP-environment-promotion-and-multi]]. Sandbox tenants are in the parent's region. Change-set records are retained as configuration evidence per [[PKG-settings-data-model#retention]].

<!-- check:failure -->
### Failure handling and recovery

Publish is one transaction; on failure nothing applies and the change set stays `approved`. The outbox ensures invalidation and audit events are delivered at least once; consumers are idempotent on change-set ID. Activation jobs are idempotent (a published change set is not republished) and retried with backoff; after 3 failures the change set moves to `failed` with an alert. Impact analysis failures do not block submit but are shown as "impact unknown" warnings that the checker must acknowledge.

<!-- check:scale -->
### Capacity, performance and cost

Expected volume per region: under 5,000 change sets per month across all tenants, mostly single-item `standard` changes. Publish p95 ≤ 500 ms for change sets up to 200 items; larger change sets (blueprint imports) up to 5,000 items publish in ≤ 10 s. Review queue and history queries are indexed by `(tenant_id, state, updated_at)`.

<!-- check:observability -->
### Observability

Per region: publish latency, activation failures, stale-change-set rate, review wait time and emergency rollbacks (each emergency rollback also raises an informational security event, [[OBS-security-events]]). Tenants see their own change activity on the admin overview. Alert: any activation failure for a scheduled change set (owner notified immediately; platform on-call if three or more tenants fail in an hour).

<!-- check:rollout -->
### Rollout and migration

Step 1: introduce change sets behind release flag `config.change_sets.enabled` with the one-click path for `standard` items, so admins see no difference. Step 2: move themes, terminology and artefacts to change sets, keeping their editors. Step 3: enable maker-checker classes per catalogue. Existing artefact versions are imported as already-published single-item change sets so history is continuous. Rollback of the rollout: disable the flag; direct writes resume through the same validators.

<!-- check:reversibility -->
### Reversibility

Hard to change later: the five shared states, atomic publish per change set, person-level maker-checker, and "sandbox is a separate production tenant". These are decided here deliberately. Easy to change: default expiry, notification recipients, and which kinds are `maker_checker` (data in catalogues and tenant settings).

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "kind": "vendor",
    "title": "Salesforce Help: Sandbox Types and Templates",
    "url": "https://help.salesforce.com/s/articleView?language=en_US&id=platform.create_test_instance.htm&type=5",
    "vendor": "Salesforce"
  },
  {
    "id": "R2",
    "kind": "vendor",
    "title": "Salesforce Help: Promote Work Items Through Your Pipeline (DevOps Center)",
    "url": "https://help.salesforce.com/s/articleView?language=en_US&id=platform.devops_center_work_items_promote.htm&type=5",
    "vendor": "Salesforce"
  },
  {
    "id": "R3",
    "kind": "vendor",
    "title": "ServiceNow Docs: System update sets",
    "url": "https://docs.servicenow.com/bundle/rome-application-development/page/build/system-update-sets/concept/system-update-sets.html",
    "vendor": "ServiceNow"
  },
  {
    "body": "IETF",
    "id": "R4",
    "ident": "RFC 6902",
    "kind": "standard",
    "title": "JavaScript Object Notation (JSON) Patch",
    "url": "https://www.rfc-editor.org/rfc/rfc6902"
  }
]
```

<!-- end -->
