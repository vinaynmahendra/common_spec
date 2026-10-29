---
id: "PKG-ethical-walls-conflict-based"
title: "Ethical walls / conflict-based access restrictions"
parent: "PKG-authorization"
order: 3
type: "feature"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "Exclusion walls (person or firm from a case, party or case group) and need-to-know walls (only listed people on a sealed case) that override every role, scope, elevation and grant, including in search, notifications and AI"
links: []
rev: 3
syncHash: "4a1ad23029395bf2"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.2.3 Ethical walls / conflict-based access restrictions

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Exclusion walls (person or firm from a case, party or case group) and need-to-know walls (only listed people on a sealed case) that override every role, scope, elevation and grant, including in search, notifications and AI

<!-- section:purpose -->
## Purpose and scope

Ethical walls are restrictions that override every role and scope. Two kinds:

- **Exclusion walls** keep a person or organisation away from a case, a party (across all its cases in the tenant) or a group of cases, because of a conflict of interest or a screening decision.
- **Need-to-know walls** lock a case (normally a `sealed` case) so that only the people on its list can access it, even if their role or scope would otherwise cover it.

They protect the integrity of proceedings (a conflicted neutral or staff member must not see or influence a case) and the confidentiality of parties.

Scenarios:
- A neutral's conflict declaration ([[DOM-neutrals]]) names a party; the neutral must not be appointable to, see or be notified about cases involving that party in this tenant.
- A secretariat member is related to a party; the institution screens them from that case.
- A neutral is successfully challenged and removed; their access ends and they are walled from the case.
- A law firm asks the institution to screen one of its lawyers who previously acted for the other side.
- A transcriber or interpreter declares a conflict with a hearing participant.
- A high-profile or sensitive matter is sealed; only the named case team, tribunal and parties may access it, and tenant-wide secretariat cannot.

Pattern borrowed from: legal-sector ethical wall and matter-security tools that combine conflicted-user exclusions, opposing-matter segregation and restricted need-to-know access, enforced across connected systems including AI tools [R3][R4].

<!-- section:assets -->
## Protected assets

| Asset | Classification |
|---|---|
| Wall records (`authz_ethical_wall`, `authz_wall_member`): who is walled from what, by whom, since when | Confidential (reveals a conflict) |
| Wall reasons (`authz_ethical_wall_reason`, field-level encrypted) | Confidential, may include personal data |
| Need-to-know lists | Confidential |
| The walled resources: cases, parties, documents, hearings | As per resource |
| Conflict declarations (source of many walls) | Personal, tenant-internal ([[DOM-neutrals-schema]]) |

<!-- section:actors -->
## Actors and roles

| Actor | Relation to walls | Permission |
|---|---|---|
| Neutral, transcriber, interpreter | Declare conflicts (creates proposed exclusion walls); subject of walls | `neutral.conflict:create` |
| `case_manager`, `secretariat` | Propose walls for cases in scope; maintain need-to-know lists of their cases; cannot lift walls on themselves | `case.wall:create`, `case.wall:read` |
| `secretariat_lead` template | Approves, creates and lifts walls; second approver for lifts | `case.wall:approve`, `case.wall:delete` |
| Designated officer (`access.walls.designated_officer`) | Second approver in small institutions | `case.wall:delete` via a custom role |
| Tenant admin roles | No wall management by default; cannot see wall reasons | — |
| `auditor` | Reads wall register without reasons | `case.wall:read` (metadata) |
| Party, counsel | Not aware of walls except where disclosed under `access.walls.disclose_to_parties` | — |
| System | Creates walls automatically from challenge decisions and accepted conflict declarations | system purpose `wall_sync` |
| AI agents | Subject to walls of the human they act for; never create, approve or lift walls | — |

<!-- section:matrix -->
## Permission matrix

