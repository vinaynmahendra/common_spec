---
id: "PKG-user-provisioning-scim"
title: "User provisioning: SCIM, JIT, invitations and deprovisioning"
parent: "PKG-authentication"
order: 8
type: "feature"
template: "integration"
status: "draft"
owner: null
indicative: false
summary: "All ways people enter, move within and leave a tenant: staff and case invitations, bulk import, SCIM 2.0 service provider per region, JIT on SSO, domain auto-join, group-to-role mappings, durable deprovisioning with reassignment, and daily reconciliation"
links: []
rev: 1
syncHash: "cfe0d17d0c4427dd"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.1.8 User provisioning: SCIM, JIT, invitations and deprovisioning

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> All ways people enter, move within and leave a tenant: staff and case invitations, bulk import, SCIM 2.0 service provider per region, JIT on SSO, domain auto-join, group-to-role mappings, durable deprovisioning with reassignment, and daily reconciliation

<!-- section:purpose -->
## Purpose and use cases

How people get into a tenant's directory, change role, and leave it, through five channels that all end in the same records (`user_account`, `membership`, `authz_role_assignment`, `membership_org_unit`, `invitation` in [[MT-tenancy-and-identity-schema]]):

| Channel | Who uses it | Typical tenant | Creates |
|---|---|---|---|
| **Staff invitation** (console or [[INT-tenant-admin-api]]) | `user_admin`, `tenant_admin` | All | Invited membership with tenant roles |
| **Bulk import** (CSV / XLSX, [[APP-bulk-admin-operations]]) | `user_admin` | Onboarding of a new institution | Invitations in a batch, dry-run first |
| **SCIM 2.0 push** from the tenant's IdP (RFC 7643 / 7644) [R1][R2] | The tenant's IdP (Entra ID, Okta, others) | Large institutions, courts | Active memberships; deactivation and group changes |
| **Just-in-time (JIT) on SSO sign-in** | Users of a verified domain | Institutions without SCIM | Membership with a default non-administrative role |
| **Case participant invitation** | `secretariat` / `case_manager` | All | External membership plus case role ([[PKG-external-party-identity]]) |
| **Domain auto-join** (`auth.domains.auto_join`) | Users with a verified-domain email | Firms and institutions | Pending or active membership ([[PKG-domain-verification]]) |

Use cases:
1. An institution's IT team assigns the "Nomology – Secretariat" group in Entra ID; SCIM creates and activates the membership with role `secretariat` in unit "Singapore office" before the person's first day.
2. A case manager leaves; IdP deactivation suspends the membership within 60 seconds, ends sessions and opens reassignment tasks for their open cases.
3. A neutral moves from the domestic panel to the international panel; a group change moves their unit membership without touching their case appointments.
4. A tenant without SCIM gets a daily stale-account report and a quarterly access review instead.

Not here: role design (that is [[PKG-roles-and-permission-sets]]); permissions granted by roles; service accounts ([[PKG-non-human-principals]]).

<!-- section:party -->
## External party and ownership

| Item | Detail |
|---|---|
| External party | The tenant's identity provider. Tested and documented profiles: Microsoft Entra ID provisioning [R3] and Okta provisioning; any SCIM 2.0 client that passes our conformance suite is accepted |
| Contract owner | The tenant (the IdP is theirs); Nomology owns the SCIM service provider endpoint. No Nomology contract with the IdP vendor |
| Our owner | Identity team (`packages/auth/provisioning`); on-call: platform security |
| Tenant contacts | `security_admin` named on the SCIM connection; alerts go to `auth.admin.alert_recipients` |
| Environments | Per region: `https://api.{region}.<product-domain>/scim/v2/` (region `in`, `sg` or `us`) in production and `https://api.{region}.sandbox.<product-domain>/scim/v2/` for the tenant sandbox ([[PKG-configuration-lifecycle]]); the tenant is identified by the bearer token, never by the URL |
| Plan | SCIM requires the `enterprise` plan (`auth.provisioning.scim_enabled`); JIT and invitations are on all plans |

<!-- section:flows -->
## Data flows

