# Template: Access and security control (`security`)

Generated from `security.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies a mechanism that decides who can do what, or protects data and sessions, with its threats and verification made explicit.

**Depth:** 4–10 pages. The permission matrix and threat table must be complete for the scope; partial matrices are the main source of access bugs. Map each requirement to an OWASP ASVS 5.0 requirement ID where one exists, and always state the ASVS version (chapter numbers changed between 4.0.3 and 5.0). Split by persona or resource family if the matrix exceeds ~40 rows.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `purpose` Purpose and scope (level 1)

What is protected, from whom, and which parts of the platform rely on this control.

Illustrative example (not a requirement):

> Case-level authorization decides whether a user may view or act on a case, its documents and hearings. Every API route and Temporal signal handler that touches case data calls it.

### `assets` Protected assets (level 1)

The data and actions being protected, with sensitivity classification.

Illustrative example (not a requirement):

> | Asset | Classification |
> |---|---|
> | Pleadings and evidence documents | Confidential — party-restricted |
> | Award drafts | Highly confidential — tribunal only |
> | Party contact details | Personal data (DPDP / GDPR) |

### `actors` Actors and roles (level 1)

Every persona and system actor, and how a user acquires each role.

Illustrative example (not a requirement):

> | Role | Acquired by |
> |---|---|
> | Claimant / respondent counsel | Invitation accepted on the case |
> | Neutral (arbitrator) | Appointment accepted |
> | Tribunal secretary | Tenant admin assignment |
> | Tenant admin | Platform onboarding |
> | Transcriber | Assigned per hearing, expires after delivery |

### `matrix` Permission matrix (level 1)

Role × resource × action, including conditions (case stage, ownership). Use a table; every cell must be decided.

Illustrative example (not a requirement):

> | Resource / action | Counsel | Neutral | Secretary | Transcriber |
> |---|---|---|---|---|
> | View own party's filings | ✓ | ✓ | ✓ | — |
> | View other party's filings | after service | ✓ | ✓ | — |
> | View award draft | — | ✓ | — | — |
> | Upload transcript | — | — | ✓ | assigned hearing only |

### `policy` Policy model (level 2)

How rules are expressed and evaluated (RBAC, ABAC attributes, policy engine), where policies live, and evaluation order.

Illustrative example (not a requirement):

> RBAC for coarse roles, ABAC conditions on `case.stage`, `document.visibility` and `assignment.expiresAt`. Policies are versioned data in the Rules engine; evaluation is deny-by-default and returns a reason code.

### `threats` Threats and abuse cases (level 1)

STRIDE-style table: threat, scenario, mitigation, residual risk.

Illustrative example (not a requirement):

> | STRIDE | Scenario | Mitigation |
> |---|---|---|
> | Elevation | Counsel edits case ID in URL to another case | Case membership check on every request + RLS |
> | Information disclosure | Transcriber keeps access after delivery | Time-bound assignment, nightly expiry job |
> | Repudiation | Neutral denies viewing a document | Read events in audit trail |

### `failure` Denial behaviour (level 2)

What the user sees on denial, what is logged, and how errors avoid leaking existence of resources.

Illustrative example (not a requirement):

> Return 404 (not 403) for resources in cases the user is not a member of. Log denial with reason code and policy version. Show "You don't have access to this document" only within a case the user belongs to.

### `requirements` Security requirements (level 2)

Numbered, testable requirements, each mapped to an ASVS item where possible.

Illustrative example (not a requirement):

> - SEC-AZ-1 Access control is enforced server-side on every request (ASVS 5.0 V8 Authorization)
> - SEC-AZ-2 Deny by default; new resources are inaccessible until a rule grants access
> - SEC-AZ-3 Privilege changes take effect within 60 seconds across all sessions

### `verification` Verification (level 2)

Automated negative tests, review steps, pen-test scope.

Illustrative example (not a requirement):

> Matrix-driven test suite: one allowed and one denied test per matrix row, generated from the matrix itself. Annual external pen test covers IDOR on case and document routes.

### `questions` Open questions (level 3)

Checklist.

Illustrative example (not a requirement):

> - [ ] Should co-counsel from the same firm see each other's private notes?

## Checks

### `tenancy` Tenant isolation

**Question:** Can any rule, code path or operator action in this control grant access to another tenant's data, and what independent layers stop it if one layer fails?

- Where does the tenant ID used for the decision come from (session claim, subdomain, URL, request body), and can a user influence it?
- Is the application check backed by Postgres Row-Level Security with FORCE ROW LEVEL SECURITY, so that a missing `where tenant_id = ...` still returns no rows?
- Is the tenant set with SET LOCAL inside each transaction by the Prisma extension, and what proves it cannot leak to the next transaction on the same PgBouncer connection?
- Which database roles bypass RLS (table owner, migration role, BYPASSRLS), which services use them, and how is their use restricted and logged?
- Do Temporal workflows, BullMQ jobs, caches (Redis keys), search indexes and object-storage paths carry and enforce the tenant ID, or do they trust the caller?
- Can a user who belongs to two tenants (for example counsel appearing before two institutions) ever have permissions or data from one tenant applied in the other?
- How is Nomology staff or support access to a tenant granted: tenant consent, time limit, scope, and audit entry visible to the tenant?

**Good answer:** Names at least two independent enforcement layers (application policy check and forced RLS keyed on a transaction-local setting) and shows the tenant ID is derived only from the authenticated session, never from user input. Lists every RLS-bypassing role and why it exists. Points to an automated cross-tenant test suite that runs in CI against a real Postgres with PgBouncer in transaction mode, and to the support-access procedure with its audit trail.

**Red flags:**

- Tenant isolation relies only on application code or on developers remembering a filter
- Tenant ID read from a header, query string or request body without checking it against the session
- Background jobs or workflows run with a superuser or BYPASSRLS role by default
- No test that tries to read, write or enumerate another tenant's records

### `enforcement` Enforcement points and bypass paths

**Question:** Is this control enforced on every path that reaches the protected asset, including non-interactive and indirect paths, with no way around it?

- List every entry point that touches the asset: Next.js route handlers, server actions, server components, public APIs, webhooks, Temporal signal and activity handlers, BullMQ jobs, exports, admin tools, and database consoles.
- Is the check centralised in one shared package in the monorepo that all of these call, and how is a new route prevented from shipping without it (lint rule, middleware default-deny, CI check)?
- Are file downloads (pre-signed URLs, transcripts, eBundles) checked at issue time, and how long do the links stay valid after access is revoked?
- Do derived copies of the data (search index, AI embeddings or prompts, notification emails, cached PDFs, analytics extracts) inherit the same access rules?
- Is authorisation checked on the server for every request, rather than relying on hidden buttons or client-side state?
- For long-running workflows, is the permission re-checked when the action executes, not only when the workflow started days earlier?

**Good answer:** Provides a complete inventory of entry points mapped to the enforcement function each one calls, and names the mechanism that makes deny the default for anything not mapped. States the maximum lifetime of any token or link that outlives a permission change (for example pre-signed URLs at 5 minutes or less) and explains how derived data such as search results and AI context is filtered by the same policy.

**Red flags:**

- Checks performed only in the UI or only in some API routes
- Workflows or jobs act on stale permissions captured at start time
- Long-lived download links, or search and AI features that bypass the policy
- No mechanism that fails the build when a new route lacks an authorisation call

### `lifecycle` Grant lifecycle and privileged access

**Question:** How are permissions granted, changed, expired and revoked, and how is privileged or emergency access controlled?

- How quickly does revocation take effect across active sessions, caches and open WebSocket or streaming connections (target in seconds or minutes)?
- Which grants are time-bound (transcriber per hearing, temporary co-counsel, interpreter), and what job expires them and alerts if expiry fails?
- What happens to a user's access when they leave a law firm, are removed from a case, or when an arbitrator is challenged or recused?
- How are conflicts and ethical walls applied when a user is added to a case, and can a tenant admin override them?
- Is there a break-glass process for platform staff, with approval, time limit, session recording and post-use review?
- Who can change roles or policies, is it maker-checker for high-impact changes, and are tenant admins prevented from granting themselves tribunal-only access?
- With SSO (SAML or OIDC), how are de-provisioned identity-provider accounts reflected (SCIM, session lifetime, re-check on token refresh)?

**Good answer:** Gives a numeric revocation target and the mechanism that meets it, names the scheduled job that expires time-bound grants with a monitored failure alert, and describes break-glass access with approval, a hard time limit and tenant-visible audit. Shows that role and policy changes are themselves permissioned, logged and, for sensitive roles, approved by a second person.

**Red flags:**

- Revocation only takes effect at next login or after a long session timeout
- Standing (permanent) platform-admin access to tenant data
- Time-bound grants with no automated expiry
- Tenant admins able to escalate themselves into tribunal-only or party-restricted data

### `resilience` Failure modes and secrets

**Question:** What does the control do when its dependencies fail or its keys and secrets are compromised, and does it always fail closed?

- If the policy store, identity provider, Redis or KMS is unavailable or slow, does the request get denied, and what does the user see?
- Are policy decisions cached; if so, for how long, and how are caches invalidated when a role or policy changes?
- Where are signing keys, encryption keys and client secrets held (AWS KMS / Azure Key Vault, per region), who can use them, and what is the rotation period?
- What is the procedure and expected time to rotate a compromised key or secret without downtime, and has it been rehearsed?
- What added latency does the check introduce at p95 and p99, and what stops teams from bypassing it for performance?
- Are rate limits and lockouts tuned so that they block brute force and enumeration without letting an attacker lock out a tribunal before a hearing?

**Good answer:** States fail-closed behaviour for each dependency with the user-facing message, gives cache lifetimes and the invalidation trigger, and names the key store, key owner and rotation interval per region. Includes a tested rotation runbook with a recorded rehearsal date and a latency budget for the check.

**Red flags:**

- Any path that allows access when the policy engine or identity provider errors
- Secrets in environment files, source code or CI logs
- No tested key rotation procedure
- Unbounded policy caches with no invalidation on change

### `residency` Data residency

**Question:** Does every piece of data this control creates or uses (sessions, audit logs, keys, identity data) stay in the tenant's pinned region?

- Are session stores, audit logs, key material and policy data deployed per region (India, Singapore, US), or is any of it global?
- Does a global component (login page, identity provider, CDN, email or SMS provider, error tracking) receive personal data or tokens of tenants pinned to another region?
- How does a user who works with tenants in two regions sign in, and where is their identity record stored?
- Do security logs shipped to a SIEM or monitoring vendor leave the region, and is that covered by the sub-processor list and transfer terms?
- Where a client requires Azure, is the control implemented identically there, and how is parity verified?

**Good answer:** Gives a table of each data element the control touches with its storage location per region and per cloud, and identifies any cross-border flow with its legal basis and sub-processor entry. Shows how parity between AWS and Azure deployments is checked.

**Red flags:**

- A single global session or audit store for all regions
- Personal data in logs sent to a vendor outside the tenant's region without a recorded transfer basis
- Azure deployments assumed to match AWS without verification

### `audit` Audit trail

**Question:** Are grants, denials, privilege changes and sensitive reads recorded in a tamper-evident log that can answer who did what, when, to which record, and under which policy version?

- Which events are logged: logins, MFA changes, role grants and removals, policy changes, denials, reads of highly confidential items such as award drafts, exports and break-glass use?
- Does each event carry tenant ID, actor, acting-on-behalf-of, resource ID, action, decision, reason code, policy version, source IP, request ID and UTC timestamp?
- How is the log protected from change or deletion, including by platform administrators (append-only table, write-once storage, hash chaining)?
- How long are logs kept, and does this meet CERT-In (logs kept for 180 days within India), DPDP Rules and tenant contract requirements?
- Can a tenant admin or tribunal export the audit trail for their own cases without seeing other tenants' events?
- Are personal data and secrets kept out of log messages, or masked?

**Good answer:** Lists the logged event types with their fields, names the storage and the tamper-evidence mechanism, and states retention per region with the legal or contractual basis for each period. Explains how a tenant retrieves its own trail and how log access is itself logged.

**Red flags:**

- Denials or reads of sensitive documents not logged
- Audit records stored in a table the application can update or delete
- Retention period not stated or shorter than CERT-In's 180 days for India-region systems
- Passwords, tokens or full document contents written to logs

### `observability` Detection and alerting

**Question:** Which signals from this control are monitored, what thresholds raise an alert, who responds, and how does an alert feed the incident and breach-notification process?

- Which patterns are alerted on: denial spikes per user or tenant, sequential ID probing, cross-tenant access attempts, impossible travel, mass downloads, privilege escalation, break-glass use?
- What are the thresholds and how were they chosen to avoid both silence and alert fatigue?
- Who receives alerts out of hours, what is the response time target, and where is the runbook?
- How does a confirmed incident trigger notification clocks: CERT-In within 6 hours, the Data Protection Board and affected people under DPDP (detailed report within 72 hours), GDPR supervisory authority within 72 hours, and Singapore PDPC within 3 days of assessing a notifiable breach?
- Are tenants told about security events affecting their cases, and within what contractual timeframe?
- Is there a dashboard of denials and anomalies per tenant that the security team reviews on a fixed cadence?

**Good answer:** Names each detection rule with its threshold, destination and on-call owner, and links each to a runbook. Shows the hand-off from alert to incident to regulatory notification with the clock start defined, so that the 6-hour CERT-In and 72-hour DPDP and GDPR deadlines can be met.

**Red flags:**

- Denials logged but nobody alerted
- No named on-call responder or runbook
- No link between security alerts and the breach-notification procedure

### `compliance` Framework and legal mapping

**Question:** Which specific clauses of ISO 27001:2022, SOC 2, privacy laws and client contracts does this control help satisfy, and what evidence will an auditor take from it?

- Which ISO 27001:2022 Annex A controls apply (for example 5.15 access control, 5.18 access rights, 8.2 privileged access, 8.3 information access restriction, 8.5 secure authentication, 8.15 logging, 8.24 use of cryptography)?
- Which SOC 2 Trust Services Criteria apply (for example CC6.1 to CC6.3 logical access, CC7.2 monitoring), and which compliance control nodes reference this spec?
- Which privacy duties does it support: DPDP reasonable security safeguards and access controls, GDPR Article 32 security of processing, PDPA protection obligation?
- Do HKIAC, SEBI ODR or other client contracts impose specific requirements (MFA for all users, IP allow-listing, data segregation, audit rights)?
- What evidence does the control produce automatically for audits (access review exports, configuration snapshots, test results)?
- If ISO 42001 applies (AI features use this data), how are AI components covered?

**Good answer:** Gives a table of clause IDs per framework mapped to the specific requirement IDs in this spec, with links to the compliance control nodes that operate and evidence them. Calls out any contractual requirement that goes beyond the frameworks.

**Red flags:**

- Generic statements such as 'supports ISO 27001' with no clause IDs
- No link to the compliance control that operates and evidences this mechanism
- Client contractual security requirements not checked

### `testing` Verification and testing

**Question:** How is every allow and deny in the permission matrix proven by automated tests, and what independent testing covers what automation cannot?

- Is there at least one automated negative test per matrix row and condition (wrong role, wrong case stage, expired assignment, other party, other tenant)?
- Are the tests generated from the matrix itself, so a change to the matrix without a matching test fails CI?
- Do tests run against a real Postgres with RLS and PgBouncer in transaction mode, not a mock?
- Do tests cover Temporal handlers, BullMQ jobs and export paths, not only HTTP routes?
- What is the scope, frequency and provider of penetration testing, does it include multi-tenant and authorisation abuse cases, and how fast are findings fixed by severity?
- Is there a regression test for every past access-control bug or pen-test finding?

**Good answer:** Shows a test suite derived from the matrix with a coverage report per row, run in CI on every change to policies or routes. States pen-test frequency (at least annually and after major changes), scope including cross-tenant and IDOR testing, and fix deadlines by severity (for example critical within 7 days).

**Red flags:**

- Only positive (happy-path) tests
- Tests run with RLS disabled or against mocked authorisation
- No pen test, or a pen test scoped without authorisation and tenant isolation testing
- No fix deadlines for findings

