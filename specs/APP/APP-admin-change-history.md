---
id: "APP-admin-change-history"
title: "Admin audit log, change history and rollback"
parent: "APP-tenant-admin-console"
order: 1
type: "feature"
template: "frontend"
status: "draft"
owner: null
indicative: false
summary: "Change sets with readable diffs, approvals and rollback; tenant audit search and export; support activity; point-in-time view of the configuration that applied to a case"
links: []
rev: 1
syncHash: "df292230e73d2437"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 2.1.2.5.1 Admin audit log, change history and rollback

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Change sets with readable diffs, approvals and rollback; tenant audit search and export; support activity; point-in-time view of the configuration that applied to a case

<!-- section:scope -->
## Scope, audiences and surfaces

Screens in the tenant admin console for answering "who changed what, when, why, through which surface, and can we undo it?":

1. **Change history** (`/admin/changes`): one entry per **change set** ([[PKG-configuration-lifecycle]]), the single unit of administrative change (one admin op, one publish of a configuration version, or one bulk job), shared with the review queue, with a readable diff, approvals, and rollback.
2. **Audit log** (`/admin/audit`): search and export of the tenant's full audit stream ([[PKG-audit-trail]]), including sign-ins, denials, sensitive reads and case actions, for `auditor` and `security_admin`.
3. **Support activity** (`/admin/security/support-access/activity`): every Nomology support grant and the actions taken under it ([[PKG-support-access-and-impersonation]]).
4. **Point-in-time view**: "show the effective configuration for this case type (or this case) on a date", answering what rules applied to a case.

