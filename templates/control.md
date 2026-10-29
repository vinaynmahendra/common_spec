# Template: Compliance control (`control`)

Generated from `control.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies an internal control so it can be operated, evidenced and audited: what risk it addresses, which frameworks it satisfies, who runs it, how often, and what proof it leaves.

**Depth:** 1–3 pages per control. Write it the way an auditor reads it: objective, description, owner, frequency, evidence, test. One node per control; group related controls under a capability. Map to framework IDs so one control can satisfy several frameworks.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `objective` Control objective (level 1)

The risk this control reduces, stated as an outcome.

Illustrative example (not a requirement):

> Access to production systems and tenant data is limited to people who currently need it.

### `mapping` Framework mapping (level 1)

Framework clause IDs this control satisfies.

Illustrative example (not a requirement):

> | Framework | Reference |
> |---|---|
> | ISO/IEC 27001:2022 Annex A | 5.15 Access control, 5.18 Access rights |
> | SOC 2 | CC6.1, CC6.2, CC6.3 |
> | DPDP Act / Rules 2025 | Reasonable security safeguards (access controls) |

### `description` Control description (level 1)

What is done, by whom, how. Specific enough that two people would perform it the same way.

Illustrative example (not a requirement):

> Each quarter, the Security lead exports all production IAM principals, database roles and platform-admin users. Each team lead confirms or revokes every account for their team within 10 working days. Revocations are executed and re-exported to prove removal.

### `owner` Owner and frequency (level 1)

Owner, backup, frequency, trigger.

Illustrative example (not a requirement):

> | Item | Value |
> |---|---|
> | Owner | Head of Security |
> | Backup | CTO |
> | Frequency | Quarterly, plus on every leaver within 24 h |
> | Type | Preventive / detective; manual with automated export |

### `evidence` Evidence (level 1)

Exactly what artefacts prove the control operated, where they are stored, and for how long.

Illustrative example (not a requirement):

> - Access export (CSV) with timestamp
> - Sign-off record per team lead
> - Revocation tickets and post-revocation export
> Stored in the compliance evidence bucket for 3 years.

### `test` Test procedure (level 2)

How an internal or external auditor tests operating effectiveness, including sample size.

Illustrative example (not a requirement):

> Select 2 quarters; for each, verify sign-off from every team lead, and for a sample of 10 leavers verify access was removed within 24 h of their exit date.

### `implementation` Implementation in the platform (level 2)

Which platform features or nodes implement or support the control.

Illustrative example (not a requirement):

> Platform-admin users and roles exported from the Authorization package; leaver hook from HR system triggers the offboarding workflow.

### `exceptions` Exceptions (level 2)

How exceptions are requested, approved, time-limited and tracked.

Illustrative example (not a requirement):

> Exceptions approved by the CTO, logged with expiry (max 90 days) and reviewed at the next quarterly review.

### `metrics` Monitoring and KPIs (level 3)

Indicators that the control is healthy.

Illustrative example (not a requirement):

> % of reviews completed on time; median hours from leaver to access removal.

### `questions` Open questions (level 3)

Checklist.

Illustrative example (not a requirement):

> - [ ] Include tenant-admin accounts held by client staff in scope?

## Checks

### `scope` Scope and population

**Question:** Exactly which entities, regions, systems, people and tenants does this control cover, and how is the full population identified so nothing in scope is missed?

- Which legal entities are covered (NTPL India, TAPL Singapore, the US entity), and does the control operate the same way in each?
- Which environments and clouds are in scope: production in each region (India, Singapore, US), AWS ECS and any Azure Container Apps deployments, staging with real data, CI/CD, corporate IT?
- What is the source of truth for the population (for example the identity provider user list, the AWS Organizations account list, the asset inventory, the sub-processor register), and how is it reconciled?
- Does the control cover Nomology staff, contractors and vendors only, or also tenant administrators and tenant users? If tenants must do something themselves, is that stated as a tenant responsibility?
- Are new systems, regions or tenants added to scope automatically, or does someone have to remember?
- What is explicitly out of scope, and why is that acceptable?

**Good answer:** Gives a scope statement listing entities, regions, clouds and system types, names the authoritative inventory the population is drawn from, and describes a reconciliation (for example monthly comparison of the identity provider against HR records). Lists tenant responsibilities (complementary user entity controls) separately so they can be published to clients.

**Red flags:**

- Scope written as 'all systems' with no inventory behind it
- Azure or non-India regions silently excluded
- Population taken from a manually kept spreadsheet with no reconciliation
- Tenant responsibilities assumed but not written down

### `owner` Ownership and accountability

**Question:** Who owns the control's design, who operates it, who covers when they are away, and who is accountable if it fails?

- Are the control owner (accountable for design), the operator (performs it) and the reviewer named by role and current person?
- Is there a named backup, and has the backup actually performed the control at least once?
- Is the operator independent of the activity being controlled (for example, the person reviewing access is not reviewing their own access)?
- Does ownership differ by entity or region (for example a Singapore data protection officer for TAPL, the DPDP grievance officer for NTPL), and is that recorded?
- How is ownership kept current when people change roles or leave, and how often is the owner list reviewed?
- Does the owner have the authority and system access needed to act on findings?

**Good answer:** Names the owner, operator, reviewer and backup by role and person, with evidence that the backup has operated the control. Shows segregation between the person performing the control and the person whose work is checked, and states how often the ownership register is reviewed (for example at each quarterly ISMS management review).

**Red flags:**

- Owner is a team or 'Engineering' rather than a person
- No backup, or a backup who has never done it
- The operator reviews their own access or changes
- Owner lacks authority to enforce remediation

### `evidence` Evidence quality and retention

**Question:** Does the control leave complete, reliable, timestamped evidence that an auditor can sample without asking the team to recreate it?

- What exactly is the evidence for each run (system export, ticket, signed review, screenshot), and does it show who performed it, when, what was reviewed and the result?
- Is the evidence generated by the system rather than typed by hand, and can it be shown to be complete and unaltered (query used, row counts, hash or immutable storage)?
- Where is it stored, in which region, who can change or delete it, and is that storage itself access-controlled and logged?
- How long is it kept, and does that cover the SOC 2 Type II observation period plus the audit, ISO 27001 surveillance cycles, DPDP Rules log retention of at least one year and client contract requirements?
- If a run is missed or late, does the evidence show that, rather than being backfilled?
- Does any evidence contain personal data, and is it minimised or masked?

**Good answer:** Lists the evidence artefact per run with its system source, storage location and retention period, and explains how completeness is shown (for example the query and row count are saved with the export). Evidence is stored in an append-only or write-once location in the relevant region and kept at least for the longest applicable period.

**Red flags:**

- Evidence is screenshots taken on request at audit time
- Evidence can be edited or deleted by the control operator
- No retention period, or one shorter than the audit period
- No way to tell a missed run from a run that left no record

### `automation` Automation and continuous monitoring

**Question:** Which parts of the control are automated or continuously monitored, which remain manual, and how is the automation itself kept trustworthy?

- Which steps could be automated with the platform or cloud tooling (for example Temporal scheduled workflows, AWS Config rules, Security Hub, Azure Policy, CI checks) and which require human judgement?
- Does automation detect drift between runs (continuous monitoring), or only run on a schedule?
- Who owns the automation code, is it in the monorepo with code review, and how are changes to it approved?
- How would you know if the automation silently stopped running or returned an empty result (heartbeat, expected-count check, alert on missing run)?
- Is the automation's output reviewed by a person where judgement is needed, and is that review evidenced?
- Is the same automation deployed in every region and cloud in scope?

**Good answer:** Separates automated and manual steps, names the tool and repository for each automated step, and describes a dead-man alert that fires if a run is missing or returns zero items unexpectedly. Changes to control automation go through the same change management as production code.

**Red flags:**

- Automation with no alert when it fails or stops
- Automation scripts outside version control or changed without review
- Claims of continuous monitoring with no defined signal or threshold

### `deficiency` Failures and remediation

**Question:** When the control finds a problem or fails to operate, how is that classified, fixed, escalated and, where required, reported to regulators or clients?

- How is a finding recorded (ticket, risk register entry), and what are the fix deadlines by severity?
- How is a control failure (control not performed, or performed badly) distinguished from a finding the control correctly caught?
- When does a finding become a security incident or personal data breach, and who decides?
- If it is a breach or incident, which notification clocks start: CERT-In within 6 hours of noticing, DPDP intimation to the Data Protection Board and affected Data Principals without delay with a detailed report to the Board within 72 hours, GDPR supervisory authority within 72 hours of becoming aware, Singapore PDPC within 3 calendar days of assessing the breach as notifiable, and any shorter client contract terms?
- How are repeat failures escalated to ISMS management review and to the risk register?
- How is the fix verified, and is root cause recorded?

**Good answer:** Defines severity levels with fix deadlines, a clear route from finding to incident to regulatory notification with the decision owner named, and escalation of repeated failures to management review. Each finding ticket records root cause and verification of the fix.

**Red flags:**

- No fix deadlines
- No defined link from findings to the incident and breach-notification process
- Missed control runs not treated as a failure
- Findings closed without verification

### `exceptions` Exceptions and risk acceptance

**Question:** How can someone be excused from this control, who can approve it, how long does it last, and what compensates for the gap?

- Who may request an exception, and what must the request include (reason, scope, risk, compensating control, end date)?
- Who approves, and does approval authority rise with risk (for example CTO for high risk, CISO or ISMS committee for critical)?
- What is the maximum exception length, and what happens automatically at expiry (reminder, re-approval, alert, revert)?
- Are exceptions recorded in the risk register and visible to auditors?
- Can exceptions affect a tenant's data or contractual commitments, and if so is the tenant told or asked?
- How many exceptions are open now, and is the count reviewed at management review?

**Good answer:** Describes an exception register with mandatory fields, risk-tiered approvers, a hard maximum duration (for example 90 days, renewable once with re-approval) and automated expiry alerts. Each exception names a compensating control and is linked to the risk register.

**Red flags:**

- Exceptions agreed in chat or email with no register
- No expiry date
- The person requesting can also approve
- No compensating control

### `assurance` Independent assurance

**Question:** How is the control's design and operating effectiveness checked independently, and does that rely on controls run by cloud providers or other third parties?

- Who tests the control internally (internal audit, a second-line reviewer), how often, and are they independent of the operator?
- Is design tested (would it stop the risk if run correctly) separately from operating effectiveness (was it actually run correctly, every time, over the period)?
- For a SOC 2 Type II, what is the observation period, and does the control have enough runs in that period for an auditor to sample (for example a quarterly control needs all runs in the period)?
- Which parts depend on AWS, Azure or other sub-processors' controls, and have their SOC 2 or ISO reports been reviewed with any carve-outs and complementary controls noted?
- How are results of internal audits, ISO surveillance audits and SOC 2 reports fed back into the control description?
- Has the control been tested with a dry run before the first external audit?

**Good answer:** Names the independent tester and frequency, separates tests of design and of operating effectiveness, and confirms the run frequency yields an auditable sample in the observation period. Lists third-party reports relied upon, the date each was reviewed, and the complementary controls Nomology must run.

**Red flags:**

- Only the operator checks the control
- Reliance on a cloud provider's controls without reviewing their assurance report
- First test of the control is the external audit

### `commitments` Legal and client commitments

**Question:** Which legal duties and client promises depend on this control, and would a change to it break any of them?

- Which specific legal duties does it support: DPDP Act and Rules 2025 (security safeguards, breach intimation, retention and erasure, Significant Data Fiduciary duties if notified), GDPR, Singapore PDPA, US state privacy laws, CERT-In directions?
- Which client contracts, data processing agreements, security questionnaires or SEBI/MII requirements quote or rely on this control?
- Do commitments differ by entity or tenant (for example HKIAC versus SEBI ODR institutions), and is the strictest one applied or are variants tracked?
- If AI features are in scope, does ISO 42001 add requirements for this control?
- Who must approve a change that weakens or removes this control, and are affected clients told?
- Is the control description used in public trust material (trust page, questionnaire answers), and is that kept in sync?

**Good answer:** Lists each law and contract that relies on the control with the clause reference, notes any tenant-specific variants, and states that changes to the control require compliance and legal review before release, with client notice where contracts require it.

**Red flags:**

- Security questionnaire answers that describe the control differently from this spec
- Contractual commitments unknown to the control owner
- Control can be changed with no compliance or legal review

