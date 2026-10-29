---
id: "PKG-access-explainer"
title: "Access explainer and permission simulator"
parent: "PKG-authorization"
order: 5
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Explains why a principal can or cannot act on a resource, who can act on it, and what a principal can do, including as of a past date, and simulates the effect of draft access changes before approval"
links: []
rev: 1
syncHash: "fc17237f673dcdcb"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.2.5 Access explainer and permission simulator

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Explains why a principal can or cannot act on a resource, who can act on it, and what a principal can do, including as of a past date, and simulates the effect of draft access changes before approval

<!-- section:statement -->
## Statement

**AEX-FR-0 (umbrella):** The platform shall let authorised administrators see, for any principal, action and resource in their tenant, whether access is allowed and exactly why, and shall let them see the effect of a proposed access change on every affected principal before it is applied.

| ID | EARS statement |
|---|---|
| AEX-FR-1 | When an administrator with `access.explainer:read` asks "can principal P do action A on resource R?", the system shall return the decision, the reason code, every allow path (assignment → role → permission set → permission, with scope), every deny rule that matched, every condition evaluated with its result, the plan entitlement result, and the policy and catalogue versions. |
| AEX-FR-2 | When asked "who can do action A on resource R?", the system shall list principals (users, groups, service accounts, AI agents) with the path for each, paged, within 5 seconds for a case with up to 500 participants. |
| AEX-FR-3 | When asked "what can principal P do?", the system shall show P's effective permissions grouped by domain and scope, highlighting privileged permissions, JIT eligibilities and toxic combinations. |
| AEX-FR-4 | When a draft change to a role, permission set, assignment, group mapping, unit structure or access setting is in `draft` or `in_review`, the simulator shall show the principals who gain or lose each permission and the count of cases newly visible or no longer visible per principal. |
| AEX-FR-5 | The simulator shall evaluate the draft against the same policy code and catalogue release as production, without writing any grant or sending any notification. |
| AEX-FR-6 | The explainer shall not reveal ethical wall reasons, the identity of the person who requested a wall, or the existence of tribunal-only documents to an administrator who lacks `case.wall:approve` or tribunal access; it shall show "Denied by a confidential restriction" instead. |
| AEX-FR-7 | Where `access.explainer.self_service` is on, a member shall be able to ask why they cannot perform an action on a resource they can already see, and get a plain-language reason and, where one exists, the way to request access. |
| AEX-FR-8 | Every explainer query and simulation shall be audited with the asker, the subject principal and the resource. |
| AEX-FR-9 | The explainer shall be able to answer "as of" a past date within the audit retention period, using assignment history and the policy and catalogue versions that applied then. |

<!-- section:rationale -->
## Rationale and source

