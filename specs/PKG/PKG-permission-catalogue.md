---
id: "PKG-permission-catalogue"
title: "Permission catalogue"
parent: "PKG-authorization"
order: 9
type: "feature"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "Every permission in the platform as resource:action, grouped by domain, with scopes, risk tier, step-up, maker-checker, customisability, non-human eligibility and the system roles that hold it"
links: []
rev: 1
syncHash: "053b3e2e7a00f06e"
createdAt: "2026-10-28T08:00:00Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.2.9 Permission catalogue

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Every permission in the platform as resource:action, grouped by domain, with scopes, risk tier, step-up, maker-checker, customisability, non-human eligibility and the system roles that hold it

<!-- section:purpose -->
## Purpose and scope

The permission catalogue is the single, versioned list of every permission in the platform, written as `<resource>:<action>` ([[PKG-authorization]] naming rules). Every check in `@nomology/authz`, every role and permission set, every API scope, every admin-console screen that shows "who can do what" and every generated test refers to keys from this catalogue. A permission that is not in the catalogue cannot be granted, checked or displayed.

**What this node owns**
- The catalogue itself (section *Permission matrix* below), grouped by domain, with the system roles that hold each permission.
- The attributes of each permission: allowed scopes, risk tier, step-up, maker-checker, whether tenants may put it into custom roles, whether non-human principals may hold it, and plan entitlement.
- The rules for adding, changing and retiring permissions.