Personas: `auditor` (read and export), `security_admin` (read, export, rollback of security changes), `tenant_admin` and the delegated admin of each domain (read their domain, roll back their own domain's changes), `unit_admin` (changes at its unit scope), `tenant_owner` (all).

Out of scope: the audit storage, sealing and retention ([[PKG-audit-trail]], [[PKG-audit-log-schema]]); configuration version storage ([[PKG-settings-data-model]], [[PKG-configuration-lifecycle]]); case history for the secretariat ([[APP-secretariat-console]]); platform audit for Nomology staff (`/platform/audit`).

<!-- section:routing -->
## Routes, layouts and boundaries

```text
app/(tenant-admin)/admin/
  changes/                       # change sets: filters state, domain, op, actor, via, scope, date; "my changes", "awaiting my review"
  changes/[changeSetId]/         # summary, diff, validation, approvals, related audit events, approve, publish, rollback
  changes/point-in-time/         # pick case type or case ref + date → effective configuration with sources
  audit/                         # full audit search (actor, action, target, case ref, outcome, via, date range ≤ 31 days per query)
  audit/exports/                 # export jobs and downloads
  security/support-access/activity/   # grants, sessions, actions under each grant
```

Old links under `/admin/history/...` redirect to `/admin/changes/...`.

<!-- section:rendering -->
## Rendering and caching strategy

Dynamic, `private, no-store`, never cached: history must always show the latest state. Diffs are computed server-side from stored versions and rendered as structured lists (setting key, scope, before, after) and, for documents such as templates and blueprints, as a side-by-side text diff in a lazily loaded chunk.

<!-- section:data -->
## Data fetching and mutations

**Change set**: history reads the change sets owned by [[PKG-configuration-lifecycle]] (tables `config.change_set`, `config.change_item` and `config.change_review`, schema in [[PKG-settings-data-model#tables]]; decision D3). There is no separate admin change table. Every admin op, configuration publish and bulk job produces a change set; direct ops are recorded as a published change set with one `admin.op` item. The fields this screen uses:

| Field (`config.change_set` unless stated) | Shown as |
|---|---|
| `number` | Reference such as `CS-0042`, used in the URL with the `id` |
| `op_key`, `domains` | Admin op label and domain filter |
| `item_kind`, `target_ref`, `target_scope_type`, `target_scope_id` (`config.change_item`) | What changed and at which scope |
| `author_membership_id`, `author_principal_id`, `on_behalf_of_membership_id`, `author_platform_user_id` | Actor (user, service account, AI agent or Nomology support) and the human it acted for |
| `via` | `console`, `api`, `bulk`, `copilot`, `support`, `scim`, `system` |
| `reason`, `ticket_ref` | From the form; required for some ops |
| `config.change_review` rows | Approvals and rejections, with reviewer and step-up time |
| `base_version`, `result_ref`, `diff`, `inverse` (`config.change_item`) | Before and after: versions for versioned changes, JSON Patch for direct changes (hashed for personal fields) |
| `reversible`, `origin = revert` with `origin_ref`, `reverted_by_change_set_id` | Rollback chain |
| `bulk_job_id`, `copilot_run_id`, `support_grant_id`, `origin_ref` | Source links |
| Audit events with this `change_set_id` ([[PKG-audit-trail]]) | Related audit events |

| Action | Op key | Notes |
|---|---|---|
| Roll back | `admin.change.rollback` | **Versioned** changes: publishes the `before` version as a new version (lifecycle applies, including maker-checker). **Direct** changes: runs the declared inverse op (for example `admin.role.unassign` for `admin.role.assign`) with current checks. **Bulk** changes: creates a bulk job of inverse rows for the rows that succeeded |
| Export audit | `admin.audit.export` | BullMQ job `audit-export` producing JSONL plus a hash manifest; signed URL valid 24 h; step-up |
| Point-in-time resolve | `admin.config.resolve_at` | Uses the settings resolver with `asOf`; for a case, uses the pinned values recorded at case start ([[PKG-configuration-scope-hierarchy]]) |

<!-- section:state -->
## Client state and URL state

Filters, date range and selected change set in the URL so a link can be shared with a colleague or an auditor. Diff view mode (list or side-by-side) is a per-user preference. No local drafts.

<!-- section:forms -->
## Forms, validation and uploads

Rollback dialog: shows what will happen in plain words ("This will publish version 7 of Session settings again, replacing version 9"), the later changes that touch the same objects, whether approval will be needed, a required reason, and step-up when the original op needed it. Export form: date range (up to 13 months hot data; older ranges go to an archive request), filters, format (JSONL or CSV with formula neutralisation).

<!-- section:errors -->
## Error, loading and empty handling

| Situation | Handling |
|---|---|
| `change-not-reversible` | The rollback button is replaced by "Cannot be undone" with the reason (for example "Invitations already sent", "Secret was shown once", "Deletion is permanent") |
| `rollback-conflict` | Lists later change sets on the same objects with links; offers to roll back the latest first |
| Rollback would violate current bounds | Explains the bound (for example the platform now requires MFA for admins) and blocks |
| Archive range requested | Creates an archive retrieval request; notifies when ready |
| No permission for the domain | Change sets of other domains are listed with domain and actor only, without diff (for `unit_admin` and delegated admins) |

<!-- section:performance -->
## Performance budgets

History list p95 under 1 s for the last 90 days; audit search p95 under 2 s for filtered 31-day queries over 13 months of hot data ([[PKG-audit-trail#nfr]]); export of 1 million events within 10 minutes. Diff rendering for a 400-setting blueprint under 1.5 s.

<!-- section:security -->
## Security headers and browser session

- History and audit are tenant-scoped under forced RLS; unit admins see only change sets at their unit scope; delegated admins see diffs only for their domains.
- Audit events store IDs and hashes; the UI resolves names only for memberships the viewer may see, otherwise shows "User in {unit}".
- Exports require step-up and are themselves audited (`admin.audit.exported`) and listed in history.
- Rollback runs the same permission checks as the original op at the time of rollback; nobody can roll back a change they could not make.
- Support actions are always shown with the grant reference and cannot be hidden or filtered out by default views.

<!-- section:i18n -->
## Localisation hookup

Op keys and audit actions are shown through translated labels from the registry (for example `admin.role.assigned` → "Role assigned"); raw keys are available in a details panel. Times in tenant time zone with UTC on hover.

<!-- section:theming -->
## Tenant theming hookup

Diff colours use semantic tokens with text markers ("Added", "Removed", "Changed") so meaning never depends on colour alone; support and AI-originated changes carry a fixed-token badge.

<!-- section:observability -->
## Frontend observability

Metrics: rollbacks per domain per month, rollback failures by reason, export jobs and sizes, median time from change to rollback. A rollback of a security domain change notifies tenant owners and is sent to the SIEM feed ([[OBS-security-events]]).

<!-- section:testing -->
## Testing strategy

- Every op in the registry with `reversible` declared has a test proving rollback restores the prior effective state; ops marked irreversible show "Cannot be undone".
- Versioned rollback goes through maker-checker where the original did.
- Conflict detection when a later change touched the same object.
- Point-in-time: for a case started under version 5 of a case-type blueprint, the view shows version 5 values even after version 7 is published.
- Unit admin and delegated admin visibility tests; two-tenant diff test.
- CSV export is neutralised against formula injection.

<!-- section:questions -->
## Open questions

- [ ] Should tenants be able to receive a monthly signed digest of their audit anchor ([[PKG-audit-trail#questions]]) from this page? (owner: product)
- [x] Retention of change sets follows [[PKG-settings-data-model#retention]]: 8 years after the change set is superseded (configuration evidence). Confirm with the DPO that this is long enough for tenants whose case records are kept longer. (owner: DPO)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation in rendering and caching

Change sets and audit events are tenant-owned with forced RLS; exports are written to the tenant's region under a tenant prefix; the support activity page shows only grants for this tenant.

<!-- check:data-exposure -->
### Server boundary and data exposure

Diffs of personal fields show hashes or 'changed' only; names are resolved only for memberships the viewer may see; delegated admins see diffs only for their domains.

<!-- check:session -->
### Sessions in the browser

Exports and rollbacks of security changes require step-up; signed export URLs expire in 24 hours and are single-tenant.

<!-- check:resilience -->
### Failure, deploys and version skew

Exports and bulk rollbacks are jobs that resume after failure; a rollback is a new change set, so a failed rollback leaves the current state untouched.

<!-- check:accessibility -->
### App-level accessibility mechanics

Diffs are available as structured lists with text labels; the side-by-side view has a linear alternative; filters are labelled form controls with a results-count live region.

<!-- check:residency -->
### Region, residency and telemetry privacy

History, audit search and exports stay in the tenant's home region; archive retrieval reads the regional archive bucket only.

<!-- end -->
