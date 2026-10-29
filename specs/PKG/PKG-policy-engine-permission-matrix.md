---
id: "PKG-policy-engine-permission-matrix"
title: "Policy engine, permission matrix per persona"
parent: "PKG-authorization"
order: 2
type: "feature"
template: "security"
status: "draft"
owner: null
indicative: false
summary: "Policy code, decision flow (context, principal, scope, deny-first, conditions, obligations), epoch-keyed caching, versioning, and the persona matrix for case resources"
links: []
rev: 3
syncHash: "5de385515f013b0f"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.2.2 Policy engine, permission matrix per persona

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Policy code, decision flow (context, principal, scope, deny-first, conditions, obligations), epoch-keyed caching, versioning, and the persona matrix for case resources

<!-- section:purpose -->
## Purpose and scope

Specifies how authorisation policies are written, evaluated, versioned, cached and tested in `@nomology/authz`, the **decision flow** every check follows, and the **persona matrix for case resources** with its conditions. The matrix is the source of truth for case-resource tests and is rendered read-only in the tenant console (`/admin/access/matrix`) so institutions can see who can do what. Permission keys come from [[PKG-permission-catalogue]]; roles from [[PKG-roles-and-permission-sets]]; conditions from [[PKG-rbac-abac-case-level-party]].

<!-- section:assets -->
## Protected assets

