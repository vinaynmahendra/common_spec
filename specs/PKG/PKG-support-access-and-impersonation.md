---
id: "PKG-support-access-and-impersonation"
title: "Support access and impersonation"
parent: "PKG-authorization"
order: 4
type: "feature"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "Consent-based, time-limited support access to tenant data and read-only 'view as', with tenant consent modes, request expiry, scoped write grants and tenant-visible audit"
links: []
rev: 3
syncHash: "7ff751d389499b74"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.2.4 Support access and impersonation

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Consent-based, time-limited support access to tenant data and read-only 'view as', with tenant consent modes, request expiry, scoped write grants and tenant-visible audit

<!-- section:purpose -->
## Purpose and scope

Lets Nomology support and engineering staff help a tenant without standing access to its data. Access is requested for a reason, consented to by the tenant (according to the tenant's chosen consent mode, or in a declared emergency by two Nomology approvers with prompt notice to the tenant), limited in scope and time, and every action taken is recorded in the tenant's own audit trail where the tenant can see it. "View as" lets staff see the product as a specific user sees it, read-only.

Protects tenant and case confidentiality from insiders and from compromised staff accounts, and gives institutions the evidence they need for their own audits. Pattern borrowed from: customer-approved, time-boxed engineer access requests in Microsoft Purview Customer Lockbox [R3] (requests expire if not approved; access is revoked automatically at the end of the approved period; approvals and operator actions are audited).

Relationships:
- Emergency elevation mechanics (approval, paging, review) are owned by [[PKG-jit-and-break-glass]]; this node defines only the `break_glass` grant type's effect inside a tenant and the tenant notification.
- Consoles: staff request and use grants in [[APP-platform-admin-and-support]]; tenants approve, configure consent and review activity in [[APP-tenant-admin-console]] (`/admin/security/support-access`) and [[APP-admin-change-history]].
- Settings: platform bounds `platform.support.*` are catalogued in [[PKG-settings-platform-operations]]; tenant consent settings `access.support.*` are catalogued in [[PKG-settings-access-control]] (decision D9).
- Tenant administrators do **not** get live impersonation of their own users. To answer "what can this user see?", they use the permission simulator in [[PKG-access-explainer]], which evaluates policy without opening a session as the user.

<!-- section:assets -->
## Protected assets

| Asset | Classification ([[SEC-data-classification]]) |
|---|---|
| Tenant configuration (settings, rules, templates, blueprints) and user lists (names, roles, status) | Tenant-internal |
| Case content (pleadings, evidence, transcripts) | Case participants |
| Tribunal-only material (award drafts, deliberations) | Tribunal-only (never in any grant) |
| Personal contact data of users and parties | Personal; masked under every grant type except `case_read` on named cases |
| Support grants, sessions and their audit trail | Internal (tenant-visible) |
| Ability to change tenant configuration | Tenant-internal, high impact |

<!-- section:actors -->
## Actors and roles

| Actor | Role key | How acquired | Interaction |
|---|---|---|---|
| Support engineer (tier 1, tier 2) | `platform_support` | Workforce IdP group | Requests grants with ticket, reason, scope and duration; uses own grants only |
| Regional operations / on-call | `regional_ops` | Workforce IdP group | Requests incident grants and break-glass |
| Platform security | `platform_security` | Workforce IdP group | Second approver for break-glass; weekly review of all grants |
| Tenant security admin | `security_admin` | Tenant role | Approves, rejects, revokes; sets consent mode |
| Tenant owner | `tenant_owner` | Tenant role | Same as security admin; only role that can enable standing consent |
| Tenant-designated approver | any tenant member named in `access.support.case_content_approvers` | Tenant setting | Additional approver for `case_read` grants (for example registrar or secretariat lead) |
| Auditor | `auditor` | Tenant role | Reads support activity |
| Impersonated user | any | — | Receives an in-app notice after a view-as session (tenant setting `access.support.notify_impersonated_user`, default on) |

<!-- section:matrix -->
## Permission matrix

**Consent modes** (tenant setting `access.support.consent_mode`, changed only by `tenant_owner` with step-up):

| Mode | Meaning | Default for |
|---|---|---|
| `per_request` | Every grant needs approval by a tenant approver | All tenant types |
| `standing_config_read` | `config_read` grants up to the platform maximum are auto-approved (recorded and notified); every other type needs approval | Opt-in only, where the contract allows |
| `deny_all_except_break_glass` | Only break-glass is possible; normal support works from screenshots and logs | Opt-in for courts or government programmes that require it |

**Grant types**

| Grant type | Allows | Never allows | Max duration (platform bound) | Approval |
|---|---|---|---|---|
| `config_read` | Tenant settings, blueprints, rules, templates, user list (names masked to initials unless tenant opts in), integration status, job and workflow status | Case content, documents, messages, audit export | 8 h | Tenant approver, or standing consent |
| `config_write` | The admin ops listed in the request (for example "republish theme", "fix SSO attribute mapping"), each executed through `runAdminOp` with `via=support` | Case content; any role grant; support-access settings; data export; deletion; legal texts | 4 h | Tenant approver per request; maker-checker ops still need the tenant's second approver |
| `case_read` | Listed case IDs: metadata and documents of tier `case_participants` | Tribunal-only and institution-internal unless named and approved by the designated approver; any write; download | 8 h | Tenant approver plus designated approver |
| `impersonate_readonly` | View the UI as one named user, read-only | Any write, consequential action, notification send, read-receipt or last-seen change, download of tribunal-only material | 2 h | Tenant approver |
| `break_glass` | As `case_read` or `config_write` for incident containment | Award signing, filing, payments, deletion | 2 h | Two platform approvers ([[PKG-jit-and-break-glass]]); tenant notified at once (and in any case within the contract period) |

**Who can do what**

| Action | Support engineer | Regional ops | Platform security | Tenant owner | Security admin | Designated approver | Auditor | Impersonated user |
|---|---|---|---|---|---|---|---|---|
| Request grant | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Approve / reject | ✗ | ✗ | break-glass second approver | ✓ | ✓ | ✓ case-content only | ✗ | ✗ |
| Use grant | requester only | requester only | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Extend grant | ✗ (new request) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Revoke grant | own | own | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| Change consent mode | ✗ | ✗ | ✗ | ✓ | ✗ (view) | ✗ | ✗ | ✗ |
| View support activity | own | own | ✓ all in region | ✓ | ✓ | ✓ | ✓ | own sessions only |

<!-- section:policy -->
## Policy model

- Support staff authenticate only through the workforce IdP with WebAuthn; their principal has no tenant membership. A grant adds a constrained context `{ supportGrantId, tenantId, type, caseIds?, impersonateUserId?, allowedOps?, expiresAt }`.
- **Request**: `platform.support.request` creates `support_grant` in state `requested` with ticket reference, reason, type, scope and requested duration (≤ platform maximum `platform.support.max_duration_min.<type>`). The tenant is notified in the console and by email to approvers.
- **Request expiry**: a request not approved within `platform.support.request_expiry_hours` (default 12 h) expires; no access is granted.
- **Approval**: needs step-up; the approver sees the exact scope, duration, requester and ticket. Approvers may shorten, never lengthen. Scope is fixed at approval; any change needs a new request.
- **States**: `requested → approved → active → ended` (`ended` by expiry, revoke, idle timeout or session end), or `requested → rejected | expired`. Code-defined state machine ([[WF-entity-state-machines]]).
- **Evaluation** under a grant: every `authz` decision first checks the grant constraints (type, case list, op allow list, expiry, host tenant equals grant tenant), then the normal policy as if the principal were the impersonated user (for `impersonate_readonly`) or a read-only viewer with the grant's scope. Writes are denied unless the grant type is `config_write` or `break_glass` and the op is in `allowedOps`.
- The UI shows a persistent banner in a fixed platform colour: "Support session · {type} · read only · expires 14:30 · grant SG-0142".
- Sessions end at expiry, on revoke (within 30 seconds through session revocation), or after `platform.support.session_idle_min` (default 30) minutes idle.
- **Impersonation side effects are suppressed**: no notification sends, no read markers, no last-seen updates, no AI usage billed to the user, no consent or declaration acceptance.
- Weekly review by platform security of all grants and their activity; weekly summary to tenant security admins (`access.support.weekly_report`, default on).

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|---|
| T1 | E | Staff with no grant reads data via internal tools (DB console, Temporal UI) | Production database access only via break-glass bastion with session recording; Temporal payloads encrypted, Codec Server decrypts only under a grant ([[WF-separation-of-concerns-temporal#guardrails]]) | Medium (insider with infrastructure access) |
| T2 | E | Grant scope creep | Scope fixed at approval; changes need a new grant; `allowedOps` enforced by the dispatcher | Low |
| T3 | S | Compromised staff account uses an approved grant | WebAuthn, short duration, IP allow-list for the support console, anomaly alerts | Low |
| T4 | R | Tenant disputes what support did | Every action in tenant's audit with `actor.type = support`, grant ID and `via=support` | Low |
| T5 | I | Impersonation triggers notifications or read receipts as the user | Side effects suppressed (policy section); tests generated from the op catalogue | Low |
| T6 | E | Support uses `config_write` to grant itself or a colleague a tenant role | Role grants and support-access settings excluded from every grant type | Low |
| T7 | S | Social engineering: attacker asks tenant approver to approve a fake request | Requests originate only from the platform console and show in the tenant console; email links open the console, never approve directly | Low |
| T8 | I | Standing consent becomes de facto standing access | Only `config_read`, only with owner opt-in, still time-limited per grant, every grant listed in weekly report | Low |
| T9 | E | Approved request used long after approval | Access starts at approval and expires at the approved end; no deferred start in v1 | Low |

<!-- section:failure -->
## Denial behaviour

Actions outside the grant return 403 `support_scope_exceeded` (support staff are not end users, so a clear reason is shown) and are audited as denied. Expired or revoked grants end the session with a message to request a new grant. If the grant store cannot be read, all support access is denied (fail closed). Tenant approvers who try to approve an expired request see "This request has expired; ask Nomology support to send a new one".

<!-- section:requirements -->
## Security requirements

ASVS references are to OWASP ASVS **5.0** at section level [R1][R2]; requirement-level IDs to be added after checking against the 5.0.0 text.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| SUP-1 | Platform staff shall have no access to tenant data without an active, approved grant. | V8.2 |
| SUP-2 | Grants shall have a type, scope, reason, ticket reference, requester, approver and an expiry no longer than the platform maximum for the type. | V8.1 |
| SUP-3 | Every action under a grant shall be recorded in the tenant's audit trail and shown on the tenant's support activity page. | V16.3 |
| SUP-4 | Impersonation shall be read-only and shall not send notifications, change read state or record acceptances. | V8.3 |
| SUP-5 | Break-glass grants shall require two platform approvers and notify the tenant. | V8.1 |
| SUP-6 | A request not approved within the configured expiry shall expire without granting access. | V8.1 |
| SUP-7 | The tenant consent mode shall be changeable only by a `tenant_owner` with step-up and shall be audited as `admin.support.consent_mode_changed`. | V8.1 |
| SUP-8 | No grant type shall permit role grants, support-access configuration, data export, deletion or tribunal-only material. | V8.2 |
| SUP-9 | Revocation shall end active support sessions within 30 seconds. | V7.4 |
| SUP-10 | Writes under `config_write` shall execute through the same admin operation as a tenant admin would, including the tenant's maker-checker rules. | V8.2 |

Acceptance (examples):
- Given a tenant in `per_request` mode, when support requests `config_read` and no approver acts within 12 hours, then the request becomes `expired` and the support engineer cannot open a session.
- Given an active `impersonate_readonly` grant, when the engineer opens a case the user can see, then the page renders read-only and no `notification.*` or `read_marker.*` write occurs.
- Given an active `config_write` grant allowing `admin.theme.publish`, when the engineer tries `admin.role.assign`, then the response is `403 support_scope_exceeded` and an `authz.denied` event is in the tenant audit.

<!-- section:verification -->
## Verification

Tests: no grant → denied on all tenant reads; each grant type allowed/denied on its list; impersonation cannot call any write op (generated from the admin operation registry and the domain action catalogue); `config_write` limited to `allowedOps`; request expiry; approval shortening; expiry, revoke and idle timeouts; consent modes (`standing_config_read` auto-approval, `deny_all_except_break_glass`); break-glass requires two distinct approvers. Quarterly test of the tenant notification path. Pen-test scope includes grant tampering and cross-tenant use of a grant on another tenant's host.

<!-- section:questions -->
## Open questions

- [ ] Tenant notification time for break-glass: immediate notification is proposed; contracts with institutions may set a maximum (24 h was the earlier proposal). Legal / account management to confirm.
- [ ] Standing consent for `config_read`: offered in the standard contract or opt-in? Proposed: opt-in by `tenant_owner`. Owner: legal.
- [ ] Session recording (screen) for support sessions on case content: needed, and where stored (in region)? Owner: security.
- [ ] Should a deferred start time be allowed (approve now for a maintenance window tonight)? Proposed: not in v1. Owner: product.
- [ ] Assisted write actions while impersonating ("act as" with the user present) for stuck filings: proposed not in v1; reconsider after 6 months of support data. Owner: security with tenants.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Staff have no tenant membership; a grant is bound to one tenant and validated against the host tenant on every request; all reads under a grant run in that tenant's RLS context. Grants, sessions and their audit events live in the tenant's region.

<!-- check:enforcement -->
### Enforcement points and bypass paths

The grant context is checked in `@nomology/authz` before any policy, so it applies to Server Components, Server Actions, tRPC, Route Handlers, signed URL issue, search, exports and AI retrieval alike; writes additionally pass through `runAdminOp`, which rejects ops outside `allowedOps`. Internal tools (database, Temporal UI, Codec Server) are covered by T1 controls.

<!-- check:lifecycle -->
### Grant lifecycle and privileged access

Grants are requested with reason, ticket and scope; expire if not approved in 12 h; are approved by the tenant per consent mode (two platform approvers for break-glass); start at approval and expire automatically (2–8 h by type); can be shortened at approval and revoked by either side; are never extended; and are reviewed weekly by platform security.

<!-- check:resilience -->
### Failure modes and secrets

If the grant store, the authz service or session revocation fails, support access is denied; the platform console shows a clear error. A compromised support account is contained by short grant durations, WebAuthn, IP allow-list and immediate revoke.

<!-- check:audit -->
### Audit trail

Grant request, approval, rejection, expiry, use, end and revocation, consent-mode changes and every action under a grant go to the tenant's audit stream with `actor.type = support`, `via=support` and the grant ID, and to the platform audit stream; the tenant admin console has a support activity page built from these events ([[APP-admin-change-history]]).

<!-- check:observability -->
### Detection and alerting

Alerts: any break-glass grant (security on-call and tenant security admins), more than 3 grants per engineer per day, any denied action under a grant (possible probing), use of a grant from an IP outside the support allow-list, standing-consent grants above 5 per tenant per week.

<!-- check:compliance -->
### Framework and legal mapping

Supports ISO 27001:2022 Annex A 8.2 (privileged access rights) and 5.18 (access rights), SOC 2 CC6.2 and CC6.3, and client audit-rights clauses. Evidence: grant register export, weekly tenant reports and tenant-visible activity. For DPDP and GDPR, support access is processing by Nomology as processor on the tenant's instructions; the consent mode records those instructions (assumption: to be confirmed by legal for each tenant contract).

<!-- check:testing -->
### Verification and testing

Every cell of the grant-type and action tables has generated allow and deny tests; impersonation write-suppression tests are generated from the op registry; consent-mode tests cover all three modes; break-glass tests require two distinct approvers.

<!-- citations -->
## Citations

```json
[
  {
    "body": "OWASP",
    "id": "R1",
    "ident": "ASVS",
    "kind": "standard",
    "title": "OWASP Application Security Verification Standard",
    "url": "https://owasp.org/www-project-application-security-verification-standard",
    "version": "5.0"
  },
  {
    "body": "OWASP",
    "id": "R2",
    "ident": "ASVS",
    "kind": "standard",
    "title": "OWASP Cheat Sheet Series: ASVS 5.0 index (chapter and section titles)",
    "url": "https://cheatsheetseries.owasp.org/IndexASVS.html",
    "version": "5.0.x"
  },
  {
    "excerpt": "Requests expire if not approved within 12 hours; approved access is revoked automatically after the requested period (currently up to 4 hours); approvals and operator actions are audited.",
    "id": "R3",
    "kind": "vendor",
    "title": "Microsoft Purview Customer Lockbox",
    "url": "https://learn.microsoft.com/purview/customer-lockbox-requests",
    "vendor": "Microsoft"
  }
]
```

<!-- end -->
