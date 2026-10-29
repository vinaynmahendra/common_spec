---
id: "PKG-separation-of-duties"
title: "Separation of duties and maker-checker"
parent: "PKG-authorization"
order: 11
type: "requirement"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Maker-checker catalogue, checker eligibility, single-admin fallbacks, toxic permission combinations, time-limited exceptions and the rule that AI may only make, never check"
links: []
rev: 1
syncHash: "38b4afb94156a7a4"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.2.11 Separation of duties and maker-checker

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Maker-checker catalogue, checker eligibility, single-admin fallbacks, toxic permission combinations, time-limited exceptions and the rule that AI may only make, never check

<!-- section:statement -->
## Statement

**SOD-FR-0 (umbrella, EARS ubiquitous):** The platform shall prevent any single principal from both making and approving a change or act listed in the maker-checker catalogue, and shall prevent or flag any principal holding a toxic combination of permissions, unless an approved, time-limited exception exists.

Detailed requirements (each testable on its own):

| ID | EARS statement |
|---|---|
| SOD-FR-1 | When an operation in the maker-checker catalogue is submitted, the system shall hold it in `in_review` and shall not apply it until a different eligible checker approves it. |
| SOD-FR-2 | The system shall consider a checker eligible only if they hold the domain's approve, publish or write permission at a scope covering the change, are not the maker, are not a principal whose own access the change alters, and are a human. |
| SOD-FR-3 | If the maker edits a change after a checker has approved it, then the system shall return it to `in_review` and discard the approval. |
| SOD-FR-4 | When a tenant has only one eligible checker for a catalogue operation, the system shall apply the fallback in `access.sod.single_admin_fallback` (`block`, `owner_approves`, or `delayed_self_approval` with a 24-hour notice to all tenant_owners), never silently self-approve. |
| SOD-FR-5 | When an assignment would give a principal a toxic combination in block mode, the system shall refuse it; in warn mode it shall require a reason and flag it in access reviews. |
| SOD-FR-6 | The system shall refuse the same person acting as maker and checker on the same case act (for example preparing and approving a regulatory submission, or submitting and approving their own vendor bill). |
| SOD-FR-7 | AI agents and the admin copilot shall be able to act only as makers, never as checkers. |
| SOD-FR-8 | Where an SoD exception is approved, the system shall record the rule, person, reason, approver and an expiry no later than 90 days, and shall show the exception in access reviews. |
| SOD-FR-9 | The system shall report reciprocal approval pairs (A approves B and B approves A more than five times in 30 days) to security_admins monthly. |

<!-- section:rationale -->
## Rationale and source

- **Fraud and error**: changes to who can do what, security settings, money and legally effective acts are the classic targets of insider abuse; a second person is the standard control.
- **Procedural fairness**: institutions must show that case-affecting configuration (deadline rules, blueprints applied to running cases) was reviewed before it applied to parties.
- **Regulatory and audit**: ISO/IEC 27001:2022 Annex A 5.3 (segregation of duties) [R1]; SOC 2 CC6.1 and CC8.1 change authorisation [R2]; NIST SP 800-53 AC-5 (separation of duties) used as design reference [R3]. SEBI ODR reporting via MIIs expects controlled submissions; maker-checker on regulatory submissions is already a requirement of [[RPT-regulatory-and-aggregator]].
- **Shared model**: section 4 of the shared model requires maker-checker changes to have a second approver who is not the author; this node defines exactly which changes, who may check, and what happens in small tenants.
- **Pattern borrowed from**: Workday business process approvals with conditions and segmented security groups [R4]; access governance tools flag toxic combinations during access reviews.

<!-- section:acceptance -->
## Acceptance criteria

**Maker-checker catalogue (minimum; locked at platform scope, tenants may add more via `access.sod.extra_maker_checker_operations`)**

