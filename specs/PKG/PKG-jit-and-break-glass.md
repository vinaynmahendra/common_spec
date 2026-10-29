---
id: "PKG-jit-and-break-glass"
title: "Just-in-time elevation and break-glass access"
parent: "PKG-authorization"
order: 7
type: "feature"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "Eligible-not-standing privileged roles activated for hours with justification and optional approval, access requests for cases and roles, and audited break-glass emergency profiles with mandatory after-the-event review"
links: []
rev: 1
syncHash: "45702be66adeeaf0"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.2.7 Just-in-time elevation and break-glass access

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Eligible-not-standing privileged roles activated for hours with justification and optional approval, access requests for cases and roles, and audited break-glass emergency profiles with mandatory after-the-event review

<!-- section:purpose -->
## Purpose and scope

Removes standing privilege. Instead of holding powerful roles all the time, people are made **eligible** for them and **activate** them for a short, justified, audited period. For emergencies there is a separate, louder path: **break-glass**, which grants a fixed emergency profile immediately and is reviewed after the event.

Three mechanisms in the product (all inside a tenant, or inside the platform tenant for Nomology staff):

| Mechanism | For | Approval | Typical duration |
|---|---|---|---|
| **JIT elevation** | Privileged administrative roles (tenant_admin, security_admin, integration_admin, ai_admin, workflow_designer publish, secretariat_lead) and privileged one-off permissions (`case:export`) | Self-activation with justification, or approval, per eligibility | 1–8 hours |
| **Access request** | A person who lacks access to a case, unit or role asks for it | Approver in scope (unit admin, supervising secretariat, case manager) | Until a date, or for the life of the case |
| **Break-glass** | Urgent action when nobody with the normal role is reachable: an emergency arbitrator application at night, a tenant locked out of SSO | No prior approval; mandatory reason; immediate notification; review within 2 working days | 2 hours, not renewable without a new event |

Scope boundaries:
- Nomology support access to tenant data is a separate, tenant-approved grant ([[PKG-support-access-and-impersonation]]); this node supplies the JIT engine it uses.
- Infrastructure break-glass (cloud consoles, database `nomo_platform_ops`) is a control in [[SEC-access-reviews]]; this node covers the application.
- Settings for all of this live in [[PKG-settings-access-control]] (`access.jit.*`, `access.break_glass.*`, `access.requests.*`).

Pattern borrowed from: eligible versus active role assignments with time-bound activation, justification and approval in Microsoft Entra Privileged Identity Management [R3].

<!-- section:assets -->
## Protected assets

| Asset | Classification |
|---|---|
| Eligibilities (who may activate what) | Confidential |
| Elevation and break-glass events with justifications | Confidential / Personal |
| What was done during an elevated or break-glass window | Per resource; audit stream tagged with `elevation_id` / `break_glass_id` |
| Emergency profiles definitions | Internal (platform-defined) |

<!-- section:actors -->
## Actors and roles

| Actor | Role in this control |
|---|---|
| Eligible member | Activates an eligibility; requests access; uses break-glass where their profile allows |
| Approver (`access.elevation:approve`, or `access.request:approve` within scope) | Approves or rejects activations and requests; cannot approve their own |
| `security_admin`, `tenant_owner` | Manage eligibilities; receive break-glass alerts; perform break-glass reviews (`access.break_glass:read`) |
| `auditor` | Reads all events |
| Nomology `platform_security` | Approves staff elevations in the platform tenant (`platform.elevation:approve`); oversees tenant-owner recovery break-glass |
| System | Expires activations; sends reminders; escalates overdue reviews |

<!-- section:matrix -->
## Permission matrix

**Eligibility rules (defaults; tenant may tighten within platform bounds)**

| Role or permission | Eligible-only by default? | Max activation | Approval | Ticket ref | Step-up |
|---|---|---|---|---|---|
| `tenant_owner` | No (standing, minimum 1) — activation used for second owners where `access.jit.owner_standing_count` is reached | 4 h | Another owner | Optional | ✓ |
| `tenant_admin` | Yes for SEBI ODR and court blueprints; optional for others | 4 h | Self with justification (default) | Optional | ✓ |
| `security_admin` | Yes | 2 h | Approval by tenant_owner or another security_admin | Required | ✓ |
| `integration_admin`, `ai_admin` | Yes | 4 h | Self with justification | Optional | ✓ |
| `secretariat_lead` template | Optional | 8 h | Self with justification | Optional | ✓ |
| `case:export` (one case) | Via access request | 24 h | Supervising secretariat | Optional | ✓ |
| Platform `platform_admin`, `regional_ops` | Always eligible-only | 8 h | `platform_security` | Required | ✓ (WebAuthn) |
| Platform `platform_owner` | Standing for 2 named people, otherwise eligible | 4 h | Another platform_owner | Required | ✓ |

