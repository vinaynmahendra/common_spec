---
id: "APP-user-and-access-admin"
title: "User, group and access administration"
parent: "APP-tenant-admin-console"
order: 4
type: "feature"
template: "frontend"
status: "draft"
owner: null
indicative: false
summary: "Tenant admin screens for users, invitations, groups, role assignments at tenant and unit scope, custom roles, access reviews, elevation requests and the access explainer"
links: []
rev: 1
syncHash: "3f5996c1f01fb6f9"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 2.1.2.5.4 User, group and access administration

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Tenant admin screens for users, invitations, groups, role assignments at tenant and unit scope, custom roles, access reviews, elevation requests and the access explainer

<!-- section:scope -->
## Scope, audiences and surfaces

Screens in the tenant admin console ([[APP-tenant-admin-console]]) for managing **who is in the tenant and what they may do**: users (memberships), invitations, groups, role assignments at tenant and unit scope, custom roles and permission sets, access reviews, access requests (just-in-time elevation), and the access explainer. Personas: `user_admin`, `unit_admin` (own unit subtree), `security_admin` (roles, reviews, sessions, MFA resets), `tenant_admin`, `tenant_owner` (owner and admin grants), `auditor` (read-only).

Capability rows are in [[APP-administration-model#design]] section 6.4. Rules referenced here: ADM-R1 to ADM-R6 in [[APP-administration-model]], TM-R6 and TM-R10 in [[MT-tenant-model#rules]].

Concepts shown on these screens:

| Concept | Meaning | Owner node |
|---|---|---|
| User | A membership of a person in this tenant | [[MT-tenant-model]] |
| Group | A named set of users, either managed here (`static`) or synced from the tenant's identity provider (`idp`, read-only membership) | [[PKG-user-provisioning-scim]], [[PKG-authorization-data-model]] |
| Role assignment | Role × scope (tenant or unit subtree) given to a user or a group | [[PKG-roles-and-permission-sets]] |
| Custom role | Bundle of permission sets with optional muted permissions | [[PKG-roles-and-permission-sets]] |
| Case-level role | Role on one case (for example `claimant_counsel`), managed by the secretariat, shown here read-only | [[PKG-rbac-abac-case-level-party]] |

Out of scope: party and counsel invitations to a case (secretariat, [[APP-secretariat-console]]); the bulk import pipeline ([[APP-bulk-admin-operations]]); SCIM configuration ([[PKG-user-provisioning-scim]]); authentication policies ([[PKG-authentication-policies]]).

<!-- section:routing -->
## Routes, layouts and boundaries

```text
app/(tenant-admin)/admin/
  users/                         # table: name, email (masked outside scope), status, roles, units, groups, last sign-in, source (invite | SCIM | intake)
  users/invite/                  # single or multi invite (up to 50 rows; more → bulk import)
  users/invitations/             # pending, expired, bounced; resend, revoke
  users/[membershipId]/
    page.tsx                     # profile tab: identity, units, status, external_ref
    access/                      # role assignments (direct and via groups), case-level roles (read-only), effective permissions summary
    security/                    # MFA status, sessions, sign-in methods, reset MFA, revoke sessions (security_admin)
    activity/                    # this user's admin-relevant audit events (from APP-admin-change-history)
    @modal/(.)end/               # end membership dialog with case-role reassignment list
  groups/  groups/[groupId]/     # members, role assignments, source
  access/
    roles/  roles/[roleId]/      # system roles (read-only), custom roles (draft → publish)
    permission-sets/             # read-only catalogue with descriptions (PKG-permission-catalogue)
    reviews/  reviews/[campaignId]/  reviews/[campaignId]/my-decisions/
    requests/                    # just-in-time elevation requests to approve (PKG-jit-and-break-glass)
    explain/                     # "Can X do Y on Z?" (PKG-access-explainer)
```
Each page calls `requireOp` for its ops; the list is filtered by `authz.where('user.list')` at the active scope.

<!-- section:rendering -->
## Rendering and caching strategy

Dynamic, `private, no-store`. Tables stream the first page from Server Components and then use tRPC with TanStack Query for filtering, sorting and paging. Nothing on these screens is cached across requests, because role changes must be visible immediately; after any `admin.role.*` or `admin.group.*` op the authz decision cache for affected memberships is invalidated in the region within 5 seconds.

<!-- section:data -->
## Data fetching and mutations

| Screen action | Op key | Kind | Notes |
|---|---|---|---|
| Invite | `admin.user.invite` | tRPC mutation | Up to 50 rows inline; role picker shows only assignable roles (ADM-R2); seat-limit check before submit |
| Resend / revoke invitation | `admin.user.invitation_resend` / `_revoke` | tRPC | Multi-select |
| Edit units, locale, external ref | `admin.user.update` | Server Action | If-Match version |
| Suspend / reactivate | `admin.user.suspend` / `.reactivate` | tRPC | Suspend revokes sessions immediately |
| End membership | `admin.user.end` | Server Action | Shows open case-level roles and asks the secretariat (notified) to reassign (TM-R10); blocked for last owner or admin (`last-owner`) |
| Assign / remove role | `admin.role.assign` / `.unassign` | tRPC | Scope picker limited to the admin's own scopes; admin roles create a change set in review (ADM-R4) |
| Group membership | `admin.group.add_member` / `.remove_member` | tRPC | IdP-synced groups are read-only with a link to the IdP |
| Group role assignment | `admin.group.assign_role` | tRPC | Shows the number of users affected before confirming |
| Custom role draft and publish | `admin.role.define` | Server Actions | Versioned; diff shows added and removed permissions; publish is maker-checker; shows how many users the change affects |
| Reset MFA, revoke sessions | `admin.user.reset_mfa`, `.revoke_sessions` | Server Actions | Step-up; user notified by email |
| Start access review | `admin.access_review.run` | Server Action | Campaign: population (all, admins only, a unit, a role), reviewers (manager, unit admin, named), due date; default quarterly for admin roles |
| Record review decision | `admin.access_review.decide` | tRPC | Keep, remove, change; "remove" executes `admin.role.unassign` when the campaign closes, or immediately if configured |
| Approve elevation | `admin.elevation.approve` | Server Action | Time-limited; approver ≠ requester |
| Explain access | `admin.access.explain` | tRPC query | Returns the decision trace: matching role assignments, scope, conditions, denials (ethical walls, stage locks) |

<!-- section:state -->
## Client state and URL state

URL: filters (status, role, unit, group, source, last sign-in before), sort, cursor, selected tab, active scope. TanStack Query keys `['admin', tenantId, scope, 'users', filters]`. Multi-select survives paging within a session (stored in component state, maximum 500 IDs; larger selections offer "select all matching filter", which becomes a bulk job). Drafts of custom roles are server-side versions.

<!-- section:forms -->
## Forms, validation and uploads

- **Invite** form: email or phone (E.164), name, roles with scope, units, locale. Pasting a list of emails creates rows. Duplicate detection against existing memberships and pending invitations in the tenant; the response never reveals memberships in other tenants.
- **Role picker**: grouped as Operational and Administrative; each option shows a one-line description, the scope choices the current admin can give, and "Needs approval" for admin roles.
- **End membership** dialog: reason (required), effective date (now or scheduled), list of open case roles with a "notify secretariat" toggle (default on).
- **Custom role editor**: start from a system role or empty; add permission sets; mute individual permissions; the editor blocks permissions outside the tenant's plan and platform bounds and shows why.
- **Review campaign** form: population, reviewers, due date, reminder cadence, auto-remove on no response (default off).

<!-- section:errors -->
## Error, loading and empty handling

| Error | Shown as |
|---|---|
| `role-escalation-forbidden` | Option disabled with "You can only give roles whose permissions you hold" |
| `last-owner` / `last-admin` | Dialog explaining that another owner or admin must exist first, with a link to add one |
| `entitlement-limit-reached` (seats) | Banner with seat usage "248 of 250 staff seats used" and who can change the plan |
| `approval-required` | Success-style message "Sent for approval to other administrators" with a link to the approval |
| IdP-managed attribute edit | Field read-only with "Managed by your identity provider" |
| Invitation bounced | Row status "Not delivered" with the provider reason category (no raw provider message) |

<!-- section:performance -->
## Performance budgets

Users table: server-side cursor paging, 50 rows default, virtualised; p95 under 1.5 s for filtered queries on a tenant with 500,000 memberships (SEBI ODR institution with parties created at intake), using `membership(tenant_id, status)`, `authz_role_assignment(tenant_id, role_id)` and a trigram index on display name in the people search ([[PKG-search]]). Effective-permission summary on the access tab is computed on demand, p95 under 800 ms.

<!-- section:security -->
## Security headers and browser session

- All actions pass `runAdminOp`; unit admins act only on memberships in their subtree.
- Contact details of users outside the admin's scope are masked; party memberships created by intake show only name, unit and status to `user_admin` (parties are managed by the secretariat on cases).
- Step-up for admin role grants, MFA reset, session revocation, custom role publish and access-review closure that removes admin roles.
- Every privileged grant notifies all tenant owners and the grantee.
- Self-service limits: an admin cannot remove their own last admin role, approve their own request, or review their own access in a campaign (reassigned to another reviewer).

<!-- section:i18n -->
## Localisation hookup

Role and permission-set names and descriptions come from the catalogue with translations; custom role names are tenant-entered per locale. Last sign-in times show in the tenant time zone with relative time ("3 days ago").

<!-- section:theming -->
## Tenant theming hookup

Tenant theme for brand slots; status badges (active, invited, suspended, ended) use semantic status tokens and text, never colour alone ([[PKG-status-and-deadline-badges]]). "Needs approval" and privileged-role markers use locked tokens.

<!-- section:observability -->
## Frontend observability

Metrics: invitations sent, accepted and bounced per day; time to accept; privileged grants per month; access review completion rate and overdue reviewers; elevation requests and approval latency; explainer usage. Alerts to tenant owners (in-app and email) for privileged grants, MFA resets of admins and access-review campaigns overdue by 5 days.

<!-- section:testing -->
## Testing strategy

- Matrix tests per persona: `user_admin` cannot assign admin roles; `unit_admin` sees only its subtree and cannot move users out of it; `auditor` sees everything read-only and no action buttons; `security_admin` can reset MFA but cannot invite.
- Last owner and last admin protections, including through group removal.
- Maker-checker: admin role grant waits for a second admin; the grantee cannot approve.
- End membership lists open case roles and notifies the secretariat.
- IdP-synced group is read-only.
- Access review: decisions applied on close; reviewer cannot review self.
- Explainer: result matches the policy engine decision for a matrix of fixtures.
- Large-tenant performance test at 500,000 memberships.

<!-- section:questions -->
## Open questions

- [ ] Groups as a first-class authorization subject: confirm with the authz group that role assignments to groups are in [[PKG-authorization-data-model]]. (owner: authz group)
- [ ] Should access reviews be required by default for admin roles (quarterly) or only offered? Proposed: on by default for `tenant_owner`, `tenant_admin`, `security_admin`; tenant may switch off with a reason. (owner: security, [[SEC-access-reviews]])
- [ ] Should party memberships created by intake appear in the users list at all, or in a separate "Parties" view? Proposed: separate filter, hidden by default. (owner: product, CORD)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation in rendering and caching

Every query runs in the session tenant under forced RLS; unit scope is an additional authz filter; invitations never reveal memberships in other tenants; two-tenant diff tests on the users, groups and roles pages.

<!-- check:data-exposure -->
### Server boundary and data exposure

Admin roles see membership data, never case content; contact details are masked outside the admin's scope; case-level roles are shown as role and case reference only; effective-permission summaries list permission names, not resource contents.

<!-- check:session -->
### Sessions in the browser

Step-up for privileged grants, MFA resets and session revocation; revoking a user's sessions takes effect within 30 seconds across the region.

<!-- check:resilience -->
### Failure, deploys and version skew

Mutations are idempotent with If-Match; large selections become bulk jobs that continue server-side; a failed role assignment leaves no partial state (single transaction with audit).

<!-- check:capacity -->
### Rendering cost and capacity

Designed for 500,000 memberships per tenant with indexed filters and cursor paging; effective permissions computed on demand rather than for every row.

<!-- check:accessibility -->
### App-level accessibility mechanics

Tables follow [[PKG-data-table]] (sortable headers, row selection with keyboard, live-region announcements of result counts); the role picker is an accessible combobox ([[PKG-combobox-and-people-picker]]); dialogs follow [[PKG-modal-dialog-and-consequential]].

<!-- end -->