**F1. SCIM create user** (IdP → us, synchronous)
```
IdP POST /scim/v2/Users  (Authorization: Bearer nscim_in_…)
  → edge → scim route handler (app/api/scim/v2/[...path]/route.ts)
  → token → scim_connection → tenant context transaction (RLS)
  → find user_account by verified email in region; create if absent (status active, email_verified_at = now, source 'scim')
  → upsert membership (status active) + scim_resource_link(externalId, scim id)
  → apply group mappings (if groups already known)
  → outbox: identity.membership.provisioned; audit admin.user.provisioned
  ← 201 with SCIM User representation (id = scim resource id, not our membership UUID)
```
**F2. SCIM update** — `PATCH /Users/{id}` with `Operations` (`add`, `replace`, `remove`) [R2]; `PUT` accepted for clients that only send full replacement. Attributes mastered by the IdP become read-only in the console for that membership (`source_of_authority = idp`).

**F3. SCIM deactivate / delete**
- `PATCH active=false` → membership `suspended` (default `auth.provisioning.deprovision_action = suspend`), revocation version bumped (sessions end ≤ 60 s, [[PKG-mfa-session-management-device]]), API credentials owned by the person are disabled ([[PKG-api-clients-and-keys]]), and Temporal workflow `{tenantId}-deprovision-{membershipId}` starts.
- `DELETE /Users/{id}` → same, then membership `ended`. The `user_account` is never deleted by SCIM (it may hold memberships in other tenants); personal data follows [[PKG-data-retention-legal-hold-and]].
- Deprovision workflow activities: `listOpenAssignments` (cases, human tasks, hearings, drafts), `createReassignmentTasks` for the unit's `secretariat` lead ([[WF-human-tasks]]), `transferOwnership` of saved reports and automation rules to a named owner, `notifyCaseParticipants` only where a case role changes (procedural notice rules apply), and timer `auth.provisioning.suspended_to_ended_days` → end membership.
- Neutral appointments are never removed automatically: a deactivated neutral with open appointments raises a high-priority task to the case manager, because removing a tribunal member is a procedural act.

**F4. SCIM groups** — `POST/PATCH /Groups` stores the IdP group and members (`scim_group`, `scim_group_member`). Groups grant nothing by themselves; **group mappings** (`group_role_mapping`: group → role keys, unit, optional expiry), maintained by `security_admin` in the console, translate membership into `authz_role_assignment` rows. A mapping that grants an administrative role needs maker-checker ([[PKG-separation-of-duties]]).

**F5. JIT on SSO sign-in** (when `auth.provisioning.jit_enabled`) — after a valid assertion from a connection with JIT allowed, for an email on a domain verified for that connection ([[PKG-domain-verification]]): create membership with `auth.provisioning.jit_default_role` (never administrative) and unit from a mapped attribute; group claims in the assertion are mapped with the same `group_role_mapping` table. JIT never reactivates a `suspended` or `ended` membership.

**F6. Invitations** — `invitation` row with SHA-256 token hash; email via [[PKG-notifications]] class `auth`; link `/invite/{token}` on the tenant host ([[APP-public-and-sign-in-surfaces]]). Acceptance requires sign-in or account creation with the invited email when `auth.invitations.require_email_match` is true; otherwise acceptance with another verified email needs approval by the inviter. Expiry: `auth.invitations.staff_ttl_days` (staff) or `auth.invitations.case_participant_ttl_days`; resend issues a new token and revokes the old one. Invitations to administrative roles need step-up by the inviter.

**F7. Lifecycle events (joiner / mover / leaver)**

| Membership state | Entered by | Leaves to |
|---|---|---|
| `invited` | Invitation, bulk import, auto-join `suggest` | `active` (accepted), `ended` (revoked or expired) |
| `active` | Acceptance, SCIM create, JIT, auto-join `automatic` | `suspended` (admin, SCIM `active=false`, stale rule), `ended` |
| `suspended` | As above; tenant suspension | `active` (admin or SCIM reactivation), `ended` (timer or admin) |
| `ended` | Admin, SCIM DELETE, timer | Terminal; a returning person gets a new membership linked to the old one |

**F8. Reconciliation** — BullMQ job `identity-provisioning:reconcile` daily per tenant: lists memberships with `source_of_authority = idp` not touched by SCIM in 30 days, staff with no sign-in for `auth.provisioning.stale_account_days`, invitations past expiry; produces a report and review tasks. Pattern borrowed from: joiner/mover/leaver lifecycle automation common in workforce identity platforms.