**Break-glass profiles (platform-defined; tenants switch them on and choose who may use them)**

| Profile | Grants | Never grants | Who may invoke | Duration | Notified at once |
|---|---|---|---|---|---|
| `emergency_case_access` | `ps.case.secretariat_core` on one named case | Tribunal-only material; award signing or serving; wall lifting; anything on a case where the user is walled | Members with `secretariat` at any scope in the tenant (configurable list) | 2 h | Case's assigned case manager, tenant_owners, security_admins |
| `emergency_tenant_admin` | `tenant_admin` for SSO and authentication settings only (`settings.security:write`, `user.session:delete`) | Role assignments; case content; data exports | Members listed in `access.break_glass.tenant_admin_holders` (should be 2, with phishing-resistant MFA) | 1 h | All tenant_owners and security_admins; Nomology security |
| `tenant_owner_recovery` (platform-run) | Restores a tenant_owner assignment when all owners are lost | Anything else | `platform_security` with `platform_owner`, after identity verification of the tenant's authorised signatory | Until a new owner signs in | Tenant's contract contacts |

**Actions**

| Action | Eligible member | Approver | security_admin | auditor |
|---|---|---|---|---|
| Activate eligibility | own ✓ | ✗ | own ✓ | ✗ |
| Approve activation | ✗ own | ✓ in scope | ✓ | ✗ |
| Extend an activation | request new activation | ✗ | ✗ | ✗ |
| End activation early | own ✓ | ✓ | ✓ | ✗ |
| Invoke break-glass | per profile | — | per profile | ✗ |
| Review break-glass event | ✗ own | ✗ | ✓ (not own) | read |
| Create or change eligibilities | ✗ | ✗ | ✓ (maker-checker) | read |

<!-- section:policy -->
## Policy model

**JIT activation flow** (Temporal workflow `authz.ElevationWorkflow` per activation, regional task queue `authz`):

1. Member opens `/admin/access/elevate` (or the "Elevate" prompt shown when a denied action could be allowed by an eligibility). Chooses eligibility, duration (≤ max), justification (min 20 characters), ticket ref if required. Step-up MFA.
2. If `requires_approval`: approvers in scope get an in-app task and email ([[WF-human-tasks]]); the workflow waits for signal `decide` with a timeout of `access.jit.approval_timeout_min` (default 60), after which the request lapses.
3. On approval (or immediately when self-activation is allowed): in one transaction, insert `authz_role_assignment` with `source='jit'`, `ends_at`, bump the principal's grant epoch, write `admin.access.elevation_activated`.
4. Timer to `ends_at`: revoke assignment, bump epoch, end any sessions' elevated state, write `admin.access.elevation_ended`. The expiry sweep (`authz-expiry` BullMQ queue, every 5 minutes) is the backstop if the workflow is delayed. Because expiry is also evaluated by the decision point with the database clock (`ends_at > now()`), a delayed workflow never extends access.
5. During the window the UI shows a banner "Elevated: security_admin until 15:40 (reason …)" and every audit event carries `elevation_id`.

**Access request flow**: same workflow shape (`authz.AccessRequestWorkflow`), approver resolved from the target: case → case manager or supervising secretariat of the owning unit; unit → unit_admin; role → user_admin (non-privileged) or security_admin (privileged). Approved requests create assignments with `source='manual'` and `source_ref` = request id. Walls are checked at request time and at decision time; a walled person cannot be granted access by request.

**Break-glass flow** (`authz.BreakGlassWorkflow`):