All resources in [[PKG-authorization#assets]]. Specific to this node: the policy bundle (`packages/authz/policies`), its version, the matrix file `packages/authz/matrix.yaml` (generated docs, console view and tests), and the grant-set cache in regional Redis.

<!-- section:actors -->
## Actors and roles

Column abbreviations in the matrix (canonical keys in brackets): **Pa** party (`claimant` / `respondent`), **Co** counsel (`claimant_counsel` / `respondent_counsel`), **PN** `presiding_neutral`, **TM** `tribunal_member`, **CM** `case_manager`, **SE** `secretariat` with a scope covering the case, **SL** `secretariat_lead` template, **Tr** case `transcriber`, **Fin** `case_finance_officer` template, **Adm** tenant administrative roles, **SA** service account with a matching scope. Other case roles (`expert`, `witness`, `interpreter`, `observer`) have narrow sets listed in [[PKG-roles-and-permission-sets#matrix]]. AI agents on behalf of a human get the intersection with that human's column ([[PKG-non-human-principals]]). Support access is governed by [[PKG-support-access-and-impersonation]].

<!-- section:matrix -->
## Permission matrix

Legend: ✓ allowed; ✗ denied; **side** own side only; **case** has a case role on the case; **own** own record; **SU** step-up required; **set:x** depends on setting `access.case.x` ([[PKG-settings-access-control]]); **stage:x** only in stages x; **rules** decided by the case-type rules ([[PKG-rules-and-decision-engine]]). Walls and need-to-know restrictions deny every cell for affected principals.

| # | Permission | Pa | Co | PN | TM | CM | SE | SL | Tr | Fin | Adm | SA |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `case:list` | case | case | case | case | case | ✓ | ✓ | hearing metadata | billing view | ✗ | scope |
| 2 | `case:read` | case | case | case | case | case | ✓ | ✓ | hearing metadata | billing fields | ✗ | scope |
| 3 | `case:create` | set:intake (via `case.intake.party_self_filing`) | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | scope (aggregator intake) |
| 4 | `case:approve` (register) | ✗ | ✗ | ✗ | ✗ | rules | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| 5 | `case.status:update` | ✗ | ✗ | tribunal commands SU | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | limited commands |
| 6 | `case:assign` | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| 7 | `case:configure` (seal, case-overridable settings) | ✗ | ✗ | ✗ | ✗ | case settings only SU | ✗ | ✓ SU | ✗ | ✗ | ✗ | ✗ |
| 8 | `case.party:create/update/delete` | ✗ (request) | ✗ (request) | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | scope |
| 9 | `case.representative:create` | side (own party) | side (co-counsel, set:counsel_can_add_cocounsel) | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| 10 | `case.participant:assign` | ✗ | ✗ | experts | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| 11 | `case.filing:create` | side, stage:open, SU | side, stage:open, SU | ✗ | ✗ | on behalf, reason, set:filing_on_behalf_enabled | same as CM | same | ✗ | ✗ | ✗ | scope |
| 12 | `case.filing:delete` (withdraw before acceptance) | own | side | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| 13 | `case.filing:approve` (admit / reject) | ✗ | ✗ | ✓ | ✗ | rules | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 14 | `case.document:read` tier `case_participants` | case | case | case | case | ✓ | ✓ | ✓ | hearing exhibits | ✗ | ✗ | scope |
| 15 | `case.document:read` tier `side_restricted` | side; other side after exchange | same | if submitted to tribunal | same | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | own side |
| 16 | `case.document:read` tier `tribunal_only` | ✗ | ✗ | ✓ | ✓ | set:secretariat_sees_tribunal_drafts | same | same | ✗ | ✗ | ✗ | ✗ |
| 17 | `case.document:read` tier `institution_internal` | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| 18 | `case.document:create` | side | side | tribunal folder | tribunal folder | ✓ | ✓ | ✓ | transcripts | ✗ | ✗ | scope |
| 19 | `case.document:export` (download URL) | as read | as read | as read | as read | as read | as read | as read | as read | ✗ | ✗ | as read |
| 20 | `case.document:update` (metadata, tier) | ✗ | ✗ | SU | ✗ | SU | SU | SU | ✗ | ✗ | ✗ | ✗ |
| 21 | document version delete | ✗ (immutable; withdrawal only) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 22 | `case.bundle:create` | ✗ | set:parties_prepare_bundles | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| 23 | `case.bundle:publish` | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| 24 | `case.order:create` (draft) | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 25 | `case.order:approve` (concur) | ✗ | ✗ | SU | SU | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 26 | `case.order:publish` (issue) | ✗ | ✗ | SU (or per rules) | rules | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 27 | `case.award:create` / `:read` (draft) | ✗ | ✗ | ✓ | ✓ | set:secretariat_sees_tribunal_drafts (read) | same | same | ✗ | ✗ | ✗ | ✗ |
| 28 | `case.award:approve` (sign) | ✗ | ✗ | SU | SU | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 29 | `case.award:publish` (serve) | ✗ | ✗ | ✗ | ✗ | SU, after all signatures | ✗ | SU | ✗ | ✗ | ✗ | ✗ |
| 30 | `case.notice:create` (serve notice) | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | scope |
| 31 | `case.hearing:create/update` | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | scope |
| 32 | `case.hearing.slot:create` | case | case | case | case | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | scope |
| 33 | `case.hearing.room:read` (join) | case | case | case | case | ✓ | ✓ | ✓ | window | ✗ | ✗ | ✗ |
| 34 | `case.recording:read` | set:recordings_to_parties | same | ✓ | ✓ | ✓ | ✓ | ✓ | assigned | ✗ | ✗ | ✗ |
| 35 | `case.transcript:update` | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | until submitted | ✗ | ✗ | ✗ |
| 36 | `case.transcript:publish` (release) | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| 37 | `case.message:create` (all participants) | case | case | case | case | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| 38 | `case.message.tribunal:create` | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 39 | `neutral.profile:list` | disclosures only | disclosures only | own | own | ✓ | ✓ | ✓ | ✗ | fee fields | ✗ | ✗ |
| 40 | `neutral:assign` (appoint) | ✗ | ✗ | ✗ | ✗ | rules | ✗ | SU | ✗ | ✗ | ✗ | ✗ |
| 41 | `neutral.challenge:create` / `:approve` | file SU | file SU | ✗ | ✗ | ✗ | ✗ | decide SU | ✗ | ✗ | ✗ | ✗ |
| 42 | `case.deadline:update` (extend) | ✗ (`case.application:create`) | ✗ (application) | SU | ✗ | rules | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| 43 | `case.invoice:read` | own | side | own vendor bills | own vendor bills | ✓ | ✓ | ✓ | own vendor bills | ✓ | ✗ | scope |
| 44 | `case.invoice:create`, `case.payment:approve` (refund) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | SU (MC above threshold) | ✗ | ✗ |
| 45 | `case.payment:create` (pay) | own | side | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 46 | `case.vendor_bill:create` / `:approve` | ✗ | ✗ | submit own | submit own | ✗ | ✗ | approve SU | submit own | approve SU | ✗ | ✗ |
| 47 | `case:export` (full case file) | ✗ | ✗ | ✗ | ✗ | SU | ✗ | SU | ✗ | ✗ | ✗ | ✗ |
| 48 | `case.audit:read` | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | auditor: metadata | ✗ |
| 49 | `case.wall:create` / `:approve` / `:delete` | ✗ | ✗ | ✗ | ✗ | propose | propose | approve, lift (second approver) SU | ✗ | ✗ | ✗ | ✗ |
| 50 | `ai.generation:create` | per AI policy | per AI policy | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |

Administrative permissions (users, roles, settings, workflow, integrations, AI, audit) are not case resources; their holders are in [[PKG-permission-catalogue#matrix]] groups F–J.

**Consequential action catalogue** (step-up plus consequential confirmation UI, [[PKG-modal-dialog-and-consequential]]): rows 5 (selected commands), 7, 11, 20, 25, 26, 28, 29, 40, 41 (decide), 42, 44, 46 (approve), 47, 49.

<!-- section:policy -->
## Policy model

**Decision (proposed, to be recorded as an ADR):** policies are typed TypeScript functions in a policy bundle, not a separate policy language. Reasons: policies need the same fact loaders and Prisma filter compilation as the rest of the codebase; one language for reviewers; no extra runtime per region. Alternatives considered: Cedar (strong analysis tooling and clear forbid-overrides-permit semantics [R4], but a second language and filter compilation would need our own partial evaluation), OPA / Rego (sidecar or WASM; same filter problem), an OpenFGA / Zanzibar-style relationship service (good for case roles and "list objects" [R5][R6], but a second datastore per region that must stay consistent with Postgres under RLS), Casbin (too thin for stages and tiers). The decision interface follows the subject / action / resource / context shape of the OpenID AuthZEN Authorization API [R7] so that an external engine could be placed behind it later without changing callers.

**Decision flow** (every call to `can`, `assert`, `where`, `explain`):

```text
1  Context      verify signed PrincipalContext; tenant = session tenant = host tenant; set app.tenant_id in tx
2  Catalogue    permission key exists in loaded release (else deny + alert)
3  Principal    kind gates: non-human ceilings; AI on-behalf → evaluate for agent AND human; support grant constraints
4  Suspension   tenant suspended / membership suspended / principal disabled → deny (except protected due-process actions per BIL-ENT-5)
5  Entitlement  permission's plan feature included? else deny 'not_in_plan'
6  Grant set    load effective permissions for principal (cache by grant epoch) → paths with scopes
7  Scope        any path whose scope covers the resource? else deny (not found for case resources)
8  Deny rules   walls and need-to-know → SoD runtime (self-approval, same-case conflicts) → seal / stage locks / legal hold
9  Conditions   policy allow rules over facts (side, tier, exchange, window, setting) 
10 Obligations  step-up, maker-checker routing, audit_read, watermark
11 Result       Decision { allow, reason, paths, policy.version, catalogue.release, obligations }
```

```ts
// packages/authz/src/index.ts
export type Permission = GeneratedPermission;              // from permissions.yaml
export interface ResourceRef { type: ResourceType; id: string; caseId?: string }
export interface Decision {
  allow: boolean;
  reason: 'allowed' | 'not_found_or_denied' | 'stage_closed' | 'walled' | 'step_up_required'
        | 'suspended' | 'not_in_plan' | 'ceiling_exceeded' | 'sod_conflict' | 'elevation_available';
  policy: { id: Permission; version: string };              // e.g. '2026.11.3+git.4f2c1a'
  catalogue: string;                                         // e.g. '2026.11.0'
  obligations?: { stepUp?: boolean; makerChecker?: boolean; auditRead?: boolean; watermark?: boolean };
}
export function can(tx: TenantTx, p: PrincipalContext, perm: Permission, r: ResourceRef): Promise<Decision>;
export function assert(tx: TenantTx, p: PrincipalContext, perm: Permission, r: ResourceRef): Promise<void>;
export function where<P extends ListPermission>(tx: TenantTx, p: PrincipalContext, perm: P): Promise<WhereFor<P>>;
export function explain(tx: TenantTx, subject: PrincipalRef, perm: Permission, r: ResourceRef, o?: { asOf?: Date }): Promise<Explanation>;

definePolicy('case.document:read', {
  load: loadDocumentFacts,
  deny: [walled, notOnNeedToKnow, caseSealedForPrincipal],
  allow: [
    when(tier('case_participants'), or(hasCaseRole(), inScope)),
    when(tier('side_restricted'), or(onOwnSide, and(exchanged, hasCaseRole()), and(submittedToTribunal, isTribunal), inScope, isCaseManager)),
    when(tier('tribunal_only'), or(isTribunal, and(setting('access.case.secretariat_sees_tribunal_drafts'), or(isCaseManager, inScope)))),
    when(tier('institution_internal'), or(isCaseManager, inScope)),
  ],
  obligations: (f) => ({ auditRead: f.tier === 'tribunal_only' || f.isKyc }),
});
```

**Caching**

| Layer | What | Key | Lifetime | Invalidation |
|---|---|---|---|---|
| L0 per request | Facts and decisions | in-memory | request | — |
| L1 regional Redis (cache Redis, [[INF-redis]]) | Grant set: permission keys with scopes and paths (no personal data, no content) | `{env}:{region}:t:{tenantId}:authz.grants:{principalId}:{epoch}:{tenantEpoch}` (namespace `authz.grants`, [[PKG-caching]]) | TTL `access.platform.decision_cache_ttl_s` (300 s) | Key changes when the epoch changes, so a stale entry is never read |
| L1 | Wall set per principal | `…:authz.walls:{principalId}:{epoch}` | 300 s | same epoch |
| Database | `authz_grant_epoch` row | PK lookup per request (~0.2 ms) | — | Incremented in the same transaction as any grant, role, set, wall, eligibility or principal change |

Decisions themselves are never cached across requests. Realtime connections (hearing room signalling, in-app notification stream) re-check on a 60-second heartbeat and on an epoch-change event published on Redis pub/sub.

**Versioning**: bundle version = package version + git SHA, attached to every decision and audit event and recorded in `authz_policy_bundle`. Matrix changes require security lead review and an updated `matrix.yaml`, which regenerates documentation, the console view and tests. Policy bundles and catalogue releases deploy together per region.

<!-- section:threats -->
## Threats and abuse cases

| # | STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|---|
| T1 | E | A new action ships without a policy | `Permission` type generated from the catalogue; an action without a policy fails the build; default deny | Very low |
| T2 | E | Policy change widens access silently | Matrix diff in PR rendered as a table; security lead CODEOWNER; generated tests change visibly | Low |
| T3 | I | Filter compilation bug leaks rows in lists | Dual-form tests; filters only add conditions to RLS-protected queries | Low |
| T4 | D | Slow fact loaders degrade pages | One-query loaders, per-request memo, grant-set cache, p95 budget in perf tests | Low |
| T5 | R | Cannot show which rule allowed an access | `explain()`, paths in decisions, versions in audit | Low |
| T6 | E | Stale cache after revocation | Epoch in cache key; epoch read from database per request | Very low |
| T7 | T | Cache poisoning in Redis | Redis ACL user per service ([[INF-redis]]); cache stores only keys derived from the database; entries signed with an HMAC checked on read | Low |

<!-- section:failure -->
## Denial behaviour

`assert` throws `NotFoundOrDeniedError` (404, identical to not-found), `StepUpRequiredError` (401 `auth/step-up-required`), `ForbiddenError` with a user-actionable reason for visible resources (403 `stage_closed`, `elevation_available`, `not_in_plan`, `checker_not_eligible`, `sod_conflict`), and `walled` shown as a generic "You cannot act on this case" to avoid revealing a conflict. Logged with permission, resource type, reason, policy version and catalogue release; resource IDs are logged, content never.

<!-- section:requirements -->
## Security requirements

ASVS references are to OWASP ASVS **5.0** at chapter level [R1][R2]. Old IDs POL-1 to POL-5 are kept as POL-FR-1 to POL-FR-5.

| ID | Requirement | ASVS 5.0 |
|---|---|---|
| POL-FR-1 | The persona matrix shall be a versioned file from which policy types, tests and the console view are generated. | V8 |
| POL-FR-2 | A permission without a policy shall be denied and fail the build. | V8 |
| POL-FR-3 | Each decision shall return the policy bundle version and catalogue release. | V8 |
| POL-FR-4 | Consequential actions listed in the catalogue shall carry a step-up obligation. | V8 |
| POL-FR-5 | Policy decisions shall add p95 ≤ 5 ms on warm caches and ≤ 15 ms on cache miss. | — |
| POL-FR-6 | Every decision shall follow the decision flow order; deny rules shall be evaluated before allow rules and shall override them. | V8 |
| POL-FR-7 | Cached grant sets shall be keyed by the principal's grant epoch so that no grant change is ever served from a stale entry. | V8 |
| POL-FR-8 | The decision interface shall accept subject, action, resource and context in a form compatible with an AuthZEN-style evaluation request. | — |

<!-- section:verification -->
## Verification

- Generated tests: for each matrix row × persona × condition, allow and deny cases (about 50 × 11 × ~3 ≈ 1,650 tests), run on every change to `packages/authz`, `matrix.yaml` or the catalogue [R3].
- Mutation testing on combinators to prove tests catch policy changes.
- Cache tests: revoke then read within the same second must deny; Redis down must fall back to database.
- Performance test: 10,000 decisions on realistic data with p95 recorded per release.

<!-- section:questions -->
## Open questions

- [ ] Record the policy engine decision (TypeScript policies vs Cedar or a relationship engine) as an ADR. (Security lead)
- [ ] Rows 4, 13, 26, 40 and 42 depend on institution rules: confirm which are rule-driven via [[PKG-rules-and-decision-engine]] and which are fixed. (Product)
- [ ] Default for parties seeing recordings (row 34): blueprint defaults proposed in [[PKG-settings-access-control#defaults]]. (Product)
- [ ] Is filing on behalf by secretariat (row 11) allowed for all tenants, and what notice goes to the party? Now `access.case.filing_on_behalf_*`. (Legal)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Cache keys include the tenant id and region ([[PKG-caching]]); decisions run inside the tenant transaction; the context's tenant must equal the host tenant before any policy runs.

<!-- check:enforcement -->
### Enforcement points and bypass paths

The catalogue generates the `Permission` type; entry points must declare a permission; default deny covers anything missing; list filters come from the same policies.

<!-- check:resilience -->
### Failure modes and secrets

Policies run in-process; dependencies are the regional database (fail closed) and the Redis grant cache (fall back to database). Epoch-keyed caching means a Redis failure can slow decisions but never serve stale grants.

<!-- check:audit -->
### Audit trail

Decisions with `auditRead` obligations (tribunal-only, KYC, exports) and all denials of consequential actions are audited with permission, policy version and catalogue release; `explain()` calls are audited in the tenant stream.

<!-- check:compliance -->
### Framework and legal mapping

Supports ISO/IEC 27001:2022 Annex A 5.15, 5.18 and 8.3 and SOC 2 CC6.1–CC6.3; the generated matrix and test report per release are the audit evidence.

<!-- check:testing -->
### Verification and testing

About 1,650 generated allow and deny tests from `matrix.yaml`, dual-form filter tests, mutation tests, cache and performance tests; all against real Postgres with RLS via PgBouncer; a matrix change without regenerated tests fails CI.

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
    "id": "R4",
    "kind": "vendor",
    "title": "Cedar documentation: How Cedar authorization works",
    "url": "https://docs.cedarpolicy.com/auth/authorization.html",
    "vendor": "Cedar (AWS open source)"
  },
  {
    "id": "R5",
    "kind": "web",
    "publisher": "USENIX ATC 2019 / Google Research",
    "title": "Zanzibar: Google's Consistent, Global Authorization System",
    "url": "https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/"
  },
  {
    "id": "R6",
    "kind": "vendor",
    "title": "OpenFGA documentation: Search with permissions",
    "url": "https://openfga.dev/docs/interacting/search-with-permissions",
    "vendor": "OpenFGA (CNCF)"
  },
  {
    "body": "OpenID Foundation",
    "id": "R7",
    "ident": "AuthZEN",
    "kind": "standard",
    "title": "OpenID AuthZEN Authorization API 1.0",
    "url": "https://openid.net/specs/authorization-api-1_0.html",
    "version": "1.0"
  }
]
```

<!-- end -->