| Action | Subject (neutral, transcriber, staff) | case_manager / secretariat (scope) | secretariat_lead | Tenant admin roles | auditor | Platform support | Others |
|---|---|---|---|---|---|---|---|
| Declare a conflict (proposes a wall) | own ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Create exclusion wall for a case | ✗ | proposed (needs approval) | ✓ | ✗ | ✗ | ✗ | ✗ |
| Create wall for a party across tenant cases | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| Create organisation wall (firm) | ✗ | ✗ | ✓ (where `access.walls.org_walls_enabled`) | ✗ | ✗ | ✗ | ✗ |
| Set a case to need-to-know and edit its list | ✗ | ✓ (own cases; adding self needs approval) | ✓ | ✗ | ✗ | ✗ | ✗ |
| View walls on a case | existence of own walls only | ✓ (no reasons) | ✓ with reasons | ✗ | register without reasons | ✗ | ✗ |
| Lift wall | ✗ | ✗ | ✓ with second approver and reason | ✗ | ✗ | ✗ | ✗ |
| Lift wall on self | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Override wall temporarily (including break-glass) | not supported; lift and re-create | | | | | | |

Effect of an active or proposed exclusion wall on the subject: every `authz` decision on the walled scope is denied (all rows of [[PKG-policy-engine-permission-matrix#matrix]]), including for secretariat_lead and tenant admin roles; people pickers exclude the subject from appointment and assignment; notifications about the scope are not sent; search, reports with drill-down, AI retrieval and agent tools exclude the scope.

Effect of a need-to-know wall: only principals on the list (`authz_wall_member.kind = 'allowed'`) plus current case roles may access the case; secretariat scope assignments no longer cover it; additions to the list are audited and notify the case manager.

<!-- section:policy -->
## Policy model

- Tables `authz_ethical_wall`, `authz_ethical_wall_reason`, `authz_wall_member` are specified in [[PKG-authorization-data-model#tables]]. A wall has `kind` (`exclusion`, `need_to_know`), `subject` via members, `scope_type` (`case`, `party`, `case_group`), `source` (`conflict_declaration`, `manual`, `challenge_decision`, `firm_request`, `sealing`), `status` (`proposed`, `active`, `lifted`), approvals and dates.
- Walls are evaluated as the first deny rule in every decision (step 8 of the decision flow in [[PKG-policy-engine-permission-matrix#policy]]). `organisation` subjects wall every member of the organisation except members on an approved carve-out list.
- A `party` scope walls every case in the tenant where that party (matched by party identity record, not name) participates, including cases created later.
- `proposed` walls already deny the subject (fail closed, locked by `access.walls.proposed_walls_deny`) but do not trigger removal from the tribunal; removal is the secretariat's decision under the rules.
- Wall sets are cached per principal keyed by grant epoch; any wall change bumps the epochs of all subjects and members, so the change applies on the next request. Writes always check the database.
- Conflict checks at appointment: `neutral:assign` and people pickers call `walls.check(subject, case)` and the conflict screening in [[DOM-neutrals]]; a match blocks appointment.
- **Acknowledgement**: where `access.walls.require_acknowledgement`, a staff subject must acknowledge the wall in-app (without seeing the reason) within 5 working days; unacknowledged walls are listed in the wall report.
- **Interaction with other mechanisms**: walls are not bypassed by JIT elevation, break-glass, access requests or support grants; a request for access to a walled case is refused.
- **Wall report** (`/admin/access/walls`): active walls by scope, recent creations and lifts, unacknowledged walls, denials caused by walls in the last 30 days (counts), visible to wall approvers and, without reasons, to auditors.

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|---|
| T1 | E | Wall bypass through a derived copy (search result, email notification, AI summary, report drill-down) | Wall deny applied in search filter, notification recipient resolution, report drill-down and AI retrieval and tools | Low |
| T2 | E | Wall created but subject already has cached access | Epoch bump on create; database check on every write | Very low |
| T3 | I | Wall record reveals a conflict to the wrong person | Reasons encrypted and visible to wall approvers only; explainer redaction | Low |
| T4 | E | Insider lifts own or colleague's wall improperly | Self-lift forbidden; second approver; alert to all wall approvers on lift | Low |
| T5 | I | Party name collision creates a wrong wall | Party scope keyed by party identity id; proposed walls reviewed | Medium (data quality) |
| T6 | E | Emergency access used to reach a walled case | Break-glass and JIT evaluated after walls | Very low |
| T7 | I | Sealed case visible to tenant-wide secretariat | Need-to-know wall overrides scope | Low |

<!-- section:failure -->
## Denial behaviour

A walled user sees the case as not found (same as any other inaccessible case); they are never shown the word "conflict" in denial responses. In pickers a walled neutral is absent; case managers see the hint "1 person excluded by an ethical wall" where `access.walls.picker_hint_visible`. In the access explainer, administrators without `case.wall:approve` see only "Denied by a confidential restriction" ([[PKG-access-explainer]]).

<!-- section:requirements -->
## Security requirements

ASVS references are to OWASP ASVS **5.0** at chapter level [R1][R2]. Old IDs WALL-1 to WALL-4 are kept as WALL-FR-1 to WALL-FR-4.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| WALL-FR-1 | An active or proposed exclusion wall shall deny the subject every action on the walled scope, overriding all roles, scopes, elevations and grants. | V8 |
| WALL-FR-2 | Walls shall be applied in search, notifications, people pickers, reports, AI retrieval and agent tools as well as direct access. | V8 |
| WALL-FR-3 | Lifting a wall shall require a reason and approval by a second authorised person, and no one may lift a wall on themselves. | V8 |
| WALL-FR-4 | Creating or lifting a wall shall take effect on the subject's next request. | V8 |
| WALL-FR-5 | For a need-to-know case, only listed principals and current case roles shall have access. | V8 |
| WALL-FR-6 | Wall reasons shall be readable only by holders of `case.wall:approve` in scope. | V8 |

<!-- section:verification -->
## Verification

Tests: a walled secretariat_lead is denied on every matrix row for the case; walled neutral absent from picker, notifications, search, report drill-down and AI retrieval; break-glass and JIT do not reach a walled case; lift without second approver fails; self-lift fails; epoch bump makes the wall effective on the next request; need-to-know case invisible to tenant-scope secretariat not on the list; explainer redaction.

<!-- section:questions -->
## Open questions

- [ ] Do institution rules require disclosure of certain walls to parties (for example when a neutral is excluded after a challenge)? Now `access.walls.disclose_to_parties`; legal to confirm defaults per tenant type. (Legal)
- [ ] Should firm-requested walls apply across all tenants in a region (one firm, many institutions)? Proposed: no, per tenant only. (Product, legal)
- [ ] Who is the second approver in small institutions with one secretariat lead? Now `access.walls.designated_officer`. (Product)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Walls are tenant-owned rows with forced RLS; a wall in tenant A has no effect in tenant B, and wall reasons never leave the tenant.

<!-- check:enforcement -->
### Enforcement points and bypass paths

The wall check is the first deny rule inside every decision, so it applies to every entry point that calls `authz`, plus search, notification recipient resolution, people pickers, reports and AI retrieval and tools, which call the same check.

<!-- check:lifecycle -->
### Grant lifecycle and privileged access

Walls start from conflict declarations, manual action, challenge decisions, firm requests or sealing; proposed walls already deny. Lifting needs a reason and a second approver; self-lift is impossible; changes apply on the next request.

<!-- check:resilience -->
### Failure modes and secrets

Wall checks read an epoch-keyed cached set with database fallback; if neither is available the decision fails closed (deny). Writes always check the database.

<!-- check:audit -->
### Audit trail

Audited: declaration-created proposal, approval, creation, lift (with both approvers and reason), need-to-know list changes, acknowledgements, and every denial caused by a wall (reason code `walled`, visible only to wall approvers in audit search). Security event `nomo.sec.ethical_wall_block` ([[OBS-security-events]]).

<!-- check:compliance -->
### Framework and legal mapping

Supports ISO/IEC 27001:2022 Annex A 5.15 and 8.3 (access restriction) and the institution's own conflict and independence obligations under its rules; evidence is the wall register export and the audit of wall changes.

<!-- check:testing -->
### Verification and testing

Generated suite proves a walled user is denied on every matrix row for the scope and absent from pickers, notifications, search, reports and AI; self-lift, single-approver lift, break-glass and JIT bypass attempts fail.

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
    "title": "iManage Security Policy Manager: Introduction",
    "url": "https://docs.imanage.com/cloud/spm-admin-help/en-US/Introduction_to_iManage_Security_Policy_Manager.html",
    "vendor": "iManage"
  },
  {
    "id": "R4",
    "kind": "vendor",
    "title": "Intapp Walls: Manage and enforce ethical policies",
    "url": "https://www.intapp.com/legal/ethical-walls-compliance/",
    "vendor": "Intapp"
  }
]
```

<!-- end -->