1. Member opens `/admin/access/break-glass` (or the "Emergency access" link on a not-found case page, only shown to holders of an applicable profile when the tenant enables it). Chooses profile and target, reason code (`urgent_deadline`, `emergency_application`, `sso_outage`, `safety`, `other`) and text, step-up MFA.
2. Assignment created immediately with `source='break_glass'`, `ends_at = now() + profile duration`. Epoch bumped.
3. Notifications sent at once to the profile's notify list (in-app, email, and SMS for tenant_owners where configured); security event `nomo.sec.break_glass_used` ([[OBS-security-events]]).
4. Every action is tagged with `break_glass_id`; reads of documents are audited individually (`audit_read` obligation applies to everything during break-glass).
5. Review task created for security_admins due in `access.break_glass.review_days` (default 2 business days on the tenant's business schedule, [[WF-sla-and-business-calendars]], computed by [[PKG-calendars-and-deadline]]). Outcome `justified`, `not_justified` (triggers a security incident record per [[SEC-security-incident-response-and]]) or `referred`. Overdue reviews escalate to tenant_owners daily.
6. Break-glass can be used at most `access.break_glass.max_per_user_per_30d` times (default 3) before it is blocked for that user pending review.

**Invariants**
- JIT and break-glass assignments always have `ends_at`; the database enforces it.
- Nobody approves their own activation or reviews their own break-glass.
- Break-glass never overrides ethical walls, tribunal-only tiers, legal holds or consequential actions reserved to the tribunal.
- Elevated windows do not stack beyond the maximum: a new activation for the same eligibility replaces the previous end time only up to `max_activation_minutes` from now.

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat | Scenario | Mitigation | Residual |
|---|---|---|---|---|---|
| T1 | E | Break-glass used as a convenience | Staff use emergency access to avoid asking colleagues | Loud notifications, mandatory review, per-user rate limit, `not_justified` creates an incident; monthly report to tenant_owners | Medium (cultural) |
| T2 | E | Access persists after the window | Workflow fails, assignment never revoked | Decision point checks `ends_at` with database clock; sweep job; alert on any JIT/break-glass assignment past `ends_at` without revocation | Very low |
| T3 | S | Stolen session activates elevation | Attacker with a session elevates | Step-up with phishing-resistant MFA where configured; new-device activation requires approval; alert on activation from new IP | Low |
| T4 | E | Approver collusion | Two admins approve each other's elevations routinely | Access review shows approval pairs; SoD report on reciprocal approvals ([[PKG-separation-of-duties]]) | Low |
| T5 | I | Break-glass reveals walled or tribunal-only material | Emergency access on a case with a wall on the user | Profiles exclude walled cases and tribunal-only tier; checked by the normal deny rules | Very low |
| T6 | D | Approver unavailable during an emergency | Nobody approves an urgent activation | Break-glass exists for exactly this; approval timeout returns a clear message suggesting break-glass where enabled | Low |

<!-- section:failure -->
## Denial behaviour

- A denial that an eligibility could cure returns 403 `elevation_available` (visible resources only) and the UI offers "Elevate to security_admin"; for case resources the response stays not-found unless the user already sees the case.
- Expired elevation mid-action: the next request is denied with `elevation_expired`; unsaved drafts are kept.
- Break-glass blocked by rate limit: 403 `break_glass_limit` with the name of the security_admin to contact.

<!-- section:requirements -->
## Security requirements

ASVS references are to OWASP ASVS 5.0 at chapter level [R1][R2]; requirement-level IDs to be added after checking against the 5.0.0 text.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| JIT-FR-1 | Where an eligibility exists, the system shall let the member activate the role for no longer than its maximum, after step-up and a justification. | V8 |
| JIT-FR-2 | When an eligibility requires approval, the system shall create the assignment only after approval by an approver other than the requester. | V8 |
| JIT-FR-3 | The decision point shall treat JIT and break-glass assignments as inactive once `ends_at` has passed by the database clock, regardless of workflow state. | V8 |
| JIT-FR-4 | When break-glass is invoked, the system shall grant only the profile's permissions on the named target, notify the profile's recipients within 1 minute and create a review task. | V8, V16 |
| JIT-FR-5 | Break-glass shall not override ethical walls, tribunal-only visibility, legal holds or permissions reserved to the tribunal. | V8 |
| JIT-FR-6 | Every action taken under an elevation or break-glass shall carry its id in the audit event. | V16 |
| JIT-FR-7 | If a break-glass review is not completed within `access.break_glass.review_days`, the system shall escalate to tenant_owners daily until it is. | — |
| JIT-FR-8 | Staff platform roles other than two named platform_owners shall be eligible-only. | V8 |

Acceptance (selected):
- **Given** security_admin is eligible with approval, **when** Asha requests 2 h, **then** no assignment exists until Ravi approves; **and when** Asha tries to approve her own request, **then** it is refused.
- **Given** an emergency arbitrator application filed at 23:00 with no case manager available, **when** a secretariat member invokes `emergency_case_access` on that case, **then** they can read the application and assign it, the tenant_owners receive an alert within 1 minute, and a review task is due in 2 working days.
- **Given** the same member is walled from the case, **when** they invoke break-glass on it, **then** the case remains not found and the attempt is audited.

<!-- section:verification -->
## Verification

- Workflow tests with Temporal time-skipping: activation, approval timeout, expiry, early end, workflow failure with sweep backstop.
- Database-clock tests: an assignment with `ends_at` in the past is denied even if `revoked_at` is null.
- Break-glass negative suite: walled case, tribunal-only document, award serving, wall lift — all denied under every profile.
- Quarterly tabletop: tenant SSO outage with `emergency_tenant_admin` in a staging tenant; recorded as evidence for [[SEC-access-reviews]].

<!-- section:questions -->
## Open questions

- [ ] Should SEBI ODR institution tenants require approval for every tenant_admin activation? Proposed default yes in that blueprint. (Product, compliance)
- [ ] Tenant-owner recovery: what identity evidence does Nomology accept from an institution (board letter, signatory KYC)? (Legal, account management)
- [ ] Break-glass review outcome `not_justified`: does it trigger notification duties to parties whose data was read? Assumption: only if the review finds misuse; legal to confirm per DPDP and tenant contract. (Legal / DPO)
- [ ] SMS alerts for break-glass in India require a DLT-registered template ([[PKG-notification-copy]]). (Integrations)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

All eligibilities, activations and events are tenant-owned under forced RLS; staff elevations use the regional platform tenant. Tenant-owner recovery is the only flow initiated by Nomology into a tenant and it grants nothing to Nomology staff.

<!-- check:enforcement -->
### Enforcement points and bypass paths

Elevations and break-glass create ordinary assignments, so every entry point that calls `@nomology/authz` respects them and their limits. Deny rules (walls, tiers, holds) run before allow rules, so emergency profiles cannot bypass them.

<!-- check:lifecycle -->
### Grant lifecycle and privileged access

Eligibilities are granted with maker-checker and an expiry (`valid_until`, default 12 months) and are listed in access reviews; activations last 1–8 hours; break-glass lasts 1–2 hours; all end by database clock; nothing is renewable without a new justified event.

<!-- check:resilience -->
### Failure modes and secrets

If Temporal is unavailable, activations requiring approval cannot start (fail closed) but expiry still works because the decision point checks `ends_at`; break-glass does not depend on Temporal for the grant itself (single transaction) and queues notifications through the outbox, with an alert if they are not delivered in 1 minute.

<!-- check:audit -->
### Audit trail

`admin.access.elevation_requested/approved/rejected/activated/ended`, `admin.access.request_*`, `admin.access.break_glass_invoked/ended/reviewed`, each with justification, approver and ids; all actions in the window carry the elevation or break-glass id.

<!-- check:observability -->
### Detection and alerting

Alerts: every break-glass (tenant and Nomology security), more than `max_per_user_per_30d`, any JIT or break-glass assignment past `ends_at` without revocation, activation from a new device or country, overdue reviews. Monthly report per tenant of elevations and break-glass ([[RPT-platform-security]]).

<!-- check:compliance -->
### Framework and legal mapping

ISO/IEC 27001:2022 Annex A 8.2 (privileged access rights) and 5.18 [R4]; SOC 2 CC6.1 and CC6.3 [R5]; NIST SP 800-53 AC-2 and AC-6 as design reference [R6]. Evidence: elevation and break-glass registers with reviews.

<!-- check:testing -->
### Verification and testing

Time-skipping workflow tests, database-clock expiry tests, break-glass negative suite and the quarterly tabletop, as in *Verification*.

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
    "id": "R3",
    "kind": "vendor",
    "title": "Microsoft Learn: What is Privileged Identity Management?",
    "url": "https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/pim-configure",
    "vendor": "Microsoft"
  },
  {
    "body": "ISO/IEC",
    "id": "R4",
    "ident": "27001",
    "kind": "standard",
    "title": "ISO/IEC 27001:2022 Information security management systems",
    "url": "https://www.iso.org/standard/27001",
    "version": "2022"
  },
  {
    "body": "AICPA",
    "id": "R5",
    "ident": "Trust Services Criteria",
    "kind": "standard",
    "title": "2017 Trust Services Criteria (with revised points of focus, 2022)",
    "url": "https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022",
    "version": "2017 (revised points of focus 2022)"
  },
  {
    "body": "NIST",
    "id": "R6",
    "ident": "SP 800-53 Rev. 5",
    "kind": "standard",
    "title": "NIST SP 800-53 Rev. 5, Security and Privacy Controls for Information Systems and Organizations (AC-2, AC-5, AC-6)",
    "url": "https://csrc.nist.gov/pubs/sp/800/53/r5/final",
    "version": "Rev. 5"
  }
]
```

<!-- end -->
