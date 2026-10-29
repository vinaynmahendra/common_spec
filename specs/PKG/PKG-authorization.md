---
id: "PKG-authorization"
title: "Authorization"
parent: "PKG"
order: 2
type: "capability"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "Authorisation for every request, job, workflow step and AI tool call: scoped roles and permission sets, case-level roles, attribute conditions, deny-first rules (walls, SoD), elevation and break-glass, non-human principals, under forced RLS"
links: []
rev: 3
syncHash: "54c669749a85a06f"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.2 Authorization

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Authorisation for every request, job, workflow step and AI tool call: scoped roles and permission sets, case-level roles, attribute conditions, deny-first rules (walls, SoD), elevation and break-glass, non-human principals, under forced RLS

<!-- section:purpose -->
## Purpose and scope

`@nomology/authz` decides whether a principal may perform an action on a resource, for every request, job, workflow step and AI tool call, and produces the database filters that make list and search queries return only what the principal may see. Postgres forced RLS already guarantees tenant separation ([[MT-isolation-strategy]]); this package adds everything inside a tenant: roles and scoped assignments, case-level roles, side, case stage, document visibility tier, ethical walls, separation of duties, elevation, support access and non-human principal limits.

**How the parts fit**

| Concern | Node |
|---|---|
| Every permission (`resource:action`), its tier and who holds it | [[PKG-permission-catalogue]] |
| System roles, managed templates, custom roles, permission sets, muting, scoped assignments | [[PKG-roles-and-permission-sets]] |
| Case-level roles, side, tiers, conditions inside a case | [[PKG-rbac-abac-case-level-party]] |
| Policy code, decision flow, caching, persona matrix for case resources | [[PKG-policy-engine-permission-matrix]] |
| Ethical walls and need-to-know cases | [[PKG-ethical-walls-conflict-based]] |
| Just-in-time elevation, access requests, break-glass | [[PKG-jit-and-break-glass]] |
| Maker-checker and toxic combinations | [[PKG-separation-of-duties]] |
| Explainer and simulator | [[PKG-access-explainer]] |
| Service accounts, integration connections, AI agents, system workers | [[PKG-non-human-principals]] |
| Nomology staff access to tenant data | [[PKG-support-access-and-impersonation]] |
| Tables | [[PKG-authorization-data-model]] |
| Settings | [[PKG-settings-access-control]] |
| Periodic access reviews (control) | [[SEC-access-reviews]] |
| Admin screens | [[APP-user-and-access-admin]], [[APP-administration-model]] |

**Relies on this control:** every domain module, search ([[PKG-search]]), storage signed URLs ([[PKG-encryption-at-rest-signed-urls]]), notification recipient resolution ([[PKG-notifications]]), AI retrieval and tools ([[AI-rag]], [[WF-ai-steps-and-agents]]), automation rules ([[WF-automation-rules]]), exports and reports ([[RPT-report-infrastructure]]), the admin API ([[INT-tenant-admin-api]]) and the admin copilot ([[APP-admin-copilot]]).