| Operation | Permission (maker) | Checker must hold | Notes |
|---|---|---|---|
| Publish or change a custom role or permission set | `role:create/update`, `permission_set:*` | `role:update` | Simulator diff attached ([[PKG-access-explainer]]) |
| Assign a privileged role | `role.privileged:assign` | `role.privileged:assign` | Checker cannot be the assignee |
| Grant or change an eligibility | `role.privileged:assign` | `access.elevation:approve` | |
| Reset another user's MFA | `user.mfa:update` | `user.mfa:update` or `tenant_owner` | |
| Change keys marked maker-checker in settings catalogues | `settings.*:write` | same write permission | e.g. turning off MFA for staff, shortening retention ([[PKG-settings-security-and-identity]], [[PKG-settings-data-and-privacy]]) |
| Publish a case-type blueprint or decision table | `workflow.definition:publish`, `rules.decision_table:publish` | `workflow.definition:approve` | Via [[PKG-configuration-lifecycle]] |
| Migrate running cases to a new blueprint version | `workflow.migration:publish` | secretariat with `ps.case.secretariat_supervisor` | [[WF-workflow-versioning]] |
| Create an integration connection or an API client with admin scopes | `integration.connection:create`, `api_client:create` | security_admin | |
| Change connector data policies or the tenant AI policy | `integration.data_policy:publish`, `ai.policy:configure` | security_admin | |
| Approve or lift an ethical wall | `case.wall:create` → `case.wall:approve`; lift `case.wall:delete` | second holder of `case.wall:approve`/`:delete` | [[PKG-ethical-walls-conflict-based]] |
| Refund, write-off, vendor bill approval | `case.payment:approve`, `case.vendor_bill:approve` | second finance holder above `access.sod.finance_dual_approval_threshold` | Below the threshold one approver who is not the submitter |
| Regulatory or aggregator submission | `report.regulatory:create` | `report.regulatory:approve` | |
| Release a legal hold; tenant data export; tenant offboarding | `data.legal_hold:delete`, `data.export:create`, `tenant:delete` | tenant_owner (another one) | |
| Platform: catalogue release, plan change, tenant suspension or region move, staff role grant | platform permissions | `platform_security` or another `platform_owner` | Platform tenant |

**Toxic combinations (system rules; tenants may add rules, not remove these)**

| Rule key | Combination | Default mode | Why |
|---|---|---|---|
| `sod.finance_issue_and_refund` | `case.invoice:create` + `case.payment:approve` | warn | Issue and refund your own invoices |
| `sod.vendor_bill_self` | `case.vendor_bill:create` + `case.vendor_bill:approve` | block (per item always blocked by SOD-FR-6) | Approve own bills |
| `sod.security_and_audit` | `settings.security:write` + sole holder of `audit.log:export` | warn | Change controls and control the evidence |
| `sod.admin_and_case_content` | any `ps.admin.*` + `case.document:read` at tenant scope | warn | Admin as back door to case files |
| `sod.reg_maker_checker` | `report.regulatory:create` + `report.regulatory:approve` | warn (per item always blocked) | |
| `sod.neutral_and_secretariat_same_case` | case role `presiding_neutral`/`tribunal_member` + `case_manager` on the same case | block | Independence of tribunal |
| `sod.party_and_staff_same_case` | case role `claimant`/`respondent`/counsel + `case_manager` or secretariat scope covering the case | block | Conflict of interest |
| `sod.integration_and_connector_policy` | `integration.connection:create` + `integration.data_policy:publish` | warn | Create a data flow and approve its policy |

**Scenarios**

1. **Given** Meera (tenant_admin) drafts a custom role "Desk supervisor", **when** she submits it, **then** it is `in_review`, the simulator diff shows 12 users gaining `case:export`, and the role has no effect until Arjun (tenant_admin) approves; **and when** Meera tries to approve it herself, **then** the approve button is absent and the API returns 403 `checker_not_eligible`.
2. **Given** Arjun approved, **when** Meera edits the role again before publish, **then** the approval is discarded (SOD-FR-3).
3. **Given** a CORD tenant with one tenant_admin and `single_admin_fallback = delayed_self_approval`, **when** the admin submits a privileged role assignment, **then** tenant_owners are notified, and the change applies automatically after 24 hours unless an owner rejects it; the audit records `approval_mode = delayed_self`.
4. **Given** `single_admin_fallback = block`, **when** there is no second eligible checker, **then** the change cannot be applied and the console explains how to add a checker.
5. **Given** the admin copilot drafts a settings change for user Kiran, **when** Kiran asks the copilot to approve it, **then** the copilot cannot (SOD-FR-7); Kiran may submit; another human must check.
6. **Given** a user holds `case.invoice:create`, **when** an admin assigns a role with `case.payment:approve`, **then** a warning names `sod.finance_issue_and_refund` and a reason is required; the assignment is flagged in the next access review.
7. **Given** Priya is case_manager on case 123, **when** someone seats Priya as co-neutral on the same case, **then** it is refused with `sod_conflict` (`sod.neutral_and_secretariat_same_case`).
8. **Negative**: **given** an exception for rule `sod.security_and_audit` expired yesterday, **when** the next access review starts, **then** the combination is listed as a violation and security_admins are alerted.

<!-- section:verification -->
## Verification method

- Unit and integration tests in `packages/authz/test/sod/*` for every catalogue row (maker cannot check; eligible checker can; ineligible checker refused), the edit-after-approval rule, and each fallback mode.
- Property test: for random assignment sequences, no principal ever ends with a blocked toxic combination without an active exception.
- Database: deferred constraint trigger asserts `approved_by_membership_id <> granted_by_principal` on assignments and change requests; tested directly.
- Inspection: the maker-checker catalogue in `packages/authz/catalogue/sod.yaml` is rendered into this node in CI.
- Demonstration to auditors: monthly SoD report (violations, exceptions, reciprocal approvals) from [[RPT-platform-security]].