<!-- section:mapping -->
## Data mapping

Core User schema `urn:ietf:params:scim:schemas:core:2.0:User` [R1], enterprise extension `urn:ietf:params:scim:schemas:extension:enterprise:2.0:User`, and our extension `urn:nomology:params:scim:schemas:extension:tenant:1.0:User`.

| SCIM attribute | Our field | Rule | Class |
|---|---|---|---|
| `id` | `scim_resource_link.scim_id` | Generated by us, opaque, stable; not the membership UUID | Internal |
| `externalId` | `scim_resource_link.external_id` | Unique per SCIM connection; used for matching on re-sync | Internal |
| `userName` | Lookup key; stored as `user_identity` subject for the connection | Must be an email on a domain verified for this tenant; otherwise `400 invalidValue` | Personal |
| `emails[primary eq true].value` | `user_account.primary_email` | Only set on create; a change on an existing user creates a pending email change verified by the user (prevents takeover by IdP mis-edit) | Personal |
| `name.givenName`, `name.familyName`, `displayName` | `user_account.display_name` | Updated when `source_of_authority = idp` | Personal |
| `phoneNumbers[type eq "mobile"]` | Pending phone (user must verify before OTP use) | Never auto-verified | Personal |
| `active` | `membership.status` | `false` → `suspended`; `true` reactivates only a `suspended` membership | Internal |
| `locale`, `timezone` | `user_account.locale`, `time_zone` | Defaults only; the user can override | Personal |
| enterprise `employeeNumber`, `department` | `membership.attributes` (jsonb, max 2 KB) | Usable in ABAC conditions ([[PKG-rbac-abac-case-level-party]]) | Personal |
| enterprise `manager.value` | Not stored at launch | — | — |
| extension `unitCodes` | `membership_org_unit` via `org_unit.code` | Unknown code → `400 invalidValue`, no partial write | Internal |
| `groups` (read-only on User) | Derived from `scim_group_member` | — | Internal |
| `password` | Rejected | `400 mutability`; we never accept passwords by SCIM | — |
| `roles`, `entitlements` | Not accepted | Roles come only from group mappings | — |

Group resource: `displayName` → `scim_group.display_name`; `members[].value` → SCIM user IDs; `externalId` as above.

Discovery endpoints: `/ServiceProviderConfig` (patch true, bulk false at launch, filter true with `maxResults` 200, changePassword false, sort false, etag true, authenticationSchemes oauthbearertoken), `/ResourceTypes`, `/Schemas`.

<!-- section:auth -->
## Authentication and secrets

- **Inbound (IdP → us)**: one SCIM connection per tenant (tenants on `enterprise` may have up to 3, for example two IdPs during a migration). Each has a bearer token `nscim_{region}_{32 random base62}`; only a SHA-256 hash and 12-character prefix are stored; shown once; lifetime ≤ `auth.scim.token_max_days`; rotation creates a second active token with 7-day overlap. Created only by a human `security_admin` in the console with `strength.phishing_resistant` step-up (never via the admin API, mirroring API client creation in [[INT-tenant-admin-api]]).
- Optional: OAuth 2.0 client credentials with `private_key_jwt` instead of a static token, for IdPs that support it; optional IP allow-list per connection.
- The token is bound to one tenant and region and can only call `/scim/v2/*`; its principal is an `integration_connection` ([[PKG-non-human-principals]]) holding permission set `ps.identity.scim_provisioner` (`user:create`, `user:update` (profile and membership status), `group:update`) and nothing else; it cannot grant roles directly.
- Key prefix format allows secret-scanning partners to detect leaked tokens; a reported leak revokes the token and alerts the tenant.
- **Outbound**: none. JIT uses the SSO connection's trust ([[PKG-sso-saml-oidc-per-tenant]]).

<!-- section:errors -->
## Errors, retries and idempotency

SCIM errors use `urn:ietf:params:scim:api:messages:2.0:Error` with HTTP status and `scimType` [R2]:

| Case | Status / `scimType` | Behaviour |
|---|---|---|
| Duplicate `userName` or `externalId` in this connection | 409 `uniqueness` | IdP should match instead; our filter `userName eq` supports it |
| Email domain not verified for tenant | 400 `invalidValue` | Admin alert once per day per domain |
| Unknown unit code | 400 `invalidValue` | No partial write |
| Unsupported filter | 400 `invalidFilter` | Supported: `eq` on `userName`, `externalId`, `emails.value`, `displayName` (Groups); `and` |
| PATCH path invalid | 400 `invalidPath` / `noTarget` | |
| Attempt to set `password`, `roles` | 400 `mutability` | |
| Membership `ended` and IdP sends `active=true` | 409 with detail "ended membership cannot be reactivated; create new" | |
| Tenant suspended | 403 | Writes rejected; reads allowed for reconciliation |
| Rate limit | 429 with `Retry-After` | |
| Server error | 500 / 503 | IdP retries per its own policy |

Idempotency: SCIM create is matched by `externalId` then `userName`; a retried create for an existing link returns 409, which Entra and Okta treat as "match". PATCH operations are applied in a single transaction; `ETag` / `If-Match` supported (`version` column). Out-of-order delivery: each operation carries no sequence, so we apply last-write-wins per attribute and record `scim_last_seen_at`; a deactivation arriving before the create is stored as a tombstone link so a late create does not activate the user.

Side effects (session revocation, deprovision workflow, notifications) are dispatched after commit through the outbox to BullMQ queue `identity-provisioning` (retries 5 with exponential backoff, dead-letter `identity-provisioning-dlq` with an alert).

<!-- section:limits -->
## Rate limits and SLAs

| Limit | Value | Reason |
|---|---|---|
| Requests per SCIM connection | 25 per second sustained, burst 100 ([[PKG-input-sanitisation-csrf-rate]]) | Initial syncs of 5,000+ users finish in minutes |
| Page size | default 100, max 200 | |
| Group size in one PATCH | 1,000 members per request | Larger groups must be paged by the IdP |
| Expected volume | Largest institution tenants: about 2,000 staff and panel members; daily churn < 1 % | |
| Latency target | p95 < 400 ms per write excluding side effects | |
| Deactivation to session end | ≤ 60 seconds | [[PKG-authentication]] AUTH-FR-8 |
| Our availability | Same SLO as the regional admin API ([[OBS-performance]]) | IdPs retry, so short outages self-heal |

<!-- section:residency -->
## Data transfer and compliance

The SCIM endpoint is served by the tenant's home region only; a token presented in another region is rejected with 401 (the prefix carries the region so the edge can route). Personal data received (names, emails, phone, department) is stored only in the regional database. The IdP is chosen and operated by the tenant; data flows from the tenant's IdP to us, so the tenant is the data fiduciary / controller for workforce data, and Nomology processes it under the DPA. Assumption: no cross-border transfer by Nomology arises from SCIM because we do not send data back to the IdP beyond echoing what it sent; legal to confirm for tenants whose IdP tenant is hosted outside the home region.

<!-- section:testing -->
## Sandbox and testing