**Model summary.** Role-based access with scoped assignments for tenant roles (scope depth borrowed from business-unit security models [R6]), relationship-style case roles derived from case records (in the spirit of relationship-based engines [R7]), attribute conditions for stage, side and tier (ABAC as described in NIST SP 800-162 [R8]), and deny rules that always override allow (the same combining rule as Cedar's forbid-overrides-permit [R9]).

<!-- section:assets -->
## Protected assets

| Asset family | Highest classification ([[SEC-data-classification]]) | Examples |
|---|---|---|
| Case record and parties | Case participants | Case metadata, party details, contact data |
| Pleadings and evidence | Case participants or one side only (before exchange) | Statement of claim, exhibits, witness statements |
| Tribunal material | Tribunal-only | Award drafts, deliberation notes, tribunal-internal messages, AI drafting workspace |
| Hearings, recordings, transcripts | Case participants (tenant policy) | Recordings, transcripts in progress |
| Neutral data | Tenant-internal and personal | Empanelment profiles, conflict declarations, fee rates |
| Financial | Tenant-internal / case participants | Invoices, payments, vendor bills, bank details |
| Tenant configuration | Tenant-internal | Blueprints, rules, templates, settings, SSO |
| Access configuration itself | Confidential | Roles, assignments, walls and their reasons, eligibilities, break-glass events |
| Audit and reports | Tenant-internal | Audit exports, MIS, regulator and aggregator reports |

<!-- section:actors -->
## Actors and roles

Canonical role keys from the shared model; full definitions in [[PKG-roles-and-permission-sets#actors]].

| Principal | Kind | Scope | Acquired by |
|---|---|---|---|
| `party`, `counsel`, `observer` | Tenant base role | Tenant (no case rights by itself) | Invitation accepted, self-registration, or aggregator intake ([[PKG-external-party-identity]]) |
| `claimant`, `respondent`, `claimant_counsel`, `respondent_counsel` | Case role | Case | Named as party, or active representation |
| `presiding_neutral`, `tribunal_member` | Case role | Case | Tribunal seat after accepted appointment; ends on unseating or close |
| `expert`, `witness`, `interpreter`, `transcriber`, `observer` (case) | Case role | Case, often time-bound | Added by case manager or tribunal; hearing assignment windows |
| `case_manager` | Case role (requires `secretariat`) | Case | Case assignment |
| `secretariat` | Tenant operational role | Tenant, unit or case type | Assigned by tenant_admin, user_admin, unit_admin |
| `secretariat_lead`, `case_finance_officer`, `reporting_viewer`, `regulatory_reporter`, `regulatory_approver`, `privacy_officer` | Managed role templates | Tenant or unit | Assigned by admins; privileged ones via maker-checker or JIT |
| `neutral`, `transcriber` | Tenant operational role | Tenant | Empanelment / onboarding by secretariat |
| `tenant_owner`, `tenant_admin`, `security_admin`, `user_admin`, `unit_admin`, `workflow_designer`, `integration_admin`, `content_admin`, `billing_admin`, `ai_admin`, `auditor` | Tenant administrative roles | Tenant (unit for unit_admin) | Platform at onboarding (first owner); then by admins under maker-checker and JIT rules |
| Custom roles (`custom:<slug>`) | Tenant-defined | As allowed | Tenant admins within bounds |
| `platform_owner`, `platform_admin`, `platform_support`, `platform_security`, `platform_billing`, `regional_ops` | Platform roles | Platform or region; tenant only under a grant | Workforce IdP + platform assignment, JIT for most ([[PKG-jit-and-break-glass]]) |
| `service_account`, `integration_connection`, `ai_agent` | Non-human | Tenant, unit, case type or case | [[PKG-non-human-principals]] |
| `system` (workers) | Non-human | One tenant per job | Declared purpose with fixed permissions, or on behalf of a recorded principal |

<!-- section:matrix -->
## Permission matrix

Summary at resource-family level. ✓ full, R read only, "own" own records only, "case" cases they participate in, "side" own side only, "scope" within the assignment's scope, ✗ none. The permission-level catalogue is [[PKG-permission-catalogue#matrix]]; the case-resource persona matrix with conditions is [[PKG-policy-engine-permission-matrix#matrix]] and is the source of truth for tests.

| Resource family | Party (case role) | Counsel (case role) | Tribunal (presiding / member) | case_manager | secretariat (scoped) | secretariat_lead | Transcriber (case) | case_finance_officer | Tenant admin roles | auditor | Support (grant) | Service account | AI agent (on behalf) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Case record | case R | case R | case R | ✓ | scope ✓ | scope ✓ | hearing metadata R | billing fields R | ✗ (counts only) | metadata R | per grant R | per scope | ∩ human |
| Pleadings / evidence | side ✓, other side R after exchange | same as party | case R | ✓ | scope ✓ | scope ✓ | ✗ | ✗ | ✗ | ✗ | per grant R | per scope | ∩ human |
| Tribunal-only material | ✗ | ✗ | ✓ | `access.case.secretariat_sees_tribunal_drafts` | same setting | same setting | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | tribunal human only, if AI policy allows |
| Hearings / recordings | case R (recordings per setting) | same | ✓ | ✓ | scope ✓ | scope ✓ | assigned ✓ (window) | ✗ | ✗ | ✗ | per grant R | per scope | ∩ human |
| Transcripts | R when released | R when released | R, release | ✓ | scope ✓ | scope ✓ | edit until submitted | ✗ | ✗ | ✗ | ✗ | ✗ | draft only |
| Neutral profiles and conflicts | disclosures R | disclosures R | own ✓ | panel R | panel R | ✓ | ✗ | fee rates R | ✗ | ✗ | per grant R | ✗ | ✗ |
| Invoices / payments | own R + pay | side R + pay | own vendor bills | R | scope R | approve vendor bills | own vendor bills | ✓ | ✗ (billing_admin: Nomology invoices only) | R | ✗ | scope R | ✗ |
| Tenant configuration | ✗ | ✗ | ✗ | ✗ | R (case settings) | R | ✗ | ✗ | per role ✓ | R | per grant | per scope | drafts via copilot |
| Users, roles, assignments | own | own | own | invite case participants | invite case participants | invite | own | own | ✓ per role (maker-checker for privileged) | R | per grant R | SCIM connection only | drafts via copilot |
| Walls | ✗ | ✗ | own (existence) | propose | propose | ✓ approve / lift (second approver) | ✗ | ✗ | ✗ | R (no reasons) | ✗ | ✗ | ✗ |
| Audit and exports | own sign-ins | own sign-ins | ✗ | case history | case history (scope) | scope | ✗ | ✗ | security_admin ✓ | ✓ | ✗ | SIEM export (scope) | ✗ |

<!-- section:policy -->
## Policy model

- **Layers**: (1) Postgres forced RLS on `tenant_id`, which application bugs cannot bypass; (2) `@nomology/authz` decisions for everything inside the tenant; (3) object-level checks at issue time for signed URLs and exports; (4) derived-copy rules: search index, notifications, AI retrieval, automation rules and caches use the same decision through `authz.where` or `authz.can` at read time.
- **Decision rule**: allow only if an active assignment (direct, group, case role, JIT, break-glass, support grant) gives the permission at a covering scope, the policy's conditions pass, the plan includes it, and no deny rule matches. Deny always overrides allow; default deny. Full flow and caching: [[PKG-policy-engine-permission-matrix#policy]].
- **Evaluation order**: authenticated and tenant matches host → principal checks (signed context, non-human ceilings, AI on-behalf intersection, support-grant constraints) → tenant or membership suspended → ethical walls and need-to-know lists (deny) → separation-of-duties runtime rules (deny self-approval) → explicit deny rules (case sealed, stage locks, legal hold for deletion) → allow rules with conditions → obligations (step-up, maker-checker, audit read, watermark) → default deny.
- **Policies are code** in `packages/authz/policies/*.ts`; tenants customise through roles, permission sets, scopes and settings ([[PKG-settings-access-control]]), never by writing policy.
- **Principle**: tenant administrators administer; they do not read case content unless they also hold an operational role that grants it. Adding case permissions to an admin role is flagged or blocked (`access.admin.case_content_in_admin_roles`).
- **Principle**: AI and automation never hold more than the human or role they act for, and never approve or publish ([[PKG-non-human-principals]]).

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat | Scenario | Mitigation | Residual |
|---|---|---|---|---|---|
| T1 | E | IDOR on case or document IDs | Counsel changes a document ID in a URL | Every load goes through `authz.assert` / `authz.where`; RLS stops cross-tenant; not-found and no-access return the same response | Low |
| T2 | I | Respondent sees claimant's unexchanged submissions | Visibility tier ignored in a list query | `authz.where` adds side and tier filters; matrix-generated negative tests | Low |
| T3 | I | Party reads tribunal-only award draft via search, notification or AI | Derived copy ignores tier | Search filter, notification recipient resolution and AI retrieval use the same policy | Low |
| T4 | E | Tenant admin grants self case access | Admin assigns `secretariat_lead` to self or builds a custom role with case permissions | Maker-checker on privileged assignment; self-assignment refused; admin-with-case-access flag; alert to other admins | Low |
| T5 | E | Long-running workflow acts after access removed | Temporal sends a filing reminder to removed counsel | Activities re-check permission at execution time; recipients resolved at send time; grant epochs make revocation immediate | Low |
| T6 | R | Disputed access | "The secretariat read our privileged exhibit" | Sensitive reads audited with policy and catalogue versions; as-of explainer | Low |
| T7 | E | Conflicted neutral keeps access | Wall not applied to existing cases | Walls are deny rules on every decision, including cached grant sets | Low |
| T8 | E | Support abuse | Staff browse case files | Tenant-approved, scoped, time-limited, tenant-visible grants | Low |
| T9 | E | Escalation through custom roles | user_admin builds a role containing `role.privileged:assign` | No-escalation rule, non-customisable permissions, maker-checker | Low |
| T10 | E | AI agent exceeds the user | Prompt injection triggers an export | Per-tool-call checks with intersected permissions; exports privileged and not grantable to AI | Low |
| T11 | E | Standing privilege abused | Dormant security_admin account compromised | Eligible-only privileged roles with JIT activation and step-up | Low |

<!-- section:failure -->
## Denial behaviour

- For resources whose existence is sensitive (cases, documents, parties), a denial returns **404 with the same body as not-found**, as required by [[APP-error-message-catalogue]]. For actions on a resource the user can see, return 403 with a reason the user can act on (`stage_closed`, `step_up_required`, `elevation_available`, `not_in_plan`).
- Wall-based denials never mention a conflict; they look like not-found or a generic "You cannot act on this case".
- Every denial of a sensitive or privileged action is audited (`authz.denied` with permission, policy and catalogue versions, reason code); routine list filtering is not audited per row.
- The UI hides actions the user cannot take and offers "request access" or "elevate" where a path exists ([[PKG-jit-and-break-glass]]); the server check is always authoritative.
- Members can see a plain-language reason for refusals on resources they can see, where self-service explanation is enabled ([[PKG-access-explainer]]).

<!-- section:requirements -->
## Security requirements

ASVS references are to OWASP ASVS **5.0** at chapter level [R1][R2]; requirement-level IDs to be added after checking against the 5.0.0 text. Old IDs AUTHZ-1 to AUTHZ-7 are kept as AUTHZ-FR-1 to AUTHZ-FR-7.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| AUTHZ-FR-1 | Every server entry point that reads or changes tenant data shall call `@nomology/authz` with a catalogue permission before acting. | V8 |
| AUTHZ-FR-2 | Access shall be denied unless an allow path exists and no deny rule (wall, stage lock, suspension, seal, SoD) matches. | V8 |
| AUTHZ-FR-3 | List and search queries shall apply `authz.where` filters in the database query, never by filtering after fetching. | V8 |
| AUTHZ-FR-4 | Denials for case-scoped resources shall be indistinguishable from not-found. | V8 |
| AUTHZ-FR-5 | Activities, jobs and agent tool calls acting for a principal shall re-evaluate the permission at execution time. | V8 |
| AUTHZ-FR-6 | Assignment of any role containing a privileged permission shall need step-up and a second approver ([[PKG-separation-of-duties]]). | V8 |
| AUTHZ-FR-7 | Every decision shall carry the policy bundle version and catalogue release, recorded in audit for sensitive actions. | V16 |
| AUTHZ-FR-8 | Revocation of any grant shall take effect on the principal's next request in the same region (grant epoch), and within 60 seconds for open realtime connections (hearing room, notifications stream). | V8 |
| AUTHZ-FR-9 | Tenant administrative roles shall not include case-content permissions by default. | V8 |
| AUTHZ-FR-10 | Non-human principals shall be bound by the ceilings in [[PKG-non-human-principals]]. | V8 |

<!-- section:verification -->
## Verification

- Matrix-generated tests: each cell of [[PKG-policy-engine-permission-matrix#matrix]] and each permission and role in [[PKG-permission-catalogue]] becomes allow and deny tests per condition and scope, run against real Postgres with RLS through PgBouncer ([[TST-multi-tenant-isolation-tests]]) [R3].
- Entry-point coverage: a CI check enumerates Server Actions, tRPC procedures, Route Handlers, Temporal Activities, BullMQ handlers and AI tools, and fails if one has no declared permission or `@public` annotation.
- Explainer agreement test ([[PKG-access-explainer]]).
- Revocation timing test: revoke, then the next request is denied; realtime channels drop within 60 s.
- Pen test: IDOR, tier leakage, workflow-time checks, support access, custom-role escalation, AI agent tool abuse.

<!-- section:questions -->
## Open questions

- [ ] Do institution tenants need secretariat access to tribunal-only drafts for scrutiny? Now a setting (`access.case.secretariat_sees_tribunal_drafts`), default off; legal and product to confirm per institution's rules.
- [ ] Should a second RLS layer enforce `tribunal_only` in the database? Trade-off: stronger guarantee vs policy complexity and query cost. (Security lead)
- [ ] Record the policy engine decision (TypeScript policies, not a separate policy language) as an ADR; see [[PKG-policy-engine-permission-matrix#questions]]. (Security lead)
- [x] Case role `tribunal_secretary` and the managed role templates (`secretariat_lead`, `case_finance_officer`, `reporting_viewer`, `regulatory_reporter`, `regulatory_approver`, `privacy_officer`) are accepted (decision D6); see [[PKG-roles-and-permission-sets#actors]].

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Tenant separation is enforced by forced RLS before any policy runs; policies see only rows of the current tenant. The tenant comes from the session, cross-checked with the host, never from the request body. Users in two tenants have independent memberships, assignments and case roles; nothing is carried across. Support access is a separate tenant-approved grant; non-human principal contexts are signed and tenant-bound.

<!-- check:enforcement -->
### Enforcement points and bypass paths

One package is called from every entry point (Server Components, Server Actions, tRPC, Route Handlers, public and admin API, webhooks, Temporal Activities and signal handlers, BullMQ jobs, exports, AI tools, automation actions). CI fails on any entry point without a declared permission or `@public`. Signed URLs are issued only after `authz.assert` and live 60 seconds. Search, notification recipient resolution and AI retrieval call the same policies.

<!-- check:lifecycle -->
### Grant lifecycle and privileged access

Case roles end with the domain record; tenant roles carry end dates (privileged within 1 year or eligible-only with JIT); SCIM deprovisioning removes memberships; break-glass and JIT end by database clock; access reviews catch the rest ([[SEC-access-reviews]]). Revocation is effective on the next request through grant epochs.

<!-- check:resilience -->
### Failure modes and secrets

Policies run in-process. Dependencies: the database (fail closed if unavailable) and Redis for cached grant sets keyed by epoch (fall back to the database). Decisions are never cached across requests. Target overhead p95 ≤ 5 ms per decision.

<!-- check:residency -->
### Data residency

All grant data, decisions and audit events live in the tenant's home region; the catalogue is replicated identically to each region; no decision needs a cross-region call.

<!-- check:audit -->
### Audit trail

Audited: denials of sensitive actions, all role, assignment, permission set and eligibility changes with approver, case role changes, wall changes, elevations, break-glass, support grants and every action under them, explainer queries, and sensitive reads (tribunal-only documents, KYC files, exports). Each event carries policy and catalogue versions.

<!-- check:observability -->
### Detection and alerting

Security events `nomo.sec.authz_fail`, `nomo.sec.ethical_wall_block`, `nomo.sec.privilege_changed`, `nomo.sec.break_glass_used` ([[OBS-security-events]]); alerts on bursts of not-found denials per principal (IDOR probing), privileged assignments outside business hours, break-glass, and any decision for an unknown permission.

<!-- check:compliance -->
### Framework and legal mapping

ISO/IEC 27001:2022 Annex A 5.3, 5.15, 5.18, 8.2, 8.3 [R4]; SOC 2 CC6.1–CC6.3 [R5]; GDPR Article 32 and DPDP reasonable security safeguards. Evidence: generated permission catalogue and matrix, test results per release, access review exports, elevation and break-glass registers.

<!-- check:testing -->
### Verification and testing

Tests are generated from the catalogue, roles and matrix (allow and deny per cell, condition and scope) and run against real Postgres with RLS via PgBouncer; they include Temporal Activities, BullMQ handlers and AI tools. Every past access-control bug gets a regression test referencing its ticket.

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
    "body": "OWASP",
    "id": "R3",
    "ident": "Cheat Sheet Series",
    "kind": "standard",
    "title": "OWASP Authorization Testing Automation Cheat Sheet",
    "url": "https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Testing_Automation_Cheat_Sheet.html"
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
    "id": "R6",
    "kind": "vendor",
    "title": "Microsoft Learn: Create or edit business units (Power Platform)",
    "url": "https://learn.microsoft.com/en-us/power-platform/admin/create-edit-business-units",
    "vendor": "Microsoft"
  },
  {
    "id": "R7",
    "kind": "web",
    "publisher": "USENIX ATC 2019 / Google Research",
    "title": "Zanzibar: Google's Consistent, Global Authorization System",
    "url": "https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/"
  },
  {
    "body": "NIST",
    "id": "R8",
    "ident": "SP 800-162",
    "kind": "standard",
    "title": "NIST SP 800-162, Guide to Attribute Based Access Control (ABAC) Definition and Considerations",
    "url": "https://csrc.nist.gov/pubs/sp/800/162/upd2/final"
  },
  {
    "id": "R9",
    "kind": "vendor",
    "title": "Cedar documentation: How Cedar authorization works",
    "url": "https://docs.cedarpolicy.com/auth/authorization.html",
    "vendor": "Cedar (AWS open source)"
  }
]
```

<!-- end -->
