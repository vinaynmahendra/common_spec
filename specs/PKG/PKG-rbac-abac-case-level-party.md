---
id: "PKG-rbac-abac-case-level-party"
title: "RBAC + ABAC (case-level, party-level access)"
parent: "PKG-authorization"
order: 1
type: "feature"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "Case-level roles derived from case records, how they combine with scoped tenant roles, and the attribute conditions (side, stage, tier, exchange, window, need-to-know) that decide access inside a case"
links: []
rev: 3
syncHash: "df427c510ab44eeb"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.2.1 RBAC + ABAC (case-level, party-level access)

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Case-level roles derived from case records, how they combine with scoped tenant roles, and the attribute conditions (side, stage, tier, exchange, window, need-to-know) that decide access inside a case

<!-- section:purpose -->
## Purpose and scope

Defines how access inside a case is decided: which **case-level roles** a person holds on a case and where they come from, how those combine with **tenant roles held at a scope** (tenant, unit, case type), and the **attributes** (side, stage, document tier, exchange, addressee, time window) that policies test. Policies in [[PKG-policy-engine-permission-matrix]] are written over these facts; permissions come from [[PKG-permission-catalogue]]; roles and scopes from [[PKG-roles-and-permission-sets]].

It protects the core confidentiality promise of dispute resolution: each side sees what it is entitled to see at each stage, the tribunal's deliberations stay with the tribunal, and staff see only the cases their scope covers.

Pattern borrowed from: group-based access across matters with item-level overrides in e-discovery workspaces (Relativity) [R3]; relationship tuples for per-object roles (Zanzibar / OpenFGA) [R4]; attribute-based conditions (NIST SP 800-162) [R5].

<!-- section:assets -->
## Protected assets

| Attribute source | Table (owner) | Classification |
|---|---|---|
| Case roles (projection) | `authz_case_role` ([[PKG-authorization-data-model]]) | Case participants |
| Tenant role assignments with scope | `authz_role_assignment` ([[PKG-authorization-data-model]]) | Confidential |
| Parties, representation | `case_parties`, `case_representations` ([[DOM-cases-schema]]) | Case participants / personal |
| Tribunal seats | `tribunal_seats` ([[DOM-cases-schema]], [[DOM-neutrals-schema]]) | Case participants |
| Hearing assignment | `hearing_assignment` ([[DOM-hearings-schema]]) | Internal |
| Case stage | `cases.status` via [[WF-entity-state-machines]] | Case participants |
| Owning unit, case type | `cases.owning_unit_id`, `cases.case_type_key` (proposed columns in [[DOM-cases-schema]]) | Internal |
| Document tier, owner side, exchange, addressees | `document.visibility`, `document.owner_side`, `document.exchanged_at`, `document.addressed_to_party_ids` ([[DOM-documents-schema]]) | Varies |
| Case confidentiality | `cases.confidentiality` (`standard`, `confidential`, `sealed`) | Internal |

<!-- section:actors -->
## Actors and roles