**What it does not own**
- How permissions are bundled into roles and permission sets: [[PKG-roles-and-permission-sets]].
- Conditions that decide access to one particular case, document or hearing (side, stage, visibility tier): [[PKG-rbac-abac-case-level-party]] and the persona matrix in [[PKG-policy-engine-permission-matrix#matrix]].
- Storage of the catalogue: [[PKG-authorization-data-model]] (`authz_permission`, `authz_catalogue_release`).
- Public API OAuth scopes: [[PKG-api-clients-and-keys]] maps each scope to a fixed list of catalogue keys.

**Source of truth.** `packages/authz/catalogue/permissions.yaml` in the monorepo. CI generates from it: the TypeScript `Permission` union type, the `authz_permission` seed for each regional database, the tenant-facing permission reference at `/admin/access/permissions`, the documentation tables below and the allow/deny test skeletons. The tables in this node are the reviewed copy; CI fails if they differ from the YAML (see *Verification*).

**Action vocabulary.** `read`, `list`, `create`, `update`, `delete`, `export`, `approve`, `publish`, `assign`, `impersonate`, `configure` from the shared model, plus `write` for settings catalogues only (used across all `PKG-settings-*` nodes as `settings.<catalogue>:write`). Legal acts and other verbs are mapped onto this vocabulary so the list stays small (for example complete a task → `case.task:update`, replay a webhook delivery → `webhook.delivery:update`, execute a migration → `workflow.migration:publish`, install a plugin → `plugin:create`, run a simulation → `workflow.simulation:create`):

| Legal or business act | Permission form | Example |
|---|---|---|
| Submit a filing | `create` on the filing | `case.filing:create` |
| Register a case for administration | `approve` on the case | `case:approve` |
| Sign an award | `approve` on the award | `case.award:approve` |
| Issue an order, serve an award, release a transcript | `publish` | `case.order:publish`, `case.award:publish` |
| Join a hearing | `read` on the hearing room | `case.hearing.room:read` |
| Appoint a neutral | `assign` on the neutral | `neutral:assign` |
| Lift an ethical wall | `delete` on the wall | `case.wall:delete` |
| Decide a challenge | `approve` on the challenge | `neutral.challenge:approve` |

<!-- section:assets -->
## Protected assets

| Asset | Classification ([[SEC-data-classification]]) | Why it matters |
|---|---|---|
| `permissions.yaml` and the generated catalogue release | Internal (published to tenants as reference) | A wrong tier or a missing `customisable: false` flag lets tenants build roles that defeat the platform's protections |
| `authz_permission` rows in each regional database | Internal | Read by the decision point on every request; must match the deployed code version |
| Catalogue release history (`authz_catalogue_release`) | Internal | Evidence of what a permission meant on a given date, needed for access disputes and audits |
| Mapping of permissions to system roles | Internal | Defines the default security posture of every tenant |
| Mapping of public API scopes to permissions | Internal | Wrong mapping lets an API client exceed what a tenant admin approved |

<!-- section:actors -->
## Actors and roles

| Actor | Relation to the catalogue | How acquired |
|---|---|---|
| Nomology security lead | CODEOWNER of `packages/authz/catalogue`; approves every new or changed permission | Engineering role |
| Platform engineering | Proposes permissions with each new feature (the feature PR must add the keys) | Engineering role |
| `platform_owner` | Publishes a catalogue release to production regions (maker-checker with `platform_security`) | Platform role, [[PKG-roles-and-permission-sets#actors]] |
| `platform_security` | Second approver for catalogue releases that add `privileged` permissions or change tiers | Platform role |
| `tenant_owner`, `tenant_admin`, `security_admin` | Read the catalogue in the console; build custom roles from `customisable` permissions | Tenant system roles |
| `auditor` | Reads the catalogue and its history | Tenant system role |
| Service accounts and AI agents | Hold only permissions flagged as grantable to non-human principals | [[PKG-non-human-principals]] |

<!-- section:matrix -->
## Permission matrix

**Column legend**
- **Scopes**: where an assignment carrying this permission may be scoped: `P` platform, `R` region, `T` tenant, `U` unit, `CT` case type, `C` case. A permission held at `T` covers every unit and case in the tenant; at `U` it covers the unit, its child units (when the assignment says so) and the cases owned by them; at `C` it covers one case.
- **Tier**: `std` standard, `sens` sensitive (reads or changes confidential or personal data, or affects many records), `priv` privileged (changes who can do what, security posture, or has legal or financial effect).
- **SU**: step-up authentication (fresh MFA within 5 minutes, [[PKG-mfa-session-management-device]]) required.
- **MC**: maker-checker required ([[PKG-separation-of-duties]]); `cfg` means it follows the configuration change lifecycle ([[PKG-configuration-lifecycle]]) with a second approver.
- **Cust**: may tenants include this permission in custom roles or custom permission sets? `y` yes, `n` no (system roles only).
- **NH**: may non-human principals hold it? `sa` service accounts, `ai` AI agents, `int` integration connections, `—` never ([[PKG-non-human-principals]]).
- **Held by**: system roles holding the permission by default. Tenant roles in plain text, case-level roles in *italics*. "own" and "side" are conditions applied by the policy ([[PKG-policy-engine-permission-matrix#matrix]]); the holder list says who can ever have the permission, not that they can use it on every record.

Platform roles are listed only in group J. `tenant_owner` holds every permission in groups F to I and K unless stated. Neither `tenant_owner` nor `tenant_admin` holds any case-content permission (groups A to D) by default: administration is not a route to case files ([[PKG-authorization#policy]]).

**A. Case record and parties**

| Permission | Meaning | Scopes | Tier | SU | MC | Cust | NH | Held by |
|---|---|---|---|---|---|---|---|---|
| `case:list` | See the case in lists and search | T U CT C | std | | | y | sa ai | secretariat; *all case-level roles* |
| `case:read` | Open the case record (metadata, parties, timeline) | T U CT C | std | | | y | sa ai | secretariat; *all case-level roles* (transcriber, interpreter, witness: hearing metadata only) |
| `case:create` | Create a draft case or file a new matter | T U CT | std | | | y | sa int | secretariat; party, counsel (where `case.intake.party_self_filing` allows) |
| `case:approve` | Register a submitted case for administration and assign a reference | T U CT C | sens | | | y | — | secretariat (supervisor set); *case_manager* |
| `case:update` | Edit case metadata and custom fields | T U CT C | std | | | y | sa | secretariat; *case_manager* |
| `case.status:update` | Run lifecycle commands of the case state machine ([[WF-entity-state-machines]]) | T U CT C | sens | per command | | y | sa | secretariat; *case_manager*; *presiding_neutral* (tribunal commands only) |
| `case:assign` | Assign or change the case manager, unit or case team | T U CT | sens | | | y | — | secretariat (supervisor set) |
| `case:configure` | Change case confidentiality level (`standard`, `confidential`, `sealed`) and case-overridable settings | T U CT C | priv | ✓ | | y | — | secretariat (supervisor set); *case_manager* (case-overridable settings only) |
| `case:export` | Export the full case file | T U CT C | priv | ✓ | | y | — | secretariat (supervisor set); *case_manager* |
| `case:delete` | Delete a draft case that was never submitted | T U C | sens | | | y | sa | secretariat; *creator of the draft* (own) |
| `case.audit:read` | Read the case's audit history | T U CT C | sens | | | y | — | secretariat; *case_manager*; auditor (metadata, no content) |
| `case.party:create` / `:update` / `:delete` | Add, correct or remove parties | T U CT C | sens | | | y | sa int | secretariat; *case_manager* |
| `case.representative:create` | Add counsel or an authorised representative | T U CT C | sens | | | y | — | secretariat; *case_manager*; *claimant*, *respondent* (own party); *claimant_counsel*, *respondent_counsel* (co-counsel, own side) |
| `case.representative:delete` | End a representation | T U CT C | sens | | | y | — | secretariat; *case_manager*; *claimant*, *respondent* (own party) |
| `case.participant:assign` | Add or remove experts, witnesses, interpreters, observers and transcribers on the case | T U CT C | sens | | | y | — | secretariat; *case_manager*; *presiding_neutral* (tribunal-appointed experts) |
| `case.note.internal:read` / `:create` | Institution-internal notes on a case | T U CT C | sens | | | y | ai (read) | secretariat; *case_manager* |
| `case.message:list` / `:create` | Read and send case messages to all participants | C | std | | | y | ai (list) | *all case-level roles except witness*; secretariat |
| `case.message.tribunal:create` | Send a message to the tribunal only | C | sens | | | y | — | *presiding_neutral*, *tribunal_member*, *tribunal_secretary*, *case_manager* |
| `case.notice:create` | Serve a formal notice ([[DOM-service-of-notices-and-proof]]) | T U CT C | sens | | | y | sa | secretariat; *case_manager* |
| `case.application:create` | Make a procedural application (for example an extension request) | C | std | ✓ | | y | — | *claimant*, *respondent*, *claimant_counsel*, *respondent_counsel* |
| `case.representative:approve` | Approve a representation claimed by counsel ([[PKG-external-party-identity]]) | T U CT C | sens | | | y | — | secretariat; *case_manager* |
| `case.task:create` / `:update` | Create a task; claim, update and complete tasks assigned to the user or their queue ([[WF-human-tasks]]). A task definition may name a narrower completion permission | T U CT C | std | per task definition | | y | sa; ai (create, as a proposal only) | secretariat; *case_manager*; *all case-level roles* (tasks assigned to them) |
| `case.task:assign` | Assign, reassign and bulk-claim tasks | T U CT C | std | | | y | sa | secretariat (supervisor set); *case_manager* |

**B. Filings, documents, bundles, orders and awards**

| Permission | Meaning | Scopes | Tier | SU | MC | Cust | NH | Held by |
|---|---|---|---|---|---|---|---|---|
| `case.filing:create` | Submit a filing (claim, response, application) | T U CT C | sens | ✓ | | y | sa int | *claimant*, *respondent*, *claimant_counsel*, *respondent_counsel* (side); secretariat and *case_manager* (on behalf, reason required) |
| `case.filing:delete` | Withdraw a filing before acceptance | C | sens | | | y | — | filer (own); *case_manager* |
| `case.filing:approve` | Admit or reject a filing | C | sens | | | y | — | *case_manager*; *presiding_neutral* |
| `case.deadline:read` | See deadlines | C | std | | | y | sa ai | *all case-level roles*; secretariat |
| `case.deadline:update` | Extend, stay or restart a deadline | T U CT C | priv | ✓ | | y | — | *presiding_neutral*; *case_manager* (where rules allow) |
| `case.document:list` / `:read` | See and open documents, subject to visibility tier | T U CT C | sens | | | y | sa ai | secretariat; *all case-level roles* (tier rules) |
| `case.document:export` | Download a document or obtain a signed URL | T U CT C | sens | | | y | sa | as `case.document:read` except *witness* |
| `case.document:create` | Upload a document | T U CT C | std | | | y | sa int | *parties and counsel* (side); *tribunal* (tribunal folder); *expert* (own report); *transcriber* (transcripts); secretariat |
| `case.document:update` | Change document metadata or visibility tier | T U CT C | priv | ✓ | | y | — | secretariat; *case_manager*; *presiding_neutral* |
| `case.bundle:create` | Assemble a hearing bundle ([[DOM-ebundling]]) | C | std | | | y | ai | *case_manager*; secretariat; *counsel* (where `access.case.parties_prepare_bundles`) |
| `case.bundle:publish` | Issue a bundle to participants | C | sens | | | y | — | *case_manager*; secretariat |
| `case.order:create` / `:read` (draft) | Draft procedural orders | C | sens | | | y | ai (draft assist) | *presiding_neutral*, *tribunal_member*, *tribunal_secretary* |
| `case.order:approve` | Concur in a draft order (multi-member tribunal) | C | sens | ✓ | | y | — | *presiding_neutral*, *tribunal_member* |
| `case.order:publish` | Issue a procedural order | C | priv | ✓ | | y | — | *presiding_neutral* (or as the rules allow) |
| `case.award:create` / `:read` (draft) | Draft the award; drafts are tribunal-only | C | priv | | | y | ai (draft assist) | *presiding_neutral*, *tribunal_member* |
| `case.award:approve` | Sign the award | C | priv | ✓ | | n | — | *presiding_neutral*, *tribunal_member* |
| `case.award:publish` | Serve the signed award on the parties | C | priv | ✓ | | n | — | *case_manager*; secretariat (supervisor set) |
| `case.wall:read` | See walls on a case (not reasons, unless approver) | T U CT C | sens | | | y | — | secretariat; *case_manager* |
| `case.wall:create` | Propose or create an ethical wall | T U CT C | priv | | | y | — | secretariat; *case_manager* (proposed only) |
| `case.wall:approve` | Approve a proposed wall | T U CT | priv | ✓ | MC | y | — | secretariat (supervisor set) |
| `case.wall:delete` | Lift a wall | T U CT | priv | ✓ | MC | n | — | secretariat (supervisor set) |

**C. Hearings, recordings, transcripts**

| Permission | Meaning | Scopes | Tier | SU | MC | Cust | NH | Held by |
|---|---|---|---|---|---|---|---|---|
| `case.hearing:read` | See hearing schedule and details | C | std | | | y | sa ai | *all case-level roles*; secretariat |
| `case.hearing:create` / `:update` | Schedule, reschedule, cancel a hearing | T U CT C | std | | | y | sa | *presiding_neutral*; *tribunal_member*; *tribunal_secretary*; *case_manager*; secretariat |
| `case.hearing.slot:create` | Propose availability slots | C | std | | | y | — | *all case-level roles except witness and observer* |
| `case.hearing.room:read` | Join the virtual hearing room | C | std | | | y | — | *all case-level roles* (transcriber and interpreter within the assignment window) |
| `case.recording:read` | Watch a hearing recording | C | sens | | | y | ai (transcription pipeline only) | *tribunal*; *case_manager*; *transcriber* (assigned); parties and counsel where `access.case.recordings_to_parties` |
| `case.recording:export` | Download a recording | C | priv | ✓ | | y | — | *case_manager*; secretariat (supervisor set) |
| `case.transcript:read` | Read a released transcript | C | std | | | y | ai | *all case-level roles except witness* |
| `case.transcript:update` | Edit a transcript before submission | C | std | | | y | ai (ASR draft) | *transcriber* (assigned, until submitted); *case_manager* |
| `case.transcript:publish` | Release a transcript to participants | C | sens | | | y | — | *presiding_neutral*; *case_manager* |

**D. Neutrals, transcribers, money**

| Permission | Meaning | Scopes | Tier | SU | MC | Cust | NH | Held by |
|---|---|---|---|---|---|---|---|---|
| `neutral.profile:read` / `:update` | Own neutral profile | T | std | | | n | — | neutral (own) |
| `neutral.profile:list` | Search the neutral panel | T U | sens | | | y | ai | secretariat; *case_manager* |
| `neutral.empanelment:approve` | Admit or remove a neutral from the panel | T U | priv | ✓ | | y | — | secretariat (supervisor set) |
| `neutral.conflict:create` | Declare a conflict or disclosure | T | std | | | n | — | neutral, transcriber (own) |
| `neutral.conflict:read` | Read conflict declarations | T U | sens | | | y | — | secretariat (supervisor set) |
| `neutral:assign` | Appoint a neutral to a case | T U CT C | priv | ✓ | | y | — | secretariat (supervisor set); *case_manager* (where rules allow) |
| `neutral.challenge:create` | File a challenge to a neutral | C | sens | ✓ | | y | — | *claimant*, *respondent*, *claimant_counsel*, *respondent_counsel* |
| `neutral.challenge:approve` | Decide a challenge | T U CT | priv | ✓ | | n | — | secretariat (supervisor set) |
| `transcription.job:read` | See own transcription jobs | T | std | | | n | — | transcriber (own) |
| `transcription.job:assign` | Assign jobs and segments | T U | std | | | y | sa | secretariat |
| `transcription.review:approve` | Approve a quality review | T U | sens | | | y | — | secretariat |
| `case.fee:read` | See fee assessment | T U CT C | sens | | | y | sa | secretariat; *case_manager*; parties and counsel (own) |
| `case.invoice:read` | See invoices | T U CT C | sens | | | y | sa int | secretariat; parties and counsel (own side) |
| `case.invoice:create` | Issue an invoice | T U | priv | ✓ | | y | sa | `case_finance_officer` template |
| `case.payment:create` | Pay an invoice | C | sens | | | n | — | *claimant*, *respondent*, *counsel* (own side) |
| `case.payment:approve` | Approve a refund or write-off | T U | priv | ✓ | MC | y | — | `case_finance_officer` template |
| `case.vendor_bill:create` | Submit own vendor bill | T | std | | | n | — | neutral, transcriber (own) |
| `case.vendor_bill:approve` | Approve a vendor bill | T U | priv | ✓ | MC | y | — | `case_finance_officer` template; secretariat (supervisor set) |

**E. Reports, search and AI on case content**

| Permission | Meaning | Scopes | Tier | SU | MC | Cust | NH | Held by |
|---|---|---|---|---|---|---|---|---|
| `report:list` / `report:read` | Tenant reports and dashboards (aggregates) ([[RPT-platform-stats]]) | T U | std | | | y | ai | secretariat; auditor; `reporting_viewer` template |
| `report:export` | Export report data | T U | sens | ✓ | | y | sa | `reporting_viewer` template; auditor |
| `report.schedule:create` | Schedule a recurring report email | T U | sens | | | y | — | `reporting_viewer` template |
| `report.regulatory:create` | Prepare a regulator or aggregator submission ([[RPT-regulatory-and-aggregator]]) | T | priv | | MC | y | sa | `regulatory_reporter` template |
| `report.regulatory:approve` | Check and approve a submission | T | priv | ✓ | MC | y | — | `regulatory_approver` template |
| `report.regulatory:publish` | Send the approved submission | T | priv | ✓ | | y | sa | `regulatory_approver` template |
| `ai.generation:create` | Use an AI feature (summaries, drafting help, agents) on content the user can already read, where the AI policy allows the feature for that user, unit, case type and case ([[AI-tenant-ai-policy]]); held through the feature's `ps.ai.<feature>_user` set | T U CT C | sens | | | y | ai (published agents and AI steps only, intersected with the invoker) | secretariat; *case_manager*; *presiding_neutral*; *tribunal_member*; others where [[PKG-settings-ai]] allows. Admin roles: admin copilot and agent test consoles only |
| `ai.output:approve` | Accept AI output so that it takes effect ([[AI-human-in-the-loop]]) | C | sens | | | y | — | the approver role named for the feature: *case_manager*, *presiding_neutral*, *tribunal_member*; never a service account or agent |
| `ai.case_restriction:update` | Restrict, or lift a restriction on, AI use in one case | C | sens | | | y | — | *case_manager* (own restrictions); *presiding_neutral* |
| `ai.party_opt_out:create` | Record an AI opt-out for a party's own submissions (where `ai.parties.opt_out_mode` allows) | C | std | | | n | — | *claimant*, *respondent*, *claimant_counsel*, *respondent_counsel* (own side); *case_manager* (on a party's behalf) |

**F. Users, groups, units, roles and access governance** (tenant scope; `unit_admin` holds the user and unit rows at `U` scope only)

| Permission | Meaning | Scopes | Tier | SU | MC | Cust | NH | Held by |
|---|---|---|---|---|---|---|---|---|
| `user:list` / `user:read` | List members and see profiles | T U | sens | | | y | sa ai | tenant_admin, user_admin, unit_admin, security_admin, auditor |
| `user:create` | Invite a user | T U | sens | | | y | sa int | tenant_admin, user_admin, unit_admin; secretariat (case participants only, via the case) |
| `user:update` | Change profile, status, unit | T U | sens | | | y | sa int | tenant_admin, user_admin, unit_admin |
| `user:delete` | Deactivate a member and end sessions | T U | priv | ✓ | | y | sa int | tenant_admin, user_admin, security_admin |
| `user.session:delete` | Revoke another user's sessions | T U | priv | ✓ | | n | — | security_admin, tenant_admin, user_admin |
| `user.mfa:update` | Reset another user's MFA (remove factors for assisted recovery) | T U | priv | ✓ | MC (administrative targets) | n | — | security_admin, tenant_owner; user_admin (non-administrative members only, after identity re-proof) |
| `user.session:list` | List a member's sessions and devices ([[PKG-mfa-session-management-device]]) | T U | sens | | | y | — | security_admin, user_admin, tenant_owner |
| `user.self:read` / `:update` | Own profile, factors, passkeys, sessions and devices | T (own) | std | ✓ (factor changes) | | n | — | every member (own only) |
| `identity.verification:create` | Start own identity verification ([[PKG-external-party-identity]]) | T (own) | std | | | n | — | party, counsel (own) |
| `identity.verification:read` | See a verification outcome (level, method, date) | T U C | sens | | | y | — | security_admin, tenant_admin, auditor; *case_manager*; the person (own) |
| `identity.verification:approve` | Perform a manual verification (document review, video) | C | priv | ✓ | | y | — | *case_manager* (never self or a colleague) |
| `identity.verification.evidence:read` | Open verification evidence documents | C | priv | ✓ | | n | — | *case_manager* (audited); the person (own) |
| `user:impersonate` | View the product as another user | — | priv | ✓ | | n | — | **No tenant role** (decision D6). Only Nomology staff under a tenant-approved grant ([[PKG-support-access-and-impersonation]]). Tenant admins use the permission simulator (`access.simulator:read`, [[PKG-access-explainer]]) |
| `group:list` / `:create` / `:update` / `:delete` | Manage groups and IdP group mappings | T U | sens | | | y | sa int | tenant_admin, user_admin, unit_admin (unit) |
| `unit:list` / `:create` / `:update` / `:delete` | Manage organisation units | T U | sens | | cfg | y | — | tenant_admin, unit_admin (child units) |
| `role:list` / `role:read` | See roles and their permissions | T | std | | | y | ai | tenant_admin, user_admin, security_admin, auditor |
| `role:create` / `:update` / `:delete` | Manage custom roles | T | priv | ✓ | MC | n | — | tenant_admin, security_admin |
| `permission_set:create` / `:update` / `:delete` | Manage custom permission sets | T | priv | ✓ | MC | n | — | tenant_admin, security_admin |
| `role:assign` | Assign roles (standard tier) to users or groups | T U CT C | sens | | | y | int (SCIM group mapping only) | tenant_admin, user_admin, unit_admin (unit) |
| `role.privileged:assign` | Assign any role that contains a `priv` permission | T U | priv | ✓ | MC | n | — | tenant_owner, tenant_admin, security_admin |
| `access.request:create` | Request access or a role | T U C | std | | | n | — | every member |
| `access.request:approve` | Approve an access request | T U C | sens | | | y | — | user_admin, unit_admin, secretariat (case access within scope) |
| `access.elevation:approve` | Approve a just-in-time activation ([[PKG-jit-and-break-glass]]) | T U | priv | ✓ | | n | — | tenant_owner, security_admin |
| `access.break_glass:read` | Review break-glass events | T | priv | | | n | — | tenant_owner, security_admin, auditor |
| `access.review:create` | Start and manage access review campaigns ([[SEC-access-reviews]]) | T U | sens | | | y | — | security_admin, tenant_admin |
| `access.review:read` | See review results | T U | sens | | | y | — | security_admin, auditor, tenant_admin |
| `access.explainer:read` | Explain why a user can or cannot act ([[PKG-access-explainer]]) | T U | sens | | | y | ai | tenant_admin, user_admin, security_admin, auditor |
| `access.simulator:read` | Simulate a role or assignment change | T | sens | | | y | ai | tenant_admin, security_admin |
| `bulk.job:create` | Start a bulk import, update or export job ([[APP-bulk-admin-operations]]); every row is also checked against its own op permission | T U | sens | over threshold | MC over threshold | y | sa | user_admin, tenant_admin, workflow_designer; unit_admin (unit) |
| `report.admin:read` | Admin reports: seats, adoption, configuration health | T U | std | | | y | — | tenant_admin, billing_admin, auditor |
| `service_account:create` / `:update` / `:delete` | Manage service accounts ([[PKG-non-human-principals]]) | T | priv | ✓ | MC | n | — | integration_admin, tenant_admin |
| `ai_agent.principal:assign` | Grant permission sets to an AI agent principal | T U CT | priv | ✓ | MC | n | — | ai_admin with security_admin as checker |

**G. Settings** (one resource per settings catalogue; `:read` is held by every tenant administrative role and by auditor)

| Permission | Catalogue | Tier | SU | MC | Held by (write) |
|---|---|---|---|---|---|
| `settings.security:write` | [[PKG-settings-security-and-identity]] | priv | ✓ | per key | security_admin, tenant_owner (tenant_admin reads only) |
| `settings.access:write` | [[PKG-settings-access-control]] | priv | ✓ | per key | security_admin, tenant_owner |
| `settings.cases:write` | [[PKG-settings-cases-and-workflows]] (`case.*` keys) | sens | | per key | workflow_designer, tenant_admin; unit_admin (unit) |
| `settings.workflow:write` | [[PKG-settings-cases-and-workflows]] (`workflow.*` keys) | sens | | per key | workflow_designer, tenant_admin; unit_admin (unit) |
| `settings.notifications:write` | [[PKG-settings-notifications]] | std | | per key | integration_admin (channels and senders), content_admin, tenant_admin; unit_admin (unit) |
| `settings.integrations:write` | [[PKG-settings-integrations]] | sens | ✓ | per key | integration_admin, tenant_admin |
| `settings.branding:write` | [[PKG-settings-branding-content]] | std | | per key | content_admin, tenant_admin; unit_admin (unit) |
| `settings.ai:write` | [[PKG-settings-ai]] | priv | ✓ | per key | ai_admin, tenant_admin |
| `settings.data:write` | [[PKG-settings-data-and-privacy]] | priv | ✓ | per key | security_admin, tenant_owner, tenant_admin; `privacy_officer` template |
| `settings.billing:write` | [[PKG-settings-billing-and-plans]] | sens | ✓ | per key | billing_admin, tenant_owner |
| `settings.personal:write` | [[PKG-settings-personal]] | std | | — | every user (own values); content_admin, tenant_admin (tenant and unit defaults) |
| `settings.platform:write` | [[PKG-settings-platform-operations]], and the platform, region and offering values of every catalogue | priv | ✓ | per key | platform_admin; regional_ops (region values, own region); platform_billing (billing keys) |

All `settings.*:write` permissions have Scopes `T U CT C` as allowed by each key's catalogue row, are `Cust: y` except `settings.security`, `settings.access` and `settings.data` (`n`), and are never held by AI agents (the admin copilot proposes drafts with the invoking human's authority, [[APP-admin-copilot]]).

Every catalogue also has `settings.<catalogue>:read` (every tenant administrative role and `auditor`; `settings.platform:read` for platform roles) and `settings.<catalogue>:approve` (the checker for that catalogue's maker-checker keys; held by the same roles as `:write`, and the checker must also hold `config.change_set:approve` and must not be the author). `unit_admin` holds `settings.cases`, `settings.workflow`, `settings.notifications` and `settings.branding` `:write` at `U` scope only, for keys that allow `unit`; for the `security`, `access` and `ai` catalogues it may only tighten the keys those catalogues mark as unit tighten-only, and `data` unit values are set by tenant-scoped holders. Case-scope values use `case:configure` (group A), held through *case_manager*. There are no area-level settings permissions such as `settings.data.retention:*`: high-risk keys are protected by maker-checker instead (decision D2).

**H. Workflow, content, integrations and configuration lifecycle**

| Permission | Meaning | Scopes | Tier | SU | MC | Cust | NH | Held by |
|---|---|---|---|---|---|---|---|---|
| `workflow.definition:read` / `:create` / `:update` | Author case-type blueprints ([[WF-workflow-authoring-studio]]) | T CT | sens | | | y | ai (draft) | workflow_designer, tenant_admin |
| `workflow.definition:publish` | Publish a blueprint version ([[WF-workflow-versioning]]) | T CT | priv | ✓ | cfg | y | — | workflow_designer, tenant_admin |
| `workflow.definition:approve` | Second approval of a blueprint version | T CT | priv | ✓ | | y | — | workflow_designer, tenant_admin (not the author) |
| `workflow.migration:create` | Plan and dry-run a migration of running cases to a new blueprint version ([[WF-workflow-versioning]]) | T CT | sens | | | n | ai (draft) | workflow_designer |
| `workflow.migration:approve` | Approve a migration plan and its recorded legal basis (not the author; two approvers for procedural migrations) | T CT | priv | ✓ | MC | n | — | secretariat (supervisor set), tenant_admin |
| `workflow.migration:publish` | Execute an approved migration | T CT | priv | ✓ | | n | — | workflow_designer, secretariat (supervisor set) |
| `workflow.sla_policy:update` / `:publish` | SLA policies ([[WF-sla-and-business-calendars]]) | T U CT | sens | | cfg | y | ai (draft) | workflow_designer, tenant_admin; unit_admin (unit) |
| `workflow.calendar:update` / `:publish` | Business schedules and closures for internal SLAs ([[WF-sla-and-business-calendars]]); procedural seat calendars are computed by [[PKG-calendars-and-deadline]] | T U | sens | | cfg | y | — | workflow_designer, tenant_admin; unit_admin (unit calendar) |
| `workflow.queue:configure` | Task queues and routing ([[WF-human-tasks]]) | T U | std | | | y | — | tenant_admin, workflow_designer; unit_admin (unit queues) |
| `workflow.ai_step:configure` | Add or change AI steps in a blueprint ([[WF-ai-steps-and-agents]]) | T CT | priv | ✓ | cfg | n | — | workflow_designer, where the tenant AI policy allows workflow AI steps |
| `metadata.field:update` / `:approve` | Custom fields ([[PKG-metadata-management-entity]]) | T CT | sens | | cfg | y | ai (draft) | workflow_designer, tenant_admin (update); tenant_admin, tenant_owner (approve, not the author) |
| `workflow.automation:create` / `:update` / `:publish` | Automation rules ([[WF-automation-rules]]) | T U CT | sens | | cfg | y | ai (draft) | workflow_designer, tenant_admin |
| `workflow.simulation:create` | Run simulations ([[WF-workflow-simulation]]) | T CT | std | | | y | ai | workflow_designer |
| `rules.decision_table:create` / `:update` / `:approve` / `:publish` | Decision tables (approve is the maker-checker step, not the author) ([[PKG-rules-and-decision-engine]]) | T CT | priv (publish) | ✓ | cfg | y | ai (draft) | workflow_designer |
| `form:create` / `:update` / `:publish` | Forms ([[PKG-forms-and-form-builder]]) | T CT | sens | | cfg | y | ai (draft) | workflow_designer, content_admin |
| `template.document:create` / `:update` / `:approve` / `:publish` | Document templates ([[PKG-document-and-notification]]); approve is the maker-checker step (not the author) | T U CT | sens | | cfg | y | ai (draft) | content_admin, tenant_admin; unit_admin (unit variants, update only) |
| `template.notification:create` / `:update` / `:approve` / `:publish` | Notification templates, same rules | T U CT | sens | | cfg | y | ai (draft) | content_admin, tenant_admin; unit_admin (unit variants, update only) |
| `template.document:configure` / `template.notification:configure` | Lock a template to a statutory or institution-prescribed format | T | priv | ✓ | | n | — | tenant_owner |
| `notify.policy:read` / `:update` / `:approve` / `:publish` | Notification policies ([[PKG-notification-policies]]) | T U CT | sens | | cfg | y | ai (draft) | tenant_admin, content_admin; unit_admin (unit, read and update) |
| `notify.suppression:update` | Manage the suppression list (bounces, opt-outs) | T | sens | | | n | — | tenant_admin, content_admin |
| `notify.delivery:read` | Delivery status and logs | T U | sens | | | y | sa | tenant_admin, content_admin, auditor |
| `notify.evidence:export` | Export proof-of-delivery evidence for a notice | T U C | sens | ✓ | | y | — | tenant_admin, secretariat; *case_manager* |
| `monitoring.threshold:update` | Operational thresholds and alerts ([[PKG-thresholds-and-alert]]) | T U | std | | cfg | y | — | tenant_admin; unit_admin (unit, within bounds) |
| `personalisation.view:publish` | Share a saved view with a unit or the whole tenant ([[PKG-personalisation]]) | T U | std | | | y | — | secretariat, tenant_admin; unit_admin (unit) |
| `content.terminology:update` / `:publish` | Terminology and copy ([[PKG-tenant-terminology-and-copy]]) | T U | std | | cfg | y | ai (draft) | content_admin |
| `brand.theme:update` / `:publish` | Branding ([[PKG-branding-and-theming]]) | T U | std | ✓ (publish) | | y | — | content_admin |
| `integration.connection:read` / `:create` / `:update` / `:delete` | Integration connections ([[INT-connections-admin]]) | T | priv | ✓ | MC (create) | n | — | integration_admin |
| `integration.connection:assign` | Limit a connection to units | T U | sens | | | n | — | integration_admin; unit_admin (unit, where allowed) |
| `integration.connection.credential:update` | Replace or rotate a connection's credential (write-only) | T | priv | ✓ | | n | — | integration_admin |
| `integration.connector:read` | Browse the connector catalogue | T | std | | | y | — | integration_admin, tenant_admin, workflow_designer |
| `integration.usage:read` | Connection usage, health and call logs | T | std | | | y | sa | integration_admin, tenant_admin, auditor |
| `integration.data_policy:read` | See connector data policies and their decisions ([[INT-connector-data-policies]]) | T | std | | | y | — | integration_admin, security_admin, tenant_admin, auditor |
| `integration.data_policy:update` | Draft a connector data policy | T | priv | ✓ | cfg | n | — | integration_admin, security_admin |
| `integration.data_policy:approve` / `:publish` | Approve (not the author) and publish a connector data policy | T | priv | ✓ | MC | n | — | security_admin |
| `integration.data_policy.exemption:create` / `:approve` | Request or approve a time-limited exemption | T | priv | ✓ | MC | n | — | integration_admin (create); security_admin (approve) |
| `integration.data_policy.violation:read` | See blocked transfers | T | sens | | | y | sa (SIEM export) | security_admin, integration_admin, auditor |
| `plugin:read` | Browse the plugin catalogue ([[INT-plugin-model]]) | T | std | | | y | — | tenant_admin, integration_admin, workflow_designer, auditor |
| `plugin.request:create` | Request a plugin install | T | std | | | n | — | any staff membership, where `integration.apps.install_policy` is `request_and_approve` |
| `plugin:create` / `:delete` | Install, upgrade or uninstall a plugin | T | priv | ✓ | MC (admin scopes) | n | — | integration_admin, security_admin |
| `plugin:configure` | Configure an installed plugin | T | sens | | | n | — | integration_admin |
| `plugin:publish` | Publish a tenant-private configuration plugin | T | priv | ✓ | MC | n | — | tenant_admin, where `integration.plugins.private_publishers` allows |
| `api_client:create` / `:update` / `:delete` | API clients ([[PKG-api-clients-and-keys]]) | T | priv | ✓ | MC (admin scopes) | n | — | integration_admin, security_admin, tenant_owner; tenant_admin may only revoke keys in an emergency ([[PKG-api-clients-and-keys]]) |
| `api_client.key:create` / `:delete` | Rotate and revoke keys | T | priv | ✓ | | n | sa (rotate own) | integration_admin |
| `api_client:list` | List API clients and usage | T | std | | | y | sa (own) | integration_admin, security_admin, tenant_owner, tenant_admin, auditor; client owner (own) |
| `api_client:approve` | Approve admin scopes on an API client (not one's own request) | T | priv | ✓ | | n | — | security_admin, tenant_owner |
| `oauth_app:configure` | Manage the OAuth app allow-list | T | priv | ✓ | | n | — | security_admin, tenant_owner |
| `oauth_app.consent:create` / `:delete` | Grant one's own consent to an OAuth app; revoke another user's consent | T | sens | | | n | — | every member (create, own); security_admin, tenant_owner (delete) |
| `webhook.endpoint:create` / `:update` / `:delete` | Webhook endpoints ([[APP-webhooks-outbound]]) | T | sens | ✓ | | y | — | integration_admin |
| `webhook.endpoint:read` | List endpoints with status and failure rate | T | std | | | y | — | integration_admin, auditor |
| `webhook.delivery:read` / `:update` | Delivery log; replay a delivery or a time range | T | sens | | | y | sa | integration_admin |
| `webhook.delivery:approve` | Approve a bulk replay above the threshold (not the requester) | T | sens | | MC | n | — | integration_admin, security_admin |
| `webhook.event:list` | Search the tenant's events (30 days) | T | sens | | | y | sa | integration_admin, auditor |
| `ai.policy:read` | Read the tenant AI policy ([[AI-tenant-ai-policy]]) | T U | std | | | y | — | every tenant administrative role, auditor; operational roles see a read-only summary |
| `ai.policy:configure` | Edit an AI policy draft | T U | priv | ✓ | cfg | n | — | ai_admin, tenant_admin, tenant_owner; security_admin (`ai.data.*`, `ai.models.*`, `ai.retention.*` only); unit_admin (own unit, narrowing only) |
| `ai.policy:approve` | Approve an AI policy change as checker (with `config.change_set:approve`; not the author) | T | priv | ✓ | MC | n | — | ai_admin, tenant_admin, tenant_owner; security_admin (required checker for data, model and retention sections) |
| `ai.policy:publish` | Publish an approved AI policy | T | priv | ✓ | MC | n | — | ai_admin, tenant_admin, tenant_owner |
| `ai.notice:approve` | Accept the AI notice for the tenant | T | priv | ✓ | | n | — | tenant_owner |
| `ai.budget:update` | Raise AI budgets and quotas within the entitlement ([[AI-cost-controls]]); lowering is allowed to the same holders without approval | T U | sens | | | n | — | ai_admin, tenant_admin, tenant_owner; unit_admin (own unit, lower only) |
| `ai.audit:read` | Read AI audit records ([[AI-ai-audit-and-transparency]]); reading conversation text also needs a recorded reason | T | sens | | | y | — | ai_admin, tenant_admin, tenant_owner, security_admin, auditor |
| `ai.audit:export` | Export AI audit records | T | sens | ✓ | | y | — | tenant_owner, security_admin, auditor |
| `ai.knowledge:read` | Search tenant knowledge collections as an agent tool | T U CT | std | | | n | ai (published agents only) | users of the agent, through the agent |
| `ai.agent:create` / `:update` / `:publish` | Tenant-configured agents ([[AI-agent-configuration]]); `:update` includes suspending an agent at once | T U CT | priv (publish) | ✓ | cfg | n | — | ai_admin |
| `ai.usage:read` | AI usage and cost ([[RPT-platform-ai-usage-analytics]]) | T | std | | | y | — | ai_admin, billing_admin, auditor |
| `config.change_set:read` | See change sets, diffs and the review queue ([[PKG-configuration-lifecycle]], [[APP-admin-change-history]]); diffs only for domains the viewer administers | T U CT | std | | | n | ai (admin copilot, within the invoking admin's rights) | every tenant administrative role, auditor |
| `config.change_set:approve` | Approve a change set in `in_review` (only where the checker also holds the domain's write or approve permission, and is not the author) | T U CT | priv | ✓ | — | n | — | any administrative role, per domain |
| `config.package:export` / `:create` / `:publish` | Export, import and apply configuration packages ([[PKG-configuration-packages]]) | T | priv | ✓ | MC | n | — | tenant_admin |
| `config.sandbox:create` | Create or refresh a configuration sandbox | T | sens | | | n | — | tenant_admin, workflow_designer |

**I. Audit, data, billing, tenant**

| Permission | Meaning | Scopes | Tier | SU | MC | Cust | NH | Held by |
|---|---|---|---|---|---|---|---|---|
| `audit.log:read` | Search the tenant audit log ([[APP-admin-change-history]]) | T U | sens | | | y | sa (SIEM export) | auditor, security_admin, tenant_admin |
| `audit.log:export` | Export audit events | T | sens | ✓ | | y | sa | auditor, security_admin |
| `data.legal_hold:create` / `:delete` | Place or release a legal hold ([[PKG-data-retention-legal-hold-and]]) | T U C | priv | ✓ | MC (release) | n | — | security_admin, tenant_owner |
| `data.export:create` | Bulk tenant data export | T | priv | ✓ | MC | n | — | tenant_owner |
| `data.dsr:approve` | Approve the response to a data principal request ([[SEC-data-principal-rights-requests]]) | T | priv | ✓ | | n | — | security_admin (or a custom privacy officer role) |
| `support.grant:read` / `:approve` | See and approve Nomology support access | T | priv | ✓ | | n | — | tenant_owner, tenant_admin, security_admin can hold it; the roles that actually approve are set by `access.support.approvers` (default `tenant_owner`, `security_admin`; [[PKG-settings-access-control]]) |
| `support.consent:configure` | Choose which kinds of Nomology support access the tenant allows ([[PKG-support-access-and-impersonation]]) | T | priv | ✓ | MC | n | — | tenant_owner |
| `billing.subscription:read` / `:update` | Plan, seats, add-ons ([[BIL-plans-entitlements-and-usage]]) | T | sens | ✓ (update) | | n | — | billing_admin, tenant_owner |
| `billing.account:update` | Billing contacts and plan change requests | T | std | | | n | — | billing_admin, tenant_owner |
| `billing.invoice:read` | Nomology invoices to the tenant | T | sens | | | y | sa | billing_admin, tenant_owner, auditor |
| `tenant:update` | Tenant profile (name, contacts); default language is the setting `locale.languages.default` | T | sens | ✓ | | n | — | tenant_owner, tenant_admin |
| `tenant:delete` | Request tenant offboarding ([[MT-tenant-lifecycle]]) | T | priv | ✓ | MC | n | — | tenant_owner (checker: a second tenant_owner, or Nomology account management where only one exists) |

**J. Platform (Nomology staff only; never customisable, never in tenant roles)**

| Permission | Meaning | Scopes | Tier | SU | MC | Held by |
|---|---|---|---|---|---|---|
| `platform.tenant:list` / `:read` | Tenant registry (no tenant data) | P R | sens | | | platform_admin, platform_support, platform_security, platform_billing, regional_ops |
| `platform.tenant:create` / `:update` | Provision and change tenants ([[APP-tenant-onboarding-wizard]]) | P R | priv | ✓ | MC (suspend, region move) | platform_admin, regional_ops (region) |
| `platform.tenant:delete` | Execute offboarding deletion | P R | priv | ✓ | MC | platform_owner |
| `platform.support_grant:create` | Request support access to a tenant | P R | priv | ✓ | — | platform_support |
| `platform.support_grant:approve` | Second approver for break-glass support access | P | priv | ✓ | — | platform_security |
| `platform.staff_role:assign` | Grant platform roles to staff | P | priv | ✓ | MC | platform_owner |
| `platform.catalogue:publish` | Publish a permission catalogue release | P | priv | ✓ | MC | platform_owner with platform_security |
| `platform.blueprint:publish` | Publish a tenant blueprint ([[PKG-configuration-packages]]) | P | priv | ✓ | MC | platform_admin |
| `platform.feature_flag:update` | Release flags ([[PKG-feature-flags]]) | P R | sens | ✓ | | platform_admin |
| `platform.plan:update` | Plans and entitlements | P | priv | ✓ | MC | platform_billing |
| `platform.audit:read` / `:export` | Platform audit log and security events; export needs step-up | P R | sens | ✓ (export) | | platform_security, platform_owner |
| `platform.elevation:approve` | Approve staff just-in-time elevation | P | priv | ✓ | | platform_security, platform_owner |
| `platform.tenant:approve` | Approve tenant deletion after the export window (with DPO sign-off), or a region move | P R | priv | ✓ | MC | platform_owner |
| `platform.tenant.security:configure` | Emergency tightening of one tenant's security (force MFA, revoke sessions); tenant notified within 1 hour | P R | priv | ✓ | MC | platform_security |
| `platform.operations:configure` | Maintenance windows and platform or tenant banners | P R | sens | | | regional_ops, platform_admin |
| `platform.workflow:update` | Operate Temporal workflows and BullMQ jobs (retry, cancel, terminate, replay dead letters) | R | priv | ✓ | | regional_ops |
| `platform.feature_flag.killswitch:update` | Operate kill switches, including `ai.killswitch` ([[PKG-feature-flags]]) | P R | priv | ✓ | | platform_admin (on call), platform_support (tier 2), platform_security |
| `platform.plan:approve` | Second approval of contract overrides and grants above the discount threshold ([[BIL-plans-entitlements-and-usage]]) | P | priv | ✓ | MC | platform_billing (not the maker), platform_owner |
| `platform.integration.data_policy:update` / `:approve` | Platform floors for connector data policies | P R | priv | ✓ | MC | platform_admin (update); platform_security (approve) |
| `platform.plugin:publish` / `:delete` | Publish or withdraw a first-party plugin version ([[INT-plugin-model]]) | P | priv | ✓ | MC | platform_admin (maker); platform_security (checker) |
| `platform.ai.exception:approve` | Approve an out-of-region AI processing exception | P | priv | ✓ | MC | platform_security with Nomology legal |

**K. Identity and authentication** (owned by [[PKG-authentication]] and its children; tenant scope)

| Permission | Meaning | Scopes | Tier | SU | MC | Cust | NH | Held by |
|---|---|---|---|---|---|---|---|---|
| `auth.connection:read` | See SSO connections and their status ([[PKG-sso-saml-oidc-per-tenant]]) | T | sens | | | y | — | security_admin, tenant_owner, tenant_admin, auditor |
| `auth.connection:create` / `:update` | Draft or change an SSO connection | T | priv | ✓ | cfg | n | — | security_admin, tenant_owner |
| `auth.connection:publish` | Enable a connection after a successful test sign-in in the last 24 hours | T | priv | ✓ | cfg | n | — | security_admin, tenant_owner |
| `auth.domain:create` | Claim and verify an email domain ([[PKG-domain-verification]]) | T | priv | ✓ | | n | — | security_admin, tenant_owner |
| `auth.provisioning:configure` | SCIM, JIT and invitation policy ([[PKG-user-provisioning-scim]]) | T | priv | ✓ | cfg | n | — | security_admin, tenant_owner |
| `auth.policy:read` | See authentication policies, strengths, network zones and factor coverage ([[PKG-authentication-policies]]) | T U | std | | | y | — | security_admin, tenant_owner, tenant_admin, user_admin, auditor; unit_admin (unit) |
| `auth.policy:update` / `:publish` | Draft and publish authentication policies | T | priv | ✓ | cfg | n | — | security_admin, tenant_owner |
| `auth.policy:approve` | Approve an authentication policy change (not one's own) | T | priv | ✓ | | n | — | security_admin, tenant_owner |
| `auth.strength:create` | Define a custom authentication strength | T | priv | ✓ | cfg | n | — | security_admin, tenant_owner |
| `auth.network_zone:update` | Manage network zones | T | priv | ✓ | cfg | n | — | security_admin, tenant_owner |
| `auth.policy_decision:list` | Read the authentication policy decision log | T U | sens | | | y | sa (SIEM export) | security_admin, tenant_owner, tenant_admin, auditor; unit_admin (unit) |
| `auth.policy_decision:export` | Export the decision log | T | sens | ✓ | | y | sa | security_admin, tenant_owner, auditor |
| `auth.signin_event:list` | Read sign-in history | T U | sens | | | y | sa | security_admin, tenant_owner, tenant_admin, user_admin, auditor; every member (own) |

<!-- section:policy -->
## Policy model

**Permission definition (YAML).** Each entry in `packages/authz/catalogue/permissions.yaml`:

```yaml
- key: case.document:update
  resource: case.document
  action: update
  description: Change document metadata or visibility tier
  scopes: [tenant, unit, case_type, case]
  tier: privileged          # standard | sensitive | privileged
  step_up: true
  maker_checker: none       # none | required | config_lifecycle
  customisable: true        # tenants may use it in custom roles / sets
  non_human: []             # subset of [service_account, ai_agent, integration_connection]
  entitlement: null         # plan feature key from BIL-plans-entitlements-and-usage, e.g. feature.ebundling
  audit_read: false         # obligation to audit every successful use
  conditions: [document_tier, own_side, stage]   # condition families the policy applies
  introduced_in: 2026.11
  deprecated_in: null
  replaced_by: null
```

**Rules**
1. **Naming**: resources are singular, dot-separated from general to specific (`case.hearing.room`); actions come only from the vocabulary in *Purpose and scope*. Lint rejects anything else.
2. **One meaning per key.** A key is never reused for a different meaning. A change in meaning is a new key plus deprecation of the old one.
3. **Tier rules.** A permission is `privileged` if it: changes roles, assignments, walls or security settings; has legal effect on a case (issue, sign, serve, extend deadlines, appoint, decide challenges); moves money; exports in bulk; or changes data retention. Privileged permissions always require step-up and are never grantable to AI agents.
4. **Entitlement gating.** If a permission has an `entitlement`, it is ineffective while the tenant's plan does not include that feature ([[BIL-plans-entitlements-and-usage]]); the explainer shows "not in plan" rather than "denied".
5. **Deprecation.** A deprecated key keeps working for two catalogue releases and is shown with a warning in custom roles that contain it; a migration maps it to `replaced_by` in system roles automatically and in custom roles after tenant-admin confirmation.
6. **Release.** A catalogue release is a numbered, signed artefact (`2026.11.0`). It is published per region with the application release that uses it ([[DEP-environment-promotion-and-multi]]); the database seed and the code must have the same release number, checked at worker start-up (fail closed on mismatch).
7. **Public API scopes** are defined as named lists of catalogue keys ([[PKG-api-clients-and-keys]]); a scope can never include a permission with `non_human` not containing `service_account`.

**Pattern sources.** Fine-grained, independently assignable permissions grouped into sets follow Salesforce permission sets [R3]; the custom-role-from-allowed-permissions model with an explicit "cannot grant what you do not hold" rule follows Okta custom admin roles [R4]; scope depth (one record, unit, whole organisation) follows Dataverse privilege access levels [R5].

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat | Scenario | Mitigation | Residual |
|---|---|---|---|---|---|
| T1 | E | Feature ships with no permission | A new endpoint checks `case:update` instead of a new specific key, so anyone who can edit metadata can also run the new action | Feature PR template requires catalogue entries; CODEOWNER review by security lead; entry-point CI check requires a catalogue key per procedure | Low |
| T2 | E | Permission mis-tiered | A legally consequential action marked `standard` lacks step-up and can be put in custom roles | Tier rules lint (keywords such as `approve`, `publish`, `export`, `assign` on case resources default to `privileged` unless justified); security review | Low |
| T3 | E | Tenant builds a role that breaks platform protections | Custom role combining `case.award:publish` with tenant-admin permissions | `customisable: n` for award signing and serving, wall lifting, MFA reset and others; toxic-combination checks ([[PKG-separation-of-duties]]) | Low |
| T4 | E | AI agent gets a privileged permission | An agent configured with `case.order:publish` | `non_human` attribute enforced at assignment time and again at decision time | Very low |
| T5 | T | Catalogue in database differs from code | A region runs code 2026.12 with catalogue 2026.11, so a new permission is missing and an old meaning is applied | Version check at start-up; decision point fails closed for unknown keys | Low |
| T6 | R | "That permission did not mean that when I granted it" | Dispute about historical meaning | Catalogue releases are immutable and kept for 10 years; audit events carry the catalogue release | Low |

<!-- section:failure -->
## Denial behaviour

- A check for a key that is not in the loaded catalogue release denies and raises `authz.unknown_permission` (alert, severity high), never a silent allow.
- A permission blocked by plan entitlement returns 403 with reason `not_in_plan` for visible resources, so the UI can show an upgrade message to admins; parties and counsel see the generic message from [[APP-error-message-catalogue]].
- Deprecated permissions behave normally but appear in the role editor with "deprecated, replaced by …".

<!-- section:requirements -->
## Security requirements

ASVS references are to OWASP ASVS 5.0 at chapter level [R1][R2].

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| PCAT-FR-1 | Every permission checked anywhere in code shall be a key in the loaded catalogue release; the `Permission` type shall be generated from `permissions.yaml`. | V8 |
| PCAT-FR-2 | Each catalogue entry shall define scopes, tier, step-up, maker-checker, customisable, non-human eligibility, entitlement and condition families. | V8 |
| PCAT-FR-3 | Permissions of tier `privileged` shall require step-up and shall not be grantable to AI agent principals. | V8 |
| PCAT-FR-4 | Permissions marked `customisable: false` shall be rejected by the custom role and permission set editors and APIs. | V8 |
| PCAT-FR-5 | Platform permissions (group J) shall never appear in a tenant role, permission set or API scope. | V8 |
| PCAT-FR-6 | A catalogue release shall be immutable, numbered and recorded in `authz_catalogue_release`; every audit event of an authorisation decision shall carry the release number. | V16 |
| PCAT-FR-7 | When the code and database catalogue releases differ, workers and web servers shall refuse to start. | V8 |
| PCAT-FR-8 | The tenant console shall show the catalogue at `/admin/access/permissions` with description, tier, and which roles in the tenant hold each permission. | — |
| PCAT-FR-9 | No tenant role shall hold `user:impersonate`. | V8 |
| PCAT-FR-10 | Every permission key used in any specification node or in code shall appear in this catalogue (decision D10); a CI check scans the spec tree and the code for `<resource>:<action>` keys and fails on any key not listed. API scopes (`admin.users:write`, `cases:read` and so on) are not permissions: each maps to catalogue keys in [[INT-tenant-admin-api#auth]] and [[PKG-api-clients-and-keys]]. | V8 |

<!-- section:verification -->
## Verification

- **Catalogue lint** (`pnpm authz:lint`): key format, vocabulary, tier rules, no duplicate meaning, every key referenced by a policy and by at least one role or explicit `unassigned: true`.
- **Doc sync**: CI renders the tables in this node from `permissions.yaml` and fails on a difference.
- **Entry-point coverage**: every tRPC procedure, Route Handler, Server Action, Temporal Activity and BullMQ handler declares the permission key(s) it checks; CI fails if a declared key is missing from the catalogue [R6 Annex A 8.3 evidence].
- **Generated tests**: for each permission, allow tests for each holding role and deny tests for a role that does not hold it, run against real Postgres with RLS ([[TST-multi-tenant-isolation-tests]]).
- **Release check**: a regional smoke test reads `authz_catalogue_release` and compares with the deployed build.

<!-- section:questions -->
## Open questions

- [x] `write` is an allowed action for settings only, as `settings.<catalogue>:write` (decision D2).
- [ ] Should `case:approve` (registration) be split from acceptance of jurisdiction for institutions that treat these as separate secretariat acts? (Product, with [[DOM-cases]])
- [x] `case_finance_officer` is a managed role template (decision D6).
- [ ] Retention of catalogue releases: proposed 10 years to cover the longest case and limitation period; confirm with legal. (Legal)
- [ ] Should party and counsel permissions for `case.recording:read` be governed by the case-type blueprint instead of a tenant setting? (Product)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

The catalogue is platform-level reference data (no `tenant_id`, read-only to `nomo_app`); it defines permissions but grants nothing. Grants are tenant-owned rows under forced RLS ([[PKG-authorization-data-model#tenancy]]). Platform permissions (group J) cannot be placed in tenant roles (PCAT-FR-5), so no tenant administrator can obtain cross-tenant capability through the catalogue.

<!-- check:enforcement -->
### Enforcement points and bypass paths

Code can only check keys that exist (generated type), and every entry point must declare its key; unknown keys deny at runtime. The same keys drive API scopes, so the public and admin APIs cannot reach an action under a different name.

<!-- check:lifecycle -->
### Grant lifecycle and privileged access

Permissions are added with features, reviewed by the security lead, released as immutable catalogue versions, deprecated for two releases with automatic mapping in system roles, then removed. Tier changes that widen access need `platform_security` approval.

<!-- check:resilience -->
### Failure modes and secrets

The catalogue is loaded at start-up from the database and compared with the compiled release; a mismatch or a missing key fails closed. It has no runtime network dependency.

<!-- check:audit -->
### Audit trail

Catalogue releases are published with `admin.catalogue.published` (platform audit) and kept immutable; every decision audit event carries `catalogue_release` and `policy_version`, so the meaning of a permission on a given date can be shown.

<!-- check:compliance -->
### Framework and legal mapping

Supports ISO/IEC 27001:2022 Annex A 5.15 (access control policy), 5.18 (access rights) and 8.2 (privileged access rights) [R6] and SOC 2 CC6.1 and CC6.3 [R7]; the rendered catalogue with tiers is the documented access-control rule set auditors request.

<!-- check:testing -->
### Verification and testing

Generated allow and deny tests per permission and holding role, lint of tiers and naming, documentation sync and entry-point coverage checks all run in CI on every change to `packages/authz`.

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
    "title": "Salesforce Help: Permission Set Groups",
    "url": "https://help.salesforce.com/s/articleView?language=en_US&id=platform.perm_set_groups.htm&type=5",
    "vendor": "Salesforce"
  },
  {
    "id": "R4",
    "kind": "vendor",
    "title": "Okta Help: Custom admin roles",
    "url": "https://help.okta.com/oie/en-us/content/topics/security/custom-admin-role/custom-admin-roles.htm",
    "vendor": "Okta"
  },
  {
    "id": "R5",
    "kind": "vendor",
    "title": "Microsoft Learn: Security roles and privileges for Dataverse (access levels)",
    "url": "https://learn.microsoft.com/en-us/power-platform/admin/security-roles-privileges",
    "vendor": "Microsoft"
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