- **Conformance suite** in CI (`packages/auth/provisioning/test/scim-conformance`): RFC 7644 operations, filters, PATCH semantics (including Entra's non-standard `replace` with a value object and string booleans `"False"`), ETags, errors and discovery documents; based on published SCIM validator behaviour for Entra ID [R3].
- **Tenant sandbox**: each tenant sandbox exposes its own SCIM endpoint with a separate token, so IT teams can test provisioning against masked data before production.
- **Cross-tenant test**: a token from tenant A cannot read or write tenant B users; `userName` on a domain verified only in B is rejected in A.
- **Deprovision E2E**: deactivate in a test IdP (Keycloak in docker-compose with a SCIM client) → sessions rejected within 60 seconds → reassignment tasks created.
- **Load test**: initial sync of 10,000 users and 200 groups within 15 minutes per region ([[TST-performance-and-load-testing]]).

<!-- section:questions -->
## Open questions

- [ ] Is SCIM `/Bulk` needed for any launch tenant, or are paged creates enough? (Product)
- [ ] Should group mappings support case-type restrictions (for example "SEBI desk group" can only see SEBI case types) or should that stay in ABAC rules? (Security, with authz group)
- [ ] Do any institutions need SCIM provisioning of panel neutrals from their own directory, given neutrals are often external people? (Product)
- [ ] Outbound SCIM (us pushing to a tenant's HR or IdP) — any demand? Proposed: out of scope. (Product)
- [ ] Legal basis and notice for processing workforce data received by SCIM in India under DPDP: tenant as data fiduciary, Nomology as processor — confirm DPA wording. (Legal)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant separation at the provider

The SCIM token resolves to exactly one `scim_connection` and tenant before any processing; every read and write runs inside a tenant-context transaction with forced RLS. `user_account` is region-level, so a person provisioned by two tenants has one account and two memberships, and each tenant's SCIM view shows only its own membership and its own `scim_resource_link` IDs; `userName` must be on a domain verified for the calling tenant.

<!-- check:security -->
### Security

Tokens are hashed, shown once, expiring and rotatable with overlap; creation requires a human `security_admin` with phishing-resistant step-up. The provisioner principal can create and update users and group memberships but cannot assign roles directly, cannot set passwords, and cannot touch administrative mappings, which need maker-checker. Email changes from the IdP do not take effect until the user verifies the new address.

<!-- check:residency -->
### Data transfer and residency

Endpoint and storage are regional; no data is sent back to the IdP except responses to its own requests. Workforce data stays in the tenant's region (see residency section; one assumption for IdPs hosted in another country).

<!-- check:vendor -->
### Vendor risk and exit

No vendor is engaged by Nomology: the IdP belongs to the tenant, which carries its risk. Our exposure is behavioural drift in IdP SCIM clients (non-standard PATCH forms); the conformance suite covers known quirks and SCIM is an open standard (RFC 7643 / 7644), so a tenant can switch IdP by re-pointing provisioning, with `externalId` re-matching on `userName` and no data loss.

<!-- check:resilience -->
### Failure handling and degradation

IdPs retry on 5xx and 429, so our outages self-heal; side effects run through the outbox and BullMQ with a dead-letter queue. Deprovisioning is durable in Temporal, so a worker crash does not leave an ended person with open tasks unassigned. If SCIM stops calling (IdP misconfigured), reconciliation flags memberships not seen for 30 days.

<!-- check:consistency -->
### Consistency and reconciliation

The IdP is the source of truth for attributes and active status of memberships with `source_of_authority = idp`; the platform is the source of truth for roles (via mappings), case assignments and everything procedural. Daily reconciliation reports drift; the tenant can trigger a full re-sync from its IdP, and our idempotent matching on `externalId` makes re-sync safe.

<!-- check:audit -->
### Audit and evidence

Each SCIM operation writes an audit event (`admin.user.provisioned`, `.updated`, `.deprovisioned`, `admin.group.updated`, `admin.group_mapping.updated`) with the connection ID, the IdP request ID header if sent, attribute names changed (not values for personal fields beyond a hash) and the resulting state. This proves who removed a case manager's access and when, which matters if a later act on a case is challenged.

<!-- check:observability -->
### Observability

Metrics per tenant and connection: requests, error rate by `scimType`, latency, last successful call. Alerts: error rate > 20 % for 15 minutes, no calls for 7 days on a connection that used to sync daily, dead-letter queue depth > 0, deactivation-to-revocation latency > 60 s.

<!-- check:testing -->
### Testing

Conformance suite against our endpoint in CI, Keycloak-based E2E for deprovisioning, tenant sandboxes for customer testing with masked data, and a scheduled weekly run of the suite against staging to catch regressions from IdP behaviour changes reported by tenants.

<!-- citations -->
## Citations

```json
[
  {
    "body": "IETF",
    "id": "R1",
    "ident": "RFC 7643",
    "kind": "standard",
    "title": "System for Cross-domain Identity Management: Core Schema",
    "url": "https://www.rfc-editor.org/rfc/rfc7643"
  },
  {
    "body": "IETF",
    "id": "R2",
    "ident": "RFC 7644",
    "kind": "standard",
    "title": "System for Cross-domain Identity Management: Protocol",
    "url": "https://www.rfc-editor.org/rfc/rfc7644"
  },
  {
    "body": "Microsoft",
    "id": "R3",
    "kind": "vendor",
    "title": "Microsoft Entra: Develop and plan provisioning for a SCIM endpoint",
    "url": "https://learn.microsoft.com/en-us/entra/identity/app-provisioning/use-scim-to-provision-users-and-groups"
  }
]
```

<!-- end -->