**Case-level roles** (canonical keys) and the domain records they are derived from. `@nomology/authz` writes `authz_case_role` rows in the same transaction as the domain command ([[PKG-authorization-data-model#tables]]):

| Case role | Derived from ([[DOM-cases-schema]], [[DOM-hearings-schema]]) | `side` | Ends when |
|---|---|---|---|
| `claimant` / `respondent` | `case_parties.role` in (`claimant`) / (`respondent`) with a `membership_id`; `additional_party` and `intervener` map to the side set by the case manager | claimant / respondent | Party removed; case closed + `access.case.read_after_close_days` |
| `claimant_counsel` / `respondent_counsel` | Active `case_representations` (`kind` `counsel` or `authorised_representative`; `guardian` maps to the party role) | side of the represented party | Representation ended; party revokes; case closed + read-after-close |
| `presiding_neutral` | `tribunal_seats.seat_role` in (`sole`, `presiding`, `emergency`, `mediator`, `conciliator`) with accepted appointment | tribunal | Unseated (`challenge_upheld`, `resignation`, `removal`, `replaced`); case closed |
| `tribunal_member` | `tribunal_seats.seat_role = co_neutral` | tribunal | as above |
| `case_manager` | Case assignment (proposed `case_assignment` table; today `cases.assigned_secretary_membership_id`) | institution | Reassigned; case closed |
| `tribunal_secretary` | `tribunal_seats.seat_role = secretary`, appointed by the tribunal (decision D6); assists the tribunal, never approves or publishes orders or awards ([[PKG-roles-and-permission-sets#actors]]) | tribunal | Unseated; case closed |
| `expert` | Tribunal-appointed or party expert participant record | tribunal (tribunal-appointed) or party side | End date or discharge |
| `witness` | Hearing participant record | side calling the witness | End of hearing day |
| `interpreter`, `transcriber` | `hearing_assignment` with `valid_from` / `valid_to` | none | `valid_to` (transcriber: turnaround window from `access.case.transcriber_access_window_hours`) |
| `observer` | Participant record with end date (funders, insurers, trainees where the rules allow) | none | `access.case.observer_default_expiry_days` |

Mapping of the old capacity list: `sole_arbitrator`, `presiding_arbitrator`, `mediator`, `conciliator` → `presiding_neutral` with `seat_label`; `co_arbitrator` → `tribunal_member`; `tribunal_secretary` → `tribunal_secretary` (its own case role, decision D6); `additional_party` → `claimant` or `respondent` by side.

**Tenant roles that reach cases** (via scope, never via membership alone):

| Tenant role | Reaches | How |
|---|---|---|
| `secretariat` at `tenant` scope | every case in the tenant | `ps.case.secretariat_core` |
| `secretariat` at `unit` scope | cases whose `owning_unit_id` is the unit (and descendants) | same |
| `secretariat` at `case_type` scope | cases of that blueprint key (for example a "SEBI ODR conciliation" desk) | same |
| `secretariat_lead` template | as its scope, plus supervisor actions | `ps.case.secretariat_supervisor` |
| `auditor` | case audit metadata only | `case.audit:read` |
| Admin roles | no case content | — |

How a case gets its `owning_unit_id` is set by `access.case.unit_owns_case_by` ([[PKG-settings-access-control]]).

<!-- section:matrix -->
## Permission matrix

**Conditions** (reusable predicates; each has a predicate form and a filter form):

| Condition | Definition | Used by |
|---|---|---|
| `hasCaseRole(case, roles?)` | Active `authz_case_role` for the principal on the case (`ended_at IS NULL`, `valid_from ≤ now() < valid_to`), not walled | Most case permissions held through case roles |
| `inScope(case)` | An assignment of the permission at `tenant`, `unit` (owning unit in set) or `case_type` (blueprint key) scope | Secretariat permissions |
| `onSide(case, side)` | Case role with that `side`, or counsel representing a party on that side | Side-restricted documents, filings, payments |
| `isTribunal(case)` | `presiding_neutral` or `tribunal_member` | Tribunal-only material, orders, awards |
| `isPresiding(case)` | `presiding_neutral` | Issue orders where the rules require |
| `isCaseManager(case)` | `case_manager` role on the case | Case administration permissions at case scope |
| `inWindow(assignment)` | `now()` (database clock) within `valid_from`–`valid_to` | Transcriber, interpreter, observer |
| `stageIn(case, stages)` | Case status in set (from the state machine) | Filing windows, locks after award |
| `tier(doc) = T` | `case_participants`, `side_restricted`, `tribunal_only`, `institution_internal` | Document reads |
| `exchanged(doc)` | `document.exchanged_at IS NOT NULL` under `access.case.exchange_mode` | Other side's read of pleadings |
| `addressedTo(doc, principal)` | Party in `addressed_to_party_ids` (only if `access.case.party_addressed_documents`) | Multi-party cases |
| `ownsRecord(r)` | `created_by = principal` or the party is the principal | Own invoices, own drafts, own filings |
| `needToKnow(case)` | For `sealed` cases with `access.case.sealed_cases_need_to_know`: principal is on the case's need-to-know list ([[PKG-ethical-walls-conflict-based]]) | All permissions on sealed cases, including secretariat scope |
| `setting(key)` | Resolved value from [[PKG-settings-access-control]] (`access.case.*`), pinned or running as declared | Tenant and case-type variations |

**How tenant-level and case-level roles combine**

| Principal holds | On a case in scope | Result |
|---|---|---|
| Case role only (party, counsel, neutral) | — | Permissions of the case role, with its conditions |
| `secretariat` at a scope covering the case, no case role | yes | Secretariat permissions; tribunal-only tier still denied unless setting |
| `secretariat` at a scope **not** covering the case, no case role | no | Not found |
| `secretariat` + `case_manager` on the case | — | Union; `case_manager` adds case-scope rights even if the unit scope does not cover the case (cross-unit assignment) |
| `neutral` tenant role + `presiding_neutral` case role | — | Tribunal permissions; the tenant role alone gives none |
| Any role + wall on the case | — | Denied (walls override) |
| Any role + `sealed` case and not on need-to-know list | — | Denied, including tenant-scope secretariat |
| `case_manager` + `tribunal_member` on the same case | — | Refused at assignment (`sod.neutral_and_secretariat_same_case`, [[PKG-separation-of-duties]]) |

**Document visibility** (the most error-prone area):

| Tier | Own side (party, counsel) | Other side | Tribunal | case_manager | secretariat (scope) | Transcriber / interpreter | Expert |
|---|---|---|---|---|---|---|---|
| `case_participants` | ✓ | ✓ | ✓ | ✓ | ✓ | only exhibits linked to an assigned hearing | if directed to them |
| `side_restricted` (before exchange) | ✓ | ✗ until `exchanged` | ✓ if submitted to tribunal | ✓ | ✓ | ✗ | ✗ |
| `tribunal_only` | ✗ | ✗ | ✓ | `access.case.secretariat_sees_tribunal_drafts` | same setting | ✗ | ✗ |
| `institution_internal` | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ |

<!-- section:policy -->
## Policy model

- **Facts loading**: `loadCaseFacts(tx, principal, caseId)` returns in one query: the principal's active case roles (with side, seat label, windows), covering scoped assignments, case status, confidentiality, owning unit, blueprint key, walls and need-to-know membership. Runs inside `withTenant` so RLS applies; memoised per request.
- **Filters**: `authz.where('case.document:list', principal)` compiles conditions into Prisma `where` fragments, for example `OR [ {visibility:'case_participants', case:{authzCaseRoles:{some:{membershipId, endedAt:null}}}}, {case:{owningUnitId:{in: unitIds}}}, … ]`. Every policy must be expressible both as a predicate and as a filter; the harness checks both forms agree on generated data.
- **Time**: windows and expiries use the database clock (`now()`), never the application clock.
- **Pinned settings**: `access.case.*` values marked pinned are copied into the case's rule-set pin at case start ([[DOM-cases-schema]] `case_rule_set_pins`) and read from there.
- **Writing case roles**: domain commands (add party, add representative, seat neutral, assign case manager, schedule hearing assignment) call `authz.caseRoles.grant/revoke` inside the same transaction; this bumps the principal's grant epoch so the change applies on the next request. A nightly reconciler compares `authz_case_role` with the domain tables and alerts on drift.
- **Side changes**: if a party's side changes (rare; joinder or re-alignment ordered by the tribunal), all case roles of that party and its counsel are revoked and re-granted with the new side, and side-restricted documents of the old side remain owned by that side.

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|---|
| T1 | I | Filter and predicate disagree (list shows an item the detail page denies, or the reverse) | Dual-form policy tests on generated data | Low |
| T2 | E | Counsel remains after the party revokes representation | Representation end revokes the case role in the same transaction; epoch bump | Low |
| T3 | E | Ended transcriber assignment still works | Window checked with database clock; expiry sweep and alert | Low |
| T4 | I | Multi-party case leaks a settlement offer to another respondent | `addressedTo` condition for side-restricted documents where enabled per case type | Medium (configuration-dependent) |
| T5 | E | Stage change not reflected (filing after deadline) | Stage read in the same transaction as the write | Low |
| T6 | E | Secretariat scope too wide | Unit or case-type scoping; review flags tenant-scope secretariat | Medium |
| T7 | E | Domain change bypasses the case-role helper | Lint rule; nightly reconciler | Low |
| T8 | I | Sealed case visible to tenant-wide secretariat | Need-to-know condition overrides scope | Low |

<!-- section:failure -->
## Denial behaviour

Denials based on missing case role or scope return not-found. Denials based on stage return 403 `stage_closed` with the stage name; missing step-up returns 401 `auth/step-up-required`; walled and need-to-know denials look like not-found.

<!-- section:requirements -->
## Security requirements

ASVS references are to OWASP ASVS **5.0** at chapter level [R1][R2]. Old IDs ABAC-1 to ABAC-5 are kept as ABAC-FR-1 to ABAC-FR-5.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| ABAC-FR-1 | Case access shall require an active case role, or a tenant role assignment whose scope covers the case; tenant membership alone grants no case access. | V8 |
| ABAC-FR-2 | Side-restricted documents shall not be visible to the other side until exchanged under the case's exchange mode. | V8 |
| ABAC-FR-3 | Tribunal-only documents shall be visible only to the tribunal, plus secretariat where `access.case.secretariat_sees_tribunal_drafts` is true for the case. | V8 |
| ABAC-FR-4 | Time-bound case roles shall stop working at `valid_to` measured by the database clock. | V8 |
| ABAC-FR-5 | Every policy shall produce the same result as a predicate and as a query filter on the policy test corpus. | V8 |
| ABAC-FR-6 | Case roles shall be written in the same transaction as the domain record they derive from. | V8 |
| ABAC-FR-7 | For sealed cases with need-to-know enabled, only principals on the case's need-to-know list shall have any access, regardless of scope. | V8 |
| ABAC-FR-8 | A unit-scoped assignment shall cover exactly the cases owned by that unit (and descendants where set), and no others. | V8 |

<!-- section:verification -->
## Verification

Generated data sets with 2 tenants × 3 case types × 3 units × every case role × every tier × sealed and unsealed; each policy evaluated as predicate and filter; results must match the matrix. Time-bound roles tested with a controlled database clock. Reconciler drift tests. Scope-edge tests (sibling unit, other case type, cross-unit case manager).

<!-- section:questions -->
## Open questions

- [ ] Confirm the case role list per product (CORD mediation and ODR vs TERES arbitration) with product; `tribunal_secretary` is accepted for TERES arbitration (D6), and its use in CORD is to be confirmed. (Product)
- [ ] Add `case_assignment`, `owning_unit_id` and `case_type_key` to [[DOM-cases-schema]]. (Domain team)
- [ ] Former participants' read access after close: `access.case.read_after_close_days` default 90 (365 for institutions); legal to confirm. (Legal)
- [ ] Do observers (funders, insurers, trainees) need a distinct permission set per type? (Product)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

All attribute tables are tenant-owned with forced RLS; facts are loaded in `withTenant`, so a case role in tenant A can never satisfy a condition in tenant B.

<!-- check:enforcement -->
### Enforcement points and bypass paths

All conditions are evaluated through shared fact loaders and `authz.where`; no domain code reads `authz_case_role` or role assignments to decide access (lint rule).

<!-- check:lifecycle -->
### Grant lifecycle and privileged access

Removal, recusal, representation end, unseating and assignment expiry end case roles immediately in the database and on the next request through the grant epoch.

<!-- check:resilience -->
### Failure modes and secrets

Facts are loaded per request in the same transaction (fail closed if unavailable); cached grant sets are keyed by epoch so a stale cache can never be used after a change.

<!-- check:audit -->
### Audit trail

Case role grants and revocations, side changes, scope assignments and time-bound role expiry are audited with policy and catalogue versions; sensitive reads (tribunal-only, KYC) carry an `audit_read` obligation.

<!-- check:compliance -->
### Framework and legal mapping

Implements the least-privilege and need-to-know parts of ISO/IEC 27001:2022 Annex A 5.15, 5.18 and 8.3 [R6] and SOC 2 CC6.1–CC6.3 [R7]; evidence is the generated condition catalogue, matrix test results and access reviews ([[SEC-access-reviews]]).

<!-- check:testing -->
### Verification and testing

Dual-form tests on generated data for every policy, time-bound role tests with a controlled clock, scope-edge tests and matrix-generated allow and deny tests per tier and case role.

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
    "title": "RelativityOne documentation: Relativity object security (item-level security)",
    "url": "https://help.relativity.com/RelativityOne/Content/Relativity/Security_permissions/Setting_permissions_on_Relativity_objects.htm",
    "vendor": "Relativity"
  },
  {
    "id": "R4",
    "kind": "web",
    "publisher": "USENIX ATC 2019 / Google Research",
    "title": "Zanzibar: Google's Consistent, Global Authorization System",
    "url": "https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/"
  },
  {
    "body": "NIST",
    "id": "R5",
    "ident": "SP 800-162",
    "kind": "standard",
    "title": "NIST SP 800-162, Guide to Attribute Based Access Control (ABAC) Definition and Considerations",
    "url": "https://csrc.nist.gov/pubs/sp/800/162/upd2/final"
  },
  {
    "body": "ISO/IEC",
    "id": "R6",
    "ident": "27001",
    "kind": "standard",
    "title": "ISO/IEC 27001:2022 Information security management systems",
    "url": "https://www.iso.org/standard/27001",
    "version": "2022"
  },
  {
    "body": "AICPA",
    "id": "R7",
    "ident": "Trust Services Criteria",
    "kind": "standard",
    "title": "2017 Trust Services Criteria (with revised points of focus, 2022)",
    "url": "https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022",
    "version": "2017 (revised points of focus 2022)"
  }
]
```

<!-- end -->
