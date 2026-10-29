# Template: Delivery plan (`plan`)

Generated from `plan.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Sequences the work into phases with clear entry and exit criteria, so progress is measured by outcomes rather than activity.

**Depth:** 2–5 pages. Each phase needs exit criteria that can be checked. Link phase scope to nodes rather than repeating their content. Revisit at every phase boundary.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `objective` Objective (level 1)

What the plan delivers overall and by when.

Illustrative example (not a requirement):

> A production-ready multi-tenant platform skeleton in three regions, onto which CORD and HKIAC CMP features can be built.

### `phases` Phases (level 1)

Table of phases: scope (linked nodes), outcome, entry criteria, exit criteria.

Illustrative example (not a requirement):

> | Phase | Scope | Entry criteria | Exit criteria |
> |---|---|---|---|
> | 0 Foundations | Monorepo, CI, envs | ADRs 19.1–19.7 approved | App deploys to staging from main in every region |
> | 1 Core platform | Tenancy, auth, authz, audit | Isolation and authorization specs approved | Isolation tests green in every region; SSO with one IdP |
> | 2 Shared services | Storage, notifications, flags | Phase 1 exit met | One end-to-end notification in prod |
> | 3 First domain slice | Cases, Documents | Cases and Documents domain nodes approved | One real case filed in UAT |

### `dependencies` Dependencies (level 1)

What each phase depends on, internal and external.

Illustrative example (not a requirement):

> Phase 3 depends on Authorization matrix approval (Security node) and on the e-sign vendor contract for settlement agreements.

### `milestones` Milestones (level 2)

Dated milestones and who signs off.

Illustrative example (not a requirement):

> | Milestone | Target | Sign-off |
> |---|---|---|
> | Staging in India region | Month 1 | CTO |
> | First tenant UAT | Month 4 | Product + client |

### `crosscutting` Cross-cutting from day one (level 2)

Concerns that are not deferred to a later phase.

Illustrative example (not a requirement):

> Audit logging, tenant isolation tests, security headers, structured logging, accessibility.

### `risks` Risks (level 2)

Delivery risks, likelihood, impact, mitigation.

Illustrative example (not a requirement):

> | Risk | Mitigation |
> |---|---|
> | Temporal self-hosting learning curve | Spike in phase 0; managed fallback evaluated |
> | Regulator format changes mid-build | Template-driven reports (Reporting) |

### `questions` Open questions (level 3)

Checklist.

Illustrative example (not a requirement):

> - [ ] Which client is the first tenant for UAT?

## Checks

### `dependencies` Dependencies

**Question:** Are all dependencies between phases, between nodes, and on outside parties explicit, owned and dated, so the critical path is known?

- For each phase, which nodes must be Approved (not just drafted) before work starts, for example the Authorisation matrix or Tenant isolation decision?
- Which external dependencies exist: vendor contracts (e-sign, transcription, payment gateway), client inputs (HKIAC data samples, test users), MII onboarding (for example NSE interface for SEBI ODR), cloud account and region setup, auditor availability? Who owns each and by when is it needed?
- What is the critical path, and which dependency, if late by four weeks, would move the final milestone?
- Are dependencies on shared people (one DevOps engineer, one designer, the security lead) treated as dependencies?
- Which items can be parallelised safely, and which look parallel but share a hidden dependency (for example both need the tenant context extension)?
- What is the fallback if an external dependency slips (stub, alternative vendor, reduced scope)?

**Good answer:** A dependency table with item, depends-on, type (internal node, external party, person), owner, needed-by date and fallback, plus the critical path stated explicitly. Dependencies on node approval reference the node and its current status.

**Red flags:**

- Dependencies stated without owners or dates.
- No critical path identified.
- External vendor or client dependencies missing.
- No fallback for a dependency on the critical path.

### `exit` Exit criteria

**Question:** Can every phase's exit criteria be checked objectively by someone other than the team, with the evidence named in advance?

- Is each exit criterion a pass / fail statement with a named evidence source (CI job, test report, dashboard, sign-off record), rather than an activity such as "implement tenancy"?
- Do exit criteria include non-functional evidence, not only features: isolation tests green, performance targets met, accessibility audit passed, security review closed, restore test done?
- Who signs off each phase exit, and is that person independent of the team that did the work where it matters (for example security review)?
- What happens if one criterion is missed: does the phase stay open, or can it close with an accepted exception that has an owner and a deadline?
- Are criteria checked in every region where the phase is meant to land, not only in India?
- Are entry criteria stated for each phase too, so work does not start on unapproved specs?

**Good answer:** Each phase has entry and exit criteria written as pass / fail checks with the evidence source and sign-off person named, including non-functional checks. The answer states the rule for missed criteria (exception with owner and due date, or the phase stays open).

**Red flags:**

- Exit criteria that describe activity rather than outcome.
- Only feature criteria, with no security, isolation, accessibility or performance evidence.
- Sign-off by the team that did the work for security-critical criteria.
- No rule for what happens when a criterion is missed.

### `capacity` Capacity

**Question:** Is the plan achievable with the people, skills and budget actually available, including time lost to support of the current CORD and TERES products?

- How many people, with which skills (TypeScript / Next.js, Postgres and RLS, Temporal, DevOps on AWS and Azure, accessibility, security), are available per phase, and what share of their time?
- How much time goes to running and supporting current CORD and TERES clients, incidents and sales support, and is it subtracted from capacity?
- Where is the plan's estimate based on evidence (past delivery data, a spike) versus a guess? What is the stated confidence?
- Which skills are missing (for example Temporal self-hosting experience), and is the plan to hire, train or bring in contractors? How long does each take?
- Is there contingency (for example 20% buffer) and is it visible rather than hidden in estimates?
- What is the budget for infrastructure in three regions, third-party tools, audits and penetration tests, and is it approved?
- If capacity drops (key person leaves, client escalation), what is cut first?

**Good answer:** A capacity table by phase with people, skills and percentage allocation after subtracting support load, estimates labelled with their basis and confidence, an explicit contingency, a plan for missing skills with lead times, an approved budget line, and a pre-agreed cut list.

**Red flags:**

- Capacity assumes everyone at 100% on the new platform.
- No allowance for supporting existing clients.
- Critical skills missing with no plan.
- No contingency or cut list.

### `risk` Risk-first sequencing

**Question:** Does the plan tackle the riskiest unknowns first, through time-boxed spikes with stated questions, rather than discovering them late?

- What are the top five technical and delivery risks (for example Temporal self-hosting per region, RLS with PgBouncer transaction pooling, Prisma tenant extension performance, Azure variant, regulator format changes)? Which phase retires each?
- For each spike, what question does it answer, what is its time box, and what decision does its result feed?
- Is there an early end-to-end slice through all layers (UI, API, domain, workflow, database in one region) before broad feature work?
- Which risks are accepted rather than mitigated, and who accepted them?
- How often is the risk register reviewed, and do risk changes trigger re-planning?
- Are compliance risks included (for example an ISO 27001 surveillance audit during migration, DPDP obligations coming into force)?

**Good answer:** A risk register with likelihood, impact, owner and the phase or spike that retires each risk; time-boxed spikes with explicit questions and decision outputs; an early thin end-to-end slice; and a review cadence tied to phase boundaries.

**Red flags:**

- Riskiest work scheduled last.
- Spikes with no question, time box or decision output.
- Risk register without owners.
- No end-to-end slice before scaling out features.

### `migration` Migration and cutover

**Question:** If this plan moves existing CORD or TERES tenants, data or features onto the new platform, is there a tested approach for data migration, parallel running, cutover, rollback and client communication?

- Which tenants, modules and data sets move, in what order, and why that order (for example a low-risk tenant first)?
- How is data migrated: mapping from old to new schema, transformation of tenant IDs and references, handling of documents and audit history, and preservation of original timestamps and case references?
- How is completeness proved after migration (row counts, checksums, sampled record comparison signed off by the client)?
- Is there a period of parallel running or read-only fallback, and how are in-flight cases and running deadlines carried across without missing a legal timeline?
- What is the rollback plan, up to what point is rollback possible, and how long would it take?
- Does data stay in the tenant's region throughout the migration, including temporary copies and migration tooling?
- When and how are clients, users and regulators (if required) told, and who approves the cutover date with the client?

**Good answer:** A per-tenant migration runbook covering mapping, verification by counts and checksums, in-flight case handling, rollback point and duration, regional handling of temporary data, and communication with client sign-off. At least one rehearsal on a production-sized copy is scheduled before the first real cutover.

**Red flags:**

- Big-bang migration of all tenants at once.
- No rehearsal on production-sized data.
- No plan for cases with running deadlines.
- Migration copies made outside the tenant's region.

### `compliance` Compliance and assurance gates

**Question:** Are the compliance and assurance activities required before each go-live placed on the plan with dates and owners, so they do not appear at the end as surprises?

- Which assurance activities must happen before production for each region: penetration test, ISO 27001 scope update, SOC 2 control evidence, data protection impact assessment, accessibility audit, ISO 42001 impact assessment for AI features?
- Which external dates constrain the plan: certification and surveillance audit windows, DPDP Rules commencement dates, client contract go-live dates, SEBI or MII onboarding timelines?
- Is evidence for audits collected from the start of each phase, or reconstructed afterwards?
- Does each go-live require updated records: record of processing, sub-processor list, privacy notices, client data processing agreements?
- Who signs off compliance readiness for each region and entity (NTPL, TAPL, US entity)?
- Is time reserved to fix findings from penetration tests and audits before go-live?

**Good answer:** Assurance activities appear as dated plan items with owners and are built into phase exit criteria, external regulatory and audit dates are listed, evidence collection starts in the first phase, and time is reserved for remediation. Compliance sign-off is named per region and entity.

**Red flags:**

- Penetration test or accessibility audit scheduled in the last week before go-live.
- No buffer to fix findings.
- Regulatory commencement dates or audit windows not on the plan.
- Privacy documents not updated for new processing.

### `readiness` Operational readiness

**Question:** Before any tenant uses a phase in production, is the platform ready to be operated: monitored, supported, recoverable and on-call?

- Is there a production readiness review per phase covering monitoring and alerts, runbooks, on-call rota per region and time zone, backups with a tested restore, and incident response including breach notification?
- Are deployment and rollback automated and rehearsed, including database migrations and Temporal worker version changes?
- Is client support ready: support process, service desk access, documentation, training for secretariat and tenant admins?
- Is the incident process able to meet breach timelines (DPDP Rules report within 72 hours, GDPR 72 hours, PDPA notification within 3 calendar days of assessing a breach as notifiable), with named roles?
- Are feature flags in place to turn off a new capability per tenant without a redeploy?
- Has a disaster-recovery exercise been run for the region going live, and were recovery targets met?

**Good answer:** A production readiness checklist is part of each phase's exit criteria and covers monitoring, runbooks, on-call, tested restore, rehearsed rollback, support readiness and an incident process that meets regulatory breach timelines. The answer names the date of the last restore and disaster-recovery exercise per region.

**Red flags:**

- Go-live without an on-call rota or runbooks.
- Backups never restored in a test.
- No incident process that meets breach-notification timelines.
- No way to disable a new feature per tenant.

### `tracking` Progress tracking and re-planning

**Question:** How will progress be measured by outcomes against the plan, and what triggers a re-plan?

- Which measures show progress: exit criteria met, nodes moved to Approved, delivery performance (deployment frequency, lead time for changes, change failure rate, time to restore service)?
- How often is the plan reviewed, by whom, and how is the status reported to the leadership team and clients?
- What variance triggers re-planning (for example a milestone slipping by more than two weeks, a critical dependency late, capacity down by 20%)?
- How are scope changes requested and approved, and what is removed when something is added?
- Are actual dates and effort recorded against estimates so future plans are better calibrated?
- Is the plan's current version visible to everyone who depends on it, with a change log?

**Good answer:** Outcome measures (exit criteria and node approval status, plus the four DORA delivery metrics) are reported at a fixed cadence, re-planning thresholds are stated, scope changes follow a trade-off rule, and estimates versus actuals are recorded for calibration.

**Red flags:**

- Progress reported as percentage of tasks done.
- No threshold for re-planning.
- Scope added without removal or date change.
- Plan versions not shared with dependent teams or clients.