<!-- section:priority -->
## Priority

Must, phase 1 (with the tenant admin console) for: role and privileged assignment maker-checker, settings keys marked maker-checker, blueprint publish, wall lift, regulatory submissions, single-admin fallback. Should, phase 2: tenant-defined toxic combinations, reciprocal-approval report, finance dual-approval threshold.

<!-- section:questions -->
## Open questions

- [ ] Default `single_admin_fallback` per blueprint: proposed `delayed_self_approval` for CORD tenants, `owner_approves` for arbitral institutions, `block` for SEBI ODR and court programmes. (Product, compliance)
- [ ] Finance dual-approval threshold default (proposed INR 1,00,000 / SGD 2,000 / USD 1,500 equivalent). (Finance)
- [ ] Should a tribunal's majority decision on an order count as maker-checker for `case.order:publish` in multi-member tribunals? Proposed: out of scope; the tribunal's own process governs. (Legal)

<!-- section:notes -->
## Notes

- Change requests and their states belong to [[PKG-configuration-lifecycle]] and the settings tables in [[PKG-settings-data-model]]; this node defines who may move a change from `in_review` to `approved`.
- Platform-side maker-checker uses the same engine in the regional platform tenant.
- The checker sees the full diff, the maker's reason, the simulator result (for access changes) and any toxic-combination warnings before approving; approval requires step-up.

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Yes. Without it any single tenant_admin could grant themselves case access, weaken security settings or apply untested blueprints to running cases; ISO 27001 A.5.3 and the shared model's maker-checker rule would be unmet.

<!-- check:unambiguous -->
### Unambiguous

The catalogue names each operation by permission key and the checker permission; eligibility is defined by four testable conditions (SOD-FR-2); fallbacks are enumerated values.

<!-- check:singular -->
### Singular

SOD-FR-0 is an umbrella; each SOD-FR-1 to SOD-FR-9 states one rule and is tested separately. The node is a capability-level requirement grouping, accepted for this platform's spec style.

<!-- check:complete -->
### Complete and scoped

Covers which operations, who may check, edits after approval, small tenants, toxic combinations, exceptions, AI actors and reporting; error responses `checker_not_eligible` and `sod_conflict` are defined.

<!-- check:feasible -->
### Feasible

Uses the existing change lifecycle, authz assignments and a database trigger; no new infrastructure.

<!-- check:verifiable -->
### Verifiable

Each catalogue row and scenario maps to automated tests; property tests cover toxic combinations; the deferred trigger is directly testable.

<!-- check:consistent -->
### Consistent

Matches shared-model section 4, uses catalogue keys from [[PKG-permission-catalogue]], and aligns with [[RPT-regulatory-and-aggregator]] and [[PKG-ethical-walls-conflict-based]] (second approver for lifts).

<!-- check:traced -->
### Traced

Sources: shared model section 4, ISO 27001 A.5.3 [R1], SOC 2 [R2], NIST AC-5 [R3]. Forward: `packages/authz/catalogue/sod.yaml`, `packages/authz/src/sod/*`, tests in `packages/authz/test/sod`, SoD report in [[RPT-platform-security]].

<!-- citations -->
## Citations

```json
[
  {
    "body": "ISO/IEC",
    "id": "R1",
    "ident": "27001",
    "kind": "standard",
    "title": "ISO/IEC 27001:2022 Information security management systems",
    "url": "https://www.iso.org/standard/27001",
    "version": "2022"
  },
  {
    "body": "AICPA",
    "id": "R2",
    "ident": "Trust Services Criteria",
    "kind": "standard",
    "title": "2017 Trust Services Criteria (with revised points of focus, 2022)",
    "url": "https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022",
    "version": "2017 (revised points of focus 2022)"
  },
  {
    "body": "NIST",
    "id": "R3",
    "ident": "SP 800-53 Rev. 5",
    "kind": "standard",
    "title": "NIST SP 800-53 Rev. 5, Security and Privacy Controls for Information Systems and Organizations (AC-2, AC-5, AC-6)",
    "url": "https://csrc.nist.gov/pubs/sp/800/53/r5/final",
    "version": "Rev. 5"
  },
  {
    "id": "R4",
    "kind": "vendor",
    "title": "Workday Education: Segment-based security",
    "url": "https://doc.workday.com/workday-education/en-us/course-manuals/security-for-administrators/segment-based-security.html",
    "vendor": "Workday"
  }
]
```

<!-- end -->