- **Admins cannot govern what they cannot see.** With permission sets, scoped assignments, case roles, walls, entitlements and settings combined, "why can she see this case?" has no obvious answer without a tool. Incorrect guesses lead to over-granting.
- **Safe change.** Role edits affect every holder at once ([[PKG-roles-and-permission-sets#policy]]); the simulator diff is the evidence the checker reviews ([[PKG-separation-of-duties]]).
- **Disputes and audits.** Parties sometimes allege that someone saw material they should not have; an "as of" explanation with policy version answers this from records ([[PKG-audit-trail]]).
- **Support.** Most access tickets are "I cannot do X". Self-service explanation reduces tickets and avoids giving support staff broad access.
- **Pattern borrowed from**: access summaries that list every permission and where it comes from in Salesforce permission set groups [R1]; "check" and "list users/objects" queries of relationship-based engines such as OpenFGA [R2]; diagnostics returned with every Cedar decision [R3].

<!-- section:acceptance -->
## Acceptance criteria

**Routes and API**
- Console: `/admin/access/explain` (three tabs: *Can they?*, *Who can?*, *What can they?*), `/admin/access/simulate/[changeRequestId]`, and an "Explain access" action on user, role, case and document pages ([[APP-user-and-access-admin]]).
- Admin API: `POST /admin/v1/access/explain`, `POST /admin/v1/access/who-can`, `GET /admin/v1/access/principals/{id}/effective`, `POST /admin/v1/access/simulations` ([[INT-tenant-admin-api]]).
- Library: `authz.explain(tx, principal, action, resource, { asOf? })` returns `Explanation` (below); `authz.simulate(tx, changeSet)` returns `SimulationResult`.

```ts
interface Explanation {
  decision: 'allow' | 'deny';
  reason: 'allowed' | 'no_permission' | 'out_of_scope' | 'condition_failed' | 'walled'
        | 'confidential_restriction' | 'not_in_plan' | 'suspended' | 'step_up_required' | 'expired';
  paths: Array<{ via: 'direct'|'group'|'case_role'|'jit'|'break_glass'|'support_grant'|'ai_on_behalf';
                 assignmentId: string; role?: string; permissionSet: string; scope: string;
                 muted?: boolean; endsAt?: string }>;
  conditions: Array<{ name: string; result: boolean; detail?: string }>;   // e.g. tier = side_restricted, exchanged = false
  denies: Array<{ rule: string; detail?: string }>;                        // redacted per AEX-FR-6
  entitlement: { feature?: string; included: boolean };
  versions: { policy: string; catalogue: string };
  remedies: Array<'request_access'|'elevate'|'ask_case_manager'|'upgrade_plan'>;
}
```

**Scenarios**
1. **Given** counsel Rohan cannot open document D in case 77, **when** the user_admin asks *Can they?*, **then** the answer is deny, reason `condition_failed`, path "claimant_counsel on case 77 via representation of Party A", condition `tier = side_restricted (respondent)`, `exchanged = false`, remedy "ask_case_manager".
2. **Given** a draft change adds `case:export` to role "Desk supervisor", **when** the checker opens the simulation, **then** it lists the 12 holders gaining `case:export`, the scope of each, and flags 2 who also hold `ps.admin.users` (toxic combination warning).
3. **Given** a secretariat member is walled from case 90, **when** a tenant_admin without `case.wall:approve` asks *Can they?*, **then** the result says "Denied by a confidential restriction" with no wall details; **and when** the secretariat_lead asks, **then** the wall id and reason code are shown.
4. **Given** an assignment ended on 1 March, **when** the auditor asks *Can they?* as of 15 February, **then** the result is allow with that assignment as the path and the policy version deployed on 15 February.
5. **Given** a party with self-service explanation on, **when** they are refused "Submit filing" on a closed stage, **then** they see "The filing window for this stage closed on 12 May. You can ask the case manager for an extension." and nothing about other users.
6. **Negative**: **given** an auditor, **when** they run *Who can?* on a case, **then** the result lists principals and roles but no document titles; the query is audited.
7. **Negative**: **given** a simulation, **when** it completes, **then** no `authz_role_assignment` rows, notifications or grant epoch changes exist from it.

<!-- section:verification -->
## Verification method

- **Agreement test**: for the generated authorisation corpus, `explain().decision` equals `can().allow` for every case (thousands of cases per run); a mismatch fails CI.
- **Redaction tests** for AEX-FR-6 across wall and tier combinations.
- **Simulator isolation test**: runs in a read-only transaction (`SET TRANSACTION READ ONLY`) with draft grants supplied in memory; asserts no writes and no outbox events.
- **Performance test**: *Who can?* on a case with 500 participants and a tenant with 5,000 staff under 5 s p95; *Can they?* under 300 ms p95.
- **As-of test**: reconstruct a past decision from history and compare with the audited decision recorded at the time.

<!-- section:priority -->
## Priority

Must, phase 1: *Can they?* and simulator diff for role and assignment changes (needed by maker-checker). Should, phase 2: *Who can?*, *What can they?*, as-of queries, self-service explanation for members. Could: copilot natural-language questions ("why can't Rohan see the reply?") answered by calling the same API ([[APP-admin-copilot]]).

<!-- section:questions -->
## Open questions

- [ ] Should tenant auditors see the explainer for Nomology support grants (paths via `support_grant`)? Proposed yes, read-only. (Admin group, [[PKG-support-access-and-impersonation]])
- [ ] As-of window: limited to audit retention; confirm minimum 7 years for case-related decisions. (Legal)
- [ ] Self-service explanations for parties: default on for CORD tenants, off for arbitral institutions? (Product)

<!-- section:notes -->
## Notes

- The explainer never impersonates. It evaluates policies for a subject principal and returns data; it never renders the subject's screens with their data. That is deliberately different from support "view as" ([[PKG-support-access-and-impersonation]]).
- AI agents may call the explainer only with the invoking human's authority and only for principals that human can administer ([[PKG-non-human-principals]]).

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Yes: maker-checker on access changes needs a reviewable diff, and disputes about who saw what need reconstructable explanations.

<!-- check:unambiguous -->
### Unambiguous

Inputs, outputs (typed `Explanation`), redaction rules and performance targets are specified.

<!-- check:singular -->
### Singular

Umbrella plus nine single-rule requirements, each tested separately.

<!-- check:complete -->
### Complete and scoped

Covers three query types, simulation, redaction, self-service, audit, as-of queries, routes and API.

<!-- check:feasible -->
### Feasible

Re-uses policy code with a tracing evaluator; simulation uses a read-only transaction with in-memory draft grants.

<!-- check:verifiable -->
### Verifiable

Agreement, redaction, isolation, performance and as-of tests defined.

<!-- check:consistent -->
### Consistent

Uses decision reasons from [[PKG-policy-engine-permission-matrix]], wall confidentiality from [[PKG-ethical-walls-conflict-based]] and change states from [[PKG-configuration-lifecycle]].

<!-- check:traced -->
### Traced

From the CTO's request for full RBAC administration and the shared model's AI and maker-checker principles; forward to `packages/authz/src/explain/*`, `/admin/access/*` screens and tests.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "kind": "vendor",
    "title": "Salesforce Help: Permission Set Groups",
    "url": "https://help.salesforce.com/s/articleView?language=en_US&id=platform.perm_set_groups.htm&type=5",
    "vendor": "Salesforce"
  },
  {
    "id": "R2",
    "kind": "vendor",
    "title": "OpenFGA documentation: Concepts",
    "url": "https://openfga.dev/docs/concepts",
    "vendor": "OpenFGA (CNCF)"
  },
  {
    "id": "R3",
    "kind": "vendor",
    "title": "Cedar documentation: How Cedar authorization works",
    "url": "https://docs.cedarpolicy.com/auth/authorization.html",
    "vendor": "Cedar (AWS open source)"
  }
]
```

<!-- end -->
